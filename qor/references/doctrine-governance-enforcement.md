# Doctrine: Governance Enforcement (Phase 13)

Phase-lifecycle discipline: branching, versioning, tagging, push/merge, GitHub hygiene.
Canonical, consolidated. `docs/PHASE_HISTORY.md` intentionally absent (V-1): phase
history lives in GitHub-native machinery (labeled issues + branches + PRs + tags).

## 1. Behavior

After substantiation passes, commit automatically; do not offer continuation menus
when work is sealable. The next decision is push/merge, not "what next phase."

## 2. Branching

One branch per phase: `phase/<NN>-<slug>`, cut from `main`.

Pre-checkout interdiction: `git status --porcelain` must be clean, or the operator
chooses stash / commit / abandon. Dirty-tree checkout is rejected with
`InterdictionError`.

## 3. Versioning

Plan headers declare canonical `**change_class**: hotfix|feature|breaking` (bold
markdown — V-2). Substantiate bumps `pyproject.toml` `[project].version` per class:

- `hotfix` → patch (0.2.0 → 0.2.1)
- `feature` → minor (0.2.0 → 0.3.0)
- `breaking` → major (0.2.0 → 1.0.0)

`bump_version` interdicts two conditions:

- target tag already exists (`v<new>` in `git tag --list`);
- target is a downgrade (`<=` highest existing tag).

## 4. Tag

Annotated tag `v{X.Y.Z}` at substantiation, with message template:

```
v{version}

Merkle seal: {seal_hash}
Ledger entry: #{entry_number}
Phase: {phase_number}
Class: {change_class}
```

**seal_tag_timing** (Phase 33 wiring): the tag is created at `/qor-substantiate` Step 9.5.5, AFTER the seal commit is made at Step 9.5 — not at Step 7.5. `governance_helpers.create_seal_tag` takes a required `commit: str` parameter; the caller captures the seal SHA via `git rev-parse HEAD` between the commit and the tag call. The pre-Phase-33 flow (tagging at Step 7.5) placed the tag on the pre-seal HEAD, producing off-by-one tags across v0.19.0–v0.22.0 where `git show <tag>:pyproject.toml` showed the version one behind the tag name. See SG-Phase33-A for the historical record.

