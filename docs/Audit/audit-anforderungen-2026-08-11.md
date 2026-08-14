# Audit-Anforderungskatalog

**Angelegt:** 2026-08-11 · **Zuletzt:** 2026-08-13
**Status:** **umgesetzt und produktiv** — die acht Entscheidungen aus § 4 sind
gefallen, der Soll-Katalog aus § 3 ist gebaut und seit dem 13.08. auf `main`.
**Betrifft:** `services/audit_criteria.py` (Wahrheitsquelle), `audit_collectors.py`,
`audit_pagespeed.py`, `audit_scoring.py`, `audit_ai.py`, `audit_runner.py`,
`routers/audit.py`, `frontend/src/components/AuditReport.jsx`

---

## 0. Stand in einem Absatz

Der Katalog wurde am 11.08. als Entwurf geschrieben, weil das Audit 38 Kriterien
anzeigte und dafür 12 Datenpunkte erhob — der Rest war geraten oder konstant.
Das ist erledigt: Es gibt jetzt **eine** Kriterien-Datei, aus der Scoring, Prompt
und API-Antwort abgeleitet werden, **27 der 38 Kriterien werden gemessen**,
4 abgeleitet, 7 sind ausgewiesene KI-Einschätzungen. Nicht erhobene Kriterien
fallen aus Zähler *und* Nenner — es wird nie eine fehlende Messung als „0 Punkte"
verkauft. Was offen bleibt, steht in § 6.

### Der gebaute Katalog

| Kategorie | P | Kriterien |
|---|---|---|
| **Recht & Compliance** | 20 | Impressum (§ 5 DDG) (6), Datenschutzerklärung (DSGVO) (6), Cookie-Consent (TDDDG) (4), Barrierefreiheitserklärung (BFSG) (2), Formular DSGVO-konform (2) |
| **Sicherheit & Datenschutz** | 10 | TLS-Zertifikat gültig (3), HTTP→HTTPS erzwungen (2), Security-Header (3), Drittanbieter ohne Einwilligung (2) |
| **Performance & Core Web Vitals** | 15 | LCP (4), CLS (3), INP (2), Mobile-Performance (3), Bildoptimierung (3) |
| **Barrierefreiheit (WCAG/BFSG)** | 10 | Lighthouse-A11y-Score (3), Farbkontraste (2), Alt-Texte (2), Semantik & Struktur (2), Tastaturbedienung (1) |
| **SEO & Auffindbarkeit** | 15 | Title & Meta (3), Überschriften & Content-Tiefe (2), Indexierbarkeit (3), Strukturierte Daten (3), Lokale Signale (3), Keine defekten Links (1) |
| **Design & Gestaltung** | 10 | Visuelle Aktualität (3), Typografie (2), Farbsystem (2), Bildqualität (2), Mobile Darstellung (1) |
| **Conversion & Nutzerführung** | 15 | Klarheit above the fold (3), Primär-CTA (3), Kontaktwege (3), Vertrauenssignale (3), Angebots-Klarheit (3) |
| **Inhalt & Substanz** | 5 | Eigene Leistungsseiten (2), Aktualität (1), Textqualität (2) |

Summe exakt 100. K.-o.-Kriterien (Level-Deckel) sind scharf: fehlendes Impressum,
fehlende Datenschutzerklärung und ungültiges TLS deckeln hart; Cookies und
Tracking ohne Einwilligung deckeln eine Stufe.

### Die acht Defekte von § 1.1 — alle behoben

| | Befund vom 11.08. | Stand 13.08. |
|---|---|---|
| **D1** | Ohne PageSpeed-Key erfindet das Audit Zahlen | ✅ Ohne Key wird es als `nicht erhoben` ausgewiesen (`used_api_key`, `kontingent_ohne_api_key`) und fällt aus der Wertung |
| **D2** | Barrierefreiheit zu 100 % geraten, A11y-Score verworfen | ✅ Lighthouse-Accessibility wird geparst und bewertet; Kategorie von 20 auf 10 P |
| **D3** | SSL nicht geprüft, Seitenabruf mit `verify=False` | ✅ Echter TLS-Handshake, `SSLCertVerificationError` wird ausgewertet — und ist K.-o. |
| **D4** | SEO komplett geraten, `qa_scanner` ungenutzt | ✅ `qa_scanner`, `hosting_scraper` und `link_checker` sind verdrahtet |
| **D5** | 20 von 38 Kriterien sind Konstanten | ✅ 27 gemessen, 4 abgeleitet, 7 ausgewiesene KI-Einschätzung, 0 Konstanten |
| **D6** | UX-Rechenfehler (6 Kriterien à 1 P, gedeckelt auf 5) | ✅ Kategorien summieren auf exakt 100 |
| **D7** | Nur die Startseite wird geladen | ✅ Impressum- und Datenschutz-Unterseite werden gesucht, geladen und auf Pflichtinhalte geprüft |
| **D8** | Kein Kriterium für Design/Gestaltung | ✅ Design 10 P und Conversion 15 P, mit Screenshot und festem Rubric |

