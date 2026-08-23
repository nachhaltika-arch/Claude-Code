"""Inhalte eines Projekts — von der Entwurfsvariante bis zur Abnahme.

**Was hier liegt (L-25, Etappe 2, 22.08.2026).** Die Kette, die aus einem
Betrieb eine fertige Website macht: KI-Entwuerfe, das Auslesen der alten
Seite, der QA-Scanner, der Sitemap-Planer, die Content-Freigaben, die
QA-Checkliste und die Abnahme. Neunzehn Endpunkte, die fachlich
zusammengehoeren und in `projects.py` nur nebeneinander lagen.

**Warum die Aufteilung ueberhaupt (L-76).** In einer Datei mit 4.800 Zeilen
sieht niemand, dass eine Adresse schon vergeben ist — genau so sind hier am
22.08. zwei Freigabe-Verfahren auf **eine** Adresse gewachsen. Der Umbau
behandelt die Ursache, nicht das Symptom.

**Reiner Umzug.** Keine Logik, kein Pfad, keine Signatur geaendert. Router und
gemeinsame Helfer kommen aus `projects_router.py` und `projects_helfer.py` —
dieselben Objekte wie zuvor, damit sich keine Adresse verschiebt.
Gegengeprueft mit `tools/endpunkte_auflisten.py`.
"""
import logging
from datetime import datetime

from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Project, SessionLocal, get_db
from routers.auth_router import get_current_user, require_admin, require_any_auth
from routers.projects_helfer import (_get_fernet, eigenes_projekt_pruefen,
                                     safe_json_parse)
from routers.projects_router import kunden_router, router
from services.audit_pagespeed import api_key as pagespeed_api_key
from services.base_urls import public_base_url
from services.ki_aufruf import frag_modell

logger = logging.getLogger(__name__)


# ── Website-Versionen (KI generiert 3 Entwürfe) ───────────────────────────────

@router.post("/{project_id}/generate-versions")
async def generate_website_versions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generiert 3 Website-Versionen basierend auf Briefing, Inspirationen und Templates."""
    import json as _json
    import os as _os

    # Projektdaten + Lead laden (inkl. Briefing-Felder)
    project_row = db.execute(text("""
        SELECT p.id as pid, p.lead_id as lead_id, p.company_name as p_company,
               l.company_name as l_company, l.trade, l.wz_title,
               l.inspiration_url_1, l.inspiration_url_2, l.inspiration_url_3
        FROM projects p
        LEFT JOIN leads l ON p.lead_id = l.id
        WHERE p.id = :id
    """), {"id": project_id}).fetchone()
    if not project_row:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead_id = project_row.lead_id
    company_name = project_row.p_company or project_row.l_company or f"Projekt {project_id}"

    # Briefing-Daten (separate Tabelle)
    briefing = None
    try:
        briefing = db.execute(text("""
            SELECT gewerk, leistungen, einzugsgebiet, usp, mitbewerber,
                   farben, wunschseiten, stil
            FROM briefings WHERE lead_id = :id
            ORDER BY created_at DESC LIMIT 1
        """), {"id": lead_id}).fetchone()
    except Exception:
        pass

    gewerk = (briefing.gewerk if briefing else None) or project_row.trade or project_row.wz_title or ""
    stil   = (briefing.stil if briefing else None) or "modern"

    # Alte Website-Content Teaser
    old_content_rows = []
    try:
        old_content_rows = db.execute(text("""
            SELECT title, h1, text_preview
            FROM website_content_cache
            WHERE customer_id = :cid
            ORDER BY scraped_at DESC LIMIT 5
        """), {"cid": lead_id}).fetchall()
    except Exception:
        pass

    # Templates filtern: passend zum Gewerk oder "alle"
    templates = db.execute(text("""
        SELECT id, name, slug,
               COALESCE(style_tags, '') AS style_tags,
               COALESCE(gewerk_tags, '') AS gewerk_tags
        FROM website_templates
        WHERE COALESCE(is_active, TRUE) = TRUE
          AND (gewerk_tags ILIKE :gewerk OR gewerk_tags ILIKE '%alle%' OR gewerk_tags IS NULL OR gewerk_tags = '')
        ORDER BY RANDOM()
        LIMIT 9
    """), {"gewerk": f"%{gewerk.lower()[:20]}%"}).fetchall()

    if len(templates) < 3:
        templates = db.execute(text("""
            SELECT id, name, slug,
                   COALESCE(style_tags, '') AS style_tags,
                   COALESCE(gewerk_tags, '') AS gewerk_tags
            FROM website_templates
            WHERE COALESCE(is_active, TRUE) = TRUE
            ORDER BY RANDOM() LIMIT 9
        """)).fetchall()

    if len(templates) < 1:
        raise HTTPException(400, "Keine Templates vorhanden. Bitte erst welche importieren.")

    template_options = "\n".join([
        f"Template {i+1}: ID={t.id}, Name={t.name}, Stile={t.style_tags}"
        for i, t in enumerate(templates[:9])
    ])

    old_content_text = "\n".join([
        f"- {r.title or ''}: {(r.text_preview or '')[:200]}"
        for r in old_content_rows if r.title
    ]) or "Keine Inhalte von alter Website vorhanden"

    inspirations = "\n".join(filter(None, [
        project_row.inspiration_url_1,
        project_row.inspiration_url_2,
        project_row.inspiration_url_3,
    ])) or "Keine Inspirationsseiten angegeben"

    system_prompt = (
        "Du bist ein professioneller Webdesigner und Markenstratege "
        "für deutsche Handwerksbetriebe. Du analysierst alle verfügbaren "
        "Informationen und wählst die 3 besten passenden Templates aus. "
        "Du denkst dabei PROAKTIV: Wenn der Kunde kein starkes Brand hat, "
        "machst du konkrete Optimierungsvorschläge für Farben, Stil und "
        "Positionierung die seine Zielgruppe ansprechen.\n\n"
        "Antworte AUSSCHLIESSLICH als valides JSON. Kein Markdown. "
        "Kein Text davor oder danach."
    )

    user_prompt = f"""
