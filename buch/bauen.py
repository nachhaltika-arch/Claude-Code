#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut das Buch aus dem Manuskript — Bildschirm- und Druckfassung.

    buch/venv/bin/python buch/bauen.py --ziel beide

**Der Build läuft nicht im Dienst.** Zweihundert Seiten zu setzen dauert
Sekunden bis Minuten und hielte einen Worker fest; bei drei gleichzeitigen
Bestellungen stünde das Backend. Gebaut wird hier, ausgeliefert wird eine
fertige Datei (`BUCH-03`, `BUCH-06`).

**Alle Kapitel tragen `status: entwurf`.** Ohne `--entwurf` bricht der Build
deshalb ab — sonst entstünde unbemerkt ein Verkaufs-PDF aus unfertigem Text.
"""
import argparse
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER / "layout"))

from reportlab.platypus import (BaseDocTemplate, Frame, NextPageTemplate,  # noqa: E402
                                PageBreak, PageTemplate)

from reportlab import rl_config  # noqa: E402

import manuskript  # noqa: E402
import satzspiegel as sp  # noqa: E402
import stile  # noqa: E402
from reportlab.platypus import Flowable  # noqa: E402

from inhalt import Umsetzer  # noqa: E402

AUSGABE = HIER / "build"


class Kapitelmarke(Flowable):
    """Nimmt keinen Platz ein und merkt sich, auf welcher Seite sie steht.

    Damit weiß der zweite Durchgang, welche Kapitel auf einer linken Seite
    angefangen haben — und wo eine Vakatseite fehlt.
    """

    def __init__(self, nummer: int, titel: str):
        super().__init__()
        self.nummer = nummer
        self.titel = titel
        self.seite = None
        self.width = self.height = 0

    def wrap(self, *_):
        return (0, 0)

    def draw(self):
        self.seite = self.canv.getPageNumber()


# **Kein Kunstgriff für die Vakatseite.** Der erste Entwurf hatte dafür einen
# Flowable, dessen `wrap` eine Höhe größer als die Seite meldete — der übliche
# Trick, um einen Umbruch zu erzwingen. Er bricht ReportLab: Was auf keine
# leere Seite passt, lässt sich auch nicht auf die nächste schieben, und der
# Satz endete mit „too large on page 9" an einer völlig unbeteiligten
# Abbildung — zwei Bauteile weiter, als der Fehler saß. Die Leerseite ist
# jetzt schlicht ein zweiter `PageBreak`.


class Buch(BaseDocTemplate):
    """Zwei Seitenvorlagen — die Ränder spiegeln sich am Bund.

    Ohne Spiegelung säße der Text auf linken Seiten zu weit außen und
    verschwände auf rechten im Bund. Bei 190 mm Satzhöhe fällt das sofort auf.
    """

    def __init__(self, pfad, masse, formate, titel):
        breite, hoehe = masse["seite"]
        super().__init__(str(pfad), pagesize=(breite, hoehe),
                         title=titel, author="Manuel Potter",
                         subject="Der Homepage Standard",
                         leftMargin=0, rightMargin=0,
                         topMargin=0, bottomMargin=0)
        self.masse = masse
        self.formate = formate
        self.buchtitel = titel
        self.kolumne = ""

        y = masse["fuss"]
        hoch = masse["satz"]
        rechts = Frame(masse["innen"], y, masse["haupt"], hoch,
                       leftPadding=0, rightPadding=0, topPadding=0,
                       bottomPadding=0, id="rechts")
        links_x = breite - masse["innen"] - masse["haupt"]
        links = Frame(links_x, y, masse["haupt"], hoch,
                      leftPadding=0, rightPadding=0, topPadding=0,
                      bottomPadding=0, id="links")
        # **Der Takt.** Rechte Seiten tragen ungerade Nummern. Ohne die
        # Zyklusliste blieb im ersten Entwurf die zuletzt gesetzte Vorlage bis
        # zum nächsten Kapitel stehen — der Satzspiegel sprang dann seitenweise
        # nach außen und die Marginalien liefen aus dem Papier.
        self.addPageTemplates([
            PageTemplate(id="rechts", frames=[rechts], onPage=self._seite),
            PageTemplate(id="links", frames=[links], onPage=self._seite),
        ])
        self.kapitelmarken = []

    def _seite(self, canvas, dok):
        """Kolumnentitel und Seitenzahl — außen, ab der ersten Kapitelseite."""
        nummer = canvas.getPageNumber()
        if nummer <= self.titelei_seiten or nummer in self.oeffnerseiten:
            return
        breite, _ = self.masse["seite"]
        stil = self.formate["kolumne"]
        canvas.setFont(stil.fontName, stil.fontSize)
        canvas.setFillColor(stil.textColor)
        y_kopf = self.masse["seite"][1] - self.masse["kopf"] + 14
        y_fuss = self.masse["fuss"] - 16

        if nummer % 2 == 1:                       # rechte Seite
            x_innen = self.masse["innen"]
            canvas.drawString(x_innen, y_kopf, self.kolumne[:60])
            canvas.drawRightString(breite - self.masse["aussen"], y_fuss, str(nummer))
        else:                                     # linke Seite
            x = breite - self.masse["innen"] - self.masse["haupt"]
            canvas.drawString(x, y_kopf, self.buchtitel)
            canvas.drawString(self.masse["aussen"], y_fuss, str(nummer))

    titelei_seiten = 0
    #: Kapitelanfänge tragen weder Kolumnentitel noch Seitenzahl — die Zäsur
    #: soll nicht durch eine Zeile Kleingedrucktes verwässert werden.
    oeffnerseiten = frozenset()

    def afterFlowable(self, flowable):
        """Der Kolumnentitel folgt dem Kapitel, in dem die Seite steht."""
        if getattr(flowable, "style", None) is not None and \
                flowable.style.name == "kapiteltitel":
            self.kolumne = flowable.getPlainText()


def bauen(ziel: str, entwurf: bool) -> dict:
    sp.schriften_laden()
    # **Die Grundschrift der Seite, nicht nur die des Absatzes.** ReportLab
    # trägt auf jeder Seite eine Anfangsschrift in die Ressourcen ein, auch
    # wenn kein sichtbares Zeichen sie benutzt — voreingestellt Helvetica.
    # Die liegt nicht im PDF, und `druckpruefung.py` meldete sie zu Recht auf
    # allen 279 Seiten als „nicht eingebettet". Ein Rückläufer aus der
    # Druckerei wegen einer Schrift, die nirgends zu sehen ist.
    rl_config.canvas_basefontname = "Buch"
    masse = sp.masse(ziel)
    formate = stile.formate(ziel)
    teile = manuskript.alles()

    entwuerfe = [t["datei"] for t in teile if t["status"] == "entwurf"]
    if entwuerfe and not entwurf:
        raise SystemExit(
            f"{len(entwuerfe)} Bestandteile tragen `status: entwurf` — "
            "der Build würde ein Verkaufs-PDF aus unfertigem Text machen.\n"
            "Mit `--entwurf` ausdrücklich zulassen.\n  "
            + "\n  ".join(entwuerfe[:5]) + ("\n  …" if len(entwuerfe) > 5 else ""))

    AUSGABE.mkdir(exist_ok=True)
    datei = AUSGABE / f"homepage-standard-{ziel}.pdf"

    # **Zwei Durchgänge, weil die Frage zirkulär ist.** Ob vor einem Kapitel
    # eine Vakatseite fehlt, hängt davon ab, wo das vorige endet — und das
    # verschiebt sich, sobald man eine einfügt. Der erste Durchgang misst, der
    # zweite setzt; danach wird geprüft, ob sich noch etwas bewegt hat.
    umsetzer = Umsetzer(formate, masse, ziel)
    # Anhang C sind Formulare; sie werden kompakt gesetzt, damit die
    # Vorlagen 1 und 2 ihre Zusage „eine Seite" halten (B6.2).
    formularsatz = Umsetzer(formate, masse, ziel, kompakt=True)
    oeffner = []

    def geschichte(vakat: set):
        """Die Erzählung als Flowable-Folge — mit Leerseite vor `vakat`."""
        marken, elemente = [], []
        if masse["marginalspalte"]:
            # **Der Takt der Seitenvorlagen.** Ohne diese Zeile bleibt es bei
            # der ersten Vorlage: Der Satzspiegel säße auf allen Seiten gleich,
            # die Ränder spiegelten nicht, und der Kolumnentitel stünde auf
            # linken Seiten neben dem Text statt darüber — genau so sah der
            # erste Probesatz aus. Seite 1 ist rechts, also folgt links.
            elemente.append(NextPageTemplate(["links", "rechts"]))
        for nr, teil in enumerate(teile):
            if nr:
                elemente.append(PageBreak())
                if nr in vakat:
                    elemente.append(PageBreak())
            marke = Kapitelmarke(nr, teil["titel"])
            marken.append(marke)
            elemente.append(marke)
            if teil["teil"]:
                elemente.append(umsetzer._absatz(teil["teil"], "teil"))
            setzer = formularsatz if teil["datei"].startswith("ANHANG-C") else umsetzer
            elemente.extend(setzer.teil(teil))
        return marken, elemente

    def leerseiten_bestimmen(marken: list) -> set:
        """Vor welchen Kapiteln eine Vakatseite fehlt — gerechnet, nicht probiert.

        **Warum nicht iterativ.** Der erste Entwurf baute, sammelte die
        Kapitel, die links begannen, fügte dort Leerseiten ein und baute neu.
        Das pendelt: Jede eingefügte Leerseite dreht die Seitenlage **aller**
        folgenden Kapitel um, also werden aus acht falschen dreizehn andere
        falsche. Nach vier Durchgängen begannen immer noch acht Kapitel links.

        Es ist aber gar keine Suche nötig. Eine ganze Leerseite verschiebt den
        nachfolgenden Satz um genau eine Seite, ohne den Umbruch im Text zu
        verändern. Damit gilt für jedes Kapitel: neue Seite = gemessene Seite
        plus Zahl der davor eingefügten Leerseiten. Das lässt sich in einem
        Durchlauf durchrechnen.
        """
        leerseiten, verschiebung = set(), 0
        for i, marke in enumerate(marken):
            if not marke.seite:
                continue
            seite = marke.seite + verschiebung
            if i and seite % 2 == 0:      # gerade Seite = linke Seite
                leerseiten.add(i)
                verschiebung += 1
        return leerseiten

    # Erster Durchgang misst, zweiter setzt. Ein dritter prüft nur noch nach.
    dok, vakat, marken = None, set(), []
    for durchgang in range(3):
        umsetzer.abbildungen = umsetzer.marginalien = 0
        marken, elemente = geschichte(vakat)
        dok = Buch(datei, masse, formate, "Der Homepage Standard")
        dok.oeffnerseiten = frozenset(oeffner)
        dok.build(elemente)
        oeffner = [m.seite for m in marken if m.seite]
        if not masse["marginalspalte"]:
            break
        gebraucht = leerseiten_bestimmen(marken)
        if not gebraucht:
            break
        vakat |= gebraucht

    groesse = datei.stat().st_size
    schief = [m.titel for m in marken if m.seite and m.seite % 2 == 0]
    return {"datei": datei, "seiten": dok.page, "bytes": groesse,
            "teile": len(teile), "abbildungen": umsetzer.abbildungen,
            "marginalien": umsetzer.marginalien, "durchgaenge": durchgang + 1,
            "linksbeginnend": schief}


def main() -> int:
    p = argparse.ArgumentParser(description="Buch setzen")
    p.add_argument("--ziel",
                   choices=("bildschirm", "druck", "druck-a4", "beide"),
                   default="beide")
    p.add_argument("--entwurf", action="store_true",
                   help="Bestandteile mit `status: entwurf` mitsetzen")
    args = p.parse_args()

    ziele = ("bildschirm", "druck") if args.ziel == "beide" else (args.ziel,)
    for ziel in ziele:
        e = bauen(ziel, args.entwurf)
        print(f"{e['datei'].name}: {e['seiten']} Seiten · "
              f"{e['bytes'] / 1024 / 1024:.1f} MB · {e['teile']} Bestandteile · "
              f"{e['abbildungen']} Abbildungen · {e['marginalien']} Marginalien · "
              f"{e['durchgaenge']} Durchgänge")
        # **Am Satzspiegel gefragt, nicht am Namen des Ziels.** Die Warnung
        # gilt für jede gebundene Fassung; als `ziel == "druck"` geschrieben
        # hätte sie bei `druck-a4` stillschweigend geschwiegen.
        if e["linksbeginnend"] and sp.masse(ziel)["marginalspalte"]:
            print(f"  ⚠ {len(e['linksbeginnend'])} Kapitel beginnen links: "
                  + ", ".join(e["linksbeginnend"][:4]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
