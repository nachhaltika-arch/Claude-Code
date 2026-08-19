# Wie HubSpot CRM, Vertrieb, Marketing, Content und Service darstellt

> Audit am 2026-08-19 im laufenden Konto (`Silva Viridis GmbH`, EU1, Free-Tarif,
> 4.920 Kontakte). Gegenstand ist die **Darstellung** — Navigation,
> Seitenaufbau, Feldmodell —, nicht der Funktionsumfang.
>
> Was gesperrt war (Kampagnen, Leadscoring, Social, SEO, Marketing-Analytics),
> ist über die Verkaufsseiten trotzdem lesbar: Die erklären das Konzept, und
> die Funktionsmatrix nennt die Grenzwerte. Der Trial-Knopf wurde **nicht**
> gedrückt.

---

## 1. Die Grammatik der Navigation — überall dieselbe

Oberste Ebene, links:

**Hubs:** CRM · Marketing · Content · Sales · Umsatz · Service
**Quer dazu:** Datenmanagement · Agents · Automatisierung · Berichterstattung ·
Entwicklung

Und jeder Hub ist innen **gleich gebaut** — drei Blöcke, durch Trennlinien
geschieden:

| Block | CRM | Marketing | Content | Sales | Service |
|---|---|---|---|---|---|
| **1. Objekte / Cockpit** | Kontakte, Unternehmen, Deals, Tickets, Produkte, Bestellungen | AEO, SEO | Website-Seiten, Landingpages, Blog, Videos, Podcasts, Fallstudien, Einbettungen | Sales-Workspace | Helpdesk, Customer Success |
| **2. Werkzeuge / Tun** | Segmente, Posteingang, Anrufe, Meetings, Aufgaben, Leitfäden, Vorlagen, Snippets | Kampagnen, E-Mail, Social Media, Werbeanzeigen, Events, Formulare, Kaufabsicht, Leadscoring | Content-Aufbereitung, Zugriffsberechtigungen, Design-Manager | Prospecting Agent, Dokumente, Meeting-Planer, Sequenzen, Aktivitätenfeed | Customer Agent, Chatflows, Wissensdatenbank, Kundenportal |
| **3. Auswertung** | — | Marketing-Analytics, Marke | — | Prognosen, Sales-Analytics | Feedbackumfragen, Service-Analytics |

**Das ist die eigentliche Lehre.** Nicht „welche Punkte gibt es", sondern:
*Womit arbeite ich* → *was tue ich damit* → *was kam dabei heraus*. Jeder Hub
endet in seiner eigenen Auswertung. Wer die Reihenfolge kennt, findet sich in
einem fremden Hub sofort zurecht.

Unser Menü ([[ux_methode_krug]], `utils/menue.js`) gruppiert nach Themen
(Akquise, Betreuung …), aber **ohne diese innere Reihenfolge**. Objekte,
Werkzeuge und Auswertungen stehen gemischt.

**Empfehlung:** Die Dreiteilung als Ordnungsregel je Gruppe übernehmen. Das
ist Umsortieren, kein Umbauen.

## 2. Die Datensatzseite: drei Spalten mit fester Bedeutung

Der Kontakt-Datensatz ist der Kern, und er ist immer gleich aufgebaut:

```
┌── WER IST DAS ────┬── WAS IST PASSIERT ────┬── WOMIT HÄNGT ES ZUSAMMEN ──┐
│ Name, Mail, Firma │ Datenhighlights        │ KI-Zusammenfassung          │
│                   │ (konfigurierbar)       │ Unternehmen (1) [Primär]    │
│ ▸ Notiz  ▸ E-Mail │                        │ Deals (0)                   │
│ ▸ Anruf  ▸ Aufgabe│ Kürzliche Aktivitäten  │ Angebote (0)                │
│ ▸ Meeting ▸ Mehr  │ (Zeitstrahl, filterbar)│ Tickets (0)                 │
│                   │                        │                             │
│ Eigenschaften     │ Zugeordnete Objekte    │ je Karte: „+ Hinzufügen"    │
│ Abonnements       │                        │                             │
│ Website-Aktivität │                        │                             │
└───────────────────┴────────────────────────┴─────────────────────────────┘
```

