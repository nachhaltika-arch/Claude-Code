---
kapitel: 3
teil: "I — Warum ein Standard"
titel: "Das Bewertungssystem"
autor: "Manuel Potter"
status: entwurf
zuletzt_geprueft: 2026-08-24
standard_version: "2026.2"
zielumfang: 16 Seiten
---

<!-- KAPITELÖFFNER — rechte Seite -->

# 3

# Das Bewertungssystem

> Acht Kategorien, 39 Kriterien, 103 Punkte. Was davon zählt, was nicht zählt und warum am Ende trotzdem eine Zahl zwischen 0 und 100 steht.

::: ABB 3.1
format:   ganz
titel:    Kapitelöffner — das Bewertungssystem auf einen Blick
zweck:    Der Leser soll vor dem ersten Wort sehen, wie das System
          aufgebaut ist. Die Abbildung ersetzt keine Erklärung,
          sie gibt eine Landkarte.
inhalt:   Senkrechter Ablauf von oben nach unten, vier Stufen:
          (1) 39 Kriterien in 8 Kategorien
          (2) davon anwendbar für Ihre Branchenklasse
          (3) davon tatsächlich prüfbar
          (4) erreichte Punkte ÷ prüfbare Punkte × 100 = Ihr Wert
          Rechts daneben eine schmale Leiste mit den fünf Stufen.
          Kein Text außer den vier Zeilen und den Stufennamen.
quelle:   Struktur aus audit_criteria.py — keine Zahlen erfinden
bezug:    Kapitelöffner, ganzseitig links vom Kapitelbeginn
bu:       Vom Kriterium zur Stufe — der Weg in vier Schritten.
sw-fest:  ja
:::

<!-- SEITENUMBRUCH -->

## 3.1 Was der Standard misst — und was er nicht misst

Bevor Sie erfahren, wie gerechnet wird, sollten Sie wissen, worüber überhaupt gerechnet wird. Denn der häufigste Fehler im Umgang mit Website-Bewertungen ist nicht, dass falsch gerechnet wird. Er ist, dass etwas gemessen wird, was gar nicht gemessen werden kann — und die Zahl trotzdem so aussieht, als wäre sie belastbar.

Der Homepage Standard bewertet Ihre Website **von außen**. Genau so, wie ein Kunde, ein Bewerber oder ein Wettbewerber sie sieht. Es wird kein Zugang zu Ihrem System benötigt, kein Passwort, keine Erlaubnis. Das hat einen Vorteil und einen Preis.

**Der Vorteil:** Die Bewertung ist wiederholbar und vergleichbar. Zwei Websites werden nach demselben Maßstab gemessen, unabhängig davon, wer sie gebaut hat und womit. Sie können Ihre Seite mit der eines Wettbewerbers vergleichen, ohne dessen Zugangsdaten zu haben. Und Sie können in sechs Monaten erneut messen und wissen, ob sich etwas verändert hat.

**Der Preis:** Was von außen nicht sichtbar ist, wird nicht bewertet. Ob Ihre Website regelmäßig gesichert wird, ob Ihre Zugangsdaten sicher verwahrt sind, ob der Vertrag mit Ihrer Agentur Ihnen die Herausgabe der Daten sichert — all das ist wichtig, und nichts davon steht in diesem Standard. Kapitel 16 sagt Ihnen, was hier fehlt und warum.

::: MRG
**Nicht bewertet**
Sicherungen · Zugangsverwaltung · Vertragslage · interne Abläufe
→ Kapitel 16
:::

Ein Standard, der behauptet, alles zu messen, misst am Ende nichts Bestimmtes. Dieser hier zieht die Grenze bewusst und sagt sie Ihnen.

---

## 3.2 Die acht Kategorien

Der Standard prüft **39 Kriterien in acht Kategorien**. Zusammen ergeben sie 103 Punkte.

<!-- ERZEUGT aus generiert/kategorien-uebersicht.md — nicht von Hand ändern.
     Änderungen gehen in audit_criteria.py, dann standard-export.py laufen lassen. -->

