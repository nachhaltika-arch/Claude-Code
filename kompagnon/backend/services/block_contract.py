"""
Der Vertrag für Bibliotheksblöcke.

Ein Block, den Claude erzeugt, muss dasselbe erfüllen wie ein von Hand
gebauter — sonst zerlegt er im Wireframe-Editor das Raster, schleppt fremde
Ressourcen ein oder kollidiert mit sich selbst, wenn er zweimal auf einer
Seite steht.

**Die Regeln sind an der bestehenden Bibliothek gemessen, nicht erfunden.**
Ein erster Entwurf verlangte ``{{UPPER_SNAKE}}``-Slots, verbot jedes
``style``-Attribut und wollte ``data-gjs-*`` sehen. Die 41 vorhandenen Blöcke
nutzen ``{{lower_snake}}``, ein ``style`` für die Schriftfamilie und
``data-block`` — der Entwurf hätte also die eigene Bibliothek durchfallen
lassen. `tests/test_block_contract.py` prüft deshalb jeden echten Block gegen
diese Regeln; was hier steht, muss die Bibliothek bestehen.

Geprüft wird mit Zeichenketten und einem HTML-Parser aus der Standardbibliothek
— bewusst ohne neue Abhängigkeit.
"""
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import List, Optional

# Fremdes laden oder ausführen. <h1> steht bewusst NICHT hier: Ein Hero ist
# die Hauptüberschrift seiner Seite, und die halbe Bibliothek nutzt sie so.
VERBOTENE_TAGS = ("script", "iframe", "object", "embed", "link", "base")

# Nur automatisch geladene Ressourcen. Ein <a href="https://wa.me/…"> ist ein
# Link, den jemand anklickt — der geht in Ordnung und steht in der Bibliothek.
EXTERNE_QUELLE = re.compile(r'src\s*=\s*["\']https?://', re.IGNORECASE)
CSS_IMPORT = re.compile(r'@import|url\(\s*["\']?https?://', re.IGNORECASE)

# on-Attribute holen Verhalten ins Markup, das im Editor unsichtbar ist.
EREIGNIS_ATTRIBUT = re.compile(r'\son[a-z]+\s*=', re.IGNORECASE)

# Slots der Bibliothek: {{kleinbuchstaben_mit_unterstrich}}
SLOT = re.compile(r"\{\{\s*([a-z][a-z0-9_]*)\s*\}\}")
SLOT_FALSCH = re.compile(r"\{\{\s*([^}]*?)\s*\}\}")

# Fest verankert im Dokument — sprengt die Vorschau im Editor.
FESTE_POSITION = re.compile(r'position\s*:\s*(fixed|sticky)', re.IGNORECASE)

MAX_TIEFE = 12

# ── R5: Marken-Bindung ──────────────────────────────────────────────────
#
# Die Farbe einer Kundenseite kommt aus dem Style-Guide, nicht aus dem Block.
# Angewendet wird sie, indem `DesignView.buildOverrideCSS` die Graustufen des
# Wireframes gegen die Marken-Token tauscht. Ein bunter Ton im Block wird davon
# nicht erfasst — er ueberlebt den Markenwechsel und steht beim Kunden.
#
# Gemessen, bevor die Regel scharf geschaltet wurde: Die 45 Bloecke der
# Bibliothek nutzen 298× `gray`, 222× `slate`, dazu `white`, `black` und
# `transparent` — keinen einzigen bunten Ton. Die Regel beschreibt also, was
# die Bibliothek ohnehin tut.
NEUTRALE_TOENE = {"gray", "slate", "zinc", "neutral", "stone"}
NEUTRALE_WOERTER = {"white", "black", "transparent", "current", "inherit", "none"}

# Klassen-Praefixe, die ueberhaupt Farbe setzen koennen. `rounded`, `p`, `m`,
# `w` und Konsorten stehen bewusst nicht dabei.
FARB_PRAEFIXE = ("bg", "text", "border", "divide", "ring", "from", "via", "to",
                 "fill", "stroke", "placeholder", "accent", "decoration",
                 "outline", "caret", "shadow")

KLASSEN_ATTRIBUT = re.compile(r'class\s*=\s*"([^"]*)"', re.IGNORECASE)
STYLE_ATTRIBUT = re.compile(r'style\s*=\s*"([^"]*)"', re.IGNORECASE)

# Ein eigener Wert in der Klasse: bg-[#004F59], text-[rgb(0,79,89)] — aber
# auch text-[11px], und das ist eine Groesse.
FARBWERT = re.compile(r"#[0-9a-f]{3,8}\b|\b(?:rgba?|hsla?|oklch|lab)\s*\(",
                      re.IGNORECASE)
HEX_FARBE = re.compile(r"#([0-9a-f]{3,8})\b", re.IGNORECASE)
RGB_FARBE = re.compile(r"\brgba?\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)",
                       re.IGNORECASE)
