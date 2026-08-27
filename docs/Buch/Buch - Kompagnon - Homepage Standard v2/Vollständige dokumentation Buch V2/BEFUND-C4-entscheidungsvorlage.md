# BEFUND C4 — Spezifikationsabgleich und Entscheidungsvorlage

**Erhoben am:** 24.08.2026 · **Grundlage:** BEFUND C1, C2, C3 und der Abgleich unten
**Geprüft:** `audit-anforderungen-2026-08-11.md` und `2026-08-14-bewertungslogik-homepage-standard-2026-2.md` gegen den Code

---

# TEIL 1 · Die sechs Fragen

| # | Frage | Antwort |
|---|---|---|
| 1 | Kriterien, die mehr versprechen als sie messen | **13 von 43** |
| 2 | Tote Stufen und unerreichbare Punktwerte | **2 tote Stufen, 2 echte unerreichbare Werte** |
| 3 | Doppelwertungen, davon unbemerkt | **5 gezählt / 3 unbemerkt** · 4 weitere nicht prüfbar |
| 4 | Widersprüchlich deklarierte Kriterien | **1** (`bf_semantik`) |
| 5 | Abweichungen Spezifikation ↔ Code | **6**, davon dokumentiert: **0** |
| 6 | **Katalogsumme danach** | **siehe Teil 4 — drei Szenarien** |

---

# TEIL 2 · Spezifikation gegen Code

## 2.1 Die Gewichtungstabelle — § 3.1

| Kategorie | Spezifikation | Code | Δ |
|---|---|---|---|
| Recht & Compliance | 20 | 20 | — |
| Sicherheit & Datenschutz | 10 | 10 | — |
| Performance | 15 | 15 | — |
| Barrierefreiheit | 10 | 10 | — |
| **SEO & Auffindbarkeit** | **15** | **18** | **+3** |
| Design & Gestaltung | 10 | 10 | — |
| Conversion & Nutzerführung | 15 | 15 | — |
| Inhalt & Substanz | 5 | 5 | — |
| **Summe** | **100** | **103** | **+3** |

**Sieben von acht Kategorien stimmen exakt.** Die gesamte Abweichung sitzt in einem Kriterium: `se_ki_lesbar`, aufgenommen am 21.08. ohne Nachtrag in der Spezifikation.

## 2.2 Die sechs Abweichungen

| # | Stelle | Spezifikation sagt | Code macht | Dokumentiert |
|---|---|---|---|---|
| 1 | § 3.1 | SEO 15 Punkte, Summe 100 | SEO 18, Summe 103 | ❌ |
| 2 | § 3.2, L1 | Kammer bei Handwerk ist Pflichtangabe | wird erhoben, zählt nicht | ❌ |
| 3 | § 3.2, L2 | Zwecke und Auftragsverarbeiter sind Pflichtinhalte | prüft Verantwortlicher, Rechtsgrundlagen, Betroffenenrechte | ❌ |
| 4 | § 2.4 | feste Klassenmaxima, in sich widersprüchlich (79 gegen 78 bei K6) | rechnet aus, kommt auf 81 | ⚠️ im Quelltext vermerkt |
| 5 | § 6 | GEO-Wert 0–10 mit zehn Merkmalen | fünf Prüfpunkte ohne Zahl, zwei davon unerhoben | ❌ |
| 6 | § 3.2, E1–E6 | sechs SEO-Kriterien | sieben | ❌ |

**Von sechs Abweichungen ist eine im Quelltext vermerkt, keine in der Spezifikation.**

## 2.3 Die Prüfpunkte aus § 9

| # | Prüfpunkt | Stand |
|---|---|---|
| 1 | Stufenschwellen Frontend gegen Backend | ✅ erledigt — 95/85/70/50 an allen drei Stellen |
| 2 | Umbau auf dem Arbeitsbranch | ✅ gegenstandslos — `claude/*`-Branches sind verworfen |
| 3 | Zeigt das Frontend acht Kategorien | ⚠️ **ungeprüft** |
| 4 | PageSpeed-Key auf Render | ✅ gesetzt, Namensdreher behoben |
| 5 | **Lauf gegen drei echte fremde Websites** | 🔴 **eine von drei** |
| 6 | Quellen-Kennzeichnung im Bericht sichtbar | ✅ am 15.08. vermerkt |

> **§ 9 sagt selbst: „Punkt 5 zuerst."** Er ist zu einem Drittel erledigt. Der eine Lauf hat fünf Erhebungsfehler freigelegt — darunter eine Fehlerseite, die als Messung zählte. **Zwei weitere Läufe kosten eine Stunde.**

## 2.4 🔴 Die Verfahrensfrage

Das 2026.2-Dokument setzt in § 0 die Regel:

