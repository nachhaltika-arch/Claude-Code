# OFFENE PUNKTE · SOFTWARE

**Stand:** 24.08.2026, nach Block C
**Umfang:** 35 Punkte mit technischer Zuständigkeit, davon 23 rot
**Ort der Umsetzung:** Claude Code im Repo `nachhaltika-arch/Claude-Code`, Branch `staging`

> **Alle Befunde sind gemessen, nicht vermutet.** Die vier Berichte aus Block C liegen vor. Was hier steht, ist die Umsetzung — nicht die Erhebung.

---

## Vorentscheidung, die alles Weitere trägt

**Die Katalogsumme bleibt 103.** Empfehlung aus BEFUND-C4, Szenario B. Damit gilt für jeden Punkt dieser Liste:

> **Keine Änderung an einem `max_points`-Wert.** Was den Katalog verändert, wandert in die Fassung 2027.1.

---

# S1 · Anschlüsse — die Daten liegen bereits vor

**Der wertvollste Block. Kein Bauauftrag, sondern Verkabelung.**

| ID | Aufgabe | Aus | Δ Punkte |
|---|---|---|---|
| **S1.1** | 🔴 **`screenreader`-Gruppe an `bf_semantik` anschließen.** `A11Y_AUDIT_GROUPS` in `audit_pagespeed.py` liefert `html-has-lang` und `label`. Niemand liest sie. Es sind genau die Prüfungen, die der Kriterienhinweis verspricht | C1 · K08-1 | **0** |
| **S1.2** | 🔴 **`lesbarkeit`-Gruppe an `dg_typografie` anschließen.** Sie liefert `font-size`. Die Schriftgröße wird gemessen — und das Kriterium schätzt sie mit einem Sprachmodell | C1 | **0** |
| **S1.3** | Prüfen, ob `meta-viewport` aus `lesbarkeit` `dg_mobil` ersetzen oder ergänzen soll — derzeit doppelt erhoben | C1 | 0 |
| **S1.4** | Prüfen, ob `heading-order` aus `lesbarkeit` an `bf_semantik` oder `se_struktur` gehört | C1 | 0 |

**Wirkung von S1.2:** Ein eingeschätztes Kriterium wird zu einem gemessenen. Der Anteil der Einschätzungen sinkt von 17 auf 15 Punkte — und drei bisher unprüfbare Doppelwertungsverdachte werden messbar.

---

# S2 · Deklarationen richtigstellen

| ID | Aufgabe | Aus | Δ |
|---|---|---|---|
| **S2.1** | 🔴 `bf_semantik` im Katalog als **gemessen** führen — die Bewertung schreibt es bereits so | C1 · K08-2 | 0 |
| **S2.2** | `rc_cookie` mit **zwei** Erhebungsarten führen — gemessen bei erkanntem Werkzeug, abgeleitet beim Schluss auf Entbehrlichkeit | C1 | 0 |

> **Warum das mehr ist als Kosmetik:** Kapitel 3 verspricht dem Leser, dass jede Erhebungsart gekennzeichnet ist und er einer Einschätzung deshalb widersprechen kann. Ein Kriterium, das im Bericht anders erscheint als im Katalog, untergräbt genau dieses Versprechen.

---

# S3 · Kriterienhinweise auf das kürzen, was gemessen wird

**Neun Hinweise versprechen mehr, als die Bewertung einlöst. Keine Punktänderung.**

| ID | Kriterium | Streichen oder präzisieren | Aus |
|---|---|---|---|
| **S3.1** | `rc_formular_dsgvo` (L5) | „und Verweis auf die Datenschutzerklärung" — wird nicht geprüft | C1 |
| **S3.2** | `si_ssl` (S1) | „Domain-Übereinstimmung" — fließt in „gültig" ein, nicht eigenständig | C1 |
| **S3.3** | `si_drittanbieter` (S4) | „Karten" — wird nicht geprüft | C1 |
| **S3.4** | `tp_bilder` (P5) | Dateigröße und Größenangaben sind **eine** Prüfung, nicht zwei | C1 |
| **S3.5** | `bf_alt` (B3) | „sinnvoll" — geprüft wird nur das Vorhandensein | C1 |
| **S3.6** | `se_index` (E3) | noindex ist an `robots.txt` gekoppelt, keine eigene Prüfung | C1 |
| **S3.7** | `se_schema` (E4) | „Bewertungen" — es genügt *ein* passender Zusatztyp | C1 |
| **S3.8** | `se_lokal` (E5) | „NAP-Angaben" — geprüft wird nur die Telefonnummer | C1 |
| **S3.9** | `dg_mobil` (D5) | „Tap-Targets groß genug" — wird nicht geprüft | C1 |
| **S3.10** | `ih_aktualitaet` (I2) | `und` durch `oder` ersetzen — das Kriterium ist milder als beschrieben | C1 |
| **S3.11** | `cv_cta` (C2) | „ergebnisorientiert" — gezählt wird die Anzahl | C1 |
| **S3.12** | `ih_textqualitaet` (I3) | „Worthülsen" streichen — der Prompt untersagt dieses Wort in der Ausgabe | K12-3 |

