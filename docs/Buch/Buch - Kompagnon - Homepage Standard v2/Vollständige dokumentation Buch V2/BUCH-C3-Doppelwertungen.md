# BUCH-C3 — Doppelwertungen vollständig erheben

**Aufwand:** halber Tag · **Ein Commit** · **Erzeugt einen Bericht, ändert keine Bewertung**
**Beantwortet:** Frage 3 des Entscheidungspapiers

---

## Was hier passiert und warum

Der Restarbeiten-Report führt vier Doppelwertungen: **L3/S4, B4/E2, D2/B2, D4/C4.**

Beim einmaligen Durchschreiben der acht Kategoriekapitel sind drei weitere aufgefallen:

| Neu gefunden | Was doppelt wirkt |
|---|---|
| **E1 / E5** | Der Ort im Seitentitel — bei E1 dritte Prüfung, bei E5 erste Prüfung |
| **B2 / D3** | Farbkontrast — bei B2 gemessen, bei D3 als Teil der Einschätzung |
| **D1 / I2** | Veraltete Jahreszahl — bei D1 Alterungsmerkmal, bei I2 gemessen |

**Sieben statt vier.** Und alle drei neuen sind durch Lesen gefunden worden, nicht durch Suchen.

**Deshalb ist die Aufgabe hier nicht, die Liste zu ergänzen — sondern sie neu zu erheben.** Und zwar so, dass das Ergebnis nicht davon abhängt, wie aufmerksam jemand gelesen hat.

## Die Idee, die das möglich macht

Eine Doppelwertung ist nicht in erster Linie eine inhaltliche Ähnlichkeit. **Sie ist eine gemeinsame Datenquelle.**

Jedes Kriterium liest bestimmte Felder aus dem Erhebungsergebnis — `qa["title_text"]`, `contact["tel_link"]`, `third_parties["external_fonts"]` und so weiter. **Zwei Kriterien, die dasselbe Feld lesen, bewerten denselben Sachverhalt.** Das lässt sich auszählen, statt es zu beurteilen.

Damit wird aus einer Ermessensfrage eine Messung — genau wie beim Rest dieses Standards.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Für jedes Kriterium die gelesenen Felder auflisten

Gehe `audit_scoring.py` Kriterium für Kriterium durch und notiere **jedes Feld, das in seine Punktvergabe eingeht.**

```bash
cd kompagnon/backend/services
grep -n "sheet.set(\|sheet.scale(\|_set_or_skip(\|sheet.skip(" audit_scoring.py
```

Beispiel für `se_lokal`:

```
se_lokal  →  facts["city"]
             qa["title_text"]
             qa["h1_text"]
             contact["tel_link"]
             qa["google_maps"]
             qa["schema_localbusiness"]
```

**Auch mittelbare Zugriffe zählen.** Wenn ein Kriterium über eine Hilfsfunktion auf ein Feld zugreift — `_kontaktmerkmal`, `_vertrauenssignale`, `_treffer_in_klasse` —, gehört das Feld in die Liste. Diese Funktionen sind der häufigste Ort, an dem eine Überschneidung unsichtbar wird.

**Bei den sieben KI-Kriterien** gibt es keine Feldliste. Notiere stattdessen, welche Merkmale der Kriterienhinweis und das Klassenprofil nennen — und vergleiche sie mit den Feldern der gemessenen Kriterien. Genau dort liegen B2/D3, D4/C4 und D1/I2.

---

## Schritt 2 — Die Überschneidungsmatrix aufstellen

Für jedes Feld: **Welche Kriterien lesen es?** Alles mit zwei oder mehr Lesern ist ein Kandidat.

```
qa["title_text"]        → se_meta (E1), se_lokal (E5)          → 2 Leser
qa["h1_genau_eins"]     → bf_semantik (B4), se_struktur (E2)   → 2 Leser
contact["tel_link"]     → se_lokal (E5), cv_kontakt (C3)       → 2 Leser
```

**Stopp-Punkt 1: Melde die vollständige Matrix, bevor du bewertest.** Ich will sehen, wie viele Felder mehr als einen Leser haben — auch die, die sich am Ende als unproblematisch erweisen.

