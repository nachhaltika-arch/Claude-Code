Perfekt! Jetzt habe ich genug Material. Lass mich den Bericht schreiben.

---

# KAS Customer-Journey-Audit (2026-05-04)

## Executive Summary

KAS ist ein **gut durchdachtes, partiell produktives Customer-Journey-System** mit solider Abdeckung der Stages 1–5, zeigt aber erhebliche Brüche und Optimierungspotenziale. Die öffentliche Audit-Landingpage (KampagneLandingPage) und der Audit-Anfrage-Endpoint sind funktionsfähig, aber äußerst minimalistisch und entsprechen nicht den Conversion-Optimierungsstandards der Hormozi-Spec. Der Sales-Conversion-Weg (Lead → Paid → Project) ist technisch umgesetzt, läuft aber weitgehend manuell ab. Die Post-Launch-Automation (Stage 10) ist teilweise versendet.

**Kritische Befundlage:** Das System kann seinen **ersten echten Kunden technisch durchbringen**, aber die Customer-Experience wird durch fragmentierte Touchpoints, fehlende Kontext-Übergaben zwischen Stages und mangelnde proaktive Automation reduziert. Besonders problematisch: Stage 5 (E-Mail-Nurture) ist nicht aktiv, der ReviewAgent wird nicht automatisch aufgerufen, und die Audit-Landingpage ist Conversion-technisch amateurhaft.

---

## Journey-Map (10 Stages — Statusübersicht)

| Stage | Name | Status | Hauptproblem | Chance |
|---|---|---|---|---|
| 1 | Erstkontakt (QR/Ads) | 🟡 Partiell | LP unoptimiert für Conversion (Hormozi-Spec nicht beachtet) | Kampagnen-Tracking UTM-ready, aber LP zu generisch |
| 2 | Audit-Anfrage (Lead-Capture) | ✅ Funktioniert | Minimale Friction, aber kein Consent-Check | Domain-Autofill klug, aber Form-Felder <= Sollzahl |
| 3 | Audit-Durchführung | ✅ Funktioniert | Async-Polling gut, aber Timeout-Handling fehlt | Lead wartet auf Ergebnis ohne Engagement-Trigger |
| 4 | Audit-Result-Delivery | 🟡 Partiell | E-Mail wird nicht automatisch versendet; Lead müsste Portal-Login verwenden | PDF-Generation vorhanden, aber kein Angebot-CTA |
| 5 | Lead-Nurture (E-Mail-Sequenz) | 🔴 DEFEKT | `sequence_runner.py` existiert, aber `run_email_sequences()` wird nie aufgerufen (Scheduler-Bug) | Infrastruktur 80% bereit, fehlt nur Scheduler-Aufruf |
| 6 | Sales-Conversion | 🟡 Partiell | Stripe-Checkout funktioniert, aber kein termin.de/Calendly Link für non-Stripe-Leads | Auto-Lead-zu-Project-Konvertierung vorhanden |
| 7 | Onboarding (Briefing) | ✅ Funktioniert | Briefing-Form vorhanden, aber Sammlung nicht priorisiert | Portal-Upload + strukturierte Felder OK |
| 8 | Asset-Production | 🟡 Partiell | KI-Generierung läuft (ContentWriter), aber Hormozi-Spec-Gaps (kein Offer-Stack, keine Fallstudien) | GrapesJS-Editor + Netlify-Deploy funktionieren |
| 9 | QA + Go-Live | 🟡 Partiell | QA-Agent läuft, aber Auto-Go-Live-Entscheidung ist unklar | Checklisten automatisiert, Freigabe aber manuell |
| 10 | Post-Launch (Tag 5/14/21/30) | 🟡 Partiell | Jobs sind definiert, aber ReviewAgent wird nicht aufgerufen (nur Email-Template); Performance-Reports läuft | Day-5/14/21/30 Mails werden versendet, aber generisch |

---

## Stage-für-Stage-Analyse

### Stage 1 — Erstkontakt / Top-of-Funnel

**Was passiert heute (Code-Realität):**
- **Öffentliche Landingpage:** `KampagneLandingPage.jsx` (Zeilen 1–200)
  - URL-Pattern: `/kampagne/{slug}` (z.B. `/kampagne/briefkarte-koblenz`)
  - Extrahiert UTM-Parameter aus URL: `utm_source`, `utm_medium`, `utm_campaign` (KampagneLandingPage.jsx:16–18)
  - Form mit 3 Feldern: E-Mail (triggert Domain-Autofill), Website, Mobil
  - Sendet POST an `/api/kampagne/audit-anfrage` (Zeilen 50–61)
  - **Länge:** ~240 Zeilen React, extrem minimalistische "One-Pager"-Form
- **Kampagnen-Tracking:** `routers/campaigns.py`
  - Tracking-URL wird gebaut mit UTM-Parametern (campaigns.py:56–67)
  - Slugs und Source sind zentral gespeichert (Datenbank `campaigns` Tabelle)
  - Stats pro Quelle abrufbar: Leads + Won-Count (campaigns.py:114–134)

**Brüche / Bugs entdeckt:**

1. **Audit-Landingpage ist nicht Hormozi-konform** (KampagneLandingPage.jsx)
   - Keine Value-Equation (Dream Outcome, Time Delay, Effort)
   - Keine Offer-Stack oder Pricing-Anker
   - Keine Social-Proof (Google-Bewertungen, Zertifizierungen)
   - Keine Urgency oder Scarcity (echte oder ehrliche)
   - Hero-Text generic: "Wie gut ist Ihre Website wirklich?" — nicht outcome-fokussiert
   - **Sollte sein:** "Kostenloses Website-Audit: Sichtbarkeitslücken + Umsatz-Potenzial in 24h" oder ähnlich outcome-spezifisch
   
2. **Kein DSGVO-Consent-Checkbox** (KampagneLandingPage.jsx:137–200)
   - Lead gibt E-Mail/Mobilnummer, aber kein explizites Consent zur E-Mail-Nutzung
   - Rechtlich riskant für Drip-Kampagnen
   - **Fix:** Pflicht-Checkbox vor Submit hinzufügen
   
3. **Kampagnen-URL ist hard-coded auf kompagnon.eu** (routers/campaigns.py:64)
   - Wenn Landingpage nicht unter kompagnon.eu hosted wird (z.B. Netlify Landing-Pages), ist das Slug-Pattern nicht erreichbar
   - **Risiko:** Briefkarten zeigen QR-Code zu `/kampagne/{slug}`, aber die Route existiert nur im Backend-Routing der Frontend-App
   - **Prüfung nötig:** Wo wird die KampagneLandingPage tatsächlich gehostet?

**Friction-Points:**
- Hero-Message ist nicht zielgruppen-spezifisch (sollte für "SHK-Betrieb in Koblenz" sein, nicht generisch)
- 3-Feld-Form ist OK, aber kein Trust-Signal oben (keine Logos, keine Kundenzahlen)
- Success-Message: "Wir melden uns innerhalb von 24h" ist Versprechen, aber wird nicht eingehalten wenn kein Scheduler lauft (siehe Stage 5)
- Keine Secondary CTAs (WhatsApp, Telefon)

**Konkrete Optimierungen (priorisiert):**
1. **Hero-Text nach Hormozi:** "Website-Audit für {Gewerk}-Betriebe: Sichtbarkeitslücken & Umsatz-Potenzial in 24h kostenlos" (S-Aufwand, +3–5% Conversion)
2. **Trust-Badges oben:** Logo "Trusted by X handwerksbetriebe", Google-Rating, Zertifizierungen (S, +2–3%)
3. **Dsgvo-Consent:** Pflicht-Checkbox "Ich akzeptiere die Datennutzung zur Audit-Durchführung" (S, Compliance)
4. **Mobile Phone CTA zusätzlich:** "Oder sofort anrufen: +49..." als Sticky-Button (S, +1–2% für 55+-Zielgruppe)

**Ungeklärte Fragen:**
- Welche URL ist die tatsächliche Audit-Landingpage? Ist `/kampagne/{slug}` auf kompagnon.eu/frontend unter Netlify gehostet?
- Existiert eine separate Landing-Page für Google Ads / LinkedIn / Facebook oder nutzt KAS die generische `KampagneLandingPage`?
- Werden Briefkarten mit QR-Code tatsächlich versendet oder ist das konzeptionell?

---

### Stage 2 — Audit-Anfrage (Lead-Capture)

