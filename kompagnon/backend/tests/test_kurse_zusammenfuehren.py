"""Zwei Kurssysteme werden eines — ohne dass Demo-Saat mitkommt.

Befund vom 2026-08-19 (`docs/akademie-vorbild-memberspot.md`): Das Werkzeug
führte zwei Kurswelten nebeneinander.

- `academy_courses` mit Modulen, Lektionen, Fortschritt, Quiz, Zertifikaten
  und Kundenzuweisung — das echte System, acht Oberflächen rufen es
- `courses` **ohne jede Struktur**: nur `chapter_count`, `participant_count`
  und `duration_minutes` als mitgeführte Zahlen. Eine einzige Oberfläche rief
  es (`pages/Courses.jsx`), und deren Adresse `/app/courses` stand in
  **keinem Menü** — erreichbar nur über die Adresszeile

Die drei Zeilen in `courses` sind Demo-Saat mit **erfundenen Zahlen**
(„14 Teilnehmer", „38", „9"). Genau diese Sorte Zahl hat David am 18.08. auf
den Mobil-Kacheln gefunden. Sie in die echte Akademie zu kopieren wäre keine
Zusammenführung, sondern eine Verschmutzung.

Deshalb trennt die Zusammenführung zwei Fälle: Was der Demo-Saat entspricht,
bleibt liegen. Alles andere — also alles, was ein Mensch dort angelegt hat —
wird übernommen, **unveröffentlicht**, damit es jemand ansieht, bevor es
erscheint.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import SessionLocal, AcademyCourse
from services.kurse_zusammenfuehren import zusammenfuehren


# Die Demo-Saat, wortgleich wie sie in `routers/courses.py` stand.
SAAT = [
    ("Gratis Mitgliedschaft",
     "Einführung in das KOMPAGNON-System und erste Schritte für neue Mitglieder.",
     "intern"),
    ("Website-Pflege für Kunden",
     "Wie Kunden ihre Website eigenständig pflegen, Inhalte aktualisieren und "
     "häufige Fehler vermeiden.",
     "kunde"),
    ("Homepage Standard 2025 — Das Produkt",
     "Vollständige Produktschulung: Anforderungen, Audit-Kriterien, "
     "Zertifizierungsstufen und Umsetzungsprozess.",
     "produkt"),
]


@pytest.fixture
def db(app):
    """``app`` wird gebraucht, nicht benutzt: Erst diese Fixture legt das
    Schema an — ohne sie gibt es ``academy_courses`` gar nicht."""
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture(autouse=True)
def leere_tabellen(db):
    """Beide Seiten leer in den Test — und hinterher wieder aufgeräumt.

    ``courses`` wird hier angelegt: Nach dem Abräumen des alten Systems gibt es
    dafür kein Modell mehr, also legt ``create_all`` die Tabelle nicht an.
    Die Zusammenführung muss trotzdem damit umgehen können.
    """
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT DEFAULT '',
            category VARCHAR(50) DEFAULT 'intern',
            thumbnail_color VARCHAR(20) DEFAULT '#008eaa',
            chapter_count INTEGER DEFAULT 0,
            participant_count INTEGER DEFAULT 0,
            duration_minutes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            created_by INTEGER
        )
    """))
    db.execute(text("DELETE FROM courses"))
    db.commit()

    yield

    # Ein Test löscht die Tabelle absichtlich — das Aufräumen darf daran nicht
    # scheitern und muss die Sitzung danach wieder brauchbar hinterlassen.
    try:
        db.execute(text("DELETE FROM courses"))
        db.commit()
    except SQLAlchemyError:
        db.rollback()

    db.query(AcademyCourse).filter(
        AcademyCourse.title.in_([t for t, _, _ in SAAT] + ["Echter Kurs von David"])
    ).delete(synchronize_session=False)
    db.commit()


def _lege_an(db, titel, beschreibung, kategorie):
    db.execute(
        text("INSERT INTO courses (title, description, category) "
             "VALUES (:t, :b, :k)"),
        {"t": titel, "b": beschreibung, "k": kategorie},
    )
    db.commit()


# ── Was übernommen wird ───────────────────────────────────────────────

