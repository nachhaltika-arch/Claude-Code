# BUCH-M3 — Punktetabellen austauschen · Fall-A-Kette retten

**Aufwand:** 1 Tag · **Ein Commit** · **Voraussetzung:** `BUCH-F2` und `BUCH-M2` gelaufen

---

## Was hier passiert und warum

Zwei Dinge, die zusammengehören.

**Erstens:** Alle Punktetabellen in den Kapiteln 2 bis 12 und in Anhang B werden durch die erzeugten Tabellen aus `docs/Buch/generiert/` ersetzt. Damit fällt Blocker B3 — ab hier stammt jede Zahl im Buch aus `audit_criteria.py` und nicht aus einer plausiblen Annahme.

**Zweitens, und das ist der gefährlichere Teil:** Die 103-Punkte-Entscheidung bricht den zentralen Praxisfall des Buchs.

## Der Praxisfall, der von Gold auf Silber fällt

`06-barrierefreiheit.md`, Zeile 467, eine redaktionelle Anmerkung, die genau davor warnt:

> …die Fall A von 76 auf 86 und damit **von Silber auf Gold** heben. **Diese Kette muss bei jeder Änderung nachgezogen werden.**

Nachgerechnet mit `round(erreicht ÷ anwendbar × 100)`:

| Fall A | bei 100 Punkten | bei 103 Punkten |
|---|---|---|
| Ausgangslage 76 Rohpunkte | 76 → **Silber** | 74 → **Silber** |
| nach dem Bildfix 86 Rohpunkte | 86 → **Gold** ✅ | 83 → **Silber** ❌ |

**Das Buch demonstriert über drei Kapitel hinweg, dass sich zehn Punkte Arbeit auszahlen — und der Betrieb landet auf derselben Stufe wie vorher.** Das ist nicht nur ein Rechenfehler; es ist der Beweis, den das Buch antritt, und er misslingt.

Reparatur: Fall A braucht **88 Rohpunkte** nach dem Bildfix, dann `round(88 ÷ 103 × 100)` = 85 → **Gold**. Der Bildfix bringt also +12 statt +10.

Die Kette liegt verteilt über drei Kapitel und mindestens fünf Stellen. Sie ist der Grund, warum dieser Prompt einen Tag braucht und nicht zwei Stunden.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Diagnose: die vollständige Punktkette

Bevor irgendetwas geändert wird, muss die Kette lückenlos auf dem Tisch liegen. Eine Zahl, die übersehen wird, ist im Druck ein Rechenfehler, den der Leser findet.

```bash
cd docs/Buch/"Buch - Kompagnon - Der Homepage Standard"

echo "=== Fall A, B, C — alle Erwähnungen ==="
grep -rn "Fall A\|Fall B\|Fall C" *.md

echo "=== Einzelpunktzahlen der Praxisfälle ==="
grep -rn "Praxisfall" *.md

echo "=== alle Punktangaben in den Fallabschnitten ==="
sed -n '/### Fall A/,/### Fall B/p' 02-das-system.md
sed -n '/Praxisfall 5/,/^## /p' 05-performance.md
sed -n '/Praxisfall 6/,/^## /p' 06-barrierefreiheit.md
```

Bekannte Bestandteile:

| Ort | Inhalt |
|---|---|
| `02-das-system.md:371` | Fall A, Elektrobetrieb, K1 — Ausgangslage und Kategorietabelle |
| `02-das-system.md:417, 432` | Fall B, „rechnerisch dasselbe Ergebnis wie Fall A" — **fällt mit** |
| `02-das-system.md:622` | Abbildungsanweisung: „zwei Netzdiagramme nebeneinander, **beide 76 Punkte**" |
| `05-performance.md:481` | Praxisfall 5.2, Punktverteilung P1 1, P2 3, P3 2, P4 1, P5 1 = 8 |
| `06-barrierefreiheit.md:464, 467` | Praxisfall 6.3, B1 1, B2 2, B3 0, B4 2, B5 1 = 6, und die Kette 76 → 86 |

**Stopp-Punkt 1: Melde die vollständige Kette mit allen Einzelpunktzahlen, bevor du rechnest.** Und melde ausdrücklich, wenn du Fall B oder Fall C betroffen findest — Fall B ist über den Satz „rechnerisch dasselbe Ergebnis" an Fall A gekoppelt, und diese Kopplung ist inhaltlich tragend (die Stelle argumentiert, dass dieselbe Punktzahl nicht dasselbe Problem bedeutet).

---

## Schritt 2 — Die Kette neu rechnen

**Ziel:** Fall A endet auf Gold. Dafür sind 85 normierte Punkte nötig, also **88 Rohpunkte** bei anwendbarem Maximum 103.

Zwei Wege dorthin. **Entscheide nicht selbst — rechne beide durch und melde sie:**

| Weg | Ausgangslage | Gewinn | Ende | Wirkung auf den Text |
|---|---|---|---|---|
| **A** | 76 bleibt | +12 statt +10 | 88 → 85 Gold | Der Bildfix muss zwei Punkte mehr hergeben. Die Einzelpunktzahlen in Kapitel 5 und 6 müssen das tragen — sonst stimmt die Addition nicht |
| **B** | 78 statt 76 | +10 bleibt | 88 → 85 Gold | Die Ausgangslage wird besser. Betrifft die Kategorietabelle in Kapitel 2 und das Netzdiagramm — und Fall B muss mitziehen |

