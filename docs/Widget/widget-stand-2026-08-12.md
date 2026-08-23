# Analyse-Widget — Stand und offene Punkte

**Stand:** 2026-08-12
**Vorgänger:** `docs/widget-stand-2026-08-11.md` (die dortige Liste „Offen" ist
mit diesem Dokument abgearbeitet, bis auf die Punkte in Abschnitt 3)
**Ziel:** Das Widget in eine fremde Landingpage einbetten — technisch,
grafisch und in der Bedienung fertig.
**Branch:** `staging`, drei Commits (`ef5aa6c`, `e4e928f`, `7dcb99e`)

---

## 1. Die Pentest-Prüfung — vier Befunde, alle behoben

### 1.1 Jeder konnte jede Analyse lesen

Der Teaser lief auf der laufenden Nummer der Analyse:
`GET /api/widget/teaser/1`, `/2`, `/3`. Damit war die Tabelle von außen
durchzuzählen, ohne Login, ohne Token. Ausgegeben wurden Firma, Adresse,
Punktzahl und die größten Mängel — **auch für die Analysen, die im Tool über
die Lead-Akquise entstanden sind und nie etwas mit dem Widget zu tun hatten.**
Das ist die Interessentenliste, lesbar für jeden, der den Quelltext einer
Seite ansieht, die uns einbettet.

Jede Anfrage bekommt jetzt ihr eigenes `poll_token`, der Endpunkt löst darüber
auf. Getrennt von `report_token`, weil dieser Wert im JavaScript der Seite
steht — der Berichts-Token gehört allein in die E-Mail.

### 1.2 Die IP-Grenzen ließen sich mit einer Kopfzeile überspringen

`CF-Connecting-IP` wurde als erstes und bedingungslos vertraut, mit der
Begründung, Cloudflare setze den Wert und er sei nicht fälschbar. Vor dieser
Anwendung steht aber kein Cloudflare — das Widget ruft `*.onrender.com`
direkt auf. Der Wert war also reine Behauptung des Aufrufers. Wer ihn pro
Anfrage neu würfelte, hatte beide IP-Grenzen ausgehebelt und konnte allein
das Tageskontingent verbrauchen: 300 Analysen und 300 E-Mails an Adressen
seiner Wahl.

Vertrauen muss jetzt über `TRUSTED_PROXY_HEADER` erklärt werden. Ohne die
Variable zählt der letzte `X-Forwarded-For`-Eintrag, und das ist auf Render
der echte Aufrufer.

### 1.3 Bericht- und Bestätigungsseite gaben ihr eigenes Token preis

Beide hängen an einem Token in der Adresszeile und trugen keine
`Referrer-Policy` — ein Klick auf den Fußzeilen-Link reichte, und das Token
stand im `Referer` der Zielseite. Einrahmen ließen sie sich auch, womit der
Double-Opt-in-Klick zu etwas wird, das man einem Besucher unterschieben kann.
Beide senden jetzt `X-Frame-Options`, `Referrer-Policy`, `no-store`
und `nosniff`.

### 1.4 Linkziele aus den Einstellungen landeten ungeprüft im `href`

`esc()` entschärft Anführungszeichen, lässt `javascript:` aber stehen — und
dieser Link wird im Widget auf einer fremden Landingpage gerendert.
`safeHref()` verlangt jetzt `http` oder `https`.

Nebenbei: `email_sent` im Teaser war `bool(audit.id)`, also immer `true`.
Es meldet jetzt `report_sent_at`.

---

## 2. Die DSGVO-Prüfung — der Bericht wandert hinter einen Klick

**Das Problem:** Die eingetragene Adresse muss dem Eintragenden nicht gehören.
Bis jetzt entschied diese Person, was in einem fremden Postfach landet: der
fertige Bericht, die Punktzahl, die Liste der Mängel der eigenen Website, ein
PDF und ein Knopf zum Kaufen einer neuen Seite. Bestellt hatte das niemand.
Das ist unbestellte Werbung nach § 7 UWG — verschickt von uns, im Auftrag von
irgendwem, der Lust hatte, die Adresse eines Wettbewerbers einzutippen.

**Die Lösung (von David am 2026-08-12 entschieden):** Double-Opt-in vor dem
Bericht.

