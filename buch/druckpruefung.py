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
* **Seitenformat 170 × 240 mm.** Ein PDF im falschen Format wird skaliert —
  damit stimmt kein Satzspiegel mehr.
* **Mindestumfang 48 Seiten**, sonst trägt der Rücken keine Beschriftung.
"""
import sys
from pathlib import Path

from pypdf import PdfReader

MM = 72 / 25.4
SOLL_BREIT, SOLL_HOCH = 170 * MM, 240 * MM
TOLERANZ = 1.0          # Punkt
MINDESTSEITEN = 48


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
    passt = (abs(breit - SOLL_BREIT) < TOLERANZ and abs(hoch - SOLL_HOCH) < TOLERANZ)
    befunde.append((
        passt,
        f"Seitenformat {breit / MM:.0f} × {hoch / MM:.0f} mm",
        f"Seitenformat {breit / MM:.1f} × {hoch / MM:.1f} mm statt 170 × 240"))

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
