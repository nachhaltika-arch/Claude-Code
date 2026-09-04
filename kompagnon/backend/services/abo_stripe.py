# -*- coding: utf-8 -*-
'''Das Pflege-Abo über Stripe einziehen (Entscheidung David, 04.09.2026).

**Was sich geändert hat.** Am 01.09.2026 war entschieden, monatlich per
Rechnung abzurechnen; `services/abo_abrechnung.py` stellt seither auf, wer was
schuldet, und ein Mensch vergibt die Rechnungsnummer. Am 04.09. ist
entschieden, das Pflege-Abo über Stripe laufen zu lassen. Damit zieht Stripe
ein, was bis dahin von Hand berechnet wurde.

**Nicht rückwirkend.** Ein Vertrag, der unter „Rechnung" geschlossen wurde,
trägt keine Einzugsermächtigung. `AboVertrag.abrechnung` hält deshalb je
Vertrag fest, wie er eingezogen wird; die Migration hat den Bestand
ausdrücklich auf `rechnung` gesetzt. Wer wechselt, wechselt mit Zustimmung.

**Warum das dem GEO-Zusatz folgt und nicht neu erfunden wird.**
`services/geo_stripe_helper.py` macht seit Wochen genau das: einen Preis bei
Bedarf anlegen, ein Abonnement über `mode="subscription"` starten, zum
Periodenende kündigen. Ein zweites Muster für dieselbe Sache wäre ein zweiter
Ort, an dem sich Stripe-Verhalten ändert.

**Der Unterschied zum GEO-Zusatz, und er ist wichtig:** Dort setzt der
Innendienst den Preis je Projekt. Hier gibt es zwei feste Tarife, und ihr
Betrag steht in `services/abo_stunden.py` — derselben Quelle, aus der die
Aufstellung rechnet. Ein Abonnement, das einen anderen Betrag abbucht als die
Aufstellung meldet, fällt niemandem auf, bis ein Kunde nachrechnet.

**Abgebucht wird brutto.** Entscheidung David vom 21.08.2026 (L-61): Was auf
dem Bildschirm steht, ist der Betrag, der abgebucht wird — kein
`automatic_tax`, keine `tax_rates`. Die Zerlegung in netto und Steuer steht in
`abo_stunden.preis_brutto_cent`.
'''
import logging
import os

import stripe

from services.abo_stunden import (STEUERSATZ_ABO, preis_brutto_cent,
                                  preis_netto_cent)

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

#: Wie das Produkt in Stripe und auf dem Kontoauszug des Kunden heißt.
PRODUKT_NAME = {
    "ABO-BAS": "KOMPAGNON Pflege Basic",
    "ABO-PRO": "KOMPAGNON Pflege Pro",
}
PRODUKT_BESCHREIBUNG = {
    "ABO-BAS": ("Hosting, SSL, Sicherungen, Verfügbarkeitsüberwachung, "
                "30 Minuten Inhaltsänderungen je Monat, jährliches Re-Audit"),
    "ABO-PRO": ("Wie Pflege Basic, dazu 90 Minuten Inhaltsänderungen je Monat "
                "und ein monatlicher Leistungsbericht"),
}

#: Beide Wege, die ein Handwerksbetrieb erwartet. `sepa_debit` steht zuerst
#: im Datenblatt (Z4) und ist bei einem Dauerschuldverhältnis der übliche;
#: die Karte bleibt daneben, weil sie sofort funktioniert.
ZAHLWEGE = ["card", "sepa_debit"]


class StripeNichtEingerichtet(RuntimeError):
    """Ohne `STRIPE_SECRET_KEY` gibt es keinen Kaufweg."""


class UnbekanntesAbo(ValueError):
    """Eine Tarifkennung, die es nicht gibt."""


def _pruefe(produkt: str) -> str:
    kennung = (produkt or "").strip().upper()
    if kennung not in PRODUKT_NAME:
        raise UnbekanntesAbo(
            f"„{produkt}“ ist kein Pflege-Abo — bekannt sind "
            f"{', '.join(sorted(PRODUKT_NAME))}")
    if not stripe.api_key:
        raise StripeNichtEingerichtet(
            "STRIPE_SECRET_KEY fehlt — ohne ihn lässt sich kein Abonnement anlegen")
    return kennung


