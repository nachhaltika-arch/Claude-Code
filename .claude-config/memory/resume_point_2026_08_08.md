---
name: wiederaufnahme-2026-08-08
description: "CI gegen Netzausfälle gehärtet, Brevo komplett neu angebunden (war seit Monaten tot), L-36 abgeschlossen — 67 leere catch-Blöcke beseitigt; zwei Render-Dashboard-Aufgaben offen bei David"
metadata: 
  node_type: memory
  type: project
  originSessionId: f9bdd03e-01fd-462a-92bd-7d4e05a67b28
  modified: 2026-08-08T17:13:26.150Z
---

**Why:** Zweiter Arbeitstag nach der Pause. Der Tag folgte einem Muster: jede
Baustelle brachte weitere stille Fehler ans Licht, die nie gemeldet wurden.
Insgesamt neun Speicher-Aktionen gefunden, die Erfolg anzeigten, ohne den
Status je geprüft zu haben.

**How to apply:** Alles ist auf `staging` deployt und grün. Nächste Sitzung mit
der Offen-Liste unten starten — Punkt 1 und 2 liegen bei David, nicht bei mir.

---

## Erledigt

**CI gegen Netzausfälle** — `scripts/ci-retry.sh` wiederholt netzabhängige
Schritte 3× mit 15 s Abstand (nur Installationen/Downloads, nie Tests). Grund
war der übersprungene Deploy vom 07.08. wegen `npm ci`-ETIMEDOUT.
Verworfen: das in der Vornotiz geplante Build-Artefakt von `frontend-build`
nach `e2e` — beide Jobs backen unterschiedliche API-URLs, es bräuchte einen
zweiten Build, und die Serialisierung macht aus 3 parallelen ~6 serielle
Minuten.

**Brevo neu angebunden** — `import brevo_python` schlug immer fehl: das Paket
`brevo-python` liefert das Modul `brevo`. Ein Namenswechsel hätte nichts
gebracht, weil brevo-python ab v4 eine völlig andere Schnittstelle hat. Jetzt
direkt über httpx gegen die REST-API v3, SDK aus den Requirements raus.
Mitgefunden: Statistik las `open_rate`/`click_rate` — bei Brevo heißt es
`opensRate`, eine Klickrate gibt es gar nicht → Analytics war immer leer.

**L-36 abgeschlossen** — 67 leere catch-Blöcke in 36 Dateien, jetzt null.
Neuer Helfer `frontend/src/utils/apiRequest.js`:
- `apiRequest` wirft, `loadJson` meldet + Ersatzwert, `saveJson` meldet +
  true/false + `onError` fürs Zurücksetzen
- 404 gilt per Voreinstellung als legitimer Leerzustand (`emptyOn`)
- Toasts tragen eine ID, damit ein kaputter Endpunkt seine eigene Meldung
  ersetzt statt den Bildschirm zuzupflastern
- `quiet` für bewusst stille Fälle — Keepalive, Brotkrumen, und die
  Passwort-vergessen-Anfrage (darf nicht verraten, ob ein Konto existiert)

**Testlage:** 39 Backend (pytest), 15 Frontend (jest, neu — hängen im
bestehenden `frontend-build`-Job, kein zweites `npm ci`), 11 Browser
(Playwright).

**Nebenbefund:** Die lokale Backend-venv steht auf FastAPI 0.136, gepinnt ist
0.141. Tests laufen gegen beide grün, aber lokal wird nicht das getestet, was
produktiv läuft. `len(app.routes)` unterscheidet sich dadurch stark (470 vs 63)
— das ist ein Zähl-Artefakt neuerer Starlette-Versionen, kein Fehler.

---

## Offen — nächste Sitzung

**1. Render Auto-Deploy abschalten (David)** — `kompagnon-backend` und
`kompagnon-frontend` (Produktiv): Settings → Build & Deploy → Auto-Deploy Off.
Ich komme nicht ran: Render-MCP antwortet `unauthorized`, kein API-Key lokal.
Erst danach ist die CI wirklich der einzige Weg nach Produktiv.

**2. `BREVO_API_KEY` in Render prüfen (David)** — Staging und Produktiv. Ohne
Schlüssel meldet der Newsletter jetzt sauber 503 statt der irreführenden
SDK-Meldung, senden kann er trotzdem nicht.

**3. Danach frei wählbar**
- Projekt-Assistent umsetzen (16 Anforderungen geklärt, siehe
  `docs/projekt-assistent-anforderungen.md`) — der größte offene Wertbeitrag
- Browser-Tests erweitern (Wireframe, Style-Guide-Freigabe, Design-View) —
  braucht ein weiterreichendes Seed
- L-38: der Mai-Audit hakt „Brevo-Stats ✅" für Code ab, der nie laufen konnte —
  Abhaken ohne Ausführung, dieselbe Blindheit wie L-36 eine Ebene höher
- L-08 Dependabot, L-34 Oregon-Region, L-10 Fehler-Tracking

---

## Zusammenarbeit

David gibt kurze Richtungsanweisungen („brevo fixen", „stufe 2 auch") und
erwartet, dass ich den Rest selbst entscheide und ausführe — inklusive Commit,
Push und Deploy-Überwachung. Siehe [[feedback_always_recommend]].
Bei Abweichung von einem vorherigen Plan: Abweichung benennen und begründen,
nicht stillschweigend anders machen.
