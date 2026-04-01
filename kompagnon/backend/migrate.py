"""
Database migration script for KOMPAGNON.
Adds new columns to existing PostgreSQL/SQLite tables.
Run automatically on startup or manually: python migrate.py
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kompagnon.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

migrations = [
    # Scraper fields
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS scraped_phone VARCHAR DEFAULT ''",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS scraped_email VARCHAR DEFAULT ''",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS scraped_description VARCHAR DEFAULT ''",
    # Granular score fields — Rechtliche Compliance
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_impressum INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_datenschutz INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_cookie INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_bfsg INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_urheberrecht INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_ecommerce INTEGER DEFAULT 0",
    # Technische Performance
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_lcp INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_cls INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_inp INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_mobile INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_bilder INTEGER DEFAULT 0",
    # Hosting & Infrastruktur
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_anbieter INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_uptime INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_http INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_backup INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_cdn INTEGER DEFAULT 0",
    # Barrierefreiheit
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_kontrast INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_tastatur INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_screenreader INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_lesbarkeit INTEGER DEFAULT 0",
    # Sicherheit & Datenschutz
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_ssl INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_header INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_drittanbieter INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_formulare INTEGER DEFAULT 0",
    # SEO & Sichtbarkeit
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS se_seo INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS se_schema INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS se_lokal INTEGER DEFAULT 0",
    # Inhalt & Nutzererfahrung
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_erstindruck INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_cta INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_navigation INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_vertrauen INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_content INTEGER DEFAULT 0",
    "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_kontakt INTEGER DEFAULT 0",
    # Academy: linear_progress flag
    "ALTER TABLE academy_courses ADD COLUMN IF NOT EXISTS linear_progress BOOLEAN DEFAULT FALSE",
    # Academy: Inhalt wandert in Lektionen — content_text und video_url entfernen
    "ALTER TABLE academy_courses DROP COLUMN IF EXISTS content_text",
    "ALTER TABLE academy_courses DROP COLUMN IF EXISTS video_url",
    # Academy: Module-Tabelle
    """CREATE TABLE IF NOT EXISTS academy_modules (
        id SERIAL PRIMARY KEY,
        course_id INT REFERENCES academy_courses(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        sort_order INT DEFAULT 0
    )""",
    # Academy: Lektionen-Tabelle
    """CREATE TABLE IF NOT EXISTS academy_lessons (
        id SERIAL PRIMARY KEY,
        module_id INT REFERENCES academy_modules(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        content_text TEXT,
        video_url VARCHAR(500),
        file_url VARCHAR(500),
        sort_order INT DEFAULT 0
    )""",
    # Academy: Checklisten-Punkte pro Lektion (JSON)
    "ALTER TABLE academy_lessons ADD COLUMN IF NOT EXISTS checklist_items_json TEXT DEFAULT '[]'",
    # Academy: Lernfortschritt je Lektion
    """CREATE TABLE IF NOT EXISTS academy_lesson_progress (
        id SERIAL PRIMARY KEY,
        user_id INT,
        lesson_id INT REFERENCES academy_lessons(id) ON DELETE CASCADE,
        completed BOOLEAN DEFAULT FALSE,
        completed_at TIMESTAMP
    )""",
]


def run_migrations():
    """Execute all pending migrations."""
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                print(f"OK: {sql[:60]}...")
            except Exception as e:
                print(f"Skip: {e}")
        conn.commit()
    print("Migration abgeschlossen!")


if __name__ == "__main__":
    run_migrations()
