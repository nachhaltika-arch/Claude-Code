"""
Tests für die Punktvergabe aus erhobenen Fakten.

Kernanliegen der Überarbeitung: es wird nichts mehr geraten. Fehlt eine
Erhebung, muss das Kriterium als 'nicht erhoben' gelten — nicht als 0 Punkte
und erst recht nicht als Konstante.
"""
from services.audit_criteria import Source
from services.audit_scoring import detect_blockers, score_audit


def _fakten(**overrides) -> dict:
    """Vollständig erhobene Fakten einer tadellosen Website."""
    facts = {
        "url": "https://example.de",
        "city": "Bochum",
        "reachable": True,
        "word_count": 850,
        "legal": {
            "collected": True,
            "impressum": {"reachable": True, "complete": True},
            "datenschutz": {"reachable": True, "complete": True},
            "bfsg": {"linked": True},
        },
        "consent": {"collected": True, "cmp_detected": True},
        "third_parties": {"collected": True, "count": 0, "tracking_services": [],
                          "external_fonts": False, "maps_embedded": False},
        "forms": {"collected": True, "total": 1, "all_secure": True, "post_method": 1,
                  "with_consent": 1, "all_consent": True},
        "tls": {"collected": True, "valid": True, "expires_soon": False},
        "redirect": {"collected": True, "redirects": True},
        "security_headers": {"collected": True, "hsts": True, "csp": True,
                             "xframe": True, "xcontent": True},
        "psi_mobile": {
            "collected": True, "lcp_seconds": 1.8, "cls_value": 0.02, "inp_ms": 120,
            "performance_score": 95, "accessibility_score": 96,
            "a11y_audits": {"kontrast": 1.0, "tastatur": 1.0,
                            "screenreader": 1.0, "lesbarkeit": 1.0},
        },
        "images": {"collected": True, "total": 10, "modern_share": 90,
                   "lazy_share": 80, "dimension_share": 100, "oversized": 0},
        "qa": {
            "title_vorhanden": True, "title_laenge_ok": True,
            # Ort **und** Leistung: Der Ort trägt den Punkt in den lokalen
            # Klassen, die Leistung dort, wo ein Ort nicht erwartet wird.
            "title_text": "Heizung Bochum — Leistungen der Muster GmbH",
            "meta_desc_vorhanden": True, "meta_desc_laenge_ok": True,
            "h1_genau_eins": True, "h2_vorhanden": True, "heading_struktur_ok": True,
            "h1_text": "Wärmepumpe in Bochum", "canonical_vorhanden": True,
            "robots_txt": True, "robots_txt_indexiert": True, "sitemap_xml": True,
            "schema_markup": True, "schema_localbusiness": True, "schema_faq": True,
            "google_maps": True, "mobile_viewport": True, "alt_texte_quote": 100,
        },
        # Tadellos heißt: tadellos in jeder Branchenklasse. Deshalb stehen hier
        # auch die Beobachtungen, an denen Praxis, Publikumsbetrieb, Anbieter
        # und Shop gemessen werden — sonst wäre die Seite nur für einen
        # Handwerksbetrieb perfekt.
        "contact": {"collected": True, "tel_link": True, "mailto_link": True,
                    "form": True, "form_is_lean": True, "response_time_stated": True,
                    "oeffnungszeiten": True, "terminbuchung": True, "anfahrt": True,
                    "ansprechperson": True, "retourenweg": True,
                    "servicekontakt": True},
        "cta": {"collected": True, "cta_count": 5, "has_cta": True},
        "trust": {"collected": True, "signal_count": 5},
        "services": {"collected": True, "service_page_count": 4},
        "freshness": {"collected": True, "copyright_current": True},
        "links": {"broken_links": []},
        "cdn": {"collected": True, "cdn_active": True},
        "hosting": {"hosting_provider": "Hetzner", "detected_technologies": ["WordPress"]},
    }
    facts.update(overrides)
    return facts


def _ki_voll() -> dict:
    return {
        "dg_aktualitaet": 3, "dg_typografie": 2, "dg_farbsystem": 2,
        "dg_bildqualitaet": 2, "cv_klarheit": 3, "cv_angebot": 3,
        "ih_textqualitaet": 2,
    }


