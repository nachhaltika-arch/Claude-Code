# RESTARBEITEN-REPORT — Buch „Der Homepage Standard"

**Stand:** 14.08.2026
**Manuskript:** 18 Dateien, 48.094 Wörter, ca. 166 Satzseiten
**Grundlage:** alle redaktionellen Anmerkungen aus Kapitel 0 bis 14 und den drei Anhängen
**Standard-Version:** 2026.2

---

## Kurzfassung

Das Manuskript ist inhaltlich vollständig. Es kann **nicht** in Druck gehen, solange fünf
Blocker offen sind. Vier davon liegen in der Software, nicht im Text.

| Kategorie | Anzahl | Davon Blocker |
|---|---|---|
| A · Software-Abgleich | 9 | 3 |
| B · Rechtliche Prüfung | 9 | 2 |
| C · Belege und Erhebungen | 8 | 0 |
| D · Redaktion und Satz | 12 | 0 |
| E · Abbildungen | 46 Stück | 0 |
| F · Formales zur Veröffentlichung | 6 | 0 |

**Geschätzter Restaufwand bis zur Druckfreigabe:** 4 bis 6 Wochen, davon der größte Teil
Wartezeit auf Software-Umsetzung und anwaltliche Prüfung.

---

## Die fünf Blocker

Ohne diese fünf Punkte widersprechen sich Buch und Produkt an sichtbarer Stelle.

| # | Blocker | Wo | Warum blockierend |
|---|---|---|---|
| **B1** | **Branchenmodell K1–K6 nicht implementiert** | Software | Kapitel 2, 7, 9 und 10 beschreiben klassenabhängige Maßstäbe. Das Audit kennt heute nur `betriebsseite` als binäre Unterscheidung. Ein Käufer liest im Buch von K2 und findet im Bericht nichts davon. |
| **B2** | **Stufenschwellen Frontend gegen Backend** | Software | Backend deckelt bei 95/85/70/50, Frontend trägt laut Projektwissen 85/70/50/30. Derselbe Score zeigt im Bericht und im Widget verschiedene Stufen. Das Buch kann nur eine Fassung drucken. |
| **B3** | **Punktabstufungen nicht gegen `audit_criteria.py` abgeglichen** | Software | Sämtliche Schwellentabellen in Kapitel 3 bis 10 sind konstruiert. Weicht der Code ab, rechnet der Leser falsch. |
| **B4** | **PageSpeed-Schlüssel auf Render** | Software | Ohne ihn fallen P1–P4 **und** B1 aus — 18 von 100 Punkten. Kapitel 5 und 6 beschreiben dann eine Bewertung, die nie stattfindet. |
| **B5** | **Rechtsprüfung der neun markierten Aussagen** | Anwalt | RDG-Risiko und inhaltliche Angreifbarkeit. Siehe Abschnitt B. |

---

## A · Software-Abgleich

| # | Punkt | Quelle | Priorität |
|---|---|---|---|
| A1 | Branchenmodell K1–K6 umsetzen: `audit_industry_map.py`, `audit_industry_profiles.py`, Anwendbarkeit in `audit_criteria.py`, Rubric in `audit_ai.py` | Kap. 2, 7, 9, 10 | **Blocker** |
| A2 | Stufenschwellen vereinheitlichen — `AuditHook.jsx`, `audit-widget.html`, `CustomerDashboard.jsx`, `AuditHistory.jsx` gegen Backend | Kap. 2 | **Blocker** |
| A3 | Alle Punktabstufungen aus `audit_criteria.py` extrahieren und mit den Tabellen in Kap. 3–10 abgleichen | alle Kategoriekapitel | **Blocker** |
| A4 | PageSpeed-Schlüssel in Render prüfen und setzen | Kap. 5, 6 | **Blocker** |
| A5 | **L5 umstellen:** Kriterium bewertet heute eine Einwilligungs-Checkbox. Buch argumentiert, dass ein Datenschutzhinweis mit Verweis ausreicht und eine erzwungene Einwilligung selbst angreifbar ist | Kap. 3 | hoch |
| A6 | **P5 prüfen:** Katalog nennt vier Teilprüfungen bei 3 Punkten — dieselbe Konstellation wie seinerzeit D6 | Kap. 5 | hoch |
| A7 | **Doppelwertungen auflisten und entscheiden:** L3/S4, B4/E2, D2/B2, D4/C4. Bei L3/S4 darf die Bronze-Deckelung nur **einmal** greifen | Kap. 4, 7, 8, 9 | hoch |
| A8 | **Die drei KI-Rubrics in den Prompt übernehmen:** acht Alterungsmerkmale (8.4), Klassentabellen (9.4–9.8), Wir- und Wettbewerbertest (10.6) | Kap. 8, 9, 10 | hoch |
| A9 | **Wiederholbarkeit messen:** dieselbe Website dreimal bewerten lassen, Streuung je Kriterium. Über einem Punkt = Rubric zu unscharf. Kapitel 2.1 verspricht Wiederholbarkeit ausdrücklich | Kap. 8 | hoch |