> *„Bei Widersprüchen zum Code gilt `services/audit_criteria.py`; Änderungen am Maßstab erfolgen hier zuerst."*

**Befolgt wurde sie in null von sechs Fällen.**

Eine Regel, an die sich niemand hält, ist schlimmer als keine — sie erzeugt Vertrauen in eine Ordnung, die es nicht gibt. **Es gibt zwei ehrliche Auswege:**

**A · Durchsetzen.** Jede Katalogänderung geht erst in die Spezifikation. Kostet Disziplin und verlangt, dass jemand sie einfordert.

**B · Umkehren.** Die Spezifikation wird **aus dem Code erzeugt**, so wie `BUCH-F2` es für das Manuskript vorsieht. Der Prototyp existiert und läuft. Was dann von Hand gepflegt wird, sind nur noch Begründungen — die Zahlen kommen aus der einzigen Stelle, an der sie ohnehin gelten.

**Meine Empfehlung ist B.** Nicht weil A falsch wäre, sondern weil A schon einmal beschlossen und sechsmal nicht eingehalten wurde. Ein Verfahren, das an Aufmerksamkeit hängt, hat sich in diesem Projekt zweimal als unzuverlässig erwiesen — bei der Spezifikation und beim Manuskript.

---

# TEIL 3 · Alle Punktänderungen auf einen Blick

## 3.1 Änderungen, die die Summe erhöhen

| Herkunft | Kriterium | Heute | Vorschlag | Δ |
|---|---|---|---|---|
| C1 · C2 | P5 `tp_bilder` | 3 | 4 — Dateigröße als eigene Prüfung | **+1** |
| C2 | S3 `si_header` | 3 | 4 — je Header ein Punkt | **+1** |
| C2 | B5 `bf_tastatur` | 1 | 2 — vier Prüfungen brauchen mehr als einen Punkt | **+1** |
| C1 | S4 `si_drittanbieter` | 2 | 3 — Karten als dritter Abzug | **+1** |
| C1 | E3 `se_index` | 3 | 4 — noindex eigenständig | **+1** |
| C1 | E4 `se_schema` | 3 | 4 — Bewertungen eigenständig | **+1** |
| C1 | D5 `dg_mobil` | 1 | 2 — Tap-Targets aufnehmen | **+1** |
| C1 | E1 `se_meta` | 3 | 4 — Ort und Leistung trennen | **+1** |
| | | | **maximal** | **+8** |

## 3.2 Änderungen, die die Summe senken

| Herkunft | Paar | Δ |
|---|---|---|
| C3 | E1 / E5 — Ort im Titel entdoppeln | **−1** |
| C3 | C3 / E5 — Telefonnummer entdoppeln | **−1** |
| C3 | E4 / E5 — Betriebsauszeichnung entdoppeln | **−1** |
| | **maximal** | **−3** |

## 3.3 Änderungen ohne Summenwirkung

**Diese sollten in jedem Fall gemacht werden — sie kosten nichts und beheben echte Fehler.**

| Herkunft | Was | Wirkung |
|---|---|---|
| C1 | 🔴 **`screenreader`-Gruppe an `bf_semantik` anschließen** | `lang`-Attribut und Labels werden endlich gewertet. **Die Daten liegen vor** |
| C1 | 🔴 **`lesbarkeit`-Gruppe an `dg_typografie` anschließen** | Schriftgröße wird gemessen statt geschätzt. **Ein eingeschätztes Kriterium wird zu einem gemessenen** |
| C1 | `bf_semantik` als „gemessen" deklarieren | Katalog und Bericht stimmen überein |
| C1 | `rc_cookie` mit zwei Erhebungsarten führen | beschreibt, was tatsächlich geschieht |
| C2 | 🔴 **Kapitel 8.5 korrigieren** | Das Buch druckt für B2 einen Punktwert, den es nicht gibt |
| C1 | Neun Kriterienhinweise kürzen oder präzisieren | Versprechen und Messung stimmen überein |
| C4 | Spezifikation § 3.1, § 3.2, § 2.4, § 6 nachziehen | eine Wahrheit statt zwei |

> **Die ersten beiden Zeilen sind der wertvollste Fund des ganzen Durchgangs.** Zwei von vier erhobenen Barrierefreiheits-Prüfgruppen werden nicht ausgewertet — und sie enthalten genau die Messungen, die an drei Stellen als „fehlt" geführt werden. **Es ist kein Bauauftrag, es ist ein Anschluss.**

---

# TEIL 4 · Drei Szenarien für die Katalogsumme

## Szenario A — Summe halten: **103**

Alle Abweichungen durch Kürzen der Hinweise, Gewichten statt Erhöhen, Doppelwertungen belassen.

