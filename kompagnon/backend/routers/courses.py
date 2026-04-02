"""
Courses API — KOMPAGNON internal/customer/product training catalogue.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Course, get_db
from routers.auth_router import get_current_user, require_admin

router = APIRouter(prefix="/api/courses", tags=["courses"])

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CourseCreate(BaseModel):
    title: str
    description: str = ""
    category: str = "intern"          # intern | kunde | produkt
    thumbnail_color: str = "#008eaa"
    chapter_count: int = 0
    participant_count: int = 0
    duration_minutes: int = 0


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    thumbnail_color: Optional[str] = None
    chapter_count: Optional[int] = None
    participant_count: Optional[int] = None
    duration_minutes: Optional[int] = None


def _fmt(c: Course) -> dict:
    """Format a Course ORM object to a JSON-serialisable dict."""
    total = c.duration_minutes or 0
    h, m  = divmod(total, 60)
    duration = f"{h}:{m:02d}:00"
    return {
        "id":               c.id,
        "title":            c.title,
        "description":      c.description or "",
        "category":         c.category or "intern",
        "thumbnail_color":  c.thumbnail_color or "#008eaa",
        "chapter_count":    c.chapter_count or 0,
        "participant_count": c.participant_count or 0,
        "duration_minutes": c.duration_minutes or 0,
        "duration":         duration,
        "created_at":       c.created_at.isoformat() if c.created_at else None,
        "created_by":       c.created_by,
    }

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/")
def list_courses(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Return all courses, optionally filtered by category."""
    q = db.query(Course)
    if category and category != "all":
        q = q.filter(Course.category == category)
    return [_fmt(c) for c in q.order_by(Course.id).all()]


@router.post("/", status_code=201)
def create_course(
    body: CourseCreate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new course (admin only)."""
    course = Course(
        title=body.title,
        description=body.description,
        category=body.category,
        thumbnail_color=body.thumbnail_color,
        chapter_count=body.chapter_count,
        participant_count=body.participant_count,
        duration_minutes=body.duration_minutes,
        created_by=admin.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return _fmt(course)


@router.get("/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    """Return a single course by ID."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Kurs nicht gefunden")
    return _fmt(course)


@router.put("/{course_id}")
def update_course(
    course_id: int,
    body: CourseUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update a course (admin only)."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Kurs nicht gefunden")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return _fmt(course)


@router.delete("/{course_id}", status_code=204)
def delete_course(
    course_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a course (admin only)."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Kurs nicht gefunden")
    db.delete(course)
    db.commit()


# ── Seed helper (called from main.py on startup) ──────────────────────────────

SEED_COURSES = [
    {
        "title": "Gratis Mitgliedschaft",
        "description": "Einführung in das KOMPAGNON-System und erste Schritte für neue Mitglieder.",
        "category": "intern",
        "thumbnail_color": "#008eaa",
        "chapter_count": 0,
        "participant_count": 14,
        "duration_minutes": 18,
    },
    {
        "title": "Website-Pflege für Kunden",
        "description": "Wie Kunden ihre Website eigenständig pflegen, Inhalte aktualisieren und häufige Fehler vermeiden.",
        "category": "kunde",
        "thumbnail_color": "#059669",
        "chapter_count": 4,
        "participant_count": 38,
        "duration_minutes": 84,
    },
    {
        "title": "Homepage Standard 2025 — Das Produkt",
        "description": "Vollständige Produktschulung: Anforderungen, Audit-Kriterien, Zertifizierungsstufen und Umsetzungsprozess.",
        "category": "produkt",
        "thumbnail_color": "#7c3aed",
        "chapter_count": 6,
        "participant_count": 9,
        "duration_minutes": 183,
    },
]


def seed_courses(db: Session) -> None:
    """Insert seed courses if the table is empty."""
    if db.query(Course).count() > 0:
        return
    for data in SEED_COURSES:
        db.add(Course(**data))
    db.commit()