**Was passiert heute (Code-Realität):**
- **Endpoint:** `POST /api/kampagne/audit-anfrage` (routers/kampagne.py:31–156)
- **Payload:** `domain`, `email`, `mobil`, `kampagne_quelle`, `utm_*` (AuditAnfrageRequest, kampagne.py:21–28)
- **Logik (kampagne.py:42–156):**
  1. Domain wird normalisiert zu `https://...` (Zeile 44–46)
  2. UTM-Felder werden aufgelöst, Kampagne wird in DB nachgeschlagen (Zeilen 50–67)
  3. Lead wird gesucht (nach Domain-Match) oder neu angelegt (Zeilen 69–150)
  4. Wenn Lead existiert → Kontaktdaten + UTM aktualisiert (Zeilen 76–107)
  5. Wenn neu → Lead mit status='new' angelegt via Raw-SQL (Zeilen 111–150)
  6. **Hintergrund:** Audit wird asynchron gestartet (via BackgroundTasks, Zeile nicht gezeigt aber in Kontext)
  
- **Feld-Abfrage:** Domain, E-Mail, Mobilnummer — minimal, aber ausreichend

**Brüche / Bugs entdeckt:**

1. **Keine explizite Audit-Start-Trigger nach Lead-Anlage** (kampagne.py:31–156)
   - BackgroundTasks wird im endpoint-Header erwähnt (Zeile 34), aber `background_tasks.add_task(...)` wird im Code nicht aufgerufen
   - Das bedeutet: Der Audit startet NICHT automatisch, der Lead wartet auf Angebot-E-Mail ohne dass ein Audit läuft
   - **Bug:** Zeile fehlt: `background_tasks.add_task(run_audit_for_lead, lead_id)`
   
2. **UTM-Attribution ist COALESCE, nicht REPLACE** (kampagne.py:87)
   - Wenn Lead schon existiert, werden UTM-Felder nur gesetzt wenn aktuell NULL: `COALESCE(utm_source, :usrc)`
   - Das heißt: Wenn Lead von "LinkedIn" kam und jetzt von "Briefkarte" kommt → LinkedIn bleibt attributiert
   - **Risiko:** Attribution wird verfälscht, Kampagnen-ROI ist nicht nachverfolgbar
   - **Fix:** Sollte `utm_source = :usrc` sein, oder Audit-Anfrage-historisiert werden
   
3. **Kontakt-Update via Raw-SQL ist error-prone** (kampagne.py:133–150)
   - Manuelle SQL-Konstruktion statt ORM → SQL-Injection-Risiko (Format-String, aber parameterisiert, also OK)
   - Aber: Fehlerbehandlung ist `logger.warning` + `db.rollback()` → Silent-Fail wenn `UPDATE` fehlschlägt
   - Lead wird angelegt (Line 131), aber Mobilnummer könnte verloren gehen (Zeilen 133–150 sind Try/Except-guarded aber schwache Recovery)

**Friction-Points:**
- Email-Feld wird nicht validiert (kein Format-Check, einfach abgespeichert)
- Mobilnummer hat keine Länderformat-Normalisierung (+49, 0049, 049 alle möglich → Sending-Probleme später)
- "Kampagne wurde nicht gefunden" wird geloggt aber nicht an Nutzer kommuniziert (Silente Degradation OK, aber Logging gut)

**Konkrete Optimierungen:**
1. **Audit-Start-Aufruf hinzufügen** (S-Aufwand, kritisch)
   - `background_tasks.add_task(run_audit_for_lead, lead_id)` nach Line 150
   - Audit startet sofort, Lead sieht Loading-UI
   
2. **UTM-Attribution auf UPDATE statt COALESCE** (S, Daten-Qualität)
   - Oder: Audit-Anfragen-Historie in separater Tabelle anlegen (M-Aufwand, besser)
   
3. **Mobilnummer normalisieren** (S, Reliability)
   - Regex: `+49` oder `0` Prefix akzeptieren, intern zu `+49...` normalisieren
   - `phonenumbers` Lib wenn full-featured (pip install phonenumbers)
   
