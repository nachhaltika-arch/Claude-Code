# Die Einwilligungsquote — gemessen am 17.09.2026

> **Antwort in einer Zahl: rund 3 %.** Von 353 echten Besuchern der Kampagnentage
> 14.–16.09. kommen bei Meta **12** an und bei GA4 **11**. Fassung 4 rechnet mit
> 60–75 %. Der Alarmwert des Prüfverfahrens liegt bei 20 %.
>
> Zwei voneinander unabhängige Portale, dieselbe Größenordnung. Das ist kein
> Ausreißer eines Tages.

Verfahren: `docs/kampagne/pruefverfahren.md`, Kennzahl „Einwilligungsquote".
Zeitraum 14.–16.09.2026 (Ortszeit, Meta rechnet in Berlin). Der 17.09. ist
*nicht erhoben* — der Tag war beim Messen nicht zu Ende.

---

## 1. Warum das überhaupt eine Messung und keine Ablesung ist

**Die Zustimmung steht in keinem unserer Protokolle.** Vor dem Messen geprüft,
nicht angenommen:

* Die Landingpage legt die Entscheidung in `localStorage['kpg-consent-v1']` ab
  und reicht sie per `postMessage` an das Widget. An keinen Server.
* `/api/widget/config` ruft das Widget **ohne** Einwilligungsprüfung auf
  (`audit-widget.html`, `loadConfig`) — deshalb taugt es als Nenner.
* Das einzige Feld, das die Zustimmung an uns meldet, ist `consent_tracking`
  in `POST /api/widget/audit`. Diese Anfrage gab es im Zeitraum **null Mal**.

**Folge:** Der Zähler kann nur aus den Portalen kommen, und die messen
zwangsläufig nur die, die zustimmen. Genau das ist hier die Frage.

---

## 2. Der Nenner — 353 echte Besucher

Aus den Render-Protokollen des Dienstes `srv-da30dg3bc2fs73fomi0g`, gefiltert
auf `GET /api/widget/config`, gezählt mit `scripts/kampagne-protokoll.py`
(sechs Abrufe, über die Log-ID entdoppelt, keine Zahl von Hand).

| Tag | Aufrufe roh | bereinigt | **echte Besucher** | abgezogen |
|---|---|---|---|---|
| 14.09. | 38 | 25 | **22** | 2 Bots, 12 eigene (`217.142.18.239`, `9.246.125.88`) |
| 15.09. | 117 | 99 | **69** | aus dem Befund vom 15.09. |
| 16.09. | 435 | 432 | **262** | 1 Bot (AdsBot-Google), 2 eigene (`9.246.125.88`) |
| | | | **353** | |

Der 16.09. trägt drei Viertel davon: **435 Aufrufe, 431 mobil, 264 verschiedene
IP-Adressen.** Die Kampagne hat an dem Tag fast das Vierfache des Vortags
gebracht.

---

## 3. Der Zähler — zweimal unabhängig

### GA4 (Statistik-Einwilligung), Property `websprint`, `G-LQ7X322YJF`

Bericht „Neu generierter Traffic", Kanal `Paid Social`. Zeitraum je Tag gesetzt
und die **Beschriftung gelesen**, nicht dem URL-Parameter geglaubt.

| Tag | Sitzungen gesamt | **Paid Social** |
|---|---|---|
| 14.09. | 3 | **1** |
| 15.09. | 9 | **6** |
| 16.09. | 8 | **4** |
| 14.–16.09. | 20 | **11** |

Die Summe der Einzeltage ergibt den Dreitageswert — die Reihe ist in sich
schlüssig. Schlüsselereignisse: **0,00** an allen drei Tagen.

### Meta (Marketing-Einwilligung), Werbekonto 361140094818155

Anzeigengruppe „Karussell | DE ab 25 | Auto-Platzierung", Zeitraum im Wähler
gesetzt, Beschriftung gelesen: **14.09.2026 bis 16.09.2026**.

