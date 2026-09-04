# -*- coding: utf-8 -*-
"""Die Pruefstufen, die ohne laufenden Dienst auskommen.

Jede Funktion hier misst **eine** Fehlerklasse, und jede dieser Klassen hat
im Repo schon einmal Schaden angerichtet. Das ist der Massstab fuer die
Aufnahme: Eine Pruefung kommt dazu, wenn sie einen Fehler gefunden haette,
der tatsaechlich passiert ist — nicht, weil sie sich gut liest.

    doppelte_routen()      → L-76: zwei Verfahren auf einer Adresse
    namensdrift_umgebung() → L-43: derselbe Schluessel, zwei Namen
    felder_ohne_leser()    → L-55: gespeichert, angezeigt, nie gelesen
    seiten_ohne_route()    → eine Seite, die niemand aufrufen kann
    farben_ausserhalb()    → Optik: Farben neben dem Designsystem
    zu_grosse_dateien()    → L-25: Dateien ueber der Grenze

Alle lesen den Quelltext, keine braucht Netz oder Abhaengigkeiten. Was nur
am laufenden Dienst messbar ist, steht in `laufzeit.py`.
"""
from __future__ import annotations

import ast
import collections
import pathlib
import re

from .befund import Befund, WURZEL

BACKEND = WURZEL / "kompagnon" / "backend"
FRONTEND = WURZEL / "kompagnon" / "frontend" / "src"

_METHODEN = ("get", "post", "put", "patch", "delete")


# ── Inventar ────────────────────────────────────────────────────────────────

def _py_dateien(ordner: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in ordner.rglob("*.py") if "venv" not in p.parts and "__pycache__" not in p.parts]


def _js_dateien() -> list[pathlib.Path]:
    return [
        p for p in FRONTEND.rglob("*")
        if p.suffix in (".js", ".jsx") and "node_modules" not in p.parts
    ]