def preis_id(produkt: str) -> str:
    '''Die Stripe-Preis-Kennung für einen Tarif, angelegt falls es sie nicht gibt.

    **Gesucht wird nach Betrag und Intervall, nicht nach dem Namen.** Ein
    Preis in Stripe ist unveränderlich; ändert sich der Tarif, entsteht ein
    neuer. Die Suche über den Betrag findet deshalb genau den, der zum heute
    gültigen Preis gehört — und legt sonst einen an, statt einen alten
    weiterzuverwenden, der einmal denselben Namen trug.
    '''
    kennung = _pruefe(produkt)
    cent = preis_brutto_cent(kennung)

    vorhanden = stripe.Price.list(active=True, type="recurring", limit=100)
    for preis in vorhanden.auto_paging_iter():
        if (preis.unit_amount == cent
                and preis.recurring
                and preis.recurring.interval == "month"
                and (preis.metadata or {}).get("kompagnon_abo") == kennung):
            logger.info("Stripe-Preis gefunden: %s (%s, %d Cent)",
                        preis.id, kennung, cent)
            return preis.id

    produkt_obj = stripe.Product.create(
        name=PRODUKT_NAME[kennung],
        description=PRODUKT_BESCHREIBUNG[kennung],
        metadata={"kompagnon_abo": kennung},
    )
    neu = stripe.Price.create(
        product=produkt_obj.id,
        unit_amount=cent,
        currency="eur",
        recurring={"interval": "month"},
        metadata={
            "kompagnon_abo": kennung,
            # Zum Nachlesen im Stripe-Dashboard, wenn jemand fragt, wie sich
            # der Betrag zusammensetzt. Stripe rechnet nichts davon nach.
            "netto_cent": str(preis_netto_cent(kennung)),
            "steuersatz": str(STEUERSATZ_ABO),
        },
    )
    logger.info("Stripe-Preis angelegt: %s (%s, %d Cent/Monat)",
                neu.id, kennung, cent)
    return neu.id


def kaufweg(produkt: str, *, lead_id: int, email: str, betrieb: str,
            erfolg_url: str, abbruch_url: str,
            kennung_kunde: str = "") -> dict:
    '''Eine Stripe-Sitzung, an deren Ende ein laufendes Abonnement steht.

    `kennung_kunde` ist die Stripe-Kundennummer, falls der Betrieb schon eine
    hat. Sie mitzugeben ist kein Beiwerk: Ohne sie legt Stripe einen zweiten
    Kunden an, und das Zahlungsportal im Kundenkonto (`zahlungsportal.py`)
    zeigt dann die eine Hälfte der Rechnungen und die andere nicht.
    '''
    kennung = _pruefe(produkt)
    preis = preis_id(kennung)

    kunde = {"customer": kennung_kunde} if kennung_kunde else {
        "customer_email": email or None,
        # Ohne bestehenden Kunden trotzdem einen anlegen — sonst gibt es
        # später nichts, worauf das Zahlungsportal zeigen könnte.
        "customer_creation": "always",
    }

    merkmale = {
        "lead_id": str(lead_id),
        "abo_produkt": kennung,
        "betrieb": betrieb or "",
    }

    sitzung = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=ZAHLWEGE,
        line_items=[{"price": preis, "quantity": 1}],
        success_url=erfolg_url,
        cancel_url=abbruch_url,
        locale="de",
        metadata=merkmale,
        # **Auch am Abonnement, nicht nur an der Sitzung.** Die Sitzung ist
        # nach dem Kauf erledigt; spätere Ereignisse (Zahlung fehlgeschlagen,
        # gekündigt) tragen nur die Merkmale des Abonnements. Ohne sie wäre
        # bei jedem davon offen, um welchen Betrieb es geht.
        subscription_data={"metadata": merkmale},
        **kunde,
    )
    return {"kaufweg_url": sitzung.url, "sitzung_id": sitzung.id,
            "preis_id": preis, "brutto_cent": preis_brutto_cent(kennung)}


def kuendigen(subscription_id: str) -> bool:
    '''Zum Ende der bezahlten Periode kündigen, nicht sofort.

    Sofort hieße: Der Kunde hat den laufenden Monat bezahlt und verliert die
    Leistung. Stripe erstattet dabei nichts von selbst.
    '''
    if not subscription_id:
        return False
    try:
        stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
        return True
    except Exception:  # noqa: BLE001
        logger.exception("Stripe-Abo %s konnte nicht gekündigt werden",
                         subscription_id)
        return False
