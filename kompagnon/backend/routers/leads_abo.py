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
