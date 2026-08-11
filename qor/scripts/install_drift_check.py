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
from pathlib import Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _source_skills(repo_root: Path) -> list[Path]:
    return sorted((repo_root / "qor" / "skills").rglob("SKILL.md"))


SCOPES = ("repo", "global")


def _skills_dir(host: str, scope: str) -> Path | None:
    """Resolve a host+scope to its skills directory, or None if unsupported."""
    from qor import hosts

    try:
        return hosts.resolve(host, scope=scope).skills_dir
    except (KeyError, ValueError):
        return None


def installed_scopes(host: str = "claude") -> list[str]:
    """Return the scopes where an install actually exists.

    Discovery, not enumeration: a scope where an install *could* live is not
    reported. This is what lets `check(scope="auto")` inspect the corpus the
    operator is really running instead of a hardcoded default.
    """
    found = []
    for scope in SCOPES:
        skills_dir = _skills_dir(host, scope)
        if skills_dir is not None and any(skills_dir.glob("*/SKILL.md")):
            found.append(scope)
    return found


def _check_auto(host: str) -> list[str]:
    """Check every scope that actually has an install."""
    scopes = installed_scopes(host)
    if not scopes:
        return [f"no install found for host {host!r} at any scope"]
    findings: list[str] = []
    for scope in scopes:
        findings.extend(check(host=host, scope=scope))
    return findings


def check(host: str = "claude", scope: str = "repo") -> list[str]:
    """Compare installed SKILL.md files vs qor/skills/** source.

    Returns list of drift descriptions (empty if clean).

    Uses qor.hosts.resolve to locate the installed skills_dir. Source tree
    walks qor/skills/** for SKILL.md; for each, locates the counterpart at
    <skills_dir>/<skill-dir-name>/SKILL.md (category flattened, matching
    dist_compile's output layout).
    """
    if scope == "auto":
        return _check_auto(host)

    skills_dir = _skills_dir(host, scope)
    if skills_dir is None:
        raise ValueError(f"host not supported: {host!r}")

    # An absent install is ONE fact, not one defect per source skill. Reporting
    # it per-skill produced 30 guaranteed-irrelevant findings on every run,
    # which is how a correct control gets trained around (GH #314).
    #
    # Keyed on the directory not existing, NOT on it being empty: an existing
    # but empty skills dir is a partial install, where naming each absent skill
    # is the useful answer and is the contract
    # tests/test_install_drift_check.py::test_missing_install_file_flagged pins.
    if not skills_dir.exists():
        return [f"host {host!r} is not installed at scope {scope!r} ({skills_dir})"]

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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="claude")
    ap.add_argument("--scope", default="repo", choices=("repo", "global", "auto"))
    args = ap.parse_args(argv)
    drift = check(host=args.host, scope=args.scope)
    if not drift:
        print(f"OK: local {args.host} install matches repo source.")
        return 0
    print(f"WARNING: local {args.host} install differs from repo source:")
    for d in drift:
        print(f"  - {d}")
    print("")
    print(f"Fix: qor-logic install --host {args.host} --scope {args.scope}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
