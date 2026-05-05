# Relume-Sections — Manueller Import

Dieses Verzeichnis sammelt Sections aus deinem **Relume-Account** (Subscription
erforderlich). Der Backend-Seed (`seed_component_library.py`) liest die Files
hier automatisch beim Backend-Start ein und schreibt sie in `component_library`.

## Workflow pro Section

1. Im Relume-Account die gewünschte Section öffnen (`relume.io/react/...`).
2. **In Relume zwischen den beiden Code-Tabs wechseln:**
   - Pro Section bietet Relume einen Tab-Switch zwischen **HTML** und **React**.
   - **HTML-Tab wählen** → ganzen Code-Block kopieren (Copy-Button rechts oben).
   - Wir nutzen die HTML-Variante, weil die KAS-Endkunden-Sites über GrapesJS
     statisches HTML+Tailwind ausliefern. JSX würde nicht direkt rendern.

3. **Speichern als** `relume-{kategorie}-{n}.html`
   Beispiele: `relume-hero-1.html`, `relume-cta-3.html`, `relume-pricing-2.html`.

   **Cleanup-Regeln** (immer anwenden, ich mache das automatisch beim Einreichen):
   - `<section id="relume">` → `<section>` (id entfernen — kein Branding-Marker)
   - Cloudfront-URLs (`https://d22po4pjz3o32e.cloudfront.net/...`) durch
     lokale Placeholder ersetzen:
     - Logo-Bilder → `/placeholder-logo.svg`
     - Avatar-/User-Bilder → `/placeholder-avatar.svg`
     - Allgemeine Demo-Bilder → `/placeholder-image.svg`
   - Andere Vorkommen des Wortes „relume" in IDs / Comments innerhalb
     des Render-HTML → entfernen (Attribution-Header oben **bleibt**).
   - Tailwind-Klassen mit Relume-Tokens (`border-border-primary`,
     `bg-background-primary`, `text-neutral` etc.) bleiben erstmal —
     siehe TOKEN-Hinweis unten.

4. **Eintrag in `index.json`** ergänzen — Schema siehe unten.

5. Backend redeployen oder lokal `python -m seeds.seed_component_library`
   ausführen → die neuen Templates landen in `component_library`.

## index.json — Schema

```json
{
  "_source":      "Relume Library (https://www.relume.io)",
  "_license":     "Proprietary — Relume Pro/Sites subscription required",
  "_attribution": "© Relume",
  "_warning":     "Internal use only — DO NOT push this folder to a public repo.",
  "_imported_at": "YYYY-MM-DD",
  "components": [
    {
      "slug":           "relume-hero-1",
      "name":           "Relume · Hero #1",
      "category":       "HERO",
      "section_hint":   "hero_value_equation",
      "tags":           ["hero", "relume", "tailwind"],
      "slots":          [],
      "ki_prompt_hint": "Großer Hero mit Headline + Subtext + 2 CTA-Buttons. Marketing-Standard.",
      "preview_note":   "Klares Hormozi-Outcome-Layout, gut für Startseiten.",
      "source":         "relume"
    }
  ]
}
```

**Pflichtfelder:** `slug`, `name`, `category`, `tags`, `slots`, `ki_prompt_hint`, `preview_note`.

**Kategorie-Werte** (matchend zur KAS-Konvention):
`NAV`, `HERO`, `LEIST`, `TRUST`, `SEO`, `CTA`, `HW`, `FOOT`, `INFO`.

**section_hint** mappt auf KAS' `SECTION_CATALOG`-Keys
(`header_nav`, `cta_final`, `service_grid` usw.) — der KI-Wireframe-Generator
nutzt das später, um die richtigen Templates pro Sitemap-Section vorzuschlagen.

## Wichtig — Lizenz-Compliance

⚠️ **Relume-Code ist proprietär** — auch mit Subscription:

- Nutzbar in **deinem eigenen Projekt** (Inhouse, geschlossene Apps).
- **NICHT** in öffentlichen Repos / Open-Source-Distributionen.
- **NICHT** weiterverkaufen / als „own template" anbieten.
- Diese Repo-Folder ist nur OK, solange `nachhaltika-arch/Claude-Code` privat bleibt.

Wenn das Repo jemals öffentlich werden soll: **dieses Verzeichnis vorher entfernen
oder in `.gitignore` aufnehmen.**

## Tailwind-Token-Replace (Pflicht beim Import)

Relume nutzt eigene Custom-Tokens, die in Standard-Tailwind nicht
existieren. **KAS-Entscheidung: Tokens werden beim Import durch
Standard-Tailwind-Klassen ersetzt** (kein Relume-Preset, KAS bleibt
unabhängig). Mapping-Tabelle:

| Relume-Token                | Standard-Tailwind          |
|-----------------------------|----------------------------|
| `border-border-primary`     | `border-gray-200`          |
| `border-border-alternative` | `border-gray-300`          |
| `border-border-secondary`   | `border-gray-100`          |
| `bg-background-primary`     | `bg-white`                 |
| `bg-background-secondary`   | `bg-gray-50`               |
| `bg-background-alternative` | `bg-gray-100`              |
| `text-text-primary`         | `text-gray-900`            |
| `text-text-alternative`     | `text-gray-600`            |
| `text-neutral`              | `text-gray-500`            |
| `placeholder:text-neutral`  | `placeholder:text-gray-500`|

Wenn beim Import ein **neuer Relume-Token** auftaucht, der nicht in der
Tabelle steht: kurz prüfen welche neutrale Tailwind-Klasse semantisch
passt, Mapping hier ergänzen, anwenden, committen. Keine `border-*-*`
oder `bg-background-*` Tokens dürfen im finalen HTML stehenbleiben.

KAS-spezifische Brand-Farben (`#FAE600`, `#008EAA`, `#004F59`) werden
NICHT durch dieses Mapping zugewiesen — die kommen pro Section gezielt
über Slots oder im KI-Color-Sweep, sonst sieht jede Page gleich aus.

## Source-Tracking

Pro HTML-File **immer** einen Attribution-Header oben einfügen:

```html
<!--
  Source:   Relume Library — {Section-Name}
  License:  Proprietary, Relume subscription
  URL:      https://www.relume.io/react-components/{slug}
  Imported: YYYY-MM-DD
-->
```

So bleibt nachvollziehbar, woher jedes Template stammt — wichtig für Audit
und für späteres Refactoring (z.B. wenn ein Template aktualisiert werden muss).
