from __future__ import annotations

import argparse
import json
from pathlib import Path

from qor.scripts import roadmap_state, roadmap_store, roadmap_view


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _repo_artifact(repo_root: str | Path, artifact: str) -> Path:
    root = Path(repo_root).resolve()
    path = Path(artifact)
    path = (path if path.is_absolute() else root / path).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise roadmap_state.InvalidHistoryError(
            f"artifact pointer escapes repository root: {artifact}"
        ) from exc
    return path


def _verified_predecessor(repo_root: str | Path, phase: str, artifact: str) -> str:
    root = Path(repo_root).resolve()
    path = _repo_artifact(root, artifact)
    if not path.is_file():
        raise roadmap_state.InvalidHistoryError(
            f"required {phase} predecessor artifact not found: {artifact}"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise roadmap_state.InvalidHistoryError(
            f"required predecessor artifact is unreadable or malformed: {artifact}"
        ) from exc
    if payload.get("phase") != phase:
        raise roadmap_state.InvalidHistoryError(
            f"predecessor phase mismatch: expected {phase!r}, got {payload.get('phase')!r}"
        )
    return str(path.relative_to(root))


def _roadmap_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--roadmap", required=True)


def _register_init(sub) -> None:
    cmd = sub.add_parser("init")
    _roadmap_arg(cmd)
    cmd.add_argument("--objective", required=True)
    cmd.add_argument("--success", action="append", default=[])
    cmd.add_argument("--exclude", action="append", default=[])


def _register_nodes(sub) -> None:
    cmd = sub.add_parser("add-node")
    _roadmap_arg(cmd)
    cmd.add_argument("--id", required=True)
    cmd.add_argument("--kind", choices=["fact", "decision", "prerequisite"], required=True)
    cmd.add_argument("--title", required=True)
    cmd.add_argument("--resolver", required=True)
    cmd.add_argument("--authority-required")

    cmd = sub.add_parser("add-dependency")
    _roadmap_arg(cmd)
    cmd.add_argument("--predecessor", required=True)
    cmd.add_argument("--dependent", required=True)

    cmd = sub.add_parser("resolve")
    _roadmap_arg(cmd)
    cmd.add_argument("--node", required=True)
    cmd.add_argument("--evidence", action="append", default=[])
    cmd.add_argument("--rationale", default="")
    cmd.add_argument("--authority")


def _register_lifecycle(sub) -> None:
    cmd = sub.add_parser("add-space")
    _roadmap_arg(cmd)
    cmd.add_argument("--id", required=True)
    cmd.add_argument("--title", required=True)

    cmd = sub.add_parser("retire-space")
    _roadmap_arg(cmd)
    cmd.add_argument("--id", required=True)
    cmd.add_argument("--reason", required=True)


def _register_scope_and_reads(sub) -> None:
    cmd = sub.add_parser("add-scope")
    _roadmap_arg(cmd)
    cmd.add_argument("--id", required=True)
    cmd.add_argument("--title", required=True)
    cmd.add_argument("--node", action="append", required=True)
    cmd.add_argument("--space", action="append", default=[])

    for name in ("show", "frontier"):
        cmd = sub.add_parser(name)
        _roadmap_arg(cmd)
        if name == "frontier":
            cmd.add_argument("--authority", action="append", default=[])

    cmd = sub.add_parser("handoff")
    _roadmap_arg(cmd)
    cmd.add_argument("--scope", required=True)
    cmd.add_argument("--predecessor-phase", choices=["ideation", "research"], required=True)
    cmd.add_argument("--predecessor-artifact", required=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qor-logic scripts roadmap_cli",
        description="Experimental Qor Roadmap decision-topology pilot.",
    )
    parser.add_argument("--repo-root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    _register_init(sub)
    _register_nodes(sub)
    _register_lifecycle(sub)
    _register_scope_and_reads(sub)
    return parser


def _append(args: argparse.Namespace, event_type: str, payload: dict) -> int:
    event = roadmap_store.append_payload(
        Path(args.repo_root), args.roadmap, event_type=event_type, payload=payload
    )
    _print(event)
    return 0


def _write_init(args: argparse.Namespace) -> int:
    event = roadmap_store.create_roadmap(
        args.repo_root,
        args.roadmap,
        title=args.objective,
        success_conditions=args.success,
        exclusions=args.exclude,
    )
    _print(event)
    return 0


def _write_node(args: argparse.Namespace) -> int:
    return _append(args, "node_added", {"node": {
        "id": args.id, "kind": args.kind, "title": args.title,
        "resolver": args.resolver, "authority_required": args.authority_required,
    }})


def _write_dependency(args: argparse.Namespace) -> int:
    return _append(args, "dependency_added", {
        "predecessor_id": args.predecessor, "dependent_id": args.dependent,
    })


def _write_resolution(args: argparse.Namespace) -> int:
    return _append(args, "node_resolved", {
        "node_id": args.node, "evidence_pointers": args.evidence,
        "rationale": args.rationale, "authority": args.authority,
    })


def _write_space(args: argparse.Namespace) -> int:
    return _append(args, "unresolved_space_added", {
        "space": {"id": args.id, "title": args.title}
    })


def _write_retirement(args: argparse.Namespace) -> int:
    return _append(args, "unresolved_space_retired", {
        "space_id": args.id, "reason": args.reason,
    })


def _write_scope(args: argparse.Namespace) -> int:
    return _append(args, "planning_scope_added", {"scope": {
        "id": args.id, "title": args.title, "node_ids": args.node,
        "unresolved_space_ids": args.space,
    }})


_WRITE_DISPATCH = {
    "init": _write_init,
    "add-node": _write_node,
    "add-dependency": _write_dependency,
    "resolve": _write_resolution,
    "add-space": _write_space,
    "retire-space": _write_retirement,
    "add-scope": _write_scope,
}


def _handle_read(args: argparse.Namespace) -> int:
    state = roadmap_store.load_state(args.repo_root, args.roadmap)
    if args.command == "show":
        _print(state.to_dict())
        return 0
    if args.command == "frontier":
        _print(roadmap_view.frontier_report(
            state, available_authorities=args.authority
        ))
        return 0
    predecessor = _verified_predecessor(
        args.repo_root, args.predecessor_phase, args.predecessor_artifact
    )
    _print(roadmap_view.build_plan_handoff(
        state,
        scope_id=args.scope,
        predecessor_phase=args.predecessor_phase,
        predecessor_artifact=predecessor,
    ))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        handler = _WRITE_DISPATCH.get(args.command)
        return handler(args) if handler else _handle_read(args)
    except roadmap_state.RoadmapError as exc:
        print(f"roadmap error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
