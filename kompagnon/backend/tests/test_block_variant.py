"""Der Erzeuger für Stufe B — geprüft ohne einen einzigen Token.

Wie in Stufe A wird die Logik um den KI-Aufruf herum gemessen, nicht der
Aufruf: Was hier zählt, ist die Entscheidung — variieren, reparieren,
ablehnen — und die fällt im Code.
"""
import pytest

from services.block_variant import (
    VariantenAbbruch,
    baue_prompt,
    erzeuge_variante,
    pruefe_variante,
)

SLUG = "hero-probe"
SLOTS = [{"key": "headline", "label": "Ueberschrift"},
         {"key": "subtext", "label": "Subtext"}]

VORLAGE = (f'<section data-block="{SLUG}" class="py-16 bg-white">'
           f'<h2 class="text-3xl text-gray-900">{{{{headline}}}}</h2>'
           f'<p class="text-gray-700">{{{{subtext}}}}</p></section>')


def _variante(html: str) -> str:
    return html


SAUBER = (f'<section data-block="{SLUG}" class="py-24 bg-gray-50">'
          f'<div class="mx-auto max-w-5xl grid md:grid-cols-2 gap-8">'
          f'<h2 class="text-4xl text-gray-900">{{{{headline}}}}</h2>'
          f'<p class="text-gray-700">{{{{subtext}}}}</p></div></section>')


class _Antwort:
    content = []


def _runden(*ergebnisse):
    """Ersetzt `ki_runde` durch vorgegebene Antworten und zählt die Aufrufe."""
    folge = iter(ergebnisse)
    aufrufe = []

    def ki_runde(client, nachrichten):
        aufrufe.append(list(nachrichten))
        return _Antwort(), next(folge)

    return ki_runde, aufrufe


# ── Die zwei Grenzen einer Variante ──────────────────────────────────────

def test_dieselben_slots_sind_in_ordnung():
    assert pruefe_variante(SAUBER, slug=SLUG, slots=SLOTS) == []


def test_weniger_slots_sind_erlaubt():
    kuerzer = (f'<section data-block="{SLUG}" class="py-24">'
               f'<h2 class="text-4xl text-gray-900">{{{{headline}}}}</h2></section>')
    assert pruefe_variante(kuerzer, slug=SLUG, slots=SLOTS) == []


def test_ein_erfundener_slot_wird_beanstandet():
    erfunden = (f'<section data-block="{SLUG}" class="py-24">'
                f'<h2>{{{{ueberschrift}}}}</h2></section>')

    verstoesse = pruefe_variante(erfunden, slug=SLUG, slots=SLOTS)

    assert any(v["regel"] == "B2" for v in verstoesse)
    # Die Meldung nennt, was erlaubt gewesen waere.
    assert "headline" in verstoesse[-1]["text"]


def test_eine_fremde_markierung_wird_beanstandet():
    fremd = '<section data-block="ein-anderer"><h2>{{headline}}</h2></section>'

    assert any(v["regel"] == "R2"
               for v in pruefe_variante(fremd, slug=SLUG, slots=SLOTS))


def test_der_vertrag_gilt_unveraendert():
    mit_karte = (f'<section data-block="{SLUG}"><h2>{{{{headline}}}}</h2>'
                 f'<iframe src="https://maps.example/x"></iframe></section>')

    assert any(v["regel"] == "R1"
               for v in pruefe_variante(mit_karte, slug=SLUG, slots=SLOTS))


# ── Der Auftrag ──────────────────────────────────────────────────────────

def test_eine_saubere_variante_braucht_keine_zweite_runde():
    ki_runde, aufrufe = _runden({"html_override": SAUBER, "begruendung": "Zweispaltig."})

    ergebnis = erzeuge_variante(ki_runde=ki_runde, client=None, slug=SLUG,
                                vorlage=VORLAGE, slots=SLOTS, briefing=None)

    assert ergebnis["contract"]["konform"] is True
    assert ergebnis["begruendung"] == "Zweispaltig."
    assert len(aufrufe) == 1


def test_ein_verstoss_geht_einmal_zurueck():
    kaputt = (f'<section data-block="{SLUG}" id="hero"><h2>{{{{headline}}}}</h2>'
              f'</section>')
    ki_runde, aufrufe = _runden({"html_override": kaputt},
                                {"html_override": SAUBER})

    ergebnis = erzeuge_variante(ki_runde=ki_runde, client=None, slug=SLUG,
                                vorlage=VORLAGE, slots=SLOTS, briefing=None)

    assert ergebnis["contract"]["konform"] is True
    assert len(aufrufe) == 2
    # Der Reparaturauftrag nennt den Verstoss beim Namen.
    assert "id-Attribut" in aufrufe[1][-1]["content"]


def test_eine_schlechtere_reparatur_wird_nicht_uebernommen():
    einmal_kaputt = (f'<section data-block="{SLUG}" id="hero">'
                     f'<h2>{{{{headline}}}}</h2></section>')
    schlimmer = (f'<section data-block="{SLUG}" id="hero">'
                 f'<h2>{{{{erfunden}}}}</h2>'
                 f'<iframe src="https://x.example/y"></iframe></section>')
    ki_runde, _ = _runden({"html_override": einmal_kaputt},
                          {"html_override": schlimmer})

    ergebnis = erzeuge_variante(ki_runde=ki_runde, client=None, slug=SLUG,
                                vorlage=VORLAGE, slots=SLOTS, briefing=None)

    assert "iframe" not in ergebnis["html_override"]
    assert ergebnis["contract"]["konform"] is False


def test_ohne_markup_bricht_der_auftrag_ab():
    ki_runde, _ = _runden({"begruendung": "vergessen"})

    with pytest.raises(VariantenAbbruch):
        erzeuge_variante(ki_runde=ki_runde, client=None, slug=SLUG,
                         vorlage=VORLAGE, slots=SLOTS, briefing=None)


# ── Der Auftrag ans Modell ───────────────────────────────────────────────

class _Briefing:
    gewerk = "Sanitär, Heizung, Klima"
    leistungen = "Wärmepumpe, Bad-Sanierung, Notdienst"
    einzugsgebiet = "Koblenz und 50 km Umkreis"
    usp = "Meisterbetrieb seit 1974, Notdienst in 90 Minuten"
    stil = None
    sonstige_hinweise = ""


def test_der_prompt_beschreibt_den_betrieb():
    """Ohne konkrete Welt fällt jedes Modell in denselben Durchschnitt."""
    prompt = baue_prompt(slug=SLUG, vorlage=VORLAGE, slots=SLOTS,
                         briefing=_Briefing(), wunsch="", seite="Startseite")

    assert "Wärmepumpe" in prompt
    assert "Koblenz und 50 km Umkreis" in prompt
    assert "Meisterbetrieb seit 1974" in prompt
    assert "Startseite" in prompt
    # Leere Felder erscheinen nicht als leere Zeilen.
    assert "Stil-Wunsch" not in prompt


def test_der_prompt_nennt_die_erlaubten_slots_und_den_slug():
    prompt = baue_prompt(slug=SLUG, vorlage=VORLAGE, slots=SLOTS, briefing=None)

    assert "{{headline}}" in prompt
    assert f'data-block="{SLUG}"' in prompt


def test_ohne_briefing_sagt_der_prompt_das_auch():
    prompt = baue_prompt(slug=SLUG, vorlage=VORLAGE, slots=SLOTS, briefing=None)

    assert "Kein Briefing hinterlegt" in prompt
