# Umami Analytics — Implementierungsplan

**Status:** Entwurf v1
**Erstellt:** 2026-04-30
**Branch:** staging
**Eigentümer:** Kompagnon

## 1. Ziele

Umami als zwei parallele Use Cases einführen:

1. **Internes Akquise-Tracking** — Kompagnon nutzt Umami für eigene Landing Pages, Funnel- und Demo-Site-Tracking. Liefert UTM-Lead-Quellen, Demo-Engagement-Signale und Pre-Sales-Daten in den bestehenden Lead-/Briefing-Flow.
2. **Customer Add-On „Analytics & Ad-Performance"** — kostenpflichtiges Self-Service-Produkt im Kundenportal, gegated über Stripe-Subscription. White-Label im Kompagnon-Branding.

Gemeinsame Infrastruktur (eine Umami-Instanz, eine DB), aber zwei UI-Sichten und zwei Berechtigungs-Pfade.

## 2. Tech-Stack & Hosting

- **Umami:** Node.js + Next.js, MIT-Lizenz, offizielles Docker-Image
- **Render Web Service** (eigenständig neben Backend/Frontend), Region **Frankfurt** (DSGVO)
- **Eigene Postgres-Instanz** (NICHT Schema-Mix mit KAS-DB — Umami verwaltet eigene Migrations, Updates wären sonst zu fragil)
- **Subdomain:** `analytics.kompagnon.eu` (Tracker + Admin) ODER getrennt:
  - `track.kompagnon.eu` (öffentliches Tracking-Skript)
  - `analytics.kompagnon.eu` (Admin, intern + per Reverse-Proxy gegated)
- **Tracking-Skript:** Standard Umami `script.js` (~2 KB), per Auto-Deploy in Kundensites injiziert

**Render-Setup:**
- Web Service: `kompagnon-umami` (Docker, image `umami/umami:postgresql-latest`)
- Postgres: `kompagnon-umami-db` (Starter-Plan reicht initial)
- Env: `DATABASE_URL`, `APP_SECRET` (random 64 char), `TRACKER_SCRIPT_NAME=script.js`
- Custom Domain + automatisches SSL über Render

## 3. Architektur — Datenfluss

```
[Kunden-Website / Kompagnon-Landing]
   │ script.js + UTM
   ▼
[Umami auf Render]  ──────────►  [Umami-Postgres]
   ▲ REST-API (Bearer Token)
   │
[KAS-Backend services/umami_service.py]
   │ caching, snapshots, mapping customer_id ↔ website_id
   ▼
[KAS-Postgres analytics_websites + analytics_snapshots]
   │
   ├──► /api/analytics/admin/...   →  [Admin-UI: Akquise-Dashboard]
   └──► /api/analytics/customer/... →  [Customer-Portal: Add-On-Tab, Stripe-gated]
```

Kunden bekommen die Umami-Admin-UI **nie** direkt zu sehen — alle Daten werden über das KAS-Backend ausgeliefert.

## 4. Datenmodell (KAS-DB)

Neue Tabelle `analytics_websites` mappt Umami-Site → Owner (intern oder Kunde):

```sql
CREATE TABLE analytics_websites (
  id                BIGSERIAL PRIMARY KEY,
  umami_website_id  UUID NOT NULL UNIQUE,
  umami_share_id    TEXT,                    -- für public-share-Links (optional)
  owner_type        TEXT NOT NULL CHECK (owner_type IN ('internal','customer','lead')),
  customer_id       BIGINT REFERENCES users(id) ON DELETE SET NULL,
  lead_id           BIGINT REFERENCES leads(id) ON DELETE SET NULL,
  project_id        BIGINT REFERENCES projects(id) ON DELETE SET NULL,
  name              TEXT NOT NULL,
  domain            TEXT NOT NULL,
  status            TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active','paused','archived')),
  addon_status      TEXT NOT NULL DEFAULT 'none'
                    CHECK (addon_status IN ('none','trial','active','cancelled','past_due')),
  stripe_subscription_id TEXT,
  stripe_price_id   TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_analytics_websites_customer ON analytics_websites(customer_id);
CREATE INDEX idx_analytics_websites_lead     ON analytics_websites(lead_id);
CREATE INDEX idx_analytics_websites_owner    ON analytics_websites(owner_type);
```

