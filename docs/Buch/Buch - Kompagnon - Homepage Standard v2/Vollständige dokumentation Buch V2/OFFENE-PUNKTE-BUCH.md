# OFFENE PUNKTE · BUCH

**Stand:** 24.08.2026, nach Block C
**Umfang:** 131 Punkte ohne technische Zuständigkeit, davon 37 rot

| Rolle | Punkte |
|---|---|
| Autor | 35 |
| Lektorat | 34 |
| Gestaltung (Manuel) | 24 |
| Recht | 20 |
| Geschäftsführung | 13 |
| Satz und Produktion | 5 |

> **Was seit Block C feststeht:** Die Katalogsumme bleibt **103**. Der Untertitel ist bestätigt. **Die Sperre auf Manuskriptzahlen ist damit aufgehoben** — alles außer den zehn Punkten in Abschnitt B1 kann anlaufen.

> **Stand 25.08.2026 — B3.1 ist abgearbeitet.** Alle fünf Nachzieh-Punkte aus
> Block C sind erledigt, seit die Software sie eingelöst hat. Dabei kam ein
> eigener Befund heraus: **Rund fünfzig Tabellen im Manuskript trugen den
> Vermerk „ERZEUGT aus `generiert/…` — nicht von Hand ändern".** Diese Dateien
> gab es nie, und kein Skript hat sie geschrieben; die Tabellen waren
> Handarbeit mit einem Schild, das Handarbeit verbot. Zwei Angaben waren
> dadurch nachweislich falsch (B4 „abgeleitet", D2 „Einschätzung"), eine
> dritte veraltet (die Zählung in 3.4). Seit dem 25.08. erzeugt
> `scripts/buch-bloecke.py` die Tabellen, die aus dem Katalog folgen,
> berichtigt den Vermerk bei allen übrigen und **rechnet 32 handgepflegte
> Abstufungstabellen gegen den Katalog nach**. `tests/test_buch_bloecke_aktuell.py`
> hält das fest.

> **Stand 25.08.2026 — das Verfahren ist gegen den Code geprüft.**
> `BEFUND-C5-pruefung-gegen-buchbeschreibung.md` stellt Schritt für Schritt
> gegenüber, wie eine Prüfung tatsächlich läuft und wie das Buch sie
> beschreibt. Ergebnis: **neun Aussagen trafen zu, sechs nicht.** Fünf der
> sechs sind im Manuskript nachgezogen (B3.1.7). Der sechste — **E2 misst
> Überschriften auf der Startseite und Wörter über alle Seiten** — ist keine
> Schreibarbeit, sondern eine Maßstabsfrage und steht als Abschnitt 7 in
> `docs/Audit/fassung-2027-1-offene-massstabsfragen.md`. **Sie muss vor dem
> Druck entschieden werden**, weil Kapitel 13 dem Leser sonst eine Zählung
> beibringt, die von der Messung abweicht.

---

# B1 · Geschäftsführung — **geschlossen**, 13 von 13

> **Diese Liste war bis zum 25.08.2026 nicht nachgeführt.** Sie zeigte dreizehn
> offene Entscheidungen, während `ENTSCHEIDUNGSPROTOKOLL-B1.md` sie am
> **24.08.2026 vollständig getroffen** hatte. Wer nur hier las, hielt den
> Engpass für offen, der es nicht mehr war.

| ID | Entscheidung vom 24.08.2026 |
|---|---|
| **B1.1** | **Umfang akzeptiert.** 284 Seiten; am 25.08. im Satz nachgemessen: **283**. Preisentscheidung dadurch neu offen → B1.15 |
| **B1.2** | **C7 erheben, dann Originaltitel** „Die zwanzig häufigsten Fehler" → macht C7 zum Publikationsblocker, siehe B1.16 |
| **B1.3** | **Eine Domain, drei Pfade** — `/pdf`, `/check`, `/fehler` unter `homepage-standard.de` |
| **B1.4** | **Bei U belassen.** Eine Anleitung für S3 und E4 wäre technischer als alles andere im Buch |
| **B1.5** | **D1-Staffelung gestrichen** — ankreuzen und bewusst schätzen |
| **B1.6** | **Abschnitt 2.7 bleibt unverändert** |
| **B1.7** | **Kapitel 17 ohne Anbieterempfehlung.** Am 25.08. maschinell bestätigt: kein Werbesatz im ganzen Buch (`test_buch_lektoratsregeln`) |
| **B1.8** | **Vorlage 1 auf die Umschlaginnenseite.** Am 25.08. verifiziert: passt auf eine Seite (B6.2) |
| **B1.9** | **Variante A** der Teil-Trennseite |
| **B1.10** | **Keine Widmung**, Titelei sechs Seiten |
| **B1.11** | **PDF-Fassung verbindlich**, nicht optional |
| **B1.12** | **Untertitel** „39 Kriterien, 8 Kategorien, 103 Punkte" |
| **B1.13** | **Zwei ISBN und eigene Verlagsnummer** bei MVB |

