# -*- coding: utf-8 -*-
"""Der Angebotskasten der Berichtsseite (Entwurf „Bericht Conversion v2",
Vorgabe David, 10.09.2026).

**Was hier geprüft wird, ist nicht die Gestaltung, sondern was behauptet
wird.** Der Kasten trägt vier Aussagen, die ein Kunde als Zusage liest:
einen Nachlass, eine Abnahmegarantie, einen Hinweis auf freie Plätze und
einen Satz darüber, warum ausgerechnet dieses Paket zu seiner Seite passt.
Jede davon ist entweder gedeckt oder sie darf nicht dastehen.

**Warum es diese Datei überhaupt gibt.** Am 10.09.2026 wurden die vier
Eckdaten des Angebots ausgetauscht — aus „Bauzeit · Festpreis · Zahlbetrag ·
Zahlung" wurde „Bauzeit · Seitenumfang · Korrekturschleife". Die vorhandenen
Wächter blieben dabei **grün**: Sie prüften, dass es einen Eckdaten-Kasten
gibt, nicht was darin steht. Ein Wächter, der einen Austausch des Inhalts
nicht bemerkt, bewacht das Gehäuse.
"""
import io
import json
import os
import re

import pytest

from services import bericht_daten


BLATT = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     "docs", "produkte", "ws-rel-01.md")
VORLAGE = os.path.join(os.path.dirname(__file__), "..", "vorlagen", "bericht.html")


#: Der Katalogeintrag, so wie ihn `startphase.py` anlegt — gekürzt auf die
#: Spalten, die der Angebotskasten liest.
RELAUNCH = {
    "slug": "websprint_relaunch", "name": "Websprint Relaunch",
    "price_netto": 3500.00, "price_brutto": 4165.00, "delivery_days": 14,
    "features": ["Eingangsaudit nach Homepage-Standard, 100 Punkte in 8 Kategorien"],
}


class _Db:
    """Ein Katalog, der antwortet. ``leer=True`` liefert kein Produkt.

    Beide Fälle werden gebraucht: mit Produkt, um die Eckdaten zu prüfen —
    ohne, um zu sehen, dass nichts erfunden wird.
    """

    def __init__(self, leer=False):
        self.leer = leer

    def execute(self, sql, params=None):
        treffer = None
        if not self.leer and (params or {}).get("s") == "websprint_relaunch":
            treffer = RELAUNCH

        class E:
            def mappings(self_):
                class M:
                    def first(self__): return treffer
                return M()
        return E()

    def rollback(self):
        pass


class _Audit:
    company_name = "Muster GmbH"
    website_url = "https://muster.de"
    total_score = 61
    item_scores = {}
    item_sources = {}
    item_belege = {}
    coverage = 0
    blockers = "[]"
    erkannte_branche = ""
    branchenklasse = ""
    level = "Homepage Standard Bronze"


def _daten(punkte=61, leer=False, **einstellungen):
    audit = _Audit()
    audit.total_score = punkte
    return bericht_daten.aufbauen(_Db(leer), audit, einstellungen=einstellungen)


def _vorlage():
    return io.open(VORLAGE, encoding="utf-8").read()


# ══════════════════════════════════════════════════════════════════════
# Die drei Eckdaten
# ══════════════════════════════════════════════════════════════════════

