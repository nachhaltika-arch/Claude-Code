# Kriterienhandbuch — was der Website-Check prüft und wie

> **Wofür diese Datei da ist.** Der Bericht nennt je Kriterium einen Hinweis,
> was geprüft wird. Er sagt nicht, **woraus** die Punktzahl entsteht. Diese
> Datei sagt es — je Kriterium die Stelle im Code, die den Wert liefert.
>
> **Stand:** 2026-09-04 · **Quellstand:** `87e2cf5` auf `staging`
>
> Sie ist **gemessen, nicht beschrieben**: Jede Zeile der Spalte „Woraus die
> Punkte kommen" ist aus `services/audit_scoring.py` und den Erhebungen in
> `services/audit_collectors.py` bzw. `services/qa_scanner.py` abgelesen.
> Wo eine Bewertung folgt, steht sie als **Befund** darunter und ist als
> Meinung gekennzeichnet.
>
> **Anlass:** Rückmeldung eines Fremdlesers zum Bericht für `neovendo.de`
> (82/100, Silber) am 2026-09-04. Fünf Beanstandungen, alle am Code
> nachgegangen — Abschnitt 1.

---

## 0 · Das Abhängigkeitsbild

Die Frage, ob eine Eigenentwicklung sinnvoll ist, lässt sich beziffern.
**103 Punkte verteilen sich auf drei Herkünfte:**

| Herkunft | Kriterien | Punkte | Was bei Ausfall passiert |
|---|---:|---:|---|
| **Eigene Messung** (HTML, TLS, robots.txt, Header) | 25 | **68** | nichts — läuft ohne Fremddienst |
| **PageSpeed Insights** (Google) | 8 | **20** | fallen aus Zähler und Nenner; der Bericht zeigt „–" |
| **Sprachmodell** | 6 | **15** | dito — **und der gesamte Fließtext des Berichts entfällt** |

Die acht PageSpeed-Kriterien: `tp_lcp` (4), `tp_cls` (3), `tp_inp` (2),
`tp_mobile` (3), `bf_lighthouse` (3), `bf_kontrast` (2), `bf_tastatur` (1),
`dg_typografie` (2).

Die sechs KI-Kriterien: `dg_aktualitaet` (3), `dg_farbsystem` (2),
`dg_bildqualitaet` (2), `cv_klarheit` (3), `cv_angebot` (3),
`ih_textqualitaet` (2).

> **Der Ausfall ist kein Gedankenspiel, er ist der Normalfall.** Im Bericht
> für `neovendo.de` sind **alle acht** PageSpeed-Kriterien ausgefallen. Der
> Kunde liest deshalb „Barrierefreiheit 0/2" und „Performance 1/3" — Zahlen,
> die wie ein vernichtendes Urteil aussehen und in Wahrheit heißen: *von fünf
> Kriterien konnten wir eines messen.* Die Rechnung ist richtig (nicht
> Erhobenes fällt aus Zähler **und** Nenner, § 3.5), die Darstellung ist
> irreführend.

**Was eine Eigenentwicklung ersetzen könnte — und was nicht:**

| Heute | Eigen machbar? | Womit |
|---|---|---|
| `bf_kontrast`, `bf_tastatur`, `bf_lighthouse`, `dg_typografie` | **ja** | Der Browserlauf (`seitenbrowser.py`, seit 26.08. produktiv) hat die gerenderte Seite bereits im Zugriff. Kontrast, Schriftgröße, Skip-Link und Fokusreihenfolge sind daraus direkt messbar — dieselben Prüfungen, die wir für L-17 am eigenen Werkzeug schon geschrieben haben. |
| `tp_lcp`, `tp_cls`, `tp_inp`, `tp_mobile` | **nein, nicht sinnvoll** | `tp_inp` ist ein **Felddatenwert** aus echten Nutzersitzungen (CrUX); den kann niemand im Labor erzeugen. LCP und CLS wären über den eigenen Browser messbar, aber ohne Googles Netz- und Gerätemodell nicht vergleichbar — und die Zahl im Bericht soll dieselbe sein, die der Betrieb bei Google sieht. |
| `dg_farbsystem`, `dg_bildqualitaet`, `dg_aktualitaet` | **teilweise** | Palettengröße und Bildherkunft sind messbar (Farbanzahl aus dem Screenshot, Stockbild-Signaturen im Dateinamen). „Wirkt zeitgemäß" ist es nicht. |
| `cv_klarheit`, `cv_angebot`, `ih_textqualitaet` | **nein** | Das sind Texturteile. Sie sind der Grund, warum ein Modell im Spiel ist. |

