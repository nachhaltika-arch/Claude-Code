# ORDERS — PROMPT 06
## Auslieferung: Download und Bestätigungsmail


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

Nach bestätigter Zahlung erhält der Käufer eine E-Mail mit einem Download-Link, der nach begrenzter Zeit abläuft.

---

## 🔴 ARCHITEKTURENTSCHEIDUNG VOR BAUBEGINN

**Das Dateisystem auf Render ist flüchtig.** Bei jedem Deploy wird der Container neu gebaut. Alles, was in ein Verzeichnis auf dem Server gelegt wurde, ist danach weg.

Konkret: Du lädst das Workbook-PDF hoch, drei Kunden kaufen es, du deployst am nächsten Tag einen Bugfix — und alle drei Download-Links laufen ins Leere. Der Fehler tritt nicht sofort auf, sondern beim nächsten Deploy. Das ist die unangenehmste Sorte Fehler.

**Netlify ist keine Lösung.** Netlify hostet die Kundenwebsites. Eine Datei dort abzulegen bedeutet, dass sie öffentlich unter einer erratbaren Adresse liegt — verkauftes Produkt, frei abrufbar.

| Option | Vorteil | Nachteil |
|---|---|---|
| **A · Render Persistent Disk** | im bestehenden Vertrag, schnell eingerichtet | verhindert Deploys ohne Ausfallzeit, an eine Instanz gebunden, nicht skalierbar |
| **B · Objektspeicher** (Cloudflare R2, Backblaze B2, AWS S3) | dauerhaft, deploy-unabhängig, signierte Links sind eingebaut, Kosten im Centbereich | ein zusätzlicher Dienst, zwei neue Zugangsdaten |
| **C · Datei in der Datenbank** | keine neuen Dienste | bläht die 256-MB-Datenbank auf, Sicherungen werden groß und langsam — **nicht empfohlen** |

**Empfehlung: B, mit Cloudflare R2.** Kein Gebührenaufschlag für ausgehenden Datenverkehr, S3-kompatibel, signierte Links mit Ablaufzeit sind Standardfunktion. Bei zwei PDF-Dateien und wenigen hundert Downloads liegen die monatlichen Kosten praktisch bei null.

**STOPPE hier und frage mich, welche Option gewählt wird.** Erst danach weiterbauen.

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

1. Wie wird Brevo heute angesprochen? Gibt es einen zentralen Mail-Dienst oder mehrere Stellen?
2. Werden Transaktionsmails über Vorlagen in Brevo oder über Inhalte aus dem Code versendet?
3. Wie werden Hintergrundaufgaben ausgeführt (APScheduler, FastAPI-Hintergrundaufgaben)?

