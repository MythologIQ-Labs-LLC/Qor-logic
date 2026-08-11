"""Phase 217 (GH #314): the skill-corpus digest recorded at seal.

Across 543 ledger entries nothing answers "which skills ran this seal?". That
absence is why install drift compounds: it is invisible retroactively as well
as prospectively. One digest over the installed SKILL.md set makes every
future seal attributable to the ceremony that produced it.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import skill_corpus


def _install(base: Path, names: list[str]) -> Path:
    skills = base / ".claude" / "skills"
    for name in names:
        d = skills / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"# {name}\nbody\n", encoding="utf-8")
    return skills


NAMES = ["qor-plan", "qor-audit", "qor-implement"]


def test_digest_changes_when_a_skill_changes(tmp_path: Path, monkeypatch):
    """A one-byte change to any installed skill changes the corpus digest."""
    skills = _install(tmp_path, NAMES)
    monkeypatch.chdir(tmp_path)

    before = skill_corpus.digest(host="claude", scope="repo")
    assert before is not None

    target = skills / "qor-audit" / "SKILL.md"
    target.write_text(target.read_text(encoding="utf-8") + "x", encoding="utf-8")

    after = skill_corpus.digest(host="claude", scope="repo")
    assert after != before, "digest must change when the corpus changes"


def test_digest_is_order_independent(tmp_path: Path, monkeypatch):
    """Directory iteration order is not guaranteed; the digest must not depend on it."""
    skills = _install(tmp_path, NAMES)
    monkeypatch.chdir(tmp_path)
    first = skill_corpus.digest(host="claude", scope="repo")

    # Rebuild the same corpus in a different creation order.
    for name in NAMES:
        (skills / name / "SKILL.md").unlink()
        (skills / name).rmdir()
    for name in reversed(NAMES):
        d = skills / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"# {name}\nbody\n", encoding="utf-8")

    assert skill_corpus.digest(host="claude", scope="repo") == first


def test_digest_absent_install_is_disclosed(tmp_path: Path, monkeypatch):
    """No install must be distinguishable from a real corpus.

    A hash over an empty set is a real hash and would read as evidence of a
    ceremony that never existed. Absence returns None so callers must handle
    it explicitly.
    """
    monkeypatch.chdir(tmp_path)
    assert skill_corpus.digest(host="claude", scope="repo") is None


def test_digest_is_stable_across_calls(tmp_path: Path, monkeypatch):
    """An unchanged corpus digests identically -- no timestamp or path leakage."""
    _install(tmp_path, NAMES)
    monkeypatch.chdir(tmp_path)

    assert skill_corpus.digest(host="claude", scope="repo") == \
        skill_corpus.digest(host="claude", scope="repo")


def test_digest_ignores_absolute_path_of_the_install(tmp_path: Path, monkeypatch):
    """Two identical corpora at different locations digest the same.

    The digest identifies the ceremony's content, not where it happens to sit,
    so a seal produced on one machine is comparable to a seal on another.
    """
    a = tmp_path / "a"
    b = tmp_path / "b"
    _install(a, NAMES)
    _install(b, NAMES)

    monkeypatch.chdir(a)
    da = skill_corpus.digest(host="claude", scope="repo")
    monkeypatch.chdir(b)
    db = skill_corpus.digest(host="claude", scope="repo")

    assert da == db
