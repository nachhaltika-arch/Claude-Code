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

## 3. Was noch offen ist

Alles Folgende braucht dich — eine echte Adresse, eine echte Website, die
Ziel-Landingpage.

- [ ] **Test-E-Mail aus dem Tool senden** (`Akquise → Analyse-Widget`).
      Erster Nachweis, dass der Weg über Brevo wirklich funktioniert.
- [ ] **Eine echte Anfrage durchlaufen lassen** mit eigener Adresse und echter
      Website: Widget → Audit → Teaser → Mail → Klick → Berichtsseite → PDF.
      Dabei prüfen, ob die Anfragenliste auf **abgerufen** springt.
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
`main.py::_run_migrations`**.

Dazu kommt: `create_all()` legt fehlende *Tabellen* an, rüstet aber niemals
*Spalten* an einer Tabelle nach, die es schon gibt. `widget_requests` behielt
damit die Form vom Tag der ersten Auslieferung.

Nichts davon ist laut gescheitert. Die Migrationsliste schluckt jeden
Statement-Fehler bewusst, der Endpunkt brach erst ab, als er die fehlende
Spalte anfasste, und die Tests sahen es nie — die Test-Datenbank wird mit
`create_all` aus den Modellen gebaut und hat die Spalte deshalb immer.

**Regel:** Neue Spalten gehören nach `main.py`. Die beiden anderen Dateien
sagen das jetzt in ihrem Kopf.

---

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
