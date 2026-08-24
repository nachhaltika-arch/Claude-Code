# BUCH-C1 — Versprechen gegen Messung

**Aufwand:** halber Tag · **Ein Commit** · **Erzeugt einen Bericht, ändert keine Bewertung**
**Beantwortet:** Frage 1 und Frage 4 des Entscheidungspapiers

---

## Was hier passiert und warum

Jedes Kriterium im Katalog hat einen **Hinweis** — einen kurzen Satz, der sagt, was geprüft wird. Dieser Satz wandert an drei Stellen weiter: in den Bericht für den Kunden, in den Bewertungsprompt für die KI-Kriterien, und ins Buch.

Bei drei Kriterien ist bereits aufgefallen, dass der Hinweis mehr verspricht, als die Bewertung einlöst:

| Kriterium | Hinweis nennt | Bewertung prüft |
|---|---|---|
| **P5** `tp_bilder` | Format, Dateigröße, verzögertes Laden, feste Dimensionen — **vier** | drei Teilprüfungen, eine davon fasst zwei zusammen |
| **B4** `bf_semantik` | genau eine H1, saubere Hierarchie, `lang`-Attribut, Labels — **vier** | **zwei** |
| **E1** `se_meta` | Ort und Leistung enthalten | bei K4/K5 nur ein hinterlegtes Leistungs-Stichwort |

**Diese drei sind beim einmaligen Durchlesen der Kapitel aufgefallen — nicht durch eine systematische Prüfung.** Es ist unklar, ob es dabei bleibt. Genau das soll dieser Prompt feststellen.

**Wichtig: Es wird nichts geändert.** Keine Punktzahl, kein Hinweis, keine Bewertung. Am Ende steht ein Bericht. Die Entscheidung, was daraus folgt, fällt danach in einer einzigen Sitzung — sonst wird die Katalogsumme dreimal geändert statt einmal.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Die Versprechen sammeln

Für alle **43 Kriterien** (39 bewertete plus 4 Infrastruktur) den Hinweis auslesen und in Einzelanforderungen zerlegen.

```bash
cd kompagnon/backend/services
python3 -c "
import importlib.util
s=importlib.util.spec_from_file_location('ac','audit_criteria.py')
ac=importlib.util.module_from_spec(s); s.loader.exec_module(ac)
for c in list(ac.all_criteria()) + list(ac.INFRASTRUCTURE):
    print(f'{c.key:20}|{c.max_points}|{c.source.value:14}|{c.hint}')
"
```

**Zerlege jeden Hinweis in die Einzelanforderungen, die er nennt.** Trennzeichen sind Komma und „und". Beispiel:

> `tp_bilder` → „Format, Dateigröße, lazy loading, feste Dimensionen" → **vier Anforderungen**

**Zähle sie.** Das ist die Spalte „versprochen".

---

## Schritt 2 — Die Messungen zählen

Für jedes Kriterium in `audit_scoring.py` nachsehen, **wie viele voneinander unabhängige Prüfungen tatsächlich stattfinden.**

Maßgeblich ist: **Wie viele Dinge können unabhängig voneinander erfüllt oder nicht erfüllt sein und den Punktwert verändern?**

| Muster im Code | Zählung |
|---|---|
| `sum([...])` mit n Bedingungen | n Prüfungen |
| `_tier(wert, ((...)))` | 1 Prüfung mit mehreren Stufen |
| `a and b` innerhalb **einer** Bedingung | **1 Prüfung** — beide müssen erfüllt sein, sie zählen nicht einzeln |
| `sheet.scale(...)` auf einen Anteil | 1 Prüfung |
| `Source.AI` | Rubric — hier zählt, was im Prompt steht |

**Der dritte Fall ist der entscheidende.** Er ist die Ursache bei P5: „Größenangaben **und** keine Übergröße" sind zwei Anforderungen im Hinweis und eine Prüfung in der Bewertung.