**Nach S3 stimmt jeder Kriterienhinweis mit dem überein, was gemessen wird.** Danach kann der Export aus `BUCH-F2` sie direkt ins Buch übernehmen.

---

# S4 · Spezifikation nachziehen

**Sechs Abweichungen, keine davon dokumentiert.**

| ID | Stelle | Was nachzuziehen ist | Aus |
|---|---|---|---|
| **S4.1** | § 3.1 | Gewichtungstabelle: SEO 18 statt 15, Summe 103 statt 100 | C4 |
| **S4.2** | § 3.2, L1 | Kammerangabe: entweder in den Pflichtsatz oder aus der Spezifikation | C4 · K05-1 |
| **S4.3** | § 3.2, L2 | Zwecke und Auftragsverarbeiter: dito | C4 · K05-2 |
| **S4.4** | § 2.4 | Klassenmaxima: die festen Werte (79/78) durch die gerechneten ersetzen | C4 · K04-1 |
| **S4.5** | § 6 | GEO: der Wert 0–10 existiert nicht. Fünf Prüfpunkte ohne Zahl beschreiben | C4 · K16-2 |
| **S4.6** | § 3.2, E1–E6 | siebtes SEO-Kriterium nachtragen | C4 |
| **S4.7** | 2026.1-Datei | Warnhinweis „überholt" in Zeile 3 setzen | BUCH-F2 |

## 🔴 S4.8 — Die Verfahrensfrage

Das 2026.2-Dokument setzt die Regel *„Änderungen am Maßstab erfolgen hier zuerst."* **Sie wurde in null von sechs Fällen befolgt.**

**Zwei Auswege:**

| | Weg | Aufwand |
|---|---|---|
| **A** | Regel durchsetzen — jede Katalogänderung erst in die Spezifikation | Disziplin, dauerhaft |
| **B** | **Spezifikation aus dem Code erzeugen**, wie `BUCH-F2` es für das Buch tut | einmalig, Prototyp läuft |

**Empfehlung: B.** Ein Verfahren, das an Aufmerksamkeit hängt, hat sich in diesem Projekt zweimal als unzuverlässig erwiesen.

---

# S5 · Fundament — die Prompts liegen vor

| ID | Prompt | Aufgabe |
|---|---|---|
| **S5.1** | `BUCH-F0` | Pflicht-Check in 13 Buch-Prompts auf `staging` |
| **S5.2** | `BUCH-F0b` | Entscheidungsprotokoll: 103 bleibt, mit Begründung aus C4 |
| **S5.3** | `BUCH-F1` | Punktabstufungen aus `audit_scoring.py` in Daten überführen |
| **S5.4** | `BUCH-F2` | Exportskript — **Prototyp existiert und läuft** |
| **S5.5** | 🔴 **Neu:** Feld `buch_label` am Kriterium — der Katalog führt Jargon, das Buch deutsche Bezeichnungen | |
| **S5.6** | 🔴 **Neu:** Feld `buch_code` am Kriterium — L1, S3, E7. Nichts im Repo verbindet sie heute | |
| **S5.7** | `BUCH-F3` | Drift-Wächter auf sechs Ebenen |

---

# S6 · Verifikationen — Behauptungen des Buchs prüfen

**Das Buch behauptet diese Dinge. Sie sind nicht bestätigt.**

| ID | Behauptung im Buch | Wo | Aus |
|---|---|---|---|
| **S6.1** | 🔴 Der Bronze-Deckel greift nur **einmal** bei L3/S4 | 6.7 | K06-2 |
| **S6.2** | 🔴 Jedes Ergebnis nennt die Fassung des Standards | 2.7 | K02-3 |
| **S6.3** | 🔴 P1–P4 liefern in einem echten Lauf Werte | 7.3 | K07-2 |
| **S6.4** | Die Betriebsauszeichnung erfüllt E5 auch **ohne** Karte | 9.8 | K09-4 |
| **S6.5** | Das Frontend zeigt acht Kategorien | — | § 9 Punkt 3 |

