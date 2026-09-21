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
    # Woher der Kontakt kam (15.09.2026). **In Brevo muss dafuer nichts von
    # Hand angelegt werden** — `ensure_attributes` legt fehlende Merkmale
    # selbst an, und genau dafuer wird es unten aufgerufen: Brevo weist
    # einen Kontakt mit unbekanntem Merkmal **vollstaendig** ab, nicht nur
    # das Merkmal.
    ("UTM_SOURCE", "text"),
    ("UTM_MEDIUM", "text"),
    ("UTM_CAMPAIGN", "text"),
    ("UTM_CONTENT", "text"),
    ("UTM_TERM", "text"),
    # Die freiwillige Rufnummer (21.09.2026). Sie steht hier, weil David den
    # Lead in Brevo sieht — eine Nummer, die nur in der eigenen Datenbank
    # liegt, fuehrt zu keinem Anruf.
    ("TELEFON", "text"),
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
               quelle: str = "widget", utm: Optional[dict] = None,
               telefon: str = "") -> bool:
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
            # Einmal lesen, nur Fehlendes anlegen. Die alte Schleife schrieb
            # je Uebertragung neun ERROR-Zeilen ins Protokoll, weil Brevo ein
            # vorhandenes Merkmal mit 400 ablehnt (20.09.2026).
            brevo.ensure_attributes(MERKMALE)

            merkmale = {"WEBSITE": website, "ANALYSE_QUELLE": quelle}
            if score is not None:
                merkmale["ANALYSE_SCORE"] = score
            if stufe:
                merkmale["ANALYSE_STUFE"] = stufe
            # **Leere Werte gehen nicht mit.** Ein leeres UTM_CONTENT in
            # Brevo saehe aus wie „Kampagne ohne Karte"; fehlt es, ist
            # sichtbar, dass nichts erhoben wurde.
            for name, wert in (utm or {}).items():
                if wert:
                    merkmale[name.upper()] = wert
            # Aus demselben Grund wie oben: Ein leeres TELEFON in Brevo saehe
            # aus wie „Nummer angegeben, aber leer". Fehlt das Merkmal, ist
            # sichtbar, dass kein Anruf gewuenscht ist.
            if telefon:
                merkmale["TELEFON"] = telefon

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
        # **Nicht mehr still.** Hier stand ein blankes `return`. `uebertrage`
        # protokolliert den Fall („Keine Brevo-Liste eingerichtet"), wird aber
        # nie erreicht — also schwieg das System vollstaendig, wenn die
        # Listen-ID fehlte.
        #
        # Am 17.09.2026 gemessen, und es war kein theoretischer Fall: Zwischen
        # dem 03.09. und 13.09. haben **neun** Adressen bestaetigt, darunter
        # zwei echte Interessenten. Zu keiner einzigen steht eine Brevo-Zeile
        # im Protokoll — weder Erfolg noch Misserfolg. Genau diese Abwesenheit
        # ist die Signatur des stillen `return`, und sie war vierzehn Tage
        # lang nicht von „laeuft alles" zu unterscheiden.
        logger.warning(
            "Brevo-Uebertragung uebersprungen (%s, Anfrage %s): keine "
            "Listen-ID gesetzt. Erwartet werden BREVO_LIST_VERIFIED_ID und "
            "BREVO_LIST_OPTIN_ID in der Umgebung.", quelle, request_id)
        return

    from database import AuditResult, SessionLocal, WidgetRequest

    db = SessionLocal()
    try:
        row = db.query(WidgetRequest).filter(WidgetRequest.id == request_id).first()
        if not row:
            return
        audit = (db.query(AuditResult).filter(AuditResult.id == row.audit_id).first()
                 if row.audit_id else None)
        # Die Herkunft steht am **Betrieb**, nicht an der Anfrage: Der Lead
        # wird beim ersten Kontakt angelegt und traegt sie seither.
        from database import Lead

        lead = (db.query(Lead).filter(Lead.id == row.lead_id).first()
                if row.lead_id else None)
        utm = {name: getattr(lead, name, "") or ""
               for name in ("utm_source", "utm_medium", "utm_campaign",
                            "utm_content", "utm_term")} if lead else {}
        uebertrage(
            email=row.email,
            listen_id=listen_id,
            website=row.website_url or "",
            score=getattr(audit, "total_score", None),
            stufe=getattr(audit, "level", "") or "",
            quelle=quelle,
            utm=utm,
            # Nur wenn der Wunsch dasteht. `row.telefon` ist ohne ihn ohnehin
            # leer — die zweite Pruefung kostet nichts und haelt die Regel an
            # der Stelle fest, an der die Nummer das Haus verlaesst.
            telefon=(row.telefon or "") if getattr(row, "anruf_gewuenscht", False) else "",
        )
    finally:
        db.close()
