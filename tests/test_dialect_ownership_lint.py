"""GH #469: a module that parses a field owned by a declared dialect must import it.

The rule under test is D1n of docs/plan-qor-phase282-dialect-ownership-lint.md,
in four steps:

  1. normalize the label region to a fixpoint over TWO enumerated constructs --
     a trailing character-class wildcard, and an optional non-capturing group;
  2. discard any expansion still carrying a construct;
  3. classify each surviving expansion independently, longest-form-wins WITHIN it;
  4. union the findings, reporting each distinct (field, kind) once per site.

Step 3 versus step 4 is the load-bearing part: longest-form-wins is a
containment tiebreaker inside one concrete label, never a selector over the
expansion set.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


from qor.scripts import dialect_ownership_lint as lint

REPO = Path(__file__).resolve().parents[1]

_HEX = "[0-9a-f]{64}"


def _module(tmp_path, name, body):
    p = tmp_path / (name + ".py")
    p.write_text(body, encoding="utf-8")
    return p


def _scan_one(tmp_path, body, name="probe"):
    """Findings for a single synthetic module."""
    return lint.scan_module(_module(tmp_path, name, body), repo_root=tmp_path)


def _kinds(findings, kind):
    return sorted({f.subject for f in findings if f.kind == kind})


# --- the core property ------------------------------------------------------

def test_flags_a_parser_that_does_not_import_its_owner(tmp_path):
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        f'_RE = re.compile(r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`")\n'
    )
    assert _kinds(_scan_one(tmp_path, body), "read") == ["Content Hash"]


def test_accepts_a_parser_that_imports_its_owner(tmp_path):
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        "from qor.scripts import ledger_dialect\n"
        f'_RE = re.compile(r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`")\n'
    )
    assert _kinds(_scan_one(tmp_path, body), "read") == []


def test_owner_parsing_its_own_field_is_not_a_violation(tmp_path):
    body = "import re\n" f'_RE = re.compile(r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`")\n'
    findings = lint.scan_module(
        _module(tmp_path, "ledger_dialect", body), repo_root=tmp_path
    )
    assert _kinds(findings, "read") == []


# --- D1a: declared forms, and containment -----------------------------------

def test_a_declared_alias_label_is_a_read_of_its_field(tmp_path):
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        f'_RE = re.compile(r"\\*\\*Previous Chain Hash\\*\\*:\\s*`({_HEX})`")\n'
    )
    assert _kinds(_scan_one(tmp_path, body), "read") == ["Previous Hash"]


def test_a_declared_alias_is_not_a_read_of_a_field_it_merely_contains(tmp_path):
    """`Previous Chain Hash` must NOT also register as a Chain Hash read."""
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        f'_RE = re.compile(r"\\*\\*Previous Chain Hash\\*\\*:\\s*`({_HEX})`")\n'
    )
    findings = _scan_one(tmp_path, body)
    assert "Chain Hash" not in _kinds(findings, "read")
    assert _kinds(findings, "undeclared-label") == []


def test_an_undeclared_containing_label_is_reported_not_ignored(tmp_path):
    """`Superseded Content Hash` is a distinct field, not an alias, and not silence."""
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        f'_RE = re.compile(r"\\*\\*Superseded Content Hash\\*\\*:\\s*`({_HEX})`")\n'
    )
    findings = _scan_one(tmp_path, body)
    assert _kinds(findings, "read") == []
    assert _kinds(findings, "undeclared-label") == ["Superseded Content Hash"]


def test_the_canonical_qualified_label_reads_as_its_field(tmp_path):
    """`**Chain Hash (Merkle seal)**` is the corpus's most common qualified form.

    A detector that unescapes `\\*` but not `\\(` files it as an unknown label
    and silently drops whole modules from the violation set. That defect was
    live during this phase.
    """
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        f'_RE = re.compile(r"\\*\\*Chain Hash \\(Merkle seal\\)\\*\\*:\\s*`({_HEX})`")\n'
    )
    findings = _scan_one(tmp_path, body)
    assert _kinds(findings, "read") == ["Chain Hash"]
    assert _kinds(findings, "undeclared-label") == []


# --- D1n: the four steps ----------------------------------------------------

def test_longest_form_wins_applies_within_an_expansion_not_across_the_set():
    """Step 3 vs step 4. Applied across the set this reports Previous Hash alone."""
    reads, undeclared = lint.classify_region(r"(?:Previous )?Chain Hash")
    assert reads == {"Previous Hash", "Chain Hash"}
    assert undeclared == set()


def test_an_intermediate_expansion_is_not_a_label_form():
    """Step 2. Six strings expand; four still carry constructs and are discarded."""
    reads, undeclared = lint.classify_region(r"(?:META_LEDGER )?Content Hash[^\n*]*")
    assert reads == {"Content Hash"}
    assert undeclared == set()


def test_a_declared_expansion_and_an_undeclared_sibling_both_report():
    reads, undeclared = lint.classify_region(r"(?:Superseded )?Content Hash")
    assert reads == {"Content Hash"}
    assert undeclared == {"Superseded Content Hash"}


def test_the_nesting_bound_resolves_ledger_base_currency():
    """The one live region needing the second level."""
    reads, _ = lint.classify_region(r"Previous Hash(?:\s*\([^)]+\))?")
    assert reads == {"Previous Hash"}


def test_optional_group_expansion_is_order_independent():
    """The group expansion must not depend on the wildcard strip running first.

    Before this was fixed, the region below resolved only because the trailing
    `[^)]+` was stripped before the group was parsed -- an ordering accident
    that a refactor of step 1 would have silently undone.
    """
    region = r"Previous Hash(?:\s*\([^)]+\))?"
    assert lint.OPT_GROUP.search(region) is not None


def test_a_third_construct_is_not_normalized():
    """D1n enumerates two constructs and closes the list."""
    reads, undeclared = lint.classify_region(r"Content Hash(?=:)")
    assert reads == set()
    assert undeclared == {"Content Hash(?=:)"} or undeclared == set()


# --- the harvest ------------------------------------------------------------

def test_a_pattern_in_a_comprehension_fed_collection_is_harvested(tmp_path):
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        "_STRIPS = [re.compile(p) for p in (\n"
        f'    r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`",\n'
        ")]\n"
    )
    assert _kinds(_scan_one(tmp_path, body), "read") == ["Content Hash"]


def test_a_hoisted_pattern_collection_is_harvested(tmp_path):
    """One level of name indirection. Hoisting the tuple is an ordinary refactor."""
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        "_PATTERNS = (\n"
        f'    r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`",\n'
        ")\n"
        "_STRIPS = [re.compile(p) for p in _PATTERNS]\n"
    )
    assert _kinds(_scan_one(tmp_path, body), "read") == ["Content Hash"]


def test_a_helper_built_pattern_is_not_claimed_as_checked(tmp_path):
    """D5 blind spot 1: indirection defeats the scan, and that is disclosed."""
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        "def _field(name):\n"
        '    return re.compile(r"\\*\\*" + name + r"\\*\\*")\n'
        '_RE = _field("Content Hash")\n'
    )
    assert _kinds(_scan_one(tmp_path, body), "read") == []


# --- D2: the declaration surface --------------------------------------------

def test_same_field_name_in_another_document_is_not_a_violation(tmp_path):
    """Fields are (document, field) pairs. The meta_ledger_walker case."""
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        '_RE = re.compile(r"^\\*\\*Verdict\\*\\*\\s*:\\s*([A-Z]+)")\n'
    )
    assert _kinds(_scan_one(tmp_path, body), "read") == []


def test_a_module_declaring_no_documents_fails(tmp_path):
    """Silence is not compliance."""
    body = "import re\n" f'_RE = re.compile(r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`")\n'
    findings = _scan_one(tmp_path, body)
    assert any(f.kind == "undeclared-document" for f in findings)


def test_a_declaration_naming_a_document_without_the_field_fails(tmp_path):
    """Cross-check (b): the declared path must appear as a literal in the module."""
    body = (
        'READS_DOCUMENTS = ("docs/NOT_REFERENCED.md",)\n'
        "import re\n"
        f'_RE = re.compile(r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`")\n'
    )
    findings = _scan_one(tmp_path, body)
    assert any(f.kind == "false-declaration" for f in findings)


# --- D3: the baseline -------------------------------------------------------

def _baseline_of(findings):
    return [lint.baseline_key(f) for f in findings]


def test_baseline_entry_reports_without_failing(tmp_path):
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        f'_RE = re.compile(r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`")\n'
    )
    findings = _scan_one(tmp_path, body)
    assert lint.evaluate(findings, baseline=_baseline_of(findings)).failures == []


def test_a_new_violation_fails_even_when_the_baseline_is_full(tmp_path):
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        f'_A = re.compile(r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`")\n'
        f'_B = re.compile(r"\\*\\*Chain Hash\\*\\*:\\s*`({_HEX})`")\n'
    )
    findings = _scan_one(tmp_path, body)
    partial = [k for k in _baseline_of(findings) if "Content Hash" in k]
    assert lint.evaluate(findings, baseline=partial).failures != []


def test_a_second_diverging_pattern_in_a_baselined_module_fails(tmp_path):
    """D3's key. A (module, document, field, kind) key is line-blind and passes this."""
    one = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        f'_A = re.compile(r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`")\n'
    )
    two = one + f'_B = re.compile(r"\\*\\*Content Hash\\*\\*:\\s*({_HEX})")\n'
    base = _baseline_of(_scan_one(tmp_path, one, name="m1"))
    findings = _scan_one(tmp_path, two, name="m2")
    # same module name would be required for a true key collision; normalize it
    base = [k.replace("m1", "m2") for k in base]
    assert lint.evaluate(findings, baseline=base).failures != []


