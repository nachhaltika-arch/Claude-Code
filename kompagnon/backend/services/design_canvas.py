"""Einen Design-Canvas aus einem Betrieb bauen — und das Bearbeitete zurueckholen.

**Was hier passiert.** `canvas_ansichten` weiss, wie ein einzelnes Artboard
aussieht. Diese Datei weiss, **welche** Artboards es fuer einen Betrieb gibt,
wie sie auf der Flaeche liegen und wie eine Bearbeitung wieder in die
Kundenseite zurueckfindet.

**Der Dateiname ist der Anker.** Ein Artboard heisst `Design12.dc.html`, wobei
12 die `sitemap_pages.id` ist. Nicht die Position: Wer zwischen Ausgabe und
Ruecknahme eine Seite einfuegt, wuerde sonst das Design der einen Seite auf
eine andere schreiben. Die Kennung aendert sich nicht, die Reihenfolge schon.

**Der Rueckweg schreibt versioniert.** Ein Import legt eine neue Zeile in
`mockup_versions` an, bevor er `sitemap_pages.mockup_html` ueberschreibt. Was
vorher dastand, bleibt damit abrufbar — der Canvas ist ein zweiter Editor auf
denselben Daten, und ein zweiter Editor ohne Verlauf ist eine Falle.
"""
import json
import logging
import re
from typing import Optional

from services.canvas_ansichten import (
    design_artboard,
    sitemap_artboard,
    styleguide_artboard,
    wireframe_artboard,
)
from services.canvas_artboards import markup_aus_artboard, verschaerfe

logger = logging.getLogger(__name__)

#: Die vier Seiten des Canvas — dieselbe Reihenfolge wie der Umschalter in
#: `KASSidebar.jsx`, damit niemand zweimal lernen muss, wo was liegt.
SEITEN = [
    {"id": "sitemap", "name": "Sitemap"},
    {"id": "wireframe", "name": "Wireframe"},
    {"id": "styleguide", "name": "Style Guide"},
    {"id": "design", "name": "Design"},
]

_DESIGN_DATEI = re.compile(r"^Design(\d+)\.dc\.html$")

# Rahmenmasse in Canvas-Pixeln. Sie schneiden nichts ab — ein zu kleiner Rahmen
# laesst das Artboard scrollen statt schrumpfen —, deshalb lieber grosszuegig.
_MASS = {
    "sitemap": (920, 760),
    "wireframe": (760, 1180),
    "styleguide": (960, 1100),
    "design": (1280, 1700),
}
_ABSTAND = 80


def _lade(text: Optional[str], vorgabe):
    """JSON aus einer Textspalte — im Zweifel die Vorgabe, nie ein Absturz."""
    if not text:
        return vorgabe
    try:
        return json.loads(text)
    except Exception:
        return vorgabe


def _style_guide(project) -> dict:
    """Der Style-Guide des Projekts — das, was `StyleGuideView` fuehrt.

    Er liegt **in** `wireframe_data`, nicht bei den Markendaten des Leads. Das
    ist keine Doppelung, sondern eine Reihenfolge: `leads.brand_*` ist die
    **gescrapte** Marke der bestehenden Kundenseite, `style_guide` die
    **entschiedene** Marke der neuen. Wer die gescrapte zeigt, wo die
    entschiedene existiert, zeigt den Stand vor der Arbeit.
    """
    daten = _wireframe_daten(project)
    guide = daten.get("style_guide") if isinstance(daten, dict) else None
    return guide if isinstance(guide, dict) else {}


