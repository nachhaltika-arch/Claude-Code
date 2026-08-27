# -*- coding: utf-8 -*-
"""`/health` sagt, ob Geld ankommen kann — ohne ein Geheimnis zu verraten.

**Der Anlass (27.08.2026).** Beim Einrichten der drei Stripe-Adressen ging
eine Stunde verloren mit der Frage, ob die Signaturgeheimnisse im laufenden
Prozess ankommen. Das Render-Dashboard zeigt eine Zeile mit leerem Wert
genauso an wie eine mit Inhalt — beide als Punkte. Die Protokolle sagten
„nicht gesetzt", der Bildschirm sagte „steht da", und dazwischen gab es
niemanden, den man haette fragen koennen.

**Die gefaehrlichste Zusicherung in dieser Datei ist die letzte.** Eine
Auskunft ueber Geheimnisse, die aus Versehen das Geheimnis ausgibt, ist
schlimmer als gar keine Auskunft — sie steht auf einem offenen Endpunkt.
"""
def _zustand(monkeypatch, **werte):
    """Der Zustand bei genau dieser Umgebung."""
    import main

    for name in main._ZAHLUNGSWERTE:
        monkeypatch.delenv(name, raising=False)
    for name, wert in werte.items():
        monkeypatch.setenv(name, wert)
    return main._zahlungszustand()


# ── Was gemeldet wird ─────────────────────────────────────────────────

def test_ein_leerer_wert_gilt_als_nicht_gesetzt(monkeypatch):
    """**Der Befund selbst.** Genau diesen Zustand konnte niemand sehen: Die
    Zeile war da, der Wert war leer, und das Dashboard zeigte beides gleich."""
    z = _zustand(monkeypatch, STRIPE_WEBHOOK_SECRET="")

    assert z["STRIPE_WEBHOOK_SECRET"]["gesetzt"] is False
    assert z["STRIPE_WEBHOOK_SECRET"]["laenge"] == 0


def test_auch_ein_wert_aus_leerzeichen(monkeypatch):
    """Ein versehentlich kopiertes Leerzeichen ist kein Geheimnis."""
    z = _zustand(monkeypatch, STRIPE_WEBHOOK_SECRET="   ")

    assert z["STRIPE_WEBHOOK_SECRET"]["gesetzt"] is False


def test_die_laenge_unterscheidet_abgeschnitten_von_vollstaendig(monkeypatch):
    """Ohne sie sehen „whs" und ein vollstaendiges Geheimnis gleich aus."""
    z = _zustand(monkeypatch, STRIPE_WEBHOOK_SECRET="whsec_" + "x" * 32)

    assert z["STRIPE_WEBHOOK_SECRET"]["gesetzt"] is True
    assert z["STRIPE_WEBHOOK_SECRET"]["laenge"] == 38


def test_ein_vertauschter_wert_faellt_auf(monkeypatch):
    """Wer API-Schluessel und Signaturgeheimnis vertauscht, saehe sonst zwei
    gesetzte Werte und einen Fehler ohne Ursache."""
    z = _zustand(monkeypatch, STRIPE_WEBHOOK_SECRET="rk_test_abc",
                 STRIPE_SECRET_KEY="whsec_abc")

    assert z["STRIPE_WEBHOOK_SECRET"]["praefix_stimmt"] is False
    assert z["STRIPE_SECRET_KEY"]["praefix_stimmt"] is False
    assert z["bereit"] is False


def test_beide_schluesselarten_gelten(monkeypatch):
    """Der eingeschraenkte Schluessel beginnt mit `rk_`, der volle mit `sk_`.
    Beide sind gueltig — nur einer davon abzunicken waere ein Fehlalarm."""
    for praefix in ("sk_test_x", "rk_test_x"):
        z = _zustand(monkeypatch, STRIPE_SECRET_KEY=praefix)
        assert z["STRIPE_SECRET_KEY"]["praefix_stimmt"] is True, praefix


def test_bereit_nur_wenn_alle_vier_stehen(monkeypatch):
    z = _zustand(monkeypatch,
                 STRIPE_SECRET_KEY="rk_test_" + "x" * 20,
                 STRIPE_WEBHOOK_SECRET="whsec_" + "a" * 32,
                 STRIPE_WEBHOOK_SECRET_BUCH="whsec_" + "b" * 32,
                 STRIPE_WEBHOOK_SECRET_GEO="whsec_" + "c" * 32)

    assert z["bereit"] is True


def test_und_nicht_wenn_einer_fehlt(monkeypatch):
    """Die Gegenprobe. Ohne sie waere `bereit` auch dann wahr, wenn es immer
    wahr waere — und dann glaubt ihm niemand mehr."""
    z = _zustand(monkeypatch,
                 STRIPE_SECRET_KEY="rk_test_" + "x" * 20,
                 STRIPE_WEBHOOK_SECRET="whsec_" + "a" * 32,
                 STRIPE_WEBHOOK_SECRET_BUCH="whsec_" + "b" * 32)

    assert z["bereit"] is False
    assert z["STRIPE_WEBHOOK_SECRET_GEO"]["gesetzt"] is False


def test_jede_adresse_ist_benannt(monkeypatch):
    """Wer liest, welcher Wert fehlt, muss wissen, wohin er gehoert —
    sonst traegt er ihn in die naechstbeste Zeile ein. Genau das ist die
    Verwechslung, die den Buchpfad taub gemacht haette (L-138)."""
    z = _zustand(monkeypatch)

    assert z["STRIPE_WEBHOOK_SECRET"]["wofuer"] == "/api/payments/webhook"
    assert z["STRIPE_WEBHOOK_SECRET_BUCH"]["wofuer"] == "/api/book/webhook"
    assert z["STRIPE_WEBHOOK_SECRET_GEO"]["wofuer"] == "/api/geo-payments/webhook"


# ── Und was nicht gemeldet wird ───────────────────────────────────────

def test_kein_geheimnis_steht_in_der_auskunft(monkeypatch):
    """**Die wichtigste Zusicherung.** `/health` ist offen; eine Auskunft
    ueber Geheimnisse, die das Geheimnis mitliefert, ist schlimmer als keine.
    """
    geheim = "whsec_diesesGeheimnisDarfNirgendsAuftauchen"

    z = _zustand(monkeypatch, STRIPE_WEBHOOK_SECRET=geheim,
                 STRIPE_SECRET_KEY="rk_test_ebenfallsGeheim")

    text = repr(z)
    assert geheim not in text
    assert "diesesGeheimnis" not in text
    assert "ebenfallsGeheim" not in text
    # Auch kein Anfangsstueck: sechs Zeichen Praefix sind oeffentlich bekannt,
    # alles darueber hinaus waere ein Leck in Scheiben.
    assert geheim[:12] not in text


def test_die_auskunft_haengt_am_endpunkt(monkeypatch):
    """Eine Auskunft, die niemand abrufen kann, ist keine.

    Gemessen am Endpunkt, nicht an der Funktion — genau diese Verwechslung
    hat `/health` am selben Tag schon einmal gekostet (L-136).
    """
    from fastapi.testclient import TestClient
    from main import app

    antwort = TestClient(app).get("/health")

    assert antwort.status_code == 200
    assert "zahlungen" in antwort.json()
    assert "bereit" in antwort.json()["zahlungen"]