---

## B · Rechtliche Prüfung

Ein Termin für alle neun Punkte. Erfahrungsgemäß 400 bis 800 Euro.

| # | Aussage | Kapitel |
|---|---|---|
| B-1 | **RDG-Absicherung insgesamt:** Haftungsausschluss in der Titelei plus Rechtshinweise zu Beginn der Kapitel 3, 4 und 6 — genügt das? | Titelei, 3, 4, 6 |
| B-2 | Telefonnummer im Impressum: EuGH-Rechtsprechung, kein Telefonzwang | 3.3 |
| B-3 | BFSG-Kleinstunternehmen-Ausnahme, insbesondere bei kombiniertem Onlineverkauf | 3.6, 6.2 |
| B-4 | Einwilligungs-Checkbox am Kontaktformular — Rechtsgrundlage und Freiwilligkeit | 3.7 |
| B-5 | Vollständigkeit der berufsständischen Impressumspflichten | 3.3 |
| B-6 | EU-US Data Privacy Framework: Abgrenzung Übermittlungsfrage gegen Einwilligungsfrage | 4.6 |
| B-7 | Preisangaben bei reglementierten Berufen — nach Berufsständen differenzieren | 9.2, 9.8 |
| B-8 | Anspruch auf Herausgabe von Zugängen | 13.2 |
| B-9 | Formulierung zur Markenbezeichnung ohne Eintragung — keine ®/™-Zeichen | Titelei |

---

## C · Belege und Erhebungen

Alle acht Punkte lassen sich aus den KAS-Audits beantworten. **Das ist der wertvollste Teil
dieser Liste** — jede dieser Zahlen ist exklusiv und macht das Buch zitierfähig.

| # | Zu belegen | Kapitel | Auswertung |
|---|---|---|---|
| C1 | Anteil mobiler Zugriffe auf Unternehmenswebsites | 1.2 | externe Quelle nötig |
| C2 | Durchschnittliche Dauer einer Stellenbesetzung | 1.3 | externe Quelle nötig |
| C3 | Typische Abmahnkosten | 1.4 | bewusst weggelassen, bleibt so |
| C4 | Unternehmensprofil und Bewertungen wiegen schwerer als Seiteninhalte | 2.5, 7.2 | externe Quelle |
| C5 | Zusammenhang Ladezeit und Absprung | 5.4 | externe Quelle oder eigene LCP-Verteilung |
| C6 | Etwa ein Drittel der WCAG-Anforderungen automatisiert prüfbar | 6.4 | Quelle oder abschwächen |
| C7 | **Häufigkeit der 20 Fehler** — Kapiteltitel behauptet „die häufigsten" | 12 | **eigene Auswertung, zwingend** |
| C8 | **Neue Websites fallen bei Einwilligung überdurchschnittlich durch** | 14.4 | Domain-Alter gegen L3-Punktzahl |

> **C7 und C8 sind die beiden Zahlen, die außer euch niemand hat.** C7 macht aus einer
> Behauptung im Kapiteltitel eine Erhebung. C8 ist der Satz, der in jeder Presseanfrage
> zitiert würde. Beide sollten vor Drucklegung erhoben werden.

Ergänzend, ohne Kapitelbezug, aber mit dem größten Wirkungsnachweis:
**Vorher-Nachher-Punktgewinne aus Wiederholungsmessungen** → ersetzt die Schätzungen in
Abschnitt 13.1.

---

## D · Redaktion und Satz

| # | Punkt | Kapitel |
|---|---|---|
| D1 | **Praxisfälle durch anonymisierte reale Fälle ersetzen** — Fall A, B und C sind konstruiert. Betrifft Kap. 2, 3, 4, 5, 6, 7, 8, 9, 10 und die Formulierung im Haftungsausschluss | durchgehend |
| D2 | **Punktkette Fall A nachziehen**, wenn sich eine Zahl ändert: 76 → Bildfix +10 → 86 (Kap. 2, 5, 6) | 2, 5, 6 |
| D3 | Tabellen in 11.4–11.6, 12.2 und Anhang B **beim Build aus `homepage-standard.json` erzeugen** statt pflegen — vier Stellen mit denselben Zahlen | 11, 12, Anhang B |
| D4 | Vorwort und Abschnitt 1.6 überschneiden sich — 1.6 straffen | Titelei, 1 |
| D5 | Ausfüllfelder in Kapitel 11 als PDF-Formularfelder prüfen | 11 |
| D6 | B3 und B5 stehen in Block C, werden aber am Rechner geprüft — beim Satz hervorheben | 11.5 |
| D7 | Rundungsregel festlegen: kaufmännisch oder abschneiden. Entscheidet in Grenzfällen über die Stufe | 11.8 |
| D8 | P3-Zeile in der Schwellentabelle wirkt durch leere Felder wie ein Fehler | Anhang B |
| D9 | Anhang B oder Vorlage 5 auf die Umschlaginnenseite — konkurrieren um denselben Platz | Anhang B, C |
| D10 | Vorlage 1 und 2 auf je einer Seite platzieren, damit sie heraustrennbar sind | Anhang C |
| D11 | **Vorlage 3 darf keine Passwortfelder bekommen** — im Lektorat sichern | Anhang C |
| D12 | **Keine ®- oder ™-Zeichen ergänzen** — Marke ist nicht eingetragen | Titelei |

