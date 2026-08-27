"""Der Katalog muss dieselbe Erhebungsart nennen wie die Bewertung (S2).

**Warum das mehr ist als Kosmetik.** Kapitel 3 des Standards verspricht dem
Leser, dass jede Erhebungsart gekennzeichnet ist — und dass er einer
**Einschätzung** deshalb widersprechen kann, einer **Messung** aber nicht.
Ein Kriterium, das im Bericht anders erscheint als im Katalog, untergräbt
genau dieses Versprechen.

**Zwei Abweichungen, gefunden in C1:**

* `bf_semantik` stand als `DERIVED` im Katalog, während die Bewertung
  `MEASURED` schrieb. Seit S1.1 ist es zweifelsfrei gemessen — DOM plus zwei
  Lighthouse-Prüfungen.
* `rc_cookie` wird auf **zwei** Wegen erhoben: gemessen, wenn ein
  Consent-Werkzeug erkannt wird; abgeleitet, wenn aus „keine
  einwilligungspflichtigen Dienste" auf „kein Banner nötig" geschlossen wird.
  Der Katalog nannte nur den ersten.

Dieser Test vergleicht nicht Text mit Text, sondern **Deklaration mit
Verhalten**: Er lässt die Bewertung laufen und sieht nach, welche Quelle
tatsächlich herauskommt.
"""
import pytest

from services.audit_criteria import Source, find_criterion


class TestBfSemantik:
    def test_der_katalog_fuehrt_es_als_gemessen(self):
        assert find_criterion("bf_semantik").source is Source.MEASURED


class TestRcCookie:
    def test_der_katalog_nennt_beide_erhebungsarten(self):
        kriterium = find_criterion("rc_cookie")
        arten = {kriterium.source, kriterium.alt_source}
        assert arten == {Source.MEASURED, Source.DERIVED}

    def test_mit_erkanntem_werkzeug_ist_es_gemessen(self):
        from services.audit_scoring import score_audit

        fakten = {
            "consent": {"collected": True, "cmp_detected": True},
            "third_parties": {"collected": True, "count": 3},
        }
        ergebnis = score_audit(fakten)
        assert ergebnis["sources"]["rc_cookie"] == Source.MEASURED.value

    def test_ohne_einwilligungspflichtige_dienste_ist_es_abgeleitet(self):
        from services.audit_scoring import score_audit

        fakten = {
            "consent": {"collected": True, "cmp_detected": False},
            "third_parties": {"collected": True, "count": 0},
        }
        ergebnis = score_audit(fakten)
        assert ergebnis["sources"]["rc_cookie"] == Source.DERIVED.value


class TestKeinKriteriumWidersprichtSichSelbst:
    """Der Waechter gegen die naechste Abweichung dieser Art.

    Er prueft nicht jedes Kriterium — viele haengen an Fakten, die eine
    Testvorlage nicht sinnvoll stellen kann. Er prueft die Kriterien, die
    eine **tadellose** Website erhebt: Dort muss die tatsaechliche Quelle in
    den Deklarationen des Katalogs vorkommen.
    """

    def test_die_gemessene_quelle_steht_im_katalog(self):
        from services.audit_scoring import score_audit
        from tests.test_audit_scoring import _fakten, _ki_voll

        ergebnis = score_audit(_fakten(), _ki_voll())

        abweichungen = []
        for schluessel, tatsaechlich in ergebnis["sources"].items():
            if tatsaechlich in (Source.NOT_COLLECTED.value,
                                Source.NOT_APPLICABLE.value):
                continue
            kriterium = find_criterion(schluessel)
            if not kriterium:
                continue
            erlaubt = {kriterium.source.value}
            if kriterium.alt_source:
                erlaubt.add(kriterium.alt_source.value)
            if tatsaechlich not in erlaubt:
                abweichungen.append(
                    f"{schluessel}: Katalog {sorted(erlaubt)}, "
                    f"Bewertung {tatsaechlich}")

        assert not abweichungen, (
            "Der Katalog nennt eine andere Erhebungsart als die Bewertung. "
            "Kapitel 3 verspricht dem Leser, dass er einer Einschaetzung "
            f"widersprechen kann — das setzt voraus, dass die Kennzeichnung "
            f"stimmt: {abweichungen}"
        )


class TestDieHinweiseVersprechenNichtMehrAlsGeprueftWird:
    """S3 — der Hinweis erscheint im Kundenbericht.

    Wer dort „Tap-Targets groß genug" liest und dafür einen Punkt verliert,
    sucht an der falschen Stelle. Diese Tests halten die zwölf Kürzungen vom
    24.08.2026 fest, damit sie nicht beim nächsten Umbau zurückkehren.
    """

    @pytest.mark.parametrize("schluessel, verboten", [
        ("rc_formular_dsgvo", "Datenschutzerklärung"),
        ("si_ssl", "Domain-Übereinstimmung"),
        ("si_drittanbieter", "Karten"),
        ("bf_alt", "sinnvoll"),
        ("se_lokal", "NAP"),
        ("dg_mobil", "Tap-Targets"),
        ("cv_cta", "ergebnisorientiert"),
    ])
    def test_der_hinweis_verspricht_die_ungeprueste_sache_nicht_mehr(
            self, schluessel, verboten):
        assert verboten not in find_criterion(schluessel).hint

    def test_ih_aktualitaet_ist_als_oder_beschrieben(self):
        """Gewertet wird `copyright_current OR has_dated_content`."""
        hinweis = find_criterion("ih_aktualitaet").hint
        assert " oder " in hinweis

    def test_kein_hinweis_benutzt_ein_wort_das_der_prompt_verbietet(self):
        """`audit_ai.py` untersagt dem Modell bestimmte Woerter in der Ausgabe.

        Ein Kriterienhinweis, der genau diese Woerter fuehrt, verlangt etwas,
        das der Prompt an anderer Stelle untersagt — und das Modell kann es
        nicht liefern, ohne sich selbst zu widersprechen. Gefunden bei
        `ih_textqualitaet` und „Worthuelsen" (S3.12).
        """
        import pathlib
        import re

        from services.audit_criteria import all_criteria

        prompt = (pathlib.Path(__file__).resolve().parent.parent
                  / "services" / "audit_ai.py").read_text(encoding="utf-8")
        # Die Tabu-Zeile fuehrt die Woerter in deutschen Anfuehrungszeichen.
        anfang = prompt.find("sind tabu")
        assert anfang != -1, "Die Tabu-Liste im Prompt ist verschwunden"
        tabu = set(re.findall(r"„([^“\"]+)[“\"]", prompt[anfang:anfang + 400]))
        assert tabu, "Keine Tabu-Woerter gefunden — hat sich die Schreibweise geaendert?"

        verstoesse = [
            f"{c.key}: {wort}"
            for c in all_criteria() for wort in tabu
            if wort.lower() in c.hint.lower()
        ]
        assert not verstoesse, (
            "Ein Kriterienhinweis fuehrt ein Wort, das der Bewertungsprompt "
            f"dem Modell untersagt: {verstoesse}"
        )
