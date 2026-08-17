"""Der KI-Aufruf darf den Server nicht anhalten.

Befund vom 17.08.2026, am Bildschirm mit David gefunden. `POST
/api/leads/{id}/extract-impressum` antwortete auf Staging dreimal mit **503**
nach 6 bis 10 Sekunden, waehrend `/api/health` in 0,13 s durchlief. Der
Browser zeigte „Failed to fetch", die Oberflaeche daraus „Verbindungsfehler" —
also einen Rat, beim eigenen Internet zu suchen.

Die Ursache steht in zwei Zeilen:

    from anthropic import Anthropic          # der SYNCHRONE Client
    ...
    async def extract_contact_from_impressum(...):
        response = client.messages.create(...)   # ohne await

Ein synchroner Aufruf in einer `async def` blockiert die Ereignisschleife.
Bei `timeout=20.0` steht der ganze Server bis zu zwanzig Sekunden — er
beantwortet in der Zeit auch Renders Gesundheitspruefung nicht, und deren
Proxy kappt die laufende Anfrage. Der Fehler sah aus wie ein Netzproblem und
war ein Nebenlaeufigkeitsproblem.

Dieser Test misst nicht die Dauer — das waere flatterig —, sondern ob
waehrend des KI-Aufrufs noch etwas anderes laufen darf.
"""
import asyncio
import time

import pytest


IMPRESSUM = ("Impressum Muster Haustechnik GmbH Musterstraße 1 55116 Mainz "
             "Registergericht Mainz HRB 4711 USt-IdNr. DE123456789 "
             "Vertreten durch Max Mustermann Telefon 06131 000000")


class _FalscheAntwort:
    def __init__(self, text):
        self.content = [type('Block', (), {'text': text})()]


@pytest.fixture
def langsame_ki(monkeypatch):
    """Ein KI-Aufruf, der 0,3 s dauert — synchron, wie der echte."""
    from services import impressum_scraper

    async def kein_netz(url):
        return IMPRESSUM

    monkeypatch.setattr(impressum_scraper, 'fetch_impressum_text', kein_netz)

    class _Nachrichten:
        def create(self, **kwargs):
            time.sleep(0.3)
            return _FalscheAntwort('{"company_name": "Muster Haustechnik"}')

    class _Client:
        def __init__(self, *a, **k):
            self.messages = _Nachrichten()

    monkeypatch.setattr(impressum_scraper, 'Anthropic', _Client)


def test_waehrend_des_ki_aufrufs_laeuft_der_server_weiter(app, langsame_ki):
    """Der eigentliche Befund: Vorher stand hier alles still.

    Ein Zaehler tickt alle 10 ms. Blockiert der KI-Aufruf die Schleife, kommt
    er waehrend der 300 ms kein einziges Mal dran.
    """
    from services.impressum_scraper import extract_contact_from_impressum

    async def lauf():
        ticks = 0

        async def ticker():
            nonlocal ticks
            while True:
                ticks += 1
                await asyncio.sleep(0.01)

        nebenher = asyncio.create_task(ticker())
        await extract_contact_from_impressum('https://beispiel.de')
        nebenher.cancel()
        return ticks

    ticks = asyncio.run(lauf())

    assert ticks >= 5, (
        f"Nur {ticks} Durchläufe während des KI-Aufrufs — die Ereignisschleife "
        "stand still. Genau daran starb die Anfrage auf Staging mit 503."
    )


def test_das_ergebnis_stimmt_trotzdem(app, langsame_ki):
    """Nebenläufig heißt nicht anders."""
    from services.impressum_scraper import extract_contact_from_impressum

    ergebnis = asyncio.run(extract_contact_from_impressum('https://beispiel.de'))

    assert ergebnis['success'] is True
    assert ergebnis['data']['company_name'] == 'Muster Haustechnik'
