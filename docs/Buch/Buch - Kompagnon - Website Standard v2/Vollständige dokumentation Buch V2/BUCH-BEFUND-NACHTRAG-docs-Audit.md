# BEFUND-NACHTRAG — nach Auswertung von `docs/Audit`

**Datum:** 24.08.2026 · **Ergänzt:** `BUCH-BEFUND-2026-08-24.md`
**Geprüft:** vier Dokumente in `docs/Audit`, dazu `audit_criteria.py` Zeilen 315–323 und `tests/test_audit_criteria.py`

---

## 1. Der wichtigste Punkt zuerst: N1 war anders herum

Im ersten Report stand: *das Buch schreibt 100, der Code hat 103.* Das stimmt zahlenmäßig, aber die Richtung war falsch. Die Dokumente zeigen:

| Quelle | Sagt | Datum |
|---|---|---|
| `audit-anforderungen-2026-08-11.md` § 3.1 | **100 Punkte, 38 Kriterien, SEO E1–E6 mit 15 P** | 11.08., freigegeben |
| `2026-08-14-…-2026-2.md` § 1 | **100 Punkte, 38 Kriterien, SEO E1–E6 mit 15 P** | 14.08. |
| Manuskript, Kapitel 2.4 | **100 Punkte, 38 Kriterien** | 14.08. |
| **Buchuntertitel, `00-titelei.md`** | **„38 Kriterien, 8 Kategorien, 100 Punkte"** | 14.08. |
| `audit_criteria.py` | **103 Punkte, 39 Kriterien, SEO E1–E7 mit 18 P** | 21.08. |

**Drei Dokumente und das Buch sagen dasselbe. Der Code ist der Abweichler.** Das Manuskript ist nicht veraltet — es ist die einzige Stelle, die noch mit der freigegebenen Spezifikation übereinstimmt.

Das ist keine Schlamperei. Der Code dokumentiert die Änderung ausdrücklich:

```python
#: 2026-08-11: 100 — Freigabe nach `docs/Audit/audit-anforderungen-2026-08-11.md`
#: 2026-08-21: 103 — `se_ki_lesbar` (3 P) ergaenzt, L-58 (a). Bewusst **ohne**
#:   anderswo Gewicht wegzunehmen: Welches Kriterium dafuer leichter wird, ist
#:   eine Produktentscheidung und gehoert David.
ERWARTETE_GESAMTPUNKTE: int = 103
```

Die Entscheidung wurde also bewusst offengelassen und Ihnen zugewiesen. Sie haben sie jetzt beantwortet — nur ohne diese drei Dokumente vor Augen.

---

## 2. Was Ihre Entscheidung tatsächlich kostet

Ich habe nachgesehen, wo „100 Punkte" im Manuskript steht. Nicht nur in einer Tabelle in Kapitel 2.

**`00-titelei.md`, drei Mal, an den drei teuersten Stellen des Buchs:**

```
## Der Selbsttest für Unternehmenswebsites: 38 Kriterien, 8 Kategorien, 100 Punkte
```

Schmutztitel, Haupttitel, **Impressumsseite**. Der Untertitel geht mit in die ISBN-Meldung, in den BoD-Katalog, ins Verzeichnis lieferbarer Bücher und auf jede Händlerseite. Er wird zu:

> *Der Selbsttest für Unternehmenswebsites: 39 Kriterien, 8 Kategorien, **103 Punkte***

Zwei Dinge daran sind sachlich, keine Geschmacksfrage:

**Erstens: „103 Punkte" ist kein Standard mehr, sondern ein Zwischenstand.** Ein Maßstab, dessen Nennwert eine krumme Zahl ist, liest sich wie eine Skala, an der noch gearbeitet wird. Genau das Gegenteil dessen, was das Buch leisten soll — laut Ihrem eigenen Datenblatt ist der Grund für das Buch, „aus einer Behauptung eine Referenz" zu machen, und darauf stützen sich 3.500 € statt 900 €.

**Zweitens: Der Nennwert ist nach dem Druck nicht mehr änderbar** und steht in der ISBN-Metadatenmeldung. Ein Untertitel ist keine Textstelle, die man in der zweiten Auflage nachzieht — er ist die Werkidentität.

**Und die Rechnung im Buch wird komplizierter.** Der Score wird auf 0–100 normiert: `round(erreicht ÷ anwendbar × 100)`. Bei 100 Rohpunkten und voller Anwendbarkeit war Rohpunkt = Score, und der Selbsttest in Kapitel 11 war eine Addition. Bei 103 muss jeder Leser zusätzlich dividieren — auf dem Titel steht dann eine Zahl, die auf keiner Ergebnisseite je erscheint.

