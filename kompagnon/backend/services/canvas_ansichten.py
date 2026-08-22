"""Die vier KAS-Ansichten als Artboards: Sitemap, Wireframe, Style-Guide, Design.

Jede Funktion hier bekommt einfache Datenstrukturen — Listen und Dicts, wie sie
die Router ohnehin schon zurueckgeben — und liefert ein fertiges `.dc.html`.
Keine Datenbank, kein Netz, kein Zustand. Das ist der Grund, warum sie
vollstaendig mit Tests abgedeckt werden koennen, ohne dass ein Canvas oder ein
Browser im Spiel ist.

**Zwei Handschriften, mit Absicht.** Sitemap, Wireframe und Style-Guide sind
KOMPAGNON-Oberflaeche und tragen die Tool-CI (`styles/tokens.css`: Dark Teal
#004F59, Noto Sans, 8px-Raster). Das Design-Artboard traegt die **Marke des
Kunden** — es zeigt die Seite so, wie sie ausgeliefert wird. Wer beides gleich
gestaltet, verwischt genau die Grenze, um die es geht.
"""
import html
from typing import Optional
from urllib.parse import quote

from services.canvas_artboards import artboard

# ── Tool-CI, aus `frontend/src/styles/tokens.css` ────────────────────────────
_DARK = "#004F59"
_MID = "#008EAA"
_GELB = "#FAE600"
_FLAECHE = "#F0F4F5"
_PAPIER = "#FAFAFA"
_RAHMEN = "#D5E0E2"
_TEXT = "#000000"
_TEXT_60 = "#4A5A5C"
_TEXT_45 = "#647071"

_TOOL_SCHRIFT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Noto+Sans:wght@400;600;900&display=swap');\n"
    "    body { font-family: 'Noto Sans', system-ui, sans-serif; "
    f"background: {_FLAECHE}; color: {_TEXT}; }}\n"
)


def _e(wert) -> str:
    """Text als Text, nie als Markup. Seitennamen kommen aus der KI."""
    return html.escape(str(wert or ""))


def _schriftimport(*namen: Optional[str]) -> str:
    """Ein Google-Fonts-Import fuer die Schriften des Kunden.

    Google Fonts ist der einzige Host, den der Canvas laedt. Ein Name, den es
    dort nicht gibt, laesst den Import stillschweigend scheitern — dafuer steht
    hinter jeder Schrift eine Ersatzkette.
    """
    sauber = sorted({n.strip() for n in namen if n and n.strip()})
    if not sauber:
        return ""
    familien = "&".join(f"family={quote(n.replace(' ', '+'), safe='+')}" for n in sauber)
    return f"@import url('https://fonts.googleapis.com/css2?{familien}&display=swap');\n"


# ── 1. Sitemap ───────────────────────────────────────────────────────────────

_STATUS_FARBE = {
    "geplant": ("#E0F4F8", "#007490"),
    "in_arbeit": ("#FFF4E0", "#9A6000"),
    "fertig": ("#E3F6EF", "#007A51"),
}


def _sitemap_karte(seite: dict, tiefe: int) -> str:
    grund, schrift = _STATUS_FARBE.get(seite.get("status") or "geplant", _STATUS_FARBE["geplant"])
    zeilen = []
    if seite.get("ziel_keyword"):
        zeilen.append(f"Keyword: {_e(seite['ziel_keyword'])}")
    if seite.get("cta_text"):
        zeilen.append(f"CTA: {_e(seite['cta_text'])} → {_e(seite.get('cta_ziel') or 'kontakt')}")
    zweck = _e(seite.get("zweck") or "")

    return (
        f'<div style="margin-left: {tiefe * 32}px; background: {_PAPIER}; '
        f'border: 1px solid {_RAHMEN}; border-left: 4px solid {_MID}; '
        'border-radius: 8px; padding: 16px 20px; display: flex; '
        'flex-direction: column; gap: 8px">\n'
        '  <div style="display: flex; align-items: center; gap: 12px">\n'
        f'    <span style="font-weight: 900; font-size: 17px; color: {_TEXT}">'
        f'{_e(seite.get("page_name"))}</span>\n'
        f'    <span style="font-size: 11px; letter-spacing: 0.08em; '
        f'text-transform: uppercase; color: {_TEXT_45}">'
        f'{_e(seite.get("page_type") or "info")}</span>\n'
        f'    <span style="margin-left: auto; font-size: 11px; padding: 3px 10px; '
        f'border-radius: 999px; background: {grund}; color: {schrift}">'
        f'{_e(seite.get("status") or "geplant")}</span>\n'
        '  </div>\n'
        + (f'  <div style="font-size: 13px; color: {_TEXT_60}; line-height: 1.5">{zweck}</div>\n'
           if zweck else "")
        + (f'  <div style="font-size: 12px; color: {_TEXT_45}">' + " · ".join(zeilen) + "</div>\n"
           if zeilen else "")
        + "</div>"
    )


