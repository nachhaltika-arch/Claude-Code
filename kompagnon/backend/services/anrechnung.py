# -*- coding: utf-8 -*-
"""Die Anrechnung auf einen Websprint (L-100, ORDERS_08).

**Die Zusage:** Wer ein Workbook für 149 € oder einen Check PLUS für 249 €
gekauft hat und binnen sechs Monaten einen Websprint beauftragt, bekommt den
Betrag vollständig angerechnet.

**Warum das automatisch laufen muss.** Eine Anrechnung, an die jemand denken
muss, wird irgendwann vergessen. Der Kunde erinnert sich immer — und es ist
genau der Moment, in dem er Vertrauen fassen soll. Ein vergessener Abzug im
Angebot kostet mehr als die 149 €.

**Dies ist die einzige Verbindung zwischen Bestellbereich und Projekten.**
Alles andere bleibt getrennt: Der Bestellablauf hat bewusst keine Projektlogik,
weil eine Workbook-Bestellung keine Domain hat und sonst bei „Veröffentlichung"
hängen bliebe.

**Adressen werden normalisiert.** „Max@Betrieb.de" und „max@betrieb.de" sind
derselbe Kunde. Ohne das findet die Prüfung nichts, und der Kunde ruft an — mit
Recht, denn er hat bezahlt.

**Alle offenen Anrechnungen, nicht die erste.** Jemand kann Workbook **und**
Check PLUS gekauft haben; das sind zusammen 398 €. Welche gezogen wird, ist
eine Entscheidung für einen Menschen und nicht für die Reihenfolge einer
Datenbankabfrage.
"""
import logging
from datetime import date, datetime

from sqlalchemy import text

logger = logging.getLogger(__name__)

#: Wie viele Tage vor Ablauf erinnert wird. **Genau** dieser Abstand, nicht
#: „höchstens": Sonst bekäme derselbe Käufer die Mail an dreißig Tagen
#: hintereinander.
WARNUNG_TAGE = 30


def normalisiert(mail: str) -> str:
    """`  Max@Betrieb.DE ` → `max@betrieb.de`."""
    return (mail or "").strip().lower()


def _zeile(eintrag, heute: date) -> dict:
    """Was der Innendienst sehen muss, um zu entscheiden.

    `tage_uebrig` steht dabei, weil „gültig bis" allein zum Rechnen zwingt —
    und wer rechnet, rechnet irgendwann falsch.
    """
    return {
        "order_number": eintrag.order_number,
        "product_code": eintrag.product_slug or "",
        "betrag_cents": int(eintrag.price_gross_cents or 0),
        "gueltig_bis": (eintrag.credit_valid_until.isoformat()
                        if eintrag.credit_valid_until else None),
        "tage_uebrig": ((eintrag.credit_valid_until - heute).days
                        if eintrag.credit_valid_until else None),
    }


def offene(db, mail: str, heute: date = None) -> list:
    """Alle offenen Anrechnungen dieser Adresse.

    Die Bedingungen stehen alle hier und nicht verteilt: bezahlt, anrechenbar,
    Frist läuft, noch nicht eingelöst. Eine davon anderswo zu prüfen hiesse,
    sie beim nächsten Aufrufer zu vergessen.
    """
    from modelle_buch import BookOrder

    heute = heute or date.today()
    ziel = normalisiert(mail)
    if not ziel:
        return []

    anrechenbare = {
        zeile[0] for zeile in db.execute(text(
            "SELECT slug FROM products WHERE is_creditable = true")).fetchall()
    }
    if not anrechenbare:
        return []

    eintraege = (db.query(BookOrder)
                 .filter(BookOrder.payment_status.in_(("paid", "delivered")),
                         BookOrder.product_slug.in_(anrechenbare),
                         BookOrder.credit_redeemed_deal_id.is_(None),
                         BookOrder.credit_valid_until.isnot(None),
                         BookOrder.credit_valid_until >= heute)
                 .order_by(BookOrder.credit_valid_until.asc())
                 .all())

    # Die Adresse in Python vergleichen: In der Datenbank stehen historisch
    # gemischte Schreibweisen, und ein `lower()` in der Abfrage umginge den
    # Index auf `email`, ohne das Ergebnis zu verbessern.
    return [_zeile(e, heute) for e in eintraege
            if normalisiert(e.email) == ziel]


