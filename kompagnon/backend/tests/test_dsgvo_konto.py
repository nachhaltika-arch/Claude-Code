# -*- coding: utf-8 -*-
"""Auskunft und Loeschung im Kundenkonto (L-160 Rang 5).

**Der Befund.** Beides ist ein **gesetzlicher Anspruch** — Art. 15 und Art. 17
DSGVO —, und beides ging bisher nur ueber eine Mail an uns. Wer sie nicht
beantwortet bekommt, hat einen Verstoss in der Hand und keine Spur, dass er
gefragt hat.

**Die Loeschung wird beantragt, nicht ausgefuehrt** — Entwurf
`kundenkonto-neu`. Drei Dinge stehen ihr im Weg, und sie sind **ungleich**:

* Das **Abo** ist ein Vertrag. Solange es laeuft, kann das Konto nicht weg —
  es ist die Grundlage der Abbuchung. Das ist eine harte Sperre.
* Das **Hosting** ist Position 1 des Leistungsverzeichnisses: Mit dem Konto
  endet es, und die Website ist offline. Das ist eine Warnung, keine Sperre.
* Die **Rechnungen** bleiben zehn Jahre. Das ist keine Weigerung, sondern
  § 147 AO — und steht deshalb dabei, statt verschwiegen zu werden.

**Warum ein Antrag und keine sofortige Loeschung.** Eine Loeschung, die sofort
greift, ist bei einem Betrieb ohne zweiten Zugang ein Ausfall ohne Rueckweg.
Und die Frist aus Art. 12 (ein Monat) laesst sich nur belegen, wenn der
Eingang irgendwo steht.
"""
import pytest


# ── Art. 15: Auskunft ─────────────────────────────────────────────────

def test_die_datenkopie_nennt_was_gespeichert_ist(client, kunde_headers, kunde_user):
    antwort = client.get("/api/portal/datenkopie", headers=kunde_headers)

    assert antwort.status_code == 200
    d = antwort.json()
    assert d["konto"]["email"] == kunde_user.email
    assert "betrieb" in d and "bereiche" in d
    # **Jeder Bereich sagt, wie viele Zeilen er hat** — auch die leeren.
    # Eine Auskunft, die nur Gefundenes nennt, beantwortet die Frage nicht:
    # „Was habt ihr ueber mich?" schliesst „nichts in diesem Bereich" ein.
    for bereich in d["bereiche"]:
        assert "titel" in bereich and "anzahl" in bereich


def test_die_datenkopie_traegt_kein_kennwort(client, kunde_headers):
    """Sie wird heruntergeladen, weitergeschickt und liegt danach irgendwo."""
    roh = client.get("/api/portal/datenkopie", headers=kunde_headers).text.lower()

    for verboten in ("password_hash", "totp_secret", "backup_codes",
                     "password_reset_token"):
        assert verboten not in roh, f"{verboten} steht in der Datenkopie"


def test_niemand_bekommt_die_kopie_eines_fremden_betriebs(client, kunde_headers,
                                                          fremder_betrieb):
    """Der Betrieb kommt aus der Anmeldung — es gibt keinen Parameter dafuer."""
    d = client.get("/api/portal/datenkopie", headers=kunde_headers).json()

    assert d["betrieb"].get("id") != fremder_betrieb


# ── Art. 17: Loeschung ────────────────────────────────────────────────

def test_die_huerden_stehen_da_bevor_jemand_klickt(client, kunde_headers):
    antwort = client.get("/api/portal/loeschung", headers=kunde_headers)

    assert antwort.status_code == 200
    d = antwort.json()
    titel = [h["titel"] for h in d["huerden"]]
    assert any("Abo" in t for t in titel)
    assert any("Rechnungen" in t for t in titel)
    for h in d["huerden"]:
        assert len(h["dazu"]) > 30, f"{h['titel']} erklärt nichts"


