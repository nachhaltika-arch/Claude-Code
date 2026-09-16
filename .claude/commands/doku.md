---
description: Tagesdokumentation nach der Hausform schreiben — Muster, Funde mit Beleg, eigene Fehler, was bei David liegt
argument-hint: "[heute | JJJJ-MM-TT]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

Schreibe die Tagesdokumentation für `$ARGUMENTS` (leer = **heute**) nach
`docs/tagesdokumentation/JJJJ-MM-TT.md`.

**Lies zuerst `docs/tagesdokumentation/README.md`** — die Konventionen gelten
vor diesem Befehl. Und sieh dir die **zwei jüngsten** Berichte im Ordner an,
nicht wegen des Inhalts, sondern wegen der Form: Tonfall, Tiefe, Tabellenbau.

## Die vier Regeln, die den Bericht tragen

1. **Keine Commit-Liste.** Die steht im Verlauf. Hierher gehört, *was sich
   geändert hat und warum*, in ganzen Sätzen.
2. **Zahlen werden gemessen, nicht erinnert.** Jede Zahl im Bericht stammt aus
   einem Befehl, den du in dieser Sitzung ausgeführt hast — nicht aus dem
   Gedächtnis, nicht aus einem älteren Bericht, nicht aus dem Lagebild-Fließtext.
   Wenn du eine Zahl nicht messen kannst, schreib **nicht erhoben** hin.
3. **Die eigenen Fehler sind Pflichtteil, kein Anhang.** Was falsch gemessen,
   zu früh gemeldet oder auf einer Annahme gebaut wurde, kommt in den Bericht —
   samt der Messung, die es aufgedeckt hat. Ein Tag ohne Abschnitt „Eigene
   Fehler" ist unvollständig; gab es wirklich keinen, dann steht dort, **woran**
   das geprüft wurde.
4. **Jeder Fund braucht einen Beleg.** Datei und Zeile, ein Statuscode, eine
   Protokollzeile, ein CI-Lauf, eine Messung mit Uhrzeit. „Sieht richtig aus"
   ist kein Beleg.

## Schritt 1 — Material sammeln (messen, nicht erinnern)

Der **Sitzungsverlauf** sagt, *was* passiert ist und *warum*. Die Zahlen kommen
aus dem Repo. Deckt die Sitzung den Tag nicht ganz ab (etwa nach `/clear`),
dann schreib das in den Bericht, statt die Lücke zu füllen.

```
git log --since="<Tag> 00:00" --until="<Tag> 23:59" --format="%h %ad %s" --date=format:%H:%M
git log --since=… --until=… --stat --format="== %h %s"
git log --since=… --until=… --format=%s%n%b | grep -oE "L-[0-9]+" | sort -u
git rev-list --count origin/staging..staging        # wie viele Commits lokal warten
gh run list --branch staging --limit 5              # CI: grün oder rot, mit Nummer
git status --short
```

Dazu, wo der Tag es hergibt: Render-Protokolle, Live-Messungen (`curl -sI`),
Testläufe. **Was du im Bericht behauptest, misst du vorher** — auch dann,
wenn es gestern noch stimmte.

## Schritt 2 — Die Form

```
# KOMPAGNON — Tagesdokumentation TT.MM.JJJJ

> Kernsatz des Tages: was sich geändert hat, in zwei bis drei Sätzen.
>
> **Die Lehre des Tages: <ein Satz>.** Die eine Sache, die beim nächsten Mal
> anders gemacht gehört — abgeleitet aus dem, was heute schiefging.

Alle Uhrzeiten in Ortszeit (CEST), sofern nicht anders vermerkt.

## Das Muster des Tages
<Tabelle: was gemessen/getan wurde | was gesucht/gemeint war | Folge>

## 1..n <Die Funde, je einer je Abschnitt, mit Beleg>

## Eigene Fehler
<nummeriert; je Fehler: was behauptet, was tatsächlich, wodurch aufgedeckt>

## Was bei David liegt
<was er entscheiden oder tun muss; getrennt nach „heute" und „sobald X">

## Zahlen
<die gemessenen Kennzahlen des Tages, mit Herkunft>
```

Die Überschriften 1..n benennen den **Fund**, nicht den Bereich: „Der Anker
sprang ins Leere" statt „Landingpage".

## Schritt 3 — Schreiben

Gibt es die Datei schon, **ergänze sie** — nie überschreiben. Ein zweiter Lauf
am selben Tag setzt fort, was der erste festgehalten hat.

Danach zwei Gegenprüfungen:

* **Trägt jede Zahl einen Beleg?** Geh den Bericht durch und streiche oder
  belege jede, die nur behauptet ist.
* **Ist im Tag eine Lücke aus dem Lagebild berührt worden** (eine `L-`Nummer in
  einem Commit)? Dann gehört sie in `docs/soll-ist-analyse.md` § 3
  fortgeschrieben, und danach läuft `python3 scripts/lagebild-bauen.py`.
  Das Lagebild von gestern sieht aus wie eines von heute.

## Schritt 4 — Ablegen

Committen, deutsch: `docs: Tagesdokumentation für den TT.MM.JJJJ`.
Der Rumpf sagt in zwei, drei Sätzen, was der Tag gebracht hat — auch hier
gehören die eigenen Fehler hinein.

**Nicht pushen** (CLAUDE.md). Zum Schluss melden, **wie viele Commits lokal
warten** — die Entscheidung zu pushen gehört David.
