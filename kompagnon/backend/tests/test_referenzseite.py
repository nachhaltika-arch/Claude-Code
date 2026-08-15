"""
Die Erhebung, gemessen an einer festen Referenz-Website.

Schritt 6 des Anforderungskatalogs. Die übrigen Tests prüfen, ob aus Fakten
die richtigen Punkte werden; dieser prüft, ob aus einer Website die richtigen
Fakten werden — die Hälfte, in der bisher jeder Fehler saß.

Die Referenz steht in ``tests/referenzseite.py`` und ist festgeschrieben.
Ändert sich hier ein Wert, hat sich die Erhebung geändert: entweder gewollt,
dann gehört der neue Wert hierher, oder nicht, dann ist es ein Fehler.

Was von außen kommt und keine Website ist — PageSpeed, TLS-Handschlag,
Link-Prüfung — wird ersetzt. Es gehört nicht zu dem, was hier gemessen wird.
"""
import asyncio
from urllib.parse import urlparse

import httpx
import pytest

from services import audit_collectors as collectors
from services import audit_runner
from services.audit_scoring import score_audit
from tests import referenzseite as ref


class AntwortAttrappe:
    def __init__(self, status_code, text, content_type="text/html"):
        self.status_code = status_code
        self.text = text
        self.content = text.encode("utf-8")
        self.headers = dict(ref.KOPFZEILEN, **{"content-type": content_type})
        self.url = ref.BASIS

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("Fehler", request=None, response=None)


def _antwort_fuer(url: str) -> AntwortAttrappe:
    pfad = urlparse(url).path or "/"
    if pfad in ref.SEITEN:
        code, inhalt, typ = ref.SEITEN[pfad]
        return AntwortAttrappe(code, inhalt, typ)
    return AntwortAttrappe(404, "<html><title>Nicht gefunden</title></html>")


class ClientAttrappe:
    """Beantwortet jede Anfrage aus der Referenz — egal welches Modul fragt."""

    def __init__(self, **_kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def aclose(self):
        return None

    async def get(self, url, **_kw):
        return _antwort_fuer(url)

    async def head(self, url, **_kw):
        return _antwort_fuer(url)


@pytest.fixture
def referenz(monkeypatch):
    """Lenkt alle Aussenkontakte der Erhebung auf die Referenz um."""
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: ClientAttrappe(**kw))

    async def kein_pagespeed(*_a, **_kw):
        # Ohne Schluessel ist das der echte Zustand: nicht erhoben.
        return {"collected": False, "reason": "kein Schlüssel im Test"}

    def tls_gueltig(_url):
        return {"collected": True, "valid": True, "days_remaining": 90,
                "issuer": "Test-CA", "reason": ""}

    def keine_toten_links(_url):
        return {"broken_links": [], "checked": 12}

    monkeypatch.setattr(audit_runner, "fetch_pagespeed", kein_pagespeed)
    monkeypatch.setattr(collectors, "check_tls", tls_gueltig)
    monkeypatch.setattr("services.link_checker.LinkChecker.check_links",
                        staticmethod(keine_toten_links))

    async def erreichbar(url):
        antwort = _antwort_fuer(url)
        return {"reachable": True, "html": antwort.text, "status_code": 200,
                "final_url": url, "headers": antwort.headers}

    monkeypatch.setattr(audit_runner, "fetch_homepage", erreichbar)


@pytest.fixture
def fakten(referenz):
    return asyncio.run(audit_runner.collect_facts(
        ref.BASIS + "/", company_name="Referenz GmbH", city="Musterstadt"))


# ── Die Erhebung ───────────────────────────────────────────────────

def test_die_referenzseite_ist_erreichbar(fakten):
    assert fakten["reachable"] is True


def test_der_qa_scan_liest_die_seite(fakten):
    qa = fakten["qa"]

    assert qa["title_vorhanden"] is True
    assert qa["canonical_vorhanden"] is True
    assert qa["schema_markup"] is True
    assert qa["mobile_viewport"] is True
    assert qa["h1_genau_eins"] is True


def test_robots_und_sitemap_werden_gefunden(fakten):
    qa = fakten["qa"]

    assert qa["robots_txt"] is True
    assert qa["sitemap_xml"] is True
    assert qa["robots_txt_indexiert"] is True


def test_die_geo_pruefpunkte_werden_erhoben(fakten):
    qa = fakten["qa"]

    # Die Datei liegt unter dem Namen der Konvention — frueher wurde
    # /llm.txt gesucht und die Seite galt als ohne.
    assert qa["llms_txt"] is True
    # Die robots.txt nimmt nur /anfrage aus, sie sperrt niemanden aus.
    assert qa["robots_ai_friendly"] is True
    assert qa["gesperrte_ki_crawler"] == []


