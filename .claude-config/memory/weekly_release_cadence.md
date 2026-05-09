---
name: Weekly Release Cadence (Mo-Do entwickeln, Fr Merge)
description: Wöchentlicher Release-Rhythmus — staging-Pushes Mo-Do, Sammel-PR staging→main wird Freitag gemerged. Verfeinert die CLAUDE.md-Regel "Nutzer merged manuell" um eine konkrete Kadenz.
type: feedback
originSessionId: 2b3ba8a9-fd56-40d4-8be3-a138fefc1e60
---
**Regel:** Über die Woche hinweg auf `staging` entwickeln und pushen (inkl. Dependabot-PRs sammel-mergen in staging). Am **Freitag** ein Pull Request `staging → main` mergen → Produktiv-Deploy.

**Why:** User möchte einen vorhersehbaren wöchentlichen Release-Rhythmus statt ad-hoc Merges. Reduziert kognitive Last (eine Entscheidung pro Woche statt mehrere), gibt natürlichen Buffer für Staging-Tests Mo-Do, und macht Produktiv-Deploys planbar (z.B. Freitag nachmittags wenn weniger Traffic). Bestätigt am 2026-05-04 nach Render-Drift-Fix, als der dual-branch-Workflow erstmals scharf wurde.

**How to apply:**
- **Mo-Do:** Code-Arbeit landet auf `staging`. Render baut Staging-Services. Dependabot-PRs (gegen staging) prüfen + sammel-mergen.
- **Mo morgen (oder nach erstem stabilen staging-Stand):** Sammel-PR `staging → main` eröffnen. Der PR aktualisiert sich automatisch mit jedem weiteren staging-Push während der Woche — kein neuer PR pro Commit nötig.
- **Fr:** PR final reviewen + mergen (Admin-Bypass auf `protect-main`-Ruleset, da `required_approving_review_count: 0` aber Status-Check-Mismatch existiert). Render baut Produktiv mit allen Wochen-Commits.
- Hotfixes außerhalb des Rhythmus: einzelnen Hotfix-PR `staging → main` eröffnen + sofort mergen, dann zurück zur regulären Kadenz.
- **Dependabot ist deaktiviert** (2026-05-04, User-Entscheidung). Repo bleibt auf nur 2 Branches: `main` + `staging`. Dependency-Updates erfolgen manuell auf staging (`npm update`, `pip install -U`), getestet, dann Freitag mit nach main. Falls security-relevant: `npm audit` / `pip-audit` lokal ausführen, gezielt patchen, normaler PR-Flow.
