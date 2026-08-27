# BUCH-M1 — Untertitel und Titelei auf 39 / 103

**Aufwand:** 45 Minuten · **Ein Commit** · **Voraussetzung:** `BUCH-F2` gelaufen (die Zahlen kommen aus `generiert/`)

---

## Was hier passiert und warum

Der Buchuntertitel lautet heute an drei Stellen in `00-titelei.md`:

> **Der Selbsttest für Unternehmenswebsites: 38 Kriterien, 8 Kategorien, 100 Punkte**

Zeile 21 (Haupttitel), Zeile 35 (Impressumsseite), Zeile 172 (redaktionelle Anmerkung zur Entscheidung vom 14.08.). Dazu Zeile 136 in einer Kurzbeschreibung.

Nach der Entscheidung vom 24.08. wird daraus:

> **Der Selbsttest für Unternehmenswebsites: 39 Kriterien, 8 Kategorien, 103 Punkte**

**Warum das kein Suchen-und-Ersetzen ist:** Der Untertitel ist keine Textstelle. Er geht in die ISBN-Meldung, in den BoD-Katalog, ins Verzeichnis lieferbarer Bücher und auf jede Händlerseite. **Nach der Titelanmeldung ist er nicht mehr änderbar.** Deshalb wird er einmal sauber gesetzt, bevor irgendetwas beantragt wird — und deshalb steht dieser Prompt vor der ISBN und nicht danach.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Diagnose: alle Vorkommen finden

```bash
cd docs/Buch/"Buch - Kompagnon - Der Homepage Standard"
grep -rn "38 Kriterien\|38 Krit\|100 Punkte\|100-Punkte\|acht Kategorien" *.md
```

Bekannt sind 17 Fundstellen über sieben Dateien. **Sie sind nicht alle gleich zu behandeln** — und genau hier entsteht der Schaden, wenn jemand blind ersetzt:

| Fundstelle | Behandlung |
|---|---|
| `00-titelei.md:21, 35, 136, 172` | → **39 / 103** |
| `02-das-system.md:136, 344, 373, 525, 570` | → **39 / 103** |
| `11-selbsttest.md:14`, `13-massnahmenplan.md:226` | → **39** |
| `02-das-system.md:471, 483` | **unverändert** — dort geht es um die Abgrenzung des GEO-Werts, nicht um die Katalogsumme. `BUCH-M2` fasst diese Stelle an |
| `02-das-system.md:499` | **prüfen** — „100 Punkte erreicht ohnehin niemand" ist ein Zitat eines Einwands. Als Einwand bleibt es; im Antwortsatz muss die Zahl stimmen |
| `06-barrierefreiheit.md:451` | **umrechnen** — „18 von 100 Punkten" beschreibt den PageSpeed-Ausfall. Das sind weiterhin 18 Rohpunkte, aber jetzt von 103 |
| `13-massnahmenplan.md:257` | **prüfen** — „[X] von 100 Punkten" ist eine Textvorlage für den Leser. Hier gehört der **normierte** Score hin, also bleibt 100 richtig |
| `90-anhang-glossar.md:72` | **unverändert** — GEO-Abgrenzung, wie oben |
| `RESTARBEITEN-REPORT.md:38` | **unverändert** — Zeitdokument |

**Stopp-Punkt 1: Melde mir diese Einordnung, bevor du ersetzt.** Wenn deine Zählung von 17 abweicht oder du eine Fundstelle findest, die in keine der Zeilen oben passt, will ich das vorher wissen.

Die Unterscheidung, auf die es ankommt: **103 ist die Rohpunktsumme des Katalogs, 100 ist die Skala des angezeigten Scores.** Beide Zahlen sind richtig — an verschiedenen Stellen. Wer sie verwechselt, macht aus einem behebbaren Fehler einen unauffälligen.

---

## Schritt 2 — Die Titelei

**2a — Untertitel** an allen drei Satzstellen (Schmutztitel, Haupttitel, Impressumsseite) identisch setzen. Sie **müssen** wörtlich übereinstimmen; eine Abweichung zwischen Titelseite und Impressum fällt beim Pflichtexemplar auf.