| # | Kategorie | Punkte | Kriterien | Was geprüft wird |
|---|---|---|---|---|
| 1 | Recht und Compliance | 20 | 5 | Pflichtangaben, Einwilligungen, Formulare |
| 2 | Sicherheit und Datenschutz | 10 | 4 | Verschlüsselung, Header, Drittanbieter |
| 3 | Ladezeit und Stabilität | 15 | 5 | Ladezeit, Layoutstabilität, Mobilmessung, Bilder |
| 4 | Barrierefreiheit | 10 | 5 | Kontrast, Alternativtexte, Semantik, Tastatur |
| 5 | Auffindbarkeit | 18 | 7 | Titel, Struktur, Indexierbarkeit, lokale Signale, Maschinenlesbarkeit |
| 6 | Gestaltung | 10 | 5 | Aktualität, Typografie, Farbe, Bilder, Mobildarstellung |
| 7 | Nutzerführung und Anfragen | 15 | 5 | Klarheit, Handlungsziel, Kontaktwege, Vertrauen, Angebot |
| 8 | Inhalt und Substanz | 5 | 3 | Leistungsseiten, Aktualität, Textqualität |
| | **Summe** | **103** | **39** | |

**Warum 103 und nicht 100.** Die Kategorien ergeben zusammen 103 Punkte. Ihr Ergebnis wird trotzdem als Wert zwischen 0 und 100 ausgewiesen. Der Grund steht in Abschnitt 3.6 und ist wichtiger, als er zunächst klingt: Je nach Branche gelten nicht alle Kriterien für Sie, und ein Maßstab, dessen Höchstwert von der Branche abhängt, wäre nicht vergleichbar. Deshalb wird gerechnet, nicht abgezählt.

::: MRG
**103 ≠ 100**
103 ist die Summe des Katalogs.
0–100 ist die Skala Ihres Ergebnisses.
→ Abschnitt 3.6
:::

Zwei Kategorien werden Sie in vergleichbaren Checklisten selten finden: **Gestaltung** und **Nutzerführung**. Genau das sind aber die beiden Dinge, die Sie selbst auf Ihrer Seite sehen und über die Sie mit einem Dienstleister diskutieren. Sie unbewertet zu lassen, weil sie unbequem zu messen sind, hieße, die Hälfte des Gesprächs auszulassen.

---

## 3.3 Warum diese Gewichtung

Jede Zahl in der Tabelle oben ist eine Entscheidung. Zwei Fragen liegen jeder zugrunde: **Wie zuverlässig lässt sich das von außen feststellen?** Und: **Wie stark wirkt es sich darauf aus, ob Sie Aufträge bekommen?** Was auf beide Fragen gut abschneidet, wiegt schwer. Was auf eine der beiden schlecht abschneidet, wiegt weniger.

**Recht und Compliance — 20 Punkte.** Vollständig messbar und mit unmittelbarem finanziellem Risiko verbunden. Das macht sie zur größten Einzelkategorie. Sie ist trotzdem nicht noch größer, und zwar aus einem systematischen Grund: Ein fehlendes Impressum ist kein Punktabzug, es ist ein Ausschluss. Wie das wirkt, steht in Abschnitt 3.8.

**Sicherheit und Datenschutz — 10 Punkte.** Technisch eindeutig messbar, aber für die Kundengewinnung nur mittelbar relevant. Ein Besucher bemerkt ein fehlendes Zertifikat sofort — den fehlenden Sicherheitsheader dahinter bemerkt er nie.

**Ladezeit und Stabilität — 15 Punkte.** Gut messbar über etablierte, öffentlich dokumentierte Messwerte, und direkt wirksam: Wer zu lange wartet, geht. Nicht mehr als 15 Punkte, weil die Messung von Netz, Gerät und Tageszeit abhängt und deshalb schwankt.

**Barrierefreiheit — 10 Punkte.** Hier gehört Ehrlichkeit hin: Von außen lässt sich Barrierefreiheit nur **teilweise** prüfen. Ob eine Seite mit einem Vorleseprogramm gut bedienbar ist, entscheidet sich in Details, die eine automatisierte Prüfung nicht sieht. Ein Standard, der dafür 20 Punkte vergibt, behauptet mehr Genauigkeit, als er hat. Die zehn Punkte umfassen genau das, was zuverlässig feststellbar ist.

**Auffindbarkeit — 18 Punkte.** Vollständig messbar und ein direkter Umsatzhebel. Die höchste Zahl nach Recht — und die einzige Kategorie, die zwischen der ersten und der zweiten Auflage dieses Standards gewachsen ist. Warum, steht in Kapitel 9.

**Gestaltung — 10 Punkte.** Der schwierigste Teil des Katalogs, weil hier zum ersten Mal etwas bewertet wird, das keine Maschine messen kann. Wie damit umgegangen wird, steht in Abschnitt 3.4.

**Nutzerführung und Anfragen — 15 Punkte.** Das eigentliche Verkaufsargument einer Website. Eine Seite, die rechtlich einwandfrei, schnell und barrierefrei ist, aber keine Anfrage auslöst, hat ihren Zweck verfehlt.

**Inhalt und Substanz — 5 Punkte.** Bewusst klein. Nicht weil Inhalt unwichtig wäre, sondern weil sich von außen nur wenige seiner Eigenschaften belastbar prüfen lassen.

::: ABB 3.2
format:   breit
titel:    Die acht Kategorien nach Gewicht
zweck:    Der Leser soll das Verhältnis der Kategorien zueinander
          sehen, nicht die Zahlen noch einmal lesen.
inhalt:   Waagerechte Balken, absteigend sortiert nach Punktzahl.
          Recht 20, Auffindbarkeit 18, Ladezeit 15, Nutzerführung 15,
          Sicherheit 10, Barrierefreiheit 10, Gestaltung 10, Inhalt 5.
          Rasterung der Balken nach Erhebungsart: durchgehend =
          überwiegend gemessen, schraffiert = enthält Einschätzungen.
          Punktzahl am Balkenende.
quelle:   generiert/kategorien-uebersicht.md — Werte NICHT frei wählen
bezug:    Abschnitt 3.3, nach dem letzten Absatz
bu:       Recht und Auffindbarkeit tragen mehr als ein Drittel des Standards.
sw-fest:  ja
:::

---

## 3.4 Woher die Punkte kommen: gemessen, abgeleitet, geschätzt

Nicht jeder Punkt in diesem Standard entsteht auf dieselbe Weise. Manche werden gemessen, manche errechnet, manche eingeschätzt. **Das ist kein Mangel — es ist die einzige ehrliche Möglichkeit, Gestaltung und Textqualität überhaupt zu bewerten.** Entscheidend ist, dass Sie bei jedem einzelnen Punkt erkennen können, welcher Art er ist.

Der Standard kennzeichnet deshalb jedes Kriterium:

| Kennzeichnung | Bedeutung | Anzahl |
|---|---|---|
| **gemessen** | Wird technisch erhoben. Zwei Prüfungen derselben Seite ergeben dasselbe Ergebnis | 28 |
| **abgeleitet** | Wird aus gemessenen Werten nach einer festen Regel berechnet | 4 |
| **Einschätzung** | Wird nach einem festen Bewertungsmaßstab beurteilt, nicht gemessen | 7 |

::: MRG
28 von 39 Kriterien werden **gemessen**.
Nur 7 sind Einschätzungen — und jede ist im Bericht als solche gekennzeichnet.
:::

**Die sieben Einschätzungen betreffen ausschließlich Gestaltung, Angebotsklarheit und Textqualität.** Also genau die Dinge, über die Menschen streiten. Sie werden nicht nach Geschmack beurteilt, sondern nach einem schriftlich festgelegten Maßstab, der für jede Branchenklasse verschieden ist — was für einen Elektrobetrieb eine klare Angebotsdarstellung ist, ist für eine Steuerkanzlei etwas anderes. Kapitel 4 erklärt das.

**Was Sie daraus mitnehmen sollten:** Wenn Ihnen jemand ein Ergebnis vorlegt, in dem nicht steht, welche Punkte gemessen und welche eingeschätzt wurden, dann können Sie mit diesem Ergebnis nicht argumentieren. Sie wissen nicht, wo Sie widersprechen können.

---

## 3.5 Nicht erhoben ist nicht null

Dieser Abschnitt ist kurz und er ist der wichtigste des Kapitels.

Manchmal lässt sich ein Kriterium nicht prüfen. Der Messdienst antwortet nicht, eine Seite ist vorübergehend nicht erreichbar, ein Messwert liegt für kleine Websites schlicht nicht vor, weil zu wenige Besucher gezählt wurden. Was passiert dann?

