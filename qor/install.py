"""Install/uninstall/list helpers for the qor-logic CLI.

Phase 24 update: install source root is per-host (``variants/<host>/``), and
the install dispatcher uses each host's install_map (keyed by source-path
prefix) to route manifest entries to the correct target directory. This lets
claude/codex/kilo-code share the ``skills/``+``agents/`` layout while gemini
uses ``commands/`` without changing the copy loop.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


def _load_manifest(manifest_path: Path) -> dict | None:
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _resolve_dest(rel: str, install_map: dict[str, Path]) -> Path | None:
    for prefix, target_dir in install_map.items():
        if rel.startswith(prefix):
            return target_dir / rel[len(prefix):]
    return None


def _copy_entry(src: Path, dst: Path, data: bytes, dry_run: bool) -> None:
    """Write the already-verified ``data`` (read once from ``src``) to ``dst``."""
    if dry_run:
        print(f"  [dry-run] {src} -> {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    shutil.copystat(src, dst)


def _write_install_record(base: Path, installed: list[dict]) -> None:
    base.mkdir(parents=True, exist_ok=True)
    (base / ".qorlogic-installed.json").write_text(
        json.dumps({"files": installed}, indent=2) + "\n",
        encoding="utf-8",
    )


def _resolve_install_source(host: str, dist_root: Path | None) -> tuple[Path, dict | None]:
    if dist_root is None:
        from qor.cli import _default_dist_root
        dist_root = _default_dist_root()
    source_root = dist_root / "variants" / host
    return source_root, _load_manifest(source_root / "manifest.json")


def _verified_entries(
    manifest: dict, source_root: Path, install_map: dict[str, Path],
) -> tuple[list[tuple[Path, Path, bytes]], list[str]]:
    """Resolve the entries install copies and check each file's bytes.

    Phase 302 (GH #440): install used to record the manifest's sha256 in the
    receipt without hashing the bytes it copied, so a stale manifest or an
    edited shipped file produced a receipt that did not describe the installed
    files. Each file is now read once and hashed before anything is written.
    Returns ``(planned, mismatches)``: the ``(src, dst, data)`` copies whose
    bytes match their manifest sha256, and the ``install_rel_path`` of every
    file whose bytes do not. Entries whose source file is absent, or that no
    install route covers, are neither copied nor checked.
    """
    planned: list[tuple[Path, Path, bytes]] = []
    mismatches: list[str] = []
    for entry in manifest["files"]:
        rel = entry["install_rel_path"]
        src = source_root / rel
        dst = _resolve_dest(rel, install_map)
        if not src.exists() or dst is None:
            continue
        data = src.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            mismatches.append(rel)
            continue
        planned.append((src, dst, data))
    return planned, mismatches


def _copy_verified(planned: list[tuple[Path, Path, bytes]], dry_run: bool) -> list[dict]:
    installed: list[dict] = []
    for src, dst, data in planned:
        _copy_entry(src, dst, data, dry_run)
        if not dry_run:
            installed.append({"path": str(dst), "sha256": hashlib.sha256(data).hexdigest()})
    return installed


def _do_install(
    host: str,
    scope: str = "repo",
    target_override: Path | None = None,
    dist_root: Path | None = None,
    dry_run: bool = False,
) -> int:
    """Install compiled variants into a host target directory."""
    from qor.hosts import resolve

    target = resolve(host, scope=scope, target_override=target_override)
    source_root, manifest = _resolve_install_source(host, dist_root)
    if manifest is None:
        print(
            f"No manifest.json for host {host!r} at {source_root}. "
            f"Run 'qor-logic compile' first.",
            file=sys.stderr,
        )
        return 1

    planned, mismatches = _verified_entries(manifest, source_root, target.install_map)
    if mismatches:
        print(
            f"Install refused: {len(mismatches)} file(s) under {source_root} do not "
            f"match the sha256 in its manifest.json; nothing was installed. "
            f"Rebuild the dist with 'qor-logic compile' or reinstall the package.",
            file=sys.stderr,
        )
        for rel in mismatches:
            print(f"  sha256 mismatch: {rel}", file=sys.stderr)
        return 1
    installed = _copy_verified(planned, dry_run)
    if dry_run:
        print(f"[dry-run] Would install {len(manifest['files'])} files to {target.name}")
    elif installed:
        _write_install_record(target.base, installed)
        print(f"Installed {len(installed)} files to {target.name}")
    return 0


def _remove_file_and_empty_parents(path: Path, base: Path) -> bool:
    if not path.exists():
        return False
    path.unlink()
    parent = path.parent
    while parent != base and parent.exists():
        try:
            parent.rmdir()
            parent = parent.parent
        except OSError:
            break
    return True


def _do_uninstall(
    host: str = "claude",
    scope: str = "repo",
    target_override: Path | None = None,
    dry_run: bool = False,
) -> int:
    """Remove previously installed files using the install record.

    With dry_run (Phase 167; GH #250) the record is read and the removal set
    listed, but nothing is unlinked.
    """
    if target_override is not None:
        base = target_override
    else:
        from qor.hosts import resolve
        target = resolve(host, scope=scope)
        base = target.base

    record_path = base / ".qorlogic-installed.json"
    if not record_path.exists():
        print("No install record found.", file=sys.stderr)
        return 1

    data = json.loads(record_path.read_text(encoding="utf-8"))
    if dry_run:
        existing = [e["path"] for e in data["files"] if Path(e["path"]).exists()]
        print(f"[dry] Would remove {len(existing)} files:")
        for p in existing:
            print(f"[dry]   {p}")
        print(f"[dry] would remove install record {record_path}")
        return 0
    removed = sum(
        1 for entry in data["files"]
        if _remove_file_and_empty_parents(Path(entry["path"]), base)
    )
    record_path.unlink()
    print(f"Removed {removed} files")
    return 0


def _list_available() -> int:
    from qor.cli import _default_dist_root
    dist_root = _default_dist_root()
    manifest = _load_manifest(dist_root / "manifest.json")
    if manifest is None:
        print("No manifest. Run 'qor-logic compile' first.", file=sys.stderr)
        return 1
    seen: set[str] = set()
    for entry in manifest["files"]:
        sid = entry["id"]
        if sid not in seen:
            print(sid)
            seen.add(sid)
    return 0


def _list_installed(host: str, scope: str = "repo") -> int:
    from qor.hosts import resolve
    target = resolve(host, scope=scope)
    record = target.base / ".qorlogic-installed.json"
    if not record.exists():
        print("No install record found.", file=sys.stderr)
        return 1
    data = json.loads(record.read_text(encoding="utf-8"))
    for entry in data["files"]:
        print(entry["path"])
    return 0


def _do_list(args: argparse.Namespace) -> int:
    """List available or installed skills."""
    if getattr(args, "available", False):
        return _list_available()
    if getattr(args, "installed", False):
        return _list_installed(
            getattr(args, "host", "claude"),
            getattr(args, "scope", "repo"),
        )
    print("Specify --available or --installed", file=sys.stderr)
    return 1
