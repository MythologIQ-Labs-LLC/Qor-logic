"""QorLogic CLI -- agent-agnostic skill distribution harness."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

__version__ = "0.12.0"


def _default_dist_root() -> Path:
    from qor import resources as _resources
    return Path(str(_resources.asset("dist")))


def _do_install(
    host: str,
    target_override: Path | None = None,
    dist_root: Path | None = None,
    dry_run: bool = False,
) -> int:
    """Install compiled variants into a host target directory."""
    from qor.hosts import resolve

    target = resolve(host, target_override=target_override)
    if dist_root is None:
        dist_root = _default_dist_root()

    manifest_path = dist_root / "manifest.json"
    if not manifest_path.exists():
        print("No manifest.json found. Run 'qorlogic compile' first.", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    claude_root = dist_root / "variants" / "claude"
    installed = []

    for entry in manifest["files"]:
        rel = entry["install_rel_path"]
        src = claude_root / rel
        if not src.exists():
            continue

        if rel.startswith("skills/"):
            dst = target.skills_dir / rel[len("skills/"):]
        elif rel.startswith("agents/"):
            dst = target.agents_dir / rel[len("agents/"):]
        else:
            continue

        if dry_run:
            print(f"  [dry-run] {src} -> {dst}")
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        installed.append({"path": str(dst), "sha256": entry["sha256"]})

    if not dry_run and installed:
        record_path = (target_override or target.skills_dir.parent) / ".qorlogic-installed.json"
        record_path.write_text(
            json.dumps({"files": installed}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Installed {len(installed)} files to {target.name}")
    elif dry_run:
        print(f"[dry-run] Would install {len(manifest['files'])} files to {target.name}")

    return 0


def _do_uninstall(
    host: str = "claude",
    target_override: Path | None = None,
) -> int:
    """Remove previously installed files using the install record."""
    base = target_override
    if base is None:
        from qor.hosts import resolve
        target = resolve(host)
        base = target.skills_dir.parent

    record_path = base / ".qorlogic-installed.json"
    if not record_path.exists():
        print("No install record found.", file=sys.stderr)
        return 1

    data = json.loads(record_path.read_text(encoding="utf-8"))
    removed = 0
    for entry in data["files"]:
        p = Path(entry["path"])
        if p.exists():
            p.unlink()
            removed += 1
            # Clean empty parent dirs
            parent = p.parent
            while parent != base and parent.exists():
                try:
                    parent.rmdir()
                    parent = parent.parent
                except OSError:
                    break

    record_path.unlink()
    print(f"Removed {removed} files")
    return 0


def _do_list(args: argparse.Namespace) -> int:
    """List available or installed skills."""
    if getattr(args, "available", False):
        dist_root = _default_dist_root()
        manifest_path = dist_root / "manifest.json"
        if not manifest_path.exists():
            print("No manifest. Run 'qorlogic compile' first.", file=sys.stderr)
            return 1
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        seen = set()
        for entry in data["files"]:
            sid = entry["id"]
            if sid not in seen:
                print(sid)
                seen.add(sid)
        return 0

    if getattr(args, "installed", False):
        host = getattr(args, "host", "claude")
        from qor.hosts import resolve
        target = resolve(host)
        record = target.skills_dir.parent / ".qorlogic-installed.json"
        if not record.exists():
            print("No install record found.", file=sys.stderr)
            return 1
        data = json.loads(record.read_text(encoding="utf-8"))
        for entry in data["files"]:
            print(entry["path"])
        return 0

    print("Specify --available or --installed", file=sys.stderr)
    return 1


def _do_info(args: argparse.Namespace) -> int:
    """Show skill metadata from compiled variants."""
    skill_name = args.skill
    dist_root = _default_dist_root()
    skill_md = dist_root / "variants" / "claude" / "skills" / skill_name / "SKILL.md"
    if not skill_md.exists():
        # Try as loose skill
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
    """Verify META_LEDGER.md chain."""
    from qor.scripts import ledger_hash
    from qor import workdir
    ledger_path = workdir.meta_ledger()
    return ledger_hash.verify(ledger_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="qorlogic",
        description="S.H.I.E.L.D. governance skills for AI coding hosts.",
    )
    parser.add_argument(
        "--version", action="version", version=f"qorlogic {__version__}",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # install
    sp_install = sub.add_parser("install", help="install skills into an AI coding host")
    sp_install.add_argument("--host", required=True, choices=["claude", "kilo-code", "codex"])
    sp_install.add_argument("--target", type=Path, default=None, help="override install path")
    sp_install.add_argument("--dry-run", action="store_true")

    # uninstall
    sp_uninstall = sub.add_parser("uninstall", help="remove installed skills")
    sp_uninstall.add_argument("--host", default="claude", choices=["claude", "kilo-code", "codex"])
    sp_uninstall.add_argument("--target", type=Path, default=None)

    # list
    sp_list = sub.add_parser("list", help="enumerate available or installed skills")
    sp_list.add_argument("--available", action="store_true")
    sp_list.add_argument("--installed", action="store_true")
    sp_list.add_argument("--host", default="claude")

    # info
    sp_info = sub.add_parser("info", help="show skill metadata")
    sp_info.add_argument("skill", help="skill name")

    # compile
    sp_compile = sub.add_parser("compile", help="regenerate variants from source")
    sp_compile.add_argument("--dry-run", action="store_true")

    # verify-ledger
    sub.add_parser("verify-ledger", help="verify META_LEDGER.md chain")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "install":
        return _do_install(args.host, target_override=args.target, dry_run=args.dry_run)
    if args.command == "uninstall":
        return _do_uninstall(host=args.host, target_override=args.target)
    if args.command == "list":
        return _do_list(args)
    if args.command == "info":
        return _do_info(args)
    if args.command == "compile":
        return _do_compile(args)
    if args.command == "verify-ledger":
        return _do_verify_ledger(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
