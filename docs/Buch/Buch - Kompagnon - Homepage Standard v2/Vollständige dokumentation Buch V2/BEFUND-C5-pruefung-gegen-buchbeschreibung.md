# BEFUND C5 — Wie die Prüfung läuft, und wie das Buch sie beschreibt

**Erhoben am 25.08.2026 am laufenden Code**, nicht aus der Erinnerung. Geprüft
wurden `routers/audit.py`, `services/audit_runner.py`,
`services/audit_aggregat.py`, `services/audit_ai.py`,
`services/audit_scoring.py`.

**Warum dieser Befund.** Kapitel 2.7 legt einen Interessenkonflikt offen und
verspricht dem Leser dafür Transparenz über das Verfahren. Kapitel 3.4
verspricht ihm, er könne einer Einschätzung **widersprechen**. Beide
Versprechen hängen daran, dass die Beschreibung im Buch das Verfahren trifft.
An sechs Stellen tut sie das nicht.

---

## Teil 1 — Was tatsächlich geschieht

Ein vollständiger Lauf hat fünf Abschnitte. Die Reihenfolge ist nicht
beliebig: Der Maßstab hängt an der Branchenklasse, die Klasse an der
Erkennung, und beide stehen vor der Bewertung.

### 1. Abruf der Startseite

Ein Aufruf mit eigener Kennung. Antwortet die Seite nicht, endet der Lauf hier
mit „nicht erreichbar" — es entsteht **kein** Ergebnis. Weiterleitungen werden
verfolgt; gemessen wird die Adresse, bei der der Aufruf ankommt.

### 2. Erhebung — acht Stränge gleichzeitig, Zeitgrenze 200 Sekunden

| Strang | Womit | Umfang |
|---|---|---|
| Messwerte Ladezeit und Barrierefreiheit | fremder Messdienst | Startseite |
| Seitenprüfung (Titel, Überschriften, Auszeichnungen, robots.txt, Sitemap) | eigener Scanner | Startseite |
| Hosting- und Technikerkennung | eigener Scanner | Startseite |
| Verweisprüfung | eigener Scanner | Startseite |
| Rechtsseiten (Impressum, Datenschutz, Barrierefreiheit) | eigener Scanner | Domain |
| Weiterleitung auf https | eigener Scanner | Domain |
| Verschlüsselungszertifikat | eigener Scanner | Domain |
| **Unterseiten** | eigener Scanner | **bis zu 25 Seiten**, Zeitgrenze 120 s |

Parallel dazu entsteht **ein** Bildschirmabzug der Startseite über einen
fremden Dienst.

### 3. Zusammenfassung über die Seiten

Die Befunde aller geprüften Seiten werden zu einem Befund je Kriterium
verdichtet. **Vier Regeln**, je nachdem, was das Kriterium behauptet:

| Regel | Bedeutung | Betrifft |
|---|---|---|
| irgendwo genügt | eine Telefonnummer irgendwo ist eine Telefonnummer | Kontaktwege, Vertrauenssignale, fremde Dienste |
| aufsummieren | zwei Formulare auf zwei Seiten sind zwei Formulare | Formulare, Bilder, **Wörter** |
| überall oder gar nicht | *jedes* Formular braucht das Einwilligungsfeld | Einwilligung am Formular |
| vereinigen | dieselbe Leistung dreifach verlinkt ist eine Leistung | Leistungsseiten, Zertifikate |

Die dritte Regel ist die einzige, bei der eine **zusätzliche** Seite das
Ergebnis verschlechtern kann. Das ist beabsichtigt.

### 4. Einordnung und Einschätzung — zwei Modellaufrufe

**Erst die Einordnung.** Ein kleines Sprachmodell liest den Seitentext und
nennt das Gewerk und die Frage „steht dahinter ein Betrieb". Daraus folgt die
Branchenklasse über eine feste Zuordnungstabelle.

**Dann die Bewertung.** Ein großes Modell bekommt den Bildschirmabzug, die
gemessenen Signale und den Seitentext — und den Maßstab **seiner Klasse**.
Bewertet werden ausschließlich die sechs eingeschätzten Kriterien.

