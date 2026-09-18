---
kapitel: 5
titel: "Performance & Core Web Vitals"
punkte: 15
kriterien: 5
status: entwurf-fertig
zuletzt_geprueft: 2026-08-14
standard_version: "2026.2"
---

# 5. Performance & Core Web Vitals — 15 Punkte

## 5.1 Was hier bewertet wird

Fünf Kriterien, zusammen 15 Punkte.

| Code | Kriterium | Punkte |
|---|---|---|
| P1 | Ladezeit des Hauptinhalts | 4 |
| P2 | Stabilität des Layouts beim Laden | 3 |
| P3 | Reaktionszeit auf Eingaben | 2 |
| P4 | Gesamtbewertung auf dem Mobiltelefon | 3 |
| P5 | Bildoptimierung | 3 |

Die ersten drei Kriterien sind das, was Google seit einigen Jahren als **Core Web Vitals**
bezeichnet — drei Messwerte, die beschreiben, wie sich eine Website für einen echten
Besucher anfühlt. Sie sind nicht von Google erfunden worden, um Websitebetreiber zu ärgern,
sondern weil sich herausgestellt hat, dass diese drei Größen ziemlich genau vorhersagen, ob
jemand bleibt oder geht.

Der große Vorteil dieser Kategorie: Sie können nichts davon wegdiskutieren. Es sind Zahlen,
sie werden mit demselben Verfahren bei jedem erhoben, und Sie können sie in fünf Minuten
selbst nachmessen.

Der große Nachteil: **Sie sehen diese Zahlen bei sich selbst nie.** Ihre Website liegt in
Ihrem Browser-Zwischenspeicher, Sie sitzen im Büro-WLAN an einem Rechner, den Sie sich
ausgesucht haben. Ihre Kunden sitzen unterwegs im Mobilfunknetz an einem drei Jahre alten
Telefon und rufen Ihre Seite zum ersten Mal auf. Das ist ein völlig anderes Erlebnis, und
nur dieses zählt.

---

## 5.2 Der Praxisfall

Der Elektrobetrieb aus Kapitel 2 erreicht hier 8 von 15 Punkten — sein schlechtestes
Ergebnis im ganzen Audit.

Die Ursache ist eine einzige. Auf der Startseite läuft eine Bilderfolge mit sechs Aufnahmen
von abgeschlossenen Projekten: eine Schaltanlage, eine Ladestation, eine Baustelle. Gute
Fotos, echte Arbeit, genau die Bilder, die auf eine Handwerkerseite gehören.

Sie wurden vom Mobiltelefon des Meisters hochgeladen, so wie sie aufgenommen wurden. Jedes
Bild hat eine Kantenlänge von über 4.000 Bildpunkten und eine Dateigröße zwischen vier und
sechs Megabyte. Auf der Website werden sie auf etwa 1.200 Bildpunkte Breite verkleinert
dargestellt — heruntergeladen wird trotzdem die volle Datei.

Ein Besucher im Mobilfunknetz lädt beim Aufruf der Startseite also rund 28 Megabyte
Bilddaten. Das dauert.

**Die Auswirkung auf die Bewertung:**

| Kriterium | Messwert | Punkte |
|---|---|---|
| P1 Ladezeit Hauptinhalt | 4,8 Sekunden | 1 von 4 |
| P2 Layoutstabilität | 0,04 | 3 von 3 |
| P3 Reaktionszeit | 180 ms | 2 von 2 |
| P4 Mobilbewertung | 41 von 100 | 1 von 3 |
| P5 Bildoptimierung | 1 von 3 Anforderungen | 1 von 3 |
| | | **8 von 15** |

Bemerkenswert daran: Die Website ist technisch sauber gebaut. Das Layout springt nicht, die
Bedienung reagiert schnell. Es ist ein einziges Versäumnis, das drei von fünf Kriterien
nach unten zieht.

