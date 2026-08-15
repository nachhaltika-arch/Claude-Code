"""Die letzten drei Kriterien, die überall dasselbe gemessen haben.

`PROFILE` sagt für K4 und K5 ausdrücklich „ein Ort wird NICHT erwartet",
verlangt je Klasse einen anderen Schema-Haupttyp und für den Kontakt einmal
Sprechzeiten, einmal Öffnungszeiten mit Anfahrt, einmal den Retourenweg.
Gerechnet wurde bis hierhin dreimal dasselbe: Ort im Title, `LocalBusiness`,
Telefon plus schlankes Formular plus Reaktionszeit.
"""
from bs4 import BeautifulSoup

from services.audit_collectors import analyse_contact
from services.audit_scoring import score_audit


def _punkte(kriterium: str, klasse: str, **fakten) -> int:
    return score_audit(fakten, {"branchenklasse": klasse})["items"][kriterium]


def _qa(**overrides) -> dict:
    qa = {
        "title_vorhanden": True, "title_laenge_ok": True,
        "title_text": "Muster GmbH — Heizung und Bad in Bochum",
        "meta_desc_vorhanden": True, "meta_desc_laenge_ok": True,
        "h1_genau_eins": True, "h2_vorhanden": True, "h1_text": "Heizung Bochum",
        "robots_txt": True, "robots_txt_indexiert": True, "sitemap_xml": True,
        "canonical_vorhanden": True, "schema_markup": True,
        "schema_typen": ["localbusiness"], "google_maps": True,
    }
    qa.update(overrides)
    return qa


def _kontakt(html: str) -> dict:
    return analyse_contact(BeautifulSoup(html, "html.parser"))


# ── Title & Meta: der Ort gilt nicht überall ──────────────────────────

def test_der_ort_im_title_zaehlt_beim_lokalen_betrieb():
    assert _punkte("se_meta", "K1", city="Bochum", qa=_qa()) == 3


def test_dem_ueberregionalen_anbieter_fehlt_der_ort_nicht():
    """PROFILE: „Ein Ort wird NICHT erwartet." Dann darf er auch nicht fehlen."""
    qa = _qa(title_text="Muster GmbH — Consulting und Workshops für den Mittelstand")

    assert _punkte("se_meta", "K4", city="Bochum", qa=qa) == 3


def test_der_ueberregionale_anbieter_braucht_dafuer_sein_angebot_im_title():
    qa = _qa(title_text="Muster GmbH")

    assert _punkte("se_meta", "K4", city="Bochum", qa=qa) == 2


def test_dem_lokalen_betrieb_fehlt_der_ort_weiterhin():
    qa = _qa(title_text="Muster GmbH — Heizung und Bad")

    assert _punkte("se_meta", "K1", city="Bochum", qa=qa) == 2


# ── Strukturierte Daten: je Klasse ein anderer Haupttyp ───────────────

def test_localbusiness_ist_der_haupttyp_des_lokalen_betriebs():
    qa = _qa(schema_typen=["localbusiness", "faqpage"])

    assert _punkte("se_schema", "K1", qa=qa) == 3


def test_ein_shop_wird_nicht_an_localbusiness_gemessen():
    qa = _qa(schema_typen=["organization", "product", "offer"])

    assert _punkte("se_schema", "K5", qa=qa) == 3
    assert _punkte("se_schema", "K1", qa=qa) == 1


def test_eine_praxis_zaehlt_mit_ihrem_eigenen_typ():
    qa = _qa(schema_typen=["medicalbusiness", "person"])

    assert _punkte("se_schema", "K2", qa=qa) == 3


def test_ohne_jedes_markup_gibt_es_keinen_punkt():
    qa = _qa(schema_markup=False, schema_typen=[])

    assert _punkte("se_schema", "K1", qa=qa) == 0


def test_ein_altbestand_ohne_typenliste_faellt_auf_die_alten_merkmale_zurueck():
    qa = _qa(schema_localbusiness=True, schema_faq=True)
    qa.pop("schema_typen")

    assert _punkte("se_schema", "K1", qa=qa) == 3


# ── Kontaktwege: je Klasse ein anderer Weg ───────────────────────────

HANDWERK = """
<a href="tel:+4923412345">0234 12345</a>
<form><input><input><input></form>
<p>Wir melden uns innerhalb von 24 Stunden.</p>
"""

PRAXIS = """
<a href="tel:+4923412345">0234 12345</a>
<p>Sprechzeiten: Mo–Fr 8–12 Uhr</p>
<form><input><input></form>
"""

SHOP = """
<a href="/service">Kundenservice</a>
<a href="/widerruf">Widerruf und Rückgabe</a>
<p>Versand innerhalb von 24 Stunden.</p>
"""


def test_der_handwerksbetrieb_wird_an_telefon_formular_und_reaktionszeit_gemessen():
    assert _punkte("cv_kontakt", "K1", contact=_kontakt(HANDWERK)) == 3


def test_die_praxis_wird_an_ihren_sprechzeiten_gemessen():
    assert _punkte("cv_kontakt", "K2", contact=_kontakt(PRAXIS)) == 3


def test_der_praxis_fehlt_die_reaktionszeit_nicht():
    """Gegen den Handwerksmaßstab verlöre dieselbe Praxis einen Punkt."""
    kontakt = _kontakt(PRAXIS)

    assert _punkte("cv_kontakt", "K2", contact=kontakt) > _punkte(
        "cv_kontakt", "K1", contact=kontakt)


def test_der_shop_wird_an_seinem_retourenweg_gemessen():
    assert _punkte("cv_kontakt", "K5", contact=_kontakt(SHOP)) == 3


def test_ohne_klasse_bleibt_der_bisherige_massstab():
    assert _punkte("cv_kontakt", "", contact=_kontakt(HANDWERK)) == 3