def test_a_reformatted_pattern_does_not_mint_a_new_key(tmp_path):
    compact = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        f'_A = re.compile(r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`")\n'
    )
    spaced = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        "_A = re.compile(\n"
        f'    r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`"\n'
        ")\n"
    )
    a = _baseline_of(_scan_one(tmp_path, compact, name="same"))
    b = _baseline_of(_scan_one(tmp_path, spaced, name="same"))
    assert a == b


def test_a_stale_baseline_entry_fails(tmp_path):
    """The baseline can only shrink."""
    body = (
        'READS_DOCUMENTS = ("docs/META_LEDGER.md",)\n'
        "import re\n"
        f'_A = re.compile(r"\\*\\*Content Hash\\*\\*:\\s*`({_HEX})`")\n'
    )
    findings = _scan_one(tmp_path, body)
    stale = _baseline_of(findings) + ["probe|docs/META_LEDGER.md|Chain Hash|read|gone"]
    assert lint.evaluate(findings, baseline=stale).failures != []


def test_the_baseline_file_is_tracked_by_git():
    """GH #457's failure mode: a lint whose data sat at a gitignored path."""
    rel = lint.BASELINE_PATH.relative_to(REPO).as_posix()
    out = subprocess.run(
        ["git", "check-ignore", rel], cwd=REPO, capture_output=True, text=True
    )
    assert out.returncode != 0, f"{rel} is gitignored"
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel], cwd=REPO, capture_output=True
    )
    assert tracked.returncode == 0, f"{rel} is not tracked by git"


# --- the live tree ----------------------------------------------------------

def test_live_tree_matches_the_recorded_baseline():
    """The enforcement mechanism until promotion: this runs the lint for real."""
    result = lint.run(REPO)
    assert result.failures == [], "\n".join(result.failures)
