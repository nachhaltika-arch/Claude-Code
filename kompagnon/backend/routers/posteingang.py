# -*- coding: utf-8 -*-
"""Antworten von Kunden kommen im Werkzeug an, nicht nur im Postfach.

**Der Anlass (26.08.2026, Entscheidung David: Brevo Inbound Parsing).**
Die Glocke meldet seit heute Tickets und Chatnachrichten (L-18). E-Mail
fehlte — und zwar nicht aus Versehen: `communications.direction` kennt den
Wert `inbound`, aber **keine Zeile im Bestand schreibt ihn**. Wer auf eine
unserer Mails antwortete, landete in Davids Postfach; das Werkzeug erfuhr
nichts davon.

**Warum die Mail zur Nachricht wird und nicht zu einer `communication`.**
`communications` hängt an einem *Projekt* und wird von keiner Oberfläche
gelesen. `Message` dagegen trägt seit jeher `channel` mit genau zwei Werten,
`in_app` und `email` — die Ablage war vorgesehen, nur nie befüllt. So steht
die Antwort im selben Verlauf wie der Chat: Der Innendienst sieht sie am
Betrieb, der Kunde in seinem Portal, und die Glocke meldet sie wie jede
andere Nachricht.

**Nichts geht still verloren.** Kommt eine Mail von einer Adresse, die zu
keinem Betrieb gehört, wird sie nicht weggeworfen — es entsteht eine Meldung
„von unbekannter Adresse" samt Betreff und Anfang des Textes. Eine Antwort,
die niemand sieht, ist schlimmer als gar keine Anbindung: Auf eine Anbindung
verlässt man sich.

**Abgesichert wie der `mail-events`-Webhook**, aus demselben Grund: Brevo
signiert seine Webhooks nicht, also steht das Geheimnis im Pfad. Ohne
hinterlegtes Geheimnis bleibt der Weg geschlossen, damit eine halb
eingerichtete Umgebung nicht offensteht.

**Und es wird immer mit 200 geantwortet**, sobald das Geheimnis stimmt. Ein
Fehlerstatus lässt Brevo dieselbe Mail stunden­lang wiederholen; abgelegt
wäre sie dann mehrfach oder gar nicht.

**Was David einrichten muss:** eine Subdomain (etwa
`posteingang.kompagnon.eu`) mit MX-Eintrag auf Brevo, dort als Inbound-Route
die Ziel-URL dieses Endpunkts hinterlegen und `BREVO_INBOUND_SECRET` in
Render setzen.
"""
import hmac
import logging
import os
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Lead, Message, User, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/posteingang", tags=["posteingang"])

MAX_BETREFF = 300
MAX_INHALT = 20000     # eine Mail mit Verlaufszitat wird lang; irgendwo ist Schluss
MAX_HINWEIS = 200      # so viel zeigt die Glocke

#: Brevo liefert Text und HTML. Der Text ist die ehrlichere Quelle — HTML
#: hier zu entschärfen hieße, einen Reinigungsschritt zu bauen, den niemand
#: prüft. Fehlt der Text, wird das HTML grob entkleidet.
_TAGS = re.compile(r"<[^>]+>")
_LEERRAUM = re.compile(r"\n{3,}")


def _geheimnis() -> str:
    return os.getenv("BREVO_INBOUND_SECRET", "").strip()


def _absender(eintrag: dict) -> str:
    """Die Adresse aus Brevos `From` holen.

    Brevo schickt ein Objekt (`{"Address": …, "Name": …}`); manche
    Weiterleitungen setzen stattdessen eine nackte Zeichenkette. Beides wird
    genommen, statt sich auf eine Form zu verlassen, die man nicht erzwingen
    kann.
    """
    roh = eintrag.get("From") or eintrag.get("from") or ""
    if isinstance(roh, dict):
        roh = roh.get("Address") or roh.get("address") or ""
    if not isinstance(roh, str):
        return ""
    # "Chef <chef@betrieb.de>" → "chef@betrieb.de"
    treffer = re.search(r"<([^>]+)>", roh)
    return (treffer.group(1) if treffer else roh).strip().lower()


def _name(eintrag: dict) -> str:
    roh = eintrag.get("From") or eintrag.get("from") or ""
    if isinstance(roh, dict):
        return (roh.get("Name") or roh.get("name") or "").strip()
    return ""


def _inhalt(eintrag: dict) -> str:
    text = eintrag.get("RawTextBody") or eintrag.get("ExtractedMarkdownMessage")
    if not text:
        html = eintrag.get("RawHtmlBody") or ""
        text = _TAGS.sub(" ", html)
    text = _LEERRAUM.sub("\n\n", (text or "").strip())
    return text[:MAX_INHALT]