class TestEckdaten:
    def test_es_sind_bauzeit_seitenumfang_und_korrekturschleife(self):
        labels = [e["label"] for e in _daten()["eckdaten"]]
        assert labels == ["Bauzeit", "Seitenumfang", "Korrekturschleife"]

    def test_kein_preis_steht_zweimal_im_kasten(self):
        """Der Festpreis hat direkt unter den Eckdaten seinen eigenen Platz.

        Bis zum 10.09.2026 stand er zusätzlich als Eckdatum, und der
        Bruttobetrag daneben. Drei Zahlen für einen Preis liest sich wie
        drei Preise.
        """
        werte = " ".join(e["wert"] for e in _daten()["eckdaten"])
        assert "€" not in werte
        assert "netto" not in werte and "brutto" not in werte

    def test_die_bauzeit_kommt_aus_dem_katalog(self):
        wert = [e["wert"] for e in _daten()["eckdaten"] if e["label"] == "Bauzeit"]
        assert wert == ["14 Werktage"]

    def test_ohne_katalogeintrag_wird_keine_bauzeit_erfunden(self):
        """Fehlt das Produkt, fehlt die Zahl — statt einer Null oder einer
        festen 14 aus dem Quelltext."""
        labels = [e["label"] for e in _daten(leer=True)["eckdaten"]]
        assert labels == ["Seitenumfang", "Korrekturschleife"]

    def test_die_beiden_grenzen_stehen_so_im_leistungsverzeichnis(self):
        """Drift-Wächter: `bis 6 Seiten` und die eine Korrekturschleife.

        Beide stehen als Konstante im Code, weil es dafür keine Spalte im
        Katalog gibt. Ändert jemand das Leistungsverzeichnis, ohne den Code
        anzufassen, verspricht die Berichtsseite etwas anderes als der
        Vertrag. Dieser Test bemerkt das.
        """
        blatt = io.open(BLATT, encoding="utf-8").read()
        assert bericht_daten.SEITENUMFANG == "bis 6 Seiten"
        assert "bis 6 Seiten" in blatt
        assert "Enthalten ist eine Korrekturschleife" in blatt

    def test_der_preis_der_weiteren_schleife_steht_so_im_blatt(self):
        """Die 290 € im Kleingedruckten sind eine Preiszusage."""
        blatt = io.open(BLATT, encoding="utf-8").read()
        assert "290 € netto" in _vorlage()
        assert "290 € netto" in blatt


# ══════════════════════════════════════════════════════════════════════
# Die Zahlungsbedingungen
# ══════════════════════════════════════════════════════════════════════

class TestZahlungsbedingungen:
    def test_sie_haengen_nicht_am_rabatt(self):
        """Der eigentliche Fund vom 10.09.2026.

        „Zahlbar bei Auftragserteilung, keine Ratenzahlung, Fristbeginn erst
        bei Vorliegen der Unterlagen" stand im Entwurf **innerhalb** des
        Rabatt-Schalters. Ohne Rabatt — also im heutigen Zustand — wären die
        Zahlungsbedingungen von der Seite verschwunden, und der Kunde hätte
        vor dem Kauf nicht gelesen, wann er zahlt.
        """
        vorlage = _vorlage()
        satz = "Zahlbar vollständig bei Auftragserteilung"
        stelle = vorlage.index(satz)
        # Zwischen dem Satz und der letzten davor geöffneten `sc-if` darf
        # kein offener Rabatt-Schalter mehr stehen.
        davor = vorlage[:stelle]
        assert davor.count("<sc-if") == davor.count("</sc-if>"), (
            "Die Zahlungsbedingungen stehen in einem Schalter — sie "
            "verschwinden, sobald er aus ist.")

    def test_der_bruttobetrag_steht_im_kleingedruckten(self):
        assert "{{ zahlbetrag }}" in _vorlage()

    def test_der_bruttobetrag_kommt_aus_dem_katalog(self):
        assert _daten()["zahlbetrag"] == "4.165,00 € brutto"

    def test_ohne_produkt_bleibt_der_bruttobetrag_leer(self):
        """Kein Produkt im Katalog heisst kein Betrag — nicht 0,00 €."""
        assert _daten(leer=True)["zahlbetrag"] == ""


# ══════════════════════════════════════════════════════════════════════
# Der Rabatt
# ══════════════════════════════════════════════════════════════════════