def sitemap_artboard(*, betrieb: str, seiten: list) -> str:
    """Der Seitenbaum eines Betriebs — Einstieg des Canvas.

    `seiten` ist die flache Liste aus `GET /api/sitemap/{lead_id}`; die
    Verschachtelung entsteht hier ueber `parent_id`.
    """
    nach_eltern: dict = {}
    for s in seiten:
        nach_eltern.setdefault(s.get("parent_id"), []).append(s)
    for liste in nach_eltern.values():
        liste.sort(key=lambda s: (s.get("position") or 0, s.get("id") or 0))

    karten: list = []

    def _entfalte(eltern_id, tiefe: int) -> None:
        for s in nach_eltern.get(eltern_id, []):
            karten.append(_sitemap_karte(s, tiefe))
            _entfalte(s.get("id"), tiefe + 1)

    _entfalte(None, 0)

    if not karten:
        karten.append(
            f'<div style="padding: 24px; border: 2px dashed {_RAHMEN}; border-radius: 8px; '
            f'color: {_TEXT_45}; font-size: 14px">Fuer diesen Betrieb ist noch keine '
            "Sitemap angelegt.</div>"
        )

    inhalt = (
        '<div style="padding: 40px; display: flex; flex-direction: column; gap: 24px">\n'
        '  <div style="display: flex; flex-direction: column; gap: 4px">\n'
        f'    <span style="font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; '
        f'color: {_MID}; font-weight: 600">Sitemap</span>\n'
        f'    <h1 style="margin: 0; font-size: 30px; font-weight: 900; color: {_DARK}; '
        f'text-wrap: balance">{_e(betrieb)}</h1>\n'
        f'    <span style="font-size: 13px; color: {_TEXT_45}">{len(karten)} Seiten</span>\n'
        "  </div>\n"
        '  <div style="display: flex; flex-direction: column; gap: 12px">\n'
        + "\n".join(karten)
        + "\n  </div>\n</div>"
    )
    return artboard(stil=f"    {_TOOL_SCHRIFT}", inhalt=inhalt)


# ── 2. Wireframe ─────────────────────────────────────────────────────────────

def _wireframe_block(block: dict, nr: int) -> str:
    slots = block.get("slots") or {}
    eintraege = "".join(
        f'<div style="display: flex; gap: 10px; font-size: 12px; line-height: 1.5">'
        f'<span style="color: {_TEXT_45}; min-width: 96px; flex-shrink: 0; '
        f'font-family: ui-monospace, monospace">{_e(k)}</span>'
        f'<span style="color: {_TEXT_60}">{_e(v)}</span></div>'
        for k, v in slots.items()
        if isinstance(v, (str, int, float)) and str(v).strip()
    )
    eigen = (
        f'<span style="font-size: 10px; padding: 2px 8px; border-radius: 999px; '
        f'background: {_GELB}; color: {_TEXT}">eigene Fassung</span>'
        if (block.get("html_override") or "").strip()
        else ""
    )
    return (
        f'<div style="border: 1.5px solid {_RAHMEN}; border-radius: 8px; background: {_PAPIER}; '
        'padding: 16px 18px; display: flex; flex-direction: column; gap: 10px">\n'
        '  <div style="display: flex; align-items: center; gap: 10px">\n'
        f'    <span style="width: 22px; height: 22px; border-radius: 6px; background: {_DARK}; '
        'color: #fff; font-size: 11px; font-weight: 600; display: flex; align-items: center; '
        f'justify-content: center; flex-shrink: 0">{nr}</span>\n'
        f'    <span style="font-family: ui-monospace, monospace; font-size: 13px; color: {_DARK}">'
        f'{_e(block.get("slug"))}</span>\n'
        f"    {eigen}\n"
        "  </div>\n"
        + (f'  <div style="display: flex; flex-direction: column; gap: 4px">{eintraege}</div>\n'
           if eintraege
           else f'  <div style="font-size: 12px; color: {_TEXT_45}">noch kein Text</div>\n')
        + "</div>"
    )


