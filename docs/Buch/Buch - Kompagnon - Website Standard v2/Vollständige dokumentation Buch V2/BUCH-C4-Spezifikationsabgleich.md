# BUCH-C4 — Spezifikationsabgleich und Entscheidungsvorlage

**Aufwand:** halber Tag · **Ein Commit** · **Voraussetzung:** C1, C2 und C3 gemeldet
**Beantwortet:** Frage 5 und Frage 6 des Entscheidungspapiers

---

## Was hier passiert und warum

Zwei Aufgaben in einem Prompt, weil sie zusammengehören.

**Erstens:** Fünf Abweichungen zwischen Code und freigegebener Spezifikation sind bekannt. Keine davon ist dokumentiert.

| | Spezifikation sagt | Code macht |
|---|---|---|
| **L1** | „Kammer bei Handwerk" ist Pflichtangabe | wird erhoben, zählt nicht |
| **L2** | Zwecke und Auftragsverarbeiter sind Pflichtinhalte | prüft drei andere Inhalte |
| **GEO** | ein Wert 0–10 mit zehn Merkmalen | fünf Prüfpunkte ohne Zahl |
| **Klassenmaxima** | feste Werte in § 2.4, die mit ihren eigenen Einzelwerten nicht übereinstimmen | rechnet aus, kommt auf 81 statt 78/79 |
| **`se_ki_lesbar`** | nicht erwähnt | seit 21.08. im Katalog |

Das 2026.2-Dokument setzt selbst die Regel: *„Änderungen am Maßstab erfolgen hier zuerst."* **Sie wurde in fünf von fünf Fällen nicht befolgt.** Das ist kein Einzelfehler mehr, sondern ein Verfahrensproblem — und es gehört als solches benannt.

**Zweitens:** Die Ergebnisse aus C1, C2 und C3 müssen zu **einer Zahl** zusammengeführt werden. Diese Zahl ist der Untertitel des Buchs, und sie ist nach der ISBN-Meldung nicht mehr änderbar.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Die Spezifikation vollständig gegen den Code stellen

Zwei Dokumente sind maßgeblich:

```bash
docs/Audit/audit-anforderungen-2026-08-11.md          # Freigabe, § 3.1 und § 3.2
docs/Audit/2026-08-14-bewertungslogik-...-2026-2.md   # geltender Maßstab
```

**Gehe § 3.2 des Anforderungskatalogs Zeile für Zeile durch.** Dort steht je Kriterium, was geprüft werden soll. Vergleiche mit dem, was `audit_scoring.py` tut.

Prüfe außerdem:

| Abschnitt | Zu vergleichen |
|---|---|
| § 3.1 | Gewichtungstabelle gegen die tatsächlichen Kategoriesummen |
| § 2.4 | Klassenmaxima gegen `anwendbares_maximum()` |
| § 6 | GEO-Wert gegen die tatsächliche Umsetzung |
| § 9 | die Prüfpunkte — welche sind abgehakt, welche nie erledigt |
| § 11 | die offenen Entscheidungen — welche sind faktisch längst gefallen |

**Die dritte Zeile von unten ist wichtig.** § 9 nennt einen Prüfpunkt „Lauf gegen drei echte fremde Websites aus drei Klassen". Erledigt ist er für **eine** Seite. Der eine Lauf hat fünf Erhebungsfehler freigelegt — darunter eine Fehlerseite, die als Messung zählte. **Zwei weitere Klassenläufe würden vermutlich weitere finden.**

---

## Schritt 2 — Die Verfahrensfrage benennen

Der Bericht muss nicht nur die Abweichungen auflisten, sondern die Frage stellen, warum es sie gibt.

**Feststellungen, die im Bericht stehen sollten:**

- Wie viele Abweichungen gibt es insgesamt?
- Wie viele davon sind in einem der beiden Dokumente vermerkt? *(bekannt: keine)*
- Wie viele Katalogänderungen gab es seit dem 11.08., und wie viele wurden in der Spezifikation nachgezogen?
- **Trägt die Regel „Änderungen erfolgen hier zuerst" noch, oder ist sie faktisch außer Kraft?**

