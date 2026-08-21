"""Wie aus vielen Seitenbefunden einer wird.

Jede dieser Regeln ist eine Entscheidung, keine Rechenvorschrift — und jede
davon kann eine Note verschieben. Deshalb hat hier jede Familie ihren eigenen
Test mit dem Fall, den sie erklaeren soll.

Der Vertrag zu `audit_scoring` steht in `test_vertrag_zur_bewertung`: Die
Bewertung liest feste Schluessel, und die muessen alle da sein. Faellt einer
weg, rutscht das Kriterium still auf 'nicht erhoben' und der Gesamtscore
steigt — ein Fehler, der wie eine Verbesserung aussieht.
"""
from services import audit_aggregat as agg


def _seite(url="https://x.de/", **bloecke):
    grund = {"url": url}
    grund.update({name: {"collected": True, **wert} for name, wert in bloecke.items()})
    return grund


# ── Irgendwo genuegt ─────────────────────────────────────────────────────────

def test_telefonnummer_im_impressum_zaehlt():
    """Eine Nummer auf der Unterseite ist eine Nummer. Genau dieser Fall fiel
    bis zum 21.08.2026 durch — geprueft wurde nur die Startseite."""
    befunde = [
        _seite("https://x.de/", contact={"tel_link": False}),
        _seite("https://x.de/impressum", contact={"tel_link": True}),
    ]

    assert agg.contact(befunde)["tel_link"] is True


def test_tracker_auf_der_kontaktseite_zaehlt():
    """Ein Kartendienst laedt oft nur auf `/kontakt`. Wer nur die Startseite
    prueft, bescheinigt Datensparsamkeit, die es nicht gibt."""
    befunde = [
        _seite(third_parties={"services": [], "tracking_services": [],
                              "external_fonts": False, "maps_embedded": False,
                              "count": 0}),
        _seite("https://x.de/kontakt",
               third_parties={"services": ["google_maps", "google_analytics"],
                              "tracking_services": ["google_analytics"],
                              "external_fonts": False, "maps_embedded": True,
                              "count": 2}),
    ]

    ergebnis = agg.third_parties(befunde)

    assert ergebnis["count"] == 2
    assert ergebnis["tracking_services"] == ["google_analytics"]
    assert ergebnis["maps_embedded"] is True


def test_dienst_auf_mehreren_seiten_zaehlt_einmal():
    befunde = [_seite(third_parties={"services": ["google_fonts"], "count": 1}),
               _seite("https://x.de/a", third_parties={"services": ["google_fonts"],
                                                        "count": 1})]

    assert agg.third_parties(befunde)["count"] == 1


# ── Aufsummieren ─────────────────────────────────────────────────────────────

def test_formulare_werden_gezaehlt():
    befunde = [_seite(forms={"total": 1, "secure_action": 1, "post_method": 1,
                             "with_consent": 1}),
               _seite("https://x.de/kontakt",
                      forms={"total": 2, "secure_action": 2, "post_method": 2,
                             "with_consent": 2})]

    assert agg.forms(befunde)["total"] == 3


def test_ein_formular_ohne_haken_kippt_all_consent():
    """Die einzige Familie, in der eine zusaetzliche Seite die Bewertung
    verschlechtern kann — und das ist richtig so."""
    befunde = [_seite(forms={"total": 1, "with_consent": 1, "secure_action": 1}),
               _seite("https://x.de/angebot",
                      forms={"total": 1, "with_consent": 0, "secure_action": 1})]

    ergebnis = agg.forms(befunde)

    assert ergebnis["with_consent"] == 1
    assert ergebnis["all_consent"] is False


def test_ohne_formulare_ist_all_consent_nicht_wahr():
    """`0 == 0` waere sonst „alle Formulare haben einen Haken" — bei null
    Formularen. Das ist kein Lob, sondern eine Fehlmessung."""
    befunde = [_seite(forms={"total": 0})]

    assert agg.forms(befunde)["all_consent"] is False


def test_woerter_werden_addiert():
    befunde = [{"url": "a", "word_count": 300}, {"url": "b", "word_count": 450}]

    assert agg.fasse_zusammen(befunde)["word_count"] == 750


# ── Anteile ──────────────────────────────────────────────────────────────────

def test_bildanteile_werden_neu_gerechnet_nicht_gemittelt():
    """Der Mittelwert aus 100 % bei einem Bild und 0 % bei neunzig ist 50 % —
    und damit eine Luege."""
    befunde = [
        _seite(images={"total": 1, "modern_format": 1, "modern_share": 100,
                       "lazy_loading": 0, "with_dimensions": 0}),
        _seite("https://x.de/a",
               images={"total": 90, "modern_format": 0, "modern_share": 0,
                       "lazy_loading": 0, "with_dimensions": 0}),
    ]

    ergebnis = agg.images(befunde)

    assert ergebnis["total"] == 91
    assert ergebnis["modern_share"] == 1


# ── Vereinigen ───────────────────────────────────────────────────────────────

def test_leistungsseiten_werden_je_pfad_einmal_gezaehlt():
    """Dieselbe Leistung aus dem Fussbereich jeder Seite verlinkt ist eine
    Leistung, nicht zwanzig."""
    seite = {"seiten": [{"pfad": "/waermepumpe", "begriffe": ["waermepumpe"]}],
             "service_page_count": 1}
    befunde = [_seite(services=seite), _seite("https://x.de/a", services=seite)]

    assert agg.services(befunde)["service_page_count"] == 1