def wireframe_artboard(*, seitenname: str, bloecke: list) -> str:
    """Das Blockgeruest einer Seite — Reihenfolge und Slots, kein Aussehen.

    Der Wireframe ist bewusst grau: Wer hier ueber Farben spricht, spricht ueber
    die falsche Stufe. Sichtbar ist, **was** auf der Seite steht und **in
    welcher Reihenfolge**.
    """
    sortiert = sorted(bloecke or [], key=lambda b: b.get("order") or 0)
    kaesten = [_wireframe_block(b, i + 1) for i, b in enumerate(sortiert)]
    if not kaesten:
        kaesten.append(
            f'<div style="padding: 24px; border: 2px dashed {_RAHMEN}; border-radius: 8px; '
            f'color: {_TEXT_45}; font-size: 13px">Fuer diese Seite ist noch kein Wireframe '
            "erzeugt.</div>"
        )

    inhalt = (
        '<div style="padding: 32px; display: flex; flex-direction: column; gap: 20px">\n'
        '  <div style="display: flex; flex-direction: column; gap: 4px">\n'
        f'    <span style="font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; '
        f'color: {_MID}; font-weight: 600">Wireframe</span>\n'
        f'    <h2 style="margin: 0; font-size: 22px; font-weight: 900; color: {_DARK}">'
        f'{_e(seitenname)}</h2>\n'
        "  </div>\n"
        '  <div style="display: flex; flex-direction: column; gap: 10px">\n'
        + "\n".join(kaesten)
        + "\n  </div>\n</div>"
    )
    return artboard(stil=f"    {_TOOL_SCHRIFT}", inhalt=inhalt)


# ── 3. Style-Guide ───────────────────────────────────────────────────────────

def _farbfeld(name: str, wert: str) -> str:
    return (
        '<div style="display: flex; flex-direction: column; gap: 6px">\n'
        f'  <div style="height: 64px; border-radius: 8px; background: {_e(wert)}; '
        f'border: 1px solid {_RAHMEN}"></div>\n'
        f'  <span style="font-size: 12px; font-weight: 600; color: {_TEXT}">{_e(name)}</span>\n'
        f'  <span style="font-size: 11px; color: {_TEXT_45}; '
        f'font-family: ui-monospace, monospace">{_e(wert)}</span>\n'
        "</div>"
    )


