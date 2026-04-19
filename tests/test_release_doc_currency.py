"""Phase 33: release-doc currency rule.

check_documentation_currency gains a plan_payload parameter. When
plan_payload.change_class is in the release set (feature, breaking),
README.md and CHANGELOG.md must appear in implement's files_touched.
Hotfix is exempt. No plan_payload preserves Phase 31 behavior.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "qor" / "scripts"))
import doc_integrity_strict as dis


def _impl(files: list[str]) -> dict:
    return {"files_touched": files}


def _plan(change_class: str | None) -> dict:
    return {"change_class": change_class} if change_class else {}


def test_change_class_feature_requires_readme():
    out = dis.check_documentation_currency(
        _impl(["qor/scripts/foo.py", "CHANGELOG.md"]),
        repo_root=".",
        plan_payload=_plan("feature"),
    )
    assert any("README.md" in w for w in out)


def test_change_class_feature_requires_changelog():
    out = dis.check_documentation_currency(
        _impl(["qor/scripts/foo.py", "README.md"]),
        repo_root=".",
        plan_payload=_plan("feature"),
    )
    assert any("CHANGELOG.md" in w for w in out)


def test_change_class_breaking_requires_release_docs():
    out = dis.check_documentation_currency(
        _impl(["qor/scripts/foo.py"]),
        repo_root=".",
        plan_payload=_plan("breaking"),
    )
    joined = " ".join(out)
    assert "README.md" in joined and "CHANGELOG.md" in joined


def test_change_class_hotfix_exempt():
    out = dis.check_documentation_currency(
        _impl(["qor/scripts/foo.py"]),
        repo_root=".",
        plan_payload=_plan("hotfix"),
    )
    # Existing system-tier warning may fire (trigger file touched, no system doc),
    # but the new release-doc branch must NOT fire.
    assert not any("Release-path" in w for w in out)


def test_change_class_feature_with_both_covers():
    out = dis.check_documentation_currency(
        _impl(["README.md", "CHANGELOG.md"]),
        repo_root=".",
        plan_payload=_plan("feature"),
    )
    assert not any("Release-path" in w for w in out)


def test_no_plan_payload_no_release_docs_warning():
    out = dis.check_documentation_currency(
        _impl(["qor/scripts/foo.py"]),
        repo_root=".",
        plan_payload=None,
    )
    # Legacy call site: release-doc branch skipped. Only system-tier warning
    # (existing Phase 31 behavior).
    assert not any("Release-path" in w for w in out)
