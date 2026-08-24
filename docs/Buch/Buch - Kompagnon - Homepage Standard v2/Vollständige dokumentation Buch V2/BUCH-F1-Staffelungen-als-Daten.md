# BUCH-F1 — Punktabstufungen aus dem Code in Daten überführen

**Aufwand:** halber Tag · **Ein Commit** · **Voraussetzung:** `BUCH-F0` erledigt
**Löst:** Befund N2 — die Vorbedingung für B3

---

## Was hier passiert und warum

Das Buch druckt in den Kapiteln 3 bis 10 für jedes Kriterium eine kleine Tabelle: *wie viele Punkte gibt es bei welchem Befund*. Zum Beispiel für die Mobilmessung: 3 Punkte ab 90, 2 ab 70, 1 ab 50, sonst 0.

Diese Tabellen wurden beim Schreiben **plausibel konstruiert**, nicht aus dem Programm ausgelesen. Ob sie stimmen, weiß aktuell niemand. Das ist Blocker B3.

Der naheliegende Gedanke war: „Wir schreiben ein kleines Ausleseprogramm, das die Werte aus dem Code holt und Tabellen daraus macht." **Das funktioniert so nicht** — und der Grund ist der eigentliche Inhalt dieser Aufgabe.

### Warum es nicht funktioniert

Die Abstufungen stehen im Programm in zwei verschiedenen Formen nebeneinander.

**Form A — als Daten.** Die Werte stehen als Liste da und lassen sich lesen wie eine Tabelle:

```python
_tier(psi.get("lcp_seconds"), ((2.5, 4), (4.0, 2)))
                              └─ Grenzwert, Punkte ─┘
```

**Form B — als Bedingung mitten im Programmtext.** Die Werte stecken in einer Rechenanweisung:

```python
sheet.set("tp_mobile", 3 if perf >= 90 else (2 if perf >= 70 else
          (1 if perf >= 50 else 0)), Source.MEASURED)
```

Für einen Menschen sieht beides gleich aus. Für ein Ausleseprogramm nicht: Form A ist eine Liste, die man aufschlagen kann. Form B ist eine Anweisung, die man nur versteht, indem man sie ausführt. Ein Skript, das Tabellen erzeugen soll, kann Form B nicht lesen.

**In `audit_scoring.py` stehen 16 Stellen in Form B und nur 4 in Form A.** Deshalb muss vor dem Ausleseprogramm erst umgebaut werden. Das ist diese Aufgabe.

### Was sich dadurch NICHT ändern darf

Die Bewertung selbst. Nach diesem Umbau muss jede Website exakt dieselbe Punktzahl bekommen wie vorher. Wir ändern nur, **wo** die Zahlen stehen, nicht **welche**. Deshalb steht am Ende ein Beweisschritt, der das nachweist statt es zu behaupten.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Diagnose: vollständiges Inventar

**Rate nicht, welche Stellen betroffen sind — zähle sie.** Die 16 Fundstellen, die ich genannt habe, stammen aus einer Stichwortsuche und sind womöglich nicht vollständig; es gibt weitere Muster, etwa additive Summen wie bei `tp_bilder`.

```bash
cd kompagnon/backend/services

echo "=== Form B: Bedingung in sheet.set ==="
grep -n "sheet.set(.*if .* else" audit_scoring.py

echo "=== Form A: _tier ==="
grep -n "_tier(" audit_scoring.py

echo "=== sheet.scale ==="
grep -n "sheet.scale(" audit_scoring.py

echo "=== additive Summen ==="
grep -n -B2 -A8 "points = sum(\[" audit_scoring.py

echo "=== alle sheet.set-Aufrufe insgesamt ==="
grep -c "sheet.set(" audit_scoring.py
```

Erstelle daraus eine Liste: **jedes der 39 bewerteten Kriterien plus die 4 Infrastruktur-Kriterien**, und dahinter, in welcher Form seine Abstufung heute vorliegt. Es gibt vier mögliche Formen:

| Form | Bedeutung | Beispiel |
|---|---|---|
| `SCHWELLE` | Grenzwerte, absteigend geprüft | `tp_mobile`, `bf_lighthouse` |
| `JA_NEIN` | erfüllt oder nicht | `rc_bfsg`, `dg_mobil` |
| `SUMME` | mehrere Teilprüfungen addiert | `tp_bilder` |
| `ANTEIL` | Prozentwert wird skaliert | `sheet.scale`-Aufrufe |
| `KI` | Einschätzung nach Rubric, keine Schwelle | die Kriterien mit `Source.AI` |

**Stopp-Punkt 1: Melde mir diese Liste, bevor du eine Zeile änderst.** Ich will sehen, wie viele Kriterien in welcher Form vorliegen, und ob dabei Kriterien auffallen, deren Abstufung logisch fragwürdig ist. Zwei Verdachtsfälle sind bereits dokumentiert und sollen bei dieser Gelegenheit mitgeprüft werden:

- **`P5`** — laut Restarbeiten-Report nennt der Katalog vier Teilprüfungen bei nur 3 Punkten. Eine Teilprüfung kann dann nicht zählen.
- **`L5`** — bewertet heute eine Einwilligungs-Checkbox; das Buch argumentiert in Kapitel 3, dass ein Datenschutzhinweis genügt.

Beide **nur melden, nicht ändern.** Das sind Produktentscheidungen, keine Aufräumarbeiten.

### Zwei Vorgaben für dieses Inventar

**`se_ki_lesbar` ist Form `SUMME`, nicht `SCHWELLE`.** Es addiert zwei Teilprüfungen:

```python
sheet.set("se_ki_lesbar", sum([
    2 if not (_gesperrt or []) else 0,   # KI-Crawler nicht in robots.txt gesperrt
    1 if _llms else 0,                    # llms.txt vorhanden
]), Source.MEASURED)
```

Wer das als Schwellentabelle einträgt, druckt im Buch eine Tabelle, die es nicht gibt.

**`ERWARTETE_GESAMTPUNKTE` in Zeile 323 wird nicht angefasst.** Diese Konstante und der Test `test_die_gesamtpunktzahl_ist_die_erklaerte` sind der bestehende Wächter über die Katalogsumme. Er hat funktioniert und muss weiter funktionieren. Ändert sich die Zahl durch deinen Umbau, hast du versehentlich ein Gewicht verschoben — dann ist der Umbau falsch, nicht die Konstante.

---

## Schritt 2 — Die Datenform anlegen

In `audit_criteria.py` — dort, wo die Kriterien ohnehin stehen — eine Struktur ergänzen, die die Abstufung eines Kriteriums beschreibt.

Wichtig: **`audit_criteria.py` bleibt die einzige Wahrheitsquelle.** Die Abstufungen wandern dorthin, wo die Punktwerte schon sind, nicht in eine neue vierte Datei.

Vorschlag für die Struktur — passe sie an, wenn das Inventar aus Schritt 1 etwas anderes nahelegt:

```python
@dataclass(frozen=True)
class Stufe:
    """Eine Zeile der Punktabstufung eines Kriteriums.

    `grenze` ist der Wert, ab dem (bzw. bis zu dem) diese Punktzahl gilt.
    `bedingung` ist der Satz, der im Bericht UND im Buch erscheint —
    beide lesen ihn von hier, damit sie nicht auseinanderlaufen können.
    """
    punkte: int
    grenze: Optional[float]
    bedingung: str


@dataclass(frozen=True)
class Abstufung:
    art: str                    # SCHWELLE | JA_NEIN | SUMME | ANTEIL | KI
    richtung: str = "ab"        # "ab" = größer ist besser, "bis" = kleiner ist besser
    stufen: Tuple[Stufe, ...] = ()
```

Und am `Criterion` ein Feld dafür:

```python
abstufung: Optional[Abstufung] = None
```

Der Text in `bedingung` ist derjenige, der später gedruckt wird. Schreib ihn so, wie er im Buch stehen soll — vollständige, verständliche Sätze in Fachsprache, keine Programmierkürzel. Nicht `perf >= 90`, sondern `Mobil-Leistungswert 90 oder höher`.

---

## Schritt 3 — Die Abstufungen eintragen

Für jedes Kriterium aus dem Inventar die Abstufung in `audit_criteria.py` eintragen. Die Werte kommen **ausschließlich aus `audit_scoring.py`** — nicht aus dem Buch, nicht aus dem Gedächtnis, nicht aus einer Vermutung, was sinnvoll wäre.

Beispiel für `tp_mobile`:

```python
Criterion(
    "tp_mobile", "Mobile Gesamtleistung", 3, Source.MEASURED,
    "PageSpeed Insights, Mobilmessung",
    abstufung=Abstufung("SCHWELLE", "ab", (
        Stufe(3, 90, "Mobil-Leistungswert 90 oder höher"),
        Stufe(2, 70, "Mobil-Leistungswert 70 bis 89"),
        Stufe(1, 50, "Mobil-Leistungswert 50 bis 69"),
        Stufe(0, None, "Mobil-Leistungswert unter 50"),
    )),
),
```

**Bei den KI-Kriterien** (`Source.AI`) gibt es keine Schwelle, sondern ein Rubric im Prompt. Trage `Abstufung("KI")` ein und lass `stufen` leer. Das Ausleseprogramm gibt dort später den Rubric-Text aus statt einer Tabelle.

**Bei `_tier`-Kriterien (Form A) auf die Richtung achten:** `_tier` prüft `value < limit`. Bei LCP ist *kleiner besser* — `((2.5, 4), (4.0, 2))` heißt: unter 2,5 Sekunden gibt es 4 Punkte, unter 4,0 Sekunden 2, sonst 0. Hier ist `richtung="bis"`. Wer das verwechselt, dreht die Tabelle im Buch um und macht aus dem besten Wert den schlechtesten.

