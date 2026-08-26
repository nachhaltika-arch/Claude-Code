"""
Faktenerhebung für das Website-Audit.

Prüft die **ganze Website**, nicht nur die Startseite: `audit_seiten` sucht die
Unterseiten, jede wird einzeln erhoben, und `audit_aggregat` fasst die Befunde
zu je einem Wert pro Kriterium zusammen. Netzwerkabhängige Erhebungen laufen
parallel; jede darf einzeln scheitern, ohne das Audit zu stoppen — das
betroffene Kriterium wird dann als 'nicht erhoben' geführt.

**Bis zum 21.08.2026 war es genau eine Seite.** Was dadurch nie gemessen wurde,
steht auf Handwerkerseiten typischerweise nicht auf der Startseite: das
Kontaktformular auf `/kontakt`, die Leistungsseiten als eigene Seiten,
Zertifikate und Referenzen, und Tracker, die erst auf der Kontaktseite laden.
Ein Betrieb mit tadelloser Startseite und einem Formular ohne
Einwilligungshaken bekam die volle Punktzahl.

**Die Bewertung blieb unberührt.** `audit_aggregat` liefert dieselben
Faktenschlüssel in derselben Form wie zuvor — nur über alle Seiten statt über
eine. Was sich ändert, ist die Grundlage, nicht die Rechnung. Dass sich
dadurch Punktzahlen verschieben, ist der Zweck der Änderung; damit niemand
zwei unvergleichbare Zahlen vergleicht, führt jedes Ergebnis mit, **wie
viele** Seiten geprüft wurden.

Bindet die bereits vorhandenen Dienste ein, die im Altcode ungenutzt herumlagen:
qa_scanner (~45 echte Checks), hosting_scraper und link_checker.
"""
import asyncio
import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from services import audit_aggregat, seitenbrowser, audit_collectors as collectors
from services.audit_pagespeed import fetch_pagespeed
from services.audit_seiten import MAX_SEITEN, finde_unterseiten
from services.url_guard import UnsafeUrlError, fetch_guarded

logger = logging.getLogger(__name__)

HOMEPAGE_TIMEOUT = 15.0
COLLECTION_TIMEOUT = 200.0  # Faktenerhebung; die KI-Bewertung läuft danach

# Eigene Zeitgrenze für die Unterseiten. Reißt sie, bewertet das Audit die
# Startseite allein statt gar nichts — und sagt es im Ergebnis.
UNTERSEITEN_TIMEOUT = 120.0
UNTERSEITEN_GLEICHZEITIG = 5
UNTERSEITEN_TIMEOUT_JE_SEITE = 10.0

# Wie viel Seitentext die KI-Bewertung zu sehen bekommt. Vorher waren es 6.000
# Zeichen der Startseite; jetzt derselbe Umfang, aber über die Seiten verteilt,
# damit die Einschätzung nicht weiter allein auf der Startseite fußt.
TEXT_GESAMT = 12000
TEXT_JE_SEITE = 2500

# Verbindungsversuche für die Startseite. Ein einzelner Fehlversuch beendet
# sonst das ganze Audit — der Besucher liest „Audit fehlgeschlagen“, obwohl
# seine Seite in Ordnung ist.
HOMEPAGE_ATTEMPTS = 3
HOMEPAGE_RETRY_DELAY = 1.5

USER_AGENT = collectors.USER_AGENT

SHOP_LEGAL_MARKERS = {
    "agb": ("agb", "allgemeine geschäftsbedingungen"),
    "widerruf": ("widerruf", "widerrufsbelehrung", "widerrufsrecht"),
    "versand": ("versandkosten", "lieferzeit", "versand und"),
}


