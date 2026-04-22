"""
Briefings CRUD — flat project-briefing fields.
GET  /api/briefings/{lead_id}  → load (auto-creates if missing)
POST /api/briefings/{lead_id}  → create or overwrite
PUT  /api/briefings/{lead_id}  → partial update
"""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db, Briefing, Lead
from routers.auth_router import require_any_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/briefings", tags=["briefings"])

FLAT_FIELDS = [
    "project_id", "gewerk", "wz_code", "wz_title", "leistungen", "einzugsgebiet", "usp",
    "mitbewerber", "vorbilder", "farben", "wunschseiten", "stil",
    "logo_vorhanden", "fotos_vorhanden", "sonstige_hinweise", "status",
    "hauptziel", "aktionen", "typischer_kunde", "haeufige_anfrage",
]


class BriefingBody(BaseModel):
    project_id: Optional[int] = None
    gewerk: Optional[str] = None
    wz_code: Optional[str] = None
    wz_title: Optional[str] = None
    leistungen: Optional[str] = None
    einzugsgebiet: Optional[str] = None
    usp: Optional[str] = None
    mitbewerber: Optional[str] = None
    vorbilder: Optional[str] = None
    farben: Optional[str] = None
    wunschseiten: Optional[str] = None
    stil: Optional[str] = None
    logo_vorhanden: Optional[bool] = None
    fotos_vorhanden: Optional[bool] = None
    sonstige_hinweise: Optional[str] = None
    status: Optional[str] = None
    hauptziel: Optional[str] = None
    aktionen: Optional[str] = None
    typischer_kunde: Optional[str] = None
    haeufige_anfrage: Optional[str] = None


def _serialize(b: Briefing) -> dict:
    def _parse(val):
        if not val:
            return {}
        if isinstance(val, dict):
            return val
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return {}

    return {
        "id":                b.id,
        "lead_id":           b.lead_id,
        # Legacy JSON sections
        "projektrahmen":     _parse(getattr(b, "projektrahmen",  None)),
        "positionierung":    _parse(getattr(b, "positionierung", None)),
        "zielgruppe":        _parse(getattr(b, "zielgruppe",     None)),
        "wettbewerb":        _parse(getattr(b, "wettbewerb",     None)),
        "inhalte":           _parse(getattr(b, "inhalte",        None)),
        "funktionen":        _parse(getattr(b, "funktionen",     None)),
        "branding":          _parse(getattr(b, "branding",       None)),
        "struktur":          _parse(getattr(b, "struktur",       None)),
        "hosting":           _parse(getattr(b, "hosting",        None)),
        "seo":               _parse(getattr(b, "seo",            None)),
        "projektplan":       _parse(getattr(b, "projektplan",    None)),
        "freigaben":         _parse(getattr(b, "freigaben",      None)),
        # Flat fields
        "project_id":        getattr(b, "project_id",        None),
        "gewerk":            getattr(b, "gewerk",            "") or "",
        "wz_code":           getattr(b, "wz_code",           "") or "",
        "wz_title":          getattr(b, "wz_title",          "") or "",
        "leistungen":        getattr(b, "leistungen",        "") or "",
        "einzugsgebiet":     getattr(b, "einzugsgebiet",     "") or "",
        "usp":               getattr(b, "usp",               "") or "",
        "mitbewerber":       getattr(b, "mitbewerber",       "") or "",
        "vorbilder":         getattr(b, "vorbilder",         "") or "",
        "farben":            getattr(b, "farben",            "") or "",
        "wunschseiten":      getattr(b, "wunschseiten",      "") or "",
        "stil":              getattr(b, "stil",              "") or "",
        "logo_vorhanden":    bool(getattr(b, "logo_vorhanden",  False)),
        "fotos_vorhanden":   bool(getattr(b, "fotos_vorhanden", False)),
        "sonstige_hinweise": getattr(b, "sonstige_hinweise", "") or "",
        "status":            getattr(b, "status",            "entwurf") or "entwurf",
        "hauptziel":         getattr(b, "hauptziel",         "") or "",
        "aktionen":          getattr(b, "aktionen",          "") or "",
        "typischer_kunde":   getattr(b, "typischer_kunde",   "") or "",
        "haeufige_anfrage":  getattr(b, "haeufige_anfrage",  "") or "",
        "created_at":        str(b.created_at)[:16] if b.created_at else "",
        "updated_at":        str(b.updated_at)[:16] if b.updated_at else "",
    }


