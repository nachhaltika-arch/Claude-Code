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

| Stand | Ungerufen | Erklärt | beurteilt |
|---|---:|---:|---:|
| Ausgangspunkt 01.09. | 96 | 14 | 0 |
| nach dem Aufräumen der Messung | 84 | 28 | 31 |
| nach dem `projects`-Block | 84 | 28 | **50** |

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

## Dritter Block — `projects` (19 Routen, 01.09.2026 abends)

Der größte Cluster. Er zerfällt in **drei Muster**, und keines ist einfach
Ballast.

### 1 · Ein ganzes Merkmal ohne Auslöser — und der Kunde wartet darauf

| Route | |
|---|---|
| `POST /{id}/generate-versions` | 248 Zeilen: erzeugt drei Website-Entwürfe aus Briefing, Inspirationen und Vorlagen |
| `GET /{id}/versions` | die erzeugten Versionen |
| `GET /{id}/versions/{vid}/preview` | HTML-Vorschau fürs iframe |
| `POST /{id}/versions/{vid}/select` | eine auswählen |

**Die Kundenseite ist fertig gebaut und angeschlossen.** Das Kundenportal
zeigt „🎨 Ihre 3 Website-Entwürfe sind bereit! — Wählen Sie Ihren Favoriten",
mit Vorschau-iframe je Entwurf, und ruft dafür `/api/portal/versions/{id}/preview`
und `/select`.

**Nur entstehen kann kein einziger Entwurf.** `POST /generate-versions` ist der
**einzige** Schreiber von `website_versions` — nachgemessen: Das Wort kommt im
ganzen Repo nur in seiner eigenen Definition vor. Kein Bildschirm, kein
Scheduler, kein Test ruft es.

**Warum es niemandem auffiel:** `KundenPortal.jsx` hat den ehrlichen Riegel
`if (versions.length === 0) return null` — der Abschnitt versteckt sich, wenn
nichts da ist. Der Kunde sieht also kein leeres Versprechen. Genau deshalb
merkt auch niemand, dass er es nie sehen wird.

> **Ein gut versteckter Mangel ist schwerer zu finden als ein sichtbarer.**

**Empfehlung: Knopf bauen.** Von vier Routen fehlt genau eine Auslösung; der
Rest der Kette steht.

### 2 · Ein abgelöstes Parallelsystem, das noch steht

| Route | ersetzt durch |
|---|---|
| `GET /{id}/sitemap` | `/api/sitemap/{lead_id}/*` (der Sitemap-Planer) |
| `PATCH /{id}/sitemap` | ebenso |
| `POST /{id}/freigabe` | `briefings.freigaben` über `PATCH /api/briefings/{id}` |
| `GET /{id}/sitemap-register` | — |

Dahinter hängen **zwei tote Spalten**: `projects.sitemap_json` wird nur von den
beiden ungerufenen Routen geschrieben und gelesen; `projects.sitemap_freigabe`
setzt ausschließlich `POST /freigabe`.

**Die Freigaben, die man im Werkzeug sieht, kommen woanders her.** Sowohl
`BriefingTab.jsx` als auch die Kundenansicht `Projektfreigaben.jsx` lesen
`briefings.freigaben` — dieselbe Bezeichnung `sitemap_freigabe`, ein anderer
Speicher. Zwei Mechanismen mit demselben Namen, einer davon tot.

**Empfehlung: löschen**, Routen und Spalten. Hier fehlt kein Knopf — der Weg
ist gegangen worden, nur woanders.

### 3 · Doppelwege — dieselbe Sache, zweimal gebaut

| ungerufen | benutzt wird |
|---|---|
| `POST /api/projects/{id}/briefing-prefill` (98 Z.) | `POST /api/leads/{id}/briefing-prefill` |
| `POST /api/projects/{id}/scrape` (88 Z.) | `POST /api/crawler/scrape-content/{id}` |

Bei `briefing-prefill` ist die Entscheidung sogar schon getroffen und
aufgeschrieben: Der Kopf von `routers/leads_briefing.py` sagt, die Adresse
laute `/api/leads/{lead_id}/briefing-prefill` „und sie soll es bleiben". Die
zweite Fassung unter `projects` hat das nicht mitbekommen.

**Empfehlung: löschen.**

### 4 · Der Rest, einzeln beurteilt

| Route | Urteil |
|---|---|
| `GET /{id}/margin` | **Knopf fehlt** — elf Kennzahlen, angezeigt wird eine (siehe zweiter Block) |
| `PATCH /{id}/gbp-checklist` | **löschen** — letzter Schreiber einer eingefrorenen Spalte (zweiter Block) |
| `POST /{id}/netlify/add-subdomain` (66 Z.) | erzeugt eine DNS-Anleitung; ohne Aufrufer, ohne Ersatzweg — **offene Frage** |
| `POST /{id}/go-live-pagespeed` (81 Z.) | die gelebte Messung läuft über `/api/leads/{id}/pagespeed` — **wahrscheinlich Doppelweg**, zu bestätigen |
| `GET /{id}/qa/result` | die QA-Ansicht holt ihr Ergebnis anders — **offene Frage** |
| `POST /{id}/trigger` | Automatik von Hand auslösen — Werkzeug für die Hand |
| `GET /{id}/debug`, `POST /seed` | Diagnose und Saat — Werkzeuge für die Hand, gehören erklärt |
| `GET /api/dashboard/projects-by-phase` | „for kanban view" — die Kanban-Ansicht gibt es, sie rechnet selbst. **Offene Frage** |

---

## Noch nicht beurteilt

**34 Routen**, im Wesentlichen:

| Bereich | Anzahl |
|---|---:|
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
