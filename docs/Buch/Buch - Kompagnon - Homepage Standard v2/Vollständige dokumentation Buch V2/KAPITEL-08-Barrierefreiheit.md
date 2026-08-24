---
kapitel: 8
teil: "II — Die acht Kategorien"
titel: "Barrierefreiheit"
autor: "Manuel Potter"
status: entwurf
zuletzt_geprueft: 2026-08-24
standard_version: "2026.2"
zielumfang: 14 Seiten
punkte: 10
kriterien: "B1–B5"
---

<!-- KAPITELÖFFNER — rechte Seite -->

# 8

# Barrierefreiheit

# 10 Punkte

> Die ehrlichste Kategorie des Standards — weil sie als einzige damit anfängt, aufzuzählen, was sie nicht kann.

<!-- SEITENUMBRUCH -->

> ### Rechtshinweis
>
> Dieses Kapitel beschreibt, was der Standard technisch prüft. Es ist keine Aussage darüber, ob Ihre Website die Anforderungen des Barrierefreiheitsstärkungsgesetzes erfüllt, und keine Rechtsberatung. Ob und in welchem Umfang Ihr Betrieb verpflichtet ist, klären Sie mit Ihrer Rechtsberatung — siehe auch Abschnitt 5.7.

---

## 8.1 Was hier bewertet wird

Fünf Kriterien, zusammen 10 Punkte.

<!-- ERZEUGT aus generiert/kriterien-barrierefreiheit.md — nicht von Hand ändern. -->

| Code | Kriterium | Punkte | Erhebung | Gilt für |
|---|---|---|---|---|
| B1 | Gesamtwert der Barrierefreiheitsprüfung | 3 | gemessen | alle Klassen |
| B2 | Farbkontraste | 2 | gemessen | alle Klassen |
| B3 | Alternativtexte für Bilder | 2 | gemessen | alle Klassen |
| B4 | Semantik und Struktur | 2 | abgeleitet | alle Klassen |
| B5 | Tastaturbedienung | 1 | abgeleitet | alle Klassen |

::: MRG
**B1–B5**
5 Kriterien · 10 Punkte
Keine Klassenunterschiede
:::

**Drei dieser fünf Kriterien — B1, B2 und B5, zusammen 6 Punkte — stammen aus derselben externen Messung wie die Kategorie Ladezeit.** Fällt sie aus, fallen sie mit aus. Zusammen mit den zwölf Punkten aus Kapitel 7 sind das bis zu 18 von 103 Punkten, die dann nicht erhoben werden können. Ihr anwendbares Maximum sinkt in diesem Fall auf 85.

B3 und B4 werden eigenständig erhoben und bleiben verfügbar.

---

## 8.2 Warum nur zehn Punkte

Hier gehört Ehrlichkeit hin, und zwar an den Anfang.

**Barrierefreiheit lässt sich von außen nur teilweise prüfen.** Eine automatisierte Messung stellt fest, ob Bilder eine Textalternative haben. Sie stellt nicht fest, ob diese Alternative etwas Sinnvolles beschreibt. Sie stellt fest, ob Farbkontraste ausreichen. Sie stellt nicht fest, ob eine Seite mit einem Vorleseprogramm verständlich vorgelesen wird, ob die Reihenfolge stimmt, ob ein blinder Nutzer das Kontaktformular tatsächlich ausfüllen kann.

Diese letzten Fragen entscheiden über Barrierefreiheit. Und keine davon lässt sich messen — sie lassen sich nur ausprobieren, von Menschen, die auf Hilfsmittel angewiesen sind.

**Ein Standard, der dafür 20 Punkte vergibt, behauptet mehr Genauigkeit, als er hat.** Zehn Punkte umfassen genau das, was zuverlässig von außen feststellbar ist. Nicht mehr.

::: MRG
**Der wichtigste Satz dieses Kapitels**
Zehn von zehn Punkten heißen: keine der prüfbaren Hürden ist vorhanden. Sie heißen nicht: die Seite ist barrierefrei.
:::

### Was diese Kategorie nicht prüft

| Nicht geprüft | Warum nicht |
|---|---|
| Ob Alternativtexte inhaltlich passen | „Bild1.jpg" ist ein Alternativtext. Ein sinnvoller ist er nicht |
| Ob Vorleseprogramme die Seite verständlich wiedergeben | Erfordert echte Benutzung, nicht Messung |
| Ob Formulare mit Hilfsmitteln ausfüllbar sind | dito |
| Ob Videos Untertitel haben, die stimmen | dito |
| Ob die Sprache verständlich ist | Leichte Sprache ist eine inhaltliche Frage |

