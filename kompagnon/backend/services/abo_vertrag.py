# -*- coding: utf-8 -*-
"""Welches Pflege-Abo gilt für einen Betrieb in einem Monat? (L-101)

**Warum das die letzte offene Hälfte von L-101 war.** Die Stunden sind seit
dem 31.08.2026 zählbar, aber `abo_stunden.monatsstand()` gibt nur den
Verbrauch aus — mit dem ausdrücklichen Hinweis, dass eine Restzahl auf einer
Annahme eine Zusage wäre, die niemand gegeben hat. Dieses Modul beantwortet
die Frage, auf der alles andere aufsetzt.

**Die drei Regeln, und jede hat einen Preis, wenn sie fehlt:**

1. **Verträge eines Betriebs überlappen nicht.** Zwei gültige Verträge für
   denselben Monat verdoppelten das Kontingent — und niemand sähe es, weil
   beide für sich richtig aussehen.
2. **Ein Wechsel schreibt eine neue Zeile.** Der alte Vertrag endet im
   Vormonat, statt überschrieben zu werden. Sonst rechnete ein später
   aufgerufener Juli mit dem Abo von heute, und eine Überschreitung von damals
   verschwände.
3. **Höchstens ein laufender Vertrag.** „Läuft" heißt `end_monat IS NULL`;
   zwei davon wären zwei offene Zusagen an denselben Kunden.

**Was hier bewusst nicht passiert: kündigen heißt löschen.** Ein beendeter
Vertrag bleibt stehen und bekommt ein Ende. Gelöscht wäre die Frage „was galt
im Juli?" nicht mehr beantwortbar — und genau die stellt sich, wenn ein Kunde
eine alte Rechnung anzweifelt.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database import Lead
from modelle_abo import ABOS, AboVertrag
from services.abo_stunden import (KONTINGENT_ABO_BAS_STUNDEN,
                                  KONTINGENT_ABO_PRO_STUNDEN, AboZeitFehler,
                                  pruefe_monat)

#: Kennung → zugesagte Stunden je Monat. **Die Zahlen kommen aus
#: `abo_stunden`**, wo sie seit dem 31.08. stehen; hier steht nur die
#: Zuordnung. Ein zweiter Ort für dieselbe Zahl ist ein Ort, an dem sie
#: irgendwann abweicht.
KONTINGENT = {
    "ABO-BAS": KONTINGENT_ABO_BAS_STUNDEN,
    "ABO-PRO": KONTINGENT_ABO_PRO_STUNDEN,
}


def _vormonat(monat: str) -> str:
    jahr, mon = int(monat[:4]), int(monat[5:])
    return f"{jahr - 1}-12" if mon == 1 else f"{jahr}-{mon - 1:02d}"


def pruefe_produkt(produkt: str) -> str:
    produkt = (produkt or "").strip().upper()
    if produkt not in ABOS:
        raise AboZeitFehler(
            f"Unbekanntes Abo {produkt!r}. Möglich: " + ", ".join(ABOS))
    return produkt


def vertraege(db: Session, lead_id: int) -> list:
    """Alle Verträge eines Betriebs, neueste zuerst."""
    return (db.query(AboVertrag)
              .filter(AboVertrag.lead_id == lead_id)
              .order_by(AboVertrag.start_monat.desc(), AboVertrag.id.desc())
              .all())


def laufender(db: Session, lead_id: int):
    """Der eine Vertrag ohne Ende — oder `None`.

    Regel 3 dieses Moduls sagt: höchstens einer. Sollten wider Erwarten zwei
    dastehen, gewinnt der zuletzt begonnene; das ist keine Reparatur, sondern
    eine berechenbare Antwort, damit der Kaufweg nicht willkürlich einen von
    beiden nimmt.
    """
    return (db.query(AboVertrag)
              .filter(AboVertrag.lead_id == lead_id)
              .filter(AboVertrag.end_monat.is_(None))
              .order_by(AboVertrag.start_monat.desc(), AboVertrag.id.desc())
              .first())


def gilt_im_monat(db: Session, *, lead_id: int, monat: str):
    """Der Vertrag, der in diesem Monat galt — oder `None`.

    **`None` ist eine gültige Antwort und kein Fehler.** Ein Betrieb ohne
    Pflege-Abo ist der Normalfall; wer daraus ein Kontingent von Null machte,
    behauptete einen Vertrag mit Null Stunden, und das ist etwas anderes.
    """
    monat = pruefe_monat(monat)
    return (db.query(AboVertrag)
              .filter(AboVertrag.lead_id == lead_id,
                      AboVertrag.start_monat <= monat)
              .filter((AboVertrag.end_monat.is_(None))
                      | (AboVertrag.end_monat >= monat))
              .order_by(AboVertrag.start_monat.desc())
              .first())


def _ueberlappt(db: Session, *, lead_id: int, start: str,
                ende: Optional[str], ausser_id: Optional[int] = None) -> bool:
    """Deckt ein bestehender Vertrag einen dieser Monate mit ab?

    Zwei Zeitspannen überlappen, wenn jede vor dem Ende der anderen beginnt.
    Ein offenes Ende (`NULL`) reicht bis in alle Zukunft.
    """
    abfrage = db.query(AboVertrag).filter(AboVertrag.lead_id == lead_id)
    if ausser_id is not None:
        abfrage = abfrage.filter(AboVertrag.id != ausser_id)
    for bestand in abfrage.all():
        beginnt_vor_unserem_ende = ende is None or bestand.start_monat <= ende
        endet_nach_unserem_start = (bestand.end_monat is None
                                    or bestand.end_monat >= start)
        if beginnt_vor_unserem_ende and endet_nach_unserem_start:
            return True
    return False


ABRECHNUNGSARTEN = ("stripe", "rechnung")


def anlegen(db: Session, *, lead_id: int, produkt: str, start_monat: str,
            end_monat: Optional[str] = None, notiz: str = "",
            wer: str = "", abrechnung: str = "stripe") -> AboVertrag:
    """Einen Vertrag eintragen. Wirft `AboZeitFehler` bei Überlappung.

    `abrechnung` sagt, wie eingezogen wird — `stripe` (Vorgabe seit der
    Entscheidung vom 04.09.2026) oder `rechnung`. Beides bleibt möglich: Ein
    Betrieb, der keine Einzugsermächtigung erteilen will, bekommt weiter eine
    Rechnung, und `abo_abrechnung` stellt genau diese auf.
    """
    produkt = pruefe_produkt(produkt)
    start = pruefe_monat(start_monat)
    ende = pruefe_monat(end_monat) if end_monat else None

    if ende is not None and ende < start:
        raise AboZeitFehler(
            f"Das Ende ({ende}) liegt vor dem Beginn ({start}).")

    if not db.query(Lead).filter(Lead.id == lead_id).first():
        raise AboZeitFehler("Betrieb nicht gefunden.")

    if _ueberlappt(db, lead_id=lead_id, start=start, ende=ende):
        raise AboZeitFehler(
            "Für diesen Zeitraum besteht bereits ein Vertrag. Beenden Sie den "
            "laufenden zuerst — ein Wechsel schreibt eine neue Zeile, damit "
            "vergangene Monate weiter mit ihrem eigenen Kontingent rechnen.")

    art = (abrechnung or "stripe").strip().lower()
    if art not in ABRECHNUNGSARTEN:
        raise AboZeitFehler(
            f"„{abrechnung}“ ist keine Abrechnungsart — möglich sind "
            f"{' und '.join(ABRECHNUNGSARTEN)}.")

    vertrag = AboVertrag(lead_id=lead_id, produkt=produkt, start_monat=start,
                         end_monat=ende, notiz=(notiz or "")[:255],
                         created_by=(wer or "")[:120], abrechnung=art,
                         created_at=datetime.utcnow())
    db.add(vertrag)
    db.commit()
    db.refresh(vertrag)
    return vertrag


def beenden(db: Session, *, vertrag_id: int, end_monat: str) -> AboVertrag:
    """Einen laufenden Vertrag zum genannten Monat beenden (einschließlich)."""
    ende = pruefe_monat(end_monat)
    vertrag = db.query(AboVertrag).filter(AboVertrag.id == vertrag_id).first()
    if not vertrag:
        raise AboZeitFehler("Vertrag nicht gefunden.")
    if ende < vertrag.start_monat:
        raise AboZeitFehler(
            f"Das Ende ({ende}) liegt vor dem Beginn ({vertrag.start_monat}).")
    if _ueberlappt(db, lead_id=vertrag.lead_id, start=vertrag.start_monat,
                   ende=ende, ausser_id=vertrag.id):
        raise AboZeitFehler("Das Ende überschneidet einen anderen Vertrag.")
    vertrag.end_monat = ende
    db.commit()
    db.refresh(vertrag)
    return vertrag


def wechseln(db: Session, *, lead_id: int, produkt: str, ab_monat: str,
             notiz: str = "", wer: str = "") -> AboVertrag:
    """Auf ein anderes Abo wechseln — der laufende endet im Vormonat.

    **Der Wechsel ist ein eigener Vorgang und kein „ändern".** Wer das Produkt
    an der bestehenden Zeile überschriebe, änderte rückwirkend das Kontingent
    jedes vergangenen Monats — und eine Überschreitung von damals wäre danach
    keine mehr.
    """
    ab = pruefe_monat(ab_monat)
    laufend = gilt_im_monat(db, lead_id=lead_id, monat=ab)
    if laufend is not None:
        if laufend.start_monat == ab:
            raise AboZeitFehler(
                f"Ab {ab} beginnt bereits ein Vertrag. Ein Wechsel im selben "
                f"Monat wäre nicht unterscheidbar — wählen Sie den Folgemonat.")
        beenden(db, vertrag_id=laufend.id, end_monat=_vormonat(ab))
    return anlegen(db, lead_id=lead_id, produkt=produkt, start_monat=ab,
                   notiz=notiz, wer=wer)


def stand(db: Session, *, lead_id: int, monat: str, verbraucht: float) -> dict:
    """Was der Monatsstand über das Abo sagen darf.

    **Ohne Vertrag bleibt es beim Verbrauch.** Genau die Zurückhaltung, die
    `abo_stunden` seit dem 31.08. übt: kein erfundenes Kontingent.

    **Mit Vertrag steht die Restzahl da — auch wenn sie negativ ist.** Auf
    Null zu begrenzen verstecke genau den Fall, für den das Kontingent
    gebaut ist: Es sind mehr Stunden verbraucht als zugesagt.
    """
    vertrag = gilt_im_monat(db, lead_id=lead_id, monat=monat)
    if vertrag is None:
        return {
            "abo": None,
            "hinweis": ("Für diesen Monat ist kein Pflege-Abo hinterlegt — "
                        "deshalb steht hier der Verbrauch und keine Restzahl."),
        }

    kontingent = KONTINGENT[vertrag.produkt]
    return {
        "abo": {
            "vertrag_id": vertrag.id,
            "produkt": vertrag.produkt,
            "start_monat": vertrag.start_monat,
            "end_monat": vertrag.end_monat,
            "kontingent_stunden": kontingent,
        },
        "kontingent_stunden": kontingent,
        "verbleibend_stunden": round(kontingent - (verbraucht or 0), 2),
        "ueberzogen": (verbraucht or 0) > kontingent,
        "hinweis": "",
    }
