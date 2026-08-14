---
name: migration_trap_main_py
description: Neue DB-Spalten gehören nach main.py::_run_migrations — migrations.py und migrate.py laufen NICHT beim Start
metadata: 
  node_type: memory
  type: project
  originSessionId: 7e2c88f9-9f53-4931-8502-eca89b9d7234
  modified: 2026-08-12T08:28:52.980Z
---

Im KOMPAGNON-Backend gibt es drei Migrationsdateien, aber beim Serverstart
läuft **nur die inline-Liste in `main.py::_run_migrations`**.
`kompagnon/backend/migrations.py` und `kompagnon/backend/migrate.py` werden
ausschließlich von Hand aufgerufen (`python migrations.py`).

Dazu: `create_all()` legt fehlende *Tabellen* an, rüstet aber niemals
*Spalten* an bestehenden Tabellen nach.

Folge, wenn eine neue Spalte nur in `migrations.py` landet: Die Spalte fehlt
auf Render. Weil SQLAlchemy immer alle Modellspalten selektiert, scheitert
dann **jede** Abfrage auf der Tabelle mit `ProgrammingError`, nicht nur der
neue Endpunkt. Die Tests merken nichts — die Test-DB wird per `create_all`
aus den Modellen gebaut und hat die Spalte immer.

Am 2026-08-12 hat genau das das Widget auf Staging lahmgelegt. Seitdem sagen
beide toten Dateien das in ihrem Kopfkommentar. Siehe
[[resume_point_2026_08_12]].
