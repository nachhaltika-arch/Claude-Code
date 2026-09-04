# -*- coding: utf-8 -*-
'''Der Monatsbericht als Verlauf und die nächste Prüfung (L-160, Rang 2).

**Zwei Zusagen, die automatisch liefen und beim Kunden nie ankamen.** Der
Monatsbericht ging als Mail hinaus und war danach nirgends abrufbar; das
Re-Audit meldete dem **Innendienst**, wer dran ist. Beides sind Positionen aus
dem Leistungsverzeichnis, für die der Kunde monatlich zahlt.

Geprüft wird hier, was ohne Postfach und ohne PageSpeed entscheidbar ist: was
gespeichert wird, wie der Verlauf gerechnet wird, und wann die nächste Prüfung
fällig ist.
'''
from datetime import datetime, timedelta

import pytest

from services import leistungsbericht, quartals_reaudit, abo_vertrag

BETRIEB_NAME = "Tischlerei Bericht-Nur-Im-Test"

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
    from database import AuditResult, Lead
    from modelle_abo import AboVertrag, Leistungsbericht

    lead = Lead(company_name=BETRIEB_NAME)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    kennung = lead.id
    try:
        yield kennung
    finally:
        db.query(Leistungsbericht).filter(Leistungsbericht.lead_id == kennung).delete()
        db.query(AboVertrag).filter(AboVertrag.lead_id == kennung).delete()
        db.query(AuditResult).filter(AuditResult.lead_id == kennung).delete()
        db.query(Lead).filter(Lead.id == kennung).delete()
        db.commit()


# ── Ablage ───────────────────────────────────────────────────────────

def test_ein_monat_ergibt_eine_zeile_auch_beim_zweiten_lauf(db, betrieb):
    """Sonst stünde derselbe Monat zweimal im Verlauf."""
    # Arrange & Act
    leistungsbericht.schreibe(db, lead_id=betrieb, monat="2026-09", mobile=61)
    zeile = leistungsbericht.schreibe(db, lead_id=betrieb, monat="2026-09", mobile=74)

    # Assert
    assert zeile.mobile == 74
    assert len(leistungsbericht.verlauf(db, betrieb)) == 1


def test_ein_erfolgreicher_versand_bleibt_vermerkt(db, betrieb):
    """Läuft der Job im selben Monat noch einmal und scheitert die Mail, wäre
    es falsch, den Kunden nachträglich als unbenachrichtigt zu führen."""
    # Arrange
    leistungsbericht.schreibe(db, lead_id=betrieb, monat="2026-09", mobile=61, versendet=True)

    # Act
    zeile = leistungsbericht.schreibe(db, lead_id=betrieb, monat="2026-09", mobile=74, versendet=False)

    # Assert
    assert zeile.versendet is True


def test_eine_fehlende_messung_ist_nicht_null_punkte(db, betrieb):
    """Dieselbe Regel wie im Audit (§ 3.5): Nicht erhoben ist kein Ergebnis."""
    # Arrange & Act
    leistungsbericht.schreibe(db, lead_id=betrieb, monat="2026-09", mobile=None)

    # Assert
    assert leistungsbericht.letzter(db, betrieb)["mobile"] is None


def test_ein_krummer_monat_wird_abgewiesen(db, betrieb):
    """`September 2026` in dieser Spalte sortiert falsch — und das fällt erst
    auf, wenn ein Verlauf durcheinandersteht."""
    with pytest.raises(leistungsbericht.MonatFehler):
        leistungsbericht.schreibe(db, lead_id=betrieb, monat="September 2026", mobile=61)


# ── Verlauf ──────────────────────────────────────────────────────────

def test_der_verlauf_rechnet_die_richtung_aus_zwei_zeilen(db, betrieb):
    """Sie steht **nicht** in einer Zeile: Wird ein Monat nachgetragen, wäre
    eine gespeicherte Richtung ab dann falsch."""
    # Arrange
    for monat, wert in (("2026-07", 61), ("2026-08", 68), ("2026-09", 74)):
        leistungsbericht.schreibe(db, lead_id=betrieb, monat=monat, mobile=wert)

    # Act
    reihe = leistungsbericht.verlauf(db, betrieb)

    # Assert — jüngster zuerst.
    assert [z["monat"] for z in reihe] == ["2026-09", "2026-08", "2026-07"]
    assert reihe[0]["unterschied"] == 6
    assert reihe[1]["unterschied"] == 7
    # Der älteste hat keinen Vormonat in der Liste — und keinen gespeicherten.
    assert reihe[2]["unterschied"] is None


def test_ohne_vormonat_greift_der_gespeicherte_wert(db, betrieb):
    """Der Job kennt den Vormonat, auch wenn dessen Zeile fehlt — etwa beim
    ersten Lauf nach der Umstellung."""
    # Arrange
    leistungsbericht.schreibe(db, lead_id=betrieb, monat="2026-09", mobile=74,
                              vormonat_mobile=68)

    # Act & Assert
    assert leistungsbericht.verlauf(db, betrieb)[0]["unterschied"] == 6


def test_ohne_berichte_ist_der_verlauf_leer_und_kein_fehler(db, betrieb):
    assert leistungsbericht.verlauf(db, betrieb) == []
    assert leistungsbericht.letzter(db, betrieb) is None


# ── Nächste Prüfung ──────────────────────────────────────────────────

def test_ohne_abo_gibt_es_keinen_termin(db, betrieb):
    """Ein Re-Audit-Datum ohne Vertrag wäre eine Zusage, die niemand gegeben hat."""
    assert quartals_reaudit.naechste_pruefung(db, betrieb) is None


def test_der_takt_haengt_am_abo_und_nicht_am_kalender(db, betrieb):
    """ABO-BAS ist jährlich dran, ABO-PRO vierteljährlich — korrigiert am
    01.09.2026 am Produktdatenblatt."""
    # Arrange
    jetzt = datetime(2026, 9, 4)
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS", start_monat="2026-01")

    # Act
    stand = quartals_reaudit.naechste_pruefung(db, betrieb, jetzt)

    # Assert
    assert stand["produkt"] == "ABO-BAS"
    assert stand["takt_monate"] == 12


def test_ohne_erste_pruefung_ist_sie_sofort_faellig(db, betrieb):
    """Sonst wartet ein Betrieb ein Jahr auf die erste Leistung, für die er zahlt."""
    # Arrange
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS", start_monat="2026-01")

    # Act
    stand = quartals_reaudit.naechste_pruefung(db, betrieb, datetime(2026, 9, 4))

    # Assert
    assert stand["letzte_pruefung"] is None
    assert stand["ist_faellig"] is True


def test_nach_einer_pruefung_zaehlt_der_takt_ab_ihr(db, betrieb):
    # Arrange
    from database import AuditResult
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO", start_monat="2026-01")
    jetzt = datetime(2026, 9, 4)
    # `website_url` ist Pflicht — eine Pruefung ohne Adresse gibt es nicht.
    db.add(AuditResult(lead_id=betrieb, status="completed",
                       website_url="https://tischlerei-nur-im-test.example",
                       company_name=BETRIEB_NAME,
                       created_at=jetzt - timedelta(days=20)))
    db.commit()

    # Act
    stand = quartals_reaudit.naechste_pruefung(db, betrieb, jetzt)

    # Assert — drei Monate nach der Prüfung, also noch nicht fällig.
    assert stand["ist_faellig"] is False
    assert stand["faellig_ab"].startswith("2026-11")