def routen_erheben() -> tuple[dict[tuple[str, str], list[str]], int]:
    """(METHODE, Pfad) → Fundstellen, dazu die Zahl der **nicht** messbaren.

    **Warum die zweite Zahl.** Ein Router, dessen Praefix nicht in derselben
    Datei steht, hat aus Sicht des Quelltextes keinen bekannten Pfad —
    `kunden_router` in `routers/projects.py` bekommt ihn erst bei der
    Registrierung. Wer solche Treffer trotzdem mit einem leeren Praefix
    fuehrt, erzeugt Scheindoppelungen: Der erste Lauf dieses Werkzeugs meldete
    `GET /` als doppelt registriert, und beide Fundstellen lagen in
    verschiedenen Routern. Nicht messbar heisst hier **nicht messbar** und
    wird gezaehlt, nicht geraten.

    Die genauere Erhebung liest die geladene Anwendung
    (`kompagnon/backend/tools/endpunkte_auflisten.py`); sie braucht dafuer die
    Umgebung des Backends. Diese hier laeuft ueberall und sagt, was sie nicht sieht.
    """
    gefunden: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    ungewiss = 0
    for datei in _py_dateien(BACKEND / "routers") + [BACKEND / "main.py"]:
        if not datei.exists():
            continue
        try:
            baum = ast.parse(datei.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        praefixe: dict[str, str] = {}
        for knoten in ast.walk(baum):
            if isinstance(knoten, ast.Assign) and isinstance(knoten.value, ast.Call):
                aufruf = knoten.value
                name = getattr(aufruf.func, "id", getattr(aufruf.func, "attr", ""))
                if name == "APIRouter":
                    praefix = ""
                    for kw in aufruf.keywords:
                        if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                            praefix = kw.value.value
                    for ziel in knoten.targets:
                        if isinstance(ziel, ast.Name):
                            praefixe[ziel.id] = praefix
        for knoten in ast.walk(baum):
            if not isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for deko in knoten.decorator_list:
                if not isinstance(deko, ast.Call):
                    continue
                f = deko.func
                if not isinstance(f, ast.Attribute) or f.attr not in _METHODEN:
                    continue
                traeger = getattr(f.value, "id", "")
                if not deko.args or not isinstance(deko.args[0], ast.Constant):
                    continue
                stelle = f"{datei.relative_to(WURZEL)}:{knoten.lineno}"
                praefix = praefixe.get(traeger)
                # Ohne eigenen, nicht leeren Praefix ist der absolute Pfad
                # aus dem Quelltext nicht bestimmbar.
                if not praefix:
                    ungewiss += 1
                    continue
                gefunden[(f.attr.upper(), praefix + deko.args[0].value)].append(stelle)
    return gefunden, ungewiss


# ── L-76: zwei Verfahren auf einer Adresse ──────────────────────────────────

def doppelte_routen() -> list[Befund]:
    """Dieselbe Methode auf demselben Pfad, an zwei Stellen registriert.

    FastAPI bedient in so einem Fall die **zuerst** registrierte und
    verschweigt die zweite. Am 22.08.2026 lagen so zwei Freigabeverfahren auf
    einer Adresse (L-76); die Kundenportal-Kette war dadurch unterbrochen,
    ohne dass irgendwo ein Fehler erschien.
    """
    befunde = []
    routen, _ungewiss = routen_erheben()
    for (methode, pfad), stellen in sorted(routen.items()):
        if len(stellen) < 2:
            continue
        befunde.append(Befund(
            kennung=f"doppelroute/{methode}{pfad}",
            ebene="schnittstelle",
            titel=f"{methode} {pfad} ist {len(stellen)}-mal registriert",
            beleg=" · ".join(stellen),
            einzelheiten=(
                "FastAPI bedient die zuerst registrierte Fassung; jede weitere "
                "ist unerreichbar, ohne dass ein Fehler erscheint. Zu pruefen, "
                "ob beide dasselbe tun — sonst ist die stillgelegte Fassung ein "
                "unterbrochener Ablauf wie in L-76."
            ),
            vorschlag="P0",
            gegenstand=pfad,
        ))
    return befunde


# ── L-43: derselbe Schluessel unter zwei Namen ──────────────────────────────

_GETENV = re.compile(r"(?:os\.getenv|os\.environ\.get)\(\s*[\"']([A-Z0-9_]+)[\"']")
_REACT_ENV = re.compile(r"process\.env\.(REACT_APP_[A-Z0-9_]+)")


def _kern(name: str) -> str:
    """Der Wortkern eines Variablennamens — ohne Anbieter- und Rollenvorsatz.

    `GOOGLE_PAGESPEED_API_KEY` und `PAGESPEED_API_KEY` teilen den Kern
    `pagespeed`. Genau dieser Unterschied kostete in L-43 sieben Fundstellen.
    """
    teile = [t for t in name.lower().split("_") if t not in
             ("api", "key", "url", "secret", "token", "google", "react", "app", "id")]
    return "_".join(teile)


def namensdrift_umgebung() -> list[Befund]:
    """Zwei Namen fuer denselben Schluessel — und wo nur einer gesetzt ist."""
    fundstellen: dict[str, list[str]] = collections.defaultdict(list)
    for datei in _py_dateien(BACKEND):
        if "tests" in datei.parts:
            continue
        try:
            text = datei.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name in _GETENV.findall(text):
            fundstellen[name].append(str(datei.relative_to(WURZEL)))

    # Was steht in den Blueprints?
    gesetzt = set()
    for name in ("render.yaml", "render-staging.yaml", "render-produktiv.yaml"):
        datei = WURZEL / "kompagnon" / name
        if datei.exists():
            gesetzt |= set(re.findall(r"key:\s*([A-Z0-9_]+)", datei.read_text(encoding="utf-8")))

    nach_kern: dict[str, set[str]] = collections.defaultdict(set)
    for name in fundstellen:
        kern = _kern(name)
        if kern:
            nach_kern[kern].add(name)

    befunde = []
    for kern, namen in sorted(nach_kern.items()):
        if len(namen) < 2:
            continue
        beschreibung = []
        for n in sorted(namen):
            wo = sorted(set(fundstellen[n]))
            marke = "im Blueprint" if n in gesetzt else "**nicht** im Blueprint"
            beschreibung.append(f"`{n}` — {len(wo)} Fundstelle(n), {marke}")
        befunde.append(Befund(
            kennung=f"namensdrift/{kern}",
            ebene="konsistenz",
            titel=f"Zwei Namen fuer denselben Schluessel: {' / '.join(sorted(namen))}",
            beleg=" · ".join(sorted({s for n in namen for s in fundstellen[n]})[:6]),
            einzelheiten=(
                " — ".join(beschreibung)
                + ". Dieselbe Form wie L-43: Dort war der Schluessel an einer Stelle "
                  "umbenannt und an sechs weiteren nicht; die sechs lasen monatelang leer."
            ),
            vorschlag="P1",
            gegenstand=sorted(namen)[0],
        ))
    return befunde


def umgebung_ohne_blueprint() -> list[Befund]:
    """Variablen, die der Code liest, die aber in keinem Blueprint stehen."""
    gelesen: dict[str, list[str]] = collections.defaultdict(list)
    for datei in _py_dateien(BACKEND):
        if "tests" in datei.parts or "tools" in datei.parts:
            continue
        try:
            text = datei.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name in _GETENV.findall(text):
            gelesen[name].append(f"{datei.relative_to(WURZEL)}")

    gesetzt = set()
    for name in ("render.yaml", "render-staging.yaml", "render-produktiv.yaml"):
        datei = WURZEL / "kompagnon" / name
        if datei.exists():
            gesetzt |= set(re.findall(r"key:\s*([A-Z0-9_]+)", datei.read_text(encoding="utf-8")))

    befunde = []
    for name, stellen in sorted(gelesen.items()):
        if name in gesetzt or len(stellen) < 2:
            continue
        befunde.append(Befund(
            kennung=f"umgebung-fehlt/{name}",
            ebene="konsistenz",
            titel=f"`{name}` wird an {len(set(stellen))} Stellen gelesen, steht in keinem Blueprint",
            beleg=" · ".join(sorted(set(stellen))[:5]),
            einzelheiten=(
                "Der Blueprint beschreibt die Umgebung. Fehlt der Schluessel dort, "
                "haengt der Betrieb an einem Dashboard-Eintrag, den niemand "
                "nachlesen kann — die Form von L-42, wo `ENVIRONMENT` produktiv "
                "nie gesetzt war und der Vorgabewert `development` griff."
            ),
            vorschlag="P1",
            gegenstand=name,
        ))
    return befunde


# ── L-55: gespeichert, angezeigt, nie gelesen ───────────────────────────────

_COLUMN = re.compile(r"^\s*(\w+)\s*=\s*Column\(", re.MULTILINE)


def felder_ohne_leser() -> list[Befund]:
    """Modellfelder, die ausser im Modell nirgends vorkommen.

    Die Familie L-05 / L-55: Ein Feld ist gespeichert, im Admin anklickbar,
    wird serialisiert — und von keinem Lesepfad je abgefragt. Die Oberflaeche
    verspricht dann eine Wirkung, die es nicht gibt.
    """
    modelle = list(BACKEND.glob("modelle_*.py")) + list(BACKEND.glob("models*.py"))
    andere = [p for p in _py_dateien(BACKEND) if p not in modelle and "tests" not in p.parts]
    heuhaufen = ""
    for p in andere:
        try:
            heuhaufen += p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            pass
    frontend_text = ""
    for p in _js_dateien():
        try:
            frontend_text += p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            pass

    befunde = []
    for modell in modelle:
        text = modell.read_text(encoding="utf-8")
        for feld in sorted(set(_COLUMN.findall(text))):
            if feld in ("id", "created_at", "updated_at") or len(feld) < 6:
                continue
            if feld in heuhaufen or feld in frontend_text:
                continue
            befunde.append(Befund(
                kennung=f"feld-ohne-leser/{modell.stem}.{feld}",
                ebene="datenbank",
                titel=f"`{feld}` ({modell.name}) kommt ausserhalb des Modells nirgends vor",
                beleg=f"{modell.relative_to(WURZEL)} — kein Treffer in Backend ausserhalb der Modelle und in {len(_js_dateien())} Frontend-Dateien",
                einzelheiten=(
                    "Entweder ist die Spalte tote Last, oder ein Lesepfad fehlt. "
                    "Dieselbe Familie wie L-55: `AcademyModule.is_locked` war "
                    "gespeichert, anklickbar, serialisiert — und nirgends gelesen."
                ),
                vorschlag="P3",
                gegenstand=feld,
            ))
    return befunde


# ── Kette Frontend → Browser ────────────────────────────────────────────────

def seiten_ohne_route() -> list[Befund]:
    """Seitendateien, die weder eine Route haben noch irgendwo importiert werden.

    **Warum die zweite Bedingung.** Der erste Lauf meldete vier Seiten als
    „ohne Route": `PackageStarter`, `PackagePremium`, `PackageKompagnon` und
    `Rechtstext`. Alle vier gibt es zu Recht — `PaketSeite.jsx` waehlt die
    ersten drei nach Kuerzel aus, und `Rechtstext` ist das gemeinsame Layout
    von AGB und Widerrufsbelehrung. Sie liegen im Ordner `pages/`, sind aber
    Bausteine. Wer nur `App.jsx` befragt, meldet jeden davon als Leiche.

    Uebrig bleibt der echte Fall: eine Datei, die **niemand** einbindet — kein
    Weg dorthin, kein Aufrufer, und trotzdem Pflegeaufwand.
    """
    app = FRONTEND / "App.jsx"
    if not app.exists():
        return []
    routen_text = app.read_text(encoding="utf-8")
    andere = ""
    for datei in _js_dateien():
        if datei.name == "App.jsx":
            continue
        try:
            andere += datei.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            pass

    befunde = []
    for seite in sorted((FRONTEND / "pages").glob("*.jsx")):
        if seite.stem in routen_text:
            continue
        if f"/{seite.stem}'" in andere or f"/{seite.stem}\"" in andere:
            continue          # wird als Baustein importiert
        befunde.append(Befund(
            kennung=f"seite-ohne-weg/{seite.stem}",
            ebene="frontend",
            titel=f"`pages/{seite.name}` hat keine Route und wird nirgends importiert",
            beleg=f"{seite.relative_to(WURZEL)} — kein Treffer in src/App.jsx und in "
                  f"keiner der {len(_js_dateien())} uebrigen Frontend-Dateien",
            einzelheiten=(
                "Weder ueber eine Adresse erreichbar noch als Baustein eingebunden. "
                "Entweder fehlt der Weg dorthin, oder die Datei ist der Rest einer "
                "frueheren Fassung und traegt Pflegeaufwand ohne Nutzen."
            ),
            vorschlag="P3",
            gegenstand=seite.name,
        ))
    return befunde


# ── Optik: Farben neben dem System ──────────────────────────────────────────

_HEX = re.compile(r"#([0-9a-fA-F]{6})\b")


def _palette() -> set[str]:
    """Die Farben, die das Designsystem kennt — aus der Tailwind-Vorgabe."""
    datei = WURZEL / "kompagnon" / "frontend" / "tailwind.config.js"
    if not datei.exists():
        return set()
    return {h.lower() for h in _HEX.findall(datei.read_text(encoding="utf-8"))}


def _abstand(a: str, b: str) -> float:
    """Wie weit zwei Hex-Farben im RGB-Raum auseinanderliegen."""
    x = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    y = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return sum((p - q) ** 2 for p, q in zip(x, y)) ** 0.5


#: Die Kernfarben der Marke. Gegen **diese** wird auf Beinahe-Treffer geprueft,
#: nicht gegen die ganze Palette: Sie enthaelt auch Grautoene, und zwischen zwei
#: Grautoenen liegt immer einer — die Pruefung wuerde jeden davon melden.
MARKENKERN = ("008eaa", "002535", "fae600", "004f59", "007090")


def farben_ausserhalb(mindestens: int = 8, naehe: float = 30.0,
                      beinahe_ab: int = 3) -> list[Befund]:
    """Farben im Frontend, die in keiner Vorgabe stehen.

    **Zwei Befunde aus einer Messung, und das mit Absicht.** Der erste ist
    ein Sammelbefund: Wie viele Farben ausserhalb der Vorgabe stehen und an
    wie vielen Stellen. Das ist **eine** Entscheidung — Palette erweitern oder
    Quelltext aufraeumen — und keine sechzig.

    Der zweite Typ wird einzeln gemeldet: Farben, die einer Markenfarbe
    **aehneln**, ohne sie zu sein. Sie sind die gefaehrliche Klasse, weil sie
    im Bildschirmfoto richtig aussehen und in der Druckvorstufe auffliegen;
    L-17 fuehrt mit `#3f9fb2` und `#2a5a6a` genau solche Faelle.
    """
    erlaubt = _palette() | {"ffffff", "000000"}
    treffer: dict[str, list[str]] = collections.defaultdict(list)
    for datei in _js_dateien() + list(FRONTEND.rglob("*.css")):
        # Fremdvorlagen (hyperui, relume) und die Bausteinbibliothek bringen
        # ihre eigenen Farben mit; sie am eigenen Designsystem zu messen,
        # erzeugt 180 Zeilen Rauschen und keinen einzigen Befund.
        if "node_modules" in datei.parts or "library" in datei.parts:
            continue
        if "external" in datei.parts or "templates" in datei.name:
            continue
        try:
            text = datei.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for roh in _HEX.findall(text):
            farbe = roh.lower()
            if farbe in erlaubt:
                continue
            treffer[farbe].append(str(datei.relative_to(WURZEL)))

    if not treffer:
        return []

    befunde: list[Befund] = []
    marken = set(MARKENKERN)

    # 0 — Markenfarben, die im Quelltext stehen, aber in keiner Vorgabe.
    #     Der auffaelligste Fall im ersten Lauf: #004F59 und #FAE600, die
    #     Hausfarben, standen 19- und 14-mal im Quelltext und in der
    #     Tailwind-Vorgabe gar nicht. Wer die Palette liest, sieht die Marke
    #     nicht — und wer den Quelltext liest, haelt sie fuer Handarbeit.
    for farbe in sorted(marken & set(treffer)):
        stellen = treffer[farbe]
        befunde.append(Befund(
            kennung=f"markenfarbe-ohne-vorgabe/#{farbe}",
            ebene="optik",
            titel=f"Markenfarbe #{farbe} wird {len(stellen)}-mal benutzt, steht aber in keiner Farbvorgabe",
            beleg=" · ".join(sorted(set(stellen))[:4]),
            einzelheiten=(
                "Die Farbe gehoert zur Marke, aber `tailwind.config.js` kennt sie "
                "nicht. Damit ist sie im Werkzeug Handarbeit statt Vorgabe: Sie "
                "laesst sich nicht zentral aendern, nicht pruefen und nicht "
                "wiederverwenden — und der naechste Bildschirm bekommt einen Ton "
                "daneben."
            ),
            vorschlag="P2",
            gegenstand=f"#{farbe}",
        ))

    # 1 — die Beinahe-Treffer, einzeln
    beinahe = []
    for farbe, stellen in treffer.items():
        if farbe in marken or len(stellen) < beinahe_ab:
            continue
        naechste = min(marken, key=lambda m: _abstand(farbe, m), default=None)
        if naechste and _abstand(farbe, naechste) < naehe:
            beinahe.append((farbe, naechste, stellen))
    for farbe, naechste, stellen in sorted(beinahe, key=lambda t: -len(t[2])):
        befunde.append(Befund(
            kennung=f"farbe-beinahe/#{farbe}",
            ebene="optik",
            titel=f"#{farbe} liegt dicht neben der Vorgabe #{naechste} ({len(stellen)} Stellen)",
            beleg=" · ".join(sorted(set(stellen))[:4]),
            einzelheiten=(
                f"Abstand {_abstand(farbe, naechste):.0f} von 442 im RGB-Raum. Eine "
                "Farbe so dicht an der Marke ist im Bildschirmfoto nicht zu "
                "unterscheiden und faellt erst auf, wenn zwei Flaechen nebeneinander "
                "liegen. Entweder ist sie ein Tippfehler, oder die Vorgabe kennt "
                "einen Ton, den sie nicht fuehrt."
            ),
            vorschlag="P2",
            gegenstand=f"#{farbe}",
        ))

    # 2 — der Rest als eine Entscheidung
    aussortiert = {b[0] for b in beinahe} | (marken & set(treffer))
    rest = {f: st for f, st in treffer.items() if f not in aussortiert}
    haeufig = sorted(rest.items(), key=lambda p: -len(p[1]))
    haeufig = [(f, st) for f, st in haeufig if len(st) >= mindestens]
    if haeufig:
        stellen_gesamt = sum(len(st) for st in rest.values())
        oben = ", ".join(f"#{f} ({len(st)}×)" for f, st in haeufig[:10])
        befunde.append(Befund(
            kennung="farbsystem/zweites-system",
            ebene="optik",
            titel=(f"{len(rest)} Farben ausserhalb der Vorgabe an {stellen_gesamt} Stellen "
                   f"— ein zweites, ungeschriebenes Farbsystem"),
            beleg=f"{len(haeufig)} davon an mindestens {mindestens} Stellen; haeufigste: {oben}",
            einzelheiten=(
                "Es sind ueberwiegend Tailwind-Grundfarben, die direkt als Hexwert "
                "im Quelltext stehen. Sie halten kein Umfaerben aus: Wer die Palette "
                "aendert, aendert sie hier nicht mit — und wer die Marke prueft, "
                "misst eine Oberflaeche, die ihr nur teilweise folgt. Zu entscheiden "
                "ist einmal, nicht sechzigmal: Entweder die Statusfarben (Rot, Gruen, "
                "Violett fuer Zustaende) kommen als benannte Werte in die Vorgabe, "
                "oder sie verschwinden aus dem Quelltext."
            ),
            vorschlag="P2",
            gegenstand="Farben ausserhalb der Vorgabe",
        ))
    return befunde


# ── L-25: Dateien ueber der Grenze ──────────────────────────────────────────

def zu_grosse_dateien(grenze: int = 800) -> list[Befund]:
    """Dateien ueber der vereinbarten Zeilengrenze — nur die neuen Ausreisser."""
    befunde = []
    kandidaten = _py_dateien(BACKEND) + _js_dateien()
    for datei in kandidaten:
        if "tests" in datei.parts:
            continue
        try:
            zeilen = len(datei.read_text(encoding="utf-8").splitlines())
        except UnicodeDecodeError:
            continue
        if zeilen <= grenze * 2:      # nur die deutlichen Faelle, sonst Rauschen
            continue
        befunde.append(Befund(
            kennung=f"dateigroesse/{datei.relative_to(WURZEL)}",
            ebene="konsistenz",
            titel=f"{datei.relative_to(WURZEL)} hat {zeilen} Zeilen (Grenze {grenze})",
            beleg=f"wc -l {datei.relative_to(WURZEL)} → {zeilen}",
            einzelheiten=(
                "Ueber der doppelten Grenze gemeldet, damit die Liste nicht von "
                "Grenzfaellen lebt. Gezaehlt wird mit derselben Methode wie in "
                "`tools/grosse-dateien.py` (L-25) — Zeilen, nicht Zeichen."
            ),
            vorschlag="P3",
            gegenstand=str(datei.relative_to(WURZEL)),
        ))
    return sorted(befunde, key=lambda b: b.titel)


ALLE_STUFEN = (
    ("Doppelte Routen", doppelte_routen),
    ("Namensdrift Umgebung", namensdrift_umgebung),
    ("Umgebung ohne Blueprint", umgebung_ohne_blueprint),
    ("Felder ohne Leser", felder_ohne_leser),
    ("Seiten ohne Weg", seiten_ohne_route),
    ("Farben ausserhalb der Vorgabe", farben_ausserhalb),
    ("Dateien ueber der Grenze", zu_grosse_dateien),
)
