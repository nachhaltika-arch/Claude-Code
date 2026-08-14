---
kapitel: 11
titel: "Der Selbsttest"
punkte: null
status: entwurf-fertig
zuletzt_geprueft: 2026-08-14
standard_version: "2026.2"
---

# 11. Der Selbsttest

## 11.1 Bevor Sie beginnen

Dieses Kapitel führt Sie durch alle 38 Kriterien. Am Ende haben Sie eine Punktzahl, eine
Stufe und eine Liste dessen, was zu tun ist.

**Was Sie brauchen:**

- Ihre Website
- einen Rechner mit Browser
- Ihr Mobiltelefon
- eine Person, die Ihren Betrieb nicht kennt — für fünf Minuten in Block C
- etwa zwei Stunden

**Nehmen Sie sich die Zeit am Stück.** Ein zwischen zwei Terminen begonnener Selbsttest
wird nicht zu Ende geführt, und ein halber Test ist wertlos.

### Die vier Blöcke

| Block | Inhalt | Wo | Dauer |
|---|---|---|---|
| **A** | Messwerte erheben | Rechner | 20 Min |
| **B** | Recht und Technik prüfen | Rechner | 35 Min |
| **C** | Darstellung und Führung prüfen | Telefon | 40 Min |
| **D** | Inhalt prüfen und auswerten | Rechner | 25 Min |

Block A sammelt zuerst alle Zahlen, die Sie in den Blöcken danach brauchen. Das spart
Zeit — Sie öffnen jedes Werkzeug nur einmal.

### Zwei Regeln für den ganzen Test

> **Die Ehrlichkeitsregel.** Schwanken Sie zwischen zwei Punktwerten, nehmen Sie den
> niedrigeren. Sie machen diesen Test nicht, um sich ein gutes Gefühl zu verschaffen.
>
> **Die Unbestimmt-Regel.** Können Sie ein Kriterium nicht prüfen, tragen Sie **U** ein
> statt 0. U-Kriterien werden am Ende aus dem Maximum herausgerechnet — sie zählen weder
> für noch gegen Sie. Das ist derselbe Grundsatz, nach dem auch das Audit arbeitet
> (Abschnitt 2.2).

---

## 11.2 Schritt 0 — Ihre Branchenklasse

Beantworten Sie der Reihe nach, hören Sie beim ersten Ja auf:

| # | Frage | Bei Ja |
|---|---|---|
| 1 | Gewinnen Sie über diese Website überhaupt Kunden für eine Leistung? **Nein?** | **K6** |
| 2 | Kann man auf Ihrer Website kaufen oder verbindlich bezahlt buchen? | **K5** (zusätzlich zu 3–6) |
| 3 | Ist Ihre Leistung **nicht** an ein Einzugsgebiet gebunden? | **K4** |
| 4 | Kommt der Kunde in Ihre Räume, entscheiden Öffnungszeiten und Sortiment? | **K3** |
| 5 | Ist Ihre Berufsqualifikation das Kaufargument und Ihr Beruf reglementiert? | **K2** |
| 6 | Sonst | **K1** |

> ### **Meine Branchenklasse: __________**

**Was das für Sie ändert:**

| Ihre Klasse | Entfällt | Ihr Ausgangsmaximum |
|---|---|---|
| K1, K2, K3 | — | 100 |
| K4 | E5 (3 P) | 97 |
| K5 | ggf. E5 | 97–100 |
| K6 | E5, C1–C5, I1, I3 (21 P) | 79 |

---

## 11.3 Block A — Messwerte erheben · 20 Minuten

Öffnen Sie nacheinander diese fünf Prüfungen und tragen Sie die Werte ein. Sie brauchen
sie später.

### A1 · Ladezeit und Barrierefreiheit

Googles PageSpeed Insights aufrufen, Adresse eingeben, **Ansicht für Mobilgeräte** wählen.

| Wert | Ihr Ergebnis |
|---|---|
| Gesamtbewertung Leistung (mobil) | ______ /100 |
| Largest Contentful Paint (LCP) | ______ s |
| Cumulative Layout Shift (CLS) | ______ |
| Interaction to Next Paint (INP) | ______ ms · ☐ nicht verfügbar |
| Total Blocking Time (Ersatz für INP) | ______ ms |
| Gesamtbewertung Barrierefreiheit | ______ /100 |

