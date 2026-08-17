---
name: resume-point-2026-08-17
description: "Stand 2026-08-17 — Mail-Vorfall, PR #41 produktiv, dann Zugriffsschutz, Löschfunktion, DSGVO-Nachweise und die UX-Pakete 3 bis 6; 23 Commits auf staging, CI grün"
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-17T21:39:48.616Z
  originSessionId: 458bef95-0615-4eb2-85b8-f2842368b8c2
---

**Ein sehr langer Tag.** Vormittags UX-Paket 2. Nachmittags ein Vorfall, der
alles verdrängt hat. Abends und nachts die Aufräumarbeit daraus — und die
UX-Pakete 3 bis 6.

## Der Vorfall

`job_check_missing_materials` (`scheduler.py`), täglich 09:00, **ohne jede
Idempotenz-Sperre**. **ENERGIEFABRIK bekam die Mail seit dem 04.04. jeden
Morgen — rund 135 Stück.** Gebaut: `automations/erinnerungen.py` (Fälligkeit
als reine Funktion) und `services/versandsperre.py` (**Not-Aus, Standard AUS**).
**PR #41 ist gemerged und produktiv** — geprüft am Ergebnis, nicht am Deploy-Log.

## Was danach entstand (23 Commits auf `staging`, alles **nicht** produktiv)

**Sicherheit.** Der Projekt-Router trug **gar keine** Anmeldung — 19 von 60
Routen offen. Dazu zwei eigene Funde: `GET /{id}/credentials` gab
**entschlüsselte CMS-Passwörter** an jeden Angemeldeten, und die Rumpfschlüssel
von `PUT /{id}` wurden ungeprüft zu Spaltennamen im SQL. Wurzel beide Male:
`require_any_auth` fragt nur, *ob* jemand angemeldet ist. Neu:
`require_innendienst` + `kunden_router` mit Prüfung je Zeile.
Wichtigster Test: `test_keine_einzige_route_haengt_frei`.

**Löschfunktion für Projekte** — es gab keine. Reihenfolge über die 15
abhängigen Tabellen in `services/projekt_loeschen.py`; `email_logs` überlebt
(nur der Verweis wird gelöst).

**Kundenfreigabe** funktionierte nie: `confirm-approval` verlangte
`require_admin`, genau der Endpunkt der Kundenseite. Jede Freigabe kam 403
zurück, unsichtbar, weil `res.ok` nicht geprüft wurde.

**Impressum-Sucher.** David fand: das Impressum von `alkozei.de` liegt unter
`/now.using/nBito/impressum`, der Verweis auf der Startseite ist mit
`onclick="return false"` **absichtlich tot**. Der schwerere Fehler war aber:
Der Sucher nahm **die erste Seite über 100 Zeichen** und fragte nie, ob es ein
Impressum ist. Jetzt Kandidaten aus drei Quellen + Prüfung auf Pflichtangaben
nach § 5 DDG.

**503 auf Staging aufgeklärt:** `client.messages.create()` — der **synchrone**
Anthropic-Client — lief in einer `async def` und hielt die Ereignisschleife an.
Siehe [[blockierte-ereignisschleife]]. Neun weitere Module haben dasselbe
Muster, ungeprüft.

**Firmennamen:** Der Domainimport setzt die Domain als Platzhalter, der
Impressum-Schritt fand den echten Namen und **verwarf ihn**, weil das Feld als
gefüllt galt. Drei Stellen. Auf Staging tragen jetzt **23 von 29** Betrieben
echte Namen.

**DSGVO:** Der Nachweis (`verified_user_agent`, `verified_ip`) wurde immer
erhoben und **nirgends angezeigt**. Jetzt in der Liste, mit der Dauer zwischen
Mailversand und Klick. Und die Bedienungshürde hatte ein Loch: Der Beleg stand
im HTML, das er schützt — jetzt trägt er seinen Ausstellungszeitpunkt und gilt
erst nach zwei Sekunden.
**Produktiv gibt es nur vier Widget-Anfragen, alle von Davids eigenen
Adressen** — der 16:12:09-Fall war fast sicher er selbst.

**UX-Pakete 3, 4, 5, 6 abgeschlossen.** Drei Diagnosen der Analyse waren
falsch und wurden erst beim Messen widerlegt (UX-12, UX-18, UX-Daten).
Artefakt auf Stand:
`https://claude.ai/code/artifact/946b018e-40f7-481f-826a-83fbf9d53d66`

**Uploads:** Blueprints bekommen `disk:` (1 GB, `/var/data`) und `UPLOAD_ROOT`.
Drei Schreibstellen folgten drei Regeln — jetzt `services/dateiablage.py`.

## Offen bei David

1. **Sammel-PR `staging → main`** — 23 Commits. Freitag
   ([[feedback-pr-only-fridays]])
2. **Datenträger in Render anlegen** — braucht genau **eine** Instanz und
   erzwingt einen **Neustart**. Bewusst seine Entscheidung
3. **`scripts/wer-hat-bestaetigt.sql`** produktiv laufen lassen (DSGVO-Beleg)
4. **`scripts/notizen-bereinigen.sql`** ist überholt — besser
   `POST /api/leads/befunde-nachtragen`
5. Datensätze: CDU-Ortsverband als „Dachdecker", `nachhaltika.denachhaltika.de`
6. Produktiv fehlen `STRIPE_SECRET_KEY`, `CMS_ENCRYPTION_KEY`
7. **Paket 7** (UX-19) ist das einzige offene UX-Thema — echte
   Gestaltungsarbeit, **L**

## Was der Tag über die Arbeitsweise sagt

**Dreimal habe ich eine Zwischenausgabe für das Ergebnis genommen** — siehe
[[feedback-am-gegenstand-pruefen]]. Zwei rote CI-Läufe gehen darauf zurück,
und David hat den ersten gefunden, nicht ich.

**Der beste Fund kam wieder vom Hinsehen:** Das Impressum von alkozei.de,
den Widerspruch „SSL nicht geprüft" neben „SSL: OK", die falschen
Kontrastdiagnosen — nichts davon stand im Code zu lesen.

Prüfstand: **1179 Backend-, 261 Frontend-Tests**, CI grün auf `ed557b1`.
Voriger Stand [[resume-point-2026-08-16]]. Methode: [[ux-methode-krug]].
