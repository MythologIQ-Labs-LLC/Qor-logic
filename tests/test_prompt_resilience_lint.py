"""Phase 25 Phase 2: prompt resilience lint (doctrine enforcement)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from yaml import safe_load


_BANNED_PHRASES = [
    r"wait for user",
    r"confirm before",
    r"pause here",
    r"Ready to proceed\?",
    r"Continue\?",
    r"Ask the user to proceed",
]
_BANNED_RE = re.compile("|".join(_BANNED_PHRASES), re.IGNORECASE)
_ALLOW_PAUSE_MARKER = "<!-- qor:allow-pause"
_RECOVERY_PROMPT_MARKER = "<!-- qor:recovery-prompt -->"
_AUTO_HEAL_MARKER = "<!-- qor:auto-heal -->"
_FAIL_FAST_MARKER = "<!-- qor:fail-fast-only"
_BREAK_GLASS_MARKER = "<!-- qor:break-the-glass"
_INTERDICTION_RE = re.compile(r"\*\*INTERDICTION\*\*")


def _read_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    meta = safe_load(text[4:end]) or {}
    return meta if isinstance(meta, dict) else {}


def _autonomy(text: str) -> str:
    meta = _read_frontmatter(text)
    val = meta.get("autonomy", "interactive")
    return val if val in ("autonomous", "interactive") else "interactive"


def _banned_phrase_hits(lines: list[str]) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for i, line in enumerate(lines, start=1):
        if not _BANNED_RE.search(line):
            continue
        window = "\n".join(lines[max(0, i - 3):i])
        if _ALLOW_PAUSE_MARKER in window:
            continue
        hits.append((i, line.strip()))
    return hits


def _abort_without_recovery(lines: list[str], mode: str) -> list[tuple[int, str]]:
    """Flag INTERDICTION blocks lacking the mode-specific recovery marker.

    Only formal `**INTERDICTION**` headers count; shell `|| ABORT` patterns
    and narrative ABORT prose are out of scope.
    """
    violations: list[tuple[int, str]] = []
    needed = _AUTO_HEAL_MARKER if mode == "autonomous" else _RECOVERY_PROMPT_MARKER
    justifier = _BREAK_GLASS_MARKER if mode == "autonomous" else _FAIL_FAST_MARKER
    for i, line in enumerate(lines, start=1):
        if not _INTERDICTION_RE.search(line):
            continue
        start = max(0, i - 3)
        end = min(len(lines), i + 15)
        window = "\n".join(lines[start:end])
        if needed in window or justifier in window:
            continue
        violations.append((i, line.strip()))
    return violations


def _autonomous_has_recovery_prompt(text: str) -> bool:
    return _RECOVERY_PROMPT_MARKER in text


def _walk_skills() -> list[Path]:
    root = Path(__file__).resolve().parent.parent / "qor" / "skills"
    skill_mds = list(root.rglob("SKILL.md"))
    loose_mds = [p for p in root.rglob("*.md") if p.name != "SKILL.md" and "/references/" not in p.as_posix()]
    return skill_mds + loose_mds


def _lint_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    mode = _autonomy(text)
    errors: list[str] = []
    for lineno, content in _banned_phrase_hits(lines):
        errors.append(f"{path}:{lineno}: banned phrase (mode={mode}): {content}")
    for lineno, content in _abort_without_recovery(lines, mode):
        errors.append(f"{path}:{lineno}: ABORT/INTERDICTION without recovery marker (mode={mode}): {content}")
    if mode == "autonomous" and _autonomous_has_recovery_prompt(text):
        errors.append(f"{path}: autonomous skill must not use qor:recovery-prompt (use qor:auto-heal)")
    return errors


def test_fixture_interactive_good_passes():
    fx = Path(__file__).parent / "fixtures" / "skill_interactive_good.md"
    assert _lint_file(fx) == []


def test_fixture_interactive_bad_fails():
    fx = Path(__file__).parent / "fixtures" / "skill_interactive_bad.md"
    errors = _lint_file(fx)
    assert errors, "Bad fixture must fail lint"
    joined = "\n".join(errors)
    assert "banned phrase" in joined or "ABORT" in joined


def test_fixture_autonomous_good_passes():
    fx = Path(__file__).parent / "fixtures" / "skill_autonomous_good.md"
    assert _lint_file(fx) == []


def test_fixture_autonomous_bad_fails():
    fx = Path(__file__).parent / "fixtures" / "skill_autonomous_bad.md"
    errors = _lint_file(fx)
    assert errors, "Bad autonomous fixture must fail lint"
    joined = "\n".join(errors)
    assert "autonomous skill must not use qor:recovery-prompt" in joined or "banned phrase" in joined


def test_all_project_skills_pass_lint():
    all_errors: list[str] = []
    for path in _walk_skills():
        if "/vendor/" in path.as_posix() or "\\vendor\\" in str(path):
            continue
        all_errors.extend(_lint_file(path))
    assert not all_errors, (
        "Prompt resilience violations:\n  " + "\n  ".join(all_errors)
    )
