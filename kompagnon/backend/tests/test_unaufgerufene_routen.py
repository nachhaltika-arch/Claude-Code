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
    def test_es_meldet_weiterhin_offene_routen(self, ausgabe):
        """Gegenprobe zur Lockerung: Wuerde `passt_auf` zu grosszuegig
        greifen, faende das Werkzeug gar nichts mehr — und waere gruen,
        ohne etwas zu pruefen."""
        assert "Ruft niemand" in ausgabe

        kopfzeile = [z for z in ausgabe.splitlines() if z.startswith("Ruft niemand")][0]
        anzahl = int(kopfzeile.rsplit("—", 1)[-1].strip().rstrip(":"))
        assert 30 < anzahl < 200, f"unglaubwuerdige Zahl: {anzahl}"

    def test_eine_route_ohne_jeden_aufrufer_bleibt_gemeldet(self, ausgabe):
        """`/api/projects/seed` legt Beispieldaten an und wird von keiner
        Oberflaeche gerufen — ein Fall, der stehen bleiben muss."""
        assert "/api/projects/seed" in ausgabe
