"""Die Migrationen, die beim Serverstart laufen.

**Warum als eigenes Modul (L-25, 22.08.2026).** `main.py` hatte 2.209 Zeilen,
und man erwartet dort viele Endpunkte. Tatsaechlich sind es zehn — die Masse
war **eine einzige Funktion**: diese hier, 1.234 Zeilen. Ausgelagert bleibt
`main.py` bei rund 970 Zeilen und ist wieder lesbar.

**Reiner Umzug.** Kein Migrationsschritt wurde veraendert, umsortiert,
zusammengefasst oder weggelassen; die Ausfuehrungsreihenfolge ist unberuehrt.
Gegenprobe beim Umzug: 477 `ALTER TABLE`/`CREATE TABLE`/`CREATE INDEX`
vorher, 477 nachher.

**Was eine Migration hier ist.** Eine Anweisung der Form „falls die Spalte
noch nicht da ist, lege sie an". Sie laeuft bei jedem Start und tut beim
zweiten Mal nichts mehr. Ueber anderthalb Jahre sind so 477 zusammengekommen;
jede einzelne ist harmlos, zusammen machten sie die zentrale Datei unlesbar.

**Diese Datei ist die einzige, die beim Start wirklich laeuft.** `migrations.py`
und `migrate.py` daneben tun es nicht, und `create_all` ruestet keine Spalten
nach — wer eine neue Spalte braucht, traegt sie **hier** ein. Das war schon
vor dem Umzug die Falle und ist es danach.
"""
import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


