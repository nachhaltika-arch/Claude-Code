# Envato Phase 1 — Vorbereitung HERO + CTA Bundle

Stand: 2026-05-09. Phase 0 (Inventur) fertig in `docs/envato-template-inventory.md`.

Phase 1 Ziel: 5-10 neue HERO + 3-5 neue CTA Wireframes ableiten.
Workflow: User sichtet Tier-1/2 Live-Demos → User postet Pattern-Notes → Claude leitet Wireframe-Kandidaten ab → neutralisiert + commitet.

---

## A) Pattern-Notes-Template (für User)

Nimm dir auf themeforest.net die ~10 Tier-1/2-Templates (siehe Inventory) zur Sichtung. Pro Template **kurze Stichpunkt-Notes** in folgendem Format. Was du nicht siehst oder unwichtig findest = einfach weglassen.

```
### {template-slug}
Live-Demo: {url}

HERO:
- Was siehst du Stark? (z.B. "Animierte Headline mit rotierenden Wörtern", "Hero mit Stat-Counter unten", "Inline-Email-Capture rechts")
- Bild/Video/Pattern? (z.B. "Background = Geometric Pattern", "Multi-Image-Collage 3-spaltig")
- CTA-Anzahl/Typ? (z.B. "1 Button + 1 Phone-Pill", "Inline-Email + Submit")
- Trust-Elemente direkt im Hero? (z.B. "★★★★★ Logo-Strip darunter")

CTA-Sections (außerhalb Hero):
- Wo erscheinen sie? (Pre-Footer / Mid-Page / Sticky-Bottom-Bar)
- Was ist Pattern? (z.B. "Countdown-Timer", "Newsletter mit Preview-Image", "Floating Mobile-Bar")
- Worauf reagiert es? (z.B. "Sticky nach 30% Scroll")

Sonst sehenswert:
- Pricing-Layout? Trust-Pattern? Alles, was außerhalb HERO/CTA aber für Phase 2/3 relevant.
```

Beispiel:
```
### bricknet-construction-company
Live-Demo: https://themeforest.net/.../bricknet

HERO:
- Hero hat 3 große Stat-Counter unten (Years/Projects/Awards) — animierte Zahlen
- Background = Foto + dunkles Overlay
- 1 CTA + 1 "Watch Video"-Pill nebendran
- Logo-Strip direkt darunter

CTA-Sections:
- Pre-Footer: "Get Free Quote" mit Telefon-Pill RECHTS, Beschreibung LINKS
- Sticky Bottom-Bar mobile: "Call Now"-Button

Sonst:
- 4-Spalten Service-Grid mit Hover-Reveal könnte für LEIST interessant sein
```

→ Du postest die Notes, Claude leitet daraus konkrete Wireframe-Kandidaten ab.

---

## B) Library-Konventionen (verbindlich für jeden neuen Wireframe)

### Slug + Filename
- Pattern: `{category}-{descriptor}` ohne Tech/Brand-Bezug
  - HERO: `hero-{descriptor}` (z.B. `hero-stat-counter`, `hero-rotating-headline`)
  - CTA:  `cta-{descriptor}` (z.B. `cta-countdown`, `cta-newsletter-preview`)
- File: `kompagnon/frontend/src/components/library/{slug}.html`

### HTML-Struktur
```html
<!--
  Pattern-Inspiration: {template-name aus Envato}
  Lizenz-Status: eigenständig neutralisiert, kein Code-Copy
-->
<section data-block="{slug}"
         class="bg-white py-16 md:py-24 px-6"
         style="font-family: 'Noto Sans', sans-serif;">
  <!-- Slot-markers per {{slot_key}} -->
  <h1 class="text-4xl md:text-6xl font-black text-gray-900 mb-6">
    {{headline}}
  </h1>
  <!-- ... -->
</section>
```

**Regeln:**
1. **Tailwind-Greys ONLY** — `gray-50/100/200/700/900`, `slate-200/500/600`. **Keine Brand-Farben, keine `--kc-*` Tokens.** Templates sollen brand-neutral sein, Brand-Application kommt später durch BrandDesignEditor.
2. **Inline-SVG für Icons** — kein FontAwesome-Dependency, keine externen Icon-Libs.
3. **`{{slot_key}}`-Marker** — alle dynamischen Texte/URLs/Bilder als Slot-Platzhalter.
4. **Pattern-Provenance** — HTML-Comment im File-Header mit Quell-Template-Name (für Lizenz-Audit).
5. **Eigenständiges HTML** — niemals direkt aus Envato-Template kopieren. Pattern als Inspiration → eigene Klassen-Struktur → eigene Markup-Reihenfolge.

### `index.json`-Eintrag
Für jeden neuen Wireframe in `kompagnon/frontend/src/components/library/index.json` `components`-Array ergänzen:

