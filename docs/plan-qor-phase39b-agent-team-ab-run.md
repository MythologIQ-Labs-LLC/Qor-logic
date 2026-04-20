# Plan: Phase 39b — Agent Team A/B run + persona sweep

**change_class**: feature
**target_version**: v0.30.0
**doc_tier**: system
**pass**: 1

**Scope**: Replaces the Phase 39 Phase 2 Anthropic-SDK harness that was withdrawn pre-merge (META_LEDGER #136). Ships a `/qor-ab-run` skill that orchestrates A/B measurement via parallel Task-tool subagent dispatch within Claude Code. Operator invokes the skill, results land in `docs/phase39-ab-results.md`, persona sweep applies findings. No external API dependency; no credential management; dogfoods the doctrine's "controlled context via subagents" principle.

**terms_introduced**:
- `A/B trial` — a single (skill, variant, replication, defect-list) measurement unit produced by one subagent dispatch. Home: `qor/skills/meta/qor-ab-run/SKILL.md` + `qor/scripts/ab_aggregator.py`.
- `A/B trial batch` — 20 trials for one (skill, variant, replication): one subagent receives all 20 fixtures in a single dispatch, returns per-defect findings_categories. Home: same.

**Source**:
- `docs/plan-qor-phase39-context-discipline.md` (original plan; withdrawal scoped Phase 2 out).
- META_LEDGER Entry #136 (scope amendment accepting Agent Team orchestration).
- `tests/fixtures/ab_corpus/` (20 defects + MANIFEST + 4 variants; shipped in v0.29.0).
- `qor/references/doctrine-context-discipline.md` §4 (subagent invocation rule).

## Open Questions

None. Orchestration architecture (Task-tool parallel dispatch), batching strategy (one subagent per `(skill, variant, replication)` = 20 total dispatches), and replication count (N=5) are locked.

## Non-goals

- No external API calls. No `anthropic` SDK dep. No `ANTHROPIC_API_KEY` env var.
- No programmatic Python harness. The skill IS the orchestrator.
- No changes to v0.29.0 doctrine or corpus fixtures. Both are consumed as-is.
- No change to the 22 skills outside `/qor-audit` and `/qor-substantiate` Identity Activation blocks. The A/B produces evidence only for those two; other skills' persona tags are evaluated by doctrine §2 judgment alone (decorative → remove; load-bearing → retain with rationale).

## Phase 1 — `/qor-ab-run` skill + aggregator

### Affected Files

- `qor/skills/meta/qor-ab-run/SKILL.md` — NEW. Orchestration skill. Step-by-step prose directing Claude Code to dispatch 20 Task subagents in parallel, wait for results, call aggregator, write results artifact.
- `qor/skills/meta/qor-ab-run/references/ab-subagent-prompt.md` — NEW. The prompt template each subagent receives. Contains the variant Identity Activation block placeholder, fixture-concat format, required JSON response shape.
- `qor/scripts/ab_aggregator.py` — NEW (~90 LOC, 3 functions). Pure Python: parses subagent JSON responses, aggregates per (skill, variant), renders markdown. Zero LLM coupling.
- `qor/gates/delegation-table.md` — add row for `/qor-ab-run` as a cross-cutting measurement skill (no fixed handoff; invoked directly by operator).
- `tests/test_qor_ab_run_skill.py` — NEW. Structural assertions: skill declares Task-tool orchestration, references the 4 variant files and MANIFEST, cites the aggregator and results-artifact path.
- `tests/test_ab_aggregator.py` — NEW. Unit tests against synthetic trials.

### Changes

**Skill orchestration (SKILL.md prose)**:

```
Step 0: Gate check. Verify tests/fixtures/ab_corpus/MANIFEST.json and the 4
        variant files exist. Abort if absent.
Step 1: Load the manifest (20 defects) and 4 variant files.
Step 2: For each (skill in {qor-audit, qor-substantiate}, variant in {persona,
        stance}, replication in 1..5): construct a Task subagent dispatch with:
        - subagent_type: "general"  (per doctrine §4)
        - description: "A/B trial: {skill}/{variant}/rep{replication}"
        - prompt: the ab-subagent-prompt template, spliced with the variant
          Identity Activation block and all 20 fixture contents.
Step 3: Dispatch ALL 20 Task calls in a single message (parallel execution).
        Wait for all results. Each subagent returns JSON:
          {"trials": [{"defect_id": N, "findings_categories": [...]}, ...]}
Step 4: Call ab_aggregator.aggregate(trial_results) to produce per-(skill,
        variant) mean+stddev detection rates and winner declarations.
Step 5: Call ab_aggregator.render_markdown(aggregated) and write to
        docs/phase39-ab-results.md.
Step 6: Write gate artifact .qor/gates/<sid>/ab-run.json with raw trial data
        + aggregate for audit trail.
```

**Aggregator API**:

`ab_aggregator.parse_trial(raw_response: str, defect_ids: list[int]) -> dict`:
- Extracts `{"trials": [...]}` JSON from a subagent's text response.
- Validates each trial has `defect_id` in `defect_ids` and `findings_categories` is a list.
- Returns `{"trials": [{"defect_id": N, "findings_categories": [...]}, ...]}`.
- On parse failure: returns trials with empty `findings_categories` (counted as missed detections).

`ab_aggregator.aggregate(trial_batches: list[dict]) -> dict`:
- Input: list of `{"skill", "variant", "replication", "trials": [...]}` records.
- Groups by `(skill, variant)`. For each group:
  - Computes per-replication detection rate: `# defects where planted category ∈ findings_categories / 20`.
  - Aggregates across replications: `mean_detection_rate`, `stddev_pp`, `n`.
- Then per-skill computes `winner` via `ab_harness.compare`-style logic (delta threshold ±5pp).
- Returns `{"per_skill": {skill: {"persona": {...}, "stance": {...}, "comparison": {...}}}}`.

`ab_aggregator.render_markdown(aggregated: dict) -> str`:
- Produces the `docs/phase39-ab-results.md` body per the template documented inline.
- Includes: corpus size, runs per variant, tie threshold, per-skill table with mean/stddev, delta, winner.

**ab-subagent-prompt.md** contents (loaded by skill; spliced into each Task dispatch):

```
{VARIANT_IDENTITY_ACTIVATION_BLOCK}

You are reviewing 20 source-code fixtures for defects. The fixtures may contain
planted defects from this closed enum: [12-value findings_categories list].

For each fixture, emit a JSON record with its defect_id and the
findings_categories you detect. Respond with exactly one JSON object:
{"trials": [{"defect_id": 1, "findings_categories": [...]}, ...]}

Fixtures follow:
{FIXTURES_CONCATENATED}
```

### Unit Tests (TDD — written first)

- `tests/test_qor_ab_run_skill.py::test_skill_file_exists` — NEW.
- `tests/test_qor_ab_run_skill.py::test_skill_declares_task_tool_orchestration` — NEW. Skill prose references "Task" (tool name) and "parallel" dispatch.
- `tests/test_qor_ab_run_skill.py::test_skill_references_corpus_manifest` — NEW.
- `tests/test_qor_ab_run_skill.py::test_skill_references_4_variant_files` — NEW.
- `tests/test_qor_ab_run_skill.py::test_skill_declares_subagent_type_general` — NEW. Per doctrine §4.
- `tests/test_qor_ab_run_skill.py::test_skill_declares_5_replications` — NEW.
- `tests/test_qor_ab_run_skill.py::test_skill_writes_results_artifact_path` — NEW. Prose cites `docs/phase39-ab-results.md`.
- `tests/test_qor_ab_run_skill.py::test_subagent_prompt_template_has_placeholders` — NEW. References file has `{VARIANT_IDENTITY_ACTIVATION_BLOCK}` and `{FIXTURES_CONCATENATED}` placeholders.
- `tests/test_ab_aggregator.py::test_parse_trial_extracts_valid_json` — NEW.
- `tests/test_ab_aggregator.py::test_parse_trial_tolerates_malformed_as_empty` — NEW. Non-JSON response → empty findings (counted as miss).
- `tests/test_ab_aggregator.py::test_aggregate_groups_by_skill_and_variant` — NEW.
- `tests/test_ab_aggregator.py::test_aggregate_computes_mean_and_stddev_per_group` — NEW.
- `tests/test_ab_aggregator.py::test_aggregate_declares_winner_above_5pp` — NEW.
- `tests/test_ab_aggregator.py::test_aggregate_declares_tie_below_5pp` — NEW.
- `tests/test_ab_aggregator.py::test_render_markdown_includes_per_skill_section` — NEW.
- `tests/test_ab_aggregator.py::test_render_markdown_includes_winner_declaration` — NEW.

## Phase 2 — persona sweep + conditional Identity Activation rewrites

**Dependency**: runs AFTER operator invokes `/qor-ab-run` and `docs/phase39-ab-results.md` exists. If the operator ships v0.30.0 without running the A/B first, Phase 2's R3 rewrites fall back to doctrine-judgment-only (no rewrite unless doctrine indicates clear decorative status).

### Affected Files

- `qor/skills/**/SKILL.md` — 24 files carrying `<persona>` frontmatter. Sweep per doctrine §5.
- `qor/skills/governance/qor-audit/SKILL.md` — Identity Activation rewrite conditional on A/B results.
- `qor/skills/governance/qor-substantiate/SKILL.md` — same.
- `qor/skills/sdlc/qor-debug/SKILL.md` — add doctrine §4 cross-reference at the line-108 `subagent_type: "general"` constraint (R4).
- `qor/skills/memory/qor-document/SKILL.md` — disambiguate persona-vs-agent at line 252 (R5).
- `tests/test_persona_sweep.py` — NEW. Enforces every surviving `<persona>` tag either carries `<persona-evidence>` pointer or belongs to the doctrine-exempt list.
- `docs/phase39-ab-results.md` — consumed, not modified.

### Changes

**S3 persona sweep**:

1. Inventory every `<persona>` tag across `qor/skills/**/SKILL.md` (24 total per grep).
2. Classify per doctrine §2:
   - **Decorative** (persona prioritizes no edge-case context beyond a bare directive): remove the frontmatter tag entirely.
   - **Load-bearing** (persona measurably prioritizes context; evidence available from A/B or future measurement): retain and add a `<persona-evidence>` pointer to the evidence artifact.
   - **Load-bearing-pending-evidence** (doctrine judgment suggests load-bearing but no A/B yet): retain with a TODO comment pointing at a future measurement cycle; no evidence pointer yet. Allowed as transitional state.
3. Initial decorative target list (from Pass 1 research): `qor-status`, `qor-help`, `qor-document` (frontmatter only — body text for R5 disambiguation), `qor-repo-scaffold`, `qor-bootstrap`, `qor-meta-log-decision`.

**R3 Identity Activation rewrite (conditional)**:

For `/qor-audit` and `/qor-substantiate` specifically:
- Read `docs/phase39-ab-results.md` if present.
- If `winner == "stance"` for a skill: rewrite that skill's Step 1 Identity Activation block to stance-directive-first phrasing (strip "You are now operating as **The QorLogic Judge**" opener; retain modifier like "adversarial mode").
- If `winner == "persona"` or `winner == "tie"`: retain current persona-named block. Add a `<persona-evidence>` pointer line to frontmatter.
- If `docs/phase39-ab-results.md` is absent: skip R3 for both skills (doctrine-judgment-only doesn't rewrite without evidence; operator must run `/qor-ab-run` first and amend Phase 2 to include R3).

**R4 qor-debug doctrine cross-reference**:

Line 108 constraint `**ALWAYS** use subagent_type: "general"` retained. Add below it:
> See `qor/references/doctrine-context-discipline.md` §4 (Subagent invocation rule) for the general doctrine.

**R5 qor-document disambiguation**:

Line 252 currently reads something like `Technical Writer Persona: Pairs with qor-technical-writer agent for quality`. Split into two discrete sentences:
1. Identity Activation (main thread): "Operator-facing documentation authoring uses the Technical Writer stance — precision-focused, glossary-consistent, reader-over-writer."
2. Subagent pairing (separate mechanism): "Substantial rewrites delegate to the `qor-technical-writer` subagent via `Task(subagent_type=\"qor-technical-writer\")` for parallel research + draft."

### Unit Tests (TDD — written first)

- `tests/test_persona_sweep.py::test_every_persona_tag_has_evidence_or_pending` — NEW. For each `<persona>` tag in `qor/skills/**/SKILL.md`: either carries `<persona-evidence>` pointer OR a `<persona-pending>` placeholder OR is in the doctrine-exempt list.
- `tests/test_persona_sweep.py::test_decorative_targets_removed` — NEW. `qor-status`, `qor-help`, `qor-document` (frontmatter), `qor-repo-scaffold`, `qor-bootstrap`, `qor-meta-log-decision` no longer carry `<persona>` frontmatter.
- `tests/test_persona_sweep.py::test_qor_debug_references_context_discipline_doctrine` — NEW. Skill prose cites §4 of the new doctrine.
- `tests/test_persona_sweep.py::test_qor_document_disambiguates_persona_and_agent` — NEW. Two distinct sentences, one for Identity Activation stance, one for subagent pairing.
- `tests/test_persona_sweep.py::test_identity_activation_matches_ab_winner_if_results_exist` — NEW. If `docs/phase39-ab-results.md` is present and declares `winner: "stance"` for a skill, that skill's Step 1 body does not contain the `"You are now operating as"` persona opener. If absent or winner is persona/tie, opener retained.

## CI Commands

- `pytest tests/test_qor_ab_run_skill.py tests/test_ab_aggregator.py` — Phase 1 targeted.
- `pytest tests/test_persona_sweep.py` — Phase 2 targeted.
- `pytest` — full suite at seal.
- `python -m qor.reliability.skill_admission qor-ab-run qor-audit qor-substantiate qor-debug qor-document` — admission on skills with prose changes.
- `python -m qor.reliability.gate_skill_matrix` — handoff integrity; persona frontmatter removal must not break any handoff reference.
- `python qor/scripts/doc_integrity_strict.py` — terms_introduced have canonical homes.

## Phase ordering rationale

Phase 1 (skill + aggregator) ships independently of operator A/B run — the skill CAN be invoked; whether evidence exists when Phase 2 lands depends on operator timing. Phase 2 is gated by doctrine-judgment for decorative removals (operator can do these without A/B), and conditionally applies A/B evidence for R3 Identity Activation rewrites of `/qor-audit` and `/qor-substantiate`. If operator ships Phase 2 before running Phase 1's A/B, R3 is a no-op (doctrine-judgment does not rewrite stance-critical skills without evidence).
