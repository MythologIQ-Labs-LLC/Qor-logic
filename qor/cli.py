"""Qor-logic CLI -- agent-agnostic skill distribution harness."""
from __future__ import annotations

import argparse
from importlib import metadata
from pathlib import Path

from qor.install import (
    _do_install,
    _do_list,
    _do_uninstall,
)

try:
    __version__ = metadata.version("qor-logic")
except metadata.PackageNotFoundError:
    __version__ = "0+unknown"


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


def _do_verify_ledger(args: argparse.Namespace) -> int:
    """Verify META_LEDGER.md chain.

    Phase 66 (GH #55) extensions:
    - ``--ledger PATH``: explicit ledger path override; defaults to
      ``workdir.meta_ledger()``.
    - ``--post-anchor``: switch to post-anchor verification mode for
      re-anchored consumer ledgers (tolerates disclosed pre-anchor
      failures up to a boundary).
    - ``--boundary N``: pin the post-anchor boundary at entry N; only
      valid with ``--post-anchor``. Default is auto-detect.
    """
    from qor.scripts import ledger_hash
    from qor import workdir
    explicit = getattr(args, "ledger", None)
    ledger_path = Path(explicit) if explicit else workdir.meta_ledger()
    if getattr(args, "post_anchor", False):
        boundary = getattr(args, "boundary", None)
        return ledger_hash.verify_post_anchor(ledger_path, boundary_entry=boundary)
    return ledger_hash.verify(
        ledger_path,
        tolerate_known_grandfathered=getattr(args, "tolerate_known_grandfathered", False),
        grandfather_cutoff=getattr(args, "grandfather_cutoff", 207),
    )


def _do_seed(args: argparse.Namespace) -> int:
    """Scaffold governance files in a workspace."""
    from qor.seed import seed
    base = getattr(args, "target", None) or Path.cwd()
    result = seed(base=base, quiet=False)
    print(f"seed: {len(result.created)} created, {len(result.skipped)} skipped")
    return 0


def _do_governance_health(args: argparse.Namespace) -> int:
    """Classify governance artifact health; exit 0/1/2 per the Phase 109 contract."""
    from qor.scripts import governance_health as gh

    return gh.main(["--repo-root", args.repo_root, "--profile", args.profile])


def _do_governance_index(args: argparse.Namespace) -> int:
    """Detect governance index drift; exit 0 clean / 1 drift (Phase 112; WARN-only)."""
    from qor.scripts import governance_index as gi

    return gi.main(["--repo-root", args.repo_root])


def _do_capabilities(args: argparse.Namespace) -> int:
    """Phase 58: governance capability surface."""
    import json as _json
    from dataclasses import asdict
    from qor import capabilities as caps
    cmd = getattr(args, "capabilities_command", None)
    if cmd == "inventory":
        inv = caps.build_inventory(repo_root=".")
        print(_json.dumps([asdict(c) for c in inv], indent=2))
        return 0
    if cmd == "context":
        packet = caps.build_context_packet(repo_root=".", target=args.target)
        print(_json.dumps(asdict(packet), indent=2))
        return 0
    if cmd == "route-risk":
        report = caps.route_risk(repo_root=".", changed_files=tuple(args.changed_file))
        print(_json.dumps(asdict(report), indent=2))
        return 0
    if cmd == "verification-request":
        from qor.capabilities.verification_request import to_dict
        req = caps.build_verification_request(
            repo_root=".", target=args.target, required_confidence=args.confidence,
        )
        payload = to_dict(req)
        print(_json.dumps(payload, indent=2))
        if getattr(args, "write_gate", False):
            out_dir = Path(".qor") / "gates" / "verification-requests"
            out_dir.mkdir(parents=True, exist_ok=True)
            slug = args.target.replace("/", "_").replace(".", "_")
            out = out_dir / f"{slug}.json"
            out.write_text(_json.dumps(payload, indent=2), encoding="utf-8")
            print(f"wrote {out}")
        return 0
    print("capabilities: provide a subcommand (inventory | context | route-risk | verification-request)")
    return 1


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

    sp_init = sub.add_parser("init", help="initialize the qor-logic config (.qorlogic/config.json)")
    sp_init.add_argument("--host", default="claude", choices=_HOSTS_CHOICES)
    sp_init.add_argument("--scope", default="repo", choices=_SCOPES_CHOICES)
    sp_init.add_argument("--profile", default="sdlc", choices=_PROFILE_CHOICES)
    sp_init.add_argument("--tone", default=None, choices=["technical", "standard", "plain"])
    sp_init.add_argument("--target", type=Path, default=None)


