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
#
#: **Sie ist am 21.08.2026 leer geworden.** Die letzte Ausnahme war
#: `POST /api/projects/{}/scrape` — zwei verschiedene Dinge unter einem
#: Namen (Branddesign gegen mehrseitigen Inhalts-Lauf). Aufgeloest durch
#: Umbenennen: `/{id}/scrape-pages`.
GEPRUEFTE_AUSNAHMEN = set()


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


def test_jede_ausnahme_ist_noch_eine():
    """Sonst steht hier bald eine Liste, die niemand mehr prueft.

    Bewusst **nicht** parametrisiert: Bei leerer Liste meldet pytest sonst
    „skipped", und ein uebersprungener Test liest sich wie ein kaputter.
    Leer ist hier der gute Zustand.
    """
    belegt = _belegte_adressen()
    veraltet = [a for a in GEPRUEFTE_AUSNAHMEN if len(belegt.get(a, ())) <= 1]

    assert veraltet == [], (
        f"Diese Ausnahmen kollidieren nicht mehr und gehoeren entfernt: {veraltet}"
    )


def test_keine_tabelle_hat_zwei_modelle():
    """Zwei Klassen auf einer Tabelle brechen `create_all`.

    Gefunden am 21.08.2026: `routers/mockups.py` und `routers/designs.py`
    bildeten beide `mockup_versions` ab — Zeichen fuer Zeichen dieselbe
    Klasse, nur anders benannt. `extend_existing=True` verhindert den Fehler
    beim Import, nicht beim Anlegen: `create_all` schickt die Index-Befehle
    zweimal und Postgres antwortet `relation already exists`.

    `mockups.py` war ausserdem **nirgends eingebunden** — vier Routen, die es
    nicht gab, und eine Kopie von `designs.py` ohne dessen Sperre aus L-51.
    Entfernt.
    """
    import collections
    import pathlib
    import re

    wurzel = pathlib.Path(__file__).resolve().parent.parent
    wo = collections.defaultdict(list)
    for datei in sorted(wurzel.rglob("*.py")):
        if "venv" in str(datei) or "/tests/" in str(datei):
            continue
        text = datei.read_text(encoding="utf-8", errors="ignore")
        for treffer in re.finditer(
            r'class (\w+)\(Base\):(?:[^\n]*\n){0,6}?\s*__tablename__ = ["\'](\w+)["\']',
            text,
        ):
            wo[treffer.group(2)].append(f"{datei.name}::{treffer.group(1)}")

    doppelt = {t: v for t, v in wo.items() if len(v) > 1}
    assert doppelt == {}, f"Tabellen mit mehr als einem Modell: {doppelt}"


# ── Die letzte Kollision ist am 21.08.2026 aufgeloest ────────────────
#
# `POST /api/projects/{id}/scrape` gab es zweimal, mit zwei verschiedenen
# Bedeutungen:
#
#   projects.py               liest **Branddesign** aus der Website
#                             (Farben, Schriften) und schreibt es ans Projekt
#   content_scraper_router.py startet einen **mehrseitigen Inhalts-Lauf**
#                             (`ProjectScrapeJob`, `ProjectScrapedPage`)
#
# `projects.py` war frueher eingebunden und gewann; der Inhalts-Lauf war als
# manueller Ausloeser unerreichbar. Angelegt wird er trotzdem — `projects.py`
# startet ihn beim Anlegen eines Projekts von selbst (`_run_content_scrape`).
# Es fehlte also nur der Weg, ihn **noch einmal** anzustossen.
#
# Aufgeloest durch Umbenennen statt Loeschen: `/{id}/scrape-pages` sagt, was
# geschieht, und `/{id}/scrape` bleibt beim Branddesign.

def test_der_mehrseitige_lauf_hat_einen_eigenen_namen():
    from routers import content_scraper_router, projects

    inhalt = {r.path for r in content_scraper_router.router.routes}
    marke = {r.path for r in projects.router.routes}

    assert "/api/projects/{project_id}/scrape-pages" in inhalt
    assert "/api/projects/{project_id}/scrape" not in inhalt
    assert "/api/projects/{project_id}/scrape" in marke


def test_und_er_ist_erreichbar(client, auth_headers):
    """Vorher war er tot. Eine tote Route ist eine ungepruefte Route (L-68) —
    deshalb wird sie hier einmal wirklich angefasst.

    404 fuer ein Projekt, das es nicht gibt, beweist: durch die Sperre,
    durch die Adressaufloesung, bis zur Datenbank.
    """
    antwort = client.post("/api/projects/999999/scrape-pages", headers=auth_headers)
    assert antwort.status_code == 404, antwort.text[:200]
