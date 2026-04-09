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
from routers.auth_router import require_any_auth, get_current_user
from seed_checklists import create_project_checklists
from agents.lead_analyst import LeadAnalystAgent
import asyncio
import csv
import httpx
import io
import json
import os
import uuid

router = APIRouter(prefix="/api/leads", tags=["leads"])

# In-memory job tracking for domain imports
import_jobs = {}


class DomainsTextInput(BaseModel):
    domains_text: str


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


@router.post("/")
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
            import asyncio
            from services.google_business import check_google_business
            from database import SessionLocal
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


@router.get("/")
def list_leads(
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(200),
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


@router.get("/export/csv")
def export_leads_csv(db: Session = Depends(get_db)):
    """Export all leads as CSV file."""
    import io as _io
    from fastapi.responses import StreamingResponse

    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    output = _io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["ID", "Firmenname", "Geschäftsführer", "Ansprechpartner", "Telefon", "E-Mail", "Website", "Stadt", "Gewerk", "Status", "Score", "Quelle", "Erstellt am"])
    for lead in leads:
        writer.writerow([
            lead.id, lead.company_name or "", lead.geschaeftsfuehrer or "", lead.contact_name or "", lead.phone or "",
            lead.email or "", lead.website_url or "", lead.city or "", lead.trade or "",
            lead.status or "", lead.analysis_score or 0, lead.lead_source or "",
            str(lead.created_at)[:10] if lead.created_at else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads-export.csv"},
    )


@router.post("/import/domains/check")
async def check_domains(data: dict, db: Session = Depends(get_db)):
    """Check which domains already exist + reachability/redirect check."""
    from sqlalchemy import or_
    from services.domain_checker import check_domains_batch
    import logging as _log
    _logger = _log.getLogger('domain_import')

    raw_domains = data.get("domains", [])

    # Normalize
    normalized = []
    for url in raw_domains:
        clean = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].lower()
        if clean:
            normalized.append(f'https://{clean}')

    # Domain reachability + redirect check
    try:
        domain_checks = await check_domains_batch(normalized)
    except Exception as e:
        _logger.error(f'Domain batch check Fehler: {e}')
        domain_checks = [{'original_url': u, 'final_url': u, 'reachable': True, 'has_redirect': False,
                          'skip_import': False, 'skip_reason': '', 'redirect_count': 0, 'final_is_https': True} for u in normalized]

    # Combine with DB check
    results = []
    for check in domain_checks:
        url = check['original_url']
        clean = url.replace('https://', '').replace('www.', '').split('/')[0]

        existing = db.query(Lead).filter(or_(
            Lead.website_url.ilike(f'%{clean}%'),
            Lead.website_url.ilike(f'%www.{clean}%'),
        )).first()

        results.append({
            'url': url,
            'final_url': check.get('final_url', url),
            'domain': clean,
            'exists': existing is not None,
            'lead_id': existing.id if existing else None,
            'company_name': (existing.display_name or existing.company_name) if existing else None,
            'status': existing.status if existing else None,
            'score': existing.analysis_score if existing else None,
            'reachable': check.get('reachable', True),
            'has_redirect': check.get('has_redirect', False),
            'redirect_count': check.get('redirect_count', 0),
            'final_is_https': check.get('final_is_https', True),
            'skip_import': check.get('skip_import', False),
            'skip_reason': check.get('skip_reason', ''),
        })

    new_count = sum(1 for r in results if not r['exists'] and not r['skip_import'])
    existing_count = sum(1 for r in results if r['exists'])
    skipped_count = sum(1 for r in results if r['skip_import'] and not r['exists'])
    redirect_count = sum(1 for r in results if r['has_redirect'] and not r['skip_import'])

    return {
        'results': results,
        'new_count': new_count,
        'existing_count': existing_count,
        'skipped_count': skipped_count,
        'redirect_count': redirect_count,
        'total': len(results),
    }


def _extract_domains(text: str) -> list:
    """Extract valid domains from text (one per line, comma or semicolon separated)."""
    import re
    domains = []
    seen = set()
    for line in re.split(r'[\n,;]', text):
        cell = line.strip().strip('"').strip("'")
        clean = re.sub(r'^https?://', '', cell).replace('www.', '').split('/')[0].lower()
        if re.match(r'^[a-z0-9][a-z0-9\-\.]+\.[a-z]{2,}$', clean) and clean not in seen:
            domains.append(f'https://{clean}')
            seen.add(clean)
    return domains