def test_die_rechtsseiten_werden_geladen_und_geprueft(fakten):
    legal = fakten["legal"]

    assert legal["impressum"]["reachable"] is True
    assert legal["impressum"]["complete"] is True
    assert legal["datenschutz"]["reachable"] is True
    assert legal["datenschutz"]["complete"] is True


def test_die_zusammenfassung_reicht_alles_weiter(fakten):
    summary = audit_runner.summarise_facts(fakten)

    assert summary["ssl_ok"] is True
    assert summary["impressum_ok"] is True
    assert summary["datenschutz_ok"] is True
    assert summary["llms_txt"] is True
    assert summary["robots_ai_friendly"] is True
    assert summary["structured_data"] is True
    # Ohne Schluessel bleibt PageSpeed unerhoben — und sagt das auch.
    assert summary["pagespeed_collected"] is False


# ── Die Stammdaten, die vor dem Audit erhoben werden ───────────────

def test_der_scraper_liest_firma_ort_und_kontakt(referenz):
    # Der Scraper laeuft vor der Erhebung und fuellt, was niemand eintippt.
    # Die Anschrift der Referenz steht in benachbarten Elementen — genau die
    # Stelle, an der der Ort frueher verschwand.
    from services.scraper import scrape_website

    ergebnis = asyncio.run(scrape_website(ref.BASIS + "/"))

    assert ergebnis["company_name"]
    assert ergebnis["city"] == "Musterstadt"
    assert ergebnis["email"] == "info@referenz-heizung.de"
    assert ergebnis["phone"]


def test_der_scraper_klebt_die_mailadresse_nicht_an_die_nummer(referenz):
    # „69705880info@firma.de" — derselbe fehlende Trenner, andere Wirkung.
    from services.scraper import scrape_website

    ergebnis = asyncio.run(scrape_website(ref.BASIS + "/"))

    assert ergebnis["email"].startswith("info@")


# ── Die Bewertung dieser Fakten ────────────────────────────────────

@pytest.fixture
def bewertung(fakten):
    # Die Klasse kommt sonst aus der KI-Erkennung; hier wird sie gesetzt,
    # damit der Test nicht am Modell haengt.
    erkennung = {"branche": "Heizung und Sanitär", "branchenklasse": "K1"}
    return score_audit(fakten, erkennung)


def test_nicht_erhobenes_zaehlt_nicht_gegen_die_seite(bewertung):
    # PageSpeed fehlt, also duerfen die Core Web Vitals nicht als Null gelten
    quellen = bewertung["sources"]

    assert quellen.get("tp_lcp") == "nicht_erhoben"
    assert quellen.get("tp_cls") == "nicht_erhoben"


# Der festgeschriebene Stand der Referenz. Ändert sich hier etwas, hat sich
# Erhebung oder Bewertung geändert — dann gehört der neue Wert hierher, mit
# Begründung im Commit. Performance steht auf 0 von 3, weil die Referenz keine
# Bilddateien ausliefert; die übrigen zwölf Punkte der Kategorie hängen an
# PageSpeed und gelten als nicht erhoben.
ERWARTETE_KATEGORIEN = {
    "recht_compliance": (20, 20),
    "sicherheit": (8, 8),
    "performance": (0, 3),
    "barrierefreiheit": (4, 4),
    "seo": (12, 15),
    "design": (1, 1),
    "conversion": (8, 9),
    "inhalt": (2, 3),
}
ERWARTETE_PUNKTZAHL = 87
ERWARTETE_ABDECKUNG = 63


def test_die_referenzseite_erreicht_ihre_bekannte_punktzahl(bewertung):
    assert bewertung["total_score"] == ERWARTETE_PUNKTZAHL
    assert bewertung["coverage"] == ERWARTETE_ABDECKUNG


def test_jede_kategorie_erreicht_ihren_bekannten_stand(bewertung):
    gemessen = {c["key"]: (c["score"], c["max"]) for c in bewertung["categories"]}

    assert gemessen == ERWARTETE_KATEGORIEN


def test_ohne_pagespeed_schrumpft_das_maximum_statt_der_punkte(bewertung):
    # Die zwölf PageSpeed-Punkte fallen aus Zähler *und* Nenner — sonst
    # verlöre jede Seite 15 Punkte, nur weil uns ein Schlüssel fehlt.
    performance = next(c for c in bewertung["categories"]
                       if c["key"] == "performance")

    assert performance["max"] < performance["nominal_max"]


def test_die_gemessenen_kriterien_haben_eine_quelle(bewertung):
    for schluessel, punkte in bewertung["items"].items():
        assert schluessel in bewertung["sources"], \
            f"{schluessel} hat Punkte, aber keine Angabe woher"
