# KOMPAGNON — Feature Roadmap & Produktentwicklung

> Branch: `claude/kompagnon-automation-system-FapM9`
> Zuletzt aktualisiert: April 2026

---

## ✅ Bereits implementiert

- 7-Phasen Projektautomatisierung mit APScheduler
- Website Audit Tool mit PDF-Bericht (ReportLab)
- Homepage Standard 2025 Zertifizierungsrahmen (Bronze/Silber/Gold/Platin)
- CSV Kontakt-Import mit KI-Spaltenmapping
- Lead Pipeline mit Kanban-Ansicht
- Kundenkartei mit Audit-Historie
- JWT Auth + TOTP/2FA + Rollenmanagement
- Landing Page mit BAFA-Kalkulator + Stripe Checkout
- Kundenportal mit E-Mail-Verifikation
- Google PageSpeed Integration
- Website-Crawler (Sistrix-Stil)
- Akademy — Kurse, Module, Lektionen, Quiz, Zertifikate
- Akademy Admin — Kurs- und Lektionsverwaltung
- Datei-Upload für Kunden und Admin
- Dark Mode / Light Mode Theme-System

---

## 🔴 Priorität 1 — Kritisch (nächste Sprints)

### Kunde & Zusammenarbeit
- [ ] **Projektfortschritt im Kundenportal** — Kunde sieht 7 Phasen live, weiß wo sein Projekt steht
- [ ] **Automatische Kunden-E-Mail Benachrichtigungen** — Phasenwechsel, Freigaben, Audit fertig
- [ ] **In-App Notifications** — Benachrichtigungen innerhalb der App ohne E-Mail
- [ ] **Geführter Onboarding-Flow** — Nach Kauf: Schritt-für-Schritt Einführung für neue Kunden
- [ ] **Zugangsdaten-Safe** — Verschlüsselter Bereich für Hosting- und Domain-Zugangsdaten

### Content & Redesign
- [ ] **Content-Scraper alte Website** — Alte Website automatisch auslesen, Briefing vorausfüllen ← In Arbeit
- [ ] **KI-Texterstellung aus Briefing** — Alle Website-Texte automatisch aus Briefing-Antworten generieren
- [ ] **Erinnerungs-E-Mails** — Automatisch nach 2 Tagen: "Diese Unterlagen fehlen noch"

### Technisch
- [ ] **Fix: LeadProfile.jsx Tabs** — Dateien + Akademy Tabs in richtige Datei verschieben

---

## 🟠 Priorität 2 — Wichtig (mittelfristig)

### Kunde & Zusammenarbeit
- [ ] **Nachrichten / Kommentare** — Chat oder Kommentar-Thread pro Projekt, ersetzt E-Mail
- [ ] **Vorschau-Link mit Kommentarfunktion** — Kunde kommentiert Design direkt auf der Seite
- [ ] **Digitale Abnahme** — Go-Live Bestätigung per Klick mit Zeitstempel (rechtssicher)
- [ ] **Design-Moodboard** — Kunde wählt aus Stilrichtungen, fließt ins Briefing
- [ ] **Terminplanung / Kickoff buchen** — Kalender-Integration direkt in KAS
- [ ] **Rechnungen im Kundenportal** — Zahlungshistorie, Abo-Status, Rechnungsdownload

### Automatisierung
- [ ] **Automatische QA vor Go-Live** — Crawler + Audit auf neue Website vor Livegang
- [ ] **Monatlicher Performance-Report** — Automatisch per E-Mail: PageSpeed, Rankings, Bewertungen
- [ ] **Update-Benachrichtigungen** — "WordPress-Update verfügbar" / "SSL läuft ab"
- [ ] **Upsell-Trigger** — Wenn Score unter Schwelle fällt → automatisch Verbesserungsangebot

### Daten & Analyse
- [ ] **Vergleichs-Dashboard für Kunden** — Score vs. Branchendurchschnitt in der Region
- [ ] **Revisionshistorie** — Welche Version wurde wann freigegeben, was wurde geändert
- [ ] **Bewertungsmanagement** — Übersicht welche Kunden bewertet haben, wie viele Sterne

