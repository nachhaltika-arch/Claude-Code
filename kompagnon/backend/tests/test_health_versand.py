# -*- coding: utf-8 -*-
"""`/health` sagt, ob die Automatik ueberhaupt Post verschickt.

**Der Befund vom 14.09.2026.** Die Versandsperre steht per Vorgabe auf
**aus** — das ist richtig so, seit am 17.08.2026 ein Job vier Monate lang
Erinnerungen an Nicht-Kunden schickte. Aber ihr Zustand war von aussen
**nicht messbar**: `/health` fuehrte ihn nicht, `GET /api/versand` verlangt
eine Anmeldung. Damit liess sich die Frage „geht das Nachfassen im Trichter
ueberhaupt raus?" nur beantworten, indem man sich anmeldet — und ein
Schalter, dessen Aus-Zustand niemand bemerkt, ist derselbe Fehler wie der,
gegen den er gebaut wurde.

**Gemeldet wird der Zustand, nicht die Einstellung.** Gelesen wird durch
dieselbe Funktion, die auch der Versand fragt.
"""
from services import versandsperre


def test_health_fuehrt_den_versandzustand(client):
    daten = client.get("/health").json()
    assert "versand" in daten, "Die Versandsperre fehlt in /health"
    assert isinstance(daten["versand"]["automatisch"], bool)


def test_er_folgt_dem_schalter(client, app):
    """Positiv **und** negativ geprueft: Ein Feld, das immer `false` meldet,
    waere von einem richtigen nicht zu unterscheiden."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        vorher = versandsperre.automatischer_versand_erlaubt(db)
        try:
            versandsperre.setzen(db, True)
            db.commit()
            assert client.get("/health").json()["versand"]["automatisch"] is True

            versandsperre.setzen(db, False)
            db.commit()
            assert client.get("/health").json()["versand"]["automatisch"] is False
        finally:
            versandsperre.setzen(db, vorher)
            db.commit()
    finally:
        db.close()


def test_er_bleibt_gesperrt_wenn_die_abfrage_scheitert(client, monkeypatch):
    """`/health` darf daran nicht scheitern — und im Zweifel meldet es
    `false`. Eine Sperre, die bei einem Fehler offen aussieht, ist keine."""
    def kaputt(*_args, **_kwargs):
        raise RuntimeError("keine Sitzung")

    monkeypatch.setattr(versandsperre, "in_eigener_sitzung_erlaubt", kaputt)

    daten = client.get("/health").json()
    assert daten["versand"]["automatisch"] is False