| | vorher | jetzt |
|---|---|---|
| Teaser im Widget | sofort | sofort (unverändert) |
| erste E-Mail | Bericht, Punktzahl, Mängel, PDF, Verkaufsknopf | „Für diese Adresse wurde eine Analyse angefordert" + Link |
| Punktzahl / Mängel | in der Mail | erst auf der Berichtsseite |
| PDF | Anhang | Download auf der Berichtsseite |
| Angebot | in der Mail | auf der Berichtsseite |
| Nachweis | keiner | `report_confirmed_at` beim ersten Abruf |

Wer die Mail nicht angefordert hat, erfährt nichts über die eigene Seite und
hört genau einmal von uns. Wer sie anfordert, klickt einmal und hat damit
belegt, dass die Adresse ihm gehört — erst dann sieht er das Angebot.

Die Anfragenliste im Tool unterscheidet deshalb jetzt **abgerufen** von
**versendet**. „Versendet" hieß nur, dass Brevo die Mail angenommen hat.

Der Marketing-Double-Opt-in bleibt unangetastet und getrennt davon: der regelt,
ob wir überhaupt Kontakt aufnehmen dürfen, nicht was im Bericht steht.

---

## 2a. CI-Umstellung und grafische Auffrischung

Widget, Berichts-Mail und Berichtsseite liefen auf **drei verschiedenen
Paletten, keine davon die CI**:

| Rolle | Bericht + Mail | Widget | CI |
|---|---|---|---|
| Dunkel | `#0F2E2B` | `#04293a` | `#004F59` Pantone 3165 |
| Mittel | — | `#207a92` | `#008EAA` Pantone 3135 |
| Akzent | `#F5C518` | `#FAE600` ✓ | `#FAE600` Pantone 3945 |

Ein Interessent traf im Widget auf eine Marke, in der Mail auf eine zweite und
im Bericht auf eine dritte.

`kompagnon/backend/services/brand.py` hält jetzt die Werte, mit denen das
Backend rendert — das Gegenstück zu `tokens.css` für alles, was ohne die
React-Anwendung ausgeliefert wird. Das Widget behält seinen eigenen
`:root`-Block, weil es bewusst eine einzelne Datei ohne Abhängigkeiten ist;
ein Test vergleicht die Werte.

**Was grafisch passiert ist:**

* **Bericht:** Kopf in Dark Teal mit Wortmarke, Punktzahl, Level und Balken.
  Danach die sechs Bereiche als Balken, bevor die 38 Einzelkriterien kommen —
  die Seite beantwortet erst „wo stehe ich", dann „warum". Kriterientabellen
  mit dunklem Kopf, Zahlen in Monospace, und sie rollen in ihrem eigenen
  Kasten, damit vier Spalten kein Telefon zur Seite schieben.
* **E-Mail:** Tabellen statt divs. Outlook auf Windows rendert mit der
  Word-Engine und ignoriert `max-width` auf einem div — dort lief die Mail
  über die volle Fensterbreite.
* **Bestätigungsseite:** derselbe Rahmen wie die Mail, mit Status-Scheibe.

**Zwei Entscheidungen, die drinstecken:**

* **Keine Webschriften, nirgends.** Die CI verlangt Noto Sans, aber die
  Berichtsseite öffnet ein Dritter und das Widget läuft auf fremden
  Landingpages. Ein Google-Fonts-Aufruf überträgt deren IP an Google ohne
  Einwilligung — genau das Problem, das Abschnitt 2 gerade beseitigt hat.
  Noto Sans wird angefragt, sonst springt die Systemschrift ein. In E-Mails
  greifen Webschriften ohnehin nicht.
* **Ein gelber Knopf je Fläche.** Auf der Berichtsseite bekommt ihn das PDF —
  dafür ist der Empfänger hergekommen. Das Angebot steht als heller Knopf
  darunter: es soll dastehen, aber nicht die Hand führen. Die beiden Stile
  liegen in `_angebot_block` nebeneinander, falls das je wieder zu drehen ist.

Nebenbei korrigiert: Die Bereichsbalken rechnen nur über tatsächlich geprüfte
Kriterien. Sonst sähe ein Bereich, der mangels API-Schlüssel nicht geprüft
wurde, aus wie einer, der durchgefallen ist.

## 2b. Der erste echte Durchlauf — und was er gefunden hat

Am 2026-08-12 über die Staging-Widget-Seite: `nachhaltika@gmail.com` /
`kompagnon.eu`, mit Einwilligungshaken. Ergebnis **65/100, Bronze**, ein
rechtlicher Ausschlussgrund. Die KI-Kriterien greifen (der Text nennt Koblenz,
ISB/BAFA und Kundennamen konkret), PageSpeed ebenso.

