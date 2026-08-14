# Bewertungslogik — Homepage Standard 2026.1

**Status:** Spezifikationsentwurf zur Umsetzung
**Gilt für:** Backend-Audit-Service, Frontend-Anzeige, Buch „Der Homepage Standard"
**Version:** 2026.1
**Stand:** 14.08.2026

---

## 0. Zweck dieses Dokuments

Dieses Dokument ist die **einzige verbindliche Quelle** für die Bewertungslogik des
Homepage Standards. Backend, Frontend und Buch müssen ihm entsprechen. Bei Widersprüchen
gilt dieses Dokument.

Änderungen an der Bewertung erfolgen ausschließlich hier und werden mit einer neuen
Versionsnummer versehen. Eine gedruckte Buchauflage bezieht sich immer auf genau eine
Version.

---

## 1. Geltungsbereich

Der Standard bewertet Websites von **Unternehmen, die über ihre Website Kunden
gewinnen oder qualifizieren**. Das umfasst Handwerksbetriebe, freie Berufe, lokale
Dienstleister, Praxen, Kanzleien, Agenturen, B2B-Dienstleister, Gastronomie, Handel und
Onlineshops.

Nicht im Geltungsbereich: reine Konzern-Repräsentanzen ohne Akquisefunktion, Behörden
(dort gilt die BITV), private Seiten, Vereinsseiten ohne wirtschaftliche Tätigkeit.

---

## 2. Grundbegriffe

| Begriff | Definition |
|---|---|
| **Kriterium** | Kleinste bewertete Einheit, z. B. `rc_impressum` |
| **Kategorie** | Gruppe von Kriterien, z. B. Rechtliche Compliance |
| **Basispunkte** | Höchstpunktzahl eines Kriteriums, wenn es anwendbar ist |
| **Anwendbarkeit** | Ob ein Kriterium auf das geprüfte Unternehmen zutrifft |
| **Anwendbares Maximum** | Summe der Basispunkte aller anwendbaren Kriterien |
| **Rohpunkte** | Tatsächlich erreichte Punkte |
| **Gesamtscore** | Auf 100 normalisierte Rohpunkte |

---

## 3. Anwendungsprofile

Vor der Bewertung wird das Unternehmen einem Profil zugeordnet. Das Profil steuert die
Anwendbarkeit einzelner Kriterien.

### 3.1 Die drei Profile

| Profil | Bezeichnung | Merkmale | Beispiele |
|---|---|---|---|
| **P1** | Lokaler Leistungsanbieter | Kundengewinnung mit räumlichem Einzugsgebiet, Leistung wird vor Ort oder beim Kunden erbracht | Handwerk, Praxen, Kanzleien, Gastronomie, Kfz-Betriebe, Pflegedienste |
| **P2** | Überregionaler Anbieter | Kundengewinnung ohne räumliche Bindung, Leistung remote oder bundesweit | Agenturen, Beratungen, Softwareanbieter, B2B-Zulieferer, Coaches |
| **P3** | Onlineverkauf | Vertragsschluss oder Bezahlung findet auf der Website statt | Shops, digitale Produkte, kostenpflichtige Onlinebuchung |

**Mehrfachzuordnung:** P3 ist mit P1 oder P2 kombinierbar. Ein Handwerksbetrieb mit
Ersatzteilshop ist P1+P3. Bei Kombination gelten alle Kriterien beider Profile.

### 3.2 Zusätzliche Merkmale

Neben dem Profil werden zwei Merkmale erhoben, die die Anwendbarkeit beeinflussen:

| Merkmal | Werte | Herkunft |
|---|---|---|
| `kleinstunternehmen` | true / false / unbekannt | Lead-Datensatz oder Selbstauskunft |
| `zielgruppe` | b2c / b2b / beides | Lead-Datensatz oder Erkennung aus Website |

**Definition Kleinstunternehmen:** weniger als 10 Beschäftigte **und** höchstens
2 Mio. € Jahresumsatz oder Jahresbilanzsumme. Beide Bedingungen müssen zusammen erfüllt
sein.

### 3.3 Profilerkennung

Ist das Profil nicht bekannt, wird es automatisch geschätzt:

| Signal | Schluss |
|---|---|
| Warenkorb-, Kasse-, Bestell-Elemente erkennbar | P3 |
| Zahlungsanbieter-Skripte geladen (Stripe, PayPal, Klarna) | P3 |
| Ortsnamen in Title/H1, Einzugsgebietsseiten, Anfahrtsbeschreibung | P1 |
| Adresse im Impressum + Ortsbezug im Seitentitel | P1 |
| Keine Ortsbezüge, überregionale Formulierungen | P2 |
| Keine eindeutigen Signale | **P1** (Standardannahme) |

