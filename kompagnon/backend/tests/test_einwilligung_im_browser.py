# -*- coding: utf-8 -*-
"""Die Sperre haelt — im Browser nachgewiesen, nicht im Markup gezaehlt (L-144).

**Warum es diese Datei zusaetzlich gibt.** `test_einwilligung.py` zaehlt
Zeichenketten: `type="text/plain"` steht da, kein `src` steht da. Das ist eine
Aussage ueber Text, nicht ueber Verhalten — dieselbe Luecke, die in
`test_ohne_den_gegenstand` beschrieben ist. Ob der Browser die Adresse
wirklich **nicht abruft**, sagt nur ein Browser.

**Was gemessen wird, ist der Netzverkehr**, nicht der Bildschirm: Vor der
Zustimmung darf die Tracking-Adresse **null** Mal angefragt werden, danach
mindestens einmal. Beides zusammen — ohne die zweite Haelfte waere „null
Anfragen" auch dann wahr, wenn das Skript gar nicht eingebaut ist.

**Uebersprungen ohne Browser.** Chromium kommt ueber den Render-Buildbefehl
(`playwright install chromium`); auf einer Maschine ohne ihn soll diese Datei
den Lauf nicht rot faerben, sondern sich melden.
"""
import re
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

from services.netlify_service import _build_full_html

TRACKER = "http://127.0.0.1:9/verfolger.js"     # Port 9 nimmt nie an
UMAMI = {"src": TRACKER, "zweck": "statistik", "attribute": {"website-id": "abc"}}


@pytest.fixture(scope="module")
def browser():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as f:                       # pragma: no cover
            pytest.skip(f"kein Chromium verfuegbar: {f}")
        yield b
        b.close()


@pytest.fixture
def seite_url(tmp_path):
    """Eine echte Herkunft — `file://` und `about:blank` sperren `localStorage`."""
    dokument = _build_full_html(
        page_name="Start", html="<h1>Hallo</h1>", company_name="Muster GmbH",
        tracking_skripte=[UMAMI])
    (tmp_path / "index.html").write_text(dokument, encoding="utf-8")

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        partial(SimpleHTTPRequestHandler, directory=str(tmp_path)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}/index.html"
    server.shutdown()


def _mit_zaehler(browser, url):
    """Seite oeffnen und die Anfragen an den Verfolger mitzaehlen."""
    seite = browser.new_page()
    anfragen = []
    seite.route(re.compile(r"verfolger\.js"), lambda route: (
        anfragen.append(route.request.url), route.abort()))
    seite.goto(url, wait_until="networkidle")
    return seite, anfragen


def test_vor_der_zustimmung_wird_der_verfolger_nicht_geladen(browser, seite_url):
    # Arrange & Act
    seite, anfragen = _mit_zaehler(browser, seite_url)

    # Assert
    assert anfragen == [], f"geladen ohne Einwilligung: {anfragen}"
    assert seite.locator("#kompagnon-einwilligung").is_visible(), \
        "der Kasten muss sichtbar sein, sonst kann niemand entscheiden"
    seite.close()


def test_nach_dem_ja_wird_er_geladen(browser, seite_url):
    """Die positive Haelfte — sonst belegt der Test oben nichts."""
    # Arrange
    seite, anfragen = _mit_zaehler(browser, seite_url)

    # Act
    seite.click('[data-kompagnon-einwilligung-antwort="ja"]')
    seite.wait_for_timeout(500)

    # Assert
    assert len(anfragen) >= 1, "nach der Zustimmung muss das Skript laden"
    assert not seite.locator("#kompagnon-einwilligung").is_visible()
    seite.close()


def test_nach_dem_nein_bleibt_er_aus_und_der_widerruf_erscheint(browser, seite_url):
    # Arrange
    seite, anfragen = _mit_zaehler(browser, seite_url)

    # Act
    seite.click('[data-kompagnon-einwilligung-antwort="nein"]')
    seite.wait_for_timeout(500)

    # Assert
    assert anfragen == [], f"trotz Ablehnung geladen: {anfragen}"
    assert seite.locator("#kompagnon-einwilligung-widerruf").is_visible(), \
        "ohne sichtbaren Widerruf ist die Entscheidung nicht zuruecknehmbar"
    seite.close()


def test_die_entscheidung_ueberdauert_das_neuladen(browser, seite_url):
    """Sonst fragt die Seite bei jedem Aufruf erneut — das ist kein Nein."""
    # Arrange
    seite, _ = _mit_zaehler(browser, seite_url)
    seite.click('[data-kompagnon-einwilligung-antwort="nein"]')
    seite.wait_for_timeout(300)

    # Act
    seite.reload(wait_until="networkidle")

    # Assert
    assert not seite.locator("#kompagnon-einwilligung").is_visible()
    seite.close()
