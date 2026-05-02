# Procedural-fidelity check (Phase 58)

Phase 58 ships a static-analysis check at `/qor-substantiate` Step 4.6.6 that verifies the seal commit's surface coverage matches the doc-surface coverage rule. WARN-only at v1; deviations are appended as severity-2 events to the Process Shadow Genome but do NOT abort substantiate. Closes B23 (operator request from Phase 57 substantiate cycle, where the operator manually identified that `docs/SYSTEM_STATE.md`, `docs/operations.md`, and `docs/architecture.md` were not updated for Phase 57's gate_written observer surface).

## Applicability

Runs at `/qor-substantiate` Step 4.6.6 (between Step 4.6.5 Phase 56 secret-scan and Step 4.7 Phase 28 documentation integrity). Reads `.qor/gates/<session_id>/implement.json` and inspects `files_touched`. Forward-only enforcement starting Phase 58; pre-Phase-58 historical seals are not retroactively scanned.

## The four v1 deviation classes

The frozen `qor.scripts.procedural_fidelity.DEVIATION_CLASSES` catalog defines the v1 set:

### `doc-surface-uncovered`

**Detection signal**: seal commit's `files_touched` contains skill / script / doctrine / schema paths but does NOT update at least one of the four system-tier docs (`docs/SYSTEM_STATE.md`, `docs/operations.md`, `docs/architecture.md`, `docs/lifecycle.md`).

**Severity**: 2.

**Remediation**: amend the seal commit to update the relevant system-tier doc OR document an explicit override rationale in the seal report (e.g., "this phase only ships test-isolation infrastructure; no system-tier surface change"). Implementation: `_detect_doc_surface_coverage` in `qor/scripts/procedural_fidelity.py`.

### `missing-step` (v1 stub)

**Detection signal** (when implemented): a numbered step in the substantiate skill body mentions a specific file path, and the file is not in `files_touched`, and the step is not on the operator's `_MAY_SKIP` allowlist.

**Severity**: 3.

**v1 status**: stub returns `[]`. Implementation lands when the failure-mode catalog grows past doc-surface coverage.

### `ordering-drift` (v1 stub)

**Detection signal** (when implemented): a sequence of steps in the substantiate skill body mandates ordering A → B → C, but the seal commit's `files_touched` shows evidence of ordering B → A → C (e.g., gate artifact timestamps show inverse order).

**Severity**: 1.

**v1 status**: stub. Reserved for future ordering-drift detection.

### `argv-shape-divergence` (v1 stub)

**Detection signal** (when implemented): a numbered step invokes a CLI with an argv shape that does not match the script's actual `argparse` declaration.

**Severity**: 2.

**v1 status**: stub. Reserved for future argv-shape detection.

## Doc-surface coverage rule

When the seal commit's `files_touched` contains a path matching any of:
- `qor/skills/...` (skill body changes)
- `qor/scripts/...` (script module changes)
- `qor/references/doctrine-...` (doctrine changes)
- `qor/gates/schema/...` (gate schema changes)

THEN at least one of the following must also be in `files_touched`:
- `docs/SYSTEM_STATE.md`
- `docs/operations.md`
- `docs/architecture.md`
- `docs/lifecycle.md`

Threshold is **at-least-one**, not all-four. Different phases legitimately affect different doc surfaces; mandating all four would cause spurious deviations. Operator can override with documented rationale in the seal report when the override is genuine.

## Operator workflow on deviation

1. Substantiate completes (WARN posture; no abort).
2. Operator reviews `dist/procedural-fidelity.findings.json` after seal.
3. For each deviation:
   - **Genuine gap**: amend the next seal cycle's `files_touched` to include the missing system-tier doc update.
   - **False positive**: document the rationale in the next seal report's "Procedural Fidelity Override" section. Future phase may add a structured override schema.
4. Process Shadow Genome accumulates events; future phase may tighten WARN → BLOCK once false-positive rate is characterized.

## Phase 58 changes vs. ad-hoc operator review

Pre-Phase-58, doc-surface coverage was caught only when the operator manually reviewed the PR (e.g., Phase 57 substantiate cycle, where SYSTEM_STATE / operations / architecture omissions were caught only on user review of the PR diff). The procedural-fidelity check structurally surfaces the gap at seal time, with a JSONL audit trail in the Process Shadow Genome.

The check operates on the implement gate artifact's `files_touched` field — already a structured contract — rather than recomputing diffs at seal time. This makes the check fast (sub-second) and deterministic.

## Future extensions

- **`missing-step`**: walk the substantiate skill body, parse numbered steps that cite files, assert touched-set coverage.
- **`ordering-drift`**: check gate artifact timestamps for canonical ordering.
- **`argv-shape-divergence`**: AST-parse cited CLI invocations; cross-reference against `argparse` declarations in target scripts.
- **Runtime tracing** (out of scope for Phase 58): instrument `qor.scripts.shadow_process.append_event` calls per substantiate step to confirm runtime fidelity, not just static fidelity. Requires careful design to avoid execution overhead.
- **WARN → BLOCK escalation**: after the false-positive rate is characterized, tighten Step 4.6.6 to `|| ABORT` semantics matching Step 4.6.5 secret-scan.

## References

- `qor/scripts/procedural_fidelity.py` — implementation.
- `qor/skills/governance/qor-substantiate/SKILL.md` Step 4.6.6 — wiring.
- `qor/references/doctrine-shadow-genome-countermeasures.md` `SG-DocSurfaceUncovered-A` — countermeasure entry.
- `qor/scripts/shadow_process.append_event` — event sink.
- META_LEDGER Entry #191 (audit PASS) — gate-time codification.
- B23 entry in `docs/BACKLOG.md` — operator request that prompted this work.
