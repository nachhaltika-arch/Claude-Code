"""Was ueber die Website eines Kunden erhoben wird (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/projects.py` hatte 1.919 Zeilen
— und das **nach** der ersten Aufteilung im August, bei der schon
`projects_netlify`, `projects_content`, `projects_sichtbarkeit` und
`projects_public` entstanden sind. Acht Routen, die alle dasselbe tun: hinschauen und aufschreiben, was da
ist — Inhalte auslesen, Hosting pruefen, Domain pruefen, Bildschirmfotos
vorher und nachher.

Transitiv gemessen samt Modulkonstanten: Geteilt ist nur `logger`. Der
Router kommt wie drueben aus `projects_router.py` — dort stehen die drei
Router mit ihren verschiedenen Sperren an einer Stelle.
"""
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from database import Lead
from database import Project
from database import SessionLocal
from database import get_db
from datetime import datetime
from routers.auth_router import get_current_user
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

from routers.projects_router import router

logger = logging.getLogger(__name__)


# **Hier stand `POST /{project_id}/scrape`** — 88 Zeilen, entfernt am
# 01.09.2026 (L-105). Ebenfalls ein Doppelweg: Dieselbe Sache — die
# Website nach Farben, Schriften und Logo absuchen — macht
# `POST /api/branddesign/{lead_id}/scrape`, und **die** ruft die
# Markendesign-Werkstatt wirklich auf.
#
# **Beim ersten Anlauf haette ich die falsche geloescht:** Der
# naheliegende Vergleich war `/api/crawler/scrape-content/{id}`, und der
# holt **Inhalte**, keine Markenfarben. Zwei Routen mit demselben Wort im
# Namen sind noch lange nicht dieselbe Sache.


