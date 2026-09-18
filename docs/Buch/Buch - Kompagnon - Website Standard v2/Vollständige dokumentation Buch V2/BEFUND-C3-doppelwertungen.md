# BEFUND C3 — Doppelwertungen, vollständig erhoben

**Erhoben am:** 24.08.2026
**Methode:** Für jedes der 32 messbaren Kriterien wurden die Erhebungsfelder aufgelistet, die in seine Punktvergabe eingehen — auch mittelbar über Hilfsfunktionen. Anschließend ausgezählt, welche Felder von mehr als einem Kriterium gelesen werden.
**Nicht beurteilt, sondern gezählt.**

---

## Ergebnis in einer Zeile

**71 Erhebungsfelder, davon 6 mit mehr als einem Leser. Daraus 5 Kriterienpaare.** Die A7-Liste nannte vier — davon bestätigen sich zwei.

**Und: Die Methode hat ein Paar gefunden, das durch Lesen nicht als Doppelwertung erkannt wurde.**

---

## 1 · Die Überschneidungsmatrix

| Erhebungsfeld | Gelesen von | Art |
|---|---|---|
| `consent.cmp_detected` | **L3 · S4** | dokumentierte Verstärkung |
| `qa.h1_genau_eins` | **B4 · E2** | zwei Blickwinkel |
| `facts.city` + `qa.title_text` | **E1 · E5** | 🔴 unbemerkt |
| `contact.tel_link` | **C3 · E5** | 🟡 als Vorteil beschrieben |
| `qa.schema_localbusiness` | **E4 · E5** | 🔴 **weder in der A7-Liste noch durch Lesen gefunden** |

**Die übrigen 65 Felder haben genau einen Leser.**

---

## 2 · Je Paar

### L3 / S4 — `consent.cmp_detected` · dokumentierte Verstärkung

Tracking ohne Einwilligungswerkzeug wirkt bei L3 (0 Punkte und Deckel auf Bronze) und bei S4 (−1 Punkt). **Das ist begründet und im Code vermerkt** — es ist der schwerste Befund beider Kategorien.

**Kein Handlungsbedarf.** Kapitel 6.7 stellt die Verstärkung transparent dar.

> **Offen bleibt eine Verifikation:** Das Buch behauptet, der Bronze-Deckel greife nur einmal. Das ist in `determine_level()` zu bestätigen.

### B4 / E2 — `qa.h1_genau_eins` · zwei Blickwinkel

Dieselbe Prüfung, zwei Fragen: Können Hilfsmittel die Gliederung erfassen (B4), erkennen Suchmaschinen den Inhalt (E2). **Beide Kriterien prüfen zusätzlich Verschiedenes** — B4 die Hierarchie, E2 die Zwischenüberschrift und den Textumfang.

**Kein Handlungsbedarf.** Kapitel 8.7 und 9.5 stellen es mit demselben Wortlaut dar.

### 🔴 E1 / E5 — `facts.city` und `qa.title_text` · unbemerkt

| | E1, dritte Prüfung | E5, erste Prüfung |
|---|---|---|
| Bedingung | Ort im Titel (K1, K2, K3, K6) | Ort im Titel **oder** in der H1 |
| Wert | 1 Punkt | 1 Punkt |

**Wer den Ort im Seitentitel führt, erhält dafür zweimal einen Punkt.** Betroffen sind K1, K2 und K3 — die drei Klassen, die zusammen den größten Teil der Zielgruppe ausmachen.

**Keine Begründung in Code oder Spezifikation.** Anders als bei L3/S4 gibt es keinen Vermerk, dass die Verstärkung gewollt wäre.

**Möglicher Punkteffekt:** −1, falls aufgelöst.

### 🟡 C3 / E5 — `contact.tel_link` · als Vorteil beschrieben

Die klickbare Telefonnummer zählt bei C3 (Kontaktwege) und bei E5 (lokale Signale), je einen Punkt.

**Das Buch beschreibt es an zwei Stellen als Vorteil:** Kapitel 9.8 und 11.7 sagen dem Leser, dass eine Änderung von wenigen Zeichen auf zwei Kriterien wirkt. **Als Motivation ist das richtig. Als Bewertung ist es eine Doppelzählung ohne Begründung.**

**Möglicher Punkteffekt:** −1, falls aufgelöst.

### 🔴 E4 / E5 — `qa.schema_localbusiness` · der Fund, der die Methode rechtfertigt

Die Betriebsauszeichnung in den strukturierten Daten zählt bei **E4** als Haupttyp und erfüllt bei **E5** die dritte Prüfung (Kartenbezug).

**Dieses Paar stand weder in der A7-Liste noch ist es beim Durchschreiben der acht Kategoriekapitel als Doppelwertung aufgefallen.** Kapitel 9.8 beschreibt es sogar ausdrücklich als klugen Handgriff:

> *„Die Betriebsauszeichnung erfüllt dieselbe Prüfung, lädt nichts nach und bringt Ihnen zusätzlich einen Punkt bei E4."*

