# KOMPAGNON — Soll-Ist-Analyse der Gesamtplattform

> Stand: 2026-08-07
> Methodik: Code-Analyse (Backend 24.367 Zeilen Router + Services, Frontend 167 Dateien),
> GitHub-API (PRs, CI, Protection, Secret-Scanning), Live-Prüfung der produktiven Endpunkte,
> Abgleich mit `ROADMAP.md`, `CHECKLIST.md`, `docs/audit-2026-05-04.md`,
> `docs/customer-journey-audit-2026-05-04.md`, `docs/kas-pipeline-architecture.md`, `CLAUDE.md`
> und den globalen Entwicklungsregeln.
>
> Enthält die bekannten offenen Punkte aus der Analyse vom 2026-08-07 sowie die noch
> offenen Befunde der beiden Mai-Audits — mit aktualisiertem Status.

---

## 1. Gesamtbild

| Bereich | Soll-Erfüllung | Einschätzung |
|---|---|---|
| A — Betrieb & Release | 🟠 | Produktiv hängt 3 Monate zurück, kein Schutz auf `main` |
| B — Sicherheit & Compliance | 🔴 | Secrets ungeschützt, kein Rate-Limiting, Rollenrechte wirkungslos |
| C — Vertrieb & Lead-Gewinnung | 🟠 | Landingpage live, aber Website-Check produktiv defekt |
| D — Verkauf & Zahlung | 🟡 | Stripe funktioniert, Preise an mehreren Stellen |
| E — Projektabwicklung | 🟢 | 7 Phasen, Checkliste, Marge, Automationen laufen |
| F — KAS-Pipeline (Site-Bau) | 🟡 | 4-View-Editor steht, Doppelstrukturen ungeräumt |
| G — Kundenportal | 🟢 | Phasen, Freigaben, Nachrichten, Dokumente vorhanden |
| H — Projekt-Assistent | ⬜ | Fachlich geklärt, nicht begonnen |
| I — Academy | 🟢 | Kurse, Module, Quiz, Zertifikate, Admin |
| J — Eigene Web-Präsenz | 🟠 | KAS-Seiten ohne Domain, WebSprint außerhalb des Systems |
| K — Qualitätssicherung | 🔴 | Praktisch keine Tests, kein Monitoring, keine Backup-Doku |
| L — Code-Struktur | 🟠 | Große Dateien, drei Editor-Generationen, veraltete Doku |

**Kurzfassung:** Die Fachlichkeit ist weit — was Kunden sehen und was intern automatisiert
läuft, trägt. Die Lücken liegen fast durchweg in Betrieb, Absicherung und Qualitätssicherung,
also dort, wo Fehler teuer und schlecht sichtbar sind.

---

## 2. Soll-Ist je Bereich

### A — Betrieb & Release

**Soll** (`CLAUDE.md`): Arbeit auf `staging`, freitags Sammel-PR nach `main`, Branch-Protection
verhindert direkten Push, CI grün vor Merge.

**Ist:** Der Workflow wird eingehalten, aber der letzte Merge nach `main` war am 2026-05-08.
Seitdem liegen **22 Commits mit 141 geänderten Dateien** (+3.627/−861) ausschließlich auf
`staging`. `main` ist laut GitHub-API **nicht geschützt** — keine Required Checks, kein
Review-Gate. Die CI läuft auf Push und PR mit vier Jobs, zuletzt grün.

**Lücke:** Der komplette Token-Cleanup, der Backend-Logger-Refactor, der Invoice-PDF-Fix und
der Library-Zuwachs sind produktiv nicht angekommen. Die in `CLAUDE.md` behauptete
Branch-Protection existiert nicht.

### B — Sicherheit & Compliance

**Soll** (globale Sicherheitsregeln): keine Secrets im Repo, Eingabevalidierung an allen
Grenzen, Rate-Limiting auf allen Endpunkten, verifizierte Autorisierung, DSGVO- und
BFSG-Konformität.

**Ist:**
- `kompagnon/backend/.env.save` enthält `ANTHROPIC_API_KEY`, `DATABASE_URL`, `SECRET_KEY` und
  wird von **keiner** `.gitignore` erfasst. Gitleaks läuft nur bei PRs nach `main`.
- **Kein Rate-Limiting** im gesamten Backend (kein `slowapi` o. ä. in `requirements.txt`).
  `POST /api/leads/public` ist unauthentifiziert, validiert die E-Mail nicht und triggert
  direkt danach den kostenpflichtigen Audit-Lauf.
- Die Rollentabelle `RolePermission` und das zugehörige Admin-UI werden **nirgends gelesen** —
  echte Grenzen stehen hartcodiert in den `require_*`-Dependencies. `require_auditor` ist
  definiert, aber an keiner Route eingehängt.
