# BUCH-F2 — Exportskript: das Buch wird aus der Software erzeugt

**Aufwand:** 1 Tag · **Ein Commit** · **Voraussetzung:** `BUCH-F1` erledigt und verifiziert
**Löst:** Blocker B3, Befund N5

---

## Was hier passiert und warum

Nach `BUCH-F1` stehen alle Punktabstufungen als Daten in `audit_criteria.py`. Jetzt bauen wir das Werkzeug, das daraus Buchtabellen macht.

**Die Grundregel dahinter:** Das Manuskript wird aus der Software erzeugt, nicht neben ihr geschrieben. Solange jemand eine Tabelle von Hand ins Buch tippt, ist der nächste Widerspruch zwischen Buch und Werkzeug nur eine Frage der Zeit — und ein Widerspruch in gedruckter Form ist nicht korrigierbar.

Das Skript erzeugt zwei Dinge:

1. **`homepage-standard.json`** — eine maschinenlesbare Fassung des kompletten Standards. Diese Datei ist später die gemeinsame Grundlage für Frontend, Widget und Drift-Prüfung.
2. **Markdown-Tabellen** — genau in der Form, in der sie im Manuskript stehen, zum direkten Einsetzen in die Kapitel 2, 3–10, 11, 12 und Anhang B.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Diagnose: welche Tabellenformen braucht das Buch?

Bevor du das Skript schreibst, sieh dir an, wie die Tabellen im Manuskript heute aussehen. Sie müssen nachher dieselbe Form haben, sonst wird aus einem Austausch ein Neusatz.

```bash
cd "docs/Buch/Buch - Kompagnon - Der Homepage Standard"

echo "=== Kategorieübersicht, Kapitel 2 ==="
sed -n '130,155p' 02-das-system.md

echo "=== Kriterienübersicht einer Kategorie ==="
sed -n '11,35p' 07-seo.md

echo "=== eine Punktabstufungstabelle ==="
sed -n '130,150p' 07-seo.md

echo "=== Anhang B ==="
ls -la; grep -rn "Anhang B" *.md | head
```

**Stopp-Punkt 1: Melde mir, welche unterschiedlichen Tabellenformen du gefunden hast** und ob sie über die Kapitel hinweg einheitlich sind. Wenn Kapitel 5 seine Tabellen anders baut als Kapitel 7, muss das Skript das entweder beide können oder wir vereinheitlichen es — das ist eine Entscheidung, keine Umsetzung.

Fällt dir dabei auf, dass Anhang B in der Manuskriptliste fehlt (die Datei `90-anhang-glossar.md` ist der Glossar-Anhang, nicht der Schwellen-Anhang): **melden.** Der Restarbeiten-Report nennt drei Anhänge, im Repo liegt einer.

---

## Schritt 2 — Das Skript anlegen

Neue Datei: `scripts/standard-export.py`

Es soll über die Kommandozeile in drei Betriebsarten laufen:

```bash
python scripts/standard-export.py --json      # homepage-standard.json schreiben
python scripts/standard-export.py --markdown  # alle Buchtabellen erzeugen
python scripts/standard-export.py --pruefen   # nur vergleichen, nichts schreiben
```

**Wichtig zur Umsetzung:** `audit_criteria.py` liegt im Paket `services`, dessen `__init__.py` beim Import Datenbankmodule mitzieht. Das Skript soll ohne Datenbankverbindung laufen können. Importiere die Datei deshalb direkt über ihren Pfad (`importlib.util.spec_from_file_location`) statt über das Paket. Wenn du stattdessen einen sauberen Weg findest, `services/__init__.py` schlanker zu machen: **erst melden, nicht einfach umbauen** — an dem `__init__.py` hängt der laufende Betrieb.

### Was in `homepage-standard.json` gehört

```json
{
  "version": "2026.2",
  "erzeugt_am": "2026-08-24",
  "quelle": "kompagnon/backend/services/audit_criteria.py",
  "summe_rohpunkte": 103,
  "normierung": "round(erreicht / anwendbar * 100)",
  "stufen": [
    { "ab": 95, "name": "Homepage Standard Platin" },
    { "ab": 85, "name": "Homepage Standard Gold" },
    { "ab": 70, "name": "Homepage Standard Silber" },
    { "ab": 50, "name": "Homepage Standard Bronze" },
    { "ab": 0,  "name": "Nicht konform" }
  ],
  "kategorien": [
    {
      "schluessel": "seo",
      "bezeichnung": "SEO & Auffindbarkeit",
      "punkte": 18,
      "kriterien": [
        {
          "schluessel": "se_meta",
          "bezeichnung": "Title & Meta-Description",
          "punkte": 3,
          "erhebung": "gemessen",
          "hinweis": "…",
          "setzt_betrieb_voraus": false,
          "setzt_ortsbezug_voraus": false,
          "abstufung": { "art": "SCHWELLE", "richtung": "ab", "stufen": [ … ] }
        }
      ]
    }
  ],
  "ko_kriterien": [ … ]
}
```

