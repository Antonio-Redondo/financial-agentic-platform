import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sys
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import time

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

load_dotenv()

# Enhanced page configuration
st.set_page_config(
    page_title="Financial Forecast AI | Prepayment Analytics",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
def load_custom_css():
    st.markdown("""
    <style>
    /* Main theme and background */
    .main {
        padding-top: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Metrics cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #3b82f6;
    }
    
    .user-message {
        background-color: #eff6ff;
        border-left-color: #3b82f6;
    }
    
    .assistant-message {
        background-color: #f0fdf4;
        border-left-color: #10b981;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8fafc;
    }
    
    /* Upload area styling */
    .upload-area {
        border: 2px dashed #cbd5e1;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8fafc;
        margin-bottom: 1rem;
    }
    
    /* Analysis results styling */
    .analysis-section {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Status indicators */
    .status-success {
        color: #10b981;
        font-weight: 600;
    }
    
    .status-warning {
        color: #f59e0b;
        font-weight: 600;
    }
    
    .status-error {
        color: #ef4444;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        border: none;
        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
        color: white;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def create_header():
    st.markdown("""
    <div class="main-header">
        <h1>🏦 Financial Forecast AI</h1>
        <p>Advanced Prepayment Analytics & Risk Assessment Platform</p>
    </div>
    """, unsafe_allow_html=True)

def create_metrics_dashboard():
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Documents Processed",
            value=len(st.session_state.get("processed_docs", [])),
            delta=None
        )
    
    with col2:
        agent = st.session_state.get("agent")
        if agent and agent.use_router:
            from src.agents import router as _router
            model_label = f"Auto: {_router.fast_model()} ⇄ {_router.strong_model()}"
            model_delta = "Model router · LangGraph"
        else:
            model_label = agent.model if agent else os.getenv("OLLAMA_MODEL", "llama3.2:1b")
            model_delta = "Multi-agent · LangGraph"
        st.metric(label="🤖 AI Model", value=model_label, delta=model_delta)
    
    with col3:
        st.metric(
            label="💬 Messages",
            value=len(st.session_state.get("messages", [])),
            delta=None
        )
    
    with col4:
        st.metric(
            label="🎯 Status",
            value="Ready",
            delta=None
        )

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

    new_routing = st.checkbox(
        "🧭 Auto model routing (fast ⇄ strong)",
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
        "🤖 Model",
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


def create_sidebar():
    with st.sidebar:
        st.markdown("### 📁 Document Management")

        # Auto-ingest folder controls — drop files here to have them indexed
        # into pgvector on next startup or "Re-scan" click.
        agent = st.session_state.get("agent")
        docs_dir = agent.documents_dir if agent else os.path.abspath("./data/documents")
        st.caption(
            "📂 Drop folder: `" + docs_dir + "`  \n"
            "Files placed here are auto-ingested into pgvector on startup."
        )
        if agent and st.button("🔄 Re-scan documents folder", use_container_width=True):
            with st.spinner("Scanning + embedding new files…"):
                result = agent.rescan_documents()
            st.success(
                f"Scanned {result.scanned} file(s) — ingested {result.ingested}, "
                f"unchanged {result.skipped_unchanged}, empty {result.skipped_empty}, "
                f"errors {len(result.errors)}"
            )
            for err in result.errors[:5]:
                st.warning(err)

        st.markdown("---")

        # Upload section with better styling
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "📄 Upload Financial Documents",
            accept_multiple_files=True,
            type=["pdf", "docx", "doc", "txt", "rtf", "csv", "xlsx", "xls", "pptx", "ppt", "html", "htm", "xml", "json", "md"],
            help="Uploads are saved into the drop folder above and ingested into pgvector. Supported: PDF, DOCX/DOC, XLSX/XLS, PPTX/PPT, TXT/RTF/MD, HTML/XML, CSV/JSON."
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_files:
            st.markdown("#### 📋 Uploaded Files")
            for i, file in enumerate(uploaded_files):
                file_size = len(file.getvalue()) / 1024  # KB
                file_extension = file.name.split('.')[-1].upper()
                
                # Choose icon based on file type
                if file_extension in ['PDF']:
                    icon = "📕"
                elif file_extension in ['DOCX', 'DOC']:
                    icon = "📘"
                elif file_extension in ['XLSX', 'XLS', 'CSV']:
                    icon = "📊"
                elif file_extension in ['PPTX', 'PPT']:
                    icon = "📽️"
                elif file_extension in ['TXT', 'MD', 'RTF']:
                    icon = "📝"
                elif file_extension in ['HTML', 'HTM', 'XML']:
                    icon = "🌐"
                elif file_extension in ['JSON']:
                    icon = "📋"
                else:
                    icon = "📄"
                
                st.markdown(f"""
                <div style="background: #f0fdf4; padding: 0.5rem; border-radius: 5px; margin: 0.25rem 0;">
                    {icon} {file.name}<br>
                    <small style="color: #6b7280;">Type: {file_extension} | Size: {file_size:.1f} KB</small>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("🚀 Process Documents", type="primary"):
                process_documents(uploaded_files)
        
        # Show processed documents status
        if st.session_state.get("processed_docs"):
            st.markdown("#### 📊 Processed Documents")
            for doc in st.session_state.processed_docs:
                icon = "✅" if doc.get("indexed", False) else "⚠️"
                chunks = doc.get("chunks_created", 0)
                file_ext = doc['name'].split('.')[-1].upper()
                
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 0.5rem; border-radius: 5px; margin: 0.25rem 0; border-left: 3px solid {'#10b981' if doc.get('indexed') else '#f59e0b'};">
                    {icon} {doc['name']}<br>
                    <small style="color: #6b7280;">
                        Type: {file_ext} | 
                        {'Indexed: ' + str(chunks) + ' chunks' if doc.get('indexed') else 'Not indexed'} | 
                        Size: {doc['size'] / 1024:.1f} KB | 
                        Content: {len(doc.get('content', '')):.0f} chars
                    </small>
                </div>
                """, unsafe_allow_html=True)
            
            # Add document search test
            if st.button("🔍 Test Document Search", help="Test if documents are searchable"):
                if st.session_state.agent and st.session_state.agent.vector_store:
                    try:
                        stats = st.session_state.agent.get_document_stats()
                        st.success(f"📊 Document Stats: {stats['total_chunks']} chunks from {stats['unique_documents']} documents in {stats['storage_type']} storage")
                        
                        # Show all documents info for debugging
                        if hasattr(st.session_state.agent.vector_store, 'get_all_documents_info'):
                            all_docs = st.session_state.agent.vector_store.get_all_documents_info()
                            if all_docs:
                                with st.expander("📋 All Stored Documents (Debug Info)"):
                                    for i, doc_info in enumerate(all_docs, 1):
                                        st.text(f"Document {i}:")
                                        st.text(f"  Filename: {doc_info.get('filename', 'unknown')}")
                                        st.text(f"  Content Length: {doc_info.get('content_length', 0)} chars")
                                        st.text(f"  Preview: {doc_info.get('content_preview', 'No preview')}")
                                        st.text("---")
                        
                        # Test search with user input
                        test_query = st.text_input("🔍 Test search query:", value="financial", help="Enter a word to search for in your documents")
                        if st.button("Search Documents"):
                            test_results = st.session_state.agent.vector_store.search_documents(test_query, k=5)
                            if test_results:
                                st.success(f"🔍 Search Test: Found {len(test_results)} relevant chunks for '{test_query}'")
                                with st.expander("Preview search results"):
                                    for i, result in enumerate(test_results, 1):
                                        st.text(f"Result {i} (Relevance: {result.get('relevance_score', 0):.2f}):")
                                        st.text(f"Source: {result.get('metadata', {}).get('filename', 'unknown')}")
                                        st.text(f"Content: {result.get('content', '')[:300]}...")
                                        st.text("---")
                            else:
                                st.warning(f"🔍 Search Test: No results found for '{test_query}' - documents may not contain this content")
                        
                    except Exception as e:
                        st.error(f"❌ Error testing document search: {str(e)}")
                else:
                    st.error("❌ Vector store not available")
        
        st.markdown("---")
        
        # Analysis options
        st.markdown("### ⚙️ Analysis Settings")

        model_selector()

        analysis_type = st.selectbox(
            "Analysis Type",
            ["Comprehensive", "Prepayment Focus", "Risk Assessment", "Market Analysis"],
            help="Choose the type of analysis to perform"
        )
        
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.5,
            max_value=1.0,
            value=0.8,
            step=0.05,
            help="Minimum confidence level for predictions"
        )
        
        st.markdown("---")
        
        # Analysis info
        st.markdown("### ℹ️ Session Info")
        st.info("� Chat history is automatically saved and will persist throughout your session.")

def process_documents(uploaded_files):
    """Process uploaded documents and save to vector database"""
    progress_bar = st.progress(0)
    status_text = st.empty()

    agent = st.session_state.agent
    vector_store = agent.vector_store if agent else None
    if vector_store is None:
        st.error("Vector store unavailable — check your DATABASE_URL.")
        return

    for i, file in enumerate(uploaded_files):
        status_text.text(f"Saving {file.name} to documents folder…")
        try:
            saved_path = save_upload(file, folder=agent.documents_dir)

            status_text.text(f"Embedding {file.name} into pgvector…")
            chunks = ingest_file(vector_store, saved_path)

            if chunks is None or chunks == 0:
                status_msg = (
                    f"ℹ️ {file.name} already up-to-date in pgvector "
                    "(no new chunks written)."
                )
            else:
                status_msg = (
                    f"✅ {file.name} → {chunks} chunk(s) embedded into pgvector "
                    f"(stored at `{saved_path}`)."
                )

            st.session_state.processed_docs.append({
                "name": file.name,
                "size": len(file.getvalue()),
                "processed_at": datetime.now(),
                "source_path": saved_path,
                "indexed": True,
                "chunks_created": chunks or 0,
                "content": f"Saved to {saved_path}",
            })

            progress_bar.progress((i + 1) / len(uploaded_files))
            st.success(status_msg)

        except Exception as e:
            error_msg = f"❌ Error processing {file.name}: {str(e)}"
            st.error(error_msg)
            print(error_msg)

    status_text.text("✅ All uploads processed.")
    time.sleep(2)
    status_text.empty()
    progress_bar.empty()

def inject_history_navigation():
    """Terminal-style ↑/↓ recall of previously sent questions in the chat box.

    Streamlit's chat_input has no built-in history, so this injects a small
    client-side script: pressing ArrowUp (when the cursor is at the start of
    the box) walks back through the questions you've already sent, ArrowDown
    walks forward, and going past the newest one clears the box. The questions
    themselves live in st.session_state.messages, so they persist for the
    whole session.
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
            // Reset the navigation cursor whenever the history grows/changes.
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


def create_chat_interface():
    """Enhanced chat interface with input at top"""
    st.markdown("### 💬 AI Financial Analyst")
    
    # Create a container for the input that stays at the top
    input_container = st.container()
    
    with input_container:
        st.markdown("#### ✍️ Ask Your Question")
        # Chat input at the top - always visible
        prompt = st.chat_input("Type your question here...", key="chat_input_top")
    
    # Separator
    st.markdown("---")
    
    # Process input immediately if provided
    if prompt:
        # Add user message to chat history and show it right away
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Stream the assistant's answer live as it is generated
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("🧭 Routing & retrieving…")
            streamed = {"text": ""}

            def on_token(tok):
                streamed["text"] += tok
                placeholder.markdown(streamed["text"] + " ▌")

            try:
                # Pass prior turns (excluding the user message just appended)
                # so the conversational rewrite can resolve follow-up phrasing.
                history = st.session_state.messages[:-1]
                response = st.session_state.agent.process_query(
                    prompt, on_token=on_token, history=history)

                # Build the multi-agent trace (so the pipeline is visible)
                trace = response.get("trace", [])
                trace_md = ""
                if trace:
                    steps = "\n".join(f"{i}. {step}" for i, step in enumerate(trace, 1))
                    trace_md = f"\n\n**🧠 Multi-agent trace**\n\n{steps}"

                # Format response with additional insights
                answered_model = response.get("analyst_model")
                model_note = f" · model: {answered_model}" if answered_model else ""
                formatted_response = f"""**Analysis Complete** ✅

{response.get("output", "No response generated")}
{trace_md}

---
*Answered by the multi-agent graph (planner → retriever → analyst){model_note} at {datetime.now().strftime("%H:%M:%S")}*"""

                # Replace the streamed text with the final formatted version
                placeholder.markdown(formatted_response)
                st.session_state.messages.append({"role": "assistant", "content": formatted_response})

                # Show additional visualizations if data is present
                if "data" in response and response["data"]:
                    create_data_visualization(response["data"])

            except Exception as e:
                error_response = f"❌ I encountered an error while processing your request: {str(e)}"
                placeholder.markdown(error_response)
                st.session_state.messages.append({"role": "assistant", "content": error_response})

        # Rerun to refresh the conversation history and metrics
        st.rerun()
    
    # Show conversation history below the input
    if st.session_state.messages:
        st.markdown("#### 🔄 Latest Conversation")
        
        # Show the last user message and AI response pair
        messages_to_show = st.session_state.messages[-2:] if len(st.session_state.messages) >= 2 else st.session_state.messages[-1:]
        
        for message in messages_to_show:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        st.markdown("---")
        
        # Show full conversation history in an expander
        if len(st.session_state.messages) > 2:
            with st.expander(f"📜 Full Conversation History ({len(st.session_state.messages)} messages)", expanded=False):
                for message in st.session_state.messages[:-2]:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
    else:
        st.info("👋 Welcome! Ask me anything about financial analysis and prepayment forecasting.")

    # Enable ↑/↓ recall of previously sent questions in the input box.
    inject_history_navigation()


def create_data_visualization(data):
    """Create visualizations for analysis data using Streamlit built-in charts"""
    if isinstance(data, dict) and data:
        st.markdown("### 📊 Analysis Results")
        
        # Display the actual data provided by the AI model
        if "chart_data" in data:
            st.markdown("#### 📈 Analysis Chart")
            chart_df = pd.DataFrame(data["chart_data"])
            st.line_chart(chart_df)
        
        if "metrics" in data:
            st.markdown("#### 📋 Key Metrics")
            metrics_df = pd.DataFrame(data["metrics"])
            st.table(metrics_df)
        
        if "summary" in data:
            st.markdown("#### 📄 Summary")
            st.write(data["summary"])
    
    elif isinstance(data, list) and data:
        st.markdown("### 📊 Analysis Results")
        st.markdown("#### 📋 Analysis Data")
        df = pd.DataFrame(data)
        st.table(df)

def initialize_session_state():
    """Initialize session state variables"""
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
            st.error(f"Failed to initialize agent: {str(e)}")
            st.session_state.agent = None
    if "processed_docs" not in st.session_state:
        st.session_state.processed_docs = []

def main():
    """Main application function"""
    load_custom_css()
    initialize_session_state()
    
    # Create header
    create_header()

    # Reserve the top spot for the live metrics, but fill it AFTER the chat and
    # sidebar have run this pass — otherwise the counts reflect last run's state
    # (e.g. a just-processed document or new message wouldn't show until the
    # next interaction).
    metrics_placeholder = st.empty()

    # Create main layout
    col1, col2 = st.columns([2, 1])

    with col1:
        create_chat_interface()

    with col2:
        create_sidebar()

    # Render the metrics now that session state is up to date for this run.
    with metrics_placeholder.container():
        create_metrics_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; padding: 1rem;">
        <small>🏦 Financial Forecast AI | Powered by Ollama (local LLM) | Built with Streamlit</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()