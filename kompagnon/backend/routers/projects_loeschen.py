"""Ein Projekt entfernen — Vorschau, einzeln, in Gruppen (L-25).

**Warum eigene Datei, 23.08.2026.** Loeschen ist der Vorgang mit den meisten
Verbindungen: Ein Projekt haengt an Checklisten, Zeiten, Sitemap-Seiten und
Dateien, und die Reihenfolge, in der man sie loest, entscheidet darueber, ob
Reste bleiben. Das gehoert an eine Stelle, an der man es ganz liest. Die
**Vorschau** steht mit hier — sie beantwortet vor dem Griff, was verschwaende.

**Ein Wegweiser, der in die falsche Richtung zeigte.** Der Abschnittsmarker
„Projekte entfernen" stand bei Zeile 523, der naechste erst bei 980. Wer
danach schneidet, nimmt 457 Zeilen mit; der Vorgang selbst umfasst **109**,
dahinter folgten Phasenwechsel, Zeiterfassung, Checkliste und Marge. Genau
dieser Fehler ist beim ersten Anlauf passiert und fiel erst auf, als `ruff`
zehn undefinierte Namen meldete — darunter `_golive_automation`, das mit
Loeschen nichts zu tun hat. Derselbe Fall wie „IMPORT ENDPOINTS" in
`leads.py`, am selben Tag.

`ProjekteLoeschenRequest` und `_ids_aus_abfrage` wandern mit: beide haben
ausserhalb keinen Aufrufer.

**`DELETE /{project_id}` ist bewusst in `projects.py` geblieben**, obwohl es
fachlich hierher gehoerte. Der Grund ist die Registrierungsreihenfolge: Dieses
Modul wird **vor** `projects.py` geladen, damit die festen Pfade
`/loeschvorschau` und `/loeschen` nicht vom Platzhalter `/{project_id}`
verdeckt werden. Eine Platzhalter-Route in ein frueh geladenes Modul zu ziehen
kehrt genau das um — sie verdeckte dann jeden festen Pfad, der spaeter kommt.
Feste Pfade frueh, Platzhalter spaet; das ist die Regel, die
`test_keine_route_wird_von_einem_platzhalter_verdeckt` erzwingt.
"""
import logging

from fastapi import Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Project, get_db
from routers.auth_router import require_admin, require_innendienst
from routers.projects_router import router

logger = logging.getLogger(__name__)


# ── Projekte entfernen ────────────────────────────────────────────────
# Bis zum 17.08.2026 gab es dafür keinen Endpunkt. Wer ein Projekt loswerden
# wollte, musste SQL von Hand fahren — und das stand an dem Tag an, weil ein
# Projekt 135 Tage lang jeden Morgen dieselbe Mail ausgelöst hatte.
# Die Reihenfolge über die fünfzehn abhängigen Tabellen steht in
# `services/projekt_loeschen.py`, damit sie nur einmal existiert.


class ProjekteLoeschenRequest(BaseModel):
    ids: list[int]


def _ids_aus_abfrage(ids: str) -> list:
    """"1,2,3" → [1, 2, 3]. Was keine Zahl ist, fliegt raus."""
    return [int(teil) for teil in ids.split(",") if teil.strip().isdigit()]


@router.get("/loeschvorschau")
def loeschvorschau(
    ids: str = Query(..., description="Projektnummern, mit Komma getrennt"),
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Was ein Löschen anfassen würde — ohne etwas anzufassen.

    In `customers` stecken wiederkehrender Umsatz und CMS-Zugangsdaten. Die
    Zeilen können nicht bleiben (NOT-NULL-Fremdschlüssel), also soll wenigstens
    vorher jemand gesehen haben, wie viele es sind.
    """
    from services.projekt_loeschen import zaehlen

    projekt_ids = _ids_aus_abfrage(ids)
    if not projekt_ids:
        raise HTTPException(400, "Keine gültigen Projektnummern angegeben")

    return zaehlen(db, projekt_ids)



@router.post("/loeschen")
def projekte_loeschen(
    anfrage: ProjekteLoeschenRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Mehrere auf einmal.

    Eine leere Liste wird abgewiesen statt als „alle" gelesen zu werden — ein
    versehentlich leerer Rumpf darf nicht den ganzen Bestand kosten.
    """
    from services.projekt_loeschen import entfernen

    if not anfrage.ids:
        raise HTTPException(400, "Keine Projektnummern angegeben")

    bericht = entfernen(db, anfrage.ids)
    db.commit()
    return bericht


