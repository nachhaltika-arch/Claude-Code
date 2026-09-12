# Kampagnenstart Montag, 14.09.2026 — Stand und offene Aufgaben

Stand: 12.09.2026. Geschrieben am Ende der Sitzung vom 10.09., damit der
nächste Anlauf nicht bei null anfängt.

> **Die eine Sache, die den Start verhindert:** Der Messblock ist nicht auf
> der Landingpage. Ohne ihn sieht Meta keinen Seitenaufruf, jeder Lead kommt
> ohne Herkunft an, und die Kampagne lässt sich nicht bewerten. Alles andere
> unten ist wichtig, aber nicht blockierend.

---

## 1. Wo die Arbeit liegt

| | |
|---|---|
| `staging` | **14 Commits vor `main`** — alle mit grünem CI-Lauf, auf dem Staging-Server ausgeliefert. Hier stand 13; der Übergabe-Commit selbst kam danach dazu |
| `main` | unverändert — **nichts davon ist produktiv** |
| offener PR | **[#56](https://github.com/nachhaltika-arch/Claude-Code/pull/56)**, geöffnet am 12.09., alle sieben CI-Jobs grün — **wartet auf den Merge durch David** |

Alles, was in dieser Sitzung entstanden ist, wirkt erst nach dem Merge.

---

## 2. Was produktiv nachgemessen ist (12.09.)

Geprüft an `api.kompagnon.group`, nicht aus dem Gedächtnis:

| | Stand |
|---|---|
| Datenschutzlink im Widget | ✅ `kompagnon.eu/rechtliches/datenschutz` |
| Meta-Pixel im Widget | ✅ `1363198722345965` |
| Meta-Serverweg (CAPI) | ✅ `bereit: true`, Token und Pixel gesetzt |
| Kriterienzahl | 39 |
| Check PLUS im Teaser | angeboten, **aber ohne Kaufknopf** — die Adresse ist nicht eingetragen |
| Häkchentext im Widget | ✅ neue Fassung live (PR #55) |

**Der fehlende Kaufknopf ist kein Fehler.** Leer heißt bewusst „Angebot ohne
Abschluss": Ein Knopf, der ins Leere führt, wird von niemandem gemeldet, ein
fehlender fällt auf. Er erscheint, sobald die Adresse im Werkzeug steht — und
das geht erst nach dem Merge.

---

## 3. Was vor Montag zu tun ist

### 3.1 Bei David — blockierend

**① Messblock hochladen.** `docs/landingpage/websprint-landingpage.html` zu
Mittwald, als Ersatz der bestehenden `index.html` von
`websprint.kompagnon.eu`. Die Datei ist fertig und enthält den Block bereits.

Was der Block tut: lädt das Meta-Pixel **nur** nach Zustimmung zu
`c.marketing`, reicht `fbclid` und `_fbp` an das Widget durch und meldet den
Abschluss doppelt-gezählt-sicher (`fbq('track','Lead')` mit `eventID` plus
`gtag('event','generate_lead')`). Ausführlich in
`kompagnon/frontend/public/embed/README.md`.

> Prüfbar erst danach: ob Meta wirklich misst. Die Vorschau zeigt
> Oberflächen, keine Abläufe.

**② Bestätigungsmail klicken.** Es liegt eine Analyse an
`nachhaltika+lauf@gmail.com`. Die Trichterschritte **7 bis 9** (Klick →
zweite Mail → Berichtsseite → PDF) sind bis heute **nie durchlaufen worden**.
Ohne diesen Klick geht die Kampagne mit einem ungetesteten Abschnitt live.

**③ Meta-Konto einrichten.** Domain verifizieren und die
Ereignis-Priorisierung (Aggregated Event Measurement) setzen. Ohne beides
misst iOS-Verkehr unvollständig.

### 3.2 Bei David — nach dem Merge, im Werkzeug unter *Akquise → Widget*

| Feld | Wert | Wirkung, wenn leer |
|---|---|---|
| Kaufadresse Check PLUS | `https://buy.stripe.com/eVq8wP9JV4ORdsGgmm9Zm01` | Angebot ohne Knopf |
| Kaufadresse Relaunch | `https://buy.stripe.com/aFa8wP8FR6WZdsG0no9Zm00` | Knopf führt in den Kalender |
| Rabatt + Code | `25 % Rabatt für die ersten 25 Kunden` / `WS25` | kein Rabattkasten |
| Abnahmezusage | siehe Entscheidung 4.1 | keine Zusage |
| Freie Plätze | z. B. `Zwei Sprint-Plätze im Oktober frei` | kein Hinweis |

Logo und Portrait brauchen **keinen** Eintrag — das Portrait liegt als Datei
im Frontend und ist Vorgabe.

**Check PLUS steht im Katalog noch auf `draft`.** Solange es nicht `live`
ist, erscheint der Angebotsblock im Teaser nicht. Entscheidung, ob es zum
Start mitläuft.

### 3.3 Bei Claude — auf Ansage

- ~~**PR `staging → main` öffnen.**~~ **Erledigt am 12.09.: PR #56**, 14
  Commits (nicht 13 — der Übergabe-Commit kam nach dem Schreiben dieser Zeile
  dazu), alle sieben CI-Jobs grün. *Der Merge bleibt bei David — Claude
  merged nie selbst.*
- **Trichterschritte 7–9 nachprüfen**, sobald ① und ② erledigt sind.
- ~~**PageSpeed-Schlüssel**: nachgehen, warum er nichts liefert.~~
  **Erledigt am 12.09. — es war nichts zu reparieren.** Siehe Abschnitt 5.

---

## 4. Entscheidungen, die niemand außer David treffen kann

### 4.1 Die Abnahmezusage

Der Entwurf sagt **96 Punkte**, der Homepage-Standard (G1) sagt **85**. Beide
Zahlen stehen für dieselbe Garantie.

**Wichtiger als die Zahl ist die Bezugsgröße.** Die Punktzahl im Bericht ist
ein Prozentsatz dessen, was gemessen wurde — nicht der 103 Katalogpunkte.
„85 Punkte" ohne Angabe der Abdeckung ist deshalb keine prüfbare Zusage.

> **Vorschlag:** *„85 Punkte bei mindestens 90 % Abdeckung."*

Solange nichts eingetragen ist, steht auf der Berichtsseite **keine** Zusage
— weder im Angebotskasten noch in den Fragen. Das ist der sichere Zustand.

### 4.2 Die Barrierefreiheitserklärung

Der Entwurf versprach in den Fragen, sie technisch korrekt einzubauen. Sie
steht **nicht** im Leistungsumfang (dort: „Grundlagen der Barrierefreiheit:
Kontraste, Tastatur, Semantik"), der Audit-Katalog führt sie aber als eigenes
Kriterium `rc_bfsg`.

Entweder sie gehört in die Merkmalsliste — dann gehört sie auch ins Angebot,
in die Fragen und in die Auftragsbestätigung — oder sie darf nicht zugesagt
werden. Zurzeit steht sie **nirgends**.

### 4.3 Check PLUS zum Start?

Produkt ist angelegt (249 € netto / 296,31 € brutto, 5 Werktage,
anrechenbar auf einen Websprint innerhalb 6 Monaten), Zahlungslink existiert
und trägt den richtigen Betrag. Offen ist nur, ob es am Montag mitläuft.

---

## 5. Was die Zahl im Bericht wert ist

Ausführlich im Lagebild, Reiter **Messtiefe**. Kurz:

Der Katalog führt **103 Punkte in 39 Kriterien**. Der Gesamtscore wird
normiert — nicht erhobene Kriterien kürzen den **Nenner**, statt als Null
durchzuschlagen. Ein Betrieb kann damit 100 Punkte erreichen, ohne dass seine
Ladezeit je gemessen wurde.

**41 der 103 Punkte hängen an einer Quelle, die ausfallen kann:**

| Quelle | Punkte | wann sie ausfällt |
|---|---|---|
| PageSpeed-API | 12 | Schlüssel fehlt, Kontingent erschöpft oder Google hängt |
| KI-Einschätzung | 15 | Modell antwortet nicht oder meldet „nicht beurteilbar" |
| ausgelieferter Quelltext | 14 | Seite baut ihre Inhalte erst im Browser auf |

`tp_inp` (2 Punkte) fehlt bei kleinen Betriebsseiten **strukturell** — es
kommt aus CrUX-Felddaten, die dort nicht existieren. Auch ein funktionierender
Schlüssel bringt es nicht zurück.

> **Richtiggestellt am 12.09.2026.** Hier stand „Schlüssel liefert nicht —
> produktiv seit dem 04.09. der Fall", und in Abschnitt 3.3 stand das als
> größter einzelner Hebel. **Beides war falsch.** Nachgemessen, nicht
> geschlossen:
>
> - `/health` meldet den Schlüssel produktiv **und** auf Staging als gesetzt,
>   39 Zeichen.
> - Jeder PSI-Aufruf produktiv seit dem 05.09. antwortet **200 OK**, der
>   letzte am 12.09. um 09:57. Keine einzige Fehlerzeile im Protokoll.
> - Ein echter Lauf auf Staging am 12.09. (Audit 13, nachhaltika.de, 30 s)
>   führt `tp_lcp`, `tp_cls` und `tp_mobile` als **gemessen**, die
>   Erhebungsnotizen sind **leer**, Abdeckung **96 %**. Nur `tp_inp` fehlt —
>   strukturell, wie oben beschrieben.
>
> **Die Ursache des Ausfalls vom 04.09. war die Zeitgrenze von 60 Sekunden,
> nicht der Schlüssel.** Behoben am 05.09. in `b469a24` (120 s), produktiv
> seit dem 06.09. Am 04.09. lief produktiv übrigens **kein einziges Audit** —
> die Quelle für „der Produktivbericht vom 04.09. zeigte genau das" kann
> kein Lauf dieses Tages gewesen sein.
>
> **Wie die falsche Zahl eine Woche überlebte.** Zwischen dem 05.09. und dem
> 12.09. lief weder produktiv noch auf Staging ein Audit — die Reparatur war
> nie bestätigt. Der Grund des Ausfalls stand in `collection_notes`, lesbar
> nur aus der Datenbank; im Protokoll stand eine Warnung **ohne Grund**, weil
> `str()` einer `ReadTimeout` leer ist. Und wer lokal nachmisst, bekommt
> sofort 429: In `kompagnon/backend/.env` ist `GOOGLE_PAGESPEED_API_KEY`
> **leer** (Zeile 48) — PageSpeed v5 antwortet dann anonym, und das anonyme
> Tageskontingent ist erschöpft. Drei Wege, auf denen ein heiler Schlüssel
> wie ein defekter aussieht.
>
> **Bei David, eine Minute:** den Schlüssel in die lokale `.env` eintragen,
> damit eine Messung am eigenen Rechner nicht wieder das Gegenteil behauptet.

---

## 6. Womit man arbeitet

### Die Trichter-Vorschau

    python3 scripts/trichter-vorschau.py     →  http://127.0.0.1:8973

Acht Ansichten: Landingpage, Widget-Formular, Teaser, drei Mails,
Berichtsseite, PDF. Regler für Punktzahl, Rabatt, Abnahmezusage, freie
Plätze und Kaufknöpfe; drei Breiten; „Öffnen ↗" für ein eigenes Fenster;
Lagebild-Link in der Seitenleiste.

**Sie zeigt die echten Erzeugnisse**, nicht Nachbauten — das ausgelieferte
Widget, dieselben Mail-Funktionen wie beim Versand, den Produktkatalog aus
`startphase.py`. Nur die Befunddaten sind erfunden.

### Beanstanden und Aufträge

„Beanstanden" drücken, in die Ansicht klicken, tippen. Der Auftrag bekommt
eine Stecknadel und landet in `.vorschau-auftraege.json` (nicht im Repo).

    python3 scripts/auftraege-melden.py

Als Monitor gestartet meldet er jeden neuen Auftrag **sofort in die laufende
Sitzung**. In einer neuen Sitzung sagen: **„Melder an"** — dann kommt auch
der Rückstand einmal durch.

### Vor jedem Push, alle fünf

    pytest · ruff · jest · react-scripts build · gitleaks 8.21.2

`react-scripts test` prüft **nicht**, was `react-scripts build` prüft: Am
10.09. lag ein Syntaxfehler in einer Datei, die kein Test importiert — die
CI fand ihn, nicht der lokale Lauf. Und gitleaks muss in **derselben
Version** laufen wie die CI (8.21.2); die neuere 8.30.1 findet zwei weitere
Stellen, die die CI nicht kennt.

---

## 7. Was diese Sitzung gelehrt hat

**Siebenmal dasselbe Muster: gelesen, aber nirgends zu schreiben.** Die vier
Angebotsaussagen, die zwei Kaufadressen, Logo und Portrait — alle wurden von
der Berichtsseite gelesen, und für keine gab es eine Stelle in der
Oberfläche. Sie blieben dauerhaft leer, und die Abschnitte unsichtbar. Wer
hier eine Einstellung einführt, muss die Oberfläche im selben Zug mitziehen,
sonst ist sie nur halb da.

**Eine Vorschau mit falschen Daten ist schlimmer als keine.** Dreimal an
einem Tag zeigte die Vorschau einen Zustand, den das System nicht hatte:
erfundene Kriterien-Kennungen (`impressum_vorhanden` statt `rc_impressum`),
Wörterbücher statt JSON-Text, und Regler, die die Aufrufe des Widgets nicht
erreichten. Jedes Mal stand eine Reparatur an etwas Heilem kurz bevor.

**Eine Nachbildung ist kein Messgerät.** Die Behauptung „bei 78 % Abdeckung
sind höchstens 80 Punkte erreichbar" stammte aus der Vorschau, nicht aus dem
System. Nachgerechnet: 100 Punkte sind erreichbar. Der wirkliche Befund war
unbequemer — siehe Abschnitt 5.
