"""LiveProgressInvariant detector (Phase 127; GH #156 / SG-FakeProgress-A).

Mechanical form of the Phase 74 Ghost-UI Live-Progress sub-rule deferred at #58.
Lexical scan over a target repo's frontend source for the fake-progress patterns:

  fake-jump            -- a progress width jumps start (0/0%) -> end (100/100%)
                          with no intermediate width write between.
  no-event-subscription-- a progress element writes width but the file never
                          subscribes to a backing event stream.
  error-no-dismiss     -- an error/catch branch touches progress UI with no
                          dismiss/retry/close control.

Backend-only repos (no frontend files) are a no-op. Inline `// qor:live-progress-ok`
suppresses a file. WARN-only at `/qor-audit` Step 0.6; the binding VETO stays the
Ghost-UI pass.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

KNOWN_FINDING_KINDS = ("fake-jump", "no-event-subscription", "error-no-dismiss")
_FRONTEND_GLOBS = ("**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx")
_SUPPRESS = "qor:live-progress-ok"

_WIDTH_RE = re.compile(r"width\s*[:=]\s*[`'\"]?(\d+)\s*%", re.IGNORECASE)
_SUBSCRIBE_RE = re.compile(
    r"addEventListener|\.on\(|onmessage|EventSource|\.subscribe\(|new WebSocket",
    re.IGNORECASE,
)
_ERROR_BRANCH_RE = re.compile(r"\bcatch\s*\(|\.catch\(|showError|onError", re.IGNORECASE)
_DISMISS_RE = re.compile(r"dismiss|retry|\.close\(|closeBtn|onclick|onClick", re.IGNORECASE)


@dataclass(frozen=True)
class ProgressFinding:
    kind: str
    file: str
    detail: str


def detect_fake_jump(text: str) -> bool:
    values = [int(m.group(1)) for m in _WIDTH_RE.finditer(text)]
    if 0 not in values or 100 not in values:
        return False
    first_zero = values.index(0)
    last_hundred = len(values) - 1 - values[::-1].index(100)
    if last_hundred <= first_zero:
        return False
    between = values[first_zero + 1:last_hundred]
    return not any(0 < v < 100 for v in between)


def scan_text(text: str, file: str = "<text>") -> list[ProgressFinding]:
    if _SUPPRESS in text:
        return []
    findings: list[ProgressFinding] = []
    has_progress = bool(_WIDTH_RE.search(text))

    if detect_fake_jump(text):
        findings.append(ProgressFinding(
            "fake-jump", file,
            "progress width jumps 0% -> 100% with no intermediate write",
        ))
    if has_progress and not _SUBSCRIBE_RE.search(text):
        findings.append(ProgressFinding(
            "no-event-subscription", file,
            "progress UI writes width but never subscribes to a backing event stream",
        ))
    if (has_progress and _ERROR_BRANCH_RE.search(text)
            and not _DISMISS_RE.search(text)):
        findings.append(ProgressFinding(
            "error-no-dismiss", file,
            "error/catch branch touches progress UI with no dismiss/retry/close control",
        ))
    return findings


def scan_repo(base: Path) -> list[ProgressFinding]:
    findings: list[ProgressFinding] = []
    seen: set[Path] = set()
    for glob in _FRONTEND_GLOBS:
        for path in base.glob(glob):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = path.relative_to(base).as_posix()
            findings.extend(scan_text(text, file=rel))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="plan_live_progress_lint")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)

    findings = scan_repo(Path(args.repo_root))
    if not findings:
        return 0
    for f in findings:
        print(f"[live-progress-fake] {f.kind} {f.file}: {f.detail}")
    print(f"plan_live_progress_lint: {len(findings)} finding(s)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
