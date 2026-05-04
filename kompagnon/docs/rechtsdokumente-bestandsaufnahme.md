# Bestandsaufnahme für Datenschutzerklärung & AGB — KAS

**Status:** Technische Bestandsaufnahme v1
**Erstellt:** 2026-04-30
**Zweck:** Vollständiger Input für Rechtsanwalt / Rechtstextgenerator
**Branch:** staging

> **WICHTIG — Haftungsausschluss:** Dieses Dokument ist eine technische Bestandsaufnahme, **kein Rechtstext**. Vor Veröffentlichung MUSS ein Fachanwalt für IT-/Datenschutzrecht prüfen. Empfohlen: eRecht24 Premium, activeMind, oder direkter Anwalt. Falsche oder fehlende Angaben können Abmahnungen + Bußgelder bis 4 % des Jahresumsatzes (DSGVO Art. 83) auslösen.

---

## TEIL A — DATENSCHUTZERKLÄRUNG (Eingabe-Daten)

### A1. Verantwortliche Stelle (vom Inhaber auszufüllen)

```
Firma:           [Rechtsform + Firmenname, z. B. Kompagnon Communications GmbH]
Inhaber/GF:      [Name(n)]
Anschrift:       [Straße, PLZ, Ort, Land]
Handelsregister: [Amtsgericht + HRB-Nummer]
USt-IdNr.:       [DE...]
E-Mail:          [info@kompagnon.eu o. ä.]
Telefon:         [+49 ...]
Website:         https://kompagnon.eu
```

### A2. Datenschutzbeauftragter

DSGVO-Kriterien für Pflicht-DSB (§ 38 BDSG):
- ≥ 20 Personen ständig mit automatisierter Verarbeitung beschäftigt **ODER**
- Kerntätigkeit: umfangreiche regelmäßige Überwachung von Betroffenen **ODER**
- Verarbeitung besonderer Kategorien (Art. 9 DSGVO)

→ **Prüfen:** Wenn KAS umfangreiche Lead-Akquise + Audit fremder Websites macht, könnte „Kerntätigkeit Überwachung" zutreffen → externer DSB empfohlen (Kosten ~50–150 €/Monat).

### A3. Hosting & Infrastruktur

| Komponente | Anbieter | Sitz | Funktion | DSGVO-Status |
|---|---|---|---|---|
| Backend (FastAPI) | Render Inc. | Region Frankfurt (EU) | API + Logik | EU-Hosting, AVV mit Render abschließen |
| Frontend (React) | Render Inc. | Region Frankfurt (EU) | Statische Auslieferung | EU-Hosting |
| Datenbank | Render Postgres | EU | Speichert ALLE personenbezogenen Daten | EU-Hosting |
| Kunden-Websites | Netlify Inc. | USA (CDN global, EU-Edge) | Hosting der vom KAS deployten Kundensites | **Drittland** — SCCs nötig, AVV mit Netlify Inc. |
| Geplant: Umami | Render (self-hosted) | EU | Analytics | EU-Hosting nach Setup |

