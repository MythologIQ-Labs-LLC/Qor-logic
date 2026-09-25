# Plan: Recompose GH #483 stale-session marker fix on current main

**change_class**: hotfix

**doc_tier**: standard

**Origin**: GH #483 and historical PR #490.

**Current base**: `eb1ed647c92ac2da5948e7f2a69a534c34fa897c` after PR #506 landed.

## Problem Contract

The session marker currently risks conflating an absent marker with a valid marker whose mtime exceeded `SESSION_TTL`. During an in-progress multi-day governed cycle, rotating that stale-but-live marker can orphan existing gate artifacts under the prior session id and split one phase across session directories.

Historical PR #490 implemented and independently reviewed a correction against an earlier base. That branch also carried independent release/version/seal and generated repository-state changes that conflict with current main. The semantic session fix remains valuable; historical promotion metadata does not become current merely because the code still applies.

PR #509 was first recomposed against `d37c192c...`; PR #506 subsequently landed as `eb1ed647...` with fresh governance evidence for GH #477. This revision reconstructs #509 directly on that newer main while preserving only the #483 semantic change, tests, and the required session-model documentation correction.

## Change Contract

### Authorized scope

- Preserve the GH #483 session semantics from PR #490:
  - distinguish marker state as `absent`, `stale`, or `fresh`;
  - detect whether a stale marker's session still owns unsealed gate artifacts;
  - reuse and refresh a stale-but-live session rather than rotating it;
  - retain prior rotation behavior for stale sealed/inactive sessions and truly absent markers.
- Preserve the seven behavioral regression tests covering stale/absent/live/sealed/no-gate cases and mtime refresh behavior.
- Preserve the narrowly required `docs/lifecycle.md` correction so documentation matches the session behavior.

### Explicit exclusions

- No historical `0.174.1` version bump, CHANGELOG release entry, META_LEDGER/seal, gate/intent-lock artifacts, README/SYSTEM_STATE seal state, Governance Index phase-state replay, or generated-manifest replay from PR #490.
- No general redesign of session identity or TTL policy.
- No Qortara Logic migration.

## Locked Decisions

### LD-1: Stale and absent are different states

A valid stale marker is evidence of an existing session, not evidence that no session exists.

### LD-2: Rotation depends on phase liveness, not age alone

A stale marker whose session still contains unsealed gate work must be reused and refreshed. A stale marker for sealed or inactive work may rotate under the existing TTL policy.

### LD-3: Recovery must preserve one gate chain

The implementation must never "recover" a stale active session by creating a second session id for the same in-flight phase.

### LD-4: Historical #490 evidence is revision-bound

The prior audit/review/tests remain useful provenance, but current-base CI and formal `/qor-audit` are required before promotion from this branch.

## Affected Files

- `qor/scripts/session.py`
- `tests/test_session_marker_staleness.py`
- `docs/lifecycle.md`

## Definition of Done

- D1: Stale-but-live sessions are reused and refreshed.
- D2: Absent, sealed, or inactive session states retain safe rotation semantics.
- D3: The seven GH #483 behavioral regressions pass.
- D4: `docs/lifecycle.md` accurately describes the stale-active exception.
- D5: Full repository CI is green on the exact current branch head.
- D6: Formal `/qor-audit` evaluates this current-base plan before promotion.

## Feature Inventory Touches

Empty. This is a bounded correction to governance session continuity.

## CI Commands

- `python -m pytest tests/test_session_marker_staleness.py -q`
- `python -m pytest tests/ -q`
- `ruff check qor/scripts/session.py tests/test_session_marker_staleness.py`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint`

## Promotion Rule

Do not merge using PR #490's old release/seal evidence. Promotion requires fresh current-base CI plus current-base governance evidence.
