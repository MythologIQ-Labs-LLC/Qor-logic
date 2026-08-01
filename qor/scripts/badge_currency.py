"""Badge currency check for README.md.

Pure functions for counting current-truth values (tests, ledger entries,
skills, agents, doctrines) and parsing the declared values in README badges.
Used by tests and by `/qor-substantiate` Step 6.5 to ABORT seal on mismatch
for feature/breaking phases.

Skill, agent, and doctrine layouts are declarable. Missing configured roots
are resolution errors, never a synthetic zero count. Counted paths must be
regular files physically confined to both the repository and declared root.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_BADGE_RE = re.compile(
    r"badge/(Tests|Ledger|Skills|Agents|Doctrines)-(\d+)",
    re.IGNORECASE,
)

DEFAULT_SKILLS_ROOT = Path("qor/skills")
DEFAULT_SKILLS_PATTERN = "**/SKILL.md"
DEFAULT_AGENTS_ROOT = Path("qor/agents")
DEFAULT_AGENTS_PATTERN = "**/*.md"
DEFAULT_DOCTRINES_ROOT = Path("qor/references")
DEFAULT_DOCTRINES_PATTERN = "doctrine-*.md"


class BadgeLayoutError(ValueError):
    """Configured badge-count layout cannot be resolved safely."""


def _resolve_count_root(repo_root: Path, configured_root: Path, label: str) -> Path:
    """Resolve a configured root within the repository and require a directory."""
    repository = repo_root.resolve()
    root = configured_root if configured_root.is_absolute() else repository / configured_root
    resolved = root.resolve()
    try:
        resolved.relative_to(repository)
    except ValueError:
        raise BadgeLayoutError(
            f"{label} root must stay within repo root: {configured_root}"
        ) from None
    if not resolved.is_dir():
        raise BadgeLayoutError(
            f"{label} root not found: {configured_root} "
            f"(resolved to {resolved}); declare the repository layout explicitly"
        )
    return resolved


def _count_matching(
    repo_root: Path,
    configured_root: Path,
    pattern: str,
    label: str,
) -> int:
    """Count confined regular files under a validated root and relative glob."""
    if not pattern.strip():
        raise BadgeLayoutError(f"{label} pattern must not be empty")
    pattern_path = Path(pattern)
    if pattern_path.is_absolute() or ".." in pattern_path.parts:
        raise BadgeLayoutError(
            f"{label} pattern must be relative and must not traverse parents: {pattern}"
        )

    repository = repo_root.resolve()
    root = _resolve_count_root(repository, configured_root, label)
    count = 0
    for path in root.glob(pattern):
        if path.is_symlink():
            raise BadgeLayoutError(f"{label} match must not be a symlink: {path}")
        if not path.is_file():
            continue
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(repository)
            resolved.relative_to(root)
        except (OSError, ValueError) as exc:
            raise BadgeLayoutError(
                f"{label} match escapes the declared root or repository: {path}"
            ) from exc
        count += 1
    return count


def count_tests(repo_root: Path) -> int:
    """Run pytest --collect-only and parse the collected count.

    Explicitly targets the `tests/` directory and uses the repo's pyproject
    config to avoid stray collection from ad-hoc paths. Picks the first clean
    matching summary line going backwards through stdout.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    summary_re = re.compile(r"(\d+)(?:/\d+)?\s+tests?\s+collected")
    clean = None
    fallback = None
    for line in reversed(result.stdout.splitlines()):
        match = summary_re.search(line)
        if not match:
            continue
        if "error" not in line.lower():
            clean = int(match.group(1))
            break
        if fallback is None:
            fallback = int(match.group(1))
    if clean is not None:
        return clean
    if fallback is not None:
        return fallback
    raise RuntimeError(
        f"could not parse pytest collected-count: {result.stdout[-500:]!r}"
    )


def count_ledger_entries(ledger_path: Path) -> int:
    """Count `### Entry #` headers in META_LEDGER.md."""
    text = ledger_path.read_text(encoding="utf-8")
    return len(re.findall(r"^### Entry #", text, re.MULTILINE))


def count_skills(
    repo_root: Path,
    root: Path = DEFAULT_SKILLS_ROOT,
    pattern: str = DEFAULT_SKILLS_PATTERN,
) -> int:
    """Count skill files under a declared root and relative glob pattern."""
    return _count_matching(repo_root, root, pattern, "skills")


