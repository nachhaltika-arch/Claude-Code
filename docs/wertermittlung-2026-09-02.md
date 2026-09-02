# Wertermittlung KOMPAGNON

> **Zweck:** Bewertung des Softwaresystems KOMPAGNON für die Übertragung auf ein
> Unternehmen. In Anlehnung an IDW S5 (Bewertung immaterieller Vermögenswerte).
>
> **Stichtag:** 2026-09-02 · **Quellstand:** `2c17fe8` auf `staging`
>
> **Keine Rechts- oder Steuerberatung, kein Wirtschaftsprüfer-Gutachten.** Alle
> Mengenangaben sind am Quellcode gemessen und reproduzierbar; Aufwandssätze,
> Lizenzsatz, Zins und Wertminderungen sind begründete Annahmen.
>
> Fassung für den Bildschirm: Artefakt
> `https://claude.ai/code/artifact/88dfed66-acea-495e-a4a3-96ddba2702ed`

---

## 0 · Ergebnis

| Verfahren | Ergebnis |
|---|---|
| Kapitalwertorientiert (Lizenzpreisanalogie) | 60.000 – 130.000 € |
| Ist-Herstellungskosten (aus der Versionsgeschichte) | 80.000 – 115.000 € |
| Marktvergleich (nur Plausibilität) | 73.000 – 292.000 € |
| **Kostenorientierter Zeitwert** (Nachbau ./. Wertminderung) | **290.000 – 400.000 €** |
| Nachbaukosten neu (767 PT) | 610.000 – 845.000 € |

**Empfehlung für den wahrscheinlichsten Fall — Einbringung in die eigene
Gesellschaft: 100.000 €.**

Belegt durch die Ist-Herstellungskosten, oberhalb des Ertragswerts, weit
unterhalb der Nachbaukosten. Der Abstand nach unten ist der Puffer gegen die
Differenzhaftung nach § 9 GmbHG.

---

## 1 · Was übertragen wird

### A · Übertragungsgegenstand

| Bestandteil | Umfang | Anmerkung |
|---|---|---|
| Quellcode mit Versionsgeschichte | 1.415 Dateien · 1.857 Commits | vollständige Historie seit 2026-03-29 |
| Backend (Python/FastAPI) | 39.941 Codezeilen · 452 Endpunkte | 88 Routerdateien, 124 Fachdienste |
| Frontend (React) | 63.403 Codezeilen · 77 Bildschirme | 130 wiederverwendbare Bausteine |
| Datenmodell und Migrationen | 66 Tabellen | 39 im ORM, 27 in rohem SQL |
| Prüfstrecke | 2.276 Tests · 12 E2E-Strecken | 270 Testdateien, in der CI verankert |
| Bausteinbibliothek für Kundenseiten | 6.881 Zeilen HTML | MIT-Quellen plus eigene SHK-Vorlagen |
| Betriebseinrichtung | 2 Umgebungen · 28 Zeitaufträge | CI mit vier Prüfjobs, Render-Blueprints |
| Dokumentation | 216 Dateien · 32.226 Zeilen | Lagebild, Modulkarte, Tagesberichte |
| Fachkonzept | 39 Prüfkriterien · 8 Kategorien | Angebotsbaukasten, Conversion-Spec, Gestaltungsrichtlinie |
| Marke und Gestaltung | Logopaket, CI-Vorgaben | Vektor- und Druckdateien, Hausschriften |
| Buchmanuskript und Satzsystem | 772 Zeilen Satzcode | eigenständiges Werk — gesondert bewerten |

### B · Was nicht automatisch mitgeht

