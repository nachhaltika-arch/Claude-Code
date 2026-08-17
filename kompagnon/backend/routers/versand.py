"""
Der Not-Aus fuer automatischen Mailversand — als Endpunkt.

Lesen darf jeder Angemeldete: Die Oberflaeche zeigt den Zustand im Menue, und
das muss sie auch dem Auditor zeigen koennen, der sich sonst wundert, warum
nichts rausgeht. Umlegen darf nur ein Admin.

Warum ein eigener Endpunkt und nicht der allgemeine Einstellungs-Endpunkt:
Ein Schalter mit dieser Wirkung soll im Code einen Namen haben, unter dem man
ihn findet — nicht ein Schluessel-Wert-Paar in einer Sammelabfrage.
Siehe `services/versandsperre.py` fuer den Anlass.
"""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from routers.auth_router import require_admin, require_any_auth
from services import versandsperre

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/versand", tags=["versand"])


class VersandZustand(BaseModel):
    erlaubt: bool


@router.get("/status")
def status_lesen(
    _=Depends(require_any_auth),
    db: Session = Depends(get_db),
) -> VersandZustand:
    """Ist der automatische Versand gerade erlaubt?"""
    return VersandZustand(erlaubt=versandsperre.automatischer_versand_erlaubt(db))


@router.put("/status")
def status_setzen(
    zustand: VersandZustand,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
) -> VersandZustand:
    """Schaltet den automatischen Versand an oder aus.

    Die Aenderung wirkt sofort — die Jobs fragen bei jedem Lauf nach, es gibt
    keinen Zwischenspeicher und keinen Neustart.
    """
    versandsperre.setzen(db, zustand.erlaubt, admin_id=getattr(admin, "id", None))
    return VersandZustand(erlaubt=versandsperre.automatischer_versand_erlaubt(db))
