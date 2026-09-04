# Leistungsverzeichnis — Nachbildung einer Vertriebs- und Projektplattform

**Ausschreibungsunterlage zur Angebotserstellung**

| | |
|---|---|
| Gegenstand | Vollständige Neuerstellung einer webbasierten Branchenplattform mit dem nachstehend beschriebenen Funktionsumfang |
| Zweck der Anfrage | Ermittlung der **Wiederbeschaffungskosten** (Nachbaukosten) für eine Unternehmensbewertung |
| Erwartete Rückmeldung | Aufwandsangebot je Leistungsposition in Personentagen und Euro |
| Bezugsstand des Mengengerüsts | Messung am vorhandenen Quellcode, Stichtag siehe Anlage A |
| Vertraulichkeit | Diese Unterlage ist vertraulich. Auftraggeber, Marke und Betriebsdaten sind bewusst nicht genannt. |

> **Hinweis zur Lesart.** Beschrieben wird nicht ein Wunschsystem, sondern der
> Funktionsumfang eines **bestehenden, produktiv betriebenen Systems**. Alle
> Mengenangaben sind am Quellcode gemessen und in Anlage A reproduzierbar
> hinterlegt. Gefragt ist, was die Neuerstellung eines funktionsgleichen
> Systems durch einen Dienstleister kosten würde — nicht, was sie gekostet hat.

---

## 1 · Ausgangslage und Zielbild

Der Auftraggeber betreibt eine integrierte Software für Akquise, Bewertung,
Verkauf, Herstellung und Betreuung von Internetauftritten für Betriebe des
Bauhandwerks (Schwerpunkt Heizung/Sanitär/Elektro). Die Plattform bildet die
gesamte Wertschöpfungskette in einem System ab:

```
Betrieb finden  →  Website prüfen und bewerten  →  Angebot und Zahlung
      →  Projekt abwickeln  →  neue Website erzeugen und ausliefern
      →  Kundenportal  →  laufende Betreuung
```

Besonderheit gegenüber einer klassischen CRM- oder Agentursoftware: Das System
**erzeugt das verkaufte Erzeugnis selbst** (Position LV 700) und **prüft es
maschinell** (Position LV 300). Beide Teile sind Fachanwendungen mit eigenem
Regelwerk, keine Verwaltungsmasken.

Das System ist **einsprachig deutsch**, **einmandantig** (ein Betreiber, viele
Endkunden) und rollenbasiert.

---

## 2 · Technischer Rahmen

Die nachstehende Zusammensetzung beschreibt das bestehende System. Ein Angebot
darf eine **gleichwertige** Zusammensetzung vorschlagen; in diesem Fall bitte in
Abschnitt „Annahmen" begründen.

| Ebene | Bestehende Umsetzung |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, asynchron |
| Datenhaltung | PostgreSQL |
| Frontend | React, Single-Page-Anwendung, eigenes Gestaltungssystem auf CSS-Variablen |
| Dokumente | serverseitige PDF-Erzeugung mit eigenem Satz- und Diagrammwerk |
| Zeitsteuerung | Auftragsplaner im Anwendungsprozess |
| Betrieb | zwei getrennte Umgebungen (Test und Produktiv), containerlose Auslieferung über einen PaaS-Anbieter, persistente Dateiablage |
| Prüfstrecke | Unit- und Integrationstests im Backend, Browsertests über die Oberfläche, Prüfjobs in der CI |
| KI-Anbindung | drei Sprachmodellanbieter für Textbewertung, Texterzeugung und Sichtbarkeitsmessung |

---

## 3 · Mengengerüst

Grundlage der Kalkulation. Alle Werte sind gezählt, nicht geschätzt; die
Zählregeln stehen in Anlage A.