| Position | Status | Was zu tun ist |
|---|---|---|
| Anbieterkonten (Render, Stripe, Brevo, Netlify, Anthropic, Google, Northdata, Trackdesk u. a.) | 12 Dienste | je Dienst Vertragsübernahme oder Neuabschluss; 68 Umgebungsvariablen umschlüsseln |
| Domains `kompagnon.group`, `kas.`, `api.` | offen | Umschreibung beim Registrar, getrennt vom Codevertrag |
| GrapesJS Studio SDK | prüfen | kommerzielle Lizenz — Übertragbarkeit beim Anbieter klären |
| Envato-Vorlagen | prüfen | kontogebunden, in der Regel nicht übertragbar |
| Relume-Bausteine | bereits entfernt | Entscheidung 2026-05-06 dokumentiert, nur Markerordner verblieben |
| Personenbezogene Daten (`leads`, `customers`, `communications`, Uploads) | DSGVO | Rechtsgrundlage klären, Betroffene informieren |
| Fachliteratur (64 PDFs in der Ablage) | nicht Bestandteil | fremde Werke, ausdrücklich ausnehmen |

---

## 2 · Methodik

| Verfahren | Umsetzung | Belastbarkeit |
|---|---|---|
| Kostenorientiert | Ist-Kosten aus der Versionsgeschichte; Wiederbeschaffung aus dem gemessenen Mengengerüst | **hoch** — jede Größe am Quellstand nachzählbar |
| Kapitalwertorientiert | Lizenzpreisanalogie auf die Preise der Produktdatenblätter | mittel — Mengengerüst ist Annahme, kein Ist |
| Marktpreisorientiert | Erfahrungswerte für Übernahmen vorumsatzlicher Systeme | gering — keine echten Vergleichstransaktionen |

---

## 3 · Der Befund: das System in Zahlen

Gemessen am Stand `2c17fe8`, ohne Leer- und Kommentarzeilen.

| Bereich | Zeilen gesamt | Kommentar | reiner Code |
|---|---:|---:|---:|
| Backend-Anwendung (Python) | 69.958 | 19.157 | 39.941 |
| Frontend (React) | 76.085 | 6.819 | 63.403 |
| Backend-Tests | 44.559 | 10.621 | 22.882 |
| Bausteinbibliothek (HTML) | 7.572 | 0 | 6.881 |
| Werkzeuge und Skripte | 4.762 | 973 | 3.054 |
| Gestaltung (CSS) | 1.427 | 111 | 1.170 |
| Buch-Satzsystem | 1.274 | 325 | 772 |
| E2E-Strecken | 707 | 152 | 446 |
| **Summe** | **206.344** | **38.158** | **138.549** |

Weitere gemessene Größen: 452 API-Endpunkte · 66 Datenbanktabellen · 77
Bildschirme · 130 Bausteine · 94 Frontend-Routen · 36 Menüpunkte · 2.288 Tests ·
28 Zeitaufträge · 12 Fremddienste · 11 Fachmodule · 51 Arbeitstage.

### Wertaufteilung nach Modulen

Schlüssel ist der gemessene Umfang der Fachrouter — die einzige Größe, die den
Zusammenhang im Code abbildet und nicht den im Kopf. Die Anteilsspalte ist der
Verteilungsschlüssel für eine Kaufpreisaufteilung im Vertrag.

| Modul | Routerzeilen | Endpunkte | Anteil | Reifegrad |
|---|---:|---:|---:|---|
| M6 Website-Bau (KAS) | 7.497 | 69 | 22,6 % | in Arbeit |
| M5 Projektabwicklung | 6.879 | 71 | 20,7 % | trägt |
| M1 Akquise | 3.697 | 56 | 11,1 % | in Arbeit |
| M3 Vertrieb | 3.276 | 51 | 9,9 % | trägt |
| M0 Fundament | 3.145 | 60 | 9,5 % | trägt |
| M4 Angebot und Zahlung | 2.714 | 34 | 8,2 % | trägt |
| M2 Audit und Bewertung | 1.813 | 26 | 5,5 % | trägt |
| M8 Akademie | 1.311 | 34 | 3,9 % | gebaut, ohne Inhalt |
| M7 Kundenportal | 908 | 13 | 2,7 % | trägt |
| M10 Werbung | 848 | 18 | 2,6 % | unfertig |
| Buch und Versand | 826 | 7 | 2,5 % | in Arbeit |
| M9 Betreuung | 332 | 12 | 1,0 % | in Arbeit |
| **Summe** | **33.246** | **451** | **100,0 %** | |

