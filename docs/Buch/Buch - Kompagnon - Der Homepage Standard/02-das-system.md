---
kapitel: 2
titel: "Das Bewertungssystem und Ihre Branchenklasse"
punkte: null
status: entwurf-fertig
zuletzt_geprueft: 2026-08-14
standard_version: "2026.2"
---

# 2. Das Bewertungssystem und Ihre Branchenklasse

## 2.1 Drei Anforderungen an ein brauchbares Bewertungssystem

Bevor wir uns die Kategorien ansehen, drei Anforderungen, an denen sich jedes
Bewertungssystem messen lassen muss. Fehlt eine davon, ist es kein Standard, sondern eine
Meinung mit Zahlen.

**Es muss messbar sein.** Jedes Kriterium muss so formuliert sein, dass zwei Prüfer
unabhängig voneinander zum selben Ergebnis kommen. „Die Seite wirkt vertrauenswürdig" ist
nicht messbar. „Auf der Startseite sind Bewertungen mit Namen und Datum sichtbar" ist
messbar.

**Es muss wiederholbar sein.** Dieselbe Website, zwei Wochen später, unverändert —
dasselbe Ergebnis. Das klingt selbstverständlich, ist es aber nicht: Viele
Website-Bewertungen im Umlauf hängen von der Tagesform des Prüfers ab, von der Tageszeit
eines Geschwindigkeitstests oder davon, welcher Dienstleister gerade etwas verkaufen will.

**Es muss unabhängig vom Prüfer sein.** Wer die Bewertung durchführt, darf keinen Einfluss
auf das Ergebnis haben.

Dieser dritte Punkt gehört offen angesprochen: Der Homepage Standard wurde von einem
Unternehmen entwickelt, das auch Websites baut. Das ist ein Interessenkonflikt. Der
einzige Umgang damit ist vollständige Offenlegung — jedes Kriterium, jede Punktzahl und
jede Prüfmethode steht in diesem Buch. Sie können jede Bewertung selbst nachvollziehen und
jeden Punkt bestreiten. Ein System, das man nicht nachprüfen kann, sollten Sie nicht
verwenden. Auch dieses nicht.

---

## 2.2 Der wichtigste Grundsatz: nichts behaupten, was nicht gemessen wurde

Wenn Sie sich aus diesem Kapitel nur eine Sache merken, dann diese.

Website-Bewertungen haben ein verbreitetes Problem: Sie zeigen mehr Kriterien an, als sie
tatsächlich erheben. Was nicht gemessen werden kann, wird geschätzt — und als Messung
ausgegeben. Der Leser sieht eine Zahl mit zwei Nachkommastellen und hält sie für ein
Ergebnis.

Der Homepage Standard kennzeichnet deshalb bei **jedem einzelnen Kriterium**, woher der
Wert stammt:

| Kennzeichnung | Bedeutung | Zählt in die Bewertung |
|---|---|---|
| **gemessen** | Über eine technische Prüfung eindeutig festgestellt — der Seitenquelltext, ein Serverantwort-Header, ein Zertifikat, ein Messwert | ja |
| **abgeleitet** | Aus gemessenen Werten nach einer festen Regel berechnet | ja |
| **Einschätzung** | Ein Mensch oder ein Sprachmodell hat nach einem festen Bewertungsraster geurteilt — bei Gestaltung und Verständlichkeit unvermeidbar | ja, gekennzeichnet |
| **nicht erhoben** | Die Prüfung war nicht möglich | **nein** |

Die letzte Zeile ist die entscheidende. Konnte ein Kriterium nicht geprüft werden — weil
die Seite den Zugriff blockiert, weil ein Messdienst nicht erreichbar war, weil die
Unterseite nicht geladen werden konnte —, dann wird es **weder mit null bewertet noch
geschätzt**. Es fällt vollständig aus der Rechnung. Der Punktwert wird auf die tatsächlich
geprüften Kriterien umgerechnet.

Ein Beispiel: Werden 92 der 100 möglichen Punkte tatsächlich geprüft und davon 66 erreicht,
lautet das Ergebnis nicht 66, sondern 72 Punkte — 66 von 92, umgerechnet auf 100. Im
Bericht steht dann, welche Kriterien nicht geprüft werden konnten und warum.

Warum das so wichtig ist: Ein Bericht, der einen nicht messbaren Punkt stillschweigend mit
null bewertet, macht Ihre Website schlechter, als sie ist — und verkauft Ihnen anschließend
die Behebung eines Problems, das vielleicht gar nicht existiert. Das ist die häufigste
unehrliche Praxis in diesem Markt.

---

## 2.3 Was tatsächlich geprüft wird

Bevor Sie den Kriterien vertrauen, sollten Sie wissen, worauf sie schauen. Eine
vollständige Prüfung nach diesem Standard betrachtet nicht „die Website", sondern eine
klar begrenzte Auswahl.

### Die geprüften Seiten

