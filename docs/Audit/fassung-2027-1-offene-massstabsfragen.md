# Fassung 2027.1 — was den Maßstab ändert

**Angelegt:** 25.08.2026 · **Stand des Katalogs:** 2026.2, 39 Kriterien, 103 Punkte
**Wahrheitsquelle im Code:** `kompagnon/backend/services/audit_criteria.py`

---

## Wozu diese Datei

Am 24.08.2026 ist entschieden worden: **Die Katalogsumme bleibt 103.** Kein
`max_points`-Wert wird angefasst. Was den Katalog verändert, wandert hierher.

Der Grund ist nicht Bequemlichkeit. Ein Standard, dessen Gewichte sich ändern,
während ein Buch darüber im Satz ist, ist kein Standard. Und ein Befund, der
in einem Chatverlauf steht, ist keine offene Frage, sondern eine Erinnerung —
der nächste Leser hält ihn für erledigt oder macht ihn neu auf. Deshalb steht
er hier, mit dem Beleg daneben.

**Was hier steht, ist gemessen und nicht entschieden.** Jeder Eintrag nennt,
was der Code heute tut, und welche Auflösungen möglich sind. Die Entscheidung
gehört David.

---

## 1. Tote Stufen — Punktwerte, die niemand erreichen kann

### 1.1 S3 · Sicherheitsheader: der dritte Header bringt nichts

`audit_scoring.py`: `scale("si_header", present / 4)` bei 3 Punkten Maximum.
Nachgerechnet:

| Vorhandene Header | Rechnung | Punkte |
|---|---|---|
| 0 von 4 | `round(0.00 × 3)` | 0 |
| 1 von 4 | `round(0.75 × 3)` | 1 |
| 2 von 4 | `round(1.50 × 3)` | **2** |
| 3 von 4 | `round(2.25 × 3)` | **2** |
| 4 von 4 | `round(3.00 × 3)` | 3 |

Wer den dritten Header setzt, bekommt dafür nichts. **Möglich:** vier Punkte
statt drei, oder eine eigene Staffelung statt der Verhältnisrechnung.

### 1.2 B5 · Tastaturbedienung: null, eine und zwei bestandene Prüfungen sind gleich viel wert

Dasselbe Verfahren bei **einem** Punkt Maximum und vier Lighthouse-Prüfungen
(`bypass`, `tabindex`, `accesskeys`, `meta-refresh`): 0, 1 und 2 bestandene
Prüfungen ergeben alle **0 Punkte**, erst ab 3 gibt es den Punkt.

Das ist der härteste Fall der Sorte, weil Tastaturbedienung der einzige
Ausfall ist, der nicht „schlechter bedienbar" heißt, sondern **„gar nicht
bedienbar"** (WCAG 2.1.1, Stufe A). **Möglich:** zwei Punkte, oder binär —
eine durchgefallene Prüfung, null Punkte.

### 1.3 C2 · Primär-CTA: den Wert 1 gibt es nicht

`3 if count >= 3 else (2 if count >= 1 else 0)`. Zwischen 2 und 0 liegt
nichts. **Möglich:** Staffelung auf 1/2/3, oder den Wert bewusst streichen.

---

## 2. Doppelwertungen — dasselbe Merkmal zählt zweimal

### 2.1 E1 / E5 · Der Ort im Titel

`se_meta` vergibt einen Punkt, wenn der Titel den Maßstab der Klasse trägt —
bei K1 bis K3 heißt das: **mit Ort**. `se_lokal` vergibt einen Punkt, wenn der
Ort im Titel **oder** in der H1 steht. Ein Betrieb, der den Ort in den Titel
schreibt, bekommt ihn zweimal.

### 2.2 C3 / E5 · Die Telefonnummer

`cv_kontakt` bewertet „Telefon klickbar", `se_lokal` vergibt einen Punkt für
`contact.tel_link`. Derselbe `tel:`-Verweis, zwei Punkte.

### 2.3 E4 / E5 · Die Betriebsauszeichnung

`se_schema` vergibt Punkte für passende `schema.org`-Typen, `se_lokal` einen
Punkt für `google_maps` **oder** `schema_localbusiness`. Wer `LocalBusiness`
auszeichnet, bekommt ihn in beiden Kriterien.

