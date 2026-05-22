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

**Cross-reference**: SG-007 (predecessor narrative); Issue #44, Issue #50; FailSafe + COREFORGE empirical evidence.

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
