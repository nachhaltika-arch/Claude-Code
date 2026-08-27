# ENTSCHEIDUNGSPAPIER · KI-Sichtbarkeit — selbst anschließen oder zukaufen

**Anlass:** Das White-Label-Angebot von `findbar.biz/agentur` (SEC GmbH),
zugeschickt am 25.08.2026 mit Lead-Kennung.
**Zu entscheiden:** Wiederverkauf unter eigenem Namen — oder das eigene, zu
großen Teilen fertige Modul anschließen.
**Entscheider:** David.

> **Eine Korrektur vorweg.** Die erste Einschätzung in der Sitzung lautete, bei
> uns existiere „nur die Anbieterschicht", es fehlten Speicherung, Ansicht und
> Bericht. **Das war falsch.** Nachgesehen statt angenommen: Der Messdienst,
> die Speicherung samt Verlauf, ein Endpunkt und vier Testdateien liegen
> vor. Was fehlt, ist kleiner und anderer Art — siehe Abschnitt 3.

---

## 1. Was findbar verkauft

**Wöchentliches Tracking, ob ein Betrieb in KI-Antworten genannt wird.** Score
0–100, Trend, priorisierte Maßnahmen. Vier Systeme: ChatGPT, Perplexity,
Google AI, Claude — gemessen mit **GPT-4o-mini** und **llama-sonar**, also den
kleinen Modellen.

| Endkundentarif | Einführungspreis bis 31.12.2026 | regulär |
|---|---|---|
| Starter — 1 Betrieb, 2 Systeme, 5 To-Dos | **9,90 €/Mo** | 49 € |
| Professional — 1 Betrieb, 4 Systeme | **29,90 €/Mo** | 99 € |
| Multi-Standort — bis 5 Betriebe | **99,90 €/Mo** | 249 € |

**Agenturangebot:** dasselbe Produkt im eigenen Branding, „bis zu 49 € /
Endkunde / Monat", ohne Mindestabnahme und ohne Setup-Gebühr. 14 Tage
kostenlos testbar.

### Der Rechenfehler im Agenturangebot

**Der White-Label-Einkaufspreis liegt über dem laufenden Endkundenpreis
desselben Anbieters.** Wir zahlten bis zu 49 € für einen Kunden, den findbar
nebenan für 29,90 € selbst bedient. Zu Regulärpreisen müssten wir für 99 €
weiterverkaufen — genau der Preis, zu dem der Kunde direkt kauft, nur mit
unserem Logo. **Solange die Einführungspreise laufen, ist die Marge negativ,
und der Direktkanal unterbietet den eigenen Wiederverkäufer.**

Was ich **nicht** prüfen konnte: ob „bis zu 49 €" nach Menge gestaffelt ist,
die Vertragslaufzeit, und die Behauptung, erste Plattform im DACH-Raum zu sein.

### Zwei Beobachtungen zur Methode

* **Die kleinen Modelle.** GPT-4o-mini und llama-sonar erklären den Preis von
  9,90 €. Sie sagen aber auch etwas über die Aussagekraft: Gemessen wird, was
  ein sparsam eingestelltes System antwortet, nicht was der Markt sieht.
* **Die Kernzahl der Startseite steht ohne Quelle da:** „Nur 1,2 % der lokalen
  Betriebe haben gute KI-Sichtbarkeit." Unser eigenes Buch verbietet sich
  genau diese Sorte Prozentzahl (B5.2.5). Wer sie unter unserem Namen
  weiterverkauft, übernimmt sie.

---

## 2. Was das mit unserem Angebot zu tun hat

**Es sind zwei verschiedene Fragen, und das ist der entscheidende Punkt.**

| | Frage | Bei uns |
|---|---|---|
| **findbar** | Werde ich in KI-Antworten **genannt**? | L-58 (b) — angeschlossen fehlt |
| **Homepage Standard** | Kann eine Maschine den Betrieb überhaupt **lesen**? | `se_ki_lesbar`, 3 von 103 Punkten, seit 21.08.2026 gemessen |

Unsere drei Punkte sind die **Voraussetzung** für ihr Produkt: Wer die
KI-Crawler aussperrt, wird nicht genannt. Das ist keine Konkurrenz, sondern
die Stufe davor — und es ist ein Verkaufsargument, kein Nachteil.

**Drei KI-nahe Produkte stehen bei uns blockiert:**

| | Produkt | Preis | Stand |
|---|---|---|---|
| L-58 (b) | KI-Sichtbarkeit messen | kein Preis | gebaut, **nicht angeschlossen** |
| L-99 | GEO-01 Add-on | 1.200 € einmalig | gesperrt: wir prüfen `llms.txt` an fremden Seiten und erzeugen es an unseren nicht |
| L-101 | Pflege-Abos | 79 / 149 € mtl. | keine wiederkehrende Abrechnung, keine Zeiterfassung |

---

## 3. Was bei uns tatsächlich schon steht

Am 25.08.2026 im Code nachgesehen:

