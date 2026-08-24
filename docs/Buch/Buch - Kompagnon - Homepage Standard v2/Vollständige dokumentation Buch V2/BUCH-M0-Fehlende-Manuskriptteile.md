# BUCH-M0 — Die drei fehlenden Manuskriptteile

**Aufwand:** 1 Stunde Suche, danach offen · **Ein Commit** · **Kann jederzeit laufen, sollte früh laufen**

---

## Was hier passiert und warum

Der `RESTARBEITEN-REPORT.md` sagt in Zeile 4: *„Manuskript: 18 Dateien, 48.094 Wörter."* und in der Kurzfassung: *„Das Manuskript ist inhaltlich vollständig."*

Nachgemessen:

```bash
ls docs/Buch/"Buch - Kompagnon - Der Homepage Standard"/*.md | grep -v RESTARB | wc -l   # 15
wc -w docs/Buch/"Buch - Kompagnon - Der Homepage Standard"/{0,1,9}*.md | tail -1          # 43.810
```

**15 Dateien, 43.810 Wörter. Es fehlen drei Dateien und 4.284 Wörter.**

| Fehlt | Belegt durch |
|---|---|
| **Kapitel 14 — Grenzen des Selbermachens** | Verweise in `01-warum.md` (2×), `02-das-system.md`, `07-seo.md`, `10-inhalt.md`, `90-anhang-glossar.md`. Der Report zitiert Abschnitt **14.4** |
| **Anhang B — Schwellentabellen** | Report D3, D8, D9 — beschreibt Inhalt und Platzierung im Detail |
| **Anhang C — Vorlagen 1–5** | Report D9, D10, D11 — nennt einzelne Vorlagen und eine Sicherungsregel dazu |

Ein Buch mit fünf Querverweisen auf ein nicht existierendes Kapitel geht nicht in Druck. Und `BUCH-F2` erzeugt Tabellen für Anhang B — **ein Export braucht ein Ziel.**

