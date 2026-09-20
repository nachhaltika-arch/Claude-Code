# Funnel-Test

Ein Bericht je Durchlauf, benannt `JJJJ-MM-TT-HHMM.md`. Erzeugt von
`/funneltest` (`.claude/commands/funneltest.md`), gemessen von
`scripts/funnel-test.py`.

## Was hier steht

Die Kette von der Form eines Anzeigenklicks bis zum ausgelieferten PDF,
Stufe für Stufe, mit Klasse und Beleg je Zeile — **gemessen**, **angenommen**
oder **nicht erhoben**. Dazu ein Abschnitt „Was ich nicht messen konnte" samt
Grund, und die Nummern der Daten, die der Lauf hinterlassen hat.

## Was hier nicht steht

**Keine Token.** `poll_token` und `verify_token` geben Zugang zu einem
Bericht; sie bleiben im Laufzustand unter `.funneltest/`, der per
`.gitignore` außerhalb der Versionsverwaltung liegt. Das Repo ist öffentlich.

**Kein Urteil über die Analysequalität.** Der Lauf sagt, ob die Kette trägt —
nicht, ob die Punktzahl im Bericht stimmt. Dafür ist der Katalog zuständig.

## Der Unterschied zu den Nachbarn

| Werkzeug | misst |
|---|---|
| `scripts/systemdurchlauf.py` | den Quelltext |
| `scripts/durchlauf-laufzeit.py` | die Seiten im Browser |
| `/kampagne` | die Zahlen des Vortags aus vier Portalen |
| **`/funneltest`** | **einen echten Durchlauf durch die ganze Kette** |

## Zwei Dinge, die ein Lauf nicht beweist

* **Den Schutz vor Postfach-Scannern.** Die Bestätigungsseite gibt ihren
  Beleg nur an ein Ereignis mit `isTrusted === true` heraus; der Test liest
  ihn stattdessen aus `data-nachweis` und setzt ihn maschinell ein. Er prüft
  damit die Mechanik der Bestätigung, nicht die Hürde davor.
* **Dass die Anzeige Menschen erreicht.** Stufe 1 liest im Ads Manager nur
  ab, ob die Anzeigengruppe läuft. Ein echter Klick auf die eigene Anzeige
  kostet Geld und verfälscht CTR und Landingpage-Aufrufe — er gehört nicht
  in einen Test (Entscheidung David, 20.09.2026).
