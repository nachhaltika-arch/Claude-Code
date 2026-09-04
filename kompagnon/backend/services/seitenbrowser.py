# -*- coding: utf-8 -*-
"""Eine Seite so sehen, wie ein Besucher sie sieht (L-107).

**Der Anlass (Entscheidung David, 26.08.2026).** Die Erhebung holt HTML über
`httpx` und führt kein JavaScript aus. Von einer React-Anwendung sieht sie
`<div id="root"></div>` und sonst nichts — beim Probelauf gegen die **eigene**
Produktivoberfläche: elf Wörter. `clientseitig_aufgebaut` verhindert seit dem
25.08., dass daraus ein Befund wird (die betroffenen Kriterien fallen aus
Zähler und Nenner). Was fehlte, war die Messung selbst.

**Die Regel bleibt: nie behaupten, gemessen zu haben.** Ist kein Browser da,
wird nicht geraten und nicht stillschweigend auf `httpx` zurückgefallen —
der Rückfall passiert, aber er steht im Ergebnis (`wie`). Ein Bericht, der
nicht sagen kann, wie er zu seinen Zahlen kam, ist die Fehlerfamilie, die
diesen Bestand am häufigsten getroffen hat.

**Ein Browser ist ein SSRF-Verstärker, und das ist hier der heikle Teil.**
`fetch_guarded` prüft **jede** Weiterleitung einzeln; ein Browser folgt ihnen
selbst und fragt niemanden. Ohne Gegenmaßnahme wäre eine Kundenwebsite, die
auf `http://169.254.169.254/` weiterleitet, ein Weg zu den Zugangsdaten des
Servers. Deshalb zwei Sperren, nicht eine:

1. Die Startadresse geht durch dieselbe Prüfung wie bisher.
2. **Jede einzelne Anfrage** des Browsers wird abgefangen und verworfen,
   wenn ihr Ziel nicht öffentlich ist — auch Bilder, Skripte und
   Weiterleitungen. Der Browser bekommt gar nicht erst die Gelegenheit.

**Warum kein Docker-Bild.** Der Dienst `iearv4-backend` im selben
Render-Konto installiert Chrome im Buildbefehl auf der normalen Laufzeit und
läuft. Die Systembibliotheken sind also da; ein eigenes Bild wäre eine
Umstellung der ganzen Auslieferung für etwas, das ohne sie geht.
"""
import asyncio
import ipaddress
import logging
import os
import socket
from urllib.parse import urlparse

from services.url_guard import _is_public_ip, check_url

logger = logging.getLogger(__name__)

from services import a11y_browser  # noqa: E402  (nach dem Logger, wie die Nachbarn)

#: Wie lange eine Seite bekommen darf, um sich aufzubauen. Grosszuegiger als
#: der `httpx`-Abruf: Ein Browser laedt Skripte nach, und genau darum geht es.
AUFBAU_MS = 15000

#: Wonach gewartet wird. `networkidle` waere ehrlicher, haengt aber an Seiten
#: mit dauerhaften Verbindungen (Chat-Widgets, Analytics-Beacons) bis zum
#: Zeitlimit. `load` plus eine kurze Ruhefrist trifft in der Praxis besser.
RUHEFRIST_MS = 1200

#: Ohne diese Variable wird kein Browser gestartet. Eine Umgebung, die ihn
#: nicht hat, soll nicht bei jeder Analyse einen Startversuch bezahlen.
SCHALTER = "AUDIT_BROWSER"


def browser_erwuenscht() -> bool:
    """Ist der Browserlauf eingeschaltet?"""
    return (os.getenv(SCHALTER, "").strip().lower()
            in ("1", "true", "yes", "on", "ja"))


