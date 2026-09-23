"""Bounded V1 tests for GH #501 governance applicability resolution."""
from __future__ import annotations

import pytest

from qor.scripts.governance_applicability import (
    ApplicabilityRule,
    GovernanceSource,
    OperationDescriptor,
    resolve_packet,
)


def _operation(**overrides: str) -> OperationDescriptor:
    values = {
        "operation_id": "op-1",
        "operation_type": "implement",
        "lifecycle_state": "EXECUTE",
        "artifact_type": "source",
        "subsystem": "engine",
        "change_class": "feature",
        "environment_relevance": "pre-deployment",
        "authority_ceiling": "implementation",
        "mutation_class": "code",
        "external_visibility": "internal",
    }
    values.update(overrides)
    return OperationDescriptor(**values)


def _source(
    stable_id: str,
    *,
    rule: ApplicabilityRule,
    posture: str = "required",
    freshness_state: str = "current",
    precedence: int = 10,
    rule_key: str = "",
    decision_token: str = "",
    superseded_by: str = "",
) -> GovernanceSource:
    return GovernanceSource(
        stable_id=stable_id,
        source_class="doctrine",
        authority_class="canonical",
        precedence=precedence,
        posture=posture,
        freshness_state=freshness_state,
        rules=(rule,),
        rule_key=rule_key,
        decision_token=decision_token,
        superseded_by=superseded_by,
    )


def _resolution(packet, stable_id: str):
    return next(r for r in packet.resolutions if r.stable_id == stable_id)


def test_ordinary_implementation_surfaces_implementation_and_excludes_runtime():
    operation = _operation()
    implementation = _source(
        "implementation-doctrine",
        rule=ApplicabilityRule("implementation", operation_types=("implement",)),
    )
    runtime = _source(
        "runtime-doctrine",
        rule=ApplicabilityRule("runtime", environment_relevance=("production",)),
    )

    packet = resolve_packet(operation, (runtime, implementation))

    assert _resolution(packet, "implementation-doctrine").disposition == "required"
    excluded = _resolution(packet, "runtime-doctrine")
    assert excluded.disposition == "excluded"
    assert excluded.reason == "no-rule-match:runtime"


def test_deployment_sensitive_operation_surfaces_release_and_operational_sources():
    operation = _operation(
        operation_type="deploy",
        lifecycle_state="PROMOTE",
        environment_relevance="production",
        authority_ceiling="deployment",
        mutation_class="external-state",
        external_visibility="public",
    )
    release = _source(
        "release-authority",
        rule=ApplicabilityRule(
            "release",
            operation_types=("deploy",),
            lifecycle_states=("PROMOTE",),
        ),
    )
    operational = _source(
        "operational-evidence",
        rule=ApplicabilityRule("operational", environment_relevance=("production",)),
        posture="advisory",
    )

    packet = resolve_packet(operation, (operational, release))

    assert _resolution(packet, "release-authority").disposition == "required"
    assert _resolution(packet, "operational-evidence").disposition == "advisory"


def test_governance_document_change_surfaces_freshness_and_excludes_runtime_ceremony():
    operation = _operation(
        operation_type="governance-doc",
        lifecycle_state="DECIDE",
        artifact_type="doctrine",
        subsystem="governance",
        change_class="docs",
        environment_relevance="none",
        authority_ceiling="planning",
        mutation_class="documentation",
    )
    freshness = _source(
        "governance-freshness",
        rule=ApplicabilityRule(
            "governance-doc",
            operation_types=("governance-doc",),
            subsystems=("governance",),
        ),
    )
    runtime = _source(
        "runtime-recovery",
        rule=ApplicabilityRule("runtime", environment_relevance=("production",)),
    )

    packet = resolve_packet(operation, (runtime, freshness))

    assert _resolution(packet, "governance-freshness").disposition == "required"
    assert _resolution(packet, "runtime-recovery").disposition == "excluded"


def test_resolver_never_upgrades_declared_advisory_posture():
    source = _source(
        "advisory-only",
        rule=ApplicabilityRule("all-implementation", operation_types=("implement",)),
        posture="advisory",
    )

    packet = resolve_packet(_operation(), (source,))

    assert _resolution(packet, "advisory-only").disposition == "advisory"


