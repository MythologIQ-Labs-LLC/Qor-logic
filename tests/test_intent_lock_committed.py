"""Phase 233 (GH #352): CI sees the lock.

Before this, intent_lock was the one ladder gate with no CI enforcement --
its ABORT was always resolvable by the person it constrains (#16798). Sealed
sessions commit their lock evidence since Phase 231; this checker makes a
merge that loses or tampers with that evidence fail CI.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from qor.reliability import intent_lock_committed as subject


def _ledger(phase: int, session: str) -> str:
    return (f"# Ledger\n\n"
            f"### Entry #1: SESSION SEAL -- Phase {phase} widget (v9.9.9)\n\n"
            f"**Session**: `{session}`\n")


def _repo(tmp_path: Path, phase: int = 300, session: str = "sess-a") -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Qor Test"], cwd=tmp_path, check=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(_ledger(phase, session), encoding="utf-8")
    plan = tmp_path / "docs" / "plan.md"
    plan.write_text("alpha\nbeta\n", encoding="utf-8")
    audit_body = b"# AUDIT\n\nVerdict: PASS\n"
    lock_dir = tmp_path / ".qor" / "intent-lock"
    lock_dir.mkdir(parents=True)
    plan_bytes = plan.read_bytes().replace(b"\r\n", b"\n")
    (lock_dir / f"{session}.plan.snapshot").write_bytes(plan_bytes)
    (lock_dir / f"{session}.audit.snapshot").write_bytes(audit_body)
    record = {
        "session": session,
        "plan_path": "docs/plan.md",
        "plan_hash": hashlib.sha256(plan_bytes).hexdigest(),
        "audit_path": ".agent/staging/AUDIT_REPORT.md",
        "audit_hash": hashlib.sha256(audit_body).hexdigest(),
        "head_commit": "0" * 40,
        "captured_ts": "2026-01-01T00:00:00Z",
    }
    (lock_dir / f"{session}.json").write_text(json.dumps(record), encoding="utf-8")
    subprocess.run(["git", "add", "-A", "-f"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "f"], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


def test_valid_session_verifies_clean(tmp_path):
    repo = _repo(tmp_path)
    assert subject.check(repo, phase_min=231) == []


def test_tampered_snapshot_is_named(tmp_path):
    repo = _repo(tmp_path)
    snap = repo / ".qor" / "intent-lock" / "sess-a.plan.snapshot"
    snap.write_bytes(snap.read_bytes() + b"tampered\n")

    failures = subject.check(repo, phase_min=231)

    assert any("sess-a" in f.detail and f.kind == "snapshot-mismatch" for f in failures)


def test_missing_family_is_named(tmp_path):
    repo = _repo(tmp_path)
    (repo / ".qor" / "intent-lock" / "sess-a.json").unlink()

    failures = subject.check(repo, phase_min=231)

    assert any(f.kind == "missing-evidence" for f in failures)


def test_plan_referent_mismatch_is_named(tmp_path):
    repo = _repo(tmp_path)
    (repo / "docs" / "plan.md").write_text("alpha\nEDITED\n", encoding="utf-8")

    failures = subject.check(repo, phase_min=231)

    kinds = {f.kind for f in failures}
    assert "plan-referent-mismatch" in kinds
    assert "snapshot-mismatch" not in kinds  # distinct failure classes


def test_grandfather_boundary_skips_old_sessions(tmp_path):
    repo = _repo(tmp_path, phase=200)
    for f in (repo / ".qor" / "intent-lock").iterdir():
        f.unlink()

    assert subject.check(repo, phase_min=231) == []


def test_the_real_ledger_verifies_clean_at_the_boundary():
    """The anti-recurrence binding: the repo's own committed evidence must
    verify -- the first check of the lock's guarantee by something other than
    the person it constrains."""
    repo = Path(__file__).resolve().parents[1]
    assert subject.check(repo, phase_min=231) == []


# ---------------------------------------------------------------------------
# Phase 296: intent-lock re-attestation. A walked sealed session's plan side may
# be superseded only by a contiguous, closed-schema, ledger-committed chain of
# `<session>.reattest-<k>.json` records; the audit side never changes.
# ---------------------------------------------------------------------------

from qor.scripts import ledger_hash  # noqa: E402

_LOCK = Path(".qor") / "intent-lock"


def _redact(repo: Path, text: str = "alpha\nREDACTED\n", session: str = "sess-a") -> str:
    """Edit the plan and regenerate its snapshot; return the new plan hash."""
    plan = repo / "docs" / "plan.md"
    plan.write_text(text, encoding="utf-8")
    data = plan.read_bytes().replace(b"\r\n", b"\n")
    (repo / _LOCK / f"{session}.plan.snapshot").write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _record(repo: Path, session: str = "sess-a") -> dict:
    return json.loads((repo / _LOCK / f"{session}.json").read_text(encoding="utf-8"))


def _reattest(repo: Path, k: str, supersedes: str, new: str, session: str = "sess-a",
              **extra) -> str:
    body = {"session": session, "supersedes_plan_hash": supersedes,
            "plan_hash": new, "reason": "publication boundary", **extra}
    rel = (_LOCK / f"{session}.reattest-{k}.json").as_posix()
    (repo / rel).write_text(json.dumps(body), encoding="utf-8")
    return rel


def _commit(repo: Path, rel: str) -> None:
    """Append an AMENDMENT whose line-leading Artifact commits `rel`'s bytes."""
    ledger = repo / "docs" / "META_LEDGER.md"
    text = ledger.read_text(encoding="utf-8")
    n = text.count("### Entry #") + 1
    digest = ledger_hash.content_hash(repo / rel)
    ledger.write_text(
        text + f"\n### Entry #{n}: AMENDMENT -- re-attestation\n\n"
        f"**Artifact**: {rel}\n**Amends**: Entry #1\n\n**Content Hash**: `{digest}`\n",
        encoding="utf-8")


