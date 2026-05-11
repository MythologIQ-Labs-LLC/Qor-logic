# Plan: Phase 45 — qor-audit hardening + `plan_text_consistency_lint` V1

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: docs/research-brief-open-issues-grouping-2026-05-09.md (α-bundle: GH issues #42, #44, #45)

**terms_introduced**:
- term: plan_text_consistency_lint
  home: qor/scripts/plan_text_consistency_lint.py
- term: target_content_hash
  home: qor/gates/schema/audit.schema.json
- term: originating_remediation
  home: qor/gates/schema/plan.schema.json
- term: plan-content short-circuit
  home: qor/skills/governance/qor-audit/SKILL.md (Step 0.4)
- term: self-targeting remediation pass
  home: qor/skills/governance/qor-audit/SKILL.md (Step 3 / Self-Targeting Remediation Pass)
- term: SG-039
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**boundaries**:
- limitations:
  - V1 ships --check mode only; no --apply rewrite (deferred to V2 per GH #46).
  - V1 uses broad-rule grouping (same kind + 2+ distinct normalized = drift); identity-based grouping deferred to V2.
  - V1 covers 5 operation kinds (cargo_test, cargo_build, python_module, python_script, filesystem_path); no `dep_name` cross-check against Cargo.toml/requirements*.txt (deferred to V2).
  - V1 may produce false positives on natural CI-command sections that legitimately invoke multiple python_modules or the same script with different args; operator distinguishes via stdout review until V2 lands.
  - The plan-content short-circuit (#45) compares whole-file SHA256; whitespace-only edits trigger a full audit. Joint hash with skill source (so that skill amendments invalidate the cache) is included in V1.
  - The self-targeting pass (#44) requires the operator to declare `originating_remediation` in plan top-matter; absence means the pass does not fire (no auto-detection).
- non_goals:
  - Auto-classification of which document is the "remediation" plan vs an ordinary plan.
  - Cross-session signature accumulation (handled by Phase β / GH #43).
  - Lint V2 features (handled by Phase β / GH #46).
- exclusions:
  - Variant dist recompile semantics unchanged; SKILL.md edits propagate via `dist_compile` at substantiate.
  - No CI workflow changes; lint runs at audit Step 0.6 only (no GitHub Actions wiring this phase).

## Open Questions

None at submission. Design questions resolved in research brief `docs/research-brief-open-issues-grouping-2026-05-09.md`.

---

## Phase 1: `plan_text_consistency_lint` V1 module + tests

### Affected Files

- `qor/scripts/plan_text_consistency_lint.py` — NEW. Stdlib-only V1 lint with 5 operation-kind detectors and broad-rule drift detection. CLI: `python -m qor.scripts.plan_text_consistency_lint --check <plan-path>`.
- `tests/test_plan_text_consistency_lint.py` — NEW. Behavior tests for each operation kind, drift detection, placeholder skip, exit codes.

### Changes

**`qor/scripts/plan_text_consistency_lint.py`** — single-file module, stdlib-only, target ≤200 lines.

Public surface:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Site:
    line: int
    section: str          # nearest preceding ## or ### heading text
    raw_text: str         # the raw match as it appeared
    normalized: str       # canonical form for comparison

@dataclass(frozen=True)
class DriftFinding:
    operation_kind: str   # one of the 5 kinds
    sites: tuple[Site, ...]   # 2+ sites with distinct normalized
    resolution_hint: str  # human-readable "pick canonical site, edit other(s) to match"

def lint(plan_text: str) -> list[DriftFinding]: ...
def main(argv: list[str] | None = None) -> int: ...   # CLI entry; returns 0/1
```

Operation-kind detectors (regex against code-span content `` `…` `` after stripping triple-fenced blocks):

| Kind | Pattern (informal) | Normalize by |
|---|---|---|
| `cargo_test` | `cargo test ...` | drop trailing whitespace, sort flags lexicographically, keep positional in order |
| `cargo_build` | `cargo build ...` | same as cargo_test |
| `python_module` | `python -m <dotted_path> [args]` | drop trailing ws |
| `python_script` | `python <relpath>.py [args]` | drop trailing ws |
| `filesystem_path` | candidate paths matching `[A-Za-z0-9_./-]+\.(md\|py\|json\|yaml\|toml\|rs\|ts\|tsx)` and directory-like `[A-Za-z0-9_./-]+/` | strip leading `./`, collapse `\\` to `/` |

Placeholder skip: any code-span containing `<...>`, `{...}`, or literal `...` (ellipsis) is excluded from comparison via `_is_placeholder(text) -> bool`.

Drift rules:

- For `cargo_test`, `cargo_build`, `python_module`, `python_script`: drift when same kind has ≥2 sites with distinct `normalized` values.
- For `filesystem_path`: asymmetric — drift when same `normalized` value appears with ≥2 distinct `raw_text` values (catches typos like `docs/PLAN.md` vs `docs/plan.md`).

CLI behavior:

- `--check <path>`: read file, run `lint(text)`, print findings to stderr in human format, exit 1 if any findings, exit 0 otherwise.
- `--check` is the only mode in V1.

**`tests/test_plan_text_consistency_lint.py`** — pytest functions:

- `test_no_drift_clean_plan_returns_empty` — feeds a plan with one cargo_test site; expects `lint()` returns `[]`; CLI exits 0.
- `test_cargo_test_drift_detected_when_two_distinct_invocations` — two `cargo test` sites with different flag sets; expects exactly 1 finding of kind `cargo_test` with both sites; CLI exits 1.
- `test_python_module_drift_detected` — same shape for `python -m foo` vs `python -m bar`; one finding of kind `python_module`.
- `test_filesystem_path_drift_asymmetric_on_raw_text` — two sites with same normalized path but different casing; one finding of kind `filesystem_path`.
- `test_placeholder_codespan_is_skipped` — code-spans containing `<sid>` or `{...}` do not produce findings.
- `test_section_attribution_uses_nearest_heading` — site's `section` field equals the nearest preceding `## …` or `### …` heading text.
- `test_cli_check_exit_codes_match_finding_presence` — invoke `main(["--check", str(tmp_path / "plan.md")])`; assert returncode 0/1 against fixture content.
- `test_cli_stderr_describes_findings` — captured stderr names operation_kind, line numbers, raw_text fragments.

CI commands listed in §CI Commands at end of plan.

---

## Phase 2: Schema bumps + qor-audit / qor-plan SKILL wiring

### Affected Files

- `qor/gates/schema/audit.schema.json` — add three optional fields: `target_content_hash`, `originating_remediation`, `plan_text_consistency_lint_findings`.
- `qor/gates/schema/plan.schema.json` — add one optional field: `originating_remediation`.
- `qor/skills/governance/qor-audit/SKILL.md` — add Step 0.4 (plan-content short-circuit), Step 0.6 (pre-audit lints), Step 3 sub-pass (Self-Targeting Remediation Pass); amend Step Z payload to include the three new fields.
- `qor/skills/sdlc/qor-plan/SKILL.md` — Step 5 review checklist gains one line + lint invocation note; Step Z payload includes `originating_remediation` when set.
- `tests/test_audit_schema_v_n.py` — NEW. Asserts schema accepts payloads with/without the three new fields; rejects malformed values.
- `tests/test_plan_schema_originating_remediation.py` — NEW. Asserts schema accepts plan payloads with `originating_remediation` string and without (omitted).
- `tests/test_audit_hash_short_circuit.py` — NEW. Asserts `gate_chain.read_phase_artifact("audit", session_id=sid)` is consulted when present and same-hash short-circuit returns the prior verdict.
- `tests/test_audit_self_targeting_pass.py` — NEW. Asserts a plan declaring `originating_remediation` triggers an additional adversarial pass slot in the audit report; absent declaration leaves the slot empty.

### Changes

**`qor/gates/schema/audit.schema.json`** — add to `properties`:

```json
"target_content_hash": {
  "description": "Phase 45: SHA256 hex of (plan_text || skill_source_concat). Set by /qor-audit Step 0.4. Read by next /qor-audit invocation in same session for plan-content short-circuit (#45). Joint hash invalidates cache when skill source changes.",
  "type": ["string", "null"],
  "pattern": "^([0-9a-f]{64}|)$"
},
"originating_remediation": {
  "description": "Phase 45: when set, mirrors the plan's originating_remediation declaration. Read by /qor-audit Step 3 Self-Targeting Remediation Pass to know whether to manually apply the not-yet-runnable discipline against the plan introducing it (#44).",
  "type": ["string", "null"]
},
"plan_text_consistency_lint_findings": {
  "description": "Phase 45: WARN-only output of qor.scripts.plan_text_consistency_lint at Step 0.6. Empty array == clean. Non-empty does NOT itself force VETO; surfaces in audit report under Process Pattern Advisory.",
  "type": ["array", "null"],
  "items": {
    "type": "object",
    "required": ["operation_kind", "sites"],
    "properties": {
      "operation_kind": { "type": "string" },
      "sites": { "type": "array", "items": { "type": "object" }, "minItems": 2 }
    }
  }
}
```

**`qor/gates/schema/plan.schema.json`** — add to `properties`:

```json
"originating_remediation": {
  "description": "Phase 45 (#44): path or descriptor for the prior remediation artifact this plan implements. When set, /qor-audit Step 3 runs the Self-Targeting Remediation Pass: manually apply the not-yet-runnable discipline this plan introduces against this plan itself.",
  "type": ["string", "null"]
}
```

**`qor/skills/governance/qor-audit/SKILL.md`** — three insertions:

1. New `### Step 0.4: Plan-content short-circuit (Phase 45 wiring — #45)` between current Step 0 and Step 0.5. Body:

   - Read prior audit artifact for current session via `gate_chain.read_phase_artifact("audit", session_id=sid)`.
   - Compute current `target_content_hash` as `sha256(plan_text + sha256_of_skill_source).hexdigest()`. Skill source = current `qor-audit/SKILL.md` bytes.
   - If prior artifact exists and prior `target_content_hash` matches current hash: emit advisory line "Plan unchanged since prior audit (verdict: <V>)"; record short-circuit event to Process Shadow Genome (severity-1, type `audit_short_circuit`); skip Steps 1-7; Step Z still writes a fresh artifact carrying the same verdict and a new `target_content_hash` field for the next invocation; report "Required next action: amend plan per prior findings, then re-run /qor-audit."
   - If no prior artifact OR hash mismatch: proceed normally.

2. New `### Step 0.6: Pre-audit lints (Phase 45 wiring — #42)` between Step 0.5 and Step 1:

   - Invoke `python -m qor.scripts.plan_text_consistency_lint --check <plan_path>` via subprocess; capture stdout/stderr and exit code.
   - Findings are WARN-only this phase: do not VETO on lint exit 1. Capture findings list (empty when exit 0) into local var for Step Z payload field `plan_text_consistency_lint_findings`.
   - Render findings under audit-report `## Process Pattern Advisory` block when non-empty (alongside existing veto-pattern advisory). Cite SG-039.

3. New sub-pass under Step 3 — "Self-Targeting Remediation Pass" (Phase 45 wiring — #44), inserted before Section 4 Razor Pass:

   - Read plan `originating_remediation` from current plan's top-matter or `plan.json` gate artifact.
   - When set: the Judge manually applies the discipline this plan introduces against this plan itself. Pseudo-code reference: read plan body, locate the discipline definition (lint contract / new SG entry / new gate), run that discipline against the plan body in the Judge's head. Findings produced this way map to existing finding categories (`specification-drift` is the typical landing).
   - When absent: skip the sub-pass; render a single line "Self-Targeting Remediation Pass: skipped (no originating_remediation declared)."
   - VETO posture: any finding from this pass uses normal Step 3 verdict semantics.

4. Amend Step Z payload construction to include the three new fields. `target_content_hash` always populated; `originating_remediation` mirrored from plan artifact when present (else null); `plan_text_consistency_lint_findings` populated from Step 0.6 (else null).

**`qor/skills/sdlc/qor-plan/SKILL.md`** Step 5 review checklist gains one bullet:

```
- [ ] Plan asserts the same command, dependency, or filesystem path identically at every site where it appears (run `python -m qor.scripts.plan_text_consistency_lint --check <plan-path>` to verify).
```

Step Z payload construction documented to include `originating_remediation` when the plan declares it in top-matter.

### Unit Tests

- `tests/test_audit_schema_v_n.py`:
  - `test_audit_schema_accepts_target_content_hash_string` — payload with valid 64-hex `target_content_hash` validates clean.
  - `test_audit_schema_accepts_target_content_hash_null` — null value accepted.
  - `test_audit_schema_rejects_target_content_hash_invalid_pattern` — 50-char or non-hex string rejected.
  - `test_audit_schema_accepts_originating_remediation_string_or_null` — both shapes pass.
  - `test_audit_schema_accepts_lint_findings_empty_or_populated` — `[]` and a populated finding both validate.
  - `test_audit_schema_unchanged_for_pre_phase_45_payloads` — payload that omits all three fields still validates.

- `tests/test_plan_schema_originating_remediation.py`:
  - `test_plan_schema_accepts_originating_remediation_string` — string value validates.
  - `test_plan_schema_accepts_omission` — payload without the field validates.
  - `test_plan_schema_rejects_non_string_value` — integer / array values rejected.

- `tests/test_audit_hash_short_circuit.py`:
  - `test_short_circuit_returns_prior_verdict_on_hash_match` — given a prior audit artifact with `target_content_hash == sha256(plan + skill)`, the next `/qor-audit` invocation in the same session reuses the prior verdict and writes a fresh artifact carrying the same verdict; second-write artifact's `target_content_hash` equals the freshly-computed value.
  - `test_short_circuit_skipped_on_hash_mismatch` — given a prior artifact with different `target_content_hash`, audit runs all passes (mock `_run_passes` to confirm invocation).
  - `test_short_circuit_skipped_on_no_prior_artifact` — clean session: audit runs full sweep.
  - `test_short_circuit_emits_shadow_event_on_match` — assert one severity-1 `audit_short_circuit` event written via `shadow_process.emit_event` (mocked).

- `tests/test_audit_self_targeting_pass.py`:
  - `test_self_targeting_pass_skipped_when_no_originating_remediation` — plan without the field; audit report contains the skip-line; no extra findings.
  - `test_self_targeting_pass_runs_when_originating_remediation_set` — plan with `originating_remediation: "docs/research-brief-X.md"`; the Judge's report carries a "Self-Targeting Remediation Pass" header section even when no findings result.
  - `test_self_targeting_pass_findings_route_to_specification_drift` — when the pass produces findings, they map to `findings_categories: ["specification-drift"]` in Step Z payload (when overall verdict becomes VETO).

---

## Phase 3: Doctrine — SG-039 entry + governance §10.6 cross-reference

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` — append SG-039 entry below SG-038.
- `qor/references/doctrine-governance-enforcement.md` — append §10.6 "Plan-content short-circuit and self-targeting passes (Phase 45)" between current §10.5 and §11.
- `tests/test_doctrine_sg_039_present.py` — NEW. Asserts SG-039 anchor exists with required fields (countermeasure, verification hint, source incident).

### Changes

**`qor/references/doctrine-shadow-genome-countermeasures.md`** — append after SG-038 block (before `## SG-InfrastructureMismatch`):

```markdown
## SG-039: prose-boundary precision drift on same-operation specifications

A plan asserts the SAME operation (a CLI invocation, a dependency name, a filesystem path) differently at MULTIPLE sites: §CI Commands says `cargo test --features X`; §Unit Tests says `cargo test --features Y`; §Decisions says `cargo test`. The implementer follows whichever copy they read first; the operator never realizes the divergence until a test fails or a wrong path is materialized.

Distinct from SG-038 (which targets numerical / enumeration drift in prose vs code blocks); SG-039 targets command/dep/path drift across same-operation invocations regardless of prose-vs-code framing.

**Countermeasure** (Phase 45): runnable lint at `qor/scripts/plan_text_consistency_lint.py` invoked at `/qor-plan` Step 5 (operator review) and `/qor-audit` Step 0.6 (Pre-audit lints, WARN-only). Detects 5 operation kinds: cargo_test, cargo_build, python_module, python_script, filesystem_path. CLI: `python -m qor.scripts.plan_text_consistency_lint --check <plan-path>`.

**Verification hint**: lint exits 1 with stderr describing each drift finding (operation kind, line numbers, raw text). Operator either canonicalizes a single site and edits others to match, or amends the plan to acknowledge intentional difference (e.g., split into distinct invocations with different operation targets — V2 identity-grouping deferred to GH #46).

**Source incident**: COREFORGE consumer workspace session 2026-05-08T1610-21dfe5; 3 consecutive VETOs across 2 plans on this signature. Filed upstream as GH #42, #43, #44, #45, #46. V1 lint sealed at COREFORGE META_LEDGER #206; ported upstream in this phase.
```

**`qor/references/doctrine-governance-enforcement.md`** — append after §10.5:

```markdown
## §10.6 Plan-content short-circuit and self-targeting audit pass (Phase 45)

### Plan-content short-circuit (#45)

`/qor-audit` Step 0.4 reads the prior audit artifact for the current session. If `prior_audit.target_content_hash == sha256(current_plan_text + sha256_of_skill_source)`, the audit short-circuits: prior verdict carried forward, no new ledger entry beyond the gate-artifact write, severity-1 `audit_short_circuit` event emitted to the Process Shadow Genome.

Joint hash with skill source means: amendments to the audit skill itself invalidate the cache (a freshly amended audit pass should re-evaluate even if plan text is byte-identical).

### Self-targeting remediation pass (#44)

When a plan declares `originating_remediation` in top-matter (mirrored to `plan.json`), `/qor-audit` Step 3 runs an additional adversarial sub-pass: the Judge manually applies the not-yet-runnable discipline this plan introduces against this plan itself. Findings route to existing finding categories (typically `specification-drift`). Plans that do not declare `originating_remediation` skip this pass with an explicit "skipped" line in the report.

Both mechanisms are advisory at the gate level and do not require operator override; they reduce wasted audit cycles and close the framework's "self-application blind spot" surfaced in COREFORGE's session 2026-05-08.
```

### Unit Tests

- `tests/test_doctrine_sg_039_present.py`:
  - `test_sg_039_anchor_exists` — opens `doctrine-shadow-genome-countermeasures.md`, asserts `## SG-039:` substring present.
  - `test_sg_039_block_has_countermeasure_and_verification_hint` — block between `## SG-039:` and the next `## SG-` or `## ` heading contains both literal substrings `**Countermeasure**` and `**Verification hint**`.
  - `test_sg_039_cites_lint_module_path` — block contains literal `qor/scripts/plan_text_consistency_lint.py`.

---

## CI Commands

- `python -m pytest tests/test_plan_text_consistency_lint.py -v` — Phase 1 lint behavior tests.
- `python -m pytest tests/test_audit_schema_v_n.py tests/test_plan_schema_originating_remediation.py -v` — Phase 2 schema tests.
- `python -m pytest tests/test_audit_hash_short_circuit.py tests/test_audit_self_targeting_pass.py -v` — Phase 2 audit-skill behavior tests.
- `python -m pytest tests/test_doctrine_sg_039_present.py -v` — Phase 3 doctrine tests.
- `python -m pytest -x` — full suite green precondition for substantiate.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase45-audit-hardening-and-plan-text-lint-v1.md` — self-application of the new lint to this plan (must exit 0).
- `python -m qor.scripts.ledger_hash` — Merkle chain integrity verification before substantiate.