**Empfehlung:** Die vier Barrierefreiheits- und Typografie-Kriterien vom
Browserlauf holen statt von Lighthouse. Das nimmt **8 Punkte** aus der
Fremdabhängigkeit, nutzt einen Dienst, der ohnehin läuft, und behebt zugleich
den auffälligsten Darstellungsfehler des Berichts. Die Core Web Vitals bleiben
bei Google — dort gehören sie hin.

---

## 1 · Der Fremdlauf vom 2026-09-04

Fünf Beanstandungen, jede am Code nachgegangen. **Zwei bestätigen sich, eine
ist etwas anderes als gemeldet, zwei sind richtig gemessen und falsch
dargestellt.**

### 1.1 🔴 „Der Preis steht prominent auf der Startseite, der Bericht sagt, er fehlt"

**Bestätigt, und die Ursache ist ein Widerspruch in derselben Ausgabe.** Der
Fließtext lobt „Leistungen, Preise, Laufzeiten … stehen offen da", die
Problemliste sagt „Die Preise stehen erst in der FAQ; auf der Startseite fehlt
oben ein kurzer Hinweis". Beides stammt aus **einem** Modellaufruf.

**Die Ursache ist eine falsche Überschrift.** Der Textblock hieß `SEITENTEXT
DER STARTSEITE`. Übergeben wird aber `_gesamttext` (`audit_runner.py:263`): der
Text **aller** erhobenen Seiten, jedes Stück mit seiner Adresse in eckigen
Klammern davor. Das Modell bekam also die ganze Website und die Anweisung, sie
für die Startseite zu halten.

**Behoben am 2026-09-04.** Die Adressmarken sind die Lösung, nicht das Problem:
Mit ihnen *kann* das Modell über Platzierung sprechen. Es muss nur wissen, dass
es sie gibt. Der Block nennt jetzt die geprüften Seiten, erklärt die Marken und
verlangt für jede Aussage über Platzierung einen Beleg daraus.

> **Korrektur an dieser Stelle.** Hier stand zuerst, das Modell könne die
> Seitenzugehörigkeit „nicht ableiten" und man müsse ihm Ortsangaben
> untersagen. Beides war falsch: Die Zuordnung lag längst im Text, nur die
> Überschrift log. Wer die Diagnose übernommen hätte, hätte dem Modell eine
> Fähigkeit verboten, die es hat.

### 1.2 🔴 „Ein Blogbeitrag vom 12. August 2026 wird als Zukunftsdatum bewertet"

**Bestätigt, und die Ursache ist klein.** Im gesamten Prompt (`audit_ai.py`,
`_user_content`) kommt **kein heutiges Datum vor**. Das Modell beurteilt
Datumsangaben gegen seine eigene Zeitvorstellung; ein Beitrag vom 12.08.2026
erscheint ihm als Zukunft.

**Besser:** Das Erhebungsdatum in den Prompt, als Satz und nicht als Feld —
`Heute ist der 04.09.2026. Datumsangaben vor diesem Tag liegen in der
Vergangenheit.` Dazu ein Test, der einen Text mit einem Datum von gestern
schickt und prüft, dass keine Zukunftsbehauptung entsteht.

> **Der Fehler hätte auffallen müssen.** `analyse_freshness` bekommt das
> laufende Jahr ausdrücklich übergeben (`current_year`) — die **gemessene**
> Seite kennt das Datum also. Nur der Teil, der Sätze schreibt, kennt es nicht.

