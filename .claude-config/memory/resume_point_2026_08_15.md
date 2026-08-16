---
name: resume-point-2026-08-15
description: "Stand 2026-08-15 — 5 stille Fehler aus dem Fremdlauf, Rotation gemeinsam erledigt, ENVIRONMENT war nie gesetzt, 7 von 8 Startphasen liefen produktiv nie; offen nur noch L-34"
metadata: 
  node_type: memory
  type: project
  originSessionId: 22412730-2482-4fd1-97ef-6882597b8ff8
  modified: 2026-08-15T10:31:57.334Z
---

**Der erste Lauf des Audits gegen eine echte fremde Website** (SHK-Betrieb
Hamburg, Läufe 80/83 auf Staging) — § 6.4 des Anforderungskatalogs, dort seit
dem 11.08. als wichtigster offener Punkt markiert. Er hat sich sofort bezahlt
gemacht: **vier Fehler an einem Vormittag**, alle behoben und gepusht.

**1. Der Scanner fragte ohne Browser-Kennung** (`0ba4eca`). Jeder andere
Collector setzt eine, `qa_scanner.py` als einziger nicht. Der Server antwortete
der httpx-Standardkennung mit **403 auf allen Pfaden**, dem Browser mit 200. Da
httpx bei 403 nichts wirft, zergliederte der Scanner die Fehlerseite und meldete
deren Nullen als **„gemessen"** — 13 Punkte auf `se_*`, `bf_*`, `dg_mobil`.
Zweiter Teil des Fixes: Eine abweisende Antwort gilt jetzt als *nicht erhoben*,
dann greift das vorhandene `if not qa: skip`.

**2. Die Adresse verlor ihren Ort zwischen zwei Tags** (`6a48346`).
`soup.get_text()` **ohne Trenner** klebt Nachbarelemente zusammen: „Straße 12" +
„22047 Hamburg" → „Straße 1222047 Hamburg", und `\b\d{5}` findet darin keine
PLZ. Über das Widget gibt niemand einen Ort ein, die Erhebung ist der einzige
Weg. Dieselbe Ursache lieferte **`69705880info@firma.de`** als gescrapte
E-Mail — kaputte Adressen direkt in der Leadliste.

**3. `/info` gab die Datenbank-Zugangsdaten aus** (`2f687b2`) — `DATABASE_URL`
unverändert, ohne Login, **produktiv wie auf Staging**. Alle übrigen Felder
waren immer schon boolesch; die Datenbank war die Ausnahme. **Offen bei David:
Passwörter in Render rotieren** — der Fix macht die Preisgabe nicht ungeschehen.
Nebeneffekt: `/info` ist jetzt ein verlässlicher Deploy-Indikator
(`database_configured` statt `database`).

**4. Das PDF druckte eine Rechtsangabe über die Nachbarspalte** (`a2b668c`).
reportlab bricht **rohe Zeichenketten in Tabellenzellen nicht um** — nur ein
`Paragraph` bricht. Zellen messen sich jetzt selbst. Falle dabei: Der
Tabellenkörper setzt keine Textfarbe, rohe Zellen sind also schwarz; mit
`KC_DARK` stand die umbrochene Zelle sichtbar in Teal daneben → `KC_TEXT`.

**Der Gegenbeweis:** derselbe Betrieb 48 → **62 Punkte**, „Nicht konform" →
„Homepage Standard Bronze"; SEO 4/15 → 11/15. Der Ortspunkt fehlt weiter, aber
jetzt zu Recht — „Hamburg" steht wirklich nicht im Titel. Aus einem Artefakt
wurde eine echte Aussage.

**§ 5.7 ist verifiziert:** Die Quellen-Kennzeichnung kommt beim Leser an —
eigene Spalte „Quelle", Erklärsatz und Legende. Das PDF zeigt „Heizung und
Sanitär (Lokaler Leistungsbetrieb)" und „Hamburg"; kein geratenes Gewerk,
obwohl der Scraper an dieser Seite „Elektriker" rät. Der Fix vom 14. hält.

