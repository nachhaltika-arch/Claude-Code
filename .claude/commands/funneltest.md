---
description: Ein Lauf über den ganzen Trichter am laufenden System — von der Form des Anzeigenklicks bis zum ausgelieferten PDF
argument-hint: "[--staging] [--domain <adresse>] [--ohne-browser] [--weiter]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, ToolSearch, mcp__claude_ai_Gmail__search_threads, mcp__claude_ai_Gmail__get_thread, mcp__claude_ai_Gmail__get_message, mcp__render__list_logs, mcp__claude-in-chrome__tabs_context_mcp, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__get_page_text, mcp__claude-in-chrome__read_page, mcp__claude-in-chrome__computer, mcp__claude-in-chrome__find, mcp__claude-in-chrome__tabs_close_mcp
---

Fahre den Trichter **einmal ganz durch** und miss jede Stufe am laufenden
System. Das Werkzeug dazu ist `scripts/funnel-test.py`; dieser Befehl fügt
hinzu, was ein Skript nicht kann: die Anzeigenseite lesen und das Postfach.

Argumente: `$ARGUMENTS`. Leer heißt **produktiv**, Testdomain `nachhaltika.de`.
`--staging` läuft gegen die Staging-Umgebung, `--ohne-browser` überspringt
Schritt 1, `--weiter` setzt einen angefangenen Lauf fort (Zustand liegt in
`.funneltest/`).

## Was dieser Lauf kostet, und warum er trotzdem läuft

Produktiv entstehen **eine echte Anfrage, ein Lead, zwei Mails und ein
Brevo-Kontakt**, und die Analyse verbraucht einen PageSpeed-Aufruf. Aufgeräumt
wird nichts (Entscheidung David, 20.09.2026) — der Bericht nennt am Ende die
Nummern. Das Kontingent liegt bei **15 Anfragen je IP und Tag**,
3 je Adresse; die Testadresse trägt deshalb das Datum als `+Alias`.

**Ein echter Klick auf die eigene Anzeige gehört nicht dazu.** Er kostet Geld
und färbt CTR und Landingpage-Aufrufe. Stufe 1 liest nur; Stufe 2 baut die
**Form** eines Anzeigenklicks nach (fbclid + fünf UTM-Felder).

## Regeln für den ganzen Lauf

* **Drei Klassen, nie zwei:** gemessen / angenommen / nicht erhoben. Was nicht
  erhoben wurde, ist **nie** „in Ordnung" und nie eine Null.
* **Zwei Fehlversuche je Quelle**, dann melden und weitermachen. Eine fehlende
  Quelle macht den Lauf nicht wertlos.
* **Nenne am Ende die erste Stufe, die reißt — nur die.** Was dahinter liegt,
  ist Folge, nicht Befund.
* **Links aus Mails führen über Brevo, nicht direkt zu uns.** Beide Links
  stehen als Klickzähler in der Mail (`…sendibt2.com/tr/cl/…`, beim nächsten
  Lauf `sendibt3.com` — **der Wirt wechselt**), am 20.09.2026 am echten Lauf
  gesehen. Die Prüfung lautet deshalb **nicht** „steht unsere
  Domain im Link", sondern: Der Zähler gehört zu Brevo, und die Adresse, auf
  der die Weiterleitung **landet**, muss `api.kompagnon.group` sein
  (produktiv) bzw. `kompagnon-backend-staging.onrender.com`. Das Skript weist
  sie als Beleg aus. Landet sie woanders, ist das ein Befund — dann nicht
  weiterklicken, sondern melden.
* **Nicht pushen.** Committen ja, pushen nur auf Ansage (CLAUDE.md).

## Schritt 1 — Stufe 1: Läuft die Anzeige überhaupt? (Chrome)

Ohne `--ohne-browser`. Erst `tabs_context_mcp`, dann ein **neuer** Tab auf
`https://adsmanager.facebook.com/adsmanager/manage/adsets?act=361140094818155&business_id=128351871884970`

Zu holen: **Status der Anzeigengruppe** (Aktiv / Deaktiviert / In Prüfung),
**Auslieferung**, und die heutigen Impressionen und Link-Klicks.