---

## 🟡 Priorität 3 — Nice-to-have (langfristig)

### Kundenportal & UX
- [ ] **Go-Live Countdown im Kundenportal** — Kunde sieht wann es soweit ist
- [ ] **PWA / Mobile App** — Kundenportal als installierbare App mit Push-Benachrichtigungen
- [ ] **Content-Kalender** — KI schlägt vor wann Kunde was posten soll

### Interne Tools
- [ ] **Automatische Angebotserstellung aus Audit** — Ein Klick vom Ergebnis zum fertigen PDF-Angebot
- [ ] **Vorher/Nachher Vergleichsaudit** — Alten vs. neuen Stand als Verkaufsargument

---

## 🚀 Neue Produkte (Produktentwicklung)

### Tier 1 — Sofort monetarisierbar

| Produkt | Preis | Status |
|---|---|---|
| Homepage Standard Zertifizierung | 149€/Jahr | Basis vorhanden |
| Kundenportal | Im Paket | Live |
| Akademy Kunden-Bereich | 29€/Monat | In Entwicklung |

### Tier 2 — Mit geringem Aufwand

| Produkt | Preis | Status |
|---|---|---|
| Website-Monitoring (monatlich) | 19€/Monat | Crawler vorhanden |
| SEO-Monitoring + KI-Report | 39€/Monat | Audit vorhanden |
| Mitarbeiter-Akademy | Projektpreis | Akademy vorhanden |

### Tier 3 — Strategisch

| Produkt | Preis | Beschreibung |
|---|---|---|
| White-Label KAS | 99€/Monat | KAS für andere Agenturen als SaaS |
| Google Business Manager | 29€/Monat | Automatische Pflege + monatlicher Report |
| Anfragen-Manager (CRM) | 19€/Monat | Einfaches CRM speziell für Handwerker |
| KI-Assistent für Website | 49€/Monat | Chatbot qualifiziert Anfragen automatisch |
| Recruiting Landing Pages | 500€ einmalig | Fachkräfte gewinnen für Handwerker |
| Handwerk Digital Report | Lead-Magnet | Jährlicher Branchenreport aus Audit-Daten |

---

## 📦 Empfohlene Paketstruktur

| Paket | Preis | Enthält |
|---|---|---|
| **Website** | 2.000€ einmalig | Website + Audit + Zertifikat Jahr 1 |
| **Pflege** | 49€/Monat | Portal + Monitoring + Akademy Kunden |
| **Wachstum** | 99€/Monat | Alles + SEO-Monitoring + monatlicher Report |

---

## 🏗️ Technische Schulden & Verbesserungen

- [ ] Einheitliches Responsive Design auf allen Seiten (Mobile First)
- [ ] Light/Dark Mode vollständig durchgezogen (keine hardcodierten Farben)
- [ ] Loading States + Skeleton Loader überall
- [ ] Micro-Interactions + Page Transitions (iOS-Niveau)
- [ ] Alle Seiten auf volle Bildschirmbreite
- [ ] Benutzerverwaltung aus Hauptnavigation in Einstellungen verschieben (nur Admin)
- [ ] LeadProfile.jsx Tab-Navigation vereinheitlichen

---

# KOMPAGNON – Produkt-Roadmap

> Stand: April 2026  
> Webdesign-Service für deutsches Handwerk | 2.000 € netto | 14 Werktage

---

## ✅ Umgesetzt (Deployed & Live)

### Backend (FastAPI / Python)
- [x] FastAPI-Grundstruktur mit PostgreSQL (Render)
- [x] JWT-Authentifizierung + TOTP/2FA
- [x] Rollenbasierter Zugriff: Admin, Auditor, Nutzer, Kunde
- [x] OAuth-Platzhalter (Google, GitHub)
- [x] 7-Phasen-Projektautomatisierung mit APScheduler
- [x] Hintergrund-Scheduling für Langzeitaufgaben
- [x] Website Audit Tool (async) mit PageSpeed API-Integration
- [x] PDF-Berichtsgenerierung via ReportLab
- [x] CSV-Kontaktimport mit KI-gestützter Spaltenzuordnung (Claude API)
- [x] Automatisches Lead-Enrichment (Website-Scraping)
- [x] Datenbankmigrationen via run_migrations() (ALTER TABLE IF NOT EXISTS)
- [x] E-Mail-Benachrichtigungen (Test-Endpoint)
- [x] Stripe-Checkout Integration
- [x] 28+ API-Endpunkte (Leads, Projekte, Agenten, Kunden, Automatisierungen)
- [x] Seed-Skript: 54 Checklisten-Einträge

