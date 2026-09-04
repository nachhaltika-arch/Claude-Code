# -*- coding: utf-8 -*-
'''Was der Kunde an einem Mitwirkungspunkt tun kann (04.09.2026).

**Der Anlass.** „Was wir brauchen" war eine Liste zum Abhaken: Der Kunde las,
was fehlt, erledigte es woanders und bestätigte hier, dass er es getan habe.
David beim Ansehen: „hier kann der Kunde nicht wirklich was machen."

**Der wichtigste Test dieser Datei ist der letzte.** M1 und M9 handeln von
Zugängen — zur Domainverwaltung und zum alten Redaktionssystem. Ein Feld dafür
wäre bequem und falsch: Es lieferte uns fremde Passwörter im Klartext in eine
Notizspalte, mit allem, was daran hängt. Der Test hält fest, dass es kein
solches Feld gibt und auch keines dazukommt.
'''
import pytest

from services import mitwirkung as kat


def test_jeder_punkt_hat_eine_aktion():
    """Ohne Aktion bliebe eine Karte eine Zeile zum Abhaken."""
    for punkt in kat.KATALOG:
        assert punkt.aktion, f"{punkt.kennung} ohne Aktion"


def test_die_aktionen_sind_die_bekannten():
    """Ein Tippfehler wäre eine Karte, die gar nichts anbietet — die
    Oberfläche fällt dann auf den Haken zurück, ohne dass etwas rot wird."""
    bekannt = {kat.AKTION_ABHAKEN, kat.AKTION_DATEIEN, kat.AKTION_DOMAIN,
               kat.AKTION_PERSON, kat.AKTION_TERMIN, kat.AKTION_TEXTE,
               kat.AKTION_FREIGABE, kat.AKTION_ANGABEN}

    for punkt in kat.KATALOG:
        assert punkt.aktion in bekannt, f"{punkt.kennung}: {punkt.aktion}"


def test_die_punkte_die_david_genannt_hat():
    """Bilder hochladen, Texte freigeben, Adresse eintragen, wer entscheidet,
    Termin buchen — die fünf aus der Rückmeldung, je an ihrem Punkt."""
    erwartet = {
        "M1": kat.AKTION_DOMAIN,    # Internet-Adresse
        "M2": kat.AKTION_TEXTE,     # Texte liefern oder schreiben lassen
        "M3": kat.AKTION_DATEIEN,   # Logo und Bilder hochladen
        "M5": kat.AKTION_PERSON,    # wer entscheidet
        "M6": kat.AKTION_TERMIN,    # Positionierungsgespräch
        "M8": kat.AKTION_FREIGABE,  # Texte freigeben
    }
    for kennung, aktion in erwartet.items():
        assert kat.NACH_KENNUNG[kennung].aktion == aktion, kennung


def test_dateipunkte_sagen_wofuer_die_datei_steht():
    """Sonst landet das Logo unter `sonstiges` und der Innendienst sucht."""
    for punkt in kat.KATALOG:
        if punkt.aktion == kat.AKTION_DATEIEN:
            assert punkt.dateiart != "sonstiges", punkt.kennung


# ── Was aus den Angaben wird ─────────────────────────────────────────

def test_die_notiz_entsteht_aus_dem_katalog():
    """Der Kunde schreibt sie nicht selbst — aus ihr wird der Nachweis."""
    notiz = kat.notiz_bauen("M5", {
        "name": "Anke Berger", "rolle": "Bürokraft",
        "email": "anke@example.de", "telefon": "0234 555111"})

    assert "Anke Berger" in notiz
    assert "Bürokraft" in notiz
    assert notiz.startswith("Name:")


def test_ein_fremdes_feld_faellt_heraus():
    """**Der Grund, warum die Notiz gebaut und nicht übernommen wird.** Sonst
    könnte ein Aufrufer bestimmen, was im Nachweis steht, aus dem später der
    Fristbeginn abgeleitet wird."""
    notiz = kat.notiz_bauen("M5", {
        "name": "Anke Berger", "freigabe_erteilt": "ja am 1.1.", "rolle": ""})

    assert "Anke Berger" in notiz
    assert "freigabe_erteilt" not in notiz
    assert "1.1." not in notiz


def test_die_wahl_wird_ausgeschrieben():
    """`kompagnon` sagt einem Menschen nichts; der Satz dahinter schon."""
    notiz = kat.notiz_bauen("M1", {"adresse": "beispiel.de", "wahl": "kompagnon"})

    assert "beispiel.de" in notiz
    assert "Melden Sie sich bei mir" in notiz


def test_eine_wahl_die_es_nicht_gibt_wird_verschwiegen():
    """Lieber eine Zeile ohne Wahl als eine erfundene."""
    notiz = kat.notiz_bauen("M1", {"adresse": "beispiel.de", "wahl": "irgendwas"})

    assert notiz == "Ihre Internet-Adresse: beispiel.de"


def test_die_notiz_passt_in_die_spalte():
    """`mitwirkung_stand.notiz` ist 255 Zeichen lang — ein längerer Wert
    scheitert erst beim Schreiben, also nach dem Klick des Kunden."""
    lang = kat.notiz_bauen("M5", {"name": "A" * 300, "hinweis": "B" * 900})

    assert len(lang) <= 255


def test_leere_angaben_ergeben_keine_notiz():
    """Ein Punkt darf auch ohne Angabe abhakbar bleiben."""
    assert kat.notiz_bauen("M5", {}) == ""
    assert kat.notiz_bauen("M9", {"irgendwas": "x"}) == ""


# ── Die Grenze, die bleiben muss ─────────────────────────────────────

def test_kein_feld_nimmt_zugangsdaten_entgegen():
    """**Die wichtigste Zusicherung dieser Datei.**

    M1 und M9 handeln von Zugängen. Ein Feld dafür lieferte uns fremde
    Passwörter im Klartext in eine Notizspalte — mit Sicherung, Protokoll,
    Löschfrist und Haftung daran. Der Kunde entscheidet stattdessen, **wer
    einträgt**; braucht es Zugang, melden wir uns.

    Der Test prüft **alle** Punkte, nicht nur die zwei: Ein solches Feld darf
    auch anderswo nicht entstehen.
    """
    verboten = ("passwort", "password", "kennwort", "zugangsdaten", "pin",
                "secret", "token", "api_key", "benutzername", "login")

    for punkt in kat.KATALOG:
        for feld, beschriftung in kat.felder_fuer(punkt.kennung):
            for wort in verboten:
                assert wort not in feld.lower(), f"{punkt.kennung}: Feld {feld}"
                assert wort not in beschriftung.lower(), \
                    f"{punkt.kennung}: Beschriftung „{beschriftung}“"


def test_der_zugangspunkt_bietet_gar_kein_formular():
    """M9 (Zugang zum alten System) bleibt bewusst beim Haken — die Sache
    gehört ins Gespräch, nicht in ein Feld."""
    assert kat.NACH_KENNUNG["M9"].aktion == kat.AKTION_ABHAKEN
    assert kat.felder_fuer("M9") == ()
