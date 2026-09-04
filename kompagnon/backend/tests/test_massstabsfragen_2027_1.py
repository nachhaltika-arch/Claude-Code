# -*- coding: utf-8 -*-
"""Der heutige Zustand der offenen Massstabsfragen — festgehalten, nicht gebilligt.

**Wozu diese Tests da sind (L-154, 04.09.2026).** Drei Kriterien bewerten
denselben Karteneinbau verschieden: `rc_cookie` gibt 0 von 4, `si_drittanbieter`
gibt volle 2, und `se_lokal` schreibt dafuer sogar einen Punkt gut. Das ist
belegt, dokumentiert und **bewusst nicht behoben** — die Aufloesung verschiebt
Punkte auf realen Seiten und gehoert deshalb in die Fassung 2027.1
(`docs/Audit/fassung-2027-1-offene-massstabsfragen.md`, Abschnitt 8).

Dieselbe Bauart wie bei L-114: **Die Tests beziffern den Widerspruch, statt
ihn zu verbieten.** Sie werden rot, wenn eines der drei Kriterien allein
wandert — dann ist entweder die Fassung 2027.1 gekommen und dieser Test
gehoert angepasst, oder jemand hat den Massstab versehentlich verschoben.

Ein vertagter Befund ohne Test ist nur ein leiseres Wort fuer vergessen.
"""
from services.audit_criteria import Source
from services.audit_scoring import score_audit

from test_audit_scoring import _fakten


def _mit_karte(**mehr):
    """Eine Seite mit Karteneinbau und ohne Consent-Werkzeug."""
    fakten = _fakten(
        consent={"collected": True, "cmp_detected": False},
        third_parties={"collected": True, "count": 1, "services": ["google_maps"],
                       "tracking_services": [], "external_fonts": False,
                       "maps_embedded": True},
        **mehr,
    )
    fakten["qa"] = {**fakten["qa"], "google_maps": True}
    return fakten


def test_drei_kriterien_urteilen_heute_verschieden():
    """Der Widerspruch in einer Zeile. Wandert eines allein, wird das hier rot."""
    ergebnis = score_audit(_mit_karte())

    assert ergebnis["items"]["rc_cookie"] == 0, "rc_cookie zaehlt jeden Drittanbieter"
    assert ergebnis["items"]["si_drittanbieter"] == 2, "si_drittanbieter sieht nur Fonts und Tracking"
    assert ergebnis["items"]["se_lokal"] == 3, "se_lokal wertet die Karte als lokales Signal"


def test_der_beleg_nennt_den_ausloeser_auch_solange_der_widerspruch_steht():
    """Was heute schon geht, ohne den Massstab anzufassen (L-151): Der Bericht
    sagt, **welcher** Dienst den Abzug ausloest. Genau daran ist die Rueckfrage
    des Fremdlaufs entstanden."""
    belege = score_audit(_mit_karte())["belege"]

    assert "google_maps" in belege["rc_cookie"]


def test_maps_embedded_wird_weiter_erhoben():
    """Es liest heute kein Kriterium — geloescht werden darf es trotzdem nicht.

    Weg A der Fassung 2027.1 (`si_drittanbieter` zieht nach) braucht genau
    diese Messung. Wer sie vorher entfernt, muss sie dann neu bauen.
    """
    from services.audit_collectors import detect_third_parties

    befund = detect_third_parties('<iframe src="https://maps.google.com/x"></iframe>')

    assert befund["maps_embedded"] is True
    assert befund["count"] == 1
    assert befund["tracking_services"] == []


def test_dg_mobil_misst_heute_nur_die_viewport_angabe():
    """Ein `meta viewport` steht in jeder Vorlage der letzten zehn Jahre.

    Festgehalten, damit die Aenderung auf die gerenderte Breite (Abschnitt 8)
    als das erscheint, was sie ist: eine Massstabsaenderung, kein Aufraeumen.
    """
    fakten = _fakten()
    fakten["qa"] = {**fakten["qa"], "mobile_viewport": True}
    assert score_audit(fakten)["items"]["dg_mobil"] == 1

    fakten["qa"] = {**fakten["qa"], "mobile_viewport": False}
    ergebnis = score_audit(fakten)
    assert ergebnis["items"]["dg_mobil"] == 0
    assert ergebnis["sources"]["dg_mobil"] == Source.MEASURED.value
