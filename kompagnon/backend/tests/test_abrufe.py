# -*- coding: utf-8 -*-
"""Bezahlte Leistungen abrufen (L-160 Rang 6, der letzte Rang).

**Der Befund.** Zwei Positionen des Leistungsverzeichnisses kann der Kunde
**nicht anfordern**, obwohl er sie monatlich bezahlt: die Ruecksicherung
(Position 3) und die eine neue Unterseite im Jahr (Position 12, nur PRO).
„Selten gebraucht, aber im Ernstfall dringend — und dann sucht niemand nach
der Telefonnummer."

**Warum die Stoerungsmeldung ausdruecklich kein Abruf ist.** Fuer sie gibt es
den Support, und seit L-160 Rang 3 steht die zugesagte Reaktionszeit ueber dem
Formular. Ein zweiter Knopf, der dasselbe Ticket anlegt, waere ein zweiter Weg
zur selben Sache — genau die Doppelung, die dieses Projekt an anderer Stelle
teuer bezahlt hat.

**Der Abruf loest nichts aus, er meldet an.** Eine Ruecksicherung ist
Handarbeit am Datenbestand (`docs/sicherung-und-wiederherstellung.md`); sie auf
Knopfdruck zu starten waere die gefaehrlichste Automatik im Haus. Was hier
entsteht, ist der Eingang — mit Zeitpunkt, damit die zugesagte Reaktionszeit
nachweisbar ist.
"""
import pytest


@pytest.fixture
def mit_abo(app, kunde_user):
    from datetime import datetime

    from database import AboVertrag, SessionLocal
    from services import abo_vertrag

    db = SessionLocal()
    try:
        db.query(AboVertrag).filter(AboVertrag.lead_id == kunde_user.lead_id).delete()
        db.commit()
        abo_vertrag.anlegen(db, lead_id=kunde_user.lead_id, produkt="ABO-PRO",
                            start_monat=datetime.utcnow().strftime("%Y-%m"),
                            wer="test@kompagnon.eu")
    finally:
        db.close()
    yield kunde_user.lead_id
    db = SessionLocal()
    try:
        from sqlalchemy import text
        db.query(AboVertrag).filter(AboVertrag.lead_id == kunde_user.lead_id).delete()
        db.execute(text("DELETE FROM abrufe WHERE lead_id = :l"),
                   {"l": kunde_user.lead_id})
        db.commit()
    finally:
        db.close()


# ── Der Katalog ───────────────────────────────────────────────────────

def test_nur_zwei_positionen_sind_abrufbar():
    """Und die Stoerung ist keine davon — dafuer gibt es den Support."""
    from services import leistungsverzeichnis as lv

    abrufbar = [p.nummer for p in lv.KATALOG if p.abruf]

    assert set(abrufbar) == {3, 12}


def test_jeder_abruf_traegt_seinen_knopftext_und_was_danach_geschieht():
    from services import leistungsverzeichnis as lv

    for p in (lv.NACH_NUMMER[3], lv.NACH_NUMMER[12]):
        assert p.abruf and len(p.abruf) > 5
        assert p.abruf_danach and len(p.abruf_danach) > 15, (
            f"Position {p.nummer} sagt nicht, was nach dem Klick geschieht")


# ── Der Weg durch das Portal ──────────────────────────────────────────

def test_ohne_abo_gibt_es_nichts_abzurufen(client, kunde_headers):
    from database import AboVertrag, SessionLocal

    db = SessionLocal()
    try:
        db.query(AboVertrag).delete(); db.commit()
    finally:
        db.close()

    d = client.get("/api/portal/abrufe", headers=kunde_headers).json()

    assert d["abrufe"] == [], "eine Leistung ohne Vertrag hat niemand zugesagt"


def test_mit_pro_stehen_beide_abrufe_bereit(client, kunde_headers, mit_abo):
    d = client.get("/api/portal/abrufe", headers=kunde_headers).json()

    nummern = {a["nummer"] for a in d["abrufe"]}
    assert nummern == {3, 12}
    for a in d["abrufe"]:
        assert a["offen"] is False
        assert a["knopf"] and a["titel"]


def test_basic_bekommt_die_unterseite_nicht(client, kunde_headers, kunde_user):
    """Position 12 gehoert zu PRO. Sie einem Basic-Kunden anzubieten waere
    eine Zusage, die sein Vertrag nicht kennt."""
    from datetime import datetime

    from database import AboVertrag, SessionLocal
    from services import abo_vertrag

    db = SessionLocal()
    try:
        db.query(AboVertrag).filter(AboVertrag.lead_id == kunde_user.lead_id).delete()
        db.commit()
        abo_vertrag.anlegen(db, lead_id=kunde_user.lead_id, produkt="ABO-BAS",
                            start_monat=datetime.utcnow().strftime("%Y-%m"),
                            wer="test@kompagnon.eu")
    finally:
        db.close()

    d = client.get("/api/portal/abrufe", headers=kunde_headers).json()
    assert {a["nummer"] for a in d["abrufe"]} == {3}

    antwort = client.post("/api/portal/abrufe/12", headers=kunde_headers, json={})
    assert antwort.status_code == 403

    db = SessionLocal()
    try:
        db.query(AboVertrag).filter(AboVertrag.lead_id == kunde_user.lead_id).delete()
        db.commit()
    finally:
        db.close()


def test_ein_abruf_wird_festgehalten_und_loest_nichts_aus(client, kunde_headers,
                                                          mit_abo):
    """**Der Kern.** Eine Ruecksicherung auf Knopfdruck waere die
    gefaehrlichste Automatik im Haus. Der Abruf meldet an; die Arbeit macht
    ein Mensch."""
    antwort = client.post("/api/portal/abrufe/3", headers=kunde_headers,
                          json={"notiz": "Seit heute früh fehlen die Bilder"})

    assert antwort.status_code == 200
    d = antwort.json()
    assert d["angefordert_am"]
    assert d["danach"], "der Kunde muss lesen, was jetzt passiert"

    stand = client.get("/api/portal/abrufe", headers=kunde_headers).json()
    sicherung = next(a for a in stand["abrufe"] if a["nummer"] == 3)
    assert sicherung["offen"] is True


def test_ein_zweiter_klick_legt_keinen_zweiten_fall_an(client, kunde_headers,
                                                       mit_abo):
    """Sonst stuenden beim Innendienst zwei Anforderungen fuer dieselbe Sache,
    und die zugesagte Reaktionszeit haette zwei Anfangszeitpunkte."""
    erst = client.post("/api/portal/abrufe/3", headers=kunde_headers, json={}).json()
    nochmal = client.post("/api/portal/abrufe/3", headers=kunde_headers, json={}).json()

    assert erst["angefordert_am"] == nochmal["angefordert_am"]


def test_eine_unbekannte_position_wird_abgewiesen(client, kunde_headers, mit_abo):
    assert client.post("/api/portal/abrufe/1", headers=kunde_headers,
                       json={}).status_code == 400
    assert client.post("/api/portal/abrufe/999", headers=kunde_headers,
                       json={}).status_code == 404