**Der Berichtslink war tot.** `{"detail":"Not Found"}`.

`api_base_url()` fiel auf die fest eingetragene **Produktiv**-Adresse zurück,
wenn `API_BASE_URL` fehlt — und die Variable ist im Staging-Blueprint nie
deklariert worden. Der Audit lief also auf Staging, das Token lag in der
Staging-Datenbank, und die E-Mail schickte den Empfänger zum Produktiv-Server,
der das Token nie gesehen hat. **Jeder Berichtslink, den Staging je verschickt
hat, war tot.** Der Rückfall war kein Sicherheitsnetz, sondern eine falsche
Antwort, die wie eine funktionierende aussah.

Der Code nimmt jetzt `RENDER_EXTERNAL_URL`, das Render für jeden Dienst selbst
setzt. Ein vergessener Eintrag zeigt damit auf den richtigen Host statt still
in eine andere Umgebung. Nötig wird `API_BASE_URL` erst mit eigener Domain
davor — steht so im Blueprint.

**Was am selben Durchlauf funktioniert hat:** Formular, Einwilligungshaken,
`poll_token`-Abfrage, Teaser, Mail-Zustellung über Brevo, Berichtsseite mit
allen Kriterien, PDF (82 KB, `application/pdf`, richtiger Dateiname).

### Offen: Brevo schreibt die Links um

Brevo ersetzt jeden Link durch einen Umleiter auf `sendibt3.com`
(Klick-Tracking). Drei Gründe, das für diese Mail abzuschalten:

* Der Empfänger sieht beim Überfahren eine wildfremde Domain — bei einer Mail,
  die auch bei jemandem landen kann, der sie nicht angefordert hat, ist das
  genau das Signal, das vom Klicken abhält.
* Brevo erfährt, wer welchen Bericht öffnet. Für die Zustellung ist das nicht
  nötig.
* Das Berichts-Token läuft durch einen fremden Umleiter.

Abschaltbar ist es im Brevo-Konto (Senders & IP → Tracking). Ob die
Transaktions-API zusätzlich einen Schalter pro Mail hat, ist ungeprüft.

## 3. Was noch offen ist

Alles Folgende braucht dich — eine echte Adresse, eine echte Website, die
Ziel-Landingpage.

- [x] **Test-E-Mail aus dem Tool senden** — durchgelaufen (David, 2026-08-12).
- [x] **Eine echte Anfrage durchlaufen lassen** — durchgelaufen, siehe 2b.
      Ein toter Berichtslink dabei gefunden und behoben.
- [ ] **In der Anfragenliste nachsehen**, ob der Eintrag auf **abgerufen**
      steht (`Akquise → Analyse-Widget`). Der Bericht wurde abgerufen, also
      muss `report_confirmed_at` gesetzt sein — nur konnte ich das ohne
      Admin-Zugang nicht selbst prüfen.
- [ ] **Brevo-Klick-Tracking abschalten** (Senders & IP → Tracking), siehe 2b.
- [ ] **Einbau in die Ziel-Landingpage** mit dem Einbaucode testen, auch auf
      dem Telefon.
- [ ] Danach: Bericht (PDF) und E-Mail grafisch fertigstellen, dann der
      Anforderungskatalog `docs/audit-anforderungen-2026-08-11.md`.

---

## 4. Ein Fallstrick, der heute Zeit gekostet hat

**Es gibt drei Migrationsdateien, und nur eine läuft.**

Der Teaser antwortete auf Staging mit `ProgrammingError`, weil die neuen
Spalten nie angelegt wurden. Sie standen in `migrations.py` — die wird aber
nur von Hand aufgerufen. `migrate.py` ebenso, obwohl im Kopf jahrelang
„Run automatically on startup" stand. Beim Start läuft **allein die Liste in
`migrations_runtime.py::run_migrations`**.

Dazu kommt: `create_all()` legt fehlende *Tabellen* an, rüstet aber niemals
*Spalten* an einer Tabelle nach, die es schon gibt. `widget_requests` behielt
damit die Form vom Tag der ersten Auslieferung.

Nichts davon ist laut gescheitert. Die Migrationsliste schluckt jeden
Statement-Fehler bewusst, der Endpunkt brach erst ab, als er die fehlende
Spalte anfasste, und die Tests sahen es nie — die Test-Datenbank wird mit
`create_all` aus den Modellen gebaut und hat die Spalte deshalb immer.