- Von 167 Frontend-Dateien nutzen **12** ARIA-Attribute (46 Vorkommen). Der zentrale
  `BriefingWizard` und das `KundenPortal` haben **null**.
- Kein Cookie-Consent im Tool. Dependabot-Alerts sind repo-weit deaktiviert; `npm audit`
  meldet **2 kritische und 23 hohe** Befunde, die sieben Dependabot-PRs von Mai wurden
  geschlossen statt gemerged.

**Lücke:** Das ist der schwächste Bereich. Besonders unangenehm: ihr verkauft auf der
WebSprint-Seite ausdrücklich "DSGVO- & BFSG-konform" — das eigene Werkzeug erfüllt den
Barrierefreiheitsteil nicht.

### C — Vertrieb & Lead-Gewinnung

**Soll:** Kaltakquise über Audit-PDF, Landingpage mit Website-Check als Lead-Magnet,
automatische E-Mail-Sequenz, Performance-Marketing als Abo (Stage 3 der Vision).

**Ist:** Audit-Tool, Scraper, Lead-Enrichment, Northdata, PageSpeed und der Crawler laufen.
Der `sequence_runner` ist inzwischen vorhanden und im Scheduler registriert — der Mai-Befund
"E-Mail-Sequenz läuft nicht" ist **erledigt**. Ebenso wird die Audit-Ergebnis-Mail versendet
(`send_audit_done_email`). Die WebSprint-Landingpage ist live.

**Lücke:** Der Website-Check auf `websprint.kompagnon.eu` ist produktiv **defekt** — der
CORS-Preflight gegen das Produktiv-Backend liefert 400 ohne `allow-origin`; der Fix liegt
uncommitted. Das Embed-Widget ist nie deployt worden (404). Google Ads und Meta Ads sind
weiterhin bei **null Zeilen Code**, ebenso Umami/Analytics — beides seit Mai unverändert.

### D — Verkauf & Zahlung

**Soll:** Alle Produkte über Stripe kaufbar, Preise zentral gepflegt.

**Ist:** Stripe-Checkout, Webhooks, Rechnungs-PDF und das GEO-Abo funktionieren. Es gibt eine
`products`-Verwaltung mit Stripe-Anbindung pro Produkt.

**Lücke:** Preise liegen weiterhin an mehreren Stellen (hartcodierte `PACKAGE_NAMES` in
`payments.py`, `products`-Tabelle, GEO-Helper). Für Stage 3/4 existiert kein Produkt.

### E — Projektabwicklung

**Soll:** 7 Phasen, 54 Checklistenpunkte, Margenverfolgung, Automatisierung.

**Ist:** Vollständig. `Project.status` von `phase_1` bis `phase_7`, Checkliste, Zeiterfassung,
Margenberechnung mit Ampel, 18 Scheduler-Jobs inklusive Post-Go-Live-Sequenz (Tag 5/14/21/30),
Phasenwechsel-Mails, Material-Erinnerungen, Briefing-Reminder.

**Lücke:** Keine funktionale. Offen bleiben nur die ROADMAP-Punkte In-App-Notifications
(existiert nicht — nur E-Mail-Schalter) und die Vereinheitlichung der `LeadProfile.jsx`-Tabs.

### F — KAS-Pipeline (Site-Bau)

**Soll** (`kas-pipeline-architecture.md`): Analyse → Sitemap → Wireframes → Styleguide →
Final Design → Deploy, 17 Schritte in 6 Phasen.

**Ist:** Der neue `OnlineFertigEditor` mit vier Views (Sitemap, Wireframe, StyleGuide, Design)
und der `KASSidebar` als Schritt-Navigation ist gebaut und unter `/app/projects/:id` aktiv.
Netlify-Deploy, Brand-Design, Component-Library mit 45 Wireframes, GrapesJS-Editor stehen.

**Lücke:** Drei Editor-Generationen koexistieren — `ProzessFlow.jsx` (2.261 Zeilen, liefert
noch `SchrittInhalt` an den neuen Editor), `ProzessFlowV3.jsx` (660, als Legacy-Route aktiv)
und `OnlineFertigEditor.jsx` (802). Der Hormozi-Offer-Stack aus der Conversion-Spec ist im
`content_writer` weiterhin nicht umgesetzt — im Agenten findet sich kein Bezug darauf. Die
Envato-Wireframe-Pipeline steckt seit Mai in Phase 1 (2 von 8–15 Wireframes).

### G — Kundenportal

**Soll:** Kunde sieht Projektstand, füllt Briefing, lädt Dateien hoch, gibt frei,
kommuniziert.

