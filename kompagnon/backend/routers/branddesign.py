"""
Brand Design API
GET  /api/branddesign/{lead_id}                    - Get all stored brand data
POST /api/branddesign/{lead_id}/scrape             - Scrape website for brand colors/fonts/logo
POST /api/branddesign/{lead_id}/analyze-screenshot - Claude Vision analysis of screenshot
POST /api/branddesign/{lead_id}/upload-pdf         - Upload brand PDF (multipart)
GET  /api/branddesign/{lead_id}/pdf                - Download brand PDF
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import get_db, Lead
import httpx, re, os, json, anthropic
from datetime import datetime

router = APIRouter(prefix="/api/branddesign", tags=["branddesign"])


# ── Utility ───────────────────────────────────────────────────────────────────

def _set(obj, attr: str, value) -> None:
    """setattr only if the column exists on the ORM object (migration-safe)."""
    try:
        setattr(obj, attr, value)
    except Exception:
        pass


def _detect_google_analytics(html: str) -> dict:
    """
    Durchsucht HTML-Quelltext nach Google Analytics / Tag Manager Codes.
    Gibt dict zurück: { status, type, measurement_id }
    """
    # GA4 — Measurement ID (G-XXXXXXXXXX)
    ga4_matches = re.findall(r'["\']?(G-[A-Z0-9]{6,12})["\']?', html)
    if ga4_matches:
        return {"status": "vorhanden", "type": "GA4", "measurement_id": ga4_matches[0]}

    # Universal Analytics (alt) — UA-XXXXXXXX-X
    ua_matches = re.findall(r'["\']?(UA-\d{6,10}-\d+)["\']?', html)
    if ua_matches:
        return {"status": "vorhanden_alt", "type": "UA", "measurement_id": ua_matches[0]}

    # Google Tag Manager — GTM-XXXXXXX
    gtm_matches = re.findall(r'["\']?(GTM-[A-Z0-9]{5,8})["\']?', html)
    if gtm_matches:
        return {"status": "gtm", "type": "GTM", "measurement_id": gtm_matches[0]}

    return {"status": "nicht_vorhanden", "type": None, "measurement_id": None}


# ── Endpoint 1 — GET brand data ───────────────────────────────────────────────

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
        "design_style":    getattr(lead, 'brand_design_style',   None),
        "brand_notes":     getattr(lead, 'brand_notes',          None),
        "pdf_filename":    getattr(lead, 'brand_pdf_filename',   None),
        "scraped_at":      str(getattr(lead, 'brand_scraped_at', '') or '')[:16] or None,
        "ga_status":         getattr(lead, 'ga_status', 'unbekannt'),
        "ga_type":           getattr(lead, 'ga_type', None),
        "ga_measurement_id": getattr(lead, 'ga_measurement_id', None),
        "ga_checked_at":     str(getattr(lead, 'ga_checked_at', '') or '')[:16] or None,
    }


# ── Endpoint 1b — Manual save ─────────────────────────────────────────────────

@router.put("/{lead_id}")
def update_brand_design(lead_id: int, body: dict, db: Session = Depends(get_db)):
    """Manuelle Branddesign-Felder speichern."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")
    mapping = {
        "primary_color": "brand_primary_color",
        "secondary_color": "brand_secondary_color",
        "font_primary": "brand_font_primary",
        "font_secondary": "brand_font_secondary",
        "design_style": "brand_design_style",
        "brand_notes": "brand_notes",
        "logo_url": "brand_logo_url",
    }
    updated = []
    for body_field, lead_attr in mapping.items():
        if body_field in body:
            _set(lead, lead_attr, body[body_field])
            updated.append(body_field)
    if updated:
        _set(lead, 'brand_scraped_at', datetime.utcnow())
        db.commit()
    return {"saved": True, "updated_fields": updated}


# ── Endpoint 1c — Font suggestions ────────────────────────────────────────────

