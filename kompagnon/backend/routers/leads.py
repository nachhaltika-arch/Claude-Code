"""
Lead Management API routes.
POST /api/leads/ - Create lead
GET /api/leads/ - List all leads
POST /api/leads/{id}/analyze - Run lead analyst agent
POST /api/leads/{id}/convert - Convert to project
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from database import Lead, Project, AuditResult, get_db, SessionLocal
from routers.auth_router import (
    INNENDIENST, require_admin, require_any_auth, require_innendienst,
    verlangt_recht,
    get_current_user,
)
from services import betriebsname, lead_quellen
from seed_checklists import create_project_checklists
from agents.lead_analyst import LeadAnalystAgent
from services.base_urls import self_base_url
from services.pdf_generator import branche_fuer_protokoll
from services.audit_pagespeed import api_key as pagespeed_api_key
import asyncio
import csv
import httpx
import io
import json
import logging
import os
import uuid
from services.ratenbegrenzung import lead_grenzen
from services.lead_verlauf import verlauf_bauen


logger = logging.getLogger(__name__)

# Vorgabe: geschlossen. Bis zum 14.08.2026 hing die Anmeldung an der einzelnen
# Route — 31 von 42 hatten keine, produktiv und ohne Anmeldung erreichbar:
# der komplette Leadbestand als Liste und als CSV, das Ändern und Löschen
# einzelner Leads samt zugehöriger Daten, und Läufe, die Geld kosten
# (Anreicherung, PageSpeed, Screenshot, Kaltakquise).
#
# Eine Erlaubnisliste je Route ist die falsche Richtung: Wer eine Route
# hinzufügt und die Abhängigkeit vergisst, öffnet sie. Deshalb hängt die
# Anmeldung jetzt am Router, und was öffentlich sein muss, steht unten
# ausdrücklich im `public_router`.
# Der Bestand ist Innendienst. Angemeldet zu sein reicht nicht — sonst
# bekommt ein Kunde die Liste aller Betriebe (Befund vom 17.08.2026).
router = APIRouter(prefix="/api/leads", tags=["leads"],
                   dependencies=[Depends(require_innendienst)])

# Ausdrücklich ohne Anmeldung — jede dieser Routen trägt ihre eigene Prüfung:
# das Anlegen aus dem Formular der Landingpage und der Kundenzugang über einen
# Einmal-Token aus der E-Mail.
public_router = APIRouter(prefix="/api/leads", tags=["leads-public"])

# Was ein Kunde braucht: den eigenen Betrieb, den das Kundenportal anzeigt
# (`KundenPortal.jsx`). Jede Route hier prüft selbst, ob die Zeile ihm gehört.
kunden_router = APIRouter(prefix="/api/leads", tags=["leads-kunde"],
                          dependencies=[Depends(require_any_auth)])





class LeadCreate(BaseModel):
    company_name: str
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    website_url: str = None
    city: str = ""
    trade: str = ""
    lead_source: str = None
    notes: str = None


class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    website_url: Optional[str] = None
    city: Optional[str] = None
    trade: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    lead_source: Optional[str] = None
    analysis_score: Optional[int] = None
    geo_score: Optional[int] = None
    display_name: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    postal_code: Optional[str] = None
    legal_form: Optional[str] = None
    vat_id: Optional[str] = None
    register_number: Optional[str] = None
    register_court: Optional[str] = None
    ceo_first_name: Optional[str] = None
    ceo_last_name: Optional[str] = None
    wz_code: Optional[str] = None
    wz_title: Optional[str] = None
    inspiration_url_1: Optional[str] = None
    inspiration_url_2: Optional[str] = None
    inspiration_url_3: Optional[str] = None


class LeadResponse(BaseModel):
    id: int
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website_url: Optional[str] = None
    city: Optional[str] = None
    trade: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    wz_code: Optional[str] = None
    wz_title: Optional[str] = None
    lead_source: Optional[str] = None
    status: str = "new"
    analysis_score: Optional[int] = None
    geo_score: Optional[int] = None
    pagespeed_mobile: Optional[int] = None
    pagespeed_desktop: Optional[int] = None
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        from_attributes = True


class LeadConvertRequest(BaseModel):
    fixed_price: float = 2000.0
    hourly_rate: float = 45.0
    ai_tool_costs: float = 50.0
    assigned_person: str = "KOMPAGNON-Team"


@router.post("/", dependencies=[Depends(verlangt_recht("create_leads"))])
def create_lead(lead: LeadCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            INSERT INTO leads (
                company_name, contact_name, phone, email,
                website_url, city, trade, lead_source, notes,
                status, analysis_score, geo_score,
                created_at, updated_at
            ) VALUES (
                :company_name, :contact_name, :phone, :email,
                :website_url, :city, :trade, :lead_source, :notes,
                'new', 0, 0,
                NOW(), NOW()
            ) RETURNING id, company_name, contact_name, phone, email,
                website_url, city, trade, lead_source, status,
                analysis_score, geo_score, created_at, updated_at
        """), {
            'company_name': lead.company_name or '',
            'contact_name': lead.contact_name or '',
            'phone': lead.phone or '',
            'email': lead.email or '',
            'website_url': lead.website_url or '',
            'city': lead.city or '',
            'trade': lead.trade or '',
            'lead_source': lead.lead_source or '',
            'notes': lead.notes or '',
        })
        db.commit()
        row = result.fetchone()
        lead_id = row[0]

        AUTO_SEQUENCE_SOURCES = {
            "stripe_checkout",
            "landing_audit",
            "landing_page",
            "llm_landing",
            "postkarte",
            "webhook_facebook",
            "webhook_linkedin",
            "webhook_google",
        }

        if lead.email and (lead.lead_source or '') in AUTO_SEQUENCE_SOURCES:
            try:
                from services.sequence_runner import start_sequence_for_lead
                import threading
                threading.Thread(
                    target=start_sequence_for_lead,
                    args=(lead_id,),
                    daemon=True,
                ).start()
                import logging as _log
                _log.getLogger('leads').info(
                    f"Auto-Sequenz gestartet für Lead {lead_id} "
                    f"(Quelle: {lead.lead_source})"
                )
            except Exception as e:
                import logging as _log
                _log.getLogger('leads').warning(f"Auto-Sequenz Fehler: {e}")

        if lead.website_url:
            from services.lead_enrichment import enrich_lead_sync
            background_tasks.add_task(enrich_lead_sync, lead_id)

        # Google Business Profile check (non-blocking)
        def _gbp_check(lid, company, city):
            from services.google_business import check_google_business
            try:
                gbp = asyncio.run(check_google_business(company, city))
                s = SessionLocal()
                s.execute(text(
                    "UPDATE leads SET gbp_place_id=:pid, gbp_claimed=:c, "
                    "gbp_rating=:r, gbp_ratings_total=:rt WHERE id=:id"
                ), {"pid": gbp["place_id"], "c": gbp["claimed"],
                    "r": gbp["rating"], "rt": gbp["ratings_total"], "id": lid})
                s.commit()
                s.close()
            except Exception:
                pass
        background_tasks.add_task(_gbp_check, lead_id,
                                  lead.company_name or '', lead.city or '')

        return {
            'id': row[0],
            'company_name': row[1] or '',
            'contact_name': row[2] or '',
            'phone': row[3] or '',
            'email': row[4] or '',
            'website_url': row[5] or '',
            'city': row[6] or '',
            'trade': row[7] or '',
            'lead_source': row[8] or '',
            'datenherkunft': lead_quellen.herkunft_fuer(row[8]),
            'rechtsgrundlage': lead_quellen.rechtsgrundlage_fuer(row[8]),
            'status': row[9] or 'new',
            'analysis_score': row[10] or 0,
            'geo_score': row[11] or 0,
            'created_at': str(row[12])[:19] if row[12] else '',
            'updated_at': str(row[13])[:19] if row[13] else '',
        }
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger('leads').error(f'Lead create error: {type(e).__name__}: {e}')
        raise HTTPException(status_code=500, detail=f'Lead konnte nicht angelegt werden: {str(e)}')