# ── Vollbild ──────────────────────────────────────────────────────────

def test_tadellose_website_erreicht_platin():
    result = score_audit(_fakten(), _ki_voll())
    assert result["total_score"] == 100
    assert result["level"] == "Homepage Standard Platin"
    assert result["blockers"] == []
    assert result["coverage"] == 100


def test_alle_kriterien_bekommen_eine_quelle():
    result = score_audit(_fakten(), _ki_voll())
    for key, source in result["sources"].items():
        assert source in {s.value for s in Source}, key


# ── Nichts wird geraten ───────────────────────────────────────────────

def test_ohne_pagespeed_gelten_performance_und_a11y_als_nicht_erhoben():
    """Ohne API-Key wurden früher Fantasiewerte eingetragen."""
    facts = _fakten(psi_mobile={"collected": False, "reason": "kein_api_key"})
    result = score_audit(facts, _ki_voll())

    for key in ("tp_lcp", "tp_cls", "tp_inp", "tp_mobile",
                "bf_lighthouse", "bf_kontrast", "bf_tastatur"):
        assert result["sources"][key] == Source.NOT_COLLECTED.value, key

    # Der Score bleibt hoch, weil der Nenner kleiner wird — kein stiller Abzug.
    assert result["total_score"] == 100
    assert result["coverage"] < 100


def test_ohne_ki_bleiben_design_und_conversion_nicht_erhoben():
    result = score_audit(_fakten(), ai={})
    for key in ("dg_aktualitaet", "dg_typografie", "cv_klarheit",
                "cv_angebot", "ih_textqualitaet"):
        assert result["sources"][key] == Source.NOT_COLLECTED.value, key
    assert result["total_score"] == 100


# ── Keine Betriebsseite: der fremde Maßstab fällt weg ─────────────────

def test_ohne_betriebsseite_fallen_die_angebotskriterien_heraus():
    """Eine Seite ohne Betrieb hat kein Angebot — das ist kein Mangel.

    Anlass: Das Audit bewertete den Auftritt eines politischen Kandidaten und
    hielt ihm fehlende Leistungsbeschreibungen, ein fehlendes Einsatzgebiet und
    einen fehlenden Preisrahmen vor. Richtig gerechnet, als Aussage unbrauchbar.
    """
    ki = {**_ki_voll(), "betriebsseite": False, "branche": "politischer Kandidat"}
    result = score_audit(_fakten(), ki)

    for key in ("cv_klarheit", "cv_angebot", "ih_textqualitaet"):
        assert result["sources"][key] == Source.NOT_APPLICABLE.value, key
    # Kein stiller Abzug: der Nenner wird kleiner, nicht der Zähler.
    assert result["total_score"] == 100
    # Die Abdeckung misst gegen das anwendbare Maximum: Es fiel nichts aus,
    # es gilt nur weniger.
    assert result["coverage"] == 100
    assert result["anwendbares_maximum"] < 100


def test_ohne_betriebsseite_bleibt_die_gestaltung_bewertet():
    """Typografie, Farbkontrast und Bildqualität gelten für jede Seite."""
    ki = {**_ki_voll(), "betriebsseite": False, "branche": "Verein"}
    result = score_audit(_fakten(), ki)

    for key in ("dg_aktualitaet", "dg_typografie", "dg_farbsystem", "dg_bildqualitaet"):
        assert result["sources"][key] == Source.AI.value, key


def test_eine_betriebsseite_wird_vollstaendig_bewertet():
    ki = {**_ki_voll(), "betriebsseite": True, "branche": "Dachdecker"}
    result = score_audit(_fakten(), ki)

    for key in ("cv_klarheit", "cv_angebot", "ih_textqualitaet"):
        assert result["sources"][key] == Source.AI.value, key
    assert result["coverage"] == 100


def test_ohne_aussage_zur_betriebsseite_bleibt_es_beim_alten_verhalten():
    """Fehlt die Angabe, wird nichts verworfen — sonst verschwinden Kriterien,
    weil das Modell ein Feld nicht gefüllt hat."""
    result = score_audit(_fakten(), _ki_voll())

    for key in ("cv_klarheit", "cv_angebot", "ih_textqualitaet"):
        assert result["sources"][key] == Source.AI.value, key


