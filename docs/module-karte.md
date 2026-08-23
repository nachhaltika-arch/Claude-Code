# KOMPAGNON — Modulkarte

> **Wofür diese Datei da ist.** Es fühlt sich an, als würde alles gleichzeitig
> entwickelt. Diese Karte schneidet das System in Module, die sich **einzeln
> fertigstellen** und **einzeln abschalten** lassen — damit „fertig" wieder ein
> erreichbarer Zustand ist und nicht ein Horizont.
>
> Stand: 2026-08-21. Sie ist **gemessen, nicht entworfen**: Der Schnitt folgt
> dem, was im Code tatsächlich zusammenhängt, nicht dem, was zusammengehören
> sollte. Wo beides auseinanderfällt, steht es dabei.

---

## Wie geschnitten wurde

Drei Messungen, übereinandergelegt:

1. **Das Menü** (`utils/menue.js`) — acht Gruppen. Das ist dein Denkmodell und
   der einzige Schnitt, den ein Nutzer sieht.
2. **Die Router** (`backend/routers/`) — 51 Dateien, **458 Routen**, 27.136
   Zeilen. Das ist der tatsächliche Zusammenhang im Code.
3. **Die Tabellen** — **66** insgesamt: 39 im ORM (`database.py`), **27 nur in
   rohem SQL** (`migrations_runtime.py::run_migrations`). Das ist der Zusammenhang in den
   Daten.

Ein Modul ist dort geschnitten, wo alle drei zusammenfallen. Wo sie es nicht
tun, steht das als **Naht** im jeweiligen Abschnitt — eine Naht ist eine
Stelle, an der das Abschalten heute nicht sauber ginge.

---

## Die Karte

| | Modul | Abschaltbar | Hängt ab von | Zustand |
|---|---|---|---|---|
| **M0** | Fundament | **nein** | — | 🟢 trägt |
| **M1** | Akquise | ja | M2, M3 | 🟡 |
| **M2** | Audit & Bewertung | nein¹ | M0 | 🟢 |
| **M3** | Vertrieb | nein¹ | M0 | 🟢 |
| **M4** | Angebot & Zahlung | ja | M3 | 🟢 **fertig 21.08.** |
| **M5** | Projektabwicklung | ja | M3 | 🟢 |
| **M6** | Website-Bau (KAS) | ja | M5 | 🟡 |
| **M7** | Kundenportal | ja | M5 | 🟢 |
| **M8** | Akademie | ja | M0 | 🟡 leer |
| **M9** | Betreuung | ja | M3, M5 | 🟡 |
| **M10** | Werbung | ja | M3 | 🟠 |

¹ *Technisch abschaltbar, praktisch nicht: Ohne sie gibt es kein Produkt.*

---

## M0 · Fundament — läuft immer

**Was drin ist:** Anmeldung und Sitzung, Rollen und Rechte, Systemeinstellungen,
Fehlerprotokoll, Scheduler, Mailversand, Dateiablage.

| | |
|---|---|
| Router | `auth_router`, `admin_settings`, `fehler`, `files`, `versand`, `diagnostics` |
| Tabellen | `users`, `user_sessions`, `role_permissions`, `system_settings`, `fehlerprotokoll`, `automation_logs` |
| Bildschirme | Anmeldung, Profil, Sicherheit, System, Benutzer, Rollen |
| Automatik | 19 Scheduler-Jobs hängen hier ein |

**Nicht abschaltbar** — ohne M0 gibt es keine Anmeldung.

**Offen:** L-05 (zehn von 18 Rechten ohne Sperre) · L-34 + L-57 + L-44 + L-35
(Umzug und Betrieb, blockiert am Render-Zugang) · L-08 (drei npm-Befunde an
`react-scripts`) · L-11 (Wiederherstellung nie geprobt) · L-41 (Wurzel: L-34)

---

## M1 · Akquise — wie ein Betrieb ins System kommt

**Was drin ist:** Kaltakquise (HWK-Scraper), Domain-Import, Audit-Tool,
Analyse-Widget, elf Webhook-Endpunkte.

| | |
|---|---|
| Router | `scraper`, `crawler`, `widget`, `webhooks`, `webhooks_trackdesk`, `acquisition`, `kampagne` |
| Tabellen | `widget_requests`, `crawl_jobs`, `crawl_results`, `lead_domains` |
| Bildschirme | Kaltakquise, Domain-Import, Audit-Tool, Analyse-Widget, Webhooks |
| Automatik | `weekly_hwk_scraper`, `daily_enrich_leads`, `domain_check_every_6h` |

