---
kapitel: 7
teil: "II — Die acht Kategorien"
titel: "Ladezeit und Stabilität"
autor: "Manuel Potter"
status: entwurf
zuletzt_geprueft: 2026-08-24
standard_version: "2026.2"
zielumfang: 16 Seiten
punkte: 15
kriterien: "P1–P5"
---

<!-- KAPITELÖFFNER — rechte Seite -->

# 7

# Ladezeit und Stabilität

# 15 Punkte

> Fünf Kriterien. Vier davon hängen an einer Messung, die nicht wir durchführen — und die bei kleinen Betriebsseiten regelmäßig unvollständig bleibt. Dieses Kapitel sagt Ihnen auch, was das für Ihr Ergebnis bedeutet.

<!-- SEITENUMBRUCH -->

## 7.1 Was hier bewertet wird

Fünf Kriterien, zusammen 15 Punkte.

<!-- ERZEUGT aus generiert/kriterien-performance.md — nicht von Hand ändern. -->

| Code | Kriterium | Punkte | Gilt für |
|---|---|---|---|
| P1 | Ladezeit des Hauptinhalts | 4 | alle Klassen |
| P2 | Layoutstabilität | 3 | alle Klassen |
| P3 | Reaktionszeit auf Eingaben | 2 | alle Klassen |
| P4 | Mobiler Gesamtwert | 3 | alle Klassen |
| P5 | Bildoptimierung | 3 | alle Klassen |

Keine Klassenunterschiede. Eine langsame Seite ist für jeden Besucher langsam, unabhängig davon, was auf ihr angeboten wird.

::: MRG
**P1–P5**
5 Kriterien · 15 Punkte
alle **gemessen**
:::

**P1 ist mit vier Punkten das schwerstwiegende Einzelkriterium dieser Kategorie** und eines der schwersten des ganzen Standards. Es gibt im Katalog nur zwei Kriterien mit mehr Gewicht, und beide stehen in Kapitel 5.

---

## 7.2 Warum 15 Punkte

Ladezeit ist gut messbar und wirkt unmittelbar. Wer zu lange wartet, geht — und zwar bevor er gesehen hat, was Sie anbieten. Das macht diese Kategorie zu einer der wenigen, bei denen ein technischer Mangel direkt in entgangene Anfragen umschlägt.

Nicht mehr als 15 Punkte, weil die Messung **schwankt**. Sie hängt vom Standort des Messservers ab, von der Tageszeit, von der Auslastung Ihres Anbieters. Zwei Messungen derselben Seite im Abstand einer Stunde können unterschiedlich ausfallen. Ein Kriterium, das nicht exakt reproduzierbar ist, darf nicht dominieren — sonst schwankt die Gesamtbewertung mit ihm.

**Deshalb ein Hinweis, der Ihnen Ärger erspart:** Wenn Sie Ihre Seite zweimal messen und leicht unterschiedliche Werte bekommen, ist das kein Fehler. Bewegen sich beide Messungen in derselben Punktstufe, ist das Ergebnis stabil. Erst wenn eine Messung 4 Punkte und die nächste 2 ergibt, liegen Sie an einer Schwelle — und dann ist die Verbesserung ohnehin fällig.

---

## 7.3 Wovon diese Kategorie abhängt

Dieser Abschnitt gehört in kein anderes Kapitel, und er gehört gelesen, bevor Sie Ihr Ergebnis bewerten.

**Vier der fünf Kriterien — P1 bis P4, zusammen 12 Punkte — stammen aus einer externen Messung.** Sie wird nicht von uns durchgeführt, sondern von einem öffentlich zugänglichen Messdienst, der Ihre Seite lädt und dabei aufzeichnet, wie lange was dauert. Nur P5, die Bildoptimierung, wird eigenständig erhoben.

Das hat zwei Folgen.

