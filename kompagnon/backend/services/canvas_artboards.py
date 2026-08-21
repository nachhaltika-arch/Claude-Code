"""Aus den vier KAS-Ansichten Artboards fuer einen Design-Canvas bauen.

**Warum es das gibt.** Sitemap, Wireframe, Style-Guide und Design liegen im
Werkzeug an vier Stellen: `sitemap_pages`, `projects.wireframe_data`,
`leads.brand_guideline_json` und `sitemap_pages.mockup_html`. Zu sehen sind sie
nur in vier React-Ansichten, jede mit ihrem eigenen Editor, und keine davon
zeigt zwei Seiten nebeneinander. Wer eine Kundenseite beurteilen will, klickt
sich durch.

Ein Design-Canvas legt dieselben Daten auf eine Flaeche: eine Seite je
Ansicht, ein Artboard je Kundenseite, alles nebeneinander und direkt
bearbeitbar. Diese Datei macht die Uebersetzung — **nur die Uebersetzung**.
Sie liest keine Datenbank und schreibt keine; sie bekommt einfache
Datenstrukturen und gibt Text zurueck. Das haelt sie pruefbar.

**Der Rueckweg gehoert dazu.** `markup_aus_artboard` ist die Umkehrung von
`artboard`: Was im Canvas bearbeitet wurde, muss wieder in die Kundenseite
zurueck, sonst ist der Canvas eine Sackgasse. Beide Richtungen stehen deshalb
hier, nebeneinander — wer die eine aendert, sieht die andere.
"""
import html
import re
from typing import Optional

#: Der Kopf, den der Editor erwartet. Die `support.js`-Zeile wird beim Rendern
#: durch die Laufzeit ersetzt — sie darf weder fehlen noch ausgeschrieben
#: werden.
_KOPF = (
    "<!doctype html>\n<html>\n<head>\n  <meta charset=\"utf-8\">\n"
    "  <script src=\"./support.js\"></script>\n</head>\n<body>\n<x-dc>\n"
)

_FUSS = (
    "</x-dc>\n<script data-dc-script data-props='{}'>\n"
    "class Component extends DCLogic {\n"
    "  renderVals() { return {}; }\n"
    "}\n</script>\n</body>\n</html>\n"
)

#: Zwischen diesen beiden Markierungen steht der Inhalt eines Artboards. Der
#: Rueckweg schneidet genau hier — deshalb stehen sie als Konstanten da und
#: nicht zweimal als Literal.
_INHALT_AUF = "<!-- kompagnon:inhalt -->"
_INHALT_ZU = "<!-- /kompagnon:inhalt -->"

#: Drei Zeichenfolgen duerfen im Inhalt eines Artboards nicht vorkommen, weil
#: sie die Datei von innen beenden wuerden. Kundenmarkup kommt aus der
#: KI-Generierung und aus GrapesJS — beides kann alles enthalten.
_GEFAEHRLICH = {
    "</x-dc>": "&lt;/x-dc&gt;",
    "<script data-dc-script": "&lt;script data-dc-script",
    "</helmet>": "&lt;/helmet&gt;",
}

_SLOT = re.compile(r"\{\{\s*(\w+)\s*\}\}")

#: Die Luecke im Canvas traegt den Slot-Namen als Attribut mit sich. Ohne das
#: waere der Rueckweg verlustbehaftet: Aus `{{headline}}` wuerde beim Import
#: dauerhaft ein gelber Kasten im Kundenmarkup — und der geht spaeter live.
_LUECKE = re.compile(
    r'<span[^>]*data-kompagnon-slot="(\w+)"[^>]*>.*?</span>', re.DOTALL
)


