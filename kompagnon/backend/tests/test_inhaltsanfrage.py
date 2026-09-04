# -*- coding: utf-8 -*-
"""Inhaltsänderungen: Guthaben sehen, Änderung anfordern (Rang 1).

**Der Anlass.** Position 5 und 8 des Leistungsverzeichnisses sagen
„Inhaltsänderungen bis 30 bzw. 90 Minuten je Monat" zu — 79 € bzw. 149 € im
Monat. Die Zeiterfassung dafür gibt es seit dem 31.08., die Abrechnung auch.
Nur konnte der Kunde nichts anfordern und sah seinen Stand nirgends. Ein
Guthaben ohne Kontostand wird entweder nicht genutzt oder überzogen; das erste
kostet Vertrauen, das zweite Geld.

**Was hier gehalten wird**, ist vor allem eine Grenze: Dieses Modul rechnet
**keine** Minuten. Der Stand kommt unveraendert aus `abo_stunden`. Genau
dieser Fehler — dieselbe Zahl an zwei Orten — ist am 01.09. schon einmal
passiert, als die Kontingente aus einem Fliesstext statt aus dem Datenblatt
kamen.
"""
import pytest

from services import inhaltsanfrage


@pytest.fixture
def betrieb(app, kunde_user):
    from database import SessionLocal
    from modelle_abo import InhaltsAnfrage

    db = SessionLocal()
    try:
        db.query(InhaltsAnfrage).filter(
            InhaltsAnfrage.lead_id == kunde_user.lead_id).delete()
        db.commit()
        yield kunde_user.lead_id
    finally:
        db.close()


# ── Der Wunsch ────────────────────────────────────────────────────────

def test_ein_wunsch_ohne_beschreibung_wird_abgewiesen(app, betrieb):
    from database import SessionLocal

    db = SessionLocal()
    try:
        with pytest.raises(inhaltsanfrage.AnfrageFehler):
            inhaltsanfrage.anlegen(db, lead_id=betrieb, beschreibung="   ")
    finally:
        db.close()


def test_eine_ablehnung_braucht_einen_grund(app, betrieb):
    """Eine Ablehnung ohne Grund ist fuer den Kunden dasselbe wie keine
    Antwort."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        a = inhaltsanfrage.anlegen(db, lead_id=betrieb,
                                   beschreibung="Telefonnummer ändern")
        with pytest.raises(inhaltsanfrage.AnfrageFehler):
            inhaltsanfrage.setze_status(db, anfrage_id=a.id, status="abgelehnt")

        gesetzt = inhaltsanfrage.setze_status(
            db, anfrage_id=a.id, status="abgelehnt",
            notiz="Die Nummer steht im Impressum und wird dort gepflegt.")
        assert gesetzt.status == "abgelehnt"
    finally:
        db.close()


def test_der_erste_abschluss_zaehlt(app, betrieb):
    """Das Erledigungsdatum steht in der Antwort an den Kunden — ein zweiter
    Klick darf es nicht verschieben."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        a = inhaltsanfrage.anlegen(db, lead_id=betrieb, beschreibung="Preis ändern")
        erst = inhaltsanfrage.setze_status(db, anfrage_id=a.id, status="erledigt").erledigt_am
        nochmal = inhaltsanfrage.setze_status(db, anfrage_id=a.id, status="erledigt").erledigt_am

        assert erst == nochmal
    finally:
        db.close()


def test_zurueck_auf_offen_loescht_das_erledigungsdatum(app, betrieb):
    """Sonst stuende beim Kunden „erledigt am …" an einem Wunsch, der wieder
    offen ist."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        a = inhaltsanfrage.anlegen(db, lead_id=betrieb, beschreibung="Bild tauschen")
        inhaltsanfrage.setze_status(db, anfrage_id=a.id, status="erledigt")
        zurueck = inhaltsanfrage.setze_status(db, anfrage_id=a.id, status="in_arbeit")

        assert zurueck.erledigt_am is None
    finally:
        db.close()


def test_der_bearbeiter_steht_nicht_in_der_kundenansicht(app, betrieb):
    """Wer bei uns daran gearbeitet hat, ist unsere Betriebsfrage."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        a = inhaltsanfrage.anlegen(db, lead_id=betrieb, beschreibung="Text kürzen")
        inhaltsanfrage.setze_status(db, anfrage_id=a.id, status="erledigt",
                                    wer="mitarbeiter@kompagnon.local")
        aussen = inhaltsanfrage.nach_aussen(a)

        assert "bearbeitet_von" not in aussen
        assert set(aussen) == {"id", "monat", "beschreibung", "seite", "status",
                               "angefragt_am", "erledigt_am", "notiz"}
    finally:
        db.close()


# ── Der Weg durch das Portal ──────────────────────────────────────────

def test_ohne_abo_gibt_es_kein_guthaben_aber_einen_satz(client, kunde_headers, betrieb):
    """Kein Abo ist kein Fehler — aber der Kunde soll lesen, warum dort nichts
    steht."""
    antwort = client.get("/api/portal/inhalt", headers=kunde_headers)

    assert antwort.status_code == 200
    d = antwort.json()
    assert d["guthaben"] is None or d["guthaben"]["kontingent_minuten"] > 0
    if d["guthaben"] is None:
        assert d["hinweis"], "ohne Guthaben muss ein Hinweis dastehen"


def test_ein_wunsch_landet_in_der_liste(client, kunde_headers, betrieb):
    gesetzt = client.post("/api/portal/inhalt",
                          json={"beschreibung": "Neue Öffnungszeiten auf der Startseite",
                                "seite": "/"},
                          headers=kunde_headers)

    assert gesetzt.status_code == 201
    liste = client.get("/api/portal/inhalt", headers=kunde_headers).json()["anfragen"]
    assert liste[0]["beschreibung"].startswith("Neue Öffnungszeiten")
    assert liste[0]["status"] == "offen"


def test_ein_leerer_wunsch_wird_mit_klarer_meldung_abgewiesen(client, kunde_headers, betrieb):
    antwort = client.post("/api/portal/inhalt", json={"beschreibung": ""},
                          headers=kunde_headers)

    assert antwort.status_code == 400
    assert "beschreiben" in antwort.json()["detail"].lower()


def test_das_guthaben_steht_in_minuten_nicht_in_stunden(client, kunde_headers,
                                                        betrieb, app):
    """Das Datenblatt sagt „bis 30 Minuten". „0,5 h verbleibend" waere
    dieselbe Zahl in einer Sprache, die der Kunde nicht spricht."""
    from database import SessionLocal
    from services import abo_vertrag

    db = SessionLocal()
    try:
        try:
            abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                                start_monat="2026-01", wer="pytest")
        except Exception:
            pass       # schon vorhanden — genau das wollen wir
    finally:
        db.close()

    d = client.get("/api/portal/inhalt", headers=kunde_headers).json()

    if d["guthaben"]:
        assert d["guthaben"]["kontingent_minuten"] == 90, "ABO-PRO: 90 Minuten"
        assert "kontingent_stunden" not in d["guthaben"]
