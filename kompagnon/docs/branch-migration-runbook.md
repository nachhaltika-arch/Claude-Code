# Branch-Migration: zwei Branches → single-trunk (IEAR-Style)

**Status:** Runbook v1
**Erstellt:** 2026-04-30
**Ziel:** KAS auf gleiches Workflow-Modell wie IEARV4 umstellen — nur `main`, alle Änderungen via PR mit grüner CI.

---

## Ausgangslage

- Zwei langlebige Branches: `main` (Prod) + `staging` (Test)
- CLAUDE.md zwang bisher Arbeit auf `staging`
- GitHub Branch-Protection-Ruleset `protect-main` ist angelegt (PR-Pflicht)
- Render-Services existieren manuell (nicht aus Blueprint adoptiert)

## Zielbild

- **Eine Branch:** `main`
- Feature-Branches `claude/*` kurzlebig, via PR auf `main`, mit CI-Gate
- Render deployed nur aus `main`
- Keine zwei Welten mehr → kein Drift, kein „weiß nicht ob Produktion hängt"

---

## Schrittfolge

### Schritt 1 — Code-Änderungen (bereits erledigt im Vorbereitungs-Commit)

- [x] `CLAUDE.md` umgeschrieben auf single-trunk
- [x] `.github/workflows/ci.yml` triggert nur noch auf `main`
- [x] `kompagnon/README.md` Repository-Sektion aktualisiert
- [x] Dieses Runbook angelegt

### Schritt 2 — PR #24 mergen (manuell, du)

**Voraussetzung:** Vier CI-Jobs auf dem letzten Push grün.

1. https://github.com/nachhaltika-arch/Claude-Code/pull/24 öffnen
2. Prüfen: alle vier Status-Checks ✅
3. **Merge** klicken (Standard „Create a merge commit" oder „Squash and merge" — egal)
4. Branch-Lösch-Dialog erscheint nach Merge → **„Delete branch"** klicken (entfernt `staging` remote)

### Schritt 3 — Lokale staging-Branch entfernen (du, einmalig)

```bash
git checkout main
git pull origin main
git branch -d staging
git remote prune origin
```

### Schritt 4 — GitHub: Required Status Checks aktivieren

Repo → Settings → Rules → Rulesets → `protect-main` → Edit:

1. Häkchen bei **„Require status checks to pass"**
2. Klick **„Add checks"** → vier Jobs auswählen:
   - `Backend — Lint (ruff)`
   - `Backend — Smoke import`
   - `Frontend — Build`
   - `Secrets — Gitleaks`
3. Häkchen bei **„Require branches to be up to date before merging"** (empfohlen)
4. Save

Jetzt kann **kein PR** ohne grüne CI gemergt werden.

### Schritt 5 — Render: bestehende Services prüfen (du)

**Ziel-Frage:** Existiert ein zweites Service-Set für „Produktion", oder sind die in CLAUDE.md aufgeführten Services (`claude-code-znq2`, `kompagnon-frontend`) bereits die einzigen / produktiven?

Render Dashboard → Services-Liste prüfen:

- **Wenn nur ein Backend-/Frontend-Paar existiert** → keine weitere Aktion nötig. Die Services bleiben, ziehen jetzt aus `main` (vorher auch — ggf. auf staging gepointet, dann muss der Branch in jedem Service auf `main` umgestellt werden, siehe Schritt 5b).
- **Wenn zwei Service-Paare existieren** (eines aus `staging` und eines aus `main`):
  1. Identifiziere welches Paar das echte Prod ist (höchster Traffic, Custom-Domain, gefüllte DB).
  2. Wähle eines als Quell-of-Truth.
  3. Das andere im Render-Dashboard auf **„Suspend"** setzen (nicht sofort löschen — als Backup für 2 Wochen).
  4. Nach 2 Wochen ohne Auffälligkeiten: löschen.

### Schritt 5b — Render-Service-Branch auf `main` setzen (du, falls Services aktuell auf staging gepointet sind)

Pro Service in Render → Settings → "Build & Deploy" → **Branch** auf `main` ändern → Save.

Bei Postgres-Service: keine Branch-Bindung, bleibt unverändert.

### Schritt 6 — Render-Blueprint aktivieren (optional, empfohlen)

Wenn die existierenden Services auf `main` gepointet sind und stabil laufen:

Render Dashboard → Blueprints → "New Blueprint Instance":
- Repo: `nachhaltika-arch/Claude-Code`
- Branch: `main`
- Pfad zur YAML: `kompagnon/render.yaml`
- Render bietet Adoption für gleichnamige Services an (dann sind sie via `trigger=blueprint_sync` gebunden, nicht mehr `new_commit`)

**Wichtig (aus IEAR-Erfahrung, siehe `IEARV4/render.yaml`-Kommentare):**
- Niemals einen Service umbenennen — Render koppelt an Service-IDs, nicht Namen → Adoption bricht
- Niemals `generateValue: true` auf existierende Live-Secrets — sonst werden `SECRET_KEY` / Stripe-Webhook-Secret rotiert und Live-Sessions / verschlüsselte Werte zerschossen

### Schritt 7 — Verifikation

Nach allen Schritten:

- [ ] `git branch -a` lokal zeigt nur `main` + Remote-`origin/main`
- [ ] GitHub Repo zeigt nur `main` als Branch
- [ ] `protect-main`-Ruleset blockiert direkten Push (Test: `git push origin main` ohne PR → blockiert)
- [ ] Render-Service-Liste enthält nur ein Backend, ein Frontend, eine Postgres
- [ ] Letzter Render-Deploy hat als Quell-Branch `main`
- [ ] Test-Commit über Feature-Branch + PR → CI läuft → Merge → Render deployed → Site live

---

## Rollback-Plan (falls etwas schiefgeht)

1. **PR #24 wurde fälschlich gemerged + staging gelöscht:**
   - `git checkout -b staging origin/main~1` (eine Position vor Merge-Commit)
   - `git push -u origin staging`
   - GitHub-Branch-Protection auf `staging` ausschalten falls aktiv
   - Render-Services auf `staging` zurückstellen

2. **Render-Service zerschossen durch Blueprint-Adoption:**
   - Blueprint im Render Dashboard wieder lösen ("Detach")
   - Service manuell neu konfigurieren — Env-Vars sind in Render's Audit-Log einsehbar

3. **JWT_SECRET / Stripe-Secret rotiert:**
   - Aus Render-Audit-Log alten Wert wiederherstellen
   - Falls nicht möglich: alle Sessions auslöggen (Datenbank: `users.last_login = NULL`), neue Stripe-Webhook im Stripe-Dashboard einrichten

---

## Kontrolle: typische Fehlerquellen

- **CI war nie auf `main`-Push gelaufen** → Required-Status-Check-Auswahl (Schritt 4) zeigt die Jobs nicht. Lösung: einmal direkten Push (oder Test-PR-Merge) auf `main` machen, dann erscheinen sie in der Liste.
- **Render deployed nicht nach Merge** → Auto-Deploy-Toggle pro Service prüfen (Settings → Build & Deploy → Auto-Deploy: Yes).
- **Feature-Branch-PR wird nie als „grün" erkannt** → CI-Workflow triggert auch auf `pull_request: branches: [main]`, also egal welcher Source-Branch. Wenn trotzdem nichts läuft: Workflow-Datei-Pfad prüfen (`.github/workflows/ci.yml` muss exakt heißen, nicht `.yaml`).
