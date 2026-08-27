# Auftrag: „Der Homepage Standard" fertigstellen

**Diese Datei ist die Übergabe an eine neue Sitzung.** Sie setzt nichts voraus
und ist am 25.08.2026 gegen den laufenden Stand geprüft — jede Zahl darin ist
gemessen, nicht geschätzt. Wo eine Zahl steht, steht daneben, womit man sie
nachrechnet.

---

## 0. Pflicht-Check, bevor irgendetwas angefasst wird

```bash
git remote -v            # muss nachhaltika-arch/Claude-Code sein
git branch --show-current # muss staging sein
```

Stimmt eines nicht: **stoppen und melden.** Nicht auf `main` arbeiten, keine
zusätzlichen Branches anlegen. Nach jedem Commit `git push origin staging`.
**Ein Pull Request nach `main` wird nur freitags geöffnet** und von David
gemerged, nie von Claude.

---

## 1. Was das Buch ist

Ein Fachbuch für Betriebsinhaber: „Der Homepage Standard — 39 Kriterien,
8 Kategorien, 103 Punkte". Es druckt den Prüfkatalog, den die Software
anwendet, und führt den Leser durch einen Selbsttest desselben Maßstabs.

**Die Katalogsumme ist 103 und bleibt es.** Kein `max_points` wird angefasst.
Was den Maßstab verändert, gehört nach
`docs/Audit/fassung-2027-1-offene-massstabsfragen.md` — nicht in die laufende
Arbeit. Diese Regel ist am 24.08. entschieden worden und trägt alles Weitere.

---

## 2. Wo alles liegt

| | Pfad |
|---|---|
| **Manuskript** (einzige Fassung) | `docs/Buch/Buch - Kompagnon - Homepage Standard v2/Vollständige dokumentation Buch V2/` |
| Baustrecke | `buch/` |
| Prüfkatalog (Quelle aller Zahlen) | `kompagnon/backend/services/audit_criteria.py` |
| Bewertung | `kompagnon/backend/services/audit_scoring.py` |
| Offene Punkte Buch | `OFFENE-PUNKTE-BUCH.md` |
| Offene Punkte Software | `OFFENE-PUNKTE-SOFTWARE.md` |
| Maßstabsfragen | `docs/Audit/fassung-2027-1-offene-massstabsfragen.md` |

> **Das Manuskript lag bis zum 25.08.2026 zweimal im Repo** — einmal im Ordner
> oben und einmal eine Ebene darüber. Die Fassungen waren auseinandergelaufen,
> und das Exportskript schrieb in die falsche. Die obere ist gelöscht.
> **Keine zweite Kopie anlegen**, auch nicht „nur zum Bauen".

---

## 3. Wie man das Buch baut und prüft

```bash
# einmalig
python3 -m venv buch/venv && buch/venv/bin/pip install -r buch/requirements-build.txt

# bauen — `--entwurf` ist Pflicht, solange die Kapitel `status: entwurf` tragen
buch/venv/bin/python buch/bauen.py --ziel beide --entwurf
buch/venv/bin/python buch/druckpruefung.py buch/build/homepage-standard-druck.pdf

# erzeugte Tabellen nachziehen, nachdem sich der Katalog geändert hat
python3 scripts/standard-export.py     # Anhang B und die Spezifikationsblöcke
python3 scripts/buch-bloecke.py        # Kriterientabellen in den Kapiteln

# Tests (2.259 Stück, laufen in ~37 s)
cd kompagnon/backend && venv/bin/python -m pytest tests/ -q
```

---

## 4. Der Stand in Zahlen — gemessen am 25.08.2026

| | Wert | Womit gemessen |
|---|---|---|
| Bestandteile | 22 (Titelei, 17 Kapitel, 4 Anhänge) | `buch/bauen.py` |
| Wörter | 55.565 (ohne redaktionelle Anmerkungen) | `buch/manuskript.py` |
| **Umfang gedruckt** | **281 Seiten**, 170 × 240 mm | `buch/bauen.py --ziel druck` |
| Umfang Bildschirm | 192 Seiten A4 | dito |
| Zielumfang laut Vorspann | 250 Seiten | Summe der `zielumfang`-Felder |
| Abbildungen | 14 gebrieft, keine gezeichnet | `buch/bauen.py` |
| Marginalien | 107 | dito |
| Kapitel mit `status: entwurf` | **21 von 21** | dito |
| Druckvorstufe | 3 von 4 Prüfungen grün | `buch/druckpruefung.py` |