> **Zusammengenommen (S7.8):** `se_lokal` hat damit **kein einziges** Merkmal,
> das nicht anderswo gezählt wird — Ort bei E1, Telefon bei C3, Auszeichnung
> bei E4. Das ist keine Doppelwertung mehr, sondern die Frage, ob E5 als
> eigenes Kriterium bestehen bleibt. Eine Produktentscheidung, keine Korrektur.

### 2.4 B4 / E2 · Die Überschriftenstruktur

`bf_semantik` vergibt einen Punkt für `heading_struktur_ok`, `se_struktur`
einen für `h1_genau_eins and h2_vorhanden`. Buchstäblich dieselbe Bedingung.

**Auflösbar ohne Katalogänderung:** Lighthouse liefert `heading-order`. Hängt
man den DOM-Anteil von B4 daran statt an die eigene Prüfung, messen die beiden
Kriterien Verschiedenes. Der Umbau ist klein, ändert aber die Punkte realer
Seiten — deshalb hier und nicht am 24.08. erledigt (S1.4).

### 2.5 D3 / B2 · Der Kontrast

`bf_kontrast` misst ihn mit Lighthouse, `dg_farbsystem` nennt ihn im Hinweis.
**Seit dem 25.08. entschärft, nicht gelöst:** Das Rubric von D3 sagt jetzt
ausdrücklich „Nicht Teil dieses Kriteriums: der Kontrastwert". Ob das reicht,
zeigt erst die Streuungsmessung (A9).

### 2.6 D1 / I2 · Die veraltete Jahreszahl

`dg_aktualitaet` führt sie unter den Alterungsmerkmalen, `ih_aktualitaet`
bewertet die Aktualität der Inhalte. Ebenfalls durch die Abgrenzung im Rubric
entschärft.

---

## 3. Gegenläufige Kriterien

### 3.1 E3 / E7 · Keine `robots.txt` bringt netto einen Punkt

`se_index` vergibt einen Punkt für eine vorhandene, indexierende `robots.txt`.
`se_ki_lesbar` vergibt **zwei** Punkte dafür, dass kein KI-Crawler ausgesperrt
ist — und eine fehlende `robots.txt` sperrt niemanden aus.

Wer die Datei löscht, verliert einen Punkt und gewinnt zwei. Das ist kein
Rundungsfehler, sondern ein Anreiz in die falsche Richtung.

**Möglich:** die zwei Punkte an eine **vorhandene** `robots.txt` binden, die
niemanden sperrt. Ändert die Punktzahl jeder Seite ohne `robots.txt`.

---

## 4. Wiederholbarkeit

### 4.1 P5 · Die Bildstichprobe

Bewertet werden acht Bilder. Welche acht, entscheidet die Reihenfolge im DOM.
Bei einer Seite mit dreißig Bildern kann derselbe Betrieb an zwei Tagen zwei
Ergebnisse bekommen. Kapitel 3 verspricht Wiederholbarkeit ausdrücklich.

### 4.2 A9 · Die Streuung ist ungemessen

Der Restarbeiten-Report verlangt, dieselbe Website dreimal bewerten zu lassen
und die Streuung je Kriterium zu messen; über einem Punkt gilt das Rubric als
zu unscharf. **Nicht durchgeführt** — es braucht einen `ANTHROPIC_API_KEY`.
Seit dem 25.08. haben die sechs eingeschätzten Kriterien ein gestuftes Rubric
(A8); die Messung ist damit erst sinnvoll.

---

## 5. Was die Erhebung nicht kann

### 5.1 Cookies vor der Einwilligung

Die K.-o.-Tabelle nennt fünf Deckelregeln; vier können greifen.
`cookies_ohne_consent` verlangt einen Vergleich der gesetzten Cookies vor und
nach der Einwilligung — erhoben wird nur, ob im HTML ein bekanntes
Consent-Werkzeug steckt. Vermerkt in `audit_criteria.NICHT_ERHOBENE_BLOCKER`.

### 5.2 Seiten, die erst im Browser entstehen (L-107)

Die Erhebung führt kein JavaScript aus. Erkannte Fälle fallen seit dem
25.08. nach § 3.5 aus der Wertung statt mit 0 zu zählen — aber gesehen hat
die Seite weiterhin niemand, die KI-Kriterien bewerten dann leeren Text, und
eine Anwendung ohne kennzeichnendes Einhängeelement rutscht durch.

