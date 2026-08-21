# KOMPAGNON — Soll-Ist-Analyse der Gesamtplattform

> **Fortlaufend geführt.** Letzte Durchsicht: 2026-08-15.
> Diese Datei hieß bis dahin `soll-ist-analyse-2026-08-07.md`. Das Datum im
> Namen war der Grund, warum sie veraltete: Sie las sich wie ein Stand und
> wurde wie eine Übersicht benutzt. Sie wird jetzt fortgeschrieben; die
> Historie steht in der Git-Geschichte.
>
> Methodik: Code-Analyse, Live-Prüfung produktiver Endpunkte, Abgleich mit
> `CLAUDE.md`, dem Audit-Anforderungskatalog und den Tagesberichten.

---

## Wie diese Datei zu lesen ist

Jede Zeile hier ist entweder belegt oder als ungeprüft gekennzeichnet. Wo eine
Einschätzung aus einer früheren Durchsicht stammt und seither niemand
nachgesehen hat, steht das dabei — eine alte Einschätzung, die als aktueller
Befund gelesen wird, ist schlimmer als eine Lücke, zu der man nichts sagt.

**Die Lückenliste in Abschnitt 3 ist die maßgebliche Übersicht.** Abschnitt 2
begründet sie, mehr nicht.

---

## 1. Gesamtbild

| Bereich | Stand | Einschätzung | Geprüft |
|---|---|---|---|
| A — Betrieb & Release | 🟡 | `main` geschützt, CI mit Pflichtjobs, dual-branch etabliert. **Aber:** produktiv liefen sieben von acht Startphasen nie (L-41, behoben 08-15), und das Backend steht in der falschen Region (L-34) | 08-15 |
| B — Sicherheit & Compliance | 🟡 | Anmeldung am Router, teure Endpunkte begrenzt, Zugangsdaten rotiert, `/info` geschlossen, `ENVIRONMENT=production`, Demo-Konten deaktiviert. Offen: Rollenrechte ohne Wirkung (L-05/L-12), Produktiv-DB im offenen Internet (L-40, hängt an L-34) | 08-15 |
| C — Vertrieb & Lead-Gewinnung | 🟡 | Widget produktiv, Double-Opt-in, Bericht und PDF tragen die Marke. Offen: Einbau in die Ziel-Landingpage, Brevo-Klick-Tracking | 08-15 |
| D — Verkauf & Zahlung | 🟡 | Stripe funktioniert; Preise weiterhin an mehreren Stellen | 08-07 |
| E — Projektabwicklung | 🟢 | 7 Phasen, Checkliste, Marge, Automationen laufen | 08-07 |
| F — KAS-Pipeline (Site-Bau) | 🟡 | Stufen A–C gebaut, Qualitätsschleife seit 08-15 geschlossen. Offen: drei Editor-Generationen parallel | 08-15 |
| G — Kundenportal | 🟢 | Phasen, Freigaben, Nachrichten, Dokumente vorhanden | 08-07 |
| H — Projekt-Assistent | 🟡 | Ausbau 1 gebaut (`routers/assistant.py`), fachlich noch von niemandem beurteilt; Ausbau 2 unberührt | 08-15 |
| I — Academy | 🟢 | Kurse, Module, Quiz, Zertifikate, Admin | 08-07 |
| J — Eigene Web-Präsenz | 🟠 | KAS-Seiten ohne Custom-Domain-Endpunkt, WebSprint außerhalb des Systems | 08-07 |
| K — Qualitätssicherung | 🟡 | 927 Backend- und 98 Frontend-Tests, vier Pflichtjobs in der CI, Referenz-Website für die Erhebung. Offen: Monitoring, Backup-Doku | 08-15 |
| L — Code-Struktur | 🟠 | **11 Backend-Dateien über 800 Zeilen** (`projects.py` mit 4.673), sechs im Frontend; Doppelstrukturen ungeräumt | 08-15 |

**Kurzfassung:** Die Fachlichkeit trägt, und die Qualitätssicherung ist seit dem
07.08. von „praktisch nichts" zu einem tragenden Fundament geworden. Die
verbliebenen Lücken liegen in der Absicherung (B) und in der Struktur (L) — und
L wird nicht besser, sondern schlechter: Die größte Datei ist seit der letzten
Zählung weiter gewachsen.

---

## 2. Was sich seit dem 07.08. geändert hat

Nur die Bereiche mit belegter Änderung. Alles Übrige steht unverändert in der
Tabelle oben mit dem Datum seiner letzten Prüfung.

### A — Betrieb & Release · 🟠 → 🟢

Der Produktiv-Rückstand ist abgetragen, `main` ist über Rulesets geschützt, die
CI läuft mit vier Pflichtjobs auf jede PR. Der wöchentliche Rhythmus steht
(Mo–Do auf `staging`, freitags Sammel-PR).

### B — Sicherheit & Compliance · 🔴 → 🟠

**Am 14.08. gefunden und behoben:** Die Kundendaten waren ohne Login lesbar und
löschbar — 31 von 42 Lead-Routen, alle 7 Kunden-Routen, 9 Usercards. Die
Ursache war die Richtung: Die Anmeldung hing an jeder Route statt am Router.
Jetzt am Router, öffentliche Ausnahmen in einem eigenen Router mit eigener
Prüfung.

**Am 15.08. gefunden und behoben:** `GET /info` lieferte `DATABASE_URL`
unverändert — Benutzer, Passwort und Host der Postgres-Instanz, ohne Anmeldung,
produktiv wie auf Staging. Der Endpunkt meldet jetzt nur noch, *dass* eine
Datenbank eingerichtet ist. **Die Rotation der Zugangsdaten steht aus** (L-39).

**Ebenfalls am 15.08.:** `POST /api/audit/start` war ohne Anmeldung und ohne
jede Grenze erreichbar — je Aufruf ein KI-Lauf, PageSpeed-Kontingent, ein
Screenshot und ein Mehrseiten-Crawl. Das Widget hatte seit dem 11.08. eigene
Grenzen, aber es ruft die Funktion intern auf; der HTTP-Weg ging daran vorbei.
Behoben in `82453bd` (L-04).

Weiterhin offen: Rollenrechte ohne Wirkung (L-05) und `require_auditor` an
keiner Route (L-12) — beide am 15.08. nachgeprüft und bestätigt.

### F — KAS-Pipeline · unverändert 🟡, aber inhaltlich weiter

Stufe A (Vertrag und Freigabe-Tor), B (Blockvariante je Kunde) und C
(Seitenkomposition) sind gebaut. Am 15.08. kam die Qualitätsschleife dazu: Eine
selbst gebaute Seite wird als Vorschau deployt und mit demselben Katalog
gemessen, den ein Kunde bekommt (`POST /api/pages/{id}/qualitaetspruefung`).
**Scharf geschaltet ist sie noch nicht** — dafür fehlt eine eigene Vorschau-Site
(L-40).

Unverändert offen: drei Editor-Generationen nebeneinander (L-26).

### H — Projekt-Assistent · ⬜ → 🟡

Ausbau 1 ist gebaut. Offen bleibt, dass die Antworten fachlich noch von
niemandem beurteilt wurden — weder von David noch von einem Handwerksbetrieb —
und dass die Ausgangswerte für das Erfolgskriterium nie gemessen wurden.

### K — Qualitätssicherung · 🔴 → 🟡

Die größte Bewegung. Aus „praktisch keine Tests" sind **927 Backend- und 98
Frontend-Tests** geworden, dazu vier Pflichtjobs in der CI und seit dem 15.08.
eine eingefrorene Referenz-Website, gegen die die Erhebung des Audits gemessen
wird.