def test_ohne_formular_wird_formularkriterium_nicht_bewertet():
    facts = _fakten(forms={"collected": True, "total": 0})
    result = score_audit(facts, _ki_voll())
    assert result["sources"]["rc_formular_dsgvo"] == Source.NOT_COLLECTED.value


def test_ohne_bilder_wird_bildoptimierung_nicht_bewertet():
    facts = _fakten(images={"collected": True, "total": 0})
    result = score_audit(facts, _ki_voll())
    assert result["sources"]["tp_bilder"] == Source.NOT_COLLECTED.value


# ── Einzelne Kriterien ────────────────────────────────────────────────

def test_ungueltiges_zertifikat_gibt_null_punkte():
    facts = _fakten(tls={"collected": True, "valid": False, "reason": "zertifikat_ungueltig"})
    result = score_audit(facts, _ki_voll())
    assert result["items"]["si_ssl"] == 0
    assert result["sources"]["si_ssl"] == Source.MEASURED.value


def test_bald_ablaufendes_zertifikat_gibt_abzug_statt_null():
    facts = _fakten(tls={"collected": True, "valid": True, "expires_soon": True})
    result = score_audit(facts, _ki_voll())
    assert result["items"]["si_ssl"] == 2


def test_impressum_erreichbar_aber_unvollstaendig_gibt_teilpunkte():
    facts = _fakten()
    facts["legal"]["impressum"] = {"reachable": True, "complete": False,
                                   "missing": ["register"]}
    result = score_audit(facts, _ki_voll())
    assert result["items"]["rc_impressum"] == 3


def test_wort_cookie_allein_reicht_nicht_fuer_punkte():
    """Der Altcode gab volle Punkte, sobald 'cookie' im HTML stand."""
    facts = _fakten(
        consent={"collected": True, "cmp_detected": False, "mentions_cookie_only": True},
        third_parties={"collected": True, "count": 2, "tracking_services": ["google_analytics"],
                       "external_fonts": True, "maps_embedded": False},
    )
    result = score_audit(facts, _ki_voll())
    assert result["items"]["rc_cookie"] == 0


def test_ohne_einwilligungspflichtige_dienste_ist_kein_banner_noetig():
    facts = _fakten(consent={"collected": True, "cmp_detected": False})
    result = score_audit(facts, _ki_voll())
    assert result["items"]["rc_cookie"] == 4
    assert result["sources"]["rc_cookie"] == Source.DERIVED.value


def test_fehlendes_inp_wird_nicht_als_schlechter_wert_gewertet():
    facts = _fakten()
    facts["psi_mobile"] = {**facts["psi_mobile"], "inp_ms": None}
    result = score_audit(facts, _ki_voll())
    assert result["sources"]["tp_inp"] == Source.NOT_COLLECTED.value


def test_defekte_links_kosten_den_punkt():
    facts = _fakten(links={"broken_links": [{"url": "https://example.de/weg", "status_code": 404}]})
    result = score_audit(facts, _ki_voll())
    assert result["items"]["se_links"] == 0


def test_wenige_vertrauenssignale_geben_teilpunkte():
    facts = _fakten(trust={"collected": True, "signal_count": 2})
    result = score_audit(facts, _ki_voll())
    assert result["items"]["cv_vertrauen"] == 2


def test_eine_sammelseite_statt_leistungsseiten_gibt_teilpunkte():
    facts = _fakten(services={"collected": True, "service_page_count": 1})
    result = score_audit(facts, _ki_voll())
    assert result["items"]["ih_leistungsseiten"] == 1


# ── K.-o.-Kriterien ───────────────────────────────────────────────────

def test_fehlendes_impressum_wird_als_blocker_erkannt():
    facts = _fakten()
    facts["legal"]["impressum"] = {"reachable": False, "complete": False}
    result = score_audit(facts, _ki_voll())
    assert "kein_impressum" in result["blockers"]
    assert result["level"] == "Nicht konform"


