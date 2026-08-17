# KAS-Oberfläche — Arbeitsliste

> Abzuarbeiten. Grundlage: `ux-soll-ist-kas.md` (Prüfung vom 2026-08-16).
> Jeder Punkt nennt **wo** man anfängt und **woran** man sieht, dass er
> erledigt ist. Reihenfolge nach Wirkung, nicht nach Aufwand.
>
> Aufwand: **S** ≤ 1 Std · **M** ≤ ½ Tag · **L** ≥ 1 Tag
>
> **Stand 2026-08-17:** Paket 1 und **Paket 2** sind abgeschlossen. Paket 2
> brachte drei ungesuchte Funde mit (UX-30 bis UX-32), alle erledigt. Alles
> liegt auf `staging` — **produktiv ist nichts davon**, das geht mit dem
> nächsten Sammel-PR. Weiter geht es mit **Paket 3**.

---

## Korrektur vorweg

**UX-01 stand in der Analyse zunächst falsch.** Ich hatte `/app/leads` von
Hand aufgerufen und daraus geschlossen, Menü und Titel widersprächen sich. Sie
tun es nicht: Die gerenderte Navigation (`AppLayout.jsx:342`) führt
*Projekte → Projektpipeline* korrekt auf `/app/leads`.

Was **stattdessen** stimmt, steht unten als UX-01 und UX-01b — schmaler, aber
belegt. Dazu ein neuer Fund beim Nachsehen: UX-29.

---

## Paket 1 — Ein Wort pro Sache · ✅ ABGESCHLOSSEN 2026-08-16

*Der billigste Eingriff mit der größten Wirkung. Beendet den dauerhaften
Übersetzungsaufwand im Kopf.*

- [x] **UX-04** · **M** · ~~Ein Vokabular festlegen und durchziehen~~
      **erledigt 2026-08-16: „Betrieb".** Entschieden von David, gestützt auf
      die kundenseitige Sprache — 2:1 im Mail- und Berichtscode, 5:0 im
      Anforderungskatalog und in der Conversion-Spec. Innen und außen sprechen
      jetzt dasselbe Wort.
      **Geändert:** Menüeintrag *Unternehmen* → **Betriebe**, Brotkrume,
      Seitentitel, Anlegen-Knopf und -Dialog, Kopfzeile der Einzelansicht
      *Kundenkartei* → **Betrieb**, Abschnittsbeschriftungen und die
      Spaltenüberschrift in „Kunden".
      **Und die Menügruppe:** *Leads* → **Vertrieb**. „Lead" ist ein Zustand,
      kein Objekt — die Gruppe benennt jetzt, worum es geht, nicht in welchem
      Zustand etwas ist.
      **Bewusst nicht geändert:** Der Seitentitel „Kunden" auf
      `/app/customers`. Zwei Bildschirme namens „Betriebe" wären eine neue
      Verwechslung; der Bildschirm verschwindet ohnehin mit UX-02.
      Das Feldlabel „Firma" bleibt — es benennt ein Feld, nicht das Objekt.

- [x] **UX-07** · **S** · ~~Statuswerte übersetzen~~ **erledigt 2026-08-16.** Statuswerte übersetzen statt roh anzeigen:
      `new`, `won`, `proposal_sent`, `domain_import`, `landing_audit`.
      Die Übersetzung **existiert bereits** in „Kunden" (Neu, Gewonnen,
      Angebot) — sie muss nur an einer Stelle liegen und überall gelten.
      **Gemacht:** `utils/leadStatus.js` als einzige Quelle — Labels, Varianten
      und Herkunft. `Companies.jsx` nutzt jetzt den `Badge`-Baustein statt
      sechs fest eingetragener Hex-Farben, `Customers.jsx` importiert dieselbe
      Abbildung statt einer eigenen.
      **Dabei zwei stille Fehler gefunden:** `proposal_sent` fehlte in der
      Farbabbildung von `Companies.jsx` — deshalb stand dieser Status ohne
      Rahmen da. Und `Customers.jsx:224` zeigte jeden **unbekannten** Status als
      „Neu" an (`STATUS[x] || STATUS.new`).
      10 neue Tests, 108 Frontend-Tests grün.

- [x] **UX-01** · **S** · ~~Nav-Eintrag~~ **erledigt 2026-08-16.** Nav-Eintrag *„Leads → Pipeline"* öffnet eine Seite mit
      dem Titel **„💼 Deals"**. Entweder das Menü heißt „Deals" oder die Seite
      heißt „Pipeline" — nicht beides.
      **Gemacht:** Menü heißt jetzt „Deals", wie die Seite. Zweiter Grund für
      diese Richtung: „Pipeline" kam im Menü **zweimal** vor — hier und als
      „Projektpipeline" unter Projekte. Ein Wort, zwei Orte, zwei Bedeutungen.
      → `AppLayout.jsx:366`

