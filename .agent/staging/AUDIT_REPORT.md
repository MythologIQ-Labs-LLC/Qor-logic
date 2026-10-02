# AUDIT REPORT

**Tribunal Date**: 2026-10-02
**Target**: `docs/plan-qor-phase302-dist-manifest-integrity.md`
**Iteration**: 1 (branch `phase/302-dist-manifest-integrity`, head `f93b106b`, plan-only; base `main` `f2e4be9a` = 0.175.5)
**Session**: `2026-09-28T0457-61990a`
**Risk Grade**: L2
**Auditor**: The Qor-logic Judge
**Mode**: Option B fresh-context reviewer, independent of the plan author. `audit_risk_score` reported `option_b_required: true` (flag `high-citation-surface`). This review is that independent audit: a subagent with no plan-authoring context. The Codex plugin is unavailable. `external_reviewer.run_external_review` returned `fallback` ("no reviewer configured"). Both `capability_shortfall` events were emitted (`399c2fec...` codex-plugin, `f030521a...` external-reviewer). Reviewer toolset: shell, git (local objects, plus `git ls-remote` over the proxy), file read and grep, Python with the in-tree `qor` package on `PYTHONPATH`, and pytest in scratch clones outside the repository. No GitHub API was used.

**Session continuity disclosure**: the container restarted after the plan was written. The session marker `.qor/session/current` (`2026-09-28T0457-61990a`), the session key and the plan gate artifacts survived on disk. `qor_audit_runtime.session_id()` resolves to this session, and `check_prior_artifact` reports the plan artifact found and valid. Nothing was re-created.

---

## VERDICT: PASS

---

### Executive Summary

The plan closes both halves of GH #440 and does what it says.

Citations: all 46 `git show ... | grep` evidence statements were re-run at `f2e4be9a`, with 0 mismatches. The two `prints` statements also match. The prose line references were spot-checked: `qor/cli.py` 314, `doctrine-changelog.md` 9/14-16/31-32/78-79/91-93, FEATURE_INDEX row 12, and the `git grep` caller list. The attribute counts reproduce: 339 `lf` and 74 `unspecified` (47 toml, 16 yml, 4 yaml, 7 json), and all 413 index blobs are `i/lf`.

The defect reproduces at the base, using the committed dist in a scratch clone:

- A stale manifest hash passes drift (`OK: 406 files`), installs 78 files, and writes a receipt row `00000000...` for a file that hashes to `921f39ce...`.
- A tampered shipped file fails drift but still installs with exit 0.
- A dropped entry passes drift, and install silently omits the file (`Installed 77`).
- An autocrlf checkout gives exactly the 5 named receipt rows whose hash differs from the installed file.

The Judge rebuilt the Phase 1 test file from the plan text and applied the Phase 2 and Phase 3 code exactly as specified:

- The base gives `11 failed, 3 passed`. The implementation gives `14 passed`, twice.
- Mutations M1 to M8 over the 53-item set each fail exactly the named items (4/2/2/5/1/1/1/1), and the set is GREEN twice after revert.
- The consumer suites give `78 passed`.
- The full suite gives `3641 passed, 3 skipped, 4 deselected`. Afterwards only the seven manifests are modified, and the drift check still gives `OK: 413 files, no drift`.
- Ruff and the publication boundary lint are clean.
- On the real committed dist, a stale claude manifest hash now fails drift (`~ variants/claude/manifest.json`, exit 1), and install refuses with no target created.

The CI step is effective. It runs in `gate-chain-completeness` after only checkout, setup-python and `pip install -e` (setuptools build, no compile hook), so it sees the committed tree and fails on a stale manifest.

The LF pin was checked with a Linux autocrlf simulation. Every dist file checks out LF, and claude/codex/kilo-code/gemini install with exit 0 (78/78/78/47). The full suite in an autocrlf clone gives `3641 passed`, against `3627 passed` for the base in the same simulation.

The release-state proof is non-vacuous:

- The CI-view simulation prints `{'0.175.5'} {'0.175.5'}` at the base.
- The guarded clone proof fails at the current head (`project version 0.175.5`). A clone of a worktree takes that worktree's HEAD, so the proof is not reading the wrong branch.
- A simulated seal commit (`0.175.6`, dated section, local `v0.175.6`) without the entry gives `1 failed, 3 passed` with orphan `0.175.5`.
- With the LD-13 entry it gives `4 passed` (exit 0), twice.
- The remote's highest tag is `v0.172.2`.

