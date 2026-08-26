# -*- coding: utf-8 -*-
"""Der Browserlauf — und die zwei Sperren, ohne die er ein Einfallstor wäre.

**Der Anlass (L-107, Entscheidung David 26.08.2026).** Die Erhebung führt kein
JavaScript aus und sah von der eigenen Produktivoberfläche elf Wörter. Seit
dem 25.08. wird daraus kein Befund mehr — die betroffenen Kriterien fallen aus
Zähler und Nenner. Gemessen wurde trotzdem nichts.

**Warum diese Datei ohne Browser auskommt.** Playwright ist in der CI nicht
installiert, und ein Test, der einen Browser braucht, läuft dort nie. Geprüft
wird deshalb das, was auch ohne ihn wahr sein muss: dass ohne Browser
**nichts behauptet** wird, und dass die Sperren **vor** dem Start greifen.

**Die Sperren sind der eigentliche Gegenstand.** `fetch_guarded` prüft jede
Weiterleitung einzeln; ein Browser folgt ihnen selbst und fragt niemanden.
Eine Kundenwebsite, die auf `http://169.254.169.254/` weiterleitet, wäre
sonst ein Weg zu den Zugangsdaten des Servers — dieselbe Adresse, die heute
schon in `test_url_guard_nat64` als verpackte Fassung geprüft wird.
"""
import asyncio
import ipaddress

import pytest

from services import seitenbrowser


@pytest.fixture(autouse=True)
def _aus(monkeypatch):
    """Vorgabe für jeden Test: Schalter aus. Wer ihn braucht, setzt ihn."""
    monkeypatch.delenv(seitenbrowser.SCHALTER, raising=False)


class TestOhneBrowserWirdNichtsBehauptet:
    def test_ausgeschaltet_gibt_kein_html_und_sagt_warum(self):
        ergebnis = asyncio.run(seitenbrowser.hole_gerendert("https://example.com/"))

        assert ergebnis["wie"] == "nicht"
        assert ergebnis["html"] == ""
        assert seitenbrowser.SCHALTER in ergebnis["grund"]

    def test_eingeschaltet_aber_nicht_installiert_ist_ein_eigener_zustand(
            self, monkeypatch, caplog):
        """„Nicht eingeschaltet" und „eingeschaltet, aber nicht installiert"
        sind verschiedene Zustaende. Der zweite ist ein Einrichtungsfehler
        und soll auffallen, nicht stillschweigend zum ersten werden."""
        monkeypatch.setenv(seitenbrowser.SCHALTER, "true")
        monkeypatch.setattr(seitenbrowser, "browser_verfuegbar", lambda: False)

        with caplog.at_level("WARNING"):
            ergebnis = asyncio.run(seitenbrowser.hole_gerendert("https://example.com/"))

        assert ergebnis["wie"] == "nicht"
        assert "Playwright" in ergebnis["grund"]
        assert any("Playwright" in s.message or "Playwright" in s.getMessage()
                   for s in caplog.records)

    def test_der_schalter_versteht_nur_ja(self, monkeypatch):
        monkeypatch.setenv(seitenbrowser.SCHALTER, "vielleicht")

        assert seitenbrowser.browser_erwuenscht() is False


