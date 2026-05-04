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
    # Academy: Kurse-Tabelle (idempotent für neue DBs)
    """CREATE TABLE IF NOT EXISTS academy_courses (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL DEFAULT '',
        description TEXT DEFAULT '',
        thumbnail_url TEXT DEFAULT '',
        is_published BOOLEAN DEFAULT FALSE,
        target_audience TEXT DEFAULT 'both',
        category VARCHAR(100) DEFAULT '',
        category_color VARCHAR(50) DEFAULT 'primary',
        audience VARCHAR(50) DEFAULT 'employee',
        formats TEXT DEFAULT '["text"]',
        linear_progress BOOLEAN DEFAULT FALSE,
        sort_order INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW()
    )""",
    # Academy: Inhalt wandert in Lektionen — content_text und video_url entfernen
    "ALTER TABLE academy_courses DROP COLUMN IF EXISTS content_text",
    "ALTER TABLE academy_courses DROP COLUMN IF EXISTS video_url",
    # Academy: Module-Tabelle
    """CREATE TABLE IF NOT EXISTS academy_modules (
        id SERIAL PRIMARY KEY,
        course_id INT REFERENCES academy_courses(id) ON DELETE CASCADE,
        title TEXT NOT NULL DEFAULT '',
        position INT DEFAULT 0,
        is_locked BOOLEAN DEFAULT FALSE,
        sort_order INT DEFAULT 0
    )""",
    # Academy: Lektionen-Tabelle
    """CREATE TABLE IF NOT EXISTS academy_lessons (
        id SERIAL PRIMARY KEY,
        module_id INT REFERENCES academy_modules(id) ON DELETE CASCADE,
        title TEXT NOT NULL DEFAULT '',
        position INT DEFAULT 0,
        type TEXT DEFAULT 'text',
        content_url TEXT DEFAULT '',
        content_text TEXT DEFAULT '',
        video_url TEXT DEFAULT '',
        file_url TEXT DEFAULT '',
        duration_minutes INT DEFAULT 0,
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
    # Academy: neue Spalten academy_courses
    "ALTER TABLE academy_courses ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500) DEFAULT ''",
    "ALTER TABLE academy_courses ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT FALSE",
    "ALTER TABLE academy_courses ADD COLUMN IF NOT EXISTS target_audience VARCHAR(20) DEFAULT 'both'",
    # Academy: neue Spalten academy_modules
    "ALTER TABLE academy_modules ADD COLUMN IF NOT EXISTS position INT DEFAULT 0",
    "ALTER TABLE academy_modules ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE",
    # Academy: neue Spalten academy_lessons
    "ALTER TABLE academy_lessons ADD COLUMN IF NOT EXISTS position INT DEFAULT 0",
    "ALTER TABLE academy_lessons ADD COLUMN IF NOT EXISTS type VARCHAR(20) DEFAULT 'text'",
    "ALTER TABLE academy_lessons ADD COLUMN IF NOT EXISTS content_url VARCHAR(500) DEFAULT ''",
    "ALTER TABLE academy_lessons ADD COLUMN IF NOT EXISTS duration_minutes INT DEFAULT 0",
    # Academy: Fortschritt (quiz-fähig, mit Score)
    """CREATE TABLE IF NOT EXISTS academy_progress (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        lesson_id INT REFERENCES academy_lessons(id) ON DELETE CASCADE,
        completed_at TIMESTAMP,
        score NUMERIC(5,2)
    )""",
    # Academy: Zertifikate
    """CREATE TABLE IF NOT EXISTS academy_certificates (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        course_id INT REFERENCES academy_courses(id) ON DELETE CASCADE,
        issued_at TIMESTAMP DEFAULT NOW(),
        certificate_code VARCHAR(64) UNIQUE NOT NULL
    )""",
    # Academy: Quiz-Fragen pro Lektion
    """CREATE TABLE IF NOT EXISTS academy_quiz_questions (
        id SERIAL PRIMARY KEY,
        lesson_id INT REFERENCES academy_lessons(id) ON DELETE CASCADE,
        question TEXT NOT NULL,
        answers_json TEXT DEFAULT '[]',
        sort_order INT DEFAULT 0
    )""",
    # Crawler: Jobs
    """CREATE TABLE IF NOT EXISTS crawl_jobs (
        id SERIAL PRIMARY KEY,
        customer_id INT,
        status VARCHAR(20) DEFAULT 'pending',
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        total_urls INT DEFAULT 0
    )""",
    # PageSpeed columns on leads table
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_mobile_score INTEGER",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_desktop_score INTEGER",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_lcp_mobile FLOAT",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_cls_mobile FLOAT",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_inp_mobile FLOAT",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_fcp_mobile FLOAT",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_checked_at TIMESTAMP",
    # Crawler: Ergebnisse
    """CREATE TABLE IF NOT EXISTS crawl_results (
        id SERIAL PRIMARY KEY,
        customer_id INT,
        job_id INT REFERENCES crawl_jobs(id) ON DELETE CASCADE,
        url VARCHAR(2000) NOT NULL,
        status_code INT,
        depth INT DEFAULT 0,
        load_time NUMERIC(8,3),
        crawled_at TIMESTAMP DEFAULT NOW()
    )""",
    # ── Seiten-Manager ──────────────────────────────────────
    """CREATE TABLE IF NOT EXISTS public_pages (
        id              SERIAL PRIMARY KEY,
        slug            VARCHAR(200) UNIQUE NOT NULL,
        name            VARCHAR(200) NOT NULL,
        description     TEXT DEFAULT '',
        page_type       VARCHAR(50) DEFAULT 'custom',
        status          VARCHAR(20) DEFAULT 'draft',
        html_content    TEXT DEFAULT '',
        grapesjs_data   JSONB DEFAULT '{}',
        css_content     TEXT DEFAULT '',
        react_component VARCHAR(100) DEFAULT '',
        product_id      INTEGER REFERENCES products(id) ON DELETE SET NULL,
        template_id     INTEGER,
        meta_title      VARCHAR(200) DEFAULT '',
        meta_description VARCHAR(300) DEFAULT '',
        published_at    TIMESTAMP,
        created_at      TIMESTAMP DEFAULT NOW(),
        updated_at      TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS page_templates (
        id              SERIAL PRIMARY KEY,
        name            VARCHAR(200) NOT NULL,
        description     TEXT DEFAULT '',
        category        VARCHAR(100) DEFAULT 'allgemein',
        thumbnail_url   VARCHAR(500) DEFAULT '',
        grapesjs_data   JSONB DEFAULT '{}',
        html_content    TEXT DEFAULT '',
        css_content     TEXT DEFAULT '',
        is_builtin      BOOLEAN DEFAULT FALSE,
        sort_order      INTEGER DEFAULT 0,
        created_at      TIMESTAMP DEFAULT NOW()
    )""",
    # Seed: alle bekannten öffentlichen Seiten vorbelegen
    """INSERT INTO public_pages (slug, name, page_type, status, react_component)
       VALUES
         ('/', 'Landing Page', 'landing', 'live', 'Landing'),
         ('/paket/starter', 'Paket: Starter', 'paket', 'live', 'PackageStarter'),
         ('/paket/kompagnon', 'Paket: Kompagnon', 'paket', 'live', 'PackageKompagnon'),
         ('/paket/premium', 'Paket: Premium', 'paket', 'draft', 'PackagePremium'),
         ('/checkout', 'Checkout', 'transaktional', 'live', 'Checkout'),
         ('/checkout/success', 'Checkout Erfolg', 'transaktional', 'draft', 'CheckoutSuccess'),
         ('/login', 'Login', 'auth', 'live', 'Login'),
         ('/register', 'Registrierung', 'auth', 'live', 'Register'),
         ('/reset-password', 'Passwort zurücksetzen', 'auth', 'live', 'ResetPassword'),
         ('/portal/login', 'Kunden-Portal Login', 'portal', 'live', 'PortalLogin'),
         ('/impressum', 'Impressum', 'legal', 'live', 'Impressum'),
         ('/datenschutz', 'Datenschutz', 'legal', 'live', 'Datenschutz'),
         ('/barrierefreiheit', 'Barrierefreiheit', 'legal', 'live', 'Barrierefreiheit')
       ON CONFLICT (slug) DO NOTHING
    """,
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
