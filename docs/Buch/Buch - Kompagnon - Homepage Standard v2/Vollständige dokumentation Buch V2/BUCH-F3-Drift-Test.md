# BUCH-F3 — Der Wächter: Buch und Software können nicht mehr auseinanderlaufen

**Aufwand:** halber Tag · **Ein Commit** · **Voraussetzung:** `BUCH-F2` erledigt
**Löst:** Befund N5 dauerhaft — und verhindert die Wiederkehr von N1

---

## Was hier passiert und warum

Befund N1 war kein Nachlässigkeitsfehler. Er ist genau so entstanden, wie solche Fehler entstehen: Das Manuskript war fertig, danach wurde ein sinnvolles Kriterium ergänzt (`se_ki_lesbar`, die KI-Lesbarkeit), und niemand hat gemerkt, dass damit das Buch falsch wurde. Zwischen der Änderung und ihrer Entdeckung lagen Wochen.

Nach `BUCH-F2` ist der Widerspruch behoben. Ohne diesen Schritt hier entsteht er beim nächsten Mal wieder.

**Was wir bauen:** einen automatischen Wächter, der bei jeder Änderung am Kriterienkatalog prüft, ob die Buchtabellen noch dazu passen — und der die Änderung ablehnt, wenn nicht. Nicht als Hinweis, den man überliest. Als roter Test, der den Vorgang stoppt.

Das ist der Unterschied zwischen „wir passen auf" und „es kann nicht mehr passieren". Bei einem gedruckten Buch ist nur das Zweite ausreichend, weil das Erste dort keine zweite Chance hat.

### Ein Wächter existiert bereits — er wird erweitert, nicht ersetzt

`audit_criteria.py` Zeile 498 und `tests/test_audit_criteria.py` Zeile 27 halten schon heute die Katalogsumme:

```python
def test_die_gesamtpunktzahl_ist_die_erklaerte():
    assert TOTAL_POINTS == ERWARTETE_GESAMTPUNKTE
```

**Dieser Test hat funktioniert.** Er hat die Änderung von 100 auf 103 gemeldet, und sie wurde ordentlich mit Datum und Grund eingetragen. Was er nicht kann: Er prüft den Code gegen sich selbst. Buch, Widget und die Spezifikationsdokumente sieht er nicht — deshalb ist die Verschiebung unbemerkt bis ins Manuskript durchgelaufen.

**Baue keinen zweiten Wächter daneben.** Erweitere diesen um die fehlenden Ebenen:

```
audit_criteria.py            ← maßgeblich · Summe bereits bewacht ✅
        │
        ├── homepage-standard.json          (erzeugt, F2)          — neu bewachen
        ├── docs/Buch/generiert/*.md        (erzeugt, F2)          — neu bewachen
        ├── utils/homepageStandard.js       (handgepflegt)          — neu bewachen
        ├── audit-widget.html               (handgepflegt)          — neu bewachen
        ├── docs/Audit/audit-anforderungen-2026-08-11.md            — neu bewachen
        └── docs/Audit/…-bewertungslogik-…-2026-2.md                — neu bewachen
```

Die letzten vier sind die eigentlichen Gefahrenstellen: Sie stimmen entweder nur überein, weil jemand sie von Hand angeglichen hat, oder sie stimmen bereits nicht mehr.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Diagnose: wo stehen die Werte heute doppelt?

```bash
echo "=== Backend, maßgeblich ==="
grep -n -A8 "^LEVELS" kompagnon/backend/services/audit_criteria.py

echo "=== Frontend-Hilfsdatei ==="
grep -n -A10 "export const STUFEN" kompagnon/frontend/src/utils/homepageStandard.js

echo "=== Widget, eigenständig ==="
grep -n -A8 "function level(s)" kompagnon/frontend/public/embed/audit-widget.html

echo "=== weitere Vorkommen der Schwellenzahlen ==="
grep -rn "95\b.*Platin\|85\b.*Gold\|70\b.*Silber\|50\b.*Bronze" kompagnon/ --include=*.js --include=*.jsx --include=*.html --include=*.py | grep -v node_modules
```