| Größe | Menge |
|---|---:|
| Fachmodule | 11 |
| API-Endpunkte gesamt | 452 |
| davon mit Anbindung an die Oberfläche | rd. 380 |
| Routerdateien / Fachdienste im Backend | 92 / 124 |
| Datenbanktabellen | 71 |
| Bildschirme (Seitenkomponenten) | 77 |
| davon über die Navigation erreichbar | 65 |
| Wiederverwendbare Oberflächenbausteine | 142 |
| Frontend-Routen / Menüpunkte | 94 / 36 |
| Rollen im Rechtewerk | 4 |
| Prüfkriterien im Bewertungswerk | 39 bewertet, 8 Kategorien, 4 Infrastrukturangaben |
| Projektphasen im Ablaufmodell | 7 |
| PDF-Dokumentarten | 6 |
| Zeitgesteuerte Aufträge | 27 |
| Angebundene Fremddienste | 12 |
| Konfigurationswerte (Umgebungsvariablen) | über 50 |
| Automatisierte Tests (Backend) | 2.276 |
| End-to-End-Strecken über den Browser | 12 |

**Codeumfang zur Größeneinordnung** — ohne Leer- und Kommentarzeilen:

| Bereich | reiner Code |
|---|---:|
| Backend-Anwendung | 39.941 |
| Frontend | 63.403 |
| Backend-Tests | 22.882 |
| Bausteinbibliothek (HTML) | 6.881 |
| Werkzeuge und Skripte | 3.054 |
| Gestaltung (CSS) | 1.170 |
| E2E-Strecken | 446 |
| **Summe** | **137.777** |

> Der Codeumfang ist als **Plausibilitätsgröße** angegeben, nicht als
> Kalkulationsbasis. Maßgeblich für das Angebot ist der beschriebene
> Funktionsumfang.

---

## 4 · Leistungspositionen — Fachmodule

Bitte je Position Aufwand in Personentagen und Preis eintragen. Die Spalte
„Kennzahl" nennt die gemessene Größe der bestehenden Umsetzung.

---

### LV 100 · Fundament, Anmeldung, Rechtewerk

**Kennzahl:** 60 Endpunkte · 6 Bildschirme · 6 Kerntabellen

Nicht abschaltbarer Unterbau, auf dem alle übrigen Positionen aufsetzen.

* Anmeldung, Sitzungsverwaltung mit serverseitigem Sitzungsbestand, Abmeldung aller Geräte
* Benutzerverwaltung: Anlage, Sperrung, Kennwortwechsel, Zwei-Faktor-Vorbereitung
* **Rollen- und Rechtewerk mit 4 Rollen und einer Rechtematrix.** Die Rechteprüfung liest die Matrix, statt Rollennamen aufzuzählen; Rollennamen stehen an einer einzigen Stelle im Code
* Systemeinstellungen als Schlüssel-Wert-Bestand mit Oberfläche, u. a. Betriebsschalter je Fachmodul auf drei Ebenen (Menü, Router, Zeitsteuerung)
* Zentrales Fehlerprotokoll mit Oberfläche, Filterung und Auswertung
* Dateiablage mit Zugriffsschutz, Typ- und Größenprüfung, persistentem Datenträger
* Mailversand mit **Versandsperre**: ein Schalter hält jeden automatischen Versand an; sichere Vorgabe ist „aus"
* Diagnoseendpunkte für Betriebsprüfung ohne Preisgabe von Konfigurationswerten

**Abnahme:** Ein Konto je Rolle kommt genau an die vorgesehenen Bildschirme und
an keinen weiteren; ein gesperrter Endpunkt antwortet mit 404, nicht 403.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 200 · Akquise und Leadgewinnung

**Kennzahl:** 56 Endpunkte · 5 Bildschirme · 4 Tabellen · 3 Zeitaufträge