Fünf Dinge daran sind übernehmbar:

1. **Die Aktionsleiste steht direkt unter der Identität** — Notiz, E-Mail,
   Anruf, Aufgabe, Meeting. Fünf Verben, keine Menüsuche.
2. **Der Verlauf ist immer sichtbar**, nicht hinter einem Reiter. Unsere
   Betriebsseite (`pages/LeadProfile.jsx`) ist **reiterbasiert** — Übersicht,
   Kontakt, Audits, Deals, Nachrichten, E-Mails, Briefing, Angebot, Design.
   Wer wissen will „was ist zuletzt passiert", muss erst den richtigen Reiter
   raten. Bei HubSpot ist das die Mittelspalte, immer.
3. **Leere Zustände erklären ihren Zweck** statt „Keine Einträge":
   „Verfolgen Sie die mit diesem Datensatz verbundenen Opportunitys."
4. **Zuordnungen tragen Rolle und Rang** — „Primär", dazu
   „Zuordnungslabel hinzufügen".
5. **Anpassen** — die Mittelspalte ist vom Nutzer konfigurierbar, samt einer
   Karte „Datenhighlights", die die drei wichtigsten Felder nach oben zieht.

## 3. Drei Felder, die unserem Lead-Modell fehlen

Am geöffneten Datensatz abgelesen:

| HubSpot-Feld | Was es leistet | Bei uns |
|---|---|---|
| **Lifecycle-Phase** (`Lead`) | Wo im Trichter — unabhängig vom Bearbeitungsstand | — |
| **Leadstatus** | Bearbeitungsstand innerhalb der Phase | `status` macht **beides** gleichzeitig |
| **Datensatzquelle** (`Formulare`) | Wie der Datensatz entstand, als **Feld** | `lead_source` als Freitext |
| **Für Kontakt zuständiger Mitarbeiter** | Verantwortung, explizit | — |
| **Rechtliche Grundlage für die Verarbeitung** | DSGVO **im Datenmodell** | separate Nachweise |

Die Trennung **Phase ≠ Status** ist der wichtigste Punkt: Unser `status`
(`new`, …) beantwortet zwei Fragen mit einem Wert, und deshalb wird er für
beides missbraucht.

Dazu im Verlauf die **Herkunft als Ereignis**: „Dieses Objekt wurde über
Organische Suche durch *Unknown keywords (SSL) (GOOGLE)* erstellt." Nicht nur
*dass* der Lead da ist, sondern *woher*.

## 4. Listen: gespeicherte Ansichten sind Reiter

Die Kontaktliste zeigt oben **Ansichten als Reiter** — „Alle Kontakte",
„Meine Kontakte", „Nicht zugewiesene Kontakte", dazu
„+ Ansicht hinzufügen (3/5)" mit sichtbarem Kontingent. Darunter erst die
Filterleiste, Erweiterte Filter, Export, Spalten bearbeiten, Listen-/
Kachelumschalter, Rückgängig und Ansicht speichern.

Der Unterschied zu uns: Wir haben **Filter**, aber keine **benannten
Ansichten**. Ein Filter ist flüchtig, eine Ansicht ist eine Arbeitsweise mit
Namen — „Nicht zugewiesen" ist eine Aufgabe, kein Filterzustand.

Und: **„Datenqualität" ist ein eigener Ort** in der Kopfzeile der Liste.

## 5. Marketing im Einzelnen

### AEO — der Punkt, der uns unmittelbar betrifft

Eigener Menüpunkt, **BETA**, und bezeichnenderweise **über** SEO, mit beiden
zusammen im ersten Block. Adresse: `/ai-visibility/`.

> „KI spricht über Ihre Marke. Jetzt können Sie zuhören."
> — Prüfen, wie das Unternehmen in **ChatGPT, Perplexity und Gemini** erscheint
> — **Prompts nachverfolgen** für Wettbewerbsvergleich
> — Content-Agent liefert AEO-optimierte Empfehlungen

Eingabe ist genau zweierlei: **Marke + Domain**.

Das Mengenmodell steht in der Funktionsmatrix: **25 Prompts, täglich über
3 Engines, 2.500 Antworten pro Monat.** Also: Prompt × Engine × Tag = Antwort,
und die Antwort ist die abgerechnete Einheit.