**Render AVV:** [render.com/legal/dpa](https://render.com/legal/dpa)
**Netlify AVV:** [netlify.com/gdpr-ccpa](https://www.netlify.com/gdpr-ccpa/)

### A4. Auftragsverarbeiter (Subprocessors) — vollständige Liste

#### A4.1 Anthropic (Claude AI)

- **Zweck:** KI-Generierung (Content-Texte, Lead-Analyse, Audit-Bewertung, QA-Prüfung, SEO/GEO-Analyse, Briefing-Auswertung)
- **Sitz:** USA
- **Übermittelte Daten:** Lead-Notizen, Briefing-Antworten, Website-Inhalte (gescraped), Audit-Befunde, ggf. Kundennamen + Branchentexte
- **Drittland:** Ja → Standardvertragsklauseln (SCCs) erforderlich
- **Aufbewahrung bei Anthropic:** 30 Tage Logs (laut Trust Center, prüfen)
- **AVV:** [anthropic.com/legal/dpa](https://www.anthropic.com/legal/dpa)
- **Code-Referenz:** `kompagnon/backend/agents/content_writer.py`, `lead_analyst.py`, `qa_agent.py`, `review_agent.py`, `seo_geo_agent.py`

#### A4.2 Stripe (Zahlungsabwicklung)

- **Zweck:** Subscription-Abrechnung GEO-Add-on, geplant Analytics-Add-on
- **Sitz:** Stripe Payments Europe Ltd. (Irland) / Stripe Inc. (USA)
- **Übermittelte Daten:** Kundenname, E-Mail, Rechnungsadresse, Zahlungsdaten (von Stripe direkt erfasst, nicht über KAS), Stripe-Customer-ID
- **Drittland:** Ja (USA, Stripe Inc.) → SCCs vorhanden
- **AVV:** [stripe.com/legal/dpa](https://stripe.com/legal/dpa)
- **Code-Referenz:** `routers/payments.py`, `routers/geo_payments.py`, `services/geo_stripe_helper.py`

#### A4.3 Brevo (E-Mail-Marketing / Newsletter)

- **Zweck:** Newsletter-Versand, Listen- und Kontakt-Verwaltung
- **Sitz:** Brevo SAS, Paris (EU) — primärer Speicher EU
- **Übermittelte Daten:** E-Mail-Adresse, Vor-/Nachname, Listen-Zugehörigkeit, Klick-/Öffnungs-Tracking
- **Drittland:** Nein (EU)
- **AVV:** [brevo.com/de/legal/agbenddatenschutz](https://www.brevo.com/de/legal/dpa/)
- **Code-Referenz:** `services/brevo_service.py`, `routers/newsletter.py`, DB-Spalten `brevo_campaign_id`, `brevo_list_id`, `brevo_contact_id`

#### A4.4 SMTP-Provider (Transaktionsmails — getrennt von Brevo)

- **Zweck:** Transaktional (Phasen-Updates, Audit-Berichte, Approval-Anfragen, Passwort-Reset)
- **Anbieter:** Gemäß Konfiguration `SMTP_HOST` Env-Variable — **vom Inhaber zu ergänzen** (z. B. „SMTP über IONOS", „SendGrid", „Brevo Transactional")
- **Übermittelte Daten:** E-Mail-Adresse Empfänger, Inhalt, Anhänge (PDFs)
- **Code-Referenz:** `services/email.py`

#### A4.5 Google PageSpeed Insights API

- **Zweck:** Performance-Messung von Lead-/Kunden-Websites im Audit
- **Sitz:** Google Ireland Ltd. / Google LLC (USA)
- **Übermittelte Daten:** URL der gescannten Website (kein personenbezogener Inhalt — aber Website-URL kann personenbeziehbar sein, z. B. bei Einzelunternehmer-Domains)
- **Drittland:** USA → SCCs
- **API-Key:** `GOOGLE_PAGESPEED_API_KEY`
- **Code-Referenz:** Audit-Pipeline (`routers/audit.py`)

#### A4.6 Netlify (Site-Hosting für Kunden-Websites)

- **Zweck:** Auslieferung der deployten Kunden-Websites + DNS/SSL
- **Sitz:** Netlify Inc., USA (mit EU-Edge-Servern)
- **Übermittelte Daten:** Website-Inhalte (HTML, Bilder), Custom-Domain, ggf. Besucher-IPs (Server-Logs auf Netlify-Seite)
- **Drittland:** Ja → SCCs
- **AVV:** vorhanden, vom Inhaber abzuschließen falls noch nicht
- **Code-Referenz:** `services/netlify_service.py`, `routers/projects.py` (Deploy-Endpoints)

#### A4.7 Google Fonts (im Frontend)

- **⚠️ KRITISCH:** Im aktuellen `kompagnon/frontend/public/index.html` werden Google Fonts direkt von `fonts.googleapis.com` und `fonts.gstatic.com` geladen.
- **Problem:** LG München I, Urteil v. 20.01.2022, Az. 3 O 17493/20 — dynamisches Einbetten von Google Fonts ohne Einwilligung = DSGVO-Verstoß, Abmahnrisiko
- **Lösung:** Fonts **lokal hosten** (per `npm install @fontsource/...`) oder via Render-CDN ausliefern
- **Aktion erforderlich:** VOR Live-Schaltung der Datenschutzerklärung beheben

#### A4.8 Screenshot-Services (thum.io, microlink)

- **Zweck:** Erzeugung von Website-Vorschau-Screenshots im Audit / Mockup
- **Sitz:** beide USA
- **Übermittelte Daten:** URL der Zielseite
- **Drittland:** USA
- **Code-Referenz:** `routers/audit.py`, `routers/website_mockup.py` (laut grep)
- **Aktion:** Prüfen, ob beide noch aktiv genutzt werden — falls ja, in DSE listen

#### A4.9 Trackdesk (Affiliate-Tracking)

- **Zweck:** Webhook-Empfänger für Affiliate-Conversions
- **Sitz:** Trackdesk s.r.o. (Tschechien, EU)
- **Code-Referenz:** `routers/webhooks_trackdesk.py`
- **Aktion:** Prüfen, ob Affiliate-Programm aktiv läuft — falls nein, ggf. Endpoint deaktivieren

#### A4.10 GitHub / git Hosting (Quellcode)

- Speichert keine Endkunden-Daten (Code only) → DSGVO **nicht relevant** für DSE, aber AVV mit GitHub Inc. existiert nicht für Anwendungs-Daten — nur für Repos.

### A5. Verarbeitete Datenkategorien (DB-Schema-Aufschlüsselung)

#### A5.1 Login-/Account-Daten — Tabelle `users`

- Vorname, Nachname, E-Mail, Passwort (gehasht mit bcrypt, **nicht** im Klartext)
- Rolle (admin, auditor, nutzer, kunde, superadmin)
- 2FA-TOTP-Secret (verschlüsselt, optional aktivierbar)
- Letzter Login, Session-Tokens (JWT)
- Code: `database.py:445` (`User`-Klasse), `auth.py`

#### A5.2 Lead-Daten — Tabelle `leads` (umfangreichster Datensatz)

| Feld | Beispiel | Sensibilität |
|---|---|---|
| company_name, contact_name | Mustermann GmbH, Max Mustermann | Standard |
| phone, mobile, email | +49…, max@… | Standard |
| website_url, screenshot | URL + Screenshot | Standard |
| street, house_number, postal_code, city | Postanschrift | Standard |
| legal_form, vat_id, register_number, register_court | Firmenrechtl. | Öffentlich, aber strukturiert gespeichert |
| ceo_first_name, ceo_last_name, geschaeftsfuehrer | Geschäftsführer-Name | Personenbezogen |
| pagespeed_*, audit-Scores | technische Metriken | Standard |
| brand_logo_url, brand_colors, brand_fonts | Brand-Material | Standard |
| ga_status, ga_measurement_id | Google-Analytics-ID | Standard |
| lead_source, status, notes | Sales-Daten | **Intern**, kein Kundenzugriff |
| customer_token | Token für Kundenportal-Zugang | Geheim, nicht öffentlich |

Code-Referenz: `database.py:54–141`

#### A5.3 Projekt-Daten — Tabelle `projects`

- Verknüpft mit Lead, plus: Vertragsdaten (`fixed_price`, `hourly_rate`), Phasen-Status (1–7), Stripe-Subscription-IDs, Netlify-Deploy-Daten, Audit-Ergebnisse, Screenshots before/after

#### A5.4 Kundendaten — Tabelle `customers`

- CMS-Zugangsdaten (URL, Username, **Passwort verschlüsselt** in `cms_password_encrypted`)
- Touchpoint-Tracking, Upsell-Status

#### A5.5 Kommunikationslog — Tabelle `communications`

- E-Mail-/Anruf-/Meeting-Protokolle pro Projekt
- Subject, Body (max. 500 Zeichen), Richtung, Channel, Zeitpunkt, ob KI-generiert

#### A5.6 Audit-Ergebnisse — Tabelle `audit_results`

- **Hinweis:** Speichert Bewertungen **fremder** Websites (Lead-Akquise → wir scannen Websites von Interessenten ohne deren expliziten Auftrag)
- 30+ Bewertungs-Felder (rc_*, tp_*, bf_*, si_*, se_*, ux_*)
- Rechtsgrundlage hier strittig — siehe A6.4

#### A5.7 Newsletter-Daten — Tabellen `newsletter_lists`, `newsletter_contacts`

- E-Mail, Vor-/Nachname, Listen-Zugehörigkeit, Brevo-IDs

#### A5.8 Zeit- & Aktivitätstracking

- `time_tracking` — wer hat wie viele Stunden geloggt (interne Mitarbeiterdaten — § 26 BDSG zu prüfen)
- `automation_log` — KI-/Automation-Ausführungen

#### A5.9 GEO-Analysen — Tabelle `geo_analyses`

- AI-Sichtbarkeits-Analyse für Kundensites, Stripe-Subscription-Daten

#### A5.10 Akademie / Lernfortschritt

- `academy_*` Tabellen — Kursfortschritt, Quiz-Antworten, Zertifikate je User

### A6. Rechtsgrundlagen (Art. 6 DSGVO)

| Verarbeitung | Rechtsgrundlage | Art. |
|---|---|---|
| Account-Anlage / Login | Vertragserfüllung | 6 (1) b |
| Auftragsabwicklung Projekt | Vertragserfüllung | 6 (1) b |
| Stripe-Zahlungen | Vertragserfüllung | 6 (1) b |
| Newsletter-Versand | Einwilligung (Double-Opt-In) | 6 (1) a |
| Transaktionsmails (Phasen, Audit-fertig) | Vertragserfüllung | 6 (1) b |
| Lead-Akquise (Erstkontakt) | Berechtigtes Interesse / Einwilligung | 6 (1) f / 6 (1) a |
| Audit fremder Websites (Pre-Sales) | **Strittig — siehe A6.4** | – |
| 2FA / Auth-Logs | Berechtigtes Interesse (Sicherheit) | 6 (1) f |
| Server-Logs | Berechtigtes Interesse (IT-Sicherheit) | 6 (1) f |
| KI-Verarbeitung (Anthropic) | Vertragserfüllung + AVV | 6 (1) b + 28 |
| Pflicht-Aufbewahrung (Steuer / HGB) | Rechtliche Verpflichtung | 6 (1) c |
| Geplant: Umami-Tracking | Berechtigtes Interesse / Einwilligung | 6 (1) f / 6 (1) a |

#### A6.4 Pre-Sales-Audit fremder Websites — RECHTLICH PRÜFEN

Das System scannt im Akquiseprozess Websites von Interessenten, die noch kein Vertragsverhältnis haben (`audit_results` mit `lead_id`, ohne Kundenstatus). Drei Bewertungen denkbar:

1. **Public-Web-Argument:** Inhalte sind öffentlich, keine personenbezogenen Daten betroffen → ggf. zulässig nach Art. 6 (1) f. Für Einzelunternehmer/Selbstständige mit personenbeziehbarer Domain (`max-mustermann.de`) jedoch personenbezogen.
2. **Erstkontakt-Argument:** Bei Erstkontakt mit Kontaktangebot kann berechtigtes Interesse greifen — aber Interessenabwägung dokumentieren.
3. **Sicherer Weg:** Audit erst NACH Erstkontakt + Einwilligung des Lead durchführen.

→ **Mit Anwalt klären:** ob Pre-Sales-Audit ohne Einwilligung überhaupt zulässig ist, oder ob Audit erst nach erstem aktiven Kontakt durch den Lead (Formular-Submit) gestartet werden darf.

### A7. Speicherdauern (technisch im Code festzulegen)

| Datenkategorie | Empfohlene Frist | Begründung |
|---|---|---|
| User-Account (aktiv) | bis zur Kontolöschung | Vertrag |
| User-Account (inaktiv > 24 Mo) | Anonymisierung empfohlen | Datenminimierung |
| Lead (kein Vertrag zustande gekommen) | 12 Monate ab letztem Kontakt, dann Löschung | DSGVO Art. 5 (1) e |
| Projekt-Daten (Vertrag erfüllt) | 10 Jahre (HGB § 257, AO § 147) | Steuerrecht |
| Rechnungen / Stripe-Daten | 10 Jahre | Steuerrecht |
| E-Mail-Kommunikation | 6 Jahre (geschäftlicher Schriftverkehr, HGB) | Handelsrecht |
| Audit-Ergebnisse fremder Sites | 90 Tage (wenn ohne Kundenvertrag) | Datenminimierung |
| Newsletter-Anmeldung | bis Abmeldung + 3 Jahre Beleg | Nachweis Einwilligung |
| Server-Logs | 7–14 Tage | IT-Sicherheit |
| Session-Tokens (JWT) | gemäß Token-Lifetime (vmtl. 24 h–7 Tage — `auth.py` prüfen) | Sicherheit |
| Anthropic-Übermittlung | 30 Tage (laut Anthropic) | Vertraglich |

**Aktion erforderlich:** Automatische Löschroutinen implementieren (Cron-Job in `automations/scheduler.py`), die Daten nach Frist löschen. Aktuell fehlt: keine `delete_after_X_days`-Logik im Code gefunden.

### A8. Empfänger-Kategorien (für DSE-Text)

- IT-Dienstleister (Render, Netlify, Brevo, Stripe, Anthropic, Google, Trackdesk) — siehe A4
- Steuerberater (auf Anforderung)
- Behörden bei rechtlicher Verpflichtung
- Bei Verkauf des Unternehmens: Erwerber

### A9. Drittlands-Übermittlungen

| Anbieter | Land | Schutzmechanismus |
|---|---|---|
| Anthropic | USA | SCCs + Anthropic DPA |
| Stripe | USA | SCCs + Stripe DPA + EU-US Data Privacy Framework |
| Google PageSpeed | USA | SCCs + Google DPA + EU-US DPF |
| Google Fonts (aktuell extern) | USA | **siehe A4.7 — beheben!** |
| Netlify | USA | SCCs + Netlify DPA + EU-US DPF |
| thum.io / microlink | USA | SCCs erforderlich, **Status prüfen** |

### A10. Cookies / LocalStorage

| Speichertyp | Schlüssel | Inhalt | Zweck | Dauer |
|---|---|---|---|---|
| LocalStorage | `kompagnon_token` | JWT | Auth-Sitzung | bis manuell oder Token-Ablauf |
| LocalStorage | weitere `kompagnon_*` | UI-State | UX | bis manuell |
| Cookies | – | – | Aktuell keine Tracking-Cookies | – |
| Geplant Umami | – | keine Cookies (cookie-less) | Analytics | – |

→ **Aktuell vermutlich KEIN Cookie-Banner-Pflicht**, da nur funktional notwendiges LocalStorage verwendet wird (Login). Mit Einführung von Analytics oder Marketing-Pixeln wird Banner Pflicht (TTDSG § 25).

### A11. Betroffenenrechte (Standard-Klauseln, müssen aufgeführt werden)

- Auskunft (Art. 15 DSGVO)
- Berichtigung (Art. 16)
- Löschung / „Recht auf Vergessenwerden" (Art. 17)
- Einschränkung (Art. 18)
- Datenübertragbarkeit (Art. 20)
- Widerspruch (Art. 21) — insbesondere bei Direktwerbung
- Widerruf einer Einwilligung (Art. 7 (3))
- Beschwerde bei der Aufsichtsbehörde — zuständig: Landesdatenschutzbehörde des Firmensitzes

**Aktion:** Im KAS einen DSGVO-Workflow implementieren („Daten exportieren" + „Account löschen") — aktuell **nicht vorhanden** im Code.

### A12. Datensicherheit (technische Maßnahmen — bereits umgesetzt)

- TLS-Verschlüsselung (Render erzwingt HTTPS)
- Passwort-Hashing: bcrypt v4.0.1 (`passlib`)
- 2FA-TOTP optional aktivierbar (`pyotp`)
- JWT mit Signatur (`SECRET_KEY` Env-Var)
- CMS-Passwörter verschlüsselt (`cms_password_encrypted`)
- CORS auf explizite Origins beschränkt (kein `*`)
- Stripe-Webhook-Signaturprüfung (`STRIPE_WEBHOOK_SECRET_GEO`)
- DB-Backups: Render-Standard (täglich, 7 Tage)
- Render Frankfurt = EU-Datenresidenz

**Lücken (Aktion empfohlen):**
- Rate-Limiting auf Login-Endpoint prüfen
- Brute-Force-Protection / Captcha am Login
- Audit-Trail für Admin-Zugriffe
- Verschlüsselung der DB at rest (Render bietet, prüfen)
- Penetration-Test vor Go-Live
- ISO 27001 / TISAX nicht erforderlich, aber TOM-Dokumentation Pflicht (Art. 32 DSGVO)

### A13. Pflicht-Inhalte einer DSGVO-Datenschutzerklärung (Checkliste)

- [ ] Name + Anschrift Verantwortlicher (A1)
- [ ] DSB-Kontaktdaten oder Hinweis, dass keiner bestellt (A2)
- [ ] Zwecke + Rechtsgrundlagen jeder Verarbeitung (A6)
- [ ] Empfänger-Kategorien (A8)
- [ ] Drittlands-Transfers + Schutzmechanismen (A9)
- [ ] Speicherdauern oder Kriterien dafür (A7)
- [ ] Betroffenenrechte (A11)
- [ ] Beschwerderecht bei Aufsichtsbehörde
- [ ] Widerrufsrecht bei Einwilligung
- [ ] Hinweis automatisierte Entscheidungsfindung — relevant: KI-Lead-Scoring? **(prüfen, vermutlich Profiling im Sinne Art. 22)**
- [ ] Cookie-/Tracking-Hinweise (A10)
- [ ] Stand der Datenschutzerklärung (Datum)

### A14. Spezielle Hinweise — KI-Verarbeitung (Anthropic)

Da KAS umfangreich Claude für Lead-Analyse + Content-Generierung nutzt, sollten in der DSE folgende Punkte stehen:

1. Welche Daten gehen an Anthropic (Claude)?
   - Lead-Notizen, Briefing-Antworten, Website-Texte des Leads/Kunden, Audit-Befunde
2. Profiling-Hinweis (Art. 13 (2) f / 22 DSGVO): Wenn KI-Score in Sales-Entscheidung einfließt → muss offengelegt werden, Logik beschrieben, Widerspruchsrecht gewährt
3. AI Act (ab 2026 stufenweise wirksam): Lead-Scoring könnte als „limited risk"-System einzustufen sein — Transparenz-Pflicht

---

## TEIL B — AGB (Allgemeine Geschäftsbedingungen)

### B1. Geltungsbereich

- KAS bietet Leistungen für **Unternehmer** (B2B, § 14 BGB) — keine Verbraucher (KI-/Marketing-Automation für Geschäftskunden)
- → AGB als **B2B-AGB** gestalten (keine Widerrufsbelehrung, kein 14-Tage-Widerrufsrecht für Endverbraucher), klärt aber prüfen lassen je nach Zielgruppe

### B2. Vertragsgegenstand — Leistungsspektrum

Aus Code + git log:

#### B2.1 Hauptleistung „KOMPAGNON Website-Paket"

- 7-Phasen-Prozess: Akquise → Briefing → Content → Technik → QA → Go-Live → Post-Launch
- Inkludiert (laut `database.py:154` Project + `routers/projects.py`):
  - Audit der bestehenden Kundenwebsite (PageSpeed, SEO, GEO, Compliance-Check)
  - Briefing-Wizard mit KI-Auswertung
  - KI-generierte Inhalte (Texte, Strukturen)
  - Brand-Design (Farben, Fonts, Logo-Auswertung)
  - Sitemap + Leistungsseiten-Wizard
  - Website-Erstellung in GrapesJS-Editor
  - Deploy auf Netlify mit Custom-Domain + SSL
  - Festpreis-Modell: Default 2.000 € (Field `fixed_price`)
  - Stundensatz für Zusatzleistungen: 45 €/h Default (`hourly_rate`)
  - KI-Tool-Kosten: 50 € Default (`ai_tool_costs`)
- **Aktion:** Konkrete Pakete + Preise mit dir abstimmen

#### B2.2 Add-Ons (Self-Service-Buchung)

- **GEO-Add-On** (existierend): KI-Sichtbarkeits-Monitoring + Optimierung, monatliche Stripe-Subscription
- **Analytics-Add-On** (geplant, siehe Umami-Plan): Visitor-/Ad-Performance-Tracking, monatliche Stripe-Subscription
- **Newsletter-Verwaltung** (Brevo-Integration): unklar ob Add-On oder im Paket

#### B2.3 Sonstige Leistungen (Code-belegt, vom Inhaber zu listen)

- Lead-Akquise-Service
- Akademie / Online-Kurse (`academy_*`-Tabellen)
- Wartung / Hosting nach Go-Live
- CMS-Verwaltung (`customers.cms_*`)

### B3. Vertragsabschluss

- **Online-Buchung:** Stripe-Checkout für Add-Ons (GEO, geplant Analytics) → Vertragsabschluss mit Klick „Jetzt buchen" + Zahlung
- **Hauptleistung:** vermutlich Angebot + Auftragsbestätigung außerhalb des Systems → AGB beim Vertragsabschluss zur Kenntnis geben
- **Mindestlaufzeiten + Kündigung** spezifizieren (siehe B6)

### B4. Vergütung & Zahlungsbedingungen

- **Festpreise** für Hauptleistung — laut Code Default 2.000 €
- **Subscriptions:** monatlich oder jährlich (Stripe), Vorauszahlung
- **Stundensatz** für außerhalb-Scope-Arbeiten: 45 €/h Default
- **Mahnverfahren** klären — nach 14 Tagen Erinnerung, dann Mahnung, dann Inkasso?
- **Verzugszinsen** B2B: 9 Prozentpunkte über Basiszinssatz (§ 288 (2) BGB)
- **Pauschale § 288 (5) BGB:** 40 € bei Zahlungsverzug B2B

### B5. Mitwirkungspflichten des Kunden

- Bereitstellung von Inhalten (Logo, Texte, Bilder, Brand-Material) — wenn nicht bereitgestellt: Kompagnon kann KI-generierte Inhalte verwenden
- Freigabe-Prozesse: Phase 5 (QA) erfordert Kundenfreigabe (`customer_approved_at` im Code)
- DNS-Konfiguration durch Kunden bei Custom-Domain (siehe `netlify-prozess.md` Schritt 4)
- Mitteilung von Änderungswünschen rechtzeitig (Scope-Creep-Klausel — `scope_creep_flags` im Code)

### B6. Vertragsdauer + Kündigung

#### B6.1 Hauptleistung (Projekt)

- Endet mit Go-Live + Post-Launch-Phase (Phase 7)
- Ggf. Anschlusswartung als separater Vertrag

#### B6.2 Subscriptions (Add-Ons)

- Monatliche Subscription mit monatlicher Kündigungsfrist? Oder jährliche Bindung?
- Aktion: pro Add-On festlegen
- Jederzeit kündbar zum Ende des Abrechnungszeitraums (Stripe-Standard, im Code prüfen)

#### B6.3 Außerordentliche Kündigung

- Beidseitig bei wichtigem Grund (§ 314 BGB)
- KAS-seitig: bei Zahlungsverzug, Missbrauch, Verstoß gegen TOS

### B7. Nutzungsrechte

#### B7.1 Vom Kunden zu Kompagnon übertragen

- Nutzung von Logos / Markenmaterial des Kunden für Erbringung der Leistung
- Veröffentlichung des Kundenprojekts als Referenz (mit Zustimmung) — opt-in/out

#### B7.2 Von Kompagnon zum Kunden

- **Wichtig**: Wem gehören die finalen Website-Inhalte?
  - Empfehlung: einfaches, nicht-exklusives Nutzungsrecht zum Betrieb der Website nach vollständiger Bezahlung
  - GrapesJS-Templates: Nutzungsrecht beim Kunden
  - KI-generierte Inhalte: bei Kunden, sofern nichts anderes vereinbart
- Bei Vertragsende: Export-Möglichkeit + Datenmitnahme

#### B7.3 KI-Inhalte

- Hinweis auf urheberrechtliche Unsicherheit von KI-Generated-Content
- Kunde haftet für Veröffentlichung — Kompagnon prüft Plagiate (QA-Agent), kann aber keine 100 %-Garantie geben

### B8. Gewährleistung & Haftung

#### B8.1 Gewährleistung

- B2B: 1 Jahr (§ 438 BGB analog für Werkvertrag) — bei Software ggf. abkürzbar
- Mängelrüge in angemessener Frist (§ 377 HGB für Kaufleute)
- Beschränkung auf Nacherfüllung (Nachbesserung / Ersatzlieferung)

#### B8.2 Haftung

- Standard-Haftungsausschluss für leichte Fahrlässigkeit
- Volle Haftung bei Vorsatz, grober Fahrlässigkeit, Verletzung Leben/Körper/Gesundheit, Kardinalpflichten
- Kardinalpflichten: vertragstypische Hauptleistung — auf vorhersehbaren typischen Schaden begrenzen
- **Empfohlene Haftungssumme:** Höhe der jeweils gezahlten Vergütung im laufenden Vertragsjahr
- **AUSSCHLUSS:** für Schäden durch KI-generierte Inhalte (Halluzinationen, falsche Aussagen) — Kunde verantwortlich für Final-Check
- **AUSSCHLUSS:** für Ausfallzeiten von Subprocessors (Render, Netlify, Stripe, Brevo, Anthropic) — Force Majeure

### B9. Verfügbarkeit / SLA

- KAS ist auf 99,5 % Verfügbarkeit optimiert (Render-Standard), aber **kein SLA** ohne separate Vereinbarung
- Wartungsfenster: Bekanntgabe X Tage vorher (z. B. „Wartung max. 4 h/Monat, sonntags")
- Subprocessors-Ausfälle (Render, Stripe, etc.) sind nicht Kompagnons Risiko

### B10. Datenschutz / AVV

- Verweis auf Datenschutzerklärung
- Auftragsverarbeitungsvertrag (AVV) mit Kunde abschließen wenn KAS personenbezogene Daten **im Auftrag des Kunden** verarbeitet (z. B. Newsletter-Versand → Kompagnon = Auftragsverarbeiter des Kunden, der Listen-Hoheit hat)
- AVV-Vorlage: Kombination der Templates von DSK / GDD / activeMind verwenden

### B11. Geheimhaltung

- Beidseitige Geheimhaltung über Geschäftsgeheimnisse
- Dauer: Vertragslaufzeit + 3 Jahre nach Ende
- Ausnahmen: öffentlich Bekanntes, gesetzlich Vorgeschriebenes

### B12. Schlussbestimmungen

- Anwendbares Recht: deutsches Recht, ausschluss UN-Kaufrecht
- Gerichtsstand: Sitz des Verantwortlichen, B2B
- Schriftformklausel
- Salvatorische Klausel
- Änderungsklausel: Änderungen mit Frist X Wochen ankündigen, Widerspruchsmöglichkeit

### B13. Widerrufsbelehrung

- Bei reinem B2B (§ 14 BGB): **NICHT erforderlich**
- Falls auch Verbraucher (Solo-Selbstständige ohne Gewerbeanmeldung könnten als Verbraucher gelten): Widerrufsbelehrung Pflicht (14 Tage)
- → mit Anwalt klären

### B14. Pflicht-Bestandteile (Checkliste)

- [ ] Vertragsgegenstand klar beschrieben (B2)
- [ ] Vergütung + MwSt-Hinweis (B4)
- [ ] Vertragsabschluss + ggf. Widerrufsbelehrung (B3, B13)
- [ ] Laufzeit + Kündigung (B6)
- [ ] Mitwirkungspflichten Kunde (B5)
- [ ] Nutzungsrechte (B7)
- [ ] Haftung + Gewährleistung (B8)
- [ ] Datenschutz-Verweis + AVV-Hinweis (B10)
- [ ] Schlussbestimmungen (B12)

---

## TEIL C — IMPRESSUM (Pflicht nach § 5 TMG / § 18 MStV)

```
Anbieter:               [Firmenname]
Anschrift:              [Vollständige Adresse]
Telefon:                [Geschäftstelefon]
E-Mail:                 [Geschäftsmail]
Vertretungsberechtigte: [Geschäftsführer]
Handelsregister:        [Amtsgericht + HRB]
USt-IdNr.:              [DE...]
Wirtschafts-ID-Nr.:     [optional]
Berufshaftpflicht:      [Versicherer + Geltungsbereich, falls beratende Tätigkeit]
Verantwortlich für      [Name + Anschrift, oft Geschäftsführer]
journalistisch-redaktionelle
Inhalte (§ 18 MStV):
EU-Streitschlichtung:   Verweis auf https://ec.europa.eu/consumers/odr/
Verbraucherschlichtung: Hinweis: nicht teilnahmebereit / -pflichtig (üblich für B2B)
```

---

## TEIL D — KONKRETE NÄCHSTE SCHRITTE (priorisiert)

| # | Aktion | Verantwortlich | Aufwand |
|---|---|---|---|
| 1 | Google Fonts lokal hosten (DSGVO-Risiko, Abmahnung) | Tech | 1 h |
| 2 | Verantwortliche-Stelle-Daten + Impressum-Felder ausfüllen | Inhaber | 30 min |
| 3 | AVVs mit allen Subprocessors abschließen (A4) | Inhaber | 1 Tag |
| 4 | Datenschutzbeauftragten-Frage klären (A2) | Inhaber + Anwalt | 1 Tag |
| 5 | Pre-Sales-Audit-Rechtsgrundlage klären (A6.4) | Anwalt | 1–2 Tage |
| 6 | DSGVO-Workflow im KAS implementieren: Daten-Export + Account-Löschung | Tech | 1–2 Tage |
| 7 | Automatische Lösch-Routinen für Lead-/Audit-Daten (A7) | Tech | 1 Tag |
| 8 | TOM-Dokumentation (Technische + Organisatorische Maßnahmen Art. 32 DSGVO) | Inhaber | 1 Tag |
| 9 | DSE + AGB + Impressum von Anwalt prüfen + finalisieren lassen | Anwalt | 2 Wochen |
| 10 | Cookie-Banner einbauen — sobald Umami / Marketing-Pixel live | Tech | 0,5 Tag |

**Gesamtaufwand bis rechtssicherer Live-Stand:** ~10–14 Werktage (parallel mit Anwaltsprüfung).

---

## TEIL E — VORLAGEN / TOOLS (Empfehlungen)

- **Generatoren** (gut für Erststand, Anwalt-Review nötig):
  - eRecht24 Premium (~70 €/Jahr) — Standard für DE-KMU
  - activeMind AG — Enterprise-Generator
  - datenschutz-generator.de (Dr. Schwenke) — kostenlos, hochwertig
- **AVV-Vorlagen:** GDD, Bitkom, DSK
- **TOM-Vorlage:** Datenschutz-Vorlage Bayerisches LDA

---

## ANHANG — Code-Pfade (für Anwalt-Review)

| Datei | Was |
|---|---|
| `kompagnon/backend/database.py` | Vollständiges Datenmodell |
| `kompagnon/backend/main.py` | Router-Registrierung, CORS, Env-Vars |
| `kompagnon/backend/auth.py` | Auth, Passwort-Hash, JWT |
| `kompagnon/backend/agents/*.py` | Anthropic-Aufrufe, Daten-Übermittlung |
| `kompagnon/backend/services/brevo_service.py` | Brevo-Integration (Newsletter) |
| `kompagnon/backend/routers/geo_payments.py` | Stripe-Integration |
| `kompagnon/backend/services/email.py` | SMTP-Versand |
| `kompagnon/backend/services/netlify_service.py` | Netlify-Deploy |
| `kompagnon/backend/routers/audit.py` | Audit fremder Websites + PageSpeed-API |
| `kompagnon/backend/routers/webhooks_trackdesk.py` | Affiliate-Tracking |
| `kompagnon/frontend/public/index.html` | Google Fonts (DSGVO-relevant) |
