# Eigene Anbieterkonten für KAS

> Angelegt am 2026-08-31. Entscheidung David: Die KI-Sichtbarkeitsanalyse
> läuft nicht länger über private Konten.

## Warum das kein Aufräumen ist

Vier Gründe, und keiner davon ist Ordnungsliebe:

1. **Der Schlüssel stirbt mit der Person.** Der OpenAI-Schlüssel vom 31.08.
   steht auf „Owned by: **You**". OpenAI sagt dazu wörtlich: *„If you are
   removed from the organization or project, this key will be disabled."*
   Ein Produktivdienst, der an einem persönlichen Benutzerkonto hängt, fällt
   aus, sobald mit diesem Konto etwas passiert.
2. **Rechnungen sind privat.** Umsatzsteuer und Betriebsausgabe brauchen eine
   Rechnung auf die Firma, nicht auf eine Privatperson.
3. **Der Schadensradius.** Eine Endlosschleife im Wochenlauf zieht heute eine
   **private** Karte leer. Mit eigenem Konto und Ausgabengrenze hört es bei
   einem festen Betrag auf.
4. **Übergabe.** Ein Konto auf `api@kompagnon.group` lässt sich weitergeben.
   Ein privates Google-Konto nicht, ohne alles Private mitzugeben.

## Die Anker-Adresse

`api@kompagnon.group` — neues Postfach bei IONOS (`kompagnon.group` trägt
`mx00.ionos.de` / `mx01.ionos.de`).

**Nicht** `posteingang.kompagnon.group` benutzen: Diese Subdomain zeigt per MX
auf Brevo und wird vom Inbound-Parsing verarbeitet. Eine Bestätigungsmail
eines Anbieters landete dort im Kundenposteingang statt in einem Postfach.

## Was nur David machen kann

Konten anlegen und Passwörter eingeben. Das ist alles. Vier Anmeldungen,
danach übernehme ich.

### 0 · Postfach

IONOS → E-Mail → `api@kompagnon.group` anlegen. Passwort in den Passwortmanager.

### 1 · OpenAI — `platform.openai.com`

* Registrieren mit `api@kompagnon.group`.
* **Settings → Organization**: Firmenname, Anschrift, **USt-IdNr.** eintragen.
  Ohne das kommen die Rechnungen ohne Steuerangaben und sind nachträglich
  schwer zu korrigieren.
* **Billing**: Zahlungsmethode hinterlegen und Guthaben aufladen. Ein neues
  Konto hat 0,00 $, und jeder Aufruf endet bis dahin mit **429** — genau das
  Bild, das das private Konto heute zeigt.

Danach übernehme ich: Projekt `KOMPAGNON KAS`, **Dienstkonto** statt
Benutzerschlüssel, Monatsgrenze.

### 2 · Anthropic — `console.anthropic.com`

* Registrieren mit `api@kompagnon.group`.
* Rechnungsangaben und Zahlungsmethode.

Danach ich: Workspace `KAS`, Schlüssel, Ausgabengrenze.

### 3 · Perplexity — `perplexity.ai`

* Registrieren mit `api@kompagnon.group`.
* Guthaben aufladen. **Perplexity ist Vorkasse** — das ist von sich aus eine
  harte Obergrenze, es kann nichts überzogen werden.

Danach ich: Projekt `KAS`, Schlüssel.

### 4 · Google — `accounts.google.com`

* **Kostenloses** Google-Konto, angelegt auf die **bestehende** Adresse
  `api@kompagnon.group` (Google erlaubt das über „Stattdessen meine aktuelle
  E-Mail-Adresse verwenden"). Kein Workspace nötig, solange kein zweites
  Postfach gewollt ist.
* `console.cloud.google.com` → Rechnungskonto mit Firmendaten anlegen.

Danach ich: Cloud-Projekt `kompagnon-kas`, Generative Language API
einschalten, Schlüssel, Budget.

## Ausgabengrenzen — und wo eine Grenze keine ist

Entscheidung David: harte Monatsgrenze je Anbieter. Gemessen kostet ein Kunde
bei Perplexity rund **0,19 $ im Monat** (0,00888 $ je Frage × 5 Fragen ×
4,33 Wochen). **20 € je Anbieter** ist also reichlich und fängt trotzdem jeden
Unfug ab.

| Anbieter | Art der Grenze | hält sie wirklich? |
|---|---|---|
| Perplexity | Vorkasse-Guthaben | **ja** — es ist nichts da, was überzogen werden könnte |
| OpenAI | Projekt-Budget | **ja** — der Aufruf wird abgewiesen |
| Anthropic | Ausgabengrenze | **ja** |
| Google Cloud | Budget | **nein — nur eine Warnung** |

> **Google ist die Ausnahme, und das gehört gesagt.** Ein Cloud-Budget
> *benachrichtigt*, es *stoppt nicht*. Eine harte Grenze gibt es dort nur über
> Budget → Pub/Sub → Rechnungskonto abklemmen, und das schaltet dann **alle**
> Dienste des Projekts ab. Wer bei Google „Budget gesetzt" liest und
> „abgesichert" versteht, hat dieselbe Verwechslung vor sich wie bei Render:
> Die Einstellung ist nicht der Zustand.
>
> Deshalb liegt Gemini in einem **eigenen** Cloud-Projekt. Dann trifft ein
> Abklemmen nur die KI-Sichtbarkeit und nicht nebenbei PageSpeed.

## Umstellung ohne Ausfall

Dieselbe Reihenfolge wie bei jedem Geheimniswechsel — erst der neue Wert,
dann der alte weg:

1. Neue Schlüssel auf **Staging** setzen, Probelauf
   (`tools/ki_sichtbarkeit_probe.py`) gegen einen echten Betrieb.
2. Erst wenn er durchläuft: dieselben Werte **produktiv**. Das startet den
   Dienst rund 40 Sekunden neu (L-94) und geschieht **auf Ansage**.
3. Danach die privaten Schlüssel in den privaten Konten **zurückziehen** —
   nicht bloß liegen lassen. Ein Schlüssel, den niemand benutzt und niemand
   löscht, ist genau der, den später niemand mehr zuordnen kann.

**Die vier Namen bleiben unverändert:** `OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `PERPLEXITY_API_KEY`, `GEMINI_API_KEY`. Es wechselt der
Wert, nicht die Bezeichnung — am Code ändert sich nichts.

## Am Gegenstand geprüft, nicht an der Einstellung

Fertig ist die Umstellung nicht, wenn die Werte in Render stehen, sondern wenn
der Probelauf mit den **neuen** Schlüsseln einen Betrieb findet:

    Alle Antworten wurden gelesen. Die Leser passen zur echten Form.

Und wenn `GET /api/geo/ki-anbieter` alle vier als angebunden meldet — heute
sind es drei, Claude hängt noch am privaten Schlüssel.
