# OWASP Top 10 (2021) — Code Review Reference

Use this as a checklist during the security pass of a code review. For each
item: if any change in the diff touches this category, run the "What to look
for" cues and flag findings with concrete fixes. Items are listed in OWASP's
own ranking order.

Source: [OWASP Top 10:2021](https://owasp.org/Top10/).

---

## A01:2021 — Broken Access Control

Failures that let users act outside their intended permissions.

**What to look for**
- Endpoints / handlers / RPC methods that read or mutate data without an
  explicit authorization check.
- Authorization based on client-supplied identifiers (`user_id` in body,
  `?owner=` in query) instead of the authenticated principal.
- Missing checks on `PUT` / `PATCH` / `DELETE` while `GET` is checked.
- IDOR: `GET /orders/{id}` returns any order regardless of who owns it.
- "Force browsing": admin routes reachable without a role check.
- CORS configured with `Access-Control-Allow-Origin: *` on authenticated
  routes.
- JWTs accepted without verifying signature, `exp`, `aud`, or `iss`.

**Fix patterns**
- Deny by default; require an explicit allow check in every handler.
- Derive the actor from the session/token, never from request body.
- Centralize policy (a single `authorize(user, action, resource)` function)
  rather than scattering `if user.role == "admin"` checks.

## A02:2021 — Cryptographic Failures

Weak, missing, or misused cryptography that exposes data in transit or at
rest.

**What to look for**
- Secrets, tokens, or PII written to logs or error messages.
- Hardcoded keys, passwords, or connection strings in source.
- `http://` URLs for anything carrying credentials or PII.
- Passwords stored with `md5`, `sha1`, plain `sha256`, or no salt. Use
  `bcrypt`, `scrypt`, `argon2`.
- `random.random()` / `Math.random()` used for tokens, session IDs, or
  password resets. Use `secrets` / `crypto.randomBytes`.
- ECB mode, static IVs, or self-rolled crypto.
- TLS verification disabled (`verify=False`, `rejectUnauthorized: false`).

**Fix patterns**
- Use the platform's vetted crypto library; never implement primitives.
- Pull secrets from env vars or a secret manager; keep them out of git.
- Verify TLS certs everywhere; pin where appropriate.

## A03:2021 — Injection

User input concatenated into an interpreter (SQL, shell, LDAP, XPath,
templates, OS command).

**What to look for**
- String-built SQL: `f"SELECT * FROM users WHERE id = {user_id}"`.
- `subprocess.run(cmd, shell=True)` with user input.
- `os.system`, `eval`, `exec`, `Function(...)`.
- Server-side template rendering with user input as the template (SSTI):
  `Template(user_input).render(...)`.
- NoSQL queries built from request body without a schema check.
- LDAP / XML / XPath built by string concatenation.

**Fix patterns**
- Parameterized queries / prepared statements; never string-build SQL.
- `subprocess.run([...], shell=False)` with an argv list.
- Render user input *into* a template as data, never *as* the template.
- Validate against an allow-list when the value is structural (table name,
  column, sort order).

## A04:2021 — Insecure Design

The flaw is in the design, not the implementation — missing controls that
no amount of careful coding would catch.

**What to look for**
- No rate limiting on auth, password reset, OTP, or expensive endpoints.
- Account enumeration: login / reset reveals whether an email is registered.
- Sensitive flows missing a second factor or step-up auth.
- Trust boundaries assumed but not enforced (e.g., "internal" service
  exposed to the internet).
- Business logic that can be replayed, reordered, or skipped (e.g., charge
  step bypassable by skipping to confirmation).

**Fix patterns**
- Threat-model the feature before implementing it.
- Add rate limits and lockouts on identity-bearing endpoints.
- Generic error responses for auth / reset ("if an account exists, an
  email was sent").

## A05:2021 — Security Misconfiguration

Defaults left on, debug surfaces exposed, frameworks misconfigured.

**What to look for**
- `DEBUG=True` / verbose stack traces shipped to production.
- Default admin credentials, default API keys, sample data left in.
- Missing security headers: `Content-Security-Policy`,
  `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`,
  `Referrer-Policy`.
- Permissive CORS (`*` with credentials).
- Directory listing enabled on static servers.
- Cloud storage buckets / DBs left publicly readable.
- Containers running as root, with the docker socket mounted, or with
  unnecessary capabilities.

**Fix patterns**
- Separate config per environment; production overrides explicit.
- Lint / scan the deployment manifest, not just the code.
- Add a CSP early; tighten over time.

## A06:2021 — Vulnerable and Outdated Components

Known-vulnerable libraries, old runtimes, abandoned dependencies.

**What to look for**
- New dependencies added without justification.
- Pinned versions years behind upstream.
- Transitive deps with public advisories (`pip-audit`, `npm audit`,
  `osv-scanner`, GitHub Dependabot alerts).
- Runtime / framework versions past end-of-life (Python 2, Node 12,
  Django 2, etc.).
- Forks of unmaintained libraries vendored into the repo.

**Fix patterns**
- Run a dependency scanner in CI and gate on Critical/High findings.
- Prefer compatible-release pins (`~=1.4.0`) over loose ranges.
- Track an SBOM; review on every release.

## A07:2021 — Identification and Authentication Failures

Weak auth flows, session handling, or credential management.

**What to look for**
- Passwords compared with `==` instead of constant-time compare.
- Session IDs that don't rotate on login / privilege change.
- Long-lived tokens with no revocation path.
- Cookies missing `HttpOnly`, `Secure`, `SameSite`.
- "Remember me" tokens stored in plain text.
- Password policies that allow trivial passwords with no breached-password
  check.
- Brute-force protection missing on login / MFA.

**Fix patterns**
- Use the framework's vetted auth (Django auth, Devise, Spring Security,
  next-auth). Don't roll your own.
- Rotate session IDs on auth-state change.
- Constant-time compare for any secret-equality check.

## A08:2021 — Software and Data Integrity Failures

Trusting code or data without verifying it hasn't been tampered with.

**What to look for**
- Deserializing untrusted input with `pickle`, `yaml.load` (without
  `SafeLoader`), `unserialize`, Java native serialization.
- Auto-updaters / plugin loaders that fetch code over HTTP without
  signature check.
- CI/CD pulling unpinned actions / images (`actions/checkout@main`,
  `image: redis` instead of a digest).
- Webhook handlers that accept payloads without signature verification.
- `eval(json_string)` instead of `json.loads`.

**Fix patterns**
- `yaml.safe_load`, JSON, or a schema-validated format. Never `pickle`
  from the network.
- Pin every CI action to a SHA; verify image digests.
- Verify webhook HMAC signatures with a constant-time compare.

## A09:2021 — Security Logging and Monitoring Failures

Can't detect or investigate an incident because the events weren't logged.

**What to look for**
- Auth events (login, failed login, password change, MFA enroll) not
  logged.
- Logs missing actor / resource / outcome, or missing timestamps.
- Sensitive data (passwords, full tokens, full card numbers) written to
  logs — the opposite failure mode, but equally common.
- No alerting on repeated failures or privilege escalations.
- Logs stored only on the affected host (gone when the host is wiped).

**Fix patterns**
- Log `(timestamp, actor, action, resource, outcome, request_id)` for
  every security-relevant event.
- Redact secrets at the logger, not at the call site.
- Ship logs off the host; alert on the high-signal events.

## A10:2021 — Server-Side Request Forgery (SSRF)

The server fetches a URL the attacker controls, often reaching internal
networks.

**What to look for**
- Code that takes a URL from user input and calls
  `requests.get(url)` / `fetch(url)` / `urllib.request.urlopen(url)`.
- Webhook / preview / "import from URL" features.
- PDF / image / Office generators that fetch remote resources.
- File-upload features that follow redirects to internal addresses.

**Fix patterns**
- Allow-list destinations; reject by default.
- Resolve the hostname yourself and reject private / link-local / loopback
  ranges (`127.0.0.0/8`, `10/8`, `172.16/12`, `192.168/16`, `169.254/16`,
  `::1`, `fc00::/7`).
- Disable HTTP redirects, or re-validate the destination on every redirect
  hop.
- Use a dedicated egress proxy with allow-listing for outbound fetches.

---

## Quick Triage Heuristic

| Diff touches… | Run checklist for… |
|---|---|
| HTTP route, handler, RPC | A01, A07 |
| SQL, ORM, shell, template | A03 |
| Cookies, tokens, sessions, passwords | A02, A07 |
| File upload, path, archive, redirect | A01, A05, A10 |
| URL fetch from user input | A10 |
| Deserialization, plugin load, CI config | A08 |
| New dependency, version bump | A06 |
| New feature with auth / payment / data export | A04 |
| Config, Dockerfile, IaC | A05 |
| Logging, error handling | A02, A09 |
