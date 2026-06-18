"""Postgres + pgvector connection helpers and schema bootstrap.

Uses raw psycopg3 with pgvector's psycopg adapter so vectors flow as native
Python lists / numpy arrays without manual casting. The schema is created on
the first call to :func:`ensure_schema`; subsequent calls are no-ops.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg
from pgvector.psycopg import register_vector


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


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    """Open a short-lived connection with pgvector adapters registered."""
    conn = psycopg.connect(_database_url(), autocommit=False)
    try:
        register_vector(conn)
        yield conn
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
