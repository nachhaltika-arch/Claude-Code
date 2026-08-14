# BUCH-07 — Print-Fulfillment: Bestellwarteschlange & BoD-Export

## Warum dieser Schritt

**Die unbequeme Wahrheit vorweg:** BoD und epubli bieten **keine öffentliche
Bestell-API**. Es gibt keinen Weg, eine eingehende Bestellung automatisch als Druckauftrag
weiterzureichen. Wer dir das anders verspricht, hat es nicht geprüft.

Damit gibt es zwei mögliche Modelle:

| Modell | Wie es läuft | Vor-/Nachteil |
|---|---|---|
| **A: Buchhandelsvertrieb** | BoD vergibt ISBN, das Buch landet bei Amazon/Buchhandel. Der Kunde kauft dort. | Kein Aufwand — aber **du bekommst keine Kundendaten**. Der Lead ist verloren. |
| **B: Eigenverkauf mit manueller Fulfillment** | Du verkaufst über deine Seite, sammelst Bestellungen, gibst sie gebündelt als Direktbestellung bei BoD auf. | Etwas Handarbeit — aber **der Lead gehört dir**. |

**Für dein Geschäftsmodell ist nur B sinnvoll.** Das Buch ist ein Lead-Generator. Ein
Verkauf über Amazon bringt dir 15 € Marge und null Kontakt. Ein Verkauf über deine Seite
bringt dir einen qualifizierten Handwerksbetrieb in die Pipeline.

Wir bauen also eine **Warteschlange mit CSV-Export**. Du öffnest sie einmal pro Woche,
exportierst, bestellst bei BoD mit Direktversand an die Kundenadresse, und trägst die
Sendungsnummern zurück.

Zusätzlich kannst du parallel Modell A für die Reichweite laufen lassen — die ISBN im
Buchhandel ist deine Autoritätsreferenz gegenüber HWK/IHK, auch wenn dort kaum Umsatz
entsteht.

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

WICHTIG
Es gibt KEINE BoD-API. Baue keine Integration, keinen HTTP-Client zu BoD und keine
Automatik, die einen Druckauftrag ausloest. Wir bauen ausschliesslich eine interne
Warteschlange mit CSV-Export fuer manuelle Bearbeitung. Alles andere waere eine
Funktion, die im Betrieb still fehlschlaegt.

SCHRITT 1 — Backend-Endpunkte
Ergaenze backend/routers/book.py (alle Routen erfordern Admin-Rolle,
nach dem im Projekt ueblichen Auth-Muster):

  GET /api/book/orders
    Query-Parameter: status, variant, from_date, to_date, limit, offset
    Gibt BookOrderAdminRead zurueck, neueste zuerst

  GET /api/book/orders/export
    Query-Parameter: status (default 'queued')
    Erzeugt eine CSV mit allen Bestellungen dieses Status.
    Spalten in exakt dieser Reihenfolge:
      Bestellnummer;Anrede;Vorname;Nachname;Firma;Strasse;PLZ;Ort;Land;Menge;Variante;Bestelldatum
    Trennzeichen Semikolon, Kodierung UTF-8 MIT BOM
    (sonst zerlegt Excel Umlaute - dieses Muster wird in MassExport.jsx bereits verwendet,
     halte dich daran)
    Dateiname: bod-bestellungen-JJJJ-MM-TT.csv
    Die exportierten Bestellungen bekommen fulfillment_status='exported'
    und fulfillment_exported_at gesetzt.

  PATCH /api/book/orders/{id}/fulfillment
    Body: {fulfillment_status, tracking_number}
    Erlaubte Statuswerte: queued, exported, shipped
    Bei Wechsel auf 'shipped': Versandbestaetigung per Brevo an den Kunden senden
    (Betreff: "Ihr Buch ist unterwegs - Bestellnr. {order_number}")

SCHRITT 2 — Frontend-Ansicht
Lege frontend/src/pages/BookOrders.jsx an.

WICHTIG ZUR FEHLERVERMEIDUNG:
- Verwende den Token aus useAuth(), NICHT aus localStorage direkt.
  (Dieser Fehler hat im Projekt bereits stille 401er verursacht.)