The scope stays hotfix. The CI step and the `.gitattributes` pin are each a necessary condition of the fix. Without the step, nothing checks the committed manifests. Without the pin, LD-4 would refuse legitimate autocrlf checkouts.

### Pre-audit gates

- Governance health preflight (`skill-entry`): all OK.
- Step 0 gate check: plan artifact `plan-iter1.json` found and valid.
- Step 0.3 `plan_iteration_status_lint`: exit 0.
- Step 0.4 unchanged-plan short-circuit: `should_skip=False` (no prior audit); plan hash `3fe222fb...90c9e`.
- Step 0.5 escalator: `cce.check` and `check_session_total` both None.
- Step 0.6 lints: all exit 0. plan_grep 46 citations truth-checked; sg_closure 40/0; gate_schema_freeze 0; publication_boundary 0. `workspace_fragility_check` reports medium (67 dirty gate artifacts, pre-existing, WARN-only).
- Step 0.7 spec-delta: the plan declares no `spec_deltas`, and no contracted spec covers install or drift (LD-10 verified: only `execution-context-governance` and `spec-corpus` exist).
- Prompt injection canaries: exit 0.
- Version applicability: `target v0.175.6 > current highest v0.175.5`.
- `prose_test_lint --enforce`: exit 0.
- Runtime contract walk (WARN-only): 2 backward WARNs (`check_variant_drift`, `release_state` have no production importer; both are CLI/test-driven by design).

### Audit Results

#### Security Pass
**Result**: PASS
There is no auth, credential or secret surface. Install now fails closed on any hash mismatch before writing anything. The bytes that are verified are the bytes that are written, so there is no read-twice TOCTOU.

#### OWASP Top 10 Pass
**Result**: PASS
- A03: no subprocess in product code. The tests use list-form `git` argv.
- A04: fail-closed with a named next step; no silent drop.
- A08: the manifest is parsed with `json.loads`, and `yaml.safe_load` is used in the test only.

#### Ghost UI Pass
**Result**: PASS (no UI surface)

#### Section 4 Razor Pass
**Result**: PASS
Measured on the reconstruction: `qor/install.py` is 220 lines (the plan says 228 with the full docstring) and `check_variant_drift.py` is 96 (103). `_do_install` is 38 lines, and every new function is under 20. Nesting is at most 3, with no nested ternaries.

#### Self-Application Sub-Pass
**Result**: PASS
`originating_remediation` is GH #440, whose discipline is: record no unchecked value as an integrity claim, and exclude no file class from verification. Applied to the plan, every quoted observation the Judge could run reproduced:

- RED/GREEN counts, mutation counts, suite totals and the 413-file drift result.
- The autocrlf install results and the CI-view and clone-proof outputs.
- The remote tag ceiling.

The one claim that was not observed is Windows CI behaviour. It is declared as unobserved in the boundaries, in LD-7 and in LD-8, and is not stated as fact.

#### Test Functionality Pass
**Result**: PASS

| Test | Invokes unit? | Asserts on output? | Verdict |
| ---- | ------------- | ------------------ | ------- |
| drift_flags_a_manifest... (4) | yes (`drift_mod.main`) | exit code + diff line, both directions | PASS |
| drift_flags_an_unparseable_manifest | yes | exit 1 + diff line, no raise | PASS |
| drift_ignores_only_the_generated_timestamp | yes | exit 0 + `OK:` | PASS |
| install_refuses_bytes... (4) | yes (`_do_install`) | rc, stderr names file, empty target, no `Installed` | PASS |
| install_receipt_hashes_equal_the_installed_bytes | yes | path set + per-row sha256 vs bytes | PASS |
| install_does_not_verify_an_entry... | yes | rc 0, row count, no `extra` row | PASS |
| a_ci_job_checks_variant_drift... | parses the workflow | step order (drift before pytest/compile) | PASS (config-ordering check; M7 proves discrimination) |
| every_committed_dist_file... | runs `git check-attr` | resolved `eol` per tracked path | PASS (M8 proves discrimination) |

No closed-enum taxonomy is introduced.

#### Dependency Pass
**Result**: PASS
The plan adds no dependency. The modules it adds are all stdlib (`hashlib`, `json`), and `yaml` is already a dependency.

#### Macro-Level Architecture Pass
**Result**: PASS
The fix sits at the only place a manifest sha256 becomes a claim. That is verified: `install_drift_check` reads no manifest, and `sbom_emit` has 0 `sha256` references. The drift check reuses its existing regenerate-and-compare path, and no logic is duplicated.