---

## 1. Befund vom 11.08. — der Ausgangszustand *(historisch)*

> Dieser Abschnitt beschreibt den Stand **vor** dem Umbau. Er bleibt stehen,
> weil er begründet, warum der Katalog so aussieht, wie er aussieht.

Der Report zeigt **38 Kriterien** an (33 mit Punkten + 5 Hosting-Kriterien ohne Punkte).
Erhoben werden dafür **12 Datenpunkte**. Der Rest wird geschätzt oder ist eine fest
einkodierte Konstante.

**Die 12 real erhobenen Signale:**

| Signal | Wie erhoben | Qualität |
|---|---|---|
| Erreichbarkeit + Status-Code | GET auf Startseite | belastbar |
| „https://" im URL-String | String-Vergleich | **kein Zertifikatscheck** |
| Wort „impressum" im HTML | Keyword-Suche | schwach |
| Wort „datenschutz" im HTML | Keyword-Suche | schwach |
| Wort „cookie" im HTML | Keyword-Suche | **fast immer falsch positiv** |
| LCP | PageSpeed API | belastbar *(wenn Key gesetzt)* |
| CLS | PageSpeed API | belastbar *(wenn Key gesetzt)* |
| INP | PageSpeed API | **liefert real nie einen Wert** (Lab-Daten enthalten INP nicht) |
| Performance-Score | PageSpeed API | belastbar *(wenn Key gesetzt)* |
| Mobile-Score | = Performance-Score | **kein eigener Wert, reine Dublette** |
| HSTS / CSP / X-Frame / X-Content | HEAD-Request | belastbar |

### 1.1 Die gravierendsten Defekte

**D1 — Ohne PageSpeed-Key erfindet das Audit Zahlen.**
`GOOGLE_PAGESPEED_API_KEY` ist lokal leer. Ist kein Key gesetzt, gibt die Funktion
fest LCP 3,8 s / CLS 0,18 / INP 320 ms / Score 55 zurück — für **jede** Website,
identisch. Der Report weist diese Werte als Messung aus. Auf Render muss geprüft
werden, ob der Key dort gesetzt ist.

**D2 — Barrierefreiheit ist die zweitgrößte Kategorie (20 P) und wird zu 100 % geraten.**
Der Fallback vergibt fix 3+2+2+3 = 10 von 20 Punkten an jede Website der Welt.
Gleichzeitig fordert der PageSpeed-Aufruf bereits `category=accessibility` an —
das Ergebnis wird geholt und dann weggeworfen.

**D3 — SSL wird nicht geprüft.** `si_ssl` gibt 4 von 4 Punkten, sobald die URL mit
`https://` beginnt. Zusätzlich läuft der Seitenabruf mit `verify=False`, d. h. ein
abgelaufenes, selbstsigniertes oder auf eine fremde Domain ausgestelltes Zertifikat
fällt nirgends auf und bekommt die volle Punktzahl.

**D4 — SEO (10 P) wird komplett geraten.** Im Fallback fix 2+0+1 = 3 Punkte.
Dabei liegen Title, Meta-Description, H1, Canonical, OG-Tags, Schema.org, robots.txt
und sitemap.xml in `services/qa_scanner.py` bereits als echte Checks vor — nur nicht
im Audit verdrahtet.

**D5 — 20 der 38 Kriterien sind reine Konstanten.** Urheberrecht (2), E-Commerce (2),
Bildoptimierung (1), Drittanbieter (2), Formularsicherheit (1), alle vier
Barrierefreiheits-Kriterien, alle drei SEO-Kriterien, alle sechs UX-Kriterien,
Hosting-Anbieter (1), Backup (0), CDN (0).

**D6 — Die UX-Kategorie hat einen Rechenfehler.** Sechs Kriterien à 1 Punkt = 6,
gedeckelt auf max. 5. Ein Kriterium ist damit strukturell wertlos.

**D7 — Nur die Startseite wird geladen.** „Impressum vorhanden" heißt real: das Wort
steht irgendwo im Startseiten-HTML. Ob `/impressum` existiert, erreichbar ist oder
die Pflichtangaben nach § 5 DDG enthält, wird nie geprüft.

**D8 — Kein einziges Kriterium für Design/Gestaltung.** Conversion ist mit 1 Punkt
(`ux_cta`) vertreten — obwohl `docs/conversion-spec-shk.md` verbindlich ist und
Conversion das eigentliche Verkaufsargument von KOMPAGNON darstellt.

