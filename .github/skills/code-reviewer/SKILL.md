---
name: code-reviewer
description: 'Structured code review with explicit OWASP Top 10 security pass. Use when reviewing diffs, PRs, or files for correctness, readability, architecture, security, and performance — especially when the change touches authentication, input handling, queries, deserialization, file I/O, secrets, dependencies, or HTTP surfaces. Pairs with the code-reviewer agent.'
---

# Code Reviewer Skill

Companion procedure for the [code-reviewer](../../agents/code-reviewer.md) agent.
The agent file defines the five-dimension review framework and output template;
this skill adds the procedural steps and the OWASP Top 10 security checklist
that turns "look at security" into a concrete pass.

## When to Use

- Reviewing uncommitted changes (`git diff`), a staged PR, or a specific file
- Pre-merge sign-off on changes that touch any of:
  - User input boundaries (HTTP handlers, CLI args, form parsers, file uploads)
  - Authentication, authorization, session, or token handling
  - SQL, NoSQL, ORM, shell, or template rendering
  - Deserialization (`pickle`, `yaml.load`, `eval`, JSON → object)
  - File system paths, archive extraction, redirects, URL construction
  - Cryptography, password storage, secret handling
  - Dependency bumps or new third-party packages

Skip this skill for cosmetic-only diffs (formatting, comments, docs).

## Procedure

1. **Scope the change.** Run `git status` and `git diff --stat` to see what
   moved. For a focused review, name the files; for a sweep, take the full
   diff.
2. **Read tests first.** Tests document intent and coverage. Note what is
   tested, what isn't, and whether the new behavior is verified.
3. **Read the code in dependency order.** Config → data layer → business
   logic → presentation. Skim, then deep-read the files with the most
   non-trivial changes.
4. **Run the five-dimension framework** from
   [code-reviewer.md](../../agents/code-reviewer.md): correctness,
   readability, architecture, security, performance.
5. **Run the OWASP pass** using [references/owasp-top-10.md](./references/owasp-top-10.md).
   For each of the 10 categories, ask: *does anything in this diff touch
   this category?* If yes, apply the "What to look for" checklist for that
   item. Record findings inline with severity.
6. **Categorize every finding** as Critical / Important / Suggestion per
   the agent's output template, with file:line links and a concrete fix.
7. **Emit the review** using the template in
   [code-reviewer.md](../../agents/code-reviewer.md). Always include at
   least one "What's done well" item.

## Reference

- [references/owasp-top-10.md](./references/owasp-top-10.md) — 2021 OWASP
  Top 10, with what-to-look-for cues and code-level mitigations.

## Anti-patterns

- **Pasting the whole OWASP list into the review.** Only call out items the
  diff actually touches.
- **Severity inflation.** "Critical" means broken behavior, data loss, or
  exploitable vulnerability — not "I would have written it differently".
- **Findings without fixes.** Every Critical and Important must include a
  one-line concrete fix recommendation.
- **Skipping praise.** "What's done well" is required; specific praise
  reinforces good patterns.
