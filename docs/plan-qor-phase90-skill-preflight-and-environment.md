# Plan: Phase 90 — Skill preflight + Environment contract for Python-dependent invocations (GH #79)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #79

**boundaries**:
- limitations: V1 ships only Options C (preflight diagnostic, WARN-only)
  and D (Environment block, doc-only) from GH #79's four-option menu.
  Option A (self-resolving `qor-logic <subcommand>` CLI dispatch) and
  Option B (install-time `${QOR_PYTHON}` path-rewriting) are NOT
  implemented in V1 — both are larger architectural shifts that would
  benefit from a V2 plan after operators have evidence on how
  effectively the C+D combination converts the silent-skip pattern
  into visible misconfiguration. The preflight is WARN-only (not
  ABORT) so the Phase 75 declarative-tolerance pattern remains intact
  on non-Python hosts; the misconfiguration is now visible at skill
  entry instead of revealing itself through accumulated
  `gate_skipped_prerequisite_absent` events.
- non_goals: changing the underlying SKIP behavior (Phase 75 V1 still
  applies — non-Python hosts and prereq-absent hosts continue to log
  SKIP and emit `gate_skipped_prerequisite_absent`); adding a new CLI
  subcommand surface (Option A; future phase); rewriting skill markdown
  at install time (Option B; future phase); per-invocation preflight
  (the issue's literal "prepend each reliability step" reading) — V1
  uses one preflight per skill at entry, since the misconfiguration
  manifests the same way regardless of which downstream call trips
  first.
- exclusions: no changes to the underlying `qor.reliability.*` or
  `qor.scripts.*` modules; no changes to `qor/installer.py` or
  variant-emission code paths; no changes to the Phase 75 SKIP-logging
  prose in `## Step Prerequisites` blocks (kept verbatim — the new
  Environment block is layered above, not in place of). No new CI
  workflow.

## Open Questions

None.

## Feature Inventory Touches

Empty. This plan touches governance/SDLC skill bodies and adds a new
behavior test under `tests/`; it introduces no `src/` user-facing
feature. `feature_inventory_touches`: `[]`.

## Design notes

GH #79 documents a credibility-erosion pattern: skills shell out to
bare `python -m qor.reliability.*` and `python -m qor.scripts.*`, but
the modules only resolve when the install venv is active. The Phase
75 V1 fix (`gate_skipped_prerequisite_absent` declarative tolerance)
made the failure mode survivable but silent — operators on hosts
where the venv is not active see SKIP events in the shadow genome
and (per the originating consumer-workspace evidence in the issue) "treat
them as normal, rather than realising the gates are recoverable with
a one-line venv activation." Seal entries land with quietly-incomplete
gate coverage; trust in the seal's "all gates ran" claim erodes.

The user-filer's recommendation is **A + D** (CLI dispatch + documented
contract). User-operator scope choice for this phase is **C + D** —
preflight diagnostic + Environment block — as the smallest-viable
visibility fix that doesn't preclude A or B in a future phase. The
preflight makes the misconfiguration visible at skill entry (one WARN
line per invocation) before Phase 75's SKIP cascade begins; the
Environment block documents the install contract so operators learn
the fix without having to read GH #79.

The preflight is WARN-only, not ABORT, by deliberate design choice.
Phase 75's declarative tolerance MUST continue to work on legitimately
non-Python hosts (e.g., a pure-Rust archetype using Qor-logic for
governance via the non-Python variant skills). An ABORT preflight
would break those operators. The WARN form makes the
misconfiguration visible to Python-archetype operators while leaving
non-Python operators undisturbed — the Phase 75 SKIP path still
exercises and they see no false-positive abort.

Per `[[feedback-progressive-disclosure]]` (the GH #92 corpus-bloat
lesson), the change is kept lean: one Environment block per skill
(~10 lines), one preflight one-liner per skill (~5 lines as a
multi-line shell snippet), no new doctrine file, no new script. The
preflight is inline bash so it works in consumer-repo contexts where
no `qor/` filesystem tree is present.

Skills affected (7 SKILL.md files in `qor/skills/` that grep-match
`python -m qor\.(reliability|scripts)`):

1. `qor/skills/governance/qor-audit/SKILL.md`
2. `qor/skills/governance/qor-process-review-cycle/SKILL.md`
3. `qor/skills/governance/qor-shadow-process/SKILL.md`
4. `qor/skills/governance/qor-substantiate/SKILL.md`
5. `qor/skills/meta/qor-repo-audit/SKILL.md`
6. `qor/skills/sdlc/qor-implement/SKILL.md`
7. `qor/skills/sdlc/qor-plan/SKILL.md`

The reference file `qor/skills/governance/qor-audit/references/phase37-subpasses.md`
also matches the grep but is loaded BY `qor-audit/SKILL.md` (progressive
disclosure target from Phase 83); the preflight in qor-audit's SKILL.md
covers it transitively. The reference file is NOT modified.

