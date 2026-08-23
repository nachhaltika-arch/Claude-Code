# ORDERS — PROMPT 08
## Anrechnung G5 — die Verbindung zwischen Shop und Projekt

> ## ⚠️ Zwei Angaben in diesem Prompt sind tot (geprüft 23.08.2026)
>
> Der Prompt lässt sich so **nicht** ausführen. Beides gilt für alle acht
> Orders-Prompts, nicht nur für diesen:
>
> 1. **Der genannte Branch `claude/kompagnon-automation-system-FapM9`
>    existiert nicht** — null Treffer, weder lokal noch auf `origin`. Die
>    `claude/*`-Branches wurden am 01.05.2026 verworfen. Gearbeitet wird auf
>    **`staging`**, gemerged wird per PR nach `main` (siehe `CLAUDE.md`).
> 2. **Die genannte Backend-URL `claude-code-znq2.onrender.com` antwortet
>    nicht mehr** (503). Der Produktivdienst läuft seit dem 23.08. in
>    Frankfurt und ist unter **`api.kompagnon.group`** erreichbar.
>
> **Fachlich vorausgesetzt, aber nicht vorhanden:** Dieser Prompt verbindet
> Bestellungen mit Projekten. Eine Tabelle `orders` gibt es nicht — weder als
> Modell noch in der Datenbank. Der Bestellweg selbst ist als **[L-100]** im
> Lagebild geführt und muss vor diesem Schritt entstehen.

---

## Was dieser Schritt macht

Wer ein Workbook für 149 € oder einen Check PLUS für 249 € gekauft hat und innerhalb von sechs Monaten einen Websprint beauftragt, bekommt den Betrag vollständig angerechnet.

**Warum das automatisch laufen muss:** Eine manuell zu berücksichtigende Anrechnung wird irgendwann vergessen. Der Kunde erinnert sich immer. Und es ist genau der Moment, in dem er gerade Vertrauen fassen sollte — ein vergessener Abzug im Angebot kostet mehr als die 149 €.

Dies ist die **einzige** Verbindung zwischen dem Bestellbereich und den Projekten. Alles andere bleibt getrennt.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `nachhaltika-arch/Claude-Code` · `claude/kompagnon-automation-system-FapM9`
**Abweichung → sofort stoppen.**

---

## Schritt 1 — Diagnose

1. Wie wird ein Deal oder Projekt angelegt? Zeige mir die Route und die Stelle im Frontend.
2. Wo wird die E-Mail-Adresse des Kunden am Deal gespeichert?
3. Wie entsteht ein Angebot — im Code erzeugtes PDF oder Vorlage?
4. Gibt es bereits eine Rabatt- oder Abzugsposition im Angebotsmodell? Falls nein, muss eine geschaffen werden.

**Ändere nichts an der Deal-Logik selbst.** Wir ergänzen eine Prüfung, wir bauen den Prozessflow nicht um.

---

## Schritt 2 — Prüfroute

| Methode | Pfad | Zugriff |
|---|---|---|
| GET | `/api/shop/credit-check?email=…` | angemeldet, über `useAuth()` |

Sucht Bestellungen mit:
- passender `buyer_email` (Groß- und Kleinschreibung ignorieren, Leerzeichen entfernen)
- Status `paid` oder `delivered`
- `is_creditable` beim Produkt wahr
- `credit_valid_until` >= heute
- `credit_redeemed_deal_id` leer

Antwort: Liste mit `order_number`, `product_code`, `amount_net`, `credit_valid_until`, `days_remaining` sowie die Summe.

⚠️ **Mehrere Anrechnungen sind möglich** — jemand kann Workbook und Check PLUS gekauft haben. Das sind zusammen 398 €. Gib alle zurück und lass die Entscheidung beim Menschen, statt automatisch nur die erste zu ziehen.

⚠️ **E-Mail-Adressen normalisieren.** „Max@Betrieb.de" und „max@betrieb.de" sind derselbe Kunde. Ohne Normalisierung findet die Prüfung nichts, und der Kunde ruft an.

---

## Schritt 3 — Einlösen

| Methode | Pfad | Zugriff |
|---|---|---|
| POST | `/api/shop/credit-redeem` | angemeldet |

Eingabe: `order_number`, `deal_id`.

Prüfungen:
1. Bestellung existiert, ist anrechenbar, Frist läuft noch
2. `credit_redeemed_deal_id` ist leer — sonst 409 mit dem Hinweis, auf welchen Deal bereits angerechnet wurde
3. Deal existiert

