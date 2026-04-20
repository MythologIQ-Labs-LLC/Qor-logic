# Plan: Phase 39 — context-discipline doctrine + persona reshape

**change_class**: feature
**target_version**: v0.29.0
**doc_tier**: system
**pass**: 2 (amended from Pass 1 VETO per `.agent/staging/AUDIT_REPORT.md` — V1 resolution (a): Anthropic SDK invocation)

**Scope**: Codify the "personas = context-prioritization scaffolds for edge-case determinations" doctrine (operator direction registered 2026-04-19 in META_LEDGER #116 research brief). Ship a seeded-defect A/B harness that measures detection rate under persona-named vs stance-directive-only Identity Activation phrasing across `/qor-audit` AND `/qor-substantiate`, using direct Anthropic SDK invocation (V1 resolution). Apply A/B findings to the 24 skills carrying `<persona>` frontmatter: decorative tags removed, load-bearing tags justified, Identity Activation blocks rewritten stance-directive-first where evidence supports.

**terms_introduced**:
- `context-prioritization scaffold` — persona framing used to prioritize the context a skill loads for edge-case determinations within its domain. Metric is performance/accuracy/results, not aesthetic flavor. Home: `qor/references/doctrine-context-discipline.md`.
- `stance-directive` — the behavioral modifier portion of an Identity Activation block (e.g., "adversarial," "prove-not-improve"), isolated from persona name vocabulary. Home: doctrine.
- `seeded-defect corpus` — curated fixture directory carrying 20 planted defects mapped to `findings_categories`. Ground-truth input for A/B measurement. Home: `tests/fixtures/ab_corpus/`.
- `detection rate` — A/B metric: percentage of seeded defects surfaced by a skill invocation under a given Identity Activation variant. Home: `qor/scripts/ab_harness.py`.

**Source**:
- `.agent/staging/RESEARCH_BRIEF.md` (META_LEDGER #116) — original research.
- Operator directives 2026-04-19: (1) personas load-bearing as context-prioritization, metric is results; (2) full /qor-plan cycle; (3) R6 A/B mandatory.
- `docs/BACKLOG.md` Phase 39 queue.

## Open Questions

None. Target skills (`/qor-audit`, `/qor-substantiate`), corpus size (20 defects), and invocation mechanism (Anthropic SDK direct, V1 resolution (a)) are locked.

## Non-goals

- No change to the v0.28.0 procedural surface contracts (schemas, enums, delegation). Consumer interfaces are frozen.
- No removal of persona vocabulary from user-facing commit messages, ledger entries, or narrative docs. Only skill-internal prose and frontmatter are in scope.
- No change to existing subagent invocations via `Task`/`Agent` tools (those are already persona-agnostic per Phase 35 lesson).

## Phase 1 — doctrine-context-discipline.md

### Affected Files

- `qor/references/doctrine-context-discipline.md` — NEW. Codifies the three-mechanism distinction (frontmatter tag vs Identity Activation prose vs subagent invocation) and the persona-as-context-prioritization framing.
- `qor/references/doctrine-governance-enforcement.md` — add §11 cross-reference to context-discipline.
- `tests/test_doctrine_context_discipline.py` — NEW. Structural assertions.

### Changes

New doctrine file (~250 LOC, single file, no sub-pages):

Sections:

1. **The three mechanisms** — distinguishes (a) `<persona>` frontmatter metadata, (b) Identity Activation prose in Step 1 of skill bodies, (c) subagent invocation via `Task`/`Agent` tools. Each mechanism has different operational semantics; conflation is the root defect class.

2. **Persona as context-prioritization scaffold** — a persona exists IFF it measurably prioritizes context for edge-case determinations within the skill's domain. The evaluation question: "What context does this persona load that a bare skill-step directive would not?" Tags failing this test are decorative and must be removed.

3. **Stance directive discipline** — Identity Activation blocks should lead with the behavioral modifier (adversarial, prove-not-improve, precision-focused), not the persona name. Persona name is optional ergonomic flavor if it carries context-prioritization value.

4. **Subagent invocation rule** — Reiterates the Phase 35 lesson: `subagent_type: "general"` by default. Persona-typed subagents (`ultimate-debugger`, etc.) require evidence that the persona prompt measurably alters tool selection or output shape. Absence of evidence = use `general`.

5. **Verification protocol** — every `<persona>` tag in `qor/skills/**/SKILL.md` must either link to an A/B detection-rate artifact or be removed. Skills under test: `/qor-audit`, `/qor-substantiate` at v0.29.0 landing; additional skills added as future phases produce evidence.

### Unit Tests (TDD — written first)

- `tests/test_doctrine_context_discipline.py::test_doctrine_file_exists` — NEW. File present at declared path.
- `tests/test_doctrine_context_discipline.py::test_doctrine_has_five_sections` — NEW. All five section headers present verbatim.
- `tests/test_doctrine_context_discipline.py::test_doctrine_governance_xref` — NEW. `doctrine-governance-enforcement.md` §11 references the new file.

## Phase 2 — A/B harness infrastructure (Anthropic SDK invocation)

### Affected Files

- `pyproject.toml` — add `anthropic>=0.40,<1.0` to a new `[project.optional-dependencies].ab-harness = [...]` extra. Kept out of the main install set so pip users who don't run the harness don't pull the dependency.
- `tests/fixtures/ab_corpus/` — NEW directory. 20 seeded defects across 10 category-typed fixture files (2 defects per category on average; categories mapped to the 12-value `findings_categories` enum; 2 categories omitted: `coverage-gap` + `dependency-unjustified` — harder to synthesize, tested live elsewhere). Every fixture file begins with the header comment `# SEEDED TEST DEFECT — NOT EXECUTABLE — Phase 39 A/B corpus (F2 resolution).`
- `tests/fixtures/ab_corpus/MANIFEST.json` — NEW. Declares every seeded defect: `{id, file, line_start, line_end, category, description}` — ground-truth reference for scoring (F5 resolution).
- `tests/fixtures/ab_corpus/variants/` — NEW directory. Pre-authored stance-directive-only rewrites of each target skill's Identity Activation block, one file per `(skill, variant)` pair: `qor-audit.persona.md`, `qor-audit.stance.md`, `qor-substantiate.persona.md`, `qor-substantiate.stance.md` (F4 resolution: hand-crafted, not programmatically string-replaced).
- `qor/scripts/ab_harness.py` — NEW (~140 LOC across 5 functions). Corpus loader, variant loader, LLM invocation, detection-rate scorer, comparison reporter. Uses `anthropic` SDK; reads `ANTHROPIC_API_KEY` from env.
- `qor/scripts/ab_live_run.py` — NEW (~60 LOC). Operator-invoked CLI that runs the full A/B cycle live (hits API, produces results artifact). Separated from `ab_harness.py` so the library remains unit-testable without API access.
- `tests/test_ab_harness.py` — NEW. Unit tests for corpus load, manifest validation, scorer arithmetic, variant loading. All tests mock the Anthropic client (no live API calls in CI).

### Changes

`tests/fixtures/ab_corpus/` layout:

```
ab_corpus/
  MANIFEST.json                      # ground truth: 20 {file, line, category, description}
  razor-overage/
    function_too_long.py             # 45-line function (planted violation)
    file_too_long.py                 # 260-line file (planted violation)
  ghost-ui/
    placeholder_button.tsx           # button with no onClick
    coming_soon.tsx                  # "coming soon" UI
  security-l3/
    hardcoded_secret.py              # credential literal
    disabled_auth.py                 # TODO: auth
  owasp-violation/
    shell_true.py                    # subprocess shell=True
    pickle_load.py                   # unsafe deserialization
  orphan-file/
    unreachable.py                   # no import chain
    isolated_module.py               # not in build path
  macro-architecture/
    cyclic_deps_a.py                 # imports cyclic_deps_b
    cyclic_deps_b.py                 # imports cyclic_deps_a
  schema-migration-missing/
    breaking_required_field.json     # schema adds required field, no migration
    enum_value_removed.json          # breaking enum reduction
  specification-drift/
    prose_code_mismatch.md           # prose says 3, code block says 5
    undeclared_referent.md           # references undeclared helper
  test-failure/
    broken_assertion.py              # failing test assertion
    skipped_test.py                  # @pytest.mark.skip without reason
  infrastructure-mismatch/
    wrong_glob_pattern.md            # plan claims audit*.json glob; actual is singleton
    undeclared_module.md             # plan references non-existent module
```

`MANIFEST.json` shape:
```json
{
  "defects": [
    {"id": 1, "file": "razor-overage/function_too_long.py", "line": 1, "category": "razor-overage", "description": "function body exceeds 40 lines"},
    ...
  ]
}
```

`ab_harness.run(variant: "persona" | "stance", skill: str, corpus_path: Path, client=None, model: str = "claude-opus-4-7") -> dict`:
- Loads manifest, iterates 20 defects.
- For each defect, constructs a prompt: system prompt = the skill's SKILL.md body with the `variant` Identity Activation block swapped in (loaded from `tests/fixtures/ab_corpus/variants/<skill>.<variant>.md`); user prompt = the fixture file content + instruction to produce a JSON object `{"findings_categories": [...]}`.
- Invokes `client.messages.create(model=model, max_tokens=800, system=system_prompt, messages=[{"role": "user", "content": user_prompt}])`. `client` defaults to a fresh `anthropic.Anthropic()` which reads `ANTHROPIC_API_KEY` from env. Tests pass a mock client.
- Parses the response: extracts the first JSON object matching `{"findings_categories": [...]}`. If parse fails, the defect counts as a miss (not an error).
- Scores: defect is a detection iff the planted category is in the emitted `findings_categories` list.
- Returns `{variant, skill, model, detections: int, total: 20, detection_rate: float, per_defect: [...]}`.

`ab_harness.compare(persona_result, stance_result) -> dict`:
- Returns `{persona_rate, stance_rate, delta, winner}` where `delta = stance_rate - persona_rate`, `winner` is `"persona" | "stance" | "tie"` (tie = |delta| < 5pp).

`ab_harness.aggregate_runs(results: list[dict]) -> dict`:
- Takes N per-run results for a single `(skill, variant)` combination.
- Returns `{mean_detection_rate, stddev_pp, n}`.

`ab_variants.load(skill: str, variant: "persona" | "stance") -> str`:
- Reads `tests/fixtures/ab_corpus/variants/<skill>.<variant>.md`.
- Returns the Identity Activation block text as a string (to be spliced into the skill system prompt).
- Hand-authored files (F4 resolution). No programmatic rewriting — the stance variant is operator-crafted once, checked into the fixture directory, reviewed alongside this plan.

**Non-determinism**: LLM responses vary across runs even at temperature 0 (Opus 4.7 cannot guarantee identical outputs). N=5 runs per `(skill, variant)` combination samples this variance. Mean + stddev quantify the noise floor; detection-rate delta must exceed noise floor to count as a real effect. **Concretely**: if stddev across 5 runs is 7pp per variant, a 5pp delta is indistinguishable from noise regardless of tie-threshold. Phase 3's results artifact reports both mean and stddev.

**Cost**: 2 skills × 2 variants × 5 runs × 20 defects = 400 API calls per full cycle. At Opus 4.7 pricing (~$15/M input, ~$75/M output tokens) and ~500 input + ~100 output tokens per call: ~$4 per full A/B cycle. Declared here for operator budget awareness.

**Rate limiting**: harness runs serially (no concurrency). Anthropic's default tier rate limits (~50 RPM on Opus) accommodate serial 400 calls in ~10-15 minutes.

**Credential handling**: `ANTHROPIC_API_KEY` read from env by the SDK. Never logged. No keys in test fixtures, code, or results artifacts. If env var is absent, `ab_live_run.py` exits with a clear error before any work; `ab_harness.py` library functions accept a mock client and never read env directly.

### Unit Tests (TDD — written first; all mock the Anthropic client)

- `tests/test_ab_harness.py::test_corpus_manifest_declares_20_defects` — NEW.
- `tests/test_ab_harness.py::test_corpus_categories_are_all_valid_enum_values` — NEW. Every defect category is in the `findings_categories` 12-value enum.
- `tests/test_ab_harness.py::test_corpus_files_exist` — NEW.
- `tests/test_ab_harness.py::test_corpus_files_carry_seeded_defect_marker` — NEW (F2). Every fixture file starts with `# SEEDED TEST DEFECT — NOT EXECUTABLE`.
- `tests/test_ab_harness.py::test_manifest_line_range_fields_present` — NEW (F5). Every defect has `line_start` and `line_end`.
- `tests/test_ab_harness.py::test_scorer_counts_category_superset_as_detection` — NEW. Synthetic model response `{"findings_categories": ["razor-overage"]}` counts as detection for a `razor-overage` seeded defect.
- `tests/test_ab_harness.py::test_scorer_counts_missing_category_as_miss` — NEW.
- `tests/test_ab_harness.py::test_scorer_counts_json_parse_failure_as_miss` — NEW. Malformed model response counts as miss, does not raise.
- `tests/test_ab_harness.py::test_compare_reports_winner_stance_above_5pp` — NEW.
- `tests/test_ab_harness.py::test_compare_reports_tie_below_5pp` — NEW.
- `tests/test_ab_harness.py::test_run_uses_injected_client_not_env` — NEW. When `client=` is passed, `ab_harness.run` does not read `ANTHROPIC_API_KEY` from env.
- `tests/test_ab_harness.py::test_run_submits_variant_system_prompt` — NEW. Mock client records the system prompt; test asserts the variant's Identity Activation block is present.
- `tests/test_ab_harness.py::test_aggregate_runs_reports_mean_and_stddev` — NEW. Given 5 mock runs with detection rates `[0.5, 0.6, 0.55, 0.52, 0.58]`, returns `{mean: 0.55, stddev_pp, n: 5}`.
- `tests/test_ab_harness.py::test_variants_load_strips_persona_names` — NEW (F4). Stance variant files do not contain persona name tokens (`Judge`, `Specialist`, `Analyst`, `Governor`, `Technical Writer`).
- `tests/test_ab_harness.py::test_variants_load_preserves_stance_modifier` — NEW (F4). Stance variant files contain the same stance modifier keyword as the persona variant.
- `tests/test_ab_harness.py::test_ab_live_run_exits_clearly_without_api_key` — NEW. Setting `ANTHROPIC_API_KEY=""` and invoking `ab_live_run.py` exits non-zero with the env-var name in stderr.

## Phase 3 — Run A/B on `/qor-audit` AND `/qor-substantiate`

### Affected Files

- `docs/phase39-ab-results.md` — NEW. Committed evidence artifact. Contains per-skill detection rates, deltas, and winner declarations.
- `qor/skills/governance/qor-audit/SKILL.md` — Identity Activation block may be retained or rewritten based on Phase 3 outcome (change deferred to Phase 4).
- `qor/skills/governance/qor-substantiate/SKILL.md` — same as above.
- `tests/test_phase39_ab_results.py` — NEW. Asserts results artifact exists and contains the 4 required data points.

### Changes

Operator runs `python qor/scripts/ab_live_run.py` once, which hits the Anthropic API for all 400 calls serially. Requires `ANTHROPIC_API_KEY` env var set; script exits clearly if absent.

Script behavior:
- 5 runs per `(skill, variant)` combination: `/qor-audit × persona × 5`, `/qor-audit × stance × 5`, `/qor-substantiate × persona × 5`, `/qor-substantiate × stance × 5`.
- Total: 20 harness invocations × 20 defects = 400 API calls, ~$4 cost, ~10-15 min wall-time.
- Aggregates per-(skill, variant) into mean detection rate + stddev via `aggregate_runs`.
- Produces `docs/phase39-ab-results.md` with the structure below.
- Writes `.qor/gates/<session>/ab-run.json` with raw per-run data for audit trail (inside gitignored `.qor/` — not pushed, operator can share if needed).

Results artifact `docs/phase39-ab-results.md` structure:

```markdown
# Phase 39 A/B Harness Results

**Corpus**: 20 seeded defects across 10 findings_categories
**Runs per variant**: 5
**Comparison threshold**: ±5 percentage points = tie

## /qor-audit
| Variant | Detection rate (mean, n=5) | Std dev |
|---|---|---|
| persona (Identity Activation as-shipped) | XX.X% | X.X pp |
| stance-directive only | YY.Y% | Y.Y pp |

**Delta**: <stance - persona> pp. **Winner**: persona | stance | tie.

## /qor-substantiate
... (same structure)

## Decision gate for Phase 4

- Winner = `stance` → Phase 4 rewrites Identity Activation blocks to stance-directive-only.
- Winner = `persona` → Phase 4 retains current persona-named blocks; doctrine §2 annotation records the evidence.
- Winner = `tie` → Phase 4 retains persona names for ergonomic readability per operator directive ("flavor isn't a requirement; performance, accuracy, results are" — ties default to readability).
```

### Unit Tests (TDD — written first)

- `tests/test_phase39_ab_results.py::test_results_artifact_exists` — NEW.
- `tests/test_phase39_ab_results.py::test_results_contains_both_skills` — NEW. `/qor-audit` and `/qor-substantiate` sections present.
- `tests/test_phase39_ab_results.py::test_results_declares_winner_per_skill` — NEW. Each skill section has `**Winner**:` line.
- `tests/test_phase39_ab_results.py::test_results_corpus_size_is_20` — NEW. Matches plan declaration.

## Phase 4 — Apply findings

### Affected Files

- `qor/skills/**/SKILL.md` — ALL files with `<persona>` frontmatter (~30). Sweep per Phase 3 evidence + doctrine §2 rule.
- `qor/skills/governance/qor-audit/SKILL.md` — Identity Activation rewrite conditional on Phase 3 winner.
- `qor/skills/governance/qor-substantiate/SKILL.md` — same.
- `qor/skills/sdlc/qor-debug/SKILL.md` — promote the line-108 `subagent_type: "general"` constraint into a cross-reference to doctrine §4.
- `qor/skills/memory/qor-document/SKILL.md` — disambiguate the persona-vs-agent conflation at line 252 per research brief R5.
- `qor/references/doctrine-governance-enforcement.md` — §11 formally references context-discipline doctrine as binding.
- `tests/test_persona_sweep.py` — NEW. Enforces: every surviving `<persona>` tag either links to A/B evidence OR appears in the doctrine-registered "load-bearing" list.

### Changes

**S3 persona sweep** (from RESEARCH_BRIEF R2 + the 5 decorative-only skills identified in Pass 1):

1. Inventory every `<persona>` tag across `qor/skills/**/SKILL.md`.
2. Classify per doctrine §2: does the persona prioritize context for edge-case determinations that a bare directive would not?
3. Remove decorative tags. Initial target list (from Pass 1 research): `qor-status`, `qor-help`, `qor-document`, `qor-repo-scaffold`, `qor-refactor` integration-section, `qor-bootstrap`, `qor-meta-log-decision`. Evidence for additional removals comes from Phase 3 A/B results.
4. Retain load-bearing tags with an added `<persona-evidence>` pointer line (to `docs/phase39-ab-results.md`) for audit trail.

**R3 Identity Activation rewrite** (conditional):

Only fires if Phase 3 declares `winner: "stance"` for the target skill. Example rewrite (if stance wins for `/qor-audit`):

Before:
```
### Step 1: Identity Activation + Mode Selection
You are now operating as **The QorLogic Judge** in adversarial mode.
```

After:
```
### Step 1: Stance + Mode Selection
**Stance**: adversarial. Any ambiguity defaults to VETO. Role is to prove the work is unsealable, not to make it sealable.
```

**R4 qor-debug lesson generalization**: line 108 constraint `**ALWAYS** use subagent_type: "general"` stays; add cross-reference line `See doctrine-context-discipline.md §4 for the general rule.` The doctrine rule becomes the canonical source; the skill constraint becomes an instance.

**R5 qor-document disambiguation**: line 252 `Technical Writer Persona: Pairs with qor-technical-writer agent for quality` rewritten into two separate lines — one for the main-thread Identity Activation, one for the subagent file pairing — so an implementer cannot conflate the two mechanisms.

### Unit Tests (TDD — written first)

- `tests/test_persona_sweep.py::test_every_persona_tag_has_evidence_or_is_load_bearing` — NEW. For each `<persona>` tag in `qor/skills/**/SKILL.md`: either file contains `<persona-evidence>` pointer OR skill is in the doctrine-registered load-bearing list.
- `tests/test_persona_sweep.py::test_decorative_persona_targets_removed` — NEW. `qor-status`, `qor-help`, `qor-document`, `qor-repo-scaffold`, `qor-bootstrap`, `qor-meta-log-decision` SKILL.md files no longer contain `<persona>` frontmatter.
- `tests/test_persona_sweep.py::test_qor_debug_references_context_discipline_doctrine` — NEW. Skill prose cites §4 of the new doctrine.
- `tests/test_persona_sweep.py::test_qor_document_disambiguates_persona_and_agent` — NEW. Two distinct sentences, one per mechanism; grep asserts "Identity Activation" appears separately from "qor-technical-writer agent".
- `tests/test_persona_sweep.py::test_identity_activation_matches_ab_winner` — NEW. For each stance-critical skill: if `docs/phase39-ab-results.md` declares `winner: "stance"`, skill's Step 1 body does not contain `"You are now operating as"` persona opener; if `winner: "persona" | "tie"`, persona opener retained.

## CI Commands

- `pytest tests/test_doctrine_context_discipline.py` — Phase 1 targeted.
- `pytest tests/test_ab_harness.py` — Phase 2 targeted (mocked; no API calls).
- `pytest tests/test_phase39_ab_results.py` — Phase 3 targeted (validates results artifact once operator-produced).
- `pytest tests/test_persona_sweep.py` — Phase 4 targeted.
- `pytest` — full suite at seal (no live API calls).
- `pip install -e .[ab-harness]` — install the optional harness dependency when operator is running the live cycle (not required for CI).
- `ANTHROPIC_API_KEY=... python qor/scripts/ab_live_run.py` — operator-only; produces `docs/phase39-ab-results.md`. NOT a CI command.
- `python -m qor.reliability.skill_admission qor-audit qor-substantiate qor-debug qor-document` — admission on skills with prose changes.
- `python -m qor.reliability.gate_skill_matrix` — handoff integrity.
- `python qor/scripts/doc_integrity_strict.py` — terms_introduced have canonical homes.

## Phase ordering rationale

Phases 1-3 must land in order (doctrine → harness → evidence). Phase 4 depends on Phase 3 evidence for conditional rewrites (R3 fires or skips per winner). Phase 2's harness is test-only infrastructure — it ships as part of the repo but runs only when explicitly invoked via `ab_live_run.py`; it does not modify skill behavior. Phase 3's live run happens once at operator direction (not in CI) and commits the results artifact as evidence for Phase 4.

## V1 resolution summary (Pass 2 amendment)

Pass 1 VETO V1: harness had no mechanism to invoke slash-command skills. Pass 2 adopts resolution (a): direct Anthropic SDK invocation.

- New optional dependency `anthropic>=0.40,<1.0` under `[project.optional-dependencies].ab-harness`. Not pulled by default installs.
- `ab_harness.run` accepts an injected client; production uses `anthropic.Anthropic()` reading `ANTHROPIC_API_KEY` from env; tests inject mocks.
- Clear separation: `ab_harness.py` is pure library (mockable, CI-testable); `ab_live_run.py` is the operator CLI that actually hits the API.
- Cost (~$4 per cycle) and rate limits (serial calls, ~10-15 min) disclosed in the harness module docstring.
- Non-determinism quantified via stddev across n=5 runs; results artifact reports both mean and stddev so readers can distinguish real effects from noise.

Other Pass 1 findings resolved:
- F1: "~30 skills" → "24 skills" (grep-verified).
- F2: `# SEEDED TEST DEFECT — NOT EXECUTABLE` header required on all corpus fixtures; enforced by test.
- F3: n=5 justified against LLM non-determinism; stddev tracked; results report both.
- F4: Variants are hand-authored markdown files under `tests/fixtures/ab_corpus/variants/`, not programmatic.
- F5: MANIFEST defect shape uses `line_start` + `line_end` to handle multi-line defects.
