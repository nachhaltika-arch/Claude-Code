import re, httpx, asyncio, logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from services.audit_collectors import USER_AGENT
from services.ki_aufruf import frag_modell

logger = logging.getLogger(__name__)

# Dieselbe Kennung wie in den übrigen Erhebungen. Ohne sie fragt httpx unter
# eigenem Namen, und Server mit Bot-Abwehr antworten mit 403 — auf Startseite,
# robots.txt und sitemap.xml gleichermaßen. Das Audit las dann eine Fehlerseite
# und schrieb deren Leere als Messwert fort.
BROWSER_HEADERS = {"User-Agent": USER_AGENT}

# Crawler der KI-Systeme. Ob sie eingelassen werden, entscheidet die robots.txt
# — und nur das ist eine Messung. Der Bericht verlangte bisher pauschal, „die
# GPTBot-Blockierung zu entfernen", auch bei robots.txt, die niemanden sperren.
KI_CRAWLER = ["GPTBot", "ChatGPT-User", "OAI-SearchBot", "ClaudeBot",
              "Claude-Web", "PerplexityBot", "Google-Extended", "CCBot",
              "Applebot-Extended", "Bytespider"]


def gesperrte_ki_crawler(robots_text: str) -> list:
    """Welche KI-Crawler die robots.txt von der ganzen Website aussperrt.

    Gewertet wird nur ``Disallow: /`` — die Sperre der gesamten Seite. Ein
    ausgenommenes Verzeichnis ist Alltag und kein Sichtbarkeitsproblem.
    ``User-agent: *`` mit ``Disallow: /`` trifft alle und wird deshalb jedem
    Crawler zugerechnet.
    """
    if not robots_text:
        return []

    # robots.txt in Bloecke zerlegen: Kennungen sammeln, bis Regeln folgen.
    bloecke, kennungen, regeln, in_regeln = [], [], [], False
    for zeile in robots_text.splitlines():
        zeile = zeile.split("#")[0].strip()
        if not zeile or ":" not in zeile:
            continue
        feld, _, wert = zeile.partition(":")
        feld, wert = feld.strip().lower(), wert.strip()
        if feld == "user-agent":
            if in_regeln:
                bloecke.append((kennungen, regeln))
                kennungen, regeln, in_regeln = [], [], False
            kennungen.append(wert)
        elif feld == "disallow":
            in_regeln = True
            regeln.append(wert)
    if kennungen:
        bloecke.append((kennungen, regeln))

    gesperrt = []
    for kennungen, regeln in bloecke:
        if "/" not in regeln:
            continue
        for kennung in kennungen:
            if kennung == "*":
                gesperrt.extend(KI_CRAWLER)
            else:
                treffer = [c for c in KI_CRAWLER if c.lower() == kennung.lower()]
                gesperrt.extend(treffer)
    return sorted(set(gesperrt))


