# BUCH-12 — Bestandsfehler: Fix-Report

## Warum das VOR dem Buchprojekt kommt

Bei der Analyse des bestehenden Codes sind fünf Fehler aufgefallen, die das Buchprojekt
direkt betreffen. Vier davon sind stille Fehler — sie erzeugen keine Fehlermeldung,
sondern falsches Verhalten.

**Diese Datei ist bewusst als Zweiter in der Reihenfolge eingeplant** (direkt nach
`BUCH-01`), weil zwei der Fehler sonst in das neue Buchprodukt hineinwachsen.

---

## Die fünf Befunde

### FIX-1 — Falscher Steuersatz als Standard · **hoch**

**Datei:** `frontend/src/pages/ProductEditor.jsx`
**Befund:** `product.tax_rate ?? 19` — Standardwert 19 %.
**Warum das falsch ist:** Für Bücher (gedruckt *und* als PDF) gilt in Deutschland der
ermäßigte Satz von 7 %. Wer ein Buchprodukt anlegt und das Feld nicht bewusst ändert,
verkauft mit falschem Steuerausweis.
**Sichtbarkeit:** Null. Es funktioniert alles, die Buchhaltung stimmt nur nicht.
**Fix:** Steuersatz-Auswahl statt freies Feld, mit den drei gültigen deutschen Sätzen
(19 % / 7 % / 0 %) und einem Hinweistext beim ermäßigten Satz.

---

### FIX-2 — Veraltete Jahreszahl im Audit-Report · **hoch**

**Datei:** `frontend/src/components/AuditReport.jsx`
**Befund:** Im Warnbanner steht fest verdrahtet „Homepage Standard **2025**".
**Warum das falsch ist:** Wir haben August 2026. Jeder Kunde, der einen Audit-Bericht
bekommt, liest eine ein Jahr alte Standardbezeichnung. Sobald das Buch mit der Version
2026.1 erscheint, widersprechen sich Buch und Bericht offen.
**Fix:** Die Version aus `shared/homepage-standard.json` (aus `BUCH-01`) laden, nicht
hart schreiben.

---

### FIX-3 — Vier Funktionen als „Bald verfügbar" markiert, obwohl vorhanden · **mittel**

**Datei:** `frontend/src/pages/MassExport.jsx`
**Befund:** Die Kachel „Audit-Bericht PDF" trägt das Etikett „Bald verfügbar" — der
Endpunkt `/api/audit/{id}/pdf` existiert und wird in `AuditHistory.jsx` und
`AuditTool.jsx` produktiv verwendet.
**Warum das zählt:** Du bietest eine Funktion nicht an, die du hast. Das ist verschenkter
Nutzen — und es lässt das Produkt unfertiger wirken, als es ist. Bei einem Werkzeug, das
du Kunden zeigst, ist das ein Verkaufsproblem.
**Fix:** Kachel aktivieren und mit dem bestehenden Endpunkt verdrahten. Die anderen fünf
Kacheln prüfen: Was davon existiert ebenfalls schon?

---

### FIX-4 — Kein Widerrufsverzicht im bestehenden Checkout · **hoch**

**Datei:** `frontend/src/pages/Checkout.jsx`
**Befund:** Das Formular erfasst Name, Firma, Website, E-Mail, Telefon, Nachricht.
Es fehlt jede Zustimmung zum sofortigen Leistungsbeginn.
**Warum das falsch ist:** Bei Dienstleistungen, die innerhalb der Widerrufsfrist
beginnen, brauchst du dieselbe Zustimmung wie beim PDF (§ 356 Abs. 4 BGB). Ohne sie
kannst du bei einem Widerruf keinen Wertersatz für bereits erbrachte Leistung verlangen.
**Fix:** Pflicht-Checkbox mit Zeitstempel, analog zur Buch-Lösung.

---

### FIX-5 — Score-Schwellen an drei Stellen dupliziert · **mittel**

