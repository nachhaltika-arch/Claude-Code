"""Der gemeinsame KI-Aufruf haelt die Ereignisschleife nicht an.

Am 17.08. wurde das im Impressum-Sucher einzeln repariert
(test_impressum_blockiert_nicht.py). Zehn weitere Stellen hatten dasselbe
Muster. Statt zehnmal dieselbe Zeile zu schreiben, gibt es jetzt eine
Stelle, an der der synchrone Client in einen Arbeitsthread wandert — und
dieser Test misst nicht, wie sie gebaut ist, sondern ob waehrend des
Aufrufs noch etwas anderes laufen darf.
"""
import asyncio
import threading
import time

import pytest

from services.ki_aufruf import frag_modell


class _Antwort:
    def __init__(self, text="fertig"):
        self.content = [type("Block", (), {"text": text})()]


class _LangsamerClient:
    """Der echte Client ist synchron — dieser auch."""

    def __init__(self, dauer=0.3):
        self.dauer = dauer
        self.gesehene_argumente = None
        self.thread_beim_aufruf = None
        client = self

        class _Nachrichten:
            def create(self, **argumente):
                client.gesehene_argumente = argumente
                client.thread_beim_aufruf = threading.current_thread()
                time.sleep(client.dauer)
                return _Antwort()

        self.messages = _Nachrichten()


def test_waehrend_des_aufrufs_laeuft_die_schleife_weiter():
    client = _LangsamerClient()

    async def lauf():
        ticks = 0

        async def ticker():
            nonlocal ticks
            while True:
                ticks += 1
                await asyncio.sleep(0.01)

        nebenher = asyncio.create_task(ticker())
        await frag_modell(client, model="claude-sonnet-4-6", max_tokens=10)
        nebenher.cancel()
        return ticks

    ticks = asyncio.run(lauf())

    assert ticks >= 5, (
        f"Nur {ticks} Durchläufe während des KI-Aufrufs — die Schleife stand "
        "still. Genau daran starben die Anfragen auf Staging mit 503."
    )


def test_der_aufruf_laeuft_in_einem_anderen_thread():
    client = _LangsamerClient(dauer=0)

    async def lauf():
        eigener = threading.current_thread()
        await frag_modell(client, model="claude-sonnet-4-6", max_tokens=10)
        return eigener

    schleifen_thread = asyncio.run(lauf())

    assert client.thread_beim_aufruf is not schleifen_thread


def test_argumente_gehen_unveraendert_durch():
    """Der Helfer entscheidet nichts — kein stilles Zeitlimit, kein Modell."""
    client = _LangsamerClient(dauer=0)

    asyncio.run(
        frag_modell(
            client,
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": "hallo"}],
            timeout=20.0,
        )
    )

    assert client.gesehene_argumente == {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": "hallo"}],
        "timeout": 20.0,
    }


def test_die_antwort_kommt_zurueck():
    client = _LangsamerClient(dauer=0)

    antwort = asyncio.run(frag_modell(client, model="m", max_tokens=1))

    assert antwort.content[0].text == "fertig"


def test_fehler_werden_durchgereicht():
    """Jede Aufrufstelle hat ihre eigene Fehlerbehandlung — der Helfer
    darf sie nicht verschlucken."""

    class _KaputterClient:
        class messages:
            @staticmethod
            def create(**_):
                raise RuntimeError("Anthropic überlastet")

    with pytest.raises(RuntimeError, match="überlastet"):
        asyncio.run(frag_modell(_KaputterClient(), model="m", max_tokens=1))