**Wenn Barrierefreiheit für Sie rechtlich verpflichtend ist**, ersetzt dieser Standard keine fachliche Prüfung. Er zeigt Ihnen, wo die maschinell auffindbaren Hürden liegen — das ist ein sinnvoller erster Schritt und kein letzter.

---

## 8.3 Der Fall

Elektro Hansen, Branchenklasse K1.

| Kriterium | Befund | Punkte |
|---|---|---|
| B1 Gesamtwert | 81 von 100 | 2 / 3 |
| B2 Farbkontraste | keine Beanstandung | 2 / 2 |
| B3 Alternativtexte | **nur 61 % der Bilder haben einen** | 0 / 2 |
| B4 Semantik und Struktur | eine Hauptüberschrift, saubere Gliederung | 2 / 2 |
| B5 Tastaturbedienung | **Fokus nicht durchgehend sichtbar** | 0 / 1 |
| | | **6 / 10** |

Vier Punkte fehlen, und die Verteilung ist typisch: Die technischen Grundlagen stimmen, die redaktionelle Sorgfalt fehlt.

**B3 ist der Befund, der zählt.** 61 Prozent klingt nach „mehr als die Hälfte" und ist trotzdem null Punkte — die Schwelle für einen Punkt liegt bei 80 Prozent. Abschnitt 8.6 erklärt, warum sie so hoch liegt.

In Kapitel 3 waren das zwei der zwölf zurückzuholenden Punkte. Der Aufwand: eine Stunde Eintragen.

---

## 8.4 B1 — Gesamtwert der Barrierefreiheitsprüfung · 3 Punkte

::: MRG
**B1 · 3 Punkte**
gemessen
externe Messung
:::

### Worum es geht

Ein zusammenfassender Wert von 0 bis 100, den der Messdienst aus einer Reihe automatisierter Einzelprüfungen bildet. Er ist das Gegenstück zum mobilen Gesamtwert aus Abschnitt 7.8: eine Zahl, die viele Einzelbefunde bündelt.

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-bf_lighthouse.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 3 | Wert 90 oder höher |
| 2 | Wert 75 bis 89 |
| 1 | Wert 50 bis 74 |
| 0 | Wert unter 50 |

### Was Sie über diesen Wert wissen sollten

**Er überschneidet sich mit B2, B3 und B5.** Kontraste, Alternativtexte und Tastaturbedienung fließen in den Gesamtwert ein und werden zusätzlich einzeln bewertet.

Das ist beabsichtigt und dieselbe Logik wie bei P4: Wer die Einzelkriterien erfüllt, findet das im Gesamtwert wieder. **Für Sie heißt das: Jede Korrektur an B2, B3 oder B5 verbessert B1 mit.** Die vier Punkte aus dem Fall in 8.3 können in der Praxis fünf werden.

**Und ein zweiter Hinweis:** Ein hoher Gesamtwert bei gleichzeitig schlechten Einzelkriterien kommt vor. Dann prüfte die Messung Dinge, die auf Ihrer Seite gar nicht vorkommen — eine Seite ohne Videos verliert keine Punkte für fehlende Untertitel. Ein hoher Wert kann also auch bedeuten: Es gab wenig zu prüfen.

---

## 8.5 B2 — Farbkontraste · 2 Punkte

::: MRG
**B2 · 2 Punkte**
gemessen
externe Messung
WCAG AA
:::

### Worum es geht

Ob Text sich ausreichend vom Hintergrund abhebt. Der Maßstab ist das Kontrastverhältnis nach der internationalen Richtlinie für barrierefreie Webinhalte, Stufe AA.

**Das betrifft weit mehr Menschen, als die meisten annehmen.** Nicht nur Sehbehinderte — auch jeden, der Ihre Seite bei Sonnenlicht auf einem Telefon ansieht, und praktisch jeden über sechzig.

### Punktvergabe

Der Anteil der bestandenen Kontrastprüfungen wird auf zwei Punkte umgelegt:

<!-- ERZEUGT aus generiert/abstufung-bf_kontrast.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 2 | keine Kontrastbeanstandung |
| 0 | mindestens eine Kontrastbeanstandung |

**Es gibt keinen Zwischenwert.** Die Prüfung ist bestanden oder nicht — ein einziges beanstandetes Textelement genügt, um beide Punkte zu verlieren. Das ist streng, und es ist der Grund, warum sich der Blick auf die drei Fundstellen unten lohnt: Sie sind fast immer die Ursache.

