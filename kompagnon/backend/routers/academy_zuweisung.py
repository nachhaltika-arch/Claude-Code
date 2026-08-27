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

from routers.academy_gemeinsam import (_kunde_user_id, _kunde_user_ids,
                                       _progress_summary)


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

# ── Freischalten gilt dem Betrieb, nicht einem Menschen darin ─────────
#
# Bis zum 25.08.2026 hatte ein Betrieb genau ein Konto; `_kunde_user_id`
# uebersetzte die Betriebsnummer aus dem Pfad in dieses eine. Seit es
# Zweitzugaenge gibt, waere das still falsch: Die Zuweisung erreichte
# **einen** der Menschen — welchen, entschiede die Reihenfolge in der
# Datenbank —, und der andere saehe eine leere Akademie.
#
# Die beiden Helfer stehen hier einmal statt viermal: Modul und Kurs
# unterscheiden sich nur im Modell und im Namen der Fremdschluesselspalte.


def _konten(db, kennung: int) -> list:
    """Die Zugaenge des Betriebs — oder die Kennung selbst.

    Der Rueckfall ist kein Schoenheitsfehler, sondern der Altbestand: Wo
    kein Kundenkonto am Betrieb haengt, war die Kennung schon immer eine
    **Benutzer**nummer (L-54/L-55). `_kunde_user_id` tat dasselbe.
    """
    return _kunde_user_ids(db, kennung) or [kennung]


def _allen_zuweisen(db, modell, feld: str, kennung: int, gegenstand: int,
                    durch: int, bereits: str):
    """Jedem Zugang des Betriebs freischalten, was er noch nicht hat.

    **409 erst, wenn es wirklich alle haben.** Sonst blockierte ein einziger
    Nachzuegler den ganzen Betrieb: Der Erste hat den Kurs, der Zweite nicht,
    und die Zuweisung meldete „bereits zugewiesen".
    """
    konten = _konten(db, kennung)
    vorhanden = {z[0] for z in db.query(modell.customer_id).filter(
        modell.customer_id.in_(konten),
        getattr(modell, feld) == gegenstand).all()}
    fehlend = [k for k in konten if k not in vorhanden]
    if not fehlend:
        raise HTTPException(409, bereits)

    neu = [modell(customer_id=k, assigned_at=datetime.utcnow(),
                  assigned_by=durch, **{feld: gegenstand})
           for k in fehlend]
    db.add_all(neu)
    db.commit()
    for zeile in neu:
        db.refresh(zeile)
    return konten, neu


def _allen_entziehen(db, modell, feld: str, kennung: int, gegenstand: int,
                     fehlt: str) -> int:
    """Wieder wegnehmen — bei jedem Zugang, sonst bliebe einer freigeschaltet."""
    konten = _konten(db, kennung)
    zeilen = db.query(modell).filter(
        modell.customer_id.in_(konten),
        getattr(modell, feld) == gegenstand).all()
    if not zeilen:
        raise HTTPException(404, fehlt)
    for zeile in zeilen:
        db.delete(zeile)
    db.commit()
    return len(zeilen)


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
    konten, angelegt = _allen_zuweisen(
        db, AcademyModuleAccess, 'module_id', customer_id, module_id,
        current_user.id, 'Modul bereits zugewiesen')
    return {
        'id': angelegt[0].id,
        'customer_id': konten[0],
        'module_id': module_id,
        'module_title': modul.title,
        'assigned_at': str(angelegt[0].assigned_at)[:10],
        'zugaenge': len(konten),
    }


@router.delete('/customer/{customer_id}/modules/{module_id}')
def remove_module_from_customer(
    customer_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Modul-Zugang fuer Kunden entfernen."""
    entzogen = _allen_entziehen(
        db, AcademyModuleAccess, 'module_id', customer_id, module_id,
        'Modulzugang nicht gefunden')
    return {'success': True, 'zugaenge': entzogen}


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
    konten, angelegt = _allen_zuweisen(
        db, AcademyCustomerAccess, 'course_id', customer_id, course_id,
        current_user.id, 'Kurs bereits zugewiesen')
    return {
        'id': angelegt[0].id,
        'customer_id': konten[0],
        'course_id': course_id,
        'course_title': course.title,
        'assigned_at': str(angelegt[0].assigned_at)[:10],
        'zugaenge': len(konten),
    }


@router.delete('/customer/{customer_id}/courses/{course_id}')
def remove_course_from_customer(
    customer_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Kurs-Zugang für Kunden entfernen."""
    entzogen = _allen_entziehen(
        db, AcademyCustomerAccess, 'course_id', customer_id, course_id,
        'Kurszugang nicht gefunden')
    return {'success': True, 'zugaenge': entzogen}
