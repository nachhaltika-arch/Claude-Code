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
| **Gespeicherte Seiteninhalte in der DB** | absolute Bild-Adressen, vom Editor hineingeschrieben | **erledigt 16.08.** |
| **Bereits versendete Berichts-Mails** | **fest in der Mail** | **nein** |
| **Elf Webhook-Endpunkte** | bei Dritten registriert | nur dort — siehe die vollständige Liste unten |

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

### Vorher — am 19.08. gemeinsam im Dashboard erhoben

Alles Folgende ist **gemessen**, nicht erinnert. Es stand bis dahin nirgends
im Repo, und genau das war der Punkt.

| Frage | Antwort | Bedeutung für den Umzug |
|---|---|---|
| **Wiederherstellungspunkt** | Point-in-Time über **7 Tage**, dazu Exporte (≥ 7 Tage) | Der Rückweg steht. Beantwortet zugleich die offene Frage aus L-11 |
| **Dateien auf `/var/data`** | **0** (32 K von 974 M belegt, das Verzeichnis selbst) | **Kein Kopierschritt.** Der heikelste Teil des Umzugs entfällt |
| **Umschreibungsregeln der Static Site** | Genau **eine**: `/*` → `/index.html`, Action *Rewrite* | Muss am neuen Dienst nachgebaut werden — eine Zeile |
| **Verschluckt die Regel das Widget?** | **Nein.** `/embed/audit-widget.html` liefert 31.464 Bytes mit Titel „KOMPAGNON — Gratis Webseiten-Analyse", 0 React-Merkmale, verschieden von `index.html` (987 B) | Die Sorge weiter unten war unbegründet. Render wendet die Regel nur als Rückfall an |

**Kennungen, die beim Umzug gebraucht werden:**

| Was | Wert |
|---|---|
| Backend (Oregon) | `srv-d74ptinfte5s73bjbv90` — Standard, Python 3, Branch `main` |
| Frontend (Static) | `srv-d74qd7oule4c73f7v4t0` — Domain `kas.kompagnon.group` |
| Datenbank | `dpg-d74t6ttm5p6s73fd6qv0-a` — **`Kompangnon-dB`**, Basic-256mb, Postgres 18, Frankfurt, 19,02 % von 1 GB |
| Interne Adresse Backend | `claude-code-znq2:10000` |

**Latenz, frisch gemessen (19.08., 18:49 UTC):** Produktiv `/health` **2,6 · 3,1
· 3,2 s** — Staging in Frankfurt **0,23 · 0,17 · 0,18 s**. Faktor **15**. Das
ist die ganze Begründung, und sie gilt heute.

### Vorher

- [x] **Entschieden am 16.08.: `api.kompagnon.group`.** DNS liegt bei IONOS
      (`ns*.ui-dns.*`), die Subdomain war frei, und die Domain ist bereits die
      bei Brevo verifizierte Absenderdomain — Mail und API an einer Stelle.
      `kompagnon.eu` (EuroDNS) und `kompagnon.de` (de-nserver) bleiben unberührt
- [x] **Datenbank-Sicherung**: Point-in-Time über 7 Tage — erhoben 19.08.
- [x] **Zahl der Dateien auf dem Datenträger**: **0** — erhoben 19.08. Der
      Umzug ist damit **kein** Kopierschritt
- [x] Aufschreiben, was gerade läuft — **gemessen 16.08., 12:41 UTC:**
      produktiv `/health` 200, `startup_complete: true`, `scheduler_running:
      true`, `startup_missing: []`, **2,10–2,63 s**; `/info`
      `environment: production`, `database_configured: true` (keine
      Zugangsdaten mehr). Staging zum Vergleich: **0,16–0,24 s**.
      Der Faktor zwischen beiden ist die ganze Begründung dieses Umzugs

### Domain vor den alten Dienst

- [x] **Erledigt 16.08.** CNAME `api` → `claude-code-znq2.onrender.com` bei
      IONOS, danach Custom Domain am Dienst. Zertifikat von Google Trust
      Services, gültig 16.08. → 14.11.2026. `https://api.kompagnon.group/health`
      antwortet identisch zur alten Adresse.
      Reihenfolge-Fund: Vor dem Eintrag in Render antwortete `http://` bereits
      mit 301, `https://` aber ohne Zertifikat — Renders Edge nimmt den Namen
      also an, lange bevor er ihm gehört. Das sieht aus wie ein halber Erfolg
      und ist keiner.

### Alles auf die Domain umstellen

- [x] **`API_BASE_URL` beim Backend gesetzt (16.08.).** Sie existierte vorher
      **gar nicht** — der Umzug hat damit nebenbei zwei Rückfälle abgestellt,
      die produktiv scharf waren (`files.py`, `leads.py`). Deploy ohne Ausfall,
      `startup_complete` und `scheduler_running` grün.
- [x] **`REACT_APP_API_URL` beim Frontend gesetzt (16.08.).** Im
      ausgelieferten Bundle nachgeprüft, dazu Preflight und GET gegen die neue
      Domain mit der Frontend-Herkunft: `access-control-allow-origin` stimmt.
