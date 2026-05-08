<!--
  Dieses Template erscheint automatisch als Body jeder neuen PR. Bei einer
  PR staging → main IMMER die Smoke-Checkliste durchgehen, bevor merged
  wird. Selbstverpflichtung — keine Branch-Protection, aber ohne Check
  kein Merge.

  Bei kleinen reinen Doc-/CI-/Tooling-PRs reicht es, die nicht zutreffenden
  Sections zu streichen und das oben kurz zu vermerken.
-->

## Was ändert diese PR

<!-- 1-3 Bullets. Was, warum. Tickets/Memory-Refs falls vorhanden. -->

-

## Smoke-Test (~10 min auf Staging)

> Test-URLs:
> - Frontend: https://kompagnon-frontend-staging.onrender.com
> - Backend:  https://kompagnon-backend-staging.onrender.com

### 0 · Build & Deploy (1 min)
- [ ] CI auf dieser PR ist grün (alle 4 Jobs: Backend lint, Backend smoke, Frontend build, Gitleaks)
- [ ] Render-Staging-Deploy für den Head-Commit ist `live` (Render-Dashboard oder MCP)
- [ ] `https://kompagnon-backend-staging.onrender.com/health` → 200 OK
- [ ] Frontend lädt unter 3 s, kein White-Screen

### 1 · Auth & Session (1 min)
- [ ] Login mit Test-Account funktioniert
- [ ] Reload nach Login behält die Session (kein erneuter Login-Prompt)
- [ ] Logout funktioniert, leitet auf Login-Page

### 2 · Customer-Editor — Critical Path (4 min)
Mindestens ein bestehendes Projekt komplett durchgehen.

**Sitemap-Tab**
- [ ] Pages werden angezeigt, Tree-Struktur stimmt
- [ ] Page hinzufügen via Topbar funktioniert (gelber KI-Vorschlag-Button + grauer "Erste Seite")
- [ ] Drag & Drop einer Page persistiert nach Reload
- [ ] "Zu Wireframe →" wechselt korrekt zum Wireframe-Tab

**Wireframe-Tab**
- [ ] Pages-Storyboard oben zeigt Mini-Previews
- [ ] Active-Page wird hervorgehoben (Dark Teal Header)
- [ ] Block-Liste rendert mit Live-Preview
- [ ] "+ Block hinzufügen" öffnet Slide-In rechts
- [ ] Block tauschen, Variante (KI), Edit-Slot funktionieren
- [ ] Drag-Reorder eines Blocks persistiert nach Reload
- [ ] "Zu Style Guide →" wechselt korrekt

**Style-Guide-Tab**
- [ ] Live-Preview rendert mit aktueller Palette
- [ ] Color-Tile-Klick öffnet Color-Picker
- [ ] Typography-Scale-Select wechselt Schrift-Größen in der Preview
- [ ] Keyboard-Shortcuts: `C`/`T`/`U`/`SPACE` würfeln korrekt
- [ ] Device-Toggle (Desktop/Tablet/Mobile) verändert Preview-Breite
- [ ] "Freigabe an Kunden" persistiert (Reload zeigt "✓ freigegeben")

**Design-Tab**
- [ ] Lock-Screen erscheint, wenn Style-Guide noch nicht freigegeben
- [ ] Live-Vorschau rendert nach Freigabe
- [ ] Sitemap-Tree links navigiert korrekt
- [ ] Breadcrumb in der Vorschau zeigt aktuelle Page
- [ ] HTML-Export lädt eine `.html`-Datei runter

### 3 · Optik & Doc-Konformität (2 min)
- [ ] Höchstens **eine** Primary-Aktion pro sichtbarem Screen
- [ ] Gelb erscheint höchstens **1×** pro sichtbarem Screen (für die wichtigste Aktion)
- [ ] Body-Text wirkt nicht zu eng (line-height 1.75 spürbar)
- [ ] Buttons sitzen visuell auf dem 8 px-Raster (keine schiefen 9 px / 14 px-Padding-Sprünge)
- [ ] Dark Teal #004F59 dominiert, nicht Mid Teal

### 4 · Links & Navigation (1 min)
- [ ] Sidebar-Links und Top-Tabs gehen alle ohne 404 / Layout-Shift
- [ ] Externe Links (z. B. Render, Netlify) öffnen in neuem Tab
- [ ] Breadcrumbs zeigen den korrekten Pfad

### 5 · Datenbank-Persistenz (1 min)
- [ ] Eine Edit-Aktion machen → Reload → Stand ist da (Sitemap-Page, Wireframe-Block, oder Style-Guide-Override)
- [ ] Browser-Tab schließen → neu öffnen → Daten sind da

### 6 · Browser-Konsole (30 s)
- [ ] DevTools öffnen → Console: keine roten Errors
- [ ] Network-Tab: keine 404 / 500 für Assets oder API-Calls

---

## Falls etwas kaputt ist

- Render-Staging-Logs prüfen (Render-Dashboard oder `mcp__render__list_logs`)
- Frontend-Build-Logs in CI prüfen
- Backend-Health-Endpoint zeigt mehr Details: `/health/detail` (falls vorhanden) oder Logs
- Bei DB-Connectivity-Issues: `mcp__render__query_render_postgres` gegen `kompagnon-staging-db`

## Bestätigung

- [ ] Smoke-Test komplett durchgegangen, alle Boxes oben hat tatsächlich geprüft (nicht nur abgehakt)
- [ ] Bekannte offene Punkte sind in der PR-Beschreibung dokumentiert oder als TODO gemerkt
