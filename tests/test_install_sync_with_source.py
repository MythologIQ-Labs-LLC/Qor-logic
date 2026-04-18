"""Phase 31 Phase 1: dist variants must stay byte-identical to source skills.

Catches the Phase 28-30 class of dist drift at CI time. If `dist_compile`
regresses or an operator forgets to recompile after a SKILL.md edit, this
test fails with the specific mismatching pair.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_SKILLS_ROOT = REPO_ROOT / "qor" / "skills"
VARIANTS_ROOT = REPO_ROOT / "qor" / "dist" / "variants"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _source_skills() -> list[Path]:
    return sorted(SOURCE_SKILLS_ROOT.rglob("SKILL.md"))


def _variant_counterpart(variant: str, source: Path) -> Path:
    rel = source.relative_to(SOURCE_SKILLS_ROOT)
    # Source layout: qor/skills/<category>/<skill-name>/SKILL.md
    # Variant layout: qor/dist/variants/<variant>/skills/<skill-name>/SKILL.md
    # The <category> dimension is flattened away by dist_compile.
    skill_dir = rel.parent.name
    return VARIANTS_ROOT / variant / "skills" / skill_dir / "SKILL.md"


def _check_variant(variant: str) -> list[str]:
    mismatches: list[str] = []
    for source in _source_skills():
        counterpart = _variant_counterpart(variant, source)
        if not counterpart.exists():
            mismatches.append(f"MISSING: {counterpart.relative_to(REPO_ROOT)}")
            continue
        if _sha256(source) != _sha256(counterpart):
            mismatches.append(
                f"DRIFT: {source.relative_to(REPO_ROOT)} vs {counterpart.relative_to(REPO_ROOT)}"
            )
    return mismatches


def test_claude_variant_skill_sync():
    mismatches = _check_variant("claude")
    assert not mismatches, "Run `python -m qor.scripts.dist_compile`:\n  " + "\n  ".join(mismatches)


def test_codex_variant_skill_sync():
    mismatches = _check_variant("codex")
    assert not mismatches, "Run `python -m qor.scripts.dist_compile`:\n  " + "\n  ".join(mismatches)


def test_kilo_code_variant_skill_sync():
    mismatches = _check_variant("kilo-code")
    assert not mismatches, "Run `python -m qor.scripts.dist_compile`:\n  " + "\n  ".join(mismatches)


def test_gemini_variant_excluded_intentionally():
    """Gemini produces TOML command files, not SKILL.md. Byte-identical
    sync is not the right test for gemini; a separate test would need to
    parse TOML and compare semantic content. Documented exclusion."""
    gemini_commands = VARIANTS_ROOT / "gemini" / "commands"
    assert gemini_commands.exists(), "Gemini variant should still exist, just in TOML form"
