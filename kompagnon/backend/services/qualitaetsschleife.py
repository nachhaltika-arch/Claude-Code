"""
Die Qualitätsschleife: der eigene Katalog gegen die selbst gebaute Seite.

Schritt 8 des Design-Konzepts. Der Weg war seit dem 13.08.2026 geklärt und
die Teile lagen bereit — erst auf eine Vorschau deployen, dann den Audit
gegen diese Adresse laufen lassen. Was wir Kunden vorwerfen, dürfen wir
selbst nicht liefern.

Der Audit ist adressgetrieben: Er braucht eine öffentlich erreichbare Seite.
Eine Vorschau bei Netlify ist genau das, und der Deploy dorthin existiert
bereits (`netlify_service.deploy_html`).

**Der gefährliche Teil ist das Ziel des Deploys.** Eine Vorschau, die auf der
Site des Kunden landet, überschreibt dessen Live-Auftritt. Deshalb kennt
dieses Modul genau eine Adresse — die aus ``NETLIFY_VORSCHAU_SITE_ID`` —, und
ohne sie deployt es nichts. Die Site-ID des Kunden wird hier nirgends gelesen.
"""
import logging
import os

import anyio
import httpx

from services.netlify_service import deploy_html

logger = logging.getLogger(__name__)

VORSCHAU_SITE_ENV = "NETLIFY_VORSCHAU_SITE_ID"

#: Wie lange auf die Veroeffentlichung der Vorschau gewartet wird, und in
#: welchem Abstand nachgesehen wird.
BEREIT_FRIST_SEKUNDEN = 30.0
BEREIT_ABSTAND_SEKUNDEN = 1.5

# Eine Vorschau der Kundenseite gehört nicht in den Suchindex: Sie stünde dort
# als Doppel des späteren Auftritts und würde ihm Sichtbarkeit nehmen.
NOINDEX = '<meta name="robots" content="noindex, nofollow">'


class NichtsZuPruefen(Exception):
    """Die Seite hat keinen Inhalt — Deploy und Audit wären sinnlos."""


class KeineVorschauSite(Exception):
    """Ohne eigene Vorschau-Site wird nicht deployt."""


class VorschauKamNicht(Exception):
    """Die Vorschau war auch nach der Frist nicht abrufbar."""


def seiten_inhalt(seite) -> tuple:
    """Markup und Stil der Seite — der Editorstand hat Vorrang vor dem Entwurf.

    ``gjs_html`` ist das, was zuletzt im Editor stand und was der Kunde später
    bekommt. ``mockup_html`` ist der Entwurf davor. Geprüft wird, was
    ausgeliefert würde.
    """
    html = (getattr(seite, "gjs_html", "") or "").strip()
    css = (getattr(seite, "gjs_css", "") or "").strip()

    if not html:
        html = (getattr(seite, "mockup_html", "") or "").strip()
        css = ""

    if not html:
        raise NichtsZuPruefen(
            "Diese Seite hat weder einen Editorstand noch einen Entwurf.")
    return html, css


def vorschau_site_id() -> str:
    site_id = os.getenv(VORSCHAU_SITE_ENV, "").strip()
    if not site_id:
        raise KeineVorschauSite(
            f"{VORSCHAU_SITE_ENV} ist nicht gesetzt. Ohne eigene Vorschau-Site "
            "wird nicht deployt — ein Deploy auf die Site des Kunden würde "
            "dessen Auftritt überschreiben."
        )
    return site_id


async def deploye_vorschau(seite, firmenname: str = "") -> str:
    """Deployt die Seite auf die Vorschau-Site und gibt deren Adresse zurück."""
    html, css = seiten_inhalt(seite)
    site_id = vorschau_site_id()

    ergebnis = await deploy_html(
        site_id=site_id,
        html=NOINDEX + html,
        css=css,
        page_title=getattr(seite, "page_name", "") or "Seite",
        meta_description=getattr(seite, "ki_meta_description", "") or "",
        company_name=firmenname,
    )

    url = ergebnis.get("deploy_url") or ""
    if not url:
        raise RuntimeError("Netlify hat keine Adresse für die Vorschau geliefert.")

    await warte_bis_abrufbar(url)

    logger.info(f"Qualitätsschleife: Seite {getattr(seite, 'id', '?')} "
                f"liegt zur Prüfung unter {url}")
    return url


async def warte_bis_abrufbar(url: str) -> None:
    """Wartet, bis die Vorschau wirklich ausgeliefert wird.

    **Der Befund (27.08.2026, erster gelungener Durchstich).** Nachdem der
    Netlify-Token endlich trug, lief der Deploy — und der Audit scheiterte
    trotzdem. Im Protokoll liegen die beiden Zeilen **dreihundert
    Millisekunden** auseinander:

        20:28:39.386  POST …/sites/…/deploys            → 200 OK
        20:28:39.692  GET  …--kompagnon-vorschau-…      → 500
        20:28:41      Audit 92 fehlgeschlagen: Website nicht erreichbar

    `deploy_html` gibt die Adresse zurueck, sobald Netlify den Deploy
    **angenommen** hat — nicht, wenn er ausgeliefert wird. Ein `curl` zwei
    Minuten spaeter bekam 200: Die Seite war in Ordnung, der Audit hat zu
    frueh hingesehen.

    **Warum das schlimmer ist als ein Fehler, der immer auftritt.** Der
    Ausgang haengt an der Tagesform von Netlify. Mal ist die Vorschau in
    einer Sekunde da, mal in fuenf — und der Bericht sagte dann „Website
    nicht erreichbar", also einen **Befund ueber die Seite**, wo in
    Wirklichkeit unser eigener Ablauf zu schnell war. Ein Kunde haette
    gelesen, seine Seite sei kaputt.

    **Gewartet wird auf die Adresse, nicht auf Netlifys Zustandsfeld.**
    `GET /deploys/{id}` wuerde melden, was Netlify ueber sich denkt; hier
    zaehlt aber genau das, was der Audit gleich tut — die Seite abrufen.
    Am Gegenstand messen statt am Werkzeug ablesen.
    """
    frist = BEREIT_FRIST_SEKUNDEN
    letzter = "kein Versuch"
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        while frist > 0:
            try:
                antwort = await client.get(url)
                if antwort.is_success:
                    return
                letzter = f"Status {antwort.status_code}"
            except Exception as fehler:            # noqa: BLE001
                letzter = f"{type(fehler).__name__}: {fehler}"
            await anyio.sleep(BEREIT_ABSTAND_SEKUNDEN)
            frist -= BEREIT_ABSTAND_SEKUNDEN

    raise VorschauKamNicht(
        f"Die Vorschau war nach {BEREIT_FRIST_SEKUNDEN:.0f} Sekunden nicht "
        f"abrufbar ({letzter}). Der Deploy lief, die Auslieferung nicht.")
