from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


class EvidenceClass(str, Enum):
    condition = "condition"
    capability = "capability"
    context = "context"


class SourceTier(str, Enum):
    official = "official"
    partner = "partner"
    professional = "professional"
    public_report = "public_report"
    synthetic = "synthetic"


class Observation(BaseModel):
    observation_id: str = Field(default_factory=lambda: new_id("obs"))
    area_id: str
    subject_ref: str
    signal: str
    value: Any
    unit: str | None = None
    evidence_class: EvidenceClass = EvidenceClass.condition
    source_ref: str
    source_tier: SourceTier
    confidence: float = Field(default=1.0, ge=0, le=1)
    observed_at: datetime = Field(default_factory=utcnow)
    synthetic: bool = False
    notes: str | None = None


class Capability(BaseModel):
    capability_id: str = Field(default_factory=lambda: new_id("cap"))
    area_id: str
    kind: str
    provider_ref: str
    source_ref: str
    source_tier: SourceTier = SourceTier.official
    confidence: float = Field(default=1.0, ge=0, le=1)
    details: dict[str, Any] = Field(default_factory=dict)


class LandscapeSnapshot(BaseModel):
    area_id: str
    area_name: str
    observations: list[Observation] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProblemCase(BaseModel):
    case_id: str
    subject_ref: str
    problem_type: str
    severity: Literal["watch", "urgent", "critical"]
    confidence: float = Field(ge=0, le=1)
    diagnosis_status: Literal["observed", "hypothesis", "unresolved"]
    bottleneck: str
    explanation: str
    intervention: str
    actuator: str
    actionability: Literal["ready_for_human_review", "needs_evidence", "monitor"]
    evidence_refs: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    synthetic: bool = False


class LandscapeAssessment(BaseModel):
    area_id: str
    area_name: str
    assessed_at: datetime = Field(default_factory=utcnow)
    cases: list[ProblemCase] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    safe_conclusion: str


def _stable_case_id(area_id: str, subject_ref: str, problem_type: str) -> str:
    digest = hashlib.sha256(f"{area_id}|{subject_ref}|{problem_type}".encode()).hexdigest()[:16]
    return f"pcase_{digest}"


def _conditions(snapshot: LandscapeSnapshot, subject_ref: str, signal: str) -> list[Observation]:
    rows = [
        x for x in snapshot.observations
        if x.subject_ref == subject_ref
        and x.signal == signal
        and x.evidence_class == EvidenceClass.condition
    ]
    return sorted(rows, key=lambda x: x.observed_at)


def _latest(snapshot: LandscapeSnapshot, subject_ref: str, signal: str) -> Observation | None:
    rows = _conditions(snapshot, subject_ref, signal)
    return rows[-1] if rows else None


def _number(obs: Observation | None) -> float | None:
    if obs is None:
        return None
    try:
        return float(obs.value)
    except (TypeError, ValueError):
        return None


def _min_confidence(rows: list[Observation]) -> float:
    return round(min((x.confidence for x in rows), default=0.0), 3)


