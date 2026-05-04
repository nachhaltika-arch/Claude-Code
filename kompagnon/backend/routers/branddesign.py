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

    design_tokens = None
    raw_tokens = getattr(lead, 'brand_design_tokens_json', None)
    if raw_tokens:
        try:
            design_tokens = json.loads(raw_tokens)
        except Exception:
            pass

    fonts_detail = None
    raw_fd = getattr(lead, 'brand_fonts_detail', None)
    if raw_fd:
        try: fonts_detail = json.loads(raw_fd)
        except Exception: pass

    return {
        "lead_id":         lead_id,
        "primary_color":   lead.brand_primary_color,
        "secondary_color": lead.brand_secondary_color,
        "font_primary":    lead.brand_font_primary,
        "font_secondary":  lead.brand_font_secondary,
        "font_heading":    getattr(lead, 'brand_font_heading', None) or lead.brand_font_primary,
        "font_body":       getattr(lead, 'brand_font_body',    None) or lead.brand_font_secondary,
        "font_accent":     getattr(lead, 'brand_font_accent',  None),
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
        "design_tokens":     design_tokens,
        "fonts_detail":      fonts_detail,
        "guideline_generated": bool(getattr(lead, 'brand_guideline_generated_at', None)),
        "guideline_generated_at": str(getattr(lead, 'brand_guideline_generated_at', '') or '')[:16] or None,
    }


# ── Endpoint 1b — Manual save ─────────────────────────────────────────────────

