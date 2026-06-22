---
name: refactoring-engineer
description: 'Step-by-step procedure for three kinds of code work: behavior-preserving in-place refactors; UI framework migrations (React ↔ Angular, Vue, Svelte, Streamlit → SPA); and backend language/version upgrades (Python, Java, Node, .NET). Picks the right playbook based on the mode you''re in, then walks the stage-by-stage plan with parity checks. Pairs with the refactoring-engineer agent.'
---

# Refactoring & Modernization Skill

Companion procedure for the [refactoring-engineer](../../agents/refactoring-engineer.md) agent.
The agent file defines responsibilities and the output template; this
skill adds the decision tree, the per-mode runbook, and links to the
specialty playbooks.

## When to Use

- "Clean this function up" / "this module is hard to read" → **in-place**.
- "Port the UI to Angular" / "replace Streamlit with React" → **UI migration**.
- "Bump us to Python 3.12" / "Java 8 to 17" / "Node 16 to 20" → **backend upgrade**.

Skip this skill for:
- Bug fixes (behavior changes — out of scope).
- New features or new tests (those have their own agents).
- Security / performance / retrieval reviews (specialist agents).

## Decision Tree

```
Is the target the SAME framework + SAME language version?
  │
  ├── YES → IN-PLACE REFACTOR
  │         → references/refactoring-catalog.md
  │
  └── NO → Is the framework / runtime changing?
              │
              ├── UI framework changes (React/Angular/Vue/Svelte/Streamlit)
              │   → UI MIGRATION
              │   → references/ui-migration-playbook.md
              │
              └── Language version or backend runtime changes
                  → BACKEND UPGRADE
                  → references/backend-modernization-playbook.md
```

If you're not sure which mode applies, ask the user — one short
question — before touching code.

## Procedure — In-place refactor

1. **Pin the smell** in one sentence.
2. **Confirm test coverage** for the target. No coverage → ask
   `test-engineer` first or pick another target.
3. **Snapshot green** — record baseline test result.
4. **Pick the smallest fix** from
   [references/refactoring-catalog.md](./references/refactoring-catalog.md).
5. **Apply, re-run, verify.** Same pass/xfail counts, or revert.
6. **Emit the report** using the agent's template.

## Procedure — UI migration

1. **Inventory** routes, screens, components, shared state, data
   fetching, external assets.
2. **Choose a target pattern** from
   [references/ui-migration-playbook.md](./references/ui-migration-playbook.md):
   strangler-fig, component-by-component, parallel implementation.
3. **Set up parity checks** before porting anything — visual snapshots
   or DOM diffs per screen.
4. **Port one component / screen at a time.** Compile, render, snapshot
   diff, ship.
5. **Repeat** until every route is on the target framework and the
   source app can be retired.
6. **Retire the source app** in its own commit.
7. **Emit the report.**

## Procedure — Backend upgrade

1. **Capture current version** and the target version. Note runtime,
   compiler, dependency manager.
2. **Run the official upgrade tool first.** It does the mechanical 80%:
   `pyupgrade`, `2to3`, OpenRewrite, Modernizer, `nx migrate`,
   `dotnet-upgrade-assistant`.
3. **List deprecations** from a dry-run on the new runtime. Fix each in
   its own commit.
4. **Update dependencies** that block the upgrade — minimum bumps only,
   no opportunistic ones.
5. **Run the test suite** on the new runtime per stage. Same pass count
   or revert.
6. **Capture before/after deprecation warning counts** and performance
   delta.
7. **Emit the report.**

## Cross-cutting guardrails

These rules hold across all three modes:

- **One stage per patch.** A small green commit beats a large maybe.
- **Use the automated tool first.** Hand edits are for what the tool
  couldn't do.
- **Don't rename and migrate in the same diff.** Names change in their
  own pass.
- **Don't add dependencies you don't need.** Each new library is a
  future migration cost.
- **Don't drive-by reformat.** Unrelated whitespace in a refactor commit
  hides the actual change.
- **Don't touch generated files.** Build output, lock files (unless
  the upgrade itself requires it), and machine-written configs are
  derivatives, not source.

## References

- [references/refactoring-catalog.md](./references/refactoring-catalog.md)
  — in-place Python refactors with before/after.
- [references/ui-migration-playbook.md](./references/ui-migration-playbook.md)
  — strangler-fig and component-by-component patterns for
  React ↔ Angular, Vue, Svelte, and Streamlit → SPA.
- [references/backend-modernization-playbook.md](./references/backend-modernization-playbook.md)
  — Python, Java, Node, and .NET version upgrades with the canonical
  tool per ecosystem.

## Anti-patterns

- **Big-bang migrations.** A 5,000-line "port everything" diff is a
  rewrite, not a migration.
- **Refactoring during a port.** Resist the urge to clean up while
  porting. Port first under existing names; refactor later as an
  in-place pass on the target.
- **Skipping parity checks.** Without a snapshot, "looks the same to me"
  is wishful thinking.
- **Upgrading two majors at once.** Python 3.8 → 3.12 in one step
  hides which version introduced which break. Go 3.8 → 3.10 → 3.12.
- **Manual transforms when a codemod exists.** OpenRewrite, `pyupgrade`,
  `@angular/cli ng update`, and `codemod` exist for a reason.
- **Mixing migration with features.** "While I'm porting we'll also add
  auth" — no. Split.
