"""Die Barrierefreiheits-Gruppen werden gelesen, nicht nur berechnet (S1).

**Der Befund aus C1.** `A11Y_AUDIT_GROUPS` in `services/audit_pagespeed.py`
berechnet vier Gruppen. Zwei davon liest niemand:

* **`screenreader`** liefert unter anderem `html-has-lang` und `label` —
  genau die zwei Prüfungen, die der Kriterienhinweis von `bf_semantik`
  verspricht („lang-Attribut, Labels"). Bewertet wurden sie nie; `bf_semantik`
  zählte nur H1 und Überschriftenhierarchie aus dem DOM.
* **`lesbarkeit`** liefert `font-size`. `dg_typografie` **schätzt** die
  Schriftgröße derweil mit einem Sprachmodell.

**Warum eigene Gruppen und nicht die vorhandenen.** Die Gruppen liefern nur
Mittelwerte. Wer `screenreader` als Ganzes an `bf_semantik` hängt, zieht
`image-alt` mit — und das zählt `bf_alt` bereits. Das wäre eine Doppelwertung
derselben Sorte, die C4 an anderer Stelle auflistet. Deshalb bekommen die
gelesenen Prüfungen eigene Gruppen; `screenreader` und `lesbarkeit` bleiben
für die Fehlerliste im Bericht erhalten.

**Keine Punktänderung.** Beide Kriterien behalten ihre Höchstpunktzahl; die
Katalogsumme bleibt 103 (Entscheidung aus C4, Szenario B).
"""
import pytest

from services.audit_criteria import Source, find_criterion
from services.audit_pagespeed import A11Y_AUDIT_GROUPS


class TestDieGruppenSindGeschnittenWieGelesen:
    def test_es_gibt_eine_gruppe_fuer_bf_semantik(self):
        assert "semantik" in A11Y_AUDIT_GROUPS
        assert set(A11Y_AUDIT_GROUPS["semantik"]) == {"html-has-lang", "label"}

    def test_es_gibt_eine_gruppe_fuer_dg_typografie(self):
        assert "typografie" in A11Y_AUDIT_GROUPS
        assert set(A11Y_AUDIT_GROUPS["typografie"]) == {"font-size"}

    def test_die_neue_gruppe_zieht_kein_alt_text_mit(self):
        """`image-alt` zaehlt `bf_alt` — zweimal waere eine Doppelwertung."""
        assert "image-alt" not in A11Y_AUDIT_GROUPS["semantik"]
        assert "image-alt" not in A11Y_AUDIT_GROUPS["typografie"]


def _fakten(*, lang_ok=True, label_ok=True, font_ok=True,
            h1=True, hierarchie=True, mit_psi=True) -> dict:
    """Fakten in der Form, die `score_audit` erwartet."""
    if not mit_psi:
        return {"psi_mobile": {"collected": False},
                "qa": {"h1_genau_eins": h1, "heading_struktur_ok": hierarchie}}
    return {
        "psi_mobile": {
            "collected": True,
            "a11y_audits": {
                "semantik": (int(lang_ok) + int(label_ok)) / 2,
                "typografie": float(font_ok),
                "kontrast": 1.0, "tastatur": 1.0,
                "screenreader": 1.0, "lesbarkeit": 1.0,
            },
            "accessibility_score": 95,
        },
        "qa": {"h1_genau_eins": h1, "heading_struktur_ok": hierarchie},
    }


class TestBfSemantik:
    """Zwei Haelften zu je einem Punkt: Struktur und Screenreader-Grundlagen.

    Die vorherige Fassung gab je einen Punkt fuer „genau eine H1" und
    „Hierarchie in Ordnung". Die beiden ueberlappen sich: `heading_struktur_ok`
    verlangt selbst schon genau eine H1. „Hierarchie ohne H1" gibt es nicht —
    die zweite Stufe war also nie unabhaengig.
    """

    @staticmethod
    def _punkte(fakten) -> tuple:
        from services.audit_scoring import score_audit

        ergebnis = score_audit(fakten)
        return (ergebnis["items"].get("bf_semantik"),
                ergebnis["sources"].get("bf_semantik"))

    def test_alles_in_ordnung_gibt_die_volle_punktzahl(self):
        punkte, quelle = self._punkte(_fakten())
        assert punkte == 2
        assert quelle == Source.MEASURED.value

    def test_ohne_lang_und_labels_bleibt_nur_die_struktur(self):
        punkte, _ = self._punkte(_fakten(lang_ok=False, label_ok=False))
        assert punkte == 1

    def test_ohne_saubere_hierarchie_bleibt_nur_der_screenreader_teil(self):
        punkte, _ = self._punkte(_fakten(hierarchie=False))
        assert punkte == 1

    def test_ohne_pagespeed_gilt_das_kriterium_als_nicht_erhoben(self):
        """Sonst waere es nur halb pruefbar und wuerde voll gewertet.

        Genau davor warnte der Kommentar an der alten Stelle — ein stiller
        Abzug fuer etwas, das der Betrieb nicht zu verantworten hat.
        """
        punkte, quelle = self._punkte(_fakten(mit_psi=False))
        assert quelle == Source.NOT_COLLECTED.value


class TestDgTypografie:
    @staticmethod
    def _quelle(fakten) -> str:
        from services.audit_scoring import score_audit

        return score_audit(fakten)["sources"].get("dg_typografie")

    def test_mit_pagespeed_ist_es_gemessen_statt_geschaetzt(self):
        assert self._quelle(_fakten()) == Source.MEASURED.value

    def test_der_katalog_fuehrt_es_nicht_mehr_als_einschaetzung(self):
        assert find_criterion("dg_typografie").source is not Source.AI

    def test_ohne_pagespeed_gilt_es_als_nicht_erhoben(self):
        assert self._quelle(_fakten(mit_psi=False)) == Source.NOT_COLLECTED.value


class TestDieKatalogsummeBleibt:
    def test_einhundertdrei(self):
        """Entscheidung aus C4, Szenario B — kein `max_points` aendert sich."""
        from services.audit_criteria import all_criteria

        assert sum(c.max_points for c in all_criteria()) == 103
