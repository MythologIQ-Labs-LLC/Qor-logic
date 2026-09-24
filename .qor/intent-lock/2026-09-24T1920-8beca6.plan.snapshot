# Plan: Phase 296 - Governed re-attestation of sealed intent-lock evidence

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: intent-lock re-attestation
  home: qor/references/doctrine-publication-boundary.md

**boundaries**:
- limitations: re-attestation supersedes only the plan side of an intent-lock family; the audit snapshot and `audit_hash` never change. The lock record (`<session>.json`) is hash-bound by nothing today, so a coordinated direct edit of record, snapshot, and plan still passes `intent_lock_committed`, exactly as before this phase; re-attestation is the sanctioned, disclosed path and does not close that pre-existing gap. Ledger AMENDMENT entries are reviewed through pull-request review; no gate machine-enforces review of them.
- non_goals: binding lock records to a ledger commitment; widening `publication_boundary_lint`'s scanned suffixes; remediating `.tpl`, dotfile, or vendor content; rewriting git history; editing any historical ledger entry or lock record.
- exclusions: identity terms in files the lint does not scan (`.tpl`, `.gitignore`) and the lock-record binding gap are separate follow-ups.

## Open Questions

None.

## Problem

`doctrine-publication-boundary.md` requires outside-repository references to be removed retroactively. Two sealed plans on `main` carry an identity term, so the seal's identity-aware `publication_boundary_lint` (substantiate Step 4.6.14, ABORT) fails for every phase sealed on an operator host with the overlay. Their tracked intent-lock plan snapshots carry the same text; the lint does not scan `.snapshot` files, so they cause no finding, but they are published content within the doctrine's scope and are remediated with their plans. CI's `intent_lock_committed` binds a walked sealed session's plan file and snapshots to its lock record's hashes, so a plain edit fails CI, and rewriting the record would remove the evidence GH #352 committed. This phase adds a ledger-committed, append-only way to supersede a walked session's recorded plan hash, then uses it once; a session the checker does not walk is remediated by edit plus disclosure, since nothing verifies it.

## Locked decisions

### LD-1: byte-level verifiers of sealed intent-lock evidence

`intent_lock_committed` verifies every walked sealed session in CI:

`git show 8968bb5f:qor/reliability/intent_lock_committed.py | grep -nE 'def _check_session'` -> `44:def _check_session(repo: Path, phase: int, session: str) -> list[Failure]:`

`git show 8968bb5f:.github/workflows/ci.yml | grep -nE 'intent_lock_committed'` -> `100:        run: python -m qor.reliability.intent_lock_committed --phase-min 231`

`intent_lock verify` also hashes a record's plan and audit, but for one named session only:

`git show 8968bb5f:qor/reliability/intent_lock.py | grep -nE 'ver.add_argument'` -> `264:    ver.add_argument("--session", required=True)`

Its only invocation is substantiate Step 4.6 (ladder row 4.6) with the active session's id (`SESSION_ID`), never a past sealed session, so it is left unchanged. Other readers only stage or detect presence:

`git show 8968bb5f:qor/scripts/seal_stage.py | grep -nE 'intent-lock/\{session_id\}'` -> `79:        f".qor/intent-lock/{session_id}.json",`

`git show 8968bb5f:qor/scripts/evidence_bundle.py | grep -nE 'def _intent_lock'` -> `151:def _intent_lock(repo_root: Path, sid: str) -> dict:`

### LD-2: re-attestation record shape and chain (plan side only)

A re-attestation is a tracked file `.qor/intent-lock/<session>.reattest-<k>.json`, `k` matching `[1-9][0-9]*` and contiguous from 1. Closed field set, all strings: `session`, `supersedes_plan_hash`, `plan_hash`, `reason`. The original `<session>.json` is never modified; `audit_hash` is never superseded.

The effective plan hash starts as the record's `plan_hash`. For each `k` in order, `supersedes_plan_hash` must equal the current effective plan hash, and `plan_hash` becomes the new one. The plan-snapshot self-consistency check and the plan-referent check compare against the final effective plan hash; the audit-snapshot check keeps comparing against the record's `audit_hash`.