Neue Tabelle `analytics_snapshots` für historische KPI-Snapshots (täglich), damit Reports auch nach Umamis Aufbewahrungs-Limits funktionieren:

```sql
CREATE TABLE analytics_snapshots (
  id              BIGSERIAL PRIMARY KEY,
  website_id      BIGINT NOT NULL REFERENCES analytics_websites(id) ON DELETE CASCADE,
  snapshot_date   DATE NOT NULL,
  visitors        INTEGER NOT NULL DEFAULT 0,
  pageviews       INTEGER NOT NULL DEFAULT 0,
  visits          INTEGER NOT NULL DEFAULT 0,
  bounce_rate     NUMERIC(5,2),
  avg_visit_secs  INTEGER,
  top_sources     JSONB,                    -- [{source, visitors}]
  top_campaigns   JSONB,                    -- [{utm_source, utm_campaign, utm_medium, visitors, conversions}]
  top_pages       JSONB,
  goals_completed INTEGER NOT NULL DEFAULT 0,
  raw             JSONB,                    -- vollständige Umami-Antwort für spätere Auswertung
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (website_id, snapshot_date)
);
CREATE INDEX idx_analytics_snapshots_date ON analytics_snapshots(snapshot_date);
```

Akquise-Verzahnung — Erweiterung bestehender Tabelle:

```sql
ALTER TABLE leads
  ADD COLUMN IF NOT EXISTS first_visit_at  TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS visit_count     INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS utm_source      TEXT,
  ADD COLUMN IF NOT EXISTS utm_medium      TEXT,
  ADD COLUMN IF NOT EXISTS utm_campaign    TEXT,
  ADD COLUMN IF NOT EXISTS umami_session_id UUID;
```

Migrations werden in `kompagnon/backend/migrations.py` ergänzt (bestehendes Muster).

## 5. Backend-Komponenten

### 5.1 Service-Layer — `kompagnon/backend/services/umami_service.py`

Analog zu `services/brevo_service.py`. Eine `UmamiService`-Klasse, die die Umami-REST-API kapselt:

```
UMAMI_BASE_URL        = os.getenv("UMAMI_BASE_URL")
UMAMI_API_TOKEN       = os.getenv("UMAMI_API_TOKEN")  # erstellt einmalig im Umami-Admin
UMAMI_TEAM_ID         = os.getenv("UMAMI_TEAM_ID", "")
```

Methoden:

| Methode | Beschreibung | Umami-Endpoint |
|---|---|---|
| `create_website(name, domain)` | Legt Umami-Website an, gibt website_id zurück | POST /api/websites |
| `delete_website(website_id)` | Löscht Site (z. B. bei Cancel) | DELETE /api/websites/{id} |
| `get_stats(website_id, start, end)` | Visitors / pageviews / bounce-rate für Zeitraum | GET /api/websites/{id}/stats |
| `get_metric(website_id, type, start, end)` | url, referrer, utm_source, utm_campaign, browser, country | GET /api/websites/{id}/metrics |
| `get_pageviews(website_id, start, end, unit)` | Zeitreihe (hourly/daily) | GET /api/websites/{id}/pageviews |
| `get_active_users(website_id)` | Live-Besucher | GET /api/websites/{id}/active |
| `get_events(website_id, start, end)` | Custom-Events / Goals | GET /api/websites/{id}/events |

