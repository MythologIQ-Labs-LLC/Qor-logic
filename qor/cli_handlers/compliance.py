"""compliance subcommand handlers (Phase 54).

Hosts ``do_report`` (extracted from ``qor.cli`` pre-Phase-54), plus the new
``do_ai_provenance`` and ``do_sprint_progress`` handlers. Single
``register(sub)`` adds the parser group for all three.

Closes Pass-1 razor-overage finding by extracting handler bodies out of
``qor/cli.py`` into this module.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _compute_coverage(practice_map: dict[int, list[str]]) -> tuple[int, int, int]:
    all_practices: set[str] = set()
    total = 0
    for practices in practice_map.values():
        for p in practices:
            all_practices.add(p)
            total += 1
    groups = {p.split(".")[0] for p in all_practices}
    return len(groups), len(all_practices), total


def do_report(ledger_path: Path | None = None) -> str:
    """Generate SSDF practice coverage report from ledger."""
    from qor.scripts.ledger_hash import extract_ssdf_practices
    if ledger_path is None:
        from qor import workdir
        ledger_path = workdir.meta_ledger()
    practice_map = extract_ssdf_practices(ledger_path)
    if not practice_map:
        return "No SSDF practice tags found in ledger. Coverage: 0"

    by_practice: dict[str, list[int]] = {}
    for entry_num, practices in practice_map.items():
        for p in practices:
            by_practice.setdefault(p, []).append(entry_num)

    lines = ["SSDF Practice Coverage:"]
    for practice in sorted(by_practice):
        entries = by_practice[practice]
        entry_refs = ", ".join(f"Entry #{n}" for n in sorted(entries))
        lines.append(f"  {practice}: {len(entries)} entries ({entry_refs})")

    groups, unique, total = _compute_coverage(practice_map)
    lines.append(f"Coverage: {groups} practice groups, {unique} individual practices, {total} total tags")
    return "\n".join(lines)


def do_ai_provenance(args: argparse.Namespace) -> int:
    """Aggregate AI provenance manifests across a session's gate artifacts."""
    from qor import workdir
    session_id = args.session
    gates_dir = workdir.gate_dir() / session_id
    if not gates_dir.exists():
        print(f"ERROR: no gate artifacts for session {session_id!r}", file=sys.stderr)
        return 1

    manifest = {"session_id": session_id, "phases": {}}
    phases = ("research", "plan", "audit", "implement", "substantiate", "validate")
    for phase in phases:
        artifact_path = gates_dir / f"{phase}.json"
        if not artifact_path.exists():
            continue
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
        manifest["phases"][phase] = data.get("ai_provenance")  # may be None

    print(json.dumps(manifest, indent=2))
    return 0


def do_sprint_progress(args: argparse.Namespace) -> int:
    """Show sprint progress derived from latest research brief + ledger."""
    from qor.scripts.sprint_progress import render_progress
    repo_root = getattr(args, "repo_root", None) or Path.cwd()
    print(render_progress(repo_root))
    return 0


def register(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Register the compliance subcommand group with the parser."""
    sp_compliance = sub.add_parser("compliance", help="NIST SSDF + AI Act compliance reporting")
    compliance_sub = sp_compliance.add_subparsers(dest="compliance_command", metavar="<subcommand>")

    sp_report = compliance_sub.add_parser("report", help="show SSDF practice coverage")
    sp_report.add_argument("--ledger", type=Path, default=None)

    sp_provenance = compliance_sub.add_parser("ai-provenance", help="aggregate AI provenance manifests for a session")
    sp_provenance.add_argument("--session", required=True, help="session id (.qor/gates/<session>/)")

    sp_progress = compliance_sub.add_parser("sprint-progress", help="show compliance-sprint progress against latest research brief")
    sp_progress.add_argument("--repo-root", type=Path, default=None)

    return sp_compliance


def dispatch(args: argparse.Namespace) -> int | None:
    """Route compliance subcommand args to the right handler."""
    cmd = getattr(args, "compliance_command", None)
    if cmd == "report":
        print(do_report(ledger_path=getattr(args, "ledger", None)))
        return 0
    if cmd == "ai-provenance":
        return do_ai_provenance(args)
    if cmd == "sprint-progress":
        return do_sprint_progress(args)
    return None
