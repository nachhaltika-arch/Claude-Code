"""
Brevo-Anbindung fuer den Newsletter — direkt gegen die REST-API v3.

Warum ohne SDK: Der Code rief frueher `import brevo_python` auf. Das Paket
`brevo-python` installiert aber das Modul `brevo`, nie `brevo_python`. Der
Import schlug immer fehl, wurde stillschweigend gefangen und der Newsletter
meldete monatelang "SDK nicht installiert". Ausserdem hat `brevo` ab Version 4
eine voellig andere Schnittstelle als der Code erwartete — ein Wechsel des
Importnamens haette also nichts repariert.

Die fuenf benoetigten Endpunkte sind schlicht genug, dass httpx sie direkt
bedient. Das ist dasselbe Muster wie in netlify_service.py und spart eine
Abhaengigkeit mit 740 Symbolen.

Fehler werden IMMER geworfen, nie als Zeichenkette zurueckgegeben. Der fruehere
Weg — Rueckgabe von "Fehler beim ..." — sah fuer den Aufrufer aus wie ein
gueltiger Wert und landete beinahe in einer BIGINT-Spalte.
"""
import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

BREVO_API = "https://api.brevo.com/v3"
REQUEST_TIMEOUT_SECONDS = 20.0
DEFAULT_FOLDER_ID = 1
SENDER_NAME = "KOMPAGNON"
SENDER_EMAIL = "info@kompagnon.eu"


class BrevoError(RuntimeError):
    """Brevo hat abgelehnt oder war nicht erreichbar."""


def _fehlertext(response: httpx.Response) -> str:
    """Brevos Begruendung herausziehen — sie ist fuer den Nutzer die einzige Spur."""
    try:
        body = response.json()
    except ValueError:
        return response.text[:200] or "keine Antwort"

    if isinstance(body, dict):
        return body.get("message") or body.get("code") or str(body)[:200]
    return str(body)[:200]


def _anteil(zaehler: Optional[int], nenner: Optional[int]) -> Optional[float]:
    if not nenner or zaehler is None:
        return None
    return zaehler / nenner


