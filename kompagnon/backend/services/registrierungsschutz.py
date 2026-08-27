# -*- coding: utf-8 -*-
"""Eine Grenze für das öffentliche Registrierungsformular.

**Der Anlass (27.08.2026).** `POST /api/auth/register` ist über `/register`
ohne Anmeldung erreichbar und schreibt bei jedem Aufruf eine Zeile in
`users` — ungedrosselt. Es gibt im ganzen Bestand keine Drosselung; das fiel
auf, als David entschied, dass die Selbstregistrierung bleiben soll.

**Was das hier ist und was nicht.** Es ist ein Zähler im Arbeitsspeicher,
nach Herkunftsadresse getrennt, mit einem gleitenden Fenster. Es ist
**keine** Abwehr gegen jemanden, der über viele Adressen kommt — dafür
bräuchte es eine Ebene davor (Cloudflare, Render). Es hält den einfachen
Fall auf, und der einfache Fall ist der häufige.

> Das steht hier so ausdrücklich, weil eine Drosselung, deren Grenzen man
> nicht kennt, gefährlicher ist als keine: Man hört auf zu suchen.

**Warum im Arbeitsspeicher und nicht in der Datenbank.** Der Dienst läuft mit
einer Instanz (`numInstances: 1`); ein Neustart setzt den Zähler zurück, und
das ist verschmerzbar. Eine Tabelle dafür hiesse, bei jedem Aufruf des
öffentlichen Formulars zu schreiben — also genau das zu tun, wovor die
Drosselung schützen soll.

**Zwei Regeln, die beide begründet sind:**

1. **Je Herkunft, nicht global.** Ein globaler Zähler wäre kein Schutz,
   sondern der Ausfall, den ein Angreifer herbeiführen will: Er sperrt mit
   ein paar Aufrufen alle echten Kunden aus.
2. **Ohne erkennbare Herkunft wird nicht gesperrt.** Fehlt die Adresse, ist
   die Frage nicht beantwortbar — und eine unbeantwortbare Frage darf
   niemanden aussperren.
"""
import logging
import threading
import time

logger = logging.getLogger(__name__)

#: Wie viele Registrierungen eine Herkunft im Fenster darf. Bewusst
#: großzügig: Ein Betrieb, in dem mehrere Menschen hinter derselben
#: Firmen-IP sitzen, soll sich nacheinander anmelden können.
HOECHSTENS = 10

#: Die Länge des gleitenden Fensters in Sekunden.
FENSTER_S = 3600

_schloss = threading.Lock()
_versuche: dict[str, list[float]] = {}


def _jetzt() -> float:
    return time.monotonic()


def _aufraeumen(marken: list[float], jetzt: float) -> list[float]:
    return [m for m in marken if jetzt - m < FENSTER_S]


def vermerken(herkunft: str | None) -> None:
    """Einen Versuch zählen."""
    if not herkunft:
        return
    jetzt = _jetzt()
    with _schloss:
        marken = _aufraeumen(_versuche.get(herkunft, []), jetzt)
        marken.append(jetzt)
        _versuche[herkunft] = marken


def zu_viele(herkunft: str | None) -> bool:
    """Hat diese Herkunft ihr Kontingent im Fenster ausgeschöpft?"""
    if not herkunft:
        return False
    jetzt = _jetzt()
    with _schloss:
        marken = _aufraeumen(_versuche.get(herkunft, []), jetzt)
        _versuche[herkunft] = marken
        return len(marken) >= HOECHSTENS


def zuruecksetzen() -> None:
    """Alles vergessen. Für Tests — der Zähler ist prozessweit."""
    with _schloss:
        _versuche.clear()


def herkunft_aus(request) -> str:
    """Die Adresse des Aufrufers, so gut es geht.

    Hinter Renders Proxy steht die echte Adresse in `X-Forwarded-For`;
    `request.client.host` wäre dort immer der Proxy — also **eine** Herkunft
    für alle, und die Drosselung sperrte nach zehn Registrierungen jeden aus.

    Genommen wird der **erste** Eintrag: Das ist der ursprüngliche Aufrufer.
    Er ist fälschbar — deshalb steht im Kopf dieses Moduls, dass dies keine
    Abwehr gegen einen entschlossenen Angreifer ist.
    """
    weiter = (request.headers.get("x-forwarded-for") or "").split(",")
    if weiter and weiter[0].strip():
        return weiter[0].strip()
    klient = getattr(request, "client", None)
    return getattr(klient, "host", "") or ""
