"""Multi-agent financial analysis workflow built on LangGraph.

A lean agentic graph tuned for fast local inference. Specialized agents
collaborate to route, retrieve, and answer:

    START
      │
      ▼
   🧭 Planner ──(general)──────────────┐
      │ (document)                     │
      ▼                                ▼
   🔎 Retriever ─────────────────▶ ✍️ Analyst ──▶ ✅ Finalize → END

Agents
  • Planner   — routes the request on two axes: (1) does it need the user's
                uploaded documents, and (2) is it SIMPLE or COMPLEX (used by the
                model router). Both come from a single classification call.
  • Retriever — a tool node; pulls the most relevant chunks from the VectorStore.
  • Analyst   — writes the answer, grounded in retrieved context when present.
                The model router picks which model writes it (fast vs strong).
"""
import os
from typing import Dict, List, Optional, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

from .llm import build_llm
from .vector_store import VectorStore
from . import retrieval
from . import router


def _emit(msg: str) -> str:
    """Append-and-print helper: prints the step to stdout (so it shows up in the
    server logs) and returns the message so it can also be stored in the trace."""
    print(msg, flush=True)
    return msg


def analyst_prompt(query: str, context: str = "") -> str:
    """Build the analyst's prompt, grounded in retrieved context if present.

    Module-level (pure) so the eval harness can reproduce the exact prompt the
    app uses without constructing the graph or touching Postgres.
    """
    parts = [
        "You are an expert financial analyst assistant. Answer the user's "
        "request directly, clearly, and professionally.",
    ]
    if context:
        parts.append(
            "Base your answer ONLY on the document content below. Quote and "
            "cite specific details (numbers, names, sections) from it. Do not "
            "claim you lack access — the relevant content is provided here:\n\n"
            f"=== DOCUMENT CONTENT ===\n{context}\n=== END DOCUMENT CONTENT ==="
        )
    else:
        parts.append(
            "No specific document content was retrieved for this request, so "
            "answer using your general financial expertise. Be clear that the "
            "answer is not drawn from an uploaded document."
        )
    parts.append(f"USER REQUEST: {query}")
    return "\n\n".join(parts)


# Words that strongly imply the user is referring to their uploaded files.
# Used as a safety net so the Planner never skips retrieval for an obvious
# document question (small local models route imperfectly).
_DOCUMENT_HINTS = (
    "document", "doc", "file", "upload", "uploaded", "resume", "cv",
    "report", "statement", "prospectus", "pdf", "spreadsheet", "attachment",
    "summary", "summarize", "extract", "the text",
)

# Words that imply the request needs heavier reasoning → route to the strong
# model. Backstop only; the planner's own classification is primary.
_COMPLEX_HINTS = (
    "analyze", "analyse", "compare", "comparison", "forecast", "project",
    "calculate", "compute", "model", "scenario", "stress test", "explain why",
    "evaluate", "assess", "derive", "optimize", "optimise", "trade-off",
    "tradeoff", "implication", "strategy", "recommend", "versus", " vs ",
)


class AgentState(TypedDict, total=False):
    """Shared state passed between agent nodes."""
    query: str
    search_query: str       # query after conversational rewrite (if any)
    history: List[Dict]     # prior chat turns: [{role, content}, ...]
    filters: Dict           # optional metadata filters for retrieval
    route: str              # "document" | "general"
    complexity: str         # "simple" | "complex" (drives the model router)
    analyst_model: str      # model chosen to write the answer
    documents: List[Dict]
    context: str
    analysis: str
    answer: str
    log: List[str]          # human-readable trace of what each agent did