async def fetch_homepage(url: str) -> dict:
    """Lädt die Startseite mit aktiver Zertifikatsprüfung.

    Der Altcode nutzte ``verify=False`` — damit blieben ungültige Zertifikate
    unsichtbar und wurden trotzdem mit der vollen SSL-Punktzahl belohnt. Die
    Prüfung bleibt deshalb an.

    Ein Verbindungsfehler wird jedoch wiederholt: beobachtet wurde, dass
    dieselbe Adresse mal einwandfrei antwortet und mal ein selbstsigniertes
    Zertifikat liefert — Server, deren Vhost nur für einen Teil ihrer
    IP-Adressen (v4/v6) ein passendes Zertifikat führt, verhalten sich je
    nach gewählter Adresse unterschiedlich. Ein einzelner Fehlversuch darf
    das Audit nicht beenden.
    """
    letzter_fehler = None

    for versuch in range(HOMEPAGE_ATTEMPTS):
        try:
            async with httpx.AsyncClient(timeout=HOMEPAGE_TIMEOUT, verify=True) as client:
                # Jede Weiterleitung einzeln geprüft — sonst wäre nur der erste
                # Hop kontrolliert und ein Redirect ins interne Netz käme durch.
                r = await fetch_guarded(client, url, headers={"User-Agent": USER_AGENT})
            return {
                "collected": True,
                "reachable": r.status_code < 400,
                "status_code": r.status_code,
                "html": r.text,
                "headers": dict(r.headers),
                "final_url": str(r.url),
            }
        except UnsafeUrlError as e:
            # Kein Netzproblem, sondern eine bewusst abgelehnte Adresse —
            # ein weiterer Versuch änderte daran nichts.
            return {"collected": True, "reachable": False, "status_code": 0,
                    "html": "", "headers": {}, "error": f"Adresse nicht erlaubt: {e}"[:200]}
        except httpx.ConnectError as e:
            letzter_fehler = f"Verbindung fehlgeschlagen: {e}"
        except Exception as e:  # noqa: BLE001
            letzter_fehler = f"{type(e).__name__}: {e}"

        if versuch + 1 < HOMEPAGE_ATTEMPTS:
            logger.warning(
                f"Startseite {url}: Versuch {versuch + 1} von {HOMEPAGE_ATTEMPTS} "
                f"fehlgeschlagen ({letzter_fehler}) — neuer Versuch")
            await asyncio.sleep(HOMEPAGE_RETRY_DELAY)

    logger.warning(f"Startseite {url} nach {HOMEPAGE_ATTEMPTS} Versuchen nicht erreichbar: "
                   f"{letzter_fehler}")
    return {"collected": True, "reachable": False, "status_code": 0,
            "html": "", "headers": {}, "error": (letzter_fehler or "unbekannt")[:200]}


def _security_headers(headers: dict) -> dict:
    lower = {k.lower(): v for k, v in headers.items()}
    return {
        "collected": True,
        "hsts": "strict-transport-security" in lower,
        "csp": "content-security-policy" in lower,
        "xframe": "x-frame-options" in lower,
        "xcontent": "x-content-type-options" in lower,
    }


def _shop_legal_markers(html: str) -> dict:
    lower = html.lower()
    return {name: any(k in lower for k in keys) for name, keys in SHOP_LEGAL_MARKERS.items()}


async def _safe(coro, label: str):
    """Führt eine Erhebung aus und schluckt nur deren eigenen Fehler."""
    try:
        return await coro
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Erhebung '{label}' fehlgeschlagen: {type(e).__name__}: {e}")
        return {"collected": False, "reason": f"{type(e).__name__}: {e}"[:200]}


async def _run_qa_scanner(url: str, company: str, trade: str) -> dict:
    from services.qa_scanner import run_full_qa

    scan = await run_full_qa(url, company, trade)
    return scan.get("checks", {}) or {}


async def _run_hosting(url: str) -> dict:
    from services.hosting_scraper import scrape_hosting_info

    return await scrape_hosting_info(url)


async def _run_link_check(url: str) -> dict:
    from services.link_checker import LinkChecker

    return await asyncio.to_thread(LinkChecker.check_links, url)


