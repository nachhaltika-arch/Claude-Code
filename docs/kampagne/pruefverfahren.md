# Prüfverfahren Kampagne — vier Portale und die eigenen Protokolle

> **Zweck:** jeden Morgen in zehn Minuten beantworten, *wo* die Kette bricht —
> nicht *ob* sie bricht. Das Verfahren ist aus dem 15.09. entstanden, an dem
> Metas Zahlen eine Diagnose nahelegten, die an den eigenen Protokollen
> gemessen falsch war (L-195).
>
> Ausgeführt wird es mit `/kampagne` (siehe `.claude/commands/kampagne.md`).

Alle Uhrzeiten in Ortszeit (CEST). Berichtszeitraum ist standardmäßig
**der Vortag, 00:00–24:00**.

---

## Die Regel, die über dem Ganzen steht

**Drei Klassen, nie zwei.** Jede Zahl ist entweder **gemessen**, **angenommen**
oder **nicht erhoben**. Eine nicht erhobene Zahl wird nie als `0` geschrieben —
weder in der Tabelle noch in `verlauf.csv` (dort bleibt das Feld leer). Eine
Null heißt: geprüft und nicht eingetreten.

Warum das hier zählt: Vier der fünf Trichterstufen hängen an der Einwilligung.
Wer eine einwilligungsgesteuerte Null für eine gemessene Null hält, repariert
am falschen Ende.

---

## 1. Der Trichter und die Quelle je Stufe

| # | Stufe | Zahl kommt aus | Klasse | Einwilligung nötig? |
|---|---|---|---|---|
| 1 | Impressionen | Meta Ads Manager | gemessen | nein |
| 2 | Link-Klicks | Meta Ads Manager | gemessen | nein |
| 3 | **echte Seitenaufrufe** | eigene Protokolle: `GET /api/widget/config` | **gemessen** | **nein** |
| 4 | Analyse begonnen | Meta `InitiateCheckout` / GA4 `begin_checkout` | gemessen, aber untere Schranke | **ja** |
| 5 | Lead | eigene Protokolle: `POST /api/widget/audit` | **gemessen** | ja (Formular) |
| 6 | Bericht / Kauf | Stripe, Auftragsmelder | gemessen | — |

**Stufe 3 ist der Anker des ganzen Verfahrens.** `/api/widget/config` ruft
jedes geladene Widget **genau einmal** — vor jeder Einwilligung, ohne Meta,
ohne GA4. Das ist die einzige Zahl im System, die einen Seitenaufruf wirklich
zählt.

### Zwei Zahlen, die *nicht* Stufe 3 sind

| Zahl | Was sie wirklich misst |
|---|---|
| Metas **„Landingpage-Aufrufe"** | Zustimmungen zum Pixel, nicht Aufrufe. Am 14./15.09.: Meta sagte **2**, die Protokolle sagten **≈ 71**. |
| GA4 **Sitzungen (Paid Social)** | ebenfalls einwilligungsgesteuert — untere Schranke, nie Stufe 3. |

Beide werden trotzdem notiert: Ihr **Verhältnis zu Stufe 3** ist die
Einwilligungsquote, und die ist eine eigene Kennzahl (siehe 3.).

---

## 2. Die Portale — was aus jedem geholt wird

### 2.1 Meta Ads Manager — Ausgabe und Vorderseite des Trichters
`https://adsmanager.facebook.com/adsmanager/manage/adsets/insights?act=361140094818155&business_id=128351871884970` (Zeitraum auf den Berichtstag stellen)

