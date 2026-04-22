"""
GEO/GAIO Monitor — monatlicher Check der KI-Sichtbarkeit.

Laeuft als geplanter Job (Scheduler) einmal pro Monat.
Prueft alle Projekte mit aktiver GEO-Analyse und sendet Admin-Bericht.

KRITISCH: Dieser Service erstellt IMMER eigene DB-Sessions.
Niemals eine Request-Session von FastAPI wiederverwenden.
"""

import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


async def run_monthly_geo_check() -> dict:
    """Hauptfunktion: Prueft alle aktiven GEO-Analysen und erstellt Bericht."""
    from database import SessionLocal, GeoAnalysis, Project

    logger.info("GEO Monitoring: Monatlicher Check gestartet — %s", datetime.utcnow())
    results = {"checked": 0, "improved": 0, "declined": 0, "unchanged": 0, "errors": 0}

    db = SessionLocal()
    try:
        analyses = (
            db.query(GeoAnalysis)
            .filter(
                GeoAnalysis.status == "done",
                GeoAnalysis.monitoring_enabled == True,
            )
            .all()
        )
        analysis_ids = [a.id for a in analyses]
    finally:
        db.close()

    logger.info("GEO Monitoring: %d Analysen zu pruefen", len(analysis_ids))

    project_reports = []

    for analysis_id in analysis_ids:
        try:
            db = SessionLocal()
            try:
                analysis = db.query(GeoAnalysis).filter(GeoAnalysis.id == analysis_id).first()
                if not analysis:
                    continue
                project = db.query(Project).filter(Project.id == analysis.project_id).first()
                if not project or not project.lead:
                    continue
                lead = project.lead
                website_url = getattr(lead, "website_url", "") or ""
                company_name = getattr(lead, "company_name", "Unbekannt")
                old_score = analysis.geo_score_total or 0
            finally:
                db.close()

            if not website_url:
                continue

            new_score = await _quick_geo_check(website_url)
            score_change = new_score - old_score

            db = SessionLocal()
            try:
                analysis = db.query(GeoAnalysis).filter(GeoAnalysis.id == analysis_id).first()
                if not analysis:
                    continue

                history = analysis.monitoring_history or []
                history.append({
                    "date": datetime.utcnow().isoformat(),
                    "score": new_score,
                    "change": score_change,
                })
                analysis.monitoring_history = history[-24:]
                analysis.last_monitored_at = datetime.utcnow()
                analysis.last_score_change = score_change

                if abs(score_change) > 5:
                    analysis.geo_score_total = new_score

                db.commit()
            finally:
                db.close()

            status = "verbessert" if score_change > 5 else "verschlechtert" if score_change < -5 else "stabil"
            if score_change > 5:
                results["improved"] += 1
            elif score_change < -5:
                results["declined"] += 1
            else:
                results["unchanged"] += 1

            project_reports.append({
                "company": company_name,
                "old_score": old_score,
                "new_score": new_score,
                "change": score_change,
                "status": status,
            })
            results["checked"] += 1

        except Exception as e:
            logger.error("GEO Monitoring: Fehler bei Analyse %s: %s", analysis_id, e)
            results["errors"] += 1

    if project_reports:
        try:
            await _send_monitoring_report(project_reports, results)
        except Exception as e:
            logger.error("GEO Monitoring: Report-Versand fehlgeschlagen: %s", e)

    logger.info("GEO Monitoring: Abgeschlossen — %s", results)
    return results


