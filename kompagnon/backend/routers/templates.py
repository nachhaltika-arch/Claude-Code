"""
Website Templates API — die eine Stelle fuer die Tabelle `website_templates`.

POST   /api/templates/upload              ZIP mit HTML/CSS hochladen (nur Admin)
POST   /api/templates/import-url          Vorlage aus einer oeffentlichen Adresse
POST   /api/templates/import-bulk         mehrere ZIPs auf einmal
GET    /api/templates/                    Liste
GET    /api/templates/suggestions         Referenz-Adressen je Gewerk
GET    /api/templates/{id}                eine Vorlage
GET    /api/templates/{id}/preview        HTML-Vorschau fuer ein iframe
PUT    /api/templates/{id}                Metadaten und Marken aendern
DELETE /api/templates/{id}                loeschen
POST   /api/templates/{id}/assign-project  einem Projekt zuweisen
POST   /api/templates/{id}/assign-lead     einem Betrieb zuweisen

Bis zum 21.08.2026 lag daneben ein zweiter Router `website_templates` unter
`/api/website-templates` — dieselbe Tabelle, drei gleiche Endpunkte, und
aufgerufen hat ihn nichts (L-28). Seine drei eigenen Endpunkte
(`import-bulk`, `suggestions`, `{id}/preview`) sind hierher gezogen.
"""
import io
import json
import logging
import os
import re
import zipfile
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth_router import require_admin, require_innendienst
from services.ki_aufruf import frag_modell

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/templates", tags=["templates"],
                   dependencies=[Depends(require_innendienst)])


# ── Hilfen, uebernommen aus dem frueheren `website_templates.py` ────
# Beide Router lagen auf derselben Tabelle; der zweite wurde von nichts
# aufgerufen (L-28, gemessen 21.08.2026).

def _make_slug(name: str) -> str:
    s = (name or "").lower().strip()
    for a, b in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")]:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:200] or "template"


def _unique_slug(base: str, db: Session) -> str:
    slug = base
    counter = 2
    while db.execute(
        text("SELECT id FROM website_templates WHERE slug = :s"), {"s": slug}
    ).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _extract_from_zip(zip_bytes: bytes, filename: str) -> dict:
    """Extracts HTML/CSS or GrapesJS JSON from a ZIP archive."""
    result = {
        "name": (filename or "template").replace(".zip", ""),
        "html": "",
        "css": "",
        "gjs_data": None,
    }
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            files = zf.namelist()

            # Prefer GrapesJS JSON
            gjs_file = next(
                (f for f in files
                 if f.endswith(".grapesjs") or f.endswith("grapesjs.json")
                 or f.endswith("gjs.json")),
                None,
            )
            if gjs_file:
                try:
                    result["gjs_data"] = zf.read(gjs_file).decode("utf-8", errors="ignore")
                    gjs = json.loads(result["gjs_data"])
                    pages = gjs.get("pages") or []
                    if pages:
                        comps = pages[0].get("frames", [{}])[0].get("component", {})
                        if isinstance(comps, dict):
                            inner = comps.get("components", "")
                            if isinstance(inner, str):
                                result["html"] = inner
                except Exception:
                    pass
                return result

            # HTML/CSS fallback
            html_file = next(
                (f for f in files if f.endswith("index.html")),
                next((f for f in files if f.endswith(".html")), None),
            )
            css_file = next(
                (f for f in files if f.endswith("style.css") or f.endswith("main.css")),
                next((f for f in files if f.endswith(".css")), None),
            )

            if html_file:
                raw_html = zf.read(html_file).decode("utf-8", errors="ignore")
                body_match = re.search(r"<body[^>]*>([\s\S]*?)</body>", raw_html, re.I)
                result["html"] = body_match.group(1).strip() if body_match else raw_html

                if css_file:
                    result["css"] = zf.read(css_file).decode("utf-8", errors="ignore")
                else:
                    # Inline <style> tags
                    styles = re.findall(r"<style[^>]*>([\s\S]*?)</style>", raw_html, re.I)
                    result["css"] = "\n".join(styles)

    except zipfile.BadZipFile:
        result["error"] = "Keine gültige ZIP-Datei"
    except Exception as e:
        result["error"] = str(e)
    return result


