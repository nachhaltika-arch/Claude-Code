# -*- coding: utf-8 -*-
"""
Der Wochenlauf misst nur, wofür bezahlt wird — und schreibt nichts ohne Zahlen.

**Warum das zwei getrennte Zusagen sind.** Ein Lauf für alle Projekte belastet
die Kostenstelle jedes Betriebs, der nie danach gefragt hat. Und ein Lauf ohne
angebundenes System erzeugte einen Verlaufseintrag ohne Zahlen — später sähe
die Kurve wie ein Einbruch aus, den es nie gab.
"""
from unittest.mock import patch

import pytest

from automations import job_ki_sichtbarkeit as job

pytestmark = pytest.mark.usefixtures("app")


def test_ohne_angebundenes_system_laeuft_nichts():
    """Kein Schlüssel heißt: nicht laufen, nicht messen, nicht schreiben."""
    with patch.object(job, "job_ki_sichtbarkeit_woechentlich",
                      wraps=job.job_ki_sichtbarkeit_woechentlich):
        with patch("services.ki_anbieter.konfigurierte_anbieter", return_value=[]):
            bilanz = job.job_ki_sichtbarkeit_woechentlich()

    # `berichtet` kam am 25.08.2026 dazu: Der Lauf verschickt seither den
    # Wochenbericht, den die Kundenkarte vorher nur versprochen hatte.
    assert bilanz == {"abonnenten": 0, "gemessen": 0, "uebersprungen": 0,
                      "fehler": 0, "berichtet": 0}


def test_nur_laufende_abos_werden_gemessen():
    """Wer nicht zahlt, wird nicht gefragt — der Lauf kostet Geld."""
    assert job.LAUFENDE_ABOS == ("active", "trialing"), (
        "Die Probezeit gehört dazu, gekündigte Abos nicht")


def test_drei_fragen_je_lauf():
    """Dieselbe Grenze wie am Endpunkt — fünf verdoppeln die Kosten."""
    assert job.FRAGEN_JE_LAUF == 3


def test_der_job_haengt_im_planer():
    """Ein Job, den niemand registriert, läuft nie — und fällt nicht auf."""
    from automations import scheduler

    quelle = (scheduler.__file__)
    with open(quelle, encoding="utf-8") as datei:
        text = datei.read()
    assert "job_ki_sichtbarkeit_woechentlich" in text
    assert 'id="ki_sichtbarkeit_woechentlich"' in text
    assert 'day_of_week="mon"' in text, "der Lauf soll wöchentlich sein, nicht täglich"


def test_ohne_gewerk_oder_ort_wird_uebersprungen_statt_geraten():
    """Eine Frage nach einem erfundenen Ort misst den falschen Markt."""
    from services.ki_sichtbarkeit import baue_fragen

    assert baue_fragen("", "Kassel") == []
    assert baue_fragen("Heizung", "") == []
    assert len(baue_fragen("Heizung", "Kassel", max_fragen=3)) == 3


# ── Der erste Lauf nach dem Kauf ─────────────────────────────────────

def test_die_erstmessung_haengt_am_kauf():
    """Das Abo verkauft eine Kurve — die braucht einen ersten Punkt.

    Wer heute kauft und bis zum Montagslauf eine leere Ansicht sieht, hat
    sechs Tage lang den Eindruck, nichts bekommen zu haben.
    """
    import inspect

    from routers import geo_payments

    quelle = inspect.getsource(geo_payments._run_geo_automation_after_purchase)
    assert "_erste_nennungsmessung" in quelle


def test_die_erstmessung_scheitert_leise():
    """Eine fehlende Messung darf den Kaufvorgang nicht umwerfen."""
    from unittest.mock import patch

    from routers import geo_payments

    with patch("services.ki_anbieter.konfigurierte_anbieter", return_value=[]):
        # Kein Schluessel: Der Aufruf kehrt zurueck, ohne zu werfen.
        geo_payments._erste_nennungsmessung(1, "Muster", "muster.de", "Heizung", "Kassel")

    with patch("services.ki_anbieter.konfigurierte_anbieter", return_value=["x"]):
        # Ohne Ort wird nicht geraten — auch hier kein Wurf.
        geo_payments._erste_nennungsmessung(1, "Muster", "muster.de", "Heizung", "")
