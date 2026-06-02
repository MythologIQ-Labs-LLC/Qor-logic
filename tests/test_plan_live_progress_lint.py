"""Behavioral tests for qor.scripts.plan_live_progress_lint (Phase 127; GH #156).

Fixtures isolate each of the four SG-FakeProgress-A sub-rules.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import plan_live_progress_lint as lpl

_FAKE_JUMP = (
    "function run(){ bar.style.width = '0%';\n"
    "  await scaffold();\n"
    "  bar.style.width = '100%'; }\n"
)
_INTERMEDIATE_GOOD = (
    "socket.addEventListener('message', e => { bar.style.width = e.pct + '%'; });\n"
    "bar.style.width = '0%';\n bar.style.width = '40%';\n bar.style.width = '80%';\n"
    "bar.style.width = '100%';\n"
    "dismissBtn.onclick = () => modal.close();\n"
)
_NO_SUB = (
    "bar.style.width = '0%';\n bar.style.width = '50%';\n bar.style.width = '100%';\n"
    "closeBtn.onclick = () => modal.dismiss();\n"
)
_WITH_SUB = _NO_SUB + "es = new EventSource('/progress'); es.onmessage = render;\n"
_ERR_NO_DISMISS = (
    "socket.addEventListener('message', render);\n"
    "bar.style.width = '0%'; bar.style.width = '50%';\n"
    "try { await go(); } catch (e) { bar.style.width = '0%'; showError(e); }\n"
)


def _kinds(findings) -> set[str]:
    return {f.kind for f in findings}


def test_fake_jump_flagged() -> None:
    assert "fake-jump" in _kinds(lpl.scan_text(_FAKE_JUMP))


def test_progress_with_intermediate_not_flagged() -> None:
    assert lpl.scan_text(_INTERMEDIATE_GOOD) == []


def test_missing_event_subscription_flagged() -> None:
    kinds = _kinds(lpl.scan_text(_NO_SUB))
    assert "no-event-subscription" in kinds
    assert "fake-jump" not in kinds  # has an intermediate (50%)


def test_event_subscription_clears() -> None:
    assert "no-event-subscription" not in _kinds(lpl.scan_text(_WITH_SUB))


def test_error_state_without_dismiss_flagged() -> None:
    assert "error-no-dismiss" in _kinds(lpl.scan_text(_ERR_NO_DISMISS))


def test_suppress_comment_clears() -> None:
    assert lpl.scan_text(_FAKE_JUMP + "// qor:live-progress-ok\n") == []


def test_scan_repo_skips_backend_only(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text("x = 1\n", encoding="utf-8")
    assert lpl.scan_repo(tmp_path) == []


def test_main_exit_1_on_finding(tmp_path: Path) -> None:
    (tmp_path / "ui.js").write_text(_FAKE_JUMP, encoding="utf-8")
    assert lpl.main(["--repo-root", str(tmp_path)]) == 1


def test_main_exit_0_backend_only(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text("x = 1\n", encoding="utf-8")
    assert lpl.main(["--repo-root", str(tmp_path)]) == 0


def test_findings_categories_has_live_progress_fake() -> None:
    schema = json.loads(Path("qor/gates/schema/audit.schema.json").read_text(encoding="utf-8"))
    assert "live-progress-fake" in schema["properties"]["findings_categories"]["items"]["enum"]


def test_audit_invokes_live_progress_lint() -> None:
    text = Path("qor/skills/governance/qor-audit/SKILL.md").read_text(encoding="utf-8")
    assert "plan_live_progress_lint" in text  # prose-lint: ok=prompt-contract