Die Werte **werden berechnet, nicht eingetippt.** `summe_rohpunkte` ergibt sich aus der Addition. Wenn jemand später ein Kriterium ergänzt, ändert sich die Zahl von selbst — genau das ist der Zweck.

### Welche Markdown-Tabellen erzeugt werden

| Ausgabe | Für | Inhalt |
|---|---|---|
| `kategorien-uebersicht.md` | Kapitel 2.4 | 8 Zeilen: Kategorie, Punkte, Anzahl Kriterien |
| `kriterien-<kategorie>.md` | Kapitel 3–10, je Kapitelanfang | Code, Kriterium, Punkte, Gilt für |
| `abstufung-<kriterium>.md` | Kapitel 3–10, je Abschnitt | Punkte, Bedingung |
| `selbsttest.md` | Kapitel 11 | alle Kriterien zum Ankreuzen, mit Punktespalte |
| `anhang-schwellen.md` | Anhang B | alle Abstufungen kompakt auf wenigen Seiten |
| `stufen.md` | Kapitel 2.6 | die fünf Stufen mit Schwellen |

Ausgabeort: `docs/Buch/generiert/`. Ein eigener Ordner, damit sofort erkennbar ist, was erzeugt und was geschrieben wurde. Lege dort eine `README.md` an mit genau einem Satz: *„Alles in diesem Ordner wird von `scripts/standard-export.py` erzeugt. Änderungen von Hand gehen beim nächsten Lauf verloren."*

---

## Schritt 3 — Die Kriteriencodes

Das Buch benutzt Codes wie `E1`, `L5`, `C2`. Der Code benutzt Schlüssel wie `se_meta`, `rc_impressum`, `cv_cta`. Beide beschreiben dasselbe, aber nichts im Repo verbindet sie.

Ohne diese Zuordnung kann das Skript keine Tabelle erzeugen, die ins Buch passt.

**Lege die Zuordnung als Feld am `Criterion` an**, nicht als separate Tabelle:

```python
buch_code: str = ""     # "E1" — der Code, unter dem das Buch dieses Kriterium führt
```

Und trage sie ein, indem du sie **aus dem Manuskript ausliest**:

```bash
grep -rn "^## [0-9]*\.[0-9]* [A-Z][0-9] —" "docs/Buch/Buch - Kompagnon - Der Homepage Standard/"*.md
```

**Stopp-Punkt 2: Melde mir die vollständige Zuordnungstabelle**, bevor du sie einträgst. Zwei Dinge werden dabei auffallen und sind beide wichtig:

- **`se_ki_lesbar` hat keinen Buchcode**, weil das Kriterium nach Manuskriptschluss dazukam. Es bekommt `E7`. Das ist entschieden.
- **Möglicherweise gibt es Buchcodes ohne Codeentsprechung** — also Kriterien, die das Buch beschreibt und die es im Programm nicht (mehr) gibt. Das wären weitere Widersprüche derselben Art wie N1. Melden, nicht auflösen.

---

## Schritt 4 — Die Normierung mit ausgeben

Weil der Standard 103 Rohpunkte hat und der angezeigte Score auf 0–100 normiert wird, muss das Skript diese Umrechnung mit ausgeben. Sie ist die Zahl, die der Leser im Selbsttest braucht.

In `selbsttest.md` gehört deshalb am Ende dieser Rechenweg, erzeugt aus den echten Werten:

```markdown
| Schritt | Ihre Zahl |
|---|---|
| 1. Erreichte Punkte zusammenzählen | ______ |
| 2. Anwendbares Maximum (siehe Ihre Branchenklasse) | ______ |
| 3. Punkte ÷ Maximum × 100, kaufmännisch gerundet | ______ |
| 4. Stufe aus der Tabelle in Kapitel 2.6 ablesen | ______ |
```

Und der Text dazu — den schreibst du nicht selbst aus, sondern das Skript erzeugt ihn aus `LEVELS` und der Summe.

Zusätzlich: **das anwendbare Maximum je Branchenklasse berechnen und ausgeben.** Es steht bereits als Funktion `anwendbares_maximum(klasse)` im Code. Für K1 bis K6 ergeben sich sechs verschiedene Maxima, weil Kriterien mit `assumes_business` oder `assumes_local` je nach Klasse wegfallen. Diese sechs Zahlen gehören in Kapitel 11 und in Anhang B — ohne sie kann ein Leser der Klasse K4 seinen Score nicht ausrechnen.

---

## Schritt 4b — Die Spezifikationsdokumente mitversorgen

**Ohne diesen Schritt bleiben zwei falsche Wahrheiten im Repo liegen.**

