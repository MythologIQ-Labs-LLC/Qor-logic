"""Documentation integrity checks.

Enforces the documentation-integrity doctrine at /qor-substantiate time.
All parsing uses yaml.safe_load; every check raises ValueError on violation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml

from qor.scripts import shadow_process
from qor.scripts.governance_paths import resolve_architecture_authority

_TIERS = ("minimal", "standard", "system", "legacy")
_TIER_REQUIREMENTS: dict[str, tuple[tuple[str, str], ...]] = {
    "minimal": (("README.md", "README.md"),),
    "standard": (
        ("README.md", "README.md"),
        ("qor/references/glossary.md", "glossary"),
    ),
    "system": (
        ("README.md", "README.md"),
        ("qor/references/glossary.md", "glossary"),
        ("docs/lifecycle.md", "lifecycle.md"),
        ("docs/operations.md", "operations.md"),
        ("docs/policies.md", "policies.md"),
    ),
    "legacy": (),
}


@dataclass
class Entry:
    """A canonical glossary entry. Represents both a term and a concept home."""

    term: str
    definition: str
    home: str
    aliases: list[str] = field(default_factory=list)
    referenced_by: list[str] = field(default_factory=list)
    introduced_in_plan: str | None = None
    scope_exclude: list[str] = field(default_factory=list)


def check_topology(tier: str, repo_root: str) -> None:
    if tier not in _TIERS:
        raise ValueError(f"Unknown doc_tier: {tier!r}. Expected one of {_TIERS}.")
    root = Path(repo_root)
    for rel_path, label in _TIER_REQUIREMENTS[tier]:
        if not (root / rel_path).exists():
            raise ValueError(
                f"Tier {tier!r} requires {label} at {rel_path!r}; not found."
            )
    if tier == "system":
        try:
            resolve_architecture_authority(root)
        except ValueError as exc:
            raise ValueError(f"Tier 'system' requires one architecture authority: {exc}") from exc


def check_glossary(
    glossary_path: str,
    declared_terms: Iterable[str],
    repo_root: str | None = None,
) -> None:
    entries = parse_glossary(glossary_path)
    by_term = {entry.term: entry for entry in entries}
    for term in declared_terms:
        if term not in by_term:
            raise ValueError(f"Declared term {term!r} has no entry in {glossary_path}.")
        entry = by_term[term]
        if not entry.definition.strip():
            raise ValueError(f"Glossary entry {term!r} has empty definition.")
        if repo_root is not None:
            home_path = Path(repo_root) / entry.home
            if not home_path.exists():
                raise ValueError(
                    f"Glossary entry {term!r} home {entry.home!r} does not resolve."
                )


def check_orphans(
    glossary_path: str,
    current_session_plan_tag: str,
    repo_root: str | None = None,
) -> None:
    entries = parse_glossary(glossary_path)
    for entry in entries:
        if repo_root is not None:
            home_path = Path(repo_root) / entry.home
            if not home_path.exists():
                raise ValueError(
                    f"Orphan home: {entry.term!r} -> {entry.home!r} does not exist."
                )
        if entry.referenced_by:
            continue
        if entry.introduced_in_plan == current_session_plan_tag:
            continue
        raise ValueError(
            f"Orphan concept: {entry.term!r} has no referenced_by and was not "
            f"introduced in current plan ({current_session_plan_tag!r})."
        )


_FENCE_PATTERN = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)


def parse_glossary(glossary_path: str) -> list[Entry]:
    text = Path(glossary_path).read_text(encoding="utf-8")
    entries: list[Entry] = []
    seen: set[str] = set()
    for match in _FENCE_PATTERN.finditer(text):
        block = match.group(1)
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as exc:
            raise ValueError(f"Malformed YAML in glossary entry: {exc}") from exc
        if data is None:
            continue
        if not isinstance(data, dict):
            raise ValueError(
                f"Glossary entry must be a mapping; got {type(data).__name__}."
            )
        for required in ("term", "definition", "home"):
            if required not in data:
                raise ValueError(f"Glossary entry missing {required!r}: {data!r}")
        term = str(data["term"])
        if term in seen:
            raise ValueError(f"duplicate term in glossary: {term!r}")
        seen.add(term)
        definition = data["definition"]
        entries.append(
            Entry(
                term=term,
                definition="" if definition is None else str(definition),
                home=str(data["home"]),
                aliases=list(data.get("aliases") or []),
                referenced_by=list(data.get("referenced_by") or []),
                introduced_in_plan=data.get("introduced_in_plan"),
                scope_exclude=list(data.get("scope_exclude") or []),
            )
        )
    return entries


def render_drift_section(plan: dict, repo_root: str) -> str:
    """Return a Documentation Drift section, or an empty string if clean."""
    tier = plan.get("doc_tier", "legacy")
    if tier == "legacy":
        return ""
    issues: list[str] = []
    try:
        check_topology(tier, repo_root)
    except ValueError as exc:
        issues.append(f"- Topology: {exc}")
    glossary_path = str(Path(repo_root) / "qor" / "references" / "glossary.md")
    declared = [term["term"] for term in plan.get("terms", [])]
    try:
        check_glossary(glossary_path, declared_terms=declared, repo_root=repo_root)
    except (ValueError, FileNotFoundError) as exc:
        issues.append(f"- Glossary: {exc}")
    try:
        check_orphans(
            glossary_path,
            current_session_plan_tag=plan.get("plan_slug", ""),
            repo_root=repo_root,
        )
    except (ValueError, FileNotFoundError) as exc:
        issues.append(f"- Orphan: {exc}")
    if not issues:
        return ""
    return (
        "## Documentation Drift\n\n"
        "Non-VETO advisory. These issues would hard-block at /qor-substantiate "
        "per `qor/references/doctrine-documentation-integrity.md`. Governor can "
        "fix in a follow-on amendment or accept the block at seal time.\n\n"
        + "\n".join(issues)
        + "\n"
    )


def run_all_checks_from_plan(plan: dict, repo_root: str, strict: bool = False) -> None:
    """Run topology, glossary, and orphan checks against declared plan state."""
    tier = plan.get("doc_tier", "legacy")
    if tier == "legacy":
        return
    check_topology(tier, repo_root)
    glossary_path = str(Path(repo_root) / "qor" / "references" / "glossary.md")
    declared = [term["term"] for term in plan.get("terms", [])]
    check_glossary(glossary_path, declared_terms=declared, repo_root=repo_root)
    check_orphans(
        glossary_path,
        current_session_plan_tag=plan.get("plan_slug", ""),
        repo_root=repo_root,
    )
    if strict:
        from qor.scripts import doc_integrity_strict as dis

        dis.check_term_drift(glossary_path, repo_root, strict=True)
        dis.check_cross_doc_conflicts(glossary_path, repo_root, strict=True)


def emit_legacy_tier_event(
    session_id: str,
    rationale: str,
    log_path: Path | None = None,
) -> str:
    """Append a severity-2 degradation event when a plan declares legacy tier."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    event = {
        "ts": now,
        "skill": "qor-plan",
        "session_id": session_id,
        "event_type": "degradation",
        "severity": 2,
        "details": {"kind": "doc_tier_legacy_declared", "rationale": rationale},
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }
    if log_path is not None:
        return shadow_process.append_event(event, log_path=log_path)
    return shadow_process.append_event(event, attribution="LOCAL")