Implementierung: `httpx.Client(timeout=10.0)` mit Bearer-Auth, Fehler werden geloggt + in HTTP 502/503 übersetzt (gleiche Defensive wie `brevo_service.py`). SDK-Defensive-Pattern (try/except ImportError) ist hier nicht nötig — wir sprechen direkt REST.

### 5.2 Snapshot-Job — `kompagnon/backend/automations/scheduler.py`

Neuer täglicher Job (z. B. 03:30 Europe/Berlin):

```
def snapshot_analytics_daily():
    for w in db.query(AnalyticsWebsite).filter_by(status='active'):
        try:
            stats     = umami.get_stats(w.umami_website_id, yesterday, today)
            campaigns = umami.get_metric(w.umami_website_id, 'utm_campaign', ...)
            sources   = umami.get_metric(w.umami_website_id, 'referrer', ...)
            pages     = umami.get_metric(w.umami_website_id, 'url', ...)
            upsert AnalyticsSnapshot(...)
        except Exception as e:
            logger.error(...)
```

Snapshots werden idempotent geschrieben (UNIQUE constraint + UPSERT).

### 5.3 Router — `kompagnon/backend/routers/analytics.py`

Prefix `/api/analytics`. **Klar getrennte Sub-Pfade**, um Prefix-Kollisionen aus dem Audit-Report zu vermeiden:

**Admin (Kompagnon-intern, require_admin):**
- `GET  /admin/websites` — alle Sites mit Filter `owner_type=internal|customer|lead`
- `POST /admin/websites` — Site anlegen (intern, lead-bound, customer-bound)
- `PATCH /admin/websites/{id}` — Owner ändern (Lead → Customer beim Onboarding)
- `DELETE /admin/websites/{id}` — Site archivieren
- `GET  /admin/websites/{id}/stats?range=7d` — KPIs
- `GET  /admin/websites/{id}/timeseries?unit=day&range=30d` — Verlauf
- `GET  /admin/leads/{lead_id}/activity` — Akquise-Activity-Timeline (Visits, Demo-Aufrufe, UTM)

**Customer (eingeloggter Kunde, gegated über Stripe-Subscription):**
- `GET /customer/website/stats?range=30d` — eigene Website (über `customer_id` aus JWT)
- `GET /customer/website/timeseries?unit=day&range=30d`
- `GET /customer/website/campaigns?range=30d` — UTM-Aufschlüsselung für Ad-Performance
- `GET /customer/website/pages?range=30d` — Top-Pages
- `GET /customer/website/sources?range=30d` — Top-Quellen / Referrer

**Public (Tracking-Helper):**
- `POST /track/lead-resolve` — Frontend-Lead-Capture sendet `umami_session_id` mit, Backend resolved Visit-Historie und schreibt UTM-Felder ins `leads`-Record (siehe Akquise-Verzahnung)

**Registrierung in `main.py`:** ein einziger Router, EIN Prefix → keine Wiederholung des im Report kritisierten Mehrfach-Prefix-Musters.

## 6. Frontend-Komponenten

### 6.1 Admin-UI — Akquise-Dashboard

Neue Seite `kompagnon/frontend/src/pages/AnalyticsAdmin.jsx`:

- Tabelle aller `internal` und `lead`-Sites mit Live-Visitor-Indicator
- Pro Lead: Activity-Timeline mit Visits + UTM-Quelle + Demo-Site-Aufrufen
- Filter: Owner-Typ, Datumsbereich, Quelle, Kampagne
- Aktion: „Lead → Kunde übergeben" (ändert `owner_type` und mappt auf neue `customer_id`)

Charts: Recharts (bereits im Projekt). Brand-Farben aus `tokens.css` (`--color-primary`, etc.) — **keine** hardcodierten Hex-Werte (Audit-Report Punkt).

### 6.2 Customer-Portal — Analytics-Tab

Neue Komponente `kompagnon/frontend/src/pages/CustomerAnalytics.jsx`:

