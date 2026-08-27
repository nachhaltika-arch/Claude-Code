# BEFUND-NACHTRAG 2 — Folgen der 103-Entscheidung · drei fehlende Manuskriptdateien

**Datum:** 24.08.2026 · **Ergänzt:** `BUCH-BEFUND-2026-08-24.md` und `BUCH-BEFUND-NACHTRAG-docs-Audit.md`
**Alle Zahlen unten:** ausgeführt gegen `audit_criteria.py`, nicht geschätzt

---

## 1. 🔴 Das Manuskript ist nicht vollständig — drei Dateien fehlen

Gemessen im Ordner `docs/Buch/Buch - Kompagnon - Der Homepage Standard/`:

| | Report behauptet | Tatsächlich | Differenz |
|---|---|---|---|
| Dateien | 18 | **15** | **−3** |
| Wörter | 48.094 | **43.810** | **−4.284** |

Der `RESTARBEITEN-REPORT.md` beginnt mit: *„Das Manuskript ist inhaltlich vollständig."* **Das stimmt am Gegenstand nicht.** Es fehlen genau drei Dateien:

| Fehlt | Wird referenziert in | Warum es weh tut |
|---|---|---|
| **Kapitel 14 — Grenzen des Selbermachens** | `01-warum.md` (2×), `02-das-system.md`, `07-seo.md`, `10-inhalt.md`, Glossar | Fünf Querverweise ins Leere. Und: 2.12 verweist für die GEO-Erklärung ausdrücklich dorthin — genau die Stelle, die Ihre 103-Entscheidung betrifft |
| **Anhang B — Schwellentabellen** | `RESTARBEITEN-REPORT` D3, D8, D9 | **Das ist der Anhang, den `BUCH-F2` befüllen soll.** Der Export hat kein Ziel |
| **Anhang C — Vorlagen 1–5** | `RESTARBEITEN-REPORT` D9, D10, D11 | Enthält laut Report die heraustrennbaren Vorlagen, darunter die Sicherung „Vorlage 3 darf keine Passwortfelder bekommen" |

Vorhanden ist nur `90-anhang-glossar.md` = „Anhang A — Glossar".

Der Report zitiert konkret aus Abschnitt **14.4** (Befund C8) und beschreibt Anhang B und C im Detail. Diese Texte existieren also — **aber nicht im Repo.** Entweder liegen sie außerhalb, oder sie wurden geplant und nie geschrieben. Das ist die erste Frage, die zu klären ist, und sie geht keinem Prompt voran, sondern Ihnen.

---

## 2. 🔴 Die 103-Entscheidung kippt den zentralen Praxisfall des Buchs von Gold auf Silber

`06-barrierefreiheit.md`, Zeile 467 — eine redaktionelle Anmerkung, die genau davor warnt:

> …die Fall A von 76 auf 86 und damit **von Silber auf Gold** heben. **Diese Kette muss bei jeder Änderung nachgezogen werden.**

Die Rechnung, ausgeführt:

| | bei 100 Punkten | bei 103 Punkten |
|---|---|---|
| Fall A, Ausgangslage: 76 Rohpunkte | 76 → **Silber** | `round(76÷103×100)` = 74 → **Silber** |
| nach dem Bildfix: 86 Rohpunkte | 86 → **Gold** ✅ | `round(86÷103×100)` = 83 → **Silber** ❌ |

**Der Praxisfall, an dem das Buch über drei Kapitel hinweg demonstriert, dass sich Arbeit auszahlt, zahlt sich nicht mehr aus.** Er endet auf derselben Stufe, auf der er begonnen hat.

Reparierbar ist das: Fall A braucht **88 Rohpunkte** statt 86, dann `round(88÷103×100)` = 85 → **Gold**. Der Bildfix bringt also +12 statt +10. Die Kette ist über Kapitel 2, 5 und 6 verteilt und muss an allen drei Stellen nachgezogen werden — das erledigt `BUCH-M3`.

Ich halte fest, ohne die Entscheidung neu aufzumachen: Die Alternative „bei 100 bleiben und 3 Punkte anderswo abziehen" hätte diese Kette unangetastet gelassen. Sie ist weiterhin möglich, aber ab dem Satz nicht mehr billig.

---

## 3. ✅ Eine Korrektur an mir selbst: Kapitel 11 hat den Rechenschritt bereits

Ich hatte geschrieben, Kapitel 11 brauche einen Normierungsschritt, den es nicht habe. **Das war falsch.** Abschnitt 11.8 enthält ihn vollständig, samt zweier durchgerechneter Beispiele:

> **Beispiel 2 — IT-Beratung, Klasse K4.** … Erreicht: 71. Anwendbar: 100 − 3 − 2 = 95. `71 ÷ 95 × 100 = 74,7` → gerundet **75 Punkte** → **Silber.**
> Ohne Umrechnung wären es 71 Punkte gewesen — und damit knapp Bronze.

Der Autor hat also genau daran gedacht. Zu ändern sind nur die Zahlen, nicht die Struktur — das ist erheblich weniger Arbeit, als ich zunächst angesetzt hatte.

---

## 4. Die sechs Klassenmaxima, ausgerechnet

`anwendbares_maximum()` gegen den heutigen Katalog laufen lassen:

| Klasse | Maximum | Was wegfällt |
|---|---|---|
| K1 Lokaler Leistungsbetrieb | **103** | nichts |
| K2 Beratung / Gesundheit | **103** | nichts |
| K3 Publikumsbetrieb | **103** | nichts |
| K4 Überregionaler Anbieter | **100** | E5 Lokale Signale (3 P) |
| K5 Onlineverkauf | **103** | nichts |
| K6 Keine Betriebsseite | **81** | alles, was einen Betrieb voraussetzt (22 P) |

Zwei Dinge fallen auf:

**K4 landet exakt auf 100.** Das ist Zufall, liest sich im Buch aber wie Absicht und wird Fragen erzeugen. Eine Fußnote spart Rückfragen.

**K6 verliert 22 Punkte.** Kapitel 11 muss diese Zahl nennen, sonst kann ein Leser der Klasse K6 seinen Score nicht ausrechnen. Sie steht heute nirgends im Manuskript.

---

## 5. Ein Selbstwiderspruch, den die Entscheidung erzeugt hat

`02-das-system.md`, Abschnitt 2.12, heute:

> **Der GEO-Wert** (0 bis 10) … Er steht bewusst **außerhalb der 100 Punkte**, weil sich dieses Feld derzeit zu schnell verändert. Ein Kriterium, dessen Anforderungen sich innerhalb eines Jahres wandeln können, gehört nicht in einen Standard, der über Jahre vergleichbar bleiben soll — **und erst recht nicht in ein gedrucktes Buch.**

Ab Kapitel 7 steht künftig `E7 — Lesbarkeit für KI-Systeme · 3 Punkte`, mitten in der Wertung.

**Das Buch widerspricht sich dann in zwei Kapiteln, und zwar an einer Stelle, an der es besonders sorgfältig argumentiert hat.** Ein aufmerksamer Leser findet das — und es ist genau die Sorte Leser, die ein Fachbuch rezensiert.

Auflösbar ist es mit der Unterscheidung, die der Code bereits trifft:

```python
# Der Name sagt **Lesbarkeit**, nicht Sichtbarkeit: Gemessen wird,
# ob eine Maschine den Betrieb lesen *kann*. Ob sie ihn auf eine
# Frage hin *nennt*, misst hier nichts.
```

*Ob eine Maschine lesen darf* (robots.txt, llms.txt) ist stabil und gehört in die Wertung. *Ob sie den Betrieb nennt* schwankt und bleibt draußen. Dieser Absatz muss in 2.12 hinein, sonst bleibt der Widerspruch stehen. `BUCH-M2` schreibt ihn.

---

## 6. Was daraus folgt

| # | Prompt | Inhalt |
|---|---|---|
| — | **Ihre Entscheidung** | Wo sind Kapitel 14, Anhang B, Anhang C? |
| 1 | `BUCH-F0b` | Entscheidungsprotokoll 103 im Code und in beiden Spezifikationen |
| 2 | `BUCH-M0` | Die drei fehlenden Dateien suchen, dann anlegen oder schreiben |
| 3 | `BUCH-M1` | Untertitel und Titelei auf 39 / 103 |
| 4 | `BUCH-M2` | Kapitel 7 um E7, Abschnitt 2.12 entwidersprechen |
| 5 | `BUCH-M3` | Alle Punktetabellen austauschen, Fall-A-Kette auf 88 nachziehen |
| 6 | `BUCH-M4` | Kapitel 11: Zahlen in 11.8, sechs Klassenmaxima ergänzen |

**Reihenfolge:** `F0` → `F0b` → `F1` → `F2` → `F3` → `M0` → `M1` → `M2` → `M3` → `M4`.

`M1` bis `M4` setzen `F2` voraus — vorher gibt es keine erzeugten Tabellen zum Einsetzen. `M0` kann jederzeit laufen und sollte früh laufen, weil es womöglich Schreibarbeit auslöst, die Wochen dauert.
