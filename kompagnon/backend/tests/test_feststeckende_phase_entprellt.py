"""Ein Ticket je feststeckendem Projekt — nicht eines pro Tag.

**Am 2026-08-23 am produktiven Bestand gefunden.** `support_tickets` trug
**2.343** Zeilen bei 62 Betrieben und 11 Nutzern. Davon sind **2.335** vom Typ
`system`, alle `open`, und sie entstehen seit dem 10.04.2026 mit rund
**neunzehn pro Tag** — Titel: „Projekt 10 feststeckend in phase_1".

Die Ursache stand als Kommentar über der Stelle: „nur einmal pro
Projekt+Phase**+Tag**". Der Schlüssel lautete
`stuck-{id}-{status}-{JJJJMMTT}` — das Datum darin macht jeden Tag einen
neuen Schlüssel und damit ein neues Ticket. Über 4½ Monate ergibt das den
Bestand.

**Es ist derselbe Fehler, der zwanzig Zeilen weiter unten schon behoben war.**
`job_check_missing_materials` verschickte bis zum 17.08. dieselbe Mail jeden
Morgen erneut; ein Betrieb bekam sie 135 Tage lang. Dort fiel es auf, weil
Mails beim Empfänger ankommen. Hier fiel es nicht auf, weil Tickets nur in
einer Liste stehen — und wer schaut in eine Liste, in der 99,7 % Maschinenlärm
steht?

Denn das ist die eigentliche Wirkung: **Acht** Rückmeldungen von Menschen
liegen in dieser Tabelle. Sie sind unauffindbar. Und als am 22.08. auffiel,
dass alle Tickets ohne Anmeldung lesbar waren (L-90), sah niemand nach, was
darin überhaupt steht.

Die Regel jetzt: Solange für dasselbe Projekt in derselben Phase ein
**offenes** Systemticket steht, entsteht kein zweites — die Beschreibung wird
fortgeschrieben. Wer das Ticket schließt, hat entschieden; dann kommt auch
kein neues.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text

from database import SessionLocal, Lead, Project
from automations.scheduler_kontakt import job_check_overdue_phases


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture
def festsitzendes_projekt(db):
    """Ein Projekt, das seit zehn Tagen in phase_1 steht."""
    betrieb = Lead(company_name="Entprellprobe GmbH")
    db.add(betrieb)
    db.commit()
    db.refresh(betrieb)

    p = Project(
        lead_id=betrieb.id,
        company_name="Entprellprobe GmbH",
        status="phase_1",
        start_date=datetime.utcnow() - timedelta(days=10),
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    yield p

    db.execute(text("DELETE FROM support_tickets WHERE ticket_number LIKE :m"),
               {"m": f"stuck-{p.id}-%"})
    db.delete(p)
    db.delete(betrieb)
    db.commit()


def _tickets(db, projekt_id: int) -> list:
    return db.execute(text(
        "SELECT ticket_number, status, description FROM support_tickets "
        "WHERE ticket_number LIKE :m ORDER BY id"
    ), {"m": f"stuck-{projekt_id}-%"}).fetchall()


def test_der_erste_lauf_legt_ein_ticket_an(db, festsitzendes_projekt):
    # Act
    job_check_overdue_phases()

    # Assert
    zeilen = _tickets(db, festsitzendes_projekt.id)
    assert len(zeilen) == 1


def test_der_schluessel_traegt_kein_datum(db, festsitzendes_projekt):
    """Das Datum im Schlüssel war die Ursache — es darf nicht zurückkommen."""
    # Act
    job_check_overdue_phases()

    # Assert
    nummer = _tickets(db, festsitzendes_projekt.id)[0][0]
    assert nummer == f"stuck-{festsitzendes_projekt.id}-phase_1"


def test_zwei_laeufe_ergeben_ein_ticket(db, festsitzendes_projekt):
    """Der eigentliche Befund: 2.335 Zeilen entstanden genau hier."""
    # Act
    job_check_overdue_phases()
    job_check_overdue_phases()
    job_check_overdue_phases()

    # Assert
    assert len(_tickets(db, festsitzendes_projekt.id)) == 1


def test_die_beschreibung_wird_fortgeschrieben(db, festsitzendes_projekt):
    """Ein Ticket, das „seit 3 Tagen" sagt, während es 40 sind, ist wertlos."""
    # Arrange
    job_check_overdue_phases()
    db.execute(text(
        "UPDATE support_tickets SET description = 'veraltet' "
        "WHERE ticket_number = :nr"
    ), {"nr": f"stuck-{festsitzendes_projekt.id}-phase_1"})
    db.commit()

    # Act
    job_check_overdue_phases()

    # Assert
    beschreibung = _tickets(db, festsitzendes_projekt.id)[0][2]
    assert "10 Tagen" in beschreibung


def test_ein_geschlossenes_ticket_kommt_nicht_wieder(db, festsitzendes_projekt):
    """Wer schließt, hat entschieden. Ein neues Ticket überstimmt ihn."""
    # Arrange
    job_check_overdue_phases()
    db.execute(text(
        "UPDATE support_tickets SET status = 'closed' WHERE ticket_number = :nr"
    ), {"nr": f"stuck-{festsitzendes_projekt.id}-phase_1"})
    db.commit()

    # Act
    job_check_overdue_phases()

    # Assert
    zeilen = _tickets(db, festsitzendes_projekt.id)
    assert len(zeilen) == 1, "kein zweites Ticket"
    assert zeilen[0][1] == "closed", "und das geschlossene bleibt geschlossen"


def test_eine_neue_phase_bekommt_ein_eigenes_ticket(db, festsitzendes_projekt):
    """Andere Phase, anderer Sachverhalt — das gehört gemeldet."""
    # Arrange
    job_check_overdue_phases()
    festsitzendes_projekt.status = "phase_2"
    db.commit()

    # Act
    job_check_overdue_phases()

    # Assert
    nummern = {z[0] for z in _tickets(db, festsitzendes_projekt.id)}
    assert nummern == {
        f"stuck-{festsitzendes_projekt.id}-phase_1",
        f"stuck-{festsitzendes_projekt.id}-phase_2",
    }