async def _process_single_domain(url: str, clean: str, _db, job_id: str) -> dict:
    """Process a single domain sequentially: Lead → pause → Audit → pause → Impressum."""
    import asyncio as _aio
    import logging as _log
    from datetime import datetime as _dt
    _logger = _log.getLogger('domain_import')

    result = {'url': url, 'status': 'created', 'lead_id': None, 'company_name': clean,
              'audit_status': 'pending', 'impressum_status': 'pending', 'score': None}

    # ── Step 1: Duplicate check + Lead creation ──
    existing = _db.query(Lead).filter(Lead.website_url.ilike(f'%{clean}%')).first()
    if existing:
        return {'url': url, 'status': 'already_exists', 'lead_id': existing.id,
                'company_name': existing.display_name or existing.company_name,
                'score': existing.analysis_score,
                'audit_status': 'skipped', 'impressum_status': 'skipped'}

    try:
        lead = Lead(
            company_name=clean, website_url=url, contact_name='', phone='',
            email='', city='', trade='', notes='', website_screenshot='',
            status='new', lead_source='domain_import', analysis_score=0, geo_score=0,
            street='', house_number='', postal_code='', legal_form='',
            vat_id='', register_number='', register_court='',
            ceo_first_name='', ceo_last_name='', display_name='',
            created_at=_dt.utcnow(), updated_at=_dt.utcnow(),
        )
        _db.add(lead)
        _db.commit()
        _db.refresh(lead)
        result['lead_id'] = lead.id
        _logger.info(f'Lead angelegt: {clean} (ID: {lead.id})')
    except Exception as e:
        try: _db.rollback()
        except: pass
        _logger.error(f'Lead anlegen Fehler {clean}: {e}')
        return {'url': url, 'status': 'error', 'error': f'Lead: {str(e)}',
                'audit_status': 'failed', 'impressum_status': 'failed'}

    await _aio.sleep(1)

    # ── Step 2: Audit (max 90s) ──
    _logger.info(f'Starte Audit: {clean}')
    try:
        import httpx
        async with httpx.AsyncClient(timeout=90) as client:
            audit_base = os.getenv('API_BASE_URL', 'http://localhost:8000')
            r = await client.post(f'{audit_base}/api/audit/start',
                json={'website_url': url, 'lead_id': lead.id, 'company_name': clean})
            if r.status_code == 200:
                aid = r.json().get('audit_id') or r.json().get('id')
                if aid:
                    for _ in range(20):
                        await _aio.sleep(4)
                        pr = await client.get(f'{audit_base}/api/audit/{aid}')
                        if pr.status_code == 200:
                            pd = pr.json()
                            if pd.get('status') == 'completed':
                                result['audit_status'] = 'completed'
                                result['score'] = pd.get('total_score')
                                result['company_name'] = pd.get('company_name') or clean
                                _logger.info(f'Audit fertig: {clean} — Score {pd.get("total_score")}')
                                break
                            elif pd.get('status') == 'failed':
                                result['audit_status'] = 'failed'
                                _logger.warning(f'Audit fehlgeschlagen: {clean}')
                                break
    except _aio.TimeoutError:
        result['audit_status'] = 'timeout'
        _logger.warning(f'Audit Timeout: {clean}')
    except Exception as e:
        result['audit_status'] = 'failed'
        _logger.warning(f'Audit Fehler {clean}: {type(e).__name__}: {e}')

    # Pause between audit and impressum (let Anthropic API recover)
    _logger.info(f'Warte 5s vor Impressum: {clean}')
    await _aio.sleep(5)

    # ── Step 3: Impressum (max 30s) ──
    _logger.info(f'Starte Impressum: {clean}')
    try:
        from services.impressum_scraper import extract_contact_from_impressum
        imp = await _aio.wait_for(extract_contact_from_impressum(url), timeout=30.0)
        if imp.get('success'):
            data_imp = imp.get('data', {})
            updated_fields = []
            try: _db.refresh(lead)
            except: pass
            for field in ['company_name', 'legal_form', 'ceo_first_name', 'ceo_last_name',
                          'street', 'house_number', 'postal_code', 'city', 'phone', 'email',
                          'vat_id', 'register_number', 'register_court', 'trade']:
                if data_imp.get(field) and not getattr(lead, field, None):
                    setattr(lead, field, data_imp[field])
                    updated_fields.append(field)
            if not lead.contact_name and data_imp.get('ceo_first_name'):
                lead.contact_name = ' '.join(filter(None, [data_imp.get('ceo_first_name'), data_imp.get('ceo_last_name')]))
            try: _db.commit()
            except: _db.rollback()
            result['impressum_status'] = 'completed'
            result['company_name'] = lead.company_name
            _logger.info(f'Impressum fertig: {clean} — {len(updated_fields)} Felder')
        else:
            result['impressum_status'] = 'failed'
            _logger.warning(f'Impressum kein Ergebnis: {clean}')
    except _aio.TimeoutError:
        result['impressum_status'] = 'timeout'
        _logger.warning(f'Impressum Timeout: {clean}')
    except Exception as e:
        result['impressum_status'] = 'failed'
        _logger.warning(f'Impressum Fehler {clean}: {type(e).__name__}: {e}')

    _logger.info(f'Domain fertig: {clean} — Audit: {result["audit_status"]}, Impressum: {result["impressum_status"]}')
    return result


