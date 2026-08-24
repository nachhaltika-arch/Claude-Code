# Bewertungslogik — Homepage Standard 2026.2

**Ersetzt:** die Fassung vom 14.08.2026 vormittags (basierte auf dem alten
6-Kategorien-Katalog aus `AuditReport.jsx` und ist gegenstandslos).
**Baut auf:** `audit-anforderungen-2026-08-11.md` (Katalog gebaut, produktiv seit 13.08.)
**Ablage:** `docs/homepage-standard/bewertungslogik.md`
**Wahrheitsquelle im Code:** `services/audit_criteria.py`
**Stand:** 14.08.2026

---

## 0. Was dieses Dokument tut

Der Anforderungskatalog vom 11.08. hat den Bewertungskatalog neu gebaut und die acht
Defekte behoben. Was dort als Punkt 5 offen blieb — **die Ausweitung des Maßstabs über
das SHK-Handwerk hinaus** — wird hier spezifiziert.

Das Dokument beschreibt den vollständigen Bewertungsstand einschließlich der Erweiterung
und dient als Vorlage für das Buch „Der Homepage Standard". Bei Widersprüchen zum Code
gilt `services/audit_criteria.py`; Änderungen am Maßstab erfolgen hier zuerst.

**Die zentrale Abgrenzung, die aus dem Anforderungskatalog übernommen wird:**

> Die **Bewertung** wird auf alle akquirierenden Unternehmen ausgeweitet. Der **Verkauf**
> bleibt in der Nische der Phase 1 (Heizung, Sanitär, Elektrik, keine Erweiterung vor
> fünf produktiven Kunden).

Das ist kein Widerspruch, sondern die Auflösung: Das Audit-Widget ist ein Akquisekanal.
Es bewertet, was ihm vorgesetzt wird — fair und erkennbar sachkundig. Ob KOMPAGNON dem
Bewerteten anschließend ein Angebot macht, ist eine getrennte Entscheidung. Ein
Steuerberater, der einen fairen Bericht bekommt und daraufhin das Buch kauft, ist ein
guter Ausgang, auch ohne Website-Auftrag.

---

## 1. Der Katalog

<!-- ERZEUGT: gewichtung — nicht von Hand ändern, siehe scripts/standard-export.py -->

| # | Kategorie | P | Kriterien |
|---|---|---|---|
| 1 | Recht & Compliance | 20 | L1–L5 |
| 2 | Sicherheit & Datenschutz | 10 | S1–S4 |
| 3 | Performance & Core Web Vitals | 15 | P1–P5 |
| 4 | Barrierefreiheit (WCAG/BFSG) | 10 | B1–B5 |
| 5 | SEO & Auffindbarkeit | 18 | E1–E7 |
| 6 | Design & Gestaltung | 10 | D1–D5 |
| 7 | Conversion & Nutzerführung | 15 | C1–C5 |
| 8 | Inhalt & Substanz | 5 | I1–I3 |
| — | Infrastruktur-Befund | 0 | rein informativ |
| | **Summe** | **103** | 39 Kriterien |

<!-- /ERZEUGT: gewichtung -->

### Stufen

| Stufe | Score |
|---|---|
| Homepage Standard Platin | 95–100 |
| Homepage Standard Gold | 85–94 |
| Homepage Standard Silber | 70–84 |
| Homepage Standard Bronze | 50–69 |
| Nicht konform | 0–49 |

> **Zu prüfen:** Diese Schwellen stammen aus dem Anforderungskatalog § 3.3. Im
> Projektwissen tragen `AuditHook.jsx`, `audit-widget.html`, `CustomerDashboard.jsx`
> und `AuditHistory.jsx` weiterhin **85 / 70 / 50 / 30**. Läuft das Backend auf den
> neuen Schwellen und das Frontend auf den alten, zeigt derselbe Score im Bericht eine
> andere Stufe als im Widget. Das ist ein stiller Fehler mit direkter Außenwirkung.
> Siehe § 9, Prüfpunkt 1.

### K.-o.-Regeln (Level-Deckel)

