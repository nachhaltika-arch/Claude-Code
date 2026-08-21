"""Das Audit bewertet die ganze Website, nicht nur die Startseite.

Bis zum 21.08.2026 lud `collect_facts` genau ein Dokument. Was dadurch nie
gemessen wurde, steht auf Handwerkerseiten typischerweise nicht auf der
Startseite — und genau diese Faelle stehen hier als Test:

* das **Kontaktformular** liegt auf `/kontakt`,
* die **Leistungsseiten** sind eigene Seiten,
* der **Tracker** laedt erst auf der Kontaktseite.

Der Test faehrt `collect_facts` mit einem erfundenen Netz. Die
domainweiten Erhebungen — PageSpeed, TLS, Hosting, Linkpruefer — sind dabei
abgeschaltet: Sie aendern sich durch die Unterseiten nicht und brauchen ein
echtes Netz.
"""
import asyncio

import pytest

from services import audit_runner

SEITEN = {
    "https://firma.de/": """
        <html><body>
          <a href="/kontakt">Kontakt</a>
          <a href="/leistungen/waermepumpe">Wärmepumpe</a>
          <h1>Heizung vom Fachbetrieb</h1>
        </body></html>""",
    "https://firma.de/kontakt": """
        <html><body>
          <script src="https://www.googletagmanager.com/gtag/js"></script>
          <a href="tel:+4926112345">Anrufen</a>
          <form action="/senden" method="post">
            <input name="name"><textarea name="text"></textarea>
            <input type="checkbox" name="dsgvo"> Datenschutz gelesen
          </form>
        </body></html>""",
    "https://firma.de/leistungen/waermepumpe": """
        <html><body><h1>Wärmepumpe</h1>
          <a href="/leistungen/wallbox">Wallbox</a>
          <a href="#anfrage">Jetzt Angebot anfordern</a>
        </body></html>""",
}


class _Antwort:
    def __init__(self, text, status=200):
        self.text = text
        self.status_code = status
        self.headers = {"content-type": "text/html; charset=utf-8"}
        self.url = "https://firma.de/"


@pytest.fixture
def erfundenes_netz(monkeypatch):
    """Ein Netz, das nur die drei Seiten oben kennt."""
    async def _hole(_client, url, **_kwargs):
        if url in SEITEN:
            return _Antwort(SEITEN[url])
        return _Antwort("", status=404)

    monkeypatch.setattr(audit_runner, "fetch_guarded", _hole)
    monkeypatch.setattr("services.audit_seiten.fetch_guarded", _hole)
    monkeypatch.setattr("services.audit_seiten.is_same_host",
                        lambda url, basis: url.startswith("https://firma.de"))

    # Domainweite Erhebungen brauchen ein echtes Netz und aendern sich durch
    # die Unterseiten nicht.
    async def _leer(*_a, **_k):
        return {"collected": False}

    for name in ("fetch_pagespeed",):
        monkeypatch.setattr(audit_runner, name, _leer)
    for name in ("_run_qa_scanner", "_run_hosting", "_run_link_check"):
        monkeypatch.setattr(audit_runner, name, _leer)
    monkeypatch.setattr(audit_runner.collectors, "check_legal_pages", _leer)
    monkeypatch.setattr(audit_runner.collectors, "check_https_redirect", _leer)
    monkeypatch.setattr(audit_runner.collectors, "check_tls", lambda _u: {"collected": False})

    async def _keine_groessen(_urls):
        return 0
    monkeypatch.setattr(audit_runner.collectors, "_sample_image_sizes", _keine_groessen)


def _fakten():
    return asyncio.run(audit_runner.collect_facts("https://firma.de/",
                                                  current_year=2026))


def test_alle_gefundenen_seiten_werden_geprueft(erfundenes_netz):
    fakten = _fakten()

    assert fakten["seiten"]["geprueft"] == 3
    assert sorted(fakten["seiten"]["seiten"]) == sorted(SEITEN)


def test_das_formular_auf_der_kontaktseite_wird_gefunden(erfundenes_netz):
    """Der wichtigste Einzelfall: Auf der Startseite steht kein Formular."""
    fakten = _fakten()

    assert fakten["forms"]["total"] == 1
    assert fakten["forms"]["with_consent"] == 1


def test_die_telefonnummer_auf_der_kontaktseite_zaehlt(erfundenes_netz):
    assert _fakten()["contact"]["tel_link"] is True


def test_der_tracker_auf_der_kontaktseite_zaehlt(erfundenes_netz):
    """Wer nur die Startseite prueft, bescheinigt Datensparsamkeit, die es
    nicht gibt."""
    assert "google_analytics" in _fakten()["third_parties"]["tracking_services"]


def test_leistungsseiten_aus_unterseiten_zaehlen_mit(erfundenes_netz):
    """`/leistungen/wallbox` ist nur von der Wärmepumpen-Seite verlinkt."""
    pfade = [s["pfad"] for s in _fakten()["services"]["seiten"]]

    assert "/leistungen/waermepumpe" in pfade
    assert "/leistungen/wallbox" in pfade


def test_woerter_aller_seiten_zaehlen(erfundenes_netz):
    fakten = _fakten()

    assert fakten["word_count"] > 10


def test_die_ki_bekommt_text_von_mehreren_seiten(erfundenes_netz):
    """Vorher sah die Einschaetzung 6.000 Zeichen der Startseite. Jetzt
    denselben Umfang, aber ueber die Seiten verteilt."""
    text = _fakten()["page_text"]

    assert "https://firma.de/kontakt" in text
    assert "Wärmepumpe" in text


def test_navigation_bleibt_die_der_startseite(erfundenes_netz):
    """Sie ist auf allen Seiten dieselbe — sie je Seite zu erheben, waere
    dasselbe Ergebnis zum Vielfachen der Abrufe."""
    assert _fakten()["navigation"]["collected"] is True


def test_unerreichbare_startseite_bleibt_unerreichbar(monkeypatch):
    """Die Seitensuche darf an diesem Fall nichts aendern."""
    async def _tot(*_a, **_k):
        raise RuntimeError("nichts da")

    monkeypatch.setattr(audit_runner, "fetch_guarded", _tot)
    monkeypatch.setattr(audit_runner, "HOMEPAGE_RETRY_DELAY", 0)

    fakten = asyncio.run(audit_runner.collect_facts("https://firma.de/"))

    assert fakten["reachable"] is False


def test_der_umfang_steht_in_der_zusammenfassung(erfundenes_netz):
    """Ergebnisse von vor dem 21.08.2026 kannten nur die Startseite — ohne die
    Zahl vergleicht jemand zwei unvergleichbare Noten."""
    zusammen = audit_runner.summarise_facts(_fakten())

    assert zusammen["seiten_geprueft"] == 3
    assert zusammen["seiten_quelle"] == "interne Verlinkung"
