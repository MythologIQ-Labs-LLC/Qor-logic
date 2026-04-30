"""Phase 52: NIST SSDF practice tag emission.

Pure functions mapping (change_class, files_touched) to SSDF practice IDs
per qor/references/doctrine-nist-ssdf-alignment.md §"Evidence Collection".
Invoked by /qor-substantiate Step 7.4 to emit `**SSDF Practices**:` block
into SESSION SEAL entries before Merkle hash computation.

Forward-only: Phase 52+ entries get tags; Phase ≤ 51 entries grandfathered
(immutable Merkle chain forbids retroactive edit).
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


_PATTERN_RULES: list[tuple[re.Pattern, list[str]]] = [
    (re.compile(r"qor/skills/governance/qor-audit/"),         ["PW.4.1", "PS.3.2"]),
    (re.compile(r"qor/skills/governance/qor-substantiate/"),  ["PS.2.1", "PW.4.1"]),
    (re.compile(r"qor/skills/governance/qor-validate/"),      ["PW.9.1"]),
    (re.compile(r"qor/skills/sdlc/qor-plan/"),                ["PW.1.1"]),
    (re.compile(r"qor/skills/sdlc/qor-implement/"),           ["PW.1.1", "PW.5.1"]),
    (re.compile(r"qor/scripts/(shadow_process|create_shadow_issue)|PROCESS_SHADOW_GENOME"), ["RV.1.1", "RV.1.2"]),
    (re.compile(r"qor/scripts/remediate_"),                   ["RV.2.1"]),
    (re.compile(r"qor/policies/.*\.cedar"),                   ["PW.7.1"]),
    (re.compile(r"qor/references/doctrine-"),                 ["PO.1.3"]),
    (re.compile(r"qor/reliability/"),                         ["PS.3.1"]),
    (re.compile(r"qor/scripts/.*\.py$"),                      ["PW.5.1"]),
    (re.compile(r"^tests/test_"),                             ["PW.5.1"]),
]

_CLASS_RULES: dict[str, list[str]] = {
    "feature":  ["PO.1.4", "PW.1.1"],
    "breaking": ["PO.1.4", "PW.1.1", "PW.4.1"],
    "hotfix":   ["RV.2.1"],
}


def compute_tags(
    change_class: str,
    files_touched: list[str],
    *,
    include_seal: bool = True,
) -> list[str]:
    """Return sorted-unique SSDF practice tags for the given phase shape."""
    tags: set[str] = set(_CLASS_RULES.get(change_class, []))
    for f in files_touched:
        norm = f.replace("\\", "/")
        for pattern, practices in _PATTERN_RULES:
            if pattern.search(norm):
                tags.update(practices)
    if include_seal:
        tags.add("PS.2.1")
    return sorted(tags)


def format_tag_line(tags: list[str]) -> str:
    return f"**SSDF Practices**: {', '.join(tags)}"


def files_touched_from_git(repo_root: Path, base_ref: str = "origin/main") -> list[str]:
    """Compute files_touched via `git diff --name-only base_ref...HEAD`.

    Replaces the VETO'd Phase 51 approach of reading from a non-existent
    gate_chain.read_phase_artifact('implement') artifact.
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        cwd=str(repo_root), capture_output=True, text=True, check=False,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--change-class", required=True, choices=["feature", "breaking", "hotfix"])
    ap.add_argument("--files", help="comma-separated file list; if omitted, computed via git diff")
    ap.add_argument("--base-ref", default="origin/main")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument(
        "--include-seal",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="add PS.2.1 to the tags (default; --no-include-seal to omit)",
    )
    args = ap.parse_args(argv)
    if args.files:
        files = [f.strip() for f in args.files.split(",") if f.strip()]
    else:
        files = files_touched_from_git(args.repo_root, args.base_ref)
    tags = compute_tags(args.change_class, files, include_seal=args.include_seal)
    print(format_tag_line(tags))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
