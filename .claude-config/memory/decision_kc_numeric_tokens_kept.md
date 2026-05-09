---
name: kc-* Numeric Scale Tokens bleiben (Phase B closed)
description: kc-text-*, kc-leading-*, kc-tracking-*, kc-space-*, kc-radius-*, kc-transition-*, kc-container-* sind als legitimes Scale-System anerkannt — keine Migration auf modern, keine Inline-Werte
type: project
originSessionId: beb8ceb2-66a6-4bb0-a141-bf118d2e4dc0
---
**Why:** Datenanalyse 2026-05-09 nach Phase A (Color-Aliases retired) zeigte: ~60% der kc-numeric Tokens haben identische Werte zu modernen Tokens (naming-only Refactor → kein Mehrwert), ~20% haben echte Wert-Diffs (1-2px, visueller Schmerz ohne Gewinn), ~20% (tracking, container, text-4xl) haben gar keine modernen Equivalente. Kc-leading-`tight/normal/relaxed` ist semantisch besser als modern `leading-3xl/base/body` (intent- vs. size-based). User hat Sub-Option 3 (Lassen) gewählt.

**How to apply:** Wenn künftige Sessions Token-Cleanup vorschlagen wollen, NICHT Phase B wieder aufmachen. kc-numeric ist Scale-System, kein Legacy. Phase A (Color/Font Aliases) war der einzige sinnvolle Cleanup. Index.css Z. 60-62 Comment dokumentiert das bereits ("kc-* SCALE TOKENS — typography sizes, tracking, spacing, radius, transitions. Color/text/border/font aliases retired").

**Konkrete Wert-Diffs (Referenz, falls die Frage doch wieder hochkommt):**

| Kategorie | kc | Modern | Status |
|-----------|-----|--------|--------|
| Spacing (10) | 4-80px | 4-40px | identisch wo überlappend, kc hat mehr Werte |
| Leading (3) | 1.2/1.6/1.75 | sized 1.2-1.75 | identische Werte, kc-naming klarer |
| Typography xs-lg (4) | 12-18px | 11-17px | kc 1px größer |
| Typography xl-3xl (3) | 20-30px | 20-30px | identisch |
| Typography 4xl (1) | 36px | — | nur kc |
| Radius sm/md (2) | 2/6px | 4/8px | kc 2px kleiner |
| Radius lg/full (2) | 12px/9999px | 12px/9999px | identisch |
| Transitions (3) | ease, slow=400ms | cubic-bezier, slow=350ms | timing-function + slow duration diff |
| Tracking (4) | -0.02 bis 0.1em | — | nur kc |
| Container (2) | 1280px, clamp(...) | — | nur kc |

**Token-System Final-State 2026-05-09:**
- **tokens.css** = Single Source of Truth für Brand-Colors (kc-dark/mid/yellow), Surfaces, Text, Border, Status, Sizes (radius/space/text/leading), Transitions
- **index.css** Z. 64-137 = kc-* Scale Tokens (legitim, complementary)
- **Phase A retired (2026-05-09):** kc-rot, kc-anthrazit-*, kc-text-{primaer,sekundaer,subtil,invers}, kc-mittel, kc-rand, kc-success/warning/info, kc-font-{display,body,mono}
- **6 neue Alpha-Helper:** kc-mid-a-08/12/20/25/30/50 (für Mid-Teal Transparenzen)