class TestDieErsteSperre:
    def test_eine_unerlaubte_adresse_startet_keinen_browser(
            self, monkeypatch):
        """Die Gegenprobe zum eigentlichen Risiko: Nicht nur „kein HTML",
        sondern **`_laden` wird nicht gerufen**. Ein Ergebnis ohne HTML
        haette auch ein abgestuerzter Browserlauf geliefert."""
        monkeypatch.setenv(seitenbrowser.SCHALTER, "true")
        monkeypatch.setattr(seitenbrowser, "browser_verfuegbar", lambda: True)

        gerufen = []

        async def _nie(url):
            gerufen.append(url)
            return {"wie": "browser", "html": "<html/>"}

        monkeypatch.setattr(seitenbrowser, "_laden", _nie)

        ergebnis = asyncio.run(seitenbrowser.hole_gerendert("http://127.0.0.1/admin"))

        assert gerufen == [], "der Browser wurde trotzdem gestartet"
        assert ergebnis["wie"] == "nicht"
        assert "nicht erlaubt" in ergebnis["grund"]

    def test_eine_erlaubte_adresse_kommt_durch(self, monkeypatch):
        """Gegenprobe zur Gegenprobe: Sperrte sie alles, waere der Test oben
        gruen und der Browser nutzlos."""
        monkeypatch.setenv(seitenbrowser.SCHALTER, "true")
        monkeypatch.setattr(seitenbrowser, "browser_verfuegbar", lambda: True)

        async def _ja(url):
            return {"wie": "browser", "html": "<html>viel Text</html>",
                    "final_url": url}

        monkeypatch.setattr(seitenbrowser, "_laden", _ja)

        ergebnis = asyncio.run(seitenbrowser.hole_gerendert("https://example.com/"))

        assert ergebnis["wie"] == "browser"
        assert "viel Text" in ergebnis["html"]

    def test_ein_absturz_im_browser_reisst_nichts_mit(self, monkeypatch):
        """Der Aufrufer hat bereits HTML aus dem gewoehnlichen Abruf. Seine
        Analyse darf nicht verloren gehen, weil der Browser nicht ansprang."""
        monkeypatch.setenv(seitenbrowser.SCHALTER, "true")
        monkeypatch.setattr(seitenbrowser, "browser_verfuegbar", lambda: True)

        async def _kracht(url):
            raise RuntimeError("chromium nicht startbar")

        monkeypatch.setattr(seitenbrowser, "_laden", _kracht)

        ergebnis = asyncio.run(seitenbrowser.hole_gerendert("https://example.com/"))

        assert ergebnis["wie"] == "nicht"
        assert "chromium" in ergebnis["grund"]


class TestDieZweiteSperre:
    """Jede einzelne Anfrage des Browsers, nicht nur die erste."""

    @pytest.mark.parametrize("adresse", [
        "http://127.0.0.1/",
        "http://localhost:8000/api/diagnostics/config",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.1.2.3/",
        "http://192.168.0.1/",
    ])
    def test_interne_ziele_werden_abgewiesen(self, adresse, monkeypatch):
        monkeypatch.setattr(seitenbrowser, "_GEPRUEFT", {})

        assert seitenbrowser._ziel_ist_oeffentlich(adresse) is False

    def test_ein_oeffentliches_ziel_darf_geladen_werden(self, monkeypatch):
        """Ohne diesen Fall waere eine Sperre, die alles abweist, gruen — und
        der Browser bekaeme nie ein Bild oder ein Skript zu sehen."""
        monkeypatch.setattr(seitenbrowser, "_GEPRUEFT", {})
        monkeypatch.setattr(
            seitenbrowser.socket, "getaddrinfo",
            lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 0))])

        assert seitenbrowser._ziel_ist_oeffentlich(
            "https://example.com/bild.png") is True

    def test_was_sich_nicht_aufloesen_laesst_wird_nicht_geladen(self,
                                                                monkeypatch):
        """Im Zweifel zu. Ein Name, den wir nicht aufloesen koennen, koennte
        im Netz des Servers etwas anderes bedeuten als hier."""
        monkeypatch.setattr(seitenbrowser, "_GEPRUEFT", {})

        def _kein_dns(*a, **k):
            raise OSError("Name or service not known")

        monkeypatch.setattr(seitenbrowser.socket, "getaddrinfo", _kein_dns)

        assert seitenbrowser._ziel_ist_oeffentlich("https://gibtsnicht/") is False

    def test_ohne_wirt_wird_nichts_geladen(self, monkeypatch):
        monkeypatch.setattr(seitenbrowser, "_GEPRUEFT", {})

        assert seitenbrowser._ziel_ist_oeffentlich("data:text/html,<h1>x") is False
        assert seitenbrowser._ziel_ist_oeffentlich("") is False

    def test_ein_wirt_mit_zwei_adressen_faellt_beim_schlechteren_durch(
            self, monkeypatch):
        """Ein Server kann v4 oeffentlich und v6 intern fuehren. Es zaehlt
        die schlechteste — sonst entscheidet der Zufall der Aufloesung."""
        monkeypatch.setattr(seitenbrowser, "_GEPRUEFT", {})
        monkeypatch.setattr(
            seitenbrowser.socket, "getaddrinfo",
            lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 0)),
                             (2, 1, 6, "", ("127.0.0.1", 0))])

        assert seitenbrowser._ziel_ist_oeffentlich("https://zwiespalt.test/") is False

    def test_auch_verpacktes_nat64_bleibt_gesperrt(self, monkeypatch):
        """Dieselbe Klasse wie in `test_url_guard_nat64`: `64:ff9b::7f00:1`
        traegt `127.0.0.1`. Der Torwaechter urteilt ueber `_is_public_ip`
        und erbt die Auspackung — dieser Test haelt fest, dass er es tut."""
        monkeypatch.setattr(seitenbrowser, "_GEPRUEFT", {})
        monkeypatch.setattr(
            seitenbrowser.socket, "getaddrinfo",
            lambda *a, **k: [(30, 1, 6, "", ("64:ff9b::7f00:1", 0, 0, 0))])

        assert seitenbrowser._ziel_ist_oeffentlich("https://getarnt.test/") is False


