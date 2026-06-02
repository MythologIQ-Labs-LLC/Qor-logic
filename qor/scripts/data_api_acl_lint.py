"""Data-API access-control lint (Phase 121; GH #177).

Static SQL scan over a target repo's migration files. Flags the deterministic,
high-confidence access-control defects that survive a privileged-principal test
(service_role / SECURITY DEFINER) but break for the runtime caller
(authenticated / anon):

  missing-grant   -- a table in an API-exposed schema with no GRANT to a
                     non-owner runtime role, no REVOKE marking it
                     service-role-only, and no `-- qor:service-role-only` escape.
  definer-view    -- a view in an API schema created without
                     `security_invoker = true` (Postgres default is
                     definer-rights, bypassing base-table RLS), no
                     `-- qor:definer-view-intended` escape.
  security-definer-fn -- advisory: each SECURITY DEFINER function (reviewed,
                     not blocked).

Not a live database probe. De-complected: pure `parse_*` helpers (str -> list)
feed `analyze` (policy), which feeds `main` (process exit).
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_API_SCHEMAS = ("public",)
MIGRATION_GLOBS = (
    "supabase/migrations/*.sql",
    "migrations/*.sql",
    "db/migrations/*.sql",
    "db/**/*.sql",
)
KNOWN_FINDING_KINDS = ("missing-grant", "definer-view", "security-definer-fn")
BLOCKING_KINDS = ("missing-grant", "definer-view")
RUNTIME_ROLES = ("authenticated", "anon")

_TABLE_RE = re.compile(
    r"create\s+table\s+(?:if\s+not\s+exists\s+)?([\w.\"]+)", re.IGNORECASE
)
_GRANT_RE = re.compile(
    r"grant\s+[\w,\s]+?\s+on\s+(?:table\s+)?([\w.\"]+)\s+to\s+([\w\"]+)",
    re.IGNORECASE,
)
_REVOKE_RE = re.compile(
    r"revoke\s+[\w,\s]+?\s+on\s+(?:table\s+)?([\w.\"]+)\s+from\s+([\w\"]+)",
    re.IGNORECASE,
)
_VIEW_RE = re.compile(
    r"create\s+(?:or\s+replace\s+)?(?:materialized\s+)?view\s+"
    r"(?:if\s+not\s+exists\s+)?([\w.\"]+)(.*?)\bas\b",
    re.IGNORECASE | re.DOTALL,
)
_FUNC_RE = re.compile(
    r"create\s+(?:or\s+replace\s+)?function\s+([\w.\"]+)", re.IGNORECASE
)


@dataclass(frozen=True)
class AclFinding:
    kind: str
    object_name: str
    file: str
    detail: str


@dataclass(frozen=True)
class AclResult:
    findings: tuple[AclFinding, ...]
    skipped: bool
    skip_reason: str


def _norm(name: str, api_schemas: tuple[str, ...]) -> tuple[str, str]:
    """Return (schema, bare_name) lowercased, quotes stripped; default schema
    is the first API schema when unqualified."""
    cleaned = name.replace('"', "").lower()
    if "." in cleaned:
        schema, _, bare = cleaned.partition(".")
        return schema, bare
    return api_schemas[0], cleaned


def find_sql_migrations(base: Path) -> list[Path]:
    found: set[Path] = set()
    for pattern in MIGRATION_GLOBS:
        found.update(p for p in base.glob(pattern) if p.is_file())
    return sorted(found)


def parse_created_tables(sql: str) -> list[str]:
    return [m.group(1) for m in _TABLE_RE.finditer(sql)]


def parse_grants(sql: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _GRANT_RE.finditer(sql)]


def parse_revokes(sql: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _REVOKE_RE.finditer(sql)]


def parse_views(sql: str) -> list[tuple[str, bool]]:
    out: list[tuple[str, bool]] = []
    for m in _VIEW_RE.finditer(sql):
        options = m.group(2)
        invoker = bool(re.search(r"security_invoker\s*=\s*(?:true|on)", options, re.IGNORECASE))
        out.append((m.group(1), invoker))
    return out


def parse_definer_functions(sql: str) -> list[str]:
    starts = [(m.start(), m.group(1)) for m in _FUNC_RE.finditer(sql)]
    out: list[str] = []
    for i, (pos, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(sql)
        if re.search(r"security\s+definer", sql[pos:end], re.IGNORECASE):
            out.append(name)
    return out


def _marker_near(sql: str, obj_start: int, marker: str) -> bool:
    """True when `marker` appears on the object's line or the 3 lines above it."""
    head = sql[:obj_start].splitlines()
    window = head[-3:] if len(head) >= 3 else head
    return any(marker in line for line in window)


