# Browser-Tests

Playwright gegen eine laufende Anwendung. Ersetzt den manuellen Smoke-Test aus
der PR-Vorlage Schritt für Schritt.

## Lokal ausführen

```bash
bash scripts/dev.sh                            # Backend 8000, Frontend 3000
cd kompagnon/backend && ./venv/bin/python -m tests.seed_e2e
cd ../e2e && npm install && npx playwright install chromium
npm test
```

`npm run test:headed` zeigt den Browser mit, `npm run report` öffnet den Bericht
nach einem Lauf.

## Das Seed ist Voraussetzung

`backend/tests/seed_e2e.py` legt ein Admin-Konto und ein Projekt an, in dem
Phase 1 lückenlos abgeschlossen ist.

Das ist kein Beiwerk: Der Editor gibt immer nur den nächsten Schritt nach der
letzten **lückenlosen** Kette abgeschlossener Schritte frei. Fehlt ein einziger
Schritt in der Mitte — etwa `zugangsdaten`, für das es gar keine Heuristik gibt —
bleiben Sitemap, Wireframe und Style Guide gesperrt. Genau daran scheiterte der
manuelle Smoke-Test am 2026-08-07: Alle drei Staging-Projekte standen in Phase 1,
der interessante Teil der Anwendung war unerreichbar.

## Was geprüft wird

| Datei | Inhalt |
|---|---|
| `anmeldung.spec.js` | Login, Sitzung nach Reload, falsches Passwort, Umleitung ohne Anmeldung |
| `komponenten-bibliothek.spec.js` | Liste lädt, Layout-Selector gefüllt, Kategoriewechsel wirkt |
| `editor.spec.js` | Projekt sichtbar, vier Views, Sitemap nicht gesperrt, Fortschritt |

In jedem Test läuft ein Konsolen-Beobachter mit. Er hat beim ersten Lauf einen
Fehler gefunden, den niemand sehen konnte: Der Editor rief
`/api/audit/lead/{id}/latest` auf — eine Route, die es nie gab. Der Aufruf endete
in einem leeren `.catch()`, das Audit-Ergebnis blieb dem Editor dauerhaft unbekannt.

## Bewusste Festlegungen

**Nur Chromium.** Die Tests sollen Regressionen in der Anwendung finden, nicht
Browser-Unterschiede. Drei Engines verdreifachen die Laufzeit ohne Erkenntnisgewinn
für ein internes Werkzeug.

**Keine Wiederholung bei Flakiness.** `retries: 0` — ein wackliger Test soll
auffallen, nicht durch einen zweiten Versuch verschwinden.

## Noch nicht abgedeckt

Wireframe-Bearbeitung, Style-Guide-Freigabe, Design-View und HTML-Export. Dafür
muss das Seed weiter reichen (Sitemap-Seiten, freigegebener Style Guide).