def _browserdatei_vorhanden() -> bool:
    """Liegt die ausführbare Browserdatei da — nicht nur das Python-Paket?

    **Warum das getrennt geprüft wird (L-147, 28.08.2026).** Bis heute prüfte
    `browser_verfuegbar()` allein, ob sich `playwright.async_api` importieren
    lässt. Das Paket lag auf beiden Diensten vor, der **Browser** nicht:
    `/opt/render/.cache/ms-playwright/` existierte gar nicht. `/health` meldete
    trotzdem `bereit: true`, während jeder Browserlauf mit „Executable doesn't
    exist" scheiterte — und mit ihm der Bildschirmabzug und die drei
    Design-Kriterien, die daran hängen.

    Geprüft wird die Datei und **kein** Probestart: Ein Browserstart in
    `/health` kostet Sekunden und liefe in einem Endpunkt, den ein
    Überwachungsdienst im Minutentakt abruft.
    """
    import glob
    from pathlib import Path

    pfad = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if pfad == "0":
        # `0` heißt: neben das Paket, damit die Dateien den Build überleben.
        try:
            import playwright
            wurzeln = [Path(playwright.__file__).parent /
                       "driver" / "package" / ".local-browsers"]
        except Exception:           # noqa: BLE001
            return False
    elif pfad:
        wurzeln = [Path(pfad)]
    else:
        wurzeln = [Path.home() / ".cache" / "ms-playwright",
                   Path("/opt/render/.cache/ms-playwright")]

    for wurzel in wurzeln:
        if not wurzel.is_dir():
            continue
        for muster in ("chromium*/chrome-linux*/headless_shell",
                       "chromium*/chrome-linux*/chrome",
                       "chromium*/chrome-mac*/**/Chromium",
                       "chromium*/chrome-win/chrome.exe"):
            if glob.glob(str(wurzel / muster), recursive=True):
                return True
    return False


def browser_verfuegbar() -> bool:
    """Liegt Playwright vor — Paket **und** Browserdatei?

    Getrennt von `browser_erwuenscht`, damit die Auskunft zwei verschiedene
    Fragen beantworten kann: „nicht eingeschaltet" und „eingeschaltet, aber
    nicht installiert" sind verschiedene Zustände, und der zweite ist ein
    Einrichtungsfehler, der auffallen soll. **Bis zum 28.08.2026 fiel er
    trotzdem nicht auf**, weil hier nur der Import geprüft wurde.
    """
    try:
        import playwright.async_api  # noqa: F401
    except Exception:               # noqa: BLE001
        return False
    return _browserdatei_vorhanden()


def _ziel_ist_oeffentlich(url: str) -> bool:
    """Zeigt diese Adresse auf einen öffentlich erreichbaren Rechner?

    Wird für **jede** Anfrage des Browsers gefragt, nicht nur für die erste.
    Die Auflösung kostet, deshalb der kleine Zwischenspeicher: Eine Seite
    holt Dutzende Dateien von derselben Handvoll Rechner.
    """
    try:
        wirt = urlparse(url).hostname
    except Exception:               # noqa: BLE001
        return False
    if not wirt:
        return False

    if wirt in _GEPRUEFT:
        return _GEPRUEFT[wirt]

    ergebnis = True
    try:
        infos = socket.getaddrinfo(wirt, None, proto=socket.IPPROTO_TCP)
        adressen = {info[4][0] for info in infos}
        if not adressen:
            ergebnis = False
        else:
            ergebnis = all(_is_public_ip(ipaddress.ip_address(a))
                           for a in adressen)
    except Exception:               # noqa: BLE001
        # Nicht aufloesbar heisst: nicht laden. Im Zweifel zu.
        ergebnis = False

    _GEPRUEFT[wirt] = ergebnis
    return ergebnis


#: Je Lauf, nicht je Prozess — `hole_gerendert` legt ihn an und wirft ihn weg.
_GEPRUEFT: dict = {}

#: **Hoechstens ein Browser gleichzeitig.** Chromium belegt rund 300 MB. Ohne
#: diese Sperre haetten zehn gleichzeitige Analysen zehn Browser gestartet und
#: den Dienst mit dem Speicher erschlagen — ein Ausfall, der genau dann
#: eintritt, wenn viel los ist. Wer wartet, wartet Sekunden; wer nicht wartet,
#: nimmt den Dienst mit.
_EINER = asyncio.Semaphore(1)

