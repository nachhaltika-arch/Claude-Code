# BUCH-04 — Datenmodell für Buchbestellungen

## Warum dieser Schritt

Bevor irgendetwas verkauft werden kann, braucht die Datenbank einen Platz für
Bestellungen. Ohne diese Tabelle gehen Käufe verloren, sobald der Stripe-Webhook feuert.

Eine Buchbestellung ist etwas anderes als ein Paketkauf im bestehenden System:

- Es gibt **zwei Varianten** (PDF, Print) mit unterschiedlichem Steuersatz-Verhalten und
  völlig unterschiedlichem Ablauf danach
- Print braucht eine **Lieferanschrift** — die erfasst dein bestehender Checkout nicht
- PDF braucht einen **Auslieferungsstatus** und ein **Download-Zählwerk**
- Print braucht einen **Fulfillment-Status**, weil du die Bestellung manuell an BoD gibst

Deshalb eine eigene Tabelle statt einer Erweiterung der bestehenden Produkt-Logik.

---

## PFLICHT-CHECK

```bash
git remote -v && git branch --show-current
```

---

## PROMPT FÜR CLAUDE CODE

```
Führe zuerst aus: git remote -v && git branch --show-current
Erwartet: origin = nachhaltika-arch/Claude-Code, branch = staging
Bei Abweichung: stoppe und melde.

SCHRITT 0 — Bestand pruefen
Zeige mir die bestehenden Modelle in backend/models/ (oder dem entsprechenden Ordner)
und sag mir, wie Migrationen in diesem Projekt bisher gemacht werden (Alembic oder
create_all). Richte dich exakt nach dem bestehenden Muster. Erfinde kein neues Verfahren.

SCHRITT 1 — Modell
Lege das SQLAlchemy-Modell BookOrder an (Tabelle book_orders) mit diesen Spalten:

  id                  Integer, PK
  order_number        String(20), unique, not null      -- z.B. HS-2026-0001
  variant             String(10), not null              -- 'pdf' | 'print' | 'bundle'
  book_version        String(10), not null              -- aus shared/homepage-standard.json

  email               String(255), not null
  first_name          String(100)
  last_name           String(100)
  company             String(200)

  -- Lieferanschrift, nur bei print/bundle Pflicht
  ship_street         String(200)
  ship_zip            String(20)
  ship_city           String(100)
  ship_country        String(2), default 'DE'

  -- Preise, alle in Cent, um Rundungsfehler auszuschliessen
  price_gross_cents   Integer, not null
  tax_rate            Numeric(4,2), not null, default 7.00
  shipping_cents      Integer, not null, default 0

  -- Stripe
  stripe_session_id   String(255), unique, index
  stripe_payment_intent String(255)
  payment_status      String(20), not null, default 'pending'
                      -- pending | paid | failed | refunded

  -- Widerrufsrecht digitale Inhalte (Paragraph 356 Abs. 5 BGB)
  waiver_accepted     Boolean, not null, default False
  waiver_accepted_at  DateTime

  -- PDF-Auslieferung
  download_token      String(64), unique, index
  download_expires_at DateTime
  download_count      Integer, not null, default 0
  delivered_at        DateTime

  -- Print-Fulfillment
  fulfillment_status  String(20), default 'not_applicable'
                      -- not_applicable | queued | exported | shipped
  fulfillment_exported_at DateTime
  tracking_number     String(100)

  -- Funnel
  lead_id             Integer, FK auf leads.id, nullable, index
  utm_source          String(100)
  utm_campaign        String(100)

  created_at          DateTime, default utcnow
  updated_at          DateTime, onupdate utcnow

WICHTIG: Alle neuen Spalten sind entweder nullable oder haben einen Default.
Eine nicht-nullable Spalte ohne Default bricht die Migration auf einer Tabelle
mit Bestandsdaten. Das ist hier zwar eine neue Tabelle, aber halte die Regel ein.

SCHRITT 2 — Pydantic-Schemas
Lege die Schemas an: BookOrderCreate, BookOrderRead, BookOrderAdminRead.
BookOrderCreate validiert:
  - variant in ('pdf','print','bundle')
  - bei variant != 'pdf': ship_street, ship_zip, ship_city sind Pflicht
  - bei variant in ('pdf','bundle'): waiver_accepted muss True sein, sonst 422
  - email per EmailStr

SCHRITT 3 — Bestellnummern
Lege eine Hilfsfunktion generate_order_number() an, die HS-JJJJ-NNNN erzeugt,
fortlaufend pro Jahr, thread-sicher ueber eine DB-Abfrage auf MAX.

SCHRITT 4 — Migration
Erzeuge die Migration nach dem im Projekt ueblichen Verfahren (Schritt 0).
Fuehre sie NICHT selbst gegen die Produktions-DB aus. Zeige mir nur den Befehl.

SCHRITT 5 — Verifikation
python -c "from backend.models import BookOrder; print([c.name for c in BookOrder.__table__.columns])"
(Pfad an die Projektstruktur anpassen)

SCHRITT 6
git add -A
git commit -m "Add BookOrder model and schemas for book sales"
git push origin staging
```

---

## VERIFIKATION

Nach dem Push: **Render-Logs öffnen** und auf den Deploy warten.

| Prüfung | Erwartung |
|---|---|
| Render-Log | `Build successful`, kein Traceback |
| Render-Log | keine `sqlalchemy.exc.ProgrammingError` |
| Tabelle vorhanden | Migration ausführen, dann in der DB prüfen |

**Achtung — typischer stiller Fehler:** Wenn das Modell existiert, die Migration aber nicht
gelaufen ist, startet das Backend normal und wirft erst beim ersten Kauf einen Fehler.
Prüfe die Tabelle aktiv, verlasse dich nicht darauf, dass der Deploy grün ist.

---

## COMMIT-MESSAGE

```
Add BookOrder model and schemas for book sales
```

---

## ZWEI SCHRITTE VORAUS

- **Preise in Cent, nicht als Float.** `39.90` als Fließkommazahl führt bei Summierung zu
  Beträgen wie `39.900000000000006`. Stripe rechnet ohnehin in Cent. Das erspart dir später
  Differenzen in der Buchhaltung.
- **`waiver_accepted` ist kein Nice-to-have.** Ohne dokumentierte Zustimmung zum Verzicht
  auf das Widerrufsrecht hat jeder PDF-Käufer 14 Tage Rückgaberecht auf eine Datei, die er
  längst heruntergeladen hat. Der Zeitstempel ist dein Nachweis.
- **`lead_id` ist der eigentliche Geschäftszweck.** Sobald hier eine Verknüpfung steht,
  taucht der Buchkäufer in deiner Pipeline auf und kann bespielt werden. Ohne diese Spalte
  verkaufst du Bücher und verlierst Kunden.