@router.put("/{lead_id}")
def update_brand_design(lead_id: int, body: dict, db: Session = Depends(get_db)):
    """Manuelle Branddesign-Felder speichern."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")
    mapping = {
        "primary_color":   "brand_primary_color",
        "secondary_color": "brand_secondary_color",
        "font_primary":    "brand_font_primary",
        "font_secondary":  "brand_font_secondary",
        "font_heading":    "brand_font_heading",
        "font_body":       "brand_font_body",
        "font_accent":     "brand_font_accent",
        "design_style":    "brand_design_style",
        "brand_notes":     "brand_notes",
        "logo_url":        "brand_logo_url",
    }
    updated = []
    for body_field, lead_attr in mapping.items():
        if body_field in body:
            _set(lead, lead_attr, body[body_field])
            updated.append(body_field)

    if "design_tokens" in body:
        tokens = body["design_tokens"]
        _set(lead, 'brand_design_tokens_json',
             json.dumps(tokens, ensure_ascii=False) if isinstance(tokens, dict) else tokens)
        updated.append("design_tokens")
        if isinstance(tokens, dict):
            if tokens.get("primary"):    _set(lead, 'brand_primary_color',  tokens["primary"])
            if tokens.get("secondary"):  _set(lead, 'brand_secondary_color', tokens["secondary"])
            if tokens.get("font_h1"):    _set(lead, 'brand_font_heading', tokens["font_h1"])
            if tokens.get("font_body"):  _set(lead, 'brand_font_body',    tokens["font_body"])
            if tokens.get("font_akzent"):_set(lead, 'brand_font_accent',  tokens["font_akzent"])

    if updated:
        _set(lead, 'brand_scraped_at', datetime.utcnow())
        db.commit()
    return {"saved": True, "updated_fields": updated}


# ── Endpoint 1c — Font suggestions ────────────────────────────────────────────

@router.post("/{lead_id}/suggest-fonts")
async def suggest_fonts(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead: raise HTTPException(404, "Lead nicht gefunden")

    fd = {}
    try: fd = json.loads(getattr(lead, 'brand_fonts_detail', '') or '{}')
    except Exception: pass

    detected_heading = getattr(lead, 'brand_font_heading', None) or fd.get('heading') or ''
    detected_body    = getattr(lead, 'brand_font_body',    None) or fd.get('body')    or ''
    detected_accent  = getattr(lead, 'brand_font_accent',  None) or fd.get('accent')  or ''
    google_fonts     = fd.get('google_fonts', [])

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"heading": {"name": "Playfair Display", "reason": "Klassisch für Handwerk"},
                "body":    {"name": "Inter",            "reason": "Modern, gut lesbar"},
                "accent":  {"name": "Barlow Condensed", "reason": "Kraftvoll für CTAs"},
                "source": "fallback"}

    prompt = (
        f"Du bist Typografie-Experte für Handwerksbetriebe.\n"
        f"KUNDE: {lead.company_name} | Gewerk: {getattr(lead, 'trade', '')}\n"
        f"ERKANNT AUF ALTER WEBSITE: heading={detected_heading or 'unbekannt'}, "
        f"body={detected_body or 'unbekannt'}, accent={detected_accent or 'unbekannt'}\n"
        f"Google Fonts: {', '.join(google_fonts) or 'keine'}\n\n"
        f"Empfehle 3 Google Fonts (heading/body/accent) für die NEUE Website.\n"
        f"Antworte NUR als JSON: "
        f'{{"heading":{{"name":"...","category":"...","reason":"..."}},'
        f'"body":{{"name":"...","category":"...","reason":"..."}},'
        f'"accent":{{"name":"...","category":"...","reason":"..."}},'
        f'"pairing_note":"..."}}'
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 500,
                      "messages": [{"role": "user", "content": prompt}]},
            )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        text = re.sub(r'^```json\s*|\s*```$', '', text)
        result = json.loads(text)
        result["source"] = "claude"
        result["detected"] = {"heading": detected_heading, "body": detected_body,
                              "accent": detected_accent, "google_fonts": google_fonts}
        return result
    except Exception as e:
        raise HTTPException(500, f"Font-Vorschläge fehlgeschlagen: {str(e)[:100]}")


def _extract_font_roles(css_text: str, html_text: str) -> dict:
    """Analysiert CSS/HTML und erkennt Schriften nach Rolle (heading/body/accent)."""
    import re as _re
    from collections import Counter

    HEADING_SEL = [r'h[1-6]\b', r'\.heading', r'\.title', r'\.headline', r'\.hero', r'\.display']
    BODY_SEL    = [r'\bbody\b', r'\bp\b', r'main\b', r'article\b', r'\.content\b', r'\.text\b']
    ACCENT_SEL  = [r'\bbtn\b', r'\.btn\b', r'button\b', r'\bnav\b', r'\.cta\b', r'blockquote\b']

    GENERIC = {
        'inherit','initial','unset','serif','sans-serif','monospace','cursive',
        'system-ui','-apple-system','blinkmacsystemfont','segoe ui',
        'helvetica neue','helvetica','arial','times new roman','courier new',
    }

    def clean(raw):
        name = raw.strip().strip("'\"").split(',')[0].strip()
        return None if not name or name.lower() in GENERIC else name

    def matches(selector, patterns):
        sel = selector.lower()
        return any(_re.search(p, sel) for p in patterns)

    rule_re = _re.compile(r'([^{}@][^{}]*?)\{([^{}]*?font-family\s*:[^;}]+[^{}]*?)\}', _re.DOTALL | _re.I)
    font_re = _re.compile(r'font-family\s*:\s*([^;}{]+)', _re.I)
    gf_re   = _re.compile(r'fonts\.googleapis\.com/css[^"\']*[?&]family=([^"\'&]+)', _re.I)

    heading_f, body_f, accent_f = [], [], []
    all_seen, all_fonts = set(), []

    for m in rule_re.finditer(css_text):
        sel, body = m.group(1).strip(), m.group(2)
        fm = font_re.search(body)
        if not fm: continue
        fn = clean(fm.group(1).split(',')[0])
        if not fn: continue
        if fn not in all_seen:
            all_seen.add(fn); all_fonts.append(fn)
        if matches(sel, HEADING_SEL): heading_f.append(fn)
        if matches(sel, BODY_SEL):    body_f.append(fn)
        if matches(sel, ACCENT_SEL):  accent_f.append(fn)

    google_fonts = []
    for text in [html_text, css_text]:
        for m in gf_re.finditer(text):
            for fam in m.group(1).split('|'):
                n = fam.split(':')[0].replace('+', ' ').strip()
                if n and n not in google_fonts:
                    google_fonts.append(n)
                    if n not in all_seen:
                        all_seen.add(n); all_fonts.append(n)

    def pick(lst, idx=0):
        if lst: return Counter(lst).most_common(1)[0][0]
        if google_fonts: return google_fonts[min(idx, len(google_fonts)-1)]
        if all_fonts: return all_fonts[min(idx, len(all_fonts)-1)]
        return None

    heading = pick(heading_f, 0)
    body    = pick(body_f,    1)
    accent  = pick(accent_f,  2)
    if heading and body and heading == body:
        rem = [f for f in all_fonts if f != heading]
        if rem: body = rem[0]

    return {
        "heading": heading, "body": body, "accent": accent,
        "all": all_fonts[:8], "google_fonts": google_fonts,
        "heading_candidates": list(set(heading_f))[:4],
        "body_candidates":    list(set(body_f))[:4],
        "accent_candidates":  list(set(accent_f))[:4],
        "source": "css_analysis" if (heading_f or body_f) else "heuristic",
    }


async def _fetch_external_css(html_text: str, base_url: str) -> str:
    """Lädt bis zu 3 externe CSS-Dateien und gibt kombinierten CSS-Text zurück."""
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    import httpx as _httpx

    soup = BeautifulSoup(html_text, 'html.parser')
    css_parts = []
    for tag in soup.find_all('link', rel=lambda r: r and 'stylesheet' in r)[:3]:
        href = tag.get('href', '')
        if not href or 'fonts.googleapis.com' in href: continue
        url = href if href.startswith('http') else urljoin(base_url, href)
        try:
            async with _httpx.AsyncClient(timeout=5.0, verify=False) as client:
                resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                css_parts.append(resp.text[:200_000])
        except Exception:
            pass
    return '\n'.join(css_parts)


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
    font_heading = font_body_val = font_accent = None
    google_fonts: list[str] = []
    font_roles: dict = {}
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

        # ── Fonts: Rollen-Analyse ──────────────────────────────────────────────
        external_css = await _fetch_external_css(html_text, website_url)
        combined_css = html_text + '\n' + external_css

        font_roles    = _extract_font_roles(combined_css, html_text)
        font_heading  = font_roles.get("heading")
        font_body_val = font_roles.get("body")
        font_accent   = font_roles.get("accent")
        all_fonts     = font_roles.get("all", [])[:6]
        google_fonts  = font_roles.get("google_fonts", [])

        # Rückwärtskompatibilität
        font_primary   = font_heading or (all_fonts[0] if all_fonts else None)
        font_secondary = font_body_val or (all_fonts[1] if len(all_fonts) > 1 else None)

        logger.info(f"Font-Analyse {website_url}: heading={font_heading}, body={font_body_val}, accent={font_accent}, google={google_fonts}")

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
    _set(lead, 'brand_font_heading', font_heading)
    _set(lead, 'brand_font_body',    font_body_val)
    _set(lead, 'brand_font_accent',  font_accent)
    _set(lead, 'brand_fonts_detail', json.dumps({
        "heading": font_heading, "body": font_body_val, "accent": font_accent,
        "google_fonts": google_fonts, "all": all_fonts,
        "heading_candidates": font_roles.get("heading_candidates", []),
        "body_candidates":    font_roles.get("body_candidates", []),
        "accent_candidates":  font_roles.get("accent_candidates", []),
        "source": font_roles.get("source", "unknown"),
    }, ensure_ascii=False))
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

    # ── Design-Tokens laden — Priorität: vollständiges design_tokens_json ──
    tokens_raw = {}
    raw_tokens = getattr(lead, 'brand_design_tokens_json', None)
    if raw_tokens:
        try:
            tokens_raw = json.loads(raw_tokens)
        except Exception:
            pass

    dd_raw        = getattr(lead, 'brand_design_json', None)
    dd            = json.loads(dd_raw) if dd_raw else {}
    brief         = dd.get('design_brief', {})

    primary       = tokens_raw.get("primary")       or getattr(lead, 'brand_primary_color',   None) or '#004F59'
    secondary     = tokens_raw.get("secondary")     or getattr(lead, 'brand_secondary_color', None) or '#2C3E50'
    accent        = tokens_raw.get("accent")        or brief.get('akzentfarbe', '#FAE600')
    color_bg      = tokens_raw.get("color_bg")      or '#F5F5F0'
    color_field   = tokens_raw.get("color_field")   or '#FFFFFF'
    color_heading = tokens_raw.get("color_heading") or '#FFFFFF'
    color_text    = tokens_raw.get("color_text")    or '#333333'
    font_h1       = tokens_raw.get("font_h1")       or getattr(lead, 'brand_font_heading', None) or getattr(lead, 'brand_font_primary',   None) or 'Georgia'
    font_body     = tokens_raw.get("font_body")     or getattr(lead, 'brand_font_body',    None) or getattr(lead, 'brand_font_secondary', None) or 'Arial'
    font_akzent   = tokens_raw.get("font_akzent")   or getattr(lead, 'brand_font_accent',  None) or 'Barlow Condensed'
    color_font_h1    = tokens_raw.get("color_font_h1")    or '#FFFFFF'
    color_font_body  = tokens_raw.get("color_font_body")  or 'rgba(255,255,255,0.75)'
    color_font_cta   = tokens_raw.get("color_font_cta")   or '#000000'
    radius        = tokens_raw.get("radius")        or dd.get('border_radius_px', 6)
    shadow_lbl    = tokens_raw.get("shadow")        or dd.get('shadow_label', 'leicht')
    farb_stimmung = dd.get('farb_stimmung', 'Neutral')
    style         = tokens_raw.get("style") or getattr(lead, 'brand_design_style', None) or dd.get('style_keyword', 'Modern')
    company       = getattr(lead, 'company_name', '') or 'Unbekannt'
    city          = getattr(lead, 'city', '') or 'Deutschland'
    gewerk        = (briefing.gewerk     if briefing else '') or getattr(lead, 'trade', '') or 'Handwerk'
    leistungen    = (briefing.leistungen if briefing else '') or ''
    usp           = (briefing.usp        if briefing else '') or ''

    prompt = f"""Du bist ein professioneller UI/UX-Designer und Brand-Strategist.
