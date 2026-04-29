"""Phase 45 Phase 1: attribution helper pure-function tests."""
from __future__ import annotations

import subprocess

from qor.scripts import attribution


def test_commit_trailer_default_emits_canonical_string():
    out = attribution.commit_trailer(model="Claude Opus 4.7 (1M context)")
    expected = (
        "\U0001F916 Authored via [Qor-logic SDLC]"
        "(https://github.com/MythologIQ-Labs-LLC/qor-logic) on "
        "[Claude Code](https://claude.com/claude-code)\n"
        "\n"
        "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    )
    assert out == expected


def test_commit_trailer_model_arg_changes_only_coauthor_line():
    a = attribution.commit_trailer(model="Foo Model")
    b = attribution.commit_trailer(model="Bar Model")
    a_lines = a.split("\n")
    b_lines = b.split("\n")
    assert a_lines[0] == b_lines[0]
    assert a_lines[2] == "Co-Authored-By: Foo Model <noreply@anthropic.com>"
    assert b_lines[2] == "Co-Authored-By: Bar Model <noreply@anthropic.com>"


def test_commit_trailer_kwargs_override_constants():
    out = attribution.commit_trailer(
        model="M",
        sdk_name="Custom SDK",
        sdk_url="https://custom.example/sdk",
        qor_url="https://custom.example/qor",
        model_email="custom@example.org",
    )
    assert "[Custom SDK](https://custom.example/sdk)" in out
    assert "[Qor-logic SDLC](https://custom.example/qor)" in out
    assert "<custom@example.org>" in out
    assert "Claude Code" not in out
    assert "MythologIQ-Labs-LLC" not in out
    assert "noreply@anthropic.com" not in out


def test_pr_footer_substitutes_defects_list():
    out = attribution.pr_footer(model="M", defects_list="1. foo\n2. bar")
    assert "1. foo\n2. bar" in out
    assert "[Qor-logic]" in out
    assert "[Claude Code]" in out


def test_pr_footer_omits_comparison_link_when_none():
    without = attribution.pr_footer(model="M", defects_list="1. x")
    with_link = attribution.pr_footer(
        model="M",
        defects_list="1. x",
        comparison_doc_path="docs/COMPARISON.md",
    )
    assert "side-by-side" not in without
    assert "docs/COMPARISON.md" in with_link
    assert "side-by-side" in with_link


def test_pr_footer_uses_canonical_qor_url():
    out = attribution.pr_footer(model="M", defects_list="1. x")
    assert "https://github.com/MythologIQ-Labs-LLC/qor-logic" in out


def test_changelog_attribution_line_is_locked_format():
    out = attribution.changelog_attribution_line()
    assert out == (
        "_Built via [Qor-logic SDLC]"
        "(https://github.com/MythologIQ-Labs-LLC/qor-logic)._"
    )


def test_no_em_dash_in_any_emitted_string():
    outputs = [
        attribution.commit_trailer(model="M"),
        attribution.commit_trailer(
            model="M",
            sdk_name="X",
            sdk_url="u",
            qor_url="v",
            model_email="e",
        ),
        attribution.pr_footer(model="M", defects_list="1. x"),
        attribution.pr_footer(
            model="M", defects_list="1. x", comparison_doc_path="c"
        ),
        attribution.changelog_attribution_line(),
        attribution.changelog_attribution_line(qor_url="https://example.org"),
    ]
    for s in outputs:
        assert "—" not in s, f"em-dash in: {s!r}"
        assert "–" not in s, f"en-dash in: {s!r}"


def test_commit_trailer_coauthor_line_is_recognized_by_git_interpret_trailers():
    """Functional check: the rendered trailer must actually parse as a git
    trailer, not just contain the literal string `Co-Authored-By:`. If spacing,
    angle brackets, or the blank-line separator drift, GitHub stops attributing
    the co-author and this test catches it before the trailer ships."""
    out = attribution.commit_trailer(model="Claude Opus 4.7 (1M context)")
    msg = "subject line\n\nbody paragraph\n\n" + out + "\n"
    result = subprocess.run(
        ["git", "interpret-trailers", "--parse"],
        input=msg.encode("utf-8"),
        capture_output=True,
        check=True,
    )
    parsed_trailers = result.stdout.decode("utf-8").strip().splitlines()
    co_author_lines = [
        line for line in parsed_trailers if line.startswith("Co-Authored-By:")
    ]
    assert len(co_author_lines) == 1, (
        f"expected exactly one Co-Authored-By trailer recognized by git, "
        f"got: {parsed_trailers!r}"
    )
    assert co_author_lines[0] == (
        "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    )


def test_module_constants_are_the_only_default_source(monkeypatch):
    monkeypatch.setattr(attribution, "_QOR_URL", "https://mutated.example/qor")
    monkeypatch.setattr(attribution, "_SDK_NAME", "Mutated SDK")
    monkeypatch.setattr(attribution, "_SDK_URL", "https://mutated.example/sdk")
    monkeypatch.setattr(attribution, "_MODEL_EMAIL", "mutated@example.org")

    trailer = attribution.commit_trailer(model="M")
    footer = attribution.pr_footer(model="M", defects_list="1. x")
    line = attribution.changelog_attribution_line()

    assert "https://mutated.example/qor" in trailer
    assert "Mutated SDK" in trailer
    assert "https://mutated.example/sdk" in trailer
    assert "mutated@example.org" in trailer
    assert "https://mutated.example/qor" in footer
    assert "Mutated SDK" in footer
    assert "https://mutated.example/qor" in line
