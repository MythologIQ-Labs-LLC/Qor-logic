"""Phase 249 (GH #404, #405): a bootstrapped workspace must emit artifacts the
governance gates can actually read.

Both defects were reported from a consumer workspace running a full governed
cycle, and both reproduce here against the shapes `/qor-bootstrap` seeds.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import feature_index_verify as fiv
from qor.scripts import governance_paths as gp
from qor.scripts import ledger_dialect as ld
from qor.scripts import ledger_hash

TEMPLATES = Path("qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md")

_H1 = "a" * 64
_H2 = "b" * 64
_H3 = "c" * 64


def _seeded_entry_shape() -> str:
    """An entry written to the bootstrap template's hash-field shape."""
    return (
        "### Entry #2: RESEARCH BRIEF\n\n"
        "**Timestamp**: 2026-09-02T00:00:00Z\n"
        "**Phase**: RESEARCH\n\n"
        f"**Content Hash**: `{_H1}`\n"
        f"**Previous Hash**: `{_H2}`\n"
        f"**Chain Hash (Merkle seal)**: `{_H3}`\n\n"
        "**Decision**: recorded.\n"
    )


def test_seeded_ledger_entry_parses_under_ledger_dialect():
    """Every hash field the template emits must match the shared dialect.

    Red before the template fix: an inline unbackticked hex on a
    `**Previous Hash**:` line matches none of the three accepted value forms,
    so PREV_HASH_RE misses and the entry is classified non-verifiable.
    """
    body = _seeded_entry_shape()

    assert ld.CONTENT_HASH_RE.search(body), "content hash must parse"
    assert ld.PREV_HASH_RE.search(body), "previous hash must parse"
    assert ld.CHAIN_HASH_RE.search(body), "chain hash must parse"


def test_bootstrap_template_documents_a_parseable_subsequent_entry():
    """The template must show an entry whose Previous Hash carries a digest.

    The genesis entry legitimately has no predecessor hash, so the template's
    GENESIS example cannot exercise PREV_HASH_RE at all. The defect appears at
    entry #2 onward, which the template never showed -- so an operator
    following it wrote an inline unbackticked hex that matches none of the
    three accepted value forms.

    Red before the fix: no subsequent-entry example exists in the template.
    The placeholder is filled exactly as an operator would fill it; the test
    does not restructure the line, or it would manufacture its own pass.
    """
    text = TEMPLATES.read_text(encoding="utf-8")
    filled = text.replace("[calculated hash]", _H1).replace("[hash]", _H2)

    prev_lines = [
        line for line in filled.splitlines()
        if line.startswith("**Previous Hash**") and "GENESIS" not in line
    ]
    assert prev_lines, (
        "template shows no subsequent-entry Previous Hash form, so an operator "
        "has nothing correct to copy for entry #2 onward"
    )
    for line in prev_lines:
        assert ld.PREV_HASH_RE.search(line), (
            f"template Previous Hash form does not parse: {line!r}"
        )


def _ledger(tmp_path: Path, entries: str) -> Path:
    p = tmp_path / "META_LEDGER.md"
    p.write_text("# Meta Ledger\n\n" + entries, encoding="utf-8")
    return p


def _unparseable_entry(num: int) -> str:
    """An entry that LABELS its hash fields but whose value form is unreadable.

    The GH #404 shape: an operator followed the old bootstrap template, so the
    entry claims integrity it cannot demonstrate.
    """
    return (
        f"### Entry #{num}: RESEARCH BRIEF\n\n"
        f"**Content Hash**:\nSHA256(x.md) = {_H1}\n\n"
        f"**Previous Hash**: {_H2}\n\n"
        "**Decision**: recorded.\n\n"
    )


def _unlabeled_entry(num: int) -> str:
    """A pre-convention entry that names no hash field at all.

    Claims nothing, so it stays a tolerated skip at any entry number.
    """
    return (
        f"### Entry #{num}: OLD\n\n"
        "**Author**: someone\n\n"
        "**Decision**: recorded before the hash convention.\n\n"
    )


def _parseable_entry(num: int, content: str, prev: str, chain: str) -> str:
    return (
        f"### Entry #{num}: SESSION SEAL\n\n"
        f"**Content Hash**: `{content}`\n"
        f"**Previous Hash**: `{prev}`\n"
        f"**Chain Hash (Merkle seal)**: `{chain}`\n\n"
        "**Decision**: sealed.\n\n"
    )


