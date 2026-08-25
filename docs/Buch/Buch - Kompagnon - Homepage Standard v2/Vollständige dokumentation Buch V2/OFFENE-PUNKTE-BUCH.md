# OFFENE PUNKTE · BUCH

**Stand:** 24.08.2026, nach Block C
**Umfang:** 131 Punkte ohne technische Zuständigkeit, davon 37 rot

| Rolle | Punkte |
|---|---|
| Autor | 35 |
| Lektorat | 34 |
| Gestaltung (Manuel) | 24 |
| Recht | 20 |
| Geschäftsführung | 13 |
| Satz und Produktion | 5 |

> **Was seit Block C feststeht:** Die Katalogsumme bleibt **103**. Der Untertitel ist bestätigt. **Die Sperre auf Manuskriptzahlen ist damit aufgehoben** — alles außer den zehn Punkten in Abschnitt B1 kann anlaufen.

> **Stand 25.08.2026 — B3.1 ist abgearbeitet.** Alle fünf Nachzieh-Punkte aus
> Block C sind erledigt, seit die Software sie eingelöst hat. Dabei kam ein
> eigener Befund heraus: **Rund fünfzig Tabellen im Manuskript trugen den
> Vermerk „ERZEUGT aus `generiert/…` — nicht von Hand ändern".** Diese Dateien
> gab es nie, und kein Skript hat sie geschrieben; die Tabellen waren
> Handarbeit mit einem Schild, das Handarbeit verbot. Zwei Angaben waren
> dadurch nachweislich falsch (B4 „abgeleitet", D2 „Einschätzung"), eine
> dritte veraltet (die Zählung in 3.4). Seit dem 25.08. erzeugt
> `scripts/buch-bloecke.py` die Tabellen, die aus dem Katalog folgen,
> berichtigt den Vermerk bei allen übrigen und **rechnet 32 handgepflegte
> Abstufungstabellen gegen den Katalog nach**. `tests/test_buch_bloecke_aktuell.py`
> hält das fest.

---

# B1 · Geschäftsführung — 13 Punkte, null Arbeitszeit

| ID | Entscheidung | Folge |
|---|---|---|
| **B1.1** | 🔴 **Umfang.** 260 statt 208 Seiten. Akzeptieren, kürzen, oder Teil II abtrennen? | Preis, Rückenbreite, Satzbeginn |
| **B1.2** | 🔴 **Kapiteltitel 14.** „Zwanzig Befunde" oder Originaltitel nach C7 | Inhaltsverzeichnis, Verweis in Kapitel 12 |
| **B1.3** | 🔴 **Vier Adressen.** *Empfehlung: eine Domain mit drei Pfaden* — `/pdf`, `/check`, `/fehler` | **nach dem Druck unumkehrbar** |
| **B1.4** | 🔴 **18 Punkte im Selbsttest nicht prüfbar.** S3 und E4 mit einer technischeren Anleitung erschließen, oder bei U belassen? | Kapitel 13, Anhang C |
| **B1.5** | 🔴 **D1-Staffelung im Selbsttest ist konstruiert.** Zulässig oder streichen? | Kapitel 13 |
| **B1.6** | 🔴 **Abschnitt 2.7 bestätigen** — der Interessenkonflikt bleibt unverändert | Glaubwürdigkeit des ganzen Buchs |
| **B1.7** | 🔴 **Kapitel 17 gegen Eigenwerbung schützen** | dito |
| **B1.8** | **Umschlaginnenseite:** Anhang B, Vorlage 1 oder Vorlage 5? *Empfehlung: Vorlage 1* | Satz |
| **B1.9** | **Teil-Trennseite:** Variante A oder B aus dem Satzmuster | vier Teile, viermal dieselbe Frage |
| **B1.10** | **Widmung oder Motto** auf Seite VII — oder Titelei auf sechs Seiten kürzen | Satz |
| **B1.11** | **Klebebindung:** PDF-Fassung von Prüfliste und Vorlagen ist Voraussetzung, nicht Zugabe | Produktion |
| **B1.12** | ✅ **Untertitel — entschieden.** „39 Kriterien, 8 Kategorien, 103 Punkte" | **ISBN kann beantragt werden** |
| **B1.13** | **Zwei ISBN und eigene Verlagsnummer** bei MVB beantragen — erst nach B1.1 und B1.2 | Vorlauf |

