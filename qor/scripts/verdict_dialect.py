"""Shared audit-report field dialect (Phase 275; GH #424, GH #462).

Single source of truth for the accepted `**Verdict**` and `**Target**` forms in
`.agent/staging/AUDIT_REPORT.md`, consumed by ``qor.reliability.intent_lock``
and ``qor.scripts.verdict_reconcile``. Before this module those two gates read
the same file with different regexes and disagreed about what a PASS looks like
on 84 of 189 real reports -- one accepting a verdict the other could not see.

Two rules, both of which exist because of a specific failure:

**Agreement-required, not first-match.** A field's value is its value only when
every line stating it agrees. First-match lets a quoted example above the real
field outvote it; last-match lets a trailing appendix do the same. Measured over
204 historical reports, zero carry disagreeing verdict values and zero carry
more than one distinct target, so agreement-required refuses nothing that has
ever been written while closing the selection hole. Applied to BOTH fields:
`.agent/staging/` is not session-scoped, so a stale report survives
indefinitely and a superseded target line must not silently win.

**The guard is strictly wider than the reader.** ``LABEL_RE`` matches every line
``VALUE_RE`` can match and more, so a verdict-labeled line whose value does not
parse is reported as *unreadable* rather than dropped. This is the counterpart
of ``ledger_dialect.any_hash_label_present`` (GH #363) and exists for the same
reason: without it, "field absent" and "field present but unparseable" are
indistinguishable, and the latter is the dangerous one -- an unreadable line
cannot conflict, so a readable PASS elsewhere carries the report uncontested.

The value pattern therefore captures whatever word is present rather than an
enumeration of known verdicts (an enumeration silently ignores ``BLOCKED``), and
tolerates one trailing parenthetical qualifier, because ``## VERDICT: PASS (L1)``
is attested and a pattern that cannot read it makes it invisible rather than
refused. Nested, repeated or unbalanced parentheses do not parse and are
reported as unreadable, which is the fail-closed direction.

Note for report authors: these patterns are line-anchored and a fenced code
block does not exempt a line from them. A report quoting a verdict form must
indent it, or the whole report becomes unreadable and the gate refuses.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# One optional trailing parenthetical, no nesting. `[^()]*` rather than `[^)]*`
# so `PASS (a (b))` fails to parse instead of matching a prefix of it.
_QUALIFIER = r"(?:\s*\([^()]*\))?"

#: Reads a verdict line and captures its value. Case-sensitive on the value:
#: lowercase is an unneeded relaxation on the path that authorizes `capture`,
#: and the corpus vocabulary is uppercase throughout (PASS 232, VETO 14).
VALUE_RE = re.compile(
    r"^(?:#{1,6}[ \t]*)?[*_]*(?:Verdict|VERDICT)[*_]*\s*[:\-]\s*"
    rf"[*_]*([A-Z]+)[*_]*{_QUALIFIER}[*_]*\s*$",
    re.MULTILINE,
)

#: Detects that a line NAMES the verdict field, whatever follows. Deliberately
#: case-insensitive on the label word while VALUE_RE is not, so that a
#: lowercase label is unreadable rather than invisible.
LABEL_RE = re.compile(
    r"^(?:#{1,6}[ \t]*)?[*_]*(?i:verdict)[*_]*\s*[:\-]\s*\S",
    re.MULTILINE,
)

#: Reads a target line, tolerating surrounding backticks and one trailing
#: qualifier. 29 corpus reports write the path in backticks; capturing them
#: turns `report-unreadable` into `target-mismatch` -- a different finding code
#: and the same refusal.
TARGET_RE = re.compile(
    r"^\*\*Target\*\*\s*:\s*`?([^`\s]+)`?(?:[ \t]+.*)?$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class Verdict:
    """`value` is None whenever the report does not state exactly one readable
    verdict -- absent, conflicting, or unreadable alike.

    That invariant is the point: a consumer branching on the raw string stays
    correct without having to route through `is_pass`. A predicate whose safety
    depends on calling the right function is a defect waiting for the next
    caller.
    """

    value: str | None
    conflict: bool
    unreadable: bool
    values: tuple[str, ...]
    lines: tuple[str, ...]


@dataclass(frozen=True)
class Field:
    """The same shape for a single-valued text field. `value` is None when the
    field is absent or when its lines disagree."""

    value: str | None
    conflict: bool
    lines: tuple[str, ...]


def _labeled_lines(body: str) -> list[str]:
    return [line for line in body.splitlines() if LABEL_RE.match(line)]


def read_verdict(body: str) -> Verdict:
    """Parse every verdict-labeled line in `body` and agree them."""
    values = tuple(v.upper() for v in VALUE_RE.findall(body))
    lines = tuple(_labeled_lines(body))
    unreadable = any(not VALUE_RE.match(line) for line in lines)
    conflict = len(set(values)) > 1
    value = values[0] if (values and not conflict and not unreadable) else None
    return Verdict(
        value=value,
        conflict=conflict,
        unreadable=unreadable,
        values=values,
        lines=lines,
    )


def read_target(body: str) -> Field:
    """Parse every `**Target**` line in `body` and agree them."""
    values = tuple(TARGET_RE.findall(body))
    lines = tuple(
        line for line in body.splitlines() if line.lstrip().startswith("**Target**")
    )
    conflict = len(set(values)) > 1
    return Field(
        value=values[0] if (values and not conflict) else None,
        conflict=conflict,
        lines=lines,
    )


def is_pass(verdict: Verdict) -> bool:
    """True only for a report stating exactly one readable verdict, of PASS.

    Compares a string. It never truth-tests a container: a predicate returning
    a list of problems, consumed as `if not problems`, inverts on a non-empty
    list of vetoes and authorizes what it was meant to block.
    """
    return verdict.value == "PASS"


def unreadable_lines(verdict: Verdict) -> tuple[str, ...]:
    """The labeled lines whose value did not parse, for error messages."""
    return tuple(line for line in verdict.lines if not VALUE_RE.match(line))
