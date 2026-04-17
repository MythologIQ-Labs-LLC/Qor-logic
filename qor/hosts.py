"""Host-to-install-path resolver for qorlogic CLI.

Maps AI coding host names to filesystem targets for skill/agent installation.
Extensible via ``register_host()`` for third-party hosts (Cursor, Continue,
Windsurf, Aider).

Phase 24: uniform scope model. Scope is either 'repo' (default) or 'global'.
- repo: base = $QORLOGIC_PROJECT_DIR or Path.cwd(), joined with .<host>/
- global: base = Path.home() / .<host>/

CLAUDE_PROJECT_DIR is no longer consulted. Use QORLOGIC_PROJECT_DIR to override
the repo root.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class HostTarget:
    """Install target for a specific AI coding host.

    install_map keys are source-path prefixes (e.g. "skills/", "agents/",
    "commands/"). The install dispatcher uses the prefix to route each manifest
    entry into its target directory. skills_dir and agents_dir are convenience
    properties for the common claude/codex/kilo-code layout.
    """
    name: str
    base: Path
    install_map: dict[str, Path]

    @property
    def skills_dir(self) -> Path:
        return self.install_map["skills/"]

    @property
    def agents_dir(self) -> Path:
        return self.install_map["agents/"]


_VALID_SCOPES = frozenset({"repo", "global"})


def _repo_root() -> Path:
    override = os.environ.get("QORLOGIC_PROJECT_DIR")
    return Path(override) if override else Path.cwd()


def _scoped_base(host_dirname: str, scope: str) -> Path:
    if scope == "global":
        return Path.home() / host_dirname
    return _repo_root() / host_dirname


def _skills_agents_map(base: Path) -> dict[str, Path]:
    return {"skills/": base / "skills", "agents/": base / "agents"}


def _claude_target(scope: str = "repo") -> HostTarget:
    base = _scoped_base(".claude", scope)
    return HostTarget(name="claude", base=base, install_map=_skills_agents_map(base))


def _kilo_target(scope: str = "repo") -> HostTarget:
    base = _scoped_base(".kilo-code", scope)
    return HostTarget(name="kilo-code", base=base, install_map=_skills_agents_map(base))


def _codex_target(scope: str = "repo") -> HostTarget:
    base = _scoped_base(".codex", scope)
    return HostTarget(name="codex", base=base, install_map=_skills_agents_map(base))


def _gemini_target(scope: str = "repo") -> HostTarget:
    base = _scoped_base(".gemini", scope)
    return HostTarget(
        name="gemini",
        base=base,
        install_map={"commands/": base / "commands"},
    )


_HOSTS: dict[str, Callable[[str], HostTarget]] = {
    "claude": _claude_target,
    "kilo-code": _kilo_target,
    "codex": _codex_target,
    "gemini": _gemini_target,
}


def register_host(name: str, factory: Callable[..., HostTarget]) -> None:
    """Register a third-party host factory. Factory signature: ``(scope: str) -> HostTarget``.

    Legacy zero-arg factories are accepted; callers may ignore the scope argument.
    """
    _HOSTS[name] = factory


def resolve(
    host_name: str,
    scope: str = "repo",
    target_override: Path | None = None,
) -> HostTarget:
    """Resolve a host name + scope to a HostTarget.

    If ``target_override`` is set, the base is that path and install_map is
    built on it (scope is ignored for base, but still influences future host-
    specific logic if factories choose to consult it).
    """
    if scope not in _VALID_SCOPES:
        raise ValueError(f"invalid scope: {scope!r} (expected 'repo' or 'global')")

    factory = _HOSTS.get(host_name)
    if factory is None:
        raise ValueError(f"unknown host: {host_name!r}")

    if target_override is not None:
        base = target_override
        # Gemini and future hosts may need a different install_map; delegate
        # the shape to the factory, then replace its base.
        sample = factory(scope)
        remapped = {
            prefix: base / dst.relative_to(sample.base)
            for prefix, dst in sample.install_map.items()
        }
        return HostTarget(name=sample.name, base=base, install_map=remapped)

    return factory(scope)
