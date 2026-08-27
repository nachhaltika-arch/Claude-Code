# BUCH-08 — Netlify-Landingpage

## Warum dieser Schritt und was das Besondere ist

Die Verkaufsseite liegt bewusst **nicht** im KAS-Frontend, sondern als eigenständige
Seite auf Netlify. Das hat Vorteile und einen Preis:

**Vorteile:** Sie lädt in Millisekunden (statische Datei vom CDN), sie ist unabhängig von
Render-Ausfällen, sie kann eine eigene Domain bekommen, und sie ist unabhängig vom
React-Build deployerbar. Für eine Verkaufsseite ist Ladezeit direkt Umsatz.

**Der Preis:** Die Seite liegt auf einer anderen Domain als dein Backend. Jeder Aufruf des
Backends ist damit ein „Cross-Origin-Request", den der Browser aktiv blockiert, solange
das Backend ihn nicht ausdrücklich erlaubt. Das ist `BUCH-09` — **und es muss vor diesem
Schritt erledigt sein**, sonst hast du eine schöne Seite mit einem toten Kaufbutton.

---

## Aufbau der Seite (Reihenfolge ist Verkaufslogik, nicht Geschmack)

| # | Abschnitt | Zweck |
|---|---|---|
| 1 | Hero: Buchcover + Titel + Kernversprechen + Preis + CTA | Entscheidung in 5 Sekunden ermöglichen |
| 2 | Das Problem | Wiedererkennung: „Genau das ist bei mir so" |
| 3 | Was drin steht | 12 Kapitel als Liste mit Seitenzahlen |
| 4 | Leseprobe | Kapitel 3 als PDF, ohne E-Mail-Abfrage |
| 5 | Für wen es ist / für wen nicht | Ehrlichkeit erhöht Konversion |
| 6 | Die drei Varianten | PDF / Print / Bundle nebeneinander |
| 7 | Autor & Herkunft der Daten | „aus über X ausgewerteten Websites" |
| 8 | Häufige Fragen | Lieferzeit, Widerruf, Rechnung, Update |
| 9 | Letzter CTA | Zweite Kaufgelegenheit |
| 10 | Footer | Impressum, Datenschutz, Widerruf, AGB |

**Bewusst weggelassen:** Countdown-Timer, „nur noch 3 Exemplare", Rabatt-Popups. Deine
Zielgruppe sind Handwerksmeister — Drucktaktiken zerstören bei dieser Gruppe das
Vertrauen, das das Buch aufbauen soll.

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

ZIEL
Eine eigenstaendige, statische Landingpage im Ordner landing-buch/ im Repo.
Sie wird spaeter separat zu Netlify deployt. Sie ist KEIN Teil des React-Frontends
und darf nichts aus frontend/ importieren.

TECHNISCHE VORGABEN
- Reines HTML + CSS + minimales Vanilla-JavaScript. Kein React, kein Build-Schritt,
  kein npm. Eine Datei index.html plus assets.
- KEINE externen Schrift-URLs. Noto Sans wird als lokale WOFF2-Datei eingebunden.
  Google Fonts per CDN ist in Deutschland abmahnfaehig - das ist genau das Thema,
  ueber das dieses Buch aufklaert. Ein Verstoss auf der eigenen Verkaufsseite waere
  fatal.
- Mobile First. Ueber 60 Prozent der Zielgruppe liest auf dem Handy.
- Keine Cookies, kein Tracking beim ersten Seitenaufruf. Damit ist kein Cookie-Banner
  noetig. Analytics erst nach ausdruecklicher Einwilligung (siehe unten).

DATEISTRUKTUR
landing-buch/
  index.html
  danke.html
  css/style.css
  js/checkout.js
  assets/fonts/       (NotoSans-Regular.woff2, NotoSans-Bold.woff2, NotoSans-Black.woff2)
  assets/img/         (cover.webp, cover@2x.webp, leseprobe-thumb.webp)
  assets/leseprobe.pdf
  _headers
  _redirects
  netlify.toml

CORPORATE DESIGN
  --kc-dark:   #004F59
  --kc-mid:    #008EAA
  --kc-yellow: #FAE600
  Headlines: Noto Sans Black. Fliesstext: Noto Sans Regular, 17px, Zeilenabstand 1,6.
  Grosszuegige Weissraeume. Der gelbe Ton nur als Akzent (CTA-Buttons, Hervorhebungen),
  niemals flaechig.

SEITENINHALT
Baue die 10 Abschnitte aus der Tabelle in BUCH-08 der Prompt-Dokumentation.
Schreibe echte deutsche Verkaufstexte, keine Platzhalter wie "Lorem ipsum".
Sie-Form, sachlich, keine Ausrufezeichen, keine Superlative.
Preise: PDF 39 Euro, Print 49 Euro zzgl. 4,95 Euro Versand, Bundle 59 Euro
zzgl. 4,95 Euro Versand. Alle Preise inklusive 7 Prozent Mehrwertsteuer.
Lieferzeit Print: 7-12 Werktage. Lieferzeit PDF: sofort per E-Mail.