#: Cookienamen, die **keine** technische Notwendigkeit haben koennen.
#:
#: Warum eine Namensliste und keine allgemeine Regel: Ob ein Cookie technisch
#: notwendig ist, haengt von der Seite ab — das kann von aussen niemand
#: entscheiden, und ein Warenkorb-Cookie darf vor der Einwilligung gesetzt
#: werden. Diese Namen gehoeren aber zu Messung und Werbung, und dafuer gibt
#: es keine Notwendigkeitsausnahme. Ein Fehlalarm auf `_ga` ist praktisch
#: ausgeschlossen; das ist der Preis dafuer, dass die Aussage haelt.
VERFOLGER = (
    "_ga", "_gid", "_gat", "_gcl_au", "__utm",      # Google Analytics / Ads
    "_fbp", "_fbc", "fr",                            # Meta
    "IDE", "NID", "DSID", "test_cookie",             # DoubleClick
    "_hj",                                            # Hotjar
    "_clck", "_clsk", "MUID",                        # Microsoft Clarity
    "_pk_",                                           # Matomo
    "li_sugr", "bcookie", "lidc",                    # LinkedIn
    "_tt_", "ttwid",                                  # TikTok
    "personalization_id",                             # X/Twitter
)


def verfolger_darunter(cookies) -> list:
    """Welche der gesetzten Cookies eindeutig Messung oder Werbung sind.

    Verglichen wird auf Praefix, nicht auf Gleichheit: Google haengt an `_ga`
    die Grundstuecksnummer (`_ga_XXXXXXX`), Hotjar zaehlt durch (`_hjSession`).
    Wer auf Gleichheit prueft, findet die Haelfte nicht.
    """
    treffer = []
    for cookie in cookies or []:
        name = (cookie or {}).get("name") or ""
        if any(name.startswith(p) for p in VERFOLGER):
            treffer.append(name)
    return sorted(set(treffer))


async def hole_gerendert(url: str) -> dict:
    """Die Seite mit einem echten Browser laden.

    Gibt immer ein Ergebnis zurück, nie eine Ausnahme: Der Aufrufer hat
    bereits HTML aus dem gewöhnlichen Abruf und soll seine Analyse nicht
    verlieren, weil der Browser nicht ansprang.

    Der Schlüssel `wie` sagt, woher das HTML kommt — `browser`, oder `nicht`
    mit einem `grund`. Wer daraus einen Bericht baut, kann damit sagen, was
    er gesehen hat und was nicht.
    """
    global _GEPRUEFT
    _GEPRUEFT = {}

    if not browser_erwuenscht():
        return {"wie": "nicht", "grund": f"{SCHALTER} steht nicht auf true",
                "html": "", "final_url": url}
    if not browser_verfuegbar():
        # Ausdruecklich eine Warnung: Eingeschaltet und nicht installiert ist
        # ein Einrichtungsfehler, kein Normalzustand.
        logger.warning("%s ist gesetzt, aber Playwright fehlt — die "
                       "Erhebung laeuft ohne Browser", SCHALTER)
        return {"wie": "nicht", "grund": "Playwright ist nicht installiert",
                "html": "", "final_url": url}

    # `check_url` **wirft nicht**, es gibt (ok, Grund) zurueck. Ein erster
    # Entwurf stand in einem `try` und haette jede unerlaubte Adresse
    # durchgelassen — eine Sperre, die nie zuschlaegt, sieht aus wie eine.
    try:
        erlaubt, grund = check_url(url)
    except Exception as fehler:     # noqa: BLE001
        return {"wie": "nicht", "grund": f"{type(fehler).__name__}: {fehler}",
                "html": "", "final_url": url}
    if not erlaubt:
        return {"wie": "nicht", "grund": f"Adresse nicht erlaubt: {grund}",
                "html": "", "final_url": url}

    try:
        async with _EINER:
            return await _laden(url)
    except Exception as fehler:     # noqa: BLE001
        logger.warning("Browserlauf fuer %s fehlgeschlagen: %s", url, fehler)
        return {"wie": "nicht", "grund": f"{type(fehler).__name__}: {fehler}",
                "html": "", "final_url": url}


