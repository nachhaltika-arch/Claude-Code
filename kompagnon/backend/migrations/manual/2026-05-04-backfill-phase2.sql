-- Migration: Backfill phase_1 → phase_2 for projects with substantial briefings
-- Date:       2026-05-04
-- Author:     Claude Code (auto-generated, manual application required)
-- Context:    Fix in routers/briefings.py adds auto-marking of briefings as
--             submitted when 3+ substantive fields are filled. This script
--             applies the same logic to 11 already-existing stuck projects.
--
-- Affected project IDs: 3, 5, 6, 7, 9, 10, 11, 14, 16, 18, 19
-- These are the projects where the briefing has 3+ flat fields with >=10 chars.
-- Excluded: projects 1, 2, 8, 12, 13, 15, 17 (briefing too thin or empty).
--
-- Side-effects:  NONE. Pure data update. No emails, no Stripe, no Netlify.
--                The phase-2 welcome email is only triggered by the application
--                via scheduler.trigger_phase_change() — not by raw SQL updates.
--
-- How to run:    psql "$DATABASE_URL" -f 2026-05-04-backfill-phase2.sql
--                (Or paste into Render Dashboard SQL tab, run in one go.)
--
-- Workflow:      1. Run as-is — it ends with ROLLBACK; review output.
--                2. If output looks correct: change ROLLBACK to COMMIT, run again.
--                3. payment_status is NOT touched here — review per project manually.

BEGIN;

-- 1) Mark associated briefings as eingereicht
UPDATE briefings
SET status = 'eingereicht'
WHERE lead_id IN (
  SELECT lead_id FROM projects
  WHERE id IN (3, 5, 6, 7, 9, 10, 11, 14, 16, 18, 19)
)
  AND (status IN ('entwurf', 'offen') OR status IS NULL);

-- 2) Update projects: mark briefing received, transition phase_1 → phase_2
UPDATE projects p
SET
  has_briefing          = TRUE,
  briefing_submitted_at = COALESCE(
    p.briefing_submitted_at,
    (SELECT b.updated_at FROM briefings b WHERE b.lead_id = p.lead_id ORDER BY b.updated_at DESC LIMIT 1),
    NOW()
  ),
  status                = 'phase_2',
  current_phase         = 2,
  updated_at            = NOW()
WHERE p.id IN (3, 5, 6, 7, 9, 10, 11, 14, 16, 18, 19)
  AND p.status = 'phase_1';

-- 3) Verification — show resulting state for review
SELECT
  p.id              AS project_id,
  p.status          AS project_status,
  p.current_phase,
  p.has_briefing,
  p.briefing_submitted_at::date  AS submitted_on,
  p.payment_status,
  l.company_name,
  b.status          AS briefing_status
FROM projects p
LEFT JOIN leads l       ON l.id = p.lead_id
LEFT JOIN briefings b   ON b.lead_id = p.lead_id
WHERE p.id IN (3, 5, 6, 7, 9, 10, 11, 14, 16, 18, 19)
ORDER BY p.id;

-- ──────────────────────────────────────────────────────────────────────────────
-- ⚠️  REVIEW the SELECT output above before deciding.
-- ⚠️  Then run ONE of the following — never both, never neither:
ROLLBACK;
-- COMMIT;
-- ──────────────────────────────────────────────────────────────────────────────
