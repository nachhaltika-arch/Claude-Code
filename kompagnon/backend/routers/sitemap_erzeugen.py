"""Seiten vorschlagen und erzeugen lassen (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/sitemap.py` hatte 1.800 Zeilen.
Sieben Routen, die alle ein Modell fragen: Was soll auf diese Website?
Dazu die zwei Helfer, die den Vorschlag in Zeilen verwandeln.

Die Verflechtung ist **transitiv** gemessen — nicht nur, was die Routen
brauchen, sondern auch, was deren Helfer brauchen. Beim Schnitt davor war
genau das die Luecke, und vier Namen fielen erst dem Lint auf.

Geteilt bleiben 2 Helfer, die auch der Rest braucht; sie werden von
dort geholt statt kopiert.
"""
import json
import os
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, text
from sqlalchemy.orm import Session
from database import Base, Briefing, Lead, get_db
from routers.auth_router import require_any_auth, optional_auth, require_innendienst
from services.ki_aufruf import frag_modell

from routers.sitemap import DEFAULT_SECTIONS_BY_PAGETYPE, PFLICHTSEITEN_BEDINGT, SECTION_CATALOG, SitemapPage, logger, _serialize, _ensure_pflichtseiten

# Optionale Zusatzseiten (Vorschlagskatalog)
OPTIONALE_SEITEN = [
    # Basis-Seiten
    {"page_name": "Startseite",     "page_type": "startseite", "position":  1, "zweck": "Hauptseite des Auftritts — erster Eindruck, Hero-Bereich, USP, CTA",                    "ziel_keyword": "Startseite Home",               "empfohlen_fuer": ["alle"],                                           "gruppe": "basis"},
    {"page_name": "Leistungen",     "page_type": "leistung",   "position":  2, "zweck": "Übersicht aller angebotenen Leistungen — zentraler SEO-Treiber",                         "ziel_keyword": "Leistungen Angebote",            "empfohlen_fuer": ["alle"],                                           "gruppe": "basis"},
    {"page_name": "Über uns",       "page_type": "info",       "position":  3, "zweck": "Geschichte, Team und Werte des Unternehmens — baut Vertrauen auf",                       "ziel_keyword": "Über uns Unternehmen",           "empfohlen_fuer": ["alle"],                                           "gruppe": "basis"},
    {"page_name": "Kontakt",        "page_type": "conversion", "position":  4, "zweck": "Kontaktformular, Adresse, Öffnungszeiten — Hauptkonversionspunkt",                       "ziel_keyword": "Kontakt Anfrage",                "empfohlen_fuer": ["alle"],                                           "gruppe": "basis"},
    {"page_name": "Landingpage",    "page_type": "conversion", "position":  5, "zweck": "Kampagnen-spezifische Zielseite für Ads / Aktionen — hohe Konversionsrate",              "ziel_keyword": "Angebot Aktion",                 "empfohlen_fuer": ["alle"],                                           "gruppe": "basis"},
    # Vertrauen & Inhalte
    {"page_name": "FAQ",            "page_type": "info",       "position": 10, "zweck": "Häufige Fragen und Antworten — stärkt Vertrauen, reduziert Supportaufwand",              "ziel_keyword": "FAQ häufige Fragen",             "empfohlen_fuer": ["alle"],                                           "gruppe": "inhalte"},
    {"page_name": "Blog / News",    "page_type": "info",       "position": 11, "zweck": "Aktuelle Beiträge, Neuigkeiten und Expertise — gut für SEO und Reichweite",              "ziel_keyword": "News Aktuelles Blog",            "empfohlen_fuer": ["alle"],                                           "gruppe": "inhalte"},
    {"page_name": "Galerie",        "page_type": "vertrauen",  "position": 12, "zweck": "Fotos abgeschlossener Projekte — visueller Beweis der Qualität",                         "ziel_keyword": "Galerie Referenzbilder Projekte","empfohlen_fuer": ["handwerk", "bau", "garten", "maler", "fotograf"], "gruppe": "inhalte"},
    {"page_name": "Referenzen",     "page_type": "vertrauen",  "position": 13, "zweck": "Kundenstimmen und abgeschlossene Projekte — Social Proof",                               "ziel_keyword": "Referenzen Kundenprojekte",      "empfohlen_fuer": ["alle"],                                           "gruppe": "inhalte"},
    {"page_name": "Team",           "page_type": "vertrauen",  "position": 14, "zweck": "Mitarbeitervorstellung — schafft Nähe, Vertrauen und Persönlichkeit",                    "ziel_keyword": "Team Mitarbeiter Experten",      "empfohlen_fuer": ["alle"],                                           "gruppe": "inhalte"},
    # Conversion & Spezial
    {"page_name": "Preise",         "page_type": "conversion", "position": 20, "zweck": "Preistransparenz — reduziert Anfragehürde, qualifiziert Leads vorab",                   "ziel_keyword": "Preise Kosten Angebot",          "empfohlen_fuer": ["dienstleistung", "beratung", "coaching"],         "gruppe": "conversion"},
    {"page_name": "Karriere / Jobs","page_type": "info",       "position": 21, "zweck": "Offene Stellen und Ausbildungsplätze — Fachkräftegewinnung",                            "ziel_keyword": "Jobs Karriere Ausbildung",       "empfohlen_fuer": ["alle"],                                           "gruppe": "conversion"},
    {"page_name": "Online-Shop",    "page_type": "conversion", "position": 22, "zweck": "Produkte online kaufen — E-Commerce-Integration",                                       "ziel_keyword": "Shop Produkte bestellen kaufen", "empfohlen_fuer": ["handel", "ecommerce"],                            "gruppe": "conversion"},
    {"page_name": "Notfallservice", "page_type": "conversion", "position": 23, "zweck": "24h Notdienst — wichtig für Handwerker mit Bereitschaftsdienst",                        "ziel_keyword": "Notfall Notdienst 24h",          "empfohlen_fuer": ["elektriker", "sanitaer", "heizung", "schlosserei"],"gruppe": "conversion"},
    {"page_name": "Terminbuchung",  "page_type": "conversion", "position": 24, "zweck": "Online-Terminbuchung — reduziert Telefon-Aufwand, erhöht Konversion",                  "ziel_keyword": "Termin buchen online",           "empfohlen_fuer": ["dienstleistung", "beratung", "handwerk"],         "gruppe": "conversion"},
]

