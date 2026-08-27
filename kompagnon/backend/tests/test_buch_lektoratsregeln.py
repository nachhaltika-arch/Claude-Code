# -*- coding: utf-8 -*-
"""
Die Lektoratsregeln des Buchs, maschinell geprüft (B5.2).

Sechs Regeln stehen in `OFFENE-PUNKTE-BUCH.md` unter B5.2. Vier davon sind
zählbar — und genau die brechen beim Kürzen zuerst, weil niemand sie beim
Streichen im Kopf hat. Was Ermessen braucht (wirkt ein Satz werblich?), bleibt
beim Lektorat; hier steht nur, was sich messen lässt.

**Der Fund vom 25.08.2026:** Das Buch nannte ein Prüfwerkzeug beim Namen —
nicht im Manuskript, sondern über den **Katalog**: Ein Rubric-Satz landete
über den Export in Anhang B. Die Regel greift also nicht nur beim Schreiben,
sondern auch dort, wo Text erzeugt wird.
"""
import pathlib
import re

import pytest

WURZEL = pathlib.Path(__file__).resolve().parents[3]
BUCH = (WURZEL / "docs" / "Buch" / "Buch - Kompagnon - Homepage Standard v2"
        / "Vollständige dokumentation Buch V2")

#: Was im Buch nicht namentlich vorkommen darf (B5.2.4). Der Leser soll den
#: Maßstab verstehen, nicht ein Werkzeug kaufen — und ein genanntes Werkzeug
#: veraltet schneller als das Buch.
WERKZEUGE = re.compile(
    r"\b(Lighthouse|PageSpeed|CrUX|Screaming Frog|Sistrix|Ahrefs|SEMrush|GTmetrix)\b",
    re.I)

#: Die drei Dateinamen, die im Fließtext stehen dürfen (B5.2.2). Sie sind
#: Gegenstand von Kriterien und deshalb unvermeidbar.
ERLAUBTE_DATEINAMEN = {"llms.txt", "robots.txt", "sitemap.xml"}
DATEINAME = re.compile(r"\b[a-z][a-z0-9_-]*\.(txt|xml|html|json|css|js|htaccess)\b")


def _kapitel() -> list:
    return sorted(BUCH.glob("KAPITEL-*.md")) + sorted(BUCH.glob("ANHANG-*.md"))


def _ohne_anmerkungen(text: str) -> str:
    """Das Arbeitsmaterial am Ende zählt nicht — es wird nicht gedruckt."""
    schnitt = re.search(r"<!--\s*REDAKTIONELLE ANMERKUNGEN", text, re.I)
    return text[:schnitt.start()] if schnitt else text


@pytest.mark.parametrize("pfad", _kapitel(), ids=lambda p: p.name)
def test_kein_pruefwerkzeug_wird_namentlich_genannt(pfad):
    """B5.2.4 — mit einer Ausnahme, die das Buch selbst festlegt.

    Im Glossar stehen die englischen Begriffe als **Verweise** auf die
    deutschen Einträge. Das ist die Regel, nicht ihr Bruch: Wer „Lighthouse"
    nachschlägt, soll zum Prüfwerkzeug geführt werden.
    """
    if pfad.name.startswith("ANHANG-A"):
        pytest.skip("Das Glossar führt die Begriffe als Verweise — so gewollt")

    text = _ohne_anmerkungen(pfad.read_text(encoding="utf-8"))
    treffer = [z.strip() for z in text.splitlines()
               if WERKZEUGE.search(z) and not z.strip().startswith("<!--")]

    assert not treffer, f"{pfad.name} nennt ein Prüfwerkzeug: {treffer[:2]}"


def test_nur_drei_dateinamen_im_fliesstext():
    """B5.2.2 — jeder weitere Dateiname macht das Buch technischer, als es ist."""
    gefunden = set()
    for pfad in _kapitel():
        text = _ohne_anmerkungen(pfad.read_text(encoding="utf-8"))
        gefunden |= {t.group(0).lower() for t in DATEINAME.finditer(text)}

    ueberzaehlig = gefunden - ERLAUBTE_DATEINAMEN
    assert not ueberzaehlig, f"neue Dateinamen im Fließtext: {sorted(ueberzaehlig)}"


def test_keine_erfundenen_prozentzahlen_zu_ladezeit_und_absprung():
    """B5.2.5 — die verbreitetste unbelegte Zahl der Branche.

    „53 % der Besucher brechen ab, wenn die Seite länger als drei Sekunden
    lädt" steht in tausend Blogbeiträgen und in keiner nachprüfbaren Quelle.
    """
    muster = re.compile(r"\d+\s*(?:%|Prozent)[^.]{0,80}"
                        r"(absprung|abbruch|verlassen|bounce|springen ab)", re.I)
    for pfad in _kapitel():
        text = _ohne_anmerkungen(pfad.read_text(encoding="utf-8"))
        treffer = muster.search(text)
        assert not treffer, f"{pfad.name}: {treffer.group(0)!r}"


def test_die_offenlegung_des_interessenkonflikts_steht_mehrfach():
    """B5.2.6 — sie steht mehrfach, und das ist Absicht.

    Die Regel nennt drei Stellen; gezählt sind es vier (Kapitel 1, 2, 17 und
    die Titelei). Der Test hält die **Untergrenze** fest: Wer beim Kürzen eine
    davon streicht, trifft die Glaubwürdigkeit des ganzen Buchs.
    """
    dateien = [p for p in BUCH.glob("*.md")
               if p.name.startswith(("KAPITEL-", "TITELEI"))
               and "Interessenkonflikt" in p.read_text(encoding="utf-8")]

    assert len(dateien) >= 3, [p.name for p in dateien]


def test_kein_werbesatz_fuer_den_herausgeber():
    """B5.2.3 — besonders Kapitel 17, das vom Selbermachen handelt."""
    muster = re.compile(
        r"(beauftragen Sie uns|wir bauen Ihre|jetzt buchen|unser Angebot für Sie"
        r"|fordern Sie ein Angebot)", re.I)
    for pfad in _kapitel():
        text = _ohne_anmerkungen(pfad.read_text(encoding="utf-8"))
        treffer = muster.search(text)
        assert not treffer, f"{pfad.name}: {treffer.group(0)!r}"