@router.get("/{lead_id}/verlauf")
def lead_verlauf(lead_id: int, limit: int = Query(20, ge=1, le=50),
                 db: Session = Depends(get_db)):
    """Was bei diesem Betrieb zuletzt geschah — aus allen Quellen (L-82).

    Die Ereignisse liegen in fuenf Tabellen, und keine Stelle fuehrte sie
    zusammen; auf der Betriebsseite hiess das drei Reiter fuer eine Frage, die
    man beim Anruf in einer Sekunde beantwortet haben will.

    Ein unbekannter Betrieb ist **404**, kein leerer Verlauf: Sonst sieht ein
    Tippfehler in der Kennung aus wie ein Betrieb, bei dem noch nichts war.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Betrieb nicht gefunden")

    return verlauf_bauen(db, lead, limit=limit)


@router.get("/quellen/wirkung")
def kanalwirkung(db: Session = Depends(get_db)):
    """Welcher Kanal bringt Kunden? (L-84)

    Die Herkunft steht seit langem in `leads.lead_source`, und
    `services/lead_quellen.py` fuehrt dazu einen gepflegten Wortschatz. Was
    fehlte, ist die Frage, fuer die man das alles erhebt.

    **Gerechnet wird auf `lifecycle_phase`, nicht auf `status`.** Der Status
    beantwortete zwei Fragen gleichzeitig, und zwei Stellen uebersahen dabei
    `customer` — ein Betrieb, den jemand von Hand auf „Kunde" gesetzt hatte,
    zaehlte in **keiner** Kennzahl mit (L-26). Eine Zahl, die auf der falschen
    Spalte rechnet, ist schlimmer als keine.

    **Unbekannte Quellen werden ausgewiesen, nicht weggelassen.** Ein Wert,
    den der Wortschatz nicht kennt, ist der interessanteste Fall: Entweder
    schreibt ihn jemand ungepflegt — oder der Wortschatz hinkt hinterher.
    Dasselbe gilt fuer Betriebe ohne Herkunft: Sie stillschweigend
    auszulassen hiesse, die Summe der Kanaele als Gesamtbestand zu lesen.
    """
    from services import lead_quellen

    zeilen = db.execute(text("""
        SELECT lead_source,
               COUNT(*) AS betriebe,
               COUNT(*) FILTER (WHERE lifecycle_phase = 'kunde') AS kunden
        FROM leads
        GROUP BY lead_source
    """)).fetchall()

    kanaele, ohne_herkunft, gesamt = [], 0, 0
    for quelle, betriebe, kunden in zeilen:
        gesamt += betriebe
        if not (quelle or "").strip():
            ohne_herkunft += betriebe
            continue

        eintrag = lead_quellen.QUELLEN.get(lead_quellen.normalisiere(quelle) or quelle)
        kanaele.append({
            "quelle":   quelle,
            "name":     (eintrag or {}).get("name") or quelle,
            "herkunft": (eintrag or {}).get("herkunft"),
            "bekannt":  eintrag is not None,
            "betriebe": betriebe,
            "kunden":   kunden,
            "quote":    round(kunden / betriebe, 2) if betriebe else None,
        })

    # Der wirksamste Kanal zuerst; bei gleicher Quote der groessere Bestand.
    kanaele.sort(key=lambda k: (-(k["quote"] or 0), -k["betriebe"]))

    return {
        "kanaele": kanaele,
        "ohne_herkunft": ohne_herkunft,
        "betriebe_gesamt": gesamt,
    }


@router.get("/")
def list_leads(
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    """List all leads with latest audit level, optionally filtered by status."""
    import logging as _log
    _logger = _log.getLogger('leads')

    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    leads = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for lead in leads:
        try:
            result.append({
                'id': lead.id,
                'company_name': lead.company_name or '',
                'display_name': lead.display_name or '',
                'contact_name': lead.contact_name or '',
                'phone': lead.phone or '',
                'email': lead.email or '',
                'website_url': lead.website_url or '',
                'city': lead.city or '',
                'trade': lead.trade or '',
                'status': lead.status or 'new',
                'lifecycle_phase': lead.lifecycle_phase,
                'lead_source': lead.lead_source or '',
                'analysis_score': lead.analysis_score or 0,
                'geo_score': lead.geo_score or 0,
                'notes': lead.notes or '',
                'website_screenshot': None,
                'street': lead.street or '',
                'house_number': lead.house_number or '',
                'postal_code': lead.postal_code or '',
                'legal_form': lead.legal_form or '',
                'vat_id': lead.vat_id or '',
                'register_number': lead.register_number or '',
                'register_court': lead.register_court or '',
                'ceo_first_name': lead.ceo_first_name or '',
                'ceo_last_name': lead.ceo_last_name or '',
                'geschaeftsfuehrer': lead.geschaeftsfuehrer or '',
                'created_at': str(lead.created_at)[:10] if lead.created_at else '',
                'updated_at': str(lead.updated_at)[:10] if lead.updated_at else '',
            })
        except Exception as e:
            _logger.error(f'Lead {lead.id} Fehler: {e}')
            continue

    return result


@router.get("/customers")
def get_customers(db: Session = Depends(get_db)):
    """Get all paying customers (won leads, stripe, etc.) with audit + project data."""
    from sqlalchemy import or_
    from database import User, Project

    customers = db.query(Lead).filter(
        or_(Lead.status == "won", Lead.lead_source == "stripe_checkout", Lead.lead_source == "llm_landing")
    ).order_by(Lead.created_at.desc()).all()

    result = []
    for lead in customers:
        latest_audit = db.query(AuditResult).filter(
            AuditResult.lead_id == lead.id, AuditResult.status == "completed"
        ).order_by(AuditResult.created_at.desc()).first()
        project = db.query(Project).filter(Project.lead_id == lead.id).order_by(Project.created_at.desc()).first()
        user = db.query(User).filter(User.lead_id == lead.id).first()
        result.append({
            "id": lead.id, "company_name": lead.company_name, "contact_name": lead.contact_name,
            "email": lead.email, "phone": lead.phone, "website_url": lead.website_url,
            "city": lead.city, "trade": lead.trade, "status": lead.status, "lead_source": lead.lead_source,
            "created_at": str(lead.created_at)[:10] if lead.created_at else "",
            "website_screenshot": f"data:image/jpeg;base64,{lead.website_screenshot}" if getattr(lead, 'website_screenshot', None) else None,
            "notes": lead.notes,
            "audit_score": latest_audit.total_score if latest_audit else None,
            "audit_level": latest_audit.level if latest_audit else None,
            "last_audit_date": str(latest_audit.created_at)[:10] if latest_audit else None,
            "project_status": project.status if project else None,
            "project_id": project.id if project else None,
            "has_account": user is not None, "user_id": user.id if user else None,
            'gbp_claimed':       getattr(lead, 'gbp_claimed', False) or False,
            'gbp_rating':        getattr(lead, 'gbp_rating', None),
            'gbp_ratings_total': getattr(lead, 'gbp_ratings_total', None),
            'gbp_place_id':      getattr(lead, 'gbp_place_id', None),
        })
    return result
















@router.post("/enrich/all")
async def enrich_all_leads(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Batch-enrich all leads with score=0. Runs in background."""
    from services.lead_enrichment import enrich_all_pending

    def _run():
        _db = SessionLocal()
        try:
            asyncio.run(enrich_all_pending(_db))
        finally:
            _db.close()

    background_tasks.add_task(_run)
    return {"message": "Anreicherung gestartet", "status": "processing"}


