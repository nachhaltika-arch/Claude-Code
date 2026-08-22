---
name: feedback-lagebild-nachfuehren
description: Nach jeder geschlossenen Lücke sofort das KOMPAGNON-Lagebild neu bauen — nicht sammeln
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 13c50d98-61aa-4d91-aa0f-f391ea9f1b35
  modified: 2026-08-22T14:37:00.056Z
---

Wenn eine Lücke (L-Nummer) geschlossen oder teilweise geschlossen wird, wird das
**Lagebild im selben Zug** aktualisiert — nicht am Tagesende gesammelt.

Artifact-URL: `https://claude.ai/code/artifact/f6fb7e07-6303-4a21-a536-74e0d6de0f2a`
(dieselbe URL beibehalten — republish über denselben Dateipfad oder mit `url`).

**Warum:** Das Lagebild ist Davids Entscheidungsgrundlage. Ein Stand von gestern
sieht aus wie einer von heute — dieselbe Falle wie bei der Datei, die
`soll-ist-analyse-2026-08-07.md` hieß und veraltete, weil das Datum im Namen
sie wie einen Stand lesen ließ.

**How to apply:**
1. Zuerst `docs/soll-ist-analyse.md` fortschreiben — sie ist die Wahrheitsquelle,
   das Lagebild nur ihre Ansicht.
2. Dann `python3 scripts/lagebild-bauen.py` (aus der Repo-Wurzel) — liest die
   Lückenliste, zählt Status und Kennzahlen selbst und schreibt
   `docs/lagebild/kompagnon-lagebild.html`.
   **Nie Zahlen von Hand eintragen:** Am 22.08. stand „7 von 11 Modulen grün",
   gezählt waren es 6. Siehe [[messfehler_eigene_zahlen]].
3. Als Artifact republishen — **mit `url`**, sonst entsteht ein zweites
   Artifact unter neuer Adresse. Vorlage und Plandaten liegen daneben in
   `docs/lagebild/`.

Gilt genauso für neue Lücken und für Statuswechsel auf „teilweise".
Verwandt: [[feedback_am_gegenstand_pruefen]], [[feedback_ci_pruefen_nach_push]].