`reattestation-invalid` is reported (as a `Failure`, never an exception) when a re-attestation file: is not valid JSON or not an object; has a field set other than exactly the four above; has a `session` that differs from its filename; has a name matching `<session>.reattest-*.json` whose suffix is not `[1-9][0-9]*` (for example `reattest-01`, `reattest-x`); breaks contiguity; does not chain from the effective plan hash; or is not ledger-committed (LD-3). A re-attestation file whose session the checker does not walk is also reported, so no record can sit unverified. "Walked" means the session set `_extract_seal_sessions` returns for the invocation's `phase_min`; CI and the live-repo test both use 231, and a higher `phase_min` legitimately treats older sessions' records as unwalked. With no re-attestation files present, behavior is unchanged.

The record's `reason` is scanned by `publication_boundary_lint` (`.json` is a scanned suffix) and, like the AMENDMENT body, must not quote removed text.

The fold lives in a helper `_effective_plan_hash(...)` returning the hash plus any failures, keeping `_check_session` within the 40-line Razor limit.

### LD-3: each re-attestation file is committed by a ledger entry

The checker requires `ledger_commitment.latest_commitments(<ledger>)[<reattest path>] == ledger_hash.content_hash(<reattest file>)`, so an uncommitted or post-commit-edited record fails. `latest_commitments` is called only when a re-attestation file exists; a `MalformedCommitmentError` becomes a `reattestation-invalid` failure rather than an exception.

`latest_commitments` attributes only line-leading Artifact, Plan, or Brief citations whose path ends in `.md` (the pattern on the line after the one cited here):

`git show 8968bb5f:qor/scripts/ledger_commitment.py | grep -nE '_ARTIFACT_RE = '` -> `39:_ARTIFACT_RE = re.compile(`

The capture widens to accept `.md` or `.json`. Measured on the live ledger at `8968bb5f`: zero line-leading citations end in `.json`, and `latest_commitments` returns the same 231 artifacts before and after, so no existing commitment changes. `_is_citable` (plans and briefs) is unchanged.

Committing kinds are unchanged:

`git show 8968bb5f:qor/scripts/ledger_commitment.py | grep -nE '_COMMITTING_KINDS = '` -> `38:_COMMITTING_KINDS = ("RESEARCH BRIEF", "IMPLEMENTATION", "SESSION SEAL", "AMENDMENT")`

Each re-attestation is committed by an `AMENDMENT` entry appended through `ledger_emit.append`, fields in this order, each on its own line: `**Artifact**: <reattest path>`, `**Amends**: Entry #<seal>`; `content=ledger_hash.content_hash(<reattest file>)`. No `**Superseded Content Hash**` field: the superseded plan hash lives in the record, and the seal entry never committed the plan bytes. The body names paths and the reason and does not quote removed text.

### LD-4: remediation targets

| Session | Seal | Plan | Walked by checker | Treatment |
|---|---|---|---|---|
| `2026-09-23T1628-c67a6a` | #801 | `docs/plan-shadow-escalation-origin-signature-current.md` | yes | re-attestation record + AMENDMENT |
| `2026-09-23T0645-a3ddc4` | #799 | `docs/plan-qor-phase291-recompose-reconcile-dialect-accessor.md` | no | edit + AMENDMENT disclosure, no record |

`git show 8968bb5f:docs/META_LEDGER.md | grep -nE '^\*\*Session\*\*: 2026-09-23T(1628-c67a6a|0645-a3ddc4)'` -> `23862:**Session**: 2026-09-23T1628-c67a6a`

Entry #799 carries no `**Session**` line, so session `0645-a3ddc4` is never walked and nothing verifies its lock family; a re-attestation record there would be rejected by LD-2's unwalked-session rule. Its plan line and plan snapshot are edited and disclosed by an AMENDMENT (`**Amends**: Entry #799`, no `**Artifact**` line, so no commitment is created).

In each plan only the one non-goal line naming the outside repository changes, to a generic phrase. Each plan snapshot is regenerated from the edited plan (LF-normalized bytes). No audit snapshot, no `<session>.json` record, and no historical ledger entry is edited.

### LD-5: staging

`git show 8968bb5f:.gitignore | grep -nE 'intent-lock'` -> `18:.qor/intent-lock/`

`seal_stage` force-adds only the sealing session's own three lock files. The remediation files belong to other sessions, so the implement pass stages them explicitly, exactly, never by glob:

