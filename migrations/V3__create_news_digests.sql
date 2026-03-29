-- Daily AI news digests compiled by the ai-digest agent on Pi 1.

CREATE TABLE news_digests (
    id           SERIAL PRIMARY KEY,
    digest_date  DATE         NOT NULL UNIQUE,
    overview     TEXT         NOT NULL,
    items        JSONB        NOT NULL DEFAULT '[]',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_news_digests_date ON news_digests (digest_date DESC);

COMMENT ON TABLE  news_digests            IS 'Daily AI news digests. One row per day, written by the ai-digest agent.';
COMMENT ON COLUMN news_digests.overview   IS 'One-paragraph summary of the day''s biggest AI themes.';
COMMENT ON COLUMN news_digests.items      IS 'JSON array of {category, headline, summary, url, source} objects.';