**Stopp-Punkt 1: Melde mir alle Fundstellen.** Wenn außer den drei bekannten noch weitere auftauchen — etwa im PDF-Erzeuger oder in einer Mailvorlage —, sind das zusätzliche Gefahrenstellen, die der Wächter mit abdecken muss.

---

## Schritt 2 — Der Test für Buch und Katalog

Neue Datei: `kompagnon/backend/tests/test_buch_stimmt_mit_code.py`

Sie prüft: Ist das, was in `docs/Buch/generiert/` liegt, noch das, was `standard-export.py` heute erzeugen würde?

Das Verfahren ist einfach und dadurch verlässlich: Der Test lässt den Export neu laufen, in einen temporären Ordner, und vergleicht Zeichen für Zeichen mit dem, was eingecheckt ist.

```python
def test_generierte_tabellen_sind_aktuell():
    """Wer den Katalog ändert, ändert das Buch mit — oder dieser Test wird rot.

    Genau so ist `se_ki_lesbar` entstanden: ein Kriterium kam dazu, das
    Manuskript blieb bei 100 Punkten, und es hat Wochen gedauert, bis es
    jemand nachgerechnet hat. Bei einem gedruckten Buch gibt es diese
    Wochen nicht.
    """
```

Wird der Test rot, muss die Fehlermeldung dem Menschen, der sie liest, sagen was zu tun ist — nicht nur, dass etwas nicht stimmt:

```
Die Buchtabellen sind nicht mehr aktuell.

  Abweichung in: docs/Buch/generiert/kategorien-uebersicht.md
  Katalog sagt:  SEO & Auffindbarkeit — 18 Punkte, 7 Kriterien
  Datei sagt:    SEO & Auffindbarkeit — 15 Punkte, 6 Kriterien

Beheben mit:  python scripts/standard-export.py --markdown --json
Danach prüfen, ob die Manuskriptkapitel die neuen Tabellen übernommen haben.
```

Der letzte Satz ist der wichtige. Das Skript erzeugt den Ordner `generiert/` neu — es setzt die Tabellen **nicht** automatisch in die Kapiteltexte ein. Wer das übersieht, hat einen grünen Test und ein falsches Manuskript.

---

## Schritt 3 — Der Test für Frontend und Widget

Zweite neue Datei: `kompagnon/frontend/src/utils/homepageStandard.test.js`

Sie prüft die beiden handgepflegten Stellen gegen `homepage-standard.json`:

```javascript
// Die Stufen stehen an drei Stellen im Haus. Zwei davon sind Abschriften.
// Sie standen schon einmal auseinander: das Backend staffelte 95/85/70/50,
// Widget und Akquise-Haken 85/70/50/30. Derselbe Score hieß im Bericht
// „Silber" und im Widget „Gold" — bei demselben Empfänger.
```

Zwei Prüfungen:

1. **`STUFEN` in `homepageStandard.js`** muss den Stufen aus `homepage-standard.json` entsprechen — gleiche Schwellen, gleiche Namen, gleiche Reihenfolge.
2. **Die `level()`-Funktion in `audit-widget.html`** muss dieselben Zahlen benutzen. Diese Datei ist eigenständig und kann nichts einbinden — sie muss deshalb als Text ausgelesen und die Zahlen daraus verglichen werden. Das ist unschön, aber es ist der einzige Weg, und ein unschöner Test ist besser als eine ungeprüfte Datei.

Prüfe vorher, ob im Frontend überhaupt eine Testumgebung eingerichtet ist:

```bash
cd kompagnon/frontend && grep -n "\"test\"\|vitest\|jest" package.json
ls src/utils/*.test.js
```

Es liegen bereits `paketpreise.test.js` und `tokenKontrast.test.js` dort — der Weg ist also vorhanden. Benutze dieselbe Einrichtung, richte keine zweite ein.

---

## Schritt 3b — Der Test für die Spezifikationsdokumente

Dritte Prüfung, in dieselbe Datei wie Schritt 2: Die Kategorietabellen in `docs/Audit/audit-anforderungen-2026-08-11.md` (§ 3.1 und § 3.2) und in `docs/Audit/2026-08-14-bewertungslogik-homepage-standard-2026-2.md` (§ 1) müssen zum Katalog passen.

