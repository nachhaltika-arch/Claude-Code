"""
Die GEO-Prüfpunkte müssen erhoben werden, bevor sie im Bericht stehen.

Gefunden am 2026-08-15 im Bericht eines echten Betriebs: Die Seite „GEO &
KI-Sichtbarkeit" führte fünf Prüfpunkte, von denen **keiner** je gemessen
wurde. Die Felder `llms_txt`, `robots_ai_friendly`, `structured_data`,
`ai_mentions` existieren als Spalten, wurden aber nie befüllt; das PDF las
sie leer und druckte für jeden Punkt eine Handlungsaufforderung. Die
Roadmap verlangte daraufhin „robots.txt: GPTBot-Blockierung entfernen" von
einem Betrieb, dessen robots.txt niemanden blockiert.

Dazu ein zweiter Fehler: Der Scanner fragte `/llm.txt` ab. Die Konvention
heißt `llms.txt` — so steht sie auch im Infokasten desselben PDF.
"""
import asyncio

from services import qa_scanner
from services.audit_runner import summarise_facts


class AntwortAttrappe:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text
        self.headers = {}


class ClientAttrappe:
    """Antwortet je nach Pfad — der Scanner fragt mehrere Adressen ab."""

    def __init__(self, antworten, protokoll, **_kw):
        self._antworten = antworten
        self._protokoll = protokoll

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def get(self, url, **_kw):
        self._protokoll.append(url)
        for teil, antwort in self._antworten.items():
            if url.endswith(teil):
                return antwort
        return self._antworten.get("*", AntwortAttrappe(404, ""))


SEITE = '<html><head><title>Ein Betrieb aus Hamburg</title></head><body><h1>Heizung</h1></body></html>'


def _scanner_mit(monkeypatch, antworten):
    protokoll = []
    monkeypatch.setattr(
        qa_scanner.httpx, "AsyncClient",
        lambda **kw: ClientAttrappe(antworten, protokoll, **kw))
    return protokoll


# ── Die Konvention heißt llms.txt ──────────────────────────────────

def test_llms_txt_wird_unter_dem_richtigen_namen_gesucht(monkeypatch):
    # Arrange — nur /llms.txt existiert, /llm.txt nicht
    protokoll = _scanner_mit(monkeypatch, {
        "/llms.txt": AntwortAttrappe(200, "# Hinweise für KI-Systeme"),
        "/llm.txt": AntwortAttrappe(404, ""),
        "*": AntwortAttrappe(200, SEITE),
    })

    # Act
    checks = asyncio.run(qa_scanner.run_full_qa("https://firma.de"))["checks"]

    # Assert
    assert any(u.endswith("/llms.txt") for u in protokoll), \
        "Der Scanner hat /llms.txt nie abgefragt"
    assert checks["llms_txt"] is True


def test_die_alte_schreibweise_zaehlt_weiterhin(monkeypatch):
    # Arrange — wer die Datei schon als /llm.txt abgelegt hat, verliert nichts
    _scanner_mit(monkeypatch, {
        "/llms.txt": AntwortAttrappe(404, ""),
        "/llm.txt": AntwortAttrappe(200, "# Hinweise"),
        "*": AntwortAttrappe(200, SEITE),
    })

    # Act
    checks = asyncio.run(qa_scanner.run_full_qa("https://firma.de"))["checks"]

    # Assert
    assert checks["llms_txt"] is True


# ── Wer sperrt KI-Crawler wirklich? ────────────────────────────────

def test_eine_robots_txt_ohne_sperre_gilt_als_ki_freundlich():
    # Arrange — genau die robots.txt des geprüften Betriebs
    robots = "# Sitemap\nSitemap: https://firma.de/sitemap.xml\nUser-agent: *\n"

    # Act & Assert
    assert qa_scanner.gesperrte_ki_crawler(robots) == []


def test_eine_gptbot_sperre_wird_erkannt():
    # Arrange
    robots = "User-agent: *\nDisallow:\n\nUser-agent: GPTBot\nDisallow: /\n"

    # Act
    gesperrt = qa_scanner.gesperrte_ki_crawler(robots)

    # Assert
    assert "GPTBot" in gesperrt


def test_eine_sperre_fuer_alle_trifft_auch_die_ki_crawler():
    # Arrange
    robots = "User-agent: *\nDisallow: /\n"

    # Act & Assert
    assert qa_scanner.gesperrte_ki_crawler(robots)


def test_ein_teilpfad_ist_keine_sperre_der_website():
    # Arrange — nur ein Verzeichnis ausgenommen, nicht die Seite
    robots = "User-agent: GPTBot\nDisallow: /intern/\n"

    # Act & Assert
    assert qa_scanner.gesperrte_ki_crawler(robots) == []


def test_der_scanner_meldet_die_ki_freundlichkeit(monkeypatch):
    # Arrange
    _scanner_mit(monkeypatch, {
        "/robots.txt": AntwortAttrappe(200, "User-agent: GPTBot\nDisallow: /\n"),
        "*": AntwortAttrappe(200, SEITE),
    })

    # Act
    checks = asyncio.run(qa_scanner.run_full_qa("https://firma.de"))["checks"]

    # Assert
    assert checks["robots_ai_friendly"] is False
    assert "GPTBot" in checks["gesperrte_ki_crawler"]


# ── Die Werte müssen bis zur Speicherung durchkommen ───────────────

def test_die_geo_fakten_erreichen_die_zusammenfassung():
    # Arrange
    facts = {"qa": {"llms_txt": True, "robots_ai_friendly": False,
                    "schema_markup": True, "gesperrte_ki_crawler": ["GPTBot"]}}

    # Act
    summary = summarise_facts(facts)

    # Assert — ohne diese Zeilen bleiben die Spalten leer und das PDF rät
    assert summary["llms_txt"] is True
    assert summary["robots_ai_friendly"] is False
    assert summary["structured_data"] is True


def test_ohne_erhebung_bleiben_die_geo_fakten_unbekannt():
    # Arrange — der QA-Scan ist ausgefallen
    facts = {"qa": {}}

    # Act
    summary = summarise_facts(facts)

    # Assert — nicht False, sondern unbekannt: False hieße „gemessen und nicht da"
    assert summary["llms_txt"] is None
    assert summary["robots_ai_friendly"] is None
    assert summary["structured_data"] is None
