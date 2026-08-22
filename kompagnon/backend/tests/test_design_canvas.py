"""Der Design-Canvas: Hinweg, Rueckweg und die Stellen, an denen er nichts tut.

Der Rueckweg ist der gefaehrliche. Er schreibt in `sitemap_pages.mockup_html`
— das Markup, das spaeter ausgeliefert wird. Ein Import, der die falsche Seite
trifft oder eine Seite leert, ist kein Anzeigefehler, sondern Datenverlust beim
Kunden. Deshalb hat jeder Fall, in dem `uebernimm` bewusst **nichts** tut,
hier einen eigenen Test.
"""
import json

from services.canvas_artboards import (
    artboard,
    entschaerfe,
    markup_aus_artboard,
    verschaerfe,
)
from services.canvas_ansichten import (
    design_artboard,
    sitemap_artboard,
    styleguide_artboard,
    wireframe_artboard,
)
from services.design_canvas import SEITEN, baue, uebernimm


class _Lead:
    """Nur die Felder, die `baue` liest — kein ORM noetig fuer eine Uebersetzung."""

    def __init__(self, **felder):
        self.company_name = "Muster Heizung GmbH"
        self.brand_guideline_json = None
        self.brand_design_tokens_json = None
        self.brand_primary_color = None
        self.brand_secondary_color = None
        self.brand_font_heading = None
        self.brand_font_primary = None
        self.brand_font_body = None
        self.brand_font_secondary = None
        self.brand_font_accent = None
        for k, v in felder.items():
            setattr(self, k, v)


class _Project:
    def __init__(self, wireframe_data=None):
        self.wireframe_data = wireframe_data


def _seite(kennung, name, **rest):
    grund = {"id": kennung, "parent_id": None, "position": kennung,
             "page_name": name, "page_type": "info", "zweck": None,
             "ziel_keyword": None, "cta_text": None, "cta_ziel": "kontakt",
             "status": "geplant", "mockup_html": None}
    grund.update(rest)
    return grund


# ── Hin und zurueck ──────────────────────────────────────────────────────────

def test_rumpf_kommt_unveraendert_zurueck():
    # Arrange
    roh = '<section class="hero"><h1>Wärme, die sich rechnet</h1></section>'

    # Act
    zurueck = verschaerfe(markup_aus_artboard(artboard(stil="", inhalt=roh)))

    # Assert
    assert zurueck == roh


def test_offener_slot_ueberlebt_die_runde():
    """`{{headline}}` ist im Werkzeug ein sichtbarer Hinweis, im Canvas eine
    Bindung an nichts. Er wird zur gelben Luecke — und muss als Marker
    zurueckkommen, sonst steht der gelbe Kasten spaeter auf der Kundenseite."""
    roh = "<h1>{{headline}}</h1>"

    hin = artboard(stil="", inhalt=roh)

    assert "{{headline}}" not in hin
    assert 'data-kompagnon-slot="headline"' in hin
    assert verschaerfe(markup_aus_artboard(hin)) == roh


def test_gefuellter_slot_bleibt_gefuellt():
    """Wer im Canvas ueber die Luecke schreibt, hat den Slot gefuellt. Die
    Ruecknahme darf daraus nicht wieder einen leeren Marker machen."""
    hin = artboard(stil="", inhalt="<h1>{{headline}}</h1>")
    bearbeitet = hin.replace(
        [z for z in hin.split("\n") if "data-kompagnon-slot" in z][0],
        "<h1>Wärme, die sich rechnet</h1>",
    )

    assert verschaerfe(markup_aus_artboard(bearbeitet)) == "<h1>Wärme, die sich rechnet</h1>"


def test_beendende_zeichenfolge_sprengt_das_artboard_nicht():
    """Kundenmarkup kommt aus der KI-Generierung und aus GrapesJS. Ein
    `</x-dc>` darin wuerde die Datei mittendrin schliessen."""
    roh = "<p>a </x-dc> b</p>"

    hin = artboard(stil="", inhalt=roh)

    assert hin.count("</x-dc>") == 1          # nur das echte Ende
    assert verschaerfe(markup_aus_artboard(hin)) == roh