## Was aus B1 noch offen ist

| ID | Punkt | Wer |
|---|---|---|
| **B1.15** | 🔴 **Preis neu prüfen** — BoD-Kalkulation für 283 Seiten in beiden Farbvarianten | GF |
| **B1.16** | 🔴 **C7 ist Publikationsblocker.** Die Abfrage steht seit dem 25.08. (`tools/befunde-zaehlen.py`) — **sie findet aber keine Daten:** Grundgesamtheit **1** abgeschlossene Prüfung, jeder der zwanzig Befunde meldet „ohne Zahl". Solange das so bleibt, kann Kapitel 14 seinen Titel nicht tragen, und B1.13 (ISBN) wartet mit | GF / Technik |
| **B1.14a** | 🔴 Domaininhaber muss die **KOMPAGNON communications BP GmbH** sein | GF |
| **B1.14b** | 🔴 Impressum mit der Offenlegung aus 2.7 auf allen drei Seiten | GF / Recht |
| **B1.14c** | 🔴 **Die drei Seiten anlegen** — keine davon existiert | Technik |
| **B1.14d** | Weiterleitungen: `homepagestandard.de` pfaderhaltend 301, die drei Pfade als 302 | Technik |
| **B1.14e** | ✅ **erledigt 25.08.2026** (`automations/job_eigene_zertifikate.py`, täglich 7:30). Die bestehende Überwachung liest `projects` — unsere eigenen Adressen stehen dort nicht. **Der erste Lauf fand sofort etwas:** `homepage-standard.de` und `homepagestandard.de` liefern **kein gültiges Zertifikat**; sie sind gesichert, aber es liegt nichts darauf (siehe B1.14c). `kas.kompagnon.group` ist gültig, 80 Tage Restlaufzeit | Technik |
| **B1.14f** | 🟡 **teilweise — die Aufgabe war so nicht umsetzbar.** Das Buch druckt Adressen **ausschließlich in der Titelei**; Kapitel 2.8 und 13.11 verweisen dorthin, und Kapitel 13 sagt ausdrücklich, mehr technische Adressen kämen im Buch nicht vor. Je Kapitel einen QR-Code zu setzen hieße, diese Regel für eine Kennzahl zu brechen. **Umgesetzt ist, was ohne Regelbruch geht:** Das QR-Ziel trägt `?q=buch` — der Parameter steht im Ziel, nicht in der gedruckten Adresse, die zum Abtippen taugen muss. Damit lässt sich Buchherkunft von anderer unterscheiden, und die drei Pfade sind ohnehin getrennt messbar. **Ob mehr nötig ist, entscheidet die Geschäftsführung** | Technik / GF |

---

# B2 · Recht — 20 Punkte, Anhang D ist die Vorlage

**Vorlauf mehrere Wochen. Ab sofort.**

## Die vierzehn Aussagen

