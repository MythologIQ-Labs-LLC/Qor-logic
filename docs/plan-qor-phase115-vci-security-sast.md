# Plan: Phase 115 - VCI security pillar (SAST via bandit) (#167)

**change_class**: feature

**doc_tier**: system

**Risk Grade**: L2

**high_risk_target**: false

**originating_remediation**: GH #167 (VCI security pillar); parent #166; umbrella #147; follows Phase 114 spine (v0.81.0)

**terms_introduced**:
- term: SAST Backend
  home: qor/references/doctrine-verification-closure-integrity.md

**boundaries**:
- limitations: Adds a SAST sub-check behind a tool-agnostic backend interface, default backend bandit, feeding the qa.json `security` pillar. When the backend tool is absent the pillar records `skip` with a note (Phase 75 prerequisite-absent pattern) -- the capability ships and is tested on canned output; it activates when bandit is installed.
- non_goals: Semgrep/other backends are NOT implemented (the interface admits them later, per #167 + the #163 pluggable-backend pattern). secret-scan / SBOM / dependency-audit / OWASP are already live elsewhere and are NOT re-implemented here.
- exclusions: No change to the seal PASS/VETO path; the security pillar is advisory in qa.json. No commit/push/PR (Review Boundary).

## Locked Decisions

- **LD1 (bandit + tool-agnostic)**: default backend is bandit (pure-Python, zero-network, low supply-chain surface, matches the lean-dep ethos). The `scan` API is backend-agnostic: a backend is a callable `(paths) -> list[normalized finding dict]`; a future semgrep backend normalizes into the same shape. Operator chose bandit with a pluggable interface over committing to semgrep up front.
- **LD2 (graceful skip)**: bandit is not installed in every environment. When the backend is unavailable the pillar is `status: "skip"` with a note (not a crash, not a false pass) -- Phase 75 prerequisite-absent semantics.
- **LD3 (dependency admission)**: bandit is declared as an optional `sast` extra (not a core runtime dep), keeping the core install lean. Cooling-period admission per `dependency_admission_lint` is recorded at seal time (operator step); noted here.

## Context

Phase 114 shipped the qa.json `security` pillar as an explicit `skip`. Research found secret-scan/SBOM/OWASP are already live; SAST is the one genuine net-new security gap (#167). This phase fills it with a tool-agnostic SAST sub-check.

## Feature Inventory Touches

Empty. Governance/QA tooling; no `src/` product feature surface.
`feature_inventory_touches`: `[]`.

## Phase 1: tool-agnostic SAST sub-check

### Affected Files
- `tests/test_sast_scan.py` - NEW. Behavioral: normalize canned bandit JSON; pillar status pass on no findings, fail on HIGH severity; metric counts; unknown backend raises; backend-unavailable -> skip; integration test gated on bandit availability.
- `qor/scripts/sast_scan.py` - NEW. `to_pillar(findings, *, fail_on="HIGH") -> dict`; `bandit_backend(paths) -> list[dict]` (runs `python -m bandit -r <paths> -f json`, normalizes); `BACKENDS` registry; `scan(paths, *, backend="bandit") -> dict` (security pillar dict; backend-unavailable -> skip); CLI `python -m qor.scripts.sast_scan --paths <p> --backend bandit [--out <f>]`.
- `pyproject.toml` - AMENDED. Add optional `sast` extra: `bandit`.

### Unit Tests
- `test_sast_scan.py::test_to_pillar_pass_on_no_findings` - [] -> status pass, metric 0.
- `::test_to_pillar_fail_on_high_severity` - a HIGH finding -> status fail.
- `::test_to_pillar_metric_counts_findings` - N findings -> metric N.
- `::test_bandit_normalize_parses_json` - canned bandit JSON -> normalized findings with severity.
- `::test_unknown_backend_raises` - scan(backend="nope") -> ValueError.
- `::test_scan_skips_when_backend_unavailable` - backend raising FileNotFoundError -> status skip + note.
- `::test_bandit_backend_integration` - gated (skip if bandit unavailable): runs bandit on a tmp file with a known issue; asserts a finding.

## Phase 2: wire into qa.json security pillar + doctrine

### Affected Files
- `tests/test_qa_evidence_security.py` - NEW. Behavioral: a SAST pillar dict from `sast_scan.scan` flows through `qa_evidence.build_payload(security=...)` and the verdict turns FAIL when the security pillar fails; skip leaves verdict PASS.
- `qor/scripts/qa_evidence.py` - AMENDED (minimal). Optional `run_sast` convenience that calls `sast_scan.scan` and feeds the `security` override (build_payload already accepts `security`); default behavior unchanged.
- `qor/references/doctrine-verification-closure-integrity.md` - AMENDED. Add the SAST Backend term + the security-pillar contract (bandit default, tool-agnostic, graceful skip).

### Unit Tests
- `test_qa_evidence_security.py::test_sast_fail_sets_verdict_fail` - security pillar fail -> overall verdict FAIL.
- `::test_sast_skip_keeps_verdict_pass` - security pillar skip -> verdict PASS, pillar visible as skip.
- `::test_doctrine_defines_sast_backend_term` - doctrine parser asserts the SAST Backend term + graceful-skip rule.

## Definition of Done

### Deliverable D-115.1: tool-agnostic SAST sub-check
- **D1**: A SAST sub-check produces a security-pillar verdict from a pluggable backend (bandit default), degrading to skip when the tool is absent.
- **D2**: `qor/scripts/sast_scan.py` (to_pillar / bandit_backend / BACKENDS / scan / CLI); bandit declared as optional `sast` extra.
- **D3**: Doctrine documents the SAST Backend contract + graceful-skip; cooling-period admission noted for seal.
- **D4**: `tests/test_sast_scan.py` passes (integration test skips cleanly when bandit absent).

### Deliverable D-115.2: qa.json wiring
- **D1**: SAST result flows into the qa.json `security` pillar and a HIGH finding fails the overall verdict.
- **D2**: `qa_evidence.run_sast` convenience; build_payload unchanged contract.
- **D3**: Doctrine updated.
- **D4**: `tests/test_qa_evidence_security.py` passes.

## CI Commands

- `python -m pytest tests/test_sast_scan.py tests/test_qa_evidence_security.py -q` - new behavioral suites.
- `python -m pytest tests/ -q` - full regression.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase115-vci-security-sast.md` - plan-internal consistency.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase115-vci-security-sast.md` - Definition of Done declaration check.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - ledger chain integrity.

## CI Coverage Exemptions

- `test_packaging_install` - packaging smoke; orthogonal.
- `check_variant_drift` - no source-skill prompt changes in this phase (scripts/tests/doctrine only); variants unaffected.
