"""Führt die alte Kurstabelle in die Akademie über.

Das Werkzeug hatte zwei Kurswelten. Die eine, ``academy_courses``, trägt
Module, Lektionen, Fortschritt, Quiz, Zertifikate und Kundenzuweisung; acht
Oberflächen rufen sie. Die andere, ``courses``, trug **gar keine Struktur** —
nur ``chapter_count``, ``participant_count`` und ``duration_minutes`` als
mitgeführte Zahlen. Eine einzige Oberfläche rief sie, und deren Adresse stand
in keinem Menü.

Der heikle Teil ist nicht das Kopieren, sondern **was nicht kopiert wird**:
Die drei Zeilen der Demo-Saat tragen erfundene Teilnehmerzahlen. Sie in die
echte Akademie zu holen hieße, genau die Sorte Zahl zu verbreiten, die am
18.08. auf den Mobil-Kacheln gefunden und entfernt wurde.

Deshalb der Zuschnitt:

- **Saat unverändert** → bleibt liegen
- **Saat bearbeitet** → wer den Text geändert hat, hat ihn zu seinem gemacht;
  wird übernommen
- **Titel schon in der Akademie** → nichts tun, kein Duplikat
- **alles andere** → übernehmen, aber ``is_published=False``, damit ein Mensch
  es ansieht, bevor es erscheint

Die Funktion läuft bei **jedem** Start als eigene Startphase. Sie muss deshalb
zweierlei aushalten: mehrfaches Laufen und eine Tabelle, die es irgendwann
nicht mehr gibt.
"""
import logging
from typing import Dict, List

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import AcademyCourse

logger = logging.getLogger(__name__)

# Die Demo-Saat, wortgleich wie sie in ``routers/courses.py`` stand. Sie steht
# hier und nicht dort, weil der Router mit dieser Zusammenführung verschwindet.
# Verglichen wird über Titel **und** Beschreibung: Ein geänderter Text ist ein
# menschlicher Eingriff und damit erhaltenswert.
DEMO_SAAT = {
    ("Gratis Mitgliedschaft",
     "Einführung in das KOMPAGNON-System und erste Schritte für neue Mitglieder."),
    ("Website-Pflege für Kunden",
     "Wie Kunden ihre Website eigenständig pflegen, Inhalte aktualisieren und "
     "häufige Fehler vermeiden."),
    ("Homepage Standard 2025 — Das Produkt",
     "Vollständige Produktschulung: Anforderungen, Audit-Kriterien, "
     "Zertifizierungsstufen und Umsetzungsprozess."),
}

# `courses.category` kannte drei Werte, `academy_courses.target_audience` auch —
# nur andere. Ohne diese Abbildung landet jeder übernommene Kurs auf dem
# Vorgabewert und damit bei der falschen Zielgruppe.
ZIELGRUPPE_NACH_KATEGORIE = {
    "intern": "employee",
    "kunde": "customer",
    "produkt": "both",
}
ZIELGRUPPE_VORGABE = "both"


def _alte_kurse_lesen(db) -> List[dict]:
    """Die Zeilen der alten Tabelle — oder ``None``, wenn es sie nicht gibt."""
    zeilen = db.execute(text(
        "SELECT id, title, description, category FROM courses ORDER BY id"
    )).fetchall()
    return [dict(z._mapping) for z in zeilen]


def zusammenfuehren(db) -> Dict[str, object]:
    """Überträgt erhaltenswerte Kurse aus ``courses`` nach ``academy_courses``.

    Gibt einen Bericht zurück, statt nur zu loggen: Der Aufrufer schreibt ihn
    ins Startprotokoll, und die Tests prüfen daran, was tatsächlich geschah.
    """
    bericht: Dict[str, object] = {
        "uebernommen": [],
        "saat_uebersprungen": [],
        "vorhanden_uebersprungen": [],
        "alte_tabelle_fehlt": False,
    }

    try:
        alte = _alte_kurse_lesen(db)
    except SQLAlchemyError:
        # Nach dem endgültigen Löschen der Tabelle ist das der Normalfall und
        # kein Fehler. Die Sitzung ist danach unbrauchbar — zurückrollen, sonst
        # scheitert jede weitere Anweisung mit „transaction is aborted".
        db.rollback()
        bericht["alte_tabelle_fehlt"] = True
        return bericht

    if not alte:
        return bericht

    vorhandene_titel = {
        titel for (titel,) in db.query(AcademyCourse.title).all()
    }

    for zeile in alte:
        titel = (zeile["title"] or "").strip()
        beschreibung = (zeile["description"] or "").strip()

        if (titel, beschreibung) in DEMO_SAAT:
            bericht["saat_uebersprungen"].append(titel)
            continue

        if titel in vorhandene_titel:
            bericht["vorhanden_uebersprungen"].append(titel)
            continue

        db.add(AcademyCourse(
            title=titel,
            description=beschreibung,
            category=zeile["category"] or "",
            target_audience=ZIELGRUPPE_NACH_KATEGORIE.get(
                zeile["category"], ZIELGRUPPE_VORGABE),
            # Nicht veröffentlicht: Der übernommene Kurs hat keine Module und
            # keine Lektionen — er wäre in der Akademie eine leere Kachel.
            is_published=False,
        ))
        vorhandene_titel.add(titel)
        bericht["uebernommen"].append(titel)

    if bericht["uebernommen"]:
        db.commit()

    return bericht


def zusammenfuehren_beim_start() -> None:
    """Startphase — eigene Sitzung, Bericht ins Protokoll."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        bericht = zusammenfuehren(db)
    finally:
        db.close()

    if bericht["alte_tabelle_fehlt"]:
        logger.info("✓ Kurse: die alte Tabelle gibt es nicht mehr — nichts zu tun")
        return

    logger.info(
        "✓ Kurse zusammengeführt — %d übernommen, %d Demo-Saat übersprungen, "
        "%d bereits vorhanden",
        len(bericht["uebernommen"]),
        len(bericht["saat_uebersprungen"]),
        len(bericht["vorhanden_uebersprungen"]),
    )
    for titel in bericht["uebernommen"]:
        logger.info("  · übernommen (unveröffentlicht): %s", titel)