⚠️ Es ist bekannt, dass es **zwei parallele Mail-Wege** gibt (offene Aufgabe „Bug #2 E-Mail-Service-Konsolidierung"). Baue keinen dritten. Melde mir, was du vorfindest, und nutze den bestehenden Weg.

---

## Schritt 2 — Speicheranbindung

Nach der in der Architekturentscheidung gewählten Option.

Bei Option B: Zugangsdaten als Umgebungsvariablen (`STORAGE_ENDPOINT`, `STORAGE_BUCKET`, `STORAGE_KEY_ID`, `STORAGE_SECRET`). **Keine Schlüssel im Code, auch nicht als Rückfallwert.** Im Projekt gab es bereits einen fest eingetragenen Lizenzschlüssel als Rückfallwert; dieses Muster wird nicht wiederholt.

Ordnung im Speicher: `products/WB-01/workbook-v1.pdf`, `products/WB-01/auditbogen-v1.xlsx`.
Der Behälter ist **nicht** öffentlich lesbar.

---

## Schritt 3 — Download mit ablaufendem Link

| Methode | Pfad | Zugriff |
|---|---|---|
| GET | `/api/shop/orders/{order_number}/download` | Token erforderlich |

Ablauf:
1. Bestellung suchen; nicht gefunden → 404
2. Status muss `paid` oder `delivered` sein, sonst → 403
3. Einmal-Token aus der Anfrage prüfen — der Käufer hat kein Benutzerkonto, deshalb dient das Token als Ausweis
4. Signierten Link mit **15 Minuten** Gültigkeit erzeugen
5. Weiterleiten oder Link zurückgeben
6. Zähler `download_count` erhöhen, `delivered_at` beim ersten Mal setzen, Status auf `delivered`

Das Download-Token: zufällig, mindestens 32 Zeichen, bei der Bestellung erzeugt, in der Datenbank gespeichert, **7 Tage** gültig. Nach Ablauf kann der Käufer über einen Link in der E-Mail ein neues anfordern.

⚠️ **Warum zwei Fristen?** Der signierte Speicher-Link läuft nach 15 Minuten ab, damit er nicht weitergegeben werden kann. Das Download-Token gilt 7 Tage, damit der Käufer die Datei mehrfach abrufen kann. Nur eine Frist zu haben ist entweder unpraktisch oder unsicher.

---

## Schritt 4 — Bestätigungsmail

Wird nach dem Statuswechsel auf `paid` aus Prompt 04 ausgelöst — als Hintergrundaufgabe, **nicht** innerhalb der Webhook-Antwort. Stripe erwartet eine schnelle Antwort.

Die Hintergrundaufgabe öffnet eine **eigene** `SessionLocal()` und schließt sie im `finally`. Die Datenbankverbindung wird geschlossen, **bevor** Brevo aufgerufen wird.

Inhalt der Mail:
- Bestellnummer, Produkt, Betrag netto und brutto mit Steuersatz
- Download-Link mit Token
- Hinweis auf die Gültigkeit von 7 Tagen und die Möglichkeit der Erneuerung
- Bei anrechenbaren Produkten: Hinweis auf die Anrechnung mit konkretem Enddatum aus `credit_valid_until`
- Wortlaut der akzeptierten AGB- und Verzichtserklärung (Bausteine aus Prompt 05)
- Vollständige Anbieterkennzeichnung

Fehlgeschlagener Versand wird protokolliert und dreimal mit Abstand wiederholt. Ein Fehler darf den Bestellstatus **nicht** zurücksetzen — bezahlt bleibt bezahlt.

---

## Schritt 5 — Downloadseite

Neue Route `/shop/download/{order_number}?token=…`, öffentlich. Zeigt Produkt, Bestellnummer, Download-Schaltfläche und die Restgültigkeit. Bei abgelaufenem Token: Schaltfläche „Neuen Link anfordern", die eine neue Mail auslöst.

---

## Schritt 6 — Verifikation

```bash
curl -s -o /dev/null -w "%{http_code}\n" "https://claude-code-znq2.onrender.com/api/shop/orders/B-2026-0001/download"
curl -s -o /dev/null -w "%{http_code}\n" "https://claude-code-znq2.onrender.com/api/shop/orders/B-2026-0001/download?token=FALSCH"
```
Erwartet: **403** bzw. **403** — niemals 200.

Vollständiger Testkauf: Mail kommt an, Link führt zur Datei.

```sql
SELECT order_number, status, delivered_at, download_count FROM orders ORDER BY created_at DESC LIMIT 3;
```
Erwartet: `delivered`, Zeitstempel gesetzt, Zähler auf 1.

**Ablauftest:** Signierten Speicher-Link kopieren, 16 Minuten warten, erneut aufrufen. Erwartet: abgelehnt.

**Deploy-Test — der wichtigste:** Nach einem weiteren Deploy den Download erneut aufrufen. Er muss weiterhin funktionieren. Tut er es nicht, liegt die Datei am falschen Ort.

**Verbindungs-Check:** Speicher ✅ · Webhook löst aus ✅ · Mail zugestellt ✅ · Download funktioniert ✅ · **auch nach Deploy** ✅

---

## Schritt 7 — Commit und Push

```bash
git add -A
git commit -m "Add digital product delivery with expiring signed download links"
git push origin staging
```

---

## STOPP

Berichte: gewählte Speicheroption, Ergebnis des Ablauftests, Ergebnis des Deploy-Tests. **Warte auf Bestätigung.**