def test_fremde_datei_hat_keinen_rumpf():
    """Kein Rumpf heisst ``None``, nicht ``""`` — ein leerer String wuerde beim
    Import als „die Seite ist jetzt leer" gelesen."""
    assert markup_aus_artboard("<html><body>irgendwas</body></html>") is None
    assert markup_aus_artboard("") is None
    assert markup_aus_artboard(None) is None


def test_leeres_markup_bleibt_leer():
    assert entschaerfe(None) == ""
    assert verschaerfe(None) == ""


# ── Die vier Ansichten ───────────────────────────────────────────────────────

def test_sitemap_verschachtelt_nach_elternseite():
    seiten = [
        _seite(1, "Startseite"),
        _seite(2, "Wärmepumpe", parent_id=1),
        _seite(3, "Kontakt"),
    ]

    quelle = sitemap_artboard(betrieb="Muster GmbH", seiten=seiten)

    # Die Kindseite ist eingerueckt, die beiden Elternseiten nicht.
    assert "margin-left: 32px" in quelle
    assert quelle.count("margin-left: 0px") == 2
    assert "Wärmepumpe" in quelle


def test_sitemap_ohne_seiten_sagt_es():
    quelle = sitemap_artboard(betrieb="Muster GmbH", seiten=[])

    assert "noch keine\nSitemap" in quelle or "noch keine Sitemap" in quelle


def test_seitenname_wird_nicht_zu_markup():
    """Seitennamen kommen aus der KI-Generierung und aus Nutzereingaben."""
    quelle = sitemap_artboard(
        betrieb="Muster GmbH",
        seiten=[_seite(1, '<script>alert(1)</script>')],
    )

    assert "<script>alert(1)</script>" not in quelle
    assert "&lt;script&gt;" in quelle


def test_wireframe_haelt_die_reihenfolge():
    bloecke = [
        {"slug": "cta-abschluss", "order": 2, "slots": {}},
        {"slug": "hero-split", "order": 0, "slots": {"headline": "Wärme"}},
        {"slug": "leistungen", "order": 1, "slots": {}},
    ]

    quelle = wireframe_artboard(seitenname="Startseite", bloecke=bloecke)

    assert (quelle.index("hero-split") < quelle.index("leistungen")
            < quelle.index("cta-abschluss"))


def test_wireframe_ohne_bloecke_sagt_es():
    quelle = wireframe_artboard(seitenname="Kontakt", bloecke=[])

    assert "noch kein Wireframe" in quelle


def test_styleguide_erfindet_keine_markenfarbe():
    """Eine erfundene Farbe landet ueber den Canvas auf einer Kundenseite."""
    quelle = styleguide_artboard(betrieb="Muster GmbH", marke={})

    assert "noch keine Markenfarben" in quelle
    assert "noch keine Schriften" in quelle


def test_styleguide_zeigt_die_hinterlegten_farben():
    quelle = styleguide_artboard(
        betrieb="Muster GmbH",
        marke={
            "farben": {"primary": "#C0392B", "accent": "#FAE600"},
            "schriften": {"heading": "Playfair Display", "body": "Noto Sans"},
            "radius": 12,
            "quelle": "Style-Guide des Projekts",
        },
    )

    assert "#C0392B" in quelle
    assert "Playfair Display" in quelle
    assert "border-radius: 12px" in quelle
    assert "fonts.googleapis.com" in quelle


def test_styleguide_nennt_seine_quelle():
    """Ein Style-Guide aus dem Scrape der alten Seite sieht aus wie einer, der
    entschieden wurde. Nur die Herkunft zeigt den Unterschied."""
    quelle = styleguide_artboard(
        betrieb="Muster GmbH",
        marke={"farben": {"primary": "#111"}, "schriften": {},
               "quelle": "Markenfarben aus dem Scrape"},
    )

    assert "Quelle: Markenfarben aus dem Scrape" in quelle


def test_design_ohne_markup_nennt_den_naechsten_schritt():
    quelle = design_artboard(seitenname="Kontakt", markup=None, schriften={})

    assert "noch kein Design" in quelle


