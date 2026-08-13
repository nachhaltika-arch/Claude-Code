"""
Der Vertrag für Bibliotheksblöcke.

Der wichtigste Test steht ganz oben: Die 41 vorhandenen Blöcke müssen ihn
bestehen. Ein Vertrag, den die eigene Bibliothek verletzt, ist kein Maßstab
für erzeugtes Markup, sondern eine Erfindung.
"""
from pathlib import Path

import pytest

from services.block_contract import (
    MAX_TIEFE,
    ist_konform,
    pruefe,
    slots_im_markup,
)

BIBLIOTHEK = (Path(__file__).resolve().parents[2]
              / "frontend" / "src" / "components" / "library")


def _bloecke():
    return sorted(BIBLIOTHEK.glob("*.html")) if BIBLIOTHEK.is_dir() else []


# ── Der Maßstab: die echte Bibliothek ─────────────────────────────────

def test_die_bibliothek_ist_nicht_leer():
    """Sonst prüft der Test unten nichts und wirkt trotzdem grün."""
    if not BIBLIOTHEK.is_dir():
        pytest.skip("Frontend nicht vorhanden")
    assert len(_bloecke()) >= 20, f"Nur {len(_bloecke())} Blöcke gefunden"


# Bekannte Schuld, bewusst offen gehalten statt den Vertrag aufzuweichen.
#
# Beide Blöcke betten Google Maps per <iframe> ein. Das überträgt die
# IP-Adresse jedes Besuchers an Google, bevor er irgendetwas angeklickt hat —
# und ist damit genau der K.-o.-Grund, den unser eigener Kriterienkatalog
# `tracking_ohne_consent` nennt („Tracking oder externe Dienste ohne
# Einwilligung"). Jede Kundenseite mit einem dieser Blöcke fällt bei unserer
# eigenen Prüfung durch.
#
# Auflösung: statische Kartengrafik oder Karte erst nach Einwilligung laden.
# Wer das behebt, streicht den Eintrag hier — dann greift die Regel wieder.
BEKANNTE_SCHULD = {
    "hw-karte": "Google-Maps-iframe — überträgt Besucher-IP ohne Einwilligung",
    "seo-lokal": "Google-Maps-iframe — überträgt Besucher-IP ohne Einwilligung",
    # Gefunden beim Messen für R5: Der Hero legt ein Overlay in
    # rgba(0,79,89,0.78) über sein Hintergrundbild — das ist KOMPAGNON-Teal,
    # fest im Markup. Auf einer Kundenseite bleibt es teal, egal welche Marke
    # der Style-Guide vorgibt; kein Override kann ein style-Attribut umbiegen.
    # Auflösung: Overlay in Graustufe oder als Klasse, die der Marken-Override
    # kennt.
    "hero-centered": "Marken-Farbe rgba(0,79,89) fest im style-Attribut",
}


@pytest.mark.parametrize("datei", _bloecke(), ids=lambda p: p.stem)
def test_jeder_vorhandene_block_erfuellt_den_vertrag(datei):
    """Was von Hand gebaut wurde, muss der Maßstab für Erzeugtes sein."""
    html = datei.read_text(encoding="utf-8")
    verstoesse = pruefe(html, slug=datei.stem)

    if datei.stem in BEKANNTE_SCHULD:
        assert verstoesse, (
            f"{datei.stem} ist offenbar behoben — bitte aus BEKANNTE_SCHULD "
            f"streichen, damit die Regel wieder greift.")
        pytest.xfail(BEKANNTE_SCHULD[datei.stem])

    assert not verstoesse, "\n".join(str(v) for v in verstoesse)


# ── Die einzelnen Regeln ──────────────────────────────────────────────

GUT = """<section data-block="probe" class="py-16">
  <h2 class="text-3xl">{{section_headline}}</h2>
  <p>{{section_text}}</p>
</section>"""


def test_ein_sauberer_block_hat_keine_verstoesse():
    assert ist_konform(GUT, slug="probe")