### So beheben Sie es

**Die häufigsten drei Fundstellen sind fast immer dieselben:**

1. **Hellgrauer Fließtext auf Weiß.** Der Klassiker. Er sieht in der Gestaltungsvorlage elegant aus und ist auf einem Telefon im Freien nicht lesbar.
2. **Text auf einem Foto.** Ohne abdunkelnde Fläche darunter wechselt der Kontrast mit jedem Bildbereich.
3. **Beschriftungen auf farbigen Schaltflächen.** Besonders bei hellen Firmenfarben — Gelb, Hellgrün, Türkis — ist weiße Schrift darauf fast immer zu kontrastarm.

**Der dritte Punkt ist unangenehm**, weil er mit Ihrer Hausfarbe kollidieren kann. Die Lösung ist nicht, die Farbe zu ändern, sondern die Schriftfarbe darauf: Dunkler Text auf hellem Firmenfarbton besteht die Prüfung, weißer nicht.

---

## 8.6 B3 — Alternativtexte für Bilder · 2 Punkte

::: MRG
**B3 · 2 Punkte**
gemessen
eigene Erhebung
:::

### Worum es geht

Jedes inhaltlich bedeutsame Bild braucht eine Textalternative. Sie wird vorgelesen, wenn jemand die Seite nicht sehen kann — und sie wird angezeigt, wenn das Bild nicht lädt.

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-bf_alt.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 2 | mindestens 95 % der Bilder haben eine Textalternative |
| 1 | mindestens 80 % |
| 0 | weniger als 80 % |

### Warum die Schwellen so hoch liegen

Das ist die strengste Staffelung des ganzen Standards, und dafür gibt es einen Grund: **Alternativtexte sind eine Alles-oder-nichts-Angelegenheit.**

Wer neun von zehn Bildern beschriftet hat, hat für einen blinden Nutzer nicht neunzig Prozent der Seite erschlossen. Er hat eine Stelle hinterlassen, an der die Vorlesung abbricht — und das kann genau die Stelle sein, an der die Telefonnummer als Grafik eingebunden ist.

Eine Schwelle bei 50 Prozent würde suggerieren, halbe Sorgfalt sei halb so gut. Sie ist es nicht.

::: MRG
**Merksatz**
Bei Alternativtexten gibt es kein „überwiegend". Es gibt vollständig oder lückenhaft.
:::

### Was der Standard nicht prüft — und was Sie trotzdem tun sollten

Geprüft wird, **ob** eine Textalternative vorhanden ist. Nicht, ob sie taugt. Die Zeichenfolge `IMG_4471` ist eine gültige Textalternative und bringt volle Punkte.

**Das ist eine Lücke, und ich nenne sie ausdrücklich**, damit Sie sie nicht ausnutzen. Wer alle Bilder mit dem Dateinamen beschriftet, bekommt zwei Punkte und hat nichts verbessert.

Was ein brauchbarer Alternativtext leistet:

| Bild | Untauglich | Brauchbar |
|---|---|---|
| Monteur an einem Schaltschrank | `IMG_4471` | Monteur prüft eine Unterverteilung |
| Firmenlogo | `logo` | Elektro Hansen GmbH |
| Rein dekorative Trennlinie | `linie` | *(leer lassen — sie soll übersprungen werden)* |

**Die dritte Zeile ist die, die am häufigsten falsch gemacht wird.** Rein dekorative Bilder bekommen eine **leere** Textalternative, damit Vorleseprogramme sie überspringen. Ein Dekorationsbild mit dem Alternativtext „Trennlinie" unterbricht die Vorlesung für nichts.

### So beheben Sie es

Bei den meisten Systemen ist das Feld beim Bild-Upload direkt vorhanden und wird schlicht übersprungen. Gehen Sie die Bibliothek einmal durch und tragen Sie nach. **Bei einer typischen Betriebswebsite mit fünfzig Bildern ist das eine Stunde** — für zwei Punkte hier und einen wahrscheinlichen dritten bei B1.

---

## 8.7 B4 — Semantik und Struktur · 2 Punkte

::: MRG
**B4 · 2 Punkte**
eigene Erhebung
→ Abgrenzung zu E2, Kapitel 9
:::

### Worum es geht

Eine Seite hat eine Gliederung — Hauptüberschrift, Abschnitte, Unterabschnitte. Für einen sehenden Leser ist sie an Schriftgröße und Abstand erkennbar. Ein Vorleseprogramm sieht keine Schriftgrößen. Es liest die Gliederung aus der technischen Auszeichnung.

