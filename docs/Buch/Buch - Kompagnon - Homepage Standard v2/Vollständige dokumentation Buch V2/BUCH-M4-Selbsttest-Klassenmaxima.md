# BUCH-M4 — Kapitel 11: Rechenbeispiele und die sechs Klassenmaxima

**Aufwand:** halber Tag · **Ein Commit** · **Voraussetzung:** `BUCH-M3` gelaufen

---

## Was hier passiert und warum

**Zuerst eine Entwarnung, entgegen einer früheren Einschätzung von mir:** Kapitel 11 hat den Normierungsschritt bereits. Abschnitt 11.8 enthält ihn vollständig, mit zwei durchgerechneten Beispielen:

> **Beispiel 2 — IT-Beratung, Klasse K4.** E5 entfällt (3 Punkte). INP nicht verfügbar … Erreicht: 71. Anwendbar: 100 − 3 − 2 = 95. `71 ÷ 95 × 100 = 74,7` → gerundet **75 Punkte** → **Silber.**
> Ohne Umrechnung wären es 71 Punkte gewesen — und damit knapp Bronze.

Der Autor hat also genau daran gedacht. **Zu ändern sind die Zahlen, nicht die Struktur.** Das ist erheblich weniger Arbeit als befürchtet.

Zu tun bleibt zweierlei: die Beispiele auf 103 umrechnen — und eine Lücke schließen, die es schon vorher gab.

## Die Lücke: die sechs Klassenmaxima stehen nirgends

Kapitel 11.8 lässt den Leser durch sein **anwendbares Maximum** teilen. Woher er diese Zahl nimmt, steht nicht im Buch. Kapitel 7 nennt sie beiläufig für die eigene Kategorie („12 statt 15"), aber die Gesamtzahl je Klasse fehlt.

Ausgerechnet über `anwendbares_maximum()`:

| Klasse | Maximum | Was wegfällt |
|---|---|---|
| K1 Lokaler Leistungsbetrieb | **103** | nichts |
| K2 Beratung und Gesundheit | **103** | nichts |
| K3 Publikumsbetrieb | **103** | nichts |
| K4 Überregionaler Anbieter | **100** | E5 Lokale Signale (3 P) |
| K5 Onlineverkauf | **103** | nichts |
| K6 Keine Betriebsseite | **81** | alles, was einen Betrieb voraussetzt (22 P) |

**Ohne diese Tabelle kann ein Leser der Klasse K6 seinen Score nicht ausrechnen** — er teilt durch 103 statt durch 81 und kommt auf eine Punktzahl, die 27 % zu niedrig ist. Das Buch fordert ihn in Kapitel 11 ausdrücklich zum Rechnen auf und gibt ihm den Divisor nicht.

**K4 landet exakt auf 100.** Das ist Zufall — 103 minus die drei Punkte für lokale Signale. Es liest sich aber wie Absicht und wird Rückfragen erzeugen. Eine Fußnote spart sie.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Diagnose

```bash
cd docs/Buch/"Buch - Kompagnon - Der Homepage Standard"
sed -n '/## 11.8/,/## 11.9/p' 11-selbsttest.md
sed -n '/## 11.2/,/## 11.3/p' 11-selbsttest.md     # Schritt 0, Branchenklasse
grep -n "anwendbar\|Anwendbar\|Maximum" 11-selbsttest.md
```

**Melde, wo die Klassenbestimmung in 11.2 endet** — dort gehört der Verweis auf die Maximatabelle hin, nicht erst bei der Auswertung in 11.8. Wer erst am Ende erfährt, dass sein Maximum ein anderes ist, hat 120 Minuten lang gegen den falschen Maßstab angekreuzt.

---

## Schritt 2 — Die Maximatabelle einsetzen

Nach der Klassenbestimmung in Abschnitt 11.2:

```markdown
**Notieren Sie Ihr anwendbares Maximum.** Es hängt an Ihrer Klasse, weil nicht jedes
Kriterium für jeden Betrieb gilt:

| Ihre Klasse | Anwendbares Maximum |
|---|---|
| K1 Lokaler Leistungsbetrieb | 103 |
| K2 Beratung und Gesundheit | 103 |
| K3 Publikumsbetrieb | 103 |
| K4 Überregionaler Anbieter | 100 |
| K5 Onlineverkauf | 103 |
| K6 Keine Betriebsseite | 81 |

> Mein anwendbares Maximum: **______**

Dass K4 auf genau 100 kommt, ist Zufall: Von den 103 Punkten des Katalogs entfallen die
drei Punkte für lokale Signale, weil ein bundesweit arbeitender Anbieter kein
Einzugsgebiet hat. Ziehen Sie darüber hinaus jedes Kriterium ab, das Sie im Selbsttest
mit **U** — unbestimmt — markiert haben.
```

**Die Zahlen nicht eintippen.** Sie kommen aus `docs/Buch/generiert/` und werden von `BUCH-F2` erzeugt. Wenn eine Klasse später ein Kriterium mehr oder weniger bekommt, muss der Drift-Test aus `BUCH-F3` diese Tabelle rot melden können.

---

## Schritt 3 — Die beiden Rechenbeispiele umrechnen

Die Struktur bleibt, die Zahlen ziehen mit:

**Beispiel 1 — Elektrobetrieb, Klasse K1.** Anwendbares Maximum **103** statt 100. Erreicht bleibt 76 oder wird auf den in `BUCH-M3` entschiedenen Wert gesetzt. `round(76 ÷ 103 × 100)` = 74 → **Silber**.

**Beispiel 2 — IT-Beratung, Klasse K4.** Anwendbares Maximum ist **100** (E5 entfällt bereits klassenbedingt — nicht noch einmal abziehen, das ist die Falle in diesem Beispiel). INP als U: 2 Punkte weniger → **98**. Erreicht 71. `round(71 ÷ 98 × 100)` = 72 → **Silber**.

Der Schlusssatz des Beispiels — *„Ohne Umrechnung wären es 71 Punkte gewesen — und damit knapp Bronze"* — **trägt weiterhin**, denn 71 wäre Silber knapp über der Grenze und 72 ist es sicher. Prüfe die Formulierung trotzdem am neuen Zahlenpaar; sie ist die didaktische Pointe des ganzen Abschnitts.

**Achte auf den doppelten Abzug.** Beim alten Maximum 100 musste E5 für K4 explizit abgezogen werden. Beim neuen Maximum 100 ist er schon drin. Wer das übersieht, rechnet 97 statt 98 und das Buch enthält ein falsch gerechnetes Beispiel in dem Kapitel, das dem Leser das Rechnen beibringt.

---

## Schritt 4 — Die Kategorietabelle in 11.8 und das Ergebnisblatt

**4a** — Die Tabelle „Schritt 1 · Punkte zusammenzählen" führt die acht Kategorien mit ihren Maxima. **SEO steht dort auf 15 und muss auf 18.** Ersetzen durch `generiert/selbsttest.md`.

**4b** — Abschnitt 11.9 „Ihr Ergebnisblatt" und `13-massnahmenplan.md:257` („derzeit **[X] von 100 Punkten**") arbeiten mit dem **normierten** Score. **Dort bleibt 100 richtig.** Nicht ersetzen — prüfen und so lassen.

