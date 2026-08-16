# KAS-Oberfläche — Arbeitsliste

> Abzuarbeiten. Grundlage: `ux-soll-ist-kas.md` (Prüfung vom 2026-08-16).
> Jeder Punkt nennt **wo** man anfängt und **woran** man sieht, dass er
> erledigt ist. Reihenfolge nach Wirkung, nicht nach Aufwand.
>
> Aufwand: **S** ≤ 1 Std · **M** ≤ ½ Tag · **L** ≥ 1 Tag

---

## Korrektur vorweg

**UX-01 stand in der Analyse zunächst falsch.** Ich hatte `/app/leads` von
Hand aufgerufen und daraus geschlossen, Menü und Titel widersprächen sich. Sie
tun es nicht: Die gerenderte Navigation (`AppLayout.jsx:342`) führt
*Projekte → Projektpipeline* korrekt auf `/app/leads`.

Was **stattdessen** stimmt, steht unten als UX-01 und UX-01b — schmaler, aber
belegt. Dazu ein neuer Fund beim Nachsehen: UX-29.

---

## Paket 1 — Ein Wort pro Sache

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

- [ ] **UX-01b** · **M** · Die Adresse `/app/leads` liefert die **Projekt**pipeline,
      die Komponente heißt `LeadPipeline`. Das Menü stimmt; Adresse und Codename
      nicht. Betrifft Lesezeichen, geteilte Links und jeden, der den Code liest.
      → `App.jsx:192`, Komponente umbenennen; alte Adresse als Weiterleitung
      stehen lassen
      **Bewusst zurückgestellt (2026-08-16):** `/app/leads` ist an **zehn**
      Stellen in `AppLayout.jsx` verdrahtet, teils mit Sonderlogik für die
      Menü-Hervorhebung (Zeilen 251, 693, 977). Das braucht eine Sichtprüfung
      am laufenden Bildschirm, und die war nicht möglich.
      *Prüfung:* `/app/projekte/pipeline` (o. ä.) zeigt die Projektpipeline,
      `/app/leads` leitet dorthin um — **und die Menü-Hervorhebung stimmt
      weiterhin auf allen betroffenen Seiten.**

---

## Paket 2 — Eine Liste statt zwei

*„Kunden" ist die bessere Gestaltung. Beide zu pflegen kostet mehr, als eine
abzulösen.*

- [ ] **UX-02** · **M** · Zwei Listen derselben Firmen zusammenführen:
      „Unternehmen" (`/app/companies`, 61 Einträge, rohe Statuswerte) und
      „Kunden" (`/app/customers`, 50 Einträge, deutsche Labels, Filterchips,
      Kennzahlen).
      **Vorher klären:** Warum 61 gegen 50? Wenn „Kunden" filtert, muss der
      Filter sichtbar sein — sonst wirkt die Liste unvollständig.
      *Prüfung:* Eine Liste, eine Zahl, ein Filter, der benannt ist.

- [ ] **UX-03** · **S** · Der bessere der beiden Bildschirme hat **keinen
      Menüeintrag** und ist nur über die Adresse erreichbar.
      → `AppLayout.jsx:355 ff.` (Gruppe `leads`)
      *Prüfung:* Jeder erreichbare Bildschirm hat einen Weg im Menü — oder wird
      abgeschaltet.

- [ ] **UX-29** · **S** · *(offen)* `components/Sidebar.jsx` ist eine **zweite, tote**
      Navigationsdefinition — nirgends importiert, aber inhaltlich abweichend.
      Wer sie beim Aufräumen findet, ändert die falsche Datei.
      *Prüfung:* Datei gelöscht, Frontend baut, 98 Tests grün.

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
