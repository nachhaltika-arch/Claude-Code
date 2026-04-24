# KOMPAGNON Automation System (KAS)

Interne Betriebsplattform der **KOMPAGNON Communications BP GmbH**. KAS verbindet Lead-Akquise, Website-Produktion, Auditing, KI-gestützte Content-Erstellung, Hosting, Rechnungsstellung, Kundenportal und Academy in einem System. Jede Phase eines Kundenauftrags — von der ersten Kontaktaufnahme bis zum laufenden Betrieb nach dem Go-Live — wird hier abgebildet, automatisiert und auswertbar gemacht.

---

## Für wen

KAS ist die Plattform für den operativen Betrieb von KOMPAGNON und bedient das Endkundengeschäft mit **Handwerksbetrieben in Deutschland**. Das System ist auf die Anforderungen kleiner und mittlerer Handwerksunternehmen zugeschnitten: klare Pakete, feste Preise, deutsche Inhalte, rechtliche Compliance (Impressum, Datenschutz, BFSG) und lokale Sichtbarkeit.

---

## Produktlinien

### ONLINE FERTIG. von KOMPAGNON
Schlüsselfertige Website-Pakete (Starter, KOMPAGNON, Premium). Vom automatisierten Audit-Report der Bestands-Website über Briefing, KI-Content und Design bis zur produktiven Website auf Netlify — inklusive Post-Launch-Betreuung, Bewertungsmanagement und Local-SEO-Optimierung.

### IMPULS Beratung ISB-158
Strategische Unternehmensberatung für Handwerksbetriebe nach dem Standard ISB-158. Eigener Leistungsumfang mit separater Abwicklung im selben System.

---

## Feature-Überblick

### Dashboard
- Echtzeit-KPIs: aktive Projekte, Marge, gewonnene Leads, Audits des Tages
- Deal-Metriken (heute gewonnen, Monatsumsatz, offene Pipeline)
- Leads nach Herkunft (Kampagnen-Tracking)
- Alerts bei überfälligen Phasen, Margen-Risiko, fehlenden Materialien
- Staggered Loading: KPIs, Leads und Sekundärdaten laden unabhängig voneinander

### CRM und Vertrieb
- **Leads-Pipeline** mit Statusverfolgung, Akquise-Quelle, KI-Bewertung (0–100), Geo-Score, automatischer Anreicherung
- **Unternehmen** (Companies)
- **Deals** — vollständige Vertriebs-Pipeline mit Wert- und Wahrscheinlichkeits-Tracking
- **Customers** — Bestandskunden mit Touchpoint-Planung, Upsell-Status, Recurring Revenue
- **Kampagnen-Tracking** nach Quelle (Facebook, LinkedIn, Google Ads, Briefkarte, E-Mail, Instagram, Postkarte, Direkt)
- **Stripe Checkout** für Website-Einmalzahlungen (3 Pakete)

### Website-Audit
- Granulare Scores in sieben Kategorien: Rechtliche Compliance, Technische Performance, Hosting, Barrierefreiheit (BFSG), Sicherheit, SEO, UX
- Integration mit **Google PageSpeed Insights** (mobile + desktop, LCP / CLS / INP / FCP)
- KI-Analyse und Zusammenfassung über Anthropic Claude
- PDF-Report und automatische Angebots-Generierung

### Projekt-Workflow (7 Phasen)
1. Onboarding
2. Briefing
3. Texte und Schema
4. Technik und Sicherheit
5. QA und Kundenpräsentation
6. Go-Live
7. Post-Launch

Jede Phase hat Checklisten, Zeitbuchung, Echtzeit-Margen-Berechnung (Ziel 78 %) und automatische Phasen-Wechsel-Benachrichtigungen.

### Briefing- und Content-Werkstatt
- **Briefing-Wizard** — mehrstufiges Formular mit KI-Prefill für Ziele, Zielgruppe, SEO, Funktionen, Wettbewerb
- **Brand-Design-Editor** — Farben, Typographie und Logo aus der Bestands-Website scrapen und als Guideline exportieren
- **Moodboard-Editor**
- **Content-Manager** — Sektionen und Medien pro Seite, mit KI-gestützter Text-Generierung
- **Sitemap-Planer** mit Struktur-Vorschlägen