| Seite | Auswahl |
|---|---|
| Startseite | immer |
| Impressum | über die Verlinkung gesucht und geladen |
| Datenschutzerklärung | über die Verlinkung gesucht und geladen |
| Kontaktseite | sofern vorhanden |
| Bis zu drei Leistungsseiten | die am häufigsten aus der Hauptnavigation verlinkten |

Mehr Seiten verbessern das Ergebnis kaum und vervielfachen die Prüfdauer. Sechs bis sieben
Seiten genügen, um die Struktur eines Auftritts zuverlässig zu beurteilen — sie decken bei
einem typischen Unternehmensauftritt den größten Teil des Inhalts ab.

Dass Impressum und Datenschutzerklärung **wirklich geladen** werden, klingt
selbstverständlich, ist es aber nicht. Viele Website-Prüfungen suchen lediglich nach dem
Wort „Impressum" im Quelltext der Startseite. Das findet den Link im Fußbereich — und sagt
nichts darüber, ob die Seite dahinter existiert, erreichbar ist und die Pflichtangaben
enthält.

### Wie geprüft wird

| Prüfung | Vorgehen |
|---|---|
| Seiteninhalt und Struktur | Aufruf mit einem echten Browser, damit auch nachgeladene Inhalte erfasst werden |
| Darstellung | Bildschirmaufnahme der Startseite, einmal am Rechner und einmal am Mobiltelefon |
| Verschlüsselung | echter Verbindungsaufbau mit Prüfung des Zertifikats, nicht nur ein Blick auf die Adresse |
| Ladezeitwerte | Messung mobil und am Rechner, bevorzugt anhand echter Nutzerdaten |
| Suchmaschinen-Grundlagen | Abruf der Steuerdateien, die Suchmaschinen auslesen |
| Einwilligungen | Aufruf ohne jede Interaktion und Aufzeichnung, was dabei bereits geladen und gespeichert wird |

Der letzte Punkt ist der aussagekräftigste der ganzen Prüfung. Die Seite wird geöffnet und
**nichts** angeklickt — kein „Akzeptieren", kein „Ablehnen", kein Scrollen. Alles, was in
diesem Moment schon an Daten fließt und an Speichereinträgen entsteht, geschieht ohne
Einwilligung. Das lässt sich nicht wegdiskutieren, und es ist der Punkt, an dem die meisten
Websites auffallen.

Eine vollständige Prüfung dauert etwa drei bis vier Minuten.

### Was nicht geprüft wird

Bereiche hinter einem Login. Bestellstrecken bis zum tatsächlichen Kaufabschluss. Inhalte,
die erst nach dem Ausfüllen eines Formulars erscheinen. Und alles, was der Betreiber nicht
öffentlich zeigt — Verträge, interne Abläufe, Dokumentationen.

**Wenn eine Website automatisierte Zugriffe blockiert**, was bei größeren Auftritten
vorkommt, können einzelne Prüfungen nicht durchgeführt werden. Nach dem Grundsatz aus 2.2
fallen die betroffenen Kriterien dann aus der Rechnung — sie werden nicht geschätzt und
nicht mit null bewertet. Der Bericht weist das aus.

---

## 2.4 Die acht Kategorien

Der Standard prüft **38 Kriterien in acht Kategorien**. Zusammen ergeben sie 100 Punkte.

| # | Kategorie | Punkte | Kriterien | Was geprüft wird |
|---|---|---|---|---|
| 1 | Recht & Compliance | 20 | 5 | Pflichtangaben, Einwilligungen, Formulare |
| 2 | Sicherheit & Datenschutz | 10 | 4 | Verschlüsselung, Header, Drittanbieter |
| 3 | Performance & Core Web Vitals | 15 | 5 | Ladezeit, Stabilität, Mobilmessung, Bilder |
| 4 | Barrierefreiheit | 10 | 5 | Kontrast, Alternativtexte, Semantik, Tastatur |
| 5 | SEO & Auffindbarkeit | 15 | 6 | Titel, Struktur, Indexierbarkeit, lokale Signale |
| 6 | Design & Gestaltung | 10 | 5 | Aktualität, Typografie, Farbe, Bilder, Mobil |
| 7 | Conversion & Nutzerführung | 15 | 5 | Klarheit, Handlungsziel, Kontakt, Vertrauen, Angebot |
| 8 | Inhalt & Substanz | 5 | 3 | Leistungsseiten, Aktualität, Textqualität |
| | **Gesamt** | **100** | **38** | |

Zwei Kategorien werden Sie in anderen Website-Checklisten selten finden: **Design** und
**Conversion**. Genau das sind aber die beiden Dinge, die Sie selbst auf Ihrer Seite sehen
und über die Sie mit einem Dienstleister diskutieren. Sie unbewertet zu lassen, weil sie
unbequem zu messen sind, hieße, die Hälfte des Gesprächs auszulassen.

---

## 2.5 Warum diese Gewichtung

Die Verteilung folgt zwei Grundsätzen, die sich gegenseitig begrenzen.

