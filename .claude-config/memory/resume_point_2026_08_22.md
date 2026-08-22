---
name: resume_point_2026_08_22
description: "2026-08-22 — Prompt-Paket abgearbeitet, Lagebild als Artifact, elf Lücken geschlossen; drei Dinge liegen bei David"
metadata: 
  node_type: memory
  type: project
  originSessionId: 13c50d98-61aa-4d91-aa0f-f391ea9f1b35
  modified: 2026-08-22T18:42:49.232Z
---

Tag der Nachprüfungen: Fast jeder geschlossene Punkt kam heraus, weil eine
frühere Meldung „erledigt" zu früh war — und der Grund war jedes Mal derselbe:
Das Werkzeug maß enger als der Befund reichte.

**Was geschlossen wurde** (Lagebild: 70 Lücken, 22 offen, 5 teilweise, 43 zu):
L-78, L-79 (Freigabe-Knopf ohne `onClick`), L-19, L-54, L-84 (Kanalwirkung),
L-83 (benannte Ansichten), L-82 (Verlauf eines Betriebs), L-29 (dritte feste
Preisliste — **im Beleg des Kunden**), L-65 Teil A, L-38 (alle Haken geprüft),
L-86 (UTM ging beim Absenden verloren), L-80 (Wurzel 63 → 16), L-05, L-08
(react-router 6.20 → 7.18.2, Playwright grün), L-09, L-87, L-88.

**Die drei lehrreichsten Funde:**

1. **Der Wächter maß zu eng.** L-29 galt als geschlossen; der Preiswächter prüft
   den Frontend-Baum auf `1.500 €` und `payments` als Modul — rohe Zahlen im
   Backend sah keiner. Per AST über alle Dateien fand sich eine dritte feste
   Preisliste in `auftragsbestaetigung_pdf.py`, dem Dokument mit Belegcharakter.
   Der gezahlte Betrag kam herein und wurde nie benutzt.
2. **Ein Haken über vier Dinge ist nicht prüfbar.** Von zwölf Haken des
   Mai-Audits hielten acht; die zwei *teilweise* falschen fassten je mehrere
   Aussagen zusammen, und die Mehrheit traf zu — daran sind sie schwer zu
   widerlegen.
3. **Mein eigenes Lagebild log zweimal.** L-80 fiel seit jeher aus der Zählung
   (maskiertes `\|` im Beleg), L-84 zählte als offen, obwohl geschlossen (fehlende
   Durchstreichung). Beide Male sah die Gesamtzahl plausibel aus. Das Skript
   bricht jetzt ab bzw. warnt. Siehe [[messfehler_eigene_zahlen]].
4. **Zwei Zahlen waren zu hoch, weil das Werkzeug enger maß als die Wirklichkeit.**
   „44 npm-Befunde" → 40 davon sind Bauwerkzeug, seit dem Router-Sprung erreicht
   **keiner** den Besucher. „120 Routen ohne Prüfung" → tatsächlich 85: Der Rest
   wird vom **Router** gesperrt, während die Signatur `require_any_auth` nennt.
   Dieselbe Verwechslung erzeugte einen Fehlalarm (L-87), den erst ein Test
   widerlegte. Werkzeuge dafür: `tools/npm-befunde-einordnen.py`,
   `tools/schwacher-zugriffsschutz.py`.

**Was bei David liegt** — in dieser Reihenfolge:
- PR #45 mergen (Abrechnungsdaten waren für jeden Angemeldeten lesbar, CI grün)
- **L-65 Teil B:** „Trustpilot 4.9/5", „4.9 ★", „Trusted Shops" stehen fest im
  Quelltext. Besteht kein Konto, ist es keine ungenaue Zahl mehr, sondern
  irreführende Werbung. Je Siegel: Beleg nennen oder Zeile streichen.
- **L-62:** Mailstrecke — Rechtsgrundlage für Kaltakquise
- **L-75:** GrapesJS-Schlüssel beim Anbieter widerrufen (blockiert Prompt 03)
- **L-11:** Aufbewahrungsdauer der Render-Wiederherstellungspunkte + einmal
  eine Wiederherstellung tatsächlich proben (der Render-MCP ist in dieser
  Session `unauthorized`, der Klassifikator blockt den API-Umweg)
- **L-54:** die zweideutigen Altzeilen der Akademie — bereinigen oder stehen
  lassen

Verwandt: [[feedback_am_gegenstand_pruefen]], [[deploy_laeuft_ueber_ci]],
[[migration_trap_main_py]], [[feedback_ci_pruefen_nach_push]]
