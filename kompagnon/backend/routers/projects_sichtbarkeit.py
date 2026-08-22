"""Sichtbarkeit nach dem Go-live — Bewertungen, Google-Eintrag, Ground Page.

**Was hier liegt (L-25, Etappe 4, 22.08.2026).** Der Bewertungs-QR-Code, die
Checkliste fuer den Google-Unternehmenseintrag und die Ground Page. Alles
drei wirkt **nach** der Uebergabe: Es sorgt dafuer, dass der Betrieb gefunden
wird und Bewertungen bekommt — waehrend `projects_content.py` daneben die
Seite selbst herstellt. Zwei verschiedene Zeitpunkte im Projekt, und deshalb
zwei Dateien.

**Reiner Umzug.** Keine Logik, kein Pfad, keine Signatur geaendert; der Router
kommt aus `projects_router.py`. Gegengeprueft mit
`tools/endpunkte_auflisten.py`.
"""
import logging
import os

from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Project, SessionLocal, get_db
from routers.auth_router import get_current_user, require_any_auth
from routers.projects_router import router

logger = logging.getLogger(__name__)


# ── Bewertungs-QR-Code & GBP-Checkliste ──────────────────────────────────────

@router.get("/{project_id}/bewertungs-qrcode")
def get_bewertungs_qrcode(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from fastapi.responses import Response
    import io

    row = db.execute(text("""
        SELECT l.gbp_place_id, l.company_name
        FROM projects p
        LEFT JOIN leads l ON l.id = p.lead_id
        WHERE p.id = :id
    """), {"id": project_id}).fetchone()

    if not row:
        raise HTTPException(404, "Projekt nicht gefunden")

    place_id = row[0]
    if not place_id:
        raise HTTPException(
            422,
            "Kein Google Business Profil verknüpft. "
            "Bitte zuerst GBP-Check in der Nutzerkartei durchführen.",
        )

    review_url = f"https://search.google.com/local/writereview?placeid={place_id}"

    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=3,
    )
    qr.add_data(review_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0F1E3A", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return Response(
        content=buf.read(),
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="bewertungs-qr-{project_id}.png"',
            "X-Review-URL": review_url,
        },
    )


