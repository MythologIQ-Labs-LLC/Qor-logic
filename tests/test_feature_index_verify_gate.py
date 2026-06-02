"""Phase 122 (GH #155): fail-closed seal gate + logged --override on
qor.scripts.feature_index_verify, and the qor-substantiate Step 6 wiring flip.

Behavioral: invoke main() and assert exit codes + the logged override event
(monkeypatched shadow log, so the real Process Shadow Genome is untouched).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import feature_index_verify as fiv

_INDEX = (
    "| ID | Name | Source-of-truth file:line | Doc citation | Test path | Verification status |\n"
    "|---|---|---|---|---|---|\n"
    "| FX001 | Foo | src/foo.py:10 | docs/foo.md | tests/test_foo.py | {status} |\n"
)


def _setup(tmp_path: Path, current_status: str, prior_status: str = "verified") -> str:
    (tmp_path / "FEATURE_INDEX.md").write_text(
        _INDEX.format(status=current_status), encoding="utf-8")
    sid = "2026-01-01T0000-prior0"
    fiv.write_seal_snapshot(tmp_path, sid, [{"id": "FX001", "status": prior_status}])
    return sid


def _args(tmp_path: Path, sid: str, *extra: str) -> list[str]:
    return ["--repo-root", str(tmp_path), "--index-path", "FEATURE_INDEX.md",
            "--snapshot", sid, *extra]


def test_main_aborts_on_outside_scope_regression(tmp_path: Path) -> None:
    sid = _setup(tmp_path, current_status="unverified")
    assert fiv.main(_args(tmp_path, sid)) == 1


def test_main_warn_only_still_passes(tmp_path: Path) -> None:
    sid = _setup(tmp_path, current_status="unverified")
    assert fiv.main(_args(tmp_path, sid, "--warn-only")) == 0


def test_main_override_exits_0_and_logs_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sid = _setup(tmp_path, current_status="unverified")
    events: list[dict] = []
    monkeypatch.setattr(fiv.shadow_process, "append_event",
                        lambda event, **kw: events.append(event) or "id")
    rc = fiv.main(_args(tmp_path, sid, "--override"))
    assert rc == 0
    assert len(events) == 1
    assert events[0]["event_type"] == "gate_override"
    assert events[0]["details"]["gate"] == "feature_index_verify"


def test_main_no_regression_returns_0(tmp_path: Path) -> None:
    sid = _setup(tmp_path, current_status="verified")
    assert fiv.main(_args(tmp_path, sid)) == 0


def test_main_skip_when_index_absent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = fiv.main(["--repo-root", str(tmp_path), "--index-path", "FEATURE_INDEX.md"])
    assert rc == 0
    assert "skip" in capsys.readouterr().out.lower()


# --- Phase 2 wiring (prompt-contract) ---

SUBSTANTIATE = Path("qor/skills/governance/qor-substantiate/SKILL.md")


def _seal_invocation_line() -> str:
    for line in SUBSTANTIATE.read_text(encoding="utf-8").splitlines():
        if "feature_index_verify" in line and "ABORT" in line:
            return line
    return ""


def test_substantiate_wiring_is_failclosed() -> None:
    line = _seal_invocation_line()
    assert line, "Step 6 must invoke feature_index_verify with || ABORT"  # prose-lint: ok=prompt-contract
    assert "|| ABORT" in line  # prose-lint: ok=prompt-contract
    assert "--warn-only" not in line  # prose-lint: ok=prompt-contract


def test_substantiate_documents_override_escape() -> None:
    text = SUBSTANTIATE.read_text(encoding="utf-8")
    assert "--override" in text  # prose-lint: ok=prompt-contract


def test_doctrine_marks_failclosed() -> None:
    doc = Path("qor/references/doctrine-feature-inventory.md").read_text(encoding="utf-8")
    assert "fail-closed" in doc  # prose-lint: ok=prompt-contract
    assert "--override" in doc  # prose-lint: ok=prompt-contract
