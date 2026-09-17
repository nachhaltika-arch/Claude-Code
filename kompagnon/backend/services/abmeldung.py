# -*- coding: utf-8 -*-
"""Der Abmeldelink der E-Mail-Strecke — Token, Wirkung, Rueckweg (P0-11).

**Warum er gebraucht wird.** Die Sequenz geht ohne Anlass des Empfaengers
raus. Das ist Werbung im Sinne des § 7 UWG, und Art. 21 Abs. 2 DSGVO gibt
jederzeit ein Widerspruchsrecht. Beides verlangt einen Weg, der **in der
Mail selbst** steht und ohne Anmeldung, ohne Formular und ohne Begruendung
funktioniert.

**Warum der Token nicht ablaeuft.** Anders als der Gestenbeleg in
`widget_report` (der absichtlich nach einer Stunde verfaellt) muss dieser
Link gelten, solange die Mail existiert — auch in einem Archiv von naechstem
Jahr. Ein abgelaufener Abmeldelink ist rechtlich dasselbe wie keiner.

**Warum ein GET abmeldet.** Ein Klick muss reichen. Die uebliche Sorge dagegen
ist der Postfach-Scanner: Sicherheitsprodukte rufen Links in Mails automatisch
ab und koennten so jemanden abmelden, der nie geklickt hat. Eine Zwischenseite
mit Bestaetigungsknopf waere die falsche Antwort — sie macht den Widerspruch
schwerer, und genau das darf er nicht sein. Die richtige Antwort ist der
**Rueckweg**: Die Bestaetigungsseite traegt einen Link, der die Abmeldung
zuruecknimmt. Der Fehlerfall wird billig statt unmoeglich.

**Warum ein unbekannter Lead dieselbe Seite bekommt.** Wuerde die Route bei
einer geloeschten Kennung 404 melden, waere sie ein Auskunftsdienst darueber,
welche Kennungen es gibt — mit einer gueltigen Unterschrift in der Hand. Fuer
den Klickenden ist der Unterschied bedeutungslos: Er wollte keine Post mehr,
und er bekommt keine.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

#: So viele Zeichen der Unterschrift stehen im Link. 32 hexadezimale Zeichen
#: sind 128 Bit — dieselbe Laenge wie beim Gestenbeleg, und weit jenseits
#: dessen, was sich raten laesst.
UNTERSCHRIFT_LAENGE = 32


def _schluessel() -> bytes:
    """Bei jedem Aufruf gelesen, nicht beim Import.

    Ein Modulwert wird beim ersten Import eingefroren; wer ``SECRET_KEY``
    nachtraegt, muesste den Dienst neu starten, ohne zu wissen warum.
    """
    return os.getenv("SECRET_KEY", "kompagnon-widget").encode()


def _unterschrift(lead_id: int) -> str:
    stoff = f"abmeldung|{lead_id}".encode()
    return hmac.new(_schluessel(), stoff,
                    hashlib.sha256).hexdigest()[:UNTERSCHRIFT_LAENGE]


def token(lead_id: int) -> str:
    """``<kennung>.<unterschrift>`` — die Kennung steht offen darin.

    Sie ist kein Geheimnis: Wer sie aendert, macht die Unterschrift ungueltig,
    weil diese ueber die Kennung geht.
    """
    return f"{int(lead_id)}.{_unterschrift(int(lead_id))}"


def lead_aus_token(wert: Optional[str]) -> Optional[int]:
    """Die Kennung — oder ``None``, wenn der Token nicht stimmt.

    Wirft nicht. Der Aufrufer steckt in einem Klick aus einer E-Mail; jede
    kaputte Eingabe ist dort ein normaler Fall, kein Fehler des Systems.
    """
    if not wert or not isinstance(wert, str):
        return None

    roh_kennung, punkt, unterschrift = wert.partition(".")
    if not punkt or not roh_kennung.isdigit() or not unterschrift:
        return None

    # Zeitkonstanter Vergleich: Ein Vergleich, der beim ersten falschen
    # Zeichen abbricht, verraet ueber die Laufzeit, wie weit man gekommen ist.
    if not hmac.compare_digest(unterschrift, _unterschrift(int(roh_kennung))):
        return None

    return int(roh_kennung)


def abmelde_url(lead_id: int) -> str:
    from services.base_urls import api_base_url

    return f"{api_base_url()}/api/mail/abmelden/{token(lead_id)}"


def setzen(db, lead_id: int, *, aktiv: bool) -> bool:
    """Schaltet die Sequenz eines Leads. Gibt zurueck, ob eine Zeile da war.

    **Der Brevo-Austrag haengt nicht daran, ob er klappt.** Faellt Brevo aus,
    ist die Abmeldung im eigenen System trotzdem wirksam — das ist die Zusage,
    die in der Mail steht. Ein Ausfall beim Dienstleister darf sie nicht
    zuruecknehmen.
    """
    from database import Lead

    zeile = db.query(Lead).filter(Lead.id == lead_id).first()
    if not zeile:
        return False

    zeile.sequence_active = aktiv
    db.commit()

    if not aktiv and zeile.email:
        _bei_brevo_austragen(zeile.email)
    return True


def _bei_brevo_austragen(email: str) -> None:
    """Setzt ``emailBlacklisted`` — der Widerspruch gilt auch fuer Brevo.

    Wirft nie: siehe ``setzen``. Ein misslungener Austrag wird protokolliert,
    damit er nachholbar ist, und nicht verschwiegen.
    """
    try:
        from services.brevo_service import BrevoService

        with BrevoService() as brevo:
            brevo._request("PUT", f"/contacts/{email}",
                           {"emailBlacklisted": True})
        logger.info("Brevo: %s ausgetragen (Abmeldung)", email)
    except Exception as fehler:  # noqa: BLE001 — darf den Klick nicht kippen
        logger.warning("Brevo: Austrag von %s misslungen: %s", email, fehler)