def test_ein_echter_kurs_wird_uebernommen(db):
    # Arrange
    _lege_an(db, "Echter Kurs von David", "Von Hand angelegt.", "kunde")

    # Act
    bericht = zusammenfuehren(db)

    # Assert
    assert bericht["uebernommen"] == ["Echter Kurs von David"]
    kurs = db.query(AcademyCourse).filter(
        AcademyCourse.title == "Echter Kurs von David").first()
    assert kurs is not None
    assert kurs.description == "Von Hand angelegt."


def test_das_uebernommene_ist_unveroeffentlicht(db):
    """Ein Mensch sieht es an, bevor es in der Akademie auftaucht."""
    # Arrange
    _lege_an(db, "Echter Kurs von David", "Von Hand angelegt.", "kunde")

    # Act
    zusammenfuehren(db)

    # Assert
    kurs = db.query(AcademyCourse).filter(
        AcademyCourse.title == "Echter Kurs von David").first()
    assert kurs.is_published is False


@pytest.mark.parametrize("kategorie,erwartet", [
    ("intern", "employee"),
    ("kunde", "customer"),
    ("produkt", "both"),
])
def test_die_kategorie_wird_auf_die_zielgruppe_abgebildet(db, kategorie, erwartet):
    # Arrange
    _lege_an(db, "Echter Kurs von David", "Von Hand angelegt.", kategorie)

    # Act
    zusammenfuehren(db)

    # Assert
    kurs = db.query(AcademyCourse).filter(
        AcademyCourse.title == "Echter Kurs von David").first()
    assert kurs.target_audience == erwartet


# ── Was liegen bleibt ─────────────────────────────────────────────────

@pytest.mark.parametrize("titel,beschreibung,kategorie", SAAT)
def test_die_demo_saat_bleibt_liegen(db, titel, beschreibung, kategorie):
    """Erfundene Teilnehmerzahlen gehören nicht in die echte Akademie."""
    # Arrange
    _lege_an(db, titel, beschreibung, kategorie)

    # Act
    bericht = zusammenfuehren(db)

    # Assert
    assert bericht["uebernommen"] == []
    assert titel in bericht["saat_uebersprungen"]
    assert db.query(AcademyCourse).filter(
        AcademyCourse.title == titel).first() is None


def test_ein_bearbeiteter_saat_kurs_gilt_nicht_mehr_als_saat(db):
    """Wer den Text geändert hat, hat ihn zu seinem gemacht."""
    # Arrange
    titel, _, kategorie = SAAT[0]
    _lege_an(db, titel, "Von David umgeschrieben.", kategorie)

    # Act
    bericht = zusammenfuehren(db)

    # Assert
    assert titel in bericht["uebernommen"]


def test_ein_schon_vorhandener_titel_wird_nicht_verdoppelt(db):
    # Arrange
    db.add(AcademyCourse(title="Echter Kurs von David", description="schon da"))
    db.commit()
    _lege_an(db, "Echter Kurs von David", "Von Hand angelegt.", "kunde")

    # Act
    bericht = zusammenfuehren(db)

    # Assert
    assert bericht["uebernommen"] == []
    assert "Echter Kurs von David" in bericht["vorhanden_uebersprungen"]
    assert db.query(AcademyCourse).filter(
        AcademyCourse.title == "Echter Kurs von David").count() == 1


# ── Zweimal laufen ────────────────────────────────────────────────────

def test_zweimal_laufen_aendert_nichts(db):
    """Die Zusammenführung läuft bei jedem Start — nicht einmalig."""
    # Arrange
    _lege_an(db, "Echter Kurs von David", "Von Hand angelegt.", "kunde")

    # Act
    zusammenfuehren(db)
    zweiter = zusammenfuehren(db)

    # Assert
    assert zweiter["uebernommen"] == []
    assert db.query(AcademyCourse).filter(
        AcademyCourse.title == "Echter Kurs von David").count() == 1


def test_ohne_die_alte_tabelle_geht_es_auch(db):
    """Nach dem endgültigen Löschen der Tabelle darf der Start nicht scheitern."""
    # Arrange
    db.execute(text("DROP TABLE IF EXISTS courses"))
    db.commit()

    # Act
    bericht = zusammenfuehren(db)

    # Assert
    assert bericht["uebernommen"] == []
    assert bericht["alte_tabelle_fehlt"] is True
