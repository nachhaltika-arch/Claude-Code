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
from routers.auth_router import require_any_auth
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
        "font_heading":    getattr(lead, 'brand_font_heading', None),
        "font_body":       getattr(lead, 'brand_font_body',    None),
        "font_accent":     getattr(lead, 'brand_font_accent',  None),
        "fonts_detail":    _j(getattr(lead, 'brand_fonts_detail', None)),
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


# ── Font-Rollen-Erkennung ──────────────────────────────────────────────────────

def _extract_font_roles(css_text: str, html_text: str) -> dict:
    """Analysiert CSS + HTML und erkennt Heading/Body/Accent Schriften."""
    HEADING_PAT = [r'h[1-6]\b', r'\.heading', r'\.title', r'\.headline', r'\.hero', r'\.display']
    BODY_PAT    = [r'\bbody\b', r'\bp\b', r'main\b', r'article\b', r'\.content\b', r'\.text\b', r'\.prose']
    ACCENT_PAT  = [r'\.btn\b', r'button\b', r'\bnav\b', r'\.cta\b', r'blockquote\b', r'\.badge\b']

    generic = {'inherit','initial','unset','serif','sans-serif','monospace','cursive','fantasy',
               'system-ui','-apple-system','blinkmacsystemfont','segoe ui','helvetica neue',
               'helvetica','arial','times new roman','courier new'}

    def _clean(raw):
        name = raw.strip().strip("'\"").split(',')[0].strip()
        return name if name and name.lower() not in generic else None

    def _match(sel, pats):
        s = sel.lower()
        return any(re.search(p, s) for p in pats)

    rule_pat = re.compile(r'([^{}@][^{}]*?)\{([^{}]*?font-family\s*:[^;}]+[^{}]*?)\}', re.DOTALL | re.IGNORECASE)
    fd_pat   = re.compile(r'font-family\s*:\s*([^;}{]+)', re.IGNORECASE)

    heading_f, body_f, accent_f = [], [], []
    seen, all_f = set(), []

    for m in rule_pat.finditer(css_text):
        sel, body = m.group(1).strip(), m.group(2)
        fm = fd_pat.search(body)
        if not fm:
            continue
        name = _clean(fm.group(1))
        if not name:
            continue
        if name not in seen:
            seen.add(name)
            all_f.append(name)
        if _match(sel, HEADING_PAT): heading_f.append(name)
        if _match(sel, BODY_PAT):    body_f.append(name)
        if _match(sel, ACCENT_PAT):  accent_f.append(name)

    gf_pat = re.compile(r'fonts\.googleapis\.com/css[^"\']*[?&]family=([^"\'&]+)', re.IGNORECASE)
    google_fonts = []
    for src in [html_text, css_text]:
        for gm in gf_pat.finditer(src):
            for fam in gm.group(1).split('|'):
                n = fam.split(':')[0].replace('+', ' ').strip()
                if n and n not in google_fonts:
                    google_fonts.append(n)
                    if n not in seen:
                        seen.add(n)
                        all_f.append(n)

    def _pick(lst, idx=0):
        if lst:
            from collections import Counter
            return Counter(lst).most_common(1)[0][0]
        if google_fonts:
            return google_fonts[min(idx, len(google_fonts) - 1)]
        if all_f:
            return all_f[min(idx, len(all_f) - 1)]
        return None

    h, b, a = _pick(heading_f, 0), _pick(body_f, 1), _pick(accent_f, 2)
    if h and b and h == b:
        rem = [f for f in all_f if f != h]
        if rem:
            b = rem[0]

    return {
        "heading": h, "body": b, "accent": a,
        "all": all_f[:8], "google_fonts": google_fonts,
        "heading_candidates": list(set(heading_f))[:4],
        "body_candidates":    list(set(body_f))[:4],
        "accent_candidates":  list(set(accent_f))[:4],
        "source": "css_analysis" if (heading_f or body_f) else "heuristic",
    }


