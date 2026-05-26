"""Phase 105: shared helpers for dependency-admission tooling.

Pure functions, no I/O. Three parsers:
- parse_lockfile_entries: pip-compile --generate-hashes output -> [LockfileEntry]
- diff_lockfile_against_base: new + version-bumped entries vs a base
- parse_override_entries: META_LEDGER `**Dependency admission override**:` lines

Companion scripts: dependency_admission_lint.py, dep_admit_override_tracker.py.
Doctrine: qor/references/doctrine-dependency-admission.md.
"""
from __future__ import annotations

import dataclasses
import re
import tomllib
from datetime import datetime, timezone


@dataclasses.dataclass(frozen=True)
class LockfileEntry:
    name: str
    version: str
    hashes: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class Bump:
    name: str
    old_version: str | None
    new_version: str


@dataclasses.dataclass(frozen=True)
class OverrideEntry:
    package: str
    version: str
    entry_ts: datetime
    upload_age_days: int
    justification: str


class LockfileParseError(ValueError):
    """Raised when requirements-release.txt format cannot be parsed."""


_LOCKFILE_PIN_RE = re.compile(r"^([a-zA-Z0-9][a-zA-Z0-9._-]*)==([^\s\\]+)")
_LOCKFILE_HASH_RE = re.compile(r"--hash=(?P<value>\S+)")
_LEDGER_ENTRY_TS_RE = re.compile(r"^### Entry #\d+", re.MULTILINE)
_LEDGER_TS_RE = re.compile(r"^\*\*Timestamp\*\*:\s*([0-9T:Z.-]+)", re.MULTILINE)
_OVERRIDE_LINE_RE = re.compile(
    r"\*\*Dependency admission override\*\*:\s*"
    r"(?P<package>[a-zA-Z0-9][a-zA-Z0-9._-]*)@(?P<version>[^\s;]+);\s*"
    r"upload_age_days=(?P<age>\d+);\s*"
    r"justification=(?P<justification>[^\n]+)"
)


def parse_lockfile_entries(text: str) -> list[LockfileEntry]:
    """Parse pip-compile --generate-hashes output into LockfileEntry list."""
    entries: list[LockfileEntry] = []
    current_name: str | None = None
    current_version: str | None = None
    current_hashes: list[str] = []

    def flush():
        if current_name and current_version:
            entries.append(
                LockfileEntry(
                    name=current_name,
                    version=current_version,
                    hashes=tuple(current_hashes),
                )
            )

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        pin_m = _LOCKFILE_PIN_RE.match(stripped)
        if pin_m:
            flush()
            current_name = pin_m.group(1).lower()
            current_version = pin_m.group(2)
            current_hashes = []
            hash_m = _LOCKFILE_HASH_RE.search(stripped)
            if hash_m:
                _validate_hash(hash_m.group("value"))
                current_hashes.append(hash_m.group("value"))
            continue
        hash_m = _LOCKFILE_HASH_RE.search(stripped)
        if hash_m:
            _validate_hash(hash_m.group("value"))
            current_hashes.append(hash_m.group("value"))

    flush()
    return entries


def _validate_hash(value: str) -> None:
    if not value.startswith("sha256:"):
        raise LockfileParseError(f"hash {value!r} must use sha256: prefix")
    digest = value.split(":", 1)[1]
    if len(digest) != 64 or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise LockfileParseError(f"hash digest {digest!r} must be 64 hex chars")


def diff_lockfile_against_base(
    current: list[LockfileEntry], base: list[LockfileEntry]
) -> list[Bump]:
    """New + version-bumped entries vs base. Sorted by name. Removals not reported."""
    base_by_name = {e.name: e for e in base}
    bumps: list[Bump] = []
    for entry in current:
        prior = base_by_name.get(entry.name)
        if prior is None:
            bumps.append(Bump(name=entry.name, old_version=None, new_version=entry.version))
        elif prior.version != entry.version:
            bumps.append(
                Bump(name=entry.name, old_version=prior.version, new_version=entry.version)
            )
    return sorted(bumps, key=lambda b: b.name)


