# Plan: Phase 54 — Prompt compiler evaluation loop

**change_class**: feature

**doc_tier**: system

**originating_remediation**: GH #39 sub-phase 5 (final sub-phase per docs/roadmap-prompt-compiler.md)

**terms_introduced**:
- term: validate_output
  home: qor/compiler/evaluation.py
- term: compare_against_intent
  home: qor/compiler/evaluation.py
- term: EvaluationResult
  home: qor/compiler/evaluation.py
- term: record_feedback
  home: qor/compiler/evaluation.py

**boundaries**:
- limitations:
  - V1 format validation: markdown is always accepted; json must `json.loads` cleanly; text is always accepted. Schema validation deferred to V2 (would require jsonschema dependency).
  - V1 drift detection is a word-overlap heuristic: each token in `ParsedIntent.user_goal` longer than 3 chars is checked for membership in the output (case-insensitive). Score = matched / total. Threshold of 0.3 yields the `drift_detected` flag.
  - V1 feedback record is JSONL written to `.qor/evaluation/<session_id>.jsonl`. Schema-validated via inline dataclass serialization.
- non_goals:
  - LLM-as-judge evaluation. V1 is deterministic-only.
  - Cost/latency telemetry (separate concern).

## Open Questions
None. This is the final sub-phase closing GH #39.

## Phase 1: evaluation module

### Affected Files
- `qor/compiler/evaluation.py` — NEW.
- `qor/compiler/__init__.py` — re-export `validate_output`, `compare_against_intent`, `EvaluationResult`, `record_feedback`.
- `tests/test_compiler_evaluation.py` — NEW.

### Changes
```python
@dataclass(frozen=True)
class EvaluationResult:
    format_valid: bool
    format_error: str | None
    drift_score: float
    drift_detected: bool
    matched_tokens: tuple[str, ...]
    missing_tokens: tuple[str, ...]

def validate_output(output_text: str, contract: OutputContract) -> tuple[bool, str | None]: ...
def compare_against_intent(output_text: str, intent: ParsedIntent, *, threshold: float = 0.3) -> EvaluationResult: ...
def record_feedback(session_id: str, result: EvaluationResult, repo_root: str | Path = ".") -> Path: ...
```

### Unit Tests
- `test_evaluation_result_is_frozen`
- `test_validate_output_markdown_always_accepts`
- `test_validate_output_text_always_accepts`
- `test_validate_output_json_accepts_well_formed`
- `test_validate_output_json_rejects_malformed_with_error_message`
- `test_compare_against_intent_full_overlap_zero_drift`
- `test_compare_against_intent_zero_overlap_full_drift`
- `test_compare_against_intent_partial_overlap_below_threshold_flagged`
- `test_compare_against_intent_short_tokens_excluded`
- `test_compare_against_intent_case_insensitive`
- `test_record_feedback_writes_jsonl_under_qor_evaluation`
- `test_record_feedback_appends_when_session_id_repeats`

## Phase 2: doctrine + roadmap (final close)

### Affected Files
- `docs/roadmap-prompt-compiler.md` — mark Phase 54 done; mark roadmap COMPLETE.
- `qor/references/doctrine-prompt-compilation.md` — update §V1 scope → all 5 sub-phases delivered; condense V2+ deferrals list.
- `tests/test_roadmap_phase_54_marked_done.py` — NEW.

## CI Commands
- `python -m pytest tests/test_compiler_evaluation.py tests/test_roadmap_phase_54_marked_done.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
