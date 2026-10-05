"""Phase 304: check that the repository is in its maintenance-freeze state.

Qor-logic is frozen and superseded. The frozen state is four properties of the
tree; each, if it regressed, would advertise active development or schedule new
work:

1. ``pyproject.toml`` declares exactly one ``Development Status`` classifier,
   and it is ``7 - Inactive``.
2. No dependabot configuration is committed.
3. No workflow under ``.github/workflows`` declares a ``schedule`` trigger.
4. ``README.md`` and ``AGENTS.md`` each carry a non-empty
   ``## Maintenance freeze`` section.

``check`` returns one violation per failed property instance, each starting
with the repository-relative path it concerns; ``[]`` means frozen. Workflows
are read with ``yaml.safe_load`` and a parse error propagates: the check fails
loudly rather than passing a file it could not read. The tested contract is the
regression set K0 to K6 in LD-2 of
``docs/plan-qor-phase304-maintenance-freeze.md``.
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

import yaml

FROZEN_CLASSIFIER = "Development Status :: 7 - Inactive"
FREEZE_HEADING = "## Maintenance freeze"
NOTICE_FILES = ("README.md", "AGENTS.md")
DEPENDABOT_FILES = (".github/dependabot.yml", ".github/dependabot.yaml")

_STATUS_PREFIX = "Development Status :: "
_WORKFLOWS_DIR = ".github/workflows"
_WORKFLOW_SUFFIXES = (".yml", ".yaml")


def _classifier_violations(root: Path) -> list[str]:
    path = root / "pyproject.toml"
    if not path.is_file():
        return ["pyproject.toml: file is missing"]
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    classifiers = data.get("project", {}).get("classifiers", [])
    statuses = [c for c in classifiers if c.startswith(_STATUS_PREFIX)]
    if statuses == [FROZEN_CLASSIFIER]:
        return []
    return [f"pyproject.toml: expected exactly {FROZEN_CLASSIFIER!r}, found {statuses!r}"]


def _dependabot_violations(root: Path) -> list[str]:
    return [
        f"{rel}: dependabot configuration is committed"
        for rel in DEPENDABOT_FILES
        if (root / rel).exists()
    ]


def _schedules(triggers: object) -> bool:
    if isinstance(triggers, (dict, list)):
        return "schedule" in triggers
    return triggers == "schedule"


def _declares_schedule(path: Path) -> bool:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return False
    # PyYAML (YAML 1.1) reads a bare `on:` key as the boolean True.
    return _schedules(data.get("on")) or _schedules(data.get(True))


def _schedule_violations(root: Path) -> list[str]:
    workflows = root / _WORKFLOWS_DIR
    if not workflows.is_dir():
        return []
    paths = sorted(
        p for p in workflows.iterdir() if p.is_file() and p.suffix in _WORKFLOW_SUFFIXES
    )
    return [
        f"{path.relative_to(root).as_posix()}: declares a schedule trigger"
        for path in paths
        if _declares_schedule(path)
    ]


def _section_body(lines: list[str]) -> list[str] | None:
    """Lines after the first FREEZE_HEADING up to the next `## ` line; None if absent."""
    if FREEZE_HEADING not in lines:
        return None
    rest = lines[lines.index(FREEZE_HEADING) + 1:]
    end = next((i for i, line in enumerate(rest) if line.startswith("## ")), len(rest))
    return rest[:end]


def _notice_violations(root: Path) -> list[str]:
    violations = []
    for name in NOTICE_FILES:
        path = root / name
        if not path.is_file():
            violations.append(f"{name}: file is missing")
            continue
        body = _section_body(path.read_text(encoding="utf-8").splitlines())
        if body is None:
            violations.append(f"{name}: no {FREEZE_HEADING!r} section")
        elif not any(line.strip() for line in body):
            violations.append(f"{name}: {FREEZE_HEADING!r} section is empty")
    return violations


def check(repo_root: Path) -> list[str]:
    root = Path(repo_root)
    return [
        *_classifier_violations(root),
        *_dependabot_violations(root),
        *_schedule_violations(root),
        *_notice_violations(root),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="freeze_check", description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    violations = check(args.repo_root)
    for violation in violations:
        print(violation)
    print(f"freeze_check: {len(violations)} violation(s)" if violations else "freeze_check: OK")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
