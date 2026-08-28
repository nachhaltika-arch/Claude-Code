# -*- coding: utf-8 -*-
"""Die Grundgesamtheit von C7 ist die auswertbare, nicht die gezaehlte (L-126).

**Der Anlass, gemessen am 28.08.2026 auf dem Produktivbestand.** Das Werkzeug
meldete in der Kopfzeile „Grundgesamtheit: 116 abgeschlossene Pruefungen" und
darunter Nenner von 4 bis 8. Beides stimmte — es waren nur zwei verschiedene
Dinge: **108 der 116** Zeilen stehen zwar auf `completed`, tragen aber
**keine** Kriterien (`item_scores` leer). Es sind Huellen aus der Zeit vor der
heutigen Erhebung, Maerz bis Juli. Auswertbar sind **8**, alle vom 16.08. bis
26.08.

**Warum das kein Schoenheitsfehler ist.** Diese Zahlen gehen in den
Methodenteil eines Buchs. Drei Angaben waren betroffen, alle aus derselben
Ursache:

* die Grundgesamtheit (116 statt 8),
* der Erhebungszeitraum (30.03.–26.08. statt 16.08.–26.08.),
* die Warnung „mehrere Fassungen" — das „ohne Vermerk" kam von den Huellen.

Eine Kennzahl, die aus zwei Feldern abgeleitet wird, geht auseinander, sobald
nur eines gepflegt wird. Hier war es die Statusspalte ohne den Inhalt.

**Die verworfenen Zeilen werden benannt, nicht verschwiegen.** Eine
Grundgesamtheit, die stillschweigend schrumpft, ist genauso wenig
nachvollziehbar wie eine zu grosse.
"""
from datetime import datetime

from services.befund_haeufigkeit import aufteilen, kopfzeilen

VOLL = {"ih_impressum": 2, "se_struktur": 1}


def _zeile(scores, wann, fassung="2026.2"):
    return (scores, {}, datetime.fromisoformat(wann), fassung)


def test_huellen_ohne_kriterien_zaehlen_nicht_zur_grundgesamtheit():
    # Arrange — zwei echte, drei Huellen
    zeilen = [
        _zeile(VOLL, "2026-08-16T10:00"),
        _zeile(VOLL, "2026-08-26T10:00"),
        _zeile({}, "2026-03-30T10:00", "ohne Vermerk"),
        _zeile({}, "2026-04-02T10:00", "ohne Vermerk"),
        _zeile({}, "2026-07-01T10:00", "ohne Vermerk"),
    ]

    # Act
    auswertbar, verworfen = aufteilen(zeilen)

    # Assert
    assert len(auswertbar) == 2
    assert len(verworfen) == 3


def test_der_erhebungszeitraum_stammt_aus_den_auswertbaren():
    """Sonst nennt das Buch einen Zeitraum, in dem gar nicht erhoben wurde."""
    # Arrange
    zeilen = [
        _zeile({}, "2026-03-30T10:00", "ohne Vermerk"),
        _zeile(VOLL, "2026-08-16T10:00"),
        _zeile(VOLL, "2026-08-26T10:00"),
    ]

    # Act
    kopf = kopfzeilen(*aufteilen(zeilen))

    # Assert
    assert "16.08.2026 bis 26.08.2026" in kopf
    assert "30.03.2026" not in kopf


def test_die_fassungswarnung_kommt_nicht_von_den_huellen():
    """„ohne Vermerk" der leeren Zeilen ist keine zweite Fassung des Massstabs."""
    # Arrange
    zeilen = [
        _zeile(VOLL, "2026-08-16T10:00", "2026.2"),
        _zeile(VOLL, "2026-08-26T10:00", "2026.2"),
        _zeile({}, "2026-04-02T10:00", "ohne Vermerk"),
    ]

    # Act
    kopf = kopfzeilen(*aufteilen(zeilen))

    # Assert
    assert "Mehrere Fassungen" not in kopf


def test_echte_fassungsmischung_wird_weiterhin_gemeldet():
    """Die Gegenprobe — sonst haette ich die Warnung nur stummgeschaltet."""
    # Arrange
    zeilen = [
        _zeile(VOLL, "2026-08-16T10:00", "2026.1"),
        _zeile(VOLL, "2026-08-26T10:00", "2026.2"),
    ]

    # Act
    kopf = kopfzeilen(*aufteilen(zeilen))

    # Assert
    assert "Mehrere Fassungen" in kopf


def test_die_verworfenen_werden_benannt():
    """Eine stillschweigend geschrumpfte Grundgesamtheit ist auch nicht pruefbar."""
    # Arrange
    zeilen = [_zeile(VOLL, "2026-08-16T10:00")] + [
        _zeile({}, "2026-04-02T10:00", "ohne Vermerk") for _ in range(108)]

    # Act
    kopf = kopfzeilen(*aufteilen(zeilen))

    # Assert
    assert "1 auswertbare" in kopf
    assert "108" in kopf


def test_ohne_huellen_bleibt_die_kopfzeile_schlicht():
    # Arrange
    zeilen = [_zeile(VOLL, "2026-08-16T10:00"), _zeile(VOLL, "2026-08-26T10:00")]

    # Act
    kopf = kopfzeilen(*aufteilen(zeilen))

    # Assert
    assert "2 auswertbare" in kopf
    assert "weitere" not in kopf
