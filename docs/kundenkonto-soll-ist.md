# Das Kundenkonto — was der Kunde verwalten können müsste, und was es gibt

> **Zweck.** Vor dem Bau eines Dashboards die Frage beantworten, die darunter
> liegt: Wofür ist dieses Konto da? Heute ist es eine Sammlung gewachsener
> Blöcke; die Frage, welche davon der Kunde **braucht**, ist nie gestellt
> worden.
>
> **Stand:** 2026-09-04 · **Gemessen**, nicht geschätzt: Menüpunkte und Routen
> am laufenden lokalen Werkzeug abgegriffen, die Soll-Seite aus den
> Produktdatenblättern und dem Angebotsbaukasten gelesen.

---

## 1 · Was der Kunde heute vorfindet

Acht Menüpunkte. Dahinter liegen sieben Seiten und eine Weiche.

| Menüpunkt | Seite | Was er dort tun kann |
|---|---|---|
| Dashboard | `CustomerDashboard` | Projektstatus lesen, Mitwirkung eintragen, Abo/Rechnungen sehen, Nachrichten schreiben |
| Meine Daten | `MeineDaten` | Stammdaten des eigenen Betriebs pflegen |
| Mein Briefing | `MeinBriefing` | Briefing ausfüllen |
| Freigaben | `Freigaben` | Entwürfe freigeben |
| Support | `SupportTickets` | Anfrage stellen, Status verfolgen |
| Rechnungen | `MeineRechnungen` | Rechnungen einsehen |
| Akademie | `Academy` | Kurse ansehen |
| Einstellungen | `Settings` | Konto, Kennwort, Benachrichtigungen |

**Dazu seit heute:** die Mitwirkungsliste mit Fristwirkung und der
Zahlungsblock (Abo, Zahlungsart über das Billing-Portal, Rechnungen).

---

## 2 · Was er können müsste

Die Soll-Seite ist keine Meinung. Sie steht in zwei Dokumenten, die der Kunde
unterschreibt.

### 2.1 · Aus dem Leistungsverzeichnis der Pflege-Abos

Zwölf Positionen, für die er **monatlich zahlt** — 79 € (BAS) bzw. 149 € (PRO).

| Pos. | Leistung | Im Konto? |
|---|---|---|
| 1 | Hosting, SSL, Domainverwaltung | ✗ nirgends sichtbar |
| 2 | Sicherheits- und Systemaktualisierungen | ✗ |
| 3 | Tägliche Sicherung, **Rücksicherung auf Anforderung** | ✗ kein Weg, sie anzufordern |
| 4 | Verfügbarkeitsüberwachung mit Störungsmeldung | ✗ |
| 5/8 | **Inhaltsänderungen bis 30 bzw. 90 Minuten je Monat** | ✗ kein Weg, sie anzufordern; kein Zähler |
| 6/11 | Störungsbehebung, Reaktion in 1 Werktag bzw. 4 Stunden | ◐ Support gibt es, die Zusage steht nirgends |
| 7/10 | Re-Audit, jährlich bzw. quartalsweise | ✗ läuft im Hintergrund, kein Ergebnis im Konto |
| 9 | **Monatlicher Leistungsbericht** (PRO) | ✗ wird versendet, liegt nicht im Konto |
| 12 | Eine neue Unterseite pro Jahr (PRO) | ✗ kein Weg, sie abzurufen |

> **Der schwerste Befund steht in dieser Tabelle, nicht darunter.** Von zwölf
> bezahlten Positionen ist **keine einzige** im Konto abrufbar. Der Kunde zahlt
> monatlich und sieht dafür nichts — weder was er bekommt, noch wie viel er
> davon schon genutzt hat, noch wie er es anfordert. Für die
> Inhaltsänderungen ist das besonders scharf: „bis 90 Minuten je Monat" ist ein
> Guthaben, und ein Guthaben ohne Kontostand wird entweder nicht genutzt oder
> überzogen. Beides kostet — den Kunden Vertrauen, uns Geld.

### 2.2 · Aus dem Mitwirkungskatalog

| | Im Konto? |
|---|---|
| Sehen, was von ihm gebraucht wird | ✓ seit heute |
| Eintragen, was er geliefert hat | ✓ seit heute |
| Sehen, was das für den Termin heißt | ✓ seit heute |
| Bauplan und Texte freigeben (M7/M8) mit Fünf-Tage-Frist | ◐ „Freigaben" gibt es, die Frist steht nicht dabei |

