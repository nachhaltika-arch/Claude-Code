# Projekt-Assistent — Anforderungsdokument

> Status: **fachlich geklärt** — alle 16 Anforderungen entschieden, bereit für den Implementierungsplan
> Erstellt: 2026-08-07
> Betrifft: Projektbereich / online fertige Produkte

---

## 1. Ausgangsanforderung (David, 2026-08-07)

> "Ich möchte für die online fertigen Produkte im Projektbereich einen Assistenten
> programmieren, der den Kunden und unsere Mitarbeiter durch den Fragebogen begleitet,
> professionelle Unterstützung bietet und die Durchführung des Projektes begleitet und leitet."

Daraus abgeleitet die drei Kernfunktionen:

1. **Fragebogen-Begleitung** — führt Kunde und Mitarbeiter durch das Briefing
2. **Fachliche Unterstützung** — professionelle Hilfe beim Ausfüllen
3. **Projektbegleitung** — begleitet und leitet die Durchführung

---

## 2. Entschieden — Runde 1: Grundarchitektur

| # | Frage | Entscheidung |
|---|-------|--------------|
| 1.1 | Assistenztyp | **Hybrid: geführter Ablauf + KI-Chat** |
| 1.2 | Fragebogen-Basis | **BriefingWizard, 6 Schritte** (flache Felder) |
| 1.3 | Schreibrecht | **Vorschlagen, Mensch bestätigt** |
| 1.4 | Phasensteuerung | **Assistent schlägt vor, Mitarbeiter gibt frei** |

### 1.1 Assistenztyp — Hybrid

Der Fragebogen bleibt der feste, deterministische Ablauf. Daneben läuft ein KI-Chat,
der den aktuellen Schritt kennt, erklärt, Beispiele gibt und nachhakt.

**Warum:** Der Kunde kann sich nicht verlaufen, bekommt aber echte Hilfe. Vollständigkeit
und Datenqualität hängen nicht am Modell. Baut auf dem vorhandenen `BriefingWizard` auf,
statt ihn zu ersetzen.

**Technische Konsequenz:** Der Chat braucht pro Nachricht den Kontext "welcher Schritt,
welche Felder, welcher Projektstand". Kein Umbau des Wizards nötig — der Assistent wird
als Panel danebengesetzt.

### 1.2 Fragebogen-Basis — BriefingWizard (6 Schritte)

Grundlage sind die flachen `Briefing`-Felder (`gewerk`, `leistungen`, `einzugsgebiet`,
`usp`, `mitbewerber`, `vorbilder`, `farben`, `wunschseiten`, `stil`, `hauptziel`,
`aktionen`, `typischer_kunde`, `haeufige_anfrage`, …).

**Warum:** Aktiv im UI genutzt, hat mit `POST /api/briefings/{lead_id}/suggest-field` und
den `ki-prefill-*`-Endpunkten bereits KI-Vorschläge pro Feld — daran dockt der Assistent an.

**Technische Konsequenz:** Das Legacy-12-Sektionen-JSON-Briefing (`projektrahmen`,
`positionierung`, `zielgruppe`, `wettbewerb`, …) wird vom Assistenten **nicht** bedient
und ist damit perspektivisch Auslaufmodell. Sollte separat entschieden werden.

### 1.3 Schreibrecht — Vorschlagen, Mensch bestätigt

Der Assistent formuliert Antworten vor, der Nutzer übernimmt per Klick oder ändert sie.

**Warum:** Entspricht der vorhandenen `suggest-field`-Logik, ist rechtlich sauber und
verhindert, dass ungeprüfte KI-Inhalte zur Projektgrundlage werden.

**Technische Konsequenz:** Jeder Vorschlag braucht einen sichtbaren Übernehmen-Schritt.
Kein direkter Schreibzugriff des Assistenten auf die `briefings`-Tabelle.

### 1.4 Phasensteuerung — Vorschlag mit menschlicher Freigabe

Der Assistent prüft die 54 Checklistenpunkte, meldet z. B. "Phase 3 ist abschlussreif"
und begründet es. Ausgelöst wird der Wechsel von einem Menschen.

**Warum:** Kontrolle bleibt intern, die Denkarbeit übernimmt der Assistent. Fehler wirken
nicht direkt beim Kunden. Vermeidet Kollision mit dem bestehenden
`automations/scheduler.py`, der heute schon tägliche Phasen- und Material-Checks fährt.

**Technische Konsequenz:** Der Assistent braucht Lesezugriff auf `ProjectChecklist`
(54 Items, Phasen 1–7) und `Project.status`, aber keinen Schreibzugriff. Vorschläge
brauchen eine eigene Ablage plus Freigabe-Aktion im UI.