**Erstens: Wenn die Messung ausfällt, fallen zwölf Punkte aus.** Nicht auf null — sie fallen aus der Rechnung, wie in Abschnitt 3.5 beschrieben. Ihr anwendbares Maximum sinkt dann von 103 auf 91. Zusammen mit zwei Kriterien in Kapitel 8, die aus derselben Quelle stammen, können auf diese Weise **bis zu 18 von 103 Punkten** unerhoben bleiben.

::: MRG
**Wenn die Messung ausfällt**
P1–P4 (12 P) und zwei Kriterien in Kapitel 8 (6 P) sind nicht erhebbar.
Anwendbares Maximum sinkt auf 85.
:::

Ein Bericht, in dem diese Kriterien als „nicht erhoben" ausgewiesen sind, ist kein fehlerhafter Bericht. Er ist ein unvollständiger — und er sagt es Ihnen. **Wiederholen Sie die Messung zu einer anderen Tageszeit.**

**Zweitens: Ein Kriterium fällt fast immer aus, und zwar planmäßig.** P3, die Reaktionszeit, wird nicht im Labor gemessen, sondern aus echten Besucherdaten gewonnen. Für kleine Betriebsseiten liegen die schlicht nicht vor — es waren zu wenige Besucher, um einen belastbaren Wert zu bilden.

**Das ist der Normalfall, nicht die Ausnahme.** Wenn bei Ihnen P3 als „nicht erhoben" steht, ist Ihre Seite nicht schlecht gemessen worden. Sie ist zu klein für diese Art von Messung, und der Standard behandelt sie deshalb korrekt: Die zwei Punkte fallen aus Zähler und Nenner.

> **Was Sie daraus mitnehmen sollten.** Vergleichen Sie Ihr Ergebnis nie über die Rohpunkte mit einem anderen Betrieb, sondern über den Wert zwischen 0 und 100. Zwei Betriebe mit 71 Rohpunkten können völlig verschiedene Werte haben, wenn bei einem drei Kriterien nicht erhoben wurden. Die Normierung aus Abschnitt 3.6 macht sie erst vergleichbar.

---

## 7.4 Der Fall

Elektro Hansen, Branchenklasse K1.

| Kriterium | Befund | Punkte |
|---|---|---|
| P1 Ladezeit des Hauptinhalts | 3,4 Sekunden | 2 / 4 |
| P2 Layoutstabilität | 0,04 — sehr gut | 3 / 3 |
| P3 Reaktionszeit | 310 Millisekunden | 1 / 2 |
| P4 Mobiler Gesamtwert | 58 von 100 | 1 / 3 |
| P5 Bildoptimierung | **keine der drei Prüfungen bestanden** | 0 / 3 |
| | | **7 / 15** |

Acht Punkte fehlen — mehr als in jeder anderen Kategorie dieses Betriebs. Und der Befund ist eindeutig: **Es sind die Bilder.**

Nicht nur bei P5, wo es offensichtlich ist. Auch die 3,4 Sekunden bei P1 gehen überwiegend auf ein einziges Bild zurück — das große Foto im Kopfbereich der Startseite, 1,8 Megabyte, unkomprimiert aus der Kamera hochgeladen. Der Besucher sieht drei Sekunden lang eine leere Fläche.

**In Kapitel 3 haben wir gerechnet, dass drei Punkte hier zurückzuholen sind** — die drei Punkte bei P5. Was dabei nicht gezählt wurde: Dieselbe Korrektur verbessert mit hoher Wahrscheinlichkeit auch P1 und P4. Der Standard zählt das nicht doppelt, aber Ihre Besucher merken es doppelt.

---

## 7.5 P1 — Ladezeit des Hauptinhalts · 4 Punkte

::: MRG
**P1 · 4 Punkte**
gemessen
externe Messung
:::

### Worum es geht

Gemessen wird nicht, wann Ihre Seite fertig geladen ist. Gemessen wird, **wann das größte sichtbare Element erscheint** — meist das Kopfbild, manchmal eine große Überschrift.

