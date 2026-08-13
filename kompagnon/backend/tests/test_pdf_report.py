"""
PDF-Bericht auf Basis des überarbeiteten Kriterienkatalogs.

Der Generator war auf die früheren sechs Kategorien verdrahtet und verteilte
den Kategorie-Score proportional auf die Einzelkriterien — die Zeilenwerte im
PDF waren gerechnet, nicht gemessen. Diese Tests halten fest, dass beides
behoben bleibt.
"""
import json

import pytest

from services.audit_criteria import CATALOGUE, Source, all_criteria
from services.pdf_generator import (
    KatalogFehlt,
    _get_styles,
    build_scorecard,
    generate_audit_report,
)


def _volle_bewertung():
    items = {c.key: c.max_points for c in all_criteria()}
    sources = {c.key: Source.MEASURED.value for c in all_criteria()}
    return items, sources


def _zellentext(zelle):
    return getattr(zelle, "text", str(zelle))


# ── Bewertungsmatrix ──────────────────────────────────────────────────

def test_matrix_enthaelt_alle_kategorien_des_katalogs():
    items, sources = _volle_bewertung()
    _, rows = build_scorecard(items, sources, _get_styles())

    text = " ".join(_zellentext(z) for zeile in rows for z in zeile)
    for kategorie in CATALOGUE:
        assert kategorie.label in text, f"{kategorie.label} fehlt im PDF"


def test_matrix_hat_eine_zeile_je_kriterium():
    items, sources = _volle_bewertung()
    _, rows = build_scorecard(items, sources, _get_styles())

    # je Kategorie eine Kopfzeile plus je Kriterium eine Zeile
    assert len(rows) == len(CATALOGUE) + len(all_criteria())


def test_zeilenwerte_stammen_aus_der_einzelbewertung():
    """Der alte Generator hat den Kategorie-Score proportional verteilt."""
    items, sources = _volle_bewertung()
    items["rc_impressum"] = 3        # Teilpunktzahl, 6 wären möglich
    items["rc_datenschutz"] = 6

    _, rows = build_scorecard(items, sources, _get_styles())
    werte = {z[0]: z[4] for z in rows if isinstance(z[0], str) and z[0].startswith("RC-")}

    assert werte["RC-01"] == "3"
    assert werte["RC-02"] == "6"


def test_nicht_erhobene_kriterien_erscheinen_als_strich():
    items, sources = _volle_bewertung()
    sources["tp_inp"] = Source.NOT_COLLECTED.value
    items["tp_inp"] = 0

    _, rows = build_scorecard(items, sources, _get_styles())
    zeile = next(z for z in rows if isinstance(z[0], str) and z[0] == "TP-03")

    assert zeile[4] == "–"
    assert zeile[5] == "nicht erhoben"


def test_nicht_erhobene_kriterien_senken_das_kategorie_maximum():
    """Sonst sähe eine fehlende Messung im PDF wie ein Punktverlust aus."""
    items, sources = _volle_bewertung()
    sources["tp_inp"] = Source.NOT_COLLECTED.value
    items["tp_inp"] = 0

    _, rows = build_scorecard(items, sources, _get_styles())
    kopf = next(_zellentext(z[4]) for z in rows
                if "Performance" in _zellentext(z[0]))

    assert "13" in kopf   # 15 Punkte minus die 2 von INP


def test_quellenangabe_steht_in_jeder_zeile():
    items, sources = _volle_bewertung()
    sources["dg_aktualitaet"] = Source.AI.value

    _, rows = build_scorecard(items, sources, _get_styles())
    zeile = next(z for z in rows if isinstance(z[0], str) and z[0] == "DG-01")

    assert zeile[2] == "KI"


# ── Gesamtdokument ────────────────────────────────────────────────────

@pytest.fixture
def audit_daten():
    items, sources = _volle_bewertung()
    return {
        "total_score": 100, "level": "Homepage Standard Platin", "coverage": 100,
        "company_name": "Muster GmbH", "website_url": "https://muster.de",
        "trade": "Heizung", "city": "Bochum", "created_at": None,
        "ai_summary": "Sehr gute Website.",
        "top_issues": json.dumps(["Kein Problem gefunden"]),
        "recommendations": json.dumps(["Weiter so"]),
        "item_scores": json.dumps(items),
        "item_sources": json.dumps(sources),
        "category_scores": json.dumps([
            {"key": c.key, "label": c.label, "score": c.max_points,
             "max": c.max_points, "nominal_max": c.max_points, "not_collected": []}
            for c in CATALOGUE
        ]),
        "blockers": json.dumps([]),
    }


def test_pdf_wird_erzeugt(audit_daten):
    pdf = generate_audit_report(audit_daten)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 20_000


def test_pdf_mit_blockern_wird_erzeugt(audit_daten):
    audit_daten["blockers"] = json.dumps(["kein_impressum", "tracking_ohne_consent"])
    pdf = generate_audit_report(audit_daten)
    assert pdf.startswith(b"%PDF")


def test_altbestand_wird_abgelehnt_statt_nullen_zu_drucken():
    """Audits aus dem früheren Katalog haben keine Einzelwerte."""
    with pytest.raises(KatalogFehlt):
        generate_audit_report({"total_score": 46, "level": "Nicht konform",
                               "company_name": "Alt GmbH"})


# ── Was der erste echte Bericht zutage gefoerdert hat ─────────────────

