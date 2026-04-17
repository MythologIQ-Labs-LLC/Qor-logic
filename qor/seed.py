"""Workspace scaffold primitive.

Creates the minimal file set that `/qor-*` skills assume exists. Idempotent:
files already present are never overwritten. Missing parent directories are
created. `.gitignore` gets a single bounded section appended (never duplicated
on re-seed).

Callable from the ``qorlogic seed`` CLI subcommand and from any Python caller
that needs the same scaffold.
"""
from __future__ import annotations

from collections import namedtuple
from pathlib import Path

from qor import resources as _resources

SeedResult = namedtuple("SeedResult", ["created", "skipped"])
SeedTarget = namedtuple("SeedTarget", ["rel_path", "template", "mode"])

_GITIGNORE_MARKER = "# qor:seed -- do not edit between markers"
_GITIGNORE_END = "# qor:seed/end"
_GITIGNORE_BODY = ".qor/session/\n"

SEED_TARGETS: tuple[SeedTarget, ...] = (
    SeedTarget("docs/META_LEDGER.md", "META_LEDGER.md", "file"),
    SeedTarget("docs/SHADOW_GENOME.md", "SHADOW_GENOME.md", "file"),
    SeedTarget("docs/ARCHITECTURE_PLAN.md", "ARCHITECTURE_PLAN.md", "file"),
    SeedTarget("docs/CONCEPT.md", "CONCEPT.md", "file"),
    SeedTarget("docs/SYSTEM_STATE.md", "SYSTEM_STATE.md", "file"),
    SeedTarget(".agent/staging/.gitkeep", None, "gitkeep"),
    SeedTarget(".qor/gates/.gitkeep", None, "gitkeep"),
    SeedTarget(".qor/session/.gitkeep", None, "gitkeep"),
    SeedTarget(".gitignore", None, "gitignore_append"),
)


def _read_template(name: str) -> str:
    path = Path(str(_resources.asset("templates"))) / name
    return path.read_text(encoding="utf-8")


def _write_file_if_missing(dst: Path, content: str) -> bool:
    if dst.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")
    return True


def _write_gitkeep(dst: Path) -> bool:
    if dst.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("", encoding="utf-8")
    return True


def _append_gitignore_section(dst: Path) -> bool:
    existing = dst.read_text(encoding="utf-8") if dst.exists() else ""
    if _GITIGNORE_MARKER in existing:
        return False
    sep = "" if existing == "" or existing.endswith("\n") else "\n"
    block = f"{sep}{_GITIGNORE_MARKER}\n{_GITIGNORE_BODY}{_GITIGNORE_END}\n"
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("a", encoding="utf-8") as fh:
        fh.write(block)
    return True


def _apply_target(base: Path, target: SeedTarget) -> bool:
    dst = base / target.rel_path
    if target.mode == "file":
        return _write_file_if_missing(dst, _read_template(target.template))
    if target.mode == "gitkeep":
        return _write_gitkeep(dst)
    if target.mode == "gitignore_append":
        return _append_gitignore_section(dst)
    raise ValueError(f"unknown seed mode: {target.mode!r}")


def seed(base: Path, *, quiet: bool = False) -> SeedResult:
    """Scaffold the governance workspace under ``base``. Idempotent."""
    base.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    skipped: list[str] = []
    for target in SEED_TARGETS:
        wrote = _apply_target(base, target)
        (created if wrote else skipped).append(target.rel_path)
        if not quiet:
            action = "created" if wrote else "skipped"
            print(f"  {action}: {target.rel_path}")
    return SeedResult(created=created, skipped=skipped)