**Die Behebung:** Die sechs Bilder werden auf 1.600 Bildpunkte Breite verkleinert, in ein
modernes Format umgewandelt und landen bei etwa 140 Kilobyte pro Datei — statt 28 Megabyte
also knapp ein Megabyte für die ganze Seite. Die Ladezeit fällt auf 2,1 Sekunden.

Aufwand: ein halber Arbeitstag, in weiten Teilen automatisierbar. Gewinn in dieser
Kategorie: von 8 auf 14 Punkte. Dazu kommen in Kapitel 6 weitere Punkte, weil bei
derselben Gelegenheit die Alternativtexte ergänzt werden.

---

## 5.3 Felddaten und Labordaten — warum das für Sie wichtig ist

Bevor wir zu den Kriterien kommen, eine Unterscheidung, die Sie kennen sollten, weil sie
Ihre eigenen Messungen erklärt.

**Felddaten** sind echte Messwerte von echten Besuchern. Google sammelt sie über den
Chrome-Browser und stellt sie anonymisiert bereit. Sie bilden die Wirklichkeit ab: alle
Gerätetypen, alle Verbindungsqualitäten, alle Tageszeiten.

**Labordaten** entstehen durch eine simulierte Messung: Ein Testsystem ruft Ihre Seite unter
festgelegten Bedingungen auf — gedrosselte Verbindung, definierte Rechenleistung — und misst
das Ergebnis.

Der Haken: **Felddaten gibt es nur, wenn Ihre Website genügend Besucher hat.** Wo die Zahl
zu klein ist, veröffentlicht Google keine Werte — aus Datenschutzgründen. Für einen großen
Teil der Leser dieses Buches bedeutet das: Für Ihre Website existieren keine Felddaten, und
alles, was Sie messen können, sind Labordaten.

Das ist kein Problem, solange Sie es wissen:

| | Felddaten | Labordaten |
|---|---|---|
| Bilden ab | tatsächliche Nutzung | eine definierte Testbedingung |
| Verfügbar | erst ab genügend Besuchern | immer |
| Schwanken | wenig | spürbar zwischen Messungen |
| Gut für | Bewertung des Ist-Zustands | Ursachensuche und Vorher-Nachher-Vergleich |

**Für den Selbsttest heißt das:** Messen Sie zwei- bis dreimal hintereinander und nehmen
Sie den mittleren Wert. Eine einzelne Labormessung kann um mehrere Zehntelsekunden daneben
liegen.

**Für die Bewertung heißt das:** Wo Felddaten vorliegen, werden sie verwendet. Wo nicht,
Labordaten mit entsprechender Kennzeichnung im Bericht. Ein Wechsel der Datengrundlage
zwischen zwei Prüfungen muss ausgewiesen sein — sonst sieht eine normale Messschwankung
wie eine Verschlechterung aus.

---

## 5.4 P1 — Ladezeit des Hauptinhalts · 4 Punkte

### Was gemessen wird

Der Fachbegriff lautet *Largest Contentful Paint*, abgekürzt LCP. Gemessen wird die Zeit
vom Aufruf der Seite bis zu dem Moment, in dem das **größte sichtbare Element** fertig
geladen ist — in der Regel das Hauptbild oder die Überschrift ganz oben.

Es geht also nicht darum, wann die Seite vollständig geladen ist. Es geht darum, wann der
Besucher den Eindruck hat, dass etwas da ist.

Das ist der wichtigste der drei Messwerte, und er ist bei kleinen Unternehmenswebsites fast
immer der schwächste. Der Grund ist in neunzehn von zwanzig Fällen derselbe: zu große
Bilder.

### So wird bewertet

Gemessen wird mobil.

| Punkte | Messwert |
|---|---|
| **4** | bis 2,5 Sekunden |
| **3** | über 2,5 bis 3,0 Sekunden |
| **2** | über 3,0 bis 4,0 Sekunden |
| **1** | über 4,0 bis 5,0 Sekunden |
| **0** | über 5,0 Sekunden |

