# Sicherung und Wiederherstellung

> Erstellt am 2026-08-19 (L-11, offen seit dem 07.08.). Gegenstand ist die
> Frage, die im Ernstfall zählt: **Wie lange dauert es, und was ist dann weg?**
>
> Was hier steht, ist entweder belegt oder ausdrücklich als offen markiert.
> Der Render-MCP ist seit zwei Tagen `unauthorized` (am 19.08. dreimal
> versucht, zuletzt nach einem Neuverbinden), deshalb konnte die
> Aufbewahrungsdauer nicht am Dienst nachgesehen werden — sie steht unten als
> die eine Frage, die du beantworten musst.

---

## 1. Was überhaupt zu sichern ist

Eine Datenbanksicherung allein rettet den Betrieb **nicht**. Es sind drei
Dinge, und nur eines davon liegt in der Datenbank:

| Was | Wo es liegt | In einer DB-Sicherung? |
|---|---|---|
| **Fachdaten** — Betriebe, Audits, Projekte, Kurse, Nachrichten | Postgres (`Kompangnon-dB`, Frankfurt) | ja |
| **Hochgeladene Dateien** — Kundendateien, Bilder, Auftragsbestätigungs-PDFs | Datenträger am Dienst, `/var/data` (1 GB, seit 18.08.) | **nein** |
| **Geheimnisse und Konfiguration** — 44 Umgebungsvariablen | Render-Dienst | **nein** |

**Der Datenträger ist der Punkt, der übersehen wird.** Er ist erst seit dem
18.08. überhaupt vorhanden; davor lagen Uploads auf einem flüchtigen
Dateisystem, und die eine vorhandene Datei war bereits verloren, als wir
nachsahen. Er gehört zum **Dienst**, nicht zum Repo und nicht zur Datenbank —
und er zieht beim Umzug nach Frankfurt nicht mit (siehe
`umzug-backend-frankfurt.md`).

Die Umgebungsvariablen sind der zweite. Sie stehen zwar seit dem 16.08. in
`kompagnon/render-produktiv.yaml` **beschrieben**, aber die Werte nicht — und
das ist richtig so. Ohne `CMS_ENCRYPTION_KEY` und `CREDENTIALS_KEY` sind
gespeicherte Zugangsdaten selbst nach einer vollständigen DB-Wiederherstellung
**unlesbar**. Eine Sicherung ohne die Schlüssel ist eine halbe Sicherung.

---

## 2. Die drei Wege zurück

### Weg A — Renders eigener Wiederherstellungspunkt *(schnellster Weg)*

Render führt für verwaltete Postgres-Instanzen Wiederherstellungspunkte. Im
Dashboard unter der Datenbank → *Recovery*. Ein Wiederherstellungspunkt
erzeugt eine **neue** Instanz; die alte bleibt stehen.

**Danach ist Handarbeit nötig:** Die neue Instanz hat eine neue interne
Adresse. `DATABASE_URL` wird produktiv **von Hand** gepflegt (der Blueprint
lässt sie bewusst offen, damit ein danebenliegender `databases:`-Block nicht
eine zweite, leere Datenbank anlegt). Also: Adresse eintragen, Deploy
auslösen, `/health` abwarten.

- [ ] **Offen: Wie weit reicht der Zeitraum zurück?** Im Dashboard bei
      *Recovery* abzulesen. Davon hängt die einzige Zahl ab, die im Ernstfall
      zählt

### Weg B — Eigener Auszug mit `pg_dump`

Läuft **innerhalb** von Render und braucht deshalb keine offene
Inbound-Regel — wichtig, sobald L-44 zugeht:

```bash
render psql kompagnon-backend      # oder: Shell am Dienst öffnen
pg_dump "$DATABASE_URL" --no-owner --no-privileges -Fc -f /tmp/kompagnon.dump
```

Zurückspielen in eine leere Instanz:

```bash
pg_restore --no-owner --no-privileges -d "$DATABASE_URL" /tmp/kompagnon.dump
```

`-Fc` statt einer Textdatei: Das Format lässt sich selektiv zurückspielen,
etwa nur eine Tabelle. Nach einem versehentlichen `DELETE` ist genau das der
Unterschied zwischen zehn Minuten und einem halben Tag.

**Größenordnung:** Die Datenbank ist `Basic-256mb` mit 1 GB Speicher, davon
18,7 % belegt (Stand 16.08.). Ein Auszug ist also klein genug, um ihn
herunterzuladen.

### Weg C — Der Datenträger

Für `/var/data` gibt es **keinen** Wiederherstellungspunkt. Was dort liegt,
ist weg, wenn der Dienst weg ist.

```bash
# Am Dienst, in der Render-Shell:
find /var/data -type f | wc -l        # zählen, bevor man etwas behauptet
tar czf /tmp/uploads.tgz -C /var/data .
```

