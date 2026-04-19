"""Phase 35: skills must be runnable from any CWD after `pip install qor-logic`.

Pre-Phase-35 skill prose used `sys.path.insert(0, 'qor/scripts'); import X`,
which only works when CWD == repo root. After installation, the working
directory is typically the operator's project root, not the Qor-logic
repo. The 'qor/scripts' relative path does not resolve there, so imports
fail with ModuleNotFoundError.

Fix: skills reference `from qor.scripts import X` instead. That works in
both repo-dev mode (editable install) AND every downstream install.

These tests lock the contract at two layers:
  1. Structural lint over skill prose: no `sys.path.insert.*qor/scripts`
     patterns remain; no hyphen-named reliability scripts invoked via
     subprocess.
  2. Runtime import: every governance module the skills name resolves
     via `qor.scripts.*` / `qor.reliability.*`.
"""
from __future__ import annotations

import re
from importlib import import_module
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[1] / "qor" / "skills"


_SYS_PATH_HACK = re.compile(r"sys\.path\.insert\(\s*0\s*,\s*['\"]qor/scripts['\"]")
_HYPHEN_RELIABILITY = re.compile(r"qor/reliability/[a-z]+-[a-z-]+\.py")


def _all_skill_docs() -> list[Path]:
    return sorted(SKILLS_DIR.rglob("*.md"))


def test_no_sys_path_hack_in_skills():
    offenders: list[tuple[Path, int, str]] = []
    for path in _all_skill_docs():
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), start=1):
            if _SYS_PATH_HACK.search(line):
                offenders.append((path, i, line.strip()))
    assert not offenders, (
        "Skill prose still uses repo-CWD-assuming sys.path.insert; "
        "switch to `from qor.scripts import X`:\n  "
        + "\n  ".join(f"{p}:{i}: {ln}" for p, i, ln in offenders)
    )


def test_no_hyphen_named_reliability_invocations():
    offenders: list[tuple[Path, int, str]] = []
    for path in _all_skill_docs():
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), start=1):
            if _HYPHEN_RELIABILITY.search(line):
                offenders.append((path, i, line.strip()))
    assert not offenders, (
        "Skill prose invokes hyphen-named reliability scripts via path "
        "(non-importable, CWD-dependent); switch to "
        "`python -m qor.reliability.<snake_case_name>`:\n  "
        + "\n  ".join(f"{p}:{i}: {ln}" for p, i, ln in offenders)
    )


def test_qor_scripts_modules_importable():
    """Every governance helper named in skill prose must import cleanly
    via qor.scripts.<name>."""
    names = [
        "gate_chain",
        "governance_helpers",
        "shadow_process",
        "session",
        "doc_integrity",
        "doc_integrity_strict",
        "qor_audit_runtime",
        "qor_platform",
        "validate_gate_artifact",
        "changelog_stamp",
    ]
    for name in names:
        module = import_module(f"qor.scripts.{name}")
        assert module is not None, f"qor.scripts.{name} import produced None"


def test_qor_reliability_modules_importable():
    """Reliability scripts must be importable as qor.reliability.<name>
    so `python -m qor.reliability.<name>` works post-install."""
    names = ["intent_lock", "skill_admission", "gate_skill_matrix"]
    for name in names:
        module = import_module(f"qor.reliability.{name}")
        assert hasattr(module, "main"), (
            f"qor.reliability.{name} missing `main()` entry point required "
            f"for `python -m` invocation"
        )
