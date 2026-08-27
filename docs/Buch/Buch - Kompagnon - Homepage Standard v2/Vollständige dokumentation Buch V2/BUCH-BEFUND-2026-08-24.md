# BEFUND-REPORT — Buch „Der Homepage Standard"

**Datum:** 24.08.2026
**Geprüft gegen:** `nachhaltika-arch/Claude-Code`, Branch `main` (77c8fbb) **und** `staging` (7d950c2)
**Methode:** Quelltext ausgeführt und ausgemessen, nicht gelesen. Alle Zahlen unten stammen aus einem Lauf gegen `services/audit_criteria.py`, nicht aus einem Dokument.
**Anlass:** Das Datenblatt `KAS_DB_05_Buch.md` und der `RESTARBEITEN-REPORT.md` (Stand 14.08.) nennen fünf Publikationsblocker. Drei davon sind seither erledigt worden, ohne dass die Dokumente nachgezogen wurden.

---

## 0. Die wichtigste Erkenntnis vorab

**Das Buch existiert bereits.** Es liegt vollständig im Repo:

```
docs/Buch/Buch - Kompagnon - Der Homepage Standard/
  00-titelei.md · 01-warum.md · 02-das-system.md · 03-recht.md
  04-sicherheit.md · 05-performance.md · 06-barrierefreiheit.md
  07-seo.md · 08-design.md · 09-conversion.md · 10-inhalt.md
  11-selbsttest.md · 12-top20-fehler.md · 13-massnahmenplan.md
  90-anhang-glossar.md
```

15 Manuskriptdateien, zusammen rund 320 KB Markdown — die dokumentierten 48.094 Wörter. Dazu 13 Umsetzungspläne `BUCH-00` bis `BUCH-12`.

Die Aufgabe ist also nicht „ein Buch entwickeln", sondern **ein fertiges Manuskript verkaufsfähig machen**. Das ist eine andere, deutlich kleinere Aufgabe — und sie hat einen anderen Engpass als bisher angenommen.

---

## 1. Statusabgleich der fünf Blocker

| ID | Blocker laut Datenblatt | Gemessener Ist-Stand | Status |
|---|---|---|---|
| **B1** | Branchenklassen K1–K6 nicht implementiert | `audit_industry_map.py` definiert alle sechs Klassen (K1–K6) mit Zuordnungstabelle. `audit_industry_profiles.py` hält die klassenabhängigen Maßstäbe. `audit_industry_signals.py` macht sie messbar. Fünf Testdateien sichern das ab. | ✅ **erledigt** |
| **B2** | Schwellen Frontend 85/70/50/30 ≠ Backend 95/85/70/50 | Backend `LEVELS`: 95/85/70/50/0. `audit-widget.html` Zeile 429–435: 95/85/70/50/0. `utils/homepageStandard.js`: 95/85/70/50/0. Im Widget steht sogar ein Kommentar, dass die Werte früher auf 85/70/50/30 standen und angeglichen wurden. | ✅ **erledigt** |
| **B3** | Punktabzugstabellen konstruiert, nicht aus `audit_criteria.py` extrahiert | Kein Exportskript vorhanden. Kein `shared/homepage-standard.json`. Und: die Abstufungen liegen **gar nicht als Daten vor** — siehe Befund N2. | 🔴 **offen, schwerer als beschrieben** |
| **B4** | PageSpeed-Schlüssel fehlt auf Render | Der Schlüssel existiert auf Render unter `PAGESPEED_API_KEY`. Der Fehler war ein Namensdreher: sieben Aufrufer lasen `GOOGLE_PAGESPEED_API_KEY`. `audit_pagespeed.py` Zeile 48 akzeptiert seither beide Schreibweisen. | ✅ **erledigt** |
| **B5** | Neun Rechtsaussagen ohne anwaltliche Prüfung | Nicht technisch prüfbar. Unverändert offen. | 🔴 **offen** |

**Von fünf Blockern sind drei gefallen.** Zwei bleiben: einer technisch (B3), einer anwaltlich (B5). Die im Datenblatt genannte Reihenfolge B3 → B2 → B4 → B1 → B5 verkürzt sich damit auf **B3 → B5**.

---

## 2. Neue Befunde

### 🔴 N1 — Der Katalog hat 103 Punkte, das Buch schreibt 100

Ausgeführt gegen `audit_criteria.py`:

| # | Kategorie | Buch (Kap. 2.4) | Code | Abweichung |
|---|---|---|---|---|
| 1 | Recht & Compliance | 20 Pkt / 5 Krit. | 20 / 5 | — |
| 2 | Sicherheit & Datenschutz | 10 / 4 | 10 / 4 | — |
| 3 | Performance & Core Web Vitals | 15 / 5 | 15 / 5 | — |
| 4 | Barrierefreiheit | 10 / 5 | 10 / 5 | — |
| 5 | **SEO & Auffindbarkeit** | **15 / 6** | **18 / 7** | **+3 Pkt, +1 Kriterium** |
| 6 | Design & Gestaltung | 10 / 5 | 10 / 5 | — |
| 7 | Conversion & Nutzerführung | 15 / 5 | 15 / 5 | — |
| 8 | Inhalt & Substanz | 5 / 3 | 5 / 3 | — |
| | **Gesamt** | **100 / 38** | **103 / 39** | **+3 / +1** |

