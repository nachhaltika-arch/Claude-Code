# -*- coding: utf-8 -*-
"""Was ein Bestandskunde dazubuchen kann (Entwurf `kundenkonto-neu`).

**Zwei Angebote, und beide sind gepruefte Produkte:** der Wechsel auf Pflege
Pro und das GEO/GAIO-Add-on.

**Check PLUS und Workbook stehen bewusst nicht dabei.** Beide brauchen einen
Bestellweg, den es nicht gibt (L-100), und das Workbook ist nicht geschrieben.
Etwas anzubieten, das man nicht liefern kann, ist teurer als es nicht
anzubieten — der Kunde klickt einmal, bekommt nichts, und glaubt dem Rest der
Seite danach auch nicht mehr.

**GEO-01 steht hier, obwohl das Datenblatt vom 23.08. es sperrt.** Der Hinweis
dort ist ueberholt: L-99 ist seit dem 04.09.2026 geschlossen — die Auslieferung
von `llms.txt` und `schema.org` steht, und `services/geo_auslieferung.py`
prueft nach der Veroeffentlichung am lebenden Dienst nach. Das Datenblatt
gehoert nachgezogen; eine Sperre, die widerlegt ist, kostet dieselbe
Glaubwuerdigkeit wie eine fehlende.

**Die Preise kommen aus der Abrechnung, nicht von Hand.** Zwei Fassungen
desselben Preises laufen auseinander, und die eine steht dann auf dem
Bildschirm, die andere auf der Rechnung.
"""
from dataclasses import dataclass

from services import abo_stunden

#: Der GEO-Preis. **Nicht in `products`**, weil GEO-01 dort keinen Eintrag
#: hat — die Zahl stammt aus dem Produktdatenblatt `docs/produkte/abo-und-geo.md`
#: (Teil C, „1.200 € netto einmalig ⚠️ Annahme"). Die Markierung betrifft die
#: **Hoehe**, nicht die Waehrung oder die Steuer; sie steht hier, damit
#: niemand die Zahl fuer bestaetigt haelt.
GEO_NETTO_CENT = 120000
STEUERSATZ = abo_stunden.STEUERSATZ_ABO


def _brutto(netto_cent: int) -> int:
    return netto_cent + int(round(netto_cent * STEUERSATZ / 100))


@dataclass(frozen=True)
class Angebot:
    """Ein buchbares Produkt, wie es auf dem Bildschirm steht.

    **Vier Angaben sind Pflicht**, und keine davon ist Zierrat: Ein Preis ohne
    Zahlungsbedingung laesst offen, wann abgebucht wird; eine Laufzeit ohne
    Rechtstext laesst offen, worauf man sich einlaesst.
    """

    kennung: str
    titel: str
    nummer: str            # was auf der Rechnung steht
    netto_cent: int
    brutto_cent: int
    einmalig: bool
    dazu: str              # ein Satz: was es ist
    punkte: tuple          # was drin ist
    zahlung: str
    laufzeit: str
    rechtstext: str        # wozu er zustimmt — wird bei der Buchung mitgeschrieben
    danach: str            # was nach dem Klick geschieht