#: So lang sind `utm_source`, `utm_medium` und `utm_campaign` in der Tabelle.
UTM_MAX = 200


def _herkunft_aus_anzeige(daten: dict) -> dict:
    """Die UTM-Angaben aus dem Formular — begrenzt entgegengenommen (L-86).

    **Der Befund.** Bis zum 22.08.2026 uebernahm dieser Weg `website_url`,
    `email` und `lead_source`, und sonst nichts. Wer ueber eine Anzeige mit
    `?utm_source=google` kam und das Formular ausfuellte, verlor seine
    Herkunft im Moment des Absendens — und die Kanalauswertung (L-84) konnte
    bezahlte Kanaele darum nie ausweisen.

    Die Werte kommen **ohne Anmeldung** aus einem Widget auf fremden Seiten,
    und `data` ist ein rohes `dict`: Was keine Zeichenkette ist, wird nicht
    uebernommen, und was zu lang ist, wird gekuerzt statt die Anlage
    scheitern zu lassen. Gespeichert wird roh — ausgewertet oder in HTML
    gesetzt wird hier nichts.

    Fehlt eine Angabe, bleibt das Feld leer. Eine geratene Herkunft waere
    schlimmer als eine fehlende: Auf ihr wuerde gerechnet.
    """
    herkunft = {}
    for feld in ("utm_source", "utm_medium", "utm_campaign"):
        wert = daten.get(feld)
        if isinstance(wert, str) and wert.strip():
            herkunft[feld] = wert.strip()[:UTM_MAX]
    return herkunft


# ── Public lead creation (no auth — used by landing page audit) ──

@public_router.post("/public")
async def create_public_lead(
    data: dict,
    db: Session = Depends(get_db),
    _grenzen=Depends(lead_grenzen),
):
    """Public endpoint for landing page audit — creates lead without login."""
    website_url = data.get('website_url', '').strip()
    email_addr = data.get('email', '').strip()
    if not website_url:
        raise HTTPException(400, "Website-URL fehlt")
    if not website_url.startswith('http'):
        website_url = 'https://' + website_url

    domain = website_url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    from sqlalchemy import or_
    existing = db.query(Lead).filter(or_(Lead.website_url.ilike(f'%{domain}%'))).first()
    if existing:
        if email_addr and not existing.email:
            existing.email = email_addr
            db.commit()
        return {'id': existing.id}

    lead = Lead(website_url=website_url, email=email_addr, company_name=domain,
                status='new', lead_source=data.get('lead_source', 'landing_audit'),
                **_herkunft_aus_anzeige(data))
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return {'id': lead.id}


# ── Portal routes (public, no auth) ──────────────────────

@public_router.get("/portal/{token}")
def get_portal_data(token: str, db: Session = Depends(get_db)):
    """Public portal page — token is the access key."""
    lead = db.query(Lead).filter(Lead.customer_token == token).first()
    if not lead:
        raise HTTPException(404, "Ungültiger Zugangslink")

    email_domain = ''
    if lead.email and '@' in lead.email:
        email_domain = lead.email.split('@')[1]

    latest_audit = db.query(AuditResult).filter(
        AuditResult.lead_id == lead.id, AuditResult.status == 'completed',
    ).order_by(AuditResult.created_at.desc()).first()

    project = db.query(Project).filter(
        Project.lead_id == lead.id
    ).order_by(Project.created_at.desc()).first()

    return {
        'lead_id': lead.id,
        'company_name': lead.display_name or lead.company_name or '',
        'email_domain': email_domain,
        'website_url': lead.website_url or '',
        'city': lead.city or '',
        'trade': lead.trade or '',
        'contact_name': lead.contact_name or '',
        'current_score': latest_audit.total_score if latest_audit else None,
        'current_level': latest_audit.level if latest_audit else None,
        'last_audit_date': str(latest_audit.created_at)[:10] if latest_audit else None,
        'rc_score': latest_audit.rc_score if latest_audit else None,
        'tp_score': latest_audit.tp_score if latest_audit else None,
        'bf_score': latest_audit.bf_score if latest_audit else None,
        'si_score': latest_audit.si_score if latest_audit else None,
        'se_score': latest_audit.se_score if latest_audit else None,
        'ux_score': latest_audit.ux_score if latest_audit else None,
        'ai_summary': latest_audit.ai_summary if latest_audit else None,
        'website_screenshot': f'data:image/jpeg;base64,{lead.website_screenshot}' if lead.website_screenshot else None,
        'onboarding_completed': getattr(lead, 'onboarding_completed', False) or False,
        'project_id':     project.id if project else None,
        'current_phase':  project.current_phase if project else None,
        'project_status': project.status if project else None,
        'go_live_date':   str(project.go_live_date)[:10] if project and project.go_live_date else None,
    }