| Vorhanden | Umfang |
|---|---|
| Anbieterschicht ChatGPT, Perplexity, Claude | `services/ki_anbieter.py`, 253 Zeilen |
| Messdienst: feste Fragen je Gewerk und Ort, Nennungserkennung in Antwort **und** Quellen | `services/ki_sichtbarkeit.py`, 262 Zeilen |
| Verlauf mit Deckel (50 Einträge) | dito, `verlauf_fortschreiben` |
| Speicherung | `geo_analyses.ki_sichtbarkeit`, `_am`, `_verlauf` (JSONB), migriert |
| Endpunkt | `POST /api/geo/{project_id}/ki-sichtbarkeit` |
| Tests | vier Dateien: Anbieter, Dienst, Endpunkt, Verlauf |
| Werkzeug für den ersten echten Lauf | `tools/ki_sichtbarkeit_probe.py` |
| Terminplaner mit Tagesjobs | `automations/scheduler.py`, Postgres-Jobstore |

**Die Bauart ist bereits die richtige.** Die Fragen sind **fest und nicht von
einem Modell erzeugt** — zwei Läufe sollen dasselbe messen, sonst ist der
Vergleich zwischen gestern und heute keiner, und genau der ist das Produkt.
Ein Anbieter ohne Schlüssel wird als *nicht erhoben* ausgewiesen und
**niemals als Null**: „Perplexity: 0 von 5" bei einem System, das wir nie
gefragt haben, wäre eine Behauptung, die den Betrieb Geld kostet.

### Was fehlt

| # | Lücke | Stand am 25.08.2026 |
|---|---|---|
| 1 | **Schlüssel.** Nie gegen einen echten Dienst gelaufen | 🔴 offen — Beschaffung durch David |
| 2 | **Kein Aufrufer im Frontend** — dieselbe Klasse, die im Lagebild fünfmal steht | ✅ **geschlossen**: Reiter „Nennung" im GEO-Schritt, mit Verlaufstabelle |
| 3 | **Kein Wochenjob** | ✅ **geschlossen**: montags 6 Uhr, nur für laufende Abos, `automations/job_ki_sichtbarkeit.py` |
| 4 | **Google AI fehlt** als vierter Anbieter | ✅ **geschlossen**: `GEMINI_API_KEY`, Interactions API mit Suchwerkzeug, Modell `gemini-3.7-flash` |
| 5 | **Kundenbericht** mit Trend für den Abonnenten | ✅ **geschlossen**: Erstmessung beim Kauf, Ansicht im Kundenportal über den erweiterten Status-Endpunkt |
| 6 | Wiederkehrende Abrechnung | ✅ **existiert bereits** — siehe Korrektur unten |

**Es bleiben die Schlüssel.** Gebaut ist alles.

> **Stand 25.08.2026, abends. Alle sechs Lücken sind zu.** Wir messen dieselben
> vier Systeme wie der Wettbewerb; gefragt wird mit den großen Modellen samt
> Websuche, nicht mit den kleinen. Ein System ohne Schlüssel erscheint überall
> als *nicht erhoben* — nie als Null, und beim Kunden ohne den Namen der
> Umgebungsvariablen.

### Zwei Zusagen, die beim Bauen aufgefallen sind

Die Kundenkarte versprach dem Abonnenten zweierlei, das nicht stimmte:

| Stand bis 25.08. | Wirklichkeit |
|---|---|
| „Ihre Website wird **monatlich** überprüft" | Der Lauf steht wöchentlich im Planer |
| „Den nächsten Report erhalten Sie automatisch **per E-Mail**" | Es gibt keinen solchen Versand — der Monatsbericht kennt die Nennung nicht |

Beides war berichtigt — **und der Bericht ist am selben Tag gebaut worden**
(`automations/bericht_ki_nennung.py`). Er hängt am Wochenlauf, nennt je System
die Trefferzahl und die Richtung gegenüber der Vorwoche, weist nicht abgefragte
Systeme aus und sichert keine Nennung zu. Damit darf die Karte ihn wieder
zusagen; der Test prüft jetzt genau das — **was zugesagt wird, muss gebaut
sein**, in beide Richtungen.

**Was der Bericht bewusst nicht enthält:** die Antworttexte der Modelle. Sie
nennen fremde Betriebe, und der Kunde hat sie nicht bestellt.

---

## 7. Entscheidungen vom 25.08.2026

| Frage | Entscheidung | Folge |
|---|---|---|
| Erster Schlüssel | **OpenAI** | Die Kundenfrage lautet „Werde ich in ChatGPT gefunden?". Die anderen drei kommen später und erscheinen bis dahin als *nicht erhoben* |
| Preismodell | **Ein Preis je Betrieb und Monat**, alle vier Systeme | Keine Anbieterauswahl je Abonnent nötig — die Abrechnung steht damit vollständig |
| Nächster Bauschritt | **E-Mail-Bericht** | ✅ am selben Tag erledigt |

