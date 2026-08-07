---
name: PR-Cadence — staging→main ausschließlich freitags
description: Niemals außerhalb Freitag PR staging→main vorschlagen oder öffnen — auch nicht wenn Commits "fertig/sauber" wirken
type: feedback
originSessionId: beb8ceb2-66a6-4bb0-a141-bf118d2e4dc0
---
**Regel:** PR `staging → main` wird **nur freitags** geöffnet und gemerged. Alle anderen Wochentage = staging-Entwicklung, sammeln, kein PR.

**Why:** Bestätigt 2026-05-09 nach Vorschlag meinerseits, am Samstag PR zu öffnen. Cadence ist verbindlich, nicht "wenn es passt". Steht auch in `weekly_release_cadence.md` und CLAUDE.md, aber wurde von mir mehrfach umgangen mit „heute Sa, kein Cadence-Tag — aber PR jetzt aufmachen, du mergst wann du willst" — explizit zurückgewiesen.

**How to apply:**
- Mo-Do: niemals PR staging→main als Option anbieten — auch nicht „du kannst später mergen"
- Fr: PR öffnen ist erlaubt/erwartet
- Wenn Commit-Set heute (Mo-Do) groß und sauber ist → einfach auf staging stehen lassen, keine Frage zu PR
- Bei Unsicherheit über Wochentag: aktuelles Datum prüfen, nicht raten