### 1.2 Was bereits im Haus liegt und ungenutzt ist

| Baustein | Kann heute schon | Im Audit genutzt |
|---|---|---|
| `services/qa_scanner.py` | ~45 echte Checks: Title, Meta, H1/H2, Canonical, OG, Schema (inkl. LocalBusiness/FAQ), robots.txt, sitemap.xml, Viewport, Alt-Text-Quote, Formular, tel:/mailto:, Google Fonts extern, Maps, DSGVO-Checkbox, BFSG-Hinweis, HTTPS-Redirect, Cache-Header, llms.txt | **nein** |
| `services/hosting_scraper.py` | Hosting-Provider via IP/ASN, WordPress-Erkennung | **nein** |
| `services/link_checker.py` | Broken Links | **nein** |
| `services/screenshot.py` | Screenshot | nur als Bild, nicht zur Bewertung |
| PageSpeed `accessibility` | Lighthouse-A11y-Score | angefordert, verworfen |

Der Umbau ist deshalb überwiegend **Verdrahtung vorhandener Teile**, nicht Neubau.

---

## 2. Der alte Katalog — alle 38 Kriterien *(historisch, ersetzt)*

Legende Datenquelle: 🟢 gemessen · 🟡 schwach/abgeleitet · 🔴 Konstante oder KI-Rateschätzung

### Rechtliche Compliance — 30 Punkte

| Kriterium | P | Quelle | Anmerkung |
|---|---|---|---|
| Impressum (TMG/DDG) | 7 | 🟡 | Keyword im Startseiten-HTML, keine Inhaltsprüfung |
| Datenschutzerklärung (DSGVO) | 7 | 🟡 | dito |
| Cookie Consent (TDDDG) | 6 | 🟡 | Wort „cookie" genügt — falsch positiv |
| Barrierefreiheitserklärung (BFSG) | 4 | 🔴 | Fallback immer 0 |
| Urheberrecht & Lizenzen | 3 | 🔴 | Konstante 2 |
| E-Commerce-Pflichten | 3 | 🔴 | Konstante 2 |

### Technische Performance — 20 Punkte

| Kriterium | P | Quelle | Anmerkung |
|---|---|---|---|
| LCP | 5 | 🟢 | nur mit PSI-Key |
| CLS | 4 | 🟢 | nur mit PSI-Key |
| INP | 3 | 🔴 | Lab-Daten liefern INP nicht → praktisch immer 0 P |
| Mobile-First Design | 4 | 🟡 | identisch mit Performance-Score |
| Bildoptimierung | 4 | 🔴 | Konstante 1 |

### Barrierefreiheit — 20 Punkte

| Kriterium | P | Quelle | Anmerkung |
|---|---|---|---|
| Farbkontraste (WCAG AA) | 5 | 🔴 | Konstante 3 |
| Tastaturzugänglichkeit | 5 | 🔴 | Konstante 2 |
| Screenreader-Kompatibilität | 5 | 🔴 | Konstante 2 |
| Lesbarkeit & Textgröße | 5 | 🔴 | Konstante 3 |

### Sicherheit & Datenschutz — 15 Punkte

| Kriterium | P | Quelle | Anmerkung |
|---|---|---|---|
| HTTPS / SSL-Zertifikat | 4 | 🟡 | nur String-Präfix, kein Zertifikatscheck |
| Security-Header | 4 | 🟢 | HSTS, CSP, X-Frame, X-Content-Type |
| DSGVO Drittanbieter | 4 | 🔴 | Konstante 2 |
| Formularsicherheit | 3 | 🔴 | Konstante 1 |

### SEO & Sichtbarkeit — 10 Punkte

| Kriterium | P | Quelle | Anmerkung |
|---|---|---|---|
| Technische SEO-Grundlagen | 4 | 🔴 | Konstante 2 |
| Strukturierte Daten | 3 | 🔴 | Konstante 0 |
| Lokale Auffindbarkeit | 3 | 🔴 | Konstante 1 |

### Inhalt & Nutzererfahrung — 5 Punkte (6 Kriterien!)

| Kriterium | P | Quelle | Anmerkung |
|---|---|---|---|
| Erster Eindruck | 1 | 🔴 | Konstante |
| Klare Call-to-Action | 1 | 🔴 | Konstante |
| Navigation & Struktur | 1 | 🔴 | Konstante |
| Vertrauenssignale | 1 | 🔴 | Konstante |
| Content-Qualität | 1 | 🔴 | Konstante |
| Kontaktmöglichkeiten | 1 | 🔴 | Konstante — Summe 6 wird auf 5 gekappt |

### Hosting & Infrastruktur — 0 Punkte (nur Anzeige)

