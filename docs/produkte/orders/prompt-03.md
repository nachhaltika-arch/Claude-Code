# ORDERS — PROMPT 03
## Stripe-Voraussetzungen prüfen, dann Bezahlvorgang


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

Wir verbinden die Kaufen-Schaltfläche mit Stripe. Ein Klick erzeugt eine Bestellung mit Status `created` und leitet auf die Bezahlseite von Stripe weiter.

**Dieser Prompt beginnt nicht mit Code, sondern mit einer Prüfung.** In der dokumentierten Liste der Umgebungsvariablen auf Render steht kein Stripe-Schlüssel. Wenn er fehlt, ist der gesamte Rest dieses Prompts wertlos — und du merkst es erst nach dem Deploy.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `nachhaltika-arch/Claude-Code` · `staging`
**Abweichung → sofort stoppen.**

---

## Schritt 1 — Voraussetzungen prüfen, NICHTS ändern

1. Ist die Bibliothek `stripe` in den Abhängigkeiten (`requirements.txt`) eingetragen?
2. Wird irgendwo im Code `STRIPE_SECRET_KEY`, `STRIPE_API_KEY` oder Ähnliches gelesen?
3. Gibt es bereits Stripe-Code für GEO- oder Wartungs-Abonnements? Falls ja: **wiederverwenden, nicht neu bauen.** Zeige mir die Stelle.
4. Gibt es bereits einen Webhook-Endpunkt für Stripe?

**Melde das Ergebnis und STOPPE hier**, wenn eine dieser Bedingungen zutrifft:
- Keine Stripe-Bibliothek vorhanden
- Kein Stripe-Schlüssel im Code gelesen

In diesem Fall brauche ich zuerst:
- `STRIPE_SECRET_KEY` auf Render (Backend)
- `STRIPE_WEBHOOK_SECRET` auf Render (Backend, wird in Prompt 04 gebraucht)

Beides hole ich aus dem Stripe-Dashboard. **Erst danach weiter.**

---

## Schritt 2 — Bestellung anlegen und Bezahlvorgang starten

Neue Route in `routers/shop.py`:

| Methode | Pfad | Zugriff |
|---|---|---|
| POST | `/api/shop/checkout` | öffentlich |

Eingabe: `product_code`, `buyer_email`, `buyer_name`, `buyer_company` (optional), `buyer_address`, `buyer_vat_id` (optional), `is_business`, `terms_accepted`, `withdrawal_waived`.

Ablauf:
1. Produkt im Katalog nachschlagen; unbekannt oder inaktiv → 404
2. Eingaben prüfen: E-Mail plausibel, Name und Anschrift vorhanden
3. **Wenn `is_business` falsch ist und `withdrawal_waived` falsch ist → 400 mit klarer Meldung.** Ohne Verzicht darf nicht sofort ausgeliefert werden. Die vollständige rechtliche Umsetzung folgt in Prompt 05; diese Sperre wird hier bereits gesetzt, damit sie nicht vergessen wird.
4. Bestellnummer erzeugen im Format `B-JJJJ-NNNN`, fortlaufend je Jahr
5. Bestellung mit Status `created` speichern, Beträge in Cent aus dem Katalog übernehmen — **niemals aus der Anfrage**, sonst kann der Preis von außen manipuliert werden
6. `credit_valid_until` setzen: heute plus `credit_months`
7. **Datenbankverbindung schließen**
8. Stripe-Sitzung erzeugen
9. Verbindung erneut öffnen, `stripe_session_id` nachtragen, schließen
10. Weiterleitungsadresse zurückgeben

⚠️ **Schritt 5 ist sicherheitskritisch.** Wird der Betrag aus der Anfrage übernommen, kann jeder das Workbook für einen Cent kaufen.

⚠️ **Schritt 7 ist der Grund, warum die Reihenfolge so festgelegt ist.** Der Stripe-Aufruf dauert je nach Netz eine bis mehrere Sekunden. Bleibt die Datenbankverbindung währenddessen offen, sind bei gleichzeitigen Käufern die Verbindungen der Basic-256MB-Datenbank schnell erschöpft.

Angaben für die Stripe-Sitzung:
- Modus: einmalige Zahlung
- Betrag: Bruttobetrag in Cent, Währung EUR
- Erfolgsadresse: `{FRONTEND_URL}/shop/danke?order={order_number}`
- Abbruchadresse: `{FRONTEND_URL}/shop?abgebrochen=1`
- Kunden-E-Mail vorbelegen
- In den Zusatzdaten (`metadata`): `order_number` und `product_code` — darüber wird die Zahlung in Prompt 04 wieder zugeordnet

`FRONTEND_URL` kommt aus der Umgebungsvariable, wird nicht fest eingetragen.

---

## Schritt 3 — Frontend

1. Kaufen-Schaltfläche aktivieren, öffnet ein Formular für die Käuferdaten
2. Pflichtfelder: Name, E-Mail, Anschrift, Auswahl privat oder geschäftlich
3. Zwei Häkchen: AGB akzeptiert · Widerrufsverzicht (Beschriftung folgt in Prompt 05)
4. Absenden ruft `/api/shop/checkout` und leitet auf die zurückgegebene Adresse weiter
5. Fehler aus dem Backend im Formular anzeigen, nicht in der Konsole verstecken
6. Neue Seite `/shop/danke` mit Bestellnummer und dem Hinweis, dass die Bestätigung per E-Mail folgt

**Kein `<form>`-Element mit Standardabsendeverhalten** — Schaltfläche mit `onClick`.

---

## Schritt 4 — Verifikation

```bash
curl -s -X POST https://claude-code-znq2.onrender.com/api/shop/checkout \
  -H "Content-Type: application/json" \
  -d '{"product_code":"WB-01","buyer_email":"test@example.com","buyer_name":"Test","buyer_address":"Teststr. 1, 56068 Koblenz","is_business":true,"terms_accepted":true,"withdrawal_waived":true}'
```
Erwartet: JSON mit Weiterleitungsadresse.

Gegenprobe — Verbraucher ohne Verzicht:
```bash
curl -s -X POST https://claude-code-znq2.onrender.com/api/shop/checkout \
  -H "Content-Type: application/json" \
  -d '{"product_code":"WB-01","buyer_email":"test@example.com","buyer_name":"Test","buyer_address":"Teststr. 1","is_business":false,"terms_accepted":true,"withdrawal_waived":false}'
```
Erwartet: **400**, nicht 200.

Datenbank:
```sql
SELECT order_number, product_code, amount_gross, status, stripe_session_id FROM orders ORDER BY created_at DESC LIMIT 5;
```

Im Browser: Stripe-Testmodus, Testkarte `4242 4242 4242 4242`, beliebiges künftiges Datum, beliebige Prüfziffer. Nach Zahlung landest du auf `/shop/danke`.

**Der Status bleibt jetzt noch auf `created`.** Das ist richtig — die Rückmeldung kommt erst in Prompt 04.

**Verbindungs-Check:** Datenbank ✅ · Schnittstelle ✅ · Frontend ✅ · Stripe erreicht ✅

---

## Schritt 5 — Commit und Push

```bash
git add -A
git commit -m "Add Stripe checkout session creation for digital products"
git push origin staging
```

---

## STOPP

Berichte: Ergebnis der Voraussetzungsprüfung, die erzeugte Bestellnummer, ob die Gegenprobe wirklich 400 liefert. **Warte auf Bestätigung.**