- Verwende API_BASE_URL aus ../config.
- Feldnamen im Frontend muessen EXAKT den Pydantic-Feldnamen entsprechen.
  Zeige mir am Ende eine Gegenueberstellung Backend-Feld -> Frontend-Zugriff,
  damit ich Namensabweichungen sehe.

Inhalt der Seite:
  - Vier KPI-Karten oben: Offen (queued), Exportiert, Versendet, Umsatz laufender Monat
  - Tabelle: Bestellnr, Datum, Name, Firma, Ort, Variante, Zahlstatus, Fulfillment
  - Filterleiste: Status, Variante, Zeitraum
  - Button "CSV fuer BoD exportieren" (nur aktiv, wenn queued > 0)
  - Pro Zeile: Aktion "Als versendet markieren" mit Eingabefeld fuer Sendungsnummer
  - Styling nach bestehendem Muster (CSS-Variablen --brand-primary usw.,
    siehe ProductManager.jsx)

SCHRITT 3 — Routing
Registriere die Route /app/book-orders in der Router-Konfiguration
und ergaenze den Menuepunkt "Buchbestellungen" in
frontend/src/components/Layout/AppLayout.jsx unter der Sektion "kompagnon",
mit adminOnly: true.

WICHTIG: Pruefe beides. Eine Seite ohne Route ist unerreichbar, ein Menuepunkt
ohne Route fuehrt auf eine leere Seite. Zeige mir beide Aenderungen.

SCHRITT 4 — Verifikation
Backend-Routen anzeigen:
python -c "from backend.main import app; [print(r.methods, r.path) for r in app.routes if 'book' in str(r.path)]"
Frontend-Route pruefen:
grep -n "book-orders" frontend/src/App.jsx frontend/src/components/Layout/AppLayout.jsx

SCHRITT 5
git add -A
git commit -m "Add print fulfillment queue with BoD CSV export"
git push origin claude/kompagnon-automation-system-FapM9
```

---

## VERIFIKATION

| Prüfung | Erwartung |
|---|---|
| Schritt 4 Backend | 3 neue Routen sichtbar |
| Schritt 4 Frontend | Treffer in **beiden** Dateien |
| `/app/book-orders` im Browser | Seite lädt, keine 401 in der Konsole |
| CSV-Export öffnen in Excel | Umlaute korrekt, Spalten getrennt |

**Der Fehler, der hier typischerweise passiert:** Die Seite lädt, die Tabelle bleibt leer,
keine Fehlermeldung. Ursache ist fast immer eine Namensabweichung — das Backend liefert
`ship_zip`, das Frontend liest `zip`. Deshalb die Gegenüberstellung in Schritt 2.
**Fordere sie ein und lies sie durch.**

---

## COMMIT-MESSAGE

```
Add print fulfillment queue with BoD CSV export
```

---

## DEIN WÖCHENTLICHER ABLAUF (nach Fertigstellung)

1. `/app/book-orders` öffnen, Filter auf „Offen"
2. „CSV für BoD exportieren" → Datei liegt im Download-Ordner
3. BoD-Konto → Direktbestellung → Bestellungen mit Versandadresse eingeben
4. Sendungsnummern zurück in die Liste eintragen → Kunde bekommt automatisch Mail

Zeitaufwand bei 10 Bestellungen: etwa 20 Minuten.

---

## ZWEI SCHRITTE VORAUS

- **Ab ~30 Bestellungen pro Woche wird das lästig.** Dann lohnt der Wechsel zu einem
  Fulfillment-Dienstleister mit API (z. B. Lulu, das eine echte Print-API hat) oder
  eine eigene Kleinauflage von 200 Stück mit Versand über einen Dienstleister. Beobachte
  die Zahl — der Umstieg braucht Vorlauf.
- **Lieferzeit kommunizieren.** BoD druckt in 2–4 Werktagen, plus Versand. Wenn du
  wöchentlich sammelst, kommen bis zu 7 Tage dazu. Auf der Landingpage muss stehen:
  „Lieferzeit 7–12 Werktage". Wenn dort „sofort lieferbar" steht, hast du ein
  wettbewerbsrechtliches Problem.
- **Reklamationen brauchen einen Platz.** Beschädigte Lieferungen kommen vor.
  `fulfillment_status` sollte später um `reclaimed` und `replaced` erweitert werden —
  jetzt nicht bauen, aber im Hinterkopf behalten.
