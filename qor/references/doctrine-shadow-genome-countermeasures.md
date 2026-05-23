# Doctrine: Shadow Genome Countermeasures

Canonical inventory of recurring failure patterns surfaced during audit tribunals and the mechanical countermeasures that prevent their recurrence. Cited by `qor/skills/sdlc/qor-plan/SKILL.md` Step 2b (Grounding Protocol) and consulted during `/qor-audit` adversarial sweeps.

Each entry names the failure pattern, the countermeasure rule, and a verification hint (grep/read/test) an agent can run to detect the antipattern.

## SG-016: generic-convention paths without grounding

Writing `src/migrations/versions/` because "most repos use that" without checking `alembic.ini` or `ls tests/` or `ls infra/`.

**Countermeasure**: Before citing any file path, run the specific grep/read that proves the path exists in this repo. Tag unverified paths with `{{verify: <mechanism>}}` in the draft pass.

**Verification hint**: `ls <proposed_root>` or `grep <symbol> --include=*.toml` before the plan cites a path.

## SG-017 / SG-020: inventing security controls without surveying existing mechanism

Claiming "role-based privilege" or `SECURITY DEFINER` enforces tenant isolation without reading the schema or existing policies.

**Countermeasure**: Grep the existing schema/code for the concrete security mechanism before proposing one. If the mechanism is absent, state that clearly — do not invent one that sounds plausible.

**Verification hint**: `grep -rn "SECURITY DEFINER\|REVOKE\|RLS_POLICIES" src/` before any security claim.

## SG-019: CLI flag portability assumption

Assuming `-k` works on both `ruff` and `mypy` because pytest accepts it. Tool CLIs disagree on flag semantics.

**Countermeasure**: Read each tool's `--help` output before citing any flag. Do not generalize across tool families.

**Verification hint**: `<tool> --help | grep <flag>` for every flag cited.

## SG-021: multi-layer edit compression

Writing "add to `RLS_POLICIES`" in a plan, which compresses "edit these 4 files" into a single verb that hides which files actually receive the edit.

**Countermeasure**: Enumerate every file that receives the edit before writing the verb. Map "add to X" → "edit `path1.py` line N; edit `path2.py` line M; ..." with grep evidence.

**Verification hint**: `grep -rn "<target_symbol>" --include=*.py` produces the file list; the plan disposes of each.

## SG-032: batch-split-write coverage gap

Lookup-table-based write-back (e.g., `src_map.get(e["id"])`) drops records created mid-cycle. Newly minted records have no prior identity in the lookup and silently fall through the filter.

**Countermeasure**: Either (a) classify records at creation time with explicit file/bucket assignment; or (b) add a default bucket in the split for unmatched records. Never rely on a post-hoc lookup to assign records that didn't exist when the lookup was built.

