---
kapitel: 16
teil: "IV — Grenzen"
titel: "Was von außen nicht messbar ist"
autor: "Manuel Potter"
status: entwurf
zuletzt_geprueft: 2026-08-24
standard_version: "2026.2"
zielumfang: 8 Seiten
---

<!-- KAPITELÖFFNER — rechte Seite -->

# 16

# Was von außen nicht messbar ist

> Fünfmal hat dieses Buch auf dieses Kapitel verwiesen. Hier steht die vollständige Aufzählung dessen, was der Standard nicht prüft — und was davon wichtiger ist als die letzten Punkte bis Platin.

<!-- SEITENUMBRUCH -->

> ### Rechtshinweis
>
> Abschnitt 16.3 nennt Auftragsverarbeitung, Löschfristen, Foto-Einwilligungen und Referenzfreigaben. Das sind Hinweise darauf, wonach zu fragen ist — keine Rechtsberatung und keine vollständige Aufzählung Ihrer Pflichten.

---

## 16.1 Warum dieses Kapitel im Buch steht

Ein Prüfmaßstab, der seine Grenzen nicht mitliefert, wird als Versprechen gelesen, das er nicht halten kann.

**Der gefährlichste Satz nach einem guten Prüfergebnis lautet: „Dann ist ja alles in Ordnung."** Er ist falsch, und er ist umso gefährlicher, je besser das Ergebnis war. Ein Betrieb mit 93 Punkten hat eine gute Website — und weiß nicht, ob sie gesichert wird, wem die Domain gehört und ob er die Daten bekommt, wenn er den Dienstleister wechselt.

Dieses Kapitel zählt drei verschiedene Dinge auf, und die Unterscheidung ist wichtig:

| | |
|---|---|
| **Erhoben, aber nicht bewertet** | Der Standard stellt es fest und gibt keine Punkte dafür — Abschnitt 16.2 |
| **Von außen nicht sichtbar** | Der Standard kann es nicht feststellen — Abschnitt 16.3 |
| **Nicht Gegenstand dieses Standards** | Es gehört zu einer anderen Frage — Abschnitt 16.5 |

---

## 16.2 Erhoben, aber nicht bewertet

Zwei Teile Ihres Berichts tragen keine Punkte. Sie sind trotzdem da, und sie sind nützlich.

### Der Infrastruktur-Befund — vier Angaben, null Punkte

<!-- VON HAND gepflegt: infrastruktur. Wird von keinem Skript erzeugt — der Vermerk „ERZEUGT" war falsch. Gegen Anhang B pruefen. -->

| Angabe | Was festgestellt wird |
|---|---|
| **Anbieter** | wo Ihre Website betrieben wird |
| **Erreichbarkeit** | ob die Startseite zum Prüfzeitpunkt antwortete |
| **System** | mit welchem Redaktionssystem oder Baukasten sie gebaut ist |
| **Auslieferungsnetzwerk** | ob ein vorgelagerter Verteildienst aktiv ist |

**Warum es keine Punkte gibt.** Sie können diese vier Dinge meist nicht ändern, ohne den Anbieter oder das System zu wechseln — und ein Standard soll bewerten, was Sie beeinflussen können. Ein Betrieb bei einem kleinen regionalen Anbieter ist nicht schlechter als einer bei einem großen.

**Wofür der Befund trotzdem gut ist:** Wenn Sie eine Überarbeitung beauftragen, ist das die erste Frage jedes Dienstleisters. Was auf Ihrer Seite steht, entscheidet über den Aufwand — und damit über den Preis. **Sie haben die Antwort, bevor Sie gefragt werden.**

::: MRG
**Für die Angebotseinholung**
Der Infrastruktur-Befund beantwortet die erste Frage jedes Dienstleisters, bevor sie gestellt wird.
:::

### Der GEO-Befund — fünf Prüfpunkte, keine Zahl

Er beschreibt, wie gut Ihre Website für Systeme aufbereitet ist, die auf eine Frage eine Antwort formulieren statt einer Linkliste.

| Prüfpunkt | Wird erhoben |
|---|---|
| Beschreibungsdatei `llms.txt` vorhanden | ja |
| Steuerdatei lässt KI-Systeme zu | ja |
| Strukturierte Daten vorhanden | ja |
| **Erwähnungen in KI-Antworten** | **nein** |
| **Erscheinen in zusammengefassten Suchantworten** | **nein** |

