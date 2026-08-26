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


def test_das_ausgelieferte_widget_zaehlt_mit():
    """**Ein Messfehler, kein Befund (26.08.2026).** `L-105` zaehlt Routen,
    die niemand ruft. Vier `/api/widget/…`-Adressen standen darin — gerufen
    werden sie aber sehr wohl, naemlich von
    `public/embed/audit-widget.html`: dem **ausgelieferten** Widget,
    eigenstaendiges Vanilla JS ohne Build, per iframe auf fremden Seiten
    eingebunden.

    Es lag ausserhalb von `src` und endet nicht auf `.js` — beides Gruende,
    aus denen das Werkzeug es nie gelesen hat. Dieselbe Sorte Fehler wie die
    zwei anderen im Kopf von `tools/adressen.py`: Wer nach **einer** Form
    sucht, misst die Form und nicht die Sache.
    """
    from tools.adressen import gerufene_adressen

    gerufen = gerufene_adressen()
    aus_dem_widget = {a for a, wo in gerufen.items()
                      if any("audit-widget.html" in stelle for stelle in wo)}

    assert "/api/widget/audit" in aus_dem_widget
    assert "/api/widget/config" in aus_dem_widget
    # Mit Platzhalter: Das Widget verkettet mit `+`, nicht mit einer Vorlage —
    # siehe den zweiten Fall unten.
    assert "/api/widget/teaser/{}" in aus_dem_widget
    assert len(aus_dem_widget) >= 4, sorted(aus_dem_widget)


def test_verkettete_adressen_treffen_ihre_route():
    """**Der zweite Messfehler desselben Nachmittags.** Kaum war `public/`
    mitgelesen, meldete der Waechter zwei Adressen als „gibt es im Backend
    nicht": `/api/widget/teaser` und `/api/widget/bestaetigung`.

    Die Routen gibt es sehr wohl — `/teaser/{token}` und
    `/bestaetigung/{token}`. Das Widget baut sie nur anders: In `src` steht
    eine Vorlage (`${token}`), im Widget eine Verkettung
    (`'/api/widget/teaser/' + encodeURIComponent(token)`). Der Ausdruck sah
    nur den Teil bis zum Anfuehrungszeichen und damit eine Adresse, die auf
    einem Schraegstrich endet.

    Ein Waechter mit Fehlalarmen wird abgeschaltet — deshalb steht das hier.
    """
    from tools.adressen import gerufene_adressen

    gerufen = gerufene_adressen()

    assert "/api/widget/teaser/{}" in gerufen
    assert "/api/widget/bestaetigung/{}" in gerufen
    # Und die Form ohne Platzhalter darf **nicht** mehr entstehen, sonst
    # waeren die Fehlalarme zurueck.
    assert "/api/widget/teaser" not in gerufen


class TestAbschnittsweiserVergleich:
    """**Der dritte Messfehler desselben Tages (26.08.2026).**

    L-105 meldete `POST /api/leads/{id}/sequence/start` als „ruft niemand
    auf". Den Knopf gibt es — `LeadProfile.jsx`, „Sequenz starten" — nur baut
    er die **Aktion** in den Pfad:

        `${API_BASE_URL}/api/leads/${leadId}/sequence/${action}`

    Der Schritt, der Vorlagen zu `{}` macht, trifft damit auch `${action}`,
    und `/api/leads/{}/sequence/{}` ist als **Zeichenkette** nicht
    `/api/leads/{}/sequence/start`.

    Der Unterschied ist nicht klein: Mit abschnittsweisem Vergleich fielen
    **59 von 134** gemeldeten Routen weg — die Zahl war um mehr als 40 %
    zu hoch.
    """

    def test_ein_platzhalter_trifft_einen_festen_abschnitt(self):
        from tools.adressen import passt_auf

        assert passt_auf("/api/leads/{}/sequence/{}",
                         "/api/leads/{}/sequence/start")
        assert passt_auf("/api/leads/{}/sequence/{}",
                         "/api/leads/{}/sequence/stop")

    def test_aber_nicht_ueber_abschnittsgrenzen_hinweg(self):
        """Sonst traefe jeder Platzhalter alles, und der Waechter waere
        gruen und wertlos."""
        from tools.adressen import passt_auf

        assert not passt_auf("/api/leads/{}", "/api/leads/{}/zugaenge")
        assert not passt_auf("/api/leads/{}/zugaenge", "/api/leads/{}")

    def test_und_verschiedene_wege_bleiben_verschieden(self):
        """`/api/geo/mein/{}/result` ist der Kundenweg, `/api/geo/{}/result`
        der des Innendienstes. Wer sie gleichsetzt, verliert genau die
        Trennung, die heute gebaut wurde."""
        from tools.adressen import passt_auf

        assert not passt_auf("/api/geo/mein/{}/result", "/api/geo/{}/result")

    def test_gleiches_bleibt_gleich(self):
        from tools.adressen import passt_auf

        assert passt_auf("/api/widget/teaser/{}", "/api/widget/teaser/{}")
        assert passt_auf("/api/health", "/api/health")
