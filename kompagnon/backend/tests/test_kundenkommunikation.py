# -*- coding: utf-8 -*-
"""Der Innendienst schreibt dem Kunden — und der erfährt davon.

Zwei Befunde vom 27.08.2026, beide beim Durchgehen der Kommunikationskette
nach Davids Bitte, „die kommunikation soweit [zu] entwickeln das wir mit
kunden kommunizieren können".

**Erstens: Nur der Admin durfte antworten.** `GET /api/messages/{lead_id}`
stand auf `require_innendienst`, `POST` daneben auf `require_admin`. Ein
Mitarbeiter KOMPAGNON konnte den Verlauf eines Betriebs **lesen und nicht
beantworten** — und die Oberfläche zeigte ihm das Eingabefeld trotzdem. Mit
der Zusammenlegung der Rollen wäre das die Regel geworden statt die Ausnahme.

**Zweitens: Eine Nachricht im Portal erreichte niemanden.** Wählte der
Innendienst den Weg `in_app`, entstand eine `Message` — und sonst nichts. Die
Glocke meldet nur nach innen; der Kunde erfuhr es erst, wenn er von sich aus
das Portal öffnete. Bei einer Rückfrage, von der der Auftrag abhängt, ist das
kein Kanal, sondern ein Zettel in einer Schublade.

**Warum die Hinweismail den Text nicht mitnimmt.** Wer `in_app` wählt, hat
sich gegen den Mailweg entschieden. Die Mail sagt deshalb nur, *dass* etwas
da ist, und führt ins Portal — sonst wäre die Wahl zwischen den beiden Wegen
ohne Unterschied, und `in_app` verschickte still doch alles.
"""
import pytest

from services import kundenmeldung


@pytest.fixture()
def betrieb(app):
    """Ein Betrieb mit E-Mail-Adresse — sonst gibt es nichts zu melden."""
    from database import Lead, SessionLocal

    db = SessionLocal()
    try:
        lead = Lead(company_name="Pytest Nachrichtenbetrieb",
                    email="chef@pytest-nachrichten.de")
        db.add(lead)
        db.commit()
        kennung = lead.id
    finally:
        db.close()

    yield kennung

    db = SessionLocal()
    try:
        from database import Message

        db.query(Message).filter(Message.lead_id == kennung).delete()
        db.query(Lead).filter(Lead.id == kennung).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def mails(monkeypatch):
    """Fängt jeden Versand ab — mit der **echten** Unterschrift.

    Ein `def merken(**k)` hätte am 26.08. genau den Fehler angenommen, den es
    finden sollte (`attachment_path=` an `send_email`). Die Doppel tragen
    seither die Unterschrift des Originals.
    """
    import inspect

    from services import email as echt

    gesendet = []

    def doppel(to_email: str, subject: str, html_body: str,
               text_body: str = "", db=None, attachments=None) -> bool:
        gesendet.append({"an": to_email, "betreff": subject,
                         "inhalt": html_body})
        return True

    assert (inspect.signature(doppel)
            == inspect.signature(echt.send_email)), (
        "Das Testdoppel weicht von send_email ab")

    monkeypatch.setattr("services.email.send_email", doppel)
    return gesendet


# ── Wer antworten darf ────────────────────────────────────────────────

def test_der_mitarbeiter_darf_dem_kunden_schreiben(client, mitarbeiter_headers,
                                                   betrieb, mails):
    antwort = client.post(f"/api/messages/{betrieb}",
                          json={"content": "Guten Tag", "channel": "in_app"},
                          headers=mitarbeiter_headers)

    assert antwort.status_code == 200, antwort.text[:300]


def test_der_admin_darf_es_weiterhin(client, auth_headers, betrieb, mails):
    """Die Gegenprobe — sonst wäre der Test oben auch grün, wenn die Route
    für alle offen stünde."""
    antwort = client.post(f"/api/messages/{betrieb}",
                          json={"content": "Guten Tag", "channel": "in_app"},
                          headers=auth_headers)

    assert antwort.status_code == 200, antwort.text[:300]


def test_ein_kunde_darf_es_nicht(client, kunde_headers, betrieb, mails):
    """Ein Kunde schreibt über `/kunde` und nicht in fremde Verläufe."""
    antwort = client.post(f"/api/messages/{betrieb}",
                          json={"content": "Fremd", "channel": "in_app"},
                          headers=kunde_headers)

    assert antwort.status_code == 403, antwort.text[:300]


# ── Dass der Kunde davon erfährt ──────────────────────────────────────

