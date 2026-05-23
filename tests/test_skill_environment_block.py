"""Phase 90: enforce ## Environment block + WARN-only preflight one-liner
across every Qor-logic skill that invokes `python -m qor.reliability.*` or
`python -m qor.scripts.*` (GH #79).

Coverage check across the production skill set under qor/skills/. Per
qor/references/doctrine-test-functionality.md, each assertion verifies an
operative property (install-contract substrings; Phase 75 SKIP-fallback
cross-reference; WARN-only preflight, not ABORT) rather than mere
section-header presence.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "qor" / "skills"

# Pattern matching skill bodies that invoke qor.reliability or qor.scripts
# modules (the surface GH #79 targets). Skills not matching this need no
# Environment block; skills matching this MUST carry one.
#
# Requires a specific submodule (`\.\w+`) so the contract-documentation
# string "python -m qor.reliability.*" in the Environment block prose
# (which describes the invocation pattern abstractly) does not itself
# count as an invocation that demands a preflight before it.
_PYTHON_QOR_INVOCATION_RE = re.compile(
    r"python\s+-m\s+qor\.(?:reliability|scripts)\.\w+\b"
)


def _python_invoking_skills() -> list[Path]:
    """SKILL.md files under qor/skills/ that grep-match the invocation pattern."""
    return sorted(
        p for p in SKILLS_ROOT.rglob("SKILL.md")
        if _PYTHON_QOR_INVOCATION_RE.search(p.read_text(encoding="utf-8"))
    )


def _section(text: str, header_pattern: str) -> str:
    """Body of the first '## ' section whose header matches header_pattern,
    up to the next '## ' header (not '### ' subheaders)."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and not line.startswith("### ") and re.search(
            header_pattern, line
        ):
            start = i
            break
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start + 1:]:
        if line.startswith("## ") and not line.startswith("### "):
            break
        body.append(line)
    return "\n".join(body)


def test_at_least_one_python_invoking_skill_exists():
    """Precondition: the lint sweep must have something to sweep.

    If this fails, the grep pattern drifted or all skills were rewritten to
    use the qor-logic CLI surface (Option A from GH #79). Either way, the
    rest of the suite needs revisiting.
    """
    skills = _python_invoking_skills()
    assert len(skills) >= 5, (
        f"expected >=5 Python-invoking skills under qor/skills/, found "
        f"{len(skills)}: {[str(s.relative_to(REPO_ROOT)) for s in skills]}"
    )


def test_each_python_invoking_skill_has_environment_section():
    failures: list[str] = []
    for skill in _python_invoking_skills():
        text = skill.read_text(encoding="utf-8")
        section = _section(text, r"^##\s+Environment\b")
        if not section:
            failures.append(str(skill.relative_to(REPO_ROOT)))
    assert not failures, (
        "skills invoking 'python -m qor.(reliability|scripts)' must carry "
        "a '## Environment' section per Phase 90 (GH #79):\n  "
        + "\n  ".join(failures)
    )


def test_environment_block_cites_install_contract():
    """Two-substring assertion guards against partial decay (one fix removed)."""
    failures: list[str] = []
    for skill in _python_invoking_skills():
        text = skill.read_text(encoding="utf-8")
        section = _section(text, r"^##\s+Environment\b")
        rel = str(skill.relative_to(REPO_ROOT))
        if "pip show qor-logic" not in section:
            failures.append(f"{rel}: missing 'pip show qor-logic' check")
        if "pipx install qor-logic" not in section:
            failures.append(f"{rel}: missing 'pipx install qor-logic' fallback")
    assert not failures, (
        "Environment block must cite both the venv-check and global-install "
        "fixes:\n  " + "\n  ".join(failures)
    )