**Die letzten beiden stehen im Bericht als „unbekannt" — ohne Empfehlung.** Sie werden nicht erhoben, weil eine Erhebung je Abfrage Geld kostet und weil das Ergebnis mit jeder neuen Modellversion ein anderes wäre.

**Sie stehen trotzdem im Bericht**, damit Sie wissen, dass es sie gibt. Eine Liste, die nur das nennt, was gemessen wurde, erweckt den Eindruck, es gäbe nichts anderes.

> **Und ausdrücklich keine Punktzahl.** Eine Zahl lädt zum Vergleichen ein, und für dieses Feld gibt es keinen stabilen Maßstab. Die ersten drei Prüfpunkte werden in der Wertung bereits erfasst — bei E4 und E7 in Kapitel 9. Sie hier ein zweites Mal zu verrechnen, wäre eine Doppelzählung mit dem Anschein von Genauigkeit.

---

## 16.3 Was von außen nicht sichtbar ist

Das ist die Aufzählung, auf die fünfmal verwiesen wurde. **Nichts davon steht in Ihrer Punktzahl.**

### A · Betrieb und Sicherung

| Nicht geprüft | Warum es zählt |
|---|---|
| **Ob Sicherungen erstellt werden** | Ohne sie ist ein Ausfall kein Zwischenfall, sondern ein Totalverlust |
| **Ob sich eine Sicherung zurückspielen lässt** | Eine Sicherung, die nie zurückgespielt wurde, ist keine — sie ist eine Annahme |
| **Wie oft und wie weit zurück** | Ein Schaden, der drei Wochen unbemerkt bleibt, überlebt eine Wochensicherung |
| **Ob das System aktuell gehalten wird** | Angriffe auf kleine Websites sind automatisiert und suchen bekannte Lücken |
| **Ob Erweiterungen gepflegt werden** | Der häufigste Einbruchsweg bei verbreiteten Redaktionssystemen |
| **Wer Zugang hat** | Der ehemalige Praktikant, die ehemalige Agentur, der ehemalige Mitarbeiter |
| **Ob die Zugänge geschützt sind** | Ein Zugang ohne zweiten Faktor ist ein Passwort entfernt |

**Die zweite Zeile ist die, die am meisten kostet, wenn sie fehlt.** Fast jeder Anbieter wirbt mit Sicherungen. Ob sie sich zurückspielen lassen, hat fast niemand ausprobiert — und man erfährt es an dem Tag, an dem es darauf ankommt.

### B · Verträge und Eigentum

| Nicht geprüft | Warum es zählt |
|---|---|
| **Wem die Domain gehört** | Steht dort Ihre Agentur statt Ihres Betriebs, gehört Ihre Adresse nicht Ihnen |
| **Ob Sie die Daten herausbekommen** | Bei einem Wechsel entscheidet der Vertrag, nicht der gute Wille |
| **Ob Sie Zugang zum System haben** | Ein Zugang, den nur der Dienstleister hat, ist eine Abhängigkeit |
| **Ob die Bilder lizenziert sind** | Ein gekauftes Motiv ohne gültige Lizenz ist teurer als jede Abmahnung wegen Impressum |
| **Ob die Schriftarten lizenziert sind** | Für Websites gelten andere Lizenzen als für Druckerzeugnisse |
| **Was der Wartungsvertrag umfasst** | „Wartung" bedeutet bei jedem Anbieter etwas anderes |

**Die erste Zeile ist der wichtigste Satz dieses Kapitels.** Wenn Ihre Domain auf einen Dritten eingetragen ist, ist alles andere in diesem Buch nachrangig. Sie haben dann keine Website, sondern ein Nutzungsrecht — und es endet, wenn die Geschäftsbeziehung endet.

::: MRG
**🔴 Prüfen Sie das**
Wem gehört Ihre Domain? Die Antwort steht in Ihrer Anbieterverwaltung. Wenn Sie keine haben, ist das bereits die Antwort.
:::

### C · Inhaltliche Richtigkeit

