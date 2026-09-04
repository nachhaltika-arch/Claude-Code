# ORDERS — PROMPT 05
## Rechtliche Pflichtangaben und Widerrufsverzicht

---

## Was dieser Schritt macht — und warum er vor dem Live-Gang stehen muss

Beim Verkauf digitaler Inhalte an Verbraucher gelten Pflichten, deren Verletzung nicht folgenlos bleibt:

**Ohne korrekte Widerrufsbelehrung beginnt die Widerrufsfrist nicht zu laufen.** Sie verlängert sich auf zwölf Monate und vierzehn Tage. Ein Käufer kann also nach einem Jahr das Geld zurückverlangen — und hat das Produkt bereits.

**Sofortige Auslieferung ohne Verzichtserklärung ist unzulässig.** Damit ein digitales Produkt direkt nach der Zahlung heruntergeladen werden darf, muss der Käufer vorher ausdrücklich zustimmen, dass die Auslieferung vor Ablauf der Widerrufsfrist beginnt, und bestätigen, dass er dadurch sein Widerrufsrecht verliert.

**Die Schaltfläche muss eindeutig beschriftet sein.** „Weiter" oder „Absenden" genügt nicht — erforderlich ist eine Formulierung, die die Zahlungspflicht klar benennt.

⚠️ Ich bin kein Rechtsanwalt. Dieser Prompt setzt die technischen Voraussetzungen um. **Die Texte selbst müssen anwaltlich geprüft werden, bevor der Shop öffentlich erreichbar ist.**

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

1. Existieren AGB, Widerrufsbelehrung und Datenschutzerklärung als Seiten im Frontend?
2. Gibt es eine Versionierung der AGB (Fassungsdatum)?
3. Wie wird die Datenschutzerklärung heute eingebunden?

**Falls Widerrufsbelehrung oder AGB fehlen: melden und stoppen.** Ich muss die Texte von der Kanzlei bekommen, bevor du sie einbaust. Erfinde keine Rechtstexte — auch keine Platzhalter, die aussehen wie echte Texte. Setze stattdessen eine unübersehbare Markierung `[[RECHTSTEXT AUSSTEHEND]]`.

---

## Schritt 2 — Backend-Absicherung

Die Sperre aus Prompt 03 wird vollständig ausgebaut:

1. `terms_accepted` fehlt oder ist falsch → 400
2. `is_business` falsch **und** `withdrawal_waived` falsch → 400 mit dem Hinweis, dass ohne Verzicht keine sofortige Auslieferung erfolgen kann
3. `terms_accepted_at` und `withdrawal_waived_at` mit Zeitstempel speichern — als Nachweis
4. Fassungsdatum der AGB in der Bestellung mitspeichern (neues Feld `terms_version`)

⚠️ **Punkt 4 ist der Punkt, den fast alle vergessen.** Ändern sich die AGB, muss nachweisbar bleiben, welche Fassung der Käufer akzeptiert hat. Ohne dieses Feld ist die Zustimmung im Streitfall wertlos.

Ergänze die Migration entsprechend, wieder mehrfach ausführbar.

---

## Schritt 3 — Frontend-Bestellformular

Vor der Kaufen-Schaltfläche als Pflichtangaben darstellen:

| Element | Umsetzung |
|---|---|
| Produktbezeichnung | Klartext, kein Kürzel |
| Preis | netto **und** brutto, Steuersatz genannt |
| Auswahl privat/geschäftlich | Pflichtfeld, keine Vorbelegung |
| AGB-Häkchen | Pflicht, mit Verweis auf die AGB-Seite in neuem Fenster |
| Widerrufsbelehrung | verlinkt, für Verbraucher sichtbar hervorgehoben |
| Verzichts-Häkchen | **nur** bei Auswahl „privat", dann Pflicht |
| Schaltfläche | Beschriftung **„Zahlungspflichtig bestellen"** |

Der Verzichtstext ist auszuformulieren und anwaltlich zu prüfen. Bis dahin `[[RECHTSTEXT AUSSTEHEND]]` einsetzen, Inhalt sinngemäß: Zustimmung zum sofortigen Beginn der Auslieferung und Kenntnisnahme des Erlöschens des Widerrufsrechts.

**Kein vorbelegtes Häkchen.** Vorangekreuzte Zustimmungen sind unwirksam.

Bei Auswahl „geschäftlich": Verzichts-Häkchen ausblenden, Feld für USt-IdNr. einblenden.

---

## Schritt 4 — Bestellbestätigung als Nachweis

Der Wortlaut der akzeptierten Erklärungen wird in der Bestätigungsmail wiederholt (Versand kommt in Prompt 06). Lege dafür jetzt die Textbausteine an, damit sie in Prompt 06 nur noch eingesetzt werden.

---

## Schritt 5 — Verifikation

Verbraucher ohne Verzicht:
```bash
curl -s -w "\n%{http_code}\n" -X POST https://claude-code-znq2.onrender.com/api/shop/checkout \
  -H "Content-Type: application/json" \
  -d '{"product_code":"WB-01","buyer_email":"t@example.com","buyer_name":"T","buyer_address":"A","is_business":false,"terms_accepted":true,"withdrawal_waived":false}'
```
Erwartet: **400** mit verständlicher Meldung.

Ohne AGB-Zustimmung:
```bash
curl -s -w "\n%{http_code}\n" -X POST https://claude-code-znq2.onrender.com/api/shop/checkout \
  -H "Content-Type: application/json" \
  -d '{"product_code":"WB-01","buyer_email":"t@example.com","buyer_name":"T","buyer_address":"A","is_business":true,"terms_accepted":false,"withdrawal_waived":true}'
```
Erwartet: **400**.

Datenbank:
```sql
SELECT order_number, is_business, terms_accepted_at, withdrawal_waived, withdrawal_waived_at, terms_version FROM orders ORDER BY created_at DESC LIMIT 3;
```
Erwartet: Zeitstempel und Fassungsdatum gefüllt.

Im Browser prüfen: Umschalten zwischen privat und geschäftlich blendet das Verzichts-Häkchen korrekt ein und aus; Schaltfläche heißt „Zahlungspflichtig bestellen"; kein Häkchen ist vorbelegt.

---

## Schritt 6 — Commit und Push

```bash
git add -A
git commit -m "Add mandatory legal consent handling for digital orders"
git push origin staging
```

---

## STOPP — dies ist ein doppelter Halt

Berichte den technischen Stand **und** liste auf, welche Rechtstexte noch mit `[[RECHTSTEXT AUSSTEHEND]]` markiert sind.

**Der Shop bleibt nicht öffentlich verlinkt, bis alle Markierungen durch geprüfte Texte ersetzt sind.**