* **Registerrecherche:** automatisierte Erfassung von Betrieben aus öffentlichen Verzeichnissen, mit Entdopplung, Wochenlauf und eigenem Betriebsschalter
* **Domain-Import:** Massenimport von Adresslisten, Erreichbarkeitsprüfung, Anreicherung aus einem Wirtschaftsdatendienst
* **Einbettbares Analyse-Widget** für fremde Websites: eigenständig gebautes JavaScript-Bündel, automatische Höhenanpassung im iframe, Einwilligungsabfrage, Double-Opt-in vor Ausgabe des Ergebnisses, getrennte Auslieferung vom Hauptfrontend
* **11 Webhook-Eingänge** für externe Quellen mit Signaturprüfung je Quelle
* Kampagnenzuordnung und Herkunftsverfolgung je Interessent
* Tages- und Sechsstundenläufe zur Anreicherung und Domainprüfung

**Abnahme:** Ein auf einer fremden Domain eingebettetes Widget liefert ein
Ergebnis, das erst nach bestätigter Einwilligung zugestellt wird.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 300 · Prüf- und Bewertungswerk (Website-Audit)

**Kennzahl:** 26 Endpunkte · 39 bewertete Kriterien in 8 Kategorien · 2 Tabellen

Fachanwendung mit eigenem Regelwerk. Der Kriterienkatalog ist die einzige
Wahrheitsquelle; Punktabstufungen liegen als Daten am Kriterium, nicht im Code.

* **Erhebung** je geprüfter Website: Seitenabruf und Auswertung des Auslieferungsstands, Zertifikatsprüfung, Ladezeitmessung über einen Geschwindigkeitsdienst, Erkennung fremder Dienste und Einwilligungswerkzeuge, Pflichtangaben (Anbieterkennzeichnung, Datenschutzerklärung), strukturierte Daten, Barrierefreiheitsmerkmale, Bild- und Textprüfung
* **KI-gestützte Bewertung** der inhaltlichen Kriterien über einen Sprachmodellanbieter, mit festgelegtem Ausgabeschema und Kennzeichnung der Erhebungsart je Kriterium
* **Punktmodell** mit Kategoriegewichtung, Klassenzuordnung (Auszeichnungsstufen) und Deckelregeln bei rechtlichen Verstößen
* **Branchenprofile:** je Gewerk abweichende Gewichtung und Schwellen
* **Sichtbarkeitsmessung in KI-Antwortsystemen** gegen vier Anbieter mit Monatslauf, Auswertung und Verlaufsdarstellung
* **PDF-Bericht** mit Diagrammen, Kriterienerläuterung und Handlungsempfehlungen
* **Eingefrorene Referenz-Website** als Regressionsanker: jede Verschiebung im Punktmodell wird von der Prüfstrecke gefangen

**Abnahme:** Ein Lauf gegen die Referenzseite liefert reproduzierbar dieselbe
Punktzahl; jede Kriterienbeschreibung deckt sich mit dem, was gemessen wird.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 400 · Vertrieb und Betriebsbestand

**Kennzahl:** 51 Endpunkte · 4 Bildschirme · 5 Tabellen · Stammsatz mit 101 Feldern

* Betriebsstamm mit Suche, Filterung, Mehrfachauswahl und Massenaktionen
* Betriebsblatt als Einzelansicht mit Verlauf, Dokumenten und Kommunikationshistorie
* Verkaufsvorgänge mit Positionen, Stufen und Wahrscheinlichkeiten
* Lebenszyklus vom Interessenten zum Kunden mit Übergabe der Stammdaten
* Kundenkartei getrennt vom Interessentenbestand
* Export in Tabellenformate mit Feldauswahl
* Umgang mit unbekannten Werten: nie roh, nie getarnt — auch nicht im Filter

**Abnahme:** Ein Betrieb durchläuft alle Stufen bis zum Kunden, ohne dass Daten
doppelt erfasst werden müssen.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 500 · Angebot, Kasse, Rechnungsstellung

**Kennzahl:** 34 Endpunkte · 2 Bildschirme · 5 Tabellen · 3 getrennte Webhook-Strecken

