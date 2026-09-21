# -*- coding: utf-8 -*-
"""`/health` sagt, ob ein Lead ueberhaupt in einer Brevo-Liste landen kann.

**Der Befund vom 17.09.2026.** `widget_crm.uebertrage_anfrage` brach bei
fehlender Listen-ID mit einem blanken `return` ab — das System schwieg
vollstaendig. Zwischen dem 03.09. und 13.09. haben neun Adressen bestaetigt,
darunter zwei echte Interessenten; zu keiner steht eine Brevo-Zeile im
Protokoll, weder Erfolg noch Misserfolg.

Die Stelle warnt seitdem. Das deckt den Fall ab, **in dem jemand ins
Protokoll sieht** — aber die Frage „ist der Weg ueberhaupt eingerichtet?"
war von aussen weiter nicht zu beantworten. Genau diese Luecke haben
`_zahlungszustand` fuer Stripe, `_meta_zustand` fuer den Serverweg und
`_agb_zustand` fuer den Kaufnachweis laengst geschlossen; Brevo fehlte als
einziges — und ausgerechnet dort war der stille Ausfall real.

**Gemeldet wird, ob etwas dasteht, nie was dasteht.** Der Schluessel ist ein
Geheimnis, und `/health` antwortet ohne Anmeldung.
"""
import json

VARIABLEN = ("BREVO_API_KEY", "BREVO_LIST_VERIFIED_ID", "BREVO_LIST_OPTIN_ID")


def _brevo(client):
    daten = client.get("/health").json()
    assert "brevo" in daten, "Der Brevo-Zustand fehlt in /health"
    return daten["brevo"]


def test_health_fuehrt_den_brevo_zustand(client, monkeypatch):
    for name in VARIABLEN:
        monkeypatch.delenv(name, raising=False)

    block = _brevo(client)
    assert set(VARIABLEN) <= set(block["variablen"])
    assert isinstance(block["bereit"], bool)


def test_eingerichtet_meldet_bereit(client, monkeypatch):
    """Die positive Zusicherung neben der negativen. Ein Feld, das immer
    `false` meldet, waere von einem richtigen nicht zu unterscheiden."""
    monkeypatch.setenv("BREVO_API_KEY", "xkeysib-testwert")
    monkeypatch.setenv("BREVO_LIST_VERIFIED_ID", "11")
    monkeypatch.setenv("BREVO_LIST_OPTIN_ID", "22")

    block = _brevo(client)
    assert block["bereit"] is True
    assert block["fehlend"] == []
    assert block["schwere"] == "ok"


def test_fehlende_listen_stehen_beim_namen(client, monkeypatch):
    """Der Fall vom 17.09.: Schluessel da, Listen nicht — und genau das war
    von aussen nicht zu sehen."""
    monkeypatch.setenv("BREVO_API_KEY", "xkeysib-testwert")
    monkeypatch.delenv("BREVO_LIST_VERIFIED_ID", raising=False)
    monkeypatch.delenv("BREVO_LIST_OPTIN_ID", raising=False)

    block = _brevo(client)
    assert block["bereit"] is False
    assert block["fehlend"] == ["BREVO_LIST_VERIFIED_ID", "BREVO_LIST_OPTIN_ID"]
    assert block["schluessel_gesetzt"] is True


def test_eine_id_die_keine_zahl_ist_gilt_nicht_als_eingerichtet(client, monkeypatch):
    """`_listen_id` gibt bei Unsinn `None` zurueck. Meldete `/health` hier
    trotzdem `bereit`, waere es genau der Wachposten ohne Wirkung, gegen den
    dieser Block gebaut ist."""
    monkeypatch.setenv("BREVO_API_KEY", "xkeysib-testwert")
    monkeypatch.setenv("BREVO_LIST_VERIFIED_ID", "11")
    monkeypatch.setenv("BREVO_LIST_OPTIN_ID", "keine-zahl")

    block = _brevo(client)
    assert block["bereit"] is False
    assert "BREVO_LIST_OPTIN_ID" in block["fehlend"]


def test_der_schluessel_steht_nirgends_in_der_antwort(client, monkeypatch):
    """`/health` antwortet ohne Anmeldung. Gemeldet wird die Laenge, nie der
    Wert — dasselbe Versprechen wie bei den Stripe-Schluesseln."""
    geheim = "xkeysib-dieser-wert-darf-nicht-hinaus"
    monkeypatch.setenv("BREVO_API_KEY", geheim)

    antwort = client.get("/health")
    assert geheim not in antwort.text
    assert antwort.json()["brevo"]["schluessel_laenge"] == len(geheim)