Erstelle eine vollständige UI Brand Guideline als strukturiertes JSON.

=== KUNDENDATEN ===
Unternehmen: {company} | Gewerk: {gewerk} | Stadt: {city}
Leistungen: {leistungen[:300] if leistungen else 'nicht angegeben'}
USP: {usp[:200] if usp else 'nicht angegeben'}

=== EXAKTE DESIGN-TOKENS (vom Admin festgelegt — 1:1 übernehmen) ===
FARBEN:
  Primär:           {primary}
  Sekundär:         {secondary}
  Akzent:           {accent}
  Hintergrund:      {color_bg}
  Felder/Inputs:    {color_field}
  Überschrift-Text: {color_heading}
  Fließtext:        {color_text}

SCHRIFTEN:
  Überschriften (H1/H2/H3): {font_h1}   Textfarbe: {color_font_h1}
  Fließtext:                  {font_body} Textfarbe: {color_font_body}
  Akzent/CTA:                 {font_akzent} Textfarbe: {color_font_cta}

STIL:
  Ecken-Radius: {radius}px | Schatten: {shadow_lbl} | Stil: {style} | Farb-Stimmung: {farb_stimmung}

KI-DESIGN-BRIEF:
{json.dumps(brief, ensure_ascii=False) if brief else 'nicht vorhanden'}

