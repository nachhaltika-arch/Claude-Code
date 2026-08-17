"""Das Impressum finden — und erkennen, dass man es gefunden hat.

Befund vom 17.08.2026 an `alkozei.de`, von David am Bildschirm gefunden.

Das Impressum liegt dort unter

    https://alkozei.de/now.using/nBito/impressum

Der Sucher baute stattdessen `https://alkozei.de/impressum`. Beide antworten
mit HTTP 200 — die zweite Adresse liefert aber nur die Huelle der Anwendung:
2597 Zeichen Navigation, kein Impressum. Die richtige liefert 4626 Zeichen mit
„Umsatzsteuer" darin.

**Zwei Fehler steckten darin, und der zweite ist der schwerere:**

1. Auf der Startseite steht `<a href="impressum" onclick="return false;"
   data-nbito-call-page="3">`. Der Verweis ist absichtlich tot — die
   Navigation macht JavaScript. Der Anwendungspfad steht aber im Quelltext
   (`now.using/nBito/…`), und mit ihm zusammengesetzt ergibt sich die richtige
   Adresse.

2. Der Sucher nahm **die erste Seite mit mehr als 100 Zeichen**. Er hat nie
   geprueft, ob das ein Impressum ist. Eine Laengenschwelle beantwortet die
   Frage „ist da Text?" — gefragt war „ist das das Richtige?".
"""
import pytest

from services.impressum_scraper import impressum_kandidaten, wirkt_wie_impressum


STARTSEITE = """
<html><head><base href="https://alkozei.de:443/"></head><body>
  <script>var pfad = "now.using/nBito/alkozei-sanitaer-hechtsheim";</script>
  <a href="impressum" onclick="return false;" data-nbito-call-page="3">Impressum</a>
  <a href="datenschutz">Datenschutz</a>
</body></html>
"""


# ── Erkennen ──────────────────────────────────────────────────────────

def test_ein_impressum_wird_erkannt():
    text = ("Impressum Alkozei Heizung Sanitaer Solartechnik Froschmarkt 17 "
            "55129 Mainz-Hechtsheim Telefon 06131 582115 info@alkozei.de "
            "Umsatzsteuer-Identifikationsnummer DE123456789 "
            "Vertreten durch den Inhaber Angaben gemäß § 5 DDG")

    assert wirkt_wie_impressum(text) is True


def test_die_huelle_wird_nicht_erkannt():
    """Genau der Text, den `/impressum` bei alkozei.de liefert."""
    text = ("Kontakt Stellenangebote Anfahrt Kontakt Impressum Datenschutz "
            "ALKOZEI SANITAER LEISTUNGEN DIENSTLEISTUNGEN HEIZUNG SANITAER "
            "SOLARTECHNIK PARTNER SERVICEANFRAGE Tel: 06131 582115")

    assert wirkt_wie_impressum(text) is False


def test_das_wort_impressum_allein_genuegt_nicht():
    """Es steht in jeder Fusszeile — als Merkmal taugt es nichts."""
    assert wirkt_wie_impressum("Impressum Datenschutz AGB Kontakt") is False


# Ein Impressum ohne das jeweilige Merkmal — als Rumpf für die Fälle darunter.
RUMPF = ("Impressum Angaben gemäß § 5 DDG Muster Haustechnik "
         "Musterstraße 1, 55116 Mainz Telefon 06131 000000 "
         "E-Mail info@muster.de Verantwortlich für den Inhalt dieser Seite ")


@pytest.mark.parametrize("merkmal", [
    "Registergericht Mainz HRB 4711",
    "USt-IdNr. DE123456789",
    "Vertreten durch: Max Mustermann",
    "Handelsregister: Amtsgericht Mainz",
    "Aufsichtsbehörde: Handwerkskammer",
])
def test_ein_einzelnes_pflichtmerkmal_genuegt(merkmal):
    assert wirkt_wie_impressum(RUMPF + merkmal) is True


def test_zu_kurz_ist_nie_ein_impressum():
    assert wirkt_wie_impressum("Registergericht") is False
    assert wirkt_wie_impressum("") is False
    assert wirkt_wie_impressum(None) is False


# ── Finden ────────────────────────────────────────────────────────────

def test_der_verweis_der_startseite_kommt_zuerst():
    kandidaten = impressum_kandidaten("https://alkozei.de", STARTSEITE)

    assert kandidaten[0] == "https://alkozei.de/impressum"


def test_der_anwendungspfad_wird_mitprobiert():
    """Der Pfad steht im Quelltext, nur nicht im href — dort steht er tot."""
    kandidaten = impressum_kandidaten("https://alkozei.de", STARTSEITE)

    assert "https://alkozei.de/now.using/nBito/impressum" in kandidaten


def test_die_festen_pfade_bleiben_als_rueckfall():
    kandidaten = impressum_kandidaten("https://beispiel.de", "<html></html>")

    assert "https://beispiel.de/impressum" in kandidaten
    assert "https://beispiel.de/imprint" in kandidaten


def test_keine_adresse_kommt_doppelt_vor():
    kandidaten = impressum_kandidaten("https://alkozei.de", STARTSEITE)

    assert len(kandidaten) == len(set(kandidaten))


def test_fremde_domains_werden_nicht_verfolgt():
    """Ein Impressum-Link auf eine andere Domain gehört einem anderen."""
    html = '<a href="https://fremde-agentur.de/impressum">Impressum</a>'

    kandidaten = impressum_kandidaten("https://beispiel.de", html)

    assert not any("fremde-agentur.de" in k for k in kandidaten)


def test_die_liste_bleibt_begrenzt():
    """Jeder Kandidat kostet einen Abruf — es darf nicht ausufern."""
    viele = "".join(f'<a href="impressum-{i}">x</a>' for i in range(50))

    kandidaten = impressum_kandidaten("https://beispiel.de", viele)

    assert len(kandidaten) <= 12
