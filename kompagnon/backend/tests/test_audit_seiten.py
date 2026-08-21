"""Welche Seiten das Audit findet — und welche es bewusst auslaesst.

Der Seitensucher entscheidet, worueber das Audit urteilt. Zwei Fehlerarten
zaehlen: Er findet zu wenig — dann bleibt es beim alten Zustand, in dem ein
Kontaktformular auf `/kontakt` unsichtbar war. Oder er findet das Falsche —
ein PDF, eine fremde Domain, den Warenkorb —, und der Betrieb bekommt Punkte
abgezogen fuer etwas, das keine Inhaltsseite ist.
"""
import asyncio

import pytest

from services.audit_seiten import (
    _aufraeumen,
    adressen_aus_html,
    finde_unterseiten,
    ist_seite,
    normalisiere,
)


# ── Einzelne Adressen ────────────────────────────────────────────────────────

def test_dieselbe_seite_in_drei_schreibweisen_ist_eine():
    """Ohne das prueft das Audit sie dreimal und zaehlt ihre Bilder dreifach."""
    formen = ["https://x.de/kontakt", "https://x.de/kontakt/",
              "https://x.de/kontakt#formular"]

    assert len({normalisiere(f) for f in formen}) == 1


def test_startseite_behaelt_ihren_strich():
    assert normalisiere("https://x.de/") == "https://x.de/"
    assert normalisiere("https://x.de") == "https://x.de/"


@pytest.mark.parametrize("pfad", [
    "/prospekt.pdf", "/bild.JPG", "/style.css", "/app.js", "/daten.xml",
])
def test_dateien_sind_keine_seiten(pfad):
    """Ein PDF im Audit zu zaehlen hiesse, seine fehlenden Alt-Texte dem
    Betrieb anzulasten."""
    assert not ist_seite(f"https://x.de{pfad}")


@pytest.mark.parametrize("pfad", ["/wp-admin", "/warenkorb", "/login", "/feed"])
def test_funktionsseiten_werden_uebergangen(pfad):
    assert not ist_seite(f"https://x.de{pfad}")


@pytest.mark.parametrize("pfad", ["/kontakt", "/leistungen/waermepumpe", "/", "/impressum"])
def test_inhaltsseiten_zaehlen(pfad):
    assert ist_seite(f"https://x.de{pfad}")


# ── Die Liste ────────────────────────────────────────────────────────────────

def test_fremde_domain_kommt_nicht_hinein():
    liste = _aufraeumen("https://x.de/", ["https://fremd.de/kontakt", "/kontakt"], 25)

    assert liste == ["https://x.de/", "https://x.de/kontakt"]


def test_startseite_steht_vorn_und_zaehlt_mit():
    """Sonst meldet das Audit „26 Seiten geprueft" bei einer Grenze von 25."""
    liste = _aufraeumen("https://x.de/", [f"/s{i}" for i in range(50)], 25)

    assert liste[0] == "https://x.de/"
    assert len(liste) == 25


def test_flache_pfade_zuerst():
    """Eine Sitemap mit 4.000 Beitraegen darf nicht dazu fuehren, dass
    `/kontakt` aus der Auswahl faellt."""
    roh = ["/blog/2019/03/altes-thema", "/kontakt", "/leistungen/waermepumpe"]

    liste = _aufraeumen("https://x.de/", roh, 25)

    assert liste == ["https://x.de/", "https://x.de/kontakt",
                     "https://x.de/leistungen/waermepumpe",
                     "https://x.de/blog/2019/03/altes-thema"]


def test_relative_adressen_werden_aufgeloest():
    liste = _aufraeumen("https://x.de/unter/seite", ["../kontakt", "seite2"], 25)

    assert "https://x.de/kontakt" in liste


def test_links_aus_html():
    html = '<a href="/kontakt">K</a><a href=\'/impressum\'>I</a><a>ohne</a>'

    assert adressen_aus_html("https://x.de/", html) == ["/kontakt", "/impressum"]


# ── Die Suche als Ganzes ─────────────────────────────────────────────────────

