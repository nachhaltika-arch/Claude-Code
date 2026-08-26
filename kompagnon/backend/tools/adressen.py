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

#: **Was ausserhalb von `src` liegt und trotzdem ruft (26.08.2026).**
#: `public/embed/audit-widget.html` ist das **ausgelieferte** Widget —
#: eigenstaendiges Vanilla JS ohne Build, per iframe auf fremden Seiten
#: eingebunden. Es ruft vier `/api/widget/…`-Adressen, und weil es weder in
#: `src` liegt noch auf `.js` endet, galten die vier als „ruft niemand auf"
#: (L-105). Dieselbe Sorte Fehler wie zweimal darunter beschrieben: Wer nach
#: **einer** Form sucht, misst die Form und nicht die Sache.
OEFFENTLICH = WURZEL.parent / "frontend" / "public"

#: Die Marke, an der ein Backend-Aufruf im Frontend erkennbar ist.
MARKE = "API_BASE_URL}"


def normalisieren(pfad: str) -> str:
    """`${projekt.id}` und `{project_id}` sind dieselbe Stelle."""
    pfad = re.sub(r"\$\{[^{}]*\}", "{}", pfad)
    pfad = re.sub(r"\{[^{}]*\}", "{}", pfad)
    return pfad.rstrip("/") or "/"


def passt_auf(gerufene: str, route: str) -> bool:
    """Trifft eine gerufene Adresse diese Route — Abschnitt fuer Abschnitt?

    **Der dritte Messfehler desselben Tages (26.08.2026).** `L-105` meldete
    `POST /api/leads/{id}/sequence/start` als „ruft niemand auf". Den Knopf
    gibt es (`LeadProfile.jsx`, „Sequenz starten") — nur baut er die **Aktion**
    in den Pfad:

        `${API_BASE_URL}/api/leads/${leadId}/sequence/${action}`

    Der Schritt, der Vorlagen zu `{}` macht, trifft damit auch `${action}`,
    und `/api/leads/{}/sequence/{}` ist als **Zeichenkette** nicht
    `/api/leads/{}/sequence/start`.

    Ein Vergleich von Zeichenketten misst die Schreibweise. Hier wird
    verglichen, was gemeint ist: gleich viele Abschnitte, und je Abschnitt
    entweder derselbe Text oder auf einer der beiden Seiten ein Platzhalter.

    (Es ist der dritte Fall an einem Tag — davor: `public/` wurde nicht
    gelesen, und `+`-Verkettung nicht verstanden. Wer nach **einer** Form
    sucht, misst die Form und nicht die Sache.)
    """
    a = gerufene.strip("/").split("/")
    b = route.strip("/").split("/")
    if len(a) != len(b):
        return False
    return all(x == y or x == "{}" or y == "{}" for x, y in zip(a, b))


def trifft_ende(gerufene_rest: list, routen_ende: list) -> bool:
    """Wie `passt_auf`, aber **einseitig** — fuer den Vergleich mit dem Ende.

    `passt_auf` laesst `{}` auf beiden Seiten gelten. Beim Vergleich mit dem
    **Ende** einer Route ist das verheerend: `{}/editor` traefe auch
    `/api/leads/{lead_id}` — der Parameter der Route schluckt das Wort
    `editor`. So kamen 84 „moegliche Routen" fuer einen Aufruf heraus, der
    genau zwei meint.

    Hier darf nur der Platzhalter des **Aufrufs** etwas offen lassen. Ein
    Wort im Aufruf muss ein Wort in der Route sein.
    """
    if len(gerufene_rest) != len(routen_ende):
        return False
    return all(x == y or x == "{}"
               for x, y in zip(gerufene_rest, routen_ende))


def trifft_irgendeine(gerufene: str, routen) -> bool:
    """Landet dieser Aufruf auf **irgendeiner** dieser Routen?

    **Warum das hier steht und nicht in einem der beiden Werkzeuge
    (26.08.2026).** Der Kopf von `unaufgerufene-routen.py` sagt, beide
    Werkzeuge laesen dieselbe Grundlage, „damit sie nicht auseinanderdriften".
    Sie waren auseinandergedriftet: Das eine verglich abschnittsweise, das
    andere mit `in`. Eine Begruendung im Kopftext ist keine Verbindung — der
    gemeinsame Code ist eine.

    Drei Formen werden erkannt:

    1. gleich — die haeufige;
    2. abschnittsweise gleich lang, etwa `/api/leads/{}/sequence/{}` gegen
       `/api/leads/{id}/sequence/start`, weil der Knopf die Aktion in den
       Pfad baut;
    3. der Anfang ist eine Variable (`${endpointBase}/${pageId}/editor`) —
       dann zaehlt das **Ende** der Route.
    """
    ziele = {normalisieren(r) for r in routen}
    if gerufene in ziele:
        return True

    teile = gerufene.strip("/").split("/")
    if set(teile) == {"{}"}:
        # Eine Adresse, die nur aus Platzhaltern besteht (`apiCall(url)`),
        # sagt ueber keine Route etwas aus — und traf sonst jede.
        return False

    for ziel in ziele:
        eigene = ziel.strip("/").split("/")
        if trifft_ende(teile, eigene):
            return True
        if teile[0] == "{}" and 0 < len(teile) - 1 < len(eigene):
            if trifft_ende(teile[1:], eigene[-(len(teile) - 1):]):
                return True
    return False


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


