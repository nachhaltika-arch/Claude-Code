# BUCH-05 — Backend: Checkout & Stripe

## Warum dieser Schritt

Hier entsteht der Bezahlvorgang. Der Ablauf ist zweigeteilt, und das ist wichtig zu
verstehen:

```
1. Kunde klickt "Kaufen" auf der Netlify-Seite
2. Netlify-Seite ruft DEIN Backend auf: POST /api/book/checkout
3. Backend legt eine Bestellung an (Status: pending) und fragt Stripe nach einer Bezahlseite
4. Backend gibt die Stripe-URL zurück, Browser leitet dorthin weiter
5. Kunde bezahlt bei Stripe
   ─────────────────────────────────────────────────
6. Stripe ruft DEIN Backend auf: POST /api/book/webhook
7. Backend setzt Status auf paid und stößt die Auslieferung an
```

**Der entscheidende Punkt bei Schritt 6–7:** Die Bestellung wird *nicht* als bezahlt
markiert, wenn der Kunde auf der Danke-Seite landet. Sie wird als bezahlt markiert, wenn
Stripe es dem Backend bestätigt. Der Kunde kann die Danke-Seite auch aufrufen, ohne
bezahlt zu haben. Das ist die häufigste Sicherheitslücke in selbstgebauten Shops.

---

## Steuerliche Vorgabe (verbindlich)

| Produkt | Steuersatz | Rechtsgrundlage |
|---|---|---|
| Gedrucktes Buch | **7 %** | ermäßigter Satz, Anlage 2 UStG |
| E-Book / Buch-PDF | **7 %** | seit Dezember 2019 dem Printbuch gleichgestellt |
| Versandkosten | 7 % | folgen dem Steuersatz der Hauptleistung |

Das bestehende System setzt `tax_rate` per Default auf 19 (`ProductEditor.jsx`).
Für dieses Produkt ist das falsch. Der Fix am Bestandssystem ist in `BUCH-12`.

---

## PFLICHT-CHECK

```bash
git remote -v && git branch --show-current
```

---

## PROMPT FÜR CLAUDE CODE

```
Führe zuerst aus: git remote -v && git branch --show-current
Erwartet: origin = nachhaltika-arch/Claude-Code, branch = claude/kompagnon-automation-system-FapM9
Bei Abweichung: stoppe und melde.

SCHRITT 0 — Bestand pruefen
Zeige mir den bestehenden Stripe-Code (vermutlich routers/stripe.py oder
routers/payments.py). Ich will wissen: Welche Stripe-Bibliotheksversion, welches
Muster fuer Checkout-Sessions, wie wird der Webhook heute verifiziert.
Nutze exakt dasselbe Muster. Baue keinen zweiten Stripe-Client auf.

SCHRITT 1 — Preiskonfiguration
Lege backend/config/book_pricing.py an:

  BOOK_VERSION = aus shared/homepage-standard.json lesen
  TAX_RATE = Decimal("7.00")
  VARIANTS = {
    "pdf":    {"gross_cents": 3900, "shipping_cents": 0,   "label": "PDF-Ausgabe"},
    "print":  {"gross_cents": 4900, "shipping_cents": 495, "label": "Gedruckte Ausgabe"},
    "bundle": {"gross_cents": 5900, "shipping_cents": 495, "label": "Print + PDF"},
  }
Keine Preise irgendwo anders hardcoden.

SCHRITT 2 — Router
Lege backend/routers/book.py an und registriere ihn in der Haupt-App
mit prefix="/api/book", tags=["book"].

Endpunkt A: POST /api/book/checkout
  Body: BookOrderCreate
  Ablauf:
    1. Validieren (Schemas aus BUCH-04 erledigen das)
    2. Bei variant pdf oder bundle: waiver_accepted muss True sein, sonst 422
       mit klarer Meldung "Zustimmung zum sofortigen Beginn der Lieferung erforderlich"
    3. order_number erzeugen
    4. BookOrder mit payment_status='pending' speichern
    5. DB-Session SCHLIESSEN, bevor Stripe aufgerufen wird
       (Pool-Erschoepfung vermeiden - bekannte Architekturregel in diesem Projekt)
    6. Stripe Checkout Session erzeugen:
         mode='payment'
         line_items mit unit_amount aus book_pricing
         bei print/bundle zusaetzlich shipping als eigenes line_item
         customer_email
         metadata: {order_number, variant, book_version}
         success_url = FRONTEND_BOOK_URL + "/danke?order={order_number}"
         cancel_url  = FRONTEND_BOOK_URL + "/?abgebrochen=1"
         automatic_tax NICHT aktivieren; wir setzen den Steuersatz selbst ueber
         eine Stripe tax_rate mit 7 Prozent (einmalig in Stripe anlegen, ID in ENV)
    7. Neue DB-Session oeffnen, stripe_session_id speichern, schliessen
    8. Rueckgabe: {"checkout_url": ..., "order_number": ...}

Endpunkt B: POST /api/book/webhook
  1. Signatur pruefen mit STRIPE_WEBHOOK_SECRET. Bei ungueltiger Signatur: 400.
     NIEMALS ungeprueft verarbeiten.
  2. Nur auf checkout.session.completed reagieren
  3. Bestellung ueber stripe_session_id finden
  4. Idempotenz: Wenn payment_status bereits 'paid', sofort 200 zurueckgeben
     und nichts tun. Stripe sendet Webhooks mehrfach.
  5. payment_status='paid' setzen
  6. Bei variant print/bundle: fulfillment_status='queued'
  7. Lead anlegen oder verknuepfen: Suche in leads nach email. Existiert einer,
     lead_id setzen. Sonst neuen Lead anlegen mit lead_source='buch'.
  8. Auslieferung als BackgroundTask anstossen (Funktion wird in BUCH-06 gebaut;
     lege hier nur den Aufruf und einen Stub an)
  9. Immer 200 zurueckgeben, auch bei internen Fehlern - sonst wiederholt Stripe
     endlos. Fehler stattdessen loggen.

Endpunkt C: GET /api/book/order/{order_number}
  Gibt minimale Bestellinfos fuer die Danke-Seite zurueck:
  {order_number, variant, payment_status, email_masked}
  KEINE Adressdaten, KEIN download_token. Diese Route ist oeffentlich.

SCHRITT 3 — Umgebungsvariablen
Ergaenze in der ENV-Dokumentation und im Code-Zugriff:
  STRIPE_WEBHOOK_SECRET
  STRIPE_TAX_RATE_ID_7
  FRONTEND_BOOK_URL      (die Netlify-Domain der Buch-Landingpage)
Wenn eine davon fehlt, soll die App beim Start eine klare Warnung loggen,
nicht stillschweigend weiterlaufen.

SCHRITT 4 — Verifikation
Zeige mir alle registrierten Routen:
python -c "from backend.main import app; [print(r.methods, r.path) for r in app.routes if '/api/book' in str(r.path)]"

SCHRITT 5
git add -A
git commit -m "Add book checkout endpoint and Stripe webhook handler"
git push origin claude/kompagnon-automation-system-FapM9
```

