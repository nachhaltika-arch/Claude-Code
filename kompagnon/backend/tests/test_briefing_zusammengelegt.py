"""Ein Briefing-Router statt zweier — und eine `_serialize`-Fassung (L-27).

**Der Ausgangsbefund.** `routers/briefing.py` und `routers/briefings.py`
trugen beide `prefix="/api/briefings"`, getrennt **nach HTTP-Verb**: PATCH
und die Analysen drueben, GET/POST/PUT hier. So gewachsen, nicht entworfen.
Wer in einer Datei eine Route ergaenzt, die es in der anderen schon gibt,
verdeckt sie **still** — es gewinnt der zuerst eingebundene Router.

**Und es war nicht theoretisch.** Beide Dateien fuehrten ein `_serialize`,
und die Fassungen waren **auseinandergelaufen**: Die in `briefings.py` gibt
22 Felder mehr zurueck — Gewerk, Leistungen, USP, Farben, Stil, Mitbewerber,
WZ-Code. Wer ueber `PATCH /{lead_id}` speicherte, bekam ein halbes Briefing
zurueck.

Schaden hat das keinen angerichtet, weil `BriefingTab.jsx` die Antwort gar
nicht auswertet (`if (res.ok)`). Genau das ist der Punkt: Es ging gut, weil
niemand hinsah — nicht, weil es richtig war.

**Was hier festgehalten wird:** ein Router auf dem Praefix, eine
`_serialize`-Fassung, und alle dreizehn Endpunkte weiterhin erreichbar.
"""
import ast
import pathlib

import pytest


WURZEL = pathlib.Path(__file__).resolve().parent.parent


def test_es_gibt_nur_noch_einen_briefing_router():
    """Zwei Router auf einem Praefix sind eine Falle mit Zeitzuender."""
    assert not (WURZEL / "routers" / "briefing.py").exists(), (
        "`routers/briefing.py` ist zurueck — damit auch der zweite Router "
        "auf `/api/briefings`.")


def test_die_ki_routen_liegen_in_ihrer_eigenen_datei():
    """**Der Schnitt nach Zustaendigkeit (L-25, 22.08.2026).** Nach dem
    Zusammenlegen war `briefings.py` 958 Zeilen lang, und die Haelfte davon
    waren sechs Routen, die alle dasselbe tun: ein Modell fragen und die
    Antwort in ein Briefing-Feld schreiben.

    Der Test haelt den Schnitt — nicht die Zeilenzahl, sondern **wo was
    liegt**. Eine Zeilengrenze allein sagt nichts darueber, ob eine Datei
    eine Sache tut.
    """
    from routers import briefings, briefings_ki

    ki_pfade = {r.path for r in briefings_ki.router.routes}
    stamm_pfade = {r.path for r in briefings.router.routes}

    assert any("ki-prefill" in p for p in ki_pfade), ki_pfade
    assert not any("ki-prefill" in p for p in stamm_pfade), (
        "KI-Routen sind zurueck in den Stammdaten")
    assert "/api/briefings/{lead_id}" in stamm_pfade


def test_keine_briefing_datei_ueberschreitet_die_grenze():
    """800 Zeilen sind die Hausgrenze (L-25). Beide liegen darunter — der
    Test sagt es, wenn eine wieder darueber waechst."""
    for name in ("briefings.py", "briefings_ki.py"):
        datei = WURZEL / "routers" / name
        zeilen = len(datei.read_text(encoding="utf-8").split("\n"))
        assert zeilen <= 800, f"{name}: {zeilen} Zeilen"


def test_serialize_gibt_es_genau_einmal():
    """Zwei Fassungen desselben Helfers laufen auseinander. Sie taten es."""
    treffer = []
    for datei in (WURZEL / "routers").glob("briefing*.py"):
        baum = ast.parse(datei.read_text(encoding="utf-8"))
        for knoten in baum.body:
            if isinstance(knoten, ast.FunctionDef) and knoten.name == "_serialize":
                treffer.append(datei.name)

    assert len(treffer) <= 1, f"`_serialize` steht in {treffer}"


def test_die_verbliebene_fassung_ist_die_vollstaendige():
    """Die abgespeckte durfte nicht gewinnen — sie liess Gewerk, USP,
    Leistungen und Farben weg."""
    from routers import briefings

    import inspect
    quelle = inspect.getsource(briefings._serialize)

    for feld in ("gewerk", "usp", "leistungen", "farben", "mitbewerber"):
        assert f'"{feld}"' in quelle or f"'{feld}'" in quelle, feld


