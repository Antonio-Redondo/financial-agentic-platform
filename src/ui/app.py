import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sys
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# Make stdout/stderr UTF-8 so emoji log lines don't crash on Windows consoles
# (default cp1252 raises UnicodeEncodeError on 🧭/🔎/✍️ etc.)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.agents.financial_agent import FinancialAgent
from src.ingestion.pipeline import ingest_file, save_upload
from src import observability

load_dotenv()
# Honour the LANGSMITH_* env block now that .env is loaded; logs once whether
# traces will upload. Tracing itself is handled automatically by LangChain.
observability.configure()

st.set_page_config(
    page_title="Financial Agentic Platform | Prepayment Analytics",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Icons for the file-type chips in the sidebar.
FILE_ICONS = {
    "PDF": "📕",
    "DOC": "📘", "DOCX": "📘",
    "XLS": "📊", "XLSX": "📊", "CSV": "📊",
    "PPT": "📽️", "PPTX": "📽️",
    "TXT": "📝", "MD": "📝", "RTF": "📝",
    "HTML": "🌐", "HTM": "🌐", "XML": "🌐",
    "JSON": "🗂️",
}
SUPPORTED_TYPES = ["pdf", "docx", "doc", "txt", "rtf", "csv", "xlsx", "xls",
                   "pptx", "ppt", "html", "htm", "xml", "json", "md"]


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
def load_custom_css():
    """Light, theme-aware styling.

    Everything that needs a surface colour uses Streamlit's own theme custom
    properties (``--background-color`` / ``--secondary-background-color`` /
    ``--text-color``) so the UI stays legible in both the light and dark
    themes instead of painting hard-coded white cards that vanish on dark.
    """
    st.markdown(
        """
    <style>
    :root {
        --fa-accent: #2563eb;
        --fa-accent-soft: rgba(37, 99, 235, 0.12);
        --fa-border: rgba(128, 128, 128, 0.25);
    }

    /* Tighten the default top padding so the header sits up high. */
    .block-container { padding-top: 1.6rem; padding-bottom: 6rem; }

    /* App header band — its own coloured surface, so it reads on any theme. */
    .app-header {
        background: linear-gradient(120deg, #0f172a 0%, #1e3a8a 55%, #2563eb 100%);
        padding: 1.4rem 1.75rem;
        border-radius: 14px;
        margin-bottom: 1.25rem;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: 0 6px 24px rgba(15, 23, 42, 0.18);
    }
    .app-header .app-mark { font-size: 2.4rem; line-height: 1; }
    .app-header h1 { margin: 0; font-size: 1.55rem; font-weight: 700; letter-spacing: -0.01em; }
    .app-header p  { margin: 0.15rem 0 0 0; font-size: 0.95rem; opacity: 0.82; }

    /* Status pill used in the header. */
    .fa-pill {
        margin-left: auto;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.3rem 0.8rem;
        border-radius: 999px;
        background: rgba(248, 250, 252, 0.15);
        border: 1px solid rgba(248, 250, 252, 0.25);
        white-space: nowrap;
    }

    /* File chip in the sidebar (theme-aware surface). */
    .fa-chip {
        background: var(--secondary-background-color);
        border: 1px solid var(--fa-border);
        border-radius: 8px;
        padding: 0.5rem 0.7rem;
        margin: 0.3rem 0;
        font-size: 0.86rem;
    }
    .fa-chip small { opacity: 0.65; }
    .fa-chip.ok   { border-left: 3px solid #10b981; }
    .fa-chip.warn { border-left: 3px solid #f59e0b; }

    /* Primary buttons: flat, professional, subtle hover. */
    .stButton > button {
        border-radius: 9px;
        font-weight: 600;
        transition: transform 0.12s ease, box-shadow 0.12s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.22);
    }

    /* Chat bubbles a touch more padded. */
    .stChatMessage { padding-top: 0.25rem; padding-bottom: 0.25rem; }

    /* Hide default Streamlit chrome for a cleaner app feel. */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    </style>
    """,
        unsafe_allow_html=True,
    )


def create_header():
    agent = st.session_state.get("agent")
    if agent is None:
        pill = "⚠️ Agent offline"
    elif agent.use_router:
        pill = "🟢 Auto-routing on"
    else:
        pill = f"🟢 {agent.model}"
    st.markdown(
        f"""
    <div class="app-header">
        <span class="app-mark">🏦</span>
        <div>
            <h1>Financial Agentic Platform</h1>
            <p>Prepayment analytics &amp; risk assessment · multi-agent RAG</p>
        </div>
        <span class="fa-pill">{pill}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_metrics():
    """Compact KPI strip rendered in theme-aware bordered containers."""
    agent = st.session_state.get("agent")
    c1, c2, c3, c4 = st.columns(4)

    with c1, st.container(border=True):
        st.metric("📁 Documents", len(st.session_state.get("processed_docs", [])))

    with c2, st.container(border=True):
        if agent and agent.use_router:
            from src.agents import router as _router
            st.metric("🤖 Model", "Auto-route",
                      delta=f"{_router.fast_model()} ⇄ {_router.strong_model()}",
                      delta_color="off")
        else:
            model_label = agent.model if agent else os.getenv("OLLAMA_MODEL", "llama3.2:1b")
            st.metric("🤖 Model", model_label, delta="Manual", delta_color="off")

    with c3, st.container(border=True):
        st.metric("💬 Messages", len(st.session_state.get("messages", [])))

    with c4, st.container(border=True):
        if agent and agent.vector_store:
            try:
                stats = agent.get_document_stats()
                st.metric("🧩 Indexed chunks", stats["total_chunks"],
                          delta=f"{stats['unique_documents']} docs", delta_color="off")
            except Exception:
                st.metric("🧩 Indexed chunks", "—")
        else:
            st.metric("🧩 Indexed chunks", "—")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def get_available_models():
    """List models available from the local Ollama server (empty on failure)."""
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        import urllib.request
        with urllib.request.urlopen(f"{base}/api/tags", timeout=4) as r:
            data = json.loads(r.read().decode("utf-8"))
        return sorted(m["name"] for m in data.get("models", []))
    except Exception:
        return []


def model_selector():
    """Auto-routing toggle + manual model dropdown.

    When routing is on, the planner classifies each query (SIMPLE/COMPLEX) and
    the router picks the fast or strong model automatically. When off, every
    query uses the manually selected model. Either way, switching rebuilds only
    the LLM clients, so uploaded documents are kept.
    """
    agent = st.session_state.get("agent")
    routing_on = bool(agent and agent.use_router)

    new_routing = st.toggle(
        "Auto model routing",
        value=routing_on,
        help="On: a planner step labels each query SIMPLE or COMPLEX and routes "
             "it to the fast or strong model. Off: all queries use the model "
             "selected below.",
    )
    if agent and new_routing != routing_on:
        with st.spinner("Updating routing…"):
            agent.set_router(new_routing)
        st.rerun()

    if new_routing:
        from src.agents import router as _router
        st.caption(
            f"Simple → `{_router.fast_model()}`  ·  Complex → `{_router.strong_model()}`"
        )
        return

    current = agent.model if agent else os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    options = get_available_models()
    if current not in options:
        options = [current] + options  # always show the active model

    selected = st.selectbox(
        "Model",
        options,
        index=options.index(current),
        help="Pulled Ollama models. Smaller models are faster; larger ones give "
             "richer analysis. Switching keeps your uploaded documents.",
    )

    if selected != current and agent:
        with st.spinner(f"Loading {selected}…"):
            agent.set_model(selected)
            os.environ["OLLAMA_MODEL"] = selected  # keep the metric in sync
        st.success(f"Switched to {selected}")
        st.rerun()


def _file_chip(name: str, subtitle: str, status: str = ""):
    """Render a small theme-aware file row. status: '' | 'ok' | 'warn'."""
    ext = name.split(".")[-1].upper()
    icon = FILE_ICONS.get(ext, "📄")
    cls = f"fa-chip {status}".strip()
    st.markdown(
        f'<div class="{cls}">{icon} {name}<br><small>{subtitle}</small></div>',
        unsafe_allow_html=True,
    )


def sidebar_documents(agent):
    docs_dir = agent.documents_dir if agent else os.path.abspath("./data/documents")
    st.caption(
        "Files placed in the drop folder are auto-ingested into pgvector on "
        "startup. Uploads below land in the same folder."
    )
    st.code(docs_dir, language=None)

    if agent and st.button("🔄 Re-scan drop folder", width="stretch"):
        with st.spinner("Scanning + embedding new files…"):
            result = agent.rescan_documents()
        st.success(
            f"Scanned {result.scanned} · ingested {result.ingested} · "
            f"unchanged {result.skipped_unchanged} · empty {result.skipped_empty} · "
            f"errors {len(result.errors)}"
        )
        for err in result.errors[:5]:
            st.warning(err)

    st.divider()

    uploaded_files = st.file_uploader(
        "Upload documents",
        accept_multiple_files=True,
        type=SUPPORTED_TYPES,
        help="Supported: PDF, DOCX/DOC, XLSX/XLS, PPTX/PPT, TXT/RTF/MD, "
             "HTML/XML, CSV/JSON.",
    )

    if uploaded_files:
        for file in uploaded_files:
            size_kb = len(file.getvalue()) / 1024
            ext = file.name.split(".")[-1].upper()
            _file_chip(file.name, f"{ext} · {size_kb:.1f} KB")
        if st.button("🚀 Process documents", type="primary", width="stretch"):
            process_documents(uploaded_files)

    if st.session_state.get("processed_docs"):
        st.divider()
        st.markdown("**Processed this session**")
        for doc in st.session_state.processed_docs:
            indexed = doc.get("indexed", False)
            ext = doc["name"].split(".")[-1].upper()
            size_kb = doc["size"] / 1024
            detail = (f"Indexed · {doc.get('chunks_created', 0)} chunks"
                      if indexed else "Not indexed")
            _file_chip(doc["name"], f"{ext} · {detail} · {size_kb:.1f} KB",
                       status="ok" if indexed else "warn")


def sidebar_search(agent):
    """Document search tester, using a form so results survive reruns."""
    if not (agent and agent.vector_store):
        st.info("Vector store unavailable.")
        return

    with st.form("doc_search", clear_on_submit=False):
        query = st.text_input("Search indexed documents", value="financial")
        submitted = st.form_submit_button("🔍 Search", width="stretch")

    if submitted:
        try:
            results = agent.vector_store.search_documents(query, k=5)
            st.session_state["search_results"] = {"query": query, "results": results}
        except Exception as e:
            st.error(f"Search failed: {e}")
            st.session_state.pop("search_results", None)

    payload = st.session_state.get("search_results")
    if payload:
        results = payload["results"]
        if not results:
            st.warning(f"No matches for “{payload['query']}”.")
        else:
            st.success(f"{len(results)} chunk(s) for “{payload['query']}”")
            for i, r in enumerate(results, 1):
                src = r.get("metadata", {}).get("filename", "unknown")
                score = r.get("relevance_score", 0)
                with st.expander(f"{i}. {src} · relevance {score:.2f}"):
                    st.write(r.get("content", "")[:600])


def create_sidebar():
    agent = st.session_state.get("agent")
    with st.sidebar:
        st.markdown("## 🏦 Control Panel")
        if agent is None:
            st.error("Agent failed to start — check DATABASE_URL and Ollama.")

        tab_docs, tab_model, tab_search = st.tabs(["📁 Documents", "⚙️ Model", "🔍 Search"])

        with tab_docs:
            sidebar_documents(agent)

        with tab_model:
            model_selector()
            st.divider()
            st.selectbox(
                "Analysis focus",
                ["Comprehensive", "Prepayment Focus", "Risk Assessment", "Market Analysis"],
                key="analysis_type",
                help="Framing hint shown in the UI for this session.",
            )
            st.slider(
                "Confidence threshold", 0.5, 1.0, 0.8, 0.05,
                key="confidence_threshold",
                help="Minimum confidence level surfaced for predictions.",
            )
            st.divider()
            if observability.tracing_enabled():
                project = os.getenv("LANGSMITH_PROJECT", "default")
                st.caption(f"🔭 LangSmith tracing **on** · project `{project}`")
            else:
                st.caption("🔭 LangSmith tracing off — enable it in `.env` "
                           "(`LANGSMITH_TRACING=true`).")

        with tab_search:
            sidebar_search(agent)

        st.divider()
        if st.button("🧹 Clear conversation", width="stretch"):
            st.session_state.messages = []
            st.session_state.pop("search_results", None)
            st.session_state.pop("suggestions", None)
            st.session_state.pop("suggestions_sig", None)
            st.rerun()
        st.caption("Chat history persists for the duration of this session.")


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------
def process_documents(uploaded_files):
    """Process uploaded documents and save them to the vector database."""
    agent = st.session_state.agent
    vector_store = agent.vector_store if agent else None
    if vector_store is None:
        st.error("Vector store unavailable — check your DATABASE_URL.")
        return

    progress = st.progress(0.0, text="Starting…")

    for i, file in enumerate(uploaded_files):
        progress.progress(i / len(uploaded_files), text=f"Saving {file.name}…")
        try:
            saved_path = save_upload(file, folder=agent.documents_dir)
            progress.progress(i / len(uploaded_files), text=f"Embedding {file.name}…")
            chunks = ingest_file(vector_store, saved_path)

            if not chunks:
                st.info(f"{file.name} already up-to-date (no new chunks).")
            else:
                st.success(f"{file.name} → {chunks} chunk(s) embedded.")

            st.session_state.processed_docs.append({
                "name": file.name,
                "size": len(file.getvalue()),
                "processed_at": datetime.now(),
                "source_path": saved_path,
                "indexed": True,
                "chunks_created": chunks or 0,
                "content": f"Saved to {saved_path}",
            })
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")
            print(f"❌ Error processing {file.name}: {e}")

    progress.progress(1.0, text="All uploads processed.")
    progress.empty()


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
def render_message(msg: dict):
    """Render one stored chat message, including its reasoning trace if any."""
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        meta = msg.get("meta")
        if meta:
            bits = []
            if meta.get("model"):
                bits.append(f"model `{meta['model']}`")
            if meta.get("route"):
                bits.append(f"route `{meta['route']}`")
            if meta.get("complexity"):
                bits.append(f"complexity `{meta['complexity']}`")
            if meta.get("time"):
                bits.append(meta["time"])
            trace = meta.get("trace") or []
            label = "🧠 Reasoning trace" + (f" · {len(trace)} steps" if trace else "")
            with st.expander(label):
                if bits:
                    st.caption(" · ".join(bits))
                if trace:
                    for i, step in enumerate(trace, 1):
                        st.markdown(f"{i}. {step}")
                else:
                    st.caption("No trace recorded for this turn.")


def handle_prompt(prompt: str):
    """Stream an answer for a freshly submitted prompt and store the result."""
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)
    render_message(user_msg)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        streamed = {"text": ""}

        def on_token(tok):
            streamed["text"] += tok
            placeholder.markdown(streamed["text"] + " ▌")

        try:
            # Prior turns (excluding the just-appended user message) let the
            # conversational rewrite resolve follow-up phrasing. The spinner
            # gives an animated "thinking" cue until the answer is ready, while
            # tokens stream live into the placeholder underneath it.
            history = st.session_state.messages[:-1]
            with st.spinner("🧭 Analyzing your question…"):
                response = st.session_state.agent.process_query(
                    prompt, on_token=on_token, history=history)

            answer = response.get("output", "No response generated")
            placeholder.markdown(answer)

            assistant_msg = {
                "role": "assistant",
                "content": answer,
                "meta": {
                    "trace": response.get("trace", []),
                    "model": response.get("analyst_model"),
                    "route": response.get("route"),
                    "complexity": response.get("complexity"),
                    "time": datetime.now().strftime("%H:%M:%S"),
                },
            }
            st.session_state.messages.append(assistant_msg)

            if response.get("data"):
                create_data_visualization(response["data"])

        except Exception as e:
            error = f"❌ I hit an error while processing your request: {e}"
            placeholder.markdown(error)
            st.session_state.messages.append({"role": "assistant", "content": error})


def render_suggestions(agent):
    """Render dynamically generated follow-up questions as clickable buttons.

    Suggestions are produced by the agent from the indexed document chunks plus
    the user's recent questions, and cached against a (chunk_count, #questions)
    signature so they refresh when documents are added or the conversation
    advances — without an LLM call on every rerun. Clicking one submits it
    through the same path as typing.
    """
    if agent is None:
        return

    try:
        chunk_sig = agent.get_document_stats().get("total_chunks", 0)
    except Exception:
        chunk_sig = 0
    n_user = sum(1 for m in st.session_state.messages if m["role"] == "user")
    sig = (chunk_sig, n_user)

    if st.session_state.get("suggestions_sig") != sig:
        st.session_state.suggestions = agent.suggest_questions(
            history=st.session_state.messages, n=4)
        st.session_state.suggestions_sig = sig

    suggestions = st.session_state.get("suggestions") or []
    if not suggestions:
        return

    head = st.columns([6, 1])
    head[0].caption("💡 Suggested questions")
    if head[1].button("🔄", key="sugg_refresh", help="Regenerate suggestions"):
        st.session_state.pop("suggestions_sig", None)
        st.rerun()

    for row_start in range(0, len(suggestions), 2):
        cols = st.columns(2)
        for offset, col in enumerate(cols):
            idx = row_start + offset
            if idx >= len(suggestions):
                break
            if col.button(suggestions[idx], key=f"sugg_{idx}", width="stretch"):
                st.session_state.pending_prompt = suggestions[idx]
                st.rerun()


def create_chat_interface():
    agent = st.session_state.agent
    # A suggestion-button click queues its text here for processing this run.
    pending = st.session_state.pop("pending_prompt", None)

    if not st.session_state.messages and not pending:
        st.info("👋 Ask me anything about financial analysis and prepayment "
                "forecasting. Upload documents in the sidebar to ground answers "
                "in your own data.")

    for msg in st.session_state.messages:
        render_message(msg)

    # Show suggestions only when we're not about to process a queued click.
    if not pending:
        render_suggestions(agent)

    typed = st.chat_input("Ask about prepayment, risk, or your documents…")
    prompt = typed or pending
    if prompt:
        if agent is None:
            st.error("Agent is offline — cannot process queries.")
        else:
            handle_prompt(prompt)
            st.rerun()

    inject_history_navigation()


def create_data_visualization(data):
    """Render visualisations for any structured data returned by the agent."""
    if isinstance(data, dict) and data:
        st.markdown("#### 📊 Analysis results")
        if "chart_data" in data:
            st.line_chart(pd.DataFrame(data["chart_data"]))
        if "metrics" in data:
            st.table(pd.DataFrame(data["metrics"]))
        if "summary" in data:
            st.write(data["summary"])
    elif isinstance(data, list) and data:
        st.markdown("#### 📊 Analysis results")
        st.table(pd.DataFrame(data))


def inject_history_navigation():
    """Terminal-style ↑/↓ recall of previously sent questions in the chat box.

    Streamlit's chat_input has no built-in history, so this injects a small
    client-side script: pressing ArrowUp (when the cursor is at the start of
    the box) walks back through the questions you've already sent, ArrowDown
    walks forward, and going past the newest one clears the box.
    """
    history = [m["content"] for m in st.session_state.get("messages", [])
               if m["role"] == "user"]
    if not history:
        return

    components.html(
        f"""
        <script>
        (function() {{
            const w = window.parent;
            const hist = {json.dumps(history)};
            w.__chatHist = hist;
            if (w.__chatHistLen !== hist.length) {{
                w.__chatHistIdx = hist.length;
                w.__chatHistLen = hist.length;
            }}
            const doc = w.document;
            const getInput = () =>
                doc.querySelector('[data-testid="stChatInput"] textarea')
                || doc.querySelector('textarea');
            function setVal(ta, text) {{
                const setter = Object.getOwnPropertyDescriptor(
                    w.HTMLTextAreaElement.prototype, 'value').set;
                setter.call(ta, text);
                ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                ta.focus();
                setTimeout(() => {{ ta.selectionStart = ta.selectionEnd = ta.value.length; }}, 0);
            }}
            function bind(ta) {{
                if (ta.dataset.histBound) return;
                ta.dataset.histBound = '1';
                ta.addEventListener('keydown', function(e) {{
                    const h = w.__chatHist || [];
                    if (!h.length) return;
                    if (e.key === 'ArrowUp' && ta.selectionStart === 0) {{
                        if (w.__chatHistIdx > 0) {{
                            w.__chatHistIdx--;
                            setVal(ta, h[w.__chatHistIdx]);
                            e.preventDefault();
                        }}
                    }} else if (e.key === 'ArrowDown' && ta.selectionStart === ta.value.length) {{
                        if (w.__chatHistIdx < h.length - 1) {{
                            w.__chatHistIdx++;
                            setVal(ta, h[w.__chatHistIdx]);
                        }} else {{
                            w.__chatHistIdx = h.length;
                            setVal(ta, '');
                        }}
                        e.preventDefault();
                    }}
                }});
            }}
            let tries = 0;
            const timer = setInterval(function() {{
                const ta = getInput();
                if (ta) bind(ta);
                if (ta || ++tries > 40) clearInterval(timer);
            }}, 100);
        }})();
        </script>
        """,
        height=0,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = FinancialAgent()
            print("✅ FinancialAgent initialized successfully")
            result = getattr(st.session_state.agent, "last_ingestion", None)
            if result and (result.ingested or result.errors):
                st.toast(
                    f"📥 Startup ingestion: {result.ingested} new file(s), "
                    f"{result.skipped_unchanged} unchanged, "
                    f"{len(result.errors)} error(s)."
                )
        except Exception as e:
            st.error(f"Failed to initialize agent: {e}")
            st.session_state.agent = None
    if "processed_docs" not in st.session_state:
        st.session_state.processed_docs = []


def main():
    load_custom_css()
    initialize_session_state()

    create_header()

    # Reserve the metrics slot, but fill it after the sidebar + chat have run so
    # the counts reflect this run's state (a just-processed doc / new message).
    metrics_placeholder = st.empty()

    create_sidebar()
    create_chat_interface()

    with metrics_placeholder.container():
        render_metrics()

    st.divider()
    st.caption("🏦 Financial Agentic Platform · powered by Ollama (local LLM) · built with Streamlit")


if __name__ == "__main__":
    main()