async def _fetch_external_css(html_text: str, base_url: str) -> str:
    """Laedt verlinkte CSS-Dateien (max 3, 5s Timeout, 200KB max)."""
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    import httpx as _hx

    soup = BeautifulSoup(html_text, 'html.parser')
    parts = []
    for tag in soup.find_all('link', rel=lambda r: r and 'stylesheet' in r)[:3]:
        href = tag.get('href', '')
        if not href or 'fonts.googleapis.com' in href:
            continue
        url = href if href.startswith('http') else urljoin(base_url, href)
        try:
            async with _hx.AsyncClient(timeout=5.0, verify=False) as c:
                resp = await c.get(url, follow_redirects=True)
            if resp.status_code == 200:
                parts.append(resp.text[:200_000])
        except Exception:
            pass
    return '\n'.join(parts)


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

    # SSL-toleranter Fetch: erst mit Zertifikatspruefung, bei Fehler Fallback.
    # Status (ssl_ok/ssl_error) wird sowohl im Lead-Modell als auch in der
    # API-Response zurueckgegeben, damit das Frontend ein Badge anzeigen kann.
    from services.ssl_helper import fetch_with_ssl_fallback_async
    ssl_result = await fetch_with_ssl_fallback_async(website_url)

    if not ssl_result["reachable"]:
        # Website komplett offline — Fehler dokumentieren und Lead trotzdem updaten
        _set(lead, 'ssl_ok',    False)
        _set(lead, 'ssl_error', ssl_result["ssl_error"])
        _set(lead, 'brand_scrape_failed', True)
        db.commit()
        return {
            "success":      False,
            "ssl_ok":       False,
            "ssl_error":    ssl_result["ssl_error"],
            "message":      f"Website nicht erreichbar: {ssl_result['ssl_error']}",
            "primary_color": None,
            "all_fonts":    [],
        }

    html_text = ssl_result["content"] or ""
    ssl_ok    = ssl_result["ssl_ok"]
    ssl_error = ssl_result["ssl_error"]

    try:
        logger.info(
            f"Brand scrape OK for {website_url}: {len(html_text)} chars "
            f"(ssl_ok={ssl_ok})"
        )

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

        # Fonts — Rollen-Analyse (Heading/Body/Accent aus CSS-Selektoren)
        external_css = await _fetch_external_css(html_text, website_url)
        combined_css = html_text + '\n' + external_css
        font_roles = _extract_font_roles(combined_css, html_text)

        font_heading_val  = font_roles.get("heading")
        font_body_val     = font_roles.get("body")
        font_accent_val   = font_roles.get("accent")
        all_fonts         = font_roles.get("all", [])[:6]
        google_fonts_list = font_roles.get("google_fonts", [])

        font_primary   = font_heading_val or (all_fonts[0] if all_fonts else None)
        font_secondary = font_body_val or (all_fonts[1] if len(all_fonts) > 1 else None)

        logger.info(
            f"Font-Analyse {website_url}: heading={font_heading_val}, "
            f"body={font_body_val}, accent={font_accent_val}, google={google_fonts_list}"
        )

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
    # Font-Rollen (Heading/Body/Accent separat)
    _set(lead, 'brand_font_heading', font_heading_val if not scrape_failed else None)
    _set(lead, 'brand_font_body',    font_body_val    if not scrape_failed else None)
    _set(lead, 'brand_font_accent',  font_accent_val  if not scrape_failed else None)
    _set(lead, 'brand_fonts_detail', json.dumps({
        "heading": font_heading_val, "body": font_body_val, "accent": font_accent_val,
        "google_fonts": google_fonts_list if not scrape_failed else [],
        "all": all_fonts,
        "heading_candidates": font_roles.get("heading_candidates", []) if not scrape_failed else [],
        "body_candidates":    font_roles.get("body_candidates", [])    if not scrape_failed else [],
        "accent_candidates":  font_roles.get("accent_candidates", [])  if not scrape_failed else [],
        "source": font_roles.get("source", "unknown") if not scrape_failed else "failed",
    }, ensure_ascii=False) if not scrape_failed else None)
    lead.brand_scrape_failed   = scrape_failed
    lead.brand_scraped_at      = now
    # SSL-Status aus dem Helper persistieren — Frontend rendert dazu ein Badge
    lead.ssl_ok                = ssl_ok
    lead.ssl_error             = ssl_error
    if design_data:
        lead.brand_design_json  = json.dumps(design_data, ensure_ascii=False)
        lead.brand_design_style = design_data.get("style_keyword")
    try:
        db.commit()
        logger.info(
            f"Brand data saved for lead {lead_id}: primary={primary_color}, "
            f"fonts={len(all_fonts)}, ssl_ok={ssl_ok}"
        )
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
        "font_heading":    font_heading_val if not scrape_failed else None,
        "font_body":       font_body_val    if not scrape_failed else None,
        "font_accent":     font_accent_val  if not scrape_failed else None,
        "scrape_failed":   scrape_failed,
        "scraped_at":      str(now)[:16],
        "design_data":     design_data,
        # SSL-Status fuer das Frontend-Badge
        "ssl_ok":          ssl_ok,
        "ssl_error":       ssl_error,
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
        logger.error(f"branddesign analysis failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analyse fehlgeschlagen")

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


