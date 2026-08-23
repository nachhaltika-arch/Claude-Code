"""Welche Pakete es gibt — beantwortet aus der Tabelle, nicht aus einer Liste.

**Warum es diesen Dienst gibt (L-97, 23.08.2026).** `projects_anlegen` prüfte
eine Paketangabe gegen eine feste Auswahl im Quelltext:

    if package_type not in ("starter", "kompagnon", "premium"):
        package_type = None

Solange der Katalog genau diese drei Zeilen hatte, fiel das nicht auf. Beim
Wechsel auf die Websprint-Produkte wäre es eine stille Falle geworden: Ein
Projekt mit dem Paket `websprint_neubau` hätte die Prüfung nicht bestanden,
die Angabe wäre auf `None` gefallen und die Spalte hätte ihren Standardwert
bekommen. Kein Fehler, keine Meldung — nur ein Projekt, das das falsche
Paket trägt, und ein Umsatz, der später an der falschen Stelle steht.

Dieselbe Klasse wie L-29: derselbe Sachverhalt an zwei Stellen gepflegt, und
eine davon läuft davon.

**Warum die Antwort nicht zwischengespeichert wird.** Der Katalog ändert sich
selten, aber er ändert sich **im Betrieb** — über `PUT /api/products/{slug}`
kann ein Paket stillgelegt oder freigeschaltet werden. Ein Zwischenspeicher
wäre genau der zweite Ort, den dieser Dienst abschaffen soll. Die Abfrage
liest eine Handvoll Zeilen; das ist billiger als die Klasse von Fehlern, die
ein veralteter Zwischenstand erzeugt.
"""
import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


def bekannte_slugs(db) -> set:
    """Alle Paketkennungen im Katalog — auch stillgelegte.

    **Auch die stillgelegten**, denn ein Projekt aus dem Frühjahr trägt
    weiterhin `kompagnon`. Wer diese Menge zum Prüfen benutzt, darf einem
    Bestandsprojekt nicht nachträglich sein Paket aberkennen.
    """
    try:
        zeilen = db.execute(text("SELECT slug FROM products")).fetchall()
    except Exception:  # noqa: BLE001 — eine fehlende Tabelle darf nichts kippen
        db.rollback()
        logger.warning("Produktkatalog nicht lesbar — Paketangabe wird verworfen")
        return set()
    return {z[0] for z in zeilen}


def verkaeufliche_slugs(db) -> set:
    """Was heute angeboten werden darf — die Teilmenge mit Status `live`.

    Für alles, was ein **neues** Geschäft anlegt. Nicht zum Prüfen von
    Bestandsdaten benutzen: dort gilt `bekannte_slugs`.
    """
    try:
        zeilen = db.execute(
            text("SELECT slug FROM products WHERE status = 'live'")).fetchall()
    except Exception:  # noqa: BLE001
        db.rollback()
        return set()
    return {z[0] for z in zeilen}
