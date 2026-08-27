"""`llms.txt` für die Kundenseite (L-99).

**Warum es das gibt.** Das Systempaket (12.900 €) verspricht einen
GEO/GAIO-Layer — `llms.txt`, `schema.org`-Auszeichnung und Ground Page. Das
Produkt steht in `main.py` ausdrücklich auf `draft`, **weil** diese Leistung
nicht ausgeliefert wird: `services/qa_scanner.py` **prüft** seit dem 16.08.,
ob eine fremde Seite eine `llms.txt` hat — **erzeugt** wurde nie eine.

**Warum erst jetzt.** Der Erzeuger braucht Anschrift und Öffnungszeiten;
`opening_hours` gab es bis zum 24.08.2026 nicht (L-15). Seit dem Feld ist der
kleinste Anfang baubar, den der Befund nennt: eine Datei aus den vorhandenen
Projektdaten, an denselben Deploy gehängt wie die Seiten selbst.

**Was `llms.txt` ist** (llmstxt.org): eine Markdown-Datei im Wurzelverzeichnis,
die einem Sprachmodell in wenigen Zeilen sagt, worum es auf dieser Seite geht
— H1 mit dem Namen, ein Zitatblock als Zusammenfassung, dann Abschnitte.
Keine Auszeichnung für Suchmaschinen, sondern eine Auskunft für Modelle.

**Nichts wird erfunden.** Fehlt eine Angabe, fehlt die Zeile — eine geratene
Adresse in einer Datei, die Modelle als Quelle lesen, wäre schlimmer als gar
keine Datei.
"""
import json

import pytest

from services.geo_artefakte import llms_txt


class _Betrieb:
    def __init__(self, **felder):
        werte = {
            "company_name": "Muster Heizung GmbH", "trade": "Heizung und Sanitär",
            "city": "Koblenz", "street": "Hauptstraße", "house_number": "12",
            "postal_code": "56070", "phone": "0261 123456",
            "email": "info@muster-heizung.de",
            "website_url": "https://muster-heizung.de",
            "opening_hours": json.dumps({"Mo-Do": "08:00-17:00", "Fr": "08:00-13:00"}),
        }
        werte.update(felder)
        for k, v in werte.items():
            setattr(self, k, v)


SEITEN = [
    {"page_name": "Wärmepumpe", "slug": "waermepumpe",
     "zweck": "Festpreis in 7 Tagen, Installation in 30"},
    {"page_name": "Kontakt", "slug": "kontakt", "zweck": ""},
]


class TestAufbau:
    def test_beginnt_mit_dem_namen_als_ueberschrift(self):
        assert llms_txt(_Betrieb(), SEITEN).startswith("# Muster Heizung GmbH\n")

    def test_die_zusammenfassung_steht_als_zitatblock(self):
        zeilen = llms_txt(_Betrieb(), SEITEN).splitlines()
        zitat = [z for z in zeilen if z.startswith("> ")]
        assert zitat, "llms.txt braucht eine Zusammenfassung als Zitatblock"
        assert "Heizung und Sanitär" in zitat[0]
        assert "Koblenz" in zitat[0]

    def test_anschrift_und_zeiten_stehen_drin(self):
        text = llms_txt(_Betrieb(), SEITEN)
        assert "Hauptstraße 12" in text
        assert "56070 Koblenz" in text
        assert "Mo-Do 08:00-17:00" in text

    def test_seiten_werden_als_verweise_gefuehrt(self):
        text = llms_txt(_Betrieb(), SEITEN)
        assert "[Wärmepumpe](https://muster-heizung.de/waermepumpe)" in text
        assert "Festpreis in 7 Tagen" in text

    def test_es_ist_markdown_und_kein_html(self):
        assert "<" not in llms_txt(_Betrieb(), SEITEN)


class TestNichtsWirdErfunden:
    def test_ohne_anschrift_fehlt_die_zeile_statt_leer_dazustehen(self):
        text = llms_txt(_Betrieb(street="", house_number="", postal_code=""), SEITEN)
        assert "Anschrift" not in text

    def test_ohne_oeffnungszeiten_fehlt_der_abschnitt(self):
        text = llms_txt(_Betrieb(opening_hours=""), SEITEN)
        assert "Öffnungszeiten" not in text

    def test_kaputte_oeffnungszeiten_zerlegen_nichts(self):
        text = llms_txt(_Betrieb(opening_hours="{kaputt"), SEITEN)
        assert "Öffnungszeiten" not in text
        assert text.startswith("# ")

    def test_ohne_seiten_bleibt_der_kopf_stehen(self):
        text = llms_txt(_Betrieb(), [])
        assert text.startswith("# Muster Heizung GmbH")
        assert "Seiten" not in text

    def test_ohne_betrieb_gibt_es_keine_datei(self):
        assert llms_txt(None, SEITEN) == ""

    def test_ohne_namen_gibt_es_keine_datei(self):
        """Eine llms.txt ohne Namen sagt einem Modell nichts."""
        assert llms_txt(_Betrieb(company_name=""), SEITEN) == ""