# ── Brand Guideline (KI Design-Token-System) ─────────────────────────────────

@router.get("/{lead_id}/guideline")
def get_brand_guideline(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")
    raw = getattr(lead, 'brand_guideline_json', None)
    if not raw:
        return {"generated": False, "guideline": None}
    try:
        return {
            "generated": True,
            "guideline": json.loads(raw),
            "generated_at": str(getattr(lead, 'brand_guideline_generated_at', '') or '')[:16],
        }
    except Exception:
        return {"generated": False, "guideline": None}


@router.post("/{lead_id}/guideline/generate")
async def generate_brand_guideline(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    from database import Briefing
    import httpx

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    primary      = lead.brand_primary_color   or "#000000"
    secondary    = lead.brand_secondary_color or "#333333"
    font_head    = lead.brand_font_primary    or "Georgia"
    font_body    = lead.brand_font_secondary  or "Arial"
    all_colors   = json.loads(lead.brand_colors  or "[]")
    all_fonts    = json.loads(lead.brand_fonts   or "[]")
    design_style = lead.brand_design_style    or "Modern"
    design_json  = getattr(lead, 'brand_design_json', None)
    design_data  = json.loads(design_json) if design_json else {}
    brief        = design_data.get("design_brief", {})
    radius_px    = design_data.get("border_radius_px", 6)
    shadow_lbl   = design_data.get("shadow_label", "leicht")
    btn_style    = design_data.get("button_style", "abgerundet")
    spacing      = design_data.get("spacing_density", "normal")
    farb_stimmung = design_data.get("farb_stimmung", "Neutral")

    gewerk     = (briefing.gewerk     if briefing else "") or (lead.trade or "Handwerk")
    leistungen = (briefing.leistungen if briefing else "") or ""
    usp        = (briefing.usp        if briefing else "") or ""
    city       = lead.city or "Deutschland"
    company    = lead.company_name or ""

    prompt = (
        "Du bist ein professioneller UI/UX-Designer. Erstelle eine vollstaendige "
        "UI Brand Guideline als strukturiertes JSON-Objekt.\n\n"
        f"KUNDENDATEN:\nUnternehmen: {company}\nGewerk: {gewerk} | Stadt: {city}\n"
        f"Leistungen: {leistungen}\nUSP: {usp}\n\n"
        f"ERKANNTE BRAND-DATEN:\nPrimaerfarbe: {primary}\nSekundaerfarbe: {secondary}\n"
        f"Farben: {', '.join(all_colors[:8])}\n"
        f"Schriften: {font_head} (Ueberschriften), {font_body} (Fliesstext)\n"
        f"Stil: {design_style} | Stimmung: {farb_stimmung}\n"
        f"Radius: {radius_px}px ({btn_style}) | Schatten: {shadow_lbl} | Dichte: {spacing}\n\n"
        f"KI DESIGN-BRIEF: {json.dumps(brief, ensure_ascii=False)[:600] if brief else 'nicht vorhanden'}\n\n"
        "AUFGABE: Erstelle ein vollstaendiges Design-Token-System. Leite aus der Primaerfarbe "
        f"{primary} automatisch Dark/Light-Varianten ab.\n\n"
        "Antworte NUR als JSON-Objekt (kein Markdown):\n"
        '{"meta":{"company":"...","gewerk":"...","style_keyword":"...","farb_stimmung":"..."},'
        '"colors":{"primary":"...","primary_dark":"...","primary_light":"...","primary_subtle":"...",'
        '"secondary":"...","accent":"...","surface":"...","surface_raised":"...","border":"...",'
        '"text_primary":"...","text_secondary":"...","text_tertiary":"...","text_inverse":"#FFF",'
        '"success":"#1D9E75","warning":"#F59E0B","error":"#E74C3C","info":"#3B82F6"},'
        '"typography":{"font_heading":"...","font_body":"...","font_mono":"JetBrains Mono",'
        '"scale":{"h1":{"size":"48px","weight":"700","line_height":"1.1","letter_spacing":"-0.02em"},'
        '"h2":{"size":"32px","weight":"700","line_height":"1.2"},'
        '"h3":{"size":"24px","weight":"600","line_height":"1.3"},'
        '"h4":{"size":"20px","weight":"600","line_height":"1.4"},'
        '"body_lg":{"size":"18px","weight":"400","line_height":"1.75"},'
        '"body":{"size":"16px","weight":"400","line_height":"1.75"},'
        '"body_sm":{"size":"14px","weight":"400","line_height":"1.6"},'
        '"label":{"size":"12px","weight":"700","text_transform":"uppercase","letter_spacing":"0.06em"},'
        '"caption":{"size":"11px","weight":"400","line_height":"1.5"},'
        '"button":{"size":"14px","weight":"700","text_transform":"uppercase","letter_spacing":"0.05em"}}},'
        '"spacing":{"xs":"4px","sm":"8px","md":"16px","lg":"24px","xl":"32px","2xl":"48px","3xl":"64px","4xl":"96px"},'
        f'"border_radius":{{"sm":"{max(1,radius_px//2)}px","md":"{radius_px}px","lg":"{int(radius_px*1.5)}px","xl":"{radius_px*2}px","full":"9999px"}},'
        '"shadows":{"sm":"...","md":"...","lg":"...","none":"none"},'
        '"components":{"button_primary":{"background":"...","color":"...","border_radius":"...","padding":"10px 24px"},'
        '"button_secondary":{"background":"transparent","color":"...","border":"1.5px solid ...","border_radius":"...","padding":"10px 24px"},'
        '"button_accent":{"background":"...","color":"...","border_radius":"...","padding":"10px 24px"},'
        '"card":{"background":"...","border":"...","border_radius":"...","shadow":"...","padding":"24px"},'
        '"input":{"background":"...","border":"...","border_radius":"...","padding":"10px 14px","focus_border":"..."},'
        '"nav":{"background":"...","text_color":"...","height":"64px","logo_height":"36px"},'
        '"hero":{"background":"...","text_color":"...","padding_y":"80px"},'
        '"footer":{"background":"...","text_color":"rgba(255,255,255,0.7)","padding_y":"48px"}},'
        '"css_variables":"<vollstaendige :root { --var: value; } CSS als String>",'
        '"voice_tone":{"charakter":"<2-3 Adjektive>","ansprache":"<Du/Sie>","cta_beispiele":["<CTA1>","<CTA2>","<CTA3>"]}}'
    )

    # DB vor langem Claude-Call freigeben
    db.close()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        raw_text = resp.json()["content"][0]["text"].strip()
        raw_text = re.sub(r'^```json\s*', '', raw_text)
        raw_text = re.sub(r'^```\s*', '', raw_text)
        raw_text = re.sub(r'\s*```$', '', raw_text)
        guideline = json.loads(raw_text)
    except Exception as e:
        raise HTTPException(500, f"Guideline-Generierung fehlgeschlagen: {str(e)[:200]}")

    from database import SessionLocal
    db2 = SessionLocal()
    try:
        lead2 = db2.query(Lead).filter(Lead.id == lead_id).first()
        if lead2:
            _set(lead2, 'brand_guideline_json', json.dumps(guideline, ensure_ascii=False))
            _set(lead2, 'brand_guideline_generated_at', datetime.utcnow())
            db2.commit()
    except Exception as e:
        db2.rollback()
        raise HTTPException(500, f"Speichern fehlgeschlagen: {str(e)[:100]}")
    finally:
        db2.close()

    return {"generated": True, "guideline": guideline}


@router.put("/{lead_id}/guideline")
def save_brand_guideline(
    lead_id: int, body: dict,
    db: Session = Depends(get_db), _=Depends(require_any_auth),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")
    guideline = body.get("guideline")
    if not guideline:
        raise HTTPException(400, "guideline fehlt")
    _set(lead, 'brand_guideline_json', json.dumps(guideline, ensure_ascii=False))
    _set(lead, 'brand_guideline_generated_at', datetime.utcnow())
    db.commit()
    return {"saved": True}
