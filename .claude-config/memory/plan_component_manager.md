---
name: Plan Component-Manager UI (2-Phasen)
description: Vereinbarter Plan fuer Component-Library-Editor in der Sidebar, Start 2026-05-06 frueh
type: project
originSessionId: 5df94fc7-afb2-46bf-a841-7ff3753e280b
---
User-Anforderung: Component-Katalog als Sidebar-Eintrag unter Einstellungen, mit Editor zum Bearbeiten und Neu-Anlegen einzelner Komponenten. Komponenten sollen nach ihrem Einsatz im Projektprozess editierbar sein. Eingabe per HTML oder React, System entscheidet kontextabhaengig welche Version genutzt wird.

**Why:** User will Komponenten-Bibliothek (aktuell 93 Eintraege: 41 KAS + 51 HyperUI + 1 Relume) selbst kuratieren statt nur per Repo-Edit + Backend-Restart. Phase 1 schafft das CRUD-UI, Phase 2 fuegt React-Eingabe hinzu.

**How to apply:** Morgen frueh (2026-05-06) direkt mit Phase 1 starten. NICHT nochmal die Wahl Phase-1-only vs. Phase-1+2 anbieten — User hat sich klar fuer "Phase 1 zuerst, Phase 2 danach" entschieden ("damit starten wir morgen frueh direkt", in Reaktion auf meinen Vorschlag mit Phase 1 als Bauchgefuehl-Empfehlung).

---

## Phase 1 (jetzt) — Component-Manager im UI

**Sidebar:** Neuer Eintrag unter "Einstellungen" — Label vermutlich "Komponenten-Bibliothek". Datei: `kompagnon/frontend/src/components/Layout/AppLayout.jsx` (5-Section-Struktur Akquise / Leads / Projekte / Kompagnon / Einstellungen).

**Route:** `/app/settings/component-library` (oder `/app/components`, beim Anlegen entscheiden).

**View — `ComponentLibraryView.jsx`:**
- Liste aller Komponenten aus `GET /api/components` (existiert)
- Filter: Quelle (KAS / HyperUI / Relume / Custom) + Kategorie
- Klick auf Eintrag oeffnet Edit-Modal
- "Neu anlegen"-Button oeffnet leeres Formular

**Editor-Modal — Felder:**
- Name, Slug, Kategorie, `section_hint` (Dropdown gegen KAS section_catalog: hero / problem / solution / features / proof / pricing / cta / footer_legal / header_nav etc.)
- Tags (Chip-Input)
- Slots-Liste (key / label / default), addable/removable
- `ki_prompt_hint`, `preview_note`
- `html_template` (Monaco-Editor oder einfach textarea mit syntax-highlight via prism)
- Live-Preview rechts (gleiche Logik wie WireframeView: `dangerouslySetInnerHTML` + `renderSlots`)

**Backend — neue Endpoints in `kompagnon/backend/routers/component_library.py`:**
- `PUT /api/components/{slug}` — update (oder PATCH)
- `POST /api/components` — create (existiert moeglicherweise schon als `/save-custom`, dann konsolidieren)
- `DELETE /api/components/{slug}` — delete

**Auth:** Wie ueberall in KAS — keine Sonderbehandlung, Standard-Auth-Middleware.

**Geschaetzter Aufwang:** ~5 neue/erweiterte Files, 1 Tag.

---

## Phase 2 (danach, nicht jetzt) — React als zweite Eingabequelle

- DB-Spalte `react_source TEXT NULL` zur `component_library`-Tabelle (Auto-Migration in `main.py`)
- Editor-Toggle "HTML | React"
- TSX-Eingabe → Auto-Konvertierung zu HTML beim Speichern (KI-gestuetzt via OpenAI/Claude: TSX rein, statisches HTML mit Standard-Tailwind-Tokens raus)
- "System entscheidet"-Regel klar definiert:
  - Endkunden-Export (Marketing-Site-Output): IMMER `html_template` (Endkunden-Sites haben kein React-Runtime)
  - KAS-Wireframe-Preview (interne Anzeige): `react_source` falls vorhanden (Interaktivitaet), sonst `html_template`
  - User sieht beide Versionen im Editor

**Geschaetzter Aufwang:** 2-3 Tage wegen TSX→HTML-Pipeline.

---

## Wichtige Hintergrund-Klaerung (vom User akzeptiert)

User dachte zunaechst "System entscheidet welche Version besser ist" — funktioniert nicht universell:
- Endkunden-Sites = statisches HTML, kein React-Runtime → React-only-Komponenten koennten dort gar nicht laufen
- KAS-Preview = Browser mit React → beides moeglich, React optional besser

Daher ist "besser" kontextabhaengig, nicht universell. User hat das akzeptiert nach meiner Tabelle.