---

## MANUELLE SCHRITTE (die musst du selbst machen)

**1. Stripe-Steuersatz anlegen**
Stripe Dashboard → Produkte → Steuersätze → Neu:
- Anzeigename: `MwSt. ermäßigt`
- Satz: `7 %`
- Inklusiv (Preise sind Bruttopreise)
- Land: Deutschland
→ Die entstehende ID (`txr_…`) als `STRIPE_TAX_RATE_ID_7` in Render eintragen.

**2. Webhook einrichten**
Stripe Dashboard → Entwickler → Webhooks → Endpunkt hinzufügen:
- URL: `https://claude-code-znq2.onrender.com/api/book/webhook`
- Ereignis: `checkout.session.completed`
→ Das Signing Secret (`whsec_…`) als `STRIPE_WEBHOOK_SECRET` in Render eintragen.

**3. Testkauf**
Stripe-Testmodus, Kartennummer `4242 4242 4242 4242`, beliebiges künftiges Datum.

---

## VERIFIKATION

| Prüfung | Erwartung |
|---|---|
| Routen-Ausgabe Schritt 4 | drei Routen unter `/api/book` |
| Render-Log nach Deploy | keine Warnung über fehlende ENV-Variablen |
| Stripe-Testkauf | Bestellung in `book_orders` mit `payment_status='paid'` |
| Stripe Dashboard → Webhooks | Antwort `200`, kein Wiederholungsversuch |

**Stiller Fehler, auf den du achten musst:** Wenn `STRIPE_WEBHOOK_SECRET` falsch ist,
antwortet dein Backend mit 400, Stripe zeigt einen roten Punkt im Dashboard — aber der
Kunde sieht eine erfolgreiche Zahlung. Er hat bezahlt und bekommt nichts. Prüfe nach dem
ersten Testkauf **immer** die Webhook-Historie im Stripe-Dashboard.

---

## COMMIT-MESSAGE

```
Add book checkout endpoint and Stripe webhook handler
```

---

## ZWEI SCHRITTE VORAUS

- **Rechnungen.** Stripe kann automatisch Rechnungen erzeugen, aber ohne deine
  Pflichtangaben (Firmierung, USt-IdNr., Anschrift) sind sie nicht §14-UStG-konform.
  Aktiviere im Stripe-Dashboard die Rechnungseinstellungen, bevor der erste echte Kauf
  stattfindet — rückwirkend korrigieren ist deutlich aufwendiger.
- **Versand ins Ausland.** `ship_country` steht auf `DE`. Sobald eine österreichische
  Bestellung kommt, ändern sich Versandkosten und die umsatzsteuerliche Behandlung
  (OSS-Verfahren ab 10.000 € EU-Umsatz). Beschränke den Versand vorerst bewusst auf
  Deutschland — das ist eine bewusste Entscheidung, keine Lücke.
- **Der Webhook ist dein Single Point of Failure.** Fällt Render aus, während Stripe
  sendet, wiederholt Stripe 3 Tage lang. Danach ist die Bestellung verloren. Baue später
  einen Abgleich-Befehl, der alle `pending`-Bestellungen älter als 1 Stunde gegen die
  Stripe-API prüft.
