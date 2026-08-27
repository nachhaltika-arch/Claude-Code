# -*- coding: utf-8 -*-
"""Die ganze Kette, einmal am Stück: hin, zurück, und wieder hin.

**Warum zusätzlich zu den Einzeltests.** Jedes Glied dieser Kette hat seinen
eigenen Test, und am 26.08. waren alle grün — während die Kette selbst
unterbrochen war: Die ausgehende Mail trug keinen `Reply-To`, also führte
nichts zum Posteingang. Kein Einzeltest konnte das sehen, weil keiner zwei
Glieder gleichzeitig anfasst.

Das ist die Bauart, die in diesem Bestand am häufigsten Geld kostet: fünf
fertige Teile und keine Verbindung. Dieser Test fasst sie zusammen und geht
den Weg, den eine echte Rückfrage geht:

1. Der Innendienst schreibt dem Betrieb per E-Mail.
2. Die Mail trägt eine Rückadresse — sonst endet die Kette hier.
3. Der Kunde antwortet; Brevo liefert die Antwort am Posteingang ab.
4. Die Antwort steht im Verlauf des Betriebs, den der Innendienst liest.
5. Die Glocke meldet sie.
6. Der Innendienst antwortet darauf — und der Kunde sieht es im Portal.

**Kein Mock der eigenen Bausteine.** Abgefangen wird genau eine Stelle:
`httpx.post` in `brevo_mail` — der letzte Punkt vor dem Netz. Alles darüber
ist echter Code, und deshalb sieht dieser Test die Kopfzeile `Reply-To` und
nicht nur den Rumpf.
"""
import inspect

import pytest

from services import antwortadresse

GEHEIMNIS = "pytest-posteingang-geheimnis"
ADRESSE = "chef@pytest-kette.de"


@pytest.fixture()
def kette(app, monkeypatch):
    """Ein Betrieb, eine eingerichtete Rückadresse, ein offener Posteingang."""
    from database import Benachrichtigung, Lead, Message, SessionLocal

    monkeypatch.setenv(antwortadresse.SCHALTER, "posteingang@kompagnon.group")
    monkeypatch.setenv("BREVO_INBOUND_SECRET", GEHEIMNIS)

    db = SessionLocal()
    try:
        lead = Lead(company_name="Pytest Kettenbetrieb", email=ADRESSE)
        db.add(lead)
        db.commit()
        kennung = lead.id
    finally:
        db.close()

    yield kennung

    db = SessionLocal()
    try:
        db.query(Message).filter(Message.lead_id == kennung).delete()
        db.query(Benachrichtigung).filter(
            Benachrichtigung.lead_id == kennung).delete()
        db.query(Lead).filter(Lead.id == kennung).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def briefkasten(monkeypatch):
    """Fängt den Versand ab — **an der Leitung, nicht an `send_email`**.

    Der erste Anlauf ersetzte `send_email` und sah damit nur Empfänger,
    Betreff und Rumpf. Genau das reicht hier nicht: Der Bruch vom 27.08. lag
    in der **Kopfzeile** `Reply-To`, und die entsteht erst weiter unten. Ein
    Doppel auf der falschen Ebene hätte den Bruch nicht bemerkt — und der
    Test hätte behauptet, die Kette halte.

    Abgefangen wird deshalb `httpx.post` in `brevo_mail`: der letzte Punkt
    vor dem Netz. Alles darüber ist echter Code.
    """
    from services import brevo_mail

    monkeypatch.setenv("BREVO_API_KEY", "pytest-brevo")
    gesendet = []

    class _Antwort:
        status_code = 201

        @staticmethod
        def json():
            return {}

    def _post(url, json=None, headers=None, timeout=None):
        gesendet.append(json or {})
        return _Antwort()

    assert (inspect.signature(_post).parameters.keys()
            >= {"url", "json"}), "Das Doppel passt nicht auf httpx.post"
    monkeypatch.setattr(brevo_mail.httpx, "post", _post)
    return gesendet


