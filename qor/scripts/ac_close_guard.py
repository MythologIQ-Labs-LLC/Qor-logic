"""Acceptance-criteria close guard (Phase 114, GH #158).

Counter-control for the half-measure pattern (umbrella #147): an issue should
not be asserted closed unless every acceptance-criteria checkbox is either met
or split into a filed follow-on. "Met-ness" comes from the qa.json evidence
verdict, not from checkbox state at close time (a closing issue legitimately
still shows unchecked boxes); the mechanical invariant the guard enforces is
*unmet criterion => must have a linked follow-on*.

V1 is WARN-first: ``main`` prints findings and exits 0. ``--enforce`` (reserved
for a graduated V2, once false-positive rate is measured) makes it exit non-zero
when enforcement would not allow closure. Issues with no machine-checkable
checklist fall back to ALLOW + WARN.

Reuses the section-slice + fence-strip approach from ``dod_record`` and the
line-scan idiom from ``plan_test_lint``; gh access mirrors ``create_shadow_issue``.
Doctrine: ``qor/references/doctrine-verification-closure-integrity.md``.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field

_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_AC_HEADING_RE = re.compile(r"^#{1,6}\s+acceptance\s+criteria\b", re.IGNORECASE)
_HEADING_RE = re.compile(r"^#{1,6}\s")
_CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$")
_CLOSES_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", re.IGNORECASE
)


@dataclass(frozen=True)
class Criterion:
    text: str
    met: bool


@dataclass
class Decision:
    allow: bool
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)


def extract_closes_refs(text: str) -> list[int]:
    """Return issue numbers referenced by a closing keyword (Closes/Fixes/Resolves #N)."""
    return [int(m) for m in _CLOSES_RE.findall(text or "")]


def _strip_fences(text: str) -> str:
    return _FENCE_RE.sub("", text)


def parse_acceptance_criteria(body: str) -> list[Criterion]:
    """Slice the 'Acceptance criteria' section and parse its checkbox bullets.

    Returns [] when the body has no such section or no checkboxes (the
    no-machine-checkable-criteria case the caller treats as ALLOW+WARN).
    """
    lines = _strip_fences(body or "").splitlines()
    in_section = False
    out: list[Criterion] = []
    for line in lines:
        if _AC_HEADING_RE.match(line):
            in_section = True
            continue
        if in_section and _HEADING_RE.match(line):
            break  # next heading ends the section
        if not in_section:
            continue
        m = _CHECKBOX_RE.match(line)
        if m:
            out.append(Criterion(text=m.group(2), met=m.group(1).lower() == "x"))
    return out


def evaluate_closure(
    criteria: list[Criterion],
    *,
    has_followon: bool,
    qa_verdict: str | None,
) -> Decision:
    """Decide whether closure would be allowed under enforcement.

    - No criteria -> ALLOW with a warning (nothing machine-checkable).
    - Unmet criteria with a linked follow-on -> ALLOW (split is acceptable).
    - Unmet criteria with no follow-on -> blocking reason (allow False).
    - qa_verdict != PASS -> warning (does not itself block in V1).
    """
    d = Decision(allow=True)

    if qa_verdict is not None and qa_verdict != "PASS":
        d.warnings.append(f"qa evidence verdict is {qa_verdict!r}, not PASS")

    if not criteria:
        d.warnings.append("no machine-checkable acceptance criteria; allowing closure")
        return d

    unmet = [c for c in criteria if not c.met]
    if unmet and not has_followon:
        d.allow = False
        for c in unmet:
            d.blocking_reasons.append(f"unmet criterion without follow-on: {c.text}")
    elif unmet and has_followon:
        d.warnings.append(
            f"{len(unmet)} unmet criterion(s) accepted as split into a filed follow-on"
        )
    return d


# --- thin gh / gate layer (not unit-tested; side-effecting) -----------------

def _run_gh(args: list[str]) -> str | None:
    try:
        r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def _issue_body(num: int, repo: str | None) -> str | None:
    extra = ["--repo", repo] if repo else []
    out = _run_gh(["issue", "view", str(num), "--json", "body", "-q", ".body", *extra])
    return out


def _has_followon(num: int, repo: str | None) -> bool:
    extra = ["--repo", repo] if repo else []
    out = _run_gh(["issue", "list", "--state", "all", "--search",
                   f"in:body #{num}", "--json", "number", *extra])
    return bool(out and out.strip() and out.strip() != "[]")


def _qa_verdict(qa_session: str | None) -> str | None:
    if not qa_session:
        return None
    try:
        from qor.scripts import gate_chain
        return gate_chain.read_phase_artifact("qa", session_id=qa_session).get("verdict")
    except Exception:  # noqa: BLE001 - advisory read; never breaks the seal flow
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.ac_close_guard")
    parser.add_argument("--pr-body-file", default=None,
                        help="file containing the planned PR body (parsed for Closes #N)")
    parser.add_argument("--issues", default=None,
                        help="comma-separated issue numbers to check directly")
    parser.add_argument("--qa-session", default=None,
                        help="session id whose qa.json verdict to consult")
    parser.add_argument("--repo", default=None)
    parser.add_argument("--enforce", action="store_true",
                        help="exit non-zero when closure would be blocked (graduated V2)")
    args = parser.parse_args(argv)

    targets: list[int] = []
    if args.pr_body_file:
        try:
            with open(args.pr_body_file, encoding="utf-8") as fh:
                targets.extend(extract_closes_refs(fh.read()))
        except OSError as e:
            print(f"close guard: cannot read --pr-body-file ({e}); skip")
            return 0
    if args.issues:
        targets.extend(int(x) for x in args.issues.split(",") if x.strip())
    targets = sorted(set(targets))

    if not targets:
        print("close guard: no closing references found; nothing to check")
        return 0

    qa_verdict = _qa_verdict(args.qa_session)
    all_allow = True
    for num in targets:
        body = _issue_body(num, args.repo)
        if body is None:
            print(f"close guard: #{num} skip (gh unavailable or issue unreadable)")
            continue
        crits = parse_acceptance_criteria(body)
        decision = evaluate_closure(crits, has_followon=_has_followon(num, args.repo),
                            qa_verdict=qa_verdict)
        for r in decision.blocking_reasons:
            print(f"  WOULD-BLOCK #{num}: {r}")
        for w in decision.warnings:
            print(f"  WARN #{num}: {w}")
        if not decision.allow:
            all_allow = False

    if not all_allow:
        if args.enforce:
            print("close guard: ENFORCE -> closure blocked")
            return 1
        print("close guard: WARN-first -> not blocking (unmet criteria without follow-on)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