The Phase 75 `## Step Prerequisites` section in skills that have it
(`qor-substantiate`, possibly others) is kept verbatim — the new
`## Environment` block sits ABOVE it (after `## Purpose`), providing
the broader environment contract that Step Prerequisites depends on.

## Phase 1: Environment block + preflight one-liner + lint enforcement

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` — add `## Environment`
  block after `## Purpose`; add preflight one-liner at the top of
  `## Execution Protocol`.
- `qor/skills/governance/qor-process-review-cycle/SKILL.md` — same shape.
- `qor/skills/governance/qor-shadow-process/SKILL.md` — same shape.
- `qor/skills/governance/qor-substantiate/SKILL.md` — same shape; the
  existing `## Step Prerequisites` block stays verbatim, with the new
  `## Environment` block sitting above it.
- `qor/skills/meta/qor-repo-audit/SKILL.md` — same shape.
- `qor/skills/sdlc/qor-implement/SKILL.md` — same shape.
- `qor/skills/sdlc/qor-plan/SKILL.md` — same shape.
- `qor/references/doctrine-shadow-genome-countermeasures.md` — append
  an `SG-SilentSkipMisconfig-A` entry citing GH #79, the sibling consumer workspace
  evidence, and the Phase 90 C+D countermeasure.
- `tests/test_skill_environment_block.py` — NEW. Behavior tests that
  verify each Python-invoking skill carries both the Environment block
  and the preflight one-liner, and that the preflight is WARN-only
  (does not call `exit 1` or `|| ABORT`).
- `docs/plan-qor-phase90-skill-preflight-and-environment.md` — NEW.
  This plan file.

### Unit Tests

- `tests/test_skill_environment_block.py`

  Each test scans the actual `qor/skills/` tree (not fixtures) since
  the lint is a coverage check across the production skill set. Per
  `qor/references/doctrine-test-functionality.md`, each assertion
  verifies an operative property of the block / preflight, not mere
  presence of a header string.

  - `test_each_python_invoking_skill_has_environment_section` —
    enumerate SKILL.md files under `qor/skills/` that grep-match
    `python -m qor\.(reliability|scripts)`; assert each contains a
    `## Environment` section. Failing this test catches a future
    skill that adds a Python invocation without the contract.
  - `test_environment_block_cites_install_contract` — for each
    affected skill, isolate the `## Environment` section; assert it
    contains the literal substring `pip show qor-logic` (the
    canonical operator-actionable check) AND the literal substring
    `pipx install qor-logic` (the global-install fallback). Two
    substrings means a partial decay (one fix removed) still fails.
  - `test_environment_block_cites_phase_75_skip_fallback` — for each
    affected skill, assert the section contains the substring
    `Phase 75` and `gate_skipped_prerequisite_absent`. This guards
    against the prose decaying into an Option-A-style absolute
    contract that breaks non-Python hosts.
  - `test_each_python_invoking_skill_has_preflight_one_liner` —
    assert each affected skill contains the substring
    `python -c "import qor.reliability"` somewhere AFTER the
    `## Execution Protocol` heading.
  - `test_preflight_is_warn_only_not_abort` — strip-and-fail-style
    boundary: for each affected skill, isolate the preflight block
    (the line containing `python -c "import qor.reliability"` plus
    the next 5 lines); assert the block does NOT contain
    `exit 1` and does NOT contain `|| ABORT`. The preflight must
    WARN-only per Phase 75 compatibility (design notes above).
  - `test_no_new_skills_invoke_python_qor_without_environment_block` —
    structural sweep: walk every `qor/skills/**/SKILL.md`; for each
    that grep-matches `python -m qor\.(reliability|scripts)`, assert
    it has the `## Environment` section. Identical assertion shape
    to the first test but framed as a forward-only guard against
    future additions.

### Changes

For each of the 7 affected SKILL.md files, insert the following
`## Environment` block immediately after the `## Purpose` section and
before the next section (typically `## Step Prerequisites` for
substantiate, `## Execution Protocol` for the others):

```markdown
## Environment (Phase 90 wiring; GH #79)

This skill invokes `python -m qor.reliability.*` and `python -m qor.scripts.*`
to run integrity gates. The Python interpreter on PATH must have `qor-logic`
importable; verify before invocation:

```bash
python -c "import qor.reliability"
```

If that command fails, activate the venv where `pip show qor-logic` resolves,
or run `pipx install qor-logic` for a global install. On hosts without
Python or where `qor-logic` is not installable (e.g., pure non-Python
archetypes), Phase 75 declarative-tolerance applies — the missing-prerequisite
gates record SKIP in the seal entry and emit `gate_skipped_prerequisite_absent`
events per `qor/references/doctrine-shadow-genome-countermeasures.md`
`SG-HalfSealedClaim-A`. The Phase 90 preflight at the top of `## Execution
Protocol` below surfaces the misconfiguration once at skill entry so the
SKIP cascade is operator-visible instead of silent.

Closes the visible-misconfiguration half of GH #79 (V2 follow-up to the
Phase 75 V1 SKIP path; full venv-reachability fix via the
`qor-logic <subcommand>` CLI dispatch remains a future phase per GH #79
Option A).
```