@router.post("/upload")
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form("allgemein"),
    tags: str = Form(""),
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Upload a ZIP archive containing an HTML/CSS template."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Nur ZIP-Dateien erlaubt")

    raw = await file.read()
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Ungültige ZIP-Datei")

    names = zf.namelist()

    # Find HTML file — prefer index.html, otherwise first .html
    html_name = next((n for n in names if n.lower().endswith("index.html")), None)
    if not html_name:
        html_name = next((n for n in names if n.lower().endswith(".html")), None)

    # Find CSS file — prefer style.css, otherwise first .css
    css_name = next((n for n in names if n.lower().endswith("style.css")), None)
    if not css_name:
        css_name = next((n for n in names if n.lower().endswith(".css")), None)

    html_content = zf.read(html_name).decode("utf-8", errors="replace") if html_name else None
    css_content = zf.read(css_name).decode("utf-8", errors="replace") if css_name else None

    if not html_content:
        raise HTTPException(status_code=400, detail="Keine HTML-Datei im ZIP gefunden")

    # `:name` und nicht `%(name)s`. Der Wechsel auf die Prozent-Schreibweise
    # (`afa35a3`, 10.04.2026) sollte „colon conflicts with CSS :root and ::
    # pseudo-elements" vermeiden — die Sorge ist unbegruendet: SQLAlchemy liest
    # nur den SQL-Text nach Platzhaltern ab, nie die gebundenen Werte. Ein
    # `:root` im CSS kann dort nicht ankommen. Die Vorsichtsmassnahme hat
    # diesen Endpunkt vier Monate lang mit einem Syntaxfehler beantwortet
    # (L-63). Ein Test schiebt jetzt `:root`, `::before` und `a:hover` durch.
    row = db.execute(
        text("""
            INSERT INTO website_templates
              (name, description, source, html_content, css_content, tags, category, created_at, updated_at)
            VALUES
              (:name, :desc, 'upload', :html, :css, :tags, :cat, NOW(), NOW())
            RETURNING id, name, created_at
        """),
        {
            "name": name,
            "desc": description,
            "html": html_content,
            "css": css_content,
            "tags": tags,
            "cat": category,
        },
    ).fetchone()
    db.commit()

    return {"id": row.id, "name": row.name, "created_at": row.created_at.isoformat()}


@router.get("/")
def list_templates(db: Session = Depends(get_db)):
    """List all active templates (without full HTML/CSS content)."""
    rows = db.execute(
        text("""
            SELECT id, name, description, source, source_url, thumbnail_url,
                   tags, category, is_active, created_at
            FROM website_templates
            WHERE is_active = true
            ORDER BY created_at DESC
        """)
    ).fetchall()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "source": r.source,
            "source_url": r.source_url,
            "thumbnail_url": r.thumbnail_url,
            "tags": r.tags,
            "category": r.category,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("/import-url")