| Kriterium | Quelle | Anmerkung |
|---|---|---|
| Anbieter identifizierbar | 🔴 | Konstante 1, obwohl `hosting_scraper` es messen könnte |
| Erreichbarkeit | 🟢 | |
| HTTP→HTTPS-Weiterleitung | 🟡 | prüft nicht die Weiterleitung, nur das URL-Präfix |
| Backup-Hinweise | 🔴 | von außen prinzipiell nicht prüfbar → sollte raus |
| CDN aktiv | 🔴 | Konstante 0, wäre über Response-Header messbar |

**Zusammenfassung Ist:** 4 Kriterien belastbar gemessen · 6 schwach · **28 geraten oder konstant**

---

## 3. Soll-Katalog — **umgesetzt**

Leitgedanken:

1. **Nichts behaupten, was nicht erhoben wurde.** Jedes Kriterium bekommt eine
   Quellen-Kennzeichnung, die auch im Report und PDF sichtbar ist.
2. **Gewicht folgt Messbarkeit und Verkaufsrelevanz.** Barrierefreiheit runter
   (20 → 10, weil von außen nur begrenzt prüfbar), Conversion und SEO hoch.
3. **Design und Conversion werden eigene Kategorien** — genau die zwei Dinge, die
   der Kunde auf seiner Seite sieht und die KOMPAGNON verkauft.
4. **K.-o.-Kriterien**: Rechtliche Totalausfälle deckeln das Level unabhängig vom Score.

### 3.1 Kategorien und Gewichtung

| # | Kategorie | Ist | **Soll** | Begründung |
|---|---|---|---|---|
| 1 | Recht & Compliance | 30 | **20** | bleibt schwer, aber 30 war überzogen; K.-o.-Regel fängt das Risiko ab |
| 2 | Sicherheit & Datenschutz | 15 | **10** | vollständig messbar, aber kein Verkaufsargument |
| 3 | Performance & Core Web Vitals | 20 | **15** | messbar, wichtig, aber nicht dominant |
| 4 | Barrierefreiheit (WCAG/BFSG) | 20 | **10** | von außen nur teilweise prüfbar — 20 P waren nicht belegbar |
| 5 | SEO & Auffindbarkeit | 10 | **15** | vollständig messbar, direkter Umsatzhebel |
| 6 | **Design & Gestaltung** | – | **10** | neu — Kernanforderung |
| 7 | **Conversion & Nutzerführung** | 5 | **15** | neu gewichtet — das eigentliche Verkaufsargument |
| 8 | Inhalt & Substanz | (in UX) | **5** | eigenständig |
| – | Infrastruktur-Befund | 0 | **0** | rein informativ, für die Angebotskalkulation |
| | **Summe** | 100 | **100** | |

### 3.2 Kriterien im Detail

#### 1 — Recht & Compliance (20 P)

| Code | Kriterium | P | Erhebung |
|---|---|---|---|
| L1 | Impressum erreichbar **und** Pflichtangaben vollständig (Name, Anschrift, Kontakt, Vertretungsberechtigter, USt-ID/HRB, Kammer bei Handwerk) | 6 | 🟢 Unterseite laden + Feldprüfung |
| L2 | Datenschutzerklärung erreichbar **und** Pflichtinhalte (Verantwortlicher, Zwecke, Rechtsgrundlagen, Betroffenenrechte, Auftragsverarbeiter) | 6 | 🟢 Unterseite laden + Feldprüfung |
| L3 | Cookie-Consent real vorhanden (bekanntes CMP-Skript erkannt, kein Setzen vor Einwilligung) | 4 | 🟢 Skript-Erkennung + Cookie-Vergleich vor/nach |
| L4 | Barrierefreiheitserklärung (BFSG) — nur bewertet, wenn anwendbar | 2 | 🟢 Keyword + Unterseite |
| L5 | Kontaktformular DSGVO-konform (Einwilligungs-Checkbox, Link zur DSE, HTTPS-Ziel) | 2 | 🟢 DOM-Prüfung |

#### 2 — Sicherheit & Datenschutz (10 P)

| Code | Kriterium | P | Erhebung |
|---|---|---|---|
| S1 | TLS-Zertifikat gültig (nicht abgelaufen, Kette korrekt, Domain passt) | 3 | 🟢 echter Handshake statt `verify=False` |
| S2 | HTTP→HTTPS-Weiterleitung erzwungen | 2 | 🟢 Redirect-Test |
| S3 | Security-Header (HSTS, CSP, X-Frame-Options, X-Content-Type-Options) | 3 | 🟢 vorhanden |
| S4 | Keine einwilligungsfreien Drittanbieter (Google Fonts extern, Maps, Analytics vor Consent) | 2 | 🟢 Netzwerk-/HTML-Analyse |