async def _seitenfakten(url: str, html: str, current_year: int) -> dict:
    """Alle DOM-Befunde **einer** Seite.

    Genau die Erhebungen, die an einem einzelnen Dokument haengen. Was die
    Domain als Ganzes betrifft — Zertifikat, Weiterleitung, Hosting,
    Sicherheits-Header, PageSpeed —, gehoert nicht hierher: Es waere auf jeder
    Seite dasselbe Ergebnis zu einem Vielfachen der Abrufe.
    """
    soup = BeautifulSoup(html, "html.parser")
    bilder = await _safe(collectors.analyse_images(soup, url), f"bilder {url}")

    return {
        "url": url,
        "consent": collectors.detect_consent(html),
        "third_parties": collectors.detect_third_parties(html),
        "forms": collectors.analyse_forms(soup, url),
        "contact": collectors.analyse_contact(soup),
        "cta": collectors.analyse_cta(soup),
        "trust": collectors.analyse_trust(soup),
        "services": collectors.analyse_service_pages(soup, url),
        "freshness": collectors.analyse_freshness(html, current_year),
        "shop": collectors.detect_shop(html),
        "shop_legal_markers": _shop_legal_markers(html),
        "images": bilder if isinstance(bilder, dict) else {"collected": False},
        "word_count": len(soup.get_text(" ").split()),
        "page_text": soup.get_text(" ", strip=True)[:TEXT_JE_SEITE],
    }


async def _hole_und_erhebe(client, sperre, url: str, current_year: int):
    """Eine Unterseite abrufen und erheben — oder ``None``, wenn das scheitert.

    Eine Seite, die nicht antwortet, wird uebergangen statt als leer gewertet:
    Sonst zoege ein 500er auf `/blog` die Bilder- und Wortzahl der ganzen
    Website nach unten, und der Betrieb bekaeme fuer einen Serverfehler eine
    schlechtere Note in Kriterien, die damit nichts zu tun haben.
    """
    async with sperre:
        try:
            antwort = await fetch_guarded(client, url,
                                          timeout=UNTERSEITEN_TIMEOUT_JE_SEITE,
                                          follow_redirects=True)
            if antwort.status_code >= 400:
                return None
            if not antwort.headers.get("content-type", "").lower().startswith("text/html"):
                return None
            return await _seitenfakten(url, antwort.text, current_year)
        except Exception as fehler:  # noqa: BLE001
            logger.debug("Unterseite %s nicht erhoben: %s", url, fehler)
            return None


async def _alle_seiten(base_url: str, startseiten_html: str,
                       current_year: int, max_seiten: int) -> tuple:
    """Die Befunde aller Seiten und der Bericht darueber, welche das waren.

    Gibt `(befunde, seiten_block)` zurueck. Der zweite Teil ist kein Beiwerk:
    Ein Audit ueber 25 von 400 Seiten sagt etwas anderes als eines ueber alle
    acht, und ein Ergebnis, dem man die Grundlage nicht ansieht, laedt dazu
    ein, es mit einem aelteren zu vergleichen, das nur die Startseite kannte.
    """
    startseite = await _seitenfakten(base_url, startseiten_html, current_year)

    try:
        async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as client:
            gefunden = await finde_unterseiten(client, base_url, startseiten_html,
                                               max_seiten=max_seiten)
            unterseiten = gefunden["seiten"][1:]   # [0] ist die Startseite

            sperre = asyncio.Semaphore(UNTERSEITEN_GLEICHZEITIG)
            ergebnisse = await asyncio.wait_for(
                asyncio.gather(*[
                    _hole_und_erhebe(client, sperre, u, current_year)
                    for u in unterseiten
                ]),
                timeout=UNTERSEITEN_TIMEOUT,
            )
    except asyncio.TimeoutError:
        logger.warning("Unterseiten fuer %s: Zeitgrenze erreicht", base_url)
        return [startseite], {"collected": True, "quelle": "abgebrochen", "geprueft": 1,
                              "gefunden": 1, "gekappt": False, "seiten": [base_url],
                              "hinweis": "Zeitgrenze erreicht — nur die Startseite bewertet"}
    except Exception as fehler:  # noqa: BLE001
        logger.warning("Unterseiten fuer %s nicht gefunden: %s", base_url, fehler)
        return [startseite], {"collected": False, "geprueft": 1, "seiten": [base_url]}

    erhoben = [e for e in ergebnisse if e]
    befunde = [startseite] + erhoben

    return befunde, {
        **gefunden,
        "seiten": [b["url"] for b in befunde],
        "geprueft": len(befunde),
        "nicht_erreichbar": len(unterseiten) - len(erhoben),
    }


