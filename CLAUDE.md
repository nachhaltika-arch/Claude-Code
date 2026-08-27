# KOMPAGNON — Claude Code Regeln

## PFLICHT-CHECK bei jeder Session
Bevor irgendein Code angefasst wird, führe aus:
  git remote -v
  git branch --show-current

Erwartetes Ergebnis:
  origin → https://github.com/nachhaltika-arch/Claude-Code
  current branch → staging (oder main, falls nur lesend)

Falls das Repo nicht stimmt:
  → STOPPE sofort
  → Melde: "Falsches Repo. Bitte prüfen."
  → Führe NICHTS aus bis der Nutzer bestätigt

## Branch-Regeln (staging → main, dual-branch, ab 2026-05-01)

| Branch  | Zweck            | Wer pusht                        | Auto-Deploy           |
|---------|------------------|----------------------------------|-----------------------|
| main    | Produktiv / Live | Nur via Pull Request aus staging | Render Produktiv      |
| staging | Test / Stage     | Direkter Push erlaubt            | Render Staging-Server |

- Claude Code arbeitet IMMER auf: `staging`
- NIE direkt auf `main` pushen — Branch-Protection blockt es ohnehin
- KEINE zusätzlichen langlebigen Branches erstellen (`claude/*`, `feature/*` etc. sind verworfen)
- Nach jedem Commit sofort: `git push origin staging`

## Workflow

1. Arbeit auf `staging`: Code ändern → committen → pushen.
2. Render deployt automatisch auf den **Staging-Server** — dort testen.
3. Wenn Test grün ist: GitHub-PR `staging → main` öffnen, CI grün abwarten.
4. **Nutzer merged manuell** in `main`. Claude Code merged NIE selbst.
5. Render deployt automatisch auf den **Produktiv-Server** → live.

## Repo-Regel
- Einziges erlaubtes Repo: `nachhaltika-arch/Claude-Code`
- NIE in anderen Repos Änderungen machen

## Commit-Regel
- Commit-Messages auf Englisch
- Conventional-Commit-Style: `feat:`, `fix:`, `docs:`, `chore:`, `ci:`, `refactor:`, `perf:`, `test:`

## Deploy-Info
- **Staging**: Render deployt auf jeden Push zu `staging`
- **Produktiv**: Render deployt auf jeden Merge in `main`

Produktiv-URLs:
- Frontend: https://kompagnon-frontend.onrender.com (Dienst `kompagnon-frontend`, Static Site)
- Backend:  https://api.kompagnon.group (Dienst `kompagnon-backend-fra`, Frankfurt)

> **Korrigiert am 2026-08-27.** Hier stand `https://claude-code-znq2.onrender.com`
> als Produktiv-Backend. Dieser Dienst liegt in Oregon, ist seit dem Umzug
> (L-34) **suspendiert** und antwortet mit 503. Eine Anweisungsdatei, die auf
> einen toten Dienst zeigt, ist gefaehrlicher als gar keine: Wer dort 503
> misst, meldet einen Produktivausfall, den es nicht gibt.
>
> **Zweimal korrigiert, am selben Tag.** Beim ersten Anlauf stand hier
> `https://kompagnon.group` als Frontend — abgeleitet aus einem **302**, dem
> ich nicht gefolgt bin. Diese Adresse leitet auf die Agenturseite
> `www.kompagnon.eu` weiter und hat mit dem Werkzeug nichts zu tun. Ein
> Statuscode ist kein Ziel: Erst der Weiterleitung folgen, dann behaupten.
> Das Werkzeug traegt bis heute **keine** eigene Domain — nur das Backend hat
> eine (`api.kompagnon.group`).

Staging-URLs (live seit 2026-05-02):
- Frontend: https://kompagnon-frontend-staging.onrender.com
- Backend:  https://kompagnon-backend-staging.onrender.com
- DB:       kompagnon-staging-db (Postgres 18, Basic, Frankfurt)
- Blueprint: `kompagnon/render-staging.yaml`

## CI-Schutz
GitHub Actions (`.github/workflows/ci.yml`) läuft auf jede PR Richtung `main` mit vier Jobs:
- Backend — Lint (ruff)
- Backend — Smoke import
- Frontend — Build
- Secrets — Gitleaks

Bei rotem CI: erst fixen, dann mergen. Nicht durchmergen mit "Bypass" — das umgeht den Schutz.
