from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.interoperability import (
    ControlPlaneInteropPacket,
    DeployableResource,
    InteroperabilityBundle,
    build_control_plane_packet,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DisasterPhase(str, Enum):
    preparedness = "preparedness"
    response = "response"
    recovery = "recovery"
    mitigation = "mitigation"


class DisasterNeedCategory(str, Enum):
    life_safety = "life_safety"
    medical = "medical"
    potable_water = "potable_water"
    shelter = "shelter"
    food = "food"
    access = "access"
    communications = "communications"
    power = "power"
    fire_suppression = "fire_suppression"
    sanitation = "sanitation"
    other = "other"


class DisasterNeed(BaseModel):
    need_id: str
    location_ref: str
    category: DisasterNeedCategory
    priority: Literal["watch", "urgent", "critical"]
    status: Literal["unmet", "partially_met", "met", "unknown"] = "unknown"
    source_ref: str
    verification_status: Literal["reported", "corroborated", "verified"] = "reported"
    observed_at: datetime
    valid_until: datetime | None = None
    people_affected: int | None = Field(default=None, ge=0)
    access_status: Literal["open", "constrained", "isolated", "unknown"] = "unknown"
    required_capabilities: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def timestamps_are_operationally_valid(self) -> "DisasterNeed":
        if self.observed_at.tzinfo is None:
            raise ValueError("need observed_at must be timezone-aware")
        if self.valid_until is not None:
            if self.valid_until.tzinfo is None:
                raise ValueError("need valid_until must be timezone-aware")
            if self.valid_until < self.observed_at:
                raise ValueError("need valid_until cannot precede observed_at")
        return self


class RecurrenceSignal(BaseModel):
    signal_id: str
    location_ref: str
    problem_class: str
    event_count: int = Field(ge=1)
    span_days: int = Field(ge=0)
    source_refs: list[str] = Field(default_factory=list)


class DisasterSnapshot(BaseModel):
    incident_id: str
    as_of: datetime
    phase: DisasterPhase
    interoperability: InteroperabilityBundle
    needs: list[DisasterNeed] = Field(default_factory=list)
    recurrence_signals: list[RecurrenceSignal] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def snapshot_is_coherent(self) -> "DisasterSnapshot":
        if self.as_of.tzinfo is None:
            raise ValueError("snapshot as_of must be timezone-aware")
        if self.interoperability.as_of != self.as_of:
            raise ValueError("interoperability.as_of must equal disaster snapshot as_of")
        ids = [need.need_id for need in self.needs]
        if len(ids) != len(set(ids)):
            raise ValueError("disaster need_id values must be unique")
        return self


class DisasterFinding(BaseModel):
    need_id: str | None = None
    location_ref: str | None = None
    stage: Literal["safety", "stabilize", "route", "capacity", "access", "outcome", "evidence"]
    problem_class: str
    priority: Literal["watch", "urgent", "critical"]
    recommended_action: str
    evidence_refs: list[str] = Field(default_factory=list)
    resource_refs: list[str] = Field(default_factory=list)
    human_authority_required: bool = True
    structural_candidate: bool = False
    rationale: list[str] = Field(default_factory=list)


class ResourceReservation(BaseModel):
    resource_record_id: str
    need_id: str
    purpose: str
    status: Literal["proposed"] = "proposed"


class DisasterAssessment(BaseModel):
    incident_id: str
    assessed_at: datetime = Field(default_factory=utcnow)
    phase: DisasterPhase
    command_context_present: bool
    findings: list[DisasterFinding] = Field(default_factory=list)
    proposed_reservations: list[ResourceReservation] = Field(default_factory=list)
    unresolved_need_ids: list[str] = Field(default_factory=list)
    stale_need_ids: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    interoperability: ControlPlaneInteropPacket
    safe_conclusion: str


_DEFAULT_CAPABILITIES: dict[DisasterNeedCategory, set[str]] = {
    DisasterNeedCategory.life_safety: {"search_and_rescue", "urban_search_and_rescue", "rescue"},
    DisasterNeedCategory.medical: {"emergency_medical", "medevac", "medical_stabilization"},
    DisasterNeedCategory.potable_water: {"potable_water_delivery", "water_purification"},
    DisasterNeedCategory.shelter: {"emergency_shelter", "shelter_management"},
    DisasterNeedCategory.food: {"food_distribution", "emergency_feeding"},
    DisasterNeedCategory.access: {"road_clearance", "engineering", "air_access", "offroad_access"},
    DisasterNeedCategory.communications: {"emergency_communications", "satellite_communications"},
    DisasterNeedCategory.power: {"emergency_power", "generator"},
    DisasterNeedCategory.fire_suppression: {"fire_suppression", "peat_fire_suppression", "water_bombing"},
    DisasterNeedCategory.sanitation: {"sanitation", "wash"},
    DisasterNeedCategory.other: set(),
}

_ACCESS_CAPABILITIES = {"air_access", "air_delivery", "offroad_access", "helicopter_transport"}
_PRIORITY_ORDER = {"critical": 0, "urgent": 1, "watch": 2}
_SURVIVAL_ORDER = {
    DisasterNeedCategory.life_safety: 0,
    DisasterNeedCategory.medical: 1,
    DisasterNeedCategory.fire_suppression: 2,
    DisasterNeedCategory.potable_water: 3,
    DisasterNeedCategory.shelter: 4,
    DisasterNeedCategory.food: 5,
    DisasterNeedCategory.sanitation: 6,
    DisasterNeedCategory.access: 7,
    DisasterNeedCategory.communications: 8,
    DisasterNeedCategory.power: 9,
    DisasterNeedCategory.other: 10,
}


def _need_fresh(need: DisasterNeed, as_of: datetime) -> bool:
    return need.valid_until is None or need.valid_until >= as_of


def _capabilities(resource: DeployableResource) -> set[str]:
    values = {value.lower() for value in resource.capabilities}
    values.add(resource.resource_type.lower())
    return values


def _required(need: DisasterNeed) -> set[str]:
    if need.required_capabilities:
        return {value.lower() for value in need.required_capabilities}
    return _DEFAULT_CAPABILITIES[need.category]


def _resource_matches(resource: DeployableResource, need: DisasterNeed) -> bool:
    available = _capabilities(resource)
    required = _required(need)
    if required and not available.intersection(required):
        return False
    if need.access_status == "isolated" and not available.intersection(_ACCESS_CAPABILITIES):
        return False
    return True


def _structural_candidate(snapshot: DisasterSnapshot, need: DisasterNeed) -> bool:
    if snapshot.phase not in {DisasterPhase.recovery, DisasterPhase.mitigation, DisasterPhase.preparedness}:
        return False
    return any(
        signal.location_ref == need.location_ref
        and signal.problem_class in {need.category.value, "access", "service_failure", "hazard_recurrence"}
        and signal.event_count >= 3
        and signal.span_days >= 14
        for signal in snapshot.recurrence_signals
    )


def _evidence_refs(need: DisasterNeed) -> list[str]:
    return [need.source_ref]


def assess_disaster(snapshot: DisasterSnapshot) -> DisasterAssessment:
    packet = build_control_plane_packet(snapshot.interoperability)
    command_present = bool(packet.command_contexts)
    findings: list[DisasterFinding] = []
    reservations: list[ResourceReservation] = []
    unresolved: list[str] = []
    stale_needs: list[str] = []
    data_gaps: list[str] = []
    used_resources: set[str] = set()

    needs = sorted(
        snapshot.needs,
        key=lambda need: (_PRIORITY_ORDER[need.priority], _SURVIVAL_ORDER[need.category], need.need_id),
    )

    for need in needs:
        if need.status == "met":
            continue
        if not _need_fresh(need, snapshot.as_of):
            stale_needs.append(need.need_id)
            unresolved.append(need.need_id)
            findings.append(
                DisasterFinding(
                    need_id=need.need_id,
                    location_ref=need.location_ref,
                    stage="evidence",
                    problem_class="stale_need_state",
                    priority=need.priority,
                    recommended_action="Obtain a fresh condition observation before treating this need as current operational state.",
                    evidence_refs=_evidence_refs(need),
                    rationale=["The need observation expired before the assessment as_of time."],
                )
            )
            continue

        unresolved.append(need.need_id)
        structural = _structural_candidate(snapshot, need)

        if need.priority == "critical" and need.verification_status == "reported":
            findings.append(
                DisasterFinding(
                    need_id=need.need_id,
                    location_ref=need.location_ref,
                    stage="safety",
                    problem_class="critical_need_requires_verification_and_escalation",
                    priority="critical",
                    recommended_action=(
                        "Escalate for rapid verification through authorized incident command; do not discard a potentially catastrophic "
                        "life-safety report merely because it is not yet corroborated."
                    ),
                    evidence_refs=_evidence_refs(need),
                    structural_candidate=False,
                    rationale=["Critical uncertainty is itself operationally relevant; verification should run in parallel with escalation."],
                )
            )

        deployable = [
            resource
            for resource in packet.deployable_resources
            if resource.record_id not in used_resources and _resource_matches(resource, need)
        ]
        candidates = [resource for resource in packet.resource_candidates_requiring_verification if _resource_matches(resource, need)]

        if need.access_status == "isolated" and not deployable:
            findings.append(
                DisasterFinding(
                    need_id=need.need_id,
                    location_ref=need.location_ref,
                    stage="access",
                    problem_class="isolated_need_without_verified_access_capability",
                    priority=need.priority,
                    recommended_action=(
                        "Establish or verify an alternative access path (air/off-road/engineering) before counting nearby resources as reachable."
                    ),
                    evidence_refs=_evidence_refs(need),
                    structural_candidate=structural,
                    rationale=["Resource existence does not establish physical reachability to an isolated location."],
                )
            )
            continue

        if deployable:
            resource = deployable[0]
            used_resources.add(resource.record_id)
            reservations.append(
                ResourceReservation(
                    resource_record_id=resource.record_id,
                    need_id=need.need_id,
                    purpose=need.category.value,
                )
            )
            findings.append(
                DisasterFinding(
                    need_id=need.need_id,
                    location_ref=need.location_ref,
                    stage="route",
                    problem_class=f"{need.category.value}_resource_route",
                    priority=need.priority,
                    recommended_action=(
                        f"Route verified available {resource.resource_type} through the authorized incident-command/resource-request process; "
                        "this assessment proposes a reservation but does not dispatch the resource."
                    ),
                    evidence_refs=_evidence_refs(need) + [resource.source_ref],
                    resource_refs=[resource.record_id],
                    structural_candidate=structural,
                    rationale=[
                        "The resource is fresh, sufficiently verified, marked available, capability-compatible and not already proposed elsewhere in this assessment."
                    ],
                )
            )
            continue

        if candidates:
            findings.append(
                DisasterFinding(
                    need_id=need.need_id,
                    location_ref=need.location_ref,
                    stage="evidence",
                    problem_class="reported_resource_requires_verification",
                    priority=need.priority,
                    recommended_action=(
                        "Verify the reportedly available matching resource before operational routing; keep the unmet need active meanwhile."
                    ),
                    evidence_refs=_evidence_refs(need) + [resource.source_ref for resource in candidates],
                    resource_refs=[resource.record_id for resource in candidates],
                    structural_candidate=structural,
                    rationale=["Reported availability is not deployable capacity."],
                )
            )
            continue

        findings.append(
            DisasterFinding(
                need_id=need.need_id,
                location_ref=need.location_ref,
                stage="capacity",
                problem_class=f"{need.category.value}_capacity_gap",
                priority=need.priority,
                recommended_action=(
                    "Request matching capability through mutual-aid/resource coordination or establish the smallest safe temporary capacity; "
                    "do not infer that a permanent facility is justified from this incident alone."
                ),
                evidence_refs=_evidence_refs(need),
                structural_candidate=structural,
                rationale=["No fresh verified uncommitted capability-compatible resource is present in the supplied interoperability packet."],
            )
        )

    if not snapshot.needs:
        data_gaps.append("No current disaster needs were supplied; hazard presence alone does not establish a specific relief requirement.")
    if not command_present:
        data_gaps.append(
            "No current command/authority context is supplied. Analysis may identify gaps, but no consequential routing recommendation is authorized for execution."
        )
    if packet.stale_record_ids:
        data_gaps.append(
            "Some interoperability records are stale and were excluded from current operational state: "
            + ", ".join(packet.stale_record_ids[:10])
        )

    safe_conclusion = (
        "This disaster assessment is decision support, not autonomous incident command. Humanitarian minimums and credible immediate life-safety "
        "needs take precedence over efficiency optimization. A proposed reservation is not a dispatch order; competent incident command, emergency, "
        "medical, engineering and other authorities retain consequential decisions. People must never be deprioritized by economic value, social status, "
        "identity, predicted productivity or aid-deservingness."
    )

    return DisasterAssessment(
        incident_id=snapshot.incident_id,
        phase=snapshot.phase,
        command_context_present=command_present,
        findings=findings,
        proposed_reservations=reservations,
        unresolved_need_ids=unresolved,
        stale_need_ids=stale_needs,
        data_gaps=data_gaps,
        interoperability=packet,
        safe_conclusion=safe_conclusion,
    )
