# assets — Marke und Schriften

Hier liegt, was nicht in den Quellcode gehört, aber zum Projekt: das
Markenmaterial und die lizenzierten Schriften.

## Warum dieser Ordner existiert

Bis zum 22.08.2026 lag beides im **Wurzelverzeichnis** — 63 Einträge, davon
46 versionierte Dateien ohne eine Zeile Programmcode (L-80). Wer das Repo
zum ersten Mal öffnete, sah zuerst 19 Schriftdateien und 26 Logos, und erst
danach `kompagnon/`.

## Was hier liegt

| Ordner | Inhalt |
|---|---|
| `marke/` | Logos, Icons und Bildmarken (PDF, PNG, SVG, JPG, AI) |
| `schriften/` | Noto Sans, alle Schnitte, mit `OFL.txt` |

## Was die Anwendung tatsächlich benutzt

**Nicht diese Dateien.** Die PDF-Erzeugung lädt ihre Schriften aus
`kompagnon/backend/assets/fonts/` (nur Regular und Bold —
`services/pdf_generator.py::SCHRIFT_ORDNER`). Die Schriften hier sind der
vollständige Satz für Gestaltungsarbeit, keine Laufzeitabhängigkeit.

Auf keine der Markendateien verweist Quellcode; sie sind Vorlagen.

## Was am 22.08.2026 wegfiel

* `._NotoSans-Regular.ttf` — ein macOS-AppleDouble-Artefakt, versioniert.
  `._*` steht jetzt in `.gitignore`.
* `kompagnon-automation-system.zip` — eine Quellcode-Kopie vom 29.03.2026
  (59 Dateien) **im Quellcode**. Den Stand führt git; das Archiv trug nichts
  bei, was nicht in der Historie steht. Geprüft war es zuvor auf
  Zugangsdaten: Es enthielt nur eine `.env.example`.
