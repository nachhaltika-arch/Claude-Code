"""`/api/dashboard/alerts` antwortete produktiv mit 500.

Gemessen am 19.08.2026 am laufenden Produktivsystem, damals noch ohne
Anmeldung erreichbar:

    GET /api/dashboard/alerts → 500 {"detail":"Internal server error",
                                     "error_type":"TypeError"}

Aufgefallen ist es nur, weil an dem Tag alle offenen Routen durchgerufen
wurden. Der Endpunkt hängt an keiner Oberfläche, die jemand täglich benutzt —
er wäre sonst längst gemeldet worden.

Diese Datei stellt den Fall nach, statt ihn zu erraten: ein Projekt, wie es
produktiv steht, und dann die Frage, was der Code damit tut. Die drei
Verdächtigen aus der ersten Durchsicht waren `entry.hours` (fällt aus:
`nullable=False`), `scope_creep_flags` (fällt aus: `ADD COLUMN … DEFAULT 0`
füllt bestehende Zeilen) und die Zeitzone von `start_date`.
"""
from datetime import datetime, timedelta, timezone

import pytest

from database import SessionLocal, Project


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture
def projekt(db, fremder_betrieb):
    """Ein Projekt in einer laufenden Phase, seit zehn Tagen — also überfällig."""
    p = Project(
        company_name="Alarmprobe Betrieb", lead_id=fremder_betrieb,
        status="phase_1",
        start_date=datetime.utcnow() - timedelta(days=10),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    yield p
    db.delete(p)
    db.commit()


def test_die_alarme_lassen_sich_abrufen(client, auth_headers, projekt):
    """Der produktiv gemessene Fall — hier muss er sich zeigen."""
    # Act
    antwort = client.get("/api/dashboard/alerts", headers=auth_headers)

    # Assert
    assert antwort.status_code == 200, antwort.text


def test_ein_ueberfaelliges_projekt_erzeugt_einen_alarm(client, auth_headers, projekt):
    """Sonst wäre eine 200 auf einer leeren Liste kein Beleg."""
    # Act
    alarme = client.get("/api/dashboard/alerts", headers=auth_headers).json()

    # Assert
    meine = [a for a in alarme if a.get("project_id") == projekt.id]
    assert meine, f"Kein Alarm für ein Projekt, das seit 10 Tagen in Phase 1 steht"
    assert any(a["alert_type"] == "overdue_phase" for a in meine)


def test_auch_mit_zeitzonenbehafteter_startzeit(client, auth_headers, db, fremder_betrieb):
    """Der wahrscheinlichste Verdacht.

    `start_date` ist im Modell `DateTime` ohne Zeitzone, und der Code rechnet
    `datetime.utcnow() - project.start_date`. Steht in der Spalte ein Wert
    **mit** Zeitzone, ist genau das ein `TypeError` — „can't subtract
    offset-naive and offset-aware datetimes".
    """
    # Arrange
    p = Project(
        company_name="Alarmprobe Zeitzone", lead_id=fremder_betrieb,
        status="phase_2",
        start_date=datetime.now(timezone.utc) - timedelta(days=9),
    )
    db.add(p)
    db.commit()

    try:
        # Act
        antwort = client.get("/api/dashboard/alerts", headers=auth_headers)

        # Assert
        assert antwort.status_code == 200, antwort.text
    finally:
        db.delete(p)
        db.commit()


def test_ohne_startzeit_faellt_nichts_um(client, auth_headers, db, fremder_betrieb):
    """`start_date` ist nullable — ein Projekt ohne Start ist erlaubt."""
    # Arrange
    p = Project(company_name="Alarmprobe ohne Start", status="phase_3", lead_id=fremder_betrieb)
    db.add(p)
    db.commit()

    try:
        # Act / Assert
        assert client.get("/api/dashboard/alerts",
                          headers=auth_headers).status_code == 200
    finally:
        db.delete(p)
        db.commit()


def test_ein_projekt_ohne_scope_creep_zaehler(client, auth_headers, db, fremder_betrieb):
    """Der zweite Verdacht — und der einzige, der sich hier erzwingen lässt.

    `scope_creep_flags` hat im Modell `default=0`, aber das ist eine
    Python-Vorgabe: Sie greift beim Anlegen über das Modell, nicht bei einer
    Zeile, die auf anderem Weg entstanden ist. Steht dort `NULL`, ist
    `project.scope_creep_flags > 0` ein `TypeError` — „'>' not supported
    between instances of 'NoneType' and 'int'".

    Die Spalte wird über `ALTER TABLE … ADD COLUMN … DEFAULT 0` nachgezogen,
    was bestehende Zeilen füllt. Wer sie umgeht, bekommt trotzdem NULL.
    """
    from sqlalchemy import text

    # Arrange
    p = Project(
        company_name="Alarmprobe ohne Zähler", lead_id=fremder_betrieb,
        status="phase_4",
        start_date=datetime.utcnow() - timedelta(days=8),
    )
    db.add(p)
    db.commit()
    db.execute(text("UPDATE projects SET scope_creep_flags = NULL WHERE id = :i"),
               {"i": p.id})
    db.commit()

    try:
        # Act
        antwort = client.get("/api/dashboard/alerts", headers=auth_headers)

        # Assert
        assert antwort.status_code == 200, antwort.text
    finally:
        db.delete(p)
        db.commit()
