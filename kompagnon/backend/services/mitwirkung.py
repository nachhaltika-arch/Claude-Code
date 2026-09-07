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
from typing import Dict, Optional, Tuple

#: Wirkung auf die Bauzeit.
FRISTBEGINN = "fristbeginn"
FRISTPAUSE = "fristpause"
OHNE_FRIST = "ohne"


#: Was der Kunde an diesem Punkt **tun** kann — nicht nur abhaken.
#:
#: **Warum das im Katalog steht und nicht in der Oberflaeche** (04.09.2026).
#: „Was wir brauchen" war eine Liste zum Abhaken: Der Kunde las, was fehlt,
#: und bestaetigte, dass er es geschickt habe — per Mail, an einem anderen
#: Ort. Die Seite wusste davon nichts und der Betrieb hatte zwei Wege.
#: Welche Handlung zu einem Punkt gehoert, ist eine **Eigenschaft des
#: Punktes** und keine Frage der Darstellung; eine Verzweigung nach Kennung
#: im JSX waere der zweite Ort, an dem der Katalog gepflegt werden muss.
AKTION_ABHAKEN = "abhaken"        # nur bestaetigen (Vorgabe)
AKTION_DATEIEN = "dateien"        # echte Dateien hochladen
AKTION_DOMAIN = "domain"          # Adresse nennen und entscheiden, wer eintraegt
AKTION_PERSON = "person"          # eine Person mit Namen und Erreichbarkeit
AKTION_TERMIN = "termin"          # einen Termin buchen
AKTION_TEXTE = "texte"            # liefern oder uns schreiben lassen
AKTION_FREIGABE = "freigabe"      # fuehrt zur Freigabenseite
AKTION_ANGABEN = "angaben"        # ein paar Felder, kein Geheimnis


@dataclass(frozen=True)
class Punkt:
    """Eine Mitwirkungsleistung, wie sie im Angebot steht und im Konto erscheint."""

    kennung: str
    titel: str                 # Kundensprache, nicht Vertragssprache
    warum: str                 # ein Satz: wozu wir das brauchen
    wirkung: str
    vertragstext: str          # der Wortlaut aus dem Angebotsbaukasten
    #: **Entfernt am 07.09.2026 (L-168).** Hier stand ein Feld `produkte` mit
    #: dem Kommentar „Leere Menge heisst: gilt fuer jedes Produkt". Kein
    #: einziger Punkt setzte es, und `gilt_fuer` las es nie — ein totes Feld
    #: mit dokumentierter Bedeutung, was schlimmer ist als gar keins: Wer es
    #: sah, hielt die Produktabhaengigkeit fuer erledigt. Die Zuordnung steht
    #: jetzt in `PRODUKT_PUNKTE`, an **einer** Stelle statt verteilt auf elf.
    #: Bedingt geltende Punkte — nur wenn das Projekt das Merkmal traegt.
    bedingung: Optional[str] = None
    #: Was der Kunde hier tun kann. Vorgabe: bestaetigen.
    aktion: str = AKTION_ABHAKEN
    #: Wofuer hochgeladene Dateien stehen (`files.file_type`), wenn die
    #: Aktion Dateien sind. Eine eigene Angabe, damit der Innendienst spaeter
    #: Logo von Karrierefotos unterscheiden kann.
    dateiart: str = "sonstiges"


