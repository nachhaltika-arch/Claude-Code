"""Der Monatsbericht an den Kunden (L-25).

**Warum eigene Datei, 22.08.2026.** `automations/scheduler.py` hatte 1.468
Zeilen und darin vier Dinge: die Zeitsteuerung selbst, die Kundenmails, die
technische Ueberwachung und den Monatsbericht. Fuenf Funktionen, zusammen 335 Zeilen: messen, kommentieren lassen, die
Mail bauen. Allein das Mail-Layout ist 111 Zeilen.

Transitiv gemessen, ohne die Infrastruktur — die Klasse `CompagnonScheduler`
nennt **jeden** Auftragsnamen, und eine Messung, die ueber sie laeuft, zieht
darum die ganze Datei nach. Das war der erste Anlauf: 1.328 von 1.468
Zeilen, was offensichtlich falsch war.
"""
from datetime import datetime, timedelta
from database import SessionLocal, Project, Communication, DATABASE_URL
from services import leistungsbericht
from services.audit_pagespeed import (
    PSI_ENDPOINT,
    api_key as pagespeed_api_key,
    auth_headers as pagespeed_auth_headers,
)
import os
import logging

logger = logging.getLogger(__name__)


def job_monthly_performance_report():
    """
    Monatlicher Performance-Report: am 1. jeden Monats für alle aktiven Kunden.
    Misst PageSpeed neu, vergleicht mit Vormonat, sendet E-Mail mit KI-Kommentar.
    """
    from sqlalchemy import text
    from services.email import send_email as _send_report_email

    logger.info("📊 Monatlicher Performance-Report gestartet...")

    db = SessionLocal()
    try:
        leads = db.execute(text("""
            SELECT
                l.id,
                l.email,
                l.company_name,
                l.website_url,
                l.pagespeed_mobile_score,
                l.pagespeed_desktop_score,
                l.pagespeed_checked_at,
                l.perf_report_last_mobile,
                l.perf_report_last_desktop,
                l.perf_report_sent_count
            FROM leads l
            WHERE l.email IS NOT NULL
              AND l.email != ''
              AND l.website_url IS NOT NULL
              AND l.website_url != ''
              AND (
                  l.actual_go_live IS NOT NULL
                  OR EXISTS (
                      SELECT 1 FROM projects p
                      WHERE p.lead_id = l.id
                        AND p.netlify_domain_status = 'active'
                  )
              )
        """)).fetchall()

        logger.info(f"Performance-Report: {len(leads)} aktive Kunden gefunden")
        sent_count = 0

        for row in leads:
            lead_id         = row[0]
            email           = row[1]
            company         = row[2] or "Ihr Unternehmen"
            website_url     = row[3]
            current_mobile  = row[4]
            current_desktop = row[5]
            last_mobile     = row[7]
            last_desktop    = row[8]
            report_count    = row[9] or 0

            try:
                api_key = pagespeed_api_key()
                new_mobile, new_desktop = current_mobile, current_desktop

                if api_key and website_url:
                    try:
                        new_mobile, new_desktop = _measure_pagespeed_sync(website_url)
                    except Exception as ps_err:
                        logger.warning(f"PageSpeed-Messung fehlgeschlagen für Lead {lead_id}: {ps_err}")

                if new_mobile is None:
                    logger.info(f"Überspringe Lead {lead_id} — kein PageSpeed-Score")
                    continue

                mobile_diff = (new_mobile - last_mobile) if (last_mobile is not None) else None

                ki_kommentar = _generate_perf_comment(
                    company, website_url, new_mobile, new_desktop or 0, last_mobile, mobile_diff
                )

                upsell = new_mobile < 70

                html_body = _build_report_email(
                    company=company,
                    website_url=website_url,
                    mobile=new_mobile,
                    desktop=new_desktop,
                    last_mobile=last_mobile,
                    mobile_diff=mobile_diff,
                    ki_kommentar=ki_kommentar,
                    upsell=upsell,
                    report_count=report_count + 1,
                )

                trend_emoji = (
                    "📈" if (mobile_diff or 0) > 2
                    else "📉" if (mobile_diff or 0) < -2
                    else "📊"
                )
                month = datetime.utcnow().strftime("%B %Y")
                subject = f"{trend_emoji} Ihr Website-Report {month} — Score: {new_mobile}/100"

                ok = _send_report_email(to_email=email, subject=subject, html_body=html_body)

                # **Gemessen ist gemessen — auch wenn die Mail nicht ankam**
                # (04.09.2026, L-160 Rang 2). Bis hierhin stand die ganze
                # Speicherung hinter `if ok:`. Eine gescheiterte Zustellung
                # warf damit die Messung weg, und der naechste Monat verglich
                # gegen einen veralteten Stand — ein stiller Fehler in einer
                # Zahl, die der Kunde zu sehen bekommt.
                #
                # Der Bericht wird deshalb **immer** geschrieben; ob er
                # hinausging, steht als eigenes Feld daneben.
                try:
                    leistungsbericht.schreibe(
                        db, lead_id=lead_id,
                        monat=leistungsbericht.monat_von(),
                        mobile=new_mobile, desktop=new_desktop,
                        vormonat_mobile=last_mobile, versendet=bool(ok))
                except Exception as schreib_err:  # noqa: BLE001
                    # Ein Fehler beim Ablegen darf den Lauf fuer die anderen
                    # Betriebe nicht beenden — und er darf auch nicht dazu
                    # fuehren, dass eine bereits versandte Mail als nicht
                    # versandt gilt.
                    logger.warning("Leistungsbericht Lead %s nicht abgelegt: %s",
                                   lead_id, schreib_err)

                if ok:
                    db.execute(text("""
                        UPDATE leads SET
                            pagespeed_mobile_score   = :mobile,
                            pagespeed_desktop_score  = :desktop,
                            pagespeed_checked_at     = NOW(),
                            perf_report_last_mobile  = :mobile,
                            perf_report_last_desktop = :desktop,
                            perf_report_sent_at      = NOW(),
                            perf_report_sent_count   = COALESCE(perf_report_sent_count, 0) + 1
                        WHERE id = :lid
                    """), {"mobile": new_mobile, "desktop": new_desktop, "lid": lead_id})
                    sent_count += 1
                    logger.info(
                        f"✓ Performance-Report gesendet: Lead {lead_id} "
                        f"({email}) Score: {new_mobile}/100"
                    )
                else:
                    # Die Messung steht, die Mail nicht. Beides gehoert ins
                    # Protokoll, sonst sieht ein stiller Ausfall wie ein
                    # uebersprungener Betrieb aus.
                    logger.warning("Performance-Report NICHT zugestellt: Lead %s (%s) "
                                   "— Messung ist abgelegt", lead_id, email)

            except Exception as lead_err:
                logger.warning(f"Performance-Report Lead {lead_id} Fehler: {lead_err}")
                continue

        db.commit()
        logger.info(f"✓ Performance-Report abgeschlossen: {sent_count}/{len(leads)} gesendet")

    except Exception as e:
        logger.error(f"Performance-Report Fehler: {e}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


def _measure_pagespeed_sync(url: str):
    """Synchrone PageSpeed-Messung für den Scheduler-Thread."""
    import httpx as _httpx
    results = []
    for strategy in ("mobile", "desktop"):
        try:
            # Schluessel als Kopfzeile, nicht in der URL — httpx protokolliert
            # die vollstaendige Anfrage-URL (L-98).
            resp = _httpx.get(
                PSI_ENDPOINT,
                params={
                    "url": url,
                    "strategy": strategy,
                    "category": "performance",
                },
                headers=pagespeed_auth_headers(),
                timeout=30.0,
            )
            if resp.is_success:
                data = resp.json()
                score = (data.get("lighthouseResult", {})
                             .get("categories", {})
                             .get("performance", {})
                             .get("score"))
                results.append(int(score * 100) if score is not None else None)
            else:
                results.append(None)
        except Exception:
            results.append(None)
    return results[0], results[1]


def _generate_perf_comment(company, url, mobile, desktop, last_mobile, diff) -> str:
    """Kurzer KI-Kommentar für den Performance-Report. Fällt auf Fallback zurück."""
    import httpx as _httpx

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_perf_comment(mobile, diff)

    if diff is not None:
        trend_text = (
            f"verbessert um {diff} Punkte" if diff > 2
            else f"verschlechtert um {abs(diff)} Punkte" if diff < -2
            else "stabil geblieben"
        )
    else:
        trend_text = "erste Messung"

    prompt = (
        f"Schreibe 2-3 Sätze als freundlicher Website-Berater für diesen Monatsbericht.\n"
        f"Firma: {company} | Website: {url}\n"
        f"PageSpeed Mobil: {mobile}/100 | Desktop: {desktop}/100\n"
        f"Trend: {trend_text}\n\n"
        f"Ton: professionell, kurz, konkret. Ein positiver Aspekt, ein Verbesserungshinweis.\n"
        f"Max 60 Wörter. Kein HTML. Nur der Text."
    )

    try:
        resp = _httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-5", "thinking": {"type": "disabled"},
                "max_tokens": 150,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20.0,
        )
        if resp.is_success:
            return resp.json()["content"][0]["text"].strip()
    except Exception:
        pass

    return _fallback_perf_comment(mobile, diff)


