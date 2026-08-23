"""Zertifikate: ausstellen, nachweisen, abrufen (L-25).

**Warum eigene Datei, 23.08.2026.** Ein abgeschlossener Vorgang mit eigener
Frage — „hat jemand den Kurs wirklich zu Ende gebracht?" — und einer eigenen
Kennung (`_gen_cert_code`). Er braucht aus dem gemeinsamen Bestand genau
einen Helfer, `_progress_summary`.
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

from routers.academy_gemeinsam import _progress_summary


# ── Certificates ───────────────────────────────────────────

def _gen_cert_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))


@router.get('/certificates')
def list_certificates(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Alle Zertifikate des aktuellen Users."""
    certs = db.query(AcademyCertificate).filter(AcademyCertificate.user_id == current_user.id).all()
    result = []
    for c in certs:
        course = db.query(AcademyCourse).filter(AcademyCourse.id == c.course_id).first()
        result.append({
            'id': c.id,
            'course_id': c.course_id,
            'course_title': course.title if course else '',
            'issued_at': str(c.issued_at)[:10] if c.issued_at else '',
            'certificate_code': c.certificate_code,
        })
    return result


@router.post('/courses/{course_id}/certificate')
def issue_certificate(course_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Zertifikat ausstellen wenn Kurs zu 100% abgeschlossen."""
    course = db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first()
    if not course:
        raise HTTPException(404, 'Kurs nicht gefunden')
    progress = _progress_summary(course_id, current_user.id, db)
    if progress['progress_pct'] < 100:
        raise HTTPException(400, f'Kurs noch nicht abgeschlossen ({progress["progress_pct"]}%)')
    existing = db.query(AcademyCertificate).filter(
        AcademyCertificate.user_id == current_user.id,
        AcademyCertificate.course_id == course_id,
    ).first()
    if existing:
        course_obj = db.query(AcademyCourse).filter(AcademyCourse.id == course_id).first()
        return {
            'id': existing.id,
            'course_id': course_id,
            'course_title': course_obj.title if course_obj else '',
            'issued_at': str(existing.issued_at)[:10] if existing.issued_at else '',
            'certificate_code': existing.certificate_code,
            'already_exists': True,
        }
    code = _gen_cert_code()
    while db.query(AcademyCertificate).filter(AcademyCertificate.certificate_code == code).first():
        code = _gen_cert_code()
    cert = AcademyCertificate(
        user_id=current_user.id, course_id=course_id,
        issued_at=datetime.utcnow(), certificate_code=code,
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return {
        'id': cert.id, 'course_id': course_id,
        'course_title': course.title,
        'issued_at': str(cert.issued_at)[:10],
        'certificate_code': cert.certificate_code,
        'already_exists': False,
    }


@router.get('/certificates/{code}/verify')
def verify_certificate(code: str, db: Session = Depends(get_db)):
    """Zertifikat öffentlich verifizieren (kein Login nötig)."""
    cert = db.query(AcademyCertificate).filter(AcademyCertificate.certificate_code == code).first()
    if not cert:
        raise HTTPException(404, 'Zertifikat nicht gefunden')
    course = db.query(AcademyCourse).filter(AcademyCourse.id == cert.course_id).first()
    # Get user name from User table if possible
    try:
        from database import User
        user = db.query(User).filter(User.id == cert.user_id).first()
        user_name = f"{user.first_name} {user.last_name}".strip() if user else f"User #{cert.user_id}"
    except Exception:
        user_name = f"User #{cert.user_id}"
    return {
        'valid': True,
        'certificate_code': cert.certificate_code,
        'user_name': user_name,
        'course_title': course.title if course else '',
        'issued_at': str(cert.issued_at)[:10] if cert.issued_at else '',
    }