---

## 3. Entschieden — Runde 2: Reichweite und Verhalten

| # | Frage | Entscheidung |
|---|-------|--------------|
| 2.1 | Zielgruppen | **Ein Assistent, zwei Modi** (Kunde / Mitarbeiter) |
| 2.2 | Produktbezug | **Alle Website-Projekte** mit Briefing |
| 2.3 | Proaktivität | **Proaktiv in der App, keine eigenen E-Mails** |
| 2.4 | MVP-Schnitt | **Fragebogen-Begleitung zuerst**, Projektbegleitung als Ausbau 2 |

### 2.1 Zielgruppen — ein Assistent, zwei Modi

Gleiche Technik; Tonalität, Datenzugriff und Vorschläge hängen an der Rolle des
angemeldeten Nutzers. Kunde bekommt Erklärung und Beispiele, Mitarbeiter Effizienz
und interne Kennzahlen.

**Warum:** Ein System pflegen statt zwei. Die Rollenlogik (`kunde`, `admin`, `auditor`,
`superadmin`) ist in KAS ohnehin vorhanden.

**Technische Konsequenz:** Der Modus wird serverseitig aus `User.role` abgeleitet, nicht
vom Client mitgegeben. Systemprompt und erlaubter Datenumfang werden pro Modus
konfiguriert. Randnotiz: `auditor` ist backendseitig aktuell nicht abgegrenzt
(`require_auditor` ist definiert, aber an keiner Route eingehängt) — für den
Mitarbeitermodus muss geklärt werden, ob Auditoren dazugehören.

### 2.2 Produktbezug — alle Website-Projekte

Jedes Projekt mit Briefing bekommt den Assistenten, unabhängig davon ob online gekauft
oder persönlich verkauft.

**Warum:** Der Fragebogen ist in beiden Fällen derselbe. Eine Sonderlogik nach Kaufweg
würde nur Komplexität erzeugen, ohne fachlichen Unterschied.

**Technische Konsequenz:** Keine Herkunftsmarkierung am Projekt nötig, kein Feature-Flag
pro Produkt. Einstiegspunkt ist schlicht: Projekt existiert + Briefing existiert.

### 2.3 Proaktivität — sichtbar in der App, kein eigener Mailversand

Der Assistent meldet sich im Portal und im Wizard von selbst ("Ihnen fehlen noch Fotos",
"dieses Feld ist zu unkonkret"), verschickt aber keine eigenen E-Mails.

**Warum:** Keine doppelten Benachrichtigungen und kein Spam-Risiko. E-Mails bleiben
ausschließlich beim bestehenden `automations/scheduler.py`.

**Technische Konsequenz:** Klare Abgrenzung zum Scheduler ist Teil der Umsetzung. Die
proaktiven Hinweise brauchen einen Auslöser (Feld verlassen, Schritt gewechselt, Portal
geöffnet) und eine Ablage, damit derselbe Hinweis nicht mehrfach erscheint.

### 2.4 MVP-Schnitt — Fragebogen zuerst

**Ausbau 1 (MVP):** Chat, Vorschläge und Qualitätsprüfung im Briefing — für Kunde und
Mitarbeiter.
**Ausbau 2:** Projektbegleitung, Phasenreife-Bewertung, Statuserklärung.

**Warum:** Klar abgrenzbar, in überschaubarer Zeit produktiv einsetzbar und sofort an der
Abschlussquote des Briefings messbar.

**Technische Konsequenz:** Der Lesezugriff auf `ProjectChecklist` und `Project.status`
(Entscheidung 1.4) wird erst in Ausbau 2 gebraucht. Das Datenmodell sollte trotzdem von
Anfang an projektbezogen sein, damit Ausbau 2 keine Migration erzwingt.

---

## 4. Entschieden — Runde 3: Oberfläche und Datenzugriff

| # | Frage | Entscheidung |
|---|-------|--------------|
| 3.1 | Oberfläche | **Panel im Wizard + Widget im Kundenportal** |
| 3.2 | Gesprächsverlauf | **Eigener Verlauf mit Eskalationsknopf** |
| 3.3 | Wissensbasis | **Projektdaten + kuratierte Fachregeln** (kein RAG) |
| 3.4 | Sichtbarkeit | **Freigabeliste (Whitelist) pro Modus** |

### 3.1 Oberfläche — zwei Einbauorte

Im Briefing ein fester Bereich neben den Feldern, im Kundenportal ein aufklappbares
Widget auf jeder Seite.