> **Der Zeitraum steht im Wähler oben rechts, nicht in der URL.** Der Parameter
> `insights_date` wird stillschweigend verworfen — am 16.09. standen deshalb
> 23,74 € statt 11,65 € im Bericht. Nach dem Umstellen die **Beschriftung des
> Wählers lesen**, bevor eine Zahl übernommen wird.

Antwortet die Erweiterung nicht oder ist die Sitzung abgelaufen: **nicht
dreimal versuchen** — Stufe 1 als *nicht erhoben* führen und weiterlaufen.
Der Rest des Tests hängt nicht daran.

## Schritt 2 — Stufen 2 bis 6: Seite, Widget, Lead, Analyse

    kompagnon/backend/venv/bin/python scripts/funnel-test.py start [--ziel staging] [--domain …]

Das Skript ruft die Landingpage mit der Klick-URL auf, vergleicht sie mit der
Repo-Fassung, liest `/api/widget/config` und die ausgelieferte Widget-Datei,
schickt das Formular ab und wartet auf die Analyse (bis 300 s).

**Nimm die Ausgabe nicht als Ergebnis, sondern lies sie.** Zwei Zeilen sind
bekannte Nicht-Befunde und dürfen nicht als Fehler gemeldet werden:

* **Staging hat keine eigene Landingpage** — die Seite liegt bei Mittwald.
* **Ein zweiter Lauf auf dieselbe Domain legt keinen neuen Lead an**: Der Lead
  wird über die Domain wiederverwendet, UTM-Felder werden nie überschrieben
  (Erstkontakt gewinnt, 15.09.2026).
* **Auf Staging sind Pixel, Serverweg und Check PLUS nicht eingerichtet**
  (`pixel_id` leer, `meta.bereit=None`, `verfuegbar=False`, am 20.09.2026
  gemessen). Das ist die Einrichtung dieser Umgebung, kein Mangel — und
  deshalb führt das Skript den Kaufweg auf der Berichtsseite dort als *nicht
  erhoben* statt als fehlend.

Bricht das Skript mit **429** ab, ist das Kontingent erschöpft — das ist eine
*nicht erhobene* Stufe 5, kein Systemfehler. Dann mit einer anderen Testdomain
oder am Folgetag.

## Schritt 3 — Stufe 7: Kommt Mail 1 an?

Gmail nach der Testadresse durchsuchen (sie steht in der Ausgabe von
Schritt 2 und im Zustand unter `.funneltest/`):

    search_threads: to:<Testadresse>

**Zwei Zahlen, nicht eine:** ob die Mail da ist **und** wie lange sie
gebraucht hat (Absendezeit des Formulars steht im Zustand unter `begonnen`).
Ist nach **fünf Minuten** nichts da, noch einmal nachsehen; danach als *nicht
erhoben* führen und Schritt 4 überspringen — nicht als „Mail kommt nicht an"
melden, bevor die Render-Protokolle in Schritt 7 dazu befragt sind.

Aus der Mail den Bestätigungslink holen (`/api/widget/verify/<token>`), den
Wirt prüfen (siehe Regeln), und mitnehmen, ob die Mail den **Abmeldelink**
trägt.

## Schritt 4 — Stufe 8: Der Klick

    …/python scripts/funnel-test.py bestaetigen --link <Link aus Mail 1>

Das Skript ruft die Seite auf, liest den signierten Gestenbeleg, **wartet die
Mindestverweildauer ab** und schickt das Formular.

> Damit ist die **Mechanik** der Bestätigung geprüft, nicht der Schutz vor
> Postfach-Scannern — der ist genau das, was hier maschinell umgangen wird.
> Schritt 7 liest deshalb `bestaetigung_verdaechtig` zurück: Ein **Ja** ist
> hier das erwartete Ergebnis und kein Mangel.
>
> **Wie der Schutz gebaut ist, und warum das Skript ihn zweimal missverstand**
> (20.09.2026): Das Feld `nachweis` wird **leer** ausgeliefert; den Wert trägt
> der Knopf als `data-nachweis`, und nur ein Ereignis mit `isTrusted === true`
> kopiert ihn hinein. Wer im Quelltext nach `value="…"` sucht, findet nichts
> und hält den Schutz für einen Defekt. Und die Erfolgsseite enthält das Wort
> „bestätigt" **nicht** — sie sagt „Wir haben Ihnen gerade eine zweite E-Mail
> geschickt". Maßgeblich ist deshalb, ob das Formular zurückkommt, nicht der
> Wortlaut.

