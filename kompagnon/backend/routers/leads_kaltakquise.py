"""Kaltakquise — ein Betrieb wird angeschrieben (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/leads.py` hatte 2.575 Zeilen und
fuenfzig Funktionen. Eine einzige Route, aber 257 Zeilen: Sie baut die Anschreiben, prueft die
Sperren und protokolliert. Mit dem Rest von `leads.py` teilte sie nichts
ausser `logger` und dem Router.

Vor dem Schnitt nachgemessen: Der Rest braucht von hier **nichts**.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import Lead, Project, AuditResult, get_db, SessionLocal
from services.pdf_generator import branche_fuer_protokoll
import httpx
import json
import os
from routers.auth_router import require_innendienst, require_any_auth
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads-kaltakquise"],
                   dependencies=[Depends(require_innendienst)])


@router.post("/{lead_id}/kaltakquise")
async def start_kaltakquise(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """
    Vollautomatischer Kaltakquise-Workflow:
    1. Neuesten abgeschlossenen Audit laden
    2. KI-Anschreiben auf Basis der Audit-Schwächen generieren
    3. Audit-PDF erstellen und als Anhang anhängen
    4. E-Mail an Lead-Adresse senden
    5. Lead-Status auf 'kontaktiert' setzen
    """
    import re as _re
    import tempfile
    import os as _os

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")
    if not lead.email:
        raise HTTPException(400, "Lead hat keine E-Mail-Adresse")
    if not lead.website_url:
        raise HTTPException(400, "Lead hat keine Website-URL — Audit nicht möglich")

    # Neuesten abgeschlossenen Audit laden
    audit = db.execute(
        text("""
            SELECT id, total_score, ai_summary, top_issues,
                   company_name, website_url, city, trade, level,
                   erkannte_branche, branchenklasse
            FROM audit_results
            WHERE lead_id = :lid AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"lid": lead_id},
    ).fetchone()

    if not audit:
        return {
            "success": False,
            "status":  "no_audit",
            "message": (
                "Kein abgeschlossener Audit vorhanden. "
                "Bitte zuerst einen Audit starten und warten bis er fertig ist."
            ),
        }

    audit_id    = audit[0]
    total_score = audit[1] or 0
    company     = audit[4] or lead.company_name or "Ihr Unternehmen"
    city        = audit[6] or lead.city or ""
    # Was in diesem Brief als Branche steht, liest der Empfänger als unsere
    # Einschätzung seiner Firma. `trade` ist bei den meisten Leads geraten
    # (Stichwortsuche über den Seitentext), und `or lead.trade` holte die
    # Vermutung selbst dann noch, wenn der Audit sie bewusst leer gelassen
    # hatte. Ein Ingenieurbüro wurde so als „Schreiner" angeschrieben — mit
    # dem Auditprotokoll im Anhang, das korrekt „Ingenieurbüro" sagte.
    # Hier gilt dieselbe Rangfolge wie im Protokoll: Befund vor Vermutung,
    # und wo nichts erhoben ist, das neutrale Wort.
    branche     = branche_fuer_protokoll({
        "erkannte_branche": audit[9],
        "branchenklasse":   audit[10],
        "trade":            "",
    })
    trade       = "Handwerksbetrieb" if branche == "k.A." else branche

    top_issues = []
    try:
        raw = audit[3]
        if raw:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            top_issues = parsed[:3] if isinstance(parsed, list) else []
    except Exception:
        pass

    # DB vor KI-Call freigeben
    db.close()

    # ── KI-Anschreiben generieren ─────────────────────────────────────────
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY fehlt")

    level_label = (
        "kritisch" if total_score < 40
        else "verbesserungswürdig" if total_score < 70
        else "gut"
    )
    issues_text = (
        "\n".join(f"- {issue}" for issue in top_issues)
        if top_issues
        else f"- Gesamt-Score nur {total_score}/100 Punkte"
    )

    prompt = f"""Du schreibst ein professionelles, kurzes Akquise-Anschreiben für einen Webdesign-Dienstleister.

EMPFÄNGER:
- Firma: {company}
- Branche: {trade}
- Stadt: {city}
- Website-Score: {total_score}/100 (Bewertung: {level_label})

TOP-PROBLEME DER WEBSITE:
{issues_text}

ABSENDER: KOMPAGNON Communications — Website-Agentur für Handwerksbetriebe

REGELN FÜR DAS ANSCHREIBEN:
- Ton: professionell, direkt, kein Werbe-Jargon
- Länge: maximal 120 Wörter im Haupttext
- Keine Floskeln wie "Sehr geehrte Damen und Herren" — direkt ansprechen
- Konkret auf die gefundenen Probleme eingehen (nicht generisch)
- Einen klaren nächsten Schritt nennen (kostenloses Erstgespräch)
- Kein HTML — nur plain text für den Briefkopf

Antworte NUR mit einem JSON-Objekt:
{{
  "betreff": "<E-Mail-Betreffzeile, max 70 Zeichen>",
  "anrede": "<z.B. Guten Tag, Team {company},>",
  "haupttext": "<Der eigentliche Anschreiben-Text, max 120 Wörter>",
  "cta": "<Abschluss mit Handlungsaufforderung, 1-2 Sätze>"
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
                    "max_tokens": 800,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        raw_text = resp.json()["content"][0]["text"].strip()
        raw_text = _re.sub(r"^```json\s*", "", raw_text)
        raw_text = _re.sub(r"\s*```$", "", raw_text)
        letter = json.loads(raw_text)
    except Exception as e:
        raise HTTPException(500, f"KI-Anschreiben fehlgeschlagen: {str(e)[:200]}")

    betreff   = letter.get("betreff", f"Ihre Website — wir haben sie analysiert")
    anrede    = letter.get("anrede",  f"Guten Tag, Team {company},")
    haupttext = letter.get("haupttext", "")
    cta       = letter.get("cta", "Wir freuen uns auf Ihre Rückmeldung.")

    # ── Audit-PDF erstellen ───────────────────────────────────────────────
    pdf_path = None
    db2 = SessionLocal()
    try:
        audit_obj = db2.execute(
            text("SELECT * FROM audit_results WHERE id = :id"),
            {"id": audit_id},
        ).fetchone()
        if audit_obj:
            from services.pdf_generator import generate_audit_report
            audit_dict = dict(audit_obj._mapping)
            pdf_bytes = generate_audit_report(audit_dict)
            tmp = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False, prefix=f"audit_{lead_id}_"
            )
            tmp.write(pdf_bytes)
            tmp.close()
            pdf_path = tmp.name
    except Exception as pdf_err:
        logger.warning(f"Kaltakquise: Audit-PDF konnte nicht erstellt werden: {pdf_err}")
    finally:
        db2.close()

    # ── HTML-E-Mail aufbauen ──────────────────────────────────────────────
    html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#1a2332;">
  <div style="background:#008EAA;padding:20px 24px;border-radius:8px 8px 0 0;">
    <div style="color:#fff;font-size:18px;font-weight:700;">KOMPAGNON</div>
    <div style="color:rgba(255,255,255,.7);font-size:12px;">Website-Optimierung für Handwerksbetriebe</div>
  </div>
  <div style="padding:28px 24px;background:#fff;border:1px solid #e2e8f0;border-top:none;">
    <p style="margin:0 0 16px;font-size:15px;font-weight:500;">{anrede}</p>
    <div style="font-size:14px;line-height:1.7;color:#374151;white-space:pre-line;">{haupttext}</div>
    <div style="background:#FEF3C7;border-left:4px solid #D97706;
                padding:14px 16px;margin:20px 0;border-radius:0 6px 6px 0;">
      <div style="font-size:12px;font-weight:700;color:#92400E;margin-bottom:6px;">
        Ihre Website {lead.website_url} — Analyse-Ergebnis
      </div>
      <div style="font-size:22px;font-weight:800;color:#92400E;">{total_score}/100 Punkte</div>
      <div style="font-size:12px;color:#92400E;margin-top:4px;">
        Den vollständigen Bericht finden Sie im Anhang.
      </div>
    </div>
    <p style="font-size:14px;line-height:1.7;color:#374151;">{cta}</p>
    <div style="margin-top:24px;padding-top:20px;border-top:1px solid #e2e8f0;
                font-size:12px;color:#6B7280;">
      <strong>KOMPAGNON Communications</strong><br>
      Website-Optimierung · Handwerksbetriebe
    </div>
  </div>
</div>"""

    # ── E-Mail senden ─────────────────────────────────────────────────────
    from services.email import send_email as _send_kalt_email
    ok = _send_kalt_email(
        to_email=lead.email,
        subject=betreff,
        html_body=html_body,
        attachment_path=pdf_path,
        attachment_name=f"Website-Analyse-{company.replace(' ', '-')}.pdf",
    )

    if pdf_path and _os.path.exists(pdf_path):
        try:
            _os.unlink(pdf_path)
        except Exception:
            pass

    if not ok:
        raise HTTPException(500, "E-Mail-Versand fehlgeschlagen — SMTP-Konfiguration prüfen")

    # ── Lead-Status aktualisieren ─────────────────────────────────────────
    db3 = SessionLocal()
    try:
        db3.execute(
            text("""
                UPDATE leads SET
                    status = 'kontaktiert',
                    kaltakquise_gesendet_at = NOW(),
                    kaltakquise_count = COALESCE(kaltakquise_count, 0) + 1
                WHERE id = :lid
            """),
            {"lid": lead_id},
        )
        db3.commit()
    except Exception as upd_err:
        logger.warning(f"Kaltakquise Lead-Status Update fehlgeschlagen: {upd_err}")
        try:
            db3.rollback()
        except Exception:
            pass
    finally:
        db3.close()

    logger.info(f"✓ Kaltakquise gesendet: Lead {lead_id} → {lead.email} (Score: {total_score})")

    return {
        "success":       True,
        "email_sent_to": lead.email,
        "audit_score":   total_score,
        "betreff":       betreff,
        "with_pdf":      pdf_path is not None,
    }