KATALOG: Tuple[Punkt, ...] = (
    Punkt("M1", "Ihre Internet-Adresse",
          "Wir brauchen einen Eintrag bei Ihrem Anbieter, damit die neue Seite "
          "unter Ihrer Adresse erscheint.",
          FRISTBEGINN,
          "Zugang zur Domain- bzw. DNS-Verwaltung (Zugangsdaten oder "
          "delegierter Zugriff)",
          aktion=AKTION_DOMAIN),
    Punkt("M2", "Ihre Texte",
          "Sagen Sie uns je Seite, was damit passieren soll. Vorgeschlagen ist "
          "überall: wir schreiben, Sie geben frei.",
          FRISTBEGINN,
          "Vollständige Lieferung bzw. Freigabe der zu verwendenden Inhalte",
          aktion=AKTION_TEXTE, dateiart="text"),
    Punkt("M3", "Logo und Bilder",
          "Legen Sie ab, was Sie haben. Wir sagen Ihnen bei jeder Datei, ob sie reicht.",
          FRISTBEGINN,
          "Logo als Vektordatei (SVG/EPS/AI) sowie Bildmaterial mit mind. "
          "2.000 px Kantenlänge und geklärten Nutzungsrechten",
          aktion=AKTION_DATEIEN, dateiart="logo"),
    Punkt("M4", "Impressum und Datenschutz",
          "Wenn Ihre bisherige Seite beides hat, übernehmen wir es auf Knopfdruck.",
          FRISTBEGINN,
          "Rechtstexte (Impressum, Datenschutzerklärung, ggf. AGB) vom Kunden "
          "oder dessen Rechtsberatung",
          aktion=AKTION_DATEIEN, dateiart="text"),
    Punkt("M5", "Wer entscheidet",
          "Eine Person, die Texte und Entwürfe freigeben darf.",
          FRISTBEGINN,
          "Benennung eines Ansprechpartners mit Entscheidungsbefugnis",
          aktion=AKTION_PERSON),
    Punkt("M6", "Positionierungsgespräch",
          "90 Minuten, in denen wir klären, für wen die Seite sprechen soll.",
          FRISTBEGINN,
          "Teilnahme am Positionierungsgespräch (90 Min.)",
          aktion=AKTION_TERMIN),
    Punkt("M7", "Freigabe des Bauplans",
          "Wie viele Seiten, was worauf steht. Sie haben fünf Werktage.",
          FRISTPAUSE,
          "Freigabe des Bauplans innerhalb von 5 Werktagen nach Vorlage",
          aktion=AKTION_FREIGABE),
    Punkt("M8", "Freigabe der Texte",
          "Wir schreiben, Sie lesen und geben frei. Sie haben fünf Werktage.",
          FRISTPAUSE,
          "Freigabe der Texte innerhalb von 5 Werktagen nach Vorlage",
          aktion=AKTION_FREIGABE),
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
          bedingung="karriereseite", aktion=AKTION_DATEIEN, dateiart="foto"),
    Punkt("M11", "Rechnungsdaten",
          "Steuernummer und, falls Sie öffentlich sind, die Leitweg-ID.",
          OHNE_FRIST,
          "Benennung der Steuer-/Rechnungsdaten und ggf. Leitweg-ID",
          aktion=AKTION_ANGABEN),
)

NACH_KENNUNG = {p.kennung: p for p in KATALOG}


# ── Was der Kunde eintraegt ──────────────────────────────────────────
#
# **Hier stehen keine Zugangsdaten, und das ist eine Entscheidung.** M1 und
# M9 handeln von Zugaengen zur Domainverwaltung und zum alten
# Redaktionssystem. Ein Feld dafuer waere bequem und falsch: Es lieferte uns
# fremde Passwoerter im Klartext in eine Notizspalte, mit allem, was daran
# haengt — Sicherung, Protokoll, Loeschfrist, Haftung. Der Kunde entscheidet
# stattdessen, **wer eintraegt**; braucht es Zugang, sagen wir ihm, wie er
# ihn delegiert. Ein Umweg von einer Minute gegen ein Geheimnis, das wir
# nicht verwahren wollen.

#: Was zu einer Aktion an Angaben erwartet wird — Feld: Beschriftung.
#: Die Reihenfolge ist die des Formulars.
FELDER = {
    AKTION_DOMAIN: (
        ("adresse", "Ihre Internet-Adresse"),
        ("anbieter", "Bei welchem Anbieter liegt sie?"),
    ),
    AKTION_PERSON: (
        ("name", "Name"),
        ("rolle", "Funktion im Betrieb"),
        ("email", "E-Mail"),
        ("telefon", "Telefon"),
    ),
    AKTION_ANGABEN: (
        ("steuernummer", "Steuernummer oder USt-IdNr."),
        ("leitweg_id", "Leitweg-ID, falls Sie öffentlich sind"),
    ),
}

