---
description: Morgen-Auswertung der Kampagne über Meta, GA4, Leadinfo, Search Console und die eigenen Protokolle
argument-hint: "[gestern | JJJJ-MM-TT | JJJJ-MM-TT..JJJJ-MM-TT]  [--ohne-browser]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, ToolSearch, mcp__render__list_logs, mcp__render__get_service, mcp__claude-in-chrome__tabs_context_mcp, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__get_page_text, mcp__claude-in-chrome__read_page, mcp__claude-in-chrome__computer, mcp__claude-in-chrome__find, mcp__claude-in-chrome__tabs_close_mcp
---

Werte die laufende Websprint-Kampagne aus. Das Verfahren steht in
`docs/kampagne/pruefverfahren.md` — **lies es zuerst**, es gilt vor diesem
Befehl, wenn beide sich widersprechen.

Zeitraum: `$ARGUMENTS`, leer bedeutet **gestern, 00:00–24:00 Ortszeit (CEST)**.
`--ohne-browser` überspringt Schritt 2 und fragt die Portalzahlen bei David ab.

## Regeln, die für den ganzen Lauf gelten

* **Drei Klassen, nie zwei:** gemessen / angenommen / nicht erhoben. Eine nicht
  erhobene Zahl wird **nie** als `0` ausgewiesen — in der CSV bleibt das Feld leer.
* **Nichts schätzen.** Steht eine Zahl nicht auf dem Schirm, ist sie nicht erhoben.
* **Kein Portal ist die Wahrheit über Stufe 3.** Metas „Landingpage-Aufrufe" und
  GA4-Sitzungen hängen an der Einwilligung; echte Aufrufe zählt nur `/api/widget/config`.
* Zahlen erst rechnen, wenn alle Quellen da sind — keine Zwischenmeldung als Ergebnis nehmen.

## Schritt 1 — Eigene Protokolle zuerst (ohne Browser, immer)

Über `mcp__render__list_logs`, Dienst `srv-da30dg3bc2fs73fomi0g`
(`kompagnon-backend-fra`, Produktiv), im Berichtszeitraum:

1. `GET /api/widget/config` — Aufrufe **roh**, verschiedene IP-Adressen,
   Anteil mobil, Bots (User-Agent), eigene Test-IPs laut Tabelle in
   `pruefverfahren.md` §2.5. Ergebnis: **Stufe 3 roh** und **bereinigt**.
   Die Zeilen in eine Datei im Scratchpad schreiben und mit
   `scripts/kampagne-protokoll.py --eigene-ip <IP> < datei.json` zählen —
   **nicht im Kopf zählen**. Zeitstempel der Antwort sind UTC; über 100 Zeilen
   seitenweise mit `direction: forward` und `nextStartTime` holen.
2. `POST /api/widget/audit` — **Stufe 4, „Analyse gestartet"**. Seit dem
   21.09.2026 trägt dieser Aufruf **keine E-Mail-Adresse** mehr und ist damit
   kein Lead; wer ihn als einen zählt, hält jeden Besucher für einen Abschluss.
   Statuscodes mitnehmen: 4xx/5xx auf diesem Pfad sind der Befund für den
   Bruch 3 → 4.
3. `POST /api/widget/bericht-anfordern/…` — **Stufe 5, der Lead**. Hier gibt
   jemand seine Adresse her; von hier läuft die Mailstrecke an. Der Bruch
   4 → 5 heißt: Punktwert gesehen, Adresse nicht hergegeben.
4. **Gegenprobe (Pflicht, bevor eine Null gemeldet wird):** derselbe Filter über
   den 12. oder 13.09. muss die bekannten Testläufe finden. Findet er sie nicht,
   ist der Filter kaputt — dann das melden und **nicht** den Trichter.

Ist eine Test-IP-Zeile in `pruefverfahren.md` noch `_offen_`, nenne die
Kandidaten (IPs mit auffällig vielen Aufrufen oder Zugriffen auf Admin-Pfade)
und frage David **einmal** nach Bestätigung; danach trag sie dort ein. Bis
dahin gilt die bereinigte Zahl als **angenommen**.

## Schritt 2 — Die vier Portale (Chrome)

Erst `tabs_context_mcp`, dann je einen **neuen** Tab. Antwortet die Erweiterung
nicht oder ist eine Sitzung abgelaufen: **nicht dreimal versuchen** — melden,
auf `--ohne-browser` umschalten und David den Zahlenblock eintippen lassen.

1. **Meta** — `https://adsmanager.facebook.com/adsmanager/manage/adsets/insights?act=361140094818155&business_id=128351871884970`
   Zeitraum auf den Berichtstag stellen. Ausgabe €, Impressionen, Link-Klicks,
   CTR, CPC, Landingpage-Aufrufe (= Einwilligungen, nicht Aufrufe), Ergebnisse.
   Dann **Aufschlüsselung → Platzierung**: Klicks aus dem Audience Network
   getrennt ausweisen (nicht abwählbar, am 15.09. 40 von 68 Klicks, null Landungen).
2. **GA4** — `https://analytics.google.com/analytics/web/#/a168071143p553177486/reports/explorer`
   Sitzungen je Kanal (`Paid Social` = Kampagne), dazu `begin_checkout` und
   `generate_lead` aus dem Ereignisbericht.
3. **Leadinfo** — `https://portal.leadinfo.com/inbox/` — Zahl erkannter Firmen
   und die Namen der interessanten. Nebenspur, **nicht** in den Trichter rechnen.
4. **Search Console** — `https://search.google.com/search-console/performance/search-analytics?resource_id=https%3A%2F%2Fwebsprint.kompagnon.eu%2F`
   Klicks, Impressionen, oberste Suchanfragen. Tagesträge: fehlende Tage sind
   *nicht erhoben*. Auf Markensuche achten („kompagnon", „websprint") — das ist
   der verzögerte Kampagneneffekt.

Danach die Tabs wieder schließen.

## Schritt 3 — Rechnen und diagnostizieren

Trichter, Kennzahlen und Schwellen aus `pruefverfahren.md` §1 und §3.
Dann §4: **die erste Stufe nennen, die reißt — nur die.** Liegt Stufe 3
bereinigt unter 30, lautet das Ergebnis „zu wenig Daten für eine Diagnose",
und das ist ein gültiges Ergebnis; dann keine Ursache erfinden.

## Schritt 4 — Ausgeben und ablegen

Im Terminal: Trichtertabelle, Kennzahlen, **ein** Diagnosesatz, und was bei
David liegt — kurz.

Dann schreiben:
* `docs/kampagne/JJJJ-MM-TT.md` — Trichter, Kennzahlen, Diagnose, offene Punkte,
  und ein Abschnitt **„Was ich nicht messen konnte"** samt Grund.
* eine Zeile an `docs/kampagne/verlauf.csv` (Kopfzeile dort ist verbindlich;
  leeres Feld = nicht erhoben, `0` = gemessen und null).

Zum Schluss committen, deutsch, `docs(kampagne): …`, mit dem Befund im Betreff.
**Nicht pushen** — pushen nur auf Ansage (CLAUDE.md).

## Wenn etwas nicht geht

Zwei Fehlversuche je Quelle, dann melden statt weiterprobieren. Eine fehlende
Quelle macht den Lauf nicht wertlos: Schritt 1 allein beantwortet schon, ob
Aufrufe und Leads da sind.