Das ist die ehrlichere Messung: Ein Besucher wartet nicht darauf, dass im Hintergrund das letzte Skript nachlädt. Er wartet darauf, dass etwas da ist, das er ansehen kann.

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-tp_lcp.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 4 | unter 2,5 Sekunden |
| 2 | 2,5 bis unter 4,0 Sekunden |
| 0 | 4,0 Sekunden oder mehr |

**Es gibt keine 3 und keine 1.** Die Staffelung springt von 4 auf 2 auf 0. Das ist beabsichtigt: Die beiden Schwellen 2,5 und 4,0 Sekunden sind die etablierten Grenzwerte des Messverfahrens, und dazwischen einen Zwischenwert zu erfinden hieße, Genauigkeit zu behaupten, die die Messung nicht hat.

::: MRG
**Zwei Sekunden entscheiden über vier Punkte**
2,4 s → 4 Punkte
2,6 s → 2 Punkte
4,1 s → 0 Punkte
:::

### So beheben Sie es

In dieser Reihenfolge, weil sie nach Wirkung je Aufwand sortiert ist:

1. **Das größte Bild im Kopfbereich verkleinern.** In neun von zehn Fällen ist genau dieses Bild die Ursache. Ein Kopfbild sollte selten mehr als 200 Kilobyte haben. Fotos direkt aus einer Kamera haben das Zehnfache.
2. **Fremde Schriftarten örtlich einbinden.** Sie kennen den Handgriff schon aus Kapitel 6 — dort brachte er einen Punkt bei S4. Hier bringt er Zeit, weil der Browser nicht erst einen fremden Server befragen muss, bevor er Text darstellen kann.
3. **Prüfen, was vor dem ersten sichtbaren Inhalt geladen wird.** Skripte im Seitenkopf blockieren die Darstellung. Vieles davon kann warten.
4. **Erst danach über den Anbieter nachdenken.** Ein schnellerer Server hilft, aber er ist die teuerste und meist nicht die wirksamste Maßnahme.

---

## 7.6 P2 — Layoutstabilität · 3 Punkte

::: MRG
**P2 · 3 Punkte**
gemessen
externe Messung
:::

### Worum es geht

Sie kennen den Effekt: Sie wollen eine Schaltfläche anklicken, im selben Moment lädt ein Bild nach, alles rutscht nach unten, und Sie klicken auf etwas anderes. Gemessen wird, wie stark sich das Layout während des Ladens noch verschiebt.

Es ist das einzige Kriterium dieser Kategorie, das **nichts mit Geschwindigkeit zu tun hat.** Eine schnelle Seite kann springen, eine langsame kann ruhig stehen.

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-tp_cls.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 3 | Wert unter 0,1 |
| 1 | 0,1 bis unter 0,25 |
| 0 | 0,25 oder mehr |

Der Wert ist eine Verhältniszahl ohne Einheit. Sie müssen ihn nicht deuten können — die drei Stufen genügen.

**Auch hier ein Sprung**, diesmal von 3 auf 1. Dieselbe Begründung wie bei P1: Die Schwellen stammen aus dem Messverfahren, nicht aus unserer Bewertung.

### So beheben Sie es

Es gibt praktisch nur drei Ursachen, und alle drei sind behebbar:

1. **Bilder ohne Größenangabe.** Der Browser weiß nicht, wie viel Platz er freihalten soll, und schiebt nach, sobald das Bild da ist. **Das ist zugleich eine der drei Prüfungen von P5** — Sie holen hier und dort Punkte mit derselben Korrektur.
2. **Nachgeladene Einwilligungsbanner oder Hinweisleisten**, die den Inhalt nach unten drücken. Sie sollen Platz einnehmen, bevor sie erscheinen.
3. **Fremde Schriftarten ohne Ersatzangabe.** Der Text wird zunächst in einer Standardschrift dargestellt, dann in Ihrer — und wenn beide unterschiedlich breit laufen, verschiebt sich alles.

