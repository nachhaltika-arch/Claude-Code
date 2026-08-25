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

## B.7 Wie die Punkte je Kriterium vergeben werden

Diese Tabellen stammen aus derselben Quelle wie die Bewertung. Was hier steht, entscheidet über die Punkte — nicht eine Beschreibung davon.

### Recht und Compliance

**L1 · Impressum — 6 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +3 | Die Impressumsseite ist erreichbar |
| +3 | Die geprüften Pflichtangaben sind vollständig — zählt nur, wenn die Seite erreichbar ist |

**L2 · Datenschutzerklärung — 6 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +3 | Die Datenschutzerklärung ist erreichbar |
| +3 | Die geprüften Pflichtinhalte sind vorhanden — zählt nur, wenn die Seite erreichbar ist |

**L3 · Einwilligung für Cookies und Tracking — 4 Punkte**

| Punkte | Bedingung |
|---|---|
| 4 | Ein Consent-Werkzeug ist erkannt — oder es ist kein einwilligungspflichtiger Dienst eingebunden |
| 0 | Einwilligungspflichtige Dienste ohne erkanntes Consent-Werkzeug |

**L4 · Barrierefreiheitserklärung — 2 Punkte**

| Punkte | Bedingung |
|---|---|
| 2 | Eine Erklärung zur Barrierefreiheit ist verlinkt |
| 0 | Es ist keine Erklärung zur Barrierefreiheit verlinkt |

**L5 · Kontaktformular — 2 Punkte**

| Punkte | Bedingung |
|---|---|
| 2 | Jedes gefundene Formular hat ein Einwilligungsfeld |
| 1 | Mindestens ein Formular hat ein Einwilligungsfeld, aber nicht jedes |
| 0 | Kein Formular hat ein Einwilligungsfeld |

### Sicherheit und Datenschutz

**S1 · Verschlüsselungszertifikat — 3 Punkte**

| Punkte | Bedingung |
|---|---|
| 3 | Das Zertifikat ist gültig und läuft nicht in Kürze ab |
| 2 | Das Zertifikat ist gültig, läuft aber in Kürze ab |
| 0 | Es gibt kein gültiges Zertifikat |

**S2 · Erzwungene Weiterleitung auf HTTPS — 2 Punkte**

| Punkte | Bedingung |
|---|---|
| 2 | Der Aufruf über http wird auf https weitergeleitet |
| 0 | Der Aufruf über http wird nicht weitergeleitet |

**S3 · Sicherheitsheader — 3 Punkte**

Anteilig: Der gemessene Anteil wird auf 3 Punkte umgerechnet und kaufmännisch gerundet.

**S4 · Fremde Dienste ohne Einwilligung — 2 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +1 | Es sind keine Schriften von fremden Servern eingebunden |
| +1 | Es läuft kein Trackingdienst ohne erkanntes Consent-Werkzeug |

### Ladezeit und Stabilität

**P1 · Ladezeit des Hauptinhalts — 4 Punkte**

| Punkte | Bedingung |
|---|---|
| 4 | Der Hauptinhalt steht in weniger als 2,5 Sekunden |
| 2 | Der Hauptinhalt steht in 2,5 bis unter 4,0 Sekunden |
| 0 | Der Hauptinhalt braucht 4,0 Sekunden oder länger |

**P2 · Layoutstabilität — 3 Punkte**

| Punkte | Bedingung |
|---|---|
| 3 | Der Layoutverschiebungswert liegt unter 0,1 |
| 1 | Der Layoutverschiebungswert liegt bei 0,1 bis unter 0,25 |
| 0 | Der Layoutverschiebungswert liegt bei 0,25 oder darüber |

**P3 · Reaktionszeit auf Eingaben — 2 Punkte**

| Punkte | Bedingung |
|---|---|
| 2 | Die Reaktionszeit liegt unter 200 Millisekunden |
| 1 | Die Reaktionszeit liegt bei 200 bis unter 500 Millisekunden |
| 0 | Die Reaktionszeit liegt bei 500 Millisekunden oder darüber |