- [x] **UX-01b** · **M** · ~~Adresse und Codename sagen „Leads", der Inhalt sind
      Projekte~~ **erledigt 2026-08-16, zu zweit am Bildschirm geprüft.**
      **Neu:** `/app/betriebe` (Liste), `/app/betriebe/:id` (Einzelansicht),
      `/app/projektpipeline` (Pipeline). Alle drei alten Adressen leiten weiter;
      die Detail-Weiterleitung nimmt die **Kennung mit** — sonst landet jeder
      geteilte Link auf der Liste. Komponente `LeadPipeline` → `Projektpipeline`.
      **Drei Sonderfälle ersatzlos entfallen**, weil sie nur die irreführende
      Adresse ausglichen: der `isActive`-Sonderfall, die Mobilnav-Zeile (die
      auf die Projektpipeline zeigte *und* für die Betriebsliste leuchtete) und
      der Knopf **„+ Neuer Lead"** auf der Projektpipeline.
      **Vorher am laufenden System geprüft**, dass alle drei sich genau so
      verhalten, wie der Code sagt — deshalb war das Entfernen belegt, nicht
      gehofft.

- [x] **Nachtrag** · ~~Seitenleiste blieb nach einer Weiterleitung ganz
      zugeklappt~~ **erledigt 2026-08-16.** Beim gemeinsamen Nachsehen
      aufgefallen: Über `/app/leads` ankommend zeigte die Navigation **nicht,
      wo man ist** — direkt aufgerufen schon. `getDefaultOpen` lief nur einmal
      beim Aufbau und sah die Adresse *vor* der Weiterleitung.
      **Kein neuer Fehler:** `/app/sales → /app/deals` hat das seit jeher; die
      neue Weiterleitung hat es nur sichtbar gemacht. Die offene Gruppe folgt
      jetzt der Adresse und **öffnet nur, schließt nie**.
      *Der Punkt daran:* Tests grün, Build sauber, Code korrekt — und die
      Navigation trotzdem blind. Das hätte kein Test gefunden.

- [x] **Nachtrag** · ~~Quelle `embed_audit` erschien als „Embed audit"~~
      **erledigt 2026-08-16.** Der Rückfall in `leadStatus.js` machte den Wert
      lesbar, aber halb englisch — genau wie gebaut: Er verrät sich, statt zu
      tarnen. Heißt jetzt **Analyse-Widget**. 109 Frontend-Tests grün.

---

## Paket 2 — Eine Liste statt zwei · ✅ ABGESCHLOSSEN 2026-08-17

*„Kunden" ist die bessere Gestaltung. Beide zu pflegen kostet mehr, als eine
abzulösen.*

- [x] **UX-02** · **M** · ~~Zwei Listen derselben Firmen zusammenführen~~
      **erledigt 2026-08-17.**

      **Die Vorfrage zuerst — warum 61 gegen 50? Es war kein Filter.** Beide
      Seiten riefen dieselbe Schnittstelle auf, nur eine nannte eine Obergrenze:
      „Unternehmen" `/api/leads/?limit=1000`, „Kunden" `/api/leads/` — und bekam
      damit die Voreinstellung des Servers, **50** (`routers/leads.py:249`).
      Elf Betriebe fehlten still. Schlimmer als die Lücke war, was darüber stand:
      Die Kacheln „Gesamt", „Mit Score" und „Ø Score" rechneten über die
      abgeschnittene Liste. **Eine abgeschnittene Zahl, die „Gesamt" heißt, ist
      schlechter als gar keine** — sie sieht nicht aus wie eine Lücke.

      **Gemacht:** Ein Bildschirm, `/app/betriebe` — die Gestaltung von „Kunden"
      mit den Funktionen von „Unternehmen":
      Kennzahlen, Statusfilter, Suche und Sortierung von dort; Anlegen-Dialog
      und Quellenfilter von hier. `/app/customers` und `/app/companies` leiten
      weiter (es gibt Lesezeichen). `Companies.jsx` und `Customers.jsx` gelöscht.
      Die Listenlogik liegt in **`utils/betriebeListe.js`** und ist damit prüfbar
      — sie lag vorher doppelt vor und lief auseinander.

      **Der Filter ist benannt:** Über der Liste steht „12 von 61 Betrieben ·
      Suche: … · Status: … · Quelle: …" mit einem Knopf „Filter zurücksetzen".
      Ist nichts gefiltert, steht dort schlicht „61 Betriebe" — keine Zahl ohne
      ihren Bezug.

      **Der Quellenfilter kommt jetzt aus den Daten.** Vorher standen dort drei
      fest eingetragene Optionen, während Quellen Freitext sind
      (Kampagnennamen). Alle übrigen fehlten: Man konnte nicht nach ihnen filtern
      und sah nicht, dass es sie gibt. Jetzt wird die Auswahl aus der Liste
      abgeleitet, nach Häufigkeit, mit Anzahl.

      **Und der Deckel wird gemeldet:** Kommen genau 1000 Datensätze zurück,
      sagt die Seite es. Ein stiller Deckel ist derselbe Fehler wie das fehlende
      `limit`, nur eine Null später.

