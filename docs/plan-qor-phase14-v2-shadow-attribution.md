## Phase 14 v2 — Shadow Attribution (remediation of Entry #31 VETO)

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Branch**: `phase/14-shadow-attribution`
**Supersedes**: `docs/plan-qor-phase14-shadow-attribution.md` (VETO'd — Entry #31)

## Open Questions

Two discoveries from the V-1 grounding sweep (Step 2b) that deviate from the dialogue-agreed scope (c) "defer `gate_chain.py` as read-only no-op":

1. `qor/scripts/gate_chain.py:100` and `qor/scripts/qor_audit_runtime.py:66` both call `shadow_process.append_event(event)` without attribution. These are **writer call sites**, not read-only. `qor_audit_runtime.py` was not in the audit's enumerated 5 scripts (it does not reference the literal `PROCESS_SHADOW_GENOME` string — it calls the function directly). Scope is expanded to include both. `gate_override` events (gate_chain) and audit-emitted events (qor_audit_runtime) both attribute **UPSTREAM** (gate/bundle logic and audit logic are Qor-logic artifacts).
2. `gate_writes:` frontmatter has **no runtime parser** (grep: only `qor/scripts/legacy/compile-*.py` reference it; no production consumer). V-5 resolution is doctrinal only — YAML list syntax is chosen for readability; no parser-tolerance test is needed because no parser exists. If a future consumer is written, its acceptance test becomes additive then.

Both surfaced here; proceeding under the same plan.

## Track A — Attribution doctrine + upstream file (closes V-4)

### Affected Files

- `qor/references/doctrine-shadow-attribution.md` (new) — classification criteria
- `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` (new, empty starter with frontmatter comment)

### Changes

`doctrine-shadow-attribution.md` (6 sections):

1. **Purpose** — why two files exist; collector reads UPSTREAM only.
2. **UPSTREAM classification** — failure implicates a Qor-logic artifact: skill prompt text, doctrine rule, gate/bundle logic, helper script behavior, reference pattern. Worked example: "agent produced an orphan file because `qor-implement` Step 4 did not check entry-point import chain."
3. **LOCAL classification** — failure implicates consumer codebase, LLM-intrinsic behavior (hallucination, context loss), or integration-site wiring. Worked example: "agent misspelled a project-specific variable name; not attributable to Qor-logic skill text."
4. **Ambiguity tiebreak** — if unclear, default LOCAL; re-classify only if a Qor-logic artifact change would have prevented the failure.
5. **File routing** — UPSTREAM → `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`; LOCAL → `docs/PROCESS_SHADOW_GENOME.md`.
6. **Out of scope** — `docs/SHADOW_GENOME.md` (narrative VETO failure-pattern log) is unchanged and not subject to attribution classification. Literal phrase `out of scope` + filename required (closes V-4).

Starter `PROCESS_SHADOW_GENOME_UPSTREAM.md`: header + comment noting purpose and link to `doctrine-shadow-attribution.md`.

## Track B — Skill wiring, 4 skills (closes V-2)

### Affected Files

- `qor/skills/governance/qor-shadow-process/SKILL.md` — classification step + dual-file `gate_writes`
- `qor/skills/governance/qor-audit/SKILL.md` — Step 6 narrative clarification (unchanged behavior)
- `qor/skills/memory/track-shadow-genome.md` — reference doctrine + dual files
- `qor/skills/meta/qor-meta-track-shadow/SKILL.md` — reference doctrine + dual files

### Changes

`qor-shadow-process/SKILL.md`:

- Add classification step in body: "Before appending, classify attribution per `qor/references/doctrine-shadow-attribution.md`. UPSTREAM → `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`. LOCAL → `docs/PROCESS_SHADOW_GENOME.md`. When in doubt, LOCAL."
- `gate_writes` frontmatter → YAML list:
  ```yaml
  gate_writes:
    - docs/PROCESS_SHADOW_GENOME.md
    - docs/PROCESS_SHADOW_GENOME_UPSTREAM.md
  ```

`qor-audit/SKILL.md` Step 6: add one line noting that narrative `SHADOW_GENOME.md` entries are out of scope for the collector (narrative, not structured); no behavior change.

`track-shadow-genome.md` + `qor-meta-track-shadow/SKILL.md`: insert one paragraph in each referencing `doctrine-shadow-attribution.md` + both file paths. Agents invoking either skill must classify before logging.

## Track C — `shadow_process.py` classification-aware API (closes V-1)

### Affected Files

- `qor/scripts/shadow_process.py`

### Changes

Add module constants:

```python
LOCAL_LOG_PATH = REPO_ROOT / "docs" / "PROCESS_SHADOW_GENOME.md"
UPSTREAM_LOG_PATH = REPO_ROOT / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md"
LOG_PATH = LOCAL_LOG_PATH  # deprecated alias; retained for existing test/caller paths
```

Add helper:

```python
def log_path_for(attribution: Literal["UPSTREAM", "LOCAL"]) -> Path:
    if attribution == "UPSTREAM":
        return UPSTREAM_LOG_PATH
    if attribution == "LOCAL":
        return LOCAL_LOG_PATH
    raise ValueError(f"Invalid attribution: {attribution!r}")
```

Update `append_event` signature (option b from dialogue — keyword-only `attribution`):

```python
def append_event(
    event: dict,
    *,
    attribution: Literal["UPSTREAM", "LOCAL"] | None = None,
    log_path: Path | None = None,
) -> str:
    if log_path is None:
        if attribution is None:
            raise ValueError("append_event requires attribution=... or log_path=...")
        log_path = log_path_for(attribution)
    # existing body unchanged
```

Rationale: keyword-only prevents positional misorder; `log_path=` override retained so tests continue to work with `tmp_path`; `ValueError` when both omitted fails loud (Rule 4 enforcement).

Add dual-file reader + id-to-source map:

```python
def read_all_events() -> list[dict]:
    return read_events(LOCAL_LOG_PATH) + read_events(UPSTREAM_LOG_PATH)

def id_source_map() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for e in read_events(LOCAL_LOG_PATH):
        out[e["id"]] = LOCAL_LOG_PATH
    for e in read_events(UPSTREAM_LOG_PATH):
        out[e["id"]] = UPSTREAM_LOG_PATH
    return out
```

## Track D — Collector w/ explicit fallback + warning (closes V-3)

### Affected Files

- `qor/scripts/collect_shadow_genomes.py`

### Changes

Replace `SHADOW_LOG_REL = "docs/PROCESS_SHADOW_GENOME.md"` with:

```python
UPSTREAM_LOG_REL = "docs/PROCESS_SHADOW_GENOME_UPSTREAM.md"
LEGACY_LOG_REL = "docs/PROCESS_SHADOW_GENOME.md"
```

Per-repo read — explicit conditional (no ambiguity):

```python
upstream = repo_root / UPSTREAM_LOG_REL
legacy = repo_root / LEGACY_LOG_REL
if upstream.exists():
    log = upstream
elif legacy.exists() and shadow_process.read_events(legacy):
    log = legacy
    print(
        f"WARN: {repo}: only legacy log present; events pending classification "
        f"to upstream doctrine.",
        file=sys.stderr,
    )
else:
    return []  # zero events, graceful
events = shadow_process.read_events(log)
```

Replaces v1's self-contradicting "single-line edit" + "fallback" wording.

## Track E — Downstream writer callers (closes V-1 residual)

### Affected Files

- `qor/scripts/gate_chain.py` (writer: `gate_override` sev-1 events)
- `qor/scripts/qor_audit_runtime.py` (writer: audit-emitted events)
- `qor/scripts/check_shadow_threshold.py` (reader + writer: sweep + escalation)
- `qor/scripts/create_shadow_issue.py` (reader + writer: flip-resolved operations)

### Changes

**`gate_chain.py:100`** — `gate_override` events classify UPSTREAM (gate/bundle logic is Qor-logic infrastructure):

```python
return shadow_process.append_event(event, attribution="UPSTREAM")
```

**`qor_audit_runtime.py:66`** — audit-emitted events classify UPSTREAM (audit machinery is Qor-logic infrastructure):

```python
return shadow_process.append_event(event, attribution="UPSTREAM")
```

**`check_shadow_threshold.py`** — switch to dual-file read; split write-back by id source:

- Replace `shadow_process.read_events(args.log)` default path with `shadow_process.read_all_events()` when `--log` not given (retain `--log` override for tests).
- Replace `shadow_process.write_events(updated, args.log)` with per-file split using `id_source_map()`:
  ```python
  src_map = shadow_process.id_source_map()
  local = [e for e in updated if src_map.get(e["id"]) == shadow_process.LOCAL_LOG_PATH]
  upstream = [e for e in updated if src_map.get(e["id"]) == shadow_process.UPSTREAM_LOG_PATH]
  shadow_process.write_events(local, shadow_process.LOCAL_LOG_PATH)
  shadow_process.write_events(upstream, shadow_process.UPSTREAM_LOG_PATH)
  ```
- `--log <path>` override retained: when given, scans that single file only.

**`create_shadow_issue.py`** — same pattern applied to `flip_events_only`, `mark_resolved`, and the main flow's `mark_addressed → write_events` sequence. `--log` override retained.

## Track F — Tests (TDD; written first)

### `tests/test_shadow_attribution.py` (new, 9 tests)

- `test_doctrine_shadow_attribution_exists` — file at `qor/references/doctrine-shadow-attribution.md`.
- `test_doctrine_shadow_attribution_defines_both_classes` — body contains literal substrings `UPSTREAM` and `LOCAL`.
- `test_doctrine_shadow_attribution_has_worked_examples` — ≥2 occurrences of substring `Worked example`.
- `test_doctrine_declares_narrative_log_out_of_scope` — body contains `out of scope` + `SHADOW_GENOME.md` (closes V-4).
- `test_upstream_file_exists` — `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` exists.
- `test_log_path_for_upstream` — `shadow_process.log_path_for("UPSTREAM")` returns `UPSTREAM_LOG_PATH`.
- `test_log_path_for_local` — `shadow_process.log_path_for("LOCAL")` returns `LOCAL_LOG_PATH`.
- `test_append_event_requires_attribution_or_log_path` — `ValueError` when both omitted (Rule 4 interdiction).
- `test_collector_warns_on_legacy_only` — when only legacy file has events, collector emits stderr containing `legacy log present` (closes V-3).

### `tests/test_shadow.py` (2 tests added)

- `test_append_event_classifies_upstream` — `append_event(event, attribution="UPSTREAM")` writes to `UPSTREAM_LOG_PATH`; readable via `read_events(UPSTREAM_LOG_PATH)`; absent from `LOCAL_LOG_PATH`.
- `test_id_source_map_distinguishes_files` — event appended to each file reports correct source path via `id_source_map()`.

### `tests/test_skill_doctrine.py` (3 tests added)

- `test_shadow_process_skill_documents_attribution` — `qor-shadow-process/SKILL.md` body references `doctrine-shadow-attribution.md` or literal `UPSTREAM`.
- `test_shadow_process_skill_documents_both_log_files` — body references both `PROCESS_SHADOW_GENOME.md` and `PROCESS_SHADOW_GENOME_UPSTREAM.md`.
- `test_shadow_tracking_skills_reference_attribution_doctrine` — `track-shadow-genome.md` and `qor-meta-track-shadow/SKILL.md` both reference `doctrine-shadow-attribution.md` (closes V-2).

### `tests/test_collect.py` (1 test added)

- `test_collector_reads_upstream_file` — when both files present, collector reads UPSTREAM; events from LOCAL not pooled.

## Affected Files (summary)

### New (3)
- `qor/references/doctrine-shadow-attribution.md`
- `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`
- `tests/test_shadow_attribution.py`

### Modified — skills (4)
- `qor/skills/governance/qor-shadow-process/SKILL.md`
- `qor/skills/governance/qor-audit/SKILL.md`
- `qor/skills/memory/track-shadow-genome.md`
- `qor/skills/meta/qor-meta-track-shadow/SKILL.md`

### Modified — scripts (5)
- `qor/scripts/shadow_process.py`
- `qor/scripts/collect_shadow_genomes.py`
- `qor/scripts/gate_chain.py`
- `qor/scripts/qor_audit_runtime.py`
- `qor/scripts/check_shadow_threshold.py`
- `qor/scripts/create_shadow_issue.py`

### Modified — tests (3)
- `tests/test_shadow.py` (+2)
- `tests/test_skill_doctrine.py` (+3)
- `tests/test_collect.py` (+1)

## Constraints

- **No changes to narrative `docs/SHADOW_GENOME.md`** (doctrine §6 declares it out of scope).
- **Tests before code** for `test_shadow_attribution.py` and the 2 new `test_shadow.py` entries.
- **Reliability**: pytest 2x consecutive identical results before commit.
- **W-1 literal-keyword discipline**: doctrine strings match test substrings verbatim (`UPSTREAM`, `LOCAL`, `Worked example`, `out of scope`).
- **Rule 4 (Rule = Test)**: every interdiction has a test. `append_event` attribution-required → `test_append_event_requires_attribution_or_log_path`. Collector legacy warning → `test_collector_warns_on_legacy_only`.
- **`attribution` keyword-only** on `append_event` — prevents positional misorder, preserves `log_path=` test overrides.
- **`gate_writes:` YAML list** — no runtime parser exists (verified); doctrinal convention only.

## Success Criteria

- [ ] Doctrine has 6 sections; all literal-match tests green.
- [ ] Upstream starter file exists.
- [ ] 4 skills reference doctrine + both files.
- [ ] `shadow_process.py`: `LOCAL_LOG_PATH`, `UPSTREAM_LOG_PATH`, `log_path_for()`, `append_event(attribution=...)`, `read_all_events()`, `id_source_map()` all present.
- [ ] Collector reads UPSTREAM; legacy fallback emits the expected stderr line.
- [ ] 4 downstream callers classify correctly; 2 read+writer callers handle dual-file split.
- [ ] Tests: +9 attribution + 2 shadow + 3 skill_doctrine + 1 collect = **+15 new**. Baseline 202 → **217 passing**, skipped unchanged.
- [ ] `check_variant_drift.py` clean after `BUILD_REGEN=1`.
- [ ] `ledger_hash.py verify docs/META_LEDGER.md` → chain valid.
- [ ] Substantiation: `0.3.0 → 0.4.0`; annotated tag `v0.4.0`.

## CI Commands

```bash
python -m pytest tests/test_shadow_attribution.py tests/test_shadow.py tests/test_skill_doctrine.py tests/test_collect.py -v
python -m pytest tests/
BUILD_REGEN=1 python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
git tag --list 'v*' | tail -3
```
