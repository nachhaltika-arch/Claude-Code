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
