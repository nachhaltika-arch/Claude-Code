"""Was ohne Anmeldung erreichbar ist — und der Link-Resolver.

**Warum diese acht eine eigene Datei bekommen (L-25, Etappe 3, 22.08.2026).**
Nicht wegen ihrer Zeilenzahl, sondern wegen ihres **Zugriffsverhaltens**: Der
`public_router` traegt bewusst keine Sperre. Die Freigabe des Kunden kommt
ueber einen Link aus der E-Mail; der Token **ist** der Nachweis, und die
Routen pruefen ihn selbst.

Genau solche Stellen gehen in einer Datei mit tausenden Zeilen unter. Am
19.08. sind 55 Werkzeug-Routen ohne Anmeldung gefunden worden (L-51), am
21.08. dreizehn Projektrouten, die jeden Angemeldeten an jedes Projekt
liessen (L-69). Wer hier etwas hinzufuegt, sieht am Dateikopf, worauf er sich
einlaesst — das ist der eigentliche Zweck dieser Trennung.

**Reiner Umzug.** Keine Logik, kein Pfad, keine Sperre geaendert. Die Router
kommen aus `projects_router.py`; gegengeprueft mit
`tools/endpunkte_auflisten.py`.
"""
import logging

from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Project, get_db
from routers.auth_router import require_any_auth
from routers.projects_router import public_router, router

logger = logging.getLogger(__name__)


# ── Link-Resolver ─────────────────────────────────────────────────────────────

import re as _re

def _make_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = slug.replace('ae', 'ae').replace('oe', 'oe').replace('ue', 'ue').replace('ss', 'ss')
    slug = _re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    SLUG_MAP = {
        'startseite': '', 'home': '', 'impressum': 'impressum',
        'datenschutz': 'datenschutz', 'datenschutzerklaerung': 'datenschutz',
        'agb': 'agb', 'kontakt': 'kontakt', 'contact': 'kontakt',
        'ueber-uns': 'ueber-uns', 'uber-uns': 'ueber-uns', 'about': 'ueber-uns',
        'leistungen': 'leistungen', 'services': 'leistungen',
        'referenzen': 'referenzen', 'galerie': 'galerie',
        'blog': 'blog', 'news': 'news', 'karriere': 'karriere',
        'jobs': 'karriere', 'stellenangebote': 'karriere',
        'preise': 'preise', 'pricing': 'preise',
    }
    return SLUG_MAP.get(slug, slug)


def _build_sitemap_register(project_id: int, db) -> list:
    lead_row = db.execute(text("SELECT lead_id FROM projects WHERE id = :pid"), {"pid": project_id}).fetchone()
    lead_id = lead_row[0] if lead_row else None
    if not lead_id:
        return []
    rows = db.execute(
        text("SELECT id, page_name, page_type, '' as slug FROM sitemap_pages WHERE lead_id = :lid ORDER BY position, id"),
        {"lid": lead_id},
    ).fetchall()
    result = []
    for row in rows:
        page_id, name, ptype, slug = row
        if not slug:
            slug = _make_slug(name)
            db.execute(text("UPDATE sitemap_pages SET slug = :slug WHERE id = :id"), {"slug": slug, "id": page_id})
        result.append({"id": page_id, "name": name, "type": ptype, "slug": slug, "path": f"/{slug}" if slug else "/"})
    db.commit()
    return result


def _resolve_links(html: str, sitemap: list, phone: str = "", email: str = "") -> tuple:
    if not html:
        return html, []
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    report = []
    path_map = {}
    for page in sitemap:
        for kw in [page['name'].lower(), page['slug'].lower(), page['type'].lower()]:
            if kw:
                path_map[kw] = page['path']
    extras = {
        'kontakt': '/kontakt', 'contact': '/kontakt', 'anfrage': '/kontakt',
        'angebot': '/kontakt', 'beratung': '/kontakt', 'termin': '/kontakt',
        'impressum': '/impressum', 'datenschutz': '/datenschutz', 'agb': '/agb',
        'leistungen': '/leistungen', 'services': '/leistungen',
        'referenzen': '/referenzen', 'galerie': '/galerie',
        'startseite': '/', 'home': '/', 'mehr erfahren': '/leistungen',
        'jetzt anfragen': '/kontakt', 'kostenlos': '/kontakt',
    }
    if phone:
        extras['anrufen'] = f'tel:{phone}'
    if email:
        extras['e-mail'] = f'mailto:{email}'
        extras['email'] = f'mailto:{email}'
    path_map.update(extras)

    def _find(text):
        t = text.lower().strip()
        if t in path_map:
            return path_map[t]
        for kw, p in path_map.items():
            if kw in t or t in kw:
                return p
        return None

    for tag in soup.find_all(['a', 'button']):
        txt = tag.get_text(strip=True)
        href = tag.get('href', '')
        is_broken = not href or href in ['#', '#!', 'javascript:void(0)', 'javascript:;'] or href.startswith('http://example') or href == 'URL_HIER'
        resolved = _find(txt)
        if is_broken and resolved:
            if tag.name == 'a':
                tag['href'] = resolved
            else:
                tag['onclick'] = f"window.location.href='{resolved}'"
            status = 'auto_fixed'
        elif is_broken:
            status = 'unresolved'
        else:
            status = 'ok'
        report.append({'text': txt[:50], 'tag': tag.name, 'original': href, 'resolved': resolved, 'href': tag.get('href', tag.get('onclick', '')), 'status': status})

    return str(soup), report