**Die falsche Antwort: null Punkte.** Sie ist bequem, sie ist die häufigste, und sie ist ein Fehler. Sie bestraft Sie für etwas, das Sie nicht getan haben. Eine kleine Website, für die kein Feld-Messwert vorliegt, ist nicht schlechter als eine große — sie ist kleiner.

**Die richtige Antwort: das Kriterium fällt aus der Rechnung.** Aus dem Zähler *und* aus dem Nenner. Es zählt weder für Sie noch gegen Sie.

::: MRG
**Merksatz**
Ein Kriterium, das nicht geprüft werden konnte, verschwindet aus der Rechnung — nicht in die Null.
:::

Daraus folgt etwas, das Sie kennen sollten: **Ihr anwendbares Maximum ist nicht immer 103.** Es sinkt, wenn Kriterien für Ihre Branchenklasse nicht gelten (Kapitel 4), und es sinkt, wenn eine Prüfung nicht durchgeführt werden konnte. Beide Fälle sehen im Bericht unterschiedlich aus, weil sie unterschiedliche Dinge bedeuten:

| Kennzeichnung | Bedeutung |
|---|---|
| **nicht erhoben** | Wir konnten es nicht prüfen. Ein Mangel unserer Prüfung, nicht Ihrer Seite |
| **gilt hier nicht** | Das Kriterium passt nicht zu Ihrer Branche. Kein Mangel, sondern eine Einordnung |

Der Unterschied klingt spitzfindig. Er ist es nicht: Beim ersten sollten Sie die Prüfung wiederholen. Beim zweiten gibt es nichts zu tun.

---

## 3.6 Von den Rohpunkten zu Ihrem Wert

Jetzt die Rechnung. Sie besteht aus einem Bruch und einer Multiplikation.

> **Erreichte Punkte ÷ anwendbare Punkte × 100 = Ihr Wert**
> Kaufmännisch gerundet.

Das ist alles. Und es hat drei Konsequenzen, die Sie kennen sollten.

**Erstens: Ihr Wert liegt immer zwischen 0 und 100**, obwohl der Katalog 103 Punkte umfasst. Die 103 sind die Rohsumme, Ihr Wert ist der Anteil, den Sie davon erreicht haben. Auf dem Titel dieses Buchs steht die Rohsumme, weil sie beschreibt, wie umfangreich der Katalog ist. In jedem Ergebnis steht Ihr Wert, weil er vergleichbar ist.

**Zweitens: Nicht erhobene Kriterien verbessern Ihren Wert nicht automatisch.** Sie verkleinern Zähler und Nenner gleichermaßen. Wer bei einer Prüfung zwei nicht erhobene Kriterien hat, bekommt keine Punkte geschenkt — der Maßstab wird nur um diese beiden kleiner.

**Drittens: Die Rundung entscheidet in Grenzfällen über die Stufe.** Es wird kaufmännisch gerundet, also ab 0,5 aufwärts. Ein Ergebnis von 84,5 wird zu 85 und damit von Silber zu Gold. Das ist selten und es ist bewusst so festgelegt, damit es nachvollziehbar bleibt.

::: MRG
**Rundung**
Kaufmännisch: ab ,5 aufwärts.
84,5 → 85 → Gold.
:::

::: ABB 3.3
format:   breit
titel:    Die Rechnung an drei Beispielen
zweck:    Der Leser soll sehen, dass derselbe Rohwert je nach
          anwendbarem Maximum zu verschiedenen Ergebnissen führt.
inhalt:   Drei waagerechte Zeilen, jeweils: Rohpunkte (Balken) über
          anwendbarem Maximum (heller Balken dahinter), rechts das
          Ergebnis und die Stufe.
          Zeile 1: 76 von 103 → 74 → Silber
          Zeile 2: 76 von 100 → 76 → Silber
          Zeile 3: 76 von  81 → 94 → Gold
          Dritte Zeile deutlich abgesetzt, sie trägt die Pointe.
quelle:   Rechnung round(erreicht ÷ anwendbar × 100)
bezug:    Abschnitt 3.6, nach dem dritten Absatz
bu:       Dieselben 76 Punkte — drei verschiedene Ergebnisse.
sw-fest:  ja
:::

---

## 3.7 Die fünf Stufen

Aus Ihrem Wert ergibt sich eine von fünf Stufen.

<!-- ERZEUGT aus generiert/stufen.md — nicht von Hand ändern. -->

| Stufe | Wert | Was sie bedeutet |
|---|---|---|
| **Homepage Standard Platin** | 95–100 | Vollständige Erfüllung einschließlich der Kriterien, die über die Pflicht hinausgehen. Selten |
| **Homepage Standard Gold** | 85–94 | Alle Pflichtanforderungen erfüllt, dazu erkennbare Qualitätsmerkmale. Das empfohlene Zielniveau |
| **Homepage Standard Silber** | 70–84 | Solide Grundlage. Rechtlich weitgehend in Ordnung, technisch und inhaltlich mit Lücken |
| **Homepage Standard Bronze** | 50–69 | Mindestanforderungen teilweise erfüllt, erhebliche Lücken |
| **Nicht konform** | 0–49 | Kritische Mängel. Handlungsbedarf, nicht Optimierungsbedarf |

**Gold ist das Ziel, nicht Platin.** Das ist keine Bescheidenheit, sondern Wirtschaftlichkeit. Die letzten Punkte zwischen 85 und 100 kosten überproportional viel Aufwand und bringen für die Kundengewinnung fast nichts mehr. Wer von Bronze auf Silber kommt, verändert seine Außenwirkung spürbar. Wer von Gold auf Platin geht, verändert vor allem seine Rechnung.

::: ABB 3.4
format:   marginal
titel:    Die fünf Stufenmarken
zweck:    Wiederkehrende Marke, die im ganzen Buch verwendet wird.
inhalt:   Fünf Marken untereinander, jeweils vier Segmente in einer
          Reihe: leer / ein Viertel / halb / drei Viertel / voll.
          Ausschließlich über Füllung unterschieden, nicht über Farbe.
          Darunter jeweils der Stufenname, klein.
warnung:  KEINE Metallfarben. Gold, Silber und Bronze in CMYK
          gedruckt sehen billig aus. Die Unterscheidung trägt
          allein die Füllung.
bezug:    Abschnitt 3.7, in der Marginalspalte neben der Tabelle
sw-fest:  ja
:::

---

## 3.8 Die Ausschlusskriterien

Fünf Befunde wirken **unabhängig von Ihrer Punktzahl**. Sie ziehen keine Punkte ab — sie begrenzen die Stufe, die Sie erreichen können.

| Befund | Höchste erreichbare Stufe |
|---|---|
| Kein erreichbares Impressum (§ 5 DDG) | Nicht konform |
| Keine erreichbare Datenschutzerklärung (Art. 13 DSGVO) | Nicht konform |
| Kein gültiges Verschlüsselungszertifikat | Nicht konform |
| Tracking oder externe Dienste ohne Einwilligung | Bronze |
| Cookies werden vor der Einwilligung gesetzt | Bronze |

::: MRG
**§ 5 DDG**
Die Impressumspflicht steht seit Mai 2024 im Digitale-Dienste-Gesetz. Ältere Quellen nennen § 5 TMG — das Gesetz gibt es nicht mehr.
:::

**Warum es diese Regel gibt.** Ohne sie könnte eine Website ohne Impressum rechnerisch 78 Punkte und damit Silber erreichen. Ein Maßstab, der einen Rechtsverstoß mit einer soliden Bewertung quittiert, ist als Maßstab nicht haltbar — und als Argument gegenüber einem Dienstleister erst recht nicht.

**Wie es im Ergebnis aussieht.** Der Bericht nennt immer beides: die rechnerische Punktzahl **und** die tatsächliche Stufe, mit Grund.

> Nicht konform (rechnerisch 78 Punkte). Begrenzt, weil keine Datenschutzerklärung erreichbar ist.

Diese Doppelangabe ist keine Formalität. **Der Abstand zwischen beiden Zahlen ist Ihre wichtigste Kennziffer**, denn er zeigt, wie viel eine einzige Korrektur bewirkt. Ein Betrieb mit 78 rechnerischen Punkten und fehlender Datenschutzerklärung ist keine schlechte Website. Er ist eine gute Website mit einem Formfehler, und der ist an einem Vormittag behoben.

---

## 3.9 Zwei Befunde außerhalb der Wertung

Eine vollständige Prüfung liefert zwei weitere Ergebnisse, die bewusst nicht in die Punktzahl einfließen.