#: Die Entscheidung bei M1: Wer traegt den Eintrag ein?
WER_TRAEGT_EIN = {
    "selbst": "Ich trage die Werte selbst ein — sagen Sie mir, welche.",
    "kompagnon": "Bitte übernehmen Sie das. Melden Sie sich bei mir wegen des Zugangs.",
}

#: Die Entscheidung bei M2: Wer schreibt?
WER_SCHREIBT = {
    "kompagnon": "Sie schreiben, ich gebe frei.",
    "selbst": "Ich liefere die Texte selbst.",
}


def felder_fuer(kennung: str) -> Tuple[Tuple[str, str], ...]:
    """Die Eingabefelder eines Punktes — leer, wenn er keine hat."""
    punkt = NACH_KENNUNG.get(kennung)
    return FELDER.get(getattr(punkt, "aktion", ""), ())


def notiz_bauen(kennung: str, angaben: dict) -> str:
    """Was der Kunde eingetragen hat, als ein lesbarer Satz je Zeile.

    **Als Text und nicht als JSON**, weil `mitwirkung_stand.notiz` genau dafuer
    da ist und weil ein Mensch im Innendienst es liest. Ein Feld mehr im
    Katalog erscheint hier von selbst; ein zweites Schema waere ein zweiter
    Ort zum Pflegen.
    """
    zeilen = []
    for feld, beschriftung in felder_fuer(kennung):
        wert = (angaben.get(feld) or "").strip()
        if wert:
            zeilen.append(f"{beschriftung}: {wert}")

    wahl = (angaben.get("wahl") or "").strip()
    punkt = NACH_KENNUNG.get(kennung)
    tabelle = (WER_TRAEGT_EIN if getattr(punkt, "aktion", "") == AKTION_DOMAIN
               else WER_SCHREIBT if getattr(punkt, "aktion", "") == AKTION_TEXTE
               else {})
    if wahl and wahl in tabelle:
        zeilen.append(tabelle[wahl])

    frei = (angaben.get("hinweis") or "").strip()
    if frei:
        zeilen.append(f"Hinweis: {frei[:400]}")
    return " · ".join(zeilen)[:255]


#: Welche Punkte ein Produkt ueberhaupt kennt — abgeschrieben aus der Zeile
#: „| Mitwirkung |" des jeweiligen Produktdatenblatts, nicht hergeleitet.
#:
#: **Warum das noetig wurde.** Bis zum 07.09.2026 bekam jedes Projekt alle elf
#: Punkte. M6 (Positionierungsgespraech) traegt `FRISTBEGINN` — ein Websprint
#: Start konnte seine Bauzeit-Uhr also erst starten, wenn ein Gespraech
#: stattgefunden hat, das sein Vertrag nicht enthaelt; Abgrenzung A18
#: schliesst persoenliche Termine dort sogar ausdruecklich aus. An dieser Uhr
#: haengt die Verzugspauschale.
#:
#: **Der Fehler ging in beide Richtungen.** Nicht nur Start war betroffen:
#: Relaunch hat ebenfalls kein M6/M7/M8, und Neubau und System haben kein M2 —
#: dort schreiben wir die Texte selbst, der Kunde liefert sie nicht.
#:
#: Nicht enthalten sind **M9** und **M10**: Die haengen ueber `bedingung` am
#: Projekt (Migration, Karriereseite), nicht am Produkt. **M11** steht in
#: keiner Kopfzeile und gilt ueberall — ohne Rechnungsdaten keine Rechnung.
PRODUKT_PUNKTE: Dict[str, Tuple[str, ...]] = {
    "websprint_start":    ("M1", "M2", "M3", "M4", "M5"),
    "websprint_relaunch": ("M1", "M2", "M3", "M4", "M5"),
    "websprint_neubau":   ("M1", "M3", "M4", "M5", "M6", "M7", "M8"),
    "websprint_system":   ("M1", "M3", "M4", "M5", "M6", "M7", "M8"),
}

