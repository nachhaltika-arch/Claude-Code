from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import (
    get_db, AcademyCourse, AcademyChecklistItem, AcademyModule, AcademyLesson,
    AcademyLessonProgress, AcademyProgress, AcademyCertificate,
)
from routers.auth_router import get_current_user, require_admin
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/academy', tags=['academy'])


# ── Helpers ───────────────────────────────────────────────

def _serialize_course(c):
    try:
        formats = json.loads(c.formats) if c.formats else ['text']
    except (json.JSONDecodeError, TypeError):
        formats = ['text']
    return {
        'id': c.id,
        'title': c.title or '',
        'description': c.description or '',
        'thumbnail_url': c.thumbnail_url or '',
        'is_published': bool(c.is_published),
        'target_audience': c.target_audience or 'both',
        'category': c.category or '',
        'category_color': c.category_color or 'primary',
        'audience': c.audience or 'employee',
        'formats': formats,
        'linear_progress': bool(c.linear_progress),
        'sort_order': c.sort_order or 0,
        'created_at': str(c.created_at)[:10] if c.created_at else '',
    }


def _serialize_module(m):
    return {
        'id': m.id,
        'course_id': m.course_id,
        'title': m.title or '',
        'position': m.position or 0,
        'is_locked': bool(m.is_locked),
        'sort_order': m.sort_order or 0,
    }


def _serialize_lesson(l):
    try:
        checklist = json.loads(l.checklist_items_json) if getattr(l, 'checklist_items_json', None) else []
    except (json.JSONDecodeError, TypeError):
        checklist = []
    return {
        'id': l.id,
        'module_id': l.module_id,
        'title': l.title or '',
        'position': l.position or 0,
        'type': l.type or 'text',
        'content_text': l.content_text or '',
        'content_url': l.content_url or '',
        'video_url': l.video_url or '',
        'file_url': l.file_url or '',
        'duration_minutes': l.duration_minutes or 0,
        'sort_order': l.sort_order or 0,
        'checklist_items': checklist,
    }


def _progress_summary(course_id: int, user_id: int, db: Session) -> dict:
    """Return {total_lessons, completed, progress_pct} for one course."""
    rows = (
        db.query(AcademyLesson.id)
        .join(AcademyModule, AcademyLesson.module_id == AcademyModule.id)
        .filter(AcademyModule.course_id == course_id)
        .all()
    )
    lesson_ids = [r[0] for r in rows]
    total = len(lesson_ids)
    if total == 0:
        return {'total_lessons': 0, 'completed': 0, 'progress_pct': 0}
    completed = db.query(AcademyProgress).filter(
        AcademyProgress.user_id == user_id,
        AcademyProgress.lesson_id.in_(lesson_ids),
        AcademyProgress.completed_at.isnot(None),
    ).count()
    return {
        'total_lessons': total,
        'completed': completed,
        'progress_pct': round((completed / total) * 100) if total else 0,
    }


# ── Courses ───────────────────────────────────────────────

