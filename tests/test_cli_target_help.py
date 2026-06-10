"""Phase 154 (GH #219): the `--target` arguments carry clarifying help text, so
`seed --target NAME` is not mistaken for an artifact name (it is a destination
directory). Also pins the now-resolved exit-0 behavior of `seed --target`.
"""
from __future__ import annotations

import argparse

from qor.cli import _build_parser, _do_seed


def _subparsers(parser: argparse.ArgumentParser) -> dict:
    for a in parser._actions:
        if isinstance(a, argparse._SubParsersAction):
            return a.choices
    return {}


def _target_action(subparser: argparse.ArgumentParser):
    for a in subparser._actions:
        if "--target" in a.option_strings:
            return a
    return None


def test_seed_target_help_clarifies_directory():
    parser, _ = _build_parser()
    action = _target_action(_subparsers(parser)["seed"])
    assert action is not None, "seed must have a --target argument"
    assert action.help, "seed --target must carry help text (GH #219)"
    low = action.help.lower()
    assert "director" in low, "help must clarify --target is a directory"
    assert "artifact" in low or "not " in low, "help must disambiguate from an artifact name"


def test_all_path_targets_have_help():
    parser, _ = _build_parser()
    subs = _subparsers(parser)
    for cmd in ("install", "uninstall", "init", "seed"):
        action = _target_action(subs[cmd])
        assert action is not None, f"{cmd} must have a --target argument"
        assert action.help, f"{cmd} --target must carry help text"


def test_seed_exit_zero_regression(tmp_path):
    # fresh workspace
    ns = argparse.Namespace(target=tmp_path / "fresh")
    assert _do_seed(ns) == 0
    # --target pointing at a sub-path of an already-seeded workspace (the #219 case);
    # the v0.106.0 exit-1 is resolved -- it must stay 0.
    seeded = tmp_path / "ws"
    assert _do_seed(argparse.Namespace(target=seeded)) == 0
    assert _do_seed(argparse.Namespace(target=seeded / "sub")) == 0