def _gesamttext(befunde: list) -> str:
    """Seitentext fuer die KI-Bewertung — ueber die Seiten verteilt, gedeckelt."""
    stuecke = []
    laenge = 0
    for b in befunde:
        text = (b.get("page_text") or "").strip()
        if not text:
            continue
        stuecke.append(f"[{b['url']}]\n{text}")
        laenge += len(text)
        if laenge >= TEXT_GESAMT:
            break
    return "\n\n".join(stuecke)[:TEXT_GESAMT]


async def collect_facts(
    url: str,
    company_name: str = "",
    trade: str = "",
    city: str = "",
    current_year: int = 2026,
    max_seiten: int = MAX_SEITEN,
) -> dict:
    """Erhebt alle Fakten zu einer Website. Wirft nie — meldet Teilausfälle."""
    homepage = await fetch_homepage(url)

    if not homepage.get("reachable"):
        return {
            "url": url,
            "reachable": False,
            "status_code": homepage.get("status_code", 0),
            "error": homepage.get("error", ""),
        }

    html = homepage["html"]
    soup = BeautifulSoup(html, "html.parser")
    base_url = homepage.get("final_url") or url

    # **Entsteht die Seite erst im Browser? Dann noch einmal, mit einem
    # (L-107, Entscheidung David 26.08.2026).** `httpx` fuehrt kein
    # JavaScript aus; von einer React-Anwendung sieht die Erhebung
    # `<div id="root"></div>` und sonst nichts — beim Probelauf gegen die
    # eigene Produktivoberflaeche elf Woerter.
    #
    # **Nur dann.** Ein Browserlauf kostet Sekunden und Speicher; ihn bei
    # jeder Analyse zu starten waere Aufwand fuer die neunundneunzig Seiten,
    # die ihn nicht brauchen. Die Erkennung steht seit dem 25.08. und
    # entscheidet ohnehin schon, ob Kriterien als gemessen gelten duerfen.
    # **Ein Lauf, zwei Erkenntnisse (26.08.2026).** Die erste Fassung startete
    # den Browser nur bei einer leeren Huelle — richtig, solange es allein um
    # L-107 ging. Er sieht aber noch etwas, das sonst niemand sehen kann:
    # welche Cookies **vor** jeder Einwilligung gesetzt werden. Das ist die
    # Deckelregel `cookies_ohne_consent`, die der Katalog seit jeher nennt und
    # die niemand erhoben hat. Zweimal zu laden waere zweimal zu zahlen.
    #
    # Kosten: rund 6 s bei einem Zeitrahmen von 200 s, und hoechstens ein
    # Browser gleichzeitig (`seitenbrowser._EINER`).
    browserlauf = {"wie": "nicht", "grund": "nicht eingeschaltet"}
    if seitenbrowser.browser_erwuenscht():
        browserlauf = await seitenbrowser.hole_gerendert(base_url)
        if browserlauf.get("wie") == "browser" and browserlauf.get("html"):
            html = browserlauf["html"]
            soup = BeautifulSoup(html, "html.parser")
            base_url = browserlauf.get("final_url") or base_url
            logger.info("%s wurde im Browser geladen (%d statt %d Woerter)",
                        base_url, len(soup.get_text(" ").split()),
                        len(BeautifulSoup(homepage["html"], "html.parser")
                            .get_text(" ").split()))

    # Netzwerkabhängige Erhebungen parallel — alle auf Domain-Ebene, deshalb
    # weiter an der Startseite und nicht je Unterseite.
    tasks = {
        "psi_mobile": _safe(fetch_pagespeed(base_url, "mobile"), "pagespeed"),
        "qa": _safe(_run_qa_scanner(base_url, company_name, trade), "qa_scanner"),
        "hosting": _safe(_run_hosting(base_url), "hosting_scraper"),
        "links": _safe(_run_link_check(base_url), "link_checker"),
        "legal": _safe(collectors.check_legal_pages(base_url, soup), "rechtsseiten"),
        "redirect": _safe(collectors.check_https_redirect(base_url), "https_redirect"),
        "tls": _safe(asyncio.to_thread(collectors.check_tls, base_url), "tls"),
        "seitenweise": _safe(
            _alle_seiten(base_url, html, current_year, max_seiten), "unterseiten"
        ),
    }

    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks.values(), return_exceptions=True),
            timeout=COLLECTION_TIMEOUT,
        )
        collected = dict(zip(tasks.keys(), results))
    except asyncio.TimeoutError:
        logger.warning(f"Faktenerhebung für {url}: Gesamt-Timeout erreicht")
        collected = {}

    seitenweise = collected.pop("seitenweise", None)
    if isinstance(seitenweise, tuple):
        befunde, seiten_block = seitenweise
    else:
        # Auch der Rueckfall bewertet noch die Startseite — ohne ihn stuenden
        # alle DOM-Kriterien auf 'nicht erhoben', und das Audit waere leer.
        befunde = [await _seitenfakten(base_url, html, current_year)]
        seiten_block = {"collected": False, "geprueft": 1, "seiten": [base_url]}

    facts = {
        "url": url,
        "final_url": base_url,
        "city": city,
        "company_name": company_name,
        "trade": trade,
        "reachable": True,
        "status_code": homepage.get("status_code"),
        # Über alle geprüften Seiten zusammengefasst (`audit_aggregat`)
        **audit_aggregat.fasse_zusammen(befunde),
        # Nur die Startseite: die Navigation ist auf allen Seiten dieselbe.
        "navigation": collectors.analyse_navigation(soup),
        # Entsteht der Inhalt erst im Browser? Dann hat die Erhebung die Seite
        # nie gesehen, und die inhaltsabhaengigen Kriterien duerfen nicht als
        # gemessen gelten (24.08.2026, `clientseitig_aufgebaut`).
        # Nach einem geglueckten Browserlauf ist die Seite **gesehen** — die
        # inhaltsabhaengigen Kriterien duerfen dann wieder zaehlen. Ohne diese
        # Neubewertung fielen sie weiter aus Zaehler und Nenner, und der
        # Browser haette nichts geaendert ausser der Laufzeit.
        "clientseitig": collectors.clientseitig_aufgebaut(
            soup, len(soup.get_text(" ").split())),
        # Wie die Seite geholt wurde. **Ein Bericht, der das nicht sagen kann,
        # ist die Fehlerfamilie, die diesen Bestand am haeufigsten getroffen
        # hat** — eine Zahl, die aussieht wie eine Messung.
        "browserlauf": {"collected": True,
                        "wie": browserlauf.get("wie", "nicht"),
                        "grund": browserlauf.get("grund", "")},
        # **Erst erhoben, seit es einen Browser gibt.** Ohne Browserlauf
        # steht hier `collected: False` — und die Deckelregel bleibt, was sie
        # war: genannt, aber nicht gemessen. Sie mit `False` zu beantworten
        # hiesse zu behaupten, nachgesehen zu haben.
        "cookies_vor_consent": _cookies_vor_consent(browserlauf),
        "cdn": collectors.detect_cdn(homepage.get("headers", {})),
        "security_headers": _security_headers(homepage.get("headers", {})),
        "page_text": _gesamttext(befunde),
        "seiten": seiten_block,
    }

    for key, value in collected.items():
        facts[key] = value if isinstance(value, dict) else {"collected": False}

    return facts


