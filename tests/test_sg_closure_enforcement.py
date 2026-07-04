"""Phase 166 (GH #249): SG closure requires an executable enforcer.

Behavioral tests for the closure_enforcer validation + stamping contract,
the schema if-then rule, and the WARN-only corpus lint. Fixtures reuse the
Phase 36 two-stage-flip helpers from tests/test_remediate.py.
"""
from __future__ import annotations

import json
from unittest import mock

import pytest

from qor.scripts import remediate_mark_addressed as rma
from qor.scripts import shadow_process, sg_closure_lint
from test_remediate import (
    _seed,
    _write_audit_artifact,
    _write_remediate_gate,
    make_event,
)

_MODULE_ENFORCER = "qor.scripts.sg_closure_lint"
_LONG_JUSTIFICATION = (
    "cannot-automate: the failure mode is a human judgment call about prose tone "
    "that no deterministic check can classify without unacceptable false positives"
)


def test_validate_accepts_all_four_forms():
    rma._validate_closure_enforcer("tests/test_sg_closure_enforcement.py")
    rma._validate_closure_enforcer(_MODULE_ENFORCER)
    rma._validate_closure_enforcer("/qor-substantiate Step 6.5")
    rma._validate_closure_enforcer(_LONG_JUSTIFICATION)


def test_validate_rejects_bad_forms():
    bad = [
        "tests/test_does_not_exist_anywhere.py",   # missing test file
        "qor.scripts.no_such_module_xyz",           # non-importable module
        "qor-substantiate Step 6.5",                # malformed gate ref (no leading /)
        "cannot-automate: too short",               # justification under 50 chars
        "",                                          # empty
        "just some prose about fixing it",          # none of the forms
    ]
    for value in bad:
        with pytest.raises(rma.ClosureEnforcerError):
            rma._validate_closure_enforcer(value)


def _happy_path(tmp_path, enforcer):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e = make_event(session_id="s-enf")
    _seed(local, [e])
    upstream.write_text("", encoding="utf-8")
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        rma.mark_addressed_pending([e["id"]], session_id="s-enf")
        gate = tmp_path / ".qor" / "gates" / "s-enf" / "remediate.json"
        _write_remediate_gate(gate, [e["id"]])
        audit = tmp_path / "audit.json"
        _write_audit_artifact(audit, verdict="PASS", reviews_gate=str(gate))
        flipped, missing = rma.mark_addressed(
            [e["id"]],
            session_id="s-enf",
            review_pass_artifact_path=str(audit),
            remediate_gate_path=str(gate),
            closure_enforcer=enforcer,
        )
    return flipped, missing, shadow_process.read_events(local)


def test_mark_addressed_stamps_closure_enforcer(tmp_path):
    flipped, missing, after = _happy_path(tmp_path, _MODULE_ENFORCER)
    assert (flipped, missing) == (1, [])
    assert after[0]["addressed"] is True
    assert after[0]["closure_enforcer"] == _MODULE_ENFORCER


def test_mark_addressed_invalid_enforcer_mutates_nothing(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e = make_event(session_id="s-bad-enf")
    _seed(local, [e])
    upstream.write_text("", encoding="utf-8")
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        rma.mark_addressed_pending([e["id"]], session_id="s-bad-enf")
        gate = tmp_path / ".qor" / "gates" / "s-bad-enf" / "remediate.json"
        _write_remediate_gate(gate, [e["id"]])
        audit = tmp_path / "audit.json"
        _write_audit_artifact(audit, verdict="PASS", reviews_gate=str(gate))
        with pytest.raises(rma.ClosureEnforcerError):
            rma.mark_addressed(
                [e["id"]],
                session_id="s-bad-enf",
                review_pass_artifact_path=str(audit),
                remediate_gate_path=str(gate),
                closure_enforcer="prose only, no enforcer",
            )
        after = shadow_process.read_events(local)
    assert after[0]["addressed"] is False
    assert "closure_enforcer" not in after[0]


def test_schema_requires_enforcer_on_remediated_close():
    import jsonschema

    schema = shadow_process.load_schema()
    closed = make_event()
    closed.update({
        "addressed": True,
        "addressed_ts": "2026-07-04T12:00:00Z",
        "addressed_reason": "remediated",
        "addressed_pending": True,
    })
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(closed, schema)
    closed["closure_enforcer"] = _MODULE_ENFORCER
    jsonschema.validate(closed, schema)
    open_event = make_event()
    jsonschema.validate(open_event, schema)  # grandfather: unaddressed needs nothing


_SYNTHETIC_DOCTRINE = """# Countermeasures

## SG-Good-A ("cited enforcer")

Pattern: something bad. Countermeasure: enforced by `tests/test_demo_lint.py`
wired into CI.

## SG-Bad-A ("prose only")

Pattern: something else bad. Countermeasure: authors should be careful and
review each other's work diligently.
"""


def test_lint_flags_only_prose_only_entries(tmp_path, capsys):
    doctrine = tmp_path / "doctrine.md"
    doctrine.write_text(_SYNTHETIC_DOCTRINE, encoding="utf-8")
    rc = sg_closure_lint.main(["--doctrine", str(doctrine)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "SG-Bad-A" in out
    assert "SG-Good-A" not in out
    doctrine.write_text(_SYNTHETIC_DOCTRINE.replace(
        "review each other's work diligently.",
        "review diligently; cannot-automate: tone judgment is inherently human per entry #386 decision.",
    ), encoding="utf-8")
    rc = sg_closure_lint.main(["--doctrine", str(doctrine)])
    assert rc == 0
