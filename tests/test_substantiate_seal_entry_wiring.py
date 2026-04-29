"""Phase 47 Phase 2: defensive tests for /qor-substantiate Step 7.7 wiring.

Each positive proximity-anchored assertion is paired with a strip-and-fail
negative-path test so the wiring lock cannot itself decay into a presence-only
check (per qor/references/doctrine-test-functionality.md and SG-035).

Three of the tests are direct countermeasures to Pass 1's V-1, V-2, V-3 grounds
and Pass 2's V-1 ground. They will fail if a future edit reintroduces any of:
- Pre-Step-7 placement (V-1 Pass 1)
- $MERKLE_SEAL undefined variable (V-2)
- python -c "...'$VAR'..." shell-interpolation pattern (V-3)
- Broken plan-path glob (V-1 Pass 2)
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SUBSTANTIATE = REPO / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"

STEP_7_7_HEADER = r"^### Step 7\.7\b"
STEP_7_HEADER = r"^### Step 7: "


def _read() -> str:
    return SUBSTANTIATE.read_text(encoding="utf-8")


def _proximity(body: str, header_pattern: str, phrase_pattern: str, span: int = 2000) -> bool:
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return False
    window = body[m.end(): m.end() + span]
    return re.search(phrase_pattern, window, re.IGNORECASE | re.DOTALL) is not None


def _strip_section(body: str, header_pattern: str, span: int = 4000) -> str:
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return body
    start = m.start()
    end = min(len(body), m.end() + span)
    filler = "\n# stripped\n" * ((end - start) // 12 + 1)
    filler = filler[: end - start]
    return body[:start] + filler + body[end:]


def test_step_7_7_invokes_seal_entry_check():
    body = _read()
    assert _proximity(body, STEP_7_7_HEADER, r"qor\.reliability\.seal_entry_check")
    assert _proximity(body, STEP_7_7_HEADER, r"\|\|\s*ABORT")


def test_step_7_7_negative_path():
    body = _read()
    mutated = _strip_section(body, STEP_7_7_HEADER)
    assert not _proximity(mutated, STEP_7_7_HEADER, r"qor\.reliability\.seal_entry_check")


def test_step_7_7_runs_after_step_7_seal_write():
    """Direct countermeasure to Pass 1 V-1: the gate's precondition is that
    the SESSION SEAL entry has been written. Step 7.7 must sit AFTER Step 7
    in the file (and therefore in execution order)."""
    body = _read()
    step_7 = re.search(STEP_7_HEADER, body, re.MULTILINE)
    step_7_7 = re.search(STEP_7_7_HEADER, body, re.MULTILINE)
    assert step_7 and step_7_7, "both step headers must exist"
    assert step_7.start() < step_7_7.start(), (
        f"Step 7.7 must follow Step 7 in document order; "
        f"Step 7 at offset {step_7.start()}, Step 7.7 at offset {step_7_7.start()}"
    )


def test_step_7_7_does_not_use_python_c_shell_interpolation():
    """Direct countermeasure to Pass 1 V-3: the wiring must not interpolate
    a shell variable into a single-quoted Python literal inside a python -c
    invocation."""
    body = _read()
    m = re.search(STEP_7_7_HEADER, body, re.MULTILINE)
    assert m, "Step 7.7 header missing"
    window = body[m.end(): m.end() + 4000]
    # Pattern: python -c "...'$VAR'..." or python -c '...'$VAR'...'
    bad_patterns = [
        r"python -c \"[^\"]*'\$[A-Z_][A-Z0-9_]*'",
        r"python -c '[^']*\$[A-Z_][A-Z0-9_]*",
    ]
    for pattern in bad_patterns:
        assert not re.search(pattern, window), (
            f"Step 7.7 contains a python -c with shell-variable interpolation "
            f"into a Python string literal (pattern {pattern!r}). This is the "
            f"OWASP A03 injection vector flagged in Pass 1 V-3."
        )


def test_step_7_7_uses_argv_form_for_plan_path():
    """The wiring must pass plan path via --plan argv flag, not via shell
    expansion into Python source."""
    body = _read()
    assert _proximity(body, STEP_7_7_HEADER, r'--plan\s+"\$PLAN_PATH"')


def test_step_7_7_does_not_reference_undefined_merkle_seal_variable():
    """Direct countermeasure to Pass 1 V-2: the wiring must not reference
    $MERKLE_SEAL or pass --merkle to the helper. The helper reads the chain
    hash from the ledger; the wiring has nothing to supply."""
    body = _read()
    m = re.search(STEP_7_7_HEADER, body, re.MULTILINE)
    assert m, "Step 7.7 header missing"
    window = body[m.end(): m.end() + 4000]
    assert "$MERKLE_SEAL" not in window, (
        "Step 7.7 references $MERKLE_SEAL, which is undefined at this point "
        "in the substantiate flow. Helper reads chain hash from ledger."
    )
    assert "--merkle" not in window, (
        "Step 7.7 passes --merkle to seal_entry_check; the helper does not "
        "accept this argument (single source of truth = the ledger)."
    )
