# -*- coding: utf-8 -*-
"""Die zugesagte Bauzeit — gerechnet statt behauptet (L-166).

**Was im Angebot steht.** Der Angebotsfuss des Baukastens sagt woertlich zu:
„Die vereinbarte Bauzeit beginnt an dem Werktag, an dem saemtliche
Mitwirkungsleistungen vollstaendig vorliegen. Verzoegert sich eine Freigabe
nach M7 oder M8, ruht die Frist fuer die Dauer der Verzoegerung."

**Was bis zum 06.09.2026 fehlte.** Die erste Haelfte trug: `mitwirkung_stand`
haelt je Punkt `erledigt_am` fest, und daraus laesst sich der Beginn ableiten.
Die zweite Haelfte gar nicht — es gab **kein Feld fuer den Vorlagezeitpunkt**.
Wann ein Bauplan zur Freigabe vorlag, wann der Kunde freigab und wie viele
Werktage dazwischen die Frist ruhte, stand nirgends. Ohne diese Spanne ist das
zugesagte Ende nicht berechenbar, sondern nur behauptbar — **von beiden
Seiten**. Im Streit steht dann Aussage gegen Aussage ueber eine Frist, die wir
selbst zugesagt haben.

**Warum die Rechnung hier steht und nicht im Router.** Sie ist die Zahl, an
der die Garantie haengt, und sie wird an mehr als einer Stelle gebraucht: im
Kundenkonto, im Innendienst und spaeter bei der Garantiepruefung. Eine Zahl,
die erst beim Beantworten einer Anfrage entsteht, laesst sich weder pruefen
noch zweimal gleich beantworten.

**Die eine Auslegung, die hier getroffen wird.** „Verzoegerung" ist das, was
**ueber** die zugesagten fuenf Werktage hinausgeht — nicht die gesamte
Wartezeit. Beide Saetze stehen im selben Vertrag: „Freigabe innerhalb von
5 Werktagen nach Vorlage" **und** „ruht fuer die Dauer der Verzoegerung". Ruhte
die Frist ab dem ersten Tag, waere die Zusage der fuenf Tage bedeutungslos —
der Kunde haette sie nur nominell. Die Lesart steht in `FREIGABEFRIST_WERKTAGE`
an **einer** Stelle; wer sie aendert, aendert sie ueberall.

**Am 07.09.2026 von David bestaetigt.** Sie war bis dahin die Setzung dessen,
der sie gebaut hat — jetzt ist sie eine Entscheidung. Der Unterschied zaehlt
im Streit: Eine Auslegung, die niemand getroffen hat, ist keine.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Optional, Sequence

#: Wie lange der Kunde je Freigabe hat, bevor die Frist ruht (M7, M8).
#: Wortlaut: „Freigabe des Bauplans innerhalb von 5 Werktagen nach Vorlage".
FREIGABEFRIST_WERKTAGE = 5

#: Wenn das Produkt keine Bauzeit fuehrt. `products.delivery_days` hat
#: denselben Spaltenstandard — hier steht er noch einmal, damit die Rechnung
#: nicht von einer Datenbankeigenschaft abhaengt.
BAUZEIT_STANDARD_WERKTAGE = 14


def ostersonntag(jahr: int) -> date:
    """Der Ostersonntag nach der anonymen gregorianischen Osterformel.

    An ihm haengen vier der neun bundeseinheitlichen Feiertage. Eine Tabelle
    mit festen Daten waere kuerzer und liefe in dem Jahr aus, in dem niemand
    mehr daran denkt, sie zu verlaengern.
    """
    a = jahr % 19
    b, c = divmod(jahr, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    monat, tag = divmod(h + ell - 7 * m + 114, 31)
    return date(jahr, monat, tag + 1)


def feiertage(jahr: int) -> frozenset:
    """Die **bundesweit** einheitlichen Feiertage eines Jahres.

    Neun Tage, und bewusst nicht mehr. Fronleichnam, Allerheiligen oder der
    Reformationstag gelten je nach Bundesland; sie hier mitzuzaehlen hiesse,
    das Bundesland des Kunden zu raten — und eine Frist auf einer Vermutung
    ist schlechter als eine, die einen Tag zu streng ist.
    """
    o = ostersonntag(jahr)
    return frozenset({
        date(jahr, 1, 1),            # Neujahr
        o - timedelta(days=2),       # Karfreitag
        o + timedelta(days=1),       # Ostermontag
        date(jahr, 5, 1),            # Tag der Arbeit
        o + timedelta(days=39),      # Christi Himmelfahrt
        o + timedelta(days=50),      # Pfingstmontag
        date(jahr, 10, 3),           # Tag der Deutschen Einheit
        date(jahr, 12, 25),          # 1. Weihnachtstag
        date(jahr, 12, 26),          # 2. Weihnachtstag
    })


def ist_werktag(tag: date) -> bool:
    """Montag bis Freitag, ausser an einem bundeseinheitlichen Feiertag."""
    return tag.weekday() < 5 and tag not in feiertage(tag.year)


def naechster_werktag(tag: date) -> date:
    """Der Tag selbst, wenn er ein Werktag ist — sonst der naechste."""
    while not ist_werktag(tag):
        tag += timedelta(days=1)
    return tag


def werktage_addieren(start: date, anzahl: int) -> date:
    """`anzahl` Werktage nach `start`.

    **Der Starttag zaehlt nicht mit.** Eine Vorlage am Montag mit fuenf
    Werktagen Frist laeuft bis zum Montag darauf, nicht bis Freitag — der
    Kunde hat fuenf ganze Tage, nicht vier plus den Rest des Vorlagetags. Ist
    der Starttag selbst kein Werktag, beginnt die Zaehlung am naechsten.
    `anzahl=0` liefert den Starttag unveraendert.
    """
    tag = start
    for _ in range(max(0, anzahl)):
        tag = naechster_werktag(tag + timedelta(days=1))
    return tag


def werktage_zwischen(von: date, bis: date) -> int:
    """Wie viele Werktage seit `von` vergangen sind — eine Dauer, kein
    Kalenderausschnitt.

    Der erste Tag zaehlt nicht mit: Von Montag bis Montag sind null Werktage
    vergangen. Liegt `bis` vor `von`, ist die Antwort null und nicht negativ —
    eine Pause laeuft nicht rueckwaerts.
    """
    if not von or not bis or bis <= von:
        return 0
    tage, tag = 0, von
    while tag < bis:
        tag += timedelta(days=1)
        if ist_werktag(tag):
            tage += 1
    return tage


def _als_datum(wert) -> Optional[date]:
    """Datum aus `date` oder `datetime` — beides kommt vor, je nach Spalte."""
    if isinstance(wert, datetime):
        return wert.date()
    return wert if isinstance(wert, date) else None


@dataclass(frozen=True)
class Pause:
    """Was eine einzelne Freigabe die Frist gekostet hat.

    `laeuft_noch` unterscheidet die abgeschlossene Verzoegerung von der
    wachsenden: Solange niemand freigegeben hat, wird die Pause jeden Werktag
    groesser. Ein Konto, das das nicht sagt, zeigt ein Ende, das mit jedem Tag
    falscher wird und trotzdem gleich bleibt.
    """

    werktage: int
    frist_bis: Optional[date]
    vorgelegt_am: Optional[date]
    freigegeben_am: Optional[date]
    laeuft_noch: bool


def pause_je_freigabe(vorgelegt_am, freigegeben_am, heute=None) -> Pause:
    """Die Ruhezeit aus **einer** Freigabe (M7 oder M8).

    Ohne Vorlage gibt es keine Pause: Was nie vorgelegt wurde, kann sich beim
    Kunden nicht verzoegern — die Wartezeit liegt dann bei uns.
    """
    vorgelegt = _als_datum(vorgelegt_am)
    freigegeben = _als_datum(freigegeben_am)
    stichtag = _als_datum(heute) or date.today()

    if not vorgelegt:
        return Pause(0, None, None, freigegeben, False)

    frist_bis = werktage_addieren(vorgelegt, FREIGABEFRIST_WERKTAGE)
    if freigegeben:
        return Pause(werktage_zwischen(frist_bis, freigegeben), frist_bis,
                     vorgelegt, freigegeben, False)
    return Pause(werktage_zwischen(frist_bis, stichtag), frist_bis,
                 vorgelegt, None, True)


def fristbeginn_aus(eingaenge: Sequence) -> Optional[date]:
    """Der Werktag, an dem **saemtliche** Mitwirkungsleistungen vorlagen.

    `eingaenge` sind die Eingangszeitpunkte der fristbegruendenden Punkte, in
    beliebiger Reihenfolge. Fehlt einer (`None`), beginnt keine Frist — und es
    wird auch keine geraten: Ein angezeigtes Ende waere eine Zusage, die
    niemand gegeben hat.
    """
    if not eingaenge:
        return None
    daten = [_als_datum(e) for e in eingaenge]
    if any(d is None for d in daten):
        return None
    return naechster_werktag(max(daten))


def bauzeitende(fristbeginn, bauzeit_werktage: int,
                pause_werktage: int = 0) -> Optional[date]:
    """Der zugesagte Fertigstellungstag — Beginn plus Bauzeit plus Ruhezeit."""
    beginn = _als_datum(fristbeginn)
    if not beginn:
        return None
    return werktage_addieren(beginn, max(0, bauzeit_werktage) + max(0, pause_werktage))


def pausen_summe(pausen: Iterable[Pause]) -> int:
    """Alle Ruhezeiten zusammen — was das Ende nach hinten schiebt."""
    return sum(p.werktage for p in pausen)
