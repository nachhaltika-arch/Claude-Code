---
kapitel: 6
teil: "II — Die acht Kategorien"
titel: "Sicherheit und Datenschutz"
autor: "Manuel Potter"
status: entwurf
zuletzt_geprueft: 2026-08-24
standard_version: "2026.2"
zielumfang: 12 Seiten
punkte: 10
kriterien: "S1–S4"
---

<!-- KAPITELÖFFNER — rechte Seite -->

# 6

# Sicherheit und Datenschutz

# 10 Punkte

> Vier Kriterien, alle vollständig messbar. Eines davon kann Ihre Stufe auf „Nicht konform" begrenzen. Und eines misst etwas, das Ihre Besucher nie bemerken, Ihre Rechtslage aber sehr wohl.

<!-- SEITENUMBRUCH -->

> ### Rechtshinweis
>
> Dieses Kapitel beschreibt technische Prüfungen und ihre rechtlichen Bezüge. Es ist keine Rechtsberatung. Insbesondere die Bewertung fremder Dienste in Abschnitt 6.7 berührt Fragen, die von Gerichten unterschiedlich beurteilt werden. Für Ihren Einzelfall gilt, was Ihre Rechtsberatung sagt — nicht, was hier steht.

---

## 6.1 Was hier bewertet wird

Vier Kriterien, zusammen 10 Punkte. Alle vier werden gemessen; keines wird eingeschätzt.

<!-- ERZEUGT aus generiert/kriterien-sicherheit.md — nicht von Hand ändern. -->

| Code | Kriterium | Punkte | Gilt für |
|---|---|---|---|
| S1 | Verschlüsselungszertifikat | 3 | alle Klassen |
| S2 | Erzwungene Weiterleitung auf HTTPS | 2 | alle Klassen |
| S3 | Sicherheitsheader | 3 | alle Klassen |
| S4 | Fremde Dienste ohne Einwilligung | 2 | alle Klassen |

Wie bei Recht gibt es hier **keine Klassenunterschiede**. Ein Zertifikat ist gültig oder nicht, gleich ob es zu einer Kanzlei oder einer Bäckerei gehört.

::: MRG
**S1–S4**
4 Kriterien · 10 Punkte
alle **gemessen**, keine Einschätzung
:::

---

## 6.2 Warum nur zehn Punkte

Die Frage ist berechtigt: Sicherheit klingt wichtiger als zehn von 103 Punkten.

Der Grund liegt in der zweiten Leitfrage des Standards — **wie stark wirkt es sich darauf aus, ob Sie Aufträge bekommen?** Und da ist die Antwort unbequem: kaum.

**Ein Besucher bemerkt ein fehlendes Zertifikat sofort.** Der Browser blendet eine Warnung ein, die Seite wird als „nicht sicher" gekennzeichnet, und ein Teil der Besucher geht. Das ist ein Verkaufsproblem, und deshalb steht S1 mit drei Punkten in der Kategorie und wirkt zusätzlich als Ausschlusskriterium.

**Einen fehlenden Sicherheitsheader bemerkt er nie.** Kein Besucher hat je eine Website verlassen, weil ihr eine Content-Security-Policy fehlte. Das macht den Header nicht unwichtig — es macht ihn zu etwas, das nicht über die Kundengewinnung entscheidet.

Diese Kategorie misst also überwiegend **Sorgfalt**, nicht Wirkung. Sorgfalt ist zehn Punkte wert. Sie ist nicht zwanzig wert, weil der Standard sonst behaupten würde, eine technisch vorbildliche Seite ohne Angebot sei besser als eine schlichte Seite, die Anfragen auslöst.

::: MRG
**Was diese Kategorie misst**
Nicht, ob Ihre Website Besucher überzeugt. Sondern, ob sie ordentlich gebaut ist.
:::

---

## 6.3 Der Fall

Elektro Hansen, Branchenklasse K1. Sie kennen den Betrieb aus den Kapiteln 3 und 5.