async def import_template_from_url(
    body: dict,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Import a template from a public URL using AI reconstruction."""
    import httpx
    from anthropic import Anthropic

    url = body.get("url", "").strip()
    name = body.get("name", "").strip()
    description = body.get("description", "")

    if not url or not name:
        raise HTTPException(status_code=400, detail="url und name sind Pflichtfelder")

    # 1. Fetch URL
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers={
            "User-Agent": "Mozilla/5.0 (compatible; KOMPAGNON/1.0)"
        }) as client:
            resp = await client.get(url)
        html_raw = resp.text
    except Exception as e:
        return {"error": "URL nicht erreichbar", "detail": str(e)}

    # 2. Extract with BeautifulSoup
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_raw, "html.parser")
    style_tags = soup.find_all("style")
    css_content = "\n".join(s.get_text() for s in style_tags)
    body_tag = soup.find("body")
    html_body = str(body_tag) if body_tag else html_raw[:6000]

    # 3. Claude API reconstruction
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            client_ai = Anthropic(api_key=api_key)
            msg = await frag_modell(
                client_ai,
                model="claude-sonnet-5", thinking={"type": "disabled"},
                max_tokens=4000,
                system=(
                    "Du bist ein HTML-Entwickler. Bereinige und rekonstruiere "
                    "das gegebene HTML zu einer sauberen, selbstständigen Seite. "
                    "Behalte Struktur und Layout. Entferne Scripts und externe Abhängigkeiten. "
                    "Antworte NUR mit HTML — kein Markdown, keine Erklärung."
                ),
                messages=[{"role": "user", "content": html_body[:6000]}],
            )
            cleaned_html = msg.content[0].text.strip()
            # Strip markdown fences if present
            if cleaned_html.startswith("```"):
                cleaned_html = "\n".join(cleaned_html.split("\n")[1:])
            if cleaned_html.endswith("```"):
                cleaned_html = "\n".join(cleaned_html.split("\n")[:-1])
        except Exception:
            cleaned_html = html_body
    else:
        cleaned_html = html_body

    # 4. Save to DB
    row = db.execute(
        text("""
            INSERT INTO website_templates
              (name, description, source, source_url, html_content, css_content, created_at, updated_at)
            VALUES (:name, :desc, 'url', :url, :html, :css, NOW(), NOW())
            RETURNING id, name, html_content, created_at
        """),
        {"name": name, "desc": description, "url": url, "html": cleaned_html, "css": css_content},
    ).fetchone()
    db.commit()

    return {
        "id": row.id,
        "name": row.name,
        "html_content": row.html_content[:200],
        "created_at": row.created_at.isoformat(),
    }


@router.get("/project/{project_id}")
def get_project_template(project_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT wt.* FROM website_templates wt JOIN projects p ON p.template_id = wt.id WHERE p.id = :pid"),
        {"pid": project_id}
    ).fetchone()
    if not row:
        return None
    return dict(row._mapping)


@router.get("/lead/{lead_id}")
def get_lead_template(lead_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT wt.* FROM website_templates wt JOIN leads l ON l.template_id = wt.id WHERE l.id = :lid"),
        {"lid": lead_id}
    ).fetchone()
    if not row:
        return None
    return dict(row._mapping)


# ── Umgezogen aus `website_templates.py` (L-28) ─────────────────────
#
# `suggestions` steht **vor** `/{template_id}`. Andersherum liest
# FastAPI „suggestions" als Zahl und antwortet 422 — genau so ist am
# 07.05. `/layout-presets` hinter einem Catch-all verschwunden und
# lieferte drei Monate lang 404, ohne dass es auffiel.

@router.get("/suggestions")
def inspiration_suggestions(gewerk: Optional[str] = None):
    """Statische Liste guter Referenz-Websites pro Gewerk."""
    suggestions = {
        "sanitaer": [
            "https://www.breunig-sanitaer.de",
            "https://www.wolff-heizung-sanitaer.de",
            "https://www.meier-haustechnik.de",
        ],
        "heizung": [
            "https://www.buderus.de",
            "https://www.vaillant.de",
            "https://www.wolff-heizung-sanitaer.de",
        ],
        "elektro": [
            "https://www.elektro-schmid.de",
            "https://www.elektro-franke.de",
            "https://www.elektro-koerner.de",
        ],
        "maler": [
            "https://www.maler-heyse.de",
            "https://www.malerkronenberg.de",
            "https://www.malerbetrieb-muenchen.de",
        ],
        "dachdecker": [
            "https://www.dachdecker-seifert.de",
            "https://www.dachdecker-wiesbaden.de",
            "https://www.dachdecker-berlin.de",
        ],
        "schreiner": [
            "https://www.schreinerei-lang.de",
            "https://www.schreinerei-gebele.de",
        ],
        "fliesenleger": [
            "https://www.fliesen-koch.de",
            "https://www.fliesen-meyer.de",
        ],
    }
    key = (gewerk or "").lower()
    for k in suggestions:
        if k in key:
            return {"gewerk": k, "suggestions": suggestions[k]}
    # Fallback
    return {
        "gewerk": "allgemein",
        "suggestions": [
            "https://www.handwerker-muster.de",
            "https://www.handwerksmeister-beispiel.de",
            "https://www.qualitaets-handwerk.de",
        ],
    }


@router.post("/import-bulk")
async def import_bulk(
    files: List[UploadFile] = File(...),
    category: str = Form("allgemein"),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Mehrere ZIP-Dateien gleichzeitig importieren."""
    results = []
    for f in files:
        try:
            content = await f.read()
            extracted = _extract_from_zip(content, f.filename or "")
            if extracted.get("error"):
                results.append({"file": f.filename, "error": extracted["error"], "ok": False})
                continue

            slug = _unique_slug(_make_slug(extracted["name"]), db)
            db.execute(text("""
                INSERT INTO website_templates
                  (name, slug, category, html_content, css_content,
                   grapes_data, source_file, gewerk_tags, source)
                VALUES
                  (:name, :slug, :category, :html, :css,
                   CAST(:gjs AS JSONB), :source_file, '["alle"]', 'upload')
            """), {
                "name":        extracted["name"],
                "slug":        slug,
                "category":    category,
                "html":        extracted.get("html", ""),
                "css":         extracted.get("css", ""),
                "gjs":         extracted.get("gjs_data"),
                "source_file": f.filename,
            })
            results.append({"file": f.filename, "slug": slug, "ok": True})
        except Exception as e:
            logger.warning(f"Template import {f.filename} failed: {e}")
            try:
                db.rollback()
            except Exception:
                pass
            results.append({"file": f.filename, "error": str(e), "ok": False})

    db.commit()
    return {
        "imported": len([r for r in results if r.get("ok")]),
        "failed":   len([r for r in results if not r.get("ok")]),
        "results":  results,
    }


@router.get("/{template_id}/preview", response_class=HTMLResponse)
def get_preview(template_id: int, db: Session = Depends(get_db)):
    """HTML-Vorschau eines Templates — iframe-safe."""
    # `name` steht mit in der Abfrage, damit der Titel den Namen der Vorlage
    # nennen kann statt nur ihrer Nummer — wer drei Vorschauen offen hat,
    # unterscheidet sie am Tab.
    row = db.execute(
        text("SELECT html_content, css_content, name "
             "FROM website_templates WHERE id=:id"),
        {"id": template_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Template nicht gefunden")

    from services.seiten_huelle import vorschau_huelle
    return HTMLResponse(content=vorschau_huelle(
        row.html_content or "", row.css_content or "",
        row.name or f"Vorlage {template_id}"))


@router.get("/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get a single template including HTML/CSS content."""
    row = db.execute(
        text("SELECT * FROM website_templates WHERE id = :id"),
        {"id": template_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")
    return dict(row._mapping)


# PUT /api/templates/{id}
@router.put("/{template_id}")
def update_template(template_id: int, body: dict, db: Session = Depends(get_db)):
    import json as _json
    row = db.execute(text("SELECT id, is_builtin FROM website_templates WHERE id = :id"), {"id": template_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")
    if getattr(row, "is_builtin", False):
        raise HTTPException(status_code=403, detail="Eingebaute Templates sind schreibgeschützt")

    # Accept grapesjs_data as alias for grapes_data
    if "grapesjs_data" in body and "grapes_data" not in body:
        body = {**body, "grapes_data": body["grapesjs_data"]}

    fields = {k: v for k, v in body.items() if k in ("name", "description", "html_content", "css_content", "grapes_data", "tags", "category", "is_active")}
    if not fields:
        raise HTTPException(status_code=400, detail="Keine gültigen Felder")

    # Serialize grapes_data to JSON string if it's a dict
    if "grapes_data" in fields and isinstance(fields["grapes_data"], dict):
        fields["grapes_data"] = _json.dumps(fields["grapes_data"], ensure_ascii=False)

    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = template_id
    try:
        db.execute(text(f"UPDATE website_templates SET {set_clause}, updated_at=NOW() WHERE id = :id"), fields)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Speichern fehlgeschlagen: {str(e)[:200]}")
    return {"saved": True, "id": template_id}


# DELETE /api/templates/{id}
@router.delete("/{template_id}")
def delete_template(template_id: int, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM website_templates WHERE id = :id"), {"id": template_id})
    db.commit()
    return {"ok": True}


# POST /api/templates/{id}/assign-project
@router.post("/{template_id}/assign-project")
def assign_to_project(template_id: int, body: dict, db: Session = Depends(get_db)):
    project_id = body.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id fehlt")
    db.execute(text("UPDATE projects SET template_id = :tid WHERE id = :pid"), {"tid": template_id, "pid": project_id})
    db.commit()
    return {"ok": True}


# POST /api/templates/{id}/assign-lead
@router.post("/{template_id}/assign-lead")
def assign_to_lead(template_id: int, body: dict, db: Session = Depends(get_db)):
    lead_id = body.get("lead_id")
    if not lead_id:
        raise HTTPException(status_code=400, detail="lead_id fehlt")
    db.execute(text("UPDATE leads SET template_id = :tid WHERE id = :lid"), {"tid": template_id, "lid": lead_id})
    db.commit()
    return {"ok": True}
