"""
Der Ort aus der Adresse — und warum er bisher fehlte.

Beobachtet an einem echten Betrieb (Lauf 80, 2026-08-15): Telefon und
E-Mail wurden erkannt, der Ort nicht, obwohl „22047 Hamburg" im Fußbereich
steht. Ursache ist die Textgewinnung: ``soup.get_text()`` ohne Trenner
klebt benachbarte Elemente aneinander. Aus „Straße 12" und „22047 Hamburg"
wird „Straße 122047 Hamburg", und ``\\b\\d{5}`` findet in „122047" keine
Postleitzahl mehr.

Das trifft die Bewertung doppelt: Ohne Ort ist der Ortspunkt in
``se_lokal`` unerreichbar, und ``_titel_traegt_den_massstab`` verlangt für
ortsgebundene Klassen genau diesen Ort im Titel. Bei Analysen über das
Widget gibt niemand einen Ort ein — die Erhebung ist der einzige Weg.
"""
import asyncio

from bs4 import BeautifulSoup

from services import scraper
from services.scraper import stadt_aus_text


ADRESSE_IN_NACHBAR_TAGS = (
    '<html><head><title>Meister Peters - Sanitär und Heizungsbau</title></head>'
    '<body><footer>'
    '<span>Werkstatt:</span><span>Angerburger Straße 12</span>'
    '<span>22047 Hamburg</span>'
    '<a href="tel:04069705880">040 69705880</a>'
    '<a href="mailto:info@firma.de">info@firma.de</a>'
    '</footer></body></html>'
)


class AntwortAttrappe:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text
        self.headers = {}


class ClientAttrappe:
    def __init__(self, antwort, **_kwargs):
        self._antwort = antwort

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def get(self, _url, **_kwargs):
        return self._antwort


def test_ort_wird_erkannt_wenn_die_adresse_ueber_tags_verteilt_ist(monkeypatch):
    # Arrange — Hausnummer und Postleitzahl stehen in benachbarten Elementen
    monkeypatch.setattr(
        scraper.httpx, "AsyncClient",
        lambda **kw: ClientAttrappe(AntwortAttrappe(200, ADRESSE_IN_NACHBAR_TAGS), **kw))

    # Act
    ergebnis = asyncio.run(scraper.scrape_website("https://firma.de"))

    # Assert
    assert ergebnis["city"] == "Hamburg"


def test_zusammengeklebter_text_liefert_keinen_ort():
    # Arrange — das alte Verhalten, hier festgehalten als Begründung
    zusammengeklebt = BeautifulSoup(ADRESSE_IN_NACHBAR_TAGS, "html.parser").get_text()

    # Act & Assert — „Straße 1222047 Hamburg" enthält keine erkennbare PLZ
    assert "1222047" in zusammengeklebt
    assert stadt_aus_text(zusammengeklebt) == ""


def test_telefon_und_mail_bleiben_erhalten(monkeypatch):
    # Arrange — der Trenner darf die übrigen Funde nicht beschädigen
    monkeypatch.setattr(
        scraper.httpx, "AsyncClient",
        lambda **kw: ClientAttrappe(AntwortAttrappe(200, ADRESSE_IN_NACHBAR_TAGS), **kw))

    # Act
    ergebnis = asyncio.run(scraper.scrape_website("https://firma.de"))

    # Assert
    assert ergebnis["email"] == "info@firma.de"
    assert ergebnis["phone"]
