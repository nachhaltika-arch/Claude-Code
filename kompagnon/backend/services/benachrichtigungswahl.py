# -*- coding: utf-8 -*-
'''Welche Mails ein Kunde bekommen möchte — und welche er bekommen muss.

**Der Anlass (06.09.2026).** Die Kontoverwaltung im Kundenkonto bekommt einen
Bereich „Benachrichtigungen". Bis dahin gab es je Nutzer **keine** Einstellung;
jede Mail ging an jeden, für den sie fällig war.

**Die wichtigste Unterscheidung steht in diesem Katalog: abwählbar oder
nicht.** Nicht jede Mail ist eine Werbemail. Eine Rechnung, eine
Freigabeanfrage mit Fünf-Tage-Frist, eine Zugangsdaten-Mail — das sind
Schritte eines Vertrags, keine Benachrichtigungen. Sie hier abwählbar zu
machen wäre bequem gebaut und im Streitfall teuer: Wer die Freigabe nie
gesehen hat, weil er sie abbestellen konnte, hat die Frist nicht versäumt.

Umgekehrt gilt: Was abwählbar ist, muss es auch wirklich sein. Ein Schalter,
der nichts tut, ist schlimmer als kein Schalter.

**Die Vorgabe ist „an".** Ein Kunde, der noch nie etwas eingestellt hat,
bekommt alles — sonst verschwände mit dieser Änderung stillschweigend Post,
die er bisher bekam.
'''
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

ABWAEHLBAR = True
PFLICHT = False


class Art:
    """Eine Mailart, wie sie im Konto erscheint."""

    def __init__(self, schluessel: str, titel: str, beschreibung: str,
                 abwaehlbar: bool, warum_pflicht: str = ""):
        self.schluessel = schluessel
        self.titel = titel
        self.beschreibung = beschreibung
        self.abwaehlbar = abwaehlbar
        self.warum_pflicht = warum_pflicht


KATALOG: Tuple[Art, ...] = (
    Art("leistungsbericht", "Monatlicher Leistungsbericht",
        "Wie sich Ladezeit und Auffindbarkeit Ihrer Seite entwickeln.",
        ABWAEHLBAR),
    Art("ki_sichtbarkeit", "Wochenbericht KI-Sichtbarkeit",
        "Ob KI-Systeme Ihren Betrieb nennen — nur beim GEO-Zusatz.",
        ABWAEHLBAR),
    Art("erinnerungen", "Erinnerungen an offene Angaben",
        "Wenn wir auf etwas von Ihnen warten und die Bauzeit stillsteht.",
        ABWAEHLBAR),
    Art("akademie", "Neues in der Akademie",
        "Wenn ein neuer Kurs oder eine Anleitung dazukommt.",
        ABWAEHLBAR),

    # ── Was bleibt, und warum ────────────────────────────────
    Art("freigaben", "Freigabeanfragen",
        "Wenn wir Ihnen etwas zur Freigabe vorlegen.",
        PFLICHT,
        "Daran hängt eine Frist von fünf Werktagen. Wer die Anfrage nicht "
        "bekommt, versäumt sie nicht — und dann steht Aussage gegen Aussage."),
    Art("rechnungen", "Rechnungen und Zahlungsbelege",
        "Rechnungen, Mahnungen und Belege zu Ihrem Abo.",
        PFLICHT,
        "Rechnungen sind Teil des Vertrags und müssen zugehen."),
    Art("konto", "Zugang und Sicherheit",
        "Zugangsdaten, Passwortänderungen, neue Anmeldungen.",
        PFLICHT,
        "Ohne diese Nachrichten bemerkt niemand einen fremden Zugriff."),
)

NACH_SCHLUESSEL = {a.schluessel: a for a in KATALOG}


class NichtAbwaehlbar(ValueError):
    """Der Versuch, eine Pflichtnachricht abzustellen."""


def stand(db, user_id: int) -> list:
    """Was der Kunde eingestellt hat — mit Vorgabe „an" für alles Ungesagte."""
    from modelle_konten import BenachrichtigungsWahl

    gesetzt = {}
    try:
        gesetzt = {w.schluessel: w.an for w in
                   db.query(BenachrichtigungsWahl)
                     .filter(BenachrichtigungsWahl.user_id == user_id).all()}
    except Exception:  # noqa: BLE001 — eine fehlende Tabelle kippt die Seite nicht
        db.rollback()
        logger.warning("Benachrichtigungswahl nicht lesbar (user %s)", user_id)

    return [{
        "schluessel": a.schluessel,
        "titel": a.titel,
        "beschreibung": a.beschreibung,
        "abwaehlbar": a.abwaehlbar,
        "warum_pflicht": a.warum_pflicht,
        # Pflichtnachrichten stehen immer auf „an" — auch wenn irgendwann
        # eine Zeile das Gegenteil behauptet. Der Katalog gewinnt.
        "an": True if not a.abwaehlbar else gesetzt.get(a.schluessel, True),
    } for a in KATALOG]


def setze(db, *, user_id: int, schluessel: str, an: bool) -> dict:
    """Eine Wahl speichern. Pflichtnachrichten weist sie ab."""
    from modelle_konten import BenachrichtigungsWahl

    art = NACH_SCHLUESSEL.get(schluessel)
    if art is None:
        raise ValueError(f"Unbekannte Benachrichtigungsart: {schluessel}")
    if not art.abwaehlbar:
        raise NichtAbwaehlbar(art.warum_pflicht or
                              "Diese Nachricht gehört zum Vertrag.")

    zeile = (db.query(BenachrichtigungsWahl)
               .filter(BenachrichtigungsWahl.user_id == user_id,
                       BenachrichtigungsWahl.schluessel == schluessel)
               .first())
    if zeile is None:
        zeile = BenachrichtigungsWahl(user_id=user_id, schluessel=schluessel)
        db.add(zeile)
    zeile.an = bool(an)
    db.commit()
    return {"schluessel": schluessel, "an": bool(an)}


def moechte(db, user_id: int, schluessel: str) -> bool:
    '''Darf diese Mail an diesen Nutzer? — für den Versand.

    **Der Schalter wirkt nur, wenn ihn jemand fragt.** Diese Funktion ist die
    Stelle, an der die Einstellung Wirkung bekommt; ohne Aufruf wäre die
    Oberfläche eine Attrappe.
    '''
    art = NACH_SCHLUESSEL.get(schluessel)
    if art is None or not art.abwaehlbar:
        return True
    for eintrag in stand(db, user_id):
        if eintrag["schluessel"] == schluessel:
            return bool(eintrag["an"])
    return True