#### Feature Test Coverage Pass
**Result**: PASS
FX001 cites `tests/test_dist_manifest_integrity.py` with a behavioural descriptor (exit 1, nothing copied, no receipt; otherwise each receipt sha256 equals the installed bytes). The descriptor holds under the acceptance question (mutations M1 and M3).

#### Infrastructure Alignment Pass
**Result**: PASS
Every cited path, function and line was verified at `f2e4be9a`, and so was every new symbol (`_verified_entries`, `_copy_verified`, `_comparable_bytes`, `_MANIFEST_NAME`, `_VOLATILE_MANIFEST_KEYS`). The removed `_copy_manifest_entries` and `_copy_entry` have callers only in `qor/install.py`, and `_do_install`'s only product caller is `qor/cli.py:314`. All test callers of `_do_install` were enumerated:

- `test_cli_install_source` hashes its `read_bytes`.
- `test_phase21_harness` compiles its dist.
- `test_cli_install_gemini` hashes `body.encode`. It is LF-only on Windows `write_text`, which is why the plan converts it to `write_bytes`.

No other test installs from a manifest with false hashes; `test_cli_feature_index_backfill`'s zero hashes reach only `_do_list`. The behavioural claim that `eol=lf` overrides `core.autocrlf` on checkout is git's documented attribute precedence, and it was observed in the simulation.

#### Filter-Stage Ordering Coherence
**Result**: PASS
In `_verified_entries` the stages run in order: resolve the route, skip absent or unrouted entries, read, hash-compare, plan. `_do_install` refuses before `_copy_verified` (mutation M3). In CI, the drift step precedes every recompile in its job.

#### Orphan Detection
**Result**: PASS
The new test file is collected by pytest (`testpaths = ["tests"]`). The modified modules stay on the CLI path (`qor.cli` -> `qor.install`; CI -> `check_variant_drift.py`).

#### Documentation Drift
`doc_integrity.render_drift_section` returned empty (glossary clean).

### Windows line-ending analysis (brief-mandated)

- **Fresh Windows checkout with the pin.** All dist files are LF, which matches the manifests (index blobs are all LF). Install verifies clean.
- **Test-matrix suite on Windows.** `tests/test_cli.py` recompiles `qor/dist` in place from sources. The `.yml` and `qor/agents/*.md` sources are unpinned, so on Windows they are CRLF. The recompiled dist and its manifests are therefore mutually consistent. That stays true because manifests hash the emitted bytes, and drift now compares manifests as parsed JSON, so a `write_text`-translated CRLF manifest is not drift. The same state already exists at the base for the pinned dist `.md`, so the pin adds no new class.
- **No new break from the pin.** No test reads committed `.yml`/`.toml`/`.json` dist files byte-for-byte against sources. `test_install_sync_with_source` compares markdown only.
- **Installs the tests drive.** Only the gemini fixture builds a manifest from `str.encode` while writing in text mode, and the plan fixes it.
- **Residual (declared).** The Windows run itself is unobserved. The Linux autocrlf simulation does not reproduce `write_text` newline translation, and that gap is exactly the gemini case the plan addresses.

### Violations Found

None.

### Advisories (non-binding)

- **A1**: LD-2 cites `_write_install_record` at "line 41". The `def` is at line 39, and line 41 is the receipt write. The citation is imprecise but not false.
- **A2**: The CHANGELOG clause "after removing only `generated_ts`" does not say that the comparison is on parsed JSON, so key order and whitespace are not drift. All values are still compared. The behaviour is declared in the boundaries, LD-5 and LD-8. The wording is not misleading about integrity.
- **A3**: `qor/dist/** text eol=lf` forces the `text` attribute on any future binary placed under `qor/dist/`. Today all 413 tracked files are md/toml/yml/yaml/json, so the risk is latent and not declared.
- **A4**: A Windows working copy checked out before the pin keeps CRLF in the five claude `.yml` files until it is re-checked-out, because git does not rewrite unchanged blobs when attributes change. Install from that copy now refuses and names the files, and the message gives a working remedy (`qor-logic compile`). This is fail-closed by design, but it is not stated in LD-8.
- **A5**: `workspace_fragility_check` reports medium (67 dirty gate artifacts). This is pre-existing.

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->

No repeated-VETO pattern detected in the last 2 sealed phases.

**Required next action:** `/qor-implement`.

---
_This verdict is binding._
