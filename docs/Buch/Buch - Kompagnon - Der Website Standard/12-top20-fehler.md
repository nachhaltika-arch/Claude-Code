---
kapitel: 12
titel: "Die zwanzig häufigsten Fehler"
punkte: null
status: entwurf-fertig
zuletzt_geprueft: 2026-08-14
standard_version: "2026.2"
---

# 12. Die zwanzig häufigsten Fehler

## 12.1 Wie Sie dieses Kapitel benutzen

Die Kapitel 3 bis 10 sind nach Kategorien geordnet — nach der Logik des Bewertungssystems.
Dieses Kapitel ist anders geordnet: nach dem, was uns in Website-Prüfungen tatsächlich am
häufigsten begegnet.

Viele Leser finden hier schneller etwas wieder als im systematischen Teil. Wenn Sie den
Selbsttest aus Kapitel 11 gemacht haben, gleichen Sie Ihre fünf größten Lücken aus
Abschnitt 11.9 mit der Übersicht unten ab — mit hoher Wahrscheinlichkeit stehen sie hier.

Jeder Fehler ist gleich aufgebaut: **warum er passiert**, **was er kostet**, **wie er
behoben wird**. Die Angabe „Aufwand" bezieht sich auf einen Fachbetrieb, nicht auf Sie
selbst.

Eine Beobachtung vorweg, die für fast alle zwanzig gilt: **Kaum einer dieser Fehler ist
durch Nachlässigkeit entstanden.** Die meisten waren zum Zeitpunkt der Erstellung richtig
oder üblich. Was fehlt, ist nicht Sorgfalt, sondern eine wiederkehrende Kontrolle.

---

## 12.2 Die zwanzig Fehler im Überblick

| Nr. | Fehler | Betrifft | Aufwand | Punkte |
|---|---|---|---|---|
| 1 | Schriftart von fremdem Server | L3, S4 | 1 Std | bis 6 + Deckel |
| 2 | Einwilligungsdialog ohne echtes Ablehnen | L3 | 2 Std | bis 4 + Deckel |
| 3 | Datenschutzerklärung passt nicht zur Website | L2 | 2 Std | bis 4 |
| 4 | Impressum nur auf der Startseite verlinkt | L1 | 15 Min | 1–2 |
| 5 | Berufsständische Angaben fehlen | L1 | 30 Min | 2–4 |
| 6 | Zertifikat fällt lautlos aus | S1, S2 | 1 Std | bis 5 + Deckel |
| 7 | Fotos direkt vom Telefon hochgeladen | P1, P4, P5 | ½ Tag | bis 8 |
| 8 | Automatisch wechselnde Bilderfolge | P1, D1 | 1 Std | 2–4 |
| 9 | Sperrvermerk vom Testsystem übernommen | E3 | 15 Min | 3 + Sichtbarkeit |
| 10 | Alle Seiten mit demselben Titel | E1 | 1 Std | 1–2 |
| 11 | Keine strukturierten Daten | E4 | 2 Std | 3 |
| 12 | Uneinheitliche Kontaktdaten | E5 | ½ Tag | 1–2 |
| 13 | „Herzlich willkommen" statt Leistungsaussage | C1 | 1 Std | bis 3 |
| 14 | Telefonnummer nicht anklickbar | C3 | 15 Min | 1 |
| 15 | Kontaktformular läuft ins Leere | — | 30 Min | keine, aber teuer |
| 16 | Fünf gleichrangige Knöpfe, kein Hauptziel | C2 | 2 Std | bis 3 |
| 17 | Bildagenturmotive statt eigener Fotos | D4, C4 | 1 Nachmittag | 2 |
| 18 | Keine Kostenorientierung | C5 | 2 Std | 1–2 |
| 19 | Alle Leistungen auf einer Sammelseite | I1, E1, C5 | 2–3 Tage | bis 8 |
| 20 | Veraltete Jahreszahl, verwaister Neuigkeitenbereich | I2 | 30 Min | 1 |

---

## 12.3 Recht und Datenschutz

### Fehler 1 — Die Schriftart kommt von einem fremden Server

**Warum es passiert:** Bis vor wenigen Jahren war es der Normalweg, Schriftarten aus einer
öffentlichen Bibliothek einzubinden. Praktisch jede Vorlage und jedes Baukastensystem tat
es. Der Betriebsinhaber hat davon nie erfahren, und der Dienstleister hat es damals richtig
gemacht.