Der Anlass dafür ist selbst ein Befund: Am 15.08. fielen fünf Fehler auf, die
alle in der *Erhebung* saßen — und alle Tests prüften bis dahin nur, wie aus
Fakten Punkte werden, nicht wie aus einer Website Fakten werden. Details in
`stand-2026-08-15.md`.

Offen bleiben Monitoring (L-10) und die Backup-Dokumentation (L-11).

### L — Code-Struktur · unverändert 🟠, Tendenz schlechter

Die Zählung vom 07.08. nannte „sechs Dateien über 800 Zeilen". Am 15.08. sind
es **elf im Backend** — `projects.py` (4.673), `leads.py` (2.196),
`component_library.py` (2.100), `main.py` (2.050), `sitemap.py` (1.785),
`scheduler.py` (1.412), `pdf_generator.py` (1.409), `database.py` (1.166) und
drei weitere — dazu sechs im Frontend, angeführt von `templates_zusatz.js`
(3.121) und `LeadProfile.jsx` (2.673).

Das ist die einzige Kennzahl, die sich seit der letzten Durchsicht
verschlechtert hat.

---

## 3. Konsolidierte Lückenliste

Priorität: **P0** = produktiv defekt oder Sicherheitsrisiko · **P1** = Betrieb/Prozess ·
**P2** = Produktentwicklung · **P3** = Schulden und Konsistenz.
Aufwand: S ≤ 1 Tag · M ≤ 1 Woche · L ≤ 4 Wochen · XL darüber.

### P0 — Sofort

| ID | Lücke | Aufwand | Beleg |
|---|---|---|---|
| ~~L-01~~ | ~~`.env.save` unignoriert im Repo~~ — **erledigt 2026-08-07**: `kompagnon/backend/.gitignore` deckt `.env*` ab | — | — |
| ~~L-02~~ | ~~Website-Check produktiv defekt~~ — **erledigt 2026-08-07**: Preflight liefert produktiv 200 mit allow-origin | — | — |
| ~~L-03~~ | ~~Embed-Widget nie deployt~~ — **erledigt 2026-08-07**: produktiv 200, echtes Widget. Rest: Staging liefert wegen `npx serve` die React-App, mit `--no-clean-urls` angleichen | S | Produktiv-Test |
| ~~L-04~~ | ~~Kein Rate-Limiting~~ — **erledigt 2026-08-15** (`82453bd`): Beim Beheben zeigte sich, dass der teurere Nachbar dasselbe Loch hatte und niemand ihn genannt hatte — `POST /api/audit/start` war ohne Anmeldung und ohne Grenze erreichbar, je Aufruf ein KI-Lauf plus PageSpeed, Screenshot und Crawl. Gezählt wird über Zeitpunkt und Zieladresse, ohne neue Spalte und ohne IP-Speicherung: 3 je Adresse und Tag, 40/Stunde und 200/Tag gesamt, 30 Leads/Stunde. Angemeldete bleiben frei; die Prüfung hängt als Abhängigkeit, damit die feineren Widget-Grenzen nicht gegeneinander arbeiten | — | — |
| L-41 | **Sieben von acht Startphasen liefen produktiv nie** — behoben am 2026-08-15 (`347379b`), aber die Ursache bleibt: Alle Phasen teilten einen Worker, die 215 s lange Migration hielt ihn, der Rest lief in Timeouts ohne je zu starten. Produktiv gab es dadurch monatelang keinen Scheduler. **Offen bleibt die Wurzel: L-34** | — | `stand-2026-08-15.md` § 7 |
| ~~L-43~~ | ~~PageSpeed-Schlüssel an sieben Stellen unsichtbar~~ — **erledigt 2026-08-16** (`6100240`): In Render heißt die Variable `PAGESPEED_API_KEY`, im Code hieß sie `GOOGLE_PAGESPEED_API_KEY`. Am 11.08. wurde das in `services/audit_pagespeed.py` behoben — **nur dort**. Leadliste, Kundenkarte, Projektmessung, Nutzerkarte, Anreicherung und der nächtliche Lauf lasen weiter allein den langen Namen und liefen ohne Schlüssel. Nichts scheiterte: PageSpeed v5 antwortet auch anonym, nur auf winzigem Kontingent — die Messung fällt unter Last aus und liefert eine Null, die wie ein Ergebnis aussieht. `/api/diagnostics/config` meldete derweil „gesetzt (als PAGESPEED_API_KEY)", weil dieser Endpunkt den Zweitnamen kennt und die Aufrufer nicht. **Damit ist die Aussage vom 15.08., § 6.1 sei mit dem gesetzten Schlüssel geklärt, nur für den Audit-Pfad richtig gewesen** | — | 11 neue Tests, `test_pagespeed_schluessel.py` |
| ~~L-42~~ | ~~`ENVIRONMENT` produktiv nie gesetzt~~ — **erledigt 2026-08-15**: Die Variable existierte nicht, der Code-Vorgabewert `development` griff. Dadurch wurden Demo-Konten produktiv *angelegt* und nie deaktiviert, und ein fehlender `SECRET_KEY` wäre stillschweigend durch einen flüchtigen ersetzt worden. Drei Demo-Konten waren aktiv und sind deaktiviert | — | — |
| ~~L-39~~ | ~~Datenbank-Zugangsdaten über `/info` abrufbar~~ — **erledigt 2026-08-15**: Endpunkt geschlossen (`2f687b2`, produktiv verifiziert), Zugangsdaten in **beiden** Umgebungen rotiert und die alten gelöscht, ohne Ausfall. Dabei zeigte sich der Unterschied, der zählt: Staging blockt jeden externen Verkehr, die preisgegebenen Daten waren dort wertlos — die Produktiv-DB nimmt Verbindungen aus dem ganzen Internet an, dort war die Preisgabe verwertbar | — | — |
| L-05 | ~~`RolePermission` ohne jede Wirkung~~ **dritter Schritt 2026-08-19:** Durchgesetzt sind jetzt **fuenf statt zwei** Rechte — dazugekommen `delete_leads`, `manage_users` und `manage_settings`, also die, mit denen etwas Unwiderrufliches passiert. Neu dafuer: `verlangt_recht(...)` als Abhaengigkeit; der Unterschied zu `require_admin` ist der Punkt — die Rolle sagt, wer jemand ist, das Recht sagt, was er darf. Die Admin-Routen waren zwar geschuetzt, aber ueber die **Rolle**, weshalb das Haeckchen weiter wirkungslos blieb. **Bewusst nicht durchgesetzt:** `deploy_kas_pages` und `manage_system_settings` — beide hat per Vorgabe nur der Superadmin, sie durchzusetzen waere eine Verhaltensaenderung und naehme dem Admin etwas weg, das er heute tut. Vorher, 2026-08-18: `services/rechte.py` liest die Tabelle (gespeicherte Eintraege stechen `DEFAULT_PERMISSIONS`), und `require_innendienst` fragt sie nach `view_leads`. Damit tut der Haken beim Auditor etwas — nachgewiesen: Recht entzogen → 403, zurueckgegeben → 200. Superadmin und Admin bleiben immer drin, sonst sperrt ein Haken den letzten aus, der ihn wieder wegnehmen koennte. **Offen bleiben 14 der 16 Rechte** — sie haengen an keiner Sperre. Der Bildschirm kennzeichnet sie jetzt als *beschreibend*, statt sie wie wirksame Haken aussehen zu lassen; die Zahl der grauen Marken ist selbst der Befund | M | `tests/test_rechte.py` |

