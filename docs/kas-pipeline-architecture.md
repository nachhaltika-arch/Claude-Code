# KAS-Pipeline-Architektur — Relume-inspirierter Workflow

> **Status:** v1 — Konzept, 2026-05-04
> **Geltungsbereich:** Verbindlich für die KAS-Engine, die für SHK-Handwerker (Phase 1, siehe `niche_phase1.md`) automatisch Premium-Homepages generiert.
> **Verbundene Dokumente:**
> - `conversion-spec-shk.md` — Hormozi-Spec (Pflicht-Section-Inhalt + Wording)
> - `niche_phase1.md` — Branche/Region-Constraints
> - `audit-2026-05-04.md` — Bestand der Code-Basis vor diesem Umbau
> - `customer-journey-audit-2026-05-04.md` — End-to-End-Customer-Brüche

## Executive Summary

KAS bewegt sich von einer monolithischen "Audit + Content-Writing"-Logik zu einer **6-stufigen Pipeline** nach Relume-Vorbild: Analyse → Sitemap → Wireframes → Styleguide → Final Design → Deploy. Jede Stufe hat klare Daten-Contracts, ist einzeln testbar und ersetzbar. Die Engine produziert pro Kunde einen kompletten Site-Build, der zur Hormozi-Conversion-Spec konform ist und über Netlify ausgerollt wird.

## Pipeline-Stages mit Daten-Contracts

### Stage 1 — Analyse  *(✅ existiert)*

**Input:** Lead.website_url + Lead-Form-Daten (kampagne, email, mobil)

**Verarbeitung:** `routers/audit.py` → `lead_analyst.py` + `scraper.py` + `lead_enrichment.py` + `northdata.py`

**Output (`AnalysisResult`):**
```json
{
  "lead_id": 123,
  "website": { "reachable": true, "ssl": true, "page_speed_mobile": 42, "issues": ["..."] },
  "brand": { "primary_color": "#0a3d62", "fonts": [...], "logo_url": "...", "design_style": "modern" },
  "company": { "name": "...", "ceo": "...", "trade": "Heizungsbau", "city": "Koblenz", "wz_code": "..." },
  "services": ["Wärmepumpen-Installation", "Wallbox", "Sanitär-Notdienst", ...],
  "audit_score": 67,
  "geo_score": 41,
  "top_3_issues": ["..."],
  "opportunity_summary": "..."
}
```

### Stage 2 — Sitemap-Generation  *(🔴 zu bauen)*

**Input:** `AnalysisResult` + Briefing (`gewerk`, `leistungen`, `usp`, `hauptziel`, ...) + Conversion-Spec-Konstanten

**Verarbeitung:** Neuer `agents/sitemap_agent.py` — ein einziger Anthropic-Call mit strukturiertem Output.

**Prompt-Logik:**
- System-Prompt enthält Hormozi-Spec-Regeln (mind. eine Service-Page pro Hauptleistung, Pflicht-Sections pro Page, max. Tiefe 2)
- User-Prompt enthält die Analyse + Briefing
- Response-Format: JSON

**Output (`SitemapPlan`):**
```json
{
  "version": "1.0",
  "lead_id": 123,
  "generated_at": "2026-05-04T14:00:00Z",
  "pages": [
    {
      "slug": "/",
      "title": "Heizungsbauer Koblenz | Müller GmbH",
      "page_type": "home",
      "intent": "lead_capture",
      "sections": ["hero_value_equation", "problem", "offer_stack_main", "trust_strip", "fallstudien_3", "guarantee_block", "faq", "cta_final"],
      "primary_cta": "Kostenlosen Vor-Ort-Termin sichern",
      "meta": { "title": "...", "description": "..." }
    },
    {
      "slug": "/waermepumpe",
      "title": "Wärmepumpe in Koblenz — Festpreis in 7 Tagen",
      "page_type": "service",
      "intent": "convert_to_lead",
      "sections": ["hero_service", "value_equation_explained", "offer_stack_waermepumpe", "process_steps", "fallstudien_local", "trust_specific", "faq_service", "guarantee_block", "cta_final"],
      "primary_cta": "Festpreis-Angebot in 7 Tagen anfordern"
    },
    /* ... weitere Pages: /wallbox, /foerderung, /referenzen, /ueber-uns, /kontakt ... */
  ],
  "navigation": { "header": ["/", "/waermepumpe", "/wallbox", "/referenzen", "/ueber-uns"], "footer": [...] },
  "rationale": "kurze AI-Begründung warum diese Sitemap für diese Branche/diesen Kunden"
}
```

