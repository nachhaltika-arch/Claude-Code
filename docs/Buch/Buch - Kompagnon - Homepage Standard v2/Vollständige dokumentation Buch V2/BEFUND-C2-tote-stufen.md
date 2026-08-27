# BEFUND C2 — Tote Stufen und unerreichbare Punktwerte

**Erhoben am:** 24.08.2026 · **Methode:** vollständige Durchrechnung aller möglichen Eingaben, nicht Lesen des Codes
**Geprüft:** alle 39 bewerteten Kriterien

---

## Ergebnis in einer Zeile

**Zwei tote Stufen, drei unerreichbare Punktwerte — und zwei davon stehen im Buchmanuskript.**

---

## 1 · Die vollständige Wertetabelle

| Code | Kriterium | Max | Tatsächlich mögliche Werte | Befund |
|---|---|---|---|---|
| L1 | `rc_impressum` | 6 | 0 · 3 · 6 | ✅ begründet — die Pflicht ist nicht teilbar |
| L2 | `rc_datenschutz` | 6 | 0 · 3 · 6 | ✅ begründet |
| L3 | `rc_cookie` | 4 | 0 · 4 | ✅ binär |
| L4 | `rc_bfsg` | 2 | 0 · 2 | ✅ binär |
| L5 | `rc_formular_dsgvo` | 2 | 0 · 1 · 2 | ✅ lückenlos |
| S1 | `si_ssl` | 3 | 0 · 2 · 3 | ✅ begründet — die 1 ist bewusst leer |
| S2 | `si_redirect` | 2 | 0 · 2 | ✅ binär |
| **S3** | **`si_header`** | **3** | **0 · 1 · 2 · 2 · 3** | 🔴 **tote Stufe** |
| S4 | `si_drittanbieter` | 2 | 0 · 1 · 2 | ✅ lückenlos |
| P1 | `tp_lcp` | 4 | 0 · 2 · 4 | ✅ begründet — Schwellen des Messverfahrens |
| P2 | `tp_cls` | 3 | 0 · 1 · 3 | ✅ begründet |
| P3 | `tp_inp` | 2 | 0 · 1 · 2 | ✅ lückenlos |
| P4 | `tp_mobile` | 3 | 0 · 1 · 2 · 3 | ✅ lückenlos |
| P5 | `tp_bilder` | 3 | 0 · 1 · 2 · 3 | ✅ lückenlos |
| B1 | `bf_lighthouse` | 3 | 0 · 1 · 2 · 3 | ✅ lückenlos |
| **B2** | **`bf_kontrast`** | **2** | **0 · 2** | 🔴 **die 1 ist unerreichbar** |
| B3 | `bf_alt` | 2 | 0 · 1 · 2 | ✅ lückenlos |
| B4 | `bf_semantik` | 2 | 0 · 1 · 2 | ✅ lückenlos |
| **B5** | **`bf_tastatur`** | **1** | **0 · 0 · 0 · 1 · 1** | 🔴 **zwei tote Stufen** |
| E1 | `se_meta` | 3 | 0 · 1 · 2 · 3 | ✅ lückenlos |
| E2 | `se_struktur` | 2 | 0 · 1 · 2 | ✅ lückenlos |
| E3 | `se_index` | 3 | 0 · 1 · 2 · 3 | ✅ lückenlos |
| E4 | `se_schema` | 3 | 0 · 1 · 2 · 3 | ✅ lückenlos |
| E5 | `se_lokal` | 3 | 0 · 1 · 2 · 3 | ✅ lückenlos |
| E6 | `se_links` | 1 | 0 · 1 | ✅ binär |
| E7 | `se_ki_lesbar` | 3 | 0 · 1 · 2 · 3 | ✅ lückenlos |
| D1–D4 | eingeschätzt | 9 | 0 bis Max | — |
| D5 | `dg_mobil` | 1 | 0 · 1 | ✅ binär |
| C1 | eingeschätzt | 3 | 0 bis 3 | — |
| **C2** | **`cv_cta`** | **3** | **0 · 2 · 3** | 🔴 **die 1 ist unerreichbar** |
| C3 | `cv_kontakt` | 3 | 0 · 1 · 2 · 3 | ✅ lückenlos |
| C4 | `cv_vertrauen` | 3 | 0 · 1 · 2 · 3 | ✅ lückenlos |
| C5 | eingeschätzt | 3 | 0 bis 3 | — |
| I1 | `ih_leistungsseiten` | 2 | 0 · 1 · 2 | ✅ lückenlos |
| I2 | `ih_aktualitaet` | 1 | 0 · 1 | ✅ binär |
| I3 | eingeschätzt | 2 | 0 bis 2 | — |

**26 der 32 messbaren Kriterien sind lückenlos oder begründet.** Vier haben einen Befund.

---

## 2 · Je Befund

### 🔴 B5 `bf_tastatur` — der schwerwiegendste

**Ein Punkt, verteilt auf vier Lighthouse-Prüfungen, kaufmännisch gerundet:**

| Bestandene Prüfungen | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| Anteil | 0,00 | 0,25 | 0,50 | 0,75 | 1,00 |
| **Punkte** | **0** | **0** | **0** | **1** | **1** |

