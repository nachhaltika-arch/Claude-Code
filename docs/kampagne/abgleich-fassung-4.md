# Abgleich: Fassung 4 gegen Lagebild und Vertriebsplan

**Gegenstand:** „Meta-Kampagne Websprint Audit · Entscheidungsvorlage, Fassung 4",
Stand 14.09.2026 (Dateiname `Fragen zu Format und Zielgruppe.pdf`), Abschnitt 11
„Offene Punkte" — fünfzehn Einträge.

**Verglichen mit:** dem Aktionsplan in `docs/Websprint-Vertriebsplan.html`
(Stand 15.09., 71 Punkte) und der Lückenliste in `docs/soll-ist-analyse.md`
(Stand 16.09., 195 Lücken, davon 30 offen).

**Gemessen am 17.09.2026** an der ausgelieferten Seite, an der Repo-Datei und im
Browser. Was nicht gemessen ist, steht als *nicht erhoben* — nicht als Null.

---

## Der Rahmen stimmt nicht mehr

Fassung 4 ist eine **Vorstart**-Vorlage: Abschnitt 11 teilt in „blockiert den
Start" und „blockiert nicht", die Schaltanleitung endet mit „Veröffentlicht wird
von David".

Die Kampagne **läuft seit dem 14.09.** — `docs/kampagne/2026-09-15.md` wertet
Tag 1 und 2 aus. Damit ist kein einziger der acht Startblocker mehr ein
Startblocker. Sie sind **Punkte, an denen jeden Tag Geld vorbeiläuft**.

Und der Befund, den Fassung 4 noch nicht kennen konnte, hebt die Fragestellung
des Dokuments auf:

| gemessen am 15.09. | Fassung 4 rechnet mit |
|---|---|
| **69 echte Besucher** | 660–1.160 über die Laufzeit — die Größenordnung passt |
| **0 abgeschickte Analysen** (`POST /api/widget/audit`) | Abschlussquote 5–10 % |
| Klickrate **7,71 %** gesamt, **5,31 %** außerhalb Audience Network | 0,8–1,4 % |
| Einwilligungsquote **0,06** (GA4 4 ÷ 69, untere Schranke) | 60–75 % |

Die Anzeige ist also nicht das Problem — sie liefert die fünffache Klickrate der
Annahme. Fassung 4 optimiert fünf Hebel an der Stelle des Trichters, die als
einzige nachweislich funktioniert.

---

## Die fünfzehn Punkte

**B** = in Fassung 4 als Startblocker geführt.

| # | Fassung 4 | Vertriebsplan | Lagebild | Stand am 17.09. |
|---|---|---|---|---|
| **2** B | Ereignis „Analyse gestartet" einbauen | P0-03 | L-188 | **erledigt und live.** Die ausgelieferte Seite trägt `kpg-analyse-begonnen`, `fbq('track','InitiateCheckout')` und `gtag('event','begin_checkout')` — je zwei Treffer, heute an der Live-Antwort gemessen. |
| **3** B | Testdurchlauf, drei Ereignisse je genau einmal | P0-08 | — | offen. Hängt an Punkt 14 (Upload), weil sonst ohne Herkunft getestet wird. |
| **4** B | Domain verifizieren, aggregierte Ereignismessung | P0-07 | — | offen, nur David (Business Manager 128351871884970). |
| **7** B | Anzeigen-URLs mit `#analyse`, Ankersprung geprüft | P0-04 | L-195 | **Ankersprung heute gemessen — er hält.** Siehe unten. Ob die geschaltete Anzeigen-URL den Anker trägt: nicht erhoben, liegt im Ads Manager. |
| **8** B | Datenschutzerklärung: Meta, GA4, Leadinfo | P0-06 | L-186 | offen, David + Anwalt. **L-186 ist der billige Teil davon** und steht nicht im PDF: Das Widget zeigt auf fremden Seiten **keinen** Datenschutzlink, weil `privacy_url` produktiv leer ist. Ein Feld in den Widget-Einstellungen, kein Code. |
| **9** B | A2-9 gestalten (9:16) | P0-12 | — | offen, David. Blockiert zusätzlich P0-17. |
| **12** B | Laufzeitbudget auf Kampagnenebene | Teil von P0-17 | — | offen, David. Bei laufender Kampagne eine Umstellung, keine Ersteinrichtung. |
| **13** B | Nachfassprozess steht | P0-09 | L-185 *(teilweise)* | **Die Technik steht, der Prozess nicht.** Gebaut sind beide Erinnerungsstrecken (`services/lead_nachfassen.py`, 14 Tests). Offen ist die menschliche Seite: wer ruft an, in welcher Frist, mit welchem Text. Das PDF nennt es „unabhängig vom Ausgang, vor dem ersten Euro" — der erste Euro ist ausgegeben. |
| **5** | Traffic-Positivliste am Datensatz | P0-16 | — | offen, David. |
| **6** | Datensatz umbenennen auf „Websprint Audit" | P0-16 | — | offen, David. |
| **10** | Karten 1, 3, 4, 6 nachschärfen | P1-13 | — | offen, David. Nachrangig, solange 0 von 69 das Formular anfassen. |
| **11** | Steuerinformationen im Konto verifizieren | P0-15 | — | offen, David. |
| **14** | UTM ins Widget durchreichen | P1-03 + **P0-05** | L-188 | **Gebaut, nicht hochgeladen.** Siehe unten. |
| **1** | Widget-Pixelfeld leeren | — | — | laut PDF entfallen (15.09.), Doppelzählung über `eventID` gelöst. Bleibt Messpunkt im Testdurchlauf. |
| **15** | Conversions API | — | — | laut PDF läuft sie, Token gesetzt. Am System heute nicht gegengeprüft — *nicht erhoben*. |

