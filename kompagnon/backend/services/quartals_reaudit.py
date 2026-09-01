# -*- coding: utf-8 -*-
"""Das Quartals-Re-Audit der Pflege-Abos — der Termingeber (L-101).

**Der letzte kleine Teil des Eintrags.** ABO-BAS und ABO-PRO sagen neben
Inhaltspflege und Sicherungen ein **Quartals-Re-Audit** zu. Der Eintrag nennt
das „den kleinsten Teil, der Scheduler laeuft ja" — richtig, und trotzdem war
er bis heute nicht baubar: Ein Termingeber muss wissen, **wen** er meint, und
welches Abo fuer einen Betrieb gilt, stand bis zum 01.09.2026 nirgends. Erst
mit `modelle_abo.AboVertrag` hat die Frage eine Antwort.

**Dieser Job gibt kein Geld aus, und das ist eine Entscheidung.** Er koennte
die Pruefung selbst ausloesen — jede kostet Modellaufrufe und PageSpeed. Er
tut es nicht, aus drei Gruenden:

1. **Die Zusage ist ein Re-Audit, der Wert ist der Vergleich.** Eine Pruefung,
   die laeuft und die niemand neben die vorige legt, loest die Zusage nicht
   ein — sie verbraucht nur Budget.
2. **Das Guthaben ist knapp und benannt.** L-58 haengt genau daran; ein Job,
   der es vierteljaehrlich still aufbraucht, ist der falsche Zeitpunkt.
3. **G4 haengt am Hinsehen.** Faellt der Wert, ist Nachbesserung ohne
   Berechnung zugesagt. Das ist eine Entscheidung mit Geldfolge und gehoert
   einem Menschen, nicht einem Cron-Eintrag.

Also: Er sagt, **wer dran ist**, und legt eine Meldung. „Termingeber" ist
woertlich das, was der Eintrag verlangt.

**Er meldet einmal je Quartal, nicht einmal je Betrieb.** Es ist eine
wiederkehrende Aufgabe, kein Ereignis je Kunde; zwanzig Meldungen an einem
Morgen sind eine, die niemand liest.

**Nicht jedes Abo ist vierteljaehrlich dran** (korrigiert am 01.09.2026 am
Produktdatenblatt). Der erste Entwurf meldete **beide** Abos jedes Quartal —
`docs/produkte/abo-und-geo.md` sagt anderes: ABO-BAS bekommt Position 7,
**jaehrliches** Re-Audit; erst ABO-PRO tauscht das gegen Position 10,
**quartalsweise**. Vier statt einer Pruefung im Jahr fuer einen
Basic-Kunden waeren viermal Guthaben und dreimal eine Leistung, fuer die
niemand zahlt.
"""
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

#: Wonach die Meldung wiedererkannt wird. Eigene Art neben `ticket`, `chat`
#: und `mail` — der Kopftext von `benachrichtigungen` sagt ausdruecklich, dass
#: eine vierte eine Zeile kosten soll und keine Migration.
ART = "faellig"

#: Wohin der Klick fuehrt. Eine Meldung ohne Weg dorthin verlangt vom Leser,
#: sich die Namen zu merken und selbst zu suchen.
ZIEL = "/app/betriebe"

#: Wie oft ein Abo geprueft wird — aus `docs/produkte/abo-und-geo.md`,
#: Position 7 (BAS: jaehrlich) und Position 10 (PRO: quartalsweise).
TAKT_MONATE = {"ABO-BAS": 12, "ABO-PRO": 3}


def quartal_von(zeitpunkt: Optional[datetime] = None) -> str:
    """`2026-Q3` — die Kennung, an der sich Faelligkeit und Meldung messen."""
    z = zeitpunkt or datetime.utcnow()
    return f"{z.year}-Q{(z.month - 1) // 3 + 1}"


