"""
Öffentliche Endpunkte für das Einbett-Widget auf fremden Landingpages.

Alles hier ist ohne Login erreichbar. Deshalb gilt durchgehend:
Zieladressen werden gegen SSRF geprüft, Anfragen werden begrenzt, und die
Einwilligung wird mit Zeitpunkt und Herkunft nachweisbar festgehalten.
"""
import logging
import os
import re
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import AuditResult, Lead, WidgetRequest, get_db
from services import widget_report
from services.url_guard import check_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/widget", tags=["widget"])

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s.]+\.[^@\s]{2,}$")

# Ratenbegrenzung: das Widget steht auf fremden Seiten und jede Anfrage kostet
# einen KI-Aufruf, PageSpeed-Kontingent und eine E-Mail an eine fremde Adresse.
# Die Adresse wird nicht vorab bestätigt — wer sie einträgt, muss sie also
# nicht besitzen. Deshalb greifen mehrere Grenzen ineinander: pro Absender,
# pro Empfänger, pro Empfänger-Betrieb und insgesamt.
LIMIT_PER_IP_PER_HOUR = 5
LIMIT_PER_IP_PER_DAY = 15
LIMIT_PER_EMAIL_PER_DAY = 3
# Schützt einen ganzen Betrieb: sonst liessen sich beliebig viele erfundene
# Adressen derselben Firma anschreiben, jede knapp unter ihrer Einzelgrenze.
LIMIT_PER_DOMAIN_PER_DAY = 10

# Bei Freemail-Anbietern sagt die Domain nichts über den Empfänger aus —
# dort wuerde die Grenze fremde Interessenten gegenseitig aussperren.
FREEMAIL_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "gmx.de", "gmx.net", "gmx.at", "web.de",
    "yahoo.de", "yahoo.com", "hotmail.com", "hotmail.de", "outlook.com",
    "outlook.de", "live.de", "icloud.com", "me.com", "t-online.de",
    "freenet.de", "aol.com", "posteo.de", "mailbox.org", "protonmail.com",
    "proton.me",
})
LIMIT_TOTAL_PER_HOUR = 60
LIMIT_TOTAL_PER_DAY = 300

TOP_ISSUES_IN_TEASER = 3

# Bericht und Bestätigung hängen an einem Token in der Adresszeile und zeigen
# Daten eines Betriebs. Ohne Referrer-Policy trägt jeder Klick auf einen Link
# das Token in den Referer der Zielseite; ohne X-Frame-Options lässt sich die
# Bestätigung in einem fremden Rahmen erschleichen; ohne no-store bleibt der
# Bericht in Zwischenspeichern liegen.
SEITEN_KOPFZEILEN = {
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "X-Content-Type-Options": "nosniff",
}


class WidgetAuditRequest(BaseModel):
    email: str
    website_url: str
    consent_marketing: bool = False
    referrer: str = ""


def _normalise_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def _client_ip(request: Request) -> str:
    """Die Adresse des echten Aufrufers — nicht die, die er selbst behauptet.

    ``X-Forwarded-For`` ist eine Kette, an die jeder Proxy hinten anhängt.
    Der vorderste Eintrag stammt damit vom Aufrufer selbst; gezählt wird
    deshalb der letzte, den der nächstgelegene Proxy angehängt hat. Auf
    Render ist das der echte Aufrufer.

    Kopfzeilen wie ``CF-Connecting-IP`` sind nur so viel wert wie der Proxy,
    der sie setzt. Hier stand diese Zeile fest verdrahtet an erster Stelle —
    aber vor dieser Anwendung steht kein Cloudflare, sie läuft direkt auf
    Render. Damit war der Wert reine Behauptung des Aufrufers: einmal pro
    Anfrage neu gewürfelt, und jede Grenze pro IP war ausgehebelt. Wer so
    einen Proxy tatsächlich davorstellt, benennt seine Kopfzeile in
    ``TRUSTED_PROXY_HEADER`` — erst dann zählt sie.

    Fehlt alles, zählt die Verbindung selbst. In unklarer Lage wird damit
    eher zu streng gezählt als zu lax — bei einem Endpunkt, der E-Mails an
    fremde Adressen auslöst, ist das die richtige Richtung.
    """
    vertrauter_kopf = os.getenv("TRUSTED_PROXY_HEADER", "").strip().lower()
    if vertrauter_kopf:
        wert = request.headers.get(vertrauter_kopf, "").strip()
        if wert:
            return wert[:64]

    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()[:64]

    return (request.client.host if request.client else "")[:64]


