"""Die KI-Sichtbarkeit muss sammeln, nicht überschreiben (L-85).

**Warum das über den Produktwert entscheidet.** Beim Bau von L-58 (b) blieb
`geo_analyses.ki_sichtbarkeit` ein einzelnes Feld: Jeder Lauf ersetzte den
vorigen. Der Wert der Messung entsteht aber erst aus dem Verlauf — „vor drei
Monaten null Nennungen, heute drei" ist die Aussage, für die ein Betrieb
zahlt. Eine Momentaufnahme ist es nicht.

Genau deshalb sind die Fragen fest verdrahtet und nicht modellerzeugt: Zwei
Läufe **können** verglichen werden. Es sammelte sie nur niemand.

**Was gesammelt wird und was nicht.** Der Verlauf trägt je Lauf das Datum und
je System die Trefferzahl — nicht die Antworttexte und nicht die Belege. Die
stehen im aktuellen Befund; im Verlauf würden sie die Spalte in einem Jahr
unlesbar machen und beantworten die Frage nicht, die der Verlauf stellt.

**Nach oben begrenzt.** Ein Verlauf, der unbegrenzt wächst, ist kein Verlauf,
sondern ein Leck: `monitoring_history` nebenan zeigt dasselbe Muster, und die
Spalte wird bei jedem Lesen mitgeladen.
"""
import pytest


@pytest.fixture(autouse=True)
def _spalten(app):
    from sqlalchemy import text
    from database import SessionLocal

    db = SessionLocal()
    try:
        for sql in (
            "ALTER TABLE geo_analyses ADD COLUMN IF NOT EXISTS ki_sichtbarkeit JSONB",
            "ALTER TABLE geo_analyses ADD COLUMN IF NOT EXISTS ki_sichtbarkeit_am TIMESTAMP",
            "ALTER TABLE geo_analyses ADD COLUMN IF NOT EXISTS ki_sichtbarkeit_verlauf JSONB",
        ):
            db.execute(text(sql))
        db.commit()
    finally:
        db.close()


BEFUND = {
    "collected": True,
    "erhoben_bei": 2,
    "genannt_bei": 1,
    "anbieter": {
        "chatgpt": {"collected": True, "anzeige": "ChatGPT", "modell": "gpt-5.6",
                    "genannt_bei": 2, "beantwortet": 3, "von": 3, "quote": 0.67,
                    "fragen": [{"frage": "…", "genannt": True,
                                "auszug": "sehr langer Text " * 40,
                                "belege": ["https://beispiel.de/"]}]},
        "perplexity": {"collected": True, "anzeige": "Perplexity", "modell": "sonar",
                       "genannt_bei": 0, "beantwortet": 3, "von": 3, "quote": 0.0,
                       "fragen": []},
        "claude": {"collected": False, "anzeige": "Claude",
                   "grund": "ANTHROPIC_API_KEY nicht gesetzt"},
    },
}


class TestEintragBauen:
    def test_traegt_je_system_die_trefferzahl(self):
        from services.ki_sichtbarkeit import verlaufseintrag

        eintrag = verlaufseintrag(BEFUND, "2026-08-22T15:00:00")

        assert eintrag["am"] == "2026-08-22T15:00:00"
        assert eintrag["anbieter"]["chatgpt"] == {"genannt_bei": 2, "von": 3, "quote": 0.67}
        assert eintrag["anbieter"]["perplexity"]["genannt_bei"] == 0

    def test_ein_nicht_erhobenes_system_steht_nicht_als_null_da(self):
        """Dieselbe Regel wie im Befund selbst: nicht erhoben ist nicht null.

        Stuende Claude hier mit 0 drin, zeigte die Verlaufskurve spaeter einen
        Einbruch, den es nie gab — nur weil ein Schluessel fehlte.
        """
        from services.ki_sichtbarkeit import verlaufseintrag

        eintrag = verlaufseintrag(BEFUND, "2026-08-22T15:00:00")

        assert "claude" not in eintrag["anbieter"]
        assert eintrag["nicht_erhoben"] == ["claude"]

    def test_die_antworttexte_bleiben_draussen(self):
        """Sonst ist die Spalte in einem Jahr unlesbar — und die Frage, die
        der Verlauf stellt, beantworten sie nicht."""
        from services.ki_sichtbarkeit import verlaufseintrag

        roh = str(verlaufseintrag(BEFUND, "2026-08-22T15:00:00"))

        assert "sehr langer Text" not in roh
        assert "beispiel.de" not in roh


class TestAnhaengen:
    def test_der_erste_lauf_beginnt_den_verlauf(self):
        from services.ki_sichtbarkeit import verlauf_fortschreiben

        neu = verlauf_fortschreiben(None, BEFUND, "2026-08-22T15:00:00")

        assert len(neu) == 1

    def test_der_zweite_haengt_an_statt_zu_ersetzen(self):
        """Das ist der ganze Befund von L-85."""
        from services.ki_sichtbarkeit import verlauf_fortschreiben

        eins = verlauf_fortschreiben(None, BEFUND, "2026-08-01T10:00:00")
        zwei = verlauf_fortschreiben(eins, BEFUND, "2026-08-22T15:00:00")

        assert [e["am"] for e in zwei] == ["2026-08-01T10:00:00", "2026-08-22T15:00:00"]

    def test_ein_nicht_erhobener_lauf_wird_nicht_vermerkt(self):
        """Ohne jeden Zugang gibt es nichts zu vergleichen."""
        from services.ki_sichtbarkeit import verlauf_fortschreiben

        vorher = verlauf_fortschreiben(None, BEFUND, "2026-08-01T10:00:00")
        nachher = verlauf_fortschreiben(vorher, {"collected": False, "grund": "kein Zugang"},
                                        "2026-08-22T15:00:00")

        assert nachher == vorher

    def test_der_verlauf_waechst_nicht_unbegrenzt(self):
        from services.ki_sichtbarkeit import VERLAUF_MAX, verlauf_fortschreiben

        verlauf = None
        for i in range(VERLAUF_MAX + 12):
            verlauf = verlauf_fortschreiben(verlauf, BEFUND, f"2026-01-{i:02d}T00:00:00")

        assert len(verlauf) == VERLAUF_MAX

    def test_gekappt_wird_vorne_und_das_neueste_bleibt(self):
        from services.ki_sichtbarkeit import VERLAUF_MAX, verlauf_fortschreiben

        verlauf = None
        for i in range(VERLAUF_MAX + 3):
            verlauf = verlauf_fortschreiben(verlauf, BEFUND, f"2026-01-{i:02d}T00:00:00")

        assert verlauf[-1]["am"] == f"2026-01-{VERLAUF_MAX + 2:02d}T00:00:00"

    def test_ein_kaputter_bestand_wirft_nicht(self):
        """Die Spalte ist JSONB und kann alles enthalten, was einmal
        hineingeschrieben wurde."""
        from services.ki_sichtbarkeit import verlauf_fortschreiben

        neu = verlauf_fortschreiben("kein array", BEFUND, "2026-08-22T15:00:00")

        assert len(neu) == 1
