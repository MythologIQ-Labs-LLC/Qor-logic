"""Phase 192 (GH #277): the seal-time delta fold + requirement verify."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from qor.scripts.spec_fold import FoldError, fold_session_deltas
from qor.scripts.spec_merge import SpecMergeError
from qor.scripts.spec_requirement_verify import verify_deltas

SID = "2026-07-13T0000-abcdef"

SPEC = """# Capability: spec-corpus

### Requirement: Corpus is current truth
The corpus SHALL reflect all sealed behavior changes.

#### Scenario: Sealed change
- GIVEN a sealed session with a declared delta
- WHEN the seal completes
- THEN the capability spec contains the folded requirement
"""

DELTA = """## ADDED Requirements

### Requirement: Deltas fold only after PASS
The seal ceremony SHALL fold declared deltas only inside substantiate after the reliability gates.

#### Scenario: VETO session
- GIVEN a session whose audit verdict is VETO
- WHEN the session ends
- THEN no delta is folded and the delta file remains
"""


def _repo(tmp_path: Path, delta_text: str = DELTA, declare: bool = True) -> Path:
    cap = tmp_path / "qor" / "specs" / "spec-corpus"
    (cap / "deltas").mkdir(parents=True)
    (cap / "spec.md").write_text(SPEC, encoding="utf-8")
    delta_rel = f"qor/specs/spec-corpus/deltas/{SID}.md"
    (tmp_path / delta_rel).write_text(delta_text, encoding="utf-8")
    gates = tmp_path / ".qor" / "gates" / SID
    gates.mkdir(parents=True)
    payload = {"phase": "plan", "session_id": SID, "ts": "2026-07-13T16:00:00Z"}
    if declare:
        payload["spec_deltas"] = [{
            "capability": "spec-corpus", "delta_path": delta_rel, "ops": ["ADDED"],
        }]
    (gates / "plan.json").write_text(json.dumps(payload), encoding="utf-8")
    return tmp_path


def _lf_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_fold_applies_and_deletes_delta(tmp_path):
    repo = _repo(tmp_path)
    result = fold_session_deltas(repo, SID)
    spec = repo / "qor" / "specs" / "spec-corpus" / "spec.md"
    assert "Deltas fold only after PASS" in spec.read_text(encoding="utf-8")
    assert not (repo / "qor" / "specs" / "spec-corpus" / "deltas" / f"{SID}.md").exists()
    assert result == {"spec-corpus": _lf_hash(spec)}


def test_fold_conflict_aborts_loudly(tmp_path):
    conflict = DELTA.replace("## ADDED Requirements", "## MODIFIED Requirements")
    repo = _repo(tmp_path, delta_text=conflict)
    spec = repo / "qor" / "specs" / "spec-corpus" / "spec.md"
    before = spec.read_bytes()
    with pytest.raises(SpecMergeError):
        fold_session_deltas(repo, SID)
    assert spec.read_bytes() == before
    assert (repo / "qor" / "specs" / "spec-corpus" / "deltas" / f"{SID}.md").exists()


def test_fold_invalid_result_aborts(tmp_path):
    # folds cleanly but the added requirement violates the grammar (no scenario)
    bad = ("## ADDED Requirements\n\n"
           "### Requirement: Grammarless\n"
           "The corpus SHALL never accept this.\n")
    repo = _repo(tmp_path, delta_text=bad)
    spec = repo / "qor" / "specs" / "spec-corpus" / "spec.md"
    before = spec.read_bytes()
    with pytest.raises(FoldError, match="missing-scenario"):
        fold_session_deltas(repo, SID)
    assert spec.read_bytes() == before


def test_fold_noop_without_deltas(tmp_path):
    repo = _repo(tmp_path, declare=False)
    spec = repo / "qor" / "specs" / "spec-corpus" / "spec.md"
    before = spec.read_bytes()
    assert fold_session_deltas(repo, SID) == {}
    assert spec.read_bytes() == before
    assert (repo / "qor" / "specs" / "spec-corpus" / "deltas" / f"{SID}.md").exists()


def test_requirement_verify_produces_coverage_payload(tmp_path):
    repo = _repo(tmp_path)
    # declare evidence that does NOT exist -> unverified, named
    gates = repo / ".qor" / "gates" / SID / "plan.json"
    payload = json.loads(gates.read_text(encoding="utf-8"))
    payload["spec_deltas"][0]["evidence"] = "qor/scripts/does_not_exist.py"
    gates.write_text(json.dumps(payload), encoding="utf-8")

    coverage = verify_deltas(repo, SID)
    assert coverage["status"] == "fail"
    assert coverage["checked"] == 1
    assert coverage["verified"] == 0
    assert "Deltas fold only after PASS" in coverage["unverified"][0]

    # existing evidence -> verified; payload feeds qa_evidence
    payload["spec_deltas"][0]["evidence"] = "qor/specs/spec-corpus/spec.md"
    gates.write_text(json.dumps(payload), encoding="utf-8")
    coverage = verify_deltas(repo, SID)
    assert coverage == {"status": "pass", "checked": 1, "verified": 1, "unverified": []}

    from qor.scripts.qa_evidence import build_payload
    qa = build_payload(None, coverage=coverage)
    assert qa["pillars"]["coverage"]["status"] == "pass"
