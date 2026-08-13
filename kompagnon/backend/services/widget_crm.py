"""
Widget-Anfragen nach Brevo übertragen.

Bis hierher schrieb der Widget-Pfad nur in die eigene Datenbank: ein `Lead`
mit `lead_source="embed_audit"`. Der Mailversand läuft über
``/v3/smtp/email`` — transaktionaler Versand legt in Brevo **keinen** Kontakt
an. Deshalb blieb die Liste dort leer, obwohl Anfragen ankamen.

**Zwei Listen, und der Unterschied ist der Punkt:**

* *Adresse bestätigt* — wer die erste Mail bestätigt hat. Das ist der
  Überblick über die Interessenten. Hier darf **keine** Automatisierung
  hängen: Die Person hat nur belegt, dass ihr die Adresse gehört, nicht dass
  sie angeschrieben werden möchte.
* *Marketing-Opt-in* — wer zusätzlich den Einwilligungslink gedrückt hat.
  Nur hier ist Werbung gedeckt.

Ohne diese Trennung würde eine Brevo-Automatisierung genau die Leute
anschreiben, die nie eingewilligt haben — und damit alles aushebeln, wofür
das Double-Opt-in gebaut wurde.

Nichts hier darf den Bestätigungsklick des Besuchers kippen. Fällt Brevo aus
oder fehlt die Konfiguration, wird das protokolliert und der Vorgang läuft
weiter.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Merkmale, an denen eine Automatisierung segmentieren kann.
MERKMALE = (
    ("WEBSITE", "text"),
    ("ANALYSE_SCORE", "float"),
    ("ANALYSE_STUFE", "text"),
    ("ANALYSE_QUELLE", "text"),
)


def liste_bestaetigt() -> Optional[int]:
    return _listen_id("BREVO_LIST_VERIFIED_ID")


def liste_optin() -> Optional[int]:
    return _listen_id("BREVO_LIST_OPTIN_ID")


def _listen_id(variable: str) -> Optional[int]:
    wert = os.getenv(variable, "").strip()
    if not wert:
        return None
    try:
        return int(wert)
    except ValueError:
        logger.warning("%s ist keine Zahl: %r", variable, wert)
        return None


def uebertrage(email: str, listen_id: Optional[int], *, website: str = "",
               score: Optional[int] = None, stufe: str = "",
               quelle: str = "widget") -> bool:
    """Trägt eine Adresse in eine Brevo-Liste ein. Gibt zurück, ob es klappte.

    Wirft nie — der Aufrufer steckt mitten im Bestätigungsklick eines
    Besuchers, und ein Ausfall bei Brevo darf ihm nicht als Fehler begegnen.
    """
    if not listen_id:
        logger.info("Keine Brevo-Liste eingerichtet — %s nicht übertragen", email)
        return False

    try:
        from services.brevo_service import BrevoService

        with BrevoService() as brevo:
            for name, typ in MERKMALE:
                brevo.ensure_attribute(name, typ)

            merkmale = {"WEBSITE": website, "ANALYSE_QUELLE": quelle}
            if score is not None:
                merkmale["ANALYSE_SCORE"] = score
            if stufe:
                merkmale["ANALYSE_STUFE"] = stufe

            brevo.create_contact(email=email, first_name="", last_name="",
                                 list_ids=[listen_id], attributes=merkmale)
        logger.info("Brevo: %s in Liste %s eingetragen", email, listen_id)
        return True
    except Exception as e:  # noqa: BLE001 — darf den Klick nicht kippen
        logger.warning("Brevo-Übertragung für %s fehlgeschlagen: %s", email, e)
        return False


def uebertrage_anfrage(request_id: int, listen_id: Optional[int],
                       quelle: str) -> None:
    """Holt die Anfrage samt Analyse und überträgt sie.

    Läuft als Hintergrundauftrag und öffnet deshalb eine eigene Sitzung.
    """
    if not listen_id:
        return

    from database import AuditResult, SessionLocal, WidgetRequest

    db = SessionLocal()
    try:
        row = db.query(WidgetRequest).filter(WidgetRequest.id == request_id).first()
        if not row:
            return
        audit = (db.query(AuditResult).filter(AuditResult.id == row.audit_id).first()
                 if row.audit_id else None)
        uebertrage(
            email=row.email,
            listen_id=listen_id,
            website=row.website_url or "",
            score=getattr(audit, "total_score", None),
            stufe=getattr(audit, "level", "") or "",
            quelle=quelle,
        )
    finally:
        db.close()