def _cookies_vor_consent(browserlauf: dict) -> dict:
    """Was ohne Einwilligung gesetzt wurde — oder dass niemand nachgesehen hat.

    Der Browserlauf klickt kein Banner an. Was danach im Kontext steht, steht
    dort ohne Zustimmung. `verfolger` nennt davon die Namen, bei denen es
    **keine** Notwendigkeitsausnahme geben kann — Messung und Werbung. Alles
    andere bleibt ungewertet: Ob ein Cookie technisch notwendig ist, haengt
    von der Seite ab, und das kann von aussen niemand entscheiden.
    """
    if browserlauf.get("wie") != "browser":
        return {"collected": False,
                "grund": browserlauf.get("grund", "kein Browserlauf")}

    cookies = browserlauf.get("cookies") or []
    verfolger = seitenbrowser.verfolger_darunter(cookies)
    return {
        "collected": True,
        "anzahl": len(cookies),
        "verfolger": verfolger,
        "verstoss": bool(verfolger),
    }


def summarise_facts(facts: dict) -> dict:
    """Verdichtet die Rohfakten auf das, was Report und KI-Prompt brauchen."""
    psi = facts.get("psi_mobile") or {}
    tls = facts.get("tls") or {}
    qa = facts.get("qa") or {}
    legal = facts.get("legal") or {}
    links = facts.get("links") or {}
    hosting = facts.get("hosting") or {}
    seiten = facts.get("seiten") or {}

    return {
        # Der Umfang gehoert ins Ergebnis, nicht nur ins Log: Ein Audit ueber
        # 25 von 400 Seiten sagt etwas anderes als eines ueber alle acht — und
        # Ergebnisse von vor dem 21.08.2026 kannten nur die Startseite.
        "seiten_geprueft": seiten.get("geprueft", 1),
        "seiten_gefunden": seiten.get("gefunden"),
        "seiten_gekappt": bool(seiten.get("gekappt")),
        "seiten_quelle": seiten.get("quelle"),
        "lcp_value": psi.get("lcp_seconds"),
        "cls_value": psi.get("cls_value"),
        "inp_value": psi.get("inp_ms"),
        "inp_source": psi.get("inp_source"),
        "performance_score": psi.get("performance_score"),
        "mobile_score": psi.get("performance_score"),
        "accessibility_score": psi.get("accessibility_score"),
        "pagespeed_collected": bool(psi.get("collected")),
        "pagespeed_reason": psi.get("reason"),
        "ssl_ok": bool(tls.get("valid")),
        "ssl_detail": tls.get("reason") or tls.get("issuer") or "",
        "impressum_ok": bool(legal.get("impressum", {}).get("reachable")),
        "impressum_complete": bool(legal.get("impressum", {}).get("complete")),
        "datenschutz_ok": bool(legal.get("datenschutz", {}).get("reachable")),
        "datenschutz_complete": bool(legal.get("datenschutz", {}).get("complete")),
        "broken_links": len(links.get("broken_links", []) or []),
        "hosting_provider": hosting.get("hosting_provider"),
        "detected_technologies": hosting.get("detected_technologies", []),
        "a11y_failures": [f["title"] for f in (psi.get("a11y_failures") or [])][:8],
        # GEO-Prüfpunkte. Sie standen im Bericht, ohne je erhoben zu werden —
        # die Spalten blieben leer, das PDF las die Leere als „nicht erfüllt"
        # und druckte Handlungsaufforderungen. `None` heißt hier unbekannt und
        # ist nicht dasselbe wie `False` („gemessen und nicht vorhanden").
        "llms_txt": qa.get("llms_txt") if qa else None,
        "robots_ai_friendly": qa.get("robots_ai_friendly") if qa else None,
        "structured_data": qa.get("schema_markup") if qa else None,
        "gesperrte_ki_crawler": (qa.get("gesperrte_ki_crawler") or []) if qa else [],
    }