**P4 · Mobiler Gesamtwert — 3 Punkte**

| Punkte | Bedingung |
|---|---|
| 3 | Mobiler Gesamtwert 90 oder höher |
| 2 | Mobiler Gesamtwert 70 bis 89 |
| 1 | Mobiler Gesamtwert 50 bis 69 |
| 0 | Mobiler Gesamtwert unter 50 |

**P5 · Bildoptimierung — 3 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +1 | Mindestens die Hälfte der Bilder liegt in einem modernen Format vor |
| +1 | Mindestens die Hälfte der Bilder wird verzögert geladen |
| +1 | Mindestens vier Fünftel der Bilder tragen Größenangaben, und kein Bild ist überdimensioniert |

### Barrierefreiheit

**B1 · Gesamtwert der Barrierefreiheitsprüfung — 3 Punkte**

| Punkte | Bedingung |
|---|---|
| 3 | Der Barrierefreiheitswert liegt bei 90 oder höher |
| 2 | Der Barrierefreiheitswert liegt bei 75 bis 89 |
| 1 | Der Barrierefreiheitswert liegt bei 50 bis 74 |
| 0 | Der Barrierefreiheitswert liegt unter 50 |

**B2 · Farbkontraste — 2 Punkte**

Anteilig: Der gemessene Anteil wird auf 2 Punkte umgerechnet und kaufmännisch gerundet.

**B3 · Alternativtexte für Bilder — 2 Punkte**

| Punkte | Bedingung |
|---|---|
| 2 | Mindestens 95 von 100 Inhaltsbildern haben einen Alternativtext |
| 1 | 80 bis unter 95 von 100 Inhaltsbildern haben einen Alternativtext |
| 0 | Weniger als 80 von 100 Inhaltsbildern haben einen Alternativtext |

**B4 · Semantik und Struktur — 2 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +1 | Genau eine Hauptüberschrift und eine Hierarchie ohne Sprünge |
| +1 | Sprachauszeichnung und Formularbeschriftungen sind vollständig |

**B5 · Tastaturbedienung — 1 Punkt**

Anteilig: Der gemessene Anteil wird auf 1 Punkt umgerechnet und kaufmännisch gerundet.

### Auffindbarkeit

**E1 · Seitentitel und Kurzbeschreibung — 3 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +1 | Ein Seitentitel ist vorhanden und hat eine sinnvolle Länge |
| +1 | Eine Kurzbeschreibung ist vorhanden und hat eine sinnvolle Länge |
| +1 | Der Titel trägt, was die Branchenklasse erwartet — den Ort, sonst die Leistung |

**E2 · Überschriften und Textumfang — 2 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +1 | Genau eine Hauptüberschrift und mindestens eine Zwischenüberschrift |
| +1 | Mindestens 300 Wörter Text |

**E3 · Auffindbarkeit für Suchmaschinen — 3 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +1 | Eine robots.txt ist vorhanden und sperrt die Seite nicht aus |
| +1 | Eine sitemap.xml ist vorhanden |
| +1 | Eine Canonical-Angabe ist gesetzt |

**E4 · Strukturierte Daten — 3 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +1 | Strukturierte Daten sind überhaupt vorhanden |
| +1 | Der Haupttyp passt zur Branchenklasse |
| +1 | Mindestens ein passender Zusatztyp ist vorhanden |

**E5 · Lokale Signale — 3 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +1 | Der Ort steht im Seitentitel oder in der Hauptüberschrift |
| +1 | Die Telefonnummer ist als Link hinterlegt |
| +1 | Eine Karte oder eine Betriebsauszeichnung ist vorhanden |

**E6 · Keine defekten Verweise — 1 Punkt**

| Punkte | Bedingung |
|---|---|
| 1 | Kein Verweis der geprüften Seite läuft ins Leere |
| 0 | Mindestens ein Verweis läuft ins Leere |

