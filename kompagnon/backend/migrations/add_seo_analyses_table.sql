-- Migration v14: SEO Analyse Tabelle
-- Wird automatisch via db_migrations.py (v14) ausgefuehrt.
-- Diese Datei dient nur als Referenz / Dokumentation.

CREATE TABLE IF NOT EXISTS seo_analyses (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    trade           VARCHAR(100),
    city            VARCHAR(100),
    radius_km       INTEGER DEFAULT 25,
    overall_score   INTEGER,
    keyword_score   INTEGER,
    onpage_score    INTEGER,
    competitor_score INTEGER,
    top_keywords    JSONB DEFAULT '[]',
    onpage_issues   JSONB DEFAULT '[]',
    competitors     JSONB DEFAULT '[]',
    action_plan     JSONB DEFAULT '[]',
    status          VARCHAR(20) DEFAULT 'pending',
    error_message   TEXT
);

CREATE INDEX IF NOT EXISTS idx_seo_analyses_project_id ON seo_analyses(project_id);
