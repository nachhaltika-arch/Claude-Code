"""
Content Scraper API
POST /api/projects/{project_id}/scrape          - Start scrape job (admin)
GET  /api/projects/{project_id}/scrape-status   - Latest job status
GET  /api/projects/{project_id}/scraped-content - All scraped pages
"""
import json
import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, ProjectScrapeJob, ProjectScrapedPage, Project
from routers.auth_router import require_admin, require_any_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["content-scraper"])


# ── Background task ────────────────────────────────────────────────────────────

def _run_content_scrape(job_id: int, project_id: int, website_url: str):
    """Synchronous wrapper — runs the async scrape in a fresh event loop."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        job = db.query(ProjectScrapeJob).filter(ProjectScrapeJob.id == job_id).first()
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()

        # Delete old scraped pages for this project
        db.query(ProjectScrapedPage).filter(
            ProjectScrapedPage.project_id == project_id
        ).delete()
        db.commit()

        # Run async scraper
        from services.content_scraper import scrape_all_pages
        results = asyncio.run(scrape_all_pages(website_url, max_pages=20))

        for item in results:
            page = ProjectScrapedPage(
                project_id=project_id,
                url=item.get("url", ""),
                page_title=item.get("page_title", ""),
                meta_description=item.get("meta_description", ""),
                h1=item.get("h1", ""),
                h2_list=item.get("h2_list", "[]"),
                paragraphs=item.get("paragraphs", "[]"),
                images=item.get("images", "[]"),
                contact_phone=item.get("contact_phone", ""),
                contact_email=item.get("contact_email", ""),
                contact_address=item.get("contact_address", ""),
            )
            db.add(page)

        job.status = "done"
        job.completed_at = datetime.utcnow()
        job.total_pages = len(results)
        db.commit()

    except Exception as e:
        logger.error("Content scrape failed for project %s: %s", project_id, e)
        try:
            job = db.query(ProjectScrapeJob).filter(ProjectScrapeJob.id == job_id).first()
            if job:
                job.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/{project_id}/scrape-full")
async def scrape_full_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Single-page full analysis: SEO, text, assets, links, contact.
    Persists result in projects.scrape_full_data for fast GET later.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    url = project.website_url or ""
    if not url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")
    if not url.startswith("http"):
        url = "https://" + url
    from services.content_scraper import scrape_page_full
    result = await scrape_page_full(url)

    # Persist in DB
    try:
        project.scrape_full_data = json.dumps(result, ensure_ascii=False)
        project.scrape_full_at   = datetime.utcnow()
        db.commit()
    except Exception as e:
        logger.warning(f"scrape-full persist error project {project_id}: {e}")
        db.rollback()

    return result


@router.get("/{project_id}/scrape-full")
def get_scrape_full_cached(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Returns cached scrape-full result. Fast, no network call."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    if not project.scrape_full_data:
        return {"status": "no_cache", "message": "Noch kein Scrape durchgeführt"}
    try:
        data = json.loads(project.scrape_full_data)
    except json.JSONDecodeError as e:
        logger.error(f"scrape_full_data parse error project {project_id}: {e}")
        return {"status": "parse_error", "message": str(e)}
    data["_cached_at"] = str(project.scrape_full_at)[:19] if project.scrape_full_at else None
    return data


@router.post("/{project_id}/scrape")
def start_scrape(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    website_url = project.website_url or ""
    if not website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL am Projekt hinterlegt")

    # Check if a job is already running
    running = (
        db.query(ProjectScrapeJob)
        .filter(ProjectScrapeJob.project_id == project_id, ProjectScrapeJob.status == "running")
        .first()
    )
    if running:
        return {"status": "already_running", "job_id": running.id}

    job = ProjectScrapeJob(project_id=project_id, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_content_scrape, job.id, project_id, website_url)
    return {"job_id": job.id, "status": "started"}


@router.get("/{project_id}/scrape-status")
def scrape_status(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    job = (
        db.query(ProjectScrapeJob)
        .filter(ProjectScrapeJob.project_id == project_id)
        .order_by(ProjectScrapeJob.id.desc())
        .first()
    )
    if not job:
        return {"status": "none", "total_pages": 0, "started_at": None, "completed_at": None}
    return {
        "status":       job.status,
        "total_pages":  job.total_pages,
        "started_at":   str(job.started_at)[:16] if job.started_at else None,
        "completed_at": str(job.completed_at)[:16] if job.completed_at else None,
    }


@router.get("/{project_id}/scraped-content")
def scraped_content(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    pages = (
        db.query(ProjectScrapedPage)
        .filter(ProjectScrapedPage.project_id == project_id)
        .order_by(ProjectScrapedPage.id)
        .all()
    )

    def _parse(val, fallback):
        try:
            return json.loads(val) if val else fallback
        except Exception:
            return fallback

    return [
        {
            "id":               p.id,
            "url":              p.url,
            "page_title":       p.page_title or "",
            "meta_description": p.meta_description or "",
            "h1":               p.h1 or "",
            "h2_list":          _parse(p.h2_list, []),
            "paragraphs":       _parse(p.paragraphs, []),
            "images":           _parse(p.images, []),
            "contact_phone":    p.contact_phone or "",
            "contact_email":    p.contact_email or "",
            "contact_address":  p.contact_address or "",
            "scraped_at":       str(p.scraped_at)[:16] if p.scraped_at else "",
        }
        for p in pages
    ]
