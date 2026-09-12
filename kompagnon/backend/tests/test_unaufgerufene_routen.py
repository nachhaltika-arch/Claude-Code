# -*- coding: utf-8 -*-
"""Das Werkzeug, das L-105 zaehlt, zaehlte drei Knoepfe nicht mit.

**Der Fund (26.08.2026, beim Abarbeiten von L-105 selbst).**
`tools/unaufgerufene-routen.py` meldete `POST /api/leads/{id}/sequence/start`,
`/pause` und `/stop` als „ruft niemand auf". Den Knopf gibt es seit langem —
`LeadProfile.jsx` baut nur die **Aktion** in den Pfad:

    `${API_BASE_URL}/api/leads/${leadId}/sequence/${action}`

Nach dem Normalisieren steht dort `/api/leads/{}/sequence/{}`, und das ist
als **Zeichenkette** nicht `/api/leads/{}/sequence/start`.

**Das Aergerliche daran:** Genau dieser Fehler war am selben Tag schon
gefunden und in `tools/adressen.passt_auf` behoben worden — fuer das
Nachbarwerkzeug `test_frontend_adressen.py`. Der Kopf von
`unaufgerufene-routen.py` behauptet, beide laesen dieselbe Grundlage, „damit
sie nicht auseinanderdriften". Sie waren auseinandergedriftet: Das eine
vergleicht abschnittsweise, das andere mit `in`. **Eine Begruendung im
Kopftext ist keine Verbindung.**

**Warum der Platzhaltervergleich hier nicht einfach ersetzt wird.**
`passt_auf` laesst `{}` auf beiden Seiten gelten. Ein Aufruf
`/api/projects/${id}/${was}` traefe damit **jede** Projektroute mit zwei
Abschnitten — und ein Werkzeug, das zu wenig meldet, ist schlimmer als eines,
das zu viel meldet: Es sagt „alles angeschlossen", wo niemand nachgesehen
hat. Solche Treffer stehen deshalb in einer **eigenen** Gruppe, mit der
rufenden Adresse daneben, und muessen von Hand beurteilt werden.
"""
import pathlib
import subprocess
import sys

import pytest

WERKZEUG = (pathlib.Path(__file__).resolve().parent.parent
            / "tools" / "unaufgerufene-routen.py")


@pytest.fixture(scope="module")
def ausgabe():
    if not WERKZEUG.exists():
        pytest.skip(f"Werkzeug nicht gefunden: {WERKZEUG}")
    lauf = subprocess.run([sys.executable, str(WERKZEUG)],
                          capture_output=True, text=True,
                          cwd=str(WERKZEUG.parent.parent))
    assert lauf.returncode in (0, 1), lauf.stderr[-2000:]
    return lauf.stdout


class TestDerAbschnittsweiseVergleich:
    @pytest.mark.parametrize("aktion", ["start", "pause", "stop"])
    def test_die_mailstrecke_gilt_als_gerufen(self, ausgabe, aktion):
        """Der Knopf sitzt in `LeadProfile.jsx` und baut die Aktion in den
        Pfad. Ihn zu uebersehen heisst, drei Routen zur Pruefung zu stellen,
        die laengst angeschlossen sind — und die echten Funde gehen darin
        unter."""
        # Bis zur naechsten Ueberschrift, nicht bis zur uebernaechsten: Die
        # Variablentreffer stehen **vor** „Nicht ueber HTTP", und mit dem
        # groesseren Ausschnitt haette dieser Test sie mitgelesen und waere
        # rot geblieben, obwohl das Werkzeug richtig zaehlt. Der Suchbereich
        # folgte der Erwartung statt dem Vorkommen — schon wieder.
        offen = ausgabe.split("Nur ueber eine Variable")[0]

        assert f"/api/leads/{{lead_id}}/sequence/{aktion}" not in offen

    def test_sie_stehen_stattdessen_unter_den_variablentreffern(self, ausgabe):
        """Nicht stillschweigend abziehen: Wer ueber eine Variable trifft,
        koennte auch zu viel treffen. Die Gruppe macht das sichtbar."""
        assert "Variable im Pfad" in ausgabe
        assert "/sequence/start" in ausgabe