| ID | Zu prüfen |
|---|---|
| **B2.1** | 🔴 Telefonnummer im Impressum — zweiter Kommunikationsweg, ohne Urteilsnachweis |
| **B2.2** | 🔴 Mindestinhalte der Datenschutzerklärung — **die Spezifikation verlangt fünf, der Code prüft drei** |
| **B2.3** | 🔴 **Einwilligungsfeld am Kontaktformular** — der Standard bewertet ein Kriterium, dessen Rechtsgrundlage er selbst als strittig bezeichnet |
| **B2.4** | 🔴 BFSG-Kleinstunternehmen-Ausnahme bei kombiniertem Onlineverkauf |
| **B2.5** | 🔴 **Kammerangabe** — die Spezifikation nennt sie als Pflichtangabe, der Code prüft sie nicht. **Ein Handwerksbetrieb kann 6 von 6 Punkten bekommen, obwohl eine Pflichtangabe fehlt** |
| **B2.6** | 🔴 Energieausweis-Vergleich (2.4) — Verwechslung mit einem hoheitlichen Nachweis |
| **B2.7** | Fremde Server und IP-Übermittlung — bewusst ohne Urteile und Beträge |
| **B2.8** | Abmahnvereine als Prüfer (1.5) — Aussage über Dritte |
| **B2.9** | Barrierefreiheits-Assistenten „umstritten" (8.10) — Aussage über ein käufliches Produkt |
| **B2.10** | 🔴 „Wir garantieren Platz 1" (17.6) — Aussage über einen Berufsstand |
| **B2.11** | Reaktionszeit-Zusage (11.7) — Zusicherung im Wettbewerbsrecht |
| **B2.12** | Foto- und Referenz-Einwilligungen (10.8, 11.8, 16.3) |
| **B2.13** | Vorlage 3 und 4 in Anhang C — Musterkorrespondenz |
| **B2.14** | 🔴 **Vervielfältigungsvorbehalt** — die Titelei erlaubt ausdrücklich das Kopieren der fünf Vorlagen |

## Dazu

| ID | Punkt |
|---|---|
| **B2.15** | 🔴 **Buchpreisbindung** — E-Book-Eigenverkauf über KAS bei gleichzeitiger Verlegerstellung |
| **B2.16** | 🔴 **Rechtsstand** — leeres Feld in Anhang D und in der Titelei, Endkontrolle |
| **B2.17** | Der Fall in 4.1 bleibt anonymisiert — im Haftungsausschluss ausgewiesen |
| **B2.18** | Bußgeld- und Abmahnkostenhöhen bleiben draußen — gegen Ergänzung schützen |
| **B2.19** | Die Liste in 16.3 fachlich gegenlesen lassen — **das einzige größere Buchelement ohne Codegrundlage** |
| **B2.20** | Bibliografische Information der DNB — Formulierung bei der Titelanmeldung |
| **B2.22** | **Unser eigenes Impressum zitierte bis zum 25.08.2026 das aufgehobene TMG** (§ 7 Abs. 1, §§ 8 bis 10). Auf DDG umgestellt, weil ein Impressum mit einem Gesetz, das es nicht mehr gibt, genau der Befund ist, den unser Standard bei Kundenseiten benennt (Kapitel 5.4). **Die Umstellung ist eine Rechtsangabe und gehört bestätigt** — die Haftungsregeln der §§ 7–10 TMG stehen seit dem 14.05.2024 in den §§ 7–10 DDG |
| **B2.21** | **Die fremden Dienste der Prüfung selbst** (C5-6). Abschnitt 16 nennt seit dem 25.08.2026, welche drei Dienste die Prüfung benutzt und was ihnen übermittelt wird: die Adresse der geprüften Seite, der Bildschirmabzug, der Seitentext. Übermittelt wird ausschließlich Öffentliches und nichts von Besuchern — **anwaltlich bestätigen lassen**, dass diese Darstellung genügt, und ob es dafür einer eigenen Angabe in der Datenschutzerklärung von KOMPAGNON bedarf |

---

# B3 · Autor — 35 Punkte

## B3.1 Nachziehen aus Block C — **jetzt möglich**