class TestDerZwischenspeicher:
    def test_er_haelt_innerhalb_eines_laufs(self, monkeypatch):
        """Eine Seite holt Dutzende Dateien von derselben Handvoll Rechner.
        Jede einzeln aufzuloesen kostet mehr als der Browserlauf selbst."""
        monkeypatch.setattr(seitenbrowser, "_GEPRUEFT", {})
        aufrufe = []

        def _zaehlen(*a, **k):
            aufrufe.append(a)
            return [(2, 1, 6, "", ("93.184.216.34", 0))]

        monkeypatch.setattr(seitenbrowser.socket, "getaddrinfo", _zaehlen)

        for pfad in ("/", "/a.css", "/b.js", "/c.png"):
            seitenbrowser._ziel_ist_oeffentlich(f"https://example.com{pfad}")

        assert len(aufrufe) == 1

    def test_und_wird_zwischen_zwei_laeufen_geleert(self, monkeypatch):
        """Sonst traegt eine Analyse das Urteil der vorigen weiter — und ein
        Rechner, dessen Adresse sich geaendert hat, bliebe falsch bewertet."""
        seitenbrowser._GEPRUEFT["alt.test"] = True

        asyncio.run(seitenbrowser.hole_gerendert("https://example.com/"))

        assert "alt.test" not in seitenbrowser._GEPRUEFT


class TestSeitenDieNochUmziehen:
    """Am Gegenstand gefunden, nicht ausgedacht."""

    class _Seite:
        def __init__(self, fehler_bis):
            self.versuche = 0
            self.fehler_bis = fehler_bis
            self.gewartet = 0

        async def content(self):
            self.versuche += 1
            if self.versuche <= self.fehler_bis:
                raise RuntimeError(
                    "Page.content: Unable to retrieve content because the "
                    "page is navigating and changing the content.")
            return "<html>fertig</html>"

        async def wait_for_timeout(self, ms):
            self.gewartet += ms

    def test_ein_zweiter_versuch_rettet_den_lauf(self):
        """`stackoverflow.com` leitet nach dem Laden noch einmal weiter. Der
        erste Versuch brach den **ganzen** Lauf ab — und damit ging nicht nur
        das HTML verloren, sondern auch die Cookie-Messung, die am selben
        Lauf haengt."""
        seite = self._Seite(fehler_bis=1)

        html = asyncio.run(seitenbrowser._inhalt(seite))

        assert html == "<html>fertig</html>"
        assert seite.versuche == 2
        assert seite.gewartet == seitenbrowser.RUHEFRIST_MS

    def test_ohne_stoerung_wird_nicht_gewartet(self):
        """Gegenprobe: Sonst kostete jeder Lauf die Ruhefrist zweimal."""
        seite = self._Seite(fehler_bis=0)

        asyncio.run(seitenbrowser._inhalt(seite))

        assert seite.versuche == 1
        assert seite.gewartet == 0

    def test_bleibt_es_kaputt_gibt_es_nichts_statt_der_haelfte(self):
        """Der Aufrufer hat das HTML aus dem gewoehnlichen Abruf. Eine halbe
        Seite waere schlechter als keine."""
        seite = self._Seite(fehler_bis=9)

        with pytest.raises(RuntimeError):
            asyncio.run(seitenbrowser._inhalt(seite))


def test_dieselbe_kennung_wie_der_gewoehnliche_abruf():
    """Zwei verschiedene Kennungen hiessen, dass zwei Messungen derselben
    Seite nicht vergleichbar sind — manche Server liefern je nach Kennung
    anderes aus."""
    from services.audit_runner import USER_AGENT

    assert seitenbrowser._kennung() == USER_AGENT


def test_die_adressen_pruefung_nutzt_dieselbe_regel_wie_der_rest():
    """Nicht eine zweite Vorstellung davon, was „intern" heisst — die
    zweite Meinung ist die, die irgendwann abweicht."""
    from services.url_guard import _is_public_ip

    assert seitenbrowser._is_public_ip is _is_public_ip
    assert _is_public_ip(ipaddress.ip_address("127.0.0.1")) is False
