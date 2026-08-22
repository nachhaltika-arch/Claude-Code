---
name: resume-point-2026-08-21
description: Stand vom 21.08.2026 — 32 Commits, M4 fertig, Design-Canvas, Website-weiter Audit, Legacy-Editor weg, Modellwechsel; morgen M5
metadata:
  type: project
---

**32 Commits auf `staging`, alle mit grüner CI.** Backend 1.679 Tests
(morgens 1.538), Frontend 396 (morgens 370). Nichts live — PR #43
`staging → main` steht offen, der Merge ist Davids Schritt. Voller Bericht:
`docs/stand-2026-08-21.md` (667 Zeilen, zwei Teile).

**Der Tag hat zwei Hälften.** Bis Abschnitt 9 Lückenliste, ab Abschnitt 10 die
Arbeit nach `docs/module-karte.md` — entstanden aus Davids Satz „ich will fertig
werden, und gerade fühlt es sich an, als ob wir alles gleichzeitig entwickeln".

## Was geschlossen wurde

* **M4 ist fertig** (L-64, L-71, L-61). Der Bestellweg lief nur nach `/login`;
  die ganze Strecke war gegen eine Schnittstelle geschrieben, die es nicht gibt.
  `ProductManager` (Menüziel!) las Felder, die die Tabelle nicht hat — jedes
  Speichern wirkungslos. Wächter: `test_frontend_adressen.py`.
* **Design-Canvas** (L-72): `GET/POST /api/design-canvas/{lead_id}` gibt die vier
  KAS-Ansichten als Artboards aus und nimmt sie bearbeitet zurück, versioniert
  über `mockup_versions`. **Keine Oberfläche im Werkzeug** — Canvas entstehen in
  Claude Code, dafür gibt es keine Schnittstelle. `scripts/canvas-export.py`.
* **Audit bewertet die ganze Website** (L-73): `audit_seiten` + `audit_aggregat`,
  25 Seiten gedeckelt. Vorher blieb das Kontaktformular auf `/kontakt` unsichtbar.
  Jedes Ergebnis trägt `seiten_geprueft`; alte stehen auf 1.
* **Legacy-Editor weg** (L-26): 2.402 Zeilen. Vorher umgezogen: GrapesJS in den
  Editor, GEO = Schritt 3, Leistungsseiten = Schritt 9.
* **Modellwechsel** (L-74): 49 Angaben, davon 16 auf `claude-sonnet-4-20250514`
  (zurückgezogen 15.06.2026). Staffelung blieb — Sonnet 5 / Opus 5 / Haiku 4.5.
* Nähte aufgetrennt (L-66…L-70): 13 offene Routen, 19 Router-Kollisionen.

## Drei Fallen, die morgen wieder greifen könnten

1. **Adaptives Denken ist die Vorgabe.** Wer eine neue KI-Aufrufstelle schreibt
   und `thinking` weglässt, bekommt Denken — und 21 Stellen lesen `content[0]`,
   wo dann ein Denkblock steht. `tests/test_modellwahl.py` hält das offen.
2. **Die Schrittkette bricht an jedem unbestätigten Schritt.** Seit heute nicht
   mehr an `optional` markierten. Wer einen Pflichtschritt einfügt, sperrt jedes
   laufende Projekt ab dort. `utils/schrittkette.js`, `schrittkette.test.js`.
3. **Ein Router, der eine Adresse überdeckt, kann die Sicherheitsarbeit machen.**
   `test_router_kollisionen.py`, Ausnahmeliste leer.

## Morgen

1. **M5 zu Ende**, damit ein Kunde vollständig durchläuft. Offen: L-27
   (Briefing-Struktur — Davids Entscheidung), L-25 (`projects.py`, 4.848 Zeilen),
   L-14 (Assistent unbewertet), L-50-Rest.
2. **Knopf für den Design-Canvas** in der KAS-Seitenleiste — heute nur Endpunkte.
3. **Fehlerprotokoll prüfen** (Verwaltung): Liefen Schriftvorschläge,
   Briefing-Vorbefüllung und der Perf-Kommentar im Scheduler wochenlang ins
   Leere? 16 Stellen standen auf einem zurückgezogenen Modell — **nicht
   gemessen**, lokal liegt kein Schlüssel.
4. **Ein echter Betrieb im Canvas.** Testbetrieb 1 hat zwei Pflichtseiten und
   keine Markendaten.

## Blockiert bei David

Render-Zugang **fünften Tag** `unauthorized` → L-34, L-35, L-40, L-44, L-57.
Offene Entscheidungen: L-27, L-56, L-58, L-60, L-62, L-65.

Verwandt: [[messfehler_eigene_zahlen]] · [[module_karte]] ·
[[deploy_laeuft_ueber_ci]] · [[feedback_am_gegenstand_pruefen]]
