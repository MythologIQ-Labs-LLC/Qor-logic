# Plan: Phase 4 — Process Shadow Genome Automation

**Status**: Active (scope-limited; incremental post-SSoT tooling)
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Scope**: Automate the self-improvement loop: append events, compute threshold, trigger `/qor-remediate`, create GitHub issue, manage `addressed` state.
**Base spec**: `docs/plan-qor-migration-final.md` §Phase 4 (authoritative; this plan inherits all decisions, adds wiring)
**Ledger base**: Entry #20 (chain `6d52c2d1...`)

## Open Questions

None. All design decisions settled in the base spec or prior dialogue:
- Severity rubric: 1–5 (override, capability_shortfall, regression, hallucination, degradation)
- Threshold: 10 unaddressed severity points
- Stale expiry: 90 days, severities 1–2 only; sev ≥ 3 never expire
- Self-escalation idempotence: at-most-one `aged_high_severity_unremediated` per `source_entry_id`
- Issue repo: `MythologIQ-Labs-LLC/Qor-logic`
- `/qor-remediate` trigger: file marker (Option A) — `.qor/remediate-pending` written on breach

## Deliverables

### 1. `qor/gates/schema/shadow_event.schema.json`

JSON Schema for event validation. 11 fields per §Phase 4 schema. Used by both append helper and threshold checker.

### 2. `qor/scripts/shadow_process.py`

Library module:
- `append_event(event: dict, log_path: Path) -> str` — validates against schema, computes `id` as SHA256 of first 7 fields, appends as JSONL line via `os.replace` (atomic), returns id.
- `read_events(log_path: Path) -> list[dict]` — parses JSONL, returns list.
- `compute_id(event: dict) -> str` — stable id derivation.

Imported by skills and `check_shadow_threshold.py`.

### 3. `qor/scripts/check_shadow_threshold.py`

CLI executable:
- Load `docs/PROCESS_SHADOW_GENOME.md` via `shadow_process.read_events()`.
- **Stale sweep**: for each event, `severity ∈ {1,2}` and `addressed == false` and age > 90 days → flip to `addressed=true, addressed_reason="stale"`. Write back if any changed.
- **Aged-high-severity sweep**: for each `severity ≥ 3`, `addressed == false`, age > 90 days: if no existing event has `event_type == "aged_high_severity_unremediated"` AND `source_entry_id == this.id`, emit one such event (sev 5). Idempotent.
- **Threshold sum**: sum `severity` over `addressed == false` events.
- If sum ≥ 10: write `.qor/remediate-pending` marker file (JSON payload with breach summary + aggregated event ids); exit 10.
- Else: remove stale marker if present; exit 0.

### 4. `qor/scripts/create_shadow_issue.py`

CLI executable:
- Validate `gh auth status` (subprocess, capture). Fail fast if not authenticated.
- Accepts `--from-marker .qor/remediate-pending` (default) or explicit `--events <id>,<id>,...`.
- Builds issue body: severity table, event listing (ts, skill, event_type, severity, details), link to session id where applicable.
- Runs `gh issue create --repo MythologIQ-Labs-LLC/Qor-logic --title "..." --body-file - --label qor-shadow`.
- Captures returned URL.
- For each aggregated event: update `addressed=true, addressed_ts=now, addressed_reason="issue_created", issue_url=<url>`. Atomic rewrite of PROCESS_SHADOW_GENOME.md.
- Removes `.qor/remediate-pending`.

### 5. `tests/test_shadow.py`

Parameterized pytest suite:
- `test_threshold_sum_ignores_addressed`
- `test_severity_gated_stale_expiry` — sev 1,2 expire at 90d; sev 3,4,5 do not
- `test_aged_high_severity_self_escalates` — sev-5 event emitted for aged sev-3
- `test_aged_escalation_is_idempotent` — 2nd sweep produces no duplicate escalation
- `test_event_schema_validation_accepts_valid` / `_rejects_malformed`
- `test_marker_written_on_breach` + `test_marker_removed_when_under_threshold`
- `test_issue_creation_flips_addressed` — `gh` subprocess mocked via `monkeypatch`
- `test_event_id_deterministic` — identical events produce identical ids

### 6. `qor/skills/governance/qor-shadow-process/SKILL.md`

Update: remove "STUB" markers, document `append_event`, `check_shadow_threshold.py`, `create_shadow_issue.py`, and `.qor/remediate-pending` marker flow.

### 7. `pyproject.toml`

Reclassify `jsonschema>=4` from dev-only (current state: dev-only via `[project.optional-dependencies].dev`) to runtime: `[project].dependencies = ["jsonschema>=4"]`.

## Constraints

- **Python 3.11+ stdlib + jsonschema only.** No other runtime deps.
- **All atomic writes use `os.replace()`** (Windows-safe).
- **Schema validation at every write boundary.** Never trust caller input.
- **No changes to SSoT skill files** beyond `qor-shadow-process/SKILL.md`.

## Success Criteria

- [ ] `pytest tests/test_shadow.py -v` all pass
- [ ] `python qor/scripts/check_shadow_threshold.py` on current PROCESS_SHADOW_GENOME.md runs clean (existing sev-1 override is below threshold → exit 0, no marker written)
- [ ] `ledger_hash.py --verify` still passes (unchanged)
- [ ] `qor/skills/governance/qor-shadow-process/SKILL.md` no longer marked STUB
- [ ] jsonschema is a runtime dep in pyproject.toml
- [ ] Committed + pushed to origin/main

## CI commands

```bash
python -m pytest tests/test_shadow.py -v
python qor/scripts/check_shadow_threshold.py                  # exit 0 on current state
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md  # chain still valid
```
