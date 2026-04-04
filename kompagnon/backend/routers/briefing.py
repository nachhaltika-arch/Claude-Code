from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Briefing, Lead
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/briefings', tags=['briefings'])


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


@router.post('/{lead_id}/zielgruppenanalyse')
async def zielgruppenanalyse(lead_id: int, db: Session = Depends(get_db)):
    """AI-powered target audience analysis based on lead trade + city."""
    from anthropic import Anthropic

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    trade = lead.trade or 'Handwerk'
    city = lead.city or 'Deutschland'
    company = lead.display_name or lead.company_name or ''

    prompt = f"""Du bist ein erfahrener Marketing-Stratege für Handwerksbetriebe in Deutschland.

Analysiere die Zielgruppe für diesen Betrieb:
- Unternehmen: {company}
- Branche/Gewerk: {trade}
- Standort: {city}

Erstelle eine strukturierte Zielgruppenanalyse mit:
1. Primäre Zielgruppe (wer kauft hauptsächlich)
2. Sekundäre Zielgruppe
3. Demografische Merkmale (Alter, Geschlecht, Einkommen)
4. Psychografische Merkmale (Werte, Bedürfnisse, Schmerzpunkte)
5. Kaufmotivation (Warum beauftragen sie einen {trade}?)
6. Entscheidungskriterien (Was ist bei der Auswahl wichtig?)
7. Bevorzugte Kommunikationskanäle
8. Empfehlung für die Website-Ansprache

Schreibe kompakt und praxisnah. Maximal 400 Wörter. Auf Deutsch."""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), max_retries=0, timeout=60.0)
        response = client.messages.create(
            model='claude-sonnet-4-6', max_tokens=1000,
            messages=[{'role': 'user', 'content': prompt}],
        )
        analyse = response.content[0].text

        briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
        if not briefing:
            briefing = Briefing(lead_id=lead_id)
            db.add(briefing)

        current = json.loads(briefing.zielgruppe) if briefing.zielgruppe and briefing.zielgruppe != '{}' else {}
        updated = {**current, 'analyse': analyse, 'analyse_datum': datetime.utcnow().strftime('%d.%m.%Y %H:%M')}
        briefing.zielgruppe = json.dumps(updated, ensure_ascii=False)
        briefing.updated_at = datetime.utcnow()
        db.commit()

        return {'analyse': analyse, 'datum': updated['analyse_datum']}
    except Exception as e:
        logger.error(f'Zielgruppenanalyse Fehler: {e}')
        raise HTTPException(500, f'Analyse fehlgeschlagen: {str(e)}')


@router.post('/{lead_id}/wettbewerbsanalyse')
async def wettbewerbsanalyse(lead_id: int, db: Session = Depends(get_db)):
    """AI-powered competitor analysis based on lead trade + city + region."""
    from anthropic import Anthropic

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    trade = lead.trade or 'Handwerk'
    city = lead.city or 'Deutschland'
    postal_code = lead.postal_code or ''
    company = lead.display_name or lead.company_name or ''
    region = f"{city} ({postal_code})" if postal_code else city

    prompt = f"""Du bist ein erfahrener Markt- und Wettbewerbsanalyst für Handwerksbetriebe in Deutschland.

Erstelle eine Wettbewerbsanalyse für:
- Unternehmen: {company}
- Branche/Gewerk: {trade}
- Region: {region} und 50 km Umkreis

Analysiere:
1. Marktübersicht — Typische Anzahl Wettbewerber, Marktstruktur
2. Typische Wettbewerber-Profile — Wie präsentieren sie sich online?
3. Online-Präsenz der Wettbewerber — Typischer Stand der Websites, Stärken, Schwächen
4. Differenzierungspotenzial — Wo kann sich {company} abheben? Welche Lücken gibt es?
5. Empfehlungen für die Website — Was muss sie zeigen? Welche Inhalte heben ab?
6. Lokale SEO Chancen — Wichtige Suchbegriffe für {trade} in {city}, Google Business Tipps

Schreibe kompakt und praxisnah. Maximal 500 Wörter. Auf Deutsch."""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), max_retries=0, timeout=60.0)
        response = client.messages.create(
            model='claude-sonnet-4-6', max_tokens=1200,
            messages=[{'role': 'user', 'content': prompt}],
        )
        analyse = response.content[0].text

        briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
        if not briefing:
            briefing = Briefing(lead_id=lead_id)
            db.add(briefing)

        current = json.loads(briefing.wettbewerb) if briefing.wettbewerb and briefing.wettbewerb != '{}' else {}
        updated = {**current, 'analyse': analyse, 'analyse_datum': datetime.utcnow().strftime('%d.%m.%Y %H:%M'), 'region': region}
        briefing.wettbewerb = json.dumps(updated, ensure_ascii=False)
        briefing.updated_at = datetime.utcnow()
        db.commit()

        return {'analyse': analyse, 'region': region, 'datum': updated['analyse_datum']}
    except Exception as e:
        logger.error(f'Wettbewerbsanalyse Fehler: {e}')
        raise HTTPException(500, f'Analyse fehlgeschlagen: {str(e)}')
