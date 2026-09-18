---
kapitel: 14
teil: "III — Anwendung"
titel: "Zwanzig Befunde, die wiederkehren"
titel_konzept: "Die zwanzig häufigsten Fehler"
titel_wechselt_wenn: "Anteile je Befund aus tools/befunde-zaehlen.py eingetragen"
autor: "Manuel Potter"
status: entwurf
zuletzt_geprueft: 2026-08-31
standard_version: "2026.2"
zielumfang: 12 Seiten
---

<!-- KAPITELÖFFNER — rechte Seite -->

# 14

# Zwanzig Befunde, die wiederkehren

> Zwanzig Dinge, die bei Betriebswebsites immer wieder auftauchen — sortiert nicht danach, wie viele Punkte sie kosten, sondern danach, wie viel es kostet, sie zu beheben. Vier davon deckeln Ihre Stufe unabhängig von allem anderen.

<!-- SEITENUMBRUCH -->

<!-- TITEL: Entschieden am 24.08.2026, ausgeführt am 31.08.2026 (Entscheidung
     David). Der Originaltitel „Die zwanzig häufigsten Fehler" gilt, sobald die
     Anteile je Befund aus der Erhebung eingetragen sind — der Methodenteil
     unten steht bereits in seiner endgültigen Form. Was noch fehlt, ist ein
     einziger Lauf: `python3 tools/befunde-zaehlen.py` am Produktivdienst.
     Bis die Zahlen stehen, bleibt der vorläufige Titel — ein Kapitel, das
     „häufigsten" heißt und die Häufigkeit schuldig bleibt, wäre genau der
     Fehler, den dieses Buch anderen vorhält. -->

## 14.1 Woher diese zwanzig kommen

**Sie sind erhoben, nicht geschätzt.** Grundlage sind **zwanzig auswertbare Prüfungen** vom 16. bis 28. August 2026, sämtlich nach Fassung `2026.2` des Standards. Auswertbar heißt: Die Prüfung trägt tatsächlich bewertete Kriterien. Zeilen, die nur den Vermerk „abgeschlossen" tragen, sind nicht mitgezählt — sie sahen lange wie eine Grundgesamtheit aus und waren keine.

**Der Nenner ist je Befund ein anderer, und das ist Absicht.** Fällt bei einer Prüfung das tragende Kriterium aus — weil eine Seite den Zugriff sperrt, weil ein Messwert nicht zustande kommt —, dann ist der Befund dort *nicht erhoben*, nicht *nicht vorhanden*. Wer durch alle zwanzig teilt, zählt jede ausgefallene Messung als bestanden und rechnet sich das Ergebnis schön. Elf der zwanzig Befunde stehen deshalb auf n = 20, sieben auf n = 15 bis 19.

**Zwei Befunde haben keine Zahl und können keine bekommen.** Nummer 5 (Jahreszahl im Fußbereich) und Nummer 10 (wann Sie antworten) werden von keinem Kriterium des Katalogs allein getragen. Sie stehen hier aus der Prüfpraxis, ausdrücklich ohne Anteil. Ein weiterer Lauf ändert daran nichts.

**Zur Herkunft der geprüften Seiten.** Es sind Betriebe aus dem eigenen Bestand, und der ist eine Nische: Von den offenen Betrieben fallen 52 in Branchenklasse K1 und 6 in K4. **K2, K3, K5 und K6 kommen nicht vor.** Wer diese Zahlen auf einen Steuerberater oder eine Arztpraxis überträgt, überträgt sie auf eine Klasse, in der nicht gemessen wurde.

**Sechs von sechsundzwanzig Anläufen scheiterten** — drei Seiten sperrten den Prüfer aus, drei waren nicht erreichbar. Das ist der übliche Anteil bei fremden Websites und keine Eigenschaft dieser Erhebung.

**Sortiert ist die Liste trotzdem nicht nach Häufigkeit, sondern nach Aufwand.** Das ist der eigentliche Wert dieses Kapitels. Der Befund mit den meisten Punkten ist nicht der, mit dem man anfängt. Kapitel 15 baut daraus einen Plan.

::: MRG
**Ehrlich gesagt**
Zwanzig Prüfungen sind die Untergrenze, ab der ein Anteil mehr ist als eine Anekdote — nicht eine große Zahl. Und sie stammen aus einer Branchenklasse.
:::

