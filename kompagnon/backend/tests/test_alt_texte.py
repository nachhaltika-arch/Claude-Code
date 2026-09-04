# -*- coding: utf-8 -*-
"""Alt-Texte — was ein Inhaltsbild ist und was keines (L-152).

**Der Anlass (04.09.2026).** Ein Betrieb hat den Bericht an seiner eigenen
Seite gegengeprueft: Die Alt-Texte sind vorhanden, der Bericht gab 0 von 2.

**Der Code widersprach dem eigenen Standard.** Die Abstufung des Kriteriums
spricht woertlich von „Inhaltsbildern"; gezaehlt wurden alle `<img>`-Elemente,
die im Quelltext stehen. Zwei Gruppen gehoeren nicht dazu:

* **`alt=""` ist korrektes Markup**, kein Mangel. Es kennzeichnet ein
  dekoratives Bild und ist nach WCAG genau der richtige Weg — es als fehlenden
  Alternativtext zu zaehlen bestraft den Betrieb dafuer, dass er es richtig
  gemacht hat. Dasselbe gilt fuer `role="presentation"` und `aria-hidden`.
* **Zaehlpixel und Trennlinien** sind keine Inhalte. Ein 1x1-Pixel wiegt sonst
  so schwer wie das Bild der Werkstatt.

Beide fallen aus **Zaehler und Nenner** — dieselbe Regel wie bei einer nicht
erhobenen Messung: Was nicht zur Sache gehoert, wird weder gutgeschrieben noch
angelastet.
"""
from bs4 import BeautifulSoup

from services.qa_scanner import alt_text_befund


def _befund(html: str) -> dict:
    return alt_text_befund(BeautifulSoup(html, "html.parser"))


# ── Dekorative Bilder ─────────────────────────────────────────────────

def test_ein_leeres_alt_ist_korrekt_und_zaehlt_nicht_als_mangel():
    befund = _befund('<img src="a.jpg" alt="Werkstatt"><img src="deko.svg" alt="">')

    assert befund["bilder_inhalt"] == 1
    assert befund["bilder_dekorativ"] == 1
    assert befund["alt_texte_quote"] == 100


def test_role_presentation_und_aria_hidden_zaehlen_ebenfalls_als_dekorativ():
    befund = _befund(
        '<img src="a.jpg" alt="Bad"><img src="b.svg" role="presentation">'
        '<img src="c.svg" aria-hidden="true"><img src="d.svg" role="none">')

    assert befund["bilder_inhalt"] == 1
    assert befund["bilder_dekorativ"] == 3
    assert befund["alt_texte_quote"] == 100


def test_ein_fehlendes_alt_attribut_bleibt_ein_mangel():
    """`alt=""` und **gar kein** `alt` sind nicht dasselbe: Das eine sagt
    „dieses Bild traegt keine Information", das andere sagt gar nichts."""
    befund = _befund('<img src="a.jpg" alt="Bad"><img src="b.jpg">')

    assert befund["bilder_inhalt"] == 2
    assert befund["bilder_mit_alt"] == 1
    assert befund["alt_texte_quote"] == 50


# ── Zählpixel ─────────────────────────────────────────────────────────

def test_ein_zaehlpixel_ist_kein_inhaltsbild():
    befund = _befund(
        '<img src="a.jpg" alt="Heizung">'
        '<img src="https://t.example/p.gif" width="1" height="1">')

    assert befund["bilder_inhalt"] == 1
    assert befund["bilder_pixel"] == 1
    assert befund["alt_texte_quote"] == 100


def test_ein_grosses_bild_bleibt_ein_inhaltsbild():
    befund = _befund('<img src="a.jpg" width="800" height="600">')

    assert befund["bilder_inhalt"] == 1
    assert befund["bilder_pixel"] == 0
    assert befund["alt_texte_quote"] == 0


# ── Randfälle ─────────────────────────────────────────────────────────

def test_ohne_bilder_bleibt_es_bei_der_bisherigen_lesart():
    """Eine Seite ganz ohne Bilder verliert hier nichts — das war vorher so
    und wird durch diesen Fund nicht mitentschieden."""
    assert _befund("<p>Nur Text</p>")["alt_texte_quote"] == 100


def test_nur_dekorative_bilder_ergeben_keinen_mangel():
    befund = _befund('<img src="a.svg" alt=""><img src="b.svg" alt="">')

    assert befund["bilder_inhalt"] == 0
    assert befund["alt_texte_quote"] == 100


def test_der_befund_nennt_alle_drei_gruppen():
    """Der Bericht soll belegen koennen, warum der Nenner kleiner ist als die
    Zahl der Bilder auf der Seite (L-151)."""
    befund = _befund(
        '<img src="a.jpg" alt="Bad"><img src="b.jpg">'
        '<img src="c.svg" alt=""><img src="p.gif" width="1" height="1">')

    assert befund["bilder_gesamt"] == 4
    assert befund["bilder_inhalt"] == 2
    assert befund["bilder_dekorativ"] == 1
    assert befund["bilder_pixel"] == 1


# ── Der Weg in den Bericht ────────────────────────────────────────────

def test_der_beleg_erklaert_den_kleineren_nenner():
    """Ohne diesen Satz wundert sich ein Betrieb, warum von zwoelf Bildern
    nur fuenf gewertet wurden (L-151)."""
    from services.audit_scoring import score_audit
    from test_audit_scoring import _fakten

    fakten = _fakten()
    fakten["qa"] = {**fakten["qa"], "alt_texte_quote": 50, "bilder_inhalt": 4,
                    "bilder_mit_alt": 2, "bilder_dekorativ": 3, "bilder_pixel": 1}

    beleg = score_audit(fakten)["belege"]["bf_alt"]

    assert "2 von 4 Inhaltsbildern" in beleg
    assert "4 dekorativ oder Zählpixel" in beleg
