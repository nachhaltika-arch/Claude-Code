# Routen ohne Aufrufer — Arbeitsstand (L-105)

> Gestartet am 01.09.2026. Zu jeder Route ohne Aufrufer stellt L-105 **eine**
> Frage: *fehlt der Knopf, oder ist die Route überflüssig geworden?*
>
> **Diese Datei ist der Arbeitsstand, nicht das Ergebnis.** Was hier steht, ist
> nachgemessen; was nicht hier steht, ist noch nicht beurteilt. Eine Liste, die
> so tut, als sei sie vollständig, ist schlechter als eine kurze, die sagt, wo
> sie aufhört.

Gemessen mit `kompagnon/backend/tools/unaufgerufene-routen.py`.

## Die Zahl und was sie bedeutet

| Stand | Ungerufen | Erklärt |
|---|---:|---:|
| Ausgangspunkt 01.09. | 96 | 14 |
| nach dem Aufräumen der Messung | 84 | 28 |

**Die Zahl fiel nicht, weil Routen verschwanden**, sondern weil die Messung
vorher Webhooks, Mail-Links und Betriebsanzeigen als offene Fragen führte.
Zwischendurch **stieg** sie von 86 auf 88: Ein entfernter Rückfall war der
einzige „Aufrufer" von `/api/usercards/` — die höhere Zahl war die ehrliche.

> **Ein ungerufener Endpunkt ist nicht ungefährlich, er ist unbeobachtet.**
> Am 31.08. lagen hinter zwei davon fremde Gespräche offen. Am 01.09. stand die
> Druckwarteschlange voller unbezahlter Bestellungen. Und `GET /api/leads/customers`
> trug eine Reparatur nicht, die anderswo dreimal gemacht worden war.

---

## Erledigt

### Die Messung selbst

| Was | Ergebnis |
|---|---|
| Vier Stripe-Rückrufe | erklärt — jede Kasse trägt ihren Rückruf im eigenen Router, `/api/webhooks/` erfasste sie nicht |
| Drei Mail-Links (`shop/download`, `shop/orders`, `files/portal`) | erklärt — belegt an `routers/shop.py:288` und `:304`, die sie schreiben |
| `/api/ping`, `/info`, `/robots.txt` | erklärt — Betriebsanzeigen; `/info` gibt seit 15.08. nur Wahrheitswerte aus |
| Vier `/editor`-Routen | **kein Befund** — `GrapesEditor.jsx` bekommt die Basis als Eigenschaft (`/api/pages`, von `KasWebsite.jsx` `/api/kas/pages`) |
| `AUSSERHALB_DES_REPOS` | **geleert** — die Begründung traf nicht mehr zu (siehe unten) |

### Eine Ausnahme, die ihren Grund überlebt hatte

Das Werkzeug nahm `/api/audit/status/` und `/api/audit/{id}` dauerhaft aus der
Prüfung: Die WebSprint-Landingpage liege außerhalb des Repos und hole ihr
Gratis-Audit darüber.

**An der Live-Seite nachgemessen:** `https://websprint.kompagnon.eu` enthält
**keinen einzigen** `/api/`-Aufruf. Sie bettet
`kas.kompagnon.group/embed/audit-widget.html` als iframe ein, und dieses Widget
ruft ausschließlich `/api/widget/*`. Die beiden Audit-Routen ruft unser
**eigenes** Frontend (`AuditTool.jsx`).

Damit ist nebenbei die Frage vom 31.08. beantwortet: `POST /api/audit/start`
hat sehr wohl einen Aufrufer. Ob er **öffentlich** sein muss, bleibt davon
getrennt eine Entscheidung.

### Repariert

| Fund | Was daran falsch war |
|---|---|
| `GET /api/leads/customers` | wählte über `status == "won"` und übersah `status == "customer"` — der **fünfte** Ort von L-26, nie repariert, weil niemand die Route ruft |
| `Dashboard.jsx:53` | Rückfall auf `usercards`, wenn `leads` leer ist — konnte nie auslösen |
| `automations.py` | derselbe Rückfall in den Kennzahlen, dazu mit `status='won'` statt über die Phase |
| Kopfzeile `routers/usercards.py` | behauptete, drei Präfixe würden von denselben Handlern bedient — keines davon stimmt |
| `MarginBadge.jsx` | behauptete weiter, keine Oberfläche rufe `/time` — seit 26.08. falsch |
| `qualitaet.jsx` | begründete das Behalten eines Endpunkts damit, dass er Altdaten halte — das tut die **Spalte** |

---

## Offen — Entscheidungen bei David

### 1 · Die Marge rechnet elf Zahlen, die Oberfläche zeigt eine

`GET /api/projects/{project_id}/margin` liefert `human_hours`, `human_costs`,
`ai_tool_costs`, `total_costs`, `margin_eur`, `margin_percent`,
**`hours_remaining_at_target`**, `status`, `alert`, `target_margin`,
`min_acceptable_margin`.

Angezeigt wird `margin_percent` — als Abzeichen auf der Projektpipeline, und
zwar aus der gespeicherten Spalte, nicht über diesen Endpunkt.

