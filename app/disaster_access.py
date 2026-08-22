from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.disaster_control import DisasterAssessment, DisasterFinding, DisasterSnapshot
from app.disaster_safety import assess_disaster_payload as assess_safety_payload


MovementStatus = Literal[
    "admissible",
    "conditionally_admissible",
    "inadmissible",
    "requires_verification",
]


class VehicleAccessRule(BaseModel):
    rule_id: str
    vehicle_class: str
    effect: Literal["allow", "conditional_allow", "deny"]
    max_gross_weight_tons: float | None = Field(default=None, gt=0)
    max_fuel_volume_liters: float | None = Field(default=None, gt=0)
    conditions: list[str] = Field(default_factory=list)


class DisasterAccessEnvelope(BaseModel):
    envelope_id: str
    need_id: str
    source_ref: str
    verification_status: Literal["reported", "corroborated", "verified"] = "reported"
    observed_at: datetime
    valid_until: datetime | None = None
    traffic_control: Literal["normal", "alternating", "controlled", "unknown"] = "unknown"
    rules: list[VehicleAccessRule] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_envelope(self) -> "DisasterAccessEnvelope":
        if self.observed_at.tzinfo is None:
            raise ValueError("access envelope observed_at must be timezone-aware")
        if self.valid_until is not None:
            if self.valid_until.tzinfo is None:
                raise ValueError("access envelope valid_until must be timezone-aware")
            if self.valid_until < self.observed_at:
                raise ValueError("access envelope valid_until cannot precede observed_at")
        ids = [rule.rule_id for rule in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("vehicle access rule_id values must be unique within an envelope")
        classes = [rule.vehicle_class for rule in self.rules]
        if len(classes) != len(set(classes)):
            raise ValueError("vehicle_class rules must be unique within an envelope")
        return self


class DisasterMovementRequest(BaseModel):
    movement_id: str
    need_id: str
    vehicle_class: str
    gross_weight_tons: float | None = Field(default=None, gt=0)
    fuel_volume_liters: float | None = Field(default=None, ge=0)
    required_for_need: bool = True
    notes: str | None = None


class MovementAdmissibility(BaseModel):
    movement_id: str
    need_id: str
    vehicle_class: str
    status: MovementStatus
    envelope_id: str | None = None
    matched_rule_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class DisasterAccessPacket(BaseModel):
    snapshot: DisasterSnapshot
    envelopes: list[DisasterAccessEnvelope] = Field(default_factory=list)
    movement_requests: list[DisasterMovementRequest] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_targets(self) -> "DisasterAccessPacket":
        need_ids = {need.need_id for need in self.snapshot.needs}
        envelope_ids = [envelope.envelope_id for envelope in self.envelopes]
        movement_ids = [movement.movement_id for movement in self.movement_requests]
        if len(envelope_ids) != len(set(envelope_ids)):
            raise ValueError("access envelope_id values must be unique")
        if len(movement_ids) != len(set(movement_ids)):
            raise ValueError("movement_id values must be unique")
        envelope_need_ids = [envelope.need_id for envelope in self.envelopes]
        if len(envelope_need_ids) != len(set(envelope_need_ids)):
            raise ValueError("only one current access envelope may target a need in this layer")
        for envelope in self.envelopes:
            if envelope.need_id not in need_ids:
                raise ValueError(f"access envelope need not found: {envelope.need_id}")
        for movement in self.movement_requests:
            if movement.need_id not in need_ids:
                raise ValueError(f"movement request need not found: {movement.need_id}")
        return self


class DisasterMovementAssessment(DisasterAssessment):
    movement_admissibility: list[MovementAdmissibility] = Field(default_factory=list)


def _strong(envelope: DisasterAccessEnvelope) -> bool:
    return envelope.verification_status in {"corroborated", "verified"}


def _fresh(envelope: DisasterAccessEnvelope, as_of: datetime) -> bool:
    return envelope.valid_until is None or envelope.valid_until >= as_of


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _remove_required_route(assessment: DisasterAssessment, need_id: str) -> None:
    assessment.findings = [
        finding
        for finding in assessment.findings
        if not (finding.need_id == need_id and finding.stage == "route")
    ]
    assessment.proposed_reservations = [
        reservation for reservation in assessment.proposed_reservations if reservation.need_id != need_id
    ]


def _movement_finding(
    *,
    need,
    problem_class: str,
    recommended_action: str,
    evidence_refs: list[str],
    rationale: list[str],
) -> DisasterFinding:
    return DisasterFinding(
        need_id=need.need_id,
        location_ref=need.location_ref,
        stage="access",
        problem_class=problem_class,
        priority=need.priority,
        recommended_action=recommended_action,
        evidence_refs=_dedupe(evidence_refs),
        structural_candidate=False,
        rationale=rationale,
    )


def _evaluate_movement(
    *,
    snapshot: DisasterSnapshot,
    assessment: DisasterAssessment,
    envelope: DisasterAccessEnvelope | None,
    movement: DisasterMovementRequest,
) -> MovementAdmissibility:
    need = next(need for need in snapshot.needs if need.need_id == movement.need_id)
    safety_blocked = any(
        finding.need_id == need.need_id
        and finding.problem_class == "operational_safety_constraint_triggered"
        for finding in assessment.findings
    )

    if safety_blocked:
        return MovementAdmissibility(
            movement_id=movement.movement_id,
            need_id=movement.need_id,
            vehicle_class=movement.vehicle_class,
            status="inadmissible",
            envelope_id=envelope.envelope_id if envelope else None,
            evidence_refs=_dedupe([need.source_ref, envelope.source_ref if envelope else ""]),
            reasons=["An active verified safety gate already suspends operational use for this need."],
        )

    if need.access_status == "isolated":
        return MovementAdmissibility(
            movement_id=movement.movement_id,
            need_id=movement.need_id,
            vehicle_class=movement.vehicle_class,
            status="inadmissible",
            envelope_id=envelope.envelope_id if envelope else None,
            evidence_refs=_dedupe([need.source_ref, envelope.source_ref if envelope else ""]),
            reasons=["The current need observation explicitly marks access as isolated."],
        )

    if envelope is None:
        return MovementAdmissibility(
            movement_id=movement.movement_id,
            need_id=movement.need_id,
            vehicle_class=movement.vehicle_class,
            status="requires_verification",
            evidence_refs=[need.source_ref],
            reasons=["No movement-specific access envelope is supplied for the represented route/need."],
        )

    evidence_refs = _dedupe([need.source_ref, envelope.source_ref])
    if not _fresh(envelope, snapshot.as_of):
        return MovementAdmissibility(
            movement_id=movement.movement_id,
            need_id=movement.need_id,
            vehicle_class=movement.vehicle_class,
            status="requires_verification",
            envelope_id=envelope.envelope_id,
            evidence_refs=evidence_refs,
            reasons=["The access envelope is stale at the current operational timestamp."],
        )

    if not _strong(envelope):
        return MovementAdmissibility(
            movement_id=movement.movement_id,
            need_id=movement.need_id,
            vehicle_class=movement.vehicle_class,
            status="requires_verification",
            envelope_id=envelope.envelope_id,
            evidence_refs=evidence_refs,
            reasons=["The access envelope is only reported and cannot govern consequential movement use yet."],
        )

    rule = next((rule for rule in envelope.rules if rule.vehicle_class == movement.vehicle_class), None)
    if rule is None:
        return MovementAdmissibility(
            movement_id=movement.movement_id,
            need_id=movement.need_id,
            vehicle_class=movement.vehicle_class,
            status="requires_verification",
            envelope_id=envelope.envelope_id,
            evidence_refs=evidence_refs,
            reasons=["The verified envelope does not establish a rule for this vehicle class; absence is not a denial."],
        )

    reasons: list[str] = []
    if rule.effect == "deny":
        reasons.append("The verified access envelope explicitly denies this vehicle class.")
        status: MovementStatus = "inadmissible"
    else:
        status = "admissible"

    if status != "inadmissible" and rule.max_gross_weight_tons is not None:
        if movement.gross_weight_tons is None:
            status = "requires_verification"
            reasons.append(
                f"Gross weight is required to evaluate the {rule.max_gross_weight_tons:g}-ton limit."
            )
        elif movement.gross_weight_tons > rule.max_gross_weight_tons:
            status = "inadmissible"
            reasons.append(
                f"Gross weight {movement.gross_weight_tons:g} t exceeds the verified {rule.max_gross_weight_tons:g} t limit."
            )
        else:
            reasons.append(
                f"Gross weight {movement.gross_weight_tons:g} t is within the verified {rule.max_gross_weight_tons:g} t limit."
            )

    if status != "inadmissible" and rule.max_fuel_volume_liters is not None:
        if movement.fuel_volume_liters is None:
            status = "requires_verification"
            reasons.append(
                f"Fuel volume is required to evaluate the {rule.max_fuel_volume_liters:g}-liter exception limit."
            )
        elif movement.fuel_volume_liters > rule.max_fuel_volume_liters:
            status = "inadmissible"
            reasons.append(
                f"Fuel volume {movement.fuel_volume_liters:g} L exceeds the verified {rule.max_fuel_volume_liters:g} L limit."
            )
        else:
            reasons.append(
                f"Fuel volume {movement.fuel_volume_liters:g} L is within the verified {rule.max_fuel_volume_liters:g} L limit."
            )

    if status == "admissible" and (
        rule.effect == "conditional_allow" or envelope.traffic_control in {"alternating", "controlled"}
    ):
        status = "conditionally_admissible"
        if rule.effect == "conditional_allow":
            reasons.append("This vehicle class is admitted only under the rule's stated conditions.")
        if envelope.traffic_control in {"alternating", "controlled"}:
            reasons.append(
                f"The route is under {envelope.traffic_control} traffic control; local control instructions remain binding."
            )

    if status == "admissible" and envelope.traffic_control == "unknown":
        status = "requires_verification"
        reasons.append("Current traffic-control state is unknown; movement-specific use requires verification.")

    reasons.extend(rule.conditions)
    return MovementAdmissibility(
        movement_id=movement.movement_id,
        need_id=movement.need_id,
        vehicle_class=movement.vehicle_class,
        status=status,
        envelope_id=envelope.envelope_id,
        matched_rule_id=rule.rule_id,
        evidence_refs=evidence_refs,
        reasons=reasons,
    )


def apply_disaster_access_envelopes(
    packet: DisasterAccessPacket,
    assessment: DisasterAssessment,
) -> DisasterMovementAssessment:
    envelope_by_need = {envelope.need_id: envelope for envelope in packet.envelopes}
    movement_results: list[MovementAdmissibility] = []
    need_by_id = {need.need_id: need for need in packet.snapshot.needs}

    for movement in packet.movement_requests:
        envelope = envelope_by_need.get(movement.need_id)
        result = _evaluate_movement(
            snapshot=packet.snapshot,
            assessment=assessment,
            envelope=envelope,
            movement=movement,
        )
        movement_results.append(result)
        need = need_by_id[movement.need_id]

        if result.status == "inadmissible":
            if movement.required_for_need:
                _remove_required_route(assessment, movement.need_id)
            # Avoid duplicating a stronger safety/access-isolation finding that
            # already explains the block.
            already_blocked = any(
                finding.need_id == movement.need_id
                and finding.problem_class
                in {"operational_safety_constraint_triggered", "confirmed_access_disruption", "isolated_need_without_verified_access_capability"}
                for finding in assessment.findings
            )
            if not already_blocked:
                assessment.findings.insert(
                    0,
                    _movement_finding(
                        need=need,
                        problem_class="movement_not_admissible_under_access_envelope",
                        recommended_action=(
                            f"Do not execute movement '{movement.movement_id}' through this route under the current verified envelope. "
                            "Use competent traffic/incident authority to verify a compliant vehicle/load or an alternative path; do not infer wider resource scarcity."
                        ),
                        evidence_refs=result.evidence_refs,
                        rationale=result.reasons,
                    ),
                )
            continue

        if result.status == "requires_verification":
            assessment.findings.append(
                _movement_finding(
                    need=need,
                    problem_class="movement_specific_access_requires_verification",
                    recommended_action=(
                        f"Verify the missing movement-specific access facts for '{movement.movement_id}' before execution. "
                        "Keep any generic route candidate distinct from authorization for this specific vehicle/load."
                    ),
                    evidence_refs=result.evidence_refs,
                    rationale=result.reasons,
                )
            )
            continue

        if result.status == "conditionally_admissible":
            assessment.findings.append(
                _movement_finding(
                    need=need,
                    problem_class="conditional_movement_admissibility",
                    recommended_action=(
                        f"Movement '{movement.movement_id}' is compatible with the current envelope only under its stated controls. "
                        "Follow local traffic supervision and any higher-order safety gate; this is not a dispatch authorization."
                    ),
                    evidence_refs=result.evidence_refs,
                    rationale=result.reasons,
                )
            )

    return DisasterMovementAssessment(
        **assessment.model_dump(mode="python"),
        movement_admissibility=movement_results,
    )


def assess_disaster_payload(payload: dict[str, Any]) -> DisasterMovementAssessment:
    snapshot = DisasterSnapshot.model_validate(payload)
    base = assess_safety_payload(payload)
    envelopes = [
        DisasterAccessEnvelope.model_validate(item)
        for item in payload.get("access_envelopes", [])
    ]
    movement_requests = [
        DisasterMovementRequest.model_validate(item)
        for item in payload.get("movement_requests", [])
    ]
    packet = DisasterAccessPacket(
        snapshot=snapshot,
        envelopes=envelopes,
        movement_requests=movement_requests,
    )
    return apply_disaster_access_envelopes(packet, base)