**Abschaltbar: ja.** Der Scraper hat bereits einen eigenen Schalter
(`HWK_SCRAPER_ENABLED`). Das Widget läuft auf **fremden Seiten** — es
abzuschalten heißt, es dort still zu legen, nicht nur im Menü zu verstecken.

**Offen:** L-62 (fünf Lead-Wege ohne Mailstrecke) · L-65 (unbelegte
Werbezahlen im Widget) · L-03 (Staging liefert das Widget anders als produktiv)

---

## M2 · Audit & Bewertung — der Türöffner

**Was drin ist:** Der Prüfkatalog (8 Kategorien, **39 bewertete Kriterien**
plus 4 Infrastruktur-Angaben ohne Wertung), die
Erhebung, die KI-Bewertung, GEO, der PDF-Bericht.

| | |
|---|---|
| Router | `audit`, `geo`, `agents` |
| Dienste | `audit_criteria`, `audit_collectors`, `audit_scoring`, `audit_ai`, `audit_pagespeed`, `geo_optimizer`, `pdf_generator` |
| Tabellen | `audit_results`, `geo_analyses` |
| Automatik | `geo_monthly_monitoring` |
| Prüfung | eingefrorene Referenz-Website (`tests/referenzseite.py`) |

**Das am besten geprüfte Modul.** Der Katalog ist die einzige Wahrheitsquelle,
und die Referenzseite fängt jede Verschiebung.

**Offen:** L-58 (b) — *tatsächliche* KI-Sichtbarkeit messen; kostet je Lauf
Geld und ist ein eigenes Produkt.

---

## M3 · Vertrieb — der Betriebsbestand

**Was drin ist:** Betriebe, Deals, Lebenszyklus, Kundenkartei, Export.

| | |
|---|---|
| Router | `leads`, `deals`, `customers`, `usercards`, `export` |
| Tabellen | `leads` (**101 Spalten**, davon 72 im ORM), `deals`, `deal_items`, `customers`, `usercards` |
| Bildschirme | Betriebe, Betriebsblatt, Deals, Export |

**Naht ✅ aufgetrennt am 21.08.2026.** Vier Router bedienten `/api/customers`.
Das Auftrennen hat drei Dinge freigelegt, die vorher niemand sehen konnte —
siehe „Was die erste Naht gekostet hat" am Ende dieser Datei.

**Offen:** L-56 (Löschen eines Betriebs mit Kundenzugang — Entscheidung) ·
L-59-Rest (Rechtsgrundlage für elf Quellen — Entscheidung) · L-24

---

## M4 · Angebot & Zahlung — 🔴 hier bricht die Kette

**Was drin ist:** Pakete, Verkaufsseiten, Checkout, Stripe, Rechnungen,
Affiliate.

| | |
|---|---|
| Router | `payments`, `products`, `pages`, `geo_payments` |
| Tabellen | `products`, `invoices`, `public_pages`, `page_templates`, `affiliate_conversions` |
| Bildschirme | Pakete, Verkaufsseiten |

**🟢 Geschlossen am 21.08.2026.** Der Bestellweg lief von `/paket/premium`
bis `/checkout/success` nur nach `/login` — die Bausteine lagen im Quellbaum
und wurden von nichts importiert (L-64). Vier Routen später läuft er im
Browser durch: Paketseite mit Preis aus der Datenbank, Kasse mit vorgewähltem
Paket, Rücksprung mit Paketnamen vom Server.

Beim Verdrahten kam heraus, dass die ganze Strecke **gegen eine Schnittstelle
geschrieben war, die es nicht gibt** — sechs falsche Adressen, darunter zwei in
der Paketverwaltung, die zusätzlich Felder las, die die Tabelle nicht hat
(L-71). Der Wächter `test_frontend_adressen.py` vergleicht seitdem jeden
Frontend-Aufruf mit den geladenen Routen. Die Preisbeschriftung ist auf
Endpreise korrigiert (L-61, Davids Entscheidung).

**Offen:** L-64 (Bestellweg) · L-61 (MwSt.-Widerspruch) · L-29-Rest (drei
unerreichbare Paketseiten mit festen Preisen) · L-20 (WebSprint-Landingpage
außerhalb des Systems)

**Dieses Modul ist das kürzeste Stück zwischen „Interesse" und „Geld".
Solange es bricht, ist jedes andere Modul Vorleistung.**

---

