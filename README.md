# Lab DB

Lab DB was a small shared database service for a home lab: a PostgreSQL database with versioned schema migrations and a thin REST API in front of it. It stored two things for web-research agents running on other machines: a list of domains to skip (because of bot detection or paywalls) and daily AI news digests.

This was an experiment and has been superseded; the repository is kept for reference.

## Stack

- PostgreSQL 16
- Flyway 10 for SQL migrations (`migrations/`)
- Python 3.12, FastAPI, Uvicorn, psycopg2
- Docker Compose

## Running

```bash
cp .env.example .env          # set DB_PASSWORD
docker compose up --build
# API on http://localhost:8741, interactive docs at /docs
```

Flyway runs the migrations once PostgreSQL is healthy. PostgreSQL is bound to `127.0.0.1:5432`; the API is published on port 8741 on all interfaces and has no authentication, so keep it on a trusted network.

### Configuration (environment variables)

- `DB_PASSWORD` - database password (compose falls back to a weak default if unset; always set it)
- `DB_URL` - PostgreSQL connection string for the API (set by the compose file)
- `ALLOWED_ORIGINS` - comma-separated CORS origins (defaults to local development ports)

## API

- `GET /blocked`, `GET /blocked/{domain}`, `POST /blocked`, `DELETE /blocked/{domain}` - blocked-domain list (re-posting a domain increments its hit count; delete is a soft unblock)
- `GET /digests`, `GET /digests/{date}`, `POST /digests`, `DELETE /digests/{date}` - one news digest per date, with items stored as JSONB

## Project layout

- `api/` - FastAPI app (`main.py`), requirements and Dockerfile
- `migrations/` - Flyway migrations: `blocked_domains` table, seed data, `news_digests` table
- `docker-compose.yml` - PostgreSQL, Flyway and the API

## Status

Superseded and no longer maintained. There are no automated tests.