class FinancialGraph:
    """Compiles and runs the multi-agent LangGraph workflow."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        self.use_router = router.router_enabled()
        # Per-model analyst clients, built on demand and reused across queries.
        self._analyst_cache: Dict[str, object] = {}
        self._build_llms()
        # The compiled graph holds bound methods that read self.*_llm at call
        # time, so swapping models later doesn't require recompiling.
        self.app = self._build()

    def _build_llms(self) -> None:
        # The planner is a tiny classifier — keep it on the fast model when the
        # router is active so routing never costs strong-model latency.
        planner_model = router.fast_model() if self.use_router else self.model
        self.planner_llm = build_llm(num_predict=24, temperature=0.0, model=planner_model)
        # Default analyst (used when the router is off). num_predict is kept
        # modest so a single answer can't run away on slow CPU inference.
        self.analyst_llm = build_llm(num_predict=700, temperature=0.7, model=self.model)

    def set_model(self, model: str) -> None:
        """Switch the manual model in place (used when routing is off). Keeps the
        vector store and any indexed documents."""
        if model and model != self.model:
            self.model = model
            self._build_llms()

    def set_router(self, enabled: bool) -> None:
        """Toggle automatic model routing. Rebuilds the planner so it sits on the
        fast model while routing is on."""
        enabled = bool(enabled)
        if enabled != self.use_router:
            self.use_router = enabled
            self._build_llms()

    # ----------------------------------------------------------------- helpers
    @staticmethod
    def _ask(llm, prompt: str) -> str:
        resp = llm.invoke([HumanMessage(content=prompt)])
        return resp.content if hasattr(resp, "content") else str(resp)

    def _analyst_for(self, model: str):
        """Return a cached analyst ChatOllama for the given model name."""
        if not self.use_router and model == self.model:
            return self.analyst_llm
        llm = self._analyst_cache.get(model)
        if llm is None:
            llm = build_llm(num_predict=700, temperature=0.7, model=model)
            self._analyst_cache[model] = llm
        return llm

    def _route_analyst_model(self, state: AgentState) -> str:
        """Pick the model that writes the answer for this query."""
        if self.use_router:
            return router.pick_model(state.get("complexity") or "simple")
        return self.model

    def warmup(self) -> None:
        """Load the (planner/fast) model into memory with a tiny generation so the
        first real query doesn't pay the cold-start cost. The strong model loads
        lazily on the first complex query."""
        try:
            self.planner_llm.invoke([HumanMessage(content="ok")])
        except Exception as e:
            print(f"⚠️ Model warmup skipped: {e}", flush=True)

    # ------------------------------------------------------------------- agents
    def planner_node(self, state: AgentState) -> AgentState:
        """Route the query on two axes: documents needed? and simple vs complex?"""
        query = state["query"]
        history = state.get("history") or []
        _emit(f"\n=== 🧠 Multi-agent run | query: {query!r} ===")

        # Conversational rewrite (cheap, default on) — used for BOTH routing
        # and retrieval so a follow-up like "what about Q2?" routes correctly.
        search_query = query
        if retrieval.enabled_rewrite() and history:
            rewritten = retrieval.rewrite_conversational(
                query, history, self.planner_llm)
            if rewritten and rewritten.strip().lower() != query.strip().lower():
                search_query = rewritten
                _emit(f"🪄 Rewrite → {search_query!r}")

        prompt = (
            "You are a routing agent in a financial analysis system.\n"
            "Classify the user's request on two axes and reply with EXACTLY two "
            "words separated by a space, nothing else:\n"
            "  axis 1: DOCUMENT (needs the user's uploaded documents) or GENERAL "
            "(answerable from general financial knowledge)\n"
            "  axis 2: SIMPLE (a definition or short factual answer) or COMPLEX "
            "(needs multi-step reasoning, calculation, comparison, or analysis)\n"
            "Example replies: 'GENERAL SIMPLE' or 'DOCUMENT COMPLEX'.\n\n"
            f"User request: {search_query}\n\nAnswer:"
        )
        raw = self._ask(self.planner_llm, prompt).strip().upper()
        route = "document" if "DOCUMENT" in raw else "general"
        complexity = "complex" if "COMPLEX" in raw else "simple"

        q_lower = search_query.lower()

        # Safety net: obvious document questions always retrieve, and if the
        # store actually holds documents we lean towards grounding the answer.
        has_docs = self._document_count() > 0
        if any(hint in q_lower for hint in _DOCUMENT_HINTS) and has_docs:
            route = "document"

        # Backstop: long or clearly analytical questions are treated as complex
        # even if the small planner labelled them simple.
        if complexity == "simple" and (
            len(search_query.split()) > 30
            or any(hint in q_lower for hint in _COMPLEX_HINTS)
        ):
            complexity = "complex"

        log = state.get("log", []) + [
            _emit(f"🧭 Planner → route: {route.upper()} | complexity: {complexity.upper()}")
        ]
        return {"route": route, "complexity": complexity,
                "search_query": search_query, "log": log}

    def retrieve_node(self, state: AgentState) -> AgentState:
        """Tool node: fetch relevant chunks from the vector store.

        Pipeline:
          1. (optional) multi-query expansion + HyDE — widens the search.
          2. Hybrid (dense + sparse) retrieval via ``vector_store.search_documents``.
          3. (optional) LLM rerank — reorders the top-N for precision.
        Toggles live in ``.env`` (see :mod:`retrieval`); defaults keep the
        added LLM calls off so retrieval stays fast on CPU.
        """
        query = state.get("search_query") or state["query"]
        filters = state.get("filters") or None
        k = int(os.getenv("RETRIEVAL_K", "6"))
        fetch_k = int(os.getenv("RETRIEVAL_FETCH_K", "20"))
        mode = os.getenv("RETRIEVAL_MODE", "hybrid").lower()
        log = state.get("log", [])

        try:
            if retrieval.enabled_multi_query() or retrieval.enabled_hyde():
                # Over-fetch through multiple query variants, then fuse.
                results = retrieval.multi_query_search(
                    query, self.vector_store, self.planner_llm,
                    k=k if not retrieval.enabled_rerank() else fetch_k,
                    fetch_k=fetch_k, mode=mode, filters=filters,
                )
            else:
                # Single-query retrieval; over-fetch only when reranking.
                results = self.vector_store.search_documents(
                    query,
                    k=fetch_k if retrieval.enabled_rerank() else k,
                    mode=mode, filters=filters,
                )

            if retrieval.enabled_rerank() and results:
                before = len(results)
                results = retrieval.rerank_llm(
                    query, results, self.planner_llm, top_k=k)
                log = log + [_emit(f"🎯 Rerank → kept top {len(results)} of {before}")]
        except Exception as e:  # vector store failure shouldn't kill the graph
            results = []
            log = log + [_emit(f"🔎 Retriever error: {e}")]

        # De-duplicate on the first 100 chars of content.
        seen, unique = set(), []
        for r in results:
            key = hash(r.get("content", "")[:100])
            if key not in seen:
                seen.add(key)
                unique.append(r)

        if unique:
            blocks = []
            for i, r in enumerate(unique, 1):
                fname = r.get("metadata", {}).get("filename", f"Document {i}")
                score = r.get("relevance_score", 0)
                blocks.append(
                    f"[Source {i}: {fname} | relevance {score:.2f}]\n{r.get('content', '')}"
                )
            context = "\n\n".join(blocks)
            log = log + [_emit(
                f"🔎 Retriever ({mode}) → {len(unique)} relevant chunk(s) found")]
        else:
            context = ""
            total = self._document_count()
            if total == 0:
                log = log + [_emit("🔎 Retriever → no documents uploaded yet")]
            else:
                log = log + [_emit(f"🔎 Retriever → no relevant content in {total} chunk(s)")]

        return {"documents": unique, "context": context, "log": log}

    def _analyst_prompt(self, state: AgentState) -> str:
        """Instance shim around the module-level :func:`analyst_prompt`."""
        return analyst_prompt(state["query"], state.get("context", ""))

    def _analyst_log(self, state: AgentState, model: str) -> List[str]:
        log = state.get("log", [])
        if self.use_router:
            log = log + [_emit(
                f"🧭 Router → {(state.get('complexity') or 'simple').upper()} → {model}")]
        return log + [_emit("✍️ Analyst → drafted answer")]

    def analyst_node(self, state: AgentState) -> AgentState:
        """Write the answer with the routed model, grounded in context when present."""
        model = self._route_analyst_model(state)
        analysis = self._ask(self._analyst_for(model), self._analyst_prompt(state))
        return {"analysis": analysis, "analyst_model": model,
                "log": self._analyst_log(state, model)}

    def finalize_node(self, state: AgentState) -> AgentState:
        return {"answer": state.get("analysis", ""),
                "log": state.get("log", []) + [_emit("✅ Finalized answer")]}

    # ------------------------------------------------------------- conditionals
    @staticmethod
    def _after_plan(state: AgentState) -> str:
        return "retrieve" if state.get("route") == "document" else "analyst"

    # -------------------------------------------------------------------- build
    def _build(self):
        g = StateGraph(AgentState)
        g.add_node("planner", self.planner_node)
        g.add_node("retrieve", self.retrieve_node)
        g.add_node("analyst", self.analyst_node)
        g.add_node("finalize", self.finalize_node)

        g.set_entry_point("planner")
        g.add_conditional_edges("planner", self._after_plan,
                                {"retrieve": "retrieve", "analyst": "analyst"})
        g.add_edge("retrieve", "analyst")
        g.add_edge("analyst", "finalize")
        g.add_edge("finalize", END)
        return g.compile()

    # ---------------------------------------------------------------------- run
    def _document_count(self) -> int:
        return self.vector_store.chunk_count()

    def run(self, query: str, on_token=None,
            history: Optional[List[Dict]] = None,
            filters: Optional[Dict] = None) -> AgentState:
        """Execute the multi-agent workflow for one query.

        Args:
            query: the user's request.
            on_token: optional callable invoked with each streamed token of the
                analyst's answer. When provided, the run is driven on the
                caller's thread via :meth:`stream_run` (see why below).
            history: prior chat turns ``[{role, content}, ...]`` used by the
                conversational rewrite step.
            filters: optional metadata filters (``filenames``, ``extensions``,
                ``source_path_like``) passed to the vector store.
        """
        if on_token is not None:
            return self.stream_run(query, on_token, history=history, filters=filters)
        return self.app.invoke({
            "query": query,
            "history": history or [],
            "filters": filters or {},
            "log": [],
        })

    def stream_run(self, query: str, on_token,
                   history: Optional[List[Dict]] = None,
                   filters: Optional[Dict] = None) -> AgentState:
        """Run planner → (retrieve) → analyst → finalize with the analyst's
        tokens streamed through ``on_token`` as they arrive.

        Why not the compiled graph? LangGraph executes nodes inside a worker
        thread pool, but Streamlit can only render from the main thread (calling
        st.* off-thread raises "missing ScriptRunContext" and silently drops the
        update). Driving the identical steps here, on the caller's thread, lets
        the live token callback reach the UI. The non-streaming path
        (:meth:`run` with no callback) still uses the compiled LangGraph.
        """
        state: AgentState = {
            "query": query,
            "history": history or [],
            "filters": filters or {},
            "log": [],
        }
        state.update(self.planner_node(state))
        if state.get("route") == "document":
            state.update(self.retrieve_node(state))

        model = self._route_analyst_model(state)
        pieces = []
        for chunk in self._analyst_for(model).stream(
                [HumanMessage(content=self._analyst_prompt(state))]):
            tok = chunk.content if hasattr(chunk, "content") else str(chunk)
            if tok:
                pieces.append(tok)
                on_token(tok)
        state["analysis"] = "".join(pieces)
        state["analyst_model"] = model
        state["log"] = self._analyst_log(state, model)

        state.update(self.finalize_node(state))
        return state
