"""Phase 56: secret-scanning gate. Closes OWASP LLM06 + AI 600-1 §2.10.

Wired into ``/qor-substantiate`` Step 4.6.5 to BLOCK seal commits containing
detected secrets. Drives the long-dormant Cedar `has_hardcoded_secrets`
attribute (rule on books since Phase 23). Zero new runtime deps; output
follows gitleaks v8 schema for downstream tool compatibility.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Pattern:
    name: str
    regex: re.Pattern[str]
    severity: int
    description: str


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    pattern_name: str
    severity: int
    matched_text_redacted: str


PATTERNS: tuple[Pattern, ...] = (
    Pattern("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}"), 3,
            "AWS access key ID"),
    Pattern("github-pat-classic", re.compile(r"ghp_[A-Za-z0-9]{36}"), 3,
            "GitHub personal access token (classic)"),
    Pattern("github-pat-finegrained",
            re.compile(r"github_pat_[A-Za-z0-9_]{82}"), 3,
            "GitHub personal access token (fine-grained)"),
    Pattern("github-oauth", re.compile(r"gho_[A-Za-z0-9]{36}"), 3,
            "GitHub OAuth access token"),
    Pattern("private-key-header",
            re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
            3, "Private key PEM header"),
    Pattern("stripe-live", re.compile(r"sk_live_[A-Za-z0-9]{24,}"), 3,
            "Stripe live secret key"),
    Pattern("slack-token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), 3,
            "Slack token"),
    Pattern("google-api-key", re.compile(r"AIza[A-Za-z0-9_\-]{35}"), 3,
            "Google API key"),
    Pattern("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{90,}"), 3,
            "Anthropic API key"),
    Pattern("generic-high-entropy-assignment",
            re.compile(r'(?i)(?:secret|token|api_key|password|access_key)'
                       r'\w*\s*=\s*["\'][A-Za-z0-9/+=_\-]{20,}["\']'),
            2, "Generic secret-like assignment"),
    Pattern("private-key-url",
            re.compile(r"https?://[^:/\s]+:[^@\s]{8,}@"), 2,
            "URL with embedded credentials"),
)


_ALLOWLIST: frozenset[str] = frozenset({
    "YOUR_API_KEY_HERE",
    "REDACTED",
    "EXAMPLE_SECRET",
    "AKIAIOSFODNN7EXAMPLE",
    "claude-opus-4-7",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "ai_provenance",
    "permitted_tools",
    "permitted_subagents",
    "model_compatibility",
    "min_model_capability",
    "OverrideFrictionRequired",
    "compute_skill_admission_attributes",
    # Per-line opt-out for test fixtures and worked examples; scanner skips
    # any line containing this literal token. Mirrors flake8 ``# noqa`` idiom.
    "noqa: secret-scan",
})


_FENCED_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_INLINE_RE = re.compile(r"`[^`\n]*`")


def mask_code_blocks(content: str) -> str:
    """Replace fenced + inline code spans with whitespace, preserving newlines.

    Mirrors ``qor.scripts.prompt_injection_canaries.mask_code_blocks``. Used
    for documentation scanning where worked examples should not flag.
    """
    masked = _FENCED_RE.sub(lambda m: " " * len(m.group(0)), content)
    masked = _INLINE_RE.sub(lambda m: " " * len(m.group(0)), masked)
    return masked


def _redact(match: str) -> str:
    if len(match) < 6:
        return "..." + match[-2:] if len(match) >= 2 else "..."
    return f"{match[:4]}...{match[-2:]}"


def _is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:8192]
    except OSError:
        return True
    return b"\x00" in chunk


def _line_is_allowlisted(line: str) -> bool:
    return any(token in line for token in _ALLOWLIST)


def scan_text(content: str, file: str = "<text>") -> list[Finding]:
    findings: list[Finding] = []
    for line_num, line in enumerate(content.splitlines(), start=1):
        if _line_is_allowlisted(line):
            continue
        for pattern in PATTERNS:
            m = pattern.regex.search(line)
            if not m:
                continue
            findings.append(Finding(
                file=file,
                line=line_num,
                pattern_name=pattern.name,
                severity=pattern.severity,
                matched_text_redacted=_redact(m.group(0)),
            ))
    return findings


def scan(path: Path, *, mask_blocks: bool | None = None) -> list[Finding]:
    if _is_binary(path):
        return []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    # Default behavior: mask code blocks for markdown sources (documentation
    # context where worked examples appear in fences/backticks). Pure source
    # files (Python, etc.) scan unmasked. Operator override via mask_blocks.
    if mask_blocks is None:
        mask_blocks = path.suffix.lower() in (".md", ".markdown")
    if mask_blocks:
        content = mask_code_blocks(content)
    return scan_text(content, file=str(path))


def scan_paths(paths: list[Path]) -> list[Finding]:
    out: list[Finding] = []
    for p in paths:
        if not p.exists():
            continue
        out.extend(scan(p))
    return out


def scan_staged(repo_root: Path) -> list[Finding]:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
        cwd=str(repo_root), capture_output=True, text=True,
    )
    if getattr(proc, "returncode", 0) != 0:
        return []
    stdout = getattr(proc, "stdout", "") or ""
    paths = [repo_root / line for line in stdout.splitlines() if line.strip()]
    return scan_paths(paths)


def to_gitleaks_json(findings: list[Finding]) -> list[dict]:
    out: list[dict] = []
    pattern_index = {p.name: p for p in PATTERNS}
    for f in findings:
        desc = pattern_index[f.pattern_name].description if f.pattern_name in pattern_index else f.pattern_name
        out.append({
            "Description": desc,
            "RuleID": f.pattern_name,
            "File": f.file,
            "Line": f.line,
            "Match": f.matched_text_redacted,
            "Secret": f.matched_text_redacted,
            "Tags": [f"severity:{f.severity}"],
        })
    return out


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="qor.scripts.secret_scanner")
    p.add_argument("--staged", action="store_true")
    p.add_argument("--files", nargs="+", default=[])
    p.add_argument("--out", default=None)
    p.add_argument("--repo-root", default=".")
    p.add_argument("--mask-blocks", action="store_true",
                   help="Mask fenced/inline code spans before scanning "
                        "(use for markdown documentation self-application).")
    return p


def _validate_files(paths: list[Path]) -> int | None:
    for p in paths:
        if not p.exists():
            sys.stderr.write(f"ERROR: file not found: {p}\n")
            return 2
    return None


def _write_findings(out_path: Path, findings: list[Finding]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(to_gitleaks_json(findings), indent=2),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    if args.staged:
        findings = scan_staged(Path(args.repo_root))
    elif args.files:
        paths = [Path(p) for p in args.files]
        rc = _validate_files(paths)
        if rc is not None:
            return rc
        # mask_blocks: None=auto-detect by suffix; True=force; we don't expose
        # explicit-False from CLI (use --files on a .md to keep auto-detect).
        force = True if args.mask_blocks else None
        findings = []
        for p in paths:
            findings.extend(scan(p, mask_blocks=force))
    else:
        sys.stderr.write("usage: --staged | --files PATH...\n")
        return 2

    if args.out:
        _write_findings(Path(args.out), findings)

    if findings:
        sys.stderr.write(f"BLOCK: {len(findings)} secret-scan finding(s)\n")
        for f in findings:
            sys.stderr.write(
                f"  {f.file}:{f.line} [{f.pattern_name}] {f.matched_text_redacted}\n"
            )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
