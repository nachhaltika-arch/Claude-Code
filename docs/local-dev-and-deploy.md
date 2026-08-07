# Lokal entwickeln, über GitHub Actions deployen

> Stand: 2026-08-07
> Ersetzt den bisherigen Ablauf aus `local-dev-with-render-db.md` für den Normalfall.
> Jenes Dokument bleibt gültig für Sonderfälle (Daten der Staging-DB ansehen, DB-GUI).

Zwei Teile: lokal arbeiten (unten Teil 1) und das Ergebnis kontrolliert ausrollen (Teil 2).

---

## Teil 1 — Lokale Entwicklung

### Ein Befehl

```bash
bash scripts/dev.sh
```

Startet Backend auf `http://localhost:8000` (API-Doku unter `/docs`) und Frontend auf
`http://localhost:3000`. Beenden mit `Strg+C`.

| Option | Wirkung |
|---|---|
| `--seed` | Checklisten und Component-Library zusätzlich einspielen |
| `--reset-db` | lokale Datenbank verwerfen und neu anlegen |
| `--backend` | nur das Backend starten |
| `--frontend` | nur das Frontend starten |
| `--remote-db` | Sperre gegen entfernte Datenbanken aufheben (siehe unten) |

### Was beim ersten Lauf passiert

1. Voraussetzungen prüfen — Python 3.11, Node, laufende Postgres
2. Datenbank `kompagnon_local` anlegen
3. `kompagnon/backend/.env` aus `.env.example` erzeugen, mit lokaler
   Datenbank-Adresse und frisch erzeugtem `SECRET_KEY`
4. Virtuelle Umgebung anlegen und Abhängigkeiten installieren
5. `kompagnon/frontend/.env.local` auf `http://localhost:8000` zeigen lassen
6. Beide Dienste starten

Das Datenbankschema entsteht beim Backend-Start automatisch (Migrationen plus
`init_db`), die Component-Library wird dabei ebenfalls befüllt. Beim ersten Lauf
wurden so 39 Tabellen und 96 Library-Einträge erzeugt.

### Die Sperre gegen entfernte Datenbanken

Der bisherige Ablauf sah vor, lokal gegen die Render-Datenbank zu arbeiten. Das ist
riskant: Beim Start laufen Migrationen, die das Schema der entfernten Datenbank
verändern. Deshalb prüft das Skript die `DATABASE_URL` und bricht ab, wenn sie nicht
auf `localhost` zeigt.

Wer es bewusst braucht — etwa um einen Fehler mit echten Daten nachzustellen —
startet mit `--remote-db` und bekommt eine deutliche Warnung.

> Die frühere `.env`, die auf Render zeigte, liegt als
> `kompagnon/backend/.env.render-backup`. Sie wird nicht mehr automatisch genutzt.

### Was du dir bewusst machen solltest

- **Node-Version:** lokal 26, in CI und auf Render 18. Das Skript warnt beim Start.
  Bei Build-Unterschieden gilt immer das Ergebnis der CI, nicht der lokale Build.
- **E-Mails:** `USE_MOCK_EMAIL=true` steht in der Vorlage. So geht lokal nichts an
  echte Empfänger raus. Vor dem Umstellen zweimal nachdenken.
- **Stripe:** Die Schlüssel bleiben lokal leer. Sonst drohen echte Buchungen.
- **KI:** Ohne `ANTHROPIC_API_KEY` laufen die Agenten in ihrem Mock-Modus. Für
  Oberflächenarbeit reicht das.
- **Anmeldung:** Setze `ADMIN_PASSWORD` in der `.env`, damit beim nächsten Start ein
  lokaler Admin-Zugang angelegt wird.

---

## Teil 2 — Deploy über GitHub Actions

### Wie es vorher war

Render hatte Auto-Deploy aktiviert und startete den Deploy bei jedem Push. Die
GitHub Actions liefen **parallel** dazu — sie prüften, hielten aber nichts auf. Ein
fehlerhafter Commit ging also live, während die Prüfung noch lief.

### Wie es jetzt läuft

```
Push auf staging  →  CI (4 Prüfjobs)  →  grün?  →  Deploy Staging  →  warten bis live
Merge in main     →  CI (4 Prüfjobs)  →  grün?  →  Deploy Produktiv →  warten bis live
```