**Ist:** Alles vorhanden — Phasenanzeige mit Fortschritt je Phase, Briefing-Wizard,
Dokumenten-Upload, Versionsauswahl, Freigaben, Nachrichten, Support-Tickets, Rechnungen,
Academy-Bereich, Zugangsdaten-Safe, Onboarding-Wizard.

**Lücke:** Zwei parallele Briefing-Strukturen (flacher `BriefingWizard` + 12-Sektionen-JSON,
dazu zwei Router `briefing.py` und `briefings.py`). Keine ARIA-Auszeichnung. Kein
In-App-Benachrichtigungsfeed.

### H — Projekt-Assistent

**Soll** (`docs/projekt-assistent-anforderungen.md`, heute geklärt): Hybrid aus geführtem
Fragebogen und KI-Chat, zwei Modi, Vorschläge mit Bestätigung, Phasenreife-Bewertung.

**Ist:** Nicht begonnen. Vorarbeiten vorhanden: `suggest-field`, die `ki-prefill-*`-Endpunkte
und fünf KI-Agenten als Muster.

**Lücke:** Vollständig offen. Voraussetzung ist das Regelwerk aus der Conversion-Spec und
eine Verbrauchsmessung, die es heute nicht gibt.

### I — Academy

**Soll:** Kurse für Kunden und Mitarbeiter, Module, Lektionen, Quiz, Zertifikate, Verwaltung.

**Ist:** Vollständig implementiert, inklusive Zielgruppentrennung und Admin-Oberfläche.

**Lücke:** Keine strukturelle.

### J — Eigene Web-Präsenz

**Soll:** KOMPAGNON-eigene Verkaufsseiten im GrapesJS-Editor pflegen und auf eine
Netlify-Site deployen (`kompagnon-kas-website`), Deploy nur durch Superadmin.

**Ist:** Der Mechanismus steht und ist die einzige Stelle im System mit
`require_superadmin`.

**Lücke:** `create_site` setzt `custom_domain: None`, und der KAS-Router hat keinen
Domain-Endpunkt — die Seiten hängen auf einer `*.netlify.app`-Adresse.
`set_custom_domain()` existiert, wird aber nur für Kundenprojekte genutzt. Parallel dazu
läuft die WebSprint-Landingpage als handgepflegte 914-KB-Datei komplett außerhalb des
Systems, obwohl sie funktional genau das ist, was KAS produzieren soll.

### K — Qualitätssicherung

**Soll** (globale Regeln): 80 % Testabdeckung, Unit- + Integrations- + E2E-Tests, TDD,
Monitoring, Backups.

**Ist:** Ein einziges Integrationsskript (`backend/tests/integration_test.py`), **null**
Frontend-Tests, **kein** Test-Job in der CI (nur Lint, Smoke-Import, Build, Gitleaks).
Kein Sentry oder vergleichbares Monitoring. Keine dokumentierte Backup-Strategie für die
Produktivdatenbank.

**Lücke:** Die größte Abweichung zwischen Anspruch und Realität im ganzen Projekt.

### L — Code-Struktur & Dokumentation

**Soll:** Dateien unter 800 Zeilen, Funktionen unter 50, keine Doppelstrukturen, aktuelle Doku.

**Ist:** `routers/projects.py` 4.673 Zeilen, `LeadProfile.jsx` 2.623, `CustomerDetail.js`
2.505, `ProzessFlow.jsx` 2.261, `routers/leads.py` 2.177, `main.py` 1.950 — sechs Dateien
über dem Doppelten des Limits. Zwei Template-Router (`templates.py`, `website_templates.py`),
zwei Briefing-Router, drei Editor-Generationen. `ROADMAP.md` enthält zwei
aneinandergehängte, sich widersprechende Roadmaps mit Stand April.

---

## 3. Konsolidierte Lückenliste

Priorität: **P0** = produktiv defekt oder Sicherheitsrisiko · **P1** = Betrieb/Prozess ·
**P2** = Produktentwicklung · **P3** = Schulden und Konsistenz.
Aufwand: S ≤ 1 Tag · M ≤ 1 Woche · L ≤ 4 Wochen · XL darüber.

### P0 — Sofort

| ID | Lücke | Aufwand | Beleg |
|---|---|---|---|
| L-01 | `.env.save` mit Produktiv-Secrets liegt unignoriert im Repo; Gitleaks greift nur bei PRs nach `main` | S | `kompagnon/backend/.env.save`, `git check-ignore` ohne Treffer |
| L-02 | Website-Check der WebSprint-Landingpage produktiv defekt (CORS-Preflight 400), Fix uncommitted | S | Preflight-Test, `main.py:1654` |
| L-03 | Embed-Widget nie deployt — dokumentierte Live-URL liefert 404 | S | `frontend/public/embed/` untracked |
| L-04 | Kein Rate-Limiting; `POST /api/leads/public` unauthentifiziert mit anschließendem Audit-Lauf | M | `leads.py:711`, keine Limiter-Abhängigkeit |
| L-05 | `RolePermission` und Berechtigungs-UI ohne jede Wirkung — Rechte lassen sich scheinbar ändern | M | keine Lesestelle außerhalb `admin_settings.py` |

