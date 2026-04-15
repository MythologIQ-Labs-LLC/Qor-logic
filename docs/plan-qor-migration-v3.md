# Plan: Qor SSoT Migration — v3 (Remediation Deltas)

**Status**: Draft (post-v2 VETO remediation)
**Author**: QoreLogic Governor
**Date**: 2026-04-15
**Supersedes**: `docs/plan-qor-migration-v2.md` (v2, VETO — Ledger #13)
**Base plan**: v2 sections stand unchanged unless listed below
**Gate artifact for**: `/qor-audit`, `/qor-implement`

## Open Questions

None. User decisions resolved pre-draft:
- Hearthlink agents (5): **DELETE** (project no longer active)
- Generic engineering specialists (7): move to `qor/vendor/agents/`
- `ql-*` → `qor-*` prefix rename applied during migration (consistent with commit 806e359)
- `qor-ux-evaluator` category: `sdlc/`

## 1. Remediation Index (from v2 audit §12)

| # | Violation | Resolved by | Delta § |
|---|---|---|---|
| V-1 | `jsonschema` dev-vs-runtime contradiction | Reclassified as runtime | §2 |
| V-2 | Subagent mapping undefined | Mapping table added | §3 |
| V-3..V-5 | `tests/`, `tests/fixtures/`, pytest config orphans | Declared in structure, assigned Phase 0 | §4 |
| V-6 | `qor/dist/variants/codex/` empty-dir strategy | `.gitkeep` committed | §5 |
| V-7 | Entry #13 content_hash subject | Migration manifest file | §6 |
| V-8 | Severity-blind stale expiry | Severity-gated (≥3 never expires) | §7 |
| V-9 | session_id collision risk | `<UTC-ISO-min>-<6-hex>` | §8 |
| V-10 | No path-rebase test | Added | §9 |
| V-11 | No severity-gated expiry test | Added | §9 |
| V-12 | No live platform probe test | Added (integration-marked) | §9 |

## 2. V-1 — Dependency reclassification

**Affected**: v2 §4 "Dependencies"

Replaces v2 §4 with:

- **Python 3.11+** — stdlib modules for all scripts (runtime)
- **`jsonschema`** — runtime dep (used by `qor/scripts/validate_gate_artifact.py` invoked on every gate artifact write; dev-time tests also consume it). Pinned in `pyproject.toml` `[project.dependencies]`. Justification vs vanilla: schema validation across 7 artifact types with `$ref` resolution and format checks is ~300 lines hand-written; `jsonschema` is a single declarative import.
- **`pytest`** — dev dep (`[project.optional-dependencies].dev`)
- **`gh` CLI** — runtime system dep; `create_shadow_issue.py` validates `gh auth status` at startup

## 3. V-2 — Agent Mapping Table

**Affected**: v2 Phase 1 (adds `§1.B Agent Mapping` before "Unit tests")

Verified count: 25 files in `ingest/subagents/` (`ls ingest/subagents/ | wc -l` → 25).

| Source (`ingest/subagents/`) | Destination | Rename |
|---|---|---|
| `ql-governor.md` | `qor/agents/governance/qor-governor.md` | ql→qor |
| `ql-judge.md` | `qor/agents/governance/qor-judge.md` | ql→qor |
| `ql-specialist.md` | `qor/agents/sdlc/qor-specialist.md` | ql→qor |
| `ql-strategist.md` | `qor/agents/sdlc/qor-strategist.md` | ql→qor |
| `ql-fixer.md` | `qor/agents/sdlc/qor-fixer.md` | ql→qor |
| `ql-ux-evaluator.md` | `qor/agents/sdlc/qor-ux-evaluator.md` | ql→qor |
| `ql-technical-writer.md` | `qor/agents/memory/qor-technical-writer.md` | ql→qor |
| `project-planner.md` | `qor/agents/sdlc/project-planner.md` | — |
| `documentation-scribe.md` | `qor/agents/memory/documentation-scribe.md` | — |
| `learning-capture.md` | `qor/agents/memory/learning-capture.md` | — |
| `agent-architect.md` | `qor/agents/meta/agent-architect.md` | — |
| `system-architect.md` | `qor/agents/meta/system-architect.md` | — |
| `build-doctor.md` | `qor/agents/meta/build-doctor.md` | — |
| `accessibility-specialist.md` | `qor/vendor/agents/accessibility-specialist.md` | — |
| `code-reviewer.md` | `qor/vendor/agents/code-reviewer.md` | — |
| `devops-engineer.md` | `qor/vendor/agents/devops-engineer.md` | — |
| `tauri-launcher.md` | `qor/vendor/agents/tauri-launcher.md` | — |
| `ui-correction-specialist.md` | `qor/vendor/agents/ui-correction-specialist.md` | — |
| `ultimate-debugger.md` | `qor/vendor/agents/ultimate-debugger.md` | — |
| `voice-integration-specialist.md` | `qor/vendor/agents/voice-integration-specialist.md` | — |
| `hearthlink-backend-dev.md` | **DELETE** | — |
| `hearthlink-frontend-dev.md` | **DELETE** | — |
| `hearthlink-skill-framework.md` | **DELETE** | — |
| `hearthlink-skill-template.md` | **DELETE** | — |
| `hearthlink-ui-ux-designer.md` | **DELETE** | — |

Totals: 13 to `qor/agents/` (5 sdlc, 3 memory, 3 meta, 2 governance), 7 to `qor/vendor/agents/`, 5 deleted. Sum: 25 ✓.

Added unit test:
- `tests/test_agent_inventory.py::test_mapping_is_exhaustive` — every `ingest/subagents/*.md` has a dispositon; no source file is unaccounted for
- `tests/test_agent_inventory.py::test_no_hearthlink_survives` — all five deleted post-migration

## 4. V-3..V-5 — Test infrastructure declared

**Affected**: v2 §1 Target Structure, Phase 0

Additions to §1 structure:

```
tests/
  fixtures/
    trivial_task/            (Phase 8)
    repos/                   (Phase 5 — cross-repo collector fixtures)
    skill_samples/           (Phase 1 — canonical skill fixtures for compile tests)
  integration/               (pytest mark: integration)
  test_*.py                  (assigned to phases per v2)

pyproject.toml               (Phase 0)
```

Phase 0 additions:
- Create `pyproject.toml` with `[build-system]`, `[project]`, `[project.dependencies] = ["jsonschema>=4"]`, `[project.optional-dependencies].dev = ["pytest>=8"]`, `[tool.pytest.ini_options] = {markers = ["integration: live probes, opt-in via -m integration"], testpaths = ["tests"]}`
- Create empty `tests/` and `tests/fixtures/` directories (`.gitkeep` in each)
- `.gitignore` adds `.qor/`, `.qor/override.log`, `__pycache__/`, `.pytest_cache/`

## 5. V-6 — Codex empty-dir strategy

**Affected**: v2 Phase 2

Amendment: `qor/dist/variants/codex/` contains a committed `.gitkeep` file. Compile script is idempotent: writes `.gitkeep` on every run if `TARGETS["codex"]` emit is a no-op. This keeps the directory present in-tree (signaling the stub is intentional, not missing) without requiring content.

Added unit test:
- `tests/test_compile.py::test_codex_stub_writes_gitkeep` — after compile, `qor/dist/variants/codex/.gitkeep` exists and no other files

## 6. V-7 — Entry #13 content_hash subject

**Affected**: v2 Phase 1.5

Amendment: Entry #13 and Entry #14 each hash a **generated manifest file** (not the plan, not a Merkle root — one concrete artifact per entry).

- `docs/migration-manifest-pre.json` — written before Phase 1 file moves; content:
  ```json
  {
    "schema_version": "1",
    "generated_ts": "ISO-8601",
    "paths": [
      {"path": "kilo-code/qor-audit/SKILL.md", "sha256": "<hash>"},
      ...
    ]
  }
  ```
  Enumerates every file slated for migration at pre-move path with its SHA256.
- Entry #13's `content_hash` = `sha256(migration-manifest-pre.json)`.
- `docs/migration-manifest-post.json` — written after Phase 1 moves; same schema, new paths.
- Entry #14's `content_hash` = `sha256(migration-manifest-post.json)`.
- Path-rebase map in ledger: `{old_path: new_path}` derived by zipping pre/post manifests by file-content-hash (identical content → rebased path). Files whose content changed during move (none should, but captured defensively) appear in a "content_modified" bucket and fail Phase 1.5 validation.

Added unit test:
- `tests/test_ledger_hash.py::test_manifest_hash_reproducible` — same directory state produces identical manifest hash across runs

## 7. V-8 — Severity-gated stale expiry

**Affected**: v2 Phase 4 `addressed` state machine

Amendment to transition rules:

- `false → true (issue_created)` — any severity, when threshold trips
- `false → true (resolved_without_issue)` — any severity, operator explicit action via `qor-remediate`
- `false → true (stale_expired)` — **severity 1 or 2 only**, after 90 days without triggering threshold
- **Severity ≥ 3** (regression, hallucination, degradation) **never stale-expires**; persists in unaddressed state until remediated or issued
- When collector sweep encounters severity-≥3 entries older than 90 days unaddressed, it emits an independent shadow-process event: `event_type=aged_high_severity_unremediated`, severity=5 — self-escalating to ensure high-severity decay becomes its own high-severity event

Added unit tests:
- `tests/test_shadow.py::test_severity_gated_stale_expiry` — severities 1-2 expire at 90d, severities 3-5 do not
- `tests/test_shadow.py::test_aged_high_severity_self_escalates` — sev-5 event at day 91 produces aged_high_severity_unremediated event

## 8. V-9 — Collision-resistant session_id

**Affected**: v2 Phase 3

Amendment: `session_id = <UTC_ISO_MIN>-<6hex>` where `6hex = secrets.token_hex(3)` (Python stdlib, 24 bits of entropy per minute → collision probability < 1e-6 for two concurrent sessions). Session ID is stable for the duration of a single user-driven workflow:
- Generated on first Qor skill invocation per session
- Cached to `$QOR_SESSION` env var (set by the skill)
- Subsequent skills read `$QOR_SESSION`; regenerate only if unset

Example: `2026-04-15T14:23-a3f9c2`

Added unit test:
- `tests/test_gates.py::test_session_id_collision_probability` — generate 10k session IDs in same minute, assert zero collisions

## 9. V-10..V-12 — Added validation tests

**Affected**: v2 Phase 8

Additions:

- `tests/test_ledger_path_rebase.py::test_historical_entry_verifiable_via_rebase_map`
  - Scenario: historical Entry #5 references path `kilo-code/qor-audit/SKILL.md` with known content_hash
  - Post-migration, same file lives at `qor/skills/governance/qor-audit/SKILL.md`
  - Rebase map resolves old → new; content re-hashing at new path matches Entry #5's stored content_hash
- `tests/test_shadow.py::test_severity_gated_stale_expiry` (see §7)
- `tests/integration/test_platform_live.py::test_detect_against_live_session` — pytest mark `integration`; opt-in via `pytest -m integration`; probes actual session environment (skipped in default CI run)

## 10. Unchanged from v2

All v2 sections not referenced above stand as-is: Phase 0 (minus additions in §4), Phase 1 (plus §3 mapping), Phase 1.5 (plus §6 clarification), Phase 2 (plus §5), Phase 3 (plus §8), Phase 4 (plus §7), Phase 5, Phase 6, Phase 7, Phase 8 (plus §9), §2 Traceability, §5 Risks.

## 11. Success criteria (delta)

v2 §6 criteria retained, plus:
- [ ] All 10 v2-audit remediation items resolved (see §1 index)
- [ ] Agent mapping table exhaustive: every `ingest/subagents/*.md` has a disposition
- [ ] `tests/` infrastructure (pyproject.toml, directories, markers) declared and committed in Phase 0
- [ ] Codex stub dir contains `.gitkeep`
- [ ] Entry #13 and #14 content_hashes resolve to committed manifest files
- [ ] Stale expiry differentiates severity; high-severity aging triggers self-escalation event
- [ ] Session IDs collision-resistant (10k-concurrent-same-minute test passes)

## 12. CI commands for plan validation

```bash
# From repo root, after implementation
python -m pytest tests/ -v                                  # all unit tests
python -m pytest tests/ -m integration                      # integration tests (opt-in)
python qor/scripts/check_variant_drift.py                   # exit 0 on clean
python qor/scripts/ledger_hash.py --verify docs/META_LEDGER.md  # chain verification
grep -r "kilo-code/qor-\|deployable state\|processed/\|compiled/" docs/ --exclude-dir=archive  # empty
grep -rn "hearthlink" qor/ || echo "clean"                  # no hearthlink survives in qor/
```
