"""Die KI-Vorbefuellung des Briefings (L-25, 22.08.2026).

**Warum diese Datei existiert.** `routers/briefings.py` war nach dem
Zusammenlegen der beiden Briefing-Router 958 Zeilen lang (L-27) — und die
Haelfte davon waren sechs Routen, die alle dasselbe tun: ein Modell fragen
und die Antwort in ein Briefing-Feld schreiben. Sie haben mit den
Stammdaten nichts gemeinsam ausser dem Gegenstand.

Geschnitten ist deshalb nach **Zustaendigkeit**, nicht nach Groesse:

* `briefings.py`     — anlegen, lesen, aendern, freigeben, PDF, Anhaenge
* `briefings_ki.py`  — was ein Modell vorschlaegt

Kein Helfer aus der Ursprungsdatei wird hier gebraucht; der Schnitt
verlaeuft ohne Naht.

**Alle sechs Routen sind Innendienst.** Vier trugen in ihrer Signatur
`require_any_auth` und lagen trotzdem unter einem Router mit
`require_innendienst` — dieselbe irrefuehrende Bauart wie bei den
Wireframe-Routen (L-87). Die Signaturen sind beim Umzug angeglichen worden,
damit Funktionskopf und Wirklichkeit dasselbe sagen.
"""
import json
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Briefing, Lead, get_db
from routers.auth_router import require_innendienst
from services.ki_aufruf import frag_modell

logger = logging.getLogger(__name__)

# Dasselbe Praefix wie `briefings.py`. Zwei Router auf einem Praefix waren
# der Befund von L-27 — dort lagen sie aber in zwei Dateien und waren nach
# HTTP-Verb getrennt, unsichtbar fuereinander. Hier ist die Trennung
# fachlich, beide Dateien nennen einander im Kopf, und ein Test verbietet
# jede Ueberschneidung.
router = APIRouter(prefix="/api/briefings", tags=["briefings-ki"],
                   dependencies=[Depends(require_innendienst)])


@router.post("/{lead_id}/suggest-field")
async def suggest_field(
    lead_id: int,
    data: dict,
    db: Session = Depends(get_db),
    _=Depends(require_innendienst),
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
                json={"model": "claude-sonnet-5", "thinking": {"type": "disabled"}, "max_tokens": 400, "messages": [{"role": "user", "content": prompt}]},
            )
        resp.raise_for_status()
        suggestion = resp.json()["content"][0]["text"].strip()
        return {"field": field, "suggestion": suggestion}
    except Exception as e:
        raise HTTPException(500, f"Vorschlag fehlgeschlagen: {str(e)[:150]}")


