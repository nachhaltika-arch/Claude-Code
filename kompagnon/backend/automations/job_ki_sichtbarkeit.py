# -*- coding: utf-8 -*-
"""Der wöchentliche Lauf für Abonnenten: Wird der Betrieb genannt? (L-58 b)

**Warum wöchentlich und nicht täglich.** Jede Frage kostet Geld, und die
Antwort eines KI-Systems ändert sich nicht über Nacht. Wöchentlich ist der
Takt, den der Markt setzt — und der Takt, der eine Kurve ergibt, statt
Rauschen.

**Warum nur für Abonnenten.** Der Lauf ist die Leistung, für die bezahlt wird.
Ihn für alle laufen zu lassen, hieße, die Kostenstelle jedes Projekts zu
belasten, das nie danach gefragt hat.

**Was er ausdrücklich nicht tut.** Er ändert keine Punktzahl. Der GEO-Score
misst die *Lesbarkeit*, dieser Lauf die *Nennung* — zwei Fragen, zwei
Ergebnisse. Sie zu verrechnen hieße, einem kostenlosen Audit eine Kostenstelle
je Aufruf anzuhängen; diese Entscheidung ist offen und gehört David.
"""
import asyncio
import logging
from datetime import datetime

from database import SessionLocal
from modelle_audit import GeoAnalysis

logger = logging.getLogger(__name__)

#: Wer bezahlt, wird gemessen. `trialing` gehört dazu — in der Probezeit soll
#: der Kunde sehen, wofür er sich entscheidet.
LAUFENDE_ABOS = ("active", "trialing")

#: Drei Fragen je Lauf. Dieselbe Grenze wie am Endpunkt: Drei reichen für eine
#: belastbare Aussage, fünf verdoppeln die Kosten für wenig Zusatzwissen.
FRAGEN_JE_LAUF = 3


def _projektdaten(db, projekt_id: int) -> dict:
    """Gewerk, Ort, Domain und Name — oder leer, wenn etwas fehlt."""
    from routers.geo import _get_project_data
    from database import Project

    daten = _get_project_data(projekt_id, db)
    projekt = db.query(Project).filter(Project.id == projekt_id).first()
    return {
        "name": getattr(getattr(projekt, "lead", None), "company_name", "") or "",
        "domain": daten.get("website_url") or "",
        "gewerk": daten.get("gewerk") or "",
        "ort": daten.get("city") or "",
    }


def job_ki_sichtbarkeit_woechentlich() -> dict:
    """Fragt für jeden aktiven Abonnenten die angebundenen KI-Systeme.

    Gibt eine Bilanz zurück — auch für den Test, der sonst nur ins Protokoll
    sehen könnte.
    """
    from services.ki_anbieter import konfigurierte_anbieter
    from services.ki_sichtbarkeit import pruefe_ki_sichtbarkeit, verlauf_fortschreiben

    bilanz = {"abonnenten": 0, "gemessen": 0, "uebersprungen": 0, "fehler": 0}

    if not konfigurierte_anbieter():
        # **Kein Schlüssel heißt: nicht laufen, nicht messen, nicht schreiben.**
        # Ein Lauf ohne Anbieter erzeugte einen Verlaufseintrag ohne Zahlen —
        # später sähe die Kurve wie ein Einbruch aus, den es nie gab.
        logger.info("KI-Sichtbarkeit: kein System angebunden — Wochenlauf entfällt")
        return bilanz

    db = SessionLocal()
    try:
        abos = (db.query(GeoAnalysis)
                .filter(GeoAnalysis.subscription_status.in_(LAUFENDE_ABOS))
                .all())
        bilanz["abonnenten"] = len(abos)

        for analyse in abos:
            try:
                daten = _projektdaten(db, analyse.project_id)
            except Exception as fehler:  # noqa: BLE001
                logger.warning("KI-Sichtbarkeit: Projekt %s nicht lesbar (%s)",
                               analyse.project_id, fehler)
                bilanz["fehler"] += 1
                continue

            if not daten["gewerk"] or not daten["ort"]:
                # Ohne beides misst die Frage einen Markt, in dem der Betrieb
                # nicht arbeitet — das Ergebnis wäre schlechter als die Wahrheit.
                logger.info("KI-Sichtbarkeit: Projekt %s ohne Gewerk oder Ort — "
                            "übersprungen", analyse.project_id)
                bilanz["uebersprungen"] += 1
                continue

            try:
                befund = asyncio.run(pruefe_ki_sichtbarkeit(
                    name=daten["name"], domain=daten["domain"],
                    gewerk=daten["gewerk"], ort=daten["ort"],
                    max_fragen=FRAGEN_JE_LAUF,
                ))
            except Exception as fehler:  # noqa: BLE001
                logger.warning("KI-Sichtbarkeit: Lauf für Projekt %s gescheitert (%s)",
                               analyse.project_id, fehler)
                bilanz["fehler"] += 1
                continue

            if not befund.get("collected"):
                bilanz["uebersprungen"] += 1
                continue

            jetzt = datetime.utcnow()
            analyse.ki_sichtbarkeit = befund
            analyse.ki_sichtbarkeit_am = jetzt
            analyse.ki_sichtbarkeit_verlauf = verlauf_fortschreiben(
                analyse.ki_sichtbarkeit_verlauf, befund,
                jetzt.isoformat(timespec="seconds"))
            bilanz["gemessen"] += 1

        db.commit()
    finally:
        db.close()

    logger.info("KI-Sichtbarkeit Wochenlauf: %s Abonnenten, %s gemessen, "
                "%s übersprungen, %s Fehler", bilanz["abonnenten"],
                bilanz["gemessen"], bilanz["uebersprungen"], bilanz["fehler"])
    return bilanz