def run_migrations():
    """Führt alle fehlenden Spalten-Migrationen aus."""
    from database import engine
    migrations = [
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
        # Kriterienkatalog ab 2026-08-11 (services/audit_criteria.py):
        # Punkte und Quellen liegen als JSON, damit neue Kriterien keine
        # Migration brauchen. Die Einzelspalten oben sind Altbestand.
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS item_scores TEXT DEFAULT '{}'",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS item_sources TEXT DEFAULT '{}'",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS category_scores TEXT DEFAULT '[]'",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS blockers TEXT DEFAULT '[]'",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS coverage INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS collection_notes TEXT DEFAULT '{}'",
        # Branchenmodell des Homepage Standards 2026.2: Gegen welchen Maßstab
        # bewertet wurde, gehört zum Ergebnis — ohne diese Angabe lässt sich
        # ein Bericht später weder erklären noch mit einem neueren vergleichen.
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS erkannte_branche VARCHAR DEFAULT ''",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS branchenklasse VARCHAR DEFAULT ''",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS standard_version VARCHAR DEFAULT ''",
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
        "ALTER TABLE academy_modules ADD COLUMN IF NOT EXISTS description TEXT DEFAULT ''",
        "ALTER TABLE academy_modules ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500) DEFAULT ''",
        "ALTER TABLE academy_courses ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE",
        """CREATE TABLE IF NOT EXISTS academy_module_access (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            module_id INTEGER REFERENCES academy_modules(id) ON DELETE CASCADE,
            assigned_at TIMESTAMP DEFAULT NOW(),
            assigned_by INTEGER
        )""",
        "CREATE INDEX IF NOT EXISTS idx_academy_module_access_kunde "
        "ON academy_module_access(customer_id)",
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
        # Befunde der Anreicherung, bis 17.08.2026 nur als Textzeile in `notes`
        # (UX-06). NULL heisst „noch nicht geprueft", nicht „nicht vorhanden".
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS has_ssl BOOLEAN",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS has_impressum BOOLEAN",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS enriched_at TIMESTAMP",
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
        # ── Project-Type + ISB-Förder-Felder (IMPULS-Projekt, ISB-158) ──────
        # Vorher landeten Antrag/Bewilligung/Volumen/Tagewerke als Pipe-Text
        # in leads.notes — nicht queryable. Jetzt strukturiert auf projects.
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_type VARCHAR(20) DEFAULT 'standard'",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS isb_antrag_datum DATE",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS isb_bewilligung_datum DATE",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS foerder_volumen NUMERIC(10,2)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS isb_tagewerke INTEGER",
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
        # Zeilen, die vor der Spalte entstanden oder am Modell vorbei
        # angelegt wurden, tragen NULL. Ein einziges solches Projekt hat
        # produktiv `/api/dashboard/alerts` mit 500 beantwortet.
        "UPDATE projects SET scope_creep_flags = 0 WHERE scope_creep_flags IS NULL",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS public_token VARCHAR(64)",
        # Über wie viele Seiten ein Audit urteilt (21.08.2026). Altzeilen
        # bekommen 1: Sie kannten nur die Startseite.
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS "
        "seiten_geprueft INTEGER DEFAULT 1",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS "
        "seiten_gefunden INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS lifecycle_phase VARCHAR(30)",
        "CREATE INDEX IF NOT EXISTS idx_leads_lifecycle_phase "
        "ON leads(lifecycle_phase)",
        # Eine Schreibweise je Quelle (L-59, gemessen 21.08.2026).
        # `routers/leads.py:1354` schrieb `Manuell`, drei Frontend-Stellen
        # schreiben `manual` — und der Quellenfilter der Betriebsliste
        # vergleicht auf `manual` (`utils/betriebeListe.js:83`). Von Hand
        # angelegte Betriebe aus dem Backend waren ueber „Von Hand" nicht zu
        # finden; sie bekamen eine eigene Gruppe und sahen aus wie eine eigene
        # Quelle. Beim Lesen wird die Zuordnung angewandt — der Filter aber
        # vergleicht den gespeicherten Wert, deshalb auch hier.
        # Der Wortschatz steht in `services/lead_quellen.SCHREIBWEISEN`.
        "UPDATE leads SET lead_source = 'manual' WHERE lead_source = 'Manuell'",
        "UPDATE leads SET lead_source = 'audit' WHERE lead_source = 'Audit'",
        # `role_permissions` hatte keinen eindeutigen Schluessel auf
        # (role, permission) — und `services/rechte.hat_recht` liest mit
        # `.first()` **ohne** Sortierung. Zwei Zeilen mit verschiedenem
        # `is_allowed` haetten die Antwort dem Zufall ueberlassen: ein
        # entzogenes Recht kaeme still zurueck. Der Schreibpfad prueft zwar
        # vorher, aber nichts **verhindert** es (L-05).
        # Erst zusammenfuehren, dann sperren — die juengste Zeile gewinnt,
        # denn sie ist die zuletzt gespeicherte Entscheidung.
        """DELETE FROM role_permissions a
             USING role_permissions b
            WHERE a.role = b.role
              AND a.permission = b.permission
              AND a.id < b.id""",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_role_permissions_eindeutig "
        "ON role_permissions(role, permission)",
        "CREATE INDEX IF NOT EXISTS idx_audit_results_public_token "
        "ON audit_results(public_token)",
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
        # Eigenprüfung: welche selbst gebaute Seite dieses Audit gemessen hat
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS sitemap_page_id INTEGER",
        "CREATE INDEX IF NOT EXISTS idx_audit_results_sitemap_page "
        "ON audit_results(sitemap_page_id)",
        # Diese vier Spalten hat bis zum 15.08.2026 niemand befuellt — der
        # Vorgabewert `false` sah im Bericht aus wie ein Messergebnis, und das
        # PDF verlangte daraufhin etwa, eine GPTBot-Sperre zu entfernen, die es
        # nicht gab. Ohne Vorgabewert bedeutet NULL jetzt „nicht erhoben".
        "ALTER TABLE audit_results ALTER COLUMN llms_txt DROP DEFAULT",
        "ALTER TABLE audit_results ALTER COLUMN robots_ai_friendly DROP DEFAULT",
        "ALTER TABLE audit_results ALTER COLUMN structured_data DROP DEFAULT",
        # Bestehende Zeilen tragen den Vorgabewert, nicht eine Messung. Die
        # feste Datumsgrenze macht die Anweisung wiederholbar: Laeufe ab dem
        # Umstellungstag bleiben unberuehrt, auch beim naechsten Start.
        "UPDATE audit_results SET llms_txt = NULL, robots_ai_friendly = NULL, "
        "structured_data = NULL WHERE created_at < '2026-08-15'",
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
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS funktionen_json TEXT",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS seo_json TEXT",
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
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_guideline_json TEXT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_guideline_generated_at TIMESTAMP",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_font_heading VARCHAR(100)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_font_body VARCHAR(100)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_font_accent VARCHAR(100)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_fonts_detail TEXT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS brand_design_tokens_json TEXT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS kaltakquise_gesendet_at TIMESTAMP",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS kaltakquise_count INTEGER DEFAULT 0",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS perf_report_last_mobile INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS perf_report_last_desktop INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS perf_report_sent_at TIMESTAMP",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS perf_report_sent_count INTEGER DEFAULT 0",
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
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_dns_retry_after TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_dns_fail_count INTEGER DEFAULT 0",
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
        # Hotfix 2026-05-04: h3s + links_internal + links_external waren nur
        # in routers/crawler.py:190-195 als Lazy-Migration registriert (laeuft
        # erst beim ersten Crawler-Save). Auf frischer Staging-DB fehlten sie
        # daher dem GET /api/crawler/content/{lead_id} Endpoint, der mit 500
        # crashte (UndefinedColumn h3s).
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS h3s TEXT DEFAULT '[]'",
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS links_internal TEXT DEFAULT '[]'",
        "ALTER TABLE website_content_cache ADD COLUMN IF NOT EXISTS links_external TEXT DEFAULT '[]'",
        """CREATE INDEX IF NOT EXISTS idx_website_content_cache_customer
           ON website_content_cache(customer_id)""",
        # Netlify-Integration (NETLIFY_API_TOKEN env-Variable erforderlich)
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
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS deal_id INTEGER",
        # DNS-Polling backoff (exponential backoff on repeated failures)
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_dns_fail_count INTEGER DEFAULT 0",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_dns_retry_after TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_golive_mail_sent BOOLEAN DEFAULT false",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_golive_mail_sent_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS netlify_ssl_checked_at TIMESTAMP",
        # Freigabe-Gates (Tor 1 + Tor 2)
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS briefing_approved_at TIMESTAMP",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS content_approval_token VARCHAR(255)",
        # Ziele & Zielgruppe flat fields
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS hauptziel TEXT",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS aktionen TEXT",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS typischer_kunde TEXT",
        "ALTER TABLE briefings ADD COLUMN IF NOT EXISTS haeufige_anfrage TEXT",
        # Batch-Content-Generierung für Sitemap-Seiten
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_h1 TEXT",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_hero_text TEXT",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_abschnitt_text TEXT",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_cta VARCHAR(100)",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_meta_title VARCHAR(70)",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ki_meta_description VARCHAR(160)",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS content_generated BOOLEAN DEFAULT false",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS content_generated_at TIMESTAMP",
        # Hormozi-Spec Section-Plan pro Page (Pipeline-Stage 2 → 3)
        # Speichert ein JSON-Array von Section-Keys aus der Wireframe-Library,
        # z.B. ["hero_value_equation","problem","offer_stack","trust_strip",
        #       "fallstudien_3","guarantee_block","faq","cta_final"]
        # Siehe docs/conversion-spec-shk.md + docs/kas-pipeline-architecture.md
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS sections_json TEXT",
        # ── Phase 1 Crawl-Import (2026-05-05): Bestand-Sitemap aus Kunden-Site ─
        # source unterscheidet 'manual' (CRUD), 'ki_generated' (KI-Vorschlag),
        # 'crawled' (aus Bestands-Website importiert). original_url speichert die
        # ursprüngliche URL bei gecrawlten Seiten. replaces_page_ids ist ein
        # JSON-Array von sitemap_page-IDs, die ein KI-Vorschlag konsolidiert.
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'manual'",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS original_url TEXT",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS replaces_page_ids TEXT",
        # ── Relume-Parität R1 (2026-05-05): per-Page-KI-Prompt + User-Color-Tag.
        # ai_prompt: optionaler Per-Page-„Goal"-Text, der dem KI-Content-Writer
        # zusätzlichen Kontext gibt. color_tag: User-frei wählbarer Hex-Code für
        # visuelle Organisation (vs page_type-Farbe, die fix vom Type kommt).
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS ai_prompt TEXT",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS color_tag VARCHAR(7)",
        # ── Relume-Parität R2 Feature 4 (2026-05-05): Alternative-Sitemap-Variants.
        # 'primary' = aktuelle Live-Sitemap. 'variant' = parallele KI-Alternative
        # zum Vergleich. Pflichtseiten + Bestand sind immer 'primary'; nur
        # KI-Vorschläge können 'variant' sein. Promote ersetzt primary durch variant.
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS variant VARCHAR(20) DEFAULT 'primary'",
        # ── Phase 4 (2026-05-07): Page-Groups. Eine Page kann als 'Gruppe'
        # markiert sein — die Gruppe traegt einen Default-Section-Plan, alle
        # Kind-Seiten erben den Plan automatisch (Showcase/Portfolio-Pattern).
        # is_group=true verwandelt die Karte visuell in einen Gruppen-Container,
        # group_template_sections speichert die geteilten Sections als JSON-Array.
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS is_group BOOLEAN DEFAULT false",
        "ALTER TABLE sitemap_pages ADD COLUMN IF NOT EXISTS group_template_sections TEXT",
        # ── Hotfix 2026-05-04: steps_confirmed war nur in migrations.py
        # (Standalone-Script, lief nie beim Backend-Start). Auf der frischen
        # Staging-DB fehlte die Spalte komplett — routers/projects.py warf
        # 500 Internal Server Error bei jedem GET /api/projects/{id}.
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS steps_confirmed TEXT DEFAULT '{}'",
        # ── Hotfix 2026-05-07: briefing_submitted_at ist im manuellen SQL-Script
        # (migrations/manual/2026-05-04-backfill-phase2.sql) befuellt, das ALTER
        # TABLE wurde aber nie auto-ausgefuehrt. Resultat: AttributeError beim
        # POST /api/briefings/{id}, weil routers/briefings.py die Spalte setzt.
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS briefing_submitted_at TIMESTAMP",
        # ── Component Library (Wireframe-Blocks) — Schritt A ────────────────
        # Speichert die 41 HTML+Tailwind-Templates fuer den KI-Wireframe-
        # Generator. Seed via seeds/seed_component_library.py (Schritt C).
        # Siehe database.py:ComponentLibrary fuer das ORM-Mapping.
        """CREATE TABLE IF NOT EXISTS component_library (
            id              SERIAL PRIMARY KEY,
            slug            VARCHAR(50) UNIQUE NOT NULL,
            name            VARCHAR(100) NOT NULL,
            category        VARCHAR(50) NOT NULL,
            tags            JSONB DEFAULT '[]'::jsonb,
            html_template   TEXT NOT NULL,
            slots           JSONB DEFAULT '[]'::jsonb,
            ki_prompt_hint  TEXT,
            preview_note    TEXT,
            created_at      TIMESTAMP DEFAULT NOW()
        )""",
        "CREATE INDEX IF NOT EXISTS idx_component_library_category ON component_library(category)",
        # Wireframe-Daten pro Projekt: Block-Zuweisungen + Slot-Werte pro
        # Sitemap-Seite. Wird vom KI-Generator (Schritt D) befuellt.
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS wireframe_data JSONB DEFAULT '[]'::jsonb",
        # ── Widget-Anfragen 2026-08-12 ──────────────────────────────────────
        # Neue Spalten an einer Tabelle, die es schon gibt. create_all() legt
        # nur fehlende Tabellen an und ruestet keine Spalten nach — ohne diese
        # beiden Zeilen laeuft der Teaser auf Staging in einen ProgrammingError.
        "ALTER TABLE widget_requests ADD COLUMN IF NOT EXISTS poll_token VARCHAR(64)",
        "CREATE INDEX IF NOT EXISTS idx_widget_requests_poll_token ON widget_requests(poll_token)",
        "ALTER TABLE widget_requests ADD COLUMN IF NOT EXISTS report_confirmed_at TIMESTAMP",
        # ── Adressbestaetigung vor dem Bericht 2026-08-12 ───────────────────
        # Erst nach dem Klick in der Bestaetigungsmail geht die Mail mit dem
        # Berichtslink raus.
        "ALTER TABLE widget_requests ADD COLUMN IF NOT EXISTS verify_token VARCHAR(64)",
        "CREATE INDEX IF NOT EXISTS idx_widget_requests_verify_token ON widget_requests(verify_token)",
        "ALTER TABLE widget_requests ADD COLUMN IF NOT EXISTS verify_sent_at TIMESTAMP",
        "ALTER TABLE widget_requests ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP",
        # Wer bestaetigt hat — ohne das war nicht feststellbar, welcher Dienst
        # die Bestaetigungslinks von selbst ausloest.
        "ALTER TABLE widget_requests ADD COLUMN IF NOT EXISTS verified_user_agent VARCHAR(400)",
        "ALTER TABLE widget_requests ADD COLUMN IF NOT EXISTS verified_ip VARCHAR(64)",
        # Zaehlt die Versandversuche der Bestaetigung — begrenzt den zweiten
        # Versuch aus dem Widget (UX-08, 17.08.2026).
        "ALTER TABLE widget_requests ADD COLUMN IF NOT EXISTS verify_attempts INTEGER DEFAULT 0",
        # ── Entwurfs-Status fuer erzeugte Bloecke 2026-08-13 ────────────────
        # Bestehende Bloecke sind freigegeben; nur neu erzeugte starten als
        # Entwurf. Default deshalb 'approved'.
        "ALTER TABLE component_library ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'approved'",
        "UPDATE component_library SET status = 'approved' WHERE status IS NULL",
        "CREATE INDEX IF NOT EXISTS idx_component_library_status ON component_library(status)",
        # ── Tatsaechliche KI-Sichtbarkeit 2026-08-22 (L-58 b) ───────────────
        # Bis hierhin mass GEO nur die Voraussetzungen — llms.txt, offene
        # Crawler, strukturierte Daten. Ob ChatGPT, Perplexity oder Claude den
        # Betrieb auf eine Kundenfrage hin wirklich **nennen**, steht jetzt
        # hier: je System die gestellten Fragen, die Belege und die Trefferzahl.
        # NULL heisst „nie gelaufen" — ausdruecklich nicht „nicht gefunden".
        "ALTER TABLE geo_analyses ADD COLUMN IF NOT EXISTS ki_sichtbarkeit JSONB",
        "ALTER TABLE geo_analyses ADD COLUMN IF NOT EXISTS ki_sichtbarkeit_am TIMESTAMP",
        # Der Verlauf, nicht nur der letzte Stand (L-85, 22.08.2026). Der
        # Wert der Messung entsteht aus dem Vergleich: „vor drei Monaten
        # null Nennungen, heute drei" ist die Aussage, fuer die ein
        # Betrieb zahlt.
        "ALTER TABLE geo_analyses ADD COLUMN IF NOT EXISTS ki_sichtbarkeit_verlauf JSONB",
    ]
    academy_tables = [
        'academy_courses', 'academy_modules', 'academy_lessons',
        'academy_progress', 'academy_lesson_progress',
        'academy_certificates', 'academy_quiz_questions',
        'academy_customer_access', 'academy_checklist_items',
    ]
    # Jedes Statement bekommt seine eigene Transaktion.
    #
    # Vorher lief die ganze Liste in einer einzigen, mit einem commit() am
    # Ende. Auf PostgreSQL bricht aber das erste fehlschlagende Statement die
    # Transaktion ab; jedes weitere scheitert dann mit „current transaction is
    # aborted", das ``pass`` verschluckt es, und der commit() schreibt nichts.
    # Ein einziger Fehler weit vorne machte damit alles dahinter wirkungslos —
    # lautlos. Genau so sind poll_token und report_confirmed_at nie entstanden,
    # obwohl sie am Ende der Liste standen.
    fehler = []
    try:
        with engine.connect() as conn:
            for sql in migrations:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception as e:  # noqa: BLE001
                    conn.rollback()  # sonst bleibt die Verbindung vergiftet
                    fehler.append((sql.strip().split("\n")[0][:80], str(e).split("\n")[0][:120]))
            # Verify academy tables exist and log
            for tbl in academy_tables:
                try:
                    conn.execute(text(f"SELECT 1 FROM {tbl} LIMIT 1"))
                    logger.info(f"✓ {tbl} OK")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"✗ {tbl} FEHLER: {e}")
        # Die meisten „Fehler" sind harmlos (Spalte existiert schon). Sie
        # gehören trotzdem ins Log: sonst ist eine Migration, die wirklich
        # nicht durchkam, von einer, die nichts zu tun hatte, nicht zu
        # unterscheiden — und das hat schon einen halben Tag gekostet.
        logger.info(f"✓ Migrationen abgeschlossen — {len(migrations) - len(fehler)} "
                    f"von {len(migrations)} ausgeführt")
        for sql, grund in fehler:
            logger.info(f"  · übersprungen: {sql} — {grund}")
    except Exception as e:
        logger.warning(f"Migration Warnung: {e}")

    # Create any ORM-defined tables that don't exist yet (incl. project_scraped_pages, project_scrape_jobs)
    try:
        from database import Base, engine as db_engine
        Base.metadata.create_all(bind=db_engine)
        logger.info("✓ Base.metadata.create_all abgeschlossen")
    except Exception as e:
        logger.warning(f"create_all Warnung: {e}")