class TestDasWerkzeugMisstNochWas:
    def test_es_misst_weiterhin_routen_ohne_aufrufer(self, ausgabe):
        """Gegenprobe zur Lockerung: Griffe `passt_auf` zu grosszuegig, faende
        das Werkzeug gar nichts mehr — und waere gruen, ohne etwas zu pruefen.

        **Gezaehlt wird jetzt die Summe, nicht der Restkorb** (12.09.2026).
        Hier stand `5 < anzahl < 200` auf dem Korb „ruft niemand", und am
        12.09. ist der auf **null** gefallen: Die letzten 19 Routen sind
        gesichtet, jede steht nun mit Begruendung unter „Knopf fehlt",
        „wartet auf eine Entscheidung" oder „erklaert". Der Test wurde rot,
        obwohl das Werkzeug richtig zaehlt.

        **Und der Kommentar, der hier stand, hatte es vorhergesagt:** Eine
        Zahlenschranke auf dem Restkorb messe den *Stand der Beurteilung* und
        nicht das Werkzeug, sie haette „bei jeder ehrlichen Arbeit im Weg
        gestanden". Genau das ist eingetreten. Die Antwort darauf ist nicht
        eine kleinere Zahl — das waere die Schranke, die bei der naechsten
        ehrlichen Arbeit wieder im Weg steht.

        **Was der Test wirklich meinte:** Wuerde der Abgleich zu grosszuegig,
        zaehlten Routen als *gerufen*, die niemand ruft — und dann faellt die
        **Summe aller vier Koerbe**. Die ist unabhaengig davon, wie viel
        gesichtet wurde, und trifft die Fehlerrichtung genau.

        **Gegengeprueft, nicht angenommen (12.09.2026):** Mit einem
        `trifft_ende`, das immer `True` liefert — dem Fehler, den dieser Test
        fangen soll —, fallen alle vier Koerbe auf null und die Schranke
        schlaegt an. Ein Waechter, der beim ersten Lauf gruen ist, beweist
        sonst nichts.
        """
        koerbe = ("Der Knopf fehlt", "Wartet auf eine Entscheidung",
                  "Ruft niemand", "Erklaert")
        summe = 0
        for korb in koerbe:
            assert korb in ausgabe, f"Korb fehlt: {korb}"
            kopfzeile = [z for z in ausgabe.splitlines() if z.startswith(korb)][0]
            summe += int(kopfzeile.rsplit("—", 1)[-1].strip().rstrip(":").split()[0])

        # Am 12.09.2026 sind es 99 von 532 Endpunkten. Die Bandbreite haelt
        # den Zerfall auf, ohne die Sichtung zu behindern: Wer erklaert,
        # verschiebt zwischen den Koerben und aendert die Summe nicht.
        assert 20 < summe < 300, f"unglaubwuerdige Summe: {summe}"

    def test_eine_gerufene_route_steht_nicht_unter_den_offenen(self, ausgabe):
        """Die Gegenrichtung — und sie rostet nicht.

        **Hier stand dreimal an einem Tag ein anderer Kanarienvogel, und
        jedes Mal habe ich ihn selbst erlegt.** Erst `/api/projects/seed`
        (Stunden spaeter als „Wartung von Hand" erklaert), dann
        `/api/usercards/{card_id}` (in die Kategorie „wartet auf eine
        Entscheidung" gewandert), dann `/api/academy/modules` (als Doppelung
        erklaert). Ein Test, der eine **einzelne** Route beim Namen nennt,
        misst nicht das Werkzeug, sondern den Stand der Beurteilung — und der
        aendert sich genau dann, wenn jemand arbeitet.

        Deshalb jetzt eine Eigenschaft statt eines Namens: Eine Route, die das
        Frontend nachweislich **ruft**, darf nicht unter den offenen stehen.
        Das ist die Richtung, in der ein Fehler wehtut — eine Falschmeldung
        schickt jemanden auf die Suche nach einem Knopf, den es gibt. Und sie
        bleibt wahr, egal wie viele Routen noch beurteilt werden.
        """
        offener_teil = ausgabe.split("Ruft niemand")[1].split("\n\n")[0]
        # `/api/auth/login` ruft jede Anmeldung; `/api/leads/` die Betriebsliste.
        for gerufen in ("/api/auth/login", "/api/leads/{lead_id}/notes"):
            assert gerufen not in offener_teil, (
                f"{gerufen} steht unter den offenen Routen, wird aber gerufen — "
                f"eine Falschmeldung schickt jemanden auf die Suche nach einem "
                f"Knopf, den es gibt.")

    def test_die_urteilskoerbe_sind_besetzt(self, ausgabe):
        """Ein Urteilskorb muss etwas enthalten, sonst ist eine Einsortierung tot.

        Faellt „wartet auf eine Entscheidung" oder „erklaert" auf null, ist
        entweder alles entschieden — dann gehoert die Kategorie weg — oder
        die Zuordnung greift nicht mehr. Beides gehoert bemerkt.

        **„Ruft niemand" steht seit dem 12.09.2026 nicht mehr in dieser
        Liste, und das ist kein Nachlassen.** Er ist kein Urteilskorb,
        sondern der **Rest**: alles, was noch keines hat. Leer heisst dort
        „fertig gesichtet" und nicht „Zuordnung tot" — die Bedingung, unter
        der die anderen drei alarmieren, gilt fuer ihn gerade umgekehrt. Dass
        er ueberhaupt noch ausgewiesen wird, prueft der Test darueber; dass
        er nicht heimlich alles verschluckt, die Summe ebendort.
        """
        for korb in ("Wartet auf eine Entscheidung", "Erklaert", "Der Knopf fehlt"):
            assert korb in ausgabe, f"Korb fehlt: {korb}"
            kopfzeile = [z for z in ausgabe.splitlines() if z.startswith(korb)][0]
            anzahl = int(kopfzeile.rsplit("—", 1)[-1].strip().rstrip(":").split()[0])
            assert anzahl > 0, f"{korb} ist leer"

    def test_der_restkorb_wird_weiterhin_ausgewiesen(self, ausgabe):
        """Leer ja, verschwunden nein.

        Ein Korb, der bei null nicht mehr gedruckt wird, nimmt der naechsten
        neuen Route ihren Platz: Sie taucht dann nirgends auf, und „nichts
        gefunden" sieht aus wie „alles in Ordnung".
        """
        assert "Ruft niemand" in ausgabe