> **Warum das hier steht.** Ein Buch, das einen Maßstab setzt, darf keine Zahl behaupten, die es nicht erhoben hat — und keine erhobene Zahl ohne ihre Grenzen zeigen. Grundgesamtheit, Zeitraum, Fassung und Klassenverteilung stehen deshalb oben und nicht in einer Fußnote.

---

## 14.2 Vier Befunde, die alles andere blockieren

Diese vier begrenzen Ihre Stufe unabhängig von Ihrer Punktzahl. **Solange einer davon zutrifft, ist jede andere Verbesserung Kosmetik.**

### 1 · Das Impressum ist verlinkt, aber nicht erreichbar

**L1 — 6 Punkte · Stufe: Nicht konform · Kapitel 5.4**

Im Fußbereich steht „Impressum". Der Verweis führt auf eine Seite, die es nicht mehr gibt — weil sie beim letzten Umbau umbenannt wurde, weil eine Unterseite gelöscht wurde, weil das System die Adresse geändert hat.

**Warum es niemand merkt:** Niemand klickt auf das eigene Impressum. Der Verweis ist da, also gilt die Sache als erledigt.

**Prüfen:** Klicken Sie darauf. Jetzt.

### 2 · Die Datenschutzerklärung fehlt oder ist nicht erreichbar

**L2 — 6 Punkte · Stufe: Nicht konform · Kapitel 5.5**

Dieselbe Ursache wie bei Nummer 1, dazu ein zweiter Fall: Sie ist im Impressum als Absatz untergebracht statt als eigene, verlinkte Seite.

### 3 · Das Zertifikat ist abgelaufen

**S1 — 3 Punkte · Stufe: Nicht konform · Kapitel 6.4**

Die automatische Erneuerung hat versagt. Der Browser warnt jeden Besucher, bevor er die Seite sieht.

**Warum es niemand merkt:** Die Ablaufwarnung geht an eine Mailadresse, die seit dem Agenturwechsel niemand mehr öffnet.

**Das ist der einzige Befund dieser Liste, der Ihre Website praktisch unbenutzbar macht** — und er tritt ohne Vorwarnung ein.

### 4 · Fremde Dienste laden, bevor eingewilligt wurde

**L3 — 4 Punkte · Stufe: höchstens Bronze · Kapitel 5.6**

Ein Einwilligungsbanner erscheint, und im Hintergrund läuft das Statistikwerkzeug bereits. Oder: Es gibt gar kein Banner, aber Schriftarten und Karten laden von fremden Servern.

**Warum es niemand merkt:** Das Banner ist da. Dass es nichts verhindert, sieht man ihm nicht an.

---

## 14.3 Sechs Befunde, die unter einer Stunde kosten

Zusammen bis zu **acht Punkte** — ohne fremde Hilfe, ohne Kosten.

### 5 · Die Jahreszahl im Fußbereich ist veraltet

**I2 — 1 Punkt, wirkt zusätzlich auf D1 · Kapitel 12.5**

Sie wurde einmal fest eingetragen. Niemand sieht in den Fußbereich der eigenen Website.

**Wirkung über die Punkte hinaus:** Ein Besucher, der 2019 liest, fragt sich, ob es den Betrieb noch gibt. Das ist der billigste Vertrauensschaden, den man haben kann.

**Aufwand:** unter einer Minute — und bei den meisten Systemen einmalig, weil sich die Zahl fortschreiben lässt.

### 6 · Ein Verweis im Fußbereich führt ins Leere

**E6 — 1 Punkt · Kapitel 9.9**

Meist auf einen Verband, einen Lieferanten oder ein Portal, das es nicht mehr gibt.

**Aufwand:** zehn Minuten. Alle Verweise der Startseite einmal anklicken.

### 7 · KI-Systeme sind ausgesperrt

**E7 — 2 Punkte · Kapitel 9.10**

In der `robots.txt` steht ein Block, der GPTBot, ClaudeBot oder ähnliche mit `Disallow: /` von der ganzen Seite ausschließt. Meist vor Jahren eingetragen, als das als vorsichtig galt.

**Wirkung über die Punkte hinaus:** Wer ein KI-System nach einem Betrieb Ihrer Art fragt, bekommt Sie nicht genannt. Sie existieren für dieses System nicht.

**Aufwand:** zwei Zeilen löschen — **wenn Sie das wollen.** Abschnitt 9.10 sagt ausdrücklich, dass es gute Gründe für die Sperre gibt.

