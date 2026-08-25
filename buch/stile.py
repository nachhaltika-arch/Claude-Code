# -*- coding: utf-8 -*-
"""Absatzformate des Buchs — aus dem Satzspiegel abgeleitet, nicht geraten.

Jede Größe hängt am Grundlinienraster (13 pt im Druck). Wer eine Schriftgröße
ändert, ohne den Zeilenabstand mitzuziehen, verliert das Raster — und mit ihm
die Ausrichtung von Marginalien und Tabellen.
"""
import sys
from pathlib import Path

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle

sys.path.insert(0, str(Path(__file__).resolve().parent / "layout"))
import satzspiegel as sp  # noqa: E402


def formate(ziel: str) -> dict:
    """Alle Absatzformate für ein Ausgabeziel."""
    m = sp.masse(ziel)
    gr, raster = m["grundschrift"], m["raster"]

    def stil(name, **kw):
        grund = dict(name=name, fontName="Buch", fontSize=gr, leading=raster,
                     textColor=sp.SCHWARZ, alignment=TA_LEFT,
                     spaceBefore=0, spaceAfter=0)
        grund.update(kw)
        return ParagraphStyle(**grund)

    return {
        # ── Überschriften ────────────────────────────────────────────
        # Die Kapitelziffer steht groß und allein — der Öffner ist eine
        # Zäsur, keine Überschrift.
        "kapitelziffer": stil("kapitelziffer", fontName="Buch-Black",
                              fontSize=gr * 5.4, leading=gr * 5.6,
                              textColor=sp.G30, spaceAfter=raster),
        "kapiteltitel": stil("kapiteltitel", fontName="Buch-Black",
                             fontSize=gr * 2.2, leading=gr * 2.5,
                             textColor=sp.TEAL, spaceAfter=raster * 2),
        "teil": stil("teil", fontName="Buch-Med", fontSize=gr * .85,
                     leading=raster, textColor=sp.G60, spaceAfter=raster),
        "abschnitt": stil("abschnitt", fontName="Buch-Black",
                          fontSize=gr * 1.25, leading=raster * 1.5,
                          textColor=sp.TEAL, spaceBefore=raster * 1.5,
                          spaceAfter=raster * .5, keepWithNext=1),
        "unterabschnitt": stil("unterabschnitt", fontName="Buch-F",
                               fontSize=gr, leading=raster,
                               spaceBefore=raster, spaceAfter=raster * .25,
                               keepWithNext=1),
        # ── Fließtext ────────────────────────────────────────────────
        "fliess": stil("fliess", spaceAfter=raster * .5),
        "einzug": stil("einzug", leftIndent=10, spaceAfter=raster * .5),
        "zitat": stil("zitat", fontName="Buch-K", leftIndent=8,
                      textColor=sp.G80, spaceBefore=raster * .5,
                      spaceAfter=raster * .75, borderPadding=0),
        "liste": stil("liste", leftIndent=12, bulletIndent=2,
                      spaceAfter=raster * .25),
        # ── Tabellen ─────────────────────────────────────────────────
        "tabellenkopf": stil("tabellenkopf", fontName="Buch-F",
                             fontSize=gr * .82, leading=gr * 1.05),
        "tabelle": stil("tabelle", fontSize=gr * .82, leading=gr * 1.05),
        # ── Marginalien und Abbildungen ──────────────────────────────
        "marginalkopf": stil("marginalkopf", fontName="Buch-F", fontSize=7.5,
                             leading=9.5),
        "marginal": stil("marginal", fontSize=7.5, leading=9.5,
                         textColor=sp.G80),
        "abbildung": stil("abbildung", fontName="Buch-Med", fontSize=gr * .85,
                          leading=raster, textColor=sp.G60),
        "kolumne": stil("kolumne", fontName="Buch", fontSize=7.5, leading=9,
                        textColor=sp.G60),
    }
