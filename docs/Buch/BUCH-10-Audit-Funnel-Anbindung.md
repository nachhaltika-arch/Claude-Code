# BUCH-10 — Funnel: Vom Audit-Ergebnis zur Buch-Landingpage

## Warum dieser Schritt zuletzt kommt

Erst wenn die Landingpage wirklich live ist und der Kauf funktioniert, darfst du Traffic
darauf lenken. Ein CTA, der auf eine halbfertige Seite zeigt, verbrennt genau die Leads,
die du am dringendsten brauchst.

## Die Funnel-Logik

Der entscheidende Gedanke: **Der Buch-CTA wird nicht allen gleich gezeigt.** Wer 88 Punkte
hat, braucht kein Buch — der braucht ein Angebot. Wer 24 Punkte hat, ist überfordert und
kauft das Buch als ersten kleinen Schritt.

| Score | Stufe | Was angezeigt wird |
|---|---|---|
| 0–29 | Nicht konform | Buch **prominent** — „Verstehen Sie zuerst, was zu tun ist" |
| 30–49 | Bronze | Buch prominent + Hinweis auf Beratung |
| 50–69 | Silber | Buch **gleichwertig** neben dem Angebot |
| 70–84 | Gold | Angebot zuerst, Buch als Nebenoption |
| 85–100 | Platin | **Kein Buch.** Wartungsvertrag anbieten. |

Das ist keine Spielerei — es ist der Unterschied zwischen einem Verkaufsfunnel und einem
Banner. Ein Platin-Kunde, dem du ein Anfängerbuch anbietest, fühlt sich nicht ernst
genommen.

---

## Wo der CTA eingebaut wird

Der Homepage Standard wird an **vier** Stellen ausgegeben. Alle vier müssen bedacht
werden, sonst hast du Lücken im Funnel:

| Datei | Kontext | CTA nötig? |
|---|---|---|
| `frontend/src/components/AuditHook.jsx` | öffentliches Audit auf der Website | **ja, wichtigste Stelle** |
| `frontend/public/embed/audit-widget.html` | Widget auf fremden Seiten | **ja** |
| `frontend/src/components/AuditReport.jsx` | interne Ansicht im KAS | nein (das siehst du selbst) |
| Audit-PDF (`/api/audit/{id}/pdf`) | wird an Leads verschickt | **ja, mit QR-Code** |

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

SCHRITT 1 — Zentrale CTA-Logik
Lege frontend/src/utils/bookCta.js an:

  export const BOOK_URL = process.env.REACT_APP_BOOK_URL
    || 'https://DEINE-NETLIFY-DOMAIN.netlify.app';

  export function getBookCta(score) {
    // gibt zurueck: { show, prominence, headline, buttonLabel, url } | null
    // prominence: 'primary' | 'secondary' | 'none'
    // ab Score 85: { show: false }
  }

  Die URL enthaelt immer UTM-Parameter:
    ?utm_source=audit&utm_medium=cta&utm_campaign=hs2026&score={score}

Texte nach Score-Bereich:
  0-29:  "Bevor Sie investieren: verstehen Sie, was fehlt"
         Button "Das Handbuch zum Standard - 39 Euro"
  30-49: "Sie haben ein Fundament. Jetzt kommt es auf die Reihenfolge an."
         Button "Der 30-Tage-Plan im Buch - 39 Euro"
  50-69: "Der Weg zu Gold ist kuerzer als Sie denken"
         Button "Buch ansehen - 39 Euro"
  70-84: kleiner Textlink "Details zu allen Kriterien im Handbuch"
  85+:   null

SCHRITT 2 — AuditHook.jsx
Baue den CTA in die Ergebnisansicht ein, direkt UNTER dem Score und der Stufe,
aber UEBER der Detailauflistung. Bei prominence 'primary' als Karte mit
--kc-yellow Akzent, bei 'secondary' als dezenter Textlink.
Der Link oeffnet in einem neuen Tab (target="_blank" rel="noopener").