def collection_notes(facts: dict, ai: Optional[dict] = None) -> dict:
    """Warum eine Prüfung ausfiel — damit 'nicht erhoben' begründet erscheint.

    Ohne diese Notiz sieht der Betrachter nur fehlende Punkte und kann nicht
    unterscheiden, ob die Website ein Problem hat oder das Audit eines.
    """
    notes = {}
    for key, label in (
        ("psi_mobile", "pagespeed"),
        ("legal", "rechtsseiten"),
        ("tls", "tls"),
        ("links", "linkpruefung"),
        ("hosting", "hosting"),
    ):
        fact = facts.get(key) or {}
        if fact.get("collected") is False:
            notes[label] = {
                "reason": fact.get("reason", "unbekannt"),
                "detail": str(fact.get("detail", ""))[:200],
            }

    # Steht hinter der Seite kein Betrieb, fallen die angebotsbezogenen
    # Kriterien heraus (siehe audit_scoring._apply_ai). Ohne diese Notiz sieht
    # der Leser nur eine niedrigere Abdeckung und erfährt nicht, warum.
    if ai and ai.get("betriebsseite") is False:
        notes["angebotskriterien"] = {
            "reason": "keine_betriebsseite",
            "detail": str(ai.get("branche") or "")[:200],
        }

    return notes