---

## Was heute gemessen wurde

### 1. Der Ankersprung hält — auch mit stehendem Einwilligungsdialog

Fassung 4 stellt die Frage unter „Vor dem Start zu prüfen", der Vertriebsplan
führt sie als P0-04, und L-195 nennt den fehlenden Anker als Verdächtigen für
die 69 Besucher ohne Formular.

Am Quelltext war sie **nicht** zu entscheiden: Die Seite liefert statisch
**930 Zeichen** aus, der gesamte Inhalt steckt in zehn Inline-Skripten und wird
erst zur Laufzeit eingehängt (das ist der SERP-Befund T2 und die Ursache von
L-20). Ein Anker auf ein Element, das beim Laden noch nicht existiert, ist ein
naheliegender Bruch.

Im Browser gemessen, zweimal, mit geleertem `kpg-consent-v1`:

| | |
|---|---|
| Ankerziel `#analyse` | vorhanden, **953 px** unter dem Seitenanfang |
| `scrollY` nach dem Laden | **953** — der Sprung wird ausgeführt |
| Einwilligungsdialog | steht, `.kco`, bildschirmfüllend, `z-index: 200` |
| Seitenlauf gesperrt? | **nein** (`body` hat `overflow: hidden auto`, kein Scroll-Lock) |
| Oberkante des Widget-Rahmens | **1.349 px** — bestätigt die Zahl aus Fassung 4 |

**Damit ist P0-04 Teil A beantwortet, aber nur für den Desktop.** Mobil — und
**95 von 117 Aufrufen waren mobil** — ist es *nicht erhoben*: Das Fenster ließ
sich nicht verkleinern, `innerWidth` blieb bei 1728. Wer die Frage mobil
beantworten will, braucht ein echtes Gerät oder die Geräteansicht der
Entwicklerwerkzeuge.

Der Verdächtige aus L-195 ist damit **entlastet, nicht freigesprochen**. Der
Bruch zwischen Seite und Formular liegt woanders.

### 2. Die Landingpage: es fehlen genau 658 Byte

| | live | Repo |
|---|---|---|
| `last-modified` | **15.09., 19:03 CEST** (dritter Tag unverändert) | Commit 15.09., 19:48 |
| Größe | 1.020.062 Byte | 1.020.720 Byte |

Die beiden Dateien wurden zeichenweise verglichen, nicht überschlagen. Sie
unterscheiden sich an **genau einer Stelle**: dem Block, der die fünf
UTM-Felder an das Widget durchreicht. Alles andere — Pixel, `InitiateCheckout`,
`begin_checkout`, `fbclid`/`fbp`, Leadinfo, der Anker — ist **live**.

Gegenprobe am geladenen `iframe`: Die Quelladresse trägt heute
`?fbp=fb.1.…` und **kein einziges** `utm_`.

**Folge:** Jeder Lead käme ohne Herkunft an. Die Frage „welche Tonlage bringt
mehr Menschen auf die Seite" — Antwort 1 der sechs, die Fassung 4 für den Monat
verspricht — ist bis zum Upload unbeantwortbar.

---

## Was Fassung 4 nicht kennt, aber die Rechnung ändert

**a) Die Einwilligungsquote trägt den ganzen Hebel 1 — und ist die einzige Zahl,
die dagegen spricht.**

Fassung 4 steht und fällt mit einer Schwelle: **25 Abschlüsse je Woche und
Anzeigengruppe**, gezählt von Meta. Abschnitt 6 setzt dafür 60–75 % Einwilligung
an. Gemessen am 15.09. sind es **6 %** (GA4 4 Sitzungen ÷ 69 Besucher) — und das
ist eine **untere Schranke**, keine Punktschätzung: GA4 zählt dieselbe Klasse
Zustimmung wie Metas „Landingpage-Aufrufe" (3 von 69).