**Für die sieben KI-Kriterien** gilt eine eigene Regel: Was das Modell tatsächlich erhält, steht in `audit_ai.py`, Funktion `_rubric()`. **Bekanntes Ergebnis: eine Zeile aus Bezeichnung und Hinweis, kein Punkterubric.** Ausnahme sind `cv_klarheit` und `cv_angebot`, deren Klassenprofil zusätzlich in den Prompt geht. **Prüfe, ob das noch stimmt.**

---

## Schritt 3 — Den Bericht schreiben

Neue Datei: `docs/Audit/BEFUND-C1-versprechen-gegen-messung.md`

```markdown
# Befund C1 — Versprechen gegen Messung

**Geprüft am:** [Datum] · **Gegen:** audit_criteria.py, audit_scoring.py, audit_ai.py
**Ergebnis:** [n] von 43 Kriterien versprechen mehr, als sie messen.

## Abweichungen

| Kriterium | Buchcode | Hinweis nennt | Bewertung prüft | Δ | Punkte |
|---|---|---|---|---|---|
| tp_bilder | P5 | 4 | 3 | −1 | 3 |
| … | | | | | |

## Je Abweichung

### tp_bilder (P5) — 3 Punkte
**Hinweis:** „Format, Dateigröße, lazy loading, feste Dimensionen"
**Gemessen:** modernes Format · verzögertes Laden · Größenangaben UND keine Übergröße
**Nicht eigenständig gewertet:** Dateigröße
**Codestelle:** audit_scoring.py Zeile [n]
**Möglicher Punkteffekt:** +1 bei Auftrennung

## Ohne Abweichung
[Liste der geprüften Kriterien, bei denen Hinweis und Messung übereinstimmen]

## Erhebungsart-Abgleich
| Kriterium | Katalog deklariert | Bewertung schreibt | Stimmt |
|---|---|---|---|
| bf_semantik | abgeleitet | gemessen | ❌ |
```

**Der letzte Abschnitt beantwortet Frage 4.** Prüfe für jedes Kriterium, ob die im Katalog deklarierte Erhebungsart mit der übereinstimmt, die `audit_scoring.py` beim Setzen schreibt.

**Warum das mehr ist als eine Formalie:** Kapitel 3 des Buchs verspricht dem Leser ausdrücklich, dass jede Erhebungsart gekennzeichnet ist und er einer Einschätzung deshalb widersprechen kann. Ein Kriterium, das im Bericht anders ausgewiesen wird als im Katalog, untergräbt genau dieses Versprechen.

---

## Schritt 4 — Prüfen

```bash
grep -c "^|" docs/Audit/BEFUND-C1-versprechen-gegen-messung.md
cd kompagnon/backend && python -m pytest tests/test_audit_criteria.py tests/test_audit_scoring.py -v
```

**Alle Tests müssen grün bleiben.** Dieser Prompt ändert keine Bewertung — wird ein Test rot, hast du versehentlich Code angefasst.

---

## Schritt 5 — Commit und Push

```bash
git add docs/Audit/BEFUND-C1-versprechen-gegen-messung.md
git commit -m "docs(audit): every criterion measured against what its hint promises"
git push origin staging
```

---

## Stopp-Punkt

Melden mit:

1. **Wie viele der 43 Kriterien mehr versprechen, als sie messen** — die Zahl allein ist die wichtigste Aussage
2. Die Summe der möglichen Punkteffekte, falls alle Abweichungen aufgelöst würden
3. Wie viele Kriterien widersprüchlich deklariert sind
4. Ob `_rubric()` in `audit_ai.py` noch immer nur eine Zeile je Kriterium liefert
5. **Falls dir beim Lesen etwas auffällt, das in keine dieser Spalten passt: melden, nicht einordnen**

**Nichts ändern.** Die Entscheidung fällt gemeinsam mit C2, C3 und C4.