def count_agents(
    repo_root: Path,
    root: Path = DEFAULT_AGENTS_ROOT,
    pattern: str = DEFAULT_AGENTS_PATTERN,
) -> int:
    """Count agent files under a declared root and relative glob pattern."""
    return _count_matching(repo_root, root, pattern, "agents")


def count_doctrines(
    repo_root: Path,
    root: Path = DEFAULT_DOCTRINES_ROOT,
    pattern: str = DEFAULT_DOCTRINES_PATTERN,
) -> int:
    """Count doctrine files under a declared root and relative glob pattern."""
    return _count_matching(repo_root, root, pattern, "doctrines")


def parse_readme_badges(readme_path: Path) -> dict[str, int]:
    """Parse README.md badge HTML and return declared badge values."""
    text = readme_path.read_text(encoding="utf-8")
    out: dict[str, int] = {}
    for match in _BADGE_RE.finditer(text):
        out[match.group(1).lower()] = int(match.group(2))
    return out


def check_currency(
    repo_root: Path,
    ledger_path: Path,
    tests_tolerance: int = 5,
    skip_tests: bool = False,
    *,
    skills_root: Path = DEFAULT_SKILLS_ROOT,
    skills_pattern: str = DEFAULT_SKILLS_PATTERN,
    agents_root: Path = DEFAULT_AGENTS_ROOT,
    agents_pattern: str = DEFAULT_AGENTS_PATTERN,
    doctrines_root: Path = DEFAULT_DOCTRINES_ROOT,
    doctrines_pattern: str = DEFAULT_DOCTRINES_PATTERN,
) -> list[str]:
    """Return mismatch descriptions; an empty list means current."""
    declared = parse_readme_badges(repo_root / "README.md")
    truth = {
        "ledger": count_ledger_entries(ledger_path),
        "skills": count_skills(repo_root, skills_root, skills_pattern),
        "agents": count_agents(repo_root, agents_root, agents_pattern),
        "doctrines": count_doctrines(repo_root, doctrines_root, doctrines_pattern),
    }
    if not skip_tests:
        truth["tests"] = count_tests(repo_root)

    mismatches: list[str] = []
    for key, actual in truth.items():
        declared_value = declared.get(key)
        if declared_value is None:
            mismatches.append(f"{key}: README has no badge")
            continue
        if key == "tests":
            if abs(declared_value - actual) > tests_tolerance:
                mismatches.append(
                    f"tests: README declares {declared_value}, truth {actual} "
                    f"(tolerance ±{tests_tolerance})"
                )
        elif declared_value != actual:
            mismatches.append(
                f"{key}: README declares {declared_value}, truth {actual}"
            )
    return mismatches


def _add_layout_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--skills-root", type=Path, default=DEFAULT_SKILLS_ROOT)
    parser.add_argument("--skills-pattern", default=DEFAULT_SKILLS_PATTERN)
    parser.add_argument("--agents-root", type=Path, default=DEFAULT_AGENTS_ROOT)
    parser.add_argument("--agents-pattern", default=DEFAULT_AGENTS_PATTERN)
    parser.add_argument("--doctrines-root", type=Path, default=DEFAULT_DOCTRINES_ROOT)
    parser.add_argument("--doctrines-pattern", default=DEFAULT_DOCTRINES_PATTERN)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--ledger", type=Path, default=Path("docs/META_LEDGER.md"))
    _add_layout_args(parser)
    args = parser.parse_args(argv)
    try:
        mismatches = check_currency(
            args.repo_root,
            args.ledger,
            skills_root=args.skills_root,
            skills_pattern=args.skills_pattern,
            agents_root=args.agents_root,
            agents_pattern=args.agents_pattern,
            doctrines_root=args.doctrines_root,
            doctrines_pattern=args.doctrines_pattern,
        )
    except (BadgeLayoutError, OSError, RuntimeError) as exc:
        print(f"FAIL: badge currency truth could not be resolved: {exc}")
        return 1
    if mismatches:
        print("FAIL: README badge currency mismatch:")
        for mismatch in mismatches:
            print(f"  {mismatch}")
        return 1
    print("OK: README badges current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