def _fallback_perf_comment(mobile: int, diff) -> str:
    if (mobile or 0) >= 85:
        return (
            "Ihre Website performt ausgezeichnet. "
            "Der hohe Score sorgt für bessere Google-Rankings "
            "und schnellere Ladezeiten für Ihre Besucher."
        )
    elif (mobile or 0) >= 70:
        return (
            "Ihre Website läuft gut. "
            "Mit einigen Optimierungen — etwa Bildkomprimierung — "
            "lässt sich der Score noch weiter verbessern."
        )
    return (
        "Ihre Website hat Optimierungsbedarf. "
        "Ein niedriger PageSpeed-Score kann sich negativ auf "
        "Google-Rankings und Absprungrate auswirken."
    )


def _build_report_email(
    company, website_url, mobile, desktop,
    last_mobile, mobile_diff, ki_kommentar,
    upsell, report_count,
) -> str:
    from datetime import datetime as _dt

    month = _dt.utcnow().strftime("%B %Y")
    score_color = (
        "#059669" if (mobile or 0) >= 85
        else "#D97706" if (mobile or 0) >= 70
        else "#DC2626"
    )
    score_label = (
        "Sehr gut" if (mobile or 0) >= 85
        else "Gut" if (mobile or 0) >= 70
        else "Optimierungsbedarf"
    )

    trend_html = ""
    if mobile_diff is not None:
        if mobile_diff > 2:
            trend_html = (
                f'<span style="color:#059669;font-weight:700;">'
                f'&#9650; +{mobile_diff} Punkte gegenüber Vormonat</span>'
            )
        elif mobile_diff < -2:
            trend_html = (
                f'<span style="color:#DC2626;font-weight:700;">'
                f'&#9660; {mobile_diff} Punkte gegenüber Vormonat</span>'
            )
        else:
            trend_html = (
                f'<span style="color:#6B7280;">'
                f'&#9654; Stabil (&#177;{abs(mobile_diff)} Punkte)</span>'
            )

    upsell_html = ""
    if upsell:
        upsell_html = """
        <div style="background:#FEF3C7;border-left:4px solid #D97706;
                    padding:14px 16px;margin:20px 0;border-radius:0 6px 6px 0;">
          <div style="font-weight:700;color:#92400E;margin-bottom:6px;">
            &#128161; Empfehlung: Website-Optimierung
          </div>
          <div style="font-size:13px;color:#92400E;line-height:1.6;">
            Ein Score unter 70 kostet Sie täglich potenzielle Kunden.
            Mit unserem <strong>Performance-Paket</strong> optimieren wir
            Ladezeiten, Bilder und technische Faktoren gezielt.<br><br>
            <a href="mailto:info@kompagnon.de" style="color:#92400E;font-weight:700;">
              Jetzt kostenloses Beratungsgespräch anfragen &#8594;
            </a>
          </div>
        </div>"""

    trend_block = (
        f'<div style="margin-bottom:16px;font-size:13px;">{trend_html}</div>'
        if trend_html else ""
    )

    return f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#1a2332;">
  <div style="background:#008EAA;padding:20px 24px;border-radius:8px 8px 0 0;">
    <div style="color:#fff;font-size:18px;font-weight:700;">KOMPAGNON</div>
    <div style="color:rgba(255,255,255,.75);font-size:13px;">
      Ihr monatlicher Website-Report &#8212; {month}
    </div>
  </div>
  <div style="padding:24px;background:#fff;
              border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;">
    <p style="margin:0 0 20px;font-size:15px;">
      Guten Tag, <strong>{company}</strong>,
    </p>
    <div style="display:flex;gap:16px;margin-bottom:20px;">
      <div style="flex:1;text-align:center;padding:16px;
                  background:#f8fafc;border-radius:8px;
                  border:2px solid {score_color};">
        <div style="font-size:11px;color:#6B7280;
                    text-transform:uppercase;margin-bottom:4px;">Mobil</div>
        <div style="font-size:36px;font-weight:800;color:{score_color};">{mobile}</div>
        <div style="font-size:12px;color:{score_color};font-weight:600;">{score_label}</div>
      </div>
      <div style="flex:1;text-align:center;padding:16px;
                  background:#f8fafc;border-radius:8px;">
        <div style="font-size:11px;color:#6B7280;
                    text-transform:uppercase;margin-bottom:4px;">Desktop</div>
        <div style="font-size:36px;font-weight:800;color:#374151;">{desktop or '&#8211;'}</div>
        <div style="font-size:12px;color:#6B7280;">Score /100</div>
      </div>
    </div>
    {trend_block}
    <div style="background:#F0F9FF;border-radius:8px;
                padding:14px 16px;margin-bottom:20px;">
      <div style="font-size:12px;font-weight:700;color:#0369A1;margin-bottom:6px;">
        &#128202; KI-Analyse
      </div>
      <div style="font-size:13px;color:#374151;line-height:1.7;">{ki_kommentar}</div>
    </div>
    {upsell_html}
    <div style="font-size:12px;color:#6B7280;margin-top:20px;">
      <a href="https://{website_url}" style="color:#008EAA;">{website_url}</a> &#183;
      Report #{report_count} &#183; Gemessen im {month}
    </div>
    <div style="margin-top:20px;padding-top:20px;
                border-top:1px solid #e2e8f0;font-size:12px;color:#6B7280;">
      <strong>KOMPAGNON Communications</strong><br>
      Bei Fragen:
      <a href="mailto:info@kompagnon.de" style="color:#008EAA;">info@kompagnon.de</a>
    </div>
  </div>
</div>"""
