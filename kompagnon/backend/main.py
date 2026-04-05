"""
KOMPAGNON Automation System - FastAPI Entry Point
Runs the complete backend with scheduler, DB, and all routers.

Usage:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import os
import json
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

logger = logging.getLogger(__name__)


# Custom JSONResponse that does NOT escape Unicode (ä, ö, ü, ß, €)
class UnicodeJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

# Initialize database and seeders
from database import init_db, get_db
from seed_checklists import seed_checklists

# Import all routers
from routers import (
    usercards_router,
    leads_alias_router,
    usercards_customers_alias_router,
    leads_router,
    customers_alias_router,
    projects_router,
    agents_router,
    customers_router,
    automations_router,
    audit_router,
    auth_router,
    admin_router,
    scraper_router,
    settings_router,
    payments_router,
    tickets_router,
    cms_connect_router,
    portal_router,
)

# Import scheduler
from automations import start_scheduler, stop_scheduler, get_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _run_migrations():
    """Führt alle fehlenden Spalten-Migrationen aus."""
    from database import engine
    migrations = [
        # NOT NULL Constraints entfernen
        "ALTER TABLE leads ALTER COLUMN contact_name DROP NOT NULL",
        "ALTER TABLE leads ALTER COLUMN phone DROP NOT NULL",
        "ALTER TABLE leads ALTER COLUMN email DROP NOT NULL",
        "ALTER TABLE leads ALTER COLUMN city DROP NOT NULL",
        "ALTER TABLE leads ALTER COLUMN trade DROP NOT NULL",
        "ALTER TABLE leads ALTER COLUMN notes DROP NOT NULL",
        "ALTER TABLE leads ALTER COLUMN website_screenshot DROP NOT NULL",
        # Bestehende Migrations
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS scraped_phone VARCHAR DEFAULT ''",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS scraped_email VARCHAR DEFAULT ''",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS scraped_description VARCHAR DEFAULT ''",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_impressum INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_datenschutz INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_cookie INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_bfsg INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_urheberrecht INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_ecommerce INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_lcp INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_cls INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_inp INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_mobile INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_bilder INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_anbieter INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_uptime INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_http INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_backup INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_cdn INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_kontrast INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_tastatur INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_screenreader INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_lesbarkeit INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_ssl INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_header INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_drittanbieter INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_formulare INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS se_seo INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS se_schema INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS se_lokal INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_erstindruck INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_cta INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_navigation INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_vertrauen INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_content INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_kontakt INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS screenshot_base64 TEXT DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS analysis_score INTEGER DEFAULT 0",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS geo_score INTEGER DEFAULT 0",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS website_screenshot TEXT DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS street VARCHAR DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS house_number VARCHAR DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS postal_code VARCHAR DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS legal_form VARCHAR DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS vat_id VARCHAR DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS register_number VARCHAR DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS register_court VARCHAR DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ceo_first_name VARCHAR DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ceo_last_name VARCHAR DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS display_name VARCHAR DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS customer_token VARCHAR UNIQUE",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS customer_token_created_at TIMESTAMP",
        """CREATE TABLE IF NOT EXISTS briefings (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
            projektrahmen TEXT DEFAULT '{}',
            positionierung TEXT DEFAULT '{}',
            zielgruppe TEXT DEFAULT '{}',
            wettbewerb TEXT DEFAULT '{}',
            inhalte TEXT DEFAULT '{}',
            funktionen TEXT DEFAULT '{}',
            branding TEXT DEFAULT '{}',
            struktur TEXT DEFAULT '{}',
            hosting TEXT DEFAULT '{}',
            seo TEXT DEFAULT '{}',
            projektplan TEXT DEFAULT '{}',
            freigaben TEXT DEFAULT '{}',
            status VARCHAR DEFAULT 'offen',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(lead_id)
        )""",
        """CREATE TABLE IF NOT EXISTS support_tickets (
            id SERIAL PRIMARY KEY, ticket_number VARCHAR UNIQUE NOT NULL,
            user_id INTEGER, user_email VARCHAR DEFAULT '', user_name VARCHAR DEFAULT '',
            type VARCHAR DEFAULT 'feedback', priority VARCHAR DEFAULT 'medium', status VARCHAR DEFAULT 'open',
            title VARCHAR NOT NULL, description TEXT NOT NULL, page_url VARCHAR DEFAULT '',
            browser_info VARCHAR DEFAULT '', screenshot_base64 TEXT DEFAULT '', admin_notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW(), resolved_at TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS academy_courses (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT DEFAULT '',
            thumbnail_url VARCHAR(500) DEFAULT '',
            is_published BOOLEAN DEFAULT FALSE,
            target_audience VARCHAR(20) DEFAULT 'both',
            category VARCHAR(100) DEFAULT '',
            category_color VARCHAR(50) DEFAULT 'primary',
            audience VARCHAR(20) DEFAULT 'employee',
            formats TEXT DEFAULT '["text"]',
            content_text TEXT DEFAULT '',
            video_url VARCHAR(500) DEFAULT '',
            linear_progress BOOLEAN DEFAULT FALSE,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        # Missing columns on academy_courses (for existing deployments)
        "ALTER TABLE academy_courses ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500) DEFAULT ''",
        "ALTER TABLE academy_courses ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT FALSE",
        "ALTER TABLE academy_courses ADD COLUMN IF NOT EXISTS target_audience VARCHAR(20) DEFAULT 'both'",
        "ALTER TABLE academy_courses ADD COLUMN IF NOT EXISTS linear_progress BOOLEAN DEFAULT FALSE",
        """CREATE TABLE IF NOT EXISTS academy_checklist_items (
            id SERIAL PRIMARY KEY,
            course_id INTEGER REFERENCES academy_courses(id) ON DELETE CASCADE,
            label VARCHAR(500) NOT NULL,
            sort_order INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS academy_modules (
            id SERIAL PRIMARY KEY,
            course_id INTEGER REFERENCES academy_courses(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            position INTEGER DEFAULT 0,
            is_locked BOOLEAN DEFAULT FALSE,
            sort_order INTEGER DEFAULT 0
        )""",
        # Missing columns on academy_modules (for existing deployments)
        "ALTER TABLE academy_modules ADD COLUMN IF NOT EXISTS position INTEGER DEFAULT 0",
        "ALTER TABLE academy_modules ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE",
        """CREATE TABLE IF NOT EXISTS academy_lessons (
            id SERIAL PRIMARY KEY,
            module_id INTEGER REFERENCES academy_modules(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            position INTEGER DEFAULT 0,
            type VARCHAR(20) DEFAULT 'text',
            content_text TEXT DEFAULT '',
            content_url VARCHAR(500) DEFAULT '',
            video_url VARCHAR(500) DEFAULT '',
            file_url VARCHAR(500) DEFAULT '',
            duration_minutes INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            checklist_items_json TEXT DEFAULT '[]'
        )""",
        # Missing columns on academy_lessons (for existing deployments)
        "ALTER TABLE academy_lessons ADD COLUMN IF NOT EXISTS position INTEGER DEFAULT 0",
        "ALTER TABLE academy_lessons ADD COLUMN IF NOT EXISTS type VARCHAR(20) DEFAULT 'text'",
        "ALTER TABLE academy_lessons ADD COLUMN IF NOT EXISTS content_url VARCHAR(500) DEFAULT ''",
        "ALTER TABLE academy_lessons ADD COLUMN IF NOT EXISTS duration_minutes INTEGER DEFAULT 0",
        "ALTER TABLE academy_lessons ADD COLUMN IF NOT EXISTS checklist_items_json TEXT DEFAULT '[]'",
        """CREATE TABLE IF NOT EXISTS academy_lesson_progress (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            lesson_id INTEGER REFERENCES academy_lessons(id) ON DELETE CASCADE,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS academy_progress (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            lesson_id INTEGER REFERENCES academy_lessons(id) ON DELETE CASCADE,
            completed_at TIMESTAMP,
            score FLOAT
        )""",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_academy_progress ON academy_progress(user_id, lesson_id)",
        """CREATE TABLE IF NOT EXISTS academy_certificates (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            course_id INTEGER REFERENCES academy_courses(id) ON DELETE CASCADE,
            issued_at TIMESTAMP DEFAULT NOW(),
            certificate_code VARCHAR(64) UNIQUE NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS academy_quiz_questions (
            id SERIAL PRIMARY KEY,
            lesson_id INTEGER REFERENCES academy_lessons(id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            answers_json TEXT DEFAULT '[]',
            sort_order INTEGER DEFAULT 0
        )""",
        # Note: users + user_sessions tables are created by init_db() via SQLAlchemy
        """CREATE TABLE IF NOT EXISTS academy_customer_access (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            course_id INTEGER REFERENCES academy_courses(id) ON DELETE CASCADE,
            assigned_at TIMESTAMP DEFAULT NOW(),
            assigned_by INTEGER
        )""",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_academy_customer_access ON academy_customer_access(customer_id, course_id)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS mobile VARCHAR(20)",
        # PageSpeed columns on leads table
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_mobile_score INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_desktop_score INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_lcp_mobile FLOAT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_cls_mobile FLOAT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_inp_mobile FLOAT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_fcp_mobile FLOAT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS pagespeed_checked_at TIMESTAMP",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS geschaeftsfuehrer VARCHAR",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS whatsapp_nummer VARCHAR(50)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS kampagne_quelle VARCHAR(100)",
        "CREATE TABLE IF NOT EXISTS lead_domains (id SERIAL PRIMARY KEY, lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE, url VARCHAR(500) NOT NULL, label VARCHAR(100) DEFAULT '', is_primary BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW())",
        "CREATE INDEX IF NOT EXISTS idx_lead_domains_lead_id ON lead_domains(lead_id)",
        # Courses table + optional columns
        """CREATE TABLE IF NOT EXISTS courses (
            id                SERIAL PRIMARY KEY,
            title             VARCHAR(255) NOT NULL,
            description       TEXT DEFAULT '',
            category          VARCHAR(50) DEFAULT 'intern',
            thumbnail_color   VARCHAR(20) DEFAULT '#008eaa',
            chapter_count     INTEGER DEFAULT 0,
            participant_count INTEGER DEFAULT 0,
            duration_minutes  INTEGER DEFAULT 0,
            created_at        TIMESTAMP DEFAULT NOW(),
            created_by        INTEGER REFERENCES users(id) ON DELETE SET NULL
        )""",
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS thumbnail_color VARCHAR(20) DEFAULT '#008eaa'",
        # CMS connection columns on customers
        # ── Portal tables ──────────────────────────────────────────────────────
        # Ensure lead_id column exists on projects (already in ORM model, safety net)
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS lead_id INTEGER REFERENCES leads(id)",
        "CREATE TABLE IF NOT EXISTS portal_messages (id SERIAL PRIMARY KEY, customer_id INTEGER NOT NULL, sender_role VARCHAR(50), text TEXT, created_at TIMESTAMP DEFAULT NOW())",
        "CREATE INDEX IF NOT EXISTS idx_portal_messages_cid ON portal_messages(customer_id)",
        "CREATE TABLE IF NOT EXISTS portal_documents (id SERIAL PRIMARY KEY, customer_id INTEGER NOT NULL, filename VARCHAR(255), filepath VARCHAR(500), created_at TIMESTAMP DEFAULT NOW())",
        "CREATE INDEX IF NOT EXISTS idx_portal_documents_cid ON portal_documents(customer_id)",
        # CMS connection columns on customers
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS cms_type VARCHAR(50)",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS cms_url VARCHAR(500)",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS cms_username VARCHAR(200)",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS cms_password_encrypted TEXT",
        # PageSpeed columns on customers
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS pagespeed_mobile_score INTEGER",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS pagespeed_desktop_score INTEGER",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS pagespeed_lcp_mobile FLOAT",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS pagespeed_cls_mobile FLOAT",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS pagespeed_inp_mobile FLOAT",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS pagespeed_fcp_mobile FLOAT",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS pagespeed_checked_at TIMESTAMP",
        # ── usercards: unified table merging leads + customer management ──────
        """CREATE TABLE IF NOT EXISTS usercards (
            id                        INTEGER PRIMARY KEY,
            company_name              VARCHAR(255) DEFAULT '',
            contact_name              VARCHAR(255),
            phone                     VARCHAR(20),
            email                     VARCHAR(255),
            website_url               VARCHAR(500) DEFAULT '',
            city                      VARCHAR(100),
            trade                     VARCHAR(100),
            lead_source               VARCHAR(100) DEFAULT '',
            status                    VARCHAR(50)  DEFAULT 'new',
            analysis_score            INTEGER      DEFAULT 0,
            geo_score                 INTEGER      DEFAULT 0,
            notes                     TEXT,
            website_screenshot        TEXT,
            street                    VARCHAR(255) DEFAULT '',
            house_number              VARCHAR(20)  DEFAULT '',
            postal_code               VARCHAR(10)  DEFAULT '',
            legal_form                VARCHAR(50)  DEFAULT '',
            vat_id                    VARCHAR(30)  DEFAULT '',
            register_number           VARCHAR(50)  DEFAULT '',
            register_court            VARCHAR(100) DEFAULT '',
            ceo_first_name            VARCHAR(100) DEFAULT '',
            ceo_last_name             VARCHAR(100) DEFAULT '',
            display_name              VARCHAR(255) DEFAULT '',
            customer_token            VARCHAR UNIQUE,
            customer_token_created_at TIMESTAMP,
            pagespeed_mobile_score    INTEGER,
            pagespeed_desktop_score   INTEGER,
            pagespeed_lcp_mobile      FLOAT,
            pagespeed_cls_mobile      FLOAT,
            pagespeed_inp_mobile      FLOAT,
            pagespeed_fcp_mobile      FLOAT,
            pagespeed_checked_at      TIMESTAMP,
            next_touchpoint_date      TIMESTAMP,
            next_touchpoint_type      VARCHAR(100),
            upsell_status             VARCHAR(50)  DEFAULT 'none',
            upsell_package            VARCHAR(255),
            recurring_revenue         FLOAT        DEFAULT 0.0,
            legacy_type               VARCHAR(20)  DEFAULT 'lead',
            created_at                TIMESTAMP    DEFAULT NOW(),
            updated_at                TIMESTAMP    DEFAULT NOW()
        )""",
        # Copy all leads into usercards (idempotent — skip rows that already exist)
        """INSERT INTO usercards (
            id, company_name, contact_name, phone, email, website_url, city, trade,
            lead_source, status, analysis_score, geo_score, notes, website_screenshot,
            street, house_number, postal_code, legal_form, vat_id, register_number,
            register_court, ceo_first_name, ceo_last_name, display_name,
            customer_token, customer_token_created_at,
            pagespeed_mobile_score, pagespeed_desktop_score,
            pagespeed_lcp_mobile, pagespeed_cls_mobile,
            pagespeed_inp_mobile, pagespeed_fcp_mobile, pagespeed_checked_at,
            legacy_type, created_at, updated_at
        )
        SELECT
            id, company_name, contact_name, phone, email, website_url, city, trade,
            lead_source, status, analysis_score, geo_score, notes, website_screenshot,
            street, house_number, postal_code, legal_form, vat_id, register_number,
            register_court, ceo_first_name, ceo_last_name, display_name,
            customer_token, customer_token_created_at,
            pagespeed_mobile_score, pagespeed_desktop_score,
            pagespeed_lcp_mobile, pagespeed_cls_mobile,
            pagespeed_inp_mobile, pagespeed_fcp_mobile, pagespeed_checked_at,
            'lead', created_at, updated_at
        FROM leads
        WHERE NOT EXISTS (SELECT 1 FROM usercards WHERE usercards.id = leads.id)""",
        # Sync the SERIAL sequence so new inserts after the bulk copy get correct IDs
        "SELECT setval(pg_get_serial_sequence('usercards', 'id'), COALESCE((SELECT MAX(id) FROM usercards), 1))",
        # Project files
        """CREATE TABLE IF NOT EXISTS project_files (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER,
            uploaded_by_role TEXT DEFAULT 'admin',
            filename TEXT NOT NULL,
            original_filename TEXT DEFAULT '',
            file_type TEXT DEFAULT 'sonstiges',
            file_size INTEGER DEFAULT 0,
            file_path TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT NOW(),
            note TEXT DEFAULT ''
        )""",
        # Redesign fields on projects
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS company_name VARCHAR(255)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS website_url VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS cms_type VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS contact_name VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS contact_phone VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS contact_email VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS go_live_date DATE",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS package_type VARCHAR DEFAULT 'kompagnon'",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS payment_status VARCHAR DEFAULT 'offen'",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS desired_pages TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS has_logo BOOLEAN DEFAULT false",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS has_briefing BOOLEAN DEFAULT false",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS has_photos BOOLEAN DEFAULT false",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS pagespeed_mobile INTEGER",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS pagespeed_desktop INTEGER",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS audit_score INTEGER",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS audit_level VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS top_problems TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS industry VARCHAR",
        # ── ORM-Felder die in älteren DBs fehlen können (f405-Fix) ──────────
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS customer_approved_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS review_received BOOLEAN DEFAULT false",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS review_platform VARCHAR(50)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS review_rating FLOAT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS review_text TEXT",
        # ── Seed: Projekte aus Leads anlegen (idempotent) ────────────────────
        # Pass 1: won-Leads die noch kein Projekt haben
        """INSERT INTO projects (lead_id, status, start_date, created_at, updated_at,
                                 company_name, website_url, contact_name, contact_email)
           SELECT l.id, 'phase_1', NOW(), NOW(), NOW(),
                  l.company_name, l.website_url, l.contact_name, l.email
           FROM leads l
           WHERE l.status = 'won'
             AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.lead_id = l.id)""",
        # Pass 2: Fallback — wenn Tabelle nach Pass 1 noch leer, neueste 50 Leads nehmen
        """INSERT INTO projects (lead_id, status, start_date, created_at, updated_at,
                                 company_name, website_url, contact_name, contact_email)
           SELECT l.id, 'phase_1', NOW(), NOW(), NOW(),
                  l.company_name, l.website_url, l.contact_name, l.email
           FROM (SELECT * FROM leads ORDER BY created_at DESC LIMIT 50) l
           WHERE (SELECT COUNT(*) FROM projects) = 0
             AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.lead_id = l.id)""",
        # Sicherheit: lead_id NOT NULL Constraint entfernen falls Direkt-Einträge existieren
        "ALTER TABLE projects ALTER COLUMN lead_id DROP NOT NULL",
        # GEO / KI-Sichtbarkeit Felder auf audit_results
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS llms_txt BOOLEAN DEFAULT false",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS robots_ai_friendly BOOLEAN DEFAULT false",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS structured_data BOOLEAN DEFAULT false",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ai_mentions INTEGER DEFAULT 0",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS email_notifications_enabled BOOLEAN DEFAULT true",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS customer_email VARCHAR",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS favicon_url VARCHAR(500) DEFAULT ''",
        "ALTER TABLE usercards ADD COLUMN IF NOT EXISTS favicon_url VARCHAR(500) DEFAULT ''",
        # Flat briefing fields on existing briefings table
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS project_id INTEGER",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS gewerk VARCHAR(100)",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS leistungen TEXT",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS einzugsgebiet VARCHAR(100)",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS usp TEXT",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS mitbewerber TEXT",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS vorbilder TEXT",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS farben VARCHAR(100)",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS wunschseiten TEXT",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS stil VARCHAR(50)",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS logo_vorhanden BOOLEAN DEFAULT false",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS fotos_vorhanden BOOLEAN DEFAULT false",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS sonstige_hinweise TEXT",
        # sitemap_pages table
        """
        CREATE TABLE IF NOT EXISTS sitemap_pages (
          id SERIAL PRIMARY KEY,
          lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
          parent_id INTEGER REFERENCES sitemap_pages(id) ON DELETE SET NULL,
          position INTEGER DEFAULT 0,
          page_name VARCHAR(100) NOT NULL,
          page_type VARCHAR(50) DEFAULT 'info',
          zweck TEXT,
          ziel_keyword VARCHAR(150),
          cta_text VARCHAR(100),
          cta_ziel VARCHAR(50) DEFAULT 'kontakt',
          notizen TEXT,
          status VARCHAR(30) DEFAULT 'geplant',
          mockup_html TEXT,
          ist_pflichtseite BOOLEAN DEFAULT false,
          created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ist_pflichtseite BOOLEAN DEFAULT false",
        # GrapesJS editor data per sitemap page
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS gjs_html TEXT DEFAULT ''",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS gjs_css TEXT DEFAULT ''",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS gjs_data TEXT DEFAULT '{}'",
        # content_sections + content_media
        """CREATE TABLE IF NOT EXISTS content_sections (
          id SERIAL PRIMARY KEY,
          sitemap_page_id INTEGER REFERENCES sitemap_pages(id) ON DELETE CASCADE,
          lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
          slot_typ VARCHAR(80) NOT NULL,
          slot_label VARCHAR(150) NOT NULL,
          hinweis TEXT,
          inhalt_ki TEXT,
          inhalt_kunde TEXT,
          inhalt_final TEXT,
          status VARCHAR(30) DEFAULT 'ausstehend',
          zeichenlimit INTEGER,
          erstellt_am TIMESTAMP DEFAULT NOW(),
          aktualisiert_am TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS content_media (
          id SERIAL PRIMARY KEY,
          sitemap_page_id INTEGER REFERENCES sitemap_pages(id) ON DELETE CASCADE,
          lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
          slot_typ VARCHAR(80) NOT NULL,
          slot_label VARCHAR(150) NOT NULL,
          hinweis TEXT,
          dateiname VARCHAR(255),
          dateityp VARCHAR(50),
          datei_base64 TEXT,
          dateigroesse_kb INTEGER,
          status VARCHAR(30) DEFAULT 'ausstehend',
          erstellt_am TIMESTAMP DEFAULT NOW()
        )""",
        # Brand design columns on leads
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_primary_color VARCHAR(20)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_secondary_color VARCHAR(20)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_font_primary VARCHAR(100)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_font_secondary VARCHAR(100)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_logo_url VARCHAR(500)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_colors TEXT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_fonts TEXT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_scrape_failed BOOLEAN DEFAULT FALSE",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_pdf_path VARCHAR(500)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_scraped_at TIMESTAMP",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_pdf_data BYTEA",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_pdf_filename VARCHAR(255)",
        # Mockup version history (simple form first — idempotent)
        "CREATE TABLE IF NOT EXISTS mockup_versions (id SERIAL PRIMARY KEY, lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE, sitemap_page_id INTEGER, page_name VARCHAR(100) DEFAULT 'Startseite', version_name VARCHAR(150), html_content TEXT, created_at TIMESTAMP DEFAULT NOW(), created_by VARCHAR(100))",
        "ALTER TABLE mockup_versions ADD COLUMN IF NOT EXISTS sitemap_page_id INTEGER",
        # Full mockup_versions with FK constraints
        """CREATE TABLE IF NOT EXISTS mockup_versions (
          id              SERIAL PRIMARY KEY,
          lead_id         INTEGER REFERENCES leads(id) ON DELETE CASCADE,
          sitemap_page_id INTEGER REFERENCES sitemap_pages(id) ON DELETE CASCADE,
          page_name       VARCHAR(150) DEFAULT '',
          version_name    VARCHAR(150) DEFAULT '',
          html_content    TEXT DEFAULT '',
          created_at      TIMESTAMP DEFAULT NOW(),
          created_by      VARCHAR(100) DEFAULT ''
        )""",
        "ALTER TABLE mockup_versions ADD COLUMN IF NOT EXISTS sitemap_page_id INTEGER REFERENCES sitemap_pages(id) ON DELETE CASCADE",
        "CREATE INDEX IF NOT EXISTS idx_mockup_versions_lead_id ON mockup_versions(lead_id)",
        "CREATE INDEX IF NOT EXISTS idx_mockup_versions_page_id ON mockup_versions(sitemap_page_id)",
    ]
    academy_tables = [
        'academy_courses', 'academy_modules', 'academy_lessons',
        'academy_progress', 'academy_lesson_progress',
        'academy_certificates', 'academy_quiz_questions',
        'academy_customer_access', 'academy_checklist_items',
    ]
    try:
        with engine.connect() as conn:
            for sql in migrations:
                try:
                    conn.execute(text(sql))
                except Exception:
                    pass  # Spalte/Tabelle existiert bereits
            conn.commit()
            # Verify academy tables exist and log
            for tbl in academy_tables:
                try:
                    conn.execute(text(f"SELECT 1 FROM {tbl} LIMIT 1"))
                    print(f"✓ {tbl} OK")
                except Exception as e:
                    print(f"✗ {tbl} FEHLER: {e}")
        logger.info("✓ Migrationen abgeschlossen")
    except Exception as e:
        logger.warning(f"Migration Warnung: {e}")


def _create_default_admin():
    """Create demo users for all 4 roles if they don't exist."""
    from database import SessionLocal, User
    from auth import hash_password
    db = SessionLocal()
    try:
        demo_users = [
            {"email": os.getenv("ADMIN_EMAIL", "admin@kompagnon.de"), "password": os.getenv("ADMIN_PASSWORD", "Admin2025!"), "first_name": "Admin", "last_name": "KOMPAGNON", "role": "admin"},
            {"email": "auditor@kompagnon.de", "password": "Auditor2025!", "first_name": "Max", "last_name": "Auditor", "role": "auditor", "position": "Senior Auditor"},
            {"email": "nutzer@kompagnon.de", "password": "Nutzer2025!", "first_name": "Lisa", "last_name": "Nutzer", "role": "nutzer"},
            {"email": "kunde@kompagnon.de", "password": "Kunde2025!", "first_name": "Thomas", "last_name": "Mustermann", "role": "kunde"},
        ]
        created = 0
        for ud in demo_users:
            if not db.query(User).filter(User.email == ud["email"]).first():
                pw = ud.pop("password")
                pos = ud.pop("position", "")
                user = User(**ud, password_hash=hash_password(pw), position=pos, is_active=True, is_verified=True)
                db.add(user)
                created += 1
                logger.info(f"✓ Demo-User angelegt: {ud['email']} ({ud['role']})")
        if created:
            db.commit()
        else:
            logger.info("Alle Demo-User bereits vorhanden")
    except Exception as e:
        db.rollback()
        logger.error(f"Demo-User Fehler: {e}")
    finally:
        db.close()

    # Link kunde user to eisistcool lead
    try:
        from database import SessionLocal, User, Lead
        _db = SessionLocal()
        kunde = _db.query(User).filter(User.email.ilike('%longhin%')).first()
        if not kunde:
            kunde = _db.query(User).filter(User.role == 'kunde').first()
        if kunde and not kunde.lead_id:
            lead = _db.query(Lead).filter(Lead.website_url.ilike('%eisistcool%')).first()
            if not lead:
                from datetime import datetime
                lead = Lead(company_name='Eisistcool', website_url='https://eisistcool.de',
                           status='customer', created_at=datetime.utcnow(), updated_at=datetime.utcnow())
                _db.add(lead)
                _db.commit()
                _db.refresh(lead)
            kunde.lead_id = lead.id
            _db.commit()
            logger.info(f"Linked kunde {kunde.email} to lead {lead.id}")
        _db.close()
    except Exception as e:
        logger.warning(f"Kunde-Link Fehler: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("🚀 KOMPAGNON Backend Starting...")
    try:
        # Playwright installed at build time via render-build.sh

        os.makedirs("uploads", exist_ok=True)
        logger.info("✓ uploads/ Ordner bereit")

        _run_migrations()
        init_db()
        logger.info("✓ Database initialized")

        # Create default admin if no users exist
        try:
            _create_default_admin()
        except Exception as e:
            logger.warning(f"⚠ Default admin: {e}")

        # Seed academy courses if empty
        try:
            from routers.academy import seed_academy_courses
            from database import SessionLocal
            _seed_db = SessionLocal()
            seed_academy_courses(_seed_db)
            _seed_db.close()
        except Exception as e:
            logger.warning(f"⚠ Academy seed: {e}")

        # Seed courses if empty
        try:
            from routers.courses import seed_courses
            from database import SessionLocal
            _seed_db = SessionLocal()
            seed_courses(_seed_db)
            _seed_db.close()
        except Exception as e:
            logger.warning(f"⚠ Courses seed: {e}")

        # Seed projects from won leads (or all leads if table empty)
        try:
            from database import SessionLocal, Project as _Project, Lead as _Lead
            _seed_db = SessionLocal()
            project_count = _seed_db.query(_Project).count()
            won_leads = _seed_db.query(_Lead).filter(_Lead.status == "won").all()
            won_without_project = [l for l in won_leads
                                   if not _seed_db.query(_Project).filter(_Project.lead_id == l.id).first()]
            seeded = 0
            # Seed won leads that have no project
            candidates = won_without_project
            # If table completely empty, also pull all leads as fallback
            if project_count == 0 and not won_without_project:
                all_leads = _seed_db.query(_Lead).order_by(_Lead.id.desc()).limit(50).all()
                candidates = [l for l in all_leads
                              if not _seed_db.query(_Project).filter(_Project.lead_id == l.id).first()]
            for lead in candidates:
                now = __import__('datetime').datetime.utcnow()
                p = _Project(lead_id=lead.id, status="phase_1",
                             start_date=now, created_at=now, updated_at=now)
                for col, val in [("company_name", lead.company_name),
                                  ("website_url",  lead.website_url),
                                  ("contact_name", lead.contact_name),
                                  ("contact_email", lead.email)]:
                    try:
                        setattr(p, col, val)
                    except Exception:
                        pass
                _seed_db.add(p)
                seeded += 1
            if seeded:
                _seed_db.commit()
                logger.info(f"✓ {seeded} Projekte aus Leads angelegt (Seed)")
            else:
                logger.info(f"✓ Projekt-Seed: {project_count} Projekte bereits vorhanden")
            _seed_db.close()
        except Exception as e:
            logger.warning(f"⚠ Projekt-Seed: {e}")

        # Start scheduler (non-critical — don't block app start)
        try:
            start_scheduler()
            logger.info("✓ Scheduler started")
        except Exception as e:
            logger.warning(f"⚠ Scheduler failed to start (non-critical): {e}")

        yield

    except Exception as e:
        logger.error(f"✗ Startup failed: {str(e)}")
        raise

    finally:
        logger.info("🛑 KOMPAGNON Backend Shutting Down...")
        try:
            stop_scheduler()
        except Exception:
            pass
        logger.info("✓ Shutdown complete")


# Create FastAPI app with lifespan
app = FastAPI(
    title="KOMPAGNON Automation System",
    description="Complete WordPress website automation for German handcraft businesses",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=UnicodeJSONResponse,
)

# CORS Middleware — must be before all routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://kompagnon-frontend.onrender.com",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include all routers — specific routers BEFORE alias/fallback routers
app.include_router(usercards_router)
app.include_router(leads_router)                      # real leads router first
app.include_router(leads_alias_router)                # alias after
app.include_router(usercards_customers_alias_router)
app.include_router(customers_router)                  # real customers router first
app.include_router(customers_alias_router)            # alias after
app.include_router(projects_router)
app.include_router(agents_router)
app.include_router(automations_router)
app.include_router(cms_connect_router)
app.include_router(portal_router)
app.include_router(audit_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(scraper_router)
app.include_router(settings_router)
app.include_router(payments_router)
app.include_router(tickets_router)

from routers import briefings
app.include_router(briefings.router)      # GET /api/briefings/{lead_id} + POST + PUT

from routers.briefing import router as briefing_router
app.include_router(briefing_router)       # PATCH + AI endpoints

from routers.kampagne import router as kampagne_router
app.include_router(kampagne_router)

from routers.courses import router as courses_router
app.include_router(courses_router)

from app.routers.academy import router as academy_router
app.include_router(academy_router)

from routers.crawler import router as crawler_router
app.include_router(crawler_router)

from app.routers.files import router as files_router
app.include_router(files_router)

from app.routers import website_mockup
app.include_router(website_mockup.router, prefix="/api")

from routers import sitemap
app.include_router(sitemap.router)
app.include_router(sitemap.pages_router)

from routers import content
app.include_router(content.router)

from routers import mockups
app.include_router(mockups.router)

from routers import content_scraper_router
app.include_router(content_scraper_router.router)

from routers.branddesign import router as branddesign_router
app.include_router(branddesign_router)


# Global exception handler — catches unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(
        f'Unbehandelter Fehler: {type(exc).__name__}: {exc}\n{traceback.format_exc()}'
    )
    return JSONResponse(
        status_code=500,
        content={'detail': 'Interner Serverfehler', 'type': type(exc).__name__},
    )


# Health check endpoint
@app.get("/health")
def health_check():
    """Check if backend and database are running."""
    from database import SessionLocal
    db_status = "unknown"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:80]}"

    try:
        scheduler = get_scheduler()
        return {
            "status": "ok" if db_status == "connected" else "degraded",
            "service": "KOMPAGNON Backend",
            "database": db_status,
            "scheduler_running": scheduler.scheduler.running,
            "timestamp": os.popen("date").read().strip(),
        }
    except Exception as e:
        return {"status": "degraded", "database": db_status, "detail": str(e)}


@app.get("/")
def root():
    """API root with documentation link."""
    return {
        "message": "🚀 KOMPAGNON Automation System",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
        "features": [
            "Lead Management Pipeline",
            "7-Phase Project Workflow",
            "KI-powered Content Generation",
            "Real-time Margin Tracking",
            "Automated Post-Launch Sequences",
            "Local SEO Schema Generation",
            "QA Automation & Testing",
            "Customer Relationship Management",
        ],
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__,
        },
    )


# Info endpoint for deployment
@app.get("/info")
def get_info():
    """Get system information."""
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": os.getenv("DATABASE_URL", "sqlite:///./kompagnon.db"),
        "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "smtp_configured": bool(os.getenv("SMTP_HOST")),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