> **Grundsatz 1 — Messbarkeit.** Ein Kriterium wiegt umso schwerer, je zuverlässiger es
> sich von außen feststellen lässt.
>
> **Grundsatz 2 — Wirkung auf die Kundengewinnung.** Ein Kriterium wiegt umso schwerer,
> je unmittelbarer es darüber entscheidet, ob aus einem Besucher eine Anfrage wird.

Beides zusammen erklärt jede einzelne Zahl in der Tabelle oben.

**Recht & Compliance — 20 Punkte.** Vollständig messbar und mit direktem finanziellem
Risiko verbunden. Das macht sie zur größten Einzelkategorie. Sie ist trotzdem nicht noch
größer, weil das Risiko nicht in Punkten abgebildet werden sollte: Ein fehlendes Impressum
ist kein Punktabzug, es ist ein Ausschlusskriterium. Dazu gleich mehr.

**Sicherheit & Datenschutz — 10 Punkte.** Technisch vollständig und eindeutig messbar,
aber für die Kundengewinnung nur mittelbar relevant. Ein Besucher bemerkt ein fehlendes
Sicherheitszertifikat, aber selten einen fehlenden Sicherheitsheader.

**Performance & Core Web Vitals — 15 Punkte.** Gut messbar über etablierte, von Google
veröffentlichte Messwerte, und direkt wirksam: Wer zu lange wartet, geht. Nicht mehr als
15 Punkte, weil die Messung von der Besucherzahl und der Messmethode abhängt und deshalb
schwankt.

**Barrierefreiheit — 10 Punkte.** Hier gilt Ehrlichkeit: Von außen lässt sich
Barrierefreiheit nur **teilweise** prüfen. Ob eine Seite mit einem Screenreader gut
bedienbar ist, entscheidet sich in Details, die eine automatisierte Prüfung nicht sieht.
Ein Standard, der dafür 20 Punkte vergibt, behauptet mehr Genauigkeit, als er hat. Die
zehn Punkte umfassen deshalb genau das, was zuverlässig feststellbar ist.

**SEO & Auffindbarkeit — 15 Punkte.** Fast vollständig messbar und mit direktem Bezug zur
Kundengewinnung. Bewusst nicht mehr, weil die wichtigsten Sichtbarkeitsfaktoren für lokale
Anbieter gar nicht auf der Website liegen: Ihr Unternehmensprofil bei Google, Ihre
Bewertungen und die Übereinstimmung Ihrer Kontaktdaten über verschiedene Verzeichnisse
hinweg wiegen schwerer als alles, was auf Ihrer eigenen Seite steht.

**Design & Gestaltung — 10 Punkte.** Nur als Einschätzung nach festem Raster bewertbar,
nie als Messung. Deshalb begrenzt auf zehn Punkte. Gleichzeitig entscheidet der visuelle
Eindruck in den ersten Sekunden mit darüber, ob überhaupt weitergelesen wird — deshalb
überhaupt bewertet.

**Conversion & Nutzerführung — 15 Punkte.** Teils messbar (ist die Telefonnummer
anklickbar? wie viele Pflichtfelder hat das Formular?), teils Einschätzung (ist in fünf
Sekunden klar, worum es geht?). Die hohe Gewichtung folgt aus Grundsatz 2: Dies ist die
Kategorie, die am unmittelbarsten darüber entscheidet, ob aus einem Besucher eine Anfrage
wird.

**Inhalt & Substanz — 5 Punkte.** Am wenigsten objektivierbar. Ob ein Text gut ist, lässt
sich diskutieren; ob eigene Leistungsseiten existieren, nicht. Nur die feststellbaren
Anteile werden bewertet, und das rechtfertigt keine größere Gewichtung.

---

## 2.6 Ausschlusskriterien: Warum Rechenkunst nicht alles heilt

Ein Punktesystem hat eine Schwäche: Man kann Schwächen mit Stärken ausgleichen. Eine
technisch hervorragende, schnelle, schön gestaltete Website ohne Impressum könnte
rechnerisch über 80 Punkte erreichen.

Das darf nicht sein. Ein Standard, der Konformität im Namen trägt, darf einer Website
keine gute Note geben, der eine gesetzliche Pflichtangabe vollständig fehlt.

Deshalb gibt es **Ausschlusskriterien**, die unabhängig von der Gesamtpunktzahl wirken:

| Fehlt oder ist unbrauchbar | Höchstens erreichbar |
|---|---|
| Impressum nicht erreichbar | Nicht konform |
| Datenschutzerklärung nicht erreichbar | Nicht konform |
| Kein gültiges Verschlüsselungszertifikat | Nicht konform |
| Tracking oder Schriftarten werden ohne Einwilligung geladen | Bronze |
| Cookies werden ohne Einwilligung gesetzt | Bronze |

Der Bericht nennt in diesem Fall immer den Grund, nie nur die Stufe:

> „Nicht konform (rechnerisch 78 Punkte). Die Einstufung ist begrenzt, weil keine
> Datenschutzerklärung erreichbar ist."