**Wichtig:** Das geschätzte Profil wird im Bericht **sichtbar ausgewiesen** mit dem Hinweis,
dass es korrigierbar ist. Ein falsch erkanntes Profil verfälscht das Ergebnis erheblich.
Bei manueller Korrektur wird das Audit neu berechnet — ohne erneuten Seitenabruf.

---

## 4. Anwendbarkeitsmatrix

| Kriterium | Basis | P1 | P2 | P3 | Zusatzbedingung |
|---|---|---|---|---|---|
| `rc_impressum` | 7 | ✓ | ✓ | ✓ | immer |
| `rc_datenschutz` | 7 | ✓ | ✓ | ✓ | immer |
| `rc_cookie` | 6 | ✓ | ✓ | ✓ | immer |
| `rc_bfsg` | 4 | ○ | ○ | ○ | nur wenn `kleinstunternehmen = false` |
| `rc_urheberrecht` | 3 | ✓ | ✓ | ✓ | immer |
| `rc_ecommerce` | 3 | ○ | ○ | ✓ | nur P3 |
| `tp_lcp` | 5 | ✓ | ✓ | ✓ | immer |
| `tp_cls` | 4 | ✓ | ✓ | ✓ | immer |
| `tp_inp` | 3 | ✓ | ✓ | ✓ | immer |
| `tp_mobile` | 4 | ✓ | ✓ | ✓ | immer |
| `tp_bilder` | 4 | ✓ | ✓ | ✓ | immer |
| `bf_kontrast` | 5 | ✓ | ✓ | ✓ | immer |
| `bf_tastatur` | 5 | ✓ | ✓ | ✓ | immer |
| `bf_screenreader` | 5 | ✓ | ✓ | ✓ | immer |
| `bf_lesbarkeit` | 5 | ✓ | ✓ | ✓ | immer |
| `si_ssl` | 4 | ✓ | ✓ | ✓ | immer |
| `si_header` | 4 | ✓ | ✓ | ✓ | immer |
| `si_drittanbieter` | 4 | ✓ | ✓ | ✓ | immer |
| `si_formulare` | 3 | ○ | ○ | ○ | nur wenn Formular vorhanden |
| `se_seo` | 4 | ✓ | ✓ | ✓ | immer |
| `se_schema` | 3 | ✓ | ✓ | ✓ | immer |
| `se_lokal` | 3 | ✓ | ○ | ○ | nur P1 |
| `ux_erstindruck` | 1 | ✓ | ✓ | ✓ | immer |
| `ux_cta` | 1 | ✓ | ✓ | ✓ | immer |
| `ux_navigation` | 1 | ✓ | ✓ | ✓ | immer |
| `ux_vertrauen` | 1 | ✓ | ✓ | ✓ | immer |
| `ux_kontakt` | 1 | ✓ | ✓ | ✓ | immer |

✓ = immer anwendbar · ○ = bedingt anwendbar

**Basissumme aller Kriterien: 100.**

### Typische anwendbare Maxima

| Fall | Nicht anwendbar | Anwendbares Maximum |
|---|---|---|
| Handwerksbetrieb, 6 MA, kein Shop, mit Formular | `rc_bfsg`, `rc_ecommerce` | 93 |
| Handwerksbetrieb, 25 MA, kein Shop, mit Formular | `rc_ecommerce` | 97 |
| B2B-Beratung, 4 MA, kein Shop, mit Formular | `rc_bfsg`, `rc_ecommerce`, `se_lokal` | 90 |
| Onlineshop, 30 MA, lokal, mit Formular | — | 100 |

---

## 5. Normalisierung und Gesamtscore

```
gesamtscore = round( rohpunkte / anwendbares_maximum * 100 )
```

Der Gesamtscore ist damit immer eine Zahl zwischen 0 und 100 und über Profile hinweg
vergleichbar.

**Beispiel:** Handwerksbetrieb mit 6 Mitarbeitern, anwendbares Maximum 93, erreicht
67 Rohpunkte → `round(67 / 93 * 100)` = **72 Punkte** → Stufe Gold.

**Kategoriewerte** werden analog normalisiert und im Bericht sowohl roh als auch
normalisiert ausgewiesen:

```
Rechtliche Compliance: 16 von 23 anwendbaren Punkten (70 %)
```

**Warum Normalisierung statt Umverteilung:** Punkte auf andere Kriterien umzulegen
verändert deren Gewicht und macht Berichte untereinander unvergleichbar. Die
Normalisierung hält die relative Gewichtung innerhalb der anwendbaren Kriterien konstant.

> **Hinweis:** Dieser Abschnitt ersetzt die im Datenblatt zu ABW-4 vorgeschlagene
> anteilige Umlegung. Normalisierung ist die saubere Lösung.

