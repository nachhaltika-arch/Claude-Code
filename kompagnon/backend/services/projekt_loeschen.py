"""Ein Projekt entfernen — an einer Stelle, in einer Reihenfolge.

An `projects` hängen fünfzehn Tabellen. Ein blankes `DELETE FROM projects`
scheitert an den Fremdschlüsseln und ließe bei den übrigen Tabellen Zeilen
zurück, deren `project_id` ins Leere zeigt. Deshalb zwei Gruppen:

  BLEIBEN   Der Verweis wird gelöst, die Zeile bleibt stehen.
            `email_logs` ist der Nachweis, was wann an wen ging — genau der
            wurde am 17.08.2026 gebraucht, um einen Fehlversand über 135 Tage
            aufzuarbeiten. Ein Protokoll, das mit dem Gegenstand verschwindet,
            über den es Auskunft gibt, ist kein Protokoll.

  GEHEN MIT Zeilen, die ohne ihr Projekt keinen Inhalt haben. `customers`
            steht bewusst am Ende: Die Tabelle hat einen NOT-NULL-Fremd-
            schlüssel auf `projects`, diese Zeilen KÖNNEN nicht bleiben. In
            ihnen stecken wiederkehrender Umsatz und CMS-Zugangsdaten — was
            `zaehlen()` vor dem Löschen sichtbar macht.
            `invoices` und `retainer_contracts` gehen vor `customers`, weil
            sie auf sie verweisen.

Die Reihenfolge in `GEHEN_MIT` ist deshalb Teil der Aussage, nicht Kosmetik.

Diese Funktionen committen nicht. Der Aufrufer entscheidet, wann die
Transaktion endet — so kann das Löschen eines Betriebs die Projekte im selben
Zug mitnehmen.

Herkunft: `scripts/projekte-entfernen.sql`, dort gegen alle fünfzehn Tabellen
geprüft. Das Skript bleibt für den Fall, dass jemand ohne laufende Anwendung
an die Daten muss.
"""
import logging

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Zeile bleibt, Verweis wird gelöst.
BLEIBEN = (
    "email_logs",
    "briefings",
    "assistant_conversations",
)

# Zeile geht mit. Reihenfolge: was verweist, zuerst.
GEHEN_MIT = (
    "project_checklists",
    "communications",
    "automation_logs",
    "time_tracking",
    "project_scraped_pages",
    "project_scrape_jobs",
    "project_credentials",
    "geo_analyses",
    "website_versions",
    "invoices",
    "retainer_contracts",
    "customers",
)


def tabelle_vorhanden(db: Session, name: str) -> bool:
    """Ob es die Tabelle in dieser Datenbank gibt.

    Ein Teil des Schemas entsteht erst beim Start in
    `main.py::_run_migrations`. Wer davon ausgeht, dass alles da ist, bricht
    die Transaktion ab, sobald es das nicht ist.
    """
    return name in set(inspect(db.get_bind()).get_table_names())


def _tabellen_mit_projektverweis(db: Session) -> frozenset:
    """Welche der genannten Tabellen es hier wirklich gibt.

    Ein Teil entsteht erst zur Laufzeit in `main.py::_run_migrations` und
    fehlt je nach Datenbank. Fehlende werden übersprungen statt die
    Transaktion abzubrechen — wie im SQL-Skript über `to_regclass`.
    """
    pruefer = inspect(db.get_bind())
    vorhanden = set(pruefer.get_table_names())
    return frozenset(
        tabelle for tabelle in BLEIBEN + GEHEN_MIT
        if tabelle in vorhanden
        and any(s["name"] == "project_id" for s in pruefer.get_columns(tabelle))
    )


def _zaehle(db: Session, tabelle: str, projekt_ids: list) -> int:
    return db.execute(
        text(f"SELECT count(*) FROM {tabelle} WHERE project_id = ANY(:ids)"),
        {"ids": projekt_ids},
    ).scalar() or 0


def zaehlen(db: Session, projekt_ids: list) -> dict:
    """Was ein Löschen anfassen würde — ohne etwas anzufassen.

    Erst zählen, dann löschen: Bei `customers` ist der Unterschied zwischen
    „weg" und „gewusst, was weg ist" der wiederkehrende Umsatz.
    """
    if not projekt_ids:
        return {"projekte": 0, "wird_geloescht": {}, "bleibt_erhalten": {}}

    vorhanden = _tabellen_mit_projektverweis(db)
    projekte = db.execute(
        text("SELECT count(*) FROM projects WHERE id = ANY(:ids)"),
        {"ids": projekt_ids},
    ).scalar() or 0

    return {
        "projekte": projekte,
        "wird_geloescht": {
            tabelle: _zaehle(db, tabelle, projekt_ids)
            for tabelle in GEHEN_MIT if tabelle in vorhanden
        },
        "bleibt_erhalten": {
            tabelle: _zaehle(db, tabelle, projekt_ids)
            for tabelle in BLEIBEN if tabelle in vorhanden
        },
    }


def entfernen(db: Session, projekt_ids: list) -> dict:
    """Entfernt die Projekte samt Anhang. Committet nicht.

    Gibt denselben Bericht zurück wie `zaehlen()` — nur eben über das, was
    tatsächlich geschehen ist.
    """
    if not projekt_ids:
        return {"projekte": 0, "geloescht": {}, "verweis_geloest": {}}

    vorhanden = _tabellen_mit_projektverweis(db)

    verweis_geloest = {}
    for tabelle in BLEIBEN:
        if tabelle not in vorhanden:
            continue
        ergebnis = db.execute(
            text(f"UPDATE {tabelle} SET project_id = NULL "
                 "WHERE project_id = ANY(:ids)"),
            {"ids": projekt_ids},
        )
        verweis_geloest = {**verweis_geloest, tabelle: ergebnis.rowcount}

    geloescht = {}
    for tabelle in GEHEN_MIT:
        if tabelle not in vorhanden:
            continue
        ergebnis = db.execute(
            text(f"DELETE FROM {tabelle} WHERE project_id = ANY(:ids)"),
            {"ids": projekt_ids},
        )
        geloescht = {**geloescht, tabelle: ergebnis.rowcount}

    ergebnis = db.execute(
        text("DELETE FROM projects WHERE id = ANY(:ids)"), {"ids": projekt_ids}
    )

    logger.info(
        "Projekte entfernt: %s — mitgelöscht %s, Verweis gelöst %s",
        ergebnis.rowcount, sum(geloescht.values()), sum(verweis_geloest.values()),
    )

    return {
        "projekte": ergebnis.rowcount,
        "geloescht": geloescht,
        "verweis_geloest": verweis_geloest,
    }