> **Schlägt die Einordnung fehl, findet gar keine Einschätzung statt.** Alle
> sechs Kriterien gelten dann als *nicht erhoben*. Das ist gewollt: Ohne
> Klasse bliebe nur ein fester Maßstab für alle — der Zustand, den die Fassung
> 2026.2 gerade abgeschafft hat.

### 5. Bewertung

Rein rechnerisch, ohne Netzzugriff: Aus den Fakten und der Einschätzung werden
Punkte, daraus der auf 0–100 normierte Wert, daraus die Stufe — gedeckelt
durch die Ausschlusskriterien.

---

## Teil 2 — Die sechs Abweichungen

### C5-1 🔴 Ein Bildschirmabzug, nicht zwei

**Buch (10.2):** „Ein Sprachmodell bekommt einen Bildschirmabzug Ihrer
Startseite — **mobil und am Rechner** — sowie den Seitentext."

**Code:** Es wird **genau ein** Abzug erzeugt und **einer** übergeben. Eine
zweite Ansicht gibt es nicht.

**Folge:** Das Buch verspricht eine Grundlage, die die Bewertung nicht hat.
Ein Leser, dessen Seite am Rechner gut und auf dem Telefon schlecht aussieht,
zieht daraus einen falschen Schluss.

**Zu tun:** entweder den Satz kürzen — oder die zweite Ansicht bauen. Für das
Buch ist die Kürzung der ehrliche Weg; die zweite Ansicht ist eine
Produktentscheidung mit Kosten je Lauf.

### C5-2 🔴 Der Umfang der Prüfung steht nirgends im Buch

**Buch:** spricht durchgehend von „Ihrer Website" und beschreibt in 3.1 die
Grenze zwischen außen und innen — aber nirgends, **wie viele Seiten** geprüft
werden.

**Code:** bis zu **25 Seiten**. Bei Zeitüberschreitung nur die Startseite; der
Bericht weist beides aus (geprüfte und gefundene Seiten).

**Folge:** Der Kunde liest im Bericht eine Zahl, die das Buch nicht erklärt.
Und der Selbsttest in Kapitel 13 misst etwas anderes als die Software —
darunter **E2**, wo der Leser die Wörter der Startseite zählt und die Software
über alle geprüften Seiten summiert.

**Zu tun:** Absatz in 3.1 ergänzen, 13.1 präzisieren, Tabelle in 2.8 um diese
Zeile erweitern.

### C5-3 🔴 E2 misst zwei Dinge auf zwei Grundlagen

**Code:** Das Kriterium besteht aus zwei Teilprüfungen. Die erste
(Überschriften) stammt aus der **Startseite**, die zweite (mindestens 300
Wörter) aus der **Summe über alle geprüften Seiten**.

**Folge:** Der zweite Punkt ist bei einer mehrseitigen Website praktisch immer
erfüllt. Für den Leser des Selbsttests ist er es nicht, weil er die Startseite
zählt. **Dieselbe Website bekommt dadurch im Selbsttest und in der
automatischen Prüfung systematisch verschiedene Werte.**

**Zu tun:** Das ist keine Buchfrage, sondern eine Maßstabsfrage — sie gehört
in `docs/Audit/fassung-2027-1-offene-massstabsfragen.md`. Bis zur Entscheidung
muss das Buch die Grundlage benennen, statt sie zu verschweigen.

### C5-4 🟡 Was das Modell bekommt, ist mehr als „eine Beschreibung"

**Buch (10.2):** „Jedes Kriterium mit seiner Spanne und einer Beschreibung."

**Code:** Seit dem 25.08.2026 (S8.2) bekommt es je Kriterium ein
**ausformuliertes Punkterubric** — was drei Punkte von zwei unterscheidet,
welche Merkmale zählen, und ausdrücklich, was **nicht** Teil des Kriteriums
ist.

**Folge:** Das Buch untertreibt. Der Vorbehalt in 10.2, die Merkmalsliste sei
„meine Zusammenstellung, nicht aus dem Code extrahiert", ist seit dem 25.08.
hinfällig — die Rubrics stehen im Katalog und erscheinen in Anhang B.

### C5-5 🟡 Wiederholbarkeit ist versprochen, aber nur zur Hälfte belegt

