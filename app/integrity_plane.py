from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IntegrityStage(str, Enum):
    allocation = "allocation"
    disbursement = "disbursement"
    procurement = "procurement"
    physical_input = "physical_input"
    service_output = "service_output"
    beneficiary_receipt = "beneficiary_receipt"
    outcome = "outcome"


class VerificationStatus(str, Enum):
    reported = "reported"
    corroborated = "corroborated"
    verified = "verified"


class FlowObservation(BaseModel):
    observation_id: str
    stage: IntegrityStage
    metric: str
    value: float
    unit: str
    source_ref: str
    verification_status: VerificationStatus = VerificationStatus.reported
    confidence: float = Field(default=1.0, ge=0, le=1)
    observed_at: datetime = Field(default_factory=utcnow)
    synthetic: bool = False
    notes: str | None = None


class ReconciliationCheck(BaseModel):
    check_id: str
    expected_observation_id: str
    observed_observation_id: str
    tolerance_pct: float = Field(default=0.05, ge=0, le=1)
    tolerance_abs: float | None = Field(default=None, ge=0)
    critical: bool = False
    innocent_explanations_to_check: list[str] = Field(default_factory=list)
    notes: str | None = None


class IntegritySnapshot(BaseModel):
    programme_id: str
    area_id: str
    observations: list[FlowObservation] = Field(default_factory=list)
    checks: list[ReconciliationCheck] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class IntegrityFinding(BaseModel):
    check_id: str
    status: Literal[
        "normal",
        "evidence_gap",
        "variance_needs_explanation",
        "integrity_risk",
        "audit_referral_recommended",
    ]
    expected_observation_id: str
    observed_observation_id: str
    expected_value: float | None = None
    observed_value: float | None = None
    unit: str | None = None
    absolute_variance: float | None = None
    variance_pct: float | None = None
    rationale: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    explanations_to_check: list[str] = Field(default_factory=list)
    synthetic: bool = False


class IntegrityAssessment(BaseModel):
    programme_id: str
    area_id: str
    assessed_at: datetime = Field(default_factory=utcnow)
    overall_status: Literal[
        "normal",
        "evidence_gap",
        "variance_needs_explanation",
        "integrity_risk",
        "audit_referral_recommended",
    ]
    findings: list[IntegrityFinding] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    safe_conclusion: str


_STATUS_RANK = {
    "normal": 0,
    "evidence_gap": 1,
    "variance_needs_explanation": 2,
    "integrity_risk": 3,
    "audit_referral_recommended": 4,
}


def _material_variance(expected: float, observed: float, check: ReconciliationCheck) -> tuple[bool, float, float | None]:
    absolute = abs(expected - observed)
    pct = None if expected == 0 else absolute / abs(expected)
    material = absolute > (check.tolerance_abs or 0)
    if expected != 0:
        material = material and pct is not None and pct > check.tolerance_pct
    return material, absolute, pct


def _trustworthy(obs: FlowObservation) -> bool:
    return obs.verification_status in {VerificationStatus.corroborated, VerificationStatus.verified}


def assess_integrity(snapshot: IntegritySnapshot) -> IntegrityAssessment:
    by_id = {o.observation_id: o for o in snapshot.observations}
    findings: list[IntegrityFinding] = []
    data_gaps: list[str] = []

    for check in snapshot.checks:
        expected = by_id.get(check.expected_observation_id)
        observed = by_id.get(check.observed_observation_id)
        if expected is None or observed is None:
            missing = [
                ref for ref, obs in (
                    (check.expected_observation_id, expected),
                    (check.observed_observation_id, observed),
                ) if obs is None
            ]
            data_gaps.append(f"{check.check_id}: missing observation(s): {', '.join(missing)}")
            findings.append(IntegrityFinding(
                check_id=check.check_id,
                status="evidence_gap",
                expected_observation_id=check.expected_observation_id,
                observed_observation_id=check.observed_observation_id,
                rationale=["The reconciliation cannot be evaluated because required evidence is missing."],
                explanations_to_check=check.innocent_explanations_to_check,
            ))
            continue

        if expected.unit != observed.unit:
            data_gaps.append(
                f"{check.check_id}: unit mismatch {expected.unit!r} vs {observed.unit!r}; normalize before comparison"
            )
            findings.append(IntegrityFinding(
                check_id=check.check_id,
                status="evidence_gap",
                expected_observation_id=expected.observation_id,
                observed_observation_id=observed.observation_id,
                expected_value=expected.value,
                observed_value=observed.value,
                rationale=["The two claims use incompatible units and must not be reconciled directly."],
                evidence_refs=[expected.source_ref, observed.source_ref],
                explanations_to_check=check.innocent_explanations_to_check,
                synthetic=expected.synthetic or observed.synthetic,
            ))
            continue

        material, absolute, pct = _material_variance(expected.value, observed.value, check)
        if not material:
            status = "normal"
            rationale = ["Observed variance is within the explicitly supplied reconciliation tolerance."]
        elif not (_trustworthy(expected) and _trustworthy(observed)):
            status = "variance_needs_explanation"
            rationale = [
                "A material variance exists, but at least one side is not independently corroborated/verified.",
                "Request stronger records before treating the variance as an integrity risk.",
            ]
        elif check.critical:
            status = "audit_referral_recommended"
            rationale = [
                "A material variance remains between independently corroborated/verified claims on a critical reconciliation.",
                "Human audit review is warranted before expansion, payment/sanction decisions, or public attribution.",
            ]
        else:
            status = "integrity_risk"
            rationale = [
                "A material variance remains between independently corroborated/verified claims.",
                "This is an integrity risk signal, not proof of fraud or corruption.",
            ]

        findings.append(IntegrityFinding(
            check_id=check.check_id,
            status=status,
            expected_observation_id=expected.observation_id,
            observed_observation_id=observed.observation_id,
            expected_value=expected.value,
            observed_value=observed.value,
            unit=expected.unit,
            absolute_variance=round(absolute, 6),
            variance_pct=None if pct is None else round(pct, 6),
            rationale=rationale,
            evidence_refs=[expected.source_ref, observed.source_ref],
            explanations_to_check=check.innocent_explanations_to_check,
            synthetic=expected.synthetic or observed.synthetic,
        ))

    overall = max((f.status for f in findings), key=lambda x: _STATUS_RANK[x], default="normal")
    if overall == "normal":
        safe = "No material integrity variance is established by the supplied reconciliation checks."
    else:
        safe = (
            f"Integrity assessment status: {overall}. A mismatch can justify reconciliation or human audit review, "
            "but this engine does not determine fraud, corruption, culpability, criminality, or sanctions."
        )

    return IntegrityAssessment(
        programme_id=snapshot.programme_id,
        area_id=snapshot.area_id,
        overall_status=overall,
        findings=findings,
        data_gaps=data_gaps,
        safe_conclusion=safe,
    )


def load_integrity_snapshot(path: str | Path) -> IntegritySnapshot:
    return IntegritySnapshot.model_validate_json(Path(path).read_text(encoding="utf-8"))


def dump_integrity_assessment(assessment: IntegrityAssessment) -> str:
    return json.dumps(assessment.model_dump(mode="json"), indent=2, ensure_ascii=False)
