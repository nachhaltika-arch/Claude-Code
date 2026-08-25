# -*- coding: utf-8 -*-
"""Ist wirklich angekommen, was ausgeliefert wurde? (GEO-01, Position 6)

**Warum es diesen Prüfer gibt.** Das Produktdatenblatt verspricht eine
„automatisierte Verifikation der Auslieferung nach Veröffentlichung". Der
Einbau in den Deploy steht seit L-99 — `llms.txt` und die
`schema.org`-Auszeichnung gehen mit derselben Auslieferung hoch wie die
Seiten. **Nachgesehen hat danach niemand.**

Das ist genau die Stelle, an der dieses Projekt wiederholt danebengelegen hat:
Der Deploy meldet „erfolgreich", und ob die Datei danach unter ihrer Adresse
steht, hat das eine mit dem anderen nicht zu tun. Ein Umschreiberegel, ein
Zwischenspeicher, eine Weiterleitung — es gibt genug Wege, auf denen eine
hochgeladene Datei unerreichbar bleibt.

**Geprüft wird am lebenden Dienst**, nicht am Deploy-Protokoll: Die Adresse
wird abgerufen, wie ein KI-Crawler sie abrufen würde.

**Ein Fehlschlag ist kein Fehler des Betriebs.** Er sagt, dass unsere
Auslieferung nicht angekommen ist — und gehört deshalb in den Innendienst,
nicht in den Kundenbericht.
"""
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

ZEITGRENZE = 15.0

#: Wie ein KI-Crawler sich meldet. Wer `llms.txt` liest, ist keine Person.
KENNUNG = "KOMPAGNON-Auslieferungspruefung/1.0 (+https://kompagnon.group)"

#: Woran eine ausgelieferte `llms.txt` erkennbar ist. Eine 200er-Antwort
#: allein genügt nicht: Viele Hosts liefern die Startseite für jede unbekannte
#: Adresse aus — dann steht dort HTML und die Prüfung wäre falsch grün.
LLMS_MERKMAL = re.compile(r"^\s*#\s|^\s*>\s|\bllms\b", re.I | re.M)


async def _hole(client: httpx.AsyncClient, url: str) -> Optional[httpx.Response]:
    try:
        return await client.get(url, headers={"User-Agent": KENNUNG},
                                follow_redirects=True)
    except Exception as fehler:  # noqa: BLE001
        logger.info("Auslieferungspruefung: %s nicht abrufbar (%s)", url, fehler)
        return None


def _ist_echte_llms_txt(antwort: httpx.Response) -> bool:
    """Steht dort eine `llms.txt` — oder die Startseite unter falschem Namen?"""
    if antwort.status_code != 200:
        return False
    text = antwort.text or ""
    if "<html" in text[:400].lower():
        return False
    return bool(text.strip()) and bool(LLMS_MERKMAL.search(text))


async def pruefe_auslieferung(basis_url: str) -> dict:
    """Prüft die drei Artefakte an der veröffentlichten Adresse.

    Liefert je Artefakt `True`, `False` oder `None` — und `None` heißt
    **nicht geprüft**, nicht „fehlt". Wenn die Seite selbst nicht antwortet,
    ist über die Dateien darauf nichts bekannt, und eine Fehlanzeige wäre eine
    Behauptung.
    """
    basis = (basis_url or "").strip().rstrip("/")
    if not basis:
        return {"collected": False, "grund": "keine Adresse hinterlegt"}
    if not basis.startswith("http"):
        basis = "https://" + basis

    befund = {"collected": True, "basis": basis, "llms_txt": None,
              "jsonld": None, "robots_txt": None}

    async with httpx.AsyncClient(timeout=ZEITGRENZE) as client:
        startseite = await _hole(client, basis)
        if startseite is None or startseite.status_code >= 400:
            return {"collected": False, "basis": basis,
                    "grund": "die Seite selbst antwortet nicht — über die "
                             "Dateien darauf ist nichts bekannt"}

        # Die Auszeichnung steht im ausgelieferten HTML der Startseite.
        html = startseite.text or ""
        befund["jsonld"] = ('application/ld+json' in html
                            and 'schema.org' in html)

        antwort = await _hole(client, f"{basis}/llms.txt")
        befund["llms_txt"] = bool(antwort) and _ist_echte_llms_txt(antwort)

        robots = await _hole(client, f"{basis}/robots.txt")
        befund["robots_txt"] = bool(robots) and robots.status_code == 200

    befund["vollstaendig"] = all(befund[k] for k in ("llms_txt", "jsonld"))
    return befund


def klartext(befund: dict) -> str:
    """Ein Satz für den Innendienst — was fehlt, nicht was gut ist."""
    if not befund.get("collected"):
        return f"Nicht geprüft: {befund.get('grund', 'unbekannt')}"
    if befund.get("vollstaendig"):
        return "Ausgeliefert und erreichbar: llms.txt und strukturierte Daten"
    fehlt = [name for name, schluessel in (("llms.txt", "llms_txt"),
                                           ("strukturierte Daten", "jsonld"))
             if not befund.get(schluessel)]
    return "Nicht angekommen: " + ", ".join(fehlt)
