# KAS — Soll-Ist-Analyse der Oberfläche

> Erhoben am 2026-08-16 an der laufenden Produktivumgebung `kas.kompagnon.group`,
> angemeldet als Superadmin. Methode: Steve Krug, *Don't Make Me Think* —
> ergänzt um eine Betrachtung der drei Nutzerreisen.
> Fortlaufend geführt, wie `soll-ist-analyse.md`.

---

## Wie diese Datei zu lesen ist

Jeder Befund hier ist **an der echten Oberfläche gesehen**, nicht aus dem Code
abgeleitet. Wo ich etwas vermute, steht es als Vermutung.

**Der Umfang ist begrenzt, und das gehört dazu:** Das System hat **86 Routen
und 72 Seiten-Dateien**. Ich habe die drei Kernreisen vollständig abgegangen
(Betreiber, Kunde, Öffentlichkeit) und die dabei berührten Bildschirme einzeln
beurteilt. Nicht einzeln angesehen habe ich den langen Schwanz: Academy-
Verwaltung, Mobil-Ansichten, Newsletter-Designer, Template- und Component-
Editoren. Sie stehen in Abschnitt 7 als offene Fläche — nicht als „in Ordnung".

Eine Zahl ohne Beleg ist in diesem Dokument nichts wert. Deshalb steht hinter
jedem Befund, woran er zu sehen ist.

---

## 1. Gesamtbild

| Reise | Stand | Kern |
|---|---|---|
| A — Öffentlichkeit (Widget, Anmeldung) | 🟢 | Das klarste am ganzen System. Ein Feld, ein Knopf, eine Erwartung |
| B — Betreiber (Akquise → Lead → Audit → Projekt) | 🟠 | Funktional vollständig, sprachlich und strukturell widersprüchlich |
| C — Kunde (Portal, Freigaben, Rechnungen) | 🟡 | Eigene, hellere Welt — nicht schlecht, aber ein anderes Produkt |

**Die Kurzfassung:** Das System kann viel und zeigt es schlecht. Die
Schwierigkeit liegt fast nirgends in der Funktion und fast überall in der
**Benennung** und der **visuellen Gewichtung**. Ein neuer Nutzer muss an
mehreren Stellen raten, was ein Wort bedeutet — und in zwei Fällen bedeutet
dasselbe Wort an zwei Orten zwei verschiedene Dinge.

Das ist eine gute Nachricht: Benennung ist billiger zu reparieren als Architektur.

---

## 2. Die Methodenprüfung nach Krug

Krugs erstes Gesetz lautet: *Don't make me think.* Eine Oberfläche soll sich
selbst erklären, ohne dass jemand innehält und überlegt. Die folgenden sechs
Prüfungen sind seine, die Belege sind aus dieser Oberfläche.

### 2.1 Ist es selbsterklärend? — **nein, an den entscheidenden Stellen nicht**

> **Korrigiert am 2026-08-16, nach Prüfung am Code.** Hier stand zuerst, Menü
> und Seitentitel widersprächen sich bei `/app/leads`. Das war falsch: Ich hatte
> die Adresse von Hand aufgerufen. Die gerenderte Navigation
> (`AppLayout.jsx:342`) führt *Projekte → Projektpipeline* korrekt dorthin. Was
> stattdessen stimmt, steht unten — schmaler, aber belegt.

Der Widerspruch existiert, nur an anderer Stelle:

> **Menü: „Leads → Pipeline"** · **Adresse: `/app/deals`** · **Seitentitel:
> „💼 Deals"**

Zwei Wörter für einen Bildschirm. Und ein zweiter, leiserer Fall daneben: Die
Adresse **`/app/leads`** und die Komponente **`LeadPipeline`** liefern die
**Projekt**pipeline. Das Menü stimmt; die Adresse und der Name im Code tun es
nicht. Das trifft Lesezeichen, geteilte Links und jeden, der den Code liest —
mich eingeschlossen, wie man oben sieht.

Der teure Fehler nach Krug ist nicht der einzelne Widerspruch, sondern das
Muster dahinter: Für denselben Gegenstand liegen mehrere Wörter im Umlauf, und
keines gilt überall.