class TestRabatt:
    def test_satz_und_code_erscheinen_nur_gemeinsam(self):
        nur_satz = _daten(bericht_rabattsatz="25 % für die ersten 25")
        nur_code = _daten(bericht_rabattcode="WS25")
        assert nur_satz["rabattsatz"] == ""
        assert nur_code["rabattsatz"] == ""
        assert nur_code["rabattcode"] == ""

    def test_beides_gesetzt_zeigt_den_kasten(self):
        d = _daten(bericht_rabattsatz="25 % für die ersten 25 Kunden",
                   bericht_rabattcode="WS25")
        assert d["rabattsatz"] == "25 % für die ersten 25 Kunden"
        assert d["rabattcode"] == "WS25"

    def test_der_code_steht_nicht_fest_in_der_vorlage(self):
        """Sonst liest der Kunde einen Code, den die Kasse nicht kennt."""
        vorlage = _vorlage()
        assert "WS25" not in vorlage
        assert vorlage.count("{{ rabattcode }}") >= 2

    def test_der_rabattpreis_wird_aus_dem_festpreis_gerechnet(self):
        """Zwei Preise von Hand zu pflegen ist die Bauart hinter L-29.

        25 % auf 3.500 € netto sind 2.625 € — dieselbe Zahl, die der
        Entwurf von Hand eingetragen hatte.
        """
        d = _daten(bericht_rabattsatz="25 % Rabatt", bericht_rabattcode="WS25")
        assert "2.625,00" in d["preisRabatt"]

    def test_ohne_rabatt_gibt_es_keinen_zweiten_preis(self):
        assert _daten()["preisRabatt"] == ""


# ══════════════════════════════════════════════════════════════════════
# Die Angebotsbegründung
# ══════════════════════════════════════════════════════════════════════

class TestAngebotsbegruendung:
    def test_sie_nennt_die_gemessene_punktzahl(self):
        text = _daten(punkte=61)["angebotsbegruendung"]
        assert "61" in text and "39" in text

    def test_sie_behauptet_nichts_ueber_das_alter_der_seite(self):
        """Der Entwurf schlug „Ihre Seite ist älter als vier Jahre" vor.

        Das Alter wird nirgends erhoben. Für einen Betrieb mit einer drei
        Monate alten Seite stünde dort schlicht etwas Falsches.
        """
        text = _daten(punkte=61)["angebotsbegruendung"]
        assert "vier Jahre" not in text
        assert "rechtlich offen" not in text

    def test_ab_der_zusagegrenze_bleibt_sie_leer(self):
        """Wer 88 Punkte hat, braucht keinen Relaunch."""
        assert _daten(punkte=bericht_daten.GARANTIEPUNKTE)["angebotsbegruendung"] == ""
        assert _daten(punkte=97)["angebotsbegruendung"] == ""

    def test_ohne_messung_bleibt_sie_leer(self):
        assert _daten(punkte=0)["angebotsbegruendung"] == ""

    def test_eine_eigene_vorgabe_schlaegt_die_ableitung(self):
        eigen = "Ihre Seite trägt, die Technik dahinter nicht mehr."
        assert _daten(punkte=61,
                      bericht_angebotsbegruendung=eigen)["angebotsbegruendung"] == eigen


# ══════════════════════════════════════════════════════════════════════
# Abnahmezusage und Knappheit
# ══════════════════════════════════════════════════════════════════════

class TestZusagen:
    def test_beide_sind_aus_solange_niemand_sie_setzt(self):
        d = _daten()
        assert d["abnahmepunkte"] == ""
        assert d["knappheit"] == ""

    def test_gesetzt_stehen_sie_da(self):
        d = _daten(bericht_abnahmepunkte="85",
                   bericht_knappheit="Zwei Sprint-Plätze im Oktober frei")
        assert d["abnahmepunkte"] == "85"
        assert d["knappheit"] == "Zwei Sprint-Plätze im Oktober frei"

    def test_die_zusage_nennt_die_punktzahl_aus_der_einstellung(self):
        """Nicht die 96 aus dem Entwurf und nicht die 85 aus dem Standard —
        was eingetragen ist."""
        vorlage = _vorlage()
        assert "{{ abnahmepunkte }}" in vorlage
        assert not re.search(r"mindestens\s+96\s+Punkte", vorlage)


# ══════════════════════════════════════════════════════════════════════
# Der Rechtsbefund
# ══════════════════════════════════════════════════════════════════════

