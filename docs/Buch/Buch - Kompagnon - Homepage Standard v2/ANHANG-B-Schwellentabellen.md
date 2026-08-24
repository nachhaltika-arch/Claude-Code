<!-- ERZEUGT aus audit_criteria.py — nicht von Hand ändern. -->
<!-- Erzeugt mit scripts/standard-export.py -->

# Anhang B — Der Katalog auf einen Blick

Fassung des Standards: **2026.2** · **39 Kriterien** in **8 Kategorien** · **103 Rohpunkte**

Alle Zahlen dieses Anhangs stammen aus dem Prüfkatalog der Software und sind nicht von Hand eingetragen. Weicht eine Angabe im Fließtext des Buchs von diesem Anhang ab, gilt dieser Anhang.

---

## B.1 Die fünf Stufen

| Ab Wert | Stufe |
|---|---|
| 95 | Homepage Standard Platin |
| 85 | Homepage Standard Gold |
| 70 | Homepage Standard Silber |
| 50 | Homepage Standard Bronze |
| 0 | Nicht konform |

Der Wert wird auf 0 bis 100 normiert: `erreichte Punkte ÷ anwendbare Punkte × 100`, kaufmännisch gerundet.

## B.2 Ihr anwendbares Maximum

| Klasse | Maximum |
|---|---|
| K1 | 103 |
| K2 | 103 |
| K3 | 103 |
| K4 | 100 |
| K5 | 103 |
| K6 | 81 |

## B.3 Die acht Kategorien

| Kap. | Kategorie | Codes | Punkte | Kriterien |
|---|---|---|---|---|
| 5 | Recht und Compliance | L1–L5 | 20 | 5 |
| 6 | Sicherheit und Datenschutz | S1–S4 | 10 | 4 |
| 7 | Ladezeit und Stabilität | P1–P5 | 15 | 5 |
| 8 | Barrierefreiheit | B1–B5 | 10 | 5 |
| 9 | Auffindbarkeit | E1–E7 | 18 | 7 |
| 10 | Gestaltung | D1–D5 | 10 | 5 |
| 11 | Nutzerführung und Anfragen | C1–C5 | 15 | 5 |
| 12 | Inhalt und Substanz | I1–I3 | 5 | 3 |
| | **Summe** | | **103** | **39** |

## B.4 Alle Kriterien im Einzelnen

### Recht und Compliance — 20 Punkte · Kapitel 5

| Code | Kriterium | P | Erhebung | Gilt für |
|---|---|---|---|---|
| **L1** | Impressum | 6 | gemessen | alle Klassen |
| **L2** | Datenschutzerklärung | 6 | gemessen | alle Klassen |
| **L3** | Einwilligung für Cookies und Tracking | 4 | gemessen | alle Klassen |
| **L4** | Barrierefreiheitserklärung | 2 | gemessen | alle Klassen |
| **L5** | Kontaktformular | 2 | gemessen | alle Klassen |

### Sicherheit und Datenschutz — 10 Punkte · Kapitel 6

| Code | Kriterium | P | Erhebung | Gilt für |
|---|---|---|---|---|
| **S1** | Verschlüsselungszertifikat | 3 | gemessen | alle Klassen |
| **S2** | Erzwungene Weiterleitung auf HTTPS | 2 | gemessen | alle Klassen |
| **S3** | Sicherheitsheader | 3 | gemessen | alle Klassen |
| **S4** | Fremde Dienste ohne Einwilligung | 2 | gemessen | alle Klassen |

### Ladezeit und Stabilität — 15 Punkte · Kapitel 7

| Code | Kriterium | P | Erhebung | Gilt für |
|---|---|---|---|---|
| **P1** | Ladezeit des Hauptinhalts | 4 | gemessen | alle Klassen |
| **P2** | Layoutstabilität | 3 | gemessen | alle Klassen |
| **P3** | Reaktionszeit auf Eingaben | 2 | gemessen | alle Klassen |
| **P4** | Mobiler Gesamtwert | 3 | gemessen | alle Klassen |
| **P5** | Bildoptimierung | 3 | gemessen | alle Klassen |

### Barrierefreiheit — 10 Punkte · Kapitel 8

