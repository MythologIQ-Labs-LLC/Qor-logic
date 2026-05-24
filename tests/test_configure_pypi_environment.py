"""Phase 101 (GH #118 P0): unit tests for the pypi env-config PUT-body factory.

No live gh-api calls; pure factory tests on the script's deterministic builders.
"""
from __future__ import annotations

import pytest

from qor.scripts import configure_pypi_environment as cpe


def test_build_put_body_includes_reviewer_requirement():
    body = cpe.build_put_body([12345], ["User"])
    reviewers = body.get("reviewers")
    assert isinstance(reviewers, list) and len(reviewers) >= 1
    assert reviewers[0] == {"type": "User", "id": 12345}


def test_build_put_body_disables_protected_branches_uses_custom_policy():
    body = cpe.build_put_body([12345], ["User"])
    policy = body["deployment_branch_policy"]
    assert policy["protected_branches"] is False
    assert policy["custom_branch_policies"] is True


def test_build_put_body_includes_self_review_prevention():
    body = cpe.build_put_body([12345], ["User"])
    assert body["prevent_self_review"] is True


def test_build_put_body_idempotent():
    """Calling with the same inputs must produce equal dicts (no hidden state)."""
    a = cpe.build_put_body([1, 2], ["User", "Team"])
    b = cpe.build_put_body([1, 2], ["User", "Team"])
    assert a == b


def test_build_put_body_rejects_mismatched_arg_lengths():
    with pytest.raises(AssertionError):
        cpe.build_put_body([1, 2], ["User"])


def test_build_put_body_rejects_empty_reviewer_list():
    with pytest.raises(AssertionError):
        cpe.build_put_body([], [])


def test_build_branch_policy_body_restricts_to_tag_refs():
    policy = cpe.build_branch_policy_body()
    assert policy["type"] == "tag"
    assert policy["name"] == "v*.*.*"