Die gesamte Differenz sitzt in **einem** Kriterium: `se_ki_lesbar` — „Lesbarkeit für KI-Systeme", 3 Punkte, gemessen. Es wurde nach Fertigstellung des Manuskripts ergänzt (das GEO/GAIO-Thema). Kapitel 7 kennt nur E1 bis E6.

Betroffene Stellen im Manuskript: Kapitel 2 (Zeilen 136, 138–148, 373, 471, 483, 499, 570), Kapitel 7 vollständig, Kapitel 11 (Selbsttest), Kapitel 12, Anhang B.

Warum das ein echter Blocker ist: Der Selbsttest in Kapitel 11 lässt den Leser seine eigene Punktzahl ausrechnen. Er kommt auf ein Maximum von 100, das Werkzeug rechnet gegen 103 und normiert. Bei einem Leser mit 82 Punkten entscheidet genau diese Differenz zwischen Silber und Gold.

### 🔴 N2 — B3 ist kein Exportproblem, sondern ein Datenproblem

Die Annahme im Datenblatt lautet: „Ein Exportskript, das `audit_criteria.py` in Markdown-Tabellen überführt." Das funktioniert so nicht.

`audit_criteria.py` enthält pro Kriterium nur: Schlüssel, Bezeichnung, **Maximalpunktzahl**, Erhebungsart, Hinweis. Die **Abstufung** — also „3 Punkte ab 90, 2 ab 70, 1 ab 50" — steht nicht dort, sondern in `audit_scoring.py`, und zwar in zwei verschiedenen Formen:

```python
# Form A — als Daten, maschinell lesbar:
_set_or_skip(sheet, "tp_lcp", _tier(psi.get("lcp_seconds"), ((2.5, 4), (4.0, 2))))

# Form B — als Bedingung im Code, nicht lesbar ohne Ausführung:
sheet.set("tp_mobile", 3 if perf >= 90 else (2 if perf >= 70 else
          (1 if perf >= 50 else 0)), Source.MEASURED)
```

Ein Exportskript kann Form A auslesen. Form B kann es nicht. **Vor dem Export muss also erst Form B in Form A überführt werden.** Das ist ein eigener Arbeitsschritt und der eigentliche Aufwand hinter B3 — nicht das Skript.

### 🟠 N3 — Es gibt zwei widersprüchliche Vertriebspläne im Haus

| Quelle | Aussage |
|---|---|
| `KAS_DB_05_Buch.md`, Abschnitt 5 | „**Bewusste Entscheidung: Das Buch wird nicht über KAS verkauft.** BoD übernimmt das." Preise 39,90 € Print / 29,90 € E-Book, Buchpreisbindung. |
| `docs/Buch/BUCH-00-MASTERPLAN.md`, Phase D | Stripe-Checkout im KAS, `book_orders`-Tabelle, PDF-Auslieferung mit Wasserzeichen per Mail, eigene Netlify-Landingpage, Preis 44 €. |

Das sind sechs Prompt-Dateien (`BUCH-04` bis `BUCH-09`), die auf einer Entscheidung aufbauen, die im Datenblatt widerrufen wurde. Solange das nicht geklärt ist, kann die Hälfte der geplanten Arbeit umsonst sein.

### 🟠 N4 — Die Buch-Prompts nennen einen verworfenen Branch

`BUCH-00-MASTERPLAN.md`, Abschnitt 5 schreibt als Pflicht-Check:

> Branch → `claude/kompagnon-automation-system-FapM9`

Die geltende Projektanweisung sagt `staging`, und `claude/*`-Branches sind ausdrücklich verworfen. Alle 13 Buch-Prompt-Dateien müssen an dieser Stelle korrigiert werden, sonst stoppt jede Session am eigenen Pflicht-Check.

### 🟠 N5 — Die geplante Single Source of Truth existiert nicht

Der Masterplan sieht `shared/homepage-standard.json` als gemeinsame Definitionsdatei plus einen Drift-Check vor. Beides fehlt. Stattdessen stehen die Schwellen heute an **drei** Stellen handgepflegt: `audit_criteria.py`, `utils/homepageStandard.js`, `audit-widget.html`. Sie stimmen aktuell überein — aber nur, weil jemand sie von Hand angeglichen hat. Beim nächsten Kriterien-Update laufen sie wieder auseinander, und dann steht die falsche Zahl gedruckt im Buch.

### 🟡 N6 — Der Masterplan beschreibt einen veralteten Katalog

Er nennt „6 Kategorien, ~30 Unterkriterien" in `AuditReport.jsx`. Gemessen sind es 8 Kategorien und 39 Kriterien. Der Plan ist älter als der Code, den er beschreibt.

### 🟡 N7 — B1 ist implementiert, aber möglicherweise schmaler als das Buch behauptet

