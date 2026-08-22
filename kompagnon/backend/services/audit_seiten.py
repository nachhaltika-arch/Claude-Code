"""Welche Seiten einer Website das Audit prueft.

**Warum es das gibt.** Bis zum 21.08.2026 lud `audit_runner` genau eine Seite —
die Startseite — und leitete daraus jede DOM-Pruefung ab. Was dabei nie
gemessen wurde, ist genau das, was auf Handwerkerseiten typischerweise nicht
auf der Startseite steht: das **Kontaktformular** (liegt auf `/kontakt`), die
**Leistungsseiten** (waren nur als Navigationslinks zaehlbar, nicht als
Seiten), **Zertifikate und Referenzen** (eigene Unterseiten), und **Tracker,
die erst auf der Kontaktseite laden**. Ein Betrieb mit tadelloser Startseite
und einem Formular ohne Einwilligungshaken bekam die volle Punktzahl.

**Zwei Wege, in dieser Reihenfolge.**

1. `sitemap.xml` — die Auskunft des Betreibers selbst, ein Abruf, vollstaendig.
   Gesucht wird sie dort, wo `robots.txt` sie nennt, und sonst unter
   `/sitemap.xml`. Ein Sitemap-Index wird eine Ebene tief aufgeloest.
2. Sonst die **interne Verlinkung der Startseite**. Das findet weniger, aber es
   findet das, was ein Besucher auch findet.

**Warum nach Pfadtiefe sortiert wird.** Eine Sitemap mit 4.000 Beitraegen darf
das Audit nicht sprengen, und die ersten 25 Eintraege einer Sitemap sind
willkuerlich. Kurze Pfade zuerst heisst: `/kontakt` und `/leistungen` vor
`/blog/2019/03/altes-thema`. Das ist die Reihenfolge, in der auch ein Kunde die
Seite beurteilt.
"""
import logging
import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse

from services.url_guard import fetch_guarded, is_same_host

logger = logging.getLogger(__name__)

#: Wie viele Seiten hoechstens geprueft werden — die Startseite eingerechnet.
MAX_SEITEN = 25

#: Zeitgrenze fuer einen einzelnen Abruf waehrend der Suche.
SUCH_TIMEOUT = 8.0

#: Endungen, hinter denen keine HTML-Seite steht. Ein PDF im Audit zu zaehlen
#: hiesse, seine fehlenden Alt-Texte dem Betrieb anzulasten.
KEINE_SEITE = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".ico",
    ".zip", ".rar", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp3", ".mp4", ".avi", ".mov", ".css", ".js", ".json", ".xml", ".rss",
)

#: Pfade, die zwar HTML liefern, aber keine Inhaltsseite sind.
KEIN_INHALT = ("/wp-admin", "/wp-login", "/wp-json", "/feed", "/cart", "/checkout",
               "/warenkorb", "/kasse", "/login", "/logout", "/admin")

_LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.IGNORECASE)
_SITEMAPINDEX = re.compile(r"<sitemapindex", re.IGNORECASE)
_ROBOTS_SITEMAP = re.compile(r"^\s*sitemap:\s*(\S+)", re.IGNORECASE | re.MULTILINE)
_HREF = re.compile(r"""href\s*=\s*["']([^"'>]+)""", re.IGNORECASE)


def normalisiere(url: str) -> str:
    """Eine Adresse ohne Fragment und ohne Schlussstrich.

    `/kontakt`, `/kontakt/` und `/kontakt#formular` sind dieselbe Seite. Ohne
    diese Zusammenfassung prueft das Audit sie dreimal und zaehlt ihre Bilder
    dreifach.
    """
    teile = urlparse(url)
    pfad = teile.path.rstrip("/") or "/"
    return teile._replace(path=pfad, fragment="", params="").geturl()


def ist_seite(url: str) -> bool:
    """Steht hinter der Adresse vermutlich eine Inhaltsseite?"""
    pfad = urlparse(url).path.lower()
    if pfad.endswith(KEINE_SEITE):
        return False
    return not any(pfad.startswith(p) or pfad == p.rstrip("/") for p in KEIN_INHALT)


