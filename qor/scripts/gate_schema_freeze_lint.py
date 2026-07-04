"""WARN-only lint: net-new ceremony-artifact schemas need registration or an
L3 justification (Phase 169; GH #251b).

Ceremony artifacts accrete cost forever (research entry #378). This lint
compares ``qor/gates/schema/*.schema.json`` against the deliberate registry
(``qor/gates/SCHEMA_REGISTRY.json``); an unregistered schema passes only when
the current session's plan declares it under ``new_ceremony_artifacts`` with
a justification. Exit 1 on findings (the audit Step 0.6 ladder wraps
``|| true``; a V2 phase removes the wrap).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def registered(registry_path: Path) -> set[str]:
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {str(name) for name in data.get("schemas", [])}


def present(schema_dir: Path) -> set[str]:
    if not schema_dir.is_dir():
        return set()
    return {p.name.removesuffix(".schema.json") for p in schema_dir.glob("*.schema.json")}


def declared_in_plan(plan_artifact: Path) -> set[str]:
    try:
        payload = json.loads(plan_artifact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    out: set[str] = set()
    for entry in payload.get("new_ceremony_artifacts") or []:
        name = str(entry.get("name", ""))
        if name and str(entry.get("justification", "")):
            out.add(name.removesuffix(".schema.json"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--session", default=None,
                    help="session id whose plan may declare new_ceremony_artifacts")
    args = ap.parse_args(argv)
    root = args.repo_root
    unregistered = present(root / "qor" / "gates" / "schema") - registered(
        root / "qor" / "gates" / "SCHEMA_REGISTRY.json")
    if unregistered and args.session:
        unregistered -= declared_in_plan(
            root / ".qor" / "gates" / args.session / "plan.json")
    for name in sorted(unregistered):
        print(f"WARN [schema-freeze] {name}.schema.json: net-new ceremony artifact "
              f"without registration or plan-declared L3 justification (GH #251)")
    print(f"gate_schema_freeze_lint: {len(unregistered)} unjustified new schema(s)")
    return 1 if unregistered else 0


if __name__ == "__main__":
    raise SystemExit(main())
