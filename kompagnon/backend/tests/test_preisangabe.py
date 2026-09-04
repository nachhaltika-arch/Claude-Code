# -*- coding: utf-8 -*-
'''Die Pflicht-Preisangabe bei gekoppeltem Abo (L-164, WS-STA-01 § 4.1).

**Warum das ein Test ist und keine Formsache.** Das Datenblatt schreibt vor:
„Der Preis darf niemals als '1.500 €' allein beworben werden." Eine Bewerbung
mit dem Einmalpreis, bei der die Abo-Pflicht erst im Kleingedruckten steht,
ist das Vorenthalten einer wesentlichen Information — angreifbar durch
Mitbewerber und Wettbewerbsvereine. Ein Fehler hier kostet Geld, kein Ansehen.
'''
from pathlib import Path

from services import abo_stunden
from services.preisangabe import (
    abo_preis_netto_cent,
    gesamtpreis_erstes_jahr_netto_cent,
    preisangabe,
)

WURZEL = Path(__file__).resolve().parent.parent


def test_der_gesamtpreis_ist_der_aus_dem_datenblatt():
    """1.500 + 12 x 79 = 2.448 EUR netto — die Zahl, die im Angebot steht."""
    assert gesamtpreis_erstes_jahr_netto_cent(150000, "ABO-BAS", 12) == 244800


def test_der_satz_nennt_alle_vier_pflichtangaben():
    """Einmalpreis, Monatsentgelt, Mindestlaufzeit **und** Gesamtpreis.

    Fehlt eine davon, ist die Angabe unvollstaendig — und unvollstaendig ist
    hier dasselbe wie falsch.
    """
    satz = preisangabe(150000, "ABO-BAS", 12)

    assert "1.500,00 €" in satz
    assert "79,00 €" in satz
    assert "12 Monate" in satz
    assert "2.448,00 €" in satz


def test_ohne_gekoppeltes_abo_bleibt_die_angabe_leer():
    """Ein Paket ohne Abo-Pflicht bekommt keinen Zusatz.

    Ein Satz, der ueberall steht, wird nirgends gelesen.
    """
    assert preisangabe(350000, None, 0) == ""
    assert preisangabe(350000, "", 12) == ""
    assert preisangabe(150000, "ABO-BAS", 0) == ""


def test_eine_unbekannte_abo_kennung_kippt_den_katalog_nicht():
    """Ein Tippfehler in einer Produktzeile darf den Shop nicht leeren.

    Die Kopplung wird dann nicht angezeigt — das faellt beim ersten Blick auf
    die Seite auf. Ein leerer Shop faellt spaeter auf und sieht nach einem
    Ausfall aus.
    """
    assert abo_preis_netto_cent("ABO-XXX") == 0
    assert preisangabe(150000, "ABO-XXX", 12) == ""


def test_der_abo_preis_kommt_aus_abo_stunden_und_nicht_von_hier():
    """**Der eigentliche Waechter.**

    Der Preis des Pflege-Abos ist die Grundlage jeder Abrechnung und liegt in
    `services/abo_stunden.py`. Schriebe jemand die 7900 hier hinein, liefen
    Rechnung und Werbung auseinander — und die Pflichtangabe waere in dem
    Moment falsch, in dem einer der beiden Werte sich aendert.
    """
    import ast

    # **Am Baum gemessen, nicht am Text.** Der erste Anlauf suchte mit einem
    # Muster nach Ziffernfolgen und schlug an — an der Rechnung „1.500 + 12 x
    # 79 = 2.448" im eigenen Erklaertext und an der Nummer L-164. Ein Test,
    # der Kommentare mitzaehlt, misst das Falsche; hier zaehlen nur Zahlen,
    # die der Code wirklich benutzt.
    quelltext = (WURZEL / "services" / "preisangabe.py").read_text(encoding="utf-8")
    literale = {k.value for k in ast.walk(ast.parse(quelltext))
                if isinstance(k, ast.Constant) and isinstance(k.value, (int, float))
                and not isinstance(k.value, bool)}

    verboten = literale & {abo_stunden.PREIS_ABO_BAS_NETTO_CENT,
                           abo_stunden.PREIS_ABO_PRO_NETTO_CENT}
    assert not verboten, (
        f"Abo-Preis fest verdrahtet in preisangabe.py: {sorted(verboten)} — "
        f"er gehoert ausschliesslich in services/abo_stunden.py")

    # Und die Kopplung wirkt wirklich: Aendert sich die Quelle, aendert sich
    # das Ergebnis. Gemessen, nicht behauptet.
    vorher = abo_preis_netto_cent("ABO-BAS")
    assert vorher == abo_stunden.PREIS_ABO_BAS_NETTO_CENT


def test_die_produktzeile_traegt_die_kopplung():
    """WS-STA-01 muss im Katalog als abo-gekoppelt stehen.

    Ohne `gekoppeltes_abo` bliebe die Pflichtangabe leer, und der Shop zeigte
    1.785 EUR ohne ein Wort ueber zwoelf Monate Pflege — genau der Fall, den
    § 4.1 verbietet.
    """
    import ast

    baum = ast.parse((WURZEL / "startphase.py").read_text(encoding="utf-8"))
    seed = next(ast.literal_eval(k.value) for k in ast.walk(baum)
                if isinstance(k, ast.Assign)
                and any(getattr(z, "id", "") == "SEED" for z in k.targets))
    start = next(e for e in seed if e["slug"] == "websprint_start")

    assert start["gekoppeltes_abo"] == "ABO-BAS"
    assert start["abo_mindestlaufzeit"] == 12
    # Der Satz, der daraus entsteht, ist der aus dem Datenblatt.
    satz = preisangabe(int(round(start["price_netto"] * 100)),
                       start["gekoppeltes_abo"], start["abo_mindestlaufzeit"])
    assert "2.448,00 €" in satz


def test_shop_und_kasse_zeigen_die_angabe():
    """Gerechnet und nicht gezeigt waere dasselbe wie nicht gerechnet.

    Fuenfmal ist in diesem Projekt etwas gebaut worden, das keine Oberflaeche
    erreicht hat. Dieser Test sieht an beiden Stellen nach, an denen ein
    Preis oeffentlich steht.
    """
    fe = WURZEL.parent / "frontend" / "src" / "pages"
    for datei in ("Shop.jsx", "Checkout.jsx"):
        text = (fe / datei).read_text(encoding="utf-8")
        assert "preisangabe" in text, f"{datei} zeigt die Pflichtangabe nicht"
