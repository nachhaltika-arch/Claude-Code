"""Was der Lernende tut: Lektionsfortschritt, Quiz, eigener Stand (L-25).

**Warum eigene Datei, 23.08.2026.** Drei Abschnitte aus `academy.py` — 260
Zeilen —, die mit dem Rest **keinen einzigen Helfer** teilen. Vor dem Schnitt
nachgemessen: Von den zwoelf Helfern der Ursprungsdatei ruft dieser Teil
**keinen**. Er braucht nur die Modelle und den Router.

Das ist der sauberste Schnitt der ganzen Datei, und deshalb der erste.
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


# ── Quiz ──────────────────────────────────────────────────

@router.get('/lessons/{lesson_id}/quiz')
def get_quiz(lesson_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Quiz-Fragen für eine Lektion laden (ohne is_correct für Nutzer)."""
    lesson = db.query(AcademyLesson).filter(AcademyLesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(404, 'Lektion nicht gefunden')
    questions = (
        db.query(AcademyQuizQuestion)
        .filter(AcademyQuizQuestion.lesson_id == lesson_id)
        .order_by(AcademyQuizQuestion.sort_order, AcademyQuizQuestion.id)
        .all()
    )
    result = []
    for q in questions:
        try:
            answers = json.loads(q.answers_json) if q.answers_json else []
        except (json.JSONDecodeError, TypeError):
            answers = []
        result.append({
            'id': q.id,
            'question': q.question,
            'answers': [{'text': a.get('text', ''), 'id': i} for i, a in enumerate(answers)],
        })
    return result


@router.post('/lessons/{lesson_id}/quiz')
def submit_quiz(lesson_id: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Quiz-Antworten prüfen, Score speichern, Lektion abschließen wenn bestanden.
    Body: {answers: {question_id: answer_index, ...}}
    """
    lesson = db.query(AcademyLesson).filter(AcademyLesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(404, 'Lektion nicht gefunden')
    questions = (
        db.query(AcademyQuizQuestion)
        .filter(AcademyQuizQuestion.lesson_id == lesson_id)
        .order_by(AcademyQuizQuestion.sort_order, AcademyQuizQuestion.id)
        .all()
    )
    if not questions:
        raise HTTPException(400, 'Keine Fragen für diese Lektion')

    user_answers = data.get('answers', {})
    correct = 0
    details = []
    for q in questions:
        try:
            answer_opts = json.loads(q.answers_json) if q.answers_json else []
        except (json.JSONDecodeError, TypeError):
            answer_opts = []
        chosen_idx = user_answers.get(str(q.id))
        is_correct = False
        if chosen_idx is not None and 0 <= int(chosen_idx) < len(answer_opts):
            is_correct = bool(answer_opts[int(chosen_idx)].get('is_correct', False))
        if is_correct:
            correct += 1
        correct_idx = next((i for i, a in enumerate(answer_opts) if a.get('is_correct')), None)
        details.append({
            'question_id': q.id, 'chosen': chosen_idx,
            'correct': is_correct, 'correct_answer_idx': correct_idx,
        })

    total = len(questions)
    score = round((correct / total) * 100) if total else 0
    passed = score >= 70  # 70% Mindestpunktzahl

    if passed:
        existing = db.query(AcademyProgress).filter(
            AcademyProgress.user_id == current_user.id,
            AcademyProgress.lesson_id == lesson_id,
        ).first()
        if existing:
            existing.completed_at = datetime.utcnow()
            existing.score = score
        else:
            db.add(AcademyProgress(
                user_id=current_user.id, lesson_id=lesson_id,
                completed_at=datetime.utcnow(), score=score,
            ))
        db.commit()

    return {
        'correct': correct, 'total': total, 'score': score,
        'passed': passed, 'details': details,
    }


@router.post('/lessons/{lesson_id}/quiz/admin')
def upsert_quiz_questions(lesson_id: int, data: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Quiz-Fragen für Lektion setzen (Admin). Body: {questions: [{question, answers: [{text, is_correct}]}]}"""
    if not db.query(AcademyLesson).filter(AcademyLesson.id == lesson_id).first():
        raise HTTPException(404, 'Lektion nicht gefunden')
    db.query(AcademyQuizQuestion).filter(AcademyQuizQuestion.lesson_id == lesson_id).delete()
    for i, q in enumerate(data.get('questions', [])):
        db.add(AcademyQuizQuestion(
            lesson_id=lesson_id,
            question=q.get('question', ''),
            answers_json=json.dumps(q.get('answers', []), ensure_ascii=False),
            sort_order=i,
        ))
    db.commit()
    return {'success': True, 'count': len(data.get('questions', []))}


# ── Progress (User) ────────────────────────────────────────

@router.get('/progress')
def get_my_progress(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Gesamtfortschritt des aktuellen Users über alle Kurse."""
    rows = (
        db.query(AcademyLesson.id, AcademyModule.course_id)
        .join(AcademyModule, AcademyLesson.module_id == AcademyModule.id)
        .all()
    )
    lesson_to_course = {r[0]: r[1] for r in rows}
    lesson_ids = list(lesson_to_course.keys())
    if not lesson_ids:
        return {'total_lessons': 0, 'completed': 0, 'courses': []}
    completed_rows = db.query(AcademyProgress).filter(
        AcademyProgress.user_id == current_user.id,
        AcademyProgress.lesson_id.in_(lesson_ids),
        AcademyProgress.completed_at.isnot(None),
    ).all()
    completed_map = {r.lesson_id: r for r in completed_rows}
    totals: dict = {}
    dones: dict = {}
    for lid, cid in lesson_to_course.items():
        totals[cid] = totals.get(cid, 0) + 1
        if lid in completed_map:
            dones[cid] = dones.get(cid, 0) + 1
    total_lessons = sum(totals.values())
    total_completed = sum(dones.values())
    courses_progress = [
        {
            'course_id': cid, 'total_lessons': total,
            'completed': dones.get(cid, 0),
            'progress_pct': round((dones.get(cid, 0) / total) * 100) if total else 0,
        }
        for cid, total in totals.items()
    ]
    return {
        'total_lessons': total_lessons,
        'completed': total_completed,
        'progress_pct': round((total_completed / total_lessons) * 100) if total_lessons else 0,
        'courses': courses_progress,
    }