def test_ohne_keyword_daten_gibt_es_kein_diagramm():
    """Sonst stehen erfundene Zahlen im Bericht.

    Der Ring zeichnete ohne Daten vier gleich grosse Viertel und schrieb an
    jedes „25 %". Der Empfänger liest daraus eine Verteilung seiner Keywords —
    bei einem Audit, das Keyword-Positionen überhaupt nicht erhebt.
    """
    from services.pdf_generator import generate_donut_chart

    assert generate_donut_chart({}) is None
    assert generate_donut_chart({"top10": 0, "11_20": 0}) is None


def test_mit_keyword_daten_entsteht_ein_diagramm():
    from services.pdf_generator import generate_donut_chart

    png = generate_donut_chart({"top10": 3, "11_20": 1, "21_50": 4, "51_100": 2})
    assert png and png.startswith(b"\x89PNG")


def test_statusspalte_nennt_den_status_im_klartext():
    """„O", „+" und „-" waren selbst mit Legende nicht zu deuten.

    Haken und Kreuz scheiden aus: die Schriftregistrierung sucht DejaVu,
    reportlab liefert das nicht mehr mit, und Helvetica kennt die Zeichen
    nicht — sie kaemen als leere Kaestchen.
    """
    from services.pdf_generator import STATUS_ZEICHEN, _score_status

    assert _score_status(10, 10) == STATUS_ZEICHEN["konform"]
    assert _score_status(5, 10) == STATUS_ZEICHEN["teilweise"]
    assert _score_status(1, 10) == STATUS_ZEICHEN["offen"]
    for zeichen in STATUS_ZEICHEN.values():
        assert len(zeichen) > 1, f"{zeichen!r} ist wieder ein Einzelzeichen"


def test_pdf_traegt_die_ci_und_nicht_die_alte_palette():
    """Geprüft wird der Code, nicht die Kommentare.

    Die alten Werte stehen bewusst noch in Kommentaren und Docstrings, damit
    nachvollziehbar bleibt, was ersetzt wurde. Ein simpler Textvergleich würde
    genau daran hängenbleiben, deshalb werden Kommentare und Zeichenketten
    vorher herausgeschnitten.
    """
    import io
    import tokenize

    from services import brand
    from services import pdf_generator

    assert pdf_generator.KC_DARK.hexval()[2:].upper() == brand.DARK[1:]

    quelle = open(pdf_generator.__file__, encoding="utf-8").read()
    code = []
    for tok in tokenize.generate_tokens(io.StringIO(quelle).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        code.append(tok.string)
    code = " ".join(code)

    for erfunden in ("#2c3e50", "#f39c12", "#e74c3c", "#27ae60", "#7f8c8d",
                     "#95a5a6", "#64748b"):
        assert erfunden not in code, f"{erfunden} steht wieder im Code"


def test_die_fusszeile_datiert_sich_nach_dem_audit():
    """Hier stand fest die Jahreszahl — auf jeder Seite jedes Berichts.

    Geprüft wird, was die Fußzeile tatsächlich zeichnet, nicht der Quelltext.
    """
    from services.pdf_generator import _footer

    gezeichnet = []

    class _CanvasAttrappe:
        def saveState(self): pass
        def restoreState(self): pass
        def setFont(self, *a): pass
        def setFillColor(self, *a): pass
        def setStrokeColor(self, *a): pass
        def setLineWidth(self, *a): pass
        def line(self, *a): pass
        def drawString(self, x, y, text): gezeichnet.append(text)
        def drawRightString(self, x, y, text): gezeichnet.append(text)

    class _DocAttrappe:
        page = 3
        kc_jahr = 2027

    _footer(_CanvasAttrappe(), _DocAttrappe())

    assert any("Audit 2027" in t for t in gezeichnet), gezeichnet
    assert any("Seite 3" in t for t in gezeichnet), gezeichnet


# ── Schrift und Zeichenabdeckung ──────────────────────────────────────

def test_die_ci_schrift_wird_benutzt():
    """Noto Sans liegt im Repo und muss auch ankommen.

    Vorher suchte die Registrierung DejaVu, das reportlab 4 nicht mehr
    mitliefert — sie lief jedes Mal in den Fehlerzweig, und jedes PDF war
    still in Helvetica gesetzt.
    """
    from services import pdf_generator

    assert pdf_generator.FONT_NORMAL == "NotoSans"
    assert pdf_generator.FONT_BOLD == "NotoSans-Bold"


def test_zeichen_ohne_glyphe_werden_ersetzt_statt_zu_verschwinden():
    """Ein fehlendes Zeichen hinterlaesst im PDF eine Luecke, keine Warnung.

    „HTTP→HTTPS erzwungen" steht so im Kriterienkatalog. Weder Noto Sans noch
    Helvetica kennen den Pfeil — ohne Ersatz stand dort „HTTPHTTPS".
    """
    from services.pdf_generator import _clean_text

    assert _clean_text("HTTP→HTTPS erzwungen") == "HTTP->HTTPS erzwungen"
    assert _clean_text("Score ≥ 80") == "Score >= 80"
    assert "✓" not in _clean_text("erledigt ✓")


def test_kitext_mit_emoji_zerstoert_das_pdf_nicht():
    """Zusammenfassung und Empfehlungen kommen aus der KI.

    Dort kann jedes Zeichen auftauchen; keines davon darf als Luecke oder
    Fehler im Bericht landen.
    """
    from services.pdf_generator import _clean_text

    sauber = _clean_text("Ihre Seite 🚀 ist schnell")
    assert "🚀" not in sauber
    assert "Ihre Seite" in sauber and "ist schnell" in sauber


def test_normaler_deutscher_text_bleibt_unveraendert():
    from services.pdf_generator import _clean_text

    for probe in ("Größe – Maß · 98 %", "„Anführung“", "Straße, Grün, Öl"):
        assert _clean_text(probe) == probe
