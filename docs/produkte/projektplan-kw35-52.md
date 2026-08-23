# KAS — PROJEKTPLAN KW35–KW52 / 2026

> ## Stand am 23.08.2026 — neun Aufgaben aus Bahn A sind bereits erledigt
>
> Am laufenden System nachgemessen, nicht aus dem Plan übernommen. Zusammen
> rund **26 der geplanten 79 Entwicklungstage** liegen schon dahinter — die
> Reihenfolge im kritischen Pfad verschiebt sich entsprechend nach vorn.
>
> | ID | Geplant | Gemessener Stand |
> |---|---|---|
> | **A01** | PageSpeed-Key setzen, 0,5 Tage | ✅ gesetzt und arbeitend (Log 22.08., HTTP 200) |
> | **A02** | Score-Schwellen zentralisieren, 3 Tage | ✅ beidseitig 95/85/70/50 identisch |
> | **A03** | Regelwiderspruch in `CLAUDE.md`, 0,5 Tage | ✅ die Datei sagt eindeutig `staging`, `claude/*` verworfen |
> | **A05** | Routen-Kollision, 3 Tage | ✅ `request-approval` kommt genau einmal vor |
> | **A06** | UWG: WordPress-Aussage **und** zwei Preiswelten, 2 Tage | ✅ beides am 23.08. behoben (L-97) |
> | **A08** | Double-Opt-in fürs Widget, 4 Tage | ✅ `verify_token`, `confirm_token`, `/bestaetigung/{token}` |
> | **A09** | PDF-Endpunkt absichern, 1 Tag | ✅ `require_innendienst`, produktiv 401 |
> | **A27** | Migrationen aus `main.py`, 2 Tage | ✅ am 22.08. (`migrations_runtime.py`) |
> | **A28/A29** | `projects.py` Split, 10 Tage | ✅ am 23.08. (L-25) |
> | **A30** | `product_type` auf drei Varianten, 2 Tage | ✅ am 23.08. — `websprint_relaunch/neubau/system` |
>
> **A30 war für KW50 geplant und ist heute passiert.** Der Plan setzt sie ans
> Ende, weil sie von A29 abhängt; tatsächlich ergab sie sich aus der
> Preisentscheidung. Damit ist auch **M7 („Drei Produktvarianten im System",
> 18.12.)** im Kern erreicht — auswählbar sind sie, verkäuflich sind zwei.
>
> **Was am Meilenstein M1 (Websprint angebotsfähig, 11.09.) noch fehlt:** nicht
> mehr die Technik, sondern die **Garantiezahl**. A01 und A02 waren die
> genannten Blocker, beide sind weg. Es braucht die fünf Referenzmessungen aus
> Bahn B, um [SCHWELLE] für G1 festzulegen.
>
> **Noch nicht abschließend gemessen:** A04 (Freigabebug `v === true`) — es gibt
> mehrere Stellen dieser Form im Frontend, welche der Plan meint, geht aus ihm
> nicht hervor. A10 (drei Namen fürs Pflegeprodukt) — „Pflege", „Wartung" und
> „Betreuung" kommen alle vor, teils aber als Branchenwort, nicht als
> Produktname.
>
> **Die Orders-Strecke A16–A23 (17 Tage)** ist im Lagebild als **[L-100]**
> geführt; die acht Prompts liegen unter `orders/`. **A24/A25 (GEO und
> Consent, 8 Tage)** sind **[L-99]**, **A11–A13 (Abo, 7 Tage)** sind
> **[L-101]**.

Stand: 23.08.2026 · Start: Montag, 24.08.2026 · Ende: Freitag, 18.12.2026

---

## 1. Wie dieser Plan gelesen wird

**Drei Bahnen, die parallel laufen.** Ein einspuriger Plan wäre unrealistisch — der Anwalt, Manuel und Claude Code arbeiten gleichzeitig.

| Bahn | Wer | Engpass |
|---|---|---|
| **A · Entwicklung** | Claude Code, von dir gesteuert | Strikt sequenziell. Ein Prompt, ein Commit, Deploy geprüft, dann der nächste. |
| **B · Recht, Steuer, Geschäftsführung** | Kanzlei, Steuerberater, du | Wartezeiten extern. Deshalb sofort anstoßen. |
| **C · Inhalt und Gestaltung** | du und Manuel | Läuft unabhängig von der Entwicklung, hängt aber an Bahn A für die Punktetabellen. |

**Prioritätsstufen**