**E7 · Lesbarkeit für KI-Systeme — 3 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +2 | Kein KI-Crawler ist in der robots.txt ausgesperrt |
| +1 | Eine llms.txt ist vorhanden |

### Gestaltung

**D1 · Visuelle Aktualität — 3 Punkte**

Eingeschätzt nach diesem Maßstab:

> 3 = kein Alterungsmerkmal erkennbar; die Seite koennte diesen Monat entstanden sein.
> 2 = ein oder zwei Merkmale, sonst zeitgemaess.
> 1 = drei bis vier Merkmale; der Eindruck kippt.
> 0 = fuenf oder mehr, oder ein einzelnes so deutlich, dass es alles ueberlagert.
> Die sechs Merkmale: feste Breite mit breiten leeren Raendern · kleine Schrift im
> Fliesstext · Verlaeufe, Schlagschatten, Spiegelungen · Bildergalerien mit Rahmen
> und Blaetterpfeilen · sichtbar veraltete Jahreszahl · gedraengte Anordnung ohne
> Weissraum.
> Nicht Teil dieses Kriteriums: die Aktualitaet der *Inhalte* (das ist I2) und die
> Schriftgroesse als Messwert (das ist D2, gemessen).

**D2 · Typografie und Lesbarkeit — 2 Punkte**

Anteilig: Der gemessene Anteil wird auf 2 Punkte umgerechnet und kaufmännisch gerundet.

**D3 · Farbsystem und Konsistenz — 2 Punkte**

Eingeschätzt nach diesem Maßstab:

> 2 = hoechstens drei tragende Farben, ueber alle Seiten gleich eingesetzt,
>     erkennbare Betriebsfarbe.
> 1 = ein System ist erkennbar, wird aber nicht durchgehalten — abweichende
>     Schaltflaechenfarben, wechselnde Flaechen.
> 0 = kein erkennbares System; Farben wirken einzeln gewaehlt.
> Nicht Teil dieses Kriteriums: der Kontrastwert. Den misst B2 mit Lighthouse.
> Bewerte hier die Konsistenz, nicht die Lesbarkeit — auch dann nicht, wenn dir
> ein Paar zu blass erscheint.

**D4 · Bildqualität und Echtheit — 2 Punkte**

Eingeschätzt nach diesem Maßstab:

> 2 = erkennbar eigene Aufnahmen: eigene Leute, eigene Fahrzeuge, eigene
>     Baustellen, eigene Raeume.
> 1 = gemischt — eigene Bilder neben deutlich gekauften.
> 0 = durchgehend generisches Material, oder gar keine Bilder.
> Anzeichen fuer gekauftes Material: freigestellte laechelnde Personen vor
> weissem Grund, Werkzeug ohne Gebrauchsspuren, Innenraeume ohne jeden Bezug zum
> Gewerk, dieselbe Person in mehreren Rollen.
> Nicht Teil dieses Kriteriums: Dateigroesse, Format und Ladeverhalten. Das ist
> P5 und wird gemessen.

**D5 · Mobile Darstellung — 1 Punkt**

| Punkte | Bedingung |
|---|---|
| 1 | Eine Viewport-Angabe steht im Kopf der Seite |
| 0 | Es steht keine Viewport-Angabe im Kopf der Seite |

### Nutzerführung und Anfragen

**C1 · Klarheit im ersten Bildschirmausschnitt — 3 Punkte**

Eingeschätzt nach diesem Maßstab:

