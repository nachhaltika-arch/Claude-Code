# -*- coding: utf-8 -*-
'''Das Pflege-Abo über Stripe (Entscheidung David, 04.09.2026).

**Zwei Stellen kosten hier Geld, wenn sie falsch sind**, und beide haben
einen Test:

1. **Doppelter Einzug.** Zieht Stripe ein und schreibt jemand aus der
   monatlichen Aufstellung zusätzlich eine Rechnung, zahlt der Kunde zweimal.
   Das fällt bei ihm auf, nicht bei uns.
2. **Rückwirkung.** Ein Vertrag, der unter „Rechnung" geschlossen wurde, trägt
   keine Einzugsermächtigung. Ihn stillschweigend auf Abbuchung zu stellen
   hieße, Geld von einem Konto zu holen, dem niemand zugestimmt hat.

Die Stripe-Aufrufe selbst sind hier **nicht** geprüft — dafür bräuchte es
einen Schlüssel und ein Konto. Geprüft ist, was ohne Stripe entscheidbar ist:
der Betrag, die Auswahl und die Weigerungen.
'''
from datetime import datetime

import pytest

from services import abo_abrechnung, abo_stripe, abo_stunden, abo_vertrag

BETRIEB_NAME = "Dachdeckerei Stripe-Nur-Im-Test"

pytestmark = pytest.mark.usefixtures("app")


@pytest.fixture()
def db(app):
    from database import SessionLocal
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture()
def betrieb(db):
    from database import Benachrichtigung, Lead, TimeTracking
    from modelle_abo import AboVertrag

    lead = Lead(company_name=BETRIEB_NAME)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    kennung = lead.id
    try:
        yield kennung
    finally:
        db.query(Benachrichtigung).filter(Benachrichtigung.lead_id == kennung).delete()
        db.query(TimeTracking).filter(TimeTracking.lead_id == kennung).delete()
        db.query(AboVertrag).filter(AboVertrag.lead_id == kennung).delete()
        db.query(Lead).filter(Lead.id == kennung).delete()
        db.commit()


def test_der_abgebuchte_betrag_ist_der_aufgestellte():
    """**Der wichtigste Wert dieser Umstellung.**

    Bucht Stripe einen anderen Betrag ab, als die Aufstellung meldet, fällt
    das niemandem auf — bis ein Kunde nachrechnet. Beide lesen deshalb
    dieselbe Funktion.
    """
    for produkt, netto in (("ABO-BAS", abo_stunden.PREIS_ABO_BAS_NETTO_CENT),
                           ("ABO-PRO", abo_stunden.PREIS_ABO_PRO_NETTO_CENT)):
        brutto = abo_stunden.preis_brutto_cent(produkt)
        steuer = int(round(netto * abo_stunden.STEUERSATZ_ABO / 100))

        assert brutto == netto + steuer
        assert abo_stunden.preis_netto_cent(produkt) == netto

    # Die Zahlen im Klartext, damit eine stille Änderung auffällt.
    assert abo_stunden.preis_brutto_cent("ABO-BAS") == 9401
    assert abo_stunden.preis_brutto_cent("ABO-PRO") == 17731


def test_was_stripe_einzieht_steht_nicht_in_der_aufstellung(db, betrieb):
    """Sonst zahlt der Kunde denselben Monat zweimal."""
    # Arrange
    monat = abo_stunden.monat_von(datetime(2026, 10, 15))
    vertrag = abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                                  start_monat=monat, abrechnung="stripe")

    # Act — noch ohne Abonnement: fällig, aber von niemandem eingezogen.
    vorher = abo_abrechnung.offene_posten(db, monat)

    vertrag.stripe_subscription_id = "sub_test_nur_im_test"
    db.commit()
    nachher = abo_abrechnung.offene_posten(db, monat)

    # Assert
    assert [p["lead_id"] for p in vorher].count(betrieb) == 1, (
        "Ein Vertrag auf Stripe ohne eingerichteten Einzug muss stehen "
        "bleiben — ihn zieht sonst niemand ein")
    assert betrieb not in [p["lead_id"] for p in nachher], (
        "Mit laufendem Abonnement gehört der Posten Stripe, nicht der "
        "Rechnungsstellung")


def test_ein_rechnungsvertrag_bleibt_in_der_aufstellung(db, betrieb):
    """Wer keine Einzugsermächtigung erteilt hat, bekommt weiter eine Rechnung."""
    # Arrange
    monat = abo_stunden.monat_von(datetime(2026, 10, 15))
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                        start_monat=monat, abrechnung="rechnung")

    # Act
    posten = abo_abrechnung.offene_posten(db, monat)

    # Assert
    assert betrieb in [p["lead_id"] for p in posten]


def test_die_abrechnungsart_ist_stripe_wenn_niemand_etwas_sagt(db, betrieb):
    """Die Entscheidung vom 04.09.2026 gilt für alles Neue."""
    # Arrange & Act
    vertrag = abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                                  start_monat="2026-11")

    # Assert
    assert vertrag.abrechnung == "stripe"
    assert vertrag.laeuft_ueber_stripe is False, (
        "Ohne Abonnement zieht Stripe nichts ein — die Art allein genügt nicht")


def test_eine_erfundene_abrechnungsart_wird_abgewiesen(db, betrieb):
    """Ein Tippfehler wäre ein Vertrag, den niemand einzieht."""
    from services.abo_stunden import AboZeitFehler

    with pytest.raises(AboZeitFehler):
        abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                            start_monat="2026-11", abrechnung="lastschrift")


def test_der_laufende_vertrag_ist_der_ohne_ende(db, betrieb):
    """Der Kaufweg braucht genau einen — und darf nicht raten."""
    # Arrange — ein beendeter und ein laufender Vertrag.
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                        start_monat="2026-01", end_monat="2026-06")
    laufend = abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                                  start_monat="2026-07")

    # Act
    gefunden = abo_vertrag.laufender(db, betrieb)

    # Assert
    assert gefunden is not None and gefunden.id == laufend.id


def test_ohne_vertrag_gibt_es_keinen_laufenden(db, betrieb):
    """`None` statt einer Ausnahme — der Aufrufer entscheidet, was das heißt."""
    assert abo_vertrag.laufender(db, betrieb) is None


def test_ein_unbekannter_tarif_kommt_nicht_bis_stripe():
    """Erst prüfen, dann Preise anlegen — ein Produkt in Stripe bleibt stehen."""
    with pytest.raises(abo_stripe.UnbekanntesAbo):
        abo_stripe.preis_id("ABO-XXL")


def test_der_stripe_dienst_kennt_beide_tarife():
    """Name und Beschreibung stehen auf dem Kontoauszug des Kunden."""
    assert set(abo_stripe.PRODUKT_NAME) == {"ABO-BAS", "ABO-PRO"}
    assert set(abo_stripe.PRODUKT_BESCHREIBUNG) == {"ABO-BAS", "ABO-PRO"}
    # SEPA gehört dazu — das Datenblatt nennt unter Z4 ausdrücklich die
    # Lastschrift, und bei einem Dauerschuldverhältnis ist sie der übliche Weg.
    assert "sepa_debit" in abo_stripe.ZAHLWEGE
