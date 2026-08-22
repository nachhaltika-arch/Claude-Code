"""Zustellungsstörungen von Brevo entgegennehmen und sichtbar machen.

Warum es das gibt: Der Versand meldet Erfolg, sobald Brevo die Mail annimmt.
Was danach beim Empfänger passiert, erfährt die Anwendung nicht. Am 14.08.2026
wies ein Empfängerserver eine Mail ab, weil die Versand-IP des Anbieters auf
einer Blockliste stand — im Werkzeug stand weiterhin „gesendet". Bei einem
Akquisekanal heißt das: Anschreiben laufen ins Leere und niemand merkt es.

Zwei Endpunkte:

* Der Webhook, den Brevo aufruft. Er ist ohne Anmeldung erreichbar, weil er
  von außen kommt, und deshalb über ein Geheimnis in der Adresse abgesichert —
  Brevo signiert seine Webhooks nicht. Ohne hinterlegtes Geheimnis bleibt er
  geschlossen, damit eine halb eingerichtete Umgebung nicht offensteht.
* Der Abruf je Lead für das Werkzeug, hinter Anmeldung.

Abgelegt werden nur Störungen. Zustellungen, Öffnungen und Klicks würden die
Tabelle fluten, ohne eine Frage zu beantworten, die hier jemand stellt.
"""
import hmac
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import Lead, MailEvent, get_db
from routers.auth_router import require_any_auth, require_innendienst

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mail-events", tags=["mail-events"])

# Die Ereignisse, die eine Zustellung verhindert oder gefährdet haben. Die
# Namen stammen unverändert aus der Brevo-Dokumentation.
STOERUNGEN = frozenset({
    "hard_bounce",    # dauerhaft unzustellbar — Adresse ist tot oder abgewiesen
    "soft_bounce",    # vorübergehend, etwa volles Postfach
    "blocked",        # vom Empfänger abgewiesen, etwa wegen Blockliste
    "spam",           # als Spam gemeldet
    "invalid_email",  # Adresse formal unbrauchbar
    "error",          # Fehler auf dem Weg
})

MAX_GRUND = 500
MAX_BETREFF = 300


def _geheimnis() -> str:
    return os.getenv("BREVO_WEBHOOK_SECRET", "").strip()


def _zeitpunkt(meldung: dict) -> Optional[datetime]:
    """Wann das Ereignis eintrat — Brevo schickt mehrere Formate."""
    epoch = meldung.get("ts_event") or meldung.get("ts") or meldung.get("ts_epoch")
    if isinstance(epoch, (int, float)) and epoch > 0:
        try:
            return datetime.utcfromtimestamp(float(epoch))
        except (OverflowError, OSError, ValueError):
            pass

    roh = str(meldung.get("date") or "").strip()
    for form in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            gelesen = datetime.strptime(roh, form)
            return gelesen.replace(tzinfo=None)
        except ValueError:
            continue
    return None


def _kennung(meldung: dict, event: str, email: str) -> str:
    """Erkennungszeichen gegen Doppelzählung.

    Brevo wiederholt Zustellversuche des Webhooks. Zweimal dieselbe Meldung in
    der Liste sähe aus wie zwei Ausfälle.
    """
    teile = [
        str(meldung.get("id") or ""),
        str(meldung.get("message-id") or ""),
        event,
        email,
        str(meldung.get("ts_event") or meldung.get("ts") or meldung.get("date") or ""),
    ]
    return "|".join(teile)[:255]


@router.post("/brevo/{secret}")
async def brevo_webhook(secret: str, request: Request, db: Session = Depends(get_db)):
    """Nimmt eine Ereignismeldung von Brevo entgegen.

    Antwortet auch dann mit 200, wenn die Meldung nichts enthält, was uns
    angeht — sonst wiederholt Brevo den Versuch endlos.
    """
    erwartet = _geheimnis()
    if not erwartet or not hmac.compare_digest(secret, erwartet):
        # Kein Hinweis darauf, welcher der beiden Fälle vorliegt.
        raise HTTPException(403, "Kein Zugriff")

    try:
        meldung = await request.json()
    except Exception:  # noqa: BLE001 — kaputter Rumpf ist kein Serverfehler
        return {"gespeichert": False, "grund": "kein_json"}

    if not isinstance(meldung, dict):
        return {"gespeichert": False, "grund": "unerwartete_form"}

    event = str(meldung.get("event") or "").strip().lower()
    email = str(meldung.get("email") or "").strip().lower()

    if event not in STOERUNGEN:
        return {"gespeichert": False, "grund": "kein_stoerungsereignis"}
    if not email:
        return {"gespeichert": False, "grund": "keine_adresse"}

    kennung = _kennung(meldung, event, email)
    if db.query(MailEvent).filter(MailEvent.event_key == kennung).first():
        return {"gespeichert": False, "grund": "bereits_bekannt"}

    lead = db.query(Lead).filter(Lead.email.ilike(email)).first()

    db.add(MailEvent(
        event=event,
        email=email,
        reason=str(meldung.get("reason") or "")[:MAX_GRUND],
        subject=str(meldung.get("subject") or "")[:MAX_BETREFF],
        sending_ip=str(meldung.get("sending_ip") or "")[:64],
        message_id=str(meldung.get("message-id") or "")[:255],
        event_key=kennung,
        lead_id=lead.id if lead else None,
        occurred_at=_zeitpunkt(meldung),
    ))
    db.commit()

    logger.warning(
        f"Zustellung gestört: {event} an {email} "
        f"({str(meldung.get('reason') or '')[:120]})")

    return {"gespeichert": True, "event": event}


@router.get("/lead/{lead_id}",
            dependencies=[Depends(require_innendienst)])
def stoerungen_eines_leads(lead_id: int, db: Session = Depends(get_db),
                           user=Depends(require_any_auth)):
    """Die Zustellungsstörungen zu einem Lead — neueste zuerst.

    **Die Sperre gilt nur hier und nicht am Router (L-67, 22.08.2026).** Die
    Antwort traegt Empfaengeradresse, Grund und Betreff jeder gescheiterten
    Zustellung; das stand jedem Angemeldeten offen. Aufgerufen wird sie aus
    `LeadProfile` (admin/auditor).

    Der Brevo-Webhook in derselben Datei bleibt **ohne** Anmeldung: Er kommt
    von aussen und weist sich mit seinem Geheimnis im Pfad aus. Eine
    Router-Sperre haette ihn mitgenommen, und dann kaeme kein einziges
    Zustellereignis mehr an.
    """
    eintraege = (db.query(MailEvent)
                   .filter(MailEvent.lead_id == lead_id)
                   .order_by(MailEvent.created_at.desc())
                   .limit(50).all())

    return {
        "lead_id": lead_id,
        "anzahl": len(eintraege),
        "ereignisse": [{
            "event": e.event,
            "email": e.email,
            "reason": e.reason,
            "subject": e.subject,
            "sending_ip": e.sending_ip,
            "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
        } for e in eintraege],
    }