- Gating: wenn `addon_status !== 'active'` → Self-Service-Booking-CTA (siehe Stripe)
- Wenn aktiv: KPI-Cards (Visitors, Pageviews, Bounce, Avg-Time), Verlaufs-Linien-Chart, Top-Quellen-Tabelle, **UTM-Kampagnen-Tabelle (für Ad-Performance)**, Top-Pages
- Datumsbereich-Selector (7d / 30d / 90d / Custom)
- Export: CSV-Download je Tabelle
- Loading-States + Error-States (Konsistenz mit Audit-Report-Befund: 258 Loading-Stellen vorhanden)

### 6.3 Booking-Komponente

`kompagnon/frontend/src/components/AnalyticsBookingCard.jsx` — analog zur GEO-Booking-Komponente (`9d7ebaa feat: add GEO addon self-service booking`). Triggert `POST /api/analytics-payments/create-subscription`.

## 7. Stripe-Add-On „Analytics & Ad-Performance"

Vorlage 1:1 von `kompagnon/backend/routers/geo_payments.py`. Neue Datei:

### 7.1 Router — `kompagnon/backend/routers/analytics_payments.py`

Prefix `/api/analytics-payments`. Endpoints:

- `POST /create-subscription` — Stripe Checkout Session erstellen, Erfolgs-/Cancel-URLs zeigen ins Kundenportal
- `POST /webhook` — Verarbeitet `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted` → setzt `analytics_websites.addon_status` und `stripe_subscription_id`
- `GET  /status` — aktueller Subscription-Status für eingeloggten Kunden
- `POST /cancel` — Subscription kündigen (Stripe-API + DB-Update)

### 7.2 Stripe-Setup (Dashboard, einmalig manuell)

- Produkt **„KOMPAGNON Analytics & Ad-Performance"**
- Preis-Optionen:
  - Standard: **29 €/Monat** (eine Website, bis 100 k Events/Monat) — Vorschlag, final mit dir
  - Optional Jahres-Tarif: 290 €/Jahr (2 Monate gratis)
- Webhook-Endpoint in Render: `https://claude-code-znq2.onrender.com/api/analytics-payments/webhook`
- Webhook-Secret als `STRIPE_WEBHOOK_SECRET_ANALYTICS` (eigene Variable, nicht mit GEO-Secret mischen)

### 7.3 Env-Variablen (Render)

```
UMAMI_BASE_URL=https://analytics.kompagnon.eu
UMAMI_API_TOKEN=...
UMAMI_TEAM_ID=...
STRIPE_WEBHOOK_SECRET_ANALYTICS=whsec_...
ANALYTICS_TRACKER_SCRIPT_URL=https://track.kompagnon.eu/script.js
```

Bestehende Variablen (`STRIPE_SECRET_KEY`, `FRONTEND_URL`) werden wiederverwendet.

## 8. Akquise-Verzahnung

Drei konkrete Berührungspunkte mit dem bestehenden Akquise-Flow:

### 8.1 UTM → Lead-Auto-Tagging

- Kompagnon-Landing-Pages (z. B. `kompagnon.eu/audit-aktion`) bekommen Umami-Snippet
- Visitor surft mit `?utm_source=meta&utm_campaign=audit-q2` — Umami speichert Session inkl. UTM
- Lead-Capture-Formular sendet beim Submit `umami_session_id` (über JS aus Local Storage / `umami.identify`) mit
- Backend `POST /api/analytics/track/lead-resolve` matcht Session → Visits → schreibt UTM-Felder + `first_visit_at` ins `leads`-Record

### 8.2 Demo-Site-Tracking

- Mockup- oder Demo-Sites (z. B. auf Subdomains während Sales-Phase) bekommen Umami-Site-Eintrag mit `owner_type='lead'`, gemappt an `lead_id`
- Sales-Dashboard zeigt pro Lead: Anzahl Demo-Aufrufe, letzter Aufruf, verbrachte Zeit
- Trigger: Bei ≥ 3 Aufrufen oder Wiederbesuch nach 24 h → automatische Slack-/E-Mail-Benachrichtigung an zuständigen Sales (optionaler Task in scheduler.py)