Das ist auch für Sie die nützlichere Information. Sie sagt Ihnen: Ihre Website ist im Kern
in Ordnung, aber ein einzelner Punkt blockiert alles. Diesen einen Punkt zu beheben, kostet
selten mehr als einen Nachmittag — und hebt Sie von der schlechtesten in eine der oberen
Stufen.

---

## 2.7 Die fünf Stufen

| Stufe | Punkte | Was das bedeutet |
|---|---|---|
| **Platin** | 95–100 | Auf dem aktuellen Stand in allen acht Kategorien. Kein Handlungsbedarf, nur Instandhaltung. |
| **Gold** | 85–94 | Rechtlich abgesichert, technisch schnell, gut geführt. Einzelne Feinheiten offen. |
| **Silber** | 70–84 | Solide Grundlage mit erkennbaren Lücken. Meist in Conversion, SEO oder Gestaltung. Wenige Tage Arbeit. |
| **Bronze** | 50–69 | Funktioniert, aber mehrere ernsthafte Schwächen. Handlungsbedarf innerhalb weniger Wochen. |
| **Nicht konform** | 0–49 | Grundlegende Mängel oder ein Ausschlusskriterium. Sofortiger Handlungsbedarf. |

Zwei Anmerkungen dazu.

**Die Schwellen liegen hoch.** Platin ab 95 Punkten bedeutet: Sie dürfen praktisch nichts
liegen lassen. Das ist Absicht. Eine Zertifizierung, die jeder Zweite erreicht, sagt
nichts aus.

**Die Stufe ist eine Zusammenfassung, keine Diagnose.** Zwei Betriebe mit je 76 Punkten
können völlig unterschiedliche Probleme haben. Für die Frage, was zu tun ist, zählt die
Verteilung über die acht Kategorien mehr als die Gesamtzahl. Wie stark dieser Unterschied
ausfällt, zeigt das Rechenbeispiel in Abschnitt 2.10.

---

## 2.8 Ihre Branchenklasse

Jetzt kommt der Teil, der diesen Standard von einer allgemeinen Checkliste unterscheidet.

Etwa ein Drittel der Bewertung — die Kategorien Conversion und Inhalt sowie Teile von SEO —
lässt sich nicht ohne einen Maßstab beurteilen. „Ist das Angebot klar?" ist keine Frage,
die man ohne Wissen über das Geschäft beantworten kann. Für einen Dachdecker gehört ein
Preisrahmen zu einem klaren Angebot. Für eine Steuerkanzlei kann die Nennung von Preisen
berufsrechtlich problematisch sein — sie wäre also nicht besser, sondern schlechter
beraten, wenn sie einen angäbe.

Ein Standard, der beide gegen denselben Maßstab misst, produziert Unsinn. Deshalb bestimmt
der Homepage Standard vor der Bewertung eine **Branchenklasse**.

### Die sechs Klassen

| Klasse | Bezeichnung | Erkennungsmerkmal | Typische Vertreter |
|---|---|---|---|
| **K1** | Lokaler Leistungsbetrieb | Die Leistung wird beim Kunden oder vor Ort erbracht, es gibt ein Einzugsgebiet | Handwerk aller Gewerke, Kfz-Betriebe, Garten- und Landschaftsbau, Gebäudereinigung, Pflegedienste |
| **K2** | Lokaler Beratungs- und Gesundheitsdienstleister | Termin statt Auftrag, die Qualifikation ist das Kaufargument, oft berufsrechtlich reglementiert | Arzt-, Zahnarzt- und Physiotherapiepraxen, Rechtsanwälte, Steuerberater, Architekten |
| **K3** | Lokaler Publikumsbetrieb | Der Kunde kommt zu Ihnen, Öffnungszeiten und Sortiment entscheiden | Gastronomie, Einzelhandel, Friseur, Fitnessstudio, Hotel |
| **K4** | Überregionaler Anbieter | Kein Einzugsgebiet, die Leistung wird ortsunabhängig erbracht | Agenturen, Unternehmensberatungen, Softwareanbieter, B2B-Zulieferer |
| **K5** | Onlineverkauf | Der Vertragsschluss oder die Bezahlung findet auf der Website statt | Onlineshops, digitale Produkte, kostenpflichtige Buchungen |
| **K6** | Keine Betriebsseite | Kein Unternehmen, das über diese Seite Kunden gewinnt | Vereine, Parteien, Kandidatenauftritte, Blogs, private Seiten |

**Kombinationen sind möglich.** Ein Dachdecker mit Ersatzteilshop ist K1 und K5. Ein Hotel
mit Onlinebuchung ist K3 und K5. In diesem Fall gelten die Anforderungen beider Klassen.

### So bestimmen Sie Ihre Klasse

Beantworten Sie die Fragen der Reihe nach und hören Sie beim ersten Ja auf:

1. **Gewinnen Sie über diese Website überhaupt Kunden für eine Leistung?**
   Nein → **K6**. Die Kategorien Conversion und Inhalt werden bei Ihnen nicht bewertet;
   Recht, Sicherheit, Technik, Barrierefreiheit, SEO und Gestaltung schon.
