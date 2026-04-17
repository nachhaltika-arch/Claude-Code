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
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db, Briefing, Lead, Project, SessionLocal
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
        # KI-Auto-Fill Metadaten (fuer Banner + Badges im Frontend)
        "ki_prefilled_at":   (
            b.ki_prefilled_at.isoformat()
            if getattr(b, "ki_prefilled_at", None) else None
        ),
        "ki_confidence":     getattr(b, "ki_confidence", "") or "",
        "ki_hinweise":       getattr(b, "ki_hinweise", "") or "",
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

    # DB-Connection vor dem externen Claude-Call freigeben — auf Render Basic
    # mit kleinem Pool wuerden 5 parallele Requests sonst den Pool verhungern
    # lassen, waehrend jeder Call bis zu 30s blockt.
    db.close()

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


# ── KI-Briefing-Auto-Fill ──────────────────────────────────────────────────────
#
# Endpoint: POST /api/briefings/{lead_id}/ki-prefill
# Kernlogik: ki_prefill_briefing(lead_id, db) — wird auch direkt vom
# Stripe-Webhook-Background-Thread aufgerufen (kein HTTP-Roundtrip).
#
# Pipeline:
#   1. Lead + website_content_cache + brand_* + audit_top_issues laden
#   2. Heuristic-Fallback-Dict aus den Rohdaten bauen (trade, page-names aus URLs)
#   3. Wenn ANTHROPIC_API_KEY + Rohdaten vorhanden: Claude-Call fuer bessere Werte
#   4. Merge: Claude-Werte ueberschreiben Heuristik
#   5. Ins Briefing schreiben — aber NUR Felder, die noch leer sind
#   6. usp / vorbilder / sonstige_hinweise werden NIE auto-befuellt
#   7. ki_prefilled_at / ki_confidence / ki_hinweise immer setzen

_KI_PREFILL_FILLABLE = [
    "gewerk", "leistungen", "einzugsgebiet", "farben", "stil",
    "wunschseiten", "logo_vorhanden", "fotos_vorhanden",
]
_KI_PREFILL_NEVER_FILL = ["usp", "vorbilder", "sonstige_hinweise"]