| Verstoß | Deckel |
|---|---|
| Kein Impressum erreichbar | Nicht konform |
| Keine Datenschutzerklärung erreichbar | Nicht konform |
| Kein gültiges TLS-Zertifikat | Nicht konform |
| Tracking oder Schriften ohne Einwilligung | Bronze |
| Cookies gesetzt ohne Consent | Bronze |

Der Bericht weist die Deckelung mit Grund aus, nie nur die Stufe:

> „Nicht konform (rechnerisch 78 Punkte). Begrenzt, weil keine Datenschutzerklärung
> erreichbar ist."

### Quellen-Kennzeichnung

| Symbol | Bedeutung | Zählt in den Score |
|---|---|---|
| 🟢 gemessen | deterministisch über HTTP, DOM, TLS oder API | ja |
| 🟡 abgeleitet | aus gemessenen Werten nach fester Regel berechnet | ja |
| 🔵 Einschätzung | KI-Bewertung auf Screenshot/Text nach festem Rubric | ja, gekennzeichnet |
| ⚪ nicht erhoben | Prüfung nicht möglich | **nein — fällt aus Zähler und Nenner** |

---

## 2. Das Branchenmodell — die Erweiterung

### 2.1 Das Problem, das gelöst wird

Sieben Kriterien werden per KI gegen einen Maßstab bewertet: `cv_*` (Conversion),
`ih_textqualitaet` und Teile von `dg_*`. Bis zum 13.08. war dieser Maßstab fest auf SHK
verdrahtet. Am 14.08. wurde die **Erkennung** gebaut: Das Modell meldet `branche` und
`betriebsseite`, und bei `betriebsseite = false` fallen `cv_klarheit`, `cv_angebot` und
`ih_textqualitaet` aus der Wertung.

Damit ist der grobe Fehler behoben — ein Kandidatenauftritt wird nicht mehr gegen
Wärmepumpen gemessen. Was fehlt, ist die Zwischenstufe: **Eine Steuerkanzlei ist eine
Betriebsseite, aber ihr Maßstab ist nicht der eines Dachdeckers.** Heute wird sie gegen
den SHK-nahen Maßstab bewertet und verliert Punkte für Dinge, die in ihrer Branche falsch
wären — etwa einen Preisrahmen, dessen Nennung berufsrechtlich problematisch sein kann.

### 2.2 Die sechs Branchenklassen

Jede erkannte `branche` wird deterministisch auf genau eine Klasse abgebildet. Die Klasse
bestimmt den Maßstab der KI-Kriterien und die Anwendbarkeit einzelner Messkriterien.

| Klasse | Bezeichnung | Merkmal | Beispiele |
|---|---|---|---|
| **K1** | Lokaler Leistungsbetrieb | Leistung wird beim Kunden oder vor Ort erbracht, Einzugsgebiet | Handwerk aller Gewerke, Kfz, Garten- und Landschaftsbau, Reinigung, Pflegedienst |
| **K2** | Lokaler Beratungs- und Gesundheitsdienstleister | Termin- statt Auftragslogik, Qualifikation ist das Kaufargument, teils berufsrechtlich reglementiert | Arzt-, Zahnarzt-, Physiopraxis, Rechtsanwalt, Steuerberater, Architekt, Heilpraktiker |
| **K3** | Lokaler Publikumsbetrieb | Kunde kommt zum Anbieter, Öffnungszeiten und Sortiment entscheiden | Gastronomie, Einzelhandel, Friseur, Fitnessstudio, Hotel |
| **K4** | Überregionaler Anbieter | Kein Einzugsgebiet, Leistung remote oder bundesweit | Agentur, Unternehmensberatung, Softwareanbieter, B2B-Zulieferer, Coaching |
| **K5** | Onlineverkauf | Vertragsschluss oder Zahlung findet auf der Website statt | Shop, digitale Produkte, kostenpflichtige Buchung |
| **K6** | Keine Betriebsseite | Kein Unternehmen, das über die Seite Kunden gewinnt | Verein, Partei, Kandidat, Blog, Privatseite, Behörde |

**Kombination:** K5 ist mit K1–K4 kombinierbar. Ein Dachdecker mit Ersatzteilshop ist
K1+K5. Bei Kombination gelten die Kriterien beider Klassen; bei widersprüchlichem Maßstab
gilt die primäre Klasse.

