# KAS-Oberfläche — Arbeitsliste

> Abzuarbeiten. Grundlage: `ux-soll-ist-kas.md` (Prüfung vom 2026-08-16).
> Jeder Punkt nennt **wo** man anfängt und **woran** man sieht, dass er
> erledigt ist. Reihenfolge nach Wirkung, nicht nach Aufwand.
>
> Aufwand: **S** ≤ 1 Std · **M** ≤ ½ Tag · **L** ≥ 1 Tag
>
> **Stand 2026-08-18:** **Paket 7 ist zu** — damit ist die Liste bis auf
> UX-Daten (Datenfrage, braucht dich) und den daraus entstandenen Punkt
> UX-34 abgearbeitet.
>
> **Stand 2026-08-17 (abends):** Paket 1 und **Paket 2** sind abgeschlossen,
> **produktiv** seit dem Merge von PR #41. Paket 2 brachte vier ungesuchte
> Funde mit (UX-30 bis UX-33), alle erledigt.
>
> **Paket 3 ist bis auf einen Punkt zu:** UX-05, UX-06, UX-06b, UX-08 und
> UX-09 sind erledigt. Offen bleibt **UX-Daten** — das ist keine Programmier-,
> sondern eine Datenfrage und braucht dich (Dubletten, Domains als
> Firmenname, der Testdatensatz KOMPAGNON). Dazwischen kam der
> Vorfall vom Nachmittag (135 Fehl-Mails an einen Betrieb) und zwei
> Sicherheitsbefunde, die alles andere verdrängt haben — nachzulesen in den
> Commits `679b32c`, `dddd7af` und `d7768f8`.

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

### Vier Funde, die beim Zusammenlegen mit herausfielen

*Nicht gesucht, sondern beim Hinsehen aufgefallen. Alle vier sind erledigt.
Drei kamen aus dem Code, einer (UX-33) erst vom laufenden System.*

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

- [x] **UX-33** · **Der einzige Fund, der nicht aus dem Code kam.** Nach dem
      Deploy stand auf Staging: 30 Betriebe, darüber „27 Neu" und „2 Gewonnen".
      **27 + 2 = 29.** Der dreißigste steht auf `opt_in` — ein Status, den
      `LEAD_STATUS` nicht kennt. In der Zeile war er richtig: `leadStatusLabel`
      machte „Opt in" daraus, genau wie vorgesehen. Aber die Filterschaltflächen
      und die Kacheln wurden aus den *Schlüsseln* von `LEAD_STATUS` gebaut — er
      bekam keine. **Sichtbar in der Liste, unerreichbar über jeden Filter**,
      und die Zahlen gingen sichtbar nicht auf.
      **Gemacht:** `statusAusBetrieben` leitet die Filter aus den Daten ab, wie
      zuvor schon die Quellen. Bekannte Werte behalten die Reihenfolge des
      Vertriebswegs, unbekannte folgen dahinter. Die Zähler summieren sich
      bauartbedingt auf die Gesamtzahl — dafür gibt es einen Test.
      *Der Punkt daran:* Die Regel „ein unbekannter Wert wird nie roh gezeigt"
      war eingehalten. Die Lücke lag eine Ebene daneben — im **Filter**, nicht
      in der Anzeige. Gefunden hat sie nur der Blick auf den Bildschirm.

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

- [x] **UX-05** · **S** · ✅ **2026-08-17** · `Invalid Date` als sichtbarer Text.
      Es war kein Einzelfall, deshalb `utils/datum.js` statt einer Reparatur an
      der Fundstelle: `datumKurz`/`datumUndZeit` nehmen den Ersatztext als
      Angabe entgegen. `LeadProfile.jsx:1517` zeigt jetzt *„Datum unbekannt"*.
      Commit `f2d61c4`.

