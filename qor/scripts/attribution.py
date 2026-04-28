"""Canonical attribution strings for QorLogic-SDLC-authored work.

Pure functions returning trailer/footer/CHANGELOG-line strings. Module-level
constants hold the SDK identity and canonical QorLogic URL; pass kwargs to
override per-call. The model name is the only required argument.

The leading robot emoji on commit trailers and PR footers is a documented,
narrowly-scoped exception to the project ASCII-only-in-data rule. Rationale
and scope live in qor/references/doctrine-attribution.md.
"""
from __future__ import annotations

_SDK_NAME = "Claude Code"
_SDK_URL = "https://claude.com/claude-code"
_QOR_URL = "https://github.com/MythologIQ-Labs-LLC/qor-logic"
_MODEL_EMAIL = "noreply@anthropic.com"


def commit_trailer(
    model: str,
    *,
    sdk_name: str | None = None,
    sdk_url: str | None = None,
    qor_url: str | None = None,
    model_email: str | None = None,
) -> str:
    """Return the commit trailer for QorLogic-SDLC-authored work."""
    sdk_name = _SDK_NAME if sdk_name is None else sdk_name
    sdk_url = _SDK_URL if sdk_url is None else sdk_url
    qor_url = _QOR_URL if qor_url is None else qor_url
    model_email = _MODEL_EMAIL if model_email is None else model_email
    return (
        f"\U0001F916 Authored via [QorLogic SDLC]({qor_url}) "
        f"on [{sdk_name}]({sdk_url})\n"
        f"\n"
        f"Co-Authored-By: {model} <{model_email}>"
    )


def pr_footer(
    model: str,
    *,
    defects_list: str,
    comparison_doc_path: str | None = None,
    sdk_name: str | None = None,
    sdk_url: str | None = None,
    qor_url: str | None = None,
) -> str:
    """Return the PR-body footer for QorLogic-SDLC-authored work.

    `defects_list` is a pre-formatted multi-line string the caller supplies
    (typically a numbered markdown list). `comparison_doc_path`, when provided,
    appends a "See <path> for the side-by-side." sentence.
    """
    sdk_name = _SDK_NAME if sdk_name is None else sdk_name
    sdk_url = _SDK_URL if sdk_url is None else sdk_url
    qor_url = _QOR_URL if qor_url is None else qor_url
    body = (
        f"\U0001F916 Authored using the [QorLogic]({qor_url}) "
        f"SDLC workflow on [{sdk_name}]({sdk_url}).\n"
        f"\n"
        f"The QorLogic adversarial audit gate caught these defects "
        f"before review:\n"
        f"\n"
        f"{defects_list}"
    )
    if comparison_doc_path is not None:
        body += f"\n\nSee `{comparison_doc_path}` for the side-by-side."
    return body


def changelog_attribution_line(*, qor_url: str | None = None) -> str:
    """Return the italic CHANGELOG attribution line.

    Intended placement is on the line immediately below an existing version
    header, leaving the `## [X.Y.Z] - YYYY-MM-DD` parser contract intact.
    """
    qor_url = _QOR_URL if qor_url is None else qor_url
    return f"_Built via [QorLogic SDLC]({qor_url})._"