---

## Schritt 3 — Drei Arten unterscheiden

Nicht jede gemeinsame Datenquelle ist ein Fehler.

| Art | Bedeutung | Beispiel |
|---|---|---|
| **Bewusste Verstärkung** | Derselbe Befund soll doppelt wiegen, und das ist dokumentiert | L3/S4 bei Tracking ohne Einwilligung |
| **Zwei Blickwinkel** | Derselbe Gegenstand, verschiedene Fragen — beide berechtigt | B4/E2: Hilfsmittel gegen Suchmaschine |
| **Unbemerkte Dopplung** | Dieselbe Frage, zweimal gezählt, ohne Begründung | E1/E5: der Ort im Titel |

**Nur die dritte Art ist ein Befund.** Die ersten beiden gehören in den Bericht als „geprüft, begründet".

**Das Unterscheidungsmerkmal:** Gibt es im Code oder in der Spezifikation eine Begründung? Bei L3/S4 gibt es sie. Bei E1/E5 nicht.

---

## Schritt 4 — Den Bericht schreiben

Neue Datei: `docs/Audit/BEFUND-C3-doppelwertungen.md`

```markdown
# Befund C3 — Doppelwertungen, vollständig erhoben

**Geprüft am:** [Datum]
**Methode:** Auszählung der gemeinsam gelesenen Erhebungsfelder — nicht inhaltliche Beurteilung
**Ergebnis:** [n] Überschneidungen, davon [m] unbemerkt

## Überschneidungsmatrix

| Feld | Gelesen von | Art |
|---|---|---|
| qa["title_text"] | E1, E5 | 🔴 unbemerkt |
| third["external_fonts"] | S4 | — |
| … | | |

## Je unbemerkter Dopplung

### E1 / E5 — der Ort im Seitentitel
**Gemeinsames Feld:** qa["title_text"] in Verbindung mit facts["city"]
**E1:** dritte Prüfung, 1 Punkt, bei K1/K2/K3/K6
**E5:** erste Prüfung, 1 Punkt, bei K1/K2/K3/K5
**Betroffene Klassen:** K1, K2, K3
**Wirkung:** Wer den Ort im Titel führt, erhält zweimal einen Punkt
**Begründung im Code oder in der Spezifikation:** keine
**Möglicher Punkteffekt:** −1, falls aufgelöst

## Begründete Überschneidungen
[Liste mit Fundstelle der Begründung]

## Abgleich mit der bisherigen A7-Liste
| Bisher genannt | Bestätigt | Anmerkung |
|---|---|---|
| L3 / S4 | ✅ | dokumentierte Verstärkung |
| B4 / E2 | ✅ | zwei Blickwinkel |
| D2 / B2 | | |
| D4 / C4 | | |
| **Neu gefunden** | | |
```

**Der letzte Abschnitt ist der wichtigste des ganzen Prompts.** Er sagt, wie vollständig die bisherige Liste war — und damit, wie sehr man Listen dieser Art künftig trauen kann.

---

## Schritt 5 — Prüfen

```bash
cd kompagnon/backend && python -m pytest tests/ -k audit -v
git diff --stat kompagnon/
```

Der zweite Befehl darf nichts ausgeben.

---

## Schritt 6 — Commit und Push

```bash
git add docs/Audit/BEFUND-C3-doppelwertungen.md
git commit -m "docs(audit): overlaps counted from shared fields, not judged by reading"
git push origin staging
```

---

## Stopp-Punkt 2

Melden mit:

1. **Wie viele Überschneidungen es insgesamt gibt** und wie viele davon unbemerkt waren
2. **Wie viele der vier bisher genannten sich bestätigt haben**
3. Je unbemerkter Dopplung der mögliche Punkteffekt
4. **Ob die Methode etwas gefunden hat, das durch Lesen nicht auffallen konnte** — das ist der eigentliche Prüfstein für dieses Verfahren
5. Ob Überschneidungen zwischen gemessenen und eingeschätzten Kriterien belastbar feststellbar waren oder nur vermutet

**Nichts ändern.**
