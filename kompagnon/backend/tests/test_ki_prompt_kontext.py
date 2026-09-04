# -*- coding: utf-8 -*-
"""Was das Modell zu sehen bekommt — und was es daraus nicht schliessen darf.

**Der Anlass (L-150, 04.09.2026).** Ein Fremdleser hat den Bericht fuer seine
Seite gegengeprueft und zwei Behauptungen widerlegt, die beide aus dem
Modellaufruf stammen:

* Ein Blogbeitrag vom **12.08.2026** wurde als „in die Zukunft datiert"
  beanstandet. Im Prompt stand **kein heutiges Datum**; das Modell hat gegen
  seine eigene Zeitvorstellung geurteilt.
* „Die Preise stehen erst in der FAQ; auf der Startseite fehlt oben ein
  Hinweis." Der Preis steht prominent auf der Startseite. **Die Ueberschrift
  des Textblocks war falsch:** Sie sagte `SEITENTEXT DER STARTSEITE`, waehrend
  `_gesamttext` den Text **aller** erhobenen Seiten uebergibt, jedes Stueck mit
  seiner Adresse in eckigen Klammern davor. Das Modell bekam also die ganze
  Website und die Anweisung, sie fuer die Startseite zu halten.

Beides sind Fehler in dem, was wir dem Modell sagen — nicht in dem, was es
kann. Diese Tests halten die Angaben fest.
"""
from datetime import date

import pytest

from services.audit_ai import _user_content


FAKTEN = {
    "company_name": "Muster GmbH", "trade": "Heizung", "city": "Bochum",
    "url": "https://muster.de",
    "page_text": "[https://muster.de]\nWir bauen Baeder.\n\n"
                 "[https://muster.de/faq]\nWas kostet das? Ab 750 Euro.",
    "seiten": {"collected": True, "geprueft": 2,
               "seiten": ["https://muster.de", "https://muster.de/faq"]},
}


def _text(fakten=None, heute=None) -> str:
    """Der Textblock des Aufrufs — der Bildteil interessiert hier nicht."""
    inhalt = _user_content(fakten or FAKTEN, {}, None, "", heute=heute)
    return " ".join(t["text"] for t in inhalt if t["type"] == "text")


# ── Das Datum ─────────────────────────────────────────────────────────

def test_der_prompt_nennt_das_heutige_datum():
    """Ohne diesen Satz beurteilt das Modell Datumsangaben gegen sein eigenes
    Zeitgefuehl — und haelt einen Beitrag von vorgestern fuer zukuenftig."""
    assert "04.09.2026" in _text(heute=date(2026, 9, 4))


def test_das_datum_folgt_dem_erhebungstag_und_nicht_der_uhr_des_lesers():
    assert "15.01.2026" in _text(heute=date(2026, 1, 15))
    assert "04.09.2026" not in _text(heute=date(2026, 1, 15))


def test_der_prompt_sagt_wie_datumsangaben_zu_lesen_sind():
    """Das Datum allein genuegt nicht — die Regel dazu muss dastehen."""
    text = _text(heute=date(2026, 9, 4)).lower()

    assert "vergangenheit" in text
    assert "zukunft" in text


def test_ohne_angabe_gilt_der_heutige_tag():
    heute = date.today().strftime("%d.%m.%Y")

    assert heute in _text()


# ── Die Seitenzuordnung ───────────────────────────────────────────────

def test_der_textblock_behauptet_nicht_mehr_die_startseite():
    """Die alte Ueberschrift war schlicht falsch: uebergeben wird der Text
    aller erhobenen Seiten."""
    assert "SEITENTEXT DER STARTSEITE" not in _text()


def test_der_prompt_erklaert_die_adressmarken_im_text():
    """`_gesamttext` stellt jedem Stueck seine Adresse in eckigen Klammern
    voran. Wer das nicht weiss, liest die ganze Website als eine Seite."""
    text = _text()

    assert "[" in text and "]" in text
    assert "adresse" in text.lower()


def test_der_prompt_nennt_die_erhobenen_seiten():
    text = _text()

    assert "https://muster.de/faq" in text


def test_ohne_unterseiten_wird_keine_zweite_seite_behauptet():
    """Eine Seite ohne Unterseiten darf nicht so aussehen, als haetten wir
    mehr geprueft, als wir geprueft haben."""
    nur_start = {
        **FAKTEN,
        "page_text": "[https://muster.de]\nWir bauen Baeder.",
        "seiten": {"collected": True, "geprueft": 1,
                   "seiten": ["https://muster.de"]},
    }
    text = _text(nur_start)

    assert "https://muster.de/faq" not in text
    assert "1 Seite" in text or "eine Seite" in text.lower()


def test_der_prompt_untersagt_ortsangaben_ohne_beleg():
    """Der zweite Fehlbefund war eine Aussage ueber Platzierung. Sie ist
    zulaessig — aber nur anhand der Adressmarken, nicht aus dem Gefuehl."""
    assert "belegen" in _text().lower() or "beleg" in _text().lower()
