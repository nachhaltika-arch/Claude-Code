# ORDERS — PROMPT 02
## Schnittstelle und Produktseite — die erste sichtbare Verbindung

---

## Was dieser Schritt macht

Wir bauen die Schnittstelle, die die Produktliste ausliefert, **und im selben Schritt** die Seite, die sie anzeigt. Beides zusammen, nicht nacheinander.

**Das ist bewusst so geschnitten.** Backend und Frontend in getrennten Schritten zu bauen ist genau das Muster, aus dem bei dir „das Backend ist fertig, aber man sieht nichts" entsteht. Wenn beide Ebenen im selben Commit entstehen, kann die Verbindung nicht vergessen werden.

Am Ende dieses Schritts siehst du zwei Produkte im Browser. Kaufen kann man sie noch nicht.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `nachhaltika-arch/Claude-Code` · `staging`
**Abweichung → sofort stoppen und melden.**

---

## Schritt 1 — Diagnose

1. Wie sind bestehende Router aufgebaut und wo werden sie in `main.py` registriert? Zeige mir eine Beispielzeile.
2. Welche Routen sind öffentlich ohne Anmeldung erreichbar? Der Shop muss öffentlich sein — ein Käufer hat kein Konto.
3. Wie ist das Routing im Frontend organisiert (React Router, welche Datei)?
4. Wo liegt `API_BASE_URL` in der Konfiguration?
5. Gibt es bereits eine Route oder einen Pfad `/shop`, `/orders` oder `/produkte`? **Falls ja: stoppen und melden.**

⚠️ **Punkt 5 ist wichtig.** In diesem Projekt gab es bereits eine versehentliche Routen-Kollision, bei der zwei Funktionen dieselbe Adresse belegten und die zweite dadurch unerreichbar wurde. Prüfe wirklich, bevor du schreibst.

---

## Schritt 2 — Backend-Router

Neue Datei `routers/shop.py`, registriert in `main.py` mit Präfix `/api/shop`.

| Methode | Pfad | Zugriff | Zweck |
|---|---|---|---|
| GET | `/api/shop/products` | öffentlich | Liste aller aktiven Produkte |
| GET | `/api/shop/products/{code}` | öffentlich | Einzelnes Produkt |

Antwortformat je Produkt: `code`, `name`, `short_description`, `amount_net`, `vat_rate`, `amount_gross`, `currency`, `is_creditable`, `credit_months`, `delivery_type`.

`amount_gross` wird aus `amount_net` berechnet und mit kaufmännischer Rundung auf ganze Cent gebracht — nicht im Katalog doppelt pflegen. Zwei Stellen für denselben Wert bedeuten, dass sie irgendwann auseinanderlaufen.

Unbekannter Code → HTTP 404 mit klarer Meldung. Inaktive Produkte erscheinen nicht in der Liste.

**Diese Routen lesen nur aus dem Katalog, nicht aus der Datenbank.** Sie brauchen keine Datenbankverbindung.

---

## Schritt 3 — Frontend-Seite

Neue Komponente `pages/Shop.jsx`, Route `/shop`, öffentlich erreichbar.

Anforderungen:
- Adresse ausschließlich über `API_BASE_URL` aus der Konfiguration — kein fest eingetragener Server
- **Kein `useAuth()` hier** — die Seite ist öffentlich, ein Anmelde-Token würde den Zugriff unnötig verhindern
- Ladezustand und Fehlerzustand darstellen; bei Fehler eine verständliche Meldung, kein leerer Bildschirm
- Je Produkt: Name, Beschreibung, Preis netto und brutto, Hinweis auf die Anrechnung bei `is_creditable`
- Schaltfläche „Kaufen" ist vorhanden, aber **deaktiviert** mit dem Hinweis „in Kürze verfügbar" — sie wird in Prompt 03 aktiviert

Gestaltung nach den Markenkonstanten: Dark Teal `#004F59`, Mid Teal `#008EAA`, Gelb `#FAE600` für aktive Zustände und Handlungsaufforderungen, Schwarz `#000000`. Überschriften in Noto Sans Black, Versalien. Fließtext Noto Sans Regular.

---

## Schritt 4 — Navigation

Trage `/shop` dort ein, wo öffentliche Seiten verlinkt sind. Eine Seite ohne Verweis ist praktisch nicht vorhanden.

Falls es keine öffentliche Navigation gibt: **melden statt raten.**

---

## Schritt 5 — Verifikation, alle vier Ebenen

```bash
curl -s https://claude-code-znq2.onrender.com/api/shop/products | head -40
curl -s -o /dev/null -w "%{http_code}\n" https://claude-code-znq2.onrender.com/api/shop/products/WB-01
curl -s -o /dev/null -w "%{http_code}\n" https://claude-code-znq2.onrender.com/api/shop/products/GIBTESNICHT
```

Erwartet: JSON mit zwei Produkten · 200 · 404

Danach im Browser:
1. `https://kompagnon-frontend.onrender.com/shop` öffnen
2. **Ohne Anmeldung** — im privaten Fenster prüfen
3. Beide Produkte sichtbar, Preise korrekt, Kaufen-Schaltfläche deaktiviert
4. Entwicklerkonsole ohne Fehler

**Verbindungs-Check:** Katalog ✅ · Schnittstelle ✅ · Frontend-Route ✅ · Im Browser sichtbar ✅

Bricht die Kette an einer Stelle: **Ursache melden, Prompt 03 nicht starten.**

---

## Schritt 6 — Commit und Push

```bash
git add -A
git commit -m "Add public shop API and product listing page"
git push origin staging
```

---

## STOPP

Berichte die Ergebnisse aller vier Verifikationsebenen und einen kurzen Hinweis, wie die Seite aussieht. **Warte auf Bestätigung.**