### 8 · Es gibt keine Beschreibungsdatei für Maschinen

**E7 — 1 Punkt · Kapitel 9.10**

Eine `llms.txt` im Wurzelverzeichnis: wenige Zeilen darüber, was Ihr Betrieb tut, wo er arbeitet, wie man ihn erreicht.

**Warum dieser Befund besonders ist:** Die allerwenigsten Websites haben eine. Es ist einer der wenigen Punkte, bei denen Sie den meisten Mitbewerbern voraus sein können, statt aufzuholen.

**Aufwand:** zwanzig Minuten, wenn Sie wissen, wie man eine Datei hochlädt.

### 9 · Die Telefonnummer ist nicht anklickbar

**E5 und C3 — bis 2 Punkte · Kapitel 9.8 und 11.7**

Sie steht als Text auf der Seite. Auf einem Telefon lässt sie sich nicht wählen — der Besucher müsste sie abschreiben.

**Wirkung über die Punkte hinaus:** Bei einem Handwerksbetrieb ist der Anruf die häufigste Reaktion. Dieser Befund steht ihr im Weg.

**Aufwand:** wenige Zeichen je Nummer. **Wirkt auf zwei Kriterien in zwei Kategorien.**

### 10 · Es ist nicht gesagt, wann Sie antworten

**C3 — 1 Punkt · Kapitel 11.7**

Ein Satz fehlt: „Wir melden uns innerhalb von 24 Stunden."

**Wirkung über die Punkte hinaus:** Er nimmt dem Besucher die Ungewissheit — und er verpflichtet Sie, was genau der Grund für seine Wirkung ist. **Sagen Sie nur zu, was Sie halten.**

**Aufwand:** fünf Minuten.

::: MRG
**Zusammen unter einer Stunde**
Befunde 5 bis 10 kosten zusammen etwa eine Stunde und bringen bis zu 8 Punkte.
:::

---

## 14.4 Sechs Befunde, die einen halben bis ganzen Tag kosten

Zusammen bis zu **achtzehn Punkte** — der größte Hebel dieser Liste.

### 11 · Das Kopfbild ist unkomprimiert

**P1, P4 und P5 — bis 8 Punkte · Kapitel 7.5 und 7.9**

Ein Foto direkt aus der Kamera, ein bis zwei Megabyte, im Kopfbereich der Startseite. Der Besucher sieht drei Sekunden lang eine leere Fläche.

**Warum es niemand merkt:** Bei Ihnen liegt das Bild im Zwischenspeicher. Sie warten nie.

**Das ist der Befund mit der größten Wirkung dieser ganzen Liste**, weil er auf drei Kriterien gleichzeitig wirkt.

**Aufwand:** eine Stunde für alle Bilder der Seite, mit einem kostenlosen Komprimierungswerkzeug.

### 12 · Die Alternativtexte der Bilder fehlen

**B3 — 2 Punkte, wirkt zusätzlich auf B1 · Kapitel 8.6**

Das Feld ist beim Hochladen vorhanden und wird übersprungen.

**Achtung bei der Behebung:** Der Dateiname als Alternativtext bringt zwar Punkte, verbessert aber nichts. Abschnitt 8.6 zeigt, wie ein brauchbarer aussieht — und dass dekorative Bilder eine **leere** Alternative bekommen.

**Aufwand:** etwa eine Stunde bei fünfzig Bildern.

### 13 · Schriftarten laden von einem fremden Server

**S4 — 1 Punkt, wirkt zusätzlich auf P1 · Kapitel 6.7**

Der häufigste Befund der Kategorie Sicherheit — und der, der die meisten Betriebe überrascht. Eine Schriftart ist Gestaltung; dass sie eine datenschutzrechtliche Frage aufwirft, erschließt sich niemandem von selbst.

**Warum ein Einwilligungswerkzeug hier nicht hilft:** Schriften stecken im Gestaltungsteil, nicht im Statistikbereich. Das Werkzeug kennt sie nicht.

**Aufwand:** eine halbe Stunde. **Verbessert nebenbei die Ladezeit.**

### 14 · Steuerdatei oder Übersichtsdatei fehlen

**E3 — bis 2 Punkte · Kapitel 9.6**

Und im schlimmsten Fall enthält die Steuerdatei noch die Sperre aus der Entwicklungszeit — dann ist Ihre Website für Suchmaschinen nicht vorhanden.