### 8.3 Pre-Sales-Audit-Daten

- Audit-Wizard (bestehender Flow) bekommt optionalen Schritt „kurzfristig Tracking auf Bestandssite" mit Einwilligungsdialog für Lead/Interessenten
- 7 oder 14 Tage Tracking → echte Visitor-/Bounce-Daten in Sales-Pitch-PDF einbauen
- Übergang Lead → Kunde: bestehende Umami-Site bleibt erhalten, `owner_type` wechselt auf `customer`, Daten gehen nicht verloren

## 9. Auto-Snippet-Injection beim Netlify-Deploy

Bestehender Flow (`kompagnon/docs/netlify-prozess.md` Schritt 2 — `POST /api/projects/{id}/netlify/deploy-all`) wird erweitert:

1. Vor dem HTML-Render: KAS prüft, ob für `project_id` ein `analytics_websites`-Record existiert
2. Wenn nein und Projekt hat aktives Analytics-Add-On: `umami.create_website(name=project.company, domain=project.netlify_url)` → Eintrag in `analytics_websites`
3. HTML-Renderer fügt Tracking-Snippet **vor `</head>`** ein:

```html
<script async defer
        src="https://track.kompagnon.eu/script.js"
        data-website-id="{umami_website_id}"></script>
```

Snippet wird dynamisch aus Site-Record gezogen, nicht hardcodiert.

## 10. Reports — Wöchentlich via Brevo

Optionaler Zusatz (Phase 7), verwendet bestehende Brevo-Pipeline:

- Cron-Job `Mon 09:00 Europe/Berlin` in scheduler.py
- Pro Customer-Site mit aktivem Add-On: Snapshot-Zusammenfassung der letzten 7 Tage als HTML-Mail
- Versand über `services/email.py` (Transaktional, NICHT Brevo-Newsletter — Reports sind individualisiert)

## 11. Sicherheit & DSGVO

- **EU-Hosting** (Render Frankfurt) für Umami + Postgres
- **Cookie-Less Tracking** (Umami nutzt keine Persistenz auf Client-Seite per Default) → keine Cookie-Banner-Pflicht für Basic-Tracking
- **Anonymisierung:** IP wird in Umami nur gehashed gespeichert (Default-Verhalten)
- **AV-Vertrag:** Standard mit Render abgeschlossen voraussetzen (klären)
- **Rate-Limiting:** auf `/api/analytics/track/*` (öffentlich aufrufbar, schon Bestandsmuster im Repo)
- **API-Token-Storage:** `UMAMI_API_TOKEN` nur in Render-Env, nicht im Code, nicht im Frontend
- **Customer-Permission-Check:** Jeder Customer-Endpoint prüft `analytics_websites.customer_id == jwt.customer_id` und `addon_status='active'`

## 12. Phasenplan

| # | Phase | Inhalt | Aufwand |
|---|---|---|---|
| 1 | Infra | Umami-Container auf Render, Postgres, Subdomain, SSL, Admin-Account, API-Token erzeugen | 1 Tag |
| 2 | Backend Core | DB-Migrations, `services/umami_service.py`, `routers/analytics.py` (Admin-Endpoints), Snapshot-Job | 1,5 Tage |
| 3 | Admin-UI | `AnalyticsAdmin.jsx`, Lead-Activity-Timeline, Owner-Wechsel-Aktion | 1 Tag |
| 4 | Customer-UI | `CustomerAnalytics.jsx`, Charts, UTM-Tabelle, CSV-Export, Add-On-Gating | 1,5 Tage |
| 5 | Stripe-Add-On | `routers/analytics_payments.py`, Stripe-Produkt anlegen, Webhook + Status-Endpoints, Booking-Komponente im Frontend | 1 Tag |
| 6 | Auto-Snippet | Erweiterung Netlify-Deploy-Pipeline (Site-Auto-Anlage + Snippet-Injection) | 0,5 Tage |
| 7 | Akquise-Verzahnung | UTM-Lead-Resolve-Endpoint, Demo-Tracking, Sales-Trigger | 1 Tag |
| 8 | Wöchentlicher Report | scheduler.py-Job + Mail-Template | 0,5 Tage |
| 9 | Tests + QA | Unit (umami_service, snapshot-job), Integration (Stripe-Webhook, Auth-Gating), E2E Customer-Flow | 1 Tag |

