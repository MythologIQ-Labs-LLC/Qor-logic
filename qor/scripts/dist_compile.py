#!/usr/bin/env python3
"""Compile qor/skills/ and qor/agents/ to per-variant outputs under qor/dist/variants/.

v1 is an identity compile: claude and kilo-code variants receive the same content;
codex writes only a .gitkeep stub. Format divergence is deferred.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from qor import resources as _resources

SKILLS_SRC = Path(str(_resources.asset("skills")))
AGENTS_SRC = Path(str(_resources.asset("agents")))
DEFAULT_OUT = Path(str(_resources.asset("dist")))

TARGETS = ("claude", "kilo-code", "codex", "gemini")


def list_source_skills(src: Path) -> list[Path]:
    """Every directory containing a SKILL.md."""
    return sorted(p.parent for p in src.rglob("SKILL.md"))


def list_loose_skills(src: Path) -> list[Path]:
    """Skills that are single .md files at category level (log-decision.md, track-shadow-genome.md)."""
    loose: list[Path] = []
    for category in src.iterdir():
        if not category.is_dir():
            continue
        for item in category.iterdir():
            if item.is_file() and item.suffix == ".md":
                loose.append(item)
    return sorted(loose)


def list_source_agents(src: Path) -> list[Path]:
    """Every .md under qor/agents/<category>/ (flat per category)."""
    return sorted(p for p in src.rglob("*.md") if p.is_file())


def emit_claude(skills_dirs: list[Path], loose_skills: list[Path], agents: list[Path], out: Path) -> None:
    skills_root = out / "skills"
    agents_root = out / "agents"
    skills_root.mkdir(parents=True, exist_ok=True)
    agents_root.mkdir(parents=True, exist_ok=True)

    for skill_dir in skills_dirs:
        dst = skills_root / skill_dir.name
        shutil.copytree(skill_dir, dst)

    for loose in loose_skills:
        shutil.copy2(loose, skills_root / loose.name)

    for agent in agents:
        shutil.copy2(agent, agents_root / agent.name)


def emit_kilocode(skills_dirs: list[Path], loose_skills: list[Path], agents: list[Path], out: Path) -> None:
    # Identical to claude in v1; separate function reserved for future divergence.
    emit_claude(skills_dirs, loose_skills, agents, out)


def emit_codex(skills_dirs: list[Path], loose_skills: list[Path], agents: list[Path], out: Path) -> None:
    """Emit codex variant. Identity-copy of claude variant for now; format TBD."""
    emit_claude(skills_dirs, loose_skills, agents, out)


def clean_variant(variant_root: Path) -> None:
    if variant_root.exists():
        shutil.rmtree(variant_root)
    variant_root.mkdir(parents=True, exist_ok=True)


def compile_all(out_root: Path, dry_run: bool = False) -> dict:
    skills_dirs = list_source_skills(SKILLS_SRC)
    loose_skills = list_loose_skills(SKILLS_SRC)
    agents = list_source_agents(AGENTS_SRC)

    summary = {
        "skill_dirs": len(skills_dirs),
        "loose_skills": len(loose_skills),
        "agents": len(agents),
        "targets": {},
    }

    for target in TARGETS:
        variant_root = out_root / "variants" / target
        summary["targets"][target] = str(variant_root)
        if dry_run:
            continue
        clean_variant(variant_root)
        if target == "claude":
            emit_claude(skills_dirs, loose_skills, agents, variant_root)
        elif target == "kilo-code":
            emit_kilocode(skills_dirs, loose_skills, agents, variant_root)
        elif target == "codex":
            emit_codex(skills_dirs, loose_skills, agents, variant_root)
        elif target == "gemini":
            from qor.scripts.gemini_variant import emit_gemini
            emit_gemini(skills_dirs, loose_skills, agents, variant_root)

    if not dry_run:
        _emit_manifest(out_root)

    return summary


def _build_manifest_entries(variant_root: Path) -> list[dict]:
    files: list[dict] = []
    for p in sorted(variant_root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(variant_root).as_posix()
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        parts = rel.split("/")
        skill_id = parts[1] if len(parts) >= 2 and parts[0] == "skills" else parts[-1]
        files.append({
            "id": skill_id,
            "source_path": rel,
            "install_rel_path": rel,
            "sha256": sha,
        })
    return files


def _write_manifest(path: Path, files: list[dict]) -> None:
    manifest = {
        "schema_version": "1",
        "generated_ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": files,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _emit_manifest(out_root: Path) -> None:
    """Write per-variant manifests and a top-level cross-variant index.

    Each compiled variant at ``variants/<host>/`` gets its own ``manifest.json``.
    The top-level ``out_root/manifest.json`` is the claude variant entries kept
    as a backwards-compatible cross-variant index for ``list --available``.
    """
    variants_root = out_root / "variants"
    if not variants_root.exists():
        return
    claude_files: list[dict] = []
    for variant_dir in sorted(variants_root.iterdir()):
        if not variant_dir.is_dir():
            continue
        files = _build_manifest_entries(variant_dir)
        if not files:
            continue
        _write_manifest(variant_dir / "manifest.json", files)
        if variant_dir.name == "claude":
            claude_files = files
    if claude_files:
        _write_manifest(out_root / "manifest.json", claude_files)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--out-root", type=Path, default=DEFAULT_OUT, help="Output root (default: qor/dist)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    summary = compile_all(args.out_root, dry_run=args.dry_run)
    action = "Would emit" if args.dry_run else "Emitted"
    print(f"{action}: {summary['skill_dirs']} skill dirs, {summary['loose_skills']} loose skills, {summary['agents']} agents")
    for target, path in summary["targets"].items():
        print(f"  {target}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
