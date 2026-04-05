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


def _run_content_job(job_id: str, briefing_dict: dict, use_mock: bool,
                     company_name: str, city: str, trade: str) -> None:
    """Runs in a background thread. Updates _jobs[job_id] when done."""
    try:
        if use_mock:
            result = ContentWriterAgent.get_mock_content(company_name, city, trade)
        else:
            agent = ContentWriterAgent()
            result = agent.write_content(briefing_dict)

        if "error" in result:
            _jobs[job_id] = {"status": "error", "error": result["error"]}
        else:
            _jobs[job_id] = {"status": "done", "result": result}
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