- [x] **UX-03** · **S** · ~~Der bessere Bildschirm hat keinen Menüeintrag~~
      **erledigt 2026-08-17, mit UX-02.** Erledigt sich durch das
      Zusammenlegen: Was übrig bleibt, liegt auf `/app/betriebe`, und das steht
      im Menü unter *Vertrieb → Betriebe*. Kein erreichbarer Bildschirm ohne Weg
      dorthin.

- [x] **UX-29** · **S** · ~~`components/Sidebar.jsx` ist eine zweite, tote
      Navigationsdefinition~~ **erledigt 2026-08-17.** Gelöscht.
      **Beim Nachsehen fand sich eine dritte** — siehe UX-30.

### Drei Funde, die beim Zusammenlegen mit herausfielen

*Nicht gesucht, sondern beim Hinsehen aufgefallen. Alle drei sind erledigt.*

- [x] **UX-30** · **Eine dritte tote Navigation, in der echten Datei.**
      `NAV_SECTIONS` stand in `AppLayout.jsx` oben, sieben Gruppen lang, nie
      importiert und inhaltlich abweichend von der Navigation, die zwanzig
      Zeilen weiter unten tatsächlich gerendert wird. Der Linter meldete sie
      seit jeher als ungenutzt — die Meldung ging in den übrigen Warnungen
      unter. Entfernt.

- [x] **UX-31** · **Eine zurückgezogene Skala hatte überlebt.** Der Kreis vor
      dem Firmennamen trug Kürzel wie `Pt`, `Go`, `Si` nach der Staffelung
      85/70/50/30. Genau diese war gegen die Backend-Skala 95/85/70/50 getauscht
      worden, weil derselbe Score im Bericht „Silber" und im Widget „Gold" hieß
      — nachzulesen im Kopf von `utils/homepageStandard.js`. In dieser Liste
      stand sie weiter. **Ein Betrieb mit 86 Punkten trug „Pt", während sein
      Bericht „Homepage Standard Gold" sagt.**
      **Gemacht:** Die eigene Skala ist weg, gerechnet wird mit
      `stufeFuerScore`. Die Kürzel sind mit ihr entfallen — zwei Buchstaben ohne
      Legende sind nicht zu entschlüsseln (das war UX-28 in klein). Der Kreis
      zeigt jetzt den Anfangsbuchstaben, die Stufe steht am Score.
      *Offen geblieben und bewusst so:* Die Liste bekommt vom Server keine
      Stufe, nur den Score (`routers/leads.py:263 ff.`) — die K.-o.-Regeln
      (kein Impressum, kein TLS) kann sie deshalb nicht kennen. Das steht als
      Kommentar an der Stelle.

- [x] **UX-32** · **Ein Rest aus Paket 1.** Die Brotkrumenleiste suchte weiter
      `/app/leads/:id`. Seit der Umbenennung traf das nichts mehr, also stand
      auf der Seite eines Betriebs nur „Betriebe" — **ohne den Namen des
      Betriebs, auf dem man gerade war.** Kein Fehler, eine Auslassung; genau
      die Sorte, die man nur beim Hinsehen findet. Sucht jetzt
      `/app/betriebe/:id`.

---

## Paket 3 — Nichts behaupten, was nicht stimmt

*Vier kleine Eingriffe, eine Ursache: Die Oberfläche sagt etwas anderes, als das
System weiß. Dieselbe Bauart wie die stillen Fehler der Vortage.*

