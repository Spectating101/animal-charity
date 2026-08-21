from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.disaster_control import DisasterAssessment, DisasterFinding, DisasterSnapshot
from app.disaster_dependencies import assess_disaster_payload as assess_dependency_payload


class DisasterSafetyConstraint(BaseModel):
    constraint_id: str
    need_id: str
    trigger: str
    trigger_status: Literal["inactive", "active", "unknown"] = "unknown"
    effect: Literal["suspend_use", "restrict_use", "verify_before_use"] = "suspend_use"
    source_ref: str
    verification_status: Literal["reported", "corroborated", "verified"] = "reported"
    observed_at: datetime
    valid_until: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_timestamps(self) -> "DisasterSafetyConstraint":
        if self.observed_at.tzinfo is None:
            raise ValueError("safety constraint observed_at must be timezone-aware")
        if self.valid_until is not None:
            if self.valid_until.tzinfo is None:
                raise ValueError("safety constraint valid_until must be timezone-aware")
            if self.valid_until < self.observed_at:
                raise ValueError("safety constraint valid_until cannot precede observed_at")
        return self


class DisasterSafetyPacket(BaseModel):
    snapshot: DisasterSnapshot
    constraints: list[DisasterSafetyConstraint] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_targets(self) -> "DisasterSafetyPacket":
        need_ids = {need.need_id for need in self.snapshot.needs}
        ids = [constraint.constraint_id for constraint in self.constraints]
        if len(ids) != len(set(ids)):
            raise ValueError("safety constraint_id values must be unique")
        for constraint in self.constraints:
            if constraint.need_id not in need_ids:
                raise ValueError(f"safety constraint need not found: {constraint.need_id}")
        return self


def _fresh(constraint: DisasterSafetyConstraint, as_of: datetime) -> bool:
    return constraint.valid_until is None or constraint.valid_until >= as_of


def _strong(constraint: DisasterSafetyConstraint) -> bool:
    return constraint.verification_status in {"corroborated", "verified"}


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def apply_disaster_safety_constraints(
    packet: DisasterSafetyPacket,
    assessment: DisasterAssessment,
) -> DisasterAssessment:
    if not packet.constraints:
        return assessment

    need_by_id = {need.need_id: need for need in packet.snapshot.needs}

    for constraint in packet.constraints:
        need = need_by_id[constraint.need_id]

        if not _fresh(constraint, packet.snapshot.as_of):
            assessment.data_gaps.append(
                f"Safety constraint {constraint.constraint_id} is stale and cannot govern current operational use."
            )
            continue

        if not _strong(constraint):
            assessment.findings.append(
                DisasterFinding(
                    need_id=need.need_id,
                    location_ref=need.location_ref,
                    stage="evidence",
                    problem_class="reported_safety_constraint_requires_verification",
                    priority=need.priority,
                    recommended_action=(
                        "Verify the reported operational safety constraint through an authorized/current source before using it to suspend or restrict a route or resource."
                    ),
                    evidence_refs=_dedupe([need.source_ref, constraint.source_ref]),
                    structural_candidate=False,
                    rationale=[
                        "Reported safety information is material but is not strong enough to invalidate an otherwise usable route/resource by itself."
                    ],
                )
            )
            continue

        if constraint.trigger_status == "active":
            if constraint.effect in {"suspend_use", "restrict_use"}:
                # Safety gates outrank throughput. Remove any route recommendation
                # and proposed reservation for the affected need; the overlay does
                # not choose a replacement resource automatically.
                assessment.findings = [
                    finding
                    for finding in assessment.findings
                    if not (finding.need_id == need.need_id and finding.stage == "route")
                ]
                assessment.proposed_reservations = [
                    reservation
                    for reservation in assessment.proposed_reservations
                    if reservation.need_id != need.need_id
                ]

            assessment.findings.insert(
                0,
                DisasterFinding(
                    need_id=need.need_id,
                    location_ref=need.location_ref,
                    stage="safety",
                    problem_class="operational_safety_constraint_triggered",
                    priority=need.priority,
                    recommended_action=(
                        f"Apply the verified safety rule for trigger '{constraint.trigger}'. "
                        f"Effect: {constraint.effect}. Suspend/restrict operational use through competent authority and reassess alternatives; do not optimize throughput through an unsafe path."
                    ),
                    evidence_refs=_dedupe([need.source_ref, constraint.source_ref]),
                    structural_candidate=False,
                    rationale=[
                        f"The constraint is {constraint.verification_status}, current, and its trigger is active.",
                        "Safety invalidation is separate from resource scarcity: blocking one unsafe route/resource does not prove alternatives are absent.",
                    ],
                ),
            )
            continue

        problem_class = (
            "conditional_operational_safety_constraint"
            if constraint.trigger_status == "inactive"
            else "safety_trigger_state_requires_monitoring"
        )
        recommendation = (
            f"Keep the current path conditionally usable while trigger '{constraint.trigger}' remains inactive, but monitor the trigger and apply {constraint.effect} if it becomes active."
            if constraint.trigger_status == "inactive"
            else f"Verify the current state of trigger '{constraint.trigger}' before relying on the path as continuously usable; apply {constraint.effect} if the trigger is active."
        )
        assessment.findings.insert(
            0,
            DisasterFinding(
                need_id=need.need_id,
                location_ref=need.location_ref,
                stage="safety",
                problem_class=problem_class,
                priority=need.priority,
                recommended_action=recommendation,
                evidence_refs=_dedupe([need.source_ref, constraint.source_ref]),
                structural_candidate=False,
                rationale=[
                    "The safety rule is sufficiently verified and current, but its trigger is not established as active at this assessment time.",
                    "Operational availability is therefore conditional rather than permanently open or permanently closed.",
                ],
            ),
        )

    return assessment


def assess_disaster_payload(payload: dict[str, Any]) -> DisasterAssessment:
    snapshot = DisasterSnapshot.model_validate(payload)
    base = assess_dependency_payload(payload)
    constraints = [
        DisasterSafetyConstraint.model_validate(item)
        for item in payload.get("safety_constraints", [])
    ]
    packet = DisasterSafetyPacket(snapshot=snapshot, constraints=constraints)
    return apply_disaster_safety_constraints(packet, base)