| Kriterium | Befund | Punkte |
|---|---|---|
| S1 Zertifikat | gültig, Laufzeit über 30 Tage, Domain passt | 3 / 3 |
| S2 Weiterleitung | http-Aufruf leitet zwingend auf https weiter | 2 / 2 |
| S3 Sicherheitsheader | alle vier gesetzt | 3 / 3 |
| S4 Fremde Dienste | **Schriftarten werden von einem fremden Server geladen** | 1 / 2 |
| | | **9 / 10** |

Ein Punkt fehlt, und er fehlt an einer Stelle, die fast niemand von sich aus prüft.

**Was hier passiert ist:** Elektro Hansen hat ein Einwilligungswerkzeug, und es funktioniert — das Statistikwerkzeug lädt tatsächlich erst nach Zustimmung. Deshalb standen in Kapitel 5 volle vier Punkte bei L3. Die **Schriftarten** aber werden bei jedem Seitenaufruf von einem fremden Server nachgeladen, bevor irgendjemand irgendetwas anklicken konnte. Das Einwilligungswerkzeug kennt sie nicht, weil sie im Design stecken und nicht im Statistikbereich.

Das ist der mit Abstand häufigste Befund dieser Kategorie. Und er ist mit einem Handgriff behoben, der nebenbei die Ladezeit verbessert.

---

## 6.4 S1 — Verschlüsselungszertifikat · 3 Punkte

::: MRG
**S1 · 3 Punkte**
gemessen
**Ausschlusskriterium**
:::

### Worum es geht

Ohne gültiges Zertifikat läuft die Verbindung zwischen Besucher und Ihrer Website unverschlüsselt. Alles, was ein Besucher eingibt — Name, Telefonnummer, Nachricht — ist auf dem Weg mitlesbar. Browser weisen inzwischen deutlich darauf hin.

### Was geprüft wird

Nicht, ob die Adresse mit `https` beginnt. **Es wird eine echte verschlüsselte Verbindung aufgebaut** und dabei dreierlei festgestellt:

| Prüfung | Bedeutung |
|---|---|
| Ist das Zertifikat gültig? | nicht abgelaufen, Kette vollständig |
| Passt es zur Domain? | ausgestellt für genau diese Adresse |
| Wie lange läuft es noch? | Restlaufzeit in Tagen |

Der Unterschied zur oberflächlichen Prüfung ist wesentlich: Ein abgelaufenes Zertifikat lässt die Adresse weiterhin mit `https` beginnen. Nur der Verbindungsaufbau scheitert.

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-si_ssl.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 3 | Zertifikat gültig, Restlaufzeit 30 Tage oder mehr |
| 2 | Zertifikat gültig, **Restlaufzeit unter 30 Tagen** |
| 0 | kein gültiges Zertifikat → **Stufe: Nicht konform** |

**Die mittlere Zeile ist eine Warnung, kein Mangel.** Ein Zertifikat mit 20 Tagen Restlaufzeit ist heute in Ordnung und in drei Wochen ein Ausschlusskriterium. Der Punktabzug soll Ihnen genau diese drei Wochen verschaffen.

::: MRG
**Warnfrist**
Unter 30 Tagen Restlaufzeit: ein Punkt weniger. Nicht als Strafe — als Vorwarnung.
:::

### So beheben Sie es

Zertifikate sind heute bei praktisch jedem Anbieter kostenlos und erneuern sich automatisch. Wenn Ihres abgelaufen ist, hat die automatische Erneuerung versagt — und das ist selten ein Einzelfall. Prüfen Sie:

1. **Ist die automatische Erneuerung überhaupt eingerichtet?**
2. **Läuft sie für alle Varianten Ihrer Adresse** — mit und ohne `www`?
3. **Geht die Ablaufwarnung Ihres Anbieters an eine Adresse, die jemand liest?** Der häufigste Grund für ein abgelaufenes Zertifikat ist eine Warnmail an ein Postfach, das seit dem Agenturwechsel niemand mehr öffnet.

---

## 6.5 S2 — Erzwungene Weiterleitung auf HTTPS · 2 Punkte

::: MRG
**S2 · 2 Punkte**
gemessen
:::

### Worum es geht

