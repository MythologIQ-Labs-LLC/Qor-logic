"""Detects a document field acquiring a second parser (GH #469).

Four sealed phases fixed the same defect by hand: a field parsed by more than
one module, each with its own regex, diverging silently. Nothing detected the
next one.

**The property**::

    A module that parses a field owned by a declared dialect must import that
    dialect.

Decidable by AST plus bounded normalization over two enumerated constructs. Not
by general pattern semantics, and not by comparing read-counts -- that
alternative was measured at roughly 50% false positives.

**The classification rule**, in four steps, stated once here and in D1n of
``docs/plan-qor-phase282-dialect-ownership-lint.md``:

1. Normalize the label region to a fixpoint over exactly two constructs: a
   trailing character-class wildcard (``[^...]*`` / ``[^...]+``) is stripped,
   and an optional non-capturing group (``(?:X)?``) expands to both its present
   and absent forms. **Nothing else. A third construct is a new plan.**
2. Discard any expansion still carrying either construct. Intermediates are not
   label forms.
3. Classify each surviving expansion independently, applying longest-form-wins
   *within* that expansion. A declared form contributes a read of its field;
   otherwise an expansion containing an owned field name contributes an
   ``undeclared-label``. The branches are mutually exclusive by construction,
   which is what stops ``Previous Chain Hash`` -- itself a declared form -- from
   also reporting the ``Chain Hash`` it contains.
4. Union the findings, reporting each distinct ``(field, kind)`` once per site.

Longest-form-wins is a containment tiebreaker inside one concrete label, never a
selector over the expansion set. Applied at step 4 it would pick the longer form
and silently drop the other read.

Advisory: this cannot fail a seal. What makes it run is
``test_live_tree_matches_the_recorded_baseline``.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.scripts import ledger_dialect, verdict_dialect

#: Owners, in import order. Each declares ``OWNS``: {(document, field): forms}.
OWNERS = (ledger_dialect, verdict_dialect)
OWNER_MODULES = frozenset(m.__name__.rsplit(".", 1)[-1] for m in OWNERS)

BASELINE_PATH = Path(__file__).resolve().parents[2] / ".qor" / "dialect-ownership-baseline.json"

# --- step 1: the two enumerated constructs, and nothing else -----------------
CLASS_TAIL = re.compile(r"\[\^[^\]]*\][*+]")
#: The body takes a character class ATOMICALLY, before the single-character
#: branch. Without that, a bare ``)`` inside ``[^)]`` closes the group early and
#: ``Previous Hash(?:\s*\([^)]+\))?`` never expands. That region did resolve
#: before, but only because CLASS_TAIL happened to run first -- an ordering
#: accident a refactor of step 1 would silently undo.
#: The single-character branch excludes `[` and `]` so the alternatives are
#: DISJOINT. With a bare `[^()]` there, `[]` is matchable both as one character
#: class and as two single characters, and a star over ambiguous alternatives
#: backtracks exponentially: measured 0.0002s at 10 repetitions of `[]` and
#: 1.34s at 22, roughly x4 per two. Flagged by CodeQL as a high-severity
#: inefficient regular expression. Disjoint alternatives are flat, and agree
#: with the ambiguous form on every label region in the corpus.
OPT_GROUP = re.compile(r"\(\?:((?:\[[^\]]*\]|\\\(|\\\)|[^()\[\]])*)\)\?")
#: One literal qualifier, e.g. ``Content Hash (session seal)``.
LITERAL_QUALIFIER = re.compile(r"\s*\((?:[^()]|\\\(|\\\))*\)\s*$")
#: Any surviving regex construct disqualifies an expansion at step 2.
HAS_CONSTRUCT = re.compile(r"\[\^|\(\?|[*+?|]|\\s|\\S|\\w|\\d")

BOLD_SPAN = re.compile(r"(?:\\\*\\\*|\*\*)(.+?)(?:\\\*\\\*|\*\*)", re.S)
RE_FUNCS = frozenset(
    {"compile", "match", "search", "findall", "finditer", "fullmatch", "sub", "subn", "split"}
)
NESTING_BOUND = 2


def _declarations():
    forms, names, documents = {}, set(), set()
    for owner in OWNERS:
        for (document, field), owned in getattr(owner, "OWNS", {}).items():
            names.add(field)
            documents.add(document)
            for form in owned:
                forms[form] = (document, field)
    return forms, names, documents


FORM_TO_PAIR, OWNED_NAMES, OWNED_DOCUMENTS = _declarations()


@dataclass(frozen=True)
class Finding:
    module: str
    document: str
    subject: str
    kind: str
    lineno: int
    pattern: str


@dataclass
class Result:
    findings: list
    reported: list
    failures: list


# --- steps 1 and 2 ----------------------------------------------------------

def normalize_region(region: str) -> set[str]:
    frontier = {region.strip()}
    seen: set[str] = set()
    for _ in range(NESTING_BOUND * 4):
        if frontier <= seen:
            break
        seen |= frontier
        nxt: set[str] = set()
        for label in frontier:
            stripped = CLASS_TAIL.sub("", label).strip()
            if stripped != label:
                nxt.add(stripped)
                continue
            m = OPT_GROUP.search(label)
            if m:
                nxt.add((label[: m.start()] + m.group(1) + label[m.end():]).strip())
                nxt.add((label[: m.start()] + label[m.end():]).strip())
            else:
                nxt.add(label)
        if nxt == frontier:
            break
        frontier = nxt
    return {lab for lab in (frontier | seen) if lab and not HAS_CONSTRUCT.search(lab)}


# --- steps 3 and 4 ----------------------------------------------------------

def classify_region(region: str):
    """Fields read, and undeclared labels, for one label region."""
    reads: set[str] = set()
    undeclared: set[str] = set()
    for label in normalize_region(region):
        # Unescape what a LABEL may legitimately contain, before comparison.
        # Missing `\(` here files `**Chain Hash (Merkle seal)**` -- the corpus's
        # most common qualified form -- as an unknown label.
        label = label.replace("\\*", "*").replace("\\(", "(").replace("\\)", ")").strip()
        if label in FORM_TO_PAIR:
            reads.add(FORM_TO_PAIR[label][1])
            continue
        bare = LITERAL_QUALIFIER.sub("", label).strip()
        if bare in FORM_TO_PAIR:
            reads.add(FORM_TO_PAIR[bare][1])
            continue
        if any(name in label for name in OWNED_NAMES):
            undeclared.add(label)
    return reads, undeclared


# --- the harvest ------------------------------------------------------------

def _has_re_call(node: ast.AST) -> bool:
    for c in ast.walk(node):
        if isinstance(c, ast.Call):
            name = getattr(c.func, "attr", None) or getattr(c.func, "id", None)
            if name in RE_FUNCS:
                return True
    return False


def harvest(tree: ast.AST):
    """String constants that flow into a compiled pattern.

    Exact dataflow is undecidable here, so three sources approximate it, each
    resolving ONE level of module-level name indirection. That level is what
    closes the hoisted-collection evasion; longer chains are still missed.
    """
    out: dict = {}
    bindings = {
        t.id: node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for t in node.targets
        if isinstance(t, ast.Name)
    }
    resolved: set[str] = set()

    def take(node, depth=0):
        for c in ast.walk(node):
            if isinstance(c, ast.Constant) and isinstance(c.value, str):
                out[(c.lineno, c.col_offset, c.value)] = None
        if depth == 0:
            for c in ast.walk(node):
                if isinstance(c, ast.Name) and c.id in bindings and c.id not in resolved:
                    resolved.add(c.id)
                    take(bindings[c.id], depth + 1)

    class V(ast.NodeVisitor):
        def visit_Call(self, node):
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name in RE_FUNCS:
                for arg in node.args:
                    take(arg)
            self.generic_visit(node)

        def visit_Assign(self, node):
            named = any(
                getattr(t, "id", "").endswith(("_RE", "_PATTERN", "_PAT"))
                for t in node.targets
            )
            if named or _has_re_call(node.value):
                take(node.value)
            self.generic_visit(node)

    V().visit(tree)
    return [(ln, text) for (ln, _c, text) in sorted(out)]


def _imports_owner(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(a.name.rsplit(".", 1)[-1] in OWNER_MODULES for a in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").rsplit(".", 1)[-1] in OWNER_MODULES:
                return True
            if any(a.name in OWNER_MODULES for a in node.names):
                return True
    return False


def _source_without_declaration(source: str, tree: ast.AST) -> str:
    """The module source with the READS_DOCUMENTS assignment removed."""
    lines = source.splitlines(keepends=True)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", "") == "READS_DOCUMENTS" for t in node.targets
        ):
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            return "".join(lines[:start] + lines[end:])
    return source


def _declared_documents(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if getattr(t, "id", "") == "READS_DOCUMENTS":
                    try:
                        return tuple(ast.literal_eval(node.value))
                    except Exception:
                        return ()
    return ()


# --- scanning ---------------------------------------------------------------

def scan_module(path: Path, repo_root: Path) -> list:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    module = path.stem
    is_owner = module in OWNER_MODULES
    compliant = is_owner or _imports_owner(tree)
    declared = _declared_documents(tree)

    reads, undeclared = [], []
    for lineno, text in harvest(tree):
        for m in BOLD_SPAN.finditer(text):
            got, und = classify_region(m.group(1))
            for field in sorted(got):
                reads.append((lineno, field, text))
            for label in sorted(und):
                undeclared.append((lineno, label, text))

    findings: list = []
    if not reads and not undeclared:
        return findings

    # D2: declarations are cross-checked, not trusted.
    if not is_owner and reads and not declared:
        findings.append(Finding(module, "", "READS_DOCUMENTS", "undeclared-document", 0, ""))
    # Cross-check (b): the declared document's STEM must appear as a literal
    # somewhere OTHER than the declaration itself.
    #
    # The stem, not the full path: measured, the full path occurs in 2 of the 6
    # in-scope modules and the stem in 5, so a path rule would report on two
    # thirds of its own subjects.
    #
    # Outside the declaration: a READS_DOCUMENTS tuple contains its own paths,
    # so counting it makes the check vacuously true and it would pass the exact
    # document it exists to catch.
    body_without_declaration = _source_without_declaration(source, tree)
    for document in declared:
        stem = Path(document).stem
        if stem not in body_without_declaration:
            findings.append(Finding(module, document, document, "false-declaration", 0, ""))
            continue
        target = repo_root / document
        if target.exists():
            body = target.read_text(encoding="utf-8", errors="replace")
            if not any(name in body for name in OWNED_NAMES):
                findings.append(
                    Finding(module, document, document, "false-declaration", 0, "")
                )

    scope = set(declared) or {""}
    for lineno, field, text in reads:
        document = FORM_TO_PAIR.get(field, ("", field))[0]
        owner_doc = next(
            (d for (d, f) in FORM_TO_PAIR.values() if f == field), ""
        )
        if owner_doc and owner_doc not in scope:
            continue  # a same-named field in another document is not this one
        if compliant:
            continue
        findings.append(Finding(module, owner_doc, field, "read", lineno, text))
    for lineno, label, text in undeclared:
        findings.append(Finding(module, "", label, "undeclared-label", lineno, text))
    return findings


def baseline_key(finding: Finding) -> str:
    """(module, document, subject, kind, normalized-pattern).

    The pattern discriminator is what stops a second diverging regex for the
    same field in an already-baselined module from producing an identical key.
    """
    normalized = re.sub(r"\s+", "", finding.pattern)
    return "|".join(
        (finding.module, finding.document, finding.subject, finding.kind, normalized)
    )


def evaluate(findings, baseline) -> Result:
    baseline = list(baseline)
    keys = [baseline_key(f) for f in findings]
    reported, failures = [], []
    for f, key in zip(findings, keys):
        if key in baseline:
            reported.append(f)
        else:
            failures.append(
                f"NEW {f.kind}: {f.module}:{f.lineno} {f.subject or f.document}"
            )
    for stale in baseline:
        if stale not in keys:
            failures.append(f"STALE baseline entry no longer applies: {stale}")
    return Result(findings=findings, reported=reported, failures=failures)


def _load_baseline() -> list:
    if not BASELINE_PATH.exists():
        return []
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8")).get("entries", [])


def run(repo_root: Path, baseline=None) -> Result:
    findings: list = []
    for path in sorted((repo_root / "qor").rglob("*.py")):
        if "vendor" in path.parts or "dist" in path.parts:
            continue
        findings.extend(scan_module(path, repo_root))
    return evaluate(findings, _load_baseline() if baseline is None else baseline)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()

    if args.write_baseline:
        findings: list = []
        for path in sorted((root / "qor").rglob("*.py")):
            if "vendor" in path.parts or "dist" in path.parts:
                continue
            findings.extend(scan_module(path, root))
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_PATH.write_text(
            json.dumps({"entries": sorted(baseline_key(f) for f in findings)}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {len(findings)} baseline entries to {BASELINE_PATH}")
        return 0

    result = run(root)
    print(f"dialect_ownership_lint: {len(result.reported)} baselined, "
          f"{len(result.failures)} failing")
    for line in result.failures:
        print("  " + line)
    return 1 if result.failures else 0


if __name__ == "__main__":
    sys.exit(main())