def _tiefe(url: str) -> tuple:
    """Sortierschluessel: erst flache Pfade, dann kurze, dann alphabetisch."""
    pfad = urlparse(url).path.strip("/")
    return (pfad.count("/") if pfad else -1, len(pfad), pfad)


def _aufraeumen(basis: str, kandidaten, max_seiten: int) -> List[str]:
    """Gleiche Domain, echte Seiten, ohne Doppelte, nach Tiefe sortiert.

    Die Startseite steht immer vorn und zaehlt gegen die Obergrenze — sonst
    meldet das Audit „26 Seiten geprueft" bei einer Grenze von 25.
    """
    startseite = normalisiere(basis)
    gesehen = {startseite}
    uebrig = []

    for roh in kandidaten:
        if not roh:
            continue
        voll = normalisiere(urljoin(basis, roh.strip()))
        if voll in gesehen or not voll.startswith(("http://", "https://")):
            continue
        if not is_same_host(voll, basis) or not ist_seite(voll):
            continue
        gesehen.add(voll)
        uebrig.append(voll)

    uebrig.sort(key=_tiefe)
    return [startseite] + uebrig[: max_seiten - 1]


async def _hole(client, url: str) -> Optional[str]:
    """Ein Abruf, der nie wirft. Die Suche darf das Audit nicht beenden."""
    try:
        antwort = await fetch_guarded(client, url, timeout=SUCH_TIMEOUT,
                                      follow_redirects=True)
        if antwort.status_code >= 400:
            return None
        return antwort.text
    except Exception as fehler:  # noqa: BLE001
        logger.debug("Seitensuche: %s nicht abrufbar (%s)", url, fehler)
        return None


async def _sitemap_adressen(client, basis: str) -> List[str]:
    """Die Adressen aus `sitemap.xml`, sofern es eine gibt.

    Ein Sitemap-Index wird **eine** Ebene tief aufgeloest. Tiefer zu gehen
    hiesse, fuer eine Handvoll zusaetzlicher Adressen beliebig viele Abrufe zu
    machen — und die ersten paar Untersitemaps liefern ohnehin mehr Adressen,
    als das Audit prueft.
    """
    herkunft = urlparse(basis)
    orte = []

    robots = await _hole(client, f"{herkunft.scheme}://{herkunft.netloc}/robots.txt")
    if robots:
        orte.extend(_ROBOTS_SITEMAP.findall(robots)[:3])
    orte.append(f"{herkunft.scheme}://{herkunft.netloc}/sitemap.xml")

    adressen: List[str] = []
    for ort in dict.fromkeys(orte):
        roh = await _hole(client, ort)
        if not roh:
            continue
        gefunden = _LOC.findall(roh)
        if _SITEMAPINDEX.search(roh):
            for untersitemap in gefunden[:5]:
                unter = await _hole(client, untersitemap)
                if unter:
                    adressen.extend(_LOC.findall(unter))
        else:
            adressen.extend(gefunden)
        if adressen:
            break

    return adressen


def adressen_aus_html(basis: str, html: str) -> List[str]:
    """Alle internen Links eines Dokuments — der Rueckfallweg."""
    return _HREF.findall(html or "")


async def finde_unterseiten(client, basis: str, startseiten_html: str,
                            max_seiten: int = MAX_SEITEN) -> dict:
    """Die Seiten, die das Audit pruefen soll — Startseite zuerst.

    Gibt neben der Liste auch **Herkunft und Zahlen** zurueck. Das ist kein
    Beiwerk: Ein Audit ueber 25 von 400 Seiten sagt etwas anderes als eines
    ueber alle 8, und wer den Bericht liest, muss den Unterschied sehen
    koennen.
    """
    adressen = await _sitemap_adressen(client, basis)
    quelle = "sitemap.xml"

    if not adressen:
        adressen = adressen_aus_html(basis, startseiten_html)
        quelle = "interne Verlinkung"

    seiten = _aufraeumen(basis, adressen, max_seiten)
    gefunden = len(_aufraeumen(basis, adressen, 10**6))

    return {
        "collected": True,
        "quelle": quelle,
        "seiten": seiten,
        "geprueft": len(seiten),
        "gefunden": gefunden,
        "gekappt": gefunden > len(seiten),
    }
