"""Briefing — Lesen, Anlegen, PDF und die KI-Vorbefuellung.

**Achtung: Dieselbe Adresse wie `routers/briefing.py`.** Siehe den Kopf dort
und `tests/test_briefing_router.py` (L-27).
"""
import json
import logging
import os  # von den uebernommenen KI-Routen gebraucht (L-27)
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db, Briefing, Lead, Project
from routers.auth_router import require_any_auth, require_innendienst

logger = logging.getLogger(__name__)

from services.ki_aufruf import frag_modell

router = APIRouter(prefix="/api/briefings", tags=["briefings"],
                   dependencies=[Depends(require_innendienst)])

# **Der Kundenweg, getrennt nach Zustaendigkeit (L-27, 22.08.2026).**
#
# `PATCH /{lead_id}/freigabe` muss ein **Kunde** erreichen — er prueft den
# Einmal-Token selbst aus dem Rumpf. Die Vorgabe oben wuerde ihn aussperren,
# und FastAPI kann eine Router-Abhaengigkeit je Route nicht aufheben.
#
# Zwei Router in **einer** Datei sind hier kein Rueckfall in den alten
# Fehler: Der bestand darin, dass zwei **Dateien** dasselbe Praefix trugen
# und nach HTTP-Verb getrennt waren — unsichtbar fuereinander. Hier stehen
# beide sichtbar nebeneinander, getrennt nach **Zustaendigkeit**, und ein
# Test verbietet jede Ueberschneidung. Dasselbe Muster fuehrt `leads.py`
# mit `router`, `public_router` und `kunden_router`.
kunden_router = APIRouter(prefix="/api/briefings", tags=["briefings-kunde"])

FLAT_FIELDS = [
    "project_id", "gewerk", "wz_code", "wz_title", "leistungen", "einzugsgebiet", "usp",
    "mitbewerber", "vorbilder", "farben", "wunschseiten", "stil",
    "logo_vorhanden", "fotos_vorhanden", "sonstige_hinweise", "status",
    "hauptziel", "aktionen", "typischer_kunde", "haeufige_anfrage",
    "funktionen_json", "seo_json",
]

# Substantive text fields used to decide whether a briefing has meaningful content.
# A briefing is considered "submitted" once 3+ of these are filled (>=10 chars after strip).
_SUBSTANTIVE_FIELDS = [
    "gewerk", "leistungen", "einzugsgebiet", "usp", "mitbewerber",
    "vorbilder", "wunschseiten", "stil", "hauptziel", "aktionen",
    "typischer_kunde", "haeufige_anfrage", "sonstige_hinweise",
]


def _is_briefing_meaningful(briefing: Briefing) -> bool:
    """True once 3+ substantive fields have non-trivial content."""
    filled = 0
    for field in _SUBSTANTIVE_FIELDS:
        val = (getattr(briefing, field, None) or "").strip()
        if len(val) >= 10:
            filled += 1
            if filled >= 3:
                return True
    return False


def _maybe_mark_submitted(db: Session, briefing: Briefing, lead_id: int) -> None:
    """If the briefing now has meaningful content, mark its project as briefing-submitted
    and (if still in phase_1) transition to phase_2 + trigger welcome automations."""
    if not _is_briefing_meaningful(briefing):
        return

    project = db.query(Project).filter(Project.lead_id == lead_id).first()
    if not project:
        return  # No project yet (kampagne-lead pre-purchase) — skip
    if project.has_briefing:
        return  # Already marked

    now = datetime.utcnow()
    project.has_briefing = True
    if not project.briefing_submitted_at:
        project.briefing_submitted_at = now
    if briefing.status != "eingereicht":
        briefing.status = "eingereicht"

    triggered_transition = False
    if project.status == "phase_1":
        project.status = "phase_2"
        if hasattr(project, "current_phase"):
            project.current_phase = 2
        triggered_transition = True

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Briefing-Submit commit fehlgeschlagen (lead {lead_id}): {e}")
        return

    if triggered_transition:
        try:
            from automations.scheduler import get_scheduler
            scheduler = get_scheduler()
            if scheduler:
                scheduler.trigger_phase_change(project.id, "phase_2")
        except Exception as e:
            logger.warning(f"Phase-2-Trigger fehlgeschlagen für Project {project.id}: {e}")

    logger.info(
        f"Briefing #{briefing.id} (Lead {lead_id}) als eingereicht markiert; "
        f"Project {project.id} {'→ phase_2 (Auto-Trigger)' if triggered_transition else '(unverändert phase ' + str(project.status) + ')'}"
    )