**Warum:** Der Assistent ist dort, wo der Nutzer ohnehin arbeitet — kein Extra-Klick,
kein Kontextverlust zum aktiven Feld.

**Technische Konsequenz:** Eine gemeinsame Chat-Komponente, zwei Einbindungen.
Sie muss den aktiven Schritt bzw. das fokussierte Feld als Kontext mitgeben können.
Das Portal wird überwiegend mobil genutzt — das Widget muss auf kleinen Bildschirmen
vollwertig bedienbar sein.

### 3.2 Gesprächsverlauf — eigene Ablage, Eskalation auf Knopfdruck

Assistentengespräche liegen in einer eigenen Tabelle. Kommt der Assistent nicht weiter,
erzeugt ein Klick daraus eine echte Nachricht an das Team, inklusive
Gesprächszusammenfassung.

**Warum:** Trennt unverbindliche Hilfestellung von verbindlicher Kommunikation. Euer
Posteingang füllt sich nicht mit KI-Nachrichten, der Verlauf bleibt trotzdem
nachvollziehbar — auch für den Nachweis, was der Assistent geraten hat.

**Technische Konsequenz:** Neue Tabellen für Konversation und Nachrichten, projekt- bzw.
leadbezogen. `Message` bleibt unverändert bei `sender_role` = `admin | kunde`; die
Eskalation schreibt einen normalen Eintrag mit zusammengefasstem Kontext.

### 3.3 Wissensbasis — Projektdaten plus Regelwerk

Der Assistent sieht Briefing, Auditergebnis und Projektstand. Dazu kommt ein gepflegtes
Regelwerk aus `docs/conversion-spec-shk.md`: gute vs. schlechte Antworten,
Branchenbeispiele aus Heizung, Sanitär und Elektrik.

**Warum:** Präzise und prüfbar, ohne Suchinfrastruktur. Trifft eure Qualitätslatte,
weil die Bewertungsmaßstäbe explizit sind statt dem Modell überlassen.

**Technische Konsequenz:** Das Regelwerk wird versioniert im Repo gepflegt, nicht in der
Datenbank. Keine Vektordatenbank, kein Index. Fachliteratur und Academy-Inhalte bleiben
bewusst außen vor — nachrüstbar, falls sich das Regelwerk als zu dünn erweist.

### 3.4 Sichtbarkeit — Whitelist pro Modus

Für jeden Modus ist explizit definiert, welche Felder überhaupt in den Kontext geladen
werden. Alles andere erreicht das Modell nie.

**Warum:** Marge, Stundensatz, KI-Kosten, Scope-Creep-Zähler und interne Notizen hängen
am selben `Project`-Datensatz. Nur eine Freigabeliste verhindert zuverlässig, dass sie
in einer Kundenantwort auftauchen — eine Prompt-Anweisung ist keine Grenze.

**Technische Konsequenz:** Der Kontextaufbau erfolgt über eine explizite Feldliste je
Modus. Neue Felder am Projekt sind damit standardmäßig unsichtbar, bis sie bewusst
freigegeben werden.

---

## 5. Entschieden — Runde 4: Betrieb und Erfolgsmessung

| # | Frage | Entscheidung |
|---|-------|--------------|
| 4.1 | Kostenrahmen | **Budget pro Projekt + Tageslimit pro Nutzer** |
| 4.2 | Übergabe an Menschen | **Automatisch anbieten + jederzeit manueller Knopf** |
| 4.3 | Erfolgskriterium | **Abschlussquote + Briefing-Qualität** |
| 4.4 | Tonalität | **Sie-Form, klar und handwerksnah** |

### 4.1 Kostenrahmen — zwei Grenzen

Ein Budget je Projekt, orientiert an den 50 € KI-Kosten, die in `Project.ai_tool_costs`
bereits im Margenmodell kalkuliert sind. Dazu eine Obergrenze pro Nutzer und Tag. Bei
Erreichen erscheint ein freundlicher Hinweis, kein Fehler.

**Warum:** Schützt die Marge pro Projekt und verhindert Missbrauch durch einen einzelnen
Nutzer.

**Technische Konsequenz:** Verbrauch muss pro Anfrage erfasst und dem Projekt zugeordnet
werden. Da es im Backend bislang **kein** Rate-Limiting gibt, wird die Zählung Teil dieses
Features. Die Grenzwerte gehören in die Konfiguration, nicht in den Code.

### 4.2 Übergabe an Menschen — angeboten und jederzeit erreichbar

Nach zwei erfolglosen Anläufen oder bei erkennbarem Ärger bietet der Assistent die
Übergabe von selbst an. Zusätzlich ist der Knopf permanent sichtbar.

