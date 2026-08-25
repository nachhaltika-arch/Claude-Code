# -*- coding: utf-8 -*-
"""
Die Nachschau nach dem Deploy (GEO-01, Position 6).

**Der Befund vom 25.08.2026.** Das Produktdatenblatt verspricht eine
„automatisierte Verifikation der Auslieferung nach Veröffentlichung". Der
Einbau in den Deploy stand seit L-99 — `llms.txt` und die Auszeichnung gehen
mit derselben Auslieferung hoch. **Nachgesehen hat danach niemand.**

Der Deploy meldet „erfolgreich"; ob die Datei unter ihrer Adresse steht, ist
eine andere Frage.
"""
import asyncio

import httpx
import pytest

from services.geo_auslieferung import klartext, pruefe_auslieferung


def _antwort(text: str, status: int = 200) -> httpx.Response:
    return httpx.Response(status, text=text, request=httpx.Request("GET", "https://x"))


def test_ohne_adresse_wird_nicht_geraten():
    befund = asyncio.run(pruefe_auslieferung(""))

    assert befund["collected"] is False
    assert "keine Adresse" in befund["grund"]


def test_eine_startseite_unter_dem_namen_llms_txt_gilt_nicht(monkeypatch):
    """Viele Hosts liefern die Startseite für jede unbekannte Adresse aus.

    Eine 200er-Antwort allein wäre deshalb falsch grün — genau der Fehler, den
    diese Prüfung finden soll.
    """
    async def _hole(self, url, **kwargs):
        if url.endswith("/llms.txt"):
            return _antwort("<!doctype html><html><body>Startseite</body></html>")
        return _antwort('<html><script type="application/ld+json">'
                        '{"@context":"https://schema.org"}</script></html>')

    monkeypatch.setattr(httpx.AsyncClient, "get", _hole)
    befund = asyncio.run(pruefe_auslieferung("https://beispiel.de"))

    assert befund["llms_txt"] is False
    assert befund["jsonld"] is True
    assert befund["vollstaendig"] is False
    assert "llms.txt" in klartext(befund)


def test_eine_echte_auslieferung_ist_vollstaendig(monkeypatch):
    async def _hole(self, url, **kwargs):
        if url.endswith("/llms.txt"):
            return _antwort("# Mustermann Heizung GmbH\n> Meisterbetrieb in Kassel\n")
        if url.endswith("/robots.txt"):
            return _antwort("User-agent: *\nAllow: /\n")
        return _antwort('<html><script type="application/ld+json">'
                        '{"@context":"https://schema.org","@type":"Plumber"}</script></html>')

    monkeypatch.setattr(httpx.AsyncClient, "get", _hole)
    befund = asyncio.run(pruefe_auslieferung("https://beispiel.de"))

    assert befund["llms_txt"] is True
    assert befund["jsonld"] is True
    assert befund["vollstaendig"] is True
    assert "erreichbar" in klartext(befund)


def test_wenn_die_seite_schweigt_wird_nichts_behauptet(monkeypatch):
    """Über Dateien auf einer Seite, die nicht antwortet, ist nichts bekannt."""
    async def _hole(self, url, **kwargs):
        return _antwort("", status=503)

    monkeypatch.setattr(httpx.AsyncClient, "get", _hole)
    befund = asyncio.run(pruefe_auslieferung("https://beispiel.de"))

    assert befund["collected"] is False
    assert "llms_txt" not in befund, "eine Fehlanzeige waere eine Behauptung"
    assert "Nicht geprüft" in klartext(befund)


def test_ein_netzfehler_meldet_nicht_gefunden_statt_zu_werfen(monkeypatch):
    async def _hole(self, url, **kwargs):
        if url.endswith("/llms.txt"):
            raise httpx.ConnectError("weg")
        return _antwort('<html><script type="application/ld+json">'
                        '{"@context":"https://schema.org"}</script></html>')

    monkeypatch.setattr(httpx.AsyncClient, "get", _hole)
    befund = asyncio.run(pruefe_auslieferung("https://beispiel.de"))

    assert befund["llms_txt"] is False


def test_der_deploy_ruft_die_pruefung_auf():
    """Ein Prüfer, den niemand auslöst, ist keiner."""
    import inspect

    from routers import projects_netlify

    quelle = inspect.getsource(projects_netlify.netlify_deploy)
    assert "_pruefe_und_merke" in quelle