def _ki_prefill_gather_context(lead: Lead, db: Session) -> dict:
    """Sammelt alle verfuegbaren Rohdaten fuer einen Lead in ein Context-Dict."""
    from sqlalchemy import text as sa_text
    from urllib.parse import urlparse

    lead_id = lead.id

    # 1. Website-Content-Cache (nach Wordcount, damit wir die textreichsten
    #    Seiten zuerst bekommen — die tragen die meiste Signal-Information)
    rows = db.execute(
        sa_text("""
            SELECT url, title, meta_description, h1, h2s, text_preview,
                   COALESCE(word_count, 0) AS wc, COALESCE(images, '[]') AS imgs
            FROM website_content_cache
            WHERE customer_id = :lid
            ORDER BY word_count DESC NULLS LAST, scraped_at DESC
            LIMIT 15
        """),
        {"lid": lead_id},
    ).fetchall()

    all_h2s: list = []
    all_titles: list = []
    page_names: list = []
    text_previews: list = []
    image_count = 0

    for row in rows:
        url, title, _meta, h1, h2s_json, preview, _wc, imgs_json = row
        if title:
            all_titles.append(title.strip())
        if h1:
            all_h2s.append(h1.strip())
        try:
            parsed_h2 = json.loads(h2s_json or '[]')
            if isinstance(parsed_h2, list):
                all_h2s.extend([str(s).strip() for s in parsed_h2 if s])
        except Exception:
            pass
        if url:
            try:
                path = urlparse(url).path.strip('/').split('/')[-1]
                if path and len(path) > 1:
                    name = path.replace('-', ' ').replace('_', ' ').title()
                    if name not in page_names:
                        page_names.append(name)
            except Exception:
                pass
        if preview:
            text_previews.append(f"{url or '?'}: {preview[:220]}")
        try:
            parsed_imgs = json.loads(imgs_json or '[]')
            if isinstance(parsed_imgs, list):
                image_count += len(parsed_imgs)
        except Exception:
            pass

    # 2. Audit-Top-Issues (letzter abgeschlossener Audit)
    audit_top_issues: list = []
    try:
        raw = db.execute(
            sa_text("""
                SELECT top_issues
                FROM audit_results
                WHERE lead_id = :lid
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"lid": lead_id},
        ).scalar()
        if raw:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(parsed, list):
                audit_top_issues = [str(i) for i in parsed[:3]]
    except Exception:
        audit_top_issues = []

    return {
        "company_name": lead.company_name or "",
        "city": lead.city or "",
        "trade": lead.trade or "",
        "website_url": lead.website_url or "",
        "pages_found": page_names[:10],
        "page_titles": list(dict.fromkeys(all_titles))[:10],
        "h2s_sample": list(dict.fromkeys(all_h2s))[:20],
        "text_previews": text_previews[:5],
        "brand_primary": getattr(lead, "brand_primary_color", "") or "",
        "brand_secondary": getattr(lead, "brand_secondary_color", "") or "",
        "brand_font": getattr(lead, "brand_font_primary", "") or "",
        "brand_style": getattr(lead, "brand_design_style", "") or "",
        "logo_found": bool(getattr(lead, "brand_logo_url", "")),
        "image_count": image_count,
        "audit_top_issues": audit_top_issues,
        "_row_count": len(rows),
    }


def _ki_prefill_heuristic(ctx: dict) -> dict:
    """Baue das Fallback-Dict rein aus den Rohdaten — ohne Claude."""
    brand_primary = ctx.get("brand_primary", "")
    brand_secondary = ctx.get("brand_secondary", "")
    if brand_primary:
        farben = f"Primärfarbe: {brand_primary}"
        if brand_secondary:
            farben += f", Sekundärfarbe: {brand_secondary}"
    else:
        farben = ""

    h2s = ctx.get("h2s_sample", [])
    leistungen_list = list(dict.fromkeys([h for h in h2s if h]))[:8]

    return {
        "gewerk": (ctx.get("trade") or (h2s[0] if h2s else ""))[:80],
        "leistungen": ", ".join(leistungen_list),
        "einzugsgebiet": ctx.get("city", ""),
        "farben": farben,
        "stil": ctx.get("brand_style", "") or "",
        "wunschseiten": ", ".join(ctx.get("pages_found", [])[:8]),
        "logo_vorhanden": bool(ctx.get("logo_found")),
        "fotos_vorhanden": (ctx.get("image_count") or 0) > 3,
        "ki_confidence": "low",
        "ki_hinweise": "Heuristik ohne KI-Call — bitte alle Angaben prüfen.",
    }


def _ki_prefill_build_prompt(ctx: dict) -> str:
    pages_list = ", ".join(ctx.get("pages_found", [])) or "(keine)"
    h2_list = ", ".join(ctx.get("h2s_sample", [])) or "(keine)"
    previews = "\n".join(f"  - {p}" for p in ctx.get("text_previews", [])) or "  (keine)"
    issues = "\n".join(f"  - {i}" for i in ctx.get("audit_top_issues", [])) or "  (keine)"
    return f"""Du bist ein Website-Analyst für KOMPAGNON. Analysiere diese Daten einer Handwerker-Website und fülle die Briefing-Felder aus.

KONTEXT:
  Unternehmen:    {ctx.get('company_name', '')}
  Branche/Trade:  {ctx.get('trade', '')}
  Stadt:          {ctx.get('city', '')}
  URL:            {ctx.get('website_url', '')}
  Gefundene Seiten:           {pages_list}
  Überschriften (H1/H2-Mix):  {h2_list}
  Bild-Anzahl:                {ctx.get('image_count', 0)}
  Logo erkannt:               {'ja' if ctx.get('logo_found') else 'nein'}
  Primärfarbe (Brand-Scan):   {ctx.get('brand_primary', '') or '(nicht erkannt)'}
  Sekundärfarbe (Brand-Scan): {ctx.get('brand_secondary', '') or '(nicht erkannt)'}
  Schriftart (Brand-Scan):    {ctx.get('brand_font', '') or '(nicht erkannt)'}
  Design-Stil (Brand-Scan):   {ctx.get('brand_style', '') or '(nicht erkannt)'}

Text-Vorschauen der wichtigsten Seiten:
{previews}

Audit-Top-Probleme (falls vorhanden):
{issues}

AUFGABE: Antworte AUSSCHLIESSLICH als valides JSON ohne Markdown-Wrapper.
Kein Text davor oder danach. Format:
{{
  "gewerk": "<kurzer Branchen-Begriff, max 40 Zeichen>",
  "leistungen": "<kommagetrennte Leistungen aus den Seiteninhalten, max 8>",
  "einzugsgebiet": "<Stadt + Region aus Texten, max 80 Zeichen>",
  "farben": "<Primärfarbe: #xxx, Sekundärfarbe: #yyy — nur wenn erkannt>",
  "stil": "<Modern|Klassisch|Handwerklich|Minimalistisch|Premium>",
  "wunschseiten": "<kommagetrennte Seitennamen, max 8>",
  "logo_vorhanden": <true|false>,
  "fotos_vorhanden": <true|false>,
  "ki_confidence": "<high|medium|low>",
  "ki_hinweise": "<max 1 Satz: was sollte der Kunde prüfen?>"
}}

Regeln:
- Sei konkret. Keine Allgemeinplätze.
- Wenn ein Feld unklar ist: setze es auf "" (empty string).
- ki_confidence: high wenn >=10 H2s UND >=5 Seiten. Sonst medium/low.
- fotos_vorhanden: true wenn image_count > 3.
- stil: exakt einer der 5 Begriffe, nichts anderes.
"""


def _ki_prefill_call_claude(ctx: dict) -> Optional[dict]:
    """Synchroner Claude-Call. Gibt dict zurueck oder None bei Fehler."""
    import os
    import httpx
    import re as _re

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 800,
                    "messages": [
                        {"role": "user", "content": _ki_prefill_build_prompt(ctx)}
                    ],
                },
            )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        # Strip potential markdown fences defensively
        raw = _re.sub(r'^```(?:json)?\s*', '', raw)
        raw = _re.sub(r'\s*```$', '', raw)
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return None
        return parsed
    except Exception as e:
        logger.warning(f"KI-Prefill Claude-Call fehlgeschlagen: {e}")
        return None


def _ki_prefill_is_empty(briefing: Briefing, field: str) -> bool:
    """Pruefe ob ein Briefing-Feld als 'leer / noch nicht vom Nutzer gesetzt' gilt.

    String-Felder: None oder leerer/whitespace-String.
    Bool-Felder: False wird als 'nicht gesetzt' interpretiert, weil der
    DB-Default False ist und der Nutzer haette aktiv auf True setzen muessen.
    """
    current = getattr(briefing, field, None)
    if current is None:
        return True
    if isinstance(current, bool):
        return current is False
    if isinstance(current, str):
        return current.strip() == ""
    return False


def ki_prefill_briefing(lead_id: int, db: Session) -> dict:
    """KI-basiertes Auto-Fill fuer ein Lead-Briefing.

    Wird von zwei Stellen aufgerufen:
      1. HTTP-Endpoint POST /api/briefings/{lead_id}/ki-prefill
      2. Stripe-Webhook Background-Thread (_handle_successful_payment)

    Pool-Safety: Der uebergebene `db` wird NACH dem Context-Sammeln und
    VOR dem blockierenden Claude-Call geschlossen. Der Persist laeuft
    danach in einer frischen SessionLocal. Auf Render Basic mit kleinem
    Pool verhindert das Pool-Exhaustion wenn mehrere KI-Prefills parallel
    laufen.

    Fehlertolerant: Wenn website_content_cache leer oder Claude nicht
    verfuegbar ist, greift die Heuristik. Wirft HTTPException nur bei
    echten DB-Fehlern oder fehlendem Lead.
    """
    # ── Phase 1: Read mit der aussen uebergebenen Session ────────────
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    ctx = _ki_prefill_gather_context(lead, db)

    # DB-Connection freigeben BEVOR der blockierende Claude-Call startet.
    # Der Aufrufer (sowohl FastAPI-Dependency als auch Stripe-Webhook) ist
    # fuer das endgueltige Teardown verantwortlich — unser close() hier
    # ist idempotent und gibt den Pool sofort zurueck.
    db.close()

    heuristic = _ki_prefill_heuristic(ctx)

    # ── Phase 2: Claude-Call OHNE DB-Connection ──────────────────────
    merged = dict(heuristic)
    if ctx.get("_row_count", 0) > 0:
        kresult = _ki_prefill_call_claude(ctx)
        if kresult:
            for key in heuristic.keys():
                val = kresult.get(key)
                if val is not None and val != "":
                    merged[key] = val

    # Bool-Felder defensiv normalisieren (Claude koennte Strings liefern)
    merged["logo_vorhanden"] = bool(merged.get("logo_vorhanden"))
    merged["fotos_vorhanden"] = bool(merged.get("fotos_vorhanden"))
    merged["ki_confidence"] = str(merged.get("ki_confidence") or "low")[:10]
    merged["ki_hinweise"] = str(merged.get("ki_hinweise") or "")[:500]

    # ── Phase 3: Persist in frischer Session ─────────────────────────
    db2 = SessionLocal()
    try:
        briefing = db2.query(Briefing).filter(Briefing.lead_id == lead_id).first()
        if not briefing:
            briefing = Briefing(lead_id=lead_id, status="entwurf")
            db2.add(briefing)
            db2.flush()

        filled: list = []
        skipped: list = []
        for field in _KI_PREFILL_FILLABLE:
            if _ki_prefill_is_empty(briefing, field):
                new_val = merged.get(field)
                if new_val not in (None, "", []):
                    setattr(briefing, field, new_val)
                    filled.append(field)
                else:
                    skipped.append(field)
            else:
                skipped.append(field)

        # KI-Metadaten immer setzen (auch wenn filled leer ist — Nutzer hatte
        # schon alles ausgefuellt, wir haben trotzdem etwas analysiert)
        briefing.ki_prefilled_at = datetime.utcnow()
        briefing.ki_confidence = merged["ki_confidence"]
        briefing.ki_hinweise = merged["ki_hinweise"]
        briefing.updated_at = datetime.utcnow()

        try:
            db2.commit()
            db2.refresh(briefing)
        except Exception as e:
            db2.rollback()
            logger.error(f"KI-Prefill Commit fehlgeschlagen fuer Lead {lead_id}: {e}")
            raise HTTPException(500, f"KI-Prefill fehlgeschlagen: {str(e)[:200]}")

        return {
            "filled_fields": filled,
            "skipped_fields": sorted(set(skipped + _KI_PREFILL_NEVER_FILL)),
            "ki_confidence": merged["ki_confidence"],
            "ki_hinweise": merged["ki_hinweise"],
            "briefing": _serialize(briefing),
        }
    finally:
        db2.close()


@router.post("/{lead_id}/ki-prefill-ziele")
async def ki_prefill_ziele(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Liest vorhandene Daten und laesst Claude Ziele + Zielgruppe ableiten."""
    import os, httpx, json as _json
    from sqlalchemy import text as sa_text

    lead     = db.query(Lead).filter(Lead.id == lead_id).first()
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    crawler_pages = []
    try:
        cached = db.execute(
            sa_text("SELECT title, text_preview, full_text FROM website_content_cache "
                    "WHERE customer_id=:id ORDER BY id LIMIT 3"),
            {"id": lead_id}
        ).fetchall()
        for p in cached:
            crawler_pages.append(f"{p[0] or ''}: {(p[2] or p[1] or '')[:300]}")
    except Exception:
        pass

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    gewerk     = (briefing.gewerk     if briefing else "") or (lead.trade or "Handwerk")
    leistungen = (briefing.leistungen if briefing else "") or ""
    usp        = (briefing.usp        if briefing else "") or ""
    region     = (briefing.einzugsgebiet if briefing else "") or (lead.city or "")
    company    = lead.company_name or ""
    crawler_text = "\n".join(crawler_pages) or "kein Crawler-Inhalt verfuegbar"

    prompt = f"""Du analysierst Daten eines Handwerksbetriebs und leitest Ziele + Zielgruppe ab.

BETRIEB: {company}
Gewerk: {gewerk} | Region: {region}
Leistungen: {leistungen}
USP: {usp}

WEBSITE-INHALTE (automatisch gescrapt):
{crawler_text}

Leite folgende Felder aus den Daten ab. Sei konkret und praxisnah.

Antworte NUR als JSON:
{{
  "hauptziel": "<Was ist das primaere Ziel der Website? 1 klarer Satz.>",
  "hauptziel_konfidenz": <0.0-1.0>,
  "cta_aktion": "<Anrufen|Kontaktformular|WhatsApp|Termin buchen|Angebot anfragen>",
  "cta_aktion_konfidenz": <0.0-1.0>,
  "zielgruppe_typ": "<B2C|B2B|Beides>",
  "zielgruppe_typ_konfidenz": <0.0-1.0>,
  "typischer_kunde": "<Persona in 1-2 Saetzen.>",
  "typischer_kunde_konfidenz": <0.0-1.0>,
  "haeufigste_anfrage": "<Top 2-3 Anfrage-Typen aus Leistungen.>",
  "haeufigste_anfrage_konfidenz": <0.0-1.0>,
  "ki_begruendung": "<1 Satz warum diese Ableitungen gemacht wurden>"
}}"""

    db.close()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
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
        raise HTTPException(500, f"KI-Vorausfuellung fehlgeschlagen: {str(e)[:200]}")


@router.post("/{lead_id}/ki-prefill")
def ki_prefill_endpoint(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """KI-basiertes Auto-Fill des Briefings fuer einen Lead.

    Liest Crawler-Content, Brand-Design und den letzten Audit, baut daraus
    einen Kontext fuer Claude und schreibt die Ergebnisse in nur jene
    Briefing-Felder, die noch leer sind. usp / vorbilder / sonstige_hinweise
    werden niemals automatisch befuellt.
    """
    return ki_prefill_briefing(lead_id, db)


# ── Tor 1: Briefing-Submit ────────────────────────────────────────────────────
#
# Der Kunde klickt "Briefing abschicken" im BriefingWizard. Das setzt
# briefing.status='submitted', projects.briefing_submitted_at=now() und
# benachrichtigt den Admin. Phase 2 (Sitemap-KI, Content-Agent, Design)
# ist dann gesperrt bis ein Admin explizit via POST /api/projects/{id}/
# approve-briefing freigibt.


def _get_admin_notification_email(db: Session) -> Optional[str]:
    """Admin-Mail aus SystemSettings holen, sonst env, sonst erster superadmin."""
    import os
    from database import SystemSettings, User
    # 1. SystemSettings-Key 'admin_notification_email'
    try:
        row = db.query(SystemSettings).filter(
            SystemSettings.key == "admin_notification_email"
        ).first()
        if row and row.value:
            return row.value.strip()
    except Exception:
        pass
    # 2. Env-Fallback
    env_val = os.getenv("ADMIN_NOTIFICATION_EMAIL", "").strip()
    if env_val:
        return env_val
    # 3. Erster aktiver superadmin als letzter Fallback
    try:
        row = db.query(User).filter(User.role == "superadmin").first()
        if row and row.email:
            return row.email
    except Exception:
        pass
    return None


def _notify_admin_briefing_submitted(lead: Lead, project: Optional[Project], db: Session) -> None:
    """Sende eine Admin-Benachrichtigung per E-Mail, dass ein Briefing
    zur Freigabe wartet. Schluckt alle Fehler — Mail-Probleme duerfen
    den Submit-Endpoint NICHT zum 500 zwingen."""
    try:
        to = _get_admin_notification_email(db)
        if not to:
            logger.warning(
                "Briefing-Submit: Keine Admin-E-Mail konfiguriert — "
                "Benachrichtigung uebersprungen."
            )
            return

        company = (lead.display_name or lead.company_name or f"Lead #{lead.id}") if lead else "Unbekannt"
        project_id = project.id if project else "—"
        subject = f"[KOMPAGNON] Briefing wartet auf Freigabe — {company}"
        # Plain-Text Body in minimales HTML wrappen, damit Zeilenumbrueche
        # im Mail-Client erhalten bleiben — die kanonische send_email
        # erwartet html_body als Pflichtparameter.
        body_text = (
            f"Ein Kunde hat sein Briefing eingereicht und wartet auf deine Freigabe.\n\n"
            f"Unternehmen: {company}\n"
            f"Lead-ID:     {lead.id if lead else '—'}\n"
            f"Projekt-ID:  {project_id}\n"
            f"Eingereicht: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"Oeffne das Projekt in KOMPAGNON und klicke 'Briefing freigeben', "
            f"um Phase 2 (Sitemap, Content, Design) zu starten.\n\n"
            f"Nach 24h ohne Freigabe erhaeltst du eine Erinnerung, "
            f"nach 48h geht eine Eskalation raus.\n"
        )
        html_body = (
            "<pre style=\"font-family:-apple-system,sans-serif;font-size:14px;"
            "white-space:pre-wrap\">" + body_text + "</pre>"
        )

        from services.email import send_email
        ok = send_email(
            to_email=to,
            subject=subject,
            html_body=html_body,
            text_body=body_text,
        )
        if ok:
            logger.info(f"Briefing-Submit: Admin-Benachrichtigung an {to} fuer Lead {lead.id if lead else '?'}")
        else:
            logger.warning(
                f"Briefing-Submit: Admin-Mail an {to} fehlgeschlagen — "
                "SMTP-Konfiguration pruefen."
            )
    except Exception as e:
        logger.error(f"Briefing-Submit: Admin-E-Mail fehlgeschlagen: {e}")


@router.post("/{lead_id}/submit")
def submit_briefing(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Kunde reicht das Briefing zur Admin-Freigabe ein (Tor 1).

    Pflichtfelder: gewerk + leistungen muessen gesetzt sein.
    Effekte:
      1. briefing.status = 'submitted'
      2. projects.briefing_submitted_at = now() (falls Projekt existiert)
      3. Admin-E-Mail-Benachrichtigung (best-effort, wirft nicht)

    Idempotent: Wenn das Briefing bereits submitted ist, wird der
    Timestamp auf dem Projekt NICHT ueberschrieben — der Endpoint gibt
    einfach den aktuellen Stand zurueck.
    """
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        raise HTTPException(404, "Briefing nicht gefunden — zuerst speichern.")

    # Pflichtfelder pruefen
    missing = []
    if not (briefing.gewerk and briefing.gewerk.strip()):
        missing.append("gewerk")
    if not (briefing.leistungen and briefing.leistungen.strip()):
        missing.append("leistungen")
    if missing:
        raise HTTPException(
            400,
            f"Pflichtfelder fehlen: {', '.join(missing)}. "
            f"Bitte vor dem Abschicken ausfuellen.",
        )

    briefing.status = "submitted"
    briefing.updated_at = datetime.utcnow()

    # Projekt-Timestamp setzen (nur beim ersten Submit, nicht bei Retry)
    project = db.query(Project).filter(Project.lead_id == lead_id).order_by(
        Project.id.desc()
    ).first()
    first_submit = False
    if project and not project.briefing_submitted_at:
        project.briefing_submitted_at = datetime.utcnow()
        first_submit = True

    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    try:
        db.commit()
        db.refresh(briefing)
    except Exception as e:
        db.rollback()
        logger.error(f"Briefing-Submit Commit fehlgeschlagen: {e}")
        raise HTTPException(500, f"Submit fehlgeschlagen: {str(e)[:200]}")

    # Admin-Benachrichtigung nur beim ersten Submit
    if first_submit:
        _notify_admin_briefing_submitted(lead, project, db)

    return {
        "status": "submitted",
        "first_submit": first_submit,
        "briefing_submitted_at": (
            project.briefing_submitted_at.isoformat()
            if project and project.briefing_submitted_at else None
        ),
        "project_id": project.id if project else None,
        "briefing": _serialize(briefing),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Legacy-Sektionen + KI-Analysen
# ═══════════════════════════════════════════════════════════════════════════
# Diese Endpunkte stammen aus dem frueheren `routers/briefing.py` (Singular),
# das parallel unter demselben Prefix `/api/briefings` registriert war. Das
# war eine stille Kollisions-Falle: wer in einer der beiden Dateien einen
# Endpunkt anlegt, der in der anderen schon existiert, bekommt ohne Warnung
# das "zuletzt registrierte" Verhalten. Durch den Merge in diese Datei ist
# die Endpunkt-Registrierung jetzt eindeutig.
# ═══════════════════════════════════════════════════════════════════════════

@router.patch("/{lead_id}")
def update_briefing_sections(
    lead_id: int,
    data: dict,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Aktualisiert Legacy-JSON-Sections eines Briefings (projektrahmen,
    positionierung, zielgruppe, wettbewerb, inhalte, funktionen, branding,
    struktur, hosting, seo, projektplan, freigaben, status).

    Unterscheidet sich bewusst vom PUT-Endpunkt oben, der die flachen Felder
    (gewerk, leistungen, einzugsgebiet, usp etc.) aktualisiert.
    """
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        briefing = Briefing(lead_id=lead_id)
        db.add(briefing)

    allowed = [
        "projektrahmen", "positionierung", "zielgruppe", "wettbewerb", "inhalte",
        "funktionen", "branding", "struktur", "hosting", "seo", "projektplan",
        "freigaben", "status",
    ]
    for key in allowed:
        if key in data:
            if isinstance(data[key], dict):
                setattr(briefing, key, json.dumps(data[key], ensure_ascii=False))
            else:
                setattr(briefing, key, data[key])

    briefing.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(briefing)
    except Exception as e:
        db.rollback()
        raise HTTPException(422, f"Speichern fehlgeschlagen: {str(e)[:200]}")
    return _serialize(briefing)


@router.patch("/{lead_id}/freigabe")
def set_freigabe(lead_id: int, data: dict, db: Session = Depends(get_db)):
    """Nur Kunden (role=kunde) koennen Freigaben erteilen — kann nicht widerrufen
    werden. Die Authentifizierung laeuft manuell ueber ein Token im Body, weil
    der Endpunkt aus dem Kundenportal per Magic-Link aufgerufen wird und der
    httpOnly-Cookie dort nicht verfuegbar ist.
    """
    from routers.auth_router import decode_token
    from database import User

    token = data.get("_token", "")
    if not token:
        raise HTTPException(403, "Nicht authentifiziert")
    try:
        payload = decode_token(token)
        current_user = db.query(User).filter(User.id == payload.get("user_id")).first()
        if not current_user or current_user.role != "kunde":
            raise HTTPException(403, "Nur Kunden koennen Freigaben erteilen")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(403, "Authentifizierung fehlgeschlagen")

    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    if not briefing:
        raise HTTPException(404, "Briefing nicht gefunden")

    key = data.get("key")
    if not key:
        raise HTTPException(400, "Freigabe-Key fehlt")

    current = (
        json.loads(briefing.freigaben)
        if briefing.freigaben and briefing.freigaben != "{}"
        else {}
    )
    existing = current.get(key, {})

    if existing.get("datum"):
        raise HTTPException(400, "Freigabe bereits erteilt und kann nicht widerrufen werden")

    updated = {
        **current,
        key: {
            "datum":   datetime.utcnow().strftime("%d.%m.%Y"),
            "uhrzeit": datetime.utcnow().strftime("%H:%M"),
            "durch":   current_user.email or f"{current_user.first_name} {current_user.last_name}",
            "user_id": current_user.id,
        },
    }

    briefing.freigaben = json.dumps(updated, ensure_ascii=False)
    briefing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(briefing)
    return _serialize(briefing)


@router.post("/{lead_id}/zielgruppenanalyse")
async def zielgruppenanalyse(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """AI-gestuetzte Zielgruppenanalyse auf Basis von Gewerk + Stadt des Leads.
    Ergebnis wird im Feld `briefing.zielgruppe.analyse` gespeichert.

    Pool-Safety: Lead-Daten werden in lokale Variablen gezogen, dann wird
    der uebergebene db GESCHLOSSEN, und der blockierende Claude-Call laeuft
    ohne DB-Connection. Persist danach in einer frischen SessionLocal.
    """
    import os
    from anthropic import Anthropic

    # ── Phase 1: Read ────────────────────────────────────────────────
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    trade   = lead.trade or "Handwerk"
    city    = lead.city or "Deutschland"
    company = lead.display_name or lead.company_name or ""

    # DB-Connection freigeben BEVOR der blockierende Claude-Call startet.
    db.close()

    prompt = f"""Du bist ein erfahrener Marketing-Stratege fuer Handwerksbetriebe in Deutschland.

Analysiere die Zielgruppe fuer diesen Betrieb:
- Unternehmen: {company}
- Branche/Gewerk: {trade}
- Standort: {city}

Erstelle eine strukturierte Zielgruppenanalyse mit:
1. Primaere Zielgruppe (wer kauft hauptsaechlich)
2. Sekundaere Zielgruppe
3. Demografische Merkmale (Alter, Geschlecht, Einkommen)
4. Psychografische Merkmale (Werte, Beduerfnisse, Schmerzpunkte)
5. Kaufmotivation (Warum beauftragen sie einen {trade}?)
6. Entscheidungskriterien (Was ist bei der Auswahl wichtig?)
7. Bevorzugte Kommunikationskanaele
8. Empfehlung fuer die Website-Ansprache

Schreibe kompakt und praxisnah. Maximal 400 Woerter. Auf Deutsch."""

    # ── Phase 2: Claude-Call OHNE DB-Connection ──────────────────────
    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), max_retries=0, timeout=60.0)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        analyse = response.content[0].text
    except Exception as e:
        logger.error(f"Zielgruppenanalyse Claude-Fehler: {e}")
        raise HTTPException(500, f"Analyse fehlgeschlagen: {str(e)}")

    # ── Phase 3: Persist in frischer Session ─────────────────────────
    analyse_datum = datetime.utcnow().strftime("%d.%m.%Y %H:%M")
    db2 = SessionLocal()
    try:
        briefing = db2.query(Briefing).filter(Briefing.lead_id == lead_id).first()
        if not briefing:
            briefing = Briefing(lead_id=lead_id)
            db2.add(briefing)

        current = (
            json.loads(briefing.zielgruppe)
            if briefing.zielgruppe and briefing.zielgruppe != "{}"
            else {}
        )
        updated = {
            **current,
            "analyse": analyse,
            "analyse_datum": analyse_datum,
        }
        briefing.zielgruppe = json.dumps(updated, ensure_ascii=False)
        briefing.updated_at = datetime.utcnow()
        db2.commit()
    except Exception as e:
        db2.rollback()
        logger.error(f"Zielgruppenanalyse Persist-Fehler: {e}")
        raise HTTPException(500, f"Analyse konnte nicht gespeichert werden: {str(e)[:200]}")
    finally:
        db2.close()

    return {"analyse": analyse, "datum": analyse_datum}


@router.post("/{lead_id}/wettbewerbsanalyse")
async def wettbewerbsanalyse(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """AI-gestuetzte Wettbewerbsanalyse auf Basis von Gewerk + Stadt + PLZ des Leads.
    Ergebnis wird im Feld `briefing.wettbewerb.analyse` gespeichert.

    Pool-Safety: Lead-Daten werden in lokale Variablen gezogen, dann wird
    der uebergebene db GESCHLOSSEN, und der blockierende Claude-Call laeuft
    ohne DB-Connection. Persist danach in einer frischen SessionLocal.
    """
    import os
    from anthropic import Anthropic

    # ── Phase 1: Read ────────────────────────────────────────────────
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    trade       = lead.trade or "Handwerk"
    city        = lead.city or "Deutschland"
    postal_code = lead.postal_code or ""
    company     = lead.display_name or lead.company_name or ""
    region      = f"{city} ({postal_code})" if postal_code else city

    # DB-Connection freigeben BEVOR der blockierende Claude-Call startet.
    db.close()

    prompt = f"""Du bist ein erfahrener Markt- und Wettbewerbsanalyst fuer Handwerksbetriebe in Deutschland.

Erstelle eine Wettbewerbsanalyse fuer:
- Unternehmen: {company}
- Branche/Gewerk: {trade}
- Region: {region} und 50 km Umkreis

Analysiere:
1. Marktuebersicht — Typische Anzahl Wettbewerber, Marktstruktur
2. Typische Wettbewerber-Profile — Wie praesentieren sie sich online?
3. Online-Praesenz der Wettbewerber — Typischer Stand der Websites, Staerken, Schwaechen
4. Differenzierungspotenzial — Wo kann sich {company} abheben? Welche Luecken gibt es?
5. Empfehlungen fuer die Website — Was muss sie zeigen? Welche Inhalte heben ab?
6. Lokale SEO Chancen — Wichtige Suchbegriffe fuer {trade} in {city}, Google Business Tipps

Schreibe kompakt und praxisnah. Maximal 500 Woerter. Auf Deutsch."""

    # ── Phase 2: Claude-Call OHNE DB-Connection ──────────────────────
    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), max_retries=0, timeout=60.0)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        analyse = response.content[0].text
    except Exception as e:
        logger.error(f"Wettbewerbsanalyse Claude-Fehler: {e}")
        raise HTTPException(500, f"Analyse fehlgeschlagen: {str(e)}")

    # ── Phase 3: Persist in frischer Session ─────────────────────────
    analyse_datum = datetime.utcnow().strftime("%d.%m.%Y %H:%M")
    db2 = SessionLocal()
    try:
        briefing = db2.query(Briefing).filter(Briefing.lead_id == lead_id).first()
        if not briefing:
            briefing = Briefing(lead_id=lead_id)
            db2.add(briefing)

        current = (
            json.loads(briefing.wettbewerb)
            if briefing.wettbewerb and briefing.wettbewerb != "{}"
            else {}
        )
        updated = {
            **current,
            "analyse": analyse,
            "analyse_datum": analyse_datum,
            "region": region,
        }
        briefing.wettbewerb = json.dumps(updated, ensure_ascii=False)
        briefing.updated_at = datetime.utcnow()
        db2.commit()
    except Exception as e:
        db2.rollback()
        logger.error(f"Wettbewerbsanalyse Persist-Fehler: {e}")
        raise HTTPException(500, f"Analyse konnte nicht gespeichert werden: {str(e)[:200]}")
    finally:
        db2.close()

    return {"analyse": analyse, "region": region, "datum": analyse_datum}