| | |
|---|---|
| Ausgegebener Betrag | **42,45 €** |
| Impressionen | 4.023 (CPM 10,55 €) |
| Link-Klicks | **561** (CPC 0,08 €, CTR 13,94 %) |
| **Landingpage-Aufrufe** | **12** |
| Kosten je Landingpage-Aufruf | **3,54 €** |
| Ergebnisse (Website-Lead) | — |
| Zeitplan | 14.09.2026 – **fortlaufend** |

---

## 4. Das Ergebnis

| Kennzahl | Formel | Wert | Verfahren sagt |
|---|---|---|---|
| **Einwilligungsquote (GA4)** | 11 ÷ 353 | **0,031** | Alarm unter 0,20 |
| **Einwilligungsquote (Meta)** | 12 ÷ 353 | **0,034** | — |
| Durchlaufquote Klick → Besucher | 353 ÷ 561 | **0,63** | gut ab 0,60 |
| Kosten je echtem Besucher | 42,45 € ÷ 353 | **0,12 €** | — |
| Kosten je Besucher **laut Meta** | 42,45 € ÷ 12 | **3,54 €** | das 29-Fache |
| Leads | `POST /api/widget/audit` | **0** | Gegenprobe bestanden |

Je Tag, zur Prüfung auf Stabilität:

| Tag | Besucher | GA4 Paid Social | Quote |
|---|---|---|---|
| 14.09. | 22 | 1 | 0,045 |
| 15.09. | 69 | 6 | 0,087 |
| 16.09. | 262 | 4 | **0,015** |

Der Tag mit der größten Stichprobe hat die niedrigste Quote. Die Zahl wird
nicht besser, wenn mehr Verkehr kommt.

---

## 5. Was die Zahl für Fassung 4 bedeutet

Fassung 4 hängt an **einer** Schwelle: **25 Abschlüsse je Woche und
Anzeigengruppe**, sonst verlässt sie die Lernphase nicht. Gezählt wird von Meta,
also nur, was durch die Einwilligung kommt.

Bei **3,4 %** braucht es rund **735 echte** „Analyse gestartet" je Woche, damit
Meta 25 sieht. Zum Vergleich: In drei Tagen kamen 353 Besucher, also gut 820 in
der Woche — und davon fängt bisher **keiner** an.

> **Damit trifft Hebel 1 dasselbe Urteil, das Fassung 4 über das Lead-Ereignis
> gefällt hat, nur eine Stufe tiefer:** Auf ein Pixel-Ereignis optimiert,
> verlässt diese Anzeigengruppe die Lernphase bei dieser Einwilligungsquote in
> keinem Szenario. Nicht bei guter Kreation, nicht bei gutem Angebot, nicht bei
> verdichtetem Budget.
>
> Das ist **kein** Argument gegen den Wechsel des Optimierungsereignisses — ein
> flacheres Ereignis bleibt besser als ein zu tiefes. Es ist ein Argument dagegen,
> von dem Wechsel die Lernphase zu **erwarten** und das Budget danach zu planen.

Was daneben gilt und wenig Beachtung findet: **Die Vorderseite arbeitet.**
0,12 € je echtem Besucher und eine Durchlaufquote von 0,63 sind gute Werte.
Metas 3,54 € je Landingpage-Aufruf sind keine Geschäftszahl, sondern der Preis
der Sichtbarkeit — das 29-Fache dessen, was ein Besucher wirklich kostet.

---

## 6. Was die Zahl **nicht** sagt — und wie man das trennt

**„Einwilligungsquote" ist der Name der Kennzahl, nicht die Diagnose.** Die 3 %
messen, welcher Anteil der Besucher als Ereignis bei Meta und GA4 **ankommt**.
Drei Ursachen kommen dafür in Frage, und diese Messung trennt sie nicht:

1. Der Besucher lehnt im Dialog ab oder entscheidet gar nicht.
2. Ein Werbeblocker oder der Tracking-Schutz des Browsers hält das Skript an.
3. **Der In-App-Browser.** 431 von 435 Aufrufen am 16.09. waren mobil, ein
   großer Teil aus den Apps von Facebook und Instagram (`FB_IAB/FB4A`,
   `Instagram …`). Dort greifen eigene Beschränkungen.

