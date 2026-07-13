# Plan: Unify governance-path resolution and ledger-dialect handling (GH #282)

**change_class**: feature

**doc_tier**: minimal

**originating_remediation**: GH #282

## Open Questions

None blocking. Design decisions settled autonomously (auto-dev cycle) and disclosed in the
substantiate packet:

- Architecture-authority precedence: when a governance index is present, the legacy literal
  `docs/architecture.md` wins if it exists and is registered (this repo: zero behavior change);
  otherwise the single registered architecture doc is resolved (adopter: `docs/ARCHITECTURE_PLAN.md`).
  "Multiple" fails only when the legacy literal is absent and two or more registered architecture
  docs exist.
- Non-release classification is a new `governance` `change_class` value (version-not-applicable).
- Ledger compatibility boundary stays at entry 123 (`MARKUP_COMPAT_BOUNDARY`), now single-sourced.

## Root Causes (from research brief)

1. `doc_integrity.check_topology` hardcodes `docs/architecture.md`; ignores the registered authority.
2. Three ledger parsers disagree; `CONTENT_HASH_RE` rejects fenced bare-hex; separate `**Phase**:`
   line unrecognized by `seal_entry_check`.
3. Version-applicability validated only at the substantiate bump (after audit PASS); no non-release
   classification.
4. `prompt_injection_canaries` allowlist admits only `docs/plan-qor-phase*.md`.

## Phase 1: Shared canonical governance-path resolver

### Affected Files

- `tests/test_governance_paths.py` - NEW. Behavioral tests for the resolver (positive + negative).
- `qor/scripts/governance_paths.py` - NEW. `resolve_architecture_authority` +
  `resolve_governance_plan_path` + `GovernancePathError`. Reuses
  `governance_index._registered_paths` / `_is_registered` (single registration source).
- `qor/scripts/doc_integrity.py` - `check_topology` consumes `resolve_architecture_authority` for the
  architecture slot of the `system` tier; other three system docs unchanged.
- `qor/scripts/prompt_injection_canaries.py` - `_validate_path` delegates to
  `resolve_governance_plan_path`; retains the four canonical files + doctrines + research briefs as
  always-registered governance paths.

### Changes

`governance_paths.resolve_architecture_authority(repo_root) -> Path`:
- Read registered paths via `governance_index._registered_paths(index_text)` when
  `docs/GOVERNANCE_INDEX.md` exists.
- Index present: if `docs/architecture.md` exists and is registered -> return it (legacy precedence).
  Else collect registered architecture-named docs (`Path.name` lower in
  `{architecture.md, architecture_plan.md}`) that exist within root; exactly one -> return it; zero ->
  raise `GovernancePathError` (missing/unregistered); two+ -> raise (multiple/ambiguous).
- Index absent: return `docs/architecture.md` if it exists (legacy fallback), else raise.
- Always reject a resolved path that escapes `repo_root` (outside-root) or is not under it.

`governance_paths.resolve_governance_plan_path(raw, repo_root) -> Path`:
- Reject empty, absolute-with-traversal, or `..`-containing raw before any read.
- Normalize `repo_root / raw`; `resolve()`; assert the result is within `repo_root.resolve()`
  (outside-root -> raise).
- Assert suffix is a governance extension (`.md`); else raise (unsupported-extension).
- Assert registration: the always-allowed governance families
  (`ARCHITECTURE_PLAN|META_LEDGER|CONCEPT`, `research-brief-*`, `doctrine-*`) OR a
  `GOVERNANCE_INDEX`-registered path; else raise (unregistered).
- Return the normalized `Path`.

### Unit Tests

- `tests/test_governance_paths.py`:
  - system-tier repo whose sole registered architecture authority is `docs/ARCHITECTURE_PLAN.md`
    (no `docs/architecture.md`) -> `resolve_architecture_authority` returns that path.
  - repo with legacy `docs/architecture.md` registered -> returns the legacy literal (precedence).
  - no architecture doc registered/present -> raises `GovernancePathError` (missing).
  - two registered architecture docs, legacy literal absent -> raises (multiple).
  - architecture path pointing outside root -> raises (outside-root).
  - `resolve_governance_plan_path` accepts a registered `docs/plan-governance-hardening.md`.
  - rejects `../etc/passwd`, an absolute outside-root path, a `.txt` extension, and an unregistered
    `docs/plan-unlisted.md` -- each before reading the file.

## Phase 2: Topology + canary consume the resolver

### Affected Files

- `tests/test_doc_integrity.py` - add system-tier-via-ARCHITECTURE_PLAN positive + missing/multiple
  negatives that invoke `check_topology` and assert raise/no-raise.
- `tests/test_prompt_injection_canary.py` - add: a registered non-`plan-qor-phase` active plan is
  scanned (canary in it is still detected); traversal/outside-root/unsupported/unregistered rejected
  before read; a real canary in a registered plan still fails.

