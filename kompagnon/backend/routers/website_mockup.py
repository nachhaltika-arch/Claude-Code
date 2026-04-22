"""
Website Design Generator
POST /api/customers/{customer_id}/generate-design
Generates a complete single-page HTML website for a lead/customer using Claude AI.
"""
import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, Lead
from routers.auth_router import require_any_auth

logger = logging.getLogger(__name__)

router = APIRouter(tags=["website_mockup"])


@router.post("/customers/{customer_id}/generate-design")
async def generate_design(
    customer_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """
    Generate a complete single-page HTML website design for a lead/customer.
    customer_id corresponds to the Lead.id (leads are the primary record in the UI).
    """
    lead = db.query(Lead).filter(Lead.id == customer_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    name   = lead.display_name or lead.company_name or f"Betrieb #{customer_id}"
    gewerk = lead.trade or "Handwerk"
    city   = lead.city or "Deutschland"
    phone  = lead.phone or ""
    email  = lead.email or ""

    system_prompt = """Du bist erstklassiger Webdesigner für deutsche Handwerksbetriebe.

LAYOUT: max-width 1140px, 40px Padding, Sections 80px vertikal.
FONTS: Poppins (Überschriften 700-800) + Inter (Body 400-500) via Google Fonts.
H1: clamp(36px,5vw,64px) weight 800. H2: clamp(26px,3.5vw,42px) weight 700. Body: 16-18px line-height 1.7.
FARBEN: CSS Custom Properties (--primary, --secondary, --accent). Kein reines Schwarz/Weiß.
HERO: IMMER Split-Layout — Links Text+CTA, rechts Fakten-Box mit 4 Zahlen.
CARDS: border-radius 16px, box-shadow 0 4px 16px rgba(0,0,0,.08), hover translateY(-4px).
BUTTONS: padding 14px 28px, border-radius 8px, font-weight 600.

SEKTIONEN: Nav → Hero(Split,600px+) → USP-Balken(4 Fakten) → Leistungen(3-Grid) → Über-uns → Referenzen(3 Karten) → CTA-Banner(dunkel) → Footer

VERBOTEN: Lorem Ipsum, generische H1, Bootstrap, !important, externe Frameworks.
PFLICHT: CSS-Reset, Custom Properties, Google Fonts @import, Media Query 768px.

Antworte NUR mit vollständigem HTML. Kein Markdown."""

    user_prompt = f"""Erstelle professionelle einseitige Website:

FIRMA: {name} | BRANCHE: {gewerk} | STADT: {city} | TEL: {phone} | MAIL: {email}

PRIMARY nach Branche: Elektriker=#1D4ED8, Sanitär=#0F766E, Maler=#EA580C,
Gärtner=#15803D, Dachdecker=#475569, Zimmerer=#92400E, Kfz=#1F2937, Standard=#004F59

PFLICHT: H1 enthält Gewerk+{city}. Hero-Fakten: Kunden/Jahre/Bewertung/Notdienst.
3+ Leistungen, 3 Kundenbewertungen (realistisch, Name+Ort). Tel {phone} im CTA.
Alle Texte Deutsch, aktive Sprache.

Vollständiger HTML-Code:"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY nicht konfiguriert")

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key, max_retries=0, timeout=120.0)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        html = response.content[0].text.strip()

        # Strip markdown code fences if Claude wrapped the HTML
        if html.startswith("```"):
            lines = html.splitlines()
            html = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            ).strip()

        return {"html": html}

    except Exception as e:
        logger.error("generate_design Fehler für customer_id=%s: %s", customer_id, e)
        raise HTTPException(status_code=500, detail=f"KI-Generierung fehlgeschlagen: {e}")
