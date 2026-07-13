"""Phase 187 (GH #243): negative-constraints injection into weak-tier variants.

The kilo-code/codex/gemini compiled variants of the fabrication-risk
governance skills carry the NR-001/NR-002 preamble; the claude variant
(the install mirror of qor/skills source) stays byte-identical to source.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import dist_compile as compile_mod
from qor.scripts.dist_compile import (
    _FABRICATION_RISK_SKILLS,
    inject_negative_constraints,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

RISK_SKILL_MD = (
    "---\n"
    "name: qor-audit\n"
    "description: test fixture\n"
    "min_model_capability: opus\n"
    "---\n"
    "# /qor-audit - Gate Tribunal\n\nbody text\n"
)


def test_inject_adds_block_after_frontmatter():
    result = inject_negative_constraints(RISK_SKILL_MD, "qor-audit")
    assert "NR-001" in result and "NR-002" in result
    assert "doctrine-negative-constraints" in result
    # frontmatter intact and first
    assert result.startswith("---\nname: qor-audit\n")
    # block sits between frontmatter close and the title heading
    fm_end = result.index("\n---\n") + len("\n---\n")
    title = result.index("# /qor-audit - Gate Tribunal")
    block = result.index("NR-001")
    assert fm_end < block < title


def test_inject_noop_for_non_risk_skill():
    text = RISK_SKILL_MD.replace("qor-audit", "qor-ideate")
    assert inject_negative_constraints(text, "qor-ideate") == text


def test_inject_noop_without_frontmatter():
    text = "# /qor-audit - Gate Tribunal\n\nbody\n"
    assert inject_negative_constraints(text, "qor-audit") == text


def test_risk_set_names_the_three_governance_skills():
    assert _FABRICATION_RISK_SKILLS == {"qor-audit", "qor-plan", "qor-substantiate"}


def test_compile_all_injects_weak_tier_variants_only(tmp_path):
    """Integration over the REAL corpus: weak-tier variants carry the rules,
    the claude variant stays byte-identical to source."""
    out = tmp_path / "dist"
    compile_mod.compile_all(out)

    source = (REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    claude = (out / "variants" / "claude" / "skills" / "qor-audit" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert claude == source, "claude variant must remain the untransformed install mirror"
    assert "NR-001" not in claude.split("## Negative Constraints", 1)[0].split("---\n", 2)[-1].split("#", 1)[0]

    for target in ("kilo-code", "codex"):
        variant = (out / "variants" / target / "skills" / "qor-audit" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert "NR-001" in variant and "NR-002" in variant, f"{target} variant missing rules"
        assert variant.startswith("---\n"), f"{target} frontmatter must stay first"

    gemini = (out / "variants" / "gemini" / "commands" / "qor-audit.toml").read_text(
        encoding="utf-8"
    )
    assert "NR-001" in gemini and "NR-002" in gemini, "gemini command missing rules"

    # non-risk skill stays identity everywhere
    src_ideate = (REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-ideate" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    kilo_ideate = (out / "variants" / "kilo-code" / "skills" / "qor-ideate" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert kilo_ideate == src_ideate


# ----- Phase 188 (GH #244): cursor + cline variants -----

def test_compile_all_cursor_and_cline_variants(tmp_path):
    out = tmp_path / "dist"
    compile_mod.compile_all(out)

    # cursor: claude-shaped with risk-skill injection
    cursor_audit = (out / "variants" / "cursor" / "skills" / "qor-audit" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "NR-001" in cursor_audit and "NR-002" in cursor_audit
    src_ideate = (REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-ideate" / "SKILL.md").read_bytes()
    cursor_ideate = (out / "variants" / "cursor" / "skills" / "qor-ideate" / "SKILL.md").read_bytes()
    assert cursor_ideate == src_ideate

    # cline: flattened command files with injection
    cline_audit = (out / "variants" / "cline" / "workflows" / "command-qor-audit.md").read_text(
        encoding="utf-8"
    )
    assert "NR-001" in cline_audit and "NR-002" in cline_audit
    workflows = out / "variants" / "cline" / "workflows"
    commands = sorted(p.name for p in workflows.glob("command-*.md"))
    skill_dirs = compile_mod.list_source_skills(compile_mod.SKILLS_SRC)
    loose = compile_mod.list_loose_skills(compile_mod.SKILLS_SRC)
    assert len(commands) == len(skill_dirs) + len(loose), (
        f"cline must flatten every skill: {len(commands)} commands vs "
        f"{len(skill_dirs)} dirs + {len(loose)} loose"
    )
    agents = sorted(p.name for p in workflows.glob("agent-*.md"))
    assert len(agents) == len(compile_mod.list_source_agents(compile_mod.AGENTS_SRC))
