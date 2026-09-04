# -*- coding: utf-8 -*-
"""Stufen, die das Drumherum pruefen: Abhaengigkeiten, Tore, Termine.

Drei Fragen, die nichts mit dem Fachlichen zu tun haben und trotzdem
Produktivausfaelle erzeugt haben:

    import_ohne_eintrag()  → L-57: der Dienst laesst sich nicht mehr bauen
    pruefto_mit_luecke()   → L-78: das Tor prueft weniger, als es verspricht
    termine_fremder_dienste() → L-81: eine angekuendigte Abschaltung laeuft ab
    bedienelement_ohne_wirkung() → L-79: ein Knopf, der nichts tut
"""
from __future__ import annotations

import ast
import datetime
import json
import pathlib
import re
import sys

from .befund import Befund, WURZEL, kurz

BACKEND = WURZEL / "kompagnon" / "backend"
FRONTEND = WURZEL / "kompagnon" / "frontend" / "src"
TERMINE = WURZEL / "docs" / "durchlauf" / "termine.json"


# ── L-57: der Dienst laesst sich nicht mehr bauen ───────────────────────────

def _eingetragene_pakete() -> set[str]:
    namen = set()
    for name in ("requirements.txt", "requirements.in", "requirements-dev.txt"):
        datei = BACKEND / name
        if not datei.exists():
            continue
        for zeile in datei.read_text(encoding="utf-8").splitlines():
            zeile = zeile.split("#")[0].strip()
            if not zeile:
                continue
            paket = re.split(r"[=<>!\[ ]", zeile)[0].strip().lower()
            if paket:
                namen.add(paket.replace("-", "_"))
    return namen


def _deckt_ab(modul: str, pakete: set[str]) -> bool:
    """Deckt ein eingetragenes Paket diesen Modulnamen ab?

    Modul- und Paketname fallen oft auseinander, und eine Liste von Hand
    gepflegter Paare ist genau so lange vollstaendig, bis jemand ein Paket
    hinzufuegt. Der erste Lauf meldete `dns`, `psycopg2` und `whois` als
    fehlend — alle drei standen als `dnspython`, `psycopg2-binary` und
    `python-whois` in der Datei. Ein Teilstringvergleich in beide Richtungen
    faengt diese Familie ohne Pflegeaufwand; er ist grosszuegig, und das ist
    hier richtig: Ein uebersehener Eintrag kostet einen Neuaufbau, ein
    Fehlalarm kostet eine Minute.
    """
    return any(modul in paket or paket in modul for paket in pakete if len(paket) > 3)