Dann `credit_redeemed_deal_id` und `credit_redeemed_at` setzen, Vorgang protokollieren.

**Die Einlösung ist endgültig.** Eine Rücknahme erfolgt nur manuell mit Protokolleintrag — sonst entsteht ein Weg, denselben Betrag mehrfach anzurechnen.

---

## Schritt 4 — Sichtbar machen im Deal

Hier entscheidet sich, ob das Ganze etwas nützt.

1. **Beim Anlegen eines Deals** wird nach Eingabe der E-Mail-Adresse automatisch `/api/shop/credit-check` aufgerufen.
2. Gibt es eine offene Anrechnung, erscheint ein **auffälliger Hinweis**, nicht eine unscheinbare Zeile:
   > „Für diese E-Mail-Adresse liegt eine offene Anrechnung über 149 € vor (Bestellung B-2026-0007, gültig bis 12.02.2027). Bei der Angebotserstellung berücksichtigen?"
3. Bei Zustimmung wird eine Abzugsposition im Angebot angelegt: „Anrechnung Workbook (Bestellung B-2026-0007) − 149,00 €".
4. Nach Angebotsannahme wird `/api/shop/credit-redeem` aufgerufen.

Gestaltung des Hinweises mit Gelb `#FAE600` als aktivem Zustand — er muss auffallen.

---

## Schritt 5 — Ablaufwarnung

Ein Hintergrundjob, der täglich läuft (bestehenden APScheduler nutzen, keinen zweiten aufsetzen):

- Bestellungen mit `credit_valid_until` in genau 30 Tagen und noch nicht eingelöst
- Erinnerungsmail über Brevo an den Käufer
- Interne Übersicht der auslaufenden Anrechnungen

Der Job öffnet eine **eigene** `SessionLocal()` und schließt sie im `finally`. Verbindung schließen, **bevor** Brevo aufgerufen wird.

⚠️ **Diese Mail ist ein Verkaufsinstrument, kein Serviceschreiben.** „Ihre Anrechnung über 149 € verfällt in 30 Tagen" ist ein legitimer, sachlicher Anlass zur Kontaktaufnahme mit jemandem, der bereits gekauft hat — und dessen Einwilligung durch die Bestellung vorliegt. Genau dafür wurde die Anrechnung konstruiert.

---

## Schritt 6 — Verifikation

```bash
curl -s "https://claude-code-znq2.onrender.com/api/shop/credit-check?email=test@example.com" -H "Authorization: Bearer TOKEN"
curl -s "https://claude-code-znq2.onrender.com/api/shop/credit-check?email=TEST@Example.COM" -H "Authorization: Bearer TOKEN"
```
Erwartet: **beide Aufrufe liefern dasselbe Ergebnis** — die Normalisierung greift.

Doppeleinlösung testen: `credit-redeem` zweimal mit derselben Bestellung aufrufen. Erwartet: **409** beim zweiten Mal.

Fristablauf testen: `credit_valid_until` einer Testbestellung auf gestern setzen, erneut prüfen. Erwartet: leeres Ergebnis.

```sql
SELECT order_number, credit_valid_until, credit_redeemed_deal_id, credit_redeemed_at FROM orders WHERE credit_valid_until IS NOT NULL;
```

Im Browser: Deal mit der Test-E-Mail anlegen. Erwartet: Der Hinweis erscheint sichtbar, ohne dass man ihn suchen muss.

**Verbindungs-Check:** Bestellung ✅ · Prüfroute ✅ · Hinweis beim Anlegen sichtbar ✅ · Abzugsposition im Angebot ✅ · Einlösung protokolliert ✅

---

## Schritt 7 — Commit und Push

```bash
git add -A
git commit -m "Add credit redemption linking digital orders to project deals"
git push origin claude/kompagnon-automation-system-FapM9
```

---

## STOPP — Abschluss des Orders-Subsystems

Berichte:
1. Alle Verifikationsergebnisse
2. Eine Liste aller neuen Umgebungsvariablen, die auf Render gesetzt sein müssen
3. Alle verbliebenen `[[RECHTSTEXT AUSSTEHEND]]`-Markierungen
4. Alle `# TODO`-Kommentare, die in diesen acht Prompts gesetzt wurden

**Punkt 3 und 4 sind die Freigabeliste.** Solange dort etwas steht, bleibt der Shop nicht öffentlich verlinkt.