**Das Muster des Tages:** Fünfmal war die Rechnung richtig und die Grundlage
falsch — eine Fehlerseite, ein zusammengeklebter Text, eine Datei unter
falschem Namen, nie befüllte Spalten mit Vorgabewert, eine ungemessene
Spaltenbreite. Dieselbe Bauart wie [[migration-trap-main-py]]: Nichts scheitert
laut, das Ergebnis ist trotzdem unwahr. **Wo ein Wert fehlt, gehört „nicht
erhoben" hin, nie eine Null.**

**Am Nachmittag geschlossen:** § 5.6 (`tests/referenzseite.py` — eingefrorene
Website, 15 Tests über die ganze Kette; die Referenz steht bei 87 Punkten und
63 % Abdeckung, festgeschrieben). **Stufe C** ist fertig: `POST
/api/pages/{id}/qualitaetspruefung` deployt die eigene Seite als Vorschau und
misst sie mit demselben Katalog; im Editor sitzt „🔍 Qualität prüfen" neben
Speichern. Der Deploy kennt genau eine Adresse — `NETLIFY_VORSCHAU_SITE_ID` —
und ohne sie passiert nichts, damit keine Vorschau je die Kundensite
überschreibt. **Der Durchstich Editor → Netlify → Audit → PDF ist ungeprüft**,
dafür fehlt die Vorschau-Site. Zuletzt: ein Rahmen für alle Mails
(`services/mail_layout.py`), `email_service.py` entfallen.

**Am Abend gemeinsam im Render-Dashboard erledigt** (Details in
`docs/stand-2026-08-15.md` § 7): Zugangsdaten in beiden Umgebungen rotiert und
die alten gelöscht, ohne Ausfall. PR #37 und #38 gemerged, `/info` produktiv
verifiziert dicht.

**Dabei drei Dinge gefunden, die niemand gesucht hatte:**
1. **Staging blockt externen DB-Verkehr, Produktiv nicht** (`0.0.0.0/0`). Die
   Preisgabe war deshalb nur produktiv verwertbar. Grund: Ein Backend in
   Oregon erreicht die interne Adresse einer Frankfurter DB nicht.
2. **`ENVIRONMENT` war produktiv nie gesetzt** → Vorgabewert `development` →
   Demo-Konten wurden *angelegt* statt deaktiviert. Drei waren aktiv
   (`kunde@`, `nutzer@`, `auditor@kompagnon.de`), jetzt deaktiviert.
   **Deaktivieren, nicht löschen** — der Seed legt fehlende Konten neu an.
3. **Sieben von acht Startphasen liefen produktiv nie** (`347379b`). Ein
   Worker im Pool, die Migration hielt ihn 215 s, der Rest lief in Timeouts
   ohne je zu starten. Kein Scheduler seit Monaten. Jetzt: Start vollständig
   in 264 s, `scheduler_running: true`.

**Offen bei David:** L-34 (Backend nach Frankfurt — Wurzel von 1 und 3, eigene
Sitzung mit Plan), danach L-40 (Inbound-Regel), `NETLIFY_VORSCHAU_SITE_ID`,
Widget-Restpunkte, Leadverwaltung nur für Administratoren?
`PAGESPEED_API_KEY` ist produktiv gesetzt (§ 6.1 damit geklärt).

**Gesamtübersicht nachgezogen:** `docs/soll-ist-analyse.md` (ohne Datum im
Namen — das Datum war der Grund, warum sie veraltete; wird jetzt
fortgeschrieben). Ampeln geprüft und belegt, Lückenliste aktuell, neue Punkte
L-39 (DB-Rotation) und L-40 (Vorschau-Site). Verschlechtert hat sich genau
eine Kennzahl: **elf** Backend-Dateien über 800 Zeilen statt sechs.

**Tagesbericht: `docs/stand-2026-08-15.md`.** Prüfstand: 927 Backend- und 98
Frontend-Tests.

Voriger Stand [[resume-point-2026-08-14]]; Release-Rhythmus
[[feedback-pr-only-fridays]] — heute Samstag, PR wartet, **außer** der
Sicherheitsfix rechtfertigt die Ausnahme.
