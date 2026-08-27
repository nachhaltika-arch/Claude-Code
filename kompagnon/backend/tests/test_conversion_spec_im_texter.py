"""Die Conversion-Spec muss im Texter ankommen (L-15).

`docs/conversion-spec-shk.md` liegt seit Mai im Repo und ist laut ihrem
eigenen § 6 **verbindlich** für den `content_writer`. Bis zum 24.08.2026 kam
davon nichts an: Im Agenten gab es keinen Treffer auf „Hormozi", „Offer",
„Garantie" oder „Wertebox" — er schrieb Leistungen als Feature-Liste, ohne
bezifferte Garantien und ohne Wertebox.

**Warum ein eigenes Modul und nicht Text im Prompt.** Zwei Gründe:

1. Die Regeln aus § 7 sind **rechtlich** und nicht stilistisch —
   „Geld-zurück-Garantie" ist bei Werkverträgen (BGB § 631 ff.) nicht
   erfüllbar, „80 % Heizkosten gespart, garantiert" ist UWG § 5.
   Was abmahnfähig ist, gehört an eine benannte Stelle, nicht mitten in
   einen f-String.
2. Ein Prompt ist nicht prüfbar, eine Liste schon.

**Was diese Tests nicht können:** Sie prüfen, dass die Regeln im Auftrag
stehen, nicht dass das Modell sie befolgt. Das ist eine andere Frage und
braucht einen Lauf gegen ein echtes Modell.
"""
import pathlib
import re

import pytest

from agents.conversion_spec import (
    ANTI_MUSTER,
    PFLICHT_FELDER,
    spec_regeln,
    verbotene_formulierungen,
)

SPEC = pathlib.Path(__file__).resolve().parents[3] / "docs" / "conversion-spec-shk.md"


class TestDieRegelnStehenImAuftrag:
    def test_der_auftrag_nennt_die_value_equation(self):
        text = spec_regeln()
        assert "Outcome" in text
        assert "Zeit" in text or "Time" in text

    def test_der_auftrag_verlangt_bezifferte_garantien(self):
        text = spec_regeln().lower()
        assert "garantie" in text
        # Vage Qualitaetsversprechen sind genau das, was die Spec ersetzt
        assert "beziffert" in text or "konkret" in text

    def test_der_auftrag_verlangt_eine_wertebox(self):
        assert "Wertebox" in spec_regeln()

    def test_der_auftrag_verbietet_die_rechtlich_heiklen_formen(self):
        verboten = verbotene_formulierungen().lower()
        for muss in ("geld-zurück", "countdown", "anti-guarantee"):
            assert muss in verboten, f"{muss} fehlt in den Verboten"


class TestDieSpecUndDerCodeLaufenNichtAuseinander:
    def test_die_spec_liegt_noch_da(self):
        assert SPEC.exists(), f"{SPEC} fehlt — dann stimmt der Verweis nicht mehr"

    def test_jedes_anti_muster_hat_seine_entsprechung_in_der_spec(self):
        """Die Liste im Code darf nichts erfinden, was die Spec nicht sagt."""
        # Arrange
        spec_text = SPEC.read_text(encoding="utf-8").lower()

        # Act & Assert
        for muster in ANTI_MUSTER:
            stichwort = muster["stichwort"].lower()
            assert stichwort in spec_text, (
                f"„{stichwort}“ steht im Code, aber nicht mehr in der Spec — "
                "eine der beiden Seiten ist veraltet."
            )

    def test_die_zahl_der_anti_muster_stimmt_mit_abschnitt_7(self):
        """Wächst § 7, muss die Liste mitwachsen — sonst fehlt eine Regel."""
        # Arrange — die Aufzählungspunkte unter „## 7."
        text = SPEC.read_text(encoding="utf-8")
        ab = text.index("## 7.")
        bis = text.index("## ", ab + 4)
        punkte = re.findall(r"^- \*\*", text[ab:bis], re.MULTILINE)

        # Assert
        assert len(punkte) == len(ANTI_MUSTER), (
            f"§ 7 der Spec führt {len(punkte)} Anti-Muster, der Code "
            f"{len(ANTI_MUSTER)}. Die Spec ist verbindlich — der Code zieht nach."
        )