* **Produktkatalog** als Datenbestand mit Status (Entwurf, live, stillgelegt), Netto- und Bruttopreis, Steuersatz, Leistungsverzeichnis je Paket. Stillgelegte Produkte bleiben lesbar, damit Altvorgänge ihre Preise behalten
* **Öffentliche Verkaufsseiten** mit Preisen aus der Datenbank, ohne Anmeldung erreichbar
* **Kassenstrecke** mit Zahlungsanbieter: Sitzungserzeugung, vorgewähltes Paket, Rücksprung mit serverseitig bestätigtem Ergebnis
* **Drei getrennte Webhook-Strecken** mit je eigenem Signaturgeheimnis für unterschiedliche Erzeugnisarten
* **Rechnung und Auftragsbestätigung** als PDF mit Nummernkreis und Archivierung
* **Partnervergütung:** Erfassung vermittelter Abschlüsse über einen Fremddienst
* Preisdarstellung durchgängig als Endpreis, ein einziges Verständnis von brutto und netto im ganzen System

**Abnahme:** Ein Kauf läuft im Browser von der Verkaufsseite bis zur
Auftragsbestätigung durch, ohne Anmeldung, mit korrektem Betrag beim
Zahlungsanbieter.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 600 · Projektabwicklung

**Kennzahl:** 71 Endpunkte · 6 Tabellen · 7 Phasen · 5 Tagesläufe

* **Projektakte** mit 7 Phasen, Fristen, Zuständigkeiten und automatischem Phasenübergang nach Inbetriebnahme
* **Checklisten** je Phase, aus Vorlagen erzeugt, mit Fortschrittsanzeige
* **Kundenbriefing:** strukturierte Erhebung über einen Fragebogen, Erinnerungsläufe bei ausbleibender Rückmeldung, Prüfung auf fehlende Materialien, PDF-Ausgabe
* **Zeiterfassung** je Projekt und Mitarbeiter
* **Margenrechnung** mit Tageslauf: geleistete Zeit gegen vereinnahmten Betrag
* **Dateiablage und Zugangsdatenverwaltung** je Projekt, Zugangsdaten verschlüsselt gespeichert
* **Projekt-Assistent:** KI-gestützte Unterstützung auf dem Projektbestand
* Inhaltsübernahme von der Altwebsite des Kunden als Ausgangsmaterial

**Abnahme:** Ein Projekt durchläuft alle Phasen; überfällige Phasen und fehlende
Kundenmaterialien werden ohne manuelles Zutun gemeldet.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 700 · Website-Erzeugung und Auslieferung

**Kennzahl:** 69 Endpunkte · 9 Tabellen · 142 Bausteine · 2 Überwachungsläufe

Kernstück und aufwendigste Position. Aus dem Briefing entsteht eine
auslieferungsfertige Website.

* **Seitenplanung:** Sitemap je Kunde mit Seitentypen, Zielen und Gliederung
* **Wireframe-Stufe:** Grobstruktur je Seite vor der Gestaltung
* **Gestaltungsrichtlinie je Kunde:** Farbwelt, Schriften, Abstände aus dem Briefing abgeleitet, als Variablensatz gespeichert
* **Visueller Editor** mit Arbeitsfläche und mehreren Zeichenflächen nebeneinander (je Kundenseite eine), Auswahl einzelner Elemente, Eigenschaftsbereich, Textbearbeitung an Ort und Stelle, Rückgängig/Wiederherstellen, **Versionierung jedes Standes**
* **Bausteinbibliothek** mit 142 wiederverwendbaren Abschnitten (Kopfbereiche, Leistungsraster, Referenzen, Formulare, Fußbereiche), lizenzrechtlich geprüfte Quellen, Aufräumroutine für entfernte Bestände
* **Vorlagen je Gewerk** mit branchenspezifischer Ansprache
* **Inhaltserzeugung:** KI-gestützte Texte nach einer verbindlichen Angebots- und Conversion-Spezifikation, je Abschnitt gesondert, mit Medienverwaltung und Bildzuordnung
* **Auslieferung** an einen statischen Hosting-Anbieter über dessen Schnittstelle, mit Domainanbindung, Überwachung der Namensauflösung (Viertelstundenlauf) und der Zertifikatsausstellung
* **Qualitätsschleife:** das erzeugte Erzeugnis wird durch das Bewertungswerk aus LV 300 geprüft, bevor es freigegeben wird

