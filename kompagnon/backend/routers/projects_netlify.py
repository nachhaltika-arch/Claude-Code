"""Netlify — Site anlegen, ausrollen, Domain setzen, Status abfragen.

**Warum eine eigene Datei (L-25, Etappe 1, 22.08.2026).** `projects.py` hatte
4.860 Zeilen. Genau dort ist am selben Tag L-76 entstanden: zwei Freigabe-
Verfahren wuchsen auf **eine** Adresse, weil in einer Datei dieser Groesse
niemand sieht, dass sie schon vergeben ist. Der Umbau ist deshalb keine
Kosmetik, sondern die Behandlung der Ursache.

**Netlify zuerst, obwohl es nicht das groesste Stueck ist.** Hier wird als
Naechstes gearbeitet: Das Tracking-Feature fuer die Kundenseiten (GA4, Meta
Pixel, Schema.org, `llms.txt`) gehoert in den Deploy-Weg, zwischen
HTML-Erzeugung und Uebergabe an Netlify. Danach entsteht es in einer Datei
von 600 Zeilen statt in einer von 4.860.

**Reiner Umzug.** Keine Logik, kein Pfad, keine Signatur geaendert. Der
Router kommt aus `projects_router.py` — dasselbe Objekt wie zuvor, damit sich
keine Adresse verschiebt. Gegengeprueft mit `tools/endpunkte_auflisten.py`:
466 Endpunkte vorher, 466 nachher.
"""
import logging
import os
from datetime import datetime

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Project, SessionLocal, get_db
from routers.auth_router import (get_current_user, require_admin,
                                 require_any_auth)
from routers.projects_router import router

logger = logging.getLogger(__name__)


# ── Netlify-Integration ───────────────────────────────────────────────────────

class NetlifyDeployRequest(BaseModel):
    html:      str
    css:       str = ""
    redirects: str = ""
    page_title:       str = "Website"
    meta_description: str = ""
    company_name:     str = ""

class NetlifyDomainRequest(BaseModel):
    domain: str