**Der Infrastruktur-Befund** stellt fest, womit Ihre Website gebaut ist und wo sie liegt: verwendetes System, Anbieter, Auslieferungsnetzwerk, Übertragungsprotokoll, Alter der Domain, Erreichbarkeit und eingesetzte Besuchermessung. Vier Angaben, null Punkte. Sie fließen nicht in die Bewertung ein, weil Sie sie meist nicht ohne Anbieterwechsel beeinflussen können. Sie sind trotzdem wertvoll: Wer wissen will, was eine Überarbeitung kostet, muss wissen, worauf er aufsetzt.

**Der GEO-Befund** beschreibt, wie gut Ihre Website für KI-gestützte Suchsysteme aufbereitet ist — für Systeme also, die keine Linkliste ausgeben, sondern eine Antwort formulieren. Er ist **keine Zahl, sondern eine Liste von Prüfpunkten** mit den Status *erfüllt*, *offen* oder *unbekannt*. Er steht außerhalb der Wertung, weil sich dieses Feld derzeit zu schnell verändert. Ein Kriterium, dessen Anforderungen sich innerhalb eines Jahres wandeln können, gehört nicht in einen Standard, der über Jahre vergleichbar bleiben soll — und erst recht nicht in ein gedrucktes Buch.

**Warum es hier ausdrücklich keine Punktzahl gibt.** Eine Zahl lädt zum Vergleichen ein, und für dieses Feld gibt es keinen stabilen Maßstab, an dem sich vergleichen ließe. Zwei der fünf Prüfpunkte — ob KI-Systeme Ihren Betrieb erwähnen und ob er in zusammengefassten Suchantworten erscheint — werden derzeit **gar nicht erhoben**. Sie stehen im Bericht als *unbekannt*, ohne Empfehlung. Das ist ehrlicher als ein Wert, der so tut, als wäre er gemessen.

**Eine Ausnahme, und warum sie eine ist.** Ein Aspekt der maschinellen Erfassbarkeit steht sehr wohl in der Wertung: Kriterium E7 in Kapitel 9 prüft, ob Ihre Website für Maschinen überhaupt **lesbar** ist — ob Sie KI-Systeme in der Steuerungsdatei aussperren und ob eine Beschreibungsdatei für sie vorliegt. Das ist etwas anderes als der GEO-Befund. Ob eine Maschine Ihre Seite lesen darf, ist eine Ja-oder-Nein-Frage, die sich in zehn Jahren genauso stellt wie heute. Ob ein bestimmtes System Sie auf eine bestimmte Frage hin nennt, ändert sich mit jeder neuen Modellversion. Das Erste ist ein Standard, das Zweite eine Momentaufnahme.

::: MRG
**Lesbar ≠ sichtbar**
Lesbarkeit für Maschinen wird bewertet (E7, Kapitel 9).
Sichtbarkeit in Antworten nicht (GEO-Befund, Kapitel 16).
:::

---

## 3.10 Ein Fall, durchgerechnet

Der Betrieb heißt Elektro Hansen, hat vierzehn Mitarbeiter und arbeitet im Umkreis von rund vierzig Kilometern. Branchenklasse K1 — lokaler Leistungsbetrieb. Für K1 gelten alle Kriterien, das anwendbare Maximum liegt also bei 103. Alle 39 Kriterien konnten geprüft werden.

| Kategorie | Erreicht | Möglich |
|---|---|---|
| Recht und Compliance | 18 | 20 |
| Sicherheit und Datenschutz | 9 | 10 |
| Ladezeit und Stabilität | 7 | 15 |
| Barrierefreiheit | 6 | 10 |
| Auffindbarkeit | 11 | 18 |
| Gestaltung | 8 | 10 |
| Nutzerführung und Anfragen | 13 | 15 |
| Inhalt und Substanz | 4 | 5 |
| **Summe** | **76** | **103** |

`76 ÷ 103 × 100 = 73,8` → gerundet **74 Punkte** → **Homepage Standard Silber**

Kein Ausschlusskriterium liegt vor. Die Website ist rechtlich in Ordnung, sie wird gefunden, sie löst Anfragen aus. Sie ist nicht schlecht. Sie ist elf Punkte von Gold entfernt.

### Wo diese elf Punkte liegen

Jetzt kommt der Teil, der die meisten Leser überrascht. Wir sehen uns an, welche einzelnen Kriterien fehlen:

| Fehlt | Punkte | Aufwand |
|---|---|---|
| Bildformate und Ladeverhalten der Bilder | 3 | Eine Einstellung im System, einmalig |
| Alternativtexte für Inhaltsbilder | 2 | Eine Stunde Eintragen |
| Strukturierte Daten für den Betrieb | 3 | Ein Textblock im Seitenkopf |
| Beschreibungsdatei für KI-Systeme | 3 | Eine Datei, wenige Zeilen |
| Ein defekter Verweis | 1 | Zehn Minuten |
| | **12** | |

**Zwölf Punkte. Keiner davon betrifft den Inhalt der Website.** Kein Text muss umgeschrieben, kein Bild neu gemacht, keine Seite neu gebaut werden. Es sind fünf technische Kleinigkeiten, von denen vier Dateien sind.

Nach diesen fünf Korrekturen:

| Kategorie | Vorher | Nachher | Möglich |
|---|---|---|---|
| Ladezeit und Stabilität | 7 | **10** | 15 |
| Barrierefreiheit | 6 | **8** | 10 |
| Auffindbarkeit | 11 | **18** | 18 |
| *übrige, unverändert* | 52 | 52 | 60 |
| **Summe** | **76** | **88** | **103** |

`88 ÷ 103 × 100 = 85,4` → gerundet **85 Punkte** → **Homepage Standard Gold**

::: ABB 3.5
format:   breit
titel:    Von Silber zu Gold in fünf Handgriffen
zweck:    Der Leser soll sehen, dass der Sprung nicht am Inhalt
          hängt, sondern an Technik — und dass die Stufengrenze
          knapp überschritten wird, nicht souverän.
inhalt:   Ein waagerechter Balken 0 bis 100 mit den vier
          Stufengrenzen 50, 70, 85, 95 als senkrechte Marken.
          Zwei Punkte darauf: 74 (vorher) und 85 (nachher),
          mit einem Pfeil verbunden. Über dem Pfeil die fünf
          Korrekturen als kurze Wortliste mit ihren Punktwerten.
          Die Marke 85 muss erkennbar knapp getroffen sein.
quelle:   Rechnung aus 3.10 — Werte NICHT frei wählen
bezug:    Abschnitt 3.10, nach der zweiten Tabelle
bu:       Elf Punkte trennten diesen Betrieb von Gold. Zwölf lagen in fünf Dateien.
sw-fest:  ja
:::

**Was dieser Fall zeigt — und was nicht.** Er zeigt, dass die günstigsten Punkte fast immer in der Technik liegen und nicht im Inhalt. Er zeigt nicht, dass jeder Betrieb so nah an Gold steht. Elektro Hansen hatte ein sauberes Impressum, eine erreichbare Datenschutzerklärung und ein gültiges Zertifikat. Betriebe, bei denen eines davon fehlt, stehen unabhängig von ihrer Punktzahl bei „Nicht konform" — und für sie ist der erste Schritt ein anderer.

> **Hinweis zur Nachvollziehbarkeit.** Alle Zahlen in diesem Abschnitt sind ausgerechnet, nicht geschätzt. Sie können sie mit dem Taschenrechner prüfen. Wenn Sie ein anderes Ergebnis bekommen als hier steht, schreiben Sie uns — das wäre ein Fehler in diesem Buch, und er gehört korrigiert.

---

## 3.11 Vier verbreitete Missverständnisse

**„100 Punkte erreicht ohnehin niemand."**
Richtig ist: Platin ab 95 Punkten ist selten, und es ist auch nicht das Ziel. Für einen Betrieb, der Kunden gewinnen und rechtlich sicher sein will, ist Gold das wirtschaftlich sinnvolle Niveau. Die Punkte darüber kosten mehr, als sie einbringen.

**„Meine Website ist neu, also ist sie in Ordnung."**
Neu heißt: zeitgemäß gestaltet. Über Recht, Ladezeit und Einwilligungen sagt es nichts. Im Gegenteil — moderne Baukastensysteme binden häufig Schriftarten, Karten und Statistikwerkzeuge von fremden Servern ein, und zwar ohne zu fragen. Ein zehn Jahre alter, handgebauter Auftritt ohne jedes Fremdelement ist an dieser Stelle im Vorteil.