def _nutrition_case(snapshot: LandscapeSnapshot, subject: str) -> ProblemCase | None:
    coverage = _latest(snapshot, subject, "feed_coverage_days")
    coverage_days = _number(coverage)
    if coverage is None or coverage_days is None or coverage_days >= 3:
        return None

    support: list[Observation] = [coverage]
    supply = _latest(snapshot, subject, "compatible_supply_kg_nearby")
    transport = _latest(snapshot, subject, "transport_available")
    budget = _latest(snapshot, subject, "budget_gap_twd")
    intake = _latest(snapshot, subject, "intake_ratio")

    diagnosis_status: Literal["observed", "hypothesis", "unresolved"] = "hypothesis"
    unknowns: list[str] = []

    if _number(supply) is not None and _number(supply) > 0:
        support.append(supply)
        if transport is not None and transport.value is False:
            support.append(transport)
            bottleneck = "last_mile_logistics"
            explanation = (
                f"Verified feed coverage is {coverage_days:g} days and compatible supply is evidenced nearby, "
                "but current transport availability is false. The immediate missing resource is movement, not feed."
            )
            intervention = "Secure a human-approved transport task for the already-identified compatible supply."
            actuator = "logistics.dispatch_request"
            actionability = "ready_for_human_review"
        elif transport is not None and transport.value is True:
            support.append(transport)
            bottleneck = "coordination"
            explanation = (
                f"Verified feed coverage is {coverage_days:g} days; compatible supply and transport are both evidenced. "
                "The remaining problem is allocation/coordination."
            )
            intervention = "Create a constrained feed allocation and route it through human approval."
            actuator = "afrn.feed_matcher"
            actionability = "ready_for_human_review"
        else:
            bottleneck = "delivery_feasibility_unknown"
            explanation = (
                f"Verified feed coverage is {coverage_days:g} days and compatible supply is evidenced, "
                "but the system cannot establish whether it can physically reach the subject."
            )
            intervention = "Verify pickup, vehicle, storage and delivery feasibility before sourcing additional feed."
            actuator = "evidence.request"
            actionability = "needs_evidence"
            unknowns.append("transport_availability")
    elif _number(budget) is not None and _number(budget) > 0:
        support.append(budget)
        bottleneck = "funding_procurement"
        explanation = (
            f"Verified feed coverage is {coverage_days:g} days, no compatible nearby supply is evidenced, "
            f"and a procurement gap of {int(_number(budget))} TWD is reported."
        )
        intervention = "Verify the quoted procurement need and expose a precise funding/purchase request."
        actuator = "funding.precise_gap_request"
        actionability = "ready_for_human_review"
    elif _number(intake) is not None and _number(intake) >= 1.5:
        support.append(intake)
        bottleneck = "capacity_surge"
        explanation = (
            f"Verified feed coverage is {coverage_days:g} days alongside intake at {_number(intake):g}× baseline. "
            "The shortage may be downstream of a capacity surge rather than ordinary procurement failure."
        )
        intervention = "Stabilize nutrition while opening foster/adoption/referral and capacity-relief options."
        actuator = "capacity.relief_plan"
        actionability = "ready_for_human_review"
    else:
        diagnosis_status = "unresolved"
        bottleneck = "cause_unresolved"
        explanation = (
            f"Verified feed coverage is {coverage_days:g} days, but current evidence does not establish why the gap exists."
        )
        intervention = "Collect supply, transport, procurement, intake and inventory-freshness evidence before selecting an intervention."
        actuator = "evidence.request"
        actionability = "needs_evidence"
        unknowns.extend(["compatible_supply", "transport", "procurement_gap", "intake_pressure"])

    severity: Literal["watch", "urgent", "critical"] = "critical" if coverage_days < 1 else "urgent"
    return ProblemCase(
        case_id=_stable_case_id(snapshot.area_id, subject, "nutrition_risk"),
        subject_ref=subject,
        problem_type="nutrition_risk",
        severity=severity,
        confidence=_min_confidence(support),
        diagnosis_status=diagnosis_status,
        bottleneck=bottleneck,
        explanation=explanation,
        intervention=intervention,
        actuator=actuator,
        actionability=actionability,
        evidence_refs=[x.source_ref for x in support],
        unknowns=unknowns,
        synthetic=any(x.synthetic for x in support),
    )


def _capacity_case(snapshot: LandscapeSnapshot, subject: str) -> ProblemCase | None:
    occupancy = _latest(snapshot, subject, "shelter_capacity_ratio")
    intake = _latest(snapshot, subject, "intake_ratio")
    occ = _number(occupancy)
    intake_ratio = _number(intake)
    triggered = (occ is not None and occ >= 0.9) or (intake_ratio is not None and intake_ratio >= 1.5)
    if not triggered:
        return None
    support = [x for x in (occupancy, intake) if x is not None]
    parts: list[str] = []
    if occ is not None:
        parts.append(f"capacity ratio {occ:.0%}")
    if intake_ratio is not None:
        parts.append(f"intake {intake_ratio:g}× baseline")
    severity: Literal["watch", "urgent", "critical"] = "urgent" if (occ or 0) >= 1 or (intake_ratio or 0) >= 2 else "watch"
    return ProblemCase(
        case_id=_stable_case_id(snapshot.area_id, subject, "capacity_pressure"),
        subject_ref=subject,
        problem_type="capacity_pressure",
        severity=severity,
        confidence=_min_confidence(support),
        diagnosis_status="observed",
        bottleneck="care_capacity",
        explanation="Observed capacity pressure: " + ", ".join(parts) + ".",
        intervention="Assess foster/adoption/referral capacity, intake controls, staffing and temporary support before treating downstream shortages in isolation.",
        actuator="capacity.relief_plan",
        actionability="ready_for_human_review",
        evidence_refs=[x.source_ref for x in support],
        synthetic=any(x.synthetic for x in support),
    )


