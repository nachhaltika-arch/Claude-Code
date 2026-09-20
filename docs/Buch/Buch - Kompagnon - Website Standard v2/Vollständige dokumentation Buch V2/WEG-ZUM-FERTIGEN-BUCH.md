# DER WEG ZUM FERTIGEN BUCH

**Stand:** 24.08.2026
**Zweck:** Ein Pfad mit Toren statt einer Liste ohne Ende

---

## Warum es sich bisher wie Hüpfen anfühlt

Wir haben 153 offene Punkte in zwei Listen. **Listen enden nicht** — es kommt immer einer dazu, und jeder erledigte Punkt fühlt sich an wie ein Schritt an einer Stelle, die niemand vermisst hätte.

**Was fehlt, sind drei Dinge:**

1. **Eine Definition von „fertig".** Ohne sie ist jede Frage „sind wir fertig?" unbeantwortbar.
2. **Phasen mit Toren.** Ein Tor ist eine prüfbare Bedingung, nach der eine Phase abgeschlossen ist und nicht wieder aufgemacht wird.
3. **Ein kritischer Pfad.** Von 153 Punkten bestimmen etwa acht das Enddatum. Die übrigen laufen nebenher oder sind egal.

Dieser Plan liefert alle drei.

---

# TEIL 1 · Was „fertig" heißt

**Das Buch ist fertig, wenn diese neun Aussagen zutreffen. Nicht acht.**

| # | Bedingung | Prüfbar durch |
|---|---|---|
| 1 | Jede Zahl im Buch stammt aus dem Kriterienkatalog der Software | `test_buch_stimmt_mit_code.py` ist grün |
| 2 | Kein Kriterienhinweis verspricht mehr, als gemessen wird | BEFUND C1 abgearbeitet, Nachprüfung leer |
| 3 | Alle vierzehn Rechtsaussagen sind anwaltlich freigegeben | schriftliche Freigabe liegt vor |
| 4 | Die Häufigkeit der zwanzig Befunde ist erhoben | C7-Auswertung mit Grundgesamtheit und Zeitraum |
| 5 | Jede Abbildung ist gezeichnet, schwarzweißfest und rechtefrei | Abbildungsliste vollständig abgehakt |
| 6 | Der Satz steht, Seitenzahl ist durch 4 teilbar | Umbruch freigegeben |
| 7 | Zwei Korrekturdurchgänge sind gelaufen, der zweite ohne Befund | Korrekturprotokoll |
| 8 | Die drei gedruckten Adressen sind erreichbar und liefern das Richtige | von Hand geprüft, an einem fremden Gerät |
| 9 | Das Belegexemplar von BoD ist geprüft und freigegeben | unterschrieben |

**Bedingung 8 ist die, die am ehesten übersehen wird.** Sie muss am gedruckten Buch geprüft werden, nicht am Manuskript — und an einem Gerät, das die Seiten noch nie geladen hat.

---

# TEIL 2 · Fünf Phasen

```
        ┌─────────────────────────────────────────────┐
   0    │ FUNDAMENT — die Software liefert die Zahlen │  4 Arbeitstage
        └─────────────────────┬───────────────────────┘
                    TOR 0: Drift-Test grün
        ┌─────────────────────▼───────────────────────┐
   1    │ MANUSKRIPT — inhaltlich abgeschlossen       │  6 Arbeitstage
        └─────────────────────┬───────────────────────┘
                    TOR 1: keine roten Autorenpunkte
        ┌─────────────────────▼───────────────────────┐
   2    │ PRÜFUNG — Recht und Fachlektorat            │  4–8 Wochen
        └─────────────────────┬───────────────────────┘
                    TOR 2: Freigaben schriftlich
        ┌─────────────────────▼───────────────────────┐
   3    │ GESTALTUNG UND SATZ                        │  6–10 Wochen
        └─────────────────────┬───────────────────────┘
                    TOR 3: Umbruch freigegeben
        ┌─────────────────────▼───────────────────────┐
   4    │ PRODUKTION                                 │  3–4 Wochen
        └─────────────────────┬───────────────────────┘
                    TOR 4: Belegexemplar freigegeben
                              ▼
                         ERSCHEINEN
```

---

## PHASE 0 · Fundament

**Eingangsbedingung:** Katalogsumme entschieden ✅ (103, BEFUND C4)

