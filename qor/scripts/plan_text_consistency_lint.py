"""Phase 48 V2: detect prose-boundary precision drift across same-operation specs.

V2 changes vs V1:
- Identity-based grouping (default): same operation IDENTITY + 2+ distinct
  normalized = drift. Eliminates V1 false-positive class on multi-pytest CI
  command sections, multi-module python invocations, --apply-vs-check patterns.
- New `dep_name` operation kind: cross-checks projection-table Imports rows
  against `Cargo.toml [dependencies]` and `requirements{,-dev}.txt`. Catches
  the original COREFORGE V1 finding (dep named in plan but not declared).
- New `--strict` flag preserves V1 broad-rule for debugging.

V3 deferrals: --apply rewrite mode, type-annotation consistency,
pyproject.toml [project.dependencies] parsing.

Stdlib-only. CLI: python -m qor.scripts.plan_text_consistency_lint --check <path> [--strict] [--repo-root <path>]
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

OPERATION_KINDS = (
    "cargo_test",
    "cargo_build",
    "python_module",
    "python_script",
    "filesystem_path",
    "dep_name",
)

_FENCED_BLOCK = re.compile(r"```.*?```", re.DOTALL)
_CODE_SPAN = re.compile(r"`([^`\n]+)`")
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_PLACEHOLDER = re.compile(r"<[^`>]+>|\{[^`}]+\}|\.\.\.")
_PATH_LIKE = re.compile(
    r"^[A-Za-z0-9_./\-]+\.(?:md|py|json|yaml|yml|toml|rs|ts|tsx|jsonl|txt)$"
)
_DIR_LIKE = re.compile(r"^[A-Za-z0-9_./\-]+/$")
_CARGO_TEST = re.compile(r"^cargo\s+test(\s.*)?$")
_CARGO_BUILD = re.compile(r"^cargo\s+build(\s.*)?$")
_CARGO_VALUE_FLAGS = frozenset({
    "--features", "-F", "--target", "--manifest-path", "--package", "-p",
    "--bin", "--example", "--test", "--bench", "--lib", "--profile",
    "--config", "--color", "--out-dir", "--jobs", "-j",
})
_PY_MODULE = re.compile(r"^python\d?\s+-m\s+([A-Za-z0-9_.]+)(\s.*)?$")
_PY_SCRIPT = re.compile(r"^python\d?\s+([A-Za-z0-9_./\-]+\.py)(\s.*)?$")
_IMPORTS_ROW = re.compile(
    r"^\|[^|]*Imports?[^|]*\|.*$",
    re.IGNORECASE | re.MULTILINE,
)
_DEP_TOKEN = re.compile(r"\b([a-z][a-z0-9_-]+)\b")
_CARGO_DEP_LINE = re.compile(
    r'^\s*([a-z][a-z0-9_-]+)\s*=', re.MULTILINE | re.IGNORECASE,
)
_CARGO_SECTION = re.compile(r"^\[([a-zA-Z0-9_.-]+)\]\s*$", re.MULTILINE)
_PY_DEP_LINE = re.compile(r"^\s*([a-zA-Z][a-zA-Z0-9_-]*)", re.MULTILINE)


@dataclass(frozen=True)
class Site:
    line: int
    section: str
    raw_text: str
    normalized: str


@dataclass(frozen=True)
class DriftFinding:
    operation_kind: str
    sites: tuple[Site, ...]
    resolution_hint: str = "pick canonical site, edit other(s) to match"


def _is_placeholder(text: str) -> bool:
    return bool(_PLACEHOLDER.search(text))


def _split_cmd(text: str, value_flags: frozenset[str] = frozenset()) -> tuple[str, list[str], list[str]]:
    """Split into (head, flags, positional). value_flags names flags that
    consume the following token as a value rather than treating it as
    positional. The `--` separator (POSIX end-of-options) terminates parsing."""
    parts = text.strip().split()
    if not parts:
        return "", [], []
    head: list[str] = [parts[0]]
    flags: list[str] = []
    positional: list[str] = []
    rest = parts[1:]
    if rest and not rest[0].startswith("-"):
        head.append(rest[0])
        rest = rest[1:]
    i = 0
    while i < len(rest):
        token = rest[i]
        if token == "--":
            break
        if token.startswith("-"):
            if token in value_flags and i + 1 < len(rest):
                flags.append(token + "=" + rest[i + 1])
                i += 2
                continue
            if "=" in token:
                flags.append(token)
            else:
                flags.append(token)
            i += 1
        else:
            positional.append(token)
            i += 1
    return " ".join(head), flags, positional


def _normalize_cmd(text: str, value_flags: frozenset[str] = frozenset()) -> str:
    head, flags, positional = _split_cmd(text, value_flags=value_flags)
    out = head
    if flags:
        out += " " + " ".join(sorted(flags))
    if positional:
        out += " " + " ".join(positional)
    return out


def _normalize_path(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned.replace("\\", "/")


def _classify(text: str) -> tuple[str, str] | None:
    body = text.strip()
    if _CARGO_TEST.match(body):
        return ("cargo_test", _normalize_cmd(body, _CARGO_VALUE_FLAGS))
    if _CARGO_BUILD.match(body):
        return ("cargo_build", _normalize_cmd(body, _CARGO_VALUE_FLAGS))
    if _PY_MODULE.match(body):
        return ("python_module", _normalize_cmd(body))
    if _PY_SCRIPT.match(body):
        return ("python_script", _normalize_cmd(body))
    if _PATH_LIKE.match(body) or _DIR_LIKE.match(body):
        return ("filesystem_path", _normalize_path(body))
    return None


def _identity_for(kind: str, site: Site) -> tuple:
    """V2 identity key per operation kind. Sites in the same identity group
    are 'the same operation' and divergent normalized values represent drift."""
    if kind in ("cargo_test", "cargo_build"):
        _, _, positional = _split_cmd(site.raw_text, _CARGO_VALUE_FLAGS)
        subcommand = "test" if kind == "cargo_test" else "build"
        return (kind, subcommand, tuple(sorted(positional)))
    if kind == "python_module":
        m = _PY_MODULE.match(site.raw_text.strip())
        module = m.group(1) if m else ""
        args_raw = m.group(2).strip() if m and m.group(2) else ""
        args_parts = args_raw.split() if args_raw else []
        first_arg = args_parts[0] if args_parts else ""
        return (kind, module, first_arg)
    if kind == "python_script":
        m = _PY_SCRIPT.match(site.raw_text.strip())
        script = m.group(1) if m else ""
        args_raw = m.group(2).strip() if m and m.group(2) else ""
        args_parts = args_raw.split() if args_raw else []
        first_arg = args_parts[0] if args_parts else ""
        return (kind, script, first_arg)
    if kind == "filesystem_path":
        return (kind, site.normalized)
    return (kind, site.normalized)


def _strip_fenced_blocks(text: str) -> str:
    return _FENCED_BLOCK.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def _heading_index(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for m in _HEADING.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        out.append((line, m.group(2)))
    return out


def _section_for(line: int, headings: list[tuple[int, str]]) -> str:
    section = ""
    for hline, htext in headings:
        if hline <= line:
            section = htext
        else:
            break
    return section


def _extract_sites(text: str) -> list[tuple[Site, str]]:
    headings = _heading_index(text)
    stripped = _strip_fenced_blocks(text)
    sites: list[tuple[Site, str]] = []
    for m in _CODE_SPAN.finditer(stripped):
        raw = m.group(1)
        if _is_placeholder(raw):
            continue
        cls = _classify(raw)
        if cls is None:
            continue
        kind, normalized = cls
        line = stripped.count("\n", 0, m.start()) + 1
        section = _section_for(line, headings)
        sites.append((Site(line=line, section=section, raw_text=raw, normalized=normalized), kind))
    return sites


def _detect_drift(sites: list[tuple[Site, str]], strict: bool = False) -> list[DriftFinding]:
    by_kind: dict[str, list[Site]] = {k: [] for k in OPERATION_KINDS}
    for site, kind in sites:
        by_kind[kind].append(site)
    findings: list[DriftFinding] = []
    for kind, items in by_kind.items():
        if len(items) < 2:
            continue
        if kind == "filesystem_path":
            by_normalized: dict[str, list[Site]] = {}
            for s in items:
                by_normalized.setdefault(s.normalized, []).append(s)
            for normalized, group in by_normalized.items():
                if len({s.raw_text for s in group}) >= 2:
                    findings.append(DriftFinding(operation_kind=kind, sites=tuple(group)))
            continue
        if strict:
            distinct = {s.normalized for s in items}
            if len(distinct) >= 2:
                findings.append(DriftFinding(operation_kind=kind, sites=tuple(items)))
        else:
            by_identity: dict[tuple, list[Site]] = {}
            for s in items:
                identity = _identity_for(kind, s)
                by_identity.setdefault(identity, []).append(s)
            for identity, group in by_identity.items():
                if len({s.normalized for s in group}) >= 2:
                    findings.append(DriftFinding(operation_kind=kind, sites=tuple(group)))
    return findings


def _extract_dep_candidates(plan_text: str) -> list[tuple[int, str]]:
    """Walk plan markdown for projection-table rows where one column is labeled
    'Imports'; emit each token from that column across all data rows under the
    header. Returns (line, dep_name) tuples."""
    candidates: list[tuple[int, str]] = []
    lines = plan_text.splitlines()
    imports_col: int | None = None
    in_table = False
    for idx, raw_line in enumerate(lines):
        stripped = raw_line.rstrip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            in_table = False
            imports_col = None
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            in_table = imports_col is not None
            continue
        if imports_col is None:
            for col_idx, c in enumerate(cells):
                if "imports" in c.lower():
                    imports_col = col_idx
                    break
            continue
        if not in_table:
            continue
        if imports_col >= len(cells):
            continue
        cell = cells[imports_col]
        for token in _DEP_TOKEN.findall(cell):
            if token in {"imports", "import", "use", "uses", "from", "and", "the"}:
                continue
            if token.startswith("qor") or token.startswith("std"):
                continue
            candidates.append((idx + 1, token))
    return candidates


def _cargo_dep_names(repo_root: Path) -> set[str]:
    path = repo_root / "Cargo.toml"
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    deps: set[str] = set()
    sections = list(_CARGO_SECTION.finditer(text))
    for i, sec in enumerate(sections):
        name = sec.group(1).lower()
        if not (name == "dependencies" or name.endswith(".dependencies") or name == "dev-dependencies" or name.endswith(".dev-dependencies")):
            continue
        start = sec.end()
        end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
        body = text[start:end]
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = _CARGO_DEP_LINE.match(line)
            if m:
                deps.add(m.group(1).lower())
    return deps


def _python_dep_names(repo_root: Path) -> set[str]:
    deps: set[str] = set()
    for fname in ("requirements.txt", "requirements-dev.txt"):
        path = repo_root / fname
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                continue
            m = _PY_DEP_LINE.match(stripped)
            if m:
                deps.add(m.group(1).lower())
    return deps


def _detect_dep_name_drift(plan_text: str, repo_root: Path | None) -> list[DriftFinding]:
    if repo_root is None:
        return []
    candidates = _extract_dep_candidates(plan_text)
    if not candidates:
        return []
    cargo_deps = _cargo_dep_names(repo_root)
    python_deps = _python_dep_names(repo_root)
    declared = cargo_deps | python_deps
    if not declared:
        return []
    findings: list[DriftFinding] = []
    by_dep: dict[str, list[Site]] = {}
    for line, dep in candidates:
        if dep.lower() in declared:
            continue
        site = Site(line=line, section="Imports", raw_text=dep, normalized=dep.lower())
        by_dep.setdefault(dep.lower(), []).append(site)
    for dep, sites in by_dep.items():
        findings.append(DriftFinding(
            operation_kind="dep_name",
            sites=tuple(sites),
            resolution_hint=f"dep '{dep}' named in plan but not declared in Cargo.toml/requirements*.txt",
        ))
    return findings


def lint(
    plan_text: str,
    strict: bool = False,
    repo_root: Path | None = None,
) -> list[DriftFinding]:
    sites = _extract_sites(plan_text)
    findings = _detect_drift(sites, strict=strict)
    findings.extend(_detect_dep_name_drift(plan_text, repo_root))
    return findings


def _format_finding(finding: DriftFinding) -> str:
    lines = [f"  operation_kind={finding.operation_kind}"]
    for s in finding.sites:
        section = s.section or "(no heading)"
        lines.append(f"    site at line {s.line} in section: {section}")
        lines.append(f"      `{s.raw_text}`")
    lines.append(f"    resolution: {finding.resolution_hint}")
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="plan_text_consistency_lint")
    parser.add_argument("--check", required=True, help="path to plan markdown file")
    parser.add_argument(
        "--strict", action="store_true",
        help="V1 broad-rule (same kind + 2+ distinct normalized = drift)",
    )
    parser.add_argument(
        "--repo-root", default=None,
        help="repo root for dep_name cross-check (Cargo.toml / requirements*.txt)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    path = Path(args.check)
    if not path.exists():
        print(f"plan_text_consistency_lint: no such file: {path}", file=sys.stderr)
        return 2
    repo_root = Path(args.repo_root) if args.repo_root else path.parent.parent
    findings = lint(path.read_text(encoding="utf-8"), strict=args.strict, repo_root=repo_root)
    if not findings:
        return 0
    print("plan_text_consistency_lint: drift detected", file=sys.stderr)
    for f in findings:
        print(_format_finding(f), file=sys.stderr)
    print(f"exit: 1 ({len(findings)} drift finding(s))", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