- [x] **UX-06** · **M** · ✅ **2026-08-17** · Die `[Auto-Enrichment]`-Zeile war
      kein Anzeigefehler — `lead_enrichment.py` schrieb sie in `lead.notes`,
      das Feld für *deine* Notizen, und stellte sie bei **jedem** Lauf erneut
      dem voran, was du geschrieben hattest.
      **Die Annahme in dieser Zeile war falsch:** Die Werte lagen *nicht*
      schon als Spalten vor. SSL und Impressum hatten keine, und
      `pagespeed_score` wurde berechnet und **nirgends** gespeichert — die
      Notizzeile war der einzige Ort, an dem er einen Lauf überlebte. Ersatzlos
      streichen hätte die Befunde vernichtet.
      **Gemacht:** Spalten `has_ssl`, `has_impressum`, `enriched_at` neu,
      `pagespeed_mobile_score` wird endlich beschrieben. Die Notizzeile ist
      weg. In der Betriebsansicht steht ein Block *Technische Prüfung* mit
      Zeitpunkt; `utils/anreicherung.js` hält die Anzeigelogik prüfbar.
      **`NULL` heißt „nicht geprüft" und wird auch so angezeigt** — nicht als
      „fehlt". Für den Altbestand ist das bis zur nächsten Anreicherung die
      ehrliche Auskunft.
      **Altbestand — am Bildschirm nachgesehen und dabei einen Widerspruch
      gefunden, den ich selbst erzeugt hatte:** Der neue Block sagte „SSL:
      nicht geprüft", zwei Zeilen darunter stand weiter die alte Notiz „SSL:
      OK". Beides stimmte für sich. Die Werte waren also da, nur im falschen
      Feld — sie zu löschen wäre der schlechtere Weg gewesen.
      Deshalb **`POST /api/leads/befunde-nachtragen`** (Admin): liest SSL,
      Impressum und PageSpeed aus der Notizzeile in die Spalten und entfernt
      die Zeile danach. Übernommen wird nur, was noch leer ist.
      **Ein Zeitpunkt wird nicht erfunden** — die Zeile trug keinen, also
      bleibt `enriched_at` leer und die Oberfläche sagt „Geprüft — Zeitpunkt
      unbekannt". Das ist ein dritter Zustand neben „geprüft am" und „noch
      nicht geprüft", und er ist nötig, weil sonst eine der beiden Angaben
      lügen müsste.
      `scripts/notizen-bereinigen.sql` bleibt als Weg ohne laufende Anwendung,
      ist aber der schlechtere: Es löscht nur.
      **Beides muss David einmal auslösen.**
      *Nachgesehen:* nach einer Anreicherung steht in `lead.notes` nur, was ein
      Mensch geschrieben hat (4 Tests).

- [x] **UX-06b** · **S** · ✅ **2026-08-17** · Zwei Punktzahlen ohne
      Unterscheidung. **Die Ursache war nicht die fehlende Beschriftung,
      sondern eine eingefrorene Zahl:** `AuditTool.jsx` belegte das Notizfeld
      beim Anlegen mit `Audit-Ergebnis: 40/100 Punkte – …` vor — obwohl das
      Modal die Punktzahl zwei Zeilen darüber ohnehin als Kachel zeigt. Der
      Text blieb stehen, das Audit lief weiter, und später stand die alte Zahl
      als Notiz neben der neuen als Ergebnis. Das sind die 40 gegen 37.
      Ein Wort davor hätte den falschen Zustand nur beschriftet.
      **Gemacht:** Notizfeld startet leer. Die Punktzahl steht in der
      Betriebsansicht unter „Letzter Audit" — und zwar die aktuelle.

- [x] **UX-08** · **S** · ✅ **2026-08-17** · Das Widget meldete
      „Bestätigungs-Mail geschickt", auch wenn der Versand scheiterte.
      Der Teaser trägt den Zustand jetzt mit (`bestaetigung_versandt`), und das
      Widget kennt drei Zustände statt einer Behauptung: *wird verschickt* →
      *geschickt* → *ging nicht raus, nochmal senden*.
      **Der Zwischenzustand war nötig:** Der Versand läuft im Hintergrund an,
      wenn die Analyse fertig ist — beim Anzeigen des Ergebnisses ist er es
      meist noch nicht. Ein sofortiges „ging nicht raus" wäre die zweite
      Unwahrheit gewesen. Sechs Nachfragen im Abstand von drei Sekunden,
      dann erst das Urteil.
      Der zweite Versuch hängt an `POST /api/widget/bestaetigung/{token}` und
      ist auf fünf Versuche begrenzt: Die Empfängeradresse steht fest, wer den
      Knopf drückt bestimmt sie nicht.
      *Nachgesehen:* mit `send_email → False` erscheint keine Erfolgsmeldung
      (7 Tests).

- [x] **UX-09** · **S** · ✅ **2026-08-17** · Prozentspalte ohne Überschrift auf
      dem Dashboard. Die Zahl war **richtig** (Gewinnquote) — sie sah nur aus
      wie ein Anteil an allem. Jetzt steht über den beiden rechten Spalten
      „Betriebe" und „Gewinnquote". Das `✓` hinter der Zahl ist weg: Es stand
      für die fehlende Überschrift ein, und die gibt es jetzt.
      **Dabei mitgenommen:** Die Karte hieß „Leads nach Herkunft" und zählte
      „12 Leads". Nach UX-04 heißt das Objekt **Betrieb** — „Lead" ist ein
      Zustand. Ein Rest aus Paket 1, wie UX-32.