```json
{
  "slug": "{slug}",
  "name": "{Human-readable Name}",
  "category": "HERO|CTA|TRUST|LEIST|SEO|FOOT|HW|NAV",
  "tags": ["hero", "{deskriptor1}", "{deskriptor2}"],
  "slots": [
    { "key": "headline", "label": "Hauptüberschrift", "type": "text", "default": "..." },
    ...
  ],
  "ki_prompt_hint": "Wann soll der KI-Selector diesen Block wählen? Konkret + diskriminierend gegenüber anderen Heroes/CTAs.",
  "preview_note": "Visuelle Beschreibung 1-2 Sätze: Layout, Farb-Akzente, Mobile-Verhalten."
}
```

### Backend-Sync
Nach jedem neuen Wireframe ergänzen:
1. `kompagnon/backend/seeds/seed_component_library.py` — `LIBRARY_VERSION_LOG` mit Datum + Pattern-Liste
2. Commit + push staging → Render Backend baut auto via rootDir-Watch

---

## C) Stand der Library — was schon existiert (Phase 0 Output)

### HERO (8 Wireframes)
| Slug | Pattern | Wann wählen? |
|------|---------|--------------|
| `hero-standard` | Split (Bild rechts + Text links + 1 CTA) | Default-Choice mit gutem Foto |
| `hero-formular` | Split (Text + Direkt-Formular) | Wenn Lead-Capture Hauptziel |
| `hero-centered` | Vollbild-BG + zentrierter Text + 2 CTAs | Wenn Bild starke Atmosphäre transportiert |
| `hero-video` | Hintergrund-Video + zentrierter Text | Premium, nur wenn gutes Video da |
| `hero-badges` | Standard + 3 Trust-Badges drunter | Etablierte Betriebe mit Reputation |
| `hero-split-dark` | Dark-Mode Split (50/50, Premium-Look) | Premium / Beratungs-Anspruch |
| `hero-image-video` | Hero mit Image + inline Video-Kachel | (Envato POC 2026-05-08) |
| `hero-stats` | Hero mit 3 Stat-Counter unten | (Envato POC 2026-05-08) |

### CTA (6 Wireframes)
| Slug | Pattern | Wann wählen? |
|------|---------|--------------|
| `cta-angebot` | Mehrstufiger Angebots-Wizard | Premium / hoher Auftragswert |
| `cta-banner` | Streifen mit 1 Button | Compact, mid-page |
| `cta-formular` | Kontaktformular (DSGVO + Brevo) | Standard-Lead-Form |
| `cta-kontakt-split` | Adresse links + Formular rechts | Local-Business-Vertrauen |
| `cta-termin` | Datums-Auswahl + Formular | Buchbares Geschäft |
| `cta-whatsapp` | Floating-Button bottom-right | Mobile-First, 1:1-Kontakt |

### Phase-1-Pattern-Kandidaten (laut envato_wireframe_plan.md)
Diese Liste ist **Erwartungswert**, nicht verbindlich — User-Notes können andere Patterns hochziehen:

**HERO:**
- Animierter-Text (rotierende Wörter)
- Background-Pattern (geometric/blob/noise)
- Inline-Email-Capture (Hero direkt mit E-Mail-Field)
- Multi-Image-Collage (3+ Bilder kombiniert)
- Stat-Counter-Hero — **schon existiert** als `hero-stats` ✓

**CTA:**
- Countdown / Limited-Offer
- Newsletter mit Preview-Image
- Floating Bottom-Bar (mobile-only)
- Hero-Style Pre-Footer-CTA (große visuelle CTA-Section vor Footer)

---

## D) Workflow-Reminder pro Wireframe

1. **Pattern-Identifikation** aus User-Notes oder gezielt aus Envato-ZIP
2. **HTML extrahieren** (nur falls nötig): `unzip -j {template}.zip "{page}.html"` — keine Assets
3. **Pattern auf Layout reduzieren** (nicht Code) — Sketch im Kopf: "was sind die 3-5 Boxes/Slots dieses Patterns?"
4. **Eigenständiges HTML schreiben** im Library-Format (siehe B)
5. **`index.json`-Eintrag** ergänzen mit slug, name, category, tags, slots, ki_prompt_hint, preview_note
6. **`seed_component_library.py`** LIBRARY_VERSION_LOG erweitern: `"2026-MM-DD.N: {pattern-list}"`
7. **Commit** mit Pattern: `feat(library): add {slug} (Envato Phase 1)`
8. **Push staging** → Render baut Backend auto

---

## E) Lizenz-Compliance (kritisch)

- **Niemals** Code aus Templates direkt kopieren — nur Layout-Pattern als Inspiration
- Eigenständiges HTML mit neutralisierten Greys schreiben
- Pattern-Provenance pro Wireframe im HTML-Comment dokumentieren
- Templates dürfen nicht in den Library-Source-Tree eingecheckt werden
- ZIPs liegen ausschließlich auf Davids Desktop (`~/Desktop/Envato`), nicht im Repo

→ Bei Unsicherheit: Pattern weglassen statt Lizenzgrenze testen.
