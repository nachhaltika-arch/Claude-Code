"""Betriebe von aussen hereinholen — CSV, Domainlisten, Einzelanlage (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/leads.py` hatte 2.575 Zeilen und
fuenfzig Funktionen. Neun davon tun dasselbe: Daten von aussen entgegennehmen
und daraus Betriebe machen — eine CSV, eine Liste von Domains, ein einzelner
Eintrag von Hand, und der Weg zurueck als Ausfuhr.

Sie teilen mit dem Rest der Datei **nichts** ausser dem Router und dem
Auftragszustand `import_jobs`; nachgemessen vor dem Schnitt, und beides ist
mitgewandert. Umgekehrt braucht der Rest von ihnen gar nichts.

**Der Router traegt dieselbe Sperre wie drueben.** Import ist Innendienst —
wer Betriebe anlegt, arbeitet am Bestand.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
from database import Lead, Project, AuditResult, get_db, SessionLocal
from services import betriebsname, lead_quellen
from services.base_urls import self_base_url
import asyncio
import csv
import httpx
import io
import json
import logging
import uuid

# Der Zustand laufender Domain-Import-Auftraege. Steht hier, weil ihn nur
# dieser Bereich anfasst — im ganzen uebrigen `leads.py` kam er nicht vor.
from pydantic import BaseModel
from routers.auth_router import require_innendienst

# `LeadResponse` bleibt in `leads.py` — dort haengt der Kundenweg daran.
from routers.leads import LeadResponse

import_jobs = {}

class DomainsTextInput(BaseModel):
    domains_text: str

class ManualLeadImport(BaseModel):
    company_name: str
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    website_url: str = ""
    city: str = ""
    trade: str = ""


router = APIRouter(prefix="/api/leads", tags=["leads-import"],
                   dependencies=[Depends(require_innendienst)])


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


def _extract_domains(roher_text: str) -> list:
    """Extract valid domains from text (one per line, comma or semicolon separated).

    Der Parameter hiess `text` und verdeckte damit `sqlalchemy.text` — in
    `leads.py` fiel das nicht auf, weil dort niemand in derselben Funktion
    eine Abfrage schrieb. Wer es getan haette, waere auf einen Fehler
    gestossen, den an dieser Stelle niemand erwartet (L-25, 22.08.2026).
    """
    import re
    domains = []
    seen = set()
    for line in re.split(r'[\n,;]', roher_text):
        cell = line.strip().strip('"').strip("'")
        clean = re.sub(r'^https?://', '', cell).replace('www.', '').split('/')[0].lower()
        if re.match(r'^[a-z0-9][a-z0-9\-\.]+\.[a-z]{2,}$', clean) and clean not in seen:
            domains.append(f'https://{clean}')
            seen.add(clean)
    return domains


async def _process_single_domain(url: str, clean: str, _session_factory, job_id: str) -> dict:
    """Process a single domain sequentially: Lead → pause → Audit → pause → Impressum.
    Uses short-lived DB sessions to avoid stale connections during long async operations."""
    import asyncio as _aio
    import logging as _log
    from datetime import datetime as _dt
    _logger = _log.getLogger('domain_import')

    result = {'url': url, 'status': 'created', 'lead_id': None, 'company_name': clean,
              'audit_status': 'pending', 'impressum_status': 'pending', 'score': None}

    # ── Step 1: Duplicate check + Lead creation (short-lived session) ──
    db = _session_factory()
    try:
        existing = db.query(Lead).filter(Lead.website_url.ilike(f'%{clean}%')).first()
        if existing:
            return {'url': url, 'status': 'already_exists', 'lead_id': existing.id,
                    'company_name': existing.display_name or existing.company_name,
                    'score': existing.analysis_score,
                    'audit_status': 'skipped', 'impressum_status': 'skipped'}

        lead = Lead(
            company_name=clean, website_url=url, contact_name='', phone='',
            email='', city='', trade='', notes='', website_screenshot='',
            status='new', lead_source='domain_import', analysis_score=0, geo_score=0,
            street='', house_number='', postal_code='', legal_form='',
            vat_id='', register_number='', register_court='',
            ceo_first_name='', ceo_last_name='', display_name='',
            created_at=_dt.utcnow(), updated_at=_dt.utcnow(),
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        lead_id = lead.id
        result['lead_id'] = lead_id
        _logger.info(f'Lead angelegt: {clean} (ID: {lead_id})')
    except Exception as e:
        try: db.rollback()
        except: pass
        _logger.error(f'Lead anlegen Fehler {clean}: {e}')
        return {'url': url, 'status': 'error', 'error': f'Lead: {str(e)}',
                'audit_status': 'failed', 'impressum_status': 'failed'}
    finally:
        db.close()

    await _aio.sleep(1)

    # ── Step 2: Audit (max 90s, no DB session needed) ──
    _logger.info(f'Starte Audit: {clean}')
    try:
        import httpx
        async with httpx.AsyncClient(timeout=90) as client:
            # Aufruf an den eigenen Server — über die interne Adresse, nicht
            # über das öffentliche Netz. Siehe services/base_urls.py.
            audit_base = self_base_url()
            r = await client.post(f'{audit_base}/api/audit/start',
                json={'website_url': url, 'lead_id': lead_id, 'company_name': clean})
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

    _logger.info(f'Warte 5s vor Impressum: {clean}')
    await _aio.sleep(5)

    # ── Step 3: Impressum (max 30s, fresh session for DB update) ──
    _logger.info(f'Starte Impressum: {clean}')
    try:
        from services.impressum_scraper import extract_contact_from_impressum
        imp = await _aio.wait_for(extract_contact_from_impressum(url), timeout=30.0)
        if imp.get('success'):
            data_imp = imp.get('data', {})
            db = _session_factory()
            try:
                lead = db.query(Lead).filter(Lead.id == lead_id).first()
                if not lead:
                    _logger.warning(f'Lead {lead_id} nicht mehr in DB gefunden')
                    result['impressum_status'] = 'failed'
                    return result
                updated_fields = []
                # Der Firmenname zuerst und nach eigener Regel: Der Import hat
                # ihn mit der Domain vorbelegt. Die Bedingung unten hielte das
                # Feld deshalb für gefüllt und würde den echten Namen aus dem
                # Impressum verwerfen — genau deshalb hieß am 17.08.2026 jeder
                # Betrieb in der Liste wie seine Domain.
                echter_name = betriebsname.uebernehmen(
                    lead.company_name, data_imp.get('company_name'), lead.website_url,
                )
                if echter_name:
                    lead.company_name = echter_name
                    updated_fields.append('company_name')

                for field in ['legal_form', 'ceo_first_name', 'ceo_last_name',
                              'street', 'house_number', 'postal_code', 'city', 'phone', 'email',
                              'vat_id', 'register_number', 'register_court', 'trade']:
                    if data_imp.get(field) and not getattr(lead, field, None):
                        setattr(lead, field, data_imp[field])
                        updated_fields.append(field)
                if not lead.contact_name and data_imp.get('ceo_first_name'):
                    lead.contact_name = ' '.join(filter(None, [data_imp.get('ceo_first_name'), data_imp.get('ceo_last_name')]))
                db.commit()
                result['impressum_status'] = 'completed'
                result['company_name'] = lead.company_name
                _logger.info(f'Impressum fertig: {clean} — {len(updated_fields)} Felder')
            except Exception as e:
                db.rollback()
                _logger.error(f'Impressum DB-Update Fehler {clean}: {type(e).__name__}: {e}')
                result['impressum_status'] = 'failed'
            finally:
                db.close()
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
        try:
            _logger.info(f'Import {job_id}: Starte {len(domains)} Domains')
            for i, url in enumerate(domains):
                clean = url.replace('https://', '').replace('http://', '')
                _logger.info(f'━━━ [{i+1}/{len(domains)}] {clean} ━━━')
                try:
                    result = await _aio.wait_for(
                        _process_single_domain(url, clean, SessionLocal, job_id),
                        timeout=150.0
                    )
                except _aio.TimeoutError:
                    _logger.warning(f'Domain komplett Timeout: {clean}')
                    result = {'url': url, 'status': 'timeout', 'audit_status': 'timeout', 'impressum_status': 'timeout', 'score': None}
                except Exception as domain_err:
                    _logger.error(f'Domain {clean} komplett fehlgeschlagen: {type(domain_err).__name__}: {domain_err}')
                    result = {'url': url, 'status': 'error', 'error': str(domain_err),
                              'audit_status': 'failed', 'impressum_status': 'failed', 'score': None}
                import_jobs[job_id]['results'].append(result)
                import_jobs[job_id]['processed'] = i + 1
                if i < len(domains) - 1:
                    _logger.info(f'Warte 10s vor nächster Domain...')
                    await _aio.sleep(10)
            import_jobs[job_id]['status'] = 'done'
            _logger.info(f'Import {job_id}: Fertig — {len(domains)} Domains verarbeitet')
        except Exception as e:
            _logger.error(f'Import {job_id} Fehler: {type(e).__name__}: {e}\n{_tb.format_exc()}')
            import_jobs[job_id]['status'] = 'error'
            import_jobs[job_id]['error'] = f'{type(e).__name__}: {str(e)}'
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
    roher_text = content.decode('utf-8', errors='ignore')
    domains = _extract_domains(roher_text)
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
        try:
            _logger.info(f'File Import {job_id}: Starte {len(domains)} Domains')
            for i, url in enumerate(domains):
                clean = url.replace('https://', '').replace('http://', '')
                _logger.info(f'━━━ [{i+1}/{len(domains)}] {clean} ━━━')
                try:
                    result = await _aio.wait_for(
                        _process_single_domain(url, clean, SessionLocal, job_id),
                        timeout=150.0
                    )
                except _aio.TimeoutError:
                    _logger.warning(f'Domain komplett Timeout: {clean}')
                    result = {'url': url, 'status': 'timeout', 'audit_status': 'timeout', 'impressum_status': 'timeout', 'score': None}
                except Exception as domain_err:
                    _logger.error(f'Domain {clean} komplett fehlgeschlagen: {type(domain_err).__name__}: {domain_err}')
                    result = {'url': url, 'status': 'error', 'error': str(domain_err),
                              'audit_status': 'failed', 'impressum_status': 'failed', 'score': None}
                import_jobs[job_id]['results'].append(result)
                import_jobs[job_id]['processed'] = i + 1
                if i < len(domains) - 1:
                    _logger.info(f'Warte 10s vor nächster Domain...')
                    await _aio.sleep(10)
            import_jobs[job_id]['status'] = 'done'
            _logger.info(f'File Import {job_id}: Fertig — {len(domains)} Domains verarbeitet')
        except Exception as e:
            _logger.error(f'File Import {job_id} Fehler: {type(e).__name__}: {e}\n{_tb.format_exc()}')
            import_jobs[job_id]['status'] = 'error'
            import_jobs[job_id]['error'] = f'{type(e).__name__}: {str(e)}'
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
        # Eine Schreibweise je Quelle — `manual` schreiben auch die drei
        # Frontend-Stellen, und der Quellenfilter vergleicht darauf (L-59).
        lead_source="manual",
        status="new",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    if lead.website_url:
        from services.lead_enrichment import enrich_lead_sync
        background_tasks.add_task(enrich_lead_sync, lead.id)

    return lead
