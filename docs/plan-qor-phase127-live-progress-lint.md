# Plan: LiveProgressInvariant detector — plan_live_progress_lint

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Ships the mechanical SG-FakeProgress-A detector deferred at #58 as `qor.scripts.plan_live_progress_lint`. It is a lexical scan over a target repo's frontend source (`.js/.jsx/.ts/.tsx`) for the four Live-Progress sub-rules, highest-confidence first: (1/2) fake-jump — a progress width set to a start (`0`/`0%`) and later to an end (`100`/`100%`) with no intermediate width write between; (3) a progress element with no event-stream subscription (`addEventListener`/`.on(`/`onmessage`/`EventSource`/`subscribe`); (4) a terminal-error branch touching progress UI with no dismiss/retry/close control. An inline `// qor:live-progress-ok` comment suppresses a region.
- non_goals: A full DOM/render-graph or runtime analysis; detecting progress correctness at runtime; flagging non-progress UI; replacing the audit Ghost-UI Live-Progress prose (this is the Step 0.6 pre-audit early catch; the binding VETO remains the audit pass).
- exclusions: Repos with no frontend source files (the lint is a no-op / disclosed-skip). Backend-only repos (like this one) produce zero findings.

## Open Questions

None. Patterns + the four sub-rules are fixed by SG-FakeProgress-A; the fake-jump rule is the deterministic core and the other two are bounded heuristics with an escape comment (FP containment per the prose-lint over-flag lesson). The `findings_categories` enum gains `live-progress-fake` (AC2), promoting the prose-only sub-tag to a schema value.

## Context

GH #156 (umbrella #147; follow-on to #58). PR #69 (v0.50.0) shipped the SG-FakeProgress-A doctrine + the `/qor-audit` Ghost-UI Live-Progress checklist text, but downgraded AC2 (`findings_categories` enum value) to prose-only and dropped AC3 (the mechanical `plan_live_progress_lint.py`). The rule is hand-enforceable only. This phase builds the detector + the enum value + behavioral tests.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/scripts` + schema + tests.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_plan_live_progress_lint.py` · test_descriptor: `plan_live_progress_lint flags the fake-jump (0%->100% no intermediate), missing-event-subscription, and error-without-dismiss patterns, and emits nothing for a progress UI with intermediate writes + event subscription + dismiss control`

## Phase 1: Detector + CLI (`qor/scripts/plan_live_progress_lint.py`)

### Affected Files

- `tests/test_plan_live_progress_lint.py` - NEW. Behavioral fixtures for the four sub-rules (see Unit Tests). Written first; red before the module exists.
- `qor/scripts/plan_live_progress_lint.py` - NEW. Lexical scan + `main(argv)` dispatchable via `qor-logic scripts plan_live_progress_lint`.

### Changes

```python
KNOWN_FINDING_KINDS = ("fake-jump", "no-event-subscription", "error-no-dismiss")
_FRONTEND_GLOBS = ("**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx")
_SUPPRESS = "qor:live-progress-ok"

@dataclass(frozen=True)
class ProgressFinding:
    kind: str
    file: str
    detail: str

def _width_writes(text: str) -> list[tuple[int, str]]:
    """(position, value) for each `...width = '<v>'` / `width: '<v>'` assignment."""

def detect_fake_jump(text: str) -> bool:
    """True when a start width (0 / 0%) is written and a later end width
    (100 / 100%) is written with NO intermediate (non-0, non-100) width write
    between them."""

def scan_text(text: str) -> list[ProgressFinding]:
    """Apply the 4 sub-rules to one file's text (suppressed by _SUPPRESS)."""

def scan_repo(base: Path) -> list[ProgressFinding]:
    """Walk frontend globs under base; aggregate scan_text. No-op when no
    frontend files exist."""

def main(argv: list[str] | None = None) -> int:
    """--repo-root PATH. Print findings; exit 1 on any finding, else 0 (WARN-only
    at Step 0.6 via `|| true`; backend-only repos exit 0)."""
```

