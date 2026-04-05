"""
Brand Design API
POST /api/branddesign/{lead_id}/scrape             - Scrape website for brand colors/fonts/logo
POST /api/branddesign/{lead_id}/analyze-screenshot - Claude Vision analysis of screenshot
POST /api/branddesign/{lead_id}/upload-pdf         - Upload brand PDF (multipart)
GET  /api/branddesign/{lead_id}/pdf                - Download brand PDF
GET  /api/branddesign/{lead_id}                    - Get all stored brand data
"""
import json
import re
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import Lead, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/branddesign", tags=["branddesign"])

# ── Colour helpers ─────────────────────────────────────────────────────────────

def _rgb_to_hex(r, g, b) -> str:
    return '#{:02x}{:02x}{:02x}'.format(int(r), int(g), int(b))


def extract_colors(text: str) -> list[str]:
    colors: list[str] = []
    # Full hex
    for m in re.findall(r'#([0-9a-fA-F]{6})\b', text):
        colors.append(f'#{m.lower()}')
    # Short hex
    for m in re.findall(r'#([0-9a-fA-F]{3})\b', text):
        r, g, b = m[0]*2, m[1]*2, m[2]*2
        colors.append(f'#{r}{g}{b}'.lower())
    # rgb(...)
    for m in re.findall(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', text):
        colors.append(_rgb_to_hex(*m))
    # Deduplicate preserving order, skip common non-brand colours
    skip = {'#000000', '#ffffff', '#ff0000', '#00ff00', '#0000ff'}
    seen: set[str] = set()
    result: list[str] = []
    for c in colors:
        if c not in seen and c not in skip:
            seen.add(c)
            result.append(c)
    return result[:10]


def extract_fonts(text: str) -> list[str]:
    fonts: list[str] = []
    # font-family: ... ;
    for m in re.findall(r'font-family\s*:\s*([^;}{]+)', text, re.IGNORECASE):
        for part in m.split(','):
            name = part.strip().strip("'\"")
            if name and name.lower() not in ('inherit', 'initial', 'unset', 'serif',
                                              'sans-serif', 'monospace', 'cursive', 'fantasy'):
                fonts.append(name)
    # Google Fonts family= parameter
    for m in re.findall(r'family=([A-Za-z+]+)', text):
        fonts.append(m.replace('+', ' '))
    seen: set[str] = set()
    result: list[str] = []
    for f in fonts:
        if f not in seen:
            seen.add(f)
            result.append(f)
    return result[:6]


# ── Endpoint 1 — Scrape ────────────────────────────────────────────────────────

@router.post("/{lead_id}/scrape")
async def scrape_brand(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    website_url = getattr(lead, 'website_url', '') or ''
    if not website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")

    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Abhängigkeit fehlt: {e}")

    scrape_failed = False
    primary_color = secondary_color = font_primary = font_secondary = logo_url = None
    all_colors: list[str] = []
    all_fonts:  list[str] = []

    try:
        async with httpx.AsyncClient(
            headers={'User-Agent': 'KOMPAGNON-BrandBot/1.0'},
            timeout=10.0,
            follow_redirects=True,
        ) as client:
            resp = await client.get(website_url)
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, 'html.parser')
        base = f"{urlparse(website_url).scheme}://{urlparse(website_url).netloc}"

        # ── Colors ──────────────────────────────────────────────────────────
        all_colors = extract_colors(html)
        if all_colors:
            primary_color   = all_colors[0]
            secondary_color = all_colors[1] if len(all_colors) > 1 else None

        # ── Fonts ────────────────────────────────────────────────────────────
        all_fonts = extract_fonts(html)
        if all_fonts:
            font_primary   = all_fonts[0]
            font_secondary = all_fonts[1] if len(all_fonts) > 1 else None

        # ── Logo ─────────────────────────────────────────────────────────────
        for img in soup.find_all('img'):
            attrs = ' '.join([
                img.get('src', ''), img.get('alt', ''),
                img.get('class', [''])[0] if img.get('class') else '',
                img.get('id', ''),
            ]).lower()
            if 'logo' in attrs:
                src = img.get('src', '')
                logo_url = src if src.startswith('http') else urljoin(base, src)
                break

        # ── Favicon ──────────────────────────────────────────────────────────
        favicon_url = None
        icon_link = soup.find('link', rel=lambda r: r and any(
            v.lower() in ('icon', 'shortcut icon') for v in (r if isinstance(r, list) else [r])
        ))
        if icon_link and icon_link.get('href'):
            href = icon_link['href']
            favicon_url = href if href.startswith('http') else urljoin(base, href)
        else:
            favicon_url = urljoin(base, '/favicon.ico')

        # Store favicon on lead if column exists
        try:
            lead.favicon_url = favicon_url
        except Exception:
            pass

    except Exception as exc:
        logger.warning("Brand scrape failed for lead %s: %s", lead_id, exc)
        scrape_failed = True

    # ── Persist to DB ────────────────────────────────────────────────────────
    now = datetime.utcnow()
    _set(lead, 'brand_primary_color',  primary_color)
    _set(lead, 'brand_secondary_color', secondary_color)
    _set(lead, 'brand_font_primary',   font_primary)
    _set(lead, 'brand_font_secondary', font_secondary)
    _set(lead, 'brand_logo_url',       logo_url)
    _set(lead, 'brand_colors',         json.dumps(all_colors))
    _set(lead, 'brand_fonts',          json.dumps(all_fonts))
    _set(lead, 'brand_scrape_failed',  scrape_failed)
    _set(lead, 'brand_scraped_at',     now)
    db.commit()

    return {
        "primary_color":   primary_color,
        "secondary_color": secondary_color,
        "font_primary":    font_primary,
        "font_secondary":  font_secondary,
        "logo_url":        logo_url,
        "all_colors":      all_colors,
        "all_fonts":       all_fonts,
        "scrape_failed":   scrape_failed,
        "scraped_at":      str(now)[:16],
    }


# ── Endpoint 2 — Vision analysis ──────────────────────────────────────────────

@router.post("/{lead_id}/analyze-screenshot")
def analyze_screenshot(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    screenshot_b64 = getattr(lead, 'website_screenshot', None) or ''
    if not screenshot_b64:
        raise HTTPException(status_code=400, detail="Kein Screenshot vorhanden")

    import os
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY nicht konfiguriert")

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": screenshot_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Analysiere diesen Website-Screenshot und extrahiere das Branddesign.\n"
                            "Antworte NUR als JSON:\n"
                            "{\n"
                            '  "primary_color": "#HEX der dominanten Markenfarbe",\n'
                            '  "secondary_color": "#HEX der zweiten Markenfarbe",\n'
                            '  "accent_color": "#HEX einer Akzentfarbe falls sichtbar",\n'
                            '  "background_color": "#HEX der Hintergrundfarbe",\n'
                            '  "text_color": "#HEX der Haupttextfarbe",\n'
                            '  "font_style": "serif|sans-serif|monospace|display",\n'
                            '  "design_style": "modern|klassisch|minimalistisch|verspielt|professionell",\n'
                            '  "logo_visible": true,\n'
                            '  "brand_notes": "kurze Beschreibung des Designstils auf Deutsch"\n'
                            "}"
                        ),
                    },
                ],
            }],
        )
        raw = message.content[0].text.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = "\n".join(l for l in raw.splitlines() if not l.startswith("```")).strip()
        result: dict = json.loads(raw)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analyse fehlgeschlagen: {exc}")

    # Persist relevant fields
    _set(lead, 'brand_primary_color',   result.get('primary_color'))
    _set(lead, 'brand_secondary_color', result.get('secondary_color'))
    _set(lead, 'brand_scraped_at',      datetime.utcnow())
    db.commit()

    return result