@router.post("/{project_id}/hosting-scan")
async def hosting_scan(
    project_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
):
    """Scannt Hosting, DNS, WHOIS und WordPress-Erkennung für das Projekt.
    Cache: liefert gespeicherten Scan wenn < 12h alt (außer force=true).
    """
    from services.hosting_scraper import scrape_hosting_info

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    website_url = getattr(project, "website_url", None)
    if not website_url:
        return {"error": "Keine Website-URL im Projekt hinterlegt"}

    if not website_url.startswith("http"):
        website_url = "https://" + website_url

    # ── Cache-Check: 12h TTL ──
    row = db.execute(text(
        "SELECT hosting_provider, hosting_org, hosting_ip, hosting_country, "
        "dns_provider, nameservers, domain_registrar, domain_created, domain_expires, "
        "server_software, wordpress_hosting, is_wordpress, detected_technologies, "
        "hosting_checked_at FROM projects WHERE id = :id"
    ), {"id": project_id}).fetchone()

    if not force and row and row[13]:  # hosting_checked_at
        age = (datetime.utcnow() - row[13]).total_seconds()
        if age < 43200:  # 12h
            logger.info(f"hosting-scan cache hit project {project_id} ({int(age/60)}min alt)")
            return {
                "hosting_provider":      row[0],
                "hosting_org":           row[1],
                "hosting_ip":            row[2],
                "hosting_country":       row[3],
                "dns_provider":          row[4],
                "nameservers":           row[5],
                "domain_registrar":      row[6],
                "domain_created":        row[7],
                "domain_expires":        row[8],
                "server_software":       row[9],
                "wordpress_hosting":     row[10],
                "is_wordpress":          row[11],
                "detected_technologies": row[12],
                "hosting_checked_at":    row[13].isoformat() if row[13] else None,
                "website_url":           website_url,
                "_cached":               True,
                "_cache_age_minutes":    int(age / 60),
            }

    # DB-Verbindung vor externem hosting scrape freigeben
    db.close()

    data = await scrape_hosting_info(website_url)

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        db2.execute(text("""
            UPDATE projects SET
                hosting_provider    = :hosting_provider,
                hosting_org         = :hosting_org,
                hosting_ip          = :hosting_ip,
                hosting_country     = :hosting_country,
                dns_provider        = :dns_provider,
                nameservers         = :nameservers,
                domain_registrar    = :domain_registrar,
                domain_created      = :domain_created,
                domain_expires      = :domain_expires,
                server_software     = :server_software,
                wordpress_hosting        = :wordpress_hosting,
                is_wordpress             = :is_wordpress,
                detected_technologies    = :detected_technologies,
                hosting_checked_at       = NOW()
            WHERE id = :project_id
        """), {
            "project_id":            project_id,
            "hosting_provider":      data.get("hosting_provider"),
            "hosting_org":           data.get("hosting_org"),
            "hosting_ip":            data.get("ip_address"),
            "hosting_country":       data.get("country"),
            "dns_provider":          data.get("dns_provider"),
            "nameservers":           ",".join(data.get("nameservers") or []) or None,
            "domain_registrar":      data.get("registrar"),
            "domain_created":        data.get("domain_created"),
            "domain_expires":        data.get("domain_expires"),
            "server_software":       data.get("server_software"),
            "wordpress_hosting":     data.get("wordpress_hosting"),
            "is_wordpress":          data.get("is_wordpress"),
            "detected_technologies": ",".join(data.get("detected_technologies") or []) or None,
        })
        db2.commit()
    finally:
        db2.close()

    return {
        "hosting_provider":      data.get("hosting_provider"),
        "hosting_org":           data.get("hosting_org"),
        "hosting_ip":            data.get("ip_address"),
        "hosting_country":       data.get("country"),
        "dns_provider":          data.get("dns_provider"),
        "nameservers":           ",".join(data.get("nameservers") or []) or None,
        "domain_registrar":      data.get("registrar"),
        "domain_created":        data.get("domain_created"),
        "domain_expires":        data.get("domain_expires"),
        "server_software":       data.get("server_software"),
        "wordpress_hosting":     data.get("wordpress_hosting"),
        "is_wordpress":          data.get("is_wordpress"),
        "detected_technologies": ",".join(data.get("detected_technologies") or []) or None,
        "hosting_checked_at":    datetime.utcnow().isoformat(),
        "website_url":           website_url,
    }


