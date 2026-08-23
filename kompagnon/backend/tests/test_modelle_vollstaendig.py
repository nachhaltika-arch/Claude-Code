"""Alle Modelle sind registriert und ihre Beziehungen loesbar (L-25).

**Warum es diesen Test gibt.** `database.py` wird am 22.08.2026 nach
Bereichen aufgeteilt — Akademie, Assistent, Crawler, KAS, Widget. Die 18
`relationship()`-Aufrufe darin nennen ihre Gegenseite als **Zeichenkette**
(`relationship("Project")`), und SQLAlchemy loest den Namen erst beim ersten
Zugriff auf.

Das geht ueber Dateigrenzen hinweg gut — **solange jedes Modul geladen ist**.
Wird eines nicht importiert, faellt das nicht beim Start auf, sondern bei
irgendeiner Abfrage, mit einer Meldung wie „expression 'Project' failed to
locate a name". An einer Stelle, die mit der Ursache nichts zu tun hat.

Der Test zwingt die Aufloesung deshalb sofort und an einer Stelle.
"""
import pytest


def test_alle_beziehungen_lassen_sich_aufloesen():
    """`configure_mappers` macht genau das, was sonst der erste Zugriff tut."""
    from sqlalchemy.orm import configure_mappers

    import database  # noqa: F401  — laedt alle Teildateien mit

    configure_mappers()


def test_die_erwarteten_modelle_sind_da():
    """Eine Datei, die niemand importiert, faellt sonst still weg."""
    from database import Base

    namen = {m.class_.__name__ for m in Base.registry.mappers}

    for erwartet in ("Lead", "Project", "User", "AuditResult", "Briefing",
                     "AcademyCourse", "AssistantConversation", "CrawlJob",
                     "KasPage", "WidgetRequest", "MailEvent"):
        assert erwartet in namen, f"{erwartet} ist nicht registriert"


def test_die_zahl_der_modelle_stimmt():
    """Faellt sie, ist eine Teildatei nicht mehr eingebunden — genau der
    Fehler, den dieser Test verhindern soll."""
    from database import Base

    assert len(Base.registry.mappers) >= 39, (
        f"{len(Base.registry.mappers)} Modelle registriert; erwartet mindestens 39")
