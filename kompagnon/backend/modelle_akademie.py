"""Die Modelle der Akademie (L-25).

**Warum eigene Datei, 22.08.2026.** `database.py` hatte 1.361 Zeilen und 39
Modellklassen. Zehn Klassen: Kurse, Module, Lektionen, Fortschritt, Quiz, Zertifikate
und die Zugaenge dazu.

**Wichtig:** Diese Datei wird von `database.py` am Ende importiert. Ohne das
waere sie nie geladen, und die `relationship()`-Aufrufe der anderen Modelle
faenden ihre Gegenseite nicht — mit einem Fehler zur Laufzeit an einer
Stelle, die mit der Ursache nichts zu tun hat.
`tests/test_modelle_vollstaendig.py` haelt das fest.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from database import Base


class AcademyCourse(Base):
    """Academy course."""
    __tablename__ = "academy_courses"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default='')
    thumbnail_url = Column(String(500), default='')
    is_published = Column(Boolean, default=False)
    target_audience = Column(String(20), default='both')   # 'customer'|'employee'|'both'
    category = Column(String(100), default='')
    category_color = Column(String(50), default='primary')
    audience = Column(String(20), default='employee')
    formats = Column(Text, default='["text"]')
    linear_progress = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    # „Nur fuer Zugewiesene" — das Gegenstueck zu Memberspots „Manuell".
    # Vorgabe False: Ein Kurs ohne Sperre bleibt sichtbar wie bisher. Waere
    # die Zuweisung ab sofort zwingend, verschwaende der Bestand vor den Augen
    # der heutigen Kunden. Erst dieses Feld gibt `AcademyCustomerAccess`
    # ueberhaupt eine Wirkung — bis zum 19.08.2026 fragte es kein Lesepfad ab.
    is_locked = Column(Boolean, default=False)


class AcademyChecklistItem(Base):
    """Checklist item for an academy course."""
    __tablename__ = "academy_checklist_items"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('academy_courses.id', ondelete='CASCADE'), nullable=False)
    label = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0)


class AcademyModule(Base):
    """Module within an academy course."""
    __tablename__ = "academy_modules"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('academy_courses.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    position = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    # Aus dem Memberspot-Vergleich vom 19.08.2026: Dort traegt jedes Modul
    # eine Zeile, die sagt, worum es geht, und ein Bild. Ohne beides ist eine
    # Modulliste eine Aufzaehlung von Ueberschriften.
    # `default=''` statt NULL: Die Oberflaeche soll nicht zwei Faelle
    # unterscheiden muessen, wo einer reicht.
    description = Column(Text, default='')
    thumbnail_url = Column(String(500), default='')


class AcademyLesson(Base):
    """Lesson within a module."""
    __tablename__ = "academy_lessons"
    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey('academy_modules.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    position = Column(Integer, default=0)
    type = Column(String(20), default='text')         # 'video'|'text'|'quiz'
    content_text = Column(Text, default='')
    content_url = Column(String(500), default='')
    video_url = Column(String(500), default='')
    file_url = Column(String(500), default='')
    duration_minutes = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    # Stand nur in der Datenbank (migrations_runtime.py::run_migrations), nicht im Modell.
    # Der Router uebergab das Feld beim Anlegen — und SQLAlchemy wies es ab:
    # `POST /api/academy/modules/{id}/lessons` antwortete mit 500, seit es
    # den Endpunkt gibt. Kurse und Module liessen sich anlegen, Lektionen nie.
    checklist_items_json = Column(Text, default='[]')


class AcademyLessonProgress(Base):
    """User progress on a lesson (legacy)."""
    __tablename__ = "academy_lesson_progress"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    lesson_id = Column(Integer, ForeignKey('academy_lessons.id', ondelete='CASCADE'), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)


class AcademyProgress(Base):
    """User progress per lesson (with quiz score)."""
    __tablename__ = "academy_progress"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    lesson_id = Column(Integer, ForeignKey('academy_lessons.id', ondelete='CASCADE'))
    completed_at = Column(DateTime, nullable=True)
    score = Column(Float, nullable=True)


class AcademyCertificate(Base):
    """Course completion certificate."""
    __tablename__ = "academy_certificates"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, ForeignKey('academy_courses.id', ondelete='CASCADE'))
    issued_at = Column(DateTime, default=datetime.utcnow)
    certificate_code = Column(String(64), unique=True, nullable=False)


class AcademyQuizQuestion(Base):
    """Quiz question belonging to a lesson."""
    __tablename__ = "academy_quiz_questions"
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey('academy_lessons.id', ondelete='CASCADE'), nullable=False)
    question = Column(Text, nullable=False)
    answers_json = Column(Text, default='[]')   # [{text, is_correct}]
    sort_order = Column(Integer, default=0)


class AcademyModuleAccess(Base):
    """Welche gesperrten Module ein Kunde freigeschaltet bekommen hat.

    Das Gegenstueck zu `AcademyCustomerAccess`, eine Ebene tiefer. Damit wird
    aus einem Kurs je Zielgruppe **ein** Kurs mit Zweigen: Der Pflichtteil
    gilt fuer alle, die gewerkespezifischen Module nur fuer die passenden
    Betriebe.
    """
    __tablename__ = "academy_module_access"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    module_id = Column(Integer, ForeignKey('academy_modules.id', ondelete='CASCADE'), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer, nullable=True)


class AcademyCustomerAccess(Base):
    """Which courses a customer (lead) has been granted access to."""
    __tablename__ = "academy_customer_access"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    course_id = Column(Integer, ForeignKey('academy_courses.id', ondelete='CASCADE'), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer, nullable=True)