### Frontend (React)
- [x] Mobile-first Design mit Bottom-Navigation
- [x] Dashboard mit KPI-Übersicht
- [x] Lead-Pipeline mit Kanban-Ansicht
- [x] Vertriebspipeline
- [x] Domain-Import / CSV-Upload
- [x] Export-Funktion
- [x] Website Audit Seite (Async-Verarbeitung + Ergebnis-Anzeige)
- [x] Nutzerkartei (Kundenprofil + Audit-Historie)
- [x] Produktentwicklung / Roadmap-Board (Kanban)
- [x] Angebots-Tab mit Paketvergleich (Starter / KOMPAGNON / Premium)
- [x] Rollen-Management
- [x] Einstellungen
- [x] Impressum
- [x] Landing Page mit BAFA-Rechner
- [x] Vollständiges Auth-System (Login, 2FA, Logout)

### Homepage Standard 2025 Framework
- [x] 5-Stufen-Zertifizierungsrahmen (Nicht konform / Bronze / Silber / Gold / Platin)
- [x] Bewertung in 7 Kategorien (0–100 Punkte):
  - Rechtliche Compliance
  - Technische Performance
  - Hosting & Infrastruktur
  - Barrierefreiheit
  - Sicherheit & Datenschutz
  - SEO & Sichtbarkeit
  - Inhalt & Nutzererfahrung
- [x] Audit-PDF-Report für Kaltakquise
- [x] Integration als Vertriebs-Qualifizierungstool

### Print & Outreach-Materialien
- [x] DIN 5008-konformes Anschreiben-Template
- [x] A3-Faltbroschüre (Ist-Stand / Soll-Stand, Mittelfalz)
- [x] CLAUDE.md Brandeisen (Marken-Systemprompt für Claude Code)

---

## 🔄 In Entwicklung / Geplant

### Kurzfristig
- [ ] E-Mail-Versand direkt aus der App (SMTP-Integration)
- [ ] Audit-Ergebnisse direkt im Kundenprofil speichern
- [ ] Kalenderansicht für Projektphasen
- [ ] Benachrichtigungssystem (In-App)

### Mittelfristig
- [ ] Automatisierter Kaltakquise-Workflow (Audit → Anschreiben → Versand)
- [ ] Google Business Profile API-Integration
- [ ] Erweiterung des Homepage Standard auf neue Branchen
- [ ] Kundenportal (Login für Endkunden)
- [ ] Dokumenten-Upload für Kunden

### Langfristig
- [ ] KI-gestützte Textgenerierung für Websites (im Workflow integriert)
- [ ] White-Label-Version für andere Agenturen
- [ ] API für externe Tools (Zapier, Make)
- [ ] Mobile App (iOS/Android)

---

## ⚙️ Technischer Stack

| Bereich | Technologie |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | React |
| Datenbank | PostgreSQL (Render) |
| Deployment | Render.com |
| KI | Anthropic Claude (claude-sonnet-4-6) |
| PDF | ReportLab |
| Zahlungen | Stripe |
| Performance | Google PageSpeed API |
| Versionierung | GitHub (nachhaltika-arch/Claude-Code) |

---

## 🔗 Live-URLs

- **Backend**: https://claude-code-znq2.onrender.com  
- **Frontend**: https://kompagnon-frontend.onrender.com  
- **Repo**: nachhaltika-arch/Claude-Code  
- **Branch**: claude/kompagnon-automation-system-FapM9

---

*Zuletzt aktualisiert: April 2026*
