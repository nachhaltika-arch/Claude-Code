---
name: feedback-am-gegenstand-pruefen
description: "Nie eine Zwischenausgabe für das Ergebnis nehmen — am Gegenstand selbst prüfen, nicht am Werkzeug, das darüber berichtet"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 458bef95-0615-4eb2-85b8-f2842368b8c2
  modified: 2026-08-17T21:39:07.989Z
---

**Nie eine Zwischenausgabe für das Ergebnis nehmen.** Am 17.08.2026 ist mir
derselbe Fehler dreimal in einer Sitzung passiert, jedes Mal in anderer
Verkleidung:

1. **„Lokale Tests grün" statt CI.** 261 Frontend-Tests liefen bei mir durch,
   also habe ich Paket 6 als fertig gemeldet. Der Playwright-Job in der CI war
   rot — er klickt sich durch das Menü, meine Tests prüfen reine Funktionen.
2. **„Push durch" statt CI grün.** Ich habe gemeldet, was gepusht war, nicht
   was geprüft war. David hat den roten Lauf gefunden, nicht ich.
3. **„Skript sagt angepasst" statt in die Datei sehen.** Mein Reparaturskript
   starb an einem Syntaxfehler (deutsche Anführungszeichen in einem
   Python-String). Ein Syntaxfehler verhindert den **ganzen** Lauf — also
   wurde auch der erste Teil nie ausgeführt. Ich sah die Ausgabe des zweiten
   Anlaufs, hielt alles für erledigt, und CI fiel ein zweites Mal an derselben
   Stelle — nach einem Commit, dessen Nachricht behauptet, es sei behoben.

**Die Regel, die alle drei abdeckt:** Am Gegenstand prüfen, nicht am Werkzeug,
das darüber berichtet. `grep` in der Datei statt der Skriptausgabe glauben.
Den CI-Lauf abfragen statt den Push. Den Bildschirm ansehen statt den Code zu
lesen.

**Konkret für diese Zusammenarbeit:**

- **Ein Paket gilt erst als fertig, wenn sein CI-Lauf grün ist** — nicht wenn
  der Push durch ist. Bis dahin heißt es „gepusht, CI läuft".
- **Nicht pushen, solange für den vorherigen Commit noch ein Job läuft.**
  Sonst bricht `cancel-in-progress` ihn ab. Am 17.08. viermal passiert.
- Nach einer Änderung per Skript: **nachsehen, dass sie drinsteht.**

Siehe auch [[feedback-ci-pruefen-nach-push]] und [[deploy-laeuft-ueber-ci]].