> **Falle, am 16.09. hineingetappt:** Der URL-Parameter `insights_date`
> **greift nicht** — die Tabelle blieb auf „Letzte 30 Tage" stehen und zeigte
> 23,74 € statt 11,65 €, also die Kampagnensumme statt des Tages. Der
> Zeitraum ist **im Wähler oben rechts** zu setzen (für den Vortag genügt
> „Gestern"), und danach ist die Beschriftung des Wählers zu **lesen**: Sie
> muss den Berichtstag nennen. Meta rechnet in der Zeitzone Berlin.

Zu holen: **Ausgabe (€)**, **Impressionen**, **Link-Klicks**, **CTR**, **CPC**,
**Landingpage-Aufrufe** (als Einwilligungszahl, siehe oben), **Ergebnisse**.

Die rechten Spalten (ab „Impressionen") liegen außerhalb des Bildes: Die
Tabelle waagerecht scrollen — das Mausrad bewegt sie kaum, die **Bildlaufleiste
unter der Zeile ziehen** wirkt.

Zusätzlich, und das ist der teure Teil: **Aufschlüsselung → Platzierung**
(Knopf „Aufschlüsselung" → „Platzierung"; danach liefert der Seitentext alle
Zeilen auf einmal).
Die Kampagne läuft als Advantage+-Leads-Kampagne, das **Audience Network lässt
sich nicht abwählen**. Am 14./15.09. kamen **40 von 68 Klicks** von dort,
Rewarded Video mit 16,9 % CTR und **null** Landungen. Diese Klicks sind bezahlt
und wertlos; sie gehören getrennt ausgewiesen, damit CTR und CPC nicht
schmeichelhaft aussehen.

> Was in Meta **nicht** geht (am 15.09. geprüft, nicht erneut versuchen):
> das Optimierungsziel einer veröffentlichten Anzeigengruppe ändern; das
> Audience Network abwählen; die Ziel-URL aus der Anzeigenvorschau holen.

### 2.2 GA4 — Kanäle und Ereignisse
`https://analytics.google.com/analytics/web/#/a168071143p553177486/reports/explorer` (Traffic Acquisition), Messstelle `G-LQ7X322YJF`

Zu holen: **Sitzungen je Kanal** (`Paid Social` ist die Kampagne, `Direct` und
`Organic Search` sind es nicht), und aus dem Ereignisbericht **`begin_checkout`**
und **`generate_lead`**.

> **Diese Property hat keinen Ereignisbericht.** Die Sammlung „Leads
> generieren" kennt nur Übersicht, Zielgruppen, Nutzergewinnung, Neu
> generierter Traffic, Leadgewinnung, Landingpage, Kohorten. `begin_checkout`
> einzeln ist dort **nicht** zu bekommen — nur die Ereignissumme. Bis eine
> Datenanalyse „Ereignisanzahl nach Ereignisname" angelegt ist, bleibt
> Stufe 4 *nicht erhoben*, und die Diagnose kann 3 → 4 nicht von 4 → 5 trennen.
> Der Bericht heißt `r=lifecycle-engagement-events`; diese Property leitet
> darauf zur Startseite um.

Fällt `Paid Social` auf null, während Stufe 3 Aufrufe zeigt, ist das **kein**
Verkehrsproblem, sondern ein Parameter- oder Einwilligungsproblem.

### 2.3 Leadinfo — Nebenspur, nicht Trichter
`https://portal.leadinfo.com/inbox/`

Zu holen: **Zahl erkannter Firmen** und die Namen der interessanten.
Leadinfo erkennt Besucher, die das Formular **nicht** ausgefüllt haben — die
Zahl gehört nicht in den Trichter (sonst wird doppelt gezählt), sondern
beantwortet eine andere Frage: *Kommt die richtige Sorte Betrieb an?*

**Bevor eine Leadinfo-Null etwas heißt, zwei Gegenproben:** steht der Zähler
in der *ausgelieferten* Seite (`curl` auf die Live-Adresse, nicht die
Repo-Datei), und kennt das Portal unter „Alle Zeiten" überhaupt Unternehmen?
Am 15.09. war beides ja — vier Unternehmen, das jüngste vom 09.09. —, also ist
die Null gemessen. Sie erklärt sich aus dem Verkehr: 95 von 117 Aufrufen mobil,
und Mobilfunkadressen tragen keine Firmenkennung.

Erkennt Leadinfo **Firmen**, während Stufe 5 null ist, liegt der Bruch am
Formular und nicht am Publikum. Erkennt es **Agenturen und Zufall**, liegt er
an der Zielgruppe.

### 2.4 Search Console — die langsame Spur
`https://search.google.com/search-console/performance/search-analytics?resource_id=https%3A%2F%2Fwebsprint.kompagnon.eu%2F`

Zu holen: **Klicks**, **Impressionen**, und die obersten Suchanfragen.

Das misst **nicht** die Kampagne — bezahlter Verkehr taucht hier nicht auf.
Es misst zwei andere Dinge, und beide sind morgens einen Blick wert:
ob die Seite überhaupt **indexiert** ist (Impressionen > 0), und ob die
Anzeigen **Markensuche** erzeugen (Anfragen mit „kompagnon" oder „websprint"
sind ein verzögerter Kampagneneffekt).

Search Console ist **tagesträge**: Zahlen für gestern sind oft noch nicht da.
Fehlende Tage sind *nicht erhoben*, nicht null.

### 2.5 Die eigenen Protokolle — Render, Dienst `kompagnon-backend-fra`
Dienst-ID `srv-da30dg3bc2fs73fomi0g` (Produktiv, Frankfurt).

| Gezählt wird | Bedeutung |
|---|---|
| `GET /api/widget/config` | Stufe 3, roh |
| … verschiedene IP-Adressen | Besucher statt Aufrufe |
| … davon Bots (User-Agent) | abziehen |
| … davon eigene Test-IPs | abziehen — **Liste siehe unten** |
| `POST /api/widget/audit` | Stufe 5 |
| Anteil mobil | Gerätebild ohne Einwilligung |

**Am 16.09. am Gegenstand geprüft** (ein Lauf über den 15.09.):

* Der Filter `path=/api/widget/config` auf `srv-da30dg3bc2fs73fomi0g` trifft.
* `startTime`/`endTime` nehmen den Zeitzonen-Versatz an (`2026-09-15T00:00:00+02:00`),
  die **zurückgegebenen Zeitstempel stehen in UTC** — 22:09 Z ist 00:09 CEST.
  Wer die Zeitstempel für Ortszeit hält, verschiebt den Tag um zwei Stunden.
* `clientIP` und `userAgent` stehen im Text der Zeile, nicht in den Labels;
  `statusCode`, `path` und `method` stehen in den Labels.
* Mehr als 100 Zeilen kommen seitenweise: `direction: forward`, dann
  `nextStartTime` als neue `startTime`. Wer die erste Seite für den Tag hält,
  zählt zu wenig.

**Gezählt wird mit `scripts/kampagne-protokoll.py`, nicht im Kopf.** Die
Protokollzeilen (ganze Antwort oder JSON-Lines) auf stdin, eigene IPs per
`--eigene-ip`. Ohne `--eigene-ip` bleibt `aufrufe_bereinigt` **leer** statt 0 —
das ist der Unterschied zwischen *nicht erhoben* und *gemessen und null*.

**Gegenprobe ist Pflicht.** Eine Null aus einem Filter kann auch ein
Messfehler sein. Bevor „0 Leads" gemeldet wird: derselbe Filter über einen
Tag mit bekannten Testläufen (12./13.09.) muss diese finden. Findet er sie
nicht, ist der Filter kaputt, nicht der Trichter.

**Eigene Test-IPs** (abzuziehen; beim ersten Lauf zu bestätigen und hier
einzutragen — bis dahin gilt die bereinigte Zahl als *angenommen*):

| IP | wem | Beleg | Stand |
|---|---|---|---|
| `9.246.125.88` | vermutlich David | 17 Aufrufe am 15.09., Mac-Desktop, 07:31–18:00 UTC; dieselbe Adresse schickte am 12.09. die `curl`-Testläufe | **unbestätigt** — bis David es sagt, ist jede Bereinigung *angenommen* |
| `91.41.13.88` | vermutlich David | Testläufe am 13.09. (Mac + `curl`) | unbestätigt, am 15.09. nicht aufgetreten |
| `217.142.18.239` | vermutlich David | Testläufe am 13.09. abends | unbestätigt, am 15.09. nicht aufgetreten |

Die Adressen wechseln (drei verschiedene an drei Tagen) — eine feste Liste
reicht also nicht. Wer morgens bereinigt, prüft die **häufigste IP mit
Desktop-Kennung** gegen diese Tabelle und fragt im Zweifel nach.

---

## 3. Die Kennzahlen, die daraus gerechnet werden

| Kennzahl | Formel | gut | Alarm |
|---|---|---|---|
| **Durchlaufquote Klick → Besucher** | Besucher bereinigt ÷ Link-Klicks | ≥ 0,6 | < 0,3 |
| **Einwilligungsquote** | GA4-Sitzungen (Paid Social) ÷ Besucher | ≥ 0,5 | < 0,2 |
| **Formularquote** | Stufe 4 ÷ Stufe 3 | _noch nicht erhoben_ | 0 bei n ≥ 30 |
| **Abschlussquote** | Stufe 5 ÷ Stufe 4 | ≥ 0,5 | < 0,25 |
| **Kosten je echtem Besucher** | Ausgabe ÷ Besucher bereinigt | — | — |
| **Kosten je Lead** | Ausgabe ÷ Stufe 5 | — | — |
| **Anteil Audience Network** | AN-Klicks ÷ Link-Klicks | < 0,3 | > 0,5 |

> **Aufrufe sind keine Besucher.** Am 15.09. standen **117 Aufrufe** gegen
> **94 Klicks** — eine Quote von 1,24, die nichts bedeutet, weil ein Besucher
> das Widget mehrfach lädt. Gegen **69 bereinigte Besucher** ergibt sich 0,73,
> und das ist die Zahl, die die Frage beantwortet. Deshalb rechnen alle
> Quoten oben mit Besuchern; `aufrufe_*` bleibt als Lastmaß daneben stehen.

**Die Formularquote hat bewusst keinen Sollwert.** Am 16.09. gibt es keine
Messung, aus der einer abzuleiten wäre; die erste Woche mit n ≥ 30 setzt ihn.
Ein erfundener Sollwert wäre eine angenommene Zahl in der Spalte „gemessen".

**Wochenmenge Leads** (für das Optimierungsziel der Anzeigengruppe):
unter **25** ist das Ziel zu eng gewählt, über **110** zu flach.

---

## 4. Die Diagnose — wo der Bruch liegt und was folgt

Von oben nach unten die erste Stufe nehmen, die reißt. Nur die.

| Bruch | Erkennbar an | Erster Verdächtiger | Was zu tun ist |
|---|---|---|---|
| **1 → 2** | CTR < 0,5 % außerhalb Audience Network | Motiv, Zielgruppe | Motive tauschen |
| **2 → 3** | Durchlaufquote < 0,3 | Ziel-URL, Anker `#analyse`, Ladezeit, Audience Network | Ziel-URL prüfen: stehen Metas Parameter **hinter** dem `#analyse`, springt der Anker ins Leere |
| **3 → 4** | Aufrufe da, `begin_checkout` = 0 bei n ≥ 30 | Formular sichtbar? Einwilligungsbanner? | Am Gerät nachstellen — mobil, im Facebook-In-App-Browser (`FBAN/FB4A`) |
| **4 → 5** | `begin_checkout` > 0, `audit` = 0 | Formularabbruch, Fehler beim Absenden | Protokoll auf 4xx/5xx auf `/api/widget/audit` |
| **5 → 6** | Leads da, kein Bericht | Zustellung, Doppel-Opt-in | `email_logs` **und** `communications` **und** Brevo prüfen — die zwei Protokolle kennen einander nicht |

**Kein Bruch erkennbar, aber die Zahlen sind klein:** dann ist die Menge das
Problem und nicht die Kette — erst ab n ≥ 30 auf Stufe 3 lohnt eine Diagnose
überhaupt. Darunter lautet das Ergebnis „zu wenig Daten", und das ist ein
gültiges Ergebnis.

---

## 5. Die drei Einzelprüfungen, solange die Kampagne jung ist

Nicht täglich zu rechnen, sondern beim **ersten vollständigen Durchlauf** zu
belegen (offen seit 15.09.):

1. **Ein `InitiateCheckout`, danach genau ein `Lead`** — nicht zwei. Zwei
   heißt Doppelauslösung.
2. **Trägt der Lead `fbc`?** Wenn nicht, wird das Pixelfeld des Widgets
   geleert (Prompt 02, Messpunkt A3).
3. **Wirkt der Anker?** Sichtbar an der Formularquote. Bleibt sie bei 0 von n,
   ist die zusammengesetzte Ziel-URL der erste Verdächtige.

---

## 6. Wohin das Ergebnis geht

| Datei | Inhalt |
|---|---|
| `docs/kampagne/JJJJ-MM-TT.md` | der Tagesbefund: Trichter, Kennzahlen, Diagnose, was bei David liegt |
| `docs/kampagne/verlauf.csv` | **eine Zeile je Tag** — leeres Feld heißt *nicht erhoben*, `0` heißt *gemessen und null* |

Die CSV ist der eigentliche Gewinn des Verfahrens: Ein einzelner Tag sagt
wenig, die Reihe sagt, ob eine Änderung gewirkt hat.
