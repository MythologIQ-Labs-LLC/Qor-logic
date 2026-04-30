"""Phase 22 Track A: Cedar-inspired policy engine tests."""
from __future__ import annotations

from qor.policy import (
    Condition,
    Constraint,
    Decision,
    EntityUID,
    EvalResult,
    Policy,
    Request,
    evaluate,
)
from qor.policy.parser import parse_policies, parse_policy


def test_entity_uid_creation():
    uid = EntityUID(type="Skill", id="qor-implement")
    assert uid.type == "Skill"
    assert uid.id == "qor-implement"
    assert str(uid) == 'Skill::"qor-implement"'


def test_request_creation():
    req = Request(
        principal=EntityUID("Skill", "qor-implement"),
        action=EntityUID("Action", "invoke"),
        resource=EntityUID("Gate", "plan-approved"),
        context={"verdict": "PASS"},
    )
    assert req.principal.type == "Skill"
    assert req.context["verdict"] == "PASS"


def test_decision_enum():
    assert Decision.ALLOW.value == "ALLOW"
    assert Decision.DENY.value == "DENY"
    assert Decision.ALLOW != Decision.DENY


def test_policy_creation():
    p = Policy(
        id="test_0",
        effect="permit",
        principal=Constraint(op="==", entity=EntityUID("Skill", "x")),
        action=Constraint(),
        resource=Constraint(),
        conditions=[Condition(lhs="resource.verdict", op="==", rhs="PASS")],
    )
    assert p.effect == "permit"
    assert len(p.conditions) == 1


def test_parser_permit_simple():
    text = '''permit (
      principal == Skill::"qor-implement",
      action == Action::"invoke",
      resource == Gate::"plan-approved"
    );'''
    policies = parse_policies(text)
    assert len(policies) == 1
    p = policies[0]
    assert p.effect == "permit"
    assert p.principal.entity.id == "qor-implement"
    assert p.action.entity.id == "invoke"
    assert p.resource.entity.id == "plan-approved"


def test_parser_forbid_with_when():
    text = '''forbid (
      principal,
      action == Action::"implement",
      resource == Gate::"plan"
    ) when { resource.verdict == "VETO" };'''
    policies = parse_policies(text)
    assert len(policies) == 1
    p = policies[0]
    assert p.effect == "forbid"
    assert p.principal.op is None  # unconstrained
    assert len(p.conditions) == 1
    assert p.conditions[0].rhs == "VETO"


def test_parser_unconstrained_principal():
    text = '''permit (
      principal,
      action == Action::"invoke",
      resource
    ) when { resource.registered == true };'''
    policies = parse_policies(text)
    p = policies[0]
    assert p.principal.op is None
    assert p.resource.op is None
    assert p.action.entity.id == "invoke"


def test_parser_in_constraint():
    text = '''permit (
      principal in Group::"admins",
      action == Action::"invoke",
      resource
    );'''
    policies = parse_policies(text)
    p = policies[0]
    assert p.principal.op == "in"
    assert p.principal.entity.type == "Group"
    assert p.principal.entity.id == "admins"


def test_evaluator_default_deny():
    req = Request(
        principal=EntityUID("Skill", "unknown"),
        action=EntityUID("Action", "invoke"),
        resource=EntityUID("Gate", "plan"),
    )
    result = evaluate(req, [])
    assert result.decision == Decision.DENY
    assert result.matching_policies == []


def test_evaluator_permit_match():
    req = Request(
        principal=EntityUID("Skill", "qor-implement"),
        action=EntityUID("Action", "implement"),
        resource=EntityUID("Gate", "plan"),
        context={},
    )
    entities = {
        'Gate::"plan"': {"verdict": "PASS"},
    }
    policy = Policy(
        id="gate_permit",
        effect="permit",
        principal=Constraint(),
        action=Constraint(op="==", entity=EntityUID("Action", "implement")),
        resource=Constraint(op="==", entity=EntityUID("Gate", "plan")),
        conditions=[Condition(lhs="resource.verdict", op="==", rhs="PASS")],
    )
    result = evaluate(req, [policy], entities=entities)
    assert result.decision == Decision.ALLOW
    assert "gate_permit" in result.matching_policies


