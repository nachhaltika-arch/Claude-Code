"""Der Deploy gilt erst als fertig, wenn der Dienst wirklich hochgefahren ist.

Beobachtet beim Produktiv-Merge am 18.08.2026: Render meldete den Backend-Deploy
um 09:43:58 als `live`, und der CI-Job war damit gruen. Der Dienst selbst war es
nicht — `/health` sagte bis **09:48:32** noch

    {"status": "ok", "scheduler_running": false, "startup_complete": null}

also viereinhalb Minuten lang: Anfragen werden beantwortet, aber der Start lief
noch. Die acht Startphasen (Migrationen, Scheduler, Demokonten-Abschaltung)
laufen als Hintergrundaufgabe weiter, nachdem der Server schon antwortet.

Das Heikle daran ist nicht die Wartezeit, sondern der Gruenton: Waere eine Phase
gescheitert, haette der Deploy-Job es nie erfahren. Genau dieser Fall — sieben
von acht Phasen fielen aus — blieb hier schon einmal monatelang unbemerkt, und
deshalb gibt es `startup_complete` ueberhaupt.

Der Job fragt jetzt den Dienst selbst, nicht nur Renders Auskunft ueber ihn.
"""

from pathlib import Path

CI = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"
INHALT = CI.read_text(encoding="utf-8")


def test_der_deploy_job_fragt_die_gesundheitspruefung():
    assert "/health" in INHALT, "Der Deploy verlaesst sich allein auf Renders Status"


def test_er_wartet_auf_den_abgeschlossenen_start():
    assert "startup_complete" in INHALT


def test_ausgefallene_startphasen_machen_den_lauf_rot():
    # Ohne diese Auswertung wuerde ein unvollstaendiger Start nur als
    # Zeitueberschreitung auffallen — und niemand wuesste, welche Phase fehlt.
    assert "startup_missing" in INHALT


def test_die_wartezeit_ist_begrenzt():
    assert "READY_MAX_SECONDS" in INHALT