**Speicherung:** Neue Tabelle `sitemap_plans` (lead_id, version, json, created_at, approved_by, approved_at)

### Stage 3 — Wireframes  *(🔴 zu bauen)*

**Input:** `SitemapPlan` + Wireframe-Section-Library

**Wireframe-Library-Struktur:** `kompagnon/frontend/src/wireframes/`
```
sections/
  hero/
    hero_value_equation.jsx        ← Hormozi-style mit Outcome+Time+Effort
    hero_service.jsx                ← Service-Detail-Hero
    hero_minimal.jsx                ← klein/statisch
  offer/
    offer_stack_main.jsx            ← Hormozi-Wertbox mit EUR-Anker
    offer_stack_waermepumpe.jsx     ← Spezifische Service-Variante
    offer_stack_wallbox.jsx
  trust/
    trust_strip.jsx                 ← Logos horizontal
    trust_specific.jsx              ← Innung+Hersteller-Zertifizierungen
  fallstudien/
    fallstudien_3.jsx               ← 3 Cards
    fallstudien_local.jsx           ← mit Karten-Marker (Koblenz-Region)
  guarantee/
    guarantee_block.jsx             ← 5 Garantien aus Conversion-Spec
  faq/
    faq.jsx
    faq_service.jsx
  cta/
    cta_final.jsx                   ← Sticky-Bottom-Bar + Form
    cta_inline.jsx
  process/
    process_steps.jsx               ← Nummerierte 4-6 Schritte mit Zeitangabe
  problem/
    problem.jsx                     ← Pain-Points-Section
```

Jeder Wireframe ist eine **React-Komponente mit Tailwind-Klassen, basierend auf Preline UI-Skeletten**. Default-Inhalt sind Lorem-Ipsum-Platzhalter mit klar markierten Slots (z.B. `{{HERO_HEADLINE}}`, `{{OFFER_STACK_ITEMS}}`).

**Verarbeitung:** Neuer `services/wireframe_assembler.py`:
1. Liest `SitemapPlan.pages[].sections`
2. Für jede Section: lädt entsprechende Wireframe-Komponente
3. Rendert als JSX-Datei pro Page (`pages/[slug].jsx`)

**Output:** Page-Strukturen mit Section-Reihenfolge, ohne finalen Inhalt

### Stage 4 — Styleguide  *(🟡 partial — Brand-Detection da, Schema fehlt)*

**Input:** `Lead.brand_*` Felder (Color, Font, Logo) + Conversion-Spec-Defaults

**Verarbeitung:** Neuer `services/styleguide_generator.py` — deterministisch (kein AI), generiert JSON-Tokens.

**Output (`StyleguideTokens`):**
```json
{
  "version": "1.0",
  "lead_id": 123,
  "foundation": {
    "color": {
      "primary":   { "50": "#e6f0f7", "100": "...", "500": "#0a3d62", "900": "..." },
      "secondary": { ... },
      "neutral":   { ... },
      "semantic":  { "success": "#1d9e75", "warning": "#f59e0b", "error": "#dc2626" }
    },
    "typography": {
      "heading": { "family": "Inter, system-ui", "weights": [600, 700], "sizes": { "h1": "3.5rem", "h2": "2.5rem", ... } },
      "body":    { "family": "Inter, system-ui", "weights": [400, 500], "sizes": { ... } }
    },
    "spacing":      { "0": "0", "1": "0.25rem", ..., "32": "8rem" },
    "border_radius":{ "none": "0", "sm": "0.25rem", "md": "0.5rem", "lg": "1rem", "full": "9999px" },
    "shadow":       { "sm": "...", "md": "...", "lg": "..." }
  },
  "tokens": {
    "button":  { "primary": { ... }, "secondary": { ... } },
    "input":   { ... },
    "card":    { ... },
    "badge":   { ... }
  },
  "patterns": {
    "hero":          { "padding": "py-20", "max_width": "max-w-6xl", ... },
    "offer_stack":   { ... },
    "guarantee":     { ... }
  }
}
```

