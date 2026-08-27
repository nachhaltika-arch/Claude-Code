"""Der QA-Scanner und die Checkliste — was vor der Abnahme geprueft wird (L-25).

**Warum eigene Datei, 23.08.2026.** Zwei Abschnitte aus `projects_content.py`
mit derselben Frage: „Ist diese Seite auslieferbar?" Der Scanner misst, die
Checkliste haelt fest, was ein Mensch entschieden hat. Sie standen 240 Zeilen
auseinander, obwohl das eine ohne das andere keinen Sinn ergibt.

**Reiner Umzug.** Kein Pfad, keine Signatur, keine Logik geaendert.
"""
import logging
from datetime import datetime

from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Project, SessionLocal, get_db
from routers.auth_router import get_current_user, require_admin, require_any_auth
from routers.projects_helfer import (_get_fernet, eigenes_projekt_pruefen,
                                     safe_json_parse)
from routers.projects_router import kunden_router, router
from services.ki_aufruf import frag_modell

logger = logging.getLogger(__name__)


# ── QA-Scanner Endpunkte ──────────────────────────────────────────────────────

@router.post("/{project_id}/qa/run")
async def run_project_qa(project_id: int, db: Session = Depends(get_db)):
    """Führt vollständigen KI-QA-Scan durch und speichert Ergebnis."""
    from services.qa_scanner import run_full_qa, ai_evaluate_qa
    import json as _json

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    # Website-URL ermitteln
    url = getattr(project, "website_url", None)
    if not url and project.lead:
        url = project.lead.website_url
    if not url:
        raise HTTPException(400, "Keine Website-URL hinterlegt")

    company = getattr(project, "customer_name", None) or \
              (project.lead.company_name if project.lead else "")
    trade = (project.lead.trade if project.lead else "") or ""

    # 1. Automatische Checks
    scan = await run_full_qa(url, company, trade)
    if "error" in scan:
        raise HTTPException(422, f"Website nicht erreichbar: {scan['error']}")

    # 2. KI-Auswertung
    ai = await ai_evaluate_qa(scan)

    # 3. Ergebnis speichern
    full_result = {**scan, "ai": ai, "checks": scan["checks"]}
    full_result.pop("html_snippet", None)  # zu groß für DB

    project.qa_result    = _json.dumps(full_result, ensure_ascii=False)
    project.qa_score     = ai.get("gesamt_score", 0)
    project.qa_golive_ok = ai.get("golive_empfehlung", False)
    project.qa_run_at    = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "score": project.qa_score,
        "golive_ok": project.qa_golive_ok,
        "result": full_result,
    }