| ID | Aufgabe | Aus |
|---|---|---|
| **B3.1.1** | ✅ **erledigt 25.08.2026.** Nachgesehen statt angenommen: Sieben der neun Hinweise beschrieb das Manuskript ohnehin richtig — es war der **Katalog**, der zu viel versprach, nicht das Buch. Angepasst wurden die zwei echten Fälle: **L5** (5.8 und die Kategorietabelle nannten den Verweis auf die Datenschutzerklärung, der nicht geprüft wird) und der Selbsttest in 13.2, der ihn abfragte | C1 |
| **B3.1.2** | ✅ **erledigt 25.08.2026.** 8.7 beschreibt jetzt zwei Prüfungen zu je einem Punkt: Gliederung und die Grundlagen für Vorleseprogramme (Sprachauszeichnung, Feldbeschriftungen). Dazu, was „nicht erhoben" hier bedeutet, und die Abgrenzung zu E2 nachgezogen | C1 |
| **B3.1.3** | ✅ **erledigt 25.08.2026.** 10.6 ist ein gemessenes Kriterium: Gemessen wird die Schriftgröße, zwei Punkte oder keine. Zeilenlänge, Zeilenabstand und Schriftanzahl stehen weiter da — jetzt ausdrücklich als das, was sie sind: **nicht bewertet**. Merkkasten, Kategorietabelle und Selbsttestzeile mitgezogen | C1 |
| **B3.1.4** | ✅ **erledigt 25.08.2026.** 3.4 zählt 30 gemessen / 3 abgeleitet / 6 eingeschätzt (81 / 7 / 15 Punkte) — und **die Tabelle wird jetzt erzeugt** statt gepflegt (`scripts/buch-bloecke.py`). Mitgezogen: 3.11, die Merkkästen in 3 und 10, Kapitel 10.2 und das Glossar | C1 |
| **B3.1.5** | 🔴 **Kapitel 9.8 und 11.7** — die als „Vorteil" beschriebenen Doppelwertungen einordnen | C3 |
| **B3.1.7** | ✅ **erledigt 25.08.2026** — **Das Verfahren im Buch trifft jetzt das Verfahren im Code** (`BEFUND-C5`). Fünf von sechs Abweichungen sind geschlossen: **ein** Bildschirmabzug statt zwei (10.2), der ausformulierte Maßstab statt „einer Beschreibung" (10.2), der **Umfang von bis zu 25 Seiten** neu in 3.1 mit der Trennung „über alle Seiten / nur Startseite" (dazu 2.8 und 13.1), die Wiederholbarkeit auf das bezogen, was sie trägt (3.1), und die fremden Dienste der Prüfung selbst benannt (16). Offen bleibt **C5-3** — dazu unten | C5 |
| **B3.1.6** | ✅ **Kapitel 8.5 (B2)** — Kontrasttabelle korrigiert | C2, **erledigt** |

## B3.2 Zahlen und Ketten

| ID | Aufgabe |
|---|---|
| **B3.2.1** | ✅ **nachgerechnet 25.08.2026 — stimmt.** Die Einzelwerte der sechs Kategoriekapitel ergeben 49 (B 6, P 7, D 8, E 11, I 4, C 13), plus Recht 18 und Sicherheit 9 sind es **76 von 103 → 74 → Silber**. Auch die Korrekturtabelle geht auf: 3+2+3+3+1 = 12 Punkte, 76+12 = 88 → 85 → Gold. **Kapitel 5 und 6 tragen als einzige keine eigene Fallzeile** — ihre Werte stehen nur in der Tabelle in 3.10. Wer dort ändert, merkt es nirgends |
| **B3.2.2** | ✅ **nachgerechnet 25.08.2026 — stimmt, aber ein Satz daneben nicht.** Die Kette 76 → 81 → 90 → 93 → 96 ergibt 74 → 79 → 87 → 90 → 93; die Wochengewinne (+5, +9, +3, +3) gehen auf. **Falsch war der Abschluss:** „Bis Platin fehlen sieben Punkte" — sieben ist der Abstand zum **Höchstwert** 103, bis Platin sind es **zwei** (98 Rohpunkte ergeben 95). Auf dieser Zahl stand das ganze Argument, Platin nicht mehr anzustreben. Neu gefasst: Rechnerisch genügte die Barrierefreiheitserklärung allein — sie ohne Prüfung der Erforderlichkeit zu veröffentlichen wäre aber eine Zusage über die eigene Website, die der Betrieb nicht halten kann. `tests/test_buch_bloecke_aktuell.py` rechnet die Kette jetzt bei jedem Lauf nach |
| **B3.2.3** | ✅ **erledigt 25.08.2026.** Die Zeile heißt jetzt „Nachmessung — **erwartet**", und ein Kasten darunter sagt, warum: Ladezeit hängt außerdem am Hoster, am System und an dem, was sonst nachgeladen wird. **Gold steht ohnehin schon nach Woche 2** — Woche 4 entscheidet nur, wie weit darüber hinaus |
| **B3.2.4** | „33 von 39" in 3.11 — bei jeder Änderung der Erhebungsart mitziehen. **Bleibt Handarbeit:** Die Tabelle in 3.4 wird erzeugt, der Satz in 3.11 nicht |
| **B3.2.5** | ✅ **geprüft und abgesichert 25.08.2026.** Alle vier Stellen nennen dieselben Werte (103 / 100 für K4 / 81 für K6), und die Rechnung in 4.5 stimmt: 77 von 81 ergeben 95, also Platin. Die Tabellen in 13.2 und Anhang B werden erzeugt; **der Glossareintrag trägt keine Marke und wird jetzt trotzdem geprüft** — ein Test hält seine Zahlen gegen `anwendbares_maximum()` |

