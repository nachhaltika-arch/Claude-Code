# -*- coding: utf-8 -*-
"""Ankreuzkästchen zeichnen, statt sie zu setzen (B6.2).

**Der Befund vom 25.08.2026.** Das Manuskript benutzt 89-mal das Zeichen `☐`
— in den fünf Vorlagen, im Selbsttest und in den Merklisten. **Noto Sans
enthält es nicht**, und zwar in keiner Form: weder `☐` (U+2610) noch `□`,
`▢`, `◻`, `■` oder `☑`. ReportLab verschluckt ein fehlendes Zeichen
**stillschweigend** und lässt seine Breite stehen. Im PDF blieb an jeder
Stelle eine Lücke.

Das trifft genau die Teile, die zum Ausfüllen gedacht sind — und die laut
`B1.11` „Voraussetzung, nicht Zugabe" sind. Ein Ergebnisblatt ohne Kästchen
ist kein Formular.

**Warum gezeichnet und nicht eine zweite Schrift.** `satzmuster.py` macht es
seit jeher so: Die Stufenmarken des Buchs sind gezeichnete Rechtecke. Eine
Symbolschrift nachzuladen hieße, eine zweite Lizenz zu prüfen (`B6.4`) und
eine zweite Datei in den Satz zu nehmen — für ein Quadrat.
"""
from reportlab.lib.colors import black
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Flowable

#: Die Zeichen, die als Kästchen gemeint sind. Alle fehlen in Noto Sans.
KAESTCHEN = "☐□▢◻"


def enthaelt_kaestchen(text: str) -> bool:
    return any(z in (text or "") for z in KAESTCHEN)


class Ankreuzzeile(Flowable):
    """Eine Textzeile, deren Kästchen gezeichnet statt gesetzt werden."""

    def __init__(self, text: str, stil, seitenrand: float = 0):
        super().__init__()
        self.roh = text or ""
        self.stil = stil
        self.seitenrand = seitenrand
        self._zeilen = []
        self.width = 0
        self.height = 0

    # ── Umbruch ──────────────────────────────────────────────────────
    def _kastengroesse(self) -> float:
        """Etwas kleiner als die Versalhöhe — ein Kästchen soll nicht schreien."""
        return self.stil.fontSize * 0.78

    def _breite(self, stueck: str) -> float:
        if stueck in KAESTCHEN:
            return self._kastengroesse() + self.stil.fontSize * 0.3
        return pdfmetrics.stringWidth(stueck, self.stil.fontName, self.stil.fontSize)

    def wrap(self, verfuegbar_breite, verfuegbar_hoehe):
        stuecke = []
        for wort in self.roh.split():
            # Ein Kästchen klebt nie am folgenden Wort — es ist ein eigenes Stück.
            rest = wort
            while rest and rest[0] in KAESTCHEN:
                stuecke.append(rest[0])
                rest = rest[1:]
            if rest:
                stuecke.append(rest)

        self._zeilen, laufend, breite = [], [], 0.0
        leerzeichen = pdfmetrics.stringWidth(" ", self.stil.fontName,
                                             self.stil.fontSize)
        for stueck in stuecke:
            zusatz = self._breite(stueck) + (leerzeichen if laufend else 0)
            if laufend and breite + zusatz > verfuegbar_breite:
                self._zeilen.append(laufend)
                laufend, breite = [stueck], self._breite(stueck)
            else:
                laufend.append(stueck)
                breite += zusatz
        if laufend:
            self._zeilen.append(laufend)

        self.width = verfuegbar_breite
        self.height = max(len(self._zeilen), 1) * self.stil.leading
        return (self.width, self.height)

    # ── Zeichnen ─────────────────────────────────────────────────────
    def draw(self):
        c = self.canv
        c.setFont(self.stil.fontName, self.stil.fontSize)
        c.setFillColor(self.stil.textColor or black)
        kasten = self._kastengroesse()
        leerzeichen = pdfmetrics.stringWidth(" ", self.stil.fontName,
                                             self.stil.fontSize)

        y = self.height - self.stil.fontSize
        for zeile in self._zeilen:
            x = 0.0
            for stueck in zeile:
                if stueck in KAESTCHEN:
                    c.saveState()
                    c.setStrokeColor(self.stil.textColor or black)
                    c.setLineWidth(0.6)
                    # Auf der Grundlinie stehend, leicht angehoben.
                    c.rect(x, y + self.stil.fontSize * 0.06, kasten, kasten,
                           stroke=1, fill=0)
                    c.restoreState()
                    x += kasten + self.stil.fontSize * 0.3
                else:
                    c.drawString(x, y, stueck)
                    x += pdfmetrics.stringWidth(stueck, self.stil.fontName,
                                                self.stil.fontSize)
                x += leerzeichen
            y -= self.stil.leading
