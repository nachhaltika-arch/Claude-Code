---
name: Wiederaufnahme 2026-05-09 (Stand Ende 2026-05-09)
description: --brand-primary Audit komplett (~94 Migrationen über 44 Files); Envato Phase 0 Inventur fertig; nächster Strang ist Live-Demo-Sichtung durch User + Phase 1 (HERO+CTA Bundle) ableiten
type: project
originSessionId: beb8ceb2-66a6-4bb0-a141-bf118d2e4dc0
---
**Why:** Heute drei Stränge durchgezogen — (1) iterativer `--brand-primary` → `-mid` Audit über 44 Files in 3 Commits (Top-Tier + Mid-Tier + Long-Tail systematisch), (2) Envato Phase 0 Inventur mit `docs/envato-template-inventory.md` (68 Templates gescannt, Tier-Empfehlungen für Live-Demo-Sichtung), (3) keine Pause/Feierabend-Angebote mehr — User wollte explizit alles abarbeiten.

**How to apply:** Wenn nächste Session startet, zuerst nachschauen ob David parallel auf themeforest.net die Live-Demos der Tier-1/Tier-2-Kandidaten gesichtet hat. Wenn ja → Phase 1 (HERO + CTA) Pattern-Kandidaten ableiten und als Wireframes neutralisiert in Library aufnehmen. Wenn nein → User erinnern oder mit anderem Strang weiter (z.B. Long-Tail Browser-Check).

---

## Heute komplette Push-Historie