def test_leistungsseiten_aus_dem_fussbereich_einer_unterseite_zaehlen_mit():
    """Bisher zaehlten nur die Links der Startseite."""
    befunde = [
        _seite(services={"seiten": [{"pfad": "/heizung", "begriffe": ["heizung"]}],
                         "service_page_count": 1}),
        _seite("https://x.de/heizung",
               services={"seiten": [{"pfad": "/wallbox", "begriffe": ["wallbox"]}],
                         "service_page_count": 1}),
    ]

    ergebnis = agg.services(befunde)

    assert ergebnis["service_page_count"] == 2
    assert [s["pfad"] for s in ergebnis["seiten"]] == ["/heizung", "/wallbox"]


def test_dieselbe_innung_auf_fuenf_seiten_ist_ein_signal():
    einer = {"innung": True, "bewertungen": False, "zertifikat_begriffe": ["meisterbetrieb"]}
    befunde = [_seite(trust=einer) for _ in range(5)]

    ergebnis = agg.trust(befunde)

    assert ergebnis["signal_count"] == 2      # innung + Zertifikat
    assert ergebnis["zertifikat_begriffe"] == ["meisterbetrieb"]


def test_cta_wird_bewusst_nicht_entdoppelt():
    """Ein „Jetzt anfragen" auf jeder Unterseite ist auf jeder Seite ein
    Angebot zu handeln — anders als eine Leistungsseite."""
    einer = {"cta_count": 2, "elemente": [{"text": "Jetzt anfragen", "begriffe": ["anfragen"]}]}
    befunde = [_seite(cta=einer), _seite("https://x.de/a", cta=einer)]

    assert agg.cta(befunde)["cta_count"] == 4


# ── Sonderfaelle ─────────────────────────────────────────────────────────────

def test_das_neueste_jahr_gewinnt():
    """Ein alter Blogbeitrag macht die Website nicht veraltet."""
    befunde = [_seite(freshness={"copyright_year": 2019, "copyright_current": False,
                                 "has_dated_content": True}),
               _seite("https://x.de/a",
                      freshness={"copyright_year": 2026, "copyright_current": True,
                                 "has_dated_content": False})]

    ergebnis = agg.freshness(befunde)

    assert ergebnis["copyright_year"] == 2026
    assert ergebnis["copyright_current"] is True


def test_das_schlankste_formular_zaehlt_nicht_die_summe():
    """Ein Drei-Feld-Formular auf `/kontakt` ist ein kurzer Weg, auch wenn
    woanders ein langes Angebotsformular steht."""
    befunde = [_seite(contact={"form_field_count": 12, "tel_link": False}),
               _seite("https://x.de/kontakt",
                      contact={"form_field_count": 3, "tel_link": False})]

    assert agg.contact(befunde)["form_field_count"] == 3


def test_ausgefallene_erhebungen_werden_uebergangen():
    """Ein Block ohne `collected` ist ein Ausfall, kein Nullwert. Ihn
    mitzuzaehlen hiesse, eine fehlende Messung als Mangel zu verkaufen."""
    befunde = [
        {"url": "a", "forms": {"collected": False}},
        _seite("https://x.de/b", forms={"total": 2, "with_consent": 2,
                                        "secure_action": 2}),
    ]

    assert agg.forms(befunde)["total"] == 2


def test_gar_keine_erhebung_bleibt_nicht_erhoben():
    assert agg.forms([{"url": "a"}]) == {"collected": False}
    assert agg.contact([]) == {"collected": False}


def test_vertrag_zur_bewertung():
    """`audit_scoring` liest diese Schluessel. Faellt einer weg, rutscht das
    Kriterium still auf 'nicht erhoben' — und der Gesamtscore steigt."""
    befunde = [_seite(
        consent={"cmp_detected": True, "cmp_names": ["cookiebot"]},
        third_parties={"services": ["google_fonts"], "tracking_services": [],
                       "external_fonts": True, "count": 1},
        forms={"total": 1, "with_consent": 1, "secure_action": 1},
        contact={"tel_link": True, "form_field_count": 4},
        trust={"innung": True, "zertifikat_begriffe": []},
        services={"seiten": [{"pfad": "/a", "begriffe": ["x"]}], "service_page_count": 1},
        freshness={"copyright_current": True, "has_dated_content": True},
        cta={"cta_count": 3, "elemente": []},
        images={"total": 4, "modern_format": 2, "lazy_loading": 1,
                "with_dimensions": 4, "oversized": 0},
        shop={"is_shop": False, "signals": []},
    )]

    zusammen = agg.fasse_zusammen(befunde)

    erwartet = {
        "contact": ["tel_link"],
        "cta": ["cta_count", "elemente"],
        "trust": ["signal_count", "zertifikat_begriffe"],
        "services": ["seiten", "service_page_count"],
        "forms": ["all_consent", "total", "with_consent"],
        "freshness": ["copyright_current", "has_dated_content"],
        "third_parties": ["count", "external_fonts", "tracking_services"],
        "consent": ["cmp_detected"],
        "images": ["dimension_share", "lazy_share", "modern_share", "oversized", "total"],
    }
    for block, schluessel in erwartet.items():
        for name in schluessel:
            assert name in zusammen[block], f"{block}.{name} fehlt"
    assert isinstance(zusammen["word_count"], int)


def test_das_fussformular_wird_je_seite_gezaehlt():
    """Bewusst so, nicht uebersehen: `total` zaehlt Vorkommen. Die Bewertung
    nutzt es nur als Schranke; entschieden wird ueber `all_consent`, und darauf
    wirkt die Vervielfachung nicht."""
    fuss = {"total": 1, "with_consent": 0, "secure_action": 1}
    befunde = [_seite(f"https://x.de/{i}", forms=fuss) for i in range(25)]

    ergebnis = agg.forms(befunde)

    assert ergebnis["total"] == 25
    assert ergebnis["all_consent"] is False