**Die letzte Frage ist eine Geschäftsführungsfrage, keine technische.** Eine Regel, an die sich niemand hält, ist schlimmer als keine — sie erzeugt Vertrauen in eine Ordnung, die es nicht gibt. Entweder wird sie durchgesetzt, oder sie wird ersetzt: etwa dadurch, dass die Spezifikation künftig **aus dem Code erzeugt** wird, wie es `BUCH-F2` für das Buch vorsieht.

---

## Schritt 3 — Die Entscheidungsvorlage bauen

Neue Datei: `docs/Audit/BEFUND-C4-entscheidungsvorlage.md`

Sie führt C1, C2, C3 und C4 zusammen und beantwortet die sechs Fragen.

```markdown
# Befund C4 — Entscheidungsvorlage Katalogsumme

**Grundlage:** BEFUND-C1, C2, C3 und der Spezifikationsabgleich unten

## Die sechs Fragen

| # | Frage | Antwort |
|---|---|---|
| 1 | Kriterien, die mehr versprechen als sie messen | [n] |
| 2 | Tote Stufen und unerreichbare Punktwerte | [n] |
| 3 | Doppelwertungen, davon unbemerkt | [n] / [m] |
| 4 | Widersprüchlich deklarierte Kriterien | [n] |
| 5 | Abweichungen Spezifikation ↔ Code | [n] |
| 6 | **Katalogsumme danach** | **[n]** |

## Alle Punktänderungen auf einen Blick

| Befund | Kriterium | Heute | Vorschlag | Δ | Herkunft |
|---|---|---|---|---|---|
| A3 | tp_bilder (P5) | 3 | 4 | +1 | C1 |
| A4 | si_header (S3) | 3 | 4 | +1 | C2 |
| … | | | | | |
| | **Summe** | **103** | **[n]** | **[Δ]** | |

## Die Alternative ohne Summenänderung

| Befund | Alternative | Δ |
|---|---|---|
| A3 | Dateigröße in den Hinweis verschieben | 0 |
| … | | |

## Auswirkung auf das Manuskript

| | bei [n] Punkten |
|---|---|
| Untertitel | „39 Kriterien, 8 Kategorien, [n] Punkte" |
| Klassenmaxima | [K1]/[K2]/[K3]/[K4]/[K5]/[K6] |
| Elektro Hansen | [erreicht] / [n] = [wert] · [Stufe] |
| 30-Tage-Kette | [alt] → … → [neu] |
| Betroffene Kapitel | [Liste] |

## Spezifikationsabgleich

[Tabelle der Abweichungen]

## Verfahrensfrage

[Feststellungen aus Schritt 2]
```

**Rechne die Auswirkungstabelle tatsächlich durch**, mit `round(erreicht ÷ anwendbar × 100)`. Die Werte für Elektro Hansen stehen in den Manuskriptdateien der Kapitel 3 bis 12.

---

## Schritt 4 — Prüfen

```bash
cd kompagnon/backend && python -m pytest tests/ -k audit -v
git diff --stat kompagnon/
```

Der zweite Befehl darf nichts ausgeben. **Auch dieser Prompt ändert keinen Bewertungscode.**

---

## Schritt 5 — Commit und Push

```bash
git add docs/Audit/BEFUND-C4-entscheidungsvorlage.md
git commit -m "docs(audit): one number to decide, and everything it moves"
git push origin staging
```

---

## Stopp-Punkt

Melden mit:

1. **Die sechs Antworten** — in der Kurzform aus der Tabelle
2. **Die vorgeschlagene Katalogsumme** und die Alternative ohne Summenänderung
3. Wie viele Spezifikationsabweichungen dokumentiert waren *(erwartete Antwort: keine)*
4. **Deine Einschätzung zur Verfahrensfrage:** Trägt die Regel noch, oder soll die Spezifikation künftig aus dem Code erzeugt werden?
5. **Ob beim Abgleich Punkte aufgetaucht sind, die in keinen der vier Befunde passen**

**Danach fällt die Entscheidung — einmal, für alle Punktänderungen zusammen.** Erst danach beginnen `BUCH-F1` und `F2`, und erst danach wird das Manuskript angefasst.