| L-51 | ~~55 Werkzeug-Routen ohne Anmeldung~~ **geschlossen 2026-08-19** (`f4d06cd`): Nicht geschaetzt, sondern gezaehlt — **499 Routen ohne Anmeldung durchgerufen, 90 antworteten**. Produktiv nachgemessen: `/api/dashboard/kpis` gab die Marge (97,5 %), `/api/dashboard/projects-by-phase` Kundennamen samt Marge je Projekt, `/api/audit/recent` die letzten Audits mit Firmenname, `/api/audit/lead/58` **187 KB** vollstaendige Audit-Daten, durchzaehlbar ueber die lead_id. Zwei handelten wirklich: `POST /api/scheduler/restart` startete den Scheduler neu, `POST /api/scraper/run` begann einen Lauf. Ursache wie am 14.08. und 17.08.: Die Anmeldung hing an der einzelnen Route — `briefings.py` hatte elf geschuetzte und drei vergessene, `sitemap.py` achtzehn und eine. Jetzt tragen elf Router eine Vorgabe, fuenf Routen sind einzeln gesperrt (ihr Router traegt etwas, das offen bleiben muss). Offen: 90 -> 42, veraendernd 47 -> 21; die 42 sind saemtlich gewollt oeffentlich | — | `test_zugriffsschutz_werkzeug.py` (60 Tests) |
| ~~L-52~~ | ~~**Audits sind ohne Anmeldung durchzaehlbar.**~~ — **geschlossen 2026-08-19**: Das Audit bekommt beim Anlegen ein Geheimnis (`public_token`), `POST /start` gibt es zurueck, und wer nicht angemeldet ist, braucht es zum Lesen — beim Detail **und** beim Zwischenstand, sonst verriete der eine Weg, was der andere verschweigt. 404 statt 403: Ob es ein Audit mit dieser Nummer gibt, ist bereits eine Auskunft. Bestandsdaten ohne Geheimnis bleiben nur angemeldet erreichbar; ein Audit von gestern holt niemand mehr ueber die Landingpage ab. Alle drei oeffentlichen Abholer fuehren das Token jetzt mit (`websprint-landing.html`, `AuditHook.jsx`, `useAudit.js`). Urspruenglicher Text: `GET /api/audit/{id}` und `/api/audit/status/{id}` bleiben offen, weil die oeffentliche Landingpage ihr Gratis-Audit damit abholt — wer hochzaehlt, liest fremde Ergebnisse. Das Widget macht es richtig vor: Es liefert seinen Bericht unter `/api/widget/report/{token}`. Derselbe Weg fuer den Audit waere die Loesung, ist aber ein Umbau an der Landingpage und keine Sperre | S | `test_zugriffsschutz_werkzeug.py` |
| ~~L-53~~ | ~~**Zwei offene Routen antworten produktiv mit 500.**~~ — **geschlossen 2026-08-19**, und es waren zwei verschiedene Dinge. `/api/dashboard/alerts`: **nachgestellt statt geraten** — `scope_creep_flags` war `NULL`, und `NULL > 0` ist ein `TypeError`. Das `default=0` im Modell ist eine Python-Vorgabe und greift nur beim Anlegen ueber das Modell. Ein einziges solches Projekt nahm die gesamte Alarmliste mit. Behoben am Lesezugriff **und** in den Daten (`UPDATE … WHERE … IS NULL`). `/api/payments/session/{id}`: **kein Absturz** — der Endpunkt warf die 500 absichtlich, weil `STRIPE_SECRET_KEY` fehlt. 500 ist dafuer die falsche Auskunft; sie landet in jeder Alarmierung und gewoehnt einen an rote Zahlen. Jetzt 503, wie es das Haus an fuenf anderen Stellen bereits macht (drei Stellen umgestellt). Urspruenglicher Text: `GET /api/dashboard/alerts` (`TypeError`) und `GET /api/payments/session/{id}`. Beide am 19.08. am laufenden Dienst gemessen. `alerts` ist inzwischen hinter der Anmeldung, der Fehler bleibt — er wurde nur nie bemerkt, weil niemand hinsah. **Nicht auf Verdacht repariert:** Der Code hat zwei plausible Stellen (`datetime.utcnow() - project.start_date`, falls die Spalte produktiv `timestamptz` ist, und `sum(entry.hours)` bei `NULL`-Stunden), und lokal antwortet die Route mit 200, weil dort keine Projekte liegen. Was fehlt, ist der Traceback — den liefert das Fehlerprotokoll aus L-10, sobald es produktiv ist | S | Produktiv-Messung 19.08. |

| L-54 | ~~**Die Kundenkennung der Akademie ist zweideutig.**~~ **weitgehend geschlossen 2026-08-19:** Neue Zeilen werden beim Schreiben aufgeloest, und ein Nachtrag in der Startphase (`services/zuweisung_kennung.py`) zieht Altzeilen nach — aber **nur wo er sicher ist**: Ist die Zahl zugleich eine gueltige Benutzernummer, bleibt sie liegen und wird gemeldet. Raten waere dort schlimmer als nichts tun, denn ein falsch geratener Eintrag schaltet einem fremden Betrieb etwas frei. **Offen bleibt damit genau der zweideutige Rest** — er steht im Startprotokoll und ist von Hand zu entscheiden. Urspruenglich: Das Kundenblatt ruft `/api/academy/customer/{id}/…` mit der **Betriebs-ID** (`lead.id`, `LeadProfile.jsx`), waehrend die Akademie alles andere ueber die **Benutzer-ID** fuehrt (`AcademyProgress.user_id`, `AcademyCertificate.user_id`). Folgenlos, solange **niemand** die Zuweisung abfragte — und genau das hat sich am 19.08. geaendert (L-55). Neue Zuweisungen werden jetzt beim **Schreiben** aufgeloest und als Benutzer-ID gespeichert; beim Lesen beide Kennungen zuzulassen waere eine Hintertuer, denn die zwei Zahlenraeume laufen unabhaengig und ueberschneiden sich (im Testbestand nachgewiesen: fremde Betriebs-ID 2 = Benutzer-ID 2). **Offen bleiben alte Zeilen**, die noch eine Betriebs-ID enthalten. Heute ungefaehrlich, weil kein einziger Kurs gesperrt ist — die Sperre ist neu und steht ueberall auf `false`. Gefaehrlich wird es mit dem ersten gesperrten Kurs. Nebenbefund derselben Wurzel, **beilaeufig mitrepariert**: `get_customer_courses` reichte die Betriebs-ID an `_progress_summary(…, user_id)` und an die Zertifikatssuche weiter — der Fortschritt im Kundenblatt bezog sich auf einen Benutzer, den es unter dieser Nummer meist nicht gibt, und zeigte stillschweigend null. Seit die Kennung beim Eintritt aufgeloest wird, stimmt er; ein eigener Test haelt das fest, damit eine beilaeufige Reparatur nicht beilaeufig wieder verschwindet | S | `routers/academy.py::_kunde_user_id` |
| L-55 | ~~Zuweisung und Modulsperre ohne jede Wirkung~~ — **geschlossen 2026-08-19**: `AcademyCustomerAccess` (Tabelle, drei Endpunkte, Oberflaeche) wurde von **keinem** Lesepfad abgefragt; einem Kunden einen Kurs zuzuweisen bewirkte nichts. `AcademyModule.is_locked` war gespeichert, im Admin anklickbar, serialisiert — und nirgends gelesen. Dieselbe Familie wie L-05. Statt neuer Felder haben die vorhandenen ihre Bedeutung bekommen (Memberspots „Manuell"), dazu `AcademyCourse.is_locked` und `academy_module_access`. **Vorgabe bleibt offen**, damit der Bestand nicht vor den Augen der heutigen Kunden verschwindet | — | `test_akademie_zuweisung.py` (18 Tests) |

| L-56 | **Einen Betrieb mit Kundenzugang loeschen ging nicht — und sagte es nicht.** `DELETE /api/leads/{id}` raeumt fuenfzehn abhaengige Tabellen ab, aber nicht `users.lead_id`; der Fremdschluessel schlug unbehandelt durch und wurde zu **500** mit einer Meldung, aus der niemand schliessen kann, was zu tun ist (gefunden 19.08. beim Verdrahten von L-05). Jetzt **409** mit Klartext: welcher Zugang im Weg steht. Das kann nichts brechen, denn der Aufruf scheiterte ohnehin. **Offen bleibt die Entscheidung:** Soll das Loeschen eines Betriebs das Konto seines Kunden mitnehmen? Das ist Datenschutz und keine Zeile Code — und es beruehrt die Loeschfunktion vom 17.08. | S | `test_rechte_wirken.py` |

| L-57 | **Der Produktiv-Dienst laesst sich nicht mehr von Grund auf bauen.** Sein Build-Befehl endet auf `python -m playwright install chromium && … install-deps chromium`, aber `playwright` steht in **keiner** `requirements.txt` — weder auf `staging` noch auf `main`. Am 19.08. bewiesen: Der neue Frankfurter Dienst, mit demselben Befehl und demselben Commit `29e7e15`, scheiterte nach 28 s mit „No module named playwright". Oregon laeuft nur deshalb, weil sein letzter Deploy ein **wiederverwendetes** Build-Artefakt war (Ausloeser „Environment updated", 46 s — zu schnell fuer einen echten Build). **Folge:** Ein erzwungener Neubau, ein Cache-Verlust bei Render oder ein Rollback wuerde produktiv fehlschlagen. Der Befehl ist ueberdies gegenstandslos — Screenshots kommen ueber externe Dienste (`services/screenshot.py`), das Backend braucht keinen Browser. **Zu tun:** die zwei Playwright-Zeilen aus dem Oregon-Build-Befehl entfernen, dann einen Testbau ausloesen | S | Build-Protokoll `dep-da30dh3bc2fs73fomls0` |

