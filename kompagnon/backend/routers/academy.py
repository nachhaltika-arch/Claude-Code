"""Die Inhalte der Akademie: Kurse, Module, Lektionen (L-25).

**Was hier stand und wohin es ging, 23.08.2026.** Diese Datei hatte 1.109
Zeilen und zehn Abschnitte. Vier davon sind ausgezogen, jeder nach seiner
Zustaendigkeit — nicht nach Groesse:

- `academy_gemeinsam.py` — die zwoelf Helfer, die alle brauchen
- `academy_fortschritt.py` — Lektionsfortschritt, Quiz, eigener Stand
- `academy_zertifikate.py` — ausstellen und nachweisen
- `academy_zuweisung.py` — wer bekommt welchen Kurs, dazu der Seed

Geblieben ist, was den **Bestand** verwaltet: Kurse, Module, Lektionen.

**Reiner Umzug.** Keine Route wurde veraendert, umbenannt oder
zusammengefasst; die Pfade sind dieselben.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import (
    get_db, AcademyCourse, AcademyChecklistItem, AcademyModule, AcademyLesson,
    AcademyLessonProgress, AcademyProgress, AcademyCertificate, AcademyQuizQuestion,
    AcademyCustomerAccess,
    AcademyModuleAccess,
    User,
)
from routers.auth_router import get_current_user, require_admin
from datetime import datetime
import json
import logging
import secrets
import string

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/academy', tags=['academy'])

from routers.academy_gemeinsam import (
    _ist_kunde, _freigeschaltete_kurse, _sichtbare_module, _kursumfang,
    _serialize_course, _serialize_module, _serialize_lesson, _progress_summary,
)


# ── Courses ───────────────────────────────────────────────

@router.get('/courses')
def list_courses(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Liste aller Kurse gefiltert nach Rolle und Zielgruppe."""
    role = current_user.role

    q = db.query(AcademyCourse)

    if role == 'kunde':
        q = q.filter(
            AcademyCourse.target_audience.in_(['customer', 'both']),
            AcademyCourse.is_published.is_(True),
        )
    elif role in ('admin', 'superadmin'):
        pass  # Admin/Superadmin sieht alle Kurse inkl. Entwürfe, keine Filterung
    else:
        # nutzer, auditor, und alle anderen internen Rollen
        q = q.filter(
            AcademyCourse.target_audience.in_(['employee', 'both']),
            AcademyCourse.is_published.is_(True),
        )

    courses = q.order_by(AcademyCourse.sort_order, AcademyCourse.id).all()

    # Gesperrte Kurse nur fuer ausdruecklich Zugewiesene. Bis zum 19.08.2026
    # fragte diese Liste `AcademyCustomerAccess` gar nicht ab — die Zuweisung
    # war eine Tabelle ohne Wirkung.
    if role == 'kunde':
        frei = _freigeschaltete_kurse(db, current_user)
        courses = [c for c in courses if not c.is_locked or c.id in frei]

    result = []
    for c in courses:
        data = _serialize_course(c)
        data.update(_kursumfang(db, c.id))
        data['progress'] = _progress_summary(c.id, current_user.id, db)
        result.append(data)
    return result


