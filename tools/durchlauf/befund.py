# -*- coding: utf-8 -*-
"""Was ein Befund ist — und was ihn davon abhaelt, zweimal aufzutauchen.

**Warum es diese Datei gibt.** Ein Durchlauf, der jede Woche dieselben
achtzig Zeilen vorlegt, wird nach dem zweiten Mal nicht mehr gelesen. Der
Wert eines wiederkehrenden Laufs steht und faellt damit, dass er **nur das
Neue** zeigt. Dafuer braucht jeder Befund drei Dinge:

* eine **Kennung**, die ueber Laeufe hinweg dieselbe bleibt (nicht die
  laufende Nummer, sondern das, worueber geredet wird — Routenpfad,
  Dateiname, Feldname);
* einen **Beleg**, der die Behauptung pruefbar macht: Datei und Zeile oder
  eine Messung. Ohne Beleg wird der Befund verworfen, nicht abgeschwaecht;
* eine **Herkunft** — welche Stufe ihn erhoben hat.

**Zwei Filter stehen zwischen Erhebung und Bericht.** Der erste vergleicht
mit der Lueckenliste: Wer einen Befund vorlegt, der als L-Nummer schon offen
steht, verlaengert die Liste, ohne Wissen hinzuzufuegen. Der zweite ist das
Quittungsjournal: Was David einmal als „kein Befund" abgeraeumt hat, kommt
nicht wieder — mit dem Grund, den er genannt hat, damit spaeter nachlesbar
ist, warum die Zeile fehlt.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import re

WURZEL = pathlib.Path(__file__).resolve().parents[2]
LUECKENLISTE = WURZEL / "docs" / "soll-ist-analyse.md"
JOURNAL = WURZEL / "docs" / "durchlauf" / "quittiert.json"

def kurz(pfad: pathlib.Path) -> str:
    """Der Pfad relativ zur Repo-Wurzel — oder ganz, wenn er ausserhalb liegt.

    `relative_to` wirft, sobald eine Datei ausserhalb des Repos liegt; die
    Selbstprobe arbeitet aber mit Beispieldateien in einem Zwischenordner.
    Ein Werkzeug, das an seiner eigenen Probe scheitert, kann nicht sagen, ob
    es blind ist.
    """
    try:
        return str(pfad.relative_to(WURZEL))
    except ValueError:
        return str(pfad)


#: Die vier Ebenen des Verbindungs-Checks plus die zwei Querschnitte.
EBENEN = ("datenbank", "schnittstelle", "frontend", "browser", "optik", "konsistenz")


@dataclasses.dataclass
class Befund:
    """Ein einzelner Fund. `kennung` ist der Schluessel ueber Laeufe hinweg."""

    kennung: str
    ebene: str
    titel: str
    beleg: str
    einzelheiten: str = ""
    vorschlag: str = "P3"        # P0 … P3, Vorschlag — David entscheidet
    gegenstand: str = ""         # der Pfad/Name, mit dem gegen die Liste geglichen wird

    def __post_init__(self) -> None:
        if self.ebene not in EBENEN:
            raise ValueError(f"unbekannte Ebene: {self.ebene}")
        if not self.beleg.strip():
            raise ValueError(f"Befund ohne Beleg: {self.kennung}")
        if not self.gegenstand:
            self.gegenstand = self.kennung.split("/")[-1]

    def als_dict(self) -> dict:
        return dataclasses.asdict(self)


# ── Filter 1: steht es schon in der Lueckenliste? ────────────────────────────

def _luecken() -> list[tuple[str, str, bool]]:
    """Alle Lueckeneintraege — (ID, Text, erledigt).

    **Auch die erledigten.** Wer nur gegen die offenen abgleicht, meldet
    einen Rueckfall als neuen Befund und verliert damit die einzige
    Information, die ihn gefaehrlich macht: dass er schon einmal behoben
    war. Erledigt heisst hier: ID **oder** Titel durchgestrichen.
    """
    if not LUECKENLISTE.exists():
        return []
    eintraege = []
    for zeile in LUECKENLISTE.read_text(encoding="utf-8").splitlines():
        treffer = re.match(r"\|\s*(~~)?\s*(L-\d+)\s*(~~)?\s*\|(.*)", zeile)
        if not treffer:
            continue
        id_, rest = treffer.group(2), treffer.group(4)
        erledigt = bool(treffer.group(1)) or rest.lstrip().startswith("~~")
        eintraege.append((id_, rest, erledigt))
    return eintraege


def schon_gefuehrt(befund: Befund, luecken: list[tuple[str, str, bool]]) -> tuple[str, bool] | None:
    """Gibt die L-Nummer zurueck, unter der dieser Gegenstand schon steht.

    Verglichen wird der **Gegenstand** — ein Routenpfad, ein Dateiname, ein
    Feldname —, nicht der Titel. Titel formuliert jeder anders; der
    Gegenstand ist derselbe Text in beiden Welten.
    """
    nadel = befund.gegenstand.strip()
    if len(nadel) < 6:          # zu kurz, um eindeutig zu treffen
        return None
    for id_, text, erledigt in luecken:
        if nadel in text:
            return id_, erledigt
    return None


# ── Filter 2: hat David das schon abgeraeumt? ────────────────────────────────

def journal_lesen() -> dict:
    if not JOURNAL.exists():
        return {}
    return json.loads(JOURNAL.read_text(encoding="utf-8"))


def journal_schreiben(daten: dict) -> None:
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        json.dumps(daten, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sieben(befunde: list[Befund]) -> tuple[list[dict], list[dict], list[dict]]:
    """Teilt in **neu**, **schon gefuehrt** und **quittiert**.

    Drei Listen statt einer, weil die zwei aussortierten Gruppen selbst eine
    Aussage sind: Eine Kennzahl, die nur die neuen zaehlt, verschweigt, wie
    viel der Lauf ueberhaupt gesehen hat.
    """
    luecken = _luecken()
    journal = journal_lesen()
    neu, gefuehrt, quittiert = [], [], []
    for b in befunde:
        eintrag = b.als_dict()
        if b.kennung in journal:
            eintrag["grund"] = journal[b.kennung].get("grund", "")
            quittiert.append(eintrag)
            continue
        treffer = schon_gefuehrt(b, luecken)
        if treffer:
            nummer, erledigt = treffer
            eintrag["luecke"] = nummer
            eintrag["rueckfall"] = erledigt
            if erledigt:
                # Ein Rueckfall ist **neu**, nicht gefuehrt: Die Zeile in der
                # Liste sagt, das Thema sei erledigt — die Messung sagt nein.
                neu.append(eintrag)
            else:
                gefuehrt.append(eintrag)
            continue
        neu.append(eintrag)
    return neu, gefuehrt, quittiert