#### 3 — Performance & Core Web Vitals (15 P)

| Code | Kriterium | P | Erhebung |
|---|---|---|---|
| P1 | LCP | 4 | 🟢 PSI |
| P2 | CLS | 3 | 🟢 PSI |
| P3 | INP (Feld) bzw. TBT (Lab, als Ersatzindikator) | 2 | 🟢 PSI + CrUX |
| P4 | Mobile-Performance eigenständig gemessen | 3 | 🟢 PSI Strategy `mobile` **und** `desktop` |
| P5 | Bildoptimierung (Format WebP/AVIF, Dateigrößen, `loading="lazy"`, feste Dimensionen) | 3 | 🟢 DOM + HEAD auf Bild-URLs |

#### 4 — Barrierefreiheit (10 P)

| Code | Kriterium | P | Erhebung |
|---|---|---|---|
| B1 | Lighthouse-Accessibility-Score | 3 | 🟢 PSI (wird heute schon geholt) |
| B2 | Farbkontraste WCAG AA | 2 | 🟢 aus Lighthouse-Audit `color-contrast` |
| B3 | Alt-Text-Quote der Inhaltsbilder | 2 | 🟢 DOM |
| B4 | Semantik (genau eine H1, saubere Hierarchie, `lang`-Attribut, Formular-Labels) | 2 | 🟢 DOM |
| B5 | Tastaturbedienung (sichtbarer Fokus, Skip-Link, keine Tastaturfallen) | 1 | 🟡 Lighthouse + DOM-Heuristik |

#### 5 — SEO & Auffindbarkeit (15 P)

| Code | Kriterium | P | Erhebung |
|---|---|---|---|
| E1 | Title & Meta-Description (vorhanden, Länge, Ort + Leistung enthalten) | 3 | 🟢 DOM |
| E2 | Heading-Struktur & Content-Tiefe (Wortanzahl, H2-Gliederung) | 2 | 🟢 DOM |
| E3 | Indexierbarkeit (robots.txt, sitemap.xml, Canonical, kein versehentliches `noindex`) | 3 | 🟢 HTTP |
| E4 | Strukturierte Daten (LocalBusiness, Service, FAQ, Bewertungen) | 3 | 🟢 JSON-LD-Parsing |
| E5 | Lokale Signale (NAP konsistent, Ort in Title/H1, Google-Business-Verknüpfung, Karte) | 3 | 🟢 DOM + Abgleich |
| E6 | Keine defekten Links | 1 | 🟢 `link_checker` |

#### 6 — Design & Gestaltung (10 P) — NEU

Erhebung über Screenshot (Desktop + Mobile) und DOM. Bewertung durch Claude anhand
eines festen Rubrics, im Report klar als Einschätzung gekennzeichnet.

| Code | Kriterium | P | Erhebung |
|---|---|---|---|
| D1 | Visuelle Aktualität — wirkt das Layout zeitgemäß oder wie 2012? | 3 | 🔵 KI auf Screenshot |
| D2 | Typografie & Lesbarkeit (Schriftgrößen, Zeilenlänge, klare Hierarchie) | 2 | 🟡 KI + DOM-Messung |
| D3 | Farbsystem & Konsistenz (begrenzte Palette, erkennbare CI, ausreichender Kontrast) | 2 | 🟡 KI + CSS-Analyse |
| D4 | Bildqualität & Authentizität (echte Betriebsfotos vs. generisches Stock, Auflösung) | 2 | 🔵 KI auf Screenshot |
| D5 | Mobile Darstellung fehlerfrei (kein horizontales Scrollen, Tap-Targets ≥ 44 px) | 1 | 🟢 Mobile-Screenshot + DOM |

#### 7 — Conversion & Nutzerführung (15 P) — NEU gewichtet

Basis: `docs/conversion-spec-shk.md`.

| Code | Kriterium | P | Erhebung |
|---|---|---|---|
| C1 | Above the Fold klar: Was, für wen, in welchem Gebiet — in 5 Sekunden erfassbar | 3 | 🔵 KI auf Screenshot + Text |
| C2 | Primär-CTA (vorhanden, ergebnisorientiert formuliert, above the fold, im Verlauf wiederholt) | 3 | 🟡 DOM + KI |
| C3 | Kontaktwege (Telefonnummer klickbar, Formular ≤ 5 Felder, Reaktionszeit benannt) | 3 | 🟢 DOM |
| C4 | Vertrauenssignale (Bewertungen, Referenzen, Zertifikate/Meisterbetrieb, echte Team-Fotos) | 3 | 🟡 DOM + KI |
| C5 | Angebots-Klarheit (Leistungen konkret statt Floskel, Ablauf/Preisrahmen, Risk Reversal) | 3 | 🔵 KI auf Seitentext |

