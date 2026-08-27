# BUCH — Fahrplan

**Stand:** 24.08.2026 · **Ablage im Repo:** `docs/Buch/`

**Getroffene Entscheidungen**
- Vertrieb: **beides** — Print über BoD, E-Book/PDF über KAS
- `se_ki_lesbar`: **bleibt in der Wertung**, Standard = 103 Rohpunkte, Untertitel wird angepasst
- Reihenfolge: **Fundament zuerst**

---

## Reihenfolge — nicht verhandelbar

```
F0   Branch-Korrektur in 13 Buch-Prompts      15 Min
 │    sonst blockieren sich alle Buch-Prompts selbst
F0b  Entscheidungsprotokoll 103               30 Min
 │    sonst wird die Frage in vier Wochen wieder aufgemacht
F1   Staffelungen als Daten                   halber Tag
 │    sonst kann F2 die Werte nicht auslesen
F2   Exportskript + Spezifikationen           1 Tag
 │    sonst hat F3 nichts zu vergleichen
F3   Drift-Wächter erweitern                  halber Tag
 │    danach kann sich N1 nicht wiederholen
M0   Kapitel 14, Anhang B und C               offen ⚠️
 │    kann und sollte parallel ab sofort laufen
M1   Untertitel und Titelei auf 39 / 103      45 Min
M2   Kapitel 7 um E7, 2.12 entwidersprechen   halber Tag
M3   Tabellen austauschen, Fall-A retten      1 Tag   ← Abnahme B3
M4   Selbsttest, sechs Klassenmaxima          halber Tag
```

Jeder Prompt: **ein Commit**, danach `git push origin staging`, danach Render-Log prüfen, danach melden. Nie zwei Prompts in einer Session.

`M1` bis `M4` setzen `F2` voraus — vorher gibt es keine erzeugten Tabellen zum Einsetzen.
`M0` hängt an nichts und sollte zuerst geklärt werden, weil es Schreibarbeit auslösen kann, die Wochen dauert.

---

## Stand der fünf Publikationsblocker

| ID | Blocker | Stand | Fällt durch |
|---|---|---|---|
| B1 | Branchenklassen K1–K6 | ✅ erledigt | — |
| B2 | Score-Schwellen Frontend ≠ Backend | ✅ erledigt | — |
| B3 | Punktabzugstabellen nicht aus dem Code | 🔴 offen | **M3** |
| B4 | PageSpeed-Schlüssel | ✅ erledigt | — |
| B5 | Neun Rechtsaussagen | 🔴 offen | Anwaltstermin |

**Neue Blocker, die dazugekommen sind:**

| ID | Befund | Fällt durch |
|---|---|---|
| N1 | Katalog 103 ≠ Buch 100 ≠ Spezifikation 100 | F0b, M1, M2, M3 |
| **M0** | **Kapitel 14, Anhang B und Anhang C fehlen als Dateien** | **M0 — Ihre Entscheidung** |

---

## Was danach anliegt

| Block | Inhalt | Voraussetzung |
|---|---|---|
| **BUCH-V** (Verkauf) | `book_orders`, Stripe-Checkout 7 %, PDF mit Wasserzeichen, Netlify-Landingpage, Audit→Buch-CTA — die alten `BUCH-04` bis `BUCH-10`, auf „beides" angepasst | Anwaltstermin |
| **BUCH-P** (Produktion) | 46 Abbildungen, Satz, Seitenzahl auf Vielfaches von 4, Cover, ISBN, BoD | M0–M4 abgeschlossen |
| **Belege** | C7 (Häufigkeit der 20 Fehler) und C8 (Einwilligung bei neuen Websites) aus den KAS-Audits | F2 |

---

## Drei Dinge, die ab sofort parallel laufen sollten

**1. Anwaltstermin.** Neun Rechtsaussagen aus B5 **plus** die Buchpreisbindungsfrage, die durch „beides" hinzugekommen ist: Sie verkaufen das E-Book selbst und sind zugleich der Verlag, der den Preis bindet — zulässig, solange nicht rabattiert oder auf einen Websprint angerechnet wird. Das gehört bestätigt, **bevor** die Checkout-Strecke gebaut wird, nicht danach.

**2. ISBN und BoD-Konto.** Zwei ISBN, weil Print und E-Book getrennt geführt werden. **Erst nach `M1`** — die Titelanmeldung friert den Untertitel ein.

**3. Das `{{QR_AUDIT}}`-Ziel.** Die einzige unumkehrbare Entscheidung im Projekt. Eine eigene Domain, die serverseitig weiterleitet — niemals direkt auf `websprint.kompagnon.eu`. Zieht die Anwendung je um, ist sonst jedes gedruckte Exemplar ein toter Link.

---

## Offene Meldungen, die aus den Prompts erwartet werden

Absichtlich als Meldung formuliert, nicht als Aufgabe — es sind Entscheidungen, keine Korrekturen.

| Aus | Punkt |
|---|---|
| F1 | `P5` — vier Teilprüfungen bei 3 Punkten, eine kann nicht zählen |
| F1 | `L5` — bewertet eine Einwilligungs-Checkbox, das Buch hält sie für angreifbar |
| F1 | Doppelwertungen L3/S4, B4/E2, D2/B2, D4/C4 |
| F2 | Buchcodes ohne Codeentsprechung — weitere Fälle der Art N1 |
| F2 | weitere Widersprüche in den beiden Spezifikationsdokumenten |
| F3 | unerwartete Fundstellen der Schwellenzahlen |
| M0 | wo Kapitel 14, Anhang B und C geblieben sind |
| M2 | ob der Abgrenzungsabsatz in 2.12 trägt |
| M3 | welcher Weg für die Fall-A-Kette, und ob Fall B mitzieht |
| M4 | ob PDF-Formularfelder in Kapitel 11 machbar sind |
| N7 | ob Kapitel 2, 7, 9, 10 mehr Klassenabhängigkeit versprechen, als die acht Kriterien leisten |
| N9 | Datenblatt § 6 sagt „Handwerks- und Baubetriebe", der Untertitel sagt „Unternehmenswebsites" |