`git add -f -- .qor/intent-lock/2026-09-23T1628-c67a6a.reattest-1.json .qor/intent-lock/2026-09-23T1628-c67a6a.plan.snapshot .qor/intent-lock/2026-09-23T0645-a3ddc4.plan.snapshot`

Both snapshots are already tracked, so `git ls-files` cannot show whether the edited bytes were staged. The confirmation is `git diff --cached --name-only`, which must list all three paths (and both edited plans) before the implement gate; if any is missing, staging failed.

Enforcement differs by session. For the walked session `1628-c67a6a`, CI's `intent_lock_committed` fails a missing record or an unstaged snapshot (`reattestation-invalid` or `plan-referent-mismatch`/`snapshot-mismatch`). For the unwalked session `0645-a3ddc4`, nothing mechanical checks its snapshot; the cached-diff confirmation above is the only check, and the seal entry names the path.

### LD-6: doctrine home

`doctrine-publication-boundary.md` gains a section on remediating sealed evidence (re-attestation for walked sessions; edit plus disclosure for unwalked ones; the guarantee and its limits as stated in `boundaries`). The glossary gains `intent-lock re-attestation` (home: that doctrine; referenced by `qor/reliability/intent_lock_committed.py`). Doctrine prose avoids `<term> is/means` phrasing that the doc-integrity check reads as a divergent definition.

## Phase 1: Checker and commitment reader

### Affected Files

- `tests/test_intent_lock_committed.py` - new tests (listed first; red before implementation)
- `tests/test_ledger_commitment.py` - new tests for `.json` attribution
- `qor/scripts/ledger_commitment.py` - `_ARTIFACT_RE` capture accepts `.md` or `.json`
- `qor/reliability/intent_lock_committed.py` - `_effective_plan_hash` helper; `_check_session` uses it; unwalked-session re-attestation scan; `reattestation-invalid` failure kind; ledger path threaded from `check`

### Unit Tests

Each builds the existing `_repo` fixture, calls `subject.check(repo, phase_min=231)`, and asserts on the returned `Failure` list (kinds and named file). The fixture ledger has no chain hash or tail marker, so tests write AMENDMENT entries as literal text with `ledger_hash.content_hash` of the record, not through `ledger_emit.append`.

- `test_redaction_with_committed_reattestation_verifies_clean`: edit plan, regenerate plan snapshot, write `reattest-1`, commit it; `[]`.
- `test_redaction_without_reattestation_still_fails`: same edit, no record; `plan-referent-mismatch` and `snapshot-mismatch`.
- `test_uncommitted_reattestation_is_invalid`: record present, no ledger entry; one `reattestation-invalid` naming it.
- `test_reattestation_edited_after_commit_is_invalid`: commit, then change `reason`; `reattestation-invalid`.
- `test_reattestation_not_chaining_from_the_record_is_invalid`: `supersedes_plan_hash` differs; `reattestation-invalid`.
- `test_two_step_reattestation_chain_verifies_clean`: `reattest-1`, `reattest-2`, both committed; `[]`.
- `test_reattestation_gap_is_invalid`: `reattest-2` without `reattest-1`; `reattestation-invalid`.
- `test_reattestation_session_mismatch_is_invalid`: `session` field differs from filename; `reattestation-invalid`.
- `test_malformed_reattestation_json_is_a_failure_not_an_exception`: invalid JSON; `check` returns `reattestation-invalid` and does not raise.
- `test_reattestation_with_extra_or_audit_field_is_invalid`: an added `audit_hash` key; `reattestation-invalid`, and the audit snapshot is still checked against the record.
- `test_non_integer_or_padded_index_is_invalid`: `reattest-01.json` and `reattest-x.json`; each `reattestation-invalid`.
- `test_reattestation_for_unwalked_session_is_invalid`: record for a session with no SESSION SEAL `**Session**` line; `reattestation-invalid`.
- `test_malformed_ledger_commitment_becomes_a_failure`: ledger carries a truncated `**Superseded Content Hash**`; with a record present, `check` returns `reattestation-invalid` and does not raise.
- `test_valid_chain_does_not_excuse_a_tampered_audit_snapshot`: committed, valid `reattest-1`; audit snapshot bytes changed; `check` returns `snapshot-mismatch` naming the audit snapshot.
- `test_valid_chain_with_stale_plan_snapshot_fails`: committed, valid `reattest-1` and edited plan, plan snapshot not regenerated; `check` returns `snapshot-mismatch` naming the plan snapshot.
- `test_no_reattestation_files_is_unchanged_behavior`: existing fixture; `[]`.
- `tests/test_ledger_commitment.py::test_json_artifact_in_a_committing_entry_is_attributed`: AMENDMENT with `**Artifact**: .qor/intent-lock/s.reattest-1.json`; `latest_commitments` maps the path to its hash.
- `tests/test_ledger_commitment.py::test_json_citation_in_a_gate_tribunal_is_not_a_commitment`: same line in a GATE TRIBUNAL; path absent.