# ── Endpoint 3 — Upload PDF ────────────────────────────────────────────────────

@router.post("/{lead_id}/upload-pdf")
async def upload_brand_pdf(
    lead_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not (file.filename or '').lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien erlaubt")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF zu groß (max 20 MB)")

    _set(lead, 'brand_pdf_data',     content)
    _set(lead, 'brand_pdf_filename', file.filename)
    db.commit()
    return {"success": True, "filename": file.filename, "size_kb": len(content) // 1024}


# ── Endpoint 4 — Download PDF ─────────────────────────────────────────────────

@router.get("/{lead_id}/pdf")
def download_brand_pdf(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    pdf_data = getattr(lead, 'brand_pdf_data', None)
    if not pdf_data:
        raise HTTPException(status_code=404, detail="Kein Brand-PDF vorhanden")

    filename = getattr(lead, 'brand_pdf_filename', None) or 'brand.pdf'
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Endpoint 5 — Get brand data ───────────────────────────────────────────────

@router.get("/{lead_id}")
def get_brand_data(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    def _j(val):
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return []

    return {
        "lead_id":         lead_id,
        "primary_color":   getattr(lead, 'brand_primary_color',   None),
        "secondary_color": getattr(lead, 'brand_secondary_color', None),
        "font_primary":    getattr(lead, 'brand_font_primary',    None),
        "font_secondary":  getattr(lead, 'brand_font_secondary',  None),
        "logo_url":        getattr(lead, 'brand_logo_url',        None),
        "all_colors":      _j(getattr(lead, 'brand_colors', None)),
        "all_fonts":       _j(getattr(lead, 'brand_fonts',  None)),
        "scrape_failed":   bool(getattr(lead, 'brand_scrape_failed', False)),
        "pdf_filename":    getattr(lead, 'brand_pdf_filename', None),
        "scraped_at":      str(getattr(lead, 'brand_scraped_at', '') or '')[:16] or None,
    }


# ── Utility ───────────────────────────────────────────────────────────────────

def _set(obj, attr: str, value) -> None:
    """setattr only if the column exists on the ORM object (migration-safe)."""
    try:
        setattr(obj, attr, value)
    except Exception:
        pass
