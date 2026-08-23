"""Der Markenleitfaden — erzeugen, lesen, aendern (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/branddesign.py` hatte 980 Zeilen
und darin **zwei Bloecke mit je ueber 200**: das Ablesen von der Website und
das Erzeugen des Leitfadens. Fuenf Funktionen, davon das Erzeugen mit 213 Zeilen. Der Leitfaden ist
das Ergebnis; die Erhebung drueben ist der Weg dorthin.

Der Router kommt aus `branddesign` — dort steht er mit seiner Sperre.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, Lead, Briefing
import httpx, re, os, json, anthropic, logging
from datetime import datetime
from services.ki_aufruf import frag_modell

from routers.branddesign import router, _set

logger = logging.getLogger(__name__)


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
        message = await frag_modell(
            client,
            model="claude-sonnet-5", thinking={"type": "disabled"},
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