class BriefingBody(BaseModel):
    project_id: Optional[int] = None
    gewerk: Optional[str] = None
    wz_code: Optional[str] = None
    wz_title: Optional[str] = None
    leistungen: Optional[str] = None
    einzugsgebiet: Optional[str] = None
    usp: Optional[str] = None
    mitbewerber: Optional[str] = None
    vorbilder: Optional[str] = None
    farben: Optional[str] = None
    wunschseiten: Optional[str] = None
    stil: Optional[str] = None
    logo_vorhanden: Optional[bool] = None
    fotos_vorhanden: Optional[bool] = None
    sonstige_hinweise: Optional[str] = None
    status: Optional[str] = None
    hauptziel: Optional[str] = None
    aktionen: Optional[str] = None
    typischer_kunde: Optional[str] = None
    haeufige_anfrage: Optional[str] = None
    funktionen_json: Optional[str] = None
    seo_json: Optional[str] = None


def _serialize(b: Briefing) -> dict:
    def _parse(val):
        if not val:
            return {}
        if isinstance(val, dict):
            return val
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return {}

    return {
        "id":                b.id,
        "lead_id":           b.lead_id,
        # Legacy JSON sections
        "projektrahmen":     _parse(getattr(b, "projektrahmen",  None)),
        "positionierung":    _parse(getattr(b, "positionierung", None)),
        "zielgruppe":        _parse(getattr(b, "zielgruppe",     None)),
        "wettbewerb":        _parse(getattr(b, "wettbewerb",     None)),
        "inhalte":           _parse(getattr(b, "inhalte",        None)),
        "funktionen":        _parse(getattr(b, "funktionen",     None)),
        "branding":          _parse(getattr(b, "branding",       None)),
        "struktur":          _parse(getattr(b, "struktur",       None)),
        "hosting":           _parse(getattr(b, "hosting",        None)),
        "seo":               _parse(getattr(b, "seo",            None)),
        "projektplan":       _parse(getattr(b, "projektplan",    None)),
        "freigaben":         _parse(getattr(b, "freigaben",      None)),
        # Flat fields
        "project_id":        getattr(b, "project_id",        None),
        "gewerk":            getattr(b, "gewerk",            "") or "",
        "wz_code":           getattr(b, "wz_code",           "") or "",
        "wz_title":          getattr(b, "wz_title",          "") or "",
        "leistungen":        getattr(b, "leistungen",        "") or "",
        "einzugsgebiet":     getattr(b, "einzugsgebiet",     "") or "",
        "usp":               getattr(b, "usp",               "") or "",
        "mitbewerber":       getattr(b, "mitbewerber",       "") or "",
        "vorbilder":         getattr(b, "vorbilder",         "") or "",
        "farben":            getattr(b, "farben",            "") or "",
        "wunschseiten":      getattr(b, "wunschseiten",      "") or "",
        "stil":              getattr(b, "stil",              "") or "",
        "logo_vorhanden":    bool(getattr(b, "logo_vorhanden",  False)),
        "fotos_vorhanden":   bool(getattr(b, "fotos_vorhanden", False)),
        "sonstige_hinweise": getattr(b, "sonstige_hinweise", "") or "",
        "funktionen_json":   getattr(b, "funktionen_json",   None),
        "seo_json":          getattr(b, "seo_json",          None),
        "status":            getattr(b, "status",            "entwurf") or "entwurf",
        "hauptziel":         getattr(b, "hauptziel",         "") or "",
        "aktionen":          getattr(b, "aktionen",          "") or "",
        "typischer_kunde":   getattr(b, "typischer_kunde",   "") or "",
        "haeufige_anfrage":  getattr(b, "haeufige_anfrage",  "") or "",
        "created_at":        str(b.created_at)[:16] if b.created_at else "",
        "updated_at":        str(b.updated_at)[:16] if b.updated_at else "",
    }