---

# B2 · Recht — 20 Punkte, Anhang D ist die Vorlage

**Vorlauf mehrere Wochen. Ab sofort.**

## Die vierzehn Aussagen

| ID | Zu prüfen |
|---|---|
| **B2.1** | 🔴 Telefonnummer im Impressum — zweiter Kommunikationsweg, ohne Urteilsnachweis |
| **B2.2** | 🔴 Mindestinhalte der Datenschutzerklärung — **die Spezifikation verlangt fünf, der Code prüft drei** |
| **B2.3** | 🔴 **Einwilligungsfeld am Kontaktformular** — der Standard bewertet ein Kriterium, dessen Rechtsgrundlage er selbst als strittig bezeichnet |
| **B2.4** | 🔴 BFSG-Kleinstunternehmen-Ausnahme bei kombiniertem Onlineverkauf |
| **B2.5** | 🔴 **Kammerangabe** — die Spezifikation nennt sie als Pflichtangabe, der Code prüft sie nicht. **Ein Handwerksbetrieb kann 6 von 6 Punkten bekommen, obwohl eine Pflichtangabe fehlt** |
| **B2.6** | 🔴 Energieausweis-Vergleich (2.4) — Verwechslung mit einem hoheitlichen Nachweis |
| **B2.7** | Fremde Server und IP-Übermittlung — bewusst ohne Urteile und Beträge |
| **B2.8** | Abmahnvereine als Prüfer (1.5) — Aussage über Dritte |
| **B2.9** | Barrierefreiheits-Assistenten „umstritten" (8.10) — Aussage über ein käufliches Produkt |
| **B2.10** | 🔴 „Wir garantieren Platz 1" (17.6) — Aussage über einen Berufsstand |
| **B2.11** | Reaktionszeit-Zusage (11.7) — Zusicherung im Wettbewerbsrecht |
| **B2.12** | Foto- und Referenz-Einwilligungen (10.8, 11.8, 16.3) |
| **B2.13** | Vorlage 3 und 4 in Anhang C — Musterkorrespondenz |
| **B2.14** | 🔴 **Vervielfältigungsvorbehalt** — die Titelei erlaubt ausdrücklich das Kopieren der fünf Vorlagen |

## Dazu

| ID | Punkt |
|---|---|
| **B2.15** | 🔴 **Buchpreisbindung** — E-Book-Eigenverkauf über KAS bei gleichzeitiger Verlegerstellung |
| **B2.16** | 🔴 **Rechtsstand** — leeres Feld in Anhang D und in der Titelei, Endkontrolle |
| **B2.17** | Der Fall in 4.1 bleibt anonymisiert — im Haftungsausschluss ausgewiesen |
| **B2.18** | Bußgeld- und Abmahnkostenhöhen bleiben draußen — gegen Ergänzung schützen |
| **B2.19** | Die Liste in 16.3 fachlich gegenlesen lassen — **das einzige größere Buchelement ohne Codegrundlage** |
| **B2.20** | Bibliografische Information der DNB — Formulierung bei der Titelanmeldung |

---

# B3 · Autor — 35 Punkte

## B3.1 Nachziehen aus Block C — **jetzt möglich**

