# ORDERS — PROMPT 07
## Rechnungsnummern und Rechnungs-PDF


> ## ⚠️ Vor dem Ausführen: zwei Angaben sind tot (geprüft 23.08.2026)
>
> Gilt für **alle** Orders-Prompts, nicht nur für diesen:
>
> 1. **Der Branch `claude/kompagnon-automation-system-FapM9` existiert nicht** —
>    null Treffer, lokal wie auf `origin`. Die `claude/*`-Branches wurden am
>    01.05.2026 verworfen. Gearbeitet wird auf **`staging`**, gemerged wird per
>    Pull Request nach `main` (siehe `CLAUDE.md`). Der Pflicht-Check am Anfang
>    jedes Prompts schlägt sonst fehl und die Session stoppt sofort — was
>    korrekt ist, nur aus dem falschen Grund.
> 2. **`claude-code-znq2.onrender.com` antwortet nicht mehr** (503). Der
>    Produktivdienst läuft seit dem 23.08.2026 in Frankfurt unter
>    **`api.kompagnon.group`**.
>
> Der in der Übersicht notierte Widerspruch („Branch-Regel sagt `claude/…`,
> Commit-Regel sagt `main`") löst sich damit von selbst: **Beides ist falsch.**
> Richtig ist `staging`, und auf `main` wird nie direkt gepusht — die
> Branch-Protection lässt es ohnehin nicht zu.
>
> **Stand des Vorhabens:** Das Subsystem ist im Lagebild als **[L-100]**
> geführt. Eine Tabelle `orders` existiert nicht, weder als Modell noch in der
> Datenbank — der Weg ist also frei, es ist ein Anbau, kein Umbau. Stripe ist
> bereits angebunden (`stripe==15.4.0`, sieben Leser, zwei Webhooks).

---

## Was dieser Schritt macht

Jede bezahlte Bestellung erhält eine Rechnung mit einer fortlaufenden Nummer.

**Warum das kein Nebenschauplatz ist:** Die Grundsätze ordnungsmäßiger Buchführung verlangen einen lückenlosen, fortlaufenden und nachvollziehbaren Nummernkreis. Fehlt eine Nummer, muss erklärbar sein, warum. Vergibt das System dieselbe Nummer zweimal, ist die Buchführung angreifbar — im ungünstigsten Fall mit Schätzung durch das Finanzamt.

⚠️ **Zuerst zu klären, bevor Code entsteht:** Es gibt bereits einen Nummernkreis für Websprint-Rechnungen. Zwei Systeme, die unabhängig Nummern vergeben, erzeugen entweder Doppelungen oder Lücken. **Diese Frage muss der Steuerberater beantworten, nicht die Software.**

Zwei zulässige Wege:
- **Getrennte Kreise mit eigenem Präfix** — z. B. `RE-2026-…` für Projekte und `SH-2026-…` für den Shop. Beide für sich lückenlos.
- **Ein gemeinsamer Kreis** — technisch aufwendiger, weil beide Systeme dieselbe Quelle nutzen müssen.

**Empfehlung: getrennte Kreise mit Präfix.** Einfacher, robuster, steuerlich üblich. Bestätigung durch den Steuerberater trotzdem einholen.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `nachhaltika-arch/Claude-Code` · `staging`
**Abweichung → sofort stoppen.**

---

## Schritt 1 — Diagnose

1. Wie werden Rechnungsnummern für Websprint-Projekte heute vergeben? Zeige mir die Stelle.
2. Wird der Zähler in der Datenbank geführt oder aus vorhandenen Datensätzen abgeleitet?
3. Gibt es bereits eine PDF-Erzeugung im Projekt (z. B. für Auditberichte)? Falls ja: **wiederverwenden.**

**Melde das Ergebnis und warte auf meine Entscheidung zum Nummernkreis, bevor du weiterbaust.**

⚠️ Wird die Nummer aus `MAX(...)+1` über bestehende Datensätze abgeleitet, ist das bei gleichzeitigen Käufen unsicher — zwei Bestellungen können dieselbe Nummer bekommen. Falls du dieses Muster vorfindest, melde es; es ist unabhängig vom Shop ein Mangel.

---

## Schritt 2 — Nummernkreis

Eigene Tabelle `invoice_counters` mit `prefix`, `year`, `last_number`.

Vergabe innerhalb **einer** Datenbanktransaktion mit Sperre auf die Zeile (`SELECT … FOR UPDATE`), damit zwei gleichzeitige Käufe nicht dieselbe Nummer erhalten.

Format: `SH-2026-0001`, vierstellig, jährlich zurückgesetzt.

Vergabe erfolgt **erst beim Statuswechsel auf `paid`**, nicht bei `created`. Andernfalls entstehen Lücken durch abgebrochene Bezahlvorgänge — und jede Lücke muss erklärt werden.

Eine einmal vergebene Nummer wird **nie** wiederverwendet, auch bei Stornierung nicht. Eine Stornierung erzeugt eine Gutschrift mit eigener Nummer.

---

## Schritt 3 — Rechnungs-PDF

Pflichtangaben:
- Vollständiger Name und Anschrift von KOMPAGNON und Käufer
- Steuernummer oder USt-IdNr. von KOMPAGNON
- Rechnungsnummer und Rechnungsdatum
- Leistungsdatum bzw. Lieferzeitpunkt
- Bezeichnung und Menge der Leistung
- Nettobetrag, Steuersatz, Steuerbetrag, Bruttobetrag
- Hinweis auf bereits erfolgte Zahlung mit Zahlungsart und Datum

Bei Geschäftskunden mit USt-IdNr. aus dem EU-Ausland: **stoppen und melden.** Reverse-Charge-Fälle brauchen eine eigene Regelung und eine Prüfung der USt-IdNr. Das ist in dieser Ausbaustufe nicht enthalten, muss aber erkannt und abgewiesen werden, statt falsch abgerechnet zu werden.

Gestaltung in den Markenfarben: Dark Teal `#004F59`, Mid Teal `#008EAA`, Schwarz. Überschriften Noto Sans Black in Versalien.

Ablage im selben Speicher wie die Produktdateien, unter `invoices/{jahr}/{rechnungsnummer}.pdf`. **Rechnungen sind zehn Jahre aufbewahrungspflichtig** — sie dürfen nicht auf dem flüchtigen Dateisystem liegen.

---

## Schritt 4 — Zustellung und Abruf

Die Rechnung wird der Bestätigungsmail aus Prompt 06 als Anhang beigefügt. Zusätzlich:

| Methode | Pfad | Zugriff |
|---|---|---|
| GET | `/api/shop/orders/{order_number}/invoice` | Token erforderlich, wie beim Download |

Interne Übersicht für dich:

| Methode | Pfad | Zugriff |
|---|---|---|
| GET | `/api/shop/admin/orders` | angemeldet, über `useAuth()` |

Mit Filter nach Status und Zeitraum sowie Export als CSV für den Steuerberater. Frontend-Seite `/admin/bestellungen`, verlinkt in der internen Navigation.

⚠️ **Die Verlinkung nicht vergessen.** Eine Verwaltungsseite ohne Menüeintrag wird nicht benutzt und beim nächsten Umbau übersehen.

---

## Schritt 5 — Verifikation

```sql
SELECT order_number, invoice_number, status FROM orders WHERE status IN ('paid','delivered') ORDER BY created_at DESC LIMIT 5;
SELECT prefix, year, last_number FROM invoice_counters;
```

Lückentest — drei Testkäufe hintereinander:
```sql
SELECT invoice_number FROM orders WHERE invoice_number IS NOT NULL ORDER BY invoice_number;
```
Erwartet: `SH-2026-0001`, `-0002`, `-0003` ohne Lücke.

Abbruchtest: Bezahlvorgang starten und abbrechen. Erwartet: **keine** Rechnungsnummer vergeben.

PDF öffnen und alle Pflichtangaben abhaken.

Zugriffstest:
```bash
curl -s -o /dev/null -w "%{http_code}\n" "https://claude-code-znq2.onrender.com/api/shop/orders/B-2026-0001/invoice"
```
Erwartet: **403** ohne Token.

**Verbindungs-Check:** Nummernkreis ✅ · PDF ✅ · Speicher ✅ · Mailanhang ✅ · Verwaltungsseite verlinkt ✅

---

## Schritt 6 — Commit und Push

```bash
git add -A
git commit -m "Add sequential invoice numbering and invoice PDF generation"
git push origin staging
```

---

## STOPP

Berichte: gewählter Nummernkreis, Ergebnis des Lückentests, Ergebnis des Abbruchtests, ob EU-Reverse-Charge korrekt abgewiesen wird. **Warte auf Bestätigung.**
