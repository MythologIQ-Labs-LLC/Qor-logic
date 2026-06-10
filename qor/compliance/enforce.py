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
    status: str  # "pass" | "fail" | "skip" | "disclosed"
    reason: str | None = None

    @property
    def passed(self) -> bool:
        return self.status != "fail"


@dataclass(frozen=True)
class Verdict:
    engagement: str
    status: str  # "enforced" (>=1 ran) | "failed" (an ABORT failed) | "no_op" (nothing ran)
    results: tuple[ControlResult, ...]

    @property
    def passed(self) -> bool:
        return self.status != "failed"


@contextlib.contextmanager
def _chdir(path: Path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def run_control(control: Control, root: Path) -> ControlResult:
    """Run the control's runner against ``root``. A control whose runner declares
    ``requires`` paths absent under ``root`` is a disclosed-skip (Phase 75 style):
    it reports ``skip`` without importing or invoking the runner, so a consumer
    lacking a governance artifact is not hard-failed."""
    runner = control.runner or {}
    for rel in runner.get("requires", []):
        if not (Path(root) / rel).exists():
            return ControlResult(control.id, control.posture, 0, "skip")
    module = importlib.import_module(runner["module"])
    entry = getattr(module, runner["entry"])
    with _chdir(root):
        code = int(entry(list(runner.get("args", []))))
    return ControlResult(control.id, control.posture, code, "pass" if code == 0 else "fail")


def select(controls: tuple[Control, ...], engagement: str) -> list[Control]:
    """Controls wired to ``engagement`` that carry a runner (runnable here)."""
    return [c for c in controls if engagement in c.engagement and c.runner]


def _disclosed(controls: tuple[Control, ...], engagement: str) -> list[Control]:
    """Engagement-matched controls that intentionally carry no runner but a
    documented reason -- surfaced so a no-op is never silent."""
    return [
        c for c in controls
        if engagement in c.engagement and c.runner is None and c.runner_unavailable_reason
    ]


def enforce(
    engagement: str, root: Path, controls: tuple[Control, ...] | None = None
) -> Verdict:
    """Run every runnable control for ``engagement`` and surface disclosed ones.
    ABORT failures fail the verdict; WARN failures are advisory. The verdict
    status is explicit so a consumer never mistakes a no-op for enforcement."""
    source = controls if controls is not None else load_packaged_matrix()
    root = Path(root)
    ran = [run_control(c, root) for c in select(source, engagement)]
    disclosed = [
        ControlResult(c.id, c.posture, 0, "disclosed", c.runner_unavailable_reason)
        for c in _disclosed(source, engagement)
    ]
    results = tuple(ran + disclosed)
    if any(r.status == "fail" and r.posture == "ABORT" for r in results):
        status = "failed"
    elif any(r.status in ("pass", "fail") for r in results):
        status = "enforced"
    else:
        status = "no_op"
    return Verdict(engagement, status, results)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="qor-logic compliance enforce")
    ap.add_argument("--engagement", required=True, choices=ENGAGEMENTS)
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args(argv)
    verdict = enforce(args.engagement, Path(args.repo_root).resolve())
    for r in verdict.results:
        if r.status == "disclosed":
            print(f"DISCLOSED {r.id} ({r.posture}): {r.reason}")
        else:
            print(f"{r.status.upper()} {r.id} ({r.posture}) exit={r.exit_code}")
    if verdict.status == "no_op":
        print(f"NOT ENFORCED: no control ran for engagement {args.engagement!r}")
    print(f"engagement {args.engagement}: {verdict.status}")
    return 1 if verdict.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