| Commit | Was |
|--------|-----|
| `ba3bbba` | Top-Tier + Mid-Tier `--brand-primary` Audit (15 Files, 67 Stellen) |
| `09225c0` | Envato Phase 0 Inventur (`docs/envato-template-inventory.md`, 123 Zeilen, 68 Templates + 14 Tier-Empfehlungen) |
| `c257601` | Long-Tail `--brand-primary` Cleanup (29 Files, 39 Stellen) |
| `65a047b` | Status-Color-Bugs gefixt (AuditHistory + MarginBadge → status-danger-text) |
| `680974b` | Legacy kc-* Color/Font Aliases retired (Phase A, 19 Aliases entfernt) |
| `1e69d2a` | Inline-style #008EAA hex → var(--kc-mid) (33 Files, 59 Stellen) |
| `968a479` | Dead-code: ProzessFlowV2.jsx gelöscht (484 Zeilen) |
| `c12a9a8` | rgba alpha-Tokens konsolidiert (6 Helper-Tokens, 19 Files, 34 Stellen) |
| `e823b80` | Ternary inline-style + accentColor #008EAA → var(--kc-mid) (15 Files) |
| `e437026` | PricingSection Starter — badgeColor + ctaBg final cleanup |
| `67e2971` | Yellow #FAE600 + Dark Teal #004F59 → tokens (15 Files, 36 Stellen) |
| `c00bb94` | Border-shorthand + gradients + alpha-suffix hex (#008EAA33 etc.) (14 Files) |
| `14dc78d` | Backend: print() → logger (4 Stellen) + duplicate logger removed |
| `104024f` | Backend invoice_pdf: BIC/IBAN/Bank-Placeholder Bug fixed |
| `ae7706a` + `546ed33` | (User-Hotfix parallel) load dotenv in database.py before DATABASE_URL is read |
| `79e7c85` | Frontend: 4 Debug console.log statements entfernt |

**Total heute:** 12 Commits, ~280+ stellen migriert. Komplette Hex-Migration für inline-style + ternary + accentColor + alpha + border-shorthand + gradient + alpha-suffix-hex. Token-Cleanup hier formal abgeschlossen.

**Token-System Final-State 2026-05-09:**
- `tokens.css` = Single Source of Truth (Brand-Primitives kc-dark/mid/yellow + 6 Mid-Teal Alpha-Helper)
- `index.css` Z. 64-137 = kc-* Numeric Scale Tokens (Phase B closed, legitimes System)
- 0 inline `#008EAA`/`#FAE600`/`#004F59` Hex in CSS-Kontexten (außer JS-Defaults/SVG/Consts/library — intentional)
- Brand-Color-Indirection: alle Consumer-Code geht über semantische Tokens (--brand-primary, --kc-mid, --kc-yellow), Primitive nur in tokens.css definiert

Verbliebene Hex-Stellen (intentional KEEP):
- JS-Defaults: `|| '#008EAA'`, `useState(...)`, `const X = '#HEX'`
- SVG fill="..." Attribute
- library/*.html (standalone Customer-Render)
- library/index.json (Config)
- 3rd-Party Brand-Colors: #1877F2 (FB), #0A66C2 (LI), #EA4335 (Google), etc.
- Dunklere Variants: #006680, #006880, #003840 (manual brand-shades)

---

## Audit-Ergebnis: was migriert vs. was behalten

**Migriert auf `--brand-primary-mid`:**
- Text-only Links (`<a>`, `<Link>`)
- Tertiary-Buttons (text-only auf bg-active/transparent)
- Outline-Buttons (border + color)
- Focus/Hover borderColor (`onFocus`, `onMouseEnter`)
- Chip-Text auf brand-primary-light bg (`background+color`-Pattern)
- Kleine Uppercase-Labels/Tags
- Inline-Akzent-Text in Body (`<strong>` in `<p>`)
- Required-Asterisks (`*`)
- Breadcrumbs
- Display-URLs (mono-font)

**Behalten auf `--brand-primary` (Dark Teal):**
- Primary-Action Button-Backgrounds
- KPI-Werte (fontSize 16+, fontWeight 700+; Currency, Percentages)
- Active-State Borders/Tabs/Cards
- Brand-Surfaces (Header-Cards, Progress-Bars)
- Spinner borderTopColor
- Save-Button-Text auf weiß (auf Brand-Header-Surface)
- Config-Color-Keys (Sidebar nav-categories, Tickets/Feedback type-mapping, DomainImport stat-row colors)
- Ternary State-Indicators (`isActive ? brand-primary : ...`)

---

## Lessons / Refinement der Audit-Methode

1. **Code-Vorfilter > Browser-First** — Memory von 08.05 sagte "Browser-Check zuerst", aber pragmatisch war Code-driven schneller: grep nach `color: 'var(--brand-primary)'` (113 Treffer) lieferte direkt die Audit-Kandidaten, dann je Stelle entscheiden. Browser-Check kann nachgeholt werden.

2. **Bulk-Patterns identifizieren** — `e.target.style.borderColor = 'var(--brand-primary)'` (Focus) und `background: 'var(--brand-primary-light)', color: 'var(--brand-primary)'` (Chips) sind eindeutig migrierbare Patterns über alle Files via `replace_all`. Spart pro File 1-2 Edit-Calls.

3. **Config vs. Inline** — Configs in const-objects (z.B. `Sidebar nav config`, `Tickets type-mapping`) sind Brand-Identitäts-Definitionen → KEEP. Inline-Style auf einzelnem Element ist Akzent-Verwendung → MIGRATE.

4. **Spinner und State-Borders bleiben dark** — alle Animation-Indikatoren (`borderTopColor` auf spinning circles) und alle Active-State Borders/Tabs sind Dark Teal — visuelle Konsistenz mit den Primary-Buttons.

---

## Envato Phase 0 — Inventur fertig

**Output:** `docs/envato-template-inventory.md` — 123 Zeilen.
- 68 Templates gescannt mit Tech-Stack-Detection (HTML/Tailwind/React/PHP/Other-FW)
- Filter: macOS `._` Metadata, Documentation/, vendor assets ausgeschlossen
- Tier-Empfehlungen für User Live-Demo-Sichtung:
  - **Tier 1 Tailwind:** agon, bricknet, travel-tour-booking
  - **Tier 2 SHK-Adjacent:** arkdin, pakkapati, roofsie, freshflow, phone-repair
  - **Tier 3 Multipurpose:** digmox, potu, techex
  - **Tier 4 Pattern-Pool:** astrax (2675 Pages!), invena (188), lightwire (97)

**User-Aufgabe (nächste Schritte):**
1. ~10 Live-Demos auf themeforest.net sichten
2. Pattern-Notes pro Template posten (z.B. "Bricknet: Service-Comparison-Table sehenswert")
3. Claude leitet daraus Phase-1-Pattern-Kandidaten (HERO + CTA Bundle) ab

---

## Bekannte legacy-Issues (separat fixen, NICHT heute angefasst)

- **AuditHistory.jsx:13** — `'Nicht konform': { color: 'var(--brand-primary)', icon: '⛔' }` — Status-Config nutzt brand-color für negative Status. Sollte vermutlich `--status-danger-text` sein.
- **MarginBadge.jsx:17** — `red: { background: 'var(--kc-rot-subtle)', color: 'var(--brand-primary)' }` — gleiche Inkonsistenz, brand-color auf rotem bg. Sollte rot-Text sein.
- **Legacy-Aliases (`--kc-rot` etc.)** — index.css Z. 65-134, Backwards-Compat-Aliases sind weiterhin definiert. Wenn Tabula rasa gewollt: ausmustern. Sonst lassen.

---

## Production-Stand 2026-05-09

- Staging-Frontend deployt automatisch auf jeden push, jetzt mit cleanup-Effekten live
- Produktiv noch auf PR #33-Stand (gemerged 2026-05-08 18:40 UTC)
- Nächster Friday-Cadence-PR: 2026-05-15? Cleanup ist klein-genug-und-ungefährlich für ad-hoc PR.

---

## Nächste-Session-Optionen

| Option | Aufwand | Wert |
|--------|---------|------|
| Phase 1 starten (User hat Pattern-Notes) | 2-3h | Hoch — direkter Library-Zuwachs |
| Browser-Check Audit-Ergebnis | 30min | Mittel — visuelle Validierung, eventuelle Nachjustage |
| Legacy-Aliases (`--kc-rot` etc.) ausmustern | 1-2h | Niedrig — kosmetisch |
| AuditHistory.jsx + MarginBadge.jsx Status-Color-Bug fixen | 30min | Mittel — kleine Konsistenz-Wins |
| PR `staging → main` öffnen für heutige Cleanups | 5min | Hoch wenn Cadence-Tag (Fr) |