Der zweite Fall ist ein Menüpunkt namens **„Kompagnon"** — der eigene
Firmenname als Rubrik im eigenen Produkt. Darunter liegen sieben Einträge, die
nichts miteinander zu tun haben: *Tickets, Templates, Produkt-Editor, Produkte,
Produktentwicklung, QR-Generator, Retainer*. Das ist die klassische
„Verschiedenes"-Schublade. Sie entsteht immer aus derselben Ursache — etwas
passte nirgends, also kam es hierher — und sie wächst, weil sie einmal da ist.

Darin außerdem drei Nachbarn: **Produkt-Editor**, **Produkte**,
**Produktentwicklung**. Welcher davon bearbeitet ein Produkt? Das ist eine
Denkpause, und zwar bei jedem einzelnen Aufruf.

### 2.2 Sprechen alle Bildschirme dieselbe Sprache? — **nein**

Dasselbe Objekt trägt im System **vier Namen**:

| Ort | Wort |
|---|---|
| Menügruppe | **Lead** |
| Menüeintrag und Listentitel | **Unternehmen** |
| Zweite Liste unter `/app/customers` | **Kunde** |
| Kopfzeile der Einzelansicht | **Kundenkartei** |

Ein Betrieb, der noch nichts gekauft hat, heißt hier abwechselnd Lead,
Unternehmen, Kunde und Kartei. Nach Krug ist das der teuerste Fehler überhaupt,
weil er sich nicht wegklicken lässt: Der Nutzer muss die Übersetzung dauerhaft
im Kopf behalten.

Dazu kommt eine zweite Sprachebene, die gar nicht für Menschen gedacht war.
In der Liste „Unternehmen" stehen die Statuswerte **roh aus der Datenbank**:

```
new          won          proposal_sent
domain_import          landing_audit          Audit
```

Englisch, teils mit Unterstrich, teils groß, teils klein — in einer deutschen
Oberfläche. Zwei Bildschirme weiter, in „Kunden", stehen für dieselben Zustände
**deutsche** Wörter: *Neu, Gewonnen, Angebot*. Es gibt also bereits eine
Übersetzung; sie ist nur nicht überall angeschlossen.

Und an einer Stelle spricht die Oberfläche endgültig Maschine:

```
[Auto-Enrichment] SSL: OK | Impressum: FEHLT | PageSpeed: 0/100 |
Score: 40/100  Audit-Ergebnis: 37/100 Punkte - Nicht konform
```

Das ist eine Protokollzeile, gerendert als Fließtext in der Kundenkartei. Sie
enthält obendrein **zwei verschiedene Punktzahlen** (40 und 37) ohne ein Wort
dazu, welche was ist. Direkt daneben steht als Datum: **„Invalid Date"**.

**Und es ist schlimmer als ein Anzeigefehler.** Am Code nachgesehen:
`services/lead_enrichment.py:125` schreibt diese Zeile in **`lead.notes`** —
das Feld für die eigenen internen Notizen — und stellt sie dem voran, was ein
Mensch dort geschrieben hat. `LeadProfile.jsx:1379` zeigt sie nur getreu an.
Die Maschine schreibt also in ein Menschenfeld, dauerhaft, bei jeder
Anreicherung.

### 2.3 Führt die visuelle Gewichtung? — **nein, sie führt in die Irre**

Auf dem Dashboard gilt: **je wichtiger die Zahl, desto schlechter lesbar.**

- Die drei Kacheln „Heute gewonnen", „Diesen Monat", „Pipeline offen" stehen
  ganz oben, in großer heller Schrift — und zeigen **dreimal `0,00 €`**.
- Die vier Kacheln darunter tragen die Zahlen, die tatsächlich etwas sagen —
  **61 Leads, 2 Audits, Ø 53/100, 6 gewonnen** — in einer dekorativen,
  kursiven, kontrastarmen Schrift, halb so groß.
- Die Abschnittsüberschriften **„DASHBOARD", „AKTUELLE LEADS", „LETZTE
  AUDITS"** sind so kontrastarm gesetzt, dass sie beim Überfliegen praktisch
  verschwinden.

Krugs Prüfung ist das Überfliegen: Wer den Bildschirm zwei Sekunden ansieht,
soll die Struktur sehen. Hier sieht er drei Nullen.

Dasselbe Muster kleiner: In der Kundenkartei ist der Knopf **„Vollständigen
Bericht anzeigen"** so dunkel auf dunkel gesetzt, dass er deaktiviert wirkt. Er
ist es nicht.