@pytest.mark.parametrize("markup,regel", [
    ('<section data-block="p"><h2>x</h2><script>alert(1)</script></section>', "R1"),
    ('<section data-block="p"><h2>x</h2><img src="https://fremd.de/a.png"></section>', "R1"),
    ('<section data-block="p"><h2>x</h2><div onclick="tu()">a</div></section>', "R1"),
    ('<section data-block="p"><h2>x</h2></section><section><h2>y</h2></section>', "R2"),
    ('<section data-block="p"><h2>{{Falscher-Slot}}</h2></section>', "R3"),
    ('<section data-block="p"><h2 id="held">x</h2></section>', "R4"),
    ('<section data-block="p" style="position:fixed"><h2>x</h2></section>', "R4"),
])
def test_verstoesse_werden_erkannt(markup, regel):
    verstoesse = pruefe(markup, slug="p")
    assert any(v.regel == regel for v in verstoesse), \
        f"{regel} nicht erkannt — gefunden: {[v.regel for v in verstoesse]}"


# ── R5: die Marken-Bindung ────────────────────────────────────────────
#
# Gemessen, bevor die Regel scharf geschaltet wurde: Die 45 Blöcke der
# Bibliothek benutzen ausschließlich Graustufen — 298× `gray`, 222× `slate`,
# dazu `white`, `black`, `transparent`. Kein einziger bunter Ton, und in der
# Datenbank-Bibliothek (96 Blöcke) ebenso wenig. Genau das ist die Regel:
# Farbe kommt aus dem Style-Guide des Kunden, nicht aus dem Block.

@pytest.mark.parametrize("klasse", [
    "bg-blue-500", "text-emerald-600", "border-red-300", "from-indigo-900",
    "ring-amber-400", "divide-teal-200", "hover:bg-rose-500",
    "md:text-violet-700", "!bg-lime-400", "ring-offset-sky-500",
])
def test_ein_bunter_ton_verletzt_die_markenbindung(klasse):
    markup = f'<section data-block="p" class="{klasse}"><h2>x</h2></section>'
    verstoesse = pruefe(markup, slug="p")
    assert any(v.regel == "R5" for v in verstoesse), \
        f"{klasse} durchgelassen — gefunden: {[str(v) for v in verstoesse]}"


@pytest.mark.parametrize("klasse", [
    "bg-white", "bg-gray-50", "text-slate-600", "border-zinc-200",
    "bg-neutral-100", "text-stone-700", "bg-white/10", "from-gray-900/95",
    "to-transparent", "text-black", "outline-none", "bg-gradient-to-t",
    "text-3xl", "border-t-4", "shadow-md", "text-[11px]", "w-[32px]",
    "rounded-2xl", "hover:bg-slate-100", "md:text-gray-500",
])
def test_graustufen_und_groessen_bleiben_erlaubt(klasse):
    """Der Wireframe ist grau — und Größen sind keine Farben."""
    markup = f'<section data-block="p" class="{klasse}"><h2>x</h2></section>'
    verstoesse = [v for v in pruefe(markup, slug="p") if v.regel == "R5"]
    assert not verstoesse, f"{klasse} fälschlich beanstandet: {verstoesse}"


@pytest.mark.parametrize("klasse", ["bg-[#004F59]", "text-[rgb(0,79,89)]",
                                    "border-[hsl(190,100%,20%)]"])
def test_ein_eigener_farbwert_in_der_klasse_verletzt_die_markenbindung(klasse):
    markup = f'<section data-block="p" class="{klasse}"><h2>x</h2></section>'
    assert any(v.regel == "R5" for v in pruefe(markup, slug="p"))


def test_eine_farbe_im_style_attribut_verletzt_die_markenbindung():
    """Das ist der schlimmere Fall: Ein style-Attribut kann kein Override
    umbiegen — die Farbe steht beim Kunden so, wie sie im Block steht."""
    markup = ('<section data-block="p" style="background: '
              'linear-gradient(rgba(0,79,89,0.78), rgba(0,79,89,0.78));">'
              '<h2>x</h2></section>')
    assert any(v.regel == "R5" for v in pruefe(markup, slug="p"))


@pytest.mark.parametrize("stil", [
    "font-family: 'Noto Sans', sans-serif;",          # 44× in der Bibliothek
    "background: rgba(255,255,255,0.15);",            # weißes Overlay
    "color: #333;",
    "border-color: #8a8a8aee;",                       # Graustufe mit Deckkraft
])
def test_graustufen_und_schrift_im_style_attribut_bleiben_erlaubt(stil):
    markup = f'<section data-block="p" style="{stil}"><h2>x</h2></section>'
    verstoesse = [v for v in pruefe(markup, slug="p") if v.regel == "R5"]
    assert not verstoesse, f"{stil} fälschlich beanstandet: {verstoesse}"


