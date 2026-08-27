from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.integrity_plane import IntegrityAssessment, IntegritySnapshot, assess_integrity


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceClass(str, Enum):
    condition = "condition"
    capability = "capability"
    context = "context"


class MBGObservation(BaseModel):
    observation_id: str
    signal: str
    value: Any
    evidence_class: EvidenceClass
    source_ref: str
    confidence: float = Field(default=1.0, ge=0, le=1)
    observed_at: datetime = Field(default_factory=utcnow)
    synthetic: bool = False
    notes: str | None = None


class MBGCaseSnapshot(BaseModel):
    programme_id: str = "indonesia-mbg-case-study"
    area_id: str
    area_name: str
    observations: list[MBGObservation] = Field(default_factory=list)
    integrity: IntegritySnapshot | None = None
    recurrence_count: int = Field(default=1, ge=0)
    recurrence_span_days: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MBGCaseFinding(BaseModel):
    problem_class: Literal[
        "food_safety_failure",
        "integrity_uncertainty",
        "capacity_gap",
        "access_or_delivery_gap",
        "targeting_or_data_gap",
        "outcome_evidence_gap",
        "cause_unresolved",
    ]
    priority: Literal["watch", "urgent", "critical"]
    rationale: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    recommended_action: str
    structural_candidate: bool = False
    human_authority_required: bool = True


class MBGCaseAssessment(BaseModel):
    programme_id: str
    area_id: str
    area_name: str
    assessed_at: datetime = Field(default_factory=utcnow)
    integrity_assessment: IntegrityAssessment | None = None
    findings: list[MBGCaseFinding] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    safe_conclusion: str
    governance_boundary: str


def _latest(snapshot: MBGCaseSnapshot, signal: str) -> MBGObservation | None:
    rows = [x for x in snapshot.observations if x.signal == signal]
    return max(rows, key=lambda x: x.observed_at) if rows else None


def _condition(snapshot: MBGCaseSnapshot, signal: str) -> MBGObservation | None:
    rows = [x for x in snapshot.observations if x.signal == signal and x.evidence_class == EvidenceClass.condition]
    return max(rows, key=lambda x: x.observed_at) if rows else None


def _bool(obs: MBGObservation | None) -> bool | None:
    if obs is None:
        return None
    if isinstance(obs.value, bool):
        return obs.value
    if isinstance(obs.value, str):
        if obs.value.lower() in {"true", "yes", "1"}:
            return True
        if obs.value.lower() in {"false", "no", "0"}:
            return False
    return None


def _num(obs: MBGObservation | None) -> float | None:
    if obs is None:
        return None
    try:
        return float(obs.value)
    except (TypeError, ValueError):
        return None


def _structural(snapshot: MBGCaseSnapshot) -> bool:
    return snapshot.recurrence_count >= 3 and snapshot.recurrence_span_days >= 14


