# -*- coding: utf-8 -*-
"""Die Bauzeit steht ueberall gleich — im Datenblatt wie im Katalog (L-182).

**Der Befund vom 07.09.2026.** Beim Vergleich der vier Datenblatt-Ordner fiel
etwas auf, das mit den vier Ordnern gar nichts zu tun hat: Im **geltenden**
Ordner sagen die acht Datenblaetter „14 Werktage / 28 Werktage / 42 Werktage",
die `KAS_Produktarchitektur_Websprint_v1.0.md` daneben aber „14 Tage | 28 Tage
| 42 Tage". Zwei Angaben zur selben Frist, im selben Ordner, und die eine ist
die Fassung von vor der Entscheidung.

**Warum ausgerechnet diese Zahl.** An ihr haengt die Verzugspauschale: 100 €
je angefangenem Verzugstag. 28 Kalendertage sind vier Wochen, 28 Werktage
knapp sechs — wer nach dem einen bindet und nach dem anderen plant, reisst die
Frist um elf Kalendertage. Das war der offene Widerspruch aus L-173, den David
am 07.09. zugunsten der **Werktage** entschieden hat; die Datenblaetter wurden
nachgezogen, die Uebersicht daneben nicht.

**Was dieser Waechter darueber hinaus tut.** Er vergleicht die Zahl im
Datenblatt mit `products.delivery_days` aus der Produktvorlage — der Zahl, die
`services/bauzeit_projekt.bauzeit_werktage` liest und die im Kundenkonto als
zugesagtes Ende erscheint. Eine Zusage im Verkaufsdokument, die das System
anders rechnet, ist genau der Fall, den [[summentext-ist-keine-definition]]
festhaelt.
"""
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL))

import pytest

#: Der Ordner, der laut L-182 bis zu Davids Entscheidung gilt.
BLAETTER = Path(__file__).resolve().parents[3] / "docs" / "Buch" / "Websprint Produkte" / "files"

#: Datenblatt → Slug in der Produktvorlage.
ZUORDNUNG = {
    "KAS_DB_01_Websprint_Relaunch.md": "websprint_relaunch",
    "KAS_DB_02_Websprint_Neubau.md":   "websprint_neubau",
    "KAS_DB_03_Websprint_System.md":   "websprint_system",
    "KAS_DB_08_Websprint_Start.md":    "websprint_start",
}


def _bauzeit_zeile(datei: Path) -> str:
    for zeile in datei.read_text(encoding="utf-8").split("\n"):
        if zeile.startswith("| Bauzeit "):
            return zeile
    return ""


def test_der_ordner_ist_da():
    """Ein Waechter, der seinen Gegenstand nicht findet, ist immer gruen."""
    assert BLAETTER.is_dir(), f"Datenblatt-Ordner fehlt: {BLAETTER}"
    assert len(list(BLAETTER.glob("*.md"))) >= 8


@pytest.mark.parametrize("datei,slug", sorted(ZUORDNUNG.items()))
def test_die_bauzeit_stimmt_mit_dem_katalog(datei, slug):
    from startphase import produkt_vorlage

    zeile = _bauzeit_zeile(BLAETTER / datei)
    assert zeile, f"{datei}: keine Bauzeit-Zeile gefunden"

    treffer = re.search(r"(\d+)\s*\*{0,2}\s*Werktage", zeile)
    assert treffer, (
        f"{datei}: Bauzeit ohne „Werktage“ — {zeile.strip()}. David hat den "
        f"Widerspruch am 07.09.2026 zugunsten der Werktage entschieden (L-173).")

    im_katalog = next(e["delivery_days"] for e in produkt_vorlage() if e["slug"] == slug)
    assert int(treffer.group(1)) == im_katalog, (
        f"{datei} sagt {treffer.group(1)} Werktage, `products.delivery_days` "
        f"sagt {im_katalog}. Das Kundenkonto rechnet mit dem Katalog.")


def test_kein_blatt_im_geltenden_ordner_spricht_von_kalendertagen():
    """Auch die Uebersicht daneben, nicht nur die Datenblaetter.

    Genau hier sass der Fund: Die acht Datenblaetter waren nachgezogen, die
    `KAS_Produktarchitektur` nicht — und sie ist das Dokument, das jemand
    zuerst liest, wenn er wissen will, was die drei Produkte unterscheidet.
    """
    verdaechtig = []
    muster = re.compile(r"(?<!Werk)(?<!werk)\b(\d{1,2})\s*Tage\b")
    for datei in sorted(BLAETTER.glob("*.md")):
        for nr, zeile in enumerate(datei.read_text(encoding="utf-8").split("\n"), 1):
            if not re.search(r"bauzeit|verzug|frist", zeile, re.I):
                continue
            if muster.search(zeile):
                verdaechtig.append(f"{datei.name}:{nr} — {zeile.strip()[:90]}")
    assert not verdaechtig, (
        "Kalendertage statt Werktage bei einer Fristaussage:\n  "
        + "\n  ".join(verdaechtig))