| ID | Aufgabe | Aus |
|---|---|---|
| **B3.1.1** | ✅ **erledigt 25.08.2026.** Nachgesehen statt angenommen: Sieben der neun Hinweise beschrieb das Manuskript ohnehin richtig — es war der **Katalog**, der zu viel versprach, nicht das Buch. Angepasst wurden die zwei echten Fälle: **L5** (5.8 und die Kategorietabelle nannten den Verweis auf die Datenschutzerklärung, der nicht geprüft wird) und der Selbsttest in 13.2, der ihn abfragte | C1 |
| **B3.1.2** | ✅ **erledigt 25.08.2026.** 8.7 beschreibt jetzt zwei Prüfungen zu je einem Punkt: Gliederung und die Grundlagen für Vorleseprogramme (Sprachauszeichnung, Feldbeschriftungen). Dazu, was „nicht erhoben" hier bedeutet, und die Abgrenzung zu E2 nachgezogen | C1 |
| **B3.1.3** | ✅ **erledigt 25.08.2026.** 10.6 ist ein gemessenes Kriterium: Gemessen wird die Schriftgröße, zwei Punkte oder keine. Zeilenlänge, Zeilenabstand und Schriftanzahl stehen weiter da — jetzt ausdrücklich als das, was sie sind: **nicht bewertet**. Merkkasten, Kategorietabelle und Selbsttestzeile mitgezogen | C1 |
| **B3.1.4** | ✅ **erledigt 25.08.2026.** 3.4 zählt 30 gemessen / 3 abgeleitet / 6 eingeschätzt (81 / 7 / 15 Punkte) — und **die Tabelle wird jetzt erzeugt** statt gepflegt (`scripts/buch-bloecke.py`). Mitgezogen: 3.11, die Merkkästen in 3 und 10, Kapitel 10.2 und das Glossar | C1 |
| **B3.1.5** | 🔴 **Kapitel 9.8 und 11.7** — die als „Vorteil" beschriebenen Doppelwertungen einordnen | C3 |
| **B3.1.6** | ✅ **Kapitel 8.5 (B2)** — Kontrasttabelle korrigiert | C2, **erledigt** |

## B3.2 Zahlen und Ketten

| ID | Aufgabe |
|---|---|
| **B3.2.1** | 🔴 **Elektro Hansen** über neun Kapitel — zentraler Drift-Kandidat, bleibt bei 76/103 = 74 |
| **B3.2.2** | 🔴 **Punktkette 15.7** — zweite Kontrollrechnung, bleibt 74 → 93 |
| **B3.2.3** | 🔴 **Der Gewinn von +3 in Woche 4** ist eine Annahme, die sich als Ergebnis liest |
| **B3.2.4** | „33 von 39" in 3.11 — bei jeder Änderung der Erhebungsart mitziehen. **Bleibt Handarbeit:** Die Tabelle in 3.4 wird erzeugt, der Satz in 3.11 nicht |
| **B3.2.5** | Klassenmaxima in 4.5, 13.2, Anhang A und B — nur gemeinsam ändern |

## B3.3 Inhaltliches

| ID | Aufgabe |
|---|---|
| **B3.3.1** | 🔴 **§ 5 DDG statt § 5 TMG** durch das ganze Buch |
| **B3.3.2** | 🔴 **Verweis in Kapitel 12** auf Kapitel 14 — abhängig von B1.2 |
| **B3.3.3** | 🔴 **Fall Elektro Hansen durch einen anonymisierten realen ersetzen** |
| **B3.3.4** | „120 Minuten" im Kapiteltitel 13 — nicht gemessen, zwei Personen durchführen lassen |
| **B3.3.5** | Verweis auf Kapitel 17 in 1.8 und 15.4 bestätigen |
| **B3.3.6** | Verweise auf Kapitel 16 — sechs Stück, alle eingelöst, gegenprüfen |

---

# B4 · Gestaltung — 24 Punkte

## B4.1 Blockierend