### Website-Editor und Hosting
- **GrapesJS Studio Editor** mit 12 Plugins (Newsletter-Preset, Formulare, Flexbox, Export)
- **Template-Library** mit Template-Editor und Gallery
- **Netlify-Integration** — automatische Site-Erstellung, Deploy, Domain-Management, SSL-Check
- **Before/After-Screenshots** automatisiert erfasst
- **Public-Pages**-System für Landingpages und Kampagnen

### GEO Add-on (Local-SEO-Abo)
- Stripe-Subscription-basiertes Monats-Abo als Post-Launch-Upsell
- Granulare Scores: `llms.txt`, KI-freundliches `robots.txt`, strukturierte Daten, Content-Tiefe, lokale Signale
- Automatische Geo-Seiten-Generierung und laufendes Monitoring
- Upsell-Automatik 30 Tage nach Go-Live

### Kundenportal
- Token-basierter Zugang (ohne Passwort-Login)
- Briefings, Freigaben, Rechnungen, Support-Tickets, Nachrichten
- Zugriff auf zugewiesene Academy-Kurse

### KOMPAGNON Academy
- E-Learning-Plattform für Mitarbeiter und Kunden
- Kurse → Module → Lektionen (Video / Text / Quiz)
- Fortschrittsverfolgung, QR-basierte Zertifikate mit öffentlicher Verifizierung
- Feingranulare Freigabe pro Kunde

### Support und Ticketing
- Interne Tickets (Priorität, Status, Screenshots)
- Portal-Nachrichten Kunde ↔ Team
- Vollständige E-Mail-Logs

### Newsletter und Marketing
- **Newsletter-Designer** auf GrapesJS-Basis mit Listen-Management, Kampagnen und Analytics
- Drip-Sequenzen abhängig von Lead-Quelle (Stripe-Checkout, Landing-Audit, Webhook-Leads)
- HTML-Rendering mit Unicode-korrekten Transaktional-E-Mails

### Admin- und Betriebstools
- Domain-Import, Massen-Export, Scraper-Control
- Webhook-Dashboard (Netlify, Stripe, Trackdesk-Affiliate)
- Rollenverwaltung: `admin`, `auditor`, `nutzer`, `kunde`, `superadmin`
- 2FA-Setup, System-Einstellungen, KAS-Website-CMS

---

## KI-Agenten

Alle Agenten nutzen **Anthropic Claude** (`claude-sonnet-4-6`).

| Agent | Aufgabe |
|---|---|
| **LeadAnalystAgent** | Website-Scoring, Potenzial-Analyse, Verkaufs-Pitch-Vorlage |
| **ContentWriterAgent** | Deutsche Website-Texte (Hero, About, Leistungen, FAQ, Meta-Tags, lokale CTA) |
| **SeoGeoAgent** | JSON-LD (LocalBusiness / FAQ / Service / Breadcrumb), `robots.txt`, Sitemap, lokale SEO-Empfehlungen |
| **QaAgent** | Automatisierte QA-Kontrolle (PageSpeed, Links, SSL, Mobile, rechtliche Compliance) mit Go-Live-Empfehlung |
| **ReviewAgent** | Personalisierte Bewertungsanfragen (E-Mail + Telefonskript, Google und ProvenExpert) |

---

## Automatisierungs-Scheduler

14 Hintergrund-Jobs via **APScheduler** — Auswahl:

- **Lead-Enrichment** — alle 2 Stunden (Website-Scan, Geschäftsführer-Lookup über Northdata)
- **Netlify-DNS-Check** — alle 6 Stunden
- **Netlify-SSL-Check** — alle 6 Stunden
- **Phasen-Überfälligkeit** — täglich
- **Fehlende Materialien** — täglich (Reminder an Kunden)
- **Margen-Neuberechnung** — täglich für alle Projekte
- **Monatlicher Performance-Report** — PageSpeed-Trend-Alerts an Admins
- **Post-Go-Live-Sequenz** — dynamisch:
  - Tag 5 — Follow-up
  - Tag 14 — Funktionscheck
  - Tag 21 — Bewertungsanfrage
  - Tag 30 — GEO-Check + Upsell-Angebot
- **HWK-Scrape** — wöchentlich
- **Domain-Gesamt-Check** — täglich

---

## Systemgröße

| Bereich | Umfang |
|---|---|
| Frontend-Routen | ~73 |
| Backend-API-Endpoints | 300+ |
| Datenbank-Modelle (SQLAlchemy) | 33 |
| Pydantic-Schemas | 50+ |
| Service-Module | 33 |
| KI-Agenten | 5 |
| Scheduler-Jobs | 14 |
| Router-Dateien | 43 |

