-- Tracks domains that should be skipped during web research
-- due to bot detection, paywalls, or consistently bad results.

CREATE TABLE blocked_domains (
    id          SERIAL PRIMARY KEY,
    domain      VARCHAR(255) NOT NULL UNIQUE,
    reason      TEXT         NOT NULL,
    added_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_seen   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    hit_count   INTEGER      NOT NULL DEFAULT 1,
    active      BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_blocked_domains_domain ON blocked_domains (domain);
CREATE INDEX idx_blocked_domains_active  ON blocked_domains (active);

COMMENT ON TABLE  blocked_domains            IS 'Domains the research agent must skip. Populated from tool failures and manual entries.';
COMMENT ON COLUMN blocked_domains.domain     IS 'Bare domain only, e.g. duckduckgo.com — no scheme or path.';
COMMENT ON COLUMN blocked_domains.hit_count  IS 'Number of times this domain has triggered a failure.';
COMMENT ON COLUMN blocked_domains.active     IS 'Set to FALSE to soft-disable without losing history.';
