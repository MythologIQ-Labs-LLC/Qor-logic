"""Phase 58: procedural_fidelity module API tests."""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from qor.scripts import procedural_fidelity as pf


def test_deviation_is_frozen_dataclass():
    assert dataclasses.is_dataclass(pf.Deviation)
    d = pf.Deviation(
        deviation_class="doc-surface-uncovered",
        severity=2, step_id=None,
        description="test", files_referenced=("x",),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.severity = 3  # type: ignore[misc]


def test_deviation_classes_constant_includes_v1_set():
    expected = {"missing-step", "doc-surface-uncovered",
                "ordering-drift", "argv-shape-divergence"}
    assert isinstance(pf.DEVIATION_CLASSES, frozenset)
    assert expected <= pf.DEVIATION_CLASSES


def test_check_seal_commit_returns_empty_for_clean_fixture(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    sid = "test-clean"
    gates = repo / ".qor" / "gates" / sid
    gates.mkdir(parents=True)
    payload = {
        "phase": "implement", "session_id": sid, "ts": "2026-05-01T20:00:00Z",
        "files_touched": [
            "qor/skills/foo/SKILL.md",
            "docs/SYSTEM_STATE.md",  # at-least-one rule satisfied
        ],
    }
    import json
    (gates / "implement.json").write_text(json.dumps(payload), encoding="utf-8")
    findings = pf.check_seal_commit(repo, sid)
    assert findings == []


def test_to_findings_json_emits_required_fields():
    d = pf.Deviation(
        deviation_class="doc-surface-uncovered",
        severity=2, step_id="step-6",
        description="missing system-tier doc",
        files_referenced=("qor/skills/foo/SKILL.md",),
    )
    out = pf.to_findings_json([d])
    assert len(out) == 1
    keys = set(out[0].keys())
    assert {"class", "severity", "step_id", "description",
            "files_referenced", "addressed"} <= keys
    assert out[0]["addressed"] is False