**Speicherung:** Neue Spalte `lead.styleguide_tokens_json` (oder eigene Tabelle bei Bedarf).

**Anwendung:** Wireframes werden mit Tokens via Tailwind-Config-Override eingefärbt — eine Tailwind-Config pro Kunde, generiert aus den Tokens.

### Stage 5 — Final Design  *(🟡 partial — content_writer existiert, Assembly fehlt)*

**Input:** Wireframe-JSX-Dateien + Styleguide-Tokens + Content (von `content_writer`)

**Verarbeitung:**
1. `services/content_writer` füllt die Slot-Platzhalter mit Hormozi-conformem Content (siehe `conversion-spec-shk.md`)
2. `services/site_compiler.py` (NEU) verarbeitet alle Pages: Tailwind-Build mit kunden-spezifischer Config, Content-Injection, statisches HTML/CSS-Output
3. QA-Agent prüft (Lighthouse, Link-Check, Hormozi-Spec-Compliance)

**Output:** Build-Output in `dist/customer-{lead_id}/` mit `index.html`, `waermepumpe.html`, etc. + Assets

### Stage 6 — Deploy  *(✅ existiert)*

`services/netlify_service.py` macht den Deploy auf Netlify.

## Architektur-Diagramm

```
┌──────────────────────────────────────────────────────────────────┐
│  routers/audit.py + lead_analyst.py + scraper.py                │ Stage 1
└──────────────────────────────────────────────────────────────────┘
                              │  AnalysisResult (existiert in DB)
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  agents/sitemap_agent.py    →  Tabelle sitemap_plans           │ Stage 2 (NEU)
└──────────────────────────────────────────────────────────────────┘
                              │  SitemapPlan
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  services/wireframe_assembler.py                                 │ Stage 3 (NEU)
│  + frontend/src/wireframes/ (React-Komponenten-Library)          │
└──────────────────────────────────────────────────────────────────┘
                              │  Page-JSX-Files mit Slots
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  services/styleguide_generator.py  →  Lead.styleguide_tokens_json│ Stage 4 (NEU)
└──────────────────────────────────────────────────────────────────┘
                              │  StyleguideTokens
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  agents/content_writer.py + services/site_compiler.py            │ Stage 5
│  + agents/qa_agent.py                                            │
└──────────────────────────────────────────────────────────────────┘
                              │  Statisches HTML/CSS Build
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  services/netlify_service.py                                     │ Stage 6
└──────────────────────────────────────────────────────────────────┘
```

## Wireframe-Library — Preline + Hormozi-Hybrid

**Foundation:** Preline UI (MIT-lizenziert, Tailwind-basiert, ~700 Components)

**KAS-Layer:** ~30 SHK-Hormozi-Spec-spezifische Sections, gebaut auf Preline-Skeletten:
- Visuelle Anpassung (Spacings, Schriftgrößen) Preline-konform
- Hormozi-Inhalts-Struktur (Value-Equation, Offer-Stack mit EUR-Box, etc.)
- Eingebettet als JSX-Module mit Slot-Platzhaltern

**Lizenzkonformität:** Preline ist MIT — frei kommerziell nutzbar, auch in SaaS-Wiederverkauf. Attribution im internen `LICENSES.md` ausreichend.

**Wireframe-Slots-Konvention:**
- `{{HEADLINE}}` — Plain-String, max 80 Zeichen
- `{{HERO_VALUE_EQUATION}}` — strukturierter Block mit 4 Feldern (outcome/likelihood/time/effort)
- `{{OFFER_STACK_ITEMS}}` — Liste von `{name, value_eur, description}` (mind. 6, max 8 — Hormozi-Anti-Pattern bei >8)
- `{{TRUST_LOGOS}}` — Liste von `{src, alt, link?}`
- `{{FALLSTUDIEN}}` — Liste von Cards (Stadt, Baujahr, alt/neu, Foto, EUR-Einsparung)
- `{{GARANTIEN}}` — Liste von 4-5 Garantien (Title, Description, Icon, AGB-Verweis)
- `{{FAQ_ITEMS}}` — Liste von `{question, answer}` (8-12 Items)