---

## 7.7 P3 — Reaktionszeit auf Eingaben · 2 Punkte

::: MRG
**P3 · 2 Punkte**
gemessen
**bei kleinen Seiten meist nicht erhebbar**
:::

### Worum es geht

Wie lange dauert es, bis Ihre Seite auf einen Klick reagiert? Nicht bis die Aktion abgeschlossen ist, sondern bis überhaupt etwas passiert.

### Was Sie über dieses Kriterium wissen sollten

**Es wird nicht im Labor gemessen, sondern aus echten Besucherdaten gewonnen.** Ein Messdienst kann simulieren, wie schnell eine Seite lädt — aber nicht, wie sie sich anfühlt, wenn jemand sie benutzt. Dafür braucht es tatsächliche Besucher, und zwar genug davon.

**Für die meisten Betriebsseiten liegen diese Daten nicht vor.** Das Kriterium wird dann als nicht erhoben ausgewiesen, die zwei Punkte fallen aus Zähler und Nenner, Ihr anwendbares Maximum sinkt auf 101.

Das ist kein Nachteil für Sie. Es ist die korrekte Behandlung einer Messung, die es nicht gibt.

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-tp_inp.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 2 | unter 200 Millisekunden |
| 1 | 200 bis unter 500 Millisekunden |
| 0 | 500 Millisekunden oder mehr |
| — | keine Besucherdaten verfügbar → nicht erhoben |

### So beheben Sie es

Wenn dieses Kriterium bei Ihnen überhaupt gemessen wurde und schlecht ausfällt, liegt es fast immer an zu vielen oder zu großen Skripten. Die häufigsten Verursacher: Zusatzfunktionen im Baukastensystem, die Sie einmal aktiviert und nie wieder benutzt haben — Bildergalerien, Animationseffekte, Chat-Fenster, Bewertungsanzeigen.

**Der wirksamste Schritt ist Wegnehmen, nicht Optimieren.**

---

## 7.8 P4 — Mobiler Gesamtwert · 3 Punkte

::: MRG
**P4 · 3 Punkte**
gemessen
Messung ausdrücklich **mobil**
:::

### Worum es geht

Ein zusammenfassender Wert von 0 bis 100, den der Messdienst aus mehreren Einzelmessungen bildet — **und zwar ausdrücklich für die mobile Darstellung**, simuliert auf einem durchschnittlichen Mobilgerät mit einer durchschnittlichen Mobilverbindung.

Dass ausschließlich mobil gemessen wird, ist eine bewusste Entscheidung. Der überwiegende Teil der Besucher einer Betriebswebsite kommt vom Telefon. Eine Seite, die am Bürorechner mit Kabelverbindung in einer Sekunde da ist, kann auf dem Telefon fünf brauchen.

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-tp_mobile.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 3 | Wert 90 oder höher |
| 2 | Wert 70 bis 89 |
| 1 | Wert 50 bis 69 |
| 0 | Wert unter 50 |

Das ist die einzige vollständige Vierer-Staffelung dieser Kategorie — hier gibt es keine Sprünge.

### Was dieses Kriterium besonders macht

**Es überschneidet sich mit P1 und P2.** Der Gesamtwert enthält die Ladezeit des Hauptinhalts und die Layoutstabilität als Bestandteile. Wer P1 verbessert, verbessert P4 mit.

Das ist keine Doppelbewertung im Sinne eines Fehlers, sondern eine bewusste Gewichtung: Wer bei den Einzelmessungen gut abschneidet, soll das auch im Gesamtwert wiederfinden. **Für Sie bedeutet es vor allem eines: Die Maßnahmen aus Abschnitt 7.5 wirken hier ein zweites Mal.**

---

## 7.9 P5 — Bildoptimierung · 3 Punkte

::: MRG
**P5 · 3 Punkte**
gemessen
**eigene Erhebung**, unabhängig von der externen Messung
:::

