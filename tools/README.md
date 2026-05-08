# tools/

Einmalige + wiederholt nutzbare Helper-Scripts für die KOMPAGNON-Library.

## neutralize-library.js

One-shot Tailwind-Color-Stripper. Ersetzt Brand-Farben in allen
Library-HTML-Files durch Gray-Equivalente (Wireframe-Style).

```
node tools/neutralize-library.js          # Dry-Run, zeigt Diff
node tools/neutralize-library.js --write  # Files überschreiben
```

Idempotent — Re-Runs sind no-op wenn alles schon gray ist.
Ursprünglicher Run am 2026-05-07: 41 Files / 267 Replacements.

## batch-generate-components.js + batch-import-components.js

**Bulk-Generator** für den Component-Designer (Task A Weg 2).

Loopt über alle Layout-Presets (`/api/components/layout-presets`)
und generiert N Varianten pro Preset via Sonnet 4.6. Resultate
landen als JSON-Files in `tools/generated/` zur manuellen Review,
**nicht direkt in der DB**.

### Workflow

1. **Plan checken** (kein API-Call):
   ```
   node tools/batch-generate-components.js --dry-run
   ```

2. **Generieren** (mit Auth-Token von einem KAS-Admin-Login):
   ```
   export API_URL=https://kompagnon-backend-staging.onrender.com
   export API_TOKEN="dein-bearer-token"
   node tools/batch-generate-components.js --per-preset 3 --industry shk
   ```

   Optionen:
   - `--per-preset N` — Anzahl Varianten pro Preset (default 5)
   - `--presets ID,ID` — nur bestimmte Presets generieren
   - `--categories C,C` — nur bestimmte Kategorien (HERO, NAV, ...)
   - `--industry KEY` — Branchen-Kontext (shk, kfz, gala, ...)
   - `--style minimal|elegant|bold` — Layout-Dichte
   - `--concurrency N` — parallele Jobs (default 2, max ~5 sinnvoll)
   - `--out DIR` — Output-Verzeichnis (default `tools/generated/`)

   **Kosten-Schätzung:** ~$0.02/Component bei Sonnet 4.6 mit
   8000 max_tokens. 53 Presets × 5 Varianten ≈ ~$5–7.

   **Laufzeit:** ~30–60 min bei Concurrency 2 (KI-Calls sind je
   30–60s; mit höherer Concurrency proportional schneller, aber
   Rate-Limits beachten).

3. **Review** — jede `tools/generated/{preset}-v{N}.json` öffnen,
   `result.html_template` prüfen (Tailwind-Validität, Wireframe-
   Stil-Compliance, kein Brand-Code geleakt). Schlechte Files
   einfach löschen.

4. **Import in DB**:
   ```
   node tools/batch-import-components.js --slug-prefix kasai-
   ```

   Optionen:
   - `--slug-prefix PFX` — Slug-Prefix für die neuen Eintraege
     (default `ai-`). Verhindert Kollisionen mit existierenden
     KAS-/HyperUI-Slugs.
   - `--skip-existing` — bei Slug-Konflikt überspringen statt
     erroren.

   Importierte Components erhalten den Tag `kas-ai-batch` und
   können später per Filter im Component-Manager identifiziert
   werden.

### Sicherheits-Hinweise

- **Nicht auf Produktiv-DB ausführen** ohne vorher den Output
  geprüft zu haben. Default-Setup zielt auf den Backend-URL aus
  der Env-Variable.
- Der `kas-ai-batch`-Tag erlaubt späteren Bulk-Delete falls die
  Generation nicht den Erwartungen entspricht.
- Sonnet 4.6 hält sich i.d.R. an `_WIREFRAME_CONSTRAINTS`
  (gray-only), aber Stichproben sind Pflicht.