Die Grenze bei 2,5 Sekunden ist keine Erfindung dieses Standards, sondern der von Google
veröffentlichte Schwellenwert für „gut". Ab 4 Sekunden gilt der Wert offiziell als
schlecht.

### Warum das Geld kostet

Der Zusammenhang zwischen Ladezeit und Absprung ist eine der am besten belegten Größen im
Onlinegeschäft. Die Faustregel: Jede zusätzliche Sekunde kostet Besucher, und der Effekt
ist in den ersten Sekunden am stärksten.

Für Sie praktisch bedeutsam ist etwas anderes: **Der Absprung geschieht, bevor der Besucher
irgendetwas von Ihnen gesehen hat.** Er kennt Ihr Angebot nicht, Ihre Referenzen nicht,
Ihre Bewertungen nicht. Er hat auf einen weißen Bildschirm geschaut und ist zurückgegangen.
Alle Mühe, die Sie in den Inhalt gesteckt haben, war für diesen Menschen umsonst.

### So prüfen Sie selbst — 10 Minuten

**Die Messung:** Rufen Sie Googles PageSpeed Insights auf, geben Sie Ihre Adresse ein und
achten Sie darauf, dass die Auswertung für **Mobilgeräte** angezeigt wird — das ist meist
die Voreinstellung, aber prüfen Sie es. Der Wert für LCP steht in der Liste der Kennzahlen.

**Die Gegenprobe, die mehr wert ist als jede Zahl:** Nehmen Sie Ihr eigenes Telefon,
schalten Sie WLAN aus, öffnen Sie ein privates Browserfenster und rufen Sie Ihre Website
auf. Zählen Sie mit. Fühlt sich das gut an? Würden Sie warten, wenn es nicht Ihre eigene
Firma wäre?

### So beheben Sie es

In der Reihenfolge der Wirksamkeit:

1. **Bilder verkleinern und umwandeln** — löst das Problem in den meisten Fällen allein.
   Siehe P5.
2. **Fremddienste entfernen oder verzögern** — jedes eingebundene Skript verzögert. Ihre
   Liste aus Kapitel 4 ist die Vorlage.
3. **Zwischenspeicherung aktivieren** — meist eine Einstellung beim Hoster.
4. **Schriftarten lokal einbinden** — bringt Punkte in drei Kategorien gleichzeitig.

Erst wenn all das erledigt ist und die Seite immer noch langsam ist, lohnt sich das
Gespräch über einen besseren Server.

---

## 5.5 P2 — Stabilität des Layouts · 3 Punkte

### Was gemessen wird

*Cumulative Layout Shift*, abgekürzt CLS. Gemessen wird, wie stark der Seiteninhalt beim
Laden noch verspringt.

Sie kennen den Effekt: Sie beginnen zu lesen, wollen auf etwas tippen — und im selben
Moment lädt ein Bild nach, alles rutscht nach unten, und Sie haben auf etwas anderes
getippt. Auf dem Mobiltelefon ist das besonders ärgerlich, weil dort das falsche Ziel
oft eine Telefonnummer oder ein Werbebanner ist.

Der Wert ist eine Verhältniszahl ohne Einheit. Je kleiner, desto ruhiger die Seite.

### Die Ursachen

Fast immer eine von dreien:

- **Bilder ohne Größenangabe.** Der Browser weiß nicht, wie viel Platz er freihalten soll,
  und schiebt alles beiseite, sobald das Bild da ist.
- **Nachgeladene Schriftarten.** Der Text erscheint zunächst in einer Ersatzschrift und
  springt um, wenn die richtige geladen ist.
- **Nachträglich eingefügte Elemente.** Ein Einwilligungsbanner, eine Hinweisleiste, ein
  Bewertungsfenster, das sich oben einschiebt.

### So wird bewertet

| Punkte | Messwert |
|---|---|
| **3** | bis 0,10 |
| **2** | über 0,10 bis 0,15 |
| **1** | über 0,15 bis 0,25 |
| **0** | über 0,25 |