Der Job `deploy` in `.github/workflows/ci.yml` hängt an allen vier Prüfjobs. Er löst
den Deploy über die Render-API aus und fragt danach den Status ab, bis der Deploy
`live` ist oder fehlschlägt. Ein roter Deploy macht den Workflow rot — du siehst es
also sofort in GitHub, nicht erst durch einen Kundenanruf.

Zeitrahmen: alle 15 Sekunden eine Statusabfrage, Abbruch nach 30 Minuten.

### Einmalige Einrichtung — in dieser Reihenfolge

**Schritt 1: Render-API-Schlüssel erzeugen**
Render-Dashboard → Account Settings → API Keys → Create API Key.

**Schritt 2: Service-IDs heraussuchen**
Jeden der vier Services im Dashboard öffnen; die ID steht in der Adresszeile und
beginnt mit `srv-`.

**Schritt 3: In GitHub hinterlegen**
Repository → Settings → Secrets and variables → Actions:

| Art | Name | Inhalt | Stand |
|---|---|---|---|
| Secret | `RENDER_API_KEY` | der Schlüssel aus Schritt 1 | **offen — von Hand einzutragen** |
| Variable | `RENDER_SERVICE_BACKEND_STAGING` | `srv-d7r1eif7f7vs73ckvlag` | gesetzt |
| Variable | `RENDER_SERVICE_FRONTEND_STAGING` | `srv-d7r1eif7f7vs73ckvl90` | gesetzt |
| Variable | `RENDER_SERVICE_BACKEND_PROD` | `srv-d74ptinfte5s73bjbv90` | gesetzt |
| Variable | `RENDER_SERVICE_FRONTEND_PROD` | `srv-d74qd7oule4c73f7v4t0` | gesetzt |

Hinweis zu den Namen: Der Produktiv-Backend-Service heißt im Dashboard
`kompagnon-backend`, seine URL ist historisch `claude-code-znq2.onrender.com`.

**Schritt 4: Erst danach pushen.**
Fehlen Schlüssel oder IDs, bricht der Deploy-Job mit einer klaren Meldung ab — die CI
wird bei jedem Push rot.

**Schritt 5: Auto-Deploy in Render abschalten — zuletzt.**

Hier unterscheiden sich die beiden Umgebungen (geprüft am 2026-08-07):

- **Staging** — beide Services tragen im Dashboard das Kennzeichen „Blueprint
  managed". Für sie greift `autoDeploy: false` aus `render-staging.yaml`, sobald
  das Blueprint synchronisiert ist. Nachsehen schadet trotzdem nicht.
- **Produktiv** — `kompagnon-backend` und `kompagnon-frontend` sind **nicht**
  blueprint-verwaltet. Dort muss der Schalter von Hand umgelegt werden:
  Settings → Build & Deploy → Auto-Deploy auf **Off**. Der Eintrag in `render.yaml`
  dokumentiert dort nur den Sollzustand und bewirkt nichts.

Solange Auto-Deploy aktiv ist, deployt Render parallel am Torwächter vorbei.

Die Reihenfolge ist Absicht: Erst wenn ein Actions-Deploy nachweislich funktioniert,
schaltest du den bisherigen Weg ab. So gibt es keinen Moment ohne funktionierenden
Deploy.

### Deploy von Hand auslösen

Im Actions-Tab lässt sich der Workflow über `workflow_dispatch` starten. Der
Deploy-Job läuft dabei nicht mit — er ist bewusst an `push` gebunden, damit ein
Deploy immer zu einem Commit auf `staging` oder `main` gehört.

Braucht es einen Deploy ohne neuen Commit, ist der direkte Weg im Render-Dashboard
über "Manual Deploy" der ehrlichere.

### Zurückrollen

Render behält frühere Deploys. Dashboard → Service → Deploys → beim gewünschten
Stand "Rollback". Das ist bei einem Zwischenfall schneller als ein Revert-Commit
durch die CI — den Revert danach trotzdem nachziehen, sonst deployt der nächste Push
den Fehler erneut.

---

## Zusammenspiel mit dem Branch-Rhythmus

Am Ablauf aus `CLAUDE.md` ändert sich nichts:

1. Lokal entwickeln mit `scripts/dev.sh`
2. Commit und Push auf `staging` → CI prüft → Staging-Deploy
3. Auf dem Staging-Server testen
4. Freitags PR `staging → main`, CI grün abwarten
5. Merge von Hand → CI prüft → Produktiv-Deploy

Neu ist allein, dass zwischen Schritt 2 und 3 sowie zwischen 5 und "live" jeweils die
Prüfung steht.
