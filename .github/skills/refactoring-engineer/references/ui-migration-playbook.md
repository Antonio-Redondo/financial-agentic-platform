# UI Migration Playbook

Patterns for porting a UI from one framework to another while keeping
the app live and the users unaware. Use during the **UI migration** mode
of the `refactoring-engineer` agent.

## Frameworks this playbook covers

| Source | Target | Notes |
|---|---|---|
| React | Angular | Different paradigms (hooks ↔ DI + RxJS). Slowest of the four pairs. |
| Angular | React | Lose DI; gain hooks. State management decision needed up front. |
| Vue 2 | Vue 3 | Strictly speaking a version upgrade — use the official `vue-migrate` first. |
| jQuery / vanilla JS | Any modern framework | Start with router + a single route. Strangler-fig works best here. |
| Streamlit (Python) | React / Angular / Svelte SPA | Backend split required first (see "Streamlit → SPA" below). |
| Server-rendered (Django / Rails templates) | SPA + JSON API | Add API endpoints alongside; swap views one at a time. |

## Three Patterns

### 1. Strangler-fig (default)

Run source and target apps **side by side** behind one URL. A thin
reverse proxy (or the host framework's catch-all route) sends each path
to whichever app currently owns it. Each migrated route flips one entry
in the routing table.

```
            ┌──────────────┐
   user ──▶ │  reverse     │ ──▶ /  /pricing  /about         (source)
            │  proxy /     │ ──▶ /dashboard  /settings/*     (target)
            │  router      │
            └──────────────┘
```

**When to use:** larger app, can't pause feature work, want to validate
the target framework on a few routes before committing.

**When NOT to use:** the app is a SPA with one HTML shell — there's
nowhere to split traffic. Use component-by-component instead.

### 2. Component-by-component (inside one SPA)

Mount target-framework components inside the source app (or vice
versa). React-in-Angular and Angular-in-React both have official
bridges (`react-from-angular`, `@angular/elements`). Replace one leaf
component at a time; work upward.

```
   AppShell (source framework)
      ├── Header (source)
      ├── Sidebar (source)
      └── MainView
            ├── Toolbar (source)
            └── ChartPanel ← ported to target framework first
                  └── Tooltip ← ported next
```

**When to use:** single SPA, no proxy, fast iteration cycle.

**When NOT to use:** the source framework has no embed story for the
target (rare in 2026 — most pairs have one).

### 3. Parallel implementation

Build the target app to feature parity in a separate repo / route /
build pipeline. Flip a feature flag or DNS entry at the end.

**When to use:** the source is so coupled to its framework that
in-place replacement is impossible (jQuery spaghetti, deeply
template-driven server apps with no API).

**When NOT to use:** anywhere else. This is the most expensive pattern
and the highest-risk cutover.

## Parity Check Toolkit

Set these up **before** porting anything. They are the safety net.

| Tool / approach | What it catches |
|---|---|
| Visual snapshot diff (Playwright / Cypress / Percy) | Layout, copy, colors, icon positions. |
| DOM snapshot diff | Semantics, accessibility tree, form names. |
| Cypress / Playwright user-flow tests | Click-throughs (login → main action → logout). |
| Lighthouse / axe-core (run both apps) | Don't regress accessibility or CWV during the port. |
| Same backend, both UIs | Eliminates "did the API change?" as a confound. |

Capture baselines on the source app. Diff the target against them per
component / per route.

## Streamlit → SPA (Python backend → JS frontend)

A special case: Streamlit conflates UI and Python execution. You can't
"port a Streamlit page to Angular" because the page IS Python that
renders widgets.

**Required first step — split the backend.**

1. Stand up a FastAPI / Flask / Django REST layer that exposes every
   Streamlit-driven action as an endpoint (`POST /query`,
   `GET /documents`, `POST /upload`).
2. Make the existing Streamlit UI call those endpoints (instead of
   importing the Python directly). Streamlit still runs, but now it's
   a thin client.
3. **Verify parity** at this step — the app should behave identically
   when Streamlit calls the API as when it imported the Python.
4. **Now** build the SPA against the same API. The SPA replaces
   Streamlit at the same parity bar.

This is the cleanest migration path. Trying to translate Streamlit
widget calls directly into React components without the API step always
ends in pain — Streamlit's rerun-on-every-interaction model has no
analog in the target.

For the local-only Streamlit app in this repo specifically: any SPA
migration would need to ship the FastAPI layer first, with parity
checks against the current Streamlit UI's reasoning trace and document
search.

## React ↔ Angular Specifics

Hard parts when porting React → Angular:

- **Hooks → DI + RxJS.** `useState` is fine in Angular signals (16+);
  `useEffect` cleanup maps awkwardly to `ngOnDestroy`.
- **Context → providers.** Many small Contexts in React become one
  module-level provider in Angular.
- **Conditional rendering.** `{flag && <X />}` → `@if (flag) { ... }`
  (Angular 17+ control flow) or `*ngIf="flag"`.
- **CSS scoping.** React relies on convention (CSS modules / styled
  components); Angular has `ViewEncapsulation` built in. Decide once
  globally; do not mix.

Hard parts when porting Angular → React:

- **Lose DI as a first-class concept.** Replace with React Context
  (small scope) or a state library (Redux / Zustand / Jotai). Pick
  ONE.
- **Template directives → JSX expressions.** Most are one-to-one;
  `*ngFor` → `.map`, `*ngIf` → `&&`/ternary.
- **Modules go away.** Group files by feature folder; no `NgModule`.
- **RxJS is optional.** Don't bring it over by default; only keep
  observables where the data is genuinely streaming.

## Stage-by-stage example: React → Angular

For a 12-route SPA, a realistic plan:

| Stage | What | Parity check |
|---|---|---|
| 0 | Stand up Angular shell at `/v2/*`. | Renders blank Angular app at `/v2/`. |
| 1 | Reverse proxy routes `/v2/*` to Angular, everything else to React. | Old app unchanged at root. |
| 2 | Port the simplest route (read-only "About"). | Snapshot diff vs. React route. |
| 3 | Port the second simplest. | Same. |
| 4-N | Continue, one route per stage. | Same. |
| N+1 | All routes ported. Flip default to Angular at the proxy. | Full user-flow tests pass on Angular. |
| N+2 | Delete React source. | Build still green. |

Each stage is one commit. Each stage can be reverted on its own.

## Anti-patterns

- **Porting the architecture, not the UX.** "Angular wants modules so
  I'll create one per page" — sometimes; sometimes that's
  over-engineering. Match the target's idioms but not its bureaucracy.
- **Rewriting state management mid-port.** Keep the source's
  state-management mental model during the port; revisit after.
- **Renaming during a port.** `UserCard` → `UserCardComponent` is a
  rename; do it in a separate commit before or after, never during.
- **Skipping the API split for Streamlit / Rails / Django.** It looks
  faster to "just port the templates" — it's not.
- **Migrating styling at the same time.** Tailwind → Bootstrap, CSS
  modules → styled-components, etc., are their own ports.
