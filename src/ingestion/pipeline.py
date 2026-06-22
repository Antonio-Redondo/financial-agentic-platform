"""Folder ingestion pipeline.

Walks ``DOCUMENTS_DIR`` (default ``./data/documents``), and for each file:

  1. Extracts text via :mod:`ingestion.loaders`.
  2. Hashes the extracted text and asks the store whether it already has that
     exact content for this path (skip if yes).
  3. Otherwise chunks → embeds → upserts into pgvector.

Designed to be safe to call on every app startup: it only does real work for
new or changed files.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .loaders import load_text


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def documents_dir() -> str:
    return os.path.abspath(os.getenv("DOCUMENTS_DIR", "./data/documents"))


@dataclass
class IngestionResult:
    scanned: int = 0
    ingested: int = 0          # files newly added or refreshed
    skipped_unchanged: int = 0
    skipped_empty: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def _iter_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        # Ignore hidden directories (.git, .venv, etc.)
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.startswith("."):
                continue
            if name.lower() == "readme.md":
                continue  # the folder's own README
            yield os.path.join(dirpath, name)


def ingest_file(vector_store, path: str) -> Optional[int]:
    """Ingest a single file. Returns chunks written, ``None`` on empty/skip."""
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        return None

    text = load_text(path)
    if not text.strip():
        return None

    stat = os.stat(path)
    extension = os.path.splitext(path)[1].lstrip(".").lower() or None
    filename = os.path.basename(path)

    chunks = vector_store.upsert_document(
        source_path=path,
        content=text,
        content_hash=_hash_text(text),
        filename=filename,
        file_size=stat.st_size,
        file_extension=extension,
        extra_metadata={
            "source": "folder_scan",
            "ingested_at": datetime.utcnow().isoformat() + "Z",
        },
    )
    return chunks


def ingest_folder(vector_store, folder: Optional[str] = None) -> IngestionResult:
    """Walk ``folder`` (or ``DOCUMENTS_DIR``) and ingest everything new/changed."""
    folder = os.path.abspath(folder or documents_dir())
    os.makedirs(folder, exist_ok=True)

    result = IngestionResult()
    known = vector_store.known_sources()

    for path in _iter_files(folder):
        result.scanned += 1
        try:
            text = load_text(path)
            if not text.strip():
                result.skipped_empty += 1
                continue

            content_hash = _hash_text(text)
            if known.get(path) == content_hash:
                result.skipped_unchanged += 1
                continue

            stat = os.stat(path)
            extension = os.path.splitext(path)[1].lstrip(".").lower() or None
            written = vector_store.upsert_document(
                source_path=path,
                content=text,
                content_hash=content_hash,
                filename=os.path.basename(path),
                file_size=stat.st_size,
                file_extension=extension,
                extra_metadata={
                    "source": "folder_scan",
                    "ingested_at": datetime.utcnow().isoformat() + "Z",
                },
            )
            if written > 0:
                result.ingested += 1
                print(f"📥 Ingested {path} → {written} chunk(s)", flush=True)
            else:
                result.skipped_unchanged += 1
        except Exception as e:  # noqa: BLE001
            msg = f"{path}: {e}"
            result.errors.append(msg)
            print(f"❌ Ingestion error — {msg}", flush=True)

    print(
        f"📊 Folder scan complete — scanned={result.scanned}, "
        f"ingested={result.ingested}, unchanged={result.skipped_unchanged}, "
        f"empty={result.skipped_empty}, errors={len(result.errors)}",
        flush=True,
    )
    return result


def save_upload(uploaded_file, folder: Optional[str] = None) -> str:
    """Persist a Streamlit ``UploadedFile`` into the ingestion folder.

    Returns the absolute path written. Existing files with the same name are
    overwritten — the upsert + content-hash check downstream ensures we don't
    re-embed identical content.
    """
    folder = os.path.abspath(folder or documents_dir())
    os.makedirs(folder, exist_ok=True)
    # Strip any path components from the uploaded name so a crafted filename
    # like "../../etc/passwd" can't escape the docs folder.
    safe_name = os.path.basename(uploaded_file.name.replace("\\", "/"))
    if not safe_name or safe_name in (".", ".."):
        raise ValueError(f"Refusing to save upload with unsafe name: {uploaded_file.name!r}")
    target = os.path.abspath(os.path.join(folder, safe_name))
    if os.path.commonpath([folder, target]) != folder:
        raise ValueError(f"Refusing to save upload outside docs folder: {uploaded_file.name!r}")
    with open(target, "wb") as f:
        f.write(uploaded_file.getvalue())
    return target