**Abnahme:** Aus einem ausgefüllten Briefing entsteht ohne Handarbeit eine
ausgelieferte, erreichbare Website, die die Qualitätsschleife besteht.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 800 · Kundenportal

**Kennzahl:** 13 Endpunkte · 4 Bildschirme · 4 Tabellen

* Eigener Zugang für Endkunden, getrennt vom Innendienst
* Dokumentenablage mit Freigabeverfahren (Kunde bestätigt Entwürfe)
* Nachrichtenkanal zwischen Kunde und Innendienst, mit Mailbenachrichtigung
* Rechnungsübersicht mit Download
* Support-Anfragen mit Statusverfolgung
* Anbindung an das Redaktionssystem der ausgelieferten Website

**Abnahme:** Ein Kunde meldet sich an, gibt einen Entwurf frei und stellt eine
Anfrage, ohne Zugriff auf Innendienstdaten zu erhalten.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 900 · Schulungsbereich

**Kennzahl:** 34 Endpunkte · 8 Tabellen

* Kurse, Module und Lektionen als dreistufige Struktur
* Zugriffssteuerung je Modul und Kunde (freigeschaltet oder gesperrt)
* Fortschrittsverfolgung, Abschlussprüfung, Zertifikatserzeugung als PDF
* Medieneinbindung (Video, Dokument) mit Zugriffsschutz

**Abnahme:** Ein freigeschaltetes Modul ist für den zugewiesenen Kunden
sichtbar und für alle anderen nicht.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 1000 · Betreuung nach Inbetriebnahme

**Kennzahl:** 12 Endpunkte · 2 Tabellen · 1 Monatslauf

* Ticketsystem mit Prioritäten, Zuständigkeit und Reaktionsfristen
* Wartungsverträge mit Leistungsumfang und Abrechnungsintervall
* Monatlicher Leistungsbericht je Kunde, automatisch erzeugt und versendet

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 1100 · Aussendungen und Kampagnen

**Kennzahl:** 18 Endpunkte · 6 Tabellen · 1 Sequenzlauf

* Newsletterverwaltung mit Listen, Kontakten und Abmeldeverfahren
* Kampagnen mit Vorlagen und Zeitplanung
* Mehrstufige Mailsequenzen mit Auslösern
* Auswertung der Zustellereignisse (zugestellt, geöffnet, angeklickt, abgewiesen) über die Rückmeldungen des Versanddienstes
* Vollständiges Versandprotokoll als Nachweis

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 1200 · Publikations- und Satzstrecke *(Bedarfsposition)*

**Kennzahl:** 7 Endpunkte · 772 Zeilen Satzcode

Eigenständiges Teilsystem, gesondert anzubieten und gesondert abwählbar.

* Satzsystem zur Erzeugung eines druckfähigen Fachbuchs aus Quelldateien
* Export des Prüfkatalogs aus LV 300 in die Buchfassung, damit gedruckte
  Angaben und Software nicht auseinanderlaufen
* Abgleichwächter über mehrere Ebenen zwischen Katalog und Manuskript
* Bestell- und Versandabwicklung für das gedruckte Werk

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

## 5 · Leistungspositionen — Querschnitt

---

### LV 2000 · Sicherheit