@router.get('/courses')
def list_courses(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Liste aller Kurse mit Fortschritt des aktuellen Users."""
    courses = db.query(AcademyCourse).order_by(AcademyCourse.sort_order, AcademyCourse.id).all()
    result = []
    for c in courses:
        data = _serialize_course(c)
        data['progress'] = _progress_summary(c.id, current_user.id, db)
        result.append(data)
    return result


@router.get('/courses/{course_id}')
def get_course(course_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Kursdetails mit Modulen und Lektionen."""
    course = db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first()
    if not course:
        raise HTTPException(404, 'Kurs nicht gefunden')

    modules = (
        db.query(AcademyModule)
        .filter(AcademyModule.course_id == course_id)
        .order_by(AcademyModule.position, AcademyModule.sort_order, AcademyModule.id)
        .all()
    )
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
def list_modules(course_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    modules = (
        db.query(AcademyModule)
        .filter(AcademyModule.course_id == course_id)
        .order_by(AcademyModule.position, AcademyModule.sort_order, AcademyModule.id)
        .all()
    )
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
    for key in ['title', 'position', 'is_locked', 'sort_order']:
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


# ── Progress ──────────────────────────────────────────────

@router.post('/lessons/{lesson_id}/complete')
def complete_lesson(lesson_id: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Lektion als abgeschlossen markieren (toggle)."""
    if not db.query(AcademyLesson).filter(AcademyLesson.id == lesson_id).first():
        raise HTTPException(404, 'Lektion nicht gefunden')
    user_id = current_user.id
    existing = db.query(AcademyProgress).filter(
        AcademyProgress.user_id == user_id,
        AcademyProgress.lesson_id == lesson_id,
    ).first()
    if existing:
        if existing.completed_at:
            existing.completed_at = None
        else:
            existing.completed_at = datetime.utcnow()
            existing.score = data.get('score')
    else:
        existing = AcademyProgress(
            user_id=user_id, lesson_id=lesson_id,
            completed_at=datetime.utcnow(), score=data.get('score'),
        )
        db.add(existing)
    db.commit()
    completed = existing.completed_at is not None
    return {
        'lesson_id': lesson_id,
        'completed': completed,
        'completed_at': str(existing.completed_at)[:16] if existing.completed_at else None,
        'score': existing.score,
    }


@router.get('/courses/{course_id}/progress')
def get_course_progress(course_id: int, user_id: Optional[int] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Lernfortschritt für alle Lektionen eines Kurses."""
    uid = user_id or current_user.id
    modules = db.query(AcademyModule).filter(AcademyModule.course_id == course_id).all()
    module_ids = [m.id for m in modules]
    if not module_ids:
        return {'total_lessons': 0, 'completed': 0, 'progress_pct': 0, 'lessons': []}
    lessons = (
        db.query(AcademyLesson)
        .filter(AcademyLesson.module_id.in_(module_ids))
        .order_by(AcademyLesson.position, AcademyLesson.sort_order)
        .all()
    )
    lesson_ids = [l.id for l in lessons]
    progress_rows = db.query(AcademyProgress).filter(
        AcademyProgress.lesson_id.in_(lesson_ids),
        AcademyProgress.user_id == uid,
    ).all()
    progress_map = {p.lesson_id: p for p in progress_rows}
    result = []
    for l in lessons:
        p = progress_map.get(l.id)
        result.append({
            'lesson_id': l.id, 'lesson_title': l.title, 'module_id': l.module_id,
            'completed': p.completed_at is not None if p else False,
            'completed_at': str(p.completed_at)[:16] if p and p.completed_at else None,
            'score': p.score if p else None,
        })
    completed_count = sum(1 for r in result if r['completed'])
    total = len(result)
    return {
        'total_lessons': total,
        'completed': completed_count,
        'progress_pct': round((completed_count / total) * 100) if total else 0,
        'lessons': result,
    }


@router.get('/progress/all')
def get_all_courses_progress(user_id: Optional[int] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Fortschritt für alle Kurse in einer Query (für Akademie-Übersicht)."""
    uid = user_id or current_user.id
    rows = (
        db.query(AcademyLesson.id, AcademyModule.course_id)
        .join(AcademyModule, AcademyLesson.module_id == AcademyModule.id)
        .all()
    )
    if not rows:
        return {}
    lesson_to_course = {r[0]: r[1] for r in rows}
    lesson_ids = list(lesson_to_course.keys())
    completed_ids = {
        r[0] for r in db.query(AcademyProgress.lesson_id).filter(
            AcademyProgress.user_id == uid,
            AcademyProgress.lesson_id.in_(lesson_ids),
            AcademyProgress.completed_at.isnot(None),
        ).all()
    }
    totals: dict = {}
    dones: dict = {}
    for lesson_id, course_id in lesson_to_course.items():
        totals[course_id] = totals.get(course_id, 0) + 1
        if lesson_id in completed_ids:
            dones[course_id] = dones.get(course_id, 0) + 1
    return {
        course_id: {
            'total_lessons': total,
            'completed': dones.get(course_id, 0),
            'progress_pct': round((dones.get(course_id, 0) / total) * 100) if total else 0,
        }
        for course_id, total in totals.items()
    }


# ── Seed (internal) ───────────────────────────────────────

def seed_academy_courses(db: Session):
    """Seed default courses if table is empty."""
    if db.query(AcademyCourse).count() > 0:
        return
    logger.info('Seeding academy courses...')
    courses = [
        ('Der KOMPAGNON Akquise-Prozess', 'Vom Erstkontakt bis zum Auftrag.', 'Akquise', 'primary', 'employee', 'employee'),
        ('Website-Audit durchführen', 'Wie Sie einen Audit starten und präsentieren.', 'Audit', 'warning', 'employee', 'employee'),
        ('Die 7 Projektphasen', 'Von Akquisition bis Post-Launch.', 'Projekt', 'success', 'employee', 'employee'),
        ('So läuft Ihr Website-Projekt ab', 'Überblick für Kunden.', 'Start', 'primary', 'customer', 'customer'),
        ('Ihre neue Website pflegen', 'WordPress-Einführung.', 'Website', 'success', 'customer', 'customer'),
    ]
    for i, (title, desc, cat, color, aud, ta) in enumerate(courses):
        c = AcademyCourse(
            title=title, description=desc, category=cat, category_color=color,
            audience=aud, target_audience=ta, formats=json.dumps(['text']),
            sort_order=i, is_published=True,
        )
        db.add(c)
    db.commit()
    logger.info('✓ Academy-Kurse angelegt')