**Was es kostet:** Bei jedem Seitenaufruf wird die IP-Adresse des Besuchers an einen
fremden Server übertragen, ohne Einwilligung, häufig außerhalb der EU. Punktverlust bei L3
und S4 — und, gravierender, ein **Ausschlusskriterium**: höchste erreichbare Stufe Bronze.
Ein Gericht hat dafür Schadensersatz zugesprochen, in der Folge kam es zu einer Welle von
Abmahnschreiben.

**Behebung:** Schriftdatei herunterladen, auf dem eigenen Server ablegen, Einbindung
umstellen. Die Seite lädt danach zusätzlich schneller. **Aufwand: 1 Stunde.**

> **Das ist der lohnendste Einzelfix in diesem ganzen Buch.** Eine Stunde Arbeit, ein
> Ausschlusskriterium weniger, Punkte in drei Kategorien.

---

### Fehler 2 — Der Einwilligungsdialog ohne echtes Ablehnen

**Warum es passiert:** Das verbreitetste Muster: ein farbiger Knopf „Alle akzeptieren",
daneben ein grauer Textlink „Einstellungen". Viele fertige Lösungen liefern das so aus,
weil es die Zustimmungsquote erhöht.

**Was es kostet:** Bis zu 4 Punkte bei L3. Und wenn zusätzlich vor der Antwort schon
geladen wird — was in dieser Konstellation meistens der Fall ist —, greift der
Bronze-Deckel.

**Behebung:** „Ablehnen" auf dieselbe Ebene, in dieselbe Größe, in vergleichbare
Auffälligkeit. Sicherstellen, dass vor der Entscheidung nichts Einwilligungspflichtiges
lädt. Widerrufsmöglichkeit dauerhaft erreichbar machen. **Aufwand: 2 Stunden.**

---

### Fehler 3 — Die Datenschutzerklärung passt nicht zur Website

**Warum es passiert:** Ein Mustertext wurde einmal übernommen und seither nicht angepasst.
Die Website hat sich verändert, der Text nicht.

**Was es kostet:** Bis zu 4 Punkte bei L2. Und ein Glaubwürdigkeitsproblem, das über die
Punkte hinausgeht: Wer eine Erklärung veröffentlicht, die erkennbar nicht zu seiner Website
passt, dokumentiert damit, dass er sich nicht damit befasst hat.

**Behebung:** Die Liste der Fremdverbindungen aus dem Selbsttest (Block A2) neben die
Erklärung legen. Jeden geladenen Dienst ergänzen, jeden nicht genutzten streichen.
Anschließend anwaltlich prüfen lassen. **Aufwand: 2 Stunden plus Prüfung.**

---

### Fehler 4 — Das Impressum ist nur auf der Startseite verlinkt

**Warum es passiert:** Der Fußbereich wurde einmal für die Startseite gebaut, die
Unterseiten verwenden eine andere Vorlage. Fällt niemandem auf, weil niemand über die
Unterseiten einsteigt — Besucher aus Suchmaschinen aber schon.

**Was es kostet:** 1 bis 2 Punkte bei L1. Rechtlich verlangt wird die ständige
Verfügbarkeit, nicht die Verfügbarkeit auf einer Seite.

**Behebung:** Fußbereich vereinheitlichen. **Aufwand: 15 Minuten.**

---

### Fehler 5 — Die berufsständischen Angaben fehlen

**Warum es passiert:** Das Impressum stammt aus einem allgemeinen Generator. Die kennen
Firma, Anschrift, Register und Steuernummer — aber nicht die Zusatzpflichten für
Kammerberufe und zulassungspflichtige Gewerke.

**Was es kostet:** 2 bis 4 Punkte bei L1. Betroffen sind Handwerksbetriebe in
zulassungspflichtigen Gewerken, Steuerberater, Rechtsanwälte, Ärzte, Architekten und
weitere reglementierte Berufe.

**Behebung:** Kammer, gesetzliche Berufsbezeichnung, Verleihungsstaat, Fundstelle der
berufsrechtlichen Regelungen und gegebenenfalls Angaben zur Berufshaftpflicht ergänzen.
Die meisten Kammern stellen ihren Mitgliedern Musterformulierungen bereit — die sind
genauer als jeder allgemeine Generator. **Aufwand: 30 Minuten.**

---

## 12.4 Sicherheit

### Fehler 6 — Das Zertifikat fällt lautlos aus

**Warum es passiert:** Zwei Varianten, beide ohne Vorwarnung.

*Variante A:* Die automatische Verlängerung scheitert nach einer Konfigurationsänderung
beim Hoster. Es gibt keine Meldung, keine E-Mail, keinen Hinweis.

