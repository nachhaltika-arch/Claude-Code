"""
KI Agent API routes.
POST /api/agents/{project_id}/content       - Start content writer job (returns job_id)
GET  /api/agents/jobs/{job_id}              - Poll job status
POST /api/agents/{project_id}/seo           - Run SEO/GEO agent
POST /api/agents/{project_id}/qa            - Run QA agent
POST /api/agents/{project_id}/review        - Run review agent
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import Project, get_db
from agents import (
    ContentWriterAgent,
    SeoGeoAgent,
    QaAgent,
    ReviewAgent,
)
import os
import asyncio
import uuid
import threading
from functools import partial

router = APIRouter(prefix="/api/agents", tags=["agents"])

# ── In-memory job store ────────────────────────────────────────────────────────
# { job_id: { "status": "running"|"done"|"error", "result": ..., "error": ... } }
_jobs: dict = {}


def _json_to_html(data: dict, context: dict | None = None) -> str:
    ctx = context or {}
    primary_color   = ctx.get('brand_primary_color')   or '#0d6efd'
    secondary_color = ctx.get('brand_secondary_color') or '#1a2332'
    font_primary    = ctx.get('brand_font_primary')    or '-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif'

    hero     = data.get('hero_headline', '')
    subline  = data.get('hero_subline', '')
    about    = data.get('about_text', '')
    services = data.get('service_texts', {})
    faqs     = data.get('faq_items', [])
    cta      = data.get('local_cta', '')

    service_cards = ''
    if isinstance(services, dict):
        for key, val in services.items():
            service_cards += (
                f'<div style="background:white;border-radius:8px;padding:24px;'
                f'box-shadow:0 2px 8px rgba(0,0,0,0.1)">'
                f'<h3 style="margin-bottom:12px;color:{primary_color}">{key}</h3>'
                f'<p style="color:#555;line-height:1.6">{val}</p></div>'
            )

    faq_html = ''
    if isinstance(faqs, list):
        for item in faqs:
            q = item.get('question', '') if isinstance(item, dict) else ''
            a = item.get('answer', '')   if isinstance(item, dict) else ''
            faq_html += (
                f'<div style="border-bottom:1px solid #eee;padding:20px 0">'
                f'<h3 style="margin-bottom:8px;font-size:1rem;color:{primary_color}">{q}</h3>'
                f'<p style="color:#555;line-height:1.6">{a}</p></div>'
            )

    hero_block = (
        f'<div style="background:{primary_color};color:white;padding:80px 40px;text-align:center">'
        f'<h1 style="font-size:2.5rem;font-weight:700;margin-bottom:16px">{hero}</h1>'
        f'<p style="font-size:1.2rem;opacity:0.9">{subline}</p></div>'
    ) if hero else ''

    about_block = (
        f'<div style="padding:60px 40px;max-width:1200px;margin:0 auto">'
        f'<h2 style="font-size:1.8rem;margin-bottom:20px;color:{primary_color}">Über uns</h2>'
        f'<p style="line-height:1.7;color:#555">{about}</p></div>'
    ) if about else ''

    services_block = (
        f'<div style="background:#f8f9fa;padding:60px 40px">'
        f'<h2 style="text-align:center;margin-bottom:40px;font-size:1.8rem;color:{primary_color}">Unsere Leistungen</h2>'
        f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));'
        f'gap:24px;max-width:1200px;margin:0 auto">{service_cards}</div></div>'
    ) if service_cards else ''

    faq_block = (
        f'<div style="padding:60px 40px;max-width:800px;margin:0 auto">'
        f'<h2 style="margin-bottom:30px;font-size:1.8rem;color:{primary_color}">Häufige Fragen</h2>'
        f'{faq_html}</div>'
    ) if faq_html else ''

    cta_block = (
        f'<div style="background:{secondary_color};color:white;padding:60px 40px;text-align:center">'
        f'<h2 style="font-size:1.8rem;margin-bottom:20px">{cta}</h2>'
        f'<a href="#" style="display:inline-block;background:{primary_color};color:white;'
        f'padding:14px 32px;border-radius:6px;text-decoration:none;font-weight:600;'
        f'margin-top:8px">Jetzt Kontakt aufnehmen</a></div>'
    ) if cta else ''

    return (
        '<!DOCTYPE html><html><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<style>*{{box-sizing:border-box;margin:0;padding:0}}'
        f'body{{font-family:{font_primary}}}</style>'
        f'</head><body>{hero_block}{about_block}{services_block}{faq_block}{cta_block}</body></html>'
    )


def _run_content_job(job_id: str, briefing_dict: dict, use_mock: bool,
                     company_name: str, city: str, trade: str) -> None:
    """Runs in a background thread. Updates _jobs[job_id] when done."""
    try:
        if use_mock:
            result = ContentWriterAgent.get_mock_content(company_name, city, trade)
        else:
            agent = ContentWriterAgent()
            result = agent.write_content(briefing_dict)  # full dict incl. context fields

        if "error" in result:
            _jobs[job_id] = {"status": "error", "error": result["error"]}
        else:
            result_html = _json_to_html(result, briefing_dict) if isinstance(result, dict) else result
            _jobs[job_id] = {"status": "done", "result": result, "result_html": result_html}
    except Exception as e:
        _jobs[job_id] = {"status": "error", "error": str(e)}


class ContentBriefing(BaseModel):
    company_name: str = ""
    city: str = ""
    trade: str = ""
    usp: str = ""
    services: list[str] = []
    target_audience: str = ""
    page_name: str = "Startseite"
    zweck: str = ""
    ziel_keyword: str = ""
    cta_text: str = ""
    team_size: int = 1
    team_info: str = ""
    years_in_business: int = 0
    awards_or_certifications: list[str] = []
    # Context fields from audit / pagespeed / crawler / briefing
    audit_score: int | None = None
    audit_problems: list[str] = []
    pagespeed_mobile: int | None = None
    crawler_titles: list[str] = []
    briefing_usp: str = ""
    briefing_leistungen: str = ""
    briefing_zielgruppe: str = ""
    # Brand design context
    brand_primary_color: str | None = None
    brand_secondary_color: str | None = None
    brand_font_primary: str | None = None
    brand_design_style: str | None = None


class CompanyData(BaseModel):
    company_name: str
    street: str
    postal_code: str
    city: str
    country: str = "DE"
    phone: str
    email: str
    website: str
    services: list[str]
    opening_hours: dict
    latitude: float = None
    longitude: float = None
    business_type: str = "LocalBusiness"


class QaInput(BaseModel):
    checklist_data: dict
    test_results: dict


class ReviewInput(BaseModel):
    customer_name: str
    company_name: str
    project_summary: str
    platform: str = "google"


@router.post("/{project_id}/content")
def start_content_agent(
    project_id: int,
    briefing: ContentBriefing,
    db: Session = Depends(get_db),
):
    """Start content writer job. Returns job_id immediately — poll /api/agents/jobs/{job_id}."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running"}

    use_mock = not os.getenv("ANTHROPIC_API_KEY")
    t = threading.Thread(
        target=_run_content_job,
        args=(job_id, briefing.dict(), use_mock,
              briefing.company_name, briefing.city, briefing.trade),
        daemon=True,
    )
    t.start()

    return {"job_id": job_id, "status": "running"}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    """Poll job status. Returns status running|done|error + result or error message."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")
    # Clean up finished jobs after first successful read
    if job["status"] in ("done", "error"):
        _jobs.pop(job_id, None)
    return job


@router.post("/{project_id}/seo")
def run_seo_agent(
    project_id: int,
    company_data: CompanyData,
    db: Session = Depends(get_db),
):
    """Run SEO/GEO agent for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        use_mock = not os.getenv("ANTHROPIC_API_KEY")
        agent = SeoGeoAgent() if not use_mock else None

        company_dict = company_data.dict()

        if agent:
            result = agent.generate_seo(company_dict)
        else:
            result = SeoGeoAgent.get_mock_seo(
                company_data.company_name,
                company_data.city,
            )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "project_id": project_id,
            "agent": "SeoGeoAgent",
            "result": result,
            "status": "success",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")


