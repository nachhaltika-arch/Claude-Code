# -*- coding: utf-8 -*-
"""Die zugesagte Bauzeit eines Betriebs — nachsehen und die Vorlage eintragen.

**Warum es diesen Weg gibt (L-166, K3, 06.09.2026).** Der Angebotsfuss sagt
zu: „Verzoegert sich eine Freigabe nach M7 oder M8, ruht die Frist fuer die
Dauer der Verzoegerung." Die **Freigabe** traegt der Kunde selbst ein
(`POST /api/portal/mitwirkung/M7`). Die **Vorlage** kann nur von uns kommen —
wir legen den Bauplan vor, nicht er. Ohne diesen Zeitpunkt gibt es keine
Spanne, ohne Spanne keine Ruhezeit, und ohne Ruhezeit ist das zugesagte Ende
nicht berechenbar, sondern nur behauptbar. Von beiden Seiten.

**Die Sperre haengt am Router.** Wer seine eigene Vorlage datieren koennte,
koennte sich die Ruhezeit wegrechnen, die er selbst verursacht hat — genau
deshalb ist das hier Innendienst und nicht Kundenkonto.

**Gelesen wird dieselbe Ableitung wie im Kundenkonto**, aus
`services/bauzeit_projekt.py`. Zwei Rechnungen fuer dasselbe Datum sind zwei,
die auseinanderlaufen koennen; bei einer zugesagten Frist ist das der Fall,
der nicht eintreten darf.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, MitwirkungStand, Project
from routers.auth_router import get_current_user, require_innendienst
from services import bauzeit, bauzeit_projekt
from services import mitwirkung as kat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bauzeit", tags=["bauzeit"],
                   dependencies=[Depends(require_innendienst)])


def _projekt(db: Session, lead_id: int):
    """Das juengste Projekt des Betriebs — dieselbe Wahl wie im Portal.

    Zwei verschiedene Projekte fuer denselben Bildschirm waeren zwei
    verschiedene Fristen, je nachdem wer hinsieht.
    """
    return (db.query(Project).filter(Project.lead_id == lead_id)
            .order_by(Project.created_at.desc()).first())


@router.get("/{lead_id}")
def bauzeit_lesen(lead_id: int, db: Session = Depends(get_db)):
    """Beginn, Ruhezeiten und das zugesagte Ende — der Innendienstblick."""
    project = _projekt(db, lead_id)
    if not project:
        # **Kein 404.** Ein Betrieb ohne Projekt ist kein Fehler, sondern der
        # Normalfall vor dem Kauf. Ein Fehlerkasten an dieser Stelle liest
        # sich, als sei etwas kaputt.
        return {"lead_id": lead_id, "projekt_id": None, "frist": None}

    return {"lead_id": lead_id, "projekt_id": project.id,
            "frist": bauzeit_projekt.frist_stand(db, project)}


@router.post("/{lead_id}/vorlage/{kennung}")
def vorlage_eintragen(lead_id: int, kennung: str,
                      db: Session = Depends(get_db),
                      nutzer=Depends(get_current_user)):
    """Festhalten, dass wir eine Freigabe vorgelegt haben.

    **Nur M7 und M8.** „Logo und Bilder" legt niemand vor — der Kunde
    liefert es. Ein Vorlagedatum daran waere eine Ruhezeit fuer etwas, das
    nie gestockt hat.

    **Die erste Vorlage zaehlt.** Ein zweiter Klick darf den Zeitpunkt nicht
    nach hinten schieben: Das verlaengerte die Frist des Kunden zu unseren
    Gunsten, und niemand saehe es. Dieselbe Regel wie beim Eingangsdatum auf
    der Gegenseite.
    """
    punkt = kat.NACH_KENNUNG.get(kennung)
    if not punkt:
        raise HTTPException(404, f"Unbekannter Mitwirkungspunkt: {kennung}")
    if punkt.wirkung != kat.FRISTPAUSE:
        raise HTTPException(
            400, f"{kennung} ist keine Freigabe — nur M7 und M8 werden vorgelegt")

    project = _projekt(db, lead_id)
    if not project:
        raise HTTPException(404, "Kein Projekt gefunden")

    stand = (db.query(MitwirkungStand)
             .filter(MitwirkungStand.project_id == project.id,
                     MitwirkungStand.kennung == kennung).first())
    if not stand:
        stand = MitwirkungStand(project_id=project.id, kennung=kennung)
        db.add(stand)

    if not stand.vorgelegt_am:
        stand.vorgelegt_am = datetime.utcnow()
        stand.vorgelegt_von = nutzer.email or ""
    db.commit()

    pause = bauzeit.pause_je_freigabe(stand.vorgelegt_am, stand.erledigt_am)
    return {
        "ok": True, "kennung": kennung,
        "vorgelegt_am": stand.vorgelegt_am.isoformat(),
        "vorgelegt_von": stand.vorgelegt_von or "",
        # **Die Frist steht in der Antwort**, damit der Bildschirm sie nicht
        # nachrechnen muss. Eine zweite Rechnung in JavaScript waere der
        # zweite Ort, an dem die Auslegung der fuenf Werktage gepflegt wird.
        "frist_bis": pause.frist_bis.isoformat() if pause.frist_bis else None,
        "freigabefrist_werktage": bauzeit.FREIGABEFRIST_WERKTAGE,
    }
