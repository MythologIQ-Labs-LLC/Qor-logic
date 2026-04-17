# AUDIT REPORT -- plan-qor-phase25-prompt-resilience-and-seed.md (Pass 3)

**Tribunal Date**: 2026-04-17
**Target**: `docs/plan-qor-phase25-prompt-resilience-and-seed.md`
**Risk Grade**: L1
**Auditor**: The QorLogic Judge
**Mode**: Solo (codex-plugin capability shortfall logged)
**Prior Audits**: Entry #76 (VETO, A08) -> Entry #77 (VETO, ghost feature) -> this pass

---

## VERDICT: **PASS**

Both prior VETO grounds cleared. No new violations surfaced under adversarial review.

---

## Pass 1: Security (L3) -- PASS

No auth, no secrets, no bypass. Tier system adds metadata + rendering guidance only; no new attack surface.

## Pass 2: OWASP Top 10 -- PASS

- **A08** (cleared in Pass 2 of Entry #77): `yaml.safe_load` commitment holds across all three new test-file blocks. Widened discipline test scope to `tests/**/*.py` with `tests/fixtures/` excluded remains in the plan. Planted-call negative test still required.
- A03, A04, A05: unchanged pass.

## Pass 3: Ghost UI / Ghost Feature -- **PASS** (SG-Phase25-B closed)

The four mandated remediations from Entry #77 all landed in plan text:

1. **Phase 4 Changes (skill bulk edit)**: every `tone_aware: true` skill gains a `## Output rendering by tone` section delimited by `<!-- qor:tone-aware-section -->` / `<!-- /qor:tone-aware-section -->` markers (plan line 364), three sub-sections (`### technical`, `### standard`, `### plain`) with non-empty content lines per tier (line 365), and a shared preamble paragraph pasted from the doctrine doc (line 366).
2. **Phase 4 Unit Tests (`test_tone_skill_frontmatter.py`)**: asserts markers are present (open + close), all three tier names appear, each tier has at least one non-empty non-blank content line, and "tier-name followed immediately by another tier name or the closing marker" fails the test (plan lines 325-330). Test output names file:line and specific missing element.
3. **Phase 4 Changes (doctrine)**: `doctrine-communication-tiers.md` now required to carry a `## How skills read the tone value` section explaining session-override -> config -> default resolution, the `qor.tone.resolve_tone` helper, and the markdown preamble pattern (plan line 358). `test_tone_resolution.py` asserts this section exists (line 310).
4. **Phase 4 Unit Tests (new file)**: `tests/test_tone_rendering_example.py` pins `qor/skills/memory/qor-status/SKILL.md` (verified to exist in repo) as the canonical reference example and asserts each tier's sub-section matches tier-register heuristics (plan lines 331-337). Anchors the doctrine in at least one worked example.

Adversarial scenario from Entry #77 reconsidered: operator runs `qorlogic init --tone plain`, expects skills to render in plain language. Now: `tone_aware: true` flag is load-bearing because (a) lint requires the rendering section with tier-specific content; (b) doctrine includes the skill-side lookup pattern; (c) canonical example anchors the doctrine. Metadata claim is tied to body content, config value has a documented consumer, and at least one skill is proven to conform.

Residual observation (not a VETO): the per-tier rendering heuristics (technical has SG/OWASP tag, standard has complete sentence without SG, plain has no jargon / no hash token) are loose regex shape-enforcement, not content-validation. An adversarial author could technically bypass them with creative prose. Plan acknowledges this trade-off explicitly (line 337: "authors retain editorial freedom while the shape is enforced"). The shape test catches obvious ghosts -- the strictest-possible content test would require LLM evaluation, which is out of reach for a unit-test framework. Accepted trade-off.

## Pass 4: Section 4 Razor -- PASS (with monitoring)

| Check | Limit | Blueprint Proposes | Status |
|-------|-------|---------------------|--------|
| `qor/seed.py` | 250 | 80-120 | OK |
| `qor/tone.py` | 250 | 30-40 | OK |
| `qor/cli.py` | 250 | 210 + ~6 (seed + --tone) = ~216 | OK |
| `qor/cli_policy.py` | 250 | 103 + ~5 (tone persistence) = ~108 | OK |
| `qor/scripts/gemini_variant.py` | 250 | 127 (unchanged this phase) | OK |
| Lint-test main fn | 40 | est. 25-35 if decomposed | OK, watch |
| `resolve_tone` fn | 40 | 12-18 | OK |
| `seed` fn | 40 | 15-20 | OK |
| Nesting | 3 | 2 | OK |
| Nested ternaries | 0 | 0 | OK |

No Razor VETO. Lint-test main function remains on watch per prior passes; implementer must decompose into `_check_banned_phrases`, `_check_abort_markers_interactive`, `_check_abort_markers_autonomous`, `_check_autonomous_purity`, `_check_tone_aware_sections`.

## Pass 5: Dependency Audit -- PASS

No new packages. Seed uses stdlib + `qor.resources`. Tone uses stdlib + existing `PyYAML` (Phase 24). Runtime deps locked at `["jsonschema>=4", "PyYAML>=6"]` with dependency-shape tests preserving the lock.

## Pass 6: Macro-Level Architecture -- PASS

- **Phase orthogonality**: seed (Phase 1), resilience doctrine (Phase 2), resilience application (Phase 3), tone tiers (Phase 4) are four independent concerns with independent enforcement tests. Each phase has exactly one doctrine file, one lint test, one SSoT reference where applicable. No complecting.
- **Autonomy vs Tone**: two parallel frontmatter keys (`autonomy`, `tone_aware`), two parallel lint tests, no cross-coupling. A `tone_aware: true` autonomous skill is legal (e.g., `qor-deep-audit-recon` prose-summary renders tone-aware output without user prompts).
- **Evidentiary boundary intact**: `tone_aware: false` required for ledger/shadow-genome/gate-artifact writers. Heuristic check + declarative freeze list (belt + suspenders per plan line 321).
- **Slash-command layering clean**: `/qor-tone` handled by agent host, `qorlogic init --tone` handled by Python CLI, `qor.tone.resolve_tone` provides Python callers the effective tier. Three surfaces, three responsibilities, no cross-boundary coupling.
- **Caveman attribution**: plan cites MIT-licensed source for tier concept (line 17). Compliance + transparency preserved.

## Pass 7: Orphan Detection -- PASS

Every new or edited file connects:

| Proposed File | Entry Point Connection | Status |
|---------------|------------------------|--------|
| `qor/seed.py` | CLI dispatch | Connected |
| `qor/tone.py` | `do_init` + documented skill runtime callers | Connected |
| `qor/templates/*.md` | `qor/seed.py` via `qor.resources` | Connected |
| `qor/references/doctrine-prompt-resilience.md` | Lint cross-check | Connected |
| `qor/references/doctrine-communication-tiers.md` | `test_tone_resolution.py` presence assertion | Connected |
| `qor/references/skill-recovery-pattern.md` | Lint SSoT | Connected |
| `tests/fixtures/skill_*.md` (4) | Lint positive controls | Connected |
| `tests/fixtures/skill_tone_aware_*.md` (2) | `test_tone_evidentiary_exclusion.py` | Connected |
| `tests/fixtures/bad_unsafe_call.py` (plant) | Widened discipline test | Connected |
| `tests/test_seed_scaffold.py` | Pytest discovery | Connected |
| `tests/test_cli_seed.py` | Pytest discovery | Connected |
| `tests/test_prompt_resilience_lint.py` | Pytest discovery | Connected |
| `tests/test_skill_prerequisite_coverage.py` | Pytest discovery | Connected |
| `tests/test_tone_resolution.py` | Pytest discovery | Connected |
| `tests/test_tone_config_persistence.py` | Pytest discovery | Connected |
| `tests/test_tone_evidentiary_exclusion.py` | Pytest discovery | Connected |
| `tests/test_tone_skill_frontmatter.py` | Pytest discovery | Connected |
| `tests/test_tone_rendering_example.py` | Pytest discovery; pins `qor/skills/memory/qor-status/SKILL.md` (verified present) | Connected |
| Edited skill files (12 under `qor/skills/`) | Existing variant-compile pipeline | Connected |

---

## Summary

| Ground | #76 | #77 | **#78 (this pass)** |
|--------|-----|-----|---------------------|
| A08 / test-scope | VETO | PASS (cleared) | PASS |
| Ghost feature / `tone_aware` | -- | VETO | **PASS** (cleared) |

Plan cleared for implementation. No further VETO grounds identified under this pass.

## Advisory / Monitor (not binding)

1. **Razor-lint function length**: implementer must decompose the lint test's main walker into per-check helpers to stay under 40 lines (flagged every pass; implementation responsibility).
2. **Shared preamble drift**: the "pasted from doctrine" preamble in each tone-aware skill is enforced for presence (markers + tier content) but not for wording equality with the doctrine source. Long-term, this may drift. Not a Phase 25 blocker; candidate for a future lint tightening.
3. **Chain drift carried forward**: Phase 23 commit `8081422` still lacks a ledger entry; Phase 25 seal will bridge directly from `68772fd3...` (Phase 24) after substantiation. Operator should decide whether to backfill Phase 23 before sealing Phase 25.

## Next Action

`/qor-implement` -- per delegation table, PASS hands off to implementation. TDD order per plan:

- Phase 1 tests first -> Phase 1 code
- Phase 2 tests first -> Phase 2 code
- Phase 3 tests first -> Phase 3 skill edits
- Phase 4 tests first -> Phase 4 code + doctrine + skill edits

Change class on seal: `feature` -> 0.15.0 -> 0.16.0.