@router.post("/{project_id}/qa")
def run_qa_agent(
    project_id: int,
    qa_input: QaInput,
    db: Session = Depends(get_db),
):
    """Run QA agent for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        use_mock = not os.getenv("ANTHROPIC_API_KEY")
        agent = QaAgent() if not use_mock else None

        if agent:
            result = agent.conduct_qa(
                project_id=project_id,
                checklist_data=qa_input.checklist_data,
                test_results=qa_input.test_results,
            )
        else:
            result = QaAgent.get_mock_qa(project_id)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "project_id": project_id,
            "agent": "QaAgent",
            "result": result,
            "status": "success",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")


@router.post("/{project_id}/review")
def run_review_agent(
    project_id: int,
    review_input: ReviewInput,
    db: Session = Depends(get_db),
):
    """Run review agent for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        use_mock = not os.getenv("ANTHROPIC_API_KEY")
        agent = ReviewAgent() if not use_mock else None

        if agent:
            result = agent.generate_review_request(
                customer_name=review_input.customer_name,
                company_name=review_input.company_name,
                project_summary=review_input.project_summary,
                platform=review_input.platform,
            )
        else:
            result = ReviewAgent.get_mock_review(
                review_input.customer_name,
                review_input.company_name,
                review_input.platform,
            )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "project_id": project_id,
            "agent": "ReviewAgent",
            "result": result,
            "status": "success",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")
