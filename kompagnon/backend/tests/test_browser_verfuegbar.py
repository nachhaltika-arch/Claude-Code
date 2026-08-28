# -*- coding: utf-8 -*-
"""`/health` darf den Browser nicht für bereit erklären, wenn er fehlt (L-147).

**Der Fund vom 28.08.2026.** Drei Wiederholungsläufe gegen dieselbe Seite
(L-112) zeigten im Protokoll:

    Browserlauf fehlgeschlagen: BrowserType.launch: Executable doesn't exist
    at /opt/render/.cache/ms-playwright/chromium_headless_shell-1194/…

Nachgemessen: Das Verzeichnis existiert auf **keinem** der beiden Dienste.
`AUDIT_BROWSER=true` steht auf beiden, der Buildbefehl enthält
`playwright install chromium` — die Dateien überleben den Build aber nicht,
weil der Dienst ohne Build-Cache läuft.

**Und `/health` meldete die ganze Zeit `browser.bereit: true`.** Die Ursache
war eine Zeile: `browser_verfuegbar()` prüfte allein, ob sich
`playwright.async_api` importieren lässt. Das Paket lag vor, der Browser
nicht. Ein Bericht, der „bereit" sagt, wo nichts bereit ist, ist schlimmer als
gar keiner — dieselbe Bauart wie die vier Fälle in `waechter_ohne_wirkung`.

**Was dieser Test festhält, ist die Unterscheidung**, nicht der Zustand dieser
Maschine: Er prüft beide Richtungen an einem gestellten Dateibaum. Ein Test,
der nur „auf meinem Rechner ist ein Browser da" belegt, wäre auf dem Server
grün und dort wertlos.
"""
import pytest

from services import seitenbrowser


@pytest.fixture
def leerer_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    return tmp_path


def test_ohne_browserdatei_ist_er_nicht_verfuegbar(leerer_cache):
    """Der Fall, der monatelang als „bereit" gemeldet wurde."""
    # Act & Assert
    assert seitenbrowser._browserdatei_vorhanden() is False
    assert seitenbrowser.browser_verfuegbar() is False


def test_mit_browserdatei_ist_er_verfuegbar(leerer_cache):
    """Die Gegenprobe — sonst wäre der Test oben auch bei kaputter Suche grün."""
    # Arrange
    datei = (leerer_cache / "chromium_headless_shell-1194"
             / "chrome-linux" / "headless_shell")
    datei.parent.mkdir(parents=True)
    datei.write_text("")

    # Act & Assert
    assert seitenbrowser._browserdatei_vorhanden() is True
    assert seitenbrowser.browser_verfuegbar() is True


def test_auch_die_gewoehnliche_chrome_datei_zaehlt(leerer_cache):
    """`playwright install chromium` legt je nach Fassung beides an."""
    # Arrange
    datei = leerer_cache / "chromium-1194" / "chrome-linux" / "chrome"
    datei.parent.mkdir(parents=True)
    datei.write_text("")

    # Act & Assert
    assert seitenbrowser._browserdatei_vorhanden() is True


def test_ein_leeres_verzeichnis_genuegt_nicht(leerer_cache):
    """Vorhandener Ordner ohne Datei ist genau der Zustand nach einem Build,
    dessen Dateien nicht mitgekommen sind."""
    # Arrange
    (leerer_cache / "chromium-1194" / "chrome-linux").mkdir(parents=True)

    # Act & Assert
    assert seitenbrowser._browserdatei_vorhanden() is False


def test_der_schalter_allein_macht_nichts_bereit(leerer_cache, monkeypatch):
    """`AUDIT_BROWSER=true` bei fehlendem Browser heisst **nicht** bereit.

    Genau diese Kombination stand am 28.08. auf beiden Diensten.
    """
    # Arrange
    monkeypatch.setenv("AUDIT_BROWSER", "true")

    # Act & Assert
    assert seitenbrowser.browser_erwuenscht() is True
    assert seitenbrowser.browser_verfuegbar() is False
