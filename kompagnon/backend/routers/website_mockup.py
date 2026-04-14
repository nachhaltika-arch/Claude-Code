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
    # Tor 1: Briefing-Freigabe-Gate (Baustein 2). customer_id == lead_id.
    from database import require_briefing_approved_for_lead
    require_briefing_approved_for_lead(customer_id, db)

    lead = db.query(Lead).filter(Lead.id == customer_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    name   = lead.display_name or lead.company_name or f"Betrieb #{customer_id}"
    gewerk = lead.trade or "Handwerk"
    city   = lead.city or "Deutschland"
    phone  = lead.phone or ""
    email  = lead.email or ""

    system_prompt = (
        "Du bist ein professioneller Webdesigner für deutsche Handwerksbetriebe."
    )

    user_prompt = (
        f"Erstelle eine vollständige, professionelle einseitige HTML-Website für folgenden Betrieb:\n"
        f"Name: {name}, Gewerk: {gewerk}, Stadt: {city}, "
        f"Telefon: {phone}, E-Mail: {email}.\n"
        f"Abschnitte: Hero mit Headline, Leistungen, Über uns, Kontakt.\n"
        f"Modernes CSS eingebettet, deutsche Sprache, professionelle Farben passend zum Gewerk.\n"
        f"Gib NUR den vollständigen HTML-Code zurück, nichts sonst."
    )

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
        logger.error(
            "generate_design Fehler für customer_id=%s: %s",
            customer_id, e, exc_info=True,
        )
        raise HTTPException(status_code=500, detail="KI-Generierung fehlgeschlagen")