def test_evaluator_forbid_overrides_permit():
    req = Request(
        principal=EntityUID("Skill", "qor-implement"),
        action=EntityUID("Action", "implement"),
        resource=EntityUID("Gate", "plan"),
    )
    entities = {
        'Gate::"plan"': {"verdict": "VETO"},
    }
    permit_policy = Policy(
        id="gate_permit",
        effect="permit",
        principal=Constraint(),
        action=Constraint(op="==", entity=EntityUID("Action", "implement")),
        resource=Constraint(op="==", entity=EntityUID("Gate", "plan")),
        conditions=[Condition(lhs="resource.verdict", op="==", rhs="PASS")],
    )
    forbid_policy = Policy(
        id="gate_forbid",
        effect="forbid",
        principal=Constraint(),
        action=Constraint(op="==", entity=EntityUID("Action", "implement")),
        resource=Constraint(op="==", entity=EntityUID("Gate", "plan")),
        conditions=[Condition(lhs="resource.verdict", op="==", rhs="VETO")],
    )
    result = evaluate(req, [permit_policy, forbid_policy], entities=entities)
    assert result.decision == Decision.DENY
    assert "gate_forbid" in result.matching_policies


def test_evaluator_condition_evaluation():
    """Boolean condition coercion: resource.registered == true."""
    req = Request(
        principal=EntityUID("Skill", "qor-plan"),
        action=EntityUID("Action", "invoke"),
        resource=EntityUID("Skill", "qor-plan"),
    )
    entities = {
        'Skill::"qor-plan"': {"registered": True, "has_frontmatter": True},
    }
    policy = Policy(
        id="admission",
        effect="permit",
        principal=Constraint(),
        action=Constraint(op="==", entity=EntityUID("Action", "invoke")),
        resource=Constraint(),
        conditions=[
            Condition(lhs="resource.registered", op="==", rhs="true"),
            Condition(lhs="resource.has_frontmatter", op="==", rhs="true"),
        ],
    )
    result = evaluate(req, [policy], entities=entities)
    assert result.decision == Decision.ALLOW


def test_cedar_forbids_prompt_injection_canary():
    """Phase 53: forbid rule for governance markdown with canary patterns.

    Loads `qor/policies/owasp_enforcement.cedar`, locates the prompt-injection
    forbid rule, and exercises it via the evaluator with a synthetic
    Code::"governance" resource entity.
    """
    from pathlib import Path

    cedar_path = (
        Path(__file__).resolve().parent.parent
        / "qor" / "policies" / "owasp_enforcement.cedar"
    )
    policies = parse_policies(cedar_path.read_text(encoding="utf-8"))

    assert any(
        p.effect == "forbid"
        and p.resource.entity is not None
        and p.resource.entity.type == "Code"
        and p.resource.entity.id == "governance"
        for p in policies
    ), 'owasp_enforcement.cedar must contain a Code::"governance" forbid rule'

    req = Request(
        principal=EntityUID("Author", "any"),
        action=EntityUID("Action", "commit"),
        resource=EntityUID("Code", "governance"),
    )

    entities_hit = {'Code::"governance"': {"has_prompt_injection_canary": True}}
    result_hit = evaluate(req, policies, entities=entities_hit)
    assert result_hit.decision == Decision.DENY

    entities_clean = {'Code::"governance"': {"has_prompt_injection_canary": False}}
    result_clean = evaluate(req, policies, entities=entities_clean)
    governance_forbid_matched = any(
        "governance" in pid.lower() or "prompt" in pid.lower()
        for pid in result_clean.matching_policies
    )
    assert not governance_forbid_matched, (
        "governance forbid must not match when has_prompt_injection_canary is False"
    )
