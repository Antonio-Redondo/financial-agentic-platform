---
name: security-auditor
description: 'Threat model and security review for this local RAG app. Use when reviewing changes that touch LLM prompts, user input handling, file uploads, the documents folder, the pgvector schema, the LangSmith integration, or any new external HTTP call. Covers prompt injection, data exfiltration via tool outputs, OWASP LLM Top 10, and the local-only trust boundary. Pairs with the security-auditor agent.'
---

# Security Auditor

Companion procedure for the [security-auditor](../../agents/security-auditor.md) agent.
This app is single-user and **local-only by design** — the threat model is
different from a multi-tenant web service. Spend audit budget where this
app actually has surface: LLM prompts, file ingestion, the one cloud edge
(LangSmith), and dependency hygiene.

## When to Use

- Code touches prompt construction, RAG context assembly, or chat input.
- New file types added to the ingestion pipeline, or file-handling code
  changes.
- New external HTTP call introduced (LangSmith, model registry, etc.).
- LangSmith config changes, or any code that handles `LANGSMITH_API_KEY`.
- New dependency or major version bump.
- Before publishing the repo or sharing a build.

## Trust Boundary

```
 ┌───── trusted ─────┐ ┌──────── untrusted ────────┐
 │  the operator     │ │  uploaded documents       │
 │  .env (secrets)   │ │  pasted chat messages     │
 │  policy.json      │ │  LLM outputs              │
 └───────────────────┘ │  external HTTP responses  │
                       └───────────────────────────┘
```

Anything to the right of the boundary can be attacker-controlled (a
poisoned PDF, a prompt-injection in chat, an Ollama response). Anything
to the left is operator config. **Treat LLM output as untrusted** — it
flows back into prompts (multi-query, rewrite, rerank) and into
suggestions.

## Procedure

1. **Map the change to the boundary.** Does it ingest, render, or echo
   anything from the untrusted side? If no, the audit is short.
2. **Run the OWASP LLM Top 10 pass** for changes that touch prompts,
   retrieval context, or tool surfaces — see
   [references/owasp-llm-top-10.md](./references/owasp-llm-top-10.md).
3. **Run the prompt-injection pass** for changes that build LLM prompts —
   see [references/prompt-injection-patterns.md](./references/prompt-injection-patterns.md).
4. **Check the local-only invariant.** Grep for new outbound HTTP calls:
   ```powershell
   git diff | Select-String -Pattern "requests\.|urlopen|httpx\.|fetch\("
   ```
   Anything new that isn't behind a `LANGSMITH_*` or `OLLAMA_BASE_URL` env
   gate is a finding.
5. **Check secret handling.** Grep for any new use of `LANGSMITH_API_KEY`
   or other secrets in logs, error messages, or `print` calls.
6. **Check the ingestion boundary.** New loaders must:
   - Use `os.path.basename` on uploaded filenames (path traversal — see
     [src/ingestion/pipeline.py](../../../src/ingestion/pipeline.py)
     `save_upload`).
   - Validate file size before parsing (zip-bomb / pathological PDF).
   - Catch and log loader exceptions instead of crashing ingestion.
7. **Emit findings** in the agent's format (Critical / Important /
   Suggestion) with file:line links and concrete fixes.

## What this app is **not** worried about

These categories often dominate web app reviews but don't apply here:

- **Broken access control** — no authn/authz layer; single local user.
- **Session management** — Streamlit `session_state` is per-process,
  per-user, in memory.
- **CSRF** — no authenticated endpoints.
- **XSS to other users** — single-user app; the only XSS impact is
  self-XSS (still worth fixing, just lower severity).

## What this app **is** worried about

- **Prompt injection** via uploaded docs, chat input, and LLM-on-LLM
  flows (multi-query, rerank, suggestion).
- **Document confidentiality** — when LangSmith is enabled, document
  content leaves the machine. Verify this is disclosed.
- **Local file system blast radius** — anything in the upload path can
  write to `data/documents/` (and beyond if path traversal isn't
  blocked).
- **Supply chain** — LangChain 1.x is recent; new transitive deps land
  on every minor bump.
- **DoS on yourself** — pathological PDFs / huge XLSX files locking the
  ingestion thread, runaway HyDE/rerank loops.

## References

- [references/owasp-llm-top-10.md](./references/owasp-llm-top-10.md) —
  LLM-specific OWASP Top 10 (different from the web Top 10 used by the
  code-reviewer skill).
- [references/prompt-injection-patterns.md](./references/prompt-injection-patterns.md)
  — payload patterns and mitigations specific to this RAG pipeline.

## Anti-patterns

- **Cargo-culting web findings.** Don't flag missing CSRF tokens or
  session timeouts — they don't exist in this threat model.
- **Severity inflation on self-XSS.** Important, not Critical, unless
  there's a real multi-user attack path.
- **Ignoring LLM output as a sink.** Suggestions, rewrites, and rerank
  scores are LLM-generated. Treat their text and structure as
  untrusted on the way back in.
