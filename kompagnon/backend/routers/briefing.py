from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Briefing
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/briefings', tags=['briefings'])


@router.get('/{lead_id}')
def get_briefing(lead_id: int, db: Session = Depends(get_db)):
    """Get or auto-create briefing for a lead."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        briefing = Briefing(lead_id=lead_id, status='offen')
        db.add(briefing)
        db.commit()
        db.refresh(briefing)
    return _serialize(briefing)


@router.patch('/{lead_id}')
def update_briefing(lead_id: int, data: dict, db: Session = Depends(get_db)):
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
    db.commit()
    db.refresh(briefing)
    return _serialize(briefing)


@router.patch('/{lead_id}/freigabe')
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


def _serialize(b):
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
        'id': b.id,
        'lead_id': b.lead_id,
        'projektrahmen': _parse(b.projektrahmen),
        'positionierung': _parse(b.positionierung),
        'zielgruppe': _parse(b.zielgruppe),
        'wettbewerb': _parse(b.wettbewerb),
        'inhalte': _parse(b.inhalte),
        'funktionen': _parse(b.funktionen),
        'branding': _parse(b.branding),
        'struktur': _parse(b.struktur),
        'hosting': _parse(b.hosting),
        'seo': _parse(b.seo),
        'projektplan': _parse(b.projektplan),
        'freigaben': _parse(b.freigaben),
        'status': b.status or 'offen',
        'updated_at': str(b.updated_at)[:16] if b.updated_at else '',
    }
