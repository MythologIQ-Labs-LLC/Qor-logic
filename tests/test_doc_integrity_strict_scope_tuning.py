"""Phase 31 Phase 2: Check Surface D/E scope-fence tuning.

Before Phase 31, lenient D returned 352 findings against the live repo --
too noisy for strict-mode wiring. Phase 31 adds three exclusion layers:
(a) doctrine-peer exclusion; (b) home-directory-peer exclusion; (c)
per-entry `scope_exclude:` glossary frontmatter.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity_strict as dis  # noqa: E402


def _mk_repo(tmp_path: Path, glossary_body: str, extra_files: dict) -> tuple[str, str]:
    (tmp_path / "qor" / "references").mkdir(parents=True, exist_ok=True)
    glossary = tmp_path / "qor" / "references" / "glossary.md"
    glossary.write_text(glossary_body, encoding="utf-8")
    for rel, body in extra_files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return str(glossary), str(tmp_path)


def test_doctrine_peer_excluded(tmp_path):
    """Term home in doctrine-a.md; usage in doctrine-b.md; NOT flagged."""
    body = (
        "# Glossary\n\n"
        "```yaml\n"
        "term: Foo\n"
        "definition: A thing.\n"
        "home: qor/references/doctrine-a.md\n"
        "referenced_by:\n"
        "  - qor/references/doctrine-a.md\n"
        "```\n"
    )
    glossary, root = _mk_repo(
        tmp_path, body,
        {
            "qor/references/doctrine-a.md": "Foo lives here.\n",
            "qor/references/doctrine-b.md": "Foo is referenced here too.\n",
        },
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert not any("doctrine-b.md" in f for f in findings), (
        f"doctrine-b should be excluded as doctrine-peer: {findings}"
    )


def test_home_dir_peer_excluded(tmp_path):
    """Term home in docs/foo.md; usage in docs/bar.md; NOT flagged (siblings)."""
    body = (
        "# Glossary\n\n"
        "```yaml\n"
        "term: Gadget\n"
        "definition: A widget.\n"
        "home: docs/foo.md\n"
        "referenced_by:\n"
        "  - docs/foo.md\n"
        "```\n"
    )
    glossary, root = _mk_repo(
        tmp_path, body,
        {
            "docs/foo.md": "Gadget is defined here.\n",
            "docs/bar.md": "Gadget referenced here too.\n",
        },
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert not any("docs/bar.md" in f for f in findings), (
        f"docs/bar.md should be excluded as home-dir-peer: {findings}"
    )


def test_scope_exclude_opt_out(tmp_path):
    """Glossary entry with scope_exclude: [docs/special.md] -> usage there NOT flagged."""
    body = (
        "# Glossary\n\n"
        "```yaml\n"
        "term: Baz\n"
        "definition: Thing.\n"
        "home: qor/references/doctrine-x.md\n"
        "referenced_by:\n"
        "  - qor/references/doctrine-x.md\n"
        "scope_exclude:\n"
        "  - docs/special.md\n"
        "```\n"
    )
    glossary, root = _mk_repo(
        tmp_path, body,
        {
            "qor/references/doctrine-x.md": "Baz defined.\n",
            "docs/special.md": "Baz referenced here with opt-out.\n",
        },
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert not any("docs/special.md" in f for f in findings), (
        f"docs/special.md should be excluded via scope_exclude: {findings}"
    )


def test_unrelated_directory_still_flagged(tmp_path):
    """Regression: scope-fence tuning must not over-exclude. Home in qor/references/;
    usage in qor/gates/ (non-peer, non-archive) IS flagged."""
    body = (
        "# Glossary\n\n"
        "```yaml\n"
        "term: Alpha\n"
        "definition: Test term.\n"
        "home: qor/references/doctrine-alpha.md\n"
        "referenced_by:\n"
        "  - qor/references/doctrine-alpha.md\n"
        "```\n"
    )
    glossary, root = _mk_repo(
        tmp_path, body,
        {
            "qor/references/doctrine-alpha.md": "Alpha is defined.\n",
            "qor/gates/unrelated.md": "Alpha is used in an unrelated directory.\n",
        },
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert any("qor/gates/unrelated.md" in f for f in findings), (
        f"Non-archive non-peer usage must still flag: {findings}"
    )