### So prüfen Sie selbst — 3 Minuten

Der Messwert steht in derselben Auswertung wie LCP. Die anschauliche Prüfung: Rufen Sie
Ihre Seite auf dem Telefon auf und beobachten Sie die ersten zwei Sekunden. Springt etwas?

### So beheben Sie es

Bei Bildern Höhe und Breite im Quelltext angeben — das ist eine Kleinigkeit, die jedes
gängige System kann und die viele Baukästen von sich aus richtig machen. Bei Schriftarten
eine Ersatzschrift mit ähnlichen Maßen hinterlegen. Bei Bannern dafür sorgen, dass sie
sich über den Inhalt legen, statt ihn zu verschieben.

Aufwand: meist ein bis zwei Stunden für einen Fachbetrieb.

---

## 5.6 P3 — Reaktionszeit auf Eingaben · 2 Punkte

### Was gemessen wird

*Interaction to Next Paint*, abgekürzt INP. Gemessen wird, wie lange es dauert, bis die
Seite sichtbar auf eine Eingabe reagiert — ein Antippen, ein Klick, eine Eingabe im
Formular.

Dieser Wert hat 2024 einen älteren Messwert abgelöst, der nur die allererste Interaktion
betrachtete. INP betrachtet alle und ist deshalb aussagekräftiger.

### Eine Besonderheit, die Sie kennen sollten

**INP lässt sich nur aus Felddaten ermitteln.** Eine simulierte Messung kann ihn nicht
liefern, weil dabei niemand etwas antippt. Hat Ihre Website nicht genug Besucher für
Felddaten, gibt es diesen Wert bei Ihnen schlicht nicht.

Der Standard verwendet in diesem Fall einen Ersatzwert aus der Labormessung: die Zeit, in
der die Seite während des Ladens mit sich selbst beschäftigt ist und deshalb nicht
reagieren könnte. Das ist ein guter Näherungswert und wird im Bericht als solcher
gekennzeichnet.

Lässt sich beides nicht ermitteln, fällt das Kriterium nach dem Grundsatz aus Kapitel 2
aus der Wertung — es wird nicht geschätzt und nicht mit null bewertet.

### So wird bewertet

| Punkte | Messwert (Felddaten) | Ersatzwert (Labor) |
|---|---|---|
| **2** | bis 200 ms | bis 200 ms |
| **1** | über 200 bis 500 ms | über 200 bis 600 ms |
| **0** | über 500 ms | über 600 ms |

### Die Ursachen

Zu viel Programmcode, der beim Laden ausgeführt wird. Bei kleinen Unternehmenswebsites
kommt der selten von der Seite selbst, sondern von Zusatzmodulen: Bildergalerien,
Animationseffekte, Buchungssysteme, Chatfenster, Statistikwerkzeuge.

Faustregel: Jedes Modul, das Sie nicht wirklich brauchen, ist ein Modul zu viel. Das gilt
für die Ladezeit wie für den Datenschutz — und deshalb lohnt sich das Ausmisten doppelt.

---

## 5.7 P4 — Gesamtbewertung auf dem Mobiltelefon · 3 Punkte

### Was gemessen wird

Zusätzlich zu den drei Einzelwerten wird die zusammenfassende Bewertung für die mobile
Nutzung herangezogen — eine Zahl von 0 bis 100, die mehrere Messgrößen zusammenfasst.

Warum ein eigenes Kriterium dafür? Weil die drei Einzelwerte Momentaufnahmen bestimmter
Aspekte sind. Eine Seite kann bei LCP gut abschneiden und trotzdem insgesamt träge sein —
etwa weil sie sehr viel Programmcode nachlädt, der erst nach dem sichtbaren Aufbau greift.

Wichtig ist die getrennte Messung: **mobil und am Rechner werden unabhängig voneinander
erhoben.** In einer früheren Fassung dieses Verfahrens wurde der Rechnerwert einfach als
Mobilwert ausgegeben — das ergab durchweg zu gute Zahlen, weil ein Mobiltelefon deutlich
weniger Rechenleistung hat und über eine langsamere Verbindung geht. Für die Bewertung
zählt ausschließlich der Mobilwert.

