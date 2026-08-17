---
name: resume-point-2026-08-17
description: "Stand 2026-08-17 — UX-Paket 2, dann der Mail-Vorfall (135 Fehl-Mails), PR #41 gemerged und produktiv; abends vier weitere Commits: Zugriffsschutz, Löschfunktion, Kundenfreigabe, UX-Paket 3"
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-17T17:54:15.641Z
  originSessionId: 458bef95-0615-4eb2-85b8-f2842368b8c2
---

**Ein langer Tag in drei Teilen.** Vormittags UX-Paket 2 nach Plan. Nachmittags
ein Vorfall, der alles verdrängt hat. Abends die Aufräumarbeit, die daraus
folgte.

## Teil 1 — UX-Paket 2 (abgeschlossen)

61 gegen 50 Einträge war **kein Filter**: Beide Seiten riefen dieselbe
Schnittstelle auf, nur eine nannte eine Obergrenze. „Kunden" bekam die
Voreinstellung des Servers — 50 (`routers/leads.py`). Elf Betriebe fehlten
still, und die Kacheln rechneten über die abgeschnittene Liste. Übrig: ein
Bildschirm `/app/betriebe`, Listenlogik in `utils/betriebeListe.js`.

## Teil 2 — Der Vorfall

`job_check_missing_materials` (`scheduler.py`), täglich 09:00, **ohne jede
Idempotenz-Sperre**. **ENERGIEFABRIK bekam die Mail seit dem 04.04. jeden
Morgen — rund 135 Stück.** Der Briefing-Job zwanzig Zeilen darunter hatte eine.

**Ich habe zweimal danebengetippt**, weil ich das falsche Protokoll prüfte —
siehe [[mail-zwei-protokolle]]. Gebaut: `automations/erinnerungen.py` (die
Fälligkeitsentscheidung als reine Funktion) und `services/versandsperre.py`
(**der Not-Aus, Standard AUS**).

## Teil 3 — Abends, nach dem Merge

**PR #41 ist gemerged** (`2d9882b`) und **produktiv deployt** — geprüft am
Ergebnis: `/api/projects/debug` antwortet produktiv 401. Damit ist der Not-Aus
live und steht auf „aus". Der 09:00-Job sendet nicht mehr.

Vier weitere Commits, alle auf `staging`, **noch nicht produktiv**:

1. **`679b32c` Zugriffsschutz.** Der Projekt-Router trug **gar keine**
   Anmeldung — 19 von 60 Routen offen, darunter `PUT /{id}` (schreibt
   beliebige Spalten per Roh-SQL) und `PATCH /{id}/phase`. Dazu zwei eigene
   Funde: **`GET /{id}/credentials` gab entschlüsselte CMS-Passwörter an jeden
   Angemeldeten**, und die Rumpfschlüssel des PUT wurden ungeprüft zu
   Spaltennamen im SQL.
   **Die Wurzel war zweimal dieselbe:** `require_any_auth` fragt nur, *ob*
   jemand angemeldet ist, nicht *wer*. Ein Kunde ist angemeldet. Deshalb neu:
   `require_innendienst`, und was ein Kunde braucht, hängt an einem
   `kunden_router` mit Prüfung je Zeile.
   Der wichtigste Test heißt `test_keine_einzige_route_haengt_frei`.
2. **`dddd7af` Löschfunktion für Projekte** — es gab bis dahin **keinen**
   Löschendpunkt. Reihenfolge über die 15 abhängigen Tabellen in
   `services/projekt_loeschen.py`; `DELETE /api/leads/{id}` nutzt sie mit (es
   wäre am Fremdschlüssel von `customers` gescheitert). Oberfläche unter
   *Kundenprojekte*: Auswahl + Vorschau, die zeigt was geht **und was bleibt**.
3. **`d7768f8` Kundenfreigabe.** `confirm-approval` verlangte `require_admin` —
   genau der Endpunkt, den die Kundenseite aufruft. **Jede Kundenfreigabe kam
   403 zurück**, unsichtbar, weil die Seite `res.ok` nicht prüfte.
   `/abnahme/:projectId` entfernt: konnte nie funktionieren, niemand verlinkte
   sie.
4. **`0bde7e0` UX-Paket 3** (UX-05, 06, 06b, 08, 09). Kern: `[Auto-Enrichment]`
   schrieb in `lead.notes`, und `pagespeed_score` wurde berechnet und
   **nirgends** gespeichert — die Notizzeile war der einzige Ort, an dem er
   überlebte. Neue Spalten, dann erst die Zeile weg.

Stand: **1088 Backend-, 201 Frontend-Tests.**

## Offen bei David

1. **`scripts/notizen-bereinigen.sql`** — entfernt die `[Auto-Enrichment]`-Zeilen
   aus den vorhandenen Notizen. Sicherungskopie, Vorher/Nachher-Ansicht,
   `ROLLBACK` am Ende. Regex gegen echtes Postgres geprüft.
2. **`scripts/projekte-entfernen.sql`** — jetzt **optional**: Projekte lassen
   sich seit `dddd7af` in der Oberfläche löschen.
3. **Nächster PR `staging → main`** mit vier Commits — Freitagsregel
   [[feedback-pr-only-fridays]] gilt wieder.
4. **`openapi.json` ist öffentlich** und listet alle 70 Projektpfade samt
   Parametern. Kein Geheimnisleck, aber eine vollständige Landkarte.
   Abschalten wäre ein Zweizeiler — **Davids Entscheidung, noch nicht gefallen**.
5. **UX-Daten** (letzter offener Punkt in Paket 3) ist eine Datenfrage, keine
   Programmierfrage: Dubletten, Domains als Firmenname, Testdatensatz
   KOMPAGNON in der Produktivliste.

## Zwei Dinge, die ich falsch gesagt habe

- Ich meldete einen „zurückgerollten Deploy" bei Render. Es war ein Fehler in
  meiner Prüfschleife: `grep -c` gibt bei null Treffern `0` aus **und** endet
  mit Fehlercode, mein `|| echo 0` hängte eine zweite `0` an.
  **Render deployt hier nicht per Webhook, sondern als letzter CI-Job** —
  `needs: [lint, import, tests, build, e2e, secrets]`. Ein Deploy nach dem Push
  dauert, bis Playwright durch ist. Das ist kein Fehler, sondern das Gate.
- Ich nannte UX-08 „durch den Not-Aus verschärft". Falsch: Die
  Widget-Bestätigung ist von der Versandsperre **ausdrücklich ausgenommen**.

Voriger Stand [[resume-point-2026-08-16]]. Methode: [[ux-methode-krug]].