class TestDieDateiKommtInsPaket:
    """Ein Erzeuger ohne Auslieferung waere „gebaut, nicht angeschlossen".

    Genau diese Fehlerfamilie ist an diesem Tag fuenfmal aufgetreten (L-55,
    L-79, L-11, L-101, L-58). Deshalb prueft dieser Teil nicht den Text,
    sondern das **ZIP**, das an Netlify geht.
    """

    @staticmethod
    def _zip_inhalt(monkeypatch, zusatz: dict) -> dict:
        """Ruft den Deploy mit abgefangenem Netzzugriff und liest das ZIP."""
        import asyncio
        import io as _io
        import zipfile

        import httpx

        from services import netlify_service

        gesendet = {}

        class _Antwort:
            is_success = True
            status_code = 200

            @staticmethod
            def json():
                return {"id": "dep-1", "deploy_ssl_url": "https://x", "state": "ready"}

        class _Client:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, url, headers=None, content=None):
                gesendet["zip"] = content
                return _Antwort()

        monkeypatch.setattr(httpx, "AsyncClient", _Client)
        monkeypatch.setenv("NETLIFY_API_TOKEN", "probe-token")

        asyncio.run(netlify_service.deploy_html(
            "site-1", "<h1>Hallo</h1>", zusatzdateien=zusatz,
        ))

        with zipfile.ZipFile(_io.BytesIO(gesendet["zip"])) as zf:
            return {n: zf.read(n).decode("utf-8") for n in zf.namelist()}

    def test_llms_txt_liegt_im_wurzelverzeichnis(self, monkeypatch):
        # Arrange & Act
        dateien = self._zip_inhalt(monkeypatch, {"llms.txt": "# Muster GmbH\n"})

        # Assert — neben index.html, im selben Deploy
        assert "llms.txt" in dateien
        assert dateien["llms.txt"] == "# Muster GmbH\n"
        assert "index.html" in dateien

    def test_eine_leere_datei_wird_nicht_ausgeliefert(self, monkeypatch):
        """Eine leere llms.txt sieht fuer ein Modell aus wie eine Auskunft."""
        # Act
        dateien = self._zip_inhalt(monkeypatch, {"llms.txt": ""})

        # Assert
        assert "llms.txt" not in dateien
        assert "index.html" in dateien

    def test_ohne_zusatzdateien_bleibt_alles_wie_vorher(self, monkeypatch):
        # Act
        dateien = self._zip_inhalt(monkeypatch, None)

        # Assert
        assert set(dateien) == {"index.html", "_redirects", "_headers"}


class TestLocalBusiness:
    """`schema.org/LocalBusiness` als JSON-LD (L-99).

    Das zweite der drei Artefakte, die das Systempaket verspricht. Es gehoert
    in den `<head>` und **nicht** in eine eigene Datei — anders als
    `llms.txt`, die ein Modell direkt liest, wird JSON-LD beim Abruf der Seite
    mitgelesen.

    **Dieselbe Regel wie ueberall hier: nichts erfinden.** Eine
    `PostalAddress` ohne Strasse ist fuer eine Suchmaschine schlechter als gar
    keine — sie sieht aus wie eine Angabe und ist keine.
    """

    def test_es_ist_gueltiges_json(self):
        from services.geo_artefakte import local_business_jsonld

        roh = local_business_jsonld(_Betrieb())
        daten = json.loads(roh)
        assert daten["@context"] == "https://schema.org"
        assert daten["@type"] == "LocalBusiness"

    def test_name_adresse_und_zeiten_stehen_drin(self):
        from services.geo_artefakte import local_business_jsonld

        daten = json.loads(local_business_jsonld(_Betrieb()))
        assert daten["name"] == "Muster Heizung GmbH"
        assert daten["address"]["streetAddress"] == "Hauptstraße 12"
        assert daten["address"]["postalCode"] == "56070"
        assert daten["address"]["addressLocality"] == "Koblenz"
        assert daten["address"]["addressCountry"] == "DE"
        assert "Mo-Do 08:00-17:00" in daten["openingHours"]

    def test_ohne_anschrift_fehlt_der_adressblock_ganz(self):
        from services.geo_artefakte import local_business_jsonld

        daten = json.loads(local_business_jsonld(
            _Betrieb(street="", house_number="", postal_code="")))
        assert "address" not in daten

    def test_ohne_namen_entsteht_nichts(self):
        from services.geo_artefakte import local_business_jsonld

        assert local_business_jsonld(_Betrieb(company_name="")) == ""
        assert local_business_jsonld(None) == ""

    def test_die_auszeichnung_steht_im_kopf_der_seite(self):
        """Erzeugt und nicht eingebaut waere wieder „nicht angeschlossen"."""
        from services.netlify_service import _build_full_html

        html = _build_full_html(
            page_name="Start", html="<h1>Hallo</h1>", company_name="Muster GmbH",
            jsonld=local_business_probe(),
        )
        assert 'type="application/ld+json"' in html
        assert '"@type": "LocalBusiness"' in html
        assert html.index("ld+json") < html.index("</head>")

    def test_ohne_auszeichnung_bleibt_der_kopf_unveraendert(self):
        from services.netlify_service import _build_full_html

        html = _build_full_html(page_name="Start", html="<h1>Hallo</h1>")
        assert "ld+json" not in html


def local_business_probe() -> str:
    from services.geo_artefakte import local_business_jsonld

    return local_business_jsonld(_Betrieb())
