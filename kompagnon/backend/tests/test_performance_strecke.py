"""Von einer PageSpeed-Antwort bis zu P1–P4 (S6.3, Teilpruefung).

**Was S6.3 verlangt und was hier steht.** Der Auftrag will P1–P4 in einem
**echten** Lauf sehen. Am 24.08.2026 ging das lokal nicht: Der Schluessel in
der `.env` ist leer, und das anonyme Kontingent von PageSpeed v5 war
erschoepft (`reason: kontingent_ohne_api_key`). Die Live-Bestaetigung braucht
den Schluessel und gehoert auf den Server.

Was **hier** geprueft wird, ist die Strecke dazwischen: Kommt eine Antwort an,
tragen P1 bis P4 danach gemessene Werte — und nicht „nicht erhoben". Das
schliesst den Fall aus, dass die Erhebung laeuft und die Bewertung sie
trotzdem nicht sieht. Genau dieser Fall lag hier schon zweimal vor: Der
Altcode forderte die Barrierefreiheits-Kategorie an und warf sie weg, und
`accessibility_score` wurde erhoben, ohne dass ein Kriterium daran hing.

Die Antwort ist nachgebaut, nicht erfunden: Feldnamen und Verschachtelung
folgen der PSI-v5-Antwort, gegen die `_parse` geschrieben ist.
"""
from services.audit_pagespeed import _parse
from services.audit_criteria import Source


def _psi_antwort() -> dict:
    """Eine PSI-v5-Antwort in der Form, die der Endpunkt liefert."""
    return {
        "lighthouseResult": {
            "categories": {
                "performance": {"score": 0.93},
                "accessibility": {"score": 0.88},
            },
            "audits": {
                "largest-contentful-paint": {"numericValue": 2100.0},
                "cumulative-layout-shift": {"numericValue": 0.04},
                "total-blocking-time": {"numericValue": 120.0},
                "color-contrast": {"score": 1},
                "html-has-lang": {"score": 1},
                "label": {"score": 0},
                "font-size": {"score": 1},
            },
        },
        "loadingExperience": {
            "metrics": {"INTERACTION_TO_NEXT_PAINT": {"percentile": 180}},
        },
    }


def test_die_antwort_wird_zu_kennzahlen():
    # Arrange
    antwort = _psi_antwort()

    # Act
    psi = _parse(antwort, "mobile")

    # Assert
    assert psi["collected"] is True
    assert psi["performance_score"] == 93
    assert psi["lcp_seconds"] == 2.1
    assert psi["cls_value"] == 0.04
    assert psi["inp_ms"] == 180
    assert psi["inp_source"] == "crux_seite"


def test_p1_bis_p4_tragen_danach_gemessene_werte():
    from services.audit_scoring import score_audit

    # Arrange
    psi = _parse(_psi_antwort(), "mobile")

    # Act
    ergebnis = score_audit({"psi_mobile": psi})
    quellen = ergebnis["sources"]
    punkte = ergebnis["items"]

    # Assert
    for schluessel in ("tp_lcp", "tp_cls", "tp_inp", "tp_mobile"):
        assert quellen[schluessel] == Source.MEASURED.value, (
            f"{schluessel} gilt als nicht erhoben, obwohl die Antwort den Wert "
            "enthaelt — erhoben und weggeworfen ist schlimmer als gar nicht "
            "erhoben, weil es im Bericht wie eine Luecke der Website aussieht."
        )
    # 2,1 s LCP und 0,04 CLS liegen in der besten Stufe, 93 Punkte ebenfalls.
    assert punkte["tp_lcp"] == 4
    assert punkte["tp_cls"] == 3
    assert punkte["tp_inp"] == 2
    assert punkte["tp_mobile"] == 3


def test_ohne_antwort_wird_nichts_behauptet():
    """Gegenprobe: Ausbleiben darf nicht als null Punkte durchgehen."""
    from services.audit_scoring import score_audit

    # Arrange / Act
    ergebnis = score_audit({"psi_mobile": {"collected": False, "reason": "api_fehler"}})

    # Assert
    for schluessel in ("tp_lcp", "tp_cls", "tp_inp", "tp_mobile"):
        assert ergebnis["sources"][schluessel] == Source.NOT_COLLECTED.value
