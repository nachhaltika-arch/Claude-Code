# Produkt 05 — WORKBOOK „Homepage-Standard in 30 Schritten"
Interne ID: `workbook_homepage_standard` · Version 1.0 · Status: **Konzept, nicht geschrieben**

---

## 1. Funktion im Portfolio
Das Workbook befähigt den Kunden, seine Seite selbst auf Standard zu bringen. Das klingt nach Kannibalisierung — ist aber das Gegenteil.

**Warum es Umsatz erzeugt statt ihn zu vernichten:**
1. **Selbstselektion.** Wer das Workbook durcharbeitet und bei Schritt 9 aufgibt, hat sich selbst bewiesen, dass er den Websprint braucht. Diese Erkenntnis ist überzeugender als jedes Verkaufsgespräch.
2. **Anrechnung.** 100 % des Kaufpreises werden auf einen Websprint innerhalb von 6 Monaten angerechnet. Damit ist der Kauf risikofrei und faktisch eine Anzahlung.
3. **Marktgröße.** Es ist nicht ortsgebunden. Ein Dachdecker in Passau kauft es, obwohl wir ihn nie besuchen werden.
4. **Es beweist den Standard.** Wer eine Norm veröffentlicht *und* das Werkzeug zu ihrer Erfüllung mitliefert, führt keine Verkaufsargumentation mehr — er hat den Maßstab gesetzt.

⚠️ **Wichtig zur Abgrenzung vom Buch:** Das Workbook bekommt **keine ISBN** und wird nicht als Buch vertrieben, sondern als **digitales Arbeitsmaterial mit Druckbeilage**. Nur so bleibt es außerhalb der Buchpreisbindung und die Anrechnung ist zulässig. Diese Konstruktion muss anwaltlich bestätigt werden.

## 2. Aufbau (Vorschlag)
| Teil | Inhalt | Umfang |
|---|---|---|
| A | Selbstaudit — die 100 Punkte als Checkliste zum Ausfüllen | 12 S. |
| B | Kategorie 1–8, je Kategorie: was geprüft wird, wie man es prüft, wie man es behebt | 60 S. |
| C | 30 Arbeitsschritte in Reihenfolge, jeweils mit Zeitaufwand und Werkzeugempfehlung | 40 S. |
| D | Vorlagen: Textbriefing, Bildbriefing, Rechtstexte-Checkliste, Fotografen-Shotlist | 20 S. |
| E | Abnahme-Selbstprotokoll | 4 S. |

**Formate:** PDF (ausfüllbar) + Druckversion + Excel-Auditbogen.

## 3. Preis
**149 € netto**, 100 % anrechenbar auf jeden Websprint innerhalb 6 Monaten.

**Preisbegründung:** Nicht am Materialwert bemessen, sondern an der Anrechnung. Bei 149 € ist die Anrechnung für den Kunden ein spürbarer, aber nicht kaufentscheidender Betrag — sie wirkt als Bindung, nicht als Rabatt.

## 4. Verkaufsargumentation
**Big Promise:** „In 30 Arbeitsschritten selbst auf 85 Punkte. Oder wir machen es — und die 149 € werden angerechnet."

**Das ist ein Angebot, das man nicht verlieren kann.** Genau das ist der Punkt.

**Einwand „dann brauche ich Sie ja nicht mehr":**
„Richtig. Wenn Sie 30 Arbeitsschritte selbst umsetzen, brauchen Sie mich nicht. Die meisten Betriebe schaffen die ersten acht und stellen dann fest, dass Schritt neun einen Entwickler braucht. Dann rufen Sie an, und die 149 € gehen ab."

## 5. Technische Anforderungen in KAS
Hier entsteht echter Neubau — das Workbook ist das **erste digitale Produkt mit eigenem Bestellvorgang**.

| Ebene | Anforderung | Status |
|---|---|---|
| DB | Neue Tabelle `orders` (getrennt von `deals`!) | ❌ offen |
| DB | Feld `anrechnung_gueltig_bis`, Verknüpfung Order → späterer Deal | ❌ offen |
| Backend | Stripe Checkout, Einmalzahlung, 19 % USt | ❌ offen |
| Backend | Auslieferung über **signierte, ablaufende Download-URL** — nicht über öffentliches Netlify-Verzeichnis | ❌ offen |
| Backend | Rechnungserstellung mit **GoBD-konformem, lückenlosem Nummernkreis** | ❌ offen |
| Backend | Bestätigungs- und Auslieferungsmail über Brevo | ❌ offen |
| Recht | Widerrufsbelehrung + ausdrücklicher Widerrufsverzicht vor Download | ❌ **Pflicht bei Verbrauchern** |
| Frontend | Produktseite, Checkout, Kundenkonto-Downloadbereich | ❌ offen |
| Verkauf | Anrechnung muss im Angebotsprozess **automatisch** gezogen werden | ❌ offen |

⚠️ **Zwei Schritte voraus — der teuerste Fehler wäre, das Workbook in die `deals`-Pipeline zu zwingen.** Ein Deal in KAS ist ein Projekt mit 17 Prozessschritten, Kunde, Domain, Deployment. Eine Workbook-Bestellung ist nichts davon. Wenn `product_type` um digitale Produkte erweitert wird, laufen diese Bestellungen durch einen Prozessflow, der auf sie nicht passt — und der Flow bricht beim Deployment-Schritt ab, weil es keine Domain gibt.

**Empfehlung: `orders` als getrenntes Subsystem. Die Verbindung zwischen Order und Deal entsteht nur über die Anrechnung.**

⚠️ **Zwei Schritte voraus — Anrechnung ohne Automatik ist eine Fehlerquelle.** Wenn die Anrechnung manuell im Angebot berücksichtigt werden muss, wird sie irgendwann vergessen. Der Kunde erinnert sich. Das ist ein vermeidbarer Vertrauensschaden. Die Angebotserstellung muss beim Anlegen eines Deals prüfen, ob unter der E-Mail-Adresse eine offene Anrechnung liegt.

## 6. Offene Entscheidungen
- Wird es überhaupt gedruckt, oder rein digital?
- 149 € oder 99 €?
- Anrechnung 6 oder 12 Monate?
- Wer schreibt es — Ableitung aus dem Buchmanuskript oder Neuerstellung?