**Die Rechnung muss in beiden Fällen aufgehen, nicht nur die Endzahl.** Wenn Kapitel 5 sagt „P1 1, P2 3, P3 2, P4 1, P5 1 = 8" und Kapitel 6 sagt „B1 1, B2 2, B3 0, B4 2, B5 1 = 6", dann sind das 14 Punkte in zwei Kategorien, die zur Kategorietabelle in Kapitel 2 passen müssen. Ein Leser, der nachrechnet — und Kapitel 11 fordert ihn dazu ausdrücklich auf —, findet jede Abweichung.

**Stopp-Punkt 2: Beide Wege durchgerechnet melden, mit allen betroffenen Einzelzahlen. Nicht umsetzen.** Das ist eine inhaltliche Entscheidung über einen Praxisfall, der über drei Kapitel trägt.

---

## Schritt 3 — Die Tabellen austauschen

Erst wenn die Kette entschieden ist.

| Stelle | Ersetzen durch |
|---|---|
| `02-das-system.md` Kategorieübersicht | `generiert/kategorien-uebersicht.md` |
| `02-das-system.md` Stufentabelle | `generiert/stufen.md` |
| Kapitel 3–10, jeweils Abschnitt .1 | `generiert/kriterien-<kategorie>.md` |
| Kapitel 3–10, jede Punktabstufung | `generiert/abstufung-<kriterium>.md` |
| Kapitel 12 | `generiert/`-Tabellen, soweit vorhanden |
| Anhang B | `generiert/anhang-schwellen.md` |

**Setze über jede ersetzte Tabelle einen Kommentar**, der beim Satz nicht mitgedruckt wird:

```markdown
<!-- ERZEUGT aus generiert/kriterien-seo.md — nicht von Hand ändern.
     Änderungen gehen in audit_criteria.py, dann standard-export.py laufen lassen. -->
```

Ohne diesen Kommentar korrigiert der Nächste die Tabelle im Manuskript, der Drift-Test aus `BUCH-F3` wird rot, und niemand weiß warum.

**Wo eine erzeugte Tabelle nicht passt** — weil das Buch eine Spalte hat, die der Export nicht kennt, oder umgekehrt: **melden, nicht anpassen.** Dann fehlt dem Export etwas, und das gehört in `standard-export.py` behoben, nicht im Manuskript umgangen.

---

## Schritt 4 — Der Rest der 103-Umrechnung

Zwei Stellen, die nicht in Schritt 3 fallen:

**`06-barrierefreiheit.md:451`** — „18 von 100 Punkten" für den PageSpeed-Ausfall. Das bleiben 18 Rohpunkte, aber der Bezug ist jetzt 103. Prüfe, ob der Satz mit „18 von 103" noch trägt oder umformuliert gehört.

**`02-das-system.md:499`** — der Einwand „100 Punkte erreicht ohnehin niemand". Als zitierter Einwand bleibt er stehen; die Antwort darunter („Platin ab 95 Punkten ist selten") bezieht sich auf den **normierten** Score und ist damit weiterhin richtig. **Prüfen, nicht automatisch ersetzen.**

---

## Schritt 5 — Prüfen

```bash
cd docs/Buch/"Buch - Kompagnon - Der Homepage Standard"

# jede Kategoriesumme im Buch gegen den Export
diff <(grep -A12 "| # | Kategorie" 02-das-system.md) ../generiert/kategorien-uebersicht.md

# die Kette rechnet auf
grep -rn "76\|86\|88\|Gold\|Silber" 02-das-system.md 05-performance.md 06-barrierefreiheit.md | grep -i "fall a"
```

Und der Test aus `BUCH-F3`:

```bash
cd kompagnon/backend && python -m pytest tests/test_buch_stimmt_mit_code.py -v
```

**Dieser Test ist der Abnahmenachweis für B3.** Wird er grün, stammt jede Zahl im Buch aus dem Code. Bleibt er rot, ist der Blocker nicht gefallen — egal wie vollständig der Austausch aussieht.

---

## Schritt 6 — Verbindungs-Check

| Ebene | Prüfung |
|---|---|
| Der Wert existiert | `audit_criteria.py` mit Abstufungen aus `BUCH-F1` |
| Etwas liefert ihn aus | `standard-export.py` erzeugt alle Tabellen |
| Es gibt eine Adresse dafür | jede Tabellenstelle im Manuskript trägt den ERZEUGT-Kommentar |
| Sichtbar | `test_buch_stimmt_mit_code.py` ist grün |

---

## Schritt 7 — Commit und Push

```bash
git add docs/Buch/
git commit -m "docs(buch): every number in the manuscript comes from the catalogue now"
git push origin staging
```

---

## Stopp-Punkt 3

Melden mit:

1. Welcher Weg für die Fall-A-Kette umgesetzt wurde und ob alle Einzelzahlen aufgehen
2. Ob Fall B und Fall C mitgezogen werden mussten
3. Wie viele Tabellen ersetzt wurden und ob eine nicht gepasst hat
4. Ob `test_buch_stimmt_mit_code.py` grün ist — **das ist die Abnahme für B3**
5. Die Abbildungsanweisung in `02-das-system.md:622` („beide 76 Punkte") — geändert oder nicht, und mit welcher Zahl. **Das ist eine Anweisung an Manuel und muss vor dem Zeichnen stimmen**