### Changes

- `check_topology(tier, repo_root)`: for the `system` tier, resolve the architecture slot through
  `resolve_architecture_authority` (raise -> topology ValueError with the resolver reason); the other
  three living docs keep the literal-existence check.
- `prompt_injection_canaries._validate_path(raw, repo_root=None)`: delegate to
  `resolve_governance_plan_path`; keep exit-2 on rejection. `main` passes `--repo-root` (default `.`).

### Unit Tests

- `tests/test_doc_integrity.py`: build a tmp repo with `docs/GOVERNANCE_INDEX.md` registering
  `docs/ARCHITECTURE_PLAN.md` + the other three system docs, no `docs/architecture.md` ->
  `check_topology("system", root)` does not raise. Remove the registration -> raises.
- `tests/test_prompt_injection_canary.py`: a registered `docs/plan-governance-hardening.md`
  containing an instruction-redirect canary (the literal string lives in the test source, not this
  plan) -> `scan` returns a hit and CLI exits 1 (path admitted, content scanned). An unregistered
  `docs/plan-unlisted.md` -> CLI exits 2 (rejected before read).

## Phase 3: Shared versioned ledger-dialect parser

### Affected Files

- `tests/test_ledger_dialect.py` - NEW. Consumer-agnostic dialect tests + the three-consumer
  consistency test.
- `qor/scripts/ledger_dialect.py` - NEW. Single source for: `MARKUP_COMPAT_BOUNDARY = 123`; the
  hash-value fragment recognizing inline-backtick, `= <hex>`, and fenced bare-hex; compiled
  `CONTENT_HASH_RE` / `PREV_HASH_RE` / `CHAIN_HASH_RE` / `SESSION_SEAL_RE`; `hash_value(match)` (first
  non-None group); `entry_phase(header, body)` (phase from header `Phase <N>` OR a separate
  `**Phase**:` line).
- `qor/scripts/ledger_hash.py` - import the shared regexes + `hash_value` + `MARKUP_COMPAT_BOUNDARY`;
  replace the local `group(1) or group(2)` extractions with `hash_value`. Verify/verify_post_anchor
  logic otherwise unchanged.
- `qor/reliability/seal_entry_check.py` - use the shared hash regexes (accept fenced) and
  `entry_phase` fallback so an entry whose header lacks `Phase <N>` but carries `**Phase**:` parses.

### Changes

`ledger_dialect`:
```
_HEX = r"[0-9a-f]{64}"
_HASH_VALUE = rf"(?:`({_HEX})`|=\s*({_HEX})\b|(?:^|\n)[ \t]*({_HEX})[ \t]*(?:\n|$))"
```
The third alternative matches a hex alone on its line (the fenced-block form) and is bounded by the
existing `_HASH_SPAN` (stops at the next `**Field**`), so prose hex is not captured.

`entry_phase(header, body)`: return int from `Phase\s*(\d+)` in the header line if present; else from
a `^\*\*Phase\*\*:\s*.*?(\d+)` line in the body; else None.

`ledger_hash`: `CONTENT_HASH_RE`/`PREV_HASH_RE`/`CHAIN_HASH_RE`/`SESSION_SEAL_RE` re-exported from
`ledger_dialect`; every `m.group(1) or m.group(2)` becomes `ledger_dialect.hash_value(m)`.
`markup_required_cutoff` default sources `ledger_dialect.MARKUP_COMPAT_BOUNDARY`.

`seal_entry_check`: `_HASH_FIELD_RE`/`_parse_latest_entry` use the shared per-field regexes;
`_ENTRY_HEADER_RE` no longer requires `Phase` on the header line -- header captures kind, phase comes
from `entry_phase(header_line, block)`.

### Unit Tests

- `tests/test_ledger_dialect.py`:
  - inline-backtick, `= <hex>`, and fenced bare-hex all extract the same hash via the shared regex +
    `hash_value`.
  - `entry_phase` reads the header form AND the separate `**Phase**:` form.
  - Consistency: a fixture ledger with separate-`**Phase**:` + fenced-hash entries at/after 123 is
    parsed identically by `ledger_hash.verify` (rc 0), `seal_entry_check.check_latest` (ok), and
    `governance_health.check_governance_health` (ledger OK) -- all three agree.
  - Negative (preserved rejections, each asserts a FAIL/rc!=0): a tampered content body (recorded
    content_hash no longer matches), a malformed (non-64) hash, a chain-hash mismatch, and an invalid
    post-boundary duplicate previous_hash.

## Phase 4: Early version-applicability validation

### Affected Files

- `tests/test_version_applicability.py` - NEW.
- `qor/scripts/version_applicability.py` - NEW. `RELEASE_CLASSES`, `NON_RELEASE_CLASSES`,
  `VersionVerdict`, `validate(plan_path, repo_root)`, `is_release_class(change_class)`.
