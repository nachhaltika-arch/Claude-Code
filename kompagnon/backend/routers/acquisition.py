"""
Einstellungen für die Akquise: Einbett-Widget und E-Mail-Versand.

Liegt im Tool unter Akquise, damit Anzeige und Links des Widgets dort gepflegt
werden können, wo das Widget auch verwendet wird — ohne Umweg über das
Render-Dashboard.

Der Versandweg wird hier nur noch **angezeigt**, nicht eingestellt: seit die
Einzelmails über die Brevo-Transaktions-API laufen, kommt der Zugang aus
``BREVO_API_KEY``. Ein SMTP-Formular im Tool hätte nur vorgetäuscht, dass dort
etwas einzurichten wäre — und sperrte tatsächlich den Test-Versand, solange
niemand einen ungenutzten SMTP-Server eintrug.
"""
import logging
import os
from datetime import timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.base_urls import public_base_url
from sqlalchemy.orm import Session

from database import User, WidgetRequest, get_db
from routers.auth_router import require_admin
from services import app_settings, pixel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/acquisition", tags=["acquisition"])


class WidgetSettings(BaseModel):
    privacy_url: str = ""
    checkout_url: str = ""
    headline: str = ""
    #: Facebook-Pixel des Widgets. Leer heisst abgeschaltet — dann laedt das
    #: Widget kein fremdes Skript. Geprueft wird in `services/pixel.py`.
    facebook_pixel_id: str = ""
    #: Wohin der Kaufknopf fuer Check PLUS im Teaser fuehrt (10.09.2026).
    #: **Leer heisst kein Knopf**, nicht „Knopf ins Leere": Solange hier
    #: nichts steht, zeigt das Widget den Angebotsblock ohne Abschluss.
    #: Eine Einstellung, weil der Weg wechseln kann — heute ein
    #: Stripe-Zahllink, spaeter die eigene Kasse — und das keinen Deploy
    #: kosten soll.
    check_plus_url: str = ""
    #: Wohin der Kaufknopf fuer den Websprint Relaunch auf der Berichtsseite
    #: fuehrt. Leer heisst: Der Knopf fuehrt in den Terminkalender — nicht
    #: ins Leere.
    kauf_relaunch_url: str = ""


class TestEmailRequest(BaseModel):
    to: str


# Wie viele der letzten Anfragen die Übersicht im Tool zeigt.
REQUEST_HISTORY_LIMIT = 25


#: Wie viel von der Fehlermeldung in die Liste kommt. Sie ist fuer den
#: Innendienst, nicht fuer den Kunden — aber eine Seite voll Rueckverfolgung
#: macht die Liste unlesbar.
FEHLER_LAENGE = 200


def _analysestaende(db, zeilen) -> dict:
    """Status und Fehlergrund je Analyse — **eine** Abfrage fuer alle Zeilen.

    Nicht je Zeile nachschlagen: Die Liste zeigt 25 Anfragen, das waeren 25
    Abfragen fuer eine Ansicht, die der Innendienst mehrmals taeglich oeffnet.

    **Ein Fehler hier darf die Liste nicht kippen.** Sie beantwortet vor
    allem, ob Berichte rausgingen; der Analysestand ist ein Zusatz. Faellt er
    aus, fehlt eine Spalte — nicht die Seite.
    """
    kennungen = {z.audit_id for z in zeilen if z.audit_id}
    if not kennungen:
        return {}
    try:
        from modelle_audit import AuditResult

        gefunden = (db.query(AuditResult)
                    .filter(AuditResult.id.in_(kennungen))
                    .all())
    except Exception as fehler:  # noqa: BLE001
        db.rollback()
        logger.warning("Analysestand nicht lesbar: %s: %s",
                       type(fehler).__name__, fehler)
        return {}

    return {
        a.id: (a.status,
               (a.error_message or "")[:FEHLER_LAENGE] if a.status == "failed" else None)
        for a in gefunden
    }


def widget_embed_url() -> str:
    base = public_base_url()
    return f"{base}/embed/audit-widget.html"


# ═══════════════════════════════════════════════════════════════════
# Widget
# ═══════════════════════════════════════════════════════════════════