def styleguide_artboard(*, betrieb: str, marke: dict) -> str:
    """Farben, Schriften und Bausteine auf einem Blatt — mit ihrer Herkunft.

    `marke` kommt aus `design_canvas._marke` und nennt neben Farben, Schriften
    und Radius auch die **Quelle**. Die steht mit im Artboard: Ein Style-Guide
    aus dem Scrape der alten Kundenseite sieht aus wie einer, der entschieden
    wurde — nur wer die Herkunft liest, merkt den Unterschied.

    Was fehlt, wird als Luecke benannt statt erfunden. Eine erfundene
    Markenfarbe landet ueber den Design-Zweig auf einer Kundenseite.
    """
    farben = [(k, v) for k, v in (marke.get("farben") or {}).items()
              if isinstance(v, str) and v.strip()]
    felder = "".join(_farbfeld(k, v) for k, v in farben)

    schriften = marke.get("schriften") or {}
    h1 = schriften.get("heading") or ""
    body = schriften.get("body") or ""
    akzent = schriften.get("accent") or ""
    primaer = next((v for k, v in farben if k == "primary"), _DARK)

    proben = "".join(
        '<div style="display: flex; flex-direction: column; gap: 4px">'
        f'<span style="font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; '
        f'color: {_TEXT_45}">{_e(rolle)} — {_e(name)}</span>'
        f'<span style="font-family: \'{_e(name)}\', {ersatz}; font-size: {groesse}px; '
        f'color: {_TEXT}">Wärmepumpe für Ihr Zuhause</span></div>'
        for rolle, name, groesse, ersatz in (
            ("Überschrift", h1, 30, "Georgia, serif"),
            ("Fließtext", body, 16, "system-ui, sans-serif"),
            ("Akzent", akzent, 18, "'Barlow Condensed', sans-serif"),
        )
        if name
    ) or (f'<span style="font-size: 13px; color: {_TEXT_45}">Für diesen Betrieb sind noch '
          "keine Schriften hinterlegt.</span>")

    knopf = (
        f'<span style="display: inline-flex; padding: 12px 24px; border-radius: '
        f'{_e(marke.get("radius") or 6)}px; background: {_e(primaer)}; color: #fff; '
        'font-size: 15px; font-weight: 600">Termin anfragen</span>'
    )

    quelle = marke.get("quelle")
    herkunft = (
        f'<span style="font-size: 12px; color: {_TEXT_45}">Quelle: {_e(quelle)}</span>'
        if quelle else ""
    )

    inhalt = (
        '<div style="padding: 40px; display: flex; flex-direction: column; gap: 32px">\n'
        '  <div style="display: flex; flex-direction: column; gap: 4px">\n'
        f'    <span style="font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; '
        f'color: {_MID}; font-weight: 600">Style Guide</span>\n'
        f'    <h1 style="margin: 0; font-size: 30px; font-weight: 900; color: {_DARK}">'
        f'{_e(betrieb)}</h1>\n'
        f"    {herkunft}\n"
        "  </div>\n"
        + (f'  <div><div style="font-size: 13px; font-weight: 600; color: {_TEXT_60}; '
           'margin-bottom: 12px">Farben</div>'
           '<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); '
           f'gap: 16px">{felder}</div></div>\n'
           if felder
           else f'  <div style="font-size: 13px; color: {_TEXT_45}">Für diesen Betrieb sind '
                "noch keine Markenfarben hinterlegt.</div>\n")
        + f'  <div><div style="font-size: 13px; font-weight: 600; color: {_TEXT_60}; '
          'margin-bottom: 12px">Schriften</div>'
          f'<div style="display: flex; flex-direction: column; gap: 16px">{proben}</div></div>\n'
        + f'  <div><div style="font-size: 13px; font-weight: 600; color: {_TEXT_60}; '
          f'margin-bottom: 12px">Bausteine</div>{knopf}</div>\n'
        "</div>"
    )
    stil = f"    {_schriftimport(h1, body, akzent)}    {_TOOL_SCHRIFT}"
    return artboard(stil=stil, inhalt=inhalt)


# ── 4. Design ────────────────────────────────────────────────────────────────

def design_artboard(*, seitenname: str, markup: Optional[str], schriften: dict) -> str:
    """Die Kundenseite, wie sie ausgeliefert wird.

    Hier steht **keine** Tool-CI: das Markup kommt aus `mockup_html` und bringt
    sein eigenes CSS mit. Was dieses Artboard hinzufuegt, ist der
    Schriftimport — ohne ihn zeigt der Canvas die Ersatzschrift und die Seite
    sieht falsch aus, obwohl sie richtig gespeichert ist.
    """
    if not (markup or "").strip():
        inhalt = (
            '<div style="padding: 48px; display: flex; flex-direction: column; gap: 12px; '
            f'font-family: \'Noto Sans\', system-ui, sans-serif; background: {_FLAECHE}">\n'
            f'  <h2 style="margin: 0; font-size: 20px; font-weight: 900; color: {_DARK}">'
            f'{_e(seitenname)}</h2>\n'
            f'  <p style="margin: 0; font-size: 14px; color: {_TEXT_45}">Für diese Seite ist '
            "noch kein Design übernommen. Im Werkzeug entsteht es aus Wireframe und "
            "Style-Guide über „Auf die Seite übernehmen“.</p>\n"
            "</div>"
        )
        return artboard(stil=f"    {_TOOL_SCHRIFT}", inhalt=inhalt)

    stil = f"    {_schriftimport(schriften.get('heading'), schriften.get('body'), schriften.get('accent'))}"
    return artboard(stil=stil, inhalt=markup)