- [ ] **UX-05** · **S** · `Invalid Date` als sichtbarer Text. Ursache: das Datum
      wird ungeprüft formatiert.
      → `pages/LeadProfile.jsx:1516` —
      `new Date(latestAudit.created_at).toLocaleDateString('de-DE')` ohne Schutz
      **Regel dabei:** Fehlt das Datum, gehört dort *„Datum unbekannt"* hin —
      kein leeres Feld und keine erfundene Zeit.
      *Prüfung:* Ein Audit ohne `created_at` zeigt den Ersatztext.

- [ ] **UX-06** · **M** · Die `[Auto-Enrichment]`-Zeile ist **kein
      Anzeigefehler**. `services/lead_enrichment.py:125` schreibt sie in
      `lead.notes` — das Feld für *deine* Notizen — und stellt sie dem voran,
      was du dort geschrieben hast. `LeadProfile.jsx:1379` zeigt sie nur getreu.
      **Zu tun:** Maschinenbefunde in eigene Felder, nicht in ein Menschenfeld.
      Die Werte (SSL, Impressum, PageSpeed, Score) liegen ohnehin schon als
      Spalten vor.
      *Prüfung:* `lead.notes` enthält nach einer Anreicherung nur, was ein
      Mensch geschrieben hat.

- [ ] **UX-06b** · **S** · Zwei Punktzahlen ohne Unterscheidung: `Score: 40/100`
      (Lead) und `Audit-Ergebnis: 37/100` (Audit) stehen unbeschriftet
      nebeneinander. Beide brauchen ein Wort davor.
      *Prüfung:* Aus dem Bildschirm allein ist erkennbar, was 40 und was 37 ist.

