"""Phase 55: tests for compute_skill_admission_attributes helper."""
from __future__ import annotations

import textwrap
from pathlib import Path

from qor.policy.resource_attributes import (
    _CANONICAL_TOOLS,
    compute_skill_admission_attributes,
)


def _write_skill(tmp_path: Path, name: str, frontmatter: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
    return p


def test_compute_skill_admission_attributes_returns_expected_shape(tmp_path):
    skill = _write_skill(tmp_path, "s.md",
        "name: x\npermitted_tools: [Read]\npermitted_subagents: []",
        "Tool: Read\n",
    )
    attrs = compute_skill_admission_attributes(skill)
    assert set(attrs.keys()) == {
        "registered", "has_frontmatter",
        "actual_tool_invocations_exceed_scope",
        "actual_subagent_invocations_exceed_scope",
    }


def test_helper_grep_detects_bash_invocation(tmp_path):
    skill = _write_skill(tmp_path, "s.md",
        "permitted_tools: [Read]\npermitted_subagents: []",
        "```bash\nls -la\n```\n",
    )
    attrs = compute_skill_admission_attributes(skill)
    assert attrs["actual_tool_invocations_exceed_scope"] is True


def test_helper_grep_detects_agent_invocation_with_subagent_type(tmp_path):
    skill = _write_skill(tmp_path, "s.md",
        "permitted_tools: [Read]\npermitted_subagents: []",
        'use: Agent(subagent_type="general-purpose")\n',
    )
    attrs = compute_skill_admission_attributes(skill)
    assert attrs["actual_subagent_invocations_exceed_scope"] is True


def test_helper_handles_skills_without_permitted_tools_frontmatter(tmp_path):
    skill = _write_skill(tmp_path, "s.md", "name: x", "Tool: Read\n")
    attrs = compute_skill_admission_attributes(skill)
    assert attrs["actual_tool_invocations_exceed_scope"] is True


def test_helper_passes_when_actual_tools_subset_of_declared(tmp_path):
    skill = _write_skill(tmp_path, "s.md",
        "permitted_tools: [Read, Grep, Bash]\npermitted_subagents: []",
        "```bash\necho hi\n```\nTool: Read\nTool: Grep\n",
    )
    attrs = compute_skill_admission_attributes(skill)
    assert attrs["actual_tool_invocations_exceed_scope"] is False


def test_helper_passes_when_subagent_invocation_in_allowlist(tmp_path):
    skill = _write_skill(tmp_path, "s.md",
        'permitted_tools: []\npermitted_subagents: [general-purpose]',
        'Agent(subagent_type="general-purpose")\n',
    )
    attrs = compute_skill_admission_attributes(skill)
    assert attrs["actual_subagent_invocations_exceed_scope"] is False


def test_helper_handles_block_list_yaml_shape(tmp_path):
    skill = _write_skill(tmp_path, "s.md",
        "permitted_tools:\n  - Read\n  - Grep\npermitted_subagents:\n  - explore",
        "Tool: Read\n",
    )
    attrs = compute_skill_admission_attributes(skill)
    assert attrs["actual_tool_invocations_exceed_scope"] is False


def test_helper_returns_unregistered_for_missing_path(tmp_path):
    attrs = compute_skill_admission_attributes(tmp_path / "nonexistent.md")
    assert attrs["registered"] is False
    assert attrs["has_frontmatter"] is False
    assert attrs["actual_tool_invocations_exceed_scope"] is True


def test_canonical_tools_set_is_frozen():
    assert isinstance(_CANONICAL_TOOLS, frozenset)
    assert "Read" in _CANONICAL_TOOLS
    assert "Bash" in _CANONICAL_TOOLS
    assert "Agent" in _CANONICAL_TOOLS
    assert len(_CANONICAL_TOOLS) >= 8
