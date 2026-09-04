# -*- coding: utf-8 -*-
"""Der Mitwirkungskatalog als Daten (L-159).

**Warum als Daten und nicht als Fliesstext.** Die Punkte M1 bis M11 stehen seit
jeher im Angebotsbaukasten (`docs/Buch/Websprint Produkte/files/
KAS_00_Angebotsbaukasten.md` § A) — als Tabelle in einem Dokument. Damit
konnten sie in einem Angebot stehen und im Kundenkonto fehlen, und genau das
war der Fall: Der Kunde bekam eine Mahnung „Materialien fehlen", ohne zu
erfahren **welche**.

**Die Fristrelevanz ist der Kern, nicht die Liste.** Acht Punkte loesen den
**Fristbeginn** aus: Die Bauzeit laeuft erst, wenn alle vorliegen. Zwei
(Bauplan- und Textfreigabe) loesen eine **Fristpause** aus. Der
Blocker-Report zum Produktversprechen (L6) sagt dazu: „14 Tage" ohne
Definition, wann die Frist beginnt und wann sie pausiert, ist entweder
unverbindlich — dann ist es keine Garantie — oder ruinoes, dann zahlen wir
fuer die Langsamkeit des Kunden.

**Die Kundensprache steht hier, nicht in der Oberflaeche.** `titel` und
`warum` sind das, was der Betrieb liest; das Kuerzel M3 sagt ihm nichts. Wer
sie in der Komponente formulierte, haette zwei Fassungen — eine im Vertrag,
eine auf dem Bildschirm.

**Nicht jeder Punkt gilt fuer jeden Auftrag.** Der Relaunch braucht weniger als
der Neubau; M9 gilt nur bei Migration, M10 nur mit Karriereseite. Eine Liste,
die zehn Punkte zeigt und acht ausgraut, hat trotzdem zehn gezeigt — deshalb
entscheidet `fuer_produkt` mit, was ueberhaupt erscheint.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

#: Wirkung auf die Bauzeit.
FRISTBEGINN = "fristbeginn"
FRISTPAUSE = "fristpause"
OHNE_FRIST = "ohne"


@dataclass(frozen=True)
class Punkt:
    """Eine Mitwirkungsleistung, wie sie im Angebot steht und im Konto erscheint."""

    kennung: str
    titel: str                 # Kundensprache, nicht Vertragssprache
    warum: str                 # ein Satz: wozu wir das brauchen
    wirkung: str
    vertragstext: str          # der Wortlaut aus dem Angebotsbaukasten
    #: Leere Menge heisst: gilt fuer jedes Produkt.
    produkte: Tuple[str, ...] = ()
    #: Bedingt geltende Punkte — nur wenn das Projekt das Merkmal traegt.
    bedingung: Optional[str] = None


KATALOG: Tuple[Punkt, ...] = (
    Punkt("M1", "Ihre Internet-Adresse",
          "Wir brauchen einen Eintrag bei Ihrem Anbieter, damit die neue Seite "
          "unter Ihrer Adresse erscheint.",
          FRISTBEGINN,
          "Zugang zur Domain- bzw. DNS-Verwaltung (Zugangsdaten oder "
          "delegierter Zugriff)"),
    Punkt("M2", "Ihre Texte",
          "Sagen Sie uns je Seite, was damit passieren soll. Vorgeschlagen ist "
          "überall: wir schreiben, Sie geben frei.",
          FRISTBEGINN,
          "Vollständige Lieferung bzw. Freigabe der zu verwendenden Inhalte"),
    Punkt("M3", "Logo und Bilder",
          "Legen Sie ab, was Sie haben. Wir sagen Ihnen bei jeder Datei, ob sie reicht.",
          FRISTBEGINN,
          "Logo als Vektordatei (SVG/EPS/AI) sowie Bildmaterial mit mind. "
          "2.000 px Kantenlänge und geklärten Nutzungsrechten"),
    Punkt("M4", "Impressum und Datenschutz",
          "Wenn Ihre bisherige Seite beides hat, übernehmen wir es auf Knopfdruck.",
          FRISTBEGINN,
          "Rechtstexte (Impressum, Datenschutzerklärung, ggf. AGB) vom Kunden "
          "oder dessen Rechtsberatung"),
    Punkt("M5", "Wer entscheidet",
          "Eine Person, die Texte und Entwürfe freigeben darf.",
          FRISTBEGINN,
          "Benennung eines Ansprechpartners mit Entscheidungsbefugnis"),
    Punkt("M6", "Positionierungsgespräch",
          "90 Minuten, in denen wir klären, für wen die Seite sprechen soll.",
          FRISTBEGINN,
          "Teilnahme am Positionierungsgespräch (90 Min.)"),
    Punkt("M7", "Freigabe des Bauplans",
          "Wie viele Seiten, was worauf steht. Sie haben fünf Werktage.",
          FRISTPAUSE,
          "Freigabe des Bauplans innerhalb von 5 Werktagen nach Vorlage"),
    Punkt("M8", "Freigabe der Texte",
          "Wir schreiben, Sie lesen und geben frei. Sie haben fünf Werktage.",
          FRISTPAUSE,
          "Freigabe der Texte innerhalb von 5 Werktagen nach Vorlage"),
    Punkt("M9", "Zugang zu Ihrem bisherigen System",
          "Nur nötig, wenn wir Inhalte aus Ihrem alten Redaktionssystem holen.",
          FRISTBEGINN,
          "Zugang zum bestehenden CMS/Hosting, sofern Inhalte migriert werden",
          bedingung="migration"),
    Punkt("M10", "Karriereinhalte",
          "Stellenprofile, Vorteile für Bewerber und wer im Haus dafür zuständig ist.",
          FRISTBEGINN,
          "Lieferung der Karriereinhalte (Stellenprofile, Benefits, "
          "Ansprechpartner Personal)",
          bedingung="karriereseite"),
    Punkt("M11", "Rechnungsdaten",
          "Steuernummer und, falls Sie öffentlich sind, die Leitweg-ID.",
          OHNE_FRIST,
          "Benennung der Steuer-/Rechnungsdaten und ggf. Leitweg-ID"),
)

NACH_KENNUNG = {p.kennung: p for p in KATALOG}


def gilt_fuer(projektmerkmale) -> Tuple[Punkt, ...]:
    """Die Punkte, die fuer dieses Projekt ueberhaupt gelten.

    `projektmerkmale` ist eine Menge von Kennworten wie ``{"migration"}``. Ein
    Punkt ohne Bedingung gilt immer; ein bedingter nur, wenn sein Kennwort
    dabei ist.

    **Was hier nicht erscheint, existiert fuer diesen Kunden nicht** — es wird
    nicht ausgegraut. Eine Liste mit zehn Zeilen, von denen acht grau sind, ist
    eine Liste mit zehn Zeilen.
    """
    merkmale = set(projektmerkmale or ())
    return tuple(p for p in KATALOG
                 if p.bedingung is None or p.bedingung in merkmale)


def fristbeginn_offen(punkte, erledigt) -> Tuple[Punkt, ...]:
    """Welche Punkte den Fristbeginn noch aufhalten.

    Nur `FRISTBEGINN` zaehlt. Die beiden Freigaben pausieren eine bereits
    laufende Frist; sie koennen sie nicht aufhalten, weil es sie vor dem Start
    noch gar nicht gibt.
    """
    fertig = set(erledigt or ())
    return tuple(p for p in punkte
                 if p.wirkung == FRISTBEGINN and p.kennung not in fertig)