Am 18.08. lagen dort **null Dateien**. Solange das so bleibt, ist dieser Weg
ein Nebensatz. Sobald Kunden Bilder hochladen, ist er der wichtigste.

---

## 3. Was du entscheiden musst

Zwei Zahlen, und ohne sie ist jede Sicherungsstrategie Geschmackssache:

- **Wie viel Datenverlust ist hinnehmbar?** (RPO) Eine Stunde? Ein Tag?
  Davon hängt ab, ob Renders Wiederherstellungspunkte reichen oder ob ein
  täglicher eigener Auszug dazugehört.
- **Wie lange darf es dauern?** (RTO) Weg A ist Minuten plus Handarbeit an
  `DATABASE_URL`. Weg B ist so lange, wie ein `pg_restore` braucht.

**Meine Empfehlung:** Weg A als Normalfall, dazu **ein monatlicher eigener
Auszug**, den du herunterlädst. Nicht wegen der Datenbank — die ist bei Render
gut aufgehoben —, sondern weil ein Auszug außerhalb von Render der einzige
Stand ist, der ein Konto-Problem überlebt. Bei rund 190 MB belegtem Speicher — ein Auszug
fällt kleiner aus, weil Indizes nicht mitkommen — ist das eine Fingerübung.

Die Schlüssel gehören in denselben Ablauf: `CMS_ENCRYPTION_KEY`,
`CREDENTIALS_KEY`, `SECRET_KEY`. Ohne sie ist der Auszug teilweise unlesbar.

---

## 4. Die Probe

Eine Sicherung, die nie zurückgespielt wurde, ist eine Vermutung. Der
Nachweis, den ich vorschlage — einmal, dann jährlich:

1. Auszug ziehen (Weg B)
2. In die **Staging**-Datenbank zurückspielen, nicht in die Produktion
3. Staging-Backend neu starten und `/health` prüfen: `startup_complete: true`,
   `startup_missing: []`
4. Im Werkzeug anmelden, eine Betriebsliste öffnen, ein Audit ansehen
5. Aufschreiben, **wie lange es gedauert hat** — das ist die Antwort auf
   „wie lange dauert es", und sie steht sonst nirgends

Schritt 2 ist der einzige mit Risiko: Er überschreibt Staging. Das ist der
Preis dafür, es einmal wirklich zu wissen.

---

## 5. Was heute belegt ist — und was nicht

| Aussage | Stand |
|---|---|
| Datenbank liegt in Frankfurt, `Basic-256mb`, 1 GB, 18,7 % belegt | belegt, 16.08. |
| Datenträger 1 GB auf `/var/data`, am Dienst nachgewiesen | belegt, 18.08. |
| Am 18.08. null Dateien auf dem Datenträger | belegt |
| `pg_dump` über die Render-Shell funktioniert ohne offene Inbound-Regel | **belegt, 28.08.** — 6 s, 28 MB |
| Aufbewahrung der Wiederherstellungspunkte: **7 Tage** | belegt, 27.08. |
| Logische Sicherungen laufen **nicht** automatisch | belegt, 27.08. |
| Inbound-Regel der Produktiv-DB ist zu (`ipAllowList: null`) | belegt, 27.08. |
| Keine Hochverfügbarkeit, keine Lesekopie | belegt, 27.08. |
| `CMS_ENCRYPTION_KEY` produktiv gesetzt | **offen** — bei David |
| Eine Wiederherstellung wurde je durchgeführt | **ja, 28.08.2026** — Weg B, 8 min 56 s, siehe § 7 |

## 6. Was am 27.08.2026 dazugekommen ist

**Die Aufbewahrungsdauer ist keine Vermutung mehr: sieben Tage.** Sie hängt
nicht am Datenbank-Tarif, sondern am **Workspace**-Tarif — Hobby drei Tage,
Pro und höher sieben. Am Dashboard nachgesehen: „Current Plan: **Pro**".

**Und die unbequemere Hälfte derselben Auskunft:** Logische Sicherungen legt
Render **nicht von selbst** an. Sie werden von Hand ausgelöst und dann sieben
Tage aufbewahrt. Ausgelöst hat sie bisher niemand.

> Damit ist das gesamte automatische Netz **sieben Tage breit**. Was älter ist
> als eine Woche, gibt es nicht mehr — auch nicht gegen Bezahlung, auch nicht
> mit Renders Hilfe. Ein Schaden, der am achten Tag auffällt, ist endgültig.

Das ist der eigentliche Inhalt dieser Datei, präziser als vorher: Wir haben
Wege zurück, keinen davon je gegangen — und das Zeitfenster, in dem sie
überhaupt existieren, ist schmaler als gedacht.