Diese beiden Dateien sind der Grund, warum es N1 gibt: Der Code wurde geändert, die Spezifikation nicht — obwohl sie selbst vorschreibt, dass Änderungen dort zuerst erfolgen. Ein Test, der nur Code und Buch vergleicht, hätte diesen Fall wieder nicht gefangen.

Die Fehlermeldung soll ausdrücklich auf die Regel verweisen:

```
Die Spezifikation widerspricht dem Katalog.

  Datei:   docs/Audit/2026-08-14-bewertungslogik-homepage-standard-2026-2.md, § 1
  Doku:    SEO & Auffindbarkeit — 15 P, E1–E6
  Katalog: SEO & Auffindbarkeit — 18 P, E1–E7

Das Dokument schreibt selbst vor: „Änderungen am Maßstab erfolgen hier zuerst."
Entweder die Spezifikation nachziehen oder die Katalogänderung zurücknehmen.
```

---

## Schritt 4 — Den Wächter scharf schalten

Ein Test, den niemand ausführt, ist kein Wächter.

```bash
ls -la .github/workflows/
cat .github/workflows/*.yml | head -60
```

**Stopp-Punkt 2: Melde mir, was du vorfindest.** Drei Fälle sind möglich:

- **Es gibt bereits einen automatischen Testlauf.** Dann werden die beiden neuen Tests dort eingehängt — fertig.
- **Es gibt einen, aber er läuft nur für das Backend.** Dann muss der Frontend-Test ergänzt werden.
- **Es gibt keinen.** Dann ist das eine eigene Entscheidung und keine Nebensache dieser Aufgabe. Melden, nicht nebenbei einrichten.

---

## Schritt 5 — Der Beweis, dass der Wächter wirkt

Ein Test, von dem man nicht weiß, ob er rot werden kann, ist wertlos. Also machen wir ihn absichtlich rot:

```bash
cd kompagnon/backend
python -m pytest tests/test_buch_stimmt_mit_code.py -v      # muss grün sein

# jetzt ein Kriterium künstlich verändern
# in audit_criteria.py: se_links von 1 auf 2 Punkte setzen

python -m pytest tests/test_buch_stimmt_mit_code.py -v      # MUSS ROT WERDEN

# und zurück
git checkout kompagnon/backend/services/audit_criteria.py
python -m pytest tests/test_buch_stimmt_mit_code.py -v      # wieder grün
```

Dasselbe für den Frontend-Test: eine Schwelle in `homepageStandard.js` auf 84 ändern, Test muss rot werden, zurückändern, grün.

**Wird der Test bei der künstlichen Änderung nicht rot, ist er falsch gebaut.** Melde das, statt ihn zu beschönigen — ein Wächter, der schläft, ist schlimmer als keiner, weil man sich auf ihn verlässt.

---

## Schritt 6 — Verbindungs-Check

| Ebene | Prüfung |
|---|---|
| Datenbank hat den Wert | `audit_criteria.py` ist die einzige Quelle |
| Schnittstelle liefert ihn aus | `standard-export.py` erzeugt `homepage-standard.json` |
| Frontend hat eine Adresse dafür | `homepageStandard.js` und Widget lesen dieselben Zahlen — vom Test geprüft |
| Im Browser sichtbar | Widget und Bericht zeigen bei demselben Score dieselbe Stufe |

Letzte Prüfung von Hand: Ein Audit über das Widget laufen lassen und dasselbe über die Anwendung. **Beide müssen dieselbe Stufe anzeigen.** Das ist der Fehler, der schon einmal da war; er ist der Grund für diesen ganzen Prompt.

---

## Schritt 7 — Commit und Push

```bash
git add kompagnon/backend/tests/test_buch_stimmt_mit_code.py \
        kompagnon/frontend/src/utils/homepageStandard.test.js \
        .github/workflows/
git commit -m "test(standard): book and software can no longer drift apart unnoticed"
git push origin staging
```

---

## Stopp-Punkt 3

Melden mit:

1. Alle Fundstellen der Schwellenzahlen aus Schritt 1 — auch unerwartete
2. Ob beide Tests bei künstlicher Änderung tatsächlich rot werden
3. Was in `.github/workflows/` vorhanden ist und ob die Tests dort laufen
4. Ob Widget und Anwendung bei demselben Score dieselbe Stufe zeigen
