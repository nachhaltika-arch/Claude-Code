# Upload der Landingpage

**Diese Datei ersetzt `UPLOAD-16-09-2026.md`** und trägt keinen Datumsnamen
mehr: Eine Übergabe mit Datum im Namen wird beim nächsten Mal daneben gelegt
statt fortgeschrieben, und dann gibt es zwei, von denen eine falsch ist.

---

## Stand 17.09.2026, 21:15 Uhr

**Der Upload von 18:13 ist angekommen** — die drei Änderungen von damals
(UTM-Felder, `fassung:KEY`, Canonical) stehen live. Seither ist **eine
weitere** dazugekommen:

| | |
|---|---|
| `last-modified` live | **Thu, 17 Sep 2026 16:13:19 GMT** (= 18:13 Ortszeit) |
| `content-length` live | 1.020.712 Bytes |
| Datei im Repo | **1.021.471 Bytes** |
| SHA-256 | `45090cb680ba5b1510e548ce7b3d6d6cf5727f06ee419e920600ec48e722f314` |

## Was die Datei trägt und die Live-Seite nicht

**Die `eventID` beim `InitiateCheckout`** (17.09., 21:10). Der Lead trägt seit
jeher eine, dieses Ereignis nicht. Ohne sie hängt die Entdopplung an Metas
eigenem Verhalten, das nicht zugesagt ist: Es greift bei zwei gleichen
Meldungen kurz hintereinander aus demselben Browser, aber nicht verlässlich
bei Abstand oder mehreren Tabs. Mit ihr verwirft Meta die zweite Meldung
selbst.

Das zählt, weil die neue Anzeigengruppe auf genau dieses Ereignis optimieren
soll: Eine doppelt gezählte „Analyse begonnen" lässt die Kosten je Abschluss
halb so hoch aussehen und die Lernphasenschwelle früher erreicht scheinen,
als sie ist.

**Erledigt und live seit 18:13** — hier nur noch der Vollständigkeit halber:
die fünf UTM-Felder, `fassung:KEY`, und der Canonical, der vorher auf eine
fremde Seite zeigte.

## Was am 17.09. um 18:13 hochgeladen wurde — zur Nachvollziehbarkeit

Der Canonical stand bis dahin auf `www.kompagnon.eu/webentwicklung-shopsysteme`,
also auf einer **anderen** Seite. Ein Canonical sagt der Suchmaschine „diese
Seite ist eine Zweitfassung von jener, nimm jene" — die Landingpage hat sich
damit selbst aus dem Index genommen. Er zeigt jetzt auf
`https://websprint.kompagnon.eu/`; der Menülink „Webentwicklung" auf dieselbe
Agenturseite blieb unberührt, denn er gehört dorthin.

## Beim Hochladen

**Die Datei heißt im Repo anders als auf dem Server.** Die Adresse
`websprint.kompagnon.eu/` liefert das Standarddokument des Verzeichnisses
aus — fast immer `index.html`. Wer `websprint-landingpage.html` hochlädt,
legt eine **zweite** Datei daneben, ohne die ausgelieferte zu ersetzen.
Genau daran ist der Upload am 15.09. gescheitert; am 17.09. um 18:13 hat es
geklappt.

Also: hochladen und dabei so benennen, wie die vorhandene heißt. Im Zweifel
im Dateimanager nachsehen, welche Datei den Zeitstempel **17.09., 18:13**
(Ortszeit) trägt — die ist zu überschreiben.

## Prüfung danach, drei Zeilen

    curl -sI https://websprint.kompagnon.eu/ | grep -i last-modified
    curl -s  https://websprint.kompagnon.eu/ | grep -c begonnenKennung
    curl -s  https://websprint.kompagnon.eu/ | grep -o "eventID: begonnenKennung"

Erwartet: ein Zeitstempel **nach 21:15**, eine **1**, und der Treffer
`eventID: begonnenKennung`.

Steht dort weiter `16:13:19 GMT`, ist die Datei nicht angekommen — unabhängig
davon, was das Upload-Fenster gemeldet hat.

## Warum das jedes Mal Handarbeit ist

Die Seite hat keine versionierte Quelle (**L-20**): Sie liegt als fertiger
Export im Repo und wird von Hand hochgeladen. Solange das so bleibt, ist
jede Änderung an ihr zweimal zu tun — hier und dort —, und der zweite Schritt
kann ausbleiben, ohne dass es auffällt. Genau das ist zwischen dem 15. und
dem 17.09. passiert.