**Wenn eine Überschrift nur groß und fett formatiert ist, aber technisch keine Überschrift ist, existiert die Gliederung für Hilfsmittel nicht.** Die Seite wird dann als ein einziger Textblock vorgelesen, von oben bis unten, ohne Möglichkeit zu springen.

### Was geprüft wird

Zwei Dinge:

| Prüfung | Bestanden, wenn |
|---|---|
| **Genau eine Hauptüberschrift** | Die Seite hat eine H1 — nicht keine, nicht drei |
| **Saubere Hierarchie** | Die Ebenen folgen aufeinander, ohne zu springen |

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-bf_semantik.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 2 | beide Prüfungen bestanden |
| 1 | eine bestanden |
| 0 | keine bestanden |

### Die Abgrenzung zu E2

Kapitel 9 bewertet unter E2 ebenfalls die Überschriftenstruktur — dort unter dem Gesichtspunkt der Auffindbarkeit. **Es ist derselbe Sachverhalt, betrachtet aus zwei Richtungen:**

| | B4 (hier) | E2 (Kapitel 9) |
|---|---|---|
| **Frage** | Können Hilfsmittel die Gliederung erfassen? | Erkennen Suchmaschinen, worum es geht? |
| **Zusätzlich** | genau eine Hauptüberschrift | Textmenge und inhaltliche Tiefe |

::: MRG
🔴 **Zu prüfen**
Doppelwertung B4 / E2. Siehe redaktionelle Anmerkungen.
:::

Wer die Überschriftenstruktur in Ordnung bringt, verbessert beide. Das ist kein Fehler — es ist die Belohnung dafür, dass eine einzige Korrektur zwei Zwecke erfüllt.

### So beheben Sie es

1. **Prüfen Sie, ob jede Seite genau eine Hauptüberschrift hat.** Häufiger Fehler bei Baukastensystemen: Das Firmenlogo im Kopfbereich ist als Hauptüberschrift ausgezeichnet, und die eigentliche Seitenüberschrift ist dann die zweite.
2. **Prüfen Sie, ob Ebenen übersprungen werden.** Auf eine Hauptüberschrift folgt eine Ebene 2, nicht direkt eine Ebene 3. Der häufigste Grund für Sprünge: Jemand hat die Ebene nach der Schriftgröße ausgewählt, die sie erzeugt.
3. **Formatieren Sie keine Überschriften von Hand.** Groß und fett ist keine Überschrift. Es sieht nur so aus.

---

## 8.8 B5 — Tastaturbedienung · 1 Punkt

::: MRG
**B5 · 1 Punkt**
abgeleitet
externe Messung
:::

### Worum es geht

Nicht jeder bedient eine Website mit der Maus. Manche können es nicht, manche wollen es nicht. Eine Seite muss sich vollständig mit der Tabulatortaste durchlaufen lassen — und man muss dabei jederzeit sehen, wo man gerade ist.

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-bf_tastatur.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 1 | keine Beanstandung |
| 0 | Beanstandung |

Nur ein Punkt — nicht weil es unwichtig wäre, sondern weil sich von außen so wenig davon zuverlässig feststellen lässt. Ob eine Seite mit der Tastatur **benutzbar** ist, entscheidet sich beim Benutzen.

### Der Selbsttest, der dreißig Sekunden dauert

Diesen können Sie sofort machen, und er sagt Ihnen mehr als jede Messung:

1. Öffnen Sie Ihre Startseite.
2. Klicken Sie **nicht** ins Fenster. Drücken Sie die Tabulatortaste.
3. Drücken Sie sie weiter, zwanzig-, dreißigmal.

**Sehen Sie jederzeit, wo Sie gerade sind?** Wenn der Rahmen um das gerade angesteuerte Element verschwindet — und sei es nur auf einem farbigen Hintergrund —, ist das der Befund. Er ist außerdem eine der häufigsten Fundstellen überhaupt, weil viele Gestaltungsvorlagen die Fokusmarkierung ausdrücklich entfernen: Sie stört den Gesamteindruck.

**Bleiben Sie irgendwo hängen?** Wenn Sie in einem Element ankommen und mit der Tabulatortaste nicht mehr herauskommen, ist das die schwerwiegendste Form dieses Befunds. Häufig bei eingebetteten Kartendiensten und Chat-Fenstern.