*Variante B:* Das Zertifikat gilt für `firma.de`, aber nicht für `www.firma.de` — oder
umgekehrt. Beide Schreibweisen sind im Umlauf, ein Teil der Besucher trifft die falsche.

**Was es kostet:** Bis zu 5 Punkte bei S1 und S2. Und bei vollständigem Ausfall den
**Ausschluss auf „Nicht konform"**. Praktisch bedeutet es: Statt Ihrer Website sieht der
Besucher eine ganzseitige Warnung seines Browsers. Wer nicht technisch versiert ist, geht
zurück.

**Behebung:** Zertifikat prüfen und für beide Adressvarianten ausstellen lassen.
Weiterleitung von unverschlüsselt auf verschlüsselt einrichten. **Und das Wichtigste: Das
Ablaufdatum in den Kalender eintragen, mit Erinnerung zwei Wochen vorher.**
**Aufwand: 1 Stunde.**

---

## 12.5 Ladezeit und Bilder

### Fehler 7 — Fotos direkt vom Telefon hochgeladen

**Warum es passiert:** Es ist der schnellste Weg, und niemand hat einen Arbeitsschritt
dazwischen vorgesehen. Ein aktuelles Mobiltelefon nimmt mit über 4.000 Bildpunkten
Kantenlänge auf; dargestellt wird das Bild mit vielleicht 800.

**Was es kostet:** Bis zu 8 Punkte über drei Kriterien: P1 (Ladezeit), P4 (Mobilbewertung)
und P5 (Bildoptimierung). Wenn zusätzlich die Alternativtexte fehlen — was fast immer der
Fall ist —, kommen bis zu 3 Punkte aus Kapitel 6 dazu.

**Behebung:** Bestehende Bilder auf maximal 1.600 Bildpunkte Breite verkleinern und in ein
modernes Format umwandeln. Bei der Gelegenheit Alternativtexte ergänzen — es ist derselbe
Arbeitsschritt. **Aufwand: ein halber Tag.**

> **Der eigentliche Fix ist der dritte Schritt:** Die automatische Aufbereitung beim
> Hochladen einrichten. Ohne sie ist die Seite in zwei Jahren wieder dort, wo sie war.

---

### Fehler 8 — Die automatisch wechselnde Bilderfolge

**Warum es passiert:** Sie galt jahrelang als Standardelement jeder Startseite und ist in
vielen Vorlagen fest eingebaut.

**Was es kostet:** 2 bis 4 Punkte über P1 und D1. Sie lädt mehrere große Bilder auf einmal
und ist zugleich eines der acht Alterungsmerkmale aus Abschnitt 8.4.

Hinzu kommt etwas, das der Standard nicht misst: Untersuchungen zeigen seit Jahren, dass
Besucher wechselnde Bildbereiche weitgehend ignorieren. Der Aufwand fließt in ein Element,
das kaum jemand ansieht.

**Behebung:** Ein einziges starkes Bild, darüber die Leistungsaussage als Text, darunter
das Handlungsziel. Das behebt gleichzeitig Fehler 13. **Aufwand: 1 Stunde.**

---

## 12.6 Auffindbarkeit

### Fehler 9 — Der Sperrvermerk vom Testsystem

**Warum es passiert:** Während des Baus liegt die Website auf einem Testsystem und wird für
Suchmaschinen gesperrt — völlig richtig. Beim Umzug auf die richtige Adresse wird die
Sperre gelegentlich vergessen.

**Was es kostet:** 3 Punkte bei E3 — und den gesamten Nutzen der Website. Sie ist erreichbar,
schnell, gepflegt und erscheint in keiner einzigen Suche.

**Es gibt keine Fehlermeldung dafür.** Nichts weist darauf hin. Der Betriebsinhaber
wundert sich monatelang, warum über die neue Seite nichts hereinkommt, und schließt daraus,
dass Websites eben nichts bringen.

**Behebung:** Sperrvermerk entfernen, Website bei der Suchmaschine erneut anmelden.
**Aufwand: 15 Minuten.**

> **Prüfen Sie das jetzt**, auch wenn Sie den Selbsttest übersprungen haben: Geben Sie bei
> Google `site:ihredomain.de` ein. Kommt gar nichts, haben Sie diesen Fehler.

---

### Fehler 10 — Alle Seiten tragen denselben Titel

**Warum es passiert:** Das Titelfeld wird beim Anlegen neuer Seiten nicht gefüllt, das
System übernimmt den Standardwert.