Nebenbei fiel auf: Die Anwendung fiel dabei **komplett** aus, nicht nur der
Teaser. SQLAlchemy selektiert immer alle Modellspalten, also scheiterte jede
Abfrage auf `widget_requests` — auch die Bestätigungsseite und die
Anfragenliste im Tool.

**Regel:** Neue Spalten gehören nach `main.py`. Die beiden anderen Dateien
sagen das jetzt in ihrem Kopf.

### Ein zweiter Fund, der dabei herausfiel

Die ~200 Statements liefen in **einer** Transaktion mit einem `commit()` am
Ende, jeder Fehler mit `pass` verschluckt. Auf PostgreSQL bricht das erste
fehlschlagende Statement die Transaktion ab; alles danach scheitert mit
„current transaction is aborted", und der `commit()` schreibt nichts. Ein
harmloser Fehler weit vorne konnte damit lautlos alles darunter entwerten.
Jedes Statement bekommt jetzt seine eigene Transaktion, und die Zahl der
ausgeführten sowie jede übersprungene stehen im Log.

**Ehrlich dazu:** Ob genau das die Ursache war, ist nicht bewiesen. Zwischen
dem Nachtragen der Spalten (`7dcb99e`) und dem ersten grünen Aufruf lagen
zwei weitere Deploys. Es kann auch schlicht sein, dass `7dcb99e` beim Prüfen
noch nicht ausgerollt war. Die Umstellung auf einzelne Transaktionen ist
davon unabhängig richtig — sie ist das übliche Muster und macht künftige
Fehlschläge im Log sichtbar statt unsichtbar.

---

## 4a. Auf Staging verifiziert (2026-08-12)

Geprüft nach dem Deploy, ohne eine Analyse zu starten oder Post zu verschicken:

| Prüfung | Ergebnis |
|---|---|
| `GET /api/widget/teaser/<text>` | 404 (vorher 500 wegen fehlender Spalte) |
| `GET /api/widget/confirm/<text>` | 404 mit `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` |
| `GET /api/widget/report/<text>/pdf` | 404 |
| `POST /api/widget/audit`, ungültige Mail | 400 |
| `POST /api/widget/audit`, `localhost` | 400 |
| `POST /api/widget/audit`, `169.254.169.254` | 400 |
| Einbett-Seite | trägt `safeHref`, `poll_token`, neuen Fußzeilentext; alter Text weg |
| `GET /api/widget/config` | liefert `criteria_count: 38` |

## 5. Zahlen

* Backend: 175 Tests grün (`pytest tests/`), vorher 167
* Frontend: 28 Tests grün, `npm run build` sauber
* `ruff check --select E9,F63,F7,F82` sauber (dieselben Regeln wie die CI)

## 6. Geänderte Endpunkte

| vorher | jetzt |
|---|---|
| `GET /api/widget/teaser/{audit_id}` | `GET /api/widget/teaser/{poll_token}` |
| — | `GET /api/widget/report/{token}/pdf` |

`POST /api/widget/audit` liefert `poll_token` statt `audit_id`.
`GET /api/acquisition/widget/requests` liefert zusätzlich `report_opened`.

---

## 7. Das PDF — vier Fehler und die CI (2026-08-12, Nachtrag)

Beim Auffrischen des Berichts-PDFs kamen Dinge heraus, die nicht die Farbe
betrafen. Alle vier waren in jedem bisher versendeten Bericht.

**Die Punktzahl war auf dem Deckblatt halb verdeckt.** Sie stand als
`<font size="48">` in einem Absatz mit `leading=14`; die Glyphen liefen aus
ihrer Zeilenbox, und der Stufenbalken zeichnete quer hindurch.

**Der Keyword-Ring erfand seine Zahlen.** Ohne Daten zeichnete er vier gleich
große Viertel mit je „25 %". Dieses Audit erhebt Keyword-Positionen überhaupt
nicht — der Empfänger las eine Verteilung seiner Website, die es nie gab. Der
Ring entfällt jetzt, und die Seite schreibt hin, dass nichts erhoben wurde.

**Die Summenzeile der Bewertungsmatrix lief aus der Tabelle.** In die 14 mm
breite Statusspalte wurde `level[:15]` geschrieben — „Homepage Standa",
sichtbar über den Rand hinaus. Dazu hielt die Schleife diese Zeile für einen
Kategoriekopf und legte ein `SPAN` über die Maximalpunkte.

**Die erste Zeile des Auditprotokolls war unlesbar.** Die Tabelle hat keine
Kopfzeile, erbte aber deren Formatierung (dunkel + weiße Schrift); die
Zebra-Schleife legte danach eine helle Fläche darüber.

