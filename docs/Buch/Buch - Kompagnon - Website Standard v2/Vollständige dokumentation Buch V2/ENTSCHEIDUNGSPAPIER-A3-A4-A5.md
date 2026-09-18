# Entscheidungspapier A3 · A4 · A5

**Drei Widersprüche im Kriterienkatalog — und warum es trotzdem nur eine Entscheidung ist**

**Stand:** 24.08.2026 · Alle Zahlen gegen `audit_criteria.py` gerechnet

---

## Die drei Befunde in einem Satz

| | Befund | Wirkung heute |
|---|---|---|
| **A3** | **P5** nennt vier Anforderungen, vergibt drei Punkte. Größenangaben und Dateigröße teilen sich einen Punkt und müssen **beide** erfüllt sein | Ein Betrieb mit allen Größenangaben und einem einzigen 400-KB-Bild bekommt für diese Prüfung null |
| **A4** | **S3** verteilt drei Punkte auf vier Header und rundet. Zwei und drei Header ergeben beide 2 Punkte | Der dritte Header ist wertlos |
| **A5** | **B4** nennt vier Prüfungen — genau eine H1, saubere Hierarchie, Sprachauszeichnung, Formularbeschriftungen — misst aber nur die ersten beiden | Zwei zentrale Barrierefreiheits-Anforderungen fließen nicht ein |

**Alle drei sind derselbe Fehlertyp:** Der Kriterienhinweis verspricht mehr, als die Bewertung einlöst. Das ist genau der Widerspruch, den das Buch bei anderen Websites bemängelt.

---

## Warum es nur eine Entscheidung ist

Jede Option lässt sich einer von zwei Haltungen zuordnen:

| | **Summe halten (103)** | **Sauber beheben (105)** |
|---|---|---|
| **A3** | Dateigröße als eigene Prüfung streichen, in den Hinweis verschieben | P5 auf 4 Punkte — jede Teilprüfung zählt einzeln |
| **A4** | Header gewichten: CSP und X-Frame-Options je 1, HSTS und X-Content-Type je 0,5 | S3 auf 4 Punkte — je Header ein Punkt |
| **A5** | Kriterienhinweis auf die zwei tatsächlichen Prüfungen kürzen | Sprachauszeichnung und Formularbeschriftungen ergänzen (Punktzahl bleibt 2) |

**Wer mischt, ändert die Summe trotzdem — und muss dann alles nachrechnen, ohne den vollen Gewinn zu haben.** Deshalb sollten die drei gemeinsam entschieden werden.

---

## Was die beiden Wege kosten

### Weg 1 — Summe halten (Katalog bleibt 103)

| | |
|---|---|
| **Untertitel** | unverändert: *39 Kriterien, 8 Kategorien, 103 Punkte* |
| **Elektro Hansen** | 76 / 103 = **74 · Silber** — unverändert |
| **Die 30-Tage-Kette** | 74 → 79 → 87 → 90 → 93 — unverändert |
| **Klassenmaxima** | 103 / 103 / 103 / 100 / 103 / 81 — unverändert |
| **Manuskriptaufwand** | **null.** Kein Kapitel muss nachgerechnet werden |
| **Anhang B** | wird ohnehin erzeugt |

**Was dabei nicht behoben wird:**

- Bei A3 verschwindet die Dateigröße aus dem Katalog. Ein Betrieb mit 2-MB-Bildern verliert dann keinen Punkt mehr bei P5 — nur noch mittelbar über P1 und P4. **Das schwächt das Kriterium mit dem größten praktischen Hebel.**
- Bei A4 ist die Gewichtung eine Setzung. Warum CSP doppelt so schwer wiegt wie X-Content-Type-Options, muss begründet werden — und die Begründung gehört ins Buch.
- Bei A5 werden zwei echte Barrierefreiheits-Anforderungen **dauerhaft nicht gemessen.** Kapitel 8 sagt bereits, dass sich Barrierefreiheit nur teilweise prüfen lässt. Dieser Weg macht die Lücke größer, statt sie zu schließen.

### Weg 2 — sauber beheben (Katalog wird 105)

| | |
|---|---|
| **Untertitel** | *39 Kriterien, 8 Kategorien, **105 Punkte*** |
| **Elektro Hansen** | 76 / 105 = **72 · Silber** — zwei Punkte niedriger |
| **Die 30-Tage-Kette** | 72 → 77 → **87 Gold** → 90 → 92 |
| **Klassenmaxima** | 105 / 105 / 105 / **102** / 105 / **83** |
| **Manuskriptaufwand** | jede Punktangabe in Kapitel 3, 6, 7, 8, 12, 13, 15 und beiden Anhängen |

**Die gute Nachricht:** Die Erzählung des Buchs überlebt. Der Sprung auf Gold fällt weiterhin in Woche 2, und Elektro Hansen bleibt Silber. Nichts muss inhaltlich umgeschrieben werden — nur nachgerechnet.

**Die unangenehme Nachricht:** Jeder Betrieb, der bereits geprüft wurde, bekommt einen anderen Wert, ohne dass sich an seiner Website etwas geändert hat. Elektro Hansen fällt von 74 auf 72.

