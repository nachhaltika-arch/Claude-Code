---
name: Envato Wireframe-Pipeline Plan
description: Multi-Session-Plan zum Ableiten maximaler Anzahl unique Wireframes aus 68 Envato-Templates (~/Desktop/Envato), lizenzkonform via Pattern-Inspiration. 5 Phasen, ~30-50 Ziel-Wireframes über 8-12 Sessions.
type: project
originSessionId: 4cd24d32-85e3-4a98-b22a-82325da50d7e
---
**Why:** David hat 68 Envato-Templates (2.1 GB) heruntergeladen und will daraus maximal viele wiederverwendbare Wireframes für die KOMPAGNON Component-Library ableiten. Lizenzrechtlich darf nichts copiert werden (gleicher Fall wie Relume vor 2 Tagen) — nur Pattern-Inspiration mit eigenständigem neutralisierten Code. POC `hero-image-video` + `hero-stats` heute gepusht (commit `5154744`), Workflow ist etabliert.

**How to apply:** Pro Session 1 Phase oder 1 Sub-Bundle nehmen, nicht alles auf einmal. Status-Tracker unten in dieser Datei pflegen, neue Wireframes pro Commit dokumentieren. User macht die visuelle Sichtung (Live-Demos / ThemeForest), Claude extrahiert HTML + neutralisiert. Niemals Template-Code in `frontend/src/components/library/` einchecken.

---

## Volumen-Realismus

- 68 Templates × ~8-10 Sektionen ≈ 540-680 Pattern-Vorkommen
- Davon ~50-80 unique (viel Wiederholung: Hero-Split, FAQ-Accordion, 3-Tier-Pricing schon 100×)
- Davon ~30-50 wertvoll für KOMPAGNON-Use-Cases
- Total Workload: 30-60h, 8-12 Sessions à 1.5-3h
- Pro Wireframe: 25-45 min (Pattern-Identifikation 5-10 min, HTML schreiben 10-20 min, Slots+JSON 5-10 min, Test 5 min)

## Etablierter Workflow pro Wireframe

1. User wählt Template + nennt Sektionen, die visuell stark sind (via Live-Demo)
2. Claude entpackt nur die relevanten HTML-Pages (`unzip -j … "<page>.html"`, keine Assets)
3. Pattern-Identifikation aus HTML-Struktur (`grep -n` für Boundaries, `sed -n` zum Lesen)
4. Eigenständiges neutralisiertes HTML im Library-Format:
   - `<section data-block="…" class="bg-white py-16 md:py-24 px-6" style="font-family: 'Noto Sans', sans-serif;">`
   - Tailwind-Greys (gray-50/100/200/700/900, slate-200/500/600), keine Brand-Farben
   - Inline-SVG für Icons (kein FontAwesome-Dependency)
   - `{{slot_key}}`-Marker an allen Texten/URLs/Bildern
   - Pattern-Comment im File-Header mit Provenance ("Pattern-Inspiration: <template-name>")
5. `index.json`-Eintrag: slug, name, category, tags, slots, ki_prompt_hint, preview_note
6. `seed_component_library.py` LIBRARY_VERSION_LOG erweitern: `"2026-MM-DD.N: <pattern-list>"`
7. Commit + Push `staging`. Render baut Backend auto via rootDir-Watch.

## Lizenz-Compliance (kritisch)

- **Niemals** Code aus Templates direkt kopieren — nur Layout-Pattern als Inspiration
- Eigenständiges HTML mit neutralisierten Greys schreiben
- Pattern-Provenance pro Wireframe im HTML-Comment dokumentieren
- Templates dürfen nicht in den Library-Source-Tree
- ZIPs liegen ausschließlich auf Davids Desktop (`~/Desktop/Envato`), nicht im Repo

## Phasen

### Phase 0 — Inventur (1 Session, ~1.5h) [STATUS: open]

**Ziel:** Übersicht aller 68 Templates, welche Pages drin, welche groben Pattern-Klassen.

**Vorgehen:**
1. ZIPs durchscannen mit `unzip -l`, HTML-File-Liste pro Template extrahieren
2. Output: `docs/envato-template-inventory.md` mit Tabelle Template / HTML-Pages / Tech-Stack (HTML/Tailwind, React, etc.)
3. User schaut Live-Demos der ~10 visuell vielversprechendsten Templates an, gibt Notes pro Template ("Hero ist stark", "Pricing-Comparison-Table sehenswert")

**Deliverable:** Liste ~20-30 Pattern-Kandidaten für Phase 1-3, priorisiert nach KOMPAGNON-Relevanz.

### Phase 1 — HERO + CTA Bundle (2-3 Sessions) [STATUS: open]

**Ziel:** 5-10 neue HERO + 3-5 neue CTA

**Existing (Stand 2026-05-08):**
- HERO (8): hero-standard, hero-formular, hero-centered, hero-video, hero-badges, hero-split-dark, hero-image-video, hero-stats
- CTA (6): cta-angebot, cta-banner, cta-formular, cta-kontakt-split, cta-termin, cta-whatsapp

