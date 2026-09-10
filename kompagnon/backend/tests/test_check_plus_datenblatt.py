# -*- coding: utf-8 -*-
"""Check PLUS traegt die Zahlen seines Datenblatts (10.09.2026).

**Der Befund.** Beim Aufnehmen des Teaser-Entwurfs fiel auf, dass der Katalog
`249,00` als **Bruttopreis** fuehrt, waehrend Datenblatt CHK-PLU-01 und der
Entwurf `249 € netto` sagen. Das ist kein Anzeigefehler: `shop.py` baut die
Kassensitzung mit `price_data` aus `price_gross_cents` der Bestellung, und die
kommt aus `products.price_brutto`. Der Katalog ist also der Betrag, der
**abgebucht** wird — bei jedem Verkauf fehlten 39,76 € netto.

**Entscheidung David, 10.09.2026: 249 netto ist richtig.** Damit sind es
296,31 € brutto.

**Zwei weitere Abweichungen derselben Klasse**, im selben Zug berichtigt:
Lieferzeit stand auf 7 statt 5 Werktagen, und das Auswertungsgespraech auf
45 statt 60 Minuten. Alle drei Werte stammen aus derselben Tabelle des
Datenblatts — sie sind beim Anlegen der Katalogzeile nicht daraus gelesen,
sondern geschaetzt worden.

**Warum ein eigener Waechter und nicht nur eine korrigierte Zeile.**
`test_produktkatalog` prueft die **Beziehung** (brutto = netto x Satz) und
haette den Fehler nie gesehen: 209,24 x 1,19 = 249,00 ist rechnerisch
tadellos. Falsch war nicht die Rechnung, sondern die Ausgangszahl. Gegen
diese Klasse hilft nur eine Pruefung gegen die **Quelle** — das Datenblatt.

**Nicht enthalten und ausdruecklich offen:** Position 3 des
Leistungsverzeichnisses, der Wettbewerbsvergleich mit drei Betrieben aus dem
Umkreis. Er steht im Datenblatt und im Teaser-Entwurf, aber es gibt im System
keinen Vergleichswert je Branche — dieselbe Luecke, die der Berichtsseite den
"Schnitt vergleichbarer Betriebe" verwehrt. Er wird deshalb hier **nicht**
zugesichert, solange niemand entschieden hat, wer ihn erhebt.
"""
import pytest

from startphase import produkt_vorlage


#: Aus `docs/produkte/chk-000-und-plus.md`, Teil B, Kopftabelle.
DATENBLATT = {
    "price_netto": 249.00,
    "price_brutto": 296.31,
    "tax_rate": 19,
    "delivery_days": 5,
}


@pytest.fixture
def eintrag():
    treffer = [p for p in produkt_vorlage() if p["slug"] == "check_plus"]
    assert len(treffer) == 1, "check_plus steht nicht genau einmal in der Vorlage"
    return treffer[0]


class TestPreis:
    def test_netto_kommt_aus_dem_datenblatt(self, eintrag):
        assert float(eintrag["price_netto"]) == DATENBLATT["price_netto"]

    def test_brutto_folgt_aus_netto_und_satz(self, eintrag):
        erwartet = DATENBLATT["price_netto"] * (1 + DATENBLATT["tax_rate"] / 100)
        assert float(eintrag["price_brutto"]) == pytest.approx(erwartet, abs=0.01)

    def test_der_alte_wert_steht_nicht_mehr_da(self, eintrag):
        # Die Gegenprobe zur positiven Pruefung oben: 249 als *Brutto* war der
        # Fehler, und 249,00 bleibt als Netto eine gueltige Zahl — ohne diese
        # Zeile faende ein Rueckfall auf den alten Betrag niemand.
        assert float(eintrag["price_brutto"]) != 249.00
        assert float(eintrag["price_netto"]) != 209.24


class TestLieferungUndLeistung:
    def test_lieferzeit_fuenf_werktage(self, eintrag):
        assert int(eintrag["delivery_days"]) == DATENBLATT["delivery_days"]

    def test_auswertungsgespraech_sechzig_minuten(self, eintrag):
        texte = " ".join(eintrag["features"])
        assert "60 Minuten" in texte
        assert "45 Minuten" not in texte

    def test_anrechnung_bleibt_zugesichert(self, eintrag):
        # G5 ist das Verkaufsargument des Produkts — es darf beim Umbau der
        # Leistungsliste nicht stillschweigend herausfallen.
        assert any("Anrechenbar" in f for f in eintrag["features"])

    def test_status_bleibt_entwurf(self, eintrag):
        # Freischalten ist eine Entscheidung, kein Handgriff: Der Shop weist
        # ohne AGB-Fassung ohnehin jede Bestellung ab.
        assert eintrag["status"] == "draft"