2. **Können Kunden auf Ihrer Website kaufen oder verbindlich buchen und bezahlen?**
   Ja → **K5** (zusätzlich zu einer der folgenden Klassen, sofern zutreffend).
3. **Ist Ihre Leistung an ein Einzugsgebiet gebunden?**
   Nein → **K4**.
4. **Kommt der Kunde zu Ihnen in Ihre Räume, und entscheiden Öffnungszeiten und
   Sortiment?** Ja → **K3**.
5. **Ist Ihre Berufsqualifikation das zentrale Kaufargument und Ihr Beruf
   berufsrechtlich reglementiert?** Ja → **K2**.
6. Sonst → **K1**.

> **Tragen Sie Ihre Klasse hier ein: ________**
>
> Sie brauchen sie in den Kapiteln 7, 9 und 10 sowie im Selbsttest in Kapitel 11.

### Was die Klasse verändert — und was nicht

**Unverändert für alle Klassen:** Recht, Sicherheit, Performance, Barrierefreiheit und
Gestaltung. Ein Impressum ist ein Impressum. Eine langsame Seite ist langsam. Ein zu
geringer Farbkontrast ist zu gering. Wer dahintersteht, ändert daran nichts.

**Klassenabhängig:** Was als klares Angebot, als passendes Handlungsziel, als taugliches
Vertrauenssignal und als sinnvolle Seitenstruktur gilt.

Drei Beispiele, damit der Unterschied greifbar wird:

| Kriterium | K1 Dachdecker | K2 Steuerkanzlei | K4 IT-Beratung |
|---|---|---|---|
| Erwartetes Handlungsziel | Angebot anfordern, Rückruf, Notdienst | Erstgespräch vereinbaren | Demo oder Erstgespräch |
| Erwartetes Vertrauenssignal | Meisterbrief, Innung, Objektfotos | Kammerzugehörigkeit, Fachkunde, Team | Referenzkunden, Fallstudien mit Zahlen |
| Preisrahmen im Angebot | erwartet | **nicht erwartet** | Projektgrößenordnung erwartet |
| Ortsangabe im Seitentitel | erwartet | erwartet | **nicht erwartet** |

**Nicht erwartet heißt: Das Fehlen kostet keine Punkte.** Eine Kanzlei ohne Preisangabe
verliert nichts. Eine überregionale IT-Beratung ohne Ortsangabe im Seitentitel verliert
nichts. Das Kriterium „Lokale Signale" wird bei ihr gar nicht erst bewertet und fällt aus
der Rechnung — genau wie ein Kriterium, das nicht gemessen werden konnte.

Das ist keine Nachsicht, sondern Genauigkeit. Ein Maßstab, der nicht passt, misst nichts.

---

## 2.9 Wie ein einzelnes Kriterium bewertet wird

Jedes der 38 Kriterien hat eine Höchstpunktzahl zwischen 1 und 6. Die Vergabe erfolgt
gestuft, nicht als Alles-oder-nichts.

Ein Beispiel am Kriterium „Impressum" mit 6 Punkten:

| Punkte | Bedingung |
|---|---|
| 6 | Von jeder geprüften Seite in einem Klick erreichbar und alle Pflichtangaben vorhanden |
| 4–5 | Alle Angaben vorhanden, aber nicht überall verlinkt, oder eine Angabe fehlt |
| 2–3 | Erreichbar, aber zwei oder mehr Pflichtangaben fehlen |
| 1 | Nur über Umwege auffindbar |
| 0 | Nicht auffindbar → **Ausschlusskriterium** |

Die genauen Abstufungen je Kriterium finden Sie in den Kapiteln 3 bis 10, jeweils im
Abschnitt „So wird bewertet".

**Für Ihren Selbsttest:** Sind Sie unsicher zwischen zwei Stufen, nehmen Sie die
niedrigere. Sie führen den Test nicht durch, um sich ein gutes Gefühl zu verschaffen,
sondern um zu wissen, was zu tun ist.

---

## 2.10 Zwei Berichte im Vergleich

Nichts erklärt das System besser als zwei durchgerechnete Fälle. Beide erreichen dieselbe
Punktzahl — und haben nichts miteinander gemein.

### Fall A — Elektrobetrieb, 14 Mitarbeiter, Klasse K1

Alle 38 Kriterien konnten geprüft werden. Anwendbares Maximum: 100 Punkte.

| Kategorie | Erreicht | Möglich |
|---|---|---|
| Recht & Compliance | 18 | 20 |
| Sicherheit & Datenschutz | 8 | 10 |
| Performance | 8 | 15 |
| Barrierefreiheit | 6 | 10 |
| SEO & Auffindbarkeit | 11 | 15 |
| Design & Gestaltung | 7 | 10 |
| Conversion & Nutzerführung | 13 | 15 |
| Inhalt & Substanz | 5 | 5 |
| **Summe** | **76** | **100** |

**Ergebnis: 76 Punkte — Homepage Standard Silber.**