**Das ist der einzige Befund dieser Liste, der nur einen Punkt kostet und trotzdem existenziell ist.**

**Prüfen:** `ihre-domain.de/robots.txt` aufrufen. Steht dort `Disallow: /` unter `User-agent: *`, ist Ihre Seite ausgesperrt.

**Aufwand:** eine Zeile löschen, eine Erweiterung aktivieren.

### 15 · Es gibt keine strukturierten Daten

**E4 — 3 Punkte, wirkt zusätzlich auf E5 · Kapitel 9.7**

Ein unsichtbarer Textblock, der maschinenlesbar beschreibt, was Ihr Betrieb ist. Ohne ihn muss jede Maschine raten.

**Ein Nebeneffekt, den Abschnitt 9.8 beschreibt:** Die Betriebsauszeichnung erfüllt zugleich eine Prüfung bei E5 — und erspart Ihnen die eingebettete Karte, die bei S4 einen Punkt kostet. **Ein Handgriff, drei Wirkungen.**

**Aufwand:** ein halber Tag, oder eine Erweiterung im Redaktionssystem.

### 16 · Die Nachweise sind da, aber nicht sichtbar

**C4 — 1 bis 2 Punkte · Kapitel 11.8**

Meisterbrief, Innungsmitgliedschaft, Zertifizierungen, Herstellerpartnerschaften — vorhanden, aber nirgends auf der Website.

**Warum es niemand merkt:** Für Sie ist es selbstverständlich. Für einen Besucher ist es der Unterschied zwischen einer Behauptung und einem Beleg.

**Aufwand:** ein halber Tag, inklusive Fotografieren und Einwilligungen.

---

## 14.5 Vier Befunde, die eine Entscheidung brauchen

Diese vier kann Ihnen niemand abnehmen — auch keine Agentur. Sie kosten keine Arbeitszeit, sondern eine Festlegung.

### 17 · Alle Leistungen stehen auf einer Sammelseite

**I1 — 2 Punkte, wirkt zusätzlich auf E1 · Kapitel 12.4**

**Die Entscheidung:** Welche drei Leistungen sind Ihnen wichtig genug für eine eigene Seite? Nicht die, über die Sie am meisten schreiben können — die, die Ihnen die besten Aufträge bringen.

### 18 · Es gibt keinen Preisrahmen und keine Kostenlogik

**C5 — 1 bis 2 Punkte · Kapitel 11.9**

**Die Entscheidung:** Wie viel sagen Sie über Ihre Preise, bevor jemand anruft?

Der übliche Einwand — jedes Objekt ist anders — stimmt und ist keine Antwort. Ein Besucher will keinen Festpreis, er will wissen, ob er in der richtigen Größenordnung ist. Abschnitt 11.9 zeigt vier Wege, das zu sagen, ohne sich festzulegen.

**Ein Nebeneffekt, den viele unterschätzen:** Eine genannte Untergrenze spart Ihnen die Anfragen, die ohnehin nicht zu Aufträgen geführt hätten.

### 19 · Zwischen echten Fotos stehen gekaufte

**D4 — 1 Punkt, wirkt zusätzlich auf C4 · Kapitel 10.8**

**Die Entscheidung:** Löschen oder ersetzen.

**Warum das eine Entscheidung ist und keine Aufgabe:** Es fühlt sich falsch an, ein professionelles Motiv gegen ein Telefonfoto zu tauschen. Es ist trotzdem richtig — **die gekauften Bilder entwerten die echten daneben.** Ein Besucher, der eines als gekauft erkennt, überträgt den Zweifel auf alle übrigen Inhalte.

### 20 · Die Texte beschreiben den Betrieb statt das Anliegen

**I3 — 1 bis 2 Punkte · Kapitel 12.6**

„Wir verfügen über langjährige Erfahrung" statt „Im Altbau finden wir fast immer Leitungen, die nicht in den Plänen stehen."

**Die Entscheidung:** Welche Fragen sollen Ihre Texte beantworten?

**Die Abkürzung:** Schreiben Sie die fünf Fragen auf, die Ihnen am Telefon am häufigsten gestellt werden. Beantworten Sie sie schriftlich, so wie Sie es am Telefon täten. **Sie sind die einzige Person, die diese fünf Fragen kennt** — kein Texter kann das für Sie erledigen.

