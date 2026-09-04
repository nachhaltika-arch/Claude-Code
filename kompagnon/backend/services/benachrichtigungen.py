# -*- coding: utf-8 -*-
"""Melden, dass sich ein Kunde gemeldet hat (L-18).

**Der Anlass (26.08.2026, David):** „ich brauche eine notification für
tickets, chat oder email die wir vom kunden erhalten."

**Was vorher geschah, wenn ein Kunde sich meldete:** Bei einem Ticket nichts
— `create_ticket` schrieb eine Zeile und schwieg. Bei einer Chatnachricht
eine Mail an `SMTP_USER`, eine feste Adresse aus der Umgebung. Eine Mail vom
Kunden kam gar nicht erst im Werkzeug an.

**Eine Stelle, drei Quellen.** Wer eine vierte hinzufügt, ruft `melden` — er
muss nicht wissen, wo die Glocke hängt, und die Glocke muss nicht wissen, was
es alles gibt.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

#: Die Quellen, die es gibt. Kein Enum in der Datenbank: Eine vierte soll
#: eine Zeile kosten und keine Migration. Die Liste hier ist trotzdem
#: nützlich — sie sagt, was gemeint ist, und ein Test hält sie fest.
ARTEN = ("ticket", "chat", "mail", "faellig")
#: `faellig` kam am 01.09.2026 dazu (L-101): keine Meldung **eines**
#: Kunden, sondern eine Aufgabe mit Termin — das Quartals-Re-Audit der
#: Pflege-Abos. Sie steht bewusst in derselben Glocke: Wer zwei Orte
#: fuer „was ist zu tun" hat, sieht irgendwann in keinen von beiden.


def melden(db, art: str, titel: str, hinweis: str = "", ziel: str = "",
           lead_id=None) -> int:
    """Eine Meldung anlegen und ihre Kennung zurückgeben.

    `ziel` ist ein Pfad im Werkzeug — wohin der Klick führt. Eine Meldung
    ohne Weg dorthin verlangt vom Leser, die Nummer zu merken und selbst zu
    suchen; dieselbe Lehre wie bei den Warnungen auf dem Dashboard.
    """
    from database import Benachrichtigung

    if art not in ARTEN:
        # Kein Abbruch: Eine unbekannte Art ist ein Programmierfehler, aber
        # keiner, der den Vorgang des Kunden zerreißen darf.
        logger.warning("Unbekannte Benachrichtigungsart %r — wird trotzdem "
                       "abgelegt", art)

    zeile = Benachrichtigung(
        art=art, titel=titel[:300], hinweis=hinweis or "",
        ziel=ziel or "", lead_id=lead_id, erstellt_am=datetime.utcnow(),
    )
    db.add(zeile)
    db.commit()
    db.refresh(zeile)
    return zeile.id


def melden_leise(db, **felder) -> None:
    """`melden`, aber ein Fehler bleibt im Protokoll statt im Vorgang.

    **Warum es diese zweite Fassung gibt.** Die Meldung ist Beiwerk, die
    Nachricht des Kunden ist die Hauptsache. Genau andersherum ging am Morgen
    des 26.08.2026 die Willkommensmail nach jeder Stripe-Zahlung verloren: Ein
    falsches Schlüsselwort im **Anhang** riss den ganzen Versand mit, und ein
    breites `except` schluckte es.

    Wer aus einem Kundenvorgang heraus meldet, nimmt diese Fassung.
    """
    try:
        melden(db, **felder)
    except Exception as fehler:      # noqa: BLE001 — siehe oben
        try:
            db.rollback()
        except Exception:            # noqa: BLE001
            pass
        logger.warning("Benachrichtigung nicht abgelegt (%s): %s",
                       felder.get("art"), fehler)