**Dateien:** `AuditHook.jsx`, `audit-widget.html`, `CustomerDashboard.jsx`,
`AuditHistory.jsx`, `AuditTool.jsx`
**Befund:** Die Schwellen 85/70/50/30 und die Stufennamen stehen in mindestens fünf
Dateien getrennt voneinander.
**Warum das gefährlich ist:** Sobald das Buch gedruckt ist, sind diese Zahlen in Papier
gegossen. Eine Änderung an einer Stelle, die nicht überall nachgezogen wird, macht das
Buch falsch — und du merkst es erst, wenn ein Kunde nachrechnet.
**Fix:** Aus `shared/homepage-standard.json` speisen. Für `audit-widget.html` (kein Build)
zumindest ein Prüfskript, das Abweichungen meldet.

---

## PFLICHT-CHECK

```bash
git remote -v && git branch --show-current
```

---

## PROMPTS FÜR CLAUDE CODE

**Regel: ein Fix = ein Commit = ein Push. Nach jedem Fix Render-Logs prüfen.**
Nicht bündeln.

### Prompt FIX-1

```
Führe zuerst aus: git remote -v && git branch --show-current
Erwartet: origin = nachhaltika-arch/Claude-Code, branch = claude/kompagnon-automation-system-FapM9

In frontend/src/pages/ProductEditor.jsx: Ersetze das freie Zahlenfeld fuer
tax_rate durch ein Auswahlfeld mit den Werten 19, 7 und 0.
Beschriftungen: "19 % - Regelsatz", "7 % - ermaessigt (Buecher, E-Books)",
"0 % - steuerfrei".
Standardwert bleibt 19. Unter dem Feld ein Hinweistext, der erscheint,
wenn 7 gewaehlt ist: "Ermaessigter Satz gilt u.a. fuer gedruckte Buecher und
E-Books nach Anlage 2 UStG."
Pruefe, ob das Backend tax_rate als Zahl oder String erwartet, und passe
den gesendeten Typ exakt an. Zeige mir die Backend-Feldnamen zur Kontrolle.

git add -A
git commit -m "Replace free tax rate input with valid German VAT rate selection"
git push origin claude/kompagnon-automation-system-FapM9
```

### Prompt FIX-2

```
Führe zuerst aus: git remote -v && git branch --show-current

Voraussetzung: shared/homepage-standard.json existiert (aus BUCH-01).

In frontend/src/components/AuditReport.jsx: Ersetze die fest verdrahtete
Zeichenkette "Homepage Standard 2025" durch die Version aus
shared/homepage-standard.json.
Suche im gesamten frontend/ und backend/ nach weiteren Vorkommen von "2025"
im Zusammenhang mit "Homepage Standard" und ersetze sie ebenfalls.
Zeige mir alle Fundstellen vor der Aenderung.

git add -A
git commit -m "Replace hardcoded standard year with version from shared definition"
git push origin claude/kompagnon-automation-system-FapM9
```

### Prompt FIX-3

```
Führe zuerst aus: git remote -v && git branch --show-current

In frontend/src/pages/MassExport.jsx sind sechs Kacheln mit dem Badge
"Bald verfuegbar" markiert.

SCHRITT 1: Pruefe fuer JEDE der sechs, ob im Backend bereits ein passender
Endpunkt existiert. Zeige mir eine Tabelle: Kachel | Endpunkt vorhanden? | Pfad.

SCHRITT 2: Aktiviere die Kachel "Audit-Bericht PDF" und verdrahte sie mit
/api/audit/{id}/pdf. Da hier keine Audit-ID vorliegt, baue eine Auswahl:
Lead auswaehlen -> letztes Audit dieses Leads -> PDF herunterladen.
Nutze dasselbe Download-Muster wie in AuditHistory.jsx (Blob, createObjectURL).

SCHRITT 3: Aktiviere alle weiteren Kacheln, fuer die Schritt 1 einen
vorhandenen Endpunkt ergeben hat. Lasse die uebrigen unveraendert.

git add -A
git commit -m "Enable available export functions in MassExport view"
git push origin claude/kompagnon-automation-system-FapM9
```

### Prompt FIX-4