@router.post("/{project_id}/resolve-links")
async def resolve_project_links(
    project_id: int, data: dict,
    db: Session = Depends(get_db), _=Depends(require_any_auth),
):
    html = data.get("html", "")
    page_id = data.get("page_id")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    lead = project.lead
    phone = getattr(lead, 'phone', '') or ''
    email = getattr(lead, 'email', '') or ''
    sitemap = _build_sitemap_register(project_id, db)
    fixed_html, link_report = _resolve_links(html, sitemap, phone, email)
    auto_fixed = sum(1 for r in link_report if r['status'] == 'auto_fixed')
    unresolved = sum(1 for r in link_report if r['status'] == 'unresolved')
    return {
        "html": fixed_html,
        "link_report": link_report,
        "summary": {
            "total": len(link_report),
            "ok": sum(1 for r in link_report if r['status'] == 'ok'),
            "auto_fixed": auto_fixed,
            "unresolved": unresolved,
        },
    }


# **Hier stand `GET /{project_id}/sitemap-register`** — entfernt am
# 01.09.2026 (L-105), ohne Aufrufer. Der Helfer `_build_sitemap_register`
# **bleibt**: Die Linkaufloesung weiter oben braucht ihn.


@router.post("/{project_id}/design-json/{page_id}")
async def generate_design_json(
    project_id: int,
    page_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Claude liefert Block-JSON statt rohem HTML."""
    import os, httpx, json, re

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead    = project.lead
    lead_id = project.lead_id

    page = db.execute(
        text("SELECT page_name, page_type, ziel_keyword, zweck, ki_h1, ki_hero_text, ki_abschnitt_text, ki_cta, content_generated FROM sitemap_pages WHERE id=:id"),
        {"id": page_id},
    ).fetchone()
    if not page:
        raise HTTPException(404, "Seite nicht gefunden")
    page_name, page_type, keyword, zweck, ki_h1, ki_hero_text, ki_abschnitt_text, ki_cta, content_generated = page

    briefing = db.execute(
        text("SELECT gewerk, leistungen, einzugsgebiet, usp FROM briefings WHERE lead_id=:lid LIMIT 1"),
        {"lid": lead_id},
    ).fetchone()

    brand_json = getattr(lead, 'brand_design_json', None)
    brand = json.loads(brand_json) if brand_json else {}

    sitemap = db.execute(
        text("SELECT page_name, '' as slug FROM sitemap_pages WHERE lead_id=:lid ORDER BY position"),
        {"lid": lead_id},
    ).fetchall()
    sitemap_list = [{"name": r[0], "path": f"/{r[1]}" if r[1] else "/"} for r in sitemap]

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    gewerk  = briefing[0] if briefing else "Handwerksbetrieb"
    region  = briefing[2] if briefing else ""
    usp     = briefing[3] if briefing else ""
    company = getattr(lead, 'company_name', '') or ''
    phone   = getattr(lead, 'phone', '') or ''

    ki_section = ""
    if content_generated and any([ki_h1, ki_hero_text, ki_abschnitt_text, ki_cta]):
        ki_section = (
            f"\nKI-INHALTE fuer diese Seite (verwende diese Texte EXAKT):\n"
            f"- headline (hero): {ki_h1 or ''}\n"
            f"- subline (hero): {ki_hero_text or ''}\n"
            f"- abschnitt-text (ueber-uns): {ki_abschnitt_text or ''}\n"
            f"- cta_text: {ki_cta or ''}\n"
        )

    prompt = (
        f"Du bist Webdesigner fuer deutsche Handwerksbetriebe. Antworte NUR als JSON-Array.\n\n"
        f"FIRMA: {company} | BRANCHE: {gewerk} | REGION: {region} | TEL: {phone}\n"
        f"SEITE: {page_name} ({page_type}) | PRIMARY: {brand.get('primary_color', '#004F59')}\n\n"
        f"BLOECKE: hero, usp-balken, leistungen-grid, ueber-uns, referenzen, cta-banner, kontakt-form, footer\n\n"
        f"REGELN:\n"
        f"- hero: Split-Layout, fakten=[{{zahl,label}}x4]\n"
        f"- leistungen-grid: min.4 items mit Emoji-icon, titel, beschreibung\n"
        f"- cta-banner: immer phone:'{phone}'\n"
        f"- Texte Deutsch, spezifisch fuer {gewerk} in {region}\n"
        f"{ki_section}\n"
        f"REIHENFOLGE fuer '{page_type}': "
        f"{'hero+usp-balken+leistungen-grid+ueber-uns+referenzen+cta-banner+footer' if page_type in ('startseite', 'home') else 'hero+leistungen-grid+ueber-uns+cta-banner+footer'}\n\n"
        f'Start: [{{"type":"hero","data":{{"headline":"{ki_h1 or f"Ihr {gewerk} in {region}"}","subline":"{ki_hero_text or "Schnell - Zuverlaessig - Fair"}","cta_text":"{ki_cta or "Jetzt anfragen"}","cta_link":"/kontakt","cta2_text":"{phone}","cta2_link":"tel:{phone}","badge":"Meisterbetrieb","fakten":[{{"zahl":"500+","label":"Kunden"}},{{"zahl":"25 J.","label":"Erfahrung"}},{{"zahl":"4.9","label":"Google"}},{{"zahl":"24h","label":"Notdienst"}}]}}}},...footer]'
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-5", "thinking": {"type": "disabled"}, "max_tokens": 4000,
                      "messages": [{"role": "user", "content": prompt}]},
            )
        resp.raise_for_status()
        text_resp = resp.json()["content"][0]["text"].strip()
        text_resp = re.sub(r'^```json\s*', '', text_resp)
        text_resp = re.sub(r'\s*```$', '', text_resp)
        blocks = json.loads(text_resp)
        if not isinstance(blocks, list):
            raise ValueError("Keine Liste")

        return {
            "page_id":    page_id,
            "page_name":  page_name,
            "blocks":     blocks,
            "ki_injected": bool(ki_section),
            "brand": {
                "primary_color":   getattr(lead, 'brand_primary_color',   '#008EAA'),
                "secondary_color": getattr(lead, 'brand_secondary_color', '#004F59'),
                "font_primary":    getattr(lead, 'brand_font_primary',    'Inter'),
                "border_radius":   brand.get('design_brief', {}).get('radius_token', '8px'),
            }
        }

    except json.JSONDecodeError as e:
        raise HTTPException(500, f"JSON-Parse-Fehler: {str(e)[:100]}")
    except Exception as e:
        raise HTTPException(500, f"Fehler: {str(e)[:200]}")

# sitemap-suggest removed — use /api/sitemap/{lead_id}/generate instead


# ── Öffentliche Freigabe-Endpoints (kein Login erforderlich) ─────────────────

@public_router.get("/approve-content/{token}")
def get_approve_content(
    token: str,
    db: Session = Depends(get_db),
):
    """Öffentlich: Projektinfo anhand des Freigabe-Tokens abrufen."""
    row = db.execute(
        text(
            "SELECT id, company_name, briefing_approved_at "
            "FROM projects WHERE content_approval_token=:t LIMIT 1"
        ),
        {"t": token},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Ungültiger oder abgelaufener Freigabe-Link")
    return {
        "project_id":       row[0],
        "company_name":     row[1] or "Ihr Projekt",
        "already_approved": bool(row[2]),
    }


@public_router.post("/approve-content/{token}")
def post_approve_content(
    token: str,
    db: Session = Depends(get_db),
):
    """Öffentlich: Freigabe erteilen — setzt briefing_approved_at auf dem Projekt."""
    from datetime import datetime as _dt
    row = db.execute(
        text(
            "SELECT id, briefing_approved_at "
            "FROM projects WHERE content_approval_token=:t LIMIT 1"
        ),
        {"t": token},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Ungültiger oder abgelaufener Freigabe-Link")
    project_id, already_approved = row[0], row[1]
    if already_approved:
        return {"success": True, "already_approved": True}
    now = _dt.utcnow()
    db.execute(
        text("UPDATE projects SET briefing_approved_at=:ts WHERE id=:id"),
        {"ts": now, "id": project_id},
    )
    db.commit()
    return {"success": True, "already_approved": False, "approved_at": str(now)[:16]}
