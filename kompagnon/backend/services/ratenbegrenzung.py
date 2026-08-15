"""
Grenzen für die Endpunkte, die ohne Anmeldung Geld kosten.

``POST /api/audit/start`` war bis zum 15.08.2026 ohne Anmeldung und ohne jede
Grenze erreichbar. Jeder Aufruf löst einen KI-Lauf, PageSpeed-Kontingent, einen
Screenshot und einen Mehrseiten-Crawl aus. Das Widget hat seit dem 11.08.
eigene Grenzen — aber es ruft die Funktion intern auf; wer den HTTP-Endpunkt
direkt anspricht, umgeht sie vollständig.

**Gezählt wird über das, was ohnehin gespeichert wird:** Zeitpunkt und
Zieladresse. Keine neue Spalte und keine IP-Adressen — für eine Grenze, die
Kosten deckelt, genügt „wie oft wurde diese Adresse zuletzt geprüft" und „wie
viel läuft insgesamt". Eine IP zu speichern wäre für diesen Zweck mehr Daten,
als die Sache rechtfertigt.

Die Prüfung hängt bewusst als FastAPI-Abhängigkeit am Endpunkt, nicht in der
Funktion: Das Widget ruft ``start_audit`` direkt auf, nachdem es seine eigenen,
feineren Grenzen geprüft hat. Abhängigkeiten laufen beim direkten Aufruf nicht
mit — die Grenzen greifen also genau dort, wo sie sollen.
"""
import logging
from datetime import datetime, timedelta
from urllib.parse import urlparse

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import AuditResult, Lead, get_db

logger = logging.getLogger(__name__)

# Dieselbe Adresse mehrmals am Tag zu prüfen ergibt kaum ein anderes Ergebnis —
# die Grenze lässt einen zweiten Versuch zu und stoppt die Wiederholung.
LIMIT_JE_ADRESSE_PRO_TAG = 3

# Deckel über alles Unangemeldete. Das Widget zählt seine Anfragen zusätzlich
# selbst; diese Grenze fängt den Weg am Widget vorbei.
LIMIT_GESAMT_PRO_STUNDE = 40
LIMIT_GESAMT_PRO_TAG = 200

# Die Lead-Anlage ist billig, aber unbegrenzt füllt sie die Liste mit Müll.
LIMIT_LEADS_PRO_STUNDE = 30

ZU_OFT = ("Diese Adresse wurde heute bereits mehrfach geprüft. "
          "Bitte versuchen Sie es morgen erneut.")
AUSGELASTET = ("Das Analyse-Kontingent ist ausgelastet. "
               "Bitte versuchen Sie es später erneut.")


def _vergleichbare_adresse(url: str) -> str:
    """Adresse ohne Schema, ``www.`` und Schrägstrich am Ende.

    Ohne diese Vereinheitlichung genügt ein angehängter Schrägstrich, um die
    Grenze zu umgehen.
    """
    roh = (url or "").strip().lower()
    if "://" in roh:
        roh = urlparse(roh).netloc + urlparse(roh).path
    return roh.removeprefix("www.").rstrip("/")


def _zaehle_audits(db: Session, seit: datetime, *bedingungen) -> int:
    return db.query(AuditResult).filter(
        AuditResult.created_at >= seit, *bedingungen).count()


def pruefe_audit_grenzen(db: Session, url: str, angemeldet: bool = False) -> None:
    """Wirft 429, wenn ein weiterer Lauf die Grenzen überschreitet.

    Angemeldete Aufrufer bleiben frei: Das Tool prüft Kundenseiten wiederholt,
    und wer sich anmeldet, ist bekannt.
    """
    if angemeldet:
        return

    jetzt = datetime.utcnow()
    vor_einer_stunde = jetzt - timedelta(hours=1)
    vor_einem_tag = jetzt - timedelta(days=1)

    adresse = _vergleichbare_adresse(url)
    if adresse:
        # Über den gespeicherten Wert vergleichen, nicht über die Rohadresse:
        # gespeichert wird mit Schema, angefragt wird in jeder Schreibweise.
        gleiche = [
            a for a in db.query(AuditResult).filter(
                AuditResult.created_at >= vor_einem_tag).all()
            if _vergleichbare_adresse(a.website_url) == adresse
        ]
        if len(gleiche) >= LIMIT_JE_ADRESSE_PRO_TAG:
            logger.info(f"Ratengrenze: {adresse} heute {len(gleiche)}× geprüft")
            raise HTTPException(429, ZU_OFT)

    if _zaehle_audits(db, vor_einer_stunde) >= LIMIT_GESAMT_PRO_STUNDE:
        logger.warning("Ratengrenze: Stundenkontingent für Audits erreicht")
        raise HTTPException(429, AUSGELASTET)
    if _zaehle_audits(db, vor_einem_tag) >= LIMIT_GESAMT_PRO_TAG:
        logger.warning("Ratengrenze: Tageskontingent für Audits erreicht")
        raise HTTPException(429, AUSGELASTET)


def pruefe_lead_grenzen(db: Session, angemeldet: bool = False) -> None:
    """Wirft 429, wenn zu viele Leads in kurzer Zeit angelegt wurden."""
    if angemeldet:
        return

    vor_einer_stunde = datetime.utcnow() - timedelta(hours=1)
    angelegt = db.query(Lead).filter(Lead.created_at >= vor_einer_stunde).count()
    if angelegt >= LIMIT_LEADS_PRO_STUNDE:
        logger.warning("Ratengrenze: Stundenkontingent für Leads erreicht")
        raise HTTPException(429, AUSGELASTET)


# ── Als Abhängigkeit am Endpunkt ───────────────────────────────────

async def audit_grenzen(request: Request, db: Session = Depends(get_db)) -> None:
    """Abhängigkeit für ``POST /api/audit/start``."""
    from routers.auth_router import optional_auth

    try:
        nutzer = await optional_auth(request)
    except Exception:  # noqa: BLE001 — keine Anmeldung ist der Normalfall
        nutzer = None

    körper = {}
    try:
        körper = await request.json()
    except Exception:  # noqa: BLE001 — ohne Adresse greift nur die Gesamtgrenze
        pass

    pruefe_audit_grenzen(db, körper.get("website_url", ""),
                         angemeldet=bool(nutzer))


async def lead_grenzen(request: Request, db: Session = Depends(get_db)) -> None:
    """Abhängigkeit für ``POST /api/leads/public``."""
    from routers.auth_router import optional_auth

    try:
        nutzer = await optional_auth(request)
    except Exception:  # noqa: BLE001
        nutzer = None

    pruefe_lead_grenzen(db, angemeldet=bool(nutzer))