### P1 — Betrieb und Prozess

| ID | Lücke | Aufwand | Beleg |
|---|---|---|---|
| ~~L-06~~ | ~~Produktiv-Rückstand~~ — **erledigt 2026-08-07**: PR #34 gemergt (36 Commits), produktiv deployt und verifiziert | — | — |
| L-07 | ~~`main` ohne Branch-Protection~~ **korrigiert 2026-08-07:** `main` ist über Rulesets geschützt (`protect-main`), die die klassische Protection-API nicht meldet. Offen bleibt: die Regel „Restrict updates" blockiert jeden Merge, und die zwei neuen Prüfjobs sind nicht als Pflicht-Checks eingetragen | S | `gh api repos/…/rules/branches/main` |
| L-08 | Dependabot-Alerts deaktiviert. **Nachgemessen 2026-08-19: 51 npm-Befunde (2 kritisch, 24 hoch)** — davon **zwei direkt**, der Rest haengt an `react-scripts`. `axios` 1.14 → 1.19 gehoben (SSRF ueber NO_PROXY, Authentifizierungs-Umgehung ueber Prototype Pollution); 325 Frontend-Tests und Build danach gruen. **Nicht gehoben: `grapesjs` 0.22 → 0.23** — der Seiteneditor, und ein Sprung der Nebenversion gehoert angesehen, nicht durchgewinkt. Die transitiven Befunde loesen sich erst mit dem Abschied von `react-scripts` (haengt an L-26) | M | `npm audit` |
| L-09 | Testabdeckung — **Stand 2026-08-15: 927 Backend- + 98 Frontend-Tests**, vier Pflichtjobs, dazu eine eingefrorene Referenz-Website für die Erhebung (`tests/referenzseite.py`). Weiterhin offen: Wireframe, Style-Guide-Freigabe, Design-View, Zahlungen | M | `backend/tests/`, `frontend/src/utils/*.test.js`, `e2e/` |
| L-10 | ~~Kein Monitoring / Fehler-Tracking~~ **geschlossen 2026-08-18:** eigenes Fehlerprotokoll (`database.Fehlerprotokoll`, `services/fehlerprotokoll.py`, `GET /api/fehler/`, Bildschirm unter Verwaltung, taegliche Aufraeumung nach 30 Tagen). Bewusst im eigenen Haus statt bei Sentry — Fehlerberichte enthalten Kundendaten. Dabei gefunden: **zwei** gleichnamige `@app.exception_handler(Exception)`, der zweite ueberschrieb den ersten | — | `tests/test_fehlerprotokoll.py` |
| L-11 | ~~Keine dokumentierte Backup- und Wiederherstellungsstrategie~~ — **Doku geschrieben 2026-08-19**: `docs/sicherung-und-wiederherstellung.md`. Dabei der eigentliche Punkt: **Eine DB-Sicherung rettet den Betrieb nicht.** Drei Dinge sind zu sichern, und nur eines liegt in der Datenbank — dazu der Datentraeger `/var/data` (erst seit 18.08. vorhanden, in keiner DB-Sicherung, zieht beim Umzug nicht mit) und die Schluessel: Ohne `CMS_ENCRYPTION_KEY` und `CREDENTIALS_KEY` sind gespeicherte Zugangsdaten auch nach vollstaendiger Wiederherstellung unlesbar. **Offen bleibt zweierlei, beides bei David:** die Aufbewahrungsdauer von Renders Wiederherstellungspunkten (Dashboard; der MCP ist den zweiten Tag `unauthorized`) und die Probe — **es wurde noch nie eine Wiederherstellung durchgefuehrt**, und damit ist „wie lange dauert es" unbeantwortet | S | `sicherung-und-wiederherstellung.md` |
| L-12 | ~~`require_auditor` an keiner Route~~ **geschlossen 2026-08-18 — und der Faden fuehrte zu drei echten Loechern:** Rolle `nutzer` bekam ueber `GET /api/leads/` den vollstaendigen Bestand (200), ein angemeldeter Kunde die ganze Kundenkartei ueber `/api/customers/` und `/api/usercards/` (200, `usercards.py` war am 17.08. uebersehen worden, samt Alias-Routern), und die Zeilenpruefung auf `GET /api/leads/{id}` fragte dasselbe Falsche. Alle drei nennen jetzt, **wer darf** (`INNENDIENST`), statt aufzuzaehlen, wer nicht darf | — | `tests/test_zugriffsschutz_kundenkartei.py` |
| L-13 | ~~`.claude/settings.json` getrackt trotz `.gitignore`~~ **geschlossen 2026-08-18:** `.claude/*` ignoriert, `settings.json` ausgenommen — die Datei beschreibt das Verhalten *dieses* Repos. Dabei die Push-Regel selbst ueberarbeitet: Sie pusste nach jedem Bash-Schritt und brach damit laufende CI-Laeufe ab (`cancel-in-progress`); jetzt wartet sie, solange ein Lauf laeuft (`scripts/push-wenn-ruhig.sh`, fuenf Tests) | — | `.gitignore`, `tests/test_push_regel.py` |
| L-40 | Qualitätsschleife nicht scharf geschaltet: `NETLIFY_VORSCHAU_SITE_ID` fehlt, deshalb ist der Durchstich Editor → Netlify → Audit → PDF nie am Stück gelaufen. Ohne die Variable antwortet der Endpunkt sauber mit 503 | S | `services/qualitaetsschleife.py` |
| ~~L-47~~ | ~~Sieben Webhook-Endpunkte nahmen unsignierte Fremdanfragen an~~ — **im Code behoben 2026-08-16** (`b8cd1b7`), **produktiv offen bis zum Merge**. Drei Signaturprüfungen trugen dieselbe Konstruktion: `if SECRET:` bzw. `if not secret: return True`. Fehlte die Variable, fand **keine Prüfung** statt — und produktiv war keine der drei je gesetzt. Fünf der sieben schreiben Leads in die Datenbank. Live gemessen vor dem Fix: `POST /api/webhooks/facebook`, `/linkedin`, `/google`, `/telefon` antworteten ohne Signatur mit 200. Jetzt: 403 mit Protokolleintrag, Geheimnis je Aufruf gelesen. **Vor dem Merge die drei Geheimnisse setzen**, sonst stirbt eine etwaige laufende Anbindung | — | 13 Tests, `test_webhook_signaturen.py` |
| ~~L-48~~ | ~~Der Selbstaufruf des Servers ging ins Leere~~ — **erledigt 2026-08-16** (`f72a292`): `webhooks.py` nahm die interne Adresse **ohne Port** (80 statt 10000), `leads.py` ging über das öffentliche Netz und fiel auf `localhost:8000` zurück. Beides scheitert leise: Der Audit startet nicht, der Lead bleibt unbewertet, im Protokoll steht eine Warnung. Jetzt `services.base_urls.self_base_url()` | — | 4 Tests |
| ~~L-49~~ | ~~`trade` wurde weiter als Befund gedruckt~~ — **erledigt 2026-08-16** (`b8cd1b7`): Der Fix vom 14.08. schützte nur den Widget-Weg. `useAudit` sendete `lead.trade` bei **jedem aus einem Lead gestarteten Audit** mit — der Hauptweg. Gedruckt wurde die Vermutung in zwei kundenwirksamen Dokumenten, die der 14.08. nicht anfasste: Angebots-PDF-Deckblatt und Kaltakquise-Anschreiben. Ein Ingenieurbüro wurde als „Schreiner" angeschrieben, mit dem Protokoll im Anhang, das korrekt „Ingenieurbüro" sagte. Damit sind § 7 und § 8 des Anforderungskatalogs geschlossen | — | `test_pdf_protokoll_branche.py` |
| ~~L-50~~ | ~~Absolute Backend-Adressen im gespeicherten Seiteninhalt~~ — **erledigt 2026-08-16**: Gezählt statt geschätzt — 0 von 170 Kunden-Editorseiten, 0 von 19 Wireframes, **2 von 2** eigenen KAS-Seiten. Die zwei umgeschrieben, mit Längen- und JSON-Prüfung. Offen als eigene Frage: `project_files` speichert lokale Pfade, kein `disk:`-Block in den Blueprints — die eine vorhandene Datei ist bereits verloren | S | `umzug-backend-frankfurt.md` |
| ~~L-45~~ | ~~Auto-Deploy stand produktiv auf „On Commit"~~ — **erledigt 2026-08-16**: Auf **beiden** Produktiv-Diensten. `ci.yml` nennt in Zeile 265 ausdrücklich die Voraussetzung „Auto-Deploy ist in Render für die Produktiv-Services abgeschaltet, sonst deployt Render parallel und der Torwächter hier ist wirkungslos" — sie war nie erfüllt. Jede Änderung an `main` ging live, unabhängig von den sechs Prüfjobs. Beide jetzt auf „Off". Alltagsfolge: Variablenänderungen wirken erst nach einem ausgelösten Deploy | — | Render-Dashboard, `ci.yml:265` |
| ~~L-46~~ | ~~Adresse der Oberfläche an dreizehn Stellen fest im Code~~ — **erledigt 2026-08-16** (`d559816`): Dieselbe Bauart wie L-43, eine Ebene weiter — Stripe-Rückleitungen, Kundenportal-Link, QR-Code, Phasenwechsel-Mails, Nachtlauf. Alle über `services.base_urls.public_base_url()`; zwei Modul-Konstanten entfallen, die die Umgebung beim *Import* lasen | — | `kas.kompagnon.group` |
| L-44 | **Inbound-Regel der Produktiv-DB steht auf `0.0.0.0/0`.** Am 2026-08-16 erhoben, wer sie heute braucht: nur zwei — das Backend in Oregon (entfällt mit L-34) und ein Rechner mit DBeaver. Dabei ein Widerspruch: `local-dev-with-render-db.md` beschreibt genau diesen Weg und schreibt „Nur Staging-DB nutzen" — die Staging-DB blockt externen Verkehr seit jeher, der dokumentierte Weg funktioniert also allein gegen die DB, vor der die Anleitung warnt. Ersatz ohne offene Regel: Render-Shell und `render psql`. **Reihenfolge zwingend: erst L-34, dann diese Regel** | S | `umzug-backend-frankfurt.md` § L-40 |
| L-34 | **Produktiv-Backend läuft in Oregon (US West)**, Datenbank in Frankfurt. **Plan liegt: `umzug-backend-frankfurt.md`.** **Am 2026-08-15 als Ursache zweier Folgeschäden bestätigt:** Die Startphasen kippten an der Latenz (L-41), und die Datenbank *muss* im offenen Internet stehen, weil ein Backend in Oregon die interne Adresse einer Frankfurter DB nicht erreicht (L-40). Nicht mehr nur Performance — der größte einzelne Hebel im System. **Am 2026-08-19 zur Hälfte erledigt:** Der Frankfurter Dienst `kompagnon-backend-fra` (`srv-da30dg3bc2fs73fomi0g`) läuft, antwortet in **0,18 s gegen Oregons 3,1 s**, erreicht die Datenbank über die **interne** Adresse und startet in 60 s statt 264 s mit leerem `startup_missing`. `GET /openapi.json` zeigt auf beiden Diensten **401 Routen, null Abweichung** — dieselbe Anwendung. Er trägt noch **keinen Verkehr**; der Zustand ist vollständig umkehrbar. **Offen:** Branch prüfen → L-57 → Webhooks → Domain → Repo-Variable → alten Dienst suspendieren. Reihenfolge und Rückweg in `umzug-backend-frankfurt.md` | L | Health-Check 0,9–2,2 s produktiv vs. 0,12–0,18 s Staging; DNS der externen DB-Adresse |
| L-35 | Blueprints beschreiben nicht die Realität: Produktiv-Frontend ist Static Site statt Web-Service, DB heißt `Kompangnon-dB` auf Postgres 18 statt `kompagnon-db` auf 16, Produktiv-Services sind nicht blueprint-verwaltet. **Am 2026-08-16 zur Hälfte geschlossen** (`27f14dd`): `render-produktiv.yaml` beschreibt den neuen Frankfurt-Dienst mit 41 Variablen — der alten Datei fehlten 32, darunter vier der sechs Webhook-Geheimnisse sowie `CREDENTIALS_KEY` und `CMS_ENCRYPTION_KEY`. Offen bleibt das Anwenden, und das hängt an L-34 | S | `render-produktiv.yaml` vs. `render.yaml` |
| ~~L-36~~ | ~~Fehler werden im Frontend systematisch weggefangen~~ — **erledigt 2026-08-08**: 67 leere catch-Blöcke in 36 Dateien beseitigt, null verbleibend. Neuer Helfer `utils/apiRequest.js` (`loadJson`/`saveJson`/`apiRequest`) mit 15 jest-Tests, erstmals Frontend-Unit-Tests in der CI. Dabei gefunden: neun Speicher-Aktionen, die Erfolg meldeten, ohne den Status je zu prüfen — darunter Go-Live („Website ist live! 🎉" trotz gescheitertem PUT), Briefing-Autosave, QA-Checkliste und Bild-Uploads. Bewusst stille Stellen (Keepalive, Brotkrumen, Passwort-vergessen) tragen jetzt `quiet` mit Begründung | — | — |
| ~~L-37~~ | ~~Newsletter komplett tot: `import brevo_python` scheitert immer, weil `brevo-python` das Modul `brevo` liefert~~ — **erledigt 2026-08-08**: Anbindung auf die REST-API v3 über httpx umgestellt, SDK aus den Requirements entfernt, 15 Tests ergänzt. Gleich mitgefunden: Statistik las `open_rate`/`click_rate`, die es bei Brevo nicht gibt (heißt `opensRate`, Klickrate gar nicht) → Analytics zeigte immer leere Werte; Massenimport zählte abgelehnte Kontakte als importiert | — | — |
| L-38 | Der Mai-Audit führt „Brevo-Stats ✅" und „Brevo-Contact-Sync ✅" als geprüft — beides konnte nie funktioniert haben. Abhaken ohne Ausführung ist der gleiche blinde Fleck wie L-36, nur eine Ebene höher | S | `docs/audit-2026-05-04.md:148,165` |

### P2 — Produktentwicklung

| ID | Lücke | Aufwand | Beleg |
|---|---|---|---|
| L-14 | Projekt-Assistent — **Ausbau 1 gebaut** (`routers/assistant.py`). Offen: fachliche Beurteilung durch David oder einen Handwerksbetrieb, Ausgangswerte der Abschlussquote, Ausbau 2 (Projektbegleitung) | M | `docs/projekt-assistent-anforderungen.md` § 9.6 |
| L-15 | Hormozi-Offer-Stack fehlt im `content_writer` — seit Mai unverändert | M | kein Bezug im Agenten auffindbar |
| L-16 | Envato-Wireframe-Pipeline steckt in Phase 1 (2 von 8–15), wartet auf Pattern-Notes | L | Plan-Status im Memory |
| L-17 | Keine Barrierefreiheit im Tool — **nachgemessen 19.08.: 20 von 182 Dateien** fuehren ueberhaupt ARIA (die alte Zahl 12/167 war aehnlich schlecht). **Eine Klasse geschlossen:** Zwanzig Schaltflaechen bestanden nur aus einem Symbol — `×`, `✕`, `✓`, `✏️`, `🗑`, `+` — ohne `aria-label`. Ein Screenreader liest daraus „mal" oder nichts. Das ist WCAG 4.1.2 und damit genau das, was wir bei Kunden pruefen; ein Werkzeug, das BFSG-Konformitaet verkauft und namenlose Knoepfe hat, ist schwer zu verteidigen. Ein Waechter haelt die Regel, nicht die zwanzig Stellen. **Offen bleibt das Thema:** Tastaturbedienung, Fokusreihenfolge, Ueberschriftenhierarchie, Formularbeschriftungen und Kontraste sind ungeprueft — eine Klasse ist kein Zustand  **Zweite Klasse gemessen, 21.08. — Formularfelder und Ueberschriften:** **399 Formularsteuerelemente** (ohne `hidden`/`submit`/`button`) im Frontend, davon tragen **18 einen programmatisch lesbaren Namen** — 8 ueber `aria-label`/`aria-labelledby`, 10 ueber eine eigene `id`, auf die ein `htmlFor` zeigt. **381 von 399 (95 %) haben keine Verknuepfung**; von 84 Dateien mit Formularfeldern hat ganze **6** ueberhaupt ein benanntes Feld. Der Punkt ist aber nicht, dass die Beschriftungen fehlen: Im Quellbaum stehen **209 `<label>`-Elemente und 13 `htmlFor`** — sichtbar ist fast alles beschriftet, **verknuepft fast nichts**. Das ist WCAG 1.3.1/4.1.2 und billiger zu beheben als es aussieht: Nicht 381 Beschriftungen schreiben, sondern 381 verknuepfen. **Ueberschriften, 63 Seiten:** 24 ohne jedes `<h1>` (10 davon ohne jede Ueberschrift), 7 mit uebersprungener Stufe (`h1` → `h3`), `AkquiseWidget.jsx` faengt bei `h3` an und geht dann auf `h2`. **Dabei der eigentliche Fund:** `components/ui/PageHeader.jsx` erzeugt ein korrektes `h1` — und wird von **0 der 63 Seiten** benutzt. Gebaut, nie angeschlossen; dieselbe Familie wie L-55. **Zur Methode, weil sie beinahe schiefgegangen waere:** Ein erster Lauf teilte die Felder in Klassen (gar nichts / Label daneben / in einer Huellkomponente). Die Handprobe fand in zwei Runden **drei Fehlklassifizierungen** — `<Lbl>Phase</Lbl><select>` und `<Field label=…>` sind fuer einen Musterabgleich nicht auseinanderzuhalten. Berichtet ist deshalb nur, was sich **positiv** pruefen laesst: Ein Name ist da oder nicht. Siehe [[feedback-am-gegenstand-pruefen]] | L | `utils/knopfName.test.js` |
| L-18 | In-App-Benachrichtigungen fehlen (nur E-Mail-Schalter vorhanden) | M | kein Notification-Modell |
| L-19 | KAS-Verkaufsseiten ohne Custom-Domain-Endpunkt — hängen auf `*.netlify.app` | S | `netlify_service.py:90`, kein KAS-Domain-Router |
| L-20 | WebSprint-Landingpage außerhalb des Systems, ohne Quellversionierung (53 KB lokal vs. 914 KB live) | M | Größenvergleich |
| L-21 | Google Ads / Meta Ads: null Code — Stage 3 der Vision blockiert | XL | keine SDK-Referenz |
| L-22 | Analytics/Umami: Plan vorhanden, null Code — ohne Tracking keine Funnel-Optimierung | L | keine Umami-Referenz |
| L-23 | Component-Manager Phase 2 (React-Eingabe) zurückgestellt | M | Plan im Memory |
| L-24 | ROADMAP-P1-Restpunkte: LeadProfile-Tabs, weitere Kundenportal-Wünsche | M | `ROADMAP.md` |
| L-58 | **Der Audit-Katalog misst KI-Sichtbarkeit mit keinem einzigen Kriterium** — nachgezaehlt am 21.08.: 8 Kategorien, **42 Kriterien, 100 Punkte**, kein Treffer auf KI, ChatGPT, Perplexity oder AEO. Gefunden am HubSpot-Konto, dessen `/ai-visibility/` (Beta) genau das aus **Marke + Domain** prueft — beides steht bei uns im Lead. **Der Fund ist nicht, dass uns die Technik fehlt, sondern dass sie am falschen Objekt haengt:** `GeoAnalysis` misst llms.txt, KI-Bot-Regeln in robots.txt, strukturierte Daten, Inhaltstiefe und lokale Signale — aber der Fremdschluessel ist `project_id`, also ein Kunde, den wir **schon gewonnen haben**. Der Tueroeffner-Audit am Lead sieht davon nichts. Zerfaellt in zwei Stuecke ungleicher Groesse: **(a)** die vorhandene GEO-Erhebung als Kriterium in den Lead-Audit ziehen — sie misst *Lesbarkeit fuer KI* und laeuft bereits; **(b)** *tatsaechliche Sichtbarkeit* — ob eine Maschine den Betrieb auf eine Frage hin **nennt** — wird bei uns **nirgends** gemessen und kostet je Lauf Geld. (a) ist Verdrahtung, (b) ist ein Produkt | M | `audit_criteria.py` (42 Kriterien), `database.py:1092` (`GeoAnalysis.project_id`) |
| L-59 | ~~**Wir pruefen bei Kunden, was wir bei uns selbst nicht fuehren: die Rechtsgrundlage.**~~ — **geschlossen 2026-08-21.** `audit_collectors.py:255` sucht auf fremden Seiten nach „Art. 6", `netlify_service.py:531` schreibt sie in erzeugte Seiten, `pdf_generator.py:427` druckt eine Spalte dafuer; am eigenen Lead: 79 Felder, keines nannte sie. **Jetzt `services/lead_quellen.py`** — ein gefuehrter Wortschatz aus 14 Quellen, je mit Herkunft, Rechtsgrundlage und **Beleg** (Datei und Zeile, an der die Quelle geschrieben wird). Das Betriebsblatt zeigt beides jetzt **immer**, nicht nur bei gesetztem `utm_source`. **Getrennt gehalten, weil es zwei verschiedene Dinge sind:** Die **Herkunft** (selbst gemeldet / von uns erhoben) ist am schreibenden Pfad ablesbar und keine Rechtsauskunft. Die **Rechtsgrundlage** ist eine — eingetragen ist deshalb nur `stripe_checkout` → Art. 6 I b, weil dort der Lead erst nach abgeschlossener Zahlung entsteht. Die uebrigen **elf stehen offen und sind ueber `quellen_ohne_rechtsgrundlage()` als Liste abrufbar**; sie sind von David zu entscheiden. Raten waere hier schlimmer als nichts tun — ein geratener Eintrag saehe aus wie ein geprueftes Ergebnis. **Beim Messen fielen drei Dinge auf, die niemand gesucht hatte:** (1) `AUTO_SEQUENCE_SOURCES` (`leads.py:181`) nennt acht Werte, von denen **fuenf nirgends geschrieben werden** (`landing_page`, `llm_landing`, `webhook_facebook`, `webhook_linkedin`, `webhook_google`) — die Webhooks schreiben `facebook`/`linkedin`/`google`. (2) `postkarte` steht in beiden Listen und greift trotzdem nicht: Die Webhooks schreiben ueber `_upsert_lead` mit rohem SQL und laufen an `create_lead` vorbei, wo die Liste gelesen wird. (3) `leads.py:1354` schrieb **`Manuell`**, drei Frontend-Stellen schreiben **`manual`**, und der Quellenfilter vergleicht auf `manual` — von der Backend-Seite von Hand angelegte Betriebe waren ueber „Von Hand" **nicht zu finden** und bekamen eine eigene Gruppe. Vereinheitlicht, Bestand mitgezogen. **Nicht geaendert:** wer eine automatische Mailstrecke bekommt. Die Liste zu reparieren hiesse, Kaltakquise-Betrieben ploetzlich Mails zu schicken — das ist eine Entscheidung und keine Aufraeumarbeit (siehe L-62) | — | `test_lead_quellen.py` (39 Tests), `leadStatus.test.js` |
| L-62 | **Fuenf von acht Werten in der Mailstrecken-Liste greifen ins Leere — und der Rest greift aus einem zweiten Grund nicht.** Gemessen am 21.08. beim Schliessen von L-59. `AUTO_SEQUENCE_SOURCES` (`routers/leads.py:181`) entscheidet, wer nach dem Anlegen automatisch eine E-Mail-Strecke bekommt. Sie nennt `landing_page`, `llm_landing`, `webhook_facebook`, `webhook_linkedin`, `webhook_google` — **keiner dieser fuenf Werte wird irgendwo geschrieben**. Die Webhooks schreiben `facebook`, `linkedin`, `google`, `postkarte`, `telefon` (`routers/webhooks.py:107-162`). Und selbst `postkarte`, das in beiden Listen steht, greift nicht: `_upsert_lead` schreibt mit rohem SQL und laeuft an `create_lead` vorbei, wo die Liste ueberhaupt erst gelesen wird. **Folge:** Von fuenf Lead-Wegen bekommt kein einziger die automatische Strecke, und niemand hat es gemerkt, weil das Ausbleiben einer Mail nichts protokolliert. **Bewusst nicht repariert:** Die Liste anzugleichen hiesse, ab dem naechsten Deploy Betrieben Mails zu schicken, die heute keine bekommen — darunter Kaltakquise. Das ist eine Entscheidung von David und beruehrt genau die Rechtsgrundlage aus L-59 | S | `routers/leads.py:181` gegen `routers/webhooks.py:107-162` |
| L-60 | **Die Akademie kann mehr als sie zeigt — es fehlt der Aufbau, nicht die Technik.** Am Memberspot-Konto gemessen (19.08.): Quiz, Fortschritt mit Punktzahl und **Zertifikate mit oeffentlicher Pruefung** haben wir bereits — genau das verkauft Memberspot ab 39 €/Monat. Was fehlt, ist die Gliederung, die daraus einen Kurs macht: `Kurs → Modul → Ordner → Lektion` mit **Status auf jeder Ebene** (veroeffentlicht / „Manuell" = nur Zugewiesene). Die Sperre dafuer ist seit L-55 wirksam, steht aber ueberall auf `false`, damit der Bestand den heutigen Kunden nicht wegbricht. **Zu tun:** eine Vorlage anlegen — Gratis-Startmodul, Pflichtstrang I–IV, sechs Abteilungs-Module auf „Manuell", ein Bonus — und den Bestand hineinsortieren | M | `docs/akademie-vorbild-memberspot.md`, `AcademyModule.is_locked` |

### P3 — Schulden und Konsistenz

| ID | Lücke | Aufwand | Beleg |
|---|---|---|---|
| L-25 | **Elf** Backend-Dateien über der 800-Zeilen-Grenze (`projects.py` 4.673, `leads.py` 2.196, `component_library.py` 2.100, `main.py` 2.050 …), dazu sechs im Frontend (`templates_zusatz.js` 3.121, `LeadProfile.jsx` 2.673). Am 2026-08-15 gezählt — **die einzige Kennzahl, die sich verschlechtert hat** | L | `wc -l` |
| L-26 | Drei Editor-Generationen parallel (`ProzessFlow`, `V3`, `OnlineFertigEditor`) | M | 3.723 Zeilen zusammen |
| L-27 | Zwei Briefing-Strukturen und zwei Briefing-Router parallel | M | `briefing.py` / `briefings.py` |
| L-28 | Zwei Template-Router (`templates.py`, `website_templates.py`) | S | Router-Inventar |
| L-29 | ~~**Preise an vier Stellen — und sie sind bereits auseinandergelaufen.**~~ — **geschlossen 2026-08-21.** Nachgemessen 19.08.: Premium stand in `payments.py` mit **2.800**, in `OfferTab.jsx` und `PricingSection.jsx` mit **2.500**; Kompagnon in `payments.py` mit **2.000**, in `Landing.jsx` an drei Stellen mit **3.500**. **Am 21.08. kam eine fuenfte Stelle dazu, die niemand gezaehlt hatte** — und es war die teuerste: `_handle_successful_payment` legte das Projekt mit einer zweiten festen Liste an (`{starter: 1500, kompagnon: 2000, premium: 2800}.get(package_id, 2000.0)`). Auf dieser Zahl rechnet `services/margin_calculator.py`. Ein Kunde, der 2.500 zahlte, bekam ein Projekt mit **2.800 Umsatz** eingetragen — die Marge war um 300 EUR zu hoch, und nichts im System haette widersprochen. Der Vorgabewert war der schlimmere Teil: Ein unbekanntes Paket bekam **2.000 EUR erfunden**, obwohl der tatsaechlich abgebuchte Betrag im selben Aufruf danebenstand. **Jetzt eine Quelle:** `projekt_festpreis(db, slug, bezahlt)` nimmt die Produktzeile, sonst den gezahlten Betrag, sonst **nichts**; die drei Verkaufsflaechen holen ihren Preis ueber `usePakete` aus `GET /api/payments/packages`, also aus derselben Zeile, aus der die Stripe-Sitzung ihren Betrag zieht. Faellt der Server aus, steht dort **kein Preis** statt eines veralteten. **Welcher Preis gilt, musste niemand entscheiden** — die Datenbank sagt es, der Quelltext behauptet es nicht mehr. Ein Waechter haelt die fuenf gemessenen Betraege aus den drei Dateien heraus | — | `test_paketbezeichnung.py`, `utils/paketpreise.test.js` |
| L-61 | **Die Verkaufsseite verspricht „zzgl. MwSt.", die Kasse schlaegt nichts auf.** Gefunden am 21.08. beim Schliessen von L-29. `PricingSection.jsx` schrieb „1.500 € **netto**" und darunter „zzgl. MwSt."; `OfferTab.jsx` verschickte „netto" im Angebotstext an den Kunden. Die Zahl stammt aber aus `products.price_brutto`, und `create_checkout` setzt `unit_amount = price_brutto * 100` — **ohne `automatic_tax`, ohne `tax_rates`**; beide kommen im ganzen Modul nicht vor. Der Kunde las 1.785 € und wurde mit 1.500 € belastet. Die Tabelle fuehrt beides getrennt: `price_brutto` 1.500,00 gegen `price_netto` 1.260,50. **Welche Seite sich bewegt, ist eine Entscheidung von David** — entweder die Kasse rechnet die Steuer auf (dann stimmt „netto"), oder die Preise sind Endpreise (dann muss die Beschriftung weg, auch aus der Angebotsmail). Bis dahin steht auf den Flaechen der Betrag, der **tatsaechlich abgebucht wird**, als „Gesamtbetrag" — die einzige Aussage, die unter beiden Lesarten heute wahr ist. **Ungeprueft geblieben:** was die Rechnung im PDF ausweist | S | `routers/payments.py::create_checkout`, `main.py:1446` (Seed) |
| L-30 | ~~`ROADMAP.md` enthaelt zwei widersprüchliche Roadmaps~~ — **gekennzeichnet 2026-08-19**: Nachgezaehlt, der Befund stimmt (Prioritaeten-Fahrplan ab Zeile 8, Zustands-Fahrplan ab Zeile 143). Die Datei sagt das jetzt im Kopf und verweist auf diese Liste. **Zusammenfuehren bleibt offen** — das ist eine Produktentscheidung, keine Aufraeumarbeit, und eine dritte Fassung waere die dritte Wahrheit | S | `ROADMAP.md` |
| L-31 | ~~`CHECKLIST.md` beschreibt einen laengst ueberholten Fruehstand als aktuell~~ — **gekennzeichnet 2026-08-19**: Sie hakte „7 Models" als vollstaendig ab, wo es rund fuenfzig sind. Traegt jetzt im Kopf, dass sie ein Stand vom Mai ist, und verweist auf die Lueckenliste. Sie wird **nicht** ersetzt: Ihre Aufgabe erfuellt diese Liste bereits | — | `CHECKLIST.md` |
| L-32 | ~~Online-Fertig-Editor definiert Markenfarben als lokale Konstanten~~ — **geschlossen 2026-08-19**, und der Befund war zu klein geschaetzt: Nicht 26 Stellen in 6 Dateien, sondern **39 Vorkommen in 21 Dateien**; **zehn** davon froren eine Farbe in einer Konstante ein — auch unter anderen Namen (`TEAL`, `DARK2`, `PRIMARY`), die eine Suche nach `KC_` uebersieht. **Es war keine Kosmetik:** `tokens.css` gibt zwei der drei im Dunkelmodus andere Werte (`--kc-dark` → `#003840`, `--kc-mid` → `#40c4df`). Die Komponenten waren auf den Hellwerten eingefroren, und `#008EAA` auf dunklem Grund ist genau das Kontrastproblem, fuer das der Dunkelmodus den Ton aufhellt — dieselbe Fehlerklasse wie die 140 Stellen weisser Schrift vom 18.08. Der Waechter prueft die **Konstante**, nicht jede Ziffer: `utils/tokenwerte.js` muss die Werte kennen, und `grapesjs/handwerk-blocks.js` erzeugt Kundenseiten, die unsere CSS-Variablen gar nicht haben | — | `utils/markenfarben.test.js` |
| L-33 | `CustomerDetail.js` als `.js` statt `.jsx`, 2.505 Zeilen | S | Dateiliste |

---

## 4. Seit Mai geschlossen

Zur Fairness gegenüber den beiden Mai-Audits — diese Befunde sind erledigt:

- **`sequence_runner.py` fehlte** → Datei existiert, im Scheduler als `email_sequence_runner`
  registriert. Die E-Mail-Sequenzen laufen.
- **Audit-Ergebnis-Mail wurde nicht versendet** → wird nach Audit-Abschluss versendet.
  Seit 2026-08-15 über `services/mail_vorlagen.py` im gemeinsamen Mailrahmen; sie
  bestand bis dahin aus vier Zeilen nacktem HTML und enthielt nie einen Link.
- **Audit startet nicht automatisch nach Lead-Anfrage** → Kette `leads/public` →
  `audit/start` ist verdrahtet (nur die CORS-Freigabe fehlt, siehe L-02).
- **Token-System uneinheitlich** → im Mai systematisch bereinigt, rund 280 Stellen migriert.
- **Invoice-PDF mit Platzhalter-Bankdaten** → behoben.

---

## 5. Empfohlene Reihenfolge

*Stand 2026-08-19. Die Reihenfolge vom 15.08. ist zur Hälfte abgearbeitet:
L-05 ist real durchgesetzt (fünf Rechte statt zwei), L-10 und L-11 sind
geschlossen, L-34 steht auf halbem Weg.*

1. **L-34 zu Ende bringen** — bleibt auf Platz eins, solange die Domain noch
   auf Oregon zeigt. Der Dienst in Frankfurt läuft und ist gemessen; was fehlt,
   ist das Umhängen. Zwingende Reihenfolge:
   **Branch prüfen → L-57 → Webhooks → Domain → `RENDER_SERVICE_BACKEND_PROD`
   → alten Dienst suspendieren.**
2. **L-57** — Oregons Build-Befehl reparieren. Steht hier so weit oben, weil er
   der **Rückweg** ist: Suspendieren und späteres Fortsetzen löst bei Render
   einen Deploy aus, und der würde heute scheitern.
3. **L-44** — Inbound-Regel der Produktiv-DB schließen. Erst nach L-34, dann
   aber zügig; es ist die letzte Stelle, an der Produktivdaten im offenen
   Internet stehen.
4. **L-12** — der zweite Teil der Rollenrechte. L-05 hat fünf Rechte
   durchgesetzt; die Matrix kennt mehr.
5. **L-29** — die Preiswidersprüche. Vier Stellen, bereits auseinandergelaufen
   (Premium 2.500 gegen 2.800, Kompagnon 2.000 gegen 3.500). **Welcher Preis
   gilt, ist eine Entscheidung von David** — bis dahin lässt sich nur die
   Behauptung aus dem Quelltext ziehen, nicht der Widerspruch auflösen.
6. **L-40** — Vorschau-Site einrichten, damit die Qualitätsschleife läuft.
7. **L-25, L-26** — Dateigrößen und Editor-Generationen. Die einzige Kennzahl,
   die sich verschlechtert.
8. Danach nach Geschäftswert: **L-14** (Assistent fachlich beurteilen lassen)
   oder **L-15/L-17** (Conversion und Barrierefreiheit — eine Klasse von zwanzig
   namenlosen Schaltflächen ist am 19.08. geschlossen worden, der Rest steht).

**L-08** (Dependabot) und **L-35** (Blueprints anwenden) hängen weiter am
Render-Zugang, der über den MCP `unauthorized` meldet — im Dashboard geht es.

**Tagesberichte:** `stand-2026-08-08.md` · `stand-2026-08-14.md` ·
`stand-2026-08-15.md` · `stand-2026-08-19.md`