## B3.3 Inhaltliches

| ID | Aufgabe |
|---|---|
| **B3.3.1** | ✅ **erledigt 25.08.2026 — und der Befund lag woanders.** Nachgesehen statt angenommen: **Das Buch war bereits richtig.** Jede TMG-Nennung im Manuskript ist die bewusste Erklärung, dass das Gesetz seit Mai 2024 abgelöst ist — in 5.4, im Glossar und in Anhang D. Falsch war die **Software**: erzeugte Sitemaps, die Homepage-Checkliste, die Kriterienbezeichnung im Auditbericht und unser eigenes Impressum. Alles umgestellt (L-122); die Impressumsänderung steht als B2.22 auf der Anwaltsliste |
| **B3.3.2** | 🔴 **Verweis in Kapitel 12** auf Kapitel 14 — abhängig von B1.2 |
| **B3.3.3** | 🔴 **Fall Elektro Hansen durch einen anonymisierten realen ersetzen** |
| **B3.3.4** | „120 Minuten" im Kapiteltitel 13 — nicht gemessen, zwei Personen durchführen lassen |
| **B3.3.5** | Verweis auf Kapitel 17 in 1.8 und 15.4 bestätigen |
| **B3.3.6** | Verweise auf Kapitel 16 — sechs Stück, alle eingelöst, gegenprüfen |

---

# B4 · Gestaltung — 24 Punkte

## B4.1 Blockierend

| ID | Aufgabe |
|---|---|
| **B4.1.1** | 🔴 **ABB 3.4 Stufenmarken zuerst** — sie kehrt im ganzen Buch wieder. Im Satzmuster bereits umgesetzt |
| **B4.1.2** | **Farbentscheidung bestätigen** — Variante B. **Blockiert nicht mehr:** Das Satzmuster codiert nirgends Information allein über Farbe |
| **B4.1.3** | 🔴 **Satzmuster-Format** — war als A4 deklariert, Raster ist für 170 × 240 gebaut. Korrigierte Fassung liegt vor, **muss übernommen werden** |
| **B4.1.4** | 🔴 **Ergebnisblatt läuft auf zwei Seiten** — verletzt D10, muss heraustrennbar sein |

## B4.2 Fehlende Abbildungen

**Stand: 4 gebrieft, rund 46 geplant.**

| ID | Kapitel | Was fehlt |
|---|---|---|
| **B4.2.1** | 🔴 **10** | Kapitel über visuelle Qualität ohne visuelle Beispiele. Zwei nötig: datiert/zeitgemäß, echt/gekauft. **Kein reales Stockmotiv verwenden** |
| **B4.2.2** | 🔴 **11** | erster Bildschirmausschnitt klar/unklar — **wichtigste Abbildung von Teil II** |
| **B4.2.3** | 🔴 **6** | Seitenaufruf mit fremden Servern — macht das unsichtbare Thema sichtbar |
| **B4.2.4** | 🔴 **14** | Aufwand-Wirkung-Diagramm — natürliche Überleitung zu Kapitel 15 |
| **B4.2.5** | 15 | ABB 15.1 auf `ganz` aufwerten — sie trägt die Schlussaussage |
| **B4.2.6** | 1 | die sieben Fragen als Ablauf — Kandidat für die Umschlaginnenseite |
| **B4.2.7** | 2, 5, 7, 8, 9, 12, 13, 16, 17 | je ein bis zwei Kandidaten, in den Kapiteln benannt |
| **B4.2.8** | — | 🔴 **Gesamtdurchsicht der Abbildungsdichte** statt kapitelweiser Nachbesserung |

