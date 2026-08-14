# Reihenfolge aller Prompts — E-Mail-Automatisierung & Newsletter

**Wichtig:** Genau in dieser Reihenfolge abarbeiten. Jeder Schritt baut auf dem
vorherigen auf. Nach jedem Backend-Prompt zuerst auf Render **Manual Deploy** —
sonst laufen die folgenden Prompts gegen eine veraltete Datenbank.

| # | Datei | Prompt | Bereich | Deploy danach |
|---|---|---|---|---|
| 1 | FEATURE_CLAUDE_MD_REGELN | 1/1 | Repo | — |
| 2 | FEATURE_00_BREVO_FIXES | 1/1 | Backend | Backend |
| 3 | FEATURE_01_AUTOMATION_BACKEND | 1/3 Tabellen | Backend | Backend |
| 4 | FEATURE_01_AUTOMATION_BACKEND | 2/3 CRUD-API | Backend | Backend |
| 5 | FEATURE_01_AUTOMATION_BACKEND | 3/3 Aufnahme | Backend | Backend |
| 6 | FEATURE_02_AUTOMATION_ENGINE | 1/3 Ausführung | Backend | Backend |
| 7 | FEATURE_02_AUTOMATION_ENGINE | 2/3 Hintergrundjob | Backend | Backend |
| 8 | FEATURE_02_AUTOMATION_ENGINE | 3/3 Opt-in | Backend | Backend |
| 9 | FEATURE_03_CANVAS_FRONTEND | 1/3 Liste | Frontend | Frontend |
| 10 | FEATURE_03_CANVAS_FRONTEND | 2/3 Canvas | Frontend | Frontend |
| 11 | FEATURE_03_CANVAS_FRONTEND | 3/3 Panel | Frontend | Frontend |
| 12 | FEATURE_04_NEWSLETTER_UI | 1/3 Backend | Backend | Backend |
| 13 | FEATURE_04_NEWSLETTER_UI | 2/3 Assistent | Frontend | Frontend |
| 14 | FEATURE_04_NEWSLETTER_UI | 3/3 Bericht | Frontend | Frontend |
| 15 | FEATURE_05_NETLIFY_SNIPPET | 1/2 Endpunkt | Backend | Backend |
| 16 | FEATURE_05_NETLIFY_SNIPPET | 2/2 Snippet | Beides | Beides |

---

## Neue Render-Umgebungsvariablen (alle Backend-Service)

| Variable | Wann nötig | Beispiel |
|---|---|---|
| `BREVO_SENDER_NAME` | ab Schritt 2 | KOMPAGNON Communications |
| `BREVO_SENDER_EMAIL` | ab Schritt 2 | verifizierte Brevo-Adresse |
| `COMPANY_NAME` | ab Schritt 8 | KOMPAGNON Communications BP GmbH |
| `COMPANY_ADDRESS` | ab Schritt 8 | Straße, PLZ Koblenz |
| `COMPANY_IMPRINT_URL` | ab Schritt 8 | https://.../impressum |

---

## Erste Automation zum Testen (nach Schritt 11)

**Name:** Audit-Nachfassen
**Auslöser:** Audit abgeschlossen
**Einwilligung:** Einwilligung liegt vor

```
Auslöser: Audit abgeschlossen
   ↓
E-Mail senden: "Ihr Website-Check ist fertig" (mit PDF-Link)
   ↓
Warten: 3 Tage
   ↓
Wenn/Dann: E-Mail geöffnet?
   ├── Ja  → E-Mail senden: "Ihre drei größten Baustellen"
   │          ↓
   │        Warten: 4 Tage
   │          ↓
   │        Aufgabe erstellen: "Anrufen"
   └── Nein → Aufgabe erstellen: "Telefonisch nachfassen"
```

Beim Testen zuerst mit deiner eigenen E-Mail-Adresse als Kontakt arbeiten und
im Reiter „Kontakte" verfolgen, wie der Eintrag durch die Schritte wandert.

---

## Rechtlicher Merksatz

Die Engine sendet **nur**, wenn zur Empfängeradresse eine bestätigte Einwilligung
in `contact_consents` steht oder der Workflow ausdrücklich als Bestandskunden-
Kommunikation markiert ist. Das ist bewusst so gebaut. Bitte diese Prüfung nicht
später „zum Testen" herausnehmen — genau daraus entstehen Abmahnungen.
