# -*- coding: utf-8 -*-
"""Der Rechnungsnummernkreis — `KAS-YY-0000` (L-100, ORDERS_07).

**Die Entscheidung (David, 29.08.2026): ein gemeinsamer Kreis**, Format
`KAS-26-0001`. ORDERS_07 stellt zwei zulässige Wege zur Wahl — getrennte
Kreise mit eigenem Präfix oder einen gemeinsamen. Projekte und Shop ziehen
jetzt aus derselben Quelle; zwei Systeme, die unabhängig Nummern vergeben,
erzeugen entweder Doppelungen oder Lücken.

**Der Mangel, den das behebt, ist älter als der Shop.** `routers/retainer.py`
vergab die Nummer als `COUNT(*) + 1` über `invoices`. ORDERS_07 warnt vor
`MAX(...) + 1` als unsicher bei gleichzeitigen Käufen — `COUNT(*)` ist
schlechter:

* Wird eine Rechnung gelöscht, **sinkt** die Zahl, und die nächste Vergabe
  wiederholt eine bereits vergebene Nummer.
* Zwei gleichzeitige Aufrufe zählen dieselbe Menge und bekommen dieselbe
  Nummer.

Die GoBD verlangen einen lückenlosen, fortlaufenden und nachvollziehbaren
Nummernkreis. Fehlt eine Nummer, muss erklärbar sein, warum; wird eine zweimal
vergeben, ist die Buchführung angreifbar.

**Warum eine eigene Tabelle und keine Ableitung aus dem Bestand.** Eine
abgeleitete Nummer hängt davon ab, welche Zeilen gerade da sind — sie ändert
sich also rückwirkend, wenn jemand eine Rechnung storniert oder ein
Datenbank-Auszug eingespielt wird. Ein Zähler ist ein eigener Sachverhalt und
gehört in eine eigene Zeile.

**Die Sperre ist der Kern.** `SELECT … FOR UPDATE` hält die Zeile für die
Dauer der Transaktion; ein zweiter Aufruf wartet, statt denselben Stand zu
lesen. Ohne sie wäre die Tabelle nur eine umständlichere Form desselben
Fehlers.

**Die Umstellung setzt auf dem Bestand auf.** Bis heute liefen die Nummern als
`KAS-2026-0001` mit vierstelligem Jahr. Beim ersten Gebrauch eines Jahres wird
der Zähler aus den vorhandenen Nummern **beider** Formate gesetzt. Ein
Formatwechsel ist erklärbar; eine zweite Rechnung mit derselben Nummer nicht.
"""
import logging
import re
from datetime import date
from typing import Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)

#: Der Präfix des gemeinsamen Kreises.
PRAEFIX = "KAS"

#: Wie viele Stellen die laufende Nummer mindestens hat. Sie wird nicht
#: abgeschnitten, wenn es mehr werden — eine fünfstellige Rechnungsnummer ist
#: richtig, eine abgeschnittene ist eine Doppelvergabe.
STELLEN = 4

#: Erkennt beide Formate: `KAS-2026-0007` (bis 28.08.2026) und `KAS-26-0007`.
_BESTAND = re.compile(r"^([A-Z]+)-(\d{2}|\d{4})-(\d+)$")


def formatieren(praefix: str, jahr: int, laufend: int) -> str:
    """`KAS`, 2026, 7 → `KAS-26-0007`."""
    return f"{praefix}-{jahr % 100:02d}-{laufend:0{STELLEN}d}"


def _hoechste_im_bestand(db, praefix: str, jahr: int) -> int:
    """Die höchste bereits vergebene laufende Nummer dieses Jahres.

    Liest **beide** Formate. In Python verglichen und nicht in SQL: Ein
    Zeichenkettenvergleich hielte `KAS-26-10000` für kleiner als
    `KAS-26-0999`, und genau dort begänne die Doppelvergabe.
    """
    zeilen = db.execute(text(
        "SELECT invoice_number FROM invoices WHERE invoice_number LIKE :muster"
    ), {"muster": f"{praefix}-%"}).fetchall()

    hoechste = 0
    for (nummer,) in zeilen:
        treffer = _BESTAND.match(str(nummer or "").strip().upper())
        if not treffer:
            continue
        gefunden_praefix, gefunden_jahr, laufend = treffer.groups()
        if gefunden_praefix != praefix:
            continue
        # Zweistellig gelesen, damit `26` und `2026` dasselbe Jahr sind.
        if int(gefunden_jahr) % 100 != jahr % 100:
            continue
        hoechste = max(hoechste, int(laufend))
    return hoechste


def naechste(db, praefix: str = PRAEFIX, jahr: Optional[int] = None) -> str:
    """Die nächste Rechnungsnummer — genau einmal vergeben.

    **Der Aufrufer schließt die Transaktion.** Die Sperre gilt bis zum
    `commit`; wer die Nummer holt und danach die Rechnung schreibt, hält den
    Zähler solange. Das ist gewollt: Sonst entstünde eine Nummer, die vergeben
    ist, während die Rechnung dazu scheitert — genau eine Lücke, die niemand
    erklären kann.
    """
    jahr = jahr or date.today().year

    # Anlegen, falls es den Kreis noch nicht gibt — mit dem Stand aus dem
    # Bestand. `ON CONFLICT DO NOTHING` heisst: Wer zuerst da ist, setzt auf;
    # alle anderen lesen gleich darunter den vorhandenen Wert.
    db.execute(text(
        "INSERT INTO invoice_counters (prefix, year, last_number) "
        "VALUES (:p, :j, :stand) ON CONFLICT (prefix, year) DO NOTHING"
    ), {"p": praefix, "j": jahr,
        "stand": _hoechste_im_bestand(db, praefix, jahr)})

    # **Die Sperre.** Ohne `FOR UPDATE` lesen zwei gleichzeitige Aufrufe
    # denselben Stand und bekommen dieselbe Nummer — derselbe Fehler wie bei
    # `COUNT(*) + 1`, nur mit mehr Tabellen.
    stand = db.execute(text(
        "SELECT last_number FROM invoice_counters "
        "WHERE prefix = :p AND year = :j FOR UPDATE"
    ), {"p": praefix, "j": jahr}).scalar()

    laufend = int(stand or 0) + 1
    db.execute(text(
        "UPDATE invoice_counters SET last_number = :n "
        "WHERE prefix = :p AND year = :j"
    ), {"n": laufend, "p": praefix, "j": jahr})

    nummer = formatieren(praefix, jahr, laufend)
    logger.info("Rechnungsnummer vergeben: %s", nummer)
    return nummer