## B4.3 Regeln

| ID | Regel |
|---|---|
| **B4.3.1** | Keine Stockfotos, keine fremden Websites, keine fremden Oberflächen |
| **B4.3.2** | Alle Abbildungen schwarzweißfest — Unterscheidung über Form, nie über Farbe |
| **B4.3.3** | Buchsatz hält die eigenen Richtwerte ein: WCAG-Kontrast, Zeilenlänge 60–80 Zeichen |
| **B4.3.4** | Tabellenziffern — im Satzmuster als `tabular-nums` gesetzt ✓ |

---

# B5 · Lektorat — 34 Punkte

## B5.1 Die Schutzliste

**Sechzehn Stellen, an denen das Buch gegen das eigene Interesse argumentiert. Genau sie werden beim Kürzen zuerst gestrichen — und genau sie tragen die Glaubwürdigkeit.**

| Stelle | Was dort steht |
|---|---|
| **2.7** | Der Herausgeber baut selbst Websites — Interessenkonflikt offengelegt |
| **2.8** | „Sie brauchen den Online-Check nicht" |
| **8.6** | Die Lücke bei den Alternativtexten — „nutzen Sie sie nicht aus" |
| **9.2** | Warum die Kategorie von 15 auf 18 Punkte wuchs |
| **9.10** | KI-Systeme auszusperren ist eine legitime Entscheidung |
| **10.2** | Vorbehalt zu den Merkmalslisten — „keine Bewertungsregel" |
| **12 Abschluss** | Der Standard vollständig auf einer Doppelseite |
| **13.11** | „Ersetzen Sie Ihre eigenen Einschätzungen nicht" |
| **14.1** | „Diese Liste ist keine Statistik" |
| **14.7** | „Der teuerste Befund steht nicht auf dieser Liste" |
| **15.7** | Der Plan endet bei Gold und begründet, warum nicht weiter |
| **16.3** | Vollständige Aufzählung dessen, was nicht geprüft wird |
| **17.2** | „Zeitmangel ist kein Anlass zu beauftragen" |
| **17.8** | Der Schluss ohne Ausblick und ohne Aufforderung |
| **D.5** | Keine Bußgeldhöhen, keine Musterformulierungen |
| **1.1 / 15.10** | Die Betriebsmittel-Metapher — Aufstellung und Einlösung gehören zusammen |

## B5.2 Regeln

| ID | Regel |
|---|---|
| **B5.2.1** | Englische Fachbegriffe nur im Glossar als Verweis, nie in Kapitelüberschriften. **Geprüft 25.08.2026:** keine Verstöße. Einziger Grenzfall ist „Online-Check" in der Überschrift 2.8 — ein eingedeutschtes Wort und der Name der kostenlosen Prüfung; **Entscheidung des Lektorats**, nicht maschinell zu klären |
| **B5.2.2** | ✅ **abgesichert 25.08.2026.** Es sind weiterhin genau drei — `llms.txt`, `robots.txt`, `sitemap.xml`. Ein Test schlägt an, sobald ein vierter dazukommt |
| **B5.2.3** | Kein Satz, der eine Leistung des Herausgebers bewirbt — besonders Kapitel 17 |
| **B5.2.4** | ✅ **erledigt 25.08.2026 — und der Verstoß kam nicht aus dem Manuskript.** Anhang B nannte „Lighthouse", eingeschleust über ein **Rubric im Katalog** (`dg_farbsystem`): Der Export druckt die Rubrics, seit BUCH-F1 die Abstufungen erzeugt werden. An der Quelle behoben, Anhang neu erzeugt. **Die Regel gilt jetzt auch dort, wo Text entsteht** — ein Test prüft alle Kapitel und Anhänge, mit einer Ausnahme für das Glossar, das die Begriffe als Verweise führen soll |
| **B5.2.5** | ✅ **abgesichert 25.08.2026.** Keine gefunden. Ein Test sucht künftig nach dem Muster „NN % … Absprung/Abbruch/verlassen" — die verbreitetste unbelegte Zahl der Branche |
| **B5.2.6** | Die Offenlegung steht mehrfach — das ist Absicht. **Gezählt am 25.08.2026: vier Stellen** (Kapitel 1, 2, 17 und die Titelei), die Regel nennt drei. **Zu klären, welche gemeint sind**; der Test hält bis dahin die Untergrenze von drei fest, damit beim Kürzen keine verschwindet |