For each of the same 7 affected SKILL.md files, insert the following
preflight one-liner at the top of the `## Execution Protocol` section
(or immediately after the protocol's heading, before Step 0):

```bash
# Phase 90 preflight (GH #79): surface qor-logic module misconfiguration
# once at skill entry. WARN-only — Phase 75 SKIP fallback still applies.
if ! python -c "import qor.reliability" 2>/dev/null; then
  echo "WARN [qor-logic]: modules not importable from $(command -v python). Steps with module: prerequisites will record SKIP per Phase 75. Activate the venv where 'pip show qor-logic' resolves, or 'pipx install qor-logic', to restore the integrity gates." >&2
fi
```

`qor/references/doctrine-shadow-genome-countermeasures.md` — append:

```markdown
## SG-SilentSkipMisconfig-A — silent-SKIP cascade hides recoverable misconfiguration (Phase 90)

**Pattern**: Phase 75 (`SG-HalfSealedClaim-A`) gave skills declarative tolerance
when `qor-logic` modules are not importable: emit `gate_skipped_prerequisite_absent`,
log SKIP in the seal, continue. The countermeasure is correct for legitimately
non-Python hosts (pure-Rust / pure-Node archetypes). It misfires on Python hosts
where the operator simply has the wrong venv active — the SKIP cascade looks
identical to the legitimate non-Python case, so operators learn to treat SKIPs
as normal. Seal entries land with quietly-incomplete gate coverage; trust in the
"all gates ran" claim erodes one silent SKIP at a time.

**Originating recurrence**: sibling consumer-workspace session (per GH #79). qor-logic
0.55.1 installed in an external workspace's venv with
`their downstream hook package`. Skills installed globally to `~/.claude/skills/qor-*/SKILL.md`.
A Claude Code session in a different repo without that venv on PATH ran the
skills; `python -m qor.reliability.X` raised `ModuleNotFoundError` on every call.
The session inferred from repeated failures that the modules "were never intended
to exist" and added a project-memory rule to silently skip the reliability
checks — propagating the misconfiguration into subsequent sessions. Diagnosed
only by running `which qor-logic` and `pip show qor-logic` outside the skill
flow, which the skills did not direct operators to do.

**Countermeasure** (Phase 90 wiring; GH #79): two layered additions to each
skill that invokes `python -m qor.reliability.*` or `python -m qor.scripts.*`.
(C) A preflight one-liner at the top of `## Execution Protocol`:
`python -c "import qor.reliability" || echo "WARN: ..."` — WARN-only (not ABORT)
so Phase 75 SKIP behavior remains intact on non-Python hosts. (D) An `## Environment`
section above the protocol that documents the install contract (`pip show qor-logic`,
`pipx install qor-logic`) and cross-references the Phase 75 SKIP fallback. V1
ships only the visibility half; the full reachability fix (Option A in GH #79:
`qor-logic <subcommand>` CLI dispatch using the CLI's own `sys.executable`)
is reserved for a follow-on phase, analogous to the V1/V2 split used for
GH #88/#91 in this cluster.

**Cross-reference**: GH #79 (this issue); doctrinally adjacent to
`SG-HalfSealedClaim-A` (Phase 75, the V1 declarative-tolerance countermeasure
this layer builds on). Same root surface, different leverage point.
```

## CI Coverage Exemptions

None for this phase. Phase 90's `## CI Commands` block declares the full
Qor-logic CI surface (matching Phase 89's self-application convention) so
`ci_coverage_lint` reports zero WARNs.

## CI Commands

- `python -m pytest tests/test_skill_environment_block.py -q` — behavior tests for the Environment block + preflight enforcement across affected skills.
- `python -m pytest tests/ -v` — full regression suite (matches the ci.yml `test` job's `-v` form).
- `python qor/scripts/check_variant_drift.py` — ci.yml `test` job step.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml `test` job step.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — ci.yml `install-smoke` job step.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — ci.yml `gate-chain-completeness` job step.
- `python qor/scripts/pr_citation_lint.py` — pr-lint.yml `lint` job step.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase90-skill-preflight-and-environment.md` — plan-internal text-consistency.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase90-skill-preflight-and-environment.md --workflows-dir .github/workflows` — Phase 89 ci-coverage lint (self-applying to this plan).
