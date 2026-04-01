from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, AcademyCourse, AcademyChecklistItem
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
