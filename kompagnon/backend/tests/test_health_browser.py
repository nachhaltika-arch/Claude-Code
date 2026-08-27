# -*- coding: utf-8 -*-
"""`/health` sagt, ob der Browserlauf wirklich läuft.

**Der Anlass (27.08.2026).** Der Browserlauf der Erhebung (L-107) hängt an
zwei Dingen, die **nicht im Quelltext** stehen, sondern in Render: dem
Buildbefehl (`playwright install chromium`) und der Variablen
`AUDIT_BROWSER=true`. Fehlt eines von beiden, misst die Erhebung eine
React-Seite als leer — und das Ergebnis steht als Befund im Kundenbericht.

Bis heute war das von aussen nicht feststellbar. Wer wissen wollte, ob die
Einrichtung griff, musste ins Render-Dashboard sehen. Das ist dieselbe
Bauart, die bei den Uploads schon einmal auffiel: am Werkzeug ablesen statt
am Gegenstand fragen.

**Zwei Felder, nicht eines.** „Nicht eingeschaltet" und „eingeschaltet, aber
Playwright fehlt" sind verschiedene Zustände, und der zweite ist ein
Einrichtungsfehler, der auffallen soll. Ein einzelnes `browser: false` würde
beide zu derselben Achselzucken-Antwort verschmelzen.
"""


def test_health_nennt_den_browserzustand(client):
    antwort = client.get("/health")

    assert antwort.status_code == 200
    zustand = antwort.json()
    assert "browser" in zustand, zustand
    assert set(zustand["browser"]) == {"eingeschaltet", "verfuegbar", "bereit"}


def test_bereit_heisst_beides(client, monkeypatch):
    """`bereit` ist die Frage, die David stellt — die anderen zwei sagen,
    woran es liegt, wenn sie falsch ist."""
    from services import seitenbrowser

    monkeypatch.setenv(seitenbrowser.SCHALTER, "true")

    zustand = client.get("/health").json()["browser"]

    assert zustand["eingeschaltet"] is True
    assert zustand["bereit"] == (zustand["eingeschaltet"]
                                 and zustand["verfuegbar"])


def test_ohne_schalter_ist_er_nicht_bereit(client, monkeypatch):
    from services import seitenbrowser

    monkeypatch.delenv(seitenbrowser.SCHALTER, raising=False)

    zustand = client.get("/health").json()["browser"]

    assert zustand["eingeschaltet"] is False
    assert zustand["bereit"] is False
    # Gegenprobe: Die Auskunft über Playwright bleibt davon unberührt —
    # sonst hiesse „ausgeschaltet" auch „nicht installiert".
    assert isinstance(zustand["verfuegbar"], bool)