| # | Aufgabe | Wer | Tage |
|---|---|---|---|
| 0.1 | **S1 — die beiden Lighthouse-Gruppen anschließen** | Technik | 0,5 |
| 0.2 | S2 — Deklarationen richtigstellen | Technik | 0,25 |
| 0.3 | S3 — zwölf Kriterienhinweise kürzen | Technik | 0,5 |
| 0.4 | S4 — Spezifikation nachziehen, Verfahrensfrage entscheiden | Technik | 0,5 |
| 0.5 | `BUCH-F0` und `F0b` | Technik | 0,25 |
| 0.6 | `BUCH-F1` — Abstufungen in Daten | Technik | 0,5 |
| 0.7 | `BUCH-F2` — Export, plus `buch_code` und `buch_label` | Technik | 1 |
| 0.8 | `BUCH-F3` — Drift-Wächter | Technik | 0,5 |

### 🚪 TOR 0

☐ `test_buch_stimmt_mit_code.py` ist grün
☐ Der Export erzeugt alle Tabellen für Teil II und Anhang B
☐ Der Wächter wird bei einer künstlichen Änderung nachweislich rot
☐ Jeder Kriterienhinweis stimmt mit dem überein, was gemessen wird

**Wird dieses Tor nicht sauber geschlossen, kommt jede Zahl im Buch später noch einmal in Bewegung.**

---

## PHASE 1 · Manuskript

**Eingangsbedingung:** Tor 0 geschlossen

| # | Aufgabe | Wer | Tage |
|---|---|---|---|
| 1.1 | Alle erzeugten Tabellen einsetzen — Teil II, Anhang B, Kapitel 13 | Autor | 1 |
| 1.2 | Kapitel 8.7 um Sprachauszeichnung und Labels erweitern | Autor | 0,5 |
| 1.3 | Kapitel 10.6 von Einschätzung auf Messung umstellen | Autor | 0,5 |
| 1.4 | Erhebungsarten neu zählen — 3.4, 12, 2.7 | Autor | 0,25 |
| 1.5 | Die neun gekürzten Hinweise im Buch nachziehen | Autor | 0,5 |
| 1.6 | § 5 DDG statt TMG durchziehen | Autor | 0,25 |
| 1.7 | Doppelwertungen einordnen — 9.8, 11.7 | Autor | 0,25 |
| 1.8 | **C7 einarbeiten, Kapiteltitel 14 zurückholen** | Autor | 1 |
| 1.9 | **Fall Elektro Hansen durch einen realen ersetzen** | Autor | 1 |
| 1.10 | Selbsttest an zwei Personen erproben, Dauer messen | Autor | 0,5 |
| 1.11 | Beide Kontrollrechnungen nachziehen — Kapitel 12 und 15.7 | Autor | 0,25 |

### 🚪 TOR 1

☐ Kein roter Autorenpunkt mehr offen
☐ Alle Verweise zeigen auf existierende Abschnitte
☐ Beide Kontrollrechnungen gehen auf
☐ Der Selbsttest wurde von zwei Personen durchgeführt, die Dauer steht im Kapiteltitel
☐ Der Drift-Test ist weiterhin grün

**Ab hier wird am Text nur noch korrigiert, nicht mehr entwickelt.**

---

## PHASE 2 · Prüfung

**Eingangsbedingung:** Tor 1 geschlossen — der Anwalt bekommt ein fertiges Manuskript, kein bewegliches
**Vorlauf: Termin ab sofort vereinbaren, unabhängig von Tor 1**

| # | Aufgabe | Wer | Dauer |
|---|---|---|---|
| 2.1 | **Anwaltstermin** — Anhang D als Vorlage, vierzehn Aussagen | Recht | 2–6 Wochen Vorlauf |
| 2.2 | Buchpreisbindung für den E-Book-Eigenverkauf | Recht | im selben Termin |
| 2.3 | Fachlektorat der Liste in 16.3 — von jemandem, der Websites **betreibt** | extern | 1 Woche |
| 2.4 | Schlusslektorat mit der Schutzliste | Lektorat | 2 Wochen |
| 2.5 | Rechtsstand eintragen | Autor | 5 Minuten |

### 🚪 TOR 2

☐ Schriftliche Freigabe für alle vierzehn Rechtsaussagen
☐ Entscheidung zum Einwilligungsfeld (B2.3) getroffen und im Buch abgebildet
☐ Kammerangabe geklärt — Code oder Spezifikation angepasst
☐ Lektorat abgeschlossen, Schutzliste unangetastet
☐ Rechtsstand steht in Anhang D und in der Titelei