def import_ohne_eintrag() -> tuple[list[Befund], str]:
    """Fremdmodule, die der Code importiert und keine Anforderungsdatei nennt.

    **Der Fall, der dahintersteht.** Am 19.08.2026 endete der Buildbefehl des
    Produktivdienstes auf `playwright install chromium`, waehrend `playwright`
    in **keiner** `requirements.txt` stand (L-57). Der Dienst lief weiter — er
    war ja schon gebaut. Erst der naechste Neuaufbau scheiterte, und zwar
    genau dann, wenn man ihn am dringendsten braucht: beim Umzug.

    Die Zuordnung Modulname → Paketname ist nicht immer gleich (`PIL` kommt
    aus `pillow`); bekannte Paare stehen in `_ALIAS`. Ein unbekanntes Paar
    erzeugt hoechstens einen Fehlalarm, den ein Eintrag in
    `docs/durchlauf/quittiert.json` fuer immer erledigt.
    """
    _ALIAS = {
        "pil": "pillow", "yaml": "pyyaml", "dotenv": "python_dotenv",
        "jose": "python_jose", "multipart": "python_multipart",
        "dateutil": "python_dateutil", "bs4": "beautifulsoup4",
        "sklearn": "scikit_learn", "cv2": "opencv_python",
        "stripe": "stripe", "fitz": "pymupdf", "pyotp": "pyotp",
        "apscheduler": "apscheduler", "sqlalchemy": "sqlalchemy",
    }
    eingetragen = _eingetragene_pakete()
    if not eingetragen:
        return [], "keine Anforderungsdatei gefunden — nicht gemessen"
    standard = set(sys.stdlib_module_names)
    eigen = {p.stem for p in BACKEND.glob("*.py")} | {
        p.name for p in BACKEND.iterdir() if p.is_dir()}

    gefunden: dict[str, list[str]] = {}
    geprueft = 0
    for datei in BACKEND.rglob("*.py"):
        if ("venv" in datei.parts or "__pycache__" in datei.parts
                or "tests" in datei.parts or "tools" in datei.parts):
            continue
        try:
            baum = ast.parse(datei.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        geprueft += 1
        for knoten in ast.walk(baum):
            namen = []
            if isinstance(knoten, ast.Import):
                namen = [a.name.split(".")[0] for a in knoten.names]
            elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0 and knoten.module:
                namen = [knoten.module.split(".")[0]]
            for name in namen:
                schluessel = name.lower().replace("-", "_")
                if (schluessel in standard or name in eigen
                        or schluessel in eingetragen
                        or _ALIAS.get(schluessel, "") in eingetragen
                        or _deckt_ab(schluessel, eingetragen)):
                    continue
                gefunden.setdefault(name, []).append(
                    f"{kurz(datei)}:{knoten.lineno}")

    befunde = []
    for name, stellen in sorted(gefunden.items()):
        befunde.append(Befund(
            kennung=f"import-ohne-eintrag/{name}",
            ebene="konsistenz",
            titel=f"`{name}` wird importiert, steht in keiner Anforderungsdatei",
            beleg=" · ".join(sorted(set(stellen))[:4]),
            einzelheiten=(
                "`requirements.txt` sagt in ihrem eigenen Kopf, sie enthalte „die "
                "vollstaendig aufgeloesten Versionen **inklusive aller transitiven "
                "Pakete**\". Ein importiertes Modul, das dort fehlt, widerspricht dem "
                "— und die Datei gibt es genau deshalb, weil zwei Deploys desselben "
                "Commits sonst unterschiedliche Software ergeben. "
                "Der laufende Dienst hat das Paket — er wurde damit gebaut. Der "
                "**naechste** Neuaufbau hat es nicht. Genau so ist L-57 entstanden: "
                "Der Buildbefehl rief `playwright` auf, das in keiner Anforderungsdatei "
                "stand; aufgefallen ist es erst beim Umzug, als ein neuer Dienst nach "
                "28 Sekunden scheiterte."
            ),
            vorschlag="P1",
            gegenstand=name,
        ))
    return befunde, f"{geprueft} Backend-Dateien gelesen, {len(eingetragen)} Pakete eingetragen"


# ── L-78: das Tor prueft weniger, als es verspricht ─────────────────────────

def pruefto_mit_luecke() -> list[Befund]:
    """Regelauswahl in der CI-Zeile statt in der Konfigdatei.

    **Warum das kein Schoenheitsfehler ist.** Steht die Auswahl im
    Arbeitsablauf, prueft `ruff check` lokal etwas anderes als das Tor. Wer
    lokal gruen ist, faellt in der CI durch — oder schlimmer: umgekehrt.
    L-78 hat das behoben; diese Stufe ist der Waechter, der den Rueckfall
    meldet.
    """
    ablauf = WURZEL / ".github" / "workflows" / "ci.yml"
    if not ablauf.exists():
        return []
    text = ablauf.read_text(encoding="utf-8")
    befunde = []
    for zeile_nr, zeile in enumerate(text.splitlines(), 1):
        if "ruff" not in zeile or zeile.strip().startswith("#"):
            continue
        if "--select" in zeile or "--ignore" in zeile or "--extend-select" in zeile:
            befunde.append(Befund(
                kennung="pruefto-luecke/ruff-auswahl-in-ci",
                ebene="konsistenz",
                titel="Die ruff-Regelauswahl steht im Arbeitsablauf statt in der Konfigdatei",
                beleg=f".github/workflows/ci.yml:{zeile_nr} — {zeile.strip()[:90]}",
                einzelheiten=(
                    "Damit prueft `ruff check` lokal etwas anderes als das Tor. Die "
                    "Auswahl gehoert nach `kompagnon/backend/ruff.toml`, damit beide "
                    "dieselbe Regel lesen — so wurde L-78 geschlossen."
                ),
                vorschlag="P2",
                gegenstand="ruff-Auswahl in ci.yml",
            ))
    konfig = BACKEND / "ruff.toml"
    if not konfig.exists() and "ruff" in text:
        befunde.append(Befund(
            kennung="pruefto-luecke/ruff-ohne-konfig",
            ebene="konsistenz",
            titel="Die CI ruft ruff auf, aber `kompagnon/backend/ruff.toml` fehlt",
            beleg="kompagnon/backend/ruff.toml nicht vorhanden; .github/workflows/ci.yml nennt ruff",
            einzelheiten=(
                "Ohne Konfigdatei prueft ruff seine Vorgabeauswahl — und niemand "
                "kann nachlesen, welche Regeln das Tor durchsetzt."
            ),
            vorschlag="P2",
            gegenstand="ruff.toml",
        ))
    return befunde


# ── L-81: angekuendigte Abschaltungen ───────────────────────────────────────

def termine_fremder_dienste() -> tuple[list[Befund], str]:
    """Termine, die ein fremder Dienst gesetzt hat — Abschaltungen, Fristen.

    **Warum als eigene Datei und nicht im Code.** Ein Termin ist kein
    Quelltext; er steht in einer Herstellerankuendigung. `termine.json` ist
    die Liste, und diese Stufe ist der Wecker: Sie meldet, was in den
    naechsten `vorlauf` Tagen faellig wird oder schon abgelaufen ist. So
    entsteht der vierte Zustand *terminiert* nicht als Zettel, den niemand
    wiederfindet.
    """
    if not TERMINE.exists():
        return [], "docs/durchlauf/termine.json fehlt — keine Termine gefuehrt"
    try:
        eintraege = json.loads(TERMINE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as fehler:
        return ([Befund(
            kennung="termine/unlesbar", ebene="konsistenz",
            titel="`docs/durchlauf/termine.json` ist nicht lesbar",
            beleg=f"JSONDecodeError: {fehler}",
            einzelheiten="Solange die Datei unlesbar ist, ueberwacht niemand die Termine.",
            vorschlag="P1", gegenstand="termine.json")], "unlesbar")

    heute = datetime.date.today()
    befunde = []
    for eintrag in eintraege:
        try:
            faellig = datetime.date.fromisoformat(eintrag["datum"])
        except (KeyError, ValueError):
            continue
        tage = (faellig - heute).days
        vorlauf = int(eintrag.get("vorlauf_tage", 45))
        if tage > vorlauf:
            continue
        abgelaufen = tage < 0
        befunde.append(Befund(
            kennung=f"termin/{eintrag.get('kennung', eintrag['datum'])}",
            ebene="konsistenz",
            titel=(f"{'ABGELAUFEN' if abgelaufen else f'in {tage} Tagen'}: "
                   f"{eintrag.get('was', 'Termin')}"),
            beleg=f"{eintrag['datum']} — {eintrag.get('quelle', 'docs/durchlauf/termine.json')}",
            einzelheiten=eintrag.get("folge", "")
                        or "Keine Folge notiert — das gehoert in den Eintrag.",
            vorschlag="P0" if abgelaufen else "P1",
            gegenstand=eintrag.get("kennung", eintrag["datum"]),
        ))
    return befunde, f"{len(eintraege)} Termine gefuehrt, {len(befunde)} faellig oder abgelaufen"


# ── L-79: ein Knopf, der nichts tut ─────────────────────────────────────────

_KNOPF = re.compile(r"<button\b")


def _ohne_js_kommentare(text: str) -> str:
    """Kommentarzeilen leeren, Zeilenzahl erhalten.

    In `AlertBanner.jsx` steht drei Zeilen ueber dem Knopf der Satz „Eine
    echte `<button>` statt `role=\"button\"`" — der erste Lauf meldete diesen
    Kommentar als Schaltflaeche ohne Handler. Ersetzt wird deshalb der Inhalt,
    nicht die Zeile: Sonst stimmen die Zeilennummern im Beleg nicht mehr, und
    ein Beleg, der auf die falsche Zeile zeigt, ist schlimmer als keiner.
    """
    zeilen = []
    im_block = False
    for zeile in text.splitlines():
        gestutzt = zeile.strip()
        if im_block:
            zeilen.append("")
            if "*/" in zeile:
                im_block = False
            continue
        if gestutzt.startswith("/*"):
            im_block = "*/" not in zeile
            zeilen.append("")
            continue
        if gestutzt.startswith("//") or gestutzt.startswith("*"):
            zeilen.append("")
            continue
        zeilen.append(zeile)
    return "\n".join(zeilen)


def _tag_ende(text: str, start: int) -> int:
    """Das Ende eines JSX-Tags, ohne an `=>` zu zerbrechen.

    `[^>]*>` findet bei `onClick={() => f()}` das `>` des Pfeils und schneidet
    das Tag mitten im Handler ab — der erste Lauf meldete darauf fuenfzehn
    Knoepfe „ohne Handler", von denen der erste einen hatte. Gezaehlt werden
    deshalb geschweifte Klammern; das Tag endet beim ersten `>` auf Tiefe null.
    """
    tiefe = 0
    for i in range(start, len(text)):
        z = text[i]
        if z == "{":
            tiefe += 1
        elif z == "}":
            tiefe -= 1
        elif z == ">" and tiefe == 0:
            return i + 1
    return len(text)


def bedienelement_ohne_wirkung() -> tuple[list[Befund], str]:
    """Schaltflaechen ohne Handler und ohne Formularrolle.

    **Was die Stufe sicher sagen kann und was nicht.** Ein `<button>` ohne
    `onClick`, ohne `type="submit"` und ohne `form=` kann im Browser nichts
    ausloesen — das ist kein Verdacht, sondern eine Eigenschaft des Markups.
    Was sie **nicht** sieht: einen Handler, der zwar da ist, aber nichts tut,
    und einen Knopf, der seine Wirkung ueber einen uebergebenen Wert bekommt.
    Deshalb wird nur die eindeutige Form gemeldet — L-79 war genau diese.
    """
    dateien = [p for p in FRONTEND.rglob("*.jsx") if "node_modules" not in p.parts]
    treffer: list[tuple[str, int, str]] = []
    for datei in dateien:
        try:
            text = _ohne_js_kommentare(datei.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
        for fund in _KNOPF.finditer(text):
            marke = text[fund.start():_tag_ende(text, fund.start())]
            if ("onClick" in marke or "onSubmit" in marke
                    or 'type="submit"' in marke or "type={" in marke
                    or "form=" in marke or "{..." in marke):
                continue
            zeile = text.count("\n", 0, fund.start()) + 1
            treffer.append((kurz(datei), zeile, marke[:70]))

    # **Je Datei, nicht je Knopf.** Vierzehn Zeilen fuer acht Dateien ist eine
    # Tapete; und quittieren laesst sich nur, was eine Kennung hat, die den
    # naechsten Lauf ueberlebt. Eine Zeilennummer tut das nicht — ein Dateiname
    # schon. Wer einmal einträgt „BrandDesignWerkstatt ist eine Markenvorschau",
    # ist die Meldung dauerhaft los.
    je_datei: dict[str, list[int]] = {}
    for datei, zeile, _ in treffer:
        je_datei.setdefault(datei, []).append(zeile)

    befunde = []
    for datei, zeilen in sorted(je_datei.items()):
        befunde.append(Befund(
            kennung=f"knopf-ohne-wirkung/{datei}",
            ebene="frontend",
            titel=(f"{pathlib.Path(datei).name}: {len(zeilen)} Schaltflaeche(n) ohne "
                   f"Handler und ohne Formularrolle"),
            beleg=f"{datei} — Zeile {', '.join(str(z) for z in zeilen[:8])}",
            einzelheiten=(
                "Ein `<button>` ohne `onClick`, ohne `type=\"submit\"` und ohne "
                "`form=` kann nichts ausloesen. Das ist keine Vermutung, sondern eine "
                "Eigenschaft des Markups — der Knopf sieht aus wie ein Angebot und ist "
                "keines. L-79 war genau das. **Zwei Ausnahmen sind haeufig und "
                "berechtigt:** ein Knopf in einer Vorschau, die zeigt, wie etwas "
                "aussehen wuerde, und einer, der nur als Anzeige dient. Beide gehoeren "
                "mit ihrem Grund ins Quittungsjournal — dann meldet der naechste Lauf "
                "die Datei nicht mehr, und die Zahl bedeutet wieder etwas."
            ),
            vorschlag="P2",
            gegenstand=datei,
        ))
    return befunde, f"{len(dateien)} JSX-Dateien gelesen"