Auch als untere Schranke steht sie quer zur Annahme. Bei 6 % bräuchte die
Anzeigengruppe rund **420 echte** „Analyse gestartet" pro Woche, damit Meta
25 sieht. Bei 60 % wären es 42.

Zwischen den beiden Zahlen liegt die Entscheidung über Hebel 1 — und sie ist
**direkt messbar**: Zustimmungen am Dialog gegen Aufrufe von
`/api/widget/config`. Das ist eine Auswertung, keine Annahme.

**b) L-183 — der eigene Erheber erreicht die eigene Seite nicht.**
`websprint.kompagnon.eu` liegt auf demselben Host wie `www.kompagnon.eu`, und
dieser Host nimmt aus dem Render-Rechenzentrum Frankfurt keine Verbindung an
(`ConnectTimeout`). Steht in keinem der beiden Kampagnendokumente. Folge: Jeder
Interessent bei einem Hoster mit derselben Sperre bekommt einen Fehler statt
eines Befunds — ein Trichterleck, das keine Anzeigenoptimierung findet.

**c) L-187 widerspricht dem Produktleiter.** Der Vertriebsplan führt Check PLUS
als „live seit 13.09.". Das Lagebild sagt: Das Produkt steht auf `draft`, beide
Kassenwege filtern auf `live`, und der produktiv stehende Zahllink hätte bis zum
14.09. bei jedem Kauf einen **Website-Auftrag** ausgelöst statt eines Check
PLUS. Das gehört in P1-18 („Widersprüche bereinigen"), bevor jemand auf dem
falschen Stand aufbaut.

**d) L-189 liegt bei mir.** Die Ereignisse gehen seit dem 15.09. raus, aber die
GA4-Sammlung dieser Property hat **keinen Ereignisbericht**. Ohne eine einmalig
angelegte Datenanalyse „Ereignisanzahl nach Ereignisname" bleibt Stufe 4 des
Trichters leer und die Diagnose bei „zwischen 3 und 5" stehen.

---

## Drei Zahlen in Fassung 4, die nicht zusammenpassen

1. **Budget: 739 € / 793 € / 795 € / 797 €.** Abschnitt 0 sagt „dieselben
   793 €", Abschnitt 4 „Laufzeitbudget 739 €", Abschnitt 7 rechnet
   245 + 494 + 56 = **795 €** und nennt daneben „5 € Puffer" (also 800),
   Variante S kommt auf 797 €. Ein Betrag, vier Schreibweisen.
2. **Impressionen und Klicks.** Abschnitt 2 rechnet mit 99.000 Impressionen und
   790–1.390 Klicks, Abschnitt 8 mit ca. 92.000 und 740–1.290. Die eine Rechnung
   steht auf 793 €, die andere auf 739 € — beide korrekt, aber nebeneinander
   liest es sich wie ein Fehler.
3. **Der Name des Ereignisses.** Fassung 4 sagt durchgängig **„Analyse
   gestartet"**, der Code sendet `kpg-analyse-begonnen`, der Vertriebsplan
   nennt P0-03 „Analyse **begonnen**". Gegenüber Meta trägt es ohnehin
   `InitiateCheckout` — die Sache stimmt. Aber wer im Events Manager nach
   „Analyse gestartet" sucht, findet nichts.

---

## Was daraus folgt

Die Reihenfolge von Fassung 4 setzt voraus, dass noch nichts läuft. Für den
17.09. dreht sie sich um:

1. **Landingpage hochladen** (P0-05, Punkt 14). 658 Byte, Anleitung liegt in
   `docs/landingpage/UPLOAD-16-09-2026.md`. Bis dahin ist jeder Lead
   herkunftslos und der Testdurchlauf (Punkt 3) nicht aussagekräftig.
2. **Einwilligungsquote auswerten**, bevor über Hebel 1 entschieden wird.
   Zustimmungen gegen `/api/widget/config`-Aufrufe. Fällt sie zweistellig aus,
   trägt das Optimierungsereignis; bleibt sie bei 6 %, ist die Lernphase über
   ein Pixel-Ereignis bei diesem Budget **unerreichbar** — und Fassung 4 braucht
   eine andere Antwort als ein flacheres Ereignis.
3. **Den Bruch zwischen Seite und Formular finden.** Der Anker ist entlastet.
   Offen sind: die mobile Ansicht (95 von 117 Aufrufen), der
   Facebook-In-App-Browser (13 Aufrufe) und das Audience Network (75 von 94
   Klicks). Alle drei sind messbar, keiner ist gemessen.
4. **`privacy_url` setzen** (L-186). Eine Minute, kein Code, und es ist der
   einzige Punkt aus dem Rechts-Block, der heute ohne Anwalt zu schließen ist.

Erst danach lohnen die Punkte 4, 5, 6, 9, 10, 11 und 12 — sie verbessern eine
Kette, deren Riss eine Stufe weiter unten liegt.