CHECKOUT-FORMULAR (js/checkout.js)
Bei Klick auf einen Kaufbutton oeffnet sich ein Formular-Overlay:
  - Variante (vorausgewaehlt durch den geklickten Button, aenderbar)
  - Vorname, Nachname, Firma (optional), E-Mail
  - Bei print/bundle zusaetzlich: Strasse, PLZ, Ort
  - Pflicht-Checkbox bei pdf/bundle:
    "Ich verlange ausdruecklich, dass Sie mit der Ausfuehrung der Leistung vor Ablauf
     der Widerrufsfrist beginnen. Mir ist bekannt, dass ich mit Beginn der Ausfuehrung
     mein Widerrufsrecht verliere."
  - Pflicht-Checkbox: Datenschutzerklaerung gelesen
  - Absenden -> POST an API_BASE + /api/book/checkout
  - Bei Erfolg: window.location.href = checkout_url
  - Bei Fehler: Fehlermeldung IM Formular anzeigen, Button wieder aktivieren,
    Eingaben NICHT loeschen

FEHLERBEHANDLUNG (kritisch)
  - Netzwerkfehler / CORS-Block: sichtbare Meldung
    "Die Verbindung zum Zahlungsdienst ist fehlgeschlagen. Bitte versuchen Sie es
     erneut oder schreiben Sie an [E-Mail]."
    UND console.error mit dem technischen Detail.
  - Kein stiller Fehlschlag. Der Button darf niemals einfach nichts tun.
  - Timeout nach 15 Sekunden mit derselben Meldung.

API_BASE wird als Konstante am Anfang von checkout.js definiert:
  const API_BASE = "https://claude-code-znq2.onrender.com";

danke.html
  Liest den Parameter ?order= aus der URL, ruft GET /api/book/order/{nr} auf
  und zeigt: Bestellnummer, Variante, Hinweis auf die E-Mail.
  WICHTIG: Diese Seite darf NICHT als Kaufbestaetigung formuliert sein, solange
  payment_status nicht 'paid' ist. Zeige bei 'pending' den Text
  "Ihre Zahlung wird verarbeitet."

_headers (Netlify Security Headers)
  /*
    X-Frame-Options: DENY
    X-Content-Type-Options: nosniff
    Referrer-Policy: strict-origin-when-cross-origin
    Strict-Transport-Security: max-age=31536000; includeSubDomains
    Content-Security-Policy: default-src 'self'; connect-src 'self' https://claude-code-znq2.onrender.com; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self'

netlify.toml
  [build] publish = "." und command = "" (kein Build noetig)

SCHRITT ZUM SCHLUSS — Selbstpruefung
Pruefe und melde mir:
  1. Kommt irgendwo im HTML/CSS eine fonts.googleapis.com oder fonts.gstatic.com URL vor?
     Befehl: grep -rn "googleapis\|gstatic" landing-buch/
     Erwartete Ausgabe: keine Treffer.
  2. Stimmt API_BASE in checkout.js mit der Backend-URL ueberein?
  3. Sind alle vier Pflicht-Links im Footer vorhanden
     (Impressum, Datenschutz, Widerrufsbelehrung, AGB)?

git add -A
git commit -m "Add standalone Netlify landing page for book sales"
git push origin staging
```

---

## MANUELLER SCHRITT: Netlify-Deployment

Das Repo enthält jetzt den Ordner. Deployen musst du selbst:

1. Netlify-Konto → **Add new site** → **Import from Git** → `nachhaltika-arch/Claude-Code`
2. **Branch:** `staging`
3. **Base directory:** `landing-buch`
4. **Publish directory:** `landing-buch`
5. **Build command:** leer lassen
6. Deploy → Netlify vergibt eine Adresse wie `random-name-123.netlify.app`
7. Diese Adresse notieren — **du brauchst sie sofort für `BUCH-09` (CORS)**
8. Später: eigene Domain verbinden, z. B. `homepage-standard.de`

---

## VERIFIKATION

| Prüfung | Erwartung |
|---|---|
| `grep -rn "googleapis\|gstatic" landing-buch/` | keine Treffer |
| Seite auf dem Handy öffnen | lesbar ohne Zoom, CTA sichtbar ohne Scrollen |
| PageSpeed Insights, Mobile | über 90 Punkte |
| Kaufbutton klicken | Formular öffnet sich |
| Formular absenden **vor** BUCH-09 | Fehlermeldung erscheint sichtbar (korrekt!) |

**Der letzte Punkt ist Absicht.** Solange CORS nicht eingerichtet ist, *muss* der Button
eine sichtbare Fehlermeldung zeigen. Wenn er stattdessen nichts tut, ist die
Fehlerbehandlung falsch gebaut — und genau dieser Fehler bleibt im Betrieb monatelang
unentdeckt.

---

## COMMIT-MESSAGE

```
Add standalone Netlify landing page for book sales
```

---

## ZWEI SCHRITTE VORAUS

- **Diese Seite ist gleichzeitig deine Referenz.** Wenn du ein Buch über den Homepage
  Standard verkaufst, wird diese Seite von Interessenten geprüft. Sie muss selbst
  Platin-Niveau erreichen — lass sie nach dem Deploy durch dein eigenes Audit laufen.
  Ein Score unter 85 wäre peinlich.
- **Tracking kommt später und braucht dann doch einen Banner.** Wenn du GA4 oder Meta
  Pixel ergänzt, brauchst du eine Einwilligungslösung und die CSP muss erweitert werden.
  Starte bewusst ohne — du kannst Konversionen fürs Erste über Stripe zählen.
- **Domain-Strategie.** `homepage-standard.de` als eigene Domain macht das Buch zur Marke
  und ist später auch der natürliche Ort für ein öffentliches Audit-Widget. Prüfe die
  Verfügbarkeit, bevor du dich auf die `.netlify.app`-Adresse festlegst — sie steht sonst
  im gedruckten Buch.