Tag CREATION (Step 9.5.5) and tag PUSH (Step 9.7) are separated (Phase 86 wiring; GH #98). The tag is created locally on the seal commit pre-merge, but pushed to the remote only AFTER the seal commit is reachable from `origin/main`. `release.yml` triggers `on: push: tags` and its `build-and-publish` job refuses to publish a tag whose commit is not an ancestor of `origin/main`; pushing the tag alongside the branch makes that job fail on the seal PR and — because the branch ruleset gates merge on all checks — blocks the very merge that would make the tag valid. Step 9.7 gates the tag push on `git merge-base --is-ancestor`, the same predicate `release.yml` uses.

## 5. Push/Merge

Four operator options (V-9 safety):

1. push only — `git push origin <branch>`
2. push + open PR — `gh pr create`
3. merge to main locally — **dry-run first** via `git merge --no-commit --no-ff <branch>`; abort on conflict
4. hold local

## 6. GitHub hygiene

Phase lifecycle indexed by GitHub-native machinery, not a parallel doc.

- **Issue label**: `phase:NN`, `class:hotfix|feature|breaking` (matches plan header).
  One issue per phase, titled `Phase {NN}: {slug}`, opened at plan authoring.
- **Branch name**: `phase/<NN>-<slug>` (enforced by §2).
- **PR description template**: must cite (a) plan file path `docs/plan-qor-phase<NN>*.md`,
  (b) ledger entry number `#<n>`, (c) Merkle seal hash.
  Mechanically enforced by `.github/workflows/pr-lint.yml` (Phase 31 wiring):
  the `pr-lint` CI job pipes the PR body through `qor/scripts/pr_citation_lint.py`
  and fails the PR if any of the three citations is absent.
- **Tag annotation**: annotated tag created at substantiation per §4; the tag's
  annotation message links back to the PR number or commit SHA.

### 6.1 CODEOWNERS operational mode (Phase 107 wiring)

`.github/CODEOWNERS` (Phase 102) carries `@Knapp-Kevin` as the sole owner of security-critical files (workflows, pyproject.toml, lockfiles, intent_lock, env-config scripts). This **solo-owner mode** is the project's chosen operational mode for the current maintainer configuration, not an interim placeholder.

The solo-owner state is the right scope for solo-maintained governance repositories: enforced approval-before-merge on security-critical files, single source of truth for review responsibility, and zero coordination overhead. Expanding the reviewer pool changes the operational contract, not just a configuration value.

**Expansion triggers** (any of the following changes the operational mode and warrants a CODEOWNERS amendment in a dedicated phase):

1. A second maintainer joins the project with security-critical-file review authority.
2. The project federates with other Qor-logic deployments, requiring cross-deployment review coordination.
3. A compliance audit (e.g., SOC 2, supply-chain certification) requires demonstrated reviewer separation.
4. Operator-initiated formalization of a maintainer team, even absent triggers 1-3.

Until one of these conditions is met, the solo-owner state is the chosen operational mode. The Phase 101 / 102 carry-forward "broaden CODEOWNERS reviewer pool" is closed by this doctrine note (not deferred indefinitely; closed as a documented operational decision).

## 7. Session Rotation

`/qor-substantiate` Step Z calls `session.rotate()` after writing the
substantiate gate artifact. The rotate writes a fresh session_id (format
`<YYYY-MM-DDTHHMM>-<6hex>`) to the session marker, so the next `/qor-plan`
starts with a clean `.qor/gates/<session_id>/` directory.

**Why**: Phase 28 and Phase 29 sealed on the same session_id
(`2026-04-17T2335-f284b9`), and each phase's plan/audit/implement/substantiate
artifacts overwrote the prior phase's in the shared session directory. The
ledger preserves the chain, but per-phase gate-artifact archaeology is lost
when directories collide.

**How**: `qor/scripts/session.py::rotate()` calls `generate_id()` and
atomically writes the result to `MARKER_PATH`. No deletion of the prior
session's directory -- operators choose when to prune `.qor/gates/<old_sid>/`
archives.

**Enforcement**: Phase 30 substantiate Step Z is the canonical call site.
Manual session rotation (e.g., via `python -m qor.scripts.session new`) is
permitted outside the seal flow but SHOULD be rare.

**Anti-pattern**: do NOT rotate at `/qor-plan` entry (Step 0.5). Rotation at
plan-time would invalidate downstream gate checks within a single phase if
the plan needs to be re-authored after audit VETO. Rotation belongs strictly
at end-of-phase seal.

### 7.1 Session ID convention (Phase 106 wiring)

Session IDs are the directory key under `.qor/gates/<sid>/` and the value
written to `.qor/session/current`. The canonical format is enforced by
`qor.scripts.session.SESSION_ID_PATTERN`:

```
^\d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}$
```

Example: `2026-05-25T2035-c8f105`.

When a session ID doesn't match this pattern, `qor.scripts.session.current()`
returns `None` and downstream tooling falls through to the string `"default"`,
fragmenting event provenance (intent_lock, procedural_fidelity, override
events) under a shared default session. The fall-through is operationally
benign (skill execution continues) but produces lost archaeology.

`qor.scripts.session_id_lint` (Phase 106) emits a non-blocking stderr WARN
at `/qor-substantiate` Step 4.6 when the active marker doesn't match the
pattern, naming the canonical format and pointing operators at
`session.rotate()` for compliant generation. The lint always exits 0; the
WARN is a visibility signal, not a seal-block.

## 8. Install Currency

Source truth lives under `qor/skills/` in the repo. The operator runs
`qor-logic install --host <host>` to copy skills into the host's install
directory (`.claude/skills/`, `.kilo-code/skills/`, `.codex/skills/`, or
`.gemini/commands/`). When source changes (e.g., after pulling a new
release), the installed copy lags and the operator may unknowingly run
stale governance instructions.

**Install drift check**: `qor/scripts/install_drift_check.py` compares
byte-identical SHA256 of every `qor/skills/**/SKILL.md` against its
installed counterpart at `<skills_dir>/<skill-name>/SKILL.md`. Returns a
drift list (empty = clean). Non-blocking; WARN semantics.

**Invocation sites**:

- Ad-hoc: `python -m qor.scripts.install_drift_check --host claude --scope repo`
- Pre-phase nudge: `/qor-plan` Step 0.2 runs the check and emits a WARNING
  if drift detected. Does not abort; operator decides whether to run
  `qor-logic install` before proceeding.

**Why**: Qor-logic is a prompt system; the operator runs the INSTALLED
skills, not the repo source. Drift between installed and source means the
operator is executing older governance, which can diverge from the current
audit/enforcement layer. Detection is cheap (SHA256 scan); the fix is one
CLI invocation. Silent drift is the failure mode to prevent.

**Scope**: the check covers the SKILL.md catalog only. Reference docs,
patterns, ql-templates, and the glossary are not verified because they
are not currently installed by `qor-logic install` into the host's
runtime surface.

### Badge currency (Phase 49 wiring; Phase 164 generate-not-assert form)

Feature and breaking phases MUST carry current README literal-count badges (Tests, Ledger, Skills, Agents, Doctrines) and SYSTEM_STATE header fields. Since Phase 164 (research entry #378) these are GENERATED, not hand-edited: `/qor-substantiate` Step 6 runs `qor.scripts.seal_artifacts --write` to regenerate them from truth (via the `qor/scripts/badge_currency.py` counters), and Step 6.5 runs `seal_artifacts --check`; ABORTs seal on mismatch. Hotfix is exempt (matches `_RELEASE_CLASSES` semantics). The same `--check` runs as a CI step on sealed state.

Locked at the test layer by `tests/test_seal_artifacts.py` (behavioral tests of the generators against synthetic fixtures) and `tests/test_substantiate_seal_artifacts_wiring.py` (Step 6/6.5 wiring regression lock). The pre-164 live-equality class (5 badge tests + 2 SYSTEM_STATE header tests + 6 prose-wiring tests) is retired: it asserted generated-artifact state against moving truth and broke on nearly every seal (phases 121/122/123/140).

Dynamic badges (PyPI, Python version, License, NIST, OWASP, Doc Tier) are NOT parsed — they auto-refresh from shields.io live queries or are framework-named and don't drift with project state.

This addition closes G-4 from `docs/compliance-re-evaluation-2026-04-29.md`. Pre-Phase-49 the check was WARN-only; Phase 49 promotes it to ABORT for release-class phases. Three phases (45/46/48) had silently shipped with stale badges; Phase 49 prevents recurrence.

## 9. Installed-Mode Invariants (Phase 35 wiring)

Qor-logic is `pip install`-able. Every governance skill must run successfully from any CWD, not only from the Qor-logic repo root. Three binding rules:

1. **Qualified imports in skill prose**. Python blocks in `qor/skills/**/SKILL.md` must use `from qor.scripts import X` (or `from qor.scripts.<module> import Y`) — never `import sys; sys.path.insert(0, 'qor/scripts'); import X`. The `sys.path` hack only resolves when CWD is the Qor-logic repo root; in installed mode the relative path points at a non-existent directory and every downstream import raises `ModuleNotFoundError`. Locked by `tests/test_installed_import_paths.py::test_no_sys_path_hack_in_skills` and `::test_qor_scripts_modules_importable`.

2. **Snake_case helper modules, `python -m` invocation**. Scripts under `qor/scripts/` and `qor/reliability/` must be snake_case (`intent_lock.py`, `check_shadow_threshold.py`, not `intent-lock.py`) so they are valid Python module names. Skills invoke them via `python -m qor.scripts.<name>` or `python -m qor.reliability.<name>` — never via filesystem path (`python qor/scripts/<name>.py` / `python qor/reliability/<name>.py`). The path form only resolves when CWD is the dev repo root; after `pip install qor-logic`, the operator's CWD is their own project and the path does not exist. Phase 118 (GH #150) adds a self-resolving dispatch: skills invoke gates via `qor-logic reliability <name>` / `qor-logic scripts <name>`, which run the module through the CLI's own `sys.executable` and so resolve from any shell regardless of the active venv; the `python -m qor.reliability.<name>` / `python -m qor.scripts.<name>` form remains the valid in-venv equivalent and fallback. Each module exposes a `main()` entry point and an `if __name__ == "__main__":` guard. Locked by `tests/test_installed_import_paths.py::test_no_path_form_qor_scripts_invocations`, `::test_no_path_form_qor_reliability_invocations`, `::test_no_hyphen_named_reliability_invocations`, and `::test_qor_reliability_modules_importable`.

3. **No bare intra-package imports**. Inside `qor/scripts/*.py`, sibling modules must be imported as `from qor.scripts import sibling` — never as bare `import sibling`. Bare imports only resolve when some caller earlier in the same process has prepended `qor/scripts/` to `sys.path`; removing the hack breaks them. Enforced implicitly by `test_qor_scripts_modules_importable` (modules that re-introduce bare imports fail to load in installed mode and the test raises).

**Why**: these three rules collectively close the installed-mode breakage family (SG-Phase35-A). Before Phase 35, every `pip install qor-logic` user received a package whose skills silently failed at every governance-helper import. The repo's own CI always ran from repo root, so the assumption held and no test caught it. The Phase 35 structural + runtime test pair is the mechanical guarantee that future skill authoring cannot reintroduce the family.

### Ledger reconciliation (forward-only; Phase 119, GH #148)

A duplicate-`previous_hash` residual (the SG-ConcurrentLedgerRace-A pattern: two entries claiming the same `previous_hash` from a concurrent pre-V1 append) is repaired with `qor-logic reconcile`, never by editing sealed entries. Two stages, mirroring the Phase 36 B19 pending->authorized contract:

1. `qor-logic reconcile propose --ledger <path>` — read-only; detects the residual and writes a pending proposal artifact. Mutates nothing.
2. `qor-logic reconcile authorize --proposal <path> --ledger <path>` — appends a forward-only **RECONCILIATION** entry whose `**Reconciled Entries**:` line attests the residual set. The explicit `--proposal <path>` arg is the sole operator-authorization signal (no heuristic proposal discovery).

`verify-ledger` honors a RECONCILIATION attestation only for entries that are genuine duplicate-`previous_hash` members (so it cannot launder content tampering), reporting `DISCLOSED_RECONCILED` for the attested set without the `--tolerate-known-grandfathered` flag. Sealed entries are never renumbered or rewritten — the RECONCILIATION entry is appended. See `qor/references/doctrine-shadow-genome-countermeasures.md` SG-ConcurrentLedgerRace-A "V2 real fix".

**Anti-pattern**: do not paper over the invariant with try/except `ImportError` ladders that fall back to `sys.path.insert`. The invariant is that the skill is invocable from any CWD; silent fallback masks the breakage instead of preventing it.

## 10. Process Remediation Lifecycle (Phase 36 wiring)

### 10.1 Two-stage remediation flip

`/qor-remediate` proposes process-level changes (skill/agent/gate/doctrine). Per the skill's own constraint, **remediation is advisory until reviewed**. This is enforced mechanically by a two-stage flip on the `addressed` state of the shadow events the remediation targets:

**Stage 1 — pending.** `/qor-remediate` Step 4 calls `remediate_mark_addressed.mark_addressed_pending(ids, session_id)`. This flips `addressed_pending: true` on each matched event. `addressed` stays `false`; `addressed_ts` stays `null`; `addressed_reason` stays `null`. The event log now records "remediation proposed; awaiting review."

**Stage 2 — addressed.** When the operator reviews the remediation, they invoke `/qor-audit` with the skill arg `reviews-remediate:<path-to-remediate.json>`. `/qor-audit` Step 4.1 captures this path and writes `reviews_remediate_gate: "<path>"` into the audit gate artifact. If the audit reaches a PASS verdict, Step 4.2 invokes `remediate_mark_addressed.mark_addressed(ids, session_id, review_pass_artifact_path, remediate_gate_path, closure_enforcer)`, which:

1. Validates `closure_enforcer` (Phase 166; GH #249) against exactly four forms: an existing `tests/test_*.py` path, an importable `qor.scripts.*`/`qor.reliability.*` module, a `/qor-<skill> Step N` gate reference, or `cannot-automate: <justification >= 50 chars>`. Invalid or missing: raises `ClosureEnforcerError`; no event mutation. A pattern cannot close on prose alone.
2. Verifies the audit artifact exists, has `phase == "audit"`, `verdict == "PASS"`.
3. Verifies the artifact's `reviews_remediate_gate` field equals `remediate_gate_path`.
4. On any verification failure: raises `ReviewAttestationError`; no event mutation.
5. On success: flips `addressed: true`, stamps `addressed_ts`, writes `addressed_reason: "remediated"`, records `closure_enforcer`, preserves `addressed_pending: true`.

The `sg_closure_lint` companion (WARN-only, `/qor-audit` Step 0.6 ladder) walks the countermeasure doctrine's `## SG-` entries and flags any entry citing no executable enforcer -- the standing backfill worklist for the same rule at corpus level.

The `reviews_remediate_gate` field is the **explicit operator signal**. Absence of the signal is interpreted as "this audit is not reviewing a remediation" — unrelated PASS audits in the same session never touch event state. This is the V1 resolution from Phase 36 Pass 1: detecting review intent via `remediate.json` file presence alone was too coarse (any session with a prior `/qor-remediate` invocation would fire the flip on any subsequent PASS audit).

**Schema invariant.** `qor/gates/schema/shadow_event.schema.json` enforces via `allOf/if-then`: any event with `addressed == true AND addressed_reason == "remediated"` must also carry `addressed_pending == true` AND a non-null `closure_enforcer` (>= 8 chars; Phase 166). Legacy closure paths (`addressed_reason in {"issue_created", "stale"}`) are unaffected — the invariants do not fire on those.

**Anti-pattern.** Do not bypass the two-stage flip by calling `mark_addressed` directly without the review-pass artifact. The function explicitly requires it and will raise. Do not attempt to derive the review-pass path from heuristics (newest audit file, file in session dir, etc.) — the operator's explicit `reviews-remediate:<path>` arg is the only valid signal.

### 10.2 Narrative SG entry closure

Narrative Shadow Genome entries in `docs/SHADOW_GENOME.md` are a different artifact class from the structured events in `docs/PROCESS_SHADOW_GENOME.md`. The two-stage flip in §10.1 applies only to structured events. Narrative SG entries use a different closure protocol:

When a countermeasure ships that addresses a narrative SG entry, append a `## Closure` block to the entry. The block cites:
- Seal commit SHA of the phase that shipped the countermeasure.
- Ledger entry number that records the seal.
- A one-sentence summary of what the countermeasure did.

Example:
```markdown
### Closure

Seal commit: abc1234 (Phase 36 B19)
Ledger entry: #125
Summary: Two-stage addressed flip in /qor-remediate; Phase 36 ships the schema field + refactored mark_addressed + doctrine §10.1.
```

A closure block does NOT remove the entry or revise its timestamp. The failure pattern remains in the shadow log as historical record; the closure block documents remediation shipment. Subsequent recurrences of the same family start a new entry rather than reopening the closed one.

### 10.3 Audit history and findings signature (Phase 37)

Every `/qor-audit` gate emission writes two artifacts:

1. **Singleton** `.qor/gates/<sid>/audit.json` — authoritative for chain gating (read by `gate_chain.check_prior_artifact` for `/qor-implement` etc.). Overwritten on re-emission.
2. **Append-only history** `.qor/gates/<sid>/audit_history.jsonl` — one JSON record per audit in session order. Advisory for stall detection. Schema-validated line-by-line on read.

The history log is the input to `findings_signature.compute_record`. Every VETO audit carries `findings_categories` (closed 12-value enum in `audit.schema.json`); the signature is the first 16 hex characters of SHA256 over the dedupe-and-sort-joined category list. Audits emitted before Phase 37 lack the `findings_categories` field and resolve to the literal sentinel `"LEGACY"` (not hex-shaped, so no collision with real signatures).

Unmapped categories raise `UnmappedCategoryError` at emission; `/qor-audit` Step Z cannot write a gate artifact whose categories are outside the closed enum. No `other` escape hatch — drift must force deliberate schema amendment.

### 10.4 Cycle-count escalation (Phase 37)

Both `/qor-plan` (Step 2c) and `/qor-audit` (Step 0.5) call `cycle_count_escalator.check(session_id)` before continuing. The helper walks session audit history backward via `stall_walk.run`:

- Counts consecutive same-signature VETO audits (`findings_signature.compute_record`)
- Resets on PASS, signature change, `LEGACY` sentinel, or any implement/debug singleton artifact whose timestamp lies between the run's audit entries
- Threshold `K = 3`

When `count >= K`, the helper returns `EscalationRecommendation(suggested_skill="/qor-remediate", escalation_reason="cycle-count", signature, cycle_count)`. The skill SURFACES the recommendation to the operator; it does not auto-execute. Operator may proceed with the current phase (plan/audit), in which case §10.5 applies.

**Phase 69 (GH #43) addition — session-total mode**. The consecutive-streak mode above misses the session-arc pattern where the same signature recurs across MULTIPLE artifacts (e.g., 3 plans authored in one session, each VETO'd with the same signature, but interleaved with PASS records or implement breaks that reset the consecutive counter). `cycle_count_escalator.check_session_total(session_id)` aggregates per-signature counts across the entire session audit history via `stall_walk.count_session_signature_totals`; when any signature reaches `K = 3` cumulative, returns `EscalationRecommendation(escalation_reason="session-total", ...)`. Both modes run in parallel at `/qor-plan` Step 2c and `/qor-audit` Step 0.5; either firing surfaces the same `/qor-remediate` recommendation. The `escalation_reason` field distinguishes them in shadow-event payloads. Same suppression marker applies (§10.5).

### 10.5 Operator override and re-prompt suppression (Phase 37)

When an operator declines a cycle-count escalation, `orchestration_override.record(session_id, skill, recommended_skill, reason)` does two things:

1. Appends a severity-2 `orchestration_override` shadow event (local attribution). This event is unioned with `gate_override` in the gate-loop classifier (`remediate_pattern_match.PATTERN_RULES`). Two overrides in one group trigger `gate-loop`, which — paired with the plan-replay classifier — drives `/qor-remediate` from the pattern-match side even when the operator keeps declining live escalations.
2. Writes `.qor/session/<sid>/escalation_suppressed` with the current timestamp. `cycle_count_escalator._suppression_active` checks this marker against `first_match_ts` of the run; if the marker is newer, the escalation is suppressed for the remainder of the session.

Session-scoped only. A new session resets the suppression. Longer-term suppression (e.g., "known issue, do not nag for the week") is deliberately out of scope — the shadow-event path IS the long-term signal; the marker file is only re-prompt hygiene.

## 11. Context Discipline (Phase 39)

Personas in Qor-logic skills are context-prioritization scaffolds for edge-case determinations, evaluated by performance/accuracy/results — not aesthetic flavor. See `qor/references/doctrine-context-discipline.md` for the full doctrine: three-mechanism distinction, persona evaluation protocol, stance-directive discipline, subagent invocation rule, and verification protocol requiring `<persona-evidence>` pointers for retained tags.

## 12. Override-friction escalator (Phase 54)

Symmetric with §10.4 cycle-count escalator. `qor.scripts.override_friction.check(session_id)` counts `gate_override` events for the session in `docs/PROCESS_SHADOW_GENOME.md`. Threshold `K = 3` (same value, same per-session scope as cycle-count). When `count >= K`, the next call to `gate_chain.emit_gate_override` raises `OverrideFrictionRequired` unless the caller passes `justification=<text>` of `>= 50` characters.

Friction form: free-text justification appended to the override event's payload via `override_friction.record_with_justification`. Lowest UX cost (one prompt at threshold), highest signal value (operator must articulate WHY the override is appropriate). Below threshold, override behavior is unchanged.

Skill prose at every gate-checking skill (`/qor-research`, `/qor-plan`, `/qor-audit`, `/qor-implement`, `/qor-substantiate`, `/qor-validate`) handles the exception by prompting the operator for a justification and re-calling `emit_gate_override(..., justification=<text>)`. Operator refusal to provide a justification leaves the gate in its current state; operator must address the underlying cause via `/qor-remediate`.

Maps to OWASP LLM Top 10 LLM08 (Excessive Agency) strengthening, NIST AI RMF MANAGE-1.1, and EU AI Act Art. 14 oversight. Per `qor/references/doctrine-ai-rmf.md` §MANAGE.

## §10.10 Session reconciliation protocol (Phase 63)

When a local session work-stream diverges from `origin/main` in phase numbering AND version space (both ahead and behind on a fork), the canonical timeline is `origin/main`. Session work is REBASED + RENUMBERED — or, when shared governance surfaces have been independently evolved on both timelines, CONSOLIDATED — rather than force-pushed. The protocol:

1. **Forensic preservation first.** Create `archive/session-<DATE>` pointing at the divergent local HEAD BEFORE any destructive git operation. The archive branch is the only authoritative record of the original session commit history after the rewrite.
2. **Reset local main to upstream.** `git fetch origin && git reset --hard origin/main`. The reset is destructive on the working branch; the archive branch is the recovery path.
3. **Choose replay strategy by conflict topology.**
   - **Path A (per-phase replay)**: cherry-pick session phases sequentially with renumbered phase + version identifiers. Each replay is a fresh META_LEDGER seal entry chained from upstream's last entry. Suitable only when shared files have minimal conflict surface.
   - **Path B (consolidated reconciliation)**: bundle session-NEW files (source, tests, docs) into ONE renumbered phase commit. Drop session-side edits to shared governance files (SKILLs, doctrines, schemas) that upstream has independently addressed. Suitable when both timelines materially evolved the same governance surfaces.
4. **Test functionality, not artifact preservation.** When Path B is chosen, tests that assert session-side governance text (e.g., `assert "Step 6.8" in SKILL.md`) are dropped along with the corresponding session edits. The deliverable is the genuine source-code surface, not the parallel governance prose.
5. **CLOSING SEAL documents the chain-rewrite explicitly.** Entry body cites: (a) which session entry numbers are abandoned, (b) the new anchor entry from upstream, (c) the path taken (A vs B), (d) the deliverables consolidated. The dropped chain-continuity is the documented compromise, not a defect.
6. **Old session tags are deleted after the closing seal.** Tags pointing at abandoned commits are removed via `git tag -d`; the abandoned commits remain reachable only through the archive branch.

Maps to NIST AI RMF MANAGE-2.4 (decommissioning), GOVERN-5.1 (incident response), and EU AI Act Art. 12 (record-keeping continuity through the discontinuity). The audit trail is preserved on the archive branch even though the live chain forks.

## 13. Seal Hash Integrity Gate (Phase 64)

The Seal Hash Integrity Gate at `/qor-substantiate` Step 6.8 is the fail-closed validator that prevents fabricated hash strings from entering the META_LEDGER chain. Closes the GH #48 failure mode where the substantiate skill, running in a non-Python repo with no local `calculate-session-seal.py`, instructed the LLM operator to compute cryptographic seals and produced patterned hex strings (ascending odd-position digits, 67-character non-SHA256 lengths) that passed no validation.

Contract:

- The gate calls `qor.scripts.hash_guard.require_toolkit_modules(("qor.scripts.ledger_hash", "qor.scripts.hash_guard"))` to fail closed when the seal-critical helpers are absent. Missing modules raise `RuntimeError` and ABORT substantiation.
- The gate calls `qor.scripts.hash_guard.validate_sha256(value, label=...)` for each of the four seal-critical hash values: `merkle_seal`, `content_hash`, `previous_hash`, `chain_hash`. Each validation raises `ValueError` on empty, wrong-length, uppercase, non-hex, or placeholder (all-zero) digests.
- The gate sits AFTER Step 6.5 (Documentation Currency Check) and BEFORE Step 7 (Final Merkle Seal). It runs before any hash value enters the SESSION SEAL entry body.
- The gate has NO override path and is NOT governed by Phase 47 skip semantics. Cryptographic evidence is seal-critical; advisory bypass is not available. This distinguishes the gate from §10 cycle-count escalation (operator override allowed) and §12 override-friction (operator justification allowed).
- Remediation on ABORT: install the seal-critical helper modules, regenerate the affected hash via `python -m qor.scripts.ledger_hash hash <path>`, or amend a fabricated value to a real digest, then re-run `/qor-substantiate`.

Maps to OWASP LLM Top 10 LLM06 (Sensitive Information Disclosure: prevent fabricated cryptographic evidence), NIST AI RMF MAP-3.1 (trust anchor integrity), and EU AI Act Art. 12 (record-keeping integrity). The gate is the runtime enforcement that closes the gap between `hash_guard`'s Phase 59 helper module landing on main and the substantiate skill actually invoking it.

## 14. Post-anchor ledger invariant (Phase 66)

`/qor-validate` runs in two modes that reflect distinct trust contracts on the META_LEDGER chain. Phase 66 introduces the post-anchor invariant alongside the existing raw-verifier semantics.

**Raw mode** (default): every entry verifies under canonical or Session Seal markup, every chain link math-checks against its recorded predecessor, every hash passes placeholder-pattern detection. Any failure is a hard error. Use for canonical-ledger pre-release audits.

**Post-anchor mode** (`qor-logic verify-ledger --post-anchor`): the active chain contract begins at a boundary entry; pre-boundary failures are reported as `DISCLOSED_PRE_ANCHOR` and tolerated, post-boundary failures remain hard errors. The boundary defaults to the highest-numbered cleanly-verifying entry; operator may pin via `--boundary N`.

Contract:

- A consumer workspace that has documented its pre-anchor edit cluster (e.g., as `## Edit Disclosure` entries cited in `docs/SHADOW_GENOME.md`) may release with `verify_post_anchor` exit 0 even when raw verifier exit code is non-zero.
- The pre-anchor disclosure is part of the audit trail; it is not concealed, it is acknowledged. Raw mode remains the strict-correctness audit and is the right tool for catching tampering on a canonical ledger.
- TAINTED entries propagate downstream from every FAIL: once a chain link breaks, every subsequent entry is reported as `TAINTED Entry #N: depends on failed predecessor #M` regardless of whether its own chain math is internally consistent. Math consistency alone is not trust; the chain root is poisoned.
- Placeholder-pattern hashes (ascending hex, repeating bigrams, issue-54-class fabrication shapes, low-entropy runs) are flagged as FAIL with the offending field named. The conventional all-zeros previous_hash for genesis entries is exempted.

Maps to NIST AI RMF MAP-3.1 (trust anchor integrity), OWASP LLM Top 10 LLM06 (Sensitive Information Disclosure: prevent unwarranted OK signals on poisoned chains), and EU AI Act Art. 12 (record-keeping continuity through documented anchor events). The two modes close the GH #54 / GH #55 pair: #54's blind spot where Session-Seal-only entries and placeholder-pattern hashes silently passed; #55's false-positive where raw-verifier failures on disclosed pre-anchor entries blocked release on otherwise-clean post-anchor surfaces.

## 15. No ungoverned path forward (Phase 109)

A skill may proceed only after its required governance artifacts classify as healthy, or after it has taken an explicitly governed recovery branch. The checker `qor.scripts.governance_health` is the single classifier; `/qor-status` consults it before lifecycle routing and every governance-reading skill runs the `qor:governance-health-preflight` before reading.

- `UNINITIALIZED` and scaffold-owned `MISSING` are the only states a skill may resolve with `qor-logic seed`.
- `DAMAGED` and `INCOMPLETE` are blocking and route to `/qor-remediate` or section completion -- never to seed or bootstrap (overwriting authoritative content is the failure this closes).
- Inventing an Ungoverned Path Forward (synthesizing a plan, audit, implementation, or seal from assumptions when an artifact is not OK) is invalid.

Maps to NIST AI RMF MAP-3.1 (trust anchor integrity) and EU AI Act Art. 12 (record-keeping integrity). Enforced by `tests/test_governance_prompt_health_coverage.py`, `tests/test_prompt_resilience_lint.py`, and `tests/test_governance_health.py`.