| Nicht geprüft | Warum es zählt |
|---|---|
| **Ob die Angaben im Impressum stimmen** | Geprüft wird, ob sie vorhanden sind — nicht, ob sie aktuell und richtig sind |
| **Ob die Datenschutzerklärung zu Ihren Diensten passt** | Der häufigste Fehler bei übernommenen Vorlagen |
| **Ob Verträge zur Auftragsverarbeitung bestehen** | Für jeden externen Dienst erforderlich, von außen unsichtbar |
| **Ob Löschfristen eingehalten werden** | Formulareingaben, die seit Jahren im Postfach liegen |
| **Ob Einwilligungen für Fotos vorliegen** | Bei Mitarbeitenden schriftlich, widerruflich, mit Regelung für den Austritt |
| **Ob Referenzen freigegeben sind** | Ein benanntes Objekt braucht die Zustimmung des Auftraggebers |

**Das ist die unangenehmste Zeile dieses Kapitels:** Ein Betrieb kann bei L1 und L2 die volle Punktzahl haben und trotzdem ein rechtliches Problem. **Zwanzig von zwanzig Punkten in Kapitel 5 bedeuten: An dieser Stelle liegt kein *sichtbarer* Mangel vor.** Mehr nicht.

### D · Barrierefreiheit in der Benutzung

Kapitel 8 hat es bereits gesagt und es gehört in die vollständige Liste:

| Nicht geprüft |
|---|
| Ob Alternativtexte inhaltlich etwas beschreiben |
| Ob ein Vorleseprogramm die Seite verständlich wiedergibt |
| Ob Formulare mit Hilfsmitteln ausfüllbar sind |
| Ob die Reihenfolge beim Vorlesen sinnvoll ist |
| Ob Videos Untertitel haben, die stimmen |
| Ob die Sprache verständlich ist |

**Diese sechs entscheiden über Barrierefreiheit.** Keine davon lässt sich messen — sie lassen sich nur ausprobieren, von Menschen, die auf Hilfsmittel angewiesen sind.

### E · Wirkung

| Nicht geprüft | Wo Sie es finden |
|---|---|
| **Wie viele Besucher Sie haben** | in Ihrer Besucherstatistik, falls vorhanden |
| **Woher sie kommen** | ebenda |
| **Wie viele Anfragen daraus werden** | in Ihrem Postfach — und in Ihrer Zählung am Telefon |
| **Was ein Auftrag Sie gekostet hat** | in Ihrer Buchhaltung |

**Das ist die Grenze, die Abschnitt 2.3 gezogen hat.** Der Standard misst den Zustand, nicht die Wirkung. Eine Website mit 95 Punkten, die niemand kennt, bringt weniger als eine mit 70, auf die eine gute Empfehlung verweist.

---

## 16.4 Zwölf Fragen an Ihren Dienstleister

Die Liste aus 16.3 ist nicht nur eine Einschränkung. Sie ist eine Fragenliste — und sie ist der einzige Weg, an die Antworten zu kommen.

**Stellen Sie diese zwölf Fragen schriftlich.** Nicht aus Misstrauen, sondern weil eine schriftliche Antwort später auffindbar ist.

> ☐ **1.** Auf wen ist unsere Domain eingetragen?
> ☐ **2.** Wer hat administrativen Zugang zu unserer Website — bitte vollständige Liste?
> ☐ **3.** Sind diese Zugänge mit einem zweiten Faktor geschützt?
> ☐ **4.** Wie oft wird gesichert, und wie weit reichen die Sicherungen zurück?
> ☐ **5.** Wann wurde zuletzt eine Sicherung testweise zurückgespielt?
> ☐ **6.** Wann wurde das System zuletzt aktualisiert?
> ☐ **7.** Welche Erweiterungen sind installiert, und werden sie noch gepflegt?
> ☐ **8.** Bekommen wir bei einem Wechsel alle Daten — und in welcher Form?
> ☐ **9.** Sind alle verwendeten Bilder und Schriften für den Einsatz im Web lizenziert, und liegen die Nachweise vor?
> ☐ **10.** Mit welchen externen Diensten bestehen Verträge zur Auftragsverarbeitung?
> ☐ **11.** Was genau umfasst unser Wartungsvertrag — und was nicht?
> ☐ **12.** Wer wird benachrichtigt, wenn das Zertifikat abläuft?

**Zur Frage 5:** Sie ist die einzige der zwölf, bei der ein Zögern selbst die Antwort ist.