### 2.4 Werden Konventionen eingehalten? — **überwiegend ja, mit einem Bruch**

Positiv: Brotkrumen sind vorhanden (`Unternehmen › Eiscafé Brustolon`), Tabellen
sind sortierbar, die Suche steht, wo man sie erwartet, das Nutzerkonto sitzt
unten links.

Der Bruch ist grundsätzlicher Art: **Das Tool ist dunkel, das Kundenportal ist
hell.** Nicht als Wahlmöglichkeit, sondern als zwei verschiedene Gestaltungen.
Die Anmeldung des Kundenportals führt zusätzlich eine dritte Domain im Fuß
(`kompagnon.eu`), während das Tool auf `kompagnon.group` läuft. Für den Kunden
ist das nicht dasselbe Haus.

### 2.5 Wie viel Rauschen? — **zu viel, und es ist vermeidbar**

Auf **jedem** Bildschirm steht die Überschrift zweimal: einmal in der schmalen
Leiste oben, einmal groß darunter. Auf der Projektpipeline stehen zusätzlich
die Spaltennamen doppelt — erst als Zusammenfassungsreihe (*Onboarding 16,
Briefing 3, Content 0 …*), dann als Spaltenköpfe (*ONBOARDING 16, BRIEFING 3 …*).
Und auf jeder Karte darin noch einmal die Phase, in deren Spalte sie ohnehin
liegt: *„Phase 1 von 7 · Onboarding"*.

In der Kundenkartei stehen **zehn Reiter** nebeneinander (Übersicht, Deals,
Nachrichten, Kontakt, Audits, Dateien, Akademy, Angebot, Zugang, E-Mails) und
darüber **fünf gleichrangige Knöpfe** plus ein Statusfeld. Keiner der Knöpfe
ist als der eine hervorgehoben, den man normalerweise drückt. Zwei davon —
**„Audit starten"** und **„Neu prüfen"** — unterscheiden sich in nichts, was
man sehen könnte.

Nebenbei: Auf dem Reiter steht **„Akademy"**. Weder deutsch noch englisch.

### 2.6 Der Trunk-Test — **fällt durch**

Krugs Prüfung: Man wird mit verbundenen Augen an einer beliebigen Stelle der
Website abgesetzt und muss beantworten können — *Wo bin ich? Was kann ich hier?
Wie komme ich woandershin?*

Auf `/app/customers` misslingt das doppelt. Der Bildschirm heißt **„Kunden"**,
zeigt **50 Einträge**, hat Kennzahlen, Filterchips und deutsche Statuswörter —
er ist die **am besten gestaltete Liste im ganzen System**. Und er hat
**keinen einzigen Menüeintrag**. Man kann ihn nur erreichen, wenn man die
Adresse kennt.

Gleichzeitig gibt es unter `/app/companies` die Liste **„Unternehmen"** mit
**61 Einträgen** derselben Firmen — schlechter beschriftet, aber im Menü.

Zwei Listen für dieselbe Sache, und die bessere ist die unsichtbare.

---

## 3. Die Nutzerreisen: Soll und Ist

### Reise A — Öffentlichkeit: vom Widget zum Bericht · 🟢

**Soll:** Ein Interessent gibt Adresse und Website ein, bekommt sofort einen
Eindruck, bestätigt seine Adresse und erhält den vollständigen Bericht.

**Ist:** Genau das. Am 16.08. vollständig durchgemessen — Widget → API → Audit
in 60 Sekunden → Bestätigungsmail → Bericht. Der Teaser zeigt drei Befunde und
hält den Rest zurück, bis die Adresse bestätigt ist.

**Warum das der beste Teil ist:** Er hat genau **eine** Aufgabe und keine
Alternative. Ein Feld, ein Knopf, ein erwartbares Ergebnis. Das ist Krugs Ideal,
und es ist hier ohne Absicht entstanden — die Enge des Anwendungsfalls hat die
Gestaltung erzwungen.

**Der eine Riss:** Nach der Analyse steht dort *„Wir haben eine kurze
Bestätigungs-Mail an … geschickt."* Scheitert der Versand, steht der Satz
trotzdem da. Am 16.08. genau so passiert (Brevo wies die Server-IP ab). Der
Server weiß es, die Oberfläche sagt es nicht.