def _betrieb_zu(db: Session, adresse: str):
    """Den Betrieb zur Absenderadresse finden.

    Zwei Stellen tragen eine Adresse: der Betrieb selbst und die Konten, die
    Zugang zu ihm haben. Wer aus seinem Zugang heraus antwortet, benutzt oft
    nicht die Adresse, die am Betrieb steht — deshalb beide.
    """
    if not adresse:
        return None

    lead = db.query(Lead).filter(
        func.lower(Lead.email) == adresse).first()
    if lead:
        return lead

    konto = db.query(User).filter(
        func.lower(User.email) == adresse,
        User.lead_id.isnot(None)).first()
    if konto:
        return db.query(Lead).filter(Lead.id == konto.lead_id).first()
    return None


def _ablegen(db: Session, eintrag: dict) -> None:
    """Eine einzelne Mail verarbeiten. Fehler bleiben bei der Mail."""
    from services.benachrichtigungen import melden_leise

    adresse = _absender(eintrag)
    betreff = (eintrag.get("Subject") or eintrag.get("subject")
               or "(ohne Betreff)")[:MAX_BETREFF]
    inhalt = _inhalt(eintrag)
    lead = _betrieb_zu(db, adresse)

    if lead is None:
        # Nicht wegwerfen. Wer sich auf den Posteingang verlässt und dessen
        # Lücke nicht kennt, verliert eine Antwort, ohne es zu merken.
        logger.info("Posteingang: keine Zuordnung für %s", adresse)
        melden_leise(db, art="mail",
                     titel=f"Mail von unbekannter Adresse: {adresse or '?'}",
                     hinweis=f"{betreff} — {inhalt[:MAX_HINWEIS]}",
                     ziel="/app/leads")
        return

    nachricht = Message(
        lead_id=lead.id,
        sender_role="kunde",
        sender_name=_name(eintrag) or lead.company_name or adresse,
        channel="email",
        subject=betreff,
        content=inhalt or "(leere Mail)",
        is_read=False,
    )
    db.add(nachricht)
    # Derselbe Zähler, den der Chat hochsetzt — sonst zeigt der Betrieb eine
    # ungelesene Nachricht weniger an, als er hat.
    lead.unread_messages = (lead.unread_messages or 0) + 1
    db.commit()

    melden_leise(db, art="mail",
                 titel=f"Mail von {lead.company_name or adresse}",
                 hinweis=f"{betreff} — {inhalt[:MAX_HINWEIS]}",
                 ziel=f"/app/betriebe/{lead.id}",
                 lead_id=lead.id)


@router.post("/brevo/{secret}")
async def brevo_posteingang(secret: str, request: Request,
                            db: Session = Depends(get_db)):
    """Eine oder mehrere eingegangene Mails entgegennehmen.

    Antwortet nach der Prüfung des Geheimnisses **immer** mit 200 — auch bei
    einem Rumpf, den niemand vorhergesehen hat. Ein Fehlerstatus lässt Brevo
    stundenlang wiederholen, und was dann abgelegt ist, weiß niemand.
    """
    erwartet = _geheimnis()
    if not erwartet or not hmac.compare_digest(secret, erwartet):
        raise HTTPException(403, "Kein Zugriff")

    try:
        rumpf = await request.json()
    except Exception:                      # noqa: BLE001 — siehe Docstring
        logger.warning("Posteingang: Rumpf ist kein JSON")
        return {"verarbeitet": 0}

    if isinstance(rumpf, dict):
        eintraege = rumpf.get("items") or rumpf.get("Items") or []
    elif isinstance(rumpf, list):
        eintraege = rumpf
    else:
        eintraege = []

    if not isinstance(eintraege, list):
        eintraege = []

    gezaehlt = 0
    for eintrag in eintraege:
        if not isinstance(eintrag, dict):
            continue
        try:
            _ablegen(db, eintrag)
            gezaehlt += 1
        except Exception as fehler:        # noqa: BLE001
            # Eine kaputte Mail darf die nächste nicht mitnehmen.
            db.rollback()
            logger.warning("Posteingang: Mail nicht abgelegt: %s", fehler)

    if not eintraege:
        logger.info("Posteingang: Rumpf ohne Mails (%s)",
                    list(rumpf)[:5] if isinstance(rumpf, dict) else type(rumpf).__name__)

    return {"verarbeitet": gezaehlt}
