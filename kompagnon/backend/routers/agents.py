"""
KI Agent API routes.
POST /api/agents/content/{project_id} - Run content writer
POST /api/agents/seo/{project_id} - Run SEO/GEO agent
POST /api/agents/qa/{project_id} - Run QA agent
POST /api/agents/review/{project_id} - Run review agent
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

router = APIRouter(prefix="/api/agents", tags=["agents"])


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
    awards_or_certifications: list[str] = None


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
def run_content_agent(
    project_id: int,
    briefing: ContentBriefing,
    db: Session = Depends(get_db),
):
    """Run content writer agent for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        use_mock = not os.getenv("ANTHROPIC_API_KEY")
        agent = ContentWriterAgent() if not use_mock else None

        briefing_dict = briefing.dict()

        if agent:
            result = agent.write_content(briefing_dict)
        else:
            result = ContentWriterAgent.get_mock_content(
                briefing.company_name,
                briefing.city,
                briefing.trade,
            )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "project_id": project_id,
            "agent": "ContentWriterAgent",
            "result": result,
            "status": "success",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")


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