### Reise B — Betreiber: von der Adresse zum Projekt · 🟠

**Soll:** Adressen importieren → bewerten lassen → die aussichtsreichen
ansprechen → Angebot → Projekt → Übergabe.

**Ist:** Alle Schritte existieren, aber die Reise ist an drei Stellen
unterbrochen — nicht funktional, sondern begrifflich:

1. **Nach dem Import** ist unklar, wo die importierten Betriebe landen. Unter
   „Leads → Pipeline"? Dort stehen Projekte. Unter „Leads → Unternehmen"? Ja —
   aber das Wort führt weg vom Begriff „Lead", mit dem der Import beschriftet ist.
2. **In der Kundenkartei** ist unklar, was der nächste Schritt ist. Fünf
   gleichrangige Knöpfe, zehn Reiter, kein Vorschlag.
3. **Zwischen Lead und Kunde** gibt es zwei Listen mit unterschiedlichem
   Bestand (61 vs. 50) und unterschiedlicher Sprache. Wann wird aus dem einen
   das andere? Der Bildschirm sagt es nicht.

**Was gut funktioniert:** Das Audit-Tool. Ein Feld, ein Knopf, ein Ergebnis —
dieselbe Klarheit wie das öffentliche Widget, aus demselben Grund.

### Reise C — Kunde: Portal, Freigaben, Rechnungen · 🟡

**Soll:** Der Kunde meldet sich an, sieht den Stand seines Projekts, gibt
Inhalte frei, findet seine Rechnungen.