> **Das ist allerdings kein neues Problem.** Es ist bereits einmal passiert, als der Katalog von 100 auf 103 wuchs. Der Standard hat dafür eine Antwort: Abschnitt 2.7 verspricht, dass jedes Ergebnis seine Fassung nennt. **Die Frage ist nicht, ob sich ein Standard ändern darf — sondern ob er es geordnet tut.**

---

## Das Argument, das ich für das stärkste halte

**Jetzt ist der letzte Moment, an dem eine Katalogänderung nichts kostet.**

Nach der ISBN-Meldung ist der Untertitel eingefroren. Nach dem Satz ist jede Punktänderung ein Neusatz mit neuer Seitenzahl und neuer Rückenbreite. Nach dem Druck ist sie eine zweite Auflage mit neuer ISBN.

**Die drei Widersprüche existieren unabhängig davon, ob sie behoben werden.** Der dritte Sicherheitsheader bleibt wertlos. Die Dateigröße bleibt an eine fremde Prüfung gekoppelt. Sprachauszeichnung und Formularbeschriftungen bleiben ungemessen.

Der Unterschied ist nur, ob sie im gedruckten Buch stehen oder nicht.

---

## Was gegen Weg 2 spricht — fair dargestellt

**Erstens: 105 ist eine noch krummere Zahl als 103.** Der Einwand aus dem ersten Durchgang gilt weiter — ein Maßstab, dessen Nennwert wandert, liest sich wie ein Zwischenstand. Wer heute von 100 auf 103 auf 105 geht, hat in achtzehn Monaten dreimal die Summe geändert.

**Zweitens: Es gibt keine Garantie, dass es die letzte Änderung ist.** Wenn beim nächsten gründlichen Durchsehen drei weitere Widersprüche auffallen — und die Erfahrung dieses Projekts spricht dafür —, steht dieselbe Frage wieder an.

**Drittens: Der Manuskriptaufwand ist nicht null.** Acht Kapitel, zwei Anhänge, das Satzmuster und die Kontrollrechnung am Ende von Teil II. Ein halber Tag, wenn `BUCH-F2` läuft, und zwei Tage, wenn nicht.

---

## Ein dritter Weg, der beide Einwände auffängt

**Erst prüfen, ob es bei diesen dreien bleibt — dann einmal ändern.**

Die Liste aus Block C enthält neun weitere Codewidersprüche, die noch nicht bewertet sind: die C2-Staffelung ohne Punktwert 1, der tote K6-Zweig, die P5-Stichprobe, E1 bei K4/K5, E3/E7, die B4-Erhebungsart. **Es ist gut möglich, dass darunter zwei weitere Punktänderungen stecken.**

Der Ablauf wäre:

1. **Block C vollständig prüfen** — alle 25 Punkte, nicht nur die drei bekannten
2. **Alle Punktänderungen zusammen entscheiden** — einmal, nicht dreimal
3. **Dann `BUCH-F1` und `F2`** — und der Export erzeugt die neuen Zahlen von selbst
4. **Danach das Manuskript nachziehen** — mit einem Drift-Test, der es künftig verhindert

**Das kostet zwei Tage mehr und macht die Änderung zur letzten.** Der Untertitel wird dann einmal festgelegt und nicht dreimal.

---

## Meine Empfehlung

**Weg 3 — und zwar aus einem Grund, der nichts mit den drei Befunden zu tun hat:**

Der Restarbeiten-Report kannte vier Doppelwertungen. Beim einmaligen Durchschreiben der acht Kategoriekapitel sind drei weitere aufgefallen. Fünf Abweichungen zwischen Code und Spezifikation waren dokumentiert: keine. **Wenn eine einmalige gründliche Durchsicht die bekannte Fehlerzahl fast verdoppelt, ist die Erhebung das Problem — nicht die einzelnen Befunde.**

Eine Punktänderung zu beschließen, bevor der Katalog vollständig durchgesehen ist, heißt, dieselbe Entscheidung in vier Wochen noch einmal zu treffen.

**Konkret:** A3, A4 und A5 heute **vormerken, nicht entscheiden.** Block C vollständig prüfen — das sind zwei Tage Technik und blockiert ohnehin alles Weitere. Danach alle Punktänderungen in einer Sitzung, mit einer Zahl am Ende.

---

## Zur Vorbereitung dieser Sitzung

Damit die Entscheidung dann in einem Durchgang fällt, sollte Block C folgende Fragen beantwortet mitbringen:

| # | Frage |
|---|---|
| 1 | Wie viele Kriterien versprechen im Hinweis mehr, als sie messen? *(bekannt: P5, B4 — vollständig prüfen)* |
| 2 | Wie viele Staffelungen haben durch Rundung wertlose Stufen? *(bekannt: S3 — vollständig prüfen)* |
| 3 | Wie viele Doppelwertungen gibt es tatsächlich? *(bekannt: 7 — die A7-Liste ist unvollständig)* |
| 4 | Welche Kriterien sind widersprüchlich deklariert? *(bekannt: B4 — vollständig prüfen)* |
| 5 | Welche Punktänderungen folgen daraus, zusammengezählt? |
| 6 | Wie lautet die Katalogsumme danach — endgültig? |

**Frage 6 ist der Untertitel.** Und der ist nach der ISBN-Meldung nicht mehr änderbar.
