# -*- coding: utf-8 -*-
"""Markdown des Manuskripts → Satzelemente.

**Warum ein eigener Leser und kein Markdown-nach-HTML-nach-PDF.** Das
Manuskript benutzt drei eigene Formen, die kein Markdown kennt:

    ::: MRG      Marginalie — gehört neben den Satzspiegel, nicht hinein
    ::: ABB 3.1  Abbildungsauftrag an den Gestalter, im Buch ein Platzhalter
    [[UMBRUCH]]  ein gesetzter Seitenumbruch aus dem Manuskript

Ein Umweg über HTML müsste sie vorher herausschneiden und hinterher wieder
einsetzen. Der Textkörper selbst ist bewusst schlicht: Überschriften, Absätze,
Aufzählungen, Tabellen, Zitate. Dafür genügt ein zeilenweiser Leser.
"""
import re

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, ListFlowable, ListItem, PageBreak,
                                Paragraph, Spacer, Table, TableStyle)

import satzspiegel as sp
from ankreuzen import Ankreuzzeile, enthaelt_kaestchen
from marginalie import Marginalie

BLOCK_AUF = re.compile(r"^:::\s*(MRG|ABB)\s*(.*)$")
BLOCK_ZU = re.compile(r"^:::\s*$")
UEBERSCHRIFT = re.compile(r"^(#{1,4})\s+(.*)$")
LISTE = re.compile(r"^\s*[-*]\s+(.*)$")
ZAHLLISTE = re.compile(r"^\s*(\d+)\.\s+(.*)$")
TABELLENZEILE = re.compile(r"^\s*\|.*\|\s*$")
TRENNZEILE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def auszeichnen(text: str) -> str:
    """Markdown-Auszeichnung in die Mini-Auszeichnung von ReportLab.

    Reihenfolge zählt: Erst die spitzen Klammern entschärfen, sonst frisst der
    Absatzsetzer ein `<` aus dem Fließtext als Befehl.
    """
    text = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r'<font name="Buch-Med">\1</font>', text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<link href="\2">\1</link>', text)
    return text


