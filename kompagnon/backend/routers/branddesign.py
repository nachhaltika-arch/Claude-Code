"""
Brand Design API
GET  /api/branddesign/{lead_id}                    - Get all stored brand data
POST /api/branddesign/{lead_id}/scrape             - Scrape website for brand colors/fonts/logo
POST /api/branddesign/{lead_id}/analyze-screenshot - Claude Vision analysis of screenshot
POST /api/branddesign/{lead_id}/upload-pdf         - Upload brand PDF (multipart)
GET  /api/branddesign/{lead_id}/pdf                - Download brand PDF
GET  /api/branddesign/{lead_id}/guideline          - Load saved brand guideline
POST /api/branddesign/{lead_id}/guideline/generate - Generate brand guideline via AI
PUT  /api/branddesign/{lead_id}/guideline          - Save manual edits to guideline
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, Lead, Briefing
import httpx, re, os, json, anthropic, logging
from datetime import datetime

logger = logging.getLogger(__name__)
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

    design_json = getattr(lead, 'brand_design_json', None)
    design_data = None
    if design_json:
        try:
            design_data = json.loads(design_json)
        except Exception:
            pass

    return {
        "lead_id":         lead_id,
        "primary_color":   lead.brand_primary_color,
        "secondary_color": lead.brand_secondary_color,
        "font_primary":    lead.brand_font_primary,
        "font_secondary":  lead.brand_font_secondary,
        "logo_url":        lead.brand_logo_url,
        "all_colors":      _j(lead.brand_colors),
        "all_fonts":       _j(lead.brand_fonts),
        "scrape_failed":   bool(lead.brand_scrape_failed or False),
        "design_style":    lead.brand_design_style,
        "brand_notes":     lead.brand_notes,
        "pdf_filename":    lead.brand_pdf_filename,
        "scraped_at":      str(lead.brand_scraped_at or '')[:16] or None,
        "ga_status":         lead.ga_status or 'unbekannt',
        "ga_type":           lead.ga_type,
        "ga_measurement_id": lead.ga_measurement_id,
        "ga_checked_at":     str(lead.ga_checked_at or '')[:16] or None,
        "design_data":       design_data,
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
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            resp = await client.get(website_url)
            resp.raise_for_status()
            html_text = resp.text
        logger.info(f"Brand scrape OK for {website_url}: {len(html_text)} chars")

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

    except Exception as e:
        scrape_failed = True
        html_text = ''
        logger.error(f"Brand scrape failed for {website_url}: {e}")

    # ── Design-DNA Extraktion ─────────────────────────────────────────
    design_data = None
    if html_text and not scrape_failed:
        # Border-Radius
        radius_values = re.findall(r'border-radius:\s*([\d]+)px', html_text)
        if radius_values:
            avg_radius = sum(int(v) for v in radius_values) / len(radius_values)
            border_radius_style = "scharf" if avg_radius < 4 else "leicht" if avg_radius < 10 else "abgerundet" if avg_radius < 20 else "rund"
            border_radius_px = round(avg_radius)
        else:
            border_radius_style, border_radius_px = "unbekannt", 8

        # Schatten
        shadow_count = len(re.findall(r'box-shadow', html_text))
        shadow_level = 0 if shadow_count == 0 else 1 if shadow_count < 3 else 2 if shadow_count < 8 else 3
        shadow_label = ["Kein Schatten", "Leicht", "Mittel", "Stark"][shadow_level]

        # Button-Stil
        button_style = "filled"
        if re.search(r'button[^{]*\{[^}]*background:\s*transparent', html_text, re.IGNORECASE | re.DOTALL):
            button_style = "ghost"
        elif re.search(r'button[^{]*\{[^}]*border[^}]*transparent', html_text, re.IGNORECASE | re.DOTALL):
            button_style = "outline"

        # Abstands-Dichte
        padding_values = [int(v) for v in re.findall(r'padding:\s*([\d]+)px', html_text) if int(v) < 200]
        spacing_density = "normal"
        if padding_values:
            avg_padding = sum(padding_values) / len(padding_values)
            spacing_density = "kompakt" if avg_padding < 12 else "normal" if avg_padding < 24 else "luftig"

        # Farbrollen klassifizieren
        color_roles = {"primary": all_colors[0] if all_colors else None, "secondary": all_colors[1] if len(all_colors) > 1 else None, "accent": None, "background": None, "text": None, "all": all_colors[:12]}
        for color in all_colors:
            try:
                r_v, g_v, b_v = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                brightness = (r_v * 299 + g_v * 587 + b_v * 114) / 1000
                if brightness > 220 and not color_roles["background"]:
                    color_roles["background"] = color
                elif brightness < 60 and not color_roles["text"]:
                    color_roles["text"] = color
            except Exception:
                pass

        design_data = {
            "colors": color_roles, "fonts": all_fonts[:6],
            "border_radius_px": border_radius_px, "border_radius_style": border_radius_style,
            "shadow_level": shadow_level, "shadow_label": shadow_label,
            "button_style": button_style, "spacing_density": spacing_density,
            "style_keyword": None, "style_beschreibung": None,
            "farb_stimmung": None, "design_brief": None,
        }

        # Claude Design-Brief
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key:
            try:
                prompt = (
                    f"Analysiere diese Design-Daten einer Website und erstelle einen Design-Brief.\n"
                    f"Website: {website_url}\nFarben: {json.dumps(color_roles)}\n"
                    f"Schriften: {all_fonts[:4]}\nEcken: {border_radius_style} ({border_radius_px}px)\n"
                    f"Schatten: {shadow_label}\nButton: {button_style}\nAbstaende: {spacing_density}\n\n"
                    "Antworte NUR als JSON:\n"
                    '{"style_keyword":"<Modern|Klassisch|Verspielt|Industriell|Premium|Bodenstaendig|Digital|Traditionell>",'
                    '"style_beschreibung":"<2 Saetze>","farb_stimmung":"<Warm|Kuehl|Neutral|Kontrastreich>",'
                    '"design_brief":{"fuer_ki_prompt":"<80-120 Woerter: Beschreibung fuer KI-Template-Erstellung>",'
                    '"primaerfarbe":"<Hex>","akzentfarbe":"<Hex>","hintergrundfarbe":"<Hex>","textfarbe":"<Hex>",'
                    '"heading_font":"<Font>","body_font":"<Font>","radius_token":"<scharf|leicht|abgerundet|rund>",'
                    '"shadow_token":"<ohne|leicht|mittel|stark>","dichte":"<kompakt|normal|luftig>"}}'
                )
                async with httpx.AsyncClient(timeout=30.0) as ai_client:
                    ai_resp = await ai_client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                        json={"model": "claude-sonnet-4-20250514", "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]},
                    )
                if ai_resp.status_code == 200:
                    content = ai_resp.json()["content"][0]["text"].strip()
                    content = re.sub(r'^```json\s*', '', content)
                    content = re.sub(r'\s*```$', '', content)
                    claude_data = json.loads(content)
                    design_data["style_keyword"] = claude_data.get("style_keyword")
                    design_data["style_beschreibung"] = claude_data.get("style_beschreibung")
                    design_data["farb_stimmung"] = claude_data.get("farb_stimmung")
                    design_data["design_brief"] = claude_data.get("design_brief")
            except Exception:
                pass

    # Persist
    now = datetime.utcnow()
    lead.brand_primary_color   = primary_color
    lead.brand_secondary_color = secondary_color
    lead.brand_font_primary    = font_primary
    lead.brand_font_secondary  = font_secondary
    lead.brand_logo_url        = logo_url
    lead.brand_colors          = json.dumps(all_colors)
    lead.brand_fonts           = json.dumps(all_fonts)
    lead.brand_scrape_failed   = scrape_failed
    lead.brand_scraped_at      = now
    if design_data:
        lead.brand_design_json  = json.dumps(design_data, ensure_ascii=False)
        lead.brand_design_style = design_data.get("style_keyword")
    try:
        db.commit()
        logger.info(f"Brand data saved for lead {lead_id}: primary={primary_color}, fonts={len(all_fonts)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Brand save failed for lead {lead_id}: {e}")
        raise HTTPException(500, f"Speichern fehlgeschlagen: {str(e)[:100]}")

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
        "design_data":     design_data,
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


# ── Brand Guideline ────────────────────────────────────────────────────────────

@router.get("/{lead_id}/guideline")
def get_brand_guideline(lead_id: int, db: Session = Depends(get_db)):
    # Existenz prüfen
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        logger.warning(f"get_brand_guideline: Lead {lead_id} nicht gefunden")
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    # Direktes SQL — robust gegen fehlende ORM-Spalte
    try:
        row = db.execute(
            text("SELECT brand_guideline_json, brand_guideline_generated_at FROM leads WHERE id = :lid"),
            {"lid": lead_id}
        ).fetchone()
    except Exception as e:
        logger.error(f"get_brand_guideline: SQL-Fehler lead_id={lead_id}: {e}")
        return {"generated": False, "guideline": None, "error": "Spalte fehlt — Migration ausstehend"}

    raw          = row[0] if row else None
    generated_at = row[1] if row else None

    logger.info(
        f"get_brand_guideline: lead_id={lead_id}, "
        f"hat_guideline={bool(raw)}, "
        f"generated_at={generated_at}"
    )

    if not raw:
        return {"generated": False, "guideline": None}

    try:
        guideline = json.loads(raw)
        return {
            "generated":    True,
            "guideline":    guideline,
            "generated_at": generated_at.isoformat() if generated_at else None,
        }
    except Exception as e:
        logger.error(f"get_brand_guideline: JSON parse Fehler lead_id={lead_id}: {e}")
        return {"generated": False, "guideline": None}


@router.post("/{lead_id}/guideline/generate")
async def generate_brand_guideline(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()

    # ── Brand-Daten zusammenstellen ──────────────────────────────────────
    primary    = getattr(lead, 'brand_primary_color',   None) or '#004F59'
    secondary  = getattr(lead, 'brand_secondary_color', None) or '#2C3E50'
    dd_raw     = getattr(lead, 'brand_design_json', None)
    dd         = json.loads(dd_raw) if dd_raw else {}
    brief      = dd.get('design_brief', {})

    accent       = brief.get('akzentfarbe', '#FAE600')
    font_head    = getattr(lead, 'brand_font_primary',   None) or dd.get('font_heading', 'Georgia')
    font_body    = getattr(lead, 'brand_font_secondary', None) or dd.get('font_body', 'Arial')
    font_accent  = dd.get('font_accent', 'Barlow Condensed')
    all_colors   = json.loads(getattr(lead, 'brand_colors', None) or '[]')
    all_fonts    = json.loads(getattr(lead, 'brand_fonts',  None) or '[]')
    logo_url     = getattr(lead, 'brand_logo_url', None) or ''
    radius       = dd.get('border_radius_px', 6)
    shadow_lbl   = dd.get('shadow_label', 'leicht')
    btn_style    = dd.get('button_style', 'abgerundet')
    spacing      = dd.get('spacing_density', 'normal')
    farb_stimmung= dd.get('farb_stimmung', 'Neutral')
    style        = getattr(lead, 'brand_design_style', None) or dd.get('style_keyword', 'Modern')
    company      = getattr(lead, 'company_name', '') or 'Unbekannt'
    city         = getattr(lead, 'city', '') or 'Deutschland'
    gewerk       = (briefing.gewerk     if briefing else '') or getattr(lead, 'trade', '') or 'Handwerk'
    leistungen   = (briefing.leistungen if briefing else '') or ''
    usp          = (briefing.usp        if briefing else '') or ''

    prompt = f"""Du bist ein professioneller UI/UX-Designer und Brand-Strategist.
