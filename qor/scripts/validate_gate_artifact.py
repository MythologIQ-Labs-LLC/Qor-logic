#!/usr/bin/env python3
"""Validate gate artifacts against their phase schemas.

Usage:
  python validate_gate_artifact.py <phase> <artifact.json>   # single
  python validate_gate_artifact.py --all                      # all in current session
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema
import referencing

from qor.scripts import session

from qor import resources as _resources
from qor import workdir as _workdir

SCHEMA_DIR = Path(str(_resources.asset("gates", "schema")))
GATES_DIR = _workdir.gate_dir()


def _build_registry() -> referencing.Registry:
    """Register every local schema file by both filename and $id (Phase 54).

    Allows phase schemas to use ``"$ref": "_provenance.schema.json"`` without
    triggering a network fetch when the validator encounters the reference.
    """
    registry: referencing.Registry = referencing.Registry()
    for schema_path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        resource = referencing.Resource.from_contents(schema)
        registry = registry.with_resource(uri=schema_path.name, resource=resource)
        schema_id = schema.get("$id")
        if schema_id:
            registry = registry.with_resource(uri=schema_id, resource=resource)
    return registry


_REGISTRY: referencing.Registry | None = None


def _registry() -> referencing.Registry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry()
    return _REGISTRY

PHASES = [
    "research",
    "plan",
    "audit",
    "implement",
    "substantiate",
    "validate",
    "remediate",
]


def load_schema(phase: str) -> dict:
    path = SCHEMA_DIR / f"{phase}.schema.json"
    if not path.exists():
        raise SystemExit(f"ERROR: schema not found for phase '{phase}': {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_one(phase: str, artifact_path: Path) -> list[str]:
    if not artifact_path.exists():
        return [f"artifact not found: {artifact_path}"]
    try:
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]
    schema = load_schema(phase)
    errors: list[str] = []
    validator = jsonschema.Draft202012Validator(schema, registry=_registry())
    for err in validator.iter_errors(data):
        path_str = ".".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{path_str}: {err.message}")
    return errors


def validate_all_current_session() -> tuple[int, int, list[str]]:
    """Walk .qor/gates/<session_id>/ for current session; validate each phase.json.

    Returns (checked_count, error_count, report_lines).
    """
    sid = session.current()
    report: list[str] = []
    if not sid:
        report.append("No active session; nothing to validate.")
        return 0, 0, report
    session_dir = GATES_DIR / sid
    if not session_dir.exists():
        report.append(f"No gate artifacts for session {sid}")
        return 0, 0, report

    checked = 0
    errors = 0
    for phase in PHASES:
        artifact = session_dir / f"{phase}.json"
        if not artifact.exists():
            continue
        checked += 1
        errs = validate_one(phase, artifact)
        if errs:
            errors += 1
            report.append(f"FAIL {phase}: {artifact}")
            for e in errs:
                report.append(f"  {e}")
        else:
            report.append(f"OK   {phase}: {artifact}")
    return checked, errors, report


def write_artifact(phase: str, data: dict, session_id: str | None = None) -> Path:
    """Helper used by skills: write artifact to .qor/gates/<session>/<phase>.json
    after validating. Returns written path."""
    sid = session_id or session.get_or_create()
    data = {"phase": phase, "session_id": sid, **data}
    errs = _validate_data(phase, data)
    if errs:
        raise ValueError(f"Cannot write invalid {phase} artifact: {errs}")
    out = GATES_DIR / sid / f"{phase}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    import os, tempfile
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=out.parent, delete=False, suffix=".tmp"
    ) as tf:
        json.dump(data, tf, indent=2)
        tmp = tf.name
    os.replace(tmp, out)
    return out


def _validate_data(phase: str, data: dict) -> list[str]:
    schema = load_schema(phase)
    errors: list[str] = []
    validator = jsonschema.Draft202012Validator(schema, registry=_registry())
    for err in validator.iter_errors(data):
        path_str = ".".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{path_str}: {err.message}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("phase", nargs="?", choices=PHASES)
    ap.add_argument("artifact", nargs="?", type=Path)
    ap.add_argument("--all", action="store_true", help="Validate every artifact in current session")
    args = ap.parse_args()

    if args.all:
        checked, errors, report = validate_all_current_session()
        for line in report:
            print(line)
        print(f"\n{checked} checked, {errors} failed")
        return 1 if errors else 0

    if not args.phase or not args.artifact:
        ap.error("phase and artifact required (or use --all)")
    errs = validate_one(args.phase, args.artifact)
    if errs:
        print(f"FAIL {args.phase}: {args.artifact}")
        for e in errs:
            print(f"  {e}")
        return 1
    print(f"OK   {args.phase}: {args.artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