- [ ] Webhook-Adressen bei den Dritten ändern — **elf Endpunkte, nicht drei.**
      Die vollständige Liste steht unter „Die elf Webhook-Endpunkte" weiter
      unten; sie ist am 19.08. am laufenden Dienst gemessen, nicht geschätzt
- [x] **Im Code die Rückfallwerte auf die Domain geändert — bereits am 16.08.
      erledigt** (`714b441`), der Haken fehlte nur. Nachgeprüft am 19.08.:
      `services/base_urls.py` trägt `FALLBACK_API_BASE_URL =
      "https://api.kompagnon.group"`, `frontend/src/config.js` denselben Wert.
      Die verbliebenen `onrender.com`-Zeilen in `render-staging.yaml` sind
      **Staging**-Adressen und bleiben richtig; in `ci.yml` steht gar keine

### Prüfen

- [ ] Tool anmelden, Leadliste, ein Audit ansehen
- [ ] Eine Widget-Analyse über die neue Domain laufen lassen, Mail und
      Berichtslink prüfen
- [ ] Alte Adresse muss weiter funktionieren (sie tut es, solange der Dienst
      steht) — die alten Mails hängen daran

---

## Die elf Webhook-Endpunkte — gezählt am 19.08. am laufenden Dienst

Der Plan nannte oben **drei** Webhooks bei Dritten. Der Dienst kennt **elf**.
Gemessen wurde nicht am Quelltext, sondern an `GET /openapi.json` der
Produktiv-Adresse — 401 Routen, davon diese:

| Endpunkt | Wer ruft dort an | Geheimnis | Im Plan bisher |
|---|---|---|---|
| `POST /api/webhooks/trackdesk` | Trackdesk | `TRACKDESK_WEBHOOK_SECRET` | ja |
| `POST /api/webhooks/netlify/audit-anfrage` | Netlify | `NETLIFY_WEBHOOK_SECRET` | als *ein* Netlify-Haken |
| `POST /api/webhooks/netlify/kontakt` | Netlify | `NETLIFY_WEBHOOK_SECRET` | — |
| `POST /api/mail-events/brevo/{secret}` | Brevo | Geheimnis **im Pfad** | ja |
| `POST /api/payments/webhook` | **Stripe** | `STRIPE_WEBHOOK_SECRET` | **nein** |
| `POST /api/geo-payments/webhook` | **Stripe** | `STRIPE_WEBHOOK_SECRET_GEO` | **nein** |
| `POST /api/webhooks/facebook` | unbekannt | `WEBHOOK_SECRET` | nein |
| `POST /api/webhooks/linkedin` | unbekannt | `WEBHOOK_SECRET` | nein |
| `POST /api/webhooks/google` | unbekannt | `WEBHOOK_SECRET` | nein |
| `POST /api/webhooks/postkarte` | unbekannt | `WEBHOOK_SECRET` | nein |
| `POST /api/webhooks/telefon` | unbekannt | `WEBHOOK_SECRET` | nein |

**Stripe fehlte ganz.** Zwei getrennte Registrierungen mit zwei getrennten
Geheimnissen — Buch-Checkout und GEO. Beide zeigen heute auf die alte Adresse.
Sie sind produktiv nicht scharf (`STRIPE_SECRET_KEY` fehlt, siehe die offenen
Punkte vom 18.08.), aber wer den Schlüssel setzt, ohne die URL zu ändern,
verkauft an einen Dienst, den es nach dem Umzug nicht mehr gibt — und Zahlungen
verschwinden still, weil ein fehlgeschlagener Webhook den Kauf nicht abbricht.

**„Unbekannt" heißt unbekannt, nicht „unwichtig".** Ob die fünf Lead-Wege bei
Facebook, Google oder einem Zapier-Zwischenstück registriert sind, steht
nirgends im Repo. Zwei Messwerte grenzen es ein: `WEBHOOK_SECRET` war produktiv
nie gesetzt, also weist der Server dort seit dem 16.08. **jeden** Aufruf ab —
und `webhook_log` war am 19.08. **leer**. Es kommt heute also nichts an. Das
ist kein Beleg dafür, dass nichts registriert ist; es ist einer dafür, dass
beim Umzug nichts kaputtgehen kann, was nicht schon still steht.

**Zu tun, bevor der alte Dienst abgeschaltet wird:** Bei Trackdesk, Netlify,
Brevo und Stripe nachsehen, welche URL dort tatsächlich eingetragen ist, und
sie auf `https://api.kompagnon.group/...` umstellen. Die Domain zeigt heute
noch auf Oregon — das Umstellen ist also **jetzt schon** gefahrlos möglich und
genau der Zweck von Weg A.

### Nebenbefund am selben Tag: `GET /api/webhooks/log` war offen

Beim Zählen fiel auf, dass diese zwölfte Route **ohne Anmeldung** mit 200
antwortete — `SELECT *` über `webhook_log`, also Mailadressen und Firmen
eingehender Leads, mit ungedeckeltem `limit`. Geschlossen am 19.08. (`ef08c31`,
zwölf Tests). Sie steht hier, weil sie zum selben Bild gehört: Der Bereich
„Webhooks" war nie als Ganzes durchgesehen worden.

---