def assess_mbg_case(snapshot: MBGCaseSnapshot) -> MBGCaseAssessment:
    condition_rows = [x for x in snapshot.observations if x.evidence_class == EvidenceClass.condition]
    integrity_assessment = assess_integrity(snapshot.integrity) if snapshot.integrity else None
    findings: list[MBGCaseFinding] = []
    data_gaps: list[str] = []

    if not condition_rows:
        return MBGCaseAssessment(
            programme_id=snapshot.programme_id,
            area_id=snapshot.area_id,
            area_name=snapshot.area_name,
            integrity_assessment=integrity_assessment,
            findings=[],
            data_gaps=[
                "No programme-condition observations supplied. Aggregate targets, SPPG counts, supplier counts, policy issues, or programme existence do not establish a local operational failure by themselves."
            ],
            safe_conclusion="Public/context capability evidence is insufficient to diagnose a local MBG failure or recommend new infrastructure.",
            governance_boundary=(
                "This case-study adapter may organize evidence and propose review questions. It cannot determine beneficiary entitlement, freeze payments, exclude suppliers, open a formal audit/investigation, impose sanctions, or accuse a person/entity of corruption."
            ),
        )

    safety = _bool(_condition(snapshot, "food_safety_ok"))
    target = _num(_condition(snapshot, "verified_target_beneficiaries"))
    capacity = _num(_condition(snapshot, "verified_service_capacity_meals_per_day"))
    actual = _num(_condition(snapshot, "verified_actual_recipients_per_day"))
    transport = _bool(_condition(snapshot, "transport_reliable"))
    data_quality = _bool(_condition(snapshot, "beneficiary_data_quality_verified"))
    outcome_measured = _bool(_condition(snapshot, "nutritional_outcome_measured"))

    if safety is False:
        obs = _condition(snapshot, "food_safety_ok")
        findings.append(MBGCaseFinding(
            problem_class="food_safety_failure",
            priority="critical",
            rationale=["Verified food-safety failure is a hard gate and takes precedence over coverage or expansion optimization."],
            evidence_refs=[obs.source_ref] if obs else [],
            recommended_action="Pause the affected service path as required by competent authority, preserve samples/records, conduct food-safety investigation, remediate the cause, and verify safe restart before optimizing coverage.",
            structural_candidate=_structural(snapshot),
        ))

    if integrity_assessment and integrity_assessment.overall_status != "normal":
        refs = [ref for f in integrity_assessment.findings for ref in f.evidence_refs]
        findings.append(MBGCaseFinding(
            problem_class="integrity_uncertainty",
            priority="urgent" if integrity_assessment.overall_status != "audit_referral_recommended" else "critical",
            rationale=[
                f"Integrity plane status is {integrity_assessment.overall_status}.",
                "A resource-flow discrepancy can masquerade as scarcity, capacity failure, or supplier failure; reconcile it before using the discrepancy to justify expansion or sanctions.",
                "The discrepancy does not itself establish fraud or corruption.",
            ],
            evidence_refs=sorted(set(refs)),
            recommended_action="Reconcile authorization/disbursement/procurement/physical-input/service-output/beneficiary-receipt records and route material verified discrepancies to authorized human audit review.",
            structural_candidate=False,
        ))

    if target is not None and capacity is not None and target > capacity:
        refs = [x.source_ref for x in (_condition(snapshot, "verified_target_beneficiaries"), _condition(snapshot, "verified_service_capacity_meals_per_day")) if x]
        findings.append(MBGCaseFinding(
            problem_class="capacity_gap",
            priority="urgent",
            rationale=[f"Verified target demand ({target:g}) exceeds verified local service capacity ({capacity:g})."],
            evidence_refs=refs,
            recommended_action="Check verified spare capacity in adjacent SPPG catchments and schedule/catchment rebalancing first; if insufficient, compare reversible capacity extension or satellite service before proposing a permanent new SPPG.",
            structural_candidate=_structural(snapshot),
        ))

    service_ceiling = None
    if target is not None and capacity is not None:
        service_ceiling = min(target, capacity)
    elif target is not None:
        service_ceiling = target
    elif capacity is not None:
        service_ceiling = capacity

    if actual is not None and service_ceiling is not None and actual < service_ceiling * 0.95:
        refs = [x.source_ref for x in (_condition(snapshot, "verified_actual_recipients_per_day"), _condition(snapshot, "transport_reliable"), _condition(snapshot, "beneficiary_data_quality_verified")) if x]
        if transport is False:
            problem = "access_or_delivery_gap"
            action = "Repair the verified route/schedule/last-mile delivery bottleneck before adding production capacity."
            rationale = ["Verified service receipt is materially below available demand/capacity and transport reliability is false."]
        elif data_quality is False:
            problem = "targeting_or_data_gap"
            action = "Reconcile beneficiary records with recipient institutions/posyandu/schools and verify eligibility/attendance using authorized processes before changing kitchen capacity."
            rationale = ["Verified service receipt is materially below available demand/capacity and beneficiary-data quality is not verified."]
        else:
            problem = "cause_unresolved"
            action = "Collect route, attendance, beneficiary-record, production, waste, schedule and recipient evidence before selecting a capacity or access intervention."
            rationale = ["Verified receipt is below the service ceiling, but the supplied evidence does not establish why."]
        findings.append(MBGCaseFinding(
            problem_class=problem,
            priority="urgent",
            rationale=rationale,
            evidence_refs=refs,
            recommended_action=action,
            structural_candidate=_structural(snapshot),
        ))

    if actual is not None and service_ceiling is not None and actual >= service_ceiling * 0.95 and outcome_measured is False:
        obs = _condition(snapshot, "nutritional_outcome_measured")
        findings.append(MBGCaseFinding(
            problem_class="outcome_evidence_gap",
            priority="watch",
            rationale=[
                "Service output/receipt is near the currently observable service ceiling, but nutritional outcome evidence is explicitly absent.",
                "Meal delivery is an output and must not be promoted to improved nutrition without outcome measurement.",
            ],
            evidence_refs=[obs.source_ref] if obs else [],
            recommended_action="Add authorized longitudinal nutrition/outcome measurement appropriate to the beneficiary group before claiming substantive programme impact.",
            structural_candidate=False,
        ))

    if outcome_measured is None:
        data_gaps.append("Nutritional outcome measurement status is unknown; output cannot be assumed to equal outcome.")
    if integrity_assessment is None:
        data_gaps.append("No structured resource-flow reconciliation supplied; allocation/disbursement/procurement/service claims cannot be cross-checked for integrity variance.")
    if target is None or capacity is None or actual is None:
        data_gaps.append("Verified target, capacity, and actual-recipient evidence are incomplete; scarcity/access classification may be under-specified.")

    if findings:
        safe = (
            f"Identified {len(findings)} evidence-bounded MBG case finding(s). Operational and integrity signals remain distinct, and no finding constitutes a corruption determination."
        )
    else:
        safe = "No supported MBG operational failure can be diagnosed from the supplied condition evidence."

    return MBGCaseAssessment(
        programme_id=snapshot.programme_id,
        area_id=snapshot.area_id,
        area_name=snapshot.area_name,
        integrity_assessment=integrity_assessment,
        findings=findings,
        data_gaps=data_gaps,
        safe_conclusion=safe,
        governance_boundary=(
            "This adapter is decision support only. Beneficiary entitlement, budget/disbursement decisions, procurement awards, payment holds, supplier exclusion, formal audit/investigation, sanctions, criminal findings, and public accusations remain with authorized human institutions and due-process mechanisms."
        ),
    )


def load_mbg_snapshot(path: str | Path) -> MBGCaseSnapshot:
    return MBGCaseSnapshot.model_validate_json(Path(path).read_text(encoding="utf-8"))


def dump_mbg_assessment(assessment: MBGCaseAssessment) -> str:
    return json.dumps(assessment.model_dump(mode="json"), indent=2, ensure_ascii=False)
