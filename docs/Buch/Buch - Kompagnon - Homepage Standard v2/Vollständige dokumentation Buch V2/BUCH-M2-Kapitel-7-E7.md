# BUCH-M2 — Kapitel 7 um E7 · und der Selbstwiderspruch in 2.12

**Aufwand:** halber Tag (Schreibarbeit) · **Ein Commit** · **Voraussetzung:** `BUCH-F2` gelaufen

---

## Was hier passiert und warum

Kapitel 7 beschreibt heute sechs SEO-Kriterien, E1 bis E6, zusammen 15 Punkte. Der Katalog hat sieben, E1 bis E7, zusammen 18 Punkte. Das siebte ist:

```python
Criterion("se_ki_lesbar", "Lesbarkeit für KI-Systeme", 3, Source.MEASURED,
          "KI-Crawler in robots.txt nicht ausgesperrt, llms.txt vorhanden")
```

Es vergibt seine Punkte additiv:

- **2 Punkte**, wenn keine KI-Crawler in `robots.txt` gesperrt sind
- **1 Punkt**, wenn eine `llms.txt` existiert

Das Kapitel bekommt also einen neuen Abschnitt. Das ist die kleinere Hälfte dieser Aufgabe.

## Die größere Hälfte: das Buch widerspricht sich sonst selbst

`02-das-system.md`, Abschnitt **2.12 — Zwei Befunde außerhalb der Wertung**, sagt heute:

> **Der GEO-Wert** (0 bis 10) beschreibt, wie gut Ihre Website für KI-gestützte Suchsysteme aufbereitet ist … Er steht bewusst **außerhalb der 100 Punkte**, weil sich dieses Feld derzeit zu schnell verändert. Ein Kriterium, dessen Anforderungen sich innerhalb eines Jahres wandeln können, gehört nicht in einen Standard, der über Jahre vergleichbar bleiben soll — **und erst recht nicht in ein gedrucktes Buch.**

Und ab Kapitel 7 steht dann: *E7 — Lesbarkeit für KI-Systeme, 3 Punkte, in der Wertung.*

**Ein sorgfältiger Leser findet diesen Widerspruch — und es ist genau der Leser, der ein Fachbuch rezensiert.** Zwei Kapitel, zwei Aussagen, und die eine argumentiert besonders gründlich gegen das, was die andere tut.

**Der Widerspruch ist echt, aber auflösbar**, und die Auflösung steht bereits als Kommentar im Code:

> Der Name sagt **Lesbarkeit**, nicht Sichtbarkeit: Gemessen wird, ob eine Maschine den Betrieb lesen *kann*. Ob sie ihn auf eine Frage hin *nennt*, misst hier nichts.

*Darf eine Maschine lesen* — `robots.txt`, `llms.txt` — ist binär, stabil und veraltet nicht. *Nennt sie den Betrieb* schwankt mit jedem Modellwechsel. Nur das Zweite gehört nicht in ein gedrucktes Buch. **Dieser Absatz muss geschrieben werden, sonst bleibt das Buch angreifbar.**

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Zuerst 2.12, dann Kapitel 7

Die Reihenfolge ist Absicht: Wer erst E7 schreibt und dann die Abgrenzung, schreibt die Abgrenzung passend zum bereits Geschriebenen. Umgekehrt trägt die Argumentation.

In `02-das-system.md`, Abschnitt 2.12, den GEO-Absatz erweitern. Der bestehende Text bleibt — er ist richtig. Ergänzt wird die Abgrenzung:

```markdown
**Eine Ausnahme, und warum sie eine ist.** Ein einzelner Aspekt der KI-Aufbereitung steht
sehr wohl in der Wertung: Kriterium E7 in Kapitel 7 prüft, ob Ihre Website für Maschinen
überhaupt **lesbar** ist — ob Sie KI-Systeme in der `robots.txt` aussperren und ob eine
`llms.txt` vorliegt. Das ist etwas anderes als der GEO-Wert. Ob eine Maschine Ihre Seite
lesen darf, ist eine Ja-oder-Nein-Frage, die sich in zehn Jahren genauso stellt wie heute.
Ob ein bestimmtes System Sie auf eine bestimmte Frage hin nennt, ändert sich mit jeder
neuen Modellversion. Das Erste ist ein Standard, das Zweite eine Momentaufnahme.
```

**Und im Glossar**, `90-anhang-glossar.md` Zeile 72, den Eintrag zum GEO-Wert um denselben Verweis ergänzen — sonst steht dort weiter „außerhalb der 100 Punkte geführt" ohne Einschränkung.

---

## Schritt 2 — Kapitel 7 erweitern

**2a — Kapitelüberschrift und 7.1.** Alle drei Zahlen ziehen mit:

```markdown
# 7. SEO & Auffindbarkeit — 18 Punkte

## 7.1 Was hier bewertet wird

Sieben Kriterien, zusammen 18 Punkte.
```

Die Kriterientabelle darunter **nicht abtippen** — sie kommt aus `docs/Buch/generiert/kriterien-seo.md`.

Die Klassenanmerkung darunter muss nachgezogen werden. Heute steht dort: *„Ihr anwendbares Maximum in dieser Kategorie beträgt dann 12 statt 15 Punkte."* Neu: **15 statt 18.**

