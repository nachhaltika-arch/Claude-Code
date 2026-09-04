# -*- coding: utf-8 -*-
"""Änderungswünsche des Kunden — der Weg zum Guthaben aus dem Abo.

**Was hier neu ist und was nicht.** Die Zusage steht in Position 5 und 8 des
Leistungsverzeichnisses: „Inhaltsänderungen bis 30 bzw. 90 Minuten je Monat".
Die **Zeiterfassung** dafür gibt es seit dem 31.08. (`services/abo_stunden`),
die **Abrechnung** seit demselben Tag. Es fehlte allein die Kundenseite: ein
Weg, eine Änderung anzufordern, und ein sichtbarer Kontostand.

**Dieses Modul rechnet keine Minuten.** Es hält den Wunsch. Der Stand kommt
unverändert aus `abo_stunden.monatsstand` — ein zweiter Ort für dieselbe Zahl
wäre ein Ort, an dem sie irgendwann abweicht. Genau dieser Fehler ist am
01.09. schon einmal passiert, als die Kontingente aus einem Fließtext statt
aus dem Datenblatt kamen.

**Zwei Produktfragen sind bewusst nicht entschieden**, sondern so gebaut, dass
die Antwort sichtbar bleibt:

* **Nicht genutzte Minuten verfallen** — „bis 30 Minuten je Monat" liest sich
  je Monat, nicht kumulativ. Wer es anders will, ändert es an einer Stelle.
* **Über dem Guthaben wird nicht blockiert.** Ein Wunsch wird angenommen und
  als „über dem Guthaben" ausgewiesen. Zu blockieren hiesse, eine Zusage zu
  machen, die im Datenblatt nicht steht („was darüber liegt, kostet X") — und
  eine Zahl zu erfinden, die niemand vereinbart hat.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from modelle_abo import InhaltsAnfrage
from services.abo_stunden import monat_von, pruefe_monat

#: Die Zustände eines Wunsches. „abgelehnt" braucht immer eine Notiz — eine
#: Ablehnung ohne Grund ist für den Kunden dasselbe wie keine Antwort.
ZUSTAENDE = ("offen", "in_arbeit", "erledigt", "abgelehnt")

MAX_BESCHREIBUNG = 2000


class AnfrageFehler(ValueError):
    """Eingabe, die so nicht angenommen werden kann."""


def anlegen(db: Session, *, lead_id: int, beschreibung: str, seite: str = "",
            wer: str = "", monat: Optional[str] = None) -> InhaltsAnfrage:
    """Einen Änderungswunsch aufnehmen."""
    text = (beschreibung or "").strip()
    if not text:
        raise AnfrageFehler("Bitte beschreiben Sie, was geändert werden soll.")
    if len(text) > MAX_BESCHREIBUNG:
        raise AnfrageFehler(
            f"Die Beschreibung ist zu lang (höchstens {MAX_BESCHREIBUNG} Zeichen).")

    anfrage = InhaltsAnfrage(
        lead_id=lead_id,
        monat=pruefe_monat(monat) if monat else monat_von(),
        beschreibung=text,
        seite=(seite or "").strip()[:300],
        status="offen",
        angefragt_von=wer or "",
    )
    db.add(anfrage)
    db.commit()
    db.refresh(anfrage)
    return anfrage


def liste(db: Session, *, lead_id: int, hoechstens: int = 50) -> list:
    """Die Wünsche eines Betriebs, neueste zuerst."""
    return (db.query(InhaltsAnfrage)
            .filter(InhaltsAnfrage.lead_id == lead_id)
            .order_by(InhaltsAnfrage.angefragt_am.desc())
            .limit(hoechstens).all())


def setze_status(db: Session, *, anfrage_id: int, status: str, wer: str = "",
                 notiz: str = "", zeit_id: Optional[int] = None) -> InhaltsAnfrage:
    """Den Zustand eines Wunsches ändern — Innendienst."""
    if status not in ZUSTAENDE:
        raise AnfrageFehler(f"Unbekannter Zustand {status!r}. Möglich: "
                            + ", ".join(ZUSTAENDE))
    anfrage = db.query(InhaltsAnfrage).filter(InhaltsAnfrage.id == anfrage_id).first()
    if not anfrage:
        raise AnfrageFehler("Diesen Änderungswunsch gibt es nicht.")
    if status == "abgelehnt" and not (notiz or "").strip():
        raise AnfrageFehler("Eine Ablehnung braucht einen Grund.")

    anfrage.status = status
    anfrage.bearbeitet_von = wer or anfrage.bearbeitet_von
    if notiz:
        anfrage.notiz = notiz.strip()
    if zeit_id is not None:
        anfrage.zeit_id = zeit_id
    # **Der erste Abschluss zaehlt.** Ein zweiter Klick auf „erledigt" darf das
    # Datum nicht verschieben — es steht in der Antwort an den Kunden.
    if status == "erledigt" and not anfrage.erledigt_am:
        anfrage.erledigt_am = datetime.utcnow()
    if status in ("offen", "in_arbeit"):
        anfrage.erledigt_am = None
    db.commit()
    db.refresh(anfrage)
    return anfrage


def nach_aussen(anfrage: InhaltsAnfrage) -> dict:
    """Was der Kunde von einem Wunsch sieht.

    Ohne `bearbeitet_von`: Wer bei uns daran gearbeitet hat, ist unsere
    Betriebsfrage und keine Auskunft, die dem Kunden weiterhilft.
    """
    return {
        "id": anfrage.id,
        "monat": anfrage.monat,
        "beschreibung": anfrage.beschreibung,
        "seite": anfrage.seite or "",
        "status": anfrage.status,
        "angefragt_am": anfrage.angefragt_am.isoformat() if anfrage.angefragt_am else None,
        "erledigt_am": anfrage.erledigt_am.isoformat() if anfrage.erledigt_am else None,
        "notiz": anfrage.notiz or "",
    }