::: ABB 8.1
format:   breit
titel:    Der Tabulator-Selbsttest
zweck:    Der Leser soll den Test machen, während er das Kapitel
          liest — er ist der einzige in diesem Buch, der ohne
          Werkzeug auskommt.
inhalt:   Drei schematische Bildschirmausschnitte derselben
          nachgebauten Startseite nebeneinander. Jeweils ein
          anderes Element mit einem deutlichen Fokusrahmen
          markiert: Navigationspunkt, Schaltfläche, Formularfeld.
          Über den drei Bildern die Beschriftung „Tab", „Tab", „Tab".
          Rechts ein vierter Ausschnitt, durchgestrichen: dasselbe
          Element ohne erkennbaren Rahmen, beschriftet „so nicht".
warnung:  Erfundener Betrieb. Keine reale Seite nachbauen.
bezug:    Abschnitt 8.8, nach dem Selbsttest
bu:       Wenn Sie nicht sehen, wo Sie sind, sieht es auch sonst niemand.
sw-fest:  ja
:::

---

## 8.9 Ihre Punkte in dieser Kategorie

| Code | Kriterium | Möglich | Erreicht | Nicht erhoben |
|---|---|---|---|---|
| B1 | Gesamtwert der Barrierefreiheitsprüfung | 3 | ____ | ☐ |
| B2 | Farbkontraste | 2 | ____ | ☐ |
| B3 | Alternativtexte für Bilder | 2 | ____ | ☐ |
| B4 | Semantik und Struktur | 2 | ____ | ☐ |
| B5 | Tastaturbedienung | 1 | ____ | ☐ |
| | **Summe** | **10** | ____ | |

**B1, B2 und B5 hängen an der externen Messung.** Fällt sie aus, kreuzen Sie alle drei als nicht erhoben an und ziehen Sie 6 Punkte von Ihrem anwendbaren Maximum ab.

---

## 8.10 Vier verbreitete Irrtümer

**„Barrierefreiheit betrifft uns nicht, wir haben keine behinderten Kunden."**
Sie wissen es nicht. Niemand meldet sich, um mitzuteilen, dass er eine Website nicht bedienen konnte — er ruft den Wettbewerber an. Und der größte Teil der Betroffenen hat keine Behinderung im rechtlichen Sinn: Menschen mit nachlassendem Sehvermögen, Menschen mit einem Gipsarm, Menschen im hellen Sonnenlicht.

**„Das ist etwas für Behörden."**
Seit dem 28. Juni 2025 gilt das Barrierefreiheitsstärkungsgesetz auch für bestimmte private Anbieter. Ob Sie darunterfallen, hängt von Betriebsgröße und Geschäftsmodell ab — siehe Abschnitt 5.7. **Unabhängig davon ist es eine Frage der erreichbaren Kundschaft**, nicht der Pflicht.

**„Wir haben einen Barrierefreiheits-Assistenten eingebaut."**
Gemeint sind Zusatzwerkzeuge, die ein Symbol einblenden, über das sich Schriftgröße und Kontrast verstellen lassen. Sie beheben die Ursachen nicht — die Überschriftenstruktur bleibt kaputt, die Alternativtexte bleiben leer, die Tastaturbedienung bleibt unmöglich. **Der Standard bewertet sie nicht**, und in der fachlichen Diskussion sind sie umstritten.

**„Zehn von zehn heißt, wir sind barrierefrei."**
Nein — und das ist der Satz, mit dem dieses Kapitel begonnen hat. Zehn Punkte heißen: Keine der von außen prüfbaren Hürden ist vorhanden. Alles, was sich nur durch Benutzung feststellen lässt, bleibt ungeprüft.

---

## Das Wichtigste aus diesem Kapitel

> - **Fünf Kriterien, 10 Punkte** — bewusst wenig, weil sich von außen nur ein Teil prüfen lässt.
> - **B1, B2 und B5 hängen an der externen Messung.** Fällt sie aus, sind 6 Punkte hier und 12 in Kapitel 7 nicht erhebbar.
> - **B3 ist die strengste Staffelung des Standards**: volle Punkte erst ab 95 Prozent. Bei Alternativtexten gibt es kein „überwiegend".
> - **Geprüft wird, ob eine Textalternative da ist, nicht ob sie taugt.** Nutzen Sie diese Lücke nicht aus.
> - **Dekorative Bilder bekommen eine leere Textalternative**, keine beschreibende.
> - **B4 und E2 betrachten dieselbe Überschriftenstruktur** aus zwei Richtungen. Eine Korrektur wirkt zweimal.
> - **Der Tabulator-Test dauert dreißig Sekunden** und braucht kein Werkzeug.

