# -*- coding: utf-8 -*-
"""Das Zahlungskonto des Kunden — über Stripes Billing-Portal.

**Warum kein eigenes Kartenformular.** Der Wunsch war, dass der Kunde seine
Zahlungsart aktualisieren kann. Ein eigenes Formular dafuer hiesse,
Kartendaten durch unseren Server zu fuehren — und damit in den Geltungsbereich
von PCI DSS zu geraten, fuer einen Betrieb mit einem Entwickler. Stripe hat
dafuer eine gehostete Seite: Der Kunde aendert dort Zahlungsart, sieht seine
Abos und seine Rechnungen. Wir erzeugen nur eine Sitzung und leiten weiter;
eine Kartennummer beruehrt uns nie.

**Woher die Kundenkennung kommt.** Stripe legt bei jedem Abo-Kauf einen Kunden
an. Wir haben diese Kennung bisher nur an der GEO-Analyse festgehalten — am
Erzeugnis eines einzelnen Kaufs. Seit dem 04.09.2026 steht sie am **Betrieb**:
Ein Kunde hat ein Zahlungsmittel, nicht eines je Produkt.

Drei Wege, in dieser Reihenfolge:

1. `leads.stripe_customer_id` — der Regelfall, sobald ein Kauf durchlief.
2. Die Kennung an einer GEO-Analyse des Betriebs — Altbestand aus der Zeit,
   als sie nur dort stand. Wird beim Finden **an den Betrieb geschrieben**,
   damit der Umweg genau einmal noetig ist.
3. Nachschlagen bei Stripe ueber die Mailadresse — fuer Kaeufe, die vor dieser
   Aenderung liefen und keine Kennung hinterlassen haben.

**Und wenn nichts davon greift, ist das kein Fehler.** Ein Betrieb, der noch
nie etwas gekauft hat, hat kein Zahlungskonto. Der Bericht sagt das, statt
einen Knopf anzubieten, der ins Leere fuehrt — dieselbe Regel wie ueberall in
diesem Bestand: nicht erhoben ist nicht null.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class KeinZahlungskonto(Exception):
    """Der Betrieb hat bei Stripe keinen Kunden — noch nichts gekauft."""


class StripeNichtEingerichtet(Exception):
    """Ohne Schluessel gibt es kein Portal. Kein Kundenfehler, ein Betriebsfehler."""


def _stripe():
    schluessel = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if not schluessel:
        raise StripeNichtEingerichtet("STRIPE_SECRET_KEY ist nicht gesetzt")
    import stripe

    stripe.api_key = schluessel
    return stripe


def kundenkennung(db, lead) -> Optional[str]:
    """Die Stripe-Kennung des Betriebs — gesucht, und beim Finden gemerkt."""
    if getattr(lead, "stripe_customer_id", None):
        return lead.stripe_customer_id

    # Altbestand: die Kennung hing an der GEO-Analyse.
    try:
        from modelle_audit import GeoAnalysis

        zeile = (db.query(GeoAnalysis)
                 .filter(GeoAnalysis.lead_id == lead.id,
                         GeoAnalysis.stripe_customer_id.isnot(None))
                 .order_by(GeoAnalysis.id.desc()).first())
        if zeile and zeile.stripe_customer_id:
            lead.stripe_customer_id = zeile.stripe_customer_id
            db.commit()
            return lead.stripe_customer_id
    except Exception as fehler:      # noqa: BLE001
        logger.info("GEO-Kennung nicht lesbar: %s: %s", type(fehler).__name__, fehler)

    # Letzter Weg: bei Stripe ueber die Mailadresse nachschlagen.
    if not (lead.email or "").strip():
        return None
    try:
        stripe = _stripe()
        treffer = stripe.Customer.list(email=lead.email.strip(), limit=1)
        if treffer.data:
            lead.stripe_customer_id = treffer.data[0].id
            db.commit()
            return lead.stripe_customer_id
    except StripeNichtEingerichtet:
        raise
    except Exception as fehler:      # noqa: BLE001
        logger.warning("Stripe-Kundensuche fuer Betrieb %s gescheitert: %s: %s",
                       lead.id, type(fehler).__name__, fehler)
    return None


def portal_sitzung(db, lead, rueckkehr: str) -> str:
    """Die Adresse der gehosteten Zahlungsseite — gilt einmal und kurz.

    `rueckkehr` ist die Seite, auf der der Kunde wieder landet. Sie kommt vom
    Aufrufer und nicht aus einer festen Zeile: Staging und Produktiv haben
    verschiedene Adressen, und ein fester Wert schickt den Kunden der
    Staging-Probe in die Produktivumgebung.
    """
    kennung = kundenkennung(db, lead)
    if not kennung:
        raise KeinZahlungskonto(
            "Für diesen Betrieb ist bei unserem Zahlungsdienst kein Konto hinterlegt.")
    stripe = _stripe()
    sitzung = stripe.billing_portal.Session.create(
        customer=kennung, return_url=rueckkehr)
    return sitzung.url


def merke_kennung(db, lead, kennung: str) -> None:
    """Die Kennung aus einem Kauf am Betrieb festhalten.

    Aufgerufen aus den Webhooks. **Der erste Wert bleibt stehen:** Stripe legt
    bei jedem Kauf ohne mitgegebenen Kunden einen neuen an; ihn zu
    ueberschreiben hiesse, das Portal auf ein Konto zu zeigen, in dem nur der
    letzte Kauf steht.
    """
    if not kennung or getattr(lead, "stripe_customer_id", None):
        return
    lead.stripe_customer_id = kennung
    db.commit()
    logger.info("Zahlungskonto %s am Betrieb %s gemerkt", kennung, lead.id)