**Warum:** Der Kunde landet nie in einer Sackgasse, ohne dass jede heikle Frage sofort
weitergereicht wird.

**Technische Konsequenz:** Nutzt den Eskalationsweg aus 3.2 — die Übergabe erzeugt eine
`Message` mit Gesprächszusammenfassung. "Erfolglos" und "Ärger" brauchen eine definierte,
nachvollziehbare Erkennungsregel.

### 4.3 Erfolgskriterium — Abschluss und Qualität

Gemessen wird, wie viele Kunden das Briefing zu Ende führen und wie gut die Antworten
gemessen am Regelwerk aus 3.3 sind.

**Warum:** Beides ist automatisch messbar und trifft den Zweck genau: verwertbare
Projektgrundlagen ohne Rückfragen.

**Technische Konsequenz:** Ein Vorher-Wert sollte vor dem Start erhoben werden, sonst
fehlt die Vergleichsbasis. Die Qualitätsbewertung fällt als Nebenprodukt der
Feldprüfung ohnehin an und kann gespeichert werden.

### 4.4 Tonalität — Sie, klar, handwerksnah

Höfliche Sie-Form, kurze Sätze, keine Marketing- oder Technikfloskeln, Beispiele aus
Heizung, Sanitär und Elektrik.

**Warum:** Passt zur Zielgruppe der Phase 1 und zur bestehenden Ansprache im Portal.

**Technische Konsequenz:** Feste Vorgabe im Systemprompt, kein Feld am Lead und keine
Umschaltung pro Kunde.

---

## 6. Offene technische Detailfragen

Nicht mehr fachlich zu entscheiden, sondern im Implementierungsplan vorzuschlagen:

- Modellwahl und Kostenprofil je Anwendungsfall (Feldvorschlag vs. Chat vs.
  Qualitätsbewertung — nicht jeder Fall braucht dasselbe Modell)
- Antwortdarstellung: streamend oder als Ganzes
- Datenmodell: Tabellen- und Feldnamen für Konversation, Nachrichten, Verbrauch,
  ausgeblendete Hinweise
- Zuschnitt der neuen Endpunkte und ihre Rollenabsicherung
- Konkrete Auslöser für proaktive Hinweise (Feld verlassen, Schritt gewechselt,
  Portal geöffnet)
- Testkonzept — im Repo existieren bislang praktisch keine Tests

---

## 7. Nächste Schritte

1. Implementierungsplan auf Basis dieses Dokuments (Datenmodell, Endpunkte,
   Komponenten, Reihenfolge, Aufwand)
2. Regelwerk aus `docs/conversion-spec-shk.md` in eine für den Assistenten nutzbare
   Form bringen (gute/schlechte Beispielantworten je Briefing-Feld)
3. Ausgangswerte messen: heutige Abschlussquote des Briefings als Vergleichsbasis
4. Ausbau 1 umsetzen, produktiv mit einem echten Kunden erproben
5. Ausbau 2 (Projektbegleitung) nach Auswertung von Ausbau 1

Schritt 1 und 2 sind erledigt, Schritt 4 zur Hälfte — siehe Abschnitt 9.

---

## 9. Gebaut — Stand 2026-08-13

Ausbau 1 ist vollständig gebaut und liegt auf `staging`. Was hier steht, ist am
Code nachgeprüft, nicht aus dem Plan abgeschrieben.

### 9.1 Die Teile

| Teil | Ort | Was er entscheidet |
|---|---|---|
| Sichtbarkeit | `backend/services/assistant_context.py` | Erlaubnisliste je Modus. Nicht der Prompt entscheidet, was der Assistent sieht, sondern der Kontextbau — was nicht in der Liste steht, erreicht das Modell nie (Entscheidung 3.4). Unbekannte Rolle ⇒ Kundenmodus. |
| Regelwerk | `backend/services/assistant_rules.py` | Neun Briefing-Felder mit Frage, Begründung, Mindestlänge, gutem und schlechtem Beispiel. `pruefe_antwort()` urteilt ohne Modellaufruf. |
| Kostenrahmen | `backend/services/assistant_budget.py` | 15 € je Projekt (`ASSISTENT_BUDGET_PROJEKT_EURO`), 60 Anfragen je Nutzer und Tag, Warnung ab 80 % (Entscheidung 4.1). |
| Ablage | `AssistantConversation`, `AssistantMessage` in `database.py` | Eigener Verlauf mit Tokenzahlen und Kosten je Nachricht — projektbezogen von Anfang an, damit Ausbau 2 keine Migration erzwingt. |
| Endpunkte | `backend/routers/assistant.py` | `POST /chat`, `GET /conversations/{id}`, `POST /field-check`, `POST /conversations/{id}/escalate`, `GET /limits`. Modell: `claude-sonnet-4-6`. |
| Oberfläche | `frontend/src/components/AssistentPanel.jsx` | Eine Komponente, zwei Einbauorte (Entscheidung 3.1): Spalte neben den Briefing-Feldern, aufklappbares Widget auf schmalen Schirmen und im Kundenportal. |