@router.get("/{lead_id}")
def get_briefing(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Load briefing for a lead; auto-creates if none exists."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        briefing = Briefing(lead_id=lead_id, status="entwurf")
        db.add(briefing)
        try:
            db.commit()
            db.refresh(briefing)
        except Exception as e:
            db.rollback()
            logger.error(f"Briefing auto-create failed: {e}")
            raise HTTPException(422, f"Erstellen fehlgeschlagen: {str(e)[:200]}")
    return _serialize(briefing)


@router.post("/{lead_id}")
def create_briefing(
    lead_id: int,
    body: BriefingBody,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Create or fully overwrite the flat briefing fields for a lead."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        briefing = Briefing(lead_id=lead_id)
        db.add(briefing)

    data = body.model_dump(exclude_unset=False)
    for field in FLAT_FIELDS:
        val = data.get(field)
        if val is not None:
            setattr(briefing, field, val)

    briefing.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(briefing)
    except Exception as e:
        db.rollback()
        logger.error(f"Briefing POST commit failed: {e}")
        raise HTTPException(422, f"Speichern fehlgeschlagen: {str(e)[:200]}")

    _maybe_mark_submitted(db, briefing, lead_id)
    return _serialize(briefing)


@router.get("/{lead_id}/pdf")
def briefing_pdf(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generate and return briefing as PDF (application/pdf)."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    company_name = (lead.display_name or lead.company_name) if lead else f"Lead #{lead_id}"

    from services.briefing_pdf import generate_briefing_pdf
    pdf_bytes = generate_briefing_pdf(briefing, company_name)

    filename = f"briefing-{lead_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.put("/{lead_id}")
def update_briefing(
    lead_id: int,
    body: BriefingBody,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Partial update — only fields present in the request body are changed."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    data = body.model_dump(exclude_unset=True)
    for field in FLAT_FIELDS:
        if field in data:
            setattr(briefing, field, data[field])

    briefing.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(briefing)
    except Exception as e:
        db.rollback()
        logger.error(f"Briefing PUT commit failed: {e}")
        raise HTTPException(422, f"Speichern fehlgeschlagen: {str(e)[:200]}")

    _maybe_mark_submitted(db, briefing, lead_id)
    return _serialize(briefing)




@router.get("/{lead_id}/assets-status")
def get_assets_status(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Gibt automatisch erkannte Asset-Informationen zurück."""
    lead     = db.query(Lead).filter(Lead.id == lead_id).first()
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    logo_url   = lead.brand_logo_url or ""
    logo_found = bool(logo_url)

    images_found = []
    try:
        rows = db.execute(
            text("SELECT images FROM website_content_cache WHERE customer_id=:id LIMIT 5"),
            {"id": lead_id}
        ).fetchall()
        for row in rows:
            imgs = json.loads(row[0] or "[]")
            for img in (imgs if isinstance(imgs, list) else []):
                src = img.get("src", "") if isinstance(img, dict) else str(img)
                if src and src.startswith("http"):
                    images_found.append(src)
    except Exception:
        pass

    photos_likely    = len(images_found) > 3
    logo_vorhanden   = bool(briefing.logo_vorhanden)  if briefing else logo_found
    fotos_vorhanden  = bool(briefing.fotos_vorhanden) if briefing else photos_likely

    return {
        "logo": {
            "vorhanden":    logo_vorhanden,
            "url":          logo_url,
            "auto_erkannt": logo_found,
            "quelle":       "Brand Scan" if logo_found else None,
        },
        "fotos": {
            "vorhanden":    fotos_vorhanden,
            "anzahl":       len(images_found),
            "vorschau":     images_found[:3],
            "auto_erkannt": True,
            "einschaetzung": "Fotos gefunden" if photos_likely else "Wenig Bilder — Fotograf empfohlen",
        },
        "ci_handbuch": {
            "vorhanden":  False,
            "dateiname":  lead.brand_pdf_filename or None,
        },
    }


@router.post("/{lead_id}/assets-save")
def save_assets(
    lead_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        briefing = Briefing(lead_id=lead_id)
        db.add(briefing)

    briefing.logo_vorhanden  = bool(body.get("logo_vorhanden"))
    briefing.fotos_vorhanden = bool(body.get("fotos_vorhanden"))
    if "sonstige_hinweise" in body:
        briefing.sonstige_hinweise = body["sonstige_hinweise"]

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(422, str(e)[:200])
    return {"saved": True}








# ── Aus `routers/briefing.py` uebernommen, 22.08.2026 (L-27) ──────────
#
# Diese vier Routen lagen in einer **zweiten** Datei mit demselben Praefix,
# getrennt nach HTTP-Verb: PATCH und die beiden Analysen drueben,
# GET/POST/PUT hier. So gewachsen, nicht entworfen — und wer in einer Datei
# eine Route ergaenzt hatte, die es in der anderen schon gab, verdeckte sie
# **still**: Es gewinnt der zuerst eingebundene Router, und keine Meldung
# sagt es.
#
# Es war nicht theoretisch. Beide Dateien fuehrten ein `_serialize`, und die
# Fassungen waren auseinandergelaufen — die drueben gab **22 Felder
# weniger** zurueck (kein Gewerk, keine Leistungen, kein USP, keine Farben).
# Wer ueber PATCH speicherte, bekam ein halbes Briefing. Schaden richtete das
# keinen an, weil `BriefingTab.jsx` die Antwort gar nicht auswertet — es ging
# gut, weil niemand hinsah, nicht weil es richtig war.
#
# `update_briefing` hiess drueben genauso wie das PUT hier; sie heisst jetzt
# `briefing_teilweise_aendern` — nach dem, was sie tut.


@router.patch('/{lead_id}', dependencies=[Depends(require_innendienst)])
def briefing_teilweise_aendern(lead_id: int, data: dict, db: Session = Depends(get_db)):
    """Update one or more briefing sections."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        briefing = Briefing(lead_id=lead_id)
        db.add(briefing)

    allowed = ['projektrahmen', 'positionierung', 'zielgruppe', 'wettbewerb', 'inhalte',
                'funktionen', 'branding', 'struktur', 'hosting', 'seo', 'projektplan', 'freigaben', 'status']
    for key in allowed:
        if key in data:
            if isinstance(data[key], dict):
                setattr(briefing, key, json.dumps(data[key], ensure_ascii=False))
            else:
                setattr(briefing, key, data[key])

    briefing.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(briefing)
    except Exception as e:
        db.rollback()
        raise HTTPException(422, f"Speichern fehlgeschlagen: {str(e)[:200]}")

    try:
        # Stand hier als `from routers.briefings import …` — ein Import aus
        # der eigenen Datei, uebriggeblieben aus der Zeit, als diese Route in
        # `briefing.py` lag (L-27). Er funktionierte, aber er beschrieb eine
        # Trennung, die es nicht mehr gibt.
        _maybe_mark_submitted(db, briefing, lead_id)
    except Exception as e:
        logger.warning(f"Briefing-Submit-Hook (PATCH) fehlgeschlagen für Lead {lead_id}: {e}")
    return _serialize(briefing)


@kunden_router.patch('/{lead_id}/freigabe')
def set_freigabe(lead_id: int, data: dict, db: Session = Depends(get_db)):
    """Only customers (role=kunde) can grant approvals. Cannot be revoked."""
    from routers.auth_router import require_kunde, get_current_user, oauth2_scheme
    from fastapi import Security
    # Manual auth check for kunde role
    from routers.auth_router import decode_token
    from database import User
    token = data.get('_token', '')
    if not token:
        raise HTTPException(403, "Nicht authentifiziert")
    try:
        payload = decode_token(token)
        current_user = db.query(User).filter(User.id == payload.get("user_id")).first()
        if not current_user or current_user.role != 'kunde':
            raise HTTPException(403, "Nur Kunden können Freigaben erteilen")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(403, "Authentifizierung fehlgeschlagen")

    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        raise HTTPException(404, "Briefing nicht gefunden")

    key = data.get('key')
    if not key:
        raise HTTPException(400, "Freigabe-Key fehlt")

    current = json.loads(briefing.freigaben) if briefing.freigaben and briefing.freigaben != '{}' else {}
    existing = current.get(key, {})

    if existing.get('datum'):
        raise HTTPException(400, "Freigabe bereits erteilt und kann nicht widerrufen werden")

    updated = {
        **current,
        key: {
            'datum': datetime.utcnow().strftime('%d.%m.%Y'),
            'uhrzeit': datetime.utcnow().strftime('%H:%M'),
            'durch': current_user.email or f'{current_user.first_name} {current_user.last_name}',
            'user_id': current_user.id,
        }
    }

    briefing.freigaben = json.dumps(updated, ensure_ascii=False)
    briefing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(briefing)
    return _serialize(briefing)




