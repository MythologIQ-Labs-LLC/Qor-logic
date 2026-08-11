"""Phase 218 (GH #321): Layer B must cover iteration artifacts.

`verify-committed` walks `_REQUIRED_PHASES` -- a *completeness* list answering
"which artifacts must exist for a phase to be complete" -- and reuses it as the
*verification scope*, answering "which artifacts do we verify". Those are
different questions, and `<phase>-iterN.json` matches neither name.

Iteration artifacts are not scratch. Entry #542 binds a vetoed plan and #543 the
amendment; the `-iter` files are what a reader consults to reconstruct why. If
they sit outside Layer B, a committed iteration artifact can be altered after the
fact and nothing detects it.

Demonstrated during the Phase 217 seal: a sidecar written with the wrong digest
formula passed `verify-committed` with "OK: provenance verified for 49 sessions".
"""
from __future__ import annotations

import json
from pathlib import Path

from qor.scripts import gate_provenance


SESSION_ID = "2026-08-11T0000-000000"


def _artifact(session_dir: Path, name: str, *, payload: dict) -> Path:
    """Build an artifact and a REAL sidecar.

    Written via `gate_provenance.write_sidecar` rather than hand-rolled, so the
    fixture cannot drift from the format the verifier expects -- a hand-built
    sidecar omitting `session_id` fails for a reason unrelated to what these
    tests assert.
    """
    session_dir.mkdir(parents=True, exist_ok=True)
    art = session_dir / f"{name}.json"
    art.write_text(json.dumps(payload), encoding="utf-8")
    phase = name.split("-iter")[0]
    gate_provenance.write_sidecar(phase, SESSION_ID, art)
    return art


def _corrupt_sidecar(art: Path) -> None:
    side = gate_provenance.sidecar_path(art)
    meta = json.loads(side.read_text(encoding="utf-8"))
    meta["payload_sha256"] = "f" * 64
    side.write_text(json.dumps(meta), encoding="utf-8")


def test_corrupted_iteration_sidecar_is_detected(tmp_path: Path):
    """THE COUNTERFACTUAL. Fails against HEAD, which never looks at -iterN."""
    sess = tmp_path / "sess"
    art = _artifact(sess, "audit-iter1", payload={"phase": "audit", "verdict": "VETO"})
    _corrupt_sidecar(art)

    findings = gate_provenance.verify_session_artifacts(sess)

    assert findings, (
        "an iteration artifact whose sidecar does not recompute must be "
        "reported; it is the record a reader consults to reconstruct a VETO"
    )
    assert any("audit-iter1" in f for f in findings), findings


def test_required_phase_artifacts_still_verified(tmp_path: Path):
    """REGRESSION. Widening the scope must not drop the original coverage."""
    sess = tmp_path / "sess"
    art = _artifact(sess, "audit", payload={"phase": "audit", "verdict": "PASS"})
    _corrupt_sidecar(art)

    findings = gate_provenance.verify_session_artifacts(sess)
    assert any(f.startswith("audit.json") or "audit.json" in f for f in findings), findings


def test_intact_session_reports_nothing(tmp_path: Path):
    """No false positives across both artifact kinds."""
    sess = tmp_path / "sess"
    _artifact(sess, "audit", payload={"phase": "audit", "verdict": "PASS"})
    _artifact(sess, "audit-iter1", payload={"phase": "audit", "verdict": "VETO"})

    assert gate_provenance.verify_session_artifacts(sess) == []


def test_artifact_without_sidecar_is_skipped_not_failed(tmp_path: Path):
    """Absence of a sidecar is not corruption.

    Completeness is `_REQUIRED_PHASES`'s job and stays there; this walk only
    verifies what claims to be verifiable.
    """
    sess = tmp_path / "sess"
    sess.mkdir(parents=True)
    (sess / "audit-iter1.json").write_text('{"phase": "audit"}', encoding="utf-8")

    assert gate_provenance.verify_session_artifacts(sess) == []


def test_live_repository_sessions_still_verify():
    """The real gate tree, including this session's iteration artifacts."""
    result = gate_provenance.verify_committed(Path("."), phase_min=158)
    assert result.ok, result.mismatches[:3]
