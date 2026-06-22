"""pgvector-backed document store with semantic search.

Replaces the in-memory keyword store with persistent storage in Postgres:

  * Each ingested source file → one row in ``documents`` (deduplicated by
    ``source_path`` and ``content_hash``).
  * Each chunk → one row in ``document_chunks`` carrying the embedding vector
    plus per-chunk metadata.

Public surface kept compatible with the previous in-memory class:

  * ``text_splitter``                — used by the UI to preview chunk counts.
  * ``index_document(text, meta)``   — chunk + embed + upsert (legacy entry).
  * ``search_documents(q, k)``       — returns ``[{content, metadata, relevance_score}]``.
  * ``get_all_documents_info()``     — listing for debug panels.
  * ``chunk_count()`` / ``unique_filenames()`` — replace the old ``.documents``
    list iteration in stats helpers.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..storage.db import ensure_schema, get_conn
from ..storage.embeddings import embed_documents, embed_query


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _rrf_fuse(result_lists: List[List[Dict]], k: int = 5,
              rrf_const: int = 60) -> List[Dict]:
    """Reciprocal Rank Fusion over multiple ranked result lists.

    Each result is identified by ``(source_path, content[:80])`` so the same
    chunk surfaced by multiple legs is recognized and its RRF scores are
    summed. The fused list is sorted descending by combined score and
    truncated to ``k``.
    """
    fused: Dict[tuple, Dict] = {}
    for results in result_lists:
        for rank, r in enumerate(results):
            key = (r["metadata"].get("source_path", ""), r["content"][:80])
            entry = fused.get(key)
            if entry is None:
                entry = dict(r)
                entry["rrf_score"] = 0.0
                fused[key] = entry
            entry["rrf_score"] += 1.0 / (rrf_const + rank + 1)
    merged = sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)
    for m in merged:
        # Expose the fused score as relevance so downstream code keeps working.
        m["relevance_score"] = m.pop("rrf_score")
    return merged[:k]


class VectorStore:
    """pgvector-backed store. Chunks, embeddings and metadata live in Postgres."""

    def __init__(self):
        # 500/100 keeps pathological char-heavy chunks (e.g. PDF ToC dot leaders)
        # under mxbai-embed-large's 512-token context window.
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
        )
        ensure_schema()

    # ----------------------------------------------------------- legacy entry
    def index_document(self, document: str, metadata: Optional[Dict] = None) -> int:
        """Chunk + embed + upsert one logical document. Returns chunks written.

        ``metadata['source_path']`` is the unique key; if omitted, it falls
        back to ``metadata['filename']`` or a synthetic ``inline:<hash>`` key
        so callers without a real path still get deduplicated behavior.
        """
        metadata = dict(metadata or {})
        text = (document or "").strip()
        if not text:
            return 0

        content_hash = _hash_text(text)
        source_path = (
            metadata.get("source_path")
            or metadata.get("filename")
            or f"inline:{content_hash[:12]}"
        )
        filename = metadata.get("filename") or os.path.basename(source_path)

        return self.upsert_document(
            source_path=source_path,
            content=text,
            content_hash=content_hash,
            filename=filename,
            file_size=metadata.get("size") or len(text.encode("utf-8")),
            file_extension=metadata.get("file_extension")
            or (os.path.splitext(filename)[1].lstrip(".").lower() or None),
            extra_metadata=metadata,
        )

    # --------------------------------------------------------------- upsert
    def upsert_document(
        self,
        *,
        source_path: str,
        content: str,
        content_hash: Optional[str] = None,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
        file_extension: Optional[str] = None,
        extra_metadata: Optional[Dict] = None,
    ) -> int:
        """Upsert one document and (re)build its chunks.

        Skips embedding when an existing row has the same ``content_hash``.
        Returns the number of chunks written this call (0 on skip).
        """
        content = (content or "").strip()
        if not content:
            return 0

        content_hash = content_hash or _hash_text(content)
        filename = filename or os.path.basename(source_path)
        extra_metadata = dict(extra_metadata or {})

        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, content_hash FROM documents WHERE source_path = %s",
                (source_path,),
            )
            row = cur.fetchone()

            if row and row[1] == content_hash:
                return 0  # unchanged → keep existing embeddings

            if row:
                doc_id = row[0]
                cur.execute(
                    "DELETE FROM document_chunks WHERE document_id = %s",
                    (doc_id,),
                )
                cur.execute(
                    """
                    UPDATE documents SET
                        filename = %s,
                        content_hash = %s,
                        file_size = %s,
                        file_extension = %s,
                        metadata = %s::jsonb,
                        uploaded_at = NOW()
                    WHERE id = %s
                    """,
                    (filename, content_hash, file_size, file_extension,
                     json.dumps(extra_metadata), doc_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO documents
                        (source_path, filename, content_hash, file_size,
                         file_extension, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING id
                    """,
                    (source_path, filename, content_hash, file_size,
                     file_extension, json.dumps(extra_metadata)),
                )
                doc_id = cur.fetchone()[0]

            chunks = self.text_splitter.split_text(content)
            if not chunks:
                conn.commit()
                return 0

            vectors = embed_documents(chunks)

            chunk_meta = {
                "filename": filename,
                "source_path": source_path,
                "file_extension": file_extension,
            }
            chunk_meta_json = json.dumps(chunk_meta)

            cur.executemany(
                """
                INSERT INTO document_chunks
                    (document_id, chunk_index, content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                """,
                [
                    (doc_id, i, chunk, vec, chunk_meta_json)
                    for i, (chunk, vec) in enumerate(zip(chunks, vectors))
                ],
            )
            conn.commit()
            return len(chunks)

    # ----------------------------------------------------------------- search
    @staticmethod
    def _filter_clause(filters: Optional[Dict]) -> tuple[str, list]:
        """Build a parameterized WHERE-suffix from a filter dict.

        Supported keys:
          * ``filenames``       — list[str], exact match on documents.filename
          * ``extensions``      — list[str], exact match on documents.file_extension
          * ``source_path_like`` — str, ILIKE pattern on documents.source_path
        Returns ``(sql_suffix, params)`` ready to splice into the query.
        """
        if not filters:
            return "", []
        clauses, params = [], []
        if filters.get("filenames"):
            clauses.append("d.filename = ANY(%s)")
            params.append(list(filters["filenames"]))
        if filters.get("extensions"):
            clauses.append("d.file_extension = ANY(%s)")
            params.append([e.lower().lstrip(".") for e in filters["extensions"]])
        if filters.get("source_path_like"):
            clauses.append("d.source_path ILIKE %s")
            params.append(filters["source_path_like"])
        if not clauses:
            return "", []
        return " AND " + " AND ".join(clauses), params

    def vector_search(self, query: str, k: int = 5,
                      filters: Optional[Dict] = None) -> List[Dict]:
        """Dense cosine-similarity search (the original retrieval leg)."""
        if not query or not query.strip():
            return []
        vec = embed_query(query)
        where_extra, where_params = self._filter_clause(filters)

        sql = f"""
            SELECT c.content, c.metadata, d.filename, d.source_path,
                   1 - (c.embedding <=> %s::vector) AS relevance_score
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE TRUE{where_extra}
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, [vec, *where_params, vec, k])
            rows = cur.fetchall()
        return self._rows_to_results(rows)

    def keyword_search(self, query: str, k: int = 5,
                       filters: Optional[Dict] = None) -> List[Dict]:
        """BM25-style full-text search using Postgres' ``ts_rank_cd``.

        Uses ``websearch_to_tsquery`` so users can pass natural phrasing
        (quoted strings, ``OR`` operator, etc.) without crafting a tsquery.
        Falls back to an empty result if the query parses to nothing.
        """
        if not query or not query.strip():
            return []
        where_extra, where_params = self._filter_clause(filters)
        sql = f"""
            SELECT c.content, c.metadata, d.filename, d.source_path,
                   ts_rank_cd(c.content_tsv,
                              websearch_to_tsquery('english', %s)) AS relevance_score
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.content_tsv @@ websearch_to_tsquery('english', %s){where_extra}
            ORDER BY relevance_score DESC
            LIMIT %s
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, [query, query, *where_params, k])
            rows = cur.fetchall()
        return self._rows_to_results(rows)

    def hybrid_search(self, query: str, k: int = 5, fetch_k: int = 20,
                      filters: Optional[Dict] = None,
                      rrf_const: int = 60) -> List[Dict]:
        """Reciprocal Rank Fusion of dense + sparse results.

        Over-fetches ``fetch_k`` from each leg, then fuses by
        ``1 / (rrf_const + rank)``. RRF is parameter-light and works well
        across heterogeneous score scales (cosine vs. ts_rank_cd).
        """
        dense = self.vector_search(query, k=fetch_k, filters=filters)
        sparse = self.keyword_search(query, k=fetch_k, filters=filters)
        return _rrf_fuse([dense, sparse], k=k, rrf_const=rrf_const)

    def search_documents(self, query: str, k: int = 5,
                         mode: Optional[str] = None,
                         filters: Optional[Dict] = None,
                         fetch_k: Optional[int] = None) -> List[Dict]:
        """Unified retrieval entry point.

        ``mode`` selects the leg(s) — ``vector`` (default for back-compat with
        env-less callers), ``keyword``, or ``hybrid``. If ``mode`` is None,
        defaults to ``$RETRIEVAL_MODE`` or ``hybrid``.
        """
        mode = (mode or os.getenv("RETRIEVAL_MODE", "hybrid")).lower()
        fetch_k = fetch_k or int(os.getenv("RETRIEVAL_FETCH_K", "20"))

        if mode == "vector":
            results = self.vector_search(query, k=k, filters=filters)
        elif mode == "keyword":
            results = self.keyword_search(query, k=k, filters=filters)
        elif mode == "hybrid":
            results = self.hybrid_search(query, k=k, fetch_k=fetch_k,
                                         filters=filters)
        else:
            raise ValueError(
                f"Unknown retrieval mode {mode!r}; expected "
                "'vector', 'keyword', or 'hybrid'."
            )
        print(f"🔍 {mode} search for {query!r} → {len(results)} chunk(s)")
        return results

    @staticmethod
    def _rows_to_results(rows) -> List[Dict]:
        out: List[Dict] = []
        for content, meta, filename, source_path, score in rows:
            md = dict(meta or {})
            md.setdefault("filename", filename)
            md.setdefault("source_path", source_path)
            out.append({
                "content": content,
                "metadata": md,
                "relevance_score": float(score) if score is not None else 0.0,
            })
        return out

    # ----------------------------------------------------------------- stats
    def chunk_count(self) -> int:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM document_chunks;")
            return int(cur.fetchone()[0])

    def unique_filenames(self) -> List[str]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT DISTINCT filename FROM documents ORDER BY filename;")
            return [r[0] for r in cur.fetchall()]

    def sample_chunks(self, k: int = 6) -> List[Dict]:
        """Return ``k`` chunks spread across the corpus for cold-start grounding.

        Used to seed question suggestions before the user has asked anything,
        so the proposals reflect the indexed documents rather than nothing.
        Shape matches ``search_documents`` (``content`` + ``metadata``).
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.content, d.filename, d.source_path
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                ORDER BY random()
                LIMIT %s
                """,
                (k,),
            )
            rows = cur.fetchall()
        return [
            {"content": content,
             "metadata": {"filename": filename, "source_path": source_path}}
            for content, filename, source_path in rows
        ]

    def known_sources(self) -> Dict[str, str]:
        """``source_path -> content_hash`` for the ingestion pipeline's
        skip-already-ingested check."""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT source_path, content_hash FROM documents;")
            return {r[0]: r[1] for r in cur.fetchall()}

    def get_all_documents_info(self) -> List[Dict]:
        """Listing used by the sidebar debug panel."""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.filename,
                       d.source_path,
                       d.file_size,
                       d.uploaded_at,
                       COUNT(c.id) AS chunks,
                       COALESCE(SUM(LENGTH(c.content)), 0) AS total_chars,
                       MIN(c.content) AS preview
                FROM documents d
                LEFT JOIN document_chunks c ON c.document_id = d.id
                GROUP BY d.id
                ORDER BY d.uploaded_at DESC
                """
            )
            rows = cur.fetchall()

        return [{
            "filename": filename,
            "source_path": source_path,
            "size_bytes": file_size,
            "uploaded_at": uploaded_at.isoformat() if uploaded_at else None,
            "chunks": int(chunks or 0),
            "content_length": int(total_chars or 0),
            "content_preview": ((preview or "")[:200] + "...") if preview else "",
        } for filename, source_path, file_size, uploaded_at,
              chunks, total_chars, preview in rows]

    def delete_source(self, source_path: str) -> bool:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE source_path = %s", (source_path,))
            deleted = cur.rowcount > 0
            conn.commit()
            return deleted

    # ---------------------------------------------------- backward-compat shim
    @property
    def documents(self) -> List[Dict]:
        """Deprecated: callers should use ``chunk_count()`` / ``unique_filenames()``.

        Kept so old code doing ``len(store.documents)`` or iterating for
        filename metadata still works without pulling embeddings or full text.
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.filename, d.source_path, c.metadata
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                """
            )
            rows = cur.fetchall()
        return [
            {
                "content": "",
                "metadata": {**(meta or {}),
                             "filename": filename,
                             "source_path": source_path},
            }
            for filename, source_path, meta in rows
        ]
