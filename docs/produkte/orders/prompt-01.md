# ORDERS — PROMPT 01
## Datenmodell `orders` und Produktkatalog


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

## Was dieser Schritt macht (Erklärung für dich, nicht für Claude Code)

Wir legen die Ablage an, in der Bestellungen digitaler Produkte gespeichert werden — getrennt von den Projekten. Dazu kommt eine kleine Liste der verkaufbaren Produkte mit Preis und Steuersatz.

Am Ende dieses Schritts kann man noch nichts kaufen. Es existiert nur der Platz dafür. Das ist Absicht: Erst die Ablage, dann die Schnittstelle, dann die Oberfläche. Wer umgekehrt anfängt, baut eine Oberfläche, die nichts speichern kann.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet:
- origin → `https://github.com/nachhaltika-arch/Claude-Code`
- Branch → `staging`

**Stimmt eines nicht: STOPPE sofort.** Melde „Falsches Repo oder falscher Branch. Bitte prüfen." und führe nichts aus.

---

## Schritt 1 — Diagnose (nichts ändern)

Verschaffe dir zuerst ein Bild und berichte mir das Ergebnis, bevor du schreibst:

1. Wo sind die SQLAlchemy-Modelle definiert? (`models.py` oder in `main.py`?)
2. Wie werden Migrationen ausgeführt? Bestätige, ob es die Funktion `_run_migrations()` in `main.py` gibt und wie neue Tabellen dort angelegt werden.
3. Gibt es bereits eine Tabelle oder ein Modell mit dem Namen `order`, `orders`, `purchase` oder `shop`? Falls ja: **stoppen und melden.**
4. Wie ist `product_type` heute definiert — als Python-Enum, als String-Spalte oder als Datenbank-Enum?
5. Welches Format haben bestehende Primärschlüssel: UUID oder fortlaufende Zahl?

Gib mir eine kurze Zusammenfassung. Passe dich beim Schreiben an die vorgefundenen Muster an — **erfinde kein neues Muster.**

---

## Schritt 2 — Tabelle `orders` anlegen

Neue Datei `models_orders.py` (oder im bestehenden Modell-Modul, falls Schritt 1 das nahelegt).

Felder:

| Feld | Typ | Bedeutung |
|---|---|---|
| `id` | wie bestehende Primärschlüssel | |
| `order_number` | String, eindeutig | menschenlesbar, z. B. `B-2026-0001` |
| `product_code` | String | `WB-01` oder `CHK-PLU-01` |
| `buyer_email` | String, indiziert | Schlüssel für die spätere Anrechnung |
| `buyer_name` | String | |
| `buyer_company` | String, optional | |
| `buyer_address` | Text | für die Rechnung erforderlich |
| `buyer_vat_id` | String, optional | USt-IdNr. bei Geschäftskunden |
| `is_business` | Boolean | steuert Widerrufsrecht und Nettoausweis |
| `amount_net` | Integer | **in Cent**, nie Fließkomma |
| `vat_rate` | Integer | z. B. 19 |
| `amount_gross` | Integer | in Cent |
| `currency` | String, Standard `EUR` | |
| `status` | String | `created`, `paid`, `delivered`, `refunded`, `failed` |
| `stripe_session_id` | String, optional, indiziert | |
| `stripe_payment_intent` | String, optional | |
| `withdrawal_waived` | Boolean, Standard `false` | Widerrufsverzicht erteilt |
| `withdrawal_waived_at` | DateTime, optional | |
| `terms_accepted_at` | DateTime, optional | |
| `delivered_at` | DateTime, optional | |
| `invoice_number` | String, optional, eindeutig | kommt in Prompt 07 |
| `credit_valid_until` | Date, optional | Ende der Anrechnungsfrist |
| `credit_redeemed_deal_id` | Fremdschlüssel, optional | wenn die Anrechnung gezogen wurde |
| `created_at`, `updated_at` | DateTime | |

**Wichtig zu den Beträgen:** Geld wird als ganzzahliger Cent-Betrag gespeichert, nicht als Kommazahl. Fließkommazahlen erzeugen bei Steuerberechnungen Rundungsfehler, die im Rechnungswesen nicht akzeptabel sind.

**Wichtig zu `buyer_email`:** Dieses Feld ist die einzige Verbindung zur späteren Anrechnung. Es muss indiziert sein, sonst wird die Prüfung in Prompt 08 langsam.

---

## Schritt 3 — Produktkatalog

Neue Datei `shop_catalog.py` mit einer festen Liste. **Keine Datenbanktabelle** — bei zwei Produkten wäre das übertrieben, und eine Codeliste ist versionierbar und nachvollziehbar.

Je Produkt: `code`, `name`, `short_description`, `amount_net` (Cent), `vat_rate`, `is_creditable` (anrechenbar ja/nein), `credit_months`, `delivery_type` (`download` oder `appointment`), `active`.

Einträge:
- `WB-01` — Workbook „Homepage-Standard in 30 Schritten", 14900 Cent netto, 19 %, anrechenbar, 6 Monate, `download`
- `CHK-PLU-01` — Check PLUS, 24900 Cent netto, 19 %, anrechenbar, 6 Monate, `appointment`

⚠️ **Der Steuersatz für WB-01 ist noch nicht geklärt** (7 % für elektronische Publikationen gegen 19 % für digitale Werkzeuge). Setze 19 % und schreibe einen Kommentar `# TODO Steuersatz mit Steuerberater klären — siehe Datenblatt WB-01 Abschnitt 6` direkt an die Zeile.

---

## Schritt 4 — Migration

Ergänze die Migration nach dem in Schritt 1 vorgefundenen Muster. Die Migration muss mehrfach ausführbar sein, ohne Fehler zu werfen (`CREATE TABLE IF NOT EXISTS` bzw. Prüfung auf Existenz).

SQL-Parameter als `:name` schreiben, niemals `%(name)s`.

**Ändere nichts an `product_type`.** Digitale Produkte laufen bewusst nicht über die Projekt-Logik.

---

## Schritt 5 — Verifikation

```bash
python -c "from models_orders import Order; print(Order.__table__.columns.keys())"
python -c "from shop_catalog import CATALOG; print([p['code'] for p in CATALOG])"
```

Nach dem Deploy zusätzlich gegen die Datenbank prüfen:
```sql
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'orders';
```

**Verbindungs-Check für diesen Prompt:** Datenbank ✅ · Schnittstelle — kommt in Prompt 02 · Frontend — kommt in Prompt 02.

---

## Schritt 6 — Commit und Push

```bash
git add -A
git commit -m "Add orders table and digital product catalog"
git push origin staging
```

---

## STOPP

Berichte:
1. Ergebnis der Diagnose aus Schritt 1
2. Ob die Migration im Render-Log fehlerfrei durchgelaufen ist
3. Die Spaltenliste aus der Datenbankprüfung

**Warte auf meine Bestätigung, bevor Prompt 02 startet.**