async def _quick_geo_check(website_url: str) -> int:
    """Schneller GEO-Check ohne KI (nur technische Signale). Score 0-100."""
    import httpx
    score = 0

    try:
        base_url = website_url.rstrip("/")
        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # 1. llms.txt vorhanden? (25 P)
            try:
                resp = await client.get(f"{base_url}/llms.txt")
                if resp.status_code == 200 and len(resp.text) > 50:
                    score += 25
            except Exception:
                pass

            # 2. robots.txt KI-freundlich? (25 P)
            try:
                resp = await client.get(f"{base_url}/robots.txt")
                if resp.status_code != 200:
                    score += 25
                else:
                    content = resp.text
                    ai_bots = ["GPTBot", "PerplexityBot", "ClaudeBot"]
                    blocked = False
                    lines = content.split("\n")
                    current_agent = None
                    for line in lines:
                        if line.lower().startswith("user-agent:"):
                            current_agent = line.split(":", 1)[1].strip()
                        elif line.lower().startswith("disallow:") and current_agent in ai_bots:
                            if line.split(":", 1)[1].strip() in ("/", "/*"):
                                blocked = True
                                break
                    if not blocked:
                        score += 25
            except Exception:
                score += 15

            # 3. schema.org auf Homepage? (30 P)
            try:
                resp = await client.get(base_url)
                if resp.status_code == 200:
                    if '"@type"' in resp.text and "LocalBusiness" in resp.text:
                        score += 30
                    elif '"@type"' in resp.text:
                        score += 15
            except Exception:
                pass

            # 4. Website erreichbar? (20 P)
            try:
                resp = await client.get(base_url)
                if resp.status_code == 200:
                    score += 20
                elif resp.status_code < 400:
                    score += 10
            except Exception:
                pass

    except Exception as e:
        logger.warning("Quick GEO check failed for %s: %s", website_url, e)
        return 0

    return min(score, 100)


async def _send_monitoring_report(project_reports: list, summary: dict):
    """Sendet den monatlichen GEO-Report per E-Mail an den Admin."""
    try:
        from services.email import send_email
    except ImportError:
        logger.warning("GEO Monitoring: services.email nicht verfuegbar")
        return

    admin_email = os.getenv("ADMIN_EMAIL", "")
    if not admin_email:
        logger.warning("GEO Monitoring: ADMIN_EMAIL nicht gesetzt — kein Report")
        return

    rows_html = ""
    for p in project_reports:
        change_str = f"+{p['change']}" if p['change'] > 0 else str(p['change'])
        color = "#16a34a" if p['change'] > 5 else "#dc2626" if p['change'] < -5 else "#64748b"
        rows_html += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb">{p['company']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right">{p['old_score']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right">{p['new_score']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right;color:{color};font-weight:600">{change_str}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb">{p['status']}</td>
        </tr>"""

    html = f"""
<div style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto">
  <div style="background:#008eaa;padding:24px;border-radius:12px 12px 0 0">
    <h2 style="color:white;margin:0">KOMPAGNON — Monatlicher GEO-Report</h2>
    <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:13px">
      Erstellt am: {datetime.utcnow().strftime('%d.%m.%Y')}
    </p>
  </div>
  <div style="padding:24px;background:#fff;border:1px solid #e5e7eb">
    <h3 style="color:#1a2332;margin:0 0 12px">Zusammenfassung</h3>
    <table style="width:100%;font-size:14px;color:#475569;margin-bottom:24px">
      <tr><td>Geprueft:</td><td><strong>{summary['checked']}</strong></td></tr>
      <tr><td>Verbessert (&gt; +5):</td><td style="color:#16a34a"><strong>{summary['improved']}</strong></td></tr>
      <tr><td>Stabil:</td><td><strong>{summary['unchanged']}</strong></td></tr>
      <tr><td>Verschlechtert:</td><td style="color:#dc2626"><strong>{summary['declined']}</strong></td></tr>
      <tr><td>Fehler:</td><td>{summary['errors']}</td></tr>
    </table>
    <h3 style="color:#1a2332;margin:0 0 12px">Projekte im Detail</h3>
    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <thead>
        <tr style="background:#f8f9fa">
          <th style="padding:8px 12px;text-align:left">Unternehmen</th>
          <th style="padding:8px 12px;text-align:right">Alt</th>
          <th style="padding:8px 12px;text-align:right">Neu</th>
          <th style="padding:8px 12px;text-align:right">Aenderung</th>
          <th style="padding:8px 12px;text-align:left">Status</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    <p style="font-size:12px;color:#94a3b8;margin-top:24px">
      Dieser Report wird automatisch von KOMPAGNON KAS erstellt.
      Projekte mit deutlicher Verschlechterung sollten zeitnah geprueft werden.
    </p>
  </div>
</div>"""

    ok = send_email(
        to_email=admin_email,
        subject=f"KOMPAGNON GEO-Report — {datetime.utcnow().strftime('%B %Y')}",
        html_body=html,
    )
    if ok:
        logger.info("GEO Monitoring: Report an %s versandt", admin_email)
    else:
        logger.warning("GEO Monitoring: Report-Versand an %s fehlgeschlagen", admin_email)
