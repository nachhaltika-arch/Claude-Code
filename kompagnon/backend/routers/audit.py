"""
Website Audit API routes.
POST /api/audit/start - Run full website audit
GET  /api/audit/{audit_id} - Get audit result
GET  /api/audit/lead/{lead_id} - All audits for a lead

Die Prüflogik liegt in services/audit_*: audit_criteria (Katalog),
audit_collectors + audit_pagespeed (Erhebung), audit_runner (Orchestrierung),
audit_scoring (Bewertung), audit_ai (subjektive Kriterien).
Dieser Router hält nur noch HTTP und Persistenz.
"""
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Optional
import secrets

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import AuditResult, Lead, User, get_db, SessionLocal
from routers.auth_router import optional_auth, require_innendienst
from services.audit_criteria import CATALOGUE, BLOCKER_LABELS, SOURCE_LABELS, Source
from services.ratenbegrenzung import audit_grenzen
from services.url_guard import check_url
# Die Aufbereitung der Antwort steht seit dem 23.08.2026 fuer sich (L-25):
# hundert Zeilen ohne eine einzige Route.
from routers.audit_darstellung import (_catalogue_payload, _format_audit,
                                       _json_field, _klassenbezeichnung)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])


#: Auf welche Stufe die Zahl im Werbetext abgerundet wird (L-65).
#: Zehner: „Über 340" bleibt ueber Wochen stehen und ist dabei immer wahr.
ANZEIGE_STUFE = 10


def analysen_zaehlen(db) -> int:
    """Wie viele Analysen es gibt — die Zahl hinter dem Werbetext."""
    from sqlalchemy import text as _text

    zeile = db.execute(_text("SELECT COUNT(*) FROM audit_results")).fetchone()
    return int(zeile[0] or 0)