@router.get('/courses/{course_id}')
def get_course(course_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Kursdetails mit Modulen und Lektionen."""
    course = db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first()
    if not course:
        raise HTTPException(404, 'Kurs nicht gefunden')

    # Ein gesperrter Kurs ohne Zuweisung ist fuer den Kunden nicht vorhanden.
    # 404 statt 403: Ob es ihn gibt, geht ihn nichts an.
    if (_ist_kunde(current_user) and course.is_locked
            and course.id not in _freigeschaltete_kurse(db, current_user)):
        raise HTTPException(404, 'Kurs nicht gefunden')

    modules = _sichtbare_module(db, course_id, current_user)
    modules_data = []
    for m in modules:
        lessons = (
            db.query(AcademyLesson)
            .filter(AcademyLesson.module_id == m.id)
            .order_by(AcademyLesson.position, AcademyLesson.sort_order, AcademyLesson.id)
            .all()
        )
        mod = _serialize_module(m)
        mod['lessons'] = [_serialize_lesson(l) for l in lessons]
        modules_data.append(mod)

    checklist_items = (
        db.query(AcademyChecklistItem)
        .filter(AcademyChecklistItem.course_id == course_id)
        .order_by(AcademyChecklistItem.sort_order, AcademyChecklistItem.id)
        .all()
    )

    result = _serialize_course(course)
    result.update(_kursumfang(db, course_id))
    result['modules'] = modules_data
    result['checklist_items'] = [{'id': i.id, 'label': i.label, 'sort_order': i.sort_order} for i in checklist_items]
    result['progress'] = _progress_summary(course_id, current_user.id, db)
    return result


@router.post('/courses')
def create_course(data: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Kurs erstellen (Admin)."""
    course = AcademyCourse(
        title=data.get('title', ''),
        description=data.get('description', ''),
        thumbnail_url=data.get('thumbnail_url', ''),
        is_published=data.get('is_published', False),
        target_audience=data.get('target_audience', 'both'),
        category=data.get('category', ''),
        category_color=data.get('category_color', 'primary'),
        audience=data.get('audience', 'employee'),
        formats=json.dumps(data.get('formats', ['text']), ensure_ascii=False),
        linear_progress=data.get('linear_progress', False),
        sort_order=data.get('sort_order', 0),
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    for i, label in enumerate(data.get('checklist_items', [])):
        db.add(AcademyChecklistItem(course_id=course.id, label=label, sort_order=i))
    if data.get('checklist_items'):
        db.commit()
    return _serialize_course(course)


@router.put('/courses/{course_id}')
def update_course(course_id: int, data: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Kurs bearbeiten (Admin)."""
    course = db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first()
    if not course:
        raise HTTPException(404, 'Kurs nicht gefunden')
    for key in ['title', 'description', 'thumbnail_url', 'is_published', 'target_audience',
                'category', 'category_color', 'audience', 'linear_progress', 'sort_order']:
        if key in data:
            setattr(course, key, data[key])
    if 'formats' in data:
        course.formats = json.dumps(data['formats'], ensure_ascii=False) if isinstance(data['formats'], list) else data['formats']
    if 'checklist_items' in data:
        db.query(AcademyChecklistItem).filter(AcademyChecklistItem.course_id == course_id).delete()
        for i, label in enumerate(data['checklist_items']):
            db.add(AcademyChecklistItem(course_id=course_id, label=label, sort_order=i))
    db.commit()
    db.refresh(course)
    return _serialize_course(course)


@router.delete('/courses/{course_id}')
def delete_course(course_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Kurs löschen (Admin)."""
    course = db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first()
    if not course:
        raise HTTPException(404, 'Kurs nicht gefunden')
    db.delete(course)
    db.commit()
    return {'success': True}


# ── Modules ───────────────────────────────────────────────

@router.get('/modules/{module_id}')
def get_module(module_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = db.query(AcademyModule).filter(AcademyModule.id == module_id).first()
    if not m:
        raise HTTPException(404, 'Modul nicht gefunden')
    return _serialize_module(m)


@router.get('/courses/{course_id}/modules')
def list_modules(course_id: int, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    # Zwei Wege fuehren zu denselben Modulen — der Kursdetail-Aufruf und
    # dieser. Beide muessen filtern, sonst ist die Sperre einen Aufruf weit weg.
    modules = _sichtbare_module(db, course_id, current_user)
    return [_serialize_module(m) for m in modules]


@router.post('/modules')
def create_module(data: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Modul erstellen (Admin). Body: {course_id, title, position?, is_locked?}"""
    course_id = data.get('course_id')
    if not course_id or not db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first():
        raise HTTPException(404, 'Kurs nicht gefunden')
    m = AcademyModule(
        course_id=course_id,
        title=data.get('title', ''),
        position=data.get('position', 0),
        is_locked=data.get('is_locked', False),
        sort_order=data.get('sort_order', data.get('position', 0)),
        description=data.get('description', ''),
        thumbnail_url=data.get('thumbnail_url', ''),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _serialize_module(m)


@router.post('/courses/{course_id}/modules')
def create_module_for_course(course_id: int, data: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Modul für Kurs erstellen (Admin)."""
    if not db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first():
        raise HTTPException(404, 'Kurs nicht gefunden')
    m = AcademyModule(
        course_id=course_id,
        title=data.get('title', ''),
        position=data.get('position', data.get('sort_order', 0)),
        is_locked=data.get('is_locked', False),
        sort_order=data.get('sort_order', data.get('position', 0)),
        description=data.get('description', ''),
        thumbnail_url=data.get('thumbnail_url', ''),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _serialize_module(m)


@router.put('/modules/{module_id}')
def update_module(module_id: int, data: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Modul bearbeiten (Admin)."""
    m = db.query(AcademyModule).filter(AcademyModule.id == module_id).first()
    if not m:
        raise HTTPException(404, 'Modul nicht gefunden')
    for key in ['title', 'position', 'is_locked', 'sort_order',
                'description', 'thumbnail_url']:
        if key in data:
            setattr(m, key, data[key])
    db.commit()
    db.refresh(m)
    return _serialize_module(m)


@router.delete('/modules/{module_id}')
def delete_module(module_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    m = db.query(AcademyModule).filter(AcademyModule.id == module_id).first()
    if not m:
        raise HTTPException(404, 'Modul nicht gefunden')
    db.delete(m)
    db.commit()
    return {'success': True}


@router.put('/courses/{course_id}/modules/reorder')
def reorder_modules(course_id: int, data: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    for item in data.get('order', []):
        m = db.query(AcademyModule).filter(
            AcademyModule.id == item['id'], AcademyModule.course_id == course_id
        ).first()
        if m:
            m.position = item.get('position', item.get('sort_order', 0))
            m.sort_order = m.position
    db.commit()
    return {'success': True}


# ── Lessons ───────────────────────────────────────────────

@router.get('/lessons/{lesson_id}')
def get_lesson(lesson_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    l = db.query(AcademyLesson).filter(AcademyLesson.id == lesson_id).first()
    if not l:
        raise HTTPException(404, 'Lektion nicht gefunden')
    return _serialize_lesson(l)


@router.get('/modules/{module_id}/lessons')
def list_lessons(module_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    lessons = (
        db.query(AcademyLesson)
        .filter(AcademyLesson.module_id == module_id)
        .order_by(AcademyLesson.position, AcademyLesson.sort_order, AcademyLesson.id)
        .all()
    )
    return [_serialize_lesson(l) for l in lessons]


@router.post('/lessons')
def create_lesson(data: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Lektion erstellen (Admin). Body: {module_id, title, type?, content_text?, content_url?, ...}"""
    module_id = data.get('module_id')
    if not module_id or not db.query(AcademyModule).filter(AcademyModule.id == module_id).first():
        raise HTTPException(404, 'Modul nicht gefunden')
    checklist = data.get('checklist_items', [])
    l = AcademyLesson(
        module_id=module_id,
        title=data.get('title', ''),
        position=data.get('position', data.get('sort_order', 0)),
        type=data.get('type', 'text'),
        content_text=data.get('content_text', ''),
        content_url=data.get('content_url', ''),
        video_url=data.get('video_url', ''),
        file_url=data.get('file_url', ''),
        duration_minutes=data.get('duration_minutes', 0),
        sort_order=data.get('sort_order', data.get('position', 0)),
        checklist_items_json=json.dumps(checklist, ensure_ascii=False),
    )
    db.add(l)
    db.commit()
    db.refresh(l)
    return _serialize_lesson(l)


@router.post('/modules/{module_id}/lessons')
def create_lesson_for_module(module_id: int, data: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Lektion für Modul erstellen (Admin)."""
    if not db.query(AcademyModule).filter(AcademyModule.id == module_id).first():
        raise HTTPException(404, 'Modul nicht gefunden')
    checklist = data.get('checklist_items', [])
    l = AcademyLesson(
        module_id=module_id,
        title=data.get('title', ''),
        position=data.get('position', data.get('sort_order', 0)),
        type=data.get('type', 'text'),
        content_text=data.get('content_text', ''),
        content_url=data.get('content_url', ''),
        video_url=data.get('video_url', ''),
        file_url=data.get('file_url', ''),
        duration_minutes=data.get('duration_minutes', 0),
        sort_order=data.get('sort_order', data.get('position', 0)),
        checklist_items_json=json.dumps(checklist, ensure_ascii=False),
    )
    db.add(l)
    db.commit()
    db.refresh(l)
    return _serialize_lesson(l)


@router.put('/lessons/{lesson_id}')
def update_lesson(lesson_id: int, data: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Lektion bearbeiten (Admin)."""
    l = db.query(AcademyLesson).filter(AcademyLesson.id == lesson_id).first()
    if not l:
        raise HTTPException(404, 'Lektion nicht gefunden')
    for key in ['title', 'position', 'type', 'content_text', 'content_url',
                'video_url', 'file_url', 'duration_minutes', 'sort_order']:
        if key in data:
            setattr(l, key, data[key])
    if 'checklist_items' in data:
        l.checklist_items_json = json.dumps(data['checklist_items'], ensure_ascii=False)
    db.commit()
    db.refresh(l)
    return _serialize_lesson(l)


@router.delete('/lessons/{lesson_id}')
def delete_lesson(lesson_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    l = db.query(AcademyLesson).filter(AcademyLesson.id == lesson_id).first()
    if not l:
        raise HTTPException(404, 'Lektion nicht gefunden')
    db.delete(l)
    db.commit()
    return {'success': True}