@router.get("/widget")
def read_widget_settings(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    config = app_settings.widget_config(db)
    return {
        **config,
        # Der **gespeicherte** Wert, nicht der abgeleitete aus `check_plus`:
        # Das Formular bearbeitet die Einstellung, nicht das Ergebnis.
        "check_plus_url": app_settings.get(db, "widget_check_plus_url"),
        "kauf_relaunch_url": app_settings.get(db, "bericht_kauf_relaunch_url"),
        "embed_url": widget_embed_url(),
        "requests_total": db.query(WidgetRequest).count(),
        "requests_confirmed": db.query(WidgetRequest).filter(
            WidgetRequest.confirmed_at.isnot(None)).count(),
    }


@router.put("/widget")
def write_widget_settings(
    payload: WidgetSettings,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    for field, value in (("widget_privacy_url", payload.privacy_url),
                         ("widget_checkout_url", payload.checkout_url),
                         # Der Wert landet in einem href auf **fremden**
                         # Seiten — `javascript:` gehoert dort nicht hin.
                         ("widget_check_plus_url", payload.check_plus_url),
                         ("bericht_kauf_relaunch_url", payload.kauf_relaunch_url)):
        if value and not value.startswith(("http://", "https://", "/")):
            raise HTTPException(400, f"'{value}' ist keine gültige Adresse.")

    # Die Pixel-ID wird geprueft und nicht bloss durchgereicht: Wer den
    # Skript-Schnipsel aus dem Events Manager einfuegt, bekaeme sonst ein
    # Widget, das nichts meldet — und ein Pixel, der nicht feuert, meldet
    # auch nicht, dass er nicht feuert.
    try:
        pixel_id = pixel.geprueft(payload.facebook_pixel_id)
    except ValueError as fehler:
        raise HTTPException(400, str(fehler))

    app_settings.set_many(db, {
        "widget_privacy_url": payload.privacy_url,
        "widget_checkout_url": payload.checkout_url,
        "widget_headline": payload.headline,
        "widget_facebook_pixel_id": pixel_id,
        "widget_check_plus_url": payload.check_plus_url,
        "bericht_kauf_relaunch_url": payload.kauf_relaunch_url,
    }, admin.id)
    return {"message": "Widget-Einstellungen gespeichert"}


# ═══════════════════════════════════════════════════════════════════
# Anfragen aus dem Widget
# ═══════════════════════════════════════════════════════════════════

def _als_utc(zeitpunkt) -> Optional[str]:
    """Zeitstempel mit Zonenangabe.

    In der Datenbank stehen naive UTC-Werte. Ohne das angehängte 'Z' liest der
    Browser sie als Ortszeit und zeigt jede Anfrage zwei Stunden zu früh an.
    """
    if not zeitpunkt:
        return None
    return zeitpunkt.replace(tzinfo=timezone.utc).isoformat()


#: Unter dieser Dauer hat niemand gelesen, verstanden und gedrückt. Am
#: 16.08.2026 kam die Berichts-Mail fünfzehn Sekunden nach der ersten, ohne
#: dass ein Mensch geklickt hatte — die Dauer ist das schärfste Merkmal, das
#: ohne fremde Hilfe zu haben ist.
VERDAECHTIG_UNTER_S = 2


def _verify_dauer(row):
    """Sekunden zwischen dem Versand der Bestätigungsmail und dem Klick."""
    gesendet, bestaetigt = row.verify_sent_at, row.verified_at
    if not gesendet or not bestaetigt:
        return None
    return int((bestaetigt - gesendet).total_seconds())


def _verdaechtig(row) -> bool:
    """Sieht diese Bestätigung nach einer Maschine aus?

    Sagt nicht „war eine Maschine" — das kann niemand von hier aus
    entscheiden. Sie sagt: Das gehört angesehen.
    """
    dauer = _verify_dauer(row)
    return dauer is not None and dauer < VERDAECHTIG_UNTER_S


@router.get("/widget/requests")
def read_widget_requests(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Die letzten Anfragen mit ihrem Zustellstand.

    Ohne diese Liste zeigt das Tool nur eine Gesamtzahl — ob die Berichte
    tatsächlich rausgingen, war daran nicht zu erkennen.
    """
    rows = (
        db.query(WidgetRequest)
        .order_by(WidgetRequest.created_at.desc())
        .limit(REQUEST_HISTORY_LIMIT)
        .all()
    )
    staende = _analysestaende(db, rows)
    return {
        "requests": [
            {
                "id": row.id,
                "email": row.email,
                "website_url": row.website_url,
                "created_at": _als_utc(row.created_at),
                # Der Weg hat jetzt drei Stufen: Bestätigung angefragt,
                # Adresse bestätigt, Bericht versendet.
                "verify_sent": row.verify_sent_at is not None,
                "verified": row.verified_at is not None,
                "report_sent": row.report_sent_at is not None,
                # Der Klick auf den Berichtslink. Er belegt, dass die Adresse
                # dem Empfänger gehört — ohne ihn ist offen, ob der Bericht
                # bei der richtigen Person gelandet ist.
                "report_opened": row.report_confirmed_at is not None,
                "consent_marketing": bool(row.consent_marketing),
                "consent_confirmed": row.confirmed_at is not None,
                # ── Nachweis, wer bestätigt hat ──────────────────────────
                # Wurde beim Bestätigen immer schon festgehalten, war aber
                # nirgends zu sehen. Am 16.08.2026 blieb deshalb offen, wer
                # um 16:12:09 die Bestätigung ausgelöst hat — die Antwort lag
                # in der Datenbank und war aus dem Tool nicht zu erreichen.
                # Art. 5 Abs. 2 DSGVO verlangt, dass man es belegen kann.
                "verified_at": _als_utc(row.verified_at),
                "verified_user_agent": getattr(row, "verified_user_agent", None) or None,
                "verified_ip": getattr(row, "verified_ip", None) or None,
                "verify_dauer_s": _verify_dauer(row),
                "bestaetigung_verdaechtig": _verdaechtig(row),
                # ── Lief die Analyse ueberhaupt? (L-184, 10.09.2026) ─────
                # Ohne diese zwei Felder sah eine **gescheiterte Erhebung**
                # genauso aus wie eine im Spam gelandete Mail: „Bestaetigung
                # angefragt: nein", sonst nichts. Zwei Ursachen, ein Bild —
                # und keine Handlungsmoeglichkeit, weil der Grund fehlte.
                # Er lag die ganze Zeit in `audit_results.error_message`.
                "analyse_status": staende.get(row.audit_id, (None, None))[0],
                "analyse_fehler": staende.get(row.audit_id, (None, None))[1],
            }
            for row in rows
        ],
        "limit": REQUEST_HISTORY_LIMIT,
    }


# ═══════════════════════════════════════════════════════════════════
# E-Mail-Versand — reine Anzeige plus Probeversand
# ═══════════════════════════════════════════════════════════════════

@router.get("/mail")
def read_mail_status(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Über welchen Weg die Berichts-Mails rausgehen. Enthält nie ein Passwort."""
    config = app_settings.smtp_config(db)
    return {
        **app_settings.mail_channel(db),
        "sender_name": config["sender_name"],
        "sender_email": config["sender_email"],
    }


@router.post("/mail/test")
def send_test_email(
    payload: TestEmailRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Verschickt eine echte Test-E-Mail über den aktiven Versandweg."""
    from services.email import send_email_detailed

    kanal = app_settings.mail_channel(db)
    if not kanal["ready"]:
        raise HTTPException(400, "Es ist kein Versandweg eingerichtet: "
                                 + kanal["detail"])
    config = app_settings.smtp_config(db)

    ok, grund = send_email_detailed(
        to_email=payload.to.strip(),
        subject="KOMPAGNON — Test des E-Mail-Versands",
        html_body=(
            "<p>Diese Nachricht bestätigt, dass der E-Mail-Versand aus dem "
            "KOMPAGNON-Tool funktioniert.</p>"
            f"<p style='color:#666;font-size:13px'>Versandweg: {kanal['label']} · "
            f"Absender: {config['sender_email'] or 'Vorgabe'}</p>"
        ),
        db=db,
    )
    if not ok:
        raise HTTPException(502, f"Versand fehlgeschlagen — {grund}")
    return {"message": f"Test-E-Mail an {payload.to} versendet",
            "channel": kanal["label"], "detail": grund}