def test_verify_fails_when_every_entry_is_below_the_compat_boundary(tmp_path, capsys):
    """A young ledger's skips must not present as a clean verdict.

    MARKUP_COMPAT_BOUNDARY is an absolute entry number from THIS repository's
    history. No entry in a fresh workspace reaches it, so before the fix every
    unparseable entry degraded to an informational skip and exit 0 -- the
    reporter's "7 of 8 skipped, exit status 0".
    """
    ledger = _ledger(tmp_path, "".join(_unparseable_entry(n) for n in (1, 2, 3)))

    rc = ledger_hash.verify(ledger)

    assert rc != 0, "an all-unparseable young ledger must not verify clean"


def test_verify_still_grandfathers_entries_that_claim_no_hash(tmp_path):
    """The tightening must not become a blanket one.

    An entry that names no hash field makes no integrity claim, so it stays a
    tolerated skip -- which is what the genuinely pre-convention residuals in
    this repository's own ledger rely on. The line is the presence of a claim,
    not the entry number: an absolute cutoff cannot grandfather correctly in a
    workspace younger than the cutoff.
    """
    # Real digests: a repeated-character hex trips is_placeholder_pattern,
    # which would fail the entry for the wrong reason.
    content = ledger_hash.content_hash(Path(__file__))
    prev = ledger_hash.content_hash(TEMPLATES)
    chain = ledger_hash.chain_hash(content, prev)
    entries = _unlabeled_entry(1) + _parseable_entry(2, content, prev, chain)
    ledger = _ledger(tmp_path, entries)

    rc = ledger_hash.verify(ledger)

    assert rc == 0, "an entry claiming no hash must stay a tolerated skip"


_CANONICAL_COLUMNS = (
    "name",
    "source-of-truth file:line",
    "doc citation",
    "test path",
    "surface",
)


def _seeded_feature_index_header() -> str:
    """The header the bootstrap template actually emits."""
    text = TEMPLATES.read_text(encoding="utf-8")
    start = text.index("## FEATURE_INDEX.md Template")
    region = text[start:start + 4000]
    for line in region.splitlines():
        if line.startswith("| ID |"):
            return line
    raise AssertionError("no FEATURE_INDEX header row found in the template")


def test_seeded_feature_index_header_parses_every_canonical_column():
    """Rows under the seeded header must resolve the columns the doctrine reads.

    Red before the template fix: only `id` and `status` resolve (GH #365's
    alias), while every citation column the coverage tally is meant to
    substantiate comes back absent.
    """
    header = _seeded_feature_index_header()
    ncols = header.count("|") - 1
    sep = "|" + "---|" * ncols
    row = "| FX001 " + "| x " * (ncols - 2) + "| verified |"
    rows = fiv.parse_index_rows(f"{header}\n{sep}\n{row}\n")

    assert rows, "seeded header must yield parseable rows"
    missing = [c for c in _CANONICAL_COLUMNS if c not in rows[0]]
    assert not missing, f"seeded header does not resolve canonical columns: {missing}"


def test_parse_index_rows_reports_unreadable_header():
    """"No rows" and "rows I could not read" must stop being the same result."""
    unreadable = "| ID | Thing | Notes |\n|---|---|---|\n| FX001 | x | y |\n"

    assert fiv.parse_index_rows(unreadable) == [], "precondition: rows are dropped"
    assert fiv.header_is_readable(unreadable) is False, (
        "a table with no recognized status column must report an unreadable header"
    )
    good = "| ID | Name | Verification status |\n|---|---|---|\n| FX001 | x | verified |\n"
    assert fiv.header_is_readable(good) is True
    assert fiv.header_is_readable("no table here at all") is False


def test_work_named_plan_resolves_through_the_tier4_glob_row(tmp_path):
    """Permanent pin on the GH #407 closure.

    A plan named after its work, rather than after a Qor phase number, resolves
    because GOVERNANCE_INDEX Tier 4 carries a `docs/plan-*.md` glob row and
    `_is_registered` resolves globs. Passes today; it exists so a future index
    edit that drops that row fails loudly instead of silently re-breaking
    consumer plans.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "GOVERNANCE_INDEX.md").write_text(
        "# Governance Index\n\n## Tier 4\n\n| Artifact | Path | Plan |\n"
        "|---|---|---|\n| _example_ | `docs/plan-*.md` | [slug] |\n",
        encoding="utf-8",
    )
    plan = docs / "plan-sprint1-install-correctness.md"
    plan.write_text("# plan\n", encoding="utf-8")

    resolved = gp.resolve_governance_plan_path(
        "docs/plan-sprint1-install-correctness.md", tmp_path
    )

    assert resolved == plan.resolve()