## M5 · Projektabwicklung — was nach dem Kauf passiert

**Was drin ist:** Projekte, 7 Phasen, Checklisten, Briefing, Marge,
Zeiterfassung, Projekt-Assistent.

| | |
|---|---|
| Router | `projects` (**4.848 Zeilen, 66 Routen**), `briefings`, `briefing`, `assistant`, `content_scraper_router` |
| Tabellen | `projects`, `project_checklists`, `project_files`, `project_credentials`, `briefings`, `time_tracking` |
| Automatik | `daily_check_overdue_phases`, `daily_update_margins`, `daily_send_briefing_reminders`, `daily_phase_postgolive_transitions`, `daily_check_missing_materials` |

**Naht ✅ aufgetrennt am 21.08.2026** — siehe „Die zweite Naht" unten.
`projects.py` bleibt mit 4.848 Zeilen die größte Datei des Systems (L-25).
Offen bleibt `/api/briefings`, die dritte Naht (L-27).

**Offen:** L-25 (Dateigröße) · L-27 (zwei Briefing-Strukturen — Entscheidung) ·
L-14 (Assistent fachlich unbeurteilt) · L-50-Rest (`project_files` speichert
lokale Pfade)

---

## M6 · Website-Bau (KAS) — das Erzeugnis

**Was drin ist:** Sitemap, Wireframe, Style-Guide, Design, drei
Editor-Generationen, Komponenten-Bibliothek, Vorlagen, Netlify-Deploy,
Qualitätsschleife.

| | |
|---|---|
| Router | `sitemap`, `component_library`, `templates`, `branddesign`, `designs`, `mockups`, `content`, `kas_router`, `website_mockup` |
| Tabellen | `sitemap_pages`, `component_library`, `website_templates`, `website_versions`, `kas_pages`, `kas_gjs_data`, `mockup_versions`, `content_sections`, `content_media` |
| Automatik | `netlify_dns_check_every_15min`, `netlify_ssl_check` |

**Naht ✅:** `component_library` bedient `/api/components` **und**
`/api/projects` — über zwei getrennte Router-Objekte, die beide zu M6 gehören.
Ein Schalter am Router trifft also das Richtige. Der `/api/projects`-Router
trägt seit dem 21.08. dieselbe Sperre wie sein Nachbar (L-69).

**Design-Canvas seit 21.08.:** Die vier Ansichten liegen an vier Stellen und
haben je einen eigenen Editor; keine zeigt zwei Seiten nebeneinander.
`GET /api/design-canvas/{lead_id}` gibt dieselben Daten als Artboards aus —
eine Fläche, vier Seiten, ein Artboard je Kundenseite. Bearbeitet kommen sie
über `POST /api/design-canvas/{lead_id}/import` zurück nach
`sitemap_pages.mockup_html`, versioniert über `mockup_versions`.

Der mittlere Schritt — aus den Dateien einen Canvas machen — läuft in Claude
Code, nicht im Server: dafür gibt es keine Schnittstelle. `scripts/canvas-export.py`
ist der Weg dorthin, wenn man ohnehin an der Datenbank sitzt.

**Offen:** L-26 (drei Editor-Generationen parallel) · L-40 (Qualitätsschleife
nie am Stück gelaufen — fehlende Netlify-Variable) · L-19 (keine eigene Domain
für Kundenseiten) · L-16 (Envato-Wireframes) · L-23 · L-15

---

## M7 · Kundenportal — was der Kunde sieht

| | |
|---|---|
| Router | `portal`, `messages`, `cms_connect` |
| Tabellen | `portal_documents`, `portal_messages`, `messages`, `communications` |
| Bildschirme | Kundenportal, Freigaben, Meine Rechnungen, Support-Anfragen |

**Abschaltbar: ja — aber mit Vorsicht.** Kunden haben Zugänge; ein Abschalten
sperrt Menschen aus, die dafür bezahlt haben.

---

## M8 · Akademie — gebaut und leer

| | |
|---|---|
| Router | `academy` (34 Routen) |
| Tabellen | 8 (`academy_courses`, `academy_modules`, `academy_lessons`, `academy_module_access`, `academy_certificates`, …) |

**Die Technik ist seit dem 21.08. vollständig** — Module tragen Beschreibung,
Bild, Sperre; Zuweisung je Modul und Kunde funktioniert. **Aber der Seed legt
fünf Kurse und null Module an.** Die Modulebene ist gebaut und leer.

**Offen:** L-60 (Lehrplan — inhaltlich, keine Programmierung) · L-54-Rest
(zweideutige Altkennungen)