**Verification hint**: review-time question — "can any record in this batch have no prior identity in the lookup?" If yes, the plan must specify the fallback. Source incident: Phase 14 v2 (Entry #32 V-1).

## SG-033: positional-to-keyword breakage

Changing a function signature from `(x, y=None)` to `(x, *, y=None)` (keyword-only) without updating existing positional callers. Runtime breaks silently until called.

**Countermeasure**: Before introducing `*` in a signature, grep all call sites (production + tests) and update positional calls to keyword form in the same commit. "Existing body unchanged" does not mean "existing callers unchanged."

**Verification hint**: `grep "<fn_name>(" --include=*.py` after the signature change. Enforced by `tests/test_shadow_genome_doctrine.py::test_no_positional_calls_to_keyword_only_functions` (AST-based). Source incident: Phase 14 v2 (Entry #32 V-2).

## SG-034: AST walker node-family omission

AST-based code analysis walkers that check only `ast.FunctionDef` miss `ast.AsyncFunctionDef`; walkers that count `Call.args` by length miss `ast.Starred` unpacking. Either omission produces false positives or false negatives.

**Countermeasure**: Enumerate every relevant node family: `FunctionDef + AsyncFunctionDef`; `Call.args` filtered for `Starred`; `Call.func` dispatched between `Name` and `Attribute`. A walker that misses a family produces unreliable results.

**Verification hint**: ast-based tests should include a Rule-4 negative-path test with each family (e.g., `test_star_unpack_call_not_flagged`, `test_async_keyword_only_functions_detected`). Source incident: Phase 15 v1 (Entry #36 V-1 + V-4).

## SG-035: doctrine-content test unanchored

Tests asserting `"keyword-only" in body` pass when the doctrine section they claim to verify is missing entirely but the keyword co-occurs elsewhere. Violates W-1 literal-keyword discipline.

**Countermeasure**: Anchor keyword checks to the section header (regex proximity or markdown header parsing). A doctrine test that passes with its subject section removed does not enforce what it claims.

**Verification hint**: use `re.search(r"<SG-ID>.{0,500}<keyword>", body, re.DOTALL)` or parse headers. Include a negative-path test (e.g., `test_proximity_anchor_fails_when_section_missing`) that strips the section and proves the test fails. Source incident: Phase 15 v1 (Entry #36 V-2).

## SG-036: doctrine adoption grace period

A doctrine codified in phase N does not become automatically load-bearing in phase N+1 unless the author treats it as active. "I'll verify during implementation" is a deferral, not compliance. The Grounding Protocol requires inline citation at plan-authoring time, not implementation time.

**Countermeasure**: Treat newly codified doctrine as active immediately. Run all grep/read verifications inline with date-stamped provenance. No grace period.

**Verification hint**: plan body contains phrases like "grounded via `wc -l`" or "verified 2026-MM-DD" for every file-size/phrase-location claim. Source incident: Phase 16 v1 (Entry #40 V-1).

## SG-037: knowledge-surface drift

Doctrine tests anchored to a single file produce false negatives when refactoring moves knowledge across files. The test asserts `"phase/" in SKILL_A.read_text()`; refactor extracts the content to a companion references file; test fails even though the knowledge surface was preserved.

**Countermeasure**: Doctrine tests must check the combined knowledge surface (skill + declared companion references), not a single file. When a skill declares its companions (via `Read:` pointers or `See <path>` citations), tests should read the union.

**Verification hint**: test reads `skill_body + extensions_body` before asserting. When a skill moves content to a reference file, update the associated doctrine tests in the same commit. Source incident: Phase 16 Track C refactor (Entry #42 implementation note).

## SG-038: prose-code mismatch in plans

A plan document encodes the same spec in two places: prose descriptions and code blocks. These drift independently when the author edits mid-draft. Prose says "test covers 11 IDs"; code block lists 9; implementer following the code produces partial coverage while prose claims full.

**Countermeasure**: When a plan updates a list, enumeration, or count, grep the plan for every occurrence of that element and update all copies in lockstep. Prose, code blocks, and success criteria must cite the same values.

**Verification hint**: Judge cross-checks prose claims against code blocks during audit; any mismatch is VETO-grade. Optional future enforcement: lint plans for prose+code consistency on named enumerations. Source incident: Phase 17a v1 (Entry #44 V-1).

## SG-InfrastructureMismatch: plan claims contradict current repository infrastructure

A plan references filesystem paths, gate artifact glob patterns, event types, cross-module function signatures, or skill-step anchors that current code does not actually provide. Plan-internal consistency passes (prose matches code blocks, tests match implementation) but plan-to-infrastructure alignment fails silently. The defect only surfaces at implement-time or (worse) at ship-time when the intended behavior is mechanically impossible.

**Source incident**: Phase 36 Pass 4 V10. Original `plan-qor-phase36-planaudit-loop-countermeasures.md` built a stall-detection mechanism on the assumption that `.qor/gates/<sid>/audit*.json` globbing would yield multiple audit artifacts per session. Verified against actual code: `gate_chain.write_gate_artifact` writes singleton and overwrites on re-emission. The entire mechanism would have shipped as dead code. The Judge missed this across four audit passes because verification was limited to plan-internal consistency.

**Countermeasure** (codified in Phase 37): `/qor-audit` gains a seventh adversarial pass — Infrastructure Alignment Pass — that grep-verifies every plan claim against current repository code before PASS verdict. Violations map to the `infrastructure-mismatch` finding category (Phase 37 `findings_categories` enum). `/qor-plan` Step 2b Grounding Protocol also gains an infrastructure alignment sub-check: every `{{verify: <claim> }}` tag that survives to plan submission must be resolved before audit can clear it.

**Verification hint**: for every filesystem path cited, run `ls -la <path>` or `git ls-files <path>`. For every glob pattern, verify against a live session's gate directory shape. For every event type, grep `qor/gates/schema/shadow_event.schema.json` for the literal enum value. For every cross-module function cited, `grep -n "def <name>" <module>`. Unresolved → VETO.

## Phase 24-26 narrative SG entries (see `docs/SHADOW_GENOME.md`)

The following pattern IDs were surfaced as narrative Shadow Genome entries during audit tribunals in Phases 24, 25, and 26. Promotion into full structured countermeasure form (with grep/test verification hint) is queued; in the meantime, citing the pattern by ID in a plan or audit report references the narrative entry in `docs/SHADOW_GENOME.md`.

- **SG-Phase24-A**: cumulative razor creep in CLI harness (additive edits to an already-over-limit file without a companion refactor). Mitigation shipped: Phase 24 `/qor-refactor` extracted `qor/install.py`.
- **SG-Phase24-B**: unsafe deserializer defaults (plan introduces YAML parsing without naming `yaml.safe_load`). Mitigation shipped: `tests/test_yaml_safe_load_discipline.py` scans `qor/` and `tests/**/*.py` (widened in Phase 25).
- **SG-Phase24-C**: reflexive dependency introduction for trivial serializers (proposing `tomli_w` when a <15-line vanilla writer suffices). Mitigation shipped: dependency-shape test locks `pyproject.toml` runtime deps.
- **SG-Phase24-D**: remediation target mismatch (running `/qor-refactor` to address plan-text VETO grounds). Mitigation shipped in Phase 26: per-ground `**Required next action:**` directives in audit reports (`qor/references/doctrine-audit-report-language.md`).
- **SG-Phase25-A**: A08 discipline scope gap (lint test root not covering new usage directory). Mitigation shipped: widened walk + planted-call negative test.
- **SG-Phase25-B**: ghost feature via metadata-only declaration (frontmatter flag without backing behavior). Mitigation shipped: canonical section markers + lint (`test_tone_skill_frontmatter.py`) + pinned example (`test_tone_rendering_example.py`).

No narrative SG entries surfaced during Phase 26 audit tribunals; pattern `repeated_veto_pattern` is a Shadow Genome *event* (structured, in `PROCESS_SHADOW_GENOME.md`), not a narrative failure pattern.

## SG-SkillProtocolBypass: skill markdown executed without runtime provenance

Skills are markdown documents under `qor/skills/**/SKILL.md`. Helper functions (`gate_chain.write_gate_artifact`, `intent_lock.capture`, etc.) accept payloads from any caller. Pre-Phase-52 there was no runtime check that a skill protocol was actually executed vs a hand-written audit/seal pasted into the ledger.

**Source incidents**: Phases 46, 48, 49, 50 (one operator session). All sealed without writing `.qor/gates/<sid>/*.json` artifacts. `git log --diff-filter=A --name-only --all -- ".qor/gates/"` returned 0 hits across the entire repo history pre-Phase-52.

**Countermeasure** (codified Phase 52): `gate_chain.write_gate_artifact` requires `QOR_SKILL_ACTIVE=<phase>` env var matching the `phase` argument. `qor.reliability.gate_chain_completeness.check()` walks ledger SESSION SEAL entries and asserts all four gate artifacts exist for sealed phases ≥ 52. Wired into `/qor-substantiate` Step 7.8 + `.github/workflows/ci.yml` `gate-chain-completeness` job (blocks PR merges to main).

**Verification hint**: `git log --diff-filter=A --name-only --all -- ".qor/gates/"` should be non-empty for any sealed phase ≥ 52. CI job `gate-chain-completeness` blocks merge on violation. Bypass via `QOR_GATE_PROVENANCE_OPTIONAL=1` is for tests only (autouse fixture in `tests/conftest.py`).

## SG-VacuousLint: self-exempting cutoff in commit-walking lints

A lint that walks `git log` and applies a "phase >= N: continue # grandfathered" cutoff at the same N where the lint was introduced is structurally vacuous on first run — there are no inputs that could fail. The lint passes by definition until a violator commits *after* the cutoff in some future phase.

**Source incident**: Phase 49's `tests/test_attribution_tiered_usage.py` lines 128, 147 (`if phase_num < 49: continue`). Authored at Phase 49 itself; only Phase 49 commits in scope at write time, all of which the same author wrote to comply.

**Countermeasure** (codified Phase 52): every cutoff lint MUST be paired with a fixture-based negative-path test that fabricates a synthetic violating input and asserts the lint catches it. The negative-path test does NOT walk real git history — it constructs a synthetic input and exercises the lint regex/parser directly. See `tests/test_attribution_tiered_negative_paths.py` for canonical pattern.

**Verification hint**: for any test using `if phase_num < N: continue # grandfathered`, search the same test file (or its companion `_negative_paths.py`) for a sibling test with a fabricated synthetic input (no `git log` invocation). If absent, the lint is presence-only on its own subject.

## SG-RecursiveBashInjection: plan that forbids shell-interpolation reintroduces it

A plan whose `non_goals` or doctrine citation forbids `python -c "..."${VAR}"` patterns (per SG-Phase47-A) but whose `## Changes` section specifies bash that interpolates shell variables into a `python -c` literal. The pattern is recursive: the plan's text correctly identifies the anti-pattern and then commits it.

**Source incident**: Phase 51 WIP (`docs/plan-qor-phase51-ssdf-tag-emission.md`) §"Source surfaces" §2 specified `python -c " ... json.loads('''${FILES_TOUCHED_JSON}''') ... "`. Plan was VETO'd retroactively by /qor-audit before merge.

**Countermeasure** (codified Phase 52): `/qor-audit` Step 3 Infrastructure Alignment Pass adds an explicit grep against the plan body: `python -c "[^"]*\$\{` patterns; any hit is an automatic VETO with `infrastructure-mismatch` category citing SG-RecursiveBashInjection. Implemented as a wiring test (`tests/test_substantiate_step_7_4_ssdf_emission.py::test_step_7_4_does_not_use_python_c_shell_interpolation`).

**Verification hint**: `grep -E 'python -c "[^"]*\$\{' docs/plan-qor-phase*.md` should be empty for any post-Phase-52 plan. If any hit, the plan recursively reintroduces SG-Phase47-A and must be amended.

## SG-PromptInjection-A: governance markdown read into LLM context without canary scan

`/qor-audit`, `/qor-implement`, and `/qor-substantiate` read `docs/ARCHITECTURE_PLAN.md`, `docs/META_LEDGER.md`, `docs/CONCEPT.md`, and the current plan file verbatim into LLM context as part of state verification. When the trust boundary spans multiple authors (open-source PRs, CI-driven invocations, multi-author working directories), an attacker with write access to any of these files can embed instructions that subvert the audit. Pre-Phase-53 there was no canary scan and no commit-time forbid rule for governance-classified resources; the only defense was operator vigilance and the host-LLM provider's own injection resistance.

**Source incident**: Phase 53 research brief (`docs/research-brief-prompt-logic-frameworks-2026-04-30.md` §A.LLM01) classified the gap as HIGH. Self-application Phase 4 of the Phase 53 plan exercises the new canary scan against the plan, brief, and doctrine to verify the meta-coherence property "the system that defends against prompt injection does not itself contain a prompt injection."

**Countermeasure** (codified Phase 53): `qor.scripts.prompt_injection_canaries` exposes a `CANARIES` tuple and `scan(content) -> list[CanaryHit]` API. `/qor-audit` Step 3 invokes the CLI argv-form and VETOs on any non-zero exit with `findings_categories: ["prompt-injection", ...]`. `qor/policies/owasp_enforcement.cedar` carries a parallel `forbid` rule on `Code::"governance"` resources whose `has_prompt_injection_canary` attribute is True; the attribute is computed by `qor/policy/resource_attributes.compute_governance_attributes`. Two enforcement points (audit-time + commit-time), single source of truth (`CANARIES`).

**Verification hint**: `python -m qor.scripts.prompt_injection_canaries --files docs/ARCHITECTURE_PLAN.md docs/META_LEDGER.md docs/CONCEPT.md docs/plan-qor-phase*.md` should exit 0 for any clean repository state. If any hit, the audit refuses to PASS and the operator must amend the offending file. Audit-pass insertion point: `/qor-audit` SKILL.md Step 3 `#### Prompt Injection Pass` immediately before `#### Security Pass (L3 Violations)`. Per `qor/references/doctrine-prompt-injection.md`.

## SG-PreAuditLintGap-A: presence-only test descriptions + infrastructure-mismatch citations recur across plan authoring

Cross-session observation: Phase 53/54/55 first audits each issued Pass-1 VETO with the same finding combination — `test-failure` (presence-only test descriptions disguised as "co-occurrence behavior invariants") + `infrastructure-mismatch` (hedged or stale Python module / file path citations). The doctrine that should have caught these (Phase 46 test-functionality + Phase 37 infrastructure-alignment audit pass) only fires at Step 3 of `/qor-audit`; the Pass-1 VETO consumed an audit cycle each time the operator could have been warned earlier.

**Source incidents**: Phase 53 Pass 1 (5 presence-only tests + 3 infrastructure mismatches), Phase 54 Pass 1 (3 + 1), Phase 55 Pass 1 (3 + 1). Same operator authoring style across three consecutive phases; doctrine alone insufficient.

**Countermeasure** (codified Phase 55): two pre-audit lints invoked at `/qor-audit` Step 0.6 (and `/qor-repo-audit` Step 0.6 as best-effort): `qor.scripts.plan_test_lint` greps plan files for the four canonical presence-only patterns (substring-presence, section-exists, substring-in-file, path-exists); `qor.scripts.plan_grep_lint` walks plan files for cited Python module / skill paths and verifies each resolves at HEAD (excluding paths declared as NEW in Affected Files blocks). Both WARN-only — the existing Test Functionality Pass and Infrastructure Alignment Pass at Step 3 issue binding VETOs; the lints catch these classes earlier so the Governor can amend without consuming an audit cycle.

**Verification hint**: `python -m qor.scripts.plan_test_lint --plan docs/plan-qor-phase*.md` should exit 0 with no stderr warnings for any plan ready for audit. Same for `plan_grep_lint`. Pre-Phase-55 plans are not retroactively scanned (forward-only enforcement).

## SG-SecretLeakAtSeal-A: dormant Cedar attribute without scanner

Historical risk: the Cedar `forbid` rule on `Code::"production"` keyed on `resource.has_hardcoded_secrets` has existed since Phase 23, but no scanner drove the boolean. Pre-Phase-56 seal commits could have committed secrets undetected; the policy enforced nothing.

**Source incident**: Phase 56 audit gap discovery (research brief `docs/research-brief-prompt-logic-frameworks-2026-04-30.md` Priority 6 / NIST AI 600-1 §2.10 / OWASP LLM06).

**Countermeasure** (codified Phase 56): `qor.scripts.secret_scanner` provides regex-pattern detection (frozen `PATTERNS` tuple) with literal-substring `_ALLOWLIST` for the known false-positive class (Cedar/schema attribute names). `compute_production_attributes(path, content)` in `qor/policy/resource_attributes.py` returns the `has_hardcoded_secrets` boolean for the Cedar evaluator. `/qor-substantiate` Step 4.6.5 invokes `python -m qor.scripts.secret_scanner --staged --out dist/secrets.findings.json || ABORT` before seal — fail-closed BLOCK on any finding. Findings JSON follows gitleaks v8 schema; redacted match form (`<first4>...<last2>`) prevents leakage in the findings file itself.

**Verification hint**: `python -m qor.scripts.secret_scanner --files <path>...` should exit 0 with empty findings JSON for clean files; exit 1 with populated JSON for files containing secrets. Retroactive remediation of historical seals is operator-driven (e.g., `gitleaks detect --source . --log-opts="--all"` for full-history sweep). Forward-only enforcement starting Phase 56.

## SG-BareExceptionSwallowsSignals-A: `except BaseException` swallows SIGINT/SystemExit

Historical risk class: a `try/except BaseException` clause (with or without `# noqa: BLE001`) catches `KeyboardInterrupt` and `SystemExit` along with the intended `Exception` class. Operators lose Ctrl-C control over the running process. With long-timeout subprocess calls, indefinitely-spinning hooks, or daemon-style worker loops, the only escape is SIGKILL — which bypasses cleanup, leaves files in inconsistent states, and obscures the original failure cause from logs.

**Source incident**: Phase 57 audit of PR #12 `feat/b24-gate-written-hooks` (Entry #186 VETO). The PR's `gate_hooks._invoke_hook_safely` and `gate_chain._fire_gate_written_hook` both used `except BaseException` (with `# noqa: BLE001`). With the proposed 30-second per-subprocess-hook timeout AND swallow-on-callable-hook, a misbehaving Python entry-point hook could spin indefinitely with SIGKILL the only escape. PR #12 design rationale was correct (hook errors must never break the authoritative write path) but the catch was over-broad.

**Countermeasure** (codified Phase 57): use `except Exception` (NOT `except BaseException`) anywhere a "swallow and log" pattern is intentional. Reserve `BaseException` only for cleanup-then-reraise patterns where the cleanup itself must run regardless of signal class:

```python
# CORRECT: swallow + log; signals propagate
try:
    user_callable()
except Exception:
    log_error()

# CORRECT: cleanup-then-reraise (use sparingly; usually try/finally is enough)
try:
    user_callable()
except BaseException:
    cleanup()
    raise

# WRONG: signals swallowed; operator loses Ctrl-C
try:
    user_callable()
except BaseException:  # noqa: BLE001
    log_error()
```

Phase 57 anchors the discipline with two regression tests:
- `tests/test_gate_hooks_swallow.py::test_swallow_uses_except_exception_not_baseexception` — AST-anchored static check that the `_invoke_hook_safely` function source has `Exception` (not `BaseException`) in any `except` clause.
- `tests/test_gate_hooks_sigint_propagates.py::test_keyboard_interrupt_in_callable_hook_propagates` and `::test_system_exit_in_callable_hook_propagates` — behavioral check that `KeyboardInterrupt` and `SystemExit` raised inside hook callables propagate through dispatch.

**Verification hint**: search source for `except BaseException` excluding cleanup-then-reraise patterns: `rg "except BaseException" qor/ --type py | grep -v "raise"` should return zero hits in observer/swallow paths. False positives in `try/finally`-equivalent reraise patterns are acceptable.

## SG-DocSurfaceUncovered-A: skill / script / doctrine / schema changes without system-tier doc update

Historical risk class: a seal commit modifies skill bodies, helper scripts, doctrines, or gate schemas but does not update any of the four system-tier docs (`docs/SYSTEM_STATE.md`, `docs/operations.md`, `docs/architecture.md`, `docs/lifecycle.md`). Operators reading the SDLC narrative on a future date see stale documentation and either misunderstand the current state or have to reconstruct it from the META_LEDGER seal entries directly. /qor-substantiate Step 6 mandates SYSTEM_STATE.md update, but pre-Phase-58 the seal flow had no structural enforcement — only operator review of the PR caught the omission.

**Source incident**: Phase 57 substantiate cycle (2026-05-01). Phase 57 shipped the gate_written observer channel, modified `qor/scripts/gate_hooks.py` (NEW), `qor/scripts/gate_chain.py`, `qor/references/doctrine-hook-contract.md` (NEW), and the substantiate skill body (existing Step 4.6.5 was unchanged but the new public API surface should have surfaced in operator-facing docs). All three system-tier docs (SYSTEM_STATE, operations, architecture) were initially omitted; the operator caught the gap on PR review and required a follow-up commit (`9aa1d84` "docs: phase 57 surface coverage + B23 future-phase note") that added the entries.

**Countermeasure** (codified Phase 58):
1. **Procedural-fidelity check at substantiate Step 4.6.6** (`qor/scripts/procedural_fidelity.py:_detect_doc_surface_coverage`): static-analysis pass over the implement-gate `files_touched` set. Skill / script / doctrine / schema changes without at least one system-tier doc update emit a severity-2 `doc-surface-uncovered` Deviation. WARN posture in v1 (no abort); future phase may tighten to BLOCK once false-positive rate is characterized.
2. **SYSTEM_STATE drift-prevention test** (`tests/test_system_state_phase_coverage.py`): forward-only enforcement at every test run. Every META_LEDGER `Phase N feature substantiated` entry must have a corresponding `## Phase N (vX.Y.Z)` heading in `docs/SYSTEM_STATE.md`, modulo the explicit `_NO_SEAL_PHASES` set (phases 42-44 absorbed by Phase 41+45; Phase 51 absorbed by Phase 52).
3. **Severity-2 events** appended to the Process Shadow Genome (`docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`) per deviation, providing a JSONL audit trail.

Phase 58 also backfilled SYSTEM_STATE.md entries for 12 sealed phases (41, 45-50, 52-56) that had accumulated drift pre-Phase-58. Forward-only enforcement starts at Phase 58.

**Verification hint**: `python -m qor.scripts.procedural_fidelity --session "$SESSION_ID"` after each implement gate write should emit no `doc-surface-uncovered` deviations for any seal commit touching skill / script / doctrine / schema surface. `python -m pytest tests/test_system_state_phase_coverage.py` enforces no future seal can land without the corresponding SYSTEM_STATE.md entry.

## SG-PrematureSolutioning-A: spark becomes solution before problem is framed

Historical risk class: an operator's spark of inspiration is structured as a solution shape (build a dashboard, ship a script, design a workflow) before the underlying problem is fully framed. Downstream planning then anchors on the solution shape; the actual problem (e.g., operational visibility, friction in workflow handoff, recurring incident class) is inferred from the solution rather than driving it. By the time `/qor-audit` pushes back, the plan has accumulated structural commitments to the wrong solution shape — premature decomposition has already split the work into tasks that match the inferred problem rather than the actual one.

**Source incident**: Issue #20 ("Future Concept: Add governed ideation readiness phase before research and planning") explicitly catalogs this and 7 other "natural unraveling points" — premature solutioning being the canonical case. The original Phase 58 plan (later renamed to Phase 59 in Phase 58's tech-debt wrap-up) was authored to introduce a structural countermeasure rather than relying on adversarial audit at Step 3 of `/qor-audit` to catch the pattern after-the-fact.

**Countermeasure** (codified Phase 59):
1. **`/qor-ideate` skill** at `qor/skills/sdlc/qor-ideate/SKILL.md`. Pre-research SDLC phase; advisory-gate posture matching Phase 8.
2. **Section 2 (Problem Frame) gate**: skill REFUSES to advance to Section 3 (Transformation Statement) until `problem_frame.affected_actors`, `problem_frame.failure_mode`, and `problem_frame.cost_of_failure` are all populated. Schema enforcement: `qor/gates/schema/ideation.schema.json` declares all three required.
3. **Section 7 (Options Matrix) gate**: skill REFUSES to advance to Section 8 (Governance Profile) until `options[]` contains ≥2 entries with at least one selected and rejection_reason populated for non-selected options.
4. **Predecessor recognition**: `gate_chain.check_prior_artifact` extension recognizes `ideation.json` as a valid prior for both `/qor-research` and `/qor-plan` phases. Hotfixes MAY skip ideation.
5. **Doctrine catalog**: `qor/references/doctrine-ideation-readiness.md` documents all 8 unraveling points with structural countermeasures.

The doctrine catalogs all 8 unraveling points (Premature Solutioning, Language Drift, Assumption Laundering, Scope Seepage, Research Asymmetry, Failure Blindness, Premature Decomposition, Validation Collapse) with the per-section guard mechanism that prevents each.

**Verification hint**: a hand-authored ideation artifact with `problem_frame: {}` (empty object) MUST fail schema validation against `qor/gates/schema/ideation.schema.json` with a `'affected_actors' is a required property` error. Tests at `tests/test_ideation_schema_validation.py::test_rejects_artifact_missing_required_field` enforce this.

---

## SG-PlanTextDrift-A — prose-boundary precision drift in plan markdown (Phase 67)

**Pattern**: same operation (command, dependency, filesystem path, env var, function signature) specified differently at multiple plan sites, where the divergence is byte-level and silent. Caught when a downstream audit pass surfaces one form as wrong while the alternate form remained unchallenged.

**Originating recurrence**: COREFORGE session 2026-05-08T1610-21dfe5, 3-VETO cycle on the same drift signature across 2 plans (META_LEDGER #200, #201, #203 in the consumer workspace).

**Countermeasure**: `qor/scripts/plan_text_consistency_lint.py` (sealed at Phase 55 from COREFORGE; wired upstream at Phase 67 GH #42) detects same-operation drift via stem extraction + grouping. Wired into `/qor-plan` Step 5 review checklist (operator self-check) and `/qor-audit` Step 0.6 (WARN-only pre-audit lint). Tolerance is zero: any drift in commands, dependencies, or paths returns exit 1 with the divergent sites named.

**Cross-reference**: Issue #42; SG-CitationDrift-A (Issue #56) catalogues a related cross-iteration citation-drift pattern targeted for a future phase.

---

## SG-CitationDrift-A — cross-iteration unverified citation drift (Phase 72)

**Pattern**: a Locked Decision (LD) cites sealed infrastructure (migration name, function signature, file:line, table schema, enum value, index/constraint name, env-var name, edge-function path) without an inline grep-evidence statement. The unverified citation enters the plan in iter-1 and survives across iterations because subsequent audits only diff-against-iter-N-1, never re-challenging LDs that were not amended in the current iteration. The drift remains silent until a downstream consumer (implementation, second auditor, runtime) trips on the mismatch.

**Originating recurrence**: Accountable-App `attribution-12g` plan, audit cycle 2026-05-13, iter-1 -> iter-3 audit chain. Iter-1 included a citation to a sealed migration column that did not match the actual schema; iter-2 audited the diff against iter-1 and did not re-grep the unchanged citation; iter-3 surfaced the mismatch via independent reviewer (SG-AuthorAuditMomentum-A), but the citation had already shaped two iterations of plan structure.

**Countermeasure P1** (`/qor-plan` Step 2 Infrastructure Citation Inventory): every LD citing sealed infrastructure MUST carry a paired grep-evidence statement of the form `git show <sealed-ref>:<path> | grep -nE '<pattern>' -> <exact observed text>`. Citations without paired evidence are Open Questions, not LDs, and block submission to `/qor-audit`.

**Countermeasure P2** (`/qor-audit` Step 3 Infrastructure Alignment Pass, iter-N>1 sub-section): on iterations after the first, the Judge re-walks the **full Locked Decision set** and grep-verifies every sealed-infrastructure citation, not just the diff-from-iter-N-1. Missing inline grep-evidence triggers immediate VETO with `infrastructure-mismatch` category, regardless of whether the LD was amended in the current iteration.

**Cross-reference**: Issue #56; SG-PlanTextDrift-A (Phase 67, Issue #42; same-iteration text-drift pattern -- distinct from this cross-iteration variant); SG-AuthorAuditMomentum-A (Phase 68; independent-reviewer countermeasure that exposed the iter-3 mismatch). Lint-extension complement (P4 -- heuristic plan_grep_lint hook for sealed-infrastructure citation patterns) deferred to a future phase.

---

## SG-ConcurrentLedgerRace-A — duplicate entries from concurrent federation append (Phase 76)

**Pattern**: META_LEDGER's sequential entry-numbering scheme (`Entry #N` allocated by reading the latest entry at append time) is fundamentally single-writer. Under concurrent federation append, two workers both read "latest is #N", both append "#N+1", and the ledger gets duplicate-numbered entries. The cryptographic chain survives (each worker's `previous_hash` is correctly anchored to what it saw) but human-readable structure breaks: downstream tooling that assumes sequential entries (audit viewers, badge_currency counter) over-counts or mis-renders.

**Originating recurrence**: cross-workspace federation observed Entries #16a/b, #17a/b, #18a/b each appearing twice from different concurrent sessions (Canonical Event Schema Extension #376 / Accountable Live Phase 01 #335 / Fix Migration Pipeline #332). The chain hashes linked forward correctly via per-entry `previous_hash`, but sequential numbering was corrupted. Earlier in the canonical Qor-logic META_LEDGER, Entries #109/#111/#113 also share a `previous_hash` from a pre-Phase-76 federation episode.

**Countermeasure** (`qor/scripts/entry_id.py` + `qor.reliability.seal_entry_check.check_previous_hash_uniqueness`, Phase 76 wiring): forward-only V1. New entries (Phase 76+) carry a content-addressable `Entry ID` derived from `SHA256(timestamp|phase|content_hash)[:12]` -- collision-resistant and coordination-free. `/qor-substantiate` Step 7.7 invokes `check_previous_hash_uniqueness(ledger_path, min_entry_num=207)` after seal write; two entries claiming the same `previous_hash` raise `SealEntryResult(ok=False, ...)` and the operator reconciles before publishing. The **previous_hash uniqueness** check is the structural detector for the concurrent-append race.

**Forbidden interpretation**: retroactive renumbering of past sealed entries (#1-#207) is structurally **prohibited**. The Merkle chain's immutability is the value proposition; any commit that rewrites past entry numbers or hashes is an audit-trail violation and must be reverted. Past sealed entries with duplicate-previous_hash instances (#109/#111/#113 plus the cross-workspace #16/17/18) remain in the ledger as documented residual; V2 operator-authorized reconciliation is the only path that may resolve them, and that V2 design must produce a forward-only reconciliation entry rather than rewriting past content. **Past sealed entries are grandfathered.**

**Cross-reference**: Issue #51; Phase 78 ideation packet `2026-05-14T2235-830921` selected Option 1 (content-addressable IDs + topological sort) with explicit forbidden-interpretation guards. Option 2 (session-scoped segments) and Option 3 (file-lock) rejected as overkill / federation-defeating. V2 follow-on: operator-authorized one-time reconciliation pass for past duplicates -- forward-only commit format.

**V2 stopgap** (Phase 91 wiring; GH #85): `qor-logic verify-ledger --tolerate-known-grandfathered` accepts chain-math failures iff the failing entries' `previous_hash` appears in the ledger's duplicate-`previous_hash` set AND the failing entry numbers are `<= --grandfather-cutoff` (default 207, matching `check_previous_hash_uniqueness`'s `min_entry_num`). Read-only verifier semantics — the ledger is not modified, so no operator-authorization protocol is needed in V1. Lets consumer workspaces (e.g., Accountable-App-3.0 per GH #85) ship clean `verify-ledger` gates immediately without rewriting past entries. The flag is OFF by default; the strict verifier remains the canonical gate unless the operator opts in. Tolerated failures emit `DISCLOSED_GRANDFATHERED Entry #N: tolerated SG-ConcurrentLedgerRace-A residual` on stdout (not stderr), do not contribute to the error count, and do NOT propagate TAINTED to downstream entries. Implementation: `qor.scripts.ledger_hash.find_grandfathered_entries(ledger_md, cutoff=207) -> frozenset[int]` enumerates the residual set; `verify(..., tolerate_known_grandfathered=True, grandfather_cutoff=207)` honors the flag. Real reconciliation that writes new entries (Options A/B from GH #85 — RECONCILIATION entry append; post-anchor pinning) is reserved for a future phase with operator-authorization protocol design.

---

## SG-HalfSealedClaim-A — substantiate seal claims gate coverage it does not have (Phase 75)

**Pattern**: an operator runs `/qor-substantiate` against a host whose archetype lacks the Python toolkit prerequisites the skill bakes in (TypeScript/Rust/Go/polyglot repos without `pyproject.toml`, `qor.scripts.*`, or `CHANGELOG.md` in Keep-a-Changelog form). Multiple gate steps silently fail or no-op. The operator hand-skips after the first failure. The resulting SESSION SEAL entry's Merkle hash anchors a **half-checked** state where only a subset of gates actually ran, but the entry body **claims coverage** the implementation does not have.

**Originating recurrence**: 2026-05-06 incident -- `Qor-logic Customer-App-3.0` (React 18 + bun + Supabase repo) during a security migration session. 8 of ~15 substantiate steps failed/skipped on the non-Python host. Session ended in a `SUBSTANTIATE DEFERRED` ledger entry rather than a seal -- preserving chain integrity but blocking the protocol from completing in the host repo without hand-authored seal (which itself defeats the automation).

**Countermeasure** (`qor/scripts/substantiate_capability.py` + `qor-logic substantiate-capability` CLI, Phase 75 wiring): each substantiate step declares its prerequisite in qor-substantiate SKILL.md's `## Step Prerequisites` table (predicate kinds `file:<path>`, `module:<dotted>`, `command:<binary>`). Operators run `qor-logic substantiate-capability` before invoking the skill to receive a markdown table of per-step prerequisite status (PRESENT / ABSENT + evidence path). The output is paste-able into the SESSION SEAL entry body so the seal explicitly cites which gates ran vs were skipped on the host archetype. Missing prerequisites emit `gate_skipped_prerequisite_absent` shadow events (severity 1; schema enum extended at Phase 75).

**Cross-reference**: Issue #38; Phase 76 ideation packet `2026-05-14T2216-a5f692` selected Option 1 (skill capability declaration) as smallest reversible step; Phases 2 (pluggable backends) and 3 (two-track skill split) deferred to V2/V3 pending operator demand signal from V1 deployment via Process Shadow Genome event counts.

---

## SG-FakeProgress-A — UI fake-jump progress without intermediate state (Phase 74)

**Pattern**: a UI element with progress semantics (progress bar, spinner, phase indicator, step list) animates from `style.width = '0%'` directly to `style.width = '100%'` with no intermediate writes while the backing operation runs silently for >2 seconds (often 20-60 seconds). The operator perceives the click as having done nothing; the progress bar appears frozen at 0%; on completion the bar jumps directly to 100% (or stays at 0% on error with no dismiss/retry control). Backing event streams (WebSocket / EventEmitter) often exist and emit per-phase events, but the UI does not subscribe and re-render.

**Originating recurrence**: FailSafe v5.1.0 Install QorLogic Skills card -- `install-skills-card.js` sets `progressBar.style.width = '0%'` at start; operator click fires `POST /api/actions/scaffold-skills`; backing pipeline runs 5 sequential phases (Python probe -> pip install -> per-host `qorlogic install` -> provenance verification -> hub refresh) over 20-60 seconds; modal shows frozen 0% throughout; `skills.install.progress` WebSocket events exist but the modal does not subscribe; bar jumps to 100% on completion. Two prior qor-audit PASS cycles (FailSafe META_LEDGER #361 + #362) missed the defect because the legacy Ghost UI Pass checked only handler presence, not live-feedback fidelity.

**Countermeasure** (`/qor-audit` Step 3 Ghost UI Pass, Phase 74 wiring): the Live-Progress Invariant sub-rule requires every progress-semantics UI element to (1) carry at least one intermediate state when the backing operation takes >2 seconds; (2) avoid the fake-jump pattern (`style.width = '0%'` -> `style.width = '100%'` with no intermediate writes); (3) subscribe modals with progress UI to the backing event stream and re-render on each event; (4) surface explicit dismiss/retry controls on terminal error states. Violations VETO with `ghost-ui` category, sub-tag `live-progress-fake`.

**Cross-reference**: Issue #58; FailSafe META_LEDGER #360 (debug report for the misattribution caused by the same async-vs-UI timing gap), #361/#362 (the two PASS audits that missed the defect), #366 (audit-VETO of the in-repo amendment that filed this upstream issue). Future V2: mechanical `qor/scripts/plan_live_progress_lint.py` heuristic at Step 0.6 pre-audit lint surface (deferred to follow-on phase pending V1 prose adoption).

---

## SG-FilterOrderInversion-A — pipeline filter stages composed out of dependency order (Phase 78)

**Pattern**: a function or method composes a candidate set through multiple filter stages and selects a winner. Each filter stage is individually correct by stage-by-stage review (Wave 2 multi-agent audit, qa-expert + qor-judge passes, or single-reviewer audit). Composition is wrong: stage N references a struct field that a separate `validate` / `check` / `verify` / `is_valid` function is supposed to enforce, but that validation is invoked **elsewhere in the codebase** rather than as a stage of the same pipeline. Candidates that violate the upstream invariant survive into stage N and can dominate selection over validity-respecting candidates. The defect is a **composition** defect, not a stage defect; stage-by-stage correctness review misses it because the question "is this stage correct?" passes for each filter individually while "did the dependency-graph topological sort actually run?" is never asked.

**Originating recurrence**: COREFORGE Skill-Forge V1 dispatcher (`src-tauri/src/synapse/skill_forge/dispatcher.rs`) sealed at COREFORGE META_LEDGER #209 with the pipeline `tier filter -> classification filter -> vendor filter -> cost score -> select lowest`. The validator (which separately rejects manifests violating 7 coherence rules + native-only-V1) was invoked elsewhere but **not before cost scoring inside `decide()`**. An invalid manifest with low cost could dominate selection over valid candidates with higher cost. Wave 2 review (qa-expert N4 + qor-judge P1) caught surface-level test coverage gaps and test fragmentation but missed the filter-order inversion because both reviewers asked "is each filter correct?" not "do the filters compose in dependency order?" Operator caught the defect during PR #82 merge review; commit `0999e47` moves the validator to the first filter stage and regression test `test_dispatch_skips_invalid_skill_and_selects_valid_candidate` locks the invariant.

**Countermeasure** (`/qor-audit` Step 3 Filter-Stage Ordering Coherence sub-pass, Phase 78 wiring): for any pipeline-shaped function (functional filter chains, sequential `let after_X = filter_X(...)` blocks, Python comprehension stacks, TypeScript `.filter().filter().reduce()`), the Judge runs the 4-step procedure: (1) identify each filter stage's preconditions; (2) identify each filter stage's invariants; (3) construct the **pipeline stage dependency graph** (stage N depends on stage M iff M enforces an invariant that N's correctness assumes); (4) verify the code execution order is a topological sort of the dependency graph. Any inversion -- stage N runs before stage M where N depends on M -- VETOes with `composition` category, sub-tag `filter-order-inversion`. When the missing precondition is an external-state assumption (e.g., "registry pre-validated by external pipeline"), the VETO uses `infrastructure-mismatch` category with the same sub-tag. Doctrinal precedent: structurally analogous to read-before-write checks in static analyzers, lifted to the pipeline-stage abstraction.

**Cross-reference**: Issue #47; COREFORGE META_LEDGER #209 (sealed defect), COREFORGE commit `0999e47` (operator fix), COREFORGE PR #82 merge review (detection event); doctrinally adjacent to Issue #44 (Wave 2 self-targeting remediation plan check -- shared blind-spot class). Future V2: mechanical `qor/scripts/plan_filter_stage_lint.py` AST helper across Rust/Python/TypeScript pipeline shapes (deferred to follow-on phase pending V1 prose adoption).

---

## SG-DocsBackloadedToSubstantiate-A — documentation lifecycle deferred to seal-time when authoring context is lost (Phase 79)

**Pattern**: `/qor-implement` has no documentation-authoring step. ARCHITECTURE_PLAN.md file-tree updates, architecture-doc additions, operations-doc entries, and schema-doc updates are all structurally deferred to `/qor-substantiate` Steps 4.7 (Documentation Integrity Check), 6 (SYSTEM_STATE.md sync), and 6.5 (Documentation Currency Check). By the time substantiation runs, the implementing agent has discarded the implementation-time context (which files changed, why, what they connect to, how the change interacts with surrounding modules). Substantiation's Step 6.5 currency check is WARN-only at `standard` tier and catches doc drift post-hoc; Step 4.6.6 procedural fidelity emits severity-2 shadow events but does not prevent the drift. Substantiation is structurally a **verification** gate, not an **authoring** phase; making it the primary authoring surface produces predictable doc-drift across sessions.

**Originating recurrence**: across 18+ META_LEDGER entries in a multi-session analytics program, ARCHITECTURE_PLAN.md file tree went stale after sub-plans 01a/b/c, 02a-i, 02a-iv, 02a-iii, 02a-vi, and 02a-ii each created new files -- the file tree still listed `[30+ edge functions]` as a placeholder rather than enumerating actual files. Migrations created `analytics_events`, `feature_flags`, `analytics_health_state`, `analytics_mirror_failures` tables and multiple SQL functions; no implement step updated any architecture or schema documentation. Substantiate Step 6.5 detected the drift as WARN-only after the implementing agent had already moved to the next sub-plan; the context for writing accurate docs was lost.

**Countermeasure** (`/qor-implement` Step 8.5 Documentation Sync, Phase 79 wiring): inserted between Step 8 (Post-Build Cleanup) and Step 9 (Complexity Self-Check). For every file created or modified in the implementation pass, the operator updates the 4 documentation surfaces (ARCHITECTURE_PLAN.md file tree / architecture docs / operations docs / schema docs) in the same commit batch -- while implementation context is fresh. `doc_tier`-aware skip semantics: `minimal` -> WARN-skip; `standard` -> require file tree + architecture docs; `system` -> require all 4 surfaces; `legacy` -> skip (matches doctrine-documentation-integrity bypass). Downstream substantiation gates (Steps 4.7 / 6 / 6.5 / 4.6.6) remain unchanged and now function as verification of Step 8.5's authoring output rather than primary-authoring fallbacks.

**Cross-reference**: Issue #52; doctrinally adjacent to `qor/references/doctrine-documentation-integrity.md` (substantiation-side verification), `qor/references/doctrine-procedural-fidelity.md` (post-hoc drift catch). Future V2: mechanical `qor/scripts/plan_doc_sync_lint.py` heuristic comparing implement gate `files_touched` against doc-surface diffs in the same commit (deferred to follow-on phase pending V1 prose adoption).

---

## SG-AuthorAuditMomentum-A — author-audit self-verification scope bias (Phase 68)

**Pattern**: when the same LLM agent authors a plan and then audits it, the audit inherits the author's search-path momentum. The locations the author did not check during planning are the same locations the author will not check during audit. Independent reviewers with no plan-authorship context naturally check different sources and find different defects.

**Originating recurrence**: SG-007 narrative reference (pre-Phase-68), promoted to structured countermeasure at Phase 68. Concrete empirical results from consumer-workspace audit chains:

- Sub-plan 01 canonical schema audit chain: self-audit iteration 1 found 4 defects but missed `src/integrations/supabase/types.ts` as a schema verification source; independent reviewer at iteration 2 found 3 additional defects including a case where iteration 1's own verification was wrong (F3 became F7).
- Sub-plan 02a audit chain: independent reviewer from iteration 1 caught 10 + 9 + 12 findings including the critical `pg_notify` durability hallucination (SG-009) at iteration 1. Without independent review, the broken architecture would have passed self-audit and shipped.

A second recurrence dimension: when a plan introduces a discipline (lint, audit pass, doctrine), the plan itself is structurally vulnerable to exhibiting the very pattern it remediates, because the discipline is not yet runnable as code. COREFORGE 3-VETO meta-cycle (META_LEDGER #200/#201/#203 in the consumer ledger): the plan authoring `plan_text_consistency_lint` exhibited the text-drift pattern the lint targets.

**Countermeasures** (Phase 68; GH #44 + #50):

- **Option B codification** in `/qor-audit` Step 1.a (GH #50): the skill prompt names "Option B: independent reviewer" as the formal fallback (and explicit operator choice) when Codex-plugin-driven Option A is unavailable. Dispatch protocol enumerated: fresh-context audit (new session), architect-reviewer subagent, second operator.
- **Self-Application Sub-Pass** in `/qor-audit` Step 3 (GH #44): when the plan's `originating_remediation` field is set (Phase 68 schema declaration in `qor/gates/schema/plan.schema.json`), the auditor manually applies the to-be-introduced discipline against the plan's own content. VETO category: `specification-drift` when self-application detects the targeted pattern.
- **Risk-score auto-dispatch** in `/qor-audit` Step 1 (Phase 87; GH #82): `qor.scripts.audit_risk_score` scores the plan under audit for author-momentum risk and, when it reports `option_b_required: true`, makes Option B mandatory for that audit. This makes the Phase 68 Option B proactive — auto-mandated on the iteration where a config-fabrication or high-citation-surface risk signal first appears, rather than reactively dispatched by operator discretion after a VETO. V1 scores the two mechanically-deterministic signals (a cited `*.config.*` file; >=5 grep-evidence statements). Originating recurrence: consumer-repo session 2026-05-18–19, where Option B caught 4 binding SG-007-family defects across 4 audit iterations that solo audits would have passed (`SG-AuthorMomentumConfigFabrication-A`, `SG-OverPromiseInvariant-A`, `SG-AuthorMomentumTestSeedFabrication-A`).

**Cross-reference**: SG-007 (predecessor narrative); Issue #44, Issue #50, Issue #82; FailSafe + COREFORGE empirical evidence.

---

## SG-DeliveryBranchDrift-A — plan delivery branch goes stale between authoring and audit (Phase 83)

**Pattern**: a plan declares a `pr_target` — the branch it will merge into — and cites infrastructure (migrations, schema objects, files) that exists on that branch. The `/qor-audit` Phase 37 Infrastructure Alignment Pass grep-verifies each citation against the branch the plan NAMES, and every citation resolves, so the audit PASSes. But between plan authoring and audit the named branch can stop being a valid delivery target: a release branch closes for new merges, or the cited infrastructure exists ONLY on that now-closed branch and is absent from the next open branch and from the default branch. The audit never challenges branch currency; the whole delivery premise is stale while every individual citation check is green.

**Originating recurrence**: consumer workspace `Accountable-Live-LLC/Accountable-App-3.0`, 2026-05-20. Plan `plan-analytics-07-admin-ui-tabs-phase-a.md` declared `pr_target: RC1.4` and `branch: feat/382-analytics-admin-tabs (off origin/RC1.4)`. `/qor-audit` iter-1 verified every cited migration against `origin/RC1.4` — all present, PASS — and the cycle implemented 14 files. By audit time `RC1.4` had closed for new merges; one cited dependency (analytics-04 drift views) existed only on the closed `RC1.4` and was absent from the next open branch `RC1.5` and from `main`. A whole feature tab was built against a data foundation unreachable from any valid delivery target. The operator caught it; the audit did not.

**Countermeasure** (Phase 83 wiring; GH #87): the Phase 37 Infrastructure Alignment Pass gains a **Delivery-Branch Currency** sub-check (`qor/skills/governance/qor-audit/references/phase37-subpasses.md`). A new optional `pr_target` field on `qor/gates/schema/plan.schema.json` declares the target branch. The pre-audit lint `qor.scripts.delivery_branch_lint` (wired into `/qor-audit` Step 0.6) extracts `pr_target` from the plan, allowlist-validates it against a conservative branch-name pattern (a `-`-prefixed value is rejected and never passed to `git` — closes the argument-injection surface), and runs `git ls-remote --heads origin <pr_target>` to confirm the branch exists on the remote. Release-branch open/closed state is not git-derivable; the sub-check prose directs the auditor to surface `pr_target` to the operator for an explicit still-open confirmation, and to grep-verify cited infrastructure against `git show origin/<pr_target>:<path>` specifically. A missing, closed, or off-target delivery branch is an `infrastructure-mismatch` VETO.

**Cross-reference**: Issue #87; sibling to `SG-InfrastructureMismatch` (Phase 37, citation existence) and `SG-CitationDrift-A` (Phase 72, sealed-citation re-walk) — same family: a citation true when the plan was authored but no longer true against the live delivery target. The GH #87-comment facet (`/qor-plan` Step 0.5 branching from `main` regardless of unmerged predecessor phases) is a related branch-base-correctness concern deferred to its own phase.

---

## SG-PreAuditDraftSubmission-A — plan declares itself pre-audit yet audit consumes a cycle (Phase 84)

**Pattern**: a plan author explicitly marks a plan as not yet audit-ready — via an `**iteration**:` value of `draft` / `pre-audit`, a numbered "Operator Decisions Required Before Audit" section, or Open Questions ending "Operator confirms before audit". The autonomous-cycle directive advances `/qor-plan -> /qor-audit -> /qor-implement` without operator pause when prior precedent exists, so `/qor-audit` runs anyway, produces a foregone VETO on a structurally not-ready plan, and ticks the cycle-count escalator toward its 3-strike threshold. The VETO is correct but the audit cycle is wasted: the plan announced its own not-readiness before the adversarial passes ran.

**Originating recurrence**: consumer-repo session 2026-05-18, plan `plan-attribution-13a-source-normalization.md` iter-1 — plan line 9 carried `**iteration**: draft (pre-audit)`, three Open Questions each ended "Operator confirms before audit", and four numbered "Operator Decisions Required Before Audit" items were listed. `/qor-audit` was invoked regardless, producing a 5-binding-finding VETO without operator dialogue on the decision items first. Cataloged in the consumer `docs/SHADOW_GENOME.md` as `SG-PreAuditDraftSubmission-A`.

**Countermeasure** (Phase 84 wiring; GH #81): a new pre-audit lint `qor.scripts.plan_iteration_status_lint` reads the plan and exits non-zero on any of the three pre-audit signals. `/qor-audit` Step 0.3 runs it BEFORE Step 1 identity activation and before any adversarial pass; on non-zero exit the audit aborts, prints the lint guidance, skips the remaining steps, and emits no audit gate artifact — so no cycle is consumed. Unlike the WARN-only Step 0.6 lints, this is a hard short-circuit: a plan that declares itself not-ready is not a candidate for adversarial review.

**Cross-reference**: Issue #81; doctrinally adjacent to `SG-PreAuditLintGap-A` (Phase 55, presence-only / infrastructure-mismatch pre-audit lints) — same family: catch a plan-readiness class before the audit cycle is spent, not after.

---

## SG-InverseCoverageGapTaxonomy-A — closed-enum taxonomy with forward-only test coverage (Phase 84)

**Pattern**: a plan defines a closed-enum taxonomy — a `CANONICAL_*_VALUES` constant tuple plus a `normalize*` function mapping arbitrary input onto that set via an alias map. The standard test list covers the forward direction (every alias-map key normalizes into the canonical set) but not the inverse (every canonical value is reachable via at least one identity-mapping). A canonical bucket can then be declared in the type union yet be unreachable through `normalize*`: data writes never produce it and downstream `WHERE bucket = 'X'` queries return zero rows even though `'X'` is a valid type. The forward round-trip test passes; the gap is invisible.

**Originating recurrence**: consumer-repo session 2026-05-18, plan `plan-attribution-13a-source-normalization.md` iter-2 (sealed PASS). `src/lib/attribution-source-taxonomy.ts` declared `CANONICAL_SOURCE_VALUES` with 15 buckets including `referral`, but the internal `ALIAS_MAP` had no `referral: 'referral'` identity entry, so `normalizeSource('referral')` returned the `unknown` fallback. The sealed round-trip test iterated `Object.keys(ALIAS_MAP)` and passed; the inverse direction was never asserted. The defect propagated through iter-1 audit, iter-2, and a byte-equivalent Deno mirror; it was caught only at operator pre-commit review, requiring a retroactive alias-map amendment plus a new inverse-coverage test. Cataloged in the consumer `docs/SHADOW_GENOME.md` as `SG-InverseCoverageGapTaxonomy-A`.

**Countermeasure** (Phase 84 wiring; GH #84): `/qor-plan` Step 5 and `/qor-audit` Step 3 Test Functionality Pass require that a plan declaring a closed-enum taxonomy carry BOTH directional assertions; missing inverse coverage is a `coverage-gap` VETO. The pre-audit lint `qor.scripts.plan_test_lint` gains an inverse-coverage check: when a plan declares a `CANONICAL_*_VALUES` tuple and a `normalize*` function with no inverse-coverage test bullet, it emits a WARN-only `inverse-coverage-missing` finding so the Governor can amend before the binding VETO. The discipline (forward + inverse assertions, gated-bucket exemption, standard test pattern) is documented in `qor/references/doctrine-test-functionality.md`.

**Cross-reference**: Issue #84; doctrinally adjacent to `SG-035` (doctrine-content test unanchored) — same family: a test that passes vacuously because it never exercises the direction where the defect lives.


---

## SG-CICoverageDrift-A — plan ci_commands never reconciled against actual CI workflow definitions (Phase 89)

**Pattern**: a phase plan hand-authors a `## CI Commands` list ("commands matching CI"). `/qor-substantiate` Step 6 runs exactly that list plus the built-in qor gates and seals "all CI green". Nothing parses `.github/workflows/*.yml` to confirm the plan's list actually covers the repo's CI jobs. A CI job the operator simply forgot to enumerate never runs through the governed cycle. The seal entry reads "all CI green" while a real CI job would fail; the gap is invisible until integration PR time, after multiple seals have already landed.

**Originating recurrence**: consumer workspace `MythologIQ-Labs-LLC/COREFORGE`, 2026-05-22. A 10-phase governed remediation stack (Phases 358-369) ran under `/qor-auto-dev-1` (plan -> audit -> implement -> substantiate). Every phase plan's `ci_commands` listed the obvious checks (`cargo check` / `cargo test`, `npx tsc`, `npx eslint`, `npx jest`, `check_razor_budget.py`); every phase passed all declared commands and all gates and sealed PASS. The repo also had a GitHub Actions job `Architecture Guard` running `scripts/architecture/check_test_metadata.py` -- a guard requiring `SPEC:` / `FEATURE:` / `TEST_ID:` markers on architecture-sensitive test files. No phase plan listed it. When the 10-phase stack was opened as an integration PR, that job failed: three test files introduced across Phases 358 and 366 lacked the required metadata markers. All ten phases had already sealed "green" carrying a latent CI failure. Filed as GH #91.

**Countermeasure** (Phase 89 wiring; GH #91): a new pre-audit lint `qor.scripts.ci_coverage_lint` runs at `/qor-audit` Step 0.6 alongside the existing four lints. It parses `.github/workflows/*.yml` (PyYAML safe_load), filters environment-setup boilerplate (`pip install`, `git fetch`, `git merge-base`, doc-only conditional bash, `>> $GITHUB_OUTPUT`, etc.), skips tag-only workflows (`on.push.tags` without `branches`), and extracts the V1 Python-fingerprint `run:` commands (`python ...` / `pytest ...`). Each discovered command is compared as a flag-normalized substring against the plan's `## CI Commands` bullets; the plan may declare a `## CI Coverage Exemptions` block of substring patterns to justify pre-existing infrastructure CI not phase-relevant. Unmatched, non-exempt commands emit WARN; the lint is WARN-only (exit 0 always) -- the Governor amends the plan before audit Step 3 catches the structural gap. A self-application test (`test_lint_self_applies_to_phase_89_plan`) asserts Phase 89's own plan reports zero WARNs against this repo's actual workflows -- the deterministic shipping-correctness anchor.

**Cross-reference**: Issue #91; doctrinally adjacent to `SG-PreAuditLintGap-A` (Phase 55, presence-only / infrastructure-mismatch pre-audit lints) and `SG-PlanTextDrift-A` (Phase 67, same-operation-different-spelling drift) -- same family: catch a structural class of plan-vs-reality gap at the pre-audit lint layer, before the binding adversarial pass would consume an audit cycle.


---

## SG-SilentSkipMisconfig-A — silent-SKIP cascade hides recoverable misconfiguration (Phase 90)

**Pattern**: Phase 75 (`SG-HalfSealedClaim-A`) gave skills declarative tolerance when `qor-logic` modules are not importable: emit `gate_skipped_prerequisite_absent`, log SKIP in the seal, continue. The countermeasure is correct for legitimately non-Python hosts (pure-Rust / pure-Node archetypes). It misfires on Python hosts where the operator simply has the wrong venv active — the SKIP cascade looks identical to the legitimate non-Python case, so operators learn to treat SKIPs as normal. Seal entries land with quietly-incomplete gate coverage; trust in the "all gates ran" claim erodes one silent SKIP at a time.

**Originating recurrence**: COREFORGE consumer session (per GH #79). qor-logic 0.55.1 installed in venv `D:\Myth-TechForge\Alden_Calindron\venv\` with `failsafe-qor-hook`. Skills installed globally to `~/.claude/skills/qor-*/SKILL.md`. A Claude Code session in a different repo without that venv on PATH ran the skills; `python -m qor.reliability.X` raised `ModuleNotFoundError` on every call. The session inferred from repeated failures that the modules "were never intended to exist" and added a project-memory rule to silently skip the reliability checks — propagating the misconfiguration into subsequent sessions. Diagnosed only by running `which qor-logic` and `pip show qor-logic` outside the skill flow, which the skills did not direct operators to do.

**Countermeasure** (Phase 90 wiring; GH #79): two layered additions to each skill that invokes `python -m qor.reliability.*` or `python -m qor.scripts.*`. (C) A preflight one-liner at the top of `## Execution Protocol` (or the skill's equivalent protocol-section): `python -c "import qor.reliability" || echo "WARN: ..."` — WARN-only (not ABORT) so Phase 75 SKIP behavior remains intact on non-Python hosts. (D) An `## Environment` section above the protocol that documents the install contract (`pip show qor-logic`, `pipx install qor-logic`) and cross-references the Phase 75 SKIP fallback. The cross-skill discipline is enforced by `tests/test_skill_environment_block.py` (7 assertions across 7 affected skills as of Phase 90: section presence, install-contract substrings, Phase 75 SKIP-fallback cross-reference, preflight precedes first invocation, preflight WARN-only). V1 ships only the visibility half; the full reachability fix (Option A in GH #79: `qor-logic <subcommand>` CLI dispatch using the CLI's own `sys.executable`) is reserved for a follow-on phase, analogous to the V1/V2 split used for GH #88/#91 in this cluster.

**Cross-reference**: GH #79; doctrinally adjacent to `SG-HalfSealedClaim-A` (Phase 75, the V1 declarative-tolerance countermeasure this layer builds on). Same root surface, different leverage point.


---

## SG-DoDImplicit-A — implicit Definition of Done lets lies ship through ceremonial gates (Phase 92)

**Pattern**: multiple Qor governance phases can return PASS while the artifact in question is still a placeholder or a lie at runtime. `/qor-plan` accepts a plan that documents intent. `/qor-audit` returns PASS when the plan is self-consistent and the implementation references match. `/qor-implement` records "implementation exists" by editing the named files. `/qor-substantiate` runs reliability sweeps, doc-integrity checks, badge-currency, secret-scan, and seal hash integrity — all *static* and *artifact-shape* checks. None of those phases require that **the implementation actually be executed and observed**. A function that returns `Ok(())` instead of doing the work, a vendor sync that returns `success: true` instead of calling the API, a recovery routine that returns `true` instead of re-probing — all of these pass every Qor gate on the books and can ship a fully-sealed phase whose code is a lie at runtime.

**Originating recurrence**: COREFORGE consumer session (per GH #86 body). ~5 distinct production-credibility blockers (recovery routines hardcoded to `true`; vendor `handle_sync` placeholders; constraint checks returning `Ok(())`; etc.) sailed through `PASS → seal` cycles. Detected only by a separate full-repo gap audit AFTER the fact. The Definition of Done was implicit per phase, and "the code runs and behaves correctly when invoked" never became a checkable item — each gate defined "done" however its own checks happened to verify, none required empirical observation.

**Countermeasure** (Phase 92 wiring; GH #86): explicit multi-tier Definition of Done as a first-class plan artifact. New `qor.scripts.dod_record.parse_plan` reads a plan's `## Definition of Done` section into structured records (D1 vision / D2 code / D3 governance / D4 empirical/runtime verification per deliverable, or D4.d waiver with rationale + follow-up phase). New `qor.scripts.dod_check.check_plan` runs at `/qor-substantiate` Step 4.6.7 (between procedural-fidelity 4.6.6 and doc-integrity 4.7); emits findings (`missing-dod-section`, `deliverable-missing-tier`, `waiver-without-rationale`, `waiver-without-followup`) with `severity="warn"`. New `qor/references/doctrine-definition-of-done.md` documents the four-tier contract and waiver protocol. V1 enforces only the *declaration presence* — that every deliverable carries a D1-D4 row OR an explicit D4.d waiver with rationale + follow-up phase. V1 is WARN-only (does not abort substantiate); V2 (deferred) will verify the *truth of D4* by cross-referencing D4-declared test names against pytest output and failing seal on mismatch.

**Forbidden interpretation**: the WARN-only V1 contract is the operator's adoption ramp, not permission to ignore D4. Operators MUST track unclosed `D4.d` waivers and close them in subsequent seal cycles. Accumulating waiver counts will trigger an `override_friction`-style escalator in V2 work analogous to Phase 54's `OverrideFrictionRequired`. A waiver without a follow-up phase reference is itself a finding; a follow-up phase that is never closed will be operator-visible.

**Cross-reference**: GH #86 (this issue); doctrinally adjacent to `SG-HalfSealedClaim-A` (Phase 75 — structural gaps below the ceremonial-verification surface) and `SG-DocSurfaceUncovered-A` (Phase 58 — procedural-fidelity check that finds skipped doc-surface updates). Same root family: ceremonial gates pass while substantive verification is absent.


---

## SG-MergePaceThrottle-A — merge velocity outpaces stabilization capacity (Phase 93)

**Pattern**: a high-throughput workstream expands multiple shared surfaces in a compressed window (PRs merging faster than review/test/regression-absorption can keep up; repair-tail density growing relative to forward features; broad shared-core touches; failing e2e on tail PRs). The governance system has no explicit throttle, so the team responds with repair PRs and after-the-fact scope back-outs instead of having earlier pressure to narrow scope. Stabilization capacity becomes an after-the-fact recovery loop instead of a pacing constraint.

**Originating recurrence**: Bicameral consumer workspace (per GH #89). 27 PRs merged in a single reporting window. 14,758 merged-PR additions. Repair cluster #346-#353 addressing stale authoritative SHA binding / status lifecycle / preflight noise / schema CI reliability. Open PR #354 carried a failing `e2e assertions (auto)` check. Later operational response: branch `chore/remove-integrations` backed Jira/Notion/Slack/Linear out of `dev` after fragility signals accumulated. The bottom line: throughput exceeded the rate at which the project could reliably review, test, absorb, and harden changes.

**Countermeasure** (Phase 93 wiring; GH #89): new `qor.scripts.merge_velocity_check` detector at `/qor-substantiate` Step 4.6.8. Walks `origin/main`'s recent merge history via `git log` (offline-safe; no GitHub API dependency) and computes a `VelocityAssessment` with three stabilization-capacity grades (`healthy` / `strained` / `exceeded`) plus an evidence list of fired signals. V1 thresholds: `strained` at `prs_merged_in_window >= 10` OR `repair_density >= 0.20`; `exceeded` at `prs_merged_in_window >= 20` AND (`repair_density >= 0.30` OR `shared_core_touch_count >= 10`). The detector is WARN-only at substantiate (CLI exits 1 on `exceeded`, but the `|| true` wrap swallows the non-zero in V1); V2 may remove the wrap to convert `exceeded` into a hard ABORT once the detector's false-positive rate is characterized. Repair-keyword classification covers `fix`, `hotfix`, `repair`, `regression`, `rollback`, `revert`. Shared-core path patterns are operator-declarable via repeat `--shared-core-path` flag (no built-in patterns; consumer-workspace-specific).

**V2 reserved** (deferred to a future phase): enforcement (hold new feature merges, isolate features as unmerged branches, require stabilization plan before more shared-core work, require issue-linked validation notes); GitHub-API integration (failing-e2e tail-check signal; test-matrix expansion detection; cross-PR repair-density clustering by subsystem). The V1 detector lands the infrastructure first so operators see the signal and adopt the discipline before the heavier enforcement machinery layers on top — the cluster's established V1/V2 split pattern.

**Inline companion** (Phase 94 wiring; GH #90): GH #90 was filed as the inline mechanism complementing GH #89's macro throttle. Phase 94 adds `qor.scripts.workspace_fragility_check` at `/qor-audit` Step 0.6 as the SIXTH pre-audit lint (after `plan_test_lint`, `plan_grep_lint`, `plan_text_consistency_lint`, `delivery_branch_lint`, `ci_coverage_lint`). Where Phase 93's `merge_velocity_check` looks BACKWARD at `origin/main`'s recent merge history at substantiate, Phase 94's `workspace_fragility_check` looks at the LOCAL working tree FORWARD pre-merge: untracked file count, dirty gate artifacts (`.qor/gates/<sid>/` whose session lacks a SESSION SEAL entry in META_LEDGER), ledger chain-math failures (excluding Phase 91 grandfathered residuals), active local branch count, branch-diff size since divergence from `origin/main`. Three grades (`low` / `medium` / `high`) with deterministic action mapping (`merge_ok` / `narrow_scope` / `hardening_only`). V1 thresholds: `medium` at `untracked_count >= 15` OR `dirty_gate_artifact_count >= 3` OR `active_branch_count >= 10` OR `recent_commit_diff_lines >= 1500`; `high` at `ledger_chain_failure_count > 0` OR `untracked_count >= 50` OR `recent_commit_diff_lines >= 5000`. CLI exits 1 on `high` so V2 can remove the `|| true` wrap and convert to a hard ABORT. WARN-only V1 at audit; V2 (audit-evidence treatment per GH #90's "Inline Enforcement Points" section; scope-expansion detection during /qor-implement; per-deliverable scope guard via Phase 92 D4 tier extension) reserved.

**Cross-reference**: GH #89 (macro) + GH #90 (inline); doctrinally adjacent to `SG-DoDImplicit-A` (Phase 92 — ceremonial gates pass while substantive verification is absent) and `SG-CICoverageDrift-A` (Phase 89 — plan ci_commands not reconciled against actual CI workflows). Same root family: governance gates that detect a class of process pressure the standard PASS/VETO sequence cannot see.


---

## SG-SkillCorpusGrowth-A — skill corpus grows monotonically with no consolidation counterweight (Phase 95)

**Pattern**: the canonical SKILL.md corpus has grown monotonically and is now a measurable latency source; the open-issue backlog is overwhelmingly additive — there is no governance counterweight that pays down skill weight. Per-skill SKILL.md files accumulate sub-passes, doctrines, and wiring paragraphs across phases; nothing budgets skill size; no recurring pass consolidates accumulated content. Two distinct slowdown sources both grow with each additive phase: context weight (larger SKILL.md = more tokens per turn = higher per-turn latency) and wall-clock (more sequential steps, sub-passes, file reads, Python shell-outs per invocation).

**Originating measurement** (per GH #92, captured via `git show` across phase anchors):

| Date | Phase | SKILL.md bytes | Lines | Tokens (~chars/4) |
|------|-------|----------------|-------|-------------------|
| 2026-04-02 | 0 | 91 KB | 3,024 | ~22.8k |
| 2026-04-15 | 1 (SSoT) | 124 KB | 4,074 | ~31k |
| 2026-04-20 | 39b | 214 KB | 5,939 | ~53.6k |
| 2026-05-01 | 58 | 241 KB | 6,294 | ~60.3k |
| 2026-05-14 | 81 (HEAD) | 282 KB | 6,766 | ~70.5k |

~3.1x bytes, 2.2x lines in ~6 weeks. Monotonic — never contracted. Concentration: qor-audit (36.7 KB) + qor-substantiate (32.7 KB) = 25% of the corpus at the issue-filing date; reference fan-out for a single qor-audit invocation can read 80-100+ KB of context (SKILL.md + own templates + chained doctrines). At the time of Phase 95 substantiate (this entry), qor-audit has grown to 44 KB and qor-substantiate to 39.8 KB+ — the new lint catches the bloat the first time it runs.

**Countermeasure** (Phase 95 wiring; GH #92): new `qor.scripts.skill_size_budget_lint` walks `qor/skills/**/SKILL.md` and emits one finding per skill exceeding the size thresholds — `skill-over-warn-threshold` at 25 KB; `skill-over-exceeded-threshold` at 40 KB. Wired at `/qor-substantiate` Step 4.6.9 (between merge-velocity 4.6.8 and doc-integrity 4.7) WARN-only. CLI exits 1 when any EXCEEDED finding is present so V2 can convert to a hard ABORT. The lint is a visibility surface; it does NOT auto-refactor skills.

**V2 reserved**: periodic consolidation cadence (extending `qor-process-review-cycle` to sweep skill weight per the issue's "Periodic consolidation pass" proposal); context-load measurement per phase (per-skill reference fan-out); growth-rate analysis from git history (the GH #92 measurement table generalized into a script); auto-suggest of progressive-disclosure refactor candidates.

**Reflective note**: Phase 95 itself adds ~270 LOC of script + ~120 lines of doctrine + ~20 lines of skill-prose wiring to the corpus it measures. The lint contributes to the very bloat it visibilizes. That tension is acknowledged: V1 lands the visibility; V2 consolidation work will need to evaluate which doctrine prose (including possibly this entry's table) is operative vs archival. The cluster's V1/V2 split pattern is itself a corpus-growth mechanism — each V1 phase ships a detector + a doctrine entry + a SKILL.md wiring paragraph. GH #92 is the issue that will eventually require some of those V1 doctrines to retire when V2 evidence shows they are not load-bearing.

**Cross-reference**: GH #92; doctrinally adjacent to `SG-DocsBackloadedToSubstantiate-A` (Phase 79 — documentation lifecycle deferred to seal-time) and `SG-MergePaceThrottle-A` + inline companion (Phase 93/94 — governance gates that detect a class of process pressure). Same root family: process-control measurements surfacing pressures the standard PASS/VETO sequence cannot see.


---

## SG-GrepShapedRunclaim-A — recon grades surfaces on grep-shaped evidence without proving end-to-end runtime contract (Phase 96)

**Pattern**: `/qor-deep-audit-recon` (and the parent `/qor-deep-audit` matrix) accepts **grep-shaped evidence** — file exists, class is defined, command is registered, claim string is present — as sufficient proof to grade a code surface HIGH severity or "production-critical". The recon never validates the runtime contract end-to-end: importability, command-registration → handler reachability, packaging in the production bundle, test inclusion at collection time, caller/callee interface match. Downstream remediation cycles (`/qor-plan`, `/qor-audit`, `/qor-implement`) inherit the misgrading; the gap surfaces only at implementation time, after substantial cycle cost.

The vulnerable class is broader than any single project: any Qor-logic-governed project with multi-language stacks (Python + Rust + TypeScript), migrations in progress (one language deprecated, another supersedes), multiple test suites at different layers, or command registrations outliving their handlers is exposed.

**Originating recurrence**: COREFORGE Phase 371 (per GH #108). Recon Vector B (codebase-wide crypto claim audit) graded `DPF-LIE-01` (persona IPC envelope claims AES-256-GCM but no cipher code path exists) as HIGH severity purely on grep evidence: `src/personas/constants.py:11` declares `DEFAULT_IPC_ENCRYPTION_SCHEME = "AES-256-GCM"`; `src/personas/ipc.py` schema includes `EncryptionMetadata` fields; zero matches for `aesgcm.encrypt`. Plan and audit cycles consumed cost; implementation phase surfaced the actual runtime state — `src/personas/communication.py:21-25` imports symbols (`PersonaIPCBridge`, `PersonaIPCEnvelope`, `PersonaChannel`, `PersonaHandshake`) that don't exist in current `src/personas/ipc.py`; `src/personas/alden.py:33` imports `main` from a non-existent module; `tests/test_persona_ipc.py` has `from __future__ import annotations` not at file top → collection `SyntaxError`; zero non-test importers from production code paths; the actual production Python sidecar (invoked from Rust `src-tauri/src/alden_legacy.rs`) uses `python/cli/*.py`, not `src/personas/`; and PR #223 already flags the entire `src/` tree as "abandoned pre-Tauri implementation". Operator framing preserved from the COREFORGE cycle: "the right classification is not 'dead code, ignore it' — it is **zombie legacy code with live command registration and broken runtime/import packaging**."

**Countermeasure** (Phase 96 wiring; GH #108): new `qor.scripts.reachability_probe` runs five checks against each cited surface — importability (`python -c "from <module> import <symbol>"` from clean process); test collection (`pytest --collect-only` against any test file referencing the surface); caller graph (at least one production code path, non-test/non-scratch/non-doc, imports/invokes the surface); packaging (cited path is in the production build manifest); interface match (call-site arity matches module-exported signature via AST parse). Each failing check emits a `reachability-*-failed` / `-no-production-caller` / `-packaging-missing` / `-interface-mismatch` finding with `severity="warn"`. Wired at `/qor-deep-audit-recon` Phase 3 Round 0 (NEW; between after-synthesis checkpoint and existing Phase 3 Verification). Detailed five-check protocol lives in `qor/references/recon-reachability-probe.md` (progressive-disclosure per `SG-SkillCorpusGrowth-A`). CLI exits 0 by default (V1 WARN-only); `--exit-on-any` opts into CI-style enforcement. The downgrade rule: any single failing check means the finding cannot retain a HIGH or production-critical grade in V1; the recon brief author annotates the finding with `reachability-gap` classification and either gathers end-to-end runtime evidence or downgrades the finding's severity.

**V2 reserved** (Phase 99): blocking enforcement in `/qor-audit` Step 3 Infrastructure Alignment Pass as a new "Runtime Contract Walk" sub-pass. When auditing a per-sprint plan that cites a Python/JS/Rust module path, the Judge walks the import graph one hop in each direction (callers of cited surface + callees the surface imports). Both halves must parse + collect + import cleanly in the project's actual environment; any half failing returns the plan to `/qor-plan` per Phase 67 unchanged-plan short-circuit precedent. Multi-language probe extension (Rust/TS/JS) is also V2-reserved.

**Cross-reference**: GH #108 (originating issue); doctrinally adjacent to `SG-DoDImplicit-A` (Phase 92 — ceremonial gates pass while substantive verification is absent) and `SG-CICoverageDrift-A` (Phase 89 — plan ci_commands not reconciled against actual CI workflows). Same root family: governance checks that detect a class of evidence-vs-reality drift the standard PASS/VETO sequence cannot see. The Phase 96 V1 detector + Phase 99 V2 enforcement split mirrors the established Phase 89/90/91/92/93/94/95 V1/V2 cluster pattern.