class _Antwort:
    def __init__(self, text="", status=200):
        self.text = text
        self.status_code = status
        self.headers = {"content-type": "text/html"}


class _Client:
    """Ein Client, der auf feste Adressen feste Antworten gibt."""

    def __init__(self, seiten: dict):
        self.seiten = seiten
        self.gefragt = []

    async def get(self, url, **kwargs):
        self.gefragt.append(url)
        if url not in self.seiten:
            return _Antwort(status=404)
        return _Antwort(self.seiten[url])


@pytest.fixture(autouse=True)
def _ohne_netz(monkeypatch):
    """`fetch_guarded` loest DNS auf — im Test steht kein Netz zur Verfuegung."""
    async def _direkt(client, url, **kwargs):
        return await client.get(url, **kwargs)

    monkeypatch.setattr("services.audit_seiten.fetch_guarded", _direkt)
    monkeypatch.setattr("services.audit_seiten.is_same_host",
                        lambda url, basis: url.startswith("https://x.de"))


def _suche(client, html="", max_seiten=25):
    return asyncio.run(
        finde_unterseiten(client, "https://x.de/", html, max_seiten=max_seiten)
    )


def test_sitemap_wird_der_verlinkung_vorgezogen():
    """Die Sitemap ist die Auskunft des Betreibers: ein Abruf, vollstaendig."""
    client = _Client({
        "https://x.de/sitemap.xml":
            "<urlset><url><loc>https://x.de/kontakt</loc></url>"
            "<url><loc>https://x.de/leistungen</loc></url></urlset>",
    })

    ergebnis = _suche(client, '<a href="/nur-verlinkt">x</a>')

    assert ergebnis["quelle"] == "sitemap.xml"
    assert ergebnis["seiten"] == ["https://x.de/", "https://x.de/kontakt",
                                  "https://x.de/leistungen"]
    assert "https://x.de/nur-verlinkt" not in ergebnis["seiten"]


def test_ohne_sitemap_zaehlt_die_verlinkung():
    ergebnis = _suche(_Client({}), '<a href="/kontakt">K</a>')

    assert ergebnis["quelle"] == "interne Verlinkung"
    assert ergebnis["seiten"] == ["https://x.de/", "https://x.de/kontakt"]


def test_robots_txt_darf_die_sitemap_woanders_hinlegen():
    client = _Client({
        "https://x.de/robots.txt": "Sitemap: https://x.de/sitemap_index.xml",
        "https://x.de/sitemap_index.xml":
            "<urlset><url><loc>https://x.de/kontakt</loc></url></urlset>",
    })

    assert _suche(client)["seiten"] == ["https://x.de/", "https://x.de/kontakt"]


def test_sitemap_index_wird_eine_ebene_aufgeloest():
    client = _Client({
        "https://x.de/sitemap.xml":
            "<sitemapindex><sitemap><loc>https://x.de/seiten.xml</loc></sitemap>"
            "</sitemapindex>",
        "https://x.de/seiten.xml":
            "<urlset><url><loc>https://x.de/kontakt</loc></url></urlset>",
    })

    assert "https://x.de/kontakt" in _suche(client)["seiten"]


def test_die_kappung_wird_gemeldet():
    """Wer den Bericht liest, muss sehen, dass 10 von 61 geprueft wurden."""
    viele = "".join(f"<url><loc>https://x.de/s{i}</loc></url>" for i in range(60))
    client = _Client({"https://x.de/sitemap.xml": f"<urlset>{viele}</urlset>"})

    ergebnis = _suche(client, max_seiten=10)

    assert ergebnis["geprueft"] == 10
    assert ergebnis["gefunden"] == 61       # 60 Unterseiten + Startseite
    assert ergebnis["gekappt"] is True


def test_alles_kaputt_liefert_wenigstens_die_startseite():
    """Die Suche darf das Audit nie beenden."""
    class _Kaputt:
        async def get(self, url, **kwargs):
            raise RuntimeError("kein Netz")

    assert _suche(_Kaputt())["seiten"] == ["https://x.de/"]
