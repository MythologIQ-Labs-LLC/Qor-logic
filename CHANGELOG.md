# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Merkle seal hashes for each release are recorded in `docs/META_LEDGER.md`; this
file is the user-facing narrative.

## [Unreleased]

## [0.113.0] - 2026-07-04

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 165 (feature; autonomous QA nightly)**: governance health now verifies itself with zero operator engagement. New `qor.scripts.status_json` runs the read-only check ladder (governance-health, ledger chain, seal-artifact currency, gate-chain completeness, provenance, governance index) in-process and emits a deterministic machine-readable JSON verdict as its final output line (closes the `status --json` ask, GH #240), with a `--self-test` mode that validates the aggregation logic before any consumer trusts a live verdict. New `.github/workflows/nightly-health.yml` runs the ladder plus the packaging smoke nightly (and on demand): drift automatically opens or updates a single "Nightly governance health" issue with the JSON payload, and recovery automatically closes it (GH #250 part a; pattern ported from the Accountable drift-detection reference).

## [0.112.0] - 2026-07-04

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 164 (feature; generate-not-assert)**: seal presentation artifacts are now generated, never hand-edited. New `qor.scripts.seal_artifacts` deterministically regenerates the five README literal-count badges (Tests, Ledger, Skills, Agents, Doctrines) and the SYSTEM_STATE header fields (Snapshot date, Phase number) from current truth (`--write`), and verifies currency fail-closed (`--check`, wired into `/qor-substantiate` Steps 6/6.5 and a new CI step). The 13-test live-equality class that broke on nearly every seal (badge counts, header freshness, prose-wiring) is retired in favor of behavioral generator tests against synthetic fixtures -- currency is now enforced where repo state is stable, at seal time and in CI. Origin: the SDLC perspective-reset research brief (ledger entry #378), recommendation 2.

## [0.111.1] - 2026-06-10

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 163 (hotfix; release-pipeline integrity)**: gate the PyPI publish on the CI suite passing for the tagged commit. `release.yml` previously had `build -> publish` with **no test step** -- a publish was coupled to tests only by operator discipline (verify PR CI before approving the `pypi` environment), which could ship untested code on an early approval or a broken `main`. New `qor.scripts.release_ci_gate` (pure, fail-closed `evaluate` returning ok only when a `CI` run for the exact SHA concluded `success`) is wired into BOTH the build (early) and publish (enforcement) jobs before their work: the workflow runs the authenticated `gh api .../ci.yml/runs?head_sha=<SHA>` and pipes it to the gate, which exits 1 (refusing the release) unless CI was green for that commit. Mirrors the existing tag-reachability double-gate; the decision logic is unit-tested in-process.

## [0.111.0] - 2026-06-10

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 162 (feature; GH #231 Option 1)**: a ledger base-currency gate that linearizes the META_LEDGER hash chain at the trunk. The ledger is a linear hash chain carried in a file that lives in a git branch DAG, so a branch that seals against a stale `origin/main` tip forks the chain (and git can auto-merge the appends silently). New `qor.reliability.ledger_base_currency`: `check_base_currency` flags a branch whose first new-on-branch entry's `previous_hash` does not equal `origin/main`'s tip `chain_hash` (new entries identified by chain-hash set membership, robust to entry-number reuse), and `reanchor` is a pure fold that deterministically rebuilds a provisional sub-chain onto the live base tip (`previous_hash`/`chain_hash`/`entry_id`) without editing the ledger. Wired as a **WARN-only** CI step (`--enforce` reserved for a V2 flip); the existing post-hoc `check_previous_hash_uniqueness` detector is retained as defense-in-depth. New `doctrine-ledger-concurrency.md` documents the provisional-until-merge contract.

## [0.110.3] - 2026-06-10

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 161 (hotfix; CI flake)**: made `tests/test_merge_velocity_check.py` deterministic. `_make_merge_commit` derived its feature-branch and filename from `abs(hash(subject)) % 100000`, where Python's `hash(str)` is `PYTHONHASHSEED`-randomized and the mod-100000 truncation collides distinct subjects -- so on some CI matrix cells the second `git checkout -b feat-<n>` hit an existing branch and exited 128 (an intermittent failure that flaked the ubuntu-3.13 cell during the Phase 158 PR). Replaced both sites with a pure `_feat_suffix(subject) = hashlib.sha1(subject).hexdigest()[:8]` -- deterministic across processes and collision-resistant for distinct subjects. Verified green under `PYTHONHASHSEED=0` and `=12345`. Test-only; no runtime change.

## [0.110.2] - 2026-06-10

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 160 (hotfix; documentation currency)**: brought the docs current with the Phase 158/159 work and added an enforcement test. The README doctrine inventory now lists `provenance-binding` (it had drifted to 34 of 35 doctrines; `badge_currency` only checks the badge count, not the prose table), and `docs/operations.md` now documents the `provenance-attest` CI job + per-session provenance sidecars and the seal-entry plan-name fallback. New `tests/test_readme_doctrine_inventory.py` pins the README doctrine table to the on-disk `doctrine-*.md` corpus bidirectionally, so the table cannot silently drift again.

## [0.110.1] - 2026-06-10

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 159 (hotfix; closes GH #223)**: `seal_entry_check` (substantiate Step 7.7, `|| ABORT`) no longer hard-fails on a plan filename that does not match the qor-internal `plan-qor-phase<N>-<slug>.md` pattern. Downstream workspaces that name plans `plan-<slug>.md` (e.g. FailSafe) were blocked from sealing a cryptographically valid ledger entry. The filename only ever supplied the phase number for the consistency check, so a non-conforming `--plan` now falls back to the ledger-derived phase (the existing `--auto` path), emitting a WARN instead of `rc=1`. The fallback still runs the identical GOV-01 `content_hash`<->cited-plan binding, so a real inconsistency still fails -- it is not a bypass.

## [0.110.0] - 2026-06-10

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 158 (feature, audit Sprint A; closes GH #210)**: non-forgeable gate-artifact provenance (GAP-GOV-05), replacing the self-asserted `QOR_SKILL_ACTIVE==phase` binding with a layered scheme. **Layer A** is a stdlib-only per-session HMAC provenance sidecar (`qor/scripts/gate_provenance.py`) written beside each gate artifact by `gate_chain.write_gate_artifact` (fail-closed): it carries a keyless `payload_sha256` and an `hmac_tag` keyed by a per-session secret under the gitignored `.qor/session/keys/`, giving tamper-evidence and cross-session replay resistance. **Layer B** is a CI attestation: a keyless `verify-committed --phase-min 158` recomputation gate wired as a required CI job (a forged committed artifact fails the merge boundary, and it runs on forks), plus a CI-secret-keyed `attest-latest` stamp only trusted CI can produce. The threat model is stated honestly: non-forgeability against the operator is impossible by construction (the operator is both author and bound party), so Layer A's ceiling is an in-repo filesystem actor and Layer B is verifiable only in CI. New `doctrine-provenance-binding.md`; this seal closes the Sprint A umbrella (only GAP-GOV-05 remained).

## [0.109.5] - 2026-06-10

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Security
- **Phase 157 (hotfix, audit Sprint A)**: gave `hash_guard.hash_file` an opt-in `normalize_newlines=True` mode so a digest recorded over a text seal artifact is invariant to git's CRLF conversion (the GAP-GOV-03 fragility class Phase 156 fixed for `ledger_hash.content_hash`, now closed for the second seal-relevant file hasher cited in the substantiate Step 6.8 preparation). The default stays byte-exact, so binary and general-purpose hashing is unchanged; `intent_lock`'s intra-checkout gate-artifact hasher is intentionally left byte-exact.

## [0.109.4] - 2026-06-10

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Security
- **Phase 156 (hotfix, audit Sprint A)**: re-verify the committed seal's `content_hash`<->plan binding (GAP-GOV-03). New `seal_entry_check --auto` (derives the phase from the latest entry) + a CI step run it on the committed `META_LEDGER.md`, so the binding is re-checked on the committed bytes (CI already re-verified the chain). This uncovered and fixed a real fragility: `ledger_hash.content_hash` was sensitive to git's CRLF conversion, so the binding could disagree between the seal-time (LF) working copy and the committed (CRLF) file; `content_hash` now normalizes line endings to LF before hashing (a no-op for LF files, so existing recorded hashes are unchanged).

## [0.109.3] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Security
- **Phase 155 (hotfix, audit Sprint A)**: `ledger_hash.verify()` no longer silently skips a modern ledger entry that lacks canonical hash markup. A skipped (no Content/Previous/Chain markup) entry numbered at/after the markup-required cutoff (123) is now a FAIL, while the 32 historical pre-convention entries (<= 122) stay grandfathered (GAP-GOV-09). The real chain still verifies clean; the floor only catches a future modern entry written without its hashes.

## [0.109.2] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 154 (hotfix, GH #219)**: `qor-logic seed --target` now carries clarifying help -- it is a destination workspace DIRECTORY (default: current directory), not an artifact name, so `seed --target FOO` no longer reads as "seed the FOO artifact" (it scaffolds a fresh workspace under `./FOO/`). The sibling `install`/`uninstall`/`init` `--target` arguments gained help too. (The issue's secondary exit-1-with-success-output was already resolved in current code; the optional warn-on-nested-workspace is deferred.)

## [0.109.1] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Changed
- **Phase 153 (hotfix, audit Sprint A)**: decomposed the ~118-line `ledger_hash.verify()` (the audit's largest-function finding) into a thin orchestrator plus two named pure helpers -- `_resolve_recorded` (hash-markup resolution incl. the Session-Seal fallback) and `_classify_entry` (placeholder / taint / OK / disclosed-tolerance / fail classification). Behavior-preserving: output bytes and exit code are unchanged, verified by the 59 existing chain-verifier assertions across 5 test files plus 4 new direct helper tests (GAP-CQ-02).

## [0.109.0] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 152 (feature, GH #213)**: the Shadow Genome graph now emits the trust / federation / maturity data surfaces the downstream FailSafe dashboard renders. New emitter API on `qor.scripts.shadow_genome_graph`: `record_trust_transition(...)` (CBT/KBT/IBT transitions as `trust` nodes linked to their evidence + governance), `set_federation_peer(...)` (adapter-level peer status, latest-wins, with a 7-value `PeerState`), and `annotate_failure_maturity(...)` + `derive_maturity_stage(...)` (Observed -> Classified -> Constraint extracted -> Detectable -> Enforced -> Verified). `to_dict` gains `trust_transitions` + `federation_peers` and a `maturity` field on failure nodes; `nodes`/`edges` are unchanged (back-compat). All surfaces are strictly append-only. Per the operator-chosen emitter-API + derive model: qor-logic owns the schema + recorders and derives maturity, while trust/federation are fed by the consumer's adapter. The doctrine's original "declined -- no consumer" scope decision (#139) is reversed now that FailSafe (#196) is the consumer.

## [0.108.3] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Removed
- **Phase 151 (hotfix, audit Sprint A)**: deleted the dead placeholder session-seal hasher (`qor/scripts/calculate-session-seal.py`) -- a non-importable script with a literal `previous_hash = "PREVIOUS_LEDGER_HASH"` placeholder that misrepresented how seals are computed -- and re-pointed the `/qor-substantiate` skill at the real seal helpers (`ledger_hash.content_hash`/`chain_hash`, bound to the plan by the Phase-150 `seal_entry_check`). A corpus guard test now blocks re-introduction of any placeholder hasher (GAP-GOV-02).

## [0.108.2] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Security
- **Phase 150 (hotfix, audit Sprint A)**: bound the ledger seal's `content_hash` to the artifacts it claims to seal. `seal_entry_check` now recomputes the SHA256 of the plan file the latest entry cites and fails the seal on mismatch (or a missing plan), so the recorded hash can no longer be an unverified free value (closes GAP-GOV-01 from the production-gap audit). Forward-only: only the just-sealed entry is recomputed; existing entries are grandfathered. Also: the `QOR_GATE_PROVENANCE_OPTIONAL` test-only bypass is now honored only under pytest, so a non-test process cannot disable the gate-artifact provenance binding by exporting the variable (GAP-GOV-04); and gate-chain completeness now validates each gate artifact's content + schema rather than mere file existence (GAP-GOV-14).

## [0.108.1] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 149 (hotfix, docs)**: corrected the PyPI-facing README host-layout table, which pointed `kilo-code` installs at a non-existent `./.kilo-code/` directory; the `kilo-code` host resolves to `./.kilo/` (per `qor/hosts.py`). Also surfaced the Phase-148 `compliance enforce` verdict/status semantics in the CLI Reference with a link to `qor/references/downstream-enforcement-sdk.md`, and added a `docs/FEATURE_INDEX.md` row to the documentation index. Found by a `/qor-document` thorough README review.

## [0.108.0] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 148 (feature, audit Sprint B)**: the downstream compliance-enforcement SDK now produces explicit verdict status and never passes vacuously. `compliance enforce --engagement ci|seal` runs real controls (`prompt-injection` for ci; `governance-index` + `gate-chain-completeness` for seal) instead of returning an empty PASS; controls that are enforced elsewhere and have no CLI runner (`ai-provenance`, `dependency-review`) are surfaced explicitly as `disclosed` with a reason. Each result carries a `status` (`pass`/`fail`/`skip`/`disclosed`) and the verdict carries `enforced`/`failed`/`no_op`. Runners may declare `requires` paths so a consumer lacking a governance artifact is reported as `skip` rather than hard-failed.
- **Phase 148**: shipped a `py.typed` marker so the typed SDK (`qor.sdk` / `qor.compliance.enforce`) is consumable by downstream type checkers, and guarded the SDK's `compliance/*.json` package data + the `py.typed` marker against silent removal in the packaging test.

### Fixed
- **Phase 148**: two doctrine-content tests (`test_doctrine_dependency_admission`, `test_codeowners_doctrine`) now resolve their paths from `__file__` so they pass from any working directory, not only the repo root.

## [0.107.3] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Security
- **Phase 147 (hotfix, audit Sprint C)**: hardened operator-supplied `session_id` handling. A single canonical path-safety validator (`qor.scripts.session.validate_session_id`) now rejects any `session_id` containing `/`, `\`, or `.` before it is used as a path segment, applied at the `orchestration_override` and `cycle_count_escalator` marker-path sites (closes the inconsistent-validation finding GAP-SEC-04/05/07 from the production-gap audit).

### Fixed
- **Phase 147**: corrected `docs/FEATURE_INDEX.md` citations -- `compliance enforce` now cites its real handler (`qor/cli_handlers/compliance.py`) and the module-dispatch row cites its real behavioral test (`tests/test_cli_module_dispatch.py`) -- and fixed the README `verify-ledger` usage to match its actual `--ledger`/`--post-anchor` flags.

## [0.107.2] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 146 (hotfix)**: backfilled behavioral test coverage for the `qor-logic list` and `qor-logic info` CLI commands (`tests/test_cli_feature_index_backfill.py`), and corrected the `qor-logic uninstall` FEATURE_INDEX row to cite its existing verifying test. `docs/FEATURE_INDEX.md` now reports all 17 features `verified` (was 14 `verified` / 3 `unverified`). Companion research brief (stash triage + backfill scope) at `docs/research-brief-stash-triage-feature-backfill-2026-06-09.md`.

## [0.107.1] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 145 (hotfix, GH #201 follow-on)**: wired the ledger-seal UTF-8/ASCII validity gate into the actual seal path. The Phase 140 helpers (`assert_sealable_text` / `normalize_punctuation`) were only called from the fragment write path (`ledger_fragment`), which `/qor-substantiate` does not traverse (it edits `META_LEDGER.md` directly), so a SESSION SEAL entry could still be written with non-ASCII / invalid-UTF-8 bytes. `qor.reliability.seal_entry_check` (already run at `/qor-substantiate` Step 7.7) now fails closed: it returns an error rather than raising on a non-UTF-8 ledger, and validates the latest entry body via `assert_sealable_text`. No skill-prompt or dist-variant change.

## [0.107.0] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 144**: authored the previously-missing `docs/FEATURE_INDEX.md` -- a feature index over the user-touchable `qor-logic` CLI command surface (17 features, each row cited to a source `file:line` and a verifying test, honestly statused: 14 `verified`, 3 `unverified`). Closes the long-standing `FEATURE_INDEX` MISSING governance-health finding and activates the seal-time `feature_index_verify` regression guard.

### Fixed
- **Phase 144**: removed an ~87-release-stale "Highlights of the v0.19+ documentation-integrity arc" block from the README `## Latest release` section, so it matches its own stated intent of avoiding version-specific content (the CHANGELOG remains the single source of truth).

## [0.106.1] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 143 (hotfix)**: stopped a test from polluting the tracked process shadow genome. `tests/test_override_friction_escalator.py::test_emit_gate_override_succeeds_with_justification` patched the override-friction check log but not the event-append target, so `emit_gate_override` wrote a real `sess-1` event into `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` on every run (78 accumulated). The emit tests now also patch `shadow_process.UPSTREAM_LOG_PATH`; the 78 synthetic lines were pruned; and a new `tests/test_shadow_upstream_no_test_pollution.py` guards that the tracked file carries no `sess-1` events and that `emit_gate_override` honors a redirected upstream path.

## [0.106.0] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 142 (downstream enforcement SDK)**: the compliance control matrix becomes an **engagement manifest** -- each control gains an `engagement` field (`pre-commit`/`pre-push`/`pre-tool-write`/`ci`/`seal`) and, where standalone-runnable, a `runner` (`module`/`entry`/`args`). A mini-SDK `qor.compliance.enforce` (re-exported at `qor.sdk`, surfaced as `qor-logic compliance enforce --engagement <point>`) loads control definitions from the installed package and runs the wired runnable controls against the consumer's tree, returning a structured `Verdict` (ABORT failures fail it, WARN are advisory). Conveyance conformance now also verifies every runnable-point control has an importable, callable runner. **Packaging fix**: `compliance/*.json` added to package-data so the matrix actually ships to pip consumers. New `downstream-enforcement-sdk.md` + 2 glossary terms (Engagement Point, Enforcement Runner). Qor-logic owns the manifest + runner + verdict; the consumer owns the trigger -- hooks remain addressed exclusively downstream (no hook installer shipped).

## [0.105.0] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 141 (compliance-conveyance integrity)**: a declarative **Compliance Control Matrix** (`qor/compliance/control_matrix.json` + schema) records every compliance control Qor-logic conveys downstream (framework, enforcing module, posture, conveyance target), seeded with the deterministic shipping controls. A **conveyance conformance** pytest gate (`qor.scripts.compliance_conformance`) fails CI when any control is missing, posture-downgraded, or absent from a conveyed variant (claude/codex/kilo-code `skills/*/SKILL.md`, gemini `commands/*.toml`). A **compliance ratchet** (`qor.scripts.compliance_ratchet`) compares the matrix against the prior release tag and fails on a dropped or `ABORT -> WARN` control unless an explicit `waivers` entry (id + justification + issue) covers it, making conveyed compliance monotonic. New doctrine `doctrine-compliance-conveyance.md` + four glossary terms. Hooks intentionally out of scope.

## [0.104.0] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 140 (GH #201)**: the ledger-seal write boundary now asserts UTF-8/ASCII validity before a content hash is computed. `qor.scripts.ledger_hash` gains `assert_sealable_text()` (rejects non-ASCII, naming the offending codepoint + index) and `normalize_punctuation()` (opt-in smart-punctuation -> ASCII map); both `ledger_fragment.write_fragment` and `ledger_fragment.canonicalize_fragments` call the gate, so codepoint-truncated / cp1252 / invalid-UTF-8 punctuation can no longer be sealed into a hash and render the ledger unreadable. On rejection the ledger is left untouched and fragments stay pending.
- **Phase 140 (GH #199)**: the skill-entry `governance-health` ledger check now tolerates a disclosed pre-anchor residual exactly as the release gate does. When strict chain verification fails, it falls back to `ledger_hash.verify_post_anchor`; a failure at or below the auto-detected boundary is tolerated (not `DAMAGED`), while a genuine post-anchor failure still classifies `DAMAGED`. This unblocks `/qor-*` skills on ledgers carrying single-lineage manual-era residuals that the release gate already accepts.
- **Phase 140 (GH #200)**: the `governance-health` placeholder check matches template-form markers only (`TODO:`/`FIXME:` labels, `<!-- TODO` comments, bracketed fill-ins) instead of the bare substring `TODO`. Prose mentions of the word TODO/FIXME (e.g. "TODO stubs", "cosmetic TODOs") no longer false-positive a governance artifact as `INCOMPLETE`.

## [0.103.1] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 139 (hotfix)**: bot-authored PRs (login ending in `[bot]`, e.g. `dependabot[bot]`) are now exempt from the PR Citation Lint. Machine-generated dependency/automation bumps that touch non-doc files (e.g. `.github/workflows/*.yml` action-version bumps) have no plan/ledger/Merkle-seal to cite, so the doctrine §6 citation requirement was failing them indefinitely (e.g. PR #195). `qor/scripts/pr_citation_lint.py` gains `is_exempt_actor()` plus an `--actor` argument that short-circuits to exit 0 for bot authors; `.github/workflows/pr-lint.yml` passes the PR author via an env var. Human-authored PRs remain gated.

## [0.103.0] - 2026-06-09

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 138 (GH #196 V1)**: a schema-optional, WARN-only surface-tag presence lint in the `/qor-substantiate` FEATURE_INDEX verification pass. `qor-logic scripts feature_index_verify --surface-lint` flags every non-`n/a` FEATURE_INDEX row missing a `Surface` value with a severity-2 `degradation` event when the repo's index header declares a `Surface` column; a repo whose header lacks the column disclosed-skips (`gate_skipped_prerequisite_absent`) and a repo without a `FEATURE_INDEX.md` silent-skips, so no existing adopter is broken by adoption. Adds an optional `surface` property to `feature_index.schema.json` (`additionalProperties:false` retained), a glossary entry, the worked-example 7th column, and step 7 of the seal pass. The motivating per-surface mapping data is FailSafe's (FailSafe#206); the enforcing gate lives in qor-logic. The lint always exits 0; V2 fail-closed promotion is deferred until consumer surface coverage is complete.

## [0.102.2] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 137 (hotfix)**: resynced `docs/SYSTEM_STATE.md`, which had drifted to a Phase-75 / v0.51.0 / 2026-05-14 snapshot (stale header, pre-migration File Tree, Ledger-chain-head at Entry #169). Rewrote the header, Authoritative-source, File Tree, Ledger-chain-head, Shipped-tooling, and Advisory-gate-overrides sections to current truth (Phase 136/137 era, v0.102.1, 329 ledger entries, live variants) and added a condensed Phases-108-136 bridge; the accurate historical per-phase sections (Phase 36-109) are left intact. Added `tests/test_system_state_freshness.py` -- a drift guard asserting the SYSTEM_STATE header phase stays within 1 of the latest ledger SESSION SEAL phase (the existing `test_system_state_phase_coverage` only matched "Phase N feature substantiated" phrasing, which is why the 61-phase drift went uncaught).

## [0.102.1] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 136 (hotfix)**: corrected a pre-existing structural defect in `qor-substantiate/SKILL.md` where the entire `### Step Z` gate-write body (including `session.rotate()`) was pasted inside the Step 4.5 "Skill File Integrity Check" required-sections list. Step 4.5 is now a clean section-name checklist; the gate-artifact write is a standalone `### Step Z` placed before Step 7.8 (so gate-chain completeness can verify this phase's `substantiate.json`); and `session.rotate()` moved to a final `### Step 9.8: Session Rotation` (rotating at Step 4.5 would have repointed `.qor/session/current` mid-seal and broken `SESSION_ID` for Steps 7.x-9.x). No code or gate behavior changed -- only the operator-facing skill prose. Locked by `tests/test_substantiate_stepz_structure.py` (char-offset ordering: write before 7.8, rotate after 7.8).

## [0.102.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Changed
- **Phase 135 (pre-1.0 consolidation)**: brought the two governance skills over the Phase 95 `skill_size_budget_lint` 40 KB EXCEEDED budget back under it via pure progressive disclosure. `qor-audit/SKILL.md` (52.7 KB -> 40.6 KB) and `qor-substantiate/SKILL.md` (49.0 KB -> 40.8 KB) relocate multi-paragraph "Phase NN wiring / Per SG-X / originating-recurrence" rationale to `references/` files (new: `qor-audit/references/pre-audit-lints.md`, `qor-substantiate/references/seal-gate-ladder.md` + `release-and-tag-timing.md`; appended: `adversarial-mode.md`, `phase37-subpasses.md`) while preserving every Critical Invariant, Step header, gate command, and VETO/ABORT checklist inline. No skill behavior changes; the corpus now reports zero EXCEEDED findings. Locked by `tests/test_skill_corpus_consolidation.py` (spine-preserved + under-budget + moved-not-deleted + admission).

## [0.101.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 134 (#164, #151)**: #147 cluster conclusion. **#164**: shipped Shadow Genome graph **export** (`ShadowGenomeGraph.to_dict/to_json/to_dot` + `export` CLI subcommand) and recorded a per-capability roadmap decision (`docs/shadow-genome-graph-roadmap.md`) deferring dashboard-API / trust-transition / federation / retention to post-1.0 with rationale. **#151**: recorded the Option-(c) determination that `qor-compliance` is FailSafe-owned/absent from Qor-logic (the in-repo compliance skill is `qor-governance-compliance`, fixed in Phase 81); no duplicate created. Both closed; the half-measure-closures cluster (#147) is fully resolved.

## [0.100.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 133 (#163)**: Pluggable version-bump + changelog backends for non-Python release mechanics. `qor.scripts.version_backends` detects the archetype (pyproject/package.json/Cargo.toml) and bumps the right manifest -- python delegates to the unchanged `governance_helpers.bump_version`; node/rust reuse the same semver compute + tag guards. `qor.scripts.changelog_backends` stamps keepachangelog (delegates to apply_stamp) or a generic prepend format. `/qor-substantiate` Step 7.5/7.6 rewired to the pluggable entry points, so non-Python repos perform real release mechanics instead of SKIPping. Ships #38's deferred Option 2.

## [0.99.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 132 (#162)**: Corpus-growth counterweight (SG-SkillCorpusGrowth-A V2). `qor.scripts.progressive_disclosure_lint` flags SKILL.md heading sections whose inline prose exceeds a per-section budget without pointing to a `references/` file (extraction candidates; escape `<!-- qor:inline-prose-ok -->`). `qor.scripts.corpus_consolidation_report` aggregates total corpus bytes + size-budget findings + extraction candidates into a ranked consolidation worklist, wired into `/qor-process-review-cycle` Phase 4 as a periodic corpus-weight sweep. Both advisory. Ships #92's two deferred V2 directions (progressive-disclosure enforcement + periodic consolidation cadence).

## [0.98.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 131 (#165)**: Closed the #138 residue. Confirmed `shadow_process.append_event` is moot for the `QOR_SKILL_ACTIVE` harness-signal leak (it consumes only the caller-supplied `event['skill']` field, never the env) with a behavioral proof + a source-guard regression test, and added the named `SG-HarnessSignalDrift-A` doctrine entry cataloguing the harness-signal-drift pattern + its shipped countermeasure + the moot finding. No `append_event` change (the phase proves none is needed).

## [0.97.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 130 (#159)**: Per-feature TDD mechanical lint. New `qor.scripts.plan_feature_tdd_lint` parses a plan's `## Feature Inventory Touches` block and flags `NEW`/`MODIFIED` feature rows that lack a failing-test declaration (no real `test_path`, or a presence-only `test_descriptor`), plus a plan that touches `src/` with no FIT block. `n/a-justified` rows + docs-only plans are exempt. Wired WARN-only into `/qor-audit` Step 0.6; the binding VETO stays the Step 3 Feature Test Coverage Pass. Ships #41's deferred V2 enforcement lint.

## [0.96.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Changed
- **Phase 129 (#153 + #154)**: SG-MergePaceThrottle-A enforcement + full wiring (combined). `/qor-substantiate` Step 4.6.8 merge-velocity gate is now **fail-closed** — an `exceeded` grade ABORTs the seal (was `|| true`); `merge_velocity_check --override` is the logged operator escape (emits `gate_override`). `workspace_fragility_check` regained the dropped `stabilization_capacity` + `shared_surface_risk` fields and the `branch_only` recommended action, and is now wired into `/qor-plan` (Step 0.4) and `/qor-implement` (Step 0.6) as WARN-only stabilization-capacity / scope-boundary checkpoints. Closes the deferred enforcer (#89) + plan/implement wiring + dropped-fields (#90).

## [0.95.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 128 (#161)**: `plan_text_consistency_lint` gains the two sub-modes #46 deferred. `--apply` (V2.3) rewrites detected command/path drift in place, normalizing every divergent site in a group to a canonical raw text (most-common; tie -> earliest); dry-run remains the default, so the Step 0.6 report contract is unchanged. `--type-check` (V2.4) flags identifiers given conflicting `name: Type` annotations across fenced code blocks. dep_name findings are not auto-rewritten. Behavioral tests for apply + type-check.

## [0.94.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 127 (#156)**: LiveProgressInvariant detector. New `qor.scripts.plan_live_progress_lint` mechanically detects the SG-FakeProgress-A patterns in a target repo's frontend source -- fake-jump (`0%`->`100%` with no intermediate width write), missing event-stream subscription, and error-without-dismiss -- replacing the hand-only Ghost-UI Live-Progress checklist. Promoted `live-progress-fake` from a prose sub-tag to a `findings_categories` schema enum value (+ findings_signature mirror). Wired WARN-only into `/qor-audit` Step 0.6; backend-only repos produce zero findings; escape `// qor:live-progress-ok`. Ships #156's AC2 (enum) + AC3 (detector + behavioral tests) that PR #69 left prose-only.

## [0.93.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 126 (#157)**: Citation consumer-trace executable check. New `qor.scripts.citation_consumer_trace` implements the Phase 83 reachability sub-check as a runnable grep-recursive trace: `trace_reachable` greps an entry-point file for a cited symbol and follows its transitive in-repo import graph (Python + JS/TS, repo-root-bounded, depth+visited guarded). `/qor-audit` Phase 37 consumer-trace Step 2 now invokes `citation_consumer_trace --entry <surface> --symbol <name>` (exit 1 => infrastructure-mismatch) instead of a manual grep. Ships #157's executable check + positive/negative behavioral fixtures that PR #83 left prose-only.

## [0.92.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 125 (#152)**: Citation-drift enforcement. Extended `qor.scripts.plan_grep_lint` with `check_citation_evidence`, which flags sealed-infrastructure citations (git-show ref / migration filename / `file:line`) inside a plan's Locked-Decision / Citation-Inventory region when the block carries no paired grep-evidence statement (`git show ... | grep ... -> observed`). LD-region-scoped so ordinary plans produce zero findings; runs WARN-only at `/qor-audit` Step 0.6 (the binding VETO remains the P2 iter-N>1 re-walk). Ships SG-CitationDrift-A AC4 + behavioral AC5/AC6 (incl. the attribution-12g cross-iteration regression) that PR #67 left as prose-only.

## [0.91.0] - 2026-06-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed
- **Phase 124**: Release pipeline unblocked. `release.yml`'s tag trigger carried `paths-ignore`, which makes GitHub skip path-filtered `push` workflows on tag pushes — silently skipping every release since v0.85 (PyPI stuck at v0.84.0). Removed `paths-ignore` from the tag trigger and added `workflow_dispatch` with a `tag` input so the corrected workflow (from `main`) can build+publish a historical tag whose own commit still has the broken trigger. Both jobs now check out the resolved ref (`inputs.tag || github.ref_name`), derive the reachability guard from the checked-out HEAD, and pass the ref via `env:` (no Actions script injection). Enables catch-up publish of v0.85–v0.90.

## [0.90.0] - 2026-06-01

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 123 (#160)**: External-reviewer subprocess bridge for `/qor-audit` Option B. New `qor.scripts.external_reviewer` dispatches the #50 reviewer I/O contract to an operator-configured external reviewer (`.qorlogic/config.json` → `external_reviewer.command`, argv) over stdin/stdout JSON, validates the returned verdict against the contract, and degrades to a graceful in-harness `fallback` (logged `capability_shortfall`) when the reviewer is absent, errors, times out, or returns invalid output. Flips `adversarial-mode.md` from "Contract-only specification" to shipped. Closes #50's documented deferral.

## [0.89.0] - 2026-06-01

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Changed
- **Phase 122 (#155)**: Seal-time feature-regression gate flipped **fail-closed**. Phase 114's `feature_index_verify` (outside-scope `verified->unverified` detector vs a prior-seal snapshot) was wired into `/qor-substantiate` Step 6 with `--warn-only`; Step 6 now runs it `|| ABORT` so a regression blocks the PASS seal. New per-seal logged escape `--override` emits a `gate_override` shadow event (`details.gate = feature_index_verify`) — the explicit logged override the #155 AC requires. Snapshot baseline + detection logic unchanged; absent `FEATURE_INDEX.md` still disclosed-skips. Also restored the missing `[0.88.0]` CHANGELOG attribution line.

## [0.88.0] - 2026-06-01

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 121 (#177)**: Runtime-principal fidelity + Data-API access-control enforcement. Closes the privileged-principal false-PASS class where tests run under `service_role` / a `SECURITY DEFINER` RPC bypass RLS + table `GRANT`s, so a feature broken for its `authenticated`/`anon` caller seals green. `/qor-substantiate` Step 4 adds a runtime-principal fidelity gate (fail-closed unless an explicit disclosed coverage-gap note is recorded) and Step 4.6.10 invokes the new `qor.scripts.data_api_acl_lint` (`|| ABORT`): a static SQL-migration scan flagging `missing-grant` (API-schema `CREATE TABLE` with no GRANT to authenticated/anon) and `definer-view` (view without `security_invoker = true`); `security-definer-fn` is advisory. Escapes: `-- qor:service-role-only`, `-- qor:definer-view-intended`. Absent migrations → Phase 75 disclosed-skip. `/qor-audit` Security Pass gains the plan-level Data-API access-control checklist.

## [0.87.0] - 2026-05-30

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 120 (#149)**: Governance Index enforcement — wires `GOVERNANCE_INDEX` into `/qor-substantiate` (Step 4.7.5, fail-closed) and `/qor-validate` (ledger cross-check), closing #140's deferred enforcement half. `governance_index.enforce_at_seal` auto-advances `Last Reviewed` to the seal date then fail-closes on `unregistered` (doc in no tier) or `tier3-unarchived` (a Tier 3 row naming an already-sealed phase); `cross_check_index_against_ledger` is the read-only validate check. New CLI flags `--advance-last-reviewed`/`--enforce`/`--cross-check-ledger`; absent index records a Phase 75 disclosed-skip. Doctrine flipped from V2-deferred to shipped (the `/qor-implement` stale-Tier-1 block + auto row-mutation remain deferred).

## [0.86.0] - 2026-05-30

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 119 (#148)**: `qor-logic reconcile propose|authorize` — real, forward-only META_LEDGER reconciliation superseding the Phase 91 `--tolerate-known-grandfathered` stopgap. Two-stage operator-authorized flow (mirroring Phase 36 B19): `propose` writes a pending proposal of the duplicate-`previous_hash` residual (read-only); `authorize --proposal <path>` appends a `RECONCILIATION` entry attesting the residual. `verify-ledger` reports `DISCLOSED_RECONCILED` for the attested set without the `--tolerate` flag — but only for genuine duplicate-`previous_hash` members, so an attestation cannot launder content tampering. Sealed entries are never renumbered or rewritten. Doctrine SG-ConcurrentLedgerRace-A updated with the V2 real fix.

## [0.85.0] - 2026-05-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 118 (#150)**: `qor-logic reliability <module>` / `qor-logic scripts <module>` CLI dispatch (Option A for module reachability). The dispatch runs the named `qor.reliability`/`qor.scripts` module through the CLI's own `sys.executable`, so integrity gates resolve from any shell regardless of which `python`/venv is active. Canonical skill prompts now invoke gates via the dispatch form; the bare `python -m qor.<family>.<module>` form is retained as the documented in-venv fallback (hybrid migration).

## [0.84.0] - 2026-05-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Changed
- **Phase 117 (#174)**: Hardened `qor.scripts.prose_test_lint` and graduated it to an enforced `/qor-audit` gate. The heuristic now flags only assertions whose membership comparator traces to a SKILL.md read (incl. module-level path constants), eliminating a ~20% false-positive rate; added an inline `# prose-lint: ok=<reason>` allowlist. Drove the suite to zero unexplained findings (39 exempted-with-reason; convertible findings gained `find_spec`/`.exists()` behavioral assertions). `--enforce` now VETOs in the Test Functionality Pass; `tests/test_prose_lint_floor.py` locks the floor.

## [0.83.0] - 2026-05-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 116 (#168, #169, #170)**: VCI completion. qa.json `coverage` pillar (`qa_evidence.run_coverage`, reads coverage data + threshold, skip when absent) and `stability` pillar (`qa_evidence.run_stability`, re-walks the runtime contract via `runtime_contract_walk` #108 at seal time) -- all four pillars now real. New `qor.scripts.prose_test_lint`: AST scan flagging presence-only test assertions (substring-in-SKILL.md), wired WARN-first into `/qor-audit` Test Functionality Pass (the #56/#58/#83 anti-pattern; the lint surfaces 40 pre-existing instances).

## [0.82.0] - 2026-05-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 115 (#167)**: VCI security pillar via SAST. New `qor.scripts.sast_scan` with a tool-agnostic backend interface (default bandit, pure-Python; semgrep pluggable later) feeding the qa.json `security` pillar (`qa_evidence.run_sast`). Degrades to `skip` when the backend is absent (Phase 75 prerequisite-absent semantics); a HIGH finding fails the pillar and the overall qa verdict. bandit declared as an optional `sast` extra. Doctrine updated with the SAST Backend contract.

## [0.81.0] - 2026-05-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 114 (#166, #158)**: Verification & Closure Integrity (spine slice). New `qa.json` evidence gate artifact (`qor/gates/schema/qa.schema.json` + `qor.scripts.qa_evidence`; `qa` registered phase) with four pillars (regression real, security/stability/coverage explicit skip+note). The deferred FEATURE_INDEX regression ABORT now ships (`feature_index_verify` CLI, `--warn-only`). New acceptance-criteria close guard (`qor.scripts.ac_close_guard`, WARN-first): met-ness from the qa.json verdict, unmet criteria must be split into a filed follow-on. New `doctrine-verification-closure-integrity.md`; consolidates into the existing substantiate FEATURE_INDEX pass rather than a parallel gate. Deferred to tracked follow-ons (#167-#170): SAST, coverage pillar, seal-time runtime-contract re-walk, prose-not-behavior test-source lint.

## [0.80.0] - 2026-05-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 113 (#139)**: Shadow Genome causal-graph layer (core only). New
  `qor.scripts.shadow_genome_graph` — typed nodes (checkpoint/state/failure/
  governance) + typed edges (produced/occurred_during/triggered_by/applies_to)
  over append-only JSONL with deterministic ids; `trace_chain` (cycle-safe,
  depth-limited), `snapshot`, `query`, and a CLI — giving operators and
  `/qor-debug`/`/qor-remediate` root-cause traceback. New
  `doctrine-shadow-genome-graph.md` + two glossary terms. Per the honest
  qor-logic fit assessment, the proposal's governance dashboard API, CBT/KBT/IBT
  trust-level transitions, and cross-module federation are **declined** for
  qor-logic (they realize their advantage in a consuming product/UI this repo
  does not have); strictly append-only, no retention automation in V1.

## [0.79.0] - 2026-05-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 112 (#140)**: Hierarchical Governance Index. New
  `docs/GOVERNANCE_INDEX.md` — a 6-tier (Canonical / Doctrine / Active /
  Per-Plan / Reference / Archived) freshness map of every governance artifact,
  scaffolded by seed and joined to the Phase 109 governance-health registry.
  New WARN-only drift checker `python -m qor.scripts.governance_index`
  (stale-Tier-1 / unregistered-doc / missing-index), `doctrine-governance-index.md`,
  three glossary terms, and a `/qor-status` drift surface. The repo dogfoods its
  own index. Full Tier 3->6 / 4->6 archival enforcement, `/qor-validate`
  cross-check, and a hard `/qor-implement` block on stale Tier 1 are deferred to V2.

## [0.78.0] - 2026-05-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed

- **Phase 111 (#138)**: `QOR_SKILL_ACTIVE` env-var leakage. Added
  `gate_chain.skill_active(<phase>)` context manager and a `skill=` parameter on
  `write_gate_artifact` so scripts self-manage the provenance env var (set for
  the wrapped scope, prior value restored on exit) instead of a leak-prone inline
  shell prefix that could strand a stale phase on a status surface. Added the
  authoritative active-phase reporter `python -m qor.scripts.active_phase`
  (newest gate-artifact `phase`) as a non-leaking status source. Backward
  compatible (ambient-env path unchanged when `skill` is omitted).

## [0.77.0] - 2026-05-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 110 (feature)**: `SG-AffectedFilesContract-A` countermeasure suite.
  New pre-audit lints `plan_signature_widening_caller_lint` (#133, caller-graph
  cascade) and `plan_data_round_trip_lint` (#134, struct-field persistence
  cascade), both WARN-only and wired into `/qor-audit` Step 0.6; three new
  `audit_risk_score` Option-B signals (#135) with a `--repo-root` flag; the
  `SG-AffectedFilesContract-A` doctrine entry with bidirectional sibling
  cross-references (#136); and a `/qor-plan` Step 5 cascade-discipline checklist
  bullet (#137). Shared `qor/scripts/_lint_utils.find_callers` centralizes
  caller discovery. Escape hatches: `<!-- signature-widening-exempt: <fn> -->`,
  `<!-- transient-field: Struct.field reason: ... -->`.

## [0.76.0] - 2026-05-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 109 (feature)**: governance artifact health gate. New
  `qor.scripts.governance_health` classifies the required governance
  artifacts as `OK` / `UNINITIALIZED` / `MISSING` / `DAMAGED` /
  `INCOMPLETE`, each with its single legal next action; exposed as
  `qor-logic governance-health` (exit 0/1/2). 17 governance-reading source
  skills gained a `qor:governance-health-preflight` marker (with
  `qor-bootstrap` and `qor-remediate` justified-exempt); `/qor-status`
  gained a Step 0 health gate that surfaces `DAMAGED`/`INCOMPLETE` before
  lifecycle routing. New doctrine terms: Governance Artifact Health,
  Ungoverned Path Forward, Governance Repair Mode. `DAMAGED` and
  `INCOMPLETE` are blocking and route to `/qor-remediate` or section
  completion -- never to seed or bootstrap.

## [0.75.1] - 2026-05-26

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed

- **Phase 108 (hotfix)**: lock `typing-extensions==4.15.0` into
  `requirements-sbom.txt` to satisfy `--require-hashes` install on
  Python 3.12 (the release workflow's resolver). Phase 107's
  `pip-compile` ran on Python 3.13 where the resolver treated
  `typing_extensions<5.0,>=4.6` (transitive of
  `cyclonedx-python-lib[validation]==11.7.0`) as satisfied by stdlib;
  3.12 still requires the backport package. v0.75.0 PyPI publish was
  blocked by this; v0.75.1 ships the corrected lockfile.

## [0.75.0] - 2026-05-26

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 107 (feature)**: closes all five accumulated V2 carry-forward
  items in one cohesive cycle. Wraps the open work surface to zero.
  - **Cooling-period lint flipped to hard fail** (Phase 105 V2 #1):
    removed `|| true` from the cooling-period lint step in
    `.github/workflows/pr-dependency-review.yml`. The lint step now
    exits non-zero on real violations, blocking PR merge. Operator
    override path remains operative (META_LEDGER `**Dependency
    admission override**:` entry OR `dep-admit-override` PR label).
  - **cyclonedx-bom hash-pinning** (Phase 102 V2): new
    `requirements-sbom.in` + `requirements-sbom.txt` (autogenerated
    via `pip-compile --generate-hashes`; ~390 lines; lxml dominates).
    Release workflow build job switched from
    `pip install cyclonedx-bom` to
    `pip install --require-hashes -r requirements-sbom.txt`. The
    lockfile is explicitly Razor-exempt per the Phase 107 plan's
    "Razor Exemption" block (autogenerated lockfile size tracks
    dependency graph, not authoring complexity; exemption narrowly
    scoped to this single file).
  - **Range-pin lower-bound coverage** (Phase 106 V2): new
    `parse_pyproject_range_pins(text)` in `_dep_admit_common.py`
    extracts lower-bound versions from `>=X.Y.Z` and `~=X.Y.Z` PEP
    440 specifiers in `[project] dependencies` and
    `[project.optional-dependencies]`. The lint applies the 14-day
    threshold to those lower-bound versions because pip's installer
    could resolve to that version on a fresh install. `<`, `!=`, and
    unbounded specifiers continue to be skipped.
  - **GH-issue emit for tracker** (Phase 105 V2 calendar/GH-issue):
    `dep_admit_override_tracker.py` gains `--emit-issue` flag. When
    set, builds a single rollup body listing all due (≥30 days old)
    overrides and invokes
    `gh issue create --label dep-admit-override-review`. Single
    rollup per invocation (anti-spam); silent when no due entries.
  - **CODEOWNERS solo-owner doctrine** (Phase 101 V2): new §6.1
    "CODEOWNERS operational mode" in
    `qor/references/doctrine-governance-enforcement.md` documents
    that the solo-owner state (`@Knapp-Kevin` for all
    security-critical files) is the project's chosen operational
    mode for the current maintainer configuration, not an interim
    placeholder. Four expansion trigger conditions named (second
    maintainer joins, federation, compliance audit, operator-
    initiated team formalization).
- `tests/test_requirements_sbom_lockfile.py` -- NEW, 3 tests.
- `tests/test_codeowners_doctrine.py` -- NEW, 2 tests.
- `tests/test_dep_admit_common.py` -- amended (+2 range-pin tests).
- `tests/test_dependency_admission_lint.py` -- amended (+1 range-pin
  within-window test).
- `tests/test_dep_admit_override_tracker.py` -- amended (+2 emit-issue
  tests).
- `tests/test_pr_dependency_review_workflow.py` -- amended (+1 test
  asserting no `|| true` wrap).
- `tests/test_release_workflow_immutability.py` -- amended (+2 tests
  asserting SBOM tool is hash-pinned and runs after install).
- `qor/references/glossary.md` -- 4 new term entries (`range-pin
  lower-bound check`, `SBOM hash-pinned lockfile`, `override rollup
  issue`, `CODEOWNERS operational mode`).
- `qor/references/doctrine-dependency-admission.md` -- additive
  Phase 107 closure note under `### Check mechanic`.
- `qor/references/doctrine-governance-enforcement.md` -- new §6.1
  documenting CODEOWNERS operational mode + 4 expansion triggers.

### Changed

- `pyproject.toml` version 0.74.0 -> 0.75.0 (feature change_class).
- `.github/workflows/pr-dependency-review.yml` -- cooling-period lint
  step removed `|| true` wrap; failures now block PR merge.
- `.github/workflows/release.yml` -- SBOM install step switched from
  unpinned `pip install cyclonedx-bom` to hash-pinned
  `pip install --require-hashes -r requirements-sbom.txt`.
- `qor/scripts/_dep_admit_common.py` -- adds
  `parse_pyproject_range_pins(text)` and `_PYPROJECT_RANGE_PIN_RE`.
- `qor/scripts/dependency_admission_lint.py` -- `run_lint()` unions
  range-pin bumps with exact-pin bumps.
- `qor/scripts/dep_admit_override_tracker.py` -- adds `subprocess`
  import, `emit_rollup_issue(due_rows)` helper, and `--emit-issue`
  CLI flag.

### Security

- Cooling-period enforcement is now binding (was visibility-only V1.1).
  Operator override procedure (Phase 103 doctrine) remains operative
  as the loud-recoverable safety valve.
- SBOM tool installation is now hash-pinned via pip's
  `--require-hashes`, closing the last unpinned-pip-install path in
  the release workflow.
- Range-pin lower-bound coverage closes the freshness-vector admission
  gap where a `>=X.Y.Z` constraint could allow a within-window
  install without lint visibility.
- After Phase 107 seals, the project's V2 carry-forward list reaches
  **zero items**. Future cycles begin from a clean carry-forward
  surface.

## [0.74.0] - 2026-05-26

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 106 (feature)**: dependency-admission lint V1.1 extensions
  on top of Phase 105's V1 surface.
  - **PR-label override** (`dep-admit-override` label): the lint now
    detects CI context (`GITHUB_EVENT_NAME=pull_request` +
    `GITHUB_REPOSITORY` + PR number from `GITHUB_REF`) and shells out
    to `gh pr view <n> --repo <owner>/<name> --json labels`. Presence
    of `dep-admit-override` clears within-window admissions. Fails
    open: any gh non-zero exit emits a stderr fallback note and falls
    back to META_LEDGER-only override check. New `--skip-pr-labels`
    flag for local testing. META_LEDGER `**Dependency admission
    override**:` entries remain binding-authority; PR label is
    supplementary.
  - **pyproject.toml exact-pin coverage**: new
    `parse_pyproject_exact_pins(text)` in `_dep_admit_common.py` uses
    stdlib `tomllib` to extract `[project] dependencies` and
    `[project.optional-dependencies]` entries matching PEP 440
    exact-pin form (`package==X.Y.Z`). Range pins (`>=4`, `~=2.1`)
    and unbounded specifiers are skipped because the resolved version
    is not knowable until install time. The lint diff loop unions
    pyproject bumps with lockfile bumps before the PyPI query loop.
  - **Session ID convention lint**: new
    `qor/scripts/session_id_lint.py` (~46 lines) emits a non-blocking
    stderr WARN at `/qor-substantiate` Step 4.6 when the active
    `.qor/session/current` marker doesn't match
    `qor.scripts.session.SESSION_ID_PATTERN` (canonical 6-hex slug
    format `\d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}$`). Always exits 0;
    the WARN names the canonical format and points operators at
    `session.rotate()` for compliant generation. Closes the
    fall-through-to-default pattern where event provenance fragments
    across sessions.
- `tests/test_dep_admit_common.py` -- amended with 3 tests for
  pyproject exact-pin parsing.
- `tests/test_dependency_admission_lint.py` -- amended with 3 tests
  for PR-label override (success + fails-open) and pyproject
  within-window violation.
- `tests/test_session_id_lint.py` -- NEW, 3 tests (WARN on
  mismatch, silent on match, silent on missing marker).
- `qor/references/doctrine-dependency-admission.md` -- additive
  Phase 106 V1.1 extensions note under `### Check mechanic`.
- `qor/references/doctrine-governance-enforcement.md` -- new §7.1
  "Session ID convention" subsection documenting the canonical
  format + the `session_id_lint` WARN surface.
- `qor/references/glossary.md` -- 3 new term entries (`PR-label
  override`, `pyproject exact-pin admission`, `session ID
  convention lint`).
- `docs/plan-qor-phase89-ci-commands-reconciliation.md` -- forward-
  maintenance bullet for the new `python -m qor.scripts.session_id_lint`
  command (the self-applied CI surface test requires Phase 89's plan
  to enumerate every operator-runnable Python invocation across all
  workflows).

### Changed

- `pyproject.toml` version 0.73.0 -> 0.74.0 (feature change_class).
- `qor/skills/governance/qor-substantiate/SKILL.md` Step 4.6 -- adds
  a 4th line invoking `python -m qor.scripts.session_id_lint` with
  `|| true` belt-and-suspenders (the script already exits 0
  unconditionally; the wrap documents intent for future readers).

### Security

- No new security-critical paths. The new PR-label query shells out
  to `gh` with list-form argv (no shell=True; SG-Phase47-A
  countermeasure honored); GitHub-controlled `GITHUB_REF` is regex-
  parsed for the PR number (digit-only capture). The
  `tomllib` parser is the stdlib safe TOML reader (no code execution).
  Fails-open semantics on the PR label query are deliberate and
  documented in the plan: a failed network query must not introduce
  a spurious within-window violation when the operator has done the
  right thing via META_LEDGER override entry.

## [0.73.0] - 2026-05-25

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 105 (feature)**: dependency-admission tooling implementing
  the Phase 103 doctrine carry-forward.
  - `qor/scripts/_dep_admit_common.py` -- shared parsing helpers:
    `parse_lockfile_entries` (pip-compile --generate-hashes format),
    `diff_lockfile_against_base` (new + version-bumped entries),
    `parse_override_entries` (META_LEDGER `**Dependency admission
    override**:` lines). Three frozen dataclasses (`LockfileEntry`,
    `Bump`, `OverrideEntry`) + `LockfileParseError` for malformed
    input. Pure functions, no I/O.
  - `qor/scripts/dependency_admission_lint.py` -- cooling-period
    lint. Walks `requirements-release.txt` diff against a base ref
    (default `merge-base origin/main HEAD`), queries the PyPI
    Warehouse API (`https://pypi.org/pypi/<pkg>/<version>/json`)
    for each new or bumped entry's `urls[0].upload_time_iso_8601`,
    reports admissions younger than the 14-day cooling-period
    threshold absent matching ledger override. Bounded retry
    (3 × 5s = 15s budget per package via stdlib `urllib.request`).
    Exit codes 0/1/2 (clean / violations / network failure).
    Markdown summary table + per-violation stderr.
  - `qor/scripts/dep_admit_override_tracker.py` -- 30-day
    re-evaluation tracker. Scans META_LEDGER for override entries
    and emits markdown (or CSV) table with `--filter due|pending|all`
    + `--since YYYY-MM-DD` + `--follow-up-days N`. Always exit 0
    (informational tool).
  - `.github/workflows/pr-dependency-review.yml` -- amended with
    WARN-only lint step (`|| true` wrap per Phase 99 V2 ramp
    pattern); setup-python step gains `cache: pip` for unprivileged
    PR-time workflow. V2 phase will flip the WARN to hard fail
    after operator-evidence accumulates.
- `tests/test_dep_admit_common.py` (4 tests), `tests/test_dependency_admission_lint.py`
  (5 tests with mocked PyPI), `tests/test_dep_admit_override_tracker.py`
  (3 tests). 12 new behavioral tests; all pass twice deterministically.

### Changed

- `pyproject.toml` version 0.72.0 -> 0.73.0 (feature change_class).
- `qor/references/doctrine-dependency-admission.md` -- additive note
  under `### Check mechanic` pointing operators at the Phase 105 lint
  + tracker tools and documenting the WARN-only ramp.
- `docs/plan-qor-phase89-ci-commands-reconciliation.md` -- forward-
  maintenance entry for the new `python -m qor.scripts.dependency_admission_lint`
  command. Phase 89's self-applied CI surface test requires its plan
  to enumerate every operator-runnable Python invocation across all
  workflows.
- `qor/references/glossary.md` -- 3 new term entries (Phase 105) +
  9 `referenced_by` backfill rows for pre-existing terms
  (`Doctrine`, `Shadow Genome`, `Substantiate`,
  `gate_skipped_prerequisite_absent`, `SG-HalfSealedClaim-A`) caught
  by the Phase 32 strict-mode `check_term_drift` + `check_cross_doc_conflicts`
  passes at seal time.
- `qor/references/doctrine-definition-of-done.md` -- reworded one
  sentence ("a compile gate is offline" -> "the compile-gate runtime
  is offline") to dodge a false-positive in the
  `check_cross_doc_conflicts` regex (`\bGate\s+(?:is|means|refers to)\s+...`).

## [0.72.0] - 2026-05-25

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed

- **Phase 104 (hotfix)**: release publish-step bug. The Phase 101 build
  job placed `SHA256SUMS` into `dist/`; Phase 102 added `sbom.json` and
  `evidence.json` into `dist/`. `pypa/gh-action-pypi-publish` uploads
  every file in its `packages-dir` (default `dist/`), so the published
  workflow failed with `InvalidDistribution: Unknown distribution
  format: 'SHA256SUMS'`. Tags v0.69.0/v0.70.0/v0.71.0 were pushed and
  their workflows failed at the publish step; nothing reached PyPI.
  - Fix: insert a `Prepare publish-only directory` step that creates a
    sibling `dist-publish/` containing only `*.whl` and `*.tar.gz`;
    point pypa-publish at `dist-publish/` via `with.packages-dir`.
    Downstream evidence-assembly + pull-back + `gh release create`
    steps continue to operate on `dist/` (which still contains the
    auxiliary files).
  - The failed v0.69.0/v0.70.0/v0.71.0 tags remain on the remote as
    historical artifacts. PyPI is unaffected (nothing was uploaded).
    This v0.72.0 release ships the cumulative cluster work from Phases
    101-103 plus the Phase 104 fix.

### Added

- `.github/dependabot.yml` -- carry-forward from the closed hygiene
  PR #122; folded into this hotfix so it ships under a plan + Merkle
  seal (clears the PR-citation lint requirement). Manages:
  - `github-actions` ecosystem (weekly Monday checks; preserves the
    `# vX.Y.Z` annotation comments added in Phase 101; grouped
    minor+patch updates to reduce PR noise)
  - `pip` ecosystem (weekly Monday checks for the hash-pinned
    `requirements-release.txt` lockfile added in Phase 102)
- `tests/test_dependabot_config.py` (3 tests: presence, both
  ecosystems covered, supported schedule intervals)
- `tests/test_release_workflow_immutability.py` amended with 2 new
  tests asserting the separate `packages-dir` pattern + the prepare
  step excludes known non-distribution files.

### Changed

- `pyproject.toml` version 0.71.0 -> 0.72.0. Hotfix change_class
  normally implies a patch bump, but v0.69.0/v0.70.0/v0.71.0 tags
  exist as historical artifacts with failed publish workflows; v0.72.0
  takes the next available minor to avoid claimed-but-unpublished
  version confusion on PyPI.

### Security

- `pypi` GitHub environment: `can_admins_bypass: false` set via
  `gh api PUT` (the GitHub Environments API has since added support
  for this field; closes the Phase 101 carry-forward UI follow-up).
- `pypi` environment: `prevent_self_review: false` set to resolve
  the single-maintainer deadlock (Knapp-Kevin is the only reviewer
  and also the deployment creator). Required-reviewer rule + tag-only
  branch policy + admin-bypass-disabled remain operative.

## [0.71.0] - 2026-05-24

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 103 (feature, GH #118 P2 — CLUSTER CLOSE)**: PyPI publication
  hardening P2 closing the final 2 acceptance items from issue #118.
  Issue #118 now fully closed across the 3-phase cluster (101+102+103).
  - Release workflow's publish job adds a post-publish PyPI pull-back
    verification step between `pypa/gh-action-pypi-publish` and
    `gh release create`. Extracts version from `${GITHUB_REF_NAME#v}`,
    runs `pip download --no-deps --no-cache-dir qor-logic==<VERSION>`
    with bounded retries (6 attempts × 10s = 60s budget), computes
    SHA-256 of downloaded wheel/sdist, and `diff -u`-compares against
    the build-produced `dist/SHA256SUMS`. Mismatch fails the workflow
    non-zero, preventing GitHub release creation with a false bundle.
    Closes F-4b.
  - `qor/references/doctrine-dependency-admission.md` (NEW) declares
    the cooling-period policy: a transitive dependency must have a
    release age of at least 14 days before entering the release tree.
    Override procedure (META_LEDGER `**Dependency admission override**:`
    entry + `dep-admit-override` PR label + 30-day follow-up
    re-evaluation) is operative; automated 14-day check tooling
    deferred to a future hygiene phase. Coordinates with the Phase 102
    dependency-review-action workflow (severity-graded vulnerability
    catch is orthogonal to the freshness-vector catch). Closes F-3c.
- `tests/test_doctrine_dependency_admission.py` -- 5 tests
  (presence, 14-day threshold, override procedure, coordination
  with dep-review workflow, SSDF mapping).
- `tests/test_release_workflow_immutability.py` -- amended with
  2 new tests (pull-back step position between publish and gh release;
  bounded retry semantics with for-loop + sleep + exit).

### Changed

- `pyproject.toml` version 0.70.0 -> 0.71.0 (feature change_class per
  Phase 103 plan; minor SemVer bump).

### Security

- Supply-chain (cluster close): all three independent ancestry legs
  now operative -- commit-ancestry (Phase 40 tag-reachable guard +
  Phase 101 replication to both jobs), artifact-ancestry (Phase 101
  SHA256SUMS handoff + Phase 102 hash-pinned lockfile + Phase 103
  PyPI pull-back), workflow-ancestry (Phase 101 SHA pins on all
  third-party Actions + Phase 102 CODEOWNERS + dependency-review +
  SBOM + evidence bundle). The cooling-period doctrine adds an
  orthogonal catch for the freshness-vector attack class. All 13
  GH #118 acceptance items closed.

## [0.70.0] - 2026-05-24

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 102 (feature, GH #118 P1)**: PyPI publication hardening P1
  closing 4 more acceptance items from issue #118 (9 of 13 closed
  across the cluster so far).
  - `requirements-release.in` + `requirements-release.txt` -- new
    hash-pinned build lockfile (`build==1.5.0` + 3 transitives,
    SHA-256 pinned via pip-tools). Release workflow's build job now
    runs `pip install --require-hashes -r requirements-release.txt`
    instead of bare `pip install build`.
  - `.github/CODEOWNERS` -- governance for security-critical files
    (workflows, pyproject.toml, lockfile pair, intent_lock,
    configure_pypi_environment). Single owner `@Knapp-Kevin` initial;
    broaden as team grows.
  - `.github/workflows/pr-dependency-review.yml` -- runs
    `actions/dependency-review-action@2031cfc...` (v4.9.0, SHA-pinned)
    on PRs touching dependency-bearing files; fails on `high` severity;
    comments summary on failure.
  - Release workflow now generates an SBOM via `cyclonedx-py
    environment --of JSON` (in the build job; `cyclonedx-bom` installed
    unpinned -- hash-pinning deferred as documented non_goal; its
    transitive set, especially lxml, would exceed the Razor file
    budget). SBOM travels with the `release-dist` artifact.
  - Publish job assembles `dist/evidence.json` containing `git_sha`,
    `tag`, `workflow_run_id`, `workflow_sha`, `lockfile_sha256`,
    `artifact_sha256sums`, and `action_pins`. After publishing,
    `gh release create` attaches `dist/*.whl`, `dist/*.tar.gz`,
    `sbom.json`, `evidence.json`, and `SHA256SUMS` to the GitHub
    release. Closes F-4a (SBOM + evidence) and F-4c (record workflow +
    action SHAs + lockfile hashes).
- `tests/test_requirements_release_lockfile.py` -- 5 tests (lockfile
  presence, SHA-256 hash format, build pin, transitive coverage,
  build job consumes `--require-hashes`).
- `tests/test_pr_dependency_review_workflow.py` -- 4 tests (file
  exists, action SHA-pinned with annotation, triggers cover
  pyproject/lockfile/workflows, fails on high severity).
- `tests/test_codeowners.py` -- 5 tests (file exists, workflow dir
  rule, pyproject + lockfile rules, intent_lock + env-config rules,
  every rule has an owner).
- `tests/test_release_workflow_immutability.py` -- amended with 3
  new tests (SBOM step in build, evidence-bundle assembly in publish,
  `gh release create` attaches the required artifacts).

### Changed

- `pyproject.toml` version 0.69.0 -> 0.70.0 (feature change_class per
  Phase 102 plan; minor SemVer bump).
- Publish job's `permissions.contents` `read` -> `write` to enable
  `gh release create` for the evidence-bundle attachment.
  `id-token: write` remains scoped to publish job only.

### Security

- Supply-chain: hash-pinned build lockfile prevents transitive-dep
  drift at install time; dependency-review-action catches vulnerable
  or high-severity dependencies entering via PR; SBOM + evidence
  bundle provide audit-grade provenance attached to every GitHub
  release. CODEOWNERS attaches required-reviewer enforcement at the
  surfaces being hardened. Phase 101's structure-AND-policy discipline
  extended to all three independent ancestry legs (commit-ancestry,
  artifact-ancestry, workflow-ancestry).

## [0.69.0] - 2026-05-24

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 101 (feature, GH #118 P0)**: PyPI publication hardening
  closing 5 of 13 acceptance items from issue #118.
  - `.github/workflows/release.yml` split into two jobs: unprivileged
    `build` (`contents: read`, allowed to use pip cache) and privileged
    `publish` (`id-token: write`, `environment: pypi`, `needs: build`,
    no cache). Build job generates `dist/SHA256SUMS` and uploads
    `release-dist` artifact; publish job downloads and verifies SHAs
    via `sha256sum -c` before invoking `pypa/gh-action-pypi-publish`.
  - All third-party Actions across `release.yml`, `ci.yml`, and
    `pr-lint.yml` SHA-pinned to full commit hashes with `# vX.Y.Z`
    annotation comments. Worst prior pin was a mutable branch ref
    (`pypa/gh-action-pypi-publish@release/v1`).
  - GitHub `pypi` environment now backed by required-reviewer +
    tag-only deployment-branch policy + prevent-self-review
    (configured live via new `qor/scripts/configure_pypi_environment.py`
    idempotent script). Closes F-1a "structure-without-policy" gap
    where the environment existed since 2026-04-16 but had zero
    protection rules.
  - Tag-ancestry guard (`git merge-base --is-ancestor origin/main`)
    preserved and replicated to both jobs as defense-in-depth.
- `qor/scripts/configure_pypi_environment.py` -- idempotent
  gh-api wrapper exposing `build_put_body()` (pure factory) and
  `build_branch_policy_body()` for unit testing. Supports `--dry-run`.
- `tests/test_release_workflow_immutability.py` -- 8 structural tests:
  SHA-pinning across all three workflow files, build/publish split,
  id-token scoping, cache-isolation asymmetry, artifact-handoff with
  SHA verification.
- `tests/test_configure_pypi_environment.py` -- 7 unit tests on the
  PUT-body factory (reviewer requirement, tag-only policy,
  idempotency, input validation).
- `tests/test_release_workflow_guard.py` -- amended with
  `test_tag_ancestry_guard_present_in_both_jobs` to lock in the
  load-bearing-gate replication.

### Changed

- `pyproject.toml` version 0.68.1 -> 0.69.0 (feature change_class
  per Phase 101 plan; minor SemVer bump).

### Security

- Supply-chain: workflow Actions no longer pinned to mutable tag or
  branch refs; OIDC token mint capability scoped to the single publish
  job; privileged publish job consumes no restorable cache state and
  verifies artifact integrity before publication.
- Research brief `docs/research-brief-gh118-pypi-hardening-2026-05-24.md`
  catalogued 12 of 13 acceptance items as DRIFT prior to this phase;
  IOC sweep returned clean (no `setup_bun.js`, `bun_environment.js`,
  or `transformers.pyz`). Cluster Phases 102 (P1) and 103 (P2) will
  close the remaining 8 items.

## [0.68.1] - 2026-05-24

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 100 (hotfix, F4)**: Critical Invariants summary blocks added
  to qor-audit and qor-substantiate SKILL.md files between `## Purpose`
  and `## Environment` sections. Each ~10-line block lists the
  inviolable ABORT/VETO contracts the skill cannot bypass:
  - qor-audit: 9 binding contracts (Step 0.3 plan-iteration ABORT;
    Step 3 Prompt Injection Pass ABORT; Step 3 L3/OWASP/Ghost-UI/Razor/
    self-application VETOs; Step 3 Test Functionality / Filter-Stage /
    Infrastructure Alignment / Feature Test Declaration VETOs). Block
    includes a V2 ramp note explicitly clarifying the Phase 99 Runtime
    Contract Walk is NEW at Step 3 but ships WARN-only (not yet a
    binding VETO; V2-of-V2 will flip the ramp).
  - qor-substantiate: 4 binding contracts (Step 4.6.* reliability
    gates; Step 6.5 README badge currency `|| ABORT`; Step 7.8
    gate-chain completeness `|| ABORT`; Constraints section at file
    foot).
  New `tests/test_governance_skills_carry_critical_invariants_block.py`
  (4 assertions) is the structural countermeasure: per-skill anchored
  positives + positional guard (block must precede Environment) +
  forward-only sweep using binding-gate syntax patterns (`-> VETO`,
  `-> ABORT`, `|| ABORT`, `**VETO**`, `**ABORT**`, `binding-VETO`,
  `binding VETO`) so any future governance skill carrying binding
  gates must also carry an invariants block. Closes the Tier 1
  prompt-surface cluster (Phases 96-100; meta-memo
  `docs/cluster-memo-prompt-surface-tier1-2026-05-23.md`).

## [0.68.0] - 2026-05-24

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 99 (feature, GH #108 full close)**: audit-side Runtime
  Contract Walk V2. Closes GH #108 fully (V1 recon-side probe shipped
  Phase 96; V2 audit-side walk ships now). New
  `qor.scripts.runtime_contract_walk.walk_plan(plan_path, repo_root) -> list[WalkFinding]`
  walks the import graph one hop in each direction for each Python
  module path cited in a plan being audited. Forward walk: cited
  module's own imports all parse via subprocess `python -c "import X"`.
  Backward walk: at least one production caller (non-test, non-scratch,
  non-doc) exists and parses cleanly with `ast.parse`. Wired into
  `/qor-audit` Step 3 Infrastructure Alignment Pass as a new sub-check
  after the existing grep-verify block. WARN-only ramp in V2 (CLI
  exits 0 by default; `--exit-on-any` opts into hard fail; audit-site
  invocation uses `|| true`) because no Phase 96 V1 operator evidence
  has accumulated in same-session cluster. A future V2-of-V2 phase
  will gather V1 evidence, tune walk thresholds, and convert to hard
  VETO with `runtime-contract-mismatch` category. `SG-GrepShapedRunclaim-A`
  doctrine entry's "V2 reserved" paragraph replaced with the shipped
  V2 implementation. Progressive disclosure: detailed two-direction
  protocol lives in `qor/references/audit-runtime-contract-walk.md`;
  qor-audit/SKILL.md gains only a one-paragraph summary + reference
  pointer.

## [0.67.2] - 2026-05-24

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Changed

- **Phase 98 (hotfix, F5+F6)**: meta-skill `## Examples` blocks moved
  out of inline SKILL.md prose into per-skill `references/` files per
  the progressive-disclosure doctrine (`SG-SkillCorpusGrowth-A`).
  `qor/skills/meta/qor-meta-log-decision/SKILL.md` Examples section
  (~90 lines: Architecture L2, Security L3, Scope Change L2) moved to
  `qor/skills/meta/qor-meta-log-decision/references/example-decision-entries.md`.
  `qor/skills/meta/qor-meta-track-shadow/SKILL.md` Examples section
  (~65 lines: Dependency Bloat SG-001, Premature Optimization SG-002,
  Hallucination SG-003) moved to
  `qor/skills/meta/qor-meta-track-shadow/references/example-shadow-genome-events.md`.
  Each SKILL.md retains a short pointer paragraph + reference link.
  No skill behavior change. New
  `tests/test_meta_skill_examples_progressive_disclosure.py` (6
  assertions) is the structural countermeasure preventing regression
  (pointer present, reference file exists, all three example IDs
  preserved per skill). Decision Point for the "stranded Entry #6
  fragment" at `qor-meta-log-decision/SKILL.md:437` closed during plan
  authoring: fragment is inside the `## Meta-Ledger File Structure`
  example code block (deliberate artifact-format documentation), not
  stranded; research brief misread the structure.

## [0.67.1] - 2026-05-23

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Changed

- **Phase 97 (hotfix, F8)**: SKILL_REGISTRY per-category drift
  reconciliation. `docs/SKILL_REGISTRY.md` declared 30 total skills
  which matched the actual total only by offset cancellation (sdlc
  undercounted by 1, meta undercounted by 1, memory internally
  consistent). A total-only currency test passed while two categories
  silently drifted. Reconciled: snapshot date 2026-04-29 → 2026-05-23;
  sdlc count 6 → 7 with `qor-ideate` row added; meta count 11 → 12
  with `qor-ab-run` row added; governance (6) and memory (7) unchanged
  (already correct). Actual total is 32 .md files across the four
  categories. New `tests/test_skill_registry_per_category_currency.py`
  (~140 LOC, 7 assertions) is the structural countermeasure: per-
  category currency checks for governance/sdlc/memory/meta plus
  inverse-drift sweep, cross-category drift guard, and arithmetic
  guard for any documented total. The per-category granularity
  prevents total-cancellation masking; F8 cannot recur the same way.
  CHANGELOG retroactively backfilled with v0.67.0 (Phase 96
  CHANGELOG omission caught by Phase 97's
  `test_every_tag_has_changelog_section`).

## [0.67.0] - 2026-05-23

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 96 (feature, GH #108 partial)**: recon reachability probe V1.
  Closes GH #108 partially by shipping a visibility-only detector for
  the grep-shaped-runclaim defect. New
  `qor.scripts.reachability_probe.check_claim(claim, repo_root, manifest_path)`
  runs five checks per cited surface: importability (subprocess import),
  test collection (pytest --collect-only against tests referencing the
  surface), caller graph (walk production .py files filtering out
  tests/.agent/.claude/.qor/docs), packaging (substring match against
  pyproject.toml or operator-passed manifest), interface match (AST
  parse of module signature vs regex parse of call-site invocation).
  Each failing check emits a `reachability-*-failed` / `-no-production-caller`
  / `-packaging-missing` / `-interface-mismatch` finding with
  `severity="warn"`. New `/qor-deep-audit-recon` Phase 3 Round 0
  (between after-synthesis checkpoint and existing Phase 3
  VERIFICATION) invokes the probe WARN-only. CLI exits 0 by default;
  `--exit-on-any` opts into CI-style enforcement. New
  `SG-GrepShapedRunclaim-A` doctrine entry carries the COREFORGE Phase
  371 originating recurrence verbatim. Detailed five-check protocol
  lives in `qor/references/recon-reachability-probe.md` (progressive
  disclosure per GH #92 doctrine). Opens the Tier 1 prompt-surface
  remediation cluster (meta-memo
  `docs/cluster-memo-prompt-surface-tier1-2026-05-23.md`). V2 (Phase
  99: `/qor-audit` Step 3 Runtime Contract Walk; binding VETO surface)
  reserved.

## [0.66.0] - 2026-05-23

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 95 (feature, GH #92)**: skill-corpus size-budget lint V1.
  Closes the meta process-finding from GH #92 (skill corpus tripled
  in 6 weeks; no consolidation counterweight). New
  `qor.scripts.skill_size_budget_lint.check_skills(skills_root)` walks
  `qor/skills/**/SKILL.md` and emits one finding per skill exceeding
  the per-skill size threshold: `skill-over-warn-threshold` at 25 KB
  and `skill-over-exceeded-threshold` at 40 KB. New `/qor-substantiate`
  Step 4.6.9 (between merge-velocity 4.6.8 and doc-integrity 4.7)
  invokes the lint WARN-only. CLI exits 1 when any EXCEEDED finding
  is present so V2 can convert to a hard ABORT. The lint catches the
  canonical Qor-logic corpus's own bloat at substantiate-time:
  `qor-audit` (44 KB) reports EXCEEDED, `qor-substantiate` (~40 KB)
  reports WARN — dogfooding the discipline the lint introduces. New
  `SG-SkillCorpusGrowth-A` doctrine entry catalogs the GH #92
  measurement table (91 KB → 282 KB in 6 weeks) and the reflective
  acknowledgement that the lint itself contributes to corpus growth.
  V2 (periodic consolidation cadence; historical-growth tracking;
  auto-refactor suggestions) reserved for a future phase.

## [0.65.0] - 2026-05-23

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 94 (feature, GH #90)**: inline workspace-fragility detector V1.
  Companion to Phase 93's macro merge-velocity check; where Phase 93
  looks BACKWARD at `origin/main`'s recent merge history at substantiate,
  Phase 94 looks at the LOCAL working tree FORWARD pre-merge. New
  `qor.scripts.workspace_fragility_check.assess_workspace_fragility(repo_root)`
  inspects five local signals: untracked file count, dirty gate
  artifacts (`.qor/gates/<sid>/` whose session lacks a SESSION SEAL),
  ledger chain-math failures (excluding Phase 91 grandfathered
  residuals), active local branch count, branch-diff size since
  divergence from `origin/main`. Three grades (`low` / `medium` /
  `high`) with deterministic action mapping (`merge_ok` /
  `narrow_scope` / `hardening_only`). New `/qor-audit` Step 0.6 SIXTH
  pre-audit lint line (after `ci_coverage_lint`). WARN-only V1; CLI
  exits 1 on `high` so V2 can convert to ABORT. Extends
  `SG-MergePaceThrottle-A` doctrine entry with an "Inline companion"
  sub-paragraph naming Phase 94's signals and the explicit framing
  of Phase 90's inline complement to Phase 89's macro throttle.
  Full suite: 1819 passed (+13).

## [0.64.0] - 2026-05-23

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 93 (feature, GH #89)**: merge-velocity throttle detector V1.
  New `qor.scripts.merge_velocity_check.assess_merge_velocity(repo_root,
  window_days, shared_core_paths)` walks `origin/main`'s recent merge
  history via `git log` (offline-safe; no GitHub API dependency) and
  computes a `VelocityAssessment` with three stabilization-capacity
  grades (`healthy` / `strained` / `exceeded`), a `recommended_action`
  string, and an evidence list naming the thresholds that fired. New
  `/qor-substantiate` Step 4.6.8 (between DoD check 4.6.7 and
  doc-integrity 4.7) invokes the detector WARN-only (CLI exits 1 on
  `exceeded`; `|| true` wrap swallows the non-zero in V1). V1
  thresholds: `strained` at `prs_merged_in_window >= 10` OR
  `repair_density >= 0.20`; `exceeded` at `prs_merged_in_window >= 20`
  AND (`repair_density >= 0.30` OR `shared_core_touch_count >= 10`).
  Repair-keyword classification covers `fix`, `hotfix`, `repair`,
  `regression`, `rollback`, `revert`. Operator-declarable shared-core
  paths via repeat `--shared-core-path` flag (no built-in patterns).
  New `SG-MergePaceThrottle-A` doctrine entry catalogs the Bicameral
  originating recurrence. V2 (enforcement, GitHub-API signals) reserved
  for a future phase.

## [0.63.0] - 2026-05-23

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 92 (feature, GH #86)**: explicit multi-tier Definition of Done
  as a first-class plan artifact. Every plan now declares per-deliverable
  D1 (vision/spec), D2 (code), D3 (governance), and D4 (empirical/
  runtime verification) acceptance criteria in a new `## Definition of
  Done` section between `## Phase N` and `## CI Commands`. D4 may be
  replaced with a `D4.d` waiver row carrying a rationale and a
  `**Follow-up phase**:` reference. New `qor.scripts.dod_record.parse_plan`
  reads the section into structured records; new
  `qor.scripts.dod_check.check_plan` runs at `/qor-substantiate` Step
  4.6.7 (new, between procedural-fidelity 4.6.6 and doc-integrity 4.7),
  emitting four finding categories — `missing-dod-section`,
  `deliverable-missing-tier`, `waiver-without-rationale`,
  `waiver-without-followup` — with V1 `severity="warn"`. WARN-only
  contract: findings surface in the seal report but do not abort
  substantiate. New `qor/references/doctrine-definition-of-done.md`
  doctrine file documents the four-tier contract and waiver protocol.
  New `SG-DoDImplicit-A` countermeasure-catalog entry. V1 enforces
  declaration presence; V2 (deferred) will verify D4's truth by
  cross-referencing named tests against pytest output. Bumps Doctrines
  badge 27 → 28.

## [0.62.0] - 2026-05-23

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 91 (feature, GH #85)**: `qor-logic verify-ledger` gains
  `--tolerate-known-grandfathered` and `--grandfather-cutoff` flags. The
  tolerance flag accepts chain-math failures iff the failing entries'
  `previous_hash` appears in the ledger's duplicate-`previous_hash` set
  AND the failing entry numbers are `<=` the cutoff (default 207,
  matching `check_previous_hash_uniqueness`'s `min_entry_num`). Lets
  consumer workspaces with SG-ConcurrentLedgerRace-A residuals (e.g.,
  the Accountable-App-3.0 case in GH #85) ship clean `verify-ledger`
  gates without rewriting past entries. Read-only verifier semantics —
  the ledger is not modified, so no operator-authorization protocol is
  needed in V1. Flag is OFF by default; strict verifier remains the
  canonical gate. Tolerated failures emit `DISCLOSED_GRANDFATHERED
  Entry #N` on stdout, do not contribute to the error count, and do not
  propagate TAINTED to downstream entries. New
  `find_grandfathered_entries(ledger_md, cutoff)` helper in
  `qor.scripts.ledger_hash`. Extends the `SG-ConcurrentLedgerRace-A`
  doctrine entry with a "V2 stopgap (Phase 91)" paragraph. Real
  reconciliation that writes new entries (Options A/B from GH #85)
  reserved for a future phase with operator-authorization protocol
  design. 13 new behavior tests including two canonical-ledger
  forward-only guards.

## [0.61.0] - 2026-05-23

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 90 (feature, GH #79)**: skills that invoke `python -m qor.reliability.*`
  or `python -m qor.scripts.*` gain (C) a WARN-only preflight one-liner at
  the top of their `## Execution Protocol` (or equivalent protocol-section)
  and (D) a new `## Environment` block documenting the install contract.
  The preflight surfaces module-misconfiguration once at skill entry —
  converting the Phase 75 silent-SKIP cascade into a visible WARN that
  operators can address (`pip show qor-logic`; `pipx install qor-logic`).
  WARN-only (not ABORT) so Phase 75 declarative-tolerance remains intact
  on legitimately non-Python hosts. Applied to 7 skills (qor-audit,
  qor-process-review-cycle, qor-shadow-process, qor-substantiate,
  qor-repo-audit, qor-implement, qor-plan). New
  `SG-SilentSkipMisconfig-A` doctrine entry; new
  `tests/test_skill_environment_block.py` (7 wiring assertions across
  affected skills) enforces forward-only structural discipline. V1 ships
  Options C + D from GH #79; Option A (CLI subcommand dispatch) and
  Option B (install-time path rewriting) reserved for a future phase.

## [0.60.0] - 2026-05-22

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 89 (feature, GH #91)**: `/qor-audit` Step 0.6 gains a fifth
  pre-audit lint, `qor.scripts.ci_coverage_lint`, that reconciles the
  plan's `## CI Commands` bullets against the Python-fingerprint `run:`
  steps discovered in `.github/workflows/*.yml`. Closes the COREFORGE-class
  credibility failure where a phase seals "all CI green" while a real
  GitHub Actions job — one the operator simply forgot to enumerate —
  would fail. WARN-only (parallels `plan_grep_lint` /
  `plan_text_consistency_lint` / `delivery_branch_lint`); tag-only
  workflows are skipped; environment-setup boilerplate is filtered.
  Plans may declare a `## CI Coverage Exemptions` block of substring
  patterns to justify pre-existing infrastructure CI not phase-relevant.
  A self-application test asserts Phase 89's own plan reports zero WARNs
  against this repo's actual workflows. Extends the
  `SG-CICoverageDrift-A` countermeasure catalog entry.

## [0.59.0] - 2026-05-22

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 88 (feature, GH #80)**: `/qor-research` gains a new Step 2.5
  issue-state pre-check. When the research target is an existing GitHub
  issue, the skill runs `gh pr list --state all --search "#<N>"` and
  `--search "in:body <N>"` before fresh research begins; if a MERGED PR
  closes the target, the skill surfaces it (number, state, mergedAt,
  title) to the operator. Saves the cycle when the work has already
  shipped from a different branch. Scope-conditional (only fires for
  existing-issue targets); skipped with a one-line note when `gh` is not
  on PATH or the target is not an issue. Wiring locked by anchored +
  strip-and-fail + scope-conditional substring tests at
  `tests/test_qor_research_issue_state_check.py`. Same prose pattern is
  recommended for the user-side `/qor-auto-dev-1` skill (which lives
  outside this repo's SSoT and is not sealed here).

## [0.58.0] - 2026-05-22

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 87 (feature, GH #82)**: `/qor-audit` now auto-dispatches the
  Option B independent reviewer when a plan exceeds an author-momentum risk
  threshold. New `qor.scripts.audit_risk_score` scores the plan under audit;
  when it reports `option_b_required: true` — a cited `*.config.*` file, or
  five or more grep-evidence citations to sealed infrastructure — `/qor-audit`
  Step 1 makes Option B (independent reviewer) mandatory for that audit,
  proactive on the iteration the risk first appears rather than
  operator-discretion dispatched after a VETO. Extends the Phase 68
  `SG-AuthorAuditMomentum-A` countermeasure.

## [0.57.2] - 2026-05-22

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed

- **Phase 86 (hotfix, GH #98)**: seal PRs no longer require an admin merge
  override on the release-publish check. `/qor-substantiate` previously
  pushed the annotated release tag together with the phase branch, before
  the seal commit was on `main`; `release.yml`'s `build-and-publish` job
  then refused to publish a tag whose commit is not reachable from
  `origin/main`, and that failing check blocked the seal PR. Tag creation
  stays at Step 9.5.5 (pre-merge); a new Step 9.7 pushes the tag only after
  the seal commit reaches `origin/main`, gated on the same
  `git merge-base --is-ancestor` check `release.yml` itself uses.

## [0.57.1] - 2026-05-22

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed

- **Phase 85 (hotfix, GH #96)**: three CI-health fixes. The
  `test_seal_commits_after_cutoff_have_full_canonical_trailer` test — red on
  `main` because the phase 82/83 seal commits were authored without the
  `Authored via [Qor-logic SDLC]` trailer line — now passes: the two
  historical commits are disclosed-grandfathered, a new
  `qor.scripts.attribution.message_has_full_trailer` predicate is the single
  source of truth for the full trailer, and a new `/qor-substantiate`
  Step 9.5.4 guard (`qor.scripts.seal_trailer_check`) ABORTs the seal if a
  seal commit lacks the full trailer, so the omission cannot recur. The
  `doc_integrity_drift_report` CLI, which re-walked the markdown tree once
  per glossary term (O(terms x files)), now materializes the corpus once —
  a ~75x reduction that brings it back well under the test timeout.

## [0.57.0] - 2026-05-22

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 84 (feature, GH #81 + #84)**: two pre-audit guards that stop a
  not-ready plan from wasting an audit cycle. **Pre-audit readiness
  short-circuit (#81)** — a new `plan_iteration_status_lint` detects a plan
  that declares itself not audit-ready (an `iteration` value of
  `draft` / `pre-audit`, an "Operator Decisions Required Before Audit"
  section, or an Open Questions bullet ending "Operator confirms before
  audit"); `/qor-audit` Step 0.3 runs it as a hard short-circuit and aborts
  before any adversarial pass, consuming no audit cycle. **Inverse-coverage
  discipline (#84)** — `plan_test_lint` now flags a plan that declares a
  closed-enum taxonomy (a `CANONICAL_*_VALUES` constant plus a `normalize*`
  function) with no inverse-coverage test; `/qor-plan` Step 5 and
  `/qor-audit` Step 3 Test Functionality Pass require both the forward
  round-trip and the inverse coverage assertion, and missing inverse
  coverage is a `coverage-gap` VETO. Adds the `SG-PreAuditDraftSubmission-A`
  and `SG-InverseCoverageGapTaxonomy-A` doctrine entries and the
  Inverse-coverage discipline section in `doctrine-test-functionality.md`.

## [0.56.0] - 2026-05-22

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 83 (feature, GH #83 + #87)**: the `/qor-audit` Phase 37
  Infrastructure Alignment Pass gains two sub-checks. **Citation
  consumer-trace** — every cited code symbol in a plan must be reachable from
  the entry-point surface the plan claims to fix; dead-code or wrong-symbol
  citations become an `infrastructure-mismatch` VETO. **Delivery-Branch
  Currency** — a new `delivery_branch_lint` pre-audit lint verifies a plan's
  declared `pr_target` branch still exists on the remote, and the audit
  prose directs an operator confirmation that it is still open for merges.
  Adds an optional `pr_target` field to the plan schema and the
  `SG-DeliveryBranchDrift-A` doctrine entry. Sub-pass procedures live in a
  new qor-audit reference file (progressive disclosure).

## [0.55.2] - 2026-05-22

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed

- **Phase 82 (hotfix, GH #88)**: `qor.reliability.seal_entry_check.check()`
  now runs its full-chain verification via `ledger_hash.verify_post_anchor()`
  instead of the strict `ledger_hash.verify()`. The strict verifier's
  Phase-66 taint propagation returned a permanent failure on any re-anchored
  ledger carrying disclosed pre-anchor failures, which made `/qor-substantiate`
  Step 7.7 abort a structurally valid SESSION SEAL. The post-anchor verifier
  tolerates pre-boundary failures and fails only on post-boundary breaks.

## [0.55.1] - 2026-05-15

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed

- **Phase 81 (hotfix, GH #77)**: `qor-governance-compliance` SKILL.md
  YAML frontmatter now carries the F244/FX359 provenance contract:
  `metadata.source.repository` (https URL to this repo) and
  `metadata.source.path`. Without these the FailSafe extension's
  `skill-provenance-schema.test.ts` walker fails on every machine
  where qor-logic has been installed; FailSafe's v5.1.0 release had
  to patch locally to ship. The source-of-truth fix flows to dist
  variants via `qor.scripts.dist_compile` and to installed copies on
  the next `qor-logic install`. 2 regression tests added.

  Out of scope: the companion `qor-compliance` skill referenced in
  GH #77 does not exist in this repo (no occurrence in `qor/skills/`,
  `qor/dist/`, or anywhere else); it is sourced from FailSafe's own
  skills bundle and must be filed upstream against FailSafe.

## [0.55.0] - 2026-05-15

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 80 (feature, GH #73)**: `/qor-bootstrap` scaffolds
  `docs/FEATURE_INDEX.md`. Closes the chicken-and-egg where newly-
  bootstrapped projects could not satisfy `/qor-implement` Step 12.5
  staging gate (the Phase 73 FEATURE_INDEX update obligation) on their
  first cycle because no file existed for the gate to verify.
  - New Step 6.6 inserted between Step 6.5 (Create Backlog) and Step 7
    (Calculate Genesis Hash) authors `docs/FEATURE_INDEX.md` from the
    canonical seed template.
  - Seed template includes title with `{project_name}` placeholder,
    purpose paragraph naming Phase 73 obligation, Coverage Summary
    block (0/0/0/0 placeholders), one placeholder Section with the
    canonical 7-column table header (`ID | Feature | Doc | Code | Test
    | Status | Notes`), and a Gaps Surfaced placeholder block.
  - Success Criteria updated to include the seed scaffold bullet.
  - 1 new glossary term: `FEATURE_INDEX.md genesis seed`.
  - 4 new tests across 3 files.

  V2 follow-on: mechanical `/qor-implement` Step 10.6 lint comparing
  plan `Feature Inventory Touches` declarations against shipped
  FEATURE_INDEX.md rows deferred (per GH #73 bonus suggestion).

## [0.54.0] - 2026-05-15

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 79 (feature, GH #52)**: `/qor-implement` Step 8.5 Documentation
  Sync. Inserts a new step between Step 8 (Post-Build Cleanup) and Step 9
  (Complexity Self-Check) that authors ARCHITECTURE_PLAN.md file tree +
  architecture / operations / schema docs in the same commit batch as the
  implementation, while context is fresh. Closes the gap where the
  authoring lifecycle was structurally deferred to `/qor-substantiate`
  Steps 4.7 / 6 / 6.5, by which time the implementing agent had already
  discarded the context needed for accurate docs.
  - 4-item checklist covering ARCHITECTURE_PLAN.md file tree;
    architecture docs (interface contracts, data flows, dependency
    tables); operations docs (scripts, env vars, deployment steps);
    schema docs (migrations, RLS policies, function signatures).
  - `doc_tier`-aware skip semantics: minimal -> WARN-skip; standard
    -> require file tree + architecture docs; system -> require all
    4 surfaces; legacy -> skip.
  - Cross-references to `/qor-substantiate` Steps 4.7 / 6 / 6.5 /
    4.6.6 as the downstream verification gates; substantiation
    behavior unchanged.
  - SG-DocsBackloadedToSubstantiate-A doctrine entry with originating
    recurrence (18+ ledger entries in a multi-session analytics
    program where ARCHITECTURE_PLAN.md file tree went stale and new
    tables/functions/migrations had no architecture-doc updates).
  - 2 new glossary terms: `implement documentation sync`,
    `SG-DocsBackloadedToSubstantiate-A`.
  - 6 new tests across 3 files. V2 follow-on: mechanical
    `qor/scripts/plan_doc_sync_lint.py` comparing implement
    `files_touched` against doc-surface diffs in the same commit
    deferred pending V1 adoption.

## [0.53.0] - 2026-05-15

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 78 (feature, GH #47)**: `/qor-audit` Step 3 Filter-Stage
  Ordering Coherence sub-pass. V1 prose-only audit-pass extension
  (matches Phase 73/74 pattern). Catches the COREFORGE-class
  composition defect where stage-by-stage review passes each filter
  individually but the validator that enforces an upstream invariant
  runs elsewhere instead of as the first stage of the pipeline.
  - New sub-pass under Step 3 names the 4-step procedure
    (preconditions / invariants / dependency graph / topological
    sort) and the heuristic for detecting pipeline-shaped functions
    across Rust / Python / TypeScript.
  - VETO sub-tag `filter-order-inversion` under existing `composition`
    category (or `infrastructure-mismatch` when the missing
    precondition is an external-state assumption). No schema enum
    change.
  - SG-FilterOrderInversion-A doctrine entry with originating
    recurrence (COREFORGE Skill-Forge V1 dispatcher META_LEDGER #209;
    operator-caught at PR #82 merge commit `0999e47`).
  - 3 new glossary terms: `pipeline stage dependency graph`,
    `filter-stage ordering coherence`, `SG-FilterOrderInversion-A`.
  - 6 new tests across 3 files. V2 follow-on: mechanical
    `qor/scripts/plan_filter_stage_lint.py` AST helper deferred
    pending operator demand from V1 deployment.

## [0.52.0] - 2026-05-14

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 76 (feature, GH #51, L3 high_risk_target)**: META_LEDGER
  federation entry IDs + duplicate detection V1 (forward-only;
  retroactive renumbering of past entries explicitly forbidden).
  - New `qor/scripts/entry_id.py` provides `derive_entry_id(ts, phase,
    content_hash, length=12)` returning a content-addressable hex ID
    (SHA256[:12] = 48 bits collision-resistant). Env
    `QOR_ENTRY_ID_FULL_HASH=1` switches to 64-char full-hash mode.
  - `qor.reliability.seal_entry_check.check_previous_hash_uniqueness(
    ledger_path, min_entry_num=207)` detects the concurrent-append
    race signature (two entries claiming the same previous_hash).
    Forward-only: past entries < min_entry_num are grandfathered.
  - `/qor-substantiate` Step 7 prose requires new entries carry an
    `**Entry ID**:` body line. Step 7.7 invokes the uniqueness check.
  - SG-ConcurrentLedgerRace-A doctrine entry with originating
    recurrence (cross-workspace #16a/b, #17a/b, #18a/b + canonical
    #109/#111/#113) and explicit prohibition of retroactive renumber.
  - 2 new glossary terms: `content-addressable entry ID`,
    `SG-ConcurrentLedgerRace-A`.
  - 10 new tests across 4 files. EU AI Act Art. 9 impact_assessment
    block populated for L3 plan.
  - V2 follow-on: operator-authorized one-time reconciliation pass
    for past duplicate-previous_hash entries (forward-only commit
    format; never history-rewrite).

## [0.51.0] - 2026-05-14

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 75 (feature, GH #38)**: Skill capability declaration for
  `/qor-substantiate` (V1 -- Option 1 from issue body; pluggable backends
  and two-track split deferred to V2/V3).
  - New `qor/scripts/substantiate_capability.py` (~110 LOC, pure-function)
    parses qor-substantiate SKILL.md `## Step Prerequisites` table and
    returns per-step CapabilityReport (PRESENT/ABSENT + evidence).
    Predicate kinds: `file:<path>`, `module:<dotted>`, `command:<binary>`.
  - New `qor-logic substantiate-capability` CLI prints a markdown table
    (4 columns: Step / Requires / Present / Evidence) paste-able into
    the SESSION SEAL entry body.
  - `qor-substantiate` SKILL.md gains `## Step Prerequisites` table with
    12 V1 declarations. Each affected step body cross-references the
    table with a `Prerequisite (Phase 75; GH #38)` callout.
  - `qor/gates/schema/shadow_event.schema.json` `event_type` enum gains
    `gate_skipped_prerequisite_absent` (severity 1 default).
  - SG-HalfSealedClaim-A doctrine entry catalogues the half-checked-seal
    pattern with 2026-05-06 originating recurrence.
  - 3 new glossary terms; 12 new tests across 5 files.
  - V2/V3 follow-on: pluggable backends, two-track skill split.

## [0.50.0] - 2026-05-14

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 74 (feature, GH #49 + #58)**: qor-audit pass extensions
  (prose-only V1; mechanical lint helper deferred to V2).
  - `/qor-audit` Step 3 **Infrastructure Alignment Pass** gains a sixth
    checklist bullet covering third-party SDK citations + behavioral-
    semantics claims. Every cited third-party SDK method/property must
    exist in installed type declarations (node_modules/<pkg>/dist/*.d.ts;
    pip-show inspection; Cargo.toml + cargo doc) OR be quoted from
    official documentation with citation. Every cited behavioral-
    semantics claim (Postgres durability/concurrency/transaction
    semantics, lock lifecycle, trigger side-effects, supabase-js method
    behavior, auth-schema mutability) must include inline citation to
    upstream docs (URL + quoted text), upstream source (file:line), or
    in-repo precedent. Closes SG-006 + SG-010 hallucination classes.
    VETO category unchanged (`infrastructure-mismatch`).
  - `/qor-audit` Step 3 **Ghost UI Pass** gains a Live-Progress Invariant
    sub-rule with 4 checklist items: intermediate state when backing op
    takes >2s; no fake-jump (0% -> 100% with no intermediate writes);
    modals subscribe to backing event stream and re-render; error UI
    surfaces explicit dismiss/retry control. Sub-tag
    `live-progress-fake` under existing `ghost-ui` VETO category.
  - `qor/references/doctrine-shadow-genome-countermeasures.md`
    SG-FakeProgress-A catalogues the pattern + originating recurrence
    (FailSafe v5.1.0 Install QorLogic Skills card) + countermeasure.
  - 4 new glossary terms: third-party SDK citation,
    behavioral-semantics claim, Live-Progress Invariant, SG-FakeProgress-A.
  - 6 new tests across 3 files (audit prose + doctrine prose).
  - V2 follow-on: mechanical `qor/scripts/plan_live_progress_lint.py`
    heuristic at Step 0.6 pre-audit lint surface queued.

## [0.49.0] - 2026-05-14

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 73 (feature, GH #40 + #41)**: Feature Inventory artifact +
  per-feature TDD-Light contract (V1 prose + schema; runtime helpers
  deferred to V2).
  - New doctrine `qor/references/doctrine-feature-inventory.md` documents
    the FEATURE_INDEX.md artifact format (6-column markdown table),
    status enum (`verified | unverified | n/a`), lifecycle hooks
    (`/qor-implement` Step 12.5 append/update; `/qor-substantiate`
    Step 6 verify + count surface), and the V2 ABORT-on-regression contract.
  - New doctrine `qor/references/doctrine-feature-tdd.md` documents the
    three-gate upstream contract (`/qor-plan` Step 5 Feature Inventory
    Touches declaration; `/qor-audit` Step 3 Feature Test Coverage Pass
    with VETO category `feature-test-undeclared`; `/qor-implement` Step 5
    per-feature failing-test-first) and the SG-035 acceptance question
    inheritance at feature scope.
  - `qor/gates/schema/plan.schema.json` gains optional
    `feature_inventory_touches` array field with `entry_id`, `operation`
    (NEW/MODIFIED/n/a-justified), `test_path`, `test_descriptor`.
  - `qor/gates/schema/audit.schema.json` `findings_categories` enum
    gains `feature-test-undeclared`.
  - 4 new glossary terms: `Feature Inventory`, `Feature Inventory Touches`,
    `per-feature TDD`, `feature-test-undeclared`.
  - SKILL prose updates: `/qor-plan` Step 5; `/qor-audit` Step 3 Feature
    Test Coverage Pass; `/qor-implement` Step 5 per-feature TDD layer +
    Step 12.5 FEATURE_INDEX update obligation; `/qor-substantiate` Step 6
    FEATURE_INDEX verification pass with count surface in seal entry.
  - 15 new tests across 7 files (doctrine prose, schema validation,
    SKILL prose).
  - Source incident: FailSafe v5 2026-05-06 -> 264-feature retroactive
    test marathon. V2 follow-on (runtime parser/verifier + ABORT helper)
    queued.

## [0.48.0] - 2026-05-14

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 72 (feature, GH #56)**: SG-CitationDrift-A cross-iteration citation
  drift countermeasure (P1 + P2 prose + doctrine).
  - `/qor-plan` Step 2 gains an **Infrastructure Citation Inventory**
    sub-section requiring every Locked Decision citing sealed infrastructure
    (migration name, function signature, file:line, schema, env var,
    edge-function path) to carry a paired grep-evidence statement of the
    canonical form `git show <sealed-ref>:<path> | grep -nE '<pattern>' ->
    <exact observed text>`. Citations without paired evidence are Open
    Questions, not Locked Decisions, and block submission to `/qor-audit`.
  - `/qor-audit` Step 3 Infrastructure Alignment Pass gains an iter-N>1
    sub-section: on iterations after the first, the Judge re-walks the
    **full** Locked Decision set (not the diff-from-iter-N-1) and
    grep-verifies every sealed-infrastructure citation. Missing inline
    grep-evidence triggers immediate VETO with `infrastructure-mismatch`
    category, regardless of whether the LD was amended this iteration.
  - `qor/references/doctrine-shadow-genome-countermeasures.md` SG-CitationDrift-A
    catalogues the pattern, originating recurrence, and P1+P2 countermeasures.
  - 8 new tests across 3 files (`test_qor_plan_infrastructure_citation_inventory`,
    `test_qor_audit_full_citation_rewalk`, `test_doctrine_sg_citation_drift_a`).
  - Lint-extension complement (P4 - heuristic plan_grep_lint hook for
    sealed-infrastructure citation patterns) deferred to a future phase.

## [0.47.3] - 2026-05-14

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 69 (hotfix, GH #43)**: cycle_count_escalator session-total signature mode.
  - New `qor/scripts/stall_walk.count_session_signature_totals(session_id)`
    aggregates per-signature VETO counts across the entire session audit
    history (non-consecutive, ignores PASS / LEGACY / implement breaks).
  - New `qor/scripts/cycle_count_escalator.check_session_total(session_id)`
    returns `EscalationRecommendation(escalation_reason="session-total", ...)`
    when any signature reaches K=3 cumulative. Runs alongside the existing
    consecutive-streak `check`; both modes can fire independently.
  - `/qor-plan` Step 2c + `/qor-audit` Step 0.5 + doctrine §10.4 all updated
    to invoke and document the new mode.
  - 11 new tests across 2 files.

## [0.47.2] - 2026-05-14

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 68 (hotfix, GH #44 + #50)**: qor-audit self-application + Option B codification.
  - `/qor-audit` Step 3 gains Self-Application Sub-Pass: when plan declares
    `originating_remediation`, auditor manually applies the to-be-introduced
    discipline against the plan's own content. VETO category:
    `specification-drift`. Closes the temporal gap between proposing a
    discipline and the discipline becoming runnable.
  - `/qor-audit` Step 1.a gains Option B codification: the independent
    reviewer pattern (per SG-007 / SG-AuthorAuditMomentum-A) is now in the
    skill prompt with dispatch options (fresh-context audit /
    architect-reviewer subagent / second operator).
  - `qor/gates/schema/plan.schema.json` declares optional
    `originating_remediation` field.
  - Doctrine `SG-AuthorAuditMomentum-A` promoted from SG-007 narrative.
  - 9 new tests across 3 files.

## [0.47.1] - 2026-05-14

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 67 (hotfix, GH #42 + #45)**: pre-audit lint wiring + audit short-circuit.
  - `plan_text_consistency_lint` wired into `/qor-audit` Step 0.6 (third lint
    alongside plan_test_lint + plan_grep_lint) and `/qor-plan` Step 5 review
    checklist. The lint detects same-operation drift across plan sites
    (commands, dependencies, paths) per the COREFORGE-class pattern.
  - Doctrine `SG-PlanTextDrift-A` catalogued in
    `doctrine-shadow-genome-countermeasures.md`.
  - `qor.scripts.qor_audit_runtime.check_unchanged_plan_short_circuit()`
    helper detects byte-identical re-invocation against prior audit's
    `target_content_hash`; `/qor-audit` Step 0.4 surfaces the prior verdict
    instead of consuming a new audit cycle.
  - `audit.schema.json` gains optional `target_content_hash` field
    (pre-Phase-67 audits without the field gracefully bypass short-circuit).
  - 8 new tests across 2 files.

## [0.47.0] - 2026-05-14

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- **Phase 66 (feature, GH #54 + #55)**: qor-validate integrity bundle.
  - `qor/scripts/ledger_hash.py` gains `SESSION_SEAL_RE` for Session Seal
    markup recognition, `is_placeholder_pattern()` detector
    (ascending-hex / repeating-bigram / FailSafe-class / low-entropy
    heuristics; all-zeros genesis convention exempted), and
    `verify_post_anchor()` mode with auto-detected or operator-pinned
    boundary.
  - `verify()` extended with taint propagation: downstream entries after
    a FAIL are reported as `TAINTED Entry #N: depends on failed
    predecessor #M` regardless of their own chain math.
  - `qor-logic verify-ledger` CLI gains `--ledger PATH`, `--post-anchor`,
    and `--boundary N` flags. Backward compatible: bare invocation
    unchanged.
  - `qor/skills/governance/qor-validate/SKILL.md` gains Step 4.5 (Mode
    Selection); stale `qor-logic verify-ledger docs/META_LEDGER.md`
    path-arg references removed; source URL corrected to
    `MythologIQ-Labs-LLC/Qor-logic`.
  - `qor/references/doctrine-governance-enforcement.md` §14 documents
    the post-anchor invariant.
  - 3 new glossary terms: `TAINTED entry`, `DISCLOSED_PRE_ANCHOR`,
    `post-anchor boundary`.
  - 30 new tests across 6 files; 5 pre-existing test files refactored
    from synthetic 64-char fixtures to real `hashlib.sha256` digests
    (the placeholder detector was correctly flagging them).

## [0.46.2] - 2026-05-14

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Fixed

- **GH #57**: `/qor-substantiate` template's "Next Session" line at
  `qor/skills/governance/qor-substantiate/references/qor-substantiate-templates.md:140`
  was recommending `/qor-bootstrap for new feature`, which misroutes operators
  on already-bootstrapped projects (`/qor-bootstrap` is genesis-only). Replaced
  with `/qor-ideate for a new concept or /qor-plan for implementation planning;
  /qor-status to review prior work`. Dist variants regenerated.
- **GH #53**: `kilo-code` host filesystem base changed from `.kilo-code` to
  `.kilo` in `qor/hosts.py:68` to match the Kilo tool's actual config directory.
  The logical host identifier `kilo-code` is preserved (no command-line
  breakage); only the on-disk install destination moves. Operators with prior
  `.kilo-code/` installs should re-run `qor-logic install --host kilo-code`.

## [0.46.1] - 2026-05-14

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- Phase 64 (hotfix): Seal Hash Integrity Gate at `/qor-substantiate` Step 6.8
  wires the existing `qor.scripts.hash_guard` helpers (`require_toolkit_modules`,
  `validate_sha256`) into the substantiate skill prose. Fail-closed gate
  validates `merkle_seal`, `content_hash`, `previous_hash`, and `chain_hash`
  before any digest enters the SESSION SEAL entry body. Step 6.8 carries a
  Preparation paragraph naming the canonical hash-producing helpers
  (`hash_guard.hash_file`, `ledger_hash.content_hash`, `ledger_hash.chain_hash`).
  Closes GH #48 (CRITICAL: substantiate produced fabricated patterned-hex
  strings in non-Python repos). Lands the Phase 59 Phase 2 work that was
  dropped during the Phase 60 session-consolidation commit.
- Doctrine `qor/references/doctrine-governance-enforcement.md` §13 documents
  the gate contract (toolkit modules, four validated labels, ABORT remediation
  guidance, OWASP LLM06 / NIST AI RMF MAP-3.1 / EU AI Act Art. 12 mapping).
- Operations runbook (`docs/operations.md`) gains three Phase 64 troubleshooting
  rows covering `ValueError` from `validate_sha256`, `RuntimeError` from
  `require_toolkit_modules`, and the pre-Phase-64 `ModuleNotFoundError` from
  the bare `doc_integrity_strict` import.

### Fixed

- `qor/scripts/doc_integrity.py:218` strict-mode import: bare
  `import doc_integrity_strict` -> package form
  `from qor.scripts import doc_integrity_strict`. Pre-Phase-31 bug that left
  `/qor-substantiate` Step 4.7 (strict-mode documentation integrity check)
  crashing with `ModuleNotFoundError` whenever the active working directory
  did not include `qor/scripts/` on `sys.path`. Regression locked by
  `tests/test_doc_integrity_strict_import.py` (three tests: runtime check,
  lenient-mode isolation, source invariant).
- `qor/references/glossary.md` `referenced_by` drift surfaced by the
  doc_integrity strict-mode fix: four pre-existing latent gaps patched
  (Gate x qor-ideate + doctrine-governance-enforcement; Substantiate x
  doctrine-procedural-fidelity; doc-surface coverage x qor-substantiate;
  ideation phase x qor-help; problem frame x qor-help). All edits document
  existing reality.

## [0.46.0] - 2026-05-11

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added

- Phase 63 session reconciliation: consolidated 17 session-side phases
  (originally numbered Phase 45-61 + Phase 59 / Phase 60 hotfixes) onto
  upstream's Phase 59 baseline as a single consolidated feature commit.
- Prompt compiler package (`qor/compiler/`) with PromptIR, ProviderCompiler
  protocol, AnthropicCompiler, governance gate, rulepack registry,
  execution modes, evaluation loop, and intent parser.
- Capability surface package (`qor/capabilities/`) with KNOWN_CAPABILITIES
  inventory, governance context packet builder, risk routing, and
  verification-request artifact emitter.
- `qor/scripts/path_match.py` — unified asymmetric path-prefix boundary matcher.
- `qor/scripts/audit_triggers.py` — structured adversarial-review trigger registry.
- `qor/scripts/hash_guard.py` — strict SHA-256 validation with placeholder rejection.
- `qor/scripts/ledger_entry_id.py` — federated entry UID generation (`le_<16hex>`).
- `qor/scripts/ledger_fragment.py` — ledger entry canonicalization helpers.
- `qor/scripts/meta_ledger_walker.py` — structured META_LEDGER traversal.
- `qor/scripts/host_capability.py` — host-capability declarations.
- `qor/scripts/pipeline_inversion_lint.py` — filter-stage ordering lint.
- `qor/scripts/plan_text_consistency_lint.py` — plan-text consistency lint.
- `qor/scripts/feature_index_verify.py` — feature-index integrity helper.
- 4 new doctrine documents: feature-inventory, feature-tdd, host-repo-posture,
  prompt-compilation.
- 5 new gate schemas: capability_inventory, feature_index, governance_context,
  risk_routing, verification_request.
- 18 session plan documents (Phase 45-63) and 2 roadmap docs preserved
  under `docs/` for historical reference.
- `qor capabilities {inventory,context,route-risk,verification-request}`
  CLI subcommand.
- ~50 functionality tests for the imported source surfaces.

### Changed

- `qor/cli.py` extended with the capabilities subcommand (additive only;
  upstream's qor-logic rename + release/compliance/policy subcommands preserved).
- `archive/session-2026-05-09` branch preserves the original 17-phase
  session commit history for forensic reference.
- Session-side governance edits to qor-audit / qor-substantiate /
  qor-implement / qor-plan / qor-debug SKILL.md and to existing doctrines
  (governance-enforcement, documentation-integrity, shadow-genome-countermeasures)
  were intentionally NOT replayed; upstream's parallel evolution of those
  surfaces (Phases 45-58) is canonical. Only the session's unique
  source-code deliverables and accompanying tests are consolidated here.
  The META_LEDGER chain between session entries #148-164 (sealed
  2026-05-09 through 2026-05-11) and this entry has been intentionally
  rewritten; the new chain anchors at upstream's Entry #195 (Phase 59
  ideate seal). See doctrine §10.10 "Session reconciliation protocol"
  for the governance rationale.

## [0.45.0] - 2026-05-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 59: `/qor-ideate` governed ideation readiness phase. Closes Issue #20 (originally catalogued as "future concept"). New optional pre-research SDLC phase that converts a raw concept into a structured artifact before research and planning, capturing intent and assumptions before they become inferred by downstream agents. Codifies `SG-PrematureSolutioning-A` countermeasure.

### Added
- **`/qor-ideate` skill** (`qor/skills/sdlc/qor-ideate/SKILL.md`): 10-section ideation dialogue protocol — Spark Record / Problem Frame / Transformation Statement / Assumption Ledger / Scope Boundary Record / Concept Brief / Options Matrix / Governance Profile / Failure Remediation Plan / Readiness Scoring + Routing. Skill REFUSES to advance past Section 2 (Problem Frame) without all 3 fields populated (anti-pattern guard for premature solutioning) and past Section 7 (Options Matrix) without ≥2 options compared.
- **`qor/skills/sdlc/qor-ideate/references/dialogue-protocol.md`**: section-by-section operator prompts.
- **`qor/gates/schema/ideation.schema.json`**: gate artifact schema with required top-level fields (`spark`, `problem_frame`, `transformation_statement`, `boundaries`, `governance_profile`, `readiness`, `ai_provenance`) + optional fields (`assumptions[]`, `options[]`, `failure_remediation[]`). Closed enums: `readiness.status` (ready/blocked/research_required/planning_advisory_only), `governance_profile.risk_grade` (L1/L2/L3/L4), `failure_remediation[].return_phase` (ideation/research/plan/audit/implement/remediate/substantiate).
- **`gate_chain.check_prior_artifact` extension**: recognizes `ideation.json` as a valid predecessor for both `/qor-research` and `/qor-plan` phases via new `_check_ideation_predecessor` helper. Backward-compatible: research with no prior still passes (legacy); plan with neither research nor ideation still reports prior missing.
- **`qor/scripts/validate_gate_artifact.py`**: `PHASES` tuple extended with `"ideation"` (matches Phase 55 `"deliver"` pattern).
- **`qor/gates/delegation-table.md`**: 5 new rows for `qor-ideate` routing (ready+research/ready+plan/research_required/blocked/planning_advisory_only).
- **`qor/gates/chain.md`**: chain visualization extended with `(ideate?)` as optional pre-research phase.
- **`qor/references/doctrine-ideation-readiness.md`** (NEW): 10-section catalog + readiness scoring model + routing decision matrix + 8-failure-mode catalog (Premature Solutioning, Language Drift, Assumption Laundering, Scope Seepage, Research Asymmetry, Failure Blindness, Premature Decomposition, Validation Collapse) + hotfix exemption + relationship to qor-research/qor-plan/qor-remediate.
- **`SG-PrematureSolutioning-A`** in `qor/references/doctrine-shadow-genome-countermeasures.md`: codifies the canonical failure pattern with Section 2 + Section 7 structural guards.
- **6 new glossary terms**: `ideation phase`, `spark record`, `problem frame`, `transformation statement`, `assumption ledger`, `ideation readiness`.
- **15 new tests** including schema validation (12 cases incl. enum-rejection + required-field), doctrine round-trip integrity, /qor-ideate skill admission, handoff matrix, predecessor recognition (research + plan), end-to-end gate artifact write, schema-validated round-trip.

### Changed
- `pyproject.toml` → 0.45.0.

## [0.44.0] - 2026-05-02

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 58: procedural-fidelity check at `/qor-substantiate` Step 4.6.6 + SYSTEM_STATE.md backfill (13 phases) + drift-prevention test + test-session pollution cleanup + Phase 58→59 ideation plan rename. Closes B23 (operator request from Phase 57 substantiate cycle where doc-surface gaps were caught manually rather than structurally). Codifies `SG-DocSurfaceUncovered-A` countermeasure.

### Added
- **procedural_fidelity module** (`qor/scripts/procedural_fidelity.py`, ~190 LOC, zero new deps): frozen `Deviation` dataclass; `DEVIATION_CLASSES` frozenset with four v1 classes (`doc-surface-uncovered` active, `missing-step` / `ordering-drift` / `argv-shape-divergence` stubs reserved); `check_seal_commit(repo_root, session_id)` reads implement gate's `files_touched` and runs all detectors; `to_findings_json` for downstream tooling; CLI `python -m qor.scripts.procedural_fidelity --session SID [--repo-root .] [--out PATH]`.
- **substantiate Step 4.6.6 wiring** (`qor/skills/governance/qor-substantiate/SKILL.md`): WARN-only invocation between Step 4.6.5 (Phase 56 secret-scan) and Step 4.7 (Phase 28 doc-integrity). Severity-2 deviations append to Process Shadow Genome; substantiate does NOT abort.
- **Doc-surface coverage rule**: skill / script / doctrine / schema changes require at-least-one update to `docs/SYSTEM_STATE.md`, `docs/operations.md`, `docs/architecture.md`, or `docs/lifecycle.md`. Threshold-based; operator-overridable with documented rationale.
- **SYSTEM_STATE.md drift-prevention test** (`tests/test_system_state_phase_coverage.py`): forward-only enforcement that every META_LEDGER `Phase N feature substantiated` entry has a corresponding `## Phase N (vX.Y.Z)` heading in SYSTEM_STATE.md.
- **SYSTEM_STATE.md backfill**: 12 sealed phases (41, 45, 46, 47, 48, 49, 50, 52, 53, 54, 55, 56) that had accumulated drift pre-Phase-58 now have entries.
- **conftest.py session-scope cleanup**: autouse fixture sweeps `.qor/gates/test*` directories at session-end to prevent test pollution from synthetic session IDs (`test-session`, `cli-test`, `t1`-`t9`).
- **`qor/references/doctrine-procedural-fidelity.md`** (NEW, ~95 LOC): applicability + four-class catalog + doc-surface coverage rule + operator workflow + Phase 58 changes vs. ad-hoc operator review + future extensions.
- **`SG-DocSurfaceUncovered-A`** in `qor/references/doctrine-shadow-genome-countermeasures.md` codifying the documentation-update gap risk class with Phase 57 source incident + Phase 58 countermeasure.
- **3 new glossary terms**: `procedural-fidelity check`, `procedural deviation`, `doc-surface coverage`.
- **9 new test files** including AST-anchored substantiate-skill wiring invariant and meta-coherence dogfood.

### Changed
- `pyproject.toml` → 0.44.0.
- `docs/plan-qor-phase58-ideation-readiness-phase.md` → `docs/plan-qor-phase59-ideation-readiness-phase.md` (Issue #20 ideation moves to Phase 59 since Phase 58 slot reassigned to tech-debt wrap-up). Plan body Phase 58 → Phase 59 references updated.
- `docs/BACKLOG.md` B23 marked `[x] (v0.44.0 — Complete)`.

## [0.43.0] - 2026-05-01

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 57: `gate_written` observer push-channel. Closes PR #12 (FailSafe-Pro B24 contribution, opened 2026-04-20) by reintegrating the hook contract on top of current main with the OWASP A04 SIGINT-swallow VETO ground resolved. Net-new public-API surface: `qor_logic.events.gate_written` entry-point group + `<root>/.qor/hooks.yaml` config-file format + frozen `GateWrittenEvent` payload. Hook channel is non-authoritative observer-only; the authoritative gate-write path is unchanged.

### Added
- **gate_hooks dispatcher** (`qor/scripts/gate_hooks.py`, ~165 LOC, zero new runtime deps): frozen `GateWrittenEvent` and `_HookTarget` dataclasses; `dispatch_gate_written` synchronous fan-out over entry-points + config-file hooks; `reload_entry_points` (test-only cache invalidator); JSONL hook-log at `<root>/.qor/hooks/hooks.log`. `except Exception` (NOT `BaseException`) — `KeyboardInterrupt` and `SystemExit` propagate.
- **gate_chain post-write hook fire** (`qor/scripts/gate_chain.py:_fire_gate_written_hook`): runs after Phase 52 provenance check + authoritative `vga.write_artifact` + Phase 37 `audit_history.append`. Reads artifact bytes back from disk to compute `payload_sha256` so the event matches what's persisted. Wrapped in `try/except Exception` so hook errors never break the write.
- **Hook-contract doctrine** (`qor/references/doctrine-hook-contract.md`): event payload, entry-point + config-file registration, invocation order, log format, trust model, performance characteristics, Phase 57 changes vs. PR #12 origin (the `except BaseException` → `except Exception` fix and SIGINT-propagation invariant).
- **Shadow-genome countermeasure** `SG-BareExceptionSwallowsSignals-A` (`qor/references/doctrine-shadow-genome-countermeasures.md`): codifies the BaseException-swallowing risk class with the corrected Exception catch + cleanup-then-reraise patterns.
- **Glossary terms**: `gate_written hook`, `hook contract`.
- **22 new tests** (Phase 1: 4 event-payload-shape + 5 dispatch + 3 swallow + 2 sigint-propagate + 6 config-file + 2 no-hooks-file; Phase 2: 2 fires-hook + 2 hook-does-not-break-write + 1 phase-52-still-enforced + 1 AST-based co-occurrence invariant). All behavior-asserting; no presence-only patterns.

### Changed
- `pyproject.toml` → 0.43.0.
- `README.md` → Tests delta, Ledger delta.
- META_LEDGER entries #186 (PR #12 audit VETO), #187 (Phase 57 plan audit PASS), #189 (implementation), #190 (session seal).

### Fixed
- PR #12 `feat/b24-gate-written-hooks` SIGINT-swallow: superseded by Phase 57. The PR's API surface (entry-point group, config-file format, GateWrittenEvent payload, swallow-log error semantics) is preserved exactly. The PR's BaseException catch is replaced by `except Exception` per Phase 57 audit verdict (Entry #186 VETO). B24 backlog item from FailSafe-Pro upstream now resolved at the qor-logic side of the contract; the FailSafe-Pro `failsafe-qor-hook` consumer in their B24 PR registers under `qor_logic.events.gate_written` and observes governance writes without filesystem polling.

## [0.42.0] - 2026-05-01

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 56: secret-scanning gate at `/qor-substantiate` Step 4.6.5. Closes OWASP LLM Top 10 (2025) **LLM06 Sensitive Information Disclosure** + **NIST AI 600-1 §2.10** at the substantiate-time enforcement layer. Drives the long-dormant Cedar `has_hardcoded_secrets` attribute (rule on books since Phase 23 with no scanner). Final phase of the five-phase compliance sprint; all six framework gaps from `docs/research-brief-prompt-logic-frameworks-2026-04-30.md` now closed (5/5 + LLM06 extension).

### Added
- **Secret-scanner module** (`qor/scripts/secret_scanner.py`, 248 LOC, zero new deps): frozen `Pattern` and `Finding` dataclasses; 11-pattern catalog (aws-access-key, github-pat-classic/finegrained/oauth, private-key-header, stripe-live, slack-token, google-api-key, anthropic-key, generic-high-entropy-assignment, private-key-url); 15-entry `_ALLOWLIST` frozenset (Cedar/schema attribute names + AWS docs sample + redaction sentinels + per-line `noqa: secret-scan` opt-out); `scan(path)` with auto-mask for `.md` suffix; `scan_paths`, `scan_staged`, `scan_text`, `to_gitleaks_json`, `mask_code_blocks`. CLI exits 0 (clean) / 1 (BLOCK) / 2 (input invalid). Findings JSON in gitleaks v8 schema; redacted Match/Secret form prevents leakage in the findings file itself.
- **Substantiate Step 4.6.5 wiring** (`qor/skills/governance/qor-substantiate/SKILL.md`): new substep between Step 4.6 (reliability sweep) and Step 4.7 (doc integrity). Single `python -m qor.scripts.secret_scanner --staged --out dist/secrets.findings.json || ABORT` invocation with fail-closed semantics.
- **`compute_production_attributes`** in `qor/policy/resource_attributes.py`: symmetric to Phase 53 `compute_governance_attributes` and Phase 55 `compute_skill_admission_attributes`. Drives the Cedar `has_hardcoded_secrets` boolean from scanner output.
- **Doctrine** (`qor/references/doctrine-eu-ai-act.md` `## Secret-scanning gate (Phase 56)` section): applicability + pattern catalog summary + allowlist semantics + gitleaks-v8 output format + operator workflow + limitations.
- **Shadow-genome countermeasure** `SG-SecretLeakAtSeal-A` (`qor/references/doctrine-shadow-genome-countermeasures.md`): codifies the historical risk of dormant Cedar attribute without scanner driving the boolean.
- **Glossary terms**: `secret-scanning gate`, `gitleaks-compatible findings`.
- **37 new tests** including frozen-catalog invariants, CLI exit-code matrix, Phase 50 co-occurrence behavior invariant for substantiate-skill wiring, doctrine round-trip integrity, self-application against own plan/doctrine/test files.

### Changed
- `pyproject.toml` → 0.42.0.
- `README.md` → Tests 1142, Ledger 185.
- META_LEDGER entries #183 (audit PASS), #184 (implementation), #185 (session seal). Merkle seal `dbec764642de264a1d53e93ed66c5ab1ed54e562e1bc77d23617c8cb44e99e93`.

Post-Phase-56 the five-phase compliance sprint surface is fully closed: Phase 53 (v0.39.0) closes LLM01 + DRIFT-1/2 + OWASP LOW-4; Phase 54 (v0.40.0) closes EU AI Act Art. 13/14/50 + AI RMF + LLM08; Phase 55 (v0.41.0) closes LLM05 + LLM07 + AI RMF GV-6.1/MG-3.1; Phase 56 (this release v0.42.0) closes LLM06 + AI 600-1 §2.10.

## [0.41.0] - 2026-05-01

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 55: Cedar-enforced subagent admission + model-pinning frontmatter + CycloneDX v1.5 SBOM emitter + pre-audit lint pair + deliver schema. Closes OWASP LLM Top 10 (2025) **LLM05 Supply Chain** + **LLM07 Insecure Plugin Design** at the manifest layer; aligns with NIST AI RMF GV-6.1 + MG-3.1. Third phase of the five-phase compliance sprint per `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`.

### Added
- **Cedar-enforced subagent admission** (Phase 1): `qor/policies/skill_admission.cedar` extended with two `forbid` rules over `actual_tool_invocations_exceed_scope` and `actual_subagent_invocations_exceed_scope`. New `compute_skill_admission_attributes` in `qor/policy/resource_attributes.py` with `_CANONICAL_TOOLS` frozenset (10 Tool names). `qor/reliability/skill_admission.py` `check_admission` extended with `check_tool_scope` Phase 55 enforcement (graceful fallback for legacy file-path invocations).
- **Model-pinning frontmatter** (Phase 2): 8 scoped skills declare `model_compatibility:` lists and `min_model_capability:` from ordered tier set `(haiku, sonnet, opus)`. New `qor/scripts/model_pinning_lint.py` (~135 LOC) with WARN-only CLI; `/qor-plan` Step 0.3 wires the lint.
- **CycloneDX v1.5 SBOM emitter** (Phase 3): `qor/scripts/sbom_emit.py` (~145 LOC, hand-rolled stdlib, zero new runtime deps) emits root + skill + doctrine + variant components with `bom-ref`, `name`, `version`, `purl`, `type`, `description`, and a root-depends-on-all dependency edge. New `qor/cli_handlers/release.py` (~38 LOC) hosts `do_sbom`; `qor-logic release sbom` registered. `/qor-repo-release` Step Z emits sidecar `dist/sbom.cdx.json` and captures `sbom_path` into the deliver gate payload.
- **NEW `qor/gates/schema/deliver.schema.json`** (Phase 3): closes long-standing pre-existing surface gap where `qor-repo-release` wrote `phase="deliver"` artifacts that bypassed schema validation. `qor/scripts/validate_gate_artifact.py` `PHASES` extended with `"deliver"`.
- **Pre-audit lint pair** (Phase 4): new `qor/scripts/plan_test_lint.py` (~76 LOC) detects four canonical presence-only patterns (substring-presence, section-exists, substring-in-file, path-exists). New `qor/scripts/plan_grep_lint.py` (~99 LOC) detects infrastructure-mismatch citations against actual repo state, excluding paths declared as NEW in plan Affected Files blocks. `/qor-audit` Step 0.6 + `/qor-repo-audit` Step 0.6 invoke both lints WARN-only. Closes the cross-session recurring pattern flagged across Phase 53/54/55 first audits.
- **SG-PreAuditLintGap-A** doctrine entry codifies the recurring presence-only-test + hedged-citation pattern and its countermeasure.
- **3 new glossary terms**: tool-scope policy, model-pinning frontmatter, CycloneDX SBOM.

### Changed
- **Sprint-progress reconciliation**: `qor/scripts/sprint_progress.py` extended with `sealed_priorities_from_ledger` that walks SESSION SEAL entries and recognizes "Bundles Priorities N, M, ..." patterns via sentence-boundary parsing. Closes the Phase 54 known-issue where bundled priorities reported PENDING.

### Security
- Closes OWASP LLM Top 10 (2025) **LLM05 Supply Chain** at the SBOM-manifest layer (downstream operators consume `dist/sbom.cdx.json` for vulnerability scanning) and **LLM07 Insecure Plugin Design** at the admission-policy layer (Cedar `forbid` rules enforce declared `permitted_tools` / `permitted_subagents` allowlists). Aligns with **NIST AI RMF** GV-6.1 + MG-3.1 (third-party AI risk). Sprint Phase 3 of 5 complete; Phase 56 (secret-scanning gate at substantiate) queued.

## [0.40.0] - 2026-05-01

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 54: AI provenance metadata + EU AI Act + AI RMF doctrine + subagent scaffolding + override-friction escalator. Bundles Priorities 2/4/5 from `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`. Closes EU AI Act Art. 13/50 transparency and Art. 14 oversight surfaces; aligns with NIST AI RMF 1.0 GOVERN/MAP/MEASURE/MANAGE and AI 600-1 GenAI Profile §2.7+§2.8.

### Added
- **AI provenance metadata in gate artifacts** (Phase 54): new `qor/gates/schema/_provenance.schema.json` (`$ref`'d from all six phase schemas) declaring `{system, version, host, model_family, human_oversight, ts}`. `human_oversight` enum: `pass | veto | override | absent` — operator decision per gate. New `qor/scripts/ai_provenance.py` (~140 LOC) with `build_manifest()` + `HumanOversight` enum. Auto-derives `version` from `pyproject.toml`, `host` from `qor.scripts.qor_platform.current()`, `model_family` from `QOR_MODEL_FAMILY` env (suppressible via `QOR_PROVENANCE_QUIET=1`). All six SDLC + governance skills wired to call `build_manifest` and pass through `gate_chain.write_gate_artifact(... ai_provenance=manifest)`. Closes EU AI Act Art. 13/50 transparency surface and NIST AI RMF MEASURE-2.1 / MANAGE-1.1 evidence-collection contract.
- **`qor-logic compliance ai-provenance` subcommand**: aggregates per-session provenance manifests across `.qor/gates/<sid>/*.json`. Suitable for inclusion in operator AI Act Art. 50 transparency packages. New `qor/cli_handlers/compliance.py` (~110 LOC) hosts this plus extracted `do_report` and new `do_sprint_progress`.
- **`qor-logic compliance sprint-progress` subcommand**: reads the latest `docs/research-brief-*.md`, parses Recommendations Priority headings, walks META_LEDGER for SESSION SEAL entries citing each Priority's phase, emits a sprint-progress table. New `qor/scripts/sprint_progress.py` (~95 LOC).
- **EU AI Act doctrine** (`qor/references/doctrine-eu-ai-act.md`): applicability classification (Qor-logic is *not* high-risk per Annex III; operator inheritance for downstream high-risk systems); article-by-article mapping for Art. 9, 10, 12, 13, 14, 15, 50, 72; Annex IV technical-documentation guidance.
- **AI RMF doctrine** (`qor/references/doctrine-ai-rmf.md`): GOVERN/MAP/MEASURE/MANAGE function-by-function mapping plus AI 600-1 GenAI Profile §2.4/§2.7/§2.8/§2.10/§2.12 mapping. Forward-only evidence-collection contract starting Phase 54.
- **Plan template `impact_assessment` block**: optional in plan top-matter; required when `high_risk_target: true`. Five sub-fields (purpose, affected_stakeholders, identified_risks, mitigations, residual_risks) per AI RMF MAP-3.1 / MAP-5.1. New Step 1c "Impact assessment dialogue" in `/qor-plan` SKILL.md.
- **Subagent tool-scope advisory frontmatter**: `permitted_tools:` and `permitted_subagents:` keys added to all six SDLC + governance skill YAML frontmatters. Declarative-only this phase; Phase 55 candidate wires Cedar-based admission enforcement.
- **Override-friction escalator** (`qor/scripts/override_friction.py`, ~80 LOC): counts `gate_override` events per session; threshold = 3 (symmetric with cycle-count escalator); raises `OverrideFrictionRequired` from `gate_chain.emit_gate_override` when threshold reached and no `justification` (>=50 chars) supplied. All six gate-checking skills wired to handle the exception. Closes OWASP LLM Top 10 LLM08 (Excessive Agency) strengthening + EU AI Act Art. 14.
- **`shadow_event.schema.json` `justification` field**: optional minLength 50 string; populated by `override_friction.record_with_justification` when threshold-friction is supplied.
- **Doctrine §12 "Override-friction escalator"** appended to `qor/references/doctrine-governance-enforcement.md`.

### Changed
- **CLI subcommand-handler split** (closes Pass-1 razor-overage): `qor/cli.py` 227 LOC → ~190 LOC after compliance handler bodies extracted to `qor/cli_handlers/compliance.py`. Headroom for Phase 55+ subcommand additions without re-hitting the cap. Tests under `tests/test_compliance_report_post_phase52.py` and `tests/test_nist_compliance.py` updated to import from the new location.
- **`qor.scripts.validate_gate_artifact`** uses a `referencing.Registry` to resolve `$ref` across local schemas — required for the `_provenance.schema.json` cross-reference. Backward compatible.
- **CLAUDE.md Authority line** appends `eu-ai-act` and `ai-rmf` doctrine references.

### Security
- Aligns Qor-logic with **EU AI Act (Reg. 2024/1689)** Art. 12 (logging, exemplary), Art. 13 (transparency), Art. 14 (oversight, strong), Art. 15 (cybersecurity), Art. 50 (transparency of AI-generated content). Aligns with **NIST AI RMF 1.0** GOVERN/MAP/MEASURE/MANAGE and **AI 600-1 GenAI Profile** §2.7 + §2.8. Sprint context: Phase 54 of a five-phase compliance sprint per `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`; Phase 55 (model-pinning + Cedar-enforced subagent admission + SBOM) and Phase 56 (secret-scanning gate) remain queued.

## [0.39.0] - 2026-04-30

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 53: prompt-injection defense + path canonicalization + intent-lock anchored regex. Closes OWASP LLM Top 10 (2025) **LLM01 Prompt Injection** (HIGH) at the audit-prose layer for operator-authored governance markdown. Aligns with NIST AI 600-1 §2.7 and EU AI Act Art. 15. Closes OWASP (2021) LOW-4 (intent-lock substring-PASS regex) — zero residual OWASP (2021) MEDIUM/LOW findings open. First phase of a five-phase compliance sprint per `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`.

### Added
- **OWASP LLM01 prompt-injection defense** (Phase 53): canary catalog at `qor/scripts/prompt_injection_canaries.py` (six pattern classes: instruction-redirect, role-redefinition, pass-coercion, meta-override, unicode-directionality, hidden-html), with frozen `CANARIES` tuple, `scan(content)` API, and argv-form CLI (`python -m qor.scripts.prompt_injection_canaries --files ...` plus `--mask-code-blocks` for documentation scanning). Integrated into `/qor-audit` Step 3 as new Prompt Injection Pass that runs before the Security Pass; any canary hit forces VETO with `findings_categories: ["prompt-injection", ...]` plus a severity-3 `prompt_injection_detected` shadow event.
- **Cedar `forbid` rule for governance markdown**: `qor/policies/owasp_enforcement.cedar` carries a fifth rule on `Code::"governance"` resources whose `has_prompt_injection_canary` attribute is True. Commit-time complement to the audit-time pass; two enforcement points, single source of truth (`CANARIES`).
- **Per-resource-kind attribute helper**: new `qor/policy/resource_attributes.py` exposes `compute_governance_attributes(path, content)` and `is_governance_path(path)`. Localizes governance-classification logic without bloating the generic evaluator. Path filter is a literal allowlist for `.md` files under `docs/` or `qor/references/`.
- **Doctrine**: `qor/references/doctrine-prompt-injection.md` (threat model, canary catalog, refusal protocol, out-of-scope limits). Cross-linked from `doctrine-shadow-genome-countermeasures.md` SG-PromptInjection-A.
- **`prompt-injection` finding category**: added to `qor/gates/schema/audit.schema.json` `findings_categories` enum and `qor/scripts/findings_signature.py` `_VALID_CATEGORIES` frozenset.

### Changed
- **Intent-lock anchored PASS regex** (closes Apr-16 OWASP LOW-4): `qor/reliability/intent_lock.py:_audit_has_pass` was `re.search("VERDICT.*PASS", body, re.IGNORECASE)`, which admitted substring "PASS" mentions in narrative prose. Now anchors to a multiline-anchored canonical verdict line (`^Verdict:\s*PASS$` with markdown-bold tolerance and `:`/`-` separator support). After Phase 53: zero residual OWASP (2021) MEDIUM/LOW findings open.
- **Path canonicalization** (DRIFT-1, DRIFT-2): `qor/skills/sdlc/qor-research/SKILL.md`, `qor/skills/governance/qor-substantiate/SKILL.md`, `qor/skills/meta/qor-bootstrap/SKILL.md`, and the five agent files under `qor/agents/` no longer reference legacy `.failsafe/governance/` directory or `memory/failsafe-bridge.md`. Replaced with current canonical paths (`docs/`, `.agent/staging/`, `.qor/gates/<session_id>/`).

### Security
- Closes OWASP LLM Top 10 (2025) **LLM01 Prompt Injection** at the audit-prose layer for the operator-authored governance markdown surface. Aligns with NIST AI 600-1 §2.7 (Information integrity / prompt injection) and EU AI Act Art. 15 (cybersecurity dimension). Sprint context: Phase 53 of a five-phase compliance sprint per `docs/research-brief-prompt-logic-frameworks-2026-04-30.md`; subsequent phases planned for AI provenance metadata (54), subagent least-privilege + model-pinning (55), secret-scanning gate (56), override-friction escalator (57).

## [0.38.0] - 2026-04-30

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 52: structural enforcement + retroactive remediation. First phase in repo history to land via proper /qor-plan + /qor-audit + /qor-implement + /qor-substantiate skill invocations with all four `.qor/gates/<sid>/*.json` gate artifacts written. Closes G-1 (SSDF tag evidence in ledger), G-3 root cause (skill-protocol bypass), and the retroactive Phase 46/48/49 VETOes from the three-skill audit corpus.

### Added
- **Gate-chain completeness enforcement** (Phase 52, keystone): new `qor/reliability/gate_chain_completeness.py` (103 lines, pure functions, CLI entrypoint via `python -m`). Walks SESSION SEAL ledger entries with phase >= 52; asserts `.qor/gates/<sid>/{plan,audit,implement,substantiate}.json` all exist for each. Wired into `/qor-substantiate` Step 7.8 + new `gate-chain-completeness` job in `.github/workflows/ci.yml` (blocks PR merges to main).
- **Skill-active provenance binding** (Phase 52): `qor/scripts/gate_chain.py` `write_gate_artifact()` reads `QOR_SKILL_ACTIVE` env var and refuses (raises `ProvenanceError`) on absence/mismatch. Closes the surface where any caller could write gate artifacts without skill provenance. `QOR_GATE_PROVENANCE_OPTIONAL=1` autouse fixture in `tests/conftest.py` bypasses for test compatibility.
- **NIST SSDF tag emission** (Phase 52, closes G-1): new `qor/scripts/ssdf_tagger.py` (99 lines) maps `change_class` + `files_touched` to SSDF practice IDs. `/qor-substantiate` Step 7.4 emits `**SSDF Practices**:` line into SESSION SEAL entry body before content_hash. Forward-only (Phase 52+); historical entries grandfathered. `qor.cli compliance report` now shows non-zero coverage starting from this seal.
- **3 structured SG countermeasures** (Phase 52): SG-SkillProtocolBypass (skill markdown executed without runtime provenance), SG-VacuousLint (self-exempting cutoff in commit-walking lints), SG-RecursiveBashInjection (plan that forbids shell-interpolation reintroduces it). Promoted from narrative ledger commentary to structured `qor/references/doctrine-shadow-genome-countermeasures.md` entries with detection + countermeasure + verification hint.

### Changed
- **Phase 46 razor-overage remediation** (closes retroactive VETO): `tests/test_doctrine_test_functionality.py` (was 285 lines) split via new `tests/_helpers.py` (45 lines, shared `proximity` + `strip_section` + `fenced_block_after`) and companion `tests/test_doctrine_test_functionality_negative_paths.py`. Both files now ≤250 lines (158 + 145). 20 tests still GREEN.
- **Phase 48 presence-only test remediation** (closes retroactive VETO): old `test_install_drift_check_emits_qor_logic_fix_string` (read source bytes + asserted substring without invoking unit) DELETED. Replaced by `tests/test_install_drift_check_subprocess.py` which subprocess-invokes `install_drift_check.main()` and asserts on captured output per Phase 46 doctrine.
- **Phase 49 self-exempting cutoff remediation** (closes retroactive VETO): new `tests/test_attribution_tiered_negative_paths.py` adds 6 fixture-based synthetic-violator tests. Closes the SG-VacuousLint anti-pattern at first run.
- **Doctrine update**: `qor/gates/chain.md` lines 34, 74 — "for future wiring" / "future work" prose updated to "Phase 52 wiring". `qor/references/doctrine-nist-ssdf-alignment.md` gains `### Phase 52 wiring (forward-only emission)` subsection. `qor/references/doctrine-governance-enforcement.md` § Skill Integration cited.

## [0.37.0] - 2026-04-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 50: skill-prose filesystem validation contract. Closes G-2 from `docs/compliance-re-evaluation-2026-04-29.md`.

### Added
- **Skill-prose filesystem validation contract** (Phase 50): skill prose performing filesystem operations on operator-controlled identifiers (e.g., `.qor/session/current`) MUST cite the canonical validator helper. `qor/references/doctrine-owasp-governance.md` §A03 gains a "Skill-prose worked example" paragraph naming the contract. `/qor-help --stuck` Mode protocol step 1 routes through `qor.scripts.session.current()` (which reads + validates against `SESSION_ID_PATTERN`) instead of naive marker reads. `qor/skills/sdlc/qor-implement/SKILL.md` and `qor/skills/governance/qor-substantiate/SKILL.md` Step 5.5 / Step 4.6 bash one-liners updated: `cat .qor/session/current` → `python -c "from qor.scripts.session import current; print(current() or 'default')"`. New lint `tests/test_skill_prose_filesystem_validation.py` (5 tests with proximity-anchor + strip-and-fail per Phase 46 doctrine) prevents regression.

## [0.36.0] - 2026-04-29

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

Phase 49: tiered attribution-trailer policy + README badge currency enforcement. Closes G-3 and G-4 from `docs/compliance-re-evaluation-2026-04-29.md`.

### Added
- **Tiered attribution policy** (Phase 49): `qor/references/doctrine-attribution.md` gains a `## Tiered usage` section defining required attribution form per surface — seal commits use full canonical (3 lines); plan/audit/implement commits use compact `Co-Authored-By:` only; PR descriptions use full PR-body footer; CHANGELOG and GitHub releases use the italic attribution line once per version. New `qor.scripts.attribution.commit_trailer_compact()` helper for the compact form. `ATTRIBUTION.md` gains a `## Tiered usage (quickref)` table. Locked by `tests/test_attribution_tiered_usage.py` (9 tests) with proximity-anchored assertions paired with strip-and-fail negative-paths per Phase 46 doctrine. Cutoff: versions ≥ 0.36.0; older commits/CHANGELOG sections grandfathered.
- **README badge currency enforcement** (Phase 49): new `qor/scripts/badge_currency.py` (~140 lines, pure functions) parses README literal-count badges (Tests, Ledger, Skills, Agents, Doctrines) and asserts them against current truth. CLI: `python -m qor.scripts.badge_currency`. Wired into `/qor-substantiate` Step 6.5: ABORTs seal on mismatch when `change_class ∈ {feature, breaking}`. Hotfix exempt. Locked by `tests/test_readme_badge_currency.py` (8 tests) and `tests/test_substantiate_badge_currency_wiring.py` (6 defensive tests). `qor/references/doctrine-governance-enforcement.md` gains a `### Badge currency` subsection under §8 Install Currency. Closes the systemic violation surfaced post-Phase-48 where Phases 45/46/48 each shipped with stale README badges.

## [0.35.0] - 2026-04-29

Phase 48: install-time UX/discoverability + canonical CLI rename + `/qor-help` conversational evolution.

### Added
- **`qor-logic` canonical CLI** (Phase 48): `pyproject.toml` `[project.scripts]` declares both `qor-logic` (canonical) and `qorlogic` (backwards-compat alias) mapping to `qor.cli:main`. `argparse` `prog="qor-logic"`; `--version` emits `qor-logic <semver>`. All operator-facing prose, skill prompts, references, README, and system-tier docs (`docs/operations.md`, `docs/policies.md`) updated. Filesystem state paths (`.qorlogic/config.json`, `.qorlogic-installed.json`) preserved for operator data integrity. New tests `tests/test_cli_rename.py` lock both entry points and the program-name output.
- **Conversational `/qor-help`** (Phase 48): `/qor-help` evolves from static catalog into a three-mode skill. Bare invocation shows the catalog plus a new ASCII SDLC flow chart and a "How to use /qor-help" intro. `/qor-help --stuck` reads `.qor/session/current` and `.qor/gates/<sid>/*.json` to infer SDLC position and recommend the next skill with rationale. `/qor-help -- "<free-form question>"` routes the question against the catalog plus current state. All modes are read-only; recommendation only. Locked by `tests/test_qor_help_conversational.py` with proximity-anchored assertions paired with strip-and-fail negative-path tests; the ASCII chart is verified plain-ASCII (round-trips through `body.encode('ascii')`) and the SDLC phases appear in left-to-right order.

### Changed
- **Script discoverability post-install** (Phase 48): the three remaining path-form `python qor/scripts/<name>.py` invocations in skill prose are now `python -m qor.scripts.<name>`, resolving against the installed package from any CWD. `doctrine-governance-enforcement.md` §138 rewritten to make the `python -m` rule symmetric across both `qor/scripts/` and `qor/reliability/` (previously covered only `reliability/`). Doctrine §92 prose example also updated (`python qor/scripts/session.py new` → `python -m qor.scripts.session new`). New lints `tests/test_installed_import_paths.py::test_no_path_form_qor_scripts_invocations` and `::test_no_path_form_qor_reliability_invocations` prevent regression. Closes the gap left by Phase 35 (which fixed only `qor/reliability/`).

## [0.34.0] - 2026-04-29

Phase 47: seal entry check — structural countermeasure for SG-AdjacentState-A (the bookkeeping-gap class that allowed Phase 46's first substantiate to seal at v0.33.0 without writing META_LEDGER entries).

### Added
- **`qor/reliability/seal_entry_check.py`**: pure-function reliability gate. Exposes `check(ledger_path, phase_num) -> SealEntryResult` and a CLI `python -m qor.reliability.seal_entry_check --ledger <path> --plan <path>`. The helper reads the ledger, asserts the latest entry is a SESSION SEAL for the given phase, verifies the chain hash is internally consistent (`chain_hash == chain_hash(content_hash, previous_hash)`), then runs full chain verification via `ledger_hash.verify()`. Single source of truth = the ledger; no caller-supplied Merkle seal expectation.
- **`/qor-substantiate` Step 7.7 (Post-seal verification)**: new step inserted between Step 7.6 (Stamp CHANGELOG) and Step 8 (Cleanup Staging). Runs `seal_entry_check` after Step 7 (Final Merkle Seal) writes the entry. Bash one-liner uses hardcoded `python -c "from qor.scripts.governance_helpers import current_phase_plan_path; print(current_phase_plan_path())"` to derive the plan path — no shell-variable interpolation into Python literals — then invokes the helper via argv-form `--plan "$PLAN_PATH"`. ABORT on non-zero exit leaves the session unsealed.
- **15 new tests**: 9 behavioral tests in `tests/test_seal_entry_check.py` (covering happy path, missing-seal, phase mismatch, internal chain inconsistency, full chain failure, the meta-test `test_check_replays_phase_46_original_gap` proving the new gate would have caught the historical Phase 46 substantiate gap, and `test_cli_rejects_path_with_shell_metacharacters_safely` confirming argv-form eliminates the OWASP A03 vector); 6 defensive wiring tests in `tests/test_substantiate_seal_entry_wiring.py` using proximity-anchor + strip-and-fail pattern from Phase 46 doctrine, with three direct countermeasures locking V-1 (post-Step-7 placement), V-2 (no `$MERKLE_SEAL` reference), V-3 (no `python -c` shell-interpolation) against future drift.

## [0.33.0] - 2026-04-28

### Added
- **Test functionality doctrine** (Phase 46): new `qor/references/doctrine-test-functionality.md` codifying the "test functionality, not presence" principle and wiring enforcement language into the four SDLC gate skills. `/qor-plan` Step 4 forbids presence-only test descriptions; Step 5 review checklist requires each test description to name the behavior it confirms. `/qor-audit` gains a Test Functionality Pass between Section 4 Razor and Dependency Audit (VETO any plan whose described tests do not invoke the unit). `/qor-implement` Step 5 (TDD-Light) requires the failing test invoke the unit and assert against its output; Step 9 scans newly-added tests for the `assert <substring> in <file_text>` family. `/qor-substantiate` Step 4 Test Audit refuses to seal if a phase-added test is presence-only. `CLAUDE.md` Authority line updated. Cross-references SG-035 ("doctrine-content test unanchored"). Locked by `tests/test_doctrine_test_functionality.py` with proximity-anchored regex assertions paired with strip-and-fail negative-path tests so the doctrine test cannot itself decay into a presence-only check. Variant artifacts regenerated under `qor/dist/variants/`.

## [0.32.0] - 2026-04-28

Phase 45: attribution trailer convention. Implements GitHub issue #18.

### Added
- **`qor/scripts/attribution.py`**: pure-function helper exposing three string-returning functions — `commit_trailer(model=...)`, `pr_footer(model=..., defects_list=..., comparison_doc_path=...)`, and `changelog_attribution_line()`. Module-level constants (`_SDK_NAME`, `_SDK_URL`, `_QOR_URL`, `_MODEL_EMAIL`) are the single source of truth; every default surface accepts a kwarg override so a fork rebranding the SDK or pointing at a different canonical URL needs no code changes outside the call site. Functions are pure: no I/O, no env reads, no time/random/network coupling.
- **`qor/references/doctrine-attribution.md`**: full doctrine — purpose, when-to-apply scope (only commits/PRs/releases produced under `/qor-bootstrap → /qor-plan → /qor-audit → /qor-implement → /qor-substantiate`), three canonical strings captioned with the helper function names that produce them, helper API contract, narrowly-scoped emoji exception (the leading robot emoji on bot-attribution trailer text is the single carve-out from CLAUDE.md's no-non-ASCII-in-data rule), worked example citing issue #18 + BicameralAI MCP #59.
- **`ATTRIBUTION.md`** (root): one-screen quick-ref with copy-pasteable canonical strings; pointers to the doctrine for rationale and to the helper for the canonical source.
- **CLAUDE.md Authority line**: now references `[attribution](qor/references/doctrine-attribution.md)` alongside the existing `token-efficiency`, `test-discipline`, and `governance-enforcement` doctrines.
- **15 new tests** (`tests/test_attribution.py` + `tests/test_attribution_docs_consistency.py`): 9 unit tests pinning canonical output and override semantics, 1 functional test piping the rendered trailer through `git interpret-trailers --parse` to confirm `Co-Authored-By:` is recognized as a valid git trailer (catches spacing/bracket/separator drift that pure presence-tests would miss), and 5 drift-guard tests asserting the helper's output appears verbatim in `ATTRIBUTION.md` and the doctrine and that `CLAUDE.md` Authority line links the doctrine.


## [0.31.1] - 2026-04-24

### Fixed
- **Phase 41 regex regression** (Phase 44): `qor/scripts/ledger_hash.py` now accepts the standard SESSION SEAL convention `**Chain Hash (Merkle seal)**:` and `**Content Hash (session seal)**:` markup. The strict `**Field**` anchor introduced in Phase 41 silently skipped 7 ledger entries with parenthetical-suffix labels (entries #126, #129, #132, #133, #137, #140, #143). Verifier metric: pre-fix 104 OK / 39 skipped; post-fix 112 OK / 32 skipped. Anti-vacuous-green guard added to `tests/test_ledger_hash.py` asserting that every modern entry (≥ #116) with hash markup verifies, would have caught the original Phase 41 regression at audit time. See `docs/META_LEDGER.md` Entry #146 (Phase 44 seal).

## [0.31.0] - 2026-04-24

Phase 41: ledger_hash verifier regex robustness. Resolves GitHub issue #13.

### Added
- **Fenced-form Content/Previous Hash parsing**: `qor/scripts/ledger_hash.py` `CONTENT_HASH_RE` and `PREV_HASH_RE` now accept both inline-backtick `` `<hex>` `` and fenced `= <hex>` forms, symmetric with `CHAIN_HASH_RE`. Real ledgers using fenced Content/Previous markup now verify cleanly where they previously skipped.

### Changed
- **Bounded-span discipline** (issue #13 root cause): all three hash-field regexes now use a non-greedy span bounded by negative lookahead on the next `**FieldName**:` marker; cannot sweep across field boundaries into unrelated hex values (e.g., a `**Plan Hash**` value previously captured as `Content Hash`). The `re.DOTALL` flag is no longer needed; `[\s\S]` is explicit inside the bounded span.
- **`CHAIN_HASH_RE` bold anchor**: now requires `\*\*Chain Hash\*\*` per Phase 41's anchor-symmetry rule. Prose mentions of "Chain Hash" no longer capture unrelated backtick-hex values.
- **`qor-validate` SKILL.md** (Steps 3, 4, 7): replaced three stale references to `.claude/commands/scripts/validate-ledger.py` (a stub path not produced by `qorlogic install`) with the canonical `qor/scripts/ledger_hash.py` module + `qorlogic verify-ledger` CLI. Variant SKILL.md files regenerated via `python -m qor.scripts.dist_compile`.

### Fixed
- **Existing test fixtures using unanchored `Chain Hash = {hash}` markup** (5 lines across 3 tests in `tests/test_ledger_hash.py`) updated to bold-anchored form, plus `capsys`-based stdout assertions (`OK   Entry #N:`) preventing vacuous-green regression where `rc == 0` is satisfied by silent-skip rather than verified-chain.

## [0.30.0] - 2026-04-20

Phase 39b Phases 1+2: Agent Team A/B orchestration + persona sweep.

### Added
- **`/qor-ab-run` skill** (`qor/skills/meta/qor-ab-run/`): orchestrates persona-vs-stance Identity Activation A/B measurement via parallel Task-tool subagent dispatch (20 concurrent calls in one message). Zero external dependency, zero marginal cost. `subagent_type: "general"` per doctrine §4. Subagent prompt template with `{VARIANT_IDENTITY_ACTIVATION_BLOCK}` + `{FIXTURES_CONCATENATED}` placeholders.
- **`qor/scripts/ab_aggregator.py`** (pure Python, no LLM coupling): brace-balanced JSON extractor (malformed-tolerant), per-(skill,variant) mean+stddev aggregation, ±5pp tie-threshold winner declaration, canonical markdown rendering.
- **Delegation-table** row for `/qor-ab-run`; **`/qor-help` catalog** entry.

### Changed
- **Persona sweep** (S3 from Phase 39b): 5 decorative `<persona>` tags removed — `qor-status`, `qor-help`, `qor-repo-scaffold`, `qor-bootstrap`, `qor-document`.
- **R4**: `qor-debug` line 108 `subagent_type: "general"` constraint now cross-references `doctrine-context-discipline.md` §4.
- **R5**: `qor-document` line 251 split into two discrete sentences — Identity Activation stance (main thread) vs `qor-technical-writer` subagent pairing — citing doctrine §1.2/§1.3 to prevent mechanism conflation.

### Changed
- **R3 Identity Activation rewrite** for `/qor-audit` + `/qor-substantiate` is **conditional on A/B evidence**. Operator invokes `/qor-ab-run` to produce `docs/phase39-ab-results.md`; `test_identity_activation_matches_ab_winner_if_results_exist` auto-applies the rewrite rule when results declare `winner: "stance"` for a skill. Without evidence, current persona-named Identity Activation is retained.
- **LOAD_BEARING_PENDING_EVIDENCE registry** (`tests/test_persona_sweep.py`): 19 skills documented as load-bearing by doctrine judgment, awaiting A/B evidence.

## [0.29.0] - 2026-04-20

Phase 39 Phase 1 seal: context-discipline doctrine + A/B corpus fixtures. Anthropic-SDK harness approach withdrawn in favor of Agent Team orchestration (Phase 39b).

### Added
- **`doctrine-context-discipline.md`**: codifies personas as context-prioritization scaffolds for edge-case determinations, evaluated by performance/accuracy/results. Five sections cover the three-mechanism distinction (frontmatter tag vs Identity Activation prose vs subagent invocation), persona evaluation protocol, stance directive discipline, subagent invocation rule (`general` by default; persona-typed requires evidence), and verification protocol requiring `<persona-evidence>` pointers for retained tags. `doctrine-governance-enforcement.md` §11 cross-references.
- **A/B corpus fixtures**: 20 seeded defects at `tests/fixtures/ab_corpus/` spanning 10 `findings_categories` (2 per category; `coverage-gap` and `dependency-unjustified` omitted per plan). Each fixture carries `# SEEDED TEST DEFECT — NOT EXECUTABLE` header. MANIFEST.json uses `line_start`/`line_end` for multi-line defect ranges. 4 hand-authored Identity Activation variant files under `tests/fixtures/ab_corpus/variants/`. Consumed by the Phase 39b Agent Team A/B skill.
- **Tests**: `tests/test_doctrine_context_discipline.py` (3 structural assertions).

### Changed
- Phase 39 Phase 2 scope narrowed: Anthropic-SDK harness (`ab_harness.py`, `ab_live_run.py`, optional `anthropic` dep) withdrawn. Phase 39b will ship `/qor-ab-run` skill that orchestrates the A/B cycle via parallel Task-tool subagents within Claude Code — no external API dependency, no credential management, aligned with the doctrine's "controlled context via subagents" principle.

## [0.28.3] - 2026-04-24

### Fixed
- **Intent-lock HEAD-drift** (Phase 43): `qor/reliability/intent_lock.py` `verify()` now uses `git merge-base --is-ancestor` instead of strict HEAD equality. Captured HEAD must be reachable from current HEAD; current HEAD may be any forward descendant. Eliminates the re-capture-as-SOP anti-pattern observed in Phase 41 and Phase 42 substantiate where the implement commit between Step 5.5 capture and Step 4.6 verify always tripped `DRIFT: head`. Real anti-drift threats (history rewrites, hard resets, branch switches to divergent histories) still caught. See `docs/META_LEDGER.md` Entry #140 (Phase 43 seal).

## [0.28.2] - 2026-04-24

### Fixed
- `test_every_changelog_section_has_tag` no longer blocks phase-seal PRs whose CHANGELOG sections are above the highest existing tag. Pre-release sections are now exempt from the match-a-tag rule, resolving the chicken-and-egg collision with Phase 40's LOCAL-ONLY tag doctrine. See `docs/META_LEDGER.md` Entry #137 (Phase 42 seal).

## [0.28.1] - 2026-04-20

### Fixed
- `.github/workflows/release.yml` now verifies the tag's commit is reachable from `origin/main` before publishing to PyPI; refuses publish otherwise. Closes the pre-merge-publish defect that shipped v0.24.1, v0.25.0, and v0.28.0 from unmerged PR branches. See `docs/META_LEDGER.md` Entry #133 (Phase 40 seal).

## [0.28.0] - 2026-04-20

Procedural surface freeze line. Consolidates phases 36-38 work into a single release: full SG-PlanAuditLoop-A countermeasure set (C1-C4) plus `ci_commands` plan-schema slot. Phase 39 (context-discipline + persona reshape) explicitly deferred pending upstream consumer lockdown.

### Added
- **Two-stage `addressed` flip in `/qor-remediate`** (B19, SG-PlanAuditLoop-A C1): `mark_addressed_pending` (stage 1) / `mark_addressed(review_pass_artifact_path, remediate_gate_path)` (stage 2). Stage 2 verifies the audit gate artifact is `phase: "audit"`, `verdict: "PASS"`, and its `reviews_remediate_gate` field matches the remediate gate being closed; `ReviewAttestationError` raised on any failure, no event mutation. Schema `shadow_event.addressed_pending` optional boolean + `allOf` invariant enforcing `addressed == true AND addressed_reason == "remediated"` implies `addressed_pending == true` (legacy `issue_created`/`stale` paths unaffected). Schema `audit.reviews_remediate_gate` optional `string | null` for the operator signal.
- **Stall-detection infrastructure** (B20 + B21, SG-PlanAuditLoop-A C2-C4): append-only `audit_history.jsonl` alongside singleton audit gate artifact; `findings_signature` module (16-hex-char SHA256 prefix over sorted unique categories, `"LEGACY"` sentinel for absent field, `UnmappedCategoryError` on non-enum); shared `stall_walk.run` helper returning `(count, signature, first_match_ts)`; `cycle_count_escalator.check` K=3 orchestrator; `orchestration_override.record` with session-scoped suppression marker.
- **New 7th `/qor-audit` adversarial pass**: Infrastructure Alignment Pass grep-verifies plan claims (filesystem paths, glob patterns, event types, cross-module signatures, skill-step anchors) against current repo code. New `infrastructure-mismatch` finding category.
- **Schema `audit.findings_categories`**: closed 12-value enum, required when `verdict == "VETO"` via `allOf`/`if-then` conditional.
- **Schema `shadow_event.event_type`**: +`plan-replay`, +`orchestration_override`.
- **Gate-loop classifier union**: `gate_override | orchestration_override` — repeated operator declines escalate via pattern match.
- **`/qor-plan` Step 2c + `/qor-audit` Step 0.5**: cycle-count hooks surface `/qor-remediate` escalation to operator.
- **`ci_commands` required field in `qor/gates/schema/plan.schema.json`** (B22): array with `minItems: 1`, items with `minLength: 1`. Plans authored from Phase 38 forward must declare local-validation commands. Pre-Phase-38 plans grandfathered at test layer. Matching `## CI Commands` template section in `/qor-plan` SKILL.md.
- **Doctrine §10.1-10.5**: Two-stage remediation flip; narrative SG entry closure protocol; audit history + findings signature; cycle-count escalation; operator override + suppression.
- **`SG-InfrastructureMismatch`**: codified countermeasure catalog entry.

### Changed
- 9 existing plan-payload test fixtures updated to include `"ci_commands": ["pytest"]` (fixtures represent Phase-38-era consumers of the schema).

## [0.25.0] - 2026-04-19

### Fixed
- **Installed-mode breakage (SG-Phase35-A)**: package shipped since v0.18.0 was non-functional for `pip install` users. 49 skill-prose Python blocks used `import sys; sys.path.insert(0, 'qor/scripts'); import X` — only works from repo root. Rewritten to `from qor.scripts import X`. `qor/reliability/{intent-lock,skill-admission,gate-skill-matrix}.py` renamed to snake_case; skill subprocess invocations now `python -m qor.reliability.<name>` (path-independent). Two bare intra-`qor/scripts` imports (`doc_integrity.py`, `doc_integrity_strict.py`) qualified. Regression guards in `tests/test_installed_import_paths.py` lock both structural (no hack pattern remains) and runtime (imports resolve) contracts.

### Added
- **Doctrine `doctrine-governance-enforcement.md` §9 Installed-Mode Invariants**: three binding rules — qualified `qor.scripts.*` / `qor.reliability.*` imports in skill prose, snake_case reliability module names, `python -m` invocation pattern.

### Changed
- `qor/reliability/` scripts renamed: `intent-lock.py` → `intent_lock.py`, `skill-admission.py` → `skill_admission.py`, `gate-skill-matrix.py` → `gate_skill_matrix.py`. Git history preserved via `git mv`. Only consumer is skill prose (`/qor-implement` Step 5.5, `/qor-substantiate` Step 4.6); both updated. Tests updated accordingly.

## [0.24.1] - 2026-04-19

### Fixed
- **CLI `__version__` drift (SG-Phase34-A)**: `qor/cli.py` hardcoded `__version__ = "0.18.0"` and never got updated across six releases (v0.18.0 → v0.24.0). `qorlogic --version` printed `0.18.0` even on v0.24.0 installs. `__version__` now reads from `importlib.metadata.version("qor-logic")` at import time; fallback `"0+unknown"` for uninstalled source checkouts. Regression guard `tests/test_cli_version_from_metadata.py` asserts runtime lookup and forbids reintroduction of a SemVer-shaped string literal on the `__version__` line.

## [0.24.0] - 2026-04-19

### Fixed
- **Seal-tag timing bug** affecting v0.19.0–v0.22.0: release tags were placed on the pre-seal HEAD (one commit behind the sealed content) because `create_seal_tag` ran at `/qor-substantiate` Step 7.5, before the seal commit at Step 9.5. Tag creation moved to a new Step 9.5.5 that captures the post-commit SHA via `git rev-parse HEAD` and passes it as a required `commit` argument. See SG-Phase33-A and META_LEDGER Entry #112 for forensic details and affected-tag inventory. Historical tags are not retagged.

### Added
- **Release-doc currency rule** at `/qor-substantiate` Step 6.5. When a plan declares `change_class: feature` or `change_class: breaking`, `check_documentation_currency` now also requires README.md and CHANGELOG.md in `implement.files_touched`. Hotfix is exempt. Catches the pattern where a release ships with stale narrative-doc version claims (SG-Phase32-B).
- **Glossary terms**: `release_docs`, `seal_tag_timing`.
- **Doctrine**: `doctrine-documentation-integrity.md` §5a (release-doc coverage) and `doctrine-governance-enforcement.md` §4 (seal_tag_timing wiring).

### Changed
- `governance_helpers.create_seal_tag` now takes a required `commit: str` positional argument. No HEAD-default fallback. Calling without `commit` raises `TypeError`.
- `check_documentation_currency` signature extended with optional `plan_payload: dict | None = None`. Legacy call sites without the kwarg preserve pre-Phase-33 behavior.

## [0.23.0] - 2026-04-18

### Added
- **Install drift detection** via `qor/scripts/install_drift_check.py`: SHA256-compares source `qor/skills/**/SKILL.md` against the installed copies. Invoked as CLI (`python -m qor.scripts.install_drift_check --host claude --scope repo`) or automatically at `/qor-plan` Step 0.2 as a pre-phase WARN. Fix via `qorlogic install --host <host>`.
- **`/qor-plan` Step 0.2 Install drift nudge** (pre-phase): non-blocking warning when local installed skills lag repo source.
- **Doctrine governance-enforcement §8 Install Currency**: full contract for the drift check, invocation sites, scope boundaries.
- **Check Surface D + E strict-mode is LIVE** at `/qor-substantiate` Step 4.7. `run_all_checks_from_plan(..., strict=True)` is now the default seal-time call; any term-drift or cross-doc conflict raises `ValueError` and aborts substantiation. `legacy` tier still bypasses.

### Changed
- **Check Surface D/E scope fence rewired**: `docs/*.md` is archive-by-default except the 4 system-tier docs (`architecture`, `lifecycle`, `operations`, `policies`); README and CHANGELOG excluded as narrative entry points; archive path patterns replaced by the simpler living-docs allowlist. `check_cross_doc_conflicts` now shares the `_excluded_by_scope_fence` helper with `check_term_drift` (was silently bypassing the fence before Phase 32).
- Glossary receives broad `referenced_by:` adoption across Gate, Shadow Genome, Doctrine, change_class, Substantiate, Check Surface D, and Workflow Bundle to cover all legitimate in-repo consumers.

## [0.22.0] - 2026-04-18

### Added
- **`/qor-substantiate` Step 6.5 Documentation Currency Check**: WARNs at seal time when a phase's `files_touched` includes doc-affecting changes (SKILL.md / doctrine / schema / script) but the 4 system-tier docs (`docs/{architecture,lifecycle,operations,policies}.md`) weren't updated. Operator decides whether to amend docs or continue. Lives in `qor/scripts/doc_integrity_strict.py::check_documentation_currency`. Doctrine §5 of `doctrine-documentation-integrity.md` documents the heuristic.
- **Check Surface D + E scope-fence tuning** (`qor/scripts/doc_integrity_strict.py`): three new exclusion layers -- doctrine-peer (cross-doctrine references not drift), home-directory-peer (siblings discussing shared concepts), and per-entry `scope_exclude: []` glossary frontmatter opt-out.
- **`qor/scripts/doc_integrity_drift_report.py`**: operator CLI producing a Markdown drift report grouped by term. Ad-hoc triage tool.
- **`qor/scripts/pr_citation_lint.py` + `.github/workflows/pr-lint.yml`**: CI lint enforcing `doctrine-governance-enforcement.md` §6 (PR descriptions must cite plan file + ledger entry + Merkle seal).
- **`tests/test_install_sync_with_source.py`**: SHA256-level sync between source SKILL.md files and dist variants (claude / codex / kilo-code). Catches dist drift at CI time.
- **`docs/phase31-drift-triage-report.md`**: 187-line artifact summarizing Phase 2 live drift triage decisions and deferred strict-mode wiring rationale.

### Changed
- `qor/scripts/session.py`: `MARKER_PATH` renamed from `.qor/current_session` to `.qor/session/current` to match bash references in substantiate Step 4.6 and implement Step 5.5. Migration was lossy -- the old marker file carries the rotated Phase 30 session id, the new marker needed manual migration at first Phase 31 substantiate attempt.
- `qor/references/glossary.md`: `Gate` and `Shadow Genome` entries gain 20+ additional `referenced_by:` consumers from the live drift triage.
- `/qor-audit` SKILL.md Documentation Drift section gains an explicit Python block invoking `doc_integrity.render_drift_section` (replacing prose-only narrative).
- `qor-audit-templates.md` gains `<!-- qor:drift-section -->` canonical insertion marker.

## [0.21.0] - 2026-04-18

### Added
- **System-tier documentation topology** at `docs/architecture.md`, `docs/lifecycle.md`, `docs/operations.md`, and `docs/policies.md`. Authored from the existing repo state (chain.md, skills catalog, policies, doctrines). Qor-logic itself can now declare `doc_tier: system` on plans and the check passes. Phase 30 is the first plan to self-substantiate at this tier.
- **`/qor-audit` Step Z** wires audit.json gate artifact writes via `gate_chain.write_gate_artifact` (Phase 29 delivered the SKILL edit; Phase 30 doctrine + live dogfood). Downstream phases can now read structured audit verdicts.
- **Session rotation** via `qor/scripts/session.py::rotate()`. `/qor-substantiate` Step Z calls it after writing `substantiate.json`, so the next `/qor-plan` starts with a clean `.qor/gates/<new_sid>/` directory. Prior session dirs preserved for archaeology. New doctrine section: `doctrine-governance-enforcement.md` §7.
- **Dist recompile on seal**: `/qor-substantiate` Step 8.5 invokes `python -m qor.scripts.dist_compile` automatically so variant outputs (claude / kilo-code / codex / gemini) stay in sync with source skills.
- **Check Surface D (term-drift grep)** and **Check Surface E (cross-doc conflict detection)** in new `qor/scripts/doc_integrity_strict.py`. Lenient-by-default; `strict=True` kwarg routes through `run_all_checks_from_plan`. Both scope-fenced to markdown files; code files excluded.
- **CONTRIBUTING.md**: Phase 29 landed pointer + quickstart; Phase 30 adds full doctrine inventory link from README.
- **Razor compliance forward-regression guards**: `tests/test_doc_integrity_razor_compliance.py` enforces <=250 lines on both `doc_integrity.py` and `doc_integrity_strict.py` (SG-Phase30-A countermeasure).

### Changed
- `/qor-substantiate` Constraints now require `bump_version` to run BEFORE `create_seal_tag` in Step 7.5. Inverted order (bug observed in Phase 29) interdicts on tag-already-exists and forces manual pyproject editing. Paired test locks the contract.
- CLAUDE.md: bare-backtick doctrine paths replaced with markdown links.
- README.md: complete doctrine inventory section added (14 doctrines + patterns + templates + glossary linked).
- 15 `qor/skills/**/SKILL.md` files: XML `<phase>X</phase>` tags lowercased to match YAML frontmatter case (GAP-REPO-06 resolution).
- `.github/workflows/ci.yml` and `.github/workflows/release.yml`: `actions/checkout@v4` gains `fetch-depth: 0, fetch-tags: true` so `test_every_changelog_section_has_tag` finds tags in CI.

### Security
- Check-surface scanners use stdlib `re` only; no new deserialization or subprocess surface. Scope fence explicitly excludes `*.py`, `*.json`, `*.toml`, `*.cedar` and `vendor/` / `fixtures/` / `dist/` directories.

## [0.20.0] - 2026-04-18

### Added
- `/qor-audit` now writes a schema-valid `audit.json` gate artifact at `.qor/gates/<session>/audit.json` (Step Z wiring). Previously missing; downstream phases (`/qor-implement`) had to fall back to gate overrides or hand-written artifacts. Payload carries `target`, `verdict`, `report_path`, and `risk_grade` per `qor/gates/schema/audit.schema.json`.
- `CONTRIBUTING.md` at the repo root (40 lines) -- canonical contributor entry point pointing to CLAUDE.md, gates/chain, delegation-table, workflow-bundles, doctrines, and the glossary in reading order. Quickstart recipe names the `/qor-research -> /qor-plan -> /qor-audit -> /qor-implement -> /qor-substantiate` chain. PR contract delegates to `doctrine-governance-enforcement.md` Section 6 (single source of truth; no duplication).

### Changed
- Glossary orphan adoption: seven `qor/references/glossary.md` entries (`Doctrine`, `Doc Tier`, `Glossary Entry`, `Concept Home`, `Orphan Concept`, `Doc Integrity Check Surface`, `Complecting`) now carry legitimate `referenced_by:` consumers. Closes the Phase 28 doctrine's newly-enforced-doctrine grace gap (SG-Phase29-A) caught during Phase 29 audit pass 1 and resolved before implementation.
- `README.md` gains a one-line link to CONTRIBUTING.md in the quickstart region.

## [0.19.0] - 2026-04-18

### Added
- Documentation-integrity doctrine (`qor/references/doctrine-documentation-integrity.md`) with four tiers (`minimal` / `standard` / `system` / `legacy`) enforced at `/qor-substantiate` time via the new `qor/scripts/doc_integrity.py` module.
- Canonical glossary at `qor/references/glossary.md` with 13 entries covering Phase 28 doctrine terms plus Qor-logic canonical terms (Phase SDLC, Gate, Shadow Genome, Substantiate, Workflow Bundle, change_class, Delegation Table, Complecting). Glossary entries serve simultaneously as concept-map entries (`home:` + `referenced_by:` fields).
- `/qor-plan` Step 1b: dialogue for `doc_tier`, `terms_introduced`, and `boundaries` declarations; Plan Structure top-matter extension.
- `/qor-substantiate` Step 4.7: hard-blocks seal on documentation-integrity violations via `doc_integrity.run_all_checks_from_plan` (topology presence + glossary hygiene + orphan scan). `legacy` tier is the sole documented escape.
- `/qor-audit` Documentation Drift advisory: non-VETO `## Documentation Drift` section in AUDIT_REPORT.md when plan declarations diverge from glossary/topology.

### Changed
- `qor/gates/schema/plan.schema.json` gains optional `doc_tier`, `doc_tier_rationale`, `terms`, and `boundaries` fields. An `if-then` rule enforces that `doc_tier: legacy` requires `doc_tier_rationale`.
- `qor/gates/workflow-bundles.md` example phases list expanded to the canonical seven-phase chain (previously omitted `validate` and `remediate`).

### Security
- New `doc_integrity.parse_glossary` uses `yaml.safe_load` exclusively and rejects documents containing custom tags (SG-Phase24-B countermeasure). Covered by existing `tests/test_yaml_safe_load_discipline.py` scanner.

## [0.18.0] - 2026-04-17

### Added
- `CHANGELOG.md` itself: full backfill v0.3.0 through v0.17.0 plus the "Unreleased" convention going forward.
- `qor/scripts/changelog_stamp.py`: pure-function module that renames `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` on seal.
- `qor/references/doctrine-changelog.md`: CHANGELOG discipline codified.
- `/qor-substantiate` Step 7.6 stamps the CHANGELOG as part of the seal ceremony; Step 9.5 auto-stage now includes `CHANGELOG.md`.
- Two new lint tests enforce Keep-a-Changelog structure and tag <-> CHANGELOG bijection.

## [0.17.0] - 2026-04-17

### Added
- Per-ground `**Required next action:**` directives in audit reports. Each VETO ground names the correct remediation skill (`/qor-refactor`, `/qor-organize`, `/qor-remediate`, `/qor-debug`) or the Governor for plan-text edits. Canonical mapping codified in `qor/references/doctrine-audit-report-language.md`.
- Repeated-VETO pattern detector (`qor/scripts/veto_pattern.py`): fires when >= 2 consecutive sealed phases each required > 1 audit pass. Emits a severity-3 `repeated_veto_pattern` Shadow Genome event.
- `## Process Pattern Advisory` section appended to every audit report; recommends `/qor-remediate` when the pattern fires (non-blocking).
- `repeated_veto_pattern` added to `qor/gates/schema/shadow_event.schema.json` event_type enum.

### Changed
- Audit-report template: generic "Mandated Remediation" header replaced by per-ground directives.
- `qor-audit` SKILL.md: each pass (Security, OWASP, Ghost UI, Razor, Dependency, Macro-Arch, Orphan) now carries an explicit `**Required next action:**` line.

## [0.16.0] - 2026-04-17

### Added
- `qorlogic seed`: new top-level CLI subcommand. Idempotent scaffold for governance workspaces (`docs/META_LEDGER.md`, `docs/SHADOW_GENOME.md`, `docs/ARCHITECTURE_PLAN.md` + `CONCEPT.md` + `SYSTEM_STATE.md` stubs, `.agent/staging/`, `.qor/gates/`, `.qor/session/`, `.gitignore` section).
- Prompt resilience doctrine (`qor/references/doctrine-prompt-resilience.md`): autonomy classification per skill (`autonomous` | `interactive`). Deep-audit family runs without user prompts; other skills use a single Y/N recovery prompt on missing prerequisites.
- Canonical `skill-recovery-pattern.md` reference with markers `qor:recovery-prompt`, `qor:auto-heal`, `qor:fail-fast-only`, `qor:break-the-glass`.
- Three-tier communication model (technical / standard / plain) via `/qor-tone` session command and `qorlogic init --tone <tier>`. `qor-status` designated as the canonical tone-aware example. Inspired by the MIT-licensed `caveman` project.
- `/qor-tone` skill added to the command catalog.
- `PyYAML>=6` declared as runtime dependency (frontmatter parsing uses `yaml.safe_load` only; unsafe APIs banned codebase-wide).

### Changed
- 11 governance/SDLC skills gained explicit `autonomy` frontmatter; banned over-pause phrases removed or justified with `qor:allow-pause` markers.
- `tests/test_yaml_safe_load_discipline.py` widened to scan both `qor/` and `tests/**/*.py` (excluding deliberate unsafe fixtures).

### Security
- Codebase-wide ban on `yaml.load`, `yaml.load_all`, `yaml.full_load`, `yaml.unsafe_load` enforced by lint; closes SG-Phase24-B and SG-Phase25-A countermeasures.

## [0.15.0] - 2026-04-17

### Added
- Gemini CLI as a first-class host (`qorlogic install --host gemini`). Variant emits TOML command files under `commands/`; frontmatter (`trigger`, `phase`, `persona`) preserved.
- Uniform `--scope {repo,global}` flag on `install`/`uninstall`/`list`/`init` (default `repo`). Applies to all hosts.
- `qor/install.py` module extracted from `qor/cli.py` (Razor remediation).
- `$QORLOGIC_PROJECT_DIR` environment variable for repo-root override.

### Changed
- `qorlogic install --host codex` now reads `variants/codex/` instead of the hardcoded claude variant (bug fix surfaced during Phase 24 audit).
- `HostTarget` shape: now carries `(name, base, install_map)` with prefix-keyed install dispatch. `skills_dir` and `agents_dir` retained as compat properties.

### Removed
- `CLAUDE_PROJECT_DIR` environment variable is no longer consulted. Use `--scope` or `$QORLOGIC_PROJECT_DIR`.

## [0.14.0] - 2026-04-16

### Added
- Cedar-inspired OWASP enforcement policies (`qor/policies/owasp_enforcement.cedar`).
- OWASP Top 10 governance doctrine (`qor/references/doctrine-owasp-governance.md`); OWASP pass wired into `qor-audit` SKILL.md.
- NIST SP 800-218A SSDF alignment: practice tags in ledger entries, `qorlogic compliance report` CLI, `qor/references/doctrine-nist-ssdf-alignment.md`.

### Fixed
- 9 security findings closed (MEDIUM-1..6, LOW-1..6): repo path validation, JSONL warnings, file locking, chain-hash separator, session-id/event-id validation, verdict regex, timezone-aware timestamps, skipped-entry reporting, backward-compatible legacy chain-hash verification.

### Security
- Shadow Genome process-event validation now enforces strict schema compliance on append.

## [0.13.0] - 2026-04-16

### Added
- Cedar-inspired policy evaluator in pure Python (`qor/policy/`). `qorlogic policy check` CLI evaluates request JSON against `*.cedar` policies; supports `permit`/`forbid`, `==` and `in` constraints, `when` conditions, default-deny semantics.
- Codex host resolution (was stub).
- `qorlogic init` CLI subcommand; persists host/profile/scope to `.qorlogic/config.json`.

## [0.12.0] - 2026-04-16

### Added
- `qorlogic install --host <claude|kilo-code|codex>` CLI with target-directory override.
- Manifest emission (`qor/dist/manifest.json`) with SHA256 per file.
- `qorlogic compile` / `qorlogic verify-ledger` CLI subcommands.
- CI workflow gains variant-drift and ledger-hash verification steps.

### Changed
- `qor/scripts/compile.py` renamed to `qor/scripts/dist_compile.py`.

## [0.11.0] - 2026-04-16

### Added
- `qor/resources.py` (`importlib.resources` wrapper) and `qor/workdir.py` (`$QOR_ROOT` or CWD anchor) separate packaged assets from consumer state.
- `pytest -m integration` opt-in marker for install-smoke tests.

### Changed
- 13 sibling imports migrated to package-relative form.
- 11 `REPO_ROOT` reference sites split across `qor.resources` and `qor.workdir`.
- Eliminated `sys.path.insert(...)` from production scripts.

## [0.10.0] - 2026-04-16

### Added
- PyPI packaging foundation: `[tool.setuptools.packages.find]` config, `[tool.setuptools.package-data]` for Markdown/JSON resources, `[project.scripts] qorlogic = qor.cli:main`, `classifiers`/`keywords`/`urls`/`authors`, BSL-1.1 license declaration.
- `.github/workflows/ci.yml` (3 Python x 2 OS matrix).
- `.github/workflows/release.yml` (OIDC trusted publisher flow).

## [0.9.0] - 2026-04-16

### Added
- `/qor-remediate` skill promoted from stub to executable. Five helper scripts: `read_context`, `pattern_match`, `propose`, `mark_addressed`, `emit_gate`.

### Changed
- Parallel-execution rechain: Phase 18 subagent sealed in isolated worktree and rechained from Entry #47 at merge.

## [0.8.0] - 2026-04-16

### Added
- Three reliability scripts under `qor/reliability/`: `intent-lock.py` (captures plan+audit+HEAD fingerprint before implement; re-verified at substantiate), `skill-admission.py` (frontmatter validation), `gate-skill-matrix.py` (verifies every `/qor-*` handoff reference resolves to a real skill).
- Wired into `/qor-implement` Step 5.5 and `/qor-substantiate` Step 4.6.

## [0.7.0] - 2026-04-16

### Added
- SG-036 (grace period), SG-037 (knowledge-surface drift), SG-038 (prose-code mismatch in plans) codified in the Shadow Genome countermeasures doctrine with proximity-anchored tests.

## [0.6.0] - 2026-04-16

### Changed
- `qor-audit` Step 3 cites countermeasures doctrine explicitly.
- `qor-plan` SKILL.md reduced from 278 to 238 lines via `step-extensions.md` reference; keeps Section 4 Razor compliance.

## [0.5.0] - 2026-04-16

### Added
- Shadow Genome countermeasures doctrine (`qor/references/doctrine-shadow-genome-countermeasures.md`) consolidates 9 SG entries (SG-016/017/019/020/021/032/033/034/035). AST-enforced SG-033 test covers `Starred` + `AsyncFunctionDef` node families.
- Proximity-anchored doctrine tests with negative-path validation.

## [0.4.0] - 2026-04-15

### Added
- Shadow attribution dual-file infrastructure: classification-aware `append_event(attribution=...)`, collector upstream-first fallback, `write_events_per_source` helper.
- 7 writer call sites updated to the new attribution API.
- 4 skills reference the shadow-attribution doctrine.

## [0.3.0] - 2026-04-15

### Added
- Governance enforcement pipeline: phase branching, version bumping, tagging, GitHub hygiene. First self-hosted use of `bump_version` (0.2.0 -> 0.3.0 via its own helper).

---

Earlier versions (< v0.3.0) shipped internally before the repo went public; see `git log` for migration pedigree.