```
Führe zuerst aus: git remote -v && git branch --show-current

In frontend/src/pages/Checkout.jsx: Ergaenze vor dem Zahlungs-Button eine
Pflicht-Checkbox:
"Ich verlange ausdruecklich, dass Sie vor Ablauf der Widerrufsfrist mit der
Ausfuehrung der beauftragten Leistung beginnen. Mir ist bekannt, dass mein
Widerrufsrecht mit vollstaendiger Vertragserfuellung erlischt."
Der Button bleibt deaktiviert, solange sie nicht gesetzt ist.
Sende den Wert und einen ISO-Zeitstempel an das Backend mit.

Pruefe zuerst, ob das Backend-Schema diese Felder aufnehmen kann. Falls nicht,
ergaenze sie im Modell und im Schema und zeige mir die noetige Migration.
Setze die Spalten nullable mit Default False, damit Bestandsdaten nicht brechen.

git add -A
git commit -m "Add mandatory withdrawal waiver consent to package checkout"
git push origin claude/kompagnon-automation-system-FapM9
```

### Prompt FIX-5

```
Führe zuerst aus: git remote -v && git branch --show-current

Voraussetzung: shared/homepage-standard.json existiert.

SCHRITT 1: Finde alle Stellen mit den Score-Schwellen 85, 70, 50, 30 und den
Stufennamen. Zeige mir eine vollstaendige Liste (Datei + Zeile).

SCHRITT 2: Lege frontend/src/utils/homepageStandard.js an, das die Definition
aus shared/homepage-standard.json importiert und exportiert:
  LEVELS, getLevel(score), getLevelColor(score), STANDARD_VERSION

SCHRITT 3: Ersetze in allen React-Dateien aus Schritt 1 die duplizierten
Definitionen durch Importe aus dieser Datei. Aendere KEIN visuelles Verhalten -
Farben und Beschriftungen muessen identisch bleiben.

SCHRITT 4: frontend/public/embed/audit-widget.html kann nicht importieren
(kein Build). Lasse die Werte dort stehen, aber erweitere
scripts/check-homepage-standard.js so, dass es auch diese Datei prueft und
Abweichungen meldet.

SCHRITT 5: npm run check:standard und npm run build ausfuehren.
Melde mir beide Ergebnisse.

git add -A
git commit -m "Centralize Homepage Standard level thresholds in shared module"
git push origin claude/kompagnon-automation-system-FapM9
```

---

## Reihenfolge und Aufwand

| Fix | Priorität | Aufwand | Voraussetzung |
|---|---|---|---|
| FIX-2 | hoch | 15 Min | BUCH-01 |
| FIX-1 | hoch | 20 Min | — |
| FIX-4 | hoch | 45 Min | Migration nötig |
| FIX-5 | mittel | 60 Min | BUCH-01 |
| FIX-3 | mittel | 60 Min | — |

**Gesamt ca. 3,5 Stunden.** FIX-2 und FIX-1 vor allem anderen — sie sind schnell und
verhindern, dass der Fehler ins Buch wandert.

---

## VERIFIKATION nach allen Fixes

```bash
npm run check:standard
npm run build
grep -rn "Homepage Standard 2025" frontend/ backend/    # muss leer sein
grep -rn "?? 19" frontend/src/pages/ProductEditor.jsx   # muss leer sein
```

Danach im Browser: ein Audit durchführen und prüfen, dass im Bericht die Version 2026.1
erscheint.

---

## ZWEI SCHRITTE VORAUS

- **FIX-5 ist die eigentliche Versicherung für das Buchprojekt.** Solange die Schwellen
  fünffach dupliziert sind, ist jede Standard-Änderung ein Risiko für ein gedrucktes
  Buch, das du nicht mehr zurückholen kannst.
- **FIX-3 lohnt eine eigene Bestandsaufnahme.** Wenn schon eine der sechs Kacheln
  fälschlich als „bald" markiert ist, sind es womöglich mehr. Die Tabelle aus Schritt 1
  ist die eigentliche Erkenntnis dieses Fixes — lies sie aufmerksam.
- **Nach diesen fünf Fixes lohnt ein systematischer Durchgang.** Es gibt weitere
  bekannte Baustellen im System (Dual-Netlify-Token, doppeltes E-Mail-Modul,
  Tracking-Injektion beim Deploy). Keine davon blockiert das Buch — aber der
  Tracking-Punkt blockiert dein Hauptprodukt und ist geschäftlich dringender als alles
  hier.