---

## 4 · Kostenorientierter Wert

### 4.1 · Tatsächliche Herstellungskosten

Der Aufwand ist aus den Zeitstempeln der Versionsgeschichte abgeleitet: **51
Tage mit Arbeitsständen, davon 43 mit einer Arbeitsspanne von sechs Stunden oder
mehr. Summe aller Tagesspannen: 592 Stunden.**

| Position | Menge | Satz | Betrag |
|---|---:|---:|---:|
| Arbeitstage aus Commit-Spannen (592 h ÷ 8 h) | 74 PT | — | — |
| Zuschlag 30 % für Konzeption, Recherche, Prüfung am laufenden System | +22 PT | — | — |
| *angesetzter Ist-Aufwand* | *96 PT* | — | — |
| unterer Ansatz | 96 PT | 800 € | 76.800 € |
| mittlerer Ansatz | 96 PT | 1.000 € | 96.000 € |
| oberer Ansatz | 96 PT | 1.200 € | 115.200 € |
| Sachkosten (KI-Werkzeuge, Hosting, Dienste, Marke, Vorlagen) | offen | — | **nachzutragen** |
| **Ist-Herstellungskosten** | | | **rd. 80.000 – 115.000 €** |

> **Warum das die untere Wertgrenze ist.** 96 Personentage für 138.549 Zeilen
> Code sind ein Verhältnis, das ohne KI-gestützte Entwicklung nicht erreichbar
> wäre. Der niedrige Ist-Aufwand ist Folge der Herstellungsweise, nicht des
> Umfangs — der Käufer erhält gleichwohl das volle System. Eine Bewertung, die
> allein auf den Ist-Kosten stehen bliebe, unterschätzt den Gegenwert.

### 4.2 · Wiederbeschaffungskosten

Was ein deutscher Dienstleister für einen Nachbau desselben Funktionsumfangs
berechnen würde. Mengen gemessen, Aufwandssätze branchenüblich.

| Position | Bezugsgröße | PT/Einheit | PT |
|---|---:|---:|---:|
| API-Endpunkte mit Validierung, Rechten und Test | 380 genutzte | 0,45 | 171 |
| Bildschirme | 65 erreichbare | 1,20 | 78 |
| Website-Erzeugung KAS (Editor, Sitemap, Vorlagen, Auslieferung) | Modul | — | 55 |
| Prüfstrecke (2.276 Tests, 12 E2E-Strecken) | Gesamt | — | 50 |
| Fachkonzept (Prüfkatalog, Angebotsbaukasten, Conversion-Spec, Gestaltungsrichtlinie) | Gesamt | — | 45 |
| Anbindung externer Dienste | 12 Dienste | 3,50 | 42 |
| Prüfwerk Audit (39 Kriterien, 8 Kategorien, Branchenprofile) | Modul | — | 40 |
| Dokumenterzeugung (6 PDF-Arten, Buchsatz) | Modul | — | 35 |
| Datenmodell und Migrationen | 66 Tabellen | 0,50 | 33 |
| Wiederverwendbare Bausteine | 130 Stück | 0,25 | 33 |
| KI-Sichtbarkeit und GEO (4 Anbieter, Wochenlauf) | Modul | — | 25 |
| Zeitsteuerung und Abläufe | 28 Aufträge | — | 20 |
| Betrieb (CI, zwei Umgebungen, Auslieferung, Sicherung) | Gesamt | — | 20 |
| Dokumentation | 32.226 Zeilen | — | 20 |
| *Zwischensumme* | | | *667* |
| Projektleitung und Qualitätssicherung, 15 % | | | 100 |
| **Nachbauaufwand** | | | **767 PT** |