Was der Bericht sagt: Rechtlich und inhaltlich sauber, Kundenführung stark. Die Website
ist langsam, und die Barrierefreiheit ist schwach. Beides hängt zusammen — unkomprimierte
Fotos von der Baustelle sind der häufigste Grund für lange Ladezeiten, und derselbe
Nachlässigkeit fallen meist auch die Alternativtexte zum Opfer.

Was zu tun ist: Bilder optimieren und mit Alternativtexten versehen. Ein Arbeitstag. Das
bringt geschätzt zehn bis zwölf Punkte und damit Gold.

### Fall B — Steuerkanzlei, 6 Mitarbeiter, Klasse K2

Die Ladezeitmessung konnte nicht durchgeführt werden — die Kanzlei-Website blockiert
automatisierte Zugriffe. Die 15 Punkte der Kategorie Performance fallen deshalb aus der
Rechnung. Anwendbares Maximum: 85 Punkte.

| Kategorie | Erreicht | Möglich |
|---|---|---|
| Recht & Compliance | 14 | 20 |
| Sicherheit & Datenschutz | 6 | 10 |
| Performance | — | *nicht erhoben* |
| Barrierefreiheit | 7 | 10 |
| SEO & Auffindbarkeit | 12 | 15 |
| Design & Gestaltung | 9 | 10 |
| Conversion & Nutzerführung | 12 | 15 |
| Inhalt & Substanz | 5 | 5 |
| **Summe** | **65** | **85** |

Umgerechnet: 65 von 85 möglichen Punkten entsprechen **76 Punkten** auf der 100er-Skala.

Rechnerisch also dasselbe Ergebnis wie Fall A. Aber:

> **Ergebnis: 50 Punkte — Homepage Standard Bronze (rechnerisch 76).**
> Die Einstufung ist begrenzt, weil Schriftarten ohne Einwilligung von einem fremden
> Server geladen werden.

Was der Bericht sagt: Gestalterisch die bessere der beiden Websites. Aber die eingebundene
Schriftart löst bei jedem Seitenaufruf eine Datenübertragung aus, bevor der Besucher
irgendetwas zugestimmt hat. Genau dafür sind Websites in Deutschland abgemahnt worden.

Was zu tun ist: Die Schriftart lokal einbinden. Zwei Stunden Arbeit für einen Fachbetrieb.
Danach steht die Kanzlei bei 76 Punkten und Silber — mit einer einzigen Änderung.

### Was Sie daraus mitnehmen

**Erstens:** Dieselbe Punktzahl bedeutet nicht dasselbe Problem. Fall A braucht einen
Arbeitstag an den Bildern, Fall B zwei Stunden an einer einzigen Zeile Code.

**Zweitens:** Ein Ausschlusskriterium wiegt schwerer als jede Punktzahl. Die Kanzlei ist
die gestalterisch bessere Website und steht trotzdem zwei Stufen tiefer.

**Drittens:** Nicht erhobene Kriterien schaden Ihnen nicht. Die Kanzlei wird nicht dafür
bestraft, dass ihre Ladezeit unbekannt ist. Sie erfährt nur, dass dieser Teil ungeprüft
blieb — und dass sie ihn selbst nachmessen sollte.

---

## 2.11 Was der Standard bewusst nicht bewertet

Ein Bewertungssystem ist auch durch das definiert, was es weglässt.

**Geschmack.** Design wird bewertet — aber anhand von Aktualität, Lesbarkeit,
Farbkonsistenz und Bildqualität, nicht danach, ob eine Gestaltung gefällt. Ob Ihnen Blau
lieber ist als Grün, gehört nicht in einen Standard.

**Social Media.** Ein gepflegtes Profil kann für die Nachwuchsgewinnung wertvoll sein. Es
ist aber keine Eigenschaft Ihrer Website.

**Verweise von anderen Websites.** Von außen nur unzuverlässig feststellbar und stark
anfällig für Scheinoptimierung.

**Ob Sie Besucherzahlen messen.** Ob auf Ihrer Seite ein Statistikwerkzeug läuft, wird
festgestellt und im Befund ausgewiesen — aber nicht bewertet. Eine Website ohne
Besuchermessung ist für ihre Besucher nicht schlechter. Für Sie als Betreiber ist sie
allerdings blind, und darauf weist der Bericht hin.

**Das Preis-Leistungs-Verhältnis Ihres Dienstleisters.** Der Standard bewertet das
Ergebnis, nicht den Weg dorthin. Eine Website für 300 Euro mit 88 Punkten ist besser als
eine für 15.000 Euro mit 61 Punkten. Was Sie daraus schließen, ist Ihre Entscheidung.

---

## 2.12 Zwei Befunde außerhalb der Wertung

Neben den 100 Punkten liefert eine vollständige Prüfung zwei weitere Ergebnisse, die
bewusst nicht in die Bewertung einfließen.

