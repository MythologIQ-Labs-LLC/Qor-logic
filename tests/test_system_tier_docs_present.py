"""Phase 30 Phase 3: docs/{architecture,lifecycle,operations,policies}.md present + wired.

Asserts the four system-tier required documents exist, have substantive
content, and link back into the rest of the governance graph. Guards
against drift (e.g., someone deleting one of the four and forgetting that
Phase 30's doc_tier: system declaration depends on them).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"


def _nonempty(name: str, min_lines: int = 50) -> None:
    path = DOCS / name
    assert path.exists(), f"{name} missing at {path}"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= min_lines, f"{name} too short: {len(lines)} lines (need >= {min_lines})"


def test_architecture_md_exists_and_nonempty():
    _nonempty("architecture.md")


def test_lifecycle_md_exists_and_nonempty():
    _nonempty("lifecycle.md")


def test_operations_md_exists_and_nonempty():
    _nonempty("operations.md")


def test_policies_md_exists_and_nonempty():
    _nonempty("policies.md", min_lines=40)


def test_each_system_doc_links_back():
    """Each of the four system-tier docs must contain at least one markdown
    link into qor/references/, qor/gates/, or qor/skills/ -- proves wiring."""
    pattern = re.compile(r"\]\((?:\.\/)?(?:\.\.\/)?qor/(references|gates|skills)/")
    for name in ("architecture.md", "lifecycle.md", "operations.md", "policies.md"):
        body = (DOCS / name).read_text(encoding="utf-8")
        assert pattern.search(body), f"{name} has no backlinks into qor/; likely orphan"


def test_system_tier_check_passes():
    """Live doctrine self-check: running doc_integrity against the repo at
    doc_tier=system with Phase 30's plan_slug must pass post-Phase-3."""
    plan = {
        "doc_tier": "system",
        "terms": [
            {"term": "Check Surface D", "home": "qor/references/doctrine-documentation-integrity.md"},
            {"term": "Check Surface E", "home": "qor/references/doctrine-documentation-integrity.md"},
            {"term": "Session Rotation", "home": "qor/references/doctrine-governance-enforcement.md"},
            {"term": "Architecture Doc", "home": "docs/architecture.md"},
            {"term": "Lifecycle Doc", "home": "docs/lifecycle.md"},
            {"term": "Operations Doc", "home": "docs/operations.md"},
            {"term": "Policies Doc", "home": "docs/policies.md"},
        ],
        "plan_slug": "phase30-system-tier-hardening",
    }
    doc_integrity.run_all_checks_from_plan(plan, repo_root=str(REPO_ROOT))
