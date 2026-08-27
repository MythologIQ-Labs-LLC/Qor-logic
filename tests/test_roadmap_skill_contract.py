from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_roadmap_skill_is_meta_and_delegation_first() -> None:
    skill = (ROOT / "qor/skills/meta/qor-roadmap/SKILL.md").read_text(encoding="utf-8")
    delegation = (ROOT / "qor/gates/delegation-table.md").read_text(encoding="utf-8")

    assert "phase: meta" in skill  # prose-lint: ok=prompt-contract metadata is the behavior surface
    assert "phase: roadmap" not in skill
    assert "permitted_tools: [Read, Grep, Glob, Bash]" in skill  # prose-lint: ok=prompt-contract tool authority is declarative
    assert "`qor-roadmap` | Problem framing is missing" in delegation
    assert "`qor-roadmap` | A fact node requires investigation" in delegation
    assert "`qor-roadmap` | Named planning scope" in delegation


def test_roadmap_skill_stops_at_plan_and_owns_no_implementation_path() -> None:
    skill = (ROOT / "qor/skills/meta/qor-roadmap/SKILL.md").read_text(encoding="utf-8")

    assert "**NEVER** modify production implementation from Roadmap." in skill  # prose-lint: ok=prompt-contract production-write boundary
    assert "**ALWAYS** stop at `/qor-plan` handoff." in skill  # prose-lint: ok=prompt-contract lifecycle handoff boundary
    assert "implementation-task nodes" in skill  # prose-lint: ok=prompt-contract roadmap excludes implementation decomposition
