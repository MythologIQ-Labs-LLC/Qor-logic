"""Gemini CLI variant emitter.

Renders skills and agents into TOML command files suitable for Gemini CLI's
``commands/<name>.toml`` layout. Frontmatter parsing uses ``yaml.safe_load``
exclusively; unsafe APIs (``yaml.load``, ``yaml.load_all``, ``yaml.full_load``,
``yaml.unsafe_load``) are banned by
``tests/test_yaml_safe_load_discipline.py``.

TOML output is produced by vanilla string templating -- no third-party writer
(``tomli_w`` etc.). Round-trip is validated by
``tests/test_dist_compile_gemini.py``.
"""
from __future__ import annotations

from pathlib import Path

from yaml import safe_load

_GEMINI_EXTRAS = ("trigger", "phase", "persona")


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from body. Returns (meta, body)."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[end + 5:]
    meta = safe_load(raw) or {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, body


def _derive_description(meta: dict, body: str) -> str:
    desc = meta.get("description")
    if desc:
        return str(desc).strip()[:200]
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:200]
    return ""


def _toml_basic(value: str) -> str:
    """Render a TOML basic string (double-quoted, escaped)."""
    out: list[str] = []
    for ch in value:
        code = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif code < 0x20:
            out.append(f"\\u{code:04X}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _toml_multiline(body: str) -> str:
    """Render a TOML multi-line basic string.

    TOML multi-line basic strings process backslash escapes. Every literal
    backslash must become ``\\\\``, and any ``\"\"\"`` sequence in the body
    must be escaped as ``\\"\\"\\"`` so the delimiter is not consumed early.
    The leading newline after the opening ``\"\"\"`` is stripped by the parser,
    so we always inject one and the body's first character is preserved.
    """
    escaped = body.replace("\\", "\\\\")
    escaped = escaped.replace('"""', '\\"\\"\\"')
    return '"""\n' + escaped + '"""'


def render_gemini_command(
    name: str,
    description: str,
    prompt_body: str,
    extras: dict | None = None,
) -> str:
    """Render a single Gemini command TOML file. Pure function."""
    lines = [f"description = {_toml_basic(description)}"]
    if extras:
        for key in _GEMINI_EXTRAS:
            value = extras.get(key)
            if value is not None and value != "":
                lines.append(f"{key} = {_toml_basic(str(value))}")
    lines.append(f"prompt = {_toml_multiline(prompt_body)}")
    return "\n".join(lines) + "\n"


def _emit_one(source_path: Path, name: str, out_dir: Path) -> Path:
    text = source_path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    description = _derive_description(meta, body)
    extras = {k: meta.get(k) for k in _GEMINI_EXTRAS}
    content = render_gemini_command(name, description, body, extras)
    dst = out_dir / f"{name}.toml"
    dst.write_text(content, encoding="utf-8")
    return dst


def emit_gemini(
    skills_dirs: list[Path],
    loose_skills: list[Path],
    agents: list[Path],
    out: Path,
) -> None:
    commands_root = out / "commands"
    commands_root.mkdir(parents=True, exist_ok=True)
    for skill_dir in skills_dirs:
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            _emit_one(skill_md, skill_dir.name, commands_root)
    for loose in loose_skills:
        _emit_one(loose, loose.stem, commands_root)
    for agent in agents:
        _emit_one(agent, f"agent-{agent.stem}", commands_root)