---

## 14.6 Was auffällig oft zusammen auftritt

Dies sind Beobachtungen aus der Prüfpraxis, keine gemessenen Zusammenhänge. Sie sind trotzdem nützlich, weil sie Ihnen sagen, wo Sie als Nächstes nachsehen sollten.

| Wenn Sie das finden | Sehen Sie auch hier nach |
|---|---|
| Veraltete Jahreszahl (5) | tote Verweise (6), fehlende Datierung überall |
| Unkomprimiertes Kopfbild (11) | fehlende Alternativtexte (12), fehlende Größenangaben |
| Fremde Schriftarten (13) | eingebettete Karte, eingebettetes Video — dieselbe Ursache |
| Sammelseite statt Leistungsseiten (17) | derselbe Seitentitel auf allen Unterseiten (E1) |
| Gekaufte Bilder (19) | fehlende Nachweise (16) — beides deutet auf eine Website, die niemand pflegt |
| Keine strukturierten Daten (15) | keine Übersichtsdatei (14), keine Kanonisierung |

**Das Muster dahinter ist fast immer dasselbe:** Eine Website wurde einmal gebaut und seither nicht mehr angefasst. Die Befunde sind keine Einzelfehler, sondern Alterserscheinungen — und deshalb treten sie in Gruppen auf.

---

## 14.7 Der teuerste Befund steht nicht auf dieser Liste

Zwanzig Befunde, bis zu vierzig Punkte, und trotzdem fehlt der wichtigste.

**Eine Website kann alle zwanzig Befunde beheben, 95 Punkte erreichen — und trotzdem keine einzige Anfrage bringen, weil niemand sie kennt.**

Der Standard misst den Zustand Ihrer Website. Er misst nicht, ob Sie gefunden werden, ob Sie empfohlen werden, ob Ihr Angebot am Markt trägt. Abschnitt 2.3 hat es gesagt, und es gehört an dieser Stelle wiederholt, weil hier die Versuchung am größten ist, die Liste für vollständig zu halten.

**Was Ihnen die zwanzig Befunde geben, ist eine Gewissheit — keine Garantie:** Wenn eine Anfrage ausbleibt, liegt es nicht an Ihrer Website.

Das ist weniger, als eine Liste dieser Art gern verspricht. Es ist trotzdem viel: Sie können eine Ursache ausschließen und sich den übrigen zuwenden.

---

## Das Wichtigste aus diesem Kapitel

> - **Diese Liste ist eine begründete Auswahl, keine Statistik.** Sie behauptet keine Rangfolge.
> - **Vier Befunde deckeln Ihre Stufe unabhängig von allem anderen.** Solange einer zutrifft, ist jede andere Verbesserung Kosmetik.
> - **Sechs Befunde kosten zusammen unter einer Stunde** und bringen bis zu acht Punkte.
> - **Das unkomprimierte Kopfbild ist der größte Einzelhebel** — es wirkt auf drei Kriterien gleichzeitig.
> - **Vier Befunde sind Entscheidungen, keine Aufgaben.** Preisrahmen, Leistungsseiten, Bildwahl, Textausrichtung — das kann keine Agentur für Sie festlegen.
> - **Befunde treten in Gruppen auf**, weil sie Alterserscheinungen sind und keine Einzelfehler.
> - **Der teuerste Befund steht nicht auf der Liste:** eine gute Website, die niemand kennt.

---

<!-- REDAKTIONELLE ANMERKUNGEN — NICHT DRUCKEN -->

## Offene Punkte zu Kapitel 14

