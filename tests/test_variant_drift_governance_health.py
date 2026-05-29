"""Phase 109 D-109.3: generated variants preserve the source preflight markers.

Asserts the build neither drops nor invents preflight markers: each variant's
marker count equals the source skill-corpus count.
"""
from __future__ import annotations

from pathlib import Path

_MARKER = "qor:governance-health-preflight"
_VARIANTS = ("claude", "codex", "kilo-code")


def _count_marked(root: Path) -> int:
    return sum(
        1
        for skill in root.rglob("SKILL.md")
        if _MARKER in skill.read_text(encoding="utf-8")
    )


def _repo() -> Path:
    return Path(__file__).resolve().parent.parent


def test_generated_variants_contain_preflight_markers():
    repo = _repo()
    source_count = _count_marked(repo / "qor" / "skills")
    assert source_count >= 1, "expected source skills to carry the preflight marker"
    for variant in _VARIANTS:
        variant_skills = repo / "qor" / "dist" / "variants" / variant / "skills"
        assert variant_skills.is_dir(), f"missing variant skills dir: {variant_skills}"
        generated_count = _count_marked(variant_skills)
        assert generated_count == source_count, (
            f"{variant}: generated marker count {generated_count} != source {source_count}"
        )