SCHRITT 3 — audit-widget.html
Dieselbe Logik in Vanilla-JavaScript nachbauen. Das Widget laeuft auf fremden
Seiten und kann nichts aus React importieren - dupliziere die Schwellenwerte
und setze einen Kommentar mit Verweis auf bookCta.js, damit die Duplizierung
bei Aenderungen auffaellt.
Beachte: Das Widget meldet seine Hoehe per postMessage an die Elternseite
(Funktion postHeight). Rufe postHeight() nach dem Einfuegen des CTA erneut auf,
sonst wird der Button im iframe abgeschnitten.

SCHRITT 4 — Audit-PDF
Ergaenze im PDF-Generator (/api/audit/{id}/pdf) auf der letzten Seite einen
Kasten mit dem CTA-Text nach derselben Score-Logik plus einem QR-Code, der auf
BOOK_URL mit utm_source=auditpdf zeigt.
Nutze die im Projekt bereits vorhandene QR-Funktionalitaet, falls es eine gibt -
zeige mir zuerst, was existiert, bevor du eine neue Bibliothek einbaust.

SCHRITT 5 — Rueckverfolgung
Im Buch-Checkout (BUCH-05) werden utm_source und utm_campaign bereits in
book_orders gespeichert. Stelle sicher, dass checkout.js in landing-buch/
diese Parameter aus der URL ausliest und mitsendet. Falls das noch nicht
implementiert ist, ergaenze es dort.

SCHRITT 6 — Umgebungsvariable
Ergaenze REACT_APP_BOOK_URL in der Frontend-ENV-Dokumentation.
Sie muss in Render beim Frontend-Service gesetzt werden.

SCHRITT 7 — Verifikation
grep -rn "bookCta\|BOOK_URL" frontend/src/ frontend/public/embed/
Zeige mir alle Fundstellen.

SCHRITT 8
git add -A
git commit -m "Add score-based book CTA to audit results and audit widget"
git push origin claude/kompagnon-automation-system-FapM9
```

---

## MANUELLER SCHRITT

Render → **Frontend**-Service → Environment:
```
REACT_APP_BOOK_URL = https://DEINE-NETLIFY-DOMAIN.netlify.app
```
React-Umgebungsvariablen werden beim **Build** eingesetzt, nicht zur Laufzeit. Nach dem
Setzen ist ein neuer Deploy nötig, sonst bleibt der Fallback-Wert aktiv.

---

## VERIFIKATION

| Prüfung | Erwartung |
|---|---|
| Audit mit Testseite (schlechter Score) durchführen | prominenter Buch-CTA erscheint |
| Audit mit sehr guter Seite | **kein** Buch-CTA |
| CTA anklicken | Landingpage öffnet, URL enthält `utm_source=audit&score=…` |
| Kauf abschließen | in `book_orders` steht `utm_source='audit'` |
| Widget in einem iframe testen | Button nicht abgeschnitten |

**Die vollständige Kette einmal durchlaufen:** Audit → CTA → Landingpage → Kauf → Mail →
Lead in der Pipeline. Wenn ein Glied fehlt, siehst du es nur hier — nicht in den Logs.

---

## COMMIT-MESSAGE

```
Add score-based book CTA to audit results and audit widget
```

---

## ZWEI SCHRITTE VORAUS

- **Die Duplizierung in `audit-widget.html` wird dich einholen.** Wenn du die
  Score-Schwellen änderst und das Widget vergisst, zeigen zwei Systeme
  Unterschiedliches. Setze den Kommentarverweis aus Schritt 3 wirklich — oder besser:
  lade die Schwellen später per API statt sie zu duplizieren.
- **Nach vier Wochen brauchst du Zahlen.** Wie viele Audits führen zu einem CTA-Klick,
  wie viele Klicks zu einem Kauf? Das lässt sich aus `book_orders.utm_source` gegen die
  Audit-Anzahl rechnen. Bau dir dafür eine kleine Auswertung — ohne sie optimierst du
  blind.
- **Der nächste logische Schritt nach dem Buchkauf ist die Wartungs- oder
  Website-Offerte.** Der Käufer ist jetzt als Lead mit `lead_source='buch'` im System.
  Eine automatische Brevo-Sequenz 14 Tage nach Kauf („Wie weit sind Sie gekommen?") ist
  der natürliche Anschluss — und passt zu der bereits geplanten Hebel-Automatisierung.