class TestDieAusgabeHatDieNeuenFelder:
    @pytest.mark.parametrize("feld", [
        "garantien", "wertebox", "cta_varianten", "einwand_faq",
    ])
    def test_das_json_geruest_fragt_das_feld_ab(self, feld):
        from agents.content_writer import ContentWriterAgent

        assert feld in PFLICHT_FELDER
        assert feld in ContentWriterAgent.antwort_geruest()


class TestDieVorschauZeigtDieNeuenBloecke:
    """Ein Feld, das ankommt und nicht gezeigt wird, ist nicht angeschlossen.

    Genau diese Klasse ist im System fuenfmal aufgetreten (L-55, L-79, L-11,
    L-101, L-58) — deshalb prueft dieser Teil nicht den Auftrag, sondern das
    Ergebnis: Was der Texter liefert, muss in der Vorschau auftauchen.
    """

    @staticmethod
    def _beispiel() -> dict:
        return {
            "hero_headline": "Waermepumpe in Koblenz",
            "hero_subline": "Festpreis in 7 Tagen, Installation in 30.",
            "about_text": "Wir sind ein Familienbetrieb.",
            "service_texts": {"Waermepumpe": "Sie heizen ab Tag 30 mit Strom."},
            "wertebox": {
                "titel": "Koblenzer Waermepumpen-Komplettpaket",
                "positionen": [
                    {"leistung": "Heizlastberechnung", "wert_eur": 490},
                    {"leistung": "BAFA-Antrag", "wert_eur": 350},
                ],
                "ankerwert_eur": 3200,
                "aktionspreis_eur": 1990,
            },
            "garantien": [
                {"versprechen": "Termintreue oder 250 EUR", "bezug": "je Werktag"},
            ],
            "einwand_faq": [
                {"einwand": "Funktioniert das im Altbau?",
                 "antwort": "In 92 % der Baujahre 1960-1990."},
            ],
            "faq_items": [{"question": "Wie lange?", "answer": "30 Tage."}],
            "local_cta": "Vor-Ort-Termin in Koblenz sichern",
        }

    @pytest.mark.parametrize("stueck", [
        "Komplettpaket", "1990 EUR", "Unsere Garantien", "Termintreue",
        "Was Kunden uns vorher fragen", "Altbau",
    ])
    def test_der_block_steht_in_der_vorschau(self, stueck):
        from routers.agents import _json_to_html

        assert stueck in _json_to_html(self._beispiel(), {})

    def test_die_reihenfolge_folgt_dem_offer_stack(self):
        """Spec § 3: Versprechen, Angebot, Leistungen, Garantie, Einwaende."""
        from routers.agents import _json_to_html

        # Act
        html = _json_to_html(self._beispiel(), {})
        folge = [
            html.index(s) for s in (
                "Waermepumpe in Koblenz", "Komplettpaket", "Unsere Leistungen",
                "Unsere Garantien", "Was Kunden uns vorher fragen",
            )
        ]

        # Assert
        assert folge == sorted(folge), (
            "Die Vorschau haelt die Reihenfolge aus Spec § 3 nicht ein — "
            "Offer-Stack-Sequencing ist Teil der Wirkung, nicht Kosmetik."
        )

    def test_fehlende_felder_erzeugen_keinen_leeren_kasten(self):
        """Ein alter Texter-Lauf ohne die neuen Felder darf nichts kaputt machen."""
        from routers.agents import _json_to_html

        # Arrange — genau die Form von vor dem 24.08.2026
        alt = {"hero_headline": "Titel", "about_text": "Text",
               "faq_items": [], "local_cta": "CTA"}

        # Act
        html = _json_to_html(alt, {})

        # Assert
        assert "Unsere Garantien" not in html
        assert "Komplettpaket" not in html
        assert "Titel" in html
