from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.disaster_control import DisasterAssessment, DisasterFinding, DisasterSnapshot, assess_disaster


class DisasterDependencyLink(BaseModel):
    link_id: str
    upstream_need_id: str
    downstream_need_id: str
    relation: Literal["blocks", "degrades"] = "blocks"
    mechanism: str
    source_ref: str
    verification_status: Literal["reported", "corroborated", "verified"] = "reported"
    observed_at: datetime
    valid_until: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_link(self) -> "DisasterDependencyLink":
        if self.upstream_need_id == self.downstream_need_id:
            raise ValueError("dependency link cannot point a need to itself")
        if self.observed_at.tzinfo is None:
            raise ValueError("dependency observed_at must be timezone-aware")
        if self.valid_until is not None:
            if self.valid_until.tzinfo is None:
                raise ValueError("dependency valid_until must be timezone-aware")
            if self.valid_until < self.observed_at:
                raise ValueError("dependency valid_until cannot precede observed_at")
        return self


class DisasterDependencyPacket(BaseModel):
    snapshot: DisasterSnapshot
    dependencies: list[DisasterDependencyLink] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_graph(self) -> "DisasterDependencyPacket":
        need_ids = {need.need_id for need in self.snapshot.needs}
        for link in self.dependencies:
            if link.upstream_need_id not in need_ids:
                raise ValueError(f"dependency upstream need not found: {link.upstream_need_id}")
            if link.downstream_need_id not in need_ids:
                raise ValueError(f"dependency downstream need not found: {link.downstream_need_id}")

        adjacency: dict[str, list[str]] = defaultdict(list)
        for link in self.dependencies:
            adjacency[link.upstream_need_id].append(link.downstream_need_id)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                raise ValueError("disaster dependency graph must be acyclic")
            visiting.add(node)
            for child in adjacency.get(node, []):
                visit(child)
            visiting.remove(node)
            visited.add(node)

        for node in need_ids:
            visit(node)
        return self


def _fresh(link: DisasterDependencyLink, as_of: datetime) -> bool:
    return link.valid_until is None or link.valid_until >= as_of


def _need_currently_unresolved(status: str) -> bool:
    return status in {"unmet", "partially_met"}


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def apply_disaster_dependencies(
    packet: DisasterDependencyPacket,
    assessment: DisasterAssessment | None = None,
) -> DisasterAssessment:
    result = assessment or assess_disaster(packet.snapshot)
    if not packet.dependencies:
        return result

    need_by_id = {need.need_id: need for need in packet.snapshot.needs}
    established_links = [
        link
        for link in packet.dependencies
        if _fresh(link, packet.snapshot.as_of)
        and link.verification_status in {"corroborated", "verified"}
        and _need_currently_unresolved(need_by_id[link.upstream_need_id].status)
        and _need_currently_unresolved(need_by_id[link.downstream_need_id].status)
    ]

    for link in established_links:
        upstream = need_by_id[link.upstream_need_id]
        downstream = need_by_id[link.downstream_need_id]

        # A strong dependency observation changes the diagnosis from
        # "independent downstream scarcity" to "downstream service constrained
        # by an upstream broken edge". It does not prove that downstream
        # fallback capacity is absent, so reservations and alternative-capability
        # verification remain separate questions.
        result.findings = [
            finding
            for finding in result.findings
            if not (
                finding.need_id == downstream.need_id
                and finding.stage == "capacity"
                and finding.problem_class in {
                    f"{downstream.category.value}_capacity_gap",
                    f"{downstream.category.value}_observed_capacity_shortage",
                }
            )
        ]

        dependency_class = f"{downstream.category.value}_blocked_by_upstream_dependency"
        if any(
            finding.need_id == downstream.need_id and finding.problem_class == dependency_class
            for finding in result.findings
        ):
            continue

        result.findings.append(
            DisasterFinding(
                need_id=downstream.need_id,
                location_ref=downstream.location_ref,
                stage="route",
                problem_class=dependency_class,
                priority=downstream.priority,
                recommended_action=(
                    f"Treat {downstream.category.value} degradation as downstream of the established "
                    f"{upstream.category.value} dependency ({link.mechanism}). Prioritize restoration or a verified workaround "
                    "for the upstream edge before declaring an independent downstream capacity shortage; keep downstream safeguards active meanwhile."
                ),
                evidence_refs=_dedupe([downstream.source_ref, upstream.source_ref, link.source_ref]),
                structural_candidate=False,
                rationale=[
                    f"The dependency is {link.verification_status} and states that {upstream.need_id} {link.relation} {downstream.need_id} via {link.mechanism}.",
                    "Dependency evidence identifies the broken delivery path; it does not establish that fallback downstream capacity is unavailable.",
                ],
            )
        )

    reported_links = [
        link
        for link in packet.dependencies
        if _fresh(link, packet.snapshot.as_of)
        and link.verification_status == "reported"
        and _need_currently_unresolved(need_by_id[link.upstream_need_id].status)
        and _need_currently_unresolved(need_by_id[link.downstream_need_id].status)
    ]
    for link in reported_links:
        downstream = need_by_id[link.downstream_need_id]
        result.findings.append(
            DisasterFinding(
                need_id=downstream.need_id,
                location_ref=downstream.location_ref,
                stage="evidence",
                problem_class="reported_dependency_requires_verification",
                priority=downstream.priority,
                recommended_action=(
                    "Verify the reported upstream dependency before using it to suppress an independent downstream diagnosis or reroute resources."
                ),
                evidence_refs=_dedupe([downstream.source_ref, link.source_ref]),
                structural_candidate=False,
                rationale=["A reported dependency is a causal hypothesis until corroborated or verified."],
            )
        )

    return result


def assess_disaster_payload(payload: dict[str, Any]) -> DisasterAssessment:
    snapshot = DisasterSnapshot.model_validate(payload)
    dependencies = [
        DisasterDependencyLink.model_validate(item)
        for item in payload.get("dependencies", [])
    ]
    packet = DisasterDependencyPacket(snapshot=snapshot, dependencies=dependencies)
    return apply_disaster_dependencies(packet)