---

## 3. Die Spezifikation hat diese Frage bereits entschieden — anders

`2026-08-14-bewertungslogik-homepage-standard-2026-2.md`, § 6:

> **GEO-Wert (0–10, außerhalb der Wertung)**
> `llms.txt` · strukturierte Daten über das Pflichtmaß hinaus · `FAQPage` · …
> Bleibt außerhalb der 100 Punkte: Das Feld verändert sich zu schnell für einen Standard, der über Jahre vergleichbar sein soll — **und für ein gedrucktes Buch.**

Das ist wörtlich die Frage, die jetzt zur Entscheidung steht, mit einer Begründung, die genau auf das Buch zielt. Und `llms.txt` — eines der beiden Dinge, die `se_ki_lesbar` misst — steht in dieser Liste namentlich drin.

**Die Gegenseite, fairerweise:** Der Code trennt bewusst und mit Begründung:

```python
# Der Name sagt **Lesbarkeit**, nicht Sichtbarkeit: Gemessen wird,
# ob eine Maschine den Betrieb lesen *kann*. Ob sie ihn auf eine
# Frage hin *nennt*, misst hier nichts — das ist L-58 (b), kostet
# je Lauf Geld und ist ein eigenes Produkt.
```

`se_ki_lesbar` prüft nur zweierlei: ob KI-Crawler in `robots.txt` ausgesperrt sind (2 P) und ob eine `llms.txt` existiert (1 P). Das ist deutlich enger als der GEO-Wert aus § 6 und beides ist stabil messbar — es veraltet nicht so schnell wie der Rest der GEO-Liste. Das Argument, es gehöre in die Wertung, ist also nicht schwach. **Aber es ist ein Argument gegen eine schriftlich getroffene Entscheidung, und es muss diese Entscheidung ersetzen, nicht überholen.**

---

## 4. Warum B3 größer ist als gedacht: es gibt drei Wahrheiten, nicht zwei

Der erste Report ging von Buch ↔ Code aus. Tatsächlich sind es drei Ebenen:

```
audit-anforderungen-2026-08-11.md    ← Freigabe, der Katalog wurde hier beschlossen
2026-08-14-…-2026-2.md               ← der geltende Maßstab, „Vorlage für das Buch"
        │
        ├── audit_criteria.py         ← Code. Weicht seit 21.08. ab.
        └── Manuskript                ← folgt noch der Spezifikation
```

Das 2026.2-Dokument setzt selbst die Regel:

> Bei Widersprüchen zum Code gilt `services/audit_criteria.py`; **Änderungen am Maßstab erfolgen hier zuerst.**

Beim Hinzufügen von `se_ki_lesbar` wurde nach dieser Regel nicht verfahren. Das ist kein Vorwurf — es ist der Grund, warum das Exportskript aus `BUCH-F2` allein nicht genügt. **Wenn nur Code und Buch synchronisiert werden, bleiben zwei Spezifikationsdokumente mit falschen Zahlen im Repo liegen** und werden beim nächsten Mal von jemandem als Grundlage genommen.

---

## 5. Der Wächter existiert bereits — `BUCH-F3` muss ihn erweitern, nicht bauen

`audit_criteria.py` Zeile 498 und `tests/test_audit_criteria.py` Zeile 27 halten bereits:

```python
def test_die_gesamtpunktzahl_ist_die_erklaerte():
    assert TOTAL_POINTS == ERWARTETE_GESAMTPUNKTE
```

Er hat funktioniert. Er hat die Änderung von 100 auf 103 gemeldet, und jemand hat sie mit Datum und Grund eingetragen — genau wie vorgesehen.

**Was er nicht kann:** Er prüft nur den Code gegen sich selbst. Buch, Widget und die beiden Spezifikationsdokumente sieht er nicht. Deshalb ist die Verschiebung genau so unbemerkt bis ins Manuskript durchgelaufen. `BUCH-F3` erweitert diesen Wächter um die vier fehlenden Ebenen, statt einen zweiten daneben zu stellen.

---

## 6. Vier kleinere Befunde aus denselben Dokumenten

**N8 — Ein überholtes Spezifikationsdokument trägt keinen Warnhinweis.**
`2026-08-14-bewertungslogik-homepage-standard-2026.md` (Fassung 2026.1) beginnt mit: *„Dieses Dokument ist die **einzige verbindliche Quelle**."* Dass es überholt ist, steht nur in der *anderen* Datei. Wer zuerst auf die 2026.1 stößt, liest die alte Gewichtung (Recht 30 P statt 20) als verbindlich. Vergleich: `audit-2026-05-04.md` macht es richtig — dort steht der Warnhinweis in Zeile 3 der eigenen Datei. 5 Minuten Aufwand, verhindert einen teuren Irrtum.

