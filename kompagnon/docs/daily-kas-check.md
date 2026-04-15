# KOMPAGNON Daily KAS Check

Tägliche Systemkontrolle für das KOMPAGNON Automation System.
Das vollständige Prompt unten in eine neue Claude-Code-Session pasten.

---

## Wann ausführen
- Nach jedem Render-Deploy
- Morgens vor dem Arbeitsstart
- Bei Verdacht auf Backend-Probleme

## Was geprüft wird
1. Git-State (Branch + Remote stimmen)
2. Backend Live-Status (`/api/ping`, `/api/health`, `/api/health/full`)
3. DB-Verbindung + aktuelle Migrations-Version
4. Alle kritischen Env-Variablen auf Render gesetzt
5. Smoke-Test-Skript erfolgreich

---

## Prompt zum Einfügen

```
Pflicht-Check:
git remote -v && git branch --show-current

Erwartetes Ergebnis:
- origin → nachhaltika-arch/Claude-Code
- branch → claude/kompagnon-automation-system-FapM9

Falls eines davon nicht stimmt → SOFORT STOPPEN.

Falls alles stimmt:

1. Smoke-Test ausführen
   python3 /home/user/Claude-Code/kompagnon/backend/scripts/smoke_test.py

2. Den Markdown-Report aus stdout zeigen.

3. Folgende Env-Variablen MÜSSEN auf dem Render Backend Service
   `claude-code-znq2` gesetzt sein:
   - ANTHROPIC_API_KEY
   - NETLIFY_API_TOKEN
   - GOOGLE_PAGESPEED_API_KEY
   - SMTP_HOST
   - SMTP_USER
   - SMTP_PASSWORD
   - SMTP_SENDER_EMAIL
   - DATABASE_URL

   Die Existenz wird vom /api/health/full Endpunkt geprüft. Wenn ein
   Check rot ist, klare Anweisung zurückgeben:
   "Bitte in Render.com → Service claude-code-znq2 → Environment
    folgende Variable setzen: <NAME>"

4. Migration-Status prüfen
   Im Self-Check-Report steht migrations.detail im Format
   "v<DB_VERSION> applied (code expects v<CODE_VERSION>)".
   Wenn DB_VERSION < CODE_VERSION:
   - Liste der pending Versionen aus
     /home/user/Claude-Code/kompagnon/backend/db_migrations.py
     (MIGRATIONS-Konstante) anzeigen
   - Bestätigung von mir einholen, ob ich auf Render einen
     manuellen Restart triggern soll, damit run_migrations() neu läuft

5. Letzte 5 Commits zeigen
   git log --oneline -5

6. Working Tree Status
   git status

7. Berichte am Ende:
   - Status: ok | degraded | error
   - Konkrete nächste Aktion (oder "nichts zu tun")
   - Falls Fehler: welcher Endpunkt, welche Env-Variable, welche
     Migration

WICHTIG:
- KEINEN Code committen, bevor ich es ausdrücklich sage
- KEINEN Push machen
- Nur lesen + berichten, nicht ändern
```

---

## Erwartete Ausgabe (Beispiel)

Wenn alles ok ist, sollte der Smoke-Test einen Markdown-Report wie diesen
zurückgeben:

```
# KOMPAGNON Smoke-Test

**Backend:** `https://claude-code-znq2.onrender.com`

## Endpunkt-Checks

| Endpunkt | Status | Zeit | Hinweis |
|---|---|---|---|
| `/api/ping` | ok (200) | 0.42s |  |
| `/api/health` | ok (200) | 0.18s |  |
| `/api/health/full` | ok (200) | 0.31s |  |

## Self-Check — Status: **ok**

| Subsystem | OK | Detail |
|---|---|---|
| **db** | ok | connected |
| **migrations** | ok | v11 applied (code expects v11) |
| **anthropic** | ok | ANTHROPIC_API_KEY set |
| **netlify** | ok | NETLIFY_API_TOKEN set |
| **smtp** | ok | all 4 SMTP env vars set |

### Info
- **routes:** 287
- **git_sha:** 3369edd
- **python_env:** production
```

## Häufigste Fehler

### `netlify.ok = false → NETLIFY_API_TOKEN missing`
Der Code für die Netlify-Integration ist live (Bug #1 Fix `04f00de`),
aber die Env-Variable wurde noch nicht in Render gesetzt.
- Lösung: Render Dashboard → Service `claude-code-znq2` → Environment
  → Add Environment Variable → Key: `NETLIFY_API_TOKEN`,
  Value: Token aus netlify.com User Settings → Personal access tokens

### `migrations.ok = false → v10 applied, but code expects v11`
Die Migration v11 (Ground Page `ki_content` Spalte aus Commit `9deaff9`)
ist noch nicht durchgelaufen. Render führt Migrations beim Start aus —
ein manueller Restart triggert sie neu.
- Lösung: Render Dashboard → Service → Manual Deploy → "Clear build
  cache & deploy" oder Logs prüfen ob `run_migrations()` Fehler wirft

### `db.ok = false`
DB-Connection Problem. Sehr selten, meist Render Postgres Cold-Start
oder DATABASE_URL nicht gesetzt.
- Lösung: Render Dashboard → Postgres-Service Status prüfen → ggf.
  einen kostenlosen Re-Run anstoßen

### Backend gar nicht erreichbar (alle Endpunkte 502/Timeout)
- Render Free-Tier hat 30-60s Cold Start beim ersten Request nach
  ~15 Minuten Inaktivität. Smoke-Test hat 30s Timeout — bei Cold
  Start nochmal ausführen
- Falls dauerhaft tot: Render Dashboard → Logs → letzter Build erfolg
  reich? Falls Build failed → Stack-Trace lesen

---

## Verwandte Dateien
- `kompagnon/backend/scripts/smoke_test.py` — Standalone-Test-Skript
- `kompagnon/backend/main.py` — Implementation `/api/health/full`
- `kompagnon/backend/db_migrations.py` — `MIGRATIONS`-Konstante
- `CLAUDE.md` (Repo-Root) — Branch-/Repo-Regeln für jede Session