**Gesamt:** ~9 Werktage. Phase 1–5 deckt **Add-On verkaufsbereit**, Phase 6–8 sind Veredelung.

## 13. Risiken & Offene Fragen

1. **Umami-Multi-Tenant-Limits** — Umami's Teams-/Berechtigungs-Modell ist begrenzt. Lösung: KAS-Backend ist alleiniger API-User, Umami selbst ist nicht für Endkunden zugänglich → kein Mandantenproblem.
2. **Render-Postgres-Kosten** bei vielen Kundensites — Starter-Plan reicht für ~50 Sites, dann Upgrade. Snapshot-Tabelle hält Reports auch bei Postgres-Wechsel.
3. **DSGVO-Einwilligung beim Pre-Sales-Tracking** (Punkt 8.3) — braucht juristisch sauberen Einwilligungstext. Klären mit Datenschutzbeauftragten BEVOR Phase 7 startet.
4. **Stripe-Pricing** — 29 €/Monat ist Vorschlag, finale Festlegung mit dir notwendig (auch: Trial-Periode? gestaffelte Tiers nach Pageview-Volumen?).
5. **Bestehende Domain/Subdomain-Strategie** — `analytics.kompagnon.eu` vs. `track.kompagnon.eu` muss mit DNS-Verantwortlichem koordiniert werden.
6. **Umami-Updates** — Self-host bedeutet Update-Pflicht. Vorschlag: Render Auto-Deploy bei Image-Tag-Änderung (`umami/umami:postgresql-latest` → ggf. auf festen Tag pinnen, kontrolliert updaten).

## 14. Akzeptanzkriterien

Phase 1–5 ist abgeschlossen, wenn:

- [ ] Umami-Instanz unter `analytics.kompagnon.eu` erreichbar, SSL aktiv
- [ ] KAS-Admin kann interne Site anlegen → Tracking funktioniert in Browser-Test
- [ ] KAS-Admin kann Lead-Site anlegen, Lead-Aktivität ist im Lead-Detail sichtbar
- [ ] Kunde mit aktiver Add-On-Subscription sieht im Portal: Visitors, Pageviews, UTM-Kampagnen-Tabelle, Top-Pages
- [ ] Kunde ohne Subscription sieht Buchungs-CTA, KEINE Stats
- [ ] Stripe-Webhook setzt `addon_status='active'` nach Kauf, `cancelled` nach Kündigung
- [ ] Tägliche Snapshots werden geschrieben, > 0 Zeilen nach 7 Tagen Live-Betrieb

## 15. Referenz-Dateien (Vorlagen aus dem Repo)

- `kompagnon/backend/services/brevo_service.py` — Service-Pattern (REST-Wrapper, defensive Init)
- `kompagnon/backend/routers/geo_payments.py` — Stripe-Add-On-Pattern (Checkout-Session, Webhook, Status, Cancel)
- `kompagnon/backend/automations/scheduler.py` — Cron-Job-Pattern + `BackgroundTasks`
- `kompagnon/docs/netlify-prozess.md` — Netlify-Deploy-Flow (Snippet-Injection-Erweiterung)
- `kompagnon/backend/services/email.py` — kanonischer Mail-Versand für Reports
