"""Behavioral tests for qor.scripts.external_reviewer (Phase 123; GH #160).

Happy path uses a real stub reviewer subprocess; the timeout path mocks
subprocess.run to raise TimeoutExpired (no flaky real sleep).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from qor.scripts import external_reviewer as er

_VALID_OUTPUT = {
    "critiques": [{"severity": "L2", "claim_challenged": "x",
                   "counter_evidence": "y", "recommended_gap": "z"}],
    "confidence": 0.7,
    "model": "stub",
    "ts": "2026-01-01T00:00:00Z",
}


def _stub(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "stub_reviewer.py"
    p.write_text(body, encoding="utf-8")
    return p


def _ok_stub(tmp_path: Path) -> list[str]:
    body = (
        "import sys, json\n"
        "json.load(sys.stdin)\n"
        f"print(json.dumps({_VALID_OUTPUT!r}))\n"
    )
    return [sys.executable, str(_stub(tmp_path, body))]


def _config(tmp_path: Path, command: list[str]) -> Path:
    cfg_dir = tmp_path / ".qorlogic"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg = cfg_dir / "config.json"
    cfg.write_text(json.dumps({"external_reviewer": {"command": command}}), encoding="utf-8")
    return cfg


def test_resolve_command_from_config(tmp_path: Path) -> None:
    cfg = _config(tmp_path, ["py", "r.py"])
    assert er.resolve_reviewer_command(cfg) == ["py", "r.py"]


def test_resolve_command_absent_returns_none(tmp_path: Path) -> None:
    assert er.resolve_reviewer_command(tmp_path / "nope.json") is None
    empty = tmp_path / "empty.json"
    empty.write_text("{}", encoding="utf-8")
    assert er.resolve_reviewer_command(empty) is None
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert er.resolve_reviewer_command(bad) is None


def test_validate_review_output_accepts_contract() -> None:
    assert er.validate_review_output(_VALID_OUTPUT) is True
    assert er.validate_review_output({"confidence": 1, "model": "m", "ts": "t"}) is False
    assert er.validate_review_output("nope") is False


def test_dispatch_review_parses_stub_verdict(tmp_path: Path) -> None:
    out = er.dispatch_review({"plan_path": "p"}, _ok_stub(tmp_path))
    assert out is not None
    assert out["critiques"][0]["severity"] == "L2"
    assert out["model"] == "stub"


def test_dispatch_review_none_on_invalid_json(tmp_path: Path) -> None:
    cmd = [sys.executable, str(_stub(tmp_path, "print('not json')\n"))]
    assert er.dispatch_review({"x": 1}, cmd) is None


def test_dispatch_review_none_on_nonzero_exit(tmp_path: Path) -> None:
    cmd = [sys.executable, str(_stub(tmp_path, "import sys; sys.exit(1)\n"))]
    assert er.dispatch_review({"x": 1}, cmd) is None


def test_dispatch_review_none_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*a, **k):
        raise subprocess.TimeoutExpired(cmd="r", timeout=0.1)
    monkeypatch.setattr(er.subprocess, "run", _raise)
    assert er.dispatch_review({"x": 1}, ["r"]) is None


def test_run_external_review_fallback_when_unconfigured(tmp_path: Path) -> None:
    outcome = er.run_external_review({"plan_path": "p"}, tmp_path / ".qorlogic" / "config.json")
    assert outcome.status == "fallback"
    assert outcome.review is None


def test_run_external_review_ok_with_stub(tmp_path: Path) -> None:
    cfg = _config(tmp_path, _ok_stub(tmp_path))
    outcome = er.run_external_review({"plan_path": "p"}, cfg)
    assert outcome.status == "ok"
    assert outcome.review["critiques"][0]["severity"] == "L2"


def test_main_prints_outcome_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cfg = _config(tmp_path, _ok_stub(tmp_path))
    inp = tmp_path / "input.json"
    inp.write_text(json.dumps({"plan_path": "p"}), encoding="utf-8")
    rc = er.main(["--config", str(cfg), "--input", str(inp)])
    assert rc == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["status"] == "ok"
