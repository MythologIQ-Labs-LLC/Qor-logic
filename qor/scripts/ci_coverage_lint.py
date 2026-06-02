"""Pre-audit lint: reconcile plan ci_commands against .github/workflows (Phase 89).

Walks the repo's GitHub Actions workflows; extracts the plan-verifiable
Python-fingerprint commands (``python ...`` / ``pytest ...``) from each
job's ``run:`` steps; verifies each appears as a substring of some bullet
in the plan's ``## CI Commands`` section, or matches a substring pattern
in an optional ``## CI Coverage Exemptions`` block.

Closes the GH #91 credibility gap: phases sealed "all CI green" while a
real CI job (one the operator simply forgot to list in the plan's
``ci_commands``) would fail. Per
``qor/references/doctrine-shadow-genome-countermeasures.md``
SG-CICoverageDrift-A.

WARN-only (parallels ``plan_grep_lint`` / ``plan_text_consistency_lint`` /
``delivery_branch_lint``); exit code is always 0.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class LintWarning:
    workflow: str
    job: str
    step_name: str | None
    command: str
    reason: str


# Env-setup / plumbing prefixes that are not plan-verifiable checks.
_ENV_SETUP_PREFIXES: tuple[str, ...] = (
    "pip install",
    "pip uninstall",
    "git fetch",
    "git merge-base",
    "git diff",
    "git rev-parse",
    "git checkout",
    "echo ",
    "echo\"",
    "echo'",
    "printf ",
    "cd ",
    "mkdir ",
    "rm ",
    "mv ",
    "cp ",
    "cat ",
    "ls ",
    ":",
)

# Workflow-conditional bash patterns (BASE_BRANCH=, [[ ]], if/fi/then/else,
# >> $GITHUB_OUTPUT, exit N) that are control-flow scaffolding, not checks.
_DOC_ONLY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*[A-Z_][A-Z0-9_]*\s*="),   # ENV_VAR=...
    re.compile(r"^\s*\[\["),
    re.compile(r"^\s*if\b"),
    re.compile(r"^\s*fi\b"),
    re.compile(r"^\s*then\b"),
    re.compile(r"^\s*else\b"),
    re.compile(r"^\s*elif\b"),
    re.compile(r"^\s*>>"),
    re.compile(r"^\s*exit\s+\d"),
    re.compile(r"^\s*#"),
)

# V1 Python-fingerprint: a line that begins (after whitespace) with `python`
# or `pytest` and a following token.
_PYTHON_CANDIDATE_RE = re.compile(r"^\s*(python\b|pytest\b)")

# Trailing-guard suffixes that should be stripped before substring matching.
_TRAILING_GUARD_RE = re.compile(
    r"\s*(?:\|\|\s*(?:true|ABORT|\{[^}]*\}|exit\s+\d+).*|&&.*|\\\s*$)"
)

# Pytest verbosity / quiet flags that do not change which checks run.
# Stripped from BOTH the discovered command and plan bullets before the
# substring match so a workflow `pytest tests/ -v` matches a plan
# `pytest tests/ -q` (and vice-versa). Marker / path arguments are NOT
# in this set -- they change the test subset and must match.
_NEUTRAL_PYTEST_FLAGS_RE = re.compile(
    r"\s+(?:-q{1,2}|-v{1,3}|--quiet|--verbose|--no-header|--no-summary)\b"
)


def _strip_trailing_guard(line: str) -> str:
    """Remove ``|| true`` / ``|| ABORT`` / ``&& ...`` / trailing ``\\`` from line."""
    cleaned = _TRAILING_GUARD_RE.sub("", line)
    return cleaned.strip()


def _is_candidate(line: str) -> bool:
    """Decide whether a normalized line is a plan-verifiable CI command."""
    stripped = line.strip()
    if not stripped:
        return False
    if any(stripped.startswith(p) for p in _ENV_SETUP_PREFIXES):
        return False
    if any(p.match(stripped) for p in _DOC_ONLY_PATTERNS):
        return False
    if _PYTHON_CANDIDATE_RE.match(stripped):
        return True
    return False


def _is_tag_only_workflow(on_value: object) -> bool:
    """True iff the workflow's ``on:`` triggers only on tag pushes.

    Accepts ``push`` configurations that also carry path filters
    (``paths-ignore`` / ``paths``); the discriminating fact is the
    presence of ``tags`` and the absence of ``branches``. ``workflow_dispatch``
    (a manual trigger on a release-class workflow, e.g. to publish a historical
    tag) is tolerated and does not reclassify the workflow as a CI gate whose
    commands must appear in feature plans.
    """
    if not isinstance(on_value, dict):
        return False
    if set(on_value.keys()) - {"push", "release", "workflow_dispatch"}:
        return False
    push = on_value.get("push")
    if push is None:
        return bool(on_value.get("release") or on_value.get("workflow_dispatch"))
    if not isinstance(push, dict):
        return False
    if "tags" not in push:
        return False
    if "branches" in push:
        return False
    return True


def discover_ci_commands(
    workflows_dir: Path,
) -> list[tuple[str, str, str | None, str]]:
    """Yield (workflow_name, job_name, step_name, normalized_command) tuples
    for every plan-verifiable Python-fingerprint ``run:`` command in
    ``workflows_dir/*.yml``. Skips tag-only workflows; filters env-setup +
    doc-only bash.
    """
    results: list[tuple[str, str, str | None, str]] = []
    if not workflows_dir.is_dir():
        return results
    for wf_path in sorted(workflows_dir.glob("*.yml")):
        try:
            doc = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        if not isinstance(doc, dict):
            continue
        on_value = doc.get("on")
        # PyYAML maps the unquoted YAML key `on:` to the boolean True (it
        # parses as the YAML 1.1 alias for true). Fall back to the True key
        # when the literal "on" key is absent.
        if on_value is None and True in doc:
            on_value = doc[True]
        if _is_tag_only_workflow(on_value):
            continue
        jobs = doc.get("jobs") or {}
        if not isinstance(jobs, dict):
            continue
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps", []) or []:
                if not isinstance(step, dict):
                    continue
                run = step.get("run")
                if not isinstance(run, str):
                    continue
                step_name = step.get("name") if isinstance(step.get("name"), str) else None
                for raw_line in run.splitlines():
                    line = _strip_trailing_guard(raw_line)
                    if not _is_candidate(line):
                        continue
                    # Collapse whitespace for canonical match form.
                    normalized = " ".join(line.split())
                    results.append((wf_path.name, str(job_name), step_name, normalized))
    return results


def _extract_section_bullets(text: str, header: str) -> list[str]:
    """Return bullet text from a ``## <header>`` section as a list of strings.

    Each bullet's contents are returned verbatim (the leading marker is
    stripped). Section ends at the next ``## `` header or end-of-file.
    """
    pattern = re.compile(rf"^##\s+{re.escape(header)}\s*$", re.MULTILINE)
    m = pattern.search(text)
    if not m:
        return []
    start = m.end()
    next_header = re.search(r"^##\s+\S", text[start:], re.MULTILINE)
    end = start + (next_header.start() if next_header else len(text) - start)
    section = text[start:end]
    bullets: list[str] = []
    for line in section.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("- ", "* ")):
            bullets.append(stripped[2:].strip())
    return bullets


def _bullet_match_text(bullet: str) -> str:
    """Extract the substring usable for matching from a plan bullet.

    If the bullet contains a backtick-quoted command (``- `python -m X` --
    rationale``), return the contents of the first backtick pair; else
    return the whole bullet text. Whitespace collapsed.
    """
    bt = re.search(r"`([^`]+)`", bullet)
    text = bt.group(1) if bt else bullet
    return " ".join(text.split())


def _strip_neutral_pytest_flags(command: str) -> str:
    """Remove pytest verbosity/quiet flags that do not change check identity."""
    return _NEUTRAL_PYTEST_FLAGS_RE.sub("", command).strip()


def check_plan(plan_path: Path, workflows_dir: Path) -> list[LintWarning]:
    """Compare discovered CI commands against the plan's ``## CI Commands``
    bullets; honor ``## CI Coverage Exemptions`` substring patterns; emit
    a WARN per unmatched, non-exempt command.
    """
    if not plan_path.is_file():
        return []
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    ci_bullets = [
        _strip_neutral_pytest_flags(_bullet_match_text(b))
        for b in _extract_section_bullets(text, "CI Commands")
    ]
    exemption_patterns = [
        _bullet_match_text(b) for b in _extract_section_bullets(text, "CI Coverage Exemptions")
    ]
    discovered = discover_ci_commands(workflows_dir)
    warnings: list[LintWarning] = []
    for workflow, job, step_name, command in discovered:
        match_form = _strip_neutral_pytest_flags(command)
        if any(match_form in plan_bullet for plan_bullet in ci_bullets):
            continue
        if any(pattern and pattern in command for pattern in exemption_patterns):
            continue
        warnings.append(LintWarning(
            workflow=workflow,
            job=job,
            step_name=step_name,
            command=command,
            reason="CI command not covered by plan ## CI Commands and no matching ## CI Coverage Exemptions pattern",
        ))
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.ci_coverage_lint")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--workflows-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    warnings = check_plan(args.plan, args.workflows_dir)
    if not warnings:
        return 0
    print(
        f"ci_coverage_lint: {len(warnings)} workflow command(s) not covered by plan",
    )
    for w in warnings:
        suffix = f" (step: {w.step_name})" if w.step_name else ""
        print(f"  WARN {w.workflow}::{w.job}{suffix}")
        print(f"    command: {w.command}")
        print(f"    reason:  {w.reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