De-complecting: pure per-text detection (`detect_fake_jump`, `scan_text`) is separate from the filesystem walk (`scan_repo`) and process/exit (`main`).

### Unit Tests

- `tests/test_plan_live_progress_lint.py::test_fake_jump_flagged` - text setting `progressBar.style.width = '0%'` then `... = '100%'` with no write between; `scan_text` returns a `fake-jump` finding.
- `::test_progress_with_intermediate_not_flagged` - same start/end but with `... = '40%'` and `... = '80%'` between; no `fake-jump`.
- `::test_missing_event_subscription_flagged` - a progress element writing width but no `addEventListener`/`.on(`/`onmessage`/`EventSource`/`subscribe`; returns `no-event-subscription`.
- `::test_event_subscription_clears` - same plus `socket.addEventListener('message', ...)`; no `no-event-subscription`.
- `::test_error_state_without_dismiss_flagged` - an `error`/`catch` branch touching the progress bar with no `dismiss`/`retry`/`close`/`onClick` nearby; returns `error-no-dismiss`.
- `::test_suppress_comment_clears` - fake-jump text with `// qor:live-progress-ok`; `scan_text` returns `[]`.
- `::test_scan_repo_skips_backend_only` - a tmp repo with only `.py` files; `scan_repo` returns `[]`.
- `::test_main_exit_1_on_finding` + `::test_main_exit_0_backend_only` - CLI exit codes over a tmp repo.

## Phase 2: Schema enum + audit wiring

### Affected Files

- `tests/test_plan_live_progress_lint.py` - add `test_findings_categories_has_live_progress_fake` (loads `audit.schema.json`, asserts the enum value).
- `qor/gates/schema/audit.schema.json` - add `live-progress-fake` to `findings_categories.items.enum` (AC2).
- `qor/scripts/findings_signature.py` - if it mirrors the enum, add the value so `UnmappedCategoryError` accepts it (otherwise no change).
- `qor/skills/governance/qor-audit/SKILL.md` - in the Live-Progress sub-pass, add the runnable Step 0.6 pre-audit invocation `qor-logic scripts plan_live_progress_lint --repo-root . || true`.

### Changes

Promote the `live-progress-fake` sub-tag to a real `findings_categories` enum value (was prose-only). Wire the detector into the pre-audit lint ladder as WARN-only (the binding VETO stays the Ghost-UI pass). Confirm `findings_signature` validation accepts the new value.

### Unit Tests

- `tests/test_plan_live_progress_lint.py::test_findings_categories_has_live_progress_fake` - `audit.schema.json` enum contains `live-progress-fake`.
- `tests/test_plan_live_progress_lint.py::test_audit_invokes_live_progress_lint` - read `qor-audit/SKILL.md`; assert it names `plan_live_progress_lint`.

## Definition of Done

### Deliverable: live-progress detector

- **D1**: the SG-FakeProgress-A fake-jump / no-subscription / error-no-dismiss patterns are mechanically detectable at the pre-audit layer; backend-only repos are unaffected.
- **D2**: `qor/scripts/plan_live_progress_lint.py` with `detect_fake_jump`, `scan_text`, `scan_repo`, `main`; dispatchable as `qor-logic scripts plan_live_progress_lint`.
- **D3**: `live-progress-fake` in `audit.schema.json` enum; audit SKILL.md Step 0.6 invocation; META_LEDGER seal entry; version bump.
- **D4**: `tests/test_plan_live_progress_lint.py::test_fake_jump_flagged` + `::test_progress_with_intermediate_not_flagged` + `::test_findings_categories_has_live_progress_fake` + `::test_scan_repo_skips_backend_only`.

## CI Commands

- `python -m pytest tests/test_plan_live_progress_lint.py -q` — detector + enum + wiring.
- `python -m qor.cli scripts plan_live_progress_lint --repo-root .` — backend-only repo: zero findings, exit 0.
- `python -m pytest tests/test_findings_signature.py -q` — enum addition does not break category validation.
- `python -m pytest -q` — full suite green before substantiate.
