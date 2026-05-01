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
