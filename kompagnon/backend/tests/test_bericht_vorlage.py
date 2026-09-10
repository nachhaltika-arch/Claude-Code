# -*- coding: utf-8 -*-
"""Die Vorlagensprache der Berichtsseite (L-191, 10.09.2026).

Der Entwurf kommt aus einem Gestaltungswerkzeug und bringt seine eigene,
sehr kleine Sprache mit: `{{ feld }}`, `<sc-for list="{{ liste }}" as="x">`
und `<sc-if value="{{ flag }}">`. Elf Schleifen, fuenf Bedingungen, 63
Platzhalter.

**Warum nachbauen und nicht ersetzen.** Der Entwurf wird sich aendern — er
ist Davids Gestaltung, nicht meine. Wer ihn beim Einbauen in
Zeichenkettenverkettung uebersetzt, macht jede spaetere Aenderung zu einer
Programmieraufgabe. So bleibt die Datei das, was sie ist: eine Vorlage, die
man austauschen kann.

**Escaping ist die Vorgabe, nicht die Ausnahme.** Auf dieser Seite stehen
Firmenname und Website-Adresse des Kunden — beides Eingaben aus dem
Widget. Ein Feld, das roh eingesetzt wird, muss das ausdruecklich sagen.
"""
import pytest

from services import bericht_vorlage as bv


class TestFelder:
    def test_einfaches_feld(self):
        assert bv.rendern("Hallo {{ name }}", {"name": "Welt"}) == "Hallo Welt"

    def test_verschachteltes_feld(self):
        assert bv.rendern("{{ a.b }}", {"a": {"b": "tief"}}) == "tief"

    def test_fehlendes_feld_wird_leer(self):
        # Kein `{{ name }}` im Ergebnis: Ein sichtbarer Platzhalter waere
        # schlimmer als eine Luecke — er stuende im Bericht beim Kunden.
        assert bv.rendern("[{{ fehlt }}]", {}) == "[]"

    def test_zeichen_werden_geschuetzt(self):
        roh = {"name": '<script>alert("x")</script>'}
        ergebnis = bv.rendern("{{ name }}", roh)
        assert "<script>" not in ergebnis
        assert "&lt;script&gt;" in ergebnis

    def test_zahlen_und_none(self):
        assert bv.rendern("{{ a }}/{{ b }}", {"a": 82, "b": None}) == "82/"


class TestSchleife:
    def test_einfache_schleife(self):
        vorlage = '<sc-for list="{{ xs }}" as="x">[{{ x.n }}]</sc-for>'
        assert bv.rendern(vorlage, {"xs": [{"n": 1}, {"n": 2}]}) == "[1][2]"

    def test_leere_liste_ergibt_nichts(self):
        vorlage = 'A<sc-for list="{{ xs }}" as="x">B</sc-for>C'
        assert bv.rendern(vorlage, {"xs": []}) == "AC"

    def test_fehlende_liste_ergibt_nichts(self):
        vorlage = 'A<sc-for list="{{ fehlt }}" as="x">B</sc-for>C'
        assert bv.rendern(vorlage, {}) == "AC"

    def test_verschachtelte_schleifen(self):
        """Der eigentliche Fall: `kat.kriterien` steckt in `kategorien`."""
        vorlage = ('<sc-for list="{{ ks }}" as="k">{{ k.name }}:'
                   '<sc-for list="{{ k.teile }}" as="t">{{ t }}</sc-for>;</sc-for>')
        daten = {"ks": [{"name": "A", "teile": ["1", "2"]},
                        {"name": "B", "teile": ["3"]}]}
        assert bv.rendern(vorlage, daten) == "A:12;B:3;"

    def test_hinweisattribute_stoeren_nicht(self):
        # Der Entwurf traegt `hint-placeholder-count` — reine Vorschau-Angaben.
        vorlage = '<sc-for list="{{ xs }}" as="x" hint-placeholder-count="8">{{ x }}</sc-for>'
        assert bv.rendern(vorlage, {"xs": ["a", "b"]}) == "ab"


class TestBedingung:
    def test_wahr_zeigt_den_inhalt(self):
        assert bv.rendern('<sc-if value="{{ f }}">JA</sc-if>', {"f": True}) == "JA"

    def test_falsch_laesst_ihn_weg(self):
        assert bv.rendern('<sc-if value="{{ f }}">JA</sc-if>', {"f": False}) == ""

    def test_fehlender_wert_gilt_als_falsch(self):
        # **Wichtig fuer den Branchenschnitt (L-190):** Es gibt ihn nicht,
        # und ohne Wert darf er nicht gezeichnet werden.
        assert bv.rendern('<sc-if value="{{ f }}">JA</sc-if>', {}) == ""

    def test_bedingung_in_einer_schleife(self):
        vorlage = ('<sc-for list="{{ xs }}" as="x">'
                   '<sc-if value="{{ x.ok }}">{{ x.n }}</sc-if></sc-for>')
        daten = {"xs": [{"n": "a", "ok": True}, {"n": "b", "ok": False}]}
        assert bv.rendern(vorlage, daten) == "a"


class TestRohElemente:
    def test_tabellenelemente_werden_zurueckbenannt(self):
        """Der Export schreibt `sc-raw-td`, damit sein Editor sie nicht anfasst."""
        vorlage = '<sc-raw-table><sc-raw-tr><sc-raw-td>x</sc-raw-td></sc-raw-tr></sc-raw-table>'
        ergebnis = bv.rendern(vorlage, {})
        assert "<table>" in ergebnis and "<td>" in ergebnis
        assert "sc-raw" not in ergebnis

    def test_attribute_bleiben_erhalten(self):
        vorlage = '<sc-raw-td style="padding:4px">x</sc-raw-td>'
        assert bv.rendern(vorlage, {}) == '<td style="padding:4px">x</td>'


def test_keine_sc_reste_im_ergebnis():
    """Die Gegenprobe ueber alles: Was der Erzeuger nicht kennt, faellt auf."""
    vorlage = ('<sc-if value="{{ a }}"><sc-for list="{{ xs }}" as="x">'
               '<sc-raw-td>{{ x }}</sc-raw-td></sc-for></sc-if>')
    ergebnis = bv.rendern(vorlage, {"a": True, "xs": ["1"]})
    assert "sc-" not in ergebnis
    assert "{{" not in ergebnis
