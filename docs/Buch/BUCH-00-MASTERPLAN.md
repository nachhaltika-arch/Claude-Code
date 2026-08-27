# BUCH — MASTERPLAN
## Der Homepage Standard (Buch) als Einstiegsprodukt

**Stand:** August 2026
**Entscheidungen:** Standardwerk 150–200 Seiten · 39–49 € · PDF + Print via BoD · Landingpage auf eigener Netlify-Seite

---

## 1. Was wir bauen (in einfachen Worten)

Wir machen aus dem bereits existierenden Audit-Bewertungssystem ein verkaufbares Buch.

Der Kunde durchläuft heute schon ein kostenloses Audit auf deiner Seite. Er bekommt einen
Score von 0–100 und eine Stufe (Bronze/Silber/Gold/Platin). Was ihm fehlt: **Er versteht
nicht, was die Punkte bedeuten und was er tun soll.** Genau das erklärt das Buch.

Der Weg des Kunden:

```
Audit (kostenlos)  →  Ergebnis-Seite mit Score  →  CTA "Was bedeutet mein Score?"
      →  Netlify-Landingpage (Buch)  →  Checkout (Stripe)
      →  PDF sofort per Mail  /  Print in Warteschlange
      →  Käufer ist automatisch Lead im KAS  →  Upsell ONLINE FERTIG.
```

Das Buch ist **kein Umsatzprodukt**, es ist ein Qualifizierungsprodukt. Wer 44 € für ein
Fachbuch über seine Website ausgibt, hat Problembewusstsein und Budget. Das ist der
wertvollste Lead, den du bekommen kannst.

---

## 2. Das zentrale Prinzip: Single Source of Truth

Der Homepage Standard existiert bereits an drei Stellen im Code:

| Ort | Was steht drin |
|---|---|
| `frontend/src/components/AuditReport.jsx` | 6 Kategorien, ~30 Unterkriterien, Punktzahlen |
| `frontend/src/components/HomepageChecklist.jsx` | Kriterien mit Gesetzesbezug (TMG, DSGVO, WCAG …) |
| `frontend/public/embed/audit-widget.html` | Stufen-Schwellen (85/70/50/30) |

**Risiko:** Wenn du das Audit später änderst, stimmt das gedruckte Buch nicht mehr.
Ein Kunde mit Buch in der Hand rechnet nach. Das kostet dich sofort die Glaubwürdigkeit.

**Lösung:** Wir legen eine gemeinsame Definitionsdatei an
(`shared/homepage-standard.json`) und einen Prüf-Befehl, der meldet, sobald Buch und
Audit auseinanderlaufen. → Siehe `BUCH-01`.

---

## 3. Reihenfolge der Umsetzung

Jede Zeile ist eine eigene Prompt-Datei. **Immer nur eine ausführen, dann Render-Logs
prüfen, dann die nächste.** Niemals mehrere zusammen.

### Phase A — Fundament (zuerst, sonst driftet alles)
| # | Datei | Was passiert | Dauer |
|---|---|---|---|
| 1 | `BUCH-01-Manuskript-Struktur.md` | Ordner `/buch/`, Definitionsdatei, Drift-Check | 20 Min |
| 2 | `BUCH-12-Bestandsfehler-Fixes.md` | 5 Altlasten-Fixes (7 % MwSt, Jahreszahl …) | 30 Min |

### Phase B — Inhalt (parallel zur Technik möglich)
| # | Datei | Was passiert | Dauer |
|---|---|---|---|
| 3 | `BUCH-02-Kapitel-Content.md` | 12 Kapitel schreiben lassen | 2–3 Tage |
| 4 | `BUCH-11-Rechtstexte-Compliance.md` | Disclaimer, Impressum, ISBN, Widerruf | 1 Tag |

### Phase C — Produktion
| # | Datei | Was passiert | Dauer |
|---|---|---|---|
| 5 | `BUCH-03-PDF-Build-Pipeline.md` | Markdown → 2 PDFs (Screen + Druck) | 1 Tag |

### Phase D — Verkauf (Technik)
| # | Datei | Was passiert | Dauer |
|---|---|---|---|
| 6 | `BUCH-04-Datenmodell-Bestellungen.md` | Tabelle `book_orders` | 30 Min |
| 7 | `BUCH-05-Backend-Checkout-Stripe.md` | Checkout-Endpunkt, 7 % MwSt, Webhook | 1 Std |
| 8 | `BUCH-09-CORS-Routing.md` | **Netlify ↔ Render Verbindung** | 20 Min |
| 9 | `BUCH-06-PDF-Auslieferung.md` | Wasserzeichen, signierte Links, Mail | 1 Std |
| 10 | `BUCH-07-Print-Fulfillment.md` | Bestell-Warteschlange, BoD-Export | 45 Min |

### Phase E — Funnel
| # | Datei | Was passiert | Dauer |
|---|---|---|---|
| 11 | `BUCH-08-Netlify-Landingpage.md` | Verkaufsseite bauen + deployen | 1 Tag |
| 12 | `BUCH-10-Audit-Funnel-Anbindung.md` | Audit-Ergebnis → Buch-CTA | 30 Min |

---

## 4. Abhängigkeiten — was NICHT vorgezogen werden darf

```
BUCH-01  ──►  BUCH-02  ──►  BUCH-03  ──►  BUCH-06
                                │
BUCH-04  ──►  BUCH-05  ──►  BUCH-06  ──►  BUCH-07
                │
                └──►  BUCH-09  ──►  BUCH-08  ──►  BUCH-10
```

- `BUCH-06` (Auslieferung) braucht **sowohl** das fertige PDF **als auch** den Checkout.
- `BUCH-08` (Landingpage) ohne `BUCH-09` (CORS) = Kaufbutton ohne Funktion.
- `BUCH-10` als Letztes — erst wenn die Landingpage wirklich live ist.

---

## 5. PFLICHT-CHECK vor jeder Session

```bash
git remote -v
git branch --show-current
```

Erwartet:
- `origin` → `https://github.com/nachhaltika-arch/Claude-Code`
- Branch → `staging`

Stimmt eines nicht: **STOPP**, nichts ausführen, melden.

---

## 6. Zwei Schritte voraus — was danach kommt

1. **Der Kunde wird fragen: „Prüft ihr das für mich?"** — Im Buch muss ein QR-Code auf
   das kostenlose Audit verweisen. Du hast bereits einen QR-Generator im System
   (`/app/qr-generator`). Der Rückweg vom Papier ins System muss vor Drucklegung stehen —
   nach dem Druck ist er nicht mehr änderbar.

2. **Das Buch wird dein Autoritätsnachweis gegenüber HWK/IHK.** Für die ISB-158/IMPULS-
   Schiene brauchst du eine Kammerempfehlung. Ein publiziertes Fachbuch mit ISBN ist
   dafür das stärkste Argument, das du bauen kannst. Deshalb: Autorenangabe, Impressum
   und Verlagsangabe von Anfang an kammertauglich setzen.

3. **Nach ~6 Monaten brauchst du eine 2. Auflage.** Gesetze ändern sich (BFSG,
   TDDDG-Rechtsprechung). Die Markdown-Quelle im Repo macht das zu einem Ein-Tages-Job
   statt zu einer Neuproduktion — vorausgesetzt, `BUCH-01` wurde sauber gebaut.