KUNDENINFORMATIONEN:
Firma: {company_name}
Gewerk: {gewerk or 'nicht angegeben'}
Leistungen: {(briefing.leistungen if briefing else None) or 'nicht angegeben'}
Einzugsgebiet: {(briefing.einzugsgebiet if briefing else None) or 'nicht angegeben'}
USPs: {(briefing.usp if briefing else None) or 'nicht angegeben'}
Gewünschte Farben: {(briefing.farben if briefing else None) or 'nicht angegeben'}
Gewünschter Stil: {stil}

INHALTE DER ALTEN WEBSITE:
{old_content_text}

INSPIRATIONSSEITEN DES KUNDEN:
{inspirations}

VERFÜGBARE TEMPLATES:
{template_options}

AUFGABE:
Wähle 3 verschiedene Templates aus den verfügbaren aus und begründe die Wahl.
Jede Version soll einen anderen Ansatz verfolgen:
- Version A: nah am Kundenwunsch
- Version B: optimierte/moderne Variante
- Version C: mutigere/auffälligere Variante

Antworte als JSON:
{{
  "versions": [
    {{
      "label": "A",
      "template_id": <ID>,
      "titel": "Kurzer Titel (max 6 Wörter)",
      "beschreibung": "2-3 Sätze",
      "optimierungen": "Was wird gegenüber der alten Website verbessert",
      "farb_empfehlung": "Konkrete Farbempfehlung",
      "zielgruppen_ansprache": "Wie das Design die Zielgruppe anspricht"
    }},
    {{"label": "B", ...}},
    {{"label": "C", ...}}
  ],
  "gesamt_empfehlung": "Welche Version empfohlen wird und warum"
}}
"""

    # Template-Infos als einfache dicts speichern (für Fallback nach DB-Close)
    templates_data = [
        {"id": t.id, "name": t.name, "style_tags": t.style_tags}
        for t in templates
    ]
    available_ids = {t["id"] for t in templates_data}

    # DB-Verbindung vor dem externen Claude-Call freigeben
    db.close()

    # Fallback ohne KI: zufällig 3 Templates
    result = None
    try:
        from anthropic import Anthropic
        api_key = _os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY nicht gesetzt")
        client = Anthropic(api_key=api_key)
        response = await frag_modell(
            client,
            model="claude-sonnet-5", thinking={"type": "disabled"},
            max_tokens=3000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = response.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = _json.loads(raw)
    except Exception as e:
        logger.warning(f"KI-Versionierung Fehler, nutze Zufallsauswahl: {e}")
        # Fallback: zufällig 3 Templates
        chosen = templates_data[:3]
        labels = ["A", "B", "C"]
        result = {
            "versions": [
                {
                    "label": labels[i],
                    "template_id": t["id"],
                    "titel":        f"Version {labels[i]}: {t['name']}",
                    "beschreibung": "Automatische Auswahl (KI nicht verfügbar).",
                    "optimierungen": "",
                    "farb_empfehlung": "",
                    "zielgruppen_ansprache": "",
                }
                for i, t in enumerate(chosen)
            ],
            "gesamt_empfehlung": "KI war nicht verfügbar — 3 Templates zufällig gewählt.",
        }

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        # Alte Versionen löschen
        db2.execute(text("DELETE FROM website_versions WHERE project_id = :id"), {"id": project_id})

        # 3 Versionen speichern
        saved = []
        template_ids_in_result = {int(v.get("template_id", 0)) for v in result.get("versions", []) if v.get("template_id")}

        for v in result.get("versions", [])[:3]:
            tid = v.get("template_id")
            # Absicherung: falls KI eine falsche ID vorschlägt, nimm ein zufälliges verfügbares
            if not tid or tid not in available_ids:
                tid = next(iter(available_ids - template_ids_in_result), next(iter(available_ids)))
                template_ids_in_result.add(tid)

            tpl = db2.execute(text(
                "SELECT html_content, css_content, grapes_data FROM website_templates WHERE id = :id"
            ), {"id": tid}).fetchone()

            row = db2.execute(text("""
                INSERT INTO website_versions
                  (project_id, version_label, template_id, html, css, gjs_data, ki_reasoning)
                VALUES (:pid, :label, :tid, :html, :css, :gjs, :reasoning)
                RETURNING id
            """), {
                "pid":       project_id,
                "label":     v.get("label", "A"),
                "tid":       tid,
                "html":      (tpl.html_content if tpl else "") or "",
                "css":       (tpl.css_content if tpl else "") or "",
                "gjs":       _json.dumps(tpl.grapes_data) if (tpl and tpl.grapes_data) else None,
                "reasoning": _json.dumps({
                    "titel":             v.get("titel"),
                    "beschreibung":      v.get("beschreibung"),
                    "optimierungen":     v.get("optimierungen"),
                    "farb_empfehlung":   v.get("farb_empfehlung"),
                    "zielgruppe":        v.get("zielgruppen_ansprache"),
                }, ensure_ascii=False),
            })
            saved.append({"version": v.get("label", "A"), "id": row.fetchone()[0]})

        db2.commit()
    finally:
        db2.close()

    return {
        "versions":     saved,
        "empfehlung":   result.get("gesamt_empfehlung"),
        "project_id":   project_id,
    }


@router.get("/{project_id}/versions")
def list_versions(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Alle generierten Versionen für ein Projekt."""
    rows = db.execute(text("""
        SELECT v.id, v.version_label, v.template_id, v.selected, v.ki_reasoning,
               v.created_at, t.name as template_name, t.thumbnail_url
        FROM website_versions v
        LEFT JOIN website_templates t ON v.template_id = t.id
        WHERE v.project_id = :pid
        ORDER BY v.version_label
    """), {"pid": project_id}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/{project_id}/versions/{version_id}/select")
def select_version(
    project_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Eine Version als ausgewählt markieren (alle anderen deaktivieren)."""
    db.execute(text("UPDATE website_versions SET selected=FALSE WHERE project_id=:pid"), {"pid": project_id})
    db.execute(text("""
        UPDATE website_versions SET selected=TRUE
        WHERE id=:vid AND project_id=:pid
    """), {"vid": version_id, "pid": project_id})
    db.commit()
    return {"selected": version_id}


@router.get("/{project_id}/versions/{version_id}/preview")
def version_preview(
    project_id: int,
    version_id: int,
    db: Session = Depends(get_db),
):
    """HTML-Preview einer Version für iframe-Einbettung."""
    from fastapi.responses import HTMLResponse
    row = db.execute(text("""
        SELECT html, css FROM website_versions
        WHERE id = :vid AND project_id = :pid
    """), {"vid": version_id, "pid": project_id}).fetchone()
    if not row:
        raise HTTPException(404, "Version nicht gefunden")
    html = row.html or "<p>Kein Inhalt</p>"
    css  = row.css or ""
    return HTMLResponse(
        f"""<!DOCTYPE html><html lang="de"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{css}</style></head><body>{html}</body></html>"""
    )


# ── Scrape Website Content ─────────────────────────────────────────────────────

@router.get("/{project_id}/scrape-content")
def scrape_project_content(project_id: int, db: Session = Depends(get_db)):
    """Fetch and parse the project's website, store clean text in scraped_content."""
    import requests
    from bs4 import BeautifulSoup

    # Ensure columns exist
    db.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS scraped_content TEXT"))
    db.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMP"))
    db.commit()

    # Load project URL
    row = db.execute(
        text("SELECT website_url FROM projects WHERE id = :id"),
        {"id": project_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    website_url = row[0]
    if not website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")

    # Fetch page
    try:
        resp = requests.get(
            website_url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"},
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Website nicht erreichbar: {e}")

    # Parse with BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    parts = []
    for el in soup.find_all(["main", "article", "section", "p", "h1", "h2", "h3", "h4", "h5", "h6"]):
        text_content = el.get_text(separator=" ", strip=True)
        if text_content:
            parts.append(text_content)

    content = "\n\n".join(parts)

    # Persist
    scraped_at = datetime.utcnow()
    db.execute(
        text("UPDATE projects SET scraped_content = :content, scraped_at = :ts WHERE id = :id"),
        {"content": content, "ts": scraped_at, "id": project_id},
    )
    db.commit()

    return {"content": content, "scraped_at": scraped_at.isoformat()}


# ── QA-Scanner Endpunkte ──────────────────────────────────────────────────────

@router.post("/{project_id}/qa/run")
async def run_project_qa(project_id: int, db: Session = Depends(get_db)):
    """Führt vollständigen KI-QA-Scan durch und speichert Ergebnis."""
    from services.qa_scanner import run_full_qa, ai_evaluate_qa
    import json as _json

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    # Website-URL ermitteln
    url = getattr(project, "website_url", None)
    if not url and project.lead:
        url = project.lead.website_url
    if not url:
        raise HTTPException(400, "Keine Website-URL hinterlegt")

    company = getattr(project, "customer_name", None) or \
              (project.lead.company_name if project.lead else "")
    trade = (project.lead.trade if project.lead else "") or ""

    # 1. Automatische Checks
    scan = await run_full_qa(url, company, trade)
    if "error" in scan:
        raise HTTPException(422, f"Website nicht erreichbar: {scan['error']}")

    # 2. KI-Auswertung
    ai = await ai_evaluate_qa(scan)

    # 3. Ergebnis speichern
    full_result = {**scan, "ai": ai, "checks": scan["checks"]}
    full_result.pop("html_snippet", None)  # zu groß für DB

    project.qa_result    = _json.dumps(full_result, ensure_ascii=False)
    project.qa_score     = ai.get("gesamt_score", 0)
    project.qa_golive_ok = ai.get("golive_empfehlung", False)
    project.qa_run_at    = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "score": project.qa_score,
        "golive_ok": project.qa_golive_ok,
        "result": full_result,
    }


@router.get("/{project_id}/qa/result")
def get_qa_result(project_id: int, db: Session = Depends(get_db)):
    """Gibt das zuletzt gespeicherte QA-Ergebnis zurück.
    Funktioniert egal ob qa_result als Text-JSON oder JSONB-Dict kommt.
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"status": "no_result", "message": "Projekt nicht gefunden"}
        if not project.qa_result:
            return {"status": "no_result", "message": "Noch kein QA-Scan für dieses Projekt"}

        parsed = safe_json_parse(project.qa_result, default=None)
        if parsed is None:
            return {
                "status": "parse_error",
                "message": "QA-Ergebnis konnte nicht gelesen werden",
                "score": project.qa_score,
                "run_at": str(project.qa_run_at)[:16] if project.qa_run_at else None,
            }

        return {
            "score": project.qa_score,
            "golive_ok": project.qa_golive_ok,
            "run_at": str(project.qa_run_at)[:16] if project.qa_run_at else None,
            "result": parsed,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"QA-Result unerwarteter Fehler: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/credentials")
def add_credential(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_auth),
):
    label    = (data.get("label") or "").strip()
    username = (data.get("username") or data.get("benutzername") or "").strip()
    password = (data.get("password") or data.get("passwort") or "").strip()
    url      = (data.get("url") or "").strip()
    notes    = (data.get("notes") or data.get("notizen") or "").strip()

    if not label:
        raise HTTPException(400, "Label ist Pflichtfeld")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    encrypted = ""
    if password:
        try:
            f = _get_fernet()
            encrypted = f.encrypt(password.encode()).decode()
        except RuntimeError as e:
            logger.error(f"CREDENTIALS_KEY Fehler: {e}")
            raise HTTPException(
                status_code=503,
                detail="Zugangsdaten-Safe nicht verfügbar: CREDENTIALS_KEY nicht konfiguriert. Bitte Administrator kontaktieren.",
            )
        except Exception as e:
            logger.error(f"Verschluesselung Fehler: {e}")
            raise HTTPException(500, "Verschluesselung fehlgeschlagen")

    typ = (data.get("typ") or "sonstiges").strip()
    db.execute(text("""
        INSERT INTO project_credentials
            (project_id, label, typ, username, password_encrypted, url, notes)
        VALUES
            (:pid, :label, :typ, :username, :pw, :url, :notes)
    """), {
        "pid":      project_id,
        "label":    label,
        "typ":      typ,
        "username": username,
        "pw":       encrypted,
        "url":      url,
        "notes":    notes,
    })
    db.commit()

    row = db.execute(text(
        "SELECT id, created_at FROM project_credentials "
        "WHERE project_id=:pid ORDER BY id DESC LIMIT 1"
    ), {"pid": project_id}).fetchone()

    return {
        "success":    True,
        "id":         row[0] if row else None,
        "label":      label,
        "username":   username,
        "url":        url,
        "created_at": str(row[1])[:16] if row else "",
    }


@router.get("/{project_id}/credentials")
def get_credentials(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_auth),
):
    rows = db.execute(text("""
        SELECT id, label, COALESCE(typ,'sonstiges') as typ, username, password_encrypted,
               url, notes, created_at
        FROM project_credentials
        WHERE project_id = :pid
        ORDER BY created_at ASC
    """), {"pid": project_id}).mappings().all()

    try:
        f = _get_fernet()
    except RuntimeError as e:
        logger.error(f"CREDENTIALS_KEY Fehler: {e}")
        raise HTTPException(
            status_code=503,
            detail="Zugangsdaten-Safe nicht verfügbar: CREDENTIALS_KEY nicht konfiguriert. Bitte Administrator kontaktieren.",
        )
    result = []
    for r in rows:
        decrypted = ""
        if r["password_encrypted"]:
            try:
                decrypted = f.decrypt(r["password_encrypted"].encode()).decode()
            except Exception:
                decrypted = "Entschluesselung fehlgeschlagen"
        result.append({
            "id":         r["id"],
            "label":      r["label"],
            "typ":        r["typ"] or "sonstiges",
            "username":   r["username"] or "",
            "password":   decrypted,
            "url":        r["url"] or "",
            "notes":      r["notes"] or "",
            "created_at": str(r["created_at"])[:16],
        })
    return result


@router.delete("/{project_id}/credentials/{cred_id}")
def delete_credential(
    project_id: int,
    cred_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_auth),
):
    db.execute(text("""
        DELETE FROM project_credentials
        WHERE id = :cid AND project_id = :pid
    """), {"cid": cred_id, "pid": project_id})
    db.commit()
    return {"success": True}


@router.get("/{project_id}/auftragsbestaetigung")
def download_auftragsbestaetigung(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Lädt die Auftragsbestätigung als PDF herunter (nur Admin)."""
    import os as _os
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    path = getattr(project, "auftragsbestaetigung_pdf", None)
    if not path or not _os.path.exists(path):
        raise HTTPException(404, "PDF nicht vorhanden")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename="KOMPAGNON-Auftragsbestaetigung.pdf",
    )


# ── Sitemap-Planer ────────────────────────────────────────────────────────────

@router.get("/{project_id}/sitemap")
def get_sitemap(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    row = db.execute(
        text("SELECT sitemap_json, sitemap_freigabe FROM projects WHERE id=:id"),
        {"id": project_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Projekt nicht gefunden")
    seiten = safe_json_parse(row[0], default=[])
    return {
        "seiten":           seiten,
        "sitemap_freigabe": str(row[1])[:16] if row[1] else None,
    }


@router.patch("/{project_id}/sitemap")
def save_sitemap(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    seiten = data.get("seiten", [])
    db.execute(
        text("UPDATE projects SET sitemap_json=:sj WHERE id=:id"),
        {"sj": json.dumps(seiten, ensure_ascii=False), "id": project_id},
    )
    db.commit()
    return {"success": True, "count": len(seiten)}


@router.post("/{project_id}/freigabe")
def request_freigabe(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    from datetime import datetime

    typ    = data.get("typ", "")
    seiten = data.get("seiten", [])
    now    = datetime.utcnow()

    if typ == "sitemap":
        db.execute(
            text("""
                UPDATE projects SET
                  sitemap_json=:sj,
                  sitemap_freigabe=:ts
                WHERE id=:id
            """),
            {
                "sj": json.dumps(seiten, ensure_ascii=False),
                "ts": now,
                "id": project_id,
            },
        )
        db.commit()
        return {
            "success":          True,
            "typ":              "sitemap",
            "sitemap_freigabe": str(now)[:16],
        }

    raise HTTPException(400, f"Unbekannter Freigabe-Typ: {typ}")


# ── Content-Freigaben ─────────────────────────────────────────────────────────

# Seitenweise Freigabe fuer das Kundenportal. Lag bis zum 22.08.2026 auf
# derselben Adresse wie die Token-Freigabe bei Zeile 1041 und war deshalb nie
# erreichbar: FastAPI nimmt bei gleichem Pfad die zuerst registrierte Funktion.
# Python ueberschrieb ausserdem den Namen `request_approval` — nachgelesen
# wurde also diese Fassung, geantwortet hat die andere.
#
# Die Gegenstelle ist `confirm_approval` weiter unten. Ohne diese Haelfte
# entstand nie ein Eintrag mit `status: "angefragt"`, und die Liste im
# Kundenportal konnte nur zeigen, was bereits entschieden war.
#
# **Sie hat noch keinen Aufrufer.** Der Knopf, der pro Seite eine Freigabe
# anfragt, muss in der Oberflaeche erst gebaut werden — das ist eine
# Produktentscheidung und war nicht Teil der Reparatur.
@router.post("/{project_id}/request-page-approval")
def request_page_approval(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    from datetime import datetime

    topic    = data.get("topic", "Freigabe erforderlich")
    notes    = data.get("notes", "")
    seite_id = data.get("seite_id")

    row = db.execute(text("""
        SELECT p.id, p.content_freigaben, l.email, l.company_name
        FROM projects p
        LEFT JOIN leads l ON l.id = p.lead_id
        WHERE p.id = :id
    """), {"id": project_id}).fetchone()

    if not row:
        raise HTTPException(404, "Projekt nicht gefunden")

    customer_email = row[2] or ""
    company_name   = row[3] or "Kunde"

    freigaben = safe_json_parse(row[1], default={}) or {}

    now_str = datetime.utcnow().strftime("%d.%m.%Y %H:%M")

    if seite_id:
        freigaben[str(seite_id)] = {
            "status":       "angefragt",
            "angefragt_am": now_str,
            "topic":        topic,
        }

    db.execute(text(
        "UPDATE projects SET content_freigaben=:cf WHERE id=:id"
    ), {"cf": json.dumps(freigaben, ensure_ascii=False), "id": project_id})
    db.commit()

    email_sent = False
    if customer_email:
        try:
            from services.email import send_email
            html = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
              <div style="background:#008eaa;padding:20px 28px;border-radius:12px 12px 0 0">
                <h2 style="color:white;margin:0;font-size:18px">
                  Ihre Freigabe wird ben&#246;tigt
                </h2>
              </div>
              <div style="padding:24px 28px;background:#fff">
                <p style="color:#1a2332">Guten Tag, {company_name},</p>
                <p style="color:#64748b;line-height:1.7">
                  f&#252;r den n&#228;chsten Schritt in Ihrem Projekt ben&#246;tigen wir Ihre Freigabe:
                </p>
                <div style="background:#F8F9FA;border-left:4px solid #008eaa;
                            padding:12px 16px;border-radius:0 8px 8px 0;margin:16px 0">
                  <strong style="color:#1a2332">{topic}</strong>
                  {"<p style='color:#64748b;margin-top:8px;font-size:14px'>" + notes + "</p>" if notes else ""}
                </div>
                <p style="color:#64748b;line-height:1.7">
                  Bitte antworten Sie auf diese E-Mail oder melden Sie sich
                  in Ihrem Kundenportal an, um die Freigabe zu erteilen.
                </p>
                <div style="text-align:center;margin:20px 0">
                  <a href="{public_base_url()}/kundenportal"
                     style="display:inline-block;padding:12px 28px;background:#008eaa;color:white;
                            text-decoration:none;border-radius:8px;font-weight:bold;font-size:15px">
                    Zum Kundenportal &rarr;
                  </a>
                </div>
              </div>
              <div style="padding:14px 28px;background:#f8f9fa;
                          border-radius:0 0 12px 12px;text-align:center">
                <p style="font-size:11px;color:#94a3b8;margin:0">
                  KOMPAGNON Communications BP GmbH &#183; kompagnon.eu
                </p>
              </div>
            </div>"""
            email_sent = send_email(
                to_email=customer_email,
                subject=f"Freigabe erforderlich: {topic}",
                html_body=html,
            )
        except Exception as e:
            logger.warning(f"Approval-E-Mail Fehler: {e}")

    return {
        "success":        True,
        "seite_id":       seite_id,
        "email_sent":     email_sent,
        "customer_email": customer_email,
        "angefragt_am":   now_str,
        "freigaben":      freigaben,
    }


@kunden_router.post("/{project_id}/confirm-approval")
def confirm_approval(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Die Freigabe eintragen — durch den Kunden oder den Innendienst.

    Stand bis zum 17.08.2026 auf `require_admin`. Damit war der Knopf auf der
    Kundenseite `customer/Freigaben.jsx` wirkungslos, während die Anfrage-Mail
    „melden Sie sich in Ihrem Kundenportal an" schrieb. Der Innendienst darf
    weiterhin: Freigaben werden auch am Telefon erteilt und nachgetragen.
    """
    import json
    from datetime import datetime

    eigenes_projekt_pruefen(db, project_id, current_user)

    seite_id   = str(data.get("seite_id", ""))
    bestaetigt = data.get("bestaetigt", True)

    row = db.execute(
        text("SELECT content_freigaben FROM projects WHERE id=:id"),
        {"id": project_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Nicht gefunden")

    freigaben = safe_json_parse(row[0], default={}) or {}

    now_str = datetime.utcnow().strftime("%d.%m.%Y %H:%M")
    if seite_id in freigaben:
        freigaben[seite_id]["status"]         = "freigegeben" if bestaetigt else "abgelehnt"
        freigaben[seite_id]["freigegeben_am"] = now_str
    else:
        freigaben[seite_id] = {
            "status":         "freigegeben" if bestaetigt else "abgelehnt",
            "freigegeben_am": now_str,
        }

    db.execute(
        text("UPDATE projects SET content_freigaben=:cf WHERE id=:id"),
        {"cf": json.dumps(freigaben, ensure_ascii=False), "id": project_id},
    )
    db.commit()
    return {"success": True, "seite_id": seite_id, "freigaben": freigaben}


# ── QA-Checkliste ─────────────────────────────────────────────────────────────

@router.patch("/{project_id}/qa-checklist")
def save_qa_checklist(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    checked = data.get("checked", {})
    db.execute(
        text("UPDATE projects SET qa_checklist_json=:qj WHERE id=:id"),
        {"qj": json.dumps(checked, ensure_ascii=False), "id": project_id},
    )
    db.commit()
    return {"success": True, "checked_count": len(checked)}


# ── Abnahme & Go-Live Nachher ─────────────────────────────────────────────────

@router.post("/{project_id}/abnahme")
def abnahme_erteilen(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from datetime import datetime as dt

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "Name ist Pflichtfeld")

    now = dt.utcnow()
    db.execute(text("""
        UPDATE projects SET
          abnahme_datum=:ts,
          abnahme_durch=:name,
          actual_go_live=COALESCE(actual_go_live, :ts)
        WHERE id=:id
    """), {"ts": now, "name": name, "id": project_id})
    db.commit()

    now_de = now.strftime("%d.%m.%Y um %H:%M Uhr")
    return {
        "success":       True,
        "abnahme_datum": str(now)[:16],
        "abnahme_durch": name,
        "text":          f"Abgenommen am {now_de} von {name}",
    }


@router.post("/{project_id}/go-live-pagespeed")
async def go_live_pagespeed(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import httpx
    import os
    import asyncio

    row = db.execute(text("""
        SELECT l.website_url FROM projects p
        LEFT JOIN leads l ON l.id = p.lead_id
        WHERE p.id = :id
    """), {"id": project_id}).fetchone()

    if not row or not row[0]:
        raise HTTPException(400, "Keine Website-URL hinterlegt")

    url     = row[0]

    # DB-Verbindung vor externen PageSpeed + Screenshot Calls freigeben
    db.close()

    api_key = pagespeed_api_key()
    base    = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params  = {"url": url}
    if api_key:
        params["key"] = api_key

    mob_score = desk_score = None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            mob, desk = await asyncio.gather(
                client.get(base, params={**params, "strategy": "mobile"}),
                client.get(base, params={**params, "strategy": "desktop"}),
            )

        def sc(r):
            try:
                return round(
                    (r.json()["categories"]["performance"]["score"] or 0) * 100
                )
            except Exception:
                return None

        mob_score  = sc(mob)
        desk_score = sc(desk)
    except Exception as e:
        logger.warning(f"Go-Live PageSpeed Fehler: {e}")

    screenshot_after = None
    try:
        from services.screenshot import capture_screenshot
        screenshot_after = await capture_screenshot(url)
    except Exception as e:
        logger.warning(f"Go-Live Screenshot Fehler: {e}")

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        db2.execute(text("""
            UPDATE projects SET
              pagespeed_after_mobile=:mob,
              pagespeed_after_desktop=:desk,
              screenshot_after=:sc
            WHERE id=:id
        """), {
            "mob":  mob_score,
            "desk": desk_score,
            "sc":   screenshot_after,
            "id":   project_id,
        })
        db2.commit()
    finally:
        db2.close()

    return {
        "success":                 True,
        "pagespeed_after_mobile":  mob_score,
        "pagespeed_after_desktop": desk_score,
        "has_screenshot":          bool(screenshot_after),
    }