def test_die_rechnungspflicht_ist_keine_huerde_sondern_eine_auskunft(
        client, kunde_headers):
    """**§ 147 AO ist keine Weigerung.** Sie als Hindernis darzustellen, das
    man ausraeumen kann, waere falsch — sie bleibt, und der Kunde soll das
    vorher wissen statt hinterher."""
    d = client.get("/api/portal/loeschung", headers=kunde_headers).json()

    rechnungen = next(h for h in d["huerden"] if "Rechnungen" in h["titel"])
    assert rechnungen["ausraeumbar"] is False
    assert rechnungen["erfuellt"] is None, "weder erfüllt noch offen — sie gilt"


def test_ohne_gekuendigtes_abo_ist_der_antrag_gesperrt(client, kunde_headers,
                                                       kunde_user):
    from datetime import datetime

    from database import SessionLocal
    from services import abo_vertrag

    db = SessionLocal()
    try:
        abo_vertrag.anlegen(db, lead_id=kunde_user.lead_id, produkt="ABO-BAS",
                            start_monat=datetime.utcnow().strftime("%Y-%m"),
                            wer="test@kompagnon.eu")
    finally:
        db.close()

    stand = client.get("/api/portal/loeschung", headers=kunde_headers).json()
    assert stand["moeglich"] is False
    assert stand["sperrgrund"]

    antwort = client.post("/api/portal/loeschung", headers=kunde_headers,
                          json={"bestaetigung": "LÖSCHEN", "verstanden": True})
    assert antwort.status_code == 409, (
        "solange das Abo läuft, ist es die Grundlage der Abbuchung")

    from database import AboVertrag
    db = SessionLocal()
    try:
        db.query(AboVertrag).filter(AboVertrag.lead_id == kunde_user.lead_id).delete()
        db.commit()
    finally:
        db.close()


def test_ein_antrag_braucht_wort_und_haekchen(client, kunde_headers):
    """Zwei Hürden, weil ein Klick zu wenig ist für etwas Unumkehrbares."""
    ohne_wort = client.post("/api/portal/loeschung", headers=kunde_headers,
                            json={"bestaetigung": "ja", "verstanden": True})
    assert ohne_wort.status_code == 400

    ohne_haken = client.post("/api/portal/loeschung", headers=kunde_headers,
                             json={"bestaetigung": "LÖSCHEN", "verstanden": False})
    assert ohne_haken.status_code == 400


def test_der_antrag_wird_festgehalten_und_nicht_ausgefuehrt(client, kunde_headers,
                                                            kunde_user):
    """**Der Kern.** Die Loeschung geschieht nicht hier — sie wird beantragt.
    Was hier entsteht, ist der **Nachweis** des Eingangs; die Frist aus
    Art. 12 laeuft ab diesem Zeitpunkt."""
    from database import SessionLocal, User

    antwort = client.post("/api/portal/loeschung", headers=kunde_headers,
                          json={"bestaetigung": "löschen", "verstanden": True})

    assert antwort.status_code == 200
    d = antwort.json()
    assert d["beantragt_am"]
    assert d["frist_bis"], "Art. 12 verlangt eine Antwort binnen eines Monats"

    db = SessionLocal()
    try:
        # Das Konto steht noch — beantragt ist nicht gelöscht.
        assert db.query(User).filter(User.id == kunde_user.id).first() is not None
        db.execute(__import__("sqlalchemy").text(
            "DELETE FROM loeschantraege WHERE lead_id = :l"),
            {"l": kunde_user.lead_id})
        db.commit()
    finally:
        db.close()


def test_ein_zweiter_antrag_verschiebt_die_frist_nicht(client, kunde_headers,
                                                       kunde_user):
    """Sonst koennte ein zweiter Klick die Monatsfrist immer wieder neu
    starten — zu unseren Gunsten, und niemand saehe es."""
    erst = client.post("/api/portal/loeschung", headers=kunde_headers,
                       json={"bestaetigung": "LÖSCHEN", "verstanden": True}).json()
    nochmal = client.post("/api/portal/loeschung", headers=kunde_headers,
                          json={"bestaetigung": "LÖSCHEN", "verstanden": True}).json()

    assert erst["beantragt_am"] == nochmal["beantragt_am"]

    from sqlalchemy import text
    from database import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM loeschantraege WHERE lead_id = :l"),
                   {"l": kunde_user.lead_id})
        db.commit()
    finally:
        db.close()
