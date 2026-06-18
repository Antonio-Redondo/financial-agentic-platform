# Auto-ingestion drop folder

Anything placed in this folder is **automatically ingested into pgvector on app
startup** (and when you click *Re-scan documents folder* in the sidebar).

Each file is:

1. Loaded and extracted to text (PDF, DOCX, XLSX, PPTX, CSV, JSON, HTML, MD, TXT, RTF supported).
2. Chunked with a `RecursiveCharacterTextSplitter` (1000 chars, 200 overlap).
3. Embedded with the local Ollama model in `EMBEDDING_MODEL` (default `mxbai-embed-large`, 1024-dim).
4. Upserted into the `documents` + `document_chunks` tables in Postgres.

Files are **deduplicated by content hash + source path**:

- Same path + same content → skipped.
- Same path + different content → old chunks deleted, new ones embedded.
- Deleting a file here does **not** delete it from the DB (use the *Purge*
  controls in the UI if you want that).

Subfolders are walked recursively. Hidden files (starting with `.`) are ignored.