## B5.3 Zu entscheiden

| ID | Punkt |
|---|---|
| **B5.3.1** | Der Kasten „Wenn Sie nur zehn Minuten haben" in der Titelei — trägt er oder wirkt er werblich? |
| **B5.3.2** | Fachbegriffe LCP, CLS, INP in einer Marginalie? Wer selbst misst, sieht sie im Werkzeug |
| **B5.3.3** | Klassentabellen erscheinen in Kapitel 11 fünfmal — Ausklapptafel oder Wiederholung im Anhang? |
| **B5.3.4** | Trägt der Abgrenzungsabsatz in 2.12 / 3.9 zu E7? |
| **B5.3.5** | HSTS-Warnung in 6.6 — soll abschrecken, nicht lähmen |
| **B5.3.6** | Ausfüllfeld „Nächster Prüftermin" steht dreimal — Dopplung oder Absicht? |
| **B5.3.7** | Kapitel 5 hat 22 Seiten und eine Abbildung — beim Kürzen 5.10 vor 5.2 |
| **B5.3.8** | Sicherheitsheader bei technischem Namen nennen oder umschreiben? |

---

# B6 · Satz und Produktion — 5 Punkte

| ID | Aufgabe |
|---|---|
| **B6.1** | 🔴 **Vorlage 3 bekommt keine Passwortfelder** — Anweisung steht im Dateikommentar |
| **B6.2** | ✅ **verifiziert und hergestellt 25.08.2026.** Gemessen statt geschätzt: Im Fließtextsatz brauchte Vorlage 1 **2,3 Seiten**. Nicht der Inhalt war schuld — er belegt 484 von 539 Punkt —, sondern der Luftraum zwischen den Blöcken. Mit einem eigenen **Formularsatz** (kleinere Grundschrift, halbierte Abstände, Ausfülllinien zählen nicht mit ihrer vollen Länge für die Spaltenbreite) passen **Vorlage 1, 2 und 3 auf je eine Seite**. **Dabei ein zweiter Befund, schwerwiegender als der erste:** Die 89 Ankreuzkästchen des Buchs waren **unsichtbar**. Noto Sans enthält weder `☐` noch ein anderes Kästchenzeichen, und ReportLab verschluckt fehlende Zeichen stillschweigend. Sie werden jetzt gezeichnet — so wie das Satzmuster seine Stufenmarken zeichnet |
| **B6.3** | BoD-Format 17 × 24 cm prüfen, sonst 17 × 22 |
| **B6.4** | Schriftlizenz ✓ **Noto ist SIL Open Font License** — Print und EPUB erlaubt |
| **B6.5** | Seitenzahl auf ein Vielfaches von 4, danach Rückenbreite |
| **B6.6** | Seitenzählung der Titelei: römisch oder arabisch |

---

# Reihenfolge

```
B1  Geschäftsführung        ← heute, 13 Entscheidungen, null Aufwand
B2  Anwaltstermin           ← ab sofort parallel, Anhang D mitschicken
B4.1 Manuel: Stufenmarken, Format, Ergebnisblatt   ← parallel
        ▼
B3.1 Nachziehen aus Block C ← sobald S1 bis S3 im Repo sind
        ▼
B4.2 Abbildungen            ← nach B1.1, weil der Umfang die Zahl bestimmt
        ▼
B5  Lektorat mit Schutzliste
        ▼
B6  Satz und Produktion
```

**Der Engpass ist B1.** Dreizehn Entscheidungen, null Arbeitszeit — und sie bestimmen den Umfang, die ISBN, den Satzbeginn und wie viele Abbildungen Manuel zeichnen muss.