### Nebenbei

* **Die Schrift war nie die, die im Code stand.** `_register_fonts` sucht
  DejaVu, reportlab 4 liefert das nicht mehr mit — der Aufruf lief jedes Mal in
  den Fehlerzweig, und jedes PDF ist in **Helvetica** gesetzt. Das mitgelieferte
  Vera wäre greifbar, kennt aber den Pfeil in „HTTP→HTTPS erzwungen" nicht
  (nachgemessen). Helvetica bleibt. Für die CI-Schrift müsste Noto Sans als TTF
  ins Repo — die OFL erlaubt das Mitliefern, es sind rund 1 MB Binärdateien.
  **Offene Entscheidung.**
* Jahr stand fest auf 2025 (Deckblatt und jede Fußzeile) → kommt aus dem
  Auditdatum.
* Rechtstabelle nannte TMG § 5 → DDG § 5 (seit 14.05.2024); der
  Kriterienkatalog auf derselben Seite sagte längst DDG.
* Schmales geschütztes Leerzeichen erschien in Helvetica als schwarzes
  Kästchen.
* Statusspalte sagte `O` / `+` / `-` → jetzt „erfüllt" / „teils" / „offen".
* Radarringe waren mit 2/4/6/8/10 ohne Einheit beschriftet → Prozent.
* Stufenabzeichen nahm den Medaillenton als Fläche mit weißer Schrift — auf
  Silber (`#C0C0C0`) kaum lesbar. Jetzt Dark Teal, Medaillenton als Balken.
* Palette war die **vierte** im Projekt (`#2c3e50`, `#f39c12`, `#e74c3c`) →
  `services/brand.py`.

### Nicht angefasst, aber aufgefallen

Die letzte Seite stellt eine **„Zertifizierungsaussage" mit Unterschriftszeile
für den Auftraggeber** aus. Beim Tool-Audit gibt es einen Auftraggeber; bei
einer Widget-Anfrage hat niemand etwas beauftragt. Ob dieselbe Seite in beiden
Fällen richtig ist, ist eine inhaltliche Frage — kein Fehler im Code.

### Nachtrag: Noto Sans eingebaut

`NotoSans-Regular.ttf` und `NotoSans-Bold.ttf` liegen jetzt in
`kompagnon/backend/assets/fonts/`, die OFL-Lizenz daneben — sie verlangt das
Mitliefern. 1,2 MB im Repo für die CI-Schrift im einzigen Dokument, das ein
Interessent behält. Die Diagramme nutzen dieselbe Schrift; matplotlib zeichnete
die Radarbeschriftung vorher in seiner Standardschrift.

**Der Wechsel hat sofort etwas kaputt gemacht — und das ist der nützlichere
Teil.** „HTTP→HTTPS erzwungen" steht so im Kriterienkatalog, und Noto Sans
(Latin-Greek-Cyrillic) hat keinen Pfeil. Gerendert wurde „HTTPHTTPS": kein
Kästchen, keine Warnung, nur eine Lücke mitten im Wort. Helvetica hatte das
Zeichen zufällig — darauf lässt sich nicht bauen.

`_clean_text` liest deshalb jetzt die Zeichentabelle der registrierten Schrift
(cmap bei TrueType, cp1252-Bereich bei Type 1) und ersetzt, was sie nicht
zeichnen kann: `→` wird `->`, `≥` wird `>=`, Haken werden `+`. Nicht
zugeordnete Zeichen werden zerlegt, und was davon übrig bleibt, fällt weg
statt als Loch stehenzubleiben.

Das gilt über feste Beschriftungen hinaus: Zusammenfassung, Mängelliste und
Empfehlungen schreibt die KI, und die kann jedes Zeichen ausgeben. Ein Emoji
im Bericht wäre auf genau dieselbe stille Weise verschwunden.

---

## 8. Zwei Mails statt einer (2026-08-12, von David entschieden)

Bis eben ging **eine** Mail raus, sobald das Audit fertig war, und sie trug
den Berichtslink. Der Klick darauf war der Nachweis, dass die Adresse dem
Empfänger gehört — der Nachweis kam also **nach** dem, was er schützen sollte.

Jetzt verlässt nichts über die Website das Haus, bevor die Adresse bestätigt
ist:

| Schritt | vorher | jetzt |
|---|---|---|
| Audit fertig | Mail mit Berichtslink | Mail **ohne** Berichtslink: „Bitte bestätigen Sie kurz Ihre Adresse" |
| Klick | öffnet den Bericht | bestätigt die Adresse, stößt Mail 2 an |
| Mail 2 | — | „Ihre Website-Analyse ist fertig" + Berichtslink |
| Nachweis | `report_confirmed_at` (Bericht geöffnet) | `verified_at` (Adresse bestätigt), zusätzlich weiterhin `report_confirmed_at` |

Wer eine fremde Adresse einträgt, löst dort genau **eine** neutrale Nachricht
aus. Ohne Klick folgt nichts.

**Technisch:** `verify_token` wird für jede Anfrage erzeugt — anders als
`confirm_token`, den es nur mit gesetztem Marketing-Haken gibt.
`GET /api/widget/verify/{token}` setzt `verified_at` und stellt die
Berichts-Mail in einen Hintergrundauftrag. Ein zweiter Klick (Postfach-Scanner
folgen Links automatisch) antwortet „bereits bestätigt" und schickt nichts
noch einmal.

**Der Marketing-Opt-in bleibt getrennt** und steht weiter in Mail 2 mit
eigenem Link. Die Adresse zu bestätigen und in Kontaktaufnahme einzuwilligen
sind zwei Entscheidungen; ein Klick darf nicht für beide stehen.

**Preis:** ein Klick mehr bis zum Bericht. Das ist der Tausch — die Adresse
ist damit bestätigt statt angenommen.

Neue Spalten (in `migrations_runtime.py::run_migrations`, der Liste die läuft — siehe
Abschnitt 4): `verify_token`, `verify_sent_at`, `verified_at`.
Die Anfragenliste im Tool zeigt jetzt: *wartet auf Bestätigung → bestätigt →
versendet → abgerufen*.

---

## 9. Der Blocker: das Double-Opt-in bestätigte sich selbst — gelöst

**Befund.** In vier Live-Durchläufen kam die Berichts-Mail 15 Sekunden bis
4 Minuten nach der Bestätigungsmail, **ohne dass jemand geklickt hatte**:

| | Mail 1 | Mail 2 | Abstand |
|---|---|---|---|
| doi | 11:28:50 | 11:29:05 | 15 s |
| doi2 | 11:47:33 | 11:48:30 | 57 s |
| doi3 | 11:53:38 | 11:57:51 | 4 min |
| doi4 | 12:30:42 | 12:31:26 | 44 s |

Damit war die Bestätigung wertlos als Nachweis — und genau sie ist die
Begründung dafür, überhaupt an eine ungeprüfte Fremdadresse zu schreiben.

**Zwei Anläufe.** Der erste (GET → POST) griff nicht: Der deployte
GET-Endpunkt war nachweislich passiv (der unbenutzte Opt-in-Link lieferte nur
das Formular), trotzdem bestätigte sich weiter alles von selbst. Es wurde also
tatsächlich abgeschickt — mehr, als einem Postfach-Scanner zuzutrauen war.

**Was jetzt greift.** Das Formular verlangt den Beleg einer echten Bedienung.
Das versteckte Feld wird **leer** ausgeliefert; sein Wert steht in einem
`data`-Attribut am Knopf und wandert erst bei `pointerdown`, `touchstart` oder
Tastendruck ins Feld. Der Server rechnet ihn als HMAC über den Token nach.
Blind abschicken, Seite nur rendern, kein JavaScript — alles ergibt ein leeres
Feld und verändert nichts; die Seite kommt mit einem Hinweis zurück.

**Und wir sehen jetzt, wer es war.** Bei Abweisung landen Methode,
User-Agent und IP im Log; bei Erfolg stehen sie in `verified_user_agent` und
`verified_ip`. Das fehlte, solange ich geraten habe.

**Live bewiesen (doi5, 2026-08-12):**

| Zeit | Ereignis |
|---|---|
| 14:07:35 | Mail 1 |
| 14:07–14:14 | nichts — sieben Minuten ohne Selbstbestätigung |
| ~14:14 | echter Mausklick auf den Knopf |
| 14:14:40 | Mail 2 mit dem Berichtslink |

Derselbe Schutz sitzt auf dem Marketing-Opt-in. Eine von einem Scanner
erteilte Einwilligung wäre als Nachweis wertlos, und das ist der einzige
Grund, warum es den Datensatz gibt.

**Preis:** Bestätigen braucht JavaScript. Der Weg hierher führt über ein
JavaScript-Widget, insofern keine neue Anforderung; `<noscript>` sagt es.