class BrevoService:
    """
    Ein Dienst pro Anfrage. Als Kontextmanager verwenden, damit die Verbindung
    geschlossen wird:

        with BrevoService() as brevo:
            brevo.create_contact(...)
    """

    def __init__(self, api_key: Optional[str] = None, transport: Optional[httpx.BaseTransport] = None):
        key = (api_key if api_key is not None else os.getenv("BREVO_API_KEY", "")).strip()
        if not key:
            raise BrevoError(
                "BREVO_API_KEY ist nicht gesetzt. Bitte in Render unter "
                "Environment eintragen — ohne Schluessel kann kein Newsletter laufen."
            )

        self._client = httpx.Client(
            base_url=BREVO_API,
            timeout=REQUEST_TIMEOUT_SECONDS,
            transport=transport,
            headers={
                "api-key": key,
                "accept": "application/json",
                "content-type": "application/json",
            },
        )

    def __enter__(self) -> "BrevoService":
        return self

    def __exit__(self, *_exc_info) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # ── Transport ────────────────────────────────────────────────────────────

    def _request(self, method: str, path: str, payload: Optional[dict] = None) -> httpx.Response:
        try:
            response = self._client.request(method, path, json=payload)
        except httpx.HTTPError as exc:
            logger.error("Brevo %s %s nicht erreichbar: %s", method, path, exc)
            raise BrevoError(f"Brevo ist nicht erreichbar: {exc}") from exc

        if response.status_code >= 400:
            grund = _fehlertext(response)
            logger.error("Brevo %s %s: HTTP %s — %s", method, path, response.status_code, grund)
            raise BrevoError(f"Brevo lehnte ab (HTTP {response.status_code}): {grund}")

        return response

    def _id_aus(self, response: httpx.Response, was: str) -> int:
        try:
            body = response.json()
        except ValueError as exc:
            raise BrevoError(f"Brevo lieferte keine gueltige Antwort fuer {was}.") from exc

        brevo_id = body.get("id") if isinstance(body, dict) else None
        if brevo_id is None:
            raise BrevoError(f"Brevo lieferte keine ID fuer {was}.")
        return brevo_id

    # ── Kontakte ─────────────────────────────────────────────────────────────

    def create_contact(self, email: str, first_name: str, last_name: str,
                       list_ids: list, attributes: Optional[dict] = None) -> int:
        """Legt einen Kontakt an oder aktualisiert ihn.

        ``attributes`` ergaenzt die Namensfelder um eigene Merkmale — das
        Widget haengt daran Website, Punktzahl und Stufe, damit eine
        Automatisierung danach segmentieren kann.
        """
        merkmale = {"FIRSTNAME": first_name, "LASTNAME": last_name}
        merkmale.update(attributes or {})

        response = self._request("POST", "/contacts", {
            "email": email,
            "attributes": merkmale,
            "listIds": list_ids,
            "updateEnabled": True,
        })

        # Kennt Brevo den Kontakt bereits, aktualisiert es ihn und antwortet mit
        # 204 ohne Rumpf. Das ist Erfolg, nur ohne ID — die holen wir nach,
        # sonst stuende in der Datenbank NULL und saehe aus wie ein Fehlschlag.
        if response.status_code == 204:
            return self._id_aus(self._request("GET", f"/contacts/{email}"), "den vorhandenen Kontakt")

        return self._id_aus(response, "den Kontakt")

    def create_list(self, name: str, folder_id: int = DEFAULT_FOLDER_ID) -> int:
        response = self._request("POST", "/contacts/lists", {"name": name, "folderId": folder_id})
        return self._id_aus(response, "die Liste")

    def ensure_attribute(self, name: str, typ: str = "text") -> None:
        """Legt ein Kontaktmerkmal an, falls es noch fehlt.

        Brevo lehnt einen Kontakt mit unbekanntem Merkmal komplett ab. Wer
        also Website oder Punktzahl mitschicken will, muss das Merkmal vorher
        kennen — sonst scheitert der ganze Eintrag an einer Kleinigkeit.
        Existiert es schon, antwortet Brevo mit einem Fehler, der hier
        bewusst verschluckt wird.
        """
        try:
            self._request("POST", f"/contacts/attributes/normal/{name}", {"type": typ})
        except BrevoError as e:
            logger.debug("Merkmal %s nicht angelegt (existiert vermutlich): %s", name, e)

    # ── Kampagnen ────────────────────────────────────────────────────────────

    def create_email_campaign(
        self,
        title: str,
        subject: str,
        html_content: str,
        list_ids: list[int],
        scheduled_at: Optional[str] = None,
    ) -> int:
        """Eine Kampagne bei Brevo anlegen.

        **`list_ids`, nicht `list_id` (26.08.2026).** Der Parameter hiess bis
        dahin Einzahl, und `send_campaign` nahm aus mehreren gewaehlten Listen
        stillschweigend die **erste** — wer drei waehlte, erreichte eine, ohne
        Fehler und ohne Meldung. Brevos Nutzdaten heissen `listIds` und sind
        eine Liste; die eine Kennung wurde nur kuenstlich hineingezwaengt.

        Aufgefallen ist es, weil der Endpunkt bis dahin **keinen Aufrufer**
        hatte (L-105): Mit einer Mehrfachauswahl in der Oberflaeche waere der
        erste echte Rundbrief an einen Teil der Empfaenger gegangen.
        """
        if not list_ids:
            raise ValueError("Eine Kampagne ohne Empfängerliste ergibt keine "
                             "Kampagne — mindestens eine Liste angeben.")

        payload: dict[str, Any] = {
            "name": title,
            "subject": subject,
            "htmlContent": html_content,
            "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
            "recipients": {"listIds": list(list_ids)},
        }
        if scheduled_at:
            payload["scheduledAt"] = scheduled_at

        return self._id_aus(self._request("POST", "/emailCampaigns", payload), "die Kampagne")

    def send_campaign_now(self, brevo_campaign_id: int) -> None:
        self._request("POST", f"/emailCampaigns/{brevo_campaign_id}/sendNow")

    def get_campaign_stats(self, brevo_campaign_id: int) -> dict:
        """
        Die Oberflaeche rechnet die Raten mal 100, erwartet also Anteile.
        Brevo liefert `opensRate` in Prozent und gar keine Klickrate — die
        wird aus uniqueClicks/delivered gebildet.
        """
        response = self._request("GET", f"/emailCampaigns/{brevo_campaign_id}")
        try:
            body = response.json()
        except ValueError as exc:
            raise BrevoError("Brevo lieferte keine gueltige Statistik-Antwort.") from exc

        stats = (body.get("statistics") or {}).get("globalStats") or {}

        opens_rate = stats.get("opensRate")
        open_rate = opens_rate / 100 if opens_rate is not None else _anteil(
            stats.get("uniqueViews"), stats.get("delivered")
        )

        return {
            "openRate": open_rate,
            "clickRate": _anteil(stats.get("uniqueClicks"), stats.get("delivered")),
            "unsubscriptions": stats.get("unsubscriptions"),
            "sentCount": stats.get("sent"),
        }
