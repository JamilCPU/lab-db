"""
Lab DB — REST API

Endpoints:
  GET    /blocked              — list all active blocked domains
  GET    /blocked/{domain}     — check a single domain (200 = blocked, 404 = not blocked)
  POST   /blocked              — add or increment a blocked domain
  DELETE /blocked/{domain}     — soft-unblock

  GET    /digests              — list all digests (date, overview, item count)
  GET    /digests/{date}       — get full digest for a date (YYYY-MM-DD)
  POST   /digests              — create or replace a digest
  DELETE /digests/{date}       — delete a digest
"""

import os
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

DB_URL = os.environ["DB_URL"]


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def extract_domain(raw: str) -> str:
    if "://" in raw:
        return urlparse(raw).netloc.lstrip("www.")
    return raw.strip().lstrip("www.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1")
    yield


app = FastAPI(title="Lab DB API", lifespan=lifespan)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://192.0.2.99:3000",
    "http://192.0.2.99:3001",
    "http://192.0.2.99:3002",
    "http://192.0.2.101:3000",
    "http://192.0.2.101:3001",
    "http://192.0.2.101:3002",
    "http://192.0.2.102:3000",
    "http://192.0.2.102:3001",
    "http://192.0.2.102:3002",
    "http://192.0.2.103:3000",
    "http://192.0.2.103:3001",
    "http://192.0.2.103:3002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Blocked Domains models ────────────────────────────────────────────────────

class BlockedDomainIn(BaseModel):
    domain: str
    reason: str

class BlockedDomainOut(BaseModel):
    domain: str
    reason: str
    hit_count: int
    last_seen: str
    active: bool


# ── News Digest models ────────────────────────────────────────────────────────

class DigestIn(BaseModel):
    date: str        # YYYY-MM-DD
    overview: str
    items: list[dict[str, Any]]

class DigestSummary(BaseModel):
    id: int
    digest_date: str
    overview: str
    item_count: int
    created_at: str

class DigestFull(BaseModel):
    id: int
    digest_date: str
    overview: str
    items: list[dict[str, Any]]
    created_at: str
    updated_at: str


# ── Blocked Domain routes ─────────────────────────────────────────────────────

@app.get("/blocked", response_model=list[BlockedDomainOut])
def list_blocked():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT domain, reason, hit_count,
                   last_seen::text AS last_seen, active
            FROM blocked_domains
            WHERE active = TRUE
            ORDER BY hit_count DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]


@app.get("/blocked/{domain}", response_model=BlockedDomainOut)
def check_domain(domain: str):
    clean = extract_domain(domain)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT domain, reason, hit_count,
                   last_seen::text AS last_seen, active
            FROM blocked_domains
            WHERE domain = %s AND active = TRUE
            """,
            (clean,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Domain not blocked")
    return dict(row)


@app.post("/blocked", response_model=BlockedDomainOut, status_code=201)
def record_blocked(body: BlockedDomainIn):
    clean = extract_domain(body.domain)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO blocked_domains (domain, reason)
            VALUES (%s, %s)
            ON CONFLICT (domain) DO UPDATE SET
                hit_count = blocked_domains.hit_count + 1,
                last_seen = NOW(),
                active    = TRUE,
                reason    = EXCLUDED.reason
            RETURNING domain, reason, hit_count,
                      last_seen::text AS last_seen, active
            """,
            (clean, body.reason),
        )
        conn.commit()
        return dict(cur.fetchone())


@app.delete("/blocked/{domain}", status_code=204)
def unblock_domain(domain: str):
    clean = extract_domain(domain)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE blocked_domains SET active = FALSE WHERE domain = %s",
            (clean,),
        )
        conn.commit()
    return Response(status_code=204)


# ── News Digest routes ────────────────────────────────────────────────────────

@app.get("/digests", response_model=list[DigestSummary])
def list_digests():
    """List all digests newest first with item counts — used by AI News app index."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id,
                   digest_date::text AS digest_date,
                   overview,
                   jsonb_array_length(items) AS item_count,
                   created_at::text AS created_at
            FROM news_digests
            ORDER BY digest_date DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]


@app.get("/digests/{date}", response_model=DigestFull)
def get_digest(date: str):
    """Get the full digest for a given date (YYYY-MM-DD)."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id,
                   digest_date::text AS digest_date,
                   overview,
                   items,
                   created_at::text AS created_at,
                   updated_at::text AS updated_at
            FROM news_digests
            WHERE digest_date = %s
            """,
            (date,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No digest found for this date")
    return dict(row)


@app.post("/digests", response_model=DigestFull, status_code=201)
def create_digest(body: DigestIn):
    """Create or replace the digest for a given date."""
    import json
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO news_digests (digest_date, overview, items)
            VALUES (%s, %s, %s)
            ON CONFLICT (digest_date) DO UPDATE SET
                overview   = EXCLUDED.overview,
                items      = EXCLUDED.items,
                updated_at = NOW()
            RETURNING id,
                      digest_date::text AS digest_date,
                      overview,
                      items,
                      created_at::text AS created_at,
                      updated_at::text AS updated_at
            """,
            (body.date, body.overview, json.dumps(body.items)),
        )
        conn.commit()
        return dict(cur.fetchone())


@app.delete("/digests/{date}", status_code=204)
def delete_digest(date: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM news_digests WHERE digest_date = %s", (date,))
        conn.commit()
    return Response(status_code=204)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}
