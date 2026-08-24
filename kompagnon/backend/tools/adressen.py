"""Welche Adressen kennt das Backend, welche ruft das Frontend? (L-101)

Gemeinsame Grundlage für zwei Richtungen derselben Frage:

* ``tests/test_frontend_adressen.py`` prüft die **Hin**richtung — jeder Aufruf
  des Frontends muss im Backend eine Route treffen. Ein falscher Pfad fällt
  sonst erst auf, wenn jemand die Seite benutzt.
* ``tools/unaufgerufene-routen.py`` zeigt die **Rück**richtung — welche Route
  ruft niemand auf.

**Warum die Rückrichtung dazugekommen ist (24.08.2026).** „Gebaut, nicht
angeschlossen" ist in diesem System eine eigene Fehlerfamilie: L-55 (der
Wächter, der nie aufgerufen wurde), L-79 (die Seitenfreigabe ohne Knopf),
L-11 (``_fernet_available``, nie gerufen und dann als überflüssig gelöscht)
und am 24.08. ``POST /api/projects/{id}/time`` — die Zeiterfassung, an der
die Margenrechnung hängt und die im ganzen Frontend niemand aufruft.

Viermal derselbe Fund, viermal von Hand entdeckt. Deshalb eine Messung.

**Es ist ein Werkzeug und kein Test**, und das ist Absicht: „Ruft niemand auf"
ist oft völlig richtig. Webhooks werden von außen gerufen, das Widget lebt auf
fremden Seiten, Portalrouten hängen an einem Einmal-Token, und manches ruft
der Scheduler. Ein Test daraus würde entweder ständig rot sein oder eine
Ausnahmeliste pflegen, die niemand liest.
"""
import importlib
import pathlib
import re

WURZEL = pathlib.Path(__file__).resolve().parent.parent
FRONTEND = WURZEL.parent / "frontend" / "src"

#: Die Marke, an der ein Backend-Aufruf im Frontend erkennbar ist.
MARKE = "API_BASE_URL}"


def normalisieren(pfad: str) -> str:
    """`${projekt.id}` und `{project_id}` sind dieselbe Stelle."""
    pfad = re.sub(r"\$\{[^{}]*\}", "{}", pfad)
    pfad = re.sub(r"\{[^{}]*\}", "{}", pfad)
    return pfad.rstrip("/") or "/"


def bekannte_adressen() -> set:
    """Alle Adressen, die das Backend führt — normalisiert."""
    import main

    bekannt = set()
    for route in main.app.routes:
        pfad = getattr(route, "path", None)
        if pfad:
            bekannt.add(normalisieren(pfad))

    # Eingebundene Router legt diese FastAPI-Fassung als `_IncludedRouter` ab
    # und flacht ihre Routen nicht auf (19.08.2026) — deshalb zusaetzlich am
    # Router selbst nachsehen.
    for datei in sorted((WURZEL / "routers").glob("*.py")):
        if datei.stem == "__init__":
            continue
        modul = importlib.import_module(f"routers.{datei.stem}")
        for name in dir(modul):
            obj = getattr(modul, name)
            if type(obj).__name__ != "APIRouter":
                continue
            for route in getattr(obj, "routes", []):
                bekannt.add(normalisieren(route.path))
    return bekannt


def routen_mit_methode() -> list:
    """(Methode, Pfad) aus dem OpenAPI-Schema — für die Rückrichtung.

    Das Schema statt der Router, weil es die Methoden mitliefert und weil
    `app.routes` unter Starlette 1.4 nur die oberste Ebene zeigt.
    """
    import main

    schema = main.app.openapi()
    return [
        (methode.upper(), pfad)
        for pfad, operationen in schema["paths"].items()
        for methode in operationen
        if methode.lower() in {"get", "post", "put", "patch", "delete"}
    ]


#: Weitere Bäume, die das Backend rufen — ohne `${API_BASE_URL}`.
WEITERE_QUELLEN = (
    ("Widget", WURZEL.parent / "frontend" / "public", ("*.html",)),
    ("E2E", WURZEL.parent / "e2e" / "tests", ("*.js", "*.ts")),
)

#: Ein Pfad in Anführungszeichen, irgendwo eine `/api/`-Stelle enthaltend.
_PFAD_IM_TEXT = re.compile(r"""['"`]([^'"`\s]*/api/[^'"`\s]*)['"`]""")


