# BEFUND C1 — Versprechen gegen Messung

**Erhoben am:** 24.08.2026 · **Gegen:** `audit_criteria.py`, `audit_scoring.py`, `audit_pagespeed.py`, `audit_ai.py`
**Stand des Repos:** `77c8fbb` (main), inhaltsgleich mit `staging` für alle geprüften Dateien
**Methode:** Kriterienhinweis in Einzelanforderungen zerlegt, gegen die tatsächlichen Prüfungen im Bewertungscode gestellt

---

## Ergebnis in einer Zeile

**13 von 43 Kriterien versprechen im Hinweis mehr, als die Bewertung einlöst.** Bekannt waren drei.

Dazu ein Befund, der über C1 hinausgeht und in Abschnitt 4 steht: **Zwei von vier erhobenen Barrierefreiheits-Prüfgruppen werden nirgends ausgewertet** — und sie enthalten genau die Prüfungen, die bei `bf_semantik` fehlen.

---

## 1 · Die Abweichungen

| Kriterium | Code | Hinweis nennt | Gemessen | Δ | Bekannt |
|---|---|---|---|---|---|
| `rc_formular_dsgvo` | L5 | Einwilligungsfeld **und** Verweis auf die Datenschutzerklärung | nur das Einwilligungsfeld | **−1** | neu |
| `si_ssl` | S1 | Handshake, Gültigkeit, **Domain-Übereinstimmung** | Gültigkeit und Restlaufzeit | **−1** | neu |
| `si_drittanbieter` | S4 | externe Schriften, **Karten** und Tracking | Schriften und Tracking | **−1** | neu |
| `tp_bilder` | P5 | Format, **Dateigröße**, verzögertes Laden, Größenangaben | drei Prüfungen, die dritte fasst zwei zusammen | **−1** | ✅ bekannt |
| `bf_alt` | B3 | Anteil der Bilder mit **sinnvollem** Alternativtext | Anteil mit *irgendeinem* Alternativtext | **Qualität** | ✅ im Buch benannt |
| `bf_semantik` | B4 | genau eine H1, saubere Hierarchie, **`lang`-Attribut**, **Labels** | die ersten beiden | **−2** | ✅ bekannt |
| `bf_tastatur` | B5 | **Skip-Link**, **Fokus-Reihenfolge**, keine Tastaturfallen | Mittelwert aus vier Lighthouse-Prüfungen | **unklar** | neu |
| `se_meta` | E1 | vorhanden, sinnvolle Länge, Ort **und** Leistung | Länge Titel, Länge Beschreibung, Ort *oder* Leistung | **−1** | ✅ bekannt |
| `se_index` | E3 | `robots.txt`, `sitemap.xml`, Canonical, **kein versehentliches noindex** | drei Prüfungen; noindex ist an `robots.txt` gekoppelt | **−1** | neu |
| `se_schema` | E4 | JSON-LD, LocalBusiness, FAQ, **Bewertungen** | vorhanden, Haupttyp, Zusatztyp | **−1** | neu |
| `se_lokal` | E5 | Ort, **NAP-Angaben**, Kartenverknüpfung | Ort, **nur die Telefonnummer**, Karte oder Auszeichnung | **−1** | neu |
| `dg_mobil` | D5 | Darstellungsanweisung gesetzt, **Tap-Targets groß genug** | nur die Darstellungsanweisung | **−1** | neu |
| `ih_aktualitaet` | I2 | datierte Inhalte **und** kein veraltetes Copyright | eines von beiden genügt (`or`) | **großzügiger** | neu |
| `cv_cta` | C2 | vorhanden, **ergebnisorientiert**, im Verlauf wiederholt | gezählt wird die Anzahl passender Elemente | **Qualität** | neu |

### Die drei Muster dahinter

**Muster 1 — `und` im Hinweis, eine Prüfung im Code.** Bei `tp_bilder`, `se_meta` und `se_struktur` sind zwei Anforderungen mit `and` in einer einzigen Bedingung verbunden. Beide müssen erfüllt sein, sie zählen aber nur einmal. **Der Leser liest zwei Chancen, der Code kennt eine Hürde.**

**Muster 2 — eine Anforderung im Hinweis, die gar nicht geprüft wird.** `si_drittanbieter` nennt Karten, prüft aber nur Schriften und Tracking. `dg_mobil` nennt Tap-Targets, prüft nur die Darstellungsanweisung. `se_schema` nennt Bewertungen, prüft aber nur, ob *ein* passender Zusatztyp vorhanden ist.