---

## M9 · Betreuung — nach dem Go-live

| | |
|---|---|
| Router | `tickets`, `retainer` |
| Tabellen | `support_tickets`, `retainer_contracts` |
| Automatik | `monthly_performance_report` |

**Offen:** L-18 (keine In-App-Benachrichtigungen)

---

## M10 · Werbung — 🟠 das am wenigsten fertige

| | |
|---|---|
| Router | `newsletter`, `campaigns`, `mail_events` |
| Tabellen | `newsletters`, `newsletter_lists`, `newsletter_contacts`, `campaigns`, `mail_events`, `email_logs` |
| Automatik | `email_sequence_runner` |

**Offen:** L-21 (Google/Meta Ads: **null Code**, XL) · L-22 (Analytics: Plan,
null Code, L) · L-38 (zwei Brevo-Haken im Mai-Audit waren nie wahr) · L-62

---

## Der Schalter — wie das An und Aus funktionieren soll

**Es gibt bereits einen erprobten Präzedenzfall.** `services/versandsperre.py`
hält allen automatischen Mailversand an: ein Schlüssel in `system_settings`,
sichere Vorgabe („aus", solange niemand ausdrücklich zustimmt), im Menü
sichtbar statt nur in den Einstellungen. Er ist am 17.08. entstanden, nachdem
ein Job vier Monate lang Mails an Nicht-Kunden geschickt hatte und es **keinen
Weg gab, ihn anzuhalten**.

Genau diese Form bekommen die Module:

```
system_settings:  modul.m1_akquise = "aus"
                  modul.m8_akademie = "aus"
```

**Drei Ebenen, und alle drei sind nötig:**

1. **Menü** — die Gruppe verschwindet. Billig, aber allein wertlos: Wer die
   Adresse kennt, kommt trotzdem hin.
2. **Router** — eine Abhängigkeit am Router antwortet **404**, nicht 403. Ein
   403 bestätigt die Existenz; dieselbe Entscheidung wie bei L-52.
3. **Scheduler** — die Jobs des Moduls laufen nicht an. Das ist die Ebene,
   die wirklich zählt: Ein abgeschaltetes Modul, dessen Nachtlauf weiter Mails
   verschickt, ist nicht abgeschaltet.

**Was ein Schalter ausdrücklich nicht tut:** Daten löschen. Aus heißt
unsichtbar und untätig, nicht weg.

**Korrektur vom 21.08.2026:** Hier stand, die Nähte blockierten den Schalter.
Nachgemessen stimmt das nicht — **kein Router bedient zwei Module**, und ein
Schalter am Router funktioniert unabhängig vom Präfix. Der Schalter ist also
**nicht blockiert** und kann gebaut werden.

Die Nähte bleiben trotzdem dran, aber aus einem anderen Grund: Auf einer
geteilten Adresse gewinnt der zuerst eingebundene Router, der andere ist tot —
und tote Routen sind ungeprüfte Routen. Was das erste Auftrennen zutage
gefördert hat, steht weiter unten.

---

## Was „fertig" heißt

Ein Modul ist fertig, wenn **alle fünf** Zeilen stimmen. Nicht vier.

| | Bedingung |
|---|---|
| 1 | Der Hauptweg läuft **auf Staging von Anfang bis Ende durch**, von einem Menschen bedient |
| 2 | Jede offene Lücke des Moduls ist geschlossen **oder** ausdrücklich vertagt, mit Datum |
| 3 | Ein Test hält den Hauptweg — Browser-Test, wo es einen Bildschirm gibt |
| 4 | Der Schalter wirkt auf allen drei Ebenen (Menü, Router, Scheduler) |
| 5 | Es gibt **keine offene Entscheidung** mehr, die den Weg blockiert |

Bedingung 5 ist die, an der heute am meisten hängt: Neun Fragen warten auf dich
(`stand-2026-08-21.md`, letzter Abschnitt), und sechs davon kosten Minuten.

---

## Die empfohlene Reihenfolge

**Erst die Kette, die Geld verdient — alles andere aus.**

Ein Kunde durchläuft: **M1 → M2 → M4 → M5 → M6 → M7.** Bricht ein Glied, ist
der Rest Vorleistung. **M4 hielt bis zum 21.08. nicht** — seitdem läuft der
Bestellweg durch, und das nächste Glied ist M5.

| Schritt | Modul | Warum jetzt | Aufwand |
|---|---|---|---|
| ~~1~~ | ~~**M4 Angebot & Zahlung**~~ | ~~Der Bestellweg ist tot (L-64)~~ — **erledigt 21.08.2026** | S |
| **2** | **M2 + M3** | Beide fast fertig — nur Entscheidungen offen, kein Code | S |
| **3** | **M5 + M6** | Die Lieferung. Größtes Stück, aber der Kunde wartet darauf | M–L |
| **4** | **M7 Kundenportal** | Übergabe. Fast fertig | S |
| **5** | **M0 Fundament** | Der Umzug (L-34), sobald Render wieder erreichbar ist | L |

**Sofort abschalten, bis Schritt 4 steht:**

- **M1 Kaltakquise** (der Scraper — nicht das Widget, das ist der Türöffner)
- **M8 Akademie** — leer, und niemand vermisst sie
- **M9 Betreuung** — greift erst nach dem ersten Go-live
- **M10 Werbung** — Ads und Analytics sind null Code; der Newsletter kann warten

Das nimmt **vier von zehn Modulen** aus dem Blickfeld. Was übrig bleibt, ist
die Kette, die einen Kunden von der Anfrage bis zur fertigen Website bringt.

---

## Was der Schnitt sichtbar gemacht hat

Vier Dinge, die vorher niemand so gesehen hat:

1. **Drei Nähte.** `/api/customers` (vier Router), `/api/projects` (vier
   Router), `/api/briefings` (zwei). Solange sie bestehen, lässt sich kein
   Modul sauber abschalten.
2. **Das Datenmodell ist nicht maßgeblich — und zwar auf zwei Ebenen.**
   **27 von 66 Tabellen** kennt das ORM gar nicht; sie entstehen in rohem SQL
   in `main.py`. Und selbst eine modellierte Tabelle ist nicht vollständig:
   `leads` hat **101 Spalten**, von denen das ORM **72** kennt — 29 werden per
   `ALTER TABLE` nachgereicht und stehen in keinem Modell. Ein Modul kann
   seine Daten nicht besitzen, wenn ein Drittel davon außerhalb liegt.
   *(Beim Schreiben dieser Karte selbst gefunden: Die Lückenliste nannte
   „79 Felder am Lead" — nachgemessen sind es 72 im Modell und 101 in der
   Tabelle. Beide Zahlen sind korrigiert.)*
3. **Ein Modul trägt ein Fünftel des Backends.** `projects.py` hat 4.848
   Zeilen und 66 Routen — mehr als M8, M9 und M10 zusammen.
4. **Die Kette bricht genau an der Kasse.** Alles davor ist gebaut und
   geprüft, alles danach auch. Der eine Punkt, an dem Geld fließt, ist der
   einzige, der nicht funktioniert.

---

## Was die erste Naht gekostet hat — und was sie erbracht hat

Die Naht `/api/customers` ist am 21.08.2026 aufgetrennt. Der Befund war
**größer als die Naht**.

**Zuerst eine Korrektur an dieser Datei.** Oben stand, die Nähte blockierten
den Schalter, weil Module auf derselben Adresse lägen. Nachgemessen stimmt das
so nicht: **Kein Router bedient zwei Module.** Ein Schalter am *Router* — nicht
am Präfix — hätte von Anfang an funktioniert. Die Nähte blockieren den Schalter
also nicht. Sie sind trotzdem gefährlich, nur aus einem anderen Grund:

**19 Kollisionen**, gemessen mit normalisierten Platzhaltern (`{card_id}` und
`{lead_id}` sind verschiedene Zeichenketten und treffen dieselben Aufrufe — eine
erste, wörtliche Messung übersah sechs davon).

Drei Dinge, die dabei herauskamen:

1. **`GET /api/customers/` lieferte UserCards statt Customers.** Zwei
   verschiedene Entitäten auf einer Adresse; welche antwortet, hing an der
   Reihenfolge in `main.py`. Am laufenden Server nachgewiesen — mit einer
   UserCard und null Customers kam die UserCard zurück. Und die
   OpenAPI-Beschreibung nannte einen **dritten** Handler, weil FastAPI dort den
   *zuletzt* registrierten einträgt, während der *erste* antwortet.
2. **Die Überdeckung machte die Sicherheitsarbeit** (L-66, L-68). Der
   überdeckende Alias trug `require_innendienst`, der überdeckte Router nur
   `require_any_auth`. Wer den Alias entfernt, ohne das zu bemerken, öffnet
   den Kundenbestand für jeden angemeldeten Kunden. Und die überdeckte Route
   war nicht bloß ungenutzt — sie war **kaputt**: Sie antwortete 500, sobald
   eine Kundenzeile keinen Termin hatte.
3. **Vier Routen ließen jeden Angemeldeten auf fremde Websites
   veröffentlichen** (L-66). `cms_connect.py` hing mit `require_any_auth` und
   ohne Zeilenprüfung unter `/api/customers`. Ein angemeldeter Kunde konnte
   beliebiges HTML in die Live-Website eines anderen Kunden schieben.

**Der Lehrsatz:** Eine tote Route ist nicht nur ungenutzt, sie ist
**ungeprüft**. Wer eine Überdeckung entfernt, schaltet scharf, was nie jemand
gesehen hat — deshalb gehört zu jedem Auftrennen ein Blick auf das, was darunter
lag.

`tests/test_router_kollisionen.py` hält die Adressen von jetzt an eindeutig:
von 19 Kollisionen bleibt **eine**, und die ist namentlich als Entscheidung
vermerkt (`POST /api/projects/{}/scrape` — Branddesign gegen Inhalt).

### Die zweite Naht: `/api/projects` (21.08.2026)

Vier Router, **dasselbe Muster wie bei der ersten** — und wieder größer als die
Naht:

**Dreizehn Routen ließen jeden Angemeldeten an jedes Projekt** (L-69).
`projects.router` trug `require_innendienst` und war richtig; die drei anderen
trugen nur eine Anmeldung und **keine Zeilenprüfung**. Ein angemeldeter Kunde
konnte die fertige Website **jedes** Projekts als ZIP laden, jeden Wireframe
lesen **und überschreiben**, und auf jedem Projekt einen Inhalts-Lauf starten.

Kein Kundenbildschirm braucht sie — alle Aufrufer hängen an
`roles={'admin','auditor'}`, und `export-zip` hat gar keinen Aufrufer. **Die
Sperre stand wieder in der Oberfläche statt am Endpunkt.**

**Zwei Modelle auf einer Tabelle** (L-70). `routers/mockups.py` und
`routers/designs.py` bildeten beide `mockup_versions` ab — Zeichen für Zeichen
dieselbe Klasse. Aufgefallen ist es nur, weil der neue Kollisionstest **alle**
Router importiert; vorher hatte nie etwas beide Dateien zugleich geladen.
`mockups.py` war zudem **nirgends eingebunden** — vier Routen, die es nicht
gab, eine Kopie ohne die Sperre, die ihr Zwilling im August bekam. Entfernt.

**Die letzte Kollision ist aufgelöst.** `POST /api/projects/{id}/scrape` gab es
zweimal mit zwei Bedeutungen: Branddesign lesen (`projects.py`, gewann) und
mehrseitiger Inhalts-Lauf (`content_scraper_router.py`, unerreichbar). Der
Inhalts-Lauf heißt jetzt `/{id}/scrape-pages` — er wird beim Anlegen eines
Projekts ohnehin automatisch gestartet, es fehlte nur der Weg, ihn noch einmal
anzustoßen.

**Damit ist `GEPRUEFTE_AUSNAHMEN` leer:** null Kollisionen unter 471 Aufrufen.

**Ein Fehlalarm, offen berichtet:** Ich hatte „vier vollständig offene Routen"
gemeldet, als ich `mockups.py` ohne Sperre sah. Nachgemessen — produktiv
`GET /api/mockups/1` → 404 gegen `GET /api/designs/1` → 401 — war der Router
nirgends eingebunden. Kein Loch, tote Datei. Der Unterschied zwischen „ungesichert"
und „nicht vorhanden" ist eine Registrierungszeile, und die gehört nachgesehen,
bevor man Alarm schlägt.
---

## Der nächste Schritt

**Sieh dir den Schnitt an.** Er kodiert Produktentscheidungen — was zu M4
gehört und was zu M6, ist keine technische Frage. Wenn er so stimmt, baue ich
in dieser Reihenfolge:

1. Die **drei Nähte** auftrennen (höchstens zwei Tage)
2. `services/module.py` nach dem Muster von `versandsperre.py`
3. Die drei Ebenen verdrahten — Menü, Router, Scheduler
4. Einen Bildschirm unter Verwaltung, auf dem die Schalter stehen

Vorher den Schalter zu bauen hieße, ihn auf Grenzen zu setzen, die sich noch
verschieben — und ein Schalter auf der falschen Grenze schaltet das Falsche ab.
