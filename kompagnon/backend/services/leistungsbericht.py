# -*- coding: utf-8 -*-
'''Der Monatsbericht als Verlauf — nicht nur als Mail (L-160, Rang 2).

**Was vorher war.** `automations/scheduler_bericht.py` misst am Monatsersten
PageSpeed, lässt einen Kommentar schreiben und verschickt eine Mail. Vom
Ergebnis blieb **der letzte Messwert** in zwei Spalten am Betrieb, die der
nächste Lauf überschreibt. Der Bericht, den ABO-PRO als Leistung zusagt,
existierte damit ausschließlich im Postfach des Kunden — und im Kundenkonto,
für das er monatlich zahlt, war er nicht abrufbar.

**Zwei Dinge, die dieses Modul richtigstellt:**

1. *Gemessen ist gemessen.* Der Job schrieb nur, **wenn** die Mail hinausging
   (`if ok:`). Eine gescheiterte Zustellung warf die Messung weg, und der
   nächste Monat verglich gegen einen veralteten Stand — ein stiller Fehler
   in einer Zahl, die der Kunde zu sehen bekommt.
2. *Ein Monat, eine Zeile.* Ein zweiter Lauf schreibt fort statt anzulegen.

**Was hier bewusst nicht gespeichert wird: der Text der Mail.** Er enthält
einen Modellkommentar und Werbung für Zusatzleistungen; beides gehört in eine
Mail und nicht in eine Akte, die der Kunde später als Zusicherung liest. Der
Bericht im Konto zeigt, was gemessen wurde.
'''
import logging
import re
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

MONAT = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

#: Wie viele Monate der Verlauf im Kundenkonto zeigt. Zwölf, weil der
#: Vergleich über ein Jahr die Frage beantwortet, die der Kunde stellt
#: („wird es besser?"), und weil ein Jahr auf einen Bildschirm passt.
VERLAUF_MONATE = 12


class MonatFehler(ValueError):
    """Ein Monat, der so nicht in die Spalte darf."""


def pruefe_monat(monat: str) -> str:
    wert = (monat or "").strip()
    if not MONAT.match(wert):
        raise MonatFehler(f"„{monat}“ ist kein Monat der Form JJJJ-MM.")
    return wert


def monat_von(zeitpunkt: Optional[datetime] = None) -> str:
    return (zeitpunkt or datetime.utcnow()).strftime("%Y-%m")


def schreibe(db, *, lead_id: int, monat: str, mobile: Optional[int],
             desktop: Optional[int] = None, vormonat_mobile: Optional[int] = None,
             versendet: bool = False):
    '''Den Bericht eines Monats festhalten — anlegen oder fortschreiben.

    Gibt die Zeile zurück. `mobile=None` ist erlaubt und heißt **nicht
    erhoben**: dieselbe Regel wie im Audit (§ 3.5). Eine fehlende Messung als
    Null zu speichern wäre eine Aussage über die Website, die niemand gemacht
    hat.
    '''
    from modelle_abo import Leistungsbericht

    monat = pruefe_monat(monat)
    zeile = (db.query(Leistungsbericht)
               .filter(Leistungsbericht.lead_id == lead_id,
                       Leistungsbericht.monat == monat)
               .first())

    if zeile is None:
        zeile = Leistungsbericht(lead_id=lead_id, monat=monat,
                                 erstellt_am=datetime.utcnow())
        db.add(zeile)

    zeile.mobile = mobile
    zeile.desktop = desktop
    zeile.vormonat_mobile = vormonat_mobile
    # **Ein einmal erfolgreicher Versand bleibt vermerkt.** Läuft der Job im
    # selben Monat ein zweites Mal und scheitert die Mail, wäre es falsch,
    # den Kunden nachträglich als unbenachrichtigt zu führen.
    zeile.versendet = bool(zeile.versendet) or bool(versendet)
    db.commit()
    db.refresh(zeile)
    return zeile


def verlauf(db, lead_id: int, monate: int = VERLAUF_MONATE) -> List[dict]:
    '''Die letzten Monate, jüngster zuerst — mit der Richtung gegenüber dem Vormonat.

    **Die Richtung wird hier gerechnet und nicht gespeichert.** Sie ist eine
    Aussage über zwei Zeilen; steht sie in einer davon, ist sie falsch, sobald
    ein Monat nachgetragen wird.
    '''
    from modelle_abo import Leistungsbericht

    zeilen = (db.query(Leistungsbericht)
                .filter(Leistungsbericht.lead_id == lead_id)
                .order_by(Leistungsbericht.monat.desc())
                .limit(max(1, monate))
                .all())

    ergebnis = []
    for i, z in enumerate(zeilen):
        vorher = zeilen[i + 1].mobile if i + 1 < len(zeilen) else z.vormonat_mobile
        unterschied = (z.mobile - vorher) if (z.mobile is not None and vorher is not None) else None
        ergebnis.append({
            "monat": z.monat,
            "mobile": z.mobile,
            "desktop": z.desktop,
            "unterschied": unterschied,
            "versendet": bool(z.versendet),
        })
    return ergebnis


def letzter(db, lead_id: int) -> Optional[dict]:
    """Der jüngste Bericht — oder `None`, wenn es noch keinen gibt."""
    reihe = verlauf(db, lead_id, monate=1)
    return reihe[0] if reihe else None