**Die interessante Zahl ist `hours_remaining_at_target`:** wie viele Stunden
noch bleiben, bevor die Zielmarge fällt. Das ist die Zahl, die beim Arbeiten
die Frage „weitermachen oder aufhören?" beantwortet — sie wird berechnet und
weggeworfen. Seit dem 26.08. werden Stunden wirklich eingetragen
(`Zeiterfassung.jsx`), seit dem 31.08. auch Abostunden.

**Empfehlung: Knopf bauen.** Eine Aufklappung am Projekt mit den vier Zahlen,
die zur Prozentzahl führen, plus der Reststunden.

### 2 · `PATCH /api/projects/{id}/gbp-checklist` — der letzte Schreiber einer eingefrorenen Spalte

Die alte GBP-Checkliste ist durch `QAChecklist.jsx` ersetzt. Die Spalte
`gbp_checklist_json` **wird weiter gelesen** — daraus werden bereits gesetzte
Haken übernommen. Der Endpunkt ist ihr **einziger Schreiber**, und niemand ruft
ihn.

Ihn zu behalten ist das Gegenteil der bereits getroffenen Entscheidung
(„wird weiterhin gelesen, nur nicht mehr geschrieben"): Wer ihn aufruft,
überschreibt die Quelle, aus der die Übernahme liest.

**Empfehlung: löschen.** Die Spalte bleibt.

### 3 · Akademie — zwei doppelte Anlege-Wege und eine fehlende Ansicht

| Route | Befund |
|---|---|
| `POST /api/academy/lessons` | Doppelweg — die Oberfläche legt über `/api/academy/modules/{id}/lessons` an |
| `POST /api/academy/modules` | Doppelweg — die Oberfläche nutzt `/api/academy/courses/{id}/modules` |
| `GET /api/academy/progress` | überflüssig — die Oberfläche nutzt `/progress/all` und `/courses/{id}/progress` |
| `GET /api/academy/certificates` | **fehlender Knopf** — „Alle Zertifikate des aktuellen Users"; es gibt keine Stelle, an der jemand seine Zertifikate sieht |

**Empfehlung:** die drei ersten löschen, für das vierte einen Knopf.

### 4 · Zwei Endpunkte beantworten dieselbe Frage, keiner hat einen Bildschirm

`GET /api/geo/ki-anbieter` („welche KI-Systeme angebunden sind — und welcher
Schlüssel fehlt") und `GET /api/diagnostics/config` („zeigt je Integration, ob
der laufende Prozess sie sieht — ohne Werte").

Das ist genau die Frage, an der L-58 und L-85 hängen: *Welcher Schlüssel fehlt?*
Beantwortet wird sie heute per `curl`.

**Empfehlung:** eine der beiden auf einen Bildschirm unter „System" legen und
die andere löschen — zwei Leser derselben Frage laufen auseinander.

### 5 · `GET /api/affiliate-conversions`

„Alle Affiliate-Conversions — für Dashboard und Admin-Übersicht." Es gibt weder
das eine noch das andere. Der Trackdesk-Webhook nimmt Meldungen entgegen; wo
sie landen, sieht niemand.

**Empfehlung:** erst klären, ob das Partnerprogramm läuft. Wenn nein,
zurückstellen statt löschen — es ist gebaut, nicht kaputt.

### 6 · `usercards` und `customers` — 18 Routen, eine Vorfrage

`usercards` wird **nie befüllt** (der Kopierschritt wurde entfernt,
`migrations_runtime.py:445`), und die einzige Stelle, die eine Zeile anlegt,
ist `POST /api/usercards/` — ohne Aufrufer. Von den Routen des Moduls ruft das
Werkzeug genau eine, und die liest seit dem 26.08. aus `leads`.

`customers` ist **nicht** dasselbe: Sieben lebende Module greifen auf die
Tabelle zu (`projects_anlegen`, `cms_connect`, `projects`, …). Nur ihre neun
HTTP-Routen ruft niemand.

**Das ist L-106 und hängt an einer Messung, die von hier aus niemand machen
kann:** Stehen produktiv Zeilen in `usercards`? Ein `SELECT count(*)` an der
Produktivdatenbank entscheidet, ob die 9 Routen Ballast oder Bestand sind.

---

## Noch nicht beurteilt

**53 Routen**, im Wesentlichen:

| Bereich | Anzahl |
|---|---:|
| `projects` | 18 |
| `leads` | 10 |
| `templates` | 5 |
| `sitemap` | 4 |
| `book` (wartet auf BUCH-08) | 3 |
| `diagnostics`, `scheduler` | 5 |
| Einzelne | 8 |

Die drei `book`-Routen sind erklärbar, sobald BUCH-08 existiert: Kasse,
Preisliste und Danke-Seiten-Auskunft gehören zur Landingpage, die noch nicht
gebaut ist. `diagnostics` und `scheduler` sind vermutlich Werkzeuge für die
Hand — das ist zu belegen, nicht anzunehmen.
