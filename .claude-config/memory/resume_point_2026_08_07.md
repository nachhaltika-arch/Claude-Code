---
name: wiederaufnahme-2026-08-07-stand-abend
description: "Testfundament gebaut (35 Tests), Deploy-Gate über GitHub Actions scharf, Versionen gesperrt, 4 stille Fehler gefunden; PR #34 gemergt, Produktiv-Deploy hing an npm-Timeout"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4c575dc8-1f76-4389-a3f1-5d8faa173ff7
  modified: 2026-08-07T20:42:21.725Z
---

**Why:** Erster Arbeitstag nach drei Monaten Pause (letzter Commit war 2026-05-09).
Der Tag begann mit einer Bestandsanalyse und endete mit einem Testfundament plus
kontrolliertem Deploy. Vier Fehler kamen ans Licht, die alle Monate unbemerkt
liefen — jeweils weil ein Fehler weggefangen wurde statt gemeldet.

**How to apply:** Morgen früh mit „Produktiv verifizieren" starten (Punkt 1 unten).
Die Reihenfolge darunter ist bewusst nach Wirkung sortiert. Vor allem: NICHT neue
Features beginnen, bevor Produktiv nachweislich auf dem neuen Stand ist.

---

## Erledigt heute

**Vier echte Fehler gefunden und behoben** — alle vorher unbekannt:

| Fehler | Wirkung | seit |
|---|---|---|
| `layout-presets` hinter `/{slug}` | KI-Layout-Selector dauerhaft leer, 54 Presets unerreichbar | 2026-05-07 |
| `send-email` hinter `/{lead_id}` | Newsletter-Versand scheiterte an int-Validierung (422) | unbekannt |
| CORS für `websprint.kompagnon.eu` | Website-Check der Landingpage brach bei jedem Besucher ab | 2026-06 |
| `/api/audit/lead/{id}/latest` | Route existiert nicht — Editor kannte nie das Audit-Ergebnis | unbekannt |

**Muster dahinter:** Dreimal war die Ursache ein stiller Fehlerfang —
`.catch(() => {})`, `r.ok ? … : []`, geschluckte 404er. Das ist der Grund, warum
Fehler hier so lange überleben. Als eigener Punkt für die Lückenliste vorgemerkt.

**Testfundament (vorher: null):**
- 24 Backend-Tests (pytest, gegen Wegwerf-Postgres, ~2,5 s)
  — darunter ein generischer Test gegen verdeckte Routen, der den zweiten Fehler
  oben selbst gefunden hat
- 11 Browser-Tests (Playwright, Chromium, ~17 s lokal / 22 s CI)
- `backend/tests/seed_e2e.py` bringt ein Projekt in einen entsperrten Zustand —
  ohne das ist der Editor nicht testbar

**Deploy-Kette:** Render-Auto-Deploy soll abgelöst werden durch GitHub Actions.
Sechs Prüfjobs, dann erst Deploy über die Render-API mit Statusabfrage bis `live`.

**Versionen gesperrt:** 24 von 26 Backend-Paketen waren ungepinnt. Jetzt
`requirements.in` (direkt) + `requirements.txt` (61 Pakete gelockt).
Sprung dabei: fastapi 0.136→0.141, starlette 1.0→1.4, anthropic 0.100→0.121.

**Lokale Entwicklung:** `bash scripts/dev.sh` startet alles gegen lokale Postgres.
Verweigert den Start gegen entfernte DB (Schutz gegen Migrationen auf Render).

**Rulesets aufgeräumt:** `protect-main` hatte eine Regel „Restrict updates", die
jeden Merge blockierte — entfernt. Die zwei neuen Prüfjobs als Pflicht ergänzt
(jetzt sechs). Leeres Ruleset `MAIN Productiv` gelöscht.
Sicherungen im Scratchpad der Sitzung vom 07.08.

---

## Offen — morgen früh in dieser Reihenfolge

**1. Produktiv verifizieren (zuerst!)**
PR #34 wurde 20:35 UTC gemergt, aber der Produktiv-Deploy wurde **übersprungen**:
Der E2E-Job scheiterte an `npm error code ETIMEDOUT` beim Frontend-`npm ci` — ein
Netzwerkproblem der CI, kein Codefehler. Neustart des Jobs lief am Abend noch.
→ Prüfen ob Produktiv jetzt auf dem neuen Stand ist. Wenn nicht: Job erneut starten.
→ Danach testen: Website-Check auf `websprint.kompagnon.eu`, Layout-Selector im
  Tool, `/embed/audit-widget.html` auf dem Produktiv-Frontend.

**2. Embed-Widget-Auslieferung klären**
Auf Staging liefert `/embed/audit-widget.html` einen 301 auf `/embed/audit-widget`
und dann die React-App statt des Widgets — `npx serve -s build` schneidet `.html`
ab. Produktiv ist eine Static Site, verhält sich möglicherweise anders. Erst
messen, dann fixen (`--no-clean-urls` wäre die Lösung für Staging).

**3. Auto-Deploy in Render abschalten**
Für `kompagnon-backend` und `kompagnon-frontend` (Produktiv): Settings →
Build & Deploy → Auto-Deploy auf Off. Erst danach ist der Torwächter wirklich
der einzige Weg. Staging folgt dem Blueprint automatisch.

**4. CI robuster machen**
Der E2E-Job installiert die Frontend-Abhängigkeiten ein zweites Mal (nach
`frontend-build`) und verdoppelt damit die Angriffsfläche für Registry-Ausfälle.
Besser: Build-Artefakt aus `frontend-build` per upload/download-artifact
weiterreichen. Spart ~2 min und einen Fehlerpfad.

**5. Danach frei wählbar**
- Browser-Tests erweitern (Wireframe, Style-Guide-Freigabe, Design-View) —
  braucht ein weiterreichendes Seed
- Projekt-Assistent umsetzen (16 Anforderungen geklärt, siehe
  `docs/projekt-assistent-anforderungen.md`)
- Brevo prüfen: `brevo-python` ist installiert, das Backend meldet trotzdem
  „SDK nicht installiert" — vermutlich abweichender Importname, Newsletter
  dauerhaft deaktiviert
- L-34 Oregon-Region entscheiden (Produktiv-Backend US-West, DB Frankfurt)

---

## Wichtige Dokumente

- `docs/soll-ist-analyse-2026-08-07.md` — 12 Bereiche, 35 Lücken priorisiert
- `docs/projekt-assistent-anforderungen.md` — 16 Entscheidungen, umsetzungsreif
- `docs/local-dev-and-deploy.md` — lokale Umgebung + Deploy-Pipeline
- `kompagnon/e2e/README.md` — warum das Seed nötig ist

## Zusammenarbeit

David will am Programm arbeiten, nicht an Prozess (siehe
[[feedback_always_recommend]]). Ich übernehme Commits, Push, PR, Deploy-Überwachung.
Bei ihm bleiben nur Merge und Zugangsdaten.
