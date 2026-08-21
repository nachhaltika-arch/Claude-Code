---
name: resume-point-2026-08-21
description: "Stand 2026-08-21 — 18 Commits ohne Render-Zugang: L-29/L-59/L-17/L-58a/L-33/L-38/L-28/L-63/L-07/L-05/L-27/L-08/L-09 geschlossen; sieben Entscheidungen liegen bei David, L-34 bleibt blockiert"
metadata:
  type: project
---

**Ein Freitag, an dem nur ging, was im Code liegt.** Der Render-MCP meldet den
**fünften Tag** `unauthorized`; damit blieben L-34 (Umzug), L-57, L-40, L-44
und L-35 blockiert. Alles Übrige aus der Lückenliste ist abgearbeitet.

## Geschlossen

L-29 (Preise), L-59 (Rechtsgrundlage), L-17 (Formularfelder + Überschriften),
L-58 (a) (KI-Lesbarkeit im Audit), L-33 (Dateiendungen), L-38 (Mai-Audit),
L-28 (Template-Router), L-63 (neu), L-07 (durch Messen), L-05 (vierter
Schritt), L-27 (abgesichert), L-08 (teilweise), L-09 (Zahlungen).

Tests: 927 + 98 → **1.538 Backend + 370 Frontend**.

## Die drei Funde, die niemand gesucht hat

1. **L-63 — zwei Endpunkte scheiterten seit vier Monaten an jedem Aufruf.**
   `templates.py` schrieb `%(name)s` in einem `sqlalchemy.text(...)`; das
   bindet nichts, Postgres antwortet `syntax error at or near "%"`. Betroffen:
   `POST /api/templates/upload` und `/import-url` — beide ruft das Frontend
   auf, seit dem 10.04.2026. Der damalige Commit nennt als Grund die Angst vor
   `:root` im CSS. Die Sorge ist unbegründet: SQLAlchemy liest **nur den
   SQL-Text**, nie die gebundenen Werte.

2. **L-62 — fünf von acht Werten in `AUTO_SEQUENCE_SOURCES` werden nirgends
   geschrieben.** Die Webhooks schreiben `facebook`/`linkedin`/`google`, die
   Liste erwartet `webhook_facebook` usw. Und `postkarte`, das in beiden
   Listen steht, greift auch nicht: `_upsert_lead` schreibt mit rohem SQL und
   läuft an `create_lead` vorbei. Von fünf Lead-Wegen bekommt **keiner** die
   automatische Mailstrecke — unbemerkt, weil das Ausbleiben einer Mail nichts
   protokolliert.

3. **L-61 — die Verkaufsseite versprach „zzgl. MwSt.", die Kasse schlägt
   nichts auf.** Kein `automatic_tax`, keine `tax_rates`; der Kunde las
   1.785 € und wurde mit 1.500 € belastet.

## Sieben Fragen, die bei David liegen

L-61 (MwSt. — die dringendste), L-62 (Mailstrecke für Kaltakquise?), L-59
(Rechtsgrundlage für elf Quellen), L-58 (welches Kriterium wird leichter?),
L-56 (Konto mitlöschen?), L-60 (Lehrplan), L-27 (welche Briefing-Struktur
bleibt?). Sie stehen als Tabelle in `docs/stand-2026-08-21.md`.

## Morgen

Erst prüfen, ob der Render-Zugang wieder geht — daran hängt die ganze obere
Hälfte der Reihenfolge. Sonst: L-25/L-26 (Dateigrößen und Editor-Generationen)
oder der Rest von L-17 (Tastaturbedienung, Fokus, Kontraste).

PR #43 (`staging → main`) stand am Vormittag offen und trägt alle heutigen
Commits.

Siehe [[feedback-am-gegenstand-pruefen]], [[messfehler-eigene-zahlen]].
