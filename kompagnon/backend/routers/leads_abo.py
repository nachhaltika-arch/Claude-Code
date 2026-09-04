"""Pflegestunden eines Betriebs — die Abo-Achse der Zeiterfassung (L-101).

Zwei Endpunkte am Betrieb: eintragen und nachsehen. Die Rechnung selbst steht
in `services/abo_stunden.py`; hier steht nur, wer darf und was zurückkommt.

**Warum eine eigene Datei und nicht `leads.py`.** Die steht bei 726 Zeilen,
und L-25 hat den Bestand mühsam unter die Grenze gebracht. Dieselbe Ordnung
wie `leads_briefing.py`: eigenes Modul, gleiches Präfix.

**Die Sperre hängt am Router, nicht nur an der Funktion.** Genau das ging beim
Umzug am 30.08.2026 zuerst schief — wer ein Modul herauslöst und den Router
ohne Abhängigkeit neu anlegt, macht aus „Innendienst" still „irgendwer ist
angemeldet". Pflegestunden eines fremden Betriebs sind Geschäftsdaten.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from routers.auth_router import get_current_user, require_innendienst
from services import abo_vertrag
from services.abo_stunden import (AboZeitFehler, eintragen, monat_von,
                                  monatsstand)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads-abo"],
                   dependencies=[Depends(require_innendienst)])


class AboZeitEingabe(BaseModel):
    """Was der Bildschirm schickt.

    **`wer` steht nicht drin.** Wer eingetragen hat, kommt aus der Anmeldung
    und nicht aus einem Textfeld — sonst ist die Zuordnung eine Behauptung des
    Absenders. Dieselbe Regel wie auf der Projektachse.
    """
    stunden: float
    taetigkeit: str = ""
    #: Leer heisst „laufender Monat". Gesetzt heisst: Der Eintrag gehört in
    #: einen anderen — etwa Augustarbeit, die am 2. September gebucht wird.
    monat: str = ""


def _wer(nutzer) -> str:
    name = (f"{getattr(nutzer, 'first_name', '') or ''} "
            f"{getattr(nutzer, 'last_name', '') or ''}").strip()
    return name or getattr(nutzer, "email", "") or "Innendienst"


@router.get("/{lead_id}/abo-zeiten")
def abo_zeiten_lesen(lead_id: int,
                     monat: str = Query(default="", description="JJJJ-MM"),
                     db: Session = Depends(get_db)):
    """Die Pflegestunden eines Betriebs in einem Monat.

    Ohne `monat` der laufende. Die **Summe** kommt mit, damit sie nicht jeder
    Bildschirm selbst rechnet und einer davon falsch — dieselbe Überlegung wie
    bei den Projektzeiten.
    """
    try:
        return monatsstand(db, lead_id=lead_id, monat=monat or monat_von())
    except AboZeitFehler as fehler:
        raise HTTPException(status_code=400, detail=str(fehler))


@router.post("/{lead_id}/abo-zeiten")
def abo_zeit_eintragen(lead_id: int, eingabe: AboZeitEingabe,
                       db: Session = Depends(get_db),
                       nutzer=Depends(get_current_user)):
    """Pflegestunden verbuchen — und den neuen Monatsstand zurückgeben.

    Der Stand kommt mit, damit der Bildschirm nach dem Eintragen nicht ein
    zweites Mal fragen muss und dabei einen anderen Augenblick sieht.
    """
    try:
        eintrag = eintragen(db, lead_id=lead_id, stunden=eingabe.stunden,
                            wer=_wer(nutzer), taetigkeit=eingabe.taetigkeit,
                            monat=eingabe.monat or None)
    except AboZeitFehler as fehler:
        raise HTTPException(status_code=400, detail=str(fehler))

    return {"id": eintrag.id,
            **monatsstand(db, lead_id=lead_id,
                          monat=eintrag.abrechnungsmonat)}


# ═══════════════════════════════════════════════════════════════════
# Der Vertrag — welches Abo gilt (L-101, zweite Hälfte)
# ═══════════════════════════════════════════════════════════════════

class AboVertragEingabe(BaseModel):
    produkt: str
    #: Leer heißt „ab dem laufenden Monat".
    start_monat: str = ""
    #: Leer heißt „läuft" — das ist der Normalfall bei einem Abschluss.
    end_monat: str = ""
    notiz: str = ""


class AboEndeEingabe(BaseModel):
    #: Der letzte Monat, für den das Abo noch gilt — einschließlich.
    end_monat: str


def _vertrag_nach_aussen(v) -> dict:
    return {
        "id": v.id,
        "produkt": v.produkt,
        "start_monat": v.start_monat,
        "end_monat": v.end_monat,
        "laeuft": v.end_monat is None,
        "kontingent_stunden": abo_vertrag.KONTINGENT.get(v.produkt),
        "notiz": v.notiz or "",
        "angelegt_am": v.created_at.isoformat() if v.created_at else None,
        "angelegt_von": v.created_by or "",
    }


@router.get("/{lead_id}/abo-vertrag")
def abo_vertraege_lesen(lead_id: int, db: Session = Depends(get_db)):
    """Alle Verträge eines Betriebs, neueste zuerst.

    **Alle, nicht nur der laufende.** Wer eine alte Rechnung prüft, muss sehen,
    was damals galt — ein beendeter Vertrag wird deshalb nicht gelöscht,
    sondern bekommt ein Ende.
    """
    alle = abo_vertrag.vertraege(db, lead_id)
    return {
        "vertraege": [_vertrag_nach_aussen(v) for v in alle],
        "laufend": next((_vertrag_nach_aussen(v) for v in alle
                         if v.end_monat is None), None),
        "abos": {k: v for k, v in abo_vertrag.KONTINGENT.items()},
    }


@router.post("/{lead_id}/abo-vertrag")
def abo_vertrag_anlegen(lead_id: int, eingabe: AboVertragEingabe,
                        db: Session = Depends(get_db),
                        nutzer=Depends(get_current_user)):
    """Ein Abo abschließen — oder auf ein anderes wechseln.

    **Ein Wechsel ist kein Ändern.** Läuft bereits ein Vertrag, wird er zum
    Vormonat beendet und ein neuer angelegt. Das Produkt an der bestehenden
    Zeile zu überschreiben änderte rückwirkend das Kontingent jedes
    vergangenen Monats.
    """
    ab = eingabe.start_monat or monat_von()
    try:
        laufend = abo_vertrag.gilt_im_monat(db, lead_id=lead_id, monat=ab)
        if laufend is not None and not eingabe.end_monat:
            vertrag = abo_vertrag.wechseln(
                db, lead_id=lead_id, produkt=eingabe.produkt, ab_monat=ab,
                notiz=eingabe.notiz, wer=_wer(nutzer))
        else:
            vertrag = abo_vertrag.anlegen(
                db, lead_id=lead_id, produkt=eingabe.produkt, start_monat=ab,
                end_monat=eingabe.end_monat or None, notiz=eingabe.notiz,
                wer=_wer(nutzer))
    except AboZeitFehler as fehler:
        raise HTTPException(status_code=400, detail=str(fehler))
    return _vertrag_nach_aussen(vertrag)


@router.patch("/{lead_id}/abo-vertrag/{vertrag_id}")
def abo_vertrag_beenden(lead_id: int, vertrag_id: int, eingabe: AboEndeEingabe,
                        db: Session = Depends(get_db)):
    """Einen Vertrag beenden — zum genannten Monat einschließlich.

    **Die Zugehörigkeit wird vor dem Schreiben geprüft, nicht danach.** Der
    erste Entwurf beendete zuerst und antwortete dann mit 404 — der Vertrag
    wäre beendet gewesen, und der Aufrufer hätte gelesen, es gebe ihn nicht.

    404 und nicht 403: Die Auskunft „diesen Vertrag gibt es, nur nicht bei
    diesem Betrieb" gehört niemandem.
    """
    vorhanden = next((v for v in abo_vertrag.vertraege(db, lead_id)
                      if v.id == vertrag_id), None)
    if vorhanden is None:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    try:
        vertrag = abo_vertrag.beenden(db, vertrag_id=vertrag_id,
                                      end_monat=eingabe.end_monat)
    except AboZeitFehler as fehler:
        raise HTTPException(status_code=400, detail=str(fehler))
    return _vertrag_nach_aussen(vertrag)
