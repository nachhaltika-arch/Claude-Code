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
Trägerseite sie durchreicht, und der `fbp`-Wert, sofern der Pixel auf ihr
läuft. **Die E-Mail-Adresse wird nicht mehr mitgesendet** (10.09.2026) — siehe
unten.

**Doppelzählung ist ausgeschlossen, nicht nur unwahrscheinlich.** Browser- und
Servermeldung tragen dieselbe `event_id`. Meta verwirft die zweite. Deshalb
darf beides gleichzeitig laufen, auch während der Umstellung.

**Was hier nicht passiert.** Die E-Mail-Adresse verlässt das System auf
diesem Weg überhaupt nicht — auch nicht gehasht (Entscheidung David,
10.09.2026). Sie ging bis dahin als SHA-256-Wert mit, was Metas erweiterter
Abgleich vorsieht; der Einwilligungstext im Widget nennt diesen Zweck nicht
mehr, und was keine Einwilligung deckt, wird nicht übertragen. Übrig bleiben
Klick-ID, IP und User-Agent. Ohne Zugangstoken in der Umgebung passiert gar
nichts — kein Fehler, kein Abbruch,
nur eine Zeile im Protokoll. Ein fehlender Token darf niemals eine Analyse
verhindern; der Besucher hat mit unserer Messung nichts zu schaffen.
"""
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


# `_hash` stand hier: SHA-256 über die normalisierte E-Mail-Adresse für Metas
# erweiterten Abgleich. Entfernt am 10.09.2026 mit dem Abgleich selbst — eine
# Hashfunktion, die niemand aufruft, liest sich beim naechsten Mal wie eine
# Zusicherung, dass hier noch gehasht wird.


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


def zustand(db=None) -> dict:
    """Kann der Serverweg ueberhaupt melden? — die Auskunft fuer `/health`.

    **Warum das hier steht und nicht nur `verfuegbar()`.** Die Funktion gab es
    seit dem 08.09., aber kein Endpunkt rief sie auf. Am 09.09. war die Frage
    „ist der Token gesetzt?" damit von aussen unbeantwortbar — waehrend fuer
    Stripe, die Uploads, den Browserlauf und die Dateiablage genau diese
    Auskunft seit Wochen offensteht. Dieselbe Lehre wie dort: **Ein Dashboard
    zeigt die Einstellung, nicht den Zustand des Prozesses.**

    **Zwei Werte, und beide muessen da sein.** Ohne Token schweigt der Weg;
    ohne Datensatznummer gibt es kein Ziel, und Meta lehnt die Meldung ab.
    `bereit` sagt deshalb nicht „Token da", sondern „es kann etwas ankommen".

    **Gemeldet wird nie ein Wert.** `/health` ist offen. Ja/Nein und Laenge
    genuegen: Ein CAPI-Token ist gut 200 Zeichen lang; steht dort 30, hat
    jemand beim Einfuegen etwas verloren. Die Pixelnummer ist zwar nicht
    geheim — sie steht ohnehin in `/api/widget/config` —, aber die Regel
    dieser Route bleibt einheitlich: Sie nennt Zustaende, keine Werte.
    """
    token = zugangstoken()
    pixel = _pixel_id(db)

    if os.getenv("META_PIXEL_ID", "").strip():
        quelle = "umgebung"
    elif pixel:
        quelle = "einstellung"
    else:
        quelle = ""

    return {
        "token_gesetzt": bool(token),
        "token_laenge": len(token),
        "pixel_gesetzt": bool(pixel),
        # Woher die Nummer kommt — sonst sucht jemand in der Datenbank, was
        # in Render steht, oder umgekehrt.
        "pixel_quelle": quelle,
        # Laeuft die Kampagne noch im Probebetrieb? Meldungen mit diesem Code
        # landen in „Events testen" und **nicht** in der Auswertung.
        "testereignis": bool(testereignis_code()),
        "bereit": bool(token and pixel),
        "variablen": ["META_CAPI_ACCESS_TOKEN", "META_PIXEL_ID"],
        "wofuer": (
            "Lead-Meldung an die Meta Conversions API. Ohne sie misst nur der "
            "Browser — und der faellt bei Adblockern, iOS und blockierten "
            "Drittskripten aus."
        ),
    }


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


#: Werte, die als ausdrueckliches Nein der Traegerseite gelten.
#: Bleibt als Begriff erhalten — das Widget wertet ihn aus, bevor es sendet.
NEIN = ("0", "false")

#: Werte, die als ausdrueckliches Ja der Traegerseite gelten. Alles andere,
#: auch ein leerer oder unbekannter Wert, ist kein Ja.
JA = ("1", "true")


def darf_melden(consent_tracking) -> bool:
    """Darf dieser Lead an Meta gemeldet werden?

    **Nur bei einem ausdruecklichen Ja der Traegerseite** (10.09.2026).

    Die Regel hat sich zweimal gedreht, und beide Male aus demselben Grund:
    Die Einwilligung muss den Zweck nennen, an dem sie haengt.

    - Bis 08.09.: nur `consent_tracking`, also der Parameter der Traegerseite.
      Das Haekchen im Formular wurde gar nicht gelesen.
    - 08.09. bis 09.09.: Haekchen **und** kein Nein von oben. Das trug, weil
      der Haekchen-Text Meta ausdruecklich nannte.
    - Seit 10.09.: Der Haekchen-Text nennt Meta nicht mehr (Entscheidung
      David) und der erweiterte Abgleich ist entfallen. Ein Haekchen, das von
      Auswertungsmails spricht, kann keine Uebermittlung an ein Werbenetzwerk
      begruenden. Es wird deshalb hier nicht mehr gefragt.

    **Schweigen ist keine Zustimmung.** § 25 TDDDG verlangt ein Ja, und das
    Widget laeuft eingebettet auf fremden Seiten, die kein Banner mitbringen.
    Ein fehlender Wert ist deshalb jetzt ein Nein — umgekehrt als vorher.

    Das ist eine bewusste Abschaltung: Auf Einbettungen ohne Consent-Signal
    gab es nie eine Rechtsgrundlage. Die eigene Landingpage muss `consent=1`
    mitgeben oder `{type:'kpg-consent', marketing:true}` ins iframe senden,
    sonst wird nichts gemeldet. Der Preis der Klarheit ist, dass eine
    vergessene Einbettung still nicht mehr misst — dagegen steht der
    Befund-Test unten und die Pruefliste im Projektdokument.
    """
    return (str(consent_tracking or "").strip().lower()) in JA


def sende_lead(
    *,
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

    # **Kein erweiterter Abgleich mehr** (Entscheidung David, 10.09.2026).
    # Hier stand die mit SHA-256 gehashte E-Mail-Adresse als zweiter
    # Abgleichschluessel. Sie ist entfallen, weil der Einwilligungstext im
    # Widget sie nicht mehr nennt — und eine Uebermittlung, die keine
    # Einwilligung deckt, darf nicht stattfinden, auch nicht gehasht.
    # Die Zuordnung zur Anzeige traegt `fbc`; das war immer der tragende Teil.
    nutzerdaten = {}
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
    if not any(k in nutzerdaten for k in ("fbc", "fbp")):
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