Antworte NUR als JSON (kein Markdown):

{{
  "meta": {{
    "company": "{company}",
    "gewerk": "{gewerk}",
    "style_keyword": "{style}",
    "farb_stimmung": "{farb_stimmung}"
  }},
  "tokens": {{
    "primary":        "{primary}",
    "primary_dark":   "<10% dunkler als {primary}>",
    "primary_light":  "<20% heller als {primary}>",
    "primary_subtle": "<{primary} mit 10% Opacity als rgba>",
    "secondary":      "{secondary}",
    "accent":         "{accent}",
    "bg":             "{color_bg}",
    "field":          "{color_field}",
    "heading_text":   "{color_heading}",
    "body_text":      "{color_text}",
    "border":         "<dezente Rahmenfarbe>",
    "text_muted":     "<abgeschwächte Textfarbe>",
    "success":        "#1D9E75",
    "warning":        "#F59E0B",
    "error":          "#E74C3C"
  }},
  "typography": {{
    "fonts": {{
      "heading": "{font_h1}",
      "body":    "{font_body}",
      "accent":  "{font_akzent}"
    }},
    "colors": {{
      "heading": "{color_font_h1}",
      "body":    "{color_font_body}",
      "cta":     "{color_font_cta}"
    }},
    "scale": {{
      "h1":      {{"size":"48px","weight":"700","family":"{font_h1}","color":"{color_font_h1}","line_height":"1.1","letter_spacing":"-0.02em"}},
      "h2":      {{"size":"32px","weight":"700","family":"{font_h1}","color":"{color_font_h1}","line_height":"1.2"}},
      "h3":      {{"size":"24px","weight":"600","family":"{font_h1}","color":"{color_font_h1}","line_height":"1.3"}},
      "body_lg": {{"size":"18px","weight":"400","family":"{font_body}","color":"{color_text}","line_height":"1.75"}},
      "body":    {{"size":"16px","weight":"400","family":"{font_body}","color":"{color_text}","line_height":"1.75"}},
      "body_sm": {{"size":"14px","weight":"400","family":"{font_body}","color":"{color_text}","line_height":"1.6"}},
      "label":   {{"size":"12px","weight":"700","family":"{font_body}","text_transform":"uppercase","letter_spacing":"0.06em"}},
      "button":  {{"size":"14px","weight":"700","family":"{font_akzent}","color":"{color_font_cta}","text_transform":"uppercase","letter_spacing":"0.05em"}}
    }}
  }},
  "spacing": {{"xs":"4px","sm":"8px","md":"16px","lg":"24px","xl":"32px","2xl":"48px","3xl":"64px","4xl":"96px"}},
  "border_radius": {{"sm":"<{radius}/2 px>","md":"{radius}px","lg":"<{radius}*1.5 px>","xl":"<{radius}*2 px>","full":"9999px"}},
  "shadows": {{"none":"none","sm":"<passend zu '{shadow_lbl}'>","md":"<mittel>","lg":"<stark>"}},
  "components": {{
    "button_primary":   {{"background":"{primary}","color":"{color_font_cta}","font_family":"{font_akzent}","border_radius":"{radius}px","padding":"10px 24px","font_weight":"700","text_transform":"uppercase"}},
    "button_secondary": {{"background":"transparent","color":"{primary}","border":"1.5px solid {primary}","border_radius":"{radius}px","padding":"10px 24px","font_family":"{font_akzent}"}},
    "button_accent":    {{"background":"{accent}","color":"{color_font_cta}","border_radius":"{radius}px","padding":"10px 24px","font_family":"{font_akzent}"}},
    "card":  {{"background":"{color_field}","border":"0.5px solid <tokens.border>","border_radius":"<border_radius.lg>","shadow":"<shadows.sm>","padding":"24px","title_font":"{font_h1}","title_color":"{color_heading}","body_font":"{font_body}","body_color":"{color_text}"}},
    "input": {{"background":"{color_field}","border":"1px solid <tokens.border>","border_radius":"{radius}px","padding":"10px 14px","font_family":"{font_body}","color":"{color_text}","focus_border":"{primary}"}},
    "nav":   {{"background":"{primary}","text_color":"{color_font_h1}","height":"64px","font_family":"{font_h1}"}},
    "hero":  {{"background":"{primary}","h1_font":"{font_h1}","h1_color":"{color_font_h1}","body_font":"{font_body}","body_color":"{color_font_body}","padding_y":"80px"}},
    "section":{{"background":"{color_bg}","h2_font":"{font_h1}","body_font":"{font_body}","body_color":"{color_text}","padding_y":"64px"}},
    "footer": {{"background":"{secondary}","text_color":"rgba(255,255,255,0.65)","padding_y":"48px"}}
  }},
  "css_variables": "<vollständige :root {{ --token: value; }} CSS als ein String>",
  "voice_tone": {{
    "charakter": "<2-3 Adjektive>",
    "ansprache": "<Du/Sie>",
    "cta_beispiele": ["<CTA 1 für {gewerk}>", "<CTA 2>", "<CTA 3>"]
  }},
  "ki_design_brief": "<100-150 Wörter: vollständige Design-System-Beschreibung für KI-Template-Generierung>"
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
        r = int(radius) if str(radius).isdigit() else 6
        guideline = {
            "meta": {"company": company, "gewerk": gewerk, "style_keyword": style, "farb_stimmung": farb_stimmung},
            "tokens": {
                "primary": primary, "primary_dark": primary, "secondary": secondary,
                "accent": accent, "bg": color_bg, "field": color_field,
                "heading_text": color_heading, "body_text": color_text,
                "border": "#E0E0E0", "text_muted": "#999999",
                "success": "#1D9E75", "warning": "#F59E0B", "error": "#E74C3C",
            },
            "typography": {
                "fonts": {"heading": font_h1, "body": font_body, "accent": font_akzent},
                "colors": {"heading": color_font_h1, "body": color_font_body, "cta": color_font_cta},
                "scale": {
                    "h1": {"size": "48px", "weight": "700", "family": font_h1, "color": color_font_h1, "line_height": "1.1"},
                    "h2": {"size": "32px", "weight": "700", "family": font_h1, "color": color_font_h1, "line_height": "1.2"},
                    "body": {"size": "16px", "weight": "400", "family": font_body, "color": color_text, "line_height": "1.75"},
                    "button": {"size": "14px", "weight": "700", "family": font_akzent, "color": color_font_cta, "text_transform": "uppercase"},
                },
            },
            "spacing": {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px"},
            "border_radius": {"sm": f"{max(2, r//2)}px", "md": f"{r}px", "lg": f"{int(r*1.5)}px", "full": "9999px"},
            "shadows": {"none": "none", "sm": "0 1px 3px rgba(0,0,0,.08)", "md": "0 4px 12px rgba(0,0,0,.12)"},
            "components": {
                "button_primary":   {"background": primary, "color": color_font_cta, "border_radius": f"{r}px", "padding": "10px 24px"},
                "button_secondary": {"background": "transparent", "color": primary, "border": f"1.5px solid {primary}", "border_radius": f"{r}px", "padding": "10px 24px"},
                "button_accent":    {"background": accent, "color": color_font_cta, "border_radius": f"{r}px", "padding": "10px 24px"},
                "nav":  {"background": primary, "text_color": color_font_h1, "height": "64px"},
                "hero": {"background": primary, "h1_color": color_font_h1, "body_color": color_font_body},
            },
            "css_variables": f":root {{\n  --color-primary: {primary};\n  --color-secondary: {secondary};\n  --color-accent: {accent};\n  --color-bg: {color_bg};\n  --font-heading: \"{font_h1}\", serif;\n  --font-body: \"{font_body}\", sans-serif;\n  --radius-md: {r}px;\n}}",
            "voice_tone": {"charakter": style, "ansprache": "Sie", "cta_beispiele": ["Jetzt anfragen", "Mehr erfahren", "Kontakt aufnehmen"]},
            "ki_design_brief": f"Design-System für {company}. Primärfarbe: {primary}, Akzent: {accent}. Fonts: {font_h1} (Überschriften), {font_body} (Fließtext). Stil: {style}. Radius: {r}px.",
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
