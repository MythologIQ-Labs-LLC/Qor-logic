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
Manual session rotation (e.g., via `python qor/scripts/session.py new`) is
permitted outside the seal flow but SHOULD be rare.

**Anti-pattern**: do NOT rotate at `/qor-plan` entry (Step 0.5). Rotation at
plan-time would invalidate downstream gate checks within a single phase if
the plan needs to be re-authored after audit VETO. Rotation belongs strictly
at end-of-phase seal.

## 8. Install Currency

Source truth lives under `qor/skills/` in the repo. The operator runs
`qorlogic install --host <host>` to copy skills into the host's install
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
  `qorlogic install` before proceeding.

**Why**: Qor-logic is a prompt system; the operator runs the INSTALLED
skills, not the repo source. Drift between installed and source means the
operator is executing older governance, which can diverge from the current
audit/enforcement layer. Detection is cheap (SHA256 scan); the fix is one
CLI invocation. Silent drift is the failure mode to prevent.

**Scope**: the check covers the SKILL.md catalog only. Reference docs,
patterns, ql-templates, and the glossary are not verified because they
are not currently installed by `qorlogic install` into the host's
runtime surface.

## 9. Installed-Mode Invariants (Phase 35 wiring)

Qor-logic is `pip install`-able. Every governance skill must run successfully from any CWD, not only from the Qor-logic repo root. Three binding rules:

1. **Qualified imports in skill prose**. Python blocks in `qor/skills/**/SKILL.md` must use `from qor.scripts import X` (or `from qor.scripts.<module> import Y`) — never `import sys; sys.path.insert(0, 'qor/scripts'); import X`. The `sys.path` hack only resolves when CWD is the Qor-logic repo root; in installed mode the relative path points at a non-existent directory and every downstream import raises `ModuleNotFoundError`. Locked by `tests/test_installed_import_paths.py::test_no_sys_path_hack_in_skills` and `::test_qor_scripts_modules_importable`.

2. **Snake_case reliability modules, `python -m` invocation**. Scripts under `qor/reliability/` must be snake_case (`intent_lock.py`, not `intent-lock.py`) so they are valid Python module names. Skills invoke them via `python -m qor.reliability.<name>` — never via filesystem path (`python qor/reliability/<name>.py`). Each module exposes a `main()` entry point and an `if __name__ == "__main__":` guard. Locked by `tests/test_installed_import_paths.py::test_no_hyphen_named_reliability_invocations` and `::test_qor_reliability_modules_importable`.

3. **No bare intra-package imports**. Inside `qor/scripts/*.py`, sibling modules must be imported as `from qor.scripts import sibling` — never as bare `import sibling`. Bare imports only resolve when some caller earlier in the same process has prepended `qor/scripts/` to `sys.path`; removing the hack breaks them. Enforced implicitly by `test_qor_scripts_modules_importable` (modules that re-introduce bare imports fail to load in installed mode and the test raises).

**Why**: these three rules collectively close the installed-mode breakage family (SG-Phase35-A). Before Phase 35, every `pip install qor-logic` user received a package whose skills silently failed at every governance-helper import. The repo's own CI always ran from repo root, so the assumption held and no test caught it. The Phase 35 structural + runtime test pair is the mechanical guarantee that future skill authoring cannot reintroduce the family.

**Anti-pattern**: do not paper over the invariant with try/except `ImportError` ladders that fall back to `sys.path.insert`. The invariant is that the skill is invocable from any CWD; silent fallback masks the breakage instead of preventing it.

## 10. Process Remediation Lifecycle (Phase 36 wiring)

### 10.1 Two-stage remediation flip

`/qor-remediate` proposes process-level changes (skill/agent/gate/doctrine). Per the skill's own constraint, **remediation is advisory until reviewed**. This is enforced mechanically by a two-stage flip on the `addressed` state of the shadow events the remediation targets:

**Stage 1 — pending.** `/qor-remediate` Step 4 calls `remediate_mark_addressed.mark_addressed_pending(ids, session_id)`. This flips `addressed_pending: true` on each matched event. `addressed` stays `false`; `addressed_ts` stays `null`; `addressed_reason` stays `null`. The event log now records "remediation proposed; awaiting review."

**Stage 2 — addressed.** When the operator reviews the remediation, they invoke `/qor-audit` with the skill arg `reviews-remediate:<path-to-remediate.json>`. `/qor-audit` Step 4.1 captures this path and writes `reviews_remediate_gate: "<path>"` into the audit gate artifact. If the audit reaches a PASS verdict, Step 4.2 invokes `remediate_mark_addressed.mark_addressed(ids, session_id, review_pass_artifact_path, remediate_gate_path)`, which:

1. Verifies the audit artifact exists, has `phase == "audit"`, `verdict == "PASS"`.
2. Verifies the artifact's `reviews_remediate_gate` field equals `remediate_gate_path`.
3. On any verification failure: raises `ReviewAttestationError`; no event mutation.
4. On success: flips `addressed: true`, stamps `addressed_ts`, writes `addressed_reason: "remediated"`, preserves `addressed_pending: true`.

The `reviews_remediate_gate` field is the **explicit operator signal**. Absence of the signal is interpreted as "this audit is not reviewing a remediation" — unrelated PASS audits in the same session never touch event state. This is the V1 resolution from Phase 36 Pass 1: detecting review intent via `remediate.json` file presence alone was too coarse (any session with a prior `/qor-remediate` invocation would fire the flip on any subsequent PASS audit).

**Schema invariant.** `qor/gates/schema/shadow_event.schema.json` enforces via `allOf/if-then`: any event with `addressed == true AND addressed_reason == "remediated"` must also carry `addressed_pending == true`. Legacy closure paths (`addressed_reason in {"issue_created", "stale"}`) are unaffected — the invariant does not fire on those.

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

### 10.5 Operator override and re-prompt suppression (Phase 37)

When an operator declines a cycle-count escalation, `orchestration_override.record(session_id, skill, recommended_skill, reason)` does two things:

1. Appends a severity-2 `orchestration_override` shadow event (local attribution). This event is unioned with `gate_override` in the gate-loop classifier (`remediate_pattern_match.PATTERN_RULES`). Two overrides in one group trigger `gate-loop`, which — paired with the plan-replay classifier — drives `/qor-remediate` from the pattern-match side even when the operator keeps declining live escalations.
2. Writes `.qor/session/<sid>/escalation_suppressed` with the current timestamp. `cycle_count_escalator._suppression_active` checks this marker against `first_match_ts` of the run; if the marker is newer, the escalation is suppressed for the remainder of the session.

Session-scoped only. A new session resets the suppression. Longer-term suppression (e.g., "known issue, do not nag for the week") is deliberately out of scope — the shadow-event path IS the long-term signal; the marker file is only re-prompt hygiene.

## 11. Context Discipline (Phase 39)

Personas in Qor-logic skills are context-prioritization scaffolds for edge-case determinations, evaluated by performance/accuracy/results — not aesthetic flavor. See `qor/references/doctrine-context-discipline.md` for the full doctrine: three-mechanism distinction, persona evaluation protocol, stance-directive discipline, subagent invocation rule, and verification protocol requiring `<persona-evidence>` pointers for retained tags.
