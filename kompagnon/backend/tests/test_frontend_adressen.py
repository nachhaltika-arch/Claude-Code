"""Jeder Aufruf des Frontends muss im Backend eine Route treffen.

Gefunden am 21.08.2026 beim Fertigstellen von M4 (`docs/module-karte.md`).
Die gesamte Bestellstrecke war gegen eine **andere** Schnittstelle
geschrieben, als es sie gibt — und es fiel nie auf, weil keine der Seiten
erreichbar war (L-64):

    CheckoutSuccess.jsx   /api/stripe/session/{}          → /api/payments/session/{}
    PackageStarter.jsx    /api/stripe/create-checkout-session
    PackageKompagnon.jsx  ebenso                          → /api/payments/create-checkout
    PackagePremium.jsx    ebenso

Beim Nachzaehlen kamen weitere heraus, die **nichts** mit dem Bestellweg zu
tun haben — die Paketverwaltung ruft zwei Endpunkte auf, die es nicht gibt.

**Warum ein Test und keine Liste von Reparaturen:** Ein falscher Pfad faellt
erst auf, wenn jemand die Seite benutzt. Ist die Seite nicht erreichbar oder
selten, faellt er nie auf. Der Test fragt die geladene Anwendung nach ihren
Routen und vergleicht sie mit dem, was im Frontend steht — beides
normalisiert, damit `${lead.id}` und `{lead_id}` als dasselbe gelten.
"""
import importlib
import pathlib
import re

import pytest


def _normalisieren(pfad: str) -> str:
    """`${projekt.id}` und `{project_id}` sind dieselbe Stelle."""
    pfad = re.sub(r"\$\{[^{}]*\}", "{}", pfad)
    pfad = re.sub(r"\{[^{}]*\}", "{}", pfad)
    return pfad.rstrip("/") or "/"


def _bekannte_adressen() -> set:
    import main

    bekannt = set()
    for route in main.app.routes:
        pfad = getattr(route, "path", None)
        if pfad:
            bekannt.add(_normalisieren(pfad))

    # Eingebundene Router legt diese FastAPI-Fassung als `_IncludedRouter` ab
    # und flacht ihre Routen nicht auf (19.08.2026) — deshalb zusaetzlich am
    # Router selbst nachsehen. Siehe [[feedback-am-gegenstand-pruefen]].
    wurzel = pathlib.Path(__file__).resolve().parent.parent / "routers"
    for datei in sorted(wurzel.glob("*.py")):
        if datei.stem == "__init__":
            continue
        modul = importlib.import_module(f"routers.{datei.stem}")
        for name in dir(modul):
            obj = getattr(modul, name)
            if type(obj).__name__ != "APIRouter":
                continue
            for route in getattr(obj, "routes", []):
                bekannt.add(_normalisieren(route.path))
    return bekannt


def _gerufene_adressen() -> dict:
    """Was das Frontend aufruft — Datei und Zeile je Adresse.

    Gelesen wird bis zum schliessenden Backtick, **nicht** ueber eine
    Zeichenklasse: Ein erster Entwurf schnitt bei `[`, `?` und Leerzeichen ab
    und meldete `/api/leads/${leadMatch` als fehlende Route. Vier von acht
    Befunden waren so entstanden — ein Waechter mit Fehlalarmen wird
    abgeschaltet.
    """
    fe = pathlib.Path(__file__).resolve().parents[2] / "frontend" / "src"
    gerufen = {}
    marke = "API_BASE_URL}"
    for datei in sorted(fe.rglob("*.js*")):
        if ".test." in datei.name:
            continue
        text = datei.read_text(encoding="utf-8", errors="ignore")
        start = text.find(marke)
        while start != -1:
            ab = start + len(marke)
            ende = text.find("`", ab)
            roh = text[ab:ende] if ende != -1 else ""
            if roh.startswith("/api/"):
                # Drei Schritte, und die Reihenfolge ist jedes Mal
                # aufgefallen, als sie falsch war:
                #   1. Einsetzungen ersetzen — `${lead?.id}` enthaelt ein
                #      Fragezeichen, das sonst als Abfrage gelesen wird
                #   2. die Abfrage abschneiden
                #   3. **dann** normalisieren, sonst bleibt der Schraegstrich
                #      aus `/api/leads/?limit=500` stehen
                adresse = _normalisieren(
                    re.sub(r"\$\{[^{}]*\}", "{}", roh).split("?", 1)[0]
                )
                # `${auditId}${abfrage}` wird zu `{}{}` — eine Stelle, nicht zwei.
                adresse = re.sub(r"(\{\})+", "{}", adresse)
                zeile = text[:start].count("\n") + 1
                gerufen.setdefault(adresse, set()).add(f"{datei.name}:{zeile}")
            start = text.find(marke, ab)
    return gerufen


#: Aufrufe, die heute ins Leere gehen und **nicht** zu M4 gehoeren.
#: Jeder gehoert zu einem Modul und wird dort behandelt — die Liste soll
#: schrumpfen, nie wachsen. Stand 21.08.2026.
GEPRUEFTE_LUECKEN = {
    "/api/academy/courses/reorder":            "M8 — Kursreihenfolge speichern",
    "/api/academy/modules/{}/lessons/reorder":  "M8 — Lektionsreihenfolge speichern",
    "/api/crawler/{}":                          "M1 — Crawler-Abfrage",
    "/api/leads/{}/sequence/{}":                "M10 — Mailstrecke je Betrieb",
    "/api/projects/{}/page-content/{}":         "M6 — Seiteninhalt",
    "/api/projects/{}/screenshot/{}":           "M6 — Screenshot je Seite",
    "/api/webhooks/{}":                         "M1 — Webhook-Verwaltung",
}


def test_kein_frontend_aufruf_geht_ins_leere():
    bekannt = _bekannte_adressen()
    fehlend = {
        adresse: sorted(wo)
        for adresse, wo in _gerufene_adressen().items()
        if adresse not in bekannt and adresse not in GEPRUEFTE_LUECKEN
    }

    assert fehlend == {}, (
        "Diese Adressen ruft das Frontend auf, im Backend gibt es sie nicht. "
        f"Der Aufruf scheitert erst, wenn jemand die Seite benutzt: {fehlend}"
    )


@pytest.mark.parametrize("adresse", sorted(GEPRUEFTE_LUECKEN))
def test_jede_bekannte_luecke_ist_noch_eine(adresse):
    """Sonst steht hier bald eine Liste, die niemand mehr prueft."""
    assert adresse not in _bekannte_adressen(), (
        f"{adresse} gibt es inzwischen — der Eintrag gehoert entfernt "
        f"({GEPRUEFTE_LUECKEN[adresse]})."
    )