| ID | Aufgabe |
|---|---|
| **B4.1.1** | 🔴 **ABB 3.4 Stufenmarken zuerst** — sie kehrt im ganzen Buch wieder. Im Satzmuster bereits umgesetzt |
| **B4.1.2** | **Farbentscheidung bestätigen** — Variante B. **Blockiert nicht mehr:** Das Satzmuster codiert nirgends Information allein über Farbe |
| **B4.1.3** | 🔴 **Satzmuster-Format** — war als A4 deklariert, Raster ist für 170 × 240 gebaut. Korrigierte Fassung liegt vor, **muss übernommen werden** |
| **B4.1.4** | 🔴 **Ergebnisblatt läuft auf zwei Seiten** — verletzt D10, muss heraustrennbar sein |

## B4.2 Fehlende Abbildungen

**Stand: 4 gebrieft, rund 46 geplant.**

| ID | Kapitel | Was fehlt |
|---|---|---|
| **B4.2.1** | 🔴 **10** | Kapitel über visuelle Qualität ohne visuelle Beispiele. Zwei nötig: datiert/zeitgemäß, echt/gekauft. **Kein reales Stockmotiv verwenden** |
| **B4.2.2** | 🔴 **11** | erster Bildschirmausschnitt klar/unklar — **wichtigste Abbildung von Teil II** |
| **B4.2.3** | 🔴 **6** | Seitenaufruf mit fremden Servern — macht das unsichtbare Thema sichtbar |
| **B4.2.4** | 🔴 **14** | Aufwand-Wirkung-Diagramm — natürliche Überleitung zu Kapitel 15 |
| **B4.2.5** | 15 | ABB 15.1 auf `ganz` aufwerten — sie trägt die Schlussaussage |
| **B4.2.6** | 1 | die sieben Fragen als Ablauf — Kandidat für die Umschlaginnenseite |
| **B4.2.7** | 2, 5, 7, 8, 9, 12, 13, 16, 17 | je ein bis zwei Kandidaten, in den Kapiteln benannt |
| **B4.2.8** | — | 🔴 **Gesamtdurchsicht der Abbildungsdichte** statt kapitelweiser Nachbesserung |

## B4.3 Regeln

| ID | Regel |
|---|---|
| **B4.3.1** | Keine Stockfotos, keine fremden Websites, keine fremden Oberflächen |
| **B4.3.2** | Alle Abbildungen schwarzweißfest — Unterscheidung über Form, nie über Farbe |
| **B4.3.3** | Buchsatz hält die eigenen Richtwerte ein: WCAG-Kontrast, Zeilenlänge 60–80 Zeichen |
| **B4.3.4** | Tabellenziffern — im Satzmuster als `tabular-nums` gesetzt ✓ |

---

# B5 · Lektorat — 34 Punkte

## B5.1 Die Schutzliste

**Sechzehn Stellen, an denen das Buch gegen das eigene Interesse argumentiert. Genau sie werden beim Kürzen zuerst gestrichen — und genau sie tragen die Glaubwürdigkeit.**

| Stelle | Was dort steht |
|---|---|
| **2.7** | Der Herausgeber baut selbst Websites — Interessenkonflikt offengelegt |
| **2.8** | „Sie brauchen den Online-Check nicht" |
| **8.6** | Die Lücke bei den Alternativtexten — „nutzen Sie sie nicht aus" |
| **9.2** | Warum die Kategorie von 15 auf 18 Punkte wuchs |
| **9.10** | KI-Systeme auszusperren ist eine legitime Entscheidung |
| **10.2** | Vorbehalt zu den Merkmalslisten — „keine Bewertungsregel" |
| **12 Abschluss** | Der Standard vollständig auf einer Doppelseite |
| **13.11** | „Ersetzen Sie Ihre eigenen Einschätzungen nicht" |
| **14.1** | „Diese Liste ist keine Statistik" |
| **14.7** | „Der teuerste Befund steht nicht auf dieser Liste" |
| **15.7** | Der Plan endet bei Gold und begründet, warum nicht weiter |
| **16.3** | Vollständige Aufzählung dessen, was nicht geprüft wird |
| **17.2** | „Zeitmangel ist kein Anlass zu beauftragen" |
| **17.8** | Der Schluss ohne Ausblick und ohne Aufforderung |
| **D.5** | Keine Bußgeldhöhen, keine Musterformulierungen |
| **1.1 / 15.10** | Die Betriebsmittel-Metapher — Aufstellung und Einlösung gehören zusammen |