Tests: 77 im Backend (Kontext, Regelwerk, Budget, API), 11 im Frontend.

### 9.2 Zwei Entscheidungen, die beim Bauen entstanden sind

**Der Vorschlag ist maschinenlesbar.** Das Modell setzt den übernehmbaren Teil
seiner Antwort in eine letzte Zeile `VORSCHLAG: …`; `trenne_vorschlag()` trennt
ihn ab, gespeichert wird nur die Erklärung, ausgeliefert werden beide getrennt.
Ohne das müsste der Kunde den Rat von Hand abschreiben — Entscheidung 1.3 wäre
formal erfüllt und praktisch wertlos.

**Übernehmen hängt an, statt zu ersetzen.** Ein Klick darf niemandem die eigenen
Sätze löschen (`utils/assistentUebernahme.js`).

### 9.3 Was der Browser-Durchlauf gefunden hat

Drei Fehler, die keine Testsuite gezeigt hätte (Commit `226420c`):

- Im Kundenportal **verschwand der Vorschlagsteil der Antwort** — er wurde vom
  Text abgetrennt und dann nur zusammen mit dem Übernehmen-Knopf gezeigt, den es
  dort nicht gibt. Jetzt erscheint er als abgesetzter Block.
- Eskalation ohne Text im Eingabefeld schickte **„Anliegen: (ohne Text)"** ans
  Team. Jetzt zählt die zuletzt gestellte Frage.
- Widget und Support-Chat **stritten um dieselbe Bildschirmecke**; die
  Support-Blase verdeckte den Weg zum Menschen.

### 9.4 Offen

- **Der Assistent hat noch nie mit dem echten Modell gesprochen.** Der
  Browser-Durchlauf lief gegen eine feste Antwort. Ungeprüft ist damit: ob das
  Modell die `VORSCHLAG:`-Konvention zuverlässig einhält, ob die Antworten
  fachlich taugen und was ein Gespräch wirklich kostet. Der Schlüssel dafür liegt
  lokal in `backend/.env.save`.
- Ausgangswerte für Erfolgskriterium 4.3 (heutige Abschlussquote) sind nicht
  gemessen — ohne sie lässt sich später kein Vorher/Nachher zeigen.
- Ausbau 2 (Projektbegleitung, Phasenreife) ist unberührt.
- Der eskalierte Verlauf landet im Team-Postfach (`Message`), nicht im
  Nachrichten-Faden des Portals (`portal_messages`). Das sind zwei getrennte
  Systeme; ob sie zusammengehören, ist offen.

---

## 8. Bestehender Unterbau (Rechercheergebnis)

Worauf der Assistent aufsetzen kann — vorhanden und produktiv:

| Baustein | Ort | Relevanz |
|---|---|---|
| Briefing-Wizard, 6 Schritte | `frontend/src/components/BriefingWizard.jsx` | Ablauf, in den der Assistent eingebettet wird |
| KI-Feldvorschläge | `backend/routers/briefings.py:290` (`suggest-field`) | Muster für 1.3, direkt wiederverwendbar |
| KI-Prefill SEO/Ziele/Funktionen | `backend/routers/briefings.py:454-658` | Bestehende Prefill-Logik |
| 7-Phasen-Modell | `Project.status` (`phase_1`…`phase_7`) | Grundlage der Projektbegleitung |
| 54-Punkte-Checkliste | `ProjectChecklist`, `seed_checklists.py` | Datenbasis für Phasenreife-Bewertung |
| Nachrichten Kunde ↔ Admin | `backend/routers/messages.py`, `Message`-Modell | Möglicher Kanal (kennt bisher nur `admin`/`kunde`) |
| Kundenportal | `backend/routers/portal.py`, `pages/KundenPortal.jsx` | Kundenseitige Oberfläche |
| 5 KI-Agenten | `backend/agents/` | Vorhandenes Muster für Claude-Aufrufe |
| Automatisierungen | `backend/automations/scheduler.py` | Läuft heute schon — Abgrenzung nötig |
| Produkte | `backend/routers/products.py`, `pages/ProductManager.jsx` | Definiert "online fertige Produkte" |
