"""Behavioral tests for the compliance ratchet (Phase 141).

`regressions` is invoked on constructed Control/Waiver tuples; each test asserts
on the returned regression list (the ratchet's actual output), not on artifacts.
"""
from __future__ import annotations

from qor.scripts import compliance_ratchet as cr
from qor.scripts.compliance_matrix import Control, Waiver


def _c(cid, posture="ABORT"):
    return Control(
        id=cid, framework="F", control="c", enforcing_module="m",
        posture=posture, detection="test", wired_into={}, variants=(),
    )


def test_dropped_control_is_a_regression():
    prior = (_c("alpha"), _c("beta"))
    current = (_c("alpha"),)
    out = cr.regressions(current, prior, ())
    assert len(out) == 1
    assert "'beta'" in out[0] and "drop" in out[0].lower()
    assert "'alpha'" not in out[0]


def test_posture_downgrade_is_a_regression():
    prior = (_c("a", "ABORT"),)
    current = (_c("a", "WARN"),)
    out = cr.regressions(current, prior, ())
    assert out
    assert any("a" in r and "downgrad" in r.lower() for r in out)


def test_waiver_suppresses_regression():
    prior = (_c("a", "ABORT"),)
    current = (_c("a", "WARN"),)
    waivers = (Waiver(id="a", justification="intentional softening pending V2", issue="#999"),)
    assert cr.regressions(current, prior, waivers) == []


def test_added_control_is_not_a_regression():
    prior = (_c("a"),)
    current = (_c("a"), _c("b"))
    assert cr.regressions(current, prior, ()) == []


def test_first_introduction_has_no_regressions(tmp_path):
    # No matrix at the ref -> prior is None -> check returns no regressions.
    assert cr.ratchet_check(tmp_path, "v0.0.0-nonexistent") == []


def test_no_compliance_regression_vs_prior_release():
    """Live CI gate: the real matrix must not drop/downgrade a control relative
    to the prior release (no-op until a prior release carries a matrix)."""
    import pathlib
    repo = pathlib.Path(__file__).resolve().parents[1]
    base = cr._default_base(repo)
    if base is None:
        import pytest
        pytest.skip("no v* release tags available")
    regs = cr.ratchet_check(repo, base)
    assert regs == [], "compliance regression vs %s:\n  %s" % (base, "\n  ".join(regs))
