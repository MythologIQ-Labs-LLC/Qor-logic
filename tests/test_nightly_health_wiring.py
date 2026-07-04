"""Phase 165: structural properties of the nightly-health workflow.

Text/regex assertions (no YAML parser dependency) over the workflow file --
the same property-test approach as the release-immutability guards. Each test
names the failure mode it locks (issue-named regression guards per GH #250c).
"""
from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "nightly-health.yml"


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_declares_schedule_dispatch_and_permissions():
    text = _text()
    assert re.search(r"^\s*schedule:\s*$", text, re.MULTILINE), "nightly cron trigger missing"
    assert re.search(r"cron:\s*'0 9 \* \* \*'", text), "expected daily 09:00 UTC cron"
    assert "workflow_dispatch:" in text, "manual trigger missing (needed for post-merge D4 evidence)"
    assert re.search(r"issues:\s*write", text), "issue lifecycle needs issues: write"
    assert re.search(r"contents:\s*read", text), "checkout needs contents: read"
    assert not re.search(r"(contents|id-token|actions|packages):\s*write", text), (
        "nightly-health must not carry write permissions beyond issues"
    )


def test_workflow_runs_self_test_before_status_and_uses_lifecycle_idioms():
    text = _text()
    self_test = text.index("qor.scripts.status_json --self-test")
    status_run = text.index("qor.scripts.status_json --repo-root")
    assert self_test < status_run, "checker must validate itself before its verdict is trusted"
    assert "gh issue list --search" in text, "lifecycle: existing-issue search missing"
    assert "gh issue create" in text, "lifecycle: create path missing"
    assert "gh issue close" in text, "lifecycle: close path missing"
    title_key = "Nightly governance health"
    assert text.count(title_key) >= 2, "title key must appear in both create and close paths"
    # OWASP A03 (audit binding note): JSON payload reaches gh via env, never
    # inline ${{ }} interpolation inside a run body.
    run_bodies = re.findall(r"run: \|([\s\S]*?)(?=\n      - |\Z)", text)
    for body in run_bodies:
        assert "${{ steps." not in body, (
            "step output interpolated into a run body (Actions script-injection surface); "
            "pass it via env: instead"
        )
