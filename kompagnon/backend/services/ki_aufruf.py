"""Der KI-Aufruf, der die Ereignisschleife in Ruhe laesst.

`anthropic.Anthropic` ist der **synchrone** Client. In einer `async def`
direkt aufgerufen haelt er die Ereignisschleife an: Der Server beantwortet
in der Zeit gar nichts mehr — auch nicht Renders Gesundheitspruefung, worauf
deren Proxy die laufende Anfrage kappt. Im Browser steht dann „Failed to
fetch", in der Oberflaeche „Verbindungsfehler", und beides zeigt in die
falsche Richtung (17.08.2026, drei 503er auf Staging).

Der Weg hier hinein ist deshalb der einzige erlaubte aus einer `async def`;
`tests/test_keine_ki_blockiert_die_schleife.py` haelt das offen.

    antwort = await frag_modell(
        client,
        model='claude-sonnet-5', thinking={"type": "disabled"},
        max_tokens=1000,
        messages=[{'role': 'user', 'content': prompt}],
    )

Bewusst duenn: kein eigenes Zeitlimit, kein Standardmodell, keine
Fehlerbehandlung. Jede Aufrufstelle hat ihre eigenen Regeln dafuer, und ein
Helfer, der still etwas anderes tut als der Client, waere schlimmer als
keiner.
"""
import asyncio
from typing import Any


async def frag_modell(client: Any, **argumente: Any) -> Any:
    """Fuehrt `client.messages.create(**argumente)` in einem Arbeitsthread aus."""
    return await asyncio.to_thread(lambda: client.messages.create(**argumente))
