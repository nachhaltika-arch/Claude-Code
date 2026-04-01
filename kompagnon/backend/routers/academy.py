from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db, AcademyCourse, AcademyChecklistItem, AcademyModule, AcademyLesson, AcademyLessonProgress
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/academy', tags=['academy'])


@router.get('/courses')
def list_courses(db: Session = Depends(get_db)):
    """List all courses ordered by sort_order."""
    courses = db.query(AcademyCourse).order_by(AcademyCourse.sort_order, AcademyCourse.id).all()
    return [_serialize_course(c) for c in courses]


@router.get('/courses/{course_id}')
def get_course(course_id: int, db: Session = Depends(get_db)):
    """Get single course with checklist items."""
    course = db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first()
    if not course:
        raise HTTPException(404, "Kurs nicht gefunden")
    items = db.query(AcademyChecklistItem).filter(
        AcademyChecklistItem.course_id == course_id
    ).order_by(AcademyChecklistItem.sort_order, AcademyChecklistItem.id).all()
    result = _serialize_course(course)
    result['checklist_items'] = [{'id': it.id, 'label': it.label, 'sort_order': it.sort_order} for it in items]
    return result


@router.post('/courses')
def create_course(data: dict, db: Session = Depends(get_db)):
    """Create a new course (admin only)."""
    course = AcademyCourse(
        title=data.get('title', ''),
        description=data.get('description', ''),
        category=data.get('category', ''),
        category_color=data.get('category_color', 'primary'),
        audience=data.get('audience', 'employee'),
        formats=json.dumps(data.get('formats', ['text']), ensure_ascii=False),
        content_text=data.get('content_text', ''),
        video_url=data.get('video_url', ''),
        sort_order=data.get('sort_order', 0),
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    # Add checklist items if provided
    for i, label in enumerate(data.get('checklist_items', [])):
        item = AcademyChecklistItem(course_id=course.id, label=label, sort_order=i)
        db.add(item)
    if data.get('checklist_items'):
        db.commit()
    return _serialize_course(course)


@router.put('/courses/{course_id}')
def update_course(course_id: int, data: dict, db: Session = Depends(get_db)):
    """Update a course (admin only)."""
    course = db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first()
    if not course:
        raise HTTPException(404, "Kurs nicht gefunden")
    for key in ['title', 'description', 'category', 'category_color', 'audience', 'content_text', 'video_url', 'sort_order']:
        if key in data:
            setattr(course, key, data[key])
    if 'formats' in data:
        course.formats = json.dumps(data['formats'], ensure_ascii=False) if isinstance(data['formats'], list) else data['formats']
    # Replace checklist items if provided
    if 'checklist_items' in data:
        db.query(AcademyChecklistItem).filter(AcademyChecklistItem.course_id == course_id).delete()
        for i, label in enumerate(data['checklist_items']):
            db.add(AcademyChecklistItem(course_id=course_id, label=label, sort_order=i))
    db.commit()
    db.refresh(course)
    return _serialize_course(course)


@router.delete('/courses/{course_id}')
def delete_course(course_id: int, db: Session = Depends(get_db)):
    """Delete a course (admin only)."""
    course = db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first()
    if not course:
        raise HTTPException(404, "Kurs nicht gefunden")
    db.delete(course)
    db.commit()
    return {'success': True}


@router.put('/courses/reorder')
def reorder_courses(data: dict, db: Session = Depends(get_db)):
    """Reorder courses. data = { "order": [{"id": 1, "sort_order": 0}, ...] }"""
    for item in data.get('order', []):
        course = db.query(AcademyCourse).filter(AcademyCourse.id == item['id']).first()
        if course:
            course.sort_order = item['sort_order']
    db.commit()
    return {'success': True}


def _serialize_course(c):
    try:
        formats = json.loads(c.formats) if c.formats else ['text']
    except (json.JSONDecodeError, TypeError):
        formats = ['text']
    return {
        'id': c.id,
        'title': c.title or '',
        'description': c.description or '',
        'category': c.category or '',
        'category_color': c.category_color or 'primary',
        'audience': c.audience or 'employee',
        'formats': formats,
        'content_text': c.content_text or '',
        'video_url': c.video_url or '',
        'sort_order': c.sort_order or 0,
        'created_at': str(c.created_at)[:10] if c.created_at else '',
    }


def seed_academy_courses(db: Session):
    """Seed 11 default courses if table is empty."""
    if db.query(AcademyCourse).count() > 0:
        return
    logger.info("Seeding academy courses...")
    courses = [
        ('Der KOMPAGNON Akquise-Prozess', 'Vom Erstkontakt bis zum Auftrag — der komplette Vertriebsprozess.', 'Akquise', 'primary', 'employee', ['text','video','checklist'],
         ['Lead-Quellen identifizieren', 'Erstkontakt vorbereiten', 'Audit als Türöffner nutzen', 'Angebot erstellen und nachfassen', 'Auftrag abschließen']),
        ('Website-Audit durchführen', 'Wie Sie einen Homepage Standard Audit starten und präsentieren.', 'Audit', 'warning', 'employee', ['text','video'],
         ['Audit-Tool öffnen und URL eingeben', 'Ergebnisse interpretieren', 'Schwachstellen priorisieren', 'Kundenpräsentation vorbereiten', 'Handlungsempfehlungen ableiten']),
        ('Die 7 Projektphasen', 'Von Akquisition über Briefing bis Post-Launch — jede Phase im Detail.', 'Projekt', 'success', 'employee', ['text','checklist'],
         ['Phase 1: Akquisition verstehen', 'Phase 2-3: Briefing & Content planen', 'Phase 4-5: Technik & QA durchführen', 'Phase 6: Go-Live vorbereiten', 'Phase 7: Post-Launch betreuen']),
        ('KOMPAGNON-System bedienen', 'Dashboard, Pipeline, Domain-Import und Kundenkartei nutzen.', 'Tools', 'info', 'employee', ['text','video'],
         ['Dashboard und KPIs verstehen', 'Vertriebspipeline bedienen', 'Domain-Import durchführen', 'Kundenkartei pflegen', 'Audit-Tool nutzen']),
        ('Kaltakquise & Anschreiben', 'Vorlagen und Best Practices für telefonische und schriftliche Akquise.', 'Vertrieb', 'danger', 'employee', ['text','checklist'],
         ['Zielgruppe definieren', 'Anschreiben-Vorlage erstellen', 'Telefonleitfaden vorbereiten', 'Follow-up Strategie planen', 'Erfolgsmessung einrichten']),
        ('Qualitätsstandards & Übergabe', 'Checklisten für QA, Kundenübergabe und Go-Live.', 'Qualität', 'secondary', 'employee', ['text','checklist'],
         ['QA-Checkliste durchgehen', 'Cross-Browser Testing', 'Mobile Responsiveness prüfen', 'Rechtliche Inhalte verifizieren', 'Kundenübergabe dokumentieren']),
        ('So läuft Ihr Website-Projekt ab', 'Überblick über alle Schritte von Beauftragung bis fertige Website.', 'Start', 'primary', 'customer', ['text','video'],
         ['Beauftragung und Zahlung', 'Briefing-Gespräch führen', 'Zwischenpräsentation prüfen', 'Feedback und Korrekturen', 'Go-Live und Einweisung']),
        ('Was wir von Ihnen brauchen', 'Logo, Texte, Fotos, Zugangsdaten — was wir benötigen.', 'Vorbereitung', 'info', 'customer', ['text','checklist'],
         ['Logo in Vektorformat bereitstellen', 'Texte und Inhalte liefern', 'Fotos in hoher Auflösung', 'Zugangsdaten sammeln', 'Ansprechpartner benennen']),
        ('Ihren Audit-Bericht verstehen', 'Was die Scores bedeuten und wo Handlungsbedarf besteht.', 'Audit', 'warning', 'customer', ['text'],
         ['Gesamtscore einordnen', 'Kategorien verstehen', 'Kritische Punkte identifizieren', 'Verbesserungspotenzial erkennen', 'Nächste Schritte planen']),
        ('Ihre neue Website pflegen', 'WordPress-Einführung: Texte ändern, Bilder tauschen, Seiten erstellen.', 'Website', 'success', 'customer', ['text','video'],
         ['WordPress-Login finden', 'Texte bearbeiten', 'Bilder austauschen', 'Neue Seite erstellen', 'Backup-Routine verstehen']),
        ('Gefunden werden — SEO & Google Business', 'Website bei Google sichtbar machen und Google Business nutzen.', 'SEO', 'secondary', 'customer', ['text'],
         ['Google Business Profil einrichten', 'Bewertungen sammeln', 'Keywords verstehen', 'Meta-Daten prüfen', 'Lokale Sichtbarkeit messen']),
    ]
    for i, (title, desc, cat, color, aud, fmts, items) in enumerate(courses):
        c = AcademyCourse(title=title, description=desc, category=cat, category_color=color,
                          audience=aud, formats=json.dumps(fmts), sort_order=i)
        db.add(c)
        db.flush()
        for j, label in enumerate(items):
            db.add(AcademyChecklistItem(course_id=c.id, label=label, sort_order=j))
    db.commit()
    logger.info(f"✓ {len(courses)} Academy-Kurse angelegt")


# ── Module CRUD ──────────────────────────────────────────

@router.get('/modules/{module_id}')
def get_module(module_id: int, db: Session = Depends(get_db)):
    m = db.query(AcademyModule).filter(AcademyModule.id == module_id).first()
    if not m:
        raise HTTPException(404, "Modul nicht gefunden")
    return {'id': m.id, 'course_id': m.course_id, 'title': m.title or '', 'sort_order': m.sort_order or 0}


@router.get('/courses/{course_id}/modules')
def list_modules(course_id: int, db: Session = Depends(get_db)):
    modules = db.query(AcademyModule).filter(AcademyModule.course_id == course_id).order_by(AcademyModule.sort_order, AcademyModule.id).all()
    return [{'id': m.id, 'course_id': m.course_id, 'title': m.title or '', 'sort_order': m.sort_order or 0} for m in modules]


@router.post('/courses/{course_id}/modules')
def create_module(course_id: int, data: dict, db: Session = Depends(get_db)):
    course = db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first()
    if not course:
        raise HTTPException(404, "Kurs nicht gefunden")
    m = AcademyModule(course_id=course_id, title=data.get('title', ''), sort_order=data.get('sort_order', 0))
    db.add(m)
    db.commit()
    db.refresh(m)
    return {'id': m.id, 'course_id': m.course_id, 'title': m.title, 'sort_order': m.sort_order}


@router.put('/modules/{module_id}')
def update_module(module_id: int, data: dict, db: Session = Depends(get_db)):
    m = db.query(AcademyModule).filter(AcademyModule.id == module_id).first()
    if not m:
        raise HTTPException(404, "Modul nicht gefunden")
    if 'title' in data:
        m.title = data['title']
    if 'sort_order' in data:
        m.sort_order = data['sort_order']
    db.commit()
    db.refresh(m)
    return {'id': m.id, 'course_id': m.course_id, 'title': m.title, 'sort_order': m.sort_order}


@router.delete('/modules/{module_id}')
def delete_module(module_id: int, db: Session = Depends(get_db)):
    m = db.query(AcademyModule).filter(AcademyModule.id == module_id).first()
    if not m:
        raise HTTPException(404, "Modul nicht gefunden")
    db.delete(m)
    db.commit()
    return {'success': True}


@router.put('/courses/{course_id}/modules/reorder')
def reorder_modules(course_id: int, data: dict, db: Session = Depends(get_db)):
    for item in data.get('order', []):
        m = db.query(AcademyModule).filter(AcademyModule.id == item['id'], AcademyModule.course_id == course_id).first()
        if m:
            m.sort_order = item['sort_order']
    db.commit()
    return {'success': True}


# ── Lesson CRUD ──────────────────────────────────────────

@router.get('/lessons/{lesson_id}')
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    l = db.query(AcademyLesson).filter(AcademyLesson.id == lesson_id).first()
    if not l:
        raise HTTPException(404, "Lektion nicht gefunden")
    return _serialize_lesson(l)


def _serialize_lesson(l):
    try:
        checklist = json.loads(l.checklist_items_json) if getattr(l, 'checklist_items_json', None) else []
    except (json.JSONDecodeError, TypeError):
        checklist = []
    return {
        'id': l.id, 'module_id': l.module_id, 'title': l.title or '',
        'content_text': l.content_text or '', 'video_url': l.video_url or '',
        'file_url': l.file_url or '', 'sort_order': l.sort_order or 0,
        'checklist_items': checklist,
    }


@router.get('/modules/{module_id}/lessons')
def list_lessons(module_id: int, db: Session = Depends(get_db)):
    lessons = db.query(AcademyLesson).filter(AcademyLesson.module_id == module_id).order_by(AcademyLesson.sort_order, AcademyLesson.id).all()
    return [_serialize_lesson(l) for l in lessons]


@router.post('/modules/{module_id}/lessons')
def create_lesson(module_id: int, data: dict, db: Session = Depends(get_db)):
    m = db.query(AcademyModule).filter(AcademyModule.id == module_id).first()
    if not m:
        raise HTTPException(404, "Modul nicht gefunden")
    checklist = data.get('checklist_items', [])
    l = AcademyLesson(
        module_id=module_id, title=data.get('title', ''), content_text=data.get('content_text', ''),
        video_url=data.get('video_url', ''), file_url=data.get('file_url', ''),
        sort_order=data.get('sort_order', 0),
        checklist_items_json=json.dumps(checklist, ensure_ascii=False),
    )
    db.add(l)
    db.commit()
    db.refresh(l)
    return _serialize_lesson(l)


@router.put('/lessons/{lesson_id}')
def update_lesson(lesson_id: int, data: dict, db: Session = Depends(get_db)):
    l = db.query(AcademyLesson).filter(AcademyLesson.id == lesson_id).first()
    if not l:
        raise HTTPException(404, "Lektion nicht gefunden")
    for key in ['title', 'content_text', 'video_url', 'file_url', 'sort_order']:
        if key in data:
            setattr(l, key, data[key])
    if 'checklist_items' in data:
        l.checklist_items_json = json.dumps(data['checklist_items'], ensure_ascii=False)
    db.commit()
    db.refresh(l)
    return _serialize_lesson(l)


@router.delete('/lessons/{lesson_id}')
def delete_lesson(lesson_id: int, db: Session = Depends(get_db)):
    l = db.query(AcademyLesson).filter(AcademyLesson.id == lesson_id).first()
    if not l:
        raise HTTPException(404, "Lektion nicht gefunden")
    db.delete(l)
    db.commit()
    return {'success': True}


# ── Lesson Progress ──────────────────────────────────────

@router.post('/lessons/{lesson_id}/complete')
def complete_lesson(lesson_id: int, data: dict, db: Session = Depends(get_db)):
    """Mark a lesson as completed for the current user."""
    user_id = data.get('user_id')
    if not user_id:
        raise HTTPException(400, "user_id fehlt")
    l = db.query(AcademyLesson).filter(AcademyLesson.id == lesson_id).first()
    if not l:
        raise HTTPException(404, "Lektion nicht gefunden")
    existing = db.query(AcademyLessonProgress).filter(
        AcademyLessonProgress.user_id == user_id, AcademyLessonProgress.lesson_id == lesson_id
    ).first()
    if existing:
        existing.completed = not existing.completed
        existing.completed_at = datetime.utcnow() if existing.completed else None
    else:
        existing = AcademyLessonProgress(user_id=user_id, lesson_id=lesson_id, completed=True, completed_at=datetime.utcnow())
        db.add(existing)
    db.commit()
    return {'lesson_id': lesson_id, 'completed': existing.completed, 'completed_at': str(existing.completed_at)[:16] if existing.completed_at else None}


@router.get('/progress/all')
def get_all_courses_progress(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get progress summary for ALL courses in a single query. Returns {course_id: {total, completed, pct}}."""
    if not user_id:
        return {}
    # One query: all lessons with module → course join
    from sqlalchemy import func
    rows = (
        db.query(AcademyLesson.id, AcademyModule.course_id)
        .join(AcademyModule, AcademyLesson.module_id == AcademyModule.id)
        .all()
    )
    if not rows:
        return {}
    lesson_to_course = {r[0]: r[1] for r in rows}
    lesson_ids = list(lesson_to_course.keys())
    # One query: completed lessons for this user
    completed = db.query(AcademyLessonProgress.lesson_id).filter(
        AcademyLessonProgress.user_id == user_id,
        AcademyLessonProgress.lesson_id.in_(lesson_ids),
        AcademyLessonProgress.completed == True,
    ).all()
    completed_ids = {r[0] for r in completed}
    # Aggregate per course
    totals: dict = {}
    dones: dict = {}
    for lesson_id, course_id in lesson_to_course.items():
        totals[course_id] = totals.get(course_id, 0) + 1
        if lesson_id in completed_ids:
            dones[course_id] = dones.get(course_id, 0) + 1
    result = {}
    for course_id, total in totals.items():
        done = dones.get(course_id, 0)
        result[course_id] = {
            'total_lessons': total,
            'completed': done,
            'progress_pct': round((done / total) * 100) if total > 0 else 0,
        }
    return result


@router.get('/courses/{course_id}/progress')
def get_course_progress(course_id: int, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get lesson progress for all lessons in a course, optionally filtered by user_id query param."""
    # Get all modules for this course
    modules = db.query(AcademyModule).filter(AcademyModule.course_id == course_id).all()
    module_ids = [m.id for m in modules]
    if not module_ids:
        return {'total_lessons': 0, 'completed': 0, 'progress_pct': 0, 'lessons': []}
    # Get all lessons
    lessons = db.query(AcademyLesson).filter(AcademyLesson.module_id.in_(module_ids)).order_by(AcademyLesson.sort_order).all()
    lesson_ids = [l.id for l in lessons]
    # Get progress (filtered by user_id if provided)
    q = db.query(AcademyLessonProgress).filter(AcademyLessonProgress.lesson_id.in_(lesson_ids))
    if user_id is not None:
        q = q.filter(AcademyLessonProgress.user_id == user_id)
    progress = q.all()
    progress_map = {p.lesson_id: p for p in progress}
    result = []
    for l in lessons:
        p = progress_map.get(l.id)
        result.append({
            'lesson_id': l.id, 'lesson_title': l.title, 'module_id': l.module_id,
            'completed': p.completed if p else False,
            'completed_at': str(p.completed_at)[:16] if p and p.completed_at else None,
        })
    completed_count = sum(1 for r in result if r['completed'])
    total = len(result)
    return {
        'total_lessons': total,
        'completed': completed_count,
        'progress_pct': round((completed_count / total) * 100) if total > 0 else 0,
        'lessons': result,
    }
