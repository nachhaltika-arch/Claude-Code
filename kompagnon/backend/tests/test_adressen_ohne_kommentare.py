# -*- coding: utf-8 -*-
"""Kommentare sind keine Aufrufe.

**Der Fund (26.08.2026).** `test_frontend_adressen.py` meldete
`/api/briefings` als Adresse, die das Frontend ruft und das Backend nicht
kennt. Gerufen wurde sie nie — sie stand in einem **JSDoc-Kommentar**, in
Backticks, und die Marke des Werkzeugs sucht genau zwischen
Anführungszeichen und Backticks.

**Warum das kein Einzelfall ist.** Dieser Bestand erklärt sich ausführlich
und nennt dabei ständig Adressen. Jede in Backticks gesetzte Route in einem
Kommentar wäre ein Fehlalarm — und ein Wächter mit Fehlalarmen wird
abgeschaltet. Genau das steht schon zweimal im Kopf von `tools/adressen.py`,
zu zwei anderen Anlässen.

Es ist dieselbe Familie wie die Fehlmessungen in [[messfehler-eigene-zahlen]]:
Zeichenketten, Kommentare und die eigene Reparatur werden mitgezählt.
"""
import pytest

from tools.adressen import ohne_kommentare


class TestWasVerschwindet:
    def test_eine_zeilenweise_bemerkung(self):
        assert "/api/geheim" not in ohne_kommentare(
            "// erklaert `/api/geheim`\nconst a = 1;")

    def test_ein_blockkommentar(self):
        assert "/api/geheim" not in ohne_kommentare(
            "/* Der Weg `/api/geheim` ist gemeint */\nconst a = 1;")

    def test_ein_jsdoc_ueber_mehrere_zeilen(self):
        """Die Form, die den Fehlalarm ausgeloest hat."""
        text = ("/**\n"
                " * Der Innendienst spricht `/api/briefings/{id}`, der Kunde\n"
                " * `/api/briefings/mein/{id}`.\n"
                " */\n"
                "const a = 1;")

        assert "/api/briefings" not in ohne_kommentare(text)


class TestWasBleibt:
    @pytest.mark.parametrize("quelle,erwartet", [
        ("const a = `/api/echt/${id}`;", "/api/echt"),
        ("const b = '/api/zweitens';", "/api/zweitens"),
        ('const c = "/api/drittens";', "/api/drittens"),
    ])
    def test_echte_aufrufe_in_allen_drei_anfuehrungszeichen(self, quelle, erwartet):
        assert erwartet in ohne_kommentare(quelle)

    def test_ein_doppelter_schraegstrich_in_einer_zeichenkette(self):
        """`'http://…'` beginnt keinen Kommentar.

        Ein Ausdruck ueber Kommentare stolpert genau hier — deshalb zaehlt
        das Werkzeug zeichenweise mit, in welchem Anfuehrungszeichen es
        gerade steht.
        """
        quelle = "const d = 'http://beispiel.de/api/pfad';"

        assert "http://beispiel.de/api/pfad" in ohne_kommentare(quelle)

    def test_ein_maskiertes_anfuehrungszeichen_beendet_nichts(self):
        quelle = r"""const e = 'er sagte \'hallo\' und /api/danach';"""

        assert "/api/danach" in ohne_kommentare(quelle)


def test_die_zeilennummern_verrutschen_nicht():
    """Der Waechter nennt Datei **und Zeile**. Faellt ein Blockkommentar
    ersatzlos weg, zeigt jede Meldung danach auf die falsche Stelle — und
    eine falsche Stelle ist schlimmer als keine."""
    quelle = "const a = 1;\n/* eine\n   zwei\n   drei */\nconst b = '/api/ziel';"

    sauber = ohne_kommentare(quelle)

    assert quelle.count("\n") == sauber.count("\n")
    zeile = sauber.split("\n").index(next(z for z in sauber.split("\n")
                                          if "/api/ziel" in z)) + 1
    assert zeile == 5


def test_der_waechter_findet_die_echten_adressen_weiterhin():
    """Eine Reparatur, die den Waechter blind macht, ist keine.

    Die Zahl ist die vom Tag des Umbaus; sie darf wachsen, aber nicht
    einbrechen.
    """
    from tools.adressen import gerufene_adressen

    assert len(gerufene_adressen()) >= 150