| Stufe | Bedeutung |
|---|---|
| **P1** | Rechtliches Risiko oder blockiert jeden Umsatz. Nicht verschiebbar. |
| **P2** | Schafft unmittelbar Umsatz. |
| **P3** | Strukturschuld und Skalierung. Wichtig, aber nicht dringend. |

**Kapazitätsannahme:** rund 3 wirksame Entwicklungstage pro Woche. Du bist Geschäftsführer, nicht Vollzeitentwickler. Wenn mehr Zeit zur Verfügung steht, verkürzt sich der Plan; die Reihenfolge bleibt.

---

## 2. Warum diese Reihenfolge

Vier Regeln bestimmen die Abfolge:

1. **Rechtliche Risiken zuerst.** Ein laufender Verstoß kostet mehr als jede verschobene Funktion. Die UWG-Korrektur am Widget und das Double-Opt-in stehen deshalb vor allem Neuen.
2. **Billige Blocker vor teuren Funktionen.** Der PageSpeed-Key ist in Minuten gesetzt und macht die Garantie erst möglich. So etwas wird nie nach hinten geschoben.
3. **Wiederkehrender Umsatz vor einmaligem.** Das Pflege-Abo kostet drei Entwicklungstage und trägt monatlich. Es steht vor dem Shop, obwohl du den Shop als Nächstes gewählt hast — es ist schlicht die bessere Rendite pro Tag.
4. **Aufräumen erst, wenn es teurer wird, es nicht zu tun.** Der Refactor von `projects.py` steht vor den Produktvarianten, weil diese die Datei stark verändern. Umgekehrt wäre die Arbeit doppelt. Der Shop steht davor, weil er ein neues, eigenständiges Modul ist und die Altlast nicht berührt.

⚠️ **Abweichung von deiner Entscheidung.** Du hast das Orders-Subsystem als nächsten Prompt-Block gewählt. Die Prompts sind fertig und liegen bereit. Im Plan liegt es dennoch hinter dem Pflege-Abo, weil drei Tage Abo-Arbeit ab Oktober monatlich Geld bringen, während der Shop erst mit dem fertigen Workbook Umsatz erzeugt — und das Workbook ist noch nicht geschrieben. Wenn du das anders siehst, tauschen wir die Blöcke A11–A14 und A16–A23.

---

## 3. Meilensteine

| | Meilenstein | Datum | Woran erkennbar |
|---|---|---|---|
| **M1** | Websprint angebotsfähig | **11.09.2026** | Erstes Angebot mit belastbarer Garantiezahl ist versendbar |
| **M2** | Audit-Widget rechtssicher | **25.09.2026** | Widget darf an Innungen und Kammern ausgeliefert werden |
| **M3** | Pflege-Abo aktiv | **09.10.2026** | Erste wiederkehrende Zahlung eingegangen |
| **M4** | Shop live | **06.11.2026** | Check PLUS ist online kaufbar |
| **M5** | Buch veröffentlicht | **20.11.2026** | ISBN gelistet, im Buchhandel bestellbar |
| **M6** | SYSTEM verkaufsfähig | **27.11.2026** | GEO-Artefakte an echter Kundendomain verifiziert |
| **M7** | Drei Produktvarianten im System | **18.12.2026** | Relaunch, Neubau und System im Deal auswählbar |

---

## 4. Bahn A · Entwicklung