def weitere_aufrufer() -> dict:
    """Adressen aus Widget und E2E-Tests — Adresse → Herkunft.

    **Warum getrennt vom Frontend (24.08.2026).** Die Marke `${API_BASE_URL}`
    findet nur, was die React-Anwendung ruft. Zwei Bäume rufen anders:

    * `public/embed/audit-widget.html` setzt `API_BASE + '/api/widget/config'`
      zusammen — es lebt eingebettet auf fremden Seiten und kennt die
      React-Konstante nicht.
    * die Playwright-Tests schreiben nackte Pfade (`/api/projects/${id}/…`).

    Beide zählen, aber nicht gleich: Was **nur** ein E2E-Test ruft, ist die
    Entsprechung zu „nur von Tests importiert" im Werkzeug für tote Dateien —
    grüne Prüfung für einen Weg, den kein Mensch geht.

    Der Ausdruck ist absichtlich weit und findet deshalb auch einen Pfad, der
    bloß in einer Fehlermeldung steht. Für die Frage „ruft das überhaupt
    jemand?" ist Übermelden das kleinere Übel: Es macht die Liste kürzer, nie
    einen Fund unsichtbar.
    """
    gefunden = {}
    for herkunft, wurzel, muster in WEITERE_QUELLEN:
        if not wurzel.is_dir():
            continue
        for endung in muster:
            for datei in sorted(wurzel.rglob(endung)):
                if "node_modules" in datei.parts:
                    continue
                text = datei.read_text(encoding="utf-8", errors="ignore")
                for roh in _PFAD_IM_TEXT.findall(text):
                    ab = roh.index("/api/")
                    adresse = normalisieren(
                        re.sub(r"\$\{[^{}]*\}", "{}", roh[ab:]).split("?", 1)[0]
                    )
                    adresse = re.sub(r"(\{\})+", "{}", adresse)
                    gefunden.setdefault(adresse, set()).add(
                        f"{herkunft}:{datei.name}")
    return gefunden


def gerufene_adressen() -> dict:
    """Was das Frontend aufruft — Datei und Zeile je Adresse.

    Gelesen wird bis zum schliessenden Backtick, **nicht** ueber eine
    Zeichenklasse: Ein erster Entwurf schnitt bei `[`, `?` und Leerzeichen ab
    und meldete `/api/leads/${leadMatch` als fehlende Route. Vier von acht
    Befunden waren so entstanden — ein Waechter mit Fehlalarmen wird
    abgeschaltet.
    """
    gerufen = {}
    for datei in sorted(FRONTEND.rglob("*.js*")):
        if ".test." in datei.name:
            continue
        text = datei.read_text(encoding="utf-8", errors="ignore")

        # **Nackte Pfade zaehlen mit (24.08.2026).** Die Marke oben findet nur
        # `fetch(`${API_BASE_URL}/api/…`)`. Vier Helfer nehmen aber den Pfad
        # **ohne** Basis entgegen — `apiCall` (20 Aufrufe), `loadJson` (71),
        # `saveJson` (17), `apiRequest` (5) —, und die haengen die Basis
        # selbst an. Ohne diese Zeilen galten 29 Adressen als nie gerufen,
        # darunter die ganze Benutzer- und Rollenverwaltung
        # (`/api/admin/users`, `/api/admin/roles`, `/api/admin/settings`).
        #
        # Dieselbe Verwechslung wie beim Werkzeug fuer tote Dateien: dort der
        # Dateiname statt des Modulpfads, hier eine von vier Schreibweisen
        # statt aller. Wer nach **einer** Form sucht, misst die Form, nicht
        # die Sache.
        # **Nur echter Code, nicht `.json`.** `rglob("*.js*")` trifft auch
        # Datendateien, und `data/index.json` fuehrt Beispiel-Pfade wie
        # `/api/leads/booking` als Inhalt. Der bestehende Test der
        # Gegenrichtung hat das sofort gemeldet — vier Adressen, die niemand
        # ruft, weil sie gar kein Aufruf sind. Die Marke oben war davon nie
        # betroffen; sie kommt in JSON nicht vor.
        if datei.suffix in (".js", ".jsx"):
            for roh in _PFAD_IM_TEXT.findall(text):
                ab = roh.index("/api/")
                adresse = normalisieren(
                    re.sub(r"\$\{[^{}]*\}", "{}", roh[ab:]).split("?", 1)[0]
                )
                adresse = re.sub(r"(\{\})+", "{}", adresse)
                zeile = text[:text.index(roh)].count("\n") + 1
                gerufen.setdefault(adresse, set()).add(f"{datei.name}:{zeile}")

        start = text.find(MARKE)
        while start != -1:
            ab = start + len(MARKE)
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
                adresse = normalisieren(
                    re.sub(r"\$\{[^{}]*\}", "{}", roh).split("?", 1)[0]
                )
                # `${auditId}${abfrage}` wird zu `{}{}` — eine Stelle, nicht zwei.
                adresse = re.sub(r"(\{\})+", "{}", adresse)
                zeile = text[:start].count("\n") + 1
                gerufen.setdefault(adresse, set()).add(f"{datei.name}:{zeile}")
            start = text.find(MARKE, ab)
    return gerufen