---

## PHASE 3 · Gestaltung und Satz

**Eingangsbedingung:** Tor 1 geschlossen — Abbildungen können vor Tor 2 beginnen
**Das ist die längste Phase und bestimmt das Enddatum.**

| # | Aufgabe | Wer | Dauer |
|---|---|---|---|
| 3.1 | **Stufenmarken zuerst** — sie kehren im ganzen Buch wieder | Manuel | 1 Tag |
| 3.2 | Farbentscheidung nach BoD-Kalkulation für 284 Seiten | GF | 1 Woche |
| 3.3 | **46 Abbildungen** — Briefings liegen vor | Manuel | **4–6 Wochen** |
| 3.4 | Satzmuster-Format übernehmen, Ergebnisblatt auf eine Seite | Manuel | 1 Tag |
| 3.5 | **Satz 284 Seiten** | Satz | 2–3 Wochen |
| 3.6 | Erster Korrekturdurchgang | Autor + Lektorat | 1 Woche |
| 3.7 | Zweiter Korrekturdurchgang | Autor | 3 Tage |
| 3.8 | Seitenzahl auf ein Vielfaches von 4 bringen | Satz | 1 Tag |
| 3.9 | Cover, Rückenbreite nach endgültiger Seitenzahl | Manuel | 3 Tage |

### 🚪 TOR 3

☐ Alle Abbildungen gezeichnet, schwarzweißfest, keine Stockmotive, keine fremden Websites
☐ Umbruch steht, Seitenzahl durch 4 teilbar
☐ Zweiter Korrekturdurchgang **ohne Befund**
☐ Rückenbreite berechnet, Cover fertig
☐ Vorlage 1 und 2 passen je auf eine Seite

---

## PHASE 4 · Produktion

**Eingangsbedingung:** Tor 2 und Tor 3 geschlossen

| # | Aufgabe | Wer | Dauer |
|---|---|---|---|
| 4.1 | **Drei Seiten unter `homepage-standard.de` anlegen** | Technik | 2 Tage |
| 4.2 | PDF-Fassung von Prüfliste und Vorlagen erzeugen | Technik | 1 Tag |
| 4.3 | QR-Codes mit Kapitelparameter erzeugen und einsetzen | Satz | 1 Tag |
| 4.4 | **Adressen am fremden Gerät prüfen** | GF | 1 Stunde |
| 4.5 | ISBN und VLB-Eintrag | Verlag | 2 Wochen |
| 4.6 | BoD-Upload, Belegexemplar | Verlag | 2 Wochen |
| 4.7 | Belegexemplar prüfen und freigeben | GF | 3 Tage |

### 🚪 TOR 4

☐ Alle drei Adressen liefern das Richtige, geprüft am fremden Gerät
☐ QR-Codes führen zum Ziel, Kapitelparameter kommen an
☐ Belegexemplar geprüft: Farbe, Rückenbreite, Bindung, Lesbarkeit im Bund
☐ ISBN und VLB-Eintrag stimmen mit der Titelei überein

---

# TEIL 3 · Der kritische Pfad

**Von 153 offenen Punkten bestimmen acht das Enddatum.**

```
Anwaltstermin vereinbaren  ──────────┐ 2–6 Wochen Vorlauf
                                     │
S1–S4 + F0–F3  ──── 4 Tage ──────────┤
                                     │
Manuskript nachziehen ── 6 Tage ─────┤
                                     │
C7 erheben ──────────── 1 Tag ───────┤
                                     ▼
                        46 ABBILDUNGEN  4–6 Wochen  ◄── längster Einzelposten
                                     │
                        SATZ  2–3 Wochen
                                     │
                        KORREKTUR  1,5 Wochen
                                     │
                        BoD  4 Wochen
                                     ▼
                              ERSCHEINEN
```

| Die acht Posten | Dauer |
|---|---|
| 1 · Anwaltstermin (Vorlauf) | 2–6 Wochen, **läuft parallel** |
| 2 · S1 bis S4 im Repo | 2 Tage |
| 3 · `BUCH-F1` bis `F3` | 2 Tage |
| 4 · C7 erheben | 1 Tag |
| 5 · Manuskript nachziehen | 6 Tage |
| 6 · **46 Abbildungen** | **4–6 Wochen** |
| 7 · Satz und zwei Korrekturen | 4 Wochen |
| 8 · BoD und Belegexemplar | 4 Wochen |

