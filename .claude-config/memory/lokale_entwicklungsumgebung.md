---
name: lokale-entwicklungsumgebung
description: Wie die lokale KOMPAGNON-Instanz startet und welche Zugänge dort gelten
metadata:
  type: reference
---

**Start** (beides braucht es):

    kompagnon/backend:   venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
    kompagnon/frontend:  BROWSER=none PORT=3000 npx react-scripts start

Oberfläche http://localhost:3000, Backend http://localhost:8000 (`/docs`).
Datenbank `kompagnon_local`, gesetzt in `backend/.env`.

**Zugänge** (nur lokal, am 21.08.2026 neu gesetzt und einzeln geprüft):

| Konto | Passwort | Rolle |
|---|---|---|
| `admin@kompagnon.local` | `lokal-admin-2026` | admin |
| `auditor@kompagnon.local` | `lokal-auditor-2026` | auditor |
| `nutzer@kompagnon.local` | `lokal-nutzer-2026` | nutzer |
| `kunde@kompagnon.local` | `lokal-kunde-2026` | kunde |
| `e2e-admin@kompagnon.local` | `e2e-test-passwort` | admin (aus `tests/seed_e2e.py`) |

**Zwei Fallen beim Aufsetzen:**

* Die lokale Datenbank hängt hinter den Migrationen zurück. `main` zu
  importieren genügt **nicht** — `main._run_migrations()` muss ausdrücklich
  laufen, sonst fehlt z. B. `leads.lifecycle_phase` und der E2E-Seed bricht ab.
* `app.routes` liefert unter Starlette 1.4 nur ~71 Einträge. Wer Routen zählen
  will, nimmt `app.openapi()['paths']` (~383).

**Daten:** Betrieb 1 „E2E Testbetrieb Heizung GmbH" (ein Projekt mit
Wireframe-Daten, zwei Sitemap-Seiten: Impressum, Datenschutz), Betrieb 2 „Demo
Mustermann Sanitaer" (leer). Für Design-Ansichten zu dünn.