def test_die_kette_haelt_von_der_frage_bis_zur_antwort(
        client, auth_headers, mitarbeiter_headers, kette, briefkasten):
    from database import Benachrichtigung, SessionLocal

    # ── 1. Der Innendienst fragt per Mail ────────────────────────────
    hin = client.post(f"/api/messages/{kette}",
                      json={"content": "Bitte bestätigen Sie den Termin.",
                            "subject": "Terminbestätigung",
                            "channel": "email"},
                      headers=auth_headers)
    assert hin.status_code == 200, hin.text[:300]
    assert len(briefkasten) == 1, "Die Frage ging gar nicht hinaus"
    assert briefkasten[0]["to"] == [{"email": ADRESSE}]

    # ── 2. Und die Mail nennt einen Weg zurück ───────────────────────
    #
    # Der Punkt, an dem die Kette bis zum 27.08.2026 riss. Zuerst der Satz
    # unter der Mail — er darf nur dastehen, wenn der Weg auch existiert.
    assert "direkt auf diese E-Mail" in briefkasten[0]["htmlContent"]

    # **Die eigentliche Verbindung.** Nicht der Satz im Rumpf, sondern die
    # Kopfzeile, der das Mailprogramm des Kunden folgt. Bis zum 27.08.2026
    # stand hier nichts — und genau deshalb kam am Posteingang nie etwas an.
    assert briefkasten[0].get("replyTo") == {
        "email": antwortadresse.rueckadresse()}, briefkasten[0].get("replyTo")

    # ── 3. Der Kunde antwortet, Brevo liefert ab ─────────────────────
    zurueck = client.post(f"/api/posteingang/brevo/{GEHEIMNIS}", json={
        "items": [{
            "From": {"Address": ADRESSE, "Name": "Chef Meier"},
            "Subject": "Re: Terminbestätigung",
            "RawTextBody": "Dienstag passt uns gut.",
        }],
    })
    assert zurueck.status_code == 200, zurueck.text[:300]
    assert zurueck.json()["verarbeitet"] == 1

    # ── 4. Sie steht im Verlauf, den der Innendienst liest ───────────
    #
    # Bewusst mit den Kopfzeilen des **Mitarbeiters**: Die Rolle ist neu, und
    # ein Verlauf, den nur der Admin sieht, wäre keine Anbindung.
    verlauf = client.get(f"/api/messages/{kette}", headers=mitarbeiter_headers)
    assert verlauf.status_code == 200, verlauf.text[:300]
    eintraege = verlauf.json()
    antworten = [m for m in eintraege if m["sender_role"] == "kunde"]
    assert len(antworten) == 1, f"{len(antworten)} Kundenantworten im Verlauf"
    assert antworten[0]["content"] == "Dienstag passt uns gut."
    assert antworten[0]["channel"] == "email"

    # ── 5. Die Glocke hat sie gemeldet ───────────────────────────────
    db = SessionLocal()
    try:
        meldungen = (db.query(Benachrichtigung)
                       .filter(Benachrichtigung.lead_id == kette,
                               Benachrichtigung.art == "mail")
                       .count())
    finally:
        db.close()
    assert meldungen == 1, f"{meldungen} Meldungen statt einer"

    # ── 6. Der Mitarbeiter antwortet, der Kunde sieht es ─────────────
    briefkasten.clear()
    rueck = client.post(f"/api/messages/{kette}",
                        json={"content": "Dann Dienstag 9 Uhr.",
                              "channel": "in_app"},
                        headers=mitarbeiter_headers)
    assert rueck.status_code == 200, rueck.text[:300]

    # Der Hinweis geht hinaus, ohne den Text mitzunehmen.
    assert len(briefkasten) == 1
    assert "Dann Dienstag 9 Uhr" not in briefkasten[0]["htmlContent"]

    # Und im Portal steht die Antwort vollständig.
    from database import Lead, SessionLocal as S2

    db = S2()
    try:
        token = db.query(Lead).filter(Lead.id == kette).first().customer_token
    finally:
        db.close()

    portal = client.get(f"/api/messages/{kette}/kunde"
                        + (f"?token={token}" if token else ""),
                        headers=auth_headers)
    assert portal.status_code == 200, portal.text[:300]
    texte = [m["content"] for m in portal.json()]
    assert "Dann Dienstag 9 Uhr." in texte


def test_ohne_rueckadresse_verspricht_die_mail_den_weg_nicht(
        client, auth_headers, kette, briefkasten, monkeypatch):
    """Die Gegenprobe zu Schritt 2.

    Ohne sie wäre der Test oben auch dann grün, wenn der Satz immer
    dastünde — und genau das war der Zustand, der die Kette riss.
    """
    monkeypatch.delenv(antwortadresse.SCHALTER, raising=False)

    client.post(f"/api/messages/{kette}",
                json={"content": "Frage", "subject": "Frage",
                      "channel": "email"},
                headers=auth_headers)

    assert "direkt auf diese E-Mail" not in briefkasten[0]["htmlContent"]
