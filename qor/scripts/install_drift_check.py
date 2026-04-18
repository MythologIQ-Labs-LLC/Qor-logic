"""Detect drift between source SKILL.md files and installed copies.

Phase 32 Phase 1. Operator-facing check run ad-hoc via
`python -m qor.scripts.install_drift_check --host claude --scope repo`
or pre-phase via /qor-plan Step 0.2.

Design: byte-identical SHA256 comparison between qor/skills/**/SKILL.md
source and the installed counterpart under the host's skills_dir.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _source_skills(repo_root: Path) -> list[Path]:
    return sorted((repo_root / "qor" / "skills").rglob("SKILL.md"))


def check(host: str = "claude", scope: str = "repo") -> list[str]:
    """Compare installed SKILL.md files vs qor/skills/** source.

    Returns list of drift descriptions (empty if clean).

    Uses qor.hosts.resolve to locate the installed skills_dir. Source tree
    walks qor/skills/** for SKILL.md; for each, locates the counterpart at
    <skills_dir>/<skill-dir-name>/SKILL.md (category flattened, matching
    dist_compile's output layout).
    """
    from qor import hosts
    try:
        target = hosts.resolve(host, scope=scope)
    except (KeyError, ValueError) as exc:
        raise ValueError(f"host not supported: {host!r} ({exc})") from exc

    skills_dir = target.skills_dir
    repo = Path.cwd()
    drift: list[str] = []
    for source in _source_skills(repo):
        skill_dir_name = source.parent.name
        counterpart = skills_dir / skill_dir_name / "SKILL.md"
        rel = source.relative_to(repo).as_posix()
        if not counterpart.exists():
            drift.append(f"missing install for {rel} (expected at {counterpart})")
            continue
        if _sha256(source) != _sha256(counterpart):
            drift.append(f"SHA256 mismatch: {rel} differs from {counterpart}")
    return drift


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="claude")
    ap.add_argument("--scope", default="repo", choices=("repo", "global"))
    args = ap.parse_args()
    drift = check(host=args.host, scope=args.scope)
    if not drift:
        print(f"OK: local {args.host} install matches repo source.")
        return 0
    print(f"WARNING: local {args.host} install differs from repo source:")
    for d in drift:
        print(f"  - {d}")
    print("")
    print(f"Fix: qorlogic install --host {args.host} --scope {args.scope}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