async def _laden(url: str) -> dict:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        try:
            kontext = await browser.new_context(
                user_agent=_kennung(), ignore_https_errors=False,
            )
            seite = await kontext.new_page()

            # **Die zweite Sperre.** Jede Anfrage einzeln — sonst holt der
            # Browser ueber eine Weiterleitung oder ein eingebettetes Bild
            # etwas aus dem internen Netz, und `fetch_guarded` sieht davon
            # nichts.
            async def torwaechter(route):
                if _ziel_ist_oeffentlich(route.request.url):
                    await route.continue_()
                else:
                    logger.info("Browser: %s abgewiesen (nicht oeffentlich)",
                                route.request.url[:120])
                    await route.abort()

            await seite.route("**/*", torwaechter)

            antwort = await seite.goto(url, timeout=AUFBAU_MS,
                                       wait_until="load")
            await seite.wait_for_timeout(RUHEFRIST_MS)
            html = await _inhalt(seite)

            # **Cookies, bevor irgendjemand eingewilligt hat.** Hier wird
            # nichts angeklickt — kein Banner, kein „Alle akzeptieren". Was
            # jetzt gesetzt ist, ist ohne Einwilligung gesetzt worden. Genau
            # das verlangt `cookies_ohne_consent`, und genau das konnte die
            # HTML-Erhebung nie sehen: Sie erkennt ein Consent-Werkzeug an
            # seiner Signatur, nicht sein Verhalten.
            cookies = await kontext.cookies()

            # **Barrierefreiheit am gerenderten Dokument (L-153).** Kontrast,
            # Schriftgroesse und Tastatur sind hier messbar; ohne diesen Lauf
            # haengen sie an Lighthouse und fallen mit PageSpeed aus. Die
            # Seite ist offen, der Aufruf kostet einen Rundlauf.
            a11y = await a11y_browser.messe(seite)

            return {
                "wie": "browser",
                "html": html,
                "a11y": a11y,
                "final_url": seite.url or url,
                "status_code": antwort.status if antwort else 0,
                "cookies": [{"name": c.get("name", ""),
                             "domain": c.get("domain", "")}
                            for c in (cookies or [])],
            }
        finally:
            await browser.close()


async def _inhalt(seite) -> str:
    """Das HTML holen, auch wenn die Seite gerade noch umzieht.

    **Am Gegenstand gefunden (26.08.2026).** Bei `stackoverflow.com` brach
    der ganze Lauf mit „Unable to retrieve content because the page is
    navigating and changing the content" ab — eine Seite, die sich nach dem
    Laden noch einmal weiterleitet. Verloren war damit nicht nur das HTML,
    sondern auch die Cookie-Messung, die am selben Lauf haengt.

    Ein zweiter Versuch nach kurzer Ruhe genuegt: Der Umzug ist dann durch.
    Scheitert auch der, gibt es lieber nichts als eine halbe Seite — der
    Aufrufer hat das HTML aus dem gewoehnlichen Abruf.
    """
    try:
        return await seite.content()
    except Exception as fehler:      # noqa: BLE001
        logger.info("Seiteninhalt beim ersten Versuch nicht lesbar (%s) — "
                    "noch einmal nach %d ms", fehler, RUHEFRIST_MS)
        await seite.wait_for_timeout(RUHEFRIST_MS)
        return await seite.content()


def _kennung() -> str:
    """Dieselbe Kennung wie der gewoehnliche Abruf.

    Zwei verschiedene haetten geheissen, dass zwei Messungen derselben Seite
    nicht vergleichbar sind — manche Server liefern je nach Kennung anderes
    aus.
    """
    from services.audit_runner import USER_AGENT
    return USER_AGENT