**Buch (2.5 und 3.1):** nennt Wiederholbarkeit ohne Einschränkung — „Zwei
Prüfungen derselben Seite ergeben dasselbe Ergebnis."

**Code:** Für die 33 gemessenen und abgeleiteten Kriterien stimmt das
bauartbedingt. Für die **sechs eingeschätzten** ist es nie gemessen worden;
die Streuung über mehrere Läufe steht als `S8.3` aus (Lagebild L-112).

**Zu tun:** Den Satz auf die gemessenen Kriterien beziehen und für die
eingeschätzten sagen, was tatsächlich gilt: fester schriftlicher Maßstab seit
dem 25.08., Streuung noch nicht erhoben. **Diese Formulierung ist stärker als
die jetzige**, weil sie hält, was sie sagt.

### C5-6 🟡 Der Bildschirmabzug entsteht bei einem fremden Dienst

**Code:** Der Abzug wird über einen externen Anbieter erzeugt; fällt er aus,
läuft die Bewertung ohne Bild weiter.

**Buch:** erwähnt es nicht — während Kapitel 6 dem Leser erklärt, dass jeder
fremde Dienst die Adresse des Besuchers erfährt.

**Zu tun:** eine Zeile in 16, und der Punkt gehört auf die Liste für den
Anwaltstermin (B2). Übermittelt wird die **geprüfte Adresse**, nicht die eines
Besuchers — gesagt gehört es trotzdem.

---

## Teil 3 — Was stimmt

Damit beim Überarbeiten nichts angefasst wird, was trägt:

| Stelle | Aussage | Befund |
|---|---|---|
| 2.5 | vier Gründe für die Messung von außen | trifft zu |
| 3.1 | kein Zugang, kein Passwort, keine Erlaubnis | trifft zu |
| 3.5 | „nicht erhoben" fällt aus Zähler **und** Nenner | trifft zu, im Code nachgeprüft |
| 3.5 | Unterschied „nicht erhoben" / „gilt hier nicht" | trifft zu |
| 4.7 | Klasse steht vor der Punktzahl, Herkunft wird genannt | trifft zu |
| 8.2 | automatisierte Prüfung sieht Alternativtexte, nicht ihre Güte | trifft zu |
| 10.2 | Sicht der Kundschaft, nicht die eines Gestalters | trifft zu, steht so im Prompt |
| 10.2 | Anweisung, streng zu sein; volle Punktzahl nur bei Belegen | trifft zu, wörtlich |
| 16 | Infrastruktur ohne Punkte, nur zur Information | trifft zu |

---

## Stand der Bearbeitung — 25.08.2026

| | Befund | Zustand |
|---|---|---|
| **C5-1** | Bildschirmabzug: einer statt zwei | ✅ 10.2 berichtigt |
| **C5-4** | ausformulierter Maßstab statt „Beschreibung" | ✅ 10.2 erweitert, Anhang B genannt |
| **C5-2** | Umfang der Prüfung | ✅ 3.1 (neuer Abschnitt mit der Trennung „alle Seiten / nur Startseite"), 2.8 (Zeile *Umfang*), 13.1 (vier betroffene Prüfungen benannt) |
| **C5-5** | Wiederholbarkeit | ✅ 3.1 auf die 33 gemessenen Kriterien bezogen; für die sechs eingeschätzten steht, dass die Streuung nicht gemessen ist |
| **C5-6** | fremde Dienste der Prüfung | ✅ neuer Abschnitt in 16; anwaltlich zu bestätigen als **B2.21** |
| **C5-3** | E2 auf zwei Grundlagen | ⏸ **offen** — Maßstabsfrage, Abschnitt 7 in `docs/Audit/fassung-2027-1-offene-massstabsfragen.md` |

**C5-3 ist der einzige, der vor dem Druck eine Entscheidung braucht.** Die
anderen fünf waren Schreibarbeit; dieser verändert die Punkte realer Seiten.
Solange er offen ist, sagt das Buch dem Leser die Grundlage — das ist Weg C
der drei dort beschriebenen Wege und ausdrücklich eine Zwischenlösung.

**Was bewusst *nicht* geändert wurde:** die neun Aussagen in Teil 3. Wer beim
Lektorat kürzt, kürzt bitte nicht dort.