def ohne_kommentare(text: str) -> str:
    """JavaScript ohne `//`- und `/* */`-Kommentare.

    **Warum es das braucht (26.08.2026).** Der Waechter meldete
    `/api/briefings` als Aufruf einer Route, die es nicht gibt. Gerufen wurde
    sie nie — sie stand in einem **Kommentar**, in Backticks, und die Marke
    oben sucht genau zwischen Anfuehrungszeichen und Backticks.

    Dieser Bestand erklaert sich ausfuehrlich und nennt dabei staendig
    Adressen: `/api/briefings/{id}`, `/api/leads/{id}`. Jede davon waere ein
    Fehlalarm, und ein Waechter mit Fehlalarmen wird abgeschaltet — das steht
    schon zweimal im Kopf dieser Datei.

    **Zeichenweise, nicht per Muster.** Ein Ausdruck ueber Kommentare stolpert
    ueber `'http://…'` in einer Zeichenkette und ueber `/regex/`-Literale.
    Hier wird gezaehlt: in welchem Anfuehrungszeichen stehe ich gerade, und
    beginnt hier wirklich ein Kommentar.
    """
    ergebnis = []
    i, laenge = 0, len(text)
    anfuehrung = None

    while i < laenge:
        z = text[i]

        if anfuehrung:
            ergebnis.append(z)
            if z == "\\" and i + 1 < laenge:      # maskiertes Zeichen mitnehmen
                ergebnis.append(text[i + 1])
                i += 2
                continue
            if z == anfuehrung:
                anfuehrung = None
            i += 1
            continue

        if z in "\"'`":
            anfuehrung = z
            ergebnis.append(z)
            i += 1
            continue

        if text.startswith("//", i):
            ende = text.find("\n", i)
            i = laenge if ende == -1 else ende
            continue

        if text.startswith("/*", i):
            ende = text.find("*/", i + 2)
            # Zeilenumbrueche behalten, damit Zeilennummern stimmen.
            block = text[i:laenge if ende == -1 else ende + 2]
            ergebnis.append("\n" * block.count("\n"))
            i = laenge if ende == -1 else ende + 2
            continue

        ergebnis.append(z)
        i += 1

    return "".join(ergebnis)


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


def routen_mit_funktion() -> dict:
    """(Methode, Pfad) → Name der Handler-Funktion.

    Gebraucht für die dritte Sorte Aufrufer: **Backend-Code, der die Funktion
    direkt aufruft, statt über HTTP zu gehen.** `projects_anlegen.py` holt
    sich `screenshot_after` aus `projects_erhebung` und ruft es in der
    Go-live-Kette auf. Die Route sieht von außen ungerufen aus und ist es
    nicht — sie hat nur keinen Knopf, sondern einen Aufrufer.
    """
    import main

    raus = {}

    def sammeln(routen, praefix=""):
        for route in routen:
            eingebunden = getattr(route, "original_router", None)
            if eingebunden is not None:
                kontext = getattr(route, "include_context", None)
                sammeln(eingebunden.routes,
                        praefix + (getattr(kontext, "prefix", "") or ""))
                continue
            pfad = getattr(route, "path", None)
            methoden = getattr(route, "methods", None)
            ziel = getattr(route, "endpoint", None)
            if not (pfad and methoden and ziel is not None):
                continue
            for methode in methoden:
                raus[(methode, praefix + pfad)] = getattr(ziel, "__name__", "")

    sammeln(main.app.routes)
    return raus


#: `from <modul> import <name>` — der einzige Weg, der eindeutig ist.
_IMPORT_AUS = re.compile(r"^\s*from ([\w.]+) import ([^\n#]+)", re.MULTILINE)