@router.post("/{lead_id}/suggest-fonts")
async def suggest_fonts(lead_id: int, db: Session = Depends(get_db)):
    """Schlägt passende Google Fonts basierend auf dem Brand-Stil vor."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    style = getattr(lead, 'brand_design_style', '') or ''
    trade = getattr(lead, 'trade', '') or ''
    existing_fonts = json.loads(getattr(lead, 'brand_fonts', '[]') or '[]')

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        fallback = [
            {"name": "Inter", "category": "Sans-Serif", "use": "Fließtext"},
            {"name": "Space Grotesk", "category": "Sans-Serif", "use": "Überschriften"},
            {"name": "DM Sans", "category": "Sans-Serif", "use": "Interface"},
        ]
        return {"suggestions": fallback, "source": "fallback"}

    prompt = f"""Du bist ein Typografie-Experte. Empfiehl 4-6 Google Fonts für einen Handwerksbetrieb.
Gewerk: {trade or 'unbekannt'}, Stil: {style or 'Modern'}, Fonts bisher: {', '.join(existing_fonts) if existing_fonts else 'keine'}.
Antworte NUR als JSON-Array: [{{"name":"Font","category":"Sans-Serif|Serif|Display","use":"Überschriften|Fließtext|Interface","reason":"Kurz"}}]"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]},
            )
        resp.raise_for_status()
        content = resp.json()["content"][0]["text"].strip()
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        return {"suggestions": json.loads(content), "source": "claude"}
    except Exception as e:
        raise HTTPException(500, f"Font-Recherche fehlgeschlagen: {str(e)[:100]}")


# ── Endpoint 2 — Scrape ────────────────────────────────────────────────────────