## Schritt 5 — Stufe 9: Kommt Mail 2?

Wie Schritt 3, mit demselben Suchbegriff. Daraus den Berichtslink holen
(`/api/widget/report/<token>`), Wirt prüfen, Laufzeit seit dem Klick messen.

## Schritt 6 — Stufen 10 und 11: Bericht und PDF

    …/python scripts/funnel-test.py bericht --link <Link aus Mail 2>

Gemessen werden Berichtsseite (Antwort, Größe, Angebot, Kaufweg) und das
ausgelieferte PDF: `%PDF`-Kopf, Seitenzahl, und die **Kopfzeile** — reines
ASCII und beide Namensformen nebeneinander. Das ist der Fund vom 12.09., und
er war nur am ausgelieferten PDF zu sehen, nicht am Test.

## Schritt 7 — Stufe 12: Die zweite Sicht

    …/python scripts/funnel-test.py stand

Liest `/api/acquisition/widget/requests` zurück — die Zustandsmaschine der
Anfrage aus Sicht des Servers: `verify_sent`, `verified`, `report_sent`,
`report_opened`, `analyse_status`. **Das ist die unabhängige Gegenprobe zu
allem, was oben gemessen wurde.** Weichen beide Sichten ab, gilt die des
Servers, und die Abweichung gehört in den Bericht.

Braucht Zugangsdaten:

    export FUNNELTEST_KONTO=…   FUNNELTEST_WORT=…

Fehlen sie, läuft die Stufe nicht und gilt als **nicht erhoben** — nicht als
in Ordnung.

Dazu, produktiv, aus den Render-Protokollen (`mcp__render__list_logs`, Dienst
`srv-da30dg3bc2fs73fomi0g`, Zeitraum des Laufs):

1. **Brevo** — steht zur Anfrage eine Übertragungszeile? Genau **eine**
   Abwesenheit ist die Signatur des stillen Abbruchs: weder Erfolg noch
   Misserfolg heißt, die Listen-ID fehlt (Fund vom 17.09.).
2. **Meta CAPI** — wurde `Lead` serverseitig gemeldet, oder steht die Warnung
   „kein Token oder keine Pixel-ID"? Die Ereigniskennung des Laufs steht im
   Zustand.
3. **Fehlerzeilen** im Zeitraum, die zu dieser Anfrage gehören.

## Schritt 8 — Ausgeben, ablegen, committen

Im Terminal: die Stufentabelle, **ein** Diagnosesatz (erste reißende Stufe),
und was bei David liegt.

Dann `docs/funneltest/JJJJ-MM-TT-HHMM.md` schreiben:

* Kopf: Ziel, Testadresse, Testdomain, Lauf-Kennung, Gesamtdauer.
* Die Stufentabelle mit Klasse und Beleg je Zeile.
* **„Was ich nicht messen konnte"** samt Grund — Pflichtabschnitt.
* Die Nummern, die stehen bleiben: Anfrage-ID, Lead, Audit-ID.
* **Jeder Befund des Laufs gehört ins Lagebild** — berührt er eine `L-`Nummer,
  dort nachtragen; hat er noch keine, bekommt er eine neue. Verfahren, Format
  und vier Fallen stehen in `CLAUDE.md`, Abschnitt „Jeder Fund kommt ins
  Lagebild". Danach `scripts/lagebild-bauen.py` laufen lassen und das Artifact
  an derselben URL aktualisieren.

**Keine Token in den Bericht.** `poll_token` und `verify_token` geben Zugang
zu einem fremden Bericht; sie bleiben in `.funneltest/`, das per `.gitignore`
außerhalb der Versionsverwaltung liegt.

Zum Schluss committen, deutsch: `test(funnel): …` mit dem Befund im Betreff.
**Nicht pushen.**

## Wenn etwas hängt

Der Zustand liegt in `.funneltest/lauf-<kennung>.json`; jede Phase kann
einzeln wiederholt werden (`--lauf <kennung>`). Ein abgebrochener Lauf
blockiert nichts — er hinterlässt eine Anfrage ohne Bestätigung, und die
verfällt von selbst.