def _register_misc(sub) -> None:
    sp_info = sub.add_parser("info", help="show skill metadata")
    sp_info.add_argument("skill", help="skill name")
    sp_compile = sub.add_parser("compile", help="regenerate variants from source")
    sp_compile.add_argument("--dry-run", action="store_true")
    # Phase 75 (GH #38): substantiate-capability report
    from qor.cli_handlers import substantiate as substantiate_handlers
    substantiate_handlers.register(sub)
    sp_verify = sub.add_parser("verify-ledger", help="verify META_LEDGER.md chain")
    sp_verify.add_argument(
        "--ledger", default=None,
        help="explicit ledger path (default: workdir.meta_ledger())",
    )
    sp_verify.add_argument(
        "--post-anchor", action="store_true",
        help="tolerate disclosed pre-anchor failures (Phase 66, GH #55)",
    )
    sp_verify.add_argument(
        "--boundary", type=int, default=None,
        help="pin post-anchor boundary at entry N (default: auto-detect)",
    )
    sp_verify.add_argument(
        "--tolerate-known-grandfathered", action="store_true",
        help="accept chain failures on SG-ConcurrentLedgerRace-A documented residuals (Phase 91, GH #85)",
    )
    sp_verify.add_argument(
        "--grandfather-cutoff", type=int, default=207,
        help="entry-number upper bound for --tolerate-known-grandfathered (default 207; Phase 76 cutoff)",
    )
    sp_seed = sub.add_parser("seed", help="scaffold governance files in a workspace")
    sp_seed.add_argument("--target", type=Path, default=None)
    sp_gh = sub.add_parser("governance-health", help="classify governance artifact health (Phase 109)")
    sp_gh.add_argument("--repo-root", default=".", help="workspace root to inspect")
    sp_gh.add_argument("--profile", default="skill-entry", help="named required-artifact set")
    sp_gi = sub.add_parser("governance-index", help="detect governance index drift (Phase 112)")
    sp_gi.add_argument("--repo-root", default=".", help="workspace root to inspect")


def _register_capabilities(sub) -> argparse.ArgumentParser:
    sp_caps = sub.add_parser("capabilities", help="governance capability surface (Phase 58)")
    caps_sub = sp_caps.add_subparsers(dest="capabilities_command", metavar="<subcommand>")
    caps_sub.add_parser("inventory", help="emit KNOWN_CAPABILITIES as JSON")
    sp_ctx = caps_sub.add_parser("context", help="emit governance context packet for a target")
    sp_ctx.add_argument("--target", required=True)
    sp_route = caps_sub.add_parser("route-risk", help="route changed files to a risk grade + required skills")
    sp_route.add_argument("--changed-file", action="append", default=[], required=True)
    sp_vr = caps_sub.add_parser("verification-request", help="emit verification-request artifact for a target")
    sp_vr.add_argument("--target", required=True)
    sp_vr.add_argument("--confidence", default="targeted")
    sp_vr.add_argument("--write-gate", action="store_true", default=False)
    return sp_caps


def _register_compliance_policy(sub) -> tuple[argparse.ArgumentParser, argparse.ArgumentParser]:
    from qor.cli_handlers import compliance as compliance_handlers
    sp_compliance = compliance_handlers.register(sub)

    sp_policy = sub.add_parser("policy", help="policy engine commands")
    policy_sub = sp_policy.add_subparsers(dest="policy_command", metavar="<subcommand>")
    sp_policy_check = policy_sub.add_parser("check", help="evaluate request against cedar policies")
    sp_policy_check.add_argument("request", help="path to request JSON file")
    return sp_compliance, sp_policy


def _build_parser() -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    parser = argparse.ArgumentParser(
        prog="qor-logic",
        description="S.H.I.E.L.D. governance skills for AI coding hosts.",
    )
    parser.add_argument("--version", action="version", version=f"qor-logic {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    _register_install_family(sub)
    _register_misc(sub)
    _register_capabilities(sub)
    sp_compliance, sp_policy = _register_compliance_policy(sub)
    from qor.cli_handlers import release as release_handlers
    sp_release = release_handlers.register(sub)
    return parser, {"compliance": sp_compliance, "policy": sp_policy, "release": sp_release}


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
        "seed": lambda: _do_seed(args),
        "governance-health": lambda: _do_governance_health(args),
        "governance-index": lambda: _do_governance_index(args),
        "capabilities": lambda: _do_capabilities(args),
        "substantiate-capability": lambda: args.func(args),
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
        from qor.cli_handlers import compliance as compliance_handlers
        rc = compliance_handlers.dispatch(args)
        if rc is not None:
            return rc
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
    if args.command == "release":
        from qor.cli_handlers import release as release_handlers
        rc = release_handlers.dispatch(args)
        if rc is not None:
            return rc
        subparsers["release"].print_help()
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
