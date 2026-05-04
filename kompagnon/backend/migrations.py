import os
import psycopg2


def run_migrations():
    """Erstellt die Newsletter-Datenbanktabellen falls sie noch nicht existieren."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL ist nicht gesetzt")

    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cur = conn.cursor()

    # Tabelle: newsletter_lists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_lists (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            brevo_list_id BIGINT,
            description TEXT,
            source VARCHAR(50) DEFAULT 'manual',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)

    # Tabelle: newsletters
    cur.execute("""
        CREATE TABLE IF NOT EXISTS newsletters (
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
        );
    """)

    # Tabelle: newsletter_contacts
    cur.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_contacts (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            list_id INTEGER REFERENCES newsletter_lists(id),
            crm_user_id INTEGER,
            status VARCHAR(50) DEFAULT 'subscribed',
            brevo_contact_id BIGINT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)

    # Tabelle: projects — lead_id Spalte ergaenzen
    cur.execute("""
        ALTER TABLE projects ADD COLUMN IF NOT EXISTS lead_id INTEGER;
    """)

    # Tabelle: briefings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS briefings (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER REFERENCES leads(id) ON DELETE SET NULL,
            project_id INTEGER,
            gewerk VARCHAR(100),
            leistungen TEXT,
            zielgruppe TEXT,
            einzugsgebiet VARCHAR(100),
            usp TEXT,
            mitbewerber TEXT,
            vorbilder TEXT,
            farben VARCHAR(100),
            wunschseiten TEXT,
            stil VARCHAR(50),
            logo_vorhanden BOOLEAN DEFAULT false,
            fotos_vorhanden BOOLEAN DEFAULT false,
            sonstige_hinweise TEXT,
            status VARCHAR(50) DEFAULT 'entwurf',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Tabelle: crawl_jobs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crawl_jobs (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER,
            status VARCHAR(20) DEFAULT 'pending',
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            total_urls INTEGER DEFAULT 0
        );
    """)

    # Tabelle: crawl_results
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crawl_results (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER,
            job_id INTEGER REFERENCES crawl_jobs(id) ON DELETE CASCADE,
            url VARCHAR(2000) NOT NULL,
            status_code INTEGER,
            depth INTEGER DEFAULT 0,
            load_time NUMERIC(8,3),
            crawled_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Indizes
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_crawl_jobs_customer
        ON crawl_jobs(customer_id);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_crawl_results_job
        ON crawl_results(job_id);
    """)

    # ── KAS Website (KOMPAGNON-eigene Seiten) ──────────────────────────────
    # Tabelle: kas_pages — KOMPAGNON eigene Seiten (kein lead_id)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kas_pages (
            id               SERIAL PRIMARY KEY,
            titel            VARCHAR(255) NOT NULL,
            pfad             VARCHAR(255) NOT NULL,
            meta_description TEXT DEFAULT '',
            position         INTEGER DEFAULT 0,
            status           VARCHAR(50) DEFAULT 'draft',
            ist_startseite   BOOLEAN DEFAULT false,
            notizen          TEXT DEFAULT '',
            created_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)

    # Tabelle: kas_gjs_data — GrapesJS-Inhalt pro KAS-Seite
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kas_gjs_data (
            id        SERIAL PRIMARY KEY,
            page_id   INTEGER REFERENCES kas_pages(id) ON DELETE CASCADE,
            html      TEXT DEFAULT '',
            css       TEXT DEFAULT '',
            gjs_data  JSONB DEFAULT '{}'::jsonb,
            saved_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_kas_gjs_data_page
        ON kas_gjs_data(page_id);
    """)

    # Schritt-Bestätigung (steps_confirmed JSON)
    cur.execute("""
        ALTER TABLE projects ADD COLUMN IF NOT EXISTS steps_confirmed TEXT DEFAULT '{}';
    """)

    cur.close()
    conn.close()
    print("Migrationen erfolgreich ausgefuehrt.")


if __name__ == "__main__":
    run_migrations()
