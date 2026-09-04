# -*- coding: utf-8 -*-
'''Sandbox oder echtes Geld — und passt das zur Umgebung? (04.09.2026)

**Die Entscheidung (David).** Staging bleibt dauerhaft auf Stripes Sandbox,
produktiv läuft mit Live-Schlüsseln. Beides sind getrennte Konten mit
getrennten Produkten, Preisen, Kunden und Webhook-Geheimnissen; ein Schlüssel
sagt selbst, wohin er gehört: `sk_test_…` gegen `sk_live_…`.

**Warum das eine Prüfung braucht und nicht nur eine Notiz.** Die beiden
Verwechslungen kosten Verschiedenes, und die eine ist teuer:

* **Live-Schlüssel auf Staging** — jeder Testklick bucht echtes Geld von
  echten Karten ab. Niemand merkt es, weil auf Staging niemand auf seinen
  Kontoauszug schaut. Das ist der Fall, den dieses Modul **blockiert**.
* **Test-Schlüssel produktiv** — der Kunde landet in Stripes Testkasse, seine
  echte Karte wird abgelehnt, und er hält uns für kaputt. Ärgerlich, aber es
  geht kein Geld verloren. Das ist der Fall, der hier nur **gemeldet** wird.

**Warum nicht beides blockiert wird.** Ob `ENVIRONMENT` produktiv überhaupt
gesetzt ist, war am 04.09.2026 von aussen nicht feststellbar — `/health` gab
die Umgebung nicht heraus (seither tut es das). Wäre die Variable nicht
gesetzt, gälte der Vorgabewert `development`, ein Live-Schlüssel wäre
„falsch", und eine harte Sperre legte die **produktive** Kasse still. Eine
Sperre, die aus einer fehlenden Variablen einen Umsatzausfall macht, ist
schlimmer als der Fehler, den sie verhüten soll.

Deshalb greift die Sperre nur, wo die Umgebung sich **ausdrücklich** als
nicht-produktiv bezeichnet. Alles andere wird laut gemeldet und steht in
`/health`.
'''
import logging
import os

logger = logging.getLogger(__name__)

LIVE = "live"
TEST = "test"
UNBEKANNT = "unbekannt"
FEHLT = "fehlt"

#: Umgebungen, die sich ausdruecklich als nicht-produktiv bezeichnen. Nur
#: hier wird gesperrt — bei allem anderen (auch bei einer fehlenden Angabe)
#: bleibt es bei der Meldung.
NICHT_PRODUKTIV = ("development", "dev", "local", "staging", "test")


def umgebung() -> str:
    return (os.getenv("ENVIRONMENT") or "development").strip().lower()


def ist_produktiv() -> bool:
    return umgebung() == "production"


def modus_von(schluessel: str) -> str:
    '''Was ein Schlüssel über sich selbst sagt.

    Stripe schreibt den Modus in den Schlüssel: `sk_live_…`, `sk_test_…`,
    ebenso `rk_` für eingeschränkte Schlüssel und `pk_` für öffentliche. Wir
    lesen ihn, statt ihn zu erraten — und geben `unbekannt` zurück, wenn das
    Muster nicht passt, statt auf `test` zu raten. Eine falsche Beruhigung
    wäre hier schlimmer als ein Fragezeichen.
    '''
    wert = (schluessel or "").strip()
    if not wert:
        return FEHLT
    for praefix in ("sk_", "rk_", "pk_"):
        if wert.startswith(praefix):
            rest = wert[len(praefix):]
            if rest.startswith("live_"):
                return LIVE
            if rest.startswith("test_"):
                return TEST
    return UNBEKANNT


def modus() -> str:
    """Der Modus des Schlüssels, mit dem dieser Prozess wirklich arbeitet."""
    return modus_von(os.getenv("STRIPE_SECRET_KEY", ""))


def erwarteter_modus() -> str:
    return LIVE if ist_produktiv() else TEST


def befund() -> dict:
    '''Was ist, was sein sollte, und wie schlimm die Abweichung ist.

    `schwere` kennt drei Werte: `ok`, `warnung` (gemeldet, nicht gesperrt),
    `gefahr` (gesperrt — echtes Geld in einer Umgebung, die keines bewegen
    darf).
    '''
    ist = modus()
    soll = erwarteter_modus()
    umg = umgebung()

    if ist == FEHLT:
        schwere, satz = "warnung", "Kein Stripe-Schlüssel gesetzt — es kann kein Geld ankommen."
    elif ist == soll:
        schwere, satz = "ok", f"Stripe läuft im Modus {ist}, wie für {umg} vorgesehen."
    elif ist == LIVE and umg in NICHT_PRODUKTIV:
        schwere = "gefahr"
        satz = (f"Ein **Live**-Schlüssel in der Umgebung {umg}: Jede Zahlung "
                f"hier bucht echtes Geld ab. Zahlungswege sind gesperrt.")
    else:
        schwere = "warnung"
        satz = (f"Stripe läuft im Modus {ist}, erwartet wäre {soll} "
                f"(ENVIRONMENT={umg}).")

    return {"modus": ist, "erwartet": soll, "umgebung": umg,
            "schwere": schwere, "hinweis": satz}


class FalscherModus(RuntimeError):
    """Ein Zahlungsweg, der in dieser Umgebung nicht geöffnet werden darf."""


def pruefe_oder_fehler() -> None:
    '''Vor jedem Weg, der Geld bewegt.

    Wirft nur bei `gefahr` — siehe Modulkopf. Der Warnfall wird protokolliert
    und steht in `/health`; er hält niemanden auf.
    '''
    stand = befund()
    if stand["schwere"] == "gefahr":
        logger.error("Stripe gesperrt: %s", stand["hinweis"])
        raise FalscherModus(stand["hinweis"])
    if stand["schwere"] == "warnung":
        logger.warning("Stripe: %s", stand["hinweis"])
