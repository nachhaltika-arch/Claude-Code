# -*- coding: utf-8 -*-
"""Die Marginalspalte — Text, der neben dem Satzspiegel steht, nicht darin.

**Warum ein eigener Flowable und keine zweite Spalte.** Platypus füllt Rahmen
nacheinander: Ein zweiter Rahmen neben dem Hauptsatz bekäme den Text, der nach
dem ersten übrig ist, nicht den, der daneben gehört. Die Marginalie muss aber
**auf der Höhe ihrer Textstelle** stehen — sonst erklärt sie im Buch etwas, das
zwei Seiten weiter vorne steht.

Deshalb ein Flowable **ohne eigene Höhe**: Es nimmt im Hauptsatz keinen Platz
weg und zeichnet beim Setzen in die Randspalte, auf der Höhe, an der es im
Textfluss steht.

**Die Spalte liegt außen.** Auf einer rechten Seite rechts, auf einer linken
links — sonst stünde sie im Bund und wäre halb verschluckt.

**Bekannte Grenze:** Zwei Marginalien dicht hintereinander können sich
überlagern; das Skript zählt solche Fälle und meldet sie am Ende, statt sie zu
verstecken. Im Manuskript stehen 106 Marginalien auf rund zweihundert Seiten.
"""
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Flowable


class Marginalie(Flowable):
    """Kopf und Text am äußeren Rand, auf Höhe der Textstelle."""

    def __init__(self, kopf: str, zeilen: list, masse: dict, formate: dict):
        super().__init__()
        self.kopf = kopf
        self.zeilen = zeilen
        self.masse = masse
        self.formate = formate
        self.width = 0
        self.height = 0
        #: Wird von `bauen.py` gesetzt und dort ausgewertet.
        self.unterkante = None

    def wrap(self, verfuegbar_breite, verfuegbar_hoehe):
        return (0, 0)

    def _umbrechen(self, text, font, groesse, breite):
        aus, zeile = [], ""
        for wort in text.split():
            probe = (zeile + " " + wort).strip()
            if pdfmetrics.stringWidth(probe, font, groesse) <= breite:
                zeile = probe
            else:
                if zeile:
                    aus.append(zeile)
                zeile = wort
        if zeile:
            aus.append(zeile)
        return aus

    def draw(self):
        if not self.masse["marginalspalte"]:
            return
        breite = self.masse["marg"]
        # **Die Seite kommt aus dem Rahmen, nicht aus der Seitenzahl.** Der
        # erste Entwurf schloss von der Seitenzahl auf die Seitenlage — und
        # lag falsch, sobald die Seitenvorlagen nicht im erwarteten Takt
        # wechselten: Die Marginalie lief auf Seite 21 rechts aus dem Papier.
        # Der Rahmen weiß es genau; er trägt seine Kennung.
        rahmen = getattr(self, "_frame", None)
        rechte_seite = getattr(rahmen, "id", "rechts") == "rechts"
        x = (self.masse["haupt"] + self.masse["steg"] if rechte_seite
             else -(breite + self.masse["steg"]))

        kopfstil = self.formate["marginalkopf"]
        textstil = self.formate["marginal"]
        y = 0
        if self.kopf:
            self.canv.setFont(kopfstil.fontName, kopfstil.fontSize)
            self.canv.setFillColor(kopfstil.textColor)
            for zeile in self._umbrechen(self.kopf, kopfstil.fontName,
                                         kopfstil.fontSize, breite):
                self.canv.drawString(x, y, zeile)
                y -= kopfstil.leading
            y -= 2

        self.canv.setFont(textstil.fontName, textstil.fontSize)
        self.canv.setFillColor(textstil.textColor)
        for absatz in self.zeilen:
            for zeile in self._umbrechen(absatz, textstil.fontName,
                                         textstil.fontSize, breite):
                self.canv.drawString(x, y, zeile)
                y -= textstil.leading
            y -= 3
        self.unterkante = y