**Der Umfang ist der wichtigste Wert dieser Tabelle.** Die Entscheidung B1.1
(„260 statt 208 Seiten") war auf eine Zahl gesperrt, die niemand gemessen
hatte. Sie liegt jetzt vor: **281 gegen 250 geplante Seiten.**

---

## 5. Was fertig ist — bitte nicht noch einmal machen

| Bereich | Stand |
|---|---|
| **Prüfkatalog** | 31 von 35 Softwarepunkten zu. Kriterienhinweise gekürzt, Erhebungsarten richtiggestellt, Punktabstufungen sind Daten (BUCH-F1), Anhang B wird erzeugt |
| **Anhang B** | erzeugt aus dem Katalog, **einschließlich der Punktabstufungen**. Nicht von Hand ändern |
| **Kriterientabellen der Kapitel** | erzeugt (`scripts/buch-bloecke.py`). Wer sie von Hand ändert, verliert es beim nächsten Lauf |
| **Baustrecke** | steht (BUCH-03). Zwei PDFs, Druckvorstufenprüfung, Test dagegen |
| **Bestellweg** | steht (BUCH-04, BUCH-05). Kasse, Stripe-Webhook, 7 % Steuersatz, Widerrufsverzicht mit Zeitstempel, Käufer wird Lead |
| **Verfahrensbeschreibung** | gegen den Code geprüft (`BEFUND-C5`), fünf von sechs Abweichungen nachgezogen |

---

## 6. Was offen ist

**88 Buchpunkte, davon 34 rot.** Aufgeteilt nach Zuständigkeit:

| Block | Punkte | rot | Wer | Kann Claude das? |
|---|---|---|---|---|
| **B1** Geschäftsführung | 13 | 7 | David | **nein** — reine Entscheidungen |
| **B2** Recht | 21 | 10 | Anwalt | **nein** — Vorlauf mehrere Wochen |
| **B3** Autor | 18 | 7 | Autor | **teilweise** — Zahlen und Ketten ja, Fallgeschichte nein |
| **B4** Gestaltung | 16 | 8 | Manuel | **nein** — 14 Abbildungen fehlen |
| **B5** Lektorat | 14 | 0 | Lektorat | **teilweise** — Regeln prüfbar |
| **B6** Satz und Produktion | 6 | 2 | Satz | **teilweise** — zwei über die Baustrecke |

### Der Engpass ist B1

Dreizehn Entscheidungen, **null Arbeitszeit**, und sie bestimmen alles
Weitere: Umfang, ISBN, Satzbeginn und wie viele Abbildungen Manuel zeichnet.
Zwei davon sind entschieden (Untertitel, Domain `homepage-standard.de`).

**B1.1 ist jetzt entscheidbar** — die 281 Seiten liegen vor. Drei Wege:
akzeptieren, kürzen, oder Teil II abtrennen. Kapitel 5 hat 22 Seiten und eine
Abbildung; das Lektorat nennt es als ersten Kürzungskandidaten (B5.3.7).

### Was Claude ohne Entscheidung tun kann

| | Aufgabe | Aufwand |
|---|---|---|
| **1** | **B3.2** — die Zahlenketten prüfen: Elektro Hansen über neun Kapitel (76/103 = 74), die Punktkette in 15.7 (74 → 93), die Klassenmaxima in 4.5, 13.2, Anhang A und B. Alles nachrechenbar | halber Tag |
| **2** | **B5.2** — die Lektoratsregeln maschinell prüfen: keine englischen Fachbegriffe in Überschriften, keine Prüfwerkzeuge namentlich, keine erfundenen Prozentzahlen, Dateinamen im Fließtext zählen | Stunden |
| **3** | **B6.2** — Vorlage 1 und 2 je auf eine Seite: über die Baustrecke nachmessen statt schätzen | Stunden |
| **4** | **B3.3.1** — § 5 DDG statt § 5 TMG durch das ganze Buch | Minuten |
| **5** | **B6.5** — Seitenzahl auf ein Vielfaches von vier. Erst sinnvoll, wenn B1.1 entschieden ist | Minuten |

**Empfohlene Reihenfolge: 4 → 1 → 2 → 3.** Punkt 4 ist eine Suchen-Ersetzen-
Arbeit mit Rechtsbezug, Punkt 1 der zentrale Drift-Kandidat des ganzen Buchs.

### Die eine Maßstabsfrage, die vor dem Druck fallen muss

**C5-3: `se_struktur` (E2) misst zwei Dinge auf zwei Grundlagen** — die
Überschriften auf der Startseite, die 300 Wörter über die Summe aller
geprüften Seiten. Dieselbe Website bekommt im Selbsttest und in der Messung
systematisch verschiedene Werte. Drei Wege stehen in
`fassung-2027-1-offene-massstabsfragen.md`, Abschnitt 7. **Bis zur
Entscheidung benennt das Buch die Grundlage** (3.1 und 13.1) — das ist eine
Zwischenlösung, keine Antwort.

---

## 7. Regeln beim Arbeiten am Manuskript

1. **Keine Zahl von Hand, die aus dem Katalog folgt.** Sie kommt aus
   `scripts/buch-bloecke.py` oder `scripts/standard-export.py`. Beide Skripte
   berichtigen außerdem den Vermerk aller Tabellen, die sie **nicht** erzeugen.
2. **Die Abstufungstabellen der Kapitel bleiben Handarbeit.** Sie sind dort
   präziser als der Katalog („Restlaufzeit 30 Tage oder mehr") und nennen die
   Deckelregeln in derselben Zeile. `buch-bloecke.py` rechnet ihre Punktwerte
   gegen den Katalog nach, ohne die Wortwahl anzufassen.
3. **Keine Prüfwerkzeuge namentlich** (B5.2.4), keine erfundenen Prozentzahlen
   zu Ladezeit und Absprung (B5.2.5), englische Fachbegriffe nur im Glossar.
4. **Die Schutzliste in B5.1 nicht kürzen.** Sechzehn Stellen, an denen das
   Buch gegen das eigene Interesse argumentiert — genau sie werden beim Kürzen
   zuerst gestrichen, und genau sie tragen die Glaubwürdigkeit.
5. **Am Gegenstand prüfen, nicht am Werkzeug.** Ein Satzfehler zeigt sich im
   PDF, nicht in der Ausgabe des Skripts. Beim ersten Bau am 25.08. meldete
   die Baustrecke 291 Seiten und sah fertig aus — im PDF spiegelten die Ränder
   nicht, eine Marginalie lief aus dem Papier, und Tabellen zerlegten Wörter.

---

## 8. Fallen, die schon zugeschnappt sind

| Falle | Was passiert ist |
|---|---|
| **Zweite Kopie des Manuskripts** | Zwei Ordner liefen auseinander, der Export schrieb in den falschen |
| **„ERZEUGT"-Vermerke ohne Erzeuger** | 50 Tabellen behaupteten, erzeugt zu sein; drei Angaben waren dadurch veraltet |
| **Eigener Wächter, der nichts mehr findet** | Nach dem Berichtigen der Vermerke erkannte das Skript seine eigenen Marken nicht mehr und meldete zufrieden „0 Abweichungen" |
| **Nicht eingebettete Schrift** | ReportLab trägt für jede Tabelle Helvetica in die Seitenressourcen ein, auch wenn kein Zeichen sie benutzt |
| **Bekanntes als Fund gemeldet** | Zwei „neue" Befunde standen längst in `BEFUND-C2`. Vor dem Melden nachsehen |

---

## 9. Was zuerst zu tun ist

```
David:  B1 entscheiden — allen voran B1.1 (281 gemessene Seiten)
        B2 Anwaltstermin ansetzen, Anhang D mitschicken
Manuel: B4.1 — Stufenmarken, Satzmuster-Format, Ergebnisblatt
Claude: B3.3.1 (DDG) → B3.2 (Zahlenketten) → B5.2 (Lektoratsregeln)
```

**Ohne B1.1 kann Manuel nicht anfangen**, weil der Umfang die Zahl der
Abbildungen bestimmt. Ohne B2 darf nichts gedruckt werden.
