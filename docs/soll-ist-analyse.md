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
| A — Betrieb & Release | 🟢 | `main` über Rulesets geschützt, CI mit vier Pflichtjobs, dual-branch etabliert, wöchentlicher Release | 08-15 |
| B — Sicherheit & Compliance | 🟠 | Anmeldung hängt seit 08-14 am Router statt an jeder Route. Offen: Rate-Limiting, Rollenrechte ohne Wirkung, **DB-Zugangsdaten waren bis 08-15 über `/info` abrufbar** | 08-15 |
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

Weiterhin offen und unverändert: Rate-Limiting (L-04), Rollenrechte ohne
Wirkung (L-05), `require_auditor` an keiner Route (L-12) — alle drei am
15.08. nachgeprüft und bestätigt.

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
| L-04 | Kein Rate-Limiting; `POST /api/leads/public` unauthentifiziert mit anschließendem Audit-Lauf — **am 2026-08-15 nachgeprüft, unverändert**. Der Widget-Endpunkt hat seit dem 11.08. eigene Grenzen (`_enforce_limits`), dieser nicht | M | `leads.py:728`, keine Limiter-Abhängigkeit |
| L-39 | **Datenbank-Zugangsdaten waren über `/info` ohne Anmeldung abrufbar** (produktiv und Staging), behoben am 2026-08-15 in `2f687b2`. **Offen: Rotation in Render** — der Fix macht die Preisgabe nicht ungeschehen, und ob jemand hingesehen hat, lässt sich nicht feststellen | S | `stand-2026-08-15.md` § 1 |
| L-05 | `RolePermission` und Berechtigungs-UI ohne jede Wirkung — Rechte lassen sich scheinbar ändern. **Am 2026-08-15 nachgeprüft, unverändert**: gelesen nur in `database.py` und `admin_settings.py` | M | keine Lesestelle außerhalb `admin_settings.py` |

### P1 — Betrieb und Prozess

