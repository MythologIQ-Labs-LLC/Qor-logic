"""Lint a plan's execution-continuity declaration (Phase 216; GH #285).

Follows the established ``plan_*_lint`` shape: argv-only input, one finding code
per defect class, non-zero exit when any finding is present.

The lint checks that the declaration is well-formed *and* that it stays within
Qor-owned vocabulary. It deliberately does not validate against the upstream
contract schema -- Qor-logic does not hold it, and copying it here would create
the second semantic authority GH #285 exists to prevent.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qor.scripts.continuity_contract import (
    QOR_OWNED_KEYS,
    REVISION_KEYS,
    Finding,
)


def _check_contract_version(declaration: dict) -> list[Finding]:
    version = declaration.get("contract_version")
    if isinstance(version, str) and version:
        return []
    return [Finding(
        "missing-contract-version",
        "declaration must reference the upstream contract by version",
    )]


def _check_unknown_keys(declaration: dict) -> list[Finding]:
    unknown = sorted(set(declaration) - QOR_OWNED_KEYS)
    return [
        Finding("unknown-key", f"{key!r} is not Qor-owned vocabulary")
        for key in unknown
    ]


def _check_revisions(declaration: dict) -> list[Finding]:
    findings = []
    for key in REVISION_KEYS:
        if key in declaration and not isinstance(declaration[key], str):
            findings.append(Finding(
                "non-string-revision", f"{key} must be a revision string"))
    return findings


def _check_successor_actors(declaration: dict) -> list[Finding]:
    actors = declaration.get("successor_actor_classes")
    if actors is None or (isinstance(actors, list) and actors):
        return []
    return [Finding(
        "empty-successor-actors",
        "declaring continuity with no permitted successor authorizes nobody",
    )]


def _check_no_nested_objects(declaration: dict) -> list[Finding]:
    """A declaration that admits no nested structure cannot hide a copied schema."""
    return [
        Finding("nested-object", f"{key} holds a nested object")
        for key, value in sorted(declaration.items())
        if isinstance(value, dict)
    ]


_CHECKS = (
    _check_contract_version,
    _check_unknown_keys,
    _check_revisions,
    _check_successor_actors,
    _check_no_nested_objects,
)


def lint(declaration: dict) -> list[Finding]:
    """Return every finding for one declaration; empty means clean."""
    findings: list[Finding] = []
    for check in _CHECKS:
        findings.extend(check(declaration))
    return findings


def _load_declaration(artifact_path: Path) -> dict | None:
    try:
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    block = data.get("execution_continuity")
    return block if isinstance(block, dict) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="plan_continuity_lint")
    parser.add_argument("--artifact", required=True,
                        help="path to a plan gate artifact (JSON)")
    args = parser.parse_args(argv)

    declaration = _load_declaration(Path(args.artifact))
    if declaration is None:
        print("SKIP: no execution_continuity declaration")
        return 0

    findings = lint(declaration)
    for finding in findings:
        print(f"[{finding.code}] {finding.detail}", file=sys.stderr)
    print(f"plan_continuity_lint: {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
