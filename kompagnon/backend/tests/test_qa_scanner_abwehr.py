"""
Was der QA-Scanner sieht, wenn die fremde Seite ihn abweist.

Beobachtet an einem echten Betrieb (Lauf 80, 2026-08-15): Der Server
beantwortete die Kennung der Python-Bibliothek mit 403 — Startseite,
robots.txt und sitemap.xml gleichermaßen —, dieselbe Adresse mit einer
Browser-Kennung mit 200. Der Scanner löste keine Ausnahme aus, sondern
zergliederte die Fehlerseite: kein Canonical, keine sitemap.xml, kein
Schema. Das Protokoll wies die Nullen als „gemessen" aus, und die Seite
verlor rund dreizehn Punkte für Mängel, die sie nicht hat.

Zwei Dinge müssen deshalb gelten: Der Scanner fragt wie ein Browser, und
was er nicht laden konnte, meldet er als nicht erhoben — nie als Null.
"""
import asyncio

from services import qa_scanner


class AntwortAttrappe:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text
        self.headers = {}


class ClientAttrappe:
    """Ersetzt httpx.AsyncClient und schreibt die gesendeten Kennungen mit."""

    def __init__(self, protokoll, antwort, **kwargs):
        self._protokoll = protokoll
        self._antwort = antwort
        self._kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def get(self, url, **kwargs):
        kopfzeilen = {**(self._kwargs.get("headers") or {}),
                      **(kwargs.get("headers") or {})}
        self._protokoll.append((url, kopfzeilen.get("User-Agent", "")))
        return self._antwort


def _scanner_mit(monkeypatch, antwort):
    protokoll = []
    monkeypatch.setattr(
        qa_scanner.httpx, "AsyncClient",
        lambda **kwargs: ClientAttrappe(protokoll, antwort, **kwargs))
    return protokoll


SEITE_MIT_ALLEM = (
    '<html><head><title>Meisterbetrieb für Heizung und Sanitär</title>'
    '<link rel="canonical" href="https://firma.de/">'
    '<script type="application/ld+json">{"@type":"Plumber"}</script>'
    '</head><body><h1>Heizung</h1><h2>Wärmepumpe</h2></body></html>'
)


def test_abgewiesene_seite_gilt_als_nicht_erhoben(monkeypatch):
    # Arrange — der Server weist ab, wie der echte Betrieb es tat
    _scanner_mit(monkeypatch, AntwortAttrappe(403, "<html><title>403 Forbidden</title></html>"))

    # Act
    ergebnis = asyncio.run(qa_scanner.run_full_qa("https://firma.de"))

    # Assert — kein einziger Messwert, sonst zählt die Bewertung Nullen
    assert ergebnis["checks"] == {}
    assert "403" in str(ergebnis.get("error", ""))


def test_scanner_fragt_mit_browser_kennung(monkeypatch):
    # Arrange
    protokoll = _scanner_mit(monkeypatch, AntwortAttrappe(200, SEITE_MIT_ALLEM))

    # Act
    asyncio.run(qa_scanner.run_full_qa("https://firma.de"))

    # Assert — jede Abfrage trägt dieselbe Kennung wie die übrigen Erhebungen
    assert protokoll, "Der Scanner hat gar nicht abgefragt"
    for adresse, kennung in protokoll:
        assert "Mozilla/5.0" in kennung, f"{adresse} ohne Browser-Kennung"


def test_erreichbare_seite_wird_weiterhin_gemessen(monkeypatch):
    # Arrange
    _scanner_mit(monkeypatch, AntwortAttrappe(200, SEITE_MIT_ALLEM))

    # Act
    checks = asyncio.run(qa_scanner.run_full_qa("https://firma.de"))["checks"]

    # Assert — der Fix darf den Normalfall nicht beschädigen
    assert checks["canonical_vorhanden"] is True
    assert checks["schema_markup"] is True
    assert checks["title_vorhanden"] is True
