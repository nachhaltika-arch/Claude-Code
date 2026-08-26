# -*- coding: utf-8 -*-
"""Die Marge wird täglich gerechnet — jetzt sieht sie auch jemand (L-95).

**Der Befund (26.08.2026).** `components/MarginBadge.jsx` lag gebaut im
Quellbaum, und `margin_percent` kam im **ganzen Frontend an keiner anderen
Stelle** vor. Das Backend rechnet die Marge dagegen täglich
(`job_update_all_margins`), und der Wert steht an jedem Projekt.

Angezeigt wurde er nirgends. Der einzige Ort, an dem er seit dem 26.08.
auftaucht, war die Warnliste auf dem Dashboard — und auch nur, wenn die
Marge bereits **kritisch** ist. Wer wissen wollte, ob ein Projekt sich
lohnt, bevor es brennt, hatte keinen Weg dorthin.

**Warum der Status vom Server kommt.** Die naheliegende Abkürzung beim
Anschließen war, die beiden Schwellen (78 % / 70 %) im Frontend nachzubauen.
Das ist die zweite Quelle für dieselbe Zahl — der Fehler, den
`paketpreise.test.js` für Preise verbietet, weil er bereits einmal Geld
gekostet hat. `MarginCalculator.status_fuer` ist jetzt die eine Stelle, und
die Projektliste gibt `margin_status` mit heraus.
"""
import pytest

from services.margin_calculator import MarginCalculator

pytestmark = pytest.mark.usefixtures("app")


class TestDieEinordnung:
    @pytest.mark.parametrize("prozent,erwartet", [
        (100, "green"),
        (78, "green"),     # genau die Zielmarge
        (77.9, "yellow"),
        (70, "yellow"),    # genau das Minimum
        (69.9, "red"),
        (0, "red"),
        (-12, "red"),      # ein Projekt kann Verlust machen
    ])
    def test_die_schwellen_liegen_wo_sie_liegen(self, prozent, erwartet):
        """Die Grenzen sind einschliessend: 78 ist noch gruen, 70 noch gelb.

        Das steht hier, weil `>=` und `>` beim Nachbauen an einer zweiten
        Stelle genau die Sorte Abweichung ergeben, die niemandem auffaellt.
        """
        assert MarginCalculator.status_fuer(prozent) == erwartet

    def test_die_konstanten_sind_die_erwarteten(self):
        """Aendert jemand die Zielmarge, soll er es hier sehen — und nicht
        an einer Anzeige, die stillschweigend anders einordnet."""
        assert MarginCalculator.TARGET_MARGIN_PERCENT == 78
        assert MarginCalculator.MIN_ACCEPTABLE_MARGIN_PERCENT == 70


class TestDieProjektlisteSagtEs:
    @pytest.fixture
    def projekt(self, app):
        from database import Project, SessionLocal

        db = SessionLocal()
        try:
            p = Project(lead_id=None, status="phase_3", margin_percent=64.0)
            db.add(p)
            db.commit()
            db.refresh(p)
            yield p.id
            db.query(Project).filter(Project.id == p.id).delete(
                synchronize_session=False)
            db.commit()
        finally:
            db.close()

    def test_jede_zeile_traegt_ihren_status(self, client, auth_headers, projekt):
        """Ohne ihn muesste die Oberflaeche die Schwellen kennen."""
        zeilen = client.get("/api/projects/?limit=200",
                            headers=auth_headers).json()

        meins = [z for z in zeilen if z["id"] == projekt]
        assert meins, "das Projekt fehlt in der Liste"
        assert meins[0]["margin_status"] == "red"
        assert meins[0]["margin_percent"] == 64.0

    def test_der_status_passt_immer_zum_wert(self, client, auth_headers,
                                             projekt):
        """Der Wächter gegen ein Auseinanderlaufen: Was die Liste als Status
        nennt, muss zu dem Prozentwert daneben passen — beides kommt aus
        derselben Zeile, aber über zwei Wege."""
        zeilen = client.get("/api/projects/?limit=200",
                            headers=auth_headers).json()

        falsch = [
            f"Projekt {z['id']}: {z['margin_percent']} % → {z['margin_status']}"
            for z in zeilen
            if z.get("margin_status")
            and z["margin_status"] != MarginCalculator.status_fuer(
                z.get("margin_percent") or 0)
        ]

        assert falsch == [], "Status und Wert laufen auseinander:\n  " + "\n  ".join(falsch)