---

## Technologie-Stack

### Backend
- **Python 3.11** / **FastAPI**
- **PostgreSQL** in Produktion, SQLite als lokaler Fallback
- **SQLAlchemy** ORM mit Connection-Pooling
- **APScheduler** für Hintergrund-Jobs
- **Anthropic SDK** — Claude Sonnet 4.6
- **Stripe SDK** — Einmalzahlungen und Subscriptions
- **Brevo (Sendinblue)** — Transaktional-E-Mail, SMTP-Fallback
- **ReportLab** — PDF-Generierung (Angebote, Rechnungen, Auftragsbestätigungen, Briefings)
- **BeautifulSoup / httpx** — Web-Scraping, Hosting-Detection, Impressum-Parser
- **pyotp / qrcode** — 2FA (TOTP) mit Backup-Codes
- **python-jose / passlib[bcrypt]** — JWT und Passwort-Hashing

### Frontend
- **React 18** / **React Router 6**
- **Tailwind CSS 3**
- **GrapesJS Studio SDK** für Page- und Newsletter-Editor
- **ECharts / Recharts** für Dashboard-Visualisierung
- **date-fns**, **react-hot-toast**, **Heroicons / Lucide**, **qrcode.react**

### Infrastruktur
- **Render.com** — Backend- und Frontend-Hosting mit Auto-Deploy
- **Netlify** — Hosting der generierten Kunden-Websites (über API angesteuert)
- **GitHub** — Single Source of Truth, Deploy-Trigger

---

## Repository- und Deployment-Struktur

Das Repository hat zwei langlebige Branches:

| Branch | Zweck | Auto-Deploy-Ziel |
|---|---|---|
| `main` | Produktion (live) | Produktiv-Server auf Render |
| `staging` | Entwicklung / Test | Stage-Server auf Render |

**Entwicklungs-Workflow:**
1. Entwicklung findet ausschließlich auf `staging` statt. Auf `main` wird **niemals** direkt gepusht.
2. Jeder Push auf `staging` löst automatisch ein Deployment auf die Stage-Server aus:
   - Frontend Stage: `https://kompagnon-frontend.onrender.com`
   - Backend Stage: `https://claude-code-znq2.onrender.com`
3. Produktions-Release erfolgt ausschließlich über einen Pull Request `staging → main` mit manuellem Merge. Render zieht den Produktiv-Server nach dem Merge automatisch nach.

---

## Lokale Entwicklung

Voraussetzungen: Python 3.11, Node.js 18, PostgreSQL (oder SQLite für Quickstart).

```bash
git clone https://github.com/nachhaltika-arch/Claude-Code.git
cd Claude-Code
git checkout staging
```

### Backend

```bash
cd kompagnon/backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env
# .env füllen: DATABASE_URL, SECRET_KEY, ANTHROPIC_API_KEY,
#              STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
#              SMTP_HOST/USER/PASSWORD, GOOGLE_PAGESPEED_API_KEY ...
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API-Docs (Swagger): `http://localhost:8000/docs`

### Frontend

```bash
cd kompagnon/frontend
npm install
npm run dev
```

Frontend: `http://localhost:3000`

---

## Sicherheit

- **JWT (HS256)** mit 8 Stunden Gültigkeit. `SECRET_KEY` ist in Produktion Pflicht — die Anwendung startet nicht, wenn die Env-Var leer ist.
- **2FA via TOTP** mit 8 Backup-Codes, QR-Setup im Profil.
- **Rollen-System** mit feingranularen Berechtigungen pro Endpoint.
- **Stripe-Webhooks** validieren die Signatur (`STRIPE_WEBHOOK_SECRET`, `STRIPE_WEBHOOK_SECRET_GEO`). Ohne gesetztes Secret antwortet die Route mit HTTP 503, sodass Stripe retriet und das Konfig-Problem sichtbar wird, statt stillschweigend zu scheitern.
- **CMS-Zugangsdaten** werden verschlüsselt in der Datenbank abgelegt.
- **CORS** ist auf bekannte Frontend-Domains beschränkt.
- **Idempotenz-Guards** bei Stripe-Webhooks (Session-ID im Lead-Notes) verhindern Doppel-Anlagen bei Stripe-Retries.

---

## Lizenz und Kontakt

Proprietär — KOMPAGNON Communications BP GmbH.

Kontakt: `info@kompagnon.eu`