**Damit ist alles gebaut.** Es fehlt der erste echte Lauf — er beantwortet die
letzte offene Frage: den Preis.

> **Korrektur zu Punkt 6.** Die erste Fassung dieses Papiers zählte die
> wiederkehrende Abrechnung als fehlend und verwies auf L-101. **Das trifft
> die Pflege-Abos (ABO-BAS, ABO-PRO), nicht das GEO-Abo.** Für GEO steht sie:
> `routers/geo_payments.py` (477 Zeilen) legt ein Stripe-Abonnement an,
> verarbeitet den Webhook, führt den Status und verschickt eine
> Begrüßungsmail; `GeoAnalysis` trägt `stripe_subscription_id`,
> `subscription_status` und die Periodendaten. Was der Kauf heute auslöst, ist
> die GEO-Analyse samt Dateierzeugung — **nicht** der Nennungslauf. Genau
> diese Verbindung ist der Rest von Punkt 5.

---

## 4. Was ein eigener Lauf kostet

Die Rechengröße steht fest, der Preis je Aufruf nicht:

```
Kosten je Kunde und Monat = 5 Fragen × Anbieter × 4 Wochen × Preis je Aufruf
```

Bei drei Anbietern sind das **60 Aufrufe je Kunde und Monat**. Der Preis je
Aufruf hängt am Modell — und hier liegt eine Entscheidung: Wir fragen heute
mit den großen Modellen samt Websuche, findbar mit den kleinen.

> **Diese Zahl wird gemessen, nicht geschätzt.** `tools/ki_sichtbarkeit_probe.py`
> ist genau dafür gebaut: ein echter Lauf gegen einen Betrieb, mit Rohantwort.
> **Vor der Entscheidung sollte er einmal laufen** — er kostet ein paar Cent
> und beendet das Raten.

---

## 5. Empfehlung: nicht white-labeln, sondern anschließen

Vier Gründe, in dieser Reihenfolge:

1. **Die Marge existiert nicht**, solange der Anbieter direkt zu 29,90 €
   verkauft, was er uns zu bis zu 49 € überlässt.
2. **Ein zugekaufter Tracker wäre ein zweiter Maßstab** neben unserem: ein
   fremder Score 0–100 neben 103 Punkten, ohne veröffentlichte Methode. Das
   ist das Muster „zweite Wahrheit", das dieses Projekt in derselben Woche
   dreimal ausgeräumt hat.
3. **Der Abstand ist drei Tage**, nicht drei Monate. Es geht um Anschließen,
   nicht um Bauen.
4. **Die eigene Methode ist das Verkaufsargument.** Wir haben einen
   veröffentlichten Katalog, ein Buch und einen Selbsttest. Ein Score ohne
   nachlesbare Methode ist genau das, wogegen der Homepage Standard antritt.

### Der ehrliche Gegeneinwand

Zukaufen liefert morgen, Anschließen in drei Tagen **plus** Schlüsselbeschaffung
plus die Abrechnung aus L-101. Wer **jetzt** wiederkehrenden Umsatz braucht,
kann drei Monate wiederverkaufen — dann aber bewusst als Zwischenlösung, mit
Auftragsverarbeitungsvertrag, weil Kundendaten unter unserem Namen bei der
SEC GmbH lägen, und ohne die 1,2-Prozent-Behauptung zu übernehmen.

### Reihenfolge, wenn entschieden wird

```
1. Probelauf mit einem Schlüssel          ← beendet die Kostenfrage   🔴 offen
2. Frontend anschließen                                                ✅ 25.08.
3. Wochenjob im vorhandenen Planer                                     ✅ 25.08.
4. Google AI als vierter Anbieter                                      ✅ 25.08.
5. Erstmessung beim Kauf                                               ✅ 25.08.
6. Ansicht für den Kunden                                              🔴 offen
   ▼
   danach erst: der Preis
```

**Der Probelauf steht weiter zuerst.** Ohne ihn ist der Preis eine Behauptung:
Bei drei Anbietern und drei Fragen sind es neun Aufrufe je Kunde und Woche,
und was einer kostet, weiß erst der erste echte Lauf.

**Was nicht passieren darf:** das Modul an den Score des Homepage Standards zu
hängen. Jeder Lauf kostet Geld; ein kostenloses Audit mit einer Kostenstelle je
Aufruf ist ein anderes Produkt. Diese Entscheidung steht so im Code und bleibt
offen — bis dahin hängt daran kein Kriterium und kein Punkt.

---

## 6. Was offen bleibt

| | Frage | An wen |
|---|---|---|
| 1 | Staffelung, Laufzeit und Kündigungsfrist des Agenturangebots | findbar, falls Weg B |
| 2 | Preis je Aufruf bei unseren Modellen | Probelauf |
| 3 | Preis des eigenen Produkts — Einzelverkauf oder nur im Abo | David |
| 4 | Auftragsverarbeitung bei Wiederverkauf | Anwalt, zu B2 |