| Tagessatz | Aufwand | Wiederbeschaffungskosten |
|---|---:|---:|
| 800 € — Freelancer-Verbund | 767 PT | 613.600 € |
| 950 € — mittelständische Agentur | 767 PT | 728.650 € |
| 1.100 € — spezialisierter Dienstleister | 767 PT | 843.700 € |
| **Ansatz für die weitere Rechnung** | 767 PT | **730.000 €** |

### 4.3 · Wertminderungen

Der Nachbauwert beschreibt ein fertiges System. Das vorliegende ist es nicht.
Drei Minderungen wirken nacheinander, nicht additiv.

| Minderung | Satz | Begründung, am Lagebild belegt |
|---|---:|---|
| funktional | −25 % | 26 nicht geschlossene Einträge der Lückenliste (20 offen, 4 teilweise, 2 terminiert); 6 von 11 Modulen grün; M8 gebaut aber inhaltsleer; M10 unfertig; Verkaufssperre auf WS-SYS-01 |
| technisch | −10 % | 72 Endpunkte ohne Aufrufer, 3.424 Frontend-Zeilen ohne Nutzerweg, 17 Dateien über der eigenen 800-Zeilen-Grenze |
| wirtschaftlich | −30 % | kein Umsatznachweis, keine belegte Nutzerbasis, Abhängigkeit von einer Person |
| **Gesamtfaktor** | **0,4725** | 730.000 € × 0,4725 = **rd. 345.000 €** |

**Kostenorientierter Zeitwert: 290.000 – 400.000 €** (Mitte rd. 345.000 €).
Das ist der Wert, den ein Käufer spart, weil er nicht selbst bauen muss — nicht
der Wert, den er damit verdienen wird.

---

## 5 · Kapitalwertorientierter Wert

Lizenzpreisanalogie: Was müsste ein Nutzer zahlen, wenn er das System
lizenzieren statt besitzen würde? Der Barwert dieser ersparten Lizenzgebühren
ist der Wert der Software.

> ⚠️ **Die Umsatzzahlen sind Annahme, nicht Ist.** Grundlage sind die Preise der
> Produktdatenblätter — Websprint Relaunch 3.500 €, Neubau 7.900 €, Check PLUS
> 249 €, Workbook 149 €, Pflege Basic 79 € / Pro 149 € monatlich, GEO-Zusatz
> 1.200 €. Das Mengengerüst ist bewusst vorsichtig gesetzt. **Liegt heute
> bereits Umsatz vor, ändert sich dieser Abschnitt erheblich.**

Lizenzsatz 10 %, Steuersatz 30 %, Kapitalisierungszins 18 %.

| Jahr | Umsatz (Annahme) | Lizenz 10 % | nach Steuern | Abzinsung | Barwert |
|---|---:|---:|---:|---:|---:|
| 1 | 87.000 € | 8.700 € | 6.090 € | 0,847 | 5.161 € |
| 2 | 150.000 € | 15.000 € | 10.500 € | 0,718 | 7.541 € |
| 3 | 220.000 € | 22.000 € | 15.400 € | 0,609 | 9.373 € |
| 4 | 280.000 € | 28.000 € | 19.600 € | 0,516 | 10.108 € |
| 5 | 320.000 € | 32.000 € | 22.400 € | 0,437 | 9.790 € |
| 6–8 (Restnutzung, konstant) | 320.000 € | 32.000 € | 22.400 € | 0,950 kum. | 21.280 € |
| **Barwert, konservativ** | | | | | **63.253 €** |

Bei doppeltem Mengengerüst — realistisch, sobald die ersten fünf Kunden
produktiv sind — rund 127.000 €.

**Kapitalwertorientierter Wert: 60.000 – 130.000 €.** Der niedrigste der drei
Werte und derjenige, der die heutige Ertragskraft am ehrlichsten abbildet.

---