The existing `test_the_real_ledger_verifies_clean_at_the_boundary` must stay green through Phase 3.

## Phase 2: Doctrine and glossary

### Affected Files

- `qor/references/doctrine-publication-boundary.md` - new section: remediating sealed evidence
- `qor/references/glossary.md` - `intent-lock re-attestation` entry

### Unit Tests

- Verified by the seal's strict `doc_integrity.run_all_checks_from_plan` (glossary home, `referenced_by`, term drift). No new test file.

## Phase 3: Remediation

### Affected Files

- `docs/plan-shadow-escalation-origin-signature-current.md` - one non-goal line anonymized
- `docs/plan-qor-phase291-recompose-reconcile-dialect-accessor.md` - one non-goal line anonymized
- `.qor/intent-lock/2026-09-23T1628-c67a6a.plan.snapshot` - regenerated from the edited plan
- `.qor/intent-lock/2026-09-23T0645-a3ddc4.plan.snapshot` - regenerated from the edited plan
- `.qor/intent-lock/2026-09-23T1628-c67a6a.reattest-1.json` - NEW
- `docs/META_LEDGER.md` - two AMENDMENT entries (LD-3 for #801 with `**Artifact**`; LD-4 disclosure for #799 without), appended before the implement gate

Staging per LD-5.

### Unit Tests

- `test_the_real_ledger_verifies_clean_at_the_boundary` (existing) passes against the remediated, staged tree.
- Operator-local verification (overlay present): `python -m qor.scripts.publication_boundary_lint --repo-root .` reports 0 findings at `structural+identity`. Not a CI test: the overlay is gitignored.

## Definition of Done

### Deliverable: re-attestation-aware intent-lock checker

- **D1**: for a walked sealed session, a plan-side change that is not a contiguous, closed-schema, ledger-committed re-attestation chain fails as before or as `reattestation-invalid`; re-attestation records for unwalked sessions fail. A coordinated direct edit of the lock record itself remains undetected, as before this phase.
- **D2**: `qor/reliability/intent_lock_committed.py` (`_effective_plan_hash`, `_check_session`, unwalked-session scan); `qor/scripts/ledger_commitment.py` `_ARTIFACT_RE`.
- **D3**: doctrine section and glossary entry; AMENDMENT entries per LD-3/LD-4.
- **D4**: the sixteen `tests/test_intent_lock_committed.py` tests and two `tests/test_ledger_commitment.py` tests above pass; run twice.

### Deliverable: sealed-evidence boundary remediation

- **D1**: no tracked, lint-scanned file carries an identity term.
- **D2**: two plan lines, two snapshots, one re-attestation record, all tracked (LD-5).
- **D3**: two AMENDMENT entries; the SESSION SEAL names all remediated paths; the seal stamps CHANGELOG and regenerates README counts (`check_documentation_currency` expects both for a feature phase).
- **D4**: `python -m qor.reliability.intent_lock_committed --phase-min 231` exits 0; operator-local `publication_boundary_lint` reports 0 findings at `structural+identity`.

## CI Commands

- `python -m pytest tests/test_intent_lock_committed.py tests/test_ledger_commitment.py -v` - new and existing checker tests
- `python -m pytest tests/ -q` - full suite
- `python -m qor.reliability.intent_lock_committed --phase-min 231` - live sealed evidence verifies
- `python -m qor.scripts.publication_boundary_lint --repo-root .` - boundary (identity scope on an overlay host)
- `python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .` - seal-artifact currency
- `python -m ruff check qor/ tests/` - lint