In `docs/Audit/` stehen die beiden Dokumente, aus denen der Katalog ursprünglich freigegeben wurde. Beide tragen dieselben Tabellen wie das Buch — und beide sind seit dem 21.08. falsch:

| Datei | Falsche Stelle |
|---|---|
| `audit-anforderungen-2026-08-11.md` | § 3.1 Gewichtungstabelle (Summe 100), § 3.2 SEO-Kriterien (E1–E6, 15 P) |
| `2026-08-14-bewertungslogik-homepage-standard-2026-2.md` | § 1 Katalogtabelle (100 P, 38 Kriterien, E1–E6) |

Das zweite Dokument setzt selbst die Regel: *„Bei Widersprüchen zum Code gilt `services/audit_criteria.py`; Änderungen am Maßstab erfolgen hier zuerst."* Diese Regel wurde beim Hinzufügen von `se_ki_lesbar` nicht befolgt — deshalb ist der Widerspruch überhaupt entstanden.

**Was zu tun ist:**

1. Beide Dokumente erhalten die erzeugte Kategorieübersicht aus `generiert/kategorien-uebersicht.md` an der jeweiligen Stelle — nicht von Hand nachgetippt.
2. In beiden Dokumenten oberhalb der Tabelle eine Zeile: *„Diese Tabelle wird von `scripts/standard-export.py` erzeugt. Änderungen am Katalog gehen zuerst in `audit_criteria.py`."*
3. **N8:** `2026-08-14-bewertungslogik-homepage-standard-2026.md` (die Fassung **2026.1**) beginnt mit „Dieses Dokument ist die **einzige verbindliche Quelle**". Sie ist überholt, aber das steht nur in der *anderen* Datei. Setze in Zeile 3 dieser Datei einen Warnhinweis nach dem Vorbild von `audit-2026-05-04.md`:

```markdown
> ⚠️ **Überholt.** Ersetzt durch `2026-08-14-bewertungslogik-homepage-standard-2026-2.md`
> (Fassung 2026.2). Die Gewichtung hier — Recht 30 P, Barrierefreiheit 20 P — gilt nicht
> mehr. Diese Datei bleibt als Zeitdokument stehen.
```

**Melden, nicht selbst entscheiden:** Wenn dir beim Durchsehen weitere Stellen in diesen Dokumenten auffallen, die dem Code widersprechen — etwa die Seitenplanung in § 8 oder die K.-o.-Regeln —, dann liste sie auf. Nicht alles davon ist ein Fehler; § 8 ist eine Planung, keine Messung.

---

## Schritt 5 — Prüfen

```bash
python scripts/standard-export.py --json
python scripts/standard-export.py --markdown
ls -la docs/Buch/generiert/
cat docs/Buch/generiert/kategorien-uebersicht.md
```

Die Kategorieübersicht muss ergeben: 8 Kategorien, 39 Kriterien, **103 Punkte**, SEO mit **18 Punkten und 7 Kriterien**. Kommt etwas anderes heraus, liest das Skript nicht die richtige Quelle.

Dann der Gegentest:

```bash
diff <(python scripts/standard-export.py --json && cat docs/Buch/generiert/homepage-standard.json) \
     <(python scripts/standard-export.py --json && cat docs/Buch/generiert/homepage-standard.json)
```

Zwei Läufe müssen identische Dateien erzeugen. Steht ein Zeitstempel drin, der sich zwischen zwei Läufen ändert, erzeugt jeder Lauf einen Unterschied in der Versionsverwaltung — dann gehört das Datum in eine eigene Zeile oder ganz heraus.

---

## Schritt 6 — Verbindungs-Check

| Ebene | Prüfung |
|---|---|
| Datenbank hat den Wert | `audit_criteria.py` enthält Punkte **und** Abstufungen **und** Buchcodes |
| Schnittstelle liefert ihn aus | `standard-export.py` liest sie ohne Datenbankverbindung |
| Frontend hat eine Adresse dafür | `docs/Buch/generiert/` existiert und ist gefüllt |
| Im Browser sichtbar | die erzeugten Markdown-Dateien lassen sich lesen und stimmen mit der Messung überein |

---

## Schritt 7 — Commit und Push

```bash
git add scripts/standard-export.py \
        kompagnon/backend/services/audit_criteria.py \
        docs/Buch/generiert/
git commit -m "feat(buch): the manuscript tables are generated from the catalogue now"
git push origin staging
```

---

## Stopp-Punkt 3

Melden mit:

1. Die Zuordnungstabelle Buchcode ↔ Codeschlüssel, vollständig
2. Buchcodes ohne Codeentsprechung — falls vorhanden
3. Die sechs anwendbaren Maxima für K1 bis K6
4. Ob Anhang B als Manuskriptdatei existiert oder fehlt
5. Ob zwei Läufe identische Dateien erzeugen
