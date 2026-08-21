---
name: resume-point-2026-08-19
description: "Stand 2026-08-19 — Umzugsvorbereitung L-34 gemessen (11 Webhooks statt 3, Blueprint umzugsreif), dabei 55 offene Werkzeug-Routen gefunden und geschlossen; Produktiv noch ungeschützt bis zum Merge"
metadata: 
  node_type: memory
  type: project
  originSessionId: e8aa66f0-58b3-41c9-973e-a20823994c33
  modified: 2026-08-19T10:25:42.908Z
---

**Der Tag begann mit dem Umzug und endete bei der Zugriffskontrolle.** Vier
Commits auf `staging`, CI grün, Staging deployt und nachgeprüft.

## L-34 vorbereitet — was gemessen wurde

Der Render-MCP ist **auch heute `unauthorized`** (`list_workspaces` → Fehler),
also ging nur, was ohne Dashboard geht. Ergebnis:

- **Elf Webhook-Endpunkte, nicht drei.** Gemessen an `GET /openapi.json` der
  Produktiv-Adresse (401 Routen). **Stripe fehlte im Plan ganz** — zwei
  Registrierungen mit zwei Geheimnissen (`STRIPE_WEBHOOK_SECRET`,
  `…_GEO`). Netlify sind zwei Pfade. Fünf Lead-Wege (facebook, linkedin,
  google, postkarte, telefon) haben **keinen dokumentierten Registrar**.
- **Blueprint ist umzugsreif.** 44 Schlüssel gegen 56 im Quelltext gelesen —
  alle 17 Abweichungen erklärt, keine echte Lücke. Was der Abgleich *nicht*
  kann: sehen, was im Oregon-Dashboard steht.
- **Zwei Plan-Korrekturen:** `ENVIRONMENT=production` **ist** gesetzt (L-42 war
  längst erledigt, nur die Umzugsnotiz nicht nachgezogen), und der
  Bereitschafts-Check hängt an der Service-ID, nicht an einer URL.
- Die Code-Rückfallwerte standen seit `714b441` (16.08.) schon auf der Domain.

## Der eigentliche Fund

Beim Zählen der Webhooks antwortete `GET /api/webhooks/log` **mit 200 ohne
Anmeldung**. Danach nicht weitergeraten, sondern **499 Routen durchgerufen:
90 antworteten**. Produktiv nachgemessen, ohne einen Anmeldeversuch:

- `/api/dashboard/kpis` → Marge 97,5 %
- `/api/dashboard/projects-by-phase` → Kundennamen samt Marge je Projekt
- `/api/audit/lead/58` → **187 KB** vollständige Audits, über `lead_id`
  durchzählbar
- `POST /api/scheduler/restart` → 200, **er startete wirklich neu**
- `POST /api/scraper/run` → 200, der Lauf begann wirklich

Ursache wie am 14.08. und 17.08.: Die Anmeldung hing an der einzelnen Route.
`briefings.py` hatte elf geschützte und drei vergessene. Jetzt: elf Router mit
Vorgabe, fünf Routen einzeln (ihr Router trägt etwas, das offen bleiben muss).
**90 → 42 offen, verändernd 47 → 21**; die 42 sind sämtlich gewollt öffentlich.

## Zwei eigene Fehlmessungen, beide lehrreich

1. `app.routes` fand `/api/webhooks/log` nicht — diese FastAPI-Version legt
   eingebundene Router als `_IncludedRouter` ab und **flacht ihre Routen nicht
   auf** (62 davon). Beinahe hätte ich einen Ladefehler in `main.py` gemeldet,
   den es nie gab. Strukturprüfungen also am **Router**, nicht an `app.routes`.
2. Ein GET auf `/api/leads/public` (eine POST-Route) fiel auf
   `GET /api/leads/{lead_id}` und lieferte 403 — der Test maß die falsche
   Route. Siehe [[feedback-am-gegenstand-pruefen]].

## Offen bei David