def einloesen(db, order_number: str, deal_id: int, heute: date = None):
    """Eine Anrechnung endgültig auf einen Deal buchen.

    **Endgültig ist wörtlich gemeint.** Eine Rücknahme erfolgt nur von Hand
    mit Protokolleintrag; ein Weg zurück im Code wäre ein Weg, denselben
    Betrag zweimal anzurechnen.

    Gibt `(eintrag, fehlercode, meldung)` zurück — der Aufrufer macht daraus
    seine HTTP-Antwort. So bleibt die Regel hier und nicht im Router.
    """
    from modelle_buch import BookOrder

    heute = heute or date.today()

    eintrag = db.query(BookOrder).filter(
        BookOrder.order_number == order_number).first()
    if not eintrag:
        return None, 404, "Bestellung nicht gefunden"

    if eintrag.credit_redeemed_deal_id:
        # 409 und **mit** der Nummer des ersten Deals: „schon eingelöst" ohne
        # Angabe, wohin, zwingt den Innendienst zur Suche in der Datenbank.
        return None, 409, (f"Diese Anrechnung wurde bereits auf Deal "
                           f"{eintrag.credit_redeemed_deal_id} gebucht")

    if not eintrag.credit_valid_until or eintrag.credit_valid_until < heute:
        return None, 400, "Die Frist für diese Anrechnung ist abgelaufen"

    if eintrag.payment_status not in ("paid", "delivered"):
        return None, 400, "Diese Bestellung ist nicht bezahlt"

    vorhanden = db.execute(text("SELECT id FROM deals WHERE id = :d"),
                           {"d": deal_id}).scalar()
    if not vorhanden:
        # Vor dem Schreiben geprüft: Sonst gilt die Anrechnung als verbraucht
        # und zeigt auf einen Deal, den es nicht gibt.
        return None, 404, f"Deal {deal_id} nicht gefunden"

    eintrag.credit_redeemed_deal_id = int(deal_id)
    eintrag.credit_redeemed_at = datetime.utcnow()
    db.commit()
    logger.info("Anrechnung %s auf Deal %s gebucht (%d Cent)",
                eintrag.order_number, deal_id, eintrag.price_gross_cents or 0)
    return eintrag, 200, "gebucht"


# ── Die Ablaufwarnung ────────────────────────────────────────────────

def _erinnerung_senden(eintrag) -> bool:
    """Die Erinnerung an eine auslaufende Anrechnung.

    **Das ist ein Verkaufsinstrument, kein Serviceschreiben** — und ein
    zulässiges: Der Empfänger hat gekauft, die Anrechnung ist ihm zugesagt,
    und der Anlass ist sachlich. Genau dafür wurde sie konstruiert.

    Der zentrale Mailweg (`services/email`), kein zweiter.
    """
    from services.email import send_email

    betrag = (eintrag.price_gross_cents or 0) / 100
    bis = (eintrag.credit_valid_until.strftime("%d.%m.%Y")
           if eintrag.credit_valid_until else "")
    html = (
        f"<p>Ihre Anrechnung über {betrag:.2f} € aus der Bestellung "
        f"{eintrag.order_number} ist noch bis zum {bis} gültig.</p>"
        f"<p>Wenn Sie in dieser Zeit einen Websprint beauftragen, ziehen wir "
        f"den Betrag vollständig ab.</p>"
    )
    return send_email(eintrag.email,
                      f"Ihre Anrechnung über {betrag:.2f} € läuft aus", html)


def ablaufwarnung(heute: date = None) -> int:
    """Täglicher Lauf: erinnert an Anrechnungen, die in 30 Tagen verfallen.

    **Eigene Sitzung, und sie ist zu, bevor Brevo gerufen wird.** Ein
    Mailversand dauert; eine offene Verbindung währenddessen ist eine
    Verbindung, die den anderen fehlt.

    **Eine gescheiterte Mail hält den Lauf nicht an.** Sonst bekäme der
    zweite Käufer keine Erinnerung, weil beim ersten Brevo klemmte.

    Gibt zurück, wie viele Erinnerungen wirklich hinausgingen — nicht, wie
    viele fällig waren. Der Unterschied ist die Aussage.
    """
    from database import SessionLocal
    from modelle_buch import BookOrder

    heute = heute or date.today()
    ziel = heute + __import__("datetime").timedelta(days=WARNUNG_TAGE)

    db = SessionLocal()
    try:
        faellig = (db.query(BookOrder)
                   .filter(BookOrder.payment_status.in_(("paid", "delivered")),
                           BookOrder.credit_redeemed_deal_id.is_(None),
                           BookOrder.credit_valid_until == ziel)
                   .all())
        for eintrag in faellig:
            db.expunge(eintrag)
    finally:
        db.close()

    gesendet = 0
    for eintrag in faellig:
        try:
            if _erinnerung_senden(eintrag):
                gesendet += 1
        except Exception as fehler:                      # noqa: BLE001
            logger.error("Ablaufwarnung fuer %s nicht versendet: %s",
                         eintrag.order_number, fehler)

    if faellig:
        logger.info("Ablaufwarnung: %d von %d Erinnerungen versendet",
                    gesendet, len(faellig))
    return gesendet
