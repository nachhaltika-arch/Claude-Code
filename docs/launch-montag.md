# Kampagnenstart Montag, 14.09.2026 — Stand und offene Aufgaben

Stand: **13.09.2026**. Geschrieben am Ende der Sitzung vom 10.09.,
fortgeschrieben am 12. und 13.09.

> **Die eine Sache, die den Start verhindert:** Der Messblock ist nicht auf
> der Landingpage. Ohne ihn sieht Meta keinen Seitenaufruf, jeder Lead kommt
> ohne Herkunft an, und die Kampagne lässt sich nicht bewerten. Alles andere
> unten ist wichtig, aber nicht blockierend.
>
> Am 13.09. an der Seite nachgemessen, nicht angenommen:
> `websprint.kompagnon.eu` antwortet mit 200 und 1.011.007 Bytes. Von neun
> Merkmalen des Blocks finden sich **zwei** — `c.marketing` und `gtag(` —,
> und die waren vorher schon da. Kein `fbq(`, kein
> `connect.facebook.net`, keine Pixelnummer, kein `fbclid`, kein `_fbp`,
> kein `generate_lead`, keine `eventID`. Gegengeprüft an der fertigen Datei
> (1.018.227 Bytes): dort stehen **alle neun**. Die Suche taugt also, und
> die Abwesenheit ist echt.

---

## 1. Wo die Arbeit liegt

| | |
|---|---|
| `main` | **PR #57 ist am 13.09. um 11:16 gemerged** (Merge-Commit `49f31000`). Alles aus den Sitzungen vom 12. und 13.09. ist produktiv |
| `staging` | **gleichauf mit `main`** — 0 Commits Abstand |
| offener PR | keiner |

Nicht am Status gemessen, sondern am Zustand:

| | |
|---|---|
| Lauf #970 auf `main` | alle sieben Jobs `success`, **Deploy — Render: success** |
| Backend produktiv | `49f31000` · **live** · fertig 11:22:55Z |
| Frontend produktiv | `49f31000` · **live** · fertig 11:22:39Z |
| `/health` | `ok`, `startup_complete`, `startup_missing: []`, DB verbunden |

> **`f1a3ffb` ist produktiv** — der PDF-Dateiname überlebt jetzt einen Umlaut.
> **Bestätigt ist er damit noch nicht.** Belegt sind der ausgerollte Commit
> und ein grüner Test; ein produktiver Abruf eines PDFs mit Umlaut im
> Firmennamen hat noch nicht stattgefunden. Bis dahin gilt: plausibel, nicht
> gemessen. Was dafür nötig ist, steht in Abschnitt 3.3.

> **Richtiggestellt am 13.09.2026, zweimal am selben Tag.** Erst stand hier
> „14 Commits vor `main`, offener PR #56, wartet auf den Merge" — der Merge
> lief acht Stunden nach dem Schreiben dieser Zeile. Dann stand hier „4
> Commits, noch nicht produktiv" — auch das hielt nur Stunden. Ein
> Übergabestand altert an genau den Zeilen, die Zahlen nennen; wer ihn liest,
> prüft sie besser einmal nach.

---

## 2. Was produktiv nachgemessen ist (Stand 13.09.)

Geprüft an `api.kompagnon.group/api/widget/config`, nicht aus dem Gedächtnis:

| | Stand |
|---|---|
| Datenschutzlink im Widget | ✅ `kompagnon.eu/rechtliches/datenschutz` |
| Meta-Pixel im Widget | ✅ `1363198722345965` |
| Meta-Serverweg (CAPI) | ✅ `bereit: true`, Token und Pixel gesetzt |
| Kriterienzahl | 39 |
| Kaufadresse Check PLUS | ✅ **seit 13.09. eingetragen** — `…9Zm01` |
| Check PLUS im Teaser | **noch ohne Kaufknopf** — `verfuegbar: false`, weil der Katalog auf `draft` steht |
| Terminkalender im Widget | ✅ zeigt auf den Kalender des Systems |
| Kaufadresse Relaunch | **von außen nicht messbar** — siehe unten |
| Häkchentext im Widget | ✅ neue Fassung live (PR #55) |

Dass die Adresse aus der Datenbank kommt und nicht geerbt ist, ist geprüft:
`widget_check_plus_url` hat weder einen `ENV_FALLBACK` noch einen Eintrag in
`DEFAULTS` (`services/app_settings.py`). Der Wert kann nur eingetragen sein.

> **Richtiggestellt am 13.09.2026, wenige Stunden nach dem Eintrag.** Hier
> stand „Kaufadresse Relaunch: ❌ leer — `checkout_url` zeigt weiter in den
> Terminkalender". Das war eine Schlussfolgerung aus der falschen Zahl.
> `checkout_url` in `/api/widget/config` ist `termin_url(widget_booking_url)`
> — der **Terminkalender** des Widgets. Die Relaunch-Kaufadresse ist eine
> andere Einstellung (`bericht_kauf_relaunch_url`) und steht dort überhaupt
> nicht. Sie ist nur über `/api/acquisition/widget` lesbar, und die antwortet
> ohne Anmeldung mit **401**. Ob sie gefüllt ist, weiß von außen niemand —
> nachsehen kann das nur David im Werkzeug.
>
> Zwei Einstellungen, die beide „führt sonst in den Kalender" als Rückfall
> haben, sind leicht zu verwechseln. Genau diese Verwechslung war schon
> einmal ein Fehler im System: Als beide an `widget_checkout_url` hingen,
> überschrieb der dort eingetragene Wert den Kalender (Kommentar in
> `services/widget_report.py`). Jetzt habe ich sie im Bericht darüber
> verwechselt.
>
> **Ebenfalls genauer gefasst:** Aus `checkout_url == STANDARD_TERMIN_URL`
> folgt nicht, dass `widget_booking_url` *leer* ist — sie könnte auch auf
> genau diesen Wert gesetzt sein. Für den Knopf ist beides gleichwertig; für
> die Aussage ist es das nicht.

**Der fehlende Kaufknopf ist kein Fehler.** Leer heißt bewusst „Angebot ohne
Abschluss": Ein Knopf, der ins Leere führt, wird von niemandem gemeldet, ein
fehlender fällt auf. Für Check PLUS fehlt jetzt nur noch **eines** — der
Katalogstatus `live` (`verfuegbar = live UND Adresse`, siehe
`services/check_plus_angebot.py`). Der Knopf erscheint in dem Moment von
selbst; die Adresse liegt bereits.

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

**~~② Bestätigungsmail klicken.~~ Erledigt am 12.09.** Die Trichterschritte
**7 bis 9** (Klick → zweite Mail → Berichtsseite → PDF) sind zweimal ganz
durchlaufen: auf Staging mit echtem Inhalt (Anfrage 10, `nachhaltika.de` —
Mail 1 um 13:24, Mail 2 um 13:25:30, Berichtsseite 62/100, PDF 11 Seiten)
und produktiv mit deinem eigenen Klick (Anfrage 20, Audit 204 — Mail 1
21:19:58, Klick 21:20:18, Mail 2 sofort, PDF 12 Seiten). Belege in
`docs/tagesdokumentation/2026-09-12.md`, Abschnitt 3.

Der Durchlauf hat den Fehler mit dem PDF-Dateinamen gefunden. `f1a3ffb`
behebt ihn und ist seit dem 13.09., 11:23 Uhr produktiv — **bestätigt durch
einen echten Abruf ist er noch nicht**, siehe Abschnitt 3.3.

**② Meta-Konto einrichten.** Domain verifizieren und die
Ereignis-Priorisierung (Aggregated Event Measurement) setzen. Ohne beides
misst iOS-Verkehr unvollständig.

### 3.2 Bei David — im Werkzeug unter *Akquise → Widget*

Die Felder sind seit dem Ausrollen am 12.09., 21:31 Uhr da. Eines ist
nachweislich gefüllt; bei den übrigen vier sagt die Liste nur, **was
hineingehört** — ob sie leer sind, ist von außen nicht prüfbar (401, siehe
Abschnitt 2). Ein Blick ins Werkzeug klärt das in einer Minute.

| Feld | Wert | Wirkung, wenn leer |
|---|---|---|
| ~~Kaufadresse Check PLUS~~ | ✅ **eingetragen** (13.09. produktiv gemessen) | — |
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

- ~~**PR `staging → main` öffnen.**~~ **Erledigt am 12.09.: PR #56**, 15
  Commits, alle sieben CI-Jobs grün, von David gemerged. *Der Merge bleibt
  bei David — Claude merged nie selbst.*
- ~~**Trichterschritte 7–9 nachprüfen.**~~ **Erledigt am 12.09.**
  (Durchlauf, siehe 3.1) **und am 13.09.** (Absicherung): Schritt 9 hatte
  keinen Test, der die Route je bis zu einem PDF fährt — der einzige, der
  sie anfasste, prüfte ein 404. `tests/test_bericht_pdf_auslieferung.py`
  holt jetzt das ausgelieferte PDF und misst die Kopfzeile, die über die
  Leitung geht. Schritte 7 und 8 waren bereits am Gegenstand abgedeckt
  (`test_der_klick_bestaetigt_und_loest_die_zweite_mail_aus`).
- ~~**PageSpeed-Schlüssel**: nachgehen, warum er nichts liefert.~~
  **Erledigt am 12.09. — es war nichts zu reparieren.** Siehe Abschnitt 5.
- **OFFEN: den PDF-Dateinamen produktiv nachmessen.** `f1a3ffb` ist seit dem
  13.09., 11:23 Uhr ausgerollt, und 22 Tests halten ihn — aber **kein
  produktiver Abruf** hat ihn bisher bestätigt. Eine Reparatur ohne
  bestätigenden Lauf gilt hier als offen; genau diese Regel hat am 12.09.
  eine falsche Diagnose eine Woche am Leben gehalten.

  **Was es braucht, und warum es nicht allein geht.** Das PDF hängt am
  `report_token`, und den gibt es erst nach dem Klick in der
  Bestätigungsmail — also dieselben zwei Minuten wie am 12.09.:

  1. Claude startet produktiv eine Analyse gegen eine Seite mit Umlaut im
     Firmennamen. `nachhaltika.de` ist das richtige Prüfobjekt — daher kam
     der Fehler („Das Ingenieurbüro für nachhaltige Wirtschaft"), und
     `kas.kompagnon.group` taugt nicht, weil dort eine Anmeldewand vermessen
     wird.
  2. David klickt die Bestätigungsmail.
  3. Claude holt das PDF und liest die `content-disposition`: kein Rohbyte
     außerhalb von ASCII, `filename="…Ingenieurbuero…"` und
     `filename*=UTF-8''…Ingenieurb%C3%BCro…` nebeneinander.

  Schritt 1 legt einen **echten Lead in der Produktivdatenbank** an und
  verschickt eine Mail. Kurz vor dem Kampagnenstart ist das kein Nebenbei —
  deshalb erst auf Ansage.

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
und trägt den richtigen Betrag. **Die Kaufadresse steht seit dem 13.09.
produktiv im Werkzeug.** Offen ist nur noch der Katalogstatus: `draft` → `live`.

### 4.4 ~~Geht vor Montag ein PR auf?~~ **Entschieden am 13.09.**

Ja. PR #57 ist um 11:16 gemerged und um 11:23 ausgerollt — acht Commits,
darunter `f1a3ffb`. Die Freitagsregel wurde für den Kampagnenstart einmal
ausgesetzt; der Grund steht oben: 40 Sekunden Produktion gegen eine
Kampagnenwoche, in der jedes PDF beim Kunden mit deutschem Firmennamen falsch
heißt. Die Regel gilt danach unverändert weiter.

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