**Was es kostet:** 1 bis 2 Punkte bei E1. Wichtiger als die Punkte: Für eine Suchmaschine
sehen acht Seiten aus wie achtmal dasselbe. Ihre Leistungsseite kann für ihre eigene
Suchanfrage nicht antreten.

**Behebung:** Für jede Seite einen eigenen Titel setzen, aufgebaut nach dem Muster Ihrer
Branchenklasse (Tabelle 7.4). **Aufwand: 1 Stunde für acht Seiten.**

---

### Fehler 11 — Keine strukturierten Daten

**Warum es passiert:** Sie sind unsichtbar. Niemand vermisst, was man nicht sieht.

**Was es kostet:** 3 Punkte bei E4 — und zunehmend die Sichtbarkeit in KI-formulierten
Antworten. Wer nicht maschinenlesbar angibt, was für ein Unternehmen er ist, wird dort
seltener genannt.

**Behebung:** Einen passenden Eintrag für Ihre Branchenklasse einfügen (Tabelle 7.7). Für
Standardfälle gibt es Generatoren; die Angaben müssen zeichengleich mit Impressum und
Unternehmensprofil sein. **Aufwand: 2 Stunden, danach dauerhaft erledigt.**

---

### Fehler 12 — Uneinheitliche Kontaktdaten

**Warum es passiert:** Über die Jahre entstehen Einträge in Verzeichnissen, Portalen und
Bewertungsplattformen — jedes Mal von einer anderen Person, in einer anderen Schreibweise.
„Hauptstraße" hier, „Hauptstr." dort, mit und ohne Rechtsformzusatz.

**Was es kostet:** 1 bis 2 Punkte bei E5 — und, schwerer wiegend, Sichtbarkeit in der
Kartenansicht. Suchmaschinen gleichen die Angaben über alle Quellen ab; Abweichungen
erzeugen Unsicherheit bei der Zuordnung.

**Behebung:** Eine verbindliche Schreibweise festlegen — ein Blatt Papier, eine Zeile pro
Angabe. Dann Website, Impressum, strukturierte Daten und die wichtigsten Verzeichnisse
angleichen. **Aufwand: ein halber Tag, überwiegend Recherche.**

---

## 12.7 Führung und Vertrauen

### Fehler 13 — „Herzlich willkommen" statt Leistungsaussage

**Warum es passiert:** Höflichkeit. Man begrüßt seine Gäste.

**Was es kostet:** Bis zu 3 Punkte bei C1 — und die wertvollste Fläche der ganzen Website.
Nach fünf Sekunden weiß der Besucher, dass es eine Firma dieses Namens gibt. Mehr nicht.

**Behebung:** Die Begrüßung durch eine Aussage ersetzen, die sagt, was Sie anbieten, für
wen und — bei lokalen Betrieben — wo. Als Text, nicht als Bild.
**Aufwand: 1 Stunde.**

---

### Fehler 14 — Die Telefonnummer ist nicht anklickbar

**Warum es passiert:** Die Nummer wurde als normaler Text eingetragen oder — schlimmer —
als Bild eingebunden, früher als Schutz vor automatischer Nummernsammlung. Dieser Schutz
ist heute wirkungslos, der Schaden geblieben.

**Was es kostet:** 1 Punkt bei C3. Der tatsächliche Schaden ist größer: Auf dem Telefon
muss die Nummer abgeschrieben werden, und das tut kaum jemand. Als Bild ist sie zusätzlich
für Suchmaschinen und Vorleseprogramme unsichtbar.

**Behebung:** Nummer als anklickbaren Verweis hinterlegen und in den Kopfbereich jeder Seite
setzen. **Aufwand: 15 Minuten.**

---

### Fehler 15 — Das Kontaktformular läuft ins Leere

**Warum es passiert:** Eine E-Mail-Adresse wurde geändert, ein Postfach aufgelöst, ein
Filter eingerichtet. Seither landen die Nachrichten im Spam-Ordner oder nirgends.

**Was es kostet:** Keine Punkte — der Standard kann das nicht prüfen. Aber es ist der
teuerste Fehler dieser Liste, weil er jede Anfrage vernichtet, die trotz aller anderen
Mängel zustande kam.

**Behebung:** Sich selbst über das eigene Formular eine Anfrage schicken. Prüfen, wo sie
ankommt. Diese Prüfung gehört ab sofort einmal im Quartal in Ihren Kalender.
**Aufwand: 30 Minuten.**

