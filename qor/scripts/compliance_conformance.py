#!/usr/bin/env python3
"""Conveyance conformance verifier (Phase 141).

For each control in the compliance matrix, verify reality matches the declared
posture and that the control reaches the conveyed payload. Dispatches on the
control's ``detection`` mode (skill-marker / test / ci-job). Pure + importable;
``main`` exits 1 listing every failing cell.

See ``qor/references/doctrine-compliance-conveyance.md``.
"""
from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

from qor.scripts.compliance_matrix import RUNNABLE_POINTS, Control, load_matrix

_HEADING_RE = re.compile(r"^#{2,6}\s", re.MULTILINE)
_HARD_MARKERS = ("ABORT", "VETO", "exit 1")


def _heading_matches(line: str, step: str) -> bool:
    """A numbered step (`4.6.5`) anchors on `Step <n>` followed by `:`/space so
    `6.5` does not false-match `Step 4.6.5`; a named pass matches its title."""
    if any(ch.isdigit() for ch in step):
        return re.search(rf"Step {re.escape(step)}(?=[:\s])", line) is not None
    return step in line


def _step_section(text: str, step: str) -> str:
    """Return the body of the heading whose line anchors ``step``, up to the
    next real heading. Headings inside ``` code fences (example markdown in the
    skill) are ignored so the section is not cut short. Empty when not found."""
    lines = text.splitlines(keepends=True)
    start = None
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence and _HEADING_RE.match(line) and _heading_matches(line, step):
            start = i
            break
    if start is None:
        return ""
    out = [lines[start]]
    in_fence = False
    for line in lines[start + 1:]:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence and _HEADING_RE.match(line):
            break
        out.append(line)
    return "".join(out)


def _variant_skill_path(skill_rel: str, variant: str) -> str:
    """Per-variant conveyed-payload location. claude/codex/kilo-code compile
    skills to ``skills/<name>/SKILL.md``; gemini compiles to a flat
    ``commands/<name>.toml`` command file."""
    name = Path(skill_rel).parent.name
    if variant == "gemini":
        return f"qor/dist/variants/gemini/commands/{name}.toml"
    return f"qor/dist/variants/{variant}/skills/{name}/SKILL.md"


def _verify_skill_marker(control: Control, root: Path) -> list[str]:
    reasons: list[str] = []
    skill_rel = control.wired_into.get("skill", "")
    step = control.wired_into.get("step", "")
    skill_path = root / skill_rel
    if not skill_path.is_file():
        return [f"source skill not found: {skill_rel}"]
    section = _step_section(skill_path.read_text(encoding="utf-8"), step)
    if control.invocation not in section:
        reasons.append(f"invocation {control.invocation!r} absent in source step {step!r}")
    else:
        has_warn = "|| true" in section
        has_hard = any(m in section for m in _HARD_MARKERS)
        if control.posture == "ABORT" and has_warn:
            reasons.append("declared ABORT but step carries '|| true' (downgrade)")
        if control.posture == "ABORT" and not has_hard:
            reasons.append("declared ABORT but step has no hard-fail marker (ABORT/VETO/exit 1)")
        if control.posture == "WARN" and not has_warn:
            reasons.append("declared WARN but step lacks '|| true'")
    for variant in control.variants:
        vp = root / _variant_skill_path(skill_rel, variant)
        if not vp.is_file():
            reasons.append(f"conveyed variant {variant} missing skill file")
        elif control.invocation not in vp.read_text(encoding="utf-8"):
            reasons.append(f"invocation absent in conveyed variant {variant}")
    return reasons


def _verify_test(control: Control, root: Path) -> list[str]:
    ref = control.wired_into.get("test", "")
    path, _, name = ref.partition("::")
    target = root / path
    if not target.is_file():
        return [f"detection=test references missing file: {path}"]
    if name and f"def {name}" not in target.read_text(encoding="utf-8"):
        return [f"detection=test references missing test function: {name}"]
    return []


def _verify_ci_job(control: Control, root: Path) -> list[str]:
    job = control.wired_into.get("job", "")
    target = root / job
    if not target.is_file():
        return [f"detection=ci-job references missing workflow: {job}"]
    short = control.enforcing_module.rsplit(".", 1)[-1]
    if short not in target.read_text(encoding="utf-8"):
        return [f"workflow {job} does not reference enforcing module {short}"]
    return []


_DISPATCH = {
    "skill-marker": _verify_skill_marker,
    "test": _verify_test,
    "ci-job": _verify_ci_job,
}


def _verify_runner(control: Control, root: Path) -> list[str]:
    """A control engaging a runnable point (pre-commit/pre-push/pre-tool-write)
    must carry a runner whose module is importable and entry is callable, so the
    SDK can actually run it (Phase 142)."""
    runner = control.runner
    requires_runner = bool(set(control.engagement) & set(RUNNABLE_POINTS))
    if runner is None:
        if requires_runner:
            return [f"engages a runnable point but has no runner: {sorted(control.engagement)}"]
        return []
    # Phase 148: any control that DOES carry a runner (incl. the wired ci/seal
    # controls) must be importable + callable, so a wired runner cannot rot.
    try:
        module = importlib.import_module(runner.get("module", ""))
    except Exception as exc:  # noqa: BLE001 - report any import failure
        return [f"runner module not importable: {runner.get('module')!r} ({exc})"]
    if not callable(getattr(module, runner.get("entry", ""), None)):
        return [f"runner entry not callable: {runner.get('module')}.{runner.get('entry')}"]
    return []


def verify_control(control: Control, root: Path) -> list[str]:
    """Return failure reasons for one control (empty == satisfied)."""
    handler = _DISPATCH.get(control.detection)
    reasons = (
        [f"unknown detection mode: {control.detection}"]
        if handler is None
        else list(handler(control, root))
    )
    return reasons + _verify_runner(control, root)


def verify_all(root: Path) -> dict[str, list[str]]:
    """Return ``{control_id: reasons}`` for every failing control."""
    failures: dict[str, list[str]] = {}
    for control in load_matrix(root):
        reasons = verify_control(control, root)
        if reasons:
            failures[control.id] = reasons
    return failures


def main() -> int:
    root = Path(".").resolve()
    failures = verify_all(root)
    if not failures:
        print("compliance conformance: OK (all controls satisfied)")
        return 0
    for cid, reasons in failures.items():
        for reason in reasons:
            print(f"FAIL {cid}: {reason}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