Ein gültiges Zertifikat allein genügt nicht, wenn Ihre Seite auch unverschlüsselt erreichbar bleibt. Wer Ihre Adresse ohne Vorsatz eintippt oder einem alten Verweis folgt, landet dann auf der unverschlüsselten Fassung — mit gültigem Zertifikat auf der anderen, ungenutzten Seite.

### Was geprüft wird

Die unverschlüsselte Adresse wird aufgerufen. Führt sie zwingend auf die verschlüsselte weiter?

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-si_redirect.md — nicht von Hand ändern. -->

| Punkte | Bedingung |
|---|---|
| 2 | http-Aufruf leitet auf https weiter |
| 0 | keine Weiterleitung |

Kein Zwischenwert. Eine Weiterleitung existiert oder sie existiert nicht.

### So beheben Sie es

Eine Einstellung beim Anbieter oder eine Zeile in der Serverkonfiguration. Bei den meisten Baukastensystemen ein Schalter mit der Beschriftung „HTTPS erzwingen" oder „SSL erzwingen".

**Danach prüfen — und zwar richtig.** Tippen Sie die Adresse mit vorangestelltem `http://` in einen Browser, in dem Sie die Seite noch nie geöffnet haben. Der eigene Browser merkt sich frühere verschlüsselte Aufrufe und leitet von sich aus um. Sie prüfen dann Ihren Browser, nicht Ihre Website.

---

## 6.6 S3 — Sicherheitsheader · 3 Punkte

::: MRG
**S3 · 3 Punkte**
gemessen
:::

### Worum es geht

Sicherheitsheader sind kurze Anweisungen, die Ihr Server bei jeder Auslieferung mitschickt. Sie sagen dem Browser, was er mit Ihrer Seite tun darf und was nicht. Ein Besucher sieht sie nie. Sie verhindern Angriffe, die ohne sie möglich wären.

Vier werden geprüft:

| Header | Was er anordnet |
|---|---|
| **HSTS** | Diese Seite ausschließlich verschlüsselt aufrufen, auch beim nächsten Mal |
| **CSP** | Nur Inhalte aus diesen Quellen ausführen |
| **X-Frame-Options** | Diese Seite nicht in einen fremden Rahmen einbetten |
| **X-Content-Type-Options** | Dateitypen nicht selbst erraten |

**Der dritte ist der praktisch wichtigste für einen Betrieb.** Ohne ihn lässt sich Ihre Website in eine fremde Seite einbetten — mit einer fremden Beschriftung darüber und einer fremden Schaltfläche darunter. Der Besucher glaubt, bei Ihnen zu sein.

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-si_header.md — nicht von Hand ändern. -->

| Punkte | Gesetzte Header |
|---|---|
| 3 | alle vier |
| 2 | zwei **oder drei** |
| 1 | einer |
| 0 | keiner |

::: MRG
**Achtung, Sprungstelle**
Der dritte Header bringt keinen zusätzlichen Punkt. Wer bei zwei steht, sollte gleich alle vier setzen — der Weg von 2 auf 3 Punkte führt nur über den vierten.
:::

**Warum zwei und drei Header dieselbe Punktzahl ergeben.** Die drei Punkte des Kriteriums werden anteilig auf vier Header verteilt und kaufmännisch gerundet. Zwei von vier ergeben 1,5 und werden zu 2. Drei von vier ergeben 2,25 und werden ebenfalls zu 2. Das ist eine Folge der Rundung, kein bewusst gesetzter Zwischenwert.

Für Sie als Leser hat das eine sehr praktische Konsequenz: **Der Aufwand für den dritten Header lohnt sich nur, wenn Sie den vierten gleich mitnehmen.**

### So beheben Sie es

Alle vier Header sind Serverkonfiguration, keine Änderung an Ihrer Website. Sie kosten nichts und wirken sofort.

Die Reihenfolge, in der ich sie einrichten würde:

1. **X-Content-Type-Options** — ein Wert, keine Nebenwirkungen
2. **X-Frame-Options** — ein Wert, Nebenwirkung nur, wenn Sie Ihre Seite selbst irgendwo einbetten
3. **HSTS** — wirkt dauerhaft im Browser des Besuchers. **Erst setzen, wenn S2 erledigt ist** und die verschlüsselte Fassung zuverlässig läuft
4. **CSP** — der aufwendigste. Er kann Ihre Seite unbrauchbar machen, wenn er zu streng eingestellt ist. Mit einem Beobachtungsmodus beginnen, nicht mit einer Sperre

> **Ein Wort der Warnung zu HSTS.** Dieser Header weist Browser an, Ihre Seite künftig nur noch verschlüsselt aufzurufen — und er wirkt über einen langen Zeitraum. Wenn danach etwas mit Ihrem Zertifikat schiefgeht, ist Ihre Seite für wiederkehrende Besucher nicht mehr erreichbar. Nicht schlecht erreichbar. Nicht erreichbar.

---

## 6.7 S4 — Fremde Dienste ohne Einwilligung · 2 Punkte

::: MRG
**S4 · 2 Punkte**
gemessen
→ Abgrenzung zu L3, Kapitel 5
:::

### Worum es geht

Jeder Inhalt, den Ihre Website von einem fremden Server nachlädt, teilt diesem Server die IP-Adresse Ihres Besuchers mit — und meist mehr. Das gilt für Statistikwerkzeuge, für Kartendienste, für eingebettete Videos, für Chat-Fenster. **Und es gilt für Schriftarten.**

Der letzte Punkt überrascht die meisten Betriebe. Eine Schriftart ist Gestaltung; dass sie eine datenschutzrechtliche Frage aufwirft, erschließt sich niemandem von selbst. Genau deshalb ist es der häufigste Befund dieser Kategorie.

### Was geprüft wird

Beim Aufruf der Seite wird beobachtet, welche fremden Server kontaktiert werden — und zwar **vor** jeder Interaktion des Besuchers.

### Punktvergabe

<!-- ERZEUGT aus generiert/abstufung-si_drittanbieter.md — nicht von Hand ändern. -->

Die Punktzahl beginnt bei 2 und wird für jeden Befund um einen Punkt gesenkt:

| Befund | Abzug |
|---|---|
| Schriftarten werden von einem fremden Server geladen | −1 |
| Statistik- oder Werbedienste laden, ohne dass ein Einwilligungswerkzeug erkannt wurde | −1 |

| Punkte | Bedeutung |
|---|---|
| 2 | keine fremden Schriftarten, keine Dienste vor der Einwilligung |
| 1 | einer der beiden Befunde |
| 0 | beide Befunde |

### Die Abgrenzung zu L3 — bitte einmal genau lesen

Dieser Abschnitt beantwortet eine Frage, die aufmerksamen Lesern in Kapitel 5 gekommen sein wird: **Wird derselbe Sachverhalt zweimal bewertet?**

Die Antwort ist: teilweise ja, und das ist beabsichtigt — mit einer wichtigen Einschränkung.

| | L3 (Kapitel 5) | S4 (dieses Kapitel) |
|---|---|---|
| **Frage** | Ist ein Einwilligungswerkzeug vorhanden? | Was lädt tatsächlich, bevor eingewilligt wurde? |
| **Fremde Schriftarten** | wirken **nicht** | **−1 Punkt** |
| **Tracking ohne Werkzeug** | 0 Punkte + Deckel auf Bronze | **−1 Punkt** |

**Fremde Schriftarten wirken nur hier.** Sie sind der Grund, warum es dieses Kriterium überhaupt gibt: Sie sind einwilligungsrelevant, aber ein Einwilligungswerkzeug erfasst sie in der Praxis fast nie, weil sie im Gestaltungsteil der Seite stecken. L3 würde sie deshalb übersehen.

**Tracking ohne Einwilligung wirkt an beiden Stellen** — einmal als Punktabzug hier, einmal als Punktverlust und Stufendeckel dort. Das ist eine bewusste Verstärkung: Es ist der schwerste Befund dieser beiden Kategorien.

::: MRG
🔴 **Zu prüfen**
Die Bronze-Deckelung darf nur einmal greifen. Siehe redaktionelle Anmerkungen.
:::