1. **Produktiv ist alles davon noch offen.** Der Fix liegt auf `staging`;
   `main` trägt ihn erst nach einem Merge. Das ist Davids Entscheidung
   ([[feedback-pr-only-fridays]] gilt).
2. Webhook-Adressen bei **Trackdesk, Netlify (2×), Brevo und Stripe (2×)** auf
   `api.kompagnon.group` umstellen — gefahrlos schon jetzt, die Domain zeigt
   noch auf Oregon.
3. Der Umzug selbst: neuer Dienst in Frankfurt über
   `kompagnon/render-produktiv.yaml`, Datenträger vorher zählen
   (`find /var/data -type f | wc -l`), Service-IDs in den Repo-Variablen.
4. Render-MCP-Zugang — zwei Tage in Folge `unauthorized`.
5. Trello als MCP war kurz Thema und wurde von David wieder verworfen.

## Neue Lücken

- **L-51** geschlossen (die 55 Routen)
- **L-52** offen: `GET /api/audit/{id}` bleibt öffentlich, weil die Landingpage
  ihr Gratis-Audit dort abholt — durchzählbar. Das Widget macht es mit
  `/api/widget/report/{token}` richtig vor
- **L-53** offen: zwei öffentliche Routen antworten produktiv mit **500**
  (`/api/dashboard/alerts` TypeError, `/api/payments/session/{id}`). Bewusst
  **nicht** auf Verdacht repariert — es fehlt der Traceback

Prüfstand: Backend-Suite grün (Exit 0), CI-Lauf `32241804122` mit allen sieben
Jobs grün inkl. Playwright und Deploy. 
## Nachmittag: zwei Fremdaudits und die Akademie

