"""Phase 257: an executable answer to "is any check still pending?".

Closes the severity-3 `merge-on-green` gate_override of 2026-08-17, whose remedy
-- "never admin-merge with any check pending" -- was a question a person had to
answer by reading a list, at the moment of least patience in the cycle.

Every test drives `classify` over payloads in the shape `gh pr checks --json
name,state,bucket` actually returns, so none touches the network.
"""
from __future__ import annotations

from qor.scripts.merge_readiness import Readiness, classify


def _check(name: str, bucket: str, state: str) -> dict:
    return {"name": name, "bucket": bucket, "state": state}


def _passing(n: int) -> list[dict]:
    return [_check(f"test-{i}", "pass", "SUCCESS") for i in range(n)]


WAITING_PUBLISH = _check("publish", "pending", "WAITING")


def test_running_check_blocks():
    """The recorded failure: PR #344 admin-merged while a run was still going."""
    checks = _passing(15) + [_check("provenance-attest", "pending", "IN_PROGRESS")]

    assert classify(checks) is Readiness.RUNNING


def test_waiting_check_does_not_block():
    """The measured shape of every recent pull request here.

    `publish` waits on a deployment-environment approval granted only after
    merge, so it is permanently pending by design. Treating it as a blocker
    would refuse every merge this repository will ever make.
    """
    checks = _passing(16) + [WAITING_PUBLISH]

    assert classify(checks) is Readiness.READY


def test_waiting_does_not_mask_a_running_check():
    """The permanent exception must not become a hiding place for the real one."""
    checks = _passing(15) + [WAITING_PUBLISH, _check("lint", "pending", "QUEUED")]

    assert classify(checks) is Readiness.RUNNING


def test_empty_check_list_is_not_ready():
    """Merging before checks are created is the sibling of merging while they run.

    A rule shaped as "nothing failing and nothing running" answers yes to an
    empty list. Zero checks is not evidence of health.
    """
    assert classify([]) is Readiness.NO_CHECKS


def test_failure_blocks_even_when_everything_else_passed():
    checks = _passing(15) + [_check("test (windows-latest, 3.13)", "fail", "FAILURE")]

    assert classify(checks) is Readiness.FAILING


def test_unrecognized_bucket_blocks():
    """Tribunal ground V-1: the default is deny.

    A cancelled required check did not pass and is not running, so a
    fall-through rule reads it as green -- exactly the false green this gate
    exists to catch. Failing closed on an unknown value also makes the check
    independent of how completely its author enumerated GitHub's vocabulary.
    """
    checks = _passing(15) + [_check("CodeQL", "cancel", "CANCELLED")]

    assert classify(checks) is Readiness.UNRECOGNIZED


def test_only_ready_is_mergeable():
    """The exit-code contract: one state opens the gate, every other closes it."""
    assert Readiness.READY.mergeable is True
    for state in Readiness:
        if state is not Readiness.READY:
            assert state.mergeable is False, f"{state} must not be mergeable"