### So wird bewertet

| Punkte | Mobilbewertung |
|---|---|
| **3** | 90 bis 100 |
| **2** | 70 bis 89 |
| **1** | 50 bis 69 |
| **0** | unter 50 |

Ordnen Sie diese Zahl richtig ein: Ein Wert von 90 und mehr ist für eine
Unternehmenswebsite mit Bildern anspruchsvoll. **70 bis 89 ist ein solides Ergebnis**, mit
dem Sie gut leben können. Unter 50 haben Sie ein handfestes Problem.

### So prüfen Sie selbst — 3 Minuten

Dieselbe Auswertung wie bei P1. Die große Zahl oben auf der Seite ist dieser Wert. Achten
Sie darauf, dass die Ansicht für Mobilgeräte gewählt ist — die Zahl für Rechner ist
regelmäßig zwanzig bis vierzig Punkte besser und verleitet zu falscher Zufriedenheit.

---

## 5.8 P5 — Bildoptimierung · 3 Punkte

### Was geprüft wird

Drei Anforderungen, je eine ergibt einen Punkt:

**1. Moderne Bildformate.** Die überwiegende Zahl der Bilder liegt in einem aktuellen
Format vor. Diese Formate liefern bei gleicher Bildqualität deutlich kleinere Dateien als
die klassischen — häufig ein Drittel bis ein Viertel der Größe. Das ist der größte
Einzelhebel für die Ladezeit.

**2. Feste Abmessungen und verzögertes Laden.** Höhe und Breite sind angegeben, damit
nichts verspringt. Bilder, die erst weiter unten auf der Seite auftauchen, werden erst
geladen, wenn der Besucher dorthin scrollt.

**3. Vernünftige Dateigrößen.** Kein einzelnes Bild überschreitet 300 Kilobyte. Für ein
gutes Foto auf einer Website ist das reichlich bemessen.

### Der häufigste Fehler in diesem ganzen Buch

Fotos werden direkt vom Telefon oder aus der Kamera hochgeladen. Ein aktuelles
Mobiltelefon nimmt mit 4.000 und mehr Bildpunkten Kantenlänge auf. Dargestellt wird das
Bild anschließend mit vielleicht 800 Bildpunkten Breite.

Der Browser lädt trotzdem die volle Datei herunter und verkleinert sie erst danach. Der
Besucher bezahlt also mit Ladezeit und Datenvolumen für eine Auflösung, die er nie zu
sehen bekommt.

Das ist kein technisches Problem. Es ist ein Ablaufproblem: Niemand hat festgelegt, dass
Bilder vor dem Hochladen aufbereitet werden.

### So wird bewertet

| Punkte | Bedingung |
|---|---|
| **3** | Alle drei Anforderungen erfüllt |
| **2** | Zwei Anforderungen erfüllt |
| **1** | Eine Anforderung erfüllt |
| **0** | Keine erfüllt |

### So prüfen Sie selbst — 10 Minuten

**Die einfache Prüfung:** Klicken Sie auf Ihrer Website mit der rechten Maustaste auf ein
Bild und wählen Sie „Grafik anzeigen" oder „Bild in neuem Tab öffnen". In der Adresszeile
sehen Sie die Dateiendung. Endet sie auf `.jpg` oder `.png`, ist es ein klassisches Format.

**Die genaue Prüfung:** Die Auswertung von PageSpeed Insights führt unter den Empfehlungen
regelmäßig Punkte wie „Bilder in modernen Formaten bereitstellen" oder „Bilder richtig
dimensionieren" auf — mit einer Liste der betroffenen Dateien und der jeweils möglichen
Einsparung. Diese Liste ist Ihre Arbeitsanweisung.

### So beheben Sie es und halten es dann so

Die Behebung ist einmalig Arbeit, die Sie automatisieren können und sollten:

