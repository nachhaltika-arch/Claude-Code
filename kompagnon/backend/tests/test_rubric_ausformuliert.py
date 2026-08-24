"""Jedes eingeschaetzte Kriterium hat ein gestuftes Rubric (A8, S8.2).

**Der Befund.** Das Modell bekam je Kriterium **eine Zeile**: „Wirkt das
Layout zeitgemaess oder veraltet?" — fuer drei Punkte. Was zwei Punkte von
einem unterscheidet, stand nirgends. BEFUND-C1 hat das nachgelesen und
bestaetigt; die acht Alterungsmerkmale, die A8 verlangt, standen nirgends.

**Zwei Folgen, und beide sind belegt.** A9 (Wiederholbarkeit) ist ohne Rubric
nicht herstellbar — Kapitel 3 verspricht sie trotzdem. Und BEFUND-C3 fuehrt
vier Verdachtsfaelle auf Doppelwertung, die unpruefbar blieben, weil die
eingeschaetzten Kriterien keine Feldliste hatten.

**Warum im Katalog.** Kapitel 10 druckt die Merkmale mit dem Vorbehalt, sie
seien „meine Zusammenstellung, nicht aus dem Code extrahiert". Steht das
Rubric im Katalog, faellt der Vorbehalt weg.
"""
import re

from services.audit_ai import _rubric
from services.audit_criteria import ai_criteria


def test_jedes_eingeschaetzte_kriterium_hat_ein_rubric():
    # Arrange / Act
    ohne = [c.buch_code for c in ai_criteria() if not c.rubric.strip()]

    # Assert
    assert not ohne, (
        f"Ohne ausformuliertes Rubric: {ohne}. Eine Zeile Kurzhinweis fuer "
        "zwei oder drei Punkte laesst das Modell die Abstufung jedes Mal neu "
        "erfinden."
    )


def test_jedes_rubric_stuft_jede_erreichbare_punktzahl():
    """Von 0 bis zum Maximum muss jede Stufe beschrieben sein.

    Ein Rubric, das nur die volle Punktzahl und die Null nennt, laesst die
    Mitte offen — und genau dort entsteht die Streuung.
    """
    for crit in ai_criteria():
        stufen = set(re.findall(r"^(\d) =", crit.rubric, re.M))
        erwartet = {str(n) for n in range(crit.max_points + 1)}

        assert stufen == erwartet, (
            f"{crit.buch_code}: beschrieben sind {sorted(stufen)}, "
            f"erreichbar sind {sorted(erwartet)}."
        )


def test_jedes_rubric_grenzt_sich_gegen_nachbarkriterien_ab():
    """Die Zeile, die BEFUND-C3 pruefbar macht."""
    # Arrange / Act
    ohne = [c.buch_code for c in ai_criteria()
            if "Nicht Teil dieses Kriteriums" not in c.rubric]

    # Assert
    assert not ohne, (
        f"Ohne Abgrenzung: {ohne}. Ohne sie bleibt jeder Verdacht auf "
        "Doppelwertung unpruefbar — der Grund, aus dem vier Faelle in "
        "BEFUND-C3 offen stehen."
    )


def test_der_prompt_traegt_das_rubric_und_nicht_die_zeile():
    # Arrange / Act
    text = _rubric("K1")

    # Assert
    assert "3 = kein Alterungsmerkmal erkennbar" in text
    assert "Nicht Teil dieses Kriteriums" in text


def test_was_die_klasse_nicht_kennt_steht_nicht_im_prompt():
    """K6 ist keine Betriebsseite — Angebotsklarheit gilt dort nicht.

    Ein Kriterium im Prompt, das spaeter verworfen wird, kostet Token und
    verleitet das Modell, es in der Zusammenfassung doch zu bemaengeln.
    """
    # Arrange / Act
    text = _rubric("K6")

    # Assert
    assert "cv_angebot" not in text
    assert "dg_aktualitaet" in text, "Gestaltung gilt fuer jede Seite."