def _marke(lead, project=None) -> dict:
    """Farben, Schriften und Radius eines Betriebs — mit der Quelle dazu.

    Vier Quellen in fester Rangfolge, von der entschiedensten zur aeltesten:

    1. `wireframe_data.style_guide` — im Projekt entschieden und bestaetigt,
    2. `leads.brand_guideline_json` — die erzeugte Marken-Guideline,
    3. `leads.brand_design_tokens_json` — rohe Tokens aus dem Scrape,
    4. die Einzelspalten `leads.brand_*` — die aelteste Quelle.

    `quelle` wird mitgeliefert und im Artboard genannt. Ein Style-Guide, dem
    man nicht ansieht, woher er kommt, laesst niemanden merken, dass er den
    Stand vor der Arbeit betrachtet.
    """
    guide = _style_guide(project)
    guideline = _lade(getattr(lead, "brand_guideline_json", None), {}) or {}
    roh = _lade(getattr(lead, "brand_design_tokens_json", None), {}) or {}

    farben: dict = {}
    quelle = None

    # `style_guide` ist im Modell ein freies Dict (`WireframeData`), und es
    # stehen zwei Schreibweisen darin: `StyleGuideView.buildTokens` schreibt
    # `colors`, aeltere Zeilen und der E2E-Seed `palette`. Beide sind dieselbe
    # Sache; wer nur eine liest, uebersieht die halbe Datenlage.
    for schluessel in ("colors", "palette"):
        if isinstance(guide.get(schluessel), dict):
            farben = {k: v for k, v in guide[schluessel].items() if isinstance(v, str)}
            if farben:
                quelle = "Style-Guide des Projekts"
                break

    if not farben:
        tokens = dict(roh)
        tokens.update({k: v for k, v in (guideline.get("tokens") or {}).items() if v})
        farben = {k: v for k, v in tokens.items()
                  if isinstance(v, str) and v.strip().startswith(("#", "rgb"))}
        if farben:
            quelle = ("Marken-Guideline des Betriebs" if guideline.get("tokens")
                      else "Markenfarben aus dem Scrape")

    if not farben:
        farben = {name: getattr(lead, spalte)
                  for name, spalte in (("primary", "brand_primary_color"),
                                       ("secondary", "brand_secondary_color"))
                  if getattr(lead, spalte, None)}
        if farben:
            quelle = "Einzelfelder am Betrieb"

    tokens_alt = dict(roh)
    tokens_alt.update(guideline.get("tokens") or {})
    schriften = {
        "heading": tokens_alt.get("font_h1")
                   or getattr(lead, "brand_font_heading", None)
                   or getattr(lead, "brand_font_primary", None),
        "body": (guide.get("typography") or {}).get("font_family")
                or tokens_alt.get("font_body")
                or getattr(lead, "brand_font_body", None)
                or getattr(lead, "brand_font_secondary", None),
        "accent": tokens_alt.get("font_akzent") or getattr(lead, "brand_font_accent", None),
    }

    radius = ((guide.get("buttons") or {}).get("radius")
              or tokens_alt.get("radius")
              or 6)

    return {"farben": farben, "schriften": schriften, "radius": radius, "quelle": quelle}


def _wireframe_daten(project):
    """`wireframe_data`, egal in welcher der drei Formen es dasteht.

    Der Router speichert ein **Objekt** (`{"pages": [...], "style_guide": …}`,
    siehe `WireframeData`), die Spalte hat als Vorgabe eine **Liste**, und in
    aelteren Zeilen steht JSON als **Text**. Eine erste Fassung dieser Datei
    kannte nur die Liste — und haette bei jedem Projekt mit echtem Wireframe
    „noch kein Wireframe" angezeigt.
    """
    daten = getattr(project, "wireframe_data", None) if project else None
    if isinstance(daten, str):
        daten = _lade(daten, None)
    if isinstance(daten, list):
        return {"pages": daten}
    if isinstance(daten, dict):
        return daten
    return {}


def _bloecke_je_seite(project) -> dict:
    """`wireframe_data` nach `page_id` aufgeschluesselt.

    Was nicht wie eine Seite mit Bloecken aussieht, wird uebergangen: Ein
    fehlender oder unerwarteter Wireframe ist kein Grund, den ganzen Canvas zu
    verweigern.
    """
    seiten = _wireframe_daten(project).get("pages")
    if not isinstance(seiten, list):
        return {}
    ergebnis = {}
    for eintrag in seiten:
        if isinstance(eintrag, dict) and isinstance(eintrag.get("blocks"), list):
            ergebnis[eintrag.get("page_id")] = eintrag["blocks"]
    return ergebnis


