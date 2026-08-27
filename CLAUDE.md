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

> **Schritt 5 kostet rund 40 Sekunden Produktion.** Das ist keine Störung,
> sondern eine bewusst gewählte Betriebseigenschaft (L-94, Entscheidung
> David am 2026-08-27): Der Dienst hat einen Datenträger unter `/var/data`,
> und Render erlaubt Diensten mit Datenträger nur **eine** Instanz — also
> „erst beenden, dann starten" statt rollierend. Wörtlich aus der
> Herstellerdoku: *„Adding a persistent disk to your service disables
> zero-downtime deploys for it."*
>
> Wer während eines Merges misst, sieht **502** und meldet einen Ausfall,
> den es als Fehler nicht gibt. Wer den Datenträger entfernt, um die
> Sekunden loszuwerden, verliert die hochgeladenen Dateien **und** die
> Auftragsbestätigungen der Kunden.
>
> **Wann die Entscheidung neu zu treffen ist:** sobald produktiv spürbar
> Verkehr ankommt (heute sechs Anfragen pro Stunde) oder ein Kunde während
> des Freitagsmerges arbeitet. Der Weg heraus ist dann ein Objektspeicher
> für die Uploads, nicht das Löschen des Datenträgers.

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
- Werkzeug (Frontend): https://kas.kompagnon.group — Dienst `kompagnon-frontend`,
  Static Site. Direkt auch unter https://kompagnon-frontend.onrender.com.
- Backend/API: https://api.kompagnon.group — Dienst `kompagnon-backend-fra`, Frankfurt.
- **Nicht** `kompagnon.group` — die leitet auf die Agenturseite
  `www.kompagnon.eu` weiter und hat mit dem Werkzeug nichts zu tun.

> **Korrigiert am 2026-08-27.** Hier stand `https://claude-code-znq2.onrender.com`
> als Produktiv-Backend. Dieser Dienst liegt in Oregon, ist seit dem Umzug
> (L-34) **suspendiert** und antwortet mit 503. Eine Anweisungsdatei, die auf
> einen toten Dienst zeigt, ist gefaehrlicher als gar keine: Wer dort 503
> misst, meldet einen Produktivausfall, den es nicht gibt.
>
> **Dreimal korrigiert, am selben Tag — und die ersten zwei Male war ich zu
> schnell.** Erst stand hier `https://kompagnon.group` als Frontend,
> abgeleitet aus einem **302**, dem ich nicht gefolgt bin; die Adresse fuehrt
> zur Agenturseite. Dann schrieb ich, das Werkzeug habe **gar keine** Domain —
> auch falsch: Es hat `kas.kompagnon.group`, und die stand seit dem 22.08. in
> L-03 als Einbettungsadresse des Widgets.
>
> Beide Male habe ich aus **einer** Messung geschlossen, statt die naheliegende
> zweite zu machen. Ein Statuscode ist kein Ziel, und „ich habe keine gefunden"
> ist keine Abwesenheit. Am 27.08. an vier Adressen gleichzeitig geprueft.

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
