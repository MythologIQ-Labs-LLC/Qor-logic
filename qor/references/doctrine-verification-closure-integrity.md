# Doctrine: Verification & Closure Integrity (Phase 114; GH #166, #158)

Counter-control for the half-measure pattern (`SG-HalfMeasureClosure`, umbrella GH #147): work must be *proven* done, not asserted done. Realized as the fail-closed promotion and seal-time wiring of existing surfaces, NOT a new QA skill.

## Terms

- **QA Evidence Artifact**: a compact, off-chain `qa.json` gate artifact (`qor/gates/schema/qa.schema.json`) recording per-pillar verification status plus an overall `verdict` (PASS|FAIL). Built by `qor.scripts.qa_evidence`; read by the close guard via `gate_chain.read_phase_artifact("qa", session_id)`.
- **Acceptance-Criteria Close Guard**: `qor.scripts.ac_close_guard` — refuses (under enforcement) to treat an issue as closed when an acceptance criterion is neither met nor split into a filed follow-on.

## QA evidence contract

Four pillars: `regression`, `security`, `stability`, `coverage`. Each is `{status: pass|fail|skip, evidence?, metric?, note?}`. `verdict` is FAIL iff any pillar is `fail`; `skip` is visible per-pillar but does not fail the verdict.

Partial coverage is explicit, never silent: a pillar not wired to real evidence emits `status: "skip"` with a `note` naming its follow-on. (Spine slice: `regression` is real, derived from `feature_index_verify.tally`; `security`/`stability`/`coverage` are skip+note pending their follow-ons.) This is the anti-half-measure invariant in artifact form.

## Met-or-split rule (close guard)

"Met-ness" comes from the QA evidence verdict, NOT from checkbox state (a closing issue legitimately still shows unchecked boxes). The mechanical invariant: an unmet acceptance criterion must have a linked follow-on issue. Inputs: the issue's acceptance-criteria checklist (parsed) + whether a follow-on references it (`gh issue list --search "in:body #N"`) + the `qa.json` verdict.

Fallback: an issue with no machine-checkable checklist is ALLOWED with a warning (do not block legitimate closures on format variance).

## WARN-first -> enforce graduation

Both the FEATURE_INDEX regression ABORT and the close guard sit on the seal control path. They ship WARN-first (exit 0; print findings) and graduate to blocking only after the false-positive rate is measured:
- `feature_index_verify`: blocks by default, `--warn-only` for rollout.
- `ac_close_guard`: WARN-only by default, `--enforce` reserved for V2.

When `gh` is unavailable the close guard records a skip (Phase 75 prerequisite-absent semantics), never a crash.