Messen Sie zweimal und nehmen Sie den mittleren Wert. Notieren Sie sich außerdem aus den
Empfehlungen, ob „Bilder in modernen Formaten" oder „Bilder richtig dimensionieren"
aufgeführt sind.

### A2 · Fremdverbindungen

Privates Browserfenster öffnen, Startseite aufrufen, **nichts anklicken**. F12 drücken,
Reiter „Netzwerk", Seite neu laden.

| Frage | Ihr Ergebnis |
|---|---|
| Fremde Domains kontaktiert (nicht Ihre eigene)? | ______ Stück |
| Welche? | ____________________________ |
| Darunter Schriftarten, Karten, Videos, Statistik? | ☐ ja ☐ nein |

Diese Liste brauchen Sie in Block B gleich dreimal.

### A3 · Auffindbarkeit

Bei Google eingeben: `site:ihredomain.de`

| Frage | Ihr Ergebnis |
|---|---|
| Wie viele Seiten werden angezeigt? | ______ |
| Wie viele Seiten hat Ihre Website? | ______ |

### A4 · Verschlüsselung und Header

- `http://ihredomain.de` aufrufen — springt es auf https? ☐ ja ☐ nein
- `http://www.ihredomain.de` aufrufen — springt es auf https? ☐ ja ☐ nein
- Auf das Schloss klicken — Zertifikat gültig bis: ____________
- Einen Sicherheitsheader-Prüfdienst aufrufen (Suche: „Security Header Check")

| Header | gesetzt |
|---|---|
| Strict-Transport-Security | ☐ |
| Content-Security-Policy | ☐ |
| X-Frame-Options | ☐ |
| X-Content-Type-Options | ☐ |

### A5 · Defekte Verweise und strukturierte Daten

- Prüfdienst für defekte Verweise aufrufen (Suche: „Broken Link Checker"):
  defekte interne Verweise: ______
- Prüfdienst für strukturierte Daten aufrufen (Suche: „Schema Markup Validator"):
  gefunden? ☐ nein ☐ ja, Typ: ____________ ☐ fehlerfrei

---

## 11.4 Block B — Recht und Technik · 35 Minuten

### Kategorie 1 · Recht & Compliance — 20 Punkte

| Code | Kriterium | So prüfen | Max | Punkte |
|---|---|---|---|---|
| L1 | Impressum | Drei Unterseiten öffnen: überall verlinkt? Pflichtangaben vollständig (Tabelle 3.3)? | 6 | ____ |
| L2 | Datenschutzerklärung | Alle Bestandteile vorhanden? Jeder Dienst aus A2 genannt? Kein nicht genutzter? | 6 | ____ |
| L3 | Einwilligung | Dialog vorhanden? Ablehnen gleichwertig? Lädt aus A2 etwas vor der Antwort? | 4 | ____ |
| L4 | Barrierefreiheitserklärung | Nur wenn **kein** Kleinstunternehmen. Sonst: **—** | 2 | ____ |
| L5 | Kontaktformular | Verschlüsselt, Datenschutzhinweis am Formular, keine unnötigen Pflichtfelder. Kein Formular: **—** | 2 | ____ |
| | | **Zwischensumme** | **20** | ____ |

### Kategorie 2 · Sicherheit & Datenschutz — 10 Punkte

| Code | Kriterium | So prüfen | Max | Punkte |
|---|---|---|---|---|
| S1 | Zertifikat | Aus A4. Gültig, beide Adressvarianten, keine Warnung auf dem Telefon | 3 | ____ |
| S2 | Weiterleitung | Aus A4. Beide Varianten springen auf https | 2 | ____ |
| S3 | Sicherheitsheader | Aus A4: 4 Header = 3 P · 3 = 2 P · 2 = 1 P · ≤1 = 0 P | 3 | ____ |
| S4 | Drittanbieter | Aus A2: keine = 2 P · 1–2 ohne Drittland = 1 P · sonst 0 P | 2 | ____ |
| | | **Zwischensumme** | **10** | ____ |

### Kategorie 3 · Performance — 15 Punkte

Alle Werte aus A1.

| Code | Kriterium | Schwellen | Max | Punkte |
|---|---|---|---|---|
| P1 | LCP | ≤2,5 s = 4 · ≤3,0 = 3 · ≤4,0 = 2 · ≤5,0 = 1 · >5,0 = 0 | 4 | ____ |
| P2 | CLS | ≤0,10 = 3 · ≤0,15 = 2 · ≤0,25 = 1 · >0,25 = 0 | 3 | ____ |
| P3 | INP / Ersatzwert | ≤200 ms = 2 · ≤500 (bzw. 600) = 1 · darüber 0 | 2 | ____ |
| P4 | Mobilbewertung | ≥90 = 3 · ≥70 = 2 · ≥50 = 1 · <50 = 0 | 3 | ____ |
| P5 | Bildoptimierung | Moderne Formate · feste Maße und verzögertes Laden · kein Bild >300 KB — je 1 P | 3 | ____ |
| | | **Zwischensumme** | **15** | ____ |

### Kategorie 5 · SEO — 15 Punkte (Teil 1)

| Code | Kriterium | So prüfen | Max | Punkte |
|---|---|---|---|---|
| E1 | Titel und Kurzbeschreibung | Vier Registerkarten öffnen: vier verschiedene Titel? Länge passend? Klassenaufbau (Tabelle 7.4)? | 3 | ____ |
| E3 | Auffindbarkeit | Aus A3. Kommt gar nichts → **0 Punkte**, unabhängig vom Rest | 3 | ____ |
| E4 | Strukturierte Daten | Aus A5. Passender Typ für Ihre Klasse (Tabelle 7.7)? | 3 | ____ |
| E6 | Defekte Verweise | Aus A5. Keine = 1 P · mindestens einer = 0 P | 1 | ____ |

*(E2 und E5 folgen in Block D.)*

---

## 11.5 Block C — Am Telefon · 40 Minuten

**Legen Sie den Rechner beiseite.** Dieser Block wird vollständig auf dem Mobiltelefon
durchgeführt, über Mobilfunk statt WLAN, in einem privaten Browserfenster.

### Zuerst: der Fünf-Sekunden-Test

Holen Sie die Person, die Ihren Betrieb nicht kennt. Startseite öffnen, Telefon hinhalten,
bis fünf zählen, umdrehen. Dann fragen:

| Frage | Antwort der Testperson |
|---|---|
| Was macht diese Firma? | ______________________ |
| Für wen? | ______________________ |
| Wo? *(nur K1, K2, K3)* | ______________________ |

Dieses Ergebnis brauchen Sie gleich bei C1.

### Kategorie 4 · Barrierefreiheit — 10 Punkte

| Code | Kriterium | So prüfen | Max | Punkte |
|---|---|---|---|---|
| B1 | Automatisierte Prüfung | Aus A1: ≥90 = 3 · ≥75 = 2 · ≥60 = 1 · <60 = 0 | 3 | ____ |
| B2 | Farbkontraste | Draußen im Tageslicht lesen. Alles mühelos lesbar? | 2 | ____ |
| B3 | Alternativtexte | Am Rechner: hat jedes Bild einen sinnvollen Text? Dekoratives leer? | 2 | ____ |
| B4 | Semantik und Struktur | Eine H1 · Hierarchie ohne Sprünge · Sprache ausgezeichnet · Formularfelder beschriftet — 4 = 2 P · 3 = 1 P · ≤2 = 0 P | 2 | ____ |
| B5 | Tastaturbedienung | Am Rechner, Maus weglegen, Tabulatortaste: Fokus sichtbar? Keine Falle? | 1 | ____ |
| | | **Zwischensumme** | **10** | ____ |

### Kategorie 6 · Design & Gestaltung — 10 Punkte

| Code | Kriterium | So prüfen | Max | Punkte |
|---|---|---|---|---|
| D1 | Visuelle Aktualität | Alterungsmerkmale aus Tabelle 8.4 zählen: 0–1 = 3 P · 2 = 2 P · 3–4 = 1 P · ≥5 = 0 P — gezählt: ____ | 3 | ____ |
| D2 | Typografie | ≤2 Schriftfamilien · klare Größenstaffelung · Zeilenlänge · kein Blocksatz — 4 = 2 P · 3 = 1 P · ≤2 = 0 P | 2 | ____ |
| D3 | Farbsystem | Begrenzte Palette · konsequent verwendet · Akzentfarbe nur für Handlungen — 3 = 2 P · 2 = 1 P · ≤1 = 0 P | 2 | ____ |
| D4 | Bildqualität | Eigene Bilder · technisch einwandfrei · einheitliche Bildsprache — 3 = 2 P · 2 = 1 P · ≤1 = 0 P | 2 | ____ |
| D5 | Mobile Darstellung | Jede Seite: nach rechts wischen — bewegt sich etwas? Überlappt etwas? | 1 | ____ |
| | | **Zwischensumme** | **10** | ____ |

### Kategorie 7 · Conversion & Nutzerführung — 15 Punkte

> **Bei Klasse K6 entfällt diese Kategorie vollständig.** Tragen Sie „—" ein.

| Code | Kriterium | So prüfen | Max | Punkte |
|---|---|---|---|---|
| C1 | Klarheit oben | Fünf-Sekunden-Test oben. Alle Fragen beantwortet = 3 P · eine offen = 2 P · zwei offen = 1 P · nur Firmenname = 0 P | 3 | ____ |
| C2 | Handlungsaufforderung | Genau ein Hauptziel, oben, ergebnisorientiert, wiederholt (Tabelle 9.5) | 3 | ____ |
| C3 | Kontaktwege | Nummer antippen — wählt es? · zweiter Weg schlank? · Reaktionszeit genannt? — je 1 P | 3 | ____ |
| C4 | Vertrauenssignale | Klassenpassende Belege zählen (Tabelle 9.7): ≥3 = 3 P · 2 = 2 P · 1 = 1 P · 0 = 0 P | 3 | ____ |
| C5 | Klarheit des Angebots | Erwartete Elemente Ihrer Klasse (Tabelle 9.8). **K2: Preisangabe wird nicht erwartet** | 3 | ____ |
| | | **Zwischensumme** | **15** | ____ |

**Zusatzprüfung ohne Punkte, aber wichtig:** Schicken Sie sich über Ihr eigenes Formular
eine Anfrage. Kommt sie an? ☐ ja ☐ nein ☐ im Spam-Ordner

---

## 11.6 Block D — Inhalt und Auswertung · 25 Minuten

### Kategorie 5 · SEO — Teil 2

| Code | Kriterium | So prüfen | Max | Punkte |
|---|---|---|---|---|
| E2 | Überschriften und Tiefe | Nur Überschriften lesen — ergibt das eine Gliederung? Leistungsseite: Wortzahl ______ | 2 | ____ |
| E5 | Lokale Signale | Nur K1, K2, K3. Kontaktdaten im Fuß jeder Seite · Ortsbezug oben · zeichengleich mit Impressum — je 1 P. **K4, K6: —** | 3 | ____ |
| | | **Zwischensumme Kategorie 5** | **15** | ____ |

### Kategorie 8 · Inhalt & Substanz — 5 Punkte

| Code | Kriterium | So prüfen | Max | Punkte |
|---|---|---|---|---|
| I1 | Eigene Leistungsseiten | Ihre 3–5 Hauptleistungen: je eine eigene Seite mit eigenem Titel? **K6: —** | 2 | ____ |
| I2 | Aktualität | Jahreszahl im Fuß · keine überholten Angaben · kein verwaister Neuigkeitenbereich | 1 | ____ |
| I3 | Textqualität | Wir-Test und Wettbewerbertest aus 10.6. **K6: —** | 2 | ____ |
| | | **Zwischensumme** | **5** | ____ |

---

## 11.7 Die Ausschlusskriterien

Bevor Sie rechnen: Prüfen Sie diese fünf Punkte. Sie wirken **unabhängig von Ihrer
Punktzahl**.

| Befund | Zutreffend? | Höchste Stufe dann |
|---|---|---|
| Impressum nicht erreichbar | ☐ | Nicht konform |
| Datenschutzerklärung nicht erreichbar | ☐ | Nicht konform |
| Kein gültiges Verschlüsselungszertifikat | ☐ | Nicht konform |
| Tracking oder Schriften ohne Einwilligung geladen | ☐ | Bronze |
| Cookies gesetzt ohne Einwilligung | ☐ | Bronze |

**Ist eines angekreuzt, notieren Sie es hier — es ist Ihre wichtigste Aufgabe:**

______________________________________________________________________

---

## 11.8 Die Auswertung

### Schritt 1 · Punkte zusammenzählen

| Kategorie | Max | Nicht anwendbar (—) | Unbestimmt (U) | **Anwendbar** | **Erreicht** |
|---|---|---|---|---|---|
| 1 Recht & Compliance | 20 | ____ | ____ | ____ | ____ |
| 2 Sicherheit & Datenschutz | 10 | ____ | ____ | ____ | ____ |
| 3 Performance | 15 | ____ | ____ | ____ | ____ |
| 4 Barrierefreiheit | 10 | ____ | ____ | ____ | ____ |
| 5 SEO & Auffindbarkeit | 15 | ____ | ____ | ____ | ____ |
| 6 Design & Gestaltung | 10 | ____ | ____ | ____ | ____ |
| 7 Conversion | 15 | ____ | ____ | ____ | ____ |
| 8 Inhalt & Substanz | 5 | ____ | ____ | ____ | ____ |
| **Gesamt** | **100** | ____ | ____ | **____** | **____** |

**Anwendbar** = 100 minus alle mit „—" und alle mit „U" bewerteten Punkte.

### Schritt 2 · Umrechnen

```
Ihr Ergebnis = erreichte Punkte ÷ anwendbare Punkte × 100
```

> **____ ÷ ____ × 100 = ______ Punkte**

### Schritt 3 · Stufe ablesen

| Stufe | Punkte | Ihre Stufe |
|---|---|---|
| Homepage Standard Platin | 95–100 | ☐ |
| Homepage Standard Gold | 85–94 | ☐ |
| Homepage Standard Silber | 70–84 | ☐ |
| Homepage Standard Bronze | 50–69 | ☐ |
| Nicht konform | 0–49 | ☐ |

**Wenn Sie in 11.7 etwas angekreuzt haben:** Ihre Stufe ist gedeckelt. Notieren Sie beides —
die rechnerische Punktzahl und die tatsächliche Stufe. Der Unterschied ist Ihre wichtigste
Kennzahl, weil er zeigt, wie viel eine einzige Korrektur bewirkt.

> **Rechnerisch: ______ Punkte · Tatsächliche Stufe: ______________**
> **Begrenzt durch: __________________________________________**

### Zwei Rechenbeispiele

**Beispiel 1 — Elektrobetrieb, Klasse K1.** Alle Kriterien anwendbar und prüfbar.
Erreicht: 76. Anwendbar: 100.
`76 ÷ 100 × 100 = 76` → **Silber.**

**Beispiel 2 — IT-Beratung, Klasse K4.** E5 entfällt (3 Punkte). INP nicht verfügbar und
kein Ersatzwert ermittelbar (2 Punkte als U).
Erreicht: 71. Anwendbar: 100 − 3 − 2 = 95.
`71 ÷ 95 × 100 = 74,7` → gerundet **75 Punkte** → **Silber.**

Ohne Umrechnung wären es 71 Punkte gewesen — und damit knapp Bronze. Das ist der Grund für
die Rechnung: Es wäre falsch, einen Betrieb dafür abzuwerten, dass ein Kriterium für ihn
nicht gilt.

---

## 11.9 Ihr Ergebnisblatt

Tragen Sie hier ein, was Sie in Kapitel 13 brauchen. Die Prozentwerte machen sichtbar, wo
Sie stehen — eine Kategorie mit 40 Prozent verdient Ihre Aufmerksamkeit mehr als eine mit
85, auch wenn dort absolut mehr Punkte fehlen.

| Kategorie | Erreicht / Anwendbar | Prozent | Balken (je 10 % ein Kästchen) |
|---|---|---|---|
| 1 Recht | ____ / ____ | ____ % | ☐☐☐☐☐☐☐☐☐☐ |
| 2 Sicherheit | ____ / ____ | ____ % | ☐☐☐☐☐☐☐☐☐☐ |
| 3 Performance | ____ / ____ | ____ % | ☐☐☐☐☐☐☐☐☐☐ |
| 4 Barrierefreiheit | ____ / ____ | ____ % | ☐☐☐☐☐☐☐☐☐☐ |
| 5 SEO | ____ / ____ | ____ % | ☐☐☐☐☐☐☐☐☐☐ |
| 6 Design | ____ / ____ | ____ % | ☐☐☐☐☐☐☐☐☐☐ |
| 7 Conversion | ____ / ____ | ____ % | ☐☐☐☐☐☐☐☐☐☐ |
| 8 Inhalt | ____ / ____ | ____ % | ☐☐☐☐☐☐☐☐☐☐ |

**Datum des Tests:** ____________  **Branchenklasse:** ______  **Ergebnis:** ______ Punkte

### Ihre fünf größten Lücken

Tragen Sie die fünf Kriterien ein, bei denen Sie am meisten Punkte verloren haben — nicht
die mit der niedrigsten Punktzahl, sondern die mit der größten Differenz zum Maximum.

| # | Code | Kriterium | Fehlende Punkte |
|---|---|---|---|
| 1 | ____ | ______________________ | ____ |
| 2 | ____ | ______________________ | ____ |
| 3 | ____ | ______________________ | ____ |
| 4 | ____ | ______________________ | ____ |
| 5 | ____ | ______________________ | ____ |

---

## 11.10 Wie es weitergeht

**Wenn Sie in 11.7 etwas angekreuzt haben:** Beginnen Sie dort. Ein Ausschlusskriterium zu
beheben kostet selten mehr als einen halben Tag und hebt Sie um zwei bis drei Stufen. Alles
andere hat Zeit.

**Wenn nicht:** Blättern Sie zu Kapitel 12. Dort stehen die zwanzig Fehler, die uns am
häufigsten begegnen — mit hoher Wahrscheinlichkeit finden Sie Ihre Lücken aus 11.9 dort
wieder, samt Behebung. Anschließend führt Kapitel 13 Ihre Punkte in eine Reihenfolge über.

**Ein Hinweis zum Wiederholen:** Legen Sie dieses ausgefüllte Kapitel ab und tragen Sie
sich in zwölf Monaten eine Erinnerung ein. Der zweite Durchgang dauert etwa halb so lange —
und der Vergleich der beiden Ergebnisblätter ist aussagekräftiger als jede einzelne
Momentaufnahme.

---

> ### Das Wichtigste aus diesem Kapitel
>
> - **Vier Blöcke, zwei Stunden.** Block A sammelt alle Messwerte auf einmal, danach wird
>   nur noch bewertet.
> - **Bestimmen Sie zuerst Ihre Branchenklasse** — sie entscheidet über Ihr anwendbares
>   Maximum.
> - **Im Zweifel den niedrigeren Wert.** Und was Sie nicht prüfen können, wird **U**, nicht
>   0.
> - **Prüfen Sie die fünf Ausschlusskriterien getrennt.** Sie wirken unabhängig von der
>   Punktzahl.
> - **Umrechnen nicht vergessen:** erreicht ÷ anwendbar × 100.
> - **Der Fünf-Sekunden-Test braucht eine fremde Person.** Ohne sie ist er wertlos.

---

## Redaktionelle Anmerkungen (nicht drucken)

**Dieses Kapitel ist die Kontrollinstanz für alle vorherigen.** Jede Schwelle in den
Tabellen muss zeichengenau mit den Kapiteln 3 bis 10 übereinstimmen. Vorschlag für die
Produktion: Die Tabellen aus 11.4 bis 11.6 **automatisch aus `homepage-standard.json`
generieren** statt sie zu pflegen — genau wie in `BUCH-01` vorgesehen. Sonst laufen
Kapitel und Selbsttest bei der ersten Änderung auseinander, und der Leser rechnet nach.

**Format prüfen.** Dieses Kapitel enthält Ausfüllfelder und ist damit das einzige, dessen
Nutzen von der gedruckten Fassung abhängt. Für die PDF-Ausgabe sollte geprüft werden, ob
die Felder als ausfüllbare Formularfelder angelegt werden — das erhöht den Wert der
digitalen Ausgabe erheblich und ist mit der Build-Pipeline aus `BUCH-03` machbar.

**Zusätzliches Verkaufsargument:** Ein separates Arbeitsblatt als Download (Kapitel 11 auf
sechs Seiten, ohne Erklärtext) wäre ein naheliegender Bonus zum Buch — und ein Anlass, die
E-Mail-Adresse des Käufers ein zweites Mal zu berühren.

**Zu prüfen — B3 und B5 stehen in Block C, werden aber am Rechner geprüft.** Das ist ein
Bruch im Ablauf. Alternativen: entweder in Block B verschieben (dann ist die
Kategorienlogik durchbrochen) oder im Text deutlicher als „kurz zurück an den Rechner"
kennzeichnen. **Empfehlung:** so lassen und beim Satz optisch hervorheben, weil die
Kategorienordnung für das Nachschlagen wichtiger ist als die Geräteordnung.

**Rechenbeispiel 2 gegenprüfen**, sobald die Rundungsregel im Code feststeht: `71 ÷ 95 ×
100 = 74,74`, hier auf 75 gerundet. Ob der Code kaufmännisch rundet oder abschneidet,
entscheidet in Grenzfällen über die Stufe. Im Buch muss dieselbe Regel stehen.

**Abbildungen (2 Stück):**
1. Der Ablaufplan der vier Blöcke als Zeitleiste
2. Das ausgefüllte Ergebnisblatt am Beispiel des Elektrobetriebs — als Vorbild, wie es
   aussehen soll
