"""Wer bekommt welchen Kurs — Zuweisung durch den Innendienst (L-25).

**Warum eigene Datei, 23.08.2026.** Der Bereich mit der eigenen Geschichte:
Hier sitzt L-54, die zweideutige Kundenkennung. Das Kundenblatt rief diese
Endpunkte mit der **Betriebs**-Nummer, waehrend die Akademie sonst ueber die
**Benutzer**-Nummer fuehrt; seit dem 19.08. loest der Schreibpfad auf, und
`_kunde_user_id` ist die Stelle, an der das geschieht.

Der Seed steht mit hier, weil er dasselbe Thema hat: Bestand anlegen, damit
ueberhaupt etwas zuzuweisen ist. `main.py` importiert `seed_academy_courses`
weiterhin — der Name bleibt, nur die Datei wechselt.
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

from routers.academy_gemeinsam import _kunde_user_id, _progress_summary


# ── Seed (internal) ───────────────────────────────────────

def seed_academy_courses(db: Session):
    """Seed default courses if table is empty."""
    if db.query(AcademyCourse).count() > 0:
        return
    logger.info('Seeding academy courses...')
    courses = [
        ('Der KOMPAGNON Akquise-Prozess', 'Vom Erstkontakt bis zum Auftrag.', 'Akquise', 'primary', 'employee', 'employee'),
        ('Website-Audit durchführen', 'Wie Sie einen Audit starten und präsentieren.', 'Audit', 'warning', 'employee', 'employee'),
        ('Die 7 Projektphasen', 'Von Onboarding bis Post-Launch.', 'Projekt', 'success', 'employee', 'employee'),
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


# ── Customer Course Access (Admin only) ──────────────────

@router.get('/customer/{customer_id}/modules')
def get_customer_modules(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Welche gesperrten Module dieser Kunde freigeschaltet hat."""
    customer_id = _kunde_user_id(db, customer_id)
    zuweisungen = db.query(AcademyModuleAccess).filter(
        AcademyModuleAccess.customer_id == customer_id
    ).all()
    ergebnis = []
    for z in zuweisungen:
        modul = db.query(AcademyModule).filter(AcademyModule.id == z.module_id).first()
        if not modul:
            continue
        kurs = db.query(AcademyCourse).filter(
            AcademyCourse.id == modul.course_id).first()
        ergebnis.append({
            'id': z.id,
            'module_id': modul.id,
            'module_title': modul.title,
            'course_id': modul.course_id,
            'course_title': kurs.title if kurs else '',
            'assigned_at': str(z.assigned_at)[:10] if z.assigned_at else '',
        })
    return ergebnis


@router.post('/customer/{customer_id}/modules/{module_id}/assign')
def assign_module_to_customer(
    customer_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Modul dem Kunden freischalten."""
    modul = db.query(AcademyModule).filter(AcademyModule.id == module_id).first()
    if not modul:
        raise HTTPException(404, 'Modul nicht gefunden')
    customer_id = _kunde_user_id(db, customer_id)
    vorhanden = db.query(AcademyModuleAccess).filter(
        AcademyModuleAccess.customer_id == customer_id,
        AcademyModuleAccess.module_id == module_id,
    ).first()
    if vorhanden:
        raise HTTPException(409, 'Modul bereits zugewiesen')
    zuweisung = AcademyModuleAccess(
        customer_id=customer_id,
        module_id=module_id,
        assigned_at=datetime.utcnow(),
        assigned_by=current_user.id,
    )
    db.add(zuweisung)
    db.commit()
    db.refresh(zuweisung)
    return {
        'id': zuweisung.id,
        'customer_id': customer_id,
        'module_id': module_id,
        'module_title': modul.title,
        'assigned_at': str(zuweisung.assigned_at)[:10],
    }


@router.delete('/customer/{customer_id}/modules/{module_id}')
def remove_module_from_customer(
    customer_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Modul-Zugang fuer Kunden entfernen."""
    customer_id = _kunde_user_id(db, customer_id)
    zuweisung = db.query(AcademyModuleAccess).filter(
        AcademyModuleAccess.customer_id == customer_id,
        AcademyModuleAccess.module_id == module_id,
    ).first()
    if not zuweisung:
        raise HTTPException(404, 'Modulzugang nicht gefunden')
    db.delete(zuweisung)
    db.commit()
    return {'success': True}


@router.get('/customer/{customer_id}/courses')
def get_customer_courses(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Alle Kurse mit Fortschritt und Zertifikat-Status für einen Kunden."""
    customer_id = _kunde_user_id(db, customer_id)
    accesses = db.query(AcademyCustomerAccess).filter(
        AcademyCustomerAccess.customer_id == customer_id
    ).all()
    result = []
    for access in accesses:
        course = db.query(AcademyCourse).filter(AcademyCourse.id == access.course_id).first()
        if not course:
            continue
        progress = _progress_summary(access.course_id, customer_id, db)
        cert = db.query(AcademyCertificate).filter(
            AcademyCertificate.user_id == customer_id,
            AcademyCertificate.course_id == access.course_id,
        ).first()
        result.append({
            'id': access.id,
            'course_id': course.id,
            'course_title': course.title,
            'course_thumbnail': course.thumbnail_url or '',
            'assigned_at': str(access.assigned_at)[:10] if access.assigned_at else '',
            'progress_pct': progress['progress_pct'],
            'total_lessons': progress['total_lessons'],
            'completed': progress['completed'],
            'certificate_code': cert.certificate_code if cert else None,
        })
    return result


@router.post('/customer/{customer_id}/courses/{course_id}/assign')
def assign_course_to_customer(
    customer_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Kurs dem Kunden freischalten."""
    course = db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first()
    if not course:
        raise HTTPException(404, 'Kurs nicht gefunden')
    customer_id = _kunde_user_id(db, customer_id)
    existing = db.query(AcademyCustomerAccess).filter(
        AcademyCustomerAccess.customer_id == customer_id,
        AcademyCustomerAccess.course_id == course_id,
    ).first()
    if existing:
        raise HTTPException(409, 'Kurs bereits zugewiesen')
    access = AcademyCustomerAccess(
        customer_id=customer_id,
        course_id=course_id,
        assigned_at=datetime.utcnow(),
        assigned_by=current_user.id,
    )
    db.add(access)
    db.commit()
    db.refresh(access)
    return {
        'id': access.id,
        'customer_id': customer_id,
        'course_id': course_id,
        'course_title': course.title,
        'assigned_at': str(access.assigned_at)[:10],
    }


@router.delete('/customer/{customer_id}/courses/{course_id}')
def remove_course_from_customer(
    customer_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Kurs-Zugang für Kunden entfernen."""
    customer_id = _kunde_user_id(db, customer_id)
    access = db.query(AcademyCustomerAccess).filter(
        AcademyCustomerAccess.customer_id == customer_id,
        AcademyCustomerAccess.course_id == course_id,
    ).first()
    if not access:
        raise HTTPException(404, 'Kurszugang nicht gefunden')
    db.delete(access)
    db.commit()
    return {'success': True}
