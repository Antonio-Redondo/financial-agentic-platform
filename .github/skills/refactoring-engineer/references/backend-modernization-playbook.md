# Backend Modernization Playbook

Patterns for upgrading a backend language version or runtime without
breaking external contracts. Use during the **backend upgrade** mode of
the `refactoring-engineer` agent.

## Stacks this playbook covers

| Source | Target | Canonical tool |
|---|---|---|
| Python 3.8 / 3.9 / 3.10 | Python 3.11 / 3.12 / 3.13 | `pyupgrade`, `ruff --fix`, `pip-tools` |
| Python 2.x | Python 3.x | `2to3`, then `pyupgrade`. **Don't.** End-of-life since 2020; treat as a parallel rewrite. |
| Java 8 / 11 | Java 17 / 21 | OpenRewrite, `jdeprscan`, Error Prone, IntelliJ Modernize |
| Node 16 / 18 | Node 20 / 22 LTS | `npm-check-updates`, `eslint --fix`, dependency-cruiser |
| .NET Framework 4.x | .NET 6 / 8 | `dotnet-upgrade-assistant`, `try-convert` |
| Ruby 2.7 | Ruby 3.x | RuboCop, Rails app:update if Rails |
| Go 1.x | Go 1.y | `go fix`, `go mod tidy` |

## Universal Procedure

### Step 1 — Capture the baseline

- Current language / runtime version.
- Target language / runtime version.
- Dependency list with current pins.
- Test suite result on the current runtime.
- Deprecation warnings on the current runtime.

### Step 2 — Pick the smallest hop

Never skip more than one major. Go 3.8 → 3.10 → 3.12, not 3.8 → 3.12.
Each hop is its own work item with its own test pass.

| Source | Recommended next hop |
|---|---|
| Python 3.8 | 3.10 (then 3.12) |
| Python 3.9 | 3.11 |
| Java 8 | 17 (LTS to LTS) |
| Java 11 | 17 or 21 (LTS to LTS) |
| Node 16 | 20 LTS |
| .NET Framework 4.8 | .NET 8 (skip .NET 5/6/7) |

### Step 3 — Run the automated upgrade tool

Per ecosystem:

```powershell
# Python
.\.venv\Scripts\python.exe -m pip install pyupgrade ruff
pyupgrade --py312-plus (Get-ChildItem -Recurse -Filter *.py | % FullName)
ruff check --select UP --fix .
```

```bash
# Java (Maven)
mvn org.openrewrite.maven:rewrite-maven-plugin:run \
  -Drewrite.activeRecipes=org.openrewrite.java.migrate.UpgradeToJava17

# Java (deprecation report)
jdeprscan --release 17 path/to/classes
```

```bash
# Node
npx npm-check-updates -u
npm install
npm test
```

```powershell
# .NET
dotnet tool install -g upgrade-assistant
upgrade-assistant upgrade <path-to-csproj>
```

The tool does the mechanical 80%. Don't review its output line-by-line;
just run the test suite and review what fails.

### Step 4 — Resolve remaining deprecations

Run the new runtime against the test suite. Anything that prints a
deprecation warning is a finding. Fix one deprecation per commit.

### Step 5 — Update dependencies that block the upgrade

Minimum bumps only. Don't bring everything to latest "while you're
here" — that's a separate work item and a separate set of risks.

### Step 6 — Verify

- Test suite passes on the new runtime.
- Deprecation warning count: lower than baseline.
- Performance delta: within ±10% unless documented.
- External contracts unchanged: same HTTP responses, same CLI output,
  same data shapes.

### Step 7 — Report

Use the agent's output format. Include before/after counts of:

- Deprecation warnings.
- Lines of code touched (the automated-tool diff vs. your hand-edits).
- Test pass count.

## Python Specifics (this repo's primary language)

For a 3.11 → 3.12 / 3.13 hop in this codebase:

- Run `pyupgrade --py311-plus` (or `--py312-plus`) across `src/`,
  `tests/`, `evals/`. Auto-converts `Optional[X]` → `X | None`,
  `Dict[str, int]` → `dict[str, int]`, f-string `=` debug, etc.
- Run `ruff check --select UP,PYI --fix .` to catch what pyupgrade
  missed.
- Check `typing_extensions` usage — features back-ported there may be
  in `typing` now.
- `pkg_resources` and `distutils` are gone in 3.12. Use `importlib`
  and `packaging`.
- `asyncio.get_event_loop()` without a running loop raises a
  DeprecationWarning since 3.10, and is an error in 3.12+. Use
  `asyncio.get_running_loop()` inside coroutines, `asyncio.new_event_loop()`
  outside.
- The walrus operator `:=` (3.8+) and PEP 695 generic syntax (3.12+)
  are **optional** — adopting them is a refactor, not part of the
  upgrade.

## Java Specifics (8 → 17 / 21)

The four breakages that bite hardest:

1. **`javax.*` → `jakarta.*`** for Jakarta EE 9+ (Servlet, JPA, JMS,
   etc.). Spring 6 / Spring Boot 3 require this. OpenRewrite handles
   the bulk; hand-fix the imports it misses.
2. **Modules / JPMS warnings.** Reflective access across module
   boundaries needs `--add-opens` or proper module declarations. Cheap
   fix: add `--add-opens java.base/java.lang=ALL-UNNAMED` to JVM args
   while you migrate.
3. **`sun.*` removed.** `sun.misc.Unsafe`, `sun.security.*`, etc., are
   gone. Find replacements in `jdk.unsupported` or rewrite the call
   site.
4. **`SecurityManager` deprecated in 17, removed in 24.** Audit any
   code that uses it.

After the upgrade:

- Adopt records (Java 14+) where DTOs are immutable. Optional pass —
  not part of the upgrade.
- Adopt sealed classes (Java 17) for closed type hierarchies.
- Switch expressions (Java 14+) — fine, optional.

## Node Specifics (16 / 18 → 20 / 22)

- `npm` major versions ship with Node. Node 20 ships npm 10. Lock
  files may regenerate.
- ESM-only packages are increasingly common. If you're still on
  CommonJS, expect to either add `"type": "module"` in `package.json`
  or pin some deps to their last CJS major.
- `crypto.createCipher` (no IV) is **gone** in Node 22. Use
  `crypto.createCipheriv`.
- `domain` module — fully removed. Replace with `AsyncLocalStorage`.

## .NET Specifics (Framework → .NET 8)

- **`upgrade-assistant`** does the bulk of the project-file changes
  (`.csproj` SDK style, target framework, package references).
- `System.Web` (Web Forms, WebApi 2) has no .NET 8 equivalent. ASP.NET
  Core is required, which is itself a UI / framework migration
  (handle separately).
- `app.config` / `web.config` → `appsettings.json`. The tool ports
  most settings.
- `BinaryFormatter` is unsafe and unsupported. Replace with
  `System.Text.Json` or a vetted serializer.

## Cross-cutting Pitfalls

- **CI image bump first.** Don't migrate locally and discover CI
  doesn't have the runtime.
- **Dependency-floor lifts.** Bumping the language can force minimum
  versions on every framework you use. List them up front.
- **Performance surprises.** New GCs, new JITs, new event loops can
  swing benchmarks. Capture before / after for the hot paths.
- **String / encoding behavior changes.** Especially in Python 3.x
  hops (PEP 597 default encoding warnings) and Java (UTF-8 default in
  18+).
- **Test runner upgrade tangled with language upgrade.** pytest /
  JUnit / Mocha versions can themselves be the blocker. Update the
  runner first, in its own commit.

## Anti-patterns

- **Two majors in one hop.** You'll spend twice as long bisecting
  failures.
- **Skipping the automated tool.** Hand-converting `Optional[X]` to
  `X | None` across 200 files is a waste of human attention.
- **"While we're upgrading, let's also..."** Refactor / restructure /
  rewrite — no. Three separate work items.
- **Upgrading dependencies opportunistically.** Each dep bump is its
  own change. Only update what blocks the runtime upgrade.
- **Calling the runtime upgrade done at "tests pass".** Also resolve
  the deprecation warnings, or you've just deferred the next
  migration's pain.