---

### Fehler 16 — Fünf gleichrangige Knöpfe, kein Hauptziel

**Warum es passiert:** Jede Abteilung, jeder Beteiligte wollte etwas verlinkt haben. Nichts
wurde weggelassen, weil nichts unwichtig erschien.

**Was es kostet:** Bis zu 3 Punkte bei C2. Der Besucher hat fünf Möglichkeiten und trifft
keine.

**Behebung:** Ein Ziel deutlich hervorheben, die anderen untergeordnet erreichbar lassen.
Und die Beschriftung vom Vorgang auf das Ergebnis umstellen: nicht „Kontakt", sondern
„Angebot anfordern". **Aufwand: 2 Stunden.**

---

### Fehler 17 — Bildagenturmotive statt eigener Fotos

**Warum es passiert:** Es gab keine eigenen Bilder, und Agenturmotive sehen professionell
aus.

**Was es kostet:** 2 Punkte über D4 und C4 — einmal für die uneinheitliche Bildsprache,
einmal, weil ein inszeniertes Motiv kein Vertrauenssignal ist. Der eigentliche Schaden ist
größer: Der Betrachter erkennt es und schließt daraus, dass es nichts zu zeigen gibt.

**Behebung:** Ein Nachmittag mit dem Telefon — auf der Baustelle, in der Werkstatt, im
Empfangsbereich, mit dem Team. Auf Licht achten, gerade halten, quer fotografieren.
**Aufwand: ein Nachmittag plus Auswahl.**

---

### Fehler 18 — Keine Kostenorientierung

**Warum es passiert:** Der berechtigte Einwand, dass jeder Auftrag anders ist.

**Was es kostet:** 1 bis 2 Punkte bei C5 — und mehr Zeit, als Sie denken. Wer Ihre
Größenordnung nicht kennt, fragt entweder gar nicht an oder fragt an, ohne zu Ihnen zu
passen. Beides kostet.

**Behebung:** Eine Spanne, eine Kostenlogik oder einen Einstiegswert nennen (Abschnitt
9.8). Keine Festpreise. **Aufwand: 2 Stunden, davon eineinhalb zum Nachdenken.**

**Für reglementierte Berufe gilt dieser Punkt nicht** — an seine Stelle tritt die
Beschreibung des Ablaufs.

---

## 12.8 Inhalt und Pflege

### Fehler 19 — Alle Leistungen auf einer Sammelseite

**Warum es passiert:** Die Website wurde als kompakte Visitenkarte angelegt, und die
Leistungen sind seither gewachsen — die Struktur nicht.

**Was es kostet:** Bis zu 8 Punkte über I1, E1 und C5. Für sieben von acht Suchanfragen
sind Sie unsichtbar, und Ihr Angebot bleibt unscharf.

**Behebung:** Aus den drei bis fünf Leistungen, die tatsächlich Umsatz bringen, eigene
Seiten machen. Je 300 bis 500 Wörter entlang der Fragen aus Abschnitt 10.4.
**Aufwand: 2 bis 3 Tage.**

Das ist die aufwendigste Maßnahme dieser Liste — und die mit der größten Wirkung.

---

### Fehler 20 — Veraltete Jahreszahl, verwaister Neuigkeitenbereich

**Warum es passiert:** Die Jahreszahl im Fußbereich wurde einmal eingetippt statt
automatisch gesetzt. Der Neuigkeitenbereich wurde mit guten Absichten angelegt und nach
drei Beiträgen nicht mehr gepflegt.

**Was es kostet:** 1 Punkt bei I2. Und die Frage, die Sie nicht beantworten können: *Gibt
es die Firma überhaupt noch?*

**Behebung:** Jahreszahl automatisch setzen lassen. Neuigkeitenbereich entweder pflegen
oder entfernen — Entfernen ist ausdrücklich erlaubt und besser als ein Beweis der
Vernachlässigung. **Aufwand: 30 Minuten.**

---

## 12.9 Wirkung pro Aufwand

Wenn Sie nur wenig Zeit haben, arbeiten Sie diese Reihenfolge ab. Sie ist nach Punkten je
Arbeitsstunde sortiert, nicht nach Kategorie.

