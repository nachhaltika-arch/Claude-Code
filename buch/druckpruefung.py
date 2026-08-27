#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prüft die Druckfassung gegen die Anforderungen der Druckerei.

    buch/venv/bin/python buch/druckpruefung.py buch/build/homepage-standard-druck.pdf

Vier Punkte, jeder mit einem Grund:

* **Seitenzahl durch vier teilbar.** Ein Bogen trägt vier Seiten; geht die Zahl
  nicht auf, füllt die Druckerei mit Leerseiten auf — an einer Stelle, die
  niemand gewählt hat.
* **Schriften eingebettet.** Der häufigste Fehler dieser Baustrecke: Das
  Werkzeug findet eine Schriftdatei nicht, setzt still eine Systemschrift ein,
  und das Ergebnis sieht erst in der Druckerei falsch aus.
* **Ein bekanntes Buchformat, und auf allen Seiten dasselbe.** Ein PDF im
  falschen Format wird skaliert — damit stimmt kein Satzspiegel mehr. Und ein
  einzelnes abweichendes Blatt mitten im Block fällt sonst erst der Druckerei
  auf.
* **Mindestumfang 48 Seiten**, sonst trägt der Rücken keine Beschriftung.
"""
import sys
from pathlib import Path

from pypdf import PdfReader

MM = 72 / 25.4
TOLERANZ = 1.0          # Punkt
MINDESTSEITEN = 48

#: Welche Buchformate die Baustrecke baut — `buch/layout/satzspiegel.py`.
#
# **Warum eine Liste und nicht ein Sollwert.** Bis zum 25.08.2026 stand hier
# `SOLL_BREIT, SOLL_HOCH = 170 × 240` fest. Sobald `bauen.py --ziel druck-a4`
# dazukam, meldete die Prüfung an einer einwandfreien A4-Fassung „Seitenformat
# 210 × 297 statt 170 × 240" — ein Fehler, den die Datei nicht hatte. Geprüft
# wird deshalb: Ist es *eines* der gebauten Formate, und ist es auf *jeder*
# Seite dasselbe.
FORMATE = {
    "170 × 240 mm": (170 * MM, 240 * MM),
    "A4 (210 × 297 mm)": (210 * MM, 297 * MM),
}


def _format_erkennen(breit: float, hoch: float):
    """Der Name des Formats, oder None, wenn es keines der gebauten ist."""
    for name, (soll_b, soll_h) in FORMATE.items():
        if abs(breit - soll_b) < TOLERANZ and abs(hoch - soll_h) < TOLERANZ:
            return name
    return None


def pruefen(pfad: Path) -> list:
    leser = PdfReader(str(pfad))
    seiten = len(leser.pages)
    befunde = []

    befunde.append((
        seiten % 4 == 0,
        f"Seitenzahl {seiten} ist durch 4 teilbar",
        f"Seitenzahl {seiten} ist nicht durch 4 teilbar — es fehlen "
        f"{(4 - seiten % 4) % 4} Seiten bis zum vollen Bogen"))

    befunde.append((
        seiten >= MINDESTSEITEN,
        f"Umfang {seiten} Seiten erreicht den Mindestumfang",
        f"Umfang {seiten} Seiten liegt unter {MINDESTSEITEN}"))

    kasten = leser.pages[0].mediabox
    breit, hoch = float(kasten.width), float(kasten.height)
    erkannt = _format_erkennen(breit, hoch)
    # Jede Seite, nicht nur die erste: Eine einzeln eingefügte Titelei oder
    # eine von Hand ergänzte Vorlage im falschen Maß bleibt sonst unsichtbar.
    abweichler = [nr for nr, seite in enumerate(leser.pages, 1)
                  if _format_erkennen(float(seite.mediabox.width),
                                      float(seite.mediabox.height)) != erkannt]
    if erkannt is None:
        befunde.append((
            False, "",
            f"Seitenformat {breit / MM:.1f} × {hoch / MM:.1f} mm ist keines der "
            f"gebauten Formate ({', '.join(FORMATE)})"))
    else:
        befunde.append((
            not abweichler,
            f"Seitenformat {erkannt} auf allen {seiten} Seiten",
            f"{len(abweichler)} Seiten weichen von {erkannt} ab, zuerst "
            f"Seite {abweichler[0] if abweichler else '?'}"))

    eingebettet, lose = set(), set()
    for seite in leser.pages:
        schriften = (seite.get("/Resources") or {}).get("/Font") or {}
        for verweis in schriften.values():
            objekt = verweis.get_object()
            name = str(objekt.get("/BaseFont", "?")).lstrip("/")
            nachfahre = (objekt.get("/DescendantFonts") or [None])[0]
            beschreibung = (nachfahre.get_object().get("/FontDescriptor")
                            if nachfahre else objekt.get("/FontDescriptor"))
            beschreibung = beschreibung.get_object() if beschreibung else {}
            hat_datei = any(k in beschreibung for k in
                            ("/FontFile", "/FontFile2", "/FontFile3"))
            (eingebettet if hat_datei else lose).add(name)
    befunde.append((
        not lose,
        f"{len(eingebettet)} Schriften eingebettet",
        f"nicht eingebettet: {', '.join(sorted(lose))}"))

    return befunde


def main() -> int:
    if len(sys.argv) < 2:
        print("Aufruf: druckpruefung.py <pfad zum druck-pdf>", file=sys.stderr)
        return 2
    pfad = Path(sys.argv[1])
    if not pfad.exists():
        print(f"Nicht gefunden: {pfad}", file=sys.stderr)
        return 2

    fehler = 0
    for erfuellt, gut, schlecht in pruefen(pfad):
        print(("  OK      " if erfuellt else "  FEHLER  ") + (gut if erfuellt else schlecht))
        fehler += 0 if erfuellt else 1
    print(f"\n{pfad.name}: {'alles in Ordnung' if not fehler else f'{fehler} Punkt(e) offen'}")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
