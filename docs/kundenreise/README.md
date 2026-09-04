# Die Kundenreise — vom ersten Kontakt bis zum laufenden Abo

> **Stand:** 2026-09-04 · Bildschirmfassung: `kundenreise.html`
> (Artefakt `82060c9c-ca26-4018-9459-a6817c3f5288`)
>
> **Aufbau nach der Vorlage „Customer Journey Layers"** mit zwei bewussten
> Abweichungen, beide unten begründet.
>
> **Die Berührungspunkte sind am System abgelesen, nicht entworfen.** Wer einen
> vermisst, prüft am Code — nicht an dieser Liste.

---

## Die fünf Stufen und ihre 38 Berührungspunkte

| Stufe | Dauer | Berührungspunkte |
|---|---|---:|
| **Aufmerksamkeit** — wir finden den Betrieb | Tage bis Wochen | 5 |
| **Erwägung** — er prüft uns | 1–14 Tage | 7 |
| **Kauf** — er entscheidet | Minuten | 7 |
| **Bau** — wir liefern | 14 Kalendertage zugesagt | 11 |
| **Betreuung** — es läuft weiter | 12 Monate, dann monatlich | 8 |

**Aufmerksamkeit:** HWK-Register · Domain-Import · Analyse-Widget auf fremder
Seite · Landingpage · Kaltakquise-Mail

**Erwägung:** Widget-Formular · Bestätigungsmail · Bericht im Browser ·
PDF-Bericht · Erstgespräch · Angebot · Verkaufsseite

**Kauf:** Paketseite · Stripe-Kasse · Zahlung · Auftragsbestätigung ·
Zugangsdaten-Mail · erste Anmeldung · Kundenkonto

**Bau:** Mitwirkungsliste · Erinnerungsmail · Positionierungsgespräch ·
Briefing · Bauplan · Entwurfsfreigabe · Textfreigabe · Auslieferung · Domain
und Zertifikat · Go-live-Mail · Schlussrechnung

**Betreuung:** Änderung anfordern · Guthaben · Monatsbericht · Re-Audit ·
Support-Ticket · Monatsrechnung · KI-Sichtbarkeit · Akademie

---

## Zwei Abweichungen von der Vorlage

**Aus „Abteilungen" wurden Module.** Ein Betrieb mit einem Entwickler hat keine
acht Abteilungen. Die ehrliche Entsprechung sind die elf Fachmodule
(`docs/module-karte.md`) — und die Matrix leistet dasselbe: Wo mehrere
gleichzeitig beteiligt sind, ist die Reise am anfälligsten. Beim Bau sind es
sechs.

**Die Stufenfarbe ist eine Abstufung, keine Kategorie.** Fünf gleichrangige
Farben bestanden die Prüfung auf Farbfehlsichtigkeit nicht — worst adjacent
ΔE 1,8 bei Deuteranopie. Das war kein Farbproblem, sondern ein Hinweis auf die
Form: **Eine Reise ist eine Reihenfolge.** Also eine monotone Abstufung von
dunkel nach hell; die Textfarbe wechselt ab Stufe 4 auf Schwarz, weil Weiß
dort 3,19:1 erreicht und damit unter AA liegt.

---

## Was die Erlebniskurve zeigt

**Die beiden tiefsten Punkte liegen beide nach dem Kauf.**

| | Punkt | Beleg |
|---|---|---|
| 🔴 | „Materialien fehlen" — eine Mahnung, die nicht sagt, welche | `job_check_missing_materials`; behoben durch L-159 |
| 🔴 | Zwölf bezahlte Abo-Leistungen sind im Konto unsichtbar | `docs/kundenkonto-soll-ist.md` § 2.1 |
| 🟠 | Drei falsche Befunde im Bericht (Preis, Zukunftsdatum, Alt-Texte) | Fremdrückmeldung 04.09., behoben L-150/L-152 |
| 🟠 | Das Konto ist leer — sieben von acht Seiten kürzer als ein Absatz | Krug-Prüfung § 5.5 |
| 🟠 | Die Akademie steht im Menü und ist leer | L-60 |
| 🟠 | Beim Merge nach produktiv rund 40 Sekunden Ausfall | bewusst gewählt, L-94 |
| 🟢 | Der Bericht ist strukturiert und verständlich | Wortlaut der Fremdrückmeldung |
| 🟢 | Die Anmeldeseite erklärt, woher die Zugangsdaten kommen | Krug-Prüfung, `ux-soll-ist-kas.md` Reise C |

> **Der Befund der ganzen Darstellung in einem Satz:** Die Reise ist **vor**
> dem Kauf am besten ausgebaut und **danach** am dünnsten — bei einem Produkt,
> dessen Ertrag im Abo liegt.

---

## Wo nichts aufgezeichnet wird

Zwei Löcher über die gesamte Reise:

* **Das Verhalten auf der erzeugten Kundenwebsite** — der Umami-Plan liegt seit
  dem 30.04.2026 und ist nie gebaut worden (L-142).
* **Das Verhalten im Kundenkonto** — gewünscht am 27.08. (L-143).

Wir wissen also nicht, was der Kunde tut, sondern nur, was er auslöst.

**Und die Mailspur liegt doppelt:** `email_logs` und `communications` kennen
einander nicht — deshalb wurde zweimal der falsche Absender beschuldigt.

---

## Die Reibungskarte (04.09.2026)

`reibungskarte.html` — dieselben 38 Berührungspunkte, aber **nicht zum
Vorzeigen**. Wunsch David: „ich will, dass wir diese Darstellung nutzen um
evtl. Konflikte oder Lücken zu identifizieren an denen wir lernen können wo es
noch hängt."

**Was sie anders macht.** Jeder Punkt trägt einen Zustand, der gemessen ist:

| Zustand | Bedeutung | gezählt am 04.09. |
|---|---|---|
| trägt | am laufenden System nachgesehen | 23 |
| hängt | gebaut, mit benanntem Vorbehalt | 14 |
| fehlt | im Code nicht auffindbar | 1 |

**Der eigentliche Inhalt sind die acht Konflikte.** Ein Konflikt ist hier
nicht „etwas ist kaputt", sondern: **zwei Aussagen, die nicht beide wahr sein
können** — eine aus einem Vertrag oder Datenblatt, eine aus dem laufenden
System. Jeder nennt beide Quellen und endet mit der Frage, die sich nicht
wegprogrammieren lässt. Zwei davon kosten unmittelbar Geld (K1 die
Garantieschwelle, K2 die 28,31 € Differenz je Kunde und Monat).

**Dazu zwei Listen, die eine Reisekarte sonst verschweigt:** wo der Kunde
wartet, ohne dass etwas Sichtbares geschieht (vier Stellen, zwei davon am
04.09. geschlossen) — und die **blinden Flecken**: vier Fragen, die diese
Karte nicht beantworten kann, weil die Zahl dahinter nirgends entsteht. Wie
viele im Widget abbrechen. Wie lange ein Bau wirklich dauert. Wer sein Konto
öffnet. Warum jemand kündigt.

> **Warum die blinden Flecken dazugehören.** Eine Reisekarte, die nur zeigt,
> was gebaut ist, bestätigt den Stand. Eine, die benennt, was sie **nicht**
> weiß, sagt, wo die nächste Messung hingehört.