| Schritt | Vorgehen |
|---|---|
| Bestehende Bilder | Mit einem kostenlosen Werkzeug auf maximal 1.600 Bildpunkte Breite verkleinern und in ein modernes Format umwandeln |
| Neue Bilder | Feste Regel im Betrieb: Vor dem Hochladen verkleinern. Wer Bilder pflegt, bekommt diese Regel schriftlich |
| Dauerhaft | Die meisten Systeme können Bilder beim Hochladen automatisch aufbereiten. Einmal einrichten, danach kein Thema mehr |

Der dritte Punkt ist der eigentlich wichtige. Ohne ihn ist Ihre Seite in zwei Jahren wieder
dort, wo sie heute steht — denn irgendjemand wird Baustellenfotos hochladen, und er wird es
so tun, wie es am schnellsten geht.

---

## 5.9 Ihre Punkte in dieser Kategorie

| Code | Kriterium | Messwert | Max. | Ihre Punkte |
|---|---|---|---|---|
| P1 | Ladezeit Hauptinhalt | ______ s | 4 | ______ |
| P2 | Layoutstabilität | ______ | 3 | ______ |
| P3 | Reaktionszeit | ______ ms | 2 | ______ |
| P4 | Mobilbewertung | ______ /100 | 3 | ______ |
| P5 | Bildoptimierung | ______ /3 | 3 | ______ |
| | **Summe** | | **15** | **______** |

**Datengrundlage:** ☐ Felddaten ☐ Labordaten ☐ gemischt

**Nicht ermittelbar:** ______________________ (aus dem anwendbaren Maximum abziehen)

---

## 5.10 Vier verbreitete Irrtümer

**„Bei mir lädt die Seite sofort."**
Natürlich. Sie liegt in Ihrem Zwischenspeicher, Sie sind im eigenen WLAN, und Sie kennen
das Layout. Der Wert, der zählt, ist der beim ersten Besuch eines fremden Menschen im
Mobilfunknetz. Machen Sie die Gegenprobe aus 5.4 — es ist die lehrreichste Übung dieses
Kapitels.

**„Ein größerer Server würde helfen."**
Selten. Bei kleinen Unternehmenswebsites liegt die Ursache fast immer bei den Bildern und
den eingebundenen Fremddiensten, nicht bei der Rechenleistung. Ein besserer Server
beschleunigt die Auslieferung von 28 Megabyte Bilddaten kaum — die müssen trotzdem durch
die Mobilfunkverbindung. Erst optimieren, dann aufrüsten.

**„Google bestraft langsame Seiten."**
Präziser: Geschwindigkeit ist ein Faktor unter vielen und wirkt vor allem dann, wenn zwei
Ergebnisse sonst gleichwertig sind. Der wirtschaftlich größere Effekt ist ein anderer und
hat mit Google nichts zu tun: Besucher, die nicht warten, sind weg — unabhängig davon, auf
welchem Platz Sie stehen.

**„Ohne Felddaten kann ich nichts messen."**
Doch. Labordaten sind für die Ursachensuche und den Vorher-Nachher-Vergleich sogar besser
geeignet, weil sie unter gleichbleibenden Bedingungen entstehen. Sie schwanken nur mehr —
also messen Sie mehrfach und nehmen den mittleren Wert.

---

> ### Das Wichtigste aus diesem Kapitel
>
> - **15 Punkte in fünf Kriterien**, alle mit klaren Schwellenwerten und in fünf Minuten
>   selbst nachmessbar.
> - **Gemessen wird mobil.** Der Wert für Rechner ist regelmäßig zwanzig bis vierzig
>   Punkte besser und führt in die Irre.
> - **Zu große Bilder sind die Ursache Nummer eins** und ziehen gleich drei Kriterien nach
>   unten: Ladezeit, Mobilbewertung und Bildoptimierung.
> - Zielwerte: **Ladezeit bis 2,5 Sekunden**, Layoutstabilität bis 0,10, Reaktionszeit bis
>   200 Millisekunden, Mobilbewertung ab 70.
> - **Felddaten gibt es nur bei genügend Besuchern.** Ohne sie zählen Labordaten — mehrfach
>   messen, mittleren Wert nehmen.
> - Die dauerhafte Lösung ist nicht das einmalige Aufräumen, sondern die **automatische
>   Bildaufbereitung beim Hochladen.** Ohne sie ist die Seite in zwei Jahren wieder
>   langsam.