**Realistisch: vier bis fünf Monate ab Start von Phase 0**, wenn Manuel die Abbildungen neben anderer Arbeit zeichnet.

**Der einzige Posten, der das spürbar verkürzt, ist Nummer 6.** Alles andere ist bereits knapp gerechnet.

---

# TEIL 4 · Was ab heute parallel läuft

**Diese vier hängen an nichts und blockieren nichts. Sie kosten Vorlauf, wenn sie liegenbleiben.**

| | Aufgabe | Wer | Warum jetzt |
|---|---|---|---|
| **1** | **Anwaltstermin vereinbaren** | GF | 2–6 Wochen Vorlauf. Anhang D ist die fertige Vorlage |
| **2** | **BoD-Kalkulation für 284 Seiten**, einfarbig und vierfarbig | GF | Entscheidet über Farbe und Preis, blockiert 46 Abbildungen |
| **3** | **ISBN und Verlagsnummer bei MVB** | GF | Untertitel steht, Umfang steht |
| **4** | **Stufenmarken zeichnen** | Manuel | Sie kehren im ganzen Buch wieder — alles andere baut darauf auf |

---

# TEIL 5 · Drei Dinge, die den Plan kippen können

**1 · C7 ergibt etwas anderes als erwartet.**
Wenn die Auswertung zeigt, dass die zwanzig ausgewählten Befunde **nicht** die zwanzig häufigsten sind, muss die Auswahl geändert werden — nicht der Titel behalten. **Wirkung: Kapitel 14 wird neu geschrieben, eine Woche.**
*Vorbeugung: C7 in Phase 0 erheben, nicht in Phase 1.*

**2 · Der Anwalt beanstandet das Einwilligungsfeld (B2.3).**
Dann bewertet der Standard ein Kriterium, dessen Rechtsgrundlage nicht trägt. **Wirkung: Kriterium L5 ändert sich, damit die Katalogsumme, damit der Untertitel — und der ist nach der ISBN-Meldung eingefroren.**
*Vorbeugung: **Die ISBN erst nach Tor 2 beantragen, nicht vorher.** Das widerspricht Punkt 3 in Teil 4 — und Tor 2 gewinnt.*

**3 · Die Abbildungen dauern länger als sechs Wochen.**
Der wahrscheinlichste Fall, weil 46 eine große Zahl ist und Manuel nicht nur daran arbeitet.
*Vorbeugung: **Nach den ersten fünf Abbildungen die Zeit messen und hochrechnen.** Wenn es nicht reicht, jetzt entscheiden, welche zwanzig unverzichtbar sind — nicht in Woche fünf.*

---

# TEIL 6 · Was ich korrigiere

**Teil 4 Punkt 3 und Teil 5 Punkt 2 widersprechen sich, und ich habe es beim Schreiben gemerkt.**

Ich hatte die ISBN unter „läuft ab heute parallel" gesetzt. Das ist falsch: **Wenn der Anwalt L5 beanstandet, ändert sich die Katalogsumme und damit der Untertitel — und der steht in der ISBN-Meldung.**

**Richtig ist: ISBN erst nach Tor 2.** Der Vorlauf von zwei Wochen ist in Phase 4 eingeplant und passt dorthin. Was heute schon geht, ist die **Verlagsnummer** — sie hängt an keinem Titel.

| | Wann |
|---|---|
| Verlagsnummer bei MVB | **ab heute** |
| Zwei ISBN beantragen | **nach Tor 2** |

---

# Die nächsten fünf Arbeitstage

| Tag | Was | Wer |
|---|---|---|
| **1** | Anwaltstermin vereinbaren · BoD-Kalkulation anfragen · Verlagsnummer beantragen | GF |
| **1** | Stufenmarken zeichnen | Manuel |
| **1–2** | S1 bis S4 im Repo | Technik |
| **3** | C7 erheben | Technik |
| **3–4** | `BUCH-F1` und `F2` | Technik |
| **5** | `BUCH-F3` — **Tor 0 schließen** | Technik |

**Nach fünf Arbeitstagen ist Tor 0 geschlossen und Phase 1 kann beginnen.** Danach ist der Weg zum ersten Mal geradeaus.
