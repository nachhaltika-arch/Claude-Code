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
