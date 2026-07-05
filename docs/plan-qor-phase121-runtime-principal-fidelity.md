# Plan: Runtime-principal fidelity + Data-API access-control enforcement

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: runtime-principal fidelity
  home: qor/references/doctrine-runtime-principal-fidelity.md
- term: Data-API access-control lint
  home: qor/references/doctrine-runtime-principal-fidelity.md

**boundaries**:
- limitations: The grant/view lint is a static SQL scan (regex over migration files), not a live database probe. It detects the deterministic high-confidence cases (a `CREATE TABLE` in an API-exposed schema with no `GRANT` to a non-owner runtime role and no service-role-only marker; a view created without `security_invoker = true`). It does not execute SQL, resolve cross-file ALTER/GRANT ordering beyond the scanned migration set, or prove a view's base tables actually carry RLS. The runtime-principal fidelity check (#177-A) is a prompt-contract acceptance gate (operator judgment, like the existing presence-only seal gate), not an executable detector of "this test used a service-role client."
- non_goals: A test-fidelity lint that statically flags service-role/privileged client construction in target tests (the heuristic Full-option, deferred — false-positive risk like #174). Live-database RLS probing. Auto-fixing missing grants. Non-Postgres access-control models (MySQL grants, Mongo rules).
- exclusions: Repos with no SQL migration directory (the lint records a Phase 75 disclosed-skip). Features with no DB read/write reachable by a non-privileged caller (the runtime-principal gate is satisfied vacuously).

## Open Questions

None blocking. One resolved design note recorded for the auditor:

- **Where the executable lint lives.** GH #177 frames the grant/view checklist under `qor-audit` (remediation B). But `qor-audit` reviews the **plan/blueprint pre-implementation**, when the SQL migrations do not yet exist; the implemented SQL exists at **seal time**. The deterministic lint therefore runs as a fail-closed gate in **`qor-substantiate`** (over real migrations), while `qor-audit` receives the **plan-level checklist items** (prompt-contract: the auditor confirms the plan commits to grants for any API-exposed table it introduces and flags any definer-rights view/SECURITY DEFINER design). This splits #177-B across both skills at the artifact boundary each one actually sees. De-complecting: detection of implemented reality (substantiate, deterministic) is separated from review of declared intent (audit, judgment).

## Context

GH #177 (filed from an external QA exemplar's customer-app autonomous cycle; two independent false-PASS instances). Root cause: the verifying principal (`service_role` key, or a `SECURITY DEFINER` RPC running as table owner) has more privilege than the runtime caller (`authenticated`/`anon`), so TDD-Light/integration tests exercise a path that does not exist for real users. `qor-substantiate` returns PASS on code that `42501`s in production. The current skills have no runtime-principal fidelity requirement and no Data-API grant/view check; this phase ships both, fail-closed with disclosed-skip per the operator decision.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Plan touches `qor/` package + skills + tests, not `src/`.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_data_api_acl_lint.py` · test_descriptor: `data_api_acl_lint.analyze flags a public CREATE TABLE with no GRANT to authenticated/anon (missing-grant) and a non-security_invoker view (definer-view); returns skipped when no migrations exist`
- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_runtime_principal_wiring.py` · test_descriptor: `qor-substantiate SKILL.md carries the runtime-principal fidelity ABORT gate + data_api_acl_lint || ABORT invocation; qor-audit SKILL.md carries the Data-API access-control checklist items`

## Phase 1: Data-API access-control lint (`qor/scripts/data_api_acl_lint.py`)

### Affected Files

- `tests/test_data_api_acl_lint.py` - NEW. Behavioral tests over synthetic SQL (see Unit Tests). Written first; red before the module exists.
- `qor/scripts/data_api_acl_lint.py` - NEW. Static SQL scanner + `main(argv)` entrypoint dispatchable via `qor-logic scripts data_api_acl_lint` (Phase 118 module dispatch; no dedicated subparser).

### Changes

```python
# Finding kinds: "missing-grant" (blocking), "definer-view" (blocking),
# "security-definer-fn" (advisory), "missing-migrations" (disclosed-skip sentinel).
@dataclass(frozen=True)
class AclFinding:
    kind: str
    object_name: str   # schema-qualified table/view/function
    file: str          # migration path
    detail: str

@dataclass(frozen=True)
class AclResult:
    findings: tuple[AclFinding, ...]
    skipped: bool      # True when no SQL migrations were found (Phase 75)
    skip_reason: str

DEFAULT_API_SCHEMAS = ("public",)
MIGRATION_GLOBS = ("supabase/migrations/*.sql", "migrations/*.sql",
                   "db/migrations/*.sql", "db/**/*.sql")

def find_sql_migrations(base: Path) -> list[Path]: ...
def parse_created_tables(sql: str) -> list[tuple[str, str]]: ...   # (schema, name)
def parse_grants(sql: str) -> list[tuple[str, str]]: ...           # (object, role)
def parse_revokes(sql: str) -> list[tuple[str, str]]: ...          # (object, role)
def parse_views(sql: str) -> list[tuple[str, bool]]: ...           # (name, security_invoker_on)
def parse_definer_functions(sql: str) -> list[str]: ...

def analyze(base: Path, api_schemas=DEFAULT_API_SCHEMAS) -> AclResult:
    """Scan all migrations as one corpus. Flag:
      missing-grant   -- a table in an API schema with no GRANT to a non-owner
                         runtime role (authenticated/anon), no REVOKE marking it
                         service-role-only, and no `-- qor:service-role-only`
                         escape comment.
      definer-view    -- a view in an API schema created without
                         `security_invoker = true`, no `-- qor:definer-view-intended`
                         escape comment.
      security-definer-fn -- advisory: each SECURITY DEFINER function (reviewed,
                         not blocked).
    Returns skipped=True when no migration files exist (disclosed-skip)."""

def main(argv: list[str] | None = None) -> int:
    """--repo-root PATH [--api-schemas a,b]. Exit 1 on any BLOCKING finding
    (missing-grant/definer-view) lacking an escape annotation; exit 0 when clean
    OR skipped (prints a `SKIP:` line so the caller records the Phase 75 event).
    Advisory findings print but do not change a clean exit 0."""
```

Escape annotations mirror the established inline-comment exemption pattern (Phase 110 `signature-widening-exempt`): a `-- qor:service-role-only` comment on or immediately above a `CREATE TABLE` suppresses `missing-grant` (the issue's instance 1 was a *legitimately* service-role-only table; the lint must not flag intentional ones); `-- qor:definer-view-intended reason: <text>` suppresses `definer-view`. De-complecting: parsing (the `parse_*` helpers, each a pure `str -> list`) is separated from policy (`analyze`), which is separated from process exit (`main`).

### Unit Tests

- `tests/test_data_api_acl_lint.py::test_missing_grant_flagged` - migration with `CREATE TABLE public.items (...)` and no GRANT; `analyze` returns one `missing-grant` finding naming `public.items`.
- `::test_grant_to_authenticated_clears` - same table plus `GRANT SELECT ON public.items TO authenticated`; `analyze` returns no `missing-grant`.
- `::test_service_role_only_escape_clears` - table preceded by `-- qor:service-role-only` and `REVOKE ALL ON public.items FROM authenticated`; no `missing-grant` (intentional, not flagged).
- `::test_definer_view_flagged` - `CREATE VIEW public.v AS SELECT ...` with no `security_invoker`; returns a `definer-view` finding.
- `::test_security_invoker_view_clears` - `CREATE VIEW public.v WITH (security_invoker = true) AS ...`; no `definer-view` finding.
- `::test_security_definer_fn_is_advisory` - a `SECURITY DEFINER` function yields a `security-definer-fn` finding AND `main` still exits 0 when that is the only finding (advisory, non-blocking).
- `::test_main_exit_1_on_blocking` - repo dir with a `missing-grant`; `main(["--repo-root", str(d)])` returns 1.
- `::test_main_exit_0_and_skip_line_when_no_migrations` - empty repo; `main` returns 0 and stdout contains `SKIP:` (disclosed-skip sentinel).
- `::test_non_api_schema_table_not_flagged` - `CREATE TABLE internal.audit_log (...)` with `api_schemas=("public",)`; no finding (only API-exposed schemas are in scope).

## Phase 2: Skill wiring + variant recompile

### Affected Files

- `tests/test_runtime_principal_wiring.py` - NEW. Prompt-contract assertions on both SKILL.md files (see Unit Tests).
- `qor/skills/governance/qor-substantiate/SKILL.md` - add (a) a Step 4 sub-section "Runtime-Principal Fidelity gate" (prompt-contract ABORT with disclosed coverage-gap escape), and (b) Step 4.6.10 invoking `qor-logic scripts data_api_acl_lint --repo-root . || ABORT`, plus a `module:qor.scripts.data_api_acl_lint` row in the Step Prerequisites table. Detailed prose lives in the reference (progressive disclosure); SKILL.md carries the short step + invocation only.
- `qor/skills/governance/qor-audit/SKILL.md` - extend the Security Pass checklist (Step 3) with the three Data-API access-control items (plan-level, prompt-contract VETO).
- `qor/dist/variants/**` - regenerated via `qor-logic compile`.

### Changes

`qor-substantiate` Step 4 gains, after the presence-only seal gate, a short Runtime-Principal Fidelity gate: for any feature whose acceptance includes a DB read/write reachable by a non-privileged caller (authenticated/anon), the operator confirms at least one test exercises that path under the real caller role. If the path is proven only under `service_role` / a `SECURITY DEFINER` RPC, the seal ABORTs UNLESS the operator records an explicit coverage-gap note in the seal entry ("data path verified only under service_role; authenticated/RLS path deferred to manual QA") and emits a `gate_skipped_prerequisite_absent`-style shadow event. The detailed acceptance question + examples live in `qor/references/doctrine-runtime-principal-fidelity.md`.

Step 4.6.10 adds the deterministic lint to the fail-closed reliability ladder using the established `|| ABORT` idiom (matching Step 4.6.5 secret-scanner and Step 4.7.5 governance-index). Phase 75 disclosed-skip applies when no migrations exist (the `SKIP:` line maps to the recorded skip event).

`qor-audit` Security Pass gains three checklist items (plan-level review): (1) every API-exposed `CREATE TABLE` the plan introduces commits to explicit GRANTs; (2) `SECURITY DEFINER` functions and definer-rights (non-`security_invoker`) views over RLS-bearing tables are called out and access-scoped; (3) a plan whose runtime caller is authenticated but whose tests construct a privileged (service-role) client is insufficient proof. Any violation -> VETO.

### Unit Tests

- `tests/test_runtime_principal_wiring.py::test_substantiate_has_runtime_principal_gate` - read `qor-substantiate/SKILL.md`; assert it contains the runtime-principal fidelity gate with an ABORT directive AND the disclosed coverage-gap escape phrase, co-located within one section. Prompt-contract test.
- `::test_substantiate_invokes_data_api_acl_lint` - assert SKILL.md contains `data_api_acl_lint` followed by `|| ABORT` within a short window (fail-closed, not WARN).
- `::test_substantiate_has_acl_prerequisite_row` - assert the Step Prerequisites table has a `module:qor.scripts.data_api_acl_lint` row (Phase 75 disclosed-skip declared).
- `::test_audit_security_pass_has_dataapi_items` - read `qor-audit/SKILL.md`; assert the Security Pass region contains all three Data-API access-control checklist items (grant-on-API-table, definer-view/SECURITY-DEFINER flag, service-role-test-insufficiency).

## Phase 3: Doctrine + reference + glossary

### Affected Files

- `qor/references/doctrine-runtime-principal-fidelity.md` - NEW. Home for both introduced terms; carries the detailed runtime-principal acceptance question, the privileged-vs-runtime-principal root cause, the lint finding-kind table + escape annotations, and the substantiate/audit split rationale (progressive-disclosure target for the two SKILL.md steps).
- `qor/references/glossary.md` - add `runtime-principal fidelity` and `Data-API access-control lint` entries.
- `tests/test_data_api_acl_lint.py::test_doctrine_documents_finding_kinds` - functional doc-contract: the reference names every finding kind the module emits.

### Changes

The reference doc states the contract the two skills point at; the glossary cross-links it. The doc-contract test reads `analyze`'s emitted kinds reflectively (or a `KNOWN_FINDING_KINDS` constant in the module) and asserts each appears in the reference — so the doc cannot drift from the code (inverse-coverage discipline per `doctrine-test-functionality.md`).

## Definition of Done

### Deliverable: Data-API access-control lint

- **D1**: a static SQL scan makes `missing-grant` and non-`security_invoker` `definer-view` defects fail-close the seal; service-role-only tables and intended definer views are not flagged (escape annotations).
- **D2**: `qor/scripts/data_api_acl_lint.py` with `analyze`, the `parse_*` helpers, `KNOWN_FINDING_KINDS`, and `main(argv)`; dispatchable as `qor-logic scripts data_api_acl_lint`.
- **D3**: Step 4.6.10 invocation + Step Prerequisites row in qor-substantiate SKILL.md; reference doc + glossary entries; META_LEDGER seal entry; version bump.
- **D4**: `tests/test_data_api_acl_lint.py::test_missing_grant_flagged` + `::test_definer_view_flagged` + `::test_service_role_only_escape_clears` + `::test_main_exit_0_and_skip_line_when_no_migrations`.

### Deliverable: runtime-principal fidelity + audit checklist

- **D1**: /qor-substantiate fail-closes on service-role-only proof of an authenticated path (unless a disclosed coverage-gap note is recorded); /qor-audit reviews API-table grants + definer views at plan time.
- **D2**: Step 4 Runtime-Principal Fidelity gate in qor-substantiate SKILL.md; three Data-API items in qor-audit Security Pass; variants recompiled.
- **D3**: Phase 75 disclosed-skip declared for absent migrations; coverage-gap disclosed-skip declared for the runtime-principal gate.
- **D4**: `tests/test_runtime_principal_wiring.py::test_substantiate_has_runtime_principal_gate` + `::test_substantiate_invokes_data_api_acl_lint` + `::test_audit_security_pass_has_dataapi_items`.

## CI Commands

- `python -m pytest tests/test_data_api_acl_lint.py tests/test_runtime_principal_wiring.py -q` — new lint + wiring.
- `python -m qor.cli scripts data_api_acl_lint --repo-root .` — canonical repo records a Phase 75 disclosed-skip (no SQL migrations) and exits 0.
- `python -m pytest -q` — full suite green before substantiate.