**Zur Frage 12:** Sie beantwortet den häufigsten Grund für ein abgelaufenes Zertifikat — die Warnmail geht an ein Postfach, das seit dem letzten Wechsel niemand öffnet.

> **Wenn Sie keinen Dienstleister haben**, sind das trotzdem Ihre zwölf Fragen. Dann stellen Sie sie sich selbst, und die Antworten stehen in Ihrer Anbieterverwaltung.

---

## 16.5 Was nicht Gegenstand dieses Standards ist

Zum Schluss die Abgrenzung nach außen — Dinge, die weder unsichtbar noch vergessen sind, sondern zu einer anderen Frage gehören.

| Nicht Gegenstand | Weil |
|---|---|
| **Werbung und Anzeigen** | eine Vertriebsfrage, keine Zustandsfrage |
| **Ihr Eintrag in Kartendiensten und Verzeichnissen** | liegt außerhalb Ihrer Website |
| **Bewertungsportale** | dito — der Standard prüft nur, ob Sie Bewertungen zeigen |
| **Soziale Netzwerke** | eigenes Feld mit eigenen Maßstäben |
| **Ihre Preise und Ihr Angebot am Markt** | der Standard prüft, ob Sie es erklären, nicht ob es trägt |
| **E-Mail und Telefonanlage** | andere Betriebsmittel, andere Prüfung |

**Der zweite Punkt verdient eine Anmerkung.** Für einen lokalen Betrieb ist der Eintrag in einem Kartendienst oft wirksamer als jede Verbesserung an der Website. Dass er hier nicht geprüft wird, heißt nicht, dass er unwichtig ist — er ist nur kein Bestandteil Ihrer Website und deshalb kein Bestandteil dieses Standards.

---

## 16.6 Was das für Ihre Punktzahl bedeutet

**Ihre Punktzahl bleibt gültig.** Sie beschreibt genau das, was sie beschreibt: den von außen prüfbaren Zustand Ihrer Website. Nichts in diesem Kapitel macht sie kleiner.

**Was dieses Kapitel ändert, ist die Bedeutung des Satzes „alles in Ordnung".**

| Ihr Ergebnis sagt | Ihr Ergebnis sagt nicht |
|---|---|
| Ein Besucher findet keine sichtbaren Hürden | dass Ihre Website sicher betrieben wird |
| Die Pflichtangaben sind vorhanden | dass sie inhaltlich richtig sind |
| Die Seite ist auffindbar aufgebaut | dass sie gefunden wird |
| Sie steht einer Anfrage nicht im Weg | dass Anfragen kommen |
| Die prüfbaren Barrieren sind beseitigt | dass die Seite barrierefrei benutzbar ist |

**Und deshalb steht dieses Kapitel vor Kapitel 17 und nicht am Ende des Buchs.** Wer eine Überarbeitung beauftragt, sollte die zwölf Fragen aus Abschnitt 16.4 stellen, bevor er über Punkte redet. Zwei davon — wem die Domain gehört und ob Sie die Daten herausbekommen — entscheiden mehr über Ihre Handlungsfähigkeit als alle 103 Punkte zusammen.

---

## Das Wichtigste aus diesem Kapitel

> - **Ein Prüfmaßstab ohne mitgelieferte Grenzen wird als Versprechen gelesen, das er nicht halten kann.**
> - **Infrastruktur-Befund und GEO-Befund werden erhoben, aber nicht bewertet.** Der GEO-Befund ist bewusst keine Zahl.
> - **Nicht geprüft werden:** Sicherungen und ihre Wiederherstellbarkeit, Aktualisierungsstand, Zugangsverwaltung, Verträge, Domaineigentum, Lizenzen, inhaltliche Richtigkeit, Barrierefreiheit in der Benutzung und jede Wirkung.
> - **Wem die Domain gehört, ist wichtiger als Ihre Punktzahl.** Steht dort ein Dritter, haben Sie keine Website, sondern ein Nutzungsrecht.
> - **Eine Sicherung, die nie zurückgespielt wurde, ist keine Sicherung.** Es ist eine Annahme.
> - **Zwölf Fragen an Ihren Dienstleister — schriftlich.** Sie kosten nichts und beantworten alles, was dieser Standard nicht kann.
> - **Volle Punktzahl heißt: keine sichtbaren Hürden.** Nicht: alles in Ordnung.