def _rewrite(repo: Path, rel: str, **changes) -> None:
    body = json.loads((repo / rel).read_text(encoding="utf-8"))
    body.update(changes)
    (repo / rel).write_text(json.dumps(body), encoding="utf-8")


def _kinds(failures) -> set[str]:
    return {f.kind for f in failures}


def test_redaction_with_committed_reattestation_verifies_clean(tmp_path):
    repo = _repo(tmp_path)
    new = _redact(repo)
    _commit(repo, _reattest(repo, "1", _record(repo)["plan_hash"], new))

    assert subject.check(repo, phase_min=231) == []


def test_redaction_without_reattestation_still_fails(tmp_path):
    repo = _repo(tmp_path)
    _redact(repo)

    kinds = _kinds(subject.check(repo, phase_min=231))

    assert {"plan-referent-mismatch", "snapshot-mismatch"} <= kinds


def test_uncommitted_reattestation_is_invalid(tmp_path):
    repo = _repo(tmp_path)
    new = _redact(repo)
    _reattest(repo, "1", _record(repo)["plan_hash"], new)

    failures = subject.check(repo, phase_min=231)

    invalid = [f for f in failures if f.kind == "reattestation-invalid"]
    assert len(invalid) == 1 and "sess-a.reattest-1.json" in invalid[0].detail


def test_reattestation_edited_after_commit_is_invalid(tmp_path):
    repo = _repo(tmp_path)
    new = _redact(repo)
    rel = _reattest(repo, "1", _record(repo)["plan_hash"], new)
    _commit(repo, rel)
    _rewrite(repo, rel, reason="changed after commit")

    assert "reattestation-invalid" in _kinds(subject.check(repo, phase_min=231))


def test_reattestation_not_chaining_from_the_record_is_invalid(tmp_path):
    repo = _repo(tmp_path)
    new = _redact(repo)
    _commit(repo, _reattest(repo, "1", "f" * 64, new))

    assert "reattestation-invalid" in _kinds(subject.check(repo, phase_min=231))


def test_two_step_reattestation_chain_verifies_clean(tmp_path):
    repo = _repo(tmp_path)
    first = _redact(repo, "alpha\nONE\n")
    _commit(repo, _reattest(repo, "1", _record(repo)["plan_hash"], first))
    second = _redact(repo, "alpha\nTWO\n")
    _commit(repo, _reattest(repo, "2", first, second))

    assert subject.check(repo, phase_min=231) == []


def test_reattestation_gap_is_invalid(tmp_path):
    repo = _repo(tmp_path)
    new = _redact(repo)
    _commit(repo, _reattest(repo, "2", _record(repo)["plan_hash"], new))

    assert "reattestation-invalid" in _kinds(subject.check(repo, phase_min=231))


