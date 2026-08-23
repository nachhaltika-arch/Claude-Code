"""Die drei KI-Entwuerfe einer Website und was daraus gewaehlt wird (L-25).

**Warum eigene Datei, 23.08.2026.** `projects_content.py` fasste am 22.08.
neunzehn Endpunkte zusammen, die fachlich zusammengehoeren — und wurde dabei
1.017 Zeilen lang. Der groesste Abschnitt darin sind diese hier: **312
Zeilen** fuer das Erzeugen, Vergleichen und Auswaehlen der Entwurfsvarianten.

Sie sind der teuerste Teil der Kette (jeder Lauf kostet ein Modellaufruf) und
der einzige, der ohne fremde Hilfe auskommt: `projects_content.py` hat
**keine** Funktion auf Modulebene, alle sind Endpunkte. Geteilt wird also nur
der Router und seine Sperre.

**Reiner Umzug.** Kein Pfad, keine Signatur, keine Logik geaendert.
"""
import logging
from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Project, SessionLocal, get_db
from routers.auth_router import get_current_user, require_admin, require_any_auth
from routers.projects_helfer import eigenes_projekt_pruefen, safe_json_parse
from routers.projects_router import kunden_router, router
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