### 1.3 🟡 „Cookie-Consent 0/4, obwohl kein einwilligungspflichtiger Dienst da ist"

**Etwas anderes als gemeldet — und schwerer.** Die Bedingung ist gebaut
(`audit_scoring.py:123`): ohne Drittanbieter gibt es die vollen 4 Punkte. Sie
hat nur nicht gegriffen, weil sie die **falsche Größe** liest.

`detect_third_parties` liefert drei Mengen: `count` (alle acht erkannten
Dienste, einschließlich **Google Maps und YouTube**), `tracking_services`
(Analytics, Facebook, Doubleclick, Hotjar, Clarity) und `external_fonts`.

Damit bewerten **drei Kriterien denselben Google-Maps-Einbau verschieden:**

| Kriterium | liest | Ergebnis für diese Seite |
|---|---|---|
| `rc_cookie` | `count > 0` → einwilligungspflichtig | **0 von 4** |
| `si_drittanbieter` | nur Fonts und Tracking | **2 von 2** ✓ |
| `se_lokal` | `qa.google_maps` → lokales Signal | **+1 Punkt** |

Ein Einbau, ein Bericht, drei Urteile — und sie stehen auf derselben Seite
untereinander. Der Fremdleser hat daraus geschlossen, die Cookie-Prüfung sei
kaputt. Sie ist es nicht; **die Kriterien sind sich uneinig, was
„einwilligungspflichtig" heißt.**

**Das ist eine Maßstabsfrage, keine Reparatur.** Rechtlich sind ein Maps- und
ein YouTube-Einbau vor der Einwilligung heikel — `rc_cookie` liegt also näher
an der Sache als `si_drittanbieter`. Zu entscheiden ist, ob `si_drittanbieter`
nachzieht (dann verliert die Seite dort zusätzlich Punkte) und ob `se_lokal`
einen Einbau weiter belohnen darf, den `rc_cookie` bestraft. Gehört in die
Fassung 2027.1 zu den übrigen Doppelwertungen (L-114).

**Sofort und ohne Maßstabsänderung möglich:** Der Bericht muss sagen,
**welcher** Dienst den Abzug ausgelöst hat. `services` steht als Liste im
Befund — sie wird nur nirgends ausgegeben. Hätte dort „Google Maps gefunden,
kein Consent-Tool" gestanden, wäre die Rückfrage nie entstanden.

> **Nebenbefund:** `maps_embedded` wird erhoben und von **keinem** Kriterium
> gelesen. Fünfte Wiederholung derselben Klasse — gebaut, nicht angeschlossen.

### 1.4 🟡 „Performance 1/3 und Barrierefreiheit 0/2, obwohl das meiste gar nicht erhoben wurde"

**Richtig gerechnet, falsch dargestellt.** Beide Kategorien haben genau ein
erhobenes Kriterium: `tp_bilder` (3 Punkte, 1 erreicht) und `bf_alt` (2 Punkte,
0 erreicht). Die übrigen acht hängen an PageSpeed und sind ausgefallen.

Der Bericht kennzeichnet die einzelnen Zeilen korrekt mit „○ nicht erhoben".
Die **Kategorieüberschrift** tut es nicht: „Barrierefreiheit (WCAG/BFSG) 0/2"
sieht aus wie ein Totalausfall des Betriebs.

**Besser:** Die Kategoriezeile trägt den Anteil mit — „0 von 2 · 1 von 5
Kriterien erhoben". Und wo eine ganze Kategorie an einem ausgefallenen
Fremddienst hängt, gehört ein Satz darüber, nicht in die Fußnote.

### 1.5 🟡 „Alt-Texte sind vorhanden, der Bericht sagt, sie fehlen"

**Die Messung ist zu grob, um den Vorwurf zu tragen.** `qa_scanner.py:205`
zählt `<img>`-Elemente im **roh geladenen HTML** und wertet jedes mit leerem
`alt` als fehlend. Drei Fälle laufen dabei falsch:

1. **`alt=""` ist korrektes Markup**, nicht ein Fehler — es kennzeichnet ein
   dekoratives Bild und ist nach WCAG genau richtig. Die Messung zählt es als
   Verstoß.
2. **Bilder, die erst im Browser entstehen** (Lazy Loading über `data-src`,
   `<picture>`, Hintergrundbilder), stehen nicht im Roh-HTML — oder stehen
   dort ohne `alt`, das erst das Skript setzt.
3. **Zählpixel und Icons** wiegen so schwer wie ein Inhaltsbild.

Der Katalog verspricht „Anteil der Bilder mit einem Alt-Text"; gemessen wird
der Anteil der `<img>`-Tags im Quelltext mit nichtleerem `alt`. Das ist nicht
dasselbe.

**Besser:** Die Messung an den Browserlauf hängen, der seit dem 26.08. läuft —
dort steht die gerenderte Seite. Dekorative Bilder (`alt=""`, `role=
"presentation"`, `aria-hidden`) aus der Grundgesamtheit nehmen statt sie als
Fehler zu zählen. Beides zusammen macht aus einer Vermutung eine Messung.

---

## 2 · Die 43 Kriterien im Einzelnen

**Erhebungsart:** ● gemessen · ◐ abgeleitet · ◇ KI-Einschätzung.
Die Spalte „Woraus die Punkte kommen" nennt den tatsächlichen Rechenweg.

### 2.1 · Recht & Compliance — 20 Punkte

| Kriterium | P | Art | Woraus die Punkte kommen |
|---|--:|:-:|---|
| `rc_impressum` Impressum (§ 5 DDG) | 6 | ● | 3 wenn die Unterseite erreichbar ist, weitere 3 wenn die Pflichtangaben vollständig sind (`_evaluate_impressum`) |
| `rc_datenschutz` Datenschutzerklärung | 6 | ● | ebenso, über `_evaluate_datenschutz` |
| `rc_cookie` Cookie-Consent (TDDDG) | 4 | ● | 4 bei erkanntem Consent-Tool (19 Signaturen), 4 wenn **kein** Drittanbieter gefunden wurde, sonst 0 |
| `rc_bfsg` Barrierefreiheitserklärung | 2 | ● | 2 wenn eine Erklärung verlinkt ist |
| `rc_formular_dsgvo` Formular DSGVO-konform | 2 | ● | 2 wenn **alle** Formulare eine Einwilligung tragen, 1 wenn mindestens eines, 0 sonst; ohne Formular nicht erhoben |