* Sitzungsverwaltung mit serverseitiger Ungültigkeitserklärung
* Verschlüsselte Ablage von Kundenzugangsdaten und Redaktionssystem-Zugängen
* Signaturprüfung aller eingehenden Webhooks
* Ratenbegrenzung auf öffentlichen Endpunkten
* Keine Existenzbestätigung bei fehlender Berechtigung (404 statt 403)
* Kein Konfigurationswert in einer Antwort, keine Zugangsdaten im Quellcode
* Automatische Geheimnissuche als Prüfjob in der CI
* Zugriffsschutz auf allen Datenendpunkten — ausdrücklich einschließlich der
  öffentlich erreichbaren Teilstrecken

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 2100 · Datenschutz und Nachweispflichten

* Double-Opt-in vor jeder Zustellung an nicht bestätigte Adressen
* Löschfunktion für personenbezogene Bestände, mit Protokoll
* Auskunftsfunktion (Datenexport je betroffener Person)
* Rechtsgrundlage je Datenquelle dokumentiert und im System hinterlegt
* Verarbeitungsnachweise, Aufbewahrungsfristen, Einwilligungsverwaltung
* Anbieterkennzeichnung und Datenschutzerklärung für alle öffentlichen Teile,
  einschließlich des eingebetteten Widgets aus LV 200

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 2200 · Dokumenterzeugung

**Kennzahl:** 6 Dokumentarten mit gemeinsamem Satzwerk

Prüfbericht · Angebot · Auftragsbestätigung · Rechnung · Briefing · Zertifikat.
Gemeinsame Grundlage: eigenes Satzwerk mit Bausteinen, Diagrammerzeugung,
Farb- und Typografievorgabe, Kopf- und Fußzeilen, Seitenzählung.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 2300 · Zeitsteuerung und Abläufe

**Kennzahl:** 27 zeitgesteuerte Aufträge

Wochen-, Tages-, Stunden- und Viertelstundenläufe. Gefordert:

* zentraler Auftragsplaner mit Zeitzonenbehandlung
* Protokollierung jedes Laufs mit Ergebnis und Dauer
* **Sperrschalter je Modul, der auch die Läufe anhält** — ein abgeschaltetes
  Modul, dessen Nachtlauf weiter Mails verschickt, gilt als nicht abgeschaltet
* Wiederanlauf ohne Doppelversand nach einem Neustart

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 2400 · Anbindung von Fremddiensten

**Kennzahl:** 12 Dienste

| Art des Dienstes | Anzahl | Anforderung |
|---|---:|---|
| Sprachmodellanbieter | 3 | Textbewertung, Texterzeugung, Sichtbarkeitsmessung |
| Zahlungsanbieter | 1 | Kasse, 3 getrennte Webhook-Strecken, Rückerstattung |
| Mailversanddienst | 1 | Versand, Ereignisrückmeldung, Listenpflege |
| Statisches Hosting | 1 | Auslieferung, Domain, Zertifikat, Überwachung |
| Geschwindigkeits- und Ortsdienste | 2 | Ladezeitmessung, Betriebsdaten |
| Wirtschaftsdatendienst | 1 | Anreicherung von Betriebsdaten |
| Partnerprogramm | 1 | Vermittlungsnachweis |
| Plattformbetrieb und Datenbank | 2 | Betrieb beider Umgebungen |

**Für jede Anbindung gefordert:** Fehlerbehandlung ohne stillen Abbruch,
Wiederholung mit Wartezeit, Zeitüberschreitung, **kein blockierender Aufruf im
asynchronen Anwendungsprozess**, Attrappenbetrieb für die Prüfstrecke.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 2500 · Prüfstrecke

**Kennzahl:** 2.276 Backend-Tests · 12 E2E-Strecken

* Unit- und Integrationstests gegen eine echte Datenbank, nicht gegen Attrappen
* Testdatenbank mit **demselben** Migrationsweg wie die Produktivdatenbank
* Browsertests über die Oberfläche für jeden Hauptweg
* **Wächtertests** gegen wiederkehrende Fehlerklassen, u. a.:
  – jeder Frontend-Aufruf wird gegen die tatsächlich geladenen Routen geprüft
  – kein synchroner Fremdaufruf in einer asynchronen Funktion
  – der Prüfkatalog wird gegen eine eingefrorene Referenzseite gerechnet