> 3 = Leistung, Zielgruppe und — wo die Klasse es erwartet — das Gebiet stehen
>     im ersten Bildschirmausschnitt und sind in fuenf Sekunden erfasst.
> 2 = zwei der drei Angaben stehen da, die dritte muss man suchen.
> 1 = nur eine Angabe, oder alle drei erst nach Scrollen.
> 0 = der erste Ausschnitt sagt nicht, worum es geht.
> Massstab ist die Klasse: Ein ueberregionaler Anbieter (K4) braucht kein Gebiet,
> ein Publikumsbetrieb (K3) dafuer Oeffnungszeiten oder Standort.
> Nicht Teil dieses Kriteriums: ob ein Handlungsaufruf vorhanden ist (C2) und ob
> das Angebot inhaltlich klar ist (C5).

**C2 · Die erwartete Hauptreaktion — 3 Punkte**

| Punkte | Bedingung |
|---|---|
| 3 | Drei oder mehr Handlungsaufrufe, die in dieser Branchenklasse zählen |
| 2 | Ein oder zwei solche Handlungsaufrufe |
| 0 | Kein Handlungsaufruf |

**C3 · Kontaktwege — 3 Punkte**

Die Teilprüfungen addieren sich:

| Punkte | Teilprüfung |
|---|---|
| +1 | Das erste der drei Kontaktmerkmale dieser Branchenklasse ist erfüllt |
| +1 | Das zweite Kontaktmerkmal ist erfüllt |
| +1 | Das dritte Kontaktmerkmal ist erfüllt |

**C4 · Vertrauenssignale — 3 Punkte**

| Punkte | Bedingung |
|---|---|
| 3 | Vier oder mehr Vertrauenssignale, die in dieser Branchenklasse zählen |
| 2 | Zwei oder drei solche Vertrauenssignale |
| 1 | Ein Vertrauenssignal |
| 0 | Kein Vertrauenssignal |

**C5 · Klarheit des Angebots — 3 Punkte**

Eingeschätzt nach diesem Maßstab:

> 3 = die Leistungen sind einzeln benannt, der Ablauf oder ein Preisrahmen steht
>     da, und es gibt eine Zusage, die das Risiko des Kunden senkt
>     (Festpreis, Garantie, kostenlose Erstbewertung).
> 2 = zwei der drei Teile.
> 1 = nur die Leistungen, ohne Ablauf, Preis oder Zusage.
> 0 = die Leistungen bleiben allgemein („alles rund ums Bad").
> Bei Beratungs- und Gesundheitsberufen (K2) ist die fehlende Preisangabe **kein**
> Mangel — dort zaehlen Ablauf und Zusage. Ziehe dafuer keinen Punkt ab.
> Nicht Teil dieses Kriteriums: eigene Leistungsseiten (I1) und die
> Textqualitaet (I3).

### Inhalt und Substanz

**I1 · Eigene Leistungsseiten — 2 Punkte**

| Punkte | Bedingung |
|---|---|
| 2 | Drei oder mehr eigene Leistungsseiten, die in dieser Branchenklasse zählen |
| 1 | Eine oder zwei solche Leistungsseiten |
| 0 | Keine eigene Leistungsseite |

**I2 · Aktualität — 1 Punkt**

| Punkte | Bedingung |
|---|---|
| 1 | Das Copyright trägt das laufende Jahr, oder es gibt datierte Inhalte |
| 0 | Weder aktuelles Copyright noch datierte Inhalte |

**I3 · Textqualität — 2 Punkte**

Eingeschätzt nach diesem Maßstab:

> 2 = die Texte gehen vom Anliegen des Kunden aus, nennen Konkretes (Orte,
>     Fristen, Ablaeufe, Zahlen) und sind ohne Fachjargon verstaendlich.
> 1 = teils kundenorientiert, teils Selbstbeschreibung; wenig Konkretes.
> 0 = durchgehend ueber den Betrieb statt ueber das Anliegen, austauschbar
>     formuliert.
> Nicht Teil dieses Kriteriums: Textlaenge und Ueberschriftenstruktur (E2,
> gemessen) und die Aktualitaet der Inhalte (I2).
> Zum Ton: Beschreibe, was fehlt. Abwertende Urteile ueber Texte sind untersagt —
> siehe den Abschnitt TON DER TEXTE.

