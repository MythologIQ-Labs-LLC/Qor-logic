"""Phase 175 (GH #267): governance-DNA durability.

Session-scoped backup of the five DNA files, no-clobber restore with a
governance-state-loss shadow event, prior-initialization evidence, the
fail-open first-write-of-session hook in gate_chain.write_gate_artifact,
and recovery-aware health-gate routing.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from qor.scripts import gate_chain, governance_snapshot as gs
from qor.scripts import shadow_process
from qor.scripts import validate_gate_artifact as vga


SID = "2026-07-13T0000-dna175"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_dna(base: Path, files=gs.DNA_FILES) -> dict[str, str]:
    hashes = {}
    for rel in files:
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"content of {rel}\n", encoding="utf-8")
        hashes[rel] = _sha(target)
    return hashes


# ----- Phase 1: snapshot helper -----

def test_backup_copies_dna_files_byte_identical(tmp_path):
    hashes = _make_dna(tmp_path)
    out = gs.ensure_session_backup(tmp_path, SID)
    assert out is not None
    for rel in gs.DNA_FILES:
        copied = out / Path(rel).name
        assert copied.exists()
        assert _sha(copied) == hashes[rel]


def test_backup_is_idempotent_per_session(tmp_path):
    _make_dna(tmp_path)
    out1 = gs.ensure_session_backup(tmp_path, SID)
    first = _sha(out1 / "META_LEDGER.md")
    (tmp_path / "docs" / "META_LEDGER.md").write_text("MUTATED\n", encoding="utf-8")
    out2 = gs.ensure_session_backup(tmp_path, SID)
    assert out2 == out1
    assert _sha(out1 / "META_LEDGER.md") == first  # not re-copied


def test_backup_tolerates_missing_files(tmp_path):
    present = gs.DNA_FILES[:3]
    _make_dna(tmp_path, files=present)
    out = gs.ensure_session_backup(tmp_path, SID)
    assert out is not None
    manifest = json.loads((out / ".complete").read_text(encoding="utf-8"))
    assert sorted(manifest["files"].keys()) == sorted(present)


def _redirect_shadow_log(tmp_path, monkeypatch) -> Path:
    """shadow_process resolves its log paths at import time (module constants);
    redirect UPSTREAM explicitly so restore events land in the tmp tree."""
    log = tmp_path / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md"
    monkeypatch.setattr(shadow_process, "UPSTREAM_LOG_PATH", log)
    return log


def test_restore_returns_byte_identical_report_and_emits_event(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    _redirect_shadow_log(tmp_path, monkeypatch)
    hashes = _make_dna(tmp_path)
    out = gs.ensure_session_backup(tmp_path, SID)
    for rel in gs.DNA_FILES:
        (tmp_path / rel).unlink()

    report = gs.restore(tmp_path, out)
    restored = {r["path"]: r for r in report if r["action"] == "restored"}
    assert sorted(restored.keys()) == sorted(gs.DNA_FILES)
    for rel in gs.DNA_FILES:
        assert _sha(tmp_path / rel) == hashes[rel]

    log = tmp_path / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md"
    events = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines()
              if ln.strip().startswith("{")]
    loss = [e for e in events if e["event_type"] == "governance-state-loss"]
    assert len(loss) == 1 and loss[0]["severity"] == 3


def test_restore_no_clobber_skips_existing_files(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    _redirect_shadow_log(tmp_path, monkeypatch)
    _make_dna(tmp_path)
    out = gs.ensure_session_backup(tmp_path, SID)
    survivor = tmp_path / "docs" / "META_LEDGER.md"
    survivor.write_text("NEWER THAN SNAPSHOT\n", encoding="utf-8")
    newer = _sha(survivor)
    for rel in gs.DNA_FILES[1:]:
        (tmp_path / rel).unlink()

    report = gs.restore(tmp_path, out)
    by_path = {r["path"]: r["action"] for r in report}
    assert by_path["docs/META_LEDGER.md"] == "skipped-exists"
    assert _sha(survivor) == newer  # untouched

    forced = gs.restore(tmp_path, out, force=True)
    assert {r["path"]: r["action"] for r in forced}["docs/META_LEDGER.md"] == "restored"
    assert _sha(survivor) != newer  # overwritten under force


def _git(base: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=base, check=True, capture_output=True)


def test_prior_evidence_from_git_history(tmp_path):
    assert gs.prior_initialization_evidence(tmp_path) is None  # bare dir
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t.local")
    _git(tmp_path, "config", "user.name", "t")
    _make_dna(tmp_path, files=("docs/META_LEDGER.md",))
    _git(tmp_path, "add", "docs/META_LEDGER.md")
    _git(tmp_path, "commit", "-q", "-m", "genesis")
    (tmp_path / "docs" / "META_LEDGER.md").unlink()
    evidence = gs.prior_initialization_evidence(tmp_path)
    assert evidence is not None and "git history" in evidence


def test_prior_evidence_from_backup_dir(tmp_path):
    _make_dna(tmp_path)
    gs.ensure_session_backup(tmp_path, SID)
    for rel in gs.DNA_FILES:
        (tmp_path / rel).unlink()
    evidence = gs.prior_initialization_evidence(tmp_path)
    assert evidence is not None and "local-backup" in evidence


def test_cli_backup_and_restore_exit_codes(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _make_dna(tmp_path)
    assert gs.main(["backup", "--session", SID]) == 0
    assert gs.backup_dir(tmp_path, SID).is_dir()
    assert gs.main(["restore", "--from", str(tmp_path / "nonexistent")]) == 1


# ----- Phase 2: write-path hook + routing -----

def test_write_gate_artifact_triggers_session_backup(tmp_path, monkeypatch):
    canonical_sid = "2026-07-13T0000-ab12cd"
    gates = tmp_path / ".qor" / "gates"
    monkeypatch.setattr(vga, "GATES_DIR", gates)
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    _make_dna(tmp_path)
    payload = {"ts": "2026-07-13T00:00:00Z", "plan_path": "docs/p.md",
               "phases": ["p1"], "ci_commands": ["pytest"]}
    gate_chain.write_gate_artifact("plan", payload, session_id=canonical_sid)
    out = gs.backup_dir(tmp_path, canonical_sid)
    assert (out / ".complete").is_file()
    assert (out / "META_LEDGER.md").is_file()


def test_backup_failure_never_breaks_gate_write(tmp_path, monkeypatch):
    canonical_sid = "2026-07-13T0000-ab12cd"
    gates = tmp_path / ".qor" / "gates"
    monkeypatch.setattr(vga, "GATES_DIR", gates)
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))

    def boom(*a, **k):
        raise RuntimeError("backup exploded")

    monkeypatch.setattr(gs, "ensure_session_backup", boom)
    payload = {"ts": "2026-07-13T00:00:00Z", "plan_path": "docs/p.md",
               "phases": ["p1"], "ci_commands": ["pytest"]}
    path = gate_chain.write_gate_artifact("plan", payload, session_id=canonical_sid)
    assert path.is_file()


def test_state_loss_event_validates_against_schema(tmp_path, monkeypatch):
    import jsonschema
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    log = _redirect_shadow_log(tmp_path, monkeypatch)
    _make_dna(tmp_path)
    out = gs.ensure_session_backup(tmp_path, SID)
    for rel in gs.DNA_FILES:
        (tmp_path / rel).unlink()
    gs.restore(tmp_path, out)
    schema = json.loads(
        (Path(__file__).resolve().parent.parent / "qor" / "gates" / "schema"
         / "shadow_event.schema.json").read_text(encoding="utf-8"))
    log = tmp_path / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md"
    events = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines()
              if ln.strip().startswith("{")]
    loss = [e for e in events if e["event_type"] == "governance-state-loss"]
    assert loss, "restore must emit a governance-state-loss event"
    jsonschema.validate(loss[0], schema)


def test_hook_skips_under_pytest_without_qor_root(tmp_path, monkeypatch):
    """GH #274 discipline: without an explicit QOR_ROOT redirect, a pytest run
    must never snapshot the operator's live DNA files."""
    gates = tmp_path / ".qor" / "gates"
    monkeypatch.setattr(vga, "GATES_DIR", gates)
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    monkeypatch.delenv("QOR_ROOT", raising=False)
    calls: list = []
    monkeypatch.setattr(gs, "ensure_session_backup", lambda *a, **k: calls.append(a))
    payload = {"ts": "2026-07-13T00:00:00Z", "plan_path": "docs/p.md",
               "phases": ["p1"], "ci_commands": ["pytest"]}
    gate_chain.write_gate_artifact("plan", payload, session_id="2026-07-13T0000-ab12cd")
    assert calls == []