async def run_full_qa(url: str, company: str = "", trade: str = "") -> dict:
    """
    Führt alle Checks durch und gibt strukturiertes Ergebnis zurück.
    Dauer: ca. 25-40 Sekunden.
    """
    if not url.startswith("http"):
        url = "https://" + url

    results = {}

    # HTML der Startseite laden (einmalig — alle Parser nutzen dasselbe)
    html = ""
    soup = None
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True,
                                     headers=BROWSER_HEADERS) as c:
            r = await c.get(url)
            # Eine abweisende Antwort ist kein Messergebnis. Ohne diese Prüfung
            # zergliedert der Scanner die Fehlerseite, findet erwartungsgemäß
            # weder Canonical noch Schema, und die Bewertung zählt die Nullen
            # als „gemessen" — die Seite verliert Punkte für Mängel, die sie
            # nicht hat. Leere Checks lassen die Bewertung stattdessen
            # überspringen (siehe `_score_seo`: `if not qa`).
            if r.status_code != 200:
                logger.warning(f"QA: {url} antwortete mit HTTP {r.status_code}")
                return {"error": f"HTTP {r.status_code}", "checks": {}}
            html = r.text
            soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        logger.warning(f"QA: Seite nicht ladbar: {e}")
        return {"error": str(e), "checks": {}}

    html_lower = html.lower()

    # ─── KATEGORIE 1: TECHNISCH / SEO ───────────────────────────────

    # SSL
    results["ssl_aktiv"] = url.startswith("https://")

    # HTTPS-Redirect (http → https)
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False,
                                     headers=BROWSER_HEADERS) as c:
            http_url = url.replace("https://", "http://")
            r2 = await c.get(http_url)
            results["https_redirect"] = r2.status_code in (301, 302) and \
                "https" in r2.headers.get("location", "")
    except Exception:
        results["https_redirect"] = False

    # Favicon
    favicon_tag = soup.find("link", rel=lambda r: r and "icon" in str(r).lower())
    results["favicon_vorhanden"] = bool(favicon_tag)

    # robots.txt
    try:
        async with httpx.AsyncClient(timeout=5.0, headers=BROWSER_HEADERS) as c:
            domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            r3 = await c.get(f"{domain}/robots.txt")
            results["robots_txt"] = r3.status_code == 200
            robots_text = r3.text if r3.status_code == 200 else ""
            results["robots_txt_indexiert"] = "noindex" not in robots_text.lower()
            # Keine robots.txt sperrt niemanden — das ist KI-freundlich.
            results["gesperrte_ki_crawler"] = gesperrte_ki_crawler(robots_text)
            results["robots_ai_friendly"] = not results["gesperrte_ki_crawler"]
    except Exception:
        results["robots_txt"] = False
        results["robots_txt_indexiert"] = False

    # sitemap.xml
    try:
        async with httpx.AsyncClient(timeout=5.0, headers=BROWSER_HEADERS) as c:
            domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            r4 = await c.get(f"{domain}/sitemap.xml")
            results["sitemap_xml"] = r4.status_code == 200 and \
                "urlset" in r4.text.lower()
    except Exception:
        results["sitemap_xml"] = False

    # ─── KATEGORIE 2: META & ON-PAGE SEO ────────────────────────────

    # Title Tag
    title_tag = soup.find("title")
    title_text = title_tag.get_text().strip() if title_tag else ""
    results["title_vorhanden"] = bool(title_text)
    results["title_laenge_ok"] = 10 <= len(title_text) <= 65
    results["title_text"] = title_text[:100]

    # Meta Description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc_text = desc_tag.get("content", "").strip() if desc_tag else ""
    results["meta_desc_vorhanden"] = bool(desc_text)
    results["meta_desc_laenge_ok"] = 50 <= len(desc_text) <= 160
    results["meta_desc_text"] = desc_text[:200]

    # H1
    h1_tags = soup.find_all("h1")
    results["h1_anzahl"] = len(h1_tags)
    results["h1_genau_eins"] = len(h1_tags) == 1
    results["h1_text"] = h1_tags[0].get_text().strip()[:100] if h1_tags else ""

    # Heading-Hierarchie (H1 → H2 vorhanden)
    h2_tags = soup.find_all("h2")
    results["h2_vorhanden"] = len(h2_tags) > 0
    results["heading_struktur_ok"] = len(h1_tags) == 1 and len(h2_tags) > 0

    # Canonical
    canonical = soup.find("link", rel="canonical")
    results["canonical_vorhanden"] = bool(canonical)

    # Open Graph
    og_title = soup.find("meta", property="og:title")
    og_desc  = soup.find("meta", property="og:description")
    og_img   = soup.find("meta", property="og:image")
    results["og_tags_vorhanden"] = bool(og_title and og_desc and og_img)

    # Schema Markup (JSON-LD)
    schema_tags = soup.find_all("script", type="application/ld+json")
    results["schema_markup"] = len(schema_tags) > 0
    schema_text = " ".join(t.get_text() for t in schema_tags).lower()
    results["schema_localbusiness"] = "localbusiness" in schema_text
    results["schema_faq"] = "faqpage" in schema_text
    # Die gefundenen @type-Werte einzeln: Welcher Typ der richtige ist, hängt
    # an der Branchenklasse — ein Shop wird nicht an `LocalBusiness` gemessen.
    # Über den Rohtext gelesen und nicht über `json.loads`, weil ein einziges
    # fehlerhaftes Snippet sonst die ganze Erhebung verschluckt.
    results["schema_typen"] = sorted({
        typ.strip().split("/")[-1]
        for typ in re.findall(r'"@type"\s*:\s*"([^"]+)"', schema_text)
        if typ.strip()
    })

    # Viewport (Mobile)
    viewport = soup.find("meta", attrs={"name": "viewport"})
    results["mobile_viewport"] = bool(viewport)

    # ─── KATEGORIE 3: INHALTE & UX ──────────────────────────────────

    # Alt-Texte
    alle_imgs = soup.find_all("img")
    imgs_mit_alt = [i for i in alle_imgs if i.get("alt", "").strip()]
    results["bilder_gesamt"] = len(alle_imgs)
    results["bilder_mit_alt"] = len(imgs_mit_alt)
    results["alt_texte_quote"] = round(
        len(imgs_mit_alt) / len(alle_imgs) * 100 if alle_imgs else 100
    )
    results["alt_texte_ok"] = results["alt_texte_quote"] >= 80

    # Kontaktformular vorhanden
    forms = soup.find_all("form")
    results["kontaktformular"] = len(forms) > 0

    # Telefon als tel:-Link
    tel_links = soup.find_all("a", href=lambda h: h and h.startswith("tel:"))
    results["telefon_link"] = len(tel_links) > 0

    # E-Mail als mailto:-Link
    mail_links = soup.find_all("a", href=lambda h: h and h.startswith("mailto:"))
    results["mailto_link"] = len(mail_links) > 0

    # Google Fonts nicht extern (DSGVO)
    results["google_fonts_extern"] = "fonts.googleapis.com" in html_lower

    # Google Maps eingebettet
    results["google_maps"] = "maps.google" in html_lower or \
                             "maps.googleapis" in html_lower or \
                             "maps.gstatic" in html_lower

    # ─── KATEGORIE 4: RECHTLICHES / DSGVO ───────────────────────────

    results["impressum_link"] = any(
        kw in html_lower for kw in
        ["impressum", "/impressum", "imprint"]
    )
    results["datenschutz_link"] = any(
        kw in html_lower for kw in
        ["datenschutz", "privacy", "/datenschutz", "datenschutzerkl"]
    )
    results["cookie_banner"] = any(
        kw in html_lower for kw in
        ["cookie", "consent", "cookiebot", "onetrust",
         "usercentrics", "borlabs", "gdpr"]
    )

    # Datenschutz-Checkbox in Formular
    inputs = soup.find_all("input", type="checkbox")
    checkbox_labels = " ".join(
        str(i.parent) for i in inputs if i.parent
    ).lower()
    results["dsgvo_checkbox"] = any(
        kw in checkbox_labels for kw in
        ["datenschutz", "privacy", "einverstanden", "akzeptiere"]
    )

    # Barrierefreiheits-Statement
    results["bfsg_hinweis"] = any(
        kw in html_lower for kw in
        ["barrierefrei", "accessibility", "wcag", "erklärung zur barrierefreiheit"]
    )

    # ─── KATEGORIE 5: PERFORMANCE-DATEN ─────────────────────────────
    # PageSpeed wird separat übergeben (existiert schon im audit.py)
    # Hier: Header-Checks

    try:
        async with httpx.AsyncClient(timeout=5.0, headers=BROWSER_HEADERS) as c:
            rh = await c.head(url, follow_redirects=True)
            headers = {k.lower(): v for k, v in rh.headers.items()}
            results["hsts"] = "strict-transport-security" in headers
            results["x_frame_options"] = "x-frame-options" in headers
            results["csp"] = "content-security-policy" in headers
            results["cache_control"] = "cache-control" in headers
            results["content_type_options"] = "x-content-type-options" in headers
    except Exception:
        results.update({"hsts": False, "x_frame_options": False,
                        "csp": False, "cache_control": False,
                        "content_type_options": False})

    # ─── KATEGORIE 6: LLM-OPTIMIERUNG ───────────────────────────────

    # llms.txt — die Konvention heisst mit s, so steht sie auch im Bericht.
    # Frueher wurde nur /llm.txt geprueft; wer die Datei nach der Konvention
    # abgelegt hatte, galt trotzdem als ohne.
    try:
        async with httpx.AsyncClient(timeout=5.0, headers=BROWSER_HEADERS) as c:
            domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            r5 = await c.get(f"{domain}/llms.txt")
            gefunden = r5.status_code == 200
            if not gefunden:
                r5b = await c.get(f"{domain}/llm.txt")
                gefunden = r5b.status_code == 200
            results["llms_txt"] = gefunden
            results["llm_txt"] = gefunden  # alter Name, im KI-Prompt genutzt
    except Exception:
        results["llms_txt"] = False
        results["llm_txt"] = False

    # FAQ-Block (Akkordeon)
    results["faq_block"] = any(
        kw in html_lower for kw in
        ["faq", "häufig", "accordion", "details", "summary"]
    )

    # Footer Timestamp / Aktualisierungsdatum
    results["footer_timestamp"] = any(
        kw in html_lower for kw in
        ["aktualisiert", "zuletzt", "last updated", "stand:"]
    )

    # IndexNow
    results["indexnow"] = "indexnow" in html_lower

    return {
        "url": url,
        "company": company,
        "trade": trade,
        "checks": results,
        "html_snippet": html[:8000],   # für KI-Bewertung
        "title": title_text,
        "meta_desc": desc_text,
        "h1": results.get("h1_text", ""),
    }