### 2.3 · Aus dem Vertrag und dem Gesetz

| | Im Konto? |
|---|---|
| Zahlungsart ändern, Abo kündigen | ✓ seit heute, über das Billing-Portal |
| Rechnungen einsehen | ✓ |
| **Auskunft über die eigenen Daten** (Art. 15 DSGVO) | ✗ |
| **Löschung verlangen** (Art. 17 DSGVO) | ✗ |
| **Kollegen Zugang geben** | ✗ die Routen gibt es, sie verlangen `manage_users` — also Innendienst |
| Vertragsunterlagen einsehen (Angebot, AGB-Fassung, Auftragsbestätigung) | ✗ |

---

## 3 · Die Lücke, geordnet

| Rang | Was fehlt | Warum zuerst |
|---|---|---|
| **1** | **Inhaltsänderung anfordern, mit Kontostand** | Die meistgenutzte Abo-Leistung, und die einzige mit einem Guthaben. Ohne Zähler streitet man später über Minuten. |
| **2** | **Leistungsbericht und Re-Audit im Konto** | Beides läuft bereits automatisch — es kommt nur nirgends an. Das ist gebaut und nicht angeschlossen. |
| **3** | **Die Zusagen benennen**, wo sie gelten (Reaktionszeit am Support, Fünf-Tage-Frist an der Freigabe) | Kostet keine Technik, macht den Vertrag sichtbar. |
| **4** | **Kollegen Zugang geben** | Ein Betrieb ist keine Person. Heute muss der Innendienst jeden Zugang einrichten. |
| **5** | **Auskunft und Löschung** | Gesetzlicher Anspruch; heute nur über eine Mail an uns. |
| **6** | **Rücksicherung anfordern** | Selten gebraucht, aber im Ernstfall dringend — und dann sucht niemand nach der Telefonnummer. |
| **7** | **Vertragsunterlagen** | Angebot, AGB-Fassung und Auftragsbestätigung liegen im System; der Kunde kommt nicht heran. |

---

## 4 · Was das für das Dashboard heißt

Ein Dashboard ist die **Antwort auf eine Frage**, nicht eine Anordnung von
Kacheln. Aus der Analyse ergeben sich drei Fragen, und sie wechseln mit der
Projektphase:

| Phase | Die Frage des Kunden | Was oben stehen muss |
|---|---|---|
| Vor dem Baubeginn | *Woran hängt es?* | die offenen Mitwirkungspunkte und der Starttermin |
| Während des Baus | *Wo stehen wir, und bin ich dran?* | Phase, und was zur Freigabe ansteht |
| Nach dem Go-live | *Was bekomme ich für mein Geld?* | Guthaben an Inhaltsänderungen, letzter Bericht, nächstes Re-Audit |

**Ein Bildschirm, drei Zustände** — nicht drei Bildschirme. Heute zeigt das
Konto in allen drei Phasen dasselbe: eine Liste von Blöcken.

---

## 5 · Die Prüfung nach Krug

> Angewandt wird derselbe Maßstab wie in `docs/ux-soll-ist-kas.md` § 2. Dort
> blieb **Reise C ausdrücklich offen**: „ob der Kunde sie in seinem eigenen
> Menü findet, ist an dieser Stelle nicht geprüft". Das ist am 04.09.2026
> nachgeholt — am laufenden Werkzeug, angemeldet als Kunde, jede der acht
> Seiten aufgerufen.

### 5.1 Ist es selbsterklärend? — **nein**

Die Startseite des Kunden heißt **„NACHHALTIKA"** — sein eigener Firmenname.
Krugs erste Frage lautet *Wo bin ich?*, und der Bildschirm antwortet mit etwas,
das der Betrachter ohnehin weiß. Er sagt nicht, was man hier tun kann.

Alle acht Seiten tragen ihren Menüpunkt als Überschrift — außer dieser einen.
Ausgerechnet die, auf der der Kunde landet.

### 5.2 Ein Wort pro Sache? — **überwiegend, mit einem Bruch**

Das Menü mischt Besitzanzeigende: **„Meine** Daten", **„Mein** Briefing",
**„Meine** Rechnungen" — daneben „Freigaben", „Support", „Akademie" ohne. Kein
schwerer Fehler, aber der Leser fragt sich, ob „Freigaben" seine sind oder
unsere.