## Was der Blueprint trägt — Abgleich vom 19.08.

`kompagnon/render-produktiv.yaml` behauptet, alle Variablen zu tragen, die der
Quelltext liest. Nachgezählt: **44 Schlüssel im Blueprint, 56 im Quelltext
gelesen.** Die Differenz sieht nach zwölf Lücken aus und ist keine — jede der
17 Abweichungen (in beide Richtungen) hat einen Grund:

| Gruppe | Warum die Abweichung in Ordnung ist |
|---|---|
| `PORT`, `RENDER_EXTERNAL_URL`, `RENDER_INTERNAL_HOSTNAME` | setzt Render je Dienst selbst |
| `ADMIN_*`, `AUDITOR_*`, `NUTZER_*`, `KUNDE_*` (Demo-Konten) | der Seed läuft nur, wenn `ENVIRONMENT` **nicht** `production` ist |
| `SMTP_HOST/PORT/USER/PASSWORD/FROM/SENDER_*` | produktiv bewusst leer — der Versand läuft über die Brevo-API; am Dienst gemessen: `/info` meldet `smtp_configured: false` |
| `USE_MOCK_EMAIL` | Vorgabe ist `false`, und `false` ist der gewünschte Zustand |
| `PAGESPEED_API_KEY`, `NETLIFY_VORSCHAU_SITE_ID` | werden über eine Konstante bzw. einen Aliasnamen gelesen — meine Suche fand sie nicht, der Quelltext nutzt sie sehr wohl |
| `REACT_APP_*`, `PYTHON_VERSION` | gehören zur Static Site bzw. zur Laufzeit |

**Ergebnis: keine echte Lücke.** Der Blueprint ist umzugsreif.

Was dieser Abgleich **nicht** beantworten kann: ob am laufenden Oregon-Dienst
Variablen gesetzt sind, die weder Quelltext noch Blueprint kennen. Das zeigt
nur der Export im Dashboard — der Render-MCP ist auch am 19.08. `unauthorized`.

### Zwei Korrekturen am Plan

