"""Phase 55: skill admission tool-scope enforcement tests."""
from __future__ import annotations

import textwrap
from pathlib import Path

from qor.reliability.skill_admission import check_admission, check_tool_scope

REPO_ROOT = Path(__file__).resolve().parent.parent

_EIGHT_SCOPED_SKILLS = (
    ("qor-research", "qor/skills/sdlc/qor-research/SKILL.md"),
    ("qor-plan", "qor/skills/sdlc/qor-plan/SKILL.md"),
    ("qor-implement", "qor/skills/sdlc/qor-implement/SKILL.md"),
    ("qor-refactor", "qor/skills/sdlc/qor-refactor/SKILL.md"),
    ("qor-audit", "qor/skills/governance/qor-audit/SKILL.md"),
    ("qor-substantiate", "qor/skills/governance/qor-substantiate/SKILL.md"),
    ("qor-validate", "qor/skills/governance/qor-validate/SKILL.md"),
    ("qor-repo-audit", "qor/skills/meta/qor-repo-audit/SKILL.md"),
)


def _write_skill(tmp_path: Path, frontmatter: str, body: str) -> Path:
    p = tmp_path / "SKILL.md"
    p.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
    return p


def test_admit_accepts_skill_with_matching_tool_scope(tmp_path):
    skill = _write_skill(tmp_path,
        "permitted_tools: [Read, Grep]\npermitted_subagents: []",
        "Tool: Read\nTool: Grep\n")
    ok, msg = check_tool_scope("test-skill", skill)
    assert ok, msg


def test_admit_rejects_skill_with_tool_invocation_exceeding_scope(tmp_path):
    skill = _write_skill(tmp_path,
        "permitted_tools: [Read]\npermitted_subagents: []",
        "```bash\necho hi\n```\n")
    ok, msg = check_tool_scope("test-skill", skill)
    assert not ok
    assert "tool-scope-exceeded" in msg


def test_admit_rejects_skill_with_subagent_invocation_exceeding_scope(tmp_path):
    skill = _write_skill(tmp_path,
        "permitted_tools: []\npermitted_subagents: []",
        'Agent(subagent_type="general-purpose")\n')
    ok, msg = check_tool_scope("test-skill", skill)
    assert not ok
    assert "subagent-scope-exceeded" in msg


def test_admit_skips_skills_without_advisory_frontmatter(tmp_path):
    """Skills lacking permitted_tools/permitted_subagents declarations are
    advisory-only (Phase 54 posture); admission does not enforce."""
    skill = _write_skill(tmp_path, "name: x", "Tool: Read\n")
    ok, _ = check_tool_scope("test-skill", skill)
    assert ok


def test_admit_passes_for_eight_actual_repo_skills():
    """Self-application: this Phase 55 implementation must satisfy its own policy."""
    failed: list[str] = []
    for name, rel in _EIGHT_SCOPED_SKILLS:
        path = REPO_ROOT / rel
        if not path.exists():
            failed.append(f"{name}: missing path {rel}")
            continue
        ok, msg = check_tool_scope(name, path)
        if not ok:
            failed.append(f"{name}: {msg}")
    assert not failed, "Phase 55 self-application FAILED:\n  " + "\n  ".join(failed)


def test_canonical_tools_set_includes_documented_tool_names():
    """Round-trip integrity: _CANONICAL_TOOLS matches Tool names a typical
    skill cites. Pre-doctrine check; full doctrine round-trip lands when
    doctrine-ai-rmf.md Tool-scope policy section is authored."""
    from qor.policy.resource_attributes import _CANONICAL_TOOLS
    for tool in ("Read", "Write", "Edit", "Glob", "Grep", "Bash", "Agent"):
        assert tool in _CANONICAL_TOOLS, f"canonical tool set missing {tool}"
