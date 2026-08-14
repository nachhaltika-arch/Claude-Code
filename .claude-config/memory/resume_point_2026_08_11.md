---
name: resume_point_2026_08_11
description: "Wiederaufnahme 2026-08-11 — Widget einbettungsfertig gemacht; offen sind Live-Verifikation, DSGVO- und Pentest-Prüfung"
metadata: 
  node_type: memory
  type: project
  originSessionId: 17693c29-1a28-4ce0-b59d-163268b820db
  modified: 2026-08-11T21:12:59.970Z
---

Arbeitsstand vom 2026-08-11 (Abend). Vollständige Übergabe liegt im Repo:
`docs/widget-stand-2026-08-11.md`.

**Reihenfolge, die David vorgegeben hat:** morgen früh zuerst das Widget
fertigstellen, danach Bericht/E-Mail und der Anforderungskatalog aus
`docs/audit-anforderungen-2026-08-11.md`.

**Ziel des Widgets:** Einbau in eine fremde Landingpage. Das ist der Maßstab
für „fertig", nicht die Tool-Vorschau.

Heute auf `staging` gepusht (4 Commits, `3da9345`…`5e39f7d`):
* SMTP-Einstellungen aus Tool und API entfernt — der Versand läuft über Brevo.
  Der Test-Knopf hing an `smtp.configured` und war dadurch dauerhaft gesperrt.
* Einbaucode führt jetzt die iframe-Höhe nach (`utils/widgetEmbed.js`, 13 Tests).
* Einwilligung ging verloren: Die Checkbox wurde gelesen, nachdem der
  Karteninhalt bereits ersetzt war — erklärt 8 Anfragen bei 0 Einwilligungen.
* „42 Kriterien" war falsch; der Katalog führt 38 bewertete.

Offen: Live-Verifikation auf Staging, DSGVO-Prüfung, Pentest-Prüfung.
Siehe [[quality_bar_kas]] und [[weekly_release_cadence]] — PR nach `main` erst
freitags, siehe [[feedback_pr_only_fridays]].
