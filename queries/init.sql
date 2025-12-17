-- AI Market Radar - initial schema for PostgreSQL

CREATE TABLE IF NOT EXISTS articles (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    url             TEXT NOT NULL UNIQUE,
    source          TEXT NOT NULL,
    source_id       TEXT NOT NULL,
    publish_date    TIMESTAMPTZ DEFAULT NOW(),
    first_seen_at   TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at    TIMESTAMPTZ DEFAULT NOW(),
    seen_count      INTEGER DEFAULT 1,
    sources         JSONB DEFAULT '[]'::jsonb,
    analyzed_at     TIMESTAMPTZ,
    analysis_summary    TEXT,
    analysis_category   TEXT,
    analysis_score      INTEGER,
    analysis_reasoning  TEXT,
    analysis_tags       JSONB
);

CREATE INDEX IF NOT EXISTS idx_articles_analysis_score ON articles (analysis_score);
CREATE INDEX IF NOT EXISTS idx_articles_last_seen ON articles (last_seen_at DESC);

CREATE TABLE IF NOT EXISTS article_metrics (
    id              SERIAL PRIMARY KEY,
    article_id      INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    recorded_at     TIMESTAMPTZ DEFAULT NOW(),
    metric_value    INTEGER DEFAULT 0,
    rank            INTEGER
);

CREATE INDEX IF NOT EXISTS idx_article_metrics_article_id ON article_metrics (article_id);
CREATE INDEX IF NOT EXISTS idx_article_metrics_recorded_at ON article_metrics (recorded_at DESC);

CREATE TABLE IF NOT EXISTS article_evaluations (
    id              SERIAL PRIMARY KEY,
    article_id      INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    version         INTEGER DEFAULT 1,
    model_name      TEXT DEFAULT 'deepseek-chat',
    overall_score   INTEGER DEFAULT 0,
    content         JSONB NOT NULL,
    full_evaluation TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (article_id, version)
);

CREATE INDEX IF NOT EXISTS idx_article_evals_article_id ON article_evaluations (article_id);