**Der Infrastruktur-Befund** stellt fest, womit Ihre Website gebaut ist und wo sie liegt:
verwendetes System, Hosting-Anbieter, Auslieferungsnetzwerk, Übertragungsprotokoll,
Domain-Alter, Antwortzeit und eingesetzte Besuchermessung. Diese Angaben fließen nicht in
die Punktzahl ein, weil Sie sie meist nicht ohne Anbieterwechsel beeinflussen können. Sie
sind trotzdem wertvoll: Wer wissen will, was eine Überarbeitung kostet, muss wissen, worauf
er aufsetzt.

**Der GEO-Wert** (0 bis 10) beschreibt, wie gut Ihre Website für KI-gestützte Suchsysteme
aufbereitet ist — also für Systeme, die keine Linkliste ausgeben, sondern eine Antwort
formulieren. Er steht bewusst außerhalb der 100 Punkte, weil sich dieses Feld derzeit zu
schnell verändert. Ein Kriterium, dessen Anforderungen sich innerhalb eines Jahres wandeln
können, gehört nicht in einen Standard, der über Jahre vergleichbar bleiben soll — und erst
recht nicht in ein gedrucktes Buch. Kapitel 14 geht darauf ein.

---

## 2.13 Vier verbreitete Missverständnisse

**„Meine Website ist neu, also ist sie in Ordnung."**
Neu heißt: zeitgemäß gestaltet. Über Recht, Ladezeit und Einwilligungen sagt es nichts.
Im Gegenteil — moderne Baukastensysteme binden häufig Schriftarten, Karten und
Statistikwerkzeuge von fremden Servern ein, und zwar ohne zu fragen. Neubauten fallen bei
den Einwilligungskriterien überdurchschnittlich oft durch. Ein zehn Jahre alter,
handgebauter Auftritt ohne jedes Fremdelement ist an dieser Stelle im Vorteil.

**„100 Punkte erreicht ohnehin niemand."**
Richtig ist: Platin ab 95 Punkten ist selten. Das ist auch nicht das Ziel. Für einen
Betrieb, der seine Website nicht täglich pflegt, ist **Gold die sinnvolle Zielmarke** — 85
Punkte bedeuten, dass nichts Wesentliches fehlt. Der Sprung von Gold auf Platin kostet oft
mehr als die gesamte Strecke davor und lohnt sich nur, wenn die Website ein zentraler
Vertriebskanal ist.

**„Mein Dienstleister sagt, das sei alles nicht nötig."**
Das kann stimmen. Fragen Sie ihn dann nicht nach seiner Meinung, sondern nach einer Zahl:
*Auf wie viele Punkte bringen Sie meine Website, und welche Kriterien lassen Sie bewusst
weg?* Wer sein Handwerk beherrscht, kann das beantworten. Wer ausweicht, hat die Frage zum
ersten Mal gehört — und das ist die eigentliche Auskunft.

**„Ein guter Wert bringt mir mehr Kunden."**
Nein. Er entfernt Hindernisse. Zwischen einer Website mit 45 und einer mit 85 Punkten
liegen erhebliche Unterschiede darin, wie viele Interessenten überhaupt bis zum
Kontaktformular kommen. Ob sie dann anfragen, hängt von Ihrem Angebot ab, nicht von Ihrer
Punktzahl. Der Standard sorgt dafür, dass Ihr Angebot gesehen wird. Überzeugen muss es
selbst.

---

## 2.14 Wie oft sollten Sie prüfen?

| Anlass | Umfang |
|---|---|
| Einmal jährlich | vollständig, alle 38 Kriterien |
| Nach jeder Änderung an der Website | betroffene Kategorien |
| Nach Wechsel des Dienstleisters oder Hosters | vollständig |
| Bei Gesetzesänderungen | Kategorien 1 und 2 |
| Bei Überschreiten von zehn Beschäftigten | Kategorien 1 und 4 |
| Wenn sich Ihr Geschäftsmodell ändert | Branchenklasse neu bestimmen, dann vollständig |

Die jährliche Prüfung ist der wichtigste Punkt, aus einem oft übersehenen Grund: **Eine
Website verschlechtert sich, ohne dass jemand etwas tut.** Ein Zertifikat läuft ab. Eine
eingebundene Landkarte ändert ihre Bedingungen. Eine Schriftart wird plötzlich von einem
fremden Server geladen. Ein Gesetz tritt in Kraft. Sie haben nichts geändert — und Ihre
Punktzahl ist gefallen.

---

## 2.15 Die Grenzen dieses Verfahrens

Vier Einschränkungen, die Sie kennen sollten.

**Der Standard prüft, was von außen sichtbar ist.** Er kann nicht feststellen, ob Ihr
Vertrag mit dem Hoster existiert, ob Ihr Verarbeitungsverzeichnis geführt wird oder ob Ihre
Datenschutzerklärung inhaltlich zu Ihren tatsächlichen Abläufen passt. Er prüft, ob die
Erklärung da ist und ob die erkennbare Technik ihr widerspricht.

**Der Standard ersetzt keine Rechtsberatung.** Er stellt fest, dass eine Pflichtangabe
fehlt. Welche Angaben in Ihrem konkreten Fall geschuldet sind, hängt von Rechtsform,
Tätigkeit und Kammerzugehörigkeit ab.