def test_auch_ein_getoenter_neutralton_im_style_attribut_wird_beanstandet():
    """Bewusst streng: `#e2e8f0` ist slate-200, also ein Blaustich — als Klasse
    in Ordnung, im style-Attribut nicht. Der Unterschied ist nicht die Farbe,
    sondern dass die Klasse ersetzbar ist und das Attribut nicht."""
    markup = ('<section data-block="p" style="border-color: #e2e8f0;">'
              '<h2>x</h2></section>')
    assert any(v.regel == "R5" for v in pruefe(markup, slug="p"))


def test_eine_farbe_im_kommentar_zaehlt_nicht():
    """Zwei Navigationen nennen die Markenfarben in einem Kommentar."""
    markup = ('<section data-block="p">'
              '<!-- Brand-Farben: #004F59 (dark), #FAE600 (accent) -->'
              '<h2>x</h2></section>')
    assert not [v for v in pruefe(markup, slug="p") if v.regel == "R5"]


def test_hero_darf_die_hauptueberschrift_tragen():
    """Ein Hero *ist* die h1 seiner Seite — die halbe Bibliothek macht das."""
    assert ist_konform('<section data-block="p"><h1>Titel</h1></section>', slug="p")


def test_ein_link_nach_draussen_ist_erlaubt():
    """wa.me, Google Maps, Telefon — anklickbare Ziele sind keine Ressourcen."""
    markup = ('<a data-block="p" href="https://wa.me/49123"><span>Schreiben</span></a>')
    assert ist_konform(markup, slug="p")


def test_ein_block_ohne_ueberschrift_ist_erlaubt():
    """Navigation, Footer und Banner haben zu Recht keine.

    Ob die Überschriftenstruktur einer Seite stimmt, prüft der eigene
    38-Kriterien-Audit — das ist die richtige Ebene.
    """
    assert ist_konform('<nav data-block="p"><a href="/x">Start</a></nav>', slug="p")


def test_externe_schrift_wird_abgewiesen():
    """Dieselbe Regel wie im Widget: keine IP an einen fremden Server."""
    markup = ('<section data-block="p"><h2>x</h2>'
              '<style>@import url(https://fonts.googleapis.com/css?f=X);</style>'
              '</section>')
    assert any(v.regel == "R1" for v in pruefe(markup, slug="p"))


def test_falscher_slug_faellt_auf():
    """Ohne data-block findet der Editor den Block nicht wieder."""
    assert any(v.regel == "R2" for v in pruefe(GUT, slug="anderer-name"))


def test_zu_tiefe_verschachtelung_faellt_auf():
    innen = "<div>" * (MAX_TIEFE + 2) + "tief" + "</div>" * (MAX_TIEFE + 2)
    markup = f'<section data-block="p"><h2>x</h2>{innen}</section>'
    assert any(v.regel == "R4" for v in pruefe(markup, slug="p"))


def test_slot_ohne_angabe_faellt_auf():
    """generate-copy füllt nur, was in den Slot-Angaben steht."""
    verstoesse = pruefe(GUT, slug="probe",
                        slots=[{"key": "section_headline"}])
    assert any(v.regel == "R3" and "section_text" in v.text for v in verstoesse)


def test_slots_werden_in_reihenfolge_und_ohne_dubletten_gelesen():
    markup = ('<section data-block="p"><h2>{{a}}</h2><p>{{b}}</p>'
              '<p>{{a}}</p></section>')
    assert slots_im_markup(markup) == ["a", "b"]


def test_kommentare_zaehlen_nicht_mit():
    """Die Bibliothek dokumentiert ihre Slots im Kopfkommentar."""
    markup = ('<!-- Slots: {{Nicht-Konform}} und <script> -->\n' + GUT)
    assert ist_konform(markup, slug="probe")


def test_leerer_block_ist_kein_block():
    assert any(v.regel == "R0" for v in pruefe("   "))