async def ai_evaluate_qa(scan: dict) -> dict:
    """
    Schickt alle Scan-Ergebnisse an Claude.
    Claude bewertet 6 Kategorien und gibt Go-Live-Empfehlung.
    """
    import os
    from anthropic import Anthropic
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    checks = scan["checks"]

    prompt = f"""Du bist ein erfahrener Website-Qualitätsauditor.
Analysiere diese automatisch gesammelten Website-Daten und
bewerte 6 Kategorien sowie eine Go-Live-Empfehlung.

WICHTIG: Antworte AUSSCHLIESSLICH mit validem JSON.
- Kein Text vor oder nach dem JSON
- Keine Markdown-Backticks
- Schließe IMMER alle JSON-Objekte und Arrays korrekt ab
- Halte Listen kurz (max 3-5 Einträge pro Array), damit die Antwort vollständig bleibt

WEBSITE: {scan.get("url")}
BETRIEB: {scan.get("company")} | Branche: {scan.get("trade")}
TITLE: {scan.get("title")}
META-DESCRIPTION: {scan.get("meta_desc")}
H1: {scan.get("h1")}

TECHNISCHE CHECKS:
{checks}

HTML-AUSSCHNITT (Startseite):
{scan.get("html_snippet", "")[:2000]}

Bewerte ALLE folgenden Punkte im JSON-Format.
Antworte NUR mit validem JSON:

{{
  "kategorien": {{
    "seo": {{
      "score": 0-100,
      "status": "bestanden|warnung|kritisch",
      "punkte": ["was gut ist"],
      "probleme": ["was fehlt oder schlecht ist"]
    }},
    "performance": {{
      "score": 0-100, "status": "...",
      "punkte": [], "probleme": []
    }},
    "mobile": {{
      "score": 0-100, "status": "...",
      "punkte": [], "probleme": []
    }},
    "dsgvo": {{
      "score": 0-100, "status": "...",
      "punkte": [], "probleme": []
    }},
    "content": {{
      "score": 0-100, "status": "...",
      "punkte": [], "probleme": []
    }},
    "technik": {{
      "score": 0-100, "status": "...",
      "punkte": [], "probleme": []
    }}
  }},
  "gesamt_score": 0-100,
  "golive_empfehlung": true,
  "golive_begruendung": "1 Satz warum ja/nein",
  "kritische_blocker": ["max 3 Dinge die VOR Go-Live behoben werden müssen"],
  "top_empfehlungen": ["5 wichtigste Verbesserungen"],
  "ki_zusammenfassung": "3-4 Sätze Gesamtbewertung für das Team"
}}

SEO: Bewerte Title-Länge ({len(scan.get("title",""))} Zeichen),
Meta-Description ({len(scan.get("meta_desc",""))} Zeichen),
H1 ({checks.get("h1_genau_eins")}), Schema ({checks.get("schema_markup")}),
OG-Tags ({checks.get("og_tags_vorhanden")}), robots.txt ({checks.get("robots_txt")}),
sitemap.xml ({checks.get("sitemap_xml")}), canonical ({checks.get("canonical_vorhanden")}),
lokale SEO-Signale.

DSGVO: Beachte impressum ({checks.get("impressum_link")}),
datenschutz ({checks.get("datenschutz_link")}),
cookie-banner ({checks.get("cookie_banner")}),
google-fonts-extern ({checks.get("google_fonts_extern")}),
dsgvo-checkbox ({checks.get("dsgvo_checkbox")}).

TECHNIK: ssl ({checks.get("ssl_aktiv")}),
https-redirect ({checks.get("https_redirect")}),
hsts ({checks.get("hsts")}), csp ({checks.get("csp")}),
favicon ({checks.get("favicon_vorhanden")}),
llm.txt ({checks.get("llm_txt")}), faq ({checks.get("faq_block")}).

CONTENT: Bilder mit Alt-Text ({checks.get("alt_texte_quote")}%),
H2 vorhanden ({checks.get("h2_vorhanden")}),
Kontaktformular ({checks.get("kontaktformular")}),
Tel-Links ({checks.get("telefon_link")}),
Google Maps ({checks.get("google_maps")}).

MOBILE: Viewport-Meta ({checks.get("mobile_viewport")}),
kein horizontales Scrollen prüfbar, schätze aufgrund HTML-Struktur.

PERFORMANCE: Cache-Header ({checks.get("cache_control")}),
PageSpeed-Daten werden separat als Wert übergeben wenn vorhanden.
"""

    try:
        resp = await frag_modell(
            client,
            model="claude-sonnet-4-6",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = resp.content[0].text
        stop = getattr(resp, 'stop_reason', None)
        logger.info(f"QA KI-Antwort: {len(raw_text)} Zeichen, stop_reason={stop}")

        result = _safe_parse_ki_json(raw_text)

        if result.get("_parse_error"):
            logger.warning(f"QA JSON-Reparatur: {result['_parse_error']}")
            logger.warning(f"Rohantwort Ende: ...{raw_text[-300:]}")

        return result
    except Exception as e:
        logger.error(f"QA KI-Auswertung Fehler: {e}")
        return {
            "kategorien": {},
            "gesamt_score": 0,
            "golive_empfehlung": False,
            "golive_begruendung": "Auswertung fehlgeschlagen",
            "kritische_blocker": [],
            "top_empfehlungen": [],
            "ki_zusammenfassung": f"Fehler: {e}",
        }


def _safe_parse_ki_json(raw_text: str) -> dict:
    """
    Parst KI-Antwort robust:
    - Entfernt Markdown-Backticks
    - Extrahiert JSON auch wenn Text davor/danach steht
    - Repariert unvollständiges JSON (abgeschnittene Antwort)
    """
    import json, re

    if not raw_text or not raw_text.strip():
        return {"_parse_error": "Leere KI-Antwort", "kategorien": {},
                "gesamt_score": 0, "golive_empfehlung": False,
                "golive_begruendung": "Leere Antwort",
                "kritische_blocker": [], "top_empfehlungen": [],
                "ki_zusammenfassung": "KI-Antwort war leer"}

    text = raw_text.strip()

    # Markdown-Backticks entfernen
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()

    # Versuch 1: Direkt parsen
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Versuch 2: Größten JSON-Block aus Text extrahieren
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Versuch 3: Unvollständiges JSON reparieren
    try:
        fixed = text
        # Unvollständigen String am Ende abschneiden
        if fixed.count('"') % 2 != 0:
            fixed = fixed[:fixed.rfind('"') + 1]
        # Unvollständige Schlüssel-Wert-Paare entfernen
        fixed = re.sub(r',\s*"[^"]*":\s*"?[^"}\]]*$', '', fixed)
        fixed = re.sub(r',\s*$', '', fixed)
        # Fehlende Klammern schließen
        open_brackets = fixed.count('[') - fixed.count(']')
        open_braces = fixed.count('{') - fixed.count('}')
        fixed += ']' * max(0, open_brackets)
        fixed += '}' * max(0, open_braces)

        result = json.loads(fixed)
        result['_parse_error'] = 'JSON war unvollständig und wurde repariert'
        return result
    except json.JSONDecodeError as e:
        return {
            "_parse_error": f"JSON nicht parsbar: {e}",
            "kategorien": {},
            "gesamt_score": 0,
            "golive_empfehlung": False,
            "golive_begruendung": "JSON-Parse fehlgeschlagen",
            "kritische_blocker": [],
            "top_empfehlungen": [],
            "ki_zusammenfassung": f"KI-Antwort konnte nicht ausgewertet werden ({len(raw_text)} Zeichen)",
        }