> **5.1 und 5.2 sind dieselbe Frage:** Wann bekommt die Erhebung einen echten
> Browserlauf? Beide Lücken verschwinden damit, und mehrere Punkte oben werden
> messbar statt geschätzt.

### 5.3 Die Kammerangabe, klassenabhängig (K05-1)

`_evaluate_impressum` erhebt `fields["kammer"]`, zählt sie aber nicht zu
`core`. Ein Handwerksbetrieb ohne Kammerangabe bekommt 6 von 6 Punkten. Sie
einfach in den Pflichtsatz zu nehmen, wäre falsch: Eine überregionale Agentur
(K4) hat keine Kammer. Richtig ist eine klassenabhängige Prüfung — das setzt
das Branchenmodell in `audit_collectors.py` voraus, wo es noch nicht ankommt.

### 5.4 Zwecke und Auftragsverarbeiter (K05-2)

Dieselbe Lage bei L2. Die Spezifikation nannte beides, der Code prüft
Verantwortlicher, Rechtsgrundlage und Betroffenenrechte. Die Beschreibung ist
am 24.08. auf den Stand des Codes gebracht worden; die Messung fehlt weiter.

---

## 6. Kleinigkeiten, die niemandem schaden — und trotzdem stimmen sollten

| Befund | Lage |
|---|---|
| **C3 bei K6** | Merkmale hinterlegt, obwohl die Kategorie für K6 entfällt — vermutlich toter Zweig |
| **K6-Klassenprofile unvollständig** | `se_schema` hat eines, `se_meta` nicht |
| **D5 `dg_mobil` (S1.3)** | Vergibt den Punkt für eine vorhandene Viewport-Angabe — **auch** für eine, die das Zoomen sperrt. Das ist ein WCAG-Verstoß, der belohnt wird. Lighthouse `meta-viewport` prüft strenger |

---

## 7. E2 misst zwei Dinge auf zwei Grundlagen (C5-3, 25.08.2026)

`se_struktur` vergibt zwei Punkte für zwei Teilprüfungen — und die beiden
stehen auf verschiedenen Grundlagen:

| Teilprüfung | Grundlage |
|---|---|
| genau eine Hauptüberschrift, mindestens eine Zwischenüberschrift | **nur die Startseite** (`qa` läuft gegen `base_url`) |
| mindestens 300 Wörter | **Summe über alle geprüften Seiten** (`audit_aggregat` summiert `word_count`) |

**Warum das eine Maßstabsfrage ist und keine Reparatur.** Bei einer Website
mit fünf Unterseiten ist die 300-Wörter-Schwelle praktisch immer erfüllt; der
Punkt ist dann geschenkt. Beim Leser des Selbsttests ist er es nicht — er
zählt die Startseite, wie Kapitel 13 es ihn heißt. **Dieselbe Website bekommt
im Selbsttest und in der automatischen Prüfung systematisch verschiedene
Werte**, und zwar nicht wegen der Sorgfalt des Lesers, sondern wegen der
Grundlage.

**Drei Wege, alle mit Folgen:**

| | Weg | Folge |
|---|---|---|
| **A** | Die Wortzahl auf die Startseite beziehen | strenger; viele Bestandsaudits verlieren einen Punkt |
| **B** | Die Schwelle bei der Summe anheben (etwa 300 je geprüfter Seite) | bleibt großzügig, wird aber vergleichbar |
| **C** | Belassen und im Buch benennen | seit dem 25.08. so umgesetzt — 3.1 und 13.1 sagen die Grundlage |

Weg C ist die **Zwischenlösung**, nicht die Antwort: Das Buch verschweigt die
Abweichung nicht mehr, aber der Maßstab bleibt uneinheitlich. Die Entscheidung
gehört in die Fassung 2027.1, weil A und B die Punkte realer Seiten verändern.

Quelle: `BEFUND-C5-pruefung-gegen-buchbeschreibung.md`.

---

## 8. Drei Kriterien, drei Urteile über denselben Karteneinbau (L-154, 04.09.2026)

