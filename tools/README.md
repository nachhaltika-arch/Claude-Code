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