Erstelle eine vollständige UI Brand Guideline als strukturiertes JSON-Objekt.

KUNDENDATEN:
Unternehmen: {company}
Gewerk: {gewerk} | Stadt: {city}
Leistungen: {leistungen[:300] if leistungen else 'nicht angegeben'}
USP: {usp[:200] if usp else 'nicht angegeben'}

ERKANNTE BRAND-DATEN (aus Website-Scan):
Primärfarbe: {primary}
Sekundärfarbe: {secondary}
Akzentfarbe: {accent}
Alle erkannten Farben: {', '.join(all_colors[:8]) if all_colors else 'keine'}
Überschriften-Font: {font_head}
Fließtext-Font: {font_body}
Alle erkannten Fonts: {', '.join(all_fonts[:6]) if all_fonts else 'keine'}
Stil-Keyword: {style}
Farb-Stimmung: {farb_stimmung}
Border-Radius: {radius}px ({btn_style})
Schatten: {shadow_lbl}
Abstands-Dichte: {spacing}
Logo-URL: {logo_url or 'nicht erkannt'}

Antworte NUR als JSON-Objekt (kein Markdown, keine Erklärungen):

{{
  "meta": {{
    "company": "{company}",
    "gewerk": "{gewerk}",
    "style_keyword": "{style}",
    "farb_stimmung": "{farb_stimmung}",
    "radius_label": "Rund"
  }},
  "colors": {{
    "primary":        "{primary}",
    "primary_dark":   "<10% dunkler als primary>",
    "primary_light":  "<20% heller als primary>",
    "primary_subtle": "<primary mit 10% Deckkraft als rgba>",
    "secondary":      "{secondary}",
    "accent":         "{accent}",
    "surface":        "<heller Seitenhintergrund, fast weiß>",
    "surface_raised": "<etwas dunklere Karten-Oberfläche>",
    "border":         "<dezente Rahmenfarbe>",
    "text_primary":   "<Haupttextfarbe, fast schwarz>",
    "text_secondary": "<Sekundärtextfarbe, grau>",
    "text_tertiary":  "<dezente Labels, helles grau>",
    "text_inverse":   "#FFFFFF",
    "success":        "#1D9E75",
    "warning":        "#F59E0B",
    "error":          "#E74C3C"
  }},
  "typography": {{
    "font_heading": "{font_head}",
    "font_body":    "{font_body}",
    "font_accent":  "{font_accent}",
    "scale": {{
      "h1":      {{"size": "48px", "weight": "700", "line_height": "1.1", "letter_spacing": "-0.02em"}},
      "h2":      {{"size": "32px", "weight": "700", "line_height": "1.2", "letter_spacing": "-0.01em"}},
      "h3":      {{"size": "24px", "weight": "600", "line_height": "1.3", "letter_spacing": "0"}},
      "h4":      {{"size": "20px", "weight": "600", "line_height": "1.4", "letter_spacing": "0"}},
      "body_lg": {{"size": "18px", "weight": "400", "line_height": "1.75"}},
      "body":    {{"size": "16px", "weight": "400", "line_height": "1.75"}},
      "body_sm": {{"size": "14px", "weight": "400", "line_height": "1.6"}},
      "label":   {{"size": "12px", "weight": "700", "text_transform": "uppercase", "letter_spacing": "0.06em"}},
      "button":  {{"size": "14px", "weight": "700", "text_transform": "uppercase", "letter_spacing": "0.05em"}},
      "caption": {{"size": "11px", "weight": "400", "line_height": "1.5"}}
    }}
  }},
  "spacing": {{
    "xs": "4px", "sm": "8px", "md": "16px", "lg": "24px",
    "xl": "32px", "2xl": "48px", "3xl": "64px", "4xl": "96px"
  }},
  "border_radius": {{
    "sm": "<radius/2>px", "md": "{radius}px",
    "lg": "<radius*1.5>px", "xl": "<radius*2>px", "full": "9999px"
  }},
  "shadows": {{
    "sm":   "<passend zu {shadow_lbl}, leicht>",
    "md":   "<mittel>",
    "lg":   "<stark>",
    "none": "none"
  }},
  "components": {{
    "button_primary":   {{"background": "<colors.primary>",   "color": "#FFFFFF", "border_radius": "{radius}px", "padding": "10px 24px"}},
    "button_secondary": {{"background": "transparent", "color": "<colors.primary>", "border": "1.5px solid <colors.primary>", "border_radius": "{radius}px", "padding": "10px 24px"}},
    "button_accent":    {{"background": "<colors.accent>",    "color": "#FFFFFF", "border_radius": "{radius}px", "padding": "10px 24px"}},
    "card":  {{"background": "<colors.surface_raised>", "border": "0.5px solid <colors.border>", "border_radius": "<border_radius.lg>", "shadow": "<shadows.sm>", "padding": "24px"}},
    "input": {{"background": "<colors.surface>", "border": "1px solid <colors.border>", "border_radius": "{radius}px", "padding": "10px 14px", "focus_border": "<colors.primary>"}},
    "nav":   {{"background": "<colors.primary>", "text_color": "#FFFFFF", "height": "64px"}},
    "hero":  {{"background": "<colors.primary>", "text_color": "#FFFFFF", "padding_y": "80px"}},
    "footer":{{"background": "<colors.secondary>", "text_color": "rgba(255,255,255,0.7)", "padding_y": "48px"}}
  }},
  "css_variables": ":root {{\n  --color-primary: <primary>;\n  --color-secondary: <secondary>;\n  --color-accent: <accent>;\n  --color-surface: <surface>;\n  --color-text: <text_primary>;\n  --font-heading: \\"<font_heading>\\", serif;\n  --font-body: \\"<font_body>\\", sans-serif;\n  --radius-md: {radius}px;\n  /* alle weiteren tokens */\n}}",
  "voice_tone": {{
    "charakter": "<2-3 Adjektive passend zu Gewerk und Stil>",
    "ansprache": "<Du oder Sie>",
    "cta_beispiele": ["<CTA passend zu {gewerk} 1>", "<CTA 2>", "<CTA 3>"]
  }}
}}"""

    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.content[0].text.strip()
        raw_text = re.sub(r'^```json\s*', '', raw_text)
        raw_text = re.sub(r'\s*```$',     '', raw_text)
        guideline = json.loads(raw_text.strip())
    except json.JSONDecodeError:
        guideline = {
            "meta": {"company": company, "gewerk": gewerk, "style_keyword": style, "farb_stimmung": farb_stimmung, "radius_label": "Rund" if radius >= 6 else "Eckig"},
            "colors": {
                "primary": primary, "primary_dark": primary, "secondary": secondary,
                "accent": accent, "surface": "#F5F5F0", "surface_raised": "#FFFFFF",
                "border": "#E0E0E0", "text_primary": "#1A1A1A", "text_secondary": "#555555",
                "text_tertiary": "#999999", "text_inverse": "#FFFFFF",
                "success": "#1D9E75", "warning": "#F59E0B", "error": "#E74C3C",
            },
            "typography": {
                "font_heading": font_head, "font_body": font_body, "font_accent": font_accent,
                "scale": {
                    "h1": {"size": "48px", "weight": "700", "line_height": "1.1"},
                    "h2": {"size": "32px", "weight": "700", "line_height": "1.2"},
                    "body": {"size": "16px", "weight": "400", "line_height": "1.75"},
                    "button": {"size": "14px", "weight": "700", "text_transform": "uppercase"},
                },
            },
            "spacing": {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px"},
            "border_radius": {"sm": f"{max(2, radius//2)}px", "md": f"{radius}px", "lg": f"{int(radius*1.5)}px", "full": "9999px"},
            "shadows": {"sm": "0 1px 3px rgba(0,0,0,.08)", "md": "0 4px 12px rgba(0,0,0,.12)", "none": "none"},
            "components": {
                "button_primary":   {"background": primary,   "color": "#FFFFFF", "border_radius": f"{radius}px", "padding": "10px 24px"},
                "button_secondary": {"background": "transparent", "color": primary, "border": f"1.5px solid {primary}", "border_radius": f"{radius}px", "padding": "10px 24px"},
                "button_accent":    {"background": accent,    "color": "#FFFFFF", "border_radius": f"{radius}px", "padding": "10px 24px"},
            },
            "css_variables": f":root {{\n  --color-primary: {primary};\n  --color-secondary: {secondary};\n  --color-accent: {accent};\n  --font-heading: \"{font_head}\", serif;\n  --font-body: \"{font_body}\", sans-serif;\n  --radius-md: {radius}px;\n}}",
            "voice_tone": {"charakter": style, "ansprache": "Sie", "cta_beispiele": ["Jetzt anfragen", "Mehr erfahren", "Kontakt aufnehmen"]},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KI-Fehler: {str(e)[:200]}")

    now = datetime.utcnow()
    try:
        db.execute(
            text("""
                UPDATE leads
                SET brand_guideline_json = :gjson,
                    brand_guideline_generated_at = :gat
                WHERE id = :lid
            """),
            {"gjson": json.dumps(guideline, ensure_ascii=False), "gat": now, "lid": lead_id}
        )
        db.commit()
        logger.info(f"generate_brand_guideline: Guideline gespeichert für lead_id={lead_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"generate_brand_guideline: Speichern fehlgeschlagen lead_id={lead_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Speichern fehlgeschlagen: {str(e)[:200]}")

    return {"guideline": guideline, "generated_at": now.isoformat()}


@router.put("/{lead_id}/guideline")
def update_brand_guideline(lead_id: int, body: dict, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    guideline = body.get("guideline")
    if not guideline:
        raise HTTPException(status_code=400, detail="guideline fehlt")

    now = datetime.utcnow()
    try:
        db.execute(
            text("""
                UPDATE leads
                SET brand_guideline_json = :gjson,
                    brand_guideline_generated_at = :gat
                WHERE id = :lid
            """),
            {"gjson": json.dumps(guideline, ensure_ascii=False), "gat": now, "lid": lead_id}
        )
        db.commit()
        logger.info(f"update_brand_guideline: Gespeichert lead_id={lead_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"update_brand_guideline: Fehler lead_id={lead_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Speichern fehlgeschlagen: {str(e)[:200]}")

    return {"ok": True, "saved_at": now.isoformat()}