**Aufgenommen aus dem Fremdlauf gegen `neovendo.de`.** Ein Leser meldete, die
Cookie-Prüfung setze „kein einwilligungspflichtiger Dienst vorhanden" mit
„kein Consent-Tool vorhanden" gleich. Sie tut es nicht — die Bedingung ist
gebaut. Sie liest nur die **falsche Größe**.

`detect_third_parties` liefert drei Mengen:

| Feld | Inhalt |
|---|---|
| `count` | alle acht erkannten Dienste — **einschließlich Google Maps und YouTube** |
| `tracking_services` | Analytics, Facebook, Doubleclick, Hotjar, Clarity |
| `external_fonts` | Google Fonts |
| `maps_embedded` | Google Maps — **wird erhoben und von keinem Kriterium gelesen** |

Damit bewerten drei Kriterien denselben Einbau verschieden:

| Kriterium | liest | Ergebnis bei eingebundener Karte, ohne Consent-Tool |
|---|---|---|
| `rc_cookie` (4 P) | `count > 0` | **0 von 4** |
| `si_drittanbieter` (2 P) | nur Fonts und Tracking | **2 von 2** ✓ |
| `se_lokal` (3 P), dritter Teil | `qa.google_maps` als lokales Signal | **+1 Punkt** |

Ein Einbau, ein Bericht, drei Urteile — untereinander auf derselben Seite.
Der Leser hat daraus geschlossen, die Prüfung sei kaputt.

**Rechtlich liegt `rc_cookie` näher an der Sache.** Ein Maps- oder
YouTube-Einbau überträgt vor jeder Einwilligung die IP-Adresse an einen
Drittanbieter; das ist genau der Fall, den § 25 TDDDG meint. Die Frage ist
nicht, ob das zählt, sondern **wo**.

**Drei Auflösungen, jede verschiebt Punkte:**

| | Weg | Wirkung auf reale Seiten |
|---|---|---|
| **A** | `si_drittanbieter` zieht nach: Maps und YouTube kosten dort ebenfalls einen Punkt | Seiten mit Karte verlieren zusätzlich 1 von 2 Punkten |
| **B** | `rc_cookie` wird enger: nur Tracking und Fonts lösen aus, Maps und YouTube nicht | Seiten mit Karte gewinnen 4 Punkte zurück — **widerspricht der Rechtslage** |
| **C** | `se_lokal` akzeptiert die Karte nicht mehr als lokales Signal, nur noch die LocalBusiness-Auszeichnung | Seiten mit Karte ohne Auszeichnung verlieren 1 Punkt |

**Empfehlung: A und C gemeinsam.** Beide folgen derselben Linie — ein Einbau,
der eine Einwilligung braucht, ist kein Gütezeichen. B wäre der bequemste Weg
und der einzige, der dem Betrieb schadet, weil er ihm bescheinigt, in Ordnung
zu sein.

**Nicht jetzt.** A und C zusammen kosten eine Seite mit Karte und ohne
Consent-Tool bis zu 2 weitere Punkte; alle Bestandsberichte wären damit nicht
mehr vergleichbar. Bis zur Entscheidung hält
`tests/test_massstabsfragen_2027_1.py` den heutigen Zustand fest — er wird rot,
wenn eines der drei Kriterien allein wandert.

**Zwei Kleinigkeiten hängen mit dran:**

* `maps_embedded` wird erhoben und von keinem Kriterium gelesen. Es zu löschen
  wäre falsch, solange A zur Entscheidung steht — dort ist es die Messung, die
  gebraucht wird.
* `dg_mobil` (1 P) vergibt seinen Punkt für ein `meta viewport` im Seitenkopf.
  Das steht in jeder Vorlage der letzten zehn Jahre; das Kriterium misst
  praktisch nichts. Am gerenderten Dokument wäre prüfbar, was der Name
  verspricht — ob die Seite bei 375 px ohne Querlauf steht. Der Browserlauf
  könnte das seit dem 04.09. liefern (L-153).

---

## Was hier **nicht** hingehört

Ein Befund, der sich ohne Änderung an `max_points` und ohne Änderung der
Punkte realer Seiten beheben lässt, gehört nicht hierher, sondern in die
laufende Arbeit. Diese Datei ist kein Ablageort für Unbequemes.
