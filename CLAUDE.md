# KOMPAGNON — Claude Code Regeln

## PFLICHT-CHECK bei jeder Session
Bevor irgendein Code angefasst wird, führe aus:
  git remote -v
  git branch --show-current

Erwartetes Ergebnis:
  origin → https://github.com/nachhaltika-arch/Claude-Code
  current branch → main (oder ein Feature-Branch davon)

Falls das Repo nicht stimmt:
  → STOPPE sofort
  → Melde: "Falsches Repo. Bitte prüfen."
  → Führe NICHTS aus bis der Nutzer bestätigt

## Branch-Regeln (single-trunk, IEAR-Style)

- **Hauptbranch:** `main` — produktiv/live, einzige langlebige Branch
- **Keine permanente `staging`-Branch** (Umstellung 2026-04-30)
- **Feature-Branches** sind erlaubt für Multi-Commit-Arbeit; Naming: `claude/<kurze-beschreibung>`
- **Direkt auf `main` pushen ist blockiert** durch GitHub-Branch-Protection (Ruleset `protect-main`) — alle Änderungen via Pull Request
- Branch löschen NACH Merge (nicht stehen lassen)

## Workflow

1. **Kleine Änderung (ein Commit):** Feature-Branch anlegen, Commit, push, PR auf `main`, CI grün abwarten, mergen lassen.
2. **Größere Arbeit:** eigener Feature-Branch, mehrere Commits, dann ein PR.
3. Claude erstellt **nie** den Merge selbst — Merge führt der Nutzer durch.
4. Nach Merge: Render deployed automatisch aus `main` → live.

## Repo-Regel
- Einziges erlaubtes Repo: `nachhaltika-arch/Claude-Code`
- NIE in anderen Repos Änderungen machen

## Commit-Regel
- Commit-Messages auf Englisch
- Conventional-Commit-Style: `feat:`, `fix:`, `docs:`, `chore:`, `ci:`, `refactor:`, `perf:`, `test:`

## Deploy-Info
Render.com deployt automatisch bei jedem Merge auf `main`.

- Frontend: https://kompagnon-frontend.onrender.com
- Backend:  https://claude-code-znq2.onrender.com

## CI-Schutz
GitHub Actions (`.github/workflows/ci.yml`) läuft auf jede PR Richtung `main` mit vier Jobs:
- Backend — Lint (ruff)
- Backend — Smoke import
- Frontend — Build
- Secrets — Gitleaks

Bei rotem CI: erst fixen, dann mergen. Nicht durchmergen mit "Bypass" — das umgeht den Schutz.