### 2.3 Zuordnung — das Modell erkennt, der Code entscheidet

Das Prinzip aus § 7 des Anforderungskatalogs wird beibehalten und erweitert:

1. Das Modell meldet weiterhin `branche` als **Freitext** und `betriebsseite` als
   Boolean. Es wählt seinen Maßstab **nicht** selbst.
2. Der Code bildet `branche` über eine gepflegte Zuordnungstabelle
   (`services/audit_industry_map.py`) auf eine Klasse ab.
3. Greift keine Regel, gilt `betriebsseite = true` → **K1**, `betriebsseite = false` → **K6**.
4. Die zugeordnete Klasse wird im Bericht ausgewiesen und ist manuell korrigierbar. Eine
   Korrektur löst eine Neuberechnung ohne erneuten Seitenabruf aus.

**Warum eine Tabelle und kein zweiter Modellaufruf:** Die Klasse steuert die Bewertung.
Eine nicht deterministische Zuordnung würde bedeuten, dass dieselbe Website an zwei Tagen
gegen zwei Maßstäbe läuft. Damit wäre die Wiederholbarkeitsanforderung an einen Standard
verletzt.

**Zuordnungstabelle, Auszug:**

| Erkannte Branche enthält | Klasse |
|---|---|
| Heizung, Sanitär, Elektro, Dach, Maler, Zimmerei, Fliesen, Garten, Kfz, Schlosser, Tischler | K1 |
| Arzt, Praxis, Zahn, Physio, Anwalt, Kanzlei, Steuerberat, Notar, Architekt, Ingenieurbüro | K2 |
| Restaurant, Gastronomie, Café, Hotel, Friseur, Kosmetik, Einzelhandel, Laden, Studio | K3 |
| Agentur, Beratung, Consulting, Software, IT-Dienstleist, Coaching, Personalvermittlung | K4 |
| Shop, Onlinehandel, E-Commerce, Versand | K5 |
| Verein, Partei, Kandidat, Blog, Stiftung, Kirche, Behörde, privat | K6 |

Die Tabelle wird bei jedem unerwarteten Freitext ergänzt. Nicht zugeordnete Freitexte
werden geloggt, damit die Lücken sichtbar werden.

### 2.4 Anwendbarkeit nach Klasse

| Kriterium | K1 | K2 | K3 | K4 | K5 | K6 | Bemerkung |
|---|---|---|---|---|---|---|---|
| L1 Impressum | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | immer |
| L2 Datenschutzerklärung | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | immer |
| L3 Cookie-Consent | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | immer |
| L4 Barrierefreiheitserklärung | ○ | ○ | ○ | ○ | ○ | ○ | nur wenn BFSG anwendbar |
| L5 Formular DSGVO-konform | ○ | ○ | ○ | ○ | ○ | ○ | nur wenn Formular vorhanden |
| S1–S4 Sicherheit | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | immer |
| P1–P5 Performance | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | immer (⚪ ohne PSI-Key) |
| B1–B5 Barrierefreiheit | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | immer |
| E1 Title & Meta | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Maßstab klassenabhängig |
| E2 Heading & Content-Tiefe | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | immer |
| E3 Indexierbarkeit | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | immer |
| E4 Strukturierte Daten | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | erwarteter Typ klassenabhängig |
| E5 Lokale Signale | ✓ | ✓ | ✓ | ✗ | ○ | ✗ | K4/K6 nicht anwendbar |
| E6 Defekte Links | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | immer |
| D1–D5 Design | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **immer**, auch K6 |
| C1 Klarheit above the fold | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | K6 nicht anwendbar |
| C2 Primär-CTA | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | Zielhandlung klassenabhängig |
| C3 Kontaktwege | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | Erwartung klassenabhängig |
| C4 Vertrauenssignale | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | Signaltyp klassenabhängig |
| C5 Angebots-Klarheit | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | **Maßstab stark klassenabhängig** |
| I1 Eigene Leistungsseiten | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | Inhalt klassenabhängig |
| I2 Aktualität | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | immer |
| I3 Textqualität | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | K6 nicht anwendbar |