def _email_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1] if "@" in email else ""


def _zaehle(db: Session, seit: datetime, *bedingungen) -> int:
    return db.query(WidgetRequest).filter(
        WidgetRequest.created_at >= seit, *bedingungen).count()


def _enforce_limits(db: Session, ip: str, email: str) -> None:
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    zu_viele = "Zu viele Anfragen. Bitte später erneut versuchen."
    postfach = ("Für diese E-Mail-Adresse wurden heute bereits mehrere Analysen "
                "angefordert. Bitte sehen Sie in Ihrem Postfach nach.")
    ausgelastet = ("Das Analyse-Kontingent ist ausgelastet. "
                   "Bitte versuchen Sie es später erneut.")

    if ip:
        if _zaehle(db, hour_ago, WidgetRequest.ip_address == ip) >= LIMIT_PER_IP_PER_HOUR:
            raise HTTPException(429, zu_viele)
        if _zaehle(db, day_ago, WidgetRequest.ip_address == ip) >= LIMIT_PER_IP_PER_DAY:
            raise HTTPException(429, zu_viele)

    if _zaehle(db, day_ago, WidgetRequest.email == email) >= LIMIT_PER_EMAIL_PER_DAY:
        raise HTTPException(429, postfach)

    domain = _email_domain(email)
    if domain and domain not in FREEMAIL_DOMAINS:
        von_domain = _zaehle(db, day_ago, WidgetRequest.email.ilike(f"%@{domain}"))
        if von_domain >= LIMIT_PER_DOMAIN_PER_DAY:
            raise HTTPException(429, postfach)

    if _zaehle(db, hour_ago) >= LIMIT_TOTAL_PER_HOUR:
        raise HTTPException(429, ausgelastet)
    if _zaehle(db, day_ago) >= LIMIT_TOTAL_PER_DAY:
        raise HTTPException(429, ausgelastet)


