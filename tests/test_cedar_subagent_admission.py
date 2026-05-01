"""Phase 55: Cedar admission rule end-to-end tests."""
from __future__ import annotations

from pathlib import Path

from qor.policy import Decision, EntityUID, Request, evaluate
from qor.policy.parser import parse_policies

REPO_ROOT = Path(__file__).resolve().parent.parent
CEDAR_PATH = REPO_ROOT / "qor" / "policies" / "skill_admission.cedar"


def _load_policies():
    return parse_policies(CEDAR_PATH.read_text(encoding="utf-8"))


def test_cedar_denies_when_tool_scope_exceeded():
    policies = _load_policies()
    req = Request(
        principal=EntityUID("Author", "x"),
        action=EntityUID("Action", "invoke"),
        resource=EntityUID("Skill", "qor-test"),
    )
    entities = {
        'Skill::"qor-test"': {
            "registered": True, "has_frontmatter": True,
            "actual_tool_invocations_exceed_scope": True,
            "actual_subagent_invocations_exceed_scope": False,
        },
    }
    result = evaluate(req, policies, entities=entities)
    assert result.decision == Decision.DENY


def test_cedar_denies_when_subagent_scope_exceeded():
    policies = _load_policies()
    req = Request(
        principal=EntityUID("Author", "x"),
        action=EntityUID("Action", "invoke"),
        resource=EntityUID("Skill", "qor-test"),
    )
    entities = {
        'Skill::"qor-test"': {
            "registered": True, "has_frontmatter": True,
            "actual_tool_invocations_exceed_scope": False,
            "actual_subagent_invocations_exceed_scope": True,
        },
    }
    result = evaluate(req, policies, entities=entities)
    assert result.decision == Decision.DENY


def test_cedar_forbid_does_not_match_when_scope_respected():
    """When neither scope-exceeded attribute is True, the new forbid rules
    must NOT match. Cedar default-deny still applies (the existing permit
    rule has a parser-incompatible `&&` clause that never matches), but the
    Phase 55 contract is that the forbid rules don't fire on clean input.
    """
    policies = _load_policies()
    req = Request(
        principal=EntityUID("Author", "x"),
        action=EntityUID("Action", "invoke"),
        resource=EntityUID("Skill", "qor-test"),
    )
    entities = {
        'Skill::"qor-test"': {
            "registered": True, "has_frontmatter": True,
            "actual_tool_invocations_exceed_scope": False,
            "actual_subagent_invocations_exceed_scope": False,
        },
    }
    result = evaluate(req, policies, entities=entities)
    # Phase 55 forbid rules must NOT contribute to matching_policies on clean input.
    forbid_match_ids = [
        pid for pid in result.matching_policies
        if pid != "policy_0"  # policy_0 is the pre-existing broken permit
    ]
    assert not forbid_match_ids, (
        f"Phase 55 forbid rules must not match clean input; got: {forbid_match_ids}"
    )


def test_cedar_admission_rule_uses_invoke_action():
    """Locate the new forbid rules; verify they target Action::"invoke"."""
    policies = _load_policies()
    forbid_rules = [p for p in policies if p.effect == "forbid"]
    assert forbid_rules, "expected at least one forbid rule"
    for rule in forbid_rules:
        assert rule.action.entity is not None
        assert rule.action.entity.type == "Action"
        assert rule.action.entity.id == "invoke"
