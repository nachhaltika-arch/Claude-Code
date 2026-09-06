# -*- coding: utf-8 -*-
"""Was der Kunde fuer sein Pflege-Abo bekommt — als Daten (L-160).

**Der Befund vom 04.09.2026.** Zwoelf Positionen, fuer die ein Betrieb 79 €
(ABO-BAS) bzw. 149 € (ABO-PRO) netto **monatlich** zahlt — und **keine
einzige** war im Konto abrufbar. Weder was er bekommt, noch wie viel er
genutzt hat, noch wie er es anfordert. In der Kundenreise ist das der tiefste
Punkt der ganzen Strecke, und der Grund ist einfach: Ein Abo, dessen
Leistungen man nicht sieht, wird gekuendigt, weil es sich nach nichts anfuehlt.

**Warum als Daten und nicht als Text in der Oberflaeche.** Dieselbe
Begruendung wie beim Mitwirkungskatalog: Eine Zusage ist eine **Eigenschaft
der Leistung**, keine Frage der Darstellung. Eine Verzweigung nach
Abo-Kennung im JSX waere der zweite Ort, an dem das Datenblatt gepflegt
werden muesste — und der Bildschirm sagte eines Tages etwas anderes als der
Vertrag.

**`ort` ist der Kern von Rang 3.** Eine Leistung, die nirgends benannt ist,
wird nicht wahrgenommen und trotzdem bezahlt. Jede Position sagt deshalb, an
welchem Bildschirm ihre Zusage hingehoert — die Reaktionszeit an den Support,
das Aenderungsguthaben an die Inhaltsaenderungen. Ein Eintrag ohne Ort waere
eine Zusage ohne Adressat.

**Die Quelle ist das Produktdatenblatt**, `KAS_DB_07_Pflege_und_GEO.md`, und
nicht ein Summentext. Wer eine Zahl braucht, liest das Blatt: Aus „bis 90
Minuten (statt 30)" wurden hier schon einmal zwei Stunden.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

ABO_BAS = "ABO-BAS"
ABO_PRO = "ABO-PRO"

#: Wo eine Zusage gilt — der Bildschirm, auf dem sie stehen muss.
ORT_LAUFEND = "laufend"          # nichts anzufordern, laeuft im Hintergrund
ORT_AENDERUNGEN = "aenderungen"  # „Inhaltsaenderungen"
ORT_SUPPORT = "support"          # „Support-Anfragen"
ORT_BERICHT = "bericht"          # „Mein Bericht"
ORT_REAUDIT = "reaudit"          # Re-Audit-Termin im Bericht
ORT_SICHERUNG = "sicherung"      # Ruecksicherung anfordern (Rang 6, noch ohne Weg)

ORTE = (ORT_LAUFEND, ORT_AENDERUNGEN, ORT_SUPPORT, ORT_BERICHT,
        ORT_REAUDIT, ORT_SICHERUNG)


@dataclass(frozen=True)
class Position:
    """Eine Abo-Leistung, wie sie im Datenblatt steht und im Konto erscheint."""

    nummer: int
    titel: str            # Kundensprache
    warum: str            # ein Satz: was er davon hat
    vertragstext: str     # der Wortlaut aus KAS_DB_07
    frequenz: str
    ort: str
    #: Was der Knopf sagt, mit dem diese Leistung abgerufen wird — `None`,
    #: wo es nichts abzurufen gibt (L-160 Rang 6, 06.09.2026).
    #:
    #: **Nur zwei Positionen tragen ihn.** Die Ruecksicherung (3) und die
    #: neue Unterseite (12) kann der Kunde heute nicht anfordern, obwohl er
    #: sie bezahlt. Die **Stoerungsmeldung** bekommt bewusst keinen: Dafuer
    #: gibt es den Support, und seit Rang 3 steht die zugesagte Reaktionszeit
    #: ueber dem Formular. Ein zweiter Knopf, der dasselbe Ticket anlegt,
    #: waere ein zweiter Weg zur selben Sache.
    abruf: Optional[str] = None
    #: Was **nach** dem Klick geschieht. Ein Abruf ohne diesen Satz laesst
    #: den Kunden raten, ob gleich etwas passiert oder jemand zurueckruft.
    abruf_danach: Optional[str] = None
    #: Die messbare Zusage als Satzteil, wo es eine gibt — sonst `None`.
    #:
    #: **Ein eigenes Feld und nicht aus dem Titel geschnitten.** Der erste
    #: Wurf las sie mit `titel.split("? ")` heraus; das haelt genau so lange,
    #: bis jemand den Titel umformuliert. Eine Zusage, die von einem
    #: Satzzeichen abhaengt, ist keine.
    zusage: Optional[str] = None
    #: Leere Menge waere „gilt fuer jedes Abo" — hier steht immer mindestens
    #: eines, weil es ohne Abo keine dieser Leistungen gibt.
    produkte: Tuple[str, ...] = (ABO_BAS, ABO_PRO)


KATALOG: Tuple[Position, ...] = (
    Position(1, "Ihre Seite ist erreichbar",
             "Server, Verschlüsselung und Ihre Internet-Adresse — wir halten sie am Laufen.",
             "Hosting, SSL-Zertifikat, Domainverwaltung", "laufend", ORT_LAUFEND),
    Position(2, "Aktuell und sicher gehalten",
             "Wir spielen Sicherheits- und Systemaktualisierungen ein, bevor sie zum Problem werden.",
             "Sicherheits- und Systemaktualisierungen", "laufend", ORT_LAUFEND),
    Position(3, "Tägliche Sicherung",
             "Jede Nacht eine Kopie. Wenn etwas schiefgeht, spielen wir sie auf Ihre Anforderung zurück.",
             "Tägliche Sicherung, Rücksicherung auf Anforderung", "täglich", ORT_SICHERUNG,
             abruf="Rücksicherung anfordern",
             abruf_danach="Wir melden uns telefonisch und klären mit Ihnen, "
                          "auf welchen Stand zurückgesetzt wird — die "
                          "Rücksicherung überschreibt, was seither entstanden "
                          "ist."),
    Position(4, "Wir merken es vor Ihnen",
             "Ihre Seite wird laufend auf Erreichbarkeit geprüft; bei einer Störung melden wir uns.",
             "Verfügbarkeitsüberwachung mit Störungsmeldung", "laufend", ORT_LAUFEND),
    Position(5, "30 Minuten Änderungen im Monat",
             "Texte, Bilder, Öffnungszeiten — sagen Sie uns, was sich ändert.",
             "Inhaltsänderungen bis 30 Minuten", "je Monat", ORT_AENDERUNGEN,
             produkte=(ABO_BAS,)),
    Position(6, "Störung? Antwort innerhalb von einem Werktag",
             "Fällt etwas aus, kümmern wir uns — und melden uns spätestens am nächsten Werktag.",
             "Störungsbehebung bei Ausfällen, Reaktion innerhalb 1 Werktag",
             "nach Bedarf", ORT_SUPPORT, produkte=(ABO_BAS,),
             zusage="innerhalb von einem Werktag"),
    Position(7, "Jährliches Re-Audit",
             "Einmal im Jahr messen wir Ihre Seite neu gegen den Homepage-Standard.",
             "Jährliches Re-Audit nach Homepage-Standard", "1× jährlich",
             ORT_REAUDIT, produkte=(ABO_BAS,)),

    # ── Nur Pflege Pro (Positionen 8 bis 12) ──────────────────────────
    Position(8, "90 Minuten Änderungen im Monat",
             "Dreimal so viel wie in Basic — Texte, Bilder, Öffnungszeiten, neue Angebote.",
             "Inhaltsänderungen bis 90 Minuten (statt 30)", "je Monat",
             ORT_AENDERUNGEN, produkte=(ABO_PRO,)),
    Position(9, "Monatlicher Leistungsbericht",
             "Jeden Monat eine Messung Ihrer Seite, mit dem Vergleich zum Vormonat.",
             "Monatlicher Leistungsbericht: Aufrufe, Anfragen, Auffindbarkeit, Ladezeit",
             "monatlich", ORT_BERICHT, produkte=(ABO_PRO,)),
    Position(10, "Re-Audit alle drei Monate",
             "Vierteljährlich statt jährlich — Abweichungen fallen früher auf.",
             "Quartalsweises Re-Audit statt jährlich", "4× jährlich",
             ORT_REAUDIT, produkte=(ABO_PRO,)),
    Position(11, "Störung? Antwort innerhalb von 4 Stunden",
             "An Werktagen melden wir uns binnen vier Stunden — nicht am nächsten Tag.",
             "Reaktionszeit bei Störungen 4 Stunden an Werktagen", "nach Bedarf",
             ORT_SUPPORT, produkte=(ABO_PRO,),
             zusage="innerhalb von 4 Stunden an Werktagen"),
    Position(12, "Eine neue Unterseite pro Jahr",
             "Ein neuer Leistungsbereich, ein neuer Standort — einmal im Jahr ist eine Seite enthalten.",
             "Eine neue Unterseite pro Jahr enthalten", "1× jährlich",
             ORT_AENDERUNGEN, produkte=(ABO_PRO,),
             abruf="Unterseite abrufen",
             abruf_danach="Ihr Betreuer meldet sich und bespricht mit Ihnen, "
                          "worum es auf der Seite gehen soll."),
)

NACH_NUMMER = {p.nummer: p for p in KATALOG}

#: Welche Position welche **ersetzt** — nicht ergaenzt.
#:
#: **Das ist der Unterschied, an dem die Abrechnung schon einmal gescheitert
#: ist.** Das Datenblatt schreibt „Inhaltsaenderungen bis 90 Minuten
#: (**statt** 30)"; wer „zusaetzlich" liest, kommt auf zwei Stunden. Dasselbe
#: gilt fuer die Reaktionszeit (11 statt 6) und das Re-Audit (10 statt 7).
#: Deshalb hat Pflege Pro **neun** wirksame Positionen und nicht zwoelf: Der
#: Katalog fuehrt zwoelf, drei davon sind Paare.
ERSETZT = {8: 5, 10: 7, 11: 6}

#: Was **nicht** im Abo steckt — wortgleich aus dem Datenblatt.
#:
#: **Warum die Ausschlussliste mitkommt.** „Inhaltsaenderungen bis 90 Minuten"
#: liest sich fuer manchen als „ihr macht alles". Der Satz daneben verhindert
#: das Gespraech, das mit „das dachte ich waere dabei" beginnt — und er steht
#: ohnehin im Vertrag.
NICHT_ENTHALTEN = (
    "neue Seiten", "Gestaltungsänderungen", "Texterstellung", "Kampagnen",
    "Rechtstextaktualisierung",
)

#: Nicht verbrauchte Minuten verfallen — auch das steht im Datenblatt und
#: gehoert dorthin, wo der Kontostand steht.
VERFALL_HINWEIS = ("Nicht verbrauchte Änderungsminuten verfallen "
                   "und werden nicht in den nächsten Monat übertragen.")


def fuer_produkt(produkt: str) -> Tuple[Position, ...]:
    """Die Positionen, die dieses Abo umfasst.

    **Ohne Abo ist die Antwort leer, nicht der Basic-Umfang.** Wer keinen
    Pflegevertrag hat, bekommt keine Leistungsliste — sonst stuende dort eine
    Zusage, die niemand gegeben hat.
    """
    kennung = (produkt or "").strip().upper()
    if kennung not in (ABO_BAS, ABO_PRO):
        return ()
    return tuple(p for p in KATALOG if kennung in p.produkte)


def reaktionszeit(produkt: str) -> Optional[str]:
    """Die zugesagte Antwortzeit bei einer Stoerung — als Satzteil.

    **Der einzige Unterschied, der im Stoerungsfall zaehlt.** Er steht heute
    im Datenblatt und gehoert an den Support: Position 6 (ein Werktag) fuer
    Basic, Position 11 (vier Stunden) fuer Pro. `None`, wenn kein Abo laeuft —
    dann gibt es keine zugesagte Zeit, und eine zu nennen waere erfunden.
    """
    for position in fuer_produkt(produkt):
        if position.ort == ORT_SUPPORT and position.zusage:
            return position.zusage
    return None
