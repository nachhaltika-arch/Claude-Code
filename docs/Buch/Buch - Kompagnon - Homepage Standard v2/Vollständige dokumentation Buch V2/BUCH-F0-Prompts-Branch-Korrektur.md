# BUCH-F0 — Pflicht-Check in allen Buch-Prompts korrigieren

**Aufwand:** 15 Minuten · **Ein Commit** · **Blockiert:** alle folgenden Buch-Prompts

---

## Was hier passiert und warum

In `docs/Buch/` liegen 13 Anleitungsdateien (`BUCH-00` bis `BUCH-12`). Jede beginnt mit einer Sicherheitsabfrage, die prüft, ob wir im richtigen Repository und auf dem richtigen Arbeitsstand sind. Diese Abfrage nennt einen Arbeitsstand namens `claude/kompagnon-automation-system-FapM9`.

Diesen Arbeitsstand gibt es nicht mehr. Er wurde verworfen; gearbeitet wird ausschließlich auf `staging`.

Die Folge ist unangenehm: Jede Session, die eine dieser Dateien ehrlich abarbeitet, **muss** am eigenen Pflicht-Check stoppen und „falscher Branch" melden. Die Dateien blockieren sich also selbst. Wer den Check stattdessen überspringt, hat die Schutzfunktion abgeschafft, für die er da ist.

Wir korrigieren deshalb zuerst die Anleitungen, bevor wir eine davon benutzen.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet:
- `origin` → `https://github.com/nachhaltika-arch/Claude-Code`
- Branch → `staging`

Stimmt eines nicht: **sofort stoppen**, melden „Falsches Repo oder falscher Branch", nichts ausführen.

---

## Schritt 1 — Diagnose: welche Dateien sind betroffen?

Erst zählen, dann ändern. Nicht raten, wie viele es sind.

```bash
grep -rln "claude/kompagnon-automation-system-FapM9" docs/ | sort
grep -rn "claude/kompagnon-automation-system-FapM9" docs/ | wc -l
```

**Melde mir die Liste und die Anzahl der Fundstellen, bevor du weitermachst.** Wenn Treffer außerhalb von `docs/Buch/` auftauchen — etwa in `docs/Features/` oder `CLAUDE.md` — dann gehören sie mit korrigiert, aber ich will vorher wissen, dass es sie gibt.

---

## Schritt 2 — Ersetzen

In allen gefundenen Dateien:

- `claude/kompagnon-automation-system-FapM9` → `staging`

Achte dabei auf den umgebenden Text. An manchen Stellen steht nicht nur der Name, sondern eine Erklärung dazu („Branch → `claude/...`"). Der Satz muss danach noch stimmen.

Zusätzlich in **jeder** korrigierten Datei den Pflicht-Check auf die geltende Fassung bringen, falls er abweicht:

```markdown
## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet:
- `origin` → `https://github.com/nachhaltika-arch/Claude-Code`
- Branch → `staging`

Stimmt eines nicht: sofort stoppen, melden „Falsches Repo oder falscher Branch", nichts ausführen.
```

---

## Schritt 3 — Zwei weitere Altlasten in `BUCH-00-MASTERPLAN.md`

Diese Datei beschreibt einen Stand, den der Code überholt hat. Zwei Stellen sind sachlich falsch und würden jeden, der danach arbeitet, in die Irre führen:

**3a — Abschnitt 2, Tabelle „Der Homepage Standard existiert bereits an drei Stellen im Code":**
Dort steht `AuditReport.jsx` enthalte „6 Kategorien, ~30 Unterkriterien". Gemessen sind es **8 Kategorien und 39 Kriterien**. Korrigiere die Zahl und ergänze die Tabelle um die heute tatsächlich maßgebliche Quelle:

| Ort | Was steht drin |
|---|---|
| `backend/services/audit_criteria.py` | **Maßgeblich.** 8 Kategorien, 39 Kriterien, Punktwerte, Stufenschwellen (`LEVELS`) |
| `frontend/src/utils/homepageStandard.js` | Stufenschwellen fürs Frontend — folgt dem Backend |
| `frontend/public/embed/audit-widget.html` | Stufenschwellen als Rückfall — eigenständige Datei, kann nichts einbinden |

**3b — Abschnitt 2, „Lösung":**
Dort steht, es solle eine Datei `shared/homepage-standard.json` angelegt werden. Diese Datei gibt es nicht, und sie wird auch nicht so kommen: Nach `BUCH-F2` wird die Definitionsdatei **aus** `audit_criteria.py` erzeugt und liegt unter `kompagnon/backend/services/`. Passe den Absatz an und verweise auf `BUCH-F1` bis `BUCH-F3` statt auf `BUCH-01`.

---

## Schritt 4 — Prüfen

```bash
grep -rn "claude/kompagnon-automation-system-FapM9" docs/ || echo "keine Fundstellen mehr — gut"
grep -rn "6 Kategorien" docs/Buch/BUCH-00-MASTERPLAN.md || echo "veraltete Zahl entfernt — gut"
```

Beide Befehle müssen die „gut"-Meldung ausgeben.

---

## Schritt 5 — Commit und Push

Genau ein Commit, Nachricht auf Englisch:

```bash
git add docs/
git commit -m "docs(buch): the mandatory branch check no longer blocks itself"
git push origin staging
```

---

## Stopp-Punkt

Danach **melden**, nicht weitermachen. Bitte in der Meldung:

1. Wie viele Dateien geändert wurden
2. Ob Treffer außerhalb von `docs/Buch/` dabei waren
3. Ob im Masterplan noch weitere Zahlen stehen, die dir gegenüber dem Code veraltet vorkommen — nur melden, nicht ändern
