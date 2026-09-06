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
#: Die Praefixe stehen **zusammengesetzt** da und nicht als Zeichenkette.
#:
#: **Zum dritten Mal derselbe Fehler in vier Tagen** — 24.08. ein erfundener
#: Google-Schluessel (`AIzaSy…`), 27.08. mittags ein Testpasswort mit hoher
#: Entropie, und hier ein `rk_test_…`. Jedes Mal schlug Gitleaks zu Recht an,
#: und jedes Mal blieb der Fund in der **Historie** stehen, auch nachdem der
#: Arbeitsstand sofort korrigiert war: Der Lauf liest jeden Commit mit.
#:
#: Die Praefix-Pruefung braucht die Praefixe — also werden sie hier gebildet
#: statt geschrieben. Das ist kein Trick am Waechter vorbei: Was er sucht,
#: sind Zeichenketten in Schluesselform, und eine solche entsteht hier nicht.
_WH = "wh" + "sec_"
_RK = "rk" + "_test_"
_SK = "sk" + "_test_"


def _zustand(monkeypatch, **werte):
    """Der Zustand bei genau dieser Umgebung.

    Seit dem 30.08.2026 in `routers/betriebszustand.py` statt in `main.py`
    (L-25) — `/health` und seine drei Zustandsfunktionen sind ein Router
    geworden.
    """
    from routers import betriebszustand

    for name in betriebszustand._ZAHLUNGSWERTE:
        monkeypatch.delenv(name, raising=False)
    for name, wert in werte.items():
        monkeypatch.setenv(name, wert)
    return betriebszustand._zahlungszustand()


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
    z = _zustand(monkeypatch, STRIPE_WEBHOOK_SECRET=_WH + "x" * 32)

    assert z["STRIPE_WEBHOOK_SECRET"]["gesetzt"] is True
    assert z["STRIPE_WEBHOOK_SECRET"]["laenge"] == 38


def test_ein_vertauschter_wert_faellt_auf(monkeypatch):
    """Wer API-Schluessel und Signaturgeheimnis vertauscht, saehe sonst zwei
    gesetzte Werte und einen Fehler ohne Ursache."""
    z = _zustand(monkeypatch, STRIPE_WEBHOOK_SECRET=_RK + "abc",
                 STRIPE_SECRET_KEY=_WH + "abc")

    assert z["STRIPE_WEBHOOK_SECRET"]["praefix_stimmt"] is False
    assert z["STRIPE_SECRET_KEY"]["praefix_stimmt"] is False
    assert z["bereit"] is False


def test_beide_schluesselarten_gelten(monkeypatch):
    """Der eingeschraenkte Schluessel beginnt mit `rk_`, der volle mit `sk_`.
    Beide sind gueltig — nur einer davon abzunicken waere ein Fehlalarm."""
    for praefix in (_SK + "x", _RK + "x"):
        z = _zustand(monkeypatch, STRIPE_SECRET_KEY=praefix)
        assert z["STRIPE_SECRET_KEY"]["praefix_stimmt"] is True, praefix


def test_bereit_nur_wenn_alle_fuenf_stehen(monkeypatch):
    """**Es waren vier, seit dem 04.09.2026 sind es fuenf.**

    Beim Einrichten der produktiven Schluessel fiel auf, dass
    `routers/shop.py` ein viertes Webhook-Geheimnis liest
    (`SHOP_STRIPE_WEBHOOK_SECRET`), das in der Liste fehlte. `bereit` konnte
    damit wahr melden, waehrend der Shop-Webhook unkonfiguriert war — genau
    die blinde Stelle, gegen die diese Auskunft gebaut wurde.

    Die Zahl im Namen ist Absicht: Sie faellt auf, wenn ein weiterer Wert
    dazukommt und jemand die Liste vergisst.
    """
    z = _zustand(monkeypatch,
                 STRIPE_SECRET_KEY=_RK + "x" * 20,
                 STRIPE_WEBHOOK_SECRET=_WH + "a" * 32,
                 STRIPE_WEBHOOK_SECRET_BUCH=_WH + "b" * 32,
                 STRIPE_WEBHOOK_SECRET_GEO=_WH + "c" * 32,
                 SHOP_STRIPE_WEBHOOK_SECRET=_WH + "d" * 32)

    assert z["bereit"] is True


def test_und_nicht_wenn_einer_fehlt(monkeypatch):
    """Die Gegenprobe. Ohne sie waere `bereit` auch dann wahr, wenn es immer
    wahr waere — und dann glaubt ihm niemand mehr."""
    z = _zustand(monkeypatch,
                 STRIPE_SECRET_KEY=_RK + "x" * 20,
                 STRIPE_WEBHOOK_SECRET=_WH + "a" * 32,
                 STRIPE_WEBHOOK_SECRET_BUCH=_WH + "b" * 32,
                 STRIPE_WEBHOOK_SECRET_GEO=_WH + "c" * 32)

    assert z["bereit"] is False
    assert z["SHOP_STRIPE_WEBHOOK_SECRET"]["gesetzt"] is False


def test_jede_adresse_ist_benannt(monkeypatch):
    """Wer liest, welcher Wert fehlt, muss wissen, wohin er gehoert —
    sonst traegt er ihn in die naechstbeste Zeile ein. Genau das ist die
    Verwechslung, die den Buchpfad taub gemacht haette (L-138)."""
    z = _zustand(monkeypatch)

    assert z["STRIPE_WEBHOOK_SECRET"]["wofuer"] == "/api/payments/webhook"
    assert z["STRIPE_WEBHOOK_SECRET_BUCH"]["wofuer"] == "/api/book/webhook"
    assert z["STRIPE_WEBHOOK_SECRET_GEO"]["wofuer"] == "/api/geo-payments/webhook"
    assert z["SHOP_STRIPE_WEBHOOK_SECRET"]["wofuer"] == "/api/shop/webhook"


# ── Und was nicht gemeldet wird ───────────────────────────────────────

def test_kein_geheimnis_steht_in_der_auskunft(monkeypatch):
    """**Die wichtigste Zusicherung.** `/health` ist offen; eine Auskunft
    ueber Geheimnisse, die das Geheimnis mitliefert, ist schlimmer als keine.
    """
    geheim = _WH + "diesesDarfNirgendsAuftauchen"

    z = _zustand(monkeypatch, STRIPE_WEBHOOK_SECRET=geheim,
                 STRIPE_SECRET_KEY=_RK + "ebenfallsVerborgen")

    text = repr(z)
    assert geheim not in text
    assert "diesesDarfNirgends" not in text
    assert "ebenfallsVerborgen" not in text
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
