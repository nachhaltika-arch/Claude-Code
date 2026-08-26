# -*- coding: utf-8 -*-
"""Der Browser läuft, wenn er gebraucht wird — und nur dann.

**Der Anlass (L-107).** `httpx` führt kein JavaScript aus. Von einer
React-Anwendung sieht die Erhebung `<div id="root"></div>` und sonst nichts;
beim Probelauf gegen die eigene Produktivoberfläche waren es elf Wörter.
`clientseitig_aufgebaut` sorgt seit dem 25.08. dafür, dass daraus kein Befund
wird — die betroffenen Kriterien fallen aus Zähler **und** Nenner, statt mit
0 zu zählen. Gemessen wurde damit aber immer noch nichts.

**Drei Eigenschaften, und die dritte ist der eigentliche Punkt:**

1. Eine gewöhnliche Seite löst **keinen** Browserlauf aus. Ein Browser kostet
   Sekunden und Speicher; ihn immer zu starten wäre Aufwand für die
   neunundneunzig Seiten, die ihn nicht brauchen.
2. Eine leere Hülle löst ihn aus.
3. **Nach einem geglückten Lauf zählen die Kriterien wieder.** Bliebe
   `clientseitig` stehen, hätte der Browser nichts geändert außer der
   Laufzeit — die Seite wäre gesehen und trotzdem als „nicht messbar"
   geführt. Genau diese Zeile hätte man beim Anbinden übersehen können.

Und wenn der Browser nicht ansprang, steht das im Ergebnis (`browserlauf`)
statt nirgends. Ein Bericht, der nicht sagen kann, wie er zu seinen Zahlen
kam, ist die Fehlerfamilie, die diesen Bestand am häufigsten getroffen hat.
"""
import asyncio

import pytest

from services import audit_runner

HUELLE = ('<!doctype html><html lang="de"><head><title>Betrieb</title></head>'
          '<body><div id="root"></div></body></html>')

GERENDERT = ('<!doctype html><html lang="de"><head><title>Betrieb</title></head>'
             '<body><h1>Heizung und Sanitaer in Bremen</h1>'
             '<p>' + ("Wir bauen Waermepumpen ein. " * 40) + '</p>'
             '</body></html>')

ECHTE_SEITE = ('<!doctype html><html lang="de"><head><title>Betrieb</title></head>'
               '<body><h1>Elektrotechnik Meier</h1>'
               '<p>' + ("Wallboxen und Photovoltaik seit 1998. " * 40) + '</p>'
               '</body></html>')


@pytest.fixture(autouse=True)
def _nur_die_startseite(monkeypatch):
    """Alles Netzabhängige aus dem Weg — geprüft wird die Verzweigung."""
    async def _leer(*a, **k):
        return {}

    for name in ("fetch_pagespeed", "_run_qa_scanner", "_run_hosting",
                 "_run_link_check", "_alle_seiten"):
        monkeypatch.setattr(audit_runner, name, _leer, raising=False)

    async def _nichts(*a, **k):
        return {}

    for name in ("check_legal_pages", "check_https_redirect"):
        monkeypatch.setattr(audit_runner.collectors, name, _nichts,
                            raising=False)
    monkeypatch.setattr(audit_runner.collectors, "check_tls",
                        lambda *a, **k: {}, raising=False)


@pytest.fixture
def gesehener_text(monkeypatch):
    """Was die Sammler tatsaechlich vor sich hatten.

    Ein Ergebnis kann auf vielen Wegen richtig aussehen. Diese Liste sagt,
    welches HTML in die Auswertung ging — die einzige Frage, um die es beim
    Browserlauf geht.
    """
    gesehen = []
    echt = audit_runner.collectors.analyse_navigation

    def _mitschreiben(soup):
        gesehen.append(soup.get_text(" "))
        return echt(soup)

    monkeypatch.setattr(audit_runner.collectors, "analyse_navigation",
                        _mitschreiben)
    return gesehen


def _mit_startseite(monkeypatch, html):
    async def _homepage(url):
        return {"collected": True, "reachable": True, "status_code": 200,
                "html": html, "headers": {}, "final_url": url}

    monkeypatch.setattr(audit_runner, "fetch_homepage", _homepage)


def _mit_browser(monkeypatch, ergebnis, protokoll):
    async def _hole(url):
        protokoll.append(url)
        return ergebnis

    monkeypatch.setattr(audit_runner.seitenbrowser, "hole_gerendert", _hole)


def _erheben(url="https://betrieb.test/"):
    return asyncio.run(audit_runner.collect_facts(url, "Betrieb", "shk", "Bremen"))