@router.get("/analysen/anzahl")
def analysen_anzahl(db: Session = Depends(get_db)):
    """Wie viele Betriebe schon analysiert wurden (L-65).

    **Ohne Anmeldung**, weil das eingebettete Widget auf fremden Seiten
    laeuft. Herausgegeben wird **eine** aggregierte Zahl — kein Betrieb,
    keine Domain, kein Ergebnis. Beim Widget-Pentest am 12.08.2026 war genau
    das der Befund: Der Teaser gab jede Analyse aus.

    `anzeige` ist auf Zehner **abgerundet**. „Über 347 analysiert" liest sich
    wie ein Zaehlerstand und ist bei der naechsten Analyse falsch;
    abgerundet ist die Aussage immer wahr — es sind mindestens so viele.
    Aufrunden hiesse mehr behaupten, als geschehen ist.

    Faellt die Zaehlung aus, kommt `0` zurueck und **kein Fehler**: Das
    Widget haengt auf einer fremden Seite. Dann faellt der Satz weg, nicht
    das Widget.
    """
    try:
        gesamt = analysen_zaehlen(db)
    except Exception as fehler:  # noqa: BLE001 — der Satz darf fehlen, das Widget nicht
        logger.warning("Analysenzahl nicht ermittelbar (%s: %s)",
                       type(fehler).__name__, fehler)
        return {"analysen": 0, "anzeige": 0}

    return {"analysen": gesamt,
            "anzeige": (gesamt // ANZEIGE_STUFE) * ANZEIGE_STUFE}

# Vollständiges Audit: Mehrseiten-Crawl, PageSpeed und KI-Bewertung.
# Freigegeben am 2026-08-11 (vorher 90s — reichte nur für die Startseite).
AUDIT_TOTAL_TIMEOUT_SEC = 240


# ═══════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════

class AuditRequest(BaseModel):
    website_url: str
    company_name: str = ""
    contact_name: str = ""
    city: str = ""
    trade: str = ""
    lead_id: Optional[int] = None


class LinkLeadRequest(BaseModel):
    lead_id: int


# ═══════════════════════════════════════════════════════════
# Hilfsfunktionen
# ═══════════════════════════════════════════════════════════

def _normalise_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


# ═══════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════

def _run_with_timeout(fn, timeout_sec, *args, **kwargs):
    """
    Runs fn(*args, **kwargs) in a daemon thread.
    Raises TimeoutError if timeout_sec is exceeded.
    Re-raises any exception thrown inside the thread.
    """
    result = [None]
    error  = [None]

    def target():
        try:
            result[0] = fn(*args, **kwargs)
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout=timeout_sec)
    if t.is_alive():
        raise TimeoutError(f"Audit-Timeout nach {timeout_sec}s")
    if error[0]:
        raise error[0]
    return result[0]


async def _gather(url: str, company: str, trade: str, city: str) -> tuple:
    """Faktenerhebung und Screenshot in einem Event-Loop."""
    import asyncio

    from services.audit_runner import collect_facts

    async def _shot():
        try:
            from services.screenshot import capture_screenshot
            return await capture_screenshot(url)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Screenshot fehlgeschlagen für {url}: {e}")
            return None

    facts, screenshot = await asyncio.gather(
        collect_facts(url, company, trade, city, datetime.now(timezone.utc).year),
        _shot(),
        return_exceptions=True,
    )
    if isinstance(facts, BaseException):
        raise facts
    return facts, (screenshot if isinstance(screenshot, str) else None)


def _run_audit_background(audit_id: int):
    """Erhebt Fakten, bewertet sie und schreibt das Ergebnis.

    Die DB-Session wird vor den externen HTTP-Aufrufen geschlossen, damit der
    Verbindungspool nicht blockiert, während PageSpeed und die KI laufen.
    """
    import asyncio
    import time

    from services.audit_runner import collection_notes, summarise_facts
    from services.audit_scoring import score_audit
    from services import audit_ai

    _start = time.monotonic()
    db = SessionLocal()

    try:
        audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
        if not audit:
            return

        audit.status = "running"
        db.commit()

        url          = audit.website_url
        company_name = audit.company_name or ""
        trade        = audit.trade or ""
        city         = audit.city or ""
        lead_id      = audit.lead_id
    finally:
        db.close()

    # ── Erhebung: keine DB-Verbindung offen ────────────────────────────
    try:
        facts, screenshot_b64 = asyncio.run(_gather(url, company_name, trade, city))
    except Exception as e:  # noqa: BLE001
        _mark_failed(audit_id, f"Erhebung fehlgeschlagen: {type(e).__name__}: {e}"[:200])
        return

    if not facts.get("reachable"):
        _mark_failed(
            audit_id,
            facts.get("error")
            or f"Website nicht erreichbar (Status {facts.get('status_code', 'N/A')})",
        )
        return

    summary = summarise_facts(facts)

    # KI-Bewertung nur für die subjektiven Kriterien; schlägt sie fehl,
    # gelten diese als 'nicht erhoben' — es werden keine Werte erfunden.
    try:
        ai = _run_with_timeout(audit_ai.evaluate, 100, facts, summary, screenshot_b64) or {}
    except TimeoutError:
        logger.warning(f"Audit {audit_id}: KI-Bewertung Timeout")
        ai = {}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Audit {audit_id}: KI-Bewertung Fehler: {e}")
        ai = {}

    result = score_audit(facts, ai)

    # ── Persistenz in neuer Session ────────────────────────────────────
    db2 = SessionLocal()
    try:
        audit2 = db2.query(AuditResult).filter(AuditResult.id == audit_id).first()
        if not audit2:
            return

        audit2.total_score     = result["total_score"]
        audit2.level           = result["level"]
        audit2.item_scores     = json.dumps(result["items"], ensure_ascii=False)
        audit2.item_sources    = json.dumps(result["sources"], ensure_ascii=False)
        audit2.category_scores = json.dumps(result["categories"], ensure_ascii=False)
        audit2.blockers        = json.dumps(result["blockers"], ensure_ascii=False)
        audit2.coverage        = result["coverage"]

        # Der Umfang gehört zum Ergebnis, nicht ins Log: Ein Audit über 25 von
        # 400 Seiten sagt etwas anderes als eines über alle acht.
        audit2.seiten_geprueft = summary["seiten_geprueft"]
        audit2.seiten_gefunden = summary["seiten_gefunden"]
        audit2.collection_notes = json.dumps(collection_notes(facts, ai), ensure_ascii=False)

        # Wogegen bewertet wurde. Gehört zum Ergebnis, nicht in die Notizen:
        # Der Bericht nennt die Klasse im ersten Absatz, damit der Leser sieht,
        # dass sein Geschäft verstanden wurde, bevor er die Punktzahl liest.
        audit2.erkannte_branche  = (result.get("branche") or "")[:200]
        audit2.branchenklasse    = result.get("branchenklasse") or ""
        audit2.standard_version  = result.get("standard_version") or ""

        audit2.ssl_ok            = summary["ssl_ok"]
        audit2.impressum_ok      = summary["impressum_ok"]
        audit2.datenschutz_ok    = summary["datenschutz_ok"]
        audit2.lcp_value         = summary["lcp_value"]
        audit2.cls_value         = summary["cls_value"]
        audit2.inp_value         = summary["inp_value"]
        audit2.mobile_score      = summary["mobile_score"]
        audit2.performance_score = summary["performance_score"]

        # Die GEO-Spalten gab es seit jeher, befüllt hat sie niemand. Das PDF
        # las sie leer, wertete das als „nicht erfüllt" und verlangte etwa,
        # eine GPTBot-Sperre zu entfernen, die es gar nicht gab.
        audit2.llms_txt           = summary["llms_txt"]
        audit2.robots_ai_friendly = summary["robots_ai_friendly"]
        audit2.structured_data    = summary["structured_data"]

        audit2.ai_summary      = ai.get("ai_summary", "")
        audit2.top_issues      = json.dumps(ai.get("top_issues", []), ensure_ascii=False)
        audit2.recommendations = json.dumps(ai.get("recommendations", []), ensure_ascii=False)

        if screenshot_b64:
            audit2.screenshot_base64 = screenshot_b64
            if lead_id:
                lead = db2.query(Lead).filter(Lead.id == lead_id).first()
                if lead:
                    lead.website_screenshot = screenshot_b64

        audit2.status = "completed"
        db2.commit()

        logger.info(
            f"✓ Audit {audit_id}: {result['total_score']}/100 ({result['level']}), "
            f"Abdeckung {result['coverage']}%, "
            f"{len(result['blockers'])} Blocker, {time.monotonic() - _start:.1f}s"
        )

        _notify_customer(db2, lead_id, audit_id)
        _notify_widget_requester(db2, audit_id)
    except Exception as e:  # noqa: BLE001
        logger.error(f"✗ Audit {audit_id} Persistenz fehlgeschlagen: {type(e).__name__}: {e}")
        _mark_failed(audit_id, f"{type(e).__name__}: {e}"[:200])
    finally:
        db2.close()


def _mark_failed(audit_id: int, message: str) -> None:
    """Setzt ein Audit auf 'failed' — in eigener Session, damit es immer greift."""
    db = SessionLocal()
    try:
        audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
        if audit and audit.status in ("pending", "running"):
            audit.status = "failed"
            audit.error_message = message
            db.commit()
            logger.warning(f"Audit {audit_id} fehlgeschlagen: {message}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Audit {audit_id}: Fehlerstatus konnte nicht gesetzt werden: {e}")
    finally:
        db.close()


def _jetzt() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _notify_widget_requester(db, audit_id: int) -> None:
    """Bittet um Bestätigung der Adresse — mehr nicht.

    Diese Mail geht an eine Adresse, die niemand geprüft hat: die Eingabe im
    Widget muss dem Eintragenden nicht gehören. Sie enthält deshalb weder
    Punktzahl noch Mängel noch einen Link zum Bericht, nur die Frage, ob die
    Adresse stimmt. Der Bericht folgt in einer zweiten Mail, sobald der
    Empfänger bestätigt hat — siehe ``send_widget_report``.
    """
    try:
        from database import WidgetRequest
        from services import widget_report
        from services.email import send_email

        row = (
            db.query(WidgetRequest)
            .filter(WidgetRequest.audit_id == audit_id,
                    WidgetRequest.verify_sent_at.is_(None))
            .first()
        )
        if not row:
            return

        audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
        if not audit or audit.status != "completed":
            return

        subject, body = widget_report.verify_email(
            company=audit.company_name or row.website_url,
            verify_token=row.verify_token,
        )

        if send_email(to_email=row.email, subject=subject, html_body=body):
            row.verify_sent_at = _jetzt()
            db.commit()
            logger.info(f"Widget-Bestätigung angefragt bei {row.email} (Audit {audit_id})")
        else:
            logger.warning(f"Widget-Bestätigung nicht versendet (Audit {audit_id})")
    except Exception as e:  # noqa: BLE001 — Versandfehler darf das Audit nicht kippen
        logger.warning(f"Widget-Benachrichtigung fehlgeschlagen für Audit {audit_id}: {e}")


def send_widget_report(request_id: int) -> None:
    """Die zweite Mail: der Link zum Bericht, nach bestätigter Adresse.

    Wird aus dem Bestätigungs-Endpunkt heraus angestoßen und öffnet dafür
    eine eigene Sitzung — der Aufrufer hat seine schon geschlossen, wenn der
    Hintergrundauftrag läuft.
    """
    from database import SessionLocal, WidgetRequest
    from services import widget_report
    from services.email import send_email

    db = SessionLocal()
    try:
        row = db.query(WidgetRequest).filter(WidgetRequest.id == request_id).first()
        if not row or not row.verified_at or row.report_sent_at:
            return

        audit = db.query(AuditResult).filter(AuditResult.id == row.audit_id).first()
        if not audit or audit.status != "completed":
            logger.warning(f"Bericht für Anfrage {request_id} noch nicht fertig")
            return

        subject, body = widget_report.report_ready_email(
            company=audit.company_name or row.website_url,
            token=row.report_token,
            confirm_token=row.confirm_token if row.consent_marketing else None,
        )

        if send_email(to_email=row.email, subject=subject, html_body=body):
            row.report_sent_at = _jetzt()
            db.commit()
            logger.info(f"Widget-Bericht versendet an {row.email} (Anfrage {request_id})")
        else:
            logger.warning(f"Widget-Bericht nicht versendet (Anfrage {request_id})")
    except Exception as e:  # noqa: BLE001 — der Klick soll trotzdem quittiert werden
        logger.warning(f"Berichts-Mail fehlgeschlagen für Anfrage {request_id}: {e}")
    finally:
        db.close()


def _notify_customer(db, lead_id: Optional[int], audit_id: int) -> None:
    """E-Mail bei Audit-Abschluss — Fehler hier dürfen das Audit nicht kippen."""
    if not lead_id:
        return
    try:
        from database import Project

        project = db.query(Project).filter(Project.lead_id == lead_id).first()
        if not project:
            return
        to_email = getattr(project, "customer_email", None) or ""
        if getattr(project, "email_notifications_enabled", True) and to_email:
            company = getattr(project, "company_name", "") or f"Lead #{lead_id}"
            # Ohne Berichts-Token gibt es keine Adresse, die der Kunde ohne
            # Anmeldung öffnen könnte. Die Vorlage sagt dann, dass wir uns
            # melden, statt einen Bericht anzukündigen und keinen Weg zu nennen.
            from services.email import send_email
            from services.mail_vorlagen import audit_fertig_mail

            betreff, html_body = audit_fertig_mail(company)
            send_email(to_email=to_email, subject=betreff, html_body=html_body)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Audit-E-Mail fehlgeschlagen für Audit {audit_id}: {e}")


@router.get("/recent", dependencies=[Depends(require_innendienst)])
def get_recent_audits(
    limit: Optional[int] = 10,
    skip: Optional[int] = 0,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(optional_auth),
):
    """Return the most recent completed audits, newest first."""
    query = db.query(AuditResult).filter(AuditResult.status == "completed")
    # Kunde role: only own audits
    if current_user and current_user.role == "kunde":
        if not current_user.lead_id:
            return []
        query = query.filter(AuditResult.lead_id == current_user.lead_id)
    audits = (
        query
        .order_by(AuditResult.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": a.id,
            "website_url": a.website_url,
            "company_name": a.company_name,
            "total_score": a.total_score,
            "level": a.level,
            "lead_id": a.lead_id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in audits
    ]


@router.post("/start")
async def start_audit(
    req: AuditRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _grenzen=Depends(audit_grenzen),
):
    """Create audit record, auto-scrape website, and run checks in background."""
    url = _normalise_url(req.website_url)

    # Der Endpunkt ist öffentlich (Einbett-Widget). Ohne diese Prüfung könnte
    # jeder den Server interne Adressen abrufen lassen — vor dem Scrapen prüfen,
    # denn auch der Scraper holt die Seite ab.
    ok, reason = check_url(url)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Adresse nicht erlaubt: {reason}")

    # DB-Verbindung vor dem externen Scrape-Call freigeben
    db.close()

    # Auto-scrape website for company info (fast, < 5s) — OHNE offene DB-Verbindung
    scraped = {}
    try:
        from services.scraper import scrape_website
        scraped = await scrape_website(url)
    except Exception as e:
        logger.warning(f"Scraping failed for {url}: {e}")

    # Use scraped data as fallback when fields not provided
    from services.scraper import firmenname_fuer_audit

    company_name = firmenname_fuer_audit(
        req.company_name, scraped.get("company_name", ""), url)
    city = req.city or scraped.get("city", "")
    # Kein Rückfall auf `scraped["trade"]`: Der Scraper rät das Gewerk über
    # Stichworte — „holz" im Text genügt für „Schreiner". Als Arbeitshypothese
    # in einer Leadliste taugt das, im Audit nicht: Der Wert ging als „Gewerk"
    # in den KI-Prompt und stand als Befund im PDF-Protokoll. Die Branche
    # erkennt seit dem Branchenmodell 2026.2 das Modell selbst
    # (`erkannte_branche`).
    #
    # Dieser Satz stand hier ab dem 14.08. und war falsch: „was niemand
    # eingetragen hat, bleibt leer". Das Frontend trug es ein — `useAudit`
    # sendete `lead.trade` bei jedem aus einem Lead gestarteten Audit mit,
    # also auf dem Hauptweg. Geschützt war nur der Widget-Weg. Seit dem 16.08.
    # sendet das Frontend das Feld nicht mehr; hier bleibt es nur für Aufrufer,
    # die einen Wert wirklich von Hand setzen.
    trade = req.trade or ""

    # Neue DB-Session nur zum Speichern
    db2 = SessionLocal()
    try:
        audit = AuditResult(
            lead_id=req.lead_id,
            website_url=url,
            company_name=company_name,
            contact_name=req.contact_name,
            city=city,
            trade=trade,
            status="pending",
            scraped_phone=scraped.get("phone", ""),
            scraped_email=scraped.get("email", ""),
            scraped_description=scraped.get("meta_description", ""),
            # Das Geheimnis, mit dem der Interessent sein eigenes Ergebnis
            # abholt. Ohne es waere die Kennung eine fortlaufende Zahl (L-52).
            public_token=secrets.token_urlsafe(24),
        )
        db2.add(audit)
        db2.commit()
        db2.refresh(audit)
        audit_id = audit.id
        audit_token = audit.public_token
    finally:
        db2.close()

    # Kick off background processing with global timeout guard
    def _run_with_global_timeout(aid: int):
        try:
            _run_with_timeout(_run_audit_background, AUDIT_TOTAL_TIMEOUT_SEC, aid)
        except TimeoutError:
            logger.error(
                f"Audit {aid}: Gesamt-Timeout ({AUDIT_TOTAL_TIMEOUT_SEC}s) erreicht"
            )
            from database import SessionLocal as _SL
            _db = _SL()
            try:
                a = _db.query(AuditResult).filter(AuditResult.id == aid).first()
                if a and a.status == "running":
                    a.status = "failed"
                    a.error_message = (
                        f"Timeout: Audit konnte nicht in "
                        f"{AUDIT_TOTAL_TIMEOUT_SEC}s abgeschlossen werden."
                    )
                    _db.commit()
            finally:
                _db.close()
        except Exception as e:
            logger.error(f"Audit {aid}: Background-Fehler: {e}")

    background_tasks.add_task(_run_with_global_timeout, audit_id)

    return {
        "id": audit_id,
        "token": audit_token,
        "status": "pending",
        "scraped": {
            "company_name": company_name,
            "city": city,
            "trade": trade,
            "phone": scraped.get("phone", ""),
            "email": scraped.get("email", ""),
            "scraping_blocked": bool(scraped.get("_scraping_blocked", False)),
        },
        "message": "Audit gestartet. Ergebnis mit GET /api/audit/{id} abrufen.",
    }


def _audit_oder_404(db, audit_id: int, token: Optional[str], nutzer):
    """Das Audit — oder 404, wenn der Fragende es nichts angeht.

    Zwei Wege fuehren hier herein: der Innendienst mit Anmeldung, und die
    oeffentliche Landingpage mit dem Geheimnis, das sie beim Start bekommen
    hat. Alles andere bekommt 404 und nicht 403: Ob es ein Audit mit dieser
    Nummer gibt, ist bereits eine Auskunft.

    Bestandsdaten ohne Geheimnis sind damit nur angemeldet erreichbar. Das ist
    gewollt — ein Audit von gestern holt niemand mehr ueber die Landingpage ab.
    """
    audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit nicht gefunden")
    if nutzer is not None:
        return audit
    if audit.public_token and token and secrets.compare_digest(
            str(token), str(audit.public_token)):
        return audit
    raise HTTPException(status_code=404, detail="Audit nicht gefunden")


@router.get("/status/{audit_id}")
def get_audit_status(audit_id: int, db: Session = Depends(get_db),
                     token: Optional[str] = None,
                     nutzer=Depends(optional_auth)):
    """Poll audit status (pending / running / completed / failed)."""
    audit = _audit_oder_404(db, audit_id, token, nutzer)
    result = {"id": audit.id, "status": audit.status}
    if audit.status == "failed":
        result["error"] = audit.error_message
    if audit.status == "completed":
        result["data"] = _format_audit(audit)
    return result


@router.get("/{audit_id}/pdf", dependencies=[Depends(require_innendienst)])
def download_audit_pdf(audit_id: int, db: Session = Depends(get_db)):
    """Download audit result as PDF report."""
    try:
        audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
        if not audit:
            raise HTTPException(status_code=404, detail="Audit nicht gefunden")
        if audit.status != "completed":
            raise HTTPException(status_code=400, detail=f"Audit noch nicht abgeschlossen: {audit.status}")

        from services.pdf_generator import KatalogFehlt, generate_audit_report

        try:
            pdf_bytes = generate_audit_report(audit.__dict__)
        except KatalogFehlt as e:
            raise HTTPException(status_code=409, detail=str(e))

        safe_name = (audit.company_name or "Audit").replace(" ", "-").replace("/", "-")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="Homepage-Standard-Audit-{safe_name}-{audit.id}.pdf"'
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"PDF generation failed for audit {audit_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PDF-Generierung fehlgeschlagen: {str(e)}")


@router.get("/{audit_id}/angebot", dependencies=[Depends(require_innendienst)])
def download_angebot_pdf(audit_id: int, db: Session = Depends(get_db)):
    """Angebots-PDF für ein abgeschlossenes Audit herunterladen."""
    try:
        audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
        if not audit:
            raise HTTPException(status_code=404, detail="Audit nicht gefunden")
        if audit.status != "completed":
            raise HTTPException(status_code=400, detail=f"Audit noch nicht abgeschlossen: {audit.status}")

        from services.angebot_pdf import generate_angebot_pdf
        pdf_bytes = generate_angebot_pdf(audit.__dict__)

        safe_name = (audit.company_name or "Angebot").replace(" ", "-").replace("/", "-")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="Angebot-KOMPAGNON-{safe_name}.pdf"'
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Angebots-PDF Generierung fehlgeschlagen für Audit {audit_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Angebots-PDF-Generierung fehlgeschlagen: {str(e)}")


@router.get("/{audit_id}")
def get_audit(audit_id: int, db: Session = Depends(get_db),
              token: Optional[str] = None,
              nutzer=Depends(optional_auth)):
    """Get a stored audit result."""
    try:
        audit = _audit_oder_404(db, audit_id, token, nutzer)
        if audit.status == "pending" or audit.status == "running":
            return {"id": audit.id, "status": audit.status, "message": "Audit läuft noch..."}
        if audit.status == "failed":
            return {"id": audit.id, "status": "failed", "message": audit.error_message or "Audit fehlgeschlagen",
                    "total_score": 0, "level": "", "website_url": audit.website_url or ""}
        return _format_audit(audit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Audit {audit_id} Fehler: {e}')
        raise HTTPException(status_code=500, detail=f'Audit konnte nicht geladen werden: {str(e)}')


@router.delete("/{audit_id}", dependencies=[Depends(require_innendienst)])
def delete_audit(audit_id: int, db: Session = Depends(get_db)):
    """Delete a single audit. Updates lead screenshot if needed."""
    audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit nicht gefunden")
    lead_id = audit.lead_id
    db.delete(audit)
    db.commit()
    # Update lead screenshot from remaining audits
    if lead_id:
        remaining = db.query(AuditResult).filter(
            AuditResult.lead_id == lead_id, AuditResult.status == "completed"
        ).order_by(AuditResult.created_at.desc()).first()
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.website_screenshot = remaining.screenshot_base64 if remaining and getattr(remaining, 'screenshot_base64', None) else ""
            db.commit()
    return {"success": True, "message": "Audit geloescht"}


@router.patch("/{audit_id}/link-lead", dependencies=[Depends(require_innendienst)])
def link_audit_to_lead(audit_id: int, req: LinkLeadRequest, db: Session = Depends(get_db)):
    """Link an existing audit to a lead."""
    audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit nicht gefunden")
    lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")
    audit.lead_id = req.lead_id
    db.commit()
    return {"id": audit.id, "lead_id": req.lead_id, "message": "Audit mit Lead verknüpft"}


@router.get("/lead/{lead_id}", dependencies=[Depends(require_innendienst)])
def get_audits_for_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get all audits for a specific lead."""
    audits = (
        db.query(AuditResult)
        .filter(AuditResult.lead_id == lead_id)
        .order_by(AuditResult.created_at.desc())
        .all()
    )
    return [_format_audit(a) for a in audits]