@public_router.post("/portal/{token}/verify")
def verify_portal_access(token: str, data: dict, db: Session = Depends(get_db)):
    """Verify access via email domain match."""
    lead = db.query(Lead).filter(Lead.customer_token == token).first()
    if not lead:
        raise HTTPException(404, "Ungültiger Link")

    input_email = data.get('email', '').lower().strip()
    if not input_email or '@' not in input_email:
        raise HTTPException(400, "Bitte gültige E-Mail eingeben")

    input_domain = input_email.split('@')[1]
    lead_domain = ''
    if lead.email and '@' in lead.email:
        lead_domain = lead.email.split('@')[1].lower()
    elif lead.website_url:
        lead_domain = lead.website_url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].lower()

    if not lead_domain:
        raise HTTPException(400, "Keine Domain hinterlegt")
    if input_domain != lead_domain:
        raise HTTPException(403, "E-Mail-Domain stimmt nicht überein")

    return {
        'verified': True,
        'contact_name': lead.contact_name or '',
        'email': lead.email or '',
        'phone': lead.phone or '',
        'street': lead.street or '',
        'house_number': lead.house_number or '',
        'postal_code': lead.postal_code or '',
        'city': lead.city or '',
        'legal_form': lead.legal_form or '',
        'vat_id': lead.vat_id or '',
        'register_number': lead.register_number or '',
        'register_court': lead.register_court or '',
        'ceo_first_name': lead.ceo_first_name or '',
        'ceo_last_name': lead.ceo_last_name or '',
        'geschaeftsfuehrer': lead.geschaeftsfuehrer or '',
    }


@public_router.post("/portal/{token}/complete-onboarding")
def complete_onboarding(token: str, data: dict, db: Session = Depends(get_db)):
    """Mark onboarding as completed and optionally save briefing fields."""
    lead = db.query(Lead).filter(Lead.customer_token == token).first()
    if not lead:
        raise HTTPException(404, "Ungültiger Zugangslink")

    if data.get('website_url'):
        lead.website_url = data['website_url']

    lead.onboarding_completed = True
    lead.onboarding_completed_at = datetime.utcnow()

    # Briefing-Felder speichern falls vorhanden
    gewerk       = data.get('gewerk')
    leistungen   = data.get('leistungen')
    einzugsgebiet = data.get('einzugsgebiet')
    has_logo     = data.get('has_logo')
    has_photos   = data.get('has_photos')
    anmerkungen  = data.get('anmerkungen')

    briefing_fields = any(v is not None for v in [
        gewerk, leistungen, einzugsgebiet, has_logo, has_photos, anmerkungen
    ])

    if briefing_fields:
        try:
            db.execute(text("""
                INSERT INTO briefings
                  (lead_id, gewerk, leistungen, einzugsgebiet,
                   logo_vorhanden, fotos_vorhanden, sonstige_hinweise, status)
                VALUES
                  (:lead_id, :gewerk, :leistungen, :einzugsgebiet,
                   :logo_vorhanden, :fotos_vorhanden, :sonstige_hinweise, 'entwurf')
                ON CONFLICT (lead_id) DO UPDATE SET
                  gewerk            = COALESCE(EXCLUDED.gewerk, briefings.gewerk),
                  leistungen        = COALESCE(EXCLUDED.leistungen, briefings.leistungen),
                  einzugsgebiet     = COALESCE(EXCLUDED.einzugsgebiet, briefings.einzugsgebiet),
                  logo_vorhanden    = COALESCE(EXCLUDED.logo_vorhanden, briefings.logo_vorhanden),
                  fotos_vorhanden   = COALESCE(EXCLUDED.fotos_vorhanden, briefings.fotos_vorhanden),
                  sonstige_hinweise = COALESCE(EXCLUDED.sonstige_hinweise, briefings.sonstige_hinweise),
                  updated_at        = NOW()
            """), {
                'lead_id':          lead.id,
                'gewerk':           gewerk,
                'leistungen':       leistungen,
                'einzugsgebiet':    einzugsgebiet,
                'logo_vorhanden':   has_logo,
                'fotos_vorhanden':  has_photos,
                'sonstige_hinweise': anmerkungen,
            })
        except Exception:
            # Briefings-Tabelle existiert nicht — Felder als Notiz sichern
            parts = []
            if gewerk:        parts.append(f"Gewerk: {gewerk}")
            if leistungen:    parts.append(f"Leistungen: {leistungen}")
            if einzugsgebiet: parts.append(f"Einzugsgebiet: {einzugsgebiet}")
            if anmerkungen:   parts.append(f"Anmerkungen: {anmerkungen}")
            if parts:
                lead.notes = ((lead.notes or '') + '\n' + '\n'.join(parts)).strip()

    db.commit()
    return {"success": True}


