---
name: KAS branch workflow — staging → main (dual-branch)
description: Aktueller Workflow ab 2026-05-01: arbeiten auf staging, Render Staging-Server testen, dann PR auf main → produktiv. Single-trunk-Versuch vom 2026-04-30 wurde verworfen.
type: project
originSessionId: 324ae64f-c7b6-403b-a0c6-61344cf01a62
---
Ab 2026-05-01 gilt: dual-branch `staging → main`. Direkt auf `staging` pushen, Render deployt auf Staging-Server, dort testen, dann PR `staging → main`, manueller Merge → Render deployt produktiv.

**Why:** Der Nutzer will Feature-Updates auf einem dedizierten Staging-Server testen, bevor sie live gehen. Der single-trunk-Versuch vom Vortag (CLAUDE.md auf "main only" umgeschrieben) wurde explizit zurückgerollt — dieselbe Person, andere Entscheidung am Folgetag. Commit `8a5653d` auf staging stellt CLAUDE.md, README und runbook auf dual-branch zurück.

**How to apply:**
- Wenn du arbeitest: bist du auf `staging`. Push direkt dorthin nach jedem Commit.
- KEINE `claude/*`- oder `feature/*`-Branches anlegen — wurden alle gelöscht und sind verworfen. Dependabot-Branches bleiben (die macht GitHub).
- `main` nur via PR aus `staging`. Claude merged NIE selbst.
- Wenn du `kompagnon/docs/branch-migration-runbook.md` liest: das ist verworfen, NICHT ausführen. Wahrheit steht in `CLAUDE.md` und `kompagnon/README.md`.
- Render-Staging-Services baut der Nutzer selbst (Dashboard, eigene DB, Stripe-Test-Keys).
