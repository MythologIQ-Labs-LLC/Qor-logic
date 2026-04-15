"""Tests for workflow-bundle contracts (Phase 12).

Bundles are markdown-only; their behavior is the contract documented in
SKILL.md frontmatter + body. Tests verify:
- Frontmatter declares required keys per workflow-bundles.md
- Phase / checkpoint counts match documented protocol
- Decomposition pointers reference real sub-bundles
- Constituent /qor-* references actually exist in the skills tree
"""
from __future__ import annotations

from pathlib import Path

import pytest

import bundle_runner as br

EXPECTED_BUNDLES = {
    "qor-deep-audit",
    "qor-deep-audit-recon",
    "qor-deep-audit-remediate",
    "qor-onboard-codebase",
    "qor-process-review-cycle",
}


def test_all_expected_bundles_present():
    found = {b.name for b in br.list_all_bundles()}
    missing = EXPECTED_BUNDLES - found
    assert not missing, f"Missing bundles: {missing}"


@pytest.mark.parametrize("bundle_name", sorted(EXPECTED_BUNDLES))
def test_bundle_frontmatter_complete(bundle_name):
    """Every bundle declares the required workflow-bundles.md keys."""
    bundles = [b for b in br.list_all_bundles() if b.name == bundle_name]
    assert len(bundles) == 1, f"Expected 1 {bundle_name}, found {len(bundles)}"
    b = bundles[0]
    assert b.type == "workflow-bundle"
    assert len(b.phases) >= 1
    assert isinstance(b.checkpoints, list)
    assert isinstance(b.budget, dict)
    assert "max_phases" in b.budget
    assert "abort_on_token_threshold" in b.budget


@pytest.mark.parametrize("bundle_name", sorted(EXPECTED_BUNDLES))
def test_bundle_phases_count_within_budget(bundle_name):
    """Declared phase count must not exceed budget.max_phases."""
    b = next(x for x in br.list_all_bundles() if x.name == bundle_name)
    assert len(b.phases) <= b.budget["max_phases"], (
        f"{bundle_name}: {len(b.phases)} phases declared but max_phases={b.budget['max_phases']}"
    )


def test_qor_deep_audit_decomposes_into_existing_subbundles():
    parent = next(x for x in br.list_all_bundles() if x.name == "qor-deep-audit")
    assert parent.decomposes_into == ["qor-deep-audit-recon", "qor-deep-audit-remediate"]
    found_names = {b.name for b in br.list_all_bundles()}
    for sub in parent.decomposes_into:
        assert sub in found_names, f"Decomposition target missing: {sub}"


def test_onboard_phase_order():
    b = next(x for x in br.list_all_bundles() if x.name == "qor-onboard-codebase")
    assert b.phases == ["research", "organize", "audit", "plan"]


def test_review_cycle_phase_order():
    b = next(x for x in br.list_all_bundles() if x.name == "qor-process-review-cycle")
    assert b.phases == ["shadow-sweep", "remediate", "audit"]


def test_review_cycle_has_checkpoints_for_phase_transitions():
    b = next(x for x in br.list_all_bundles() if x.name == "qor-process-review-cycle")
    # 3 phases => at least 2 checkpoints (after-1, after-2)
    assert len(b.checkpoints) >= 2


@pytest.mark.parametrize("bundle_name", sorted(EXPECTED_BUNDLES))
def test_bundle_references_existing_skills(bundle_name):
    """Every /qor-* trigger referenced in a bundle body must resolve to a real skill."""
    b = next(x for x in br.list_all_bundles() if x.name == bundle_name)
    refs = br.extract_skill_refs(b.body)
    # Drop self-reference
    refs.discard(f"/{b.name}")
    for ref in refs:
        skill_name = ref.lstrip("/")
        # Find any SKILL.md whose frontmatter name matches, OR a directory named that
        matches = br.find_skill_dirs(skill_name)
        assert matches, f"{bundle_name} references {ref} but no skill found"


def test_onboard_references_constituent_chain():
    b = next(x for x in br.list_all_bundles() if x.name == "qor-onboard-codebase")
    refs = br.extract_skill_refs(b.body)
    # Must explicitly delegate per its 4 phases
    expected = {"/qor-research", "/qor-organize", "/qor-audit", "/qor-plan"}
    missing = expected - refs
    assert not missing, f"qor-onboard-codebase missing constituent references: {missing}"


def test_review_cycle_references_constituents():
    b = next(x for x in br.list_all_bundles() if x.name == "qor-process-review-cycle")
    refs = br.extract_skill_refs(b.body)
    expected = {"/qor-remediate", "/qor-audit"}
    missing = expected - refs
    assert not missing, f"qor-process-review-cycle missing constituent references: {missing}"


def test_no_bundle_invokes_unrelated_bundle():
    """workflow-bundles.md anti-pattern: bundles invoking unrelated bundles -> context blowup.

    Allowed:
    - Parent bundle naming its decomposes_into sub-bundles
    - Sub-bundles in the same decomposition family naming each other
      (e.g., recon -> remediate handoff via prose)
    """
    bundles = br.list_all_bundles()
    bundle_names = {b.name for b in bundles}

    # Build sub-bundle -> parent map
    sub_to_parent: dict[str, str] = {}
    for b in bundles:
        for sub in b.decomposes_into:
            sub_to_parent[sub] = b.name

    for b in bundles:
        refs = br.extract_skill_refs(b.body)
        for ref in refs:
            target = ref.lstrip("/")
            if target not in bundle_names or target == b.name:
                continue
            # Allow parent -> sub-bundle (decomposition pointer)
            if target in b.decomposes_into:
                continue
            # Allow sibling sub-bundles (same parent)
            if sub_to_parent.get(b.name) and sub_to_parent.get(b.name) == sub_to_parent.get(target):
                continue
            # Allow sub-bundle -> parent (back-reference for context)
            if sub_to_parent.get(b.name) == target:
                continue
            pytest.fail(
                f"{b.name} body references unrelated bundle {ref}; bundles must not "
                f"invoke bundles outside their decomposition family"
            )


@pytest.mark.parametrize("bundle_name", sorted(EXPECTED_BUNDLES))
def test_bundle_body_mentions_workflow_bundles_md(bundle_name):
    """Per workflow-bundles.md doctrine, every bundle must reference the convention."""
    b = next(x for x in br.list_all_bundles() if x.name == bundle_name)
    assert "workflow-bundles.md" in b.body, (
        f"{bundle_name} should reference qor/gates/workflow-bundles.md"
    )


@pytest.mark.parametrize("bundle_name", sorted(EXPECTED_BUNDLES))
def test_bundle_budget_threshold_in_valid_range(bundle_name):
    b = next(x for x in br.list_all_bundles() if x.name == bundle_name)
    threshold = b.budget.get("abort_on_token_threshold")
    assert threshold is not None
    assert 0.5 <= threshold <= 0.95, (
        f"{bundle_name}: abort_on_token_threshold={threshold} out of sensible range 0.5-0.95"
    )