| Rang | Fehler | Aufwand | Wirkung |
|---|---|---|---|
| 1 | Nr. 9 — Sperrvermerk prüfen | 15 Min | 3 Punkte + gesamte Sichtbarkeit |
| 2 | Nr. 4 — Impressum überall verlinken | 15 Min | 1–2 Punkte |
| 3 | Nr. 14 — Telefonnummer anklickbar | 15 Min | 1 Punkt + Anrufe |
| 4 | Nr. 1 — Schriftart lokal einbinden | 1 Std | bis 6 Punkte + Ausschluss weg |
| 5 | Nr. 6 — Zertifikat prüfen und Termin setzen | 1 Std | bis 5 Punkte + Ausschluss weg |
| 6 | Nr. 5 — Berufsständische Angaben | 30 Min | 2–4 Punkte |
| 7 | Nr. 20 — Jahreszahl und Altbestand | 30 Min | 1 Punkt |
| 8 | Nr. 13 — Leistungsaussage statt Begrüßung | 1 Std | bis 3 Punkte |
| 9 | Nr. 15 — Formular testen | 30 Min | keine Punkte, aber teuer |
| 10 | Nr. 7 — Bilder aufbereiten | ½ Tag | bis 11 Punkte über zwei Kategorien |

**Die ersten sieben zusammen: etwa vier Stunden.** Sie bringen bei einer typischen Website
zwischen 12 und 20 Punkte und beseitigen in der Regel beide Ausschlusskriterien.

Kapitel 13 macht daraus einen Plan über dreißig Tage.

---

> ### Das Wichtigste aus diesem Kapitel
>
> - **Kaum einer dieser Fehler entstand durch Nachlässigkeit.** Die meisten waren einmal
>   richtig. Was fehlt, ist die wiederkehrende Kontrolle.
> - **Die drei stillen Fehler**, die niemand bemerkt: der Sperrvermerk (Nr. 9), das
>   ausgefallene Zertifikat (Nr. 6), das tote Formular (Nr. 15). Alle drei kosten mehr als
>   alles andere in dieser Liste — und keiner erzeugt eine Fehlermeldung.
> - **Vier Stunden für die ersten sieben Punkte** aus der Rangliste bringen typischerweise
>   12 bis 20 Punkte.
> - Die aufwendigste Maßnahme (Nr. 19, eigene Leistungsseiten) ist zugleich die
>   wirksamste — aber erst nach den schnellen Korrekturen.

---

## Redaktionelle Anmerkungen (nicht drucken)

**Die Häufigkeitsaussage muss belegt werden.** Der Kapiteltitel behauptet, dies seien die
zwanzig häufigsten Fehler. Diese Liste ist derzeit fachlich begründet, aber nicht
ausgezählt. **Vor Drucklegung zwingend erforderlich:** eine Auswertung der KAS-Audits mit
der tatsächlichen Häufigkeit je Befund. Dann kann im Kapitel stehen: „In X ausgewerteten
Websites trat dieser Befund bei Y Prozent auf." Das macht aus einer Behauptung eine
Erhebung — und aus dem Kapitel den zitierfähigsten Teil des Buches.

**Reihenfolge nach Erhebung anpassen.** Wenn die Auswertung vorliegt, sollte die
Nummerierung der tatsächlichen Häufigkeit folgen. Aktuell ist sie thematisch gruppiert.

**Aufwandsangaben prüfen.** Alle Angaben beziehen sich auf einen Fachbetrieb bei einer
gepflegten Website mit gängigem System. Bei Altsystemen ohne Zugang zum Quelltext liegen
sie deutlich höher. **Empfehlung:** einen Satz dazu in 12.1 ergänzen, sobald die Zahlen
aus der Praxis vorliegen.

**Punktangaben in der Übersichtstabelle** sind Spannen und mit den Kapiteln 3 bis 10
abgeglichen. Bei jeder Änderung an einer Punktzahl muss diese Tabelle nachgezogen werden —
sie ist die dritte Stelle nach Kategoriekapitel und Selbsttest, an der dieselben Zahlen
stehen. **Auch diese Tabelle sollte beim Build erzeugt werden.**

**Fehler 8 — nicht belegte Aussage.** „Untersuchungen zeigen seit Jahren, dass Besucher
wechselnde Bildbereiche weitgehend ignorieren." Das ist Fachkonsens, aber ohne konkrete
Quelle. Entweder belegen oder auf eine eigene Beobachtung umformulieren.

**Abbildungen (3 Stück):**
1. Die drei stillen Fehler als Tafel: was der Betreiber sieht gegen das, was tatsächlich
   passiert
2. Die Rangliste aus 12.9 als Balkendiagramm Punkte je Arbeitsstunde
3. Fehler 13 als Vorher-Nachher des ersten sichtbaren Bereichs — schematisch nachgebaut