Für die Lernphase ist die Ursache gleichgültig — die Wirkung ist dieselbe. Für
die **Reparatur** ist sie es nicht: Gegen (1) hilft der Dialog, gegen (3) hilft
nur eine serverseitige Messung.

**Trennbar wäre es mit einer kleinen Ergänzung:** die Entscheidung am Dialog an
den eigenen Server melden — nicht das Verhalten, nur „zugestimmt / abgelehnt".
Dann steht neben der Ankunftsquote die echte Zustimmungsquote, und die Differenz
ist der Blockier- und In-App-Anteil.

> Das ist ohnehin fällig: **Art. 7 Abs. 1 DSGVO verlangt, die Einwilligung
> nachweisen zu können.** Heute liegt sie ausschließlich im Browser des
> Besuchers — wir haben keinen Nachweis, nur ein `localStorage` auf fremden
> Geräten. Eine Zeile Nachweis erschlägt beide Fragen.

---

## 7. Eigene Fehler bei dieser Messung

1. **Der GA4-Wert für den 15.09. war falsch — mein eigener von gestern.**
   Am 16.09. notiert: 4 Paid-Social-Sitzungen. Heute meldet dieselbe Property
   für denselben Tag **6**. GA4 verarbeitet nach; wer am Folgetag misst, misst
   zu früh. `verlauf.csv` ist berichtigt. **Die Regel daraus:** Portalzahlen für
   „gestern" sind vorläufig, bis sie zwei Tage alt sind.
2. **Ich wollte die Einwilligung an `fbp` im iframe-Aufruf ablesen** — und das
   wäre falsch gewesen. Der Einbau-Block liest das `_fbp`-Cookie **einmal beim
   Laden**; gesetzt wird es aber erst vom Pixel, also erst **nach** der
   Zustimmung. Bei einem Erstbesucher ist es zu diesem Zeitpunkt nie da, und die
   Funktion läuft kein zweites Mal. `fbp` erreicht das Widget deshalb nur bei
   **Wiederkehrern**. Als Einwilligungssignal wäre es ein Zähler gewesen, der
   fast immer null meldet — und ich hätte 0 % gemessen statt 3 %.
   *(Die Anzeigenzuordnung hängt daran nicht: `fbclid` kommt aus der Adresszeile
   und wird immer durchgereicht.)*
3. **Metas Datumswähler, zweiter Anlauf.** Der erste Klick setzte 14.–15.09.,
   während die URL `date=2026-09-14_2026-09-15` trug und die Beschriftung nur
   „14.09.2026" sagte. Erst das Nachsehen in den beiden Datumsfeldern des
   Wählers brachte es auf 14.–16. Die Warnung im Prüfverfahren stammt vom
   16.09., und sie greift weiterhin: **Die Beschriftung gilt, nicht die URL.**

---

## 8. Was daraus zu tun ist

1. **Nicht am Optimierungsereignis entscheiden, ohne die Ursache zu trennen.**
   Nachweis der Einwilligung serverseitig aufzeichnen (Abschnitt 6) — klein,
   rechtlich ohnehin geschuldet, und es beantwortet die Frage endgültig.
2. **Den Bruch zwischen Seite und Formular weiter verfolgen.** Er ist die
   teurere Baustelle: 353 Besucher, 0 Anläufe. Der Ankersprung ist am 17.09.
   entlastet worden; offen bleiben die mobile Ansicht und der In-App-Browser.
3. **Metas eigene Zahlen nicht mehr zur Steuerung heranziehen.** Bei 12 Signalen
   in drei Tagen optimiert der Algorithmus auf Rauschen. Gesteuert wird an den
   eigenen Protokollen — so steht es schon im Prüfverfahren, jetzt mit einer
   Zahl dahinter.
4. **Zwei Nebenfunde, die David gehören:** Die Anzeigengruppe läuft
   „14.09.2026 – fortlaufend", also **ohne Enddatum** (Punkt 12 der Fassung 4
   ist damit offen, nicht erledigt). Und im Werbekonto steht
   **„Überprüfen und veröffentlichen (1)"** — eine unveröffentlichte Änderung
   liegt im Entwurf.