class Umsetzer:
    """Liest die Zeilen eines Buchteils und liefert Satzelemente."""

    def __init__(self, formate: dict, masse: dict, ziel: str,
                 kompakt: bool = False):
        self.f = formate
        self.m = masse
        self.ziel = ziel
        #: Formularsatz statt Fließtextsatz — für Anhang C (B6.2).
        self.kompakt = kompakt
        self.abbildungen = 0
        self.marginalien = 0

    # ── Einzelne Formen ──────────────────────────────────────────────
    def _absatz(self, text, stil="fliess"):
        # **Kästchen werden gezeichnet, nicht gesetzt.** Noto Sans kennt das
        # Zeichen nicht, und ReportLab verschluckt es stillschweigend (B6.2).
        if enthaelt_kaestchen(text):
            return Ankreuzzeile(re.sub(r"[*`]", "", text), self.f[stil])
        return Paragraph(auszeichnen(text), self.f[stil])

    def _spaltenbreiten(self, zeilen: list) -> list:
        """Breite nach Inhalt statt gleichmäßig verteilt.

        Gleiche Breiten zerlegten im ersten Entwurf Wörter mitten im Wort
        („Suchmaschinenbe rater"), weil eine Spalte mit zwei Zeichen genauso
        breit war wie eine mit vierzig. Gewichtet wird nach der längsten Zelle,
        gedeckelt, damit eine einzelne lange Zelle nicht alles an sich zieht.
        """
        laengen = []
        for zeile in zeilen:
            if TRENNZEILE.match(zeile):
                continue
            felder = [f.strip() for f in zeile.strip().strip("|").split("|")]
            for i, feld in enumerate(felder):
                text = re.sub(r"[*`\[\]]", "", feld)
                # **Ausfülllinien zählen nicht mit ihrer vollen Länge.** Eine
                # Zeile aus vierzig Unterstrichen ist Platz zum Schreiben, kein
                # Text, der passen muss — sonst zieht sie die Spaltenbreite an
                # sich, und die Beschriftung daneben bricht um („Branchenklass
                # / e"). Am Satz gesehen, nicht überlegt (B6.2).
                text = re.sub(r"_{3,}", "_" * 12, text)
                if i >= len(laengen):
                    laengen.append(0)
                laengen[i] = max(laengen[i], min(len(text), 60))
        if not laengen:
            return None
        summe = sum(laengen) or 1
        mindest = 0.08                      # keine Spalte unter 8 Prozent
        anteile = [max(mindest, laenge / summe) for laenge in laengen]
        gesamt = sum(anteile)
        return [self.m["haupt"] * anteil / gesamt for anteil in anteile]

    def _tabelle(self, zeilen):
        """Eine Markdown-Tabelle als gesetzte Tabelle.

        Die Spaltenbreiten werden gleichmäßig verteilt. Das ist grob, aber
        vorhersagbar — und im Zweifel besser als eine Automatik, die eine
        Spalte auf zwei Zeichen zusammenzieht.
        """
        reihen = []
        kopfstil = "formularkopf" if self.kompakt else "tabellenkopf"
        zellstil = "formular" if self.kompakt else "tabelle"
        for i, zeile in enumerate(zeilen):
            if TRENNZEILE.match(zeile):
                continue
            felder = [f.strip() for f in zeile.strip().strip("|").split("|")]
            stil = kopfstil if not reihen else zellstil
            reihen.append([
                Ankreuzzeile(re.sub(r"[*`]", "", feld), self.f[stil])
                if enthaelt_kaestchen(feld)
                else Paragraph(auszeichnen(feld), self.f[stil])
                for feld in felder])
        if not reihen:
            return None
        # `repeatRows=1`: Läuft eine Tabelle über den Seitenfuß, steht ihre
        # Kopfzeile auf der Folgeseite erneut. Ohne das beginnt die Fortsetzung
        # mit nackten Zellen, und der Leser muss zurückblättern, um zu wissen,
        # welche Spalte was bedeutet.
        tabelle = Table(reihen, colWidths=self._spaltenbreiten(zeilen),
                        hAlign="LEFT", repeatRows=1)
        tabelle.setStyle(TableStyle([
            # **Ohne diese Zeile liegt Helvetica im PDF.** ReportLab legt für
            # jede Tabelle seine Voreinstellung in die Seitenressourcen —
            # auch dann, wenn in allen Zellen Absätze mit eigener Schrift
            # stehen und kein Zeichen in Helvetica erscheint. Die Druckerei
            # sieht dann eine nicht eingebettete Schrift und schickt zurück.
            ("FONTNAME", (0, 0), (-1, -1), "Buch"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 1 if self.kompakt else 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1 if self.kompakt else 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, 0), .8, colors.black),
            ("LINEBELOW", (0, 1), (-1, -2), .25, sp.G30),
        ]))
        return tabelle

    def _marginalie(self, inhalt):
        self.marginalien += 1
        kopf = ""
        zeilen = []
        for zeile in inhalt:
            roh = zeile.strip()
            if not roh:
                continue
            if not kopf and roh.startswith("**") and roh.endswith("**"):
                kopf = roh.strip("*")
                continue
            zeilen.append(re.sub(r"\*\*(.+?)\*\*", r"\1", roh))
        if not self.m["marginalspalte"]:
            # Bildschirmfassung: eingerückter Kasten statt Randspalte.
            teile = [Paragraph(auszeichnen(kopf), self.f["marginalkopf"])] if kopf else []
            teile += [Paragraph(auszeichnen(z), self.f["marginal"]) for z in zeilen]
            return [Spacer(1, 4), KeepTogether(teile), Spacer(1, 6)]
        return [Marginalie(kopf, zeilen, self.m, self.f)]

    def _abbildung(self, nummer, inhalt):
        """Der Abbildungsauftrag wird im Satz zu einem maßhaltigen Platzhalter.

        Damit stimmt die Seitenzahl: Eine Abbildung, die im Buch eine halbe
        Seite einnimmt, darf beim Zählen nicht null Zeilen kosten.
        """
        self.abbildungen += 1
        angaben = {}
        for zeile in inhalt:
            if ":" in zeile and not zeile.startswith(" "):
                schluessel, wert = zeile.split(":", 1)
                angaben[schluessel.strip()] = wert.strip()
        # **Auf den Satzspiegel gedeckelt.** Ein Platzhalter, der höher ist als
        # der Satzspiegel, passt auf keine Seite — ReportLab bricht dann mit
        # „too large on page" ab, statt umzubrechen, weil ein Kasten mit fester
        # Zeilenhöhe sich nicht teilen lässt. Der Deckel lässt Luft für die
        # Bildunterschrift.
        gewuenscht = {"ganz": 150 * mm, "breit": 80 * mm}.get(
            angaben.get("format", "schmal"), 50 * mm)
        hoehe = min(gewuenscht, self.m["satz"] * .8)
        kasten = Table(
            [[Paragraph(f"<b>ABB {nummer}</b><br/>{angaben.get('titel', '')}",
                        self.f["abbildung"])]],
            colWidths=[self.m["haupt"]], rowHeights=[hoehe])
        kasten.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Buch"),
            ("BOX", (0, 0), (-1, -1), .5, sp.G30),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, 0), (-1, -1), sp.G15),
        ]))
        return [Spacer(1, 6), kasten, Spacer(1, 8)]

    # ── Der Durchlauf ────────────────────────────────────────────────
    def teil(self, kapitel: dict) -> list:
        aus = []
        zeilen = kapitel["text"].splitlines()
        i = 0
        tabelle, liste = [], []

        def liste_abschliessen():
            if liste:
                # **`bulletFontName` ist Pflicht, nicht Kosmetik.** ReportLab
                # setzt Aufzählungszeichen sonst in Helvetica — einer Schrift,
                # die nicht im PDF liegt. `druckpruefung.py` meldet das als
                # „nicht eingebettet: Helvetica"; in der Druckerei wäre es ein
                # Rückläufer. Genau der Fehler, vor dem BUCH-03 warnt.
                aus.append(ListFlowable(
                    [ListItem(Paragraph(auszeichnen(t), self.f["liste"]),
                              leftIndent=12) for t in liste],
                    bulletType="bullet", bulletFontName="Buch",
                    bulletFontSize=6, leftIndent=12, bulletOffsetY=-1))
                liste.clear()

        def tabelle_abschliessen():
            if tabelle:
                gesetzt = self._tabelle(tabelle)
                if gesetzt is not None:
                    vor, nach = (2, 3) if self.kompakt else (4, 6)
                    aus.extend([Spacer(1, vor), gesetzt, Spacer(1, nach)])
                tabelle.clear()

        while i < len(zeilen):
            zeile = zeilen[i]
            roh = zeile.strip()

            auf = BLOCK_AUF.match(roh)
            if auf:
                liste_abschliessen(), tabelle_abschliessen()
                art, rest = auf.group(1), auf.group(2).strip()
                inhalt = []
                i += 1
                while i < len(zeilen) and not BLOCK_ZU.match(zeilen[i].strip()):
                    inhalt.append(zeilen[i])
                    i += 1
                aus.extend(self._marginalie(inhalt) if art == "MRG"
                           else self._abbildung(rest, inhalt))
                i += 1
                continue

            if roh == "[[UMBRUCH]]":
                liste_abschliessen(), tabelle_abschliessen()
                aus.append(PageBreak())
                i += 1
                continue

            if TABELLENZEILE.match(zeile):
                liste_abschliessen()
                tabelle.append(zeile)
                i += 1
                continue
            tabelle_abschliessen()

            treffer = UEBERSCHRIFT.match(roh)
            if treffer:
                liste_abschliessen()
                tiefe, text = len(treffer.group(1)), treffer.group(2)
                if tiefe == 1:
                    stil = "kapitelziffer" if re.fullmatch(r"\d+", text) \
                        else "kapiteltitel"
                    aus.append(self._absatz(text, stil))
                elif self.kompakt:
                    # Im Formular sind Zwischenüberschriften Beschriftungen,
                    # keine Kapitelmarken — sie bekommen weniger Luft.
                    aus.append(self._absatz(text, "formularabschnitt"))
                else:
                    aus.append(self._absatz(
                        text, "abschnitt" if tiefe == 2 else "unterabschnitt"))
                i += 1
                continue

            eintrag = LISTE.match(zeile) or ZAHLLISTE.match(zeile)
            if eintrag:
                liste.append(eintrag.groups()[-1])
                i += 1
                continue
            liste_abschliessen()

            if roh.startswith(">"):
                aus.append(self._absatz(roh.lstrip("> ").strip(), "zitat"))
                i += 1
                continue

            if roh.startswith("---") and set(roh) <= {"-"}:
                aus.append(Spacer(1, self.m["raster"]))
                i += 1
                continue

            if roh:
                aus.append(self._absatz(roh))
            i += 1

        liste_abschliessen()
        tabelle_abschliessen()
        return aus