---

## E · Abbildungen — 46 Stück

| Kapitel | Anzahl | Kapitel | Anzahl |
|---|---|---|---|
| 1 | 3 | 9 | 4 |
| 2 | 6 | 10 | 3 |
| 3 | 4 | 11 | 2 |
| 4 | 3 | 12 | 3 |
| 5 | 4 | 13 | 3 |
| 6 | 4 | 14 | 2 |
| 7 | 4 | | |
| 8 | 5 | **Gesamt** | **46** |

**Zwei Grundregeln, die für alle gelten:**

1. **Keine fremden Websites abfotografieren.** Alle Negativ- und Positivbeispiele werden
   schematisch nachgebaut, mit erfundenen Firmennamen. Das ist urheberrechtlich sauber und
   im Haftungsausschluss bereits so zugesichert.
2. **Keine fremden Benutzeroberflächen abbilden.** Prüfwerkzeuge ändern ihr Aussehen; eine
   abfotografierte Oberfläche veraltet vor der zweiten Auflage. Schematisch nachbauen.

**Doppelnutzung prüfen:** Die Abbildung „Netzwerk-Reiter mit markierten Fremddomains"
erscheint in Kapitel 3 und 4 mit unterschiedlicher Beschriftung. Eine gemeinsame Abbildung
mit zwei Bildunterschriften könnte genügen.

---

## F · Formales zur Veröffentlichung

| # | Punkt | Wann |
|---|---|---|
| F1 | BoD-Konto anlegen, Titel anlegen, **kostenlose ISBN** beantragen | vor Satz |
| F2 | Platzhalter füllen: Registerangaben, Anschrift, Kontakt, Auflage, Jahr, Monat | vor Satz |
| F3 | **`{{QR_AUDIT}}`-Ziel festlegen** — eigene Domain, serverseitig weiterleitbar, mit `utm_source=buch`. **Nach dem Druck nicht mehr änderbar** | vor Satz |
| F4 | Cover gestalten — erst nach finaler Seitenzahl möglich, weil die Rückenbreite davon abhängt | nach Satz |
| F5 | Seitenzahl auf ein Vielfaches von 4 bringen, Mindestumfang 48 Seiten | nach Satz |
| F6 | **Pflichtexemplare:** zwei an die Deutsche Nationalbibliothek, eines an die Landesbibliothek Rheinland-Pfalz in Koblenz | nach Erscheinen |

---

## Empfohlene Reihenfolge

**Phase 1 — parallel starten (Woche 1)**

1. A4 PageSpeed-Schlüssel prüfen — fünf Minuten, größte Hebelwirkung
2. A2 Stufenschwellen vereinheitlichen — halber Tag
3. A3 Punktabstufungen extrahieren und an mich zurückspielen — halber Tag
4. B Anwaltstermin vereinbaren — Vorlauf einplanen
5. C7 und C8 auswerten, sobald genügend Audits vorliegen

**Phase 2 — Software (Woche 2 bis 4)**

6. A1 Branchenmodell umsetzen — sieben Schritte, ein Commit je Schritt
7. A5 bis A9 abarbeiten
8. Drei Testläufe gegen echte fremde Websites aus drei Klassen

**Phase 3 — Manuskript nachziehen (Woche 4)**

9. Alle Schwellentabellen auf die Code-Werte umstellen
10. D1 Praxisfälle durch reale Fälle ersetzen
11. C-Belege einarbeiten oder Aussagen abschwächen
12. Lektorat

**Phase 4 — Produktion (Woche 5 bis 6)**

13. Abbildungen erstellen
14. Satz, Seitenzahl justieren, Cover
15. BoD-Upload, Druckfreigabe

---

## Was ich als Nächstes von dir brauche

**Zuerst A3:** die Punktabstufungen aus `services/audit_criteria.py`. Ohne sie bleiben
sämtliche Schwellentabellen in acht Kapiteln vorläufig — das ist der größte Einzelposten
in diesem Report.

**Danach A2 und A4:** zwei Prüfungen von je fünf Minuten, die klären, ob zwei Kapitel
überhaupt eine reale Bewertung beschreiben.