def test_environment_block_cites_phase_75_skip_fallback():
    """Guard against the prose decaying into an Option-A-style absolute
    contract that breaks non-Python hosts."""
    failures: list[str] = []
    for skill in _python_invoking_skills():
        text = skill.read_text(encoding="utf-8")
        section = _section(text, r"^##\s+Environment\b")
        rel = str(skill.relative_to(REPO_ROOT))
        if "Phase 75" not in section:
            failures.append(f"{rel}: missing 'Phase 75' cross-reference")
        if "gate_skipped_prerequisite_absent" not in section:
            failures.append(
                f"{rel}: missing 'gate_skipped_prerequisite_absent' event name "
                "(the operative Phase 75 SKIP signal)"
            )
    assert not failures, (
        "Environment block must cross-reference the Phase 75 SKIP fallback:\n  "
        + "\n  ".join(failures)
    )


def test_each_python_invoking_skill_has_preflight_one_liner():
    """The preflight must appear BEFORE the first `python -m qor.X`
    invocation in the file so misconfiguration is surfaced once at skill
    entry. Semantically stronger than 'after Execution Protocol heading'
    because skills use various protocol-section names (`Execution
    Protocol`, `Bundle protocol`, etc.) — the universal anchor is the
    first qor-module invocation itself.
    """
    failures: list[str] = []
    canonical_check = 'python -c "import qor.reliability"'
    for skill in _python_invoking_skills():
        text = skill.read_text(encoding="utf-8")
        rel = str(skill.relative_to(REPO_ROOT))
        first_invocation = _PYTHON_QOR_INVOCATION_RE.search(text)
        if not first_invocation:
            failures.append(
                f"{rel}: precondition violated -- skill matched grep but no "
                f"invocation found by the regex"
            )
            continue
        preflight_pos = text.find(canonical_check)
        if preflight_pos < 0:
            failures.append(f"{rel}: preflight '{canonical_check}' not present")
            continue
        if preflight_pos > first_invocation.start():
            failures.append(
                f"{rel}: preflight at offset {preflight_pos} appears AFTER "
                f"first qor invocation at offset {first_invocation.start()}; "
                f"must precede to surface misconfiguration before the SKIP cascade"
            )
    assert not failures, (
        "Phase 90 preflight (GH #79) must precede the first qor.module "
        "invocation:\n  " + "\n  ".join(failures)
    )


def test_preflight_is_warn_only_not_abort():
    """Preflight must NOT use `exit 1` or `|| ABORT` so Phase 75 SKIP
    fallback remains intact on non-Python hosts.

    Isolates the 6-line window starting at the preflight anchor; checks
    that window for abort-flavor tokens. Boundary: a larger window could
    pick up unrelated ABORTs from other steps; 6 lines covers the
    preflight if-block.
    """
    failures: list[str] = []
    anchor = 'python -c "import qor.reliability"'
    for skill in _python_invoking_skills():
        text = skill.read_text(encoding="utf-8")
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if anchor in line:
                window = "\n".join(lines[i:i + 6])
                rel = str(skill.relative_to(REPO_ROOT))
                if "exit 1" in window:
                    failures.append(
                        f"{rel}: preflight contains 'exit 1' (must be WARN-only)"
                    )
                if "|| ABORT" in window:
                    failures.append(
                        f"{rel}: preflight contains '|| ABORT' (must be WARN-only)"
                    )
                break
    assert not failures, (
        "Phase 90 preflight must be WARN-only (Phase 75 SKIP fallback preserved):\n  "
        + "\n  ".join(failures)
    )


def test_no_new_skills_invoke_python_qor_without_environment_block():
    """Forward-only structural guard: any future SKILL.md added to
    qor/skills/ that grep-matches the invocation pattern must carry the
    Environment block. Identical shape to
    test_each_python_invoking_skill_has_environment_section but framed as a
    drift-prevention check rather than a coverage check; both guard the
    same invariant from different framings.
    """
    skills = _python_invoking_skills()
    missing = [
        str(s.relative_to(REPO_ROOT))
        for s in skills
        if not _section(s.read_text(encoding="utf-8"), r"^##\s+Environment\b")
    ]
    assert not missing, (
        "future-skill drift: SKILL.md files invoking 'python -m qor.X' "
        "without the Phase 90 Environment block (GH #79):\n  "
        + "\n  ".join(missing)
    )
