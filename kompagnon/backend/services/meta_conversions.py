# -*- coding: utf-8 -*-
"""Lead-Ereignisse an die Meta Conversions API — der zweite Meldeweg.

**Warum es diesen Weg überhaupt gibt.** Bis hierher meldete nur der Browser:
Das Widget lädt beim Absenden `fbevents.js` nach und feuert `Lead`. Dieser Weg
bricht regelmäßig weg — Adblocker, „Do Not Track", iOS-Beschränkungen, ein
Consent-Banner, das Skripte von Drittanbietern blockiert. Gemessen am
08.09.2026: sechs Lead-Ereignisse insgesamt, Qualität des Abgleichs 6,1 von 10,
und die Conversions-API-Verknüpfung im Konto hatte seit 46 Tagen nichts
erhalten. Der Serverweg fällt nicht aus, wenn im Browser etwas blockiert.

**Der eigentliche Zweck ist aber die Zuordnung.** Das Widget läuft in einem
iframe auf einer fremden Domain. Es sieht die Klick-ID (`fbclid`) der
Trägerseite nicht, und ohne sie ist eine Meldung eine Meldung ohne Herkunft:
Meta weiß, dass jemand ein Formular abgeschickt hat, aber nicht, welche Anzeige
ihn gebracht hat. Hier wird beides zusammengeführt — die Klick-ID, sofern die
Trägerseite sie durchreicht, und die gehashte E-Mail-Adresse als zweiter,
unabhängiger Abgleichschlüssel.

**Doppelzählung ist ausgeschlossen, nicht nur unwahrscheinlich.** Browser- und
Servermeldung tragen dieselbe `event_id`. Meta verwirft die zweite. Deshalb
darf beides gleichzeitig laufen, auch während der Umstellung.

**Was hier nicht passiert.** Es wird nichts im Klartext übertragen, was Meta
nicht ohnehin bekäme: Die E-Mail-Adresse wird vor dem Versand mit SHA-256
gehasht, so wie Meta es für den erweiterten Abgleich vorschreibt. Ohne
Zugangstoken in der Umgebung passiert gar nichts — kein Fehler, kein Abbruch,
nur eine Zeile im Protokoll. Ein fehlender Token darf niemals eine Analyse
verhindern; der Besucher hat mit unserer Messung nichts zu schaffen.
"""
import hashlib
import logging
import os
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

API_VERSION = "v21.0"
TIMEOUT = 10.0

#: Meta verlangt genau diese Schreibweise: `fb.<subdomain-index>.<zeit>.<klick-id>`.
FBC_MUSTER = "fb.1.{zeit}.{klick_id}"


def zugangstoken() -> str:
    return os.getenv("META_CAPI_ACCESS_TOKEN", "").strip()


def testereignis_code() -> str:
    """Optional. Gesetzt landen die Meldungen in „Events testen"."""
    return os.getenv("META_TEST_EVENT_CODE", "").strip()


def verfuegbar() -> bool:
    return bool(zugangstoken())


def _hash(wert: str) -> Optional[str]:
    """SHA-256 über den normalisierten Wert — so verlangt es Meta.

    Kleinschreibung und getrimmt, sonst trifft der Abgleich nicht. Leere Werte
    ergeben nichts: Ein Hash über den leeren String wäre für jeden Datensatz
    derselbe und würde wildfremde Menschen miteinander verknüpfen.
    """
    sauber = (wert or "").strip().lower()
    if not sauber:
        return None
    return hashlib.sha256(sauber.encode("utf-8")).hexdigest()


def _pixel_id(db=None) -> str:
    """Die Nummer aus der Umgebung, sonst die aus den Widget-Einstellungen.

    Zwei Quellen, weil die Umgebung im Zweifel gewinnen soll: Wer den Serverweg
    auf einen anderen Datensatz legen muss, tut das ohne Datenbankeingriff.
    """
    aus_umgebung = os.getenv("META_PIXEL_ID", "").strip()
    if aus_umgebung:
        return aus_umgebung
    if db is None:
        return ""
    try:
        from services.app_settings import get as einstellung
        return (einstellung(db, "widget_facebook_pixel_id") or "").strip()
    except Exception:
        return ""