def test_tracking_ohne_consent_deckelt_das_level():
    facts = _fakten(
        consent={"collected": True, "cmp_detected": False},
        third_parties={"collected": True, "count": 1,
                       "tracking_services": ["google_analytics"],
                       "external_fonts": False, "maps_embedded": False},
    )
    result = score_audit(facts, _ki_voll())
    assert "tracking_ohne_consent" in result["blockers"]
    assert result["level"] == "Homepage Standard Bronze"


def test_ohne_erhobene_rechtsseiten_gibt_es_keine_falschen_blocker():
    """Nicht erhoben heißt nicht 'fehlt' — sonst blockiert jeder Netzwerkfehler."""
    facts = _fakten(legal={"collected": False, "reason": "timeout"})
    assert detect_blockers(facts) == []


def test_leere_fakten_stuerzen_nicht_ab():
    result = score_audit({}, {})
    assert result["total_score"] == 0
    assert result["level"] == "Nicht konform"


# ── Die Branchenklasse trägt die Bewertung (Bewertungslogik 2026.2) ───

def test_der_ueberregionale_anbieter_verliert_die_lokalen_signale():
    """K4 arbeitet bundesweit — ein Ortsbezug ist dort kein Qualitätsmerkmal."""
    ki = {**_ki_voll(), "branche": "Unternehmensberatung", "betriebsseite": True,
          "branchenklasse": "K4", "branchenklasse_quelle": "map"}
    result = score_audit(_fakten(), ki)

    assert result["sources"]["se_lokal"] == Source.NOT_APPLICABLE.value
    # Kein Abzug: der Nenner wird kleiner, nicht der Zähler.
    assert result["total_score"] == 100
    assert result["anwendbares_maximum"] == 97
    # Alles Anwendbare wurde erhoben.
    assert result["coverage"] == 100


def test_die_klasse_ohne_betrieb_verwirft_die_angebotskriterien():
    ki = {**_ki_voll(), "branche": "politischer Kandidat", "betriebsseite": False,
          "branchenklasse": "K6", "branchenklasse_quelle": "map"}
    result = score_audit(_fakten(), ki)

    for key in ("cv_klarheit", "cv_cta", "cv_kontakt", "cv_vertrauen",
                "cv_angebot", "ih_leistungsseiten", "ih_textqualitaet",
                "se_lokal"):
        assert result["sources"][key] == Source.NOT_APPLICABLE.value, key
    assert result["anwendbares_maximum"] == 78
    assert result["total_score"] == 100


def test_gestaltung_wird_auch_ohne_betrieb_bewertet():
    ki = {**_ki_voll(), "branchenklasse": "K6", "betriebsseite": False}
    result = score_audit(_fakten(), ki)

    for key in ("dg_aktualitaet", "dg_typografie", "dg_farbsystem",
                "dg_bildqualitaet"):
        assert result["sources"][key] == Source.AI.value, key


def test_ohne_klasse_im_ergebnis_wird_sie_aus_der_branche_abgeleitet():
    """Ältere Ergebnisse tragen nur branche und betriebsseite."""
    ki = {**_ki_voll(), "branche": "Dachdecker", "betriebsseite": True}
    result = score_audit(_fakten(), ki)

    assert result["branchenklasse"] == "K1"
    assert result["branchenklasse_quelle"] == "map"


def test_ohne_jede_erkennung_wird_der_ganze_katalog_bewertet():
    """Ein fehlgeschlagener KI-Aufruf darf keine Kriterien verschwinden lassen."""
    result = score_audit(_fakten(), ai={})

    assert result["branchenklasse"] == ""
    assert result["anwendbares_maximum"] == 100
    assert result["sources"]["se_lokal"] != Source.NOT_APPLICABLE.value


def test_das_ergebnis_traegt_die_fassung_des_standards():
    """Ohne Versionsstempel lässt sich ein Altbestand später nicht einordnen."""
    result = score_audit(_fakten(), _ki_voll())

    assert result["standard_version"] == "2026.2"


def test_rohpunkte_und_anwendbares_maximum_stehen_nebeneinander():
    ki = {**_ki_voll(), "branchenklasse": "K6", "betriebsseite": False}
    result = score_audit(_fakten(), ki)

    assert result["rohpunkte"] == result["achieved_points"]
    assert result["rohpunkte"] <= result["anwendbares_maximum"]
