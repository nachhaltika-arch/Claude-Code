---
name: wiederaufnahme-2026-08-07-stand-abend
description: "Testfundament gebaut (35 Tests), Deploy-Gate über GitHub Actions scharf, Versionen gesperrt, 4 stille Fehler gefunden; PR #34 gemergt und produktiv verifiziert — Website-Check und Embed-Widget wieder funktionsfähig"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4c575dc8-1f76-4389-a3f1-5d8faa173ff7
  modified: 2026-08-07T20:53:24.736Z
---

**Why:** Erster Arbeitstag nach drei Monaten Pause (letzter Commit war 2026-05-09).
Der Tag begann mit einer Bestandsanalyse und endete mit einem Testfundament plus
kontrolliertem Deploy. Vier Fehler kamen ans Licht, die alle Monate unbemerkt
liefen — jeweils weil ein Fehler weggefangen wurde statt gemeldet.

**How to apply:** Produktiv ist verifiziert (Abschnitt unten) — morgen früh mit
Punkt 1 der Offen-Liste starten: Auto-Deploy in Render abschalten. Die Reihenfolge
ist nach Wirkung sortiert.

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

## Produktiv-Stand am Abend (nach dem Merge erledigt)

PR #34 gemergt 20:35 UTC. Der erste Deploy-Versuch wurde **übersprungen**, weil der
E2E-Job an `npm error code ETIMEDOUT` beim Frontend-`npm ci` scheiterte — ein
Netzwerkproblem der CI, kein Codefehler. Nach Neustart des Jobs lief alles durch:

```
▸ Ziel: Produktiv
✓ Backend: live   ✓ Frontend: live   ✓ Produktiv vollständig deployt
```

Verifiziert direkt danach:

| Prüfung | vorher | jetzt |
|---|---|---|
| Backend `/health` | 200 | 200 in 1,2 s |
| CORS `websprint.kompagnon.eu` | 400, kein allow-origin | **200 mit allow-origin** |
| `/embed/audit-widget.html` | 404 | **200, 15.021 Bytes, echtes Widget** |

→ Der Website-Check der Landingpage funktioniert wieder (war seit Juni tot).
→ **Embed-Widget produktiv in Ordnung:** Die Static Site liefert `.html` direkt aus.
  Der 301-Umweg in die React-App ist ein reines Staging-Problem von `npx serve`.
  Produktiv braucht KEINEN Fix — nur Staging sollte mit `--no-clean-urls`
  angeglichen werden, damit beide Umgebungen sich gleich verhalten.

**Noch offen zur Produktiv-Prüfung:** Layout-Selector im Tool (braucht Anmeldung,
im Browser nachholen) und ein echter Durchlauf des Website-Checks mit einer
richtigen Domain, um die Audit-Kette zu sehen.

---

## Offen — morgen früh in dieser Reihenfolge

**1. Auto-Deploy in Render abschalten**
Für `kompagnon-backend` und `kompagnon-frontend` (Produktiv): Settings →
Build & Deploy → Auto-Deploy auf Off. Erst danach ist der Torwächter wirklich
der einzige Weg. Staging folgt dem Blueprint automatisch.

**2. CI robuster machen**
Der E2E-Job installiert die Frontend-Abhängigkeiten ein zweites Mal (nach
`frontend-build`) und verdoppelt damit die Angriffsfläche für Registry-Ausfälle.
Besser: Build-Artefakt aus `frontend-build` per upload/download-artifact
weiterreichen. Spart ~2 min und einen Fehlerpfad.

**3. Danach frei wählbar**
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