| | |
|---|---|
| Untertitel | unverändert |
| Elektro Hansen | 76 / 103 = **74 · Silber** |
| Manuskriptaufwand | **nur Kapitel 8.5 korrigieren** |
| Was behoben wird | die Deklaration, die Buchtabelle, die Spezifikation |
| Was offen bleibt | zwei tote Stufen, drei Doppelwertungen, neun geschönte Hinweise |

## Szenario B — nur das Kostenlose: **103**

Wie A, **plus** die beiden Lighthouse-Gruppen anschließen.

| | |
|---|---|
| Untertitel | unverändert |
| Elektro Hansen | 76 / 103 = **74 · Silber** — die Punktzahl bleibt, die Messung wird genauer |
| Manuskriptaufwand | Kapitel 8.5 und 8.7 korrigieren, Kapitel 10.6 von Einschätzung auf Messung umstellen |
| Was behoben wird | wie A, **plus** `lang`-Attribut, Labels und Schriftgröße |
| Nebeneffekt | **Ein eingeschätztes Kriterium wird zu einem gemessenen.** Der Anteil sinkt von 17 auf 15 Punkte |
| Was offen bleibt | tote Stufen, Doppelwertungen |

## Szenario C — alles beheben: **108**

+8 aus den erweiterten Prüfungen, −3 aus den entdoppelten.

| | |
|---|---|
| Untertitel | **„39 Kriterien, 8 Kategorien, 108 Punkte"** |
| Elektro Hansen | neu zu erheben — die Kategoriewerte ändern sich in fünf von acht Kategorien |
| Manuskriptaufwand | **acht Kapitel, zwei Anhänge, Satzmuster, beide Kontrollrechnungen** |
| Was behoben wird | alles |
| Risiko | 108 ist eine noch krummere Zahl als 103 — und es wäre die dritte Summe in achtzehn Monaten |

---

# TEIL 5 · Empfehlung

**Szenario B.**

Die Begründung ist keine Geschmacksfrage, sondern eine Rechnung:

**Szenario B behebt die beiden Befunde, die tatsächlich Substanz haben** — dass zwei Barrierefreiheits-Prüfgruppen erhoben und nie gelesen werden, und dass das Buch einen Punktwert druckt, den es nicht gibt. **Beides kostet keine Katalogänderung.**

**Szenario C behebt zusätzlich acht geschönte Hinweise und drei Doppelwertungen — und kostet dafür die dritte Katalogsumme in achtzehn Monaten.** Der Gewinn ist Genauigkeit im Detail. Der Preis ist der Nennwert des Standards.

**Und es gibt einen Grund, C nicht ganz zu verwerfen, sondern zu verschieben:** Drei der vier vermuteten Doppelwertungen, die C3 nicht prüfen konnte, werden erst prüfbar, wenn A8 umgesetzt ist. **Eine Summenänderung heute wäre wieder eine ohne vollständige Grundlage** — genau der Fehler, den Weg 3 vermeiden sollte.

## Vorgeschlagene Reihenfolge

| | Was | Summe |
|---|---|---|
| **1** | Szenario B umsetzen — Anschlüsse, Deklarationen, Hinweise kürzen, Spezifikation nachziehen | **103** |
| **2** | Untertitel bestätigen, ISBN beantragen, `BUCH-F1` und `F2` starten | 103 |
| **3** | A8 umsetzen — Rubrics in den Prompt | 103 |
| **4** | C3 wiederholen, jetzt vollständig prüfbar | 103 |
| **5** | **Fassung 2027.1** — dann alle Punktänderungen zusammen, mit vollständiger Grundlage | offen |

**Damit erscheint das Buch zur Fassung 2026.2 mit 103 Punkten** — der Zahl, die seit dem 11.08. gilt und die die Spezifikation nach dem Nachziehen ebenfalls trägt. Die nächste Summe kommt mit der nächsten Fassung, und dann begründet.

---

## Zu melden

| # | Feststellung |
|---|---|
| 1 | **Sechs Abweichungen zwischen Spezifikation und Code, davon dokumentiert: keine** |
| 2 | Die Gewichtungstabelle stimmt in **sieben von acht** Kategorien exakt |
| 3 | 🔴 **Die Regel „Änderungen erfolgen hier zuerst" wurde in null von sechs Fällen befolgt.** Empfehlung: Spezifikation künftig erzeugen statt pflegen |
| 4 | **Prüfpunkt 5 aus § 9 ist zu einem Drittel erledigt** — zwei Läufe kosten eine Stunde und haben beim ersten Mal fünf Fehler gefunden |
| 5 | **Empfehlung: Szenario B, Katalogsumme bleibt 103** |
| 6 | 🔴 **Der Untertitel ist damit bestätigt: „39 Kriterien, 8 Kategorien, 103 Punkte"** — die ISBN kann beantragt werden |