**Zwei bestandene Prüfungen sind so viel wert wie null.** Und der Grenzfall bei genau 0,50 ergibt null, nicht eins — Python rundet 0,5 zur geraden Zahl ab.

**Praktische Folge:** Ein Betrieb, der zwei der vier Tastaturprüfungen besteht, bekommt dieselbe Punktzahl wie einer, der keine besteht. Der Anreiz, von null auf zwei zu kommen, ist null.

**Ein Punkt lässt sich nicht sinnvoll auf vier Prüfungen verteilen.** Entweder wird das Kriterium binär (eine Prüfung entscheidet), oder es bekommt mehr Punkte.

### 🔴 B2 `bf_kontrast` — und das Buch druckt einen Wert, den es nicht gibt

Die Gruppe `kontrast` enthält **genau eine** Lighthouse-Prüfung: `color-contrast`. Barrierefreiheitsprüfungen bei Lighthouse sind binär — bestanden oder nicht.

**Der Anteil kann deshalb nur 0,0 oder 1,0 sein. Mögliche Punktwerte: 0 oder 2.**

> **🔴 Fehler im Buchmanuskript.** Kapitel 8.5 druckt eine dreistufige Tabelle:
>
> | Punkte | Bedingung |
> |---|---|
> | 2 | keine oder nahezu keine Kontrastbeanstandung |
> | **1** | **ein Teil der Textelemente beanstandet** |
> | 0 | überwiegend beanstandet |
>
> **Die mittlere Zeile beschreibt einen Zustand, den es nicht gibt.** Ein Leser, der genau ein beanstandetes Textelement hat, erwartet einen Punkt und bekommt null.

Das ist genau der Fund, für den Meldepunkt 4 des Prompts C2 gedacht war: eine Wertetabelle im Buch, die anders ausfällt als der Code.

### 🔴 S3 `si_header` — bekannt, bestätigt

| Gesetzte Header | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| Punkte | 0 | 1 | 2 | **2** | 3 |

Der dritte Header verändert die Punktzahl nicht. Das Buch weist es in Kapitel 6.6 offen aus und macht eine Handlungsempfehlung daraus.

### 🟡 C2 `cv_cta` — bekannt, Buch ist korrekt

Mögliche Werte: 0 · 2 · 3. Der Punktwert 1 kommt nicht vor. **Kapitel 11.6 druckt die Staffelung korrekt** und leitet daraus die Handlungsempfehlung ab, dass der Schritt von null auf ein Angebot zwei Punkte bringt.

Kein Buchfehler — aber eine grobe Staffelung für ein Dreipunktekriterium.

---

## 3 · Was ausdrücklich **kein** Befund ist

Diese Sprünge sind begründet und gehören so:

| Code | Werte | Begründung |
|---|---|---|
| P1 `tp_lcp` | 0 · 2 · 4 | Die Schwellen 2,5 s und 4,0 s stammen aus dem Messverfahren. Ein Zwischenwert würde Genauigkeit behaupten, die die Messung nicht hat |
| P2 `tp_cls` | 0 · 1 · 3 | dito, Schwellen 0,1 und 0,25 |
| S1 `si_ssl` | 0 · 2 · 3 | Die 2 ist eine Vorwarnung bei unter 30 Tagen Restlaufzeit. Die 1 bleibt bewusst leer |
| L1, L2 | 0 · 3 · 6 | „Erreichbar" und „vollständig" sind zwei Zustände, keine Skala. Die Pflicht ist nicht teilbar |

**Alle vier sind im Buch korrekt abgedruckt.**

---

## 4 · Mögliche Punkteffekte

| Befund | Auflösung ohne Summenänderung | Auflösung mit Summenänderung |
|---|---|---|
| **B5** | binär machen — eine entscheidende Prüfung statt vier | auf 2 Punkte, dann 0/1/2 bei 0–1 / 2–3 / 4 Prüfungen: **+1** |
| **B2** | Buchtabelle auf zwei Stufen korrigieren — **kostet nichts** | zweite Kontrastprüfung aufnehmen, dann wird die 1 erreichbar: ±0 |
| **S3** | Header gewichten (CSP und X-Frame schwerer) | auf 4 Punkte: **+1** |
| **C2** | so lassen — das Buch beschreibt es korrekt | auf 4 Punkte für vier Stufen: **+1** |

**Größenordnung: 0 bis +3.**

**B2 ist der einzige Befund, der ohne jede Entscheidung behoben werden muss** — die Buchtabelle beschreibt einen Zustand, den es nicht gibt. Das ist eine Korrektur, keine Wahl.

---

## Zu melden

| # | Feststellung |
|---|---|
| 1 | **Zwei tote Stufen** (S3 bei drei Headern, B5 bei zwei Prüfungen) und **drei unerreichbare Punktwerte** (B2 die 1, C2 die 1, S1 die 1 — letztere gewollt) |
| 2 | 🔴 **B5 ist schwerwiegender als S3:** Null, eine und zwei bestandene Prüfungen sind gleich viel wert |
| 3 | 🔴 **Fehler im Buchmanuskript gefunden:** Kapitel 8.5 druckt für B2 einen Punktwert 1, den es nicht gibt |
| 4 | **26 von 32 messbaren Kriterien sind lückenlos.** Vier Sprünge sind begründet und im Buch korrekt |
| 5 | Möglicher Punkteffekt: **0 bis +3** |
