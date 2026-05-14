# Plan: Phase 65 - Substantiate template wording + kilo-code host filesystem path

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: GH #57 (substantiate template hardcodes `/qor-bootstrap for new feature` recommendation that misroutes operators away from `/qor-ideate` or `/qor-plan` on already-bootstrapped projects) and GH #53 (`kilo-code` host installs to `.kilo-code/` but the Kilo tool reads `.kilo/`; installed skills land in a directory Kilo never reads).

**terms_introduced**: none. Both fixes operate on existing surfaces.

**boundaries**:
- limitations:
  - V1 changes the `kilo-code` host's filesystem base from `.kilo-code` to `.kilo` while preserving the logical host identifier `kilo-code`. The dist variant directory `qor/dist/variants/kilo-code/` is unchanged; it is a build artifact namespace, not a filesystem destination.
  - V1 fixes the substantiate template's "Next Session" recommendation only at the canonical source. Generated dist variants are regenerated via `python -m qor.scripts.dist_compile`.
- non_goals:
  - Renaming the `kilo-code` host identifier to `kilo` (would be a breaking change; deferred to a possible future phase per GH #53 open question).
  - Updating historical archive references to `/qor-bootstrap` (per `docs/claude-open-issues-remediation-handoff.md` Stage 3.4: "Ignore historical archive hits unless a doc policy explicitly requires archive edits").
  - Migrating existing `.kilo-code/` installations on operator workstations (forward-only; operators re-run `qor-logic install --host kilo-code` post-update).
- exclusions:
  - No changes to other host targets (claude, codex, gemini).
  - No changes to substantiate skill Step 9 prose (the misrouting lives in `references/qor-substantiate-templates.md`, not the SKILL.md body).
  - No changes to `qor/references/doctrine-governance-enforcement.md:104` historical mention of `.kilo-code/skills/` (forensic prose; not a path consumer).

## Open Questions

None. Issue #53 explicitly recommends "keep `kilo-code` as the logical identifier but change only the filesystem path" as the safe option; this plan adopts it. Issue #57 explicitly recommends replacing `/qor-bootstrap for new feature` with `/qor-ideate ... or /qor-plan ...` wording.

## Phase 1: Substantiate template wording fix (GH #57)

### Affected Files

- `tests/test_substantiate_template_next_session_wording.py` - NEW. Two behavior-focused tests asserting the canonical template names `/qor-ideate` and `/qor-plan` in the Next Session line, and does NOT name `/qor-bootstrap` in that line.
- `qor/skills/governance/qor-substantiate/references/qor-substantiate-templates.md` - line 140: replace `_Next Session: Run /qor-bootstrap for new feature or /qor-status to review_` with `_Next Session: Run /qor-ideate for a new concept or /qor-plan for implementation planning; /qor-status to review prior work_`.
- `qor/dist/variants/{claude,codex,kilo-code,gemini}/skills/qor-substantiate/references/qor-substantiate-templates.md` - regenerated via `python -m qor.scripts.dist_compile`.

### Changes

Tests written first (TDD). The single-line wording fix in the canonical template propagates to dist variants via the existing recompile pipeline. The replacement preserves the `/qor-status to review` clause but reroutes the "new feature" branch from `/qor-bootstrap` (which initializes a NEW project; wrong target) to `/qor-ideate` (ideation phase for already-bootstrapped projects) and `/qor-plan` (implementation planning entry point).

### Unit Tests

- `tests/test_substantiate_template_next_session_wording.py::test_canonical_template_recommends_ideate_for_new_concept` - reads `qor/skills/governance/qor-substantiate/references/qor-substantiate-templates.md`, locates the line containing `Next Session`, asserts the line contains `/qor-ideate`. Fails if absent.
- `tests/test_substantiate_template_next_session_wording.py::test_canonical_template_does_not_misroute_to_bootstrap` - reads the same file, asserts no line containing `Next Session` also contains the substring `/qor-bootstrap for new feature`. Guards against regression where the historical phrasing creeps back.
- `tests/test_substantiate_template_next_session_wording.py::test_dist_variants_propagate_template_fix` - reads each of the four dist-variant copies of the template (claude, codex, kilo-code, gemini), asserts each contains `/qor-ideate` in its Next Session line. Locks Phase 30 dist-recompile discipline.

## Phase 2: kilo-code host filesystem path fix (GH #53)

### Affected Files

- `tests/test_kilo_host_base_path.py` - NEW. Behavior-focused tests asserting `_kilo_target` (and the public `resolve("kilo-code", ...)` API) produce `.kilo` as the filesystem base across repo and global scopes, while the host name stays `kilo-code`.
- `qor/hosts.py` - line 68: change `_scoped_base(".kilo-code", scope)` to `_scoped_base(".kilo", scope)` inside `_kilo_target()`. The `HostTarget` name argument stays `"kilo-code"`.
- `tests/test_hosts_scope.py` - line 36: update assertion to `target.base == tmp_path / ".kilo"`.
- `tests/test_phase21_harness.py` - lines 26-27: update assertions to `Path.home() / ".kilo" / "skills"` and `Path.home() / ".kilo" / "agents"`.

### Changes

`qor/hosts.py:68` swap is the entire production code change. The `_skills_agents_map(base)` helper produces `base/skills` and `base/agents`; under the new base this resolves to `.kilo/skills` and `.kilo/agents` which matches the Kilo tool's actual config directory layout.

The two existing test files assert the old behavior and would have to be updated regardless; updating them is part of the TDD flip-test pattern (existing tests turn red, get rewritten to the new contract, new tests in `test_kilo_host_base_path.py` lock the new contract independently).

The host identifier remains `kilo-code` everywhere: the public `resolve()` argument, the `HostTarget.name` field, the dist variant directory name, the doctrine prose mentions. Only the on-disk install destination changes.

### Unit Tests

- `tests/test_kilo_host_base_path.py::test_kilo_repo_scope_base_is_dot_kilo` - invokes `resolve("kilo-code", scope="repo")` with a controlled cwd via `monkeypatch.chdir`, asserts `target.base` equals `<cwd>/.kilo`.
- `tests/test_kilo_host_base_path.py::test_kilo_global_scope_base_is_dot_kilo` - invokes `resolve("kilo-code", scope="global")`, asserts `target.base` equals `Path.home() / ".kilo"`.
- `tests/test_kilo_host_base_path.py::test_kilo_host_name_is_unchanged` - invokes `resolve("kilo-code", scope="repo")`, asserts `target.name == "kilo-code"`. Locks the "keep host id; change only filesystem path" decision per Issue #53 + handoff doc.
- `tests/test_kilo_host_base_path.py::test_kilo_skills_agents_dirs_resolve_under_dot_kilo` - asserts `target.install_map["skills/"]` ends in `.kilo/skills` and `target.install_map["agents/"]` ends in `.kilo/agents` for both repo and global scopes.

## Phase 3: Documentation refresh

### Affected Files

- `docs/SYSTEM_STATE.md` - prepend a Phase 65 entry naming both bug closures (#57 + #53), the change_class, and the preserved-host-id decision.
- `docs/operations.md` - the existing troubleshooting table gains one row for the kilo-code install path migration (operators who installed under `.kilo-code/` need to re-run install post-update).
- `CHANGELOG.md` - new Unreleased entries describing both fixes; substantiate Step 7.6 stamps the section to `[0.46.2]` at seal time.
- `README.md` - badge currency: bump Tests count to reflect new test surface; Ledger badge bumped to 199 after Phase 65 seal entry lands (handled mechanically at substantiate time).

### Changes

These are mechanical doc-currency updates the substantiate gates (procedural-fidelity, Phase 31 currency check, Phase 49 badge currency) enforce. Hotfix is exempt from the Phase 33 release-doc-requires-README+CHANGELOG rule, but updating both is good hygiene and the badge currency check still runs for the ledger count.

### Unit Tests

No new tests for Phase 3. The existing badge-currency, procedural-fidelity, and SYSTEM_STATE-coverage tests are the structural enforcement.

## CI Commands

- `python -m pytest tests/test_substantiate_template_next_session_wording.py tests/test_kilo_host_base_path.py tests/test_hosts_scope.py tests/test_phase21_harness.py -v` - validates new Phase 65 tests + the two updated existing tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants so Phase 1's variant-propagation test can find the fix in each variant.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase65-substantiate-template-and-kilo-host-paths.md` - lint the plan file itself.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite minus the flaky tag-coverage test that requires not-yet-sealed git history.