---

## Redaktionelle Anmerkungen (nicht drucken)

**Abgleich mit dem Code steht aus.** Kriterienzuschnitt und Punktzahlen (P1 4, P2 3, P3 2,
P4 3, P5 3) stammen aus `audit-anforderungen-2026-08-11.md` § 3.2. Die Schwellenwerte in
5.4 bis 5.8 sind an den offiziellen Core-Web-Vitals-Grenzen ausgerichtet und gegen
`audit_pagespeed.py` und `audit_criteria.py` abzugleichen.

**Offener Punkt mit direkter Wirkung auf dieses Kapitel:** Ist auf Render ein
PageSpeed-Schlüssel gesetzt? Ohne ihn bleiben P1 bis P4 dauerhaft „nicht erhoben", und das
Kapitel beschreibt dann eine Bewertung, die im Bericht nie stattfindet. Das ist offener
Punkt 1 aus § 6 des Anforderungskatalogs und sollte vor Drucklegung geklärt sein.

**P3 — konstruierte Ersatzwertschwellen.** Der Anforderungskatalog nennt TBT als
Ersatzindikator für INP, ohne Schwellen zu benennen. Die Werte in 5.6 (bis 200 ms, bis
600 ms) sind an gängigen Bewertungsgrenzen orientiert und müssen bestätigt werden. Wenn
`audit_pagespeed.py` andere Grenzen verwendet, gilt der Code.

**P5 — Zuschnitt zu prüfen.** Der Katalog beschreibt vier Teilprüfungen (Format,
Dateigrößen, verzögertes Laden, feste Abmessungen) bei 3 Punkten. Ich habe im Kapitel drei
Anforderungen gebildet, indem „verzögertes Laden" und „feste Abmessungen" zusammengefasst
wurden. Falls der Code vier Teilprüfungen bei 3 Punkten führt, entsteht dasselbe
Rundungsproblem wie seinerzeit bei der UX-Kategorie. **Bitte gezielt prüfen.**

**Zu belegen:** Die Aussage in 5.4, dass der Zusammenhang zwischen Ladezeit und Absprung
gut belegt ist. Hier wäre eine Quellenangabe im Anhang sinnvoll — oder, besser, eine eigene
Auswertung aus den KAS-Audits: durchschnittlicher LCP der geprüften Websites und Verteilung
über die Punktstufen. Das wäre eine Zahl, die sonst niemand hat.

**Praxisfall 5.2** setzt Fall A fort. Punktverteilung (P1 1, P2 3, P3 2, P4 1, P5 1 = 8)
ist mit Kapitel 2 abgestimmt. Die Rechnung „28 Megabyte, danach knapp 1 Megabyte" ist
plausibel gerechnet, aber konstruiert — nach den ersten echten Läufen durch einen realen
Fall ersetzen.

**Abbildungen (4 Stück):**
1. Die drei Core Web Vitals als Zeitstrahl eines Seitenaufbaus, mit den Schwellenwerten
2. Vorher-Nachher der Bilderfolge aus 5.2: Dateigrößen und resultierende Ladezeit
3. Layoutsprung als Bildfolge in drei Schritten — der Daumen tippt daneben
4. Screenshot der PageSpeed-Auswertung mit Markierung, wo die vier Werte stehen. **Achtung:**
   Fremde Benutzeroberflächen ändern sich; Abbildung schematisch nachbauen statt
   abfotografieren, sonst veraltet sie vor der zweiten Auflage.
