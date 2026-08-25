"""
GEO/GAIO Router — Endpunkte fuer die KI-Sichtbarkeitsanalyse.

WICHTIG: Dieser Router registriert /api/geo/* Endpunkte.
Keine Ueberschneidung mit sitemap.py (registriert /api/sitemap/*).
"""

import asyncio
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db, GeoAnalysis, Project
from routers.auth_router import require_any_auth, require_admin, require_innendienst

logger = logging.getLogger(__name__)
# **Die Sperre haengt am Router (L-67, 22.08.2026).** Die fuenf Routen hier
# stossen Analysen an und lassen Dateien erzeugen — auf fremden Projekten,
# fuer jeden Angemeldeten.
#
# Vor der Sperre gemessen: `GeoOptimizerStep` ueber `KASSidebar` im
# `OnlineFertigEditor` (`roles={['admin','auditor']}`). `ProzessFlow.jsx`
# bindet es ebenfalls ein, haengt aber in keiner Seite mehr.
router = APIRouter(prefix="/api/geo", tags=["geo"],
                   dependencies=[Depends(require_innendienst)])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def _get_project_data(project_id: int, db: Session) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    lead = project.lead
    return {
        "website_url": getattr(lead, "website_url", "") or "",
        "gewerk": getattr(lead, "trade", "") or "Handwerk",
        "city": getattr(lead, "city", "") or "",
    }


