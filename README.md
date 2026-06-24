# 🏦 Financial Agentic Platform

> **Advanced Prepayment Analytics & Risk Assessment Platform**
> *A multi-agent RAG app that runs fully locally with [Ollama](https://ollama.com) + [pgvector](https://github.com/pgvector/pgvector) — no cloud, no API keys.*

---

## 🖥️ Deploy Locally

The app runs **100% offline**: local LLMs via Ollama + a local Postgres/pgvector
database for persistent chunks, embeddings, and metadata. No cloud, no API keys.

**Prerequisites:** Python 3.11+, [Ollama](https://ollama.com/download), and Docker
(or an existing Postgres with the pgvector extension available).

```bash
# 1️⃣ Pull the models (Ollama). The router uses two chat models by default.
ollama pull llama3.2:1b           # fast chat model (CPU-friendly)
ollama pull qwen2.5:3b            # stronger chat model (used by the router)
ollama pull mxbai-embed-large     # embeddings — 1024-dim, matches $EMBEDDING_DIM
ollama serve                       # ensure the server is running (often already is)

# 2️⃣ Start Postgres + pgvector (Docker is easiest — the image bundles pgvector).
docker run -d --name financial-rag-pg \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=financial_rag \
  -p 5432:5432 pgvector/pgvector:pg16
#    The app auto-creates the `vector` extension + tables on first run, so no
#    manual SQL is needed. (Using your own Postgres? Just make sure the pgvector
#    extension is installed and DATABASE_URL points at it.)

# 3️⃣ Configure environment (copy the template; adjust DATABASE_URL if needed).
cp .env.example .env

# 4️⃣ Install dependencies and launch.
pip install -r requirements.txt
streamlit run src/ui/app.py --server.port 8516

# 🌐 Open: http://localhost:8516
```

On first run the app creates the `documents` + `document_chunks` tables (and the
`vector` extension), then scans `./data/documents/` for files to ingest.

> 💡 **Don't want the router?** Set `MODEL_ROUTER_ENABLED=false` in `.env` and only
> `llama3.2:1b` is required — `qwen2.5:3b` is needed only while routing is on.

### Configuration (`.env`)

```env
# Models
OLLAMA_MODEL=llama3.2:1b                 # model used when routing is OFF
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=mxbai-embed-large
EMBEDDING_DIM=1024

# Model router (data-driven; see "Evals & Model Router" below)
MODEL_ROUTER_ENABLED=true
ROUTER_FAST_MODEL=llama3.2:1b
ROUTER_STRONG_MODEL=qwen2.5:3b

# Storage + ingestion
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/financial_rag
DOCUMENTS_DIR=./data/documents
```

> 💡 **Switching embedding models.** Changing `EMBEDDING_MODEL` requires
> changing `EMBEDDING_DIM` to match (e.g. `nomic-embed-text` is 768).
> Drop the `document_chunks` table so it can be recreated with the new
> dimension, then re-ingest.

---

## 📥 Where Do My Documents Go?

There are **two equivalent ways** to feed the pipeline; both end up in pgvector.

### Option A — drop files into the ingestion folder (recommended)

```text
./data/documents/
```

Anything placed here is auto-ingested on the next app startup (or when you
click **🔄 Re-scan documents folder** in the sidebar). Files are deduplicated
by content hash + source path, so:

- Same file unchanged → skipped (no re-embedding).
- Same path, edited content → old chunks dropped, new ones embedded.
- Subfolders are walked recursively.

### Option B — use the upload UI in the sidebar

Uploads are saved into `./data/documents/` first, then ingested via the same
pipeline. You can leave files there for the next startup; nothing is lost on
restart.

### What gets stored

| Table | Columns |
| --- | --- |
| `documents` | `id`, `source_path` (unique), `filename`, `content_hash`, `file_size`, `file_extension`, `uploaded_at`, `metadata` (JSONB) |
| `document_chunks` | `id`, `document_id` (FK), `chunk_index`, `content`, `embedding` (`vector(1024)`), `metadata` (JSONB) |

An HNSW cosine-similarity index (`vector_cosine_ops`) on `document_chunks.embedding`
backs the retriever.

---

## 🧠 How It Works — Multi-Agent Graph

This is a genuine agentic workflow built on **LangGraph**, not a single LLM call.
Specialized agents collaborate to route, retrieve, and answer:

```
   🧭 Planner ──(general)──────────────┐
      │ (document)                     │
      ▼                                ▼
   🔎 Retriever ─────────────────▶ ✍️ Analyst ──▶ ✅ Finalize
```

- **Planner** — classifies the request on two axes in a single LLM call:
  (1) does it need the user's uploaded documents vs. general knowledge, and
  (2) is it **SIMPLE** or **COMPLEX** (used by the model router).
- **Retriever** — hybrid search over `document_chunks` in pgvector (dense cosine +
  Postgres full-text, fused with Reciprocal Rank Fusion) returning the top-k matches.
- **Analyst** — writes the answer (streamed token-by-token to the UI), grounded
  in the retrieved context when present, using the model the router selected.

## ⚖️ Evals & Model Router

Different models trade quality for speed. Rather than guess, the app **measures**
each model and routes per query.

**Run the evals** (needs Ollama; not Postgres):

```bash
ollama pull llama3.2:1b && ollama pull qwen2.5:3b
python -m evals.run_evals          # add --limit 6 for a quick smoke run
```

This runs a curated set of financial queries ([evals/dataset.py](evals/dataset.py))
through each model and scores every answer two ways:

- **Key-point coverage** — deterministic: fraction of expected concepts present.
- **LLM-as-judge** — a 1–5 correctness/relevance rating from the strongest model.

…plus **latency**. Results land in `evals/results/` (`summary.md`,
`results_<ts>.json`) and the harness derives **`policy.json`**: for each
complexity bucket it keeps the fast model unless the strong model's judged
quality gain exceeds `QUALITY_TOLERANCE`. The mapping is **whatever the data
says** — it is not assumed to be "simple→fast, complex→strong".

**The router** ([src/agents/router.py](src/agents/router.py)) reads `policy.json`
(falling back to the `ROUTER_*` env vars) and the planner's SIMPLE/COMPLEX label
to pick the model per query at **no extra latency** (the classification rides on
the planner call that already runs). Toggle it live with **🧭 Auto model routing**
in the sidebar; the answer footer and trace show which model replied.

> 📊 **Re-run the evals on your machine** to generate a policy tuned to your
> hardware and models — the committed `policy.json` reflects one CPU run and may
> differ from yours (small local models can score unintuitively per bucket).

## 📄 Supported Document Formats

Upload financial documents (or drop them into `./data/documents/`) and ask
questions about them:

```
📕 PDF          📊 Excel (.xlsx/.xls), CSV      📝 Word (.docx), Text, RTF, Markdown
📽️ PowerPoint  🌐 HTML/XML                      📋 JSON
```

## 🏗️ Architecture

```mermaid
flowchart TB
    User([👤 User])

    subgraph UI["🖥️ UI — Streamlit"]
        App["app.py<br/>chat · upload · model & routing controls"]
    end

    subgraph Agents["🧠 Agentic Graph — LangGraph"]
        direction TB
        Planner["🧭 Planner<br/>doc-vs-general · SIMPLE/COMPLEX"]
        Router["🔀 Model Router<br/>policy.json → fast/strong"]
        Retriever["🔎 Retriever<br/>hybrid search + RRF"]
        Analyst["✍️ Analyst<br/>streamed, grounded answer"]
        Finalize["✅ Finalize"]

        Planner -->|document| Retriever
        Planner -->|general| Analyst
        Retriever --> Analyst
        Analyst --> Finalize
        Router -.->|selects model| Analyst
        Planner -.->|complexity| Router
    end

    subgraph Ingestion["📥 Ingestion"]
        direction TB
        Loaders["loaders.py<br/>PDF/DOCX/XLSX/… → text"]
        Pipeline["pipeline.py<br/>scan · chunk · upsert"]
        Loaders --> Pipeline
    end

    subgraph Storage["🗄️ Storage — Postgres + pgvector"]
        DB[("document_chunks<br/>HNSW cosine + GIN full-text")]
    end

    subgraph Ollama["🤖 Ollama (local)"]
        Chat["Chat models<br/>fast + strong"]
        Embed["Embedding model"]
    end

    subgraph Evals["⚖️ Evals"]
        Runner["run_evals.py<br/>coverage · LLM-judge · latency"]
        Policy["policy.json"]
        Runner --> Policy
    end

    User <-->|query / streamed answer| App
    App --> Planner
    Finalize --> App

    Retriever -->|top-k| DB
    Pipeline -->|embeddings| DB
    Pipeline -. embeds .-> Embed
    Retriever -. embeds query .-> Embed
    Planner -. LLM call .-> Chat
    Analyst -. LLM call .-> Chat
    Policy -.->|routing data| Router
    Runner -. scores .-> Chat
```

## 🏗️ Project Structure

```
financial-agentic-platform/
├── data/
│   └── documents/             # 📥 Drop folder — auto-ingested on startup
├── src/
│   ├── agents/
│   │   ├── financial_agent.py # Entry point — runs the multi-agent graph
│   │   ├── graph.py           # LangGraph workflow (planner → retriever → analyst)
│   │   ├── router.py          # Model router (complexity → fast/strong model)
│   │   ├── retrieval.py       # Rewrite / multi-query / HyDE / rerank helpers
│   │   ├── llm.py             # Shared Ollama (ChatOllama) factory
│   │   └── vector_store.py    # pgvector-backed chunk/embedding store
│   ├── ingestion/
│   │   ├── loaders.py         # Path → text extraction (PDF/DOCX/XLSX/…)
│   │   └── pipeline.py        # Folder scan + upsert into pgvector
│   ├── storage/
│   │   ├── db.py              # psycopg connection + schema bootstrap
│   │   └── embeddings.py      # Ollama embeddings factory
│   └── ui/
│       └── app.py             # Streamlit chat + upload interface
├── evals/                     # ⚖️ Model evals + router policy
│   ├── dataset.py             # Curated financial queries + key points
│   ├── judge.py               # LLM-as-judge (1–5)
│   ├── metrics.py             # Coverage + latency aggregation
│   ├── run_evals.py           # Runner → results/ + policy.json
│   └── results/               # summary.md, policy.json, results_<ts>.json
├── requirements.txt
└── .env.example
```

## 🛠️ Technology Stack

- **UI** — Streamlit (streamed answers, ↑/↓ history recall, model + routing controls)
- **AI/ML** — Ollama (local chat + embedding models), LangChain, LangGraph
- **Agents** — planner → retriever → analyst graph + data-driven model router
- **Retrieval** — hybrid dense + full-text search (RRF), conversational rewrite;
  optional multi-query / HyDE / LLM rerank (env-toggled)
- **Storage** — Postgres + pgvector (HNSW cosine + GIN full-text indexes), psycopg3
- **Evals** — key-point coverage + LLM-as-judge + latency → `policy.json`
