"""QorLogic CLI -- agent-agnostic skill distribution harness."""
from __future__ import annotations

import argparse
from pathlib import Path

from qor.install import (
    _do_install,
    _do_list,
    _do_uninstall,
)

__version__ = "0.15.0"


def _default_dist_root() -> Path:
    from qor import resources as _resources
    return Path(str(_resources.asset("dist")))


def _do_info(args: argparse.Namespace) -> int:
    """Show skill metadata from compiled variants."""
    import sys

    skill_name = args.skill
    dist_root = _default_dist_root()
    skill_md = dist_root / "variants" / "claude" / "skills" / skill_name / "SKILL.md"
    if not skill_md.exists():
        skill_md = dist_root / "variants" / "claude" / "skills" / f"{skill_name}.md"
    if not skill_md.exists():
        print(f"Skill {skill_name!r} not found", file=sys.stderr)
        return 1
    print(skill_md.read_text(encoding="utf-8")[:500])
    return 0


def _do_compile(args: argparse.Namespace) -> int:
    """Compile variants from source."""
    from qor.scripts import dist_compile
    summary = dist_compile.compile_all(
        dist_compile.DEFAULT_OUT, dry_run=getattr(args, "dry_run", False),
    )
    action = "Would emit" if getattr(args, "dry_run", False) else "Compiled"
    print(f"{action}: {summary['skill_dirs']} skill dirs, {summary['loose_skills']} loose, {summary['agents']} agents")
    return 0


def _compute_coverage(practice_map: dict[int, list[str]]) -> tuple[int, int, int]:
    """Compute (group_count, unique_practices, total_tags) from practice_map."""
    all_practices: set[str] = set()
    total = 0
    for practices in practice_map.values():
        for p in practices:
            all_practices.add(p)
            total += 1
    groups = {p.split(".")[0] for p in all_practices}
    return len(groups), len(all_practices), total


def _do_compliance_report(
    ledger_path: Path | None = None,
) -> str:
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


def _do_verify_ledger(args: argparse.Namespace) -> int:
    """Verify META_LEDGER.md chain."""
    from qor.scripts import ledger_hash
    from qor import workdir
    ledger_path = workdir.meta_ledger()
    return ledger_hash.verify(ledger_path)


_HOSTS_CHOICES = ["claude", "kilo-code", "codex", "gemini"]
_SCOPES_CHOICES = ["repo", "global"]
_PROFILE_CHOICES = ["sdlc", "filesystem", "data", "research"]


def _register_install_family(sub) -> None:
    sp_install = sub.add_parser("install", help="install skills into an AI coding host")
    sp_install.add_argument("--host", required=True, choices=_HOSTS_CHOICES)
    sp_install.add_argument("--scope", default="repo", choices=_SCOPES_CHOICES)
    sp_install.add_argument("--target", type=Path, default=None)
    sp_install.add_argument("--dry-run", action="store_true")

    sp_uninstall = sub.add_parser("uninstall", help="remove installed skills")
    sp_uninstall.add_argument("--host", default="claude", choices=_HOSTS_CHOICES)
    sp_uninstall.add_argument("--scope", default="repo", choices=_SCOPES_CHOICES)
    sp_uninstall.add_argument("--target", type=Path, default=None)

    sp_list = sub.add_parser("list", help="enumerate available or installed skills")
    sp_list.add_argument("--available", action="store_true")
    sp_list.add_argument("--installed", action="store_true")
    sp_list.add_argument("--host", default="claude")
    sp_list.add_argument("--scope", default="repo", choices=_SCOPES_CHOICES)

    sp_init = sub.add_parser("init", help="initialize .qorlogic/config.json")
    sp_init.add_argument("--host", default="claude", choices=_HOSTS_CHOICES)
    sp_init.add_argument("--scope", default="repo", choices=_SCOPES_CHOICES)
    sp_init.add_argument("--profile", default="sdlc", choices=_PROFILE_CHOICES)
    sp_init.add_argument("--target", type=Path, default=None)


def _register_misc(sub) -> None:
    sp_info = sub.add_parser("info", help="show skill metadata")
    sp_info.add_argument("skill", help="skill name")
    sp_compile = sub.add_parser("compile", help="regenerate variants from source")
    sp_compile.add_argument("--dry-run", action="store_true")
    sub.add_parser("verify-ledger", help="verify META_LEDGER.md chain")


def _register_compliance_policy(sub) -> tuple[argparse.ArgumentParser, argparse.ArgumentParser]:
    sp_compliance = sub.add_parser("compliance", help="NIST SSDF compliance reporting")
    compliance_sub = sp_compliance.add_subparsers(dest="compliance_command", metavar="<subcommand>")
    sp_compliance_report = compliance_sub.add_parser("report", help="show SSDF practice coverage")
    sp_compliance_report.add_argument("--ledger", type=Path, default=None)

    sp_policy = sub.add_parser("policy", help="policy engine commands")
    policy_sub = sp_policy.add_subparsers(dest="policy_command", metavar="<subcommand>")
    sp_policy_check = policy_sub.add_parser("check", help="evaluate request against cedar policies")
    sp_policy_check.add_argument("request", help="path to request JSON file")
    return sp_compliance, sp_policy


def _build_parser() -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    parser = argparse.ArgumentParser(
        prog="qorlogic",
        description="S.H.I.E.L.D. governance skills for AI coding hosts.",
    )
    parser.add_argument("--version", action="version", version=f"qorlogic {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    _register_install_family(sub)
    _register_misc(sub)
    sp_compliance, sp_policy = _register_compliance_policy(sub)
    return parser, {"compliance": sp_compliance, "policy": sp_policy}


def _dispatch(args: argparse.Namespace) -> int | None:
    direct = {
        "install": lambda: _do_install(
            args.host, scope=args.scope,
            target_override=args.target, dry_run=args.dry_run,
        ),
        "uninstall": lambda: _do_uninstall(
            host=args.host, scope=args.scope, target_override=args.target,
        ),
        "list": lambda: _do_list(args),
        "info": lambda: _do_info(args),
        "compile": lambda: _do_compile(args),
        "verify-ledger": lambda: _do_verify_ledger(args),
    }
    if args.command in direct:
        return direct[args.command]()
    return None


def main(argv: list[str] | None = None) -> int:
    parser, subparsers = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    rc = _dispatch(args)
    if rc is not None:
        return rc

    if args.command == "compliance":
        if getattr(args, "compliance_command", None) == "report":
            print(_do_compliance_report(ledger_path=getattr(args, "ledger", None)))
            return 0
        subparsers["compliance"].print_help()
        return 0
    if args.command == "init":
        from qor.cli_policy import do_init
        return do_init(args)
    if args.command == "policy":
        from qor.cli_policy import do_policy_check
        if getattr(args, "policy_command", None) == "check":
            return do_policy_check(args)
        subparsers["policy"].print_help()
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
