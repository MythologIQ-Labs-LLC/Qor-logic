# Plan: Phase 186 - Provenance host autodetect inside Claude Code (GH #242)

**change_class**: feature

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-provenance-autodetect-2026-07-13.md (ledger entry #462, session `2026-07-13T0940-f515e2`); GH #242 host half. The model half DEFERS with the live enumeration as evidence (no ambient model signal exists; auto-detection would fabricate).

## Locked Decisions

- **LD-1: the signal family is empirical, most-specific first.**
  `grep -nE 'CLAUDE_PROJECT_DIR' qor/scripts/qor_platform.py -> 33` (the only current signal; ABSENT in live CLI sessions per the enumeration). `detect_host` gains: `CLAUDECODE` set, OR any env key starting `CLAUDE_CODE_`, OR `CLAUDE_PROJECT_DIR` -> "claude-code"; else "unknown". The future-hosts comment stays.
- **LD-2: fresh-detection fallback in the manifest builder.**
  `grep -nE 'def _detect_host' qor/scripts/ai_provenance.py -> 61` reads only the cached platform marker; when that yields "unknown", fall back to `qor_platform.detect_host()` directly (ImportError-guarded as today). The one-time WARN fires only when BOTH paths yield unknown.
- **LD-3: model half deferred, honestly.**
  No live model signal exists (enumeration in the brief); `QOR_MODEL_FAMILY` remains the explicit channel and the WARN text is unchanged. Recorded on GH #242 at disposition.

## Phase 1: Signal family + fallback (TDD first)

### Affected Files

- tests/test_platform.py - ladder cases appended
- tests/test_ai_provenance_helper.py - fresh-fallback integration case appended
- qor/scripts/qor_platform.py - detect_host ladder per LD-1
- qor/scripts/ai_provenance.py - _detect_host fallback per LD-2

### Changes

`detect_host`: three-signal ladder with a comment citing the Phase 186 live enumeration. `_detect_host`: after the marker path resolves unknown, `from qor.scripts.qor_platform import detect_host; fresh = detect_host()` returned when not unknown.

### Unit Tests

- tests/test_platform.py::test_detect_host_claudecode_env - only `CLAUDECODE=1` set -> "claude-code" (red today)
- tests/test_platform.py::test_detect_host_claude_code_family_env - only `CLAUDE_CODE_ENTRYPOINT=cli` set -> "claude-code" (red today)
- tests/test_platform.py::test_detect_host_unknown_when_no_signals - all family vars cleared -> "unknown" (regression lock)
- tests/test_ai_provenance_helper.py::test_build_manifest_autodetects_host_without_marker - no platform marker, `CLAUDECODE=1` set: manifest host == "claude-code" and NO host WARN emitted (red today)

## Feature Inventory Touches

(empty -- provenance tooling)

## Definition of Done

### Deliverable: truthful host provenance in Claude Code

- **D1**: Gate manifests written inside a Claude Code session record `host: claude-code` without operator env setup, closing the false-unknown class this working session demonstrated on itself (GH #242 host half; model half deferred with evidence).
- **D2**: LD-1 ladder + LD-2 fallback; WARN only when both paths yield unknown.
- **D3**: Ledger entries for plan/audit/implement/seal; GH #242 disposition records the model deferral.
- **D4**: The two red-today ladder tests + the no-marker manifest integration test observe the behaviors; the live proof lands in this very session's subsequent gate writes.

## CI Commands

- `python -m pytest tests/test_platform.py tests/test_ai_provenance_helper.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