#### 8 — Inhalt & Substanz (5 P)

| Code | Kriterium | P | Erhebung |
|---|---|---|---|
| I1 | Eigene Leistungsseiten je Gewerk statt einer Sammelseite | 2 | 🟢 Crawl der Navigation |
| I2 | Aktualität (datierte Referenzen/News, keine toten Inhalte, kein „© 2019") | 1 | 🟢 DOM |
| I3 | Textqualität (Kundennutzen statt Selbstbeschreibung, keine Worthülsen) | 2 | 🔵 KI auf Seitentext |

#### Infrastruktur-Befund (0 P, nur Information)

CMS/Tech-Stack · Hosting-Provider (ASN) · CDN aktiv · HTTP/2 oder /3 · Domain-Alter ·
Erreichbarkeit/Antwortzeit. Dient der Aufwandsschätzung im Angebot, nicht der Bewertung.

**Entfällt:** „Backup-Hinweise erkennbar" — von außen nicht prüfbar, erzeugt nur Rauschen.

### 3.3 K.-o.-Kriterien (Level-Deckel)

Heute kann eine Website ohne Impressum rechnerisch 78 Punkte und damit „Silber"
erreichen. Das ist nicht vertretbar. Vorschlag:

| Verstoß | Deckel |
|---|---|
| Kein Impressum erreichbar | max. „Nicht konform" |
| Keine Datenschutzerklärung erreichbar | max. „Nicht konform" |
| Kein gültiges TLS-Zertifikat | max. „Nicht konform" |
| Tracking/Fonts ohne Consent | max. „Bronze" |
| Kein Cookie-Consent bei gesetzten Cookies | max. „Bronze" |

Level-Schwellen bleiben: 95 Platin · 85 Gold · 70 Silber · 50 Bronze · darunter nicht konform.

### 3.4 Quellen-Kennzeichnung im Report

Jedes Kriterium wird mit seiner Herkunft ausgewiesen — im UI und im PDF:

| Symbol | Bedeutung |
|---|---|
| 🟢 gemessen | deterministisch über HTTP, DOM oder API erhoben |
| 🟡 abgeleitet | aus gemessenen Werten über feste Regeln berechnet |
| 🔵 Einschätzung | KI-Bewertung auf Screenshot/Text nach festem Rubric |
| ⚪ nicht erhoben | Prüfung nicht möglich — **zählt nicht in den Score**, statt heimlich 0 oder Konstante |

Damit ist der Report gegenüber dem Kunden belastbar und gleichzeitig ehrlich.
Bewusst kein Fallback mehr auf erfundene Werte: fehlt der PageSpeed-Key,
wird die Kategorie als „nicht erhoben" ausgewiesen und der Score auf die
tatsächlich geprüften Kriterien normiert.

### 3.5 Methodische Änderungen

| Bereich | Heute | Soll |
|---|---|---|
| Seitenumfang | nur Startseite | Startseite + Impressum + Datenschutz + Kontakt + bis zu 3 Leistungsseiten |
| Screenshot | 1× Desktop, nur als Bild | Desktop + Mobile, zusätzlich als Bewertungsgrundlage |
| PageSpeed | 1 Aufruf (mobile) | mobile + desktop, plus CrUX-Felddaten |
| TLS | String-Präfix, `verify=False` | echter Handshake mit Zertifikatsprüfung |
| Fehlende Daten | Konstante/Fantasiewert | „nicht erhoben", Score normiert |
| Laufzeit-Budget | 90 s hart | ca. 3–4 min, Fortschritt im Frontend sichtbar |

---

## 4. Entschieden am 2026-08-11 — alle acht wie empfohlen

| # | Frage | Entscheidung und Stand |
|---|---|---|
| 1 | Gewichtung der 8 Kategorien wie in 3.1? | **ja**, gebaut — Summe exakt 100 |
| 2 | Barrierefreiheit 20 → 10 Punkte? | **ja**, gebaut — dazu echter Lighthouse-Score |
| 3 | Conversion 5 → 15 und Design neu mit 10? | **ja**, gebaut |
| 4 | Design/Conversion als gekennzeichnete KI-Einschätzung? | **ja**, gebaut — 7 Kriterien tragen `einschaetzung`, Screenshot + festes Rubric |
| 5 | Laufzeit von 90 s auf ~4 min anheben? | **ja** — Impressum und Datenschutz werden als Unterseiten geladen |
| 6 | PageSpeed-Key beschaffen? | **ja**, im Code erledigt (Abfrage auch ohne Key, `PAGESPEED_API_KEY` als zweiter Name). **Ob er auf Render gesetzt ist, bleibt offen** — § 6 |
| 7 | K.-o.-Regel für Impressum/DSE/TLS? | **ja**, gebaut — `BLOCKING_CRITICAL` (Impressum, DSE, TLS) und `BLOCKING_MAJOR` (Cookies, Tracking) |
| 8 | Backup-Hinweise streichen? | **ja**, gestrichen |

---

## 5. Umsetzung — Stand der sieben Schritte

| # | Schritt | Stand |
|---|---|---|
| 1 | Kriterienkatalog als eigenes Modul | ✅ `services/audit_criteria.py`, einzige Wahrheitsquelle für Scoring, Prompt und API |
| 2 | `qa_scanner`, `hosting_scraper`, `link_checker` verdrahten | ✅ in `audit_runner.py` |
| 3 | Echte Erheber: TLS, Unterseiten, Bildanalyse, Consent | ✅ `audit_collectors.py` — `check_tls`, `check_https_redirect`, `check_legal_pages`, `analyse_images`, `detect_consent`, `detect_third_parties` |
| 4 | KI auf Design/Conversion/Text begrenzen, Screenshot + Rubric | ✅ `audit_ai.py` |
| 5 | DB-Migration für die neuen Spalten | ✅ in `main.py::_run_migrations` — der einzigen Liste, die beim Start läuft |
| 6 | Tests je Kategorie gegen eine feste Referenz-Website | ⬜ **offen** — 46 Tests prüfen Katalog und Rechenwege, aber gegen erfundene Eingaben |
| 7 | Report und PDF um Quellen-Kennzeichnung erweitern | ⬜ **nicht verifiziert** — die Erhebungsart steht im Modell und in der API; ob sie beim Leser ankommt, wurde nicht geprüft |

---

## 6. Was an diesem Katalog offen bleibt

1. **PageSpeed-Schlüssel auf Render.** Im Code ist beides gelöst: Abfrage auch
   ohne Key, und `PAGESPEED_API_KEY` wird als zweiter Name akzeptiert. Ob
   produktiv ein Schlüssel gesetzt ist, war von hier nicht prüfbar. Ohne ihn
   bleiben die Core Web Vitals dauerhaft „nicht erhoben“ — ehrlich, aber
   15 Punkte weniger Aussage.
2. **Referenz-Website für die Tests** (Schritt 6). Ohne sie prüfen die Tests die
   Rechenwege, nicht die Erhebung.
3. **Quellen-Kennzeichnung im Report** (Schritt 7). Nachsehen, ob „gemessen /
   abgeleitet / KI-Einschätzung / nicht erhoben“ beim Kunden sichtbar ist — das
   ist die Stelle, an der der ganze Umbau für den Leser überhaupt erkennbar wird.
4. **Der umgebaute Katalog ist nie gegen eine echte fremde Website gelaufen.**
   Ein Lauf gegen zwei, drei reale SHK-Seiten würde zeigen, ob die Punktzahlen
   plausibel sind. Das ist der wichtigste der vier Punkte.
5. **Die Erkennung ist gebaut, die Branchen-Ausweitung nicht.** *(Stand
   2026-08-14, siehe § 7)* Was unten als Befund steht, ist behoben: Das Audit
   erkennt jetzt, was es vor sich hat, und lässt den fremden Maßstab weg. Offen
   bleibt die Ausweitung auf weitere Gewerke und Branchen — die
   Geschäftsentscheidung.

   Der ursprüngliche Befund: **Das Audit unterstellte jeder Seite ein
   Handwerksgewerk — auch wenn keins da war.** (David, 2026-08-14) Ein Bericht
   aus dem Staging-Widget bewertete den
   Auftritt eines politischen Kandidaten gegen den SHK-Maßstab: „Für
   Hausbesitzer, die z. B. ein Dach, eine Wärmepumpe oder ein Bad suchen, gibt
   es hier keinen Anknüpfungspunkt … es fehlen Leistungsbeschreibungen,
   Einsatzgebiet, Preisrahmen." Fachlich richtig gerechnet, als Aussage
   unbrauchbar — und der Empfänger liest, dass wir seine Seite nicht verstanden
   haben. Das Widget ist ein Akquisekanal; der Bericht ist dort der erste
   Eindruck.

   Die Ursache steht fest verdrahtet in `services/audit_ai.py:35`: Der
   Systemprompt setzt „Websites von Handwerksbetrieben (Heizung, Sanitär,
   Elektrik)" und als Maßstab „Hausbesitzer, die eine Wärmepumpe, ein Bad oder
   eine Wallbox suchen". Das erhobene Feld `trade` wird zwar als `gewerk`
   mitgegeben (`audit_ai.py:113`), kann den festen Rahmen aber nicht
   verschieben. Dieselbe Annahme steckt in `docs/conversion-spec-shk.md` und
   damit in der QA und den Templates.

   Darin stecken zwei Dinge, die getrennt gehören:

   - **Die Erkennung.** Das Audit muss benennen können, was es vor sich hat —
     einschließlich „kein Handwerksbetrieb". Die sieben KI-Kriterien müssten
     dann entweder gegen den passenden Maßstab laufen oder wie eine nicht
     erhobene Messung aus Zähler *und* Nenner fallen, statt gegen einen
     fremden Maßstab gerechnet zu werden. Das ist ein Defekt und unabhängig
     von jeder Strategiefrage.
   - **Die Ausweitung** der Bewertung — und später der Ausführung von Online
     fertig / WebSprint — auf weitere Gewerke und Branchen. Das ist eine
     Geschäftsentscheidung und berührt die Nischenregel der Phase 1 (Heizung /
     Sanitär / Elektrik, keine Erweiterung vor fünf produktiven Kunden). Der
     Maßstab je Branche ist dabei die eigentliche Arbeit, nicht die Technik:
     Conversion-Spec, Kriteriengewichte und Templates hängen daran.

   Die Erkennung ist gebaut (§ 7), die Ausweitung nicht.

---

## 7. Die Erkennung — gebaut am 2026-08-14

Das Audit erkennt jetzt, was es vor sich hat, bevor es bewertet. Der
Systemprompt schrieb bis dahin „Websites von Handwerksbetrieben (Heizung,
Sanitär, Elektrik)" und als Maßstab „Hausbesitzer, die eine Wärmepumpe, ein Bad
oder eine Wallbox suchen" fest — beides ist raus. Der Maßstab leitet sich jetzt
aus der erkannten Branche ab.

**Zwei neue Felder in der KI-Antwort** (`services/audit_ai.py`, im Schema
verlangt): `branche` — was die Seite konkret ist, vom Gewerk bis zu „politischer
Kandidat", „Verein", „Blog" — und `betriebsseite` — steht dahinter ein Betrieb,
der über diese Website Kunden für seine Leistungen gewinnen will?

**Drei Kriterien setzen einen Betrieb voraus** und sind im Katalog als
`assumes_business` markiert: `cv_klarheit`, `cv_angebot`, `ih_textqualitaet`.
Ist `betriebsseite` false, fallen sie aus Zähler *und* Nenner — dieselbe
Mechanik wie bei einer nicht erhobenen Messung. Die vier Gestaltungskriterien
(`dg_*`) bleiben bewertet: Typografie, Farbkontrast, Bildqualität und
Aktualität gelten für jede Seite, unabhängig davon, wer dahintersteht.

**Wer entscheidet, ist der Code, nicht der Prompt.** Das Modell erkennt und
meldet; verworfen wird in `audit_scoring._apply_ai()` anhand des
Katalog-Merkmals. Fehlt die Angabe ganz — altes Ergebnis, Modell hat das Feld
nicht gefüllt —, bleibt es beim vorherigen Verhalten: nichts wird verworfen,
weil ein Feld leer blieb.

**Der Leser erfährt den Grund.** `collection_notes()` trägt
`angebotskriterien: keine_betriebsseite` mit der erkannten Art der Seite als
Detail ein, der Report zeigt „kein Betrieb erkannt — Maßstab nicht anwendbar".
Und die KI-Zusammenfassung sagt es im ersten Satz, weil der Prompt es verlangt —
im Lauf gegen das echte Modell: „Diese Bewertung ist eigentlich für Handwerks-
und Dienstleistungsbetriebe gemacht, deshalb passt sie auf Ihre Kandidatenseite
nur teilweise." Das ist die Stelle, die im Widget zuerst gelesen wird.

**Geprüft gegen das echte Modell**, drei Seiten:

| Seite | erkannt als | `betriebsseite` | Angebotskriterien | Gestaltung |
|---|---|---|---|---|
| Kandidatenauftritt | politischer Kandidat (Stadtratswahl) | false | nicht erhoben | bewertet |
| Dachdeckerei | Dachdecker (mit Zimmerei, Bauklempnerei) | true | bewertet | bewertet |
| SHK-Betrieb | Heizung und Sanitär (SHK-Meisterbetrieb) | true | bewertet | bewertet |

Der Dachdecker wird gegen seinen eigenen Maßstab bewertet, ohne dass Wärmepumpe
oder Bad noch vorkommen — der SHK-Fall bleibt unverändert. Das ist ausdrücklich
**keine** Branchen-Ausweitung: bewertet wird fair, verkauft wird weiter in der
Nische der Phase 1.

Offen bleibt: `trade` aus den Stammdaten und die erkannte `branche` können
auseinanderlaufen. Die Erkennung korrigiert nur die Bewertung, sie schreibt den
Stammdatensatz nicht zurück.
