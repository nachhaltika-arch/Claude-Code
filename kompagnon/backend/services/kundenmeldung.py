# -*- coding: utf-8 -*-
"""Der Kunde erfährt, dass eine Nachricht für ihn da ist.

**Der Befund (27.08.2026).** Schrieb der Innendienst eine Nachricht über den
Weg `in_app`, entstand eine `Message` am Betrieb — und sonst nichts. Die
Glocke (`services/benachrichtigungen.py`) meldet ausschliesslich nach innen;
der Kunde erfuhr davon erst, wenn er von sich aus das Portal öffnete.

Bei einer Rückfrage, von der ein Auftrag abhängt, ist das kein Kanal, sondern
ein Zettel in einer Schublade. Und wie bei jeder Stille sah es von aussen
aus, als gäbe es nichts zu klären.

**Warum die Mail den Text nicht mitnimmt.** Wer `in_app` wählt, hat sich
gegen den Mailweg entschieden — bei `email` geht der volle Text ohnehin
hinaus. Die Hinweismail sagt deshalb nur, *dass* etwas da ist, und führt ins
Portal. Ginge der Text mit, wäre die Wahl zwischen den beiden Wegen ohne
Unterschied, und `in_app` verschickte still doch alles.

**Zur Vorgabe.** In diesem Bestand gilt sonst: Die Vorgabe eines
nachgerüsteten Schalters ist das Verhalten von heute. Hier steht sie
bewusst auf **an**, denn das Verhalten von heute ist genau der Befund — die
Nachricht erreichte niemanden. Der Schalter ist da, damit man es abstellen
kann, nicht damit die Änderung wirkungslos bleibt.
"""
import logging

logger = logging.getLogger(__name__)

#: Der Schlüssel in `services/meldungsvorlieben.py`. Steht dort, weil die
#: Einstellungsseite ihre Liste von dort holt: Ein Schalter, den die
#: Oberfläche nicht kennt, ist keiner.
SCHLUESSEL = "kunde_portalnachricht"

BETREFF = "Neue Nachricht in Ihrem KOMPAGNON-Kundenportal"


def _rumpf(firma: str, portal_adresse: str) -> str:
    anrede = f"für {firma}" if firma else ""
    return f"""
<h3>Es liegt eine neue Nachricht für Sie bereit</h3>
<p>Guten Tag,</p>
<p>in Ihrem Kundenportal {anrede} wartet eine neue Nachricht von
KOMPAGNON auf Sie.</p>
<p><a href="{portal_adresse}">Nachricht im Kundenportal lesen</a></p>
<hr>
<p style="color:gray;font-size:12px">
  Den Inhalt sehen Sie aus Datenschutzgründen nur im Portal.
</p>
"""


def portal_adresse() -> str:
    """Wohin der Verweis führt.

    Aus der Umgebung, weil Staging und Produktiv verschiedene Adressen
    haben — ein festverdrahteter Verweis schickt den Kunden der Staging-Probe
    in die Produktivumgebung oder umgekehrt.
    """
    import os

    basis = (os.getenv("FRONTEND_URL", "").strip().rstrip("/")
             or "https://kompagnon-frontend.onrender.com")
    return f"{basis}/portal"


def hinweisen(db, lead) -> bool:
    """Dem Kunden sagen, dass etwas da ist. Gibt zurück, ob gesendet wurde.

    **Fehler bleiben hier.** Die Ablage der Nachricht ist die Hauptsache, die
    Mail nur der Hinweis darauf. Bricht der Versand, darf die Nachricht nicht
    mitfallen — sonst kostet ein Mailserver-Schluckauf den Verlauf.
    """
    adresse = (getattr(lead, "email", "") or "").strip()
    if not adresse:
        # Kein Fehler: Nicht jeder Betrieb hat eine Adresse hinterlegt. Die
        # Nachricht steht trotzdem im Portal.
        return False

    from services.meldungsvorlieben import soll_melden_leise

    if not soll_melden_leise(db, SCHLUESSEL):
        return False

    try:
        from services.email import send_email

        return bool(send_email(
            to_email=adresse,
            subject=BETREFF,
            html_body=_rumpf(getattr(lead, "company_name", "") or "",
                             portal_adresse()),
        ))
    except Exception as fehler:            # noqa: BLE001 — siehe Docstring
        logger.warning("Hinweis an %s nicht zugestellt: %s", adresse, fehler)
        return False