def klick_kennung(fbclid: str, fbc: str = "") -> Optional[str]:
    """Die `_fbc`-Kennung, wie der Browser sie selbst gesetzt hätte.

    Reicht die Trägerseite ein fertiges `fbc` durch, gilt das. Sonst wird es
    aus der Klick-ID gebaut. Beides fehlt, wenn niemand die Parameter
    durchreicht — dann bleibt der E-Mail-Abgleich als einziger Schlüssel.
    """
    fertig = (fbc or "").strip()
    if fertig.startswith("fb."):
        return fertig
    kennung = (fbclid or "").strip()
    if not kennung:
        return None
    return FBC_MUSTER.format(zeit=int(time.time() * 1000), klick_id=kennung)


def sende_lead(
    *,
    email: str,
    event_id: str,
    quell_url: str = "",
    ip: str = "",
    user_agent: str = "",
    fbclid: str = "",
    fbc: str = "",
    fbp: str = "",
    db=None,
) -> bool:
    """Meldet ein `Lead`-Ereignis serverseitig. Wirft nie.

    :param event_id: dieselbe Kennung, die der Browser mitsendet. Ohne sie
        zählt Meta zweimal.
    :returns: True, wenn Meta die Meldung angenommen hat.
    """
    token = zugangstoken()
    pixel = _pixel_id(db)
    if not token or not pixel:
        logger.info("Meta CAPI: kein Token oder keine Pixel-ID — nichts gesendet.")
        return False

    nutzerdaten = {}
    gehashte_mail = _hash(email)
    if gehashte_mail:
        nutzerdaten["em"] = [gehashte_mail]
    if ip:
        nutzerdaten["client_ip_address"] = ip
    if user_agent:
        nutzerdaten["client_user_agent"] = user_agent
    kennung = klick_kennung(fbclid, fbc)
    if kennung:
        nutzerdaten["fbc"] = kennung
    if (fbp or "").strip():
        nutzerdaten["fbp"] = fbp.strip()

    # Ohne mindestens einen Abgleichschlüssel ist die Meldung wertlos: Meta
    # nimmt sie an und ordnet sie niemandem zu. Dann lieber gar nicht senden,
    # sonst steht im Konto eine Zahl, die nichts bedeutet.
    if not any(k in nutzerdaten for k in ("em", "fbc", "fbp")):
        logger.info("Meta CAPI: kein Abgleichschlüssel vorhanden — nichts gesendet.")
        return False

    ereignis = {
        "event_name": "Lead",
        "event_time": int(time.time()),
        "event_id": event_id,
        "action_source": "website",
        "user_data": nutzerdaten,
    }
    if quell_url:
        ereignis["event_source_url"] = quell_url[:500]

    rumpf = {"data": [ereignis]}
    code = testereignis_code()
    if code:
        rumpf["test_event_code"] = code

    url = f"https://graph.facebook.com/{API_VERSION}/{pixel}/events"
    try:
        antwort = httpx.post(
            url,
            params={"access_token": token},
            json=rumpf,
            timeout=TIMEOUT,
        )
        if antwort.status_code >= 400:
            # Der Text von Meta nennt das konkrete Feld. Ohne ihn im Protokoll
            # sucht man am falschen Ende.
            logger.warning(
                "Meta CAPI abgelehnt (%s): %s",
                antwort.status_code, antwort.text[:400],
            )
            return False
        logger.info("Meta CAPI: Lead gemeldet (event_id=%s).", event_id)
        return True
    except Exception as fehler:  # noqa: BLE001
        logger.warning("Meta CAPI nicht erreichbar: %s", fehler)
        return False
