# Plan: External-reviewer subprocess bridge (Option B)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: external-reviewer bridge
  home: qor/skills/governance/qor-audit/references/adversarial-mode.md

**boundaries**:
- limitations: The bridge dispatches the existing #50 reviewer I/O contract (`adversarial-mode.md`) to an operator-configured external command via subprocess (reviewer-input JSON on stdin, reviewer-output JSON on stdout). It does not bundle a specific reviewer (Codex etc.), parse free-form text, or run the reviewer in-process. The command is resolved from `.qorlogic/config.json` (`external_reviewer.command`, an argv list).
- non_goals: An env-var override (operator chose config-file only); streaming/interactive review; auto-installing a reviewer; changing the reviewer I/O schema; making Option B mandatory (the Phase 87 auto-dispatch mandate is unchanged).
- exclusions: Hosts with no `.qorlogic/config.json` or no `external_reviewer.command` field fall back to in-harness review (the existing solo path + `capability_shortfall`); a configured-but-unavailable/timing-out/invalid-output command also falls back (never crashes the audit).

## Open Questions

None. Config mechanism resolved: `.qorlogic/config.json` `external_reviewer.command` (argv list); transport is stdin/stdout JSON; any resolution/dispatch failure degrades to graceful fallback.

## Context

GH #160 (umbrella #147; follow-on to #50). #50 (PR #63, v0.47.0) shipped Option B's specification: Step 1.b, the reviewer input/output schema (`adversarial-mode.md`), and the Phase 87 proactive mandate. The **subprocess bridge** to a genuinely independent reviewer was left documented-but-unimplemented ("Status: Contract-only specification"). Option B can be enforced as a manual/in-harness procedure but cannot dispatch to an external process. This phase ships the bridge. (Direct motivation: this development session's solo author-audit nearly shipped a duplicate module — the exact author-momentum failure independent review exists to catch.)

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/` + skills + tests, not `src/`.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_external_reviewer.py` · test_descriptor: `external_reviewer.run_external_review returns status=ok with the parsed reviewer verdict when a stub command is configured, and status=fallback (no crash) when the command is absent / errors / times out / returns invalid JSON`

## Phase 1: Bridge logic + CLI (`qor/scripts/external_reviewer.py`)

### Affected Files

- `tests/test_external_reviewer.py` - NEW. Behavioral tests using a stub reviewer script (see Unit Tests). Written first; red before the module exists.
- `qor/scripts/external_reviewer.py` - NEW. Config resolution + subprocess dispatch + output validation + `main(argv)`.

### Changes

```python
@dataclass(frozen=True)
class ReviewOutcome:
    status: str            # "ok" | "fallback"
    reason: str            # human-readable (e.g. "no reviewer configured", "timeout")
    review: dict | None    # the validated reviewer-output object when status == "ok"

def resolve_reviewer_command(config_path: Path) -> list[str] | None:
    """Read `.qorlogic/config.json` -> external_reviewer.command (argv list).
    None when the file/field is absent or malformed (tolerant parse, mirrors
    qor.tone._config_tone)."""

def validate_review_output(obj: object) -> bool:
    """True iff obj matches the adversarial-mode output contract: dict with a
    list `critiques`, numeric `confidence`, str `model`, str `ts`."""

def dispatch_review(review_input: dict, command: list[str], *, timeout: float = 120.0) -> dict | None:
    """Run command (list-form argv, no shell), writing json.dumps(review_input)
    to stdin; parse stdout as JSON; return it iff validate_review_output passes.
    None on nonzero exit, TimeoutExpired, OSError, or invalid/!contract JSON."""

def run_external_review(review_input: dict, config_path: Path, *, timeout: float = 120.0) -> ReviewOutcome:
    """Single entry point. Resolve command; if None -> ReviewOutcome("fallback",
    "no reviewer configured", None). Else dispatch; failure -> ReviewOutcome(
    "fallback", <reason>, None); success -> ReviewOutcome("ok", "", review)."""

def main(argv: list[str] | None = None) -> int:
    """--config PATH --input PATH: run_external_review and print the outcome as
    JSON to stdout. Exit 0 always (fallback is a valid outcome the audit acts on,
    not a process error)."""
```

De-complecting: config resolution, output validation, subprocess dispatch, and the orchestrating `run_external_review` are separate units; `main` is the only side-effecting/process layer. Fallback is a value (`ReviewOutcome`), never an exception.