def _table_starts(sql: str) -> dict[str, int]:
    return {m.group(1): m.start() for m in _TABLE_RE.finditer(sql)}


def _view_starts(sql: str) -> dict[str, int]:
    return {m.group(1): m.start() for m in _VIEW_RE.finditer(sql)}


def analyze(base: Path, api_schemas: tuple[str, ...] = DEFAULT_API_SCHEMAS) -> AclResult:
    migrations = find_sql_migrations(base)
    if not migrations:
        return AclResult((), True, "no SQL migrations found")

    sources = [(p, p.read_text(encoding="utf-8")) for p in migrations]
    corpus = "\n".join(sql for _, sql in sources)

    granted = {_norm(o, api_schemas) for o, role in parse_grants(corpus)
               if role.replace('"', "").lower() in RUNTIME_ROLES}
    revoked = {_norm(o, api_schemas) for o, role in parse_revokes(corpus)
               if role.replace('"', "").lower() in RUNTIME_ROLES}

    findings: list[AclFinding] = []
    for path, sql in sources:
        rel = path.as_posix()
        starts = _table_starts(sql)
        for raw in parse_created_tables(sql):
            schema, bare = _norm(raw, api_schemas)
            if schema not in api_schemas:
                continue
            key = (schema, bare)
            if key in granted or key in revoked:
                continue
            if _marker_near(sql, starts.get(raw, 0), "qor:service-role-only"):
                continue
            findings.append(AclFinding(
                "missing-grant", f"{schema}.{bare}", rel,
                "table in API schema has no GRANT to authenticated/anon and "
                "is not marked service-role-only",
            ))
        vstarts = _view_starts(sql)
        for raw, invoker in parse_views(sql):
            schema, bare = _norm(raw, api_schemas)
            if schema not in api_schemas or invoker:
                continue
            if _marker_near(sql, vstarts.get(raw, 0), "qor:definer-view-intended"):
                continue
            findings.append(AclFinding(
                "definer-view", f"{schema}.{bare}", rel,
                "view created without security_invoker = true (bypasses base-table RLS)",
            ))
        for raw in parse_definer_functions(sql):
            schema, bare = _norm(raw, api_schemas)
            findings.append(AclFinding(
                "security-definer-fn", f"{schema}.{bare}", rel,
                "SECURITY DEFINER function -- review that it does not bypass RLS",
            ))

    return AclResult(tuple(findings), False, "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="data_api_acl_lint")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--api-schemas", default="public")
    args = parser.parse_args(argv)

    schemas = tuple(s.strip().lower() for s in args.api_schemas.split(",") if s.strip())
    result = analyze(Path(args.repo_root), schemas or DEFAULT_API_SCHEMAS)

    if result.skipped:
        print(f"SKIP: {result.skip_reason} (Phase 75 disclosed-skip)")
        return 0

    for f in result.findings:
        tag = "BLOCK" if f.kind in BLOCKING_KINDS else "WARN"
        print(f"[{tag}] {f.kind} {f.object_name} ({f.file}): {f.detail}")

    blocking = [f for f in result.findings if f.kind in BLOCKING_KINDS]
    if blocking:
        print(f"data_api_acl_lint: {len(blocking)} blocking finding(s)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