Das ist die Stelle, an der ein blindes Suchen-und-Ersetzen den meisten Schaden anrichtet: Zwei Zahlen, beide richtig, an verschiedenen Stellen.

**4c** — `11-selbsttest.md:14` („alle 38 Kriterien") → 39.

**4d** — Aus dem Restarbeiten-Report gehören zwei Punkte hierher, die bei dieser Gelegenheit erledigt werden können:

- **D7** — die Rundungsregel festlegen. Der Code rechnet `round()`, also kaufmännisch. Das gehört ausdrücklich ins Buch, weil es in Grenzfällen über die Stufe entscheidet: 84,5 wird zu 85 und damit Gold.
- **D5** — die Ausfüllfelder in Kapitel 11 als PDF-Formularfelder prüfen. **Nur melden**, ob es technisch geht; nicht umsetzen.

---

## Schritt 5 — Prüfen

Die einzige Prüfung, die wirklich zählt: **Rechne beide Beispiele mit einem Taschenrechner nach**, so wie ein Leser es täte.

```bash
python3 -c "print(round(76/103*100), round(71/98*100))"
```

Kommt etwas anderes heraus als im Buch steht, ist das Buch falsch.

```bash
cd kompagnon/backend && python -m pytest tests/test_buch_stimmt_mit_code.py -v
```

---

## Schritt 6 — Verbindungs-Check

| Ebene | Prüfung |
|---|---|
| Der Wert existiert | `anwendbares_maximum()` liefert 103/103/103/100/103/81 |
| Etwas liefert ihn aus | `generiert/selbsttest.md` enthält die sechs Maxima |
| Es gibt eine Adresse dafür | Kapitel 11.2 zeigt die Tabelle, 11.8 rechnet damit |
| Sichtbar | Ein Leser der Klasse K6 kann seinen Score ausrechnen, ohne raten zu müssen |

---

## Schritt 7 — Commit und Push

```bash
git add docs/Buch/
git commit -m "docs(buch): readers of every industry class can now compute their score"
git push origin staging
```

---

## Stopp-Punkt

Melden mit:

1. Beide Rechenbeispiele mit den neuen Zahlen, vollständig ausgeschrieben
2. Ob der Schlusssatz von Beispiel 2 didaktisch noch trägt
3. Ob es weitere Stellen gibt, an denen der Leser durch ein Maximum teilen soll, ohne es zu kennen
4. **D5:** ob PDF-Formularfelder in Kapitel 11 technisch machbar sind — nur die Einschätzung, keine Umsetzung
