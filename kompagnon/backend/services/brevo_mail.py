"""
Einzelmails über die Brevo-Transaktions-API.

Bis 2026-08-11 liefen alle Einzelmails über SMTP — das war in keiner Umgebung
konfiguriert, also wurde nie eine zugestellt. Der Brevo-API-Schlüssel liegt
dagegen in beiden Umgebungen und treibt bereits die Newsletter.

Diese Anbindung nutzt denselben Schlüssel für Einzelmails. Damit entfällt ein
zweiter Zugangsweg, der separat gepflegt und überwacht werden müsste.
"""
import base64
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

API_URL = "https://api.brevo.com/v3/smtp/email"
TIMEOUT = 20.0

DEFAULT_SENDER_NAME = "KOMPAGNON"
DEFAULT_SENDER_EMAIL = "noreply@kompagnon.group"


def api_key() -> str:
    return os.getenv("BREVO_API_KEY", "").strip()


def is_available() -> bool:
    return bool(api_key())


def _attachment_payload(attachments) -> list:
    """Anhänge im Brevo-Format: base64 plus Dateiname."""
    payload = []
    for dateiname, daten, _subtyp in attachments or []:
        payload.append({
            "name": dateiname,
            "content": base64.b64encode(daten).decode("ascii"),
        })
    return payload


def send(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str = "",
    sender_name: str = "",
    sender_email: str = "",
    attachments=None,
) -> tuple:
    """Verschickt eine Einzelmail. Gibt (erfolg, meldung) zurück.

    Die Meldung wird bei Fehlern nach oben gereicht, damit im Tool steht,
    woran es lag — etwa ein nicht verifizierter Absender.
    """
    key = api_key()
    if not key:
        return False, "BREVO_API_KEY ist nicht gesetzt"

    payload = {
        "sender": {
            "name": sender_name or DEFAULT_SENDER_NAME,
            "email": sender_email or DEFAULT_SENDER_EMAIL,
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
    }
    if text_body:
        payload["textContent"] = text_body

    anhaenge = _attachment_payload(attachments)
    if anhaenge:
        payload["attachment"] = anhaenge

    try:
        response = httpx.post(
            API_URL,
            json=payload,
            headers={"api-key": key, "content-type": "application/json",
                     "accept": "application/json"},
            timeout=TIMEOUT,
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Brevo-Versand an {to_email} fehlgeschlagen: {e}")
        return False, f"Brevo nicht erreichbar: {type(e).__name__}"

    if response.status_code in (200, 201, 202):
        logger.info(f"E-Mail über Brevo gesendet an {to_email}")
        return True, "gesendet"

    meldung = _fehlermeldung(response)
    logger.error(f"Brevo lehnte den Versand an {to_email} ab: {meldung}")
    return False, meldung


def _fehlermeldung(response) -> str:
    """Übersetzt die häufigsten Brevo-Fehler in verwertbare Hinweise."""
    try:
        daten = response.json()
        code = daten.get("code", "")
        text = daten.get("message", response.text[:200])
    except Exception:  # noqa: BLE001
        code, text = "", response.text[:200]

    if response.status_code == 401:
        # Brevo unterscheidet hier zwei völlig verschiedene Ursachen:
        # 'Key not found' (falscher Schlüssel) und 'unrecognised IP address'
        # (Aufruf von einer nicht freigegebenen Adresse). Beide auf eine
        # gemeinsame Meldung zu reduzieren kostet nur Suchzeit.
        hinweis = text.lower()
        if "ip" in hinweis:
            return (f"Brevo blockiert die aufrufende IP-Adresse — unter "
                    f"Sicherheit → Autorisierte IPs freigeben. Brevo meldet: {text}")
        return f"Brevo lehnt den Schlüssel ab. Brevo meldet: {text}"
    if code == "invalid_parameter" and "sender" in text.lower():
        return ("Absenderadresse ist in Brevo nicht verifiziert — "
                "unter Senders bestätigen oder die Domain einrichten")
    return f"HTTP {response.status_code}: {text}"