@router.post("/import/domains/text")
async def import_domains_text(
    data: DomainsTextInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Import domains from text input — runs audit + impressum extraction in background."""
    domains = _extract_domains(data.domains_text)
    if not domains:
        raise HTTPException(400, "Keine gültigen Domains gefunden")
    domains = domains[:20]
    job_id = str(uuid.uuid4())[:8]
    import_jobs[job_id] = {
        'status': 'running', 'total': len(domains),
        'processed': 0, 'results': [],
        'started_at': str(datetime.utcnow())[:19],
    }

    import logging as _log
    _logger = _log.getLogger('domain_import')

    async def run():
        import asyncio as _aio
        import traceback as _tb
        from database import SessionLocal
        try:
            _logger.info(f'Import {job_id}: Starte {len(domains)} Domains')
            for i, url in enumerate(domains):
                clean = url.replace('https://', '').replace('http://', '')
                _logger.info(f'━━━ [{i+1}/{len(domains)}] {clean} ━━━')
                # Own session per domain
                domain_db = SessionLocal()
                try:
                    result = await _aio.wait_for(
                        _process_single_domain(url, clean, domain_db, job_id),
                        timeout=150.0
                    )
                except _aio.TimeoutError:
                    _logger.warning(f'Domain komplett Timeout: {clean}')
                    result = {'url': url, 'status': 'timeout', 'audit_status': 'timeout', 'impressum_status': 'timeout', 'score': None}
                except Exception as domain_err:
                    _logger.error(f'Domain {clean} komplett fehlgeschlagen: {type(domain_err).__name__}: {domain_err}')
                    result = {'url': url, 'status': 'error', 'error': str(domain_err),
                              'audit_status': 'failed', 'impressum_status': 'failed', 'score': None}
                finally:
                    try: domain_db.close()
                    except: pass
                import_jobs[job_id]['results'].append(result)
                import_jobs[job_id]['processed'] = i + 1
                # 10s pause between domains
                if i < len(domains) - 1:
                    _logger.info(f'Warte 10s vor nächster Domain...')
                    await _aio.sleep(10)
            import_jobs[job_id]['status'] = 'done'
            _logger.info(f'Import {job_id}: Fertig — {len(domains)} Domains verarbeitet')
        except Exception as e:
            _logger.error(f'Import {job_id} Fehler: {type(e).__name__}: {e}\n{_tb.format_exc()}')
            import_jobs[job_id]['status'] = 'error'
            import_jobs[job_id]['error'] = f'{type(e).__name__}: {str(e)}'

    import asyncio
    asyncio.ensure_future(run())

    return {
        'job_id': job_id, 'total_domains': len(domains),
        'domains_preview': domains[:5],
        'message': f'{len(domains)} Domains werden verarbeitet',
    }


@router.post("/import/domains/file")
async def import_domains_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import domains from CSV file upload."""
    content = await file.read()
    text = content.decode('utf-8', errors='ignore')
    domains = _extract_domains(text)
    if not domains:
        raise HTTPException(400, "Keine gültigen Domains in der Datei gefunden")
    domains = domains[:20]
    job_id = str(uuid.uuid4())[:8]
    import_jobs[job_id] = {
        'status': 'running', 'total': len(domains),
        'processed': 0, 'results': [],
        'started_at': str(datetime.utcnow())[:19],
    }
    import logging as _log
    _logger = _log.getLogger('domain_import')

    async def run():
        import asyncio as _aio
        import traceback as _tb
        from database import SessionLocal
        try:
            _logger.info(f'File Import {job_id}: Starte {len(domains)} Domains')
            for i, url in enumerate(domains):
                clean = url.replace('https://', '').replace('http://', '')
                _logger.info(f'━━━ [{i+1}/{len(domains)}] {clean} ━━━')
                # Own session per domain
                domain_db = SessionLocal()
                try:
                    result = await _aio.wait_for(
                        _process_single_domain(url, clean, domain_db, job_id),
                        timeout=150.0
                    )
                except _aio.TimeoutError:
                    _logger.warning(f'Domain komplett Timeout: {clean}')
                    result = {'url': url, 'status': 'timeout', 'audit_status': 'timeout', 'impressum_status': 'timeout', 'score': None}
                except Exception as domain_err:
                    _logger.error(f'Domain {clean} komplett fehlgeschlagen: {type(domain_err).__name__}: {domain_err}')
                    result = {'url': url, 'status': 'error', 'error': str(domain_err),
                              'audit_status': 'failed', 'impressum_status': 'failed', 'score': None}
                finally:
                    try: domain_db.close()
                    except: pass
                import_jobs[job_id]['results'].append(result)
                import_jobs[job_id]['processed'] = i + 1
                # 10s pause between domains
                if i < len(domains) - 1:
                    _logger.info(f'Warte 10s vor nächster Domain...')
                    await _aio.sleep(10)
            import_jobs[job_id]['status'] = 'done'
            _logger.info(f'File Import {job_id}: Fertig — {len(domains)} Domains verarbeitet')
        except Exception as e:
            _logger.error(f'File Import {job_id} Fehler: {type(e).__name__}: {e}\n{_tb.format_exc()}')
            import_jobs[job_id]['status'] = 'error'
            import_jobs[job_id]['error'] = f'{type(e).__name__}: {str(e)}'

    import asyncio
    asyncio.ensure_future(run())

    return {
        'job_id': job_id, 'total_domains': len(domains),
        'domains_preview': domains[:5],
        'message': f'{len(domains)} Domains werden verarbeitet',
    }


@router.get("/import/domains/{job_id}/status")
def get_import_status(job_id: str):
    """Get status of a domain import job."""
    if job_id not in import_jobs:
        raise HTTPException(404, "Job nicht gefunden")
    return import_jobs[job_id]


@router.post("/enrich/all")
async def enrich_all_leads(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Batch-enrich all leads with score=0. Runs in background."""
    from services.lead_enrichment import enrich_all_pending
    import asyncio

    def _run():
        from database import SessionLocal
        _db = SessionLocal()
        try:
            asyncio.run(enrich_all_pending(_db))
        finally:
            _db.close()

    background_tasks.add_task(_run)
    return {"message": "Anreicherung gestartet", "status": "processing"}


# ── Public lead creation (no auth — used by landing page audit) ──

@router.post("/public")
async def create_public_lead(data: dict, db: Session = Depends(get_db)):
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
                status='new', lead_source=data.get('lead_source', 'landing_audit'))
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return {'id': lead.id}


# ── Portal routes (public, no auth) ──────────────────────

@router.get("/portal/{token}")
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


@router.post("/portal/{token}/verify")
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


@router.post("/portal/{token}/complete-onboarding")
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


@router.post("/portal-auth/complete-onboarding")
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


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific lead by ID."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}")
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


@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """Delete a lead and all associated data in correct dependency order."""
    # 1. Prüfen ob Lead existiert
    lead = db.execute(
        text("SELECT id FROM leads WHERE id = :id"), {"id": lead_id}
    ).fetchone()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    # 2. Verknüpfte Projekte finden
    projects = db.execute(
        text("SELECT id FROM projects WHERE lead_id = :id"), {"id": lead_id}
    ).fetchall()
    project_ids = [p[0] for p in projects]

    # 3. Abhängige Daten der Projekte löschen (Reihenfolge wichtig)
    for pid in project_ids:
        db.execute(text("DELETE FROM project_checklists WHERE project_id = :id"), {"id": pid})
        db.execute(text("DELETE FROM time_tracking WHERE project_id = :id"), {"id": pid})
        db.execute(text("DELETE FROM briefings WHERE project_id = :id"), {"id": pid})
        db.execute(text("DELETE FROM project_files WHERE lead_id = :id"), {"id": lead_id})

    # 4. Projekte selbst löschen
    if project_ids:
        db.execute(text("DELETE FROM projects WHERE lead_id = :id"), {"id": lead_id})

    # 5. Weitere Lead-abhängige Daten löschen
    db.execute(text("DELETE FROM briefings WHERE lead_id = :id"), {"id": lead_id})
    db.execute(text("DELETE FROM audit_results WHERE lead_id = :id"), {"id": lead_id})
    db.execute(text("DELETE FROM email_logs WHERE lead_id = :id"), {"id": lead_id})

    # 6. Lead selbst löschen
    db.execute(text("DELETE FROM leads WHERE id = :id"), {"id": lead_id})
    db.commit()

    return {"deleted": True, "id": lead_id}


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

class ManualLeadImport(BaseModel):
    company_name: str
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    website_url: str = ""
    city: str = ""
    trade: str = ""


@router.post("/import/csv")
async def import_leads_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """Import leads from a CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Nur CSV-Dateien erlaubt.")

    try:
        content = await file.read()

        # Encoding erkennen
        try:
            text = content.decode("utf-8-sig")  # BOM entfernen
        except UnicodeDecodeError:
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")

        # Delimiter manuell erkennen — KEIN Sniffer
        first_line = text.split("\n")[0] if text else ""

        if ";" in first_line:
            delimiter = ";"
        elif "\t" in first_line:
            delimiter = "\t"
        else:
            delimiter = ","

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

        imported = 0
        errors = 0
        skipped = 0

        for row in reader:
            try:
                # Spaltennamen bereinigen
                clean_row = {}
                for k, v in row.items():
                    if k:
                        clean_key = k.strip().lower().lstrip('\ufeff')
                        clean_row[clean_key] = v.strip() if v else ""

                # Firmenname ist Pflicht
                company = (
                    clean_row.get("company_name")
                    or clean_row.get("firmenname")
                    or clean_row.get("firma")
                    or clean_row.get("unternehmen")
                    or clean_row.get("name")
                    or ""
                )

                if not company:
                    skipped += 1
                    continue

                lead = Lead(
                    company_name=company,
                    contact_name=(
                        clean_row.get("contact_name")
                        or clean_row.get("ansprechpartner")
                        or clean_row.get("kontakt")
                        or ""
                    ),
                    phone=(
                        clean_row.get("phone")
                        or clean_row.get("telefon")
                        or clean_row.get("tel")
                        or ""
                    ),
                    email=(
                        clean_row.get("email")
                        or clean_row.get("e-mail")
                        or clean_row.get("mail")
                        or ""
                    ),
                    website_url=(
                        clean_row.get("website_url")
                        or clean_row.get("website")
                        or clean_row.get("url")
                        or clean_row.get("homepage")
                        or ""
                    ),
                    city=(
                        clean_row.get("city")
                        or clean_row.get("stadt")
                        or clean_row.get("ort")
                        or ""
                    ),
                    trade=(
                        clean_row.get("trade")
                        or clean_row.get("gewerk")
                        or clean_row.get("branche")
                        or "Sonstiges"
                    ),
                    lead_source="csv_import",
                    status="new",
                )
                db.add(lead)
                imported += 1

            except Exception:
                errors += 1
                continue

        db.commit()

        # Background-enrich all imported leads with websites
        if background_tasks and imported > 0:
            from services.lead_enrichment import enrich_lead_sync
            new_leads = db.query(Lead).filter(Lead.lead_source == "csv_import", Lead.analysis_score == 0, Lead.website_url != "").limit(imported).all()
            for nl in new_leads:
                background_tasks.add_task(enrich_lead_sync, nl.id)

        return {
            "success": True,
            "imported": imported,
            "errors": errors,
            "skipped": skipped,
            "message": (
                f"{imported} Kontakte erfolgreich importiert"
                + (f", {skipped} übersprungen" if skipped > 0 else "")
                + (f", {errors} Fehler" if errors > 0 else "")
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Import fehlgeschlagen: {str(e)}",
        )


@router.post("/import/manual", response_model=LeadResponse)
def import_lead_manual(
    lead_data: ManualLeadImport,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Import a single lead manually."""
    if not lead_data.company_name.strip():
        raise HTTPException(status_code=400, detail="Firmenname ist Pflichtfeld.")

    lead = Lead(
        company_name=lead_data.company_name.strip(),
        contact_name=lead_data.contact_name.strip(),
        phone=lead_data.phone.strip(),
        email=lead_data.email.strip(),
        website_url=lead_data.website_url.strip(),
        city=lead_data.city.strip(),
        trade=lead_data.trade.strip(),
        lead_source="Manuell",
        status="new",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    if lead.website_url:
        from services.lead_enrichment import enrich_lead_sync
        background_tasks.add_task(enrich_lead_sync, lead.id)

    return lead


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


@router.post("/{lead_id}/extract-impressum")
async def extract_impressum(lead_id: int, db: Session = Depends(get_db)):
    """Extract contact data from a lead's website impressum using AI."""
    from services.impressum_scraper import extract_contact_from_impressum

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")
    if not lead.website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")

    result = await extract_contact_from_impressum(lead.website_url)

    if not result['success']:
        raise HTTPException(status_code=422, detail=result['error'])

    # Nur leere Felder befüllen — vorhandene Daten NICHT überschreiben
    data = result['data']
    updated = {}

    field_map = {
        'company_name': lead.company_name,
        'legal_form': lead.legal_form,
        'ceo_first_name': lead.ceo_first_name,
        'ceo_last_name': lead.ceo_last_name,
        'street': lead.street,
        'house_number': lead.house_number,
        'postal_code': lead.postal_code,
        'city': lead.city,
        'phone': lead.phone,
        'email': lead.email,
        'vat_id': lead.vat_id,
        'register_number': lead.register_number,
        'register_court': lead.register_court,
        'trade': lead.trade,
    }

    for field, existing in field_map.items():
        if field in data and not existing:
            setattr(lead, field, data[field])
            updated[field] = data[field]

    if updated:
        db.commit()

    return {
        'success': True,
        'extracted': data,
        'updated_fields': updated,
        'skipped_fields': [f for f in data if f not in updated],
    }


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


def _pagespeed_payload_lead(lead: Lead) -> dict:
    """Return stored PageSpeed values for a lead as a dict."""
    return {
        "mobile_score":  lead.pagespeed_mobile_score,
        "desktop_score": lead.pagespeed_desktop_score,
        "lcp_mobile":    lead.pagespeed_lcp_mobile,
        "cls_mobile":    lead.pagespeed_cls_mobile,
        "inp_mobile":    lead.pagespeed_inp_mobile,
        "fcp_mobile":    lead.pagespeed_fcp_mobile,
        "checked_at":    lead.pagespeed_checked_at.isoformat() if lead.pagespeed_checked_at else None,
    }


@router.get("/{lead_id}/pagespeed")
def get_lead_pagespeed(lead_id: int, db: Session = Depends(get_db)):
    """Return the last stored PageSpeed values for this lead without a new API call."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")
    return _pagespeed_payload_lead(lead)


@router.post("/{lead_id}/pagespeed")
async def run_lead_pagespeed(lead_id: int, db: Session = Depends(get_db)):
    """Call Google PageSpeed Insights (mobile + desktop), persist results on the lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    website_url = lead.website_url
    if not website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")

    # DB-Verbindung vor externem PageSpeed-Call freigeben
    db.close()

    api_key = os.getenv("PAGESPEED_API_KEY") or os.getenv("GOOGLE_PAGESPEED_API_KEY", "")
    base = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params_base = {"url": website_url}
    if api_key:
        params_base["key"] = api_key

    async with httpx.AsyncClient(timeout=60.0) as client:
        mobile_resp, desktop_resp = await asyncio.gather(
            client.get(base, params={**params_base, "strategy": "mobile"}),
            client.get(base, params={**params_base, "strategy": "desktop"}),
        )

    def _score(resp) -> int | None:
        try:
            return round((resp.json()["categories"]["performance"]["score"] or 0) * 100)
        except Exception:
            return None

    def _audit(resp, key) -> float | None:
        try:
            return resp.json()["lighthouseResult"]["audits"][key]["numericValue"]
        except Exception:
            return None

    # Neue DB-Session zum Speichern
    db2 = SessionLocal()
    try:
        lead = db2.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead nicht gefunden")
        lead.pagespeed_mobile_score  = _score(mobile_resp)
        lead.pagespeed_desktop_score = _score(desktop_resp)
        lead.pagespeed_lcp_mobile    = _audit(mobile_resp, "largest-contentful-paint")
        lead.pagespeed_cls_mobile    = _audit(mobile_resp, "cumulative-layout-shift")
        lead.pagespeed_inp_mobile    = _audit(mobile_resp, "interaction-to-next-paint")
        lead.pagespeed_fcp_mobile    = _audit(mobile_resp, "first-contentful-paint")
        lead.pagespeed_checked_at    = datetime.utcnow()
        db2.commit()
        db2.refresh(lead)
        return _pagespeed_payload_lead(lead)
    finally:
        db2.close()


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


@router.post("/{lead_id}/domain-check")
async def domain_check_lead(lead_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)):
    """Manueller Domain-Check für einen Lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")
    if not lead.website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")
    website_url = lead.website_url

    # DB-Verbindung vor externem Check freigeben
    db.close()

    from services.domain_checker import check_domain
    result = await check_domain(website_url)

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        lead = db2.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead nicht gefunden")
        lead.domain_reachable   = result["reachable"]
        lead.domain_status_code = result.get("status_code")
        lead.domain_checked_at  = datetime.utcnow()
        db2.commit()
        return {
            "reachable":    lead.domain_reachable,
            "status_code":  lead.domain_status_code,
            "checked_at":   lead.domain_checked_at.isoformat(),
            "website_url":  lead.website_url,
        }
    finally:
        db2.close()


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
# Registers identical handlers under /api/customers/{lead_id}/... so that
# frontend calls to either prefix work transparently.

customers_alias_router = APIRouter(prefix="/api/customers", tags=["customers"])

customers_alias_router.add_api_route("/",                            list_leads,           methods=["GET"])
customers_alias_router.add_api_route("/",                            create_lead,          methods=["POST"],   response_model=LeadResponse)
customers_alias_router.add_api_route("/{lead_id}",                  get_lead,             methods=["GET"],    response_model=LeadResponse)
customers_alias_router.add_api_route("/{lead_id}",                  update_lead,          methods=["PATCH"])
customers_alias_router.add_api_route("/{lead_id}",                  delete_lead,          methods=["DELETE"])
customers_alias_router.add_api_route("/{lead_id}/analyze",          analyze_lead,         methods=["POST"])
customers_alias_router.add_api_route("/{lead_id}/convert",          convert_lead,         methods=["POST"])
customers_alias_router.add_api_route("/{lead_id}/enrich",           enrich_single_lead,   methods=["POST"])
customers_alias_router.add_api_route("/{lead_id}/latest-screenshot",get_latest_screenshot,methods=["GET"])
customers_alias_router.add_api_route("/{lead_id}/screenshot",       create_screenshot,    methods=["POST"])
customers_alias_router.add_api_route("/{lead_id}/profile",          get_lead_profile,     methods=["GET"])
customers_alias_router.add_api_route("/{lead_id}/audits",           get_lead_audits,      methods=["GET"])
customers_alias_router.add_api_route("/{lead_id}/extract-impressum",extract_impressum,    methods=["POST"])
customers_alias_router.add_api_route("/{lead_id}/qr-code",          get_qr_code,          methods=["GET"])
customers_alias_router.add_api_route("/{lead_id}/qr-code/refresh",  refresh_qr_code,      methods=["POST"])
customers_alias_router.add_api_route("/{lead_id}/pagespeed",        get_lead_pagespeed,   methods=["GET"])
customers_alias_router.add_api_route("/{lead_id}/pagespeed",        run_lead_pagespeed,   methods=["POST"])
customers_alias_router.add_api_route("/{lead_id}/domain-check",     domain_check_lead,    methods=["POST"])