`KI_KRITERIEN_MIT_PROFIL = ("cv_klarheit", "cv_angebot")` — nur zwei KI-Kriterien bekommen den Klassenmaßstab in den Prompt. Sechs weitere rechnen klassenabhängig über `audit_industry_signals`. Die Kapitel 2, 7, 9 und 10 beschreiben klassenabhängige Maßstäbe — es ist zu prüfen, ob sie mehr versprechen als die acht Kriterien, die es tatsächlich tun. Kein Blocker, aber ein Abgleich vor Drucklegung.

---

## 3. Verbindungs-Check für das Buchprojekt

Die vier Ebenen, angewandt auf „Kunde kann das Buch kaufen":

| Ebene | Ist-Stand |
|---|---|
| Datenbank hat den Wert | ❌ Tabelle `book_orders` existiert nicht |
| Schnittstelle liefert ihn aus | ❌ kein `/api/book/checkout` |
| Frontend hat eine Adresse dafür | ❌ keine Landingpage |
| Etwas ist im Browser sichtbar | ❌ nichts |

Die Kette ist an keiner Stelle angefangen. Das ist sauber — es gibt keine halbfertige Strecke, die für fertig gehalten werden könnte. **Aber:** ob diese Kette überhaupt gebaut werden soll, hängt an der Entscheidung aus N3. Bei reinem BoD-Vertrieb bleibt sie zu Recht leer.

---

## 4. Abzuarbeitende Liste, in vorgeschlagener Reihenfolge

| # | Aufgabe | Art | Aufwand | Abhängig von |
|---|---|---|---|---|
| 1 | **Entscheidung N3:** BoD oder Eigenverkauf oder beides | Geschäftsführung | 0 | — |
| 2 | **Entscheidung N1:** `se_ki_lesbar` ins Buch oder aus den 100 heraus | Geschäftsführung | 0 | — |
| 3 | N4: Pflicht-Check in allen 13 Buch-Prompts auf `staging` korrigieren | Technik | 15 Min | — |
| 4 | N2 Teil 1: Abstufungen aus `audit_scoring.py` in Daten überführen | Technik | halber Tag | — |
| 5 | N5 + B3: Eine Definitionsquelle + Exportskript + Drift-Test | Technik | 1 Tag | 4 |
| 6 | N1 Umsetzung: Manuskripttabellen aus dem Export erzeugen | Technik + Text | 1 Tag | 5, Entsch. 2 |
| 7 | N7: Klassenversprechen in Kap. 2, 7, 9, 10 gegen den Code prüfen | Abgleich | halber Tag | — |
| 8 | B5: Anwaltstermin, neun Aussagen + Buchpreisbindung | Recht | Vorlauf | — |
| 9 | C7 / C8: eigene Auswertungen aus den KAS-Audits | Auswertung | halber Tag | genügend Audits |
| 10 | Verkaufsstrecke `BUCH-04` bis `BUCH-10` | Technik | 3–4 Tage | Entsch. 1 |
| 11 | D1: konstruierte Praxisfälle durch anonymisierte echte ersetzen | Text | 1 Tag | 9 |
| 12 | 46 Abbildungen — Manuel | Gestaltung | — | 6 |
| 13 | ISBN, BoD-Konto, `{{QR_AUDIT}}`-Ziel festlegen | Verlag | — | 1 |
| 14 | Satz, Seitenzahl auf Vielfaches von 4, Cover | Produktion | — | 12 |

Positionen 1 und 2 kosten null Aufwand und blockieren zusammen sieben der übrigen zwölf.

---

## 5. Zwei Schritte voraus

**Erstens: Das `{{QR_AUDIT}}`-Ziel ist die einzige unumkehrbare Entscheidung im ganzen Projekt.** Was gedruckt ist, ist gedruckt. Der QR-Code muss auf eine **eigene** Domain zeigen, die serverseitig weiterleitet — niemals direkt auf `websprint.kompagnon.eu`. Zieht die Anwendung je um, ist sonst jedes verkaufte Exemplar ein toter Link. Diese Entscheidung gehört vor den Satz, nicht in die Endkorrektur.

**Zweitens: Wenn das Buch mit ISBN erscheint, greift die Buchpreisbindung — und sie widerspricht dem Masterplan.** Der Masterplan baut das Buch als Funnel-Einstieg mit 44 € und Upsell. Das Datenblatt listet korrekt, dass Anrechnung des Kaufpreises auf einen Websprint ein faktischer Rabatt ist und damit unzulässig. **Beide Pläne können nicht gleichzeitig gelten.** Wer zuerst die Verkaufsstrecke baut und danach die Rechtsfrage klärt, baut möglicherweise eine Strecke, die er nicht benutzen darf. Deshalb steht der Anwaltstermin in der Liste oben vor Position 10, nicht danach.

**Drittens, kleiner, aber teuer:** Kapitel 11 enthält Ausfüllfelder für den Selbsttest. Wenn die 46 Abbildungen und der Satz stehen, ist eine Punktzahländerung keine Textkorrektur mehr, sondern ein Neusatz mit neuer Seitenzahl — und die Rückenbreite des Covers hängt an der Seitenzahl. **Alle Zahlen müssen vor Position 12 endgültig sein.**
