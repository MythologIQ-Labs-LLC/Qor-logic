#!/usr/bin/env python3
"""Compliance ratchet (Phase 141).

Compares the current control matrix against the matrix at a prior release ref. A
*regression* is a control that was dropped, or whose posture was downgraded
(ABORT -> WARN), relative to the prior release -- unless an explicit waiver
(id + justification + issue) covers it. Growth (new controls) is always allowed.

This makes the compliance Qor-logic conveys downstream monotonic: hold-or-
strengthen across versions. See ``qor/references/doctrine-compliance-conveyance.md``.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from qor.scripts.compliance_matrix import (
    Control,
    Waiver,
    load_matrix,
    load_waivers,
)

_MATRIX_REL = "qor/compliance/control_matrix.json"


def prior_matrix(root: Path, ref: str) -> tuple[Control, ...] | None:
    """Controls in the matrix at ``ref`` via ``git show``; None when the matrix
    file does not exist at that ref (first introduction -- nothing to ratchet)."""
    try:
        out = subprocess.run(
            ["git", "show", f"{ref}:{_MATRIX_REL}"],
            cwd=root, check=True, capture_output=True, text=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    data = json.loads(out)
    return tuple(
        Control(
            id=c["id"], framework=c.get("framework", ""), control=c.get("control", ""),
            enforcing_module=c.get("enforcing_module", ""), posture=c["posture"],
            detection=c.get("detection", ""), wired_into=c.get("wired_into", {}),
            variants=tuple(c.get("variants", ())), invocation=c.get("invocation", ""),
        )
        for c in data.get("controls", [])
    )


def regressions(
    current: tuple[Control, ...],
    prior: tuple[Control, ...],
    waivers: tuple[Waiver, ...],
) -> list[str]:
    """Regression strings for dropped/downgraded controls not covered by a waiver."""
    waived = {w.id for w in waivers}
    current_posture = {c.id: c.posture for c in current}
    out: list[str] = []
    for pc in prior:
        if pc.id in waived:
            continue
        if pc.id not in current_posture:
            out.append(f"control {pc.id!r} was dropped (present in prior release, absent now)")
        elif pc.posture == "ABORT" and current_posture[pc.id] == "WARN":
            out.append(f"control {pc.id!r} downgraded ABORT -> WARN")
    return out


def ratchet_check(root: Path, ref: str) -> list[str]:
    """Ratchet the current matrix against ``ref``; empty on first introduction."""
    prior = prior_matrix(root, ref)
    if prior is None:
        return []
    return regressions(load_matrix(root), prior, load_waivers(root))


def _default_base(root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "tag", "-l", "v*"],
            cwd=root, check=True, capture_output=True, text=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    import re
    tags = [t.strip() for t in out.splitlines() if re.match(r"^v\d+\.\d+\.\d+$", t.strip())]
    if not tags:
        return None
    return max(tags, key=lambda t: tuple(int(n) for n in t[1:].split(".")))


def main() -> int:
    ap = argparse.ArgumentParser(description="Compliance ratchet vs a prior release ref")
    ap.add_argument("--base", default=None, help="prior release ref (default: highest v* tag)")
    args = ap.parse_args()
    root = Path(".").resolve()
    ref = args.base or _default_base(root)
    if ref is None:
        print("compliance ratchet: no prior release ref; nothing to ratchet")
        return 0
    regs = ratchet_check(root, ref)
    if not regs:
        print(f"compliance ratchet: OK (no regression vs {ref})")
        return 0
    for r in regs:
        print(f"REGRESSION vs {ref}: {r}")
    print("Add a waiver (id+justification+issue) to control_matrix.json to accept a deliberate change.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