| Code | Kriterium | P | Erhebung | Gilt für |
|---|---|---|---|---|
| **B1** | Gesamtwert der Barrierefreiheitsprüfung | 3 | gemessen | alle Klassen |
| **B2** | Farbkontraste | 2 | gemessen | alle Klassen |
| **B3** | Alternativtexte für Bilder | 2 | gemessen | alle Klassen |
| **B4** | Semantik und Struktur | 2 | gemessen | alle Klassen |
| **B5** | Tastaturbedienung | 1 | abgeleitet | alle Klassen |

### Auffindbarkeit — 18 Punkte · Kapitel 9

| Code | Kriterium | P | Erhebung | Gilt für |
|---|---|---|---|---|
| **E1** | Seitentitel und Kurzbeschreibung | 3 | gemessen | alle Klassen |
| **E2** | Überschriften und Textumfang | 2 | gemessen | alle Klassen |
| **E3** | Auffindbarkeit für Suchmaschinen | 3 | gemessen | alle Klassen |
| **E4** | Strukturierte Daten | 3 | gemessen | alle Klassen |
| **E5** | Lokale Signale | 3 | gemessen | K1, K2, K3, K5 |
| **E6** | Keine defekten Verweise | 1 | gemessen | alle Klassen |
| **E7** | Lesbarkeit für KI-Systeme | 3 | gemessen | alle Klassen |

### Gestaltung — 10 Punkte · Kapitel 10

| Code | Kriterium | P | Erhebung | Gilt für |
|---|---|---|---|---|
| **D1** | Visuelle Aktualität | 3 | Einschätzung | alle Klassen |
| **D2** | Typografie und Lesbarkeit | 2 | gemessen | alle Klassen |
| **D3** | Farbsystem und Konsistenz | 2 | Einschätzung | alle Klassen |
| **D4** | Bildqualität und Echtheit | 2 | Einschätzung | alle Klassen |
| **D5** | Mobile Darstellung | 1 | gemessen | alle Klassen |

### Nutzerführung und Anfragen — 15 Punkte · Kapitel 11

| Code | Kriterium | P | Erhebung | Gilt für |
|---|---|---|---|---|
| **C1** | Klarheit im ersten Bildschirmausschnitt | 3 | Einschätzung | alle außer K6 |
| **C2** | Die erwartete Hauptreaktion | 3 | abgeleitet | alle außer K6 |
| **C3** | Kontaktwege | 3 | gemessen | alle außer K6 |
| **C4** | Vertrauenssignale | 3 | abgeleitet | alle außer K6 |
| **C5** | Klarheit des Angebots | 3 | Einschätzung | alle außer K6 |

### Inhalt und Substanz — 5 Punkte · Kapitel 12

| Code | Kriterium | P | Erhebung | Gilt für |
|---|---|---|---|---|
| **I1** | Eigene Leistungsseiten | 2 | gemessen | alle außer K6 |
| **I2** | Aktualität | 1 | gemessen | alle Klassen |
| **I3** | Textqualität | 2 | Einschätzung | alle außer K6 |

## B.5 Die Ausschlusskriterien

Diese Befunde begrenzen die Stufe unabhängig von der Punktzahl.

| Befund | Höchste erreichbare Stufe |
|---|---|
| Kein erreichbares Impressum | Nicht konform |
| Keine erreichbare Datenschutzerklärung | Nicht konform |
| Kein gültiges Verschlüsselungszertifikat | Nicht konform |
| Tracking ohne Einwilligung | Bronze |
| Cookies vor der Einwilligung gesetzt | Bronze |

## B.6 Wie erhoben wird

| Erhebungsart | Kriterien | Punkte |
|---|---|---|
| gemessen | 30 | 81 |
| abgeleitet | 3 | 7 |
| Einschätzung | 6 | 15 |
| **Summe** | **39** | **103** |

## B.7 🔴 Was in diesem Anhang noch fehlt

**Die Punktabstufungen je Kriterium.** Sie stehen derzeit nicht als Daten im Katalog, sondern als Bedingungen im Bewertungscode und lassen sich deshalb nicht erzeugen. Sobald `BUCH-F1` sie überführt hat, erscheinen sie hier automatisch.

**Die deutschen Kriterienbezeichnungen** stehen derzeit im Skript statt im Katalog. Sie gehören als Feld `buch_label` an das Kriterium — sonst gibt es zwei Wahrheiten über denselben Namen.

**Bis dahin stehen die Abstufungen in den Kapiteln 5 bis 12** — dort von Hand aus dem Bewertungscode übertragen und damit ungeschützt gegen die nächste Änderung.
