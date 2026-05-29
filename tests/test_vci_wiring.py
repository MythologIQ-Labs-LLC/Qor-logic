"""Wiring + doctrine tests for Verification & Closure Integrity (Phase 114).

The load-bearing behavioral tests live in test_qa_evidence / test_feature_index_abort
/ test_ac_close_guard. These assert the *consolidation* facts: the substantiate
FEATURE_INDEX pass now invokes the executable ABORT (not "deferred"), the close
guard is wired, and the doctrine states the load-bearing rules. Per
doctrine-test-functionality, these check meaningful state (module invocation +
removal of the deferred-language), not mere prose presence.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBSTANTIATE = ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
DOCTRINE = ROOT / "qor" / "references" / "doctrine-verification-closure-integrity.md"


def test_substantiate_invokes_feature_index_abort():
    text = SUBSTANTIATE.read_text(encoding="utf-8")
    assert importlib.util.find_spec("qor.scripts.feature_index_verify") is not None
    assert "qor.scripts.feature_index_verify" in text  # prose-lint: ok=prompt-citation paired with existence check
    # the deferred-language must be gone from the FEATURE_INDEX pass
    assert "ABORT-on-outside-scope-regression helper is deferred" not in text


def test_substantiate_references_close_guard():
    text = SUBSTANTIATE.read_text(encoding="utf-8")
    assert importlib.util.find_spec("qor.scripts.ac_close_guard") is not None
    assert "qor.scripts.ac_close_guard" in text  # prose-lint: ok=prompt-citation paired with existence check


def test_doctrine_defines_terms_and_rules():
    text = DOCTRINE.read_text(encoding="utf-8").lower()
    assert "qa evidence artifact" in text
    assert "acceptance-criteria close guard" in text
    # met-or-split rule + WARN-first graduation must both be stated
    assert "follow-on" in text and "met-ness" in text
    assert "warn-first" in text and "graduat" in text