**Pattern-Kandidaten (Phase-0-Output füllt):**
- HERO: animierter-Text (rotierende Wörter), Background-Pattern (geometric/blob), Inline-Email-Capture, Multi-Image-Collage, Stat-Counter-Hero
- CTA: Countdown/Limited-Offer, Newsletter-mit-Preview-Image, Floating-Bottom-Bar, Hero-Style-Pre-Footer-CTA

### Phase 2 — TRUST + LEIST Bundle (2-3 Sessions) [STATUS: open]

**Ziel:** 5-10 neue TRUST + 5-10 neue LEIST

**Existing:**
- TRUST (7): trust-bewertungen, trust-galerie, trust-kennzahlen, trust-team, trust-testimonial, trust-ueber-uns, trust-zertifikate
- LEIST (7): leist-foto, leist-grid-3, leist-highlight, leist-liste, leist-preise, leist-prozess, leist-tabbed

**Pattern-Kandidaten:**
- TRUST: Award-Strip-mit-Year, Press-Quotes, Hover-Reveal-Team, Animated-Stats-Counter, Customer-Logo-Marquee
- LEIST: Service-Comparison-Table, Iconboard-Grid (Icons-only, kein Bild), Step-by-Step-Process-Vertikal, Tabs-with-Image-Switch, Service-Detail-Split

### Phase 3 — SEO + FOOT + HW Bundle (2 Sessions) [STATUS: open]

**Ziel:** 5-10 neue Wireframes

**Existing:**
- SEO (6): seo-blog, seo-faq, seo-leistung-hero, seo-lokal, seo-notdienst, seo-textblock
- FOOT (2): foot-kompakt, foot-standard
- HW (4): hw-karte, hw-marken, hw-oeffnungszeiten, hw-vor-ort

**Pattern-Kandidaten:**
- SEO: Blog-Magazin-Layout (Featured + Grid), FAQ-mit-Sidebar-Search, Glossary, How-It-Works-Steps
- FOOT: Multi-Column-Footer-mit-Newsletter, Mega-Footer-mit-Service-Links
- HW: Service-Areas-Karte (mit Marker), Notfall-Sticky-Bar, Garantie-Highlight

### Phase 4 — Polish & Dedup (1 Session) [STATUS: open]

- Library auf Doppelungen prüfen (visuelle Diff bei 80%+ Ähnlichkeit)
- Naming-Konsistenz (alle Slugs `category-feature` Pattern)
- ki_prompt_hints reviewen — sind sie spezifisch genug für AI-Auswahl?
- Library-Version-Log abschließen
- Optional: Bundle-Größe-Tracking

## Status-Tracker

| Phase | Sessions | Wireframes Ziel | IST | Status |
|-------|----------|-----------------|-----|--------|
| 0 — Inventur | 1 | (Plan-Liste) | 1 | **DONE 2026-05-09** (`docs/envato-template-inventory.md`, commit `09225c0`) |
| 1 — HERO+CTA | 2-3 | 8-15 | 2 | in progress (POC: hero-image-video + hero-stats) |
| 2 — TRUST+LEIST | 2-3 | 10-20 | 0 | open |
| 3 — SEO+FOOT+HW | 2 | 5-10 | 0 | open |
| 4 — Polish | 1 | (cleanup) | — | open |

**POC vor Plan-Start (2026-05-08):** hero-image-video + hero-stats — commit `5154744`. Pattern-Quelle: agon-multipurpose-agency.

**Phase 0 Output (2026-05-09):** 68 Templates inventarisiert in `docs/envato-template-inventory.md`. 14 Tier-Empfehlungen für User-Live-Demo-Sichtung. Tier 1 Tailwind: agon, bricknet, travel-tour-booking. Tier 2 SHK-adjacent: arkdin, pakkapati, roofsie, freshflow, phone-repair. Tier 3 Multipurpose: digmox, potu, techex. Tier 4 Pattern-Pool: astrax (2675 Pages), invena, lightwire.

**User-Aufgabe als Voraussetzung für Phase 1 Vollstart:** Live-Demos der ~10 Tier-1/2 Templates auf themeforest.net sichten, Pattern-Notes posten. Erst dann kann Claude gezielte Pattern-Kandidaten ableiten.

## Decision-Points zwischen Phasen

Nach jeder Phase entscheidet der User:
- Weiter mit der nächsten Phase
- Phasenwechsel überspringen (z. B. SEO später)
- Polish vorziehen (wenn Library schon zu groß wird)
- Aussteigen (Plan archivieren, später wieder aufnehmen)

## Nächster Schritt

**Phase 0 starten** in der nächsten Session:
1. Claude scriptet die Inventur (`unzip -l` über alle 68 ZIPs, HTML-Pages-Liste)
2. Output: `docs/envato-template-inventory.md`
3. User sichtet 5-10 Live-Demos, postet Pattern-Notes als nächste Iteration
4. Claude leitet daraus Phase-1-Pattern-Kandidaten ab