> **Eine gedruckte Zusage, die die Software nicht einlöst, ist genau der Fehlertyp, der dieses Buchprojekt schon einmal blockiert hat.**

---

# S7 · Offene Befunde ohne Entscheidung

**Gemessen, aber die Auflösung steht in der Fassung 2027.1.**

| ID | Befund | Möglicher Δ |
|---|---|---|
| **S7.1** | S3: tote Stufe beim dritten Header | +1 oder Gewichtung |
| **S7.2** | 🔴 B5: null, eine und zwei bestandene Prüfungen sind gleich viel wert | +1 oder binär |
| **S7.3** | C2: Punktwert 1 unerreichbar | +1 oder belassen |
| **S7.4** | 🔴 E1 / E5 — Ort im Titel doppelt gewertet | −1 |
| **S7.5** | 🟡 C3 / E5 — Telefonnummer doppelt gewertet | −1 |
| **S7.6** | 🔴 E4 / E5 — Betriebsauszeichnung doppelt gewertet | −1 |
| **S7.7** | 🔴 E3 / E7 heben sich auf: keine `robots.txt` bringt netto +1 | 0 |
| **S7.8** | E5 hat keine eigenständige Grundlage — alle drei Merkmale werden anderswo gezählt | Produktentscheidung |
| **S7.9** | P5-Stichprobe: acht Bilder, Ergebnis kann zwischen Läufen schwanken | Wiederholbarkeit |
| **S7.10** | C3 bei K6: Merkmale hinterlegt, obwohl die Kategorie entfällt — toter Zweig? | 0 |
| **S7.11** | K6-Klassenprofile unvollständig: `se_schema` hat eines, `se_meta` nicht | 0 |

---

# S8 · Größere Vorhaben

| ID | Aufgabe | Aus | Wirkung |
|---|---|---|---|
| **S8.1** | 🔴 **Der Bewertungsprompt widerspricht dem Standard.** „Wenn du etwas nicht beurteilen kannst, vergib 0 Punkte" gegen Abschnitt 3.5. Ein Betrieb verliert bis zu neun Punkte für etwas, das er nicht getan hat | K10-1 | **hoch** |
| **S8.2** | 🔴 **A8 umsetzen** — die eingeschätzten Kriterien bekommen ein ausformuliertes Punkterubric statt einer Zeile | K10-2 · K11-2 | **hoch** — macht drei Doppelwertungen prüfbar |
| **S8.3** | 🔴 **A9 messen** — dieselbe Website dreimal bewerten, Streuung je Kriterium. Kapitel 3 verspricht Wiederholbarkeit | K10-3 | **hoch** |
| **S8.4** | 🔴 **C7 erheben** — Häufigkeit der zwanzig Befunde über die geprüften Websites. Nach `BUCH-F2` eine Abfrage | K14-3 | **Umsatz** |
| **S8.5** | 🔴 **Prüfpunkt 5 aus § 9** — zwei weitere Läufe gegen fremde Websites aus anderen Klassen. Der erste hat fünf Erhebungsfehler gefunden | C4 | **hoch, eine Stunde** |
| **S8.6** | PDF-Formularfelder für Anhang C und Kapitel 13 | Anh C-5 | Produktion |

---

# Reihenfolge

```
S1  Anschlüsse            ← halber Tag, größte Wirkung, keine Summenänderung
S2  Deklarationen         ← eine Stunde
S3  Hinweise kürzen       ← halber Tag
S4  Spezifikation         ← halber Tag, plus Entscheidung S4.8
S5  Fundament F0–F3       ← Prompts liegen vor
S6  Verifikationen        ← eine Stunde, bevor gedruckt wird
S8.5 Zwei Klassenläufe    ← eine Stunde, hoher Ertrag
S8.4 C7 erheben           ← nach F2
S8.1–S8.3                 ← eigene Vorhaben
S7  Fassung 2027.1        ← nicht jetzt
```

**S1 zuerst.** Es behebt drei als „fehlt" geführte Befunde, kostet keine Katalogänderung — und macht ein eingeschätztes Kriterium zu einem gemessenen.
