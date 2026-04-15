"""
KOMPAGNON — Zentrale Datenbank-Migrationen

Einzige Quelle der Wahrheit fuer alle Schema-Aenderungen nach Einfuehrung
des Version-Tracking-Systems (Tech-Debt Fix 01).

Jede Migration hat:
- Eine eindeutige Version (aufsteigend)
- Einen beschreibenden Namen
- SQL das idempotent ausfuehrbar ist (IF NOT EXISTS / IF EXISTS)

Neue Migrationen immer am Ende anhaengen — nie bestehende aendern.
Die `schema_migrations`-Tabelle haelt den angewandten Stand fest.
"""
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


# ── Versions-Tabelle ───────────────────────────────────────────────────────
CREATE_VERSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    applied_at  TIMESTAMP DEFAULT NOW()
);
"""


# ── Legacy-Baseline ────────────────────────────────────────────────────────
# Enthaelt saemtliche Schema-Operationen die bis Tech-Debt Fix 01 direkt
# in main.py._run_migrations() standen. Jede Operation ist idempotent
# (IF NOT EXISTS / IF EXISTS / INSERT ... ON CONFLICT), daher sicher
# anwendbar auf eine DB in beliebigem Zustand.
#
# WICHTIG: Diese Liste NIE aendern. Neue Schema-Changes kommen als
# eigenstaendige Version 2+ unten an die MIGRATIONS-Liste.
_LEGACY_BASELINE = [
        # Ensure the users.role column can hold 'superadmin' (and drop any
        # legacy CHECK constraint that might reject it)
        "ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check",
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
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS customer_token_expires TIMESTAMP",
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
            browser_info VARCHAR DEFAULT '', page_name VARCHAR DEFAULT '', screenshot_base64 TEXT DEFAULT '', admin_notes TEXT DEFAULT '',
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
        # Campaign Manager
        """CREATE TABLE IF NOT EXISTS campaigns (
            id            SERIAL PRIMARY KEY,
            name          VARCHAR(500) NOT NULL,
            slug          VARCHAR(200) UNIQUE NOT NULL,
            source        VARCHAR(100) NOT NULL,
            medium        VARCHAR(100),
            channel       VARCHAR(100),
            description   TEXT,
            target_url    VARCHAR(1000) DEFAULT 'https://kompagnon.eu',
            is_active     BOOLEAN DEFAULT TRUE,
            created_by    INTEGER,
            created_at    TIMESTAMP DEFAULT NOW(),
            archived_at   TIMESTAMP
        )""",
        "CREATE INDEX IF NOT EXISTS idx_campaigns_slug ON campaigns(slug)",
        "CREATE INDEX IF NOT EXISTS idx_campaigns_source ON campaigns(source)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS kampagne_id INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_source VARCHAR(200)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_medium VARCHAR(200)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_campaign VARCHAR(200)",
        # Trackdesk / Affiliate Partner Tracking
        """CREATE TABLE IF NOT EXISTS affiliate_conversions (
            id                SERIAL PRIMARY KEY,
            trackdesk_id      VARCHAR(200) UNIQUE,
            event_type        VARCHAR(100),
            affiliate_id      VARCHAR(200),
            affiliate_email   VARCHAR(500),
            affiliate_name    VARCHAR(500),
            customer_email    VARCHAR(500),
            customer_name     VARCHAR(500),
            conversion_value  NUMERIC(12,2),
            commission_value  NUMERIC(12,2),
            currency          VARCHAR(10) DEFAULT 'EUR',
            status            VARCHAR(100),
            lead_id           INTEGER REFERENCES leads(id) ON DELETE SET NULL,
            raw_payload       TEXT,
            received_at       TIMESTAMP DEFAULT NOW()
        )""",
        "CREATE INDEX IF NOT EXISTS idx_affiliate_conversions_lead ON affiliate_conversions(lead_id)",
        "CREATE INDEX IF NOT EXISTS idx_affiliate_conversions_affiliate ON affiliate_conversions(affiliate_id)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS affiliate_id VARCHAR(200)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS affiliate_name VARCHAR(500)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS affiliate_conversion_id INTEGER",
        # ── Seiten-Manager (öffentliche Seiten + Templates) ──
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
            product_id      INTEGER,
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
        "CREATE INDEX IF NOT EXISTS idx_public_pages_slug ON public_pages(slug)",
        "CREATE INDEX IF NOT EXISTS idx_public_pages_type ON public_pages(page_type)",
        # Seed: bekannte öffentliche Seiten vorbelegen
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
        # NOTE: usercards bulk-copy removed — caused DB lock on startup.
        # Run manually via /admin endpoint or separate script if needed.
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
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS hosting_provider VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS hosting_org VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS hosting_ip VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS hosting_country VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS dns_provider VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS nameservers TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS domain_registrar VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS domain_created VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS domain_expires VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS server_software VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS wordpress_hosting VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_wordpress BOOLEAN",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS hosting_checked_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS detected_technologies TEXT",
        "ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS page_name VARCHAR DEFAULT ''",
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
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS actual_hours FLOAT DEFAULT 0.0",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS hourly_rate FLOAT DEFAULT 45.0",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS ai_tool_costs FLOAT DEFAULT 50.0",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS margin_percent FLOAT DEFAULT 0.0",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS scope_creep_flags INTEGER DEFAULT 0",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS target_go_live TIMESTAMP",
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
        # Widen VARCHAR columns to TEXT for KI-generated content
        "ALTER TABLE briefings ALTER COLUMN gewerk TYPE TEXT",
        "ALTER TABLE briefings ALTER COLUMN farben TYPE TEXT",
        "ALTER TABLE briefings ALTER COLUMN stil TYPE TEXT",
        "ALTER TABLE briefings ALTER COLUMN einzugsgebiet TYPE TEXT",
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
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS slug TEXT",
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
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_design_style VARCHAR(100)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_notes TEXT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_design_json TEXT",
        # Design version history (simple form first — idempotent)
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
        # Website Templates
        """CREATE TABLE IF NOT EXISTS website_templates (
          id             SERIAL PRIMARY KEY,
          name           VARCHAR(200) NOT NULL,
          description    TEXT,
          source         VARCHAR(50) DEFAULT 'upload',
          source_url     VARCHAR(500),
          thumbnail_url  VARCHAR(500),
          html_content   TEXT,
          css_content    TEXT,
          grapes_data    JSONB,
          tags           VARCHAR(200),
          category       VARCHAR(100) DEFAULT 'allgemein',
          is_active      BOOLEAN DEFAULT true,
          created_at     TIMESTAMP DEFAULT NOW(),
          updated_at     TIMESTAMP DEFAULT NOW()
        )""",
        # Template library extension columns
        "ALTER TABLE website_templates ADD COLUMN IF NOT EXISTS slug VARCHAR(200)",
        "ALTER TABLE website_templates ADD COLUMN IF NOT EXISTS style_tags TEXT",
        "ALTER TABLE website_templates ADD COLUMN IF NOT EXISTS gewerk_tags TEXT",
        "ALTER TABLE website_templates ADD COLUMN IF NOT EXISTS source_file VARCHAR(500)",
        "ALTER TABLE website_templates ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_website_templates_slug ON website_templates(slug)",
        # Inspiration URLs for briefing + portal
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS inspiration_url_1 TEXT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS inspiration_url_2 TEXT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS inspiration_url_3 TEXT",
        # Google Analytics detection
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ga_status VARCHAR(30) DEFAULT 'unbekannt'",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ga_measurement_id VARCHAR(50)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ga_type VARCHAR(20)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ga_checked_at TIMESTAMP",
        # Website version generation (KI picks 3 templates)
        """CREATE TABLE IF NOT EXISTS website_versions (
            id             SERIAL PRIMARY KEY,
            project_id     INTEGER REFERENCES projects(id) ON DELETE CASCADE,
            version_label  VARCHAR(10) DEFAULT 'A',
            template_id    INTEGER REFERENCES website_templates(id) ON DELETE SET NULL,
            html           TEXT,
            css            TEXT,
            gjs_data       TEXT,
            ki_reasoning   TEXT,
            selected       BOOLEAN DEFAULT FALSE,
            created_at     TIMESTAMP DEFAULT NOW()
        )""",
        "CREATE INDEX IF NOT EXISTS idx_website_versions_project ON website_versions(project_id)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS template_id INTEGER REFERENCES website_templates(id) ON DELETE SET NULL",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS template_id INTEGER REFERENCES website_templates(id) ON DELETE SET NULL",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS screenshot_before TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS screenshot_before_date TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS moodboard_data TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS moodboard_updated_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS screenshot_after TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS screenshot_after_date TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS screenshot_url_before VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS screenshot_url_after VARCHAR",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS unread_messages INTEGER DEFAULT 0",
        "ALTER TABLE leads    ADD COLUMN IF NOT EXISTS domain_reachable BOOLEAN DEFAULT NULL",
        "ALTER TABLE leads    ADD COLUMN IF NOT EXISTS domain_status_code INTEGER",
        "ALTER TABLE leads    ADD COLUMN IF NOT EXISTS domain_checked_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS domain_reachable BOOLEAN DEFAULT NULL",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS domain_status_code INTEGER",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS domain_checked_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS customer_name VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS current_phase INTEGER DEFAULT 1",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS fixed_price FLOAT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS mockup_html TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS mockup_css TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS brand_assets TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS hosting_provider VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS domain_registrar VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS nameserver1 VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS nameserver2 VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS ftp_credentials TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS wp_admin_url VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS hosting_notes TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS scraped_content TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMP",
        # Website-Content-Cache für Crawler-Scraping
        """CREATE TABLE IF NOT EXISTS website_content_cache (
          id               SERIAL PRIMARY KEY,
          customer_id      INTEGER,
          url              VARCHAR,
          title            VARCHAR,
          meta_description TEXT,
          h1               VARCHAR,
          h2s              TEXT,
          text_preview     TEXT,
          full_text        TEXT,
          word_count       INTEGER DEFAULT 0,
          images           TEXT DEFAULT '[]',
          files            TEXT DEFAULT '[]',
          scraped_at       TIMESTAMP DEFAULT NOW()
        )""",
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS full_text TEXT",
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS images TEXT DEFAULT '[]'",
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS files TEXT DEFAULT '[]'",
        """CREATE INDEX IF NOT EXISTS idx_website_content_cache_customer
           ON website_content_cache(customer_id)""",
        # Netlify-Integration — NETLIFY_API_TOKEN env-Variable erforderlich.
        # `projects.netlify_token` ist seit Bug #1 Fix DEPRECATED und wird
        # vom Backend nicht mehr gelesen oder geschrieben. Die Spalte bleibt
        # nur aus Rollback-Gruenden bestehen (bestehende DB-Zeilen werden
        # beim Deploy nicht geaendert). Alle Deploys nutzen jetzt den
        # zentralen Token aus `NETLIFY_API_TOKEN`.
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_token TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_site_id VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_site_url VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_deploy_id VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_domain VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_domain_status VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_ssl_active BOOLEAN DEFAULT false",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_last_deploy TIMESTAMP",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS wz_code VARCHAR",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS wz_title VARCHAR",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS wz_code VARCHAR",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS wz_title VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS wz_code VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS wz_title VARCHAR",
        # email_logs Tabelle
        """CREATE TABLE IF NOT EXISTS email_logs (
          id SERIAL PRIMARY KEY,
          lead_id INTEGER,
          project_id INTEGER,
          recipient VARCHAR,
          subject VARCHAR,
          body TEXT,
          sent_at TIMESTAMP DEFAULT NOW(),
          status VARCHAR DEFAULT 'sent'
        )""",
        "CREATE INDEX IF NOT EXISTS idx_email_logs_lead ON email_logs(lead_id)",
        "CREATE INDEX IF NOT EXISTS idx_email_logs_project ON email_logs(project_id)",
        # email_logs erweiterte Spalten
        "ALTER TABLE email_logs ADD COLUMN IF NOT EXISTS to_email VARCHAR",
        "ALTER TABLE email_logs ADD COLUMN IF NOT EXISTS template_key VARCHAR",
        "ALTER TABLE email_logs ADD COLUMN IF NOT EXISTS error_message TEXT",
        # Lead-Sequenzen
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS sequence_active BOOLEAN DEFAULT false",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS sequence_step INTEGER DEFAULT 0",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS sequence_last_sent TIMESTAMP",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS sequence_paused BOOLEAN DEFAULT false",
        # Onboarding + Go-Live Automation
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT false",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS actual_go_live TIMESTAMP",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS website_url VARCHAR",
        # ── Newsletter tables ──────────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS newsletters (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            preview_text VARCHAR(255),
            html_content TEXT,
            json_content JSONB,
            status VARCHAR(50) DEFAULT 'draft',
            brevo_campaign_id BIGINT,
            scheduled_at TIMESTAMP WITH TIME ZONE,
            sent_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS newsletter_lists (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            brevo_list_id BIGINT,
            description TEXT,
            source VARCHAR(50) DEFAULT 'manual',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS newsletter_contacts (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            list_id INTEGER REFERENCES newsletter_lists(id),
            crm_user_id INTEGER,
            status VARCHAR(50) DEFAULT 'subscribed',
            brevo_contact_id BIGINT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )""",
        # ── Crawl tables ───────────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS crawl_jobs (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER,
            status VARCHAR(20) DEFAULT 'pending',
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            total_urls INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS crawl_results (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER,
            job_id INTEGER REFERENCES crawl_jobs(id) ON DELETE CASCADE,
            url VARCHAR(2000) NOT NULL,
            status_code INTEGER,
            depth INTEGER DEFAULT 0,
            load_time NUMERIC(8,3),
            crawled_at TIMESTAMP DEFAULT NOW()
        )""",
        "CREATE INDEX IF NOT EXISTS idx_crawl_jobs_customer ON crawl_jobs(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_crawl_results_job ON crawl_results(job_id)",
        "CREATE INDEX IF NOT EXISTS idx_crawl_results_customer_id ON crawl_results(customer_id)",
        # ── Performance-Indizes fuer haeufige Sortierungen ──────────
        "CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_projects_id ON projects(id DESC)",
        "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
        "CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)",
        "CREATE INDEX IF NOT EXISTS idx_audit_results_lead_id ON audit_results(lead_id, created_at DESC)",
        # ── Webhook log ────────────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS webhook_log (
            id SERIAL PRIMARY KEY,
            source VARCHAR(50),
            email VARCHAR(255),
            company VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        # ── Digitale Abnahme + PageSpeed After ─────────────────────
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS abnahme_datum TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS abnahme_durch VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS pagespeed_after_mobile INTEGER",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS pagespeed_after_desktop INTEGER",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS screenshot_after_url VARCHAR",
        # ── Retainer + Invoices ────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS retainer_contracts (
            id SERIAL PRIMARY KEY,
            project_id INTEGER,
            lead_id INTEGER,
            package_name VARCHAR DEFAULT 'SEO-Pflege',
            price_net NUMERIC(10,2) DEFAULT 89.00,
            billing_cycle VARCHAR DEFAULT 'monthly',
            start_date DATE,
            next_billing_date DATE,
            status VARCHAR DEFAULT 'aktiv',
            customer_email VARCHAR,
            customer_name VARCHAR,
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS invoices (
            id SERIAL PRIMARY KEY,
            retainer_id INTEGER,
            project_id INTEGER,
            invoice_number VARCHAR UNIQUE,
            amount_net NUMERIC(10,2),
            tax_rate NUMERIC(5,2) DEFAULT 19.00,
            amount_gross NUMERIC(10,2),
            status VARCHAR DEFAULT 'offen',
            due_date DATE,
            paid_at TIMESTAMP,
            customer_email VARCHAR,
            customer_name VARCHAR,
            line_item VARCHAR DEFAULT 'Website-Pflege & SEO-Paket',
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        # Go-Live Automation — additional project columns
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS customer_email VARCHAR",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS golive_audit_id INTEGER",
        # QA-Scanner Ergebnisse
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS qa_result JSONB",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS qa_score INTEGER",
        # Scrape Cache
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS scrape_full_data TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS scrape_full_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS qa_golive_ok BOOLEAN",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS qa_run_at TIMESTAMP",
        # Auftragsbestätigung PDF
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS auftragsbestaetigung_pdf VARCHAR",
        # Sitemap-Planer
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS sitemap_json TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS sitemap_freigabe TIMESTAMP",
        # Content-Freigaben
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS content_freigaben TEXT",
        # QA-Checkliste
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS qa_checklist_json TEXT",
        # Abnahme & Go-Live Nachher-Daten
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS gbp_checklist_json TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS abnahme_durch VARCHAR(200)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS screenshot_after TEXT",
        # Zugangsdaten-Safe
        """CREATE TABLE IF NOT EXISTS project_credentials (
            id                  SERIAL PRIMARY KEY,
            project_id          INTEGER NOT NULL,
            label               VARCHAR(100) NOT NULL,
            username            VARCHAR(255),
            password_encrypted  TEXT,
            url                 VARCHAR(500),
            notes               TEXT,
            created_at          TIMESTAMP DEFAULT NOW()
        )""",
        "ALTER TABLE project_credentials ADD COLUMN IF NOT EXISTS typ VARCHAR(50) DEFAULT 'sonstiges'",
        "CREATE INDEX IF NOT EXISTS idx_project_credentials_pid ON project_credentials(project_id)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS gbp_place_id VARCHAR",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS gbp_claimed BOOLEAN DEFAULT false",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS gbp_rating FLOAT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS gbp_ratings_total INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS gbp_checked_at TIMESTAMP",
        # ── Products ──────────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            slug VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            short_desc TEXT,
            long_desc TEXT,
            price_brutto NUMERIC(10,2) NOT NULL DEFAULT 0,
            price_netto NUMERIC(10,2) NOT NULL DEFAULT 0,
            tax_rate NUMERIC(5,2) NOT NULL DEFAULT 19.0,
            payment_type VARCHAR(50) NOT NULL DEFAULT 'once',
            delivery_days INTEGER DEFAULT 14,
            highlighted BOOLEAN DEFAULT false,
            highlight_label VARCHAR(100) DEFAULT 'Empfehlung',
            features JSONB DEFAULT '[]',
            checkout_fields JSONB DEFAULT '[]',
            webhook_actions JSONB DEFAULT '[]',
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            stripe_price_id VARCHAR(200),
            stripe_product_id VARCHAR(200),
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        # Products schema upgrade (for existing deployments)
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS short_desc TEXT",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS long_desc TEXT",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS price_brutto NUMERIC(10,2) DEFAULT 0",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS price_netto NUMERIC(10,2) DEFAULT 0",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS tax_rate NUMERIC(5,2) DEFAULT 19.0",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS payment_type VARCHAR(50) DEFAULT 'once'",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS delivery_days INTEGER DEFAULT 14",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS highlighted BOOLEAN DEFAULT false",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS highlight_label VARCHAR(100) DEFAULT 'Empfehlung'",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS features JSONB DEFAULT '[]'",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS checkout_fields JSONB DEFAULT '[]'",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS webhook_actions JSONB DEFAULT '[]'",
        # ── Deals (CRM-Pipeline) ──────────────────────────────────
        """CREATE TABLE IF NOT EXISTS deals (
            id            SERIAL PRIMARY KEY,
            title         VARCHAR(500) NOT NULL,
            company_id    INTEGER REFERENCES leads(id) ON DELETE SET NULL,
            status        VARCHAR(50) DEFAULT 'neu',
            total_value   NUMERIC(12,2) DEFAULT 0,
            currency      VARCHAR(3) DEFAULT 'EUR',
            notes         TEXT,
            assigned_to   INTEGER,
            won_at        TIMESTAMP,
            lost_at       TIMESTAMP,
            created_at    TIMESTAMP DEFAULT NOW(),
            updated_at    TIMESTAMP DEFAULT NOW()
        )""",
        "CREATE INDEX IF NOT EXISTS idx_deals_company ON deals(company_id)",
        "CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status)",
        """CREATE TABLE IF NOT EXISTS deal_items (
            id          SERIAL PRIMARY KEY,
            deal_id     INTEGER REFERENCES deals(id) ON DELETE CASCADE,
            position    VARCHAR(500) NOT NULL,
            quantity    NUMERIC(10,2) DEFAULT 1,
            unit_price  NUMERIC(12,2) DEFAULT 0,
            total_price NUMERIC(12,2) DEFAULT 0,
            product_id  INTEGER,
            sort_order  INTEGER DEFAULT 0
        )""",
        "CREATE INDEX IF NOT EXISTS idx_deal_items_deal ON deal_items(deal_id)",
        # Revoked-Token Blacklist fuer JWT-Revokation (Security Fix 12)
        """CREATE TABLE IF NOT EXISTS revoked_tokens (
            id          SERIAL PRIMARY KEY,
            jti         VARCHAR(64) UNIQUE NOT NULL,
            revoked_at  TIMESTAMP DEFAULT NOW(),
            expires_at  TIMESTAMP NOT NULL
        )""",
        "CREATE INDEX IF NOT EXISTS idx_revoked_tokens_jti ON revoked_tokens(jti)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS deal_id INTEGER",
]


# ── Migrationen in Reihenfolge ─────────────────────────────────────────────
# Format: (version, name, sql_statements)
#   sql_statements kann eine Liste von Strings sein (bevorzugt, kein
#   Semikolon-Splitting) oder ein einzelner Multi-Statement-String.
#
# NIEMALS bestehende Eintraege aendern — nur am Ende anhaengen.
MIGRATIONS = [
    (1, "legacy_baseline", _LEGACY_BASELINE),

    # ── Neue Migrationen ab hier ──
    (2, "add_profile_indexes", [
        # Audit-Abfragen nach lead_id + status + Datum (fuer /api/leads/{id}/profile):
        "CREATE INDEX IF NOT EXISTS idx_audit_lead_status_date ON audit_results(lead_id, status, created_at DESC)",
        # Projekt-Abfragen nach lead_id + Datum (fuer LATERAL-JOIN auf letztes Projekt):
        "CREATE INDEX IF NOT EXISTS idx_projects_lead_created ON projects(lead_id, created_at DESC)",
        # Lead-Suche nach Status (fuer Listen-Filter):
        "CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)",
        # Lead-Suche nach lead_source (fuer Kampagnen-/Herkunfts-Filter):
        "CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(lead_source)",
    ]),

    (3, "add_margin_summary_indexes", [
        # time_tracking.project_id — fuer LEFT JOIN in get_margin_summary():
        "CREATE INDEX IF NOT EXISTS idx_time_tracking_project ON time_tracking(project_id)",
        # projects.status — fuer WHERE p.status = ANY(...) Filter der aktiven Phasen:
        "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
    ]),

    (4, "add_audit_status_date_index", [
        # audit_results(status, created_at DESC) — fuer /api/audit/recent
        # (WHERE status = 'completed' ORDER BY created_at DESC LIMIT N).
        # Der bestehende v2-Index idx_audit_lead_status_date hat lead_id als
        # fuehrende Spalte und kann daher ohne WHERE lead_id nicht sauber
        # benutzt werden.
        "CREATE INDEX IF NOT EXISTS idx_audit_status_date ON audit_results(status, created_at DESC)",
    ]),

    (5, "add_briefing_ki_prefill_metadata", [
        # KI-Auto-Fill Metadaten (gesetzt von POST /api/briefings/{id}/ki-prefill):
        # ki_prefilled_at markiert wann die KI das Briefing befuellt hat,
        # ki_confidence ist high|medium|low, ki_hinweise ist ein kurzer
        # Hinweistext fuer den Kunden. Das Frontend zeigt auf Basis von
        # ki_prefilled_at einen Info-Banner und auf den befuellten Feldern
        # ein KI-Badge.
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS ki_prefilled_at TIMESTAMP",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS ki_confidence VARCHAR(10)",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS ki_hinweise TEXT",
    ]),

    (6, "add_project_briefing_approval_gate", [
        # Tor 1: Briefing-Freigabe-Gate (Baustein 2 der Funnel-Automation).
        # Der Kunde schickt das Briefing ab (briefing_submitted_at wird
        # gesetzt), Phase-2-Endpoints sind dann gesperrt bis ein Admin das
        # Briefing explizit freigibt (briefing_approved_at + _by). Der
        # APScheduler-Job 'briefing_approval_reminders' kontrolliert alle
        # pending Freigaben stuendlich und eskaliert bei >48h Wartezeit.
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS briefing_submitted_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS briefing_approved_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS briefing_approved_by VARCHAR(200)",
        # Partial-Index fuer den stuendlichen Reminder-Scan: nur Projekte
        # mit submitted aber not approved — das sind typischerweise nur
        # wenige Zeilen, der Index spart full table scans bei wachsender
        # projects-Tabelle.
        "CREATE INDEX IF NOT EXISTS idx_projects_briefing_pending "
        "ON projects(briefing_submitted_at) "
        "WHERE briefing_approved_at IS NULL",
    ]),

    (7, "add_project_content_approval_gate", [
        # Tor 2: Content-Freigabe durch den Kunden (Baustein 3).
        # Nachdem Admin Sitemap + Content-Texte fertig hat, schickt er
        # POST /api/projects/{id}/request-content-approval: das generiert
        # einen sicheren Token (secrets.token_urlsafe(32)) und setzt
        # content_approval_sent_at. Der Kunde klickt entweder den
        # tokenisierten Link aus der Mail (GET /approve-content/{token})
        # oder bestaetigt im Portal (POST /approve-content-portal).
        # Beide Wege setzen content_approved_at + _by.
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS content_approval_sent_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS content_approval_token VARCHAR(64)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS content_approved_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS content_approved_by VARCHAR(200)",
        # Unique-Index auf Token: der tokenisierte Link-Endpoint matcht
        # auf genau eine Zeile. Kollisionen sind bei 32 random bytes
        # praktisch ausgeschlossen; der Unique-Constraint macht es zur
        # harten Garantie und beschleunigt den Lookup gleichzeitig.
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_content_token "
        "ON projects(content_approval_token) "
        "WHERE content_approval_token IS NOT NULL",
        # Partial-Index fuer den 48h-Reminder-Job (analog zu v6):
        "CREATE INDEX IF NOT EXISTS idx_projects_content_pending "
        "ON projects(content_approval_sent_at) "
        "WHERE content_approved_at IS NULL",
    ]),

    (8, "add_sitemap_page_ki_content_columns", [
        # Batch-Content-Generierung fuer die ContentWerkstatt (Optimierung #3).
        # Das neue POST /api/projects/{id}/content-workshop/generate-all
        # schreibt KI-Texte aller Sitemap-Seiten in einem einzigen Claude-Call
        # direkt in diese neuen Spalten. Das GET /api/sitemap/{lead_id}
        # liefert sie zurueck, damit die ContentWerkstatt sie nach dem Reload
        # rehydratisieren kann.
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_h1 TEXT",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_hero_text TEXT",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_abschnitt_text TEXT",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_cta VARCHAR(100)",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_meta_title VARCHAR(70)",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_meta_description VARCHAR(160)",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS content_generated BOOLEAN DEFAULT false",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS content_generated_at TIMESTAMP",
    ]),

    (9, "add_lead_kaltakquise_tracking", [
        # Kaltakquise-Tracking (Hebel #4): Ein Button in LeadProfile.jsx
        # triggert Audit → KI-Anschreiben → PDF → E-Mail → Status-Update.
        # Die zwei Spalten dokumentieren Wann-zuletzt und Wie-oft.
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS kaltakquise_gesendet_at TIMESTAMP",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS kaltakquise_count INTEGER DEFAULT 0",
    ]),

    (10, "add_lead_perf_report_tracking", [
        # Monatlicher Performance-Report (Hebel #5): APScheduler triggert
        # job_monthly_performance_report am 1. jeden Monats um 08:30 Berlin-Zeit.
        # Pro aktiver Lead (mit Go-Live oder Netlify-aktiv) wird PageSpeed
        # frisch gemessen, mit dem letzten Report verglichen und per E-Mail
        # mit KI-Kommentar verschickt.
        #
        # perf_report_last_*  = Score zum Zeitpunkt des letzten Reports
        #                       (nicht "aktueller Score" — der bleibt in
        #                        pagespeed_*_score). Damit ist der Vergleich
        #                       stabil: letzter Report ↔ dieser Report.
        # perf_report_sent_*  = Tracking fuer Logs / Statistiken / Audit-Trail
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS perf_report_last_mobile INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS perf_report_last_desktop INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS perf_report_sent_at TIMESTAMP",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS perf_report_sent_count INTEGER DEFAULT 0",
    ]),

    (11, "add_sitemap_ki_content_for_ground_page", [
        # Ground Page (GEO / KI-Optimierung): strukturierte JSON-Daten
        # (Fakten, FAQ, USP, Schema.org JSON-LD) werden als serialisiertes
        # JSON in ki_content abgelegt. Die granularen v8-Spalten (ki_h1,
        # ki_hero_text, ki_abschnitt_text, ki_cta) reichen dafuer nicht aus.
        # Fuer normale Seiten bleibt ki_content leer — die v8-Spalten
        # werden weiter genutzt.
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_content TEXT",
    ]),
]


# ── Runner ─────────────────────────────────────────────────────────────────

def _to_statements(sql) -> list:
    """Normalisiert das SQL-Feld auf eine Liste von Einzel-Statements."""
    if isinstance(sql, (list, tuple)):
        return [s.strip() for s in sql if s and s.strip()]
    # String → auf Semikolon splitten (alter Task-Spec-Stil)
    return [s.strip() for s in str(sql).split(";") if s.strip()]


def run_migrations(engine) -> dict:
    """
    Fuehrt alle ausstehenden Migrationen aus.

    Gibt Stats zurueck: {"applied": N, "skipped": N, "failed": N}
    """
    stats = {"applied": 0, "skipped": 0, "failed": 0}

    with engine.connect() as conn:
        # 1. Versions-Tabelle sicherstellen
        try:
            conn.execute(text(CREATE_VERSIONS_TABLE))
            conn.commit()
        except Exception as e:
            logger.error(f"schema_migrations Tabelle konnte nicht angelegt werden: {e}")
            stats["failed"] += 1
            return stats

        # 2. Bereits angewandte Versionen laden
        try:
            applied = {
                row[0] for row in conn.execute(text("SELECT version FROM schema_migrations"))
            }
        except Exception as e:
            logger.error(f"schema_migrations konnte nicht gelesen werden: {e}")
            applied = set()

        # 3. Ausstehende Migrationen der Reihe nach anwenden
        for version, name, sql in MIGRATIONS:
            if version in applied:
                stats["skipped"] += 1
                continue

            statements = _to_statements(sql)
            failed_in_this_migration = 0

            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                except Exception as stmt_err:
                    # Idempotente Statements koennen harmlose Fehler werfen
                    # (z.B. wenn die Spalte schon existiert und Postgres
                    # trotzdem meckert). Wir loggen sie, aber brechen NICHT
                    # die ganze Migration ab — die Baseline hat 386
                    # Statements, davon sind manche historisch broken.
                    snippet = stmt.replace("\n", " ")[:120]
                    logger.warning(
                        f"Migration {version:03d} '{name}' Statement uebersprungen: "
                        f"{type(stmt_err).__name__}: {stmt_err} | SQL: {snippet}..."
                    )
                    # Rollback nur DIESES Statements, damit nachfolgende
                    # nicht im "transaction aborted" state landen.
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    failed_in_this_migration += 1

            # Version als angewandt markieren (auch wenn einzelne
            # Statements uebersprungen wurden — Baseline ist idempotent,
            # ein Re-Run beim naechsten Start bringt eh nichts).
            try:
                conn.execute(
                    text("INSERT INTO schema_migrations (version, name) VALUES (:v, :n)"),
                    {"v": version, "n": name}
                )
                conn.commit()
                stats["applied"] += 1
                if failed_in_this_migration:
                    logger.info(
                        f"~ Migration {version:03d}: {name} "
                        f"(mit {failed_in_this_migration} uebersprungenen Statements)"
                    )
                else:
                    logger.info(f"+ Migration {version:03d}: {name}")
            except Exception as e:
                # Kritischer Fehler: Version-Eintrag selbst ist gescheitert
                logger.error(
                    f"- Migration {version:03d} '{name}' konnte nicht als angewandt "
                    f"markiert werden: {e}"
                )
                stats["failed"] += 1
                try:
                    conn.rollback()
                except Exception:
                    pass
                break

    if stats["failed"]:
        logger.error(
            f"Migration abgebrochen: {stats['applied']} angewandt, "
            f"{stats['skipped']} uebersprungen, {stats['failed']} fehlgeschlagen"
        )
    else:
        logger.info(
            f"Migrationen ok: {stats['applied']} neu, "
            f"{stats['skipped']} bereits vorhanden"
        )

    return stats