## 6 · Marktvergleich (nur Plausibilität)

Es gibt keine belastbaren Vergleichstransaktionen für Branchensoftware dieses
Zuschnitts im deutschen Handwerksumfeld.

* **Umsatzmultiplikator:** Vertikale Branchensoftware mit laufenden Erlösen
  handelt beim Drei- bis Sechsfachen des Jahresumsatzes. Ohne Umsatz greift der
  Multiplikator nicht — er ergäbe null, was offensichtlich falsch ist.
* **Anteil an den Nachbaukosten:** Übernahmen vorumsatzlicher, aber lauffähiger
  Systeme liegen erfahrungsgemäß bei 10–40 % der Nachbaukosten. Auf 730.000 €
  bezogen: **73.000 – 292.000 €.**

Die zweite Größe bestätigt das Band der beiden anderen Verfahren. Als
eigenständiger Ansatz taugt sie nicht.

---

## 7 · Empfehlung nach Übertragungsfall

| Fall | Vorgang | Ansatz | Begründung |
|---|---|---:|---|
| **1** *(wahrscheinlichster)* | Einbringung in die eigene Gesellschaft (Sacheinlage, § 20 UmwStG) | **100.000 €** | Vorsicht ist Eigeninteresse: Bei Überbewertung haftet der Gesellschafter nach § 9 GmbHG in bar für die Differenz. Über dem Ertragswert, durch Ist-Kosten belegt, viel Luft nach oben. Überschuss als Kapitalrücklage oder Gesellschafterdarlehen, **nicht** als Stammkapital. |
| **2** | Verkauf an ein fremdes Unternehmen (Asset Deal) | 150.000 – 350.000 € | Einstieg mit den 730.000 € Nachbaukosten belegen, den Abstand als Nachlass verkaufen. Realistischer Abschluss 200.000 – 250.000 €. Erfolgsabhängige Nachzahlung über zwei Jahre teilt das Ertragsrisiko. |
| **3** | Übertragung zwischen verbundenen Unternehmen | rd. 110.000 € | Kostenaufschlagsmethode: Ist-Kosten + 10 % Gewinnaufschlag. Preisanpassungsklausel nach § 1a AStG beachten; eine vertragliche Anpassungsklausel nimmt dem die Schärfe. |

> **Warum nicht der höhere Wert.** Die 345.000 € aus dem Nachbau sind fachlich
> sauber hergeleitet und für die Verhandlung mit einem fremden Käufer der
> richtige Anker. Für eine Einbringung in die eigene Gesellschaft sind sie das
> falsche Werkzeug: Dort trägt der Einbringende das Risiko der Überbewertung
> allein, und der Gewinn aus einem hohen Ansatz ist ein Buchgewinn, dem kein
> Zufluss gegenübersteht.

---

## 8 · Vorbehalte und Risiken

### 🔴 Urheberrecht an maschinell erzeugtem Code

**968 von 1.857 Commits — 52 % — tragen „Claude" als Autor.** Rein maschinell
erzeugter Code erfüllt die Voraussetzung der persönlichen geistigen Schöpfung
nach § 2 Abs. 2 UrhG nicht und genießt insoweit keinen Urheberrechtsschutz.

Für den Vertrag folgt daraus: Die Übertragung darf sich **nicht allein** auf die
Einräumung ausschließlicher Nutzungsrechte stützen, weil ein Teil des
Gegenstands solche Rechte gar nicht trägt. Stattdessen zusätzlich
Besitzübergabe, Quellcode-Herausgabe, Know-how-Übertragung und Geheimhaltung
regeln — und die menschliche Auswahl-, Anordnungs- und Bearbeitungsleistung als
eigenständigen Schutzgegenstand benennen.

**Anwaltlich prüfen lassen. Das ist kein Randpunkt, sondern die tragende Frage
des Vertrags.**

### Weitere Risiken

