# -*- coding: utf-8 -*-
"""Die Abo-Zahlen stehen im Datenblatt — und der Code muss sie treffen (L-101).

**Der Anlass ist ein eigener Fehler vom 01.09.2026.** Kontingente und
Prüftakt kamen aus dem Fließtext des Lagebild-Eintrags („Pro zusätzlich zwei
Stunden", „BAS sagt keine Änderungsstunden zu"). Im Produktdatenblatt
`docs/produkte/abo-und-geo.md` steht anderes:

* Position 5 — ABO-BAS: **Inhaltsänderungen bis 30 Minuten** je Monat
* Position 8 — ABO-PRO: **bis 90 Minuten (statt 30)** — nicht *zusätzlich*
* Position 7 — ABO-BAS: **jährliches** Re-Audit
* Position 10 — ABO-PRO: **quartalsweises** Re-Audit statt jährlich

Beide Abweichungen kosten Geld, und zwar in verschiedene Richtungen: Mit 0,0
Stunden für Basic wäre **jede** Minute eine Überschreitung gewesen, und wir
hätten berechnet, was im Preis steht. Mit 2,0 statt 1,5 für Pro hätten wir
monatlich eine halbe Stunde verschenkt. Vier statt einer Prüfung im Jahr für
einen Basic-Kunden wären viermal Guthaben.

**Warum dieser Test die Datei liest, statt Zahlen zu wiederholen.** Ein Test,
der `1.5 == 1.5` prüft, hält nur fest, was jemand zweimal geschrieben hat.
Dieser hier liest das Datenblatt und rechnet die Minuten in Stunden um — wer
das Produkt ändert, ohne den Code nachzuziehen, wird rot.

**Ein Summentext ist keine Produktdefinition.** Das ist die Lehre.
"""
import pathlib
import re

import pytest

from services import abo_stunden

DATENBLATT = (pathlib.Path(__file__).resolve().parent.parent.parent.parent
              / "docs" / "produkte" / "abo-und-geo.md")


@pytest.fixture(scope="module")
def blatt():
    if not DATENBLATT.exists():
        pytest.fail(f"Produktdatenblatt fehlt: {DATENBLATT}")
    return DATENBLATT.read_text(encoding="utf-8")


def _minuten(text: str, muster: str) -> int:
    treffer = re.search(muster, text)
    assert treffer, f"Zeile nicht gefunden: {muster}"
    return int(treffer.group(1))


# ── Die Kontingente ──────────────────────────────────────────────────

def test_abo_bas_traegt_die_minuten_aus_dem_datenblatt(blatt):
    minuten = _minuten(blatt, r"Inhaltsänderungen bis (\d+) Minuten\*\*\s*\|")
    assert minuten == 30, "Position 5 des Leistungsverzeichnisses"
    assert abo_stunden.KONTINGENT_ABO_BAS_STUNDEN == minuten / 60


def test_abo_pro_ersetzt_die_minuten_und_addiert_sie_nicht(blatt):
    """**Der teure Halbsatz.** „(statt 30)" — nicht „zusätzlich"."""
    treffer = re.search(r"bis (\d+) Minuten\*\* \(statt (\d+)\)", blatt)
    assert treffer, "Position 8 des Leistungsverzeichnisses"
    neu, alt = int(treffer.group(1)), int(treffer.group(2))
    assert (neu, alt) == (90, 30)
    assert abo_stunden.KONTINGENT_ABO_PRO_STUNDEN == neu / 60
    assert abo_stunden.KONTINGENT_ABO_PRO_STUNDEN != (neu + alt) / 60, \
        'statt heisst ersetzen, nicht addieren'


def test_basic_hat_ein_kontingent_und_nicht_null():
    """Null waere eine andere Zusage als „30 Minuten" — und jede Minute eines
    Basic-Kunden erschiene als Überschreitung."""
    assert abo_stunden.KONTINGENT_ABO_BAS_STUNDEN > 0


# ── Der Prüftakt ─────────────────────────────────────────────────────

def test_der_takt_folgt_dem_datenblatt(blatt):
    from services.quartals_reaudit import TAKT_MONATE

    assert "Jährliches Re-Audit" in blatt, "Position 7 (ABO-BAS)"
    assert "Quartalsweises Re-Audit" in blatt, "Position 10 (ABO-PRO)"
    assert TAKT_MONATE["ABO-BAS"] == 12
    assert TAKT_MONATE["ABO-PRO"] == 3


# ── Die Preise ───────────────────────────────────────────────────────

def test_die_preise_stehen_wie_im_datenblatt(blatt):
    preise = [int(x) for x in re.findall(r"\*\*(\d+) € netto / Monat\*\*", blatt)]
    assert preise == [79, 149], f"gefunden: {preise}"
    assert abo_stunden.PREIS_ABO_BAS_NETTO_CENT == 79 * 100
    assert abo_stunden.PREIS_ABO_PRO_NETTO_CENT == 149 * 100


def test_der_steuersatz_ist_neunzehn_prozent(blatt):
    """Nicht sieben: Das Buch ist ermäßigt, eine Dienstleistung nicht."""
    assert "| Umsatzsteuer | 19 %" in blatt
    assert abo_stunden.STEUERSATZ_ABO == 19.0


def test_die_preise_sind_im_datenblatt_noch_als_annahme_gekennzeichnet(blatt):
    """**Kein Mangel, sondern eine Zusicherung mit Verfallsdatum.**

    Solange dort „⚠️ Annahme" steht, ist jede Abrechnung damit eine Annahme —
    und der Abrechnungslauf sagt das auch. Verschwindet die Kennzeichnung,
    wird dieser Test rot und erinnert daran, den Hinweis aus dem Lauf zu
    nehmen. Ein Vorbehalt, den niemand zurücknimmt, steht ewig da und wird
    irgendwann überlesen.
    """
    assert "⚠️ Annahme" in blatt
