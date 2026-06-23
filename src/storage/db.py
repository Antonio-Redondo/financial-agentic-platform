"""Postgres + pgvector connection helpers and schema bootstrap.

Uses raw psycopg3 with pgvector's psycopg adapter so vectors flow as native
Python lists / numpy arrays without manual casting. The schema is created on
the first call to :func:`ensure_schema`; subsequent calls are no-ops.

Connections are served from a process-wide :class:`psycopg_pool.ConnectionPool`
so the per-query "open TCP + auth + register adapter" cost is paid once per
pooled connection instead of on every call. If ``psycopg_pool`` is unavailable
or ``DB_POOL_ENABLED=false``, :func:`get_conn` transparently falls back to the
original open-a-fresh-connection behaviour, so the app never hard-depends on
the pool.
"""
from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Iterator, Optional

import psycopg
from pgvector.psycopg import register_vector

try:  # optional dependency — fall back to direct connections if absent
    from psycopg_pool import ConnectionPool
except Exception:  # noqa: BLE001
    ConnectionPool = None  # type: ignore[assignment]

_TRUTHY = {"1", "true", "yes", "on"}


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and configure "
            "your local Postgres connection."
        )
    return url


def embedding_dim() -> int:
    return int(os.getenv("EMBEDDING_DIM", "1024"))


# --------------------------------------------------------------- connection pool
_pool: "Optional[ConnectionPool]" = None
_pool_lock = threading.Lock()
_pool_disabled = False  # set if pool creation fails → use direct connections


def _pool_enabled() -> bool:
    return (
        ConnectionPool is not None
        and not _pool_disabled
        and os.getenv("DB_POOL_ENABLED", "true").strip().lower() in _TRUTHY
    )


def _configure_connection(conn: psycopg.Connection) -> None:
    """Run once per pooled connection when it is created."""
    register_vector(conn)


def _get_pool() -> "Optional[ConnectionPool]":
    """Lazily build the shared pool. Returns None if pooling is unavailable."""
    global _pool, _pool_disabled
    if not _pool_enabled():
        return None
    if _pool is None:
        with _pool_lock:
            if _pool is None and not _pool_disabled:
                try:
                    _pool = ConnectionPool(
                        conninfo=_database_url(),
                        min_size=int(os.getenv("DB_POOL_MIN_SIZE", "1")),
                        max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
                        timeout=float(os.getenv("DB_POOL_TIMEOUT", "30")),
                        max_idle=float(os.getenv("DB_POOL_MAX_IDLE", "300")),
                        configure=_configure_connection,
                        kwargs={"autocommit": False},
                        open=True,
                    )
                except Exception as e:  # noqa: BLE001 — degrade, never crash
                    print(f"⚠️  DB pool unavailable, using direct connections: {e}",
                          flush=True)
                    _pool_disabled = True
                    _pool = None
    return _pool


def close_pool() -> None:
    """Close the shared pool (e.g. on shutdown / in tests)."""
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.close()
            _pool = None


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    """Yield a pgvector-ready connection.

    Served from the pool when available; otherwise a short-lived direct
    connection (the original behaviour). The transaction is committed on a
    clean exit and rolled back on error either way, so existing explicit
    ``conn.commit()`` calls remain correct (the final commit is then a no-op).
    """
    pool = _get_pool()
    if pool is not None:
        with pool.connection() as conn:  # returned to the pool on exit
            yield conn
        return

    conn = psycopg.connect(_database_url(), autocommit=False)
    try:
        register_vector(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


_SCHEMA_READY = False


def ensure_schema() -> None:
    """Create the `vector` extension and the documents/chunks tables.

    Safe to call repeatedly: only the first call in a process actually runs the
    DDL. If `document_chunks` exists with a different embedding dimension than
    `EMBEDDING_DIM`, a clear error is raised so the user knows to drop the
    table before switching models.
    """
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return

    dim = embedding_dim()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id              BIGSERIAL PRIMARY KEY,
                source_path     TEXT UNIQUE NOT NULL,
                filename        TEXT NOT NULL,
                content_hash    TEXT NOT NULL,
                file_size       BIGINT,
                file_extension  TEXT,
                uploaded_at     TIMESTAMPTZ DEFAULT NOW(),
                metadata        JSONB DEFAULT '{}'::jsonb
            );
            """
        )

        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id           BIGSERIAL PRIMARY KEY,
                document_id  BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index  INT NOT NULL,
                content      TEXT NOT NULL,
                embedding    vector({dim}) NOT NULL,
                metadata     JSONB DEFAULT '{{}}'::jsonb,
                UNIQUE (document_id, chunk_index)
            );
            """
        )

        # Generated tsvector column powers the BM25-style keyword leg of the
        # hybrid retriever. ADD COLUMN IF NOT EXISTS so it migrates existing
        # tables in place (Postgres backfills generated columns automatically).
        cur.execute(
            "ALTER TABLE document_chunks "
            "ADD COLUMN IF NOT EXISTS content_tsv tsvector "
            "GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;"
        )

        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_doc "
            "ON document_chunks(document_id);"
        )
        # HNSW cosine index for fast ANN search. Building it can take a moment
        # on first run but is idempotent.
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_embedding "
            "ON document_chunks USING hnsw (embedding vector_cosine_ops);"
        )
        # GIN index for fast full-text ranking (ts_rank_cd on content_tsv).
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv "
            "ON document_chunks USING gin (content_tsv);"
        )

        # Sanity-check dimension if the table pre-existed.
        cur.execute(
            """
            SELECT a.atttypmod
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            WHERE c.relname = 'document_chunks' AND a.attname = 'embedding';
            """
        )
        row = cur.fetchone()
        if row and row[0] not in (-1, dim):
            raise RuntimeError(
                f"document_chunks.embedding has dimension {row[0]} but "
                f"EMBEDDING_DIM is {dim}. Drop the table (and re-ingest) to "
                "switch embedding models."
            )

        conn.commit()

    _SCHEMA_READY = True