@router.get("/{project_id}/bewertungs-url")
def get_bewertungs_url(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.execute(text("""
        SELECT l.gbp_place_id, l.gbp_rating, l.gbp_ratings_total,
               l.company_name
        FROM projects p
        LEFT JOIN leads l ON l.id = p.lead_id
        WHERE p.id = :id
    """), {"id": project_id}).fetchone()

    if not row:
        raise HTTPException(404, "Nicht gefunden")

    place_id = row[0]
    if not place_id:
        return {"available": False, "review_url": None, "place_id": None}

    return {
        "available":     True,
        "review_url":    f"https://search.google.com/local/writereview?placeid={place_id}",
        "place_id":      place_id,
        "rating":        row[1],
        "ratings_total": row[2],
        "company_name":  row[3],
    }


@router.patch("/{project_id}/gbp-checklist")
def save_gbp_checklist(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    checked = data.get("checked", {})
    db.execute(
        text("UPDATE projects SET gbp_checklist_json=:gj WHERE id=:id"),
        {"gj": json.dumps(checked, ensure_ascii=False), "id": project_id},
    )
    db.commit()
    return {"success": True}


@router.post("/{project_id}/ki-report")
async def generate_ki_report(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """
    Sammelt alle Onboarding-Daten und lässt Claude einen strukturierten
    Report mit Lückenanalyse erstellen.
    """
    import httpx, json, re

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead_id = project.lead_id
    if not lead_id:
        raise HTTPException(400, "Kein Lead verknüpft")

    # ── Alle verfügbaren Onboarding-Daten sammeln ──
    data_parts = []

    # 1. Lead-Basisdaten
    lead = db.execute(
        text("""
            SELECT company_name, website_url, email, phone, city,
                   trade, wz_code, wz_title, brand_primary_color,
                   brand_secondary_color, brand_font_primary, brand_design_style
            FROM leads WHERE id = :lid
        """),
        {"lid": lead_id},
    ).fetchone()
    if lead:
        data_parts.append(f"""## Unternehmensdaten
Firma: {lead.company_name or '–'}
Website: {lead.website_url or '–'}
E-Mail: {lead.email or '–'}
Telefon: {lead.phone or '–'}
Stadt: {lead.city or '–'}
Gewerk: {lead.trade or '–'}
WZ-Code: {lead.wz_code or '–'} — {lead.wz_title or '–'}
Primärfarbe: {lead.brand_primary_color or '–'}
Sekundärfarbe: {lead.brand_secondary_color or '–'}
Schriftart: {lead.brand_font_primary or '–'}
Designstil: {lead.brand_design_style or '–'}""")

    # 2. Briefing-Daten
    briefing = db.execute(
        text("""
            SELECT gewerk, leistungen, einzugsgebiet, zielgruppe,
                   usp, mitbewerber, wunschseiten, farben, stil,
                   sonstige_hinweise, logo_vorhanden, fotos_vorhanden
            FROM briefings WHERE lead_id = :lid
            ORDER BY id DESC LIMIT 1
        """),
        {"lid": lead_id},
    ).fetchone()
    if briefing:
        data_parts.append(f"""## Briefing-Daten
Gewerk: {briefing.gewerk or '–'}
Leistungen: {briefing.leistungen or '–'}
Einzugsgebiet: {briefing.einzugsgebiet or '–'}
Zielgruppe: {briefing.zielgruppe or '–'}
USP: {briefing.usp or '–'}
Mitbewerber: {briefing.mitbewerber or '–'}
Wunschseiten: {briefing.wunschseiten or '–'}
Farben: {briefing.farben or '–'}
Stil: {briefing.stil or '–'}
Sonstige Hinweise: {briefing.sonstige_hinweise or '–'}
Logo vorhanden: {'Ja' if briefing.logo_vorhanden else 'Nein'}
Fotos vorhanden: {'Ja' if briefing.fotos_vorhanden else 'Nein'}""")

    # 3. Letzter Audit (Tabelle: audit_results)
    try:
        audit = db.execute(
            text("""
                SELECT total_score, ai_summary
                FROM audit_results WHERE lead_id = :lid
                ORDER BY created_at DESC LIMIT 1
            """),
            {"lid": lead_id},
        ).fetchone()
        if audit:
            data_parts.append(f"""## Audit
Score: {audit[0] or '–'}/100
Zusammenfassung: {audit[1] or '–'}""")
    except Exception:
        pass

    # 4. PageSpeed (aus leads-Tabelle, nicht separate Tabelle)
    try:
        ps = db.execute(
            text("SELECT pagespeed_mobile_score, pagespeed_desktop_score FROM leads WHERE id = :lid"),
            {"lid": lead_id},
        ).fetchone()
        if ps and (ps[0] or ps[1]):
            data_parts.append(f"""## PageSpeed
Mobil: {ps[0] or '–'}/100
Desktop: {ps[1] or '–'}/100""")
    except Exception:
        pass

    # 5. Crawler (Tabelle: crawl_results, Spalte: customer_id)
    try:
        crawler_count = db.execute(
            text("SELECT COUNT(*) FROM crawl_results WHERE customer_id = :lid"),
            {"lid": lead_id},
        ).scalar()
        if crawler_count:
            data_parts.append(f"## Crawler\nGecrawlte Seiten: {crawler_count}")
    except Exception:
        pass

    # 6. Sitemap-Seiten
    sitemap_pages = db.execute(
        text("SELECT page_name, page_type, ziel_keyword FROM sitemap_pages WHERE lead_id = :lid AND ist_pflichtseite = false ORDER BY position"),
        {"lid": lead_id},
    ).fetchall()
    if sitemap_pages:
        seiten_text = "\n".join([
            f"- {p.page_name} ({p.page_type}){' → ' + p.ziel_keyword if p.ziel_keyword else ''}"
            for p in sitemap_pages
        ])
        data_parts.append(f"## Geplante Seiten (Sitemap)\n{seiten_text}")

    if not data_parts:
        raise HTTPException(400, "Keine Onboarding-Daten vorhanden. Bitte zuerst Audit, Briefing und Crawler ausführen.")

    all_data = "\n\n".join(data_parts)

    # DB-Verbindung vor externem API-Call freigeben
    db.close()

    # ── KI-Analyse via Claude ──
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    prompt = f"""Du bist ein Website-Stratege bei KOMPAGNON. Analysiere die folgenden Onboarding-Daten eines Kunden und erstelle einen strukturierten Report.

{all_data}

Erstelle einen JSON-Report mit GENAU dieser Struktur (nur JSON, kein Markdown):
{{
  "completeness_score": <0-100, wie vollständig sind die Daten>,
  "data_points_count": <Anzahl vorhandener Datenpunkte>,
  "gaps_count": <Anzahl fehlender wichtiger Informationen>,
  "summary": "<3-5 Sätze: Wer ist der Kunde, was macht er, wo steht er>",
  "available_data": [
    "<Was vorhanden ist, z.B. 'Briefing mit USP und Zielgruppe'>",
    "<weiterer Punkt>"
  ],
  "gaps": [
    {{
      "field": "<Name des fehlenden Feldes, z.B. 'Fotos/Bildmaterial'>",
      "impact": "<Warum das fehlt ist ein Problem für die Content-Erstellung>",
      "action": "<Was konkret getan werden kann>"
    }}
  ],
  "recommendation": "<1-2 Sätze: Kann man jetzt mit Content-Erstellung beginnen oder was fehlt noch>",
  "content_brief": "<Kompakter Steckbrief in 10-15 Zeilen für die spätere Content-KI: Firma, Gewerk, USP, Zielgruppe, Leistungen, Keyword-Fokus, Tonalität>"
}}"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-5", "thinking": {"type": "disabled"},
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        content = resp.json()["content"][0]["text"].strip()

        # JSON parsen — eventuelle Markdown-Backticks entfernen
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        report_data = json.loads(content)

        return report_data

    except Exception as e:
        raise HTTPException(500, f"KI-Report fehlgeschlagen: {str(e)[:200]}")


@router.post("/{project_id}/moodboard")
async def save_moodboard(
    project_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Speichert die Moodboard-Auswahl zum Projekt."""
    import json as _json
    db.execute(
        text("""
            UPDATE projects SET
              moodboard_data = :data,
              moodboard_updated_at = NOW()
            WHERE id = :id
        """),
        {"data": _json.dumps(body, ensure_ascii=False), "id": project_id},
    )
    db.commit()
    return {"ok": True}


@router.post("/{project_id}/moodboard/preview")
async def generate_moodboard_preview(
    project_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Lässt Claude eine Moodboard-Beschreibung + Farbpalette generieren."""
    import httpx, json, re

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    # DB-Verbindung vor externem Call freigeben
    db.close()

    stilrichtung = body.get("stilrichtung", "")
    farbstimmung = body.get("farbstimmung", "")
    typografie   = body.get("typografie", "")
    bildsprache  = body.get("bildsprache", [])
    notizen      = body.get("notizen", "")

    prompt = f"""Du bist ein Website-Designer für Handwerksbetriebe. Erstelle auf Basis dieser Moodboard-Auswahl eine konkrete Designbeschreibung und Farbpalette.

Stilrichtung: {stilrichtung}
Farbstimmung: {farbstimmung}
Typografie: {typografie}
Bildsprache: {', '.join(bildsprache) if bildsprache else 'nicht festgelegt'}
Besondere Wünsche: {notizen or 'keine'}

Antworte NUR mit diesem JSON (kein Markdown, keine Erklärungen):
{{
  "description": "<3-4 Sätze: Wie wird die Website aussehen, welche Atmosphäre entsteht, was macht sie besonders>",
  "color_palette": [
    {{"hex": "#FARBCODE", "role": "Primärfarbe"}},
    {{"hex": "#FARBCODE", "role": "Sekundärfarbe"}},
    {{"hex": "#FARBCODE", "role": "Akzentfarbe"}},
    {{"hex": "#FARBCODE", "role": "Hintergrund"}},
    {{"hex": "#FARBCODE", "role": "Text"}}
  ]
}}"""

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
                    "max_tokens": 600,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        content = resp.json()["content"][0]["text"].strip()
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        return json.loads(content)
    except Exception as e:
        raise HTTPException(500, f"Preview-Generierung fehlgeschlagen: {str(e)[:200]}")


@router.post("/{project_id}/briefing-prefill")
async def briefing_prefill_from_content(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Analysiert gecrawlten Website-Content und gibt Briefing-Vorschläge zurück."""
    import os, httpx, json, re
    from urllib.parse import urlparse

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    lead_id = project.lead_id
    if not lead_id:
        raise HTTPException(400, "Kein Lead verknüpft")

    rows = db.execute(
        text("""
            SELECT url, title, meta_description, h1, h2s, text_preview
            FROM website_content_cache
            WHERE customer_id = :lid ORDER BY scraped_at DESC LIMIT 20
        """),
        {"lid": lead_id},
    ).fetchall()

    if not rows:
        raise HTTPException(400, "Kein Website-Content vorhanden. Bitte zuerst Crawler + Content-Scraping ausführen.")

    # Kontaktdaten
    try:
        contact = db.execute(
            text("SELECT contact_phone, contact_email, contact_address FROM project_scraped_pages WHERE project_id = :pid LIMIT 1"),
            {"pid": project_id},
        ).fetchone()
    except Exception:
        contact = None

    pages_text = []
    all_h2s = []
    all_titles = []
    page_names = []

    for row in rows:
        url, title, meta, h1, h2s_json, preview = row
        all_titles.append(title or h1 or '')
        try:
            h2s = json.loads(h2s_json or '[]')
            all_h2s.extend(h2s)
        except Exception:
            pass
        if preview:
            pages_text.append(f"URL: {url}\nH1: {h1 or title}\nVorschau: {preview[:400]}")
        try:
            path = urlparse(url).path.strip('/').split('/')[-1]
            if path and len(path) > 1:
                name = path.replace('-', ' ').replace('_', ' ').title()
                if name not in page_names:
                    page_names.append(name)
        except Exception:
            pass

    wunschseiten = ', '.join(page_names[:8])

    def heuristic():
        return {
            "gewerk": (all_titles[0] if all_titles else '')[:80],
            "leistungen": '\n'.join(set(all_h2s[:10])),
            "einzugsgebiet": (contact[2] if contact and contact[2] else ''),
            "wunschseiten": wunschseiten,
            "source": "heuristic",
        }

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return heuristic()

    content_summary = "\n---\n".join(pages_text[:8])
    prompt = f"""Analysiere diesen Website-Content eines Handwerksbetriebs.
{content_summary}

Gib NUR JSON zurück:
{{"gewerk":"<max 60 Zeichen>","leistungen":"<kommagetrennt, max 300>","einzugsgebiet":"<Stadt/Region>","usp":"<max 200>","wunschseiten":"{wunschseiten}","zielgruppe":"Privatkunden|Gewerbekunden|Beides"}}"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-5", "thinking": {"type": "disabled"}, "max_tokens": 600, "messages": [{"role": "user", "content": prompt}]},
            )
        resp.raise_for_status()
        txt = resp.json()["content"][0]["text"].strip()
        txt = re.sub(r'^```json\s*', '', txt)
        txt = re.sub(r'\s*```$', '', txt)
        result = json.loads(txt)
        result["source"] = "claude"
        return result
    except Exception:
        return heuristic()


@router.post("/{project_id}/content-workshop/generate-all")
async def generate_all_pages_content(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generiert KI-Content für ALLE Sitemap-Seiten in einem einzigen Claude-API-Call."""
    import os, json, re
    import httpx as _httpx

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead    = project.lead
    lead_id = project.lead_id

    pages = db.execute(
        text("""
            SELECT id, page_name, page_type, ziel_keyword, zweck
            FROM sitemap_pages
            WHERE lead_id = :lid
            ORDER BY position
        """),
        {"lid": lead_id},
    ).fetchall()

    if not pages:
        raise HTTPException(400, "Keine Sitemap-Seiten gefunden. Zuerst Sitemap anlegen.")

    briefing = db.execute(
        text("SELECT gewerk, leistungen, einzugsgebiet, usp, zielgruppe FROM briefings WHERE lead_id = :lid LIMIT 1"),
        {"lid": lead_id},
    ).fetchone()

    brand_json = getattr(lead, "brand_design_json", None)
    brand = json.loads(brand_json) if brand_json else {}

    crawled_rows = db.execute(
        text("""
            SELECT url, h1, text_preview
            FROM website_content_cache
            WHERE customer_id = :lid
            ORDER BY scraped_at DESC
            LIMIT 20
        """),
        {"lid": lead_id},
    ).fetchall()
    crawled_summary = "\n".join(
        [f"- {r[1] or r[0]}: {(r[2] or '')[:200]}" for r in crawled_rows[:8]]
    ) or "Kein gecrawlter Content vorhanden."

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    gewerk     = briefing[0] if briefing else "Handwerksbetrieb"
    leistungen = briefing[1] if briefing else ""
    region     = briefing[2] if briefing else ""
    usp        = briefing[3] if briefing else ""
    zielgruppe = briefing[4] if briefing else "Privatkunden"
    company    = getattr(lead, "company_name", "") or ""
    phone      = getattr(lead, "phone", "") or ""

    pages_for_prompt = [
        {"id": p[0], "name": p[1], "type": p[2], "keyword": p[3] or "", "zweck": p[4] or ""}
        for p in pages
    ]
    pages_json_str = json.dumps(pages_for_prompt, ensure_ascii=False, indent=2)

    prompt = f"""Du bist ein professioneller Werbetexter für deutsche Handwerksbetriebe.

UNTERNEHMEN:
- Firma: {company}
- Branche/Gewerk: {gewerk}
- Leistungen: {leistungen}
- Region: {region}
- USP: {usp}
- Telefon: {phone}
- Zielgruppe: {zielgruppe}
- Design-Stil: {brand.get("style_keyword", "Modern & professionell")}

BESTEHENDE WEBSITE (gecrawlt):
{crawled_summary}

Schreibe jetzt für JEDE der folgenden Seiten professionelle deutsche Texte.
Ton: direkt, vertrauenswürdig, keine Floskeln. Regional konkret. Immer den USP einbauen.

SEITEN:
{pages_json_str}

Antworte NUR mit einem JSON-Array. Ein Objekt pro Seite:
[
  {{
    "page_id": <int, die id aus der Seiten-Liste>,
    "h1": "<Hauptüberschrift, max 70 Zeichen, enthält Gewerk + Region>",
    "hero_text": "<Hero-Fliesstext, 2-3 Sätze, Nutzen für den Kunden>",
    "abschnitt_text": "<Haupttext der Seite, 3-5 Sätze, ausführlicher>",
    "cta": "<Call-to-Action Text, max 40 Zeichen, aktiv formuliert>",
    "meta_title": "<SEO-Title, max 60 Zeichen, Keyword + Firmenname>",
    "meta_description": "<SEO-Description, max 155 Zeichen, Nutzen + CTA>"
  }}
]

Nur JSON, kein Markdown, keine Erklärungen."""

    db.close()

    try:
        async with _httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-5", "thinking": {"type": "disabled"},
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        results = json.loads(raw)
    except Exception as e:
        raise HTTPException(500, f"KI-Generierung fehlgeschlagen: {str(e)[:200]}")

    db2 = SessionLocal()
    saved = []
    try:
        for item in results:
            page_id = item.get("page_id")
            if not page_id:
                continue
            db2.execute(
                text("""
                    UPDATE sitemap_pages SET
                        ki_h1               = :h1,
                        ki_hero_text        = :hero,
                        ki_abschnitt_text   = :abschnitt,
                        ki_cta              = :cta,
                        ki_meta_title       = :meta_title,
                        ki_meta_description = :meta_desc,
                        content_generated   = true,
                        content_generated_at = NOW()
                    WHERE id = :pid
                """),
                {
                    "h1":         item.get("h1", ""),
                    "hero":       item.get("hero_text", ""),
                    "abschnitt":  item.get("abschnitt_text", ""),
                    "cta":        item.get("cta", ""),
                    "meta_title": item.get("meta_title", ""),
                    "meta_desc":  item.get("meta_description", ""),
                    "pid":        page_id,
                },
            )
            saved.append(page_id)
        db2.commit()
    except Exception as e:
        db2.rollback()
        raise HTTPException(500, f"DB-Speichern fehlgeschlagen: {str(e)[:200]}")
    finally:
        db2.close()

    return {
        "success": True,
        "pages_generated": len(saved),
        "page_ids": saved,
        "results": results,
    }


@router.post("/{project_id}/content-workshop/{page_id}")
async def generate_page_content(
    project_id: int,
    page_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generiert KI-Content fuer eine Sitemap-Seite basierend auf Crawler-Daten + Briefing."""
    import os, httpx, json, re

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    # Tor 1: Briefing muss vom Kunden freigegeben sein
    if not getattr(project, "briefing_approved_at", None):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "BRIEFING_NOT_APPROVED",
                "message": "Das Briefing wurde noch nicht vom Kunden freigegeben. Bitte zuerst eine Freigabe-E-Mail senden.",
            },
        )

    lead_id = project.lead_id

    page = db.execute(
        text("SELECT page_name, page_type, ziel_keyword, zweck FROM sitemap_pages WHERE id = :id"),
        {"id": page_id},
    ).fetchone()
    if not page:
        raise HTTPException(404, "Seite nicht gefunden")

    page_name, page_type, keyword, zweck = page

    briefing = db.execute(
        text("SELECT gewerk, leistungen, einzugsgebiet, usp, zielgruppe FROM briefings WHERE lead_id = :lid LIMIT 1"),
        {"lid": lead_id},
    ).fetchone()

    crawled = db.execute(
        text(
            "SELECT url, h1, h2s, text_preview, full_text "
            "FROM website_content_cache "
            "WHERE customer_id = :lid "
            "AND (url ILIKE :name OR h1 ILIKE :name OR title ILIKE :name) "
            "ORDER BY scraped_at DESC LIMIT 1"
        ),
        {"lid": lead_id, "name": f"%{page_name.lower().replace(' ', '%')}%"},
    ).fetchone()

    old_content = ""
    if crawled:
        old_content = f"URL: {crawled[0]}\nH1: {crawled[1]}\n"
        try:
            h2s = json.loads(crawled[2] or '[]')
            if h2s:
                old_content += "H2: " + " | ".join(h2s[:5]) + "\n"
        except Exception:
            pass
        old_content += f"Text: {(crawled[4] or crawled[3] or '')[:1500]}"

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    gewerk     = briefing[0] if briefing else "Handwerksbetrieb"
    leistungen = briefing[1] if briefing else ""
    region     = briefing[2] if briefing else ""
    usp        = briefing[3] if briefing else ""
    zielgruppe = briefing[4] if briefing else "Privatkunden"

    old_section = f"\nBestehender Content:\n{old_content}" if old_content else "\nKein bestehender Content — komplett neu schreiben."

    prompt = (
        f"Du bist ein professioneller Webtexter fuer lokale Unternehmen.\n"
        f"Schreibe den Content fuer die Seite \"{page_name}\" ({page_type}).\n\n"
        f"Unternehmen: {gewerk}\nLeistungen: {leistungen}\nRegion: {region}\nUSP: {usp}\nZielgruppe: {zielgruppe}\n"
        f"Seite: {page_name}\nZweck: {zweck or 'Informieren und ueberzeugen'}\nKeyword: {keyword or 'nicht definiert'}\n"
        f"{old_section}\n\n"
        "Antworte NUR als JSON:\n"
        '{"headline":"<H1 max 60 Zeichen>","subheadline":"<max 100 Zeichen>","intro":"<2-3 Saetze>",'
        '"sections":[{"titel":"<H2>","text":"<3-5 Saetze>"}],'
        '"cta":"<Call-to-Action>","meta_title":"<max 60>","meta_description":"<max 155>"}'
    )

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-5", "thinking": {"type": "disabled"}, "max_tokens": 3000, "messages": [{"role": "user", "content": prompt}]},
            )
        resp.raise_for_status()
        raw_text = resp.json()["content"][0]["text"].strip()
        raw_text = re.sub(r'^```json\s*', '', raw_text)
        raw_text = re.sub(r'\s*```$', '', raw_text)
        # JSON repair for truncated responses
        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError:
            repaired = raw_text.rstrip().rstrip(",")
            if repaired.count('"') % 2 != 0:
                repaired += '"'
            open_brackets = repaired.count('[') - repaired.count(']')
            repaired += ']' * max(0, open_brackets)
            open_braces = repaired.count('{') - repaired.count('}')
            repaired += '}' * max(0, open_braces)
            result = json.loads(repaired)
        result["old_content"] = old_content
        result["page_name"] = page_name
        result["page_id"] = page_id
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(500, f"KI-Antwort nicht parsebar: {str(e)[:100]}")
    except Exception as e:
        raise HTTPException(500, f"Content-Generierung fehlgeschlagen: {str(e)[:200]}")


# ── Ground Page ────────────────────────────────────────────────────────────────

def _build_schema_jsonld(data: dict, company: str, city: str, website: str,
                          phone: str, rating: str, rating_count: str,
                          founded: str, employees: str, leistungen: str) -> dict:
    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": company,
        "url": website or "",
        "telephone": phone or "",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": city,
            "addressCountry": "DE",
        },
        "description": data.get("meta_description", ""),
    }
    if rating and rating != "—":
        try:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(rating),
                "reviewCount": str(rating_count or "0"),
            }
        except Exception:
            pass
    if founded and founded != "—":
        schema["foundingDate"] = str(founded)
    if employees and employees != "—":
        schema["numberOfEmployees"] = str(employees)
    services = [s.strip() for s in (leistungen or "").split(",") if s.strip()]
    if services:
        schema["hasOfferCatalog"] = {
            "@type": "OfferCatalog",
            "name": "Leistungen",
            "itemListElement": services[:10],
        }
    faq_items = data.get("faq", [])
    if faq_items:
        schema["mainEntity"] = [
            {
                "@type": "Question",
                "name": item["frage"],
                "acceptedAnswer": {"@type": "Answer", "text": item["antwort"]},
            }
            for item in faq_items
        ]
    return schema


@router.post("/{project_id}/ground-page")
async def generate_ground_page(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generiert eine Ground Page für GEO/KI-Optimierung (Fakten, Keywords, FAQ, Schema.org)."""
    import os, httpx, json, re

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead    = project.lead
    lead_id = project.lead_id

    briefing = db.execute(
        text("""
            SELECT gewerk, leistungen, einzugsgebiet, usp,
                   zielgruppe, hauptziel, aktionen,
                   telefon, email, gruendungsjahr,
                   mitarbeiterzahl, google_bewertung,
                   google_bewertung_anzahl, zertifikate,
                   auszeichnungen, sonstige_hinweise
            FROM briefings WHERE lead_id = :lid LIMIT 1
        """),
        {"lid": lead_id},
    ).fetchone()

    company    = getattr(lead, 'company_name', '') or ''
    city       = getattr(lead, 'city', '') or ''
    website    = getattr(lead, 'website_url', '') or ''
    phone      = getattr(lead, 'phone', '') or ''

    gewerk         = (briefing[0]  if briefing else '') or ''
    leistungen     = (briefing[1]  if briefing else '') or ''
    einzugsgebiet  = (briefing[2]  if briefing else city) or city
    usp            = (briefing[3]  if briefing else '') or ''
    zielgruppe     = (briefing[4]  if briefing else 'Privatkunden') or 'Privatkunden'
    hauptziel      = (briefing[5]  if briefing else '') or ''
    telefon_b      = (briefing[7]  if briefing else phone) or phone
    gruendungsjahr = (briefing[9]  if briefing else '') or ''
    mitarbeiter    = (briefing[10] if briefing else '') or ''
    g_bewertung    = (briefing[11] if briefing else '') or ''
    g_anzahl       = (briefing[12] if briefing else '') or ''
    zertifikate    = (briefing[13] if briefing else '') or ''
    auszeichnungen = (briefing[14] if briefing else '') or ''
    hinweise       = (briefing[15] if briefing else '') or ''

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    prompt = f"""Du erstellst eine Ground Page für ein Handwerksunternehmen.
Eine Ground Page ist eine maschinenlesbare Seite für KI-Systeme (ChatGPT, Perplexity, Google AI).
Sie soll das Unternehmen bei relevanten KI-Suchanfragen empfehlenswert machen.

UNTERNEHMENSDATEN:
- Name: {company}
- Branche/Gewerk: {gewerk}
- Stadt: {city}
- Einzugsgebiet: {einzugsgebiet}
- Website: {website}
- Telefon: {telefon_b or phone}
- Gegründet: {gruendungsjahr or '—'}
- Mitarbeiter: {mitarbeiter or '—'}
- Google-Bewertung: {g_bewertung or '—'} ({g_anzahl or '—'} Bewertungen)
- Zertifikate: {zertifikate or '—'}
- Auszeichnungen: {auszeichnungen or '—'}
- Leistungen: {leistungen}
- USP: {usp}
- Zielgruppe: {zielgruppe}
- Hauptziel: {hauptziel}
- Hinweise: {hinweise}

AUFGABE: Erstelle NUR gültiges JSON mit GENAU dieser Struktur:

{{
  "page_title": "Über uns & Informationen — {company}",
  "meta_description": "<155 Zeichen: Wer wir sind, was wir anbieten, wo wir sind>",
  "intro": "<2-3 Sätze Einleitung, direkt und informativ für KI-Systeme>",
  "fakten": {{
    "name": "{company}",
    "branche": "<Gewerk>",
    "standort": "<Stadt, Bundesland, Deutschland>",
    "einzugsgebiet": "<Region mit Städten>",
    "gegruendet": "<Jahr oder —>",
    "mitarbeiter": "<Zahl oder —>",
    "telefon": "<Telefon>",
    "website": "<URL>",
    "notdienst": "<Ja 24/7 / Ja Mo-Fr / Nein>",
    "sprachen": "Deutsch"
  }},
  "leistungen_keywords": [
    "<Leistung + Stadt, z.B. Wallbox installieren München>",
    "<weitere 7-9 GEO-optimierte Leistungs-Keywords>"
  ],
  "usp_saetze": [
    "<USP 1 als vollständiger Satz für KI-Verständnis>",
    "<USP 2>",
    "<USP 3>"
  ],
  "faq": [
    {{"frage": "<Frage genau wie Nutzer sie in ChatGPT eintippen würden>", "antwort": "<Direkte informative Antwort mit Firmenname und Kontakt>"}},
    {{"frage": "<Frage 2>", "antwort": "<Antwort 2>"}},
    {{"frage": "<Frage 3>", "antwort": "<Antwort 3>"}},
    {{"frage": "<Frage 4>", "antwort": "<Antwort 4>"}},
    {{"frage": "<Frage 5>", "antwort": "<Antwort 5>"}}
  ],
  "vertrauen": {{
    "google_bewertung": "{g_bewertung or '—'}",
    "google_anzahl": "{g_anzahl or '—'}",
    "zertifikate": "<Zertifikate aufgelistet oder —>",
    "auszeichnungen": "<Auszeichnungen aufgelistet oder —>",
    "seit": "<Gründungsjahr oder —>",
    "projekte": "<Geschätzte Projektanzahl falls ableitbar, sonst —>"
  }},
  "schema_type": "LocalBusiness",
  "letzte_aktualisierung": "2026-04"
}}

Gib NUR das JSON zurück, keine Erklärung, kein Markdown."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-5", "thinking": {"type": "disabled"},
                    "max_tokens": 3000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        ground_data = json.loads(raw)

        ground_data["schema_jsonld"] = _build_schema_jsonld(
            ground_data, company, city, website,
            telefon_b or phone, g_bewertung, g_anzahl,
            gruendungsjahr, mitarbeiter, leistungen,
        )

        # Persist to website_content of the ground sitemap page
        ground_page = db.execute(
            text("SELECT id FROM sitemap_pages WHERE lead_id = :lid AND page_type = 'ground' LIMIT 1"),
            {"lid": lead_id},
        ).fetchone()
        if ground_page:
            db.execute(
                text("""
                    INSERT INTO website_content (sitemap_page_id, ki_content, content_generated, updated_at)
                    VALUES (:pid, :content, TRUE, NOW())
                    ON CONFLICT (sitemap_page_id)
                    DO UPDATE SET ki_content = EXCLUDED.ki_content,
                                  content_generated = TRUE,
                                  updated_at = NOW()
                """),
                {"pid": ground_page[0], "content": json.dumps(ground_data, ensure_ascii=False)},
            )
            db.commit()

        return {"ok": True, "ground_page": ground_data}

    except json.JSONDecodeError:
        raise HTTPException(500, "KI-Antwort konnte nicht verarbeitet werden")
    except Exception as e:
        raise HTTPException(500, f"Ground Page Generierung fehlgeschlagen: {str(e)[:300]}")
