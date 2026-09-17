# Upload der Landingpage

**Diese Datei ersetzt `UPLOAD-16-09-2026.md`** und trägt keinen Datumsnamen
mehr: Eine Übergabe mit Datum im Namen wird beim nächsten Mal daneben gelegt
statt fortgeschrieben, und dann gibt es zwei, von denen eine falsch ist.

---

## Stand 17.09.2026, 16:50 Uhr

Die ausgelieferte Seite ist **zwei Tage alt** und trägt **drei** Änderungen
nicht. Gemessen, nicht vermutet:

| | |
|---|---|
| `last-modified` live | **Tue, 15 Sep 2026 17:03:17 GMT** |
| `content-length` live | 1.020.062 Bytes |
| Datei im Repo | **1.020.712 Bytes** |
| SHA-256 | `2a42aaaaf6ab9c69279146981c8c0358385410a76538039a9d6e964fae906959` |

## Was die Datei trägt und die Live-Seite nicht

1. **Die fünf UTM-Felder** (15.09.) — ohne sie kommt keine Kampagnenherkunft
   im Lead und in Brevo an.
2. **`fassung:KEY`** (17.09.) — der Textbezug für den Einwilligungsnachweis.
3. **Der Canonical zeigt auf die Seite selbst** (17.09., neu) — siehe unten.

## Der Canonical war auf eine fremde Seite gerichtet

Bis zur vorigen Zeile stand im Kopf der Seite:

    <link rel="canonical" href="https://www.kompagnon.eu/webentwicklung-shopsysteme">

Das ist kein fehlendes Merkmal, sondern ein **falsches**: Ein Canonical sagt
der Suchmaschine „diese Seite ist eine Zweitfassung von jener, nimm jene".
Die Landingpage hat sich damit selbst aus dem Index genommen und ihre
Signale an die Agenturseite abgegeben — eine Seite, die mit dem Websprint
nichts zu tun hat.

Der Wert steht jetzt auf `https://websprint.kompagnon.eu/`. **Der Menülink
„Webentwicklung" auf dieselbe Agenturseite ist unberührt geblieben** — er ist
ein normaler Verweis und gehört dorthin; es gab zwei Fundstellen, und nur
eine war falsch.

Nebenbefund: `websprint.kompagnon.eu` kam in der ganzen Seite **kein
einziges Mal** vor. Sie kannte ihre eigene Adresse nicht.

## Beim Hochladen

**Die Datei heißt im Repo anders als auf dem Server.** Die Adresse
`websprint.kompagnon.eu/` liefert das Standarddokument des Verzeichnisses
aus — fast immer `index.html`. Wer `websprint-landingpage.html` hochlädt,
legt eine **zweite** Datei daneben, ohne die ausgelieferte zu ersetzen.
Genau daran ist der Upload am 15.09. gescheitert.

Also: hochladen und dabei so benennen, wie die vorhandene heißt. Im Zweifel
im Dateimanager nachsehen, welche Datei den Zeitstempel **15.09., 19:03**
(Ortszeit) trägt — die ist zu überschreiben.

## Prüfung danach, drei Zeilen

    curl -sI https://websprint.kompagnon.eu/ | grep -i last-modified
    curl -s  https://websprint.kompagnon.eu/ | grep -c utm_content
    curl -s  https://websprint.kompagnon.eu/ | grep -o 'canonical[^>]*'

Erwartet: ein Zeitstempel von **heute**, eine **1**, und ein Canonical, der
`websprint.kompagnon.eu` nennt — nicht `webentwicklung-shopsysteme`.

Steht dort weiter `17:03:17 GMT`, ist die Datei nicht angekommen — unabhängig
davon, was das Upload-Fenster gemeldet hat.

## Warum das jedes Mal Handarbeit ist

Die Seite hat keine versionierte Quelle (**L-20**): Sie liegt als fertiger
Export im Repo und wird von Hand hochgeladen. Solange das so bleibt, ist
jede Änderung an ihr zweimal zu tun — hier und dort —, und der zweite Schritt
kann ausbleiben, ohne dass es auffällt. Genau das ist zwischen dem 15. und
dem 17.09. passiert.
