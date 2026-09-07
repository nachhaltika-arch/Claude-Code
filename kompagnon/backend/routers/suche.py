# -*- coding: utf-8 -*-
"""Die allgemeine Suche im Werkzeug (Wunsch David, 06.09.2026).

**Der Befund: Es gab keine.** Wer einen Betrieb suchte, ging auf die
Betriebsliste und filterte dort; wer ein Projekt suchte, auf die Pipeline; wer
einen Zugang suchte, in die Benutzerverwaltung. Die Frage „wo ist Firma
Mueller?" hatte je nach Gegenstand eine andere Antwort — und wer den
Gegenstand nicht kannte, suchte dreimal.

**Was durchsucht wird, und warum genau das.** Betriebe, Projekte und Zugaenge.
Audits, Tickets und Rechnungen haengen alle an einem Betrieb; wer ihn gefunden
hat, ist da. Drei Tabellen sind billig, sieben waeren langsam und die vier
zusaetzlichen fuehrten meist zum selben Ziel.

**Sie ist Innendienst.** Eine Volltextsuche ueber den Bestand in der Hand
eines Kunden waere ein Datenleck mit Suchfeld — deshalb haengt die Sperre am
Router, nicht an der Funktion.

**Jeder Treffer traegt sein Ziel.** Eine Liste, aus der man nicht springen
kann, ist eine Liste zum Abschreiben; und die Adresse gehoert dorthin, wo
bekannt ist, was gefunden wurde.
"""
import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth_router import require_innendienst

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/suche", tags=["suche"],
                   dependencies=[Depends(require_innendienst)])

#: Ab wie vielen Zeichen ueberhaupt gesucht wird. **Ein Buchstabe ist keine
#: Suche, sondern ein Tastendruck** — ohne Untergrenze liefe bei jedem Zeichen
#: eine Abfrage ueber drei Tabellen.
MINDESTLAENGE = 2

#: Wie viele Treffer hoechstens herauskommen. Eine Suche, die alles herausgibt,
#: ist ein Ausleseweg.
HOECHSTMENGE = 30
JE_ART = 10


@router.get("")
def suchen(q: str = Query("", max_length=120), db: Session = Depends(get_db)):
    """Betriebe, Projekte und Zugaenge auf einmal."""
    begriff = (q or "").strip()
    if len(begriff) < MINDESTLAENGE:
        return {"treffer": [], "begriff": begriff,
                "hinweis": f"Bitte mindestens {MINDESTLAENGE} Zeichen eingeben."}

    muster = f"%{begriff.lower()}%"
    treffer = []

    def hole(sql: str, bauen):
        try:
            for zeile in db.execute(text(sql), {"m": muster, "n": JE_ART}).fetchall():
                treffer.append(bauen(zeile))
        except Exception as fehler:  # noqa: BLE001 — eine Tabelle darf die Suche nicht kippen
            db.rollback()
            logger.warning("Suche: Teilabfrage fehlgeschlagen (%s: %s)",
                           type(fehler).__name__, fehler)

    # ── Betriebe ──────────────────────────────────────────────────────
    hole(
        "SELECT id, company_name, email, website_url FROM leads "
        "WHERE LOWER(COALESCE(company_name,'')) LIKE :m "
        "   OR LOWER(COALESCE(email,'')) LIKE :m "
        "   OR LOWER(COALESCE(website_url,'')) LIKE :m "
        "ORDER BY company_name ASC LIMIT :n",
        lambda z: {"art": "betrieb", "titel": z[1] or z[2] or f"Betrieb {z[0]}",
                   "dazu": z[2] or z[3] or "", "ziel": f"/app/betriebe/{z[0]}"})

    # ── Projekte ──────────────────────────────────────────────────────
    #
    # **Ueber den Betriebsnamen mitgesucht.** Ein Projekt heisst selten anders
    # als sein Betrieb, und wer „Mueller" tippt, meint dessen Projekt.
    hole(
        "SELECT p.id, p.lead_id, p.status, p.package_type, l.company_name "
        "FROM projects p LEFT JOIN leads l ON l.id = p.lead_id "
        "WHERE LOWER(COALESCE(l.company_name,'')) LIKE :m "
        "   OR LOWER(COALESCE(p.package_type,'')) LIKE :m "
        "ORDER BY p.created_at DESC LIMIT :n",
        lambda z: {"art": "projekt",
                   "titel": f"Projekt · {z[4] or f'Betrieb {z[1]}'}",
                   "dazu": " · ".join(x for x in (z[3], z[2]) if x),
                   "ziel": f"/app/projects/{z[0]}"})

    # ── Zugaenge ──────────────────────────────────────────────────────
    #
    # **Kein Kennwort, kein Zweitfaktor, kein Kundentoken.** Was hier
    # herauskommt, steht auf einem Bildschirm, den mehrere Personen sehen.
    hole(
        "SELECT id, email, first_name, last_name, role FROM users "
        "WHERE LOWER(COALESCE(email,'')) LIKE :m "
        "   OR LOWER(COALESCE(first_name,'') || ' ' || COALESCE(last_name,'')) LIKE :m "
        "ORDER BY email ASC LIMIT :n",
        lambda z: {"art": "zugang",
                   "titel": (f"{z[2] or ''} {z[3] or ''}".strip() or z[1]),
                   "dazu": f"{z[1]} · {z[4]}", "ziel": "/app/admin/users"})

    return {"treffer": treffer[:HOECHSTMENGE], "begriff": begriff, "hinweis": ""}