## B5.2 Regeln

| ID | Regel |
|---|---|
| **B5.2.1** | Englische Fachbegriffe nur im Glossar als Verweis, nie in Kapitelüberschriften |
| **B5.2.2** | Nur drei Dateinamen im Fließtext ✓ **geprüft** |
| **B5.2.3** | Kein Satz, der eine Leistung des Herausgebers bewirbt — besonders Kapitel 17 |
| **B5.2.4** | Keine Prüfwerkzeuge namentlich |
| **B5.2.5** | Keine erfundenen Prozentzahlen zu Ladezeit und Absprung |
| **B5.2.6** | Die Interessenkonflikt-Offenlegung steht dreifach — das ist Absicht |

## B5.3 Zu entscheiden

| ID | Punkt |
|---|---|
| **B5.3.1** | Der Kasten „Wenn Sie nur zehn Minuten haben" in der Titelei — trägt er oder wirkt er werblich? |
| **B5.3.2** | Fachbegriffe LCP, CLS, INP in einer Marginalie? Wer selbst misst, sieht sie im Werkzeug |
| **B5.3.3** | Klassentabellen erscheinen in Kapitel 11 fünfmal — Ausklapptafel oder Wiederholung im Anhang? |
| **B5.3.4** | Trägt der Abgrenzungsabsatz in 2.12 / 3.9 zu E7? |
| **B5.3.5** | HSTS-Warnung in 6.6 — soll abschrecken, nicht lähmen |
| **B5.3.6** | Ausfüllfeld „Nächster Prüftermin" steht dreimal — Dopplung oder Absicht? |
| **B5.3.7** | Kapitel 5 hat 22 Seiten und eine Abbildung — beim Kürzen 5.10 vor 5.2 |
| **B5.3.8** | Sicherheitsheader bei technischem Namen nennen oder umschreiben? |

---

# B6 · Satz und Produktion — 5 Punkte

| ID | Aufgabe |
|---|---|
| **B6.1** | 🔴 **Vorlage 3 bekommt keine Passwortfelder** — Anweisung steht im Dateikommentar |
| **B6.2** | 🔴 **Vorlage 1 und 2 je auf eine Seite** — im Satz verifizieren |
| **B6.3** | BoD-Format 17 × 24 cm prüfen, sonst 17 × 22 |
| **B6.4** | Schriftlizenz ✓ **Noto ist SIL Open Font License** — Print und EPUB erlaubt |
| **B6.5** | Seitenzahl auf ein Vielfaches von 4, danach Rückenbreite |
| **B6.6** | Seitenzählung der Titelei: römisch oder arabisch |

---

# Reihenfolge

```
B1  Geschäftsführung        ← heute, 13 Entscheidungen, null Aufwand
B2  Anwaltstermin           ← ab sofort parallel, Anhang D mitschicken
B4.1 Manuel: Stufenmarken, Format, Ergebnisblatt   ← parallel
        ▼
B3.1 Nachziehen aus Block C ← sobald S1 bis S3 im Repo sind
        ▼
B4.2 Abbildungen            ← nach B1.1, weil der Umfang die Zahl bestimmt
        ▼
B5  Lektorat mit Schutzliste
        ▼
B6  Satz und Produktion
```

**Der Engpass ist B1.** Dreizehn Entscheidungen, null Arbeitszeit — und sie bestimmen den Umfang, die ISBN, den Satzbeginn und wie viele Abbildungen Manuel zeichnen muss.