**Muster 3 — ein Qualitätsversprechen ohne Qualitätsprüfung.** `bf_alt` verspricht „sinnvoll", `cv_cta` verspricht „ergebnisorientiert". Beides wird nicht geprüft. Bei `bf_alt` benennt das Buch die Lücke bereits ausdrücklich (Abschnitt 8.6) — bei `cv_cta` nicht.

### Eine Abweichung nach oben

`ih_aktualitaet` verknüpft mit `or`, wo der Hinweis `und` nahelegt. **Das Kriterium ist milder als beschrieben.** Ein Betrieb mit aktueller Jahreszahl, aber ohne datierte Inhalte bekommt den Punkt. Das ist vertretbar — es sollte nur im Hinweis stehen.

---

## 2 · Erhebungsart: deklariert gegen geschrieben

| Kriterium | Katalog deklariert | Bewertung schreibt | Stimmt |
|---|---|---|---|
| `bf_semantik` | abgeleitet | **gemessen** | ❌ |
| `bf_tastatur` | abgeleitet | abgeleitet | ✅ |
| `cv_cta` | abgeleitet | abgeleitet | ✅ |
| `cv_vertrauen` | abgeleitet | abgeleitet | ✅ |
| `rc_cookie` | gemessen | **gemessen oder abgeleitet** | ⚠️ zwei Wege |
| alle übrigen | — | — | ✅ |

**Ein echter Widerspruch, ein Sonderfall.**

`bf_semantik` ist im Katalog als abgeleitet geführt und wird als gemessen geschrieben. **Kapitel 3 verspricht dem Leser, dass jede Erhebungsart gekennzeichnet ist und er einer Einschätzung deshalb widersprechen kann.** Ein Kriterium, das im Bericht anders erscheint als im Katalog, untergräbt genau dieses Versprechen.

`rc_cookie` ist kein Fehler: Es schreibt „gemessen", wenn ein Einwilligungswerkzeug erkannt wurde, und „abgeleitet", wenn geschlossen wurde, dass keines nötig ist. **Das ist richtig und im Buch beschrieben** (Abschnitt 5.6). Der Katalog müsste beide Möglichkeiten führen.

---

## 3 · Die sieben eingeschätzten Kriterien

`audit_ai.py`, Funktion `_rubric()`, Zeile 109:

```python
lines.append(f"- {crit.key} (0-{crit.max_points}): {crit.label} — {crit.hint}")
```

**Bestätigt: Das Modell erhält je Kriterium eine einzige Zeile aus Bezeichnung und Kurzhinweis.** Ein Punkterubric — was 0, 1, 2 oder 3 Punkte bedeuten — existiert nicht.

| Kriterium | Was das Modell bekommt | Zusätzlich |
|---|---|---|
| `dg_aktualitaet` | eine Zeile | — |
| `dg_typografie` | eine Zeile | — |
| `dg_farbsystem` | eine Zeile | — |
| `dg_bildqualitaet` | eine Zeile | — |
| `ih_textqualitaet` | eine Zeile | — |
| `cv_klarheit` | eine Zeile | **Klassenprofil aus `PROFILE`** |
| `cv_angebot` | eine Zeile | **Klassenprofil aus `PROFILE`** |

**A8 aus dem Restarbeiten-Report ist damit bestätigt nicht umgesetzt.** Die acht Alterungsmerkmale für `dg_aktualitaet`, die dort verlangt werden, stehen nirgends.

**Für das Buch folgt daraus:** Die Merkmalslisten in Kapitel 10 sind zu Recht als „Orientierung für die Selbsteinschätzung, keine Bewertungsregel" gekennzeichnet. Die Klassentabellen in Kapitel 11 dürfen zu Recht als verbindlich abgedruckt werden — sie stehen tatsächlich im Prompt.

---

## 4 · 🔴 Der schwerwiegendste Fund: zwei Prüfgruppen sind gebaut und nicht angeschlossen

`audit_pagespeed.py`, Zeile 26 bis 35, definiert **vier** Barrierefreiheits-Prüfgruppen. `_a11y_scores()` berechnet für alle vier einen Mittelwert.

**Ausgewertet werden zwei.**

| Gruppe | Enthaltene Lighthouse-Prüfungen | Wird gelesen von |
|---|---|---|
| `kontrast` | `color-contrast` | `bf_kontrast` (B2) |
| `tastatur` | `bypass`, `tabindex`, `accesskeys`, `meta-refresh` | `bf_tastatur` (B5) |
| **`screenreader`** | `image-alt`, **`label`**, `link-name`, `button-name`, **`html-has-lang`**, `document-title`, `aria-required-attr`, `aria-valid-attr-value` | **niemand** |
| **`lesbarkeit`** | `font-size`, `meta-viewport`, `heading-order` | **niemand** |

