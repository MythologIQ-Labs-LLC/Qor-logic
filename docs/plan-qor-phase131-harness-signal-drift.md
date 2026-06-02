# Plan: Confirm append_event moot + add SG-HarnessSignalDrift-A doctrine entry

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Closes the #138 residue (#165). AC1: a behavioral test proves `shadow_process.append_event` does NOT consume `QOR_SKILL_ACTIVE` — the recorded `skill` is the caller-supplied `event["skill"]` regardless of the env var — confirming the leak does not flow through it (no code change to `append_event`; it is genuinely moot). AC2: add the `SG-HarnessSignalDrift-A` doctrine entry under that name (the #138 harness-signal env-var leakage pattern + its shipped countermeasure), with a doc-contract test, rather than leaving it implicit.
- non_goals: Re-opening the #138 fix (already shipped in PR #144); changing `append_event` (the confirmation is that no change is needed); a runnable harness-signal lint (the pattern is closed by the existing context-manager fix; the doctrine entry records it).
- exclusions: n/a.

## Open Questions

None. `append_event` reads `event["skill"]` only (grep-confirmed: no `os.environ`/`getenv`/`QOR_SKILL_ACTIVE` in the module) — moot confirmed. Decision on AC2: ADD the named entry (the substantive, completeness-respecting closure) rather than fold it silently.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/references` + tests, not `src/`.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_harness_signal_drift.py` · test_descriptor: `append_event records the caller-supplied event['skill'] verbatim with QOR_SKILL_ACTIVE set to a different value (proves no env consumption); the SG-HarnessSignalDrift-A doctrine entry names the pattern + the moot append_event finding`

## Phase 1: append_event moot-confirmation test (#165 AC1)

### Affected Files

- `tests/test_harness_signal_drift.py` - NEW. Behavioral confirmation (see Unit Tests). Written first; it passes against the unchanged `append_event` (the point: prove no change is needed).

### Changes

No production code change. The test sets `QOR_SKILL_ACTIVE` in the environment to a sentinel that differs from the `skill` field passed in the event dict, calls `append_event` with a temp `log_path`, reads back the appended JSONL line, and asserts the recorded `skill` equals the event-dict value (not the env sentinel) — functionally proving `append_event` ignores the harness env signal.

### Unit Tests

- `tests/test_harness_signal_drift.py::test_append_event_ignores_qor_skill_active_env` - with `monkeypatch.setenv("QOR_SKILL_ACTIVE", "env-skill")`, call `append_event({... "skill": "param-skill" ...}, log_path=tmp.jsonl)`; read the JSONL line; assert `json.loads(line)["skill"] == "param-skill"`.
- `tests/test_harness_signal_drift.py::test_append_event_source_has_no_env_read` - import `qor.scripts.shadow_process` and assert (via `inspect.getsource(append_event)`) that the function body contains no `os.environ` / `getenv` / `QOR_SKILL_ACTIVE` reference (regression guard that the moot property holds).

## Phase 2: SG-HarnessSignalDrift-A doctrine entry (#165 AC2)

### Affected Files

- `tests/test_harness_signal_drift.py` - add the doc-contract test.
- `qor/references/doctrine-shadow-genome-countermeasures.md` - add the `SG-HarnessSignalDrift-A` entry: Pattern (a harness-provided signal — `QOR_SKILL_ACTIVE` env var set by one skill — leaks across the skill-boundary context and mislabels another skill's gate artifacts), Originating recurrence (#138; the env var persisted into a child skill's `write_gate_artifact`), Countermeasure (PR #144 context-manager scoping + `write_gate_artifact(skill=)` explicit param + active-phase reporter + restore-on-exit test; SHIPPED), and the **moot note** that `shadow_process.append_event` carries `skill` only as a JSONL data field and never consumes the env signal, so the leak does not flow through it (confirmed Phase 131; GH #165).

### Changes

Doctrine-only addition + the doc-contract test. The entry names the pattern explicitly so future harness-signal leaks have a catalogued countermeasure to cite, closing #165 AC2 with a real artifact rather than an implicit fold.

### Unit Tests

- `tests/test_harness_signal_drift.py::test_doctrine_has_harness_signal_drift_entry` - read `doctrine-shadow-genome-countermeasures.md`; assert it contains `SG-HarnessSignalDrift-A` AND names `QOR_SKILL_ACTIVE` AND records the `append_event` moot finding (so the doctrine cannot drift from the confirmed reality).

## Definition of Done

### Deliverable: #138 residue closed

- **D1**: `append_event`'s moot property is proven by test (not asserted in prose); the harness-signal-drift pattern is a named, catalogued doctrine entry.
- **D2**: `tests/test_harness_signal_drift.py` (3 tests); `SG-HarnessSignalDrift-A` in `doctrine-shadow-genome-countermeasures.md`. No `append_event` change (by design).
- **D3**: META_LEDGER seal entry; version bump.
- **D4**: `tests/test_harness_signal_drift.py::test_append_event_ignores_qor_skill_active_env` + `::test_doctrine_has_harness_signal_drift_entry`.

## CI Commands

- `python -m pytest tests/test_harness_signal_drift.py -q` — moot-confirmation + doc-contract.
- `python -m pytest -q` — full suite green before substantiate.