**Ein Teil der Bewertung bleibt Einschätzung.** Gestaltung und Verständlichkeit lassen
sich nicht messen. Der Standard macht das transparent, statt es zu verschleiern — aber
transparent bleibt es eine Einschätzung, über die man streiten kann. Wo Sie anderer
Meinung sind, sollten Sie es sein.

**Eine hohe Punktzahl garantiert keinen geschäftlichen Erfolg.** Sie garantiert, dass Ihre
Website die bekannten Fehler nicht macht. Ob daraus Aufträge werden, hängt von Dingen ab,
die dieses Buch nicht behandelt: Ihrem Angebot, Ihrem Preis, Ihrer Erreichbarkeit, Ihrem
Ruf. Der Standard beseitigt Hindernisse. Er schafft keine Nachfrage.

Mit dieser Einordnung können wir in die Einzelkriterien gehen. Wir beginnen dort, wo am
meisten auf dem Spiel steht.

---

> ### Das Wichtigste aus diesem Kapitel
>
> - **38 Kriterien in acht Kategorien**, zusammen 100 Punkte. Geprüft werden sechs bis
>   sieben Seiten, darunter Impressum und Datenschutzerklärung als eigene Seiten.
> - Jedes Kriterium ist gekennzeichnet als **gemessen, abgeleitet, Einschätzung** oder
>   **nicht erhoben**. Was nicht geprüft werden konnte, wird nicht mit null bewertet,
>   sondern fällt aus der Rechnung.
> - Die Gewichtung folgt **Messbarkeit** und **Wirkung auf die Kundengewinnung**.
> - **Ausschlusskriterien** wirken unabhängig von der Punktzahl: ohne Impressum,
>   Datenschutzerklärung oder gültige Verschlüsselung keine gute Stufe.
> - Fünf Stufen mit hohen Schwellen: **Platin ab 95, Gold ab 85, Silber ab 70,
>   Bronze ab 50.** Sinnvolle Zielmarke für die meisten Betriebe: **Gold.**
> - Ihre **Branchenklasse (K1–K6)** bestimmt den Maßstab bei Conversion, Inhalt und
>   Teilen von SEO. Was in Ihrer Klasse nicht erwartet wird, kostet keine Punkte.
> - Prüfen Sie **einmal jährlich vollständig** — Websites verschlechtern sich auch ohne
>   Ihr Zutun.

---

## Redaktionelle Anmerkungen (nicht drucken)

**Abhängigkeit für die Kapitel 3 bis 10:** Die Punktabstufungen je Kriterium müssen aus
`services/audit_criteria.py` übernommen werden. Die in 2.9 gezeigte Impressum-Staffelung
ist als Beispiel plausibel gesetzt und mit dem Code abzugleichen, bevor Kapitel 3
geschrieben wird.

**Abhängigkeit für 2.7:** Die Stufenschwellen 95/85/70/50 stammen aus dem
Anforderungskatalog. Frontend-Komponenten tragen im Projektwissen noch 85/70/50/30. Vor
Drucklegung muss feststehen, welche Werte produktiv gelten.

**Noch nicht gebaut:** Das Branchenklassenmodell (2.8) ist spezifiziert, aber in der
Software noch nicht umgesetzt. Bis dahin beschreibt das Kapitel einen Soll-Zustand. Das
Buch darf erst erscheinen, wenn das Audit die Klassen tatsächlich anwendet.

**Zu prüfen in 2.3:** Der beschriebene Prüfumfang (Startseite, Impressum, Datenschutz,
Kontakt, bis zu drei Leistungsseiten; Screenshot Desktop und Mobil; Messung mobil und
Desktop) entspricht dem Soll aus dem Anforderungskatalog § 3.5. Ob der Kontaktseiten-Abruf
und der Desktop-Screenshot tatsächlich implementiert sind, ist gegen `audit_runner.py`
abzugleichen.

**Zu prüfen in 2.10:** Fall A und Fall B sind konstruiert, aber realistisch gehalten. Nach
den ersten Läufen gegen echte Websites sollten sie durch **echte, anonymisierte**
Ergebnisse ersetzt werden. Das ist der stärkste Abschnitt des Kapitels — er sollte auf
Daten stehen, nicht auf Annahmen.

**Zu belegen:** In 2.5 steht die Aussage, dass Unternehmensprofil, Bewertungen und
Verzeichniskonsistenz für lokale Sichtbarkeit schwerer wiegen als Seiteninhalte.

**Abbildungen (6 Stück):**
1. Balkendiagramm der acht Kategorien mit Punktzahlen
2. Die vier Quellen-Kennzeichnungen mit je einem Beispielkriterium
3. Rechenbeispiel Normierung: 66 von 92 geprüften Punkten → 72
4. Entscheidungsbaum zur Branchenklasse (aus 2.8 als Flussdiagramm)
5. Die fünf Stufen als Skala, mit eingezeichneter Wirkung der Ausschlusskriterien
6. Fall A und Fall B als zwei Netzdiagramme nebeneinander, beide 76 Punkte