**Der Deckel greift dabei nur einmal.** Eine Website mit Tracking ohne Einwilligung wird auf Bronze begrenzt — nicht zweimal, nicht tiefer. S4 zieht einen Punkt ab, mehr nicht.

### So beheben Sie es

**Schriftarten örtlich einbinden.** Die Dateien werden einmal heruntergeladen und liegen danach auf Ihrem eigenen Server. Es ist eine Änderung an zwei Stellen im Gestaltungsteil. Sie brauchen dafür niemanden, der Ihre Website versteht — nur jemanden, der sie bearbeiten darf.

Nebeneffekt: **Die Seite wird schneller.** Ein fremder Server bedeutet eine zusätzliche Namensauflösung, einen zusätzlichen Verbindungsaufbau und eine zusätzliche Wartezeit, bevor der erste Buchstabe erscheint. Sie holen hier einen Punkt und in Kapitel 7 möglicherweise einen zweiten.

**Karten ersetzen.** Ein statisches Bild Ihres Standorts mit einem Verweis auf den Kartendienst erfüllt denselben Zweck und lädt nichts nach.

**Videos erst auf Klick laden.** Die meisten Baukastensysteme bieten das unter Bezeichnungen wie „datenschutzfreundliche Einbettung" an.

---

## 6.8 Ihre Punkte in dieser Kategorie

| Code | Kriterium | Möglich | Erreicht |
|---|---|---|---|
| S1 | Verschlüsselungszertifikat | 3 | ____ |
| S2 | Erzwungene Weiterleitung auf HTTPS | 2 | ____ |
| S3 | Sicherheitsheader | 3 | ____ |
| S4 | Fremde Dienste ohne Einwilligung | 2 | ____ |
| | **Summe** | **10** | ____ |

**Zusätzlich anzukreuzen:**

| Ausschlusskriterium | Trifft zu |
|---|---|
| Kein gültiges Verschlüsselungszertifikat | ☐ |

---

## 6.9 Vier verbreitete Irrtümer

**„Bei uns gibt es nichts zu holen, wir sind kein Ziel."**
Angriffe auf kleine Websites sind fast nie gezielt. Sie sind automatisiert und suchen nach bekannten Lücken, unabhängig davon, wem die Seite gehört. Die Frage ist nicht, ob jemand es auf Sie abgesehen hat, sondern ob Ihre Seite in ein Suchmuster passt.

**„Wir haben ein Schloss-Symbol, also ist alles verschlüsselt."**
Das Schloss zeigt, dass **diese eine Verbindung** verschlüsselt ist. Es sagt nichts darüber, ob die unverschlüsselte Fassung Ihrer Seite ebenfalls erreichbar ist (S2), und nichts über die vier Header (S3).

**„Schriftarten von einem fremden Server sind doch normal."**
Verbreitet ja, unproblematisch nein. Es ist die häufigste Fundstelle dieser Kategorie, und sie ist gleichzeitig die am schnellsten behobene. Der Aufwand liegt bei einer halben Stunde.

**„Zehn von zehn Punkten heißt, wir sind sicher."**
Nein. Der Standard prüft von außen. Ob Ihre Zugangsdaten gut gewählt sind, ob Ihr Redaktionssystem aktuell ist, ob es Sicherungen gibt und ob sie sich zurückspielen lassen — davon ist nichts von außen sichtbar. Kapitel 16 führt auf, was hier fehlt. **Die zehn Punkte sagen: Was ein Fremder prüfen kann, ist in Ordnung.**

---

## Das Wichtigste aus diesem Kapitel

> - **Vier Kriterien, 10 Punkte**, alle gemessen, keine Klassenunterschiede.
> - **S1 ist Ausschlusskriterium.** Ohne gültiges Zertifikat: Nicht konform, unabhängig von allem anderen.
> - **Unter 30 Tagen Restlaufzeit** kostet ein Zertifikat einen Punkt — als Vorwarnung, nicht als Strafe.
> - **Der dritte Sicherheitsheader bringt keinen zusätzlichen Punkt.** Wer bei zwei steht, nimmt am besten gleich alle vier.
> - **HSTS erst setzen, wenn die Weiterleitung sauber läuft.** Falsch gesetzt macht er die Seite unerreichbar.
> - **Fremde Schriftarten sind der häufigste Befund** — und der am schnellsten behobene. Er bringt außerdem Ladezeit.
> - **Volle Punktzahl heißt: was von außen prüfbar ist, stimmt.** Über Zugänge, Aktualisierungen und Sicherungen sagt sie nichts.

