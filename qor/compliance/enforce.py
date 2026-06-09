#!/usr/bin/env python3
"""Downstream enforcement SDK (Phase 142).

The mini-SDK a downstream consumer calls to run the compliance controls wired to
an enforcement engagement point (pre-commit / pre-push / pre-tool-write). Control
definitions come from the installed qor-logic package (the engagement manifest);
each control's runner runs against the consumer's working tree. Qor-logic owns
the manifest + uniform runner behavior + verdict shape; the consumer owns the
trigger (hook). See ``qor/references/downstream-enforcement-sdk.md``.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import os
from dataclasses import dataclass
from pathlib import Path

from qor.scripts.compliance_matrix import (
    Control,
    ENGAGEMENTS,
    load_packaged_matrix,
)


@dataclass(frozen=True)
class ControlResult:
    id: str
    posture: str
    exit_code: int
    passed: bool


@dataclass(frozen=True)
class Verdict:
    engagement: str
    passed: bool
    results: tuple[ControlResult, ...]


@contextlib.contextmanager
def _chdir(path: Path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def run_control(control: Control, root: Path) -> ControlResult:
    """Import the control's runner and invoke its entry against ``root``."""
    runner = control.runner or {}
    module = importlib.import_module(runner["module"])
    entry = getattr(module, runner["entry"])
    with _chdir(root):
        code = int(entry(list(runner.get("args", []))))
    return ControlResult(control.id, control.posture, code, code == 0)


def select(controls: tuple[Control, ...], engagement: str) -> list[Control]:
    """Controls wired to ``engagement`` that carry a runner (runnable here)."""
    return [c for c in controls if engagement in c.engagement and c.runner]


def enforce(
    engagement: str, root: Path, controls: tuple[Control, ...] | None = None
) -> Verdict:
    """Run every runnable control for ``engagement``; ABORT failures fail the
    verdict, WARN failures are advisory (posture-honoring)."""
    source = controls if controls is not None else load_packaged_matrix()
    results = tuple(run_control(c, Path(root)) for c in select(source, engagement))
    passed = all(r.passed for r in results if r.posture == "ABORT")
    return Verdict(engagement, passed, results)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="qor-logic compliance enforce")
    ap.add_argument("--engagement", required=True, choices=ENGAGEMENTS)
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args(argv)
    verdict = enforce(args.engagement, Path(args.repo_root).resolve())
    for r in verdict.results:
        print(f"{'OK' if r.passed else 'FAIL'} {r.id} ({r.posture}) exit={r.exit_code}")
    if not verdict.results:
        print(f"no runnable controls for engagement {args.engagement!r}")
    print(f"engagement {args.engagement}: {'PASS' if verdict.passed else 'FAIL'}")
    return 0 if verdict.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