Das ist genau der Fehlertyp, vor dem die Projektanweisung warnt: Eine Überschrift („inhaltlich vollständig") passt nicht mehr zum Inhalt. Der Report ist deshalb nicht wertlos — er ist nur an dieser Stelle nicht nachgemessen worden.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `origin` → `https://github.com/nachhaltika-arch/Claude-Code`, Branch → `staging`.
Stimmt eines nicht: sofort stoppen, melden, nichts ausführen.

---

## Schritt 1 — Die Suche ist bereits erledigt

**Nicht noch einmal suchen.** Am 24.08.2026 wurden beide Ablagen vollständig durchsucht:

**Git — alle 1.537 Commits, alle Branches, auch gelöschte Stände:**

```bash
git log --all --pretty=format: --name-only --diff-filter=A -- "docs/Buch/*" | sort -u
git grep -l "Grenzen des Selbermachens" $(git rev-list --all) -- "docs/Buch/*"
```

Ergebnis: **null Treffer.** Die drei Dateien wurden nie committet — sie sind nicht gelöscht worden, sie waren nie da. Die 244 Treffer für „Anhang B" und „Vorlage 3" stammen ausnahmslos aus `RESTARBEITEN-REPORT.md` über 244 Commits hinweg, also aus der Datei, die sie *beschreibt*.

**Google Drive — Volltext und Titel:**

```
fullText contains 'Grenzen des Selbermachens'   → 0 Treffer
title contains 'Selbermachens' / 'anhang'        → nichts Einschlägiges
```

**Wie das Manuskript ins Repo kam** — fünf Commits am 14.08.2026, in dieser Reihenfolge:

| Commit | Dateien |
|---|---|
| `d6a27d3` | Kapitel 1–8 |
| `64fed23` | Kapitel 9–10 |
| `7572453` | Kapitel 11 |
| `99813f0` | Kapitel 12–13 |
| `8081dcd` | Anhang A (Glossar) |
| `79a291e` | Titelei **und** `RESTARBEITEN-REPORT.md` |

Der Report kam **zuletzt** — als alle anderen Dateien bereits im Repo lagen — und zählte trotzdem 18 Dateien und 48.094 Wörter. Er beschreibt außerdem Details, die man nur nennt, wenn man die Dateien vor sich hat: dass die P3-Zeile in Anhang B durch leere Felder wie ein Fehler wirkt, dass Vorlage 1 und 2 je auf eine Seite müssen, dass Vorlage 3 keine Passwortfelder bekommen darf.

**Daraus folgt:** Die drei Dateien existierten am 14.08. sehr wahrscheinlich außerhalb des Repos, und die letzte Übertragung ist abgebrochen. Der wahrscheinlichste Ort ist der lokale Rechner oder die Ablage, aus der die anderen 15 Dateien stammen.

**Stopp-Punkt 1: Frage zuerst nach, bevor du irgendetwas schreibst.** Nur wenn feststeht, dass die drei Dateien nirgends mehr liegen, geht es mit Schritt 2 weiter. 4.284 Wörter neu zu schreiben, die es schon gibt, ist der teuerste Fehler in diesem ganzen Vorhaben.

---

## Schritt 2 — Nur wenn nichts gefunden wurde: Gerüste anlegen, nicht Text erfinden

**Schreibe die drei Dateien nicht aus.** Ein KI-geschriebenes Kapitel 14 neben dreizehn selbstgeschriebenen fällt im Lektorat auf, und bei einem Buch, dessen Verkaufsargument Autorität ist, ist das ein Eigentor.

Lege stattdessen Gerüste an, die genau die Stellen benennen, die gefüllt werden müssen — abgeleitet **aus den vorhandenen Querverweisen**, nicht aus einer Vermutung.

**2a — `14-grenzen.md`.** Sammle zuerst, was die anderen Kapitel diesem Kapitel versprechen:

```bash
grep -rn -B3 -A3 "Kapitel 14" docs/Buch/"Buch - Kompagnon - Der Homepage Standard"/*.md
```

Vier Versprechen sind bereits bekannt und müssen als Abschnitte auftauchen:

| Versprochen in | Was Kapitel 14 einlösen muss |
|---|---|
| `01-warum.md:106` | die für Menschen unsichtbaren Merkmale, zusammen mit Kapitel 7 |
| `01-warum.md:323` | „Nicht alles in diesem Buch können Sie selbst…" — die eigentliche Kapitelthese |
| `02-das-system.md:486` und `07-seo.md:289` | der GEO-Wert und warum er außerhalb der Wertung steht |
| `10-inhalt.md:120` | maschinelle Auswertbarkeit von Text |
| Report, C8 | Abschnitt **14.4**: neue Websites fallen bei der Einwilligung überdurchschnittlich durch |

Front-Matter wie in den anderen Dateien, `status: gerüst`:

```markdown
---
kapitel: 14
titel: "Grenzen des Selbermachens"
status: geruest
zuletzt_geprueft: 2026-08-24
standard_version: "2026.2"
---
```

**2b — `91-anhang-b-schwellen.md`.** Reines Zielgefäß für den Export aus `BUCH-F2`. Kein Fließtext — eine Einleitung von drei Sätzen und darunter der Platzhalter, den das Skript befüllt:

```markdown
<!-- ERZEUGT: docs/Buch/generiert/anhang-schwellen.md — nicht von Hand pflegen -->
```

Beachte aus dem Report: **D8** — die P3-Zeile wirkt durch leere Felder wie ein Fehler; **D9** — Anhang B und Vorlage 5 konkurrieren um die Umschlaginnenseite. Beides als Kommentar vermerken, nicht entscheiden.

**2c — `92-anhang-c-vorlagen.md`.** Fünf Vorlagen, laut Report:

- Vorlage 1 und 2 müssen **je auf eine Seite** passen, damit sie heraustrennbar sind (D10)
- **Vorlage 3 darf keine Passwortfelder bekommen** (D11) — das ist eine Sicherungsregel, keine Gestaltungsfrage. Sie gehört als Kommentar **in die Datei**, nicht nur in den Report, sonst geht sie beim Satz verloren
- Vorlage 5 konkurriert mit Anhang B um die Umschlaginnenseite (D9)

---

## Schritt 3 — Den Report korrigieren

Der `RESTARBEITEN-REPORT.md` behauptet einen Zustand, den er nicht hat. Trage die Messung ein:

```markdown
**Manuskript:** 15 Dateien, 43.810 Wörter im Repo (Stand 24.08.2026, nachgemessen).
Die Kopfzeile nannte 18 Dateien und 48.094 Wörter — Kapitel 14, Anhang B und Anhang C
fehlen als Dateien. Siehe `BUCH-M0`.
```

Und in der Kurzfassung den Satz *„Das Manuskript ist inhaltlich vollständig"* ersetzen durch das, was gilt.

---

## Schritt 4 — Verbindungs-Check

Hier hat er eine ungewöhnliche, aber passende Form:

| Ebene | Prüfung |
|---|---|
| Der Wert existiert | die drei Dateien liegen im Ordner |
| Etwas liefert ihn aus | die Querverweise „Kapitel 14" zeigen auf eine existierende Datei |
| Es gibt eine Adresse dafür | Anhang B hat einen Platzhalter, den `BUCH-F2` befüllen kann |
| Sichtbar | ein Inhaltsverzeichnis über alle Dateien ist lückenlos |

```bash
ls docs/Buch/"Buch - Kompagnon - Der Homepage Standard"/*.md | grep -v RESTARB
grep -rn "Kapitel 14" docs/Buch/"Buch - Kompagnon - Der Homepage Standard"/*.md | wc -l
```

---

## Schritt 5 — Commit und Push

```bash
git add docs/Buch/
git commit -m "docs(buch): chapter 14 and appendices B and C exist as files now"
git push origin staging
```

---

## Stopp-Punkt 2

Melden mit:

1. Welcher der drei Ausgänge aus Schritt 1 eingetreten ist
2. Falls Gerüste angelegt wurden: geschätzter Schreibaufwand je Datei
3. Ob beim Durchsehen der Querverweise weitere Versprechen an Kapitel 14 auftauchen, die oben nicht stehen
4. Ob noch weitere Verweise ins Leere zeigen — etwa auf Abschnittsnummern, die es nicht gibt
