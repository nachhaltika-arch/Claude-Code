"""Was von der Website eines Kunden abgelesen wird (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/branddesign.py` hatte 980 Zeilen
und darin **zwei Bloecke mit je ueber 200**: das Ablesen von der Website und
das Erzeugen des Leitfadens. Sieben Funktionen, davon eine mit 223 Zeilen: Farben, Schriften und
Analyse-Einbindung von der bestehenden Seite ablesen.

Der Router kommt aus `branddesign` — dort steht er mit seiner Sperre.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, Lead, Briefing
import httpx, re, os, json, anthropic, logging
from datetime import datetime

from routers.branddesign import router, _set

logger = logging.getLogger(__name__)


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
                        json={"model": "claude-sonnet-5", "thinking": {"type": "disabled"}, "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]},
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
                json={"model": "claude-sonnet-5", "thinking": {"type": "disabled"}, "max_tokens": 500,
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
            model="claude-sonnet-5", thinking={"type": "disabled"}, max_tokens=800,
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