Das ist als Ratschlag richtig. Als Befund ist es dasselbe Merkmal, zweimal gezählt.

**Möglicher Punkteffekt:** −1, falls aufgelöst.

---

## 3 · Abgleich mit der bisherigen A7-Liste

| A7 nannte | Durch Feldauszählung bestätigt | Anmerkung |
|---|---|---|
| **L3 / S4** | ✅ ja | dokumentierte Verstärkung |
| **B4 / E2** | ✅ ja | zwei Blickwinkel |
| **D2 / B2** | ❌ **nicht auffindbar** | D2 ist ein eingeschätztes Kriterium ohne Feldliste |
| **D4 / C4** | ❌ **nicht auffindbar** | dito |
| — | 🔴 **E1 / E5 neu** | durch Lesen gefunden, durch Zählung bestätigt |
| — | 🟡 **C3 / E5 neu** | im Buch als Vorteil beschrieben |
| — | 🔴 **E4 / E5 neu** | **nur durch Zählung gefunden** |

**Die A7-Liste war zu zwei Vierteln richtig und zur Hälfte nicht überprüfbar.**

---

## 4 · Die Grenze der Methode — ausdrücklich

**Die Feldauszählung findet nur Überschneidungen zwischen gemessenen Kriterien.** Die sieben eingeschätzten Kriterien haben keine Feldliste — das Modell bekommt einen Bildschirmabzug und Text, nicht einzelne Merkmale.

**Damit sind vier Verdachtsfälle mit dieser Methode grundsätzlich nicht prüfbar:**

| Paar | Vermutete Überschneidung | Nur durch Lesen erkennbar |
|---|---|---|
| B2 / D3 | Kontrast — gemessen und eingeschätzt | ja |
| D2 / B2 | Typografie und Kontrast | ja |
| D4 / C4 | echte Objektfotos | ja |
| D1 / I2 | veraltete Jahreszahl | ja |

**Sie bleiben Vermutungen.** Sie lassen sich erst prüfen, wenn A8 umgesetzt ist und die eingeschätzten Kriterien ein ausformuliertes Rubric bekommen — dann kann man dessen Merkmale gegen die Feldliste stellen.

> **Ein Nebenergebnis von C1 macht drei davon lösbar:** Die Lighthouse-Gruppe `lesbarkeit` enthält `font-size` und wird nicht ausgewertet. Würde `dg_typografie` daran angeschlossen, hätte es eine Feldliste — und die Überschneidung mit B2 wäre messbar statt vermutet.

---

## 5 · Bewertung nach Art

| Art | Anzahl | Paare |
|---|---|---|
| **Bewusste Verstärkung, dokumentiert** | 1 | L3 / S4 |
| **Zwei Blickwinkel, begründet** | 1 | B4 / E2 |
| 🔴 **Unbemerkte Dopplung** | 3 | E1 / E5 · C3 / E5 · E4 / E5 |
| **Nicht prüfbar (eingeschätzte Kriterien)** | 4 | B2/D3 · D2/B2 · D4/C4 · D1/I2 |

**Alle drei unbemerkten Dopplungen betreffen E5 — die lokalen Signale.**

Das ist kein Zufall. E5 prüft drei Merkmale, und **jedes einzelne davon wird auch anderswo gezählt**: der Ort bei E1, die Telefonnummer bei C3, die Betriebsauszeichnung bei E4.

**E5 ist damit das Kriterium mit der schwächsten eigenständigen Grundlage im ganzen Katalog.** Es misst nichts, was nicht schon gemessen wird — es bündelt es unter einer anderen Frage.

**Das ist eine Produktentscheidung, keine technische.** Für einen lokalen Betrieb ist „werde ich am Ort gefunden" eine eigenständige und wichtige Frage. Ob sie eigene Punkte verdient oder ob die drei Merkmale dort genügen, wo sie ohnehin gezählt werden, entscheidet die Geschäftsführung.

---

## Zu melden

| # | Feststellung |
|---|---|
| 1 | **5 Kriterienpaare aus 6 mehrfach gelesenen Feldern**, davon **3 unbemerkt** |
| 2 | Von den vier bisher genannten bestätigen sich **zwei**; zwei sind mit dieser Methode nicht prüfbar |
| 3 | 🔴 **Die Methode hat E4 / E5 gefunden — das war weder in der A7-Liste noch durch Lesen aufgefallen.** Der Prüfstein aus dem Prompt ist damit bestanden |
| 4 | 🔴 **Alle drei unbemerkten Dopplungen betreffen E5.** Jedes seiner drei Merkmale wird auch anderswo gezählt |
| 5 | **Vier Verdachtsfälle bleiben unprüfbar**, weil die eingeschätzten Kriterien keine Feldliste haben. Sie werden prüfbar, sobald A8 umgesetzt ist |
| 6 | Möglicher Punkteffekt: **−1 bis −3** |
