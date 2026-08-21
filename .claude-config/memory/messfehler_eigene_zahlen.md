---
name: messfehler-eigene-zahlen
description: "Eigene Messungen sind selbst Code und haben Bugs — sieben Fehlmessungen an einem Tag, alle beim Nachprüfen am Gegenstand gefunden"
metadata:
  type: feedback
---

Eine selbstgeschriebene Messung ist kein Beleg, sondern eine Behauptung mit
Zwischenschritt. Am 2026-08-21 haben sieben eigene Zahlen nicht gestimmt —
**jede wurde beim Nachprüfen am Gegenstand gefunden, keine beim Nachdenken.**

Die wiederkehrenden Fehlerquellen, nach Häufigkeit:

1. **Zeichenketten mitgezählt.** `TemplateLibrary.jsx` wurde mit neun `<h1>`
   gemeldet — acht stehen in HTML-Vorlagen für Kundenseiten. Vor dem Zählen
   Backticks und Anführungszeichen entfernen.
2. **Kommentare mitgezählt.** Zwei Wächter meldeten sich selbst, weil in ihrer
   eigenen Beschreibung das gesuchte Muster stand.
3. **Die eigene Reparatur nicht erkannt.** Die Überschriften-Messung sah
   `<SeitenTitel>` nicht als `h1` und meldete 22 gerade reparierte Seiten
   weiter als kaputt.
4. **Regex über JSX-Attribute.** `onChange={e => f(e)}` enthält ein `>`, an
   dem `[^>]*>` das Tag auseinanderschneidet. Es braucht einen Scanner, der
   Klammern und Anführungszeichen mitzählt.
5. **Die falsche Ebene gelesen.** Ein Audit-Kriterium las `facts["llms_txt"]`
   — dorthin hebt es `summarise_facts`, aber die Bewertung bekommt
   `collect_facts`. Es wäre produktiv **nie** gelaufen.
6. **Die falsche Route gemessen.** `GET /api/leads/{id}` antwortete 200 ohne
   das erwartete Feld: ein `LeadResponse`, nicht die Route, die den Bildschirm
   speist. **Ein Statuscode allein beweist nichts.**
7. **Erster statt letzter Treffer.** `re.search` fand die erste Beschriftung
   vor einem Feld statt der nächstgelegenen.

**Why:** Eine falsche Messung ist teurer als keine — sie sieht aus wie ein
Ergebnis und wird weitergereicht. Zwei der sieben hätten eine Reparatur
vorgetäuscht, die es nicht gab.

**How to apply:** Nach jeder selbstgebauten Zählung eine Handprobe an zwei bis
drei Treffern. Beim Ergebnis immer mitprüfen, ob die eigene Änderung im
Zählverfahren überhaupt sichtbar wäre. Und wo ein Test grün ist, fragen: an
welchem Gegenstand? Siehe [[feedback-am-gegenstand-pruefen]].