# Farbtoene, die nicht ueber rgb/hex laufen: hsl mit Buntheit, benannte Farben.
HSL_FARBE = re.compile(r"\bhsla?\s*\(\s*[\d.]+\s*[, ]\s*([\d.]+)%", re.IGNORECASE)
STUFE = re.compile(r"^\d{2,3}$")


@dataclass(frozen=True)
class Verstoss:
    regel: str
    text: str

    def __str__(self) -> str:  # für Fehlermeldungen und Logs
        return f"{self.regel}: {self.text}"


class _Baum(HTMLParser):
    """Zählt Verschachtelungstiefe und sammelt Tags, ids und das Wurzelelement."""

    LEER = {"br", "hr", "img", "input", "meta", "source", "wbr", "col"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tiefe = 0
        self.max_tiefe = 0
        self.tags: List[str] = []
        self.ids: List[str] = []
        self.wurzel: Optional[str] = None
        self.wurzel_attrs: dict = {}
        self.wurzeln = 0

    def handle_starttag(self, tag, attrs):
        attr = {k.lower(): (v or "") for k, v in attrs}
        if self.tiefe == 0:
            self.wurzeln += 1
            if self.wurzel is None:
                self.wurzel, self.wurzel_attrs = tag, attr
        self.tags.append(tag)
        if "id" in attr and attr["id"]:
            self.ids.append(attr["id"])
        if tag not in self.LEER:
            self.tiefe += 1
            self.max_tiefe = max(self.max_tiefe, self.tiefe)

    def handle_endtag(self, tag):
        if tag not in self.LEER and self.tiefe > 0:
            self.tiefe -= 1


def _ohne_kommentare(html: str) -> str:
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def _bunter_ton(klasse: str) -> bool:
    """Traegt diese Klasse einen Farbton, den kein Markenwechsel erwischt?

    Varianten (``md:``, ``hover:``) und das ``!`` fuer wichtig stehen davor und
    sagen nichts ueber die Farbe. Danach zaehlt nur das Ende: ``…-<ton>-<stufe>``
    oder ein Grundwort wie ``white``.
    """
    rein = klasse.split(":")[-1].lstrip("!")
    if "-" not in rein:
        return False
    praefix, rest = rein.split("-", 1)
    if praefix not in FARB_PRAEFIXE:
        return False

    if rest.startswith("["):                     # eigener Wert: bg-[#004F59]
        return bool(FARBWERT.search(rest))

    teile = rest.split("/")[0].split("-")        # Deckkraft abtrennen
    if len(teile) >= 2 and STUFE.match(teile[-1]):
        return teile[-2] not in NEUTRALE_TOENE   # slate-600 ja, blue-600 nein
    if len(teile) == 1:
        # bg-white, text-black — und alles andere ohne Stufe ist Groesse
        # oder Ausrichtung (text-3xl, shadow-md, border-t).
        return False
    return False


def _bunte_farbwerte(stil: str) -> List[str]:
    """Farbwerte in einem style-Attribut, die nicht Graustufe sind.

    Ein style-Attribut kann kein Override umbiegen: Was hier steht, steht beim
    Kunden. Graustufen sind unbedenklich — sie passen zu jeder Marke.
    """
    gefunden = []
    for wert in HEX_FARBE.findall(stil):
        if len(wert) in (3, 4):                  # #abc → #aabbcc
            kanaele = [int(z * 2, 16) for z in wert[:3]]
        elif len(wert) in (6, 8):
            kanaele = [int(wert[i:i + 2], 16) for i in (0, 2, 4)]
        else:
            continue
        if len(set(kanaele)) > 1:
            gefunden.append(f"#{wert}")
    for r, g, b in RGB_FARBE.findall(stil):
        if len({r, g, b}) > 1:
            gefunden.append(f"rgb({r},{g},{b})")
    for saettigung in HSL_FARBE.findall(stil):
        if float(saettigung) > 0:
            gefunden.append(f"hsl(…{saettigung}%…)")
    return gefunden


def slots_im_markup(html: str) -> List[str]:
    """Die Slot-Namen, die im Markup tatsächlich vorkommen — ohne Dubletten."""
    gesehen, ergebnis = set(), []
    for name in SLOT.findall(_ohne_kommentare(html)):
        if name not in gesehen:
            gesehen.add(name)
            ergebnis.append(name)
    return ergebnis


def pruefe(html: str, slug: str = "",
           slots: Optional[List[dict]] = None) -> List[Verstoss]:
    """Alle Verstöße eines Blocks. Leere Liste heißt: vertragskonform."""
    if not (html or "").strip():
        return [Verstoss("R0", "Der Block ist leer.")]

    rumpf = _ohne_kommentare(html)
    verstoesse: List[Verstoss] = []

    # ── R1: nichts, was den Besucher zu einem fremden Server schickt ──
    for tag in VERBOTENE_TAGS:
        if re.search(rf"<\s*{tag}\b", rumpf, re.IGNORECASE):
            verstoesse.append(Verstoss(
                "R1", f"<{tag}> ist nicht erlaubt — lädt oder führt Fremdes aus."))
    if EXTERNE_QUELLE.search(rumpf):
        verstoesse.append(Verstoss(
            "R1", "Externe Quelle in src. Bilder und Schriften gehören "
                  "mitgeliefert — sonst geht die IP des Besuchers an einen "
                  "fremden Server."))
    if CSS_IMPORT.search(rumpf):
        verstoesse.append(Verstoss("R1", "@import oder url(https://…) im CSS."))
    if EREIGNIS_ATTRIBUT.search(rumpf):
        verstoesse.append(Verstoss(
            "R1", "on…-Attribut gefunden. Verhalten im Markup ist im Editor "
                  "unsichtbar und übersteht das Bearbeiten nicht."))

    # ── R2: genau eine Wurzel, und die ist die Sektion ──
    baum = _Baum()
    try:
        baum.feed(rumpf)
    except Exception as e:  # noqa: BLE001 — kaputtes Markup ist selbst ein Verstoss
        return verstoesse + [Verstoss("R2", f"Markup nicht lesbar: {e}")]

    # Welches Tag die Wurzel ist, bleibt offen: Footer nutzen <footer>,
    # Navigation <nav>, ein Banner auch mal <a>. Entscheidend ist, dass es
    # genau eine gibt und sie sich zu erkennen gibt.
    if baum.wurzeln > 1:
        verstoesse.append(Verstoss(
            "R2", f"{baum.wurzeln} Wurzelelemente. Ein Block ist genau eine Sektion."))
    if slug and baum.wurzel_attrs.get("data-block") != slug:
        verstoesse.append(Verstoss(
            "R2", f'data-block fehlt oder passt nicht — erwartet "{slug}".'))

    # ── R3: Slots nach der Konvention der Bibliothek ──
    for roh in SLOT_FALSCH.findall(rumpf):
        if not SLOT.fullmatch("{{" + roh + "}}"):
            verstoesse.append(Verstoss(
                "R3", f'Slot "{roh}" passt nicht zur Konvention '
                      f"(kleinbuchstaben_mit_unterstrich)."))
    if slots is not None:
        bekannt = {s.get("key") for s in slots if isinstance(s, dict)}
        for name in slots_im_markup(rumpf):
            if name not in bekannt:
                verstoesse.append(Verstoss(
                    "R3", f'Slot "{name}" steht im Markup, aber nicht in den '
                          f"Slot-Angaben — generate-copy würde ihn nie füllen."))

    # ── R4: bedienbar im Editor ──
    if baum.max_tiefe > MAX_TIEFE:
        verstoesse.append(Verstoss(
            "R4", f"Verschachtelung {baum.max_tiefe} Ebenen tief (erlaubt "
                  f"{MAX_TIEFE}). Im Editor nicht mehr zu treffen."))
    if baum.ids:
        verstoesse.append(Verstoss(
            "R4", f"id-Attribut gefunden ({', '.join(baum.ids[:3])}). Steht der "
                  f"Block zweimal auf einer Seite, ist die id doppelt."))
    if FESTE_POSITION.search(rumpf):
        verstoesse.append(Verstoss(
            "R4", "position:fixed/sticky sprengt die Vorschau im Editor."))

    # ── R5: die Farbe kommt vom Kunden, nicht aus dem Block ──
    bunte_klassen, gesehen = [], set()
    for attribut in KLASSEN_ATTRIBUT.findall(rumpf):
        for klasse in attribut.split():
            if klasse not in gesehen and _bunter_ton(klasse):
                gesehen.add(klasse)
                bunte_klassen.append(klasse)
    if bunte_klassen:
        verstoesse.append(Verstoss(
            "R5", f"Feste Farbe im Markup: {', '.join(bunte_klassen[:5])}"
                  f"{' …' if len(bunte_klassen) > 5 else ''}. Der Wireframe "
                  f"bleibt grau — die Marke kommt aus dem Style-Guide und "
                  f"ersetzt die Graustufen."))

    stil_farben = []
    for attribut in STYLE_ATTRIBUT.findall(rumpf):
        stil_farben.extend(_bunte_farbwerte(attribut))
    if stil_farben:
        verstoesse.append(Verstoss(
            "R5", f"Farbe im style-Attribut: {', '.join(stil_farben[:3])}. "
                  f"Die laesst sich spaeter durch nichts ersetzen — sie steht "
                  f"beim Kunden genau so."))

    # Eine Überschrift je Block wird bewusst NICHT verlangt: Navigation,
    # Footer, Banner und Logo-Leisten haben zu Recht keine. Ob die
    # Überschriftenstruktur einer *Seite* stimmt, prüft der eigene
    # 38-Kriterien-Audit — das ist die richtige Ebene dafür.
    return verstoesse


def ist_konform(html: str, slug: str = "",
                slots: Optional[List[dict]] = None) -> bool:
    return not pruefe(html, slug, slots)


def als_text(verstoesse: List[Verstoss]) -> str:
    """Für Log und Fehlermeldung."""
    return " | ".join(str(v) for v in verstoesse)
