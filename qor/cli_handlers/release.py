"""release subcommand handlers (Phase 55).

Hosts ``do_sbom`` for ad-hoc CycloneDX SBOM generation outside the seal cycle.
Mirrors the ``compliance`` handler-module pattern from Phase 54.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def do_sbom(args: argparse.Namespace) -> int:
    """Emit a CycloneDX v1.5 SBOM to the requested path."""
    from qor.scripts.sbom_emit import write
    repo_root = getattr(args, "repo_root", None) or Path.cwd()
    out = getattr(args, "out", Path("dist/sbom.cdx.json"))
    written = write(repo_root, out)
    print(f"SBOM written: {written}")
    return 0


def register(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Register the release subcommand group with the parser."""
    sp_release = sub.add_parser("release", help="release-time artifact emitters")
    release_sub = sp_release.add_subparsers(dest="release_command", metavar="<subcommand>")

    sp_sbom = release_sub.add_parser("sbom", help="emit CycloneDX v1.5 SBOM")
    sp_sbom.add_argument("--repo-root", type=Path, default=None)
    sp_sbom.add_argument("--out", type=Path, default=Path("dist/sbom.cdx.json"))

    return sp_release


def dispatch(args: argparse.Namespace) -> int | None:
    """Route release subcommand args to the right handler."""
    if getattr(args, "release_command", None) == "sbom":
        return do_sbom(args)
    return None