@router.get("/{lead_id}")
def get_briefing(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Load briefing for a lead; auto-creates if none exists."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        briefing = Briefing(lead_id=lead_id, status="entwurf")
        db.add(briefing)
        try:
            db.commit()
            db.refresh(briefing)
        except Exception as e:
            db.rollback()
            logger.error(f"Briefing auto-create failed: {e}")
            raise HTTPException(422, f"Erstellen fehlgeschlagen: {str(e)[:200]}")
    return _serialize(briefing)


@router.post("/{lead_id}")
def create_briefing(
    lead_id: int,
    body: BriefingBody,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Create or fully overwrite the flat briefing fields for a lead."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        briefing = Briefing(lead_id=lead_id)
        db.add(briefing)

    data = body.model_dump(exclude_unset=False)
    for field in FLAT_FIELDS:
        val = data.get(field)
        if val is not None:
            setattr(briefing, field, val)

    briefing.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(briefing)
    except Exception as e:
        db.rollback()
        logger.error(f"Briefing POST commit failed: {e}")
        raise HTTPException(422, f"Speichern fehlgeschlagen: {str(e)[:200]}")
    return _serialize(briefing)


@router.get("/{lead_id}/pdf")
def briefing_pdf(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generate and return briefing as PDF (application/pdf)."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    company_name = (lead.display_name or lead.company_name) if lead else f"Lead #{lead_id}"

    from services.briefing_pdf import generate_briefing_pdf
    pdf_bytes = generate_briefing_pdf(briefing, company_name)

    filename = f"briefing-{lead_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.put("/{lead_id}")
def update_briefing(
    lead_id: int,
    body: BriefingBody,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Partial update — only fields present in the request body are changed."""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    data = body.model_dump(exclude_unset=True)
    for field in FLAT_FIELDS:
        if field in data:
            setattr(briefing, field, data[field])

    briefing.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(briefing)
    except Exception as e:
        db.rollback()
        logger.error(f"Briefing PUT commit failed: {e}")
        raise HTTPException(422, f"Speichern fehlgeschlagen: {str(e)[:200]}")
    return _serialize(briefing)


@router.post("/{lead_id}/suggest-field")
async def suggest_field(
    lead_id: int,
    data: dict,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Claude analysiert Website-Content und schlaegt Wert fuer ein Briefing-Feld vor."""
    import os, httpx, re
    from sqlalchemy import text as sa_text

    field = data.get("field", "")
    if not field:
        raise HTTPException(400, "field fehlt")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    rows = db.execute(
        sa_text("SELECT url, title, h1, h2s, text_preview, full_text FROM website_content_cache WHERE customer_id = :lid ORDER BY word_count DESC LIMIT 8"),
        {"lid": lead_id},
    ).fetchall()

    if not rows:
        raise HTTPException(400, "Kein Website-Content vorhanden")

    content_parts = []
    for row in rows:
        url, title, h1, h2s_json, preview, full_text = row
        h2s = []
        try:
            h2s = json.loads(h2s_json or '[]')
        except Exception:
            pass
        part = f"URL: {url}\nH1: {h1 or title}"
        if h2s:
            part += "\nH2: " + " | ".join(h2s[:5])
        if preview:
            part += f"\nText: {preview[:400]}"
        content_parts.append(part)

    website_content = "\n\n---\n\n".join(content_parts)

    FIELD_PROMPTS = {
        "gewerk": "Erkenne die Hauptbranche/das Gewerk. Antworte NUR mit dem Gewerknamen. Max 40 Zeichen.",
        "leistungen": "Liste alle konkreten Leistungen auf. Eine pro Zeile. Max 10 Zeilen.",
        "einzugsgebiet": "Erkenne die Region/Stadt. Antworte mit Stadt und Radius. Max 80 Zeichen.",
        "zielgruppe": "Primaere Zielgruppe. Antworte NUR mit: Privatkunden, Geschaeftskunden, oder Beides.",
        "typischerKunde": "Beschreibe den typischen Kunden. 1-2 Saetze.",
        "haeufigeAnfrage": "Was ist die haeufigste Kundenanfrage? 1 Satz.",
        "usp": "Finde Alleinstellungsmerkmale (USP). Max 3 Saetze.",
        "mitbewerber": "Werden Mitbewerber erwaehnt? Falls nein: Keine Angaben gefunden.",
        "vorbilder": "Werden andere Websites erwaehnt? Falls nein: Keine Angaben gefunden.",
        "farben": "Welche Farben verwendet die Website? Antworte NUR mit Farbnamen oder Hex-Codes, z.B. 'Blau (#0056b3), Weiss, Grau'. Max 80 Zeichen, keine Analyse.",
        "stil": "Welchen Stil hat die Website? Waehle: Modern, Klassisch, Freundlich, Handwerklich, oder Premium. NUR ein Wort.",
        "wunschseiten": "Welche Seiten hat die aktuelle Website? Liste Hauptseiten auf, eine pro Zeile.",
        "sonstige_hinweise": "Besondere Informationen, Zertifikate, Auszeichnungen? Max 3 Saetze.",
    }

    field_prompt = FIELD_PROMPTS.get(field)
    if not field_prompt:
        raise HTTPException(400, f"Kein Vorschlag fuer Feld: {field}")

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    prompt = f"Du analysierst Website-Content und beantwortest eine Frage.\n\nWEBSITE-CONTENT:\n{website_content}\n\nAUFGABE: {field_prompt}\n\nAntworte NUR mit dem Wert, keine Einleitung."

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 400, "messages": [{"role": "user", "content": prompt}]},
            )
        resp.raise_for_status()
        suggestion = resp.json()["content"][0]["text"].strip()
        return {"field": field, "suggestion": suggestion}
    except Exception as e:
        raise HTTPException(500, f"Vorschlag fehlgeschlagen: {str(e)[:150]}")


@router.get("/{lead_id}/assets-status")
def get_assets_status(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Gibt automatisch erkannte Asset-Informationen zurück."""
    lead     = db.query(Lead).filter(Lead.id == lead_id).first()
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    logo_url   = lead.brand_logo_url or ""
    logo_found = bool(logo_url)

    images_found = []
    try:
        rows = db.execute(
            text("SELECT images FROM website_content_cache WHERE customer_id=:id LIMIT 5"),
            {"id": lead_id}
        ).fetchall()
        for row in rows:
            imgs = json.loads(row[0] or "[]")
            for img in (imgs if isinstance(imgs, list) else []):
                src = img.get("src", "") if isinstance(img, dict) else str(img)
                if src and src.startswith("http"):
                    images_found.append(src)
    except Exception:
        pass

    photos_likely    = len(images_found) > 3
    logo_vorhanden   = bool(briefing.logo_vorhanden)  if briefing else logo_found
    fotos_vorhanden  = bool(briefing.fotos_vorhanden) if briefing else photos_likely

    return {
        "logo": {
            "vorhanden":    logo_vorhanden,
            "url":          logo_url,
            "auto_erkannt": logo_found,
            "quelle":       "Brand Scan" if logo_found else None,
        },
        "fotos": {
            "vorhanden":    fotos_vorhanden,
            "anzahl":       len(images_found),
            "vorschau":     images_found[:3],
            "auto_erkannt": True,
            "einschaetzung": "Fotos gefunden" if photos_likely else "Wenig Bilder — Fotograf empfohlen",
        },
        "ci_handbuch": {
            "vorhanden":  False,
            "dateiname":  lead.brand_pdf_filename or None,
        },
    }


@router.post("/{lead_id}/assets-save")
def save_assets(
    lead_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        briefing = Briefing(lead_id=lead_id)
        db.add(briefing)

    briefing.logo_vorhanden  = bool(body.get("logo_vorhanden"))
    briefing.fotos_vorhanden = bool(body.get("fotos_vorhanden"))
    if "sonstige_hinweise" in body:
        briefing.sonstige_hinweise = body["sonstige_hinweise"]

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(422, str(e)[:200])
    return {"saved": True}


@router.get("/{lead_id}/ki-prefill-funktionen")
def prefill_funktionen(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Regex-based pattern detection for booking, shop, multilingual, and tool integrations."""
    import re

    rows = db.execute(
        text("SELECT url, full_text FROM website_content_cache WHERE customer_id = :lid"),
        {"lid": lead_id},
    ).fetchall()

    all_urls  = " ".join(r[0] or "" for r in rows).lower()
    all_text  = " ".join(r[1] or "" for r in rows).lower()
    combined  = all_urls + " " + all_text

    # Terminbuchung
    booking_patterns = [
        r"calendly", r"booksy", r"treatwell", r"timify", r"appointy",
        r"termin\w*buche", r"termin\w*reserv", r"online.?termin",
        r"jetzt\s+termin", r"wunschtermin", r"terminanfrage",
    ]
    booking_found = any(re.search(p, combined) for p in booking_patterns)

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    gewerk = ""
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if briefing:
        gewerk = (briefing.gewerk or "").lower()
    booking_gewerk_hint = any(k in gewerk for k in [
        "friseur", "kosmetik", "massage", "physiotherap", "arzt", "zahnarzt",
        "nagelstudio", "tattoo", "fotograf", "coach", "berater",
    ])

    # Online-Shop
    shop_patterns = [
        r"woocommerce", r"shopify", r"prestashop", r"magento",
        r"/shop/", r"/produkte/", r"/warenkorb", r"in\s+den\s+warenkorb",
        r"kaufen", r"preis\s*:", r"€\s*\d", r"\d\s*€",
        r"auf\s+lager", r"lieferzeit",
    ]
    shop_found = any(re.search(p, combined) for p in shop_patterns)

    # Mehrsprachig
    lang_patterns = [
        r"/en/", r"/fr/", r"/es/", r"/it/", r"/pl/", r"/tr/", r"/ru/",
        r"lang=", r"hreflang", r"wpml", r"polylang", r"gtranslate",
        r"language\s*switcher", r"sprachauswahl",
    ]
    multi_found = any(re.search(p, combined) for p in lang_patterns)

    # External tools
    TOOL_PATTERNS = {
        "Trustpilot":   r"trustpilot",
        "Google Maps":  r"google\.com/maps|maps\.google|goo\.gl/maps",
        "Instagram":    r"instagram\.com",
        "Facebook":     r"facebook\.com",
        "WhatsApp":     r"wa\.me|whatsapp",
        "Calendly":     r"calendly\.com",
        "Tidio":        r"tidio",
        "Intercom":     r"intercom",
        "YouTube":      r"youtube\.com|youtu\.be",
    }
    detected_tools = [name for name, pat in TOOL_PATTERNS.items() if re.search(pat, combined)]

    return {
        "terminbuchung": {
            "vorhanden":    booking_found,
            "auto_erkannt": booking_found,
            "empfohlen":    booking_gewerk_hint and not booking_found,
            "quelle":       "Crawler" if booking_found else ("Gewerk-Heuristik" if booking_gewerk_hint else None),
        },
        "online_shop": {
            "vorhanden":    shop_found,
            "auto_erkannt": shop_found,
            "quelle":       "Crawler" if shop_found else None,
        },
        "mehrsprachig": {
            "vorhanden":    multi_found,
            "auto_erkannt": multi_found,
            "quelle":       "Crawler" if multi_found else None,
        },
        "externe_tools": {
            "liste":        detected_tools,
            "auto_erkannt": True,
            "quelle":       "Crawler" if detected_tools else None,
        },
    }


@router.post("/{lead_id}/ki-prefill-seo")
async def ki_prefill_seo(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generates SEO keywords via Claude, reads Google Business status and social media from crawler."""
    import os, httpx, json as _json, re as _re

    lead     = db.query(Lead).filter(Lead.id == lead_id).first()
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    gewerk     = (briefing.gewerk     if briefing else "") or getattr(lead, "trade", "") or "Handwerk"
    leistungen = (briefing.leistungen if briefing else "") or ""
    city       = getattr(lead, "city", "") or "Deutschland"
    einzug     = (briefing.einzugsgebiet if briefing else "") or city

    ga_status = getattr(lead, "ga_status", None) or "unbekannt"
    ga_type   = getattr(lead, "ga_type",   None) or ""

    # Google Business — detect via crawler
    gb_status = "unbekannt"
    try:
        rows = db.execute(
            text("SELECT full_text FROM website_content_cache WHERE customer_id=:id LIMIT 5"),
            {"id": lead_id},
        ).fetchall()
        full_text = " ".join(r[0] or "" for r in rows).lower()
        if _re.search(r"maps\.google|goo\.gl/maps|google\.com/maps", full_text):
            gb_status = "Vorhanden (Link auf Website gefunden)"
        elif _re.search(r"google business|google my business", full_text):
            gb_status = "Wahrscheinlich vorhanden"
    except Exception:
        pass

    # Social media — detect via crawler URLs + text
    social_found = []
    try:
        rows = db.execute(
            text("SELECT full_text, url FROM website_content_cache WHERE customer_id=:id LIMIT 5"),
            {"id": lead_id},
        ).fetchall()
        all_text = " ".join((r[0] or "") + " " + (r[1] or "") for r in rows).lower()
        SOCIAL_PATTERNS = {
            "Facebook":      r"facebook\.com/",
            "Instagram":     r"instagram\.com/",
            "LinkedIn":      r"linkedin\.com/",
            "YouTube":       r"youtube\.com/",
            "TikTok":        r"tiktok\.com/",
            "Pinterest":     r"pinterest\.",
            "X/Twitter":     r"twitter\.com/|x\.com/",
            "Xing":          r"xing\.com/",
        }
        for name, pat in SOCIAL_PATTERNS.items():
            if _re.search(pat, all_text):
                social_found.append(name)
    except Exception:
        pass

    # Keywords via Claude
    api_key  = os.getenv("ANTHROPIC_API_KEY", "")
    keywords = []
    if api_key:
        prompt = (
            f"Generiere die Top 5 Google-Suchbegriffe für diesen Handwerksbetrieb.\n"
            f"Gewerk: {gewerk} | Stadt: {city} | Einzugsgebiet: {einzug}\n"
            f"Leistungen: {leistungen}\n\n"
            f"Regel: Immer nach Muster \"{{Leistung}} {{Stadt}}\" und \"{{Leistung}} {{Region}}\".\n"
            f"Füge 1-2 Notfall/Spezial-Keywords hinzu wenn relevant.\n\n"
            f"Antworte NUR als JSON-Array: [\"keyword1\", \"keyword2\", \"keyword3\", \"keyword4\", \"keyword5\"]"
        )
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                             "content-type": "application/json"},
                    json={"model": "claude-sonnet-4-20250514", "max_tokens": 200,
                          "messages": [{"role": "user", "content": prompt}]},
                )
            resp.raise_for_status()
            raw = resp.json()["content"][0]["text"].strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            keywords = _json.loads(raw)
        except Exception:
            pass

    if not keywords:
        keywords = [f"{gewerk} {city}", f"{gewerk} {einzug}", f"{gewerk} {city} günstig"]

    return {
        "keywords":        keywords,
        "keywords_quelle": "Claude + Gewerk/Stadt",
        "google_business": {
            "status": gb_status,
            "quelle": "Crawler-Analyse",
        },
        "social_media": {
            "gefunden": social_found,
            "quelle":   f"{len(social_found)} Kanäle auf Website erkannt",
            "auto":     True,
        },
        "ga_analytics": {
            "status": ga_status,
            "type":   ga_type,
        },
    }


@router.post("/{lead_id}/ki-prefill-ziele")
async def ki_prefill_ziele(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Reads existing data and lets Claude derive goals and target audience."""
    import os, httpx, json as _json

    lead     = db.query(Lead).filter(Lead.id == lead_id).first()
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    gewerk     = (briefing.gewerk     if briefing else "") or getattr(lead, "trade", "") or "Handwerk"
    leistungen = (briefing.leistungen if briefing else "") or ""
    usp        = (briefing.usp        if briefing else "") or ""
    region     = (briefing.einzugsgebiet if briefing else "") or getattr(lead, "city", "") or ""
    company    = getattr(lead, "company_name", "") or ""

    crawler_pages = []
    try:
        cached = db.execute(
            text("SELECT title, text_preview, full_text FROM website_content_cache "
                 "WHERE customer_id=:id ORDER BY id LIMIT 3"),
            {"id": lead_id},
        ).fetchall()
        for p in cached:
            crawler_pages.append(f"{p[0] or ''}: {(p[2] or p[1] or '')[:300]}")
    except Exception:
        pass

    crawler_text = "\n".join(crawler_pages) or "kein Crawler-Inhalt verfügbar"

    prompt = (
        f"Du analysierst Daten eines Handwerksbetriebs und leitest Ziele + Zielgruppe ab.\n\n"
        f"BETRIEB: {company}\n"
        f"Gewerk: {gewerk} | Region: {region}\n"
        f"Leistungen: {leistungen}\n"
        f"USP: {usp}\n\n"
        f"WEBSITE-INHALTE (automatisch gescrapt):\n{crawler_text}\n\n"
        f"Leite folgende Felder aus den Daten ab. Sei konkret und praxisnah.\n\n"
        f"Antworte NUR als JSON:\n"
        f'{{\n'
        f'  "hauptziel": "<Was ist das primäre Ziel der Website? 1 klarer Satz.>",\n'
        f'  "hauptziel_konfidenz": <0.0–1.0>,\n'
        f'  "cta_aktion": "<Anrufen|Kontaktformular|WhatsApp|Termin buchen|Angebot anfragen>",\n'
        f'  "cta_aktion_konfidenz": <0.0–1.0>,\n'
        f'  "zielgruppe_typ": "<B2C|B2B|Beides>",\n'
        f'  "zielgruppe_typ_konfidenz": <0.0–1.0>,\n'
        f'  "typischer_kunde": "<Persona in 1-2 Sätzen>",\n'
        f'  "typischer_kunde_konfidenz": <0.0–1.0>,\n'
        f'  "haeufigste_anfrage": "<Top 2-3 Anfrage-Typen>",\n'
        f'  "haeufigste_anfrage_konfidenz": <0.0–1.0>,\n'
        f'  "ki_begruendung": "<1 Satz warum diese Ableitungen gemacht wurden>"\n'
        f'}}'
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 800,
                      "messages": [{"role": "user", "content": prompt}]},
            )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = _json.loads(raw)
        result["source"] = "claude"
        return result
    except Exception as e:
        raise HTTPException(500, f"KI-Vorausfüllung fehlgeschlagen: {str(e)[:200]}")
