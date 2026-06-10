"""Phase 158 (GAP-GOV-05): non-forgeable gate-artifact provenance.

Layer A -- local per-session HMAC sidecar: tamper-evidence + cross-session
replay resistance. Honest ceiling = an in-repo filesystem actor (the per-session
key lives under the gitignored .qor/session/).
Layer B -- CI attestation: a keyless `verify_committed` recomputation gate
(merge-boundary teeth, runs on forks) + a CI-secret-keyed attestation only
trusted CI can produce.

Every test invokes the unit and asserts on its output / raised exception
(functionality tests, not presence-only), per doctrine-test-functionality.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

import pytest

from qor.scripts import gate_provenance as gp


# ---------------------------------------------------------------- Layer A core

def test_sign_verify_round_trip_true():
    key = b"k" * 32
    data = b"# Seal\nplan body\n"
    tag = gp.sign("plan", "2026-06-10T1350-aaaaaa", data, key=key)
    assert gp.verify_tag("plan", "2026-06-10T1350-aaaaaa", data, tag, key=key) is True


def test_verify_false_on_payload_edit():
    key = b"k" * 32
    sid = "2026-06-10T1350-aaaaaa"
    tag = gp.sign("plan", sid, b"original body\n", key=key)
    assert gp.verify_tag("plan", sid, b"tampered body\n", tag, key=key) is False


def test_verify_false_on_phase_swap():
    key = b"k" * 32
    sid = "2026-06-10T1350-aaaaaa"
    data = b"body\n"
    tag = gp.sign("plan", sid, data, key=key)
    # A tag signed for phase=plan must not verify as phase=audit (replay).
    assert gp.verify_tag("audit", sid, data, tag, key=key) is False


def test_sign_is_crlf_invariant():
    # Gate artifacts are committed; git autocrlf may rewrite them to CRLF.
    # The signed material is LF-normalized, so a CRLF twin signs identically.
    key = b"k" * 32
    sid = "2026-06-10T1350-aaaaaa"
    lf = gp.sign("plan", sid, b"a\nb\n", key=key)
    crlf = gp.sign("plan", sid, b"a\r\nb\r\n", key=key)
    assert lf == crlf


# ---------------------------------------------------------------- session key

def test_distinct_sessions_get_distinct_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    k1 = gp.session_key("2026-06-10T1350-aaaaaa")
    k2 = gp.session_key("2026-06-10T1350-bbbbbb")
    assert k1 != k2
    data = b"body\n"
    tag = gp.sign("plan", "2026-06-10T1350-aaaaaa", data, key=k1)
    # A tag from session A fails under session B's distinct key.
    assert gp.verify_tag("plan", "2026-06-10T1350-aaaaaa", data, tag, key=k2) is False


def test_session_key_persisted_and_stable(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    first = gp.session_key("2026-06-10T1350-aaaaaa")
    second = gp.session_key("2026-06-10T1350-aaaaaa")
    assert first == second  # loaded, not regenerated
    assert len(first) == 32


def test_session_key_rejects_pathunsafe_id(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    with pytest.raises(ValueError):
        gp.session_key("../evil")


def test_session_key_absent_without_create(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        gp.session_key("2026-06-10T1350-cccccc", create=False)


# ---------------------------------------------------------------- sidecar I/O

def _write_artifact(tmp_path: Path, name: str, body: dict) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return p


def test_write_sidecar_then_verify_sidecar_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    art = _write_artifact(tmp_path, "plan.json", {"phase": "plan", "x": 1})
    gp.write_sidecar("plan", "2026-06-10T1350-aaaaaa", art)
    res = gp.verify_sidecar(art)
    assert res.payload_ok and res.hmac_ok and res.key_present


def test_verify_sidecar_detects_artifact_tamper(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    art = _write_artifact(tmp_path, "plan.json", {"phase": "plan", "x": 1})
    gp.write_sidecar("plan", "2026-06-10T1350-aaaaaa", art)
    art.write_text(json.dumps({"phase": "plan", "x": 999}), encoding="utf-8")
    res = gp.verify_sidecar(art)
    assert res.payload_ok is False


def test_payload_digest_is_keyless_and_matches_recompute(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    art = _write_artifact(tmp_path, "plan.json", {"phase": "plan", "x": 1})
    gp.write_sidecar("plan", "2026-06-10T1350-aaaaaa", art)
    sidecar = json.loads(gp.sidecar_path(art).read_text(encoding="utf-8"))
    expect = hashlib.sha256(art.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert sidecar["payload_sha256"] == expect


def test_verify_sidecar_keyless_when_key_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    art = _write_artifact(tmp_path, "plan.json", {"phase": "plan", "x": 1})
    gp.write_sidecar("plan", "2026-06-10T1350-aaaaaa", art)
    # Simulate CI: the per-session key is absent. payload_ok still recomputes;
    # hmac_ok is not asserted (key_present False).
    (tmp_path / ".qor" / "session" / "keys" / "2026-06-10T1350-aaaaaa.key").unlink()
    res = gp.verify_sidecar(art, require_key=False)
    assert res.payload_ok is True
    assert res.key_present is False


# ---------------------------------------------------------------- Layer B: CI

def test_ci_attest_returns_none_without_secret(monkeypatch):
    monkeypatch.delenv("QOR_CI_ATTEST_SECRET", raising=False)
    assert gp.ci_attest("a" * 64, "b" * 64) is None


def test_ci_attest_deterministic_with_secret():
    a = gp.ci_attest("a" * 64, "b" * 64, secret="s3cr3t")
    again = gp.ci_attest("a" * 64, "b" * 64, secret="s3cr3t")
    other = gp.ci_attest("a" * 64, "b" * 64, secret="different")
    assert a == again and a != other and a is not None


def test_verify_ci_attestation_round_trip():
    att = gp.ci_attest("a" * 64, "b" * 64, secret="s3cr3t")
    assert gp.verify_ci_attestation("a" * 64, "b" * 64, att, secret="s3cr3t") is True
    assert gp.verify_ci_attestation("a" * 64, "b" * 64, att, secret="wrong") is False
    # Cannot verify without the secret -- the documented CI-only property.
    assert gp.verify_ci_attestation("a" * 64, "b" * 64, att, secret=None) is False


def test_latest_seal_hashes_extracts_last_entry(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(
        "**Content Hash**: `" + "a" * 64 + "`\n"
        "**Chain Hash (Merkle seal)**: `" + "b" * 64 + "`\n"
        "**Content Hash**: `" + "c" * 64 + "`\n"
        "**Chain Hash (Merkle seal)**: `" + "d" * 64 + "`\n",
        encoding="utf-8",
    )
    assert gp.latest_seal_hashes(tmp_path) == ("c" * 64, "d" * 64)


def test_latest_seal_hashes_none_when_no_markers(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text("no hashes here\n", encoding="utf-8")
    assert gp.latest_seal_hashes(tmp_path) is None


def test_attest_latest_cli_skips_without_secret(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("QOR_CI_ATTEST_SECRET", raising=False)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(
        "**Content Hash**: `" + "a" * 64 + "`\n"
        "**Chain Hash (Merkle seal)**: `" + "b" * 64 + "`\n",
        encoding="utf-8",
    )
    rc = gp.main(["attest-latest", "--repo-root", str(tmp_path)])
    assert rc == 0
    assert "SKIP" in capsys.readouterr().out


def test_attest_latest_cli_emits_under_secret(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("QOR_CI_ATTEST_SECRET", "s3cr3t")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(
        "**Content Hash**: `" + "a" * 64 + "`\n"
        "**Chain Hash (Merkle seal)**: `" + "b" * 64 + "`\n",
        encoding="utf-8",
    )
    rc = gp.main(["attest-latest", "--repo-root", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out == gp.ci_attest("a" * 64, "b" * 64, secret="s3cr3t")


# ---------------------------------------------- Layer B: verify_committed gate

def _seed_sealed_repo(root: Path, phase_num: int, sid: str, *, with_sidecars: bool):
    (root / "docs").mkdir(parents=True, exist_ok=True)
    ledger = root / "docs" / "META_LEDGER.md"
    ledger.write_text(
        f"### Entry #999: SESSION SEAL -- Phase {phase_num} test\n\n"
        f"**Phase**: SUBSTANTIATE (Phase {phase_num})\n"
        f"**Session**: `{sid}`\n\n"
        "**Content Hash**: `" + "0" * 64 + "`\n",
        encoding="utf-8",
    )
    gates = root / ".qor" / "gates" / sid
    gates.mkdir(parents=True, exist_ok=True)
    arts = {}
    for ph in ("plan", "audit", "implement", "substantiate"):
        art = gates / f"{ph}.json"
        art.write_text(json.dumps({"phase": ph, "session_id": sid}), encoding="utf-8")
        if with_sidecars:
            gp.write_sidecar(ph, sid, art)
        arts[ph] = art
    return ledger, arts


def test_verify_committed_passes_on_consistent_sidecars(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    _seed_sealed_repo(tmp_path, 158, "2026-06-10T1350-aaaaaa", with_sidecars=True)
    res = gp.verify_committed(tmp_path, phase_min=158)
    assert res.ok is True


def test_verify_committed_fails_on_artifact_tamper(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    _, arts = _seed_sealed_repo(tmp_path, 158, "2026-06-10T1350-aaaaaa", with_sidecars=True)
    arts["plan"].write_text(json.dumps({"phase": "plan", "evil": True}), encoding="utf-8")
    res = gp.verify_committed(tmp_path, phase_min=158)
    assert res.ok is False
    assert any("plan" in m for _, m in res.mismatches)


def test_verify_committed_fails_on_missing_sidecar(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    _seed_sealed_repo(tmp_path, 158, "2026-06-10T1350-aaaaaa", with_sidecars=False)
    res = gp.verify_committed(tmp_path, phase_min=158)
    assert res.ok is False  # no fail-open: missing sidecar is a failure


def test_verify_committed_grandfathers_below_phase_min(tmp_path, monkeypatch):
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    _seed_sealed_repo(tmp_path, 100, "2026-06-10T1350-oldold", with_sidecars=False)
    res = gp.verify_committed(tmp_path, phase_min=158)
    assert res.ok is True  # phase 100 < 158 is grandfathered (no sidecar required)
