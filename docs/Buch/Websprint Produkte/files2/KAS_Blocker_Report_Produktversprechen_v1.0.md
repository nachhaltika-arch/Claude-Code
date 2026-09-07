# Blocker-Report — Produktversprechen vs. Systemwirklichkeit
Version 1.0 · 23.08.2026 · Bezug: Produktarchitektur Websprint v1.0

---

## Zusammenfassung

Von fünf geplanten Produkten sind **zwei sofort verkaufbar** (nach zwei kleinen Fixes), **eines gesperrt**, **eines rechtlich zu klären**, **eines noch nicht geschrieben**.

Elf Punkte wurden identifiziert, an denen ein geplantes Verkaufsversprechen von dem abweicht, was KAS heute tatsächlich leistet. Vier davon sind haftungsrelevant.

| Ampel | Anzahl | Bedeutung |
|---|---|---|
| 🔴 | 4 | Verkauf würde eine Leistung zusichern, die nicht existiert |
| 🟠 | 4 | Widersprüchlich oder rechtlich ungeklärt |
| 🟡 | 3 | Technische Schuld, die beim Skalieren zuschlägt |

---

## 🔴 Kritisch — Verkaufssperre bis behoben

### L1 · GEO/GAIO wird nicht ausgeliefert
**Versprechen:** SYSTEM enthält `llms.txt`, `schema.org`, Ground Page, GA4, Clarity.
**Wirklichkeit:** Tracking- und Strukturcode wird nicht in die auf Netlify deployten Kundenseiten injiziert. Das Kernversprechen des Produkts existiert in Produktion nicht.
**Risiko:** Mangel nach § 633 BGB; irreführende geschäftliche Handlung nach § 5 UWG. Bei einem Produkt zu 12.900 € ist das kein Bagatellrisiko.
**Fix:** Injection in den Netlify-Deploy-Schritt einbauen **plus automatische Verifikation nach Go-Live** (Abruf der Live-URL, Prüfung auf Vorhandensein der Artefakte). Ohne Verifikation weiß niemand, wenn es wieder ausfällt.
**Sperre:** Produkt 03 (SYSTEM), GEO/GAIO Add-on.

### L2 · Standard-Garantie ist nicht messbar
**Versprechen:** „mindestens 85 von 100 Punkten bei Abnahme".
**Wirklichkeit:** Ohne `PAGESPEED_API_KEY` auf Render werden **18 von 100 Punkten dauerhaft nicht erhoben**. Der maximal erreichbare Score liegt bei 82. Die zugesicherten 85 sind arithmetisch unerreichbar.
**Risiko:** Jede Abnahme scheitert per Definition. Jeder Kunde hat einen Anspruch auf kostenlose Nachbesserung, den wir nie erfüllen können.
**Fix:** API-Key setzen (Aufwand: Minuten). Danach echte Messreihe über mindestens 5 Referenzseiten, bevor 85 zugesichert werden.
**Sperre:** Standard-Garantie in allen drei Websprint-Produkten.

### L3 · Zwei verschiedene Standards im selben Produkt
**Versprechen:** Ein Standard, eine Punktzahl.
**Wirklichkeit:** Frontend arbeitet mit Schwellen 85/70/50/30, Backend mit 95/85/70/50. Dieselbe Website bekommt in der App und im Report unterschiedliche Bewertungen.
**Risiko:** Der Mechanismus, auf dem die gesamte Preisstellung ruht, widerlegt sich selbst. Ein Kunde, der das bemerkt, hat Recht — und wir haben kein Argument.
**Fix:** **Eine** Schwellendefinition im Backend, Frontend liest sie über die API. Keine Duplikate, keine Konstanten im JSX. Danach alle bereits versendeten Reports prüfen.
**Sperre:** Buchveröffentlichung, Abnahmeprotokolle, Check-Versand.

### L4 · Branchenklassen K1–K6 existieren nur im Buch
**Versprechen:** Buch und Vertrieb beschreiben ein branchenspezifisches Bewertungsmodell.
**Wirklichkeit:** In KAS nicht implementiert. Ein Leser, der nach K3-Bewertung fragt, bekommt sie nicht.
**Fix:** Implementieren **oder** aus dem Manuskript streichen. Beides ist vertretbar — der Zwischenzustand nicht.
**Sperre:** Buchveröffentlichung.

---

## 🟠 Widersprüchlich oder rechtlich ungeklärt

### L5 · Punktetabellen im Buch sind konstruiert, nicht extrahiert
Die Punktabzugstabellen wurden plausibel geschrieben, nicht aus `audit_criteria.py` erzeugt. Buch und Software werden auseinanderlaufen, spätestens beim ersten Kriterien-Update.
**Fix:** Export-Skript bauen. Das Manuskript muss aus der Software generiert werden — dauerhaft, nicht einmalig.

### L6 · Bauzeitgarantie ohne definierten Fristbeginn
„14 Tage" ohne Definition, wann die Frist beginnt und wann sie pausiert, ist entweder unverbindlich (dann ist es keine Garantie und die Werbung damit angreifbar) oder ruinös (dann zahlen wir für die Langsamkeit des Kunden).
**Fix:** Mitwirkungskatalog in AGB und Angebot, wortgleich. Fristpause bei ausstehender Freigabe. Technisch: Feld für Fristbeginn und Pausenzeiten im Deal.