#: Punkte ohne Produktbindung — sie stehen in keiner Kopfzeile, weil sie
#: selbstverstaendlich sind.
UNABHAENGIG: Tuple[str, ...] = ("M11",)


def gilt_fuer(projektmerkmale, produkt: Optional[str] = None) -> Tuple[Punkt, ...]:
    """Die Punkte, die fuer dieses Projekt ueberhaupt gelten.

    Zwei Filter, die verschiedene Fragen beantworten:

    * `produkt` ist der Paket-Slug (``project.package_type``) und sagt, was
      **der Vertrag** kennt — nach `PRODUKT_PUNKTE`.
    * `projektmerkmale` ist eine Menge von Kennworten wie ``{"migration"}``
      und sagt, was **dieses eine Projekt** zusaetzlich braucht.

    **Ein unbekanntes oder fehlendes Produkt filtert nicht.** Dann gilt wieder
    der ganze Katalog. Das ist Absicht: Der Fehler soll in die sichtbare
    Richtung fallen — lieber ein Punkt zu viel, den jemand wegklickt, als ein
    fehlender, den niemand bemerkt. `test_jedes_katalogprodukt_ist_zugeordnet`
    sorgt dafuer, dass ein neues Produkt trotzdem nicht still durchfaellt.

    **Was hier nicht erscheint, existiert fuer diesen Kunden nicht** — es wird
    nicht ausgegraut. Eine Liste mit zehn Zeilen, von denen acht grau sind, ist
    eine Liste mit zehn Zeilen.
    """
    merkmale = set(projektmerkmale or ())
    erlaubt = PRODUKT_PUNKTE.get((produkt or "").strip())
    zulaessig = set(erlaubt) | set(UNABHAENGIG) if erlaubt else None

    def passt(p: Punkt) -> bool:
        if p.bedingung is not None:
            # Bedingte Punkte kommen aus dem Projekt und werden vom Produkt
            # nicht ueberstimmt — eine Migration bleibt eine Migration.
            return p.bedingung in merkmale
        return zulaessig is None or p.kennung in zulaessig

    return tuple(p for p in KATALOG if passt(p))


def merkmale_von(project) -> set:
    """Welche bedingten Punkte fuer dieses Projekt gelten.

    **Am 07.09.2026 aus drei Kopien zusammengelegt** (L-168). Dieselben acht
    Zeilen standen in `routers/portal.py`, `services/bauzeit_projekt.py` und
    `automations/scheduler_kontakt.py`. Die Kopie im Portal trug dabei den
    Kommentar „die Stelle ist bewusst **eine**, damit die Ableitung nicht an
    drei Orten auseinanderlaeuft" — sie war zu dem Zeitpunkt die dritte.

    Eine Absichtserklaerung im Kommentar haelt nichts zusammen; ein
    gemeinsamer Aufruf tut es.
    """
    merkmale = set()
    if getattr(project, "migration_noetig", False):
        merkmale.add("migration")
    if getattr(project, "karriereseite", False):
        merkmale.add("karriereseite")
    return merkmale


def fuer_projekt(project) -> Tuple[Punkt, ...]:
    """Die geltenden Punkte eines Projekts — Produkt und Merkmale in einem.

    Der Aufruf, den alle drei Stellen brauchen. Wer `gilt_fuer` direkt ruft,
    muss an das Paket denken; hier kann man es nicht vergessen.
    """
    return gilt_fuer(merkmale_von(project),
                     produkt=getattr(project, "package_type", None))


def fristbeginn_offen(punkte, erledigt) -> Tuple[Punkt, ...]:
    """Welche Punkte den Fristbeginn noch aufhalten.

    Nur `FRISTBEGINN` zaehlt. Die beiden Freigaben pausieren eine bereits
    laufende Frist; sie koennen sie nicht aufhalten, weil es sie vor dem Start
    noch gar nicht gibt.
    """
    fertig = set(erledigt or ())
    return tuple(p for p in punkte
                 if p.wirkung == FRISTBEGINN and p.kennung not in fertig)