- [~] **UX-Daten** · **M** · **Halb erledigt 2026-08-17 — und es war kein
      Datenpflegeproblem.**
      „Domains als Firmenname" sah nach fehlender Pflege aus. Es war eine Zeile
      Code. Der Domainimport legt einen Betrieb mit der Domain als Namen an,
      als Platzhalter. Der Impressum-Schritt liest kurz darauf den echten Namen
      aus — und verwirft ihn:

          if data_imp.get(field) and not getattr(lead, field, None):

      `company_name` ist zu dem Zeitpunkt gefüllt. Mit dem Platzhalter. Also
      galt das Feld als erledigt. **Das System hat den richtigen Namen jedes
      Mal gelesen und weggeworfen** — an drei Stellen: im Domainimport, in
      `enrich_lead` (prüfte nur auf leer und „Unbekannt") und im einzelnen
      Impressum-Endpunkt.
      **Gemacht:** `services/betriebsname.py` sagt an einer Stelle, was ein
      Platzhalter ist — leer, „Unbekannt", die eigene Domain, alles in
      Domainform. Das deckt auch `nachhaltika.denachhaltika.de` ab. Alle drei
      Stellen nutzen sie. Ein von Hand gepflegter Name wird nie überschrieben.
      **Für den Bestand:** `POST /api/leads/namen-nachtragen` (Admin) nimmt
      genau die Betriebe mit Platzhalternamen und liest ihr Impressum erneut,
      höchstens 25 je Aufruf. Der Bericht nennt jede Änderung einzeln und auch
      jeden Betrieb, bei dem nichts zu holen war. **Muss David einmal
      auslösen** — ein SQL-Skript kann es nicht, der richtige Name steht nicht
      in der Datenbank.
      **Offen und bei David** (keine Codefrage): Dublette **ECO-VOX**, Ort
      `News` (vermutlich Neuss), die Testdatensätze **KOMPAGNON** und
      **example.com** in der Produktivliste.
      *Prüfung:* Kein Datensatz in der Liste, den man einem Kunden nicht zeigen
      würde.

---

## Paket 4 — Eine Primäraktion je Bildschirm

- [x] **UX-13** · **S** · ✅ **2026-08-17** · Es waren sechs, nicht fünf, und
      zwei davon trugen Farbe. Jetzt trägt **genau einer** Gelb — und welcher,
      hängt davon ab, wie weit der Betrieb ist:
      kein Audit → *Audit starten* · Audit da → *Kaltakquise starten* ·
      gewonnen → *Projekt anlegen* · Projekt da → *Zum Projekt*.
      **Nach gesendetem Angebot und bei verloren ist kein Knopf hervorgehoben.**
      Da wartet man auf Antwort — einer auf Verdacht wäre eine Behauptung.
      Die Entscheidung liegt als reine Funktion in `utils/naechsterSchritt.js`
      (9 Tests), nicht als Farbe im Markup.

- [x] **UX-14** · **S** · ✅ **2026-08-17** · Sie tun Verschiedenes:
      *Audit starten* erzeugt die Punktzahl, *Neu prüfen* rief `/enrich` auf und
      holt Firmendaten, Google Business, SSL, Impressum und PageSpeed.
      Der Unterschied stand nur im Tooltip — **ein Tooltip ist keine
      Beschriftung.** Heißt jetzt **„Stammdaten neu holen"**.

- [x] **UX-11** · **M** · ✅ **2026-08-17** · Gewichtung umgedreht: Die
      Kennzahlenreihe steht jetzt **über** den Geldkacheln.
      **Und `0,00 €` steht nicht mehr in Erfolgsgrün** — Grün behauptet ein
      Ergebnis, eine Null ist keines. Farbe bekommt der Betrag erst, wenn es
      etwas zu färben gibt. Das war derselbe Fehler wie in Paket 3, nur in
      Farbe statt in Worten.
      **Mitgenommen:** „Leads gesamt" → **Betriebe gesamt**, „Gewonnene Leads"
      → **Gewonnene Betriebe**, „+ Neuer Lead" → **+ Neuer Betrieb**,
      „Aktuelle Leads" → **Aktuelle Betriebe** (UX-04).

- [x] **UX-12** · **S** · ✅ **2026-08-17** · **Diagnose war falsch — gemessen
      statt geschätzt.** Die Abschnittsüberschriften „AKTUELLE LEADS" und
      „LETZTE AUDITS" haben **8.89** Kontrast. Sie bestehen WCAG AA deutlich
      und waren nie das Problem.
      Unsichtbar waren die **Beschriftungen unter den Zahlen**: `--text-30`
      auf der App-Fläche = **2.13**, Schwelle für Text ist 4.5. Und dieser Ton
      hing an `--text-tertiary` — **911 Verwendungen im Frontend**. Nicht die
      Zahlen waren zu schwach, sondern die Wörter, die sagen, was die Zahl
      bedeutet. Deshalb las sich die Reihe wie Dekoration; das ist zugleich die
      halbe Ursache von UX-11.
      **Gemacht:** neuer Ton `--text-45: #647071` (4.63 auf der Fläche, 4.91
      auf Karten), `--text-tertiary` zeigt darauf. `--text-30` bleibt hell und
      ist damit ausdrücklich **kein** Textton mehr — für Trennlinien und
      Zierrat. Die 15 direkten Textverwendungen sind umgestellt.
      Der Dunkelmodus war schon in Ordnung (7.10) und bleibt unverändert.
      **Damit es nicht zurückrutscht:** `utils/kontrast.test.js` liest
      `tokens.css` und rechnet die Verhältnisse nach. Wer einen Textton
      aufhellt, bricht den Test.
      *Nachgemessen:* im Browser auf der Staging-Oberfläche, nicht geschätzt.

- [x] **UX-10** · **S** · ✅ **2026-08-17** · Kennzahlen, Betriebsliste und
      Auditliste hatten den Platzhalter bereits (`Skeleton`). Offen war nur die
      Geldreihe: Sie stand während des Ladens gar nicht da und schob beim
      Eintreffen alles darunter nach unten. Jetzt drei Platzhalterkacheln.

- [x] **UX-18** · **S** · ✅ **2026-08-17** · **Nachgemessen, und die
      Richtung stimmte nicht:** Nicht dunkel auf dunkel — im *Hellmodus* stand
      `--brand-primary-mid` auf `--bg-active` mit **3.39**, unter der Schwelle.
      Im Dunkelmodus waren es 5.62, also in Ordnung.
      Jetzt `--brand-primary` (8.16), halbfett und mit sichtbarem Rand. Die
      Paarung steht in `utils/kontrast.test.js` und ist damit festgehalten.

- [x] **UX-15** · **M** · ✅ **2026-08-17, von David entschieden.** Zehn
      gleichrangige Reiter waren zehn Entscheidungen bei jedem Aufruf.

      **Oben bleiben sechs:** Übersicht · Kontakt · Audits · Angebot ·
      Nachrichten · Dateien.
      *Nachrichten* bleibt oben, weil dort der Ungelesen-Zähler hängt — ein
      Zähler hinter einem Menü zählt für niemanden.

      **Hinter „Mehr":** Deals (steht auch unter Vertrieb → Deals), Akademie
      (kundenseitig, nicht Innendienst), Zugang (QR-Code, einmal je Betrieb),
      E-Mails.

      Ist einer der untergeordneten Reiter offen, ist **„Mehr" hervorgehoben** —
      sonst sucht man ihn zwischen den sechs. Ein Klick daneben schließt das
      Menü. Die Aufteilung liegt in `utils/betriebReiter.js` (13 Tests), nicht
      verteilt im Markup.

      **Nichts ist weg**, es ist nur nicht mehr alles gleich laut.

---|---|
      | Übersicht | der Einstieg |
      | Kontakt | Stammdaten, wird beim Bearbeiten angesteuert |
      | Audits | der Kern des Angebots |
      | Angebot | daraus entsteht das Geschäft |
      | Nachrichten | trägt den ungelesen-Zähler, muss sichtbar bleiben |
      | Dateien | Anhänge des Betriebs |

      **Unterordnen (hinter „Mehr" oder in die Übersicht):** *Deals* (steht
      auch unter Vertrieb → Deals), *Akademie* (kundenseitig, nicht
      Innendienst), *Zugang* (QR-Code, einmal je Betrieb gebraucht),
      *E-Mails* (Verlauf, gehört sachlich zu Nachrichten).

      **Zusammenlegen wäre die Alternative:** *Nachrichten* und *E-Mails* sind
      derselbe Gegenstand in zwei Kanälen. Das wären dann fünf.

      **Zwei Kleinigkeiten schon erledigt (2026-08-17):** Der Reiter hieß
      **„Akademy"** — halb deutsch, halb englisch, ein Wort, das es nicht gibt;
      heißt jetzt *Akademie*. Und bei *E-Mails* stand das Zeichen in der
      Beschriftung statt im `icon`-Feld, weshalb dieser Reiter als einziger
      einen Abstand mehr hatte.

---

## Paket 5 — Das Sammelbecken auflösen · ✅ ABGESCHLOSSEN 2026-08-17

- [x] **UX-16** · **M** · ✅ Die Gruppe **„Kompagnon"** hieß nach der eigenen
      Firma und war damit der Name für „alles Übrige". Sieben unverwandte
      Einträge.

      **Erst nachgesehen, was sie wirklich sind** — das entschied die
      Zuordnung, nicht mein Gefühl:

      | Eintrag | Beleg | wohin |
      |---|---|---|
      | QR-Generator | Platzhalter `postkarte-koblenz-mai-2025` | **Werbung** |
      | Templates | Platzhalter `/paket/mein-produkt` | **Angebot** (heißt jetzt *Verkaufsseiten*) |
      | Produkte | `api/products/` — der Katalog | **Angebot** (*Pakete*) |
      | Produktentwicklung | Ideen-Board Idee→Geplant→Fertig | **Angebot** (*Roadmap*) |
      | Tickets, Retainer | Betreuung nach dem Verkauf | **Betreuung** |

      Dabei fiel auf, dass „Einstellungen" mit acht Einträgen gerade das
      nächste Sammelbecken wurde. Getrennt in **Einstellungen** (was eine
      Person für sich einstellt) und **Verwaltung** (was für alle gilt).
      *Webhooks* liefern Leads herein → Akquise. *Export* gibt Betriebe
      heraus → Vertrieb.

      **Der eigentliche Fund lag darunter:** Die Zuordnung Adresse → Gruppe
      stand **zweimal** — in der Menüdefinition und noch einmal als Pfadliste
      in `getDefaultOpen`. Wer einen Eintrag verschiebt und die zweite Liste
      vergisst, bekommt eine Seitenleiste, die nicht mehr zeigt, wo man ist —
      derselbe Fehler wie am 16.08., nur an anderer Stelle. Beides kommt jetzt
      aus `utils/menue.js`.

      *Nachgesehen:* 17 Tests, darunter „jede Gruppe lässt sich mit einem Wort
      benennen" und „keine zwei Einträge heißen fast gleich".

- [x] **UX-17** · **S** · ✅ **Produkt-Editor**, **Produkte** und
      **Produktentwicklung** nebeneinander. Die Antwort war schärfer als die
      Frage: **„Produkte" und „Produkt-Editor" sind dieselbe Sache** — Liste
      und Editor desselben Bestands (`api/products/`), und der Editor war von
      der Liste aus ohnehin erreichbar. Zwei Menüeinträge für ein Objekt sind
      einer zu viel; der Editor ist aus dem Menü raus.
      „Produktentwicklung" war überhaupt keine Produktpflege, sondern ein
      Ideen-Board → heißt **Roadmap**.
      **Dabei entfernt:** `/app/products/editor`, eine zweite Adresse für
      denselben Bildschirm, von nirgends verlinkt.

---

## Paket 6 — Politur · ✅ ABGESCHLOSSEN 2026-08-17

*Neun kleine Dinge. Zwei davon waren beim Anfassen keine Politur mehr.*

- [x] **UX-20** · Überschrift auf jedem Bildschirm doppelt. **Ursache benannt:**
      Auf obersten Seiten bestand die Brotkrume aus **einem** Element — dem
      Seitennamen, der zwei Zeilen tiefer als H1 steht. Eine Brotkrume mit
      einem Element zeigt keinen Weg, sie wiederholt nur. Sie erscheint jetzt
      erst ab zwei Elementen; auf Detailseiten („Betriebe › Name") bleibt sie.
- [x] **UX-21** · Dieselben sieben Phasen mit denselben Zahlen **zweimal
      übereinander** — als Kennzahlreihe und als Spaltenköpfe, auf mobil ein
      drittes Mal als Reiterzeile. Die Kennzahlreihe ist weg; die Zahl steht
      dort, wo auch die Karten dazu liegen.
- [x] **UX-22** · Reiter `Akademy` → **Akademie**.
- [x] **UX-23** · **War schlimmer als notiert:** Der Knopf „+ Neues Audit"
      stand in der oberen Leiste mit `action: () => {}` — **er tat nichts**.
      Ein Knopf ohne Wirkung ist schlimmer als keiner: Man drückt ihn und
      sucht den Fehler bei sich. Entfernt; nach einem fertigen Bericht steht
      der richtige Knopf ohnehin unter dem Ergebnis.
- [x] **UX-24** · „Zurück"-Knopf zusätzlich zur Brotkrume — und
      `navigate(-1)` führt woandershin als die Brotkrume, je nachdem, woher
      man kam. Zwei Wege, zwei Ziele, ein Zweck. Entfernt.
- [x] **UX-25** · „Geschäftsführer *(auto)*" → **Geschäftsführer**. Woher der
      Wert kommt, interessiert die Maschine, nicht den Menschen davor.
- [x] **UX-26** · Das Formular „Weitere Domains" stand immer offen. Bei den
      meisten Betrieben gibt es gar keine zweite Domain. Jetzt erst auf
      Verlangen.
- [x] **UX-27** · Das Audit-Tool zeigte keine früheren Audits, obwohl das
      Dashboard sie führte — dieselbe Schnittstelle, nur kannte dieser
      Bildschirm sie nicht. Fünf zuletzt geprüfte Seiten stehen jetzt unter
      dem Formular. Schlägt der Abruf fehl, fehlt der Verlauf und sonst
      nichts.
- [x] **UX-28** · Score-Balken ohne Legende — **die Stufe hing allein im
      `title`, also im Tooltip.** Auf einem Berührungsgerät gibt es den nicht.
      Dieselbe Bauart wie UX-14: Ein Tooltip ist keine Beschriftung. Die Stufe
      steht jetzt am Score (`stufeKurz`, 3 Tests).

---

## Paket 7 — eine Welt statt zwei · ✅ ABGESCHLOSSEN 2026-08-18

- [x] **UX-19** · **L** · ~~Bruch hell/dunkel zwischen Tool und Kundenportal~~
      **erledigt 2026-08-18.** Der Befund las sich wie zwei
      Gestaltungsentscheidungen und war eine Auslassung: Die Anwendung hat
      **ein** Farbsystem mit hellem und dunklem Modus (`styles/tokens.css`),
      und die Kundenseiten sind ihm nie beigetreten. `PortalLogin` trug 17
      feste Hexwerte gegen 3 Tokens — also blieb der erste Bildschirm nach
      dem Kauf weiß, während alles andere dem System des Betrachters folgt.
      **Umgestellt:** PortalLogin, CustomerPortal (71 feste Werte),
      KundenPortal, Freigaben, SupportTickets.
      **Fest bleiben nur zwei Sorten Farbe**, und der Sperrtest nennt den
      Grund: die Medaillentöne des Homepage Standards und die drei
      Fensterknöpfe des Browser-Nachbaus — die zitieren ein Fenster, sie
      melden keinen Zustand.
      **Die dritte Domain ist weg.** Stattdessen der Firmenname und die
      eigenen Rechtsseiten — die es in `pages/` gab, die aber **an keiner
      Adresse hingen**: ein Impressum, zu dem kein Weg führte, und in dessen
      Fuß ein Verweis auf `/barrierefreiheit`, das es ebenfalls nicht gab.
      Alle drei sind jetzt erreichbar und folgen demselben Farbsystem.
      *Geprüft:* im Browser in beiden Modi, nicht nur im Test.

### Zwei Funde beim Messen — beide schwerer als der Listenpunkt

- [x] **UX-19a** · Weiß auf `--brand-primary` erreicht im Dunkelmodus **2.06**.
      So ist in der Anwendung **jeder** Knopf gebaut; auf der Kundenseite wäre
      es die erste Fläche nach dem Kauf gewesen. Neues Token
      `--text-on-brand` dreht die Tinte statt der Markenfarbe: **8.43**.
- [x] **UX-19b** · `ThemeContext` setzt **immer** ein `data-theme`, aber
      `[data-theme="light"]` nannte nur Flächen und Schrift. Auf einem
      Rechner, dessen System dunkel steht, ergab die Wahl „hell" deshalb
      helle Flächen mit den **Markenfarben des Dunkelmodus**:
      `--brand-primary` war `#008eaa` statt `#004f59`, Weiß darauf 3.85.
      Dreizehn Tokens fehlten. `styles/tokens.test.js` verlangt jetzt, dass
      der Hellblock jeden Ton des Dunkelblocks zurücknimmt.

### Daraus entstanden — ebenfalls erledigt

- [x] **UX-34** · **M** · ~~Weiß auf Marke im Innendienst~~ **erledigt
      2026-08-18.** Geschätzt waren 62 Stellen. Gemessen wurden es mehr, und
      schlimmer: **140** Stellen weiße Schrift auf einer Fläche, die im
      Dunkelmodus durchfällt, und **46** weitere auf festen Hexwerten, die in
      **beiden** Modi durchfallen — dort war der Text nie lesbar.

      | | Fund | hell / dunkel |
      |---|---|---|
      | 87 | Weiß auf `--brand-primary` | 9.28 / **2.06** |
      | 31 | Weiß auf `--kc-mid` | **3.85** / **2.06** |
      | 33 | grau gefärbte Sperrfläche mit weißer Schrift | Text verschwindet |
      | 36 | feste Grün-, Rot- und Bernsteintöne | 1.6 bis 3.9 |

      **Regeln statt Geschmack:** Markenflächen bekommen `--text-on-brand`;
      `--kc-mid` als gefüllte Fläche wird `--brand-primary` (die Tinte allein
      hätte nicht gereicht, Weiß fällt dort schon im Hellmodus durch); ein
      gesperrter Knopf behält seine Farbe und wird über `opacity: 0.5` leiser,
      wie `.btn-primary:disabled` es immer schon macht; die festen Töne werden
      `--success`/`--error`/`--warn`, wobei Bernstein **schwarze** Tinte trägt.

- [x] **UX-34a** · Im Hellmodus lagen **drei von vier Statustönen** als
      Schrift unter der Schwelle: success 4.11, warn 4.08, info 3.48 — und
      `[data-theme="light"]` führte ein viertes warn (`#B8860B`, **2.94**).
      Neue Werte gegen `--surface`, `--paper` und die eigene Fläche gemessen.
      Der Dunkelmodus war nie betroffen; wer dunkel arbeitet, sieht es nie.

### Was jetzt dagegen steht

- `utils/weisseSchrift.test.js` misst **jede** Paarung Weiß-auf-Fläche im
  ganzen Quellbaum, in beiden Modi.
- `styles/tokens.test.js` verlangt, dass die beiden hellen Wege (`:root` und
  `[data-theme="light"]`) dieselben Werte tragen.
- `utils/tokenwerte.js` löst die `var()`-Ketten je Modus auf — von Hand
  nachgeschlagen geht genau das schief, und daran hat UX-19a so lange
  überlebt.

### Offen

- [ ] **193 Stellen** weiße Schrift auf einer Fläche, die die Datei nicht
      nennt: geerbt, ein Verlauf, oder aus den Daten. Von außen nicht
      messbar. Sie sind **nicht** geprüft — nur gezählt.

---

## Paket 8 — Akademie und Mobil · 2026-08-18

*Beide Flächen standen als „nicht angesehen". Sie waren es nicht.*

### Erledigt

- [x] **UX-35** · **Leere Seite auf dem Desktop.** `/app/vertrieb` — die
      Adresse, die in der Mobilleiste steht — zeigte auf einem breiten
      Bildschirm **nichts**. Alle vier Mobil-Einstiege riefen `navigate()` im
      Rumpf der Komponente auf; der Router verwirft das, `return null` bleibt
      stehen. Jetzt `<Navigate replace />`. *Geprüft:* `/app/vertrieb` landet
      auf `/app/deals`.
- [x] **UX-36** · **Erfundene Zahlen auf den Kacheln.** „12" Leads, „5" neue,
      „3" Projekte, „2 offen", „54 Punkte / Projekt", „5 Rollen",
      „2 Seiten live" — und ein **„Abonnement: Professional"**, das eine
      Zahlungstatsache behauptet. In der lokalen Datenbank steht **ein**
      Betrieb. Eine erfundene Zahl ist schlimmer als keine: Sie wird geglaubt.
      Entfernt, bis sie aus den Daten kommt.
- [x] **UX-37** · **„Akademy" an neun weiteren Stellen** — gestern wurde ein
      Reiter umbenannt. Der Rest stand noch: die Überschrift der Akademie
      selbst, der Reiter in der Kundenkartei, und **zweimal die Urkunde**,
      die der Kunde ausgedruckt behält.
- [x] **UX-38** · **Fremdes Monogramm.** Auf der Passwort-zurücksetzen-Seite
      stand ein goldenes **„HS"** neben dem Wort KOMPAGNON. Jetzt die echte
      Marke.
- [x] **UX-39** · **Ein Bildschirm, zwei Namen und zwei Adressräume.**
      Brotkrume „Kurse verwalten", Überschrift „Kursverwaltung"; die eigenen
      Knöpfe zeigten auf `/app/akademie/…`, während der Bildschirm unter
      `/app/academy/…` erreicht wird — ein Klick wechselte den Adressraum.
      Dazu „← Zurück" neben der Brotkrume (UX-24-Klasse).
- [x] **UX-40** · **Unsichtbarer Kreis — mein Fehler von heute Vormittag.**
      Der Umbau aus UX-34 zog einen Avatar-Kreis von `--kc-mid` auf
      `--brand-primary` — auf eine Karte, die selbst `--brand-primary` ist.
      Zwei Stellen. Die Regel „Markenfläche trägt lesbare Tinte" ist richtig
      und sagt nichts über eine Fläche, die sich von ihrer **Nachbarfläche**
      abheben muss.
- [x] **UX-41** · Die Mobil-Einstiege folgten dem Farbsystem nicht (`#9AACAE`
      als Beschriftungsfarbe = 2.13 auf Weiß). Jetzt Tokens.
- [x] Totes Gewicht: `pages/Akademie.jsx` war importiert und an keiner Route;
      `m-vertrieb` war eine zweite Adresse für einen Bildschirm, den nichts
      verlinkt.

### Offen — jeweils mit Empfehlung

- [x] **UX-42** · **M** · ~~Die Akademie gibt es zweimal~~ **erledigt
      2026-08-18.** Ein Adressraum: `/app/akademie/*` leitet vollständig auf
      `/app/academy/*` um (eine Weiterleitung statt elf Routen, alte
      Lesezeichen bleiben gültig). Der zweite Kurseditor, der Modul-Editor und
      der alte Lektions-Spieler sind entfernt — **zu portieren war nichts**,
      ihre Mehrfelder erscheinen auf keinem Bildschirm.
      **Davor** (Schritt 1 der Empfehlung): Ein gescheitertes Speichern ist
      jetzt sichtbar. `utils/schreiben.js` fängt beides ab — die geworfene
      Ausnahme **und** die Antwort, die nicht `ok` ist — und macht aus dem
      Statuscode einen Satz. *Geprüft am Gegenstand:* Modul im Hintergrund
      gelöscht, dann „+ Lektion hinzufügen" gedrückt → „Die Lektion nicht
      gespeichert. Das Ziel gibt es nicht (mehr)." Vorher: nichts.
      **Offen daraus:** ob Checklisten je Lektion ein Merkmal bleiben sollen —
      sie waren nur im entfernten Modul-Editor pflegbar und nur im entfernten
      Lektions-Spieler sichtbar; die Daten stehen weiter in der Spalte
      `checklist_items_json`. Ebenso `category`, `category_color`, `formats`:
      im Modell, nirgends angezeigt.

- [x] **UX-43** · **S** · ~~Drei Mobil-Einstiege sind von nirgends verlinkt~~
      **erledigt 2026-08-18: entfernt.** Angebunden hätte sie verdoppelt, was
      es schon gibt — `/app/settings` rendert unter `SettingsLayout` eine
      **eigene** Mobilansicht und steht im „Mehr"-Fach; die übrigen Ziele
      (Projektpipeline, Alle Projekte, Betriebe, Tickets) stehen direkt in der
      Mobilleiste. Geblieben ist `MobileVertrieb` — der Einstieg, auf den die
      Leiste unter „Vertrieb" tatsächlich zeigt. Mit den drei Seiten fiel auch
      die gemeinsame Komponente `MobileHub`, die sonst niemand benutzte.

- [x] **UX-44** · **S** · ~~Zwei Arten, eine Löschung zu bestätigen~~
      **erledigt 2026-08-18 — anders als vorgeschlagen.** Beim Nachzählen:
      **26 Stellen** nutzen die Browserfrage, **eine** einen eigenen Dialog
      (Kursliste), **eine** einen mit Vorschau (Projekte löschen). 26 Stellen
      auf einen Dialog umzubauen wäre viel Arbeit für wenig — die Browserfrage
      ist eindeutig, tastaturfähig und nicht zu übersehen.

      **Die Regel, die stattdessen gilt** (`utils/loeschfrage.js`): Nicht die
      Bauform entscheidet, sondern was auf dem Spiel steht.

      | Was verschwindet | Wie gefragt wird |
      |---|---|
      | eine einzelne, ersetzbare Sache | Browserfrage genügt |
      | etwas mit Anhang | die Frage **nennt den Anhang** |
      | Unwiderrufliches mit vielen Abhängigkeiten | eigener Dialog mit Vorschau |

      Umgesetzt an den beiden Stellen der Akademie: Aus „Modul und alle
      Lektionen darin löschen?" wird „Modul „Grundlagen" löschen? — Damit geht
      auch: 3 Lektionen." Die Frage sagt jetzt, **wie viel** mitgeht.

### Offen

- [ ] **193 Stellen** weiße Schrift auf einer Fläche, die die Datei nicht
      nennt: geerbt, ein Verlauf, oder aus den Daten. Von außen nicht
      messbar. Sie sind **nicht** geprüft — nur gezählt.
- [ ] **Kein Wächter gegen verwaiste Adressen.** UX-35 und UX-43 waren beide
      derselbe Fall: ein Bildschirm ohne Weg dorthin. Ein Test, der das
      allgemein hält, fehlt — mein schneller Durchlauf dazu meldete 18
      Adressen, von denen die meisten Fehltreffer waren (verschachtelte
      Routen unter `settings`, legitime Weiterleitungen). Ohne saubere
      Auflösung der Verschachtelung ist so ein Test mehr Lärm als Nutzen.

---

## Noch nicht geprüft — vor dem Abhaken zu erheben

Diese Flächen sind nicht angesehen worden. Sie sind **nicht** „in Ordnung",
sondern unbekannt:

- [ ] Newsletter-Designer, Template-Editor, Component-Library,
      Online-fertig-Editor
- [ ] Das Kundenportal **von innen** — braucht einen echten Kundenzugang
- [ ] Barrierefreiheit — hier nicht gemessen; die Lückenliste führt sie als
      L-17 (12 von 167 Dateien mit ARIA) bei verkaufter BFSG-Konformität.
      Die Kontrastpunkte UX-11, UX-12 und UX-18 sind Vorboten, keine Prüfung
- [ ] Verhalten auf kleinen Bildschirmen
- [ ] Ladezeit als Erlebnis über eine ganze Reise (hängt an L-34)

---

*Angelegt 2026-08-16. Stand der Prüfung: `ee08ddc`.*