ANGEBOTE = {
    "ABO-PRO": Angebot(
        kennung="ABO-PRO",
        titel="Auf Pflege Pro wechseln",
        nummer="ABO-PRO · Pflege-Abonnement",
        netto_cent=abo_stunden.preis_netto_cent("ABO-PRO"),
        brutto_cent=abo_stunden.preis_brutto_cent("ABO-PRO"),
        einmalig=False,
        dazu=("Pflege Pro enthält alles aus Pflege Basic und zusätzlich "
              "fünf Positionen."),
        punkte=(
            "Inhaltsänderungen bis 90 Minuten je Monat statt 30",
            "Monatlicher Leistungsbericht",
            "Re-Audit quartalsweise statt jährlich",
            "Reaktionszeit bei Störungen 4 Stunden an Werktagen statt 1 Werktag",
            "Eine neue Unterseite pro Jahr enthalten",
        ),
        zahlung=("Monatlich im Voraus per SEPA-Lastschrift, Abrechnung zum "
                 "Monatsersten."),
        laufzeit="12 Monate, danach monatlich kündbar mit einem Monat Frist.",
        rechtstext=("Mit dem Buchen erklären Sie verbindlich den Wechsel auf "
                    "Pflege Pro. Der Wechsel gilt ab dem kommenden "
                    "Monatsersten; die Differenz zu Pflege Basic wird nicht "
                    "rückwirkend berechnet. Nicht verbrauchte Änderungsminuten "
                    "verfallen zum Monatsende und werden nicht übertragen."),
        danach=("Wir stellen Ihren Vertrag und die Abbuchung um und "
                "bestätigen Ihnen den Wechsel. Ab dem Monatsersten gelten "
                "die neun Positionen von Pflege Pro."),
    ),
    "GEO-01": Angebot(
        kennung="GEO-01",
        titel="GEO/GAIO Add-on",
        nummer="GEO-01 · einmalige Leistung",
        netto_cent=GEO_NETTO_CENT,
        brutto_cent=_brutto(GEO_NETTO_CENT),
        einmalig=True,
        dazu=("Ihre Seite wird so aufbereitet, dass KI-Assistenten sie lesen "
              "und zitieren können."),
        punkte=(
            "llms.txt und strukturierte Auszeichnung nach schema.org",
            "Ground Page mit den Kernaussagen Ihres Betriebs",
            "Nachschau nach der Veröffentlichung, ob es angekommen ist",
            "Vergleich 60 Tage später",
        ),
        zahlung=("50 % bei Auftragserteilung, 50 % bei Abnahme. Zahlungsziel "
                 "je 14 Tage netto."),
        laufzeit="Lieferzeit 10 Werktage ab Auftragserteilung.",
        # **Der Satz, der hier am wichtigsten ist.** Wir liefern die
        # technische Voraussetzung; ob ein Assistent den Betrieb nennt,
        # entscheidet dessen Anbieter. Eine Zusicherung waere unhaltbar.
        rechtstext=("Wir stellen sicher, dass die technischen Voraussetzungen "
                    "erfüllt sind. Ob und wie ein KI-Assistent Sie nennt, "
                    "entscheidet dessen Anbieter — eine Nennung können wir "
                    "nicht zusichern. Nicht enthalten sind eine "
                    "Platzierungsgarantie bei Suchmaschinen und laufende "
                    "Optimierung."),
        danach=("Ihr Betreuer meldet sich mit dem Auftrag und der ersten "
                "Rechnung über 50 %. Die Lieferzeit läuft ab Ihrer "
                "Auftragserteilung."),
    ),
}


def buchbar_fuer(laufendes_abo: str, schon_gebucht) -> list:
    """Welche Angebote diesem Kunden noch offenstehen — mit Grund, wo nicht.

    **Kein stilles Weglassen.** Ein Angebot, das nicht erscheint, wirft die
    Frage auf, ob es das noch gibt; eines mit Grund daneben beantwortet sie.
    """
    gebucht = set(schon_gebucht or ())
    abo = (laufendes_abo or "").strip().upper()
    heraus = []
    for a in ANGEBOTE.values():
        grund = ""
        if a.kennung in gebucht:
            grund = "Bereits gebucht — wir setzen es um und melden uns."
        elif a.kennung == "ABO-PRO" and abo == "ABO-PRO":
            grund = "Sie haben Pflege Pro bereits."
        elif a.kennung == "ABO-PRO" and not abo:
            grund = ("Der Wechsel setzt ein laufendes Pflege-Abo voraus. "
                     "Sprechen Sie uns an — wir richten es ein.")
        heraus.append((a, not grund, grund))
    return heraus
