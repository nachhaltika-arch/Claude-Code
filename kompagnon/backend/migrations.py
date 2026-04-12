"""
DEPRECATED — Nicht mehr verwenden.

Alle Migrationen sind jetzt in `db_migrations.py` konsolidiert
(Tech-Debt Fix 01). Diese Datei bleibt vorerst als Deprecation-Marker
erhalten und wird in einem spaeteren Cleanup-Sprint geloescht.

Nutze stattdessen:
    from db_migrations import run_migrations
    run_migrations(engine)
"""
raise ImportError(
    "migrations.py ist deprecated. Bitte db_migrations.py verwenden."
)