### Worum es geht

Das einzige Kriterium dieser Kategorie, das eigenständig erhoben wird. Es fällt also auch dann nicht aus, wenn die externe Messung ausfällt — und das macht es zum verlässlichsten Kriterium des Kapitels.

Bewertet wird nicht, ob Ihre Bilder schön sind, sondern ob sie technisch für das Web aufbereitet wurden.

### Was geprüft wird

Drei Prüfungen, jede einen Punkt wert:

| Prüfung | Bestanden, wenn |
|---|---|
| **Zeitgemäßes Bildformat** | mindestens die Hälfte der Bilder in einem modernen Format vorliegt |
| **Verzögertes Nachladen** | mindestens die Hälfte der Bilder erst geladen wird, wenn sie in Sicht kommen |
| **Größenangaben und Dateigröße** | mindestens vier von fünf Bildern eine Größenangabe haben **und** kein geprüftes Bild über 300 Kilobyte liegt |

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-tp_bilder.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 3 | alle drei Prüfungen bestanden |
| 2 | zwei Prüfungen bestanden |
| 1 | eine Prüfung bestanden |
| 0 | keine bestanden |
| — | keine Bilder auf der Seite → nicht erhoben |

> **Ein Hinweis zur dritten Prüfung.** Sie fasst zwei Anforderungen zusammen — Größenangaben und Dateigröße — und vergibt dafür einen einzigen Punkt. Beide müssen erfüllt sein. Wer alle Größenangaben gesetzt hat, aber ein einziges Bild von 400 Kilobyte auf der Seite lässt, bekommt für diese Prüfung nichts. Das ist streng, und es ist der Grund, warum P5 in der Praxis selten mit 3 Punkten abschließt.

::: MRG
🔴 **Zu prüfen**
Vier Anforderungen, drei Punkte. Siehe redaktionelle Anmerkungen.
:::

**Zur Dateigröße:** Geprüft wird eine Stichprobe von bis zu acht Bildern. Ein Bild über 300 Kilobyte in dieser Stichprobe genügt, um die dritte Prüfung ausfallen zu lassen. Wenn Sie also viele Bilder haben und nur einzelne davon groß sind, kann das Ergebnis zwischen zwei Messungen schwanken — je nachdem, welche acht in die Stichprobe geraten.

### So beheben Sie es

**Das ist der günstigste Punktgewinn im ganzen Standard**, und er braucht niemanden, der programmieren kann.

1. **Alle Bilder durch ein Komprimierungswerkzeug schicken.** Zielgröße: unter 200 Kilobyte für große Bilder, unter 80 für kleine. Der sichtbare Qualitätsverlust ist bei richtiger Einstellung keiner.
2. **Ins moderne Format umwandeln.** Die meisten Baukastensysteme tun das inzwischen automatisch — aber nur für neu hochgeladene Bilder. Altbestände bleiben, wie sie sind.
3. **Verzögertes Nachladen aktivieren.** Bei den meisten Systemen ein Schalter. Bei selbstgebauten Seiten ein Zusatz von zwölf Zeichen je Bild.
4. **Größenangaben ergänzen.** Wirkt zugleich auf P2.

::: ABB 7.1
format:   breit
titel:    Wo die Ladezeit hingeht
zweck:    Der Leser soll sehen, dass ein einziges Bild den größten
          Teil der Wartezeit verursacht — und dass die Korrektur
          an einer Stelle vier Kriterien berührt.
inhalt:   Waagerechter Zeitstrahl 0 bis 4 Sekunden, unterteilt in
          Abschnitte: Serverantwort, Schriftart vom fremden Server,
          Skripte im Seitenkopf, Kopfbild 1,8 MB.
          Der letzte Abschnitt nimmt deutlich mehr als die Hälfte ein.
          Die Marken 2,5 s und 4,0 s als senkrechte Linien mit
          den Punktwerten 4 / 2 / 0 beschriftet.
          Darunter eine zweite, kürzere Leiste: derselbe Aufbau
          nach der Bildkomprimierung, Gesamtdauer 1,9 s.