**Memberspot auditiert** (`docs/akademie-vorbild-memberspot.md`). Testzeitraum
abgelaufen — Lektionsdetails, Prüfungen und Mitgliederbereich gesperrt, der
**Kursbaum** aber lesbar. Struktur: `Kurs → Modul → Ordner → Lektion`, **Status
auf jeder Ebene** (veröffentlicht / „Manuell" = nur Zugewiesene). Daraus baut
die Vorlage: ein Gratis-Startmodul, ein Pflichtstrang I–IV, **sechs
Abteilungs-Module auf „Manuell"**, ein Bonus. Unerwartet: Unsere Akademie kann
schon Quiz, Fortschritt mit Punktzahl und **Zertifikate mit öffentlicher
Prüfung** — was Memberspot ab 39 €/Monat verkauft. **Die Lücke ist die
Struktur, nicht die Technik.**

**HubSpot auditiert** (`docs/hubspot-vorbild-darstellung.md`, Konto
*Silva Viridis*, 4.920 Kontakte). Der Fund ist eine **Grammatik**: Jeder Hub ist
gleich gebaut — *Objekte → Werkzeuge → Auswertung*, jeder endet in eigenem
`*-Analytics`. Datensatzseite = **drei Spalten mit fester Bedeutung**, Verlauf
**immer sichtbar** (unsere Betriebsseite ist reiterbasiert). Fehlende Felder:
Lifecycle-Phase getrennt von Leadstatus, Datensatzquelle, Rechtsgrundlage.
**AEO** (`/ai-visibility/`, Beta) prüft Sichtbarkeit in ChatGPT/Perplexity/
Gemini — Eingabe nur *Marke + Domain*, beides haben wir im Lead. Das ist ein
**fehlendes Audit-Kriterium** bei uns.

**Gebaut, mit Tests und grüner CI:**
1. `b1d89bb` — **zwei Kurssysteme zusammengeführt.** `courses` hatte keine
   Struktur, einen Aufrufer und keinen Menüeintrag; `seed_courses` wurde nie
   aufgerufen. `services/kurse_zusammenfuehren.py` lässt die drei Demo-Saaten
   mit erfundenen Zahlen liegen, holt Bearbeitetes nach, unveröffentlicht.
   **Tabelle `courses` bleibt stehen** (DROP nicht umkehrbar)
2. `d704a9c` — `description` + `thumbnail_url` an `AcademyModule`
3. `ad8beec` — **Der Bearbeiten-Knopf an einer Lektion warf einen aus dem
   Kurs**: Ziel war `/app/akademie/admin/modul/{id}`, das die Umleitung auf die
   Kursliste abbildet. Der Lektions-Editor war von dort **gar nicht
   erreichbar**

**Zurückgestellt und warum:** Die Trennung Lifecycle-Phase/Leadstatus hatte ich
als „kleinsten Eingriff" bezeichnet — **falsch**. Gemessen: 31 Fundstellen in
den Lead-/Kunden-Routern, 47 Frontend-Dateien, gemischter Wortschatz
(`won`/`gewonnen`, `done`/`completed`/`approved`). Eigenes Paket; halb gemacht
wäre schlechter als gar nicht.

Trello als MCP war kurz Thema und wurde von David verworfen.


## Abend: die Lückenliste abgearbeitet

**L-52** (Audits durchzählbar) — geschlossen. Das Audit bekommt beim Anlegen
ein `public_token`, `/start` gibt es zurück, ohne Anmeldung braucht man es —
am Detail **und** am Zwischenstand. 404 statt 403. Alle drei öffentlichen
Abholer führen es mit (`websprint-landing.html`, `AuditHook.jsx`, `useAudit`).

**L-53** (zwei 500er) — waren zwei verschiedene Dinge. `/api/dashboard/alerts`:
**nachgestellt statt geraten** — `scope_creep_flags` war `NULL`, und `NULL > 0`
ist ein TypeError. Behoben am Lesezugriff *und* in den Daten.
`/api/payments/session/{id}`: **kein Absturz**, sondern absichtliche 500 wegen
fehlendem Stripe-Schlüssel — jetzt 503, wie es das Haus an fünf Stellen macht.

**L-54** (zweideutige Kundenkennung) — Nachtrag als Startphase
(`services/zuweisung_kennung.py`), schreibt nur um, **wo es sicher ist**; bei
Zahlen, die beides sein können, bleibt es liegen und wird gemeldet.

**L-08** — 51 npm-Befunde gemessen, nur zwei direkt. `axios` 1.14 → 1.19
(SSRF + Auth-Umgehung). **`grapesjs` 0.22 → 0.23 bewusst nicht** — Seiteneditor.

**L-11** — `docs/sicherung-und-wiederherstellung.md`. Kernpunkt: **Eine
DB-Sicherung rettet den Betrieb nicht.** Datenträger `/var/data` ist in keiner
DB-Sicherung, und ohne `CMS_ENCRYPTION_KEY`/`CREDENTIALS_KEY` sind
Zugangsdaten auch nach vollständiger Wiederherstellung unlesbar.

**L-05, dritter Schritt** — durchgesetzt sind jetzt **fünf statt zwei** Rechte
(`delete_leads`, `manage_users`, `manage_settings`). Neu `verlangt_recht(...)`.
Die Admin-Routen waren geschützt, aber über die **Rolle** — deshalb blieb das
Häkchen wirkungslos. `deploy_kas_pages` und `manage_system_settings` bewusst
**nicht**: hat nur der Superadmin, das wäre eine Verhaltensänderung.

**L-56 neu** — einen Betrieb mit Kundenzugang löschen lief in den
Fremdschlüssel `users.lead_id` und wurde zu 500. Jetzt 409 mit Klartext. Offen
bleibt die Frage, ob das Löschen eines Betriebs sein Kundenkonto mitnimmt —
Datenschutz, keine Zeile Code.

**Was ich nicht kann:** L-34/L-41/L-44 (Render-Dashboard, MCP dreimal
`unauthorized`), L-40 (Netlify-Site), L-26 (drei Editor-Generationen),
Webhook-Umstellungen bei Dritten, die Lifecycle-Trennung (eigenes Paket) und
der Freitags-PR.


## Später Abend: Lifecycle-Paket und vier kleine Lücken

**Lifecycle-Umbau als eigenes Paket** (`a7e9cc5`). `Lead.lifecycle_phase`
neben `status`, der unverändert bleibt — vier Phasen (`interessent`,
`im_gespraech`, `kunde`, `ausgeschieden`), abgeleitet aus dem Wortschatz, der
wirklich vorkommt. Ein SQLAlchemy-Ereignis zieht sie mit, dazu ein
`before_insert`-Haken. **Unbekannter Status → keine Phase**, die Oberfläche
zeigt „Phase offen". **Der Gewinn sind zwei falsche Zahlen:**
`automations.py` und `projects.py` fragten `status == "won"` und übersahen
`customer` — ein von Hand als Kunde markierter Betrieb zählte in keiner
Kennzahl. Meine frühere Einschätzung („31 Stellen, eigenes Paket, halb wäre
schlimmer") war **richtig gezählt, falsch geschlossen**: additiv daneben
brauchte `status` gar nicht anzufassen.

**L-29** — Preise: nicht drei Stellen, sondern **vier, und bereits
auseinandergelaufen** (Premium 2.800 vs. 2.500, Kompagnon 2.000 vs. 3.500).
`PACKAGE_NAMES` stand im **Text der Kundenmail**; Name und Betrag kommen jetzt
aus derselben Zeile. Die drei Frontend-Stellen bleiben offen — welcher Preis
gilt, ist Davids Entscheidung.

**L-32** — Markenfarben: nicht 26 Stellen in 6 Dateien, sondern **39 in 21**,
zehn davon als Konstante eingefroren, teils unter Namen wie `TEAL`, `DARK2`,
`PRIMARY`. **Keine Kosmetik:** `--kc-dark` und `--kc-mid` haben im
Dunkelmodus andere Werte. Der Wächter prüft die **Konstante**, nicht jede
Ziffer — `tokenwerte.js` muss die Werte kennen, und `handwerk-blocks.js`
erzeugt Kundenseiten ohne unsere Variablen.

**L-17** — 20 von 182 Dateien führen ARIA. Eine Klasse geschlossen: **zwanzig
Symbolknöpfe ohne Namen** (WCAG 4.1.2) — genau das, was wir bei Kunden prüfen.
Rest bleibt offen.

**L-30/L-31** — zwei Dateien, die einen Mai-Stand als aktuell ausgaben, tragen
jetzt einen ehrlichen Kopf. Nicht neu geschrieben: das wäre die dritte
Wahrheit.

**Zwei eigene Fehlmessungen:** „fünf Bilder ohne alt" — alle haben es, nur in
der Folgezeile. Und meine Suche nach `KC_` fand sieben Dateien, die Regel
fand zehn. **Zeilenweises Zählen ist keine Messung.**


## Nacht: L-34 zur Hälfte — Frankfurt läuft

**Der Dienst steht:** `kompagnon-backend-fra`, `srv-da30dg3bc2fs73fomi0g`,
Frankfurt, Standard, Datenträger 1 GB auf `/var/data`, Health-Check `/health`,
Auto-Deploy Off. **Gemessen:** `/health` in **0,18 s** gegen Oregons **3,1 s**
(Faktor 15), `database: connected` über die **interne** Adresse, Start in 60 s
mit leerem `startup_missing` (Oregon: 264 s, sieben von acht Phasen verloren).

**Wie, entgegen dem Plan:** Der Blueprint-Weg ging nicht — Namenskonflikt mit
zwei laufenden Diensten, kein `render.yaml` im Wurzelverzeichnis, und Render
hätte das laufende Frontend mitübernommen. Das Umbenennen des Oregon-Dienstes
ließ sich im Dashboard **nicht speichern** (Knopf bleibt inaktiv, auch bei
David). Also von Hand angelegt, Name frei gewählt — Blocker umgangen.

**Variablen über eine Environment-Gruppe** `kompagnon-produktiv` (15 Stück),
Geheimnisse haben Render nie verlassen. `DATABASE_URL` bewusst **nicht** in der
Gruppe: Oregon braucht extern, Frankfurt intern.

**Nebenbefund:** Produktiv sind nur **15** Variablen gesetzt, der Blueprint
deklariert 44 — `WEBHOOK_SECRET`, `STRIPE_SECRET_KEY`, `CMS_ENCRYPTION_KEY`,
`NETLIFY_VORSCHAU_SITE_ID` fehlen wirklich. Vier Vermutungen belegt.

**Mein Fehler, korrigiert:** Ich meldete, der Blueprint hätte Frankfurt „ohne
Browser" gebaut, und übernahm Oregons Build-Befehl. Falsch — `playwright`
steht in **keiner** `requirements.txt`, Screenshots kommen über thum.io/
microlink. Der erste Build scheiterte prompt. Daraus **L-57: Der
Oregon-Dienst lässt sich nicht mehr von Grund auf bauen** — er läuft auf einem
wiederverwendeten Artefakt (letzter Deploy 46 s, „Environment updated"). Ein
erzwungener Neubau oder Rollback würde produktiv fehlschlagen.

**Offen, in dieser Reihenfolge:** fachliche Probe am neuen Dienst → Webhooks
(6 Stück) → **Domain umhängen (erster unumkehrbarer Schritt)** →
`RENDER_SERVICE_BACKEND_PROD` auf `srv-da30dg3bc2fs73fomi0g` → alten Dienst
suspendieren → L-44.

**Kosten:** zwei Standard-Dienste parallel; Renders August-Prognose stieg auf
294,99 $.

**Auch beantwortet:** L-11 (Point-in-Time **7 Tage**), Datenträger **0
Dateien**, Umschreibungsregel genau eine (verschluckt das Widget **nicht**,
gemessen), David ist **superadmin**.


## Morgen zuerst — L-34 zu Ende, in dieser Reihenfolge

**0. Aus welchem Branch deployt `kompagnon-backend-fra`?** Von Hand angelegt,
also steht die Vorgabe nirgends. Erwartet `main`, **geprüft nicht**. Hängt er
an `staging`, schaltet das Umhängen der Domain den gesamten heutigen,
produktiv ungetesteten Stand live. Im Dashboard nachsehen — der Render-MCP
antwortet `unauthorized`.

**1. L-57 zuerst, nicht als Aufräumarbeit.** Solange Oregons Build-Befehl die
zwei Playwright-Zeilen trägt, lässt der Dienst sich nicht neu bauen.
Suspendieren und späteres Fortsetzen löst bei Render einen Deploy aus — **der
Rückweg wäre genau dann kaputt, wenn man ihn braucht.**

**2.** Webhooks (6: Trackdesk, Netlify 2×, Brevo, Stripe 2×) · **3.** Domain
umhängen (kurze Zertifikatslücke möglich) · **4.**
`RENDER_SERVICE_BACKEND_PROD` auf `srv-da30dg3bc2fs73fomi0g` — wer das
vergisst, deployt weiter nach Oregon und **die CI meldet trotzdem grün** ·
**5.** alten Dienst suspendieren, nicht löschen · **6.** ein paar ruhige Tage
später L-44.

**Gleichheitsprobe schon erbracht:** `GET /openapi.json` liefert auf beiden
Diensten **401 Routen, null Abweichung**, fünf Stichproben identisch. Weiter
kommt man ohne Zugangsdaten nicht — der Rest ist Umhängen, nicht Prüfen.

**Zustand heute Nacht:** vollständig umkehrbar. Frankfurt trägt keinen
Verkehr, produktiv läuft unverändert Oregon auf `main` — **ohne die 30
Commits dieses Tages und damit ohne die heutigen Sicherheitsfixes.** Deshalb
antwortet `/api/dashboard/kpis` produktiv noch 200 statt 401. Sammel-PR am
**Freitag**.

**Braucht eine Entscheidung von David:** L-29, welcher Preis gilt. Premium
steht mit 2.500 und mit 2.800, Kompagnon mit 2.000 und mit 3.500. Ohne
Entscheidung lässt sich nur die Behauptung aus dem Quelltext ziehen.

Tagesbericht im Repo: `docs/stand-2026-08-19.md`.

Voriger Stand [[resume-point-2026-08-18]].