---

<!-- REDAKTIONELLE ANMERKUNGEN — NICHT DRUCKEN -->

## Offene Punkte zu Kapitel 6

| # | Punkt | Wer | Status |
|---|---|---|---|
| 1 | 🔴 **S3-Staffelung: der dritte Header ist wertlos.** Nachgerechnet: `round(anteil × 3)` ergibt für 0/1/2/3/4 gesetzte Header die Punktwerte 0/1/2/2/3. Zwei und drei Header sind gleich viel wert. Das ist eine Rundungsfolge, kein Entwurf. Abschnitt 6.6 weist es offen aus und macht eine Handlungsempfehlung daraus — **das ist die ehrliche, nicht die richtige Lösung.** Entweder die Header gewichten (CSP und X-Frame höher) oder das Kriterium auf 4 Punkte setzen | Technik | **offen** |
| 2 | 🔴 **Doppelwertung L3 / S4.** Der Restarbeiten-Report führt sie als A7. Abschnitt 6.7 stellt sie transparent dar und behauptet, der Bronze-Deckel greife nur einmal. **Das ist im Code zu verifizieren**, bevor der Satz beginnt — die Aussage steht sonst ungeprüft im Buch | Technik | **offen** |
| 3 | **Fremde Schriftarten und Rechtsprechung.** Abschnitt 6.7 formuliert bewusst ohne Nennung konkreter Urteile oder Schadensersatzhöhen. Ob das so bleibt, gehört auf den Anwaltstermin — der Restarbeiten-Report führt „typische Abmahnkosten" als bewusst weggelassen (C3) | Recht | bestätigen |
| 4 | **HSTS-Warnung in 6.6.** Die Aussage „für wiederkehrende Besucher nicht mehr erreichbar" ist technisch korrekt, aber drastisch. Beim Lektorat prüfen, ob sie so stehen bleibt — sie soll abschrecken, nicht lähmen | Lektorat | offen |
| 5 | **Der Fall Elektro Hansen** hat hier 9/10 mit fremden Schriftarten als einzigem Befund. Das muss zur Kategorietabelle in Kapitel 3 passen und zu L3 = 4/4 in Kapitel 5 (Einwilligungswerkzeug vorhanden, Tracking dahinter, Schriften davor). **Diese Kette bei jeder Änderung mitziehen** | Autor | Drift-Kandidat |
| 6 | **Abbildungen fehlen vollständig.** Für 12 Seiten sind null Abbildungen zu wenig. Drei Kandidaten: (a) Zeitstrahl Zertifikatslaufzeit mit der 30-Tage-Marke, (b) schematischer Seitenaufruf mit den kontaktierten fremden Servern, (c) Gegenüberstellung L3 / S4 als Zwei-Spalten-Schema. **(b) ist die wichtigste** — sie macht das unsichtbare Thema dieser Kategorie sichtbar | Gestaltung | **offen** |
| 7 | Begriffe: Das Kapitel benutzt „Sicherheitsheader" und nennt die vier bei ihren technischen Namen. Prüfen, ob das für die Zielgruppe tragbar ist oder ob die Namen in eine Marginalie gehören und im Fließtext umschrieben werden | Lektorat | offen |
| 8 | Kapitel 16 muss auflisten, was diese Kategorie nicht prüft: Zugangsverwaltung, Aktualisierungsstand, Sicherungen, Wiederherstellbarkeit. Abschnitt 6.9 verweist darauf | Autor | Folgekapitel |

**Abbildungen in diesem Kapitel:** 0 — siehe Punkt 6
**Marginalien:** 6
**Geschätzter Satzumfang:** 11–12 Seiten