✓ anwendbar · ○ bedingt · ✗ nicht anwendbar (fällt aus Zähler und Nenner)

**Anwendbares Maximum je Klasse** (ohne bedingte Kriterien):

<!-- ERZEUGT: klassenmaxima — nicht von Hand ändern, siehe scripts/standard-export.py -->

| Klasse | Maximum | Nicht anwendbar |
|---|---|---|
| K1 | 103 | — |
| K2 | 103 | — |
| K3 | 103 | — |
| K4 | 100 | E5 (3 P) |
| K5 | 103 | — |
| K6 | 81 | E5, C1, C2, C3, C4, C5, I1, I3 (22 P) |

<!-- /ERZEUGT: klassenmaxima -->

---

## 3. Der Branchenmaßstab je Kriterium

Dies ist die eigentliche Arbeit der Ausweitung. Für jede Klasse wird definiert, **wogegen**
gemessen wird. Ablage als Datei: `services/audit_industry_profiles.py` bzw. als JSON, damit
das Rubric ohne Codeänderung erweiterbar ist.

### C1 — Klarheit above the fold (3 P)

Gemeinsame Anforderung: In fünf Sekunden ist erkennbar, **was** angeboten wird und **für
wen**. Klassenabhängig kommt hinzu:

| Klasse | Zusätzlich erwartet |
|---|---|
| K1 | Einsatzgebiet erkennbar (Ort oder Umkreis) |
| K2 | Fachgebiet und Zulassung/Qualifikation erkennbar |
| K3 | Standort und Öffnungszeiten oder Reservierungsmöglichkeit erkennbar |
| K4 | Zielkundensegment erkennbar (Branche, Unternehmensgröße), Ort ausdrücklich **nicht** erwartet |
| K5 | Sortimentsbereich und Versandbedingungen erkennbar |

### C2 — Primär-CTA (3 P)

| Klasse | Erwartete primäre Zielhandlung |
|---|---|
| K1 | Anfrage, Rückruf, Termin vor Ort, Notdienstnummer |
| K2 | Terminvereinbarung, Erstgespräch, Rückruf |
| K3 | Reservierung, Tischbuchung, Anfahrt, Anruf |
| K4 | Erstgespräch, Demo, Whitepaper, Kontaktformular |
| K5 | In den Warenkorb, Direktkauf |