**Für uns:** Das ist ein **neues Audit-Kriterium**. Unsere Qualitätslatte
([[quality_bar_kas]]) ist „technisch + SEO + SEA + Conversion perfekt" — die
KI-Sichtbarkeit fehlt darin, und sie ist bei einem SHK-Betrieb heute die Frage
„empfiehlt ChatGPT mich, wenn jemand nach *Wärmepumpe + Ort* fragt?". Eingabe
hätten wir bereits: Betriebsname und Domain stehen im Lead.

### Kampagne — ein Dachobjekt über allen Assets

Gesperrt, aber die Erklärung ist eindeutig: Kampagnenmanagement „führt alle
Ihre Elemente zusammen, verfolgt nach, **welche Kontakte** Ihre Kampagne
erreicht". Eine Kampagne hat **Verwalten · Kalender · Aufgaben** und misst
Sitzungen, neue Kontakte, beeinflusste Kontakte, abgeschlossene Deals und
attributierten Umsatz.

Es ist also kein Ordner, sondern eine **Klammer mit Attribution**: E-Mail,
Landingpage, Anzeige, Social-Beitrag und Formular gehören zu *einer* Kampagne,
und am Ende steht, welcher Umsatz daraus kam.

Bei uns gibt es Leads, Audits und Projekte — aber **kein Objekt, das eine
Maßnahme klammert**. Das ist der größte konzeptionelle Unterschied im
Marketing-Teil.

### Die übrigen Punkte, kurz

- **Leadscoring:** „Bis zu 5 Scores" — also **mehrere benannte Bewertungen**
  nebeneinander (etwa Passung und Kaufbereitschaft getrennt), nicht eine Zahl.
  Wir haben `analysis_score` und `geo_score` — faktisch schon zwei Scores,
  aber ohne gemeinsames Modell.
- **Formulare** stehen bei den *Werkzeugen*, nicht bei Content — ein Formular
  ist eine Marketing-Handlung, keine Seite. Dazu „unbegrenzte einfache
  Workflows **pro Formular**": An jedem Formular hängt seine Automatik.
- **Kaufabsicht** (Buying Intent) als eigener Punkt — anonyme Besucher werden
  zu einem Signal, bevor sie ein Formular ausfüllen.
- **Events** als eigene Objektart neben E-Mail und Ads.
- **Werbeanzeigen:** Retargeting-Zielgruppen und bis zu 50 mit dem Werbekonto
  synchronisierte **Conversion-Events** — die Rückmeldung an die Plattform ist
  Teil des Produkts.
- **Segmente** doppelt geführt: **aktiv** (regelbasiert, aktualisiert sich) vs.
  **statisch** (eingefroren). Unsere Filter sind immer „aktiv"; für einen
  Versandnachweis braucht es die eingefrorene Variante.
- **Marke** als eigener Menüpunkt unter Marketing — das Markenprofil ist ein
  gepflegtes Objekt, nicht eine PDF im Laufwerk.

## 6. Reihenfolge, wenn wir etwas davon übernehmen

1. **Lifecycle-Phase von Leadstatus trennen** — ein Feld, das zwei Fragen
   beantwortet, beantwortet keine richtig. Kleinster Eingriff, größte Klärung
2. **Der Verlauf gehört auf die Seite, nicht in einen Reiter** — die
   Betriebsseite auf drei Spalten umstellen, Aktionsleiste unter die Identität
3. **Benannte Ansichten** statt bloßer Filter in der Betriebsliste
4. **Datensatzquelle als Feld + Herkunft als Ereignis im Verlauf**
5. **KI-Sichtbarkeit (AEO) als neues Audit-Kriterium** — eigener Abschnitt im
   Bericht, Eingabe Betriebsname + Domain, Messgröße Nennungen je Prompt
6. *Später:* ein Kampagnen-Objekt, das Maßnahmen klammert und Umsatz attribuiert
7. *Später:* aktive und statische Segmente unterscheiden

Punkte 1, 3 und 4 sind je unter einem Tag. Punkt 2 ist ein Seiten-Umbau.
Punkt 5 ist ein Produktentscheid.