@public_router.post("/portal-auth/complete-onboarding")
def portal_auth_complete_onboarding(
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """JWT-geschützter Onboarding-Abschluss für Kunden."""
    from database import User as UserModel
    if current_user.role != 'kunde':
        raise HTTPException(403, "Nur für Kunden zugänglich")

    lead_id = data.get('lead_id') or current_user.lead_id
    if not lead_id:
        raise HTTPException(400, "lead_id fehlt")

    if current_user.lead_id and current_user.lead_id != lead_id:
        raise HTTPException(403, "Zugriff verweigert")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    if data.get('website_url'):
        lead.website_url = data['website_url']

    lead.onboarding_completed = True
    lead.onboarding_completed_at = datetime.utcnow()

    parts = []
    if data.get('gewerk'):        parts.append(f"Gewerk: {data['gewerk']}")
    if data.get('leistungen'):    parts.append(f"Leistungen: {data['leistungen']}")
    if data.get('einzugsgebiet'): parts.append(f"Einzugsgebiet: {data['einzugsgebiet']}")
    if data.get('anmerkungen'):   parts.append(f"Anmerkungen: {data['anmerkungen']}")
    if parts:
        lead.notes = ((lead.notes or '') + '\n---\nOnboarding:\n' + '\n'.join(parts)).strip()

    db.commit()
    return {"success": True}


# ── Routes with {lead_id} parameter below ──────────────────────


@kunden_router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a specific lead by ID.

    Die einzige Lead-Route, die auch ein Kunde aufrufen darf — für den
    eigenen Betrieb. Die eigene Nummer hochzuzählen ist der naheliegendste
    Angriff, deshalb steht die Prüfung hier und nicht in der Oberfläche.

    **18.08.2026:** Die Prüfung fragte, ob jemand `kunde` ist — und liess
    damit die Rolle `nutzer` durch, die laut Rechtematrix kein `view_leads`
    hat. Jetzt umgekehrt: Wer nicht zum Innendienst gehört, sieht nur den
    eigenen Betrieb. Dieselbe Umkehrung wie in `require_innendienst`.
    """
    if current_user.role not in INNENDIENST and current_user.lead_id != lead_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diesen Betrieb")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", dependencies=[Depends(verlangt_recht("edit_leads"))])
def update_lead(lead_id: int, data: LeadUpdate, db: Session = Depends(get_db)):
    """Update a lead — saves all provided fields."""
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    update_fields = data.dict(exclude_none=True)
    for field, value in update_fields.items():
        if hasattr(db_lead, field):
            setattr(db_lead, field, value)

    db_lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_lead)
    return {"success": True, "id": db_lead.id}


@router.delete("/{lead_id}", dependencies=[Depends(verlangt_recht("delete_leads"))])
def delete_lead(lead_id: int, mit_zugang: bool = False, db: Session = Depends(get_db)):
    """Einen Betrieb samt allem, was an ihm hängt, entfernen.

    `mit_zugang=true` nimmt das Kundenkonto mit. **Ohne diesen Zusatz
    geschieht das nicht** — die Entscheidung dazu fiel am 22.08.2026 (L-56),
    und beide Hälften haben ihren Grund:

    Wer einen Betrieb aus dem Bestand räumt — Dublette, kein Kunde mehr —,
    soll nicht unbemerkt einen Zugang löschen, mit dem sich ein Mensch
    anmeldet. Ein Konto darf keine Nebenwirkung einer Aufräumarbeit sein.

    Ein Weg muss es aber geben: Bei einem Löschverlangen nach Art. 17 DSGVO
    muss beides weg. Ohne ihn müsste der Innendienst das Konto in einem
    anderen Bildschirm suchen — zwei Schritte, von denen man einen vergisst,
    und ein übriggebliebenes Konto ist genau der Verstoß, den die Vorschrift
    meint.

    Die Antwort nennt jedes mitgelöschte Konto. Sonst wäre das Mitnehmen
    wieder die stille Nebenwirkung, die es nicht sein soll.
    """
    # 1. Prüfen ob Lead existiert
    lead = db.execute(
        text("SELECT id FROM leads WHERE id = :id"), {"id": lead_id}
    ).fetchone()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    # 2. Projekte samt Anhang — die Reihenfolge über die fünfzehn abhängigen
    #    Tabellen steht in `services/projekt_loeschen.py` und gilt hier
    #    genauso. Vorher stand hier eine eigene Liste mit vier Tabellen; sie
    #    wäre am NOT-NULL-Fremdschlüssel von `customers` gescheitert, sobald
    #    ein Projekt einen Kunden hatte, und hätte bei den übrigen elf Zeilen
    #    zurückgelassen, deren `project_id` ins Leere zeigt.
    from services.projekt_loeschen import entfernen, tabelle_vorhanden

    projekte = db.execute(
        text("SELECT id FROM projects WHERE lead_id = :id"), {"id": lead_id}
    ).fetchall()
    entfernen(db, [zeile[0] for zeile in projekte])

    # 3. Weitere Lead-abhängige Daten löschen
    #
    # Jede Tabelle wird vorher nachgeschlagen. `project_files` tat das schon;
    # die drei anderen nicht — und das fiel am 22.08.2026 in der CI auf, wo
    # die Datenbank frisch ist: `email_logs` gab es dort nicht, der Aufruf
    # endete in einem unbehandelten `UndefinedTable`. Lokal lief derselbe
    # Test grün, weil die Testdatenbank die Tabelle noch von einem früheren
    # Lauf hatte. Eine Tabelle, die es nicht gibt, hat auch nichts, was zu
    # löschen wäre.
    for tabelle in ("project_files", "briefings", "audit_results", "email_logs"):
        if tabelle_vorhanden(db, tabelle):
            db.execute(text(f"DELETE FROM {tabelle} WHERE lead_id = :id"), {"id": lead_id})

    # 6. Lead selbst löschen
    #
    # Ein Betrieb mit Kundenzugang scheiterte hier am Fremdschlüssel
    # `users.lead_id` — unbehandelt, also **500** mit einer Meldung, aus der
    # niemand schließen kann, was zu tun ist (gefunden 19.08.2026).
    #
    # Ein Betrieb mit Kundenzugang scheiterte hier am Fremdschlüssel
    # `users.lead_id`. Seit dem 22.08.2026 entscheidet der Aufrufer, ob das
    # Konto mitgeht — die Begründung steht im Docstring (L-56).
    konten = db.execute(
        text("SELECT email FROM users WHERE lead_id = :id"), {"id": lead_id}
    ).fetchall()
    adressen = [zeile[0] for zeile in konten]

    if adressen and not mit_zugang:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Der Betrieb hat noch {len(adressen)} Kundenzugang"
                f"{'' if len(adressen) == 1 else '/-zugänge'} "
                f"({', '.join(adressen)}). Entweder den Zugang zuerst "
                f"entfernen — oder mit ?mit_zugang=true beides zusammen "
                f"löschen, etwa bei einem Löschverlangen nach DSGVO."
            ),
        )

    if adressen:
        # Erst die Sitzungen, dann die Konten: `user_sessions.user_id` hält
        # sonst dagegen, und der Aufruf scheiterte an derselben Sorte
        # Fremdschlüssel wie vorher, nur eine Tabelle weiter.
        db.execute(text(
            "DELETE FROM user_sessions WHERE user_id IN "
            "(SELECT id FROM users WHERE lead_id = :id)"), {"id": lead_id})
        db.execute(text("DELETE FROM users WHERE lead_id = :id"), {"id": lead_id})
        logger.info("Betrieb %s gelöscht, Zugänge mitgenommen: %s",
                    lead_id, ", ".join(adressen))

    db.execute(text("DELETE FROM leads WHERE id = :id"), {"id": lead_id})
    db.commit()

    return {"deleted": True, "id": lead_id, "zugaenge_geloescht": adressen}


@router.post("/{lead_id}/analyze")
def analyze_lead(lead_id: int, db: Session = Depends(get_db)):
    """Run lead analyst agent on a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        # Initialize agent
        use_mock = not os.getenv("ANTHROPIC_API_KEY")
        agent = LeadAnalystAgent() if not use_mock else None

        if agent:
            result = agent.analyze_lead(
                website_url=lead.website_url or "https://example.com",
                company_name=lead.company_name,
                city=lead.city,
                trade=lead.trade,
            )
        else:
            # Use mock for testing
            result = LeadAnalystAgent.get_mock_analysis(lead.company_name, lead.trade)

        # Store scores
        lead.analysis_score = result.get("overall_score", 0)
        lead.geo_score = result.get("geo_visibility_score", 0)
        lead.status = "qualified" if result.get("overall_score", 0) >= 60 else "contacted"
        db.commit()

        return {
            "lead_id": lead_id,
            "analysis": result,
            "updated_lead": {
                "analysis_score": lead.analysis_score,
                "geo_score": lead.geo_score,
                "status": lead.status,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/{lead_id}/convert")
def convert_lead(
    lead_id: int,
    convert_request: LeadConvertRequest,
    db: Session = Depends(get_db),
):
    """Convert lead to a project (create Project)."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check if already converted
    existing_project = db.query(Project).filter(Project.lead_id == lead_id).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="Lead already converted to project")

    try:
        # Create project
        project = Project(
            lead_id=lead_id,
            status="phase_1",
            start_date=datetime.utcnow(),
            fixed_price=convert_request.fixed_price,
            hourly_rate=convert_request.hourly_rate,
            ai_tool_costs=convert_request.ai_tool_costs,
        )
        db.add(project)
        db.flush()  # Get the project ID

        # Create checklists for all 7 phases
        create_project_checklists(db, project.id)

        # Update lead status
        lead.status = "won"
        db.commit()
        db.refresh(project)

        return {
            "project_id": project.id,
            "lead_id": lead_id,
            "status": project.status,
            "created_at": project.created_at,
            "message": f"Lead converted to Project #{project.id}",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


# ===== IMPORT ENDPOINTS =====







@router.post("/{lead_id}/enrich")
async def enrich_single_lead(lead_id: int, db: Session = Depends(get_db)):
    """Manually trigger enrichment for a single lead."""
    from services.lead_enrichment import enrich_lead
    result = await enrich_lead(lead_id, db)
    return result


@router.get("/{lead_id}/latest-screenshot")
def get_latest_screenshot(lead_id: int, db: Session = Depends(get_db)):
    """Get the latest audit screenshot for a lead, saving it to the lead if found."""
    latest = (
        db.query(AuditResult)
        .filter(AuditResult.lead_id == lead_id, AuditResult.status == "completed", AuditResult.screenshot_base64 != "", AuditResult.screenshot_base64 != None)
        .order_by(AuditResult.created_at.desc())
        .first()
    )
    if not latest or not latest.screenshot_base64:
        return {"screenshot_url": None}
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if lead and not lead.website_screenshot:
        lead.website_screenshot = latest.screenshot_base64
        db.commit()
    return {
        "screenshot_url": f"data:image/jpeg;base64,{latest.screenshot_base64}",
        "audit_date": latest.created_at.strftime("%d.%m.%Y") if latest.created_at else "",
        "audit_score": latest.total_score,
    }


@router.post("/{lead_id}/screenshot")
async def create_screenshot(lead_id: int, db: Session = Depends(get_db)):
    """Capture website screenshot and return it immediately."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")
    if not lead.website_url:
        raise HTTPException(400, "Keine Website-URL hinterlegt")

    url = lead.website_url
    if not url.startswith("http"):
        url = "https://" + url

    try:
        from services.screenshot import capture_screenshot
        screenshot_b64 = await capture_screenshot(url)
        if screenshot_b64:
            lead.website_screenshot = screenshot_b64
            db.commit()
            return {"success": True, "screenshot_url": f"data:image/jpeg;base64,{screenshot_b64}"}
        else:
            raise HTTPException(500, "Screenshot konnte nicht erstellt werden")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Screenshot Fehler: {str(e)}")


@router.get("/{lead_id}/profile")
def get_lead_profile(lead_id: int, db: Session = Depends(get_db)):
    """Full lead profile with audits, projects, and score history."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    audits = (
        db.query(AuditResult)
        .filter(AuditResult.lead_id == lead_id)
        .order_by(AuditResult.created_at.desc())
        .all()
    )

    projects = db.query(Project).filter(Project.lead_id == lead_id).all()

    latest_audit = audits[0] if audits else None

    score_history = [
        {
            "date": a.created_at.strftime("%d.%m.%Y") if a.created_at else "",
            "score": a.total_score,
            "level": a.level,
        }
        for a in reversed(audits)
    ]

    def _audit_dict(a):
        d = {
            "id": a.id,
            "created_at": a.created_at.strftime("%d.%m.%Y %H:%M") if a.created_at else "",
            "total_score": a.total_score,
            "level": a.level,
            "status": a.status,
            "website_url": a.website_url,
            "company_name": a.company_name,
            "trade": a.trade,
            "city": a.city,
            "ai_summary": a.ai_summary,
            "ssl_ok": a.ssl_ok,
            "mobile_score": a.mobile_score,
            "lcp_value": a.lcp_value,
            "cls_value": a.cls_value,
            "inp_value": a.inp_value,
            "rc_score": a.rc_score, "tp_score": a.tp_score,
            "bf_score": a.bf_score, "si_score": a.si_score,
            "se_score": a.se_score, "ux_score": a.ux_score,
        }
        # Item-level scores
        for key in [
            "rc_impressum", "rc_datenschutz", "rc_cookie", "rc_bfsg", "rc_urheberrecht", "rc_ecommerce",
            "tp_lcp", "tp_cls", "tp_inp", "tp_mobile", "tp_bilder",
            "ho_anbieter", "ho_uptime", "ho_http", "ho_backup", "ho_cdn",
            "bf_kontrast", "bf_tastatur", "bf_screenreader", "bf_lesbarkeit",
            "si_ssl", "si_header", "si_drittanbieter", "si_formulare",
            "se_seo", "se_schema", "se_lokal",
            "ux_erstindruck", "ux_cta", "ux_navigation", "ux_vertrauen", "ux_content", "ux_kontakt",
        ]:
            d[key] = getattr(a, key, 0) or 0
        # GEO / KI-Sichtbarkeit fields
        d["llms_txt"] = getattr(a, "llms_txt", False) or False
        d["robots_ai_friendly"] = getattr(a, "robots_ai_friendly", False) or False
        d["structured_data"] = getattr(a, "structured_data", False) or False
        d["ai_mentions"] = getattr(a, "ai_mentions", 0) or 0
        # JSON fields
        try:
            d["top_issues"] = json.loads(a.top_issues) if a.top_issues else []
        except (json.JSONDecodeError, TypeError):
            d["top_issues"] = []
        try:
            d["recommendations"] = json.loads(a.recommendations) if a.recommendations else []
        except (json.JSONDecodeError, TypeError):
            d["recommendations"] = []
        return d

    return {
        "lead": {
            "id": lead.id,
            "company_name": lead.company_name,
            "contact_name": lead.contact_name,
            "phone": lead.phone,
            "mobile": getattr(lead, 'mobile', '') or '',
            "email": lead.email,
            "website_url": lead.website_url,
            "city": lead.city,
            "trade": lead.trade,
            "status": lead.status,
            "lead_source": lead.lead_source,
            # Woher der Betrieb kam und unter welcher Rechtsgrundlage wir ihn
            # fuehren — abgeleitet aus derselben gespeicherten Quelle, damit
            # es keine zweite Wahrheit gibt (L-59).
            "datenherkunft": lead_quellen.herkunft_fuer(lead.lead_source),
            "rechtsgrundlage": lead_quellen.rechtsgrundlage_fuer(lead.lead_source),
            "quelle_gefuehrt": lead_quellen.quelle_bekannt(lead.lead_source),
            "notes": lead.notes,
            "created_at": lead.created_at.strftime("%d.%m.%Y") if lead.created_at else "",
            "website_screenshot": f"data:image/jpeg;base64,{lead.website_screenshot}" if getattr(lead, 'website_screenshot', None) else None,
            "street": getattr(lead, 'street', '') or '',
            "house_number": getattr(lead, 'house_number', '') or '',
            "postal_code": getattr(lead, 'postal_code', '') or '',
            "legal_form": getattr(lead, 'legal_form', '') or '',
            "vat_id": getattr(lead, 'vat_id', '') or '',
            "register_number": getattr(lead, 'register_number', '') or '',
            "register_court": getattr(lead, 'register_court', '') or '',
            "ceo_first_name": getattr(lead, 'ceo_first_name', '') or '',
            "ceo_last_name": getattr(lead, 'ceo_last_name', '') or '',
            "geschaeftsfuehrer": getattr(lead, 'geschaeftsfuehrer', '') or '',
            "display_name": getattr(lead, 'display_name', '') or '',
        },
        # Befunde der Anreicherung. Bewusst ohne `or False`: `None` heißt
        # „noch nicht geprüft" und darf nicht als „fehlt" durchgehen (UX-06).
        "anreicherung": {
            "has_ssl": getattr(lead, 'has_ssl', None),
            "has_impressum": getattr(lead, 'has_impressum', None),
            "pagespeed_mobile": getattr(lead, 'pagespeed_mobile_score', None),
            "geprueft_am": (lead.enriched_at.strftime("%d.%m.%Y")
                            if getattr(lead, 'enriched_at', None) else None),
        },
        "current_score": latest_audit.total_score if latest_audit else None,
        "current_level": latest_audit.level if latest_audit else None,
        "score_history": score_history,
        "total_audits": len(audits),
        "audits": [_audit_dict(a) for a in audits],
        "projects": [
            {
                "id": p.id,
                "status": p.status,
                "start_date": p.start_date.strftime("%d.%m.%Y") if p.start_date else "",
                "target_go_live": p.target_go_live.strftime("%d.%m.%Y") if p.target_go_live else "",
                "margin_percent": p.margin_percent,
            }
            for p in projects
        ],
        "project_id": projects[0].id if projects else None,
    }


@router.get("/{lead_id}/audits")
def get_lead_audits(lead_id: int, db: Session = Depends(get_db)):
    """Get all audits linked to a lead, newest first."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    audits = (
        db.query(AuditResult)
        .filter(AuditResult.lead_id == lead_id, AuditResult.status == "completed")
        .order_by(AuditResult.created_at.desc())
        .all()
    )

    results = []
    for a in audits:
        try:
            top_issues = json.loads(a.top_issues) if a.top_issues else []
        except (json.JSONDecodeError, TypeError):
            top_issues = []
        results.append({
            "id": a.id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "total_score": a.total_score,
            "level": a.level,
            "website_url": a.website_url,
            "top_issues": top_issues,
            "ai_summary": a.ai_summary,
        })
    return results






@router.post("/befunde-nachtragen")
def befunde_nachtragen(
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Holt SSL, Impressum und PageSpeed aus der alten Notizzeile in die Spalten.

    Seit dem 17.08.2026 stehen diese Befunde in eigenen Spalten. Für den
    Bestand hieß das: Spalten leer, Oberfläche sagt „nicht geprüft" — und
    darunter behauptet die alte Notiz „SSL: OK". Beides stimmt für sich,
    zusammen widersprechen sie sich auf einem Bildschirm.

    Übernommen wird nur, was noch leer ist: Was die neue Anreicherung
    geschrieben hat, ist jünger als die Notiz. Ein Zeitpunkt wird nicht
    erfunden — die Zeile trug keinen.
    """
    from services import anreicherungsnotiz

    betroffen = db.query(Lead).filter(
        Lead.notes.ilike(f"%{anreicherungsnotiz.MARKE}%")).all()

    bericht = []
    for lead in betroffen:
        befunde = anreicherungsnotiz.befunde_aus_notiz(lead.notes)
        uebernommen = []
        for feld, wert in befunde.items():
            if getattr(lead, feld, None) is None:
                setattr(lead, feld, wert)
                uebernommen.append(feld)

        lead.notes = anreicherungsnotiz.notiz_ohne_maschinenzeilen(lead.notes)
        bericht.append({
            "id": lead.id,
            "betrieb": lead.company_name,
            "uebernommen": uebernommen,
            "notiz_bleibt": bool(lead.notes),
        })

    if bericht:
        db.commit()

    return {"betroffen": len(betroffen), "betriebe": bericht}




@router.get("/{lead_id}/qr-code")
def get_qr_code(lead_id: int, db: Session = Depends(get_db)):
    """Get or create QR code for customer portal access."""
    from services.qr_service import generate_token, generate_qr_code, get_portal_url

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Nicht gefunden")

    if not lead.customer_token:
        lead.customer_token = generate_token()
        lead.customer_token_created_at = datetime.utcnow()
        db.commit()
        db.refresh(lead)

    portal_url = get_portal_url(lead.customer_token)
    qr_b64 = generate_qr_code(portal_url)

    return {
        'token': lead.customer_token,
        'portal_url': portal_url,
        'qr_code_base64': qr_b64,
        'created_at': str(lead.customer_token_created_at)[:10] if lead.customer_token_created_at else '',
    }


@router.post("/{lead_id}/qr-code/refresh")
def refresh_qr_code(lead_id: int, db: Session = Depends(get_db)):
    """Generate a new QR code token, invalidating the old one."""
    from services.qr_service import generate_token, generate_qr_code, get_portal_url

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Nicht gefunden")

    lead.customer_token = generate_token()
    lead.customer_token_created_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)

    portal_url = get_portal_url(lead.customer_token)
    qr_b64 = generate_qr_code(portal_url)

    return {
        'token': lead.customer_token,
        'portal_url': portal_url,
        'qr_code_base64': qr_b64,
        'created_at': str(lead.customer_token_created_at)[:10],
    }








# ── Lead Domains ─────────────────────────────────────────────────────────────

@router.get("/{lead_id}/domains")
def get_lead_domains(lead_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)):
    from database import LeadDomain
    domains = db.query(LeadDomain).filter(LeadDomain.lead_id == lead_id).order_by(LeadDomain.is_primary.desc(), LeadDomain.created_at).all()
    return [{"id": d.id, "url": d.url, "label": d.label, "is_primary": d.is_primary} for d in domains]

@router.post("/{lead_id}/domains")
def add_lead_domain(lead_id: int, data: dict, db: Session = Depends(get_db), _=Depends(require_any_auth)):
    from database import LeadDomain
    url = data.get("url", "").strip()
    if not url:
        raise HTTPException(400, "URL fehlt")
    if not url.startswith("http"):
        url = "https://" + url
    is_primary = data.get("is_primary", False)
    if is_primary:
        db.query(LeadDomain).filter(LeadDomain.lead_id == lead_id).update({"is_primary": False})
    domain = LeadDomain(lead_id=lead_id, url=url, label=data.get("label", ""), is_primary=is_primary)
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return {"id": domain.id, "url": domain.url, "label": domain.label, "is_primary": domain.is_primary}

@router.delete("/{lead_id}/domains/{domain_id}")
def delete_lead_domain(lead_id: int, domain_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)):
    from database import LeadDomain
    domain = db.query(LeadDomain).filter(LeadDomain.id == domain_id, LeadDomain.lead_id == lead_id).first()
    if not domain:
        raise HTTPException(404, "Domain nicht gefunden")
    db.delete(domain)
    db.commit()
    return {"ok": True}




# ── E-Mail-Sequenz-Endpunkte ─────────────────────────────────────────────────

@router.post("/{lead_id}/sequence/start", dependencies=[Depends(require_any_auth)])
def sequence_start(lead_id: int, db: Session = Depends(get_db)):
    from services.sequence_runner import start_sequence_for_lead
    ok = start_sequence_for_lead(lead_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Lead not found or no email")
    return {"success": ok}


@router.post("/{lead_id}/sequence/pause", dependencies=[Depends(require_any_auth)])
def sequence_pause(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.sequence_paused = True
    db.commit()
    return {"success": True}


@router.post("/{lead_id}/sequence/stop", dependencies=[Depends(require_any_auth)])
def sequence_stop(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.sequence_active = False
    lead.sequence_paused = False
    lead.sequence_step = 0
    db.commit()
    return {"success": True}


@router.get("/{lead_id}/email-logs", dependencies=[Depends(require_any_auth)])
def get_email_logs(lead_id: int, db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT * FROM email_logs WHERE lead_id=:id ORDER BY sent_at DESC LIMIT 50"),
        {"id": lead_id},
    ).mappings().all()
    return [dict(r) for r in rows]


# ── /api/customers aliases for all /{lead_id}/... endpoints ─────────────────
@router.post("/{lead_id}/briefing-prefill")
async def briefing_prefill_from_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Briefing-Vorschlaege aus gecrawltem Website-Content via lead_id."""
    import json
    from urllib.parse import urlparse

    rows = db.execute(
        text("""
            SELECT url, title, meta_description, h1, h2s, text_preview
            FROM website_content_cache
            WHERE customer_id = :lid
            ORDER BY scraped_at DESC LIMIT 20
        """),
        {"lid": lead_id},
    ).fetchall()

    if not rows:
        raise HTTPException(400, "Kein Website-Content vorhanden. Bitte zuerst Crawler ausfuehren.")

    all_h2s, page_names, pages_text = [], [], []
    for row in rows:
        url, title, meta, h1, h2s_json, preview = row
        try:
            all_h2s.extend(json.loads(h2s_json or '[]'))
        except Exception:
            pass
        try:
            path = urlparse(url).path.strip('/').split('/')[-1]
            if path and len(path) > 1:
                name = path.replace('-', ' ').replace('_', ' ').title()
                if name not in page_names:
                    page_names.append(name)
        except Exception:
            pass
        if preview:
            pages_text.append(f"URL: {url}\nH1: {h1 or title}\nVorschau: {preview[:300]}")

    return {
        "gewerk":        (all_h2s[0] if all_h2s else '')[:80],
        "leistungen":    ', '.join(set(all_h2s[:8])),
        "wunschseiten":  ', '.join(page_names[:8]),
        "einzugsgebiet": '',
        "usp":           '',
        "zielgruppe":    '',
        "source":        "heuristic",
    }


# ── Admin: manueller Performance-Report Trigger ──────────────────────────────

@router.post("/admin/trigger-performance-reports")
async def trigger_performance_reports(
    _=Depends(require_any_auth),
):
    """Manueller Trigger für den monatlichen Performance-Report (Admin-Test)."""
    from automations.scheduler import job_monthly_performance_report

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, job_monthly_performance_report)

    return {
        "message": "Performance-Report Job gestartet — prüfe Render-Logs",
        "note": "Läuft im Hintergrund, dauert 1-3 Min. je nach Anzahl Kunden",
    }


# ── Kaltakquise ──────────────────────────────────────────────────────────────



# ── Kein `/api/customers`-Alias mehr (21.08.2026) ────────────────────────────
#
# Hier stand ein Router, der denselben Lead-Bestand zusaetzlich unter
# `/api/customers` anbot. Er war **tot**: `usercards.customers_alias_router`
# war frueher eingebunden und gewann jede seiner Routen — die OpenAPI-Datei
# beschrieb allerdings *ihn*, weil FastAPI dort den zuletzt registrierten
# Handler eintraegt. Die Beschreibung nannte also einen Endpunkt, der nie
# antwortete. Drei Router beanspruchten diese Adresse mit drei verschiedenen
# Entitaeten (Lead, UserCard, Customer); jetzt gehoert sie `customers.py`.