Bewertet wird: Vorhandensein, ergebnisorientierte Formulierung („Termin sichern" statt
„Mehr erfahren"), Position im ersten sichtbaren Bereich, Wiederholung im Seitenverlauf.

### C3 — Kontaktwege (3 P)

| Klasse | Erwartung |
|---|---|
| K1 | Telefonnummer klickbar, Formular ≤ 5 Felder, Reaktionszeit benannt |
| K2 | Telefonnummer klickbar, Sprechzeiten oder Onlineterminbuchung |
| K3 | Telefonnummer klickbar, Öffnungszeiten strukturiert, Anfahrt/Karte |
| K4 | Formular oder Terminbuchung, benannte Ansprechperson |
| K5 | Kundenservice-Kontakt, Bestell- und Retourenweg erkennbar |

### C4 — Vertrauenssignale (3 P)

Mindestens zwei passende Signale der jeweiligen Klasse:

| Klasse | Zählende Signale |
|---|---|
| K1 | Meisterbrief, Innung, Herstellerpartnerschaften, Bewertungen, echte Objektfotos, Gründungsjahr |
| K2 | Kammerzugehörigkeit, Fachkunde/Schwerpunkte, Team mit Qualifikation, Bewertungen soweit berufsrechtlich zulässig |
| K3 | Bewertungen, Auszeichnungen, Fotos der Räumlichkeiten, Mitgliedschaften |
| K4 | Benannte Referenzkunden, Fallstudien mit Zahlen, Zertifizierungen, Team |
| K5 | Käuferbewertungen, Gütesiegel, Zahlungsarten, Rückgaberegelung sichtbar |

**Erkennbare Bildagenturmotive zählen in keiner Klasse als Vertrauenssignal.**

### C5 — Angebots-Klarheit (3 P)

Das Kriterium mit dem größten Klassenunterschied.

| Klasse | Erwartet | Ausdrücklich nicht erwartet |
|---|---|---|
| K1 | Leistungen konkret benannt, Ablauf beschrieben, Preisrahmen oder Kostenlogik, Garantie/Risk Reversal | — |
| K2 | Leistungsfelder konkret, Ablauf des Mandats/der Behandlung, Ersttermin-Erwartung | **Preisangaben** — berufsrechtlich teils unzulässig, Fehlen darf keinen Punktabzug bewirken |
| K3 | Sortiment oder Karte einsehbar, Preise, Öffnungszeiten | Ablaufbeschreibung |
| K4 | Leistungsmodule, Vorgehensmodell, Projektgrößen oder Investitionsrahmen | Ortsbezug |
| K5 | Produktangaben vollständig, Gesamtpreis inkl. USt, Versandkosten, Lieferzeit | — |

> **Diese Zeile ist der Grund für das gesamte Branchenmodell.** Eine Steuerkanzlei ohne
> Preisrahmen ist nicht schlechter, sondern berufsrechtlich korrekt. Sie dafür
> abzuwerten, macht den Bericht als Akquiseinstrument unbrauchbar — genau der Effekt, den
> der Kandidatenauftritt am 14.08. gezeigt hat.

### E1 — Title & Meta (3 P)

| Klasse | Erwartung im Title |
|---|---|
| K1, K2, K3 | Leistung **und** Ort |
| K4 | Leistung und Zielsegment, **kein** Ort erwartet |
| K5 | Sortiment/Marke, kein Ort erwartet |

### E4 — Strukturierte Daten (3 P)

| Klasse | Erwarteter Haupttyp | Zusätzlich |
|---|---|---|
| K1 | `LocalBusiness` oder spezifischer Untertyp | `Service`, `FAQPage` |
| K2 | `LocalBusiness` / `MedicalBusiness` / `LegalService` | `Person` für Berufsträger |
| K3 | `Restaurant`, `Store`, `LodgingBusiness` | `OpeningHoursSpecification`, `Menu` |
| K4 | `Organization` | `Service`, `Article` |
| K5 | `Organization` + `Product` + `Offer` | `AggregateRating` |
| K6 | `Organization` oder `Person` | — |

### E7 — Lesbarkeit für KI-Systeme (3 P)

**Klassenunabhängig.** Ob ein Sprachmodell die Seite lesen darf, hängt nicht am Gewerk.
Gemessen wird zweierlei, und die Gewichtung sagt, was schwerer wiegt:

| Teil | Punkte | Gemessen an |
|---|---|---|
| Kein KI-Crawler ausgesperrt | 2 | `robots.txt` |
| `llms.txt` vorhanden | 1 | Abruf unter `/llms.txt` |

Wer GPTBot aussperrt, ist für ChatGPT nicht vorhanden — das wiegt schwerer als eine
fehlende `llms.txt`, die kaum eine Seite hat. Fehlen **beide** Erhebungen, wird das
Kriterium übersprungen und zählt in keinem der beiden Brüche mit.

### I1 — Eigene Leistungsseiten (2 P)

| Klasse | Erwartung |
|---|---|
| K1 | Je Gewerk oder Hauptleistung eine eigene Seite statt einer Sammelseite |
| K2 | Je Rechtsgebiet, Fachgebiet oder Behandlungsschwerpunkt eine Seite |
| K3 | Sortiment, Speisekarte oder Leistungsübersicht als eigene Seite |
| K4 | Je Leistungsmodul eine Seite, zusätzlich Fallstudien |
| K5 | Kategorieseiten mit eigenem Text, nicht nur Produktlisten |

### I3 — Textqualität (2 P)

Klassenunabhängig: Kundennutzen statt Selbstbeschreibung, keine Worthülsen, konkrete statt
generischer Aussagen. Der Bezugspunkt für „Kundennutzen" ist die Zielgruppe der Klasse.

### D1–D5 — Design

**Klassenunabhängig.** Typografie, Farbsystem, Bildqualität, visuelle Aktualität und
mobile Darstellung gelten für jede Website, unabhängig davon, wer dahintersteht. Das ist
bereits so gebaut (§ 7 des Anforderungskatalogs) und bleibt.

---

## 4. Was aus dem Conversion-Spec in den Maßstab wandert

`docs/conversion-spec-shk.md` ist heute die Grundlage der Conversion-Bewertung — und sie
ist SHK-spezifisch. Für die Ausweitung wird sie in zwei Teile getrennt:

| Teil | Neuer Ort | Inhalt |
|---|---|---|
| **Allgemeine Conversion-Prinzipien** | `docs/conversion-spec-core.md` | Klarheit, ein Primärziel, Kontaktwege, Vertrauen, Angebotstransparenz — gilt für K1–K5 |
| **Branchenausprägung** | `docs/conversion-spec-{k1..k5}.md` | Was die Prinzipien in dieser Klasse konkret bedeuten |

Die im Code-Audit vom 04.05. benannten fünf Conversion-Lücken bleiben gültig, werden aber
klassenabhängig:

| Lücke aus dem Code-Audit | Klassenzuordnung |
|---|---|
| Wertebox mit EUR-Positionen und Anker | K1, K4, K5 — bei K2 berufsrechtlich prüfen, bei K3 durch Karte/Sortiment ersetzt |
| Fallstudien-Card-Template | K1 (Objekt, Baujahr, Ergebnis), K4 (Kunde, Ausgangslage, Ergebnis), K2 (anonymisierte Mandatsbeispiele) |
| Dynamische Stichtage (BAFA/GEG) | nur K1 und nur bei förderfähigen Gewerken — kein allgemeines Kriterium |
| Sekundär-CTAs (WhatsApp, Click-to-Call, PDF-Magnet) | K1–K3 stark, K4 als Whitepaper, K5 als Newsletter |
| Vorher/Nachher-Fotos | K1, K3 — bei K2 datenschutzrechtlich meist ausgeschlossen |

**Wichtig für die Bewertung:** Diese fünf Punkte sind Anforderungen an das, was KOMPAGNON
**baut**, nicht Bewertungskriterien des Standards. Sie fließen in C4 und C5 als
Beispielausprägungen ein, nicht als eigene Punkte. Sonst bewertet der Standard, ob eine
Website nach KOMPAGNON-Methode gebaut wurde — das wäre kein Standard mehr, sondern eine
Verkaufsvorlage.

---

## 5. Infrastruktur-Befund (0 Punkte)

Rein informativ, dient der Aufwandsschätzung im Angebot:

CMS und Tech-Stack · Hosting-Provider über ASN · CDN aktiv · HTTP/2 oder /3 · Domain-Alter ·
Erreichbarkeit und Antwortzeit · **erkanntes Tracking (GA4, Meta Pixel, Matomo, keins)**.

Der letzte Punkt ist neu und ergibt sich aus dem Code-Audit vom 04.05.: Für die
Angebotskalkulation ist entscheidend, ob ein Kunde heute überhaupt messbar ist. Er gehört
aber **nicht** in die Bewertung — eine Website ohne Tracking ist nicht schlechter für ihre
Besucher.

**Ausdrücklich entfallen:** „Backup-Hinweise erkennbar" — von außen nicht prüfbar.

---

## 6. GEO — fünf Prüfpunkte, kein Punktwert

Frühere Fassungen nannten hier einen „GEO-Wert (0–10)". **Den gibt es nicht** — weder im
Katalog noch im Bericht. Gerechnet wurde er nie; die Zahl stand nur in diesem Dokument.
Was es gibt, ist eine eigene Seite im Bericht mit fünf Prüfpunkten
(`services/pdf_kataloge.py::geo_pruefpunkte`):

| Prüfpunkt | Erhoben | Fließt in die Wertung |
|---|---|---|
| `llms.txt` vorhanden | ja | E7 (1 P) |
| `robots.txt` KI-freundlich | ja | E7 (2 P) |
| Strukturierte Daten | ja | E4 (3 P) |
| KI-Erwähnungen | **nein** | — |
| Google AI Overview | **nein** | — |

Die letzten beiden bleiben im Bericht, damit der Leser weiß, dass es sie gibt — aber ohne
Behauptung: Sie bekommen den Status „unbekannt" und **keine** Empfehlung. Ein früherer
Stand druckte für jeden der fünf Punkte eine Aufforderung, auch „GPTBot nicht blockieren"
an einen Betrieb, dessen `robots.txt` niemanden sperrt.

Die Trennung „GEO steht außerhalb der Wertung" gilt damit **nicht mehr vollständig**: Seit
E7 im Katalog steht, sind zwei der drei erhobenen Prüfpunkte Teil der 103 Punkte. Außerhalb
bleibt, was sich zu schnell ändert für einen Standard, der über Jahre vergleichbar sein
soll — und für ein gedrucktes Buch: Erwähnungen in Modellen und Sichtbarkeit in AI
Overviews. Beides ist nicht reproduzierbar messbar und wäre in einem Buch ein Jahr später
falsch.

---

## 7. Ausgabeformat (Ergänzungen)

```json
{
  "standard_version": "2026.2",
  "branche": "Steuerberatung mit Schwerpunkt Handwerk",
  "branchenklasse": "K2",
  "branchenklasse_quelle": "map",
  "betriebsseite": true,
  "rohpunkte": 71,
  "anwendbares_maximum": 98,
  "gesamtscore": 72,
  "stufe": "Homepage Standard Silber",
  "stufe_begrenzt_durch": null,
  "kriterien": {
    "cv_angebot": {
      "punkte": 2, "max": 3, "quelle": "einschaetzung",
      "massstab": "K2",
      "befund": "Leistungsfelder konkret benannt, Ablauf des Mandats fehlt. Preisangaben werden bei dieser Branchenklasse nicht erwartet."
    },
    "se_lokal": {
      "punkte": 3, "max": 3, "quelle": "gemessen"
    }
  },
  "collection_notes": {
    "branchenmassstab": "K2 — Lokaler Beratungs- und Gesundheitsdienstleister"
  }
}
```

**Der Bericht nennt die Klasse im ersten Absatz.** Der Leser muss erkennen, dass sein
Geschäft verstanden wurde, bevor er die Punktzahl sieht. Das ist bei einem Akquisekanal
wichtiger als jedes Einzelkriterium.

---

## 8. Auswirkung auf das Buch

Das Buchmanuskript muss angepasst werden. Betroffen:

| Kapitel | Änderung |
|---|---|
| 1 | „Recht mit 30 Punkten" → 20 Punkte; Schadensprinzip-Argument bleibt, Zahlen ändern sich |
| 2 | **vollständig neu** — 8 statt 6 Kategorien, neue Gewichtung, K.-o.-Regeln, Quellen-Kennzeichnung, Branchenklassen |
| 3–8 | Kapitelzuschnitt folgt jetzt 8 Kategorien statt 6 |
| 9 | Selbsttest: 38 Kriterien statt 27, Branchenklasse als erster Schritt |

**Neue Kapitelstruktur:**

| Kapitel | Inhalt | Seiten |
|---|---|---|
| 1 | Warum Ihre Website kein Prospekt ist | 12 |
| 2 | Das Bewertungssystem und Ihre Branchenklasse | 14 |
| 3 | Recht & Compliance (20 P) | 22 |
| 4 | Sicherheit & Datenschutz (10 P) | 12 |
| 5 | Performance & Core Web Vitals (15 P) | 18 |
| 6 | Barrierefreiheit (10 P) | 12 |
| 7 | SEO & Auffindbarkeit (15 P) | 18 |
| 8 | Design & Gestaltung (10 P) | 14 |
| 9 | Conversion & Nutzerführung (15 P) | 18 |
| 10 | Inhalt & Substanz (5 P) | 8 |
| 11 | Der Selbsttest in 120 Minuten | 16 |
| 12 | Die 20 häufigsten Fehler | 12 |
| 13 | Der 30-Tage-Maßnahmenplan | 12 |
| 14 | Grenzen des Selbermachens | 8 |
| A | Anhang | 12 |
| | **Summe** | **~208** |

Die Kapitel „Design" und „Conversion" sind der eigentliche Gewinn: Genau das sind die
beiden Dinge, die der Leser auf seiner Seite sieht — und die kein vergleichbares Fachbuch
messbar macht.

---

## 9. Zu prüfen, bevor weitergebaut wird

| # | Prüfpunkt | Warum | Befehl / Ort |
|---|---|---|---|
| 1 | **Stufenschwellen Frontend vs. Backend** | Backend 95/85/70/50, Frontend laut Projektwissen 85/70/50/30 → derselbe Score zeigt zwei Stufen | `grep -rn "85\|70\|50\|30" frontend/src/components/AuditHook.jsx frontend/public/embed/audit-widget.html` |
| 2 | **Ist der Umbau auf dem Arbeitsbranch?** | Doc sagt `main`, Arbeitsregel sagt Feature-Branch. Projektwissen zeigt alten Katalog im Frontend | `git diff main staging --stat` |
| 3 | **Zeigt das Frontend die 8 Kategorien?** | `AuditReport.jsx`, `CustomerDashboard.jsx`, `HomepageChecklist.jsx` tragen im Projektwissen den alten 6er-Katalog | `grep -n "rc_score\|bf_score\|max: 30" frontend/src/` |
| 4 | **PageSpeed-Key auf Render gesetzt?** | Offener Punkt 1 aus § 6 des Anforderungskatalogs. Ohne Key sind 15 Punkte dauerhaft ⚪ | Render → Environment |
| 5 | **Lauf gegen 3 echte fremde Websites** | Offener Punkt 4 — der Katalog ist nie gegen reale Seiten gelaufen | manuell |
| 6 | **Quellen-Kennzeichnung im Report sichtbar?** | Schritt 7 unverifiziert. Ohne sie ist der ganze Umbau für den Leser unsichtbar | Bericht öffnen |

**Punkt 5 zuerst.** Ein Katalog, der nie gegen eine fremde Seite gelaufen ist, ist eine
Hypothese. Drei Läufe gegen reale Websites aus drei verschiedenen Branchenklassen zeigen
in einer Stunde mehr als jede weitere Spezifikation.

---

## 10. Umsetzungsreihenfolge der Ausweitung

| # | Schritt | Aufwand |
|---|---|---|
| 1 | `audit_industry_map.py` — Zuordnungstabelle Freitext → Klasse, mit Logging nicht zugeordneter Werte | S |
| 2 | `audit_industry_profiles.py` — Rubric je Klasse für C1–C5, E1, E4, I1 | M |
| 3 | `audit_criteria.py` — Anwendbarkeitsmatrix je Klasse ergänzen | S |
| 4 | `audit_ai.py` — Rubric der erkannten Klasse in den Prompt einsetzen statt festem SHK-Text | M |
| 5 | `audit_scoring.py` — Klassenabhängige Anwendbarkeit in Zähler/Nenner | S |
| 6 | Report: Klasse im ersten Absatz, Korrekturmöglichkeit, Neuberechnung ohne Neuabruf | M |
| 7 | `conversion-spec-shk.md` in Core + fünf Klassendateien aufteilen | M |

**Ein Schritt pro Commit, Render-Logs prüfen, dann der nächste.**

---

## 11. Offene Entscheidungen

| # | Frage | Tragweite |
|---|---|---|
| 1 | Wird `trade` aus den Stammdaten mit der erkannten `branche` abgeglichen und zurückgeschrieben? | Heute laufen beide auseinander (§ 7 Schlussabsatz) |
| 2 | Bleibt der Verkauf in der SHK-Nische, während die Bewertung alle Klassen abdeckt? | Empfehlung: ja — sonst verwässert Phase 1 |
| 3 | Buchtitel: branchenoffen oder Handwerk im Titel? | Bei branchenoffener Bewertung ist ein Handwerk-Titel nicht mehr haltbar |
| 4 | Werden Bestandsaudits nach 2026.1 neu berechnet? | Empfehlung: nein, Versionsstempel und Trennlinie im Verlauf |
| 5 | Wird K2 anwaltlich zur Preisangabe geprüft? | Betrifft die Aussage in C5 und im Buch |