# ── Der ganze Canvas ─────────────────────────────────────────────────────────

def test_jedes_artboard_der_anordnung_hat_eine_datei():
    """Die Anordnung darf keine Datei nennen, die es nicht gibt — der Editor
    haengt sonst ein leeres Artboard an."""
    ergebnis = baue(
        lead=_Lead(),
        seiten=[_seite(7, "Startseite"), _seite(9, "Kontakt")],
        project=_Project([{"page_id": 7, "blocks": [{"slug": "hero", "order": 0}]}]),
    )

    genannt = {a["file"] for a in ergebnis["canvas"]["artboards"]}
    assert genannt == set(ergebnis["files"])
    assert "Main.dc.html" in ergebnis["files"]


def test_dateiname_traegt_die_seitenkennung_nicht_die_position():
    """Wer zwischen Ausgabe und Ruecknahme eine Seite einfuegt, wuerde bei
    positionsbasierten Namen das Design der einen Seite auf eine andere
    schreiben."""
    ergebnis = baue(lead=_Lead(), seiten=[_seite(7, "Startseite"), _seite(9, "Kontakt")])

    assert "Design7.dc.html" in ergebnis["files"]
    assert "Design9.dc.html" in ergebnis["files"]
    assert "Wireframe7.dc.html" in ergebnis["files"]


def test_anordnung_ist_gueltig():
    """Was der Editor verwirft, faellt still weg — deshalb hier gemessen:
    jede genannte Seite ist gelistet, und der Einstieg zeigt auf eine davon."""
    ergebnis = baue(lead=_Lead(), seiten=[_seite(1, "Startseite")])
    canvas = ergebnis["canvas"]

    kennungen = {s["id"] for s in canvas["pages"]}
    assert kennungen == {s["id"] for s in SEITEN}
    assert all(a["page"] in kennungen for a in canvas["artboards"])
    assert canvas["launch"]["page"] in kennungen
    assert canvas["launch"]["view"] == "canvas"
    # Muss serialisierbar sein — es wird als Datei mitgegeben.
    json.dumps(canvas)


def test_artboard_namen_sind_eindeutig():
    """Der Editor unterscheidet Artboards am Namen, ohne Ruecksicht auf Gross-
    und Kleinschreibung."""
    ergebnis = baue(lead=_Lead(), seiten=[_seite(1, "Start"), _seite(2, "Start")])

    stamm = [n.lower() for n in ergebnis["files"]]
    assert len(stamm) == len(set(stamm))


def test_marke_zieht_die_guideline_den_rohen_tokens_vor():
    lead = _Lead(
        brand_design_tokens_json=json.dumps({"primary": "#111111", "font_body": "Arial"}),
        brand_guideline_json=json.dumps({"tokens": {"primary": "#C0392B"}}),
    )

    quelle = baue(lead=lead, seiten=[])["files"]["Styleguide.dc.html"]

    assert "#C0392B" in quelle
    assert "#111111" not in quelle
    assert "Arial" in quelle          # was die Guideline nicht nennt, bleibt


def test_style_guide_des_projekts_schlaegt_die_marke_des_leads():
    """Die entschiedene Marke gewinnt gegen die gescrapte.

    `leads.brand_*` ist der Stand der **alten** Kundenseite. Wer den zeigt,
    obwohl im Projekt ein Style-Guide entschieden wurde, zeigt den Stand vor
    der Arbeit — und die Design-Artboards daneben zeigen etwas anderes."""
    lead = _Lead(brand_guideline_json=json.dumps({"tokens": {"primary": "#111111"}}))
    project = _Project({"pages": [], "style_guide": {"colors": {"primary": "#C0392B"}}})

    quelle = baue(lead=lead, seiten=[], project=project)["files"]["Styleguide.dc.html"]

    assert "#C0392B" in quelle
    assert "#111111" not in quelle
    assert "Quelle: Style-Guide des Projekts" in quelle


