"""Phase 66 (#54 + #55): qor-validate skill prose contract.

Locks the skill-prose changes that consumer workspaces depend on:
- post-anchor mode documented with `--post-anchor` flag.
- Stale `qor-logic verify-ledger docs/META_LEDGER.md` path-arg invocation removed.
- Source URL points at MythologIQ-Labs-LLC (post-rename canonical repo).
- New entry classifications (TAINTED, DISCLOSED_PRE_ANCHOR) named in prose.
"""
from __future__ import annotations

from pathlib import Path

SKILL_PATH = Path("qor/skills/governance/qor-validate/SKILL.md")


def _text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def test_skill_documents_post_anchor_mode():
    body = _text()
    assert "--post-anchor" in body, (
        "qor-validate SKILL.md must document the --post-anchor flag per GH #55"
    )
    assert "post-anchor" in body.lower()
    assert "boundary" in body.lower(), (
        "skill prose must mention the boundary concept (entry id partitioning "
        "pre- vs post-anchor)"
    )


def test_skill_no_longer_recommends_stale_path_arg_invocation():
    """Pre-Phase-66 prose said `qor-logic verify-ledger docs/META_LEDGER.md`
    which the CLI rejected (path was not accepted). The new prose either
    drops the path entirely (CLI default) or uses `--ledger PATH`."""
    body = _text()
    for line in body.splitlines():
        if "qor-logic verify-ledger" in line and "docs/META_LEDGER.md" in line:
            # Allowed: `--ledger docs/META_LEDGER.md` (explicit flag).
            # Forbidden: bare positional path arg.
            if "--ledger" not in line:
                raise AssertionError(
                    f"stale path-arg invocation found: {line!r}; "
                    "use `qor-logic verify-ledger` (default) or "
                    "`qor-logic verify-ledger --ledger PATH`"
                )


def test_skill_source_url_uses_labs_llc():
    body = _text()
    assert "https://github.com/MythologIQ-Labs-LLC/Qor-logic" in body, (
        "qor-validate SKILL.md frontmatter must reference the post-rename "
        "canonical repository (MythologIQ-Labs-LLC); pre-Phase-66 still "
        "pointed at the old MythologIQ org"
    )
    # And the old URL must be absent.
    for line in body.splitlines():
        if "github.com/MythologIQ/Qor-logic" in line and "Labs-LLC" not in line:
            raise AssertionError(
                f"stale source URL found: {line!r}; should be MythologIQ-Labs-LLC"
            )


def test_skill_names_new_failure_classifications():
    body = _text()
    assert "TAINTED" in body, (
        "qor-validate SKILL.md must name the TAINTED classification "
        "per Phase 66 taint propagation (GH #54)"
    )
    assert "DISCLOSED_PRE_ANCHOR" in body, (
        "qor-validate SKILL.md must name DISCLOSED_PRE_ANCHOR per "
        "Phase 66 post-anchor mode (GH #55)"
    )
