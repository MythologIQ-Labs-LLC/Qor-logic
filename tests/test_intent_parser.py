"""Phase 50 intent_parser behavior tests."""
from __future__ import annotations

import pytest

from qor.compiler.intent_parser import parse_intent


def test_parse_intent_detects_draft_verb():
    out = parse_intent("Draft a migration plan for the auth module.")
    assert out.task_type == "draft"


def test_parse_intent_detects_implement_verb():
    out = parse_intent("Implement a Markdown parser using stdlib only.")
    assert out.task_type == "implement"


def test_parse_intent_detects_review_verb():
    out = parse_intent("Review the supplied PR for security issues.")
    assert out.task_type == "review"


def test_parse_intent_detects_analyze_verb():
    out = parse_intent("Analyze the failure-rate trend over the last 30 days.")
    assert out.task_type == "analyze"


def test_parse_intent_detects_explain_verb():
    out = parse_intent("Explain how the cycle-count escalator works.")
    assert out.task_type == "explain"


def test_parse_intent_detects_summarize_verb():
    out = parse_intent("Summarize the open issues by category.")
    assert out.task_type == "summarize"


def test_parse_intent_falls_back_to_draft_when_no_keyword_matches():
    out = parse_intent("Hello there, can you help with something?")
    assert out.task_type == "draft"


def test_parse_intent_extracts_must_constraint():
    out = parse_intent("Draft a plan. Must use stdlib only.")
    assert any("stdlib only" in c for c in out.explicit_constraints)


def test_parse_intent_extracts_do_not_constraint():
    out = parse_intent("Implement the parser. Do not introduce new dependencies.")
    assert any("not introduce new dependencies" in c.lower() for c in out.explicit_constraints)


def test_parse_intent_extracts_avoid_constraint():
    out = parse_intent("Review the code. Avoid suggesting style refactors.")
    assert any("avoid" in c.lower() for c in out.explicit_constraints)


def test_parse_intent_user_goal_strips_leading_verb():
    out = parse_intent("Draft a migration plan.")
    assert "Draft" not in out.user_goal


def test_parse_intent_user_goal_preserves_body_when_no_verb_match():
    out = parse_intent("Hello there")
    assert out.user_goal == "Hello there"


def test_parse_intent_leaves_v1_deferred_fields_empty():
    out = parse_intent("Implement a feature. Must be fast.")
    assert out.implicit_constraints == ()
    assert out.required_outputs == ()
    assert out.context_dependencies == ()
    assert out.ambiguity_flags == ()
    assert out.risk_hints == ()


def test_parse_intent_returns_no_constraints_when_none_present():
    out = parse_intent("Draft a basic plan with no special rules.")
    assert out.explicit_constraints == ()


def test_parse_intent_handles_empty_string():
    out = parse_intent("")
    assert out.task_type == "draft"
    assert out.user_goal == ""
    assert out.explicit_constraints == ()
