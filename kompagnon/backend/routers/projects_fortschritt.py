"""Wie weit ein Projekt ist und was es gekostet hat (L-25).

Zeiterfassung, Marge und Phasen-Checkliste. Am 2026-08-30 aus `projects.py`
herausgeloest — die Datei stand mit 887 Zeilen wieder ueber der Grenze.

**Warum die drei zusammengehoeren.** Sie beantworten dieselbe Frage aus drei
Richtungen: Die Checkliste sagt, **was** erledigt ist, die Zeiten sagen,
**wie teuer** es wurde, und die Marge rechnet beides gegen den Festpreis. Wer
eine davon aendert, sieht die anderen mit — und das ist der Punkt: Bis zum
26.08.2026 kam die Marge auf ueberall ~97,5 %, weil `actual_hours` an jedem
Projekt 0 war und niemand einen Bildschirm zum Eintragen hatte. Eine Zahl, die
aussah wie eine Messung und keine war.

**Sie haengt am selben Router** wie `projects.py` — ohne den Import in
`routers/__init__.py` fehlten die fuenf Routen lautlos. Genau dafuer wird nach
jedem Schnitt die Endpunktzahl ueber `openapi()` verglichen.
"""
from datetime import datetime

from fastapi import Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Project, ProjectChecklist, get_db
from routers.auth_router import get_current_user
from routers.projects_modelle import (ChecklistItemResponse,
                                       ChecklistItemUpdate, MarginResponse,
                                       TimeLogRequest)
from routers.projects_router import router
from services.margin_calculator import MarginCalculator


@router.get("/{project_id}/time")
def zeiten_lesen(project_id: int, db: Session = Depends(get_db)):
    """Die erfassten Zeiten eines Projekts, neueste zuerst.

    **Warum es das erst seit dem 26.08.2026 gibt.** Eintragen ging, nachsehen
    nicht — eine Eingabe ohne Rueckschau laedt zum doppelten Eintragen ein.

    Die **Summe** kommt mit: Sonst rechnet sie jeder Bildschirm selbst, und
    einer davon falsch. Dieselbe Ueberlegung wie beim Margenstatus, der
    seit heute ebenfalls vom Server kommt.
    """
    if not db.query(Project).filter(Project.id == project_id).first():
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    zeilen = db.execute(text(
        "SELECT id, hours, phase, logged_by, activity_description, logged_at "
        "FROM time_tracking WHERE project_id = :p "
        "ORDER BY logged_at DESC, id DESC"
    ), {"p": project_id}).fetchall()

    eintraege = [{
        "id": z[0],
        "hours": float(z[1] or 0),
        "phase": z[2],
        "logged_by": z[3] or "",
        "activity_description": z[4] or "",
        "logged_at": z[5].isoformat() if z[5] else None,
    } for z in zeilen]

    return {"eintraege": eintraege,
            "summe": round(sum(e["hours"] for e in eintraege), 2)}


@router.post("/{project_id}/time")
def log_time(
    project_id: int,
    time_log: TimeLogRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Log hours spent on a project and update margin."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # **Null oder negativ wird abgewiesen.** Eine negative Stunde waere eine
    # Korrektur, und die gehoert besprochen statt stillschweigend verbucht;
    # null ist kein Eintrag, sondern ein Fehlklick.
    if (time_log.hours or 0) <= 0:
        raise HTTPException(status_code=400,
                            detail="Bitte eine Stundenzahl größer als 0 angeben.")

    # Wer eingetragen hat, kommt aus der Anmeldung — nicht aus einem
    # Textfeld (siehe `TimeLogRequest.logged_by`).
    wer = (time_log.logged_by or "").strip() or (
        f"{getattr(current_user, 'first_name', '') or ''} "
        f"{getattr(current_user, 'last_name', '') or ''}".strip()
        or getattr(current_user, "email", "") or "Innendienst")

    try:
        # Log time
        time_entry = MarginCalculator.log_time(
            db=db,
            project_id=project_id,
            hours=time_log.hours,
            logged_by=wer,
            phase=time_log.phase,
            activity_description=time_log.activity_description,
        )

        # Get updated margin
        margin = MarginCalculator.calculate_margin(db, project_id)

        return {
            "time_entry_id": time_entry.id,
            "hours_logged": time_log.hours,
            "logged_by": wer,
            "updated_margin": margin,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Time logging failed: {str(e)}")


@router.get("/{project_id}/checklist", response_model=list[ChecklistItemResponse])
def get_checklist(
    project_id: int,
    phase: int = Query(None),
    db: Session = Depends(get_db),
):
    """Get project checklist, optionally filtered by phase."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = db.query(ProjectChecklist).filter(ProjectChecklist.project_id == project_id)
    if phase:
        query = query.filter(ProjectChecklist.phase == phase)

    items = query.all()
    return items


@router.patch("/{project_id}/checklist/{item_key}")
def update_checklist_item(
    project_id: int,
    item_key: str,
    update: ChecklistItemUpdate,
    db: Session = Depends(get_db),
):
    """Mark checklist item as complete."""
    item = (
        db.query(ProjectChecklist)
        .filter(
            ProjectChecklist.project_id == project_id,
            ProjectChecklist.item_key == item_key,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    item.is_completed = update.is_completed
    if update.is_completed:
        item.completed_at = datetime.utcnow()
        item.completed_by = update.completed_by or "unknown"
    db.commit()

    return {
        "item_key": item_key,
        "is_completed": item.is_completed,
        "completed_at": item.completed_at,
        "completed_by": item.completed_by,
    }


@router.get("/{project_id}/margin", response_model=MarginResponse)
def get_margin(project_id: int, db: Session = Depends(get_db)):
    """Get real-time margin for project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    margin = MarginCalculator.calculate_margin(db, project_id)
    if "error" in margin:
        raise HTTPException(status_code=500, detail=margin["error"])

    return margin
