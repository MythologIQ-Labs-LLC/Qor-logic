# Plan: layout configurability and typed gate skips (GH #406)

**change_class**: feature

**doc_tier**: standard

**terms**: []

No new domain vocabulary. `Layout key` and `typed skip` are descriptive uses of
existing configuration and shadow-event concepts, not new registered terms.

**boundaries**:
- limitations: [does not relocate this repository's own glossary or skills corpus; the defaults remain the `qor/` topology so a workspace declaring nothing behaves exactly as today. Does not extend the `layout` section beyond the three keys the layout-bound gates actually resolve.]
- non_goals: [does not make `data_api_acl_lint` or `feature_index_verify.surface_lint` configurable -- their skips are legitimately schema-optional or input-absent, not layout-bound, as GH #406 itself separates out; does not touch `badge_layout`'s existing six badge keys or their precedence]
- exclusions: [no change to `qorlogic_config.load_section`'s tolerant-reader contract -- a malformed operator config must still degrade to defaults rather than raising]

## Problem

Several `/qor-substantiate` gates resolve truth from paths that exist only in
the Qor-logic repository, so in any consumer workspace the only available
outcome is a Phase 75 disclosed skip. The reporter's first seal recorded six
skips and five were this rather than a property of their repository. Six
disclosed skips in one seal stops reading as signal.

### The layout-bound constants, verified on `main`

- `qor/scripts/doc_integrity.py:26,30` -- `("qor/references/glossary.md", "glossary")`
  inside the module-level `_TIER_REQUIREMENTS` table, for the `standard` and
  `system` tiers.
- `qor/scripts/doc_integrity.py:176,212` -- `Path(repo_root) / "qor" / "references" / "glossary.md"`
  built literally in `render_drift_section` and `run_all_checks_from_plan`.
- `qor/scripts/doc_integrity_strict.py:77,199` -- the same literal as the
  non-absolute fallback for `glossary_rel`.
- `qor/scripts/skill_size_budget_lint.py:64` -- `--skills-root` defaults to
  `Path("qor/skills")` with no config channel.

### Why this is fixable rather than inherent

The mechanism exists and these gates do not use it. `qor/scripts/qorlogic_config.py`
is the repository's one tolerant reader for `.qorlogic/config.json`, and
`qor/scripts/badge_layout.py` already resolves a `layout` section through it
with flag > config > default precedence per key (`badge_layout.py:62-73`).
`attribution_policy.py:48` reads the same file for a different section. The
pattern is established; three gates simply resolve their paths as constants.

### What is not a defect

GH #406 separates these correctly and this plan keeps that separation.
`data_api_acl_lint` globs SQL migration paths and correctly no-ops for a repo
with no SQL -- its skip is about absent input, not about layout.
`feature_index_verify.surface_lint` is documented schema-optional. Neither is in
scope.

## Fix

### Half 1 -- resolve the layout-bound paths through config

1. `qor/scripts/badge_layout.py`: add `glossary_path: Path = Path("qor/references/glossary.md")`
   to `BadgeLayout`, resolved by the existing per-key precedence. The dataclass
   is already the `layout`-section reader and already carries `skills_root`;
   adding the third key keeps one resolver rather than starting a second.
2. `qor/scripts/layout_paths.py` (**new module**) + `qor/scripts/doc_integrity.py`:
   `resolve_glossary_path(repo_root)` and `tier_requirements(repo_root)` live in
   the new module; `doc_integrity` re-exports them and calls them where it
   previously joined the literal, in `check_topology`, `render_drift_section`
   and `run_all_checks_from_plan`.

   **Revised during implementation.** Defining the resolvers inside
   `doc_integrity` pushed that file to 283 lines against its 250-line Section 4
   Razor cap, which `tests/test_doc_integrity_razor_compliance.py` enforces.
   They are not in `badge_layout` either: that module's subject is badge
   counting, and a governance-document locator does not belong under it. A
   separate module keeps one answer to "where does this workspace keep X"
   without overloading either existing home.
3. `qor/scripts/doc_integrity_strict.py`: the non-absolute fallback resolves
   through the layout instead of the literal.
4. `qor/scripts/skill_size_budget_lint.py`: `--skills-root` default becomes
   `None`, resolving flag > config > `qor/skills`, matching how `badge_layout`
   already avoids an always-populated flag making the config channel inert
   (the Phase 210 / GH #299 lesson, cited in `badge_layout.py:47`).

   **And the caller must stop supplying it** (tribunal ground V-1, entry #686).
   `qor/skills/governance/qor-substantiate/SKILL.md:244` and
   `references/seal-gate-ladder.md:76` write the invocation as
   `skill_size_budget_lint --skills-root qor/skills`, hardcoded in the prompt
   and compiled into all six variants, so at seal time the flag would always
   arrive populated with the Qor-logic path regardless of any config -- the
   same inert-channel trap one layer up from where the plan cites it. Drop the
   flag from the source skill and its reference, recompile the variants, and
   let the resolver decide. `doc_integrity` and `doc_integrity_strict` need no
   equivalent change: the skill invokes them as Python with no path argument
   (`SKILL.md:263`), so fixes 2 and 3 already reach their callers.

### Retired seal-ladder token

7. `tests/test_seal_ladder_tokens_survived.py` guards every ladder command
   present at `BASELINE_REV` against silent loss, so dropping the hardcoded
   `--skills-root qor/skills` (fix 4) trips it by design. The retirement is
   declared in an `INTENTIONALLY_RETIRED` mapping carrying the exact token and
   its reason, rather than by advancing `BASELINE_REV` -- advancing the baseline
   would silently absolve every other drop in the same range.

   The allowlist gets its own two guards so it cannot become a mute button:
   `test_retired_tokens_carry_a_reason` requires a substantive reason citing an
   issue number, and `test_retired_tokens_are_actually_absent` fails if an
   allowlisted token is still present, which would mean the list is stale. The
   existing `test_the_survival_check_can_fail` counterfactual is untouched and
   still bites.

### Half 2 -- the typed-skip contract

Today a skip is an ad-hoc free-text `reason`, so the shadow genome accumulates
events nobody can group. Two changes:

5. The `gate_skipped_prerequisite_absent` event gains a structured
   `details.layout_key` naming the declaration the gate needed
   (`glossary_path`, `skills_root`), alongside the existing `gate`. Grouping
   becomes possible without parsing prose.
6. **A layout-bound gate whose path does not resolve fails unless the operator
   declared it.** Declared absent (`"glossary_path": null` in the `layout`
   section) records a typed skip citing that key. No declaration at all is a
   hard failure telling the operator which key to declare.

   The asymmetry is the point. A silent pass on an unresolvable path is the
   vacuous-gate shape this repository has now closed four times; a hard failure
   with a named key is actionable. This repository declares nothing and is
   unaffected, because its paths resolve.

## Tests (written first)

- `tests/test_layout_configurability.py::test_glossary_path_defaults_to_the_qor_topology`
  -- `badge_layout` with no config resolves `qor/references/glossary.md`, so a
  workspace declaring nothing behaves as today.
- `::test_glossary_path_resolves_from_the_layout_config`
  -- a config declaring `layout.glossary_path` moves the resolved path. Red
  before fix 1.
- `::test_doc_integrity_reads_the_configured_glossary`
  -- `run_all_checks_from_plan` against a workspace whose glossary sits at a
  non-`qor/` path, with a term registered there, must PASS; today it raises
  because it reads the literal. Red before fix 2. This is the reporter's exact
  case (`docs/00-glossary.md`).
- `::test_doc_integrity_strict_reads_the_configured_glossary`
  -- same for the strict tier. Red before fix 3.
- `::test_skill_size_budget_lint_resolves_skills_root_from_config`
  -- a config declaring `layout.skills_root` makes the lint walk that tree.
  Red before fix 4.
- `::test_skills_flag_still_beats_config`
  -- an explicit `--skills-root` overrides the config, pinning the precedence
  order so the flag does not become inert.
- `::test_seal_ladder_does_not_hardcode_a_skills_root`
  -- the `/qor-substantiate` skill text and its `seal-gate-ladder.md` reference
  must invoke `skill_size_budget_lint` without a `--skills-root` argument, so
  the config channel stays reachable from the caller that matters. Red before
  the fix-4 extension. This is a prompt-contract assertion with no unit behind
  it, which is why it is scoped narrowly to the invocation shape rather than
  standing in for the resolver tests above.
- `tests/test_seal_ladder_tokens_survived.py::test_retired_tokens_carry_a_reason`
  and `::test_retired_tokens_are_actually_absent` -- the allowlist's own guards
  (fix 7). Both pass once the allowlist is populated correctly and fail on an
  unexplained or stale entry.
- `::test_typed_skip_names_the_layout_key`
  -- the emitted event carries `details.layout_key`, not only free text. Red
  before fix 5.
- `::test_unresolvable_layout_path_without_a_declaration_fails`
  -- a gate whose path does not resolve and whose key is undeclared exits
  non-zero and names the key. Red before fix 6.
- `::test_unresolvable_layout_path_declared_absent_records_a_typed_skip`
  -- the same gate with `"glossary_path": null` declared exits 0 and emits the
  typed skip. Red before fix 6; the pair together is what makes the asymmetry
  testable rather than asserted.

Every test invokes the unit and asserts on its return value, raised error, or
emitted event; none asserts file presence or substring membership.

## Validation

- `python -m pytest tests/test_layout_configurability.py -q` -- run twice for determinism
- `python -m pytest -q` (full suite)
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint`
- `qor-logic-plus governance-health --profile skill-entry` -- this repository must stay clean with no `layout` section declared

## CI Commands

- `python -m pytest -q`
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