---

<!-- REDAKTIONELLE ANMERKUNGEN — NICHT DRUCKEN -->

## Offene Punkte zu Kapitel 16

| # | Punkt | Wer | Status |
|---|---|---|---|
| 1 | 🔴 **Korrektur an Kapitel 3 und 9 bereits eingepflegt.** Beide Kapitel sprachen vom „GEO-Wert (0 bis 10)" — diese Zahl stammt aus § 6 der Spezifikation und ist **nicht implementiert.** Der Bericht enthält stattdessen fünf Prüfpunkte mit Statuswörtern, zwei davon ausdrücklich unerhoben. Eine separate GEO-Überwachung rechnet einen Wert 0–100, gehört aber zu einem anderen Produkt und nicht zum Audit. **Mein Fehler: Ich habe der Spezifikation vertraut statt gemessen.** Kapitel 3.9 und 9.10 sind korrigiert und tragen jetzt „GEO-Befund" | Autor | **erledigt** |
| 2 | 🔴 **Folgeaufgabe: § 6 der Spezifikation nachziehen.** Sie beschreibt einen Wert 0–10 mit zehn Merkmalen. Implementiert sind fünf Prüfpunkte ohne Zahl. **Dritte Abweichung zwischen Spezifikation und Code** nach der Kammerangabe bei L1 und den Pflichtinhalten bei L2. Das Muster ist inzwischen belegt: Die Spezifikationsdokumente sind älter als der Code und werden nicht nachgezogen | Technik | **offen** |
| 3 | 🔴 **Die Liste in 16.3 ist eine fachliche Aufzählung, keine Extraktion.** Sie folgt aus dem, was der Standard nicht erhebt — aber es gibt im Code keine Gegenliste, aus der sie erzeugt werden könnte. **Sie ist damit das einzige größere Buchelement ohne Codegrundlage**, und sie steht an einer Stelle, an der das Buch Vollständigkeit verspricht („zählt es vollständig auf"). **Vor Drucklegung fachlich gegenlesen lassen** — idealerweise von jemandem, der Websites betreibt und nicht baut | Autor / Technik | **offen** |
| 4 | **Die zwölf Fragen in 16.4 sind der praktisch wertvollste Teil des Kapitels** und ein natürlicher Kandidat für Anhang C als heraustrennbare Vorlage. **Mit Vorlage 1 und 2 abstimmen**, damit sie nicht doppelt erscheinen | Autor / Gestaltung | **empfohlen** |
| 5 | ✅ **ERLEDIGT 24.08.2026** — Rechtshinweis am Kapitelanfang ergänzt. Die Aussagen bleiben auf dem Anwaltstermin (B12) | Recht | **offen** |
| 6 | **Die Aussage zur Domain (16.3 B, erste Zeile)** ist die stärkste des Kapitels und juristisch verkürzt — „gehört Ihre Adresse nicht Ihnen" beschreibt die praktische Lage, nicht die Rechtslage im Einzelfall. **Formulierung anwaltlich prüfen** | Recht | **offen** |
| 7 | **Fünf Verweise eingelöst:** 1.7 (Sicherungen, Zugangsdaten, Vertragslage), 2.3 (zweimal), 2.5 (hinter der Anmeldung), 6.9 (Zugangsverwaltung, Aktualisierungsstand, Sicherungen, Wiederherstellbarkeit), 15.8. **Alle abgedeckt.** Zusätzlich 3.1, 3.9, 8.2 und 9.10. **Beim Lektorat gegenprüfen, dass kein Verweis ins Leere zeigt** | Lektorat | **prüfen** |
| 8 | **Keine Abbildung.** Für acht Seiten vertretbar. Ein Kandidat wäre nützlich: die drei Zonen aus 16.1 als konzentrische Darstellung — was bewertet wird, was erhoben aber nicht bewertet wird, was gar nicht sichtbar ist. Es wäre die einzige Abbildung, die den Geltungsbereich des Standards zeigt | Gestaltung | **empfohlen** |

**Abbildungen in diesem Kapitel:** 0 — siehe Punkt 8
**Marginalien:** 2
**Geschätzter Satzumfang:** 8 Seiten
