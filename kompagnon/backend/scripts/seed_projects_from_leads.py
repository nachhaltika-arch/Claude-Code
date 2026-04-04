#!/usr/bin/env python3
"""
Diagnostic + Seed Script: Projekte aus gewonnenen Leads anlegen.

Usage:
    cd kompagnon/backend
    python scripts/seed_projects_from_leads.py

    # Dry-run (kein Commit):
    python scripts/seed_projects_from_leads.py --dry-run

    # Ersten Lead auf 'won' setzen falls kein won-Lead existiert:
    python scripts/seed_projects_from_leads.py --force-win
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine

DRY_RUN = "--dry-run" in sys.argv
FORCE_WIN = "--force-win" in sys.argv

def run():
    with engine.connect() as conn:
        # ── 1. Projekttabelle ──────────────────────────────────────────────
        count = conn.execute(text("SELECT COUNT(*) FROM projects")).scalar()
        print(f"\n[1] Projekte in DB: {count}")

        rows = conn.execute(
            text("SELECT id, company_name, status, current_phase FROM projects LIMIT 5")
        ).fetchall()
        if rows:
            for r in rows:
                print(f"    id={r[0]} company={r[1]} status={r[2]} phase={r[3]}")
        else:
            print("    (keine Projekte)")

        # ── 2. Gewonnene Leads ─────────────────────────────────────────────
        won_leads = conn.execute(
            text("SELECT id, company_name, status FROM leads WHERE status = 'won'")
        ).fetchall()
        print(f"\n[2] Leads mit status='won': {len(won_leads)}")
        for r in won_leads:
            print(f"    id={r[0]} company={r[1]}")

        recent = conn.execute(
            text("SELECT id, company_name, status FROM leads ORDER BY created_at DESC LIMIT 5")
        ).fetchall()
        print(f"\n    Letzte 5 Leads:")
        for r in recent:
            print(f"    id={r[0]} company={r[1]} status={r[2]}")

        # ── 4. Falls kein won-Lead → ersten Lead auf 'won' setzen ──────────
        if not won_leads and FORCE_WIN:
            first = conn.execute(
                text("SELECT id, company_name FROM leads ORDER BY id LIMIT 1")
            ).fetchone()
            if first:
                print(f"\n[4] Setze Lead id={first[0]} ({first[1]}) auf status='won'")
                if not DRY_RUN:
                    conn.execute(
                        text("UPDATE leads SET status = 'won' WHERE id = :id"),
                        {"id": first[0]},
                    )
                    conn.commit()
                    won_leads = [(first[0], first[1], 'won')]
                else:
                    print("    [DRY-RUN] übersprungen")
            else:
                print("\n[4] Keine Leads gefunden – nichts zu tun.")

        # ── 3. Projekte aus won-Leads anlegen ──────────────────────────────
        if won_leads:
            insert_sql = text("""
                INSERT INTO projects (lead_id, status, start_date, created_at, updated_at,
                                      company_name, website_url, contact_name, contact_email)
                SELECT
                    l.id,
                    'phase_1',
                    NOW(), NOW(), NOW(),
                    l.company_name,
                    l.website_url,
                    l.contact_name,
                    l.email
                FROM leads l
                WHERE l.status = 'won'
                  AND NOT EXISTS (
                      SELECT 1 FROM projects p WHERE p.lead_id = l.id
                  )
            """)
            if not DRY_RUN:
                result = conn.execute(insert_sql)
                conn.commit()
                print(f"\n[3] Projekte angelegt: {result.rowcount}")
            else:
                print("\n[3] [DRY-RUN] INSERT würde ausgeführt werden")

        # ── 5. Ergebnis ────────────────────────────────────────────────────
        final_count = conn.execute(text("SELECT COUNT(*) FROM projects")).scalar()
        print(f"\n[5] Projekte in DB jetzt: {final_count}")
        if count == 0 and final_count == 0:
            print("\n    HINWEIS: Keine Leads mit status='won' gefunden.")
            print("    Nutze --force-win um den ersten Lead auf 'won' zu setzen,")
            print("    oder ändere manuell einen Lead-Status über das Frontend.")

if __name__ == "__main__":
    print("=" * 60)
    print("Projekt-Seed: won-Leads → projects")
    if DRY_RUN:
        print("MODUS: DRY-RUN (kein Commit)")
    print("=" * 60)
    run()
