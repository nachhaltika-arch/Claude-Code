# Tools

## relume-bulk-downloader.user.js

Tampermonkey-Userscript um Relume's gesamte Komponenten-Bibliothek
in einem Lauf als HTML-Files herunterzuladen — Voraussetzung fuer den
Bulk-Import in die KAS Komponenten-Bibliothek.

### Setup (einmalig, ~3 min)

1. **Tampermonkey** Browser-Extension installieren (Chrome / Firefox / Edge).
2. **Auto-Downloads erlauben** auf relume.io:
   Chrome → `chrome://settings/content/automaticDownloads` →
   "Automatische Downloads zulassen" → `https://www.relume.io` hinzufuegen.
   (Sonst muss bei jedem 2. File geklickt werden.)
3. **Standard-Download-Folder** auf einen leeren Ordner setzen, z.B.
   `C:\Users\DavidVaeth\Desktop\relume-raw\`. Sonst landet alles in
   `Downloads\` und muss spaeter umverteilt werden.
4. Inhalt von `relume-bulk-downloader.user.js` kopieren →
   Tampermonkey-Dashboard → "Neues Skript" → einfuegen → Speichern (Strg+S).
5. Auf relume.io eingeloggt sein (sonst kommt kein HTML im Tab).

### Workflow

1. Geh auf `https://www.relume.io/react/components` (oder eine Kategorie-
   Seite wie `/react-categories/navbars`). Das Floating-Panel **KAS · Relume
   Walker** erscheint unten rechts.
2. **"➕ Sichtbare Links zur Queue"** klicken — sammelt alle Component-Links
   der aktuellen Seite in die Queue. Bei Bedarf weiter zu anderen
   Kategorie-Seiten und nochmal sammeln; Queue wird kumuliert + dedupliziert.
3. **"▶ Walker starten"** klicken — Browser navigiert automatisch durch
   alle Pages, scraped jeden HTML-Tab, lädt als File runter
   (`relume-{category}-{slug}.html`), wartet 3 sec, naechste Page.
4. Bei Pause/Crash einfach Tab schliessen und neu oeffnen — der State
   ueberlebt (GM-Storage).

### Status-Anzeige

- **Queue** — noch zu scrapende URLs
- **Done** — erfolgreich runtergeladene slugs
- **Fail** — Slugs bei denen kein Code-Block / Download-Fehler

Mit "📋 Failed anzeigen" kannst du die Liste der Fehlschlaege kopieren
und manuell nacharbeiten.

### Tuning

Wenn der Walker zu schnell laeuft (Anti-Bot-Block oder fehlende Code-Blocks
durch React-Lazy-Render), die Konstanten oben im Skript erhoehen:

- `NAV_DELAY_MS = 3000` — Pause zwischen Component-Pages
- `TAB_DELAY_MS = 1500` — Wartezeit nach HTML-Tab-Klick

Bei 1541 Komponenten:
- 3000 ms / Page → ~80 min
- 5000 ms / Page → ~130 min

### Sicherheit

Das Skript ist **read-only** auf relume.io — es klickt nur den HTML-Tab,
liest den Code, navigiert. Keine Form-Submissions, kein Auth-Handling.
GM-Storage liegt lokal in Tampermonkey, nichts geht an externe Server.

---

## import-relume-bulk.mjs

Node-Script das nach dem Walker-Lauf alle gesammelten HTML-Files
durchnudelt: Token-Mapping, Slot-Detection, schreibt die fertigen
Snippets ins Repo, generiert/updated index.json.

### Usage

```bash
node tools/import-relume-bulk.mjs <inputDir> [--smart] [--dry-run] [--limit=N]
```

- `<inputDir>` — Pfad zum Walker-Output (z.B. `C:/Users/DavidVaeth/Desktop/relume-raw`)
- `--smart` — Slot-Detection ueber Claude Haiku 4.5 (semantisch).
  Braucht `ANTHROPIC_API_KEY` env var. Kostet ~$0.001 pro Snippet,
  bei 1524 also ~$1.50.
- `--dry-run` — Schreibt nichts, zeigt nur was passieren wuerde.
- `--limit=N` — Verarbeitet nur die ersten N Files (zum Testen).

### Beispiele

Test-Lauf auf 5 Files ohne Schreiben:

```bash
node tools/import-relume-bulk.mjs C:/Users/DavidVaeth/Desktop/relume-raw --dry-run --limit=5
```

Smart-Mode auf 10 Files (zum Pricing testen):

```bash
$env:ANTHROPIC_API_KEY="sk-ant-..."; node tools/import-relume-bulk.mjs C:/Users/DavidVaeth/Desktop/relume-raw --smart --limit=10
```

Voller Lauf mit Pattern-Mode:

```bash
node tools/import-relume-bulk.mjs C:/Users/DavidVaeth/Desktop/relume-raw
```

### Was das Script macht

1. Liest `relume-{category}-{slug}.html` aus dem Input-Folder.
2. Cleanup: alle Relume-Tokens (`border-border-primary` etc.) auf
   Standard-Tailwind gemappt; `id="relume"` raus; Cloudfront-Logo durch
   `{{logo_text}}`-Slot ersetzt.
3. Slot-Detection:
   - **Pattern**: `<h1>/<h2>` -> `headline`/`subheadline`,
     Buttons mit "Button"-Text -> `cta_label_N`,
     Links mit "Link One/Two/..." -> `nav_link_N`.
   - **Smart**: Claude Haiku schlaegt Slots semantisch vor
     (`hero_headline`, `cta_primary`, `feature_title_1` ...).
4. Schreibt fertige HTML-Files nach
   `kompagnon/frontend/src/components/library/external/relume/{slug}.html`.
5. Merged `index.json` — manuell kuratierte Eintraege bleiben unangetastet
   (`relume-navbar-1/-2/-3`).

### Nach dem Lauf

`seed_component_library.py` triggert sich nicht selbst — du musst noch:

1. `LIBRARY_VERSION_LOG` in `kompagnon/backend/seeds/seed_component_library.py`
   um einen Eintrag erweitern (z.B. `"2026-05-XX.X: bulk-import N relume sections"`)
2. Commit + Push -> Render redeployt Backend -> Seed laeuft -> alle Snippets in DB.

Erwartete Laufzeiten bei 1524 Snippets:
- Pattern-Mode: ~10 Sekunden
- Smart-Mode: ~25 min (1500 Haiku-Calls, ~1 sec each)