| # | Punkt | Wer | Status |
|---|---|---|---|
| 1 | ⚠️ **ENTSCHIEDEN 24.08.2026 (B1.2): C7 wird erhoben, danach kehrt der Originaltitel „Die zwanzig häufigsten Fehler" zurück.** Damit wird C7 zum **Publikationsblocker** — solange die Häufigkeit nicht erhoben ist, kann das Kapitel den Titel nicht tragen. Bis dahin gilt der Arbeitstitel. Ursprünglicher Befund: **Kapiteltitel geändert.** Das Buchkonzept sah „Die zwanzig häufigsten Fehler" vor. **Die Häufigkeit ist nicht erhoben** — der Restarbeiten-Report führt sie als C7 mit dem Vermerk, sie aus den vorliegenden Prüfungen zu gewinnen. Solange das nicht geschehen ist, wäre der ursprüngliche Titel eine Behauptung ohne Grundlage, und zwar auf einer Kapitelüberschrift. Der Entwurf heißt deshalb **„Zwanzig Befunde, die wiederkehren"**, und Abschnitt 14.1 sagt ausdrücklich, dass es keine Statistik ist. **Entscheidung der Geschäftsführung:** Titel so lassen, oder C7 vor Drucklegung erheben und den Originaltitel zurückholen | GF | **🔴 offen** |
| 2 | 🔴 **Folgeänderung in Kapitel 12.** Der Abschluss von Teil II verweist auf „Kapitel 14 fasst zusammen, welche Befunde in der Praxis am häufigsten sind". Dieser Satz muss mitgeändert werden. **Ebenso das Inhaltsverzeichnis und Abschnitt 1.8, falls dort verwiesen wird** | Autor | **einzupflegen** |
| 3 | 🔴 **C7 ist jetzt Publikationsblocker (B1.2)** und zugleich der wertvollste Teil des ganzen Buchs. Sobald eine Auswertung der geprüften Websites vorliegt — mit Grundgesamtheit und Erhebungszeitraum —, wird aus dieser Auswahl eine Erhebung, die außer dem Herausgeber niemand hat. Für die Presse- und Kammerarbeit ist das mehr wert als das übrige Buch. **Nach BUCH-F2 ist die Auswertung eine Abfrage, keine Auswertungsarbeit** | Technik / GF | **empfohlen** |
| 4 | ✅ **TEILWEISE ERLEDIGT 24.08.2026** — Konsistenzprüfung gegen Kapitel 15 durchgeführt. **Ein Widerspruch gefunden und behoben:** Kapitel 14 nannte „etwa 45 Minuten" für die Befunde 5 bis 10, die Einzelposten in Abschnitt 15.3 summieren sich auf 60 Minuten. Auf „etwa eine Stunde" vereinheitlicht. **Offen bleibt:** ob die Angaben insgesamt konservativ genug sind — das entscheidet sich erst, wenn jemand sie tatsächlich abarbeitet | Lektorat | **offen** |
| 5 | **Befund 7 (KI-Sperre)** wiederholt die Zurückhaltung aus Abschnitt 9.10: Es gibt gute Gründe für die Sperre, das Buch empfiehlt nicht, sie aufzuheben. **Diese Zurückhaltung muss an beiden Stellen erhalten bleiben** | Lektorat | **schützen** |
| 6 | **Abschnitt 14.6 ist ausdrücklich als Beobachtung gekennzeichnet, nicht als gemessener Zusammenhang.** Wie Punkt 1: Sobald C7 vorliegt, können daraus belegte Korrelationen werden. Bis dahin bleibt die Kennzeichnung | Autor / Lektorat | **schützen** |
| 7 | **Abschnitt 14.7 nimmt dem Kapitel bewusst die Spitze.** Ein Kapitel „zwanzig Fehler" endet normalerweise mit einem Versprechen. Dieses endet mit einer Einschränkung. **Das ist Absicht und beim Lektorat zu verteidigen** — es ist derselbe Grundsatz wie in 2.3 und 2.7 | Lektorat | **schützen** |
| 8 | **Punktsummen geprüft:** Gruppe A bis 19 P (plus Stufendeckel), Gruppe B bis 8 P, Gruppe C bis 18 P, Gruppe D bis 8 P. Die Angabe „bis zu vierzig Punkte" in 14.7 ist gerundet und konservativ; die Einzelangaben überschneiden sich teilweise (Befund 11 zählt P1, P4 und P5, die auch anderswo genannt sind). **Beim Lektorat sichern, dass keine Gesamtsumme addiert wird** — sie wäre falsch | Autor | **Warnung** |
| 9 | **Keine Abbildung.** Ein Kandidat wäre stark: die vier Gruppen als Aufwand-Wirkung-Diagramm — waagerecht Aufwand, senkrecht Punkte, zwanzig Punkte im Feld. Es wäre die einzige Abbildung des Buchs, die eine Reihenfolge sichtbar macht, und **die natürliche Überleitung zu Kapitel 15** | Gestaltung | **🔴 empfohlen** |

**Abbildungen in diesem Kapitel:** 0 — siehe Punkt 9
**Marginalien:** 2
**Geschätzter Satzumfang:** 11–12 Seiten