@router.get("/{project_id}/hosting-info")
def hosting_info(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Gibt gespeicherte Hosting-Infos des Projekts zurück (kein neuer Scan)."""
    row = db.execute(text("""
        SELECT hosting_provider, hosting_org, hosting_ip, hosting_country,
               dns_provider, nameservers, domain_registrar, domain_created,
               domain_expires, server_software, wordpress_hosting, is_wordpress,
               detected_technologies, hosting_checked_at, website_url
        FROM projects WHERE id = :id
    """), {"id": project_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    return dict(row)


@router.post("/{project_id}/domain-check")
async def domain_check_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Prüft DNS, WHOIS und SSL für die Website-URL des Projekts."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead = project.lead
    website_url = getattr(project, "website_url", None) or (lead.website_url if lead else None)
    if not website_url:
        raise HTTPException(400, "Keine Website-URL hinterlegt")

    url = website_url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    # DB-Verbindung vor externen Checks freigeben
    db.close()

    from urllib.parse import urlparse
    import socket
    import ssl
    import datetime as dt

    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path

    result = {
        "domain": domain,
        "url": url,
        "dns": None,
        "ssl": None,
        "ssl_expiry": None,
        "ssl_days_remaining": None,
        "reachable": False,
        "status_code": None,
        "redirect_url": None,
        "error": None,
    }

    # DNS check
    try:
        ip = socket.gethostbyname(domain)
        result["dns"] = ip
    except Exception as e:
        result["error"] = f"DNS-Fehler: {str(e)}"
        return result

    # Reachability check
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
            result["reachable"] = True
            result["status_code"] = resp.status_code
            if str(resp.url) != url:
                result["redirect_url"] = str(resp.url)
    except Exception as e:
        result["error"] = f"Erreichbarkeit: {str(e)}"

    # SSL cert expiry
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5)
            s.connect((domain, 443))
            cert = s.getpeercert()
            expiry_str = cert.get("notAfter", "")
            if expiry_str:
                expiry = dt.datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
                days = (expiry - dt.datetime.utcnow()).days
                result["ssl"] = "valid"
                result["ssl_expiry"] = expiry.strftime("%d.%m.%Y")
                result["ssl_days_remaining"] = days
    except Exception:
        result["ssl"] = "none_or_error"

    # Persist reachability to project — neue Session
    db2 = SessionLocal()
    try:
        project = db2.query(Project).filter(Project.id == project_id).first()
        if project:
            project.domain_reachable   = result["reachable"]
            project.domain_status_code = result.get("status_code")
            project.domain_checked_at  = datetime.utcnow()
            db2.commit()
    except Exception:
        db2.rollback()
    finally:
        db2.close()

    return result


@router.post("/{project_id}/screenshot/before")
async def screenshot_before(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Nimmt einen Before-Screenshot der alten Website auf."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    if not project.website_url:
        raise HTTPException(status_code=400, detail="Keine website_url am Projekt hinterlegt")

    from services.screenshot import capture_screenshot
    b64 = await capture_screenshot(project.website_url)
    if not b64:
        raise HTTPException(status_code=502, detail="Screenshot konnte nicht erstellt werden")

    project.screenshot_before      = b64
    project.screenshot_before_date = datetime.utcnow()
    project.screenshot_url_before  = project.website_url
    db.commit()

    return {"success": True, "screenshot_url": f"data:image/jpeg;base64,{b64}"}


@router.post("/{project_id}/screenshot/after")
async def screenshot_after(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Nimmt einen After-Screenshot der neuen Website auf."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    url = getattr(project, "new_website_url", None) or project.website_url
    if not url:
        raise HTTPException(status_code=400, detail="Keine URL am Projekt hinterlegt")

    from services.screenshot import capture_screenshot
    b64 = await capture_screenshot(url)
    if not b64:
        raise HTTPException(status_code=502, detail="Screenshot konnte nicht erstellt werden")

    project.screenshot_after      = b64
    project.screenshot_after_date = datetime.utcnow()
    project.screenshot_url_after  = url
    db.commit()

    return {"success": True, "screenshot_url": f"data:image/jpeg;base64,{b64}"}


@router.get("/{project_id}/screenshots")
def get_screenshots(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Gibt gespeicherte Before/After-Screenshots zurück."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    return {
        "before": {
            "data":  f"data:image/jpeg;base64,{project.screenshot_before}" if project.screenshot_before else None,
            "date":  project.screenshot_before_date.isoformat() if project.screenshot_before_date else None,
            "url":   project.screenshot_url_before,
        },
        "after": {
            "data":  f"data:image/jpeg;base64,{project.screenshot_after}" if project.screenshot_after else None,
            "date":  project.screenshot_after_date.isoformat() if project.screenshot_after_date else None,
            "url":   project.screenshot_url_after,
        },
    }


async def _capture_project_screenshot_after(project_id: int):
    """Background-Hilfsfunktion: After-Screenshot aufnehmen und speichern."""
    from database import SessionLocal
    from services.screenshot import capture_screenshot
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        url = getattr(project, "new_website_url", None) or project.website_url
        if not url:
            return
        b64 = await capture_screenshot(url)
        if b64:
            project.screenshot_after      = b64
            project.screenshot_after_date = datetime.utcnow()
            project.screenshot_url_after  = url
            db.commit()
            logger.info(f"✓ After-Screenshot für Projekt {project_id} gespeichert")
    except Exception as e:
        logger.warning(f"After-Screenshot Fehler (Projekt {project_id}): {e}")
    finally:
        db.close()
