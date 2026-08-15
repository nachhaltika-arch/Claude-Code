# Analyse-Widget — Stand und offene Punkte

**Stand:** 2026-08-11, Abend
**Ziel:** Das Widget in eine fremde Landingpage einbetten — technisch, grafisch
und in der Bedienung fertig.
**Branch:** `staging` (4 Commits gepusht, Render-Staging-Deploy angestoßen)
**Morgen zuerst:** Widget fertigstellen, danach Bericht/E-Mail und der
Anforderungskatalog aus `docs/audit-anforderungen-2026-08-11.md`.

---

## 1. Was heute geändert wurde

| Commit | Inhalt |
|---|---|
| `3da9345` | SMTP-Einstellungen aus Tool und API entfernt; Versandstatus + Anfragenliste ergänzt |
| `f04891f` | Einbaucode mit Höhen-Nachführung (`utils/widgetEmbed.js`) inkl. 13 Tests |
| `f192f73` | Tool-Seite `Akquise → Analyse-Widget` neu aufgebaut |
| `5e39f7d` | Widget selbst: Einwilligungs-Bug, Kriterienzahl, Höhenmeldung |

### 1.1 Die drei echten Fehler, die dabei rausgefallen sind

**Einwilligung ging verloren.** Die Checkbox wurde erst gelesen, nachdem
`renderLoading()` den Karteninhalt bereits ersetzt hatte — das Element existierte
zu dem Zeitpunkt nicht mehr. Jede Anfrage wurde als *ohne Einwilligung* gespeichert,
auch wenn der Interessent zugestimmt hatte. Das erklärt vermutlich die
**8 Anfragen bei 0 bestätigten Einwilligungen** auf Staging.

**Test-Versand war dauerhaft gesperrt.** Der Knopf hing an `smtp.configured`,
der Versand läuft aber seit dem Wechsel über Brevo. Auf Staging ist Brevo bereit
(`BREVO_API_KEY` gesetzt), SMTP leer — also war der Knopf grau und die Seite
verlangte einen Server, den niemand braucht.

**Falsche Kriterienzahl.** Widget und E-Mail behaupteten „42 Kriterien", der
Katalog führt 38 bewertete (+ 4 Infrastruktur ohne Punkte). Die Zahl kommt jetzt
aus `audit_criteria.py`.

### 1.2 Einbettung

Der alte Einbaucode war ein nackter iframe mit `height:760px`. Auf der Kundenseite
heißt das: totes Weiß unter dem Formular, abgeschnittenes Ergebnis sobald die
Ergebniskarte höher wird. Das Widget meldete seine Höhe schon immer per
`postMessage` — es hörte nur niemand zu.

Der neue Code liefert den Listener mit. Er nimmt Nachrichten nur von der Herkunft
des Widgets und nur vom eigenen Rahmen an, damit auf einer fremden Seite kein
anderes iframe die Höhe verstellen kann. Die Vorschau im Tool nutzt dieselbe
Logik — was in der Vorschau sitzt, sitzt auch beim Kunden.

### 1.3 Tests

* Backend: 167 Tests grün (`pytest tests/`)
* Frontend: 28 Tests grün, davon 13 neu für den Einbaucode
* `eslint` auf den geänderten Dateien: sauber

---

## 2. Offen — in dieser Reihenfolge

### 2.1 Widget fertigstellen

- [ ] **Staging-Deploy verifizieren.** Seite `/app/widget` live durchgehen:
      Vorschau wächst mit, Anfragenliste gefüllt, Versandstatus grün.
- [ ] **Test-E-Mail senden** — erster Nachweis, dass der Weg aus dem Tool heraus
      wirklich funktioniert. War bisher nie möglich.
- [ ] **Eine echte Anfrage durchlaufen lassen** (eigene Adresse, echte Website):
      Widget → Audit → PDF → Brevo-Mail → Berichtsseite. Prüfen, ob
      `report_sent` in der neuen Liste auf „versendet" springt.
- [ ] **Einbau in die Ziel-Landingpage** mit dem neuen Code testen — inklusive
      Verhalten auf dem Telefon.
- [ ] **DSGVO-Prüfung** (Aufgabe #7): Einwilligung und Nachweis, Double-Opt-in,
      Datenminimierung, Speicherdauer, Auftragsverarbeitung Brevo,
      Informationspflichten Art. 13, Widerruf. Besonderheit: Die eingetragene
      Adresse gehört nicht zwingend dem Eintragenden — es geht eine E-Mail an
      einen Dritten.
- [ ] **Pentest-Prüfung** (Aufgabe #8): SSRF über die Zieladresse, Umgehung der
      Ratenbegrenzung, XSS in Widget und Berichtsseite, Entropie und IDOR bei
      `report_token`/`confirm_token`, Clickjacking, CORS, Enumeration über den
      Teaser-Endpunkt, Missbrauch als Spam-Schleuder.

### 2.2 Danach

- [ ] Bericht (PDF) und E-Mail grafisch und inhaltlich fertigstellen — dafür liegt
      ein E2E-Skript bereit, das die Kette ohne Datenbank durchspielt
      (Erhebung → Bewertung → PDF → Berichtsseite → Mail).
- [ ] Anforderungskatalog `docs/audit-anforderungen-2026-08-11.md` weiter umsetzen.

---

## 3. Was beim Weiterarbeiten zu wissen ist

**Lokal fehlen alle Schlüssel.** `ANTHROPIC_API_KEY`, `GOOGLE_PAGESPEED_API_KEY`
und `BREVO_API_KEY` sind lokal leer. Faktenerhebung und Bewertung laufen trotzdem,
aber KI-Kriterien und PageSpeed fallen auf „nicht erhoben" — das ist gewolltes
Verhalten, kein Fehler.

**Der Frontend-Build meldet Warnungen** aus Altbestand (`Settings.jsx`,
`Freigaben.jsx`, `Leads.jsx` u. a.). Mit `CI=true` gelten sie als Fehler. Die
heute geänderten Dateien sind sauber; die Altlasten sind ein eigener Punkt.

**Endpunkte, die sich geändert haben:**

| vorher | jetzt |
|---|---|
| `GET /api/acquisition/smtp` | `GET /api/acquisition/mail` (nur Anzeige) |
| `PUT /api/acquisition/smtp` | entfällt — Zugang kommt aus der Umgebung |
| `POST /api/acquisition/smtp/test` | `POST /api/acquisition/mail/test` |
| — | `GET /api/acquisition/widget/requests` |

`GET /api/widget/config` liefert zusätzlich `criteria_count`.
