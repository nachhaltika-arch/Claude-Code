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

    system_prompt = """Du bist ein erstklassiger Webdesigner und Frontend-Entwickler.
Du erstellst vollstaendige, professionelle HTML-Websites fuer deutsche Handwerksbetriebe.

DEIN DESIGN-STANDARD — jede Website muss diese Qualitaetsmerkmale haben:

## LAYOUT & STRUKTUR
- Max-Width: 1140px, zentriert, mit 40px horizontalem Padding auf Desktop
- Mobile-First: alle Layouts brechen bei 768px auf Einspaltigkeit um
- Sections haben mind. 80px vertikales Padding (60px auf Mobile)
- Konsistente Abstands-Hierarchie: 8px Basis, Vielfache davon (16, 24, 32, 48, 64, 80px)

## TYPOGRAFIE-SYSTEM
- Google Font: "Inter" fuer Fliesstext, "Poppins" fuer Ueberschriften (600-800 weight)
- H1: clamp(36px, 5vw, 64px), Gewicht 800, line-height 1.1
- H2: clamp(26px, 3.5vw, 42px), Gewicht 700, line-height 1.2
- H3: 20-24px, Gewicht 600
- Body: 16-18px, line-height 1.7, color #374151
- Kein Text unter 13px

## FARB-SYSTEM
- Verwende die uebergebenen Branding-Farben als Primary
- Sekundaer: dunklere Variante der Primary (-20% Helligkeit)
- Accent: hell aufgehellte Variante (+85% Helligkeit) fuer Hintergruende
- Neutral: #F9FAFB (sehr hell), #F3F4F6 (hell), #E5E7EB (Rand), #6B7280 (Text sekundaer), #111827 (Text primaer)
- NIEMALS reines Schwarz oder Weiss — immer mit leichtem Farbton

## HERO-SECTION — modern, nicht generisch
Gute Heros haben EINES der folgenden Layouts:
A) Split-Layout: Links Text + CTA, rechts Illustration/Foto-Placeholder (60/40)
B) Full-Width mit Overlay: Hintergrundbild-Placeholder + Gradient-Overlay + Text zentriert
C) Asymmetrisch: Grosser farbiger Blob links, Text rechts daneben
NICHT: simpler Farbverlauf + Text zentriert — das ist Standard und sieht billig aus

## KOMPONENTEN-QUALITAET

### Buttons
- Primary: filled, abgerundet (radius 8px), hover mit leichtem Scale(1.02)
- Secondary: outlined, gleiche Groesse
- Mindest-Padding: 14px 28px, font-weight 600
- NIEMALS eckige Buttons ohne radius

### Cards / Feature-Boxen
- Schatten: box-shadow: 0 1px 3px rgba(0,0,0,.1), 0 4px 16px rgba(0,0,0,.05)
- Border: 1px solid #E5E7EB
- Border-radius: 12-16px
- Hover: leichter translateY(-4px) Effekt per CSS
- Innenabstand: 24-32px

### Icons
- Nutze SVG-Icons (inline) ODER Unicode-Zeichen in einem farbigen Kreis/Quadrat
- Icon-Container: 48-56px, border-radius 12px, Hintergrund = Primary mit 10-15% Opacity
- NIEMALS Emoji als einzige Icon-Loesung (ausser als Ergaenzung)

## SEKTIONEN-REIHENFOLGE (Startseite)
1. Navigation (sticky, mit Logo-Placeholder + Links + CTA-Button)
2. Hero (mind. 600px hoch, mit konkretem USP in H1)
3. Social Proof Bar (3-4 Zahlen/Fakten: "500+ Kunden", "20 Jahre", "4.9 \u2605")
4. Leistungen (3-spaltig auf Desktop, mit Icons und Hover-Effekt)
5. Ueber uns (Bild-Placeholder links + Text rechts, mit Fakten-Liste)
6. Referenzen / Bewertungen (3 Karten mit 5 Sternen)
7. CTA-Banner (kontrastreich, mit Telefon prominent)
8. Footer (3-spaltig, dunkel)

## CSS-ANFORDERUNGEN
- CSS-Reset am Anfang (*, box-sizing: border-box, margin:0, padding:0)
- CSS Custom Properties (--primary, --secondary, --accent etc.) am :root
- Smooth hover transitions: transition: all 0.2s ease
- Google Fonts via @import einbinden
- Media Queries fuer 768px und 480px Breakpoints
- Print-freundliche Grundstruktur

## WAS VERBOTEN IST
- Kein Lorem Ipsum — echter branchen-spezifischer Text
- Kein generischer "Willkommen auf unserer Website" H1
- Keine table-basierten Layouts
- Keine inline-Styles fuer Design (nur fuer dynamische Werte wie Farben)
- Kein !important ausser in Notfaellen
- Keine externen CSS-Frameworks (Bootstrap etc.) — nur reines CSS
- Keine JavaScript-abhaengigen Layouts

Antworte NUR mit dem vollstaendigen HTML-Code. Kein Markdown, keine Erklaerungen."""

    user_prompt = f"""Erstelle eine professionelle einseitige Website fuer:

UNTERNEHMEN: {name}
BRANCHE / GEWERK: {gewerk}
STADT: {city}
TELEFON: {phone}
E-MAIL: {email}

DESIGN-ENTSCHEIDUNGEN:
- Primary-Farbe: Waehle eine zur Branche passende Farbe
  (Elektriker -> kraeftiges Blau #1D4ED8, Sanitaer -> Teal #0F766E,
   Maler -> Orange #EA580C, Gaertner -> Gruen #15803D,
   Dachdecker -> Slate #475569, Zimmerer -> Braun #92400E,
   Kfz -> Dunkelgrau #1F2937)
- Schrift: Poppins fuer Ueberschriften, Inter fuer Fliesstext (beide via Google Fonts)
- Stil: Modern, professionell, vertrauenswuerdig

INHALT-ANFORDERUNGEN:
- H1 muss Gewerk + Stadt enthalten (z.B. "Ihr Elektriker in {city}")
- USP prominent: Schnelligkeit, Zuverlaessigkeit, Erfahrung
- Mind. 3 konkrete Leistungen mit kurzer Beschreibung
- 3 Social-Proof-Zahlen (Erfahrungsjahre, Kundenzahl, Bewertung)
- 3 Kundenbewertungen (erfunden aber realistisch klingend, mit Name und Ort)
- Kontaktbereich mit Telefon und E-Mail prominent
- Alle Texte auf Deutsch, aktive Sprache ("Wir kommen zu Ihnen")

Erstelle jetzt den vollstaendigen HTML-Code:"""

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