### 5.3 Führt die visuelle Gewichtung? — **nein, sie widerspricht sich**

Auf der Startseite stehen zwei Blöcke, die sich gegenseitig widersprechen:
oben *„Es fehlen noch vier Angaben"*, darunter der Projektstatus *„Kickoff
läuft"*. Beides gleich groß, beides gleich gewichtet. Der Kunde muss selbst
entscheiden, welcher der beiden gilt — genau das, was Krug „thinking" nennt.

### 5.4 Werden Konventionen eingehalten? — **nein, an zwei Stellen**

**Ein Knopf, der nichts tut.** Erledigte Mitwirkungskarten waren gesperrt,
sahen aber aus wie die offenen — gleiche Form, gleicher Rahmen, **gleicher
Zeigefinger-Cursor**. Wer auf die erste Karte klickte, klickte auf die tote.
Gefunden am 04.09. von David beim ersten Hinsehen; behoben.

**Ein Menüpunkt, der nie leuchtet.** „Dashboard" zeigte auf `/app/dashboard` —
eine Weiche, die einen Kunden sofort weiterschickt. Der Klick landete richtig,
die Hervorhebung nie: `isActive` verglich mit der Adresse **nach** der
Umleitung. Von außen: „lässt sich nicht aktivieren". Ebenfalls am 04.09.
behoben — und derselbe Fehler stand zwei Zeilen darunter schon einmal
kommentiert, dort am 26.08. behoben.

> **Beide sind dieselbe Regel:** Was aussieht wie bedienbar, muss bedienbar
> sein. Und was man anklickt, muss zeigen, dass man dort ist.

### 5.5 Wie viel Rauschen? — **wenig. Zu wenig.**

Das seltene umgekehrte Problem. Gemessen wurde der Textumfang jeder Seite:

| Seite | Wörter | |
|---|---:|---|
| Dashboard | 250 | |
| Mein Briefing | 179 | |
| Freigaben | 135 | wirkt leer |
| Meine Daten | 110 | wirkt leer |
| Akademie | 57 | leer — kein einziges Modul (L-60) |
| Meine Rechnungen | 50 | |
| Support-Anfragen | 39 | wirkt leer |
| Einstellungen | 32 | |

**Sieben von acht Seiten sind kürzer als dieser Abschnitt.** Ein Konto, das
79 € oder 149 € im Monat kostet, zeigt auf seiner umfangreichsten Seite 250
Wörter. Das ist kein Gestaltungsfehler, sondern die Folge von Abschnitt 2: Von
zwölf bezahlten Leistungen ist keine abrufbar, also hat das Konto nichts zu
zeigen.

### 5.6 Der Trunk-Test — **fällt durch, aber anders als beim Innendienst**

*Wo bin ich?* — Auf einer Seite mit meinem eigenen Firmennamen als Titel.
*Was kann ich hier?* — Vier Blöcke ohne erkennbare Ordnung.
*Wie komme ich woandershin?* — Das gelingt: Das Menü ist kurz, deutsch und
vollständig sichtbar. **Das ist die eine Frage, die das Kundenkonto besser
beantwortet als der Innendienst.**

---

## 6 · Was daraus für den Bau folgt

Drei Regeln, aus dieser Prüfung und nicht aus Geschmack:

1. **Die Startseite bekommt einen Titel, der eine Frage beantwortet** — nicht
   den Firmennamen. „Ihr Projekt" oder „Ihr Websprint Relaunch".
2. **Ein Satz oben, der beide Seiten zusammenfasst.** Solange zwei Blöcke sich
   widersprechen dürfen, muss der Kunde entscheiden, welcher gilt.
3. **Kein Menüpunkt ohne Inhalt.** Die Akademie steht im Menü und ist leer;
   ein Raum, in dem nichts steht, kostet Vertrauen — jedes Mal, wenn jemand
   hineinsieht.

---

## Reproduzierbarkeit

```bash
# Menüpunkte des Kunden
grep -n "Kunde view" -A 20 kompagnon/frontend/src/components/Layout/SidebarNav.jsx

# Kundennahe Routen am geladenen Backend
cd kompagnon/backend && venv/bin/python -c "
from main import app
print([p for p in sorted(app.openapi()['paths']) if '/portal/' in p])"

# Das Leistungsverzeichnis der Abos
sed -n '50,80p' docs/produkte/abo-und-geo.md
```
