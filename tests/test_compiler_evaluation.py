"""Phase 54 evaluation loop tests."""
from __future__ import annotations

import dataclasses
import json

import pytest

from qor.compiler.evaluation import (
    EvaluationResult,
    compare_against_intent,
    record_feedback,
    validate_output,
)
from qor.compiler.types import OutputContract, ParsedIntent


def test_evaluation_result_is_frozen():
    r = EvaluationResult(format_valid=True, format_error=None, drift_score=0.0,
                         drift_detected=False, matched_tokens=(), missing_tokens=())
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.drift_score = 1.0


def test_validate_output_markdown_always_accepts():
    ok, err = validate_output("anything goes", OutputContract(format="markdown"))
    assert ok is True
    assert err is None


def test_validate_output_text_always_accepts():
    ok, err = validate_output("free form text", OutputContract(format="text"))
    assert ok is True


def test_validate_output_json_accepts_well_formed():
    ok, err = validate_output('{"a": 1}', OutputContract(format="json"))
    assert ok is True
    assert err is None


def test_validate_output_json_rejects_malformed_with_error_message():
    ok, err = validate_output("{not json}", OutputContract(format="json"))
    assert ok is False
    assert err is not None
    assert "json parse error" in err


def test_compare_against_intent_full_overlap_zero_drift():
    intent = ParsedIntent(task_type="draft", user_goal="migration plan auth module")
    out = compare_against_intent(
        "Here is the migration plan for the auth module.",
        intent,
    )
    assert out.drift_score == 0.0
    assert out.drift_detected is False
    assert set(out.matched_tokens) >= {"migration", "plan", "auth", "module"}


def test_compare_against_intent_zero_overlap_full_drift():
    intent = ParsedIntent(task_type="draft", user_goal="migration plan auth module")
    out = compare_against_intent("Completely unrelated response about apples.", intent)
    assert out.drift_score == 1.0
    assert out.drift_detected is True
    assert "migration" in out.missing_tokens


def test_compare_against_intent_partial_overlap_below_threshold_flagged():
    intent = ParsedIntent(task_type="draft", user_goal="migration plan auth module marketplace install")
    # 1 of 6 long tokens matches
    out = compare_against_intent("migration topic only", intent)
    assert out.drift_detected is True


def test_compare_against_intent_short_tokens_excluded():
    intent = ParsedIntent(task_type="draft", user_goal="a be go is")
    out = compare_against_intent("response", intent)
    # All goal tokens are length <= 3; filtered out; goal_tokens set is empty.
    assert out.drift_score == 0.0
    assert out.drift_detected is False


def test_compare_against_intent_case_insensitive():
    intent = ParsedIntent(task_type="draft", user_goal="MIGRATION plan")
    out = compare_against_intent("migration PLAN ready", intent)
    assert out.drift_score == 0.0


def test_record_feedback_writes_jsonl_under_qor_evaluation(tmp_path):
    r = EvaluationResult(format_valid=True, format_error=None, drift_score=0.2,
                         drift_detected=False, matched_tokens=("foo",), missing_tokens=())
    path = record_feedback("sess-x", r, repo_root=tmp_path)
    assert path == tmp_path / ".qor" / "evaluation" / "sess-x.jsonl"
    assert path.exists()
    line = path.read_text(encoding="utf-8").strip()
    parsed = json.loads(line)
    assert parsed["drift_score"] == 0.2
    assert parsed["matched_tokens"] == ["foo"]


def test_record_feedback_appends_when_session_id_repeats(tmp_path):
    r1 = EvaluationResult(format_valid=True, format_error=None, drift_score=0.1,
                          drift_detected=False, matched_tokens=(), missing_tokens=())
    r2 = EvaluationResult(format_valid=True, format_error=None, drift_score=0.9,
                          drift_detected=True, matched_tokens=(), missing_tokens=())
    record_feedback("sess-y", r1, repo_root=tmp_path)
    record_feedback("sess-y", r2, repo_root=tmp_path)
    path = tmp_path / ".qor" / "evaluation" / "sess-y.jsonl"
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["drift_score"] == 0.1
    assert json.loads(lines[1])["drift_score"] == 0.9
