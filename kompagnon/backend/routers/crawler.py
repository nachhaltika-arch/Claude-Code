"""
Crawler REST API for KOMPAGNON.
POST /api/crawler/start/{customer_id}          → start background crawl
GET  /api/crawler/status/{customer_id}         → job status
GET  /api/crawler/results/{customer_id}        → crawled URL list
POST /api/crawler/scrape-content/{customer_id} → scrape content from crawled URLs
GET  /api/crawler/content/{customer_id}        → cached content results
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db, CrawlJob, CrawlResult, SessionLocal
from routers.auth_router import get_current_user, require_admin
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/crawler', tags=['crawler'])


@router.get('/status')
def crawler_status():
    """Prüft ob der Crawler verfügbar ist."""
    try:
        from services.crawler_service import crawl_website  # noqa: F401
        return {'status': 'available', 'engine': 'httpx+beautifulsoup4'}
    except ImportError as e:
        return {'status': 'unavailable', 'error': str(e)}


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


@router.post('/scrape-content/{customer_id}')
async def scrape_content(customer_id: int, db: Session = Depends(get_db)):
    """Scrapt Inhalte aller gecrawlten URLs und speichert sie in website_content_cache."""
    from bs4 import BeautifulSoup
    import httpx
    import json
    from datetime import datetime
    from urllib.parse import urljoin, urlparse

    FILE_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.csv'}

    # Ensure new columns exist
    for col_sql in [
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS full_text TEXT",
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS images TEXT",
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS files TEXT",
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS h3s TEXT DEFAULT '[]'",
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS links_internal TEXT DEFAULT '[]'",
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS links_external TEXT DEFAULT '[]'",
    ]:
        db.execute(text(col_sql))
    db.commit()

    url_list = [
        r.url for r in db.query(CrawlResult).filter(
            CrawlResult.customer_id == customer_id,
            CrawlResult.status_code == 200,
        ).limit(50).all()
    ]

    # DB-Verbindung vor den externen HTTP-Calls freigeben
    db.close()

    entries = []
    errors = []
    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=True,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,*/*;q=0.9',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.7',
        },
    ) as client:
        for crawl_url in url_list:
            try:
                res = await client.get(crawl_url)
                soup = BeautifulSoup(res.text, 'html.parser')
                base_url = crawl_url

                title = soup.find('title')
                meta  = soup.find('meta', attrs={'name': 'description'})
                h1    = soup.find('h1')
                h2s   = [h.get_text(strip=True) for h in soup.find_all('h2')[:5]]
                h3s   = [h.get_text(strip=True) for h in soup.find_all('h3')[:8]]

                # Extract image URLs (src attributes)
                images = []
                for img in soup.find_all('img', src=True):
                    src = img['src'].strip()
                    if src and not src.startswith('data:'):
                        images.append(urljoin(base_url, src))

                # Extract file links (href pointing to documents)
                files = []
                for a in soup.find_all('a', href=True):
                    href = a['href'].strip()
                    parsed = urlparse(href)
                    ext = parsed.path.lower()
                    if any(ext.endswith(fe) for fe in FILE_EXTENSIONS):
                        files.append(urljoin(base_url, href))

                # Interne und externe Links trennen
                from urllib.parse import urlparse as _urlparse
                base_domain = _urlparse(base_url).netloc
                links_internal = []
                links_external = []
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href'].strip()
                    if not href or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                        continue
                    if href.startswith('/') or base_domain in href:
                        full = urljoin(base_url, href)
                        if full not in links_internal:
                            links_internal.append(full)
                    elif href.startswith('http'):
                        if href not in links_external:
                            links_external.append(href)
                links_internal = links_internal[:30]
                links_external = links_external[:20]

                # Remove noise tags, then extract full text
                for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()
                full_text  = soup.get_text(separator='\n', strip=True)
                body_text  = ' '.join(full_text.split())  # compact for word count
                text_preview = body_text[:300]

                entries.append({
                    'customer_id':      customer_id,
                    'url':              crawl_url,
                    'title':            title.get_text(strip=True) if title else '',
                    'meta_description': meta.get('content', '') if meta else '',
                    'h1':               h1.get_text(strip=True) if h1 else '',
                    'h2s':              json.dumps(h2s, ensure_ascii=False),
                    'h3s':              json.dumps(h3s, ensure_ascii=False),
                    'text_preview':     text_preview,
                    'full_text':        full_text,
                    'images':           json.dumps(list(dict.fromkeys(images)), ensure_ascii=False),
                    'files':            json.dumps(list(dict.fromkeys(files)), ensure_ascii=False),
                    'links_internal':   json.dumps(links_internal, ensure_ascii=False),
                    'links_external':   json.dumps(links_external, ensure_ascii=False),
                    'word_count':       len(body_text.split()),
                    'scraped_at':       datetime.utcnow(),
                })
            except Exception as e:
                errors.append({'url': crawl_url, 'error': str(e)})

    # Neue Session zum Speichern der Ergebnisse
    db2 = SessionLocal()
    try:
        for entry in entries:
            existing = db2.execute(
                text("SELECT id FROM website_content_cache WHERE customer_id=:c AND url=:u"),
                {"c": customer_id, "u": entry['url']},
            ).fetchone()
            if existing:
                db2.execute(
                    text(
                        "UPDATE website_content_cache SET "
                        "title=:title, meta_description=:meta_description, h1=:h1, "
                        "h2s=:h2s, h3s=:h3s, text_preview=:text_preview, full_text=:full_text, "
                        "images=:images, files=:files, links_internal=:links_internal, "
                        "links_external=:links_external, word_count=:word_count, "
                        "scraped_at=:scraped_at WHERE id=:id"
                    ),
                    {**entry, 'id': existing[0]},
                )
            else:
                db2.execute(
                    text(
                        "INSERT INTO website_content_cache "
                        "(customer_id, url, title, meta_description, h1, h2s, h3s, "
                        "text_preview, full_text, images, files, links_internal, links_external, "
                        "word_count, scraped_at) "
                        "VALUES (:customer_id, :url, :title, :meta_description, :h1, "
                        ":h2s, :h3s, :text_preview, :full_text, :images, :files, "
                        ":links_internal, :links_external, :word_count, :scraped_at)"
                    ),
                    entry,
                )
        db2.commit()
    finally:
        db2.close()

    results = [{**e, 'scraped_at': e['scraped_at'].isoformat()} for e in entries] + errors
    return {'scraped': len(entries), 'results': results}


@router.get('/content/{customer_id}')
def get_content(customer_id: int, db: Session = Depends(get_db)):
    """Gibt gecachte Content-Scraping-Ergebnisse für customer_id zurück."""
    import json

    rows = db.execute(
        text(
            "SELECT id, customer_id, url, title, meta_description, h1, h2s, "
            "text_preview, word_count, scraped_at, "
            "COALESCE(full_text, '') as full_text, "
            "COALESCE(images, '[]') as images, "
            "COALESCE(files, '[]') as files, "
            "COALESCE(h3s, '[]') as h3s, "
            "COALESCE(links_internal, '[]') as links_internal, "
            "COALESCE(links_external, '[]') as links_external "
            "FROM website_content_cache WHERE customer_id = :c ORDER BY scraped_at DESC"
        ),
        {"c": customer_id},
    ).fetchall()

    result = []
    for r in rows:
        def _parse(val):
            try: return json.loads(val) if val else []
            except: return []
        result.append({
            'id':               r[0],
            'customer_id':      r[1],
            'url':              r[2],
            'title':            r[3],
            'meta_description': r[4],
            'h1':               r[5],
            'h2s':              _parse(r[6]),
            'text_preview':     r[7],
            'word_count':       r[8],
            'scraped_at':       r[9].isoformat() if r[9] else None,
            'full_text':        r[10],
            'images':           _parse(r[11]),
            'files':            _parse(r[12]),
            'h3s':              _parse(r[13]),
            'links_internal':   _parse(r[14]),
            'links_external':   _parse(r[15]),
        })
    return result