**Was daraus folgt und noch niemand entschieden hat:** ob ein regelmäßiger
eigener Auszug (Weg B) irgendwohin gehört, wo er länger als sieben Tage
liegt. Der Scheduler läuft und führt vierzehn Jobs; ein fünfzehnter wäre
technisch der kleinste Teil. Die Frage ist nicht, ob es geht, sondern wohin
der Auszug soll — und das ist eine Entscheidung über Ort, Kosten und
Zugriffsrechte.

---

## 7. Die Probe ist gelaufen — 28.08.2026

Sie war seit dem 19.08. der letzte offene Punkt aus L-11. Jetzt ist sie
durchgeführt, und der Satz „eine Sicherung, die nie zurückgespielt wurde, ist
eine Vermutung" gilt für diese Sicherung nicht mehr.

### Die Zahlen

| Schritt | Dauer | Beleg |
|---|---|---|
| `pg_dump` produktiv, `-Fc` | **6 s** | 28.010.097 Bytes, 73 Tabellen |
| Auszug herunterladen | 35 s | — |
| Auszug nach Staging hochladen | 51 s | Bytezahl unverändert |
| `DROP SCHEMA public CASCADE` | 1 s | — |
| `pg_restore` | **39 s** | **0 Fehlerzeilen** |
| Backend neu bauen bis `live` | 89 s | `dep-da8lic3tqb8s73aipe40` |
| **Gesamt bis `/health` grün** | **8 min 56 s** | 09:40:01 → 09:48:57 UTC |

**Die ehrliche Zahl ist kleiner.** Die 86 Sekunden Übertragung entstanden nur,
weil der Auszug über einen Arbeitsplatzrechner geleitet wurde — es gibt keine
direkte Verbindung zwischen zwei Render-Diensten. Wer im Ernstfall innerhalb
von Render zurückspielt, spart sie: **rund sieben Minuten**.

### Was tatsächlich belegt ist

Nicht „es lief durch", sondern der Inhalt: Vor dem Zurückspielen wurden die
Zeilenzahlen **aller 73 Tabellen** auf beiden Seiten erhoben, danach erneut.

- Staging vorher: 70 Tabellen, 1.014 Zeilen
- Produktiv beim Auszug: 73 Tabellen, 5.089 Zeilen
- Staging nachher: 73 Tabellen, 5.089 Zeilen — **keine einzige Abweichung**

Der Unterschied vorher/nachher ist der Grund, warum das etwas heißt. Ein
Vergleich, der auch bei misslungener Wiederherstellung gleich ausgesehen
hätte, wäre kein Beleg gewesen.

Danach: `/health` mit `startup_complete: true` und `startup_missing: []`, im
Werkzeug angemeldet, Betriebsliste und Audits sichtbar — dieselben Werte wie
produktiv.

### Der Fund, den die Probe hergegeben hat

**Eine Wiederherstellung ist nicht der letzte Zustand.** Nach dem Neustart war
die Datenbank nicht mehr zeilengleich mit der Produktion:

| Tabelle | nach `pg_restore` | nach dem Neustart |
|---|---|---|
| `leads` | 65 | 66 |
| `products` | 9 | 12 |
| `project_checklists` | 0 | 67 |
| `projects` | 0 | 7 |
| `users` | 8 | **10** |

Das ist kein Fehler, sondern `main.py::_create_default_admin()`: Demo-Konten,
ein Demo-Betrieb („Mustermann Sanitär GmbH") und die Checklisten werden beim
Start angelegt. **Zwei zusätzliche Benutzerkonten** — das ist der Teil, der
bei einer Wiederherstellung zählt.

**Produktiv kann das nicht passieren, und auch das ist gemessen** statt
angenommen: Die Funktion läuft nur bei `ENVIRONMENT` in
`{development, dev, local, staging}`, und das Produktiv-Protokoll sagt
wörtlich `⏭ Demo-User-Erstellung übersprungen (ENVIRONMENT=production)`.

Der Vorgabewert der Variablen ist allerdings `"development"`. Wäre
`ENVIRONMENT` produktiv **nicht** gesetzt, legte ein Neustart dort Demo-Konten
an. Sie ist gesetzt — geprüft am 28.08. Wer eine Wiederherstellung in eine
**neue** Instanz fährt, muss sie dort zuerst setzen, bevor das Backend das
erste Mal startet.

### Was die Probe nicht belegt

- **Weg A** (Renders Wiederherstellungspunkt) wurde weiterhin nicht angeklickt.
  Belegt ist Weg B, der eigene Auszug — die wertvollere Hälfte.
- **Weg C**, der Datenträger, war nicht Teil der Probe. Seit L-141 liegen dort
  Auftragsbestätigungen; für sie gibt es weiterhin keinen Wiederherstellungspunkt.
- `CMS_ENCRYPTION_KEY` ist **produktiv weiterhin nicht gesetzt** (Protokoll
  27.08., 10:07). Folgenlos, solange `customers` produktiv 0 Zeilen hat — aber
  die Zeile in § 5 bleibt offen.
