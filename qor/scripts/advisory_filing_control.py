"""Advisory boundary control for the outbound filing path (Phase 286).

`create_shadow_issue` composes a GitHub issue body from shadow events and hands
it to `gh`. This module inspects what is about to be sent, reports what it
found, and records a line when it found anything. It never prevents the filing.

Three properties carry the design, and each exists because a blocking
predecessor failed on it:

* **Advisory, structurally.** `inspect` never raises. Its whole body is wrapped
  and any exception yields an empty report carrying the `control-error` class,
  because a control whose purpose is to observe must not become the reason a
  report cannot be filed. The breadth of that catch is the accepted cost; the
  `control-error` class is what keeps it from hiding anything.

* **Identity is anchored on the event source.** The terms are derived from the
  directory the log was read from, so the repository whose events composed the
  body and the repository whose identity is matched against it cannot diverge.

* **The record is not a shadow event.** `gate_override` is the only event type
  carrying a raising override-friction escalator, so recording there would let
  this control refuse a filing at the third occurrence -- and would corrupt the
  population `override_friction.check` reads. The record is a JSONL line beside
  the log instead.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from qor.scripts.publication_boundary_lint import _ALLOW_RE, _load_terms, scan_text

#: Appended beside the log the events were read from; gitignored.
RECORD_REL = Path(".qor") / "advisory" / "filing-observations.jsonl"
OVERLAY_REL = Path(".qor") / "private" / "boundary-terms.txt"

_REMOTE_RE = re.compile(r"[:/](?P<owner>[\w.-]+)/(?P<name>[\w.-]+?)(?:\.git)?/?$")

#: Finding prefixes emitted by `scan_text`, mapped to the class recorded.
_CLASS_BY_MARKER = (
    ("identity term:", "identity-term"),
    ("absolute local path:", "absolute-path"),
    ("foreign repository URL:", "foreign-url"),
    ("cross-repo issue shape:", "cross-repo-issue"),
)


@dataclass(frozen=True)
class AdvisoryReport:
    """What a filing would publish. Never an instruction to stop."""

    findings: tuple[str, ...]
    classes: tuple[str, ...]
    unscanned_lines: int

    def render(self) -> str:
        """Operator-local text. Carries the matched detail; the record does not."""
        if not self.findings and not self.unscanned_lines:
            return ""
        out = [f"advisory_filing_control: {len(self.findings)} finding(s)"]
        out += [f"  {f}" for f in self.findings]
        if self.unscanned_lines:
            out.append(
                f"  note: {self.unscanned_lines} line(s) carried a boundary-lint "
                "suppression marker and were not scanned"
            )
        return "\n".join(out)


def origin_pair(root: Path) -> str | None:
    """`owner/name` from `origin`, scheme and `.git` stripped, or None.

    A retained `.git` suffix would match no destination, so every self-run would
    report -- which is why this is a named function with its own test rather
    than an inline parse.

    Git being unavailable is NOT swallowed here. It propagates to `inspect`'s
    wrap and surfaces as `control-error`, because a scan that lost two of its
    three derived terms must not be indistinguishable from a clean one.
    """
    result = subprocess.run(
        ["git", "-C", str(root), "remote", "get-url", "origin"],
        capture_output=True, text=True, timeout=5,
    )
    if result.returncode != 0:
        # No remote configured. A normal state, not a degraded scan: the
        # directory name still identifies the checkout.
        return None
    match = _REMOTE_RE.search(result.stdout.strip())
    if match is None:
        return None
    return f"{match.group('owner')}/{match.group('name')}"


def identity_terms(root: Path, overlay: Path | None = None) -> list[str]:
    """Terms naming this checkout: origin owner and name, the directory name,
    and the operator's overlay.

    The overlay defaults beside the checkout, mirroring
    `publication_boundary_lint`'s own fallback, because a consuming repository
    will not have one and a control that required it would report nothing there.
    """
    terms: set[str] = set()
    pair = origin_pair(root)
    if pair:
        owner, name = pair.split("/", 1)
        terms.update({owner, name})
    if root.name:
        terms.add(root.name)
    terms.update(_load_terms(overlay if overlay is not None else root / OVERLAY_REL))
    return sorted(t for t in terms if t)


def _derived_terms(root: Path) -> list[str]:
    terms: set[str] = set()
    pair = origin_pair(root)
    if pair:
        owner, name = pair.split("/", 1)
        terms.update({owner, name})
    if root.name:
        terms.add(root.name)
    return sorted(terms)


def _classes_for(findings: list[str]) -> tuple[str, ...]:
    seen: list[str] = []
    for finding in findings:
        for marker, klass in _CLASS_BY_MARKER:
            if marker in finding and klass not in seen:
                seen.append(klass)
    return tuple(seen)


def inspect(
    title: str,
    body: str,
    *,
    log_path: Path,
    destination: str,
    overlay: Path | None = None,
) -> AdvisoryReport:
    """Report what this filing would publish. Never raises.

    The anchor is `log_path.parent.parent` -- the directory the events were read
    from -- so terms and events cannot come from different repositories.

    Derived terms are dropped when the anchor's origin pair equals
    `destination`: naming the repository a report is filed *into* is permitted.
    Overlay terms are never dropped; they are operator-declared and may name a
    party the checkout cannot describe. The comparison is on the whole pair,
    never the name alone, so a fork filing upstream still reports its own name.

    Marker-bearing lines are counted before scanning and disclosed rather than
    honoured: that marker records a maintainer's exception in a tracked file and
    carries no authority over text arriving from a consumer's event log.
    """
    try:
        anchor = log_path.parent.parent
        overlay_terms = _load_terms(
            overlay if overlay is not None else anchor / OVERLAY_REL
        )
        derived = _derived_terms(anchor)
        if origin_pair(anchor) == destination:
            derived = []

        terms = sorted(set(derived) | set(overlay_terms))
        unscanned = sum(
            1 for line in (title + "\n" + body).splitlines() if _ALLOW_RE.search(line)
        )
        findings = scan_text("title", title, terms) + scan_text("body", body, terms)
        return AdvisoryReport(
            findings=tuple(findings),
            classes=_classes_for(findings),
            unscanned_lines=unscanned,
        )
    except Exception as exc:  # noqa: BLE001 -- see module docstring
        return AdvisoryReport(
            findings=(f"[advisory] control error: {type(exc).__name__}",),
            classes=("control-error",),
            unscanned_lines=0,
        )


def _append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def record(report: AdvisoryReport, *, anchor: Path, destination: str) -> None:
    """Append one calibration line when the report carried findings.

    Classes only, never the matched text: this file is durable, and writing the
    matched identity into it would persist exactly what the control exists to
    notice. A clean report records nothing, so the file remains usable as a rate.
    """
    if not report.findings:
        return
    try:
        _append_line(anchor / RECORD_REL, json.dumps({
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "destination": destination,
            "count": len(report.findings),
            "classes": list(report.classes),
            "unscanned_lines": report.unscanned_lines,
        }, sort_keys=True))
    except Exception:  # noqa: BLE001 -- recording must not block a filing either
        pass