**2b — Abschnitt 7.2** heißt heute „Warum nur 15 Punkte auf Sichtbarkeit stehen" und begründet die Gewichtung. Er wird zu „**Warum nur 18 Punkte auf Sichtbarkeit stehen**", und die Begründung im Text muss die drei zusätzlichen Punkte mit abdecken — sonst begründet der Abschnitt eine Zahl, die nicht mehr dasteht.

**2c — Neuer Abschnitt `7.10 E7 — Lesbarkeit für KI-Systeme · 3 Punkte`**, eingefügt nach 7.9 (E6). Die folgenden Abschnitte verschieben sich: 7.10 → 7.11, 7.11 → 7.12.

Aufbau wie die anderen Kriterienabschnitte (siehe 7.8 als Vorlage). Inhaltlich gehören hinein:

| Teil | Inhalt |
|---|---|
| Worum es geht | Nicht Suchmaschinen-Ranking, sondern: Kann ein KI-System Ihren Betrieb überhaupt erfassen |
| Was geprüft wird | `robots.txt` auf Sperren gegen KI-Crawler · Existenz einer `llms.txt` |
| Punktetabelle | **aus `generiert/abstufung-se_ki_lesbar.md`**, nicht abtippen |
| Warum es zählt | Wer GPTBot aussperrt, ist für ChatGPT nicht vorhanden. Das wiegt schwerer als eine fehlende `llms.txt`, die kaum eine Seite hat — daher 2 zu 1 |
| Wie man es behebt | Beide Maßnahmen sind Dateien im Wurzelverzeichnis. Das ist der günstigste Punktgewinn im ganzen Katalog |
| Abgrenzung | Verweis auf 2.12 und Kapitel 14: Lesbarkeit ≠ Sichtbarkeit |

**Eine Warnung, die hineingehört:** Es gibt legitime Gründe, KI-Crawler auszusperren. Ein Betrieb, der das bewusst tut, verliert hier zwei Punkte und hat trotzdem recht. **Das Buch muss das sagen** — sonst empfiehlt es einem Leser, eine bewusste Entscheidung zurückzunehmen, um in einer Bewertung besser dazustehen. Das wäre genau der Vorwurf, den Kapitel 2 den unseriösen Checklisten macht.

**2d — Abschnitt 7.10 (neu 7.11) „Ihre Punkte in dieser Kategorie"** — die Summentabelle zieht auf 18 nach, ebenfalls aus dem Export.

---

## Schritt 3 — Die Querverweise

`07-seo.md:289` verweist heute auf Kapitel 14 für das GEO-Thema. Nach diesem Prompt gibt es zwei Verweisziele — E7 in diesem Kapitel und der GEO-Wert in Kapitel 14. Prüfe, ob der Verweis noch das Richtige meint.

```bash
grep -rn "E6\|sechs Kriterien\|Sechs Kriterien" docs/Buch/"Buch - Kompagnon - Der Homepage Standard"/*.md
grep -rn "Kapitel 7" docs/Buch/"Buch - Kompagnon - Der Homepage Standard"/*.md
```

**Melden, wenn ein anderes Kapitel Kapitel 7 mit „sechs Kriterien" oder „15 Punkte" zitiert.**

---

## Schritt 4 — Prüfen

```bash
cd docs/Buch/"Buch - Kompagnon - Der Homepage Standard"
grep -n "18 Punkte\|Sieben Kriterien" 07-seo.md
grep -n "15 Punkte" 07-seo.md          # darf nur noch beim K4/K6-Maximum stehen
grep -n "7\.1[0-2]" 07-seo.md          # Abschnittsnummern lückenlos
```

---

## Schritt 5 — Verbindungs-Check

| Ebene | Prüfung |
|---|---|
| Der Wert existiert | `audit_criteria.py`: `se_ki_lesbar`, 3 P, in Kategorie `seo` |
| Etwas liefert ihn aus | `generiert/kriterien-seo.md` zeigt E1–E7 mit 18 P |
| Es gibt eine Adresse dafür | Kapitel 7 hat einen Abschnitt 7.10 für E7 |
| Sichtbar | Kapitel 2.12, Kapitel 7 und der Glossar sagen dasselbe über KI-Lesbarkeit |

Die letzte Zeile ist der eigentliche Erfolgsnachweis dieses Prompts. **Lies die drei Stellen nacheinander und prüfe, ob ein Leser sie ohne Stirnrunzeln hintereinander lesen kann.**

---

## Schritt 6 — Commit und Push

```bash
git add docs/Buch/
git commit -m "docs(buch): chapter 7 has a seventh criterion and chapter 2 explains why"
git push origin staging
```

---

## Stopp-Punkt

Melden mit:

1. Ob andere Kapitel Kapitel 7 mit den alten Zahlen zitieren
2. Ob der Abgrenzungsabsatz in 2.12 aus deiner Sicht trägt — **wenn nicht, sag das.** Ein schwaches Argument an dieser Stelle ist schlechter als ein sichtbarer Widerspruch, weil es aussieht, als wäre es nachträglich zurechtgelegt worden
3. Falls du beim Schreiben feststellst, dass der Abschnitt 7.2 („Warum nur 18 Punkte") mit der neuen Zahl nicht mehr überzeugend ist: melden, nicht überspielen
