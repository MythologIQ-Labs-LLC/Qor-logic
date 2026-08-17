"""Evidence-statement grammar and citation scanning for plan lints (Phase 225).

Extracted from ``plan_grep_lint`` so the grammar (what a statement IS, and how
it resolves against a revision) lives apart from the policy (what a plan owes).
``plan_grep_lint`` imports from here; nothing here imports back.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

# --- Citation-drift enforcement (Phase 125; GH #152 / SG-CitationDrift-A P1) ---
# A grep-evidence statement: a `grep` invocation completed with `-> <observed text>`.
_EVIDENCE_RE = re.compile(r"grep\b.*->")
# Sealed-infrastructure citation kinds (high-confidence, low false-positive).
_GIT_SHOW_RE = re.compile(r"git show\s+\S+:\S+")
_MIGRATION_RE = re.compile(r"\b\d{8,}[_-][\w-]+\.sql\b")
#: Shared extension alternation: both path regexes below derive from it, so the
#: demanded set and the working-tree fallback can never disagree on extensions.
#: Documentation surfaces (md, json, toml, yml, yaml) are demandable like code
#: surfaces (Phase 225; GH #336 -- markdown infrastructure is what Qor plans
#: cite most, and it could never enter a demand set before).
#: Ordered longest-prefix-first (tsx before ts, json before js): the working-tree
#: fallback has no trailing anchor to force backtracking, so `f.tsx` would
#: otherwise capture as `f.ts`.
_PATH_EXT = r"py|tsx|ts|sql|rs|go|json|js|md|toml|yml|yaml"
_FILE_LINE_RE = re.compile(r"\b[\w./-]+\.(?:" + _PATH_EXT + r"):\d+\b")
# The check runs ONLY inside these regions so plans that don't use the
# Locked-Decision discipline produce zero findings (no over-flag).
_LD_HEADING_RE = re.compile(r"^#+\s.*(locked decision|citation inventory)", re.IGNORECASE)
_ANY_HEADING_RE = re.compile(r"^#+\s")


# --- Evidence-statement parsing and resolution (Phase 223; GH #330) ---
# The predicate above checks that a statement EXISTS. It reads neither the path,
# the line, nor the observed text, so a citation whose line does not hold its
# quoted content passes (ledger #565). These parse a statement into a value that
# can be resolved against the revision it names.

#: `[git show <ref>:]<path> | grep ... -> <NN>:<observed>`. The `NN:` observation
#: is required: a statement without one satisfies `_EVIDENCE_RE` and carries
#: nothing a truth check can resolve, so it is deliberately not parsed.
_EVIDENCE_STMT_RE = re.compile(
    r"(?:git\s+show\s+(?P<ref>\S+):(?P<gitpath>\S+)\s*\|\s*)?"
    r"grep\b[^\n]*?->\s*(?P<line>\d+):(?P<observed>[^\n]*)"
)
#: Fallback path capture for the working-tree form, which names its file inside
#: the grep invocation rather than before a pipe.
_WT_PATH_RE = re.compile(r"([\w./-]+\.(?:" + _PATH_EXT + r"))")


@dataclass(frozen=True)
class EvidenceStatement:
    """One grep-evidence statement, parsed into something resolvable.

    ``ref`` is None for the working-tree form. ``observed`` is the text right of
    the ``NN:`` prefix, unstripped -- comparison strips both sides so indentation
    does not fail a true citation.
    """

    ref: str | None
    path: str
    line: int
    observed: str


def parse_evidence_statements(block: str) -> list[EvidenceStatement]:
    """Parse every resolvable evidence statement in ``block``, in order.

    Backticks are removed first: they are markdown span delimiters, not
    statement content. Without this, the two-span styling (observation in its
    own span) never matches, and the one-span styling captures its closing
    delimiter into ``observed`` (Phase 225; GH #336).
    """
    out: list[EvidenceStatement] = []
    for match in _EVIDENCE_STMT_RE.finditer(block.replace("`", "")):
        path = match.group("gitpath")
        if path is None:
            candidates = _WT_PATH_RE.findall(match.group(0))
            if not candidates:
                continue
            path = candidates[0]
        out.append(EvidenceStatement(
            ref=match.group("ref"), path=path,
            line=int(match.group("line")), observed=match.group("observed"),
        ))
    return out


def resolve_line(stmt: EvidenceStatement, repo_root: Path | None = None) -> str | None:
    """Return the cited line's text, or None when it cannot be resolved.

    None is a distinct outcome from a mismatch: an environment that cannot answer
    is not an answer that is wrong, which is why the caller gives it its own
    finding kind.
    """
    root = repo_root or Path.cwd()
    if stmt.ref:
        completed = subprocess.run(
            ["git", "show", f"{stmt.ref}:{stmt.path}"],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
        )
        if completed.returncode != 0:
            return None
        body = completed.stdout
    else:
        target = root / stmt.path
        if not target.is_file():
            return None
        body = target.read_text(encoding="utf-8", errors="replace")

    lines = body.splitlines()
    if not 1 <= stmt.line <= len(lines):
        return None
    return lines[stmt.line - 1]


def reproduces(stmt: EvidenceStatement, repo_root: Path | None = None) -> bool:
    """True iff the cited line holds the quoted text, compared stripped."""
    actual = resolve_line(stmt, repo_root)
    return actual is not None and actual.strip() == stmt.observed.strip()


def _ld_blocks(text: str) -> list[tuple[int, str]]:
    """Return (start_line, block_text) for each Locked-Decision / Citation-Inventory
    region: from its heading up to (not including) the next heading."""
    lines = text.splitlines()
    blocks: list[tuple[int, str]] = []
    i = 0
    while i < len(lines):
        if _LD_HEADING_RE.match(lines[i]):
            start = i
            j = i + 1
            while j < len(lines) and not _ANY_HEADING_RE.match(lines[j]):
                j += 1
            blocks.append((start + 1, "\n".join(lines[start:j])))
            i = j
        else:
            i += 1
    return blocks


def _sealed_citations(block: str) -> list[str]:
    found: list[str] = []
    for rx in (_GIT_SHOW_RE, _MIGRATION_RE, _FILE_LINE_RE):
        found.extend(m.group(0) for m in rx.finditer(block))
    return found


def _file_line_citations(block: str) -> list[tuple[str, int, int]]:
    """(citation, start, end) for every `path.ext:NN` span in the block."""
    return [(m.group(0), m.start(), m.end()) for m in _FILE_LINE_RE.finditer(block)]


def _demand_set(block: str) -> list[str]:
    """Distinct `file:line` citations owing evidence, in first-seen order.

    Two reductions, and they are not the same one. Span exclusion drops a
    citation lying inside a parsed statement, without which every statement
    would demand a statement. Deduplication by `(path, line)` then collapses
    restatements -- a table repeating a citation multiplies one location into
    several, and the reported count is of distinct locations.

    Spans are computed over the raw block: normalization is confined to
    ``parse_evidence_statements`` (a declared limitation of Phase 225; a
    citation inside a two-span statement's observed text registers as a demand).
    """
    spans = [(m.start(), m.end()) for m in _EVIDENCE_STMT_RE.finditer(block)]
    seen: dict[str, None] = {}
    for citation, start, _end in _file_line_citations(block):
        if any(a <= start < b for a, b in spans):
            continue
        seen.setdefault(citation, None)
    return list(seen)


def _statement_index(block: str) -> dict[tuple[str, int], EvidenceStatement]:
    return {(s.path, s.line): s for s in parse_evidence_statements(block)}