> **Befund `rc_cookie`:** siehe 1.3 — liest `count` statt einer Menge
> einwilligungspflichtiger Dienste.
>
> **Befund `rc_impressum` / `rc_datenschutz`:** Die Erkennung der Unterseite
> läuft über Linktexte und Adressmuster (`_find_link`). Eine Seite, die ihr
> Impressum nur im Fußbereich als Bild oder hinter einem Skript führt, gilt als
> nicht erreichbar — mit dem schwersten Ergebnis, das der Katalog kennt
> (Deckel auf „Nicht konform"). Der Browserlauf würde auch das auflösen.

### 2.2 · Sicherheit & Datenschutz — 10 Punkte

| Kriterium | P | Art | Woraus die Punkte kommen |
|---|--:|:-:|---|
| `si_ssl` TLS-Zertifikat | 3 | ● | echter Handshake (`check_tls`); 3 gültig, 2 bei baldigem Ablauf, 0 ungültig |
| `si_redirect` HTTP→HTTPS | 2 | ● | 2 wenn die http-Variante weiterleitet |
| `si_header` Security-Header | 3 | ● | Anteil von HSTS, CSP, X-Frame-Options, X-Content-Type-Options, skaliert auf 3 |
| `si_drittanbieter` Drittanbieter ohne Einwilligung | 2 | ● | 2 minus 1 für externe Google-Fonts, minus 1 für Tracking ohne Consent-Tool |

> **Befund `si_header`:** Vier Header auf drei Punkte, gerundet — wer den
> dritten von vier nachrüstet, bekommt dafür nichts (0→0, 1→1, 2→2, **3→2**,
> 4→3). Belegt und vertagt auf die Fassung 2027.1, von vier Tests gehalten
> (L-114).
>
> **Befund `si_drittanbieter`:** ignoriert Maps- und YouTube-Einbauten, die
> `rc_cookie` mit 4 Punkten bestraft. Siehe 1.3.

### 2.3 · Performance & Core Web Vitals — 15 Punkte

| Kriterium | P | Art | Woraus die Punkte kommen |
|---|--:|:-:|---|
| `tp_lcp` LCP | 4 | ● | PageSpeed: unter 2,5 s → 4 · unter 4,0 s → 2 · darüber 0 |
| `tp_cls` CLS | 3 | ● | PageSpeed, Schwellenstaffel |
| `tp_inp` INP | 2 | ● | **CrUX-Felddaten** — nur vorhanden, wenn die Seite genug echten Verkehr hat |
| `tp_mobile` Mobile-Performance | 3 | ● | PageSpeed-Gesamtwert mobil: ab 90 → 3 · ab 70 → 2 · ab 50 → 1 |
| `tp_bilder` Bildoptimierung | 3 | ● | je 1 Punkt: ≥50 % moderne Formate · ≥50 % lazy · ≥80 % mit Größenangabe **und** kein überdimensioniertes Bild |

> **Befund:** Vier von fünf hängen an einem Fremddienst; fällt er aus, bleibt
> `tp_bilder` allein und die Kategorie liest sich als „1 von 3". Siehe 1.4.
>
> **`tp_inp` ist strukturell oft nicht erhebbar** — ein Handwerksbetrieb mit
> wenig Verkehr hat keine CrUX-Daten. Der Katalog nennt das im Hinweis; der
> Bericht sollte den Unterschied zwischen „ausgefallen" und „für diese Seite
> nicht erhebbar" zeigen, statt beides als „nicht erhoben" zu führen.

### 2.4 · Barrierefreiheit (WCAG/BFSG) — 10 Punkte

| Kriterium | P | Art | Woraus die Punkte kommen |
|---|--:|:-:|---|
| `bf_lighthouse` Accessibility-Score | 3 | ● | Lighthouse-Gesamtwert, Schwellenstaffel |
| `bf_kontrast` Farbkontraste | 2 | ● | Lighthouse-Audit `color-contrast`, skaliert |
| `bf_alt` Alt-Texte | 2 | ● | Anteil der `<img>` im Roh-HTML mit nichtleerem `alt`, Schwellenstaffel |
| `bf_semantik` Semantik & Struktur | 2 | ● | 1 für saubere Überschriftenhierarchie, 1 für bestandenes Lighthouse-Semantik-Audit |
| `bf_tastatur` Tastaturbedienung | 1 | ◐ | Lighthouse-Audit, skaliert |

> **Befund:** Vier von fünf hängen an Lighthouse — und Lighthouse kommt über
> PageSpeed, fällt also mit ihm aus. Das fünfte (`bf_alt`) misst am Roh-HTML
> und zählt korrektes `alt=""` als Fehler (1.5).
>
> **Diese Kategorie ist der beste Kandidat für die Eigenentwicklung.** Kontrast,
> Schriftgröße, Fokusreihenfolge, Skip-Link und Alt-Texte sind am gerenderten
> Dokument alle direkt messbar — und der Browser läuft bereits.

### 2.5 · SEO & Auffindbarkeit — 18 Punkte

| Kriterium | P | Art | Woraus die Punkte kommen |
|---|--:|:-:|---|
| `se_meta` Title & Meta-Description | 3 | ● | je 1: Title vorhanden und Länge in Ordnung · Description ebenso · Title trägt Ort **oder** Leistung nach Branchenklasse |
| `se_struktur` Überschriften & Tiefe | 2 | ● | 1 für genau ein H1 mit H2-Gliederung, 1 für Mindestwortzahl |
| `se_index` Indexierbarkeit | 3 | ● | je 1: robots.txt vorhanden und ohne Aussperrung · sitemap.xml · Canonical |
| `se_schema` Strukturierte Daten | 3 | ● | je 1: JSON-LD vorhanden · passender Haupttyp zur Klasse · ein passender Zusatztyp |
| `se_lokal` Lokale Signale | 3 | ● | je 1: Ort in Title oder H1 · Telefon als `tel:`-Link · Karteneinbau **oder** LocalBusiness-Auszeichnung |
| `se_links` Keine defekten Links | 1 | ● | 1 wenn die Linkprüfung der Startseite nichts findet |
| `se_ki_lesbar` Lesbarkeit für KI | 3 | ● | 2 wenn kein KI-Crawler ausgesperrt ist, 1 für vorhandene `llms.txt` |

> **Befund `se_lokal`:** belohnt den Karteneinbau, den `rc_cookie` mit vier
> Punkten bestraft. Siehe 1.3.
>
> **Befund `se_links`:** prüft nur die Startseite. Der Hinweis sagt das auch —
> aber ein Betrieb liest „Keine defekten Links: 1/1" und hält seine ganze Seite
> für geprüft. Entweder tiefer prüfen (die Unterseiten liegen vor) oder den
> Kriteriumsnamen auf das eingrenzen, was gemessen wird.

### 2.6 · Design & Gestaltung — 10 Punkte

| Kriterium | P | Art | Woraus die Punkte kommen |
|---|--:|:-:|---|
| `dg_aktualitaet` Visuelle Aktualität | 3 | ◇ | Modellurteil am Bildschirmfoto |
| `dg_typografie` Typografie & Lesbarkeit | 2 | ● | Lighthouse-Audit `font-size` |
| `dg_farbsystem` Farbsystem & Konsistenz | 2 | ◇ | Modellurteil |
| `dg_bildqualitaet` Bildqualität & Authentizität | 2 | ◇ | Modellurteil |
| `dg_mobil` Mobile Darstellung | 1 | ● | 1 wenn eine Viewport-Angabe im Kopf steht |

> **Befund `dg_mobil`:** Ein `<meta viewport>` ist die niedrigste denkbare
> Hürde — sie steht in jeder Vorlage der letzten zehn Jahre. Das Kriterium
> vergibt seinen Punkt praktisch immer und misst damit nichts. Am gerenderten
> Dokument wäre stattdessen prüfbar, was der Name verspricht: ob die Seite bei
> 375 px Breite ohne Querlauf steht.

### 2.7 · Conversion & Nutzerführung — 15 Punkte

| Kriterium | P | Art | Woraus die Punkte kommen |
|---|--:|:-:|---|
| `cv_klarheit` Klarheit above the fold | 3 | ◇ | Modellurteil am Bildschirmfoto |
| `cv_cta` Primär-CTA | 3 | ◐ | Anzahl branchenpassender Handlungsaufrufe: ab 3 → 3 · ab 1 → 2 · sonst 0 |
| `cv_kontakt` Kontaktwege | 3 | ● | je 1 für die drei Kontaktmerkmale der Branchenklasse |
| `cv_vertrauen` Vertrauenssignale | 3 | ◐ | Anzahl der Signalgruppen (Bewertungen, Referenzen, Team, Garantie, passende Zertifikate): ab 4 → 3 · ab 2 → 2 · ab 1 → 1 |
| `cv_angebot` Angebots-Klarheit | 3 | ◇ | Modellurteil am Seitentext |

> **Befund `cv_angebot`:** Das Kriterium, das im Fremdlauf den falschen Befund
> erzeugt hat (1.1). Es urteilt über Platzierung, ohne die Seitenstruktur zu
> kennen.

### 2.8 · Inhalt & Substanz — 5 Punkte

| Kriterium | P | Art | Woraus die Punkte kommen |
|---|--:|:-:|---|
| `ih_leistungsseiten` Eigene Leistungsseiten | 2 | ● | Anzahl branchenpassender Leistungsseiten, Schwellenstaffel |
| `ih_aktualitaet` Aktualität | 1 | ● | 1 wenn das Copyright-Jahr aktuell ist **oder** ein Datum im Text steht |
| `ih_textqualitaet` Textqualität | 2 | ◇ | Modellurteil |

> **Befund `ih_aktualitaet`:** `has_dated_content` erkennt jedes Muster
> `TT.MM.JJJJ` — auch eines aus dem Jahr 2019 und auch eines in der Zukunft.
> Ein Datum genügt, sein Wert wird nicht geprüft. Genau die Seite, deren
> Blogdatum das Modell als Zukunft beanstandet hat, bekommt dafür hier ihren
> Punkt.

### 2.9 · Infrastruktur — ohne Wertung

| Angabe | Woraus sie kommt |
|---|---|
| `ho_anbieter` Hosting-Anbieter | Rückwärtsauflösung und Header |
| `ho_uptime` Erreichbarkeit | Antwort auf den Abruf |
| `ho_cdn` CDN aktiv | sieben Header-Signaturen |
| `ho_cms` CMS / Tech-Stack | Signaturen im HTML |

Diese vier tragen 0 Punkte und stehen im Bericht als Auskunft.

---

## 3 · Rangliste der Weiterentwicklung

Geordnet nach dem, was der Fremdlauf gezeigt hat: **falsche Befunde zuerst,
dann fehlende Belege, dann Maßstabsfragen.**

| # | Was | Wirkung | Aufwand | Maßstab betroffen? |
|---|---|---|---|---|
| **1** | Heutiges Datum in den KI-Prompt | beendet die Zukunftsbehauptung | S | nein |
| **2** | Jeder Punktabzug nennt seinen Messwert im Bericht | beantwortet die Hauptkritik des Fremdlaufs; `rc_cookie` hätte nie zur Rückfrage geführt | M | nein |
| **3** | Kategoriezeile zeigt „x von y Kriterien erhoben" | „0/2" liest sich nicht mehr als Urteil | S | nein |
| **4** | Alt-Texte am Browserlauf messen, `alt=""` als korrekt werten | behebt einen belegten Fehlbefund | M | nein |
| **5** | KI darf keine Aussage über Platzierung machen, solange sie die Seitenstruktur nicht kennt | behebt den zweiten belegten Fehlbefund | M | nein |
| **6** | Barrierefreiheit vom Browserlauf statt von Lighthouse | 8 Punkte weniger Fremdabhängigkeit, Kategorie fällt nicht mehr komplett aus | L | nein — dieselben Kriterien, andere Quelle |
| **7** | `maps_embedded` anschließen oder entfernen | ein erhobener Wert ohne Leser | S | ja |
| **8** | Einigung, was „einwilligungspflichtig" heißt (`rc_cookie` / `si_drittanbieter` / `se_lokal`) | beendet drei Urteile über einen Sachverhalt | M | **ja — Fassung 2027.1** |
| **9** | `dg_mobil` an der gerenderten Breite messen statt am Viewport-Tag | das Kriterium misst wieder etwas | M | ja |

**Die ersten fünf ändern keinen einzigen Punktwert im Bestand.** Sie machen
den Bericht belegbar, nicht strenger. Erst ab Nummer 6 wird es Arbeit, und
erst ab Nummer 8 verschieben sich Punktzahlen — dort gehört es in die
Katalogfassung 2027.1 zu den übrigen Doppelwertungen aus L-114.

---

## Reproduzierbarkeit

```bash
# Zuordnung Kriterium → Messstelle, wie sie diesem Dokument zugrunde liegt
grep -nE '_nach_abstufung\(sheet, "|sheet\.set\("|sheet\.scale\("' \
  kompagnon/backend/services/audit_scoring.py

# Herkunft je Kriterium (gemessen / abgeleitet / KI)
cd kompagnon/backend && venv/bin/python -c "
from services.audit_criteria import all_criteria
for c in all_criteria(): print(c.key, c.max_points, c.source.name)"
```