_FALLBACK_PAGES = [
    {"page_name": "Startseite",                 "page_type": "startseite", "position": 0,  "parent_id": None, "zweck": "Erster Eindruck, klare Botschaft",                                               "ziel_keyword": "", "cta_text": "Jetzt anfragen",    "cta_ziel": "kontakt"},
    {"page_name": "Leistungen",                 "page_type": "leistung",   "position": 1,  "parent_id": None, "zweck": "Übersicht aller Leistungen",                                                      "ziel_keyword": "", "cta_text": "Mehr erfahren",     "cta_ziel": "kontakt"},
    {"page_name": "Leistung 1",                 "page_type": "leistung",   "position": 2,  "parent_id": 1,    "zweck": "Detail-Seite erste Leistung",                                                     "ziel_keyword": "", "cta_text": "Angebot anfordern", "cta_ziel": "kontakt"},
    {"page_name": "Leistung 2",                 "page_type": "leistung",   "position": 3,  "parent_id": 1,    "zweck": "Detail-Seite zweite Leistung",                                                    "ziel_keyword": "", "cta_text": "Angebot anfordern", "cta_ziel": "kontakt"},
    {"page_name": "Über uns",                   "page_type": "vertrauen",  "position": 4,  "parent_id": None, "zweck": "Vertrauen aufbauen, Team vorstellen",                                             "ziel_keyword": "", "cta_text": "Kontakt aufnehmen", "cta_ziel": "kontakt"},
    {"page_name": "Kontakt",                    "page_type": "conversion", "position": 5,  "parent_id": None, "zweck": "Leadgenerierung, Kontaktformular",                                                "ziel_keyword": "", "cta_text": "Nachricht senden",  "cta_ziel": "kontakt"},
    {"page_name": "Über uns & Informationen",   "page_type": "ground",     "position": 99, "parent_id": None, "zweck": "Maschinenlesbare Informationsseite für KI-Systeme (GEO-Optimierung)",             "ziel_keyword": "",  "cta_text": "Jetzt Kontakt aufnehmen", "cta_ziel": "kontakt", "notizen": "Ground Page — GEO/KI-Optimierung"},
]