* Mindestabdeckung 80 %, in der CI durchgesetzt
* Ein Test, der nur die Abwesenheit von etwas zusichert, gilt nicht als Nachweis

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 2600 · Betrieb, Auslieferung, Datensicherung

* **Zwei vollständig getrennte Umgebungen** (Test und Produktiv) mit eigener Datenbank, eigenen Zugangsdaten und eigener Konfiguration
* Infrastruktur als Datei beschrieben (Blueprint je Umgebung)
* **CI mit mindestens vier Prüfjobs:** Stilprüfung, Startprüfung, Frontend-Bau, Geheimnissuche; Auslieferung erst nach grüner Prüfung
* Automatische Auslieferung bei Änderung des jeweiligen Zweigs
* **Migrationen laufen beim Start**, ein einziger Weg, nachrüstbar für bestehende Spalten
* Datensicherung **mit geprobter Wiederherstellung** — eine Sicherung, die nie zurückgespielt wurde, gilt als nicht vorhanden
* Persistente Dateiablage für Uploads und erzeugte Dokumente

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 2700 · Dokumentation und Übergabe

* Technische Dokumentation: Architektur, Datenmodell, Schnittstellenverzeichnis
* Betriebshandbuch: Einrichtung, Konfigurationswerte, Sicherung, Störungsfälle
* Fachdokumentation: Kriterienkatalog, Angebotsbaukasten, Gestaltungsrichtlinie
* Einweisung der Anwender

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

### LV 2800 · Projektleitung und Qualitätssicherung

Anforderungsaufnahme, Feinkonzept, Abstimmung, Abnahmebegleitung,
Änderungsverwaltung. Bitte als Prozentsatz auf die Summe der Fachpositionen
oder als eigener Aufwand ausweisen.

| Aufwand (PT) | Preis (€) |
|---|---|
| | |

---

## 6 · Nichtfunktionale Anforderungen

| Nr. | Anforderung |
|---|---|
| NF-1 | Oberfläche vollständig deutsch, Fachbegriffe einheitlich über alle Bildschirme |
| NF-2 | Bedienbar auf Bildschirm und Tablet; öffentliche Teile und Kundenportal zusätzlich auf dem Telefon |
| NF-3 | Barrierefreiheit: Tastaturbedienbarkeit durchgängig, sichtbarer Fokus, Kontrastverhältnis mindestens 4,5:1, Dialoge über Escape verlassbar, Mindestschriftgröße eingehalten |
| NF-4 | Antwortzeit der Fachendpunkte unter 500 ms im Regelfall; kein Fremdaufruf blockiert den Anwendungsprozess |
| NF-5 | Fehler werden nie stillschweigend verschluckt; jede Fehlermeldung ist für den Anwender verständlich und serverseitig mit Kontext protokolliert |
| NF-6 | Eingaben werden an jeder Systemgrenze schemagestützt geprüft |
| NF-7 | Unbekannte Werte werden als unbekannt dargestellt — weder als Null noch als Leerstring getarnt |
| NF-8 | Quelltextorganisation: Dateien unter 800 Zeilen, Funktionen unter 50 Zeilen, keine Verschachtelung über vier Ebenen |
| NF-9 | Öffentliche Teile ohne Anmeldung erreichbar, interne Bestände ohne Anmeldung **nicht** erreichbar — auch nicht über direkte Adresseingabe |
| NF-10 | Jedes Fachmodul einzeln abschaltbar, ohne Datenverlust |

---

## 7 · Abgrenzung — nicht Bestandteil dieser Ausschreibung