def parse_override_entries(ledger_text: str) -> list[OverrideEntry]:
    """Walk META_LEDGER for **Dependency admission override**: lines.

    Each override is paired with its containing entry's **Timestamp** (the IMPLEMENTATION
    entry timestamp). When an entry contains multiple override lines, all of them inherit
    that entry's timestamp.
    """
    overrides: list[OverrideEntry] = []
    entry_blocks = re.split(_LEDGER_ENTRY_TS_RE, ledger_text)
    # entry_blocks[0] is pre-first-entry preamble (no entry); skip.
    for block in entry_blocks[1:]:
        ts_m = _LEDGER_TS_RE.search(block)
        if not ts_m:
            continue
        ts_str = ts_m.group(1)
        try:
            entry_ts = _parse_iso_utc(ts_str)
        except ValueError:
            continue
        for ovr_m in _OVERRIDE_LINE_RE.finditer(block):
            overrides.append(
                OverrideEntry(
                    package=ovr_m.group("package"),
                    version=ovr_m.group("version"),
                    entry_ts=entry_ts,
                    upload_age_days=int(ovr_m.group("age")),
                    justification=ovr_m.group("justification").strip(),
                )
            )
    return overrides


_PYPROJECT_EXACT_PIN_RE = re.compile(
    r"^([a-zA-Z0-9][a-zA-Z0-9._-]*)\s*==\s*([0-9][^\s;,]*)\s*$"
)
_PYPROJECT_RANGE_PIN_RE = re.compile(
    r"^([a-zA-Z0-9][a-zA-Z0-9._-]*)\s*(?:>=|~=)\s*([0-9][^\s;,]*)"
)


def parse_pyproject_exact_pins(text: str) -> list[LockfileEntry]:
    """Extract `package==X.Y.Z` exact pins from pyproject [project].dependencies
    and [project.optional-dependencies].*. Range / unbounded forms skipped.

    Returned LockfileEntry instances carry hashes=() because pyproject deps are
    not hash-pinned at this layer (the lockfile layer carries hashes).
    """
    data = tomllib.loads(text)
    project = data.get("project") or {}
    deps_lists: list[list[str]] = []
    base = project.get("dependencies") or []
    if isinstance(base, list):
        deps_lists.append(base)
    for group in (project.get("optional-dependencies") or {}).values():
        if isinstance(group, list):
            deps_lists.append(group)
    pins: list[LockfileEntry] = []
    for deps in deps_lists:
        for entry in deps:
            m = _PYPROJECT_EXACT_PIN_RE.match(str(entry).strip())
            if m:
                pins.append(
                    LockfileEntry(
                        name=m.group(1).lower(),
                        version=m.group(2),
                        hashes=(),
                    )
                )
    return pins


def parse_pyproject_range_pins(text: str) -> list[LockfileEntry]:
    """Phase 107 D-107.3: extract lower-bound version from `>=` and `~=` range pins.

    Returns LockfileEntry instances carrying the lower-bound version as `version`
    (the earliest version pip could resolve to). `<`, `!=`, and unbounded
    specifiers are skipped because they don't carry a meaningful lower-bound for
    cooling-period attention. Combined specifiers (`>=1.0,<2.0`) match the
    `>=` portion only.

    Pairs with parse_pyproject_exact_pins (Phase 106) which handles `==`.
    The two parsers are orthogonal: a single entry hits at most one of them.
    """
    data = tomllib.loads(text)
    project = data.get("project") or {}
    deps_lists: list[list[str]] = []
    base = project.get("dependencies") or []
    if isinstance(base, list):
        deps_lists.append(base)
    for group in (project.get("optional-dependencies") or {}).values():
        if isinstance(group, list):
            deps_lists.append(group)
    pins: list[LockfileEntry] = []
    for deps in deps_lists:
        for entry in deps:
            text_e = str(entry).strip()
            # Skip if exact-pin form (parse_pyproject_exact_pins handles those)
            if _PYPROJECT_EXACT_PIN_RE.match(text_e):
                continue
            m = _PYPROJECT_RANGE_PIN_RE.match(text_e)
            if m:
                pins.append(
                    LockfileEntry(
                        name=m.group(1).lower(),
                        version=m.group(2),
                        hashes=(),
                    )
                )
    return pins


def _parse_iso_utc(value: str) -> datetime:
    """Parse ISO-8601 UTC timestamp; tolerate 'Z' suffix and fractional seconds."""
    normalized = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
