"""Pure bounded governance-applicability resolver for GH #501.

V1 deliberately performs no retrieval, I/O, semantic search, policy mutation, or
authority inference. Callers provide a typed operation descriptor and explicit
source metadata. The resolver only decides which supplied sources apply and why.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


POSTURES = frozenset({"required", "advisory", "optional"})
FRESHNESS_STATES = frozenset({"current", "stale", "superseded"})
RESOLUTION_STATES = frozenset(
    {"required", "advisory", "optional", "excluded", "stale", "superseded", "ambiguous"}
)


@dataclass(frozen=True)
class OperationDescriptor:
    """Caller-supplied facts used for applicability resolution.

    No field is inferred from prose or retrieved content. In particular,
    ``authority_ceiling`` is an input fact, never a resolver output.
    """

    operation_id: str
    operation_type: str
    lifecycle_state: str
    artifact_type: str
    subsystem: str
    change_class: str
    environment_relevance: str
    authority_ceiling: str
    mutation_class: str
    external_visibility: str


@dataclass(frozen=True)
class ApplicabilityRule:
    """Exact-match predicates for one explicit applicability rule.

    Empty tuples mean that field is unconstrained. A GovernanceSource with no
    rules is intentionally *not* global; it is excluded as unclassified.
    """

    rule_id: str
    operation_types: tuple[str, ...] = ()
    lifecycle_states: tuple[str, ...] = ()
    artifact_types: tuple[str, ...] = ()
    subsystems: tuple[str, ...] = ()
    change_classes: tuple[str, ...] = ()
    environment_relevance: tuple[str, ...] = ()
    authority_ceilings: tuple[str, ...] = ()
    mutation_classes: tuple[str, ...] = ()
    external_visibility: tuple[str, ...] = ()

    def matches(self, operation: OperationDescriptor) -> bool:
        checks = (
            (self.operation_types, operation.operation_type),
            (self.lifecycle_states, operation.lifecycle_state),
            (self.artifact_types, operation.artifact_type),
            (self.subsystems, operation.subsystem),
            (self.change_classes, operation.change_class),
            (self.environment_relevance, operation.environment_relevance),
            (self.authority_ceilings, operation.authority_ceiling),
            (self.mutation_classes, operation.mutation_class),
            (self.external_visibility, operation.external_visibility),
        )
        return all(not allowed or actual in allowed for allowed, actual in checks)


@dataclass(frozen=True)
class GovernanceSource:
    """Metadata for one governance source considered by the resolver.

    ``precedence`` is explicit metadata; larger values outrank smaller values
    only within the same ``rule_key``. The resolver never invents precedence.

    ``rule_key`` and ``decision_token`` provide a minimal, explicit conflict
    surface. Two current applicable sources at the same highest precedence for
    the same non-empty rule key are ambiguous when their decision tokens differ.
    An empty rule key means the source is additive and is not conflict-ranked.
    """

    stable_id: str
    source_class: str
    authority_class: str
    precedence: int
    posture: str
    freshness_state: str
    rules: tuple[ApplicabilityRule, ...]
    rule_key: str = ""
    decision_token: str = ""
    superseded_by: str = ""

    def __post_init__(self) -> None:
        if self.posture not in POSTURES:
            raise ValueError(f"invalid posture: {self.posture}")
        if self.freshness_state not in FRESHNESS_STATES:
            raise ValueError(f"invalid freshness_state: {self.freshness_state}")
        if self.freshness_state == "superseded" and not self.superseded_by:
            raise ValueError("superseded source must name superseded_by")


@dataclass(frozen=True)
class Resolution:
    stable_id: str
    source_class: str
    authority_class: str
    disposition: str
    precedence: int
    matched_rule_ids: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.disposition not in RESOLUTION_STATES:
            raise ValueError(f"invalid disposition: {self.disposition}")


@dataclass(frozen=True)
class GovernancePacket:
    operation_id: str
    resolutions: tuple[Resolution, ...]

    def by_disposition(self, disposition: str) -> tuple[Resolution, ...]:
        if disposition not in RESOLUTION_STATES:
            raise ValueError(f"invalid disposition: {disposition}")
        return tuple(r for r in self.resolutions if r.disposition == disposition)


@dataclass(frozen=True)
class _Candidate:
    source: GovernanceSource
    matched_rule_ids: tuple[str, ...]


def _match_source(
    operation: OperationDescriptor,
    source: GovernanceSource,
) -> tuple[str, tuple[str, ...], str] | _Candidate:
    if not source.rules:
        return "excluded", (), "no-applicability-rules"

    matched = tuple(sorted(rule.rule_id for rule in source.rules if rule.matches(operation)))
    if not matched:
        considered = ",".join(sorted(rule.rule_id for rule in source.rules))
        return "excluded", (), f"no-rule-match:{considered}"

    if source.freshness_state == "stale":
        return "stale", matched, "applicable-source-is-stale"
    if source.freshness_state == "superseded":
        return "superseded", matched, f"superseded-by:{source.superseded_by}"

    return _Candidate(source=source, matched_rule_ids=matched)


def resolve_packet(
    operation: OperationDescriptor,
    sources: Iterable[GovernanceSource],
) -> GovernancePacket:
    """Resolve an operation against supplied governance metadata.

    The function is deterministic and pure. It records negative evidence for
    excluded sources, refuses to rank through same-precedence conflicts, and
    never creates authority or upgrades a source's declared posture.
    """

    ordered_sources = tuple(sorted(sources, key=lambda source: source.stable_id))
    ids = tuple(source.stable_id for source in ordered_sources)
    if len(ids) != len(set(ids)):
        raise ValueError("governance source stable_id values must be unique")

    resolved: dict[str, Resolution] = {}
    candidates: list[_Candidate] = []

    for source in ordered_sources:
        result = _match_source(operation, source)
        if isinstance(result, _Candidate):
            candidates.append(result)
            continue
        disposition, matched, reason = result
        resolved[source.stable_id] = Resolution(
            stable_id=source.stable_id,
            source_class=source.source_class,
            authority_class=source.authority_class,
            disposition=disposition,
            precedence=source.precedence,
            matched_rule_ids=matched,
            reason=reason,
        )

    additive = [candidate for candidate in candidates if not candidate.source.rule_key]
    ranked: dict[str, list[_Candidate]] = {}
    for candidate in candidates:
        if candidate.source.rule_key:
            ranked.setdefault(candidate.source.rule_key, []).append(candidate)

    for candidate in additive:
        source = candidate.source
        resolved[source.stable_id] = Resolution(
            stable_id=source.stable_id,
            source_class=source.source_class,
            authority_class=source.authority_class,
            disposition=source.posture,
            precedence=source.precedence,
            matched_rule_ids=candidate.matched_rule_ids,
            reason="applicable-additive-source",
        )

    for rule_key in sorted(ranked):
        group = ranked[rule_key]
        highest = max(candidate.source.precedence for candidate in group)
        winners = [candidate for candidate in group if candidate.source.precedence == highest]
        losers = [candidate for candidate in group if candidate.source.precedence < highest]

        for candidate in losers:
            source = candidate.source
            resolved[source.stable_id] = Resolution(
                stable_id=source.stable_id,
                source_class=source.source_class,
                authority_class=source.authority_class,
                disposition="excluded",
                precedence=source.precedence,
                matched_rule_ids=candidate.matched_rule_ids,
                reason=f"shadowed-by-higher-precedence:{rule_key}:{highest}",
            )

        tokens = {candidate.source.decision_token for candidate in winners}
        conflict = len(winners) > 1 and len(tokens) > 1
        for candidate in winners:
            source = candidate.source
            if conflict:
                disposition = "ambiguous"
                reason = f"same-precedence-conflict:{rule_key}:{highest}"
            else:
                disposition = source.posture
                reason = f"applicable-precedence-winner:{rule_key}:{highest}"
            resolved[source.stable_id] = Resolution(
                stable_id=source.stable_id,
                source_class=source.source_class,
                authority_class=source.authority_class,
                disposition=disposition,
                precedence=source.precedence,
                matched_rule_ids=candidate.matched_rule_ids,
                reason=reason,
            )

    return GovernancePacket(
        operation_id=operation.operation_id,
        resolutions=tuple(resolved[source_id] for source_id in sorted(resolved)),
    )
