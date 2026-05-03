-- PaperRadar core schema (W1).
-- Run via: uv run python -m paperradar.index.load init
-- Idempotent: safe to re-run.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS papers (
    forum_id     TEXT PRIMARY KEY,
    raw_id       TEXT NOT NULL,
    venue        TEXT NOT NULL,
    api_version  TEXT NOT NULL,
    title        TEXT NOT NULL,
    abstract     TEXT NOT NULL,
    authors      TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    keywords     TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    primary_area TEXT,
    pdf_url      TEXT,
    is_withdrawn BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS papers_venue_idx  ON papers(venue);
CREATE INDEX IF NOT EXISTS papers_active_idx ON papers(is_withdrawn) WHERE NOT is_withdrawn;

CREATE TABLE IF NOT EXISTS reviews (
    review_id         TEXT PRIMARY KEY,
    forum_id          TEXT NOT NULL REFERENCES papers(forum_id) ON DELETE CASCADE,
    venue             TEXT NOT NULL,
    api_version       TEXT NOT NULL,
    reviewer_handle   TEXT NOT NULL,
    rating            INT,
    confidence        INT,
    summary           TEXT,
    strengths         TEXT,
    weaknesses        TEXT,
    questions         TEXT,
    overall_verdict   TEXT,
    soundness         INT,
    presentation      INT,
    contribution      INT,
    correctness       INT,
    technical_novelty INT,
    empirical_novelty INT,
    review_text       TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS reviews_forum_idx  ON reviews(forum_id);
CREATE INDEX IF NOT EXISTS reviews_venue_idx  ON reviews(venue);
CREATE INDEX IF NOT EXISTS reviews_rating_idx ON reviews(rating);

CREATE TABLE IF NOT EXISTS meta_reviews (
    meta_id         TEXT PRIMARY KEY,
    forum_id        TEXT NOT NULL REFERENCES papers(forum_id) ON DELETE CASCADE,
    venue           TEXT NOT NULL,
    api_version     TEXT NOT NULL,
    metareview      TEXT,
    decision        TEXT,
    why_not_higher  TEXT,
    why_not_lower   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS meta_reviews_forum_idx    ON meta_reviews(forum_id);
CREATE INDEX IF NOT EXISTS meta_reviews_decision_idx ON meta_reviews(decision);

-- BGE-M3 dense embeddings: 1024 dims.
-- Composite PK lets us store multiple models side-by-side for ablation.
CREATE TABLE IF NOT EXISTS paper_embeddings (
    forum_id    TEXT NOT NULL REFERENCES papers(forum_id) ON DELETE CASCADE,
    model       TEXT NOT NULL,
    embedding   vector(1024) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (forum_id, model)
);

CREATE TABLE IF NOT EXISTS review_embeddings (
    review_id   TEXT NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    model       TEXT NOT NULL,
    embedding   vector(1024) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (review_id, model)
);

-- Vector indexes (HNSW) are created AFTER bulk load via:
--   uv run python -m paperradar.index.load build-vector-indexes
