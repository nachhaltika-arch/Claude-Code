# BUCH-F0b — Die 103-Entscheidung protokollieren

**Aufwand:** 30 Minuten · **Ein Commit** · **Nach:** `BUCH-F0` · **Vor:** `BUCH-F1`

---

## Was hier passiert und warum

Am 21.08.2026 kam das Kriterium `se_ki_lesbar` in den Katalog. Der Code hat das ordentlich vermerkt — und die dahinterliegende Frage ausdrücklich offengelassen:

```python
#: 2026-08-21: 103 — `se_ki_lesbar` (3 P) ergaenzt, L-58 (a). Bewusst **ohne**
#:   anderswo Gewicht wegzunehmen: Welches Kriterium dafuer leichter wird, ist
#:   eine Produktentscheidung und gehoert David.
ERWARTETE_GESAMTPUNKTE: int = 103
```

**Diese Entscheidung ist am 24.08.2026 gefallen: Es wird keinem Kriterium Gewicht weggenommen. Der Standard hat 103 Rohpunkte, der Buchuntertitel wird angepasst.**

Solange das nur in einem Chatverlauf steht, ist es keine Entscheidung, sondern eine Erinnerung. Der nächste, der die Zeile „gehoert David" liest — auch Sie selbst in vier Wochen —, hält die Frage für offen und macht sie wieder auf. Deshalb wird sie festgeschrieben, bevor irgendetwas darauf aufbaut.

Das ist auch der Grund, warum dieser Schritt **vor** `BUCH-F1` steht: `F1` baut den Katalog um. Wer während eines Umbaus noch über den Sollzustand diskutiert, baut zweimal.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Den Vermerk im Code schließen

In `kompagnon/backend/services/audit_criteria.py`, oberhalb von `ERWARTETE_GESAMTPUNKTE` (etwa Zeile 318–323), den Änderungsverlauf um die Entscheidung ergänzen. Die bestehenden Zeilen **bleiben stehen** — ein Verlauf, aus dem man Einträge entfernt, ist keiner:

```python
#: 2026-08-11: 100 — Freigabe nach `docs/Audit/audit-anforderungen-2026-08-11.md`
#: 2026-08-21: 103 — `se_ki_lesbar` (3 P) ergaenzt, L-58 (a). Bewusst **ohne**
#:   anderswo Gewicht wegzunehmen: Welches Kriterium dafuer leichter wird, ist
#:   eine Produktentscheidung und gehoert David.
#: 2026-08-24: entschieden — es wird **kein** Gewicht weggenommen. 103 bleibt.
#:   Der Buchuntertitel wird auf „39 Kriterien, 8 Kategorien, 103 Punkte"
#:   geaendert (`00-titelei.md`, drei Stellen). Der angezeigte Score bleibt
#:   0–100, weil normiert wird; 103 ist die Rohpunktsumme des Katalogs.
#:   Die Praxisfall-Kette in Kap. 2/5/6 wird auf 88 Rohpunkte nachgezogen,
#:   sonst faellt Fall A von Gold auf Silber (BUCH-M3).
ERWARTETE_GESAMTPUNKTE: int = 103
```

Die Zahl selbst ändert sich nicht. Nur der offene Punkt wird geschlossen.

---

## Schritt 2 — Die Spezifikation nachziehen, wie sie es selbst verlangt

`docs/Audit/2026-08-14-bewertungslogik-homepage-standard-2026-2.md` setzt in § 0 die Regel:

> Bei Widersprüchen zum Code gilt `services/audit_criteria.py`; **Änderungen am Maßstab erfolgen hier zuerst.**

Bei `se_ki_lesbar` ist das nicht geschehen. Wir holen es nach — sonst bleibt die Regel eine, an die sich niemand hält, und dann ist sie schlimmer als keine.

**2a — § 6 des Dokuments** trennt heute nicht zwischen Lesbarkeit und Sichtbarkeit. Ergänze dort:

```markdown
> **Nachtrag 24.08.2026 — E7 `se_ki_lesbar` (3 P) ist ausgenommen.**
> Der GEO-Wert bleibt außerhalb der Wertung. Zwei Merkmale daraus sind es nicht:
> ob KI-Crawler in `robots.txt` ausgesperrt sind und ob eine `llms.txt` existiert.
> Beides ist binär, stabil messbar und veraltet nicht — es beschreibt, ob eine
> Maschine den Betrieb **lesen kann**, nicht ob sie ihn **nennt**. Nur das Zweite
> schwankt schnell genug, um in einem gedruckten Buch zu stören.
> Damit: Katalog 103 Rohpunkte, SEO E1–E7 mit 18 P.
```

**2b — § 11, offene Entscheidung Nr. 3** („Buchtitel: branchenoffen oder Handwerk im Titel?") ist beantwortet. Trage ein:

```markdown
| 3 | ~~Buchtitel branchenoffen oder Handwerk?~~ | **Entschieden 14.08.2026: branchenoffen.**
Untertitel „Der Selbsttest für Unternehmenswebsites" (`00-titelei.md`). Das Datenblatt
`KAS_DB_05_Buch.md` § 6 trägt noch „Handwerks- und Baubetriebe" und ist zu korrigieren. |
```

**Nicht in dieser Sitzung erledigen:** Die Tabellen in § 1 und § 3.1 der beiden Spezifikationsdokumente werden erst von `BUCH-F2` erzeugt und ausgetauscht. Hier wird nur die Entscheidung dokumentiert, nicht gerechnet.

---

## Schritt 3 — Prüfen

```bash
cd kompagnon/backend && python -m pytest tests/test_audit_criteria.py -v
grep -n "2026-08-24" services/audit_criteria.py
grep -n "Nachtrag 24.08.2026" ../../docs/Audit/2026-08-14-bewertungslogik-homepage-standard-2026-2.md
```

Alle Tests müssen grün bleiben — dieser Prompt ändert nur Kommentare und Prosa, keine Zahl. **Wird ein Test rot, hast du versehentlich Code angefasst.**

---

## Schritt 4 — Commit und Push

```bash
git add kompagnon/backend/services/audit_criteria.py docs/Audit/
git commit -m "docs(standard): the parked question about the 103rd point is closed"
git push origin staging
```

---

## Stopp-Punkt

Melden mit:

1. Ob die Tests grün geblieben sind
2. Ob dir in § 6 oder § 11 weitere Punkte auffallen, die faktisch längst entschieden sind, aber noch als offen geführt werden — **nur melden**