def _monate_zurueck(datum: datetime, monate: int) -> datetime:
    """Derselbe Tag, `monate` frueher — ohne Bibliothek und ohne Ueberlauf."""
    gesamt = (datum.year * 12 + datum.month - 1) - monate
    return datetime(gesamt // 12, gesamt % 12 + 1, datum.day)


def quartalsbeginn(zeitpunkt: Optional[datetime] = None) -> datetime:
    z = zeitpunkt or datetime.utcnow()
    return datetime(z.year, ((z.month - 1) // 3) * 3 + 1, 1)


def faellige_betriebe(db, zeitpunkt: Optional[datetime] = None) -> list:
    """Betriebe mit laufendem Abo, die in diesem Quartal keine Pruefung haben.

    **Ohne Vertrag keine Faelligkeit.** Ein Re-Audit ist zugesagt, wo ein Abo
    gilt — sonst waere es eine Leistung, fuer die niemand zahlt, und die
    Meldung nennte Betriebe, die nichts erwarten.
    """
    from database import AuditResult, Lead
    from modelle_abo import AboVertrag
    from services import abo_vertrag

    monat = (zeitpunkt or datetime.utcnow()).strftime("%Y-%m")
    beginn = quartalsbeginn(zeitpunkt)

    laufende = (db.query(AboVertrag)
                  .filter(AboVertrag.start_monat <= monat)
                  .filter((AboVertrag.end_monat.is_(None))
                          | (AboVertrag.end_monat >= monat))
                  .all())

    faellig = []
    for vertrag in laufende:
        # **Der Vertrag wird ueber denselben Weg geprueft wie ueberall.** Die
        # Abfrage oben ist die Vorauswahl; welcher Vertrag im Monat wirklich
        # gilt, beantwortet `abo_vertrag` — zwei Rechnungen fuer dieselbe
        # Frage waeren zwei Wahrheiten.
        gueltig = abo_vertrag.gilt_im_monat(db, lead_id=vertrag.lead_id,
                                            monat=monat)
        if gueltig is None or gueltig.id != vertrag.id:
            continue

        # **Der Zeitraum haengt am Abo, nicht am Kalenderquartal.** ABO-BAS
        # ist einmal im Jahr dran; die Frage lautet dann „gab es in den
        # letzten zwoelf Monaten eine Pruefung", nicht „in diesem Quartal".
        takt = TAKT_MONATE.get(gueltig.produkt, 3)
        seit = beginn if takt <= 3 else _monate_zurueck(beginn, takt - 3)

        letzte = (db.query(AuditResult)
                    .filter(AuditResult.lead_id == vertrag.lead_id,
                            AuditResult.status == "completed",
                            AuditResult.created_at >= seit)
                    .first())
        if letzte is not None:
            continue

        betrieb = db.query(Lead).filter(Lead.id == vertrag.lead_id).first()
        faellig.append({
            "lead_id": vertrag.lead_id,
            "betrieb": (betrieb.company_name if betrieb else "") or f"#{vertrag.lead_id}",
            "produkt": gueltig.produkt,
        })
    return faellig


def bereits_gemeldet(db, quartal: str) -> bool:
    """Steht die Meldung fuer dieses Quartal schon?

    Der Job kann zweimal laufen — ein Neustart am Ersten, ein Aufruf von Hand.
    Eine zweite Meldung fuer dasselbe Quartal waere kein Schaden, aber sie
    macht die Glocke unglaubwuerdig, und eine Glocke, der man nicht glaubt,
    schaltet man ab.
    """
    from database import Benachrichtigung

    return db.query(Benachrichtigung).filter(
        Benachrichtigung.art == ART,
        Benachrichtigung.titel.like(f"%{quartal}%")).first() is not None


def lauf(db, zeitpunkt: Optional[datetime] = None) -> dict:
    """Faelligkeiten feststellen und einmal melden. Wirft nie."""
    from services.benachrichtigungen import melden_leise

    quartal = quartal_von(zeitpunkt)
    faellig = faellige_betriebe(db, zeitpunkt)

    ergebnis = {"quartal": quartal, "faellig": len(faellig),
                "betriebe": [f["betrieb"] for f in faellig], "gemeldet": False}

    if not faellig:
        # **Keine Meldung, wenn nichts ansteht.** „Nichts zu tun" als
        # Benachrichtigung ist der schnellste Weg, dass die naechste echte
        # ueberlesen wird.
        logger.info("Quartals-Re-Audit %s: nichts faellig", quartal)
        return ergebnis

    if bereits_gemeldet(db, quartal):
        logger.info("Quartals-Re-Audit %s: schon gemeldet", quartal)
        return ergebnis

    namen = ", ".join(f["betrieb"] for f in faellig[:8])
    if len(faellig) > 8:
        namen += f" und {len(faellig) - 8} weitere"

    melden_leise(
        db, art=ART,
        titel=f"Quartals-Re-Audit {quartal} fällig — {len(faellig)} Betriebe",
        hinweis=(f"{namen}. Das Re-Audit ist im Pflege-Abo zugesagt; fällt der "
                 f"Wert gegenüber der letzten Prüfung, ist Nachbesserung ohne "
                 f"Berechnung vereinbart (G4). Die Prüfung wird von Hand "
                 f"ausgelöst — sie kostet Guthaben."),
        ziel=ZIEL)
    ergebnis["gemeldet"] = True
    logger.info("Quartals-Re-Audit %s: %d Betriebe gemeldet", quartal, len(faellig))
    return ergebnis


def lauf_mit_eigener_sitzung() -> dict:
    """Einstieg fuer den Scheduler — eigene Sitzung, wie alle Jobs hier."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        return lauf(db)
    except Exception:                                   # noqa: BLE001
        logger.exception("Quartals-Re-Audit: Lauf fehlgeschlagen")
        return {"quartal": quartal_von(), "faellig": 0, "betriebe": [],
                "gemeldet": False}
    finally:
        db.close()