### P1 — Betrieb und Prozess

| ID | Lücke | Aufwand | Beleg |
|---|---|---|---|
| L-06 | 22 Commits / 141 Dateien seit 09.05. nicht in `main` — Produktiv auf altem Stand | S | `git rev-list origin/main...origin/staging` |
| L-07 | `main` ohne Branch-Protection, entgegen `CLAUDE.md` | S | GitHub-API: "Branch not protected" |
| L-08 | Dependabot-Alerts deaktiviert; 2 kritische / 23 hohe npm-Befunde; 7 Update-PRs geschlossen | M | `npm audit`, PR-Historie |
| L-09 | Keine Testabdeckung (1 Skript, 0 Frontend-Tests, kein CI-Test-Job) gegen 80-%-Vorgabe | L | `.github/workflows/ci.yml` |
| L-10 | Kein Monitoring / Fehler-Tracking im Produktivbetrieb | M | kein Sentry in Requirements/Package |
| L-11 | Keine dokumentierte Backup- und Wiederherstellungsstrategie für die Produktiv-DB | S | `render.yaml` ohne Backup-Konfiguration |
| L-12 | `require_auditor` an keiner Route eingehängt — Auditor faktisch nicht abgegrenzt | S | Suche nach `Depends(require_auditor)` ohne Treffer |
| L-13 | `.claude/settings.json` getrackt trotz `.gitignore`-Ausschluss, mit fremdem Pfad im Hook | S | `git status`, Diff |
| L-34 | **Produktiv-Backend läuft in Oregon (US West)**, Datenbank in Frankfurt — jede Abfrage überquert den Atlantik; widerspricht der eigenen Vorgabe in `render.yaml` („Region: frankfurt — DSGVO-relevant") | L | Render-Dashboard, Service-Settings; Health-Check 2,4 s produktiv vs. 0,2 s Staging |
| L-35 | Blueprints beschreiben nicht die Realität: Produktiv-Frontend ist Static Site statt Web-Service, DB heißt `Kompangnon-dB` auf Postgres 18 statt `kompagnon-db` auf 16, Produktiv-Services sind nicht blueprint-verwaltet | S | Render-Dashboard vs. `render.yaml` |

### P2 — Produktentwicklung

| ID | Lücke | Aufwand | Beleg |
|---|---|---|---|
| L-14 | Projekt-Assistent (Fragebogen + Projektbegleitung) — geklärt, nicht begonnen | L | `docs/projekt-assistent-anforderungen.md` |
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
| L-25 | Sechs Dateien weit über der 800-Zeilen-Grenze (bis 4.673) | L | `wc -l` |
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
- **Audit-Ergebnis-Mail wurde nicht versendet** → `send_audit_done_email` wird nach
  Audit-Abschluss aufgerufen.
- **Audit startet nicht automatisch nach Lead-Anfrage** → Kette `leads/public` →
  `audit/start` ist verdrahtet (nur die CORS-Freigabe fehlt, siehe L-02).
- **Token-System uneinheitlich** → im Mai systematisch bereinigt, rund 280 Stellen migriert.
- **Invoice-PDF mit Platzhalter-Bankdaten** → behoben.

---

## 5. Empfohlene Reihenfolge

1. **L-01** — Secrets absichern, bevor irgendetwas committet wird.
2. **L-02, L-03** — Landingpage und Widget funktionsfähig machen; das ist verlorener Umsatz pro Tag.
3. **L-06** — Freitags-PR nach `main`, damit die Fixes und drei Monate Arbeit produktiv ankommen.
4. **L-07, L-13** — Schutz auf `main` einschalten, `CLAUDE.md` an die Realität angleichen.
5. **L-04** — Rate-Limiting, bevor die Landingpage stärker beworben wird.
6. **L-05, L-12** — Rollenrechte entweder real durchsetzen oder das irreführende UI entfernen.
7. **L-08, L-10, L-11** — Abhängigkeiten, Monitoring, Backups: die Grundlagen des Betriebs.
8. Danach nach Geschäftswert: **L-14** (Assistent) oder **L-15/L-17** (Conversion und Barrierefreiheit).

**L-09** (Tests) lässt sich nicht nachholen, sondern nur ab jetzt aufbauen — sinnvollerweise
beginnend mit den Endpunkten, die Geld bewegen: Payments, Leads, Audit.