def importe_je_modul() -> dict:
    """(Herkunftsmodul, Name) → Module, die genau das importieren.

    **Warum nur Importe und keine Aufrufe (24.08.2026).** Der erste Anlauf
    suchte den Funktionsnamen als Aufruf im ganzen Baum. Das ergab dreimal
    Unsinn, und jedes Mal aus einem anderen Grund:

    * `get_active_jobs()` stand in einem **Kommentar** in `scheduler.py`.
    * `widget_report.verify_email(...)` ist eine **Namensvetterin** des
      Handlers `verify_email` aus `auth_router`.
    * `MarginCalculator.log_time(...)` heisst wie der Handler `log_time`,
      ist aber eine Methode einer ganz anderen Klasse.

    Namen quer durch einen Baum zu vergleichen ist grundsaetzlich mehrdeutig.
    Eindeutig ist nur: **Wer einen Handler wirklich benutzt, importiert ihn
    aus seinem Modul** — so wie `projects_anlegen` es mit `screenshot_after`
    aus `projects_erhebung` tut. Danach wird gesucht, und nur danach.

    Der Preis: Ein `import routers.x` mit spaeterem `routers.x.handler()`
    faellt durch. Diese Form kommt hier nicht vor; lieber eine Frage zu viel
    in der Liste als eine falsche Entwarnung.
    """
    raus = {}
    for pfad in WURZEL.rglob("*.py"):
        teile = pfad.relative_to(WURZEL).parts
        if any(t in ("venv", "tests", "__pycache__", "tools") for t in teile):
            continue
        modul = ".".join(pfad.relative_to(WURZEL).with_suffix("").parts)
        text = pfad.read_text(encoding="utf-8", errors="ignore")
        for herkunft, zeile in _IMPORT_AUS.findall(text):
            for teil in zeile.replace("(", "").replace(")", "").split(","):
                name = teil.strip().split(" as ")[0].strip()
                if name:
                    raus.setdefault((herkunft, name), set()).add(modul)
    return raus


def gerufene_adressen() -> dict:
    """Was das Frontend aufruft — Datei und Zeile je Adresse.

    Gelesen wird bis zum schliessenden Backtick, **nicht** ueber eine
    Zeichenklasse: Ein erster Entwurf schnitt bei `[`, `?` und Leerzeichen ab
    und meldete `/api/leads/${leadMatch` als fehlende Route. Vier von acht
    Befunden waren so entstanden — ein Waechter mit Fehlalarmen wird
    abgeschaltet.
    """
    gerufen = {}
    quellen = list(FRONTEND.rglob("*.js*"))
    if OEFFENTLICH.is_dir():
        quellen += list(OEFFENTLICH.rglob("*.html"))
    for datei in sorted(quellen):
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
        if datei.suffix in (".js", ".jsx", ".html"):
            # Kommentare zaehlen nicht mit — siehe `ohne_kommentare`.
            sauber = ohne_kommentare(text)
            for treffer in _PFAD_IM_TEXT.finditer(sauber):
                roh = treffer.group(1)
                ab = roh.index("/api/")
                adresse = normalisieren(
                    re.sub(r"\$\{[^{}]*\}", "{}", roh[ab:]).split("?", 1)[0]
                )
                adresse = re.sub(r"(\{\})+", "{}", adresse)

                # **Verkettung mit `+` (26.08.2026).** In `src` werden
                # Adressen als Vorlage geschrieben (`${id}`), und die ersetzt
                # der Schritt darueber. Das ausgelieferte Widget ist Vanilla
                # JS ohne Build und schreibt
                # `'/api/widget/teaser/' + encodeURIComponent(token)`.
                # Ohne diese Zeilen endete die Adresse auf einem Schraegstrich
                # und traf `/api/widget/teaser/{token}` nicht — zwei
                # Fehlalarme, kaum dass `public/` mitgelesen wurde. Ein
                # Waechter mit Fehlalarmen wird abgeschaltet.
                danach = sauber[treffer.end():treffer.end() + 4].lstrip()
                if roh.endswith("/") and danach.startswith("+"):
                    adresse = adresse.rstrip("/") + "/{}"

                zeile = sauber[:treffer.start()].count("\n") + 1
                gerufen.setdefault(adresse, set()).add(f"{datei.name}:{zeile}")

        start = text.find(MARKE)
        while start != -1:
            ab = start + len(MARKE)
            ende = text.find("`", ab)
            roh = text[ab:ende] if ende != -1 else ""

            # **Eine Variable kann fuer den ganzen Anfang stehen
            # (26.08.2026).** `GrapesEditor` ruft
            # `${API_BASE_URL}${endpointBase}/${pageId}/editor` auf, und
            # `endpointBase` ist `/api/pages` oder `/api/kas/pages`. Hier
            # folgte auf die Marke kein `/api/`, also galt der Aufruf als
            # nicht vorhanden — und fuenf angeschlossene Routen standen als
            # „ruft niemand auf" da. Die Adresse wird zu `/{}/...`; das
            # fuehrende `{}` ist das Kennzeichen, an dem das Zaehlwerkzeug
            # sie am **Ende** der Route vergleicht statt am Anfang.
            if roh.startswith("${") and "}" in roh:
                roh = "/{}" + roh[roh.index("}") + 1:]

            # Eine Adresse, die **nur** aus Platzhaltern besteht, ist keine.
            # `apiCall(url)` in `AuthContext` und `${a.src}` im Bildverwalter
            # bekommen den Pfad von aussen; aufgezeichnet sagt `/{}` in beide
            # Richtungen nichts und trifft alles.
            if set(normalisieren(roh).strip("/").split("/")) == {"{}"}:
                start = text.find(MARKE, ab)
                continue

            if roh.startswith("/api/") or roh.startswith("/{}"):
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
