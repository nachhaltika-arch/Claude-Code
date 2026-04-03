"""
One-time fix: link Mark Longhin's user account to the eisistcool.de lead.

Run from the kompagnon/backend directory:
    python scripts/fix_link_eisistcool.py

Idempotent — safe to run multiple times.
"""
import sys
import os

# Add backend root to path so database.py etc. are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine


def run():
    with engine.connect() as conn:

        # 1. Find Mark Longhin's user
        result = conn.execute(text(
            "SELECT id, email, lead_id FROM users "
            "WHERE email ILIKE '%longhin%' OR email ILIKE '%eisistcool%'"
        ))
        users = result.fetchall()
        print("=== Users found ===")
        for u in users:
            print(f"  id={u[0]}  email={u[1]}  lead_id={u[2]}")

        if not users:
            print("ERROR: No user found for Mark Longhin / eisistcool. Aborting.")
            sys.exit(1)

        if len(users) > 1:
            print("WARNING: Multiple users found — using the first one.")
        user_id = users[0][0]
        current_lead_id = users[0][2]
        print(f"\nTarget user_id = {user_id}  (current lead_id = {current_lead_id})")

        # 2. Find the lead
        result = conn.execute(text(
            "SELECT id, company_name, website_url FROM leads "
            "WHERE website_url ILIKE '%eisistcool%' "
            "ORDER BY id LIMIT 1"
        ))
        lead = result.fetchone()

        if not lead:
            # Try usercards view
            result = conn.execute(text(
                "SELECT id, company_name, website_url FROM usercards "
                "WHERE website_url ILIKE '%eisistcool%' "
                "ORDER BY id LIMIT 1"
            ))
            lead = result.fetchone()

        if lead:
            lead_id = lead[0]
            print(f"\nLead found: id={lead_id}  company='{lead[1]}'  url='{lead[2]}'")
        else:
            print("\nNo existing lead found — creating one.")
            result = conn.execute(text(
                "INSERT INTO leads (company_name, website_url, status, created_at, updated_at) "
                "VALUES ('Eisistcool', 'https://eisistcool.de', 'customer', NOW(), NOW()) "
                "RETURNING id"
            ))
            lead_id = result.fetchone()[0]
            print(f"  Created lead id={lead_id}")

        # 3. Link user → lead
        if current_lead_id == lead_id:
            print(f"\nAlready linked (lead_id={lead_id}). Nothing to do.")
        else:
            conn.execute(text(
                "UPDATE users SET lead_id = :lead_id WHERE id = :user_id"
            ), {"lead_id": lead_id, "user_id": user_id})
            conn.commit()
            print(f"\nDone: users.id={user_id} → lead_id={lead_id}")


if __name__ == "__main__":
    run()