def test_style_guide_kennt_beide_schreibweisen():
    """`StyleGuideView` schreibt `colors`, aeltere Zeilen und der E2E-Seed
    `palette`. Beides ist dieselbe Sache."""
    for schluessel in ("colors", "palette"):
        project = _Project({"pages": [], "style_guide": {schluessel: {"primary": "#C0392B"}}})
        quelle = baue(lead=_Lead(), seiten=[], project=project)["files"]["Styleguide.dc.html"]
        assert "#C0392B" in quelle, schluessel


def test_wireframe_wird_auch_als_objekt_gelesen():
    """Der Router speichert `{"pages": [...]}`, die Spaltenvorgabe ist eine
    Liste, aeltere Zeilen halten JSON als Text. Eine erste Fassung kannte nur
    die Liste — und haette bei jedem Projekt mit echtem Wireframe „noch kein
    Wireframe" angezeigt."""
    block = [{"slug": "hero-standard", "order": 0, "slots": {}}]
    formen = [
        {"pages": [{"page_id": 1, "blocks": block}]},
        [{"page_id": 1, "blocks": block}],
        json.dumps({"pages": [{"page_id": 1, "blocks": block}]}),
    ]

    for form in formen:
        ergebnis = baue(lead=_Lead(), seiten=[_seite(1, "Start")], project=_Project(form))
        assert "hero-standard" in ergebnis["files"]["Wireframe1.dc.html"], form


def test_kaputtes_wireframe_json_verhindert_den_canvas_nicht():
    """`wireframe_data` ist JSONB und wurde ueber Jahre von mehreren Stellen
    beschrieben. Ein unerwarteter Inhalt ist kein Grund, gar nichts zu
    liefern."""
    ergebnis = baue(lead=_Lead(), seiten=[_seite(1, "Start")],
                    project=_Project({"kein": "listeneintrag"}))

    assert "noch kein Wireframe" in ergebnis["files"]["Wireframe1.dc.html"]


# ── Der Rueckweg ─────────────────────────────────────────────────────────────

def test_uebernimmt_das_bearbeitete_design():
    dateien = {"Design5.dc.html": artboard(stil="", inhalt="<h1>Neu</h1>")}

    ergebnis = uebernimm(dateien=dateien, seiten_nach_id={5: object()})

    assert ergebnis == [{"page_id": 5, "markup": "<h1>Neu</h1>"}]


def test_fremder_betrieb_schreibt_nichts():
    """Ein Canvas eines anderen Kunden darf hier nichts hinterlassen."""
    dateien = {"Design5.dc.html": artboard(stil="", inhalt="<h1>Neu</h1>")}

    assert uebernimm(dateien=dateien, seiten_nach_id={9: object()}) == []


def test_die_anderen_drei_ansichten_schreiben_nichts():
    """Sitemap, Wireframe und Style-Guide sind im Canvas bearbeitbar — aber
    ihr Ziel ist nicht `mockup_html`. Sie hier zu uebernehmen hiesse, einen
    Wireframe als Kundenseite auszuliefern."""
    dateien = {
        "Main.dc.html": artboard(stil="", inhalt="<p>Baum</p>"),
        "Wireframe5.dc.html": artboard(stil="", inhalt="<p>Geruest</p>"),
        "Styleguide.dc.html": artboard(stil="", inhalt="<p>Farben</p>"),
        "canvas.json": "{}",
    }

    assert uebernimm(dateien=dateien, seiten_nach_id={5: object()}) == []


def test_leeres_artboard_loescht_keine_seite():
    """Eine Seite zu leeren ist ein Loeschvorgang und passiert nicht aus
    Versehen ueber einen Import."""
    dateien = {"Design5.dc.html": artboard(stil="", inhalt="")}

    assert uebernimm(dateien=dateien, seiten_nach_id={5: object()}) == []


def test_datei_ohne_markierung_wird_uebergangen():
    dateien = {"Design5.dc.html": "<html><body>von woanders</body></html>"}

    assert uebernimm(dateien=dateien, seiten_nach_id={5: object()}) == []


def test_leere_eingabe_ist_kein_fehler():
    assert uebernimm(dateien={}, seiten_nach_id={}) == []
    assert uebernimm(dateien=None, seiten_nach_id={}) == []