- `qor/scripts/governance_helpers.py` - `_CHANGE_CLASS_RE` accepts `governance`. `parse_change_class`
  unchanged otherwise.
- `qor/gates/schema/plan.schema.json` - `change_class` enum adds `governance`; the `feature|breaking`
  audit-required rule is unchanged (governance is non-release, audit still optional-by-existing-rule).
- `qor/skills/governance/qor-audit/SKILL.md` - add a version-applicability step before PASS emission.
- `qor/skills/governance/qor-substantiate/SKILL.md` - the bump step SKIPs for `governance`
  (version-not-applicable; no bump, no tag), and cites `version_applicability.validate` as the
  early-and-final check.

### Changes

`version_applicability.validate(plan_path, repo_root) -> VersionVerdict`:
- `parse_change_class(plan_path)` (raises if missing/invalid).
- `governance` -> `VersionVerdict(ok=True, classification="version-not-applicable", ...)`.
- release class -> `target = governance_helpers._compute_new(current_version, change_class)`;
  `highest = _highest_tag(_list_tags())`; `ok = highest is None or target > highest`; reason names
  both versions. Mirrors the existing bump-time downgrade guard exactly, moved earlier.

### Unit Tests

- `tests/test_version_applicability.py` (monkeypatch `_list_tags` for determinism -- no live tag
  coupling):
  - `feature` plan with current 0.132.0 and highest tag v0.132.0 -> `target=(0,133,0)`, `ok=True`.
  - `feature` plan with highest tag v0.140.0 -> `ok=False` (target <= current highest).
  - a plan missing `change_class` -> `parse_change_class` raises (validated before any PASS).
  - `governance` plan -> `ok=True`, `classification="version-not-applicable"`, no target computed.

## Definition of Done

### Deliverable: shared governance-path resolver

- **D1**: One resolver answers "which file is the architecture authority?" and "is this plan path a
  registered governance file?", fail-closed, reusing the index registration parser.
- **D2**: `qor/scripts/governance_paths.py` exports `resolve_architecture_authority(repo_root)->Path`,
  `resolve_governance_plan_path(raw, repo_root)->Path`, `GovernancePathError(ValueError)`.
- **D3**: `check_topology` and `prompt_injection_canaries` consume it; ledger entry records the shared
  resolver; README + CHANGELOG document the topology + canary contract change.
- **D4**: `tests/test_governance_paths.py` asserts ARCHITECTURE_PLAN resolves, and
  missing/multiple/outside-root/unregistered/unsupported-ext each raise.

### Deliverable: shared ledger-dialect parser

- **D1**: One parser recognizes inline/`=`/fenced hash forms + separate `**Phase**:` line with one
  compatibility boundary; three consumers agree.
- **D2**: `qor/scripts/ledger_dialect.py` exports the compiled hash regexes, `hash_value`,
  `entry_phase`, `MARKUP_COMPAT_BOUNDARY`; `ledger_hash` + `seal_entry_check` import them.
- **D3**: CHANGELOG documents the accepted dialect + boundary; no ledger history changed.
- **D4**: `tests/test_ledger_dialect.py` asserts fenced+separate-Phase fixtures verify under all three
  consumers AND tampered/malformed/chain-mismatch/dup-previous still FAIL.

### Deliverable: early version-applicability validation

- **D1**: A release-class plan whose target would not exceed the current tag is rejected before audit
  PASS; a governance-only cycle is explicitly version-not-applicable.
- **D2**: `qor/scripts/version_applicability.py` exports `validate(plan_path, repo_root)->VersionVerdict`
  and `is_release_class`; `governance` accepted by `parse_change_class` + plan schema.
- **D3**: audit + substantiate SKILLs consume the same validator; CHANGELOG documents the class.
- **D4**: `tests/test_version_applicability.py` asserts feature-target>tag PASS, target<=tag FAIL,
  missing-class raise, governance version-not-applicable.

## Feature Inventory Touches

None. This plan touches `qor/scripts`, `qor/reliability`, gate schema, and skills -- not `src/`
(Qor-logic has no `src/`). Governance/tooling only.

## CI Commands

- `python -m pytest tests/test_governance_paths.py tests/test_ledger_dialect.py tests/test_version_applicability.py -q` -- new unit suites.
- `python -m pytest tests/test_doc_integrity.py tests/test_prompt_injection_canary.py tests/test_seal_entry_check.py tests/test_verify_ledger_cli.py tests/test_ledger_hash.py tests/test_ledger_hash_markup_cutoff.py tests/test_governance_health.py -q` -- regression neighbors.
- `python -m qor.cli verify-ledger --ledger docs/META_LEDGER.md` -- ledger chain stays green.
- `python -m pytest -q` -- full suite.