**„Das ist doch alles Geschmackssache."**
Bei 32 von 39 Kriterien nicht. Sie werden gemessen oder aus Messungen berechnet, und zwei Prüfungen derselben Seite ergeben dasselbe Ergebnis. Die sieben Kriterien, bei denen eingeschätzt wird, sind im Bericht als solche gekennzeichnet — und Sie können ihnen widersprechen, weil der angelegte Maßstab dabeisteht.

**„Wenn ich alle Punkte hole, bekomme ich mehr Aufträge."**
Nein. Der Standard misst den Zustand Ihrer Website, nicht Ihren Vertrieb. Eine Website mit 95 Punkten, die niemand kennt, bringt weniger als eine mit 70 Punkten, auf die eine gute Empfehlung verweist. Was der Standard Ihnen gibt, ist etwas anderes: die Gewissheit, dass Ihre Website nicht der Grund ist, warum eine Anfrage ausbleibt.

---

## Das Wichtigste aus diesem Kapitel

> - **39 Kriterien in acht Kategorien**, zusammen 103 Rohpunkte. Ihr Ergebnis wird auf einen Wert zwischen 0 und 100 umgerechnet.
> - **28 Kriterien werden gemessen**, 4 berechnet, 7 eingeschätzt. Jedes ist im Bericht gekennzeichnet.
> - **Nicht erhobene Kriterien fallen aus der Rechnung**, nicht auf null. Ihr anwendbares Maximum kann kleiner als 103 sein.
> - **Fünf Stufen**, Gold ab 85 ist das empfohlene Ziel — nicht Platin.
> - **Fünf Ausschlusskriterien** begrenzen die Stufe unabhängig von der Punktzahl. Drei davon führen zu „Nicht konform".
> - **Die günstigsten Punkte liegen fast immer in der Technik**, nicht im Inhalt.

---

<!-- REDAKTIONELLE ANMERKUNGEN — NICHT DRUCKEN -->

## Offene Punkte zu Kapitel 3

| # | Punkt | Wer | Status |
|---|---|---|---|
| 1 | Alle Tabellen mit `ERZEUGT`-Kommentar müssen aus `standard-export.py` kommen. Solange das Skript nicht existiert, sind die Werte hier von Hand aus `audit_criteria.py` übertragen und **beim nächsten Katalogstand ungeprüft** | Technik | offen |
| 2 | § 5 DDG statt § 5 TMG — im ganzen Buch durchziehen. Das TMG ist seit Mai 2024 abgelöst; beide Spezifikationsdokumente und das alte Manuskript nennen noch TMG | Recht | **prüfen** |
| 3 | Der Fall Elektro Hansen ist konstruiert, wenn auch realistisch gerechnet. Vor Drucklegung durch einen anonymisierten realen Fall ersetzen — sonst muss der Haftungsausschluss die Konstruktion ausweisen | Autor | offen |
| 4 | Abschnitt 3.7: Die Aussage „Gold ab 85 ist das empfohlene Ziel" ist eine Empfehlung, keine Messung. Beim Lektorat prüfen, ob sie als solche erkennbar bleibt | Lektorat | offen |
| 5 | Abschnitt 3.11, dritter Punkt: „32 von 39" = 28 gemessen + 4 abgeleitet. Wenn sich die Erhebungsart eines Kriteriums ändert, ändert sich diese Zahl mit | Technik | Drift-Kandidat |
| 6 | Der Satz in 3.10 („schreiben Sie uns") braucht eine Adresse. Erst festlegen, wenn der QR-/Kontaktweg entschieden ist — nach dem Druck nicht änderbar | GF | **blockiert** |
| 7 | Abbildung 3.4 (Stufenmarken) wird im ganzen Buch wiederverwendet. Sie muss vor allen anderen Abbildungen fertig sein, sonst zeichnet Manuel achtmal Varianten | Gestaltung | **zuerst** |
| 8 | Kapitel 4 muss die sechs anwendbaren Maxima nennen (K1/K2/K3/K5 = 103, K4 = 100, K6 = 81). Abschnitt 3.5 verweist darauf | Autor | Folgekapitel |

**Abbildungen in diesem Kapitel:** 5 (ABB 3.1 ganz, 3.2 breit, 3.3 breit, 3.4 marginal, 3.5 breit)
**Marginalien:** 6
**Geschätzter Satzumfang:** 15–16 Seiten