@router.post("/{project_id}/analyze")
async def start_geo_analysis(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Startet GEO/GAIO Analyse fuer ein Projekt im Hintergrund."""
    project_data = _get_project_data(project_id, db)

    if not project_data["website_url"]:
        raise HTTPException(status_code=400, detail="Keine Website-URL im Projekt hinterlegt")

    analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not analysis:
        analysis = GeoAnalysis(project_id=project_id, status="pending")
        db.add(analysis)
    else:
        analysis.status = "pending"
        analysis.error_message = None

    db.commit()
    db.refresh(analysis)
    analysis_id = analysis.id

    background_tasks.add_task(
        _run_analysis_background,
        analysis_id,
        project_id,
        project_data["website_url"],
        project_data["gewerk"],
        project_data["city"],
    )

    return {
        "status": "gestartet",
        "analysis_id": analysis_id,
        "message": "GEO-Analyse laeuft im Hintergrund (~30 Sekunden)",
    }


async def _run_analysis_background(
    analysis_id: int,
    project_id: int,
    website_url: str,
    gewerk: str,
    city: str,
):
    """Hintergrundtask: GEO-Analyse mit eigenen DB-Sessions."""
    from database import SessionLocal
    from services.geo_optimizer import GeoOptimizerAgent

    db = SessionLocal()
    try:
        analysis = db.query(GeoAnalysis).filter(GeoAnalysis.id == analysis_id).first()
        if not analysis:
            return
        analysis.status = "running"
        db.commit()
    finally:
        db.close()

    try:
        agent = GeoOptimizerAgent(api_key=ANTHROPIC_API_KEY)
        result = await agent.analyze(website_url, gewerk, city)

        db = SessionLocal()
        try:
            analysis = db.query(GeoAnalysis).filter(GeoAnalysis.id == analysis_id).first()
            if analysis:
                analysis.geo_score_total = result["geo_score_total"]
                analysis.llms_txt_score = result["llms_txt_score"]
                analysis.robots_ai_score = result["robots_ai_score"]
                analysis.structured_data_score = result["structured_data_score"]
                analysis.content_depth_score = result["content_depth_score"]
                analysis.local_signal_score = result["local_signal_score"]
                analysis.raw_checks = result["raw_checks"]
                analysis.recommendations = result["recommendations"]
                analysis.status = "done"
                analysis.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"GEO-Analyse {analysis_id} abgeschlossen: Score {result['geo_score_total']}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"GEO analysis background task failed: {type(e).__name__}: {e}")
        try:
            db_err = SessionLocal()
            try:
                a = db_err.query(GeoAnalysis).filter(GeoAnalysis.id == analysis_id).first()
                if a:
                    a.status = "failed"
                    a.error_message = str(e)[:500]
                    db_err.commit()
            finally:
                db_err.close()
        except Exception:
            pass


@router.get("/{project_id}/result")
def get_geo_result(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Gibt das aktuelle GEO-Analyse-Ergebnis zurueck."""
    analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not analysis:
        return {"status": "not_started", "geo_score_total": None}

    return {
        "status": analysis.status,
        "geo_score_total": analysis.geo_score_total,
        "llms_txt_score": analysis.llms_txt_score,
        "robots_ai_score": analysis.robots_ai_score,
        "structured_data_score": analysis.structured_data_score,
        "content_depth_score": analysis.content_depth_score,
        "local_signal_score": analysis.local_signal_score,
        "recommendations": analysis.recommendations or [],
        "raw_checks": analysis.raw_checks or {},
        "upsell_active": analysis.upsell_active,
        "upsell_price": analysis.upsell_price,
        "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None,
        "error_message": analysis.error_message,
    }


@router.patch("/{project_id}/upsell")
def set_upsell(
    project_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Admin: Upsell-Paket aktivieren/deaktivieren und Preis setzen."""
    analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Noch keine GEO-Analyse vorhanden")

    if "upsell_active" in payload:
        analysis.upsell_active = bool(payload["upsell_active"])
    if "upsell_price" in payload:
        analysis.upsell_price = payload["upsell_price"]
    db.commit()

    return {
        "status": "ok",
        "upsell_active": analysis.upsell_active,
        "upsell_price": analysis.upsell_price,
    }


# ── Dateien generieren ───────────────────────────────────────────────────────

@router.post("/{project_id}/generate")
async def generate_geo_files(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Generiert alle GEO-Optimierungsdateien (llms.txt, schema.org, Ground Page)."""
    from services.geo_generator import GeoGeneratorAgent

    analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not analysis or analysis.status != "done":
        raise HTTPException(
            status_code=400,
            detail="Bitte zuerst GEO-Analyse abschliessen (POST /analyze)",
        )

    project_data = _get_project_data(project_id, db)
    project = db.query(Project).filter(Project.id == project_id).first()
    lead = project.lead

    briefing = {}
    try:
        from database import Briefing
        b = db.query(Briefing).filter(Briefing.lead_id == lead.id).first()
        if b:
            briefing = {
                "leistungen": getattr(b, "leistungen", "") or "",
                "usp": getattr(b, "usp", "") or "",
                "strasse": getattr(b, "strasse", "") or "",
                "plz": getattr(b, "plz", "") or "",
            }
    except Exception:
        pass

    leistungen = []
    raw = briefing.get("leistungen", "") or ""
    if raw:
        leistungen = [l.strip() for l in raw.split(",") if l.strip()]

    blocked_bots = []
    raw_checks = analysis.raw_checks or {}
    if raw_checks.get("robots_ai"):
        blocked_bots = raw_checks["robots_ai"].get("blocked_bots", [])

    generator = GeoGeneratorAgent(api_key=ANTHROPIC_API_KEY)
    # `generate_all` ist synchron und ruft das Modell zweimal. Direkt hier
    # aufgerufen stuende der Server so lange still — deshalb als Ganzes in
    # einen Arbeitsthread, statt jede Stufe einzeln umzubauen.
    files = await asyncio.to_thread(
        generator.generate_all,
        company_name=getattr(lead, "company_name", "") or "",
        gewerk=project_data["gewerk"],
        city=project_data["city"],
        leistungen=leistungen,
        usp=briefing.get("usp", ""),
        phone=getattr(lead, "phone", "") or "",
        email=getattr(lead, "email", "") or "",
        website_url=project_data["website_url"],
        street=briefing.get("strasse", "") or getattr(lead, "street", "") or "",
        postal_code=briefing.get("plz", "") or getattr(lead, "postal_code", "") or "",
        blocked_bots=blocked_bots,
    )

    analysis.generated_files = files
    analysis.updated_at = datetime.utcnow()
    db.commit()

    return {
        "status": "ok",
        "files_generated": list(files.keys()),
        "message": "Dateien generiert — im GEO-Tab abrufbar",
    }


@router.get("/{project_id}/files")
def get_geo_files(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Gibt alle generierten GEO-Dateien zurueck."""
    analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not analysis or not analysis.generated_files:
        return {"files": {}, "message": "Noch keine Dateien generiert"}
    return {"files": analysis.generated_files}


# ── Monitoring ────────────────────────────────────────────────────────────────

@router.get("/{project_id}/monitoring")
def get_monitoring_history(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Gibt die Monitoring-Historie zurueck (monatliche Score-Entwicklung)."""
    analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not analysis:
        return {"history": [], "monitoring_enabled": False}

    return {
        "history": analysis.monitoring_history or [],
        "monitoring_enabled": bool(analysis.monitoring_enabled),
        "last_monitored_at": analysis.last_monitored_at.isoformat() if analysis.last_monitored_at else None,
        "last_score_change": analysis.last_score_change,
    }


@router.patch("/{project_id}/monitoring/toggle")
def toggle_monitoring(
    project_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Admin: Monitoring fuer ein Projekt aktivieren oder deaktivieren."""
    analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Keine GEO-Analyse gefunden")

    if "enabled" in payload:
        analysis.monitoring_enabled = bool(payload["enabled"])
    db.commit()
    return {"status": "ok", "monitoring_enabled": bool(analysis.monitoring_enabled)}


@router.post("/admin/run-monitoring-now")
async def run_monitoring_manually(
    _=Depends(require_admin),
):
    """Admin: Monitoring sofort manuell ausloesen (fuer Tests)."""
    from services.geo_monitor import run_monthly_geo_check
    results = await run_monthly_geo_check()
    return {"status": "abgeschlossen", "results": results}


# ── Tatsaechliche KI-Sichtbarkeit (L-58 b, 22.08.2026) ───────────────────────
#
# Alles darueber misst die **Voraussetzungen**: llms.txt, offene Crawler,
# strukturierte Daten. Ob ChatGPT, Perplexity oder Claude den Betrieb auf eine
# Kundenfrage hin wirklich **nennen**, misst das nicht — und genau das verkauft
# GEO. Die Anbindung steht in `services/ki_anbieter.py`.
#
# `require_innendienst` statt des `require_any_auth` der Nachbarn: Jeder Lauf
# stellt echte Anfragen an fremde Modelle und kostet Geld. Das loest kein Kunde
# aus, auch nicht am eigenen Projekt.

@router.get("/ki-anbieter")
def ki_anbieter_stand(_=Depends(require_innendienst)):
    """Welche KI-Systeme angebunden sind — und welcher Schluessel fehlt.

    Ohne diese Auskunft merkt niemand, dass ein Schluessel in Render fehlt
    oder leer angelegt wurde: Der Lauf meldet dann brav „nicht erhoben", und
    das liest sich wie ein Ergebnis.

    Bewusst ohne Schluesselwerte — `/info` hat am 15.08.2026 schon einmal
    Zugangsdaten preisgegeben.
    """
    from services.ki_anbieter import anbieter_stand

    stand = anbieter_stand()
    return {
        "anbieter": stand,
        "angebunden": sum(1 for a in stand if a["konfiguriert"]),
        "von": len(stand),
    }


@router.post("/{project_id}/ki-sichtbarkeit")
async def pruefe_ki_sichtbarkeit_endpunkt(
    project_id: int,
    max_fragen: int = 3,
    db: Session = Depends(get_db),
    _=Depends(require_innendienst),
):
    """Fragt jedes angebundene System, ob es diesen Betrieb nennt.

    Laeuft **synchron** und dauert: je Frage eine echte Websuche. `max_fragen`
    begrenzt das nach oben; drei reichen fuer eine belastbare Aussage.

    Antwortet 503, wenn kein System angebunden ist — nicht 200 mit lauter
    Nullen. Ein Ergebnis, das aussieht wie „nirgends gefunden", waere eine
    Aussage ueber Systeme, die nie gefragt wurden.
    """
    from services.ki_anbieter import ANBIETER, konfigurierte_anbieter
    from services.ki_sichtbarkeit import (pruefe_ki_sichtbarkeit,
                                          verlauf_fortschreiben)

    daten = _get_project_data(project_id, db)

    if not konfigurierte_anbieter():
        fehlend = ", ".join(a.env_name for a in ANBIETER)
        raise HTTPException(
            503, f"Kein KI-System angebunden. Erwartet wird mindestens einer "
                 f"dieser Schluessel: {fehlend}")

    if not daten["city"]:
        raise HTTPException(
            400, "Am Betrieb fehlt der Ort. Ohne ihn misst die Frage einen "
                 "Markt, in dem der Betrieb nicht arbeitet.")

    projekt = db.query(Project).filter(Project.id == project_id).first()
    name = getattr(projekt.lead, "company_name", "") or ""

    befund = await pruefe_ki_sichtbarkeit(
        name=name,
        domain=daten["website_url"],
        gewerk=daten["gewerk"],
        ort=daten["city"],
        max_fragen=max(1, min(max_fragen, 5)),
    )

    analyse = db.query(GeoAnalysis).filter(
        GeoAnalysis.project_id == project_id).first()
    if not analyse:
        analyse = GeoAnalysis(project_id=project_id, status="pending")
        db.add(analyse)
    jetzt = datetime.utcnow()
    analyse.ki_sichtbarkeit = befund
    analyse.ki_sichtbarkeit_am = jetzt
    # Anhaengen statt ersetzen (L-85): Eine Momentaufnahme ist kein Produkt.
    analyse.ki_sichtbarkeit_verlauf = verlauf_fortschreiben(
        analyse.ki_sichtbarkeit_verlauf, befund, jetzt.isoformat(timespec="seconds"))
    db.commit()

    return {**befund, "verlauf_laenge": len(analyse.ki_sichtbarkeit_verlauf or [])}


@router.get("/{project_id}/wirkungsbericht")
def wirkungsbericht(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_innendienst),
):
    """Der Vergleich 60 Tage nach der Auslieferung (GEO-01, Position 7).

    Rechnet nur auf vorhandenen Daten — er kostet nichts und darf deshalb
    jederzeit abgerufen werden. Ist es zu frueh, sagt er das, statt eine
    Wirkung aus zwei Messpunkten zu behaupten.
    """
    from services.geo_wirkungsbericht import baue_wirkungsbericht, klartext

    analyse = db.query(GeoAnalysis).filter(
        GeoAnalysis.project_id == project_id).first()
    if not analyse:
        raise HTTPException(404, "Fuer dieses Projekt gibt es keine GEO-Analyse")

    bericht = baue_wirkungsbericht(analyse)
    return {**bericht, "klartext": klartext(bericht)}


@router.get("/{project_id}/ki-sichtbarkeit/verlauf")
def ki_sichtbarkeit_verlauf(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_innendienst),
):
    """Wie sich die Nennungen ueber die Laeufe entwickelt haben (L-85).

    Getrennt vom Lauf-Endpunkt, weil Lesen nichts kostet und Messen Geld.
    """
    analyse = db.query(GeoAnalysis).filter(
        GeoAnalysis.project_id == project_id).first()
    if not analyse:
        return {"verlauf": [], "zuletzt": None}

    return {
        "verlauf": analyse.ki_sichtbarkeit_verlauf or [],
        "zuletzt": analyse.ki_sichtbarkeit_am.isoformat()
                   if analyse.ki_sichtbarkeit_am else None,
    }