---

## 6. Zertifizierungsstufen

| Stufe | Gesamtscore | Zusatzbedingung |
|---|---|---|
| Homepage Standard Platin | 85–100 | kein anwendbares Kriterium der Kategorie 1 bei 0 Punkten |
| Homepage Standard Gold | 70–84 | kein anwendbares Kriterium der Kategorie 1 bei 0 Punkten |
| Homepage Standard Silber | 50–69 | — |
| Homepage Standard Bronze | 30–49 | — |
| Nicht konform | 0–29 | — |

**Die Zusatzbedingung ist neu und wichtig.** Ohne sie könnte eine Website mit fehlendem
Impressum durch gute Werte in allen anderen Kategorien Gold erreichen. Das wäre eine
Aussage, die der Standard nicht treffen darf.

**Regel:** Steht ein anwendbares Kriterium der Kategorie 1 (Rechtliche Compliance) auf
0 Punkten, ist die höchste erreichbare Stufe **Silber**, unabhängig vom Gesamtscore. Der
Bericht weist das gesondert aus:

> „Silber (rechnerisch 81 Punkte). Die Einstufung ist begrenzt, weil folgende rechtliche
> Pflichtangabe fehlt: Datenschutzerklärung."

---

## 7. Prüfumfang

### 7.1 Welche Seiten werden geprüft

| Seite | Auswahl |
|---|---|
| Startseite | immer |
| Impressum | über Linkerkennung |
| Datenschutzerklärung | über Linkerkennung |
| Bis zu 3 weitere Seiten | die drei aus der Hauptnavigation am häufigsten verlinkten |

Maximal 6 Seiten pro Audit. Mehr Seiten verbessern das Ergebnis kaum und vervielfachen
Laufzeit und Kosten.

### 7.2 Datenquellen

| Quelle | Verwendet für |
|---|---|
| HTML-Abruf mit Headless-Browser | Struktur, Inhalte, Formulare, Kontrast, Drittanbieter-Requests |
| HTTP-Response-Header | `si_header`, `si_ssl`, Weiterleitungen |
| TLS-Handshake | Zertifikatsgültigkeit, Protokollversion |
| PageSpeed Insights API (mobil) | `tp_lcp`, `tp_cls`, `tp_inp` |
| `robots.txt`, `sitemap.xml` | `se_seo` |
| JSON-LD-Parsing | `se_schema` |
| Sprachmodell-Auswertung | `ux_*`, Textqualität, Zusammenfassung |

**Messbedingungen für Performance:** Immer Strategie `mobile`. Felddaten (CrUX)
bevorzugt; liegen keine vor, Labordaten mit Kennzeichnung im Bericht. Ein Wechsel der
Datenquelle zwischen zwei Audits muss im Bericht sichtbar sein, sonst wirken normale
Messschwankungen wie Verschlechterungen.

### 7.3 Fehlerbehandlung

| Fall | Verhalten |
|---|---|
| Website nicht erreichbar | Audit bricht ab, kein Score, klare Meldung |
| Einzelne Unterseite nicht erreichbar | Kriterium auf Basis der erreichbaren Seiten bewerten, Hinweis im Bericht |
| Scraping blockiert (Bot-Schutz) | Betroffene Kriterien als `unbestimmt` markieren, **nicht** mit 0 bewerten |
| PageSpeed-API nicht verfügbar | Kategorie 2 als `unbestimmt`, aus dem anwendbaren Maximum herausnehmen |
| Sprachmodell-Antwort unvollständig | Wiederholung mit erhöhtem Token-Limit; danach `unbestimmt` |

**Grundregel:** `unbestimmt` ist niemals dasselbe wie `0 Punkte`. Ein Kriterium, das
nicht geprüft werden konnte, wird aus dem anwendbaren Maximum entfernt und im Bericht
sichtbar als ungeprüft ausgewiesen. Ein Audit mit mehr als 5 unbestimmten Kriterien gilt
als unvollständig und wird ohne Stufenzuweisung ausgegeben.

---

# 8. Die Kriterien im Einzelnen

Jedes Kriterium ist beschrieben mit: Prüfgegenstand, Datenquelle, Bewertungsstufen und
Selbstprüfung. Der Abschnitt „Selbstprüfung" ist die Vorlage für das Buch.

---

## Kategorie 1 — Rechtliche Compliance (30 Basispunkte)

### `rc_impressum` — Impressum · 7 Punkte

**Prüfgegenstand:** Vorhandensein, Erreichbarkeit und Vollständigkeit der
Anbieterkennzeichnung nach § 5 DDG.

**Pflichtangaben** (anwendbar je nach Rechtsform und Tätigkeit):

