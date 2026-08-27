# -*- coding: utf-8 -*-
"""Welche Meldung zusätzlich per Mail kommt (Entscheidung David, 26.08.2026).

**Der Anlass.** Unter Einstellungen → Benachrichtigungen standen sechs
Ankreuzfelder und ein „Speichern"-Knopf, der grün meldete und nichts sendete.
Kein Backend las die sechs Schlüssel; es gab nicht einmal eine Stelle, an die
sie hätten gehen können. Sie sind am selben Tag entfernt worden — ein Feld,
das nichts schaltet, ist schlimmer als keines, weil es die Suche beendet.

**Nachtrag 27.08.2026.** Das vierte Ereignis geht an den **Kunden** und nicht
an David — die Trennung unten gilt also nicht mehr wortwörtlich. Es steht
trotzdem hier: Die Einstellungsseite holt ihre Liste von hier, und ein
zweiter Ort für Schalter wäre ein zweiter Ort, an dem sie auseinanderlaufen.

**Hier wird nichts erfunden.** Nachgezählt, welche Mails überhaupt in
Davids eigenes Postfach gehen, gab es am 26.08. genau zwei: die Chatnachricht vom
Kunden (`routers/messages.py` → `SMTP_USER`) und den monatlichen GEO-Bericht
(`services/geo_monitor.py` → `ADMIN_EMAIL`). Alles andere geht an **Kunden**
und wird vom Versandschalter und von `project.email_notifications_enabled`
geregelt — nicht von hier.

**Das dritte Ereignis gab es noch nicht**, und sein Schalter steht deshalb
aus: Ein neues Ticket meldet bisher nur die Glocke. Die Vorgabe jedes
Schalters ist genau das Verhalten von heute — wer nichts umstellt, merkt von
dieser Änderung nichts. Das ist die Bedingung, unter der man Schalter
nachrüsten darf.

**Die Glocke bleibt unberührt.** Sie meldet weiterhin alles; hier geht es nur
darum, was **zusätzlich** den Weg ins Postfach nimmt. Eine Meldung stumm zu
schalten, die im Werkzeug sichtbar ist, wäre etwas anderes — und niemand hat
danach gefragt.
"""
import logging

logger = logging.getLogger(__name__)

#: (Schlüssel, Beschriftung, Vorgabe). Die Beschriftung steht hier und nicht
#: in der Oberfläche: Ein Schlüssel ohne Text wird dort zu `chat_mail`, und
#: dann rät der Leser, was er gerade abschaltet.
EREIGNISSE = (
    ("chat_mail",
     "Chatnachricht vom Kunden auch per E-Mail (die Glocke meldet sie ohnehin)",
     True),
    ("ticket_mail",
     "Neues Ticket auch per E-Mail (bisher nur in der Glocke)",
     False),
    ("geo_bericht",
     "Monatlicher GEO-Bericht per E-Mail an die Admin-Adresse",
     True),
    # **Das vierte Ereignis geht an den Kunden, nicht an David** — und
    # weicht damit von dem ab, was oben steht. Es steht trotzdem hier, weil
    # es ein Schalter ist und die Einstellungsseite ihre Liste von hier
    # holt; ein zweiter Ort waere ein zweiter Ort. Warum die Vorgabe „an"
    # ist und nicht „das Verhalten von heute": siehe
    # `services/kundenmeldung.py` — das Verhalten von heute war, dass die
    # Nachricht niemanden erreichte.
    ("kunde_portalnachricht",
     "Kunde per E-Mail darauf hinweisen, dass eine Portalnachricht fuer ihn "
     "bereitliegt (ohne den Text)",
     True),
)

_VORGABE = {schluessel: vorgabe for schluessel, _, vorgabe in EREIGNISSE}
_TEXT = {schluessel: text for schluessel, text, _ in EREIGNISSE}


def _pruefen(schluessel: str) -> None:
    """Ein unbekannter Schlüssel ist ein Fehler, kein stilles Nichts.

    Sonst legt ein Tippfehler in der Oberfläche eine Zeile an, die niemand
    liest — und der Schalter, den der Nutzer meinte, bleibt, wo er war. Der
    Knopf meldet Erfolg, nichts geschieht: genau der Zustand, aus dem dieser
    Dienst entstanden ist.
    """
    if schluessel not in _VORGABE:
        raise ValueError(f"Unbekanntes Meldungsereignis: {schluessel!r}")


def soll_melden(db, schluessel: str) -> bool:
    """Darf dieses Ereignis eine Mail auslösen?"""
    from database import Meldungsvorliebe

    _pruefen(schluessel)
    zeile = db.query(Meldungsvorliebe).filter(
        Meldungsvorliebe.schluessel == schluessel).first()
    return _VORGABE[schluessel] if zeile is None else bool(zeile.aktiv)


def soll_melden_leise(db, schluessel: str) -> bool:
    """`soll_melden`, aber ein Fehler entscheidet nicht gegen den Versand.

    **Warum die Richtung so herum.** Wer diese Frage stellt, steht kurz vor
    einem Versand, der bisher stattfand. Bricht die Abfrage — kaputte
    Verbindung, fehlende Tabelle nach einem halben Deploy —, dann soll die
    Mail rausgehen wie bisher und nicht stillschweigend ausfallen. Ein
    Schalter, der bei Stoerung abschaltet, ist ein Ausfall mit Begruendung.
    """
    try:
        return soll_melden(db, schluessel)
    except Exception as fehler:      # noqa: BLE001
        logger.warning("Meldungsvorliebe %r nicht lesbar (%s) — es bleibt "
                       "beim bisherigen Verhalten", schluessel, fehler)
        return _VORGABE.get(schluessel, True)


def setzen(db, schluessel: str, aktiv: bool) -> None:
    """Einen Schalter umlegen."""
    from datetime import datetime

    from database import Meldungsvorliebe

    _pruefen(schluessel)
    zeile = db.query(Meldungsvorliebe).filter(
        Meldungsvorliebe.schluessel == schluessel).first()
    if zeile is None:
        db.add(Meldungsvorliebe(schluessel=schluessel, aktiv=bool(aktiv),
                                geaendert_am=datetime.utcnow()))
    else:
        zeile.aktiv = bool(aktiv)
        zeile.geaendert_am = datetime.utcnow()
    db.commit()


def alle(db) -> dict:
    """Jedes Ereignis mit Beschriftung und Stand — für die Oberfläche."""
    return {
        schluessel: {"text": _TEXT[schluessel],
                     "aktiv": soll_melden(db, schluessel)}
        for schluessel, _, _ in EREIGNISSE
    }