| ID | Aufgabe | Prio | Tage | Hängt ab von | KW |
|---|---|---|---|---|---|
| A01 | PageSpeed-Key auf Render setzen | **P1** | 0,5 | — | 35 |
| A02 | Score-Schwellen zentralisieren, Frontend liest vom Backend | **P1** | 3 | A01 | 35–36 |
| A03 | Regelwiderspruch in CLAUDE.md korrigieren | P2 | 0,5 | — | 35 |
| A04 | ProzessFlow-Freigabebug `v === true` | **P1** | 1 | A02 | 36 |
| A05 | Routen-Kollision `request-approval` und Status-Vokabular | **P1** | 3 | A04 | 36–37 |
| A06 | UWG-Korrektur: WordPress-Aussage und zwei Preiswelten | **P1** | 2 | A05 | 37 |
| A07 | Eigene Datenschutzseite auf TDDDG-Konformität | **P1** | 2 | A06 | 37–38 |
| A08 | Double-Opt-in für das Audit-Widget | **P1** | 4 | A07 | 38 |
| A09 | PDF-Audit-Endpunkt absichern | P2 | 1 | A08 | 38–39 |
| A10 | Drei Namen für das Pflegeprodukt vereinheitlichen | P2 | 0,5 | A09 | 39 |
| A11 | Pflege-Abo: Checkout-Endpunkt und Stripe-Produkte | **P2** | 3 | A10 | 39–40 |
| A12 | Abo-Angebot als Pflichtschritt nach der Abnahme | **P2** | 2 | A11 | 40 |
| A13 | Zeiterfassung der Änderungskontingente | P2 | 2 | A12 | 40–41 |
| A14 | Monatsreport über APScheduler (Hebel #5) | P2 | 3 | A13 | 41 |
| A15 | Export-Skript `audit_criteria.py` → Manuskripttabellen | **P1** | 2 | A02 | 41–42 |
| A16 | Orders Prompt 01 — Datenmodell | P2 | 1 | A15 | 42 |
| A17 | Orders Prompt 02 — API und Produktseite | P2 | 2 | A16 | 42 |
| A18 | Orders Prompt 03 — Stripe Checkout | P2 | 2 | A17, B04 | 43 |
| A19 | Orders Prompt 04 — Webhook | P2 | 2 | A18 | 43 |
| A20 | Orders Prompt 05 — Widerruf und Pflichtangaben | **P1** | 2 | A19, B07 | 44 |
| A21 | Orders Prompt 06 — Auslieferung | P2 | 3 | A20, B09 | 44 |
| A22 | Orders Prompt 07 — Rechnungsnummern | **P1** | 3 | A21, B03 | 45 |
| A23 | Orders Prompt 08 — Anrechnung | P2 | 2 | A22 | 45 |
| A24 | GEO-Injection in den Netlify-Deploy plus Verifikation | **P2** | 4 | A23 | 46 |
| A25 | Consent-Layer für Kundenseiten | **P1** | 4 | A24 | 46–47 |
| A26 | Quartals-Re-Audit als Hintergrundjob | P2 | 2 | A25 | 47 |
| A27 | Migrationen aus `main.py` extrahieren | P3 | 2 | A26 | 48 |
| A28 | `projects.py` Split, Sessions 1 und 2 | P3 | 5 | A27 | 48–49 |
| A29 | `projects.py` Split, Sessions 3 und 4 | P3 | 5 | A28 | 49–50 |
| A30 | `product_type` auf drei Varianten erweitern | P3 | 2 | A29 | 50 |
| A31 | Prozessflow datengetrieben, Schritte aus der Datenbank | P3 | 4 | A30 | 51 |
| A32 | Stripe-Mapping und Angebots-PDF je Produkt | P3 | 3 | A31 | 51–52 |

---

## 5. Bahn B · Recht, Steuer, Geschäftsführung

| ID | Aufgabe | Prio | Dauer | Start | Hinweis |
|---|---|---|---|---|---|
| B04 | Stripe-Schlüssel prüfen und beschaffen | **P1** | 2 Tage | 24.08. | In der Env-Liste fehlt ein Stripe-Key |
| B01 | Anwaltsbriefing zusammenstellen | **P1** | 3 Tage | 24.08. | Alle Punkte in **einem** Auftrag bündeln |
| B02 | Anwaltliche Prüfung | **P1** | 5 Wochen | 27.08. | Externe Wartezeit, deshalb sofort starten |
| B03 | Steuerberater: USt Workbook, Rechnungsnummernkreis | **P1** | 2 Wochen | 31.08. | Blockiert A22 |
| B05 | Referenzmessung und Festlegung der Garantieschwelle | **P1** | 2 Tage | nach A02 | 5 Referenzseiten messen |
| B06 | Entscheidung Branchenklassen K1–K6 | P2 | 3 Tage | 07.09. | Implementieren oder aus dem Buch streichen |
| B08 | Angebotsvorlagen Relaunch und Neubau | **P2** | 5 Tage | 07.09. | Aus den Datenblättern, Rechtstexte vorläufig |
| B07 | AGB und Mitwirkungskatalog final | **P1** | 1 Woche | nach B02 | Wortgleich mit den Angeboten |
| B09 | Speicherentscheidung Objektspeicher | P2 | 2 Tage | 19.10. | Empfehlung Cloudflare R2 |
| B10 | AV-Vertragsmuster | **P1** | 1 Woche | nach B07 | Voraussetzung für SYSTEM |
| B11 | ISBN beantragen, BoD-Konto einrichten | P2 | 3 Tage | 09.11. | Vorlauf beachten |
| B12 | Entscheidung SYSTEM-Preis | P2 | 2 Tage | 23.11. | 12.900 € halten oder 13.900 € |

### Inhalt des Anwaltsbriefings (B01) — alles in einem Auftrag
1. Standard-Garantie und Bauzeitgarantie, Verzugspauschale, Fristbeginn und Fristpause
2. Bauplan-Ausstiegsgarantie
3. Quartals-Garantie und ihre Ausschlüsse
4. Buchpreisbindung: Lead-Magnet, Bundles, Anrechnung
5. Konstruktion des Workbooks als Nichtbuch
6. Widerrufsbelehrung und Verzichtserklärung für digitale Produkte
7. AV-Vertrag für Analysedienste auf Kundenseiten
8. Neun Rechtsaussagen im Buchmanuskript
9. Namentliche Nennung von Wettbewerbern im Check-PLUS-Bericht
10. Barrierefreiheit nach BFSG — Betroffenheit von Handwerksbetrieben

**Ein Auftrag statt zehn Einzelfragen** spart Geld und vermeidet widersprüchliche Auskünfte.

---

## 6. Bahn C · Inhalt und Gestaltung

| ID | Aufgabe | Prio | Dauer | Start | Hängt ab von |
|---|---|---|---|---|---|
| C01 | Punktetabellen aus dem Export ins Manuskript | **P1** | 8 Tage | 12.10. | A15 |
| C02 | Branchenklassen im Buch nachziehen oder streichen | P2 | 6 Tage | nach C01 | B06 |
| C03 | Titel und Umschlag (Manuel) | P2 | 8 Tage | 26.10. | — |
| C04 | Buch-Endkorrektur | P2 | 5 Tage | 09.11. | C02, B02 |
| C05 | BoD-Upload und Veröffentlichung | P2 | 4 Tage | 16.11. | C04, B11 |
| C06 | Workbook schreiben | P2 | 20 Tage | 02.11. | Ableitung aus dem Manuskript |
| C07 | Workbook Satz und ausfüllbares PDF (Manuel) | P2 | 5 Tage | 07.12. | C06 |
| C08 | Workbook Verkaufsstart im Shop | P2 | 2 Tage | 14.12. | C07, A23 |

---

## 7. Kritischer Pfad

```
A01 → A02 → A04 → A05 → A06 → A07 → A08 → A11 → A15 → A16…A23 → A24 → A25 → A27…A32
```

Jede Verzögerung auf diesem Pfad verschiebt alle nachfolgenden Meilensteine. Die Bahnen B und C haben Puffer, **mit einer Ausnahme:** B02 (anwaltliche Prüfung) blockiert A20, A22 und B10. Wird das Briefing nicht in der ersten Woche versendet, verschiebt sich der Shop-Start um genau so viele Tage.

---

## 8. Risiken

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| Anwaltsprüfung dauert länger als 5 Wochen | Shop und SYSTEM verschieben sich | Briefing in Woche 1 raus, Zwischenstand nach 3 Wochen erfragen |
| Stripe-Schlüssel existieren gar nicht | A18 bis A23 blockiert | B04 sofort in Woche 1 |
| `projects.py`-Refactor bricht Bestehendes | Produktivsystem instabil | Vier getrennte Sessions, je ein Commit, Deploy einzeln geprüft |
| Workbook wird nicht fertig geschrieben | M7 fällt aus | C06 blockweise planen, nicht nebenbei |
| GEO-Injection funktioniert an echter Domain nicht | SYSTEM bleibt gesperrt | A24 enthält die Verifikation als Teil der Aufgabe, nicht als Nachprüfung |
| Textaufwand beim Neubau reißt die Kalkulation | Marge unter 95 €/h | Nach drei Projekten messen, dann Seitenzahl begrenzen |

---

## 9. Wochenrhythmus

**Montag, 15 Minuten:** Welche Aufgaben stehen diese Woche in Bahn A? Ist der Vorgänger deployt und geprüft?
**Freitag, 15 Minuten:** Was ist erledigt, was rutscht, liegt etwas auf dem kritischen Pfad?

**Feste Regel für Bahn A:** Ein Prompt, ein Commit, Push, Render-Log geprüft — erst dann der nächste. Kein Prompt startet, solange der Verbindungs-Check des vorherigen nicht durchgelaufen ist. Genau diese Disziplin verhindert das Muster, bei dem am Ende einer Woche vier Dinge halb fertig sind und keines funktioniert.
