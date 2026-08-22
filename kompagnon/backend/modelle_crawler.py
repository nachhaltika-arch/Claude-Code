"""Die Modelle der Website-Erhebung (L-25).

**Warum eigene Datei, 22.08.2026.** `database.py` hatte 1.361 Zeilen und 39
Modellklassen. Auftraege und Ergebnisse des Crawlers, dazu die ausgelesenen Seiten
eines Projekts.

**Wichtig:** Diese Datei wird von `database.py` am Ende importiert. Ohne das
waere sie nie geladen, und die `relationship()`-Aufrufe der anderen Modelle
faenden ihre Gegenseite nicht — mit einem Fehler zur Laufzeit an einer
Stelle, die mit der Ursache nichts zu tun hat.
`tests/test_modelle_vollstaendig.py` haelt das fest.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text

from database import Base


class CrawlJob(Base):
    """Background crawl job."""
    __tablename__ = "crawl_jobs"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=True)
    status = Column(String(20), default='pending')   # pending|running|completed|failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_urls = Column(Integer, default=0)


class CrawlResult(Base):
    """Single URL result from a crawl job."""
    __tablename__ = "crawl_results"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=True)
    job_id = Column(Integer, ForeignKey('crawl_jobs.id', ondelete='CASCADE'), nullable=True)
    url = Column(String(2000), nullable=False)
    status_code = Column(Integer, nullable=True)
    depth = Column(Integer, default=0)
    load_time = Column(Float, nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow)


class ProjectScrapedPage(Base):
    __tablename__ = "project_scraped_pages"
    id                = Column(Integer, primary_key=True)
    project_id        = Column(Integer, ForeignKey("projects.id"), nullable=False)
    url               = Column(String, nullable=False)
    page_title        = Column(String)
    meta_description  = Column(Text)
    h1                = Column(String)
    h2_list           = Column(Text)       # JSON-Array als String
    paragraphs        = Column(Text)       # JSON-Array als String
    images            = Column(Text)       # JSON-Array {src, alt} als String
    contact_phone     = Column(String)
    contact_email     = Column(String)
    contact_address   = Column(Text)
    scraped_at        = Column(DateTime, default=datetime.utcnow)


class ProjectScrapeJob(Base):
    __tablename__ = "project_scrape_jobs"
    id           = Column(Integer, primary_key=True)
    project_id   = Column(Integer, nullable=False)
    status       = Column(String, default="pending")  # pending/running/done/failed
    total_pages  = Column(Integer, default=0)
    started_at   = Column(DateTime)
    completed_at = Column(DateTime)