### Unit Tests

- `tests/test_external_reviewer.py::test_resolve_command_from_config` - write `.qorlogic/config.json` with `{"external_reviewer": {"command": ["py", "r.py"]}}`; `resolve_reviewer_command` returns `["py", "r.py"]`.
- `::test_resolve_command_absent_returns_none` - no config file -> None; config without the field -> None; malformed JSON -> None.
- `::test_validate_review_output_accepts_contract` - a dict with `critiques=[]`, `confidence=0.5`, `model="x"`, `ts="..."` -> True; missing `critiques` -> False.
- `::test_dispatch_review_parses_stub_verdict` - write a stub script that reads stdin and prints a valid output JSON; `dispatch_review(input, [sys.executable, stub])` returns the parsed dict with the stub's `critiques`.
- `::test_dispatch_review_none_on_invalid_json` - stub prints `not json`; returns None.
- `::test_dispatch_review_none_on_nonzero_exit` - stub exits 1; returns None.
- `::test_dispatch_review_none_on_timeout` - monkeypatch `subprocess.run` to raise `TimeoutExpired`; returns None (no flaky real sleep).
- `::test_run_external_review_fallback_when_unconfigured` - empty tmp config dir; `run_external_review` returns `ReviewOutcome(status="fallback", ...)`, `review is None`.
- `::test_run_external_review_ok_with_stub` - config points at the stub; returns `status="ok"` and `review["critiques"]` matches the stub.
- `::test_main_prints_outcome_json` - `main(["--config", cfg, "--input", inp])` prints JSON containing `"status"`; returns 0.

## Phase 2: Audit wiring + reference

### Affected Files

- `tests/test_external_reviewer_wiring.py` - NEW. Prompt-contract assertions on qor-audit SKILL.md + adversarial-mode.md.
- `qor/skills/governance/qor-audit/SKILL.md` - in Step 1.a, after `should_run_adversarial_mode`, document the bridge: when an external reviewer is configured, dispatch via `qor.scripts.external_reviewer.run_external_review`; on `status == "fallback"` log the existing `capability_shortfall` and proceed solo; on `status == "ok"` synthesize the returned critiques. Keep the existing solo fallback intact.
- `qor/skills/governance/qor-audit/references/adversarial-mode.md` - flip "Status: Contract-only specification" to note the Phase 123 subprocess bridge (`qor.scripts.external_reviewer`), the `.qorlogic/config.json` `external_reviewer.command` config, and the graceful-fallback contract.
- `qor/dist/variants/**` - regenerated via `qor-logic compile`.

### Changes

The bridge is additive: `should_run_adversarial_mode` (codex-plugin path) is unchanged; the config-driven bridge is the general mechanism, and absence of configuration reproduces today's solo behavior exactly. No change to the Phase 87 auto-dispatch mandate.

### Unit Tests

- `tests/test_external_reviewer_wiring.py::test_audit_references_bridge_with_fallback` - read `qor-audit/SKILL.md`; assert it names `external_reviewer` AND `capability_shortfall` within the Step 1 region (dispatch + documented fallback).
- `::test_adversarial_mode_doc_marks_bridge_shipped` - read `adversarial-mode.md`; assert it no longer says "Contract-only specification" and names `qor.scripts.external_reviewer` + `external_reviewer.command`.

## Definition of Done

### Deliverable: external-reviewer subprocess bridge

- **D1**: /qor-audit can dispatch the reviewer-schema input to a configured external process and ingest its verdict, with graceful fallback to in-harness review.
- **D2**: `qor/scripts/external_reviewer.py` with `resolve_reviewer_command`, `validate_review_output`, `dispatch_review`, `run_external_review`, `main`; dispatchable as `qor-logic scripts external_reviewer`.
- **D3**: Step 1.a wiring + adversarial-mode.md flip; META_LEDGER seal entry; version bump; variants recompiled.
- **D4**: `tests/test_external_reviewer.py::test_run_external_review_ok_with_stub` + `::test_run_external_review_fallback_when_unconfigured` + `::test_dispatch_review_none_on_nonzero_exit` + `tests/test_external_reviewer_wiring.py::test_audit_references_bridge_with_fallback`.

## CI Commands

- `python -m pytest tests/test_external_reviewer.py tests/test_external_reviewer_wiring.py -q` — bridge + wiring.
- `python -m pytest -q` — full suite green before substantiate.
