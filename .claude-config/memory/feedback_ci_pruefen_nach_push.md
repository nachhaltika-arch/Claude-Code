---
name: feedback-ci-pruefen-nach-push
description: Nach jedem Push nach staging den CI-Lauf mit gh run prüfen — lokale Tests sind nicht CI
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7e2c88f9-9f53-4931-8502-eca89b9d7234
  modified: 2026-08-13T07:56:56.805Z
---

Nach jedem `git push origin staging` den CI-Lauf prüfen
(`gh run list --branch staging`, bei Bedarf `gh run watch <id> --exit-status`)
und erst danach von „grün" sprechen.

**Why:** Am 2026-08-13 habe ich „volle Suite grün, CI-Regelsatz sauber"
gemeldet und damit lokale Tests plus lokales ruff gemeint. Der CI-Lauf war
rot: Der Playwright-E2E-Test fand, dass die gesamte Komponenten-Bibliothek
leer zurückkam. David musste selbst danach fragen. Zwei Läufe standen rot, und
der Render-Deploy nach staging wurde übersprungen — der Stand, den ich als
fertig beschrieben hatte, war nie deployt.

**How to apply:** Die CI hat sieben Jobs, nicht die vier aus CLAUDE.md:
pytest, ruff, Smoke-Import, Frontend-Build, Gitleaks, **Playwright-E2E** und
Render-Deploy. Der E2E-Job läuft gegen eine per `create_all` frisch gebaute
Datenbank und einen echten Seed — er findet Dinge, die die Backend-Tests nicht
finden können, weil die ihre Daten per ORM anlegen. Bei Änderungen an Spalten,
Filtern oder Seeds ist er der eigentliche Prüfer.

Siehe [[migration-trap-main-py]] für die verwandte stille Falle bei
Spaltenänderungen und [[resume-point-2026-08-13]] für den konkreten Fall.