quelle:   Fall aus 7.4 — Werte konsistent zu P1 = 2 Punkte halten
bezug:    Abschnitt 7.9, nach „So beheben Sie es"
bu:       Ein Bild von 1,8 Megabyte kostete diesen Betrieb acht Punkte.
sw-fest:  ja
:::

---

## 7.10 Ihre Punkte in dieser Kategorie

| Code | Kriterium | Möglich | Erreicht | Nicht erhoben |
|---|---|---|---|---|
| P1 | Ladezeit des Hauptinhalts | 4 | ____ | ☐ |
| P2 | Layoutstabilität | 3 | ____ | ☐ |
| P3 | Reaktionszeit | 2 | ____ | ☐ |
| P4 | Mobiler Gesamtwert | 3 | ____ | ☐ |
| P5 | Bildoptimierung | 3 | ____ | ☐ |
| | **Summe** | **15** | ____ | |

**Wichtig für Ihre Auswertung:** Jedes hier angekreuzte Kästchen senkt Ihr anwendbares Maximum um die entsprechende Punktzahl. Tragen Sie die Summe der nicht erhobenen Punkte in Kapitel 13 ein.

---

## 7.11 Vier verbreitete Irrtümer

**„Bei mir lädt die Seite sofort."**
Sie laden sie aus dem Zwischenspeicher Ihres Browsers, über die Verbindung Ihres Büros, auf Ihrem Gerät. Ein neuer Besucher lädt sie zum ersten Mal, unterwegs, auf einem drei Jahre alten Telefon. Genau das simuliert die Messung — und deshalb weicht sie so oft von Ihrem Eindruck ab.

**„Wir haben schöne, große Bilder, das ist uns wichtig."**
Das ist kein Widerspruch. Ein komprimiertes Bild sieht auf einem Bildschirm identisch aus. Der Unterschied ist nicht sichtbar, er ist nur messbar — und im Wartebalken spürbar. Was Sie hochladen, ist für den Druck gedacht; was der Bildschirm braucht, ist ein Bruchteil davon.

**„Wir brauchen einen schnelleren Server."**
Selten die Ursache und fast nie der erste Schritt. Bei einem typischen Befund entfallen wenige Zehntelsekunden auf die Serverantwort und mehrere Sekunden auf das, was danach geladen wird. Ein schnellerer Server verbessert den kleineren Teil.

**„Google straft langsame Seiten ab, deshalb ist das wichtig."**
Die Wirkung auf die Auffindbarkeit gibt es, sie ist aber der schwächere Grund. Der stärkere: Wer wartet, geht — und zwar bevor er gesehen hat, was Sie anbieten. Der entgangene Besucher kostet Sie mehr als der Rangplatz.

---

## Das Wichtigste aus diesem Kapitel

> - **Fünf Kriterien, 15 Punkte.** Vier stammen aus einer externen Messung, nur P5 wird eigenständig erhoben.
> - **Fällt die externe Messung aus**, sind zwölf Punkte hier und sechs in Kapitel 8 nicht erhebbar. Sie fallen aus der Rechnung, nicht auf null.
> - **P3 ist bei kleinen Betriebsseiten fast immer nicht erhebbar.** Das ist der Normalfall und kein Nachteil.
> - **P1 und P2 springen** — 4/2/0 und 3/1/0. Die Schwellen stammen aus dem Messverfahren.
> - **Ein zu großes Kopfbild** ist der häufigste Einzelbefund und wirkt auf P1, P4 und P5 gleichzeitig.
> - **Größenangaben an Bildern** wirken auf P2 und P5 zugleich.
> - **Bildoptimierung ist der günstigste Punktgewinn im ganzen Standard** und braucht keine Programmierkenntnisse.

---

<!-- REDAKTIONELLE ANMERKUNGEN — NICHT DRUCKEN -->

