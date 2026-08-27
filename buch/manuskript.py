# -*- coding: utf-8 -*-
"""Welche Dateien das Buch ausmachen — und in welcher Reihenfolge.

**Gelesen wird aus `docs/Buch/…/Vollständige dokumentation Buch V2/`, nicht aus
einer Kopie unter `buch/manuskript/`.** `BUCH-03` sah eine solche Kopie vor;
sie wäre die dritte Fassung desselben Textes gewesen. Am 25.08.2026 ist die
zweite gelöscht worden, nachdem sie mit der ersten auseinandergelaufen war und
das Exportskript seinen erzeugten Anhang in die falsche geschrieben hatte. Eine
Baustrecke, die kopiert, baut irgendwann etwas anderes als das, was jemand
schreibt.

**Die Reihenfolge steht hier und nicht im Dateinamen.** Alphabetisch stünden
die Anhänge vor Kapitel 1. Ein Buch ist keine Dateiliste.
"""
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
QUELLE = (WURZEL / "docs" / "Buch" / "Buch - Kompagnon - Homepage Standard v2"
          / "Vollständige dokumentation Buch V2")

#: Titelei, siebzehn Kapitel, vier Anhänge — die Leseordnung des Buchs.
REIHENFOLGE = (
    ["TITELEI.md"]
    + [f"KAPITEL-{n:02d}-" for n in range(1, 18)]
    + ["ANHANG-A-", "ANHANG-B-", "ANHANG-C-", "ANHANG-D-"]
)

#: Was im Buch nichts zu suchen hat: die redaktionellen Anmerkungen am Ende
#: jeder Kapiteldatei. Sie sind Arbeitsmaterial für Autor, Recht und Satz —
#: eine Tabelle mit Zuständigkeiten und „🔴 offen" gehört nicht ins Buch.
#:
#: Das Manuskript markiert sie selbst, und zwar so eindeutig, dass man nicht
#: raten muss: `<!-- REDAKTIONELLE ANMERKUNGEN — NICHT DRUCKEN -->`. Ein
#: erster Entwurf suchte stattdessen nach Überschriften und schnitt dadurch in
#: vier Dateien zu wenig und in einer zu viel weg.
ANMERKUNGEN = re.compile(r"<!--\s*REDAKTIONELLE ANMERKUNGEN.*?-->", re.I | re.S)

#: Marken, die der Satz braucht und die deshalb den Kommentarfilter überleben.
SEITENUMBRUCH = "<!-- SEITENUMBRUCH -->"
KAPITELOEFFNER = re.compile(r"<!--\s*KAPITELÖFFNER.*?-->", re.I | re.S)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def _teil(name: str) -> str:
    """Der Abschnittstitel, wie er im Kolumnentitel erscheint."""
    ohne = re.sub(r"^(KAPITEL-\d+-|ANHANG-[A-D]-)", "", name).removesuffix(".md")
    return ohne.replace("-", " ")


def dateien() -> list:
    """Die Manuskriptdateien in Leseordnung — fehlende werden gemeldet."""
    gefunden, fehlend = [], []
    vorhanden = sorted(QUELLE.glob("*.md"))
    for eintrag in REIHENFOLGE:
        treffer = [p for p in vorhanden if p.name.startswith(eintrag)]
        if not treffer:
            fehlend.append(eintrag)
            continue
        gefunden.extend(treffer)
    if fehlend:
        raise FileNotFoundError(
            "Diese Bestandteile des Buchs fehlen im Manuskriptordner: "
            + ", ".join(fehlend))
    return gefunden


def _kopfdaten(roh: str) -> dict:
    """Der YAML-Vorspann — bewusst mit eigenen Mitteln gelesen.

    Es sind sieben flache Felder je Datei; dafür eine Abhängigkeit auf PyYAML
    aufzunehmen, wäre die schwerere Lösung. Verschachteltes gibt es hier nicht.
    """
    treffer = FRONTMATTER.match(roh)
    if not treffer:
        return {}
    daten = {}
    for zeile in treffer.group(1).splitlines():
        if ":" not in zeile or zeile.startswith(" "):
            continue
        schluessel, wert = zeile.split(":", 1)
        daten[schluessel.strip()] = wert.strip().strip('"')
    return daten


def lesen(pfad: Path) -> dict:
    """Eine Datei als Buchteil: Kopfdaten, Text ohne Arbeitsmaterial."""
    roh = pfad.read_text(encoding="utf-8")
    kopfdaten = _kopfdaten(roh)
    text = FRONTMATTER.sub("", roh, count=1)

    # Die redaktionellen Anmerkungen und alles danach fallen weg.
    schnitt = ANMERKUNGEN.search(text)
    if schnitt:
        text = text[:schnitt.start()]

    # Der Kapitelöffner sagt dem Satz „rechte Seite" — das merken wir uns,
    # bevor die Kommentare fallen.
    oeffner = bool(KAPITELOEFFNER.search(text))

    # Der Seitenumbruch überlebt als Marke, alle anderen Kommentare nicht:
    # Erzeuger-Vermerke sind Werkstattzeichen, keine Buchinhalte.
    text = text.replace(SEITENUMBRUCH, "\n\n[[UMBRUCH]]\n\n")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)

    kopf = re.search(r"^#\s+(.+)$", text, re.M)
    nummer = kopfdaten.get("kapitel", "")
    return {
        "datei": pfad.name,
        "nummer": nummer,
        "teil": kopfdaten.get("teil", ""),
        "titel": kopfdaten.get("titel") or (kopf.group(1).strip() if kopf
                                            else _teil(pfad.name)),
        "kurz": _teil(pfad.name),
        "status": kopfdaten.get("status", ""),
        "zielumfang": kopfdaten.get("zielumfang", ""),
        "text": text,
        "oeffner_rechts": oeffner,
        "anhang": pfad.name.startswith("ANHANG"),
        "titelei": pfad.name == "TITELEI.md",
    }


def alles() -> list:
    return [lesen(p) for p in dateien()]
