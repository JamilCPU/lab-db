-- Seed: domains confirmed to block automated web_search calls

INSERT INTO blocked_domains (domain, reason) VALUES
    ('duckduckgo.com',  'Bot-detection challenge on web_search — returns CAPTCHA instead of results'),
    ('google.com',      'Rate-limiting / bot-detection on direct scrape — use search API instead'),
    ('cloudflare.com',  'Blocks headless requests with Turnstile challenge');
