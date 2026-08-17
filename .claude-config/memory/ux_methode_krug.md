---
name: ux-methode-krug
description: "UX-Prüfung des KAS nach Steve Krug — Analyse und Arbeitsliste liegen im Repo, Paket 1 und 2 erledigt, Paket 3 als Nächstes"
metadata: 
  node_type: memory
  type: project
  originSessionId: 23187c5a-98e4-46cd-b53f-9f76742d7f0a
  modified: 2026-08-17T12:27:31.357Z
---

**Die Oberflächenprüfung des KAS läuft nach Steve Krug**, *Don't Make Me Think*
— ergänzt um die drei Nutzerreisen (Betreiber, Kunde, Öffentlichkeit).

Zwei Dateien im Repo, beide fortgeschrieben:

- **`docs/ux-soll-ist-kas.md`** — die Analyse. Inzwischen 34 Befunde, jeder mit
  dem Bildschirm daneben, an dem er zu sehen ist
- **`docs/ux-arbeitsliste.md`** — das Abzuarbeitende. Sieben Pakete, jeder
  Punkt mit **Fundstelle** (Datei:Zeile), **Aufwand** (S/M/L) und
  **Prüfschritt**. Ohne den Prüfschritt ist eine Liste nur eine Wunschliste

Browser-Fassung der Analyse:
`https://claude.ai/code/artifact/946b018e-40f7-481f-826a-83fbf9d53d66`

**Der Kern des Befunds:** Fast nichts ist ein Funktionsfehler, fast alles ist
Benennung und visuelle Gewichtung.

**Entschieden am 2026-08-16:** Das Objekt heißt überall **„Betrieb"**. Der
Zustand („Lead", „Kunde") ist ein **Status**, kein Objektname.

**Stand:** Paket 1 und 2 abgeschlossen. Als Nächstes **Paket 3** — vier
Stellen, an denen die Oberfläche etwas Falsches behauptet.

**Drei Regeln, die sich als tragfähig erwiesen haben:**

1. **Ein unbekannter Wert wird nie roh gezeigt und nie als bekannter getarnt.**
   Er wird lesbar gemacht und bleibt neutral — dann verrät er sich als „kenne
   ich nicht", statt durchzurutschen.
2. **Die Regel gilt nicht nur für die Anzeige, sondern auch für den Filter.**
   Paket 2 zeigte den Fall: Ein Betrieb mit Status `opt_in` wurde korrekt als
   „Opt in" angezeigt — aber Filter und Kacheln wurden aus den *Schlüsseln* der
   bekannten Werte gebaut. Sichtbar und trotzdem unerreichbar, und die Zahlen
   gingen nicht auf. **Auswahllisten gehören aus den Daten abgeleitet, nicht
   aus der Landkarte der bekannten Werte.** Dasselbe galt für den
   Quellenfilter, wo drei feste Optionen bei freitextlichen Quellen standen.
3. **Vor dem Entfernen einer Sonderlogik am laufenden System nachsehen, was sie
   tatsächlich tut.**

**Und die Beobachtung, die sich zweimal bestätigt hat:** Der jeweils beste Fund
kam vom Hinsehen nach dem Deploy, nicht vom Lesen des Codes. Paket 1: die
zugeklappte Seitenleiste. Paket 2: die Zahlen, die nicht aufgingen. Beide Male
waren Tests grün, Build sauber und der Code für sich genommen korrekt.

Siehe [[resume-point-2026-08-17]] und [[kompagnon-ui-guidelines]].