### L7 · Buchpreisbindung
Buch als Gratis-Lead-Magnet, im Rabatt-Bundle oder mit Anrechnung auf Dienstleistungen ist nach BuchPrG sehr wahrscheinlich unzulässig — für Print **und** E-Book.
**Fix:** Lead-Magnet ist der kostenlose Check, nicht das Buch. Workbook bewusst ohne ISBN als Arbeitsmaterial konstruieren. Anwaltlich bestätigen lassen.

### L8 · Umsatzsteuer und Rechnungspflichten bei digitalen Produkten
Buch 7 %, Dienstleistung 19 %, Workbook 19 %. Ein Bundle mit gemischtem Steuersatz braucht eine korrekte Aufteilung. Zusätzlich: GoBD verlangt einen lückenlosen, fortlaufenden Rechnungsnummernkreis — ein Shop-Subsystem, das eigene Nummern vergibt, darf nicht mit dem bestehenden Kreis kollidieren.
**Fix:** Vor Shop-Entwicklung mit dem Steuerberater klären. Keine gemischten Bundles im ersten Schritt.

---

## 🟡 Technische Schuld mit Skalierungswirkung

### L9 · Datenmodell trägt drei Produkte nicht
`product_type` kennt heute `website` und `impuls`. Drei Websprint-Varianten plus digitale Produkte sprengen sowohl das Feld als auch `ProzessFlowV3.jsx`, der auf einen festen 17-Schritt-Ablauf ausgelegt ist.
**Empfehlung:** Schrittdefinition in die Datenbank verlagern, **bevor** das zweite Produkt live geht. Drei parallele Flow-Komponenten sind der Zustand, aus dem man nicht mehr herauskommt.
**Zwei Schritte voraus:** Genau hier entsteht dein wiederkehrender Fehler — Backend kennt drei Produkte, Frontend zeigt zwei, Routing für das dritte fehlt. Deshalb gehört in jeden Umsetzungs-Prompt ein expliziter Verbindungs-Check: DB-Wert → API-Response → Frontend-Route → sichtbares Element.

### L10 · Kein Bestell-Subsystem für digitale Produkte
Workbook und Check PLUS lassen sich heute technisch nicht verkaufen. Es fehlen `orders`, Checkout, signierte Downloads, Rechnungsstellung, Widerrufsbelehrung.
**Empfehlung:** Getrennt von `deals` bauen. Digitale Bestellungen dürfen nicht durch den Projekt-Prozessflow laufen — er bricht beim Deployment-Schritt ab, weil keine Domain existiert.

### L11 · Offene Sicherheitspunkte vor Traffic-Anstieg
SEC-02 (GrapesJS-Lizenzschlüssel in der Git-Historie) und der `gitleaks`-CI-Fehler zu hartkodierten Keys in `projects.py` sind heute unangenehm. Ab dem Moment, in dem eine öffentliche Buch-Landingpage und ein Shop Traffic bringen, sind sie ein anderes Kaliber.
**Empfehlung:** Vor Shop-Launch schließen, nicht danach.

---

## Abarbeitungsreihenfolge

| # | Aufgabe | Aufwand | Blockiert |
|---|---|---|---|
| 1 | `PAGESPEED_API_KEY` auf Render setzen | Minuten | L2 |
| 2 | Score-Schwellen zentralisieren (BE = Quelle, FE liest) | klein | L3, Buch |
| 3 | Referenzmessung 5 Seiten → realistische Garantieschwelle festlegen | klein | Garantietexte |
| 4 | Export-Skript `audit_criteria.py` → Manuskript-Tabellen | mittel | L5, Buch |
| 5 | Anwaltliche Prüfung (Garantien, BuchPrG, Widerruf, AV-Vertrag) | extern | L6, L7, Produkt 03 |
| 6 | Code-Injection in Netlify-Deploy + Verifikation | mittel | L1, Produkt 03 |
| 7 | Entscheidung K1–K6: implementieren oder streichen | Entscheidung | L4, Buch |
| 8 | Datenmodell + datengetriebener Prozessflow | groß | L9, Produkte 01–03 |
| 9 | `orders`-Subsystem | groß | L10, Produkt 05 |
| 10 | SEC-02 + gitleaks | mittel | L11 |

**Schritte 1–3 sind an einem Vormittag machbar und machen Produkt 01 verkaufbar.** Das ist der schnellste Weg zu Umsatz.

---

## Schlussvermerk — 04.09.2026: diese Liste wird nicht mehr eigenständig geführt

**Warum dieser Vermerk hier steht.** Die Produktdatenblätter tragen im Kopf
einen Freigabestatus, der auf die Nummern dieser Liste verweist — „verkaufbar
nach Behebung **L2 und L3**". Zugleich führt `docs/soll-ist-analyse.md` eine
zweite Liste, deren Einträge **L-01 bis L-166** heißen. Zwei Listen mit
derselben Kennung sind keine Formsache: Am 04.09.2026 wurde die Frage „wo
stehen wir mit L2 und L3" am Lagebild beantwortet, wo es **kein L-02 gibt** und
L-03 seit dem 07.08. geschlossen ist. Die Antwort war sauber gemessen und
betraf die falsche Liste.