## Offene Punkte zu Kapitel 7

| # | Punkt | Wer | Status |
|---|---|---|---|
| 1 | 🔴 **P5: vier Anforderungen, drei Punkte — bestätigt.** Der Restarbeiten-Report führt das als A6 mit dem Verdacht, eine Teilprüfung könne nicht zählen. Nachgelesen: Es sind drei Prüfungen zu je einem Punkt, aber die dritte fasst **Größenangaben und Dateigröße** zusammen und verlangt beides. Der Kriterienhinweis nennt vier Dinge, vergeben werden drei Punkte. Abschnitt 7.9 weist es offen aus. **Entscheidung nötig:** entweder P5 auf 4 Punkte, oder die Dateigröße als eigene Prüfung streichen und in den Hinweis verschieben | Technik / GF | **offen** |
| 2 | 🔴 **B4 — externe Messung.** Dieses Kapitel steht und fällt damit, dass die Messung läuft. Der Zugang ist inzwischen gesetzt, aber sieben Aufrufer lasen lange einen Schlüsselnamen, den es nicht gab. **Vor Drucklegung nachweisen**, dass P1–P4 in einem echten Lauf tatsächlich Werte liefern und nicht „nicht erhoben" | Technik | **offen** |
| 3 | **Stichprobengröße bei P5.** Geprüft werden bis zu acht Bilder. Bei bildreichen Seiten kann das Ergebnis zwischen zwei Läufen schwanken. Abschnitt 7.9 sagt es. Kapitel 3 verspricht aber Wiederholbarkeit — **Widerspruch prüfen**, notfalls Stichprobe erhöhen oder in Kapitel 3 einschränken | Technik / Autor | **offen** |
| 4 | **Fachbegriffe.** Das Kapitel vermeidet LCP, CLS und INP im Fließtext vollständig. Beim Lektorat prüfen, ob die Kürzel in einer Marginalie stehen sollten — Leser, die eine Messung selbst aufrufen, sehen dort die englischen Bezeichnungen und müssen zuordnen können | Lektorat | **empfohlen** |
| 5 | **Der Messdienst wird nicht namentlich genannt.** Bewusste Entscheidung: Namen und Oberflächen von Prüfwerkzeugen veralten vor der zweiten Auflage. Prüfen, ob der Leser ihn trotzdem braucht, um selbst zu messen — dann gehört er in den Anhang, nicht in den Fließtext | Autor | **entscheiden** |
| 6 | **Fall Elektro Hansen:** P1 = 2, P2 = 3, P3 = 1, P4 = 1, P5 = 0 ergibt 7. Muss zur Kategorietabelle in Kapitel 3 passen. **P3 ist hier erhoben** — das ist für einen 14-Mann-Betrieb eher unwahrscheinlich, aber Kapitel 3 rechnet mit vollem Maximum 103. Entweder so lassen und in 7.3 nicht darauf verweisen, oder Kapitel 3 auf ein Beispiel mit nicht erhobenem P3 umstellen | Autor | **Drift-Kandidat** |
| 7 | **Der Zusammenhang zwischen Ladezeit und Absprung** wird in 7.2 und 7.11 behauptet, aber nicht belegt. Der Restarbeiten-Report führt ihn als C5 mit dem Hinweis „externe Quelle oder eigene Auswertung". Entweder belegen oder abschwächen — **nicht mit einer erfundenen Prozentzahl unterlegen** | Autor | **offen** |
| 8 | Nur eine Abbildung auf 16 Seiten. Zwei weitere Kandidaten: die drei Teilprüfungen von P5 als Checkliste, und eine Gegenüberstellung „so sieht die Seite nach 1 / 2 / 3 Sekunden aus" | Gestaltung | offen |

**Abbildungen in diesem Kapitel:** 1 (ABB 7.1 breit)
**Marginalien:** 7
**Geschätzter Satzumfang:** 15–16 Seiten