def baue(*, lead, seiten: list, project=None) -> dict:
    """Die Dateien und die Anordnung eines Canvas fuer einen Betrieb.

    Gibt `{"files": {...}, "canvas": {...}}` zurueck — genau die zwei Dinge,
    aus denen ein Canvas besteht. Keine Datenbank wird hier angefasst; die
    Aufrufer reichen fertige Objekte herein.
    """
    betrieb = getattr(lead, "company_name", None) or "Betrieb"
    marke = _marke(lead, project)
    schriften = marke["schriften"]
    bloecke = _bloecke_je_seite(project)

    geordnet = sorted(seiten, key=lambda s: (s.get("position") or 0, s.get("id") or 0))

    dateien = {
        "Main.dc.html": sitemap_artboard(betrieb=betrieb, seiten=seiten),
        "Styleguide.dc.html": styleguide_artboard(betrieb=betrieb, marke=marke),
    }
    artboards = [
        {"file": "Main.dc.html", "title": "Sitemap", "page": "sitemap",
         "x": 0, "y": 0, "w": _MASS["sitemap"][0], "h": _MASS["sitemap"][1]},
        {"file": "Styleguide.dc.html", "title": f"Style Guide — {betrieb}",
         "page": "styleguide", "x": 0, "y": 0,
         "w": _MASS["styleguide"][0], "h": _MASS["styleguide"][1]},
    ]

    for nr, seite in enumerate(geordnet):
        kennung = seite.get("id")
        name = seite.get("page_name") or f"Seite {kennung}"

        wf = f"Wireframe{kennung}.dc.html"
        dateien[wf] = wireframe_artboard(
            seitenname=name, bloecke=bloecke.get(kennung) or []
        )
        artboards.append({
            "file": wf, "title": name, "page": "wireframe",
            "x": nr * (_MASS["wireframe"][0] + _ABSTAND), "y": 0,
            "w": _MASS["wireframe"][0], "h": _MASS["wireframe"][1],
        })

        ds = f"Design{kennung}.dc.html"
        dateien[ds] = design_artboard(
            seitenname=name, markup=seite.get("mockup_html"), schriften=schriften
        )
        artboards.append({
            "file": ds, "title": name, "page": "design",
            "x": nr * (_MASS["design"][0] + _ABSTAND), "y": 0,
            "w": _MASS["design"][0], "h": _MASS["design"][1],
        })

    return {
        "files": dateien,
        "canvas": {
            "artboards": artboards,
            "pages": SEITEN,
            "launch": {"view": "canvas", "page": "sitemap"},
        },
    }


def uebernimm(*, dateien: dict, seiten_nach_id: dict) -> list:
    """Bearbeitete Design-Artboards zurueck in Kundenseiten uebersetzen.

    Liefert eine Liste von `{"page_id", "markup"}` — was damit geschieht,
    entscheidet der Router. Vier Faelle werden dabei uebergangen statt gemeldet,
    weil sie alle harmlos sind und ein Abbruch die uebrigen Seiten mitnehmen
    wuerde:

    * eine Datei, die kein `Design<id>.dc.html` ist (Sitemap, Wireframe,
      Style-Guide, `canvas.json`, ein im Canvas neu angelegtes Artboard),
    * eine Kennung, die zu diesem Betrieb nicht gehoert — ein Canvas eines
      anderen Kunden schreibt hier nichts,
    * eine Datei ohne die Inhaltsmarkierungen: nicht von uns, also nicht
      unsere Seite,
    * ein leerer Rumpf: eine Seite zu leeren ist ein Loeschvorgang und
      passiert nicht aus Versehen ueber einen Import.
    """
    ergebnis = []
    for name, quelle in (dateien or {}).items():
        treffer = _DESIGN_DATEI.match(name)
        if not treffer:
            continue
        kennung = int(treffer.group(1))
        if kennung not in seiten_nach_id:
            logger.info("Canvas-Import: Artboard %s gehoert nicht zu diesem Betrieb", name)
            continue
        rumpf = markup_aus_artboard(quelle)
        if rumpf is None:
            logger.info("Canvas-Import: %s traegt keine Inhaltsmarkierung", name)
            continue
        markup = verschaerfe(rumpf)
        if not markup.strip():
            logger.info("Canvas-Import: %s ist leer — Seite bleibt unveraendert", name)
            continue
        ergebnis.append({"page_id": kennung, "markup": markup})
    return ergebnis