| Punkt | Wirkung | Umgang |
|---|---|---|
| Abhängigkeit von einer Person | hoch | Ohne Übergabephase verliert der Käufer einen erheblichen Teil des Werts. Drei Monate Begleitung vertraglich vereinbaren und im Preis berücksichtigen. |
| Personenbezogene Daten | hoch | Vor der Übertragung Rechtsgrundlage klären und Betroffene informieren. Alternativ ohne Datenbestand übertragen. |
| Fremdlizenzen (GrapesJS Studio SDK, Envato) | mittel | Übertragbarkeit je Lizenz beim Anbieter klären. Der Relume-Fall vom 2026-05-06 zeigt, dass diese Prüfung im Haus schon einmal zu einer Entfernung geführt hat. |
| Marke „KOMPAGNON" | mittel | Prüfen, ob eine Eintragung beim DPMA besteht. Falls ja, gesonderte Umschreibung; falls nein, im Wert nicht angesetzt. |
| Buchmanuskript | mittel | Eigenständiges Werk mit eigener Verwertung. Gesondert bewerten und übertragen oder ausdrücklich ausnehmen — nicht stillschweigend mitlaufen lassen. |
| 12 Anbieterkonten, 68 Umgebungsvariablen | mittel | Übergabeplan je Dienst. Ohne ihn steht das System nach der Übertragung still, obwohl der Code vollständig ist. |
| 26 nicht geschlossene Arbeitspunkte, kein offener P0 | eingepreist | Als funktionale Wertminderung von 25 % berücksichtigt, nicht behoben. Der Käufer erwirbt sie mit. |

### Diese Ausarbeitung ist kein Wirtschaftsprüfer-Gutachten

Sie folgt der Systematik von IDW S5 und ist in jeder Mengenangabe am Quellstand
nachprüfbar. Für Handelsregister, Notar oder Finanzamt kann eine Bestätigung
durch einen Steuerberater oder Wirtschaftsprüfer erforderlich sein. Diese
Ausarbeitung ist dafür die Vorlage — sie ersetzt sie nicht.

---

## 9 · Offene Eingaben

Fünf Angaben machen aus dieser Ausarbeitung eine prüffeste Unterlage. Jede
einzelne verschiebt eine Zahl.

| # | Was fehlt | Wirkung |
|---|---|---|
| 1 | Sachkosten 03–09/2026 (KI-Werkzeuge, Hosting, Fremddienste, Marke, gekaufte Vorlagen) | fließt in die Ist-Herstellungskosten, hebt die untere Wertgrenze |
| 2 | Bisheriger Umsatz und Kundenzahl | macht aus Abschnitt 5 eine Rechnung statt eines Annahmemodells; hebt den Ertragswert deutlich |
| 3 | Welcher der drei Übertragungsfälle vorliegt | bestimmt, welche der drei Zahlen maßgeblich ist |
| 4 | Ist die Marke beim DPMA eingetragen? | eine eingetragene Marke ist ein eigener, hier nicht angesetzter Vermögenswert |
| 5 | Geht das Buch mit? | Manuskript und Satzsystem sind in den 100.000 € **nicht** enthalten |

---

## Reproduzierbarkeit

Alle Mengenangaben lassen sich am Quellstand nachzählen:

```bash
# Zeilen reiner Code je Bereich (ohne Leer- und Kommentarzeilen)
#   siehe Messskript im Tagesbericht docs/stand-2026-09-02.md

# API-Endpunkte
git ls-files '*.py' | xargs grep -hE '^\s*@(router|app)\.(get|post|put|patch|delete)' | wc -l

# Datenbanktabellen
git ls-files '*.py' | xargs grep -hE '__tablename__' | sort -u | wc -l

# Testfunktionen
git ls-files 'kompagnon/backend/tests/*' | xargs grep -hE '^\s*(async )?def test_' | wc -l

# Arbeitstage und Autorenverteilung
git log --format=%ad --date=short | sort -u | wc -l
git shortlog -sn --all
```
