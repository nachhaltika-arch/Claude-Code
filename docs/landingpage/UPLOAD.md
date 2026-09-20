# Upload der Landingpage

**Diese Datei ersetzt `UPLOAD-16-09-2026.md`** und trägt keinen Datumsnamen
mehr: Eine Übergabe mit Datum im Namen wird beim nächsten Mal daneben gelegt
statt fortgeschrieben, und dann gibt es zwei, von denen eine falsch ist.

---

## Stand 18.09.2026

**Der Upload vom 17.09., 22:59 Uhr ist angekommen.** Die Live-Seite ist
bytegleich mit der Fassung, die bis eben im Repo lag — gemessen, nicht
angenommen: gleiche Länge (1.021.471), gleiche SHA-256
(`45090cb6…e722f314`). Damit ist auch die `eventID` beim
`InitiateCheckout` draußen; der Abschnitt darunter, der sie als „noch
nicht live" führte, war überholt.

## Was die Datei jetzt trägt und die Live-Seite nicht

**Die Begriffsumstellung: „Webseite" → „Website"** (Entscheidung David,
18.09.2026). Sie betrifft **38 Stellen**, darunter `<title>`, H1,
Meta-Beschreibung, die Leistungsüberschriften und die FAQ — sichtbarer
Text *und* die strukturierten Daten, die dazu gehören.

| | |
|---|---|
| Datei im Repo | **1.021.433 Bytes** |
| SHA-256 | `87e57e566f941541945a478da7f1b1974eb6a880da1d0dbb6c7de2b06956afcd` |
| Live-Stand vorher | 1.021.471 Bytes, `Thu, 17 Sep 2026 20:59:33 GMT` |

**Eine Stelle behält bewusst „Webseite":** die FAQ-Frage „Was kostet eine
professionelle Webseite bei KOMPAGNON?". Das ist eine reale Suchanfrage —
unsere eigene Keyword-Recherche (`docs/Keywords/…`) führt „Webseite" als
eigenständigen Begriff neben „Website". Sie steht zweimal in der Datei,
sichtbar und im FAQ-Markup, und muss wortgleich bleiben: Weicht das
Markup vom sichtbaren Text ab, verwirft Google das Rich Result.

> **Beim Durchsehen aufgefallen, nicht gesucht:** Die Seite zeigt **acht**
> FAQ-Fragen, das FAQ-Markup kennt nur **vier**. Die vier stimmen wörtlich
> mit dem sichtbaren Text überein — an der Umstellung liegt es also nicht,
> das war vorher genauso. Vier Fragen sind damit für die Suchmaschine
> unsichtbar, darunter „Wird meine Website auch bei Google gefunden?".

## Beim Hochladen

**Die Datei heißt im Repo anders als auf dem Server.** Die Adresse
`websprint.kompagnon.eu/` liefert das Standarddokument des Verzeichnisses
aus — fast immer `index.html`. Wer `websprint-landingpage.html` hochlädt,
legt eine **zweite** Datei daneben, ohne die ausgelieferte zu ersetzen.
Genau daran ist der Upload am 15.09. gescheitert; am 17.09. um 18:13 hat es
geklappt.

Deshalb liegt `index.html` byte-gleich daneben — schon unter dem Zielnamen,
zum direkten Hochladen. **Sie ist nicht versioniert**, `websprint-landingpage.html`
schon (zwei Tests und die Trichter-Vorschau lesen diese). Wer die eine ändert,
schreibt die andere mit; sonst gibt es wieder zwei Fassungen, diesmal im
selben Ordner.

Also: hochladen und dabei so benennen, wie die vorhandene heißt. Im Zweifel
im Dateimanager nachsehen, welche Datei den Zeitstempel **17.09., 22:59**
(Ortszeit) trägt — die ist zu überschreiben.

**Über FTP** (seit 18.09. vorhanden): im **Binärmodus** übertragen, nicht
in ASCII. Ein FTP-Programm, das auf ASCII steht, schreibt Zeilenenden um —
bei einer Datei, die ein eingebettetes Bildarchiv und eine JSON-Zeichenkette
trägt, kommt dann etwas an, das anders lang ist als das, was losgeschickt
wurde. Die Längenprüfung unten fängt genau das.

## Prüfung danach, vier Zeilen

    curl -sI https://websprint.kompagnon.eu/ | grep -iE "last-modified|content-length"
    curl -s  https://websprint.kompagnon.eu/ | shasum -a 256
    curl -s  https://websprint.kompagnon.eu/ | grep -oi "webseiten\?" | wc -l
    curl -s  https://websprint.kompagnon.eu/ | grep -c begonnenKennung

Erwartet: ein Zeitstempel **vom 18.09.**, `content-length: 1021433`, die
Prüfsumme `87e57e56…6956afcd`, eine **2** (die beiden gewollten
„Webseite" in der Preisfrage) und eine **1** für den Messblock.

**Die Prüfsumme ist die eigentliche Antwort.** Länge und Zeitstempel sagen,
dass *etwas* angekommen ist; nur sie sagt, dass es **diese** Datei war.
Steht dort weiter `20:59:33 GMT` oder eine **40** bei „Webseite", ist die
Datei nicht angekommen — unabhängig davon, was das Upload-Fenster gemeldet
hat.

## Warum das jedes Mal Handarbeit ist

Die Seite hat keine versionierte Quelle (**L-20**): Sie liegt als fertiger
Export im Repo und wird von Hand hochgeladen. Solange das so bleibt, ist
jede Änderung an ihr zweimal zu tun — hier und dort —, und der zweite Schritt
kann ausbleiben, ohne dass es auffällt. Genau das ist zwischen dem 15. und
dem 17.09. passiert.