class TestRechtsbefund:
    """Gefunden am 10.09.2026 in der Trichter-Vorschau, nicht produktiv.

    Die Seite zeigte im roten Kasten `kein_impressum. keine_datenschutz-
    erklaerung.` — die Kennungen aus der Datenbank, nicht die Sätze dazu.
    """

    def _mit(self, blocker):
        audit = _Audit()
        audit.blockers = json.dumps(blocker)
        return bericht_daten.aufbauen(_Db(), audit, einstellungen={})["rechtsbefund"]

    def test_kennungen_werden_uebersetzt(self):
        from services.audit_criteria import BLOCKER_LABELS

        text = self._mit(["kein_impressum", "keine_datenschutzerklaerung"])
        assert BLOCKER_LABELS["kein_impressum"] in text
        assert "kein_impressum." not in text

    def test_keine_kennung_erreicht_den_kunden(self):
        """Positiv-Gegenstueck: nicht nur „der Rohtext fehlt", sondern
        „nichts sieht aus wie eine Kennung"."""
        text = self._mit(list(_alle_blocker()))
        assert "_" not in text

    def test_eine_unbekannte_kennung_wird_weggelassen(self):
        """Ein neuer Blocker ohne Text ist ein Fehler im Katalog — der Kunde
        soll ihn nicht buchstabieren muessen."""
        assert self._mit(["voellig_neuer_blocker"]) == ""

    def test_ohne_blocker_bleibt_der_kasten_weg(self):
        assert self._mit([]) == ""

    def test_die_einwilligungsfaelle_nennen_ihre_fundstelle(self):
        """Ergänzt am 10.09.2026 auf Wunsch David.

        Auf einer Seite, die einem Betrieb sagt, was rechtlich offen ist,
        ist die Fundstelle die Hälfte der Aussage. „Cookies werden vor der
        Einwilligung gesetzt" ist ein Vorwurf; mit § 25 TDDDG dahinter ist
        es einer, den er nachlesen kann.
        """
        from services.audit_criteria import BLOCKER_LABELS

        for kennung in ("tracking_ohne_consent", "cookies_ohne_consent"):
            assert "§ 25 TDDDG" in BLOCKER_LABELS[kennung], kennung

        # Und im Erzeugnis, nicht nur in der Tabelle.
        text = self._mit(["cookies_ohne_consent"])
        assert "§ 25 TDDDG" in text

    def test_tls_bekommt_keinen_paragrafen_untergeschoben(self):
        """Art. 32 DSGVO gilt nur, wenn die Seite personenbezogene Daten
        überträgt. Ein Betrieb mit reiner Visitenkarte ohne Formular
        verstößt gegen nichts — ihm eine Norm vorzuhalten, die auf ihn
        nicht anwendbar ist, wäre dieselbe unbelegte Zusatzbehauptung, die
        aus dem Angebotskasten geflogen ist.
        """
        from services.audit_criteria import BLOCKER_LABELS

        assert "DSGVO" not in BLOCKER_LABELS["kein_gueltiges_tls"]
        assert "§" not in BLOCKER_LABELS["kein_gueltiges_tls"]

    def test_jede_kennung_des_katalogs_hat_einen_text(self):
        """Drift-Waechter: Wer einen Blocker einfuehrt und den Text vergisst,
        laesst ihn auf der Berichtsseite verschwinden — still."""
        from services.audit_criteria import BLOCKER_LABELS

        fehlend = [k for k in _alle_blocker() if k not in BLOCKER_LABELS]
        assert not fehlend, f"ohne lesbaren Text: {fehlend}"


def _alle_blocker():
    """Alle Kennungen, die die Bewertung vergeben kann.

    Aus den beiden Mengen des Katalogs, **nicht** aus `BLOCKER_LABELS`: Wer
    die Liste der Kennungen aus der Liste der Texte ableitet, kann nicht
    mehr feststellen, dass ein Text fehlt.
    """
    from services.audit_criteria import BLOCKING_CRITICAL, BLOCKING_MAJOR

    return sorted(BLOCKING_CRITICAL | BLOCKING_MAJOR)
