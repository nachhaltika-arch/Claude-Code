# -*- coding: utf-8 -*-
"""
Der Wirkungsbericht nach 60 Tagen (GEO-01, Position 7).

Das Datenblatt führte ihn seit Mai mit dem Vermerk „braucht eine Messmethode,
die es noch nicht gibt". Seit dem 25.08.2026 gibt es sie. Diese Tests halten
fest, was er sagen darf — und vor allem, wann er **nichts** sagt.
"""
from datetime import datetime, timedelta

from services.geo_wirkungsbericht import (FRIST_TAGE, baue_wirkungsbericht,
                                          klartext)


class Analyse:
    """Ein Stellvertreter — der Bericht liest nur Felder."""

    def __init__(self, tage=61, verlauf=None, historie=None, auslieferung=None):
        self.auslieferung_am = (datetime.utcnow() - timedelta(days=tage)
                                if tage is not None else None)
        self.monitoring_history = historie if historie is not None else [
            {"date": "2026-06-26", "score": 42}, {"date": "2026-08-25", "score": 67}]
        self.ki_sichtbarkeit_verlauf = verlauf if verlauf is not None else [
            {"am": "2026-06-26", "anbieter": {"chatgpt": {"genannt_bei": 0}}},
            {"am": "2026-08-25", "anbieter": {"chatgpt": {"genannt_bei": 2},
                                              "gemini": {"genannt_bei": 1}}}]
        self.auslieferung = auslieferung or {"vollstaendig": True}


def test_vor_der_frist_wird_nichts_behauptet():
    """Eine Wirkung nach zwölf Tagen wäre eine Hochrechnung, keine Messung."""
    bericht = baue_wirkungsbericht(Analyse(tage=12))

    assert bericht["faellig"] is False
    assert "zu früh" in bericht["grund"]
    assert "geo_wert" not in bericht


def test_wenige_tage_vor_der_frist_genuegen():
    """Ein Bericht am 58. Tag ist derselbe wie am 60."""
    assert baue_wirkungsbericht(Analyse(tage=FRIST_TAGE - 2))["faellig"] is True


def test_ohne_auslieferung_gibt_es_keinen_bezugspunkt():
    bericht = baue_wirkungsbericht(Analyse(tage=None))

    assert bericht["faellig"] is False
    assert "keine ausgelieferte Fassung" in bericht["grund"]


def test_beide_groessen_werden_getrennt_ausgewiesen():
    """Lesbarkeit ist unser Werk, die Nennung nicht.

    Beides in eine Zahl zu pressen verkaufte eine Wirkung, die niemand
    zusichern kann.
    """
    bericht = baue_wirkungsbericht(Analyse())

    assert bericht["geo_wert"] == {"vorher": 42, "heute": 67, "veraenderung": 25}
    assert bericht["nennungen"]["vorher"] == 0
    assert bericht["nennungen"]["heute"] == 3
    assert bericht["nennungen"]["laeufe"] == 2


def test_ein_messpunkt_ist_kein_verlauf():
    """Lieber die Lücke benennen als eine Veränderung gegen nichts rechnen."""
    bericht = baue_wirkungsbericht(Analyse(
        verlauf=[{"am": "2026-08-25", "anbieter": {"chatgpt": {"genannt_bei": 2}}}]))

    assert bericht["nennungen"] is None
    assert "nicht genug Messungen" in bericht["nennungen_grund"]
    assert "nicht genug Messungen" in klartext(bericht)


def test_ein_system_ohne_schluessel_erzeugt_keinen_einbruch():
    """Nicht erhobene Systeme stehen nicht mit Null im Verlauf.

    Sonst zeigte die Kurve später einen Einbruch, den es nie gab — nur weil
    ein Schlüssel fehlte.
    """
    bericht = baue_wirkungsbericht(Analyse(verlauf=[
        {"am": "2026-06-26", "anbieter": {"chatgpt": {"genannt_bei": 2},
                                          "gemini": {"genannt_bei": 2}}},
        # Zweiter Lauf: Gemini fehlte, steht deshalb gar nicht drin.
        {"am": "2026-08-25", "anbieter": {"chatgpt": {"genannt_bei": 2}},
         "nicht_erhoben": ["gemini"]},
    ]))

    assert bericht["nennungen"]["veraenderung"] == -2
    # Die Zahl stimmt — sie ist eine Aussage über die **erhobenen** Systeme.
    # Der Verlaufseintrag weist die Lücke aus; der Bericht erfindet sie nicht weg.
    assert bericht["nennungen"]["laeufe"] == 2


def test_der_klartext_nennt_die_richtung():
    text = klartext(baue_wirkungsbericht(Analyse()))

    assert "gestiegen" in text
    assert "42 auf 67" in text


def test_der_endpunkt_ist_registriert():
    from main import app

    assert "/api/geo/{project_id}/wirkungsbericht" in app.openapi()["paths"]
