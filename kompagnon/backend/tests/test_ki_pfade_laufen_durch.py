"""Die umgebauten Aufrufstellen laufen wirklich durch — nicht nur der Helfer.

Nach dem Umbau von zwoelf Stellen auf `frag_modell` stand die Testsuite auf
gruen, obwohl **keine einzige** dieser Funktionen von einem Test ausgefuehrt
wurde. Gruen hiess dort nur: nichts anderes ist kaputtgegangen. Ein
vergessenes `await` haette genau so ausgesehen — und in `ai_evaluate_qa`
sogar unauffaellig, weil die Funktion jeden Fehler abfaengt und ein
Ersatzergebnis zurueckgibt.

Deshalb hier die beiden Dienstwege echt durchgespielt: mit einem langsamen,
synchronen Client wie dem richtigen, und mit einem Zaehler, der nebenher
laufen darf. Die zehn Router-Stellen sind so nicht erreichbar (Datenbank und
Anmeldung dazwischen); fuer die stehen die Sperre in
`test_keine_ki_blockiert_die_schleife.py` und ein Live-Aufruf auf Staging.
"""
import asyncio
import json
import time

import anthropic

from services import qa_scanner
from services.geo_optimizer import GeoOptimizerAgent


class _Block:
    def __init__(self, text):
        self.text = text


class _Antwort:
    def __init__(self, text):
        self.content = [_Block(text)]
        self.stop_reason = "end_turn"


class _LangsamerClient:
    """Synchron und traege — genau die Kombination, die den Server anhielt."""

    def __init__(self, antwort_text, dauer=0.3):
        client = self

        class _Nachrichten:
            def create(self, **_):
                time.sleep(dauer)
                return _Antwort(antwort_text)

        self.messages = _Nachrichten()


async def _ticks_waehrend(aufgabe):
    """Zaehlt, wie oft die Schleife waehrend `aufgabe` drankommt."""
    ticks = 0

    async def ticker():
        nonlocal ticks
        while True:
            ticks += 1
            await asyncio.sleep(0.01)

    nebenher = asyncio.create_task(ticker())
    ergebnis = await aufgabe
    nebenher.cancel()
    return ergebnis, ticks


QA_ANTWORT = json.dumps({
    "kategorien": {"seo": {"score": 80, "status": "gut", "punkte": [], "probleme": []}},
    "gesamt_score": 77,
    "golive_empfehlung": True,
    "golive_begruendung": "Sieht gut aus",
    "kritische_blocker": [],
    "top_empfehlungen": [],
})

SCAN = {
    "url": "https://beispiel.de",
    "company": "Muster Haustechnik",
    "trade": "Heizung",
    "title": "Muster Haustechnik — Heizung in Mainz",
    "meta_desc": "Heizung, Sanitaer, Waermepumpe",
    "h1": "Ihre Heizung in Mainz",
    "html_snippet": "<html></html>",
    "checks": {},
}


def test_qa_auswertung_liefert_ein_ergebnis_und_haelt_die_schleife_nicht_an(monkeypatch):
    # `ai_evaluate_qa` holt den Client erst im Funktionsrumpf
    # (`from anthropic import Anthropic`) — deshalb am Paket ersetzen, nicht
    # am Modul. Das Modul zu ersetzen wirkt nicht, und der Test waere trotzdem
    # gruen geworden: mit dem Ersatzergebnis aus dem except-Zweig.
    monkeypatch.setattr(anthropic, "Anthropic", lambda **_: _LangsamerClient(QA_ANTWORT))

    ergebnis, ticks = asyncio.run(_ticks_waehrend(qa_scanner.ai_evaluate_qa(SCAN)))

    # Ohne diese Zusicherung waere der Test auch mit dem Ersatzergebnis gruen,
    # das die Funktion bei jedem Fehler zurueckgibt.
    assert ergebnis["gesamt_score"] == 77, ergebnis
    assert ergebnis["golive_empfehlung"] is True
    assert ticks >= 5, f"Nur {ticks} Durchläufe — die Schleife stand still"


GEO_ANTWORT = json.dumps({
    "content_depth_score": 71,
    "local_signal_score": 64,
    "authority_score": 60,
    "ai_citable_score": 55,
    "faq_potential_score": 40,
    "strengths": ["Klare Leistungen"],
    "weaknesses": ["Keine FAQ"],
    "ai_summary": "Solide Grundlage.",
})


def test_geo_analyse_liefert_die_ki_werte_und_haelt_die_schleife_nicht_an(monkeypatch):
    monkeypatch.setattr(
        "services.geo_optimizer.Anthropic", lambda **_: _LangsamerClient(GEO_ANTWORT)
    )

    agent = GeoOptimizerAgent(api_key="egal")

    async def kein_netz(_self, _url):
        return {"score": 0, "exists": False}

    for name in ("_check_llms_txt", "_check_robots_ai", "_check_structured_data"):
        monkeypatch.setattr(GeoOptimizerAgent, name, kein_netz)

    ergebnis, ticks = asyncio.run(_ticks_waehrend(
        agent.analyze(
            website_url="https://beispiel.de",
            gewerk="Heizung",
            city="Mainz",
            website_text="Wir bauen Waermepumpen ein.",
        )
    ))

    # 71 statt der 50 aus dem Ersatzwert: Die KI-Antwort ist wirklich angekommen.
    assert ergebnis["content_depth_score"] == 71, ergebnis
    assert ergebnis["raw_checks"]["ai_content"]["ai_summary"] == "Solide Grundlage."
    assert ticks >= 5, f"Nur {ticks} Durchläufe — die Schleife stand still"
