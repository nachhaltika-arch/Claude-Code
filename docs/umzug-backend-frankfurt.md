# Umzug: Produktiv-Backend von Oregon nach Frankfurt (L-34)

> Plan, erstellt am 2026-08-15 für den Start am 2026-08-16.
> Ausgangslage und Begründung stehen in `stand-2026-08-15.md` § 7.

---

## Warum

Am 15.08. hat sich gezeigt, dass die Region kein Performance-Detail ist,
sondern die Ursache unter zwei Folgeschäden:

- **Die Startphasen kippten an der Latenz** (L-41). Jede Datenbankabfrage
  kostet ~1 s statt ~0,1 s; die Migration brauchte 215 s und hielt den einzigen
  Worker, während sieben Phasen in ihren Timeouts verliefen. Produktiv gab es
  monatelang keinen Scheduler.
- **Die Datenbank muss im offenen Internet stehen** (L-44). Render dokumentiert:
  „services in *different* regions can't communicate directly over a private
  network." Das Backend in Oregon *kann* die interne Adresse der Frankfurter
  Datenbank nicht erreichen — deshalb `0.0.0.0/0` und eine externe Adresse,
  während Staging jeden externen Verkehr blockt.

Dazu: Die Datenbank liegt in Frankfurt, weil der Blueprint es so vorsieht
(„Region: frankfurt — DSGVO-relevant"). Das Backend, das die Daten verarbeitet,
steht in den USA.

**Ein Umzug löst beides auf einmal** und macht nebenbei jede Abfrage zehnmal
schneller.

---

## Was der Umzug technisch bedeutet

Render kann die Region eines bestehenden Dienstes **nicht** ändern
(dokumentiert). Es muss ein **neuer Dienst** in Frankfurt entstehen, und der
bekommt eine **neue Adresse**.

Das ist die eigentliche Arbeit. Nicht der Umzug — die Adresse.

### Wer auf `claude-code-znq2.onrender.com` zeigt

| Wo | Art | Umschaltbar |
|---|---|---|
| `frontend/src/config.js` | Rückfallwert, sonst `REACT_APP_API_URL` | ja, Variable |
| `services/base_urls.py` | **seit 16.08. der einzige Rückfall im Backend**; davor `API_BASE_URL`, dann `RENDER_EXTERNAL_URL` (setzt Render selbst) | ja |
| ~~`services/widget_report.py`~~, ~~`routers/files.py`~~ | hatten je eine eigene Zeile mit der Produktiv-Adresse — zusammengelegt (`22480d1`) | erledigt |
| **Bereits versendete Berichts-Mails** | **fest in der Mail** | **nein** |
| **Webhook bei Trackdesk** | bei einem Dritten registriert | nur dort |
| **Webhook bei Netlify** | bei einem Dritten registriert | nur dort |
| **Webhook bei Brevo** | bei einem Dritten registriert | nur dort |

**Die versendeten Berichtslinks sind der Punkt, der weh tut.** Jeder Empfänger
einer Widget-Analyse hat eine Mail mit
`https://claude-code-znq2.onrender.com/api/widget/report/{token}`. Wird der alte
Dienst abgeschaltet, sind diese Links tot — bei genau den Interessenten, die wir
gewinnen wollten.

---

## Die Entscheidung vor dem Umzug: eigene Domain oder nicht

### Weg A — erst eine eigene Domain, dann umziehen *(empfohlen)*

1. `api.kompagnon.group` auf den **alten** Dienst legen
2. Alles darauf umstellen: `REACT_APP_API_URL`, `API_BASE_URL`, die drei
   Webhooks bei Trackdesk, Netlify und Brevo
3. Ein paar Tage laufen lassen, bis nichts mehr die `onrender.com`-Adresse ruft
4. Neuen Dienst in Frankfurt bauen, Domain umhängen, alten Dienst abschalten

**Dauer:** zwei Sitzungen plus Wartezeit.
**Vorteil:** Der Umzug selbst ist dann unsichtbar — und **jeder künftige**
Umzug auch. Die versendeten Links zeigen ab Schritt 2 auf eine Adresse, die uns
gehört.

### Weg B — direkt umziehen, alten Dienst als Brücke behalten

1. Neuen Dienst in Frankfurt bauen und testen
2. Umschalten (Frontend-Variable, Webhooks)
3. **Alten Dienst weiterlaufen lassen**, heruntergestuft, nur damit die alten
   Berichtslinks funktionieren

**Dauer:** eine Sitzung.
**Nachteil:** Der alte Dienst bleibt auf unbestimmte Zeit als Altlast stehen und
kostet weiter. Das Problem ist verschoben, nicht gelöst.

**Empfehlung: Weg A.** Der Umzug ist ohnehin fällig; ohne eigene Domain
wiederholt sich diese Fesselung beim nächsten Mal. Wenn morgen nur eine Sitzung
Zeit ist, sind die Schritte 1–2 aus Weg A ein sinnvolles Tagesziel — sie sind
für sich genommen schon ein Gewinn und ohne Risiko für den Betrieb.

---

## Ablauf (Weg A, Schritte 1–2 für morgen)

### Vorher

- [x] **Entschieden am 16.08.: `api.kompagnon.group`.** DNS liegt bei IONOS
      (`ns*.ui-dns.*`), die Subdomain war frei, und die Domain ist bereits die
      bei Brevo verifizierte Absenderdomain — Mail und API an einer Stelle.
      `kompagnon.eu` (EuroDNS) und `kompagnon.de` (de-nserver) bleiben unberührt
- [ ] **Datenbank-Sicherung**: Render Recovery-Punkt notieren, damit es einen
      Rückweg gibt
- [x] Aufschreiben, was gerade läuft — **gemessen 16.08., 12:41 UTC:**
      produktiv `/health` 200, `startup_complete: true`, `scheduler_running:
      true`, `startup_missing: []`, **2,10–2,63 s**; `/info`
      `environment: production`, `database_configured: true` (keine
      Zugangsdaten mehr). Staging zum Vergleich: **0,16–0,24 s**.
      Der Faktor zwischen beiden ist die ganze Begründung dieses Umzugs

### Domain vor den alten Dienst

- [ ] Render → `kompagnon-backend` → Settings → Custom Domain → Domain eintragen
- [ ] DNS-Eintrag beim Anbieter setzen (Render nennt den Zielwert)
- [ ] Warten, bis Render das Zertifikat ausgestellt hat
- [ ] Prüfen: `https://<domain>/health` antwortet wie die alte Adresse

### Alles auf die Domain umstellen

- [ ] `REACT_APP_API_URL` beim Frontend → neue Domain (löst Frontend-Deploy aus)
- [ ] `API_BASE_URL` beim Backend → neue Domain (damit Berichtslinks und
      Datei-Adressen sie nutzen; sie hat Vorrang vor `RENDER_EXTERNAL_URL`)
- [ ] Webhook-Adresse bei **Trackdesk** ändern
- [ ] Webhook-Adresse bei **Netlify** ändern
- [ ] Webhook-Adresse bei **Brevo** ändern
- [ ] Im Code die Rückfallwerte auf die Domain ändern — es sind seit dem
      16.08. nur noch zwei Stellen: `services/base_urls.py`
      (`FALLBACK_API_BASE_URL`) und `frontend/src/config.js`. Dazu die
      Beispieladressen in `render-staging.yaml`, `ci.yml` und der
      Trackdesk-Anleitung. **Erst wenn die Domain antwortet** — vorher zeigt
      jeder Rückfall auf einen Namen, den es noch nicht gibt.
      Commit auf `staging`, PR wie üblich freitags

### Prüfen

- [ ] Tool anmelden, Leadliste, ein Audit ansehen
- [ ] Eine Widget-Analyse über die neue Domain laufen lassen, Mail und
      Berichtslink prüfen
- [ ] Alte Adresse muss weiter funktionieren (sie tut es, solange der Dienst
      steht) — die alten Mails hängen daran

---

## Der eigentliche Umzug (danach, eigene Sitzung)

- [ ] Neuen Web Service in **Frankfurt** anlegen: gleiches Repo, Branch `main`,
      gleiche Build- und Start-Befehle, Plan „Standard"
- [ ] **Alle** Umgebungsvariablen übertragen (Render kann exportieren);
      `DATABASE_URL` dabei auf die **interne** Adresse umstellen — das ist der
      Punkt, an dem die Datenbank aus dem Internet verschwinden kann
- [ ] `ENVIRONMENT=production` nicht vergessen (war beim alten Dienst nie
      gesetzt, siehe L-42)
- [ ] Neuen Dienst testen, **ohne** Domain: `/health` muss
      `startup_complete: true` und `scheduler_running: true` zeigen, und der
      Start sollte deutlich unter 264 s liegen
- [ ] Domain vom alten auf den neuen Dienst umhängen
- [ ] Alten Dienst suspendieren (nicht löschen — Rückweg)
- [ ] **Dann L-44**: Inbound-Regel der Datenbank von `0.0.0.0/0` auf „kein
      externer Verkehr" wie bei Staging
- [ ] Nach ein paar ruhigen Tagen: alten Dienst löschen

### Gelegenheit beim Schopf

Der neue Dienst sollte **über einen Blueprint** entstehen. Das schließt L-35
mit — heute ist produktiv nichts blueprint-verwaltet, weshalb `DATABASE_URL`
dort von Hand gepflegt wird und die Rotation mehr Arbeit war als auf Staging.

**Der Blueprint liegt seit dem 16.08.: `kompagnon/render-produktiv.yaml`.** Er
beschreibt den neuen Dienst, nicht den alten, und trägt alle Variablen, die der
Quelltext liest — der alten `render.yaml` fehlen davon 32, darunter vier
Webhook-Geheimnisse und die beiden Schlüssel, ohne die gespeicherte
Zugangsdaten unlesbar bleiben. Zwei Dinge sind darin bewusst offen gelassen,
weil ein geratener Wert dort teuer wäre:

- **Die Datenbank steht nicht im Blueprint.** Ein `databases:`-Block trifft
  `Kompangnon-dB` nur zeichengenau; trifft er daneben, legt Render eine
  zweite, leere Datenbank an, `create_all` füllt sie, und alles sieht gesund
  aus. `DATABASE_URL` wird deshalb von Hand gesetzt.
- **Die Umschreibungsregeln der Static Site** stehen heute nur im Dashboard.
  Eine falsche Regel verschluckt `/embed/audit-widget.html` lautlos — 200 statt
  Datei. Vor dem Umzug abschreiben.

---

## L-44 vorbereitet: Wer erreicht die Datenbank heute von außen

Die Inbound-Regel steht produktiv auf `0.0.0.0/0`. Bevor sie zugeht, muss
feststehen, wer dadurch die Verbindung verliert. Geprüft am 2026-08-16:

| Zugriff | Braucht offene Regel? | Nach dem Umzug |
|---|---|---|
| Produktiv-Backend (Oregon) | **ja** — interne Adressen lösen nicht über Regionen hinweg auf | entfällt, das ist der Umzug |
| CI (GitHub Actions) | nein — vier Jobs, alle mit eigenem Postgres-Container bzw. SQLite | unverändert |
| Staging-Backend | nein — eigene DB, `ipAllowList: []` | unverändert |
| Netlify, Brevo, Trackdesk, Stripe | nein — sie sprechen mit dem Backend, nie mit der DB | unverändert |
| Davids Rechner (DBeaver, `pg_dump`) | **ja** | siehe unten |

Der letzte Punkt ist der einzige, der eine Entscheidung braucht — und dabei
fällt ein Widerspruch auf: `docs/local-dev-with-render-db.md` beschreibt genau
diesen Weg, sagt aber ausdrücklich **„Nur Staging-DB nutzen"**. Die Staging-DB
blockt externen Verkehr seit jeher. Der dokumentierte Weg funktioniert also
heute nur gegen die Produktiv-DB — gegen genau die, vor der die Anleitung
warnt.

Damit ist die Regel keine Einschränkung, sondern eine Korrektur: Für einen
Blick in die Daten gibt es `psql` über die Render-Shell und
`render psql <dienst>` über die CLI. Beides läuft innerhalb von Render und
braucht die offene Regel nicht. `docs/local-dev-with-render-db.md` gehört
danach entsprechend korrigiert.

**Reihenfolge:** Die Regel geht zu, *nachdem* der neue Dienst in Frankfurt über
die interne Adresse läuft — nicht vorher. Vorher nimmt sie dem alten Dienst in
Oregon die Datenbank weg, und das ist ein Ausfall, kein Umzug.

---

## Rückweg

Bis zum Umhängen der Domain ist jeder Schritt umkehrbar: Der alte Dienst läuft
unverändert weiter, der neue ist bis dahin nur eine zweite Adresse ohne
Verkehr. Geht nach dem Umhängen etwas schief, zeigt die Domain in wenigen
Minuten wieder auf den alten Dienst.

Der einzige Schritt ohne einfachen Rückweg ist das **Löschen** des alten
Dienstes — deshalb steht es am Ende und mit Abstand.

---

## Was der Umzug **nicht** löst

- Die Datenbank bleibt `Basic-256mb` mit 1 GB Speicher (18,7 % belegt)
- „Kompangnon-dB" behält seinen Tippfehler im Namen (L-35)
- Das Frontend ist eine Static Site auf „Global" — davon ist nichts betroffen