class TestErLaeuftNurWennNoetig:
    def test_eine_gewoehnliche_seite_startet_keinen_browser(self, monkeypatch):
        _mit_startseite(monkeypatch, ECHTE_SEITE)
        protokoll = []
        _mit_browser(monkeypatch, {"wie": "browser", "html": GERENDERT},
                     protokoll)

        fakten = _erheben()

        assert protokoll == [], "Browser lief fuer eine Seite, die ihn nicht braucht"
        assert fakten["browserlauf"]["wie"] == "nicht"

    def test_eine_leere_huelle_startet_ihn(self, monkeypatch):
        _mit_startseite(monkeypatch, HUELLE)
        protokoll = []
        _mit_browser(monkeypatch,
                     {"wie": "browser", "html": GERENDERT,
                      "final_url": "https://betrieb.test/"}, protokoll)

        _erheben()

        assert protokoll == ["https://betrieb.test/"]


class TestNachDemLaufZaehltDieSeiteWieder:
    def test_clientseitig_faellt_zurueck_auf_falsch(self, monkeypatch):
        """Der eigentliche Punkt. Bliebe die Kennzeichnung stehen, waere die
        Seite gesehen und trotzdem als „nicht messbar" gefuehrt — der
        Browser haette nur Laufzeit gekostet."""
        _mit_startseite(monkeypatch, HUELLE)
        _mit_browser(monkeypatch,
                     {"wie": "browser", "html": GERENDERT,
                      "final_url": "https://betrieb.test/"}, [])

        fakten = _erheben()

        assert fakten["clientseitig"] is False

    def test_die_sammler_bekommen_das_gerenderte_html(self, monkeypatch,
                                                       gesehener_text):
        """**Die erste Fassung dieses Tests war wertlos.** Sie schrieb

            assert "Waermepumpen" in fakten.get("page_text", "") + GERENDERT

        — und stellte den gesuchten Text selbst daneben. Gruen, ohne die
        Sache zu beruehren; dieselbe Familie wie die Waechter, die sich in
        ihrer eigenen Beschreibung fanden.

        Gefragt wird jetzt, was die **Sammler** zu sehen bekommen haben.
        """
        _mit_startseite(monkeypatch, HUELLE)
        _mit_browser(monkeypatch,
                     {"wie": "browser", "html": GERENDERT,
                      "final_url": "https://betrieb.test/"}, [])

        fakten = _erheben()

        assert "Waermepumpen" in gesehener_text[0]
        assert fakten["browserlauf"]["wie"] == "browser"


class TestWennErNichtAnspringt:
    def test_bleibt_die_seite_als_nicht_messbar_gekennzeichnet(self, monkeypatch):
        """Kein Rueckfall auf „dann eben mit 0 bewerten". Was niemand gesehen
        hat, wird nicht benotet."""
        _mit_startseite(monkeypatch, HUELLE)
        _mit_browser(monkeypatch,
                     {"wie": "nicht", "grund": "Playwright ist nicht installiert",
                      "html": ""}, [])

        fakten = _erheben()

        assert fakten["clientseitig"] is True

    def test_und_der_grund_steht_im_ergebnis(self, monkeypatch):
        """Sonst sieht ein Bericht ohne Browserlauf genauso aus wie einer mit."""
        _mit_startseite(monkeypatch, HUELLE)
        _mit_browser(monkeypatch,
                     {"wie": "nicht", "grund": "Playwright ist nicht installiert",
                      "html": ""}, [])

        fakten = _erheben()

        assert fakten["browserlauf"]["wie"] == "nicht"
        assert "Playwright" in fakten["browserlauf"]["grund"]

    def test_ein_leeres_html_wird_nicht_uebernommen(self, monkeypatch,
                                                    gesehener_text):
        """Ein Lauf, der `wie: browser` meldet und nichts liefert, darf die
        vorhandene Huelle nicht ueberschreiben — sonst waere das Ergebnis
        schlechter als vorher."""
        _mit_startseite(monkeypatch, ECHTE_SEITE)
        monkeypatch.setattr(audit_runner.collectors, "clientseitig_aufgebaut",
                            lambda *a, **k: True)
        _mit_browser(monkeypatch, {"wie": "browser", "html": ""}, [])

        fakten = _erheben()

        assert "Wallboxen" in gesehener_text[0], (
            "die vorhandene Seite wurde durch leeres HTML ersetzt")
        assert fakten["browserlauf"]["wie"] == "browser"