**Ab hier gilt das Lagebild.** Diese Datei bleibt als Befund vom 23.08.2026
stehen — sie ist der Grund, warum die Produktlinie so aussieht, wie sie
aussieht. Fortgeschrieben wird sie nicht mehr.

**Stand der elf Punkte, am 04.09.2026 am Code nachgemessen statt übernommen:**

| Nr. | Stand | Beleg / Fortsetzung |
|---|---|---|
| L1 · GEO wird nicht ausgeliefert | ✅ geschlossen | Einbau seit L-99; `services/geo_auslieferung.py` prüft nach der Veröffentlichung am lebenden Dienst nach |
| L2 · Garantie nicht messbar | 🟠 **teilweise** | → **L-165**. Der PageSpeed-Schluessel ist produktiv **gesetzt** (am 07.09.2026 an `/health` nachgemessen, Laenge 39) — die Messbarkeit steht. Offen ist die Produktentscheidung aus **K1**: die Zusage auf das zuschneiden, was wirklich geprueft wird, oder die fehlenden Kriterien erheben. |
| L3 · Zwei Standards | ✅ geschlossen | Eine Quelle: `services/audit_katalog.py::LEVELS`; `frontend/src/utils/homepageStandard.js` spiegelt sie mit begründeter Regel |
| L4 · K1–K6 nur im Buch | ✅ geschlossen | `services/audit_industry_map.py`, wirksam im Scoring |
| L5 · Buchtabellen konstruiert | ✅ geschlossen | `scripts/buch-bloecke.py`, mit `--pruefen` als Wächter |
| L6 · Bauzeit ohne Fristbeginn | ✅ **geschlossen** | → **L-166**, am 06.09.2026. Fristbeginn **und** Fristpause liegen in `services/bauzeit.py`; `mitwirkung_stand.vorgelegt_am` haelt den Vorlagezeitpunkt, und Kundenkonto wie Innendienst lesen dieselbe Rechnung. Die Auslegung — Verzoegerung ist, was ueber die fuenf Werktage hinausgeht — hat David am 07.09. bestaetigt. |
| L7 · Buchpreisbindung | 🟠 **offen** | Rechtsfrage, bei David |
| L8 · USt und GoBD | 🟠 **teilweise** | Nummernkreis in `services/rechnungsnummer.py`; gemischte Bündel steuerlich ungeklärt |
| L9 · Datenmodell trägt drei Produkte nicht | ✅ **geschlossen** | → **L-164**. Websprint Start steht seit dem 04.09. im Katalog; dass die Schrittkette das Produkt noch nicht kennt, laeuft getrennt als **L-168**. |
| L10 · Kein Bestell-Subsystem | ✅ geschlossen | Orders-Strecke gebaut, siehe L-100 |
| L11 · Offene Sicherheitspunkte | ✅ geschlossen | GrapesJS siehe L-75; `routers/projects.py` ohne hartkodierte Schlüssel |

> ## Fortgeschrieben am 07.09.2026 — jetzt neun von elf
>
> **L6 und L9 sind geschlossen**, L2 ist von „offen“ auf „teilweise“ gerückt.
> Offen bleiben genau zwei, und **keiner davon ist Programmierarbeit**:
>
> * **L7 · Buchpreisbindung** — Rechtsfrage, bei David.
> * **L8 · USt und GoBD** — der Nummernkreis liegt in
>   `services/rechnungsnummer.py`; die steuerliche Klärung gemischter Bündel
>   gehört zum Steuerberater.
>
> **L2** ist der dritte Rest und ein Zwitter: Gemessen werden kann, entschieden
> ist nicht. Im Lagebild trägt er deshalb die Kennzeichnung `beides`.

**Sieben von elf waren erledigt, ohne dass es jemand eingetragen hatte.** Genau
das ist der Preis einer zweiten Liste: Sie altert unbemerkt, und ein
Verkaufsdokument, das auf sie zeigt, meldet eine Sperre, die es nicht mehr gibt
— oder verschweigt eine, die es noch gibt.

**Was an den Datenblättern zu ändern war, ist am 07.09.2026 geändert:** Der
Freigabestatus nennt jetzt die Lagebild-Nummer statt der alten. Diese Tabelle
bleibt als Übersetzung stehen — wer die alten Nummern im Kopf hat oder sie in
einem älteren Dokument liest, findet hier die Entsprechung.

**Die Lehre dieses Reports in einem Satz:** Eine zweite Liste altert unbemerkt,
und ein Verkaufsdokument, das auf sie zeigt, meldet eine Sperre, die es nicht
mehr gibt — oder verschweigt eine, die es noch gibt. Ab jetzt wird sie im
Lagebild geführt; dieser Report wird nicht mehr fortgeschrieben, er übersetzt
nur noch.
