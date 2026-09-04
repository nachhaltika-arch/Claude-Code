"""Die Content-Werkstatt: Texte fuer die Seiten erzeugen (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/projects_sichtbarkeit.py` hatte
1.038 Zeilen und darin zwei Dinge: die **Sichtbarkeit** (KI-Bericht,
Ground-Page, Schema-Daten) und die **Werkstatt**, in der die Texte der
einzelnen Seiten entstehen. Drei Funktionen, zusammen 392 Zeilen — die
groesste erzeugt alle Seiten eines Projekts auf einmal.

Der Router kommt aus `projects_router.py`, wo die drei Router mit ihren
verschiedenen Sperren an einer Stelle stehen.
"""
import os
from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import Project, SessionLocal, get_db
from routers.auth_router import get_current_user, require_any_auth
from routers.projects_router import router
import logging

logger = logging.getLogger(__name__)


@router.post("/{project_id}/content-workshop/generate-all")
async def generate_all_pages_content(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generiert KI-Content für ALLE Sitemap-Seiten in einem einzigen Claude-API-Call."""
    import json, re
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


# **Hier stand `POST /{project_id}/briefing-prefill`** — 98 Zeilen,
# entfernt am 01.09.2026 beim Durchgehen der Endpunkte ohne Aufrufer
# (L-105). Es war ein **Doppelweg**: Das Frontend ruft seit jeher
# `POST /api/leads/{lead_id}/briefing-prefill`, und der Kopf von
# `routers/leads_briefing.py` sagt ausdruecklich, die Adresse „soll es
# bleiben". Diese zweite Fassung hat das nie mitbekommen.