| ID | Lücke | Aufwand | Beleg |
|---|---|---|---|
| ~~L-06~~ | ~~Produktiv-Rückstand~~ — **erledigt 2026-08-07**: PR #34 gemergt (36 Commits), produktiv deployt und verifiziert | — | — |
| L-07 | ~~`main` ohne Branch-Protection~~ **korrigiert 2026-08-07:** `main` ist über Rulesets geschützt (`protect-main`), die die klassische Protection-API nicht meldet. Offen bleibt: die Regel „Restrict updates" blockiert jeden Merge, und die zwei neuen Prüfjobs sind nicht als Pflicht-Checks eingetragen | S | `gh api repos/…/rules/branches/main` |
| L-08 | Dependabot-Alerts deaktiviert; 2 kritische / 23 hohe npm-Befunde; 7 Update-PRs geschlossen | M | `npm audit`, PR-Historie |
| L-09 | Testabdeckung — **Stand 2026-08-15: 927 Backend- + 98 Frontend-Tests**, vier Pflichtjobs, dazu eine eingefrorene Referenz-Website für die Erhebung (`tests/referenzseite.py`). Weiterhin offen: Wireframe, Style-Guide-Freigabe, Design-View, Zahlungen | M | `backend/tests/`, `frontend/src/utils/*.test.js`, `e2e/` |
| L-10 | Kein Monitoring / Fehler-Tracking im Produktivbetrieb | M | kein Sentry in Requirements/Package |
| L-11 | Keine dokumentierte Backup- und Wiederherstellungsstrategie für die Produktiv-DB | S | `render.yaml` ohne Backup-Konfiguration |
| L-12 | `require_auditor` an keiner Route eingehängt — Auditor faktisch nicht abgegrenzt. **Am 2026-08-15 nachgeprüft: weiterhin null Treffer** | S | Suche nach `Depends(require_auditor)` ohne Treffer |
| L-13 | `.claude/settings.json` getrackt trotz `.gitignore`-Ausschluss — **Hook-Pfad korrigiert 2026-08-08** (zeigte auf `/home/user/Claude-Code`, jeder Auto-Push scheiterte still); offen bleibt die widersprüchliche Verfolgung der Datei | S | `git status`, Diff |
| L-40 | Qualitätsschleife nicht scharf geschaltet: `NETLIFY_VORSCHAU_SITE_ID` fehlt, deshalb ist der Durchstich Editor → Netlify → Audit → PDF nie am Stück gelaufen. Ohne die Variable antwortet der Endpunkt sauber mit 503 | S | `services/qualitaetsschleife.py` |
| L-34 | **Produktiv-Backend läuft in Oregon (US West)**, Datenbank in Frankfurt — jede Abfrage überquert den Atlantik; widerspricht der eigenen Vorgabe in `render.yaml` („Region: frankfurt — DSGVO-relevant") | L | Render-Dashboard, Service-Settings; Health-Check 2,4 s produktiv vs. 0,2 s Staging |
| L-35 | Blueprints beschreiben nicht die Realität: Produktiv-Frontend ist Static Site statt Web-Service, DB heißt `Kompangnon-dB` auf Postgres 18 statt `kompagnon-db` auf 16, Produktiv-Services sind nicht blueprint-verwaltet | S | Render-Dashboard vs. `render.yaml` |
| ~~L-36~~ | ~~Fehler werden im Frontend systematisch weggefangen~~ — **erledigt 2026-08-08**: 67 leere catch-Blöcke in 36 Dateien beseitigt, null verbleibend. Neuer Helfer `utils/apiRequest.js` (`loadJson`/`saveJson`/`apiRequest`) mit 15 jest-Tests, erstmals Frontend-Unit-Tests in der CI. Dabei gefunden: neun Speicher-Aktionen, die Erfolg meldeten, ohne den Status je zu prüfen — darunter Go-Live („Website ist live! 🎉" trotz gescheitertem PUT), Briefing-Autosave, QA-Checkliste und Bild-Uploads. Bewusst stille Stellen (Keepalive, Brotkrumen, Passwort-vergessen) tragen jetzt `quiet` mit Begründung | — | — |
| ~~L-37~~ | ~~Newsletter komplett tot: `import brevo_python` scheitert immer, weil `brevo-python` das Modul `brevo` liefert~~ — **erledigt 2026-08-08**: Anbindung auf die REST-API v3 über httpx umgestellt, SDK aus den Requirements entfernt, 15 Tests ergänzt. Gleich mitgefunden: Statistik las `open_rate`/`click_rate`, die es bei Brevo nicht gibt (heißt `opensRate`, Klickrate gar nicht) → Analytics zeigte immer leere Werte; Massenimport zählte abgelehnte Kontakte als importiert | — | — |
| L-38 | Der Mai-Audit führt „Brevo-Stats ✅" und „Brevo-Contact-Sync ✅" als geprüft — beides konnte nie funktioniert haben. Abhaken ohne Ausführung ist der gleiche blinde Fleck wie L-36, nur eine Ebene höher | S | `docs/audit-2026-05-04.md:148,165` |

### P2 — Produktentwicklung

| ID | Lücke | Aufwand | Beleg |
|---|---|---|---|
| L-14 | Projekt-Assistent — **Ausbau 1 gebaut** (`routers/assistant.py`). Offen: fachliche Beurteilung durch David oder einen Handwerksbetrieb, Ausgangswerte der Abschlussquote, Ausbau 2 (Projektbegleitung) | M | `docs/projekt-assistent-anforderungen.md` § 9.6 |
| L-15 | Hormozi-Offer-Stack fehlt im `content_writer` — seit Mai unverändert | M | kein Bezug im Agenten auffindbar |
| L-16 | Envato-Wireframe-Pipeline steckt in Phase 1 (2 von 8–15), wartet auf Pattern-Notes | L | Plan-Status im Memory |
| L-17 | Keine Barrierefreiheit im Tool (12 von 167 Dateien mit ARIA) — bei verkaufter BFSG-Konformität | L | Auszählung |
| L-18 | In-App-Benachrichtigungen fehlen (nur E-Mail-Schalter vorhanden) | M | kein Notification-Modell |
| L-19 | KAS-Verkaufsseiten ohne Custom-Domain-Endpunkt — hängen auf `*.netlify.app` | S | `netlify_service.py:90`, kein KAS-Domain-Router |
| L-20 | WebSprint-Landingpage außerhalb des Systems, ohne Quellversionierung (53 KB lokal vs. 914 KB live) | M | Größenvergleich |
| L-21 | Google Ads / Meta Ads: null Code — Stage 3 der Vision blockiert | XL | keine SDK-Referenz |
| L-22 | Analytics/Umami: Plan vorhanden, null Code — ohne Tracking keine Funnel-Optimierung | L | keine Umami-Referenz |
| L-23 | Component-Manager Phase 2 (React-Eingabe) zurückgestellt | M | Plan im Memory |
| L-24 | ROADMAP-P1-Restpunkte: LeadProfile-Tabs, weitere Kundenportal-Wünsche | M | `ROADMAP.md` |

### P3 — Schulden und Konsistenz

| ID | Lücke | Aufwand | Beleg |
|---|---|---|---|
| L-25 | **Elf** Backend-Dateien über der 800-Zeilen-Grenze (`projects.py` 4.673, `leads.py` 2.196, `component_library.py` 2.100, `main.py` 2.050 …), dazu sechs im Frontend (`templates_zusatz.js` 3.121, `LeadProfile.jsx` 2.673). Am 2026-08-15 gezählt — **die einzige Kennzahl, die sich verschlechtert hat** | L | `wc -l` |
| L-26 | Drei Editor-Generationen parallel (`ProzessFlow`, `V3`, `OnlineFertigEditor`) | M | 3.723 Zeilen zusammen |
| L-27 | Zwei Briefing-Strukturen und zwei Briefing-Router parallel | M | `briefing.py` / `briefings.py` |
| L-28 | Zwei Template-Router (`templates.py`, `website_templates.py`) | S | Router-Inventar |
| L-29 | Preise an drei Stellen gepflegt statt zentral | S | `payments.py`, `products`, GEO-Helper |
| L-30 | `ROADMAP.md` enthält zwei widersprüchliche Roadmaps, Stand April | S | Datei |
| L-31 | `CHECKLIST.md` beschreibt einen längst überholten Frühstand als aktuell | S | Datei |
| L-32 | Online-Fertig-Editor definiert Markenfarben als lokale Konstanten (26 Stellen in 6 Dateien) statt über Tokens — durch die dokumentierte Ausnahme gedeckt, aber außerhalb des Token-Systems | S | `KASSidebar.jsx:35-38` u. a. |
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

*Stand 2026-08-15. Die Reihenfolge vom 07.08. ist abgearbeitet — L-01 bis L-03,
L-06, L-07 und L-36 sind erledigt, L-09 hat ein tragendes Fundament.*

1. **L-39** — Datenbank-Zugangsdaten rotieren. Das ist das Einzige, was nicht
   warten kann, und es hängt nicht am Code.
2. **L-04** — Rate-Limiting auf `POST /api/leads/public`. Der Endpunkt ist
   unauthentifiziert und stößt einen Audit-Lauf an, der Geld kostet. Das Widget
   hat seit dem 11.08. eigene Grenzen; dieser Weg nicht.
3. **L-05, L-12** — Rollenrechte entweder real durchsetzen oder das
   irreführende UI entfernen. Ein Berechtigungs-Dialog ohne Wirkung ist
   schlimmer als keiner.
4. **L-10, L-11** — Monitoring und Backup-Dokumentation. Die beiden letzten
   echten Betriebslücken.
5. **L-40** — Vorschau-Site einrichten, damit die Qualitätsschleife läuft.
6. **L-25, L-26** — Dateigrößen und Editor-Generationen. Die einzige Kennzahl,
   die sich verschlechtert, und die Ursache der meisten Reibung beim Arbeiten.
7. Danach nach Geschäftswert: **L-14** (Assistent fachlich beurteilen lassen,
   dann Ausbau 2) oder **L-15/L-17** (Conversion und Barrierefreiheit).

**L-08** (Dependabot) und **L-34/L-35** (Render-Region und Blueprints) hängen
am Render-Zugang, der weiterhin `unauthorized` meldet.
