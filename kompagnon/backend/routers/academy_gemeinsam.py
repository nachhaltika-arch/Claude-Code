"""Wer darf welchen Kurs sehen, und wie weit ist er — die geteilten Helfer.

**Warum eigene Datei (L-25, 23.08.2026).** `routers/academy.py` hatte 1.109
Zeilen und zehn Abschnitte. Die ersten 200 Zeilen waren keiner davon: zwölf
Helfer, die alle anderen brauchen. Sie hier zu fuehren macht die Schnitte
darunter erst moeglich — sonst zoege jeder Teil eine Kopie hinter sich her.

**Zwei Gruppen, und beide gehoeren zusammen:**

- **Freischaltung** — `_ist_kunde`, `_kunde_user_id`, `_sichere_zuweisungen`,
  `_freigeschaltete_kurse`, `_freigeschaltete_module`, `_sichtbare_module`.
  Hier haengt L-54 dran: Eine Zuweisung mit zweideutiger Kennung schaltet
  **nichts** frei, und `_sichere_zuweisungen` ist die Stelle, die das haelt.
- **Darstellung** — `_kursumfang`, die drei `_serialize_*` und
  `_progress_summary`. Sie rufen einander **nicht** auf; nachgemessen vor dem
  Schnitt, und das ist der Grund, warum sie gemeinsam wandern konnten, ohne
  dass eine Reihenfolge zu beachten waere.

**Reiner Umzug.** Keine Funktion wurde veraendert, umbenannt oder
zusammengefasst.
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


# ── Helpers ───────────────────────────────────────────────

# Wer den Bestand pflegt, muss ihn auch sehen — sonst waere ein gesperrter
# Kurs unbearbeitbar. Die Sperre richtet sich an Kunden, nicht an den Betrieb.
def _ist_kunde(user) -> bool:
    return getattr(user, 'role', None) == 'kunde'


def _kunde_user_id(db, kennung: int) -> int:
    """Uebersetzt die Kennung aus dem Pfad in die Benutzer-ID des Kunden.

    Zweideutigkeit im Bestand, aufgedeckt am 19.08.2026: Das Kundenblatt ruft
    `/api/academy/customer/{id}/...` mit der **Betriebs-ID** (`lead.id`,
    `LeadProfile.jsx`), waehrend die Akademie alles andere ueber die
    **Benutzer-ID** fuehrt — `AcademyProgress.user_id`,
    `AcademyCertificate.user_id`. Zugewiesen wurde unter der einen Kennung,
    gelesen unter der anderen. Folgenlos war das nur, solange **niemand** die
    Zuweisung abfragte.

    Aufgeloest wird beim **Schreiben**, nicht beim Lesen. Der naheliegende Weg
    — beim Lesen einfach beide Kennungen zulassen — waere eine Hintertuer:
    Benutzer-IDs und Betriebs-IDs sind verschiedene, fortlaufende Zahlenraeume
    und koennen sich ueberschneiden. Dann schaltete die Zuweisung eines
    fremden Betriebs jemanden frei, den niemand gemeint hat.

    Gespeichert wird deshalb immer die Benutzer-ID.
    """
    kunden = _kunde_user_ids(db, kennung)
    return kunden[0] if kunden else kennung


def _kunde_user_ids(db, kennung: int) -> list:
    """**Alle** Konten dieses Betriebs — die Antwort auf dieselbe Frage,
    seit ein Betrieb mehrere haben kann (25.08.2026).

    `_kunde_user_id` gab bis dahin `.first()` zurueck. Das war richtig,
    solange ein Betrieb genau ein Konto hatte, und wurde am Tag der
    Zweitzugaenge still falsch: Eine Zuweisung auf dem Betriebsblatt haette
    **einen** der Menschen erreicht — welchen, entschied die Reihenfolge in
    der Datenbank. Der andere haette eine leere Akademie gesehen, ohne dass
    irgendwo ein Fehler steht.

    Lesen darf weiter mit einem auskommen: Geschrieben wird fuer alle, also
    haben alle dasselbe. Geschrieben wird ab hier fuer **jeden**.
    """
    zeilen = (db.query(User.id).filter(User.lead_id == kennung,
                                       User.role == 'kunde')
              .order_by(User.id).all())
    return [z[0] for z in zeilen]


#: Seit diesem Tag loest der **Schreib**pfad die Kennung beim Zuweisen auf
#: (L-55, 19.08.2026). Was danach entstand, ist sicher eine Benutzernummer;
#: nur aeltere Zeilen koennen noch eine Betriebsnummer enthalten.
AUFLOESUNG_SEIT = datetime(2026, 8, 19)


def _sichere_zuweisungen(db, user, modell, feld):
    """Die Zuweisungen dieses Nutzers, ohne die zweideutigen Altzeilen.

    **Das Problem (L-54).** Altzeilen fuehren teils die **Betriebs**nummer,
    waehrend alles andere ueber die **Benutzer**nummer laeuft. Wo eine Zahl
    beides sein kann, laesst `services/zuweisung_kennung.py` sie beim
    Nachtrag bewusst liegen — raten waere schlimmer als nichts tun, denn ein
    falsch geratener Eintrag schaltet einem **fremden** Betrieb etwas frei.

    Im Befund stand, das sei „heute ungefaehrlich, weil kein einziger Kurs
    gesperrt ist" — gefaehrlich werde es mit dem ersten gesperrten. Darauf zu
    warten war die Luecke: Der Lehrplan aus L-60 wird Kurse sperren.

    **Warum der Zeitstempel und nicht die Nummer allein.** Ein erster Entwurf
    sperrte jeden Nutzer aus, dessen Nummer zweideutig ist. Das traf auch
    voellig gueltige Zuweisungen — die Ueberschneidung zweier Zahlenraeume
    sagt ja nichts ueber die einzelne Zeile. Ein eigener Test hat das
    gefangen. Uebergangen wird deshalb nur, was **vor** der Aufloesung
    entstand und damit wirklich zweideutig sein kann.
    """
    from services.zuweisung_kennung import zweideutige_kennungen

    abfrage = db.query(feld).filter(modell.customer_id == user.id)
    if user.id in zweideutige_kennungen(db):
        abfrage = abfrage.filter(modell.assigned_at >= AUFLOESUNG_SEIT)
    return {wert for (wert,) in abfrage.all()}


def _freigeschaltete_kurse(db, user) -> set:
    return _sichere_zuweisungen(db, user, AcademyCustomerAccess,
                                AcademyCustomerAccess.course_id)


def _freigeschaltete_module(db, user) -> set:
    return _sichere_zuweisungen(db, user, AcademyModuleAccess,
                                AcademyModuleAccess.module_id)


def _sichtbare_module(db, course_id, user):
    """Die Module eines Kurses in Reihenfolge — gefiltert, wenn noetig.

    Ein gesperrtes Modul ist fuer einen Kunden nicht versteckt, sondern nicht
    zugewiesen. Der Unterschied zaehlt: Es fehlt vollstaendig, statt als
    Schloss dazustehen und Neugier zu wecken.
    """
    module = (
        db.query(AcademyModule)
        .filter(AcademyModule.course_id == course_id)
        .order_by(AcademyModule.position, AcademyModule.sort_order, AcademyModule.id)
        .all()
    )
    if not _ist_kunde(user):
        return module

    frei = _freigeschaltete_module(db, user)
    return [m for m in module if not m.is_locked or m.id in frei]


def _kursumfang(db, course_id) -> dict:
    """Module, Lektionen und Gesamtdauer — berechnet, nicht mitgefuehrt.

    Die alte `courses`-Tabelle fuehrte genau diese drei als Zaehler, die
    niemand nachrechnete. Zaehler driften; eine Abfrage nicht.
    """
    modul_ids = [
        m_id for (m_id,) in
        db.query(AcademyModule.id).filter(AcademyModule.course_id == course_id).all()
    ]
    if not modul_ids:
        return {'module_count': 0, 'lesson_count': 0, 'duration_minutes': 0}

    lektionen = (
        db.query(AcademyLesson.duration_minutes)
        .filter(AcademyLesson.module_id.in_(modul_ids)).all()
    )
    return {
        'module_count': len(modul_ids),
        'lesson_count': len(lektionen),
        'duration_minutes': sum((d or 0) for (d,) in lektionen),
    }


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
        'is_locked': bool(c.is_locked),
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
        'description': m.description or '',
        'thumbnail_url': m.thumbnail_url or '',
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