---

<!-- REDAKTIONELLE ANMERKUNGEN — NICHT DRUCKEN -->

## Offene Punkte zu Kapitel 8

| # | Punkt | Wer | Status |
|---|---|---|---|
| 1 | 🔴 **B4: Kriterienhinweis nennt vier Prüfungen, gemessen werden zwei.** Der Hinweis lautet „genau eine H1, saubere Hierarchie, `lang`-Attribut, Labels". Die Bewertung prüft nur die ersten beiden. Dasselbe Muster wie bei P5 in Kapitel 7. **Entscheidung nötig:** entweder Sprachauszeichnung und Formularbeschriftungen ergänzen, oder den Kriterienhinweis auf das kürzen, was tatsächlich geprüft wird. Abschnitt 8.7 beschreibt nur die zwei tatsächlichen Prüfungen | Technik / GF | **offen** |
| 2 | 🔴 **B4 steht in der erzeugten Tabelle als „abgeleitet" — und das ist der bekannte Widerspruch.** Die Bewertung schreibt „gemessen". Die Tabelle in 8.1 wird beim nächsten Export von selbst auf „gemessen" wechseln, **sobald S2.1 im Repo erledigt ist.** Bis dahin druckt das Buch den Katalogwert — nicht den Berichtswert. Ursprünglicher Befund: **B4: Erhebungsart widersprüchlich deklariert.** Das Kriterium ist im Katalog als „abgeleitet" geführt, die Bewertung schreibt „gemessen". Der Bericht weist damit möglicherweise eine andere Erhebungsart aus als der Katalog. Kapitel 3 verspricht, dass jede Erhebungsart gekennzeichnet ist — dieser Widerspruch untergräbt das Versprechen | Technik | **offen** |
| 3 | 🔴 **Korrektur an Kapitel 7 erforderlich.** Abschnitt 7.3 spricht von „zwei Kriterien in Kapitel 8". Es sind **drei** (B1, B2, B5), zusammen 6 Punkte. Die Punktsumme in Kapitel 7 stimmt, die Anzahl nicht. **In Kapitel 7 korrigieren** | Autor | **korrigiert einzupflegen** |
| 4 | **C6 aus dem Restarbeiten-Report:** Die Aussage, ein bestimmter Anteil der Anforderungen sei automatisiert prüfbar, war dort mit „Quelle oder abschwächen" markiert. Abschnitt 8.2 nennt bewusst **keine Quote**, sondern beschreibt qualitativ, was nicht prüfbar ist. Beim Lektorat sichern, dass keine Zahl nachträglich eingesetzt wird | Autor / Lektorat | **erledigt, sichern** |
| 5 | **Doppelwertung B4 / E2.** Der Restarbeiten-Report führt sie als A7. Abschnitt 8.7 stellt sie transparent dar. Kapitel 9 muss mit demselben Wortlaut darauf Bezug nehmen | Autor | **Folgekapitel** |
| 6 | **Barrierefreiheits-Assistenten.** Abschnitt 8.10 nennt sie umstritten und sagt, der Standard bewerte sie nicht. Das ist eine wertende Aussage über ein käufliches Produkt. **Beim Anwaltstermin mitprüfen**, ob die Formulierung so tragfähig ist | Recht | **offen** |
| 7 | **Zusammenhang mit dem eigenen Buchsatz.** Dieses Kapitel bewertet Farbkontraste nach WCAG AA. Das Buch selbst muss diese Kontraste im Satz einhalten und darf Informationen nicht allein über Farbe codieren — sonst ist das Kapitel angreifbar. Steht bereits im Buchkonzept unter 1.4 | Gestaltung | **verbindlich** |
| 8 | **Fall Elektro Hansen:** B1 = 2, B2 = 2, B3 = 0, B4 = 2, B5 = 0 ergibt 6. Muss zur Kategorietabelle in Kapitel 3 passen (6/10) und zum Gewinn von +2 durch Alternativtexte | Autor | Drift-Kandidat |
| 9 | Nur eine Abbildung auf 14 Seiten. Zweiter Kandidat: die drei häufigsten Kontrastfehler aus 8.5 als Gegenüberstellung — sie sind rein visuell und in Text schlecht zu vermitteln | Gestaltung | **empfohlen** |

**Abbildungen in diesem Kapitel:** 1 (ABB 8.1 breit)
**Marginalien:** 6
**Geschätzter Satzumfang:** 13–14 Seiten