def entschaerfe(markup: Optional[str]) -> str:
    """Kundenmarkup so vorbereiten, dass es ein Artboard nicht sprengt.

    Zwei Dinge passieren hier, und beide sind bewusst sichtbar:

    * **Offene Slot-Marker werden zu sichtbaren Luecken.** `{{headline}}` ist
      im Werkzeug ein Marker, der stehenbleibt, wenn kein Text da ist — so ist
      zu sehen, dass etwas fehlt (`utils/pageHtml.js`). Im Canvas waere
      dieselbe Schreibweise eine Bindung an einen Wert, den es nicht gibt: die
      Laufzeit rendert **nichts**. Aus dem sichtbaren Hinweis wuerde ein
      unsichtbares Loch. Also wird der Marker zu `[headline]` mit gelbem
      Grund — dieselbe Aussage, in der Sprache des Canvas — und behaelt den
      Namen als Attribut, damit `verschaerfe` ihn zurueckverwandeln kann.
    * **Drei beendende Zeichenfolgen werden maskiert.** Ein Kundenmarkup mit
      `</x-dc>` darin wuerde das Artboard mittendrin schliessen und den Rest
      der Datei als Text ausgeben.
    """
    if not markup:
        return ""

    text = _SLOT.sub(
        lambda m: (
            f'<span data-kompagnon-slot="{html.escape(m.group(1))}" '
            'style="background: #fde68a; color: #78350f; padding: 0 4px; '
            'border-radius: 3px; font-family: ui-monospace, monospace; '
            f'font-size: 0.9em">[{html.escape(m.group(1))}]</span>'
        ),
        markup,
    )

    for roh, ersatz in _GEFAEHRLICH.items():
        text = text.replace(roh, ersatz)
    return text


def verschaerfe(markup: Optional[str]) -> str:
    """Die Umkehrung von `entschaerfe` — fuer den Weg aus dem Canvas zurueck.

    Aus der gelben Luecke wird wieder `{{headline}}`, aus den maskierten
    Zeichenfolgen wieder sie selbst. Wer im Canvas ueber die Luecke geschrieben
    hat, hat den Span ersetzt; dann findet die Umkehrung nichts und laesst den
    neuen Text stehen — genau richtig, denn dann ist der Slot gefuellt.
    """
    if not markup:
        return ""
    text = _LUECKE.sub(lambda m: "{{" + m.group(1) + "}}", markup)
    for roh, ersatz in _GEFAEHRLICH.items():
        text = text.replace(ersatz, roh)
    return text


def artboard(*, stil: str, inhalt: str) -> str:
    """Ein vollstaendiges `.dc.html` aus Kopfstil und Rumpf.

    `stil` landet im `<helmet>`, `inhalt` zwischen den Inhaltsmarkierungen.
    Link-Farben stehen immer im Stil: ein Link, den jemand spaeter im Canvas
    einfuegt, waere sonst browserblau.

    **`entschaerfe` laeuft hier drin, nicht beim Aufrufer.** Vier Stellen bauen
    Artboards; eine, die es vergisst, liefert eine Datei, die sich selbst
    beendet — und das faellt erst im Canvas auf.
    """
    inhalt = entschaerfe(inhalt)
    return (
        _KOPF
        + "<helmet>\n  <style>\n"
        + "    body { margin: 0; }\n"
        + "    a { color: inherit; text-decoration: underline; }\n"
        + "    a:hover { text-decoration: none; }\n"
        + stil
        + "\n  </style>\n</helmet>\n"
        + _INHALT_AUF + "\n"
        + inhalt.strip()
        + "\n" + _INHALT_ZU + "\n"
        + _FUSS
    )


def markup_aus_artboard(quelle: Optional[str]) -> Optional[str]:
    """Der Rumpf eines Artboards — oder ``None``, wenn keiner zu finden ist.

    Gibt bewusst ``None`` und nicht ``""`` zurueck, wenn die Markierungen
    fehlen. Ein leerer String hiesse „die Seite ist jetzt leer" und wuerde beim
    Import eine Kundenseite loeschen; ``None`` heisst „das hier ist kein
    Artboard, das ich geschrieben habe" — und der Import laesst es liegen.
    """
    if not quelle:
        return None
    auf = quelle.find(_INHALT_AUF)
    zu = quelle.rfind(_INHALT_ZU)
    if auf == -1 or zu == -1 or zu < auf:
        return None
    return quelle[auf + len(_INHALT_AUF):zu].strip()