def test_reattestation_session_mismatch_is_invalid(tmp_path):
    repo = _repo(tmp_path)
    new = _redact(repo)
    rel = _reattest(repo, "1", _record(repo)["plan_hash"], new)
    _rewrite(repo, rel, session="sess-other")
    _commit(repo, rel)

    assert "reattestation-invalid" in _kinds(subject.check(repo, phase_min=231))


def test_malformed_reattestation_json_is_a_failure_not_an_exception(tmp_path):
    repo = _repo(tmp_path)
    _redact(repo)
    rel = (_LOCK / "sess-a.reattest-1.json").as_posix()
    (repo / rel).write_text("{not json", encoding="utf-8")
    _commit(repo, rel)

    failures = subject.check(repo, phase_min=231)

    assert "reattestation-invalid" in _kinds(failures)


def test_reattestation_with_extra_or_audit_field_is_invalid(tmp_path):
    repo = _repo(tmp_path)
    new = _redact(repo)
    _commit(repo, _reattest(repo, "1", _record(repo)["plan_hash"], new, audit_hash="0" * 64))

    failures = subject.check(repo, phase_min=231)

    assert "reattestation-invalid" in _kinds(failures)
    # the audit side was never superseded, so the untouched audit snapshot passes
    assert not any("audit.snapshot" in f.detail for f in failures)


def test_non_integer_or_padded_index_is_invalid(tmp_path):
    for k in ("01", "x"):
        repo_dir = tmp_path / k
        repo_dir.mkdir()
        repo = _repo(repo_dir)
        new = _redact(repo)
        _commit(repo, _reattest(repo, k, _record(repo)["plan_hash"], new))

        failures = subject.check(repo, phase_min=231)

        assert any(f.kind == "reattestation-invalid" and f"reattest-{k}.json" in f.detail
                   for f in failures), k


def test_reattestation_for_unwalked_session_is_invalid(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, _reattest(repo, "1", "a" * 64, "b" * 64, session="sess-unsealed"))

    failures = subject.check(repo, phase_min=231)

    assert any(f.kind == "reattestation-invalid" and "sess-unsealed" in f.detail
               for f in failures)


def test_malformed_ledger_commitment_becomes_a_failure(tmp_path):
    repo = _repo(tmp_path)
    new = _redact(repo)
    _commit(repo, _reattest(repo, "1", _record(repo)["plan_hash"], new))
    ledger = repo / "docs" / "META_LEDGER.md"
    ledger.write_text(ledger.read_text(encoding="utf-8")
                      + "\n### Entry #9: AMENDMENT -- bad\n\n**Superseded Content Hash**: abc123\n",
                      encoding="utf-8")

    failures = subject.check(repo, phase_min=231)

    assert "reattestation-invalid" in _kinds(failures)


def test_valid_chain_does_not_excuse_a_tampered_audit_snapshot(tmp_path):
    repo = _repo(tmp_path)
    new = _redact(repo)
    _commit(repo, _reattest(repo, "1", _record(repo)["plan_hash"], new))
    audit = repo / _LOCK / "sess-a.audit.snapshot"
    audit.write_bytes(audit.read_bytes() + b"tampered\n")

    failures = subject.check(repo, phase_min=231)

    assert [f.kind for f in failures] == ["snapshot-mismatch"]
    assert "audit.snapshot" in failures[0].detail


def test_valid_chain_with_stale_plan_snapshot_fails(tmp_path):
    repo = _repo(tmp_path)
    old_snapshot = (repo / _LOCK / "sess-a.plan.snapshot").read_bytes()
    new = _redact(repo)
    (repo / _LOCK / "sess-a.plan.snapshot").write_bytes(old_snapshot)
    _commit(repo, _reattest(repo, "1", _record(repo)["plan_hash"], new))

    failures = subject.check(repo, phase_min=231)

    assert [f.kind for f in failures] == ["snapshot-mismatch"]
    assert "plan.snapshot" in failures[0].detail


def test_no_reattestation_files_is_unchanged_behavior(tmp_path):
    repo = _repo(tmp_path)

    assert subject.check(repo, phase_min=231) == []