@router.get("/{lead_id}/ki-prefill-funktionen")
def prefill_funktionen(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_innendienst),
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
    _=Depends(require_innendienst),
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
                    json={"model": "claude-sonnet-5", "thinking": {"type": "disabled"}, "max_tokens": 200,
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
    _=Depends(require_innendienst),
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
                json={"model": "claude-sonnet-5", "thinking": {"type": "disabled"}, "max_tokens": 800,
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


@router.post('/{lead_id}/zielgruppenanalyse')
async def zielgruppenanalyse(lead_id: int, db: Session = Depends(get_db)):
    """AI-powered target audience analysis based on lead trade + city."""
    from anthropic import Anthropic

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    trade = lead.trade or 'Handwerk'
    city = lead.city or 'Deutschland'
    company = lead.display_name or lead.company_name or ''

    prompt = f"""Du bist ein erfahrener Marketing-Stratege für Handwerksbetriebe in Deutschland.

Analysiere die Zielgruppe für diesen Betrieb:
- Unternehmen: {company}
- Branche/Gewerk: {trade}
- Standort: {city}

Erstelle eine strukturierte Zielgruppenanalyse mit:
1. Primäre Zielgruppe (wer kauft hauptsächlich)
2. Sekundäre Zielgruppe
3. Demografische Merkmale (Alter, Geschlecht, Einkommen)
4. Psychografische Merkmale (Werte, Bedürfnisse, Schmerzpunkte)
5. Kaufmotivation (Warum beauftragen sie einen {trade}?)
6. Entscheidungskriterien (Was ist bei der Auswahl wichtig?)
7. Bevorzugte Kommunikationskanäle
8. Empfehlung für die Website-Ansprache

Schreibe kompakt und praxisnah. Maximal 400 Wörter. Auf Deutsch."""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), max_retries=0, timeout=60.0)
        response = await frag_modell(
            client,
            model='claude-sonnet-5', thinking={"type": "disabled"}, max_tokens=1000,
            messages=[{'role': 'user', 'content': prompt}],
        )
        analyse = response.content[0].text

        briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
        if not briefing:
            briefing = Briefing(lead_id=lead_id)
            db.add(briefing)

        current = json.loads(briefing.zielgruppe) if briefing.zielgruppe and briefing.zielgruppe != '{}' else {}
        updated = {**current, 'analyse': analyse, 'analyse_datum': datetime.utcnow().strftime('%d.%m.%Y %H:%M')}
        briefing.zielgruppe = json.dumps(updated, ensure_ascii=False)
        briefing.updated_at = datetime.utcnow()
        db.commit()

        return {'analyse': analyse, 'datum': updated['analyse_datum']}
    except Exception as e:
        logger.error(f'Zielgruppenanalyse Fehler: {e}')
        raise HTTPException(500, f'Analyse fehlgeschlagen: {str(e)}')


@router.post('/{lead_id}/wettbewerbsanalyse')
async def wettbewerbsanalyse(lead_id: int, db: Session = Depends(get_db)):
    """AI-powered competitor analysis based on lead trade + city + region."""
    from anthropic import Anthropic

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    trade = lead.trade or 'Handwerk'
    city = lead.city or 'Deutschland'
    postal_code = lead.postal_code or ''
    company = lead.display_name or lead.company_name or ''
    region = f"{city} ({postal_code})" if postal_code else city

    prompt = f"""Du bist ein erfahrener Markt- und Wettbewerbsanalyst für Handwerksbetriebe in Deutschland.

Erstelle eine Wettbewerbsanalyse für:
- Unternehmen: {company}
- Branche/Gewerk: {trade}
- Region: {region} und 50 km Umkreis

Analysiere:
1. Marktübersicht — Typische Anzahl Wettbewerber, Marktstruktur
2. Typische Wettbewerber-Profile — Wie präsentieren sie sich online?
3. Online-Präsenz der Wettbewerber — Typischer Stand der Websites, Stärken, Schwächen
4. Differenzierungspotenzial — Wo kann sich {company} abheben? Welche Lücken gibt es?
5. Empfehlungen für die Website — Was muss sie zeigen? Welche Inhalte heben ab?
6. Lokale SEO Chancen — Wichtige Suchbegriffe für {trade} in {city}, Google Business Tipps

Schreibe kompakt und praxisnah. Maximal 500 Wörter. Auf Deutsch."""

    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), max_retries=0, timeout=60.0)
        response = await frag_modell(
            client,
            model='claude-sonnet-5', thinking={"type": "disabled"}, max_tokens=1200,
            messages=[{'role': 'user', 'content': prompt}],
        )
        analyse = response.content[0].text

        briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
        if not briefing:
            briefing = Briefing(lead_id=lead_id)
            db.add(briefing)

        current = json.loads(briefing.wettbewerb) if briefing.wettbewerb and briefing.wettbewerb != '{}' else {}
        updated = {**current, 'analyse': analyse, 'analyse_datum': datetime.utcnow().strftime('%d.%m.%Y %H:%M'), 'region': region}
        briefing.wettbewerb = json.dumps(updated, ensure_ascii=False)
        briefing.updated_at = datetime.utcnow()
        db.commit()

        return {'analyse': analyse, 'region': region, 'datum': updated['analyse_datum']}
    except Exception as e:
        logger.error(f'Wettbewerbsanalyse Fehler: {e}')
        raise HTTPException(500, f'Analyse fehlgeschlagen: {str(e)}')
