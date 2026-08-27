# ORDERS — PROMPT 04
## Zahlungsrückmeldung verarbeiten


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

Stripe meldet uns, wenn eine Zahlung tatsächlich eingegangen ist. Diese Meldung heißt Webhook. Erst sie darf den Status auf `paid` setzen.

**Warum nicht die Erfolgsseite?** Weil der Käufer die Erfolgsseite auch aufrufen kann, ohne bezahlt zu haben — die Adresse steht im Browser. Nur die Meldung von Stripe ist belastbar. Wer die Auslieferung an die Erfolgsseite hängt, verschenkt seine Produkte.

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

1. Existiert bereits ein Stripe-Webhook-Endpunkt (für GEO oder Wartung)? Falls ja: **Zeige ihn mir. Wir erweitern ihn nicht blind, sondern entscheiden gemeinsam.**
2. Ist `STRIPE_WEBHOOK_SECRET` auf Render gesetzt? Falls nein → **stoppen und melden.**
3. Gibt es in `main.py` eine Middleware, die den Anfragekörper liest oder verändert?

⚠️ **Punkt 3 ist ein klassischer Stolperstein.** Die Signaturprüfung von Stripe braucht den unveränderten Rohkörper der Anfrage. Wird er vorher von einer Middleware gelesen, schlägt die Prüfung fehl — mit einer Fehlermeldung, die nicht darauf hindeutet.

**Wenn bereits ein Webhook-Endpunkt existiert:** Stripe erlaubt mehrere getrennte Endpunkte mit je eigenem Secret. Sauberer ist ein eigener Endpunkt für den Shop, damit sich Abo- und Shop-Logik nicht vermischen. Melde mir, was du vorfindest, bevor du entscheidest.

---

## Schritt 2 — Webhook-Endpunkt

| Methode | Pfad | Zugriff |
|---|---|---|
| POST | `/api/shop/webhook` | öffentlich, aber signaturgeprüft |

Ablauf:
1. Rohkörper über `await request.body()` lesen — **nicht** über ein geparstes Modell
2. Signatur mit `STRIPE_WEBHOOK_SECRET` prüfen; ungültig → HTTP 400, sofort beenden
3. Nur auf das Ereignis `checkout.session.completed` reagieren, alles andere mit HTTP 200 quittieren und ignorieren
4. `order_number` aus den Zusatzdaten lesen, Bestellung suchen; nicht gefunden → protokollieren und HTTP 200 zurückgeben
5. **Wenn der Status bereits `paid` oder höher ist: nichts tun, HTTP 200.** Stripe stellt Meldungen bei Zweifeln erneut zu. Ohne diese Prüfung würde derselbe Kauf mehrfach verarbeitet — doppelte Rechnung, doppelte E-Mail.
6. Bezahlten Betrag mit `amount_gross` der Bestellung vergleichen. Abweichung → als Auffälligkeit protokollieren, Status **nicht** setzen
7. Status auf `paid`, `stripe_payment_intent` speichern
8. Verbindung schließen
9. Auslieferung anstoßen — die eigentliche Auslieferung kommt in Prompt 06; hier zunächst nur ein Protokolleintrag

**Immer HTTP 200 zurückgeben, außer bei ungültiger Signatur.** Ein Fehlercode veranlasst Stripe zu Wiederholungsversuchen über Tage.

---

## Schritt 3 — Statusanzeige für den Käufer

Neue Route:

| Methode | Pfad | Zugriff |
|---|---|---|
| GET | `/api/shop/orders/{order_number}/status` | öffentlich |

Gibt ausschließlich zurück: `order_number`, `status`, `product_code`.

⚠️ **Keine personenbezogenen Daten, keine Beträge, keine Anschrift.** Die Bestellnummer steht im Browserverlauf und in E-Mails; sie ist kein Geheimnis. Wer hier den vollen Datensatz ausliefert, baut eine Datenschutzlücke.

Die Seite `/shop/danke` fragt diesen Status alle 3 Sekunden ab, maximal 20-mal, und zeigt: „Zahlung wird bestätigt…" → „Zahlung eingegangen".

---

## Schritt 4 — Verifikation

Im Stripe-Dashboard (Testmodus) den Endpunkt eintragen:
`https://claude-code-znq2.onrender.com/api/shop/webhook`, Ereignis `checkout.session.completed`.

Dann einen vollständigen Testkauf durchführen.

```sql
SELECT order_number, status, stripe_payment_intent, updated_at FROM orders ORDER BY created_at DESC LIMIT 3;
```
Erwartet: Status `paid`.

Doppelzustellung testen — im Stripe-Dashboard dieselbe Meldung erneut senden:
```sql
SELECT order_number, status, updated_at FROM orders WHERE order_number = 'B-2026-XXXX';
```
Erwartet: `updated_at` hat sich **nicht** verändert.

Signaturprüfung testen:
```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://claude-code-znq2.onrender.com/api/shop/webhook -d '{}'
```
Erwartet: **400**.

**Verbindungs-Check:** Stripe ✅ · Webhook ✅ · Datenbank ✅ · Statusanzeige im Browser ✅

---

## Schritt 5 — Commit und Push

```bash
git add -A
git commit -m "Add Stripe webhook handler with signature check and idempotency"
git push origin staging
```

---

## STOPP

Berichte: Statuswechsel bestätigt, Doppelzustellung ohne Wirkung, ungültige Signatur abgewiesen. **Warte auf Bestätigung.**
