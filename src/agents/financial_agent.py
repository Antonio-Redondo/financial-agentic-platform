from typing import Dict, List, Optional
from dotenv import load_dotenv

from .vector_store import VectorStore
from .graph import FinancialGraph
from . import semantic_cache
from ..ingestion.pipeline import documents_dir, ingest_folder
from ..guardrails import get_guardrails

load_dotenv()


class FinancialAgent:
    """Entry point that runs the multi-agent LangGraph workflow.

    Keeps the same public interface the Streamlit UI expects
    (``process_query``, ``vector_store``, ``get_document_stats``)
    while delegating the actual reasoning to a multi-agent graph
    (planner → retriever → analyst).

    On construction it also walks the ``DOCUMENTS_DIR`` folder (default
    ``./data/documents``) and ingests any new or changed files into pgvector,
    so dropping a file into that folder and restarting the app is enough to
    make it available to the retriever.
    """

    def __init__(self):
        self.vector_store = VectorStore()
        self.graph = FinancialGraph(self.vector_store)
        self.guardrails = get_guardrails()
        self.cache = semantic_cache.get_cache()
        # Ingest anything sitting in the drop folder before serving queries.
        try:
            self.last_ingestion = ingest_folder(self.vector_store)
        except Exception as e:  # noqa: BLE001 — never block startup on ingest
            print(f"⚠️  Startup ingestion skipped: {e}", flush=True)
            self.last_ingestion = None
        # Preload the model so the first query doesn't pay the cold-start cost.
        self.graph.warmup()

    @property
    def model(self) -> str:
        """The Ollama model currently in use (manual mode / routing off)."""
        return self.graph.model

    @property
    def use_router(self) -> bool:
        """Whether automatic model routing is enabled."""
        return self.graph.use_router

    def set_router(self, enabled: bool) -> None:
        """Enable/disable automatic model routing, then warm up the planner."""
        self.graph.set_router(enabled)
        self.graph.warmup()

    @property
    def documents_dir(self) -> str:
        return documents_dir()

    def rescan_documents(self):
        """Re-run the folder ingestion (for the sidebar's manual trigger)."""
        self.last_ingestion = ingest_folder(self.vector_store)
        # New/changed chunks can change answers → drop cached responses.
        self.cache.clear()
        return self.last_ingestion

    def _redact_history(self, history: Optional[List[Dict]]) -> Optional[List[Dict]]:
        """PII-redact chat-history turns before they reach the rewrite model.

        Assistant turns are already output-redacted, but user turns are stored
        raw in the UI session — scrub them so the conversational rewrite (and
        any trace of it) never carries raw PII."""
        if not history:
            return history
        out = []
        for m in history:
            content = m.get("content", "")
            out.append({**m, "content": self.guardrails.redact_for_prompt(content)})
        return out

    def _cache_namespace(self) -> str:
        """Scope cached answers so they self-invalidate when a cached answer
        would become wrong: on model/router change, or when the corpus changes
        (chunk count moves as documents are added / removed / re-chunked)."""
        model_part = "router" if self.use_router else self.model
        try:
            corpus = self.vector_store.chunk_count()
        except Exception:  # noqa: BLE001
            corpus = "na"
        return f"{model_part}|{corpus}"

    def set_model(self, model: str) -> None:
        """Switch the active model in place (uploaded documents are preserved),
        then warm it up so the next query is fast."""
        self.graph.set_model(model)
        self.graph.warmup()

    def process_query(self, query: str, on_token=None,
                      history: Optional[List[Dict]] = None,
                      filters: Optional[Dict] = None) -> Dict:
        """Process a user query through the multi-agent graph.

        Args:
            query: the user's request.
            on_token: optional callable invoked with each streamed answer token.
            history: prior chat turns ``[{role, content}, ...]`` so the
                conversational rewrite can resolve follow-ups.
            filters: optional metadata filters forwarded to the retriever.
        """
        # Input guardrail (LLM01/LLM10): reject over-long input and, when
        # configured to block, instruction-override / jailbreak attempts before
        # any model is invoked.
        decision = self.guardrails.check_input(query)
        for note in decision.notes:
            print(f"🛡️ Input guardrail → {note}", flush=True)
        if not decision.allowed:
            return {
                "output": decision.reason,
                "trace": [f"🛡️ Blocked by guardrails: {n}" for n in decision.notes],
                "blocked": True,
            }

        # Prompt-bound PII redaction (default on): scrub the query and chat
        # history BEFORE they reach any model call, the embedder, or the cache —
        # so the planner/analyst/rewrite never see raw PII and nothing raw is
        # sent to an off-machine trace. Toggle with GUARDRAILS_PII_REDACT_PROMPTS.
        query = self.guardrails.redact_for_prompt(query)
        history = self._redact_history(history)

        # Semantic response cache. Only used for standalone questions: a
        # follow-up (history) is rewritten using the conversation, and filters
        # change retrieval, so the query text alone wouldn't identify the same
        # answer in those cases.
        cacheable = not history and not filters
        namespace = self._cache_namespace()
        if cacheable:
            hit = self.cache.get(query, namespace)
            if hit is not None:
                sim = hit.get("cache_similarity")
                print(f"⚡ Cache hit ({hit.get('cache_kind')}, sim={sim}) for "
                      f"{self.guardrails.scrub_for_log(query)!r}", flush=True)
                if on_token:           # paint the answer into the live area
                    on_token(hit["output"])
                hit["trace"] = [f"⚡ Served from semantic cache "
                                f"({hit.get('cache_kind')} match, "
                                f"similarity {sim})"] + (hit.get("trace") or [])
                return hit

        try:
            result = self.graph.run(query, on_token=on_token,
                                    history=history, filters=filters)
            answer = (result.get("answer")
                      or result.get("analysis")
                      or "No analysis available.")
            response = {
                "output": answer,
                "trace": result.get("log", []),
                "route": result.get("route"),
                "complexity": result.get("complexity"),
                "analyst_model": result.get("analyst_model"),
                "search_query": result.get("search_query"),
                "cached": False,
            }
            if cacheable:
                self.cache.put(query, response, namespace)
            return response
        except Exception as e:
            return {
                "output": (
                    "I'm currently experiencing technical difficulties. "
                    f"Please try again later. Error: {str(e)}"
                ),
                "trace": [],
            }

    def suggest_questions(self, history: Optional[List[Dict]] = None,
                          n: int = 4) -> List[str]:
        """Propose follow-up questions grounded in the indexed documents and the
        user's recent questions.

        Args:
            history: prior chat turns ``[{role, content}, ...]``; only the
                user turns are used as recent-question context.
            n: how many suggestions to return.
        """
        queries = [m.get("content", "") for m in (history or [])
                   if m.get("role") == "user"]
        try:
            return self.graph.suggest_questions(queries, n=n)
        except Exception as e:  # noqa: BLE001 — suggestions are best-effort
            print(f"⚠️ suggest_questions failed: {e}", flush=True)
            return []

    def get_document_stats(self) -> Dict:
        """Get statistics about indexed documents."""
        return {
            "total_chunks": self.vector_store.chunk_count(),
            "unique_documents": len(self.vector_store.unique_filenames()),
            "storage_type": "pgvector",
        }