@router.post("/audit")
async def start_widget_audit(
    payload: WidgetAuditRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Nimmt eine Anfrage aus dem Widget an und startet das Audit."""
    email = payload.email.strip().lower()
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(400, "Bitte eine gültige E-Mail-Adresse angeben.")

    url = _normalise_url(payload.website_url)
    ok, reason = check_url(url)
    if not ok:
        raise HTTPException(400, f"Diese Adresse lässt sich nicht prüfen: {reason}")

    ip = _client_ip(request)
    _enforce_limits(db, ip, email)

    domain = url.split("//", 1)[-1].replace("www.", "").split("/")[0]
    lead = db.query(Lead).filter(Lead.website_url.ilike(f"%{domain}%")).first()
    if lead is None:
        lead = Lead(website_url=url, email=email, company_name=domain,
                    status="new", lead_source="embed_audit")
        db.add(lead)
        db.commit()
        db.refresh(lead)
    elif not lead.email:
        lead.email = email
        db.commit()

    now = datetime.utcnow()
    widget_request = WidgetRequest(
        email=email,
        website_url=url,
        consent_marketing=bool(payload.consent_marketing),
        consent_at=now if payload.consent_marketing else None,
        ip_address=ip,
        user_agent=request.headers.get("user-agent", "")[:400],
        referrer=(payload.referrer or request.headers.get("referer", ""))[:500],
        confirm_token=secrets.token_urlsafe(32) if payload.consent_marketing else None,
        # Immer erzeugt: die Adressbestätigung steht vor allem anderen und
        # hängt nicht am Marketing-Haken.
        verify_token=secrets.token_urlsafe(32),
        report_token=secrets.token_urlsafe(32),
        poll_token=secrets.token_urlsafe(32),
        lead_id=lead.id,
    )
    db.add(widget_request)
    db.commit()
    db.refresh(widget_request)

    from routers.audit import start_audit, AuditRequest

    started = await start_audit(
        AuditRequest(website_url=url, company_name=domain, lead_id=lead.id),
        background_tasks,
        db,
    )

    # start_audit schließt die übergebene Session vor dem Scrape-Aufruf,
    # deshalb hier eine eigene für den Nachtrag der Audit-ID.
    from database import SessionLocal

    db2 = SessionLocal()
    try:
        row = db2.query(WidgetRequest).filter(WidgetRequest.id == widget_request.id).first()
        if row:
            row.audit_id = started["id"]
            db2.commit()
    finally:
        db2.close()

    # Die Analyse-Nummer bleibt bewusst draussen: das Widget braucht sie nicht,
    # und herausgegeben wäre sie der Schlüssel zu fremden Analysen.
    return {"request_id": widget_request.id,
            "poll_token": widget_request.poll_token,
            "status": "pending"}


@router.get("/config")
def widget_config(db: Session = Depends(get_db)):
    """Öffentliche Widget-Konfiguration — vom Widget beim Laden abgerufen.

    Enthält bewusst nur Anzeigewerte (Datenschutz-Link, Ziel des CTA), damit
    der Einbettende nichts anpassen muss, wenn sich etwas ändert.
    """
    from services import app_settings

    return app_settings.widget_config(db)


@router.get("/teaser/{token}")
def audit_teaser(token: str, db: Session = Depends(get_db)):
    """Kurzfassung fürs Widget — der vollständige Bericht geht per E-Mail.

    Der Zugang hängt am Token der eigenen Anfrage, nicht an der laufenden
    Nummer der Analyse. Vorher liess sich die Tabelle von 1 aufwärts
    durchzählen — jede im Tool angelegte Analyse mit Firma, Adresse,
    Punktzahl und Schwachstellen war ohne Login zu holen.
    """
    row = db.query(WidgetRequest).filter(WidgetRequest.poll_token == token).first()
    if not row or not row.audit_id:
        raise HTTPException(404, "Analyse nicht gefunden")

    audit = db.query(AuditResult).filter(AuditResult.id == row.audit_id).first()
    if not audit:
        raise HTTPException(404, "Analyse nicht gefunden")

    if audit.status != "completed":
        return {"status": audit.status,
                "error": audit.error_message if audit.status == "failed" else None}

    issues = widget_report._json_field(audit.top_issues, [])
    blockers = widget_report._json_field(audit.blockers, [])
    return {
        "status": "completed",
        "website_url": audit.website_url,
        "company_name": audit.company_name,
        "total_score": audit.total_score,
        "level": audit.level,
        "coverage": getattr(audit, "coverage", None),
        "top_issues": issues[:TOP_ISSUES_IN_TEASER],
        "blocker_count": len(blockers),
        "email_sent": row.report_sent_at is not None,
    }


@router.get("/report/{token}", response_class=HTMLResponse)
def public_report(token: str, db: Session = Depends(get_db)):
    """Berichtsseite ohne Login — erreichbar nur über den Link aus der E-Mail."""
    row = db.query(WidgetRequest).filter(WidgetRequest.report_token == token).first()
    if not row or not row.audit_id:
        raise HTTPException(404, "Bericht nicht gefunden")

    audit = db.query(AuditResult).filter(AuditResult.id == row.audit_id).first()
    if not audit or audit.status != "completed":
        raise HTTPException(404, "Bericht noch nicht verfügbar")

    # Der Link steht nur in der E-Mail. Wer ihn öffnet, hat Zugriff auf das
    # Postfach — das ist der Nachweis, dass die eingetragene Adresse dem
    # Empfänger gehört. Nur der erste Abruf wird festgehalten.
    if not row.report_confirmed_at:
        row.report_confirmed_at = datetime.utcnow()
        db.commit()

    # Das Ziel des Angebots-Knopfes kommt aus derselben Einstellung wie im
    # Widget (Akquise → Analyse-Widget). Vorher zeigte die Berichtsseite fest
    # auf den Checkout und konnte damit woanders hin als das Widget.
    from services import app_settings

    return HTMLResponse(
        widget_report.render_report_page(
            audit, audit.company_name, token=token,
            cta_url=app_settings.get(db, "widget_checkout_url")),
        headers=SEITEN_KOPFZEILEN)


@router.get("/report/{token}/pdf")
def public_report_pdf(token: str, db: Session = Depends(get_db)):
    """Derselbe Bericht als PDF — früher hing er als Anhang an der ersten Mail.

    Der Anhang ging an eine Adresse, die noch niemand bestätigt hatte. Hier
    liegt er hinter demselben Klick wie der Bericht.
    """
    row = db.query(WidgetRequest).filter(WidgetRequest.report_token == token).first()
    if not row or not row.audit_id:
        raise HTTPException(404, "Bericht nicht gefunden")

    audit = db.query(AuditResult).filter(AuditResult.id == row.audit_id).first()
    if not audit or audit.status != "completed":
        raise HTTPException(404, "Bericht noch nicht verfügbar")

    try:
        from services.pdf_generator import generate_audit_report

        pdf = generate_audit_report(audit.__dict__)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"PDF für Audit {audit.id} nicht erzeugt: {e}")
        raise HTTPException(503, "Das PDF lässt sich gerade nicht erzeugen.")

    name = (audit.company_name or "Analyse").replace(" ", "-").replace("/", "-")
    return Response(
        pdf, media_type="application/pdf",
        headers={**SEITEN_KOPFZEILEN,
                 "Content-Disposition": f'attachment; filename="Website-Analyse-{name}.pdf"'},
    )


@router.get("/verify/{token}", response_class=HTMLResponse)
def verify_address_page(token: str, db: Session = Depends(get_db)):
    """Zeigt nur den Knopf — verändert nichts.

    Der Link aus der E-Mail landet hier. Er darf nichts auslösen: Gmail und
    Sicherheits-Gateways rufen Links in Mails automatisch ab, und als dieser
    Aufruf die Bestätigung noch selbst vollzog, kam die Berichts-Mail fünfzehn
    Sekunden nach der Bestätigungs-Mail — ohne dass ein Mensch geklickt hatte.
    Damit war das Double-Opt-in wirkungslos.
    """
    row = db.query(WidgetRequest).filter(WidgetRequest.verify_token == token).first()
    if not row:
        return HTMLResponse(widget_report.verification_page(False), status_code=404,
                            headers=SEITEN_KOPFZEILEN)
    if row.verified_at:
        return HTMLResponse(widget_report.verification_page(True, bereits=True),
                            headers=SEITEN_KOPFZEILEN)

    return HTMLResponse(
        widget_report.aktionsseite(
            "Analyse bestätigen",
            "Bitte bestätigen Sie, dass diese E-Mail-Adresse Ihnen gehört. "
            "Danach schicken wir Ihnen den Link zum vollständigen Bericht.",
            "Ja, Analyse bestätigen",
            widget_report.verify_url(token),
        ),
        headers=SEITEN_KOPFZEILEN)


@router.post("/verify/{token}", response_class=HTMLResponse)
def verify_address(token: str, background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db)):
    """Bestätigt die Adresse und stößt erst dann die Berichts-Mail an.

    Nur über POST erreichbar, also nur durch einen gedrückten Knopf. Ein
    Scanner, der Links abklappert, kommt hier nicht an.
    """
    row = db.query(WidgetRequest).filter(WidgetRequest.verify_token == token).first()
    if not row:
        return HTMLResponse(widget_report.verification_page(False), status_code=404,
                            headers=SEITEN_KOPFZEILEN)

    if row.verified_at:
        # Ein zweiter Klick, etwa aus dem Verlauf, darf nichts erneut auslösen.
        return HTMLResponse(widget_report.verification_page(True, bereits=True),
                            headers=SEITEN_KOPFZEILEN)

    row.verified_at = datetime.utcnow()
    db.commit()
    logger.info(f"Widget-Adresse bestätigt: {row.email}")

    from routers.audit import send_widget_report
    from services import widget_crm

    # Die Berichts-Mail geht direkt raus, nicht als Hintergrundauftrag.
    # Ein solcher Auftrag läuft erst nach der Antwort, und wird der Container
    # in genau dem Moment neu gestartet — auf Render bei jedem Deploy — ist er
    # ersatzlos weg. Der Besucher hat dann bestätigt und bekommt nie etwas.
    # Genau das war am 2026-08-12 bei einer Testanfrage zu sehen: bestätigt,
    # aber keine zweite Mail. Der Klick wartet dafür rund eine Sekunde.
    send_widget_report(row.id)

    # Liste „Adresse bestätigt": der Überblick über die Interessenten. Hier
    # darf keine Automatisierung hängen — bestätigt ist die Adresse, nicht
    # die Einwilligung in Werbung. Bleibt im Hintergrund: Brevo darf den
    # Besucher nicht warten lassen.
    background_tasks.add_task(widget_crm.uebertrage_anfrage, row.id,
                              widget_crm.liste_bestaetigt(), "adresse_bestaetigt")

    return HTMLResponse(widget_report.verification_page(True),
                        headers=SEITEN_KOPFZEILEN)


@router.get("/confirm/{token}", response_class=HTMLResponse)
def confirm_marketing_page(token: str, db: Session = Depends(get_db)):
    """Zeigt den Knopf für den Marketing-Opt-in — verändert nichts.

    Hier wiegt die Trennung schwerer als bei der Adressbestätigung: Eine
    Einwilligung, die ein Postfach-Scanner beim Abklappern der Links erteilt
    hat, ist keine Einwilligung. Als Nachweis im Streitfall wäre sie wertlos.
    """
    row = db.query(WidgetRequest).filter(WidgetRequest.confirm_token == token).first()
    if not row:
        return HTMLResponse(widget_report.confirmation_page(False), status_code=404,
                            headers=SEITEN_KOPFZEILEN)
    if row.confirmed_at:
        return HTMLResponse(widget_report.confirmation_page(True),
                            headers=SEITEN_KOPFZEILEN)

    return HTMLResponse(
        widget_report.aktionsseite(
            "Kontaktaufnahme bestätigen",
            "Bitte bestätigen Sie, dass wir Sie zu Ihrer Website-Analyse "
            "kontaktieren dürfen. Sie können dem jederzeit formlos "
            "widersprechen.",
            "Ja, Kontaktaufnahme bestätigen",
            widget_report.confirm_url(token),
        ),
        headers=SEITEN_KOPFZEILEN)


@router.post("/confirm/{token}", response_class=HTMLResponse)
def confirm_marketing(token: str, background_tasks: BackgroundTasks,
                      db: Session = Depends(get_db)):
    """Double-Opt-in: bestätigt die Einwilligung zur Kontaktaufnahme."""
    row = db.query(WidgetRequest).filter(WidgetRequest.confirm_token == token).first()
    if not row:
        return HTMLResponse(widget_report.confirmation_page(False), status_code=404,
                            headers=SEITEN_KOPFZEILEN)

    if not row.confirmed_at:
        row.confirmed_at = datetime.utcnow()
        lead = db.query(Lead).filter(Lead.id == row.lead_id).first()
        if lead:
            lead.status = "opt_in"
        db.commit()
        logger.info(f"Widget-Einwilligung bestätigt: {row.email}")

        from services import widget_crm

        # Erst hier ist Werbung gedeckt — nur diese Liste trägt eine
        # Automatisierung.
        background_tasks.add_task(widget_crm.uebertrage_anfrage, row.id,
                                  widget_crm.liste_optin(), "marketing_optin")

    return HTMLResponse(widget_report.confirmation_page(True),
                        headers=SEITEN_KOPFZEILEN)
