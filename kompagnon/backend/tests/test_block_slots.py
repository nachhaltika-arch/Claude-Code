"""Slot-Angaben aus dem Markup vervollstaendigen.

Der scharfe Lauf vom 2026-08-13 hat genau einen Vertragsverstoss produziert,
und der war zwoelfmal derselbe: Slots stehen im Markup, fehlen aber in den
Slot-Angaben — `generate-copy` wuerde sie nie fuellen. Das Modell dafuer ein
zweites Mal zu fragen hat in dem Fall 11k Eingabe- und 8k Ausgabe-Token
gekostet. Ableiten laesst es sich aus dem Markup selbst.
"""
from services.block_slots import ergaenze_fehlende_slots


def test_fehlender_slot_wird_aus_dem_markup_ergaenzt():
    html = '<section data-block="x"><h2>{{headline}}</h2><p>{{sub_text}}</p></section>'
    slots = [{"key": "headline", "type": "text", "label": "Ueberschrift",
              "default": "Waermepumpe"}]

    ergebnis = ergaenze_fehlende_slots(html, slots)

    assert [s["key"] for s in ergebnis] == ["headline", "sub_text"]
    assert ergebnis[1]["label"] == "Sub Text"
    assert ergebnis[1]["type"] == "text"


def test_bestehende_angaben_bleiben_unangetastet():
    """Was das Modell selbst beschriftet hat, ist besser als jede Ableitung."""
    html = '<section data-block="x"><h2>{{headline}}</h2></section>'
    slots = [{"key": "headline", "label": "Hauptueberschrift", "default": "Original"}]

    ergebnis = ergaenze_fehlende_slots(html, slots)

    assert ergebnis == slots


def test_die_urspruengliche_liste_wird_nicht_veraendert():
    html = '<section data-block="x">{{a}}{{b}}</section>'
    slots = [{"key": "a"}]

    ergaenze_fehlende_slots(html, slots)

    assert slots == [{"key": "a"}], "Die Eingabeliste wurde mutiert"


def test_reihenfolge_folgt_dem_markup():
    html = '<section data-block="x">{{dritter}}{{erster}}{{zweiter}}</section>'

    ergebnis = ergaenze_fehlende_slots(html, [{"key": "erster"}])

    assert [s["key"] for s in ergebnis] == ["erster", "dritter", "zweiter"]


def test_slots_ohne_markup_bleiben_erhalten():
    """Ein Slot mehr in den Angaben ist kein Verstoss — nur einer weniger."""
    html = '<section data-block="x">{{a}}</section>'

    ergebnis = ergaenze_fehlende_slots(html, [{"key": "a"}, {"key": "unbenutzt"}])

    assert [s["key"] for s in ergebnis] == ["a", "unbenutzt"]


def test_dubletten_im_markup_ergeben_einen_eintrag():
    html = '<section data-block="x">{{wiederholt}} … {{wiederholt}}</section>'

    ergebnis = ergaenze_fehlende_slots(html, [])

    assert [s["key"] for s in ergebnis] == ["wiederholt"]


def test_kaputte_eintraege_stehen_der_ergaenzung_nicht_im_weg():
    """Ein Eintrag ohne key sagt nichts darueber, welche Slots belegt sind."""
    html = '<section data-block="x">{{headline}}</section>'

    ergebnis = ergaenze_fehlende_slots(html, [{"label": "ohne key"}, "kein dict"])

    assert [s.get("key") for s in ergebnis if isinstance(s, dict)] == [None, "headline"]


def test_ohne_slots_im_markup_aendert_sich_nichts():
    assert ergaenze_fehlende_slots("<section>ohne Slots</section>", []) == []