def test_eine_portalnachricht_loest_einen_hinweis_aus(client, auth_headers,
                                                      betrieb, mails):
    client.post(f"/api/messages/{betrieb}",
                json={"content": "Bitte um Rückmeldung", "channel": "in_app"},
                headers=auth_headers)

    assert len(mails) == 1, f"{len(mails)} Mails statt einer"
    assert mails[0]["an"] == "chef@pytest-nachrichten.de"


def test_der_hinweis_traegt_den_text_nicht_mit(client, auth_headers,
                                               betrieb, mails):
    """Wer `in_app` wählt, hat sich gegen den Mailweg entschieden."""
    geheim = "Der Preis liegt bei 12.400 Euro"
    client.post(f"/api/messages/{betrieb}",
                json={"content": geheim, "channel": "in_app"},
                headers=auth_headers)

    assert geheim not in mails[0]["inhalt"]
    # Gegenprobe: Ein Weg ins Portal steht drin.
    assert "portal" in mails[0]["inhalt"].lower()


def test_beim_mailweg_geht_der_text_mit_und_kein_zweiter_hinweis(
        client, auth_headers, betrieb, mails):
    """Sonst bekäme der Kunde zwei Mails für eine Nachricht."""
    client.post(f"/api/messages/{betrieb}",
                json={"content": "Ihr Termin am Dienstag", "subject": "Termin",
                      "channel": "email"},
                headers=auth_headers)

    assert len(mails) == 1, f"{len(mails)} Mails statt einer"
    assert "Ihr Termin am Dienstag" in mails[0]["inhalt"]


def test_ohne_adresse_wird_nichts_versendet_und_nichts_verschluckt(
        client, auth_headers, app, mails):
    """Ein Betrieb ohne E-Mail ist kein Fehler — aber auch kein Versand."""
    from database import Lead, Message, SessionLocal

    db = SessionLocal()
    try:
        lead = Lead(company_name="Pytest Ohne Adresse", email=None)
        db.add(lead)
        db.commit()
        kennung = lead.id
    finally:
        db.close()

    antwort = client.post(f"/api/messages/{kennung}",
                          json={"content": "Hallo", "channel": "in_app"},
                          headers=auth_headers)

    assert antwort.status_code == 200, antwort.text[:300]
    assert mails == []

    db = SessionLocal()
    try:
        # Die Nachricht ist trotzdem abgelegt — sie geht nicht verloren,
        # nur der Hinweis entfaellt.
        assert db.query(Message).filter(Message.lead_id == kennung).count() == 1
        db.query(Message).filter(Message.lead_id == kennung).delete()
        db.query(Lead).filter(Lead.id == kennung).delete()
        db.commit()
    finally:
        db.close()


def test_ein_gescheiterter_hinweis_kippt_die_nachricht_nicht(
        client, auth_headers, betrieb, monkeypatch):
    """Die Ablage ist die Hauptsache, die Mail der Hinweis darauf.

    Bricht der Versand, darf die Nachricht nicht mitfallen — sonst kostet ein
    Mailserver-Schluckauf den Verlauf.
    """
    from database import Message, SessionLocal

    def kaputt(*args, **kwargs):
        raise RuntimeError("Mailserver antwortet nicht")

    monkeypatch.setattr("services.email.send_email", kaputt)

    antwort = client.post(f"/api/messages/{betrieb}",
                          json={"content": "Trotzdem da", "channel": "in_app"},
                          headers=auth_headers)

    assert antwort.status_code == 200, antwort.text[:300]

    db = SessionLocal()
    try:
        assert db.query(Message).filter(
            Message.lead_id == betrieb,
            Message.content == "Trotzdem da").count() == 1
    finally:
        db.close()


# ── Der Schalter ──────────────────────────────────────────────────────

def test_der_hinweis_laesst_sich_abschalten(client, auth_headers, betrieb,
                                            mails, app):
    from database import Meldungsvorliebe, SessionLocal

    db = SessionLocal()
    try:
        db.add(Meldungsvorliebe(schluessel=kundenmeldung.SCHLUESSEL,
                               aktiv=False))
        db.commit()
    finally:
        db.close()

    try:
        client.post(f"/api/messages/{betrieb}",
                    json={"content": "Still", "channel": "in_app"},
                    headers=auth_headers)
        assert mails == []
    finally:
        db = SessionLocal()
        try:
            db.query(Meldungsvorliebe).filter(
                Meldungsvorliebe.schluessel == kundenmeldung.SCHLUESSEL).delete()
            db.commit()
        finally:
            db.close()


def test_der_schalter_ist_der_oberflaeche_bekannt():
    """Ein Schalter, den die Einstellungsseite nicht kennt, ist keiner."""
    from services.meldungsvorlieben import EREIGNISSE

    schluessel = {s for s, _, _ in EREIGNISSE}
    assert kundenmeldung.SCHLUESSEL in schluessel