@router.get("/{project_id}/qa/result")
def get_qa_result(project_id: int, db: Session = Depends(get_db)):
    """Gibt das zuletzt gespeicherte QA-Ergebnis zurück.
    Funktioniert egal ob qa_result als Text-JSON oder JSONB-Dict kommt.
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"status": "no_result", "message": "Projekt nicht gefunden"}
        if not project.qa_result:
            return {"status": "no_result", "message": "Noch kein QA-Scan für dieses Projekt"}

        parsed = safe_json_parse(project.qa_result, default=None)
        if parsed is None:
            return {
                "status": "parse_error",
                "message": "QA-Ergebnis konnte nicht gelesen werden",
                "score": project.qa_score,
                "run_at": str(project.qa_run_at)[:16] if project.qa_run_at else None,
            }

        return {
            "score": project.qa_score,
            "golive_ok": project.qa_golive_ok,
            "run_at": str(project.qa_run_at)[:16] if project.qa_run_at else None,
            "result": parsed,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"QA-Result unerwarteter Fehler: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/credentials")
def add_credential(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_auth),
):
    label    = (data.get("label") or "").strip()
    username = (data.get("username") or data.get("benutzername") or "").strip()
    password = (data.get("password") or data.get("passwort") or "").strip()
    url      = (data.get("url") or "").strip()
    notes    = (data.get("notes") or data.get("notizen") or "").strip()

    if not label:
        raise HTTPException(400, "Label ist Pflichtfeld")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    encrypted = ""
    if password:
        try:
            f = _get_fernet()
            encrypted = f.encrypt(password.encode()).decode()
        except RuntimeError as e:
            logger.error(f"CREDENTIALS_KEY Fehler: {e}")
            raise HTTPException(
                status_code=503,
                detail="Zugangsdaten-Safe nicht verfügbar: CREDENTIALS_KEY nicht konfiguriert. Bitte Administrator kontaktieren.",
            )
        except Exception as e:
            logger.error(f"Verschluesselung Fehler: {e}")
            raise HTTPException(500, "Verschluesselung fehlgeschlagen")

    typ = (data.get("typ") or "sonstiges").strip()
    db.execute(text("""
        INSERT INTO project_credentials
            (project_id, label, typ, username, password_encrypted, url, notes)
        VALUES
            (:pid, :label, :typ, :username, :pw, :url, :notes)
    """), {
        "pid":      project_id,
        "label":    label,
        "typ":      typ,
        "username": username,
        "pw":       encrypted,
        "url":      url,
        "notes":    notes,
    })
    db.commit()

    row = db.execute(text(
        "SELECT id, created_at FROM project_credentials "
        "WHERE project_id=:pid ORDER BY id DESC LIMIT 1"
    ), {"pid": project_id}).fetchone()

    return {
        "success":    True,
        "id":         row[0] if row else None,
        "label":      label,
        "username":   username,
        "url":        url,
        "created_at": str(row[1])[:16] if row else "",
    }


@router.get("/{project_id}/credentials")
def get_credentials(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_auth),
):
    rows = db.execute(text("""
        SELECT id, label, COALESCE(typ,'sonstiges') as typ, username, password_encrypted,
               url, notes, created_at
        FROM project_credentials
        WHERE project_id = :pid
        ORDER BY created_at ASC
    """), {"pid": project_id}).mappings().all()

    try:
        f = _get_fernet()
    except RuntimeError as e:
        logger.error(f"CREDENTIALS_KEY Fehler: {e}")
        raise HTTPException(
            status_code=503,
            detail="Zugangsdaten-Safe nicht verfügbar: CREDENTIALS_KEY nicht konfiguriert. Bitte Administrator kontaktieren.",
        )
    result = []
    for r in rows:
        decrypted = ""
        if r["password_encrypted"]:
            try:
                decrypted = f.decrypt(r["password_encrypted"].encode()).decode()
            except Exception:
                decrypted = "Entschluesselung fehlgeschlagen"
        result.append({
            "id":         r["id"],
            "label":      r["label"],
            "typ":        r["typ"] or "sonstiges",
            "username":   r["username"] or "",
            "password":   decrypted,
            "url":        r["url"] or "",
            "notes":      r["notes"] or "",
            "created_at": str(r["created_at"])[:16],
        })
    return result


@router.delete("/{project_id}/credentials/{cred_id}")
def delete_credential(
    project_id: int,
    cred_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_auth),
):
    db.execute(text("""
        DELETE FROM project_credentials
        WHERE id = :cid AND project_id = :pid
    """), {"cid": cred_id, "pid": project_id})
    db.commit()
    return {"success": True}


@router.get("/{project_id}/auftragsbestaetigung")
def download_auftragsbestaetigung(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Lädt die Auftragsbestätigung als PDF herunter (nur Admin)."""
    import os as _os
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    path = getattr(project, "auftragsbestaetigung_pdf", None)
    if not path or not _os.path.exists(path):
        raise HTTPException(404, "PDF nicht vorhanden")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename="KOMPAGNON-Auftragsbestaetigung.pdf",
    )


# ── QA-Checkliste ─────────────────────────────────────────────────────────────

@router.patch("/{project_id}/qa-checklist")
def save_qa_checklist(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    checked = data.get("checked", {})
    db.execute(
        text("UPDATE projects SET qa_checklist_json=:qj WHERE id=:id"),
        {"qj": json.dumps(checked, ensure_ascii=False), "id": project_id},
    )
    db.commit()
    return {"success": True, "checked_count": len(checked)}