@router.post("/{lead_id}/scrape")
async def scrape_brand(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    website_url = getattr(lead, 'website_url', '') or ''
    if not website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")

    scrape_failed = False
    primary_color = secondary_color = font_primary = font_secondary = logo_url = None
    all_colors: list[str] = []
    all_fonts:  list[str] = []

    try:
        async with httpx.AsyncClient(
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=10.0,
            follow_redirects=True,
        ) as client:
            resp = await client.get(website_url)
            resp.raise_for_status()
            html_text = resp.text

        # ── Google Analytics erkennen ──
        ga_result = _detect_google_analytics(html_text)
        _set(lead, 'ga_status',         ga_result['status'])
        _set(lead, 'ga_type',           ga_result['type'])
        _set(lead, 'ga_measurement_id', ga_result['measurement_id'])
        _set(lead, 'ga_checked_at',     datetime.utcnow())

        # Colors
        hex_colors = re.findall(r'#([0-9a-fA-F]{6})', html_text)
        fonts = re.findall(r"font-family:\s*['\"]?(.*?)['\"]?\s*[;,{]", html_text)

        # Deduplicate colors, skip pure black/white
        skip = {'000000', 'ffffff', 'ff0000', '00ff00', '0000ff'}
        seen: set[str] = set()
        for c in hex_colors:
            lc = c.lower()
            if lc not in seen and lc not in skip:
                seen.add(lc)
                all_colors.append(f'#{lc}')

        primary = '#' + hex_colors[0] if hex_colors else None
        primary_color = primary
        secondary_color = all_colors[1] if len(all_colors) > 1 else None

        # Fonts — deduplicate, skip generic families
        generic = {'inherit', 'initial', 'unset', 'serif', 'sans-serif',
                   'monospace', 'cursive', 'fantasy', 'system-ui'}
        seen_f: set[str] = set()
        for f in fonts:
            name = f.strip().strip("'\"").split(',')[0].strip()
            if name and name.lower() not in generic and name not in seen_f:
                seen_f.add(name)
                all_fonts.append(name)
        all_fonts = all_fonts[:6]

        if all_fonts:
            font_primary   = all_fonts[0]
            font_secondary = all_fonts[1] if len(all_fonts) > 1 else None

        # Logo
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse
        soup = BeautifulSoup(html_text, 'html.parser')
        base = f"{urlparse(website_url).scheme}://{urlparse(website_url).netloc}"
        for img in soup.find_all('img'):
            attrs = ' '.join([
                img.get('src', ''), img.get('alt', ''),
                (img.get('class') or [''])[0],
                img.get('id', ''),
            ]).lower()
            if 'logo' in attrs:
                src = img.get('src', '')
                logo_url = src if src.startswith('http') else urljoin(base, src)
                break

    except Exception as exc:
        scrape_failed = True

    # Persist
    now = datetime.utcnow()
    _set(lead, 'brand_primary_color',   primary_color)
    _set(lead, 'brand_secondary_color', secondary_color)
    _set(lead, 'brand_font_primary',    font_primary)
    _set(lead, 'brand_font_secondary',  font_secondary)
    _set(lead, 'brand_logo_url',        logo_url)
    _set(lead, 'brand_colors',          json.dumps(all_colors))
    _set(lead, 'brand_fonts',           json.dumps(all_fonts))
    _set(lead, 'brand_scrape_failed',   scrape_failed)
    _set(lead, 'brand_scraped_at',      now)
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


# ── Endpoint 3 — Vision analysis ──────────────────────────────────────────────

@router.post("/{lead_id}/analyze-screenshot")
def analyze_screenshot(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    screenshot_b64 = getattr(lead, 'website_screenshot', None) or ''
    if not screenshot_b64:
        raise HTTPException(status_code=400, detail="Kein Screenshot vorhanden")

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY nicht konfiguriert")

    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=800,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": lead.website_screenshot,
                }},
                {"type": "text", "text": (
                    "Analysiere das Branddesign. Antworte NUR als JSON: "
                    "{primary_color, secondary_color, accent_color, background_color, "
                    "text_color, font_style, design_style, brand_notes}"
                )},
            ]}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = "\n".join(l for l in raw.splitlines() if not l.startswith("```")).strip()
        result = json.loads(raw)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analyse fehlgeschlagen: {exc}")

    _set(lead, 'brand_primary_color',   result.get('primary_color'))
    _set(lead, 'brand_secondary_color', result.get('secondary_color'))
    _set(lead, 'brand_design_style',    result.get('design_style'))
    _set(lead, 'brand_notes',           result.get('brand_notes'))
    _set(lead, 'brand_scraped_at',      datetime.utcnow())
    db.commit()

    return result


# ── Endpoint 4 — Upload PDF ────────────────────────────────────────────────────

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


# ── Endpoint 5 — Download PDF ─────────────────────────────────────────────────

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


# ── Endpoint 6 — Check Google Analytics ──────────────────────────────────────

@router.post("/{lead_id}/check-ga")
async def check_google_analytics(lead_id: int, db: Session = Depends(get_db)):
    """
    Holt die Startseite der Kundendomain und prüft auf GA/GTM-Codes.
    Schnell (~2 Sek.), kein vollständiger Scrape.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    website_url = getattr(lead, 'website_url', '') or ''
    if not website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")

    if not website_url.startswith('http'):
        website_url = 'https://' + website_url

    try:
        async with httpx.AsyncClient(
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=10.0,
            follow_redirects=True,
        ) as client:
            resp = await client.get(website_url)
            html_text = resp.text
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Website nicht erreichbar: {str(e)[:100]}")

    ga_result = _detect_google_analytics(html_text)

    _set(lead, 'ga_status',         ga_result['status'])
    _set(lead, 'ga_type',           ga_result['type'])
    _set(lead, 'ga_measurement_id', ga_result['measurement_id'])
    _set(lead, 'ga_checked_at',     datetime.utcnow())
    db.commit()

    return {
        "lead_id":        lead_id,
        "website_url":    website_url,
        **ga_result,
        "ga_checked_at":  datetime.utcnow().strftime('%Y-%m-%d %H:%M'),
    }