## Styleguide-Schema-Aufbau

Wie oben in Stage 4 beschrieben. Vier Schichten von abstrakt zu konkret:

1. **Foundation** — Color/Typography/Spacing/Radius/Shadow (= Atome)
2. **Tokens** — Button/Input/Card/Badge (= einfache Moleküle)
3. **Patterns** — Hero/OfferStack/Guarantee (= komplexe Moleküle für Sections)
4. **Templates** — Page-Layouts (Home, Service-Detail, Über-uns, Kontakt)

Jede Schicht ist ein JSON-Layer; höhere Schichten referenzieren niedrigere via Token-Namen.

Pro Kunde wird eine **eigene Tailwind-Config aus dem Styleguide-JSON gebaut** — diese Config einbinden bei Build → Site sieht Brand-konform aus, ohne Code-Anpassung.

## Customer-Approval-Flow

Pro Stage gibt's einen Customer-sichtbaren Approval-Punkt:

| Stage | Approval-Step | UI-Ort |
|-------|---------------|--------|
| 2 — Sitemap | Customer sieht Page-Tree, kann Pages umbenennen / hinzufügen / streichen | Portal-Seite "Sitemap-Freigabe" |
| 4 — Styleguide | Customer sieht Styleguide-Vorschau (Logo, Farben, Typo, Buttons) | Portal-Seite "Design-Freigabe" |
| 5 — Final Design | Customer sieht klickbares Mockup auf Subdomain (z.B. `vorschau.kompagnon.eu/{lead_id}`) | Portal-Seite "Site-Freigabe" |

Nach Final-Approval: Stage 6 (Deploy) startet automatisch.

Approval-Felder existieren bereits im Project-Schema:
- `sitemap_freigabe`, `briefing_approved_at`, `content_approval_token`, `content_approved_at`, `abnahme_datum`

## Implementation-Phasen

| Phase | Inhalt | Aufwand | Output |
|-------|--------|---------|--------|
| **1** | Sitemap-Agent + Styleguide-Schema | 1 Woche | Pro Kunde: SitemapPlan + StyleguideTokens (im Backend nutzbar, noch keine UI) |
| **2** | Wireframe-Library aufbauen (~30 Sections) + Wireframe-Assembler | 1-2 Wochen | Pro Page: gerenderte Wireframe-JSX mit Slots |
| **3** | Final-Assembly + Customer-Approval-Flow | 1-2 Wochen | Customer sieht klickbares Mockup, kann freigeben, Deploy-Trigger |
| **4** | Iteration auf Conversion-Daten (wenn Stage 3 Performance-Marketing live) | laufend | Kontinuierliche Optimierung |

## Open Questions / Decisions

- **Wireframe-Storage:** Single-File pro Page-Slug oder Component-Tree in Datenbank? → Empfehlung: File-System (`dist/customer-{id}/pages/{slug}.jsx`) für einfaches Build, JSON-Manifest in DB für Status.
- **Page-Vorschau-Hosting:** `vorschau.kompagnon.eu` als Subdomain mit dynamischem Routing oder Netlify-Preview-URLs? → Empfehlung: Netlify Branch-Deploys (eingebaut, kein Extra-Setup).
- **Sitemap-Editing-UI:** Drag-and-Drop (umfangreich) oder simple Liste mit Add/Remove (schnell)? → Phase 2 simple Liste, Drag-and-Drop in Phase 3+.
- **Multi-Page-Variant-Generation:** Soll die Sitemap mehrere Hero-Varianten vorschlagen (für A/B)? → Phase 1 nur eine, A/B-Logik in Stage 3 (Performance-Marketing).

## Was diese Architektur explizit NICHT tut

- Keine eigene Headless-CMS-Integration (Wireframe + Content sind ein Build-Step, kein Live-CMS)
- Keine Customer-Self-Service-Seitenanlage (Customer kann Pages nicht selbst erfinden, nur die generierten freigeben/anpassen)
- Keine Mehrsprachigkeit in Phase 1 (Pflicht-Region: Koblenz, Sprache: Deutsch)
- Kein E-Commerce/Shop-Modul (Phase 1 ist Lead-Generation, nicht Verkauf)