| Position | Anmerkung |
|---|---|
| Inhalte | Kurstexte, Buchmanuskript, Marketingtexte — nur die Technik ist Gegenstand |
| Marke und Gestaltungsvorgaben | werden gestellt |
| Fremdlizenzen | Editor-Baukasten und gekaufte Vorlagen werden gestellt oder gesondert beschafft |
| Datenübernahme aus dem Altsystem | gesondert anzubieten, falls gewünscht |
| Laufende Betriebs- und Nutzungsentgelte | Hosting, Sprachmodelle, Versanddienst — trägt der Auftraggeber |
| Domains und Anbieterkonten | werden vom Auftraggeber gestellt |
| Rechtsberatung | Datenschutzdokumente werden anwaltlich geprüft, nicht vom Anbieter erstellt |

---

## 8 · Anforderungen an das Angebot

1. **Aufwand je Leistungsposition** in Personentagen, in der Gliederung dieses
   Verzeichnisses. Eine Gesamtsumme ohne Aufteilung ist nicht verwertbar.
2. **Tagessatz und Rollenmix** (Projektleitung, Architektur, Backend, Frontend,
   Test, Betrieb) getrennt ausweisen.
3. **Zwei Varianten** bitte getrennt kalkulieren:
   * **Variante A — Vollumfang:** LV 100 bis LV 2800 einschließlich der
     Bedarfsposition LV 1200.
   * **Variante B — Kernkette:** nur LV 100, 200, 300, 400, 500, 600, 700, 800
     sowie der vollständige Querschnitt LV 2000–2800.
4. **Annahmen und Ausschlüsse** ausdrücklich benennen — insbesondere dort, wo
   eine Position aus Ihrer Sicht unterbestimmt ist.
5. **Abweichende technische Zusammensetzung** ist zulässig, aber zu begründen.
6. **Termine:** Gesamtlaufzeit, Meilensteine, Teamgröße.
7. **Gewährleistung und Zahlungsplan.**
8. **Rückfragen** sind erwünscht und werden gesammelt beantwortet; bitte
   innerhalb einer Woche nach Erhalt stellen.

> **Was ausdrücklich nicht gefragt ist:** ein Angebot über ein „vergleichbares"
> oder vereinfachtes System. Gefragt ist die Nachbildung **dieses**
> Funktionsumfangs. Wo eine Position aufwendiger ist, als sie klingt, sagen Sie
> es bitte, statt sie kleinzurechnen.

---

## Anlage A · Zählweise des Mengengerüsts

Damit jede Zahl in Abschnitt 3 nachprüfbar bleibt, hier die Zählregel. Die
Messung erfolgte auf dem Quellstand des Auftraggebers; die Befehle sind auf
jedem Stand wiederholbar.

| Größe | Zählregel |
|---|---|
| API-Endpunkte | Anzahl der Routendekoratoren (`get`, `post`, `put`, `patch`, `delete`) in allen Python-Dateien |
| Datenbanktabellen | Vereinigungsmenge aus ORM-Tabellennamen und `CREATE TABLE`-Anweisungen der Migrationen, entdoppelt |
| Bildschirme | Seitenkomponenten im Verzeichnis `pages`; „erreichbar" = mit Eintrag im Routenwerk |
| Oberflächenbausteine | Komponentendateien im Verzeichnis `components` |
| Tests | Anzahl der Testfunktionen im Backend-Testverzeichnis |
| Zeitaufträge | Anzahl der Registrierungen beim Auftragsplaner |
| Codezeilen | Gesamtzeilen abzüglich Leer- und Kommentarzeilen, je Bereich getrennt |

**Abweichungen sind möglich und beabsichtigt offengelegt:** Je nach Zählregel
schwanken einzelne Größen um wenige Prozent (etwa Tabellen, wenn man
Migrationsartefakte mitzählt). Für die Kalkulation ist der beschriebene
Funktionsumfang maßgeblich, nicht die letzte Stelle einer Zahl.

---

*Ende des Leistungsverzeichnisses.*
