# -*- coding: utf-8 -*-
"""Barrierefreiheit aus dem Browserlauf statt aus Lighthouse (L-153).

**Der Anlass (04.09.2026).** Vier der fuenf Barrierefreiheitskriterien kamen
aus Lighthouse, und Lighthouse kommt ueber PageSpeed. Faellt der Dienst aus,
bleibt von der Kategorie ein Kriterium uebrig — und der Bericht zeigt
„0 von 2", was wie ein Urteil ueber den Betrieb aussieht.

**Die Reihenfolge ist der Kern dieser Tests.** Lighthouse bleibt erste Quelle;
die Eigenmessung greift nur bei Ausfall. Waere es umgekehrt, verschoeben sich
Punktzahlen im Bestand, ohne dass sich am Massstab etwas geaendert haette.

**`bf_lighthouse` bleibt ausdruecklich aussen vor.** Das Kriterium heisst
„Lighthouse-Accessibility-Score" und **ist** dieser Wert; ihn durch eine eigene
Zahl zu ersetzen waere ein anderes Kriterium, keine andere Messung desselben.
"""
from services import a11y_browser
from services.audit_criteria import Source
from services.audit_scoring import score_audit

from test_audit_scoring import _fakten

SAUBER = {"collected": True, "kontrast_geprueft": 120, "kontrast_verstoesse": 0,
          "kontrast_nicht_messbar": 0,
          "kontrast_beispiele": [], "schrift_geprueft": 120, "schrift_zu_klein": 0,
          "fokussierbar": 40, "positive_tabindex": 0, "skiplink": True}
MAENGEL = {**SAUBER, "kontrast_verstoesse": 3,
           "kontrast_beispiele": ["Jetzt anfragen (2,9:1)"],
           "schrift_zu_klein": 5, "skiplink": False, "positive_tabindex": 2}


# ── Die Umrechnung ────────────────────────────────────────────────────

def test_ohne_messung_gibt_es_keinen_wert():
    """Nicht null — sonst wird ein misslungener Lauf zum Mangel des Betriebs."""
    assert a11y_browser.kontrast_anteil({"collected": False}) is None
    assert a11y_browser.schrift_anteil({"collected": False}) is None
    assert a11y_browser.tastatur_anteil({"collected": False}) is None


def test_ohne_geprueften_text_gibt_es_keinen_wert():
    leer = {"collected": True, "kontrast_geprueft": 0, "kontrast_nicht_messbar": 0,
            "schrift_geprueft": 0, "fokussierbar": 0}
    assert a11y_browser.kontrast_anteil(leer) is None
    assert a11y_browser.schrift_anteil(leer) is None
    assert a11y_browser.tastatur_anteil(leer) is None


def test_die_umrechnung_ist_binaer_wie_das_lighthouse_audit():
    assert a11y_browser.kontrast_anteil(SAUBER) == 1.0
    assert a11y_browser.kontrast_anteil(MAENGEL) == 0.0
    assert a11y_browser.schrift_anteil(SAUBER) == 1.0
    assert a11y_browser.schrift_anteil(MAENGEL) == 0.0


def test_die_tastatur_verlangt_beides():
    assert a11y_browser.tastatur_anteil(SAUBER) == 1.0
    assert a11y_browser.tastatur_anteil({**SAUBER, "skiplink": False}) == 0.0
    assert a11y_browser.tastatur_anteil({**SAUBER, "positive_tabindex": 1}) == 0.0


# ── Die Reihenfolge in der Bewertung ──────────────────────────────────

def _ohne_pagespeed(a11y):
    return _fakten(psi_mobile={"collected": False}, a11y_browser=a11y)


def test_ohne_pagespeed_traegt_der_browserlauf_die_kategorie():
    """Vorher blieb von fuenf Kriterien eines uebrig."""
    ergebnis = score_audit(_ohne_pagespeed(SAUBER))

    assert ergebnis["items"]["bf_kontrast"] == 2
    assert ergebnis["items"]["bf_tastatur"] == 1
    assert ergebnis["items"]["dg_typografie"] == 2
    assert ergebnis["sources"]["bf_kontrast"] == Source.MEASURED.value


def test_bf_lighthouse_bleibt_ohne_pagespeed_nicht_erhoben():
    """Die Grenze der Eigenmessung, ausdruecklich festgehalten: Das Kriterium
    **ist** der Lighthouse-Wert."""
    ergebnis = score_audit(_ohne_pagespeed(SAUBER))

    assert ergebnis["sources"]["bf_lighthouse"] == Source.NOT_COLLECTED.value


def test_lighthouse_bleibt_die_erste_quelle():
    """Liegen beide vor, entscheidet Lighthouse — sonst verschoeben sich
    Punktzahlen im Bestand ohne Massstabsaenderung."""
    fakten = _fakten(a11y_browser=MAENGEL)      # Lighthouse sagt: alles gut
    ergebnis = score_audit(fakten)

    assert ergebnis["items"]["bf_kontrast"] == 2
    assert "Lighthouse" in ergebnis["belege"]["bf_kontrast"]


def test_ohne_beides_bleibt_es_nicht_erhoben():
    ergebnis = score_audit(_ohne_pagespeed({"collected": False}))

    assert ergebnis["sources"]["bf_kontrast"] == Source.NOT_COLLECTED.value
    assert ergebnis["sources"]["dg_typografie"] == Source.NOT_COLLECTED.value


# ── Der Beleg ─────────────────────────────────────────────────────────

def test_der_beleg_sagt_woher_die_zahl_kommt():
    belege = score_audit(_ohne_pagespeed(MAENGEL))["belege"]

    assert "Am gerenderten Dokument" in belege["bf_kontrast"]
    assert "3 von 120" in belege["bf_kontrast"]
    assert "2,9:1" in belege["bf_kontrast"]
    assert "5 von 120 Textstellen unter 12 px" in belege["dg_typografie"]


def test_der_tastaturbeleg_nennt_beide_teile():
    beleg = score_audit(_ohne_pagespeed(MAENGEL))["belege"]["bf_tastatur"]

    assert "offen:" in beleg
    assert "Sprungziel" in beleg


# ── Wann ein Urteil überhaupt trägt ───────────────────────────────────

def test_zu_wenige_messbare_stellen_ergeben_kein_urteil():
    """Am Gegenstand entstanden: Bei `neovendo.de` liessen sich 121 von 433
    Textstellen nicht aus Farben bestimmen — weisse Navigation in einem
    schwebenden Kopf ueber fremdem Inhalt. Ein „0 von 2" auf Grundlage einer
    Handvoll messbarer Stellen waere ein Urteil ohne Messung."""
    knapp = {**SAUBER, "kontrast_geprueft": 5, "kontrast_nicht_messbar": 200,
             "kontrast_verstoesse": 1}

    assert a11y_browser.kontrast_anteil(knapp) is None


def test_unter_der_haelfte_messbar_ergibt_kein_urteil():
    haelfte = {**SAUBER, "kontrast_geprueft": 40, "kontrast_nicht_messbar": 200,
               "kontrast_verstoesse": 2}

    assert a11y_browser.kontrast_anteil(haelfte) is None


def test_der_gemessene_fall_traegt_weiterhin():
    """Die echten Zahlen von `neovendo.de` nach der Haertung: 312 messbar,
    18 Verstoesse, 121 nicht bestimmbar — das ist ein Urteil wert."""
    echt = {**SAUBER, "kontrast_geprueft": 312, "kontrast_nicht_messbar": 121,
            "kontrast_verstoesse": 18}

    assert a11y_browser.kontrast_anteil(echt) == 0.0