---

## Schritt 4 — `audit_scoring.py` auf die Daten umstellen

Jetzt liest die Bewertung die Werte aus `audit_criteria.py`, statt sie selbst zu enthalten. Eine gemeinsame Hilfsfunktion ersetzt die 16 Einzelfälle:

```python
def _nach_abstufung(sheet: _Sheet, key: str, wert, quelle: Source) -> None:
    """Punkte nach der am Kriterium hinterlegten Abstufung vergeben.

    Der Fall `wert is None` heißt: nicht erhoben. Er wird übersprungen,
    nicht mit null Punkten bewertet — sonst verkauft die Auswertung eine
    fehlende Messung als Mangel.
    """
```

Danach steht in `_score_performance` statt der Bedingung nur noch:

```python
_nach_abstufung(sheet, "tp_mobile", perf, Source.MEASURED)
```

**Die `SUMME`-Fälle wie `tp_bilder` bleiben zunächst, wie sie sind** — sie addieren Teilprüfungen und lassen sich nicht in eine Schwellentabelle pressen. Trage für sie die Abstufung als Daten ein (damit das Buch sie drucken kann), aber lass die Rechenlogik unangetastet. Sonst wird aus einem Umbau ein Umbau plus Neuentwicklung, und beides zusammen ist nicht mehr prüfbar.

---

## Schritt 5 — Der Beweis, dass sich nichts geändert hat

Das ist der wichtigste Schritt. Ohne ihn ist der Umbau nicht abgeschlossen.

**5a — Bestehende Tests müssen grün bleiben:**

```bash
cd kompagnon/backend
python -m pytest tests/test_audit_scoring.py tests/test_audit_criteria.py \
                 tests/test_audit_klassen_bewertung.py tests/test_audit_aggregat.py -v
```

Kein einziger Test darf angepasst werden, damit er wieder grün wird. Wenn ein Test rot wird, ist der Umbau falsch — nicht der Test.

**5b — Ein neuer Test, der die Gleichwertigkeit beweist.** Neue Datei `tests/test_abstufungen_identisch.py`: Für jedes umgestellte Kriterium wird über eine Reihe von Eingabewerten (unter, genau auf und über jeder Grenze) geprüft, dass die neue Datenform dieselbe Punktzahl liefert wie die alte Bedingung.

Die Grenzwerte selbst sind die gefährlichsten Stellen: `>= 90` und `> 90` unterscheiden sich um genau einen Fall, und dieser eine Fall entscheidet im Zweifel über eine Stufe. Prüfe jede Grenze exakt.

**5c — Ein Lauf gegen eine echte Website**, vorher und nachher, mit identischem Ergebnis:

```bash
git stash                          # alter Stand
# Audit gegen eine feste Test-URL laufen lassen, Ergebnis speichern
git stash pop                      # neuer Stand
# denselben Lauf wiederholen, Ergebnisse vergleichen
```

Beide Läufe müssen dieselbe Punktzahl je Kriterium und denselben Gesamtscore ergeben.

---

## Schritt 6 — Verbindungs-Check

Diese Aufgabe ändert nichts, was im Browser sichtbar wird — sie verschiebt Werte innerhalb des Backends. Die Kette lautet hier:

| Ebene | Prüfung |
|---|---|
| Datenbank hat den Wert | unverändert — dieselben Punkte je Kriterium |
| Schnittstelle liefert ihn aus | `/api/audit/...` liefert unverändert dieselben `items` |
| Frontend hat eine Adresse dafür | unverändert |
| Im Browser sichtbar | **derselbe Score wie vorher** — das ist der Erfolgsnachweis |

Führe ein Audit über die Oberfläche aus und vergleiche den Score mit einem Lauf von vor dem Umbau. Weicht er ab, ist der Umbau nicht fertig.

---

## Schritt 7 — Commit und Push

```bash
git add kompagnon/backend/services/audit_criteria.py \
        kompagnon/backend/services/audit_scoring.py \
        kompagnon/backend/tests/test_abstufungen_identisch.py
git commit -m "refactor(audit): point gradations are data now, not conditions"
git push origin staging
```

Danach Render-Deployment abwarten und die Logs prüfen. Erst wenn der Dienst sauber hochgekommen ist, geht es weiter.

---

## Stopp-Punkt 2

Melden, nicht weitermachen. Bitte mit:

1. Wie viele Kriterien umgestellt wurden, aufgeteilt nach Form
2. Ob alle bestehenden Tests grün geblieben sind — ohne Anpassung
3. Ergebnis des Vorher-Nachher-Laufs: identisch oder nicht
4. Die Meldungen zu `P5` und `L5` aus Schritt 1
5. Falls beim Eintragen der Werte eine Abstufung auffiel, die sachlich fragwürdig wirkt: melden, nicht korrigieren