def test_source_with_no_applicability_rules_is_not_silently_global():
    source = GovernanceSource(
        stable_id="unclassified",
        source_class="doctrine",
        authority_class="canonical",
        precedence=10,
        posture="required",
        freshness_state="current",
        rules=(),
    )

    packet = resolve_packet(_operation(), (source,))

    result = _resolution(packet, "unclassified")
    assert result.disposition == "excluded"
    assert result.reason == "no-applicability-rules"


def test_stale_applicable_source_is_fail_visible():
    source = _source(
        "stale-source",
        rule=ApplicabilityRule("implementation", operation_types=("implement",)),
        freshness_state="stale",
    )

    result = _resolution(resolve_packet(_operation(), (source,)), "stale-source")

    assert result.disposition == "stale"
    assert result.matched_rule_ids == ("implementation",)


def test_superseded_applicable_source_names_successor():
    source = _source(
        "old-doctrine",
        rule=ApplicabilityRule("implementation", operation_types=("implement",)),
        freshness_state="superseded",
        superseded_by="new-doctrine",
    )

    result = _resolution(resolve_packet(_operation(), (source,)), "old-doctrine")

    assert result.disposition == "superseded"
    assert result.reason == "superseded-by:new-doctrine"


def test_higher_precedence_explicitly_shadows_lower_precedence_in_same_rule_domain():
    rule = ApplicabilityRule("implementation", operation_types=("implement",))
    lower = _source(
        "lower",
        rule=rule,
        precedence=10,
        rule_key="implementation-policy",
        decision_token="allow",
    )
    higher = _source(
        "higher",
        rule=rule,
        precedence=20,
        rule_key="implementation-policy",
        decision_token="allow",
    )

    packet = resolve_packet(_operation(), (lower, higher))

    assert _resolution(packet, "higher").disposition == "required"
    lower_result = _resolution(packet, "lower")
    assert lower_result.disposition == "excluded"
    assert lower_result.reason == "shadowed-by-higher-precedence:implementation-policy:20"


def test_same_precedence_conflict_is_ambiguous_not_best_effort_ranked():
    rule = ApplicabilityRule("implementation", operation_types=("implement",))
    allow = _source(
        "allow-source",
        rule=rule,
        rule_key="mutation-authority",
        decision_token="allow",
    )
    deny = _source(
        "deny-source",
        rule=rule,
        rule_key="mutation-authority",
        decision_token="deny",
    )

    packet = resolve_packet(_operation(), (deny, allow))

    assert _resolution(packet, "allow-source").disposition == "ambiguous"
    assert _resolution(packet, "deny-source").disposition == "ambiguous"


def test_same_decision_but_different_obligation_strength_is_ambiguous():
    rule = ApplicabilityRule("implementation", operation_types=("implement",))
    required = _source(
        "required-source",
        rule=rule,
        posture="required",
        rule_key="mutation-authority",
        decision_token="allow",
    )
    advisory = _source(
        "advisory-source",
        rule=rule,
        posture="advisory",
        rule_key="mutation-authority",
        decision_token="allow",
    )

    packet = resolve_packet(_operation(), (required, advisory))

    assert _resolution(packet, "required-source").disposition == "ambiguous"
    assert _resolution(packet, "advisory-source").disposition == "ambiguous"


def test_output_is_deterministic_independent_of_source_input_order():
    rule = ApplicabilityRule("implementation", operation_types=("implement",))
    a = _source("a-source", rule=rule, posture="advisory")
    b = _source("b-source", rule=rule)

    first = resolve_packet(_operation(), (b, a))
    second = resolve_packet(_operation(), (a, b))

    assert first == second
    assert tuple(r.stable_id for r in first.resolutions) == ("a-source", "b-source")


def test_duplicate_source_ids_fail_closed():
    rule = ApplicabilityRule("implementation", operation_types=("implement",))
    first = _source("duplicate", rule=rule)
    second = _source("duplicate", rule=rule, posture="advisory")

    with pytest.raises(ValueError, match="stable_id"):
        resolve_packet(_operation(), (first, second))


def test_invalid_source_metadata_fails_closed():
    rule = ApplicabilityRule("implementation", operation_types=("implement",))

    with pytest.raises(ValueError, match="posture"):
        _source("bad-posture", rule=rule, posture="mandatory")

    with pytest.raises(ValueError, match="superseded_by"):
        _source("bad-supersession", rule=rule, freshness_state="superseded")

    with pytest.raises(ValueError, match="decision_token"):
        _source("incomplete-conflict-metadata", rule=rule, rule_key="mutation-authority")
