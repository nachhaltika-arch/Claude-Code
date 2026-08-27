# BUCH-C2 — Tote Stufen in den Punktstaffelungen

**Aufwand:** halber Tag · **Ein Commit** · **Erzeugt einen Bericht, ändert keine Bewertung**
**Beantwortet:** Frage 2 des Entscheidungspapiers

---

## Was hier passiert und warum

Bei **S3** — den vier Sicherheitsheadern — ist aufgefallen, dass zwei und drei gesetzte Header **dieselbe Punktzahl** ergeben:

| Gesetzte Header | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| Punkte | 0 | 1 | 2 | **2** | 3 |

Die Ursache ist eine Rundung: Drei Punkte werden anteilig auf vier Header verteilt. Zwei von vier ergeben 1,5 und werden zu 2. Drei von vier ergeben 2,25 und werden ebenfalls zu 2.

**Der dritte Header ist damit wertlos.** Das ist keine Entwurfsentscheidung, sondern eine Nebenwirkung.

Bei **C2** — der erwarteten Hauptreaktion — gibt es ein verwandtes Problem: Die Staffelung ist 3 / 2 / 0. **Den Punktwert 1 gibt es nicht**, obwohl das Kriterium drei Punkte umfasst.

Bei **P1** und **P2** springt die Staffelung ebenfalls (4/2/0 und 3/1/0). Dort ist es begründet — die Schwellen stammen aus dem Messverfahren — und gehört ausdrücklich **nicht** zu den Befunden.

**Dieser Prompt stellt fest, wie viele solcher Stellen es insgesamt gibt.** Zwei sind bekannt. Ob es dabei bleibt, weiß niemand.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Jede Staffelung vollständig durchrechnen

**Nicht lesen — ausrechnen.** Für jedes Kriterium alle möglichen Eingaben durchspielen und die entstehende Punktzahl aufschreiben.

Vier Muster kommen vor:

| Muster | Vorgehen |
|---|---|
| `_tier(wert, ((g1,p1),(g2,p2)))` | Werte knapp unter, genau auf und knapp über jeder Grenze einsetzen |
| `sheet.scale(key, anteil)` | Anteil 0,0 bis 1,0 in Schritten der tatsächlich möglichen Teilprüfungen |
| `sum([...])` | alle Kombinationen der Teilbedingungen |
| verschachtelte Bedingungen | jeden Zweig einzeln |

Ein Hilfsskript ist zulässig und sinnvoll. Es gehört **nicht** ins Repo — es dient nur der Erhebung.

**Für `scale` unbedingt beachten:** Der Anteil kann nicht jeden Wert annehmen. Bei vier Headern sind nur 0, ¼, ½, ¾ und 1 möglich. **Genau in dieser Beschränkung entstehen die toten Stufen.**

---

## Schritt 2 — Drei Arten von Befunden unterscheiden

| Art | Bedeutung | Beispiel |
|---|---|---|
| **Tote Stufe** | Zwei verschiedene Erfüllungsgrade ergeben dieselbe Punktzahl | S3: 2 und 3 Header |
| **Unerreichbarer Wert** | Ein Punktwert innerhalb der Spanne kann nie vorkommen | C2: die 1 |
| **Begründeter Sprung** | Eine Stufe fehlt, weil das Messverfahren sie nicht hergibt | P1: 4/2/0 |

**Die dritte Art ist kein Befund.** Sie gehört in den Bericht, aber als „geprüft, in Ordnung" — sonst sieht die Liste länger aus, als sie ist.

**Die Unterscheidung zwischen der zweiten und der dritten Art ist eine Ermessensfrage.** Wenn du unsicher bist, ob ein Sprung begründet oder eine Nebenwirkung ist: **als unklar melden, nicht entscheiden.**

---

## Schritt 3 — Den Bericht schreiben

Neue Datei: `docs/Audit/BEFUND-C2-tote-stufen.md`

```markdown
# Befund C2 — Tote Stufen und unerreichbare Punktwerte

**Geprüft am:** [Datum] · **Methode:** vollständige Durchrechnung aller Eingaben
**Ergebnis:** [n] tote Stufen, [m] unerreichbare Punktwerte

## Die vollständige Wertetabelle

| Kriterium | Code | Max | Mögliche Punktwerte | Befund |
|---|---|---|---|---|
| si_header | S3 | 3 | 0, 1, 2, 2, 3 | 🔴 tote Stufe bei 3 von 4 |
| cv_cta | C2 | 3 | 0, 2, 3 | 🔴 Punktwert 1 unerreichbar |
| tp_lcp | P1 | 4 | 0, 2, 4 | ✅ begründet — Schwellen des Messverfahrens |
| … | | | | |

## Je Befund

### si_header (S3) — 3 Punkte
**Ursache:** `round(anteil × 3)` bei vier möglichen Anteilen
**Wirkung:** Der dritte gesetzte Header verändert die Punktzahl nicht
**Möglicher Punkteffekt:** +1 bei Erhöhung auf 4 Punkte, ±0 bei Gewichtung

## Ohne Befund
[Kriterien, deren Staffelung vollständig und lückenlos ist]
```

---

## Schritt 4 — Prüfen

```bash
cd kompagnon/backend && python -m pytest tests/test_audit_scoring.py -v
git diff --stat kompagnon/
```

Der zweite Befehl darf **nichts** ausgeben. Dieser Prompt ändert keinen Bewertungscode.

---

## Schritt 5 — Commit und Push

```bash
git add docs/Audit/BEFUND-C2-tote-stufen.md
git commit -m "docs(audit): every gradation computed through, not read"
git push origin staging
```

---

## Stopp-Punkt

Melden mit:

1. **Wie viele tote Stufen und unerreichbare Punktwerte es insgesamt gibt** — die Zahl ist die Hauptaussage
2. Je Befund der mögliche Punkteffekt, falls er behoben würde
3. Die Liste der Fälle, bei denen du dir unsicher warst, ob ein Sprung begründet ist
4. **Ob die Wertetabelle für ein Kriterium anders ausfällt als in den Kapiteln 5 bis 12 beschrieben** — das wäre ein Fehler im Buchmanuskript und gehört gemeldet

**Nichts ändern.**