| Angabe | Anwendbar |
|---|---|
| Name / Firma inkl. Rechtsform | immer |
| Ladungsfähige Anschrift (Straße, PLZ, Ort) | immer |
| Telefonnummer | immer |
| E-Mail-Adresse | immer |
| Vertretungsberechtigte Person | juristische Personen |
| Registergericht und Registernummer | eingetragene Unternehmen |
| Umsatzsteuer-Identifikationsnummer | sofern vorhanden |
| Zuständige Kammer | Kammerberufe |
| Gesetzliche Berufsbezeichnung und Verleihungsstaat | reglementierte Berufe |
| Aufsichtsbehörde | zulassungspflichtige Tätigkeiten |
| Verantwortlicher für journalistische Inhalte | bei redaktionellem Angebot |

**Bewertung:**

| Punkte | Bedingung |
|---|---|
| 7 | Von **jeder** geprüften Seite in einem Klick erreichbar **und** alle anwendbaren Pflichtangaben vorhanden |
| 5 | Alle Pflichtangaben vorhanden, aber nicht von allen Seiten verlinkt |
| 4 | Erreichbar, eine Pflichtangabe fehlt |
| 3 | Erreichbar, zwei Pflichtangaben fehlen |
| 2 | Erreichbar, drei oder mehr Pflichtangaben fehlen |
| 1 | Nur über Suche oder mehr als zwei Klicks auffindbar |
| 0 | Nicht auffindbar |

**Selbstprüfung:** Öffnen Sie drei beliebige Unterseiten Ihrer Website und suchen Sie im
Fußbereich nach „Impressum". Ist es auf allen dreien verlinkt? Öffnen Sie es und gleichen
Sie die Tabelle oben ab.

---

### `rc_datenschutz` — Datenschutzerklärung · 7 Punkte

**Prüfgegenstand:** Vorhandensein, Erreichbarkeit, Mindestbestandteile nach Art. 13 DSGVO
und Übereinstimmung mit der tatsächlich erkennbaren Datenverarbeitung.

**Mindestbestandteile:** Verantwortlicher mit Kontaktdaten · Datenschutzbeauftragter,
sofern benannt · Verarbeitungszwecke · Rechtsgrundlagen · Empfänger und eingesetzte
Dienste · Drittlandübermittlung mit Garantien · Speicherdauer · Betroffenenrechte ·
Widerrufsrecht · Beschwerderecht bei einer Aufsichtsbehörde.

**Bewertung:**

| Punkte | Bedingung |
|---|---|
| 7 | Von jeder Seite erreichbar, alle Bestandteile vorhanden, **kein** erkennbarer Drittdienst fehlt in der Aufzählung |
| 5 | Alle Bestandteile vorhanden, aber ein tatsächlich geladener Drittdienst ist nicht genannt |
| 4 | Ein bis zwei Bestandteile fehlen |
| 2 | Drei oder mehr Bestandteile fehlen, oder erkennbar unangepasstes Muster |
| 1 | Vorhanden, aber nur über Umwege erreichbar |
| 0 | Nicht auffindbar |

**Erkennbar unangepasstes Muster:** Platzhalter wie „[Ihr Unternehmen]", Nennung von
Diensten, die nachweislich nicht eingesetzt werden, oder Verweise auf eine andere Firma.

**Selbstprüfung:** Prüfen Sie in Ihrer Erklärung, ob jeder Dienst genannt ist, den Ihre
Seite lädt — Karten, Videos, Schriftarten, Statistik, Chat, Bewertungsanzeigen.

---

### `rc_cookie` — Einwilligung für Cookies und Tracking · 6 Punkte

**Prüfgegenstand:** § 25 TDDDG. Einwilligung ist erforderlich für jede Speicherung oder
jeden Zugriff auf Endgeräteinformationen, die nicht technisch zwingend erforderlich ist.

**Prüfmethode:** Seitenaufruf ohne jede Interaktion. Erfassung aller gesetzten Cookies,
`localStorage`-Einträge und ausgehenden Requests an Drittdomains.

**Bewertung:**

