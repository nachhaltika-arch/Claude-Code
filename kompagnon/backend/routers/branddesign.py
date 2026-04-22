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
from database import get_db, Lead
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
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        logger.warning(f"get_brand_guideline: Lead {lead_id} nicht gefunden")
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    raw = getattr(lead, 'brand_guideline_json', None)
    generated_at = getattr(lead, 'brand_guideline_generated_at', None)

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

    # Aktuelle Brand-Daten zusammenstellen
    primary   = getattr(lead, 'brand_primary_color',  None) or '#004F59'
    secondary = getattr(lead, 'brand_secondary_color', None) or '#2C3E50'
    dd_raw    = getattr(lead, 'brand_design_json', None)
    dd        = json.loads(dd_raw) if dd_raw else {}

    accent      = dd.get('design_brief', {}).get('akzentfarbe', '#FAE600')
    font_head   = getattr(lead, 'brand_font_primary',   None) or dd.get('font_heading', 'Georgia')
    font_body   = getattr(lead, 'brand_font_secondary', None) or dd.get('font_body', 'Arial')
    font_accent = dd.get('font_accent', 'Barlow Condensed')
    radius      = dd.get('border_radius_px', 6)
    shadow      = dd.get('shadow_label', 'leicht')
    style       = getattr(lead, 'brand_design_style', None) or dd.get('style_keyword', 'Modern')
    company     = getattr(lead, 'company_name', '') or 'Unbekannt'

    prompt = f"""Du bist ein Brand-Design-Experte. Erstelle eine vollständige Brand Guideline als JSON für folgendes Unternehmen:

Unternehmen: {company}
Primärfarbe: {primary}
Sekundärfarbe: {secondary}
Akzentfarbe: {accent}
Überschriften-Font: {font_head}
Fließtext-Font: {font_body}
Akzent-Font: {font_accent}
Stil: {style}
Border-Radius: {radius}px
Schatten: {shadow}

Gib NUR valides JSON zurück, kein Markdown, keine Erklärungen. Format:
{{
  "meta": {{
    "style_keyword": "Modern",
    "farb_stimmung": "Kuehl",
    "radius_label": "Rund",
    "shadow_label": "leicht"
  }},
  "colors": {{
    "primary": "{primary}",
    "primary_dark": "abgedunkelte Variante",
    "secondary": "{secondary}",
    "accent": "{accent}",
    "background": "#F5F5F0",
    "surface": "#FFFFFF",
    "text_primary": "#1A1A1A",
    "text_secondary": "#555555",
    "text_on_primary": "#FFFFFF",
    "text_on_accent": "#000000",
    "border": "#E0E0E0",
    "success": "#00875A"
  }},
  "typography": {{
    "heading": "{font_head}",
    "body": "{font_body}",
    "accent": "{font_accent}"
  }},
  "spacing": {{
    "border_radius": "{radius}px",
    "shadow": "{shadow}"
  }}
}}"""

    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.content[0].text.strip()
        # JSON aus der Antwort extrahieren
        if raw_text.startswith('```'):
            raw_text = raw_text.split('```')[1]
            if raw_text.startswith('json'):
                raw_text = raw_text[4:]
        guideline = json.loads(raw_text.strip())
    except json.JSONDecodeError:
        # Fallback: strukturierte Guideline direkt erstellen
        guideline = {
            "meta": {
                "style_keyword": style,
                "farb_stimmung": "Professionell",
                "radius_label": "Rund" if radius >= 6 else "Eckig",
                "shadow_label": shadow,
            },
            "colors": {
                "primary": primary, "secondary": secondary, "accent": accent,
                "background": "#F5F5F0", "surface": "#FFFFFF",
                "text_primary": "#1A1A1A", "text_secondary": "#555555",
                "text_on_primary": "#FFFFFF", "text_on_accent": "#000000",
                "border": "#E0E0E0", "success": "#00875A",
            },
            "typography": {"heading": font_head, "body": font_body, "accent": font_accent},
            "spacing": {"border_radius": f"{radius}px", "shadow": shadow},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KI-Fehler: {str(e)[:200]}")

    _set(lead, 'brand_guideline_json', json.dumps(guideline, ensure_ascii=False))
    _set(lead, 'brand_guideline_generated_at', datetime.utcnow())
    db.commit()

    return {"guideline": guideline, "generated_at": datetime.utcnow().isoformat()}


@router.put("/{lead_id}/guideline")
def update_brand_guideline(lead_id: int, body: dict, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    guideline = body.get("guideline")
    if not guideline:
        raise HTTPException(status_code=400, detail="guideline fehlt")

    _set(lead, 'brand_guideline_json', json.dumps(guideline, ensure_ascii=False))
    _set(lead, 'brand_guideline_generated_at', datetime.utcnow())
    db.commit()

    return {"ok": True, "saved_at": datetime.utcnow().isoformat()}
