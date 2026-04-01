"""
Crawler REST API for KOMPAGNON.
POST /api/crawler/start/{customer_id}  → start background crawl
GET  /api/crawler/status/{customer_id} → job status
GET  /api/crawler/results/{customer_id} → crawled URL list
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db, CrawlJob, CrawlResult
from routers.auth_router import get_current_user, require_admin
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/crawler', tags=['crawler'])


def _run_crawl(job_id: int, customer_id: int, start_url: str, max_pages: int):
    """Background task: run crawler and persist results."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job:
            return
        job.status = 'running'
        job.started_at = datetime.utcnow()
        db.commit()

        from services.crawler_service import crawl_website
        results = crawl_website(start_url, max_pages)

        for r in results:
            db.add(CrawlResult(
                customer_id=customer_id,
                job_id=job_id,
                url=r['url'],
                status_code=r.get('status_code'),
                depth=r.get('depth', 0),
                load_time=r.get('load_time'),
                crawled_at=datetime.utcnow(),
            ))

        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        job.total_urls = len(results)
        db.commit()
        logger.info(f'Crawl job {job_id} abgeschlossen: {len(results)} URLs')
    except Exception as e:
        logger.exception(f'Crawl job {job_id} Fehler: {e}')
        try:
            job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
            if job:
                job.status = 'failed'
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post('/start/{customer_id}')
def start_crawl(
    customer_id: int,
    data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Starte Crawl für Kunden im Hintergrund. Body: {url, max_pages?}"""
    start_url = data.get('url', '').strip()
    if not start_url:
        raise HTTPException(400, 'URL fehlt')
    if not start_url.startswith('http'):
        start_url = 'https://' + start_url
    max_pages = min(int(data.get('max_pages', 50)), 200)

    # Cancel any running job for this customer
    running = db.query(CrawlJob).filter(
        CrawlJob.customer_id == customer_id,
        CrawlJob.status.in_(['pending', 'running']),
    ).first()
    if running:
        running.status = 'failed'
        running.completed_at = datetime.utcnow()
        db.commit()

    job = CrawlJob(customer_id=customer_id, status='pending')
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_crawl, job.id, customer_id, start_url, max_pages)
    return {'job_id': job.id, 'status': 'pending', 'url': start_url, 'max_pages': max_pages}


@router.get('/status/{customer_id}')
def get_status(customer_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Aktueller Job-Status für Kunden."""
    job = (
        db.query(CrawlJob)
        .filter(CrawlJob.customer_id == customer_id)
        .order_by(CrawlJob.id.desc())
        .first()
    )
    if not job:
        return {'status': 'none', 'job_id': None, 'total_urls': 0}
    duration = None
    if job.started_at and job.completed_at:
        duration = round((job.completed_at - job.started_at).total_seconds())
    elif job.started_at:
        duration = round((datetime.utcnow() - job.started_at).total_seconds())
    return {
        'job_id': job.id,
        'status': job.status,
        'started_at': str(job.started_at)[:19] if job.started_at else None,
        'completed_at': str(job.completed_at)[:19] if job.completed_at else None,
        'total_urls': job.total_urls or 0,
        'duration_seconds': duration,
    }


@router.get('/results/{customer_id}')
def get_results(
    customer_id: int,
    job_id: int = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """URL-Ergebnisse für den letzten (oder angegebenen) Job."""
    if not job_id:
        job = (
            db.query(CrawlJob)
            .filter(CrawlJob.customer_id == customer_id, CrawlJob.status == 'completed')
            .order_by(CrawlJob.id.desc())
            .first()
        )
        if not job:
            return {'results': [], 'job_id': None}
        job_id = job.id

    results = (
        db.query(CrawlResult)
        .filter(CrawlResult.job_id == job_id)
        .order_by(CrawlResult.depth, CrawlResult.id)
        .all()
    )
    return {
        'job_id': job_id,
        'results': [
            {
                'url': r.url,
                'status_code': r.status_code,
                'depth': r.depth,
                'load_time': float(r.load_time) if r.load_time else None,
                'crawled_at': str(r.crawled_at)[:19] if r.crawled_at else None,
            }
            for r in results
        ],
    }