**2b — Die redaktionelle Anmerkung in Zeile 171 ff.** dokumentiert heute die Untertitel-Entscheidung vom 14.08. Sie wird nicht überschrieben, sondern fortgeschrieben:

```markdown
**Untertitel entschieden am 14.08.2026:** „Der Selbsttest für Unternehmenswebsites:
38 Kriterien, 8 Kategorien, 100 Punkte" (Prüfrichtung). Gesetzt in Schmutztitel, …

**Geändert am 24.08.2026 auf „39 Kriterien, 8 Kategorien, 103 Punkte".** Grund: `se_ki_lesbar`
(E7, 3 P) kam am 21.08. in den Katalog und wurde am 24.08. bewusst ohne Ausgleich
aufgenommen. 103 ist die Rohpunktsumme; der angezeigte Score bleibt 0–100 (normiert).
Der Untertitel geht in die ISBN-Meldung — **nach der Titelanmeldung nicht mehr änderbar.**
```

**2c — Zeile 136**, die Kurzbeschreibung des Bewertungssystems, mitziehen.

---

## Schritt 3 — Der Satz, der jetzt gebraucht wird

Ein Leser sieht auf dem Titel 103 und auf jeder Ergebnisseite 0–100. **Diese Frage muss das Buch selbst beantworten, und zwar früh** — nicht erst in Kapitel 11, wo gerechnet wird.

In `02-das-system.md`, im Abschnitt, der den Katalog einführt (heute Zeile 136 ff.), nach der Kategorietabelle:

```markdown
**Warum 103 und nicht 100.** Die Kategorien ergeben zusammen 103 Punkte. Ihr Ergebnis
wird trotzdem als Wert zwischen 0 und 100 ausgewiesen: Erreichte Punkte geteilt durch
die für Sie anwendbaren Punkte, mal 100. Das ist keine Schönheitskorrektur, sondern
notwendig — je nach Branchenklasse gelten nicht alle Kriterien, und ein Maßstab, dessen
Höchstwert von der Branche abhängt, wäre nicht vergleichbar. Wie Sie selbst umrechnen,
steht in Abschnitt 11.8.
```

Die Zahl 103 in diesem Absatz **nicht eintippen** — sie kommt aus `docs/Buch/generiert/kategorien-uebersicht.md`. Wenn sich der Katalog wieder ändert, muss `BUCH-F3` diesen Absatz rot melden können.

---

## Schritt 4 — Prüfen

```bash
cd docs/Buch/"Buch - Kompagnon - Der Homepage Standard"

# Untertitel muss dreimal wortgleich sein
grep -c "39 Kriterien, 8 Kategorien, 103 Punkte" 00-titelei.md    # erwartet: 3

# keine verwaisten alten Zahlen mehr, außer den bewusst belassenen
grep -rn "38 Kriterien" *.md | grep -v RESTARB
```

Zweiter Befehl darf **nichts** ausgeben. Bleibt eine Fundstelle übrig, prüfe gegen die Tabelle in Schritt 1, ob sie dorthin gehört.

---

## Schritt 5 — Verbindungs-Check

| Ebene | Prüfung |
|---|---|
| Der Wert existiert | `audit_criteria.py` → 103, 39 Kriterien |
| Etwas liefert ihn aus | `generiert/kategorien-uebersicht.md` nennt dieselben Zahlen |
| Es gibt eine Adresse dafür | Titelei und Kapitel 2 nennen sie ebenfalls |
| Sichtbar | Untertitel und Kapitel 2 widersprechen sich nicht |

---

## Schritt 6 — Commit und Push

```bash
git add docs/Buch/
git commit -m "docs(buch): the subtitle states the catalogue's real point total"
git push origin staging
```

---

## Stopp-Punkt 2

Melden mit:

1. Anzahl geänderter und bewusst unveränderter Fundstellen
2. Ob eine Fundstelle in keine Zeile der Tabelle aus Schritt 1 passte
3. **Ausdrücklich:** ob der Untertitel jetzt an allen drei Satzstellen wortgleich steht

Danach ist der Untertitel festgeschrieben. **Erst danach darf die ISBN beantragt werden.**