**N9 — Der Buchuntertitel hat eine offene Entscheidung stillschweigend beantwortet.**
§ 11 des 2026.2-Dokuments führt als offene Frage: *„Buchtitel: branchenoffen oder Handwerk im Titel? Bei branchenoffener Bewertung ist ein Handwerk-Titel nicht mehr haltbar."* Das Manuskript sagt „**Unternehmenswebsites**" — also branchenoffen, richtig entschieden. **Aber Ihr Datenblatt `KAS_DB_05_Buch.md` Abschnitt 6 sagt noch:** *„für die Websites von Handwerks- und Baubetrieben"*. Der Textbaustein für die Kundenkommunikation widerspricht dem Buch, das er bewerben soll. Korrektur gehört ins Datenblatt, nicht ins Buch.

**N10 — Das 2026.2-Dokument plant 208 Seiten, geschrieben wurden 166.**
§ 8 enthält eine Seitenplanung je Kapitel (Kapitel 3: 22 Seiten, Kapitel 5: 18 …). Das Manuskript liegt bei ~166. Kein Fehler — aber bei BoD hängt die Rückenbreite des Covers an der endgültigen Seitenzahl, und die Seitenzahl muss ein Vielfaches von 4 sein. **Die Planung im Dokument ist nicht die Messung am Satz.** Erst nach dem Satz gilt eine Zahl.

**N11 — Zwei Punkte aus § 9 des 2026.2-Dokuments sind nie abgehakt worden.**
Prüfpunkt 5 („Lauf gegen 3 echte fremde Websites aus drei Klassen") ist laut `audit-anforderungen` § 6 für *eine* Seite erledigt (nachhaltika.de, K2). Für drei Klassen nicht. Prüfpunkt 6 („Quellen-Kennzeichnung im Report sichtbar") wurde am 15.08. als erledigt vermerkt. **Der erste Fremdlauf hat fünf Erhebungsfehler freigelegt** — darunter eine Fehlerseite, die als Messung zählte, und `/llm.txt` statt `/llms.txt`. Zwei weitere Klassenläufe würden vermutlich weitere finden. Das gehört vor die Drucklegung, weil das Buch behauptet, der Standard sei wiederholbar messbar.

---

## 7. Die Lehre aus § 8, die für das Buch gilt

`audit-anforderungen-2026-08-11.md` § 8 heißt: **„das PDF druckte die Vermutung."** Ein Ingenieurbüro bekam im PDF „Branche / Gewerk: **Schreiner**", weil irgendwo im Seitentext das Wort „holz" stand. Der HTML-Bericht daneben ordnete korrekt ein.

Das ist derselbe Fehlertyp wie B3, nur eine Stufe früher: **Ein Wert, den jemand geraten hat, wanderte an eine Stelle, die wie ein Befund gelesen wird — und die gedruckte Fassung war die falsche.**

Beim Buch gibt es diese Stelle 46 Mal in Abbildungen, in acht Kapiteln mit Punktetabellen und einmal auf dem Titel. Der Grund für `BUCH-F1` bis `BUCH-F3` ist nicht Ordnungsliebe. Es ist, dass dieser Fehler in Ihrem eigenen System bereits zweimal aufgetreten ist und beide Male erst durch Ihren eigenen Blick auf ein echtes Ergebnis gefunden wurde.

---

## 8. Was das an den Prompts ändert

| Prompt | Änderung |
|---|---|
| `BUCH-F1` | Diagnoseschritt ergänzt: `se_ki_lesbar` ist Form `SUMME` (2 P für nicht gesperrte KI-Crawler + 1 P für `llms.txt`), nicht `SCHWELLE`. Zusätzlich: `ERWARTETE_GESAMTPUNKTE` darf beim Umbau nicht angefasst werden. |
| `BUCH-F2` | Neuer Schritt: die beiden Spezifikationsdokumente in `docs/Audit` mitversorgen — sonst bleiben zwei falsche Wahrheiten im Repo. Plus N8: Warnhinweis in die 2026.1-Datei. |
| `BUCH-F3` | Umformuliert: den bestehenden Wächter **erweitern**, nicht neu bauen. Zu prüfende Ebenen jetzt sechs statt vier — Buch, Widget, Frontend-Hilfsdatei und die beiden Spezifikationsdokumente. |
| `BUCH-F0` | Unverändert. |

Die Prompts liegen korrigiert vor.
