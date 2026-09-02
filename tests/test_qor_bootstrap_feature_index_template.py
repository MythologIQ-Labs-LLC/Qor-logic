"""Phase 80 P1: qor-bootstrap FEATURE_INDEX.md template section (GH #73).

Phase 249 (GH #405) converted the header assertion. It previously asserted the
*defective* 7-column header was "canonical" by substring presence, never
invoking the parser -- which is why GH #405 survived a test positioned to catch
it. The header check now drives the template's own header through
`feature_index_verify.parse_index_rows`, so a template edit that breaks parsing
fails regardless of which strings happen to be present.

The remaining assertions stay as presence checks by design: they cover template
shape (placeholder, section headings, consumer reference) with no behavioral
counterpart to invoke.
"""
from pathlib import Path

from qor.scripts import feature_index_verify as fiv

TEMPLATES = Path("qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md")

CANONICAL_COLUMNS = (
    "id",
    "name",
    "source-of-truth file:line",
    "doc citation",
    "test path",
    "surface",
    "status",
)


def _region() -> str:
    text = TEMPLATES.read_text(encoding="utf-8")
    start = text.index("## FEATURE_INDEX.md Template")
    end_idx = text.find("## Final Report Template", start)
    return text[start: end_idx if end_idx != -1 else start + 4000]


def test_templates_define_feature_index_section():
    region = _region()
    assert "{project_name}" in region, "template must use {project_name} placeholder"
    assert "Coverage Summary" in region, "template must include Coverage Summary block"
    assert "Gaps Surfaced" in region, "template must include Gaps Surfaced section"
    assert "/qor-implement" in region, (
        "template must reference /qor-implement as the consumer of FEATURE_INDEX.md"
    )


def test_template_header_parses_every_canonical_column():
    """The seeded header must resolve every column the doctrine reads.

    Acceptance question: if the template's header were silently wrong for the
    parser but its strings were still present, would this fail? Yes -- because
    the header is fed to the parser rather than matched as text.
    """
    header = next(
        line for line in _region().splitlines() if line.startswith("| ID |")
    )
    ncols = header.count("|") - 1
    sep = "|" + "---|" * ncols
    row = "| FX001 " + "| x " * (ncols - 2) + "| verified |"

    table = "\n".join([header, sep, row]) + "\n"
    rows = fiv.parse_index_rows(table)

    assert rows, "the seeded header must yield parseable rows"
    missing = [c for c in CANONICAL_COLUMNS if c not in rows[0]]
    assert not missing, f"seeded header does not resolve canonical columns: {missing}"
