# Plan: Phase 5 — Cross-Repo Shadow Genome Collector

**Status**: Active (scope-limited)
**Author**: QoreLogic Governor
**Date**: 2026-04-15
**Scope**: Sweep shadow-process logs across multiple Qor-using repos; pool unaddressed events; open a single consolidated GitHub issue on threshold breach; delegate per-repo `addressed=true` flipping back to each repo's own tooling.
**Base spec**: `docs/plan-qor-migration-final.md` §Phase 5

## Open Questions

None. Decisions settled:
- Cross-repo writes: delegated via subprocess — collector reads state, calls per-repo tools to mutate state
- Config: `~/.qor/repos.json` (or `$QOR_CONFIG` override)
- Issue: one consolidated issue per sweep, opened against `meta_repo`
- Missing repo paths: warning, non-fatal
- Scheduling: documented only (Task Scheduler / cron); not configured

## Deliverables

### 1. `qor/scripts/create_shadow_issue.py` — `--flip-only` mode (additive)

Existing script gains a `--flip-only <URL>` flag. When set:
- Skip `gh auth status` check
- Skip `gh issue create`
- Read target events from `--events <ids>` or marker
- Update matching events to `addressed=true`, `addressed_reason="issue_created"`, `issue_url=<URL>`
- Remove `.qor/remediate-pending` if present

This lets the collector reuse the per-repo flipping logic without each repo opening its own duplicate issue.

### 2. `qor/scripts/collect_shadow_genomes.py`

Python 3.11 stdlib + `jsonschema` (runtime) + subprocess.

Library:
- `load_config(path: Path | None = None) -> dict` — reads `$QOR_CONFIG` or `~/.qor/repos.json`
- `sweep_one(repo: dict) -> list[dict]` — subprocess check_shadow_threshold in repo; read updated log; return unaddressed events tagged with `source_repo`
- `sweep_all(config: dict) -> list[dict]` — calls `sweep_one` per enabled repo; aggregates; logs warning on missing paths
- `build_issue_body(events: list[dict], threshold: int) -> str` — grouped by `source_repo`, severity breakdown
- `dispatch(events: list[dict], meta_repo: str) -> str` — `gh issue create` against meta_repo; returns URL
- `flip_per_repo(url: str, events: list[dict]) -> None` — group by source_repo; subprocess `create_shadow_issue.py --flip-only <url> --events <ids>` per repo

CLI:
- `collect` (default) — run full sweep + pool + maybe-issue + flip
- `dry-run` — sweep + pool; print summary; don't create issue or flip
- `config-show` — print effective config

Config schema (`qor/gates/schema/repos_config.schema.json`):
```json
{
  "version": "1",
  "meta_repo": "MythologIQ-Labs-LLC/Qor-logic",
  "repos": [
    {"path": "G:/MythologIQ/Qorelogic", "name": "qor-logic", "enabled": true}
  ],
  "threshold": 10,
  "stale_days": 90
}
```

### 3. `qor/gates/schema/repos_config.schema.json`

New schema validated by `jsonschema` in the collector.

### 4. `tests/test_collect.py`

- `test_load_config_from_env` — `QOR_CONFIG` env var path wins over `~/.qor/repos.json`
- `test_config_schema_accepts_valid`
- `test_config_schema_rejects_missing_required`
- `test_sweep_one_returns_unaddressed_tagged` — fixture repo with 2 unaddressed events → both returned with `source_repo`
- `test_sweep_one_missing_repo_logs_warning_returns_empty`
- `test_sweep_one_skips_disabled_repos`
- `test_sweep_all_pools_multi_repo` — 2 repo fixtures → combined list preserves source
- `test_build_issue_body_groups_by_repo`
- `test_threshold_trips_globally_not_per_repo` — two repos each sev 5 → combined 10 trips; neither alone would
- `test_dispatch_calls_gh_correctly` — mocked subprocess; correct args; returns URL
- `test_flip_per_repo_groups_invocations` — mocked subprocess; one call per source_repo
- `test_flip_only_mode_updates_events_without_gh` — integration with create_shadow_issue.py
- `test_flip_only_preserves_other_events`

### 5. Docs update: `qor/skills/governance/qor-shadow-process/SKILL.md`

Add a "Cross-repo aggregation" section describing `collect_shadow_genomes.py` and scheduling pointers.

## Constraints

- Python 3.11+ stdlib + `jsonschema` (already runtime) + subprocess
- Atomic writes via `os.replace()` (delegated to shadow_process)
- **No direct writes to foreign repos** — all state mutation happens via subprocess to the target repo's own scripts
- Issue body format is stable (tests assert grouping) but content is advisory; actual gh API response is what we trust for URL

## Success Criteria

- [ ] `~/.qor/repos.json` schema validates the example config in the plan
- [ ] `collect-shadow-genomes.py dry-run` runs against a 2-repo fixture, prints pooled summary
- [ ] Threshold globally pooled: 2 repos × severity 5 each trips; 2 repos × severity 3 each does not
- [ ] `--flip-only` mode in `create_shadow_issue.py` skips gh call and updates events correctly
- [ ] All 13 collect tests pass
- [ ] Full suite 91/91 (11 compile + 18 shadow + 25 gates + 24 platform + 13 collect)
- [ ] Drift clean; ledger chain intact
- [ ] Committed + pushed

## CI Commands

```bash
python -m pytest tests/test_collect.py -v
python qor/scripts/collect_shadow_genomes.py --help
```
