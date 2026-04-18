"""Documentation integrity checks.

Enforces the documentation-integrity doctrine at /qor-substantiate time.
All parsing uses yaml.safe_load (SG-Phase24-B); every check raises ValueError
on violation (changelog_stamp idiom; no return codes).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml

import shadow_process

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
        ("docs/architecture.md", "architecture.md"),
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


def check_topology(tier: str, repo_root: str) -> None:
    if tier not in _TIERS:
        raise ValueError(
            f"Unknown doc_tier: {tier!r}. Expected one of {_TIERS}."
        )
    root = Path(repo_root)
    for rel_path, label in _TIER_REQUIREMENTS[tier]:
        if not (root / rel_path).exists():
            raise ValueError(
                f"Tier {tier!r} requires {label} at {rel_path!r}; not found."
            )


def check_glossary(
    glossary_path: str,
    declared_terms: Iterable[str],
    repo_root: str | None = None,
) -> None:
    entries = parse_glossary(glossary_path)
    by_term = {e.term: e for e in entries}
    for term in declared_terms:
        if term not in by_term:
            raise ValueError(
                f"Declared term {term!r} has no entry in {glossary_path}."
            )
        entry = by_term[term]
        if not entry.definition.strip():
            raise ValueError(
                f"Glossary entry {term!r} has empty definition."
            )
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
    for e in entries:
        if repo_root is not None:
            home_path = Path(repo_root) / e.home
            if not home_path.exists():
                raise ValueError(
                    f"Orphan home: {e.term!r} -> {e.home!r} does not exist."
                )
        if e.referenced_by:
            continue
        if e.introduced_in_plan == current_session_plan_tag:
            continue
        raise ValueError(
            f"Orphan concept: {e.term!r} has no referenced_by and was not "
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
                raise ValueError(
                    f"Glossary entry missing {required!r}: {data!r}"
                )
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
            )
        )
    return entries


def render_drift_section(plan: dict, repo_root: str) -> str:
    """Return a '## Documentation Drift' markdown section, or '' if clean.

    Non-blocking advisory for /qor-audit. Reports the same violations that
    /qor-substantiate would hard-block on, but as warnings -- so operators
    can fix drift in one pass before seal.
    """
    tier = plan.get("doc_tier", "legacy")
    if tier == "legacy":
        return ""
    issues: list[str] = []
    try:
        check_topology(tier, repo_root)
    except ValueError as exc:
        issues.append(f"- Topology: {exc}")
    glossary_path = str(Path(repo_root) / "qor" / "references" / "glossary.md")
    declared = [t["term"] for t in plan.get("terms", [])]
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


def run_all_checks_from_plan(plan: dict, repo_root: str) -> None:
    """Run topology + glossary + orphans against the declared plan state.

    Called by /qor-substantiate Step 4.7. Raises ValueError on first violation
    (changelog_stamp idiom; no return codes, no silent retry). Legacy tier
    bypasses all checks.
    """
    tier = plan.get("doc_tier", "legacy")
    if tier == "legacy":
        return
    check_topology(tier, repo_root)
    glossary_path = str(Path(repo_root) / "qor" / "references" / "glossary.md")
    declared = [t["term"] for t in plan.get("terms", [])]
    check_glossary(glossary_path, declared_terms=declared, repo_root=repo_root)
    plan_slug = plan.get("plan_slug", "")
    check_orphans(
        glossary_path,
        current_session_plan_tag=plan_slug,
        repo_root=repo_root,
    )


def emit_legacy_tier_event(
    session_id: str,
    rationale: str,
    log_path: Path | None = None,
) -> str:
    """Append a severity-2 degradation event when a plan declares doc_tier:legacy.

    The event_type 'degradation' is reused from the existing shadow_event schema
    (legacy tier is a standards degradation). details.kind distinguishes it
    from other degradations.
    """
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