- [ ] **UX-08** · **S** · Das Widget meldet „Bestätigungs-Mail geschickt", auch
      wenn der Versand scheitert. Der Server weiß es (`routers/audit.py`
      protokolliert „Widget-Bestätigung nicht versendet"), sagt es aber nicht
      weiter.
      **Zu tun:** Versandergebnis in die Antwort aufnehmen, das Widget zeigt bei
      Fehlschlag einen ehrlichen Satz plus Wiederholmöglichkeit.
      → `kompagnon/frontend/public/embed/audit-widget.html`
      *Prüfung:* Mit abgeschaltetem Versand erscheint keine Erfolgsmeldung.

- [ ] **UX-09** · **S** · Prozentspalte ohne Überschrift auf dem Dashboard. Die
      Zahl ist **richtig** (Gewinnquote, 6 von 60) — sie sieht nur wie ein
      Anteil aus.
      *Prüfung:* Über der Spalte steht „Gewinnquote".

- [ ] **UX-Daten** · **M** · Was die Listen über die Daten verraten, gehört
      separat angefasst — es trifft die Glaubwürdigkeit vor Kunden:
      Domains als Firmenname (`adrian-vidak.de`), eine Notiz als Firmenname
      (`gibts nicht dachdeckerei-heinen.de`), Dublette **ECO-VOX**, Ort `News`
      (vermutlich Neuss), Testdatensatz **KOMPAGNON** mit
      `kompagnon-frontend.onrender.com` in der Produktivliste.
      *Prüfung:* Kein Datensatz in der Liste, den man einem Kunden nicht zeigen
      würde.

---

## Paket 4 — Eine Primäraktion je Bildschirm

- [ ] **UX-13** · **S** · Fünf gleichrangige Knöpfe in der Kundenkartei
      (*Audit starten, Bearbeiten, Neu prüfen, Briefing starten, Projekt
      anlegen*). Einer bekommt Farbe — der, den man normalerweise drückt —,
      der Rest wird ruhig.
      *Prüfung:* Ein Blick genügt, um den nächsten Schritt zu erkennen.

- [ ] **UX-14** · **S** · „Audit starten" und „Neu prüfen" sind visuell und
      sprachlich nicht unterscheidbar. Entweder benennen, was sie unterscheidet,
      oder zusammenlegen.
      *Prüfung:* Aus den Beschriftungen allein ist der Unterschied erkennbar.

- [ ] **UX-11** · **M** · Auf dem Dashboard sind die Kennzahlen, die etwas
      sagen (61 Leads, 2 Audits, Ø 53/100, 6 gewonnen), kontrastarm und
      dekorativ gesetzt — während drei Kacheln mit `0,00 €` den Bildschirm
      beherrschen. Gewichtung umdrehen.
      *Prüfung:* Zwei Sekunden Hinsehen genügen für die wichtigste Zahl.

- [ ] **UX-12** · **S** · Abschnittsüberschriften („AKTUELLE LEADS", „LETZTE
      AUDITS") sind beim Überfliegen unsichtbar. Kontrast anheben.
      *Prüfung:* Die Struktur ist ohne Lesen erkennbar.

- [ ] **UX-10** · **S** · Kein Ladezustand: leere Kacheln lesen sich wie „null",
      bis die Werte nachkommen. Bei 0,9–2,6 s Antwortzeit ist das jedes Mal
      sichtbar.
      *Prüfung:* Während des Ladens steht dort ein Platzhalter, keine Leere.

- [ ] **UX-18** · **S** · Knopf „Vollständigen Bericht anzeigen" wirkt
      deaktiviert (dunkel auf dunkel). Er ist es nicht.
      *Prüfung:* Der Knopf sieht anklickbar aus.

- [ ] **UX-15** · **M** · Zehn Reiter in der Kundenkartei. Prüfen, welche
      zusammengehören und welche selten benutzt werden.
      *Prüfung:* Höchstens sechs Reiter, der Rest untergeordnet.

---

## Paket 5 — Das Sammelbecken auflösen

- [ ] **UX-16** · **M** · Menügruppe **„Kompagnon"** enthält sieben unverwandte
      Einträge (Tickets, Templates, Produkt-Editor, Produkte,
      Produktentwicklung, QR-Generator, Retainer) unter dem eigenen
      Firmennamen. Verteilen oder umbenennen — „Kompagnon" sagt nicht, was
      darin liegt.
      → `AppLayout.jsx:374 ff.`
      *Prüfung:* Jede Gruppe im Menü ist mit einem Wort beschreibbar.

- [ ] **UX-17** · **S** · **Produkt-Editor**, **Produkte** und
      **Produktentwicklung** stehen nebeneinander. Wer will was bearbeiten?
      *Prüfung:* Aus den drei Namen allein ist ableitbar, welcher wofür ist.

---

## Paket 6 — Politur

- [ ] **UX-20** · **S** · Überschrift auf **jedem** Bildschirm doppelt (obere
      Leiste und H1). Eine davon weg.
- [ ] **UX-21** · **S** · Spaltenköpfe der Projektpipeline doppelt, die Phase
      auf jeder Karte ein drittes Mal.
- [ ] **UX-22** · **S** · Reiter `Akademy` — weder deutsch noch englisch.
- [ ] **UX-23** · **S** · „+ Neues Audit" auf dem Bildschirm, der selbst das
      neue Audit ist.
- [ ] **UX-24** · **S** · „Zurück"-Knopf zusätzlich zur Brotkrume.
- [ ] **UX-25** · **S** · Feldbeschriftung „Geschäftsführer *(auto)*" — interne
      Herkunft im Kundenblick.
- [ ] **UX-26** · **S** · Leeres Formular „Weitere Domains" nimmt Platz auf der
      Übersicht.
- [ ] **UX-27** · **S** · Audit-Tool zeigt keine früheren Audits, obwohl das
      Dashboard sie führt.
- [ ] **UX-28** · **S** · Score-Balken ohne Legende — die Schwellen bleiben
      unerklärt.

---

## Paket 7 — Später: eine Welt statt zwei

- [ ] **UX-19** · **L** · Bruch hell/dunkel zwischen Tool und Kundenportal,
      dazu eine dritte Domain im Fuß (`kompagnon.eu`, während das Tool auf
      `kompagnon.group` läuft). Der größte Eingriff auf dieser Liste und der
      einzige, der echte Gestaltungsarbeit ist — wirkt aber dort, wo es ums
      Geld geht: im ersten Eindruck nach dem Kauf.
      *Prüfung:* Ein Kunde, der vom Bericht ins Portal wechselt, merkt keinen
      Hauswechsel.

---

## Noch nicht geprüft — vor dem Abhaken zu erheben

Diese Flächen sind nicht angesehen worden. Sie sind **nicht** „in Ordnung",
sondern unbekannt:

- [ ] Academy-Verwaltung (14 Routen), Mobil-Ansichten (5),
      Newsletter-Designer, Template-Editor, Component-Library,
      Online-fertig-Editor
- [ ] Das Kundenportal **von innen** — braucht einen echten Kundenzugang
- [ ] Barrierefreiheit — hier nicht gemessen; die Lückenliste führt sie als
      L-17 (12 von 167 Dateien mit ARIA) bei verkaufter BFSG-Konformität.
      Die Kontrastpunkte UX-11, UX-12 und UX-18 sind Vorboten, keine Prüfung
- [ ] Verhalten auf kleinen Bildschirmen
- [ ] Ladezeit als Erlebnis über eine ganze Reise (hängt an L-34)

---

*Angelegt 2026-08-16. Stand der Prüfung: `ee08ddc`.*
