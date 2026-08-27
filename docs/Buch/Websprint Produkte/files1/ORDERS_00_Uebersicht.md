# ORDERS-SUBSYSTEM — Prompt-Übersicht
Für: Verkauf digitaler Produkte (Workbook WB-01, Check PLUS CHK-PLU-01)
Version 1.0 · 23.08.2026

---

## Was hier gebaut wird — in einem Satz ohne Fachsprache

Ein zweiter, kleiner Bereich im System, in dem jemand ein digitales Produkt kaufen kann, ohne dass daraus ein Projekt mit Website, Domain und Prozessschritten wird.

## Warum getrennt von den bestehenden Projekten

In KAS ist ein Auftrag heute immer ein Projekt: Kunde, Domain, Aufbau, Veröffentlichung, Abnahme. Eine Workbook-Bestellung ist nichts davon. Würde man sie durch denselben Ablauf schicken, bliebe sie beim Schritt „Veröffentlichung" hängen, weil es keine Domain gibt.

Deshalb: **eine eigene Tabelle `orders`, ein eigener Ablauf.** Berührungspunkt zwischen beiden Welten ist genau einer — die Anrechnung (Garantie G5).

---

## Reihenfolge der acht Prompts

| Nr. | Inhalt | Ergebnis, das du sehen kannst |
|---|---|---|
| **01** | Datenmodell `orders` + Produktkatalog | Tabelle existiert, zwei Produkte hinterlegt |
| **02** | Backend-Schnittstelle + Produktseite im Frontend | Du siehst die Produkte im Browser |
| **03** | Stripe-Voraussetzungen prüfen, dann Bezahlvorgang | Klick auf „Kaufen" führt zur Bezahlseite |
| **04** | Zahlungsrückmeldung verarbeiten | Bestellung wechselt auf „bezahlt" |
| **05** | Rechtliche Pflichtangaben und Widerrufsverzicht | Kauf ohne Häkchen nicht möglich |
| **06** | Auslieferung: Download und Bestätigungsmail | Käufer erhält Datei |
| **07** | Rechnungsnummern und Rechnungs-PDF | Rechnung liegt bei |
| **08** | Anrechnung G5 automatisch beim Angebot | 149 € werden beim Websprint abgezogen |

**Vor Prompt 05 darf nichts live gehen.** Ein Verkauf an Verbraucher ohne Widerrufsbelehrung ist ein Rechtsverstoß, und die Widerrufsfrist läuft dann nicht ab — der Käufer kann noch nach einem Jahr widerrufen.

---

## Regeln für jede Session (in jedem Prompt wiederholt)

```
git remote -v
git branch --show-current
```
Erwartet: `nachhaltika-arch/Claude-Code` und `staging`.
Stimmt eines nicht → sofort stoppen und melden.

- Genau **ein Commit pro Prompt**, danach sofort `git push origin staging`
- Commit-Message auf Englisch
- Nach dem Push: Render-Deploy-Log prüfen, **bevor** der nächste Prompt startet
- Niemals auf `main` pushen, keine neuen Branches

⚠️ **Widerspruch in deinen Regeln.** Unter „Branch-Regel" steht `staging`, unter „Commit-Regel" steht „Branch immer main". Ich folge der Branch-Regel und pushe **nie** auf main. Bitte die Commit-Regel entsprechend korrigieren, sonst führt sie irgendwann jemanden in die Irre.

---

## Technische Vorgaben, die in allen Prompts gelten

| Regel | Grund |
|---|---|
| Token immer über `useAuth()`, nie aus `localStorage` | sonst bricht die Anmeldung an einzelnen Stellen weg |
| Adressen immer über `API_BASE_URL` aus der Konfiguration | sonst funktioniert es lokal, aber nicht auf Render |
| SQL-Parameter als `:name`, nie `%(name)s` | SQLAlchemy-Syntax, andernfalls Laufzeitfehler |
| Hintergrundaufgaben öffnen eigene `SessionLocal()` und schließen sie im `finally` | sonst laufen die Datenbankverbindungen voll |
| Datenbankverbindung schließen, **bevor** ein externer Dienst aufgerufen wird | Stripe und Brevo brauchen Sekunden; solange blockiert die Verbindung |

---

## Verbindungs-Check — der Punkt, an dem es bei dir bisher schiefging

Jeder Prompt endet mit einer Prüfkette über alle vier Ebenen:

```
Datenbank hat den Wert
        ↓
Schnittstelle liefert ihn aus
        ↓
Frontend hat eine Adresse dafür
        ↓
Etwas ist im Browser sichtbar
```

Bricht die Kette an einer Stelle, wird **nicht** der nächste Prompt gestartet. Genau diese Lücke erzeugt das Muster „Backend ist fertig, aber nichts ist zu sehen".