router = APIRouter(prefix="/api/sitemap", tags=["sitemap-erzeugen"],
                   dependencies=[Depends(require_innendienst)])


@router.post("/{lead_id}/generate")
async def generate_sitemap(
    lead_id: int,
    body: dict = Body(default={}),
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generate sitemap pages via Claude AI (or fallback template).

    Optional body:
      - "page_count": N — geclamped auf 3..15. Default: KI entscheidet (5-8).
      - "as_variant": bool — true = parallele Alternative, false = neue Live.
    """
    as_variant = bool((body or {}).get("as_variant"))
    target_variant = "variant" if as_variant else "primary"
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    # Tor 1: Briefing muss vom Kunden freigegeben sein
    proj_row = db.execute(
        text(
            "SELECT briefing_approved_at FROM projects "
            "WHERE lead_id=:lid ORDER BY id DESC LIMIT 1"
        ),
        {"lid": lead_id},
    ).fetchone()
    if not proj_row or not proj_row[0]:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "BRIEFING_NOT_APPROVED",
                "message": "Das Briefing wurde noch nicht freigegeben. Bitte zuerst eine Freigabe-E-Mail senden und die Kundenfreigabe einholen.",
            },
        )

    # Step 1: Pflichtseiten nur bei primary-Generation sicherstellen.
    # Pflichtseiten leben ausschließlich im Primary-Slot — der Variant-Tab
    # zeigt nur die KI-Alternativvorschläge.
    if not as_variant:
        _ensure_pflichtseiten(lead_id, db)

    briefing      = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    gewerk        = (getattr(briefing, "gewerk",        None) if briefing else None) or getattr(lead, "trade", None) or "Handwerk"
    leistungen    = (getattr(briefing, "leistungen",    None) if briefing else None) or ""
    einzugsgebiet = (getattr(briefing, "einzugsgebiet", None) if briefing else None) or getattr(lead, "city", None) or "Deutschland"
    usp           = (getattr(briefing, "usp",           None) if briefing else None) or ""
    zielgruppe    = (getattr(briefing, "zielgruppe",    None) if briefing else None) or "Privatkunden und Gewerbekunden"
    wunschseiten  = (getattr(briefing, "wunschseiten",  None) if briefing else None) or ""
    city          = getattr(lead, "city", None) or "Deutschland"
    company       = getattr(lead, "company_name", None) or getattr(lead, "display_name", None) or ""

    # Gecrawlte Seiten der alten Website laden
    old_pages_summary = ""
    try:
        from sqlalchemy import text as _text
        crawled = db.execute(
            _text("""
                SELECT url, h1, title
                FROM website_content_cache
                WHERE customer_id = :lid
                ORDER BY scraped_at DESC
                LIMIT 12
            """),
            {"lid": lead_id},
        ).fetchall()
        if crawled:
            old_pages_summary = "Seiten der alten Website (gecrawlt):\n" + "\n".join(
                [f"- {r[2] or r[1] or r[0]}" for r in crawled[:10]]
            )
    except Exception:
        old_pages_summary = ""

    # Step 2: Frühere KI-Vorschläge im Ziel-Slot (primary oder variant) löschen.
    # Bestand und manuelle Pages bleiben erhalten. Bei variant-Generation wird
    # primary nicht angefasst.
    db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.ist_pflichtseite.is_(False),
        SitemapPage.source == "ki_generated",
        SitemapPage.variant == target_variant,
    ).delete(synchronize_session=False)
    db.commit()

    # Phase 3: Bestand (source='crawled') als Prompt-Input für die KI lesen.
    # Pro Bestandsseite gibt der Prompt id/name/type/url, damit die KI im
    # Output `replaces_page_ids: [<bestands-id>, ...]` setzen kann.
    # Bestand lebt immer in primary, deshalb keine variant-Filter hier.
    crawled_pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.source == "crawled")
        .order_by(SitemapPage.position, SitemapPage.id)
        .all()
    )
    bestand_section = ""
    if crawled_pages:
        lines = ["BESTANDS-SEITEN (Phase-1 Crawl der aktuellen Website):"]
        for cp in crawled_pages[:30]:
            url = cp.original_url or ""
            ptype = cp.page_type or "sonstige"
            lines.append(f"  ID {cp.id} | {cp.page_name} | {ptype} | {url}")
        bestand_section = "\n".join(lines)

    # Step 3: KI oder Fallback
    api_key = os.getenv("ANTHROPIC_API_KEY")
    source = "fallback"
    if not api_key:
        _insert_pages(lead_id, _FALLBACK_PAGES, db, variant=target_variant)
    else:
        wunschseiten_hint = (
            f"\nDer Kunde hat folgende Seiten gewünscht: {wunschseiten}"
            if wunschseiten else ""
        )
        old_pages_hint = (
            f"\n{old_pages_summary}"
            if old_pages_summary else ""
        )
        bestand_hint = f"\n\n{bestand_section}" if bestand_section else ""
        bestand_mapping_rule = (
            "\n- Wenn BESTANDS-SEITEN vorhanden sind: pro neuer Inhaltsseite "
            "OPTIONAL `replaces_page_ids: [<id>, ...]` setzen mit den IDs der "
            "Bestandsseiten, die diese neue Seite konsolidiert oder ersetzt. "
            "Leer lassen / weglassen wenn die neue Seite keinen Bestandsbezug hat. "
            "Eine Bestandsseite darf von mehreren neuen Pages referenziert werden."
            if bestand_section else ""
        )
        # Section-Katalog kompakt für den Prompt (key: kurzbeschreibung)
        section_catalog_text = "\n".join(
            f"  - {key}: {desc}" for key, desc in SECTION_CATALOG.items()
        )
        # User-gewählte Seitenanzahl (R1) — geclamped auf vernünftige Range.
        try:
            page_count = int((body or {}).get("page_count") or 0)
        except (TypeError, ValueError):
            page_count = 0
        if page_count < 3 or page_count > 15:
            page_count_text = "5-8"
        else:
            page_count_text = str(page_count)
        prompt = (
            "Du bist ein Website-Stratege für deutsche Handwerksbetriebe.\n"
            f"Erstelle eine optimale Sitemap mit {page_count_text} INHALTLICHEN Seiten für diesen Betrieb.\n"
            "Pro Seite gibst du auch an, WELCHE Conversion-Sections (siehe Section-Katalog unten) "
            "in welcher Reihenfolge auf der Seite stehen sollen — basierend auf Hormozi-Conversion-Spec.\n\n"
            "WICHTIG — NICHT einschließen (werden automatisch ergänzt):\n"
            "Impressum, Datenschutz, AGB, Barrierefreiheit, Cookie-Hinweise\n\n"
            f"UNTERNEHMEN:\n"
            f"- Firma: {company}\n"
            f"- Gewerk/Branche: {gewerk}\n"
            f"- Leistungen: {leistungen}\n"
            f"- Region/Einzugsgebiet: {einzugsgebiet}\n"
            f"- USP (Alleinstellungsmerkmal): {usp or '–'}\n"
            f"- Zielgruppe: {zielgruppe}\n"
            f"{wunschseiten_hint}"
            f"{old_pages_hint}"
            f"{bestand_hint}\n\n"
            "SECTION-KATALOG (du wählst pro Page eine geordnete Liste aus diesen Keys):\n"
            f"{section_catalog_text}\n\n"
            "REGELN FÜR DIE SITEMAP:\n"
            "- Position 0 = Startseite (immer)\n"
            "- Jede Hauptleistung bekommt eine eigene Seite (page_type='leistung')\n"
            "- Vertrauensseite einplanen (Referenzen, Team, Über uns)\n"
            "- Kontaktseite immer als letzte Inhaltsseite\n"
            "- ziel_keyword auf die wichtigsten SEO-Begriffe abstimmen\n"
            "- Branchenspezifisch denken: Was sucht die Zielgruppe wirklich?"
            f"{bestand_mapping_rule}\n\n"
            "REGELN FÜR DIE SECTION-AUSWAHL pro Page:\n"
            "- Startseite: hero_value_equation am Anfang, mind. offer_stack ODER service_grid, "
            "  trust_strip, fallstudien_3, guarantee_block, faq, cta_final am Ende. Reihenfolge wichtig.\n"
            "- Leistung: hero_service am Anfang, problem, offer_stack (Service-spezifisch), "
            "  process_steps, fallstudien_3, guarantee_block, faq_service, cta_final am Ende.\n"
            "- Vertrauen: hero_minimal, team, fallstudien_3, trust_strip, cta_inline.\n"
            "- Conversion (Landingpage): hero_minimal, offer_stack, guarantee_block, urgency_block, "
            "  contact_form, cta_final.\n"
            "- Ground (GEO): hero_minimal, service_grid, faq, contact_form.\n"
            "- Info-Seite: hero_minimal, content_richtext, faq, cta_inline.\n"
            "- Pro Seite mind. 4, max. 9 Sections. Keine Duplikate. cta_final immer am Ende von "
            "  Conversion-relevanten Pages.\n\n"
            "PFLICHT: Füge IMMER genau eine Seite mit page_type='ground' ein (position 99):\n"
            '{ "page_name": "Über uns & Informationen", "page_type": "ground", "position": 99, '
            '"zweck": "Maschinenlesbare Informationsseite für KI-Systeme (GEO-Optimierung)", '
            f'"ziel_keyword": "{gewerk} {einzugsgebiet} Informationen", '
            '"cta_text": "Jetzt Kontakt aufnehmen", "cta_ziel": "kontakt", "parent_id": null, '
            '"sections": ["hero_minimal","service_grid","faq","contact_form"] }\n\n'
            "Antworte NUR als JSON-Array — kein Markdown, keine Erklärungen:\n"
            '[{ "page_name": "", "page_type": "startseite|leistung|info|vertrauen|conversion|ground", '
            '"zweck": "", "ziel_keyword": "", "cta_text": "", "cta_ziel": "kontakt|formular|tel", '
            '"position": 0, "parent_id": null, '
            '"sections": ["hero_xxx","..."], '
            '"replaces_page_ids": [] }]'
        )
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key, max_retries=0, timeout=60.0)
            response = await frag_modell(
                client,
                model="claude-sonnet-5", thinking={"type": "disabled"},
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = "\n".join(
                    line for line in raw.splitlines()
                    if not line.strip().startswith("```")
                ).strip()
            # Truncated JSON repair: close open strings/objects/arrays
            try:
                raw_pages = json.loads(raw)
            except json.JSONDecodeError:
                repaired = raw.rstrip().rstrip(",")
                if not repaired.endswith("]"):
                    # Close any unterminated string
                    if repaired.count('"') % 2 != 0:
                        repaired += '"'
                    # Close unterminated object
                    open_braces = repaired.count("{") - repaired.count("}")
                    repaired += "}" * max(0, open_braces)
                    # Close array
                    if not repaired.endswith("]"):
                        repaired += "]"
                raw_pages = json.loads(repaired)
            if not isinstance(raw_pages, list) or not raw_pages:
                raise ValueError("Ungültige Antwortstruktur")
            _insert_pages(lead_id, raw_pages, db, variant=target_variant)
            source = "ai"
        except Exception as exc:
            logger.warning("Sitemap KI-Generierung fehlgeschlagen, Fallback: %s", exc)
            _insert_pages(lead_id, _FALLBACK_PAGES, db, variant=target_variant)

    # Ensure at least one ground page exists regardless of AI/fallback source.
    # Bei variant-Generation übernehmen wir die ground-Page aus primary —
    # wir brauchen sie im Variant-Tab nicht zu duplizieren.
    if not as_variant:
        has_ground = db.query(SitemapPage).filter(
            SitemapPage.lead_id == lead_id,
            SitemapPage.page_type == "ground",
            SitemapPage.variant == "primary",
        ).first()
    else:
        has_ground = True  # skip — primary kümmert sich
    if not has_ground:
        _insert_pages(lead_id, [{
            "page_name": "Über uns & Informationen",
            "page_type": "ground",
            "position": 99,
            "zweck": "Maschinenlesbare Informationsseite für KI-Systeme (GEO-Optimierung)",
            "ziel_keyword": f"{gewerk} {city} Informationen",
            "cta_text": "Jetzt Kontakt aufnehmen",
            "cta_ziel": "kontakt",
            "notizen": "Ground Page — GEO/KI-Optimierung",
        }], db)

    # Sitemap des Ziel-Slots zurückgeben (primary inkl. Pflicht/Bestand,
    # variant nur die KI-Vorschläge der Alternative).
    all_pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.variant == target_variant)
        .order_by(SitemapPage.position)
        .all()
    )
    return {"pages": [_serialize(p) for p in all_pages], "source": source, "variant": target_variant}


@router.post("/{lead_id}/generate-more")
async def generate_more_pages(
    lead_id: int,
    body: dict = Body(default={}),
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Append N additional content pages via Claude AI.

    Im Gegensatz zu /generate werden hier KEINE bestehenden Pages gelöscht.
    Body: {"additional_pages": N}, geclamped auf 1..10. Default 3.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    try:
        n = int((body or {}).get("additional_pages") or 3)
    except (TypeError, ValueError):
        n = 3
    n = max(1, min(10, n))

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="KI-API nicht konfiguriert")

    # generate-more arbeitet nur am primary-Slot — wer Alternativen will, nimmt
    # /generate mit as_variant=true.
    existing = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.variant == "primary")
        .order_by(SitemapPage.position)
        .all()
    )
    existing_summary = "\n".join(f"- {p.page_name} ({p.page_type})" for p in existing) or "(leer)"

    briefing = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    company   = getattr(lead, "company_name", "") or ""
    gewerk    = (getattr(briefing, "gewerk", None) if briefing else None) or getattr(lead, "trade", None) or "Handwerk"
    leistungen = (getattr(briefing, "leistungen", None) if briefing else None) or ""

    prompt = (
        "Du bist ein Website-Stratege für deutsche Handwerksbetriebe.\n"
        f"Schlage GENAU {n} WEITERE Inhaltsseiten für die bestehende Sitemap vor.\n"
        "WICHTIG: KEINE Duplikate zu existierenden Seiten anlegen, KEINE Pflichtseiten "
        "(Impressum, Datenschutz, AGB, Barrierefreiheit) — die werden separat verwaltet.\n\n"
        f"UNTERNEHMEN:\n- Firma: {company}\n- Gewerk: {gewerk}\n- Leistungen: {leistungen}\n\n"
        f"BEREITS BESTEHENDE SEITEN:\n{existing_summary}\n\n"
        "Antworte NUR als JSON-Array (kein Markdown):\n"
        '[{ "page_name":"", "page_type":"leistung|info|vertrauen|conversion|sonstige", '
        '"zweck":"", "ziel_keyword":"", "cta_text":"", "cta_ziel":"kontakt", '
        '"sections":["hero_minimal","content_richtext","cta_inline"] }]'
    )

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key, max_retries=0, timeout=60.0)
        response = await frag_modell(
            client,
            model="claude-sonnet-5", thinking={"type": "disabled"},
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = "\n".join(line for line in raw.splitlines() if not line.strip().startswith("```")).strip()
        new_pages = json.loads(raw)
        if not isinstance(new_pages, list) or not new_pages:
            raise ValueError("Erwarte nicht-leeres JSON-Array")
    except Exception as exc:
        logger.exception("generate-more failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"KI-Generation fehlgeschlagen: {exc}")

    max_pos = max((p.position or 0 for p in existing), default=0)
    for i, p_data in enumerate(new_pages):
        # parent bleibt None (top-level) — KI hat keine IDs zum Verlinken
        p_data["position"] = max_pos + 1 + i
        p_data["parent_id"] = None

    _insert_pages(lead_id, new_pages, db, source="ki_generated", variant="primary")

    all_pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.variant == "primary")
        .order_by(SitemapPage.position)
        .all()
    )
    return {"added": len(new_pages), "pages": [_serialize(p) for p in all_pages]}


@router.get("/{lead_id}/suggest")
def suggest_pages(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Return bedingte Pflichtseiten + optional pages as suggestions for the admin to pick from."""
    existing_names = {
        p.page_name
        for p in db.query(SitemapPage).filter(SitemapPage.lead_id == lead_id).all()
    }

    bedingte = [
        {**s, "bereits_vorhanden": s["page_name"] in existing_names, "kategorie": "bedingt_pflicht"}
        for s in PFLICHTSEITEN_BEDINGT
    ]
    optional = [
        {**s, "bereits_vorhanden": s["page_name"] in existing_names, "kategorie": "optional"}
        for s in OPTIONALE_SEITEN
    ]

    return {"bedingte_pflichtseiten": bedingte, "optionale_seiten": optional}


@router.get("/{lead_id}/ki-empfehlung")
async def ki_seitenempfehlung(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Let Claude generate individual page recommendations based on this customer's briefing."""
    import os, httpx, json as _json

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    briefing   = db.query(Briefing).filter(Briefing.lead_id == lead_id).first()
    existing   = [p.page_name for p in db.query(SitemapPage).filter(SitemapPage.lead_id == lead_id).all()]
    gewerk     = (getattr(briefing, "gewerk",      None) if briefing else None) or (getattr(lead, "trade", None) or "Handwerk")
    leistungen = (getattr(briefing, "leistungen",  None) if briefing else None) or ""
    usp        = (getattr(briefing, "usp",         None) if briefing else None) or ""
    zielgruppe = (getattr(briefing, "zielgruppe",  None) if briefing else None) or ""
    mitbewerber= (getattr(briefing, "mitbewerber", None) if briefing else None) or ""
    city       = getattr(lead, "city", None) or "Deutschland"
    company    = getattr(lead, "company_name", None) or ""

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    prompt = f"""Du bist ein Website-Stratege für Handwerksbetriebe.

KUNDE: {company}
Gewerk: {gewerk}
Stadt: {city}
Leistungen: {leistungen}
USP: {usp}
Zielgruppe: {zielgruppe}
Wettbewerber: {mitbewerber}

Bereits geplante Seiten: {', '.join(existing) or 'keine'}

Empfehle 3-5 spezifische Seiten die für DIESEN Betrieb besonders wichtig sind.
Berücksichtige Gewerk, USP und Zielgruppe — gib individuelle, nicht generische Empfehlungen.

Antworte NUR als JSON-Array:
[{{
  "page_name": "<Seitenname>",
  "page_type": "startseite|leistung|info|vertrauen|conversion|ground",
  "zweck": "<1-2 Sätze warum diese Seite für DIESEN Betrieb wichtig ist>",
  "ziel_keyword": "<Haupt-Keyword>",
  "position": <Zahl>,
  "ki_begruendung": "<Individueller Grund warum genau diese Seite für {company} sinnvoll ist>"
}}]"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-5", "thinking": {"type": "disabled"},
                    "max_tokens": 1500,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        empfehlungen = _json.loads(raw)
        empfehlungen = [e for e in empfehlungen if e.get("page_name") not in existing]
        return {"empfehlungen": empfehlungen, "company": company, "gewerk": gewerk}
    except Exception as e:
        raise HTTPException(500, f"KI-Empfehlung fehlgeschlagen: {str(e)[:200]}")


@router.post("/{lead_id}/add-suggested")
def add_suggested_page(
    lead_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Add a suggested page (bedingt-Pflicht or optional) to the sitemap."""
    page_name = (body.get("page_name") or "").strip()
    if not page_name:
        raise HTTPException(400, "page_name fehlt")

    alle_vorschlaege = PFLICHTSEITEN_BEDINGT + OPTIONALE_SEITEN
    vorlage = next((s for s in alle_vorschlaege if s["page_name"] == page_name), None)
    ist_pflicht = bool(vorlage and vorlage.get("bedingung"))

    db.add(SitemapPage(
        lead_id=lead_id,
        page_name=page_name,
        page_type=body.get("page_type") or (vorlage["page_type"] if vorlage else "info"),
        position=body.get("position") or (vorlage["position"] if vorlage else 50),
        zweck=body.get("zweck") or (vorlage["zweck"] if vorlage else ""),
        ziel_keyword=body.get("ziel_keyword") or (vorlage["ziel_keyword"] if vorlage else ""),
        ist_pflichtseite=ist_pflicht,
        status="geplant",
    ))
    db.commit()
    return {"ok": True, "page_name": page_name}


@router.post("/{lead_id}/promote-variant")
def promote_variant(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Macht aus dem 'variant'-Slot den neuen 'primary'-Slot.

    Schritte:
    1. Alle primary-Pages mit source='ki_generated' und !ist_pflichtseite löschen.
       Bestand (source='crawled') und manuelle Pages bleiben primary, weil
       sie variant-agnostisch sind.
    2. Alle 'variant'-Pages → variant='primary' setzen.
    """
    has_variant = db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.variant == "variant",
    ).first()
    if not has_variant:
        raise HTTPException(status_code=400, detail="Keine Variante zum Übernehmen vorhanden")

    db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.variant == "primary",
        SitemapPage.source == "ki_generated",
        SitemapPage.ist_pflichtseite.is_(False),
    ).delete(synchronize_session=False)

    db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.variant == "variant",
    ).update({SitemapPage.variant: "primary"}, synchronize_session=False)

    db.commit()
    pages = (
        db.query(SitemapPage)
        .filter(SitemapPage.lead_id == lead_id, SitemapPage.variant == "primary")
        .order_by(SitemapPage.position)
        .all()
    )
    return {"promoted": True, "pages": [_serialize(p) for p in pages]}


@router.delete("/{lead_id}/discard-variant", status_code=204)
def discard_variant(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Verwirft alle 'variant'-Pages eines Leads. Primary bleibt unangetastet."""
    db.query(SitemapPage).filter(
        SitemapPage.lead_id == lead_id,
        SitemapPage.variant == "variant",
    ).delete(synchronize_session=False)
    db.commit()


def _insert_pages(
    lead_id: int,
    raw_pages: list,
    db: Session,
    source: str = "ki_generated",
    variant: str = "primary",
) -> list:
    """Persist a list of page dicts, return serialized results.

    `source` is written into sitemap_pages.source. Defaults to 'ki_generated'
    because all current callers are the AI generator (or its fallback). Each
    raw_page may include a `replaces_page_ids` list — if present and non-empty,
    it is JSON-encoded into sitemap_pages.replaces_page_ids (Phase-3 mapping
    of "this AI suggestion replaces these crawled bestand pages").
    `variant` ('primary' | 'variant') determines which slot the pages live in
    — see the R2-Variants doc on the column.
    """
    created = []
    id_map: dict[int, int] = {}  # old position-based index → new DB id (for parent linking)

    for i, p in enumerate(raw_pages):
        sections = _resolve_sections(p)
        replaces_raw = p.get("replaces_page_ids")
        replaces_json: Optional[str] = None
        if isinstance(replaces_raw, list) and replaces_raw:
            cleaned_ids: list[int] = []
            for item in replaces_raw:
                try:
                    cleaned_ids.append(int(item))
                except (TypeError, ValueError):
                    continue
            if cleaned_ids:
                replaces_json = json.dumps(cleaned_ids)
        page = SitemapPage(
            lead_id=lead_id,
            page_name=str(p.get("page_name", "Seite"))[:100],
            page_type=str(p.get("page_type", "info"))[:50],
            position=int(p.get("position", i)),
            parent_id=None,  # resolve after first pass
            zweck=p.get("zweck") or "",
            ziel_keyword=str(p.get("ziel_keyword") or "")[:150],
            cta_text=str(p.get("cta_text") or "")[:100],
            cta_ziel=str(p.get("cta_ziel") or "kontakt")[:50],
            notizen=p.get("notizen") or "",
            status="geplant",
            sections_json=json.dumps(sections, ensure_ascii=False),
            source=source,
            replaces_page_ids=replaces_json,
            variant=variant,
        )
        db.add(page)
        db.flush()  # get page.id
        id_map[i] = page.id
        created.append((page, p.get("parent_id")))

    # Second pass: resolve parent_id references
    for page, raw_parent in created:
        if isinstance(raw_parent, int) and raw_parent in id_map:
            page.parent_id = id_map[raw_parent]

    db.commit()
    for page, _ in created:
        db.refresh(page)
    return [_serialize(page) for page, _ in created]


def _resolve_sections(page_dict: dict) -> list[str]:
    """Pick a section list from the AI output, falling back to the page-type default.
    Filters unknown keys against SECTION_CATALOG so we never persist garbage."""
    raw = page_dict.get("sections")
    if isinstance(raw, list) and raw:
        cleaned = [str(s) for s in raw if isinstance(s, str) and s in SECTION_CATALOG]
        if cleaned:
            return cleaned
    page_type = str(page_dict.get("page_type") or "info")
    return DEFAULT_SECTIONS_BY_PAGETYPE.get(page_type, DEFAULT_SECTIONS_BY_PAGETYPE["info"])
