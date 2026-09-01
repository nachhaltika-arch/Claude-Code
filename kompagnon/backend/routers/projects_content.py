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

from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Project, SessionLocal, get_db
from routers.auth_router import get_current_user, require_admin, require_any_auth
from routers.projects_helfer import (_get_fernet, eigenes_projekt_pruefen,
                                     safe_json_parse)
from routers.projects_router import kunden_router, router
from services.audit_pagespeed import (
    PSI_ENDPOINT,
    auth_headers as pagespeed_auth_headers,
)
from services.base_urls import public_base_url
from services.ki_aufruf import frag_modell

logger = logging.getLogger(__name__)


# ── Scrape Website Content ─────────────────────────────────────────────────────

# ── Der dritte Scraper — entfernt am 26.08.2026 ──────────────────────────────
#
# Hier stand `GET /api/projects/{id}/scrape-content`: noch ein Weg, dieselbe
# Kundenwebsite auszulesen, mit eigener Ablage (`projects.scraped_content`).
# Gelesen hat diese Spalte **keine Zeile im Bestand** — weder eine Oberflaeche
# noch ein anderer Dienst.
#
# **Entscheidung David:** „der crawler ist der richtige, den anderen weg."
# Die Oberflaeche arbeitet mit `/api/crawler/…`; der zweite Weg
# (`content_scraper_router`) ist am selben Tag ebenfalls entfernt worden.
#
# Die Spalten `scraped_content` und `scraped_at` bleiben stehen. Sie zu
# loeschen waere ein Datenverlust fuer einen Aufraeumgewinn — dieselbe
# Ueberlegung wie bei den Abnahme-Spalten.
#
# `tests/test_ein_scraper.py` verhindert die Rueckkehr.

# ── Sitemap-Planer ────────────────────────────────────────────────────────────





# **Hier standen `GET`/`PATCH /{project_id}/sitemap` und
# `POST /{project_id}/freigabe`** — entfernt am 01.09.2026 (L-105).
#
# Sie waren ein **abgeloestes Parallelsystem**: Die gelebte Seitenstruktur
# liegt unter `/api/sitemap/*` (der Sitemap-Planer), und die gelebten
# Freigaben stehen in `briefings.freigaben` — dieselbe Bezeichnung
# `sitemap_freigabe`, ein anderer Speicher. `BriefingTab.jsx` und die
# Kundenansicht `Projektfreigaben.jsx` lesen beide von dort.
#
# **Die Spalten `projects.sitemap_json` und `sitemap_freigabe` bleiben
# stehen.** Sie zu leeren waere Datenverlust ohne Not; sie haben nur
# keinen Schreiber mehr. Wer sie eines Tages entfernt, findet hier den
# Grund.


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


# ── Abnahme & Go-Live Nachher ─────────────────────────────────────────────────

# ── Abnahme: entfernt am 26.08.2026 (Entscheidung David) ─────────────
#
# Hier stand `POST /{project_id}/abnahme`. Er nahm einen **frei getippten
# Namen** entgegen und schrieb ihn nach `projects.abnahme_durch`, dazu
# `abnahme_datum` und `actual_go_live`. Aufgerufen hat ihn nie jemand
# (L-105) — er hatte keinen Knopf.
#
# **Warum entfernt und nicht verdrahtet.** Es waere die **dritte** Stelle
# gewesen, an der „abgenommen" steht:
#
#   `briefing.freigaben['abnahme_go_live']`  Kundenkonto, Zeitstempel,
#                                            unwiderruflich (seit 26.08.)
#   `content_freigaben`                      Kunde, je Seite
#   `projects.abnahme_datum`                 irgendwer, getippter Name
#
# Eine Abnahme, die der Auftragnehmer selbst abhakt, ist keine Abnahme; eine
# ohne Beweis neben eine mit Beweis zu stellen waere ein Rueckschritt. Wo die
# Abnahme jetzt steht, sagt der Kundenbildschirm „Freigaben".
#
# **Die Spalten bleiben.** Sie sind leer — nur dieser Endpunkt hat je
# hineingeschrieben —, und eine Spalte zu loeschen ist ein Eingriff, der
# nichts gewinnt. `actual_go_live` setzt weiterhin `projects_anlegen.py`.

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

    # Schluessel als Kopfzeile, nicht in der URL — httpx protokolliert die
    # vollstaendige Anfrage-URL (L-98). Eine Stelle, vier Aufrufer.
    base    = PSI_ENDPOINT
    params  = {"url": url}
    kopf    = pagespeed_auth_headers()

    mob_score = desk_score = None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            mob, desk = await asyncio.gather(
                client.get(base, params={**params, "strategy": "mobile"}, headers=kopf),
                client.get(base, params={**params, "strategy": "desktop"}, headers=kopf),
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
