"""L-27: Zwei Briefing-Router auf **demselben** Praefix.

`routers/briefing.py` und `routers/briefings.py` tragen beide
`prefix="/api/briefings"`. Gemessen am 21.08.2026, und der Befund ist ein
anderer als notiert: Es sind **keine zwei konkurrierenden Wege**, sondern
eine Endpunktfamilie, die versehentlich auf zwei Dateien verteilt liegt —
getrennt nach HTTP-Verb, nicht nach Zustaendigkeit.

    briefing.py    PATCH /{id}            PATCH /{id}/freigabe
                   POST  /{id}/zielgruppenanalyse
                   POST  /{id}/wettbewerbsanalyse
    briefings.py   GET   /{id}            POST /{id}          PUT /{id}
                   GET   /{id}/pdf        POST /{id}/suggest-field   …

`BriefingTab.jsx` ruft **beide** auf: `GET` aus dem einen, `PATCH` aus dem
anderen. Solange sich kein Verb-Pfad-Paar doppelt, geht das gut — aber nur
zufaellig. Wer in einer der Dateien eine Route ergaenzt, die es in der anderen
schon gibt, verdeckt sie still: Es gewinnt die zuerst eingebundene, und keine
Fehlermeldung sagt es.

Dieser Test misst genau das. Er verlangt **nicht**, dass die Dateien
zusammengelegt werden — das waere eine Datei mit rund 980 Zeilen und damit
gegen die eigene 800-Zeilen-Grenze (L-25).

Zur zweiten Haelfte von L-27, den „zwei Briefing-Strukturen": Sie stehen in
**einer** Tabelle. `Briefing` traegt zwoelf JSON-Abschnitte („Legacy JSON
sections (used by BriefingTab)") **und** achtzehn flache Felder. Gemessen:
Die JSON-Abschnitte benutzt genau eine Datei (`BriefingTab.jsx`), die flachen
Felder benutzen `BriefingWizard.jsx` und `OnboardingWizard.jsx`. Beide leben.
Welche bleibt, ist eine Produktentscheidung und steht in der Lueckenliste.
"""
import collections


def _router(modul):
    from importlib import import_module

    return import_module(f"routers.{modul}").router


def _verb_pfad(router):
    paare = set()
    for route in router.routes:
        for methode in getattr(route, "methods", set()) or set():
            if methode in ("HEAD", "OPTIONS"):
                continue
            paare.add((methode, route.path))
    return paare


def test_beide_router_tragen_wirklich_dasselbe_praefix():
    """Der Befund selbst — damit er nicht unbemerkt verschwindet."""
    assert _router("briefing").prefix == _router("briefings").prefix == "/api/briefings"


def test_keine_route_verdeckt_eine_andere():
    """Zwei Router auf einem Praefix: Es gewinnt der zuerst eingebundene.

    Eine Ueberschneidung faellt nirgends auf — sie zeigt sich erst daran,
    dass ein Aufruf etwas anderes tut als erwartet.
    """
    doppelt = _verb_pfad(_router("briefing")) & _verb_pfad(_router("briefings"))

    assert doppelt == set(), (
        f"Diese Aufrufe gibt es in beiden Briefing-Routern: {sorted(doppelt)}. "
        "Der zuerst eingebundene gewinnt, der andere ist tot."
    )


def test_jede_route_ist_gesichert():
    """`briefings.py` traegt eine Vorgabe am Router, `briefing.py` nicht —
    dort haengt die Pruefung an jeder Route einzeln. Genau diese Bauart hat
    am 19.08. 55 offene Routen erzeugt (L-51): `briefings.py` hatte elf
    geschuetzte und drei vergessene.
    """
    router = _router("briefing")
    ungeschuetzt = []
    for route in router.routes:
        hat_abhaengigkeit = bool(getattr(route, "dependencies", None))
        # `PATCH /{id}/freigabe` prueft den Token selbst aus dem Rumpf, weil
        # ein Kunde sie erreichen muss und `require_innendienst` ihn sperren
        # wuerde. Das ist gewollt und steht im Quelltext begruendet.
        selbst_geprueft = "freigabe" in route.path
        if not hat_abhaengigkeit and not selbst_geprueft:
            ungeschuetzt.append(route.path)

    assert ungeschuetzt == [], ungeschuetzt
