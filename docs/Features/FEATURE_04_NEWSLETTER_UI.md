# FEATURE 04: Newsletter im HubSpot-Stil

**Was hier entsteht:** Aus der jetzigen Kampagnenliste wird ein geführter Ablauf
**Inhalt → Empfänger → Prüfen & Senden**, mit Drag-&-Drop-Editor, Vorschau,
Testversand, A/B-Betreffzeile und einer Ergebnisseite nach dem Versand.

**Repo:** nachhaltika-arch/Claude-Code · **Branch:** main
**Prompts:** 3 · **Voraussetzung:** Feature 00 ist deployed

---

## Prompt 1 von 3 — Backend-Erweiterungen

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

ZIEL: backend/routers/newsletter.py erweitern. Bestehende Endpunkte NICHT umbenennen.

DATENBANK — Spalten ergänzen (Migration im Projektmuster):
  newsletters:  preheader TEXT, design_json JSONB DEFAULT '{}',
                ab_test JSONB DEFAULT '{}',   -- {"enabled":true,"subject_b":"...","split":50}
                winner_variant TEXT
  newsletter_lists: is_dynamic BOOLEAN DEFAULT false,
                    filter_rules JSONB DEFAULT '{}'

NEUE ENDPUNKTE
  POST /campaigns/{id}/test-send   Body: recipients[] (max 5)
       → schickt über BrevoService.send_transactional_email eine Testmail,
         Betreff mit Präfix "[TEST] "
  POST /campaigns/{id}/preview     → rendert html_content mit Beispieldaten
                                     über render_tokens, gibt HTML zurück
  GET  /campaigns/{id}/report      → erweiterte Statistik aus Brevo:
         gesendet, zugestellt, geöffnet, geklickt, Bounces, Abmeldungen,
         Spam-Meldungen, dazu Öffnungs- und Klickrate als Prozentwerte
  POST /lists/{id}/preview-dynamic Body: filter_rules
       → gibt Anzahl passender Kontakte zurück, ohne zu speichern
  GET  /tokens                     → AVAILABLE_TOKENS aus email_personalization

ANPASSUNG send_campaign
  - Vor dem Versand prüfen: alle Empfänger der gewählten Listen müssen in
    contact_consents status='confirmed' haben ODER die Kampagne ist als
    consent_basis='bestandskunde' markiert. Andernfalls 400 mit Klartext:
    "X Empfänger ohne dokumentierte Einwilligung. Versand blockiert."
  - Abmeldelink über append_unsubscribe automatisch anhängen, falls nicht vorhanden.

  git add -A
  git commit -m "feat: newsletter test send, preview, extended report and consent check"
  git push origin main
```

**Danach:** Backend deployen.

---

## Prompt 2 von 3 — Drei-Schritt-Assistent und Editor

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

VORAB: Prüfe, ob react-email-editor (Unlayer) bereits in frontend/package.json steht.
Falls nicht: npm install react-email-editor

ZIEL: Neue Datei frontend/src/components/NewsletterEditor.tsx —
ein Assistent mit drei Schritten und Fortschrittsanzeige oben.

SCHRITT 1 "Inhalt"
- Felder: interner Name, Betreffzeile, Preheader
- Umschalter "A/B-Test Betreffzeile": zweites Betrefffeld + Schieberegler für die
  Aufteilung in Prozent
- Unlayer-Editor als Hauptfläche; design_json und die erzeugte HTML beim Speichern
  beide an PATCH /api/newsletter/campaigns/{id} senden
- Startvorlage im KOMPAGNON-Design: Kopfbereich Dunkelteal #004F59 mit Logo,
  Fließtext Noto Sans, Buttons Teal #008EAA, Akzentlinien Gelb #FAE600,
  Fußzeile mit Impressum und Abmeldelink
- Seitenleiste "Platzhalter einfügen" aus GET /api/newsletter/tokens

SCHRITT 2 "Empfänger"
- Mehrfachauswahl der Listen mit Kontaktanzahl je Liste
- Live-Anzeige "Erreicht X Empfänger" (Überschneidungen abgezogen)
- Warnhinweis in Rot, wenn Empfänger ohne bestätigte Einwilligung dabei sind
- Auswahl der Einwilligungsgrundlage wie in Feature 03

SCHRITT 3 "Prüfen & Senden"
- Vorschau-Umschalter Desktop / Mobil (Rahmenbreite 375px) über POST /preview
- Prüfliste mit grünen Haken: Betreff gesetzt, Absender verifiziert,
  Abmeldelink vorhanden, mindestens eine Liste gewählt, Einwilligung geklärt
- Testversand an bis zu 5 Adressen
- Auswahl: Sofort senden oder Termin planen (Datum + Uhrzeit)
- Sende-Button erst aktiv, wenn alle Haken grün sind

KEINE localStorage- oder sessionStorage-Aufrufe verwenden.

  git add -A
  git commit -m "feat: three-step newsletter wizard with drag and drop editor"
  git push origin main
```

**Danach:** Frontend deployen.

---

## Prompt 3 von 3 — Übersicht und Ergebnisseite

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

ZIEL: frontend/src/components/Newsletter.tsx überarbeiten.

ÜBERSICHT (Tab "Kampagnen")
- Kennzahlenkarten oben behalten, ergänzen um "Abmelderate"
- Kampagnen als Karten statt reiner Tabelle: Vorschaubild links (aus design_json
  gerenderte Miniatur oder Platzhalter), Name, Betreff, Status-Chip,
  Empfängerzahl, bei gesendeten zusätzlich Öffnungs- und Klickrate als Balken
- Filterleiste: Alle / Entwurf / Geplant / Gesendet mit Anzahl je Filter
- Aktionen je Karte: Bearbeiten, Duplizieren, Bericht, Löschen

TAB "KONTAKTLISTEN"
- Umschalter beim Anlegen: Statische Liste oder Dynamische Liste
- Bei dynamisch: einfacher Regelbauer (Feld / Operator / Wert, mehrere Regeln
  mit UND-Verknüpfung), Live-Vorschau der Trefferzahl über POST /lists/{id}/preview-dynamic
- Spalte "Bestätigte Einwilligungen" je Liste

NEUE DATEI frontend/src/components/NewsletterReport.tsx
- Kopfbereich: Kampagnenname, Versanddatum, Empfängerzahl
- Sechs Kennzahlenkarten: Zugestellt, Geöffnet, Geklickt, Bounces,
  Abmeldungen, Spam-Meldungen — jeweils absolut und in Prozent
- Bei A/B-Test: Variante A gegen B nebeneinander, Gewinner hervorgehoben
- Balkendiagramm der meistgeklickten Links (recharts, falls vorhanden)
- Button "Als Vorlage speichern" → legt Eintrag in email_templates an

  git add -A
  git commit -m "feat: newsletter overview cards, dynamic lists and campaign report"
  git push origin main
```

**Danach:** Frontend deployen.
