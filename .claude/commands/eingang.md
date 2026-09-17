---
description: Den Briefkasten aus Design und Desktop leeren — jede Datei einordnen, ins Repo einarbeiten, nach erledigt verschieben
argument-hint: "[--nur-lesen]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

Arbeite `austausch/eingang/` ab. **Lies zuerst `austausch/README.md`** — die
Hausordnung gilt vor diesem Befehl, wenn beide sich widersprechen.

`--nur-lesen` heißt: einordnen und melden, aber nichts schreiben und nichts
verschieben. Nützlich, wenn erst einmal klar werden soll, was da liegt.

## Die Regel, die den Befehl trägt

**Nichts verschwindet stillschweigend.** Eine Datei, die du nicht einordnen
kannst, bleibt liegen und wird gemeldet — sie wird nicht geraten, nicht
weggeräumt und nicht „vorläufig" irgendwohin geschrieben. Ein Briefkasten,
der Post verschluckt, ist schlimmer als keiner: Der Absender glaubt, es sei
angekommen.

## Schritt 1 — Bestand aufnehmen

    ls -la austausch/eingang/

Zu jeder Datei: Name, Größe, Änderungsdatum. Bei Textdateien die **erste
Zeile** lesen — dort steht nach der Hausordnung, was es ist und wohin es soll.
Bei Bildern und PDFs reicht der Dateiname.

Ist der Eingang leer, sag das in einem Satz und höre auf. Kein Bericht über
nichts.

## Schritt 2 — Einordnen, nicht raten

Jede Datei bekommt genau eines von vier Zielen:

| Was es ist | Wohin |
|---|---|
| **Entscheidung** — etwas ist jetzt so und bleibt so | `docs/soll-ist-analyse.md` als Lücke oder Ergänzung, und bei Grundsätzlichem zusätzlich `CLAUDE.md` |
| **Entwurf / Konzept** — Text, der gelesen werden soll | `docs/` unter sprechendem Namen; bei Kampagnensachen `docs/kampagne/` |
| **Gestaltung** — Motiv, Layout, Farbe, Schrift | Die Tool-CI gilt (`memory/kompagnon_ui_guidelines.md`). Bilder nach `docs/` oder ins Frontend, je nach Verwendung |
| **Arbeitsauftrag** — etwas soll gebaut werden | Nicht einarbeiten. Melden, damit daraus eine Ansage wird |

**Bei Unklarheit wird gefragt, nicht entschieden.** Zwei plausible Ziele sind
ein Grund für eine Rückfrage, kein Grund für eine Münze.

## Schritt 3 — Einarbeiten

Für jede eingeordnete Datei:

* **Den Inhalt einarbeiten, nicht die Datei kopieren.** Ein Entwurf, der als
  Datei neben zwanzig anderen liegt, ist nicht eingearbeitet — er ist
  umgezogen. Eingearbeitet heißt: Der Inhalt steht an der Stelle, an der ihn
  jemand sucht, der ihn braucht.
* **Widerspricht der Inhalt etwas Bestehendem, gewinnt nicht automatisch der
  Neuling.** Nenne beide Stände und frage. Eine Anweisungsdatei, die beim
  Nachsehen widerlegt wird, kostet ihre Glaubwürdigkeit auch dort, wo sie
  recht hat.
* **Zahlen aus dem Eingang sind Behauptungen, bis sie gemessen sind.** Steht
  in einem Entwurf eine Zahl über das System, miss sie nach, bevor sie ins
  Lagebild geht.

## Schritt 4 — Wegräumen

Nur was wirklich eingearbeitet wurde:

    git mv austausch/eingang/<datei> austausch/erledigt/JJJJ-MM-TT-<datei>

Was liegen bleibt, bleibt liegen. Kein `erledigt` für etwas, das nur
angesehen wurde.

## Schritt 5 — Melden

Eine kurze Tabelle, keine Erzählung:

| Datei | Eingeordnet als | Wohin | Stand |
|---|---|---|---|

Darunter, und nur wenn es sie gibt:

* **Was liegen blieb** und warum — mit der Frage, die es klären würde.
* **Was widersprochen hat** — beide Stände nebeneinander.
* **Was daraus eine Ansage werden sollte** — Arbeitsaufträge aus Schritt 2.

Committen: ja, auf Deutsch, Conventional-Commit-Stil, `docs:` oder der
passende Bereich. **Pushen nicht** — die Sammelregel in `CLAUDE.md` gilt.