**Ist:** Die Anmeldung ist ruhig und erklärt sogar, woher die Zugangsdaten
kommen (*„Zugangsdaten erhalten Sie per E-Mail nach Ihrem Kauf"*) — vorbildlich,
weil sie eine Frage beantwortet, bevor sie entsteht.

**Aber es ist ein anderes Produkt.** Helles Layout, andere Markenfarbe, andere
Domain im Fuß. Wer vom Bericht (dunkel, KOMPAGNON-Teal) ins Portal wechselt,
kommt woanders an. Für ein Produkt, dessen Verkaufsargument handwerkliche
Sorgfalt ist, ist das der falsche erste Eindruck nach dem Kauf.

Die Reiseabschnitte *Freigaben* und *Rechnungen* existieren als Routen, sind
aber im Menü des Betreibers nicht sichtbar — ob der Kunde sie in seinem eigenen
Menü findet, ist an dieser Stelle **nicht geprüft** (Abschnitt 7).

---

## 4. Was die Oberfläche über die Daten verrät

Krug betrachtet Gestaltung, aber eine Oberfläche zeigt auch, was dahinter
liegt. Hier zeigt sie unfertige Daten — und das trifft die Glaubwürdigkeit
härter als jede Farbwahl, weil der Betreiber diese Listen vor Kunden öffnet.

| Beleg | Was man sieht |
|---|---|
| `adrian-vidak.de`, `bb-foto.de`, `dennisaden.com` | Domains stehen als **Firmenname** in der Hauptspalte |
| **„gibts nicht dachdeckerei-heinen.de"** | Eine Notiz ist zum Firmennamen geworden |
| **ECO-VOX** zweimal, beide `eco-vox.com` | Dublette ohne Hinweis |
| Ort: **„News"** (Faust Klimatechnik) | Vermutlich Neuss — niemand hat es gesehen |
| Projekt **„KOMPAGNON"**, Website `kompagnon-frontend.onrender.com` | Testdatensatz in der Produktivliste |
| **„PageSpeed: 0/100"** | Vermutlich *nicht erhoben*, angezeigt als Null — dieselbe Bauart wie die Befunde vom 15.08. |

Ein Punkt, den ich zuerst für einen Rechenfehler hielt und der keiner ist:
Unter „Leads nach Herkunft" steht *„Direkt · 60 Leads · 10 %"*. 60 von 61 sind
98 %, nicht 10 %. Die 10 % sind die **Gewinnquote** (6 von 60) — richtig
gerechnet, aber **die Spalte hat keine Überschrift**. Eine korrekte Zahl, die
zum Fehlschluss einlädt, ist nach Krug schlimmer als eine fehlende.

---

## 5. Befundliste

Priorität: **P0** = Nutzer wird in die Irre geführt · **P1** = kostet bei jedem
Aufruf Zeit · **P2** = Politur.

### P0 — Führt in die Irre

| ID | Befund | Beleg |
|---|---|---|
| UX-01 | Nav-Eintrag „Leads → Pipeline" öffnet eine Seite mit dem Titel **„💼 Deals"** — zwei Wörter für einen Bildschirm | `/app/deals`, `AppLayout.jsx:360` |
| UX-01b | Adresse `/app/leads` und Komponente `LeadPipeline` liefern die **Projekt**pipeline. Menü korrekt, Adresse und Codename nicht | `App.jsx:192` |
| UX-02 | **Zwei Listen** für dieselben Firmen: „Unternehmen" (61) und „Kunden" (50), verschiedene Sprache und Umfang | `/app/companies`, `/app/customers` |
| UX-03 | Die besser gestaltete der beiden Listen hat **keinen Menüeintrag** | `/app/customers` |
| UX-04 | **Vier Namen** für ein Objekt: Lead, Unternehmen, Kunde, Kundenkartei | durchgängig |
| UX-05 | **„Invalid Date"** als sichtbarer Text | Kundenkartei, „Letzter Audit" |
| UX-06 | **Protokollzeile im Notizfeld des Nutzers.** Kein Anzeigefehler: `lead_enrichment.py:125` schreibt sie in `lead.notes` und stellt sie dem voran, was ein Mensch dort geschrieben hat | `services/lead_enrichment.py:125`, `LeadProfile.jsx:1379` |
| UX-06b | Zwei Punktzahlen ohne Unterscheidung — 40 (Lead) und 37 (Audit) unbeschriftet nebeneinander | Kundenkartei, Übersicht |
| UX-29 | `components/Sidebar.jsx` ist eine **zweite, tote** Navigationsdefinition — nirgends importiert, inhaltlich abweichend. Wer sie beim Aufräumen findet, ändert die falsche Datei | `components/Sidebar.jsx` |
| UX-07 | Rohe Datenbankwerte als Status: `new`, `won`, `proposal_sent`, `domain_import` | `/app/companies` |
| UX-08 | Widget meldet **Mailversand-Erfolg auch bei Fehlschlag** | Widget-Ergebnis |
| UX-09 | Prozentspalte **ohne Überschrift** — korrekte Zahl, falscher Schluss | Dashboard, „Leads nach Herkunft" |

### P1 — Kostet bei jedem Aufruf Zeit

| ID | Befund | Beleg |
|---|---|---|
| UX-10 | **Kein Ladezustand**: Kacheln stehen leer da und lesen sich wie „null", bis die Werte nachkommen | Dashboard |
| UX-11 | Wichtige Kennzahlen **kontrastarm und dekorativ**, drei Nullwerte dominieren | Dashboard |
| UX-12 | Abschnittsüberschriften beim Überfliegen **unsichtbar** | Dashboard, Pipeline |
| UX-13 | **Fünf gleichrangige Knöpfe**, keine Primäraktion | Kundenkartei |
| UX-14 | **„Audit starten" vs. „Neu prüfen"** — Unterschied nicht erkennbar | Kundenkartei |
| UX-15 | **Zehn Reiter** nebeneinander | Kundenkartei |
| UX-16 | „Kompagnon" als **Sammelbecken** für sieben unverwandte Einträge | Hauptmenü |
| UX-17 | **Produkt-Editor / Produkte / Produktentwicklung** nebeneinander | Hauptmenü |
| UX-18 | Knopf **„Vollständigen Bericht anzeigen"** wirkt deaktiviert | Kundenkartei |
| UX-19 | **Bruch hell/dunkel** zwischen Tool und Kundenportal, dazu dritte Domain im Fuß | `/kundenportal` |

### P2 — Politur

| ID | Befund |
|---|---|
| UX-20 | Überschrift auf **jedem** Bildschirm doppelt (Leiste + H1) |
| UX-21 | Spaltenköpfe der Pipeline doppelt, Phase auf der Karte ein drittes Mal |
| UX-22 | **„Akademy"** — Schreibweise weder deutsch noch englisch |
| UX-23 | „+ Neues Audit" auf dem Bildschirm, der selbst das neue Audit ist |
| UX-24 | „Zurück"-Knopf **zusätzlich** zur Brotkrume |
| UX-25 | Feldbeschriftung **„Geschäftsführer (auto)"** — interne Herkunft im Kundenblick |
| UX-26 | Leeres Formular „Weitere Domains" nimmt Platz auf der Übersicht |
| UX-27 | Audit-Tool zeigt **keine früheren Audits**, obwohl das Dashboard sie führt |
| UX-28 | Score-Balken **ohne Legende** — Schwellen unerklärt |

---

## 6. Empfehlung: die Reihenfolge

> Als abzuarbeitende Liste mit Fundstellen und Prüfschritt:
> **`docs/ux-arbeitsliste.md`**.

Nicht nach Aufwand sortiert, sondern nach Wirkung pro Eingriff.

**Erstens — ein Wort pro Sache** (UX-04, UX-07, UX-01).
Entscheide **ein** Vokabular und ziehe es durch: Menü, Titel, Adresse,
Statuswerte. Die deutsche Übersetzung existiert bereits in „Kunden"; sie muss
nur überall angeschlossen werden. Das ist der billigste Eingriff mit der
größten Wirkung, weil er den dauerhaften Übersetzungsaufwand im Kopf beendet.

**Zweitens — eine Liste statt zwei** (UX-02, UX-03).
„Kunden" ist die bessere Gestaltung. Sie zu behalten und „Unternehmen"
abzulösen ist weniger Arbeit als beide zu pflegen — und beseitigt die Frage,
welche der beiden stimmt.

**Drittens — nichts behaupten, was nicht stimmt** (UX-05, UX-06, UX-08, UX-09).
„Invalid Date", die Protokollzeile, die Erfolgsmeldung bei gescheitertem
Versand, die Prozentspalte ohne Überschrift. Vier kleine Eingriffe, gleiche
Ursache: Die Oberfläche sagt etwas anderes als das System weiß. Das ist
dieselbe Bauart wie die Befunde der letzten Tage — und dieselbe Gefahr, weil
nichts davon laut scheitert.

**Viertens — eine Primäraktion je Bildschirm** (UX-13, UX-14, UX-11).
Auf der Kundenkartei: Was ist der nächste Schritt? Genau der bekommt Farbe, der
Rest wird ruhig. Auf dem Dashboard: Die Zahl, die zählt, wird groß und lesbar;
die drei Nullen werden klein.

**Fünftens — das Sammelbecken auflösen** (UX-16, UX-17).
„Kompagnon" ist keine Rubrik. Die sieben Einträge gehören verteilt oder
umbenannt.

**Später, aber nicht vergessen — eine Welt statt zwei** (UX-19).
Der Bruch zwischen Tool und Kundenportal ist der größte Eingriff auf dieser
Liste und der einzige, der wirklich Gestaltungsarbeit ist. Er wirkt aber genau
dort, wo es ums Geld geht: im ersten Eindruck nach dem Kauf.

---

## 7. Was diese Analyse nicht abdeckt

Damit niemand aus dem Schweigen ein „in Ordnung" liest:

- **Academy-Verwaltung** (14 Routen), **Mobil-Ansichten** (5), **Newsletter-
  Designer**, **Template-Editor**, **Component-Library**, **Online-fertig-
  Editor** — nicht einzeln angesehen
- **Das Kundenportal von innen** — nur die Anmeldung geprüft, nicht der
  angemeldete Zustand. Dafür braucht es einen echten Kundenzugang
- **Barrierefreiheit** — hier nicht gemessen. Die Lückenliste führt sie als
  L-17 (12 von 167 Dateien mit ARIA) bei verkaufter BFSG-Konformität. Die
  Kontrastbefunde oben (UX-11, UX-12, UX-18) sind Vorboten davon, aber keine
  Prüfung
- **Verhalten auf kleinen Bildschirmen** — durchgängig am Desktop erhoben
- **Ladezeiten als Erlebnis** — das Backend antwortet produktiv in 0,9–2,6 s
  (L-34, Umzug nach Frankfurt offen). Wie sich das über die Reisen hinweg
  anfühlt, ist eine eigene Messung

---

*Erhoben 2026-08-16 an `kas.kompagnon.group`, Produktivstand `ee08ddc`.*