- **`ENVIRONMENT=production` ist gesetzt**, entgegen der Notiz weiter unten
  („war beim alten Dienst nie gesetzt, siehe L-42"). Am 19.08. gemessen:
  `/info` gibt `environment: production` aus, und dieses Feld ist nichts
  anderes als `os.getenv("ENVIRONMENT", "development")`. Die Folge ist
  beruhigend: Die vier Demo-Konten werden produktiv **übersprungen**. Für den
  neuen Dienst bleibt der Punkt trotzdem stehen — dort ist die Variable neu zu
  setzen, und wer sie vergisst, legt sich Demo-Konten in die Produktivdaten.
- **Der Bereitschafts-Check hängt an der Service-ID, nicht an einer Adresse.**
  Der Deploy-Job holt `serviceDetails.url` über die Render-API und prüft
  `/health` dort. Beim Umzug ist also wirklich **nur** die Repository-Variable
  `RENDER_SERVICE_BACKEND_PROD` zu ändern; in `ci.yml` steht keine URL, die
  jemand vergessen könnte.

---

## Planänderung vom 19.08.: kein Blueprint, sondern von Hand

Der Plan sah vor, den neuen Dienst **über den Blueprint** entstehen zu lassen
und damit L-35 gleich mitzuschließen. Beim Anlauf stellte sich heraus, dass
drei Dinge dagegen stehen — alle drei am Objekt geprüft, nicht vermutet:

1. **Namenskonflikt mit zwei laufenden Diensten.** Der Blueprint benennt
   `kompagnon-backend` **und** `kompagnon-frontend`; beide gibt es. Das
   Umbenennen des alten Dienstes ließ sich im Dashboard **nicht speichern** —
   der Knopf „Save changes" bleibt inaktiv, auch nach mehreren Versuchen.
2. **Die Datei liegt nicht, wo Render sucht.** Es gibt kein `render.yaml` im
   Wurzelverzeichnis, nur `kompagnon/render-produktiv.yaml`.
3. **Das laufende Frontend würde mitübernommen.** Es soll unangetastet
   bleiben; es zieht ohnehin nicht um.

**Entschieden: den Frankfurter Dienst von Hand anlegen.** Jedes Feld ist
bekannt (siehe Tabelle oben). L-35 („nichts ist blueprint-verwaltet") bleibt
offen und wird ein eigener Schritt — einen Regionsumzug mit einer
Infrastruktur-als-Code-Umstellung zu vermischen verdoppelt die Wege, auf denen
er schiefgehen kann.

**Der Name des neuen Dienstes ist damit frei wählbar** (`kompagnon-backend-fra`),
und das blockierte Umbenennen entfällt vollständig.

### Die Variablen: eine Gruppe statt Abtippen

Auf der Umgebungsseite gibt es „Create environment group". Der Dialog kommt
**vorbefüllt** — die Geheimnisse verlassen Render dabei nie, niemand muss sie
sehen oder in eine Zwischenablage legen.

**Angelegt am 19.08.: `kompagnon-produktiv`, 15 Variablen**, keinem Dienst
zugeordnet (Spalte *Environment*: `—`), der laufende Betrieb also unberührt.
Nachgeprüft: produktiv weiterhin `startup_complete: true`,
`scheduler_running: true`, 2,4–2,6 s.

**`DATABASE_URL` wurde bewusst aus der Gruppe entfernt.** Sie ist die eine
Variable, die sich zwischen den beiden Diensten unterscheidet: Oregon braucht
die externe Adresse, Frankfurt bekommt die **interne** — und genau das ist der
Punkt, an dem die Datenbank aus dem Internet verschwinden kann (L-44).

**Nebenbefund, der mehrere offene Punkte auf einmal bestätigt:** Produktiv
sind **15 Variablen** gesetzt, der Blueprint deklariert **44**. Es fehlen
also 29 — darunter `WEBHOOK_SECRET` (deshalb sind die fünf Lead-Webhooks zu),
`STRIPE_SECRET_KEY` (deshalb ist Stripe nicht scharf), `CMS_ENCRYPTION_KEY`
(deshalb wären gespeicherte Zugangsdaten nach einer Wiederherstellung
unlesbar) und `NETLIFY_VORSCHAU_SITE_ID` (L-40). Alle vier waren vermutet und
sind jetzt belegt.

---

## Stand am 19.08. abends — der Dienst steht, die Domain nicht

**Angelegt: `kompagnon-backend-fra`, `srv-da30dg3bc2fs73fomi0g`.**

| Einstellung | Wert | woher |
|---|---|---|
| Region | **Frankfurt (EU Central)** | der Grund des Umzugs |
| Plan | Standard, 1 CPU / 2 GB | wie Oregon |
| Branch / Root | `main` / `kompagnon/backend` | wie Oregon |
| Build | `pip install -r requirements.txt` | **nicht** wie Oregon — siehe L-57 |
| Start | `uvicorn main:app --host 0.0.0.0 --port $PORT` | wie Oregon |
| Datentraeger | 1 GB auf `/var/data` | wie Oregon |
| Health-Check | `/health` | **besser** als Oregon (dort leer) |
| Auto-Deploy | Off | wie Oregon; die CI loest aus |
| Variablen | Gruppe `kompagnon-produktiv` (15) | neu, geteilt |
| `DATABASE_URL` | **intern**, je Dienst gesetzt | der Punkt, an dem L-44 moeglich wird |
| Adresse | `https://kompagnon-backend-fra.onrender.com` | ohne Domain, ohne Verkehr |

**Am 19.08. um 22:02 gemessen — der Dienst laeuft und ist gesund:**

```
status: ok            database: connected      ← ueber die INTERNE Adresse
scheduler_running: true                        startup_complete: true
startup_missing: []   environment: production
```

| | Frankfurt (neu) | Oregon (produktiv) |
|---|---|---|
| `/health`, fuenf Messungen | 0,30 · 0,22 · **0,18** · 0,20 · **0,17 s** | 3,14 · 3,47 · **2,22** · 3,10 · 2,52 s |

**Faktor 15.** Dazu zwei Dinge, die keine Messung sind, sondern Beweise:

- **`database: connected`** heisst, die interne Adresse traegt. Genau das
  konnte Oregon nie — und deshalb steht die Datenbank bis heute im offenen
  Internet (L-44).
- Der Start brauchte **60 Sekunden**. Oregon brauchte 264 und verlor dabei
  sieben von acht Startphasen (L-41). Hier ist `startup_missing` leer.

**Gleichheitsprobe, ohne Zugangsdaten moeglich und deshalb sofort gemacht:**
`GET /openapi.json` liefert auf beiden Diensten **401 Routen, null Abweichung**
— es ist dieselbe Anwendung. Fuenf Stichproben verhalten sich identisch
(`/health`, `/info`, `/api/widget/config` je 200; `/api/leads/` je 401).

**Reihenfolge-Falle, vor dem Suspendieren zu beachten:** Solange L-57 offen
ist, laesst sich der Oregon-Dienst **nicht neu bauen**. Suspendieren und
spaeter fortsetzen loest bei Render einen Deploy aus — der Rueckweg waere
damit kaputt, genau dann, wenn man ihn braucht. **Also: L-57 zuerst** (die
zwei Playwright-Zeilen aus Oregons Build-Befehl entfernen, Testbau ausloesen),
**dann** suspendieren.

**Schritt 0 der naechsten Sitzung, vor allem anderen** — am 21.08.
beantwortet, siehe den Abschnitt weiter unten: Es ist `main`. Der urspruengliche
Auftrag lautete: Nachsehen, aus
welchem **Branch** `kompagnon-backend-fra` deployt. Der Dienst wurde von Hand
angelegt, nicht aus dem Blueprint — die Vorgabe steht also nirgends
geschrieben. Haengt er an `staging`, wuerde das Umhaengen der Domain den
gesamten heutigen, produktiv ungetesteten Stand live schalten. Erwartet ist
`main`, geprueft ist es nicht. (Ueber den Render-MCP nicht nachzusehen — er
antwortet `unauthorized`; also im Dashboard.)

**Noch offen, in dieser Reihenfolge:**

1. Erfolgreicher Build und `startup_complete: true` am neuen Dienst
2. Fachliche Probe: anmelden, Betriebsliste, ein Audit ansehen
3. Webhooks bei Trackdesk, Netlify (2×), Brevo, Stripe (2×) umstellen
4. `RENDER_SERVICE_BACKEND_PROD` in den Repo-Variablen auf
   `srv-da30dg3bc2fs73fomi0g` aendern, sonst deployt die CI weiter nach Oregon
   und meldet trotzdem gruen — **das kommt jetzt vor dem Umhaengen**, siehe
   die Reihenfolge-Falle vom 21.08.
5. Frankfurt einmal von Hand neu bauen lassen und danach
   **`scripts/umzug-bereitschaft.sh`** laufen lassen — es beendet sich nur mit
   0, wenn der Dienst den aktuellen Stand traegt. Am 21.08. gegen Frankfurt
   gemessen: drei Fehlschlaege (`/api/dashboard/kpis` und `/api/webhooks/log`
   antworten **200** statt 401, und fuenf Routen fehlen, waehrend zwei
   entfallene noch da sind) — bei gleichzeitig makellosem `/health` in 0,20 s
6. **Domain umhaengen** — der erste unumkehrbare Schritt
7. Alten Dienst suspendieren (nicht loeschen) — **erst nach L-57**
8. **Dann L-44**: Inbound-Regel der Datenbank zu

**Kosten in der Zwischenzeit:** Zwei Standard-Dienste laufen parallel. Renders
Prognose fuer August stieg dadurch auf 294,99 $ (Stand 19.08. abends,
Monat bis dahin 179,85 $).

---

## Schritt 0 beantwortet — am Dienst gemessen, nicht im Dashboard gelesen (21.08.)

Der Render-MCP antwortet den **vierten Tag in Folge `unauthorized`**. Die Frage
liess sich trotzdem beantworten — nicht an der Einstellung, sondern an dem,
was der Dienst tatsaechlich ausliefert.

**Der Messpunkt:** Am 19.08. wurden auf `staging` 55 offene Routen geschlossen.
Diese Aenderung haengt an `dependencies=` der Router — sie veraendert die
`openapi.json` **nicht**, aber sie veraendert die Antwort zur Laufzeit. Damit
unterscheidet sie `staging`-Code von `main`-Code, ohne dass man sich anmelden
muss.

| ohne Anmeldung | Staging (Referenz) | Frankfurt | Oregon (produktiv) |
|---|---|---|---|
| `/api/dashboard/kpis` | **401** | **200** | **200** |
| `/api/webhooks/log` | **401** | **200** | **200** |
| `/health` | 200 (0,2 s) | 200 (**0,17 s**) | 200 (**2,2 s**) |

Dazu: `GET /openapi.json` ist auf Frankfurt und Oregon **Byte fuer Byte
identisch** (358.699 Byte, 401 Pfade, gleiche Pruefsumme ueber das sortierte
JSON).

**Schluss:** Frankfurt laeuft auf `main`-Code. Der Dienst wurde am 19.08. gegen
22 Uhr gebaut, als die Sicherheitsfixes auf `staging` laengst lagen — haette er
an `staging` gehangen, traege der Bau sie. Er traegt sie nicht. Auto-Deploy ist
Off, ein zweiter Bau kann es also auch nicht gewesen sein.

**Was diese Messung nicht ist:** ein Blick in die Einstellung. Sie belegt den
**ausgelieferten Bau**, nicht die eingetragene Vorgabe. Fuer den naechsten
Schritt reicht das — beim naechsten Dashboard-Besuch trotzdem nachsehen.

### Die Reihenfolge-Falle, die dadurch sichtbar wurde

Frankfurt hat **Auto-Deploy Off**, und die CI deployt nach
`RENDER_SERVICE_BACKEND_PROD` — das steht nachweislich immer noch auf Oregon
(`srv-d74ptinfte5s73bjbv90`, abgelesen im Deploy-Job von Lauf `32122610100`).

Daraus folgt: **Ein Merge nach `main` erreicht Frankfurt nicht.** Nach dem
Freitags-PR laeuft Oregon auf dem neuen Stand und Frankfurt weiter auf dem
alten. Wer dann die Domain umhaengt, schaltet die **55 offenen Routen wieder
scharf** — nach aussen sieht alles gesund aus, `/health` antwortet in 0,17 s.

**Also gilt zwischen Schritt 4 und 5 der Liste eine neue Zwischenstufe:**
erst `RENDER_SERVICE_BACKEND_PROD` umstellen **und** Frankfurt einmal von Hand
neu bauen lassen, dann messen — und **erst dann** die Domain umhaengen.

Dafuer gibt es seit dem 21.08. **`scripts/umzug-bereitschaft.sh`**. Es prueft
nicht, ob Routen *existieren*, sondern was sie **antworten, wenn niemand
angemeldet ist** — denn genau dort liegt der Unterschied zwischen den beiden
Staenden. Die Vollstaendigkeit misst es **gegen einen laufenden Dienst**
(Vorgabe: Staging), nicht gegen eine Zahl im Skript; eine hart notierte 401
waere schon heute falsch, Staging traegt 404.

### L-57 praeziser gefasst — die Behauptung war zu breit

Notiert war: „Der Oregon-Dienst laesst sich nicht mehr von Grund auf bauen."
Am Objekt geprueft stimmt das so nicht. Der Deploy-Job der CI loest mit
`{"clearCache":"do_not_clear"}` aus, und Lauf `32122610100` (PR #42, 18.08.)
zeigt fuer Oregon `build_in_progress` ueber 45 s, dann `update_in_progress`,
dann `live`. Ein echter Bau auf einer echten Code-Aenderung, **erfolgreich**,
vor drei Tagen.

Der Kern der Luecke bleibt, nur enger: Der Bau gelingt, **weil** der Cache das
`playwright`-Programm aus einer frueheren Abhaengigkeitsliste noch enthaelt.
Ohne Cache faellt der Build-Befehl auf einen Befehl zurueck, den niemand mehr
installiert.

- **Der Freitags-Merge ist damit unbedenklich** — er nimmt den Cache-Weg.
- **Suspendieren, Fortsetzen, Rollback und jeder Bau mit `clear` sind es
  nicht** — genau dort greift der Cache nicht.

L-57 ist damit keine Blockade fuer den PR, aber weiterhin eine **vor** dem
Suspendieren (Schritt 6).

---

## Stand am 23.08. — Frankfurt ist bereit, und drei Annahmen sind belegt

Der Render-Zugang antwortet wieder (Ursache stand in L-57: ein projektweiter
Eintrag mit abgelaufenem Schlüssel stach den gültigen). Damit ließ sich zum
ersten Mal messen statt erschließen.

**Schritt 0 endgültig beantwortet.** Die API sagt, was am 21.08. nur aus dem
ausgelieferten Bau geschlossen war: `kompagnon-backend-fra` hängt an
`branch: main`. Die Messung von damals stimmte.

**Der Dienst trägt jetzt den aktuellen `main`** (`a95a1d8`, PR #44 — er hing
102 Commits zurück). Gebaut **mit leerem Cache**, und das ist zugleich die
Gegenprobe zu L-57: `build_in_progress → live` in **73 Sekunden**. Ein
Cache-Verlust ist hier kein Ausfallrisiko.

| Prüfung | Frankfurt |
|---|---|
| `/health` | ok, `database: connected`, `startup_complete`, `startup_missing: []` |
| `uploads` | **`dauerhaft: true`** — der Datenträger ist wirklich eingehängt |
| `/health`-Dauer | **0,11 s** gegen Oregons **2,9 s** |
| `/api/dashboard/kpis`, `/api/webhooks/log`, `/api/leads/` | je **401** — die Sicherheitsfixes sind an Bord |
| Routen | **386, deckungsgleich** mit der Produktivadresse |

`scripts/umzug-bereitschaft.sh` meldet: **Alle Prüfungen halten.**

### Die Referenz des Bereitschaftsskripts war falsch gewählt

Der erste Lauf an diesem Tag meldete **fünf fehlende Routen** und verweigerte
die Freigabe. Die fünf fehlten nicht: `/api/audit/analysen/anzahl`,
`/api/geo/{id}/ki-sichtbarkeit/verlauf`, `/api/kas/domain`,
`/api/leads/quellen/wirkung` und `/api/leads/{id}/verlauf` liegen auf
`staging` in einem **noch nicht gemergten** PR, während Frankfurt aus `main`
baut.

Das Skript verglich den neuen Dienst also mit einer Zukunft, die produktiv gar
nicht gilt. Die Frage beim Umzug lautet nicht „trägt er den neuesten Stand?",
sondern **„trägt er dasselbe wie der, den er ersetzt?"** — die Vorgabe-Referenz
ist deshalb jetzt `https://api.kompagnon.group`, und das Skript bricht ab, wenn
Dienst und Referenz dieselbe Adresse sind (nach dem Umhängen verglichen sie
sich sonst mit sich selbst und meldeten immer „deckungsgleich").

### Schritt 3 ist risikoärmer als gedacht — an der Datenbank nachgezählt

Der Plan verlangt, elf Webhook-Adressen bei Dritten umzustellen, bevor der alte
Dienst abgeschaltet wird. Am 23.08. nachgesehen, was dort **ankommt**:

| Tabelle | Zeilen |
|---|---|
| `webhook_log` | **0** |
| `mail_events` | **0** |
| `email_logs` | **0** |

Bei keinem der elf Endpunkte kommt derzeit etwas an. Der Verkehr auf die alte
`onrender.com`-Adresse ist von **139** Anfragen am 16.08. auf **1** am 21.08.
gefallen; was seither zählt, sind die eigenen Prüfungen. Das Umstellen bleibt
zu tun — aber es blockiert den Umzug nicht, und es kann nichts brechen, was
nicht schon stillsteht.

**Die Ausnahme, die bleibt:** Wer `STRIPE_SECRET_KEY` setzt, *bevor* die beiden
Stripe-Webhooks auf die Domain zeigen, verkauft an einen Dienst, den es nach
dem Umzug nicht mehr gibt — und ein fehlgeschlagener Webhook bricht den Kauf
nicht ab, das Geld ist weg und niemand merkt es.

### Was dabei auffiel und den Umzug betrifft: zwei Scheduler (L-91)

Seit dem 19.08. laufen beide Dienste gegen dieselbe Datenbank, und **beide
fuhren einen Scheduler auf derselben Jobtabelle**. APScheduler kennt keine
Sperre über Prozessgrenzen. Geschlossen über `SCHEDULER_ENABLED` — der liegt
aber auf `staging`, und Frankfurt baut aus `main`. **Bis zum nächsten Merge
bleibt der Zustand bestehen.**

### Stand nach dem Merge von PR #45 (23.08., 10:45)

Oregon ist auf `77c8fbb` live, Frankfurt ebenfalls. Zwei Dinge sind damit
belegt, die vorher nur gegen einen Speicher-Jobstore geprüft waren:

- **Der verwaiste Job ist weg.** `apscheduler_jobs` trug 15 Zeilen mit *zwei*
  DNS-Prüfungen (10 und 15 Minuten). Nach dem Start mit dem Aufräumcode:
  **14 Zeilen, eine** DNS-Prüfung. Der Abgleich wirkt am echten Jobstore.
- **Der Schalter wirkt.** Frankfurt meldet `scheduler_enabled: false`,
  `scheduler_running: false` — und dabei `startup_complete: true` mit leerem
  `startup_missing`. Ein abgeschalteter Scheduler wird also **nicht** als
  ausgefallene Startphase gewertet. Oregon fährt die Jobs weiter.

| | Frankfurt | Oregon |
|---|---|---|
| `/health` | ok, 0,18 s | ok, ~2,9 s |
| Routen | **391, deckungsgleich** | 391 |
| Scheduler | aus (gewollt) | an |

`scripts/umzug-bereitschaft.sh`: **Alle Prüfungen halten.**

### Der Schritt, der beim Umhängen leicht vergessen wird

Das Bereitschaftsskript wertete `scheduler_running: False` zunächst als
Fehler und verweigerte die Freigabe — für einen Zustand, den wir absichtlich
hergestellt haben. Das eigene Werkzeug hätte den Umzug blockiert.

Dahinter steckt aber ein echter Ablaufpunkt, der im Plan fehlte:

> **Beim Umhängen der Domain muss `SCHEDULER_ENABLED` bei Frankfurt entfernt
> und bei Oregon auf `false` gesetzt werden.**

Sonst fährt produktiv **kein** Scheduler. Das fällt nicht auf: `/health`
antwortet makellos, alle Routen stimmen, und die Lücke zeigt sich erst, wenn
wochenlang keine Nachfassmail mehr ankommt. Das Skript weist jetzt darauf hin,
statt zu blockieren.

## Vollzogen am 23.08.2026, 10:56 UTC

Die Domain `api.kompagnon.group` zeigt auf `kompagnon-backend-fra`.

| Probe | Ergebnis |
|---|---|
| `/health` über die Domain | **0,155 s** (vorher 2,5–2,9 s) |
| Routen | **391, deckungsgleich** mit der Referenz |
| `/api/dashboard/kpis`, `/api/webhooks/log`, `/api/leads/` | je **401** |
| `/api/widget/config` | 200 |
| CORS-Preflight vom Frontend | 200 |
| Frontend-Bundle | trägt `api.kompagnon.group`, **null** Treffer für `claude-code-znq2` |
| `RENDER_SERVICE_BACKEND_PROD` | `srv-da30dg3bc2fs73fomi0g` |
| Scheduler | genau **einer**, auf Frankfurt |
| Jobs im Store | 14, eine DNS-Prüfung |

### Der Schritt, der beinahe vergessen wurde

Nach dem Umhängen stand der Scheduler **falsch herum**: Frankfurt trug die
Domain mit `SCHEDULER_ENABLED=false`, während Oregon ohne Verkehr die Jobs
fuhr. Akut folgenlos — beide arbeiten auf derselben Datenbank, die Jobs liefen
also. Mit dem Suspendieren von Oregon wären sie **alle** stehen geblieben, und
`/health` hätte weiter „ok" gemeldet.

Umgedreht in dieser Reihenfolge: **erst Oregon aus, dann Frankfurt an.** Ein
kurzes Fenster *ohne* Scheduler ist harmloser als eines mit *zweien* — das
Doppelrisiko aus L-91 ist genau das, was hier nicht zurückkommen darf.

### Was der Umzug gekostet hat: 40 Sekunden Ausfall (L-94)

Während des Umschaltens antwortete die Produktivdomain sechsmal hintereinander
im Achtsekundentakt: `200 502 502 502 502 502`, dann wieder 200.

**Das ist keine Eigenheit dieses Umzugs, sondern die jedes Deploys.**
`instance_count` steht über alle drei Deploys des Tages konstant auf **1** —
bei einem rollierenden Deploy müsste kurz eine zweite Instanz danebenstehen.
Der Grund ist der Datenträger: Render begrenzt Dienste mit `disk` auf eine
Instanz. Alte beenden, neue starten.

Seit dem 18.08. ist damit **jeder** Deploy ein Ausfall — auch der gewöhnliche
nach einem Merge nach `main`. Aufgefallen ist es nie, weil produktiv rund sechs
Anfragen pro Stunde ankommen. Siehe L-94.

### Noch offen — nur noch drei Handgriffe

1. **Oregon suspendieren** (nicht löschen — der Rückweg). L-57 ist erledigt,
   ein Neubau von Grund auf gelingt wieder
2. **L-44**: Inbound-Regel der Produktiv-DB von `0.0.0.0/0` auf leer. Jetzt
   möglich: Frankfurt erreicht die Datenbank über die **interne** Adresse
3. **Webhooks** bei Trackdesk, Netlify (2×), Brevo und Stripe (2×) auf
   `https://api.kompagnon.group/...` — eilt nicht, dort kommt nichts an
   (`webhook_log`, `mail_events`, `email_logs` alle leer). Ausnahme Stripe
2. **`RENDER_SERVICE_BACKEND_PROD`** auf `srv-da30dg3bc2fs73fomi0g` — sonst
   deployt die CI weiter nach Oregon und meldet trotzdem grün. **Eng vor
   Schritt 3 legen:** Dazwischen erreicht ein Merge nach `main` den
   produktiven Dienst nicht mehr
3. **Domain umhängen** — der erste unumkehrbare Schritt, im Dashboard. In
   derselben Minute: `SCHEDULER_ENABLED` bei Frankfurt **entfernen** und bei
   Oregon auf `false` setzen. Danach Oregon suspendieren (nicht löschen),
   dann L-44

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

### Was seit dem 18.08. dazugehört

Vier Dinge sind an diesem Tag entstanden, die den Umzug betreffen. Sie stehen
hier, damit sie morgen nicht als Überraschung auftauchen.

- [ ] **Der Datenträger zieht nicht mit.** Am 18.08. wurde am *Oregon*-Dienst
      ein Datenträger angehängt (1 GB, `/var/data`, `UPLOAD_ROOT=/var/data/uploads`).
      Datenträger gehören zum Dienst, nicht zum Repo: Der Frankfurter Dienst
      braucht einen **eigenen**, und die Dateien darauf müssen kopiert werden,
      **bevor** der alte suspendiert wird. Heute liegen dort null Dateien —
      wenn das morgen noch stimmt, ist es ein Nebensatz. Wenn nicht, ist es
      der heikelste Schritt des Umzugs.
      *Prüfung vorher:* `find /var/data -type f | wc -l` in der Render-Shell.
- [ ] **`/health` sagt es jetzt selbst.** Der neue Dienst ist erst in Ordnung,
      wenn dort steht: `"uploads": {"dauerhaft": true}`. Das ist die Probe
      dafür, dass der Datenträger wirklich eingehängt ist — nicht das
      Dashboard.
- [ ] **Der Deploy-Job wartet auf `startup_complete`.** Seit dem 18.08. prüft
      die CI nach dem Deploy die Betriebsbereitschaft des Dienstes (600 s
      Grenze). Beim Umzug ändern sich die **Service-IDs** in den
      Repository-Variablen (`RENDER_SERVICE_BACKEND_PROD`) — wer sie vergisst,
      deployt weiter nach Oregon, und die CI meldet trotzdem grün.
- [ ] **Zwei neue Tabellen entstehen beim Start** (`fehlerprotokoll`, und die
      Spalten aus dem Modellabgleich). `Base.metadata.create_all` legt Tabellen
      an, aber **keine Spalten** — beim ersten Start in Frankfurt läuft
      derselbe Migrationsblock wie heute, gegen dieselbe Datenbank. Es ist
      also nichts zu tun; es ist nur nichts zu vergessen.

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

## Die Datenbank zeigte selbst auf die alte Adresse — gezählt am 16.08.

Der Editor schreibt **absolute** Bild-Adressen in den gespeicherten
Seiteninhalt. Die brechen nicht beim Umzug, sondern erst beim **Löschen** des
alten Dienstes — und dann still, denn im Code ist dann alles richtig.

Gezählt über die Render-Shell, also ohne offene Inbound-Regel:

| Tabelle | Bestand | betroffen |
|---|---|---|
| `sitemap_pages` (Kunden-Editorseiten) | 170 | **0** |
| `projects.wireframe_data` | 19 | **0** |
| `kas_gjs_data` (eigene KAS-Seiten) | 2 | **2** |
| `project_files` (Uploads) | 1 | 1 |

**Kundenseiten waren nicht betroffen.** Die zwei eigenen Seiten sind am selben
Tag umgeschrieben worden, mit Vorher-Nachher-Prüfung: 2 Treffer je Zeile, die
Länge sank um exakt 20 Zeichen (2 × die Differenz der beiden Adressen), `json`
danach weiterhin gültig. Kein anderer Inhalt hat sich bewegt.

**Was dabei nebenbei auffiel und offen bleibt:** `project_files` speichert
lokale Dateipfade, und keiner der Blueprints enthält einen `disk:`-Block. Die
Uploads liegen also auf einem flüchtigen Dateisystem. Die eine vorhandene Zeile
zeigt bereits auf eine Datei, die es **nicht mehr gibt** — verloren bei einem
früheren Deploy, lange vor diesem Umzug. Bei einer Datei ist das keine
Umzugssperre; als Bauweise gehört es geklärt, bevor Kunden Bilder hochladen.

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
