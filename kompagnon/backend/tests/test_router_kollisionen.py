"""Zwei Router duerfen nicht dieselbe Adresse beanspruchen.

Beim Auftrennen der Nahtstellen aus `docs/module-karte.md` (21.08.2026)
gemessen: **19 Kollisionen** — gleiches Verb, gleiche Adresse, zwei oder drei
verschiedene Router. Was daran gefaehrlich ist, hat sich an Ort und Stelle
gezeigt:

* **Es gewinnt der zuerst eingebundene, und niemand sagt es.**
  `GET /api/customers/` lieferte **UserCards statt Customers** — zwei
  verschiedene Entitaeten auf einer Adresse. Nachgewiesen am laufenden Server
  mit einer UserCard und null Customers.
* **Die Beschreibung nennt einen anderen.** FastAPI traegt in `openapi.json`
  den **zuletzt** registrierten Handler ein, geroutet wird der **erste**. Die
  Schnittstellenbeschreibung beschrieb also einen Endpunkt, der nie antwortet.
* **Die Ueberdeckung kann die Sicherheitsarbeit machen.** Der ueberdeckende
  Alias trug `require_innendienst`, der ueberdeckte Router nur
  `require_any_auth`. Wer den Alias entfernt, ohne das zu bemerken, oeffnet
  den Kundenbestand fuer jeden angemeldeten Kunden.

Der Test vergleicht **normalisierte** Adressen: `/api/customers/{card_id}` und
`/api/customers/{lead_id}` sind verschiedene Zeichenketten, treffen aber
dieselben Aufrufe. Eine erste Fassung verglich woertlich und uebersah dadurch
sechs der neunzehn.

Er loest `test_briefing_router.py` ab, das dasselbe fuer zwei Dateien tat.
"""
import collections
import importlib
import pathlib
import re

import pytest


def _router_objekte():
    """Alle `APIRouter` aus `routers/` — je Objekt einmal, nicht je Name.

    `usercards.py` band seine Alias-Router in einer Schleife; die
    Schleifenvariable `_alias` zeigte am Ende auf denselben Router und liess
    eine erste Messung sechs Kollisionen erfinden, die es nicht gab.
    """
    wurzel = pathlib.Path(__file__).resolve().parent.parent / "routers"
    gesehen = set()
    for datei in sorted(wurzel.glob("*.py")):
        if datei.stem == "__init__":
            continue
        modul = importlib.import_module(f"routers.{datei.stem}")
        for name in dir(modul):
            obj = getattr(modul, name)
            if type(obj).__name__ != "APIRouter" or id(obj) in gesehen:
                continue
            gesehen.add(id(obj))
            yield f"{datei.stem}.{name}", obj


def _belegte_adressen():
    belegt = collections.defaultdict(set)
    for herkunft, router in _router_objekte():
        for route in getattr(router, "routes", []):
            adresse = re.sub(r"\{[^}]+\}", "{}", route.path)
            for methode in (getattr(route, "methods", set()) or set()):
                if methode in ("HEAD", "OPTIONS"):
                    continue
                belegt[(methode, adresse)].add(herkunft)
    return belegt


#: Kollisionen, die bleiben duerfen — jede mit Grund.
#: Diese Liste soll schrumpfen, nie wachsen.
GEPRUEFTE_AUSNAHMEN = {
    # `projects.py` scrapt die Website fuer **Branddesign** (Farben,
    # Schriften), `content_scraper_router.py` startet einen **Inhalts**-Lauf im
    # Hintergrund. Zwei verschiedene Dinge unter einem Namen; heute gewinnt
    # `projects.py`, der andere ist unerreichbar. Welcher bleibt und wie der
    # andere heisst, ist eine Produktentscheidung (Modulkarte, M5 gegen M6).
    ("POST", "/api/projects/{}/scrape"),
}


def test_keine_zwei_router_auf_derselben_adresse():
    doppelt = {
        adresse: sorted(wer)
        for adresse, wer in _belegte_adressen().items()
        if len(wer) > 1 and adresse not in GEPRUEFTE_AUSNAHMEN
    }

    assert doppelt == {}, (
        "Diese Aufrufe beansprucht mehr als ein Router. Es gewinnt der zuerst "
        f"eingebundene, der andere ist tot: {doppelt}"
    )


@pytest.mark.parametrize("adresse", sorted(GEPRUEFTE_AUSNAHMEN))
def test_jede_ausnahme_ist_noch_eine(adresse):
    """Sonst steht hier bald eine Liste, die niemand mehr prueft."""
    belegt = _belegte_adressen()
    assert len(belegt.get(adresse, ())) > 1, (
        f"{adresse} kollidiert nicht mehr — die Ausnahme gehoert entfernt."
    )