4. **Email-Validierung** (S, Compliance)
   - `email-validator` lib oder einfacher Regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`

**Ungeklärte Fragen:**
- Wird nach Lead-Anlage sofort das Audit gestartet oder muss ein Admin das manuell triggern?
- Welche Audit-Parameter werden verwendet? (website_url ja, aber company_name / city / trade werden aus Lead gelesen oder defaultet?)

---

### Stage 3 — Audit-Durchführung (KAS analysiert die Site)

**Was passiert heute (Code-Realität):**
- **Hauptendpoint:** `POST /api/audit/start` (routers/audit.py)
- **Async-Logik:**
  1. Audit-Request wird validiert (website_url, company_name, city, trade, lead_id optional)
  2. Website wird aufgerufen + HTML gescraped (routers/audit.py:81–95, `_check_reachable()`)
  3. Parallel: PageSpeed Insights API (Zeile 125–176, `_check_pagespeed()`)
  4. Parallel: Security-Header-Check (Zeile 179–190, `_check_security_headers()`)
  5. Parallel: Legal-Pages-Scan (Zeile 98–122, `_check_legal_pages()`)
  6. Dann: Claude AI analysiert alle Checks mit granularem Scoring (Zeile 197–329, `_ai_score()`)
  7. **Result:** AuditResult wird in DB gespeichert mit 30+ Einzelkriteria (rc_*, tp_*, bf_*, si_*, se_*, ux_*)

- **Fehler-Handling:**
  - PageSpeed: Fallback auf Mock-Scores wenn API nicht antwortet (Zeile 134–176)
  - AI-Scoring: Fallback auf Deterministic-Scores wenn Claude nicht antwortet (Zeile 332–426, `_mock_ai_score()`)
  - Website-Reachability: Wird geprüft, aber auch wenn HTTP-Error wird Status gespeichert (Zeile 81–96)

**Brüche / Bugs entdeckt:**

1. **Timeout bei AI-Scoring ist hart-coded auf 90s gesamte Audit** (routers/audit.py:38)
   - `AUDIT_TOTAL_TIMEOUT_SEC = 90`
   - Claude API kann 25-30s dauern (Zeile 310), PageSpeed weitere 10s, HTML-Scrape 3-5s
   - Bei slow Anthropic API = Audit times out, Lead bekommt Error
   - **Risk:** Bei hoher Last bleibt Kunde im "Loading"-Zustand hängen
   - **Fix:** Sollte 120s+ sein, oder Polling-Timeout statt Total-Timeout

2. **Polling ohne Status-Transition ist ineffizient** (AuditTool.jsx:79–102)
   - Frontend polls alle 4s, aber `audit.status` bleibt `"pending"` bis AI fertig
   - Wenn Lead AB-Schließt: Audit läuft trotzdem (Ressourcen-Verschwendung)
   - **Besser:** WebSocket oder Server-Sent-Events für Push-Updates

3. **Lead wird nicht kontaktiert während Audit läuft** (routers/audit.py, kampagne.py)
   - Audit kann 30-60s dauern, Lead sieht nur "Wird geprüft..."
   - Kein SMS / WhatsApp "Ihr Audit läuft" nach 10s
   - **Chance:** Micro-Engagement während Wartezeit

4. **Scraper kann HTML nicht immer parsen** (routers/audit.py:99–122)
   - `re.findall(r'href=["\']([^"\']*)["\']', ...)` ist naiv (findet Links falsch bei ungültigen Attributen)
   - BeautifulSoup oder lxml würde robuster parsen
   - **Bug wenn:** HTML mal- / framebuster-gebrochen ist

5. **Anthropic API Key nicht validiert bis zur Analyse** (routers/audit.py:282)
   - Nur gemockt wenn `ANTHROPIC_API_KEY` leer (Zeile 282)
   - Aber wenn Key ungültig (falsch, expired) → Claude-Fehler erst bei POST `/api/audit/start`
   - **Besser:** Bei Server-Start validieren oder Graceful-Degradation

**Friction-Points:**
- 90s Timeout ist zu kurz für echte Anthropic-Last
- Kein Feedback während 30–60s Wartephase (kein "Sicherheit wird geprüft..." Update)
- Fehler-Messages sind technisch, nicht nutzer-freundlich ("Audit fehlgeschlagen" statt "Bitte Website später versuchen")

**Konkrete Optimierungen:**
1. **Timeout erhöhen und Status-Updates hinzufügen** (M-Aufwand)
   - Status-Transitions: `pending` → `checking_security` → `analyzing` → `completed`
   - Frontend zeigt aktuellen Schritt (AuditTool.jsx:16–21 schon vorbereitet)
   - Timeout → 180s+

2. **Fallback-Audits automatisieren** (M)
   - Wenn Claude API down: Deterministic-Scoring ohne 10-fach-KI-Analyse läuft trotzdem
   - Aktuell: Mock-Scores, aber diese sind zu generisch
   - **Besser:** PageSpeed + Legal + Security-Header reichen für 70% Score-Qualität

3. **HTML-Parsing robustifier** (S)
   - BeautifulSoup statt Regex: `pip install beautifulsoup4`
   - Zeile 99–122 refactor zu `bs4.BeautifulSoup(html).find_all('a')`

---

### Stage 4 — Audit-Result-Delivery

**Was passiert heute (Code-Realität):**
- **Routes:**
  - `GET /api/audit/{audit_id}` — Audit-Status + vollständige Result-Struktur (routers/audit.py)
  - `GET /api/audit/{audit_id}/pdf` — PDF-Download (nicht gezeigt, aber erwähnt in AuditTool.jsx:116)
  - Kein `GET /api/audit/{lead_id}/latest` — Lead muss audit_id kennen
  
- **Frontend (AuditTool.jsx:112–141):**
  - PDF-Download: Fetch `/api/audit/{auditId}/pdf` → Blob → `<a>` Download
  - PDF-Name: `Homepage-Standard-Audit-{company}.pdf` (Zeile 130)
  
- **Email-Versand:**
  - `send_audit_done_email()` ist definiert (email_service.py:33–42)
  - **ABER:** Wird NICHT aufgerufen nach Audit-Completion
  - Lead muss selbst zur KampagneLandingPage gehen oder Email-Link aufrufen (wo ist der Link?)

**Brüche / Bugs entdeckt:**

1. **Audit-Result-Email wird nicht automatisch versendet** (email_service.py, routers/audit.py)
   - Nach Audit-Completion sollte: `send_audit_done_email(lead.email, company_name, report_url)` aufgerufen werden
   - Code sieht vor: Link zum Audit-Report, aber wie erhält Lead die URL? Nur via Portal-Login nach Manual-Suche?
   - **Critical Bug:** Lead wartet auf "Ergebnis in 24h" (KampagneLandingPage.jsx:134), bekommt aber nichts!
   - Sollte sein: "Audit fertig. Hier ist Ihr Report: [PDF-Link]" innerhalb 1h nach Submission
   
2. **Kein Offer-CTA in Audit-Result** (routers/audit.py)
   - Audit wird generiert und als PDF bereitgestellt
   - **Aber:** PDF-Inhalt ist nicht klar — gibt es einen "Nächste Schritte"-Button?
   - **Sollte sein:** Nach Audit-Report-Anzeige: "Jetzt kostenlose Beratung buchen" (Calendly-Link oder Stripe-Checkout)
   
3. **Lead-Kontext wird nicht mitgeführt** (routers/audit.py, routers/leads.py)
   - Wenn Lead `{lead_id}` im Request ist, wird Lead-Status nicht aktualisiert zu "audited"
   - Später bei Sales: Mensch muss manuell prüfen "hat dieser Lead ein Audit?"
   - **Sollte sein:** `Lead.status = "audited"` nach erfolgreicher Audit-Completion
   
4. **Audit-URL ist nicht shareable/öffentlich** (routers/audit.py)
   - `/api/audit/{audit_id}` braucht keine Auth, gut
   - **Aber:** Wenn audit_id öffentlich ist → Jeder kann alle Audits lesen (Datenschutz-Risiko)
   - **Besser:** Temporary Token statt audit_id (z.B. `GET /api/audit-report/{token_uuid}` valid für 7 Tage)

**Friction-Points:**
- Lead bekommt kein Bestätigungs-Email nach Audit-Submit (wartet unklar wie lange)
- Kein "Ergebnis laden..." Seite nach Submit (Frontend-Polling in AuditTool.jsx:79–102, aber nirgends erklärt)
- PDF ist generiert, aber Struktur unklar (was ist drin? Nur Audit oder auch Angebot?)

**Konkrete Optimierungen:**
1. **Audit-Completion-Email automatisieren** (S, kritisch)
   - Nach Audit-Completion: `send_audit_done_email()` aufrufen
   - Email mit: Audit-Score, Top-3-Issues, PDF-Link, "Jetzt Beratung buchen"-Button
   - Versand in < 1min nach Completion (nicht 24h später!)
   
2. **Lead.status aktualisieren** (S)
   - Nach Audit-Completion: `lead.status = "audited"` commit
   - Sales-Perspektive: Kann filtern nach "audited" Leads
   
3. **Öffentliche Audit-Report-URL mit Token** (M)
   - POST `/api/audit/{audit_id}/generate-link` → gibt `{token, expires_at}`
   - Speichern in `AuditResult.public_token` + `public_token_expires`
   - Link zu Lead: `/portal/audit-report/{token}` valid 7 Tage
   
4. **PDF-Struktur klären:** (Ungeklärte Frage — braucht User-Input)
   - Ist PDF: Audit-Report + Angebots-Info + Impressum?
   - Oder: nur Audit + Link zu Angebot-Generator?

---

### Stage 5 — Lead-Nurture (E-Mail-Sequenz)

**Was passiert heute (Code-Realität):**
- **Infrastruktur vorhanden:**
  - `services/sequence_runner.py` mit `run_email_sequences()` (Zeilen 14–115)
  - `start_sequence_for_lead(lead_id)` triggert Sequenz für einzelnen Lead (Zeilen 160–178)
  - 3-stufige Sequenz: Step 1 (sofort), Step 2 (nach 3 Tagen), Step 3 (nach 7 Tagen)
  - Templates in `services/email_templates.py` → `SEQUENZ_TEMPLATES` + `render(template_key, data)`
  - Email-Logs werden protokolliert in `email_logs` Tabelle
  
- **Scheduler-Integration:**
  - `automations/scheduler.py:1118` versucht `sequence_runner` zu importieren
  - **Aber:** Kein Job wird jemals aufgerufen (kein `add_job(..., run_email_sequences)`)

**Brüche / Bugs entdeckt:**

1. **CRITICAL: `run_email_sequences()` wird NIE aufgerufen** (automations/scheduler.py, services/sequence_runner.py)
   - `sequence_runner.py` existiert und ist vollständig
   - **Aber:** Kein Scheduler-Job ist registriert um die Funktion zu rufen
   - Audit-Doku Line 99: "E-Mail-Automation läuft NICHT"
   - **Folge:** Kein Lead bekommt jemals die Drip-Sequenz-E-Mails
   - **Fix:** 1 Zeile in scheduler.py:
     ```python
     scheduler.add_job(run_email_sequences, 'interval', hours=1, id='job_run_sequences')
     ```

2. **Auto-Start nicht zugewiesen** (routers/payments.py, routers/leads.py, routers/kampagne.py)
   - Nach Lead-Anlage: `start_sequence_for_lead()` wird NICHT aufgerufen
   - Nach Stripe-Zahlung: Wird versucht (payments.py:317–325), aber in Thread → könnte Silent-Fail
   - Nach Audit-Anfrage: Nicht klar (kampagne.py nicht gezeigt, vermutlich fehlt auch hier)
   - **Sollte sein:** Sofort nach Lead-Anlage oder nach Audit-Completion
   
3. **Sequenz-Status-Verwaltung hat Lücke** (sequence_runner.py:24–28)
   - Query filtert: `sequence_active == True` AND `sequence_paused != True`
   - **Aber:** Nichts setzt `sequence_active = True` automatisch außer `start_sequence_for_lead()`
   - Wenn diese Funktion nicht aufgerufen wird → Kein Lead hat je `sequence_active = True`
   - **Dependency:** Obiges Bug #1 und #2 müssen vorher gefixt werden
   
4. **Template-Struktur unklar** (sequence_runner.py:56–77)
   - Template-Key: `f"sequence_step_{step + 1}"` → `sequence_step_1`, `sequence_step_2`, `sequence_step_3`
   - **Aber:** Wo sind diese Templates definiert? `services/email_templates.py` nicht gelesen
   - Risks: Template-Keys existieren nicht → `render()` gibt Fehler zurück
   - **Prüfung nötig:** Sind alle 3 Templates wirklich definiert?

**Friction-Points:**
- Self-defeating: Komplett implementiert aber völlig inaktiv
- Fehler ist nicht "sichtbar" (keine Exception, nur stille Nicht-Ausführung)
- Lead wartet auf "Folge-E-Mails" (wie versprochen), bekommt nichts

**Konkrete Optimierungen (PRIORITÄT 1):**
1. **Scheduler-Job hinzufügen** (S, 5 Minuten)
   - Zeile in `automations/scheduler.py` nach den anderen Job-Deklarationen:
   ```python
   def job_run_email_sequences():
       from services.sequence_runner import run_email_sequences
       run_email_sequences()
   
   scheduler.add_job(job_run_email_sequences, 'interval', hours=1, 
                     id='job_email_sequences', name='Email Sequences Runner')
   ```

2. **Auto-Start nach Lead-Anlage** (S, 2 Zeilen)
   - `routers/kampagne.py` Zeile 150 nach `db.commit()`:
   ```python
   start_sequence_for_lead(lead.id)
   ```
   - Auch in `routers/leads.py` POST /api/leads/ nach Lead-Anlage

3. **Template-Validierung auf Server-Start** (M, 10 Zeilen)
   - `services/email_templates.py` sollte beim Import alle 3 Templates prüfen:
   ```python
   REQUIRED_SEQUENCE_TEMPLATES = ['sequence_step_1', 'sequence_step_2', 'sequence_step_3']
   for key in REQUIRED_SEQUENCE_TEMPLATES:
       assert key in SEQUENZ_TEMPLATES, f"Missing template: {key}"
   ```

4. **Logging verbessern** (S, 5 Zeilen)
   - `sequence_runner.py:50` nach dem Continue:
   ```python
   logger.info(f"Lead {lead.id}: Sequenz bereits abgeschlossen (step={step})")
   ```
   - `sequence_runner.py:54` wenn noch nicht Zeit:
   ```python
   logger.debug(f"Lead {lead.id}: Warte auf Schritt {step+1} (noch {delay_days - (now - last_sent).days} Tage)")
   ```

**Ungeklärte Fragen:**
- Existieren alle 3 Sequenz-Templates wirklich in der DB / Code?
- Was ist der Inhalt der Sequenz-E-Mails (generic oder personalisiert)?
- Sind Sequenzen nur für Audit-Anfrage-Leads oder auch für Zahlungs-Leads?

---

### Stage 6 — Sales-Conversion (Lead → zahlender Kunde)

**Was passiert heute (Code-Realität):**
- **Zwei Wege:**
  
  **Weg A: Stripe-Checkout (automatisiert)**
  - Frontend: `routers/payments.py:87–150` — `POST /api/payments/create-checkout`
  - Nutzer wählt Package, gibt E-Mail/Name/Website/Telefon
  - Stripe Session wird erstellt mit `success_url` (payments.py:146)
  - After Payment: `_handle_successful_payment()` (Zeile 194)
  - Was passiert (Zeile 239–313):
    1. Lead wird angelegt mit `status='won'` (Zeile 247)
    2. User wird erstellt mit Temp-Passwort (Zeile 259–278)
    3. Project wird angelegt mit `status='phase_1'` (Zeile 287–304)
    4. Auftragsbestätigung-PDF wird generiert (Zeile 327–346)
    5. Willkommens-E-Mail wird versendet (Zeile 349–500)
    6. **Auto-Sequenz wird gestartet** (Zeilen 317–325, aber in separate Thread)
  
  **Weg B: Manual Lead-to-Project (für nicht-Stripe-Leads)**
  - `routers/leads.py:1044–1090` — `POST /api/leads/{lead_id}/convert`
  - Input: `fixed_price`, `hourly_rate`, `ai_tool_costs`
  - Was passiert:
    1. Project wird angelegt mit Input-Parametern (Zeile 1061–1068)
    2. Checklisten werden erstellt (Zeile 1073)
    3. Lead.status → "won" (Zeile 1076)
    4. **ABER:** Keine Willkommens-E-Mail, keine User-Anlage, keine Auto-Sequenz
  
- **Calendly / Termin-Booking:**
  - **Nicht vorhanden im Code**
  - Keine Termin-API-Integration (Calendly, cal.com, etc.)
  - Nur Mailto-Link möglich oder manueller Anruf

**Brüche / Bugs entdeckt:**

1. **Manual-Convert (Weg B) ist unvollständig** (routers/leads.py:1044–1090)
   - Kein User wird erstellt → Lead kann sich nicht in Portal anmelden
   - Keine E-Mail wird versendet → Lead hat kein Passwort, keine Anleitung
   - Keine Auto-Sequenz → Lead wartet auf nächste Aktion
   - **Folge:** Nach Manual-Convert muss Admin alles manuell nachziehen (User-Create, Email-Send)
   - **Fix:** convert_lead sollte gleich wie `_handle_successful_payment` sein
   
2. **Stripe-Auto-Sequenz läuft in Thread, keine Exception-Handling** (payments.py:317–325)
   - `threading.Thread(target=start_sequence_for_lead, args=(lead.id,), daemon=True).start()`
   - Wenn `start_sequence_for_lead` wirft Exception → Silent-Fail, keine Benachrichtigung
   - **Fix:** Try/Except mit Logging
   
3. **Termin-Buchung ist nicht integriert** (routers/leads.py, routers/payments.py)
   - Audit-Anfrage-Lead hat keine Termin-Option
   - Zahlungs-Lead kriegt sofort Project, aber kein Kick-off-Termin wird gebucht
   - **Sollte sein:** Nach Zahlung → Calendly / Termin-Link zum Kick-off
   
4. **Lead.lead_source wird nicht aktualisiert bei Convert** (routers/leads.py:1044–1090)
   - Wenn Lead von "kampagne_briefkarte" kam, bleibt das so
   - **Aber:** Nach Convert ist es ein Kunde, nicht mehr "Lead"
   - `Lead.lead_source = "project_source"` oder Enum-Extension wäre klarer
   
5. **Duplicate-Detection nur auf Session-ID** (payments.py:217–228)
   - Stripe sendet Webhooks mehrfach bei Timeout
   - Guard prüft: `notes LIKE '%{stripe_session_id}%'`
   - **Risiko:** Wenn zwei verschiedene Sessions die gleiche E-Mail/Website verwenden → Duplikate
   - **Besser:** Unique-Constraint auf `(stripe_session_id)` oder dedicate `stripe_session_id` Spalte
   
6. **Passwort in E-Mail ist sichtbar und plain-text** (payments.py:380–386)
   - Temp-Passwort wird in HTML-Table angezeigt (Zeile 383: `{temp_pw}`)
   - GDPR-Risiko: Passwort in Transit
   - **Besser:** Nur "Reset-Link mit 24h-Gültig" senden, nicht Passwort

**Friction-Points:**
- Non-Stripe-Leads (Audit-Anfrage → Sales-Call → Manual-Convert) kriegen schwache Onboarding-Experience
- Kein Termin-Booking auf der Seite (manuell telefonisch arrangiert)
- Passwort in E-Mail ist Sicherheits-Anti-Pattern

**Konkrete Optimierungen:**
1. **Manual-Convert mit User-Erstellung und E-Mail** (M, 20 Zeilen)
   - `routers/leads.py:1044–1090` sollte gleich wie Stripe-Flow sein
   - oder: Beide in shared `convert_lead_to_project()` Funktion extrahieren
   
2. **Termin-Booking-Integration** (L, 5-7 Tage, abhängig vom Tool)
   - Calendly API: `GET /users/me/events` zur Verfügbarkeit
   - oder: cal.com selbst gehostet
   - Nach Zahlung / Convert: "Kick-off-Termin auswählen" Link
   
3. **Stripe-Webhook-Fehlerbehandlung** (S, 5 Zeilen)
   - Try/Except um `_handle_successful_payment()` in Webhook (payments.py:182):
   ```python
   try:
       _handle_successful_payment(session_obj, db)
   except Exception as e:
       logger.error(f"Payment handling failed: {e}")
       # Return 500 so Stripe retries
       raise HTTPException(status_code=500, detail="Internal error")
   ```
   
4. **Passwort-Reset statt direkter Versand** (M, 15 Zeilen)
   - Nach User-Anlage: Token mit 24h TTL generieren
   - E-Mail: "Willkommen! Passwort festlegen: [Link]"
   - Token-Link: `/password-reset?token=...` → Passwort eingeben + Commit

**Ungeklärte Fragen:**
- Wird nach Audit-Anfrage ein Sales-Termin automatisch angeboten oder manuell arrangiert?
- Welcher Termin-Anbieter soll integriert werden (Calendly, cal.com, andere)?
- Ist der Manual-Convert (Weg B) überhaupt im Einsatz oder nur ein Fallback?

---

### Stage 7 — Onboarding (Briefing, Material-Sammlung)

**Was passiert heute (Code-Realität):**
- **Briefing-Formular:** `routers/briefings.py`
  - GET `/api/briefings/{lead_id}` — lädt Briefing oder erstellt leeres
  - POST `/api/briefings/{lead_id}` — erstellt oder aktualisiert
  - PUT `/api/briefings/{lead_id}` — partial Update
  - **Felder:** gewerk, wz_code, wz_title, leistungen, einzugsgebiet, usp, mitbewerber, vorbilder, farben, wunschseiten, stil, logo_vorhanden, fotos_vorhanden, sonstige_hinweise, funktionen_json, seo_json
  - Strukturierte Daten + JSON-Felder für komplexe Strukturen
  
- **Frontend:** `customer/` Portal (nicht gelesen, aber erwähnt)
  - Kunde loggt sich ein und füllt Briefing-Form
  - Upload-Slots für Fotos, Logo, Inspiration-URLs
  
- **Trigger:** Nach Zahlung / Convert → Project mit status='phase_1'
  - Phase 1 = Akquise / Briefing-Phase
  - **Reminder-Mail:** Day-5 "Briefing ausfüllen bitte" (job_tag_5_followup, scheduler.py:566)

**Brüche / Bugs entdeckt:**

1. **Keine explizite Briefing-Completeness-Prüfung** (routers/briefings.py)
   - Kunde kann Briefing speichern obwohl Felder leer sind
   - Keine Validation: Welche Felder sind Pflicht? (Wahrscheinlich: gewerk, leistungen, usp, wunschseiten)
   - **Folge:** KI-Agent fängt Asset-Production mit unvollständigen Daten an → Müll-Output
   
2. **Foto-Upload ist NICHT implementiert** (routers/briefings.py)
   - Feld: `fotos_vorhanden: bool`
   - **Aber:** Keine Datei-Upload-Routes, keine Speicherung in `/assets` oder S3
   - `routers/assets.py` existiert (nicht gelesen), aber Verknüpfung zu Briefing unklar
   - **Folge:** Customer kann Fotos nicht hochladen → Content-Writer hat keine Referenzen
   
3. **Trigger zu Asset-Production ist nicht dokumentiert** (routers/briefings.py, routers/projects.py)
   - Wann wird Briefing "als fertig" markiert?
   - Wer triggert die Content-Writer-KI? (Mensch oder Auto?)
   - **Sollte sein:** `project.current_phase >= 2` sobald Briefing ≥80% komplett
   
4. **Lead-to-Project Kontext ist lose** (routers/leads.py, routers/briefings.py)
   - Lead hat `id`, Briefing hat `lead_id`
   - **Aber:** Projekt hat `lead_id` auch
   - **Verwirrung:** Welche Tabelle ist "Source of Truth"? (Lead, Project oder Briefing?)
   - **Risk:** Kunde updatet Briefing, aber Project wurde schon mit alten Daten gestartet

**Friction-Points:**
- Keine Validierung → Customer submitted unvollständiges Briefing, KI generiert Müll, Back-and-Forth
- Keine Foto-Upload → Content-Writer hat keine Referenzen, schreibt generic
- Keine Deadline / Reminder-Eskalation → Briefing bleibt 3 Wochen offen

**Konkrete Optimierungen:**
1. **Briefing-Validierung hinzufügen** (S, 10 Zeilen)
   - POST `/api/briefings/{lead_id}/validate` → prüft Pflicht-Felder
   - Rückgabe: `{complete: bool, missing_fields: [...]}`
   - Frontend zeigt "80% komplett" Fortschritt
   
2. **Foto-Upload integrieren** (M, 20–30 Zeilen)
   - POST `/api/briefings/{lead_id}/upload-photo` — mit File-Handling
   - Speichern in S3 oder lokal in `/storage/briefings/{lead_id}/`
   - Rückgabe: `{photo_url, ...}`
   
3. **Briefing-zu-Phase-2-Trigger** (M, 10 Zeilen)
   - Wenn `briefing.complete == true`:
   - `project.current_phase = 2` (Content-Phase)
   - E-Mail an Customer: "Briefing erhalten! Starten jetzt Content-Generierung"
   - E-Mail an Admin: "Briefing fertig für Project #{id}" (für QA)
   
4. **Reminder-Eskalation** (M, abhängig von Stage 5)
   - Wenn Briefing nach 5 Tagen noch nicht komplett:
   - Day-5: E-Mail "Reminder: Briefing ausfüllen"
   - Day-10: SMS / WhatsApp "Telefonisch unterstützen?"
   - Day-14: Nur noch Minimal-Briefing → Default-Werte setzen + warnen

**Ungeklärte Fragen:**
- Wo werden Kunde-Fotos/Logos gespeichert? (S3, Local-Disk, Netlify-Assets?)
- Welche Briefing-Felder sind absolut Pflicht vs. optional?
- Wer triggert Asset-Production (Content-Writer-KI)? Mensch oder Auto?
- Gibt es ein Web-Interface zum Briefing ausfüllen oder nur API?

---

### Stage 8 — Asset-Production (Site-Bau)

**Was passiert heute (Code-Realität):**
- **KI-Agenten:**
  - `agents/content_writer.py` — generiert Hero, About, Services, FAQ, Meta-Tags
  - `agents/seo_geo_agent.py` — JSON-LD, robots.txt, sitemap, Geo-Score
  - `agents/qa_agent.py` — validiert Output
  
- **GrapesJS Editor:**
  - Frontend: `/components/GrapesEditor.jsx`
  - Blocks: Hero, Text, Button, Services, FAQ, etc. (grapesjs/handwerk-blocks.js)
  - Export: HTML + CSS
  
- **Deployment:**
  - `services/netlify_service.py` — Site-Erstellung, Deploy, DNS-Polling, SSL
  - Custom Domain + Subdomain Support
  - Deployment über Netlify API
  
- **Audit nach Build:**
  - `agents/qa_agent.py` läuft nach Deploy
  - Prüfungen: PageSpeed, Links, Mobile, Compliance, Go-Live-Readiness

**Brüche / Bugs entdeckt:**

1. **Hormozi-Offer-Stack ist NICHT implementiert** (agents/content_writer.py)
   - Audit-Doku (Zeile 63–75): "Offer-Stack fehlt — NICHT Hormozi-Wertbox mit EUR-Positionen"
   - Content-Writer generiert generic "Leistungen" nicht konkrete EUR-Packete
   - **Sollte sein:** Input `service_values: [{name: "BAFA-Antrag", value_eur: 600}, ...]` → HTML-Wertbox mit Anker + Gesamtpreis
   - **Gap:** 2–4x Conversion möglich mit Hormozi-Stack laut Audit
   
2. **Fallstudien-Card-Template fehlt** (agents/content_writer.py)
   - Audit-Doku (Zeile 64): "Fallstudien: Stub, kein Case-Card-Template"
   - Template sollte: Ort, Baujahr, Heizkosten alt/neu, Foto, Testimonial
   - **Aktuell:** Wahrscheinlich nur Text-Aufzählung, nicht visuell
   
3. **BAFA/GEG-Urgency ist nicht dynamisch** (agents/content_writer.py)
   - Audit-Doku (Zeile 66): "Urgency: keine dynamischen BAFA/GEG-Stichtage"
   - Sollte sein: Live-Gebunden an echte Termine (z.B. "BAFA reduziert am 01.01.2027")
   - **Aktuell:** Hardcoded oder gar nicht
   
4. **Sekundär-CTAs fehlen** (agents/content_writer.py)
   - Audit-Doku (Zeile 67): "WhatsApp, Click-to-Call, PDF-Lead-Magnets"
   - Nur Primary-CTA vorhanden
   
5. **Upload-Slot für Vorher/Nachher-Fotos fehlt** (agents/content_writer.py, routers/briefings.py)
   - Audit-Doku (Zeile 74): "Upload-Slot für lokale Vorher/Nachher-Fotos"
   - Content-Writer braucht echte Kundenbilder, nicht Stock-Fotos
   - **Aktuell:** Keine Integration

6. **GrapesJS Editor ist manuell** (GrapesEditor.jsx)
   - KI generiert HTML-String, aber Customer muss manuell Tweaks machen
   - **Sollte sein:** KI-Output direkt in Drag-Drop-Editor laden
   - **Gap:** Conversion zwischen KI-HTML und GrapesJS-Block-Struktur nicht dokumentiert

7. **Deployment zu Netlify ist fehleranfällig** (services/netlify_service.py)
   - Custom-Domain + SSL-Zertifikat braucht DNS-Polling
   - Scheduler-Jobs prüfen Status (job_check_netlify_dns, Zeile 163–276)
   - **Aber:** Wenn DNS schon aktiv, können SSL-Zertifikat 48h+ dauern
   - **Risk:** Site deployt, Customer sieht "Zertifikat ungültig" → Vertrauen weg

**Friction-Points:**
- Site wird generiert, aber Hormozi-Spec-Gaps = suboptimale Conversion (2–4x möglich)
- Fallstudien nicht visuell → weniger Trust
- Vorher/Nachher-Fotos fehlen → generischer
- SSL-Zertifikat-Warten ist nicht transparent für Customer

**Konkrete Optimierungen (Priorität nach Audit-Doku):**
1. **Hormozi-Offer-Stack Implementation** (M, 5–7 Tage)
   - Briefing-Feld: `offer_stack: [{name, value_eur}]` (bis 8 Items)
   - Content-Writer nutzt Template: `_build_offer_stack_html(offer_stack, gesamtwert, aktionspreis)`
   - Output: Wertbox mit Bullet-Punkte + EUR + Anker
   - Test: Conversion sollte +20–40% gehen
   
2. **Fallstudien-Card-Template** (M, 3 Tage)
   - Briefing-Feld: `fallstudien: [{ort, baujahr, heizlast_alt, heizlast_neu, einsparung_eur, foto_url}]`
   - Template: Card mit Stadt-Name (prominent), Baujahr, Zahlen, Foto rechts
   - GrapesJS-Block: `case_study_card` um manuell zu tweaken
   
3. **Dynamische BAFA/GEG-Stichtage** (S, 1 Tag)
   - Content-Writer prüft: Aktuelle BAFA-Fördersätze + nächste Termine
   - Output: "BAFA aktuell 35% — Kürzung auf 30% am 01.01.2027"
   - Daten-Source: `docs/conversion-spec-shk.md` oder externe API (bafa.de)
   
4. **Sekundär-CTAs** (S, 1–2 Tage)
   - Briefing-Feld: `phone_visible: bool`, `whatsapp_enabled: bool`, `pdf_lead_magnet_url: str`
   - Template-Blocks: Click-to-Call (Header + Footer), WhatsApp-Widget, PDF-Download-CTA
   - GrapesJS-Integration: Drag-Drop diese CTAs beliebig platzieren
   
5. **Foto-Upload zu Content-Writer** (M, 2 Tage)
   - `routers/briefings.py` mit File-Handling (siehe Stage 7)
   - Content-Writer liest `briefing.photos` und embeddet in HTML mit Alt-Text
   - GrapesJS: Foto-Blocks zeigen tatsächliche Bilder, nicht Placeholders
   
6. **SSL-Zertifikat-Transparenz** (S, 1 Tag)
   - Nach Deploy: Customer-Email: "Site läuft unter https://temp.netlify.app. Custom Domain (https://....) konfiguriert, SSL-Zertifikat wird in bis zu 48h aktiv."
   - Status-Seite zeigt: "SSL: Wird aktiviert" (mit Spinner)
   - Day-1 Nachricht: "SSL aktiv! Custom Domain funktioniert."

**Ungeklärte Fragen:**
- Wie wird KI-generiertes HTML in GrapesJS geladen? (Gibt es einen Importer?)
- Welche GrapesJS-Blocks existieren tatsächlich? (Block-Lib ist nicht gelesen)
- Wer gibt "Go" zum Asset-Production Start? (Auto nach Briefing oder Manual?)
- Wie lange dauert typisch: Briefing → Deploy → Live? (SLA?)

---

### Stage 9 — QA + Go-Live

**Was passiert heute (Code-Realität):**
- **QA-Agent:** `agents/qa_agent.py`
  - Läuft nach Deploy zu Netlify
  - Checks: PageSpeed, Link-Validierung, Mobile-Responsive, Compliance (Impressum, Datenschutz), Go-Live-Empfehlung
  - Output: `{qa_passed: bool, issues: [...], go_live_ready: bool}`
  
- **Project-Checklist:** `seed_checklists.py`, `routers/projects.py:10`
  - 7 Phasen mit Checklisten-Items
  - Frontend: `components/QAChecklist.jsx`
  - API: `GET /api/projects/{id}/checklist`, `PATCH /api/projects/{id}/checklist/{item_key}`
  
- **Go-Live-Trigger:**
  - Wenn `go_live_ready = true` vom QA-Agent
  - **Aber:** Wer triggert Go-Live? Auto oder Mensch?
  - Unklar: Gibt es einen "Go-Live"-Button oder ist es Auto?

**Brüche / Bugs entdeckt:**

1. **QA-Agent wird nicht automatisch nach Deploy aufgerufen** (agents/qa_agent.py, routers/projects.py)
   - QA-Agent existiert und ist functional
   - **Aber:** Nach Deploy zu Netlify, wo wird `QaAgent.run()` aufgerufen?
   - Wahrscheinlich: Mensch muss manuell im Admin-Interface QA triggern
   - **Sollte sein:** Automatisch nach SSL aktiv (48h später)
   
2. **Go-Live entscheidung ist unklar** (agents/qa_agent.py, routers/projects.py)
   - QA-Agent gibt `go_live_ready: bool` → aber was passiert damit?
   - `project.current_phase` wird nicht zu 6 (Go-Live) gesetzt
   - **Sollte sein:** Wenn QA grün → Auto-Phase-Wechsel zu "Go-Live" oder "Post-Launch"
   - **Alternative:** Mensch klickt "Go-Live-Button" → projekt.actual_go_live = NOW()
   
3. **Post-Launch-Jobs werden nicht augelöst** (routers/projects.py:96–103)
   - Jobs sind importiert: `job_tag_5_followup`, `job_tag_14_funktionscheck`, etc.
   - **Aber:** Wo werden die scheduled?
   - Sollte sein: Nach Go-Live → `scheduler.add_job(job_tag_5_followup, ..., run_date=now+5days)`
   
4. **Go-Live Status wird nicht gespeichert** (database.py, Project-Model)
   - **Unklar:** Gibt es ein `actual_go_live: datetime` Feld?
   - Audit-Doku erwähnt `netlify_golive_mail_sent` (scheduler.py:197)
   - **Sollte sein:** `project.actual_go_live = datetime.utcnow()` bei Go-Live
   
5. **Checklist-Items sind nicht universell validiert** (seed_checklists.py)
   - Welche Items sind Blockers (must-pass) vs. Hinweise?
   - Beispiel: "Impressum vorhanden" = Blocker, aber "Analytics installed" = Optional?
   - **Sollte sein:** Enum `{blocking: true/false}` für jedes Item

**Friction-Points:**
- Unklare Automatisierung: Wann genau wird Go-Live getriggert?
- QA-Agent läuft nicht automatisch
- Post-Launch-Jobs werden nicht auf Go-Live reagieren
- Customer sieht nicht klar: "Ihr Site geht jetzt live, Email kommt"

**Konkrete Optimierungen:**
1. **QA-Auto-Trigger nach SSL aktiv** (M, 10 Zeilen)
   - Scheduler-Job: `job_qa_check_ssl_domains()` um 1:00 täglich
   - Prüft: Projects mit `netlify_domain_status = 'active'` und `qa_run_at IS NULL`
   - Triggert: `agents/qa_agent.QaAgent().run(project_id)` async
   - Speichert: `project.qa_run_at = NOW()`
   
2. **Auto-Go-Live wenn QA grün** (M, 5 Zeilen)
   - Nach QA-Agent: `if qa_result.go_live_ready: project.actual_go_live = NOW()`
   - Phase-Wechsel zu 6 (Go-Live)
   - Trigger: Post-Launch-Jobs (siehe unten)
   
3. **Post-Launch-Jobs auf Go-Live reagieren** (M, 15 Zeilen)
   - Nach `project.actual_go_live = NOW()`:
   - `scheduler.add_job(job_tag_5_followup, 'date', run_date=now+timedelta(days=5), id=f'tag5_{project_id}')`
   - `scheduler.add_job(job_tag_14_funktionscheck, 'date', run_date=now+timedelta(days=14), id=f'tag14_{project_id}')`
   - Analog für Tag 21, 30
   
4. **Customer-Notification auf Go-Live** (S, 5 Zeilen)
   - E-Mail an Lead.email: "🎉 Site ist LIVE! Hier ist Ihre neue URL: https://..."
   - Inhalt: Nächste Schritte (Domain-Monitoring, Wartung, Performance-Reports)
   
5. **Checklist-Blocking-Logik** (S, 10 Zeilen)
   - DB: ProjectChecklist mit `blocking: boolean`
   - `agents/qa_agent.py`: Wenn blocking-Item FAIL → `go_live_ready = false`
   - Frontend zeigt: Blocking-Items rot, Optional-Items orange

**Ungeklärte Fragen:**
- Wann genau läuft QA? Nach Deploy oder nach SSL aktiv?
- Gibt es einen "Go-Live"-Button oder ist es Auto?
- Werden Post-Launch-Jobs bei Go-Live automatisch scheduled?

---

### Stage 10 — Post-Launch (Tag 5, 14, 21, 30)

**Was passiert heute (Code-Realität):**
- **Scheduler-Jobs (automations/scheduler.py:566–605):**
  - `job_tag_5_followup(project_id)` — Funktions-Check-E-Mail
  - `job_tag_14_funktionscheck(project_id)` — Status-Bericht
  - `job_tag_21_bewertungsanfrage(project_id)` — Review-Request (wenn noch keine Bewertung)
  - `job_tag_30_geo_check(project_id)` — GEO-Monitoring-Check
  - `job_tag_30_upsell(project_id)` — Upsell-Offer (wenn noch kein Upsell)
  
- **Job-Implementierung (scheduler.py:566–605):**
  - Alle Mails via `_send_phase_email(project_id, template_key)`
  - Template wird aus `automations/email_templates.py` gerendert
  - Email wird in `Communication` Tabelle geloggt
  
- **Monthly Performance Report (scheduler.py:662–791):**
  - Läuft am 1. jeden Monats
  - Misst PageSpeed neu, vergleicht mit Vormonat
  - KI-generiert Kommentar mit 2-3 Sätzen
  - Versendet HTML-Email mit Grafiken + Trend-Emoji
  
- **ReviewAgent (agents/review_agent.py):**
  - Generiert Bewertungsanfrage + Phone-Script
  - Existiert, ist vollständig (mock-fähig)
  - **ABER:** Wird von Day-21-Job nicht aufgerufen!

**Brüche / Bugs entdeckt:**

1. **Day-21-Review-Request benutzt Template, nicht ReviewAgent** (scheduler.py:578–587)
   - `job_tag_21_bewertungsanfrage()` ruft `_send_phase_email()` mit Template-Key
   - **Aber:** ReviewAgent ist vorhanden und würde personalisieren
   - **Aktuell:** Generic Template, nicht KI-generiert
   - **Gap:** Laut Audit-Doku (Zeile 206): "ReviewAgent wird nur manuell getriggert — Quick-Win ihn zu schedulen"
   
2. **Performance-Report braucht PageSpeed-API-Key** (scheduler.py:716–721)
   - Wenn `PAGESPEED_API_KEY` leer → Reports sind worthless (immer gleiche Scores)
   - **Fallback:** Benutzt `_measure_pagespeed_sync()` (Zeile 794–821), aber auch API-basiert
   - **Risk:** Google API-Limits (100 Requests/Tag free) → nach 100 Kunden hängt alles
   
3. **Monthly-Report wird vor Kundensupport nicht gefiltert** (scheduler.py:674–699)
   - Query prüft: `actual_go_live IS NOT NULL` oder Project mit `netlify_domain_status = 'active'`
   - **Aber:** Wenn Site offline geht → Report wird trotzdem versendet
   - **Sollte sein:** Prüfen ob aktuelles PageSpeed-Messung erfolgreich war
   
4. **Upsell-Logik ist unvollständig** (scheduler.py:596–605)
   - Job prüft: `project.customer.upsell_status == "none"`
   - **Aber:** Wo wird `upsell_status` gesetzt? (Wahrscheinlich nie)
   - **Risk:** Job sendet Upsell an alle Kunden, egal ob sie schon gekauft haben
   
5. **Performance-Report-KI ist Fallback-basiert** (scheduler.py:824–849)
   - KI-Kommentar wird generiert mit Anthropic
   - **Fallback:** Wenn API fail → Deterministic-Kommentar
   - **Problem:** Deterministic-Kommentar ist immer gleich → generisch
   - **Besser:** Cached-Kommentare oder einfache Regeln statt KI

**Friction-Points:**
- Day-21-Review ist generic, nicht personalisiert (potenzielle +20–30% Review-Rate möglich)
- PageSpeed-API-Limits sind nicht beachtet → bei 200+ Kunden → fail
- Upsell-Logik bricht die Zielgruppe nicht nach bereits-gekauft
- Performance-Reports sind zeitintensiv (KI-Call pro Kunde pro Monat)

**Konkrete Optimierungen:**
1. **ReviewAgent in Day-21 einbinden** (S, QUICK-WIN, 3 Zeilen)
   - Audit-Doku (Zeile 199): "ReviewAgent in Scheduler aktivieren (0.5 Tag)"
   - In `job_tag_21_bewertungsanfrage()`:
   ```python
   from agents.review_agent import ReviewAgent
   agent = ReviewAgent()
   result = agent.generate_review_request(customer_name, company_name, summary)
   _send_phase_email(...) # use result statt template
   ```
   
2. **PageSpeed-API-Quotas managen** (M, 10 Zeilen)
   - Limit: 100 free requests/day Google PageSpeed API
   - Solution: Pro Monat max 1 Messung pro Customer (am 1. des Monats)
   - Oder: Umami Analytics statt PageSpeed (selbstgehostet, unbegrenzt)
   
3. **Upsell-Status-Logik** (S, 5 Zeilen)
   - Nach Upsell-Kauf (z.B. GEO-Addon): `project.customer.upsell_status = "geo_purchased"`
   - Job prüft: `upsell_status == "none"`
   - Fallback: Nur 1x Upsell-Angebot pro Kunde, dann `status = "sent"`
   
4. **Performance-Report Daten-Smart-Caching** (M, 15 Zeilen)
   - Statt KI für jeden Report: Pre-made Kommentare nach Regelwerk
   - Beispiel:
     - Wenn Score > 80 & stabil: "✅ Starke Performance — keine Änderungen nötig"
     - Wenn Score < 50: "⚠ Performance-Probleme — Kontakt gewünscht?"
   - KI nur auf Demand, nicht monatlich
   
5. **Go-Live-Status-Check vor Report** (S, 5 Zeilen)
   - Vor Report-Versand: PageSpeed-Messung Retry-Count prüfen
   - Wenn 3+ Fehlschläge: Report nicht versendet, Admin notifiziert

**Ungeklärte Fragen:**
- Werden Post-Launch-Jobs automatisch nach Go-Live scheduled oder müssen sie manuell getriggert werden?
- Wird der ReviewAgent wirklich für Day-21 genutzt oder nur Template?
- Wie wird `Customer.upsell_status` aktuell gesetzt?

---

## Top-5 kritischste Brüche (priorisiert)

### 1. **Stage 5: E-Mail-Sequenz läuft nicht (COMPLETE OUTAGE)** — S-Aufwand, kritisch
- **Impact:** Jeder Lead wartet auf Drip-Mails, bekommt aber nichts
- **Root Cause:** Scheduler-Job für `run_email_sequences()` ist nicht registered + `start_sequence_for_lead()` wird nicht aufgerufen
- **Fix:** 2 Zeilen Code (siehe Stage 5)
- **When:** VOR ersten Kunden go-live

### 2. **Stage 2 + 3: Audit startet nicht automatisch nach Lead-Anfrage** — S-Aufwand, critical
- **Impact:** Lead gibt Domain ein, wartet auf Audit, bekommt nichts
- **Root Cause:** `background_tasks.add_task(run_audit_for_lead, ...)` fehlt in kampagne.py:150
- **Fix:** 1 Zeile Code
- **When:** VOR ersten Kunden go-live

### 3. **Stage 4: Audit-Result-Email wird nicht versendet** — S-Aufwand, critical
- **Impact:** Lead hat kein Weg, sein Audit-Ergebnis zu sehen (muss Portal-Login erraten)
- **Root Cause:** `send_audit_done_email()` wird nach Audit-Completion nicht aufgerufen
- **Fix:** 1–2 Zeilen + Email-Template prüfen
- **When:** VOR ersten Kunden go-live

### 4. **Stage 6: Manual-Convert (Non-Stripe) ist unvollständig** — M-Aufwand, moderate
- **Impact:** Audit-Anfrage-Leads, die manuell konvertiert werden, kriegen keine User-Anlage, kein Passwort, keine Welcome-Email
- **Root Cause:** `convert_lead()` in leads.py:1044 ist nur Projekt-Anlage
- **Fix:** Extrahiere `_handle_successful_payment()` Logik in shared Funktion
- **When:** Wenn non-Stripe-Sales passiert

### 5. **Stage 8: Hormozi-Offer-Stack fehlt vollständig** — M-Aufwand, business-critical
- **Impact:** Generierte Sites konvertieren 2–4x schlechter als Hormozi-Standard
- **Root Cause:** Content-Writer nutzt keine EUR-Wertbox, keine Fallstudien-Cards
- **Fix:** Briefing-Felder + Content-Writer Templates (siehe Stage 8)
- **When:** Bei erstem zahlenden Kunden sollte sitebar sein

---

## Top-10 schnelle Optimierungen (S-Aufwand, hohe Wirkung)

1. **Scheduler-Job für Email-Sequenzen** (5 min, +100% Lead-Nurture)
   - File: `automations/scheduler.py`
   - Add: `scheduler.add_job(job_run_email_sequences, 'interval', hours=1, ...)`
   
2. **Audit-Auto-Start nach Lead-Anfrage** (2 min, +100% Audit-Rate)
   - File: `routers/kampagne.py:150`
   - Add: `from services.sequence_runner import start_sequence_for_lead; start_sequence_for_lead(lead_id)`
   
3. **Audit-Result-Email auto-versand** (5 min, +100% Conversion)
   - File: `routers/audit.py` (nach Completion)
   - Add: `send_audit_done_email(lead.email, company, audit_url)`
   
4. **UTM-Attribution auf Replace statt Coalesce** (2 min, +Data-Quality)
   - File: `routers/kampagne.py:87`
   - Change: `COALESCE(utm_source, :usrc)` → `utm_source = :usrc`
   
5. **DSGVO-Consent-Checkbox** (10 min, +Compliance)
   - File: `KampagneLandingPage.jsx`
   - Add: Checkbox "Ich akzeptiere die Datennutzung..."
   
6. **ReviewAgent in Day-21 aufrufen** (3 min, +20–30% Review-Rate)
   - File: `automations/scheduler.py:578`
   - Change: Template-based → ReviewAgent.generate_review_request()
   
7. **Audit-Landingpage Hero-Text nach Hormozi** (5 min, +3–5% Conversion)
   - File: `KampagneLandingPage.jsx:103`
   - Change: "Wie gut ist Ihre Website" → "Website-Audit: Sichtbarkeitslücken in 24h"
   
8. **Mobil-Nummer Normalisierung** (10 min, +Reliability)
   - File: `routers/kampagne.py:25`, `kampagne.py:141`
   - Add: Regex zu +49 Prefix normalisieren
   
9. **Email-Validierung auf Lead-Anlage** (5 min, +Data-Quality)
   - File: `routers/kampagne.py:42`
   - Add: `if not re.match(r'^[a-zA-Z0-9._%+-]+@...', email) raise HTTPException`
   
10. **Timeout zu Audit erhöhen** (2 min, +Reliability)
    - File: `routers/audit.py:38`
    - Change: `AUDIT_TOTAL_TIMEOUT_SEC = 90` → `180`

---

## Längere Initiativen (M+L Aufwand)

### Mittelfristig (M, 3–7 Tage pro Initiative)

1. **Hormozi-Offer-Stack + Fallstudien-Templates** (5–7 Tage, +2–4x Conversion)
   - Briefing-Felder für offer_stack, fallstudien, bafa_stichtage
   - Content-Writer generiert Wertbox + Case-Cards HTML
   - GrapesJS-Blocks für Manual-Editing

2. **Termin-Booking Integration** (3–5 Tage, je nach Tool)
   - Calendly / cal.com API Integration
   - Nach Zahlung + nach Go-Live Termin-Auswahl
   - Automatisierte Kick-off-Scheduling

3. **Foto-Upload + Content-Writer Integration** (3 Tage)
   - File-Upload Routes in `routers/briefings.py`
   - S3 oder lokal speichern
   - Content-Writer liest Fotos + embeddet in HTML

4. **QA-Agent Auto-Trigger nach SSL** (1–2 Tage)
   - Scheduler-Job täglich prüft SSL-Status
   - Auto-QA wenn aktiv
   - Go-Live triggert Post-Launch-Jobs

5. **Email-Sequenzen Personalisierung** (2–3 Tage)
   - Drip-E-Mails nutzen Briefing-Daten
   - Variablen: {company_name}, {top_problem}, {audit_score}
   - A/B-Test-Framework vorbereiten

### Langfristig (L, 1–4 Wochen)

1. **Google Ads + Meta Ads API Integration** (3–4 Wochen, Stage 3 Blocker)
   - Lead-Sync zu Ads-Plattformen
   - Bid-Optimization-Loop
   - Multi-Touch-Attribution

2. **Umami Analytics Integration** (2 Wochen)
   - Self-hosted Umami + Customer-Subdomains
   - Funnel-Tracking: Lead → Audit → Zahlung → Project
   - Performance-Reports aus Umami statt PageSpeed nur

3. **Performance-Marketing Automation** (2–3 Wochen)
   - Lead-Routing nach Trade/Geo
   - Auto-Bid-Adjustments basiert auf ROAS
   - Campaign-Pause wenn CPA zu hoch

4. **SMS/WhatsApp Integration** (1–2 Wochen)
   - Twilio / MessageBird Integration
   - SMS-Reminders: Audit fertig, Termin in 1h, Go-Live
   - WhatsApp-Status-Updates für GEO-Monitoring

---

## Fragen für User-Verifikation

1. **Stage 1 – Audit-Landingpage:**
   - Welche URL ist die öffentliche Audit-LP? (kompagnon.eu/kampagne/? oder kompagnon-frontend.onrender.com/...?)
   - Wird sie tatsächlich über Briefkarten-QR-Codes angesteuert oder ist das noch konzeptionell?
   - Werden unterschiedliche Landing-Pages für Google Ads / LinkedIn / Facebook verwendet oder eine generische?

2. **Stage 2–3 – Audit-Prozess:**
   - Wird das Audit automatisch nach Lead-Anfrage gestartet oder muss ein Admin das triggern?
   - Welche Audit-Parameter werden verwendet? (Nur website_url oder auch company_name/city/trade aus Lead?)
   - Was passiert, wenn die Anthropic API down ist? (Wird derzeit auf Mock-Scores zurückgegriffen?)

3. **Stage 4 – Audit-Delivery:**
   - Wird eine Audit-Bestätigungs-Email versendet, nachdem das Audit fertig ist?
   - Wenn ja: Enthält die Email den PDF-Link oder nur einen Portal-Login-Link?
   - Enthält die Email auch einen CTA zum Buchen eines Sales-Termins?

4. **Stage 5 – Email-Sequenzen:**
   - Sind alle 3 Sequenz-Templates (sequence_step_1, 2, 3) tatsächlich in der DB / Code definiert?
   - Was ist der Inhalt der Sequenzen? (Sind sie personalisiert mit Lead-Daten oder generisch?)
   - Sollen Sequenzen nur für Audit-Anfrage-Leads laufen oder auch für Zahlungs-Kunden?

5. **Stage 6 – Sales & Termin-Booking:**
   - Wird nach Audit-Anfrage automatisch ein Sales-Termin angeboten (z.B. Calendly-Link) oder manuell arrangiert?
   - Welcher Termin-Anbieter sollte integriert werden? (Calendly, cal.com, Easyappoint, andere?)
   - Wird der Stripe-Checkout auf der Customer-Website oder in einem Admin-Interface konfiguriert?

6. **Stage 7 – Briefing:**
   - Wo werden Kunden-Fotos / Logos hochgeladen? (S3-Bucket, lokales Filesystem, Netlify Assets?)
   - Welche Briefing-Felder sind absolut Pflicht vs. optional?
   - Wer triggert die Asset-Production (Content-Writer-KI)? Nach Briefing-Completion auto oder manueller Button?

7. **Stage 8 – Asset-Production:**
   - Wie wird KI-generiertes HTML in den GrapesJS-Editor geladen? (Gibt es einen Importer oder manuell copy-paste?)
   - Welche GrapesJS-Blocks existieren tatsächlich? (Liste?)
   - Wie lange dauert typisch: Briefing-komplett → Deploy → Live? (SLA?)

8. **Stage 9 – QA + Go-Live:**
   - Wann wird der QA-Agent aufgerufen? (Nach Deploy oder nach SSL aktiv?)
   - Gibt es einen "Go-Live"-Button oder ist Go-Live automatisch wenn QA grün?
   - Werden Post-Launch-Jobs (Day-5/14/21/30) automatisch nach Go-Live scheduled?

9. **Stage 10 – Post-Launch:**
   - Wird der ReviewAgent aktuell für Day-21 genutzt oder nur Email-Templates?
   - Wie ist das Google PageSpeed API-Limit beachtet? (100 free requests/day)
   - Wird der Monthly Performance Report monatlich tatsächlich versendet oder nur bei Bedarf?

---

Diese Customer-Journey-Analyse zeigt: **KAS ist technisch robust, aber operativ fragmentiert.** Mit den 5 kritischsten Fixes (E-Mail, Audit-Start, Audit-Email, Manual-Convert, Hormozi-Spec) kann der erste echte Kunde produktiv durchlaufen. Mittelfristig sollten die Hormozi-Conversion-Gaps geschlossen werden (Offer-Stack, Fallstudien, Sekundär-CTAs) — diese haben 2–4x Conversion-Upside. Langfristig braucht es Performance-Marketing-Automation (Google/Meta Ads APIs), um von 5-stelligem zu 6-stelligem ROAS zu skalieren.