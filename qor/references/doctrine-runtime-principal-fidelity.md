# Doctrine: Runtime-principal fidelity + Data-API access-control

**Phase 121; GH #177.** Home for the terms *runtime-principal fidelity* and
*Data-API access-control lint*. Progressive-disclosure target for the short
steps in `qor-substantiate` (Step 4 + Step 4.6.10) and `qor-audit` (Security Pass).

## Root cause

A governance false-PASS class: the verifying principal has more privilege than
the runtime caller, so a test exercises a path that does not exist for real
users. Concretely, on a Postgres/Supabase Data API:

- Tests construct the client with the **service-role key**, or call a
  `SECURITY DEFINER` RPC that runs as the table owner. Both bypass row-level
  security (RLS) and table-level `GRANT`s.
- The feature reads/writes a table that is `REVOKE`d from `authenticated`, or a
  newly-created table that never received its Data-API `GRANT` (the platform
  removed the legacy automatic grant for new tables).
- The suite passes; the authenticated/anon caller hits `42501` in production.

`qor-substantiate` returned PASS on code broken for its real caller. This
doctrine closes that surface.

## Runtime-principal fidelity (the term)

**runtime-principal fidelity** — the property that a feature's access path is
proven under the principal that actually calls it at runtime (`authenticated` /
`anon`), not only under a privileged principal (`service_role`, or a
`SECURITY DEFINER` function running as owner).

### Acceptance question (qor-substantiate Step 4 gate)

For any feature whose acceptance includes a DB read/write reachable by a
non-privileged caller: *"Is there at least one test or assertion that exercises
this path under the real caller role?"* If the path is proven **only** under
`service_role` / a `SECURITY DEFINER` RPC, the seal ABORTs — **unless** the
operator records an explicit coverage-gap note in the seal entry
(the disclosed-skip):

> data path verified only under service_role; authenticated/RLS path deferred to
> manual QA

and emits a `gate_skipped_prerequisite_absent`-style shadow event. A
service-role-only proof must not *silently* satisfy a path used by authenticated
callers. Fail-closed with a disclosed escape, not WARN-only.

## Data-API access-control lint (the term)

**Data-API access-control lint** — `qor.scripts.data_api_acl_lint`, a static
scan over a target repo's SQL migrations, invoked fail-closed at
`qor-substantiate` Step 4.6.10 (`|| ABORT`). It runs against the implemented
SQL, not a live database.

### Finding kinds

| kind | blocking? | meaning | escape |
|---|---|---|---|
| `missing-grant` | yes | a `CREATE TABLE` in an API-exposed schema with no `GRANT` to `authenticated`/`anon`, no `REVOKE ... FROM authenticated/anon`, and no escape comment | `-- qor:service-role-only` on/above the `CREATE TABLE`, or an explicit `REVOKE` |
| `definer-view` | yes | a view in an API schema created without `security_invoker = true` (Postgres default is definer-rights, which bypasses base-table RLS for any reader) | `-- qor:definer-view-intended reason: ...` on/above the `CREATE VIEW` |
| `security-definer-fn` | no (advisory) | a `SECURITY DEFINER` function — surfaced for review (these are often legitimate) | n/a (review, not block) |

When no migration files are found, the lint records a Phase 75 disclosed-skip
(`SKIP:` line, exit 0) rather than failing — non-Postgres / unseeded repos are
out of scope by construction.

### Postgres `security_invoker` citation

Postgres 15+ supports `CREATE VIEW ... WITH (security_invoker = true)`, which
makes the view run with the *querying* user's privileges (so base-table RLS
applies). The default (`security_invoker = false`) runs the view with the
*view owner's* privileges, bypassing base-table RLS for any reader. See the
PostgreSQL `CREATE VIEW` reference
(https://www.postgresql.org/docs/current/sql-createview.html,
"security_invoker"). The lint is a static text scan and does not depend on a
live database to evaluate this option.

## Where each check lives (substantiate vs audit)

GH #177 frames the grant/view checklist under `qor-audit` (remediation B). But
`qor-audit` reviews the **plan/blueprint pre-implementation**, when the SQL
migrations do not yet exist; the implemented SQL exists at **seal time**.
Therefore:

- **`qor-substantiate`** carries the deterministic executable lint (Step 4.6.10,
  fail-closed over real migrations) **and** the runtime-principal fidelity
  acceptance gate (Step 4).
- **`qor-audit`** carries the plan-level checklist (prompt-contract): the
  auditor confirms the plan commits to `GRANT`s for any API-exposed table it
  introduces, flags `SECURITY DEFINER` functions and definer-rights views over
  RLS tables, and treats a service-role-client test for an authenticated-caller
  feature as insufficient proof. Any plan-level violation → VETO.

De-complecting: detection of implemented reality (substantiate, deterministic)
is separated from review of declared intent (audit, judgment).
