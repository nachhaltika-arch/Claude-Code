---
name: KOMPAGNON UI/UX Guidelines v1.0
description: Verbindliche Design-Referenz für das KAS-Tool selbst (Sitemap, Wireframe, Styleguide, Design Views). Legt Farben, Typo, Spacing, Buttons, Cards, Tabellen, Navigation fest.
type: project
originSessionId: 4cd24d32-85e3-4a98-b22a-82325da50d7e
---
Ab 2026-05-07 ist `KOMPAGNON_UI-UX_Guidelines_v1.0.pdf` (Downloads) verbindlich für alle Interface-Views des KAS-Tools — Sitemap, Wireframe, Styleguide, Design.

**Why:** David hat den Styleguide-Editor gerade umgebaut und will die ganze App-Oberfläche jetzt am verbindlichen Markenstandard ausrichten. Vorher haben die Views verschiedene CIs gemischt; das war Markenverwässerung.

**How to apply:** Beim Bauen / Refactor von Tool-UI strikt einhalten:

- **Farben (Tool-CI, nicht Endkunden-Output):** Dark Teal `#004F59` dominiert (Sidebar, Buttons-primary, Tabellenköpfe, Headlines). Mid Teal `#008EAA` für Links und sekundäre Kategorien. Gelb `#FAE600` als Akzent — **max 1 Element pro Screen** für die wichtigste Aktion. Schwarz `#000000` für Text. Status: Erfolg `#00875A`, Hinweis `#A86800`, Fehler `#C0392B`, Info `#008EAA` Tint. Text auf `#004F59` nur Weiß oder Gelb — niemals Grau.
- **Typografie:** Noto Sans Black 900 für Headlines/Buttons/Labels (UC, ls -0.025em). Noto Sans 300/400/700 für Body (lh 1.75, ls 0.01em). Eloquent JF Pro Italic für Display/Hero. Rift Demi 600 für Claims (UC, ls 0.08em). DM Mono 500 für Kennzahlen/Daten. Body max 65 Zeichen Lesebreite.
- **Spacing:** 8px-Basisraster, alle Werte Vielfache von 4/8: 4/8/12/16/24/32/48/96. Layout-Grid 220px Sidebar / 1fr Main / 280px Context.
- **Buttons:** Eine Primary pro Screen (Gelb für die *wichtigste* Aktion, sonst Dark-Teal-solid). Niemals 2 Primary nebeneinander. Label = Verb + Objekt ("Projekt speichern", nicht "OK"). Destruktiv = btn-danger, niemals Teal/Gelb. Disabled opacity 0.4.
- **Forms:** Label über dem Feld (nie als Placeholder). Validierung onBlur, nicht keystroke. Fehlermeldung konkret ("Erwartet: BAFA-JJJJ-00000"). Max 7 Felder pro Seite.
- **Cards:** Border-Top kodiert Wichtigkeit — Dark = primäre KPI (1× pro Gruppe), Yellow = CTA-nahe Ausnahme, Mid = sekundäre Kategorie, Flat `#F6F5F2` = sekundäre Info.
- **Badges:** Status immer durch Farbe **und** Text — niemals Farbe allein.
- **Tabellen:** Tabellenköpfe Dark Teal. Erste Spalte fett. Zahlen rechtsbündig + Monospace. Zeilenaktionen rechts bei Hover. Max 6 Spalten ohne horizontales Scrolling.
- **Navigation:** Breadcrumbs `Dashboard › Kunden › X`. Aktiver Tab = Gelb-Unterstrich `#FAE600` 3px. Tab-Wechsel lädt nicht neu. Max 7 Punkte pro Ebene (Miller's Law).
- **Feedback:** Jede Aktion → sichtbare Reaktion in 100ms. Toasts mit Icons (✓ ⚠ ✕ ℹ). Rückgängig statt "Bist du sicher?".
- **Anti-Pattern:** Modal-Hölle, 2 Primary nebeneinander, Gelb überall, Status nur durch Farbe — alle verboten.
- **Abschlussprinzip:** Ziel ist *Unsichtbarkeit* — Nutzer denkt über die Aufgabe nach, nicht das Interface.