### Warum das mehr ist als toter Code

**Die Gruppe `screenreader` enthält `html-has-lang` und `label`.** Das sind genau die beiden Prüfungen, die der Hinweis von `bf_semantik` verspricht — „`lang`-Attribut, Labels" — und die laut Befund 1 fehlen.

**Sie fehlen nicht. Sie werden erhoben und nicht gelesen.**

Damit ändert sich der Aufwand für A5 vollständig: Es geht nicht darum, zwei neue Messungen zu bauen, sondern darum, eine vorhandene Zahl an ein vorhandenes Kriterium anzuschließen.

**Die Gruppe `lesbarkeit` enthält `font-size`, `meta-viewport` und `heading-order`.** Auch das sind Prüfungen, für die es Kriterien gibt:

| Erhoben in `lesbarkeit` | Kriterium, das es bräuchte | Wird dort heute |
|---|---|---|
| `font-size` | `dg_typografie` (D2) | **eingeschätzt** statt gemessen |
| `meta-viewport` | `dg_mobil` (D5) | eigenständig geprüft — doppelt erhoben |
| `heading-order` | `bf_semantik` (B4), `se_struktur` (E2) | eigenständig geprüft — doppelt erhoben |

**`font-size` ist der bemerkenswerteste Eintrag der ganzen Tabelle.** Die Schriftgröße wird gemessen und liegt vor — und `dg_typografie` schätzt sie stattdessen mit einem Sprachmodell. Ein gemessener Wert, der zugunsten einer Einschätzung ungenutzt bleibt.

> **Der Code kennt dieses Muster selbst.** In `audit_scoring.py` steht bei `se_ki_lesbar` der Kommentar: *„dieselbe Familie wie L-55 (gebaut, nie angeschlossen)."* Es ist also mindestens der dritte Fall.

---

## 5 · Was ohne Abweichung ist

Diese Kriterien messen genau das, was ihr Hinweis nennt:

`rc_impressum` · `rc_datenschutz` · `rc_cookie` · `rc_bfsg` · `si_redirect` · `si_header` · `tp_lcp` · `tp_cls` · `tp_inp` · `tp_mobile` · `bf_lighthouse` · `bf_kontrast` · `se_struktur` · `se_links` · `se_ki_lesbar` · `cv_kontakt` · `cv_vertrauen` · `ih_leistungsseiten` · alle vier Infrastruktur-Kriterien

**Das sind 22 von 43.** Bei sieben weiteren wird eingeschätzt, bei 13 weicht der Hinweis ab, bei einem ist die Erhebungsart falsch deklariert.

---

## 6 · Mögliche Punkteffekte

**Nur zur Größenordnung. Die Entscheidung fällt in C4, zusammen mit C2 und C3.**

| Wenn aufgelöst durch … | Δ Katalogsumme |
|---|---|
| Alle 13 Abweichungen durch **Erweitern** der Prüfungen | bis **+10** |
| Alle 13 durch **Kürzen der Hinweise** | **0** |
| Nur die vier mit vorhandener Datengrundlage anschließen (`bf_semantik` +0, `dg_typografie` +0, `dg_mobil` +0, `si_ssl` +0) | **0** — die Punktzahl bleibt, die Messung wird genauer |

**Die dritte Zeile ist die interessanteste.** Vier Abweichungen lassen sich beheben, **ohne die Katalogsumme anzufassen** — weil die Messwerte bereits vorliegen und nur mehr Prüfungen in dieselbe Punktzahl einfließen.

---

## Zu melden

| # | Feststellung |
|---|---|
| 1 | **13 von 43 Kriterien** versprechen mehr, als sie messen. Bekannt waren drei |
| 2 | **Ein Kriterium ist falsch deklariert** (`bf_semantik`), eines hat zu Recht zwei Erhebungsarten (`rc_cookie`) |
| 3 | **A8 bestätigt nicht umgesetzt** — die eingeschätzten Kriterien bekommen eine Zeile |
| 4 | 🔴 **Zwei von vier Barrierefreiheits-Prüfgruppen werden erhoben und nirgends ausgewertet** — und sie enthalten die Prüfungen, die bei `bf_semantik` und `dg_typografie` fehlen |
| 5 | **Vier Abweichungen lassen sich ohne Änderung der Katalogsumme beheben** |