@router.post("/{project_id}/netlify/create-site")
async def netlify_create_site(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Erstellt eine neue Netlify-Site für das Projekt (nur Admin)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")

    existing = db.execute(
        text("SELECT netlify_site_id FROM projects WHERE id = :id"),
        {"id": project_id},
    ).scalar()
    if existing:
        raise HTTPException(409, f"Netlify-Site bereits vorhanden: {existing}")

    lead = project.lead
    company = (
        getattr(project, "company_name", None)
        or (lead.company_name if lead else None)
        or f"projekt-{project_id}"
    )

    # DB-Verbindung vor externem Netlify-API-Call freigeben
    db.close()

    from services.netlify_service import create_site
    result = await create_site(company)

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        db2.execute(
            text(
                "UPDATE projects SET netlify_site_id = :sid, netlify_site_url = :url "
                "WHERE id = :id"
            ),
            {"sid": result["site_id"], "url": result["site_url"], "id": project_id},
        )
        db2.commit()
    finally:
        db2.close()
    return {"site_id": result["site_id"], "site_url": result["site_url"]}


def _llms_txt_fuer(db, project_id: int) -> str:
    """Die `llms.txt` fuer die Site dieses Projekts (L-99).

    **Warum sie mit dem Deploy hochgeht und nicht danach.** Netlify ersetzt
    bei jeder Auslieferung den **ganzen** Inhalt der Site. Ein zweiter Aufruf
    nur fuer die Datei naehme die Seiten wieder weg; umgekehrt zeigte eine
    Datei aus einem frueheren Deploy auf Seiten, die es nicht mehr gibt.

    **Der Slug wird abgeleitet, nicht aus der Spalte gelesen.** Die Tabelle
    fuehrt zwar `sitemap_pages.slug`, aber der Multi-Page-Deploy benutzt sie
    **nicht**: Dort entsteht der Dateiname immer aus
    `_slugify_page_name(page_name)`. Wer hier die Spalte naehme, schriebe
    Adressen in die Datei, die es auf der Site nicht gibt — und ein Modell
    liest sie als Quelle.

    Fehlt die Anschrift, entsteht keine Datei: `geo_artefakte` erfindet
    nichts, und eine halbe `llms.txt` sieht fuer ein Modell aus wie eine
    Auskunft.
    """
    from services.geo_artefakte import llms_txt

    betrieb = db.execute(
        text("SELECT l.* FROM leads l JOIN projects p ON p.lead_id = l.id "
             "WHERE p.id = :id"),
        {"id": project_id},
    ).fetchone()
    if not betrieb:
        return ""
    seiten = [
        {"page_name": z[0], "slug": _slugify_page_name(z[0] or ""),
         "zweck": z[1] or ""}
        for z in db.execute(
            text("SELECT s.page_name, s.zweck FROM sitemap_pages s "
                 "JOIN projects p ON p.lead_id = s.lead_id "
                 "WHERE p.id = :id ORDER BY s.position"),
            {"id": project_id},
        ).fetchall()
    ]
    return llms_txt(betrieb, seiten)


@router.post("/{project_id}/netlify/deploy")
async def netlify_deploy(
    project_id: int,
    body: NetlifyDeployRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Deployt HTML auf die Netlify-Site des Projekts (nur Admin)."""
    row = db.execute(
        text(
            "SELECT p.netlify_site_id, COALESCE(l.company_name, '') "
            "FROM projects p LEFT JOIN leads l ON l.id = p.lead_id "
            "WHERE p.id = :id"
        ),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(400, "Keine Netlify-Site vorhanden. Zuerst Site anlegen.")

    site_id       = row[0]
    company_name  = body.company_name or row[1] or ""
    page_title    = body.page_title or company_name or "Website"

    geo_datei = _llms_txt_fuer(db, project_id)

    # DB-Verbindung vor externem Netlify-Deploy freigeben
    db.close()

    from services.netlify_service import deploy_html
    result = await deploy_html(
        site_id,
        body.html,
        body.css,
        body.redirects,
        page_title=page_title,
        meta_description=body.meta_description,
        company_name=company_name,
        zusatzdateien={"llms.txt": geo_datei},
    )

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        db2.execute(
            text(
                "UPDATE projects SET netlify_deploy_id = :did, netlify_last_deploy = :ts "
                "WHERE id = :id"
            ),
            {"did": result["deploy_id"], "ts": datetime.utcnow(), "id": project_id},
        )
        db2.commit()
    finally:
        db2.close()
    return {
        "deploy_id":  result["deploy_id"],
        "deploy_url": result["deploy_url"],
        "state":      result["state"],
    }


def _slugify_page_name(name: str) -> str:
    """URL-safe slug for sitemap page names (used by Multi-Page Deploy)."""
    import re
    s = (name or "").lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "seite"


@router.post("/{project_id}/netlify/deploy-all")
async def netlify_deploy_all(
    project_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """
    Deployt alle gespeicherten GrapesJS-Seiten eines Projekts auf Netlify.
    Jede Seite wird als eigene HTML-Datei abgelegt (Pfad = Ordner).

    Startseite (position=0 oder Name Startseite/Home) → /index.html
    Andere Seiten → /{slug}/index.html
    """
    row = db.execute(
        text(
            "SELECT p.netlify_site_id, p.lead_id, COALESCE(l.company_name, '') "
            "FROM projects p LEFT JOIN leads l ON l.id = p.lead_id "
            "WHERE p.id = :id"
        ),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(400, "Keine Netlify-Site vorhanden. Zuerst Site anlegen.")
    if not row[1]:
        raise HTTPException(400, "Kein Lead verknuepft")

    site_id      = row[0]
    lead_id      = row[1]
    company_name = row[2] or "Website"

    pages = db.execute(
        text("""
            SELECT page_name, gjs_html, gjs_css, zweck, position, ist_pflichtseite
            FROM sitemap_pages
            WHERE lead_id = :lid
            ORDER BY position, id
        """),
        {"lid": lead_id},
    ).fetchall()

    if not pages:
        raise HTTPException(400, "Keine Seiten in der Sitemap gefunden.")

    # ── Seiten-Dateien zusammenstellen ────────────────────────────────────
    page_files: dict = {}
    css_parts: list = []
    used_slugs: dict = {}

    for page in pages:
        page_name, gjs_html, gjs_css, zweck, position, ist_pflichtseite = page
        html = gjs_html or "<p>Diese Seite hat noch keinen Inhalt.</p>"
        css  = gjs_css or ""
        if css:
            css_parts.append(css)

        slug = _slugify_page_name(page_name)
        if slug in used_slugs:
            used_slugs[slug] += 1
            slug = f"{slug}-{used_slugs[slug]}"
        else:
            used_slugs[slug] = 0

        is_home = (position == 0) or slug in ("startseite", "home", "index")
        filename = "index.html" if is_home else f"{slug}/index.html"

        page_files[filename] = {
            "html":       html,
            "css":        css,
            "page_title": f"{page_name} — {company_name}" if not is_home else company_name,
            "meta_desc":  zweck or f"{page_name} — {company_name}",
        }

    # Deduplicate CSS (gemeinsame Styles)
    shared_css = "\n".join(dict.fromkeys(css_parts))

    geo_datei = _llms_txt_fuer(db, project_id)

    # DB-Verbindung vor externem API-Call freigeben
    db.close()

    from services.netlify_service import deploy_all_pages
    try:
        result = await deploy_all_pages(site_id, page_files, shared_css,
                                        company_name,
                                        zusatzdateien={"llms.txt": geo_datei})
    except Exception as e:
        raise HTTPException(500, f"Netlify Deploy Fehler: {str(e)[:200]}")

    # Deploy-Info speichern
    db2 = SessionLocal()
    try:
        db2.execute(
            text(
                "UPDATE projects SET netlify_deploy_id = :did, netlify_last_deploy = :ts "
                "WHERE id = :id"
            ),
            {"did": result["deploy_id"], "ts": datetime.utcnow(), "id": project_id},
        )
        db2.commit()
    finally:
        db2.close()

    return {
        "deploy_id":      result["deploy_id"],
        "deploy_url":     result["deploy_url"],
        "state":          result["state"],
        "pages_deployed": list(page_files.keys()),
    }


@router.post("/{project_id}/netlify/set-domain")
async def netlify_set_domain(
    project_id: int,
    body: NetlifyDomainRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Setzt eine Custom-Domain auf der Netlify-Site, generiert DNS-Guide,
    sendet E-Mail an Kunden und legt eine Portal-Nachricht an."""
    row = db.execute(
        text("SELECT netlify_site_id, netlify_site_url, lead_id FROM projects WHERE id = :id"),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(400, "Keine Netlify-Site vorhanden.")

    site_id       = row[0]
    site_url      = row[1] or ""
    lead_id       = row[2]

    # DB-Verbindung vor externem Netlify-Call freigeben
    db.close()

    from services.netlify_service import set_custom_domain, generate_dns_guide
    try:
        result = await set_custom_domain(site_id, body.domain)
    except Exception as e:
        logger.warning(f"Netlify set_custom_domain Fehler: {e}")
        result = {"custom_domain": body.domain}

    # DNS-Guide generieren
    guide = generate_dns_guide(body.domain, site_url)

    # Neue Session zum Speichern + Mail/Nachricht
    db2 = SessionLocal()
    try:
        db2.execute(
            text(
                "UPDATE projects SET netlify_domain = :domain, netlify_domain_status = 'pending' "
                "WHERE id = :id"
            ),
            {"domain": body.domain, "id": project_id},
        )
        db2.commit()

        # Asynchron: E-Mail + Portal-Nachricht senden (Fehler werden nur geloggt)
        try:
            _send_dns_guide_email_and_message(project_id, lead_id, body.domain, guide, db2)
        except Exception as e:
            logger.warning(f"DNS-Guide E-Mail/Nachricht Fehler: {e}")
    finally:
        db2.close()

    return {
        "custom_domain":       result.get("custom_domain", body.domain),
        "required_dns_record": result.get("required_dns_record"),
        "cname_target":        f"{body.domain}.netlify.app",
        "guide":               guide,
        "status":              "pending",
    }


def _send_dns_guide_email_and_message(project_id, lead_id, domain, guide, db):
    """Sendet DNS-Guide per E-Mail an den Kunden und legt eine Portal-Nachricht an."""
    if not lead_id:
        return
    lead = db.execute(
        text("SELECT email, company_name FROM leads WHERE id = :id"),
        {"id": lead_id},
    ).fetchone()
    if not lead:
        return

    # HTML-Tabelle für die E-Mail
    records_html = "".join([
        f"""<tr>
          <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;font-weight:600;color:#2d3748">{r['type']}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;font-family:monospace">{r['name']}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;font-family:monospace;color:#008eaa;word-break:break-all">{r['value']}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;color:#718096;font-size:12px">{r['note']}</td>
        </tr>"""
        for r in guide["records"]
    ])

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;background:#f7fafc;padding:20px">
      <div style="background:#008eaa;padding:32px;border-radius:12px 12px 0 0;text-align:center">
        <h1 style="color:white;margin:0;font-size:24px">Ihre Website ist bereit!</h1>
        <p style="color:rgba(255,255,255,0.9);margin:8px 0 0;font-size:14px">
          Nur noch ein Schritt bis zum Go-Live
        </p>
      </div>
      <div style="padding:32px;background:#ffffff">
        <p style="color:#2d3748">Sehr geehrte Damen und Herren,</p>
        <p style="color:#4a5568;line-height:1.7">
          Ihre neue Website für <strong>{lead.company_name or 'Ihr Unternehmen'}</strong> ist fertig und bereit für den Go-Live.
          Um Ihre Domain <strong>{domain}</strong> mit der Website zu verbinden,
          tragen Sie bitte folgende Einstellungen bei Ihrem Domain-Anbieter ein:
        </p>

        <table style="width:100%;border-collapse:collapse;margin:24px 0;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden">
          <thead>
            <tr style="background:#f7fafc">
              <th style="padding:10px 14px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:0.05em">Typ</th>
              <th style="padding:10px 14px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:0.05em">Name</th>
              <th style="padding:10px 14px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:0.05em">Wert</th>
              <th style="padding:10px 14px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:0.05em">Info</th>
            </tr>
          </thead>
          <tbody>{records_html}</tbody>
        </table>

        <div style="background:#f0fff4;border:1px solid #c6f6d5;border-radius:8px;padding:16px;margin:20px 0">
          <p style="margin:0;color:#276749;font-size:13px">
            <strong>Zeitrahmen:</strong> DNS-Änderungen werden innerhalb von 1–48 Stunden aktiv.
            Wir informieren Sie automatisch sobald Ihre Domain live ist.
          </p>
        </div>

        <p style="color:#4a5568;font-size:13px;line-height:1.6">
          {guide.get('instructions', '')}
        </p>"""

    if guide.get("email_records"):
        html_body += """
        <div style="margin-top:20px;padding:16px;background:#FFF7E6;border-radius:8px;
                    border-left:3px solid #F59E0B">
          <p style="font-size:14px;font-weight:600;color:#B45309;margin:0 0 8px">
            E-Mail-Einträge (optional)
          </p>
          <p style="font-size:12px;color:#92400E;margin:0 0 8px">
            Damit E-Mails an Ihre Domain (info@..., kontakt@...) ankommen:
          </p>
          <table style="width:100%;border-collapse:collapse;font-size:12px">
        """
        for r in guide["email_records"]:
            html_body += f"""
            <tr>
              <td style="padding:4px 8px;font-weight:600;color:#92400E">{r['type']}</td>
              <td style="padding:4px 8px;font-family:monospace">{r['name']}</td>
              <td style="padding:4px 8px;font-family:monospace">{r['value']}</td>
              <td style="padding:4px 8px;color:#6B7280">{r.get('note','')}</td>
            </tr>"""
        html_body += "</table></div>"

    html_body += """
        <p style="color:#4a5568;font-size:13px">
          Bei Fragen helfen wir Ihnen gerne weiter.
        </p>
      </div>
      <div style="background:#f7fafc;padding:16px;text-align:center;border-radius:0 0 12px 12px;font-size:12px;color:#718096">
        KOMPAGNON Communications
      </div>
    </div>
    """

    # E-Mail versenden
    if lead.email:
        from services.email import send_email
        ok = send_email(
            to_email=lead.email,
            subject=f"DNS-Einstellungen für {domain} — letzter Schritt vor Go-Live",
            html_body=html_body,
        )
        if ok:
            logger.info(f"DNS-Guide E-Mail gesendet an {lead.email}")
        else:
            logger.warning(f"DNS-Guide E-Mail an {lead.email} fehlgeschlagen")

    # Portal-Nachricht anlegen
    try:
        records_text = "\n".join([
            f"  • {r['type']}  {r['name']}  →  {r['value']}" for r in guide["records"]
        ])
        msg = (
            f"Ihre Website ist bereit! Um {domain} zu verbinden, tragen Sie bitte "
            f"folgende DNS-Einträge bei Ihrem Domain-Anbieter ein:\n\n"
            f"{records_text}\n\n"
            f"Die Änderungen werden innerhalb von 1–48 Stunden aktiv. "
            f"Sie haben diese Anleitung auch per E-Mail erhalten."
        )
        db.execute(text("""
            INSERT INTO messages (lead_id, channel, content, direction, created_at, sender_role)
            VALUES (:lead_id, 'in_app', :content, 'outbound', NOW(), 'system')
        """), {"lead_id": lead_id, "content": msg})
        db.commit()
    except Exception as e:
        logger.warning(f"DNS-Guide Portal-Nachricht Fehler: {e}")
        try:
            db.rollback()
        except Exception:
            pass


class SubdomainRequest(BaseModel):
    subdomain: str
    subdomain_type: str = "cname"


@router.post("/{project_id}/netlify/add-subdomain")
async def netlify_add_subdomain(
    project_id: int,
    body: SubdomainRequest,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Fügt eine Subdomain zur Netlify-Site hinzu und generiert DNS-Anleitung."""
    row = db.execute(
        text("SELECT netlify_site_id, netlify_site_url, netlify_domain, lead_id FROM projects WHERE id=:id"),
        {"id": project_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(400, "Keine Netlify-Site vorhanden")

    site_id     = row[0]
    site_url    = row[1] or ""
    main_domain = row[2] or ""
    lead_id     = row[3]

    sub = body.subdomain.lower().strip()
    full_sub = f"{sub}.{main_domain}" if main_domain and "." not in sub else sub

    netlify_host = site_url.replace("https://", "").replace("http://", "").rstrip("/")

    from services.netlify_service import set_domain_alias
    try:
        await set_domain_alias(site_id, full_sub)
    except Exception as e:
        logger.warning(f"Netlify add_domain_alias fehlgeschlagen: {e}")

    subdomain_record = {
        "type":  "CNAME",
        "name":  sub,
        "value": netlify_host,
        "ttl":   "3600",
        "note":  f"{full_sub} zeigt auf Netlify",
    }

    db2 = SessionLocal()
    try:
        db2.execute(text("""
            INSERT INTO messages (lead_id, channel, content, direction, created_at, sender_role)
            VALUES (:lid, 'in_app', :content, 'outbound', NOW(), 'system')
        """), {
            "lid":     lead_id,
            "content": (
                f"Neue Subdomain {full_sub} eingerichtet. "
                f"Bitte tragen Sie bei Ihrem Domain-Anbieter ein: "
                f"CNAME  {sub}  →  {netlify_host}"
            ),
        })
        db2.commit()
    except Exception as e:
        logger.warning(f"Subdomain Portal-Nachricht Fehler: {e}")
    finally:
        db2.close()

    return {
        "subdomain":      full_sub,
        "netlify_target": netlify_host,
        "dns_record":     subdomain_record,
        "instructions":   (
            f"Tragen Sie bei Ihrem Domain-Anbieter ein: "
            f"CNAME  {sub}  →  {netlify_host}. "
            f"Aktiv in 1–24 Stunden."
        ),
    }


@router.get("/{project_id}/netlify/status")
async def netlify_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ruft den Netlify-Status des Projekts ab.
    Gibt IMMER 200 mit status-Feld zurück — nie 404/500 für fehlende Site.
    """
    row = db.execute(
        text(
            "SELECT netlify_site_id, netlify_site_url, netlify_deploy_id, "
            "netlify_domain, netlify_domain_status, netlify_ssl_active, netlify_last_deploy "
            "FROM projects WHERE id = :id"
        ),
        {"id": project_id},
    ).fetchone()

    if not row:
        return {"connected": False, "status": "project_not_found", "project_id": project_id}
    if not row[0]:
        return {
            "connected": False,
            "status": "not_connected",
            "message": "Keine Netlify-Site verbunden",
            "project_id": project_id,
        }

    # Check if NETLIFY_API_TOKEN is configured
    if not os.getenv("NETLIFY_API_TOKEN"):
        return {
            "connected": False,
            "status": "no_token",
            "message": "NETLIFY_API_TOKEN nicht konfiguriert",
            "netlify_site_id": row[0],
            "netlify_site_url": row[1],
        }

    site_id = row[0]
    try:
        from services.netlify_service import get_site_status
        live = await get_site_status(site_id)
    except Exception as e:
        logger.error(f"Netlify get_site_status Fehler: {e}")
        return {
            "connected": False,
            "status": "api_error",
            "message": str(e),
            "netlify_site_id": row[0],
            "netlify_site_url": row[1],
        }

    # SSL-Status in DB aktualisieren
    ssl_active = bool(live.get("ssl"))
    try:
        db.execute(
            text("UPDATE projects SET netlify_ssl_active = :ssl WHERE id = :id"),
            {"ssl": ssl_active, "id": project_id},
        )
        db.commit()
    except Exception as e:
        logger.warning(f"Netlify SSL-Status update Fehler: {e}")
        db.rollback()

    return {
        **live,
        "connected":             True,
        "status":                "connected",
        "netlify_site_id":       row[0],
        "netlify_site_url":      row[1],
        "netlify_deploy_id":     row[2],
        "netlify_domain":        row[3],
        "netlify_domain_status": row[4],
        "netlify_ssl_active":    ssl_active,
        "netlify_last_deploy":   row[6].isoformat() if row[6] else None,
    }