| Punkte | Bedingung |
|---|---|
| 6 | Keine einwilligungspflichtigen Technologien vorhanden **oder** Banner mit gleichwertigem „Ablehnen" auf der ersten Ebene, **und** vor Einwilligung wird nichts Einwilligungspflichtiges geladen |
| 4 | Banner korrekt gestaltet, aber einzelne nicht-essenzielle Ressourcen laden bereits vor der Einwilligung |
| 3 | Banner vorhanden, „Ablehnen" nur auf zweiter Ebene oder optisch deutlich untergeordnet |
| 2 | Banner vorhanden, aber kein Ablehnen möglich (nur „OK") |
| 1 | Reiner Hinweistext ohne Wahlmöglichkeit |
| 0 | Einwilligungspflichtige Technologien vorhanden, kein Banner |

**Zusatzprüfung:** Ist ein Widerruf der Einwilligung jederzeit möglich (dauerhaft
erreichbarer Link oder Schaltfläche)? Fehlt er, ein Punkt Abzug, Minimum 0.

**Selbstprüfung:** Öffnen Sie Ihre Seite in einem privaten Browserfenster. Erscheint ein
Banner? Steht „Ablehnen" gleichwertig neben „Akzeptieren" — gleiche Größe, gleiche Ebene,
gleiche Auffälligkeit?

---

### `rc_bfsg` — Barrierefreiheitserklärung · 4 Punkte

**Anwendbar nur, wenn `kleinstunternehmen = false`.**

Bei Dienstleistungen sind Kleinstunternehmen von den Anforderungen des BFSG ausgenommen.
Ist das Merkmal `unbekannt`, wird das Kriterium als `unbestimmt` behandelt und aus dem
anwendbaren Maximum entfernt — **nicht** mit 0 bewertet.

**Prüfgegenstand:** Vorhandensein und Inhalt einer Erklärung zur Barrierefreiheit.

**Bewertung:**

| Punkte | Bedingung |
|---|---|
| 4 | Erklärung vorhanden, verlinkt, mit Stand, Konformitätsaussage, Beschreibung nicht barrierefreier Inhalte und Kontaktmöglichkeit für Barrieremeldungen |
| 3 | Vorhanden, ein Bestandteil fehlt |
| 2 | Vorhanden, zwei oder mehr Bestandteile fehlen |
| 1 | Nur ein Hinweissatz ohne Substanz |
| 0 | Nicht vorhanden |

> **Rechtlich zu bestätigen:** Die Abgrenzung der Kleinstunternehmen-Ausnahme sowie die
> Frage, ob sie auch bei kombiniertem Onlineverkauf greift, sollte vor Veröffentlichung
> des Buches anwaltlich geprüft werden.

---

### `rc_urheberrecht` — Urheberrecht & Lizenzen · 3 Punkte

**Prüfgegenstand:** Erkennbare Rechteklärung an eingebundenen Inhalten.

**Geprüft wird:** Bildnachweis oder Lizenzangaben vorhanden · verwendete Schriftarten
lizenzkonform eingebunden · eingebundene Karten- und Videodienste mit Anbieterangabe ·
keine offensichtlich fremden Marken- oder Herstellerlogos ohne erkennbaren Bezug ·
Kartenmaterial mit erforderlicher Namensnennung.

**Bewertung:**

| Punkte | Bedingung |
|---|---|
| 3 | Bildnachweis vorhanden oder erkennbar ausschließlich eigenes Material, keine Auffälligkeiten |
| 2 | Kein Bildnachweis, aber keine erkennbar problematischen Inhalte |
| 1 | Fremde Logos oder Kartenmaterial ohne Nennung eingebunden |
| 0 | Mehrere erkennbare Verstöße |

**Grenze der Prüfbarkeit:** Ob für ein Foto eine Lizenz erworben wurde, ist von außen
nicht feststellbar. Das Kriterium prüft nur erkennbare Indizien. Im Bericht ist das
kenntlich zu machen.

---

### `rc_ecommerce` — Pflichten im Onlineverkauf · 3 Punkte

**Anwendbar nur bei Profil P3.**

**Geprüft wird:** AGB vorhanden · Widerrufsbelehrung mit Muster-Widerrufsformular ·
Preisangaben als Gesamtpreis inkl. Umsatzsteuer · Versandkosten vor Bestellabschluss
erkennbar · Lieferzeitangabe · Bestellschaltfläche eindeutig beschriftet
(„zahlungspflichtig bestellen") · Bestellübersicht vor Abschluss · Angabe akzeptierter
Zahlungsarten.

**Bewertung:**

| Punkte | Bedingung |
|---|---|
| 3 | Alle Punkte erfüllt |
| 2 | Ein bis zwei Punkte fehlen |
| 1 | Drei bis vier Punkte fehlen |
| 0 | Mehr als vier Punkte fehlen oder AGB und Widerrufsbelehrung fehlen vollständig |

---

## Kategorie 2 — Technische Performance (20 Basispunkte)

Alle Werte werden mobil gemessen. Felddaten bevorzugt, sonst Labordaten mit Kennzeichnung.

### `tp_lcp` — Largest Contentful Paint · 5 Punkte

Zeit, bis das größte sichtbare Element geladen ist.

| Punkte | Messwert |
|---|---|
| 5 | ≤ 2,5 s |
| 4 | > 2,5 s bis 3,0 s |
| 3 | > 3,0 s bis 3,5 s |
| 2 | > 3,5 s bis 4,0 s |
| 1 | > 4,0 s bis 5,0 s |
| 0 | > 5,0 s |

### `tp_cls` — Cumulative Layout Shift · 4 Punkte

Maß dafür, wie stark der Seiteninhalt beim Laden verspringt.

| Punkte | Messwert |
|---|---|
| 4 | ≤ 0,10 |
| 3 | > 0,10 bis 0,15 |
| 2 | > 0,15 bis 0,25 |
| 1 | > 0,25 bis 0,40 |
| 0 | > 0,40 |

### `tp_inp` — Interaction to Next Paint · 3 Punkte

Reaktionszeit auf Nutzereingaben.

| Punkte | Messwert |
|---|---|
| 3 | ≤ 200 ms |
| 2 | > 200 ms bis 350 ms |
| 1 | > 350 ms bis 500 ms |
| 0 | > 500 ms |

### `tp_mobile` — Mobile-First-Umsetzung · 4 Punkte

Je erfüllter Punkt 1 Punkt, maximal 4:

- Viewport-Angabe korrekt gesetzt
- Kein horizontales Scrollen bei 360 px Breite
- Alle Bedienelemente mindestens 24 × 24 px, kein Überlappen
- Basisschriftgröße mindestens 16 px

### `tp_bilder` — Bildoptimierung · 4 Punkte

Je erfüllter Punkt 1 Punkt, maximal 4:

- Mehrheit der Bilder in modernem Format (WebP oder AVIF)
- Höhe und Breite gesetzt, damit kein Layoutsprung entsteht
- Bilder außerhalb des sichtbaren Bereichs werden verzögert geladen
- Kein einzelnes Bild über 300 KB

---

## Kategorie 3 — Barrierefreiheit (20 Basispunkte)

Referenz: WCAG 2.2 Konformitätsstufe AA.

### `bf_kontrast` — Farbkontraste · 5 Punkte

Anforderung: 4,5:1 für normalen Text, 3:1 für großen Text ab 24 px oder ab 18,5 px fett,
3:1 für Bedienelemente und deren Zustände.

| Punkte | Bedingung |
|---|---|
| 5 | Alle geprüften Textelemente bestehen |
| 4 | Bis zu 5 % der Elemente fallen durch |
| 3 | Bis zu 15 % fallen durch |
| 2 | Bis zu 30 % fallen durch |
| 1 | Bis zu 50 % fallen durch |
| 0 | Mehr als 50 % fallen durch |

### `bf_tastatur` — Tastaturzugänglichkeit · 5 Punkte

Je erfüllter Punkt 1 Punkt, maximal 5:

- Alle interaktiven Elemente sind per Tabulatortaste erreichbar
- Fokus ist deutlich sichtbar
- Keine Tastaturfalle (jedes Element ist wieder verlassbar)
- Reihenfolge folgt der visuellen Anordnung
- Sprunglink zum Hauptinhalt vorhanden

### `bf_screenreader` — Screenreader-Kompatibilität · 5 Punkte

Je erfüllter Punkt 1 Punkt, maximal 5:

- Alle informationstragenden Bilder haben aussagekräftige Alternativtexte,
  dekorative Bilder haben leere Alternativtexte
- Sprache der Seite ist ausgezeichnet
- Semantische Bereiche vorhanden (Kopf, Navigation, Hauptinhalt, Fuß)
- Überschriftenhierarchie ohne Ebenensprünge
- Alle Formularfelder haben zugeordnete Beschriftungen

### `bf_lesbarkeit` — Lesbarkeit & Textgestaltung · 5 Punkte

Je erfüllter Punkt 1 Punkt, maximal 5:

- Basisschriftgröße mindestens 16 px
- Zeilenhöhe mindestens 1,5-fach
- Zoom bis 200 % nicht unterbunden
- Zeilenlänge im Fließtext höchstens 90 Zeichen
- Kein Fließtext in Bildern

---

## Kategorie 4 — Sicherheit & Datenschutz (15 Basispunkte)

### `si_ssl` — Verschlüsselung · 4 Punkte

Je erfüllter Punkt 1 Punkt, maximal 4:

- Gültiges Zertifikat, Laufzeit nicht abgelaufen
- TLS 1.2 oder höher, keine veralteten Protokolle
- Unverschlüsselte Aufrufe werden auf die verschlüsselte Version umgeleitet
- Keine unverschlüsselt eingebundenen Ressourcen

**Sonderregel:** Kein gültiges Zertifikat → 0 Punkte, unabhängig von den übrigen Punkten.

### `si_header` — Sicherheitsheader · 4 Punkte

Je gesetztem Header 1 Punkt, maximal 4:

- `Strict-Transport-Security`
- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy`

### `si_drittanbieter` — Drittanbieter und Drittlandtransfer · 4 Punkte

| Punkte | Bedingung |
|---|---|
| 4 | Vor Einwilligung keine Requests an Drittdomains |
| 3 | Ein Drittdienst vor Einwilligung, kein Drittlandbezug |
| 2 | Mehrere Drittdienste vor Einwilligung, kein Drittlandbezug |
| 1 | Drittlandtransfer vor Einwilligung (z. B. extern geladene Schriftarten, Karten, Videos) |
| 0 | Mehrere Drittlandtransfers vor Einwilligung |

### `si_formulare` — Formularsicherheit · 3 Punkte

**Anwendbar nur, wenn mindestens ein Formular vorhanden ist.**

Je erfüllter Punkt 1 Punkt, maximal 3:

- Übertragung verschlüsselt und per POST
- Datenschutzhinweis oder Einwilligung unmittelbar am Formular
- Spam-Schutz erkennbar vorhanden

---

## Kategorie 5 — SEO & Sichtbarkeit (10 Basispunkte)

### `se_seo` — Technische SEO-Grundlagen · 4 Punkte

Je erfüllter Punkt 1 Punkt, maximal 4:

- Genau eine H1 pro Seite, inhaltlich aussagekräftig
- Seitentitel vorhanden, 30–65 Zeichen, je Seite unterschiedlich
- Meta-Beschreibung vorhanden, 70–160 Zeichen, je Seite unterschiedlich
- `robots.txt` und `sitemap.xml` vorhanden, Hauptseiten nicht von der Indexierung
  ausgeschlossen

### `se_schema` — Strukturierte Daten · 3 Punkte

| Punkte | Bedingung |
|---|---|
| 3 | JSON-LD vorhanden, passender Typ (`LocalBusiness` bei P1, sonst `Organization`), Pflichtfelder Name, Anschrift, Telefon, URL gefüllt, syntaktisch valide |
| 2 | Vorhanden und valide, aber ein bis zwei Pflichtfelder fehlen |
| 1 | Vorhanden, aber unpassender Typ oder Syntaxfehler |
| 0 | Nicht vorhanden |

### `se_lokal` — Lokale Auffindbarkeit · 3 Punkte

**Anwendbar nur bei Profil P1.**

Je erfüllter Punkt 1 Punkt, maximal 3:

- Name, Anschrift und Telefonnummer im Fußbereich jeder Seite
- Ortsbezug in Seitentitel oder H1 der Startseite
- Kontaktdaten in Impressum und Fußbereich identisch

---

## Kategorie 6 — Inhalt & Nutzererfahrung (5 Basispunkte)

Jedes Kriterium: 1 Punkt bei Erfüllung, 0 bei Nichterfüllung. Keine Zwischenstufen.

### `ux_erstindruck` — Erster Eindruck & Inhaltsqualität · 1 Punkt

Erfüllt, wenn im ersten sichtbaren Bereich ohne Scrollen erkennbar ist: **was** angeboten
wird, **für wen**, und bei P1 zusätzlich **wo**. Die Aussage muss als Text vorliegen,
nicht ausschließlich als Bild.

### `ux_cta` — Klare Handlungsaufforderung · 1 Punkt

Erfüllt, wenn im ersten sichtbaren Bereich genau ein optisch hervorgehobenes primäres
Handlungsziel erkennbar ist (Anrufen, Anfrage, Termin, Bestellen).

### `ux_navigation` — Navigation & Struktur · 1 Punkt

Erfüllt, wenn die Hauptnavigation 3 bis 8 Punkte umfasst, auf allen Seiten gleich ist und
mobil ohne Zoom bedienbar ist.

### `ux_vertrauen` — Vertrauenssignale · 1 Punkt

Erfüllt, wenn mindestens zwei der folgenden Elemente vorhanden sind: Kundenbewertungen mit
Namen · Zertifikate, Mitgliedschaften oder Qualifikationen · echte Team- oder Objektfotos
(keine erkennbaren Bildagenturmotive) · benannte Referenzen · Angabe des Gründungsjahres
oder der Betriebszugehörigkeit.

### `ux_kontakt` — Kontaktmöglichkeiten · 1 Punkt

Erfüllt, wenn Telefonnummer und E-Mail-Adresse als anklickbare Verweise hinterlegt sind
**und** mindestens ein Kontaktweg im Kopfbereich oder in einer dauerhaft sichtbaren Leiste
erreichbar ist.

---

## 9. Zusatzprüfungen außerhalb der Wertung

### Hosting-Check

`ho_anbieter` · `ho_uptime` · `ho_http` · `ho_backup` · `ho_cdn` — je erfüllt oder nicht
erfüllt. Kein Einfluss auf den Gesamtscore. Ausgabe als eigener Abschnitt im Bericht.

### GEO-Wert (0–10)

Bewertet die Aufbereitung für KI-gestützte Suchsysteme. Je erfüllter Punkt 1 Punkt:

`llms.txt` vorhanden · strukturierte Daten über das Pflichtmaß hinaus · FAQ-Abschnitt mit
`FAQPage`-Auszeichnung · eindeutige Leistungsbeschreibungen als Text · Angaben zu
Einzugsgebiet maschinenlesbar · Öffnungszeiten strukturiert · Preisangaben oder -spannen
vorhanden · Autoren- oder Verantwortlichkeitsangabe · Aktualitätsdatum der Inhalte ·
zitierfähige Faktenabschnitte.

**Der GEO-Wert fließt nicht in die 100 Punkte ein.** Begründung: Das Feld verändert sich zu
schnell für einen Standard, der Vergleichbarkeit über Jahre herstellen soll.

---

## 10. Ausgabeformat

```json
{
  "standard_version": "2026.1",
  "profile": "P1",
  "profile_source": "auto",
  "merkmale": {
    "kleinstunternehmen": true,
    "zielgruppe": "b2c"
  },
  "rohpunkte": 67,
  "anwendbares_maximum": 93,
  "gesamtscore": 72,
  "stufe": "Homepage Standard Gold",
  "stufe_begrenzt_durch": null,
  "kategorien": {
    "rechtliche_compliance": {
      "rohpunkte": 16, "anwendbares_maximum": 23, "prozent": 70
    }
  },
  "kriterien": {
    "rc_impressum": {
      "punkte": 5, "max": 7, "status": "teilweise",
      "anwendbar": true,
      "befund": "Alle Pflichtangaben vorhanden, aber nur von der Startseite verlinkt."
    },
    "rc_bfsg": {
      "punkte": null, "max": 4, "status": "nicht_anwendbar",
      "anwendbar": false,
      "befund": "Kleinstunternehmen — bei Dienstleistungen von den BFSG-Anforderungen ausgenommen."
    }
  },
  "unbestimmt": [],
  "hosting": {},
  "geo_score": 3
}
```

**Statuswerte:** `erfuellt` · `teilweise` · `nicht_erfuellt` · `nicht_anwendbar` ·
`unbestimmt`

**Statusableitung für die Anzeige:** ≥ 80 % der Basispunkte = `erfuellt`, ≥ 40 % =
`teilweise`, darunter `nicht_erfuellt`.

---

## 11. Versionierung

| Änderungsart | Versionssprung | Folge |
|---|---|---|
| Neues Kriterium, geänderte Punktzahl, geänderte Schwelle | Hauptversion (2026.1 → 2027.1) | Alte Audits nicht mehr vergleichbar, Buchneuauflage nötig |
| Präzisierte Formulierung, neue Prüfmethode bei gleichem Ergebnis | Nebenversion (2026.1 → 2026.2) | Vergleichbarkeit bleibt |
| Fehlerkorrektur in der Umsetzung | keine | — |

Jedes gespeicherte Audit hält seine `standard_version` fest. Score-Verläufe über
Hauptversionen hinweg werden im Bericht mit einer Trennlinie dargestellt, nie als
durchgehende Kurve.

---

## 12. Offene Punkte

| # | Punkt | Zu klären durch |
|---|---|---|
| 1 | BFSG-Kleinstunternehmen-Ausnahme bei kombiniertem Onlineverkauf | Anwalt |
| 2 | Grenze der Prüfbarkeit bei `rc_urheberrecht` — reicht die Indizienprüfung? | Anwalt |
| 3 | Profilerkennung: Trefferquote der Automatik messen, bevor sie produktiv geht | Auswertung Bestandsaudits |
| 4 | Schwellenwerte Kategorie 2: gegen Bestandsaudits gegenprüfen, damit die Verteilung nicht einseitig ausfällt | Auswertung Bestandsaudits |
| 5 | Umstellung bestehender Audits: Neuberechnung oder Bestandsschutz? | Entscheidung |

---

## 13. Migration der Bestandsdaten

Die Umstellung auf Version 2026.1 verändert Scores. Empfohlenes Vorgehen:

1. Neues Feld `standard_version` auf der Audit-Tabelle, Bestandsdatensätze auf `2025.x`
2. Bestandsaudits **nicht** neu berechnen — die Rohdaten für die neuen Kriterien liegen
   nicht vor
3. Im Bericht alter Audits einen Hinweis anzeigen: „Bewertet nach Version 2025.x"
4. Beim ersten Folge-Audit nach Umstellung im Kundenbericht ausweisen, dass der Sprung
   auf eine Methodenänderung zurückgeht

**Ohne Punkt 4 sieht jeder Kunde eine unerklärte Score-Änderung und ruft an.**