def _rescue_delay_case(snapshot: LandscapeSnapshot, subject: str) -> ProblemCase | None:
    delay = _latest(snapshot, subject, "unresolved_rescue_age_hours")
    hours = _number(delay)
    if delay is None or hours is None or hours < 12:
        return None
    severity: Literal["watch", "urgent", "critical"] = "critical" if hours >= 24 else "urgent"
    return ProblemCase(
        case_id=_stable_case_id(snapshot.area_id, subject, "rescue_delay"),
        subject_ref=subject,
        problem_type="rescue_delay",
        severity=severity,
        confidence=round(delay.confidence, 3),
        diagnosis_status="observed",
        bottleneck="response_delay",
        explanation=f"A verified rescue case has remained unresolved for {hours:g} hours.",
        intervention="Escalate to an authorized rescue channel and record acceptance, handoff or reason for non-action.",
        actuator="rescue.escalate",
        actionability="ready_for_human_review",
        evidence_refs=[delay.source_ref],
        synthetic=delay.synthetic,
    )


def assess_landscape(snapshot: LandscapeSnapshot) -> LandscapeAssessment:
    condition_rows = [x for x in snapshot.observations if x.evidence_class == EvidenceClass.condition]
    subjects = sorted({x.subject_ref for x in condition_rows})
    cases: list[ProblemCase] = []
    for subject in subjects:
        for detector in (_nutrition_case, _capacity_case, _rescue_delay_case):
            case = detector(snapshot, subject)
            if case is not None:
                cases.append(case)

    severity_rank = {"critical": 0, "urgent": 1, "watch": 2}
    cases.sort(key=lambda x: (severity_rank[x.severity], -x.confidence, x.case_id))

    data_gaps: list[str] = []
    if not condition_rows:
        data_gaps.extend([
            "No live condition evidence: capability/service data alone cannot establish an active welfare problem.",
            "Need current recipient or field observations (for example inventory coverage, verified rescue state, or capacity pressure).",
            "Need current logistics/resource availability to distinguish scarcity from access/coordination failure.",
            "Need outcome timestamps/evidence to learn whether interventions actually resolved cases.",
        ])
        safe_conclusion = (
            "The area has observable welfare capabilities, but the supplied evidence does not justify asserting an active welfare crisis."
        )
    elif not cases:
        data_gaps.append("Condition evidence was supplied, but none crossed the current conservative problem thresholds.")
        safe_conclusion = "No active problem crossed the current conservative detection thresholds. Continue monitoring."
    else:
        safe_conclusion = (
            f"Detected {len(cases)} candidate welfare problem(s). Diagnoses are evidence-bounded; causal labels remain hypotheses unless directly established."
        )

    return LandscapeAssessment(
        area_id=snapshot.area_id,
        area_name=snapshot.area_name,
        cases=cases,
        capabilities=snapshot.capabilities,
        data_gaps=data_gaps,
        safe_conclusion=safe_conclusion,
    )


def load_snapshot(path: str | Path) -> LandscapeSnapshot:
    return LandscapeSnapshot.model_validate_json(Path(path).read_text(encoding="utf-8"))


def dump_assessment(assessment: LandscapeAssessment) -> str:
    return json.dumps(assessment.model_dump(mode="json"), indent=2, ensure_ascii=False)
