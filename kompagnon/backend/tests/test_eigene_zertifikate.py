# -*- coding: utf-8 -*-
"""
Die eigenen Domains stehen in der Ablaufüberwachung (B1.14e).

**Der Befund vom 25.08.2026.** `job_check_netlify_ssl` liest die Tabelle
`projects` — unsere eigenen Adressen stehen dort nicht, weil sie keine
Projekte sind. Eine davon, `homepage-standard.de`, wird im Buch **gedruckt**.
Ein abgelaufenes Zertifikat auf einer gedruckten Adresse lässt sich nicht
nachbessern.

Dasselbe Muster wie L-121: Der eigene Maßstab galt für Kunden und nicht für
uns.
"""
from unittest.mock import patch

from automations import job_eigene_zertifikate as job


def test_die_gedruckte_domain_wird_ueberwacht():
    """Sie steht im Buch — sie muss zuerst in der Liste stehen."""
    assert any("homepage-standard.de" in d for d in job.EIGENE_DOMAINS)
    assert any("homepagestandard.de" in d for d in job.EIGENE_DOMAINS)


def test_die_warngrenze_ist_die_des_kriteriums():
    """S1 zieht bei dreißig Tagen einen Punkt ab — früher zu warnen wäre
    Lärm, später zu warnen käme zu spät."""
    assert job.WARNGRENZE_TAGE == 30


def test_nicht_erreichbar_wird_nicht_als_abgelaufen_gemeldet():
    """Zwei verschiedene Nachrichten — dieselbe Regel wie überall sonst."""
    with patch("services.audit_collectors.check_tls",
               return_value={"collected": False, "reason": "timeout"}):
        befunde = job.job_eigene_zertifikate_pruefen()

    for eintrag in befunde:
        assert eintrag["collected"] is False
        assert eintrag.get("gueltig") is not True


def test_der_job_haengt_im_planer():
    """Ein Prüfer, den niemand auslöst, ist keiner."""
    import inspect

    from automations import scheduler

    quelle = inspect.getsource(scheduler)
    assert "job_eigene_zertifikate_pruefen" in quelle
    assert 'id="eigene_zertifikate"' in quelle
