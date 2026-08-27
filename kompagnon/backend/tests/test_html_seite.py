# -*- coding: utf-8 -*-
"""Eine hochgeladene HTML-Datei wird eine bearbeitbare Seite (Bitte David).

**Die wichtigste Zusicherung ist nicht, dass etwas entfernt wird, sondern
dass es gesagt wird.** Wer eine Seite hochlädt und sie danach nicht
wiedererkennt, sucht den Fehler bei sich. Still zu entfernen wäre schlimmer
als abzulehnen.

**Und die zweite: dass der Inhalt heil bleibt.** Ein Reiniger, der zu viel
mitnimmt, ist kein Schutz, sondern ein Datenverlust mit Begründung.
"""
import pytest

from services import html_seite


BEISPIEL = """<!doctype html>
<html lang="de">
<head>
  <title>Meine Seite</title>
  <meta name="description" content="Kurz beschrieben">
  <style>body { color: rebeccapurple; }</style>
</head>
<body>
  <h1>Willkommen</h1>
  <p onclick="alert('hallo')">Ein Absatz</p>
  <a href="javascript:void(0)">Ein Link</a>
  <script>console.log('boese');</script>
  <iframe src="https://fremd.example"></iframe>
</body>
</html>"""


def test_der_inhalt_bleibt_erhalten():
    """Die Gegenprobe zuerst: Ein Reiniger, der zu viel mitnimmt, ist ein
    Datenverlust mit Begründung."""
    ergebnis = html_seite.einlesen(BEISPIEL)

    assert "<h1>Willkommen</h1>" in ergebnis["html"]
    assert "Ein Absatz" in ergebnis["html"]
    assert "Ein Link" in ergebnis["html"]


def test_titel_und_beschreibung_kommen_aus_dem_kopf():
    ergebnis = html_seite.einlesen(BEISPIEL)

    assert ergebnis["titel"] == "Meine Seite"
    assert ergebnis["beschreibung"] == "Kurz beschrieben"


def test_stile_wandern_ins_eigene_feld():
    """Sonst stehen sie als Text mitten im Rumpf und der Editor zeigt sie an."""
    ergebnis = html_seite.einlesen(BEISPIEL)

    assert "rebeccapurple" in ergebnis["css"]
    assert "rebeccapurple" not in ergebnis["html"]


def test_nur_der_rumpf_wird_uebernommen():
    """`<html>` und `<head>` gehören nicht in eine eingebettete Seite —
    sonst stehen zwei Dokumente ineinander."""
    ergebnis = html_seite.einlesen(BEISPIEL)

    assert "<head>" not in ergebnis["html"]
    assert "<!doctype" not in ergebnis["html"].lower()


# ── Was entfernt wird ─────────────────────────────────────────────────

@pytest.mark.parametrize("muster", ["<script", "console.log", "<iframe",
                                    "onclick", "javascript:"])
def test_ausfuehrbares_verschwindet(muster):
    ergebnis = html_seite.einlesen(BEISPIEL)

    assert muster not in ergebnis["html"], (
        f"{muster!r} steht noch in der gespeicherten Seite")


def test_und_es_wird_gemeldet():
    """**Die eigentliche Zusicherung.** Ohne die Meldung sucht der
    Hochladende den Unterschied zwischen Datei und Seite bei sich."""
    ergebnis = html_seite.einlesen(BEISPIEL)
    satz = html_seite.meldung(ergebnis["entfernt"])

    assert satz, "Es wurde entfernt und nichts gesagt"
    for erwartet in ("Skriptblock", "Rahmen", "Ereignis-Attribut",
                     "javascript:-Adresse"):
        assert erwartet in satz, f"{erwartet} fehlt in der Meldung: {satz}"


def test_eine_saubere_datei_meldet_nichts():
    """Die Gegenprobe. Ohne sie wäre die Meldung auch dann „richtig", wenn sie
    immer erschiene — und dann glaubt ihr niemand mehr."""
    ergebnis = html_seite.einlesen(
        "<html><body><h1>Sauber</h1><p>Nur Text.</p></body></html>")

    assert ergebnis["entfernt"] == []
    assert html_seite.meldung(ergebnis["entfernt"]) == ""


def test_ein_wort_im_fliesstext_wird_nicht_entfernt():
    """`onclick` in einem Absatz ist Text, kein Attribut.

    Mit einem Muster über die Zeichenkette wäre das nicht zu unterscheiden —
    deshalb liest der Dienst den Baum.
    """
    ergebnis = html_seite.einlesen(
        "<body><p>Das Attribut onclick sollte man meiden.</p></body>")

    assert "onclick" in ergebnis["html"]
    assert ergebnis["entfernt"] == []


# ── Der Bezeichner ────────────────────────────────────────────────────

@pytest.mark.parametrize("eingabe,erwartet", [
    ("Meine Seite", "meine-seite"),
    ("Über uns", "ueber-uns"),
    ("Preise & Pakete", "preise-pakete"),
    ("  ", "seite"),
    ("", "seite"),
])
def test_der_bezeichner_taugt_fuer_eine_adresse(eingabe, erwartet):
    assert html_seite.slug_aus(eingabe) == erwartet
