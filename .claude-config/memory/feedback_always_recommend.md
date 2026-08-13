---
name: feedback-always-recommend
description: "Bei jeder Entscheidung einen empfohlenen Weg vorschlagen statt offen zu fragen — David will Empfehlung mit Begründung, nicht Optionsliste"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4c575dc8-1f76-4389-a3f1-5d8faa173ff7
  modified: 2026-08-07T20:04:54.165Z
---

Nie mit einer offenen Frage enden ("Soll ich X oder Y?"). Immer einen **empfohlenen
Pfad** nennen, kurz begründen, und dann weitermachen — David korrigiert, wenn er
etwas anderes will.

**Why:** David ist Solo-Operator und will am Programm arbeiten, nicht an
Entscheidungsvorlagen (Aussage am 2026-08-07: "ich will nicht ständig am pushen und
mergen arbeiten sondern am programm"). Jede offene Frage verlagert Arbeit zu ihm
zurück. Er hat in der Multiple-Choice-Runde zum Projekt-Assistenten **alle 16**
Empfehlungen übernommen — die Empfehlungen treffen also, und Rückfragen ohne
Empfehlung kosten nur Zeit.

**How to apply:**
- Format: Empfehlung zuerst, Begründung in ein bis zwei Sätzen, dann handeln.
- Bei echten Verzweigungen (materiell unterschiedliche Arbeit) weiterhin
  Multiple-Choice über AskUserQuestion — aber die Empfehlung IMMER als erste
  Option markieren. Dieses Format funktioniert gut.
- Bei kleinen Entscheidungen gar nicht fragen, sondern die naheliegende Variante
  wählen und im Bericht erwähnen.
- Ausnahmen bleiben: Zugangsdaten, Merges (siehe [[workflow_dual_branch]]) und
  alles, was produktiv unumkehrbar ist.

Verwandt: [[user_role]], [[feedback_pr_only_fridays]]