ERWARTETE_PFADE = {
    "/api/briefings/{lead_id}",
    "/api/briefings/{lead_id}/pdf",
    "/api/briefings/{lead_id}/freigabe",
    "/api/briefings/{lead_id}/suggest-field",
    "/api/briefings/{lead_id}/assets-status",
    "/api/briefings/{lead_id}/assets-save",
    "/api/briefings/{lead_id}/ki-prefill-funktionen",
    "/api/briefings/{lead_id}/ki-prefill-seo",
    "/api/briefings/{lead_id}/ki-prefill-ziele",
    "/api/briefings/{lead_id}/zielgruppenanalyse",
    "/api/briefings/{lead_id}/wettbewerbsanalyse",
}


def test_kein_endpunkt_ist_beim_umzug_verlorengegangen(app):
    """Die Zahl allein genuegt nicht — es zaehlt, **welche** da sind."""
    from main import app as anwendung

    vorhanden = {p for p in anwendung.openapi()["paths"] if p.startswith("/api/briefings")}

    fehlt = ERWARTETE_PFADE - vorhanden
    assert fehlt == set(), f"Beim Umzug verloren: {sorted(fehlt)}"


def test_die_verben_stimmen_noch(app):
    """`PATCH /{lead_id}` kam aus der einen Datei, `PUT /{lead_id}` aus der
    anderen. Beim Zusammenlegen darf keins von beiden verschwinden."""
    from main import app as anwendung

    pfad = anwendung.openapi()["paths"]["/api/briefings/{lead_id}"]

    for verb in ("get", "post", "put", "patch"):
        assert verb in pfad, f"{verb.upper()} /api/briefings/{{lead_id}} fehlt"


def test_die_router_ueberschneiden_sich_nicht():
    """**Uebernommen aus `test_briefing_router.py`,** das seinen Gegenstand
    verloren hat: Es gibt keine zweite Datei mehr.

    Die Zusicherung bleibt trotzdem noetig. In `briefings.py` stehen jetzt
    **zwei** Router auf demselben Praefix — `router` (Innendienst) und
    `kunden_router` (nur die Freigabe ueber Token). Das ist etwas anderes als
    der alte Fehler, weil beide sichtbar nebeneinander stehen und nach
    **Zustaendigkeit** getrennt sind. Unsichtbar wuerde eine Ueberschneidung
    trotzdem: Es gewinnt der zuerst eingebundene.
    """
    from routers import briefings, briefings_ki

    def verb_pfad(r):
        return {(m, route.path) for route in r.routes
                for m in (getattr(route, "methods", set()) or set())
                if m not in ("HEAD", "OPTIONS")}

    # Drei Router auf `/api/briefings`: Innendienst-Stammdaten, der
    # Kundenweg (nur die Freigabe) und die KI-Vorbefuellung (L-25).
    alle = {
        "briefings.router": verb_pfad(briefings.router),
        "briefings.kunden_router": verb_pfad(briefings.kunden_router),
        "briefings_ki.router": verb_pfad(briefings_ki.router),
    }
    namen = sorted(alle)
    for i, a in enumerate(namen):
        for b in namen[i + 1:]:
            doppelt = alle[a] & alle[b]
            assert doppelt == set(), (
                f"In {a} und {b}: {sorted(doppelt)}. Der zuerst eingebundene "
                f"gewinnt, der andere ist tot.")


def test_der_kundenrouter_traegt_nur_die_freigabe():
    """Er hat **keine** Vorgabe. Jede weitere Route dort waere ungeschuetzt —
    genau die Bauart, die am 19.08. 55 offene Routen erzeugt hat (L-51).
    """
    from routers import briefings

    pfade = {r.path for r in briefings.kunden_router.routes}

    assert pfade == {"/api/briefings/{lead_id}/freigabe"}, pfade


def test_jede_innendienst_route_ist_gesichert():
    """Die Vorgabe am Router deckt sie alle — dieser Test sagt es, wenn
    jemand sie entfernt."""
    from routers import briefings

    # `fastapi.params.Depends` fuehrt die Funktion unter `dependency`,
    # nicht unter `call` — das steht am aufgeloesten `Dependant`.
    namen = {getattr(d.dependency, "__name__", "") for d in briefings.router.dependencies}

    assert "require_innendienst" in namen, (
        "Die Router-Vorgabe ist weg — dann haengt der Schutz wieder an jeder "
        "einzelnen Route.")


class TestSperrenBleiben:
    def test_der_kunde_aendert_kein_fremdes_briefing(self, client, kunde_headers):
        antwort = client.patch("/api/briefings/1", json={"projektrahmen": {}},
                               headers=kunde_headers)

        assert antwort.status_code == 403, antwort.text[:200]

    def test_die_freigabe_bleibt_ohne_innendienst_erreichbar(self, client):
        """`PATCH /{id}/freigabe` prueft den Token selbst aus dem Rumpf — ein
        Kunde muss sie erreichen. Eine Router-Vorgabe haette ihn gesperrt.
        """
        antwort = client.patch("/api/briefings/1/freigabe", json={"token": "falsch"})

        assert antwort.status_code != 401, antwort.text[:200]
