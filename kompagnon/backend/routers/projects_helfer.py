"""Was alle Module unter `/api/projects` gemeinsam brauchen.

**Warum als eigene Datei (L-25, 22.08.2026).** `projects.py` wird in Etappen
zerlegt. Diese drei Helfer benutzt jedes herausgeloeste Stueck; sie in
`projects.py` stehen zu lassen hiesse, dass jedes neue Modul von dort
importiert — und damit haengt die zerlegte Datei wieder an der grossen.

`eigenes_projekt_pruefen` gehoert dabei zum Zugriffsschutz und nicht zum
Beiwerk: Sie ist die Stelle, an der ein Kunde von einem fremden Projekt
ferngehalten wird. Dass sie hier steht und nicht in einer Datei mit
viertausend Zeilen, macht sie auffindbar.
"""
# Der Aliasname stammt aus `projects.py` und bleibt, damit der Umzug
# reiner Umzug ist — die Funktionen sind Zeichen fuer Zeichen dieselben.
import json as _json_mod
import logging
import os

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def safe_json_parse(raw, default=None):
    """Gibt ein Python-Objekt zurück egal ob die DB den Wert als String
    oder bereits als dict/list liefert (PostgreSQL JSONB-Spalten kommen
    oft schon geparst zurück).

    - None / leer     → default
    - dict / list     → direkt zurück
    - str/bytes       → json.loads()
    - JSONDecodeError → default (mit Log)
    - Sonst           → default
    """
    if raw is None or raw == "":
        return default
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.decode("utf-8")
        except Exception:
            return default
    if isinstance(raw, str):
        try:
            return _json_mod.loads(raw)
        except _json_mod.JSONDecodeError as e:
            logger.warning(f"safe_json_parse: {e} (len={len(raw)}, tail={raw[-80:]!r})")
            return default
    return default


def _get_fernet():
    """
    Gibt eine Fernet-Instanz zurück.
    CREDENTIALS_KEY muss ein 32-Byte URL-safe base64 Key sein.
    Generierung: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

    Kein Fallback: wenn CREDENTIALS_KEY fehlt oder ungültig ist,
    wird eine RuntimeError geworfen — niemals zufällige oder unsichere Keys.
    """
    from cryptography.fernet import Fernet
    key = os.getenv("CREDENTIALS_KEY", "")
    if not key:
        raise RuntimeError(
            "CREDENTIALS_KEY Umgebungsvariable nicht gesetzt. "
            "Bitte in Render.com Environment eintragen. "
            "Generieren mit: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as e:
        raise RuntimeError(
            f"CREDENTIALS_KEY ist ungültig ({e}). "
            f"Muss ein 32-Byte URL-safe base64-encoded Fernet-Key sein."
        ) from e


def eigenes_projekt_pruefen(db: Session, project_id: int, current_user) -> int:
    """Gibt die `lead_id` des Projekts zurück — oder wirft.

    Ein Kunde darf nur an sein eigenes Projekt. Die eigene Nummer
    hochzuzählen ist der naheliegendste Angriff, deshalb steht die Prüfung
    hier und nicht in der Oberfläche.

    Für den Innendienst ist es nur ein Nachschlagen: Er kommt an alle.
    """
    zeile = db.execute(
        text("SELECT lead_id FROM projects WHERE id = :id"), {"id": project_id}
    ).fetchone()
    if not zeile:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead_id = zeile[0]
    if getattr(current_user, "role", "") == "kunde" and lead_id != current_user.lead_id:
        raise HTTPException(403, "Kein Zugriff auf dieses Projekt")
    return lead_id
