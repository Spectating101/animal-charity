from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.animal_welfare_control import AreaControlAssessment, WelfareLandscape, assess_area
from app.mbg_case_study import MBGCaseAssessment, MBGCaseSnapshot, assess_mbg_case


ROOT = Path(__file__).resolve().parents[1]
DOMAIN_REGISTRY = ROOT / "config" / "domains" / "public_good_domains.json"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PublicGoodDomain(str, Enum):
    animal_welfare = "animal_welfare"
    mbg_public_nutrition = "mbg_public_nutrition"
    disaster_response = "disaster_response"


class EvidenceManifestEntry(BaseModel):
    source_ref: str
    source_kind: Literal["official", "partner", "professional", "operator", "public", "transaction", "sensor", "synthetic", "other"] = "other"
    verification_status: Literal["reported", "corroborated", "verified"] = "reported"
    sensitivity: Literal["public", "internal", "sensitive", "restricted"] = "internal"
    observed_at: datetime | None = None
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    notes: str | None = None


class PublicGoodCase(BaseModel):
    case_id: str
    domain: PublicGoodDomain
    payload: dict[str, Any]
    evidence_manifest: list[EvidenceManifestEntry] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def manifest_refs_must_be_unique(self) -> "PublicGoodCase":
        refs = [entry.source_ref for entry in self.evidence_manifest]
        if len(refs) != len(set(refs)):
            raise ValueError("evidence_manifest source_ref values must be unique")
        return self


class NormalizedFinding(BaseModel):
    stage: Literal[
        "safety",
        "stabilize",
        "prevent",
        "route",
        "integrity",
        "capacity",
        "access",
        "outcome",
        "evidence",
    ]
    problem_class: str
    priority: Literal["watch", "urgent", "critical"]
    recommended_action: str
    evidence_refs: list[str] = Field(default_factory=list)
    human_authority_required: bool = True
    structural_candidate: bool = False
    domain_detail: dict[str, Any] = Field(default_factory=dict)


class EvidenceManifestSummary(BaseModel):
    status: Literal["not_supplied", "complete", "incomplete"]
    cited_ref_count: int = 0
    registered_ref_count: int = 0
    missing_refs: list[str] = Field(default_factory=list)
    verified_ref_count: int = 0
    sensitive_ref_count: int = 0


class PublicGoodAssessment(BaseModel):
    case_id: str
    domain: PublicGoodDomain
    assessed_at: datetime = Field(default_factory=utcnow)
    constitution_ref: str
    unit_of_concern: str
    desired_state: str
    shared_loop: list[str]
    hard_gates: list[str]
    normalized_findings: list[NormalizedFinding] = Field(default_factory=list)
    evidence_manifest: EvidenceManifestSummary
    data_gaps: list[str] = Field(default_factory=list)
    safe_conclusion: str
    non_transfer_rule: str
    domain_result: dict[str, Any]


def _registry() -> dict[str, Any]:
    return json.loads(DOMAIN_REGISTRY.read_text(encoding="utf-8"))


def _animal_stage(intervention_class: str) -> str:
    if intervention_class == "rescue_stabilize":
        return "stabilize"
    if intervention_class in {"reunification", "owner_retention", "source_control"}:
        return "prevent"
    if intervention_class in {"foster_to_adoption", "foster_capacity", "specialist_referral", "owner_trace"}:
        return "route"
    return "evidence"


def _normalize_animal(result: AreaControlAssessment) -> list[NormalizedFinding]:
    normalized: list[NormalizedFinding] = []
    structural_classes = {str(x.get("intervention_class")) for x in result.structural_signals}
    for decision in result.decisions:
        normalized.append(
            NormalizedFinding(
                stage=_animal_stage(decision.intervention_class),
                problem_class=decision.problem_type,
                priority=decision.priority,
                recommended_action=f"{decision.actuator}: " + (decision.rationale[0] if decision.rationale else "Follow domain decision."),
                evidence_refs=decision.evidence_refs,
                human_authority_required=decision.human_authority_required,
                structural_candidate=decision.intervention_class in structural_classes,
                domain_detail={
                    "subject_ref": decision.subject_ref,
                    "intervention_class": decision.intervention_class,
                    "actuator": decision.actuator,
                    "intended_transition": decision.intended_transition.value if decision.intended_transition else None,
                    "prerequisites": decision.prerequisites,
                    "guardrails": decision.welfare_guardrails,
                    "unknowns": decision.unknowns,
                },
            )
        )
    return normalized


def _mbg_stage(problem_class: str) -> str:
    return {
        "food_safety_failure": "safety",
        "integrity_uncertainty": "integrity",
        "capacity_gap": "capacity",
        "access_or_delivery_gap": "access",
        "targeting_or_data_gap": "access",
        "outcome_evidence_gap": "outcome",
        "cause_unresolved": "evidence",
    }.get(problem_class, "evidence")


def _normalize_mbg(result: MBGCaseAssessment) -> list[NormalizedFinding]:
    return [
        NormalizedFinding(
            stage=_mbg_stage(finding.problem_class),
            problem_class=finding.problem_class,
            priority=finding.priority,
            recommended_action=finding.recommended_action,
            evidence_refs=finding.evidence_refs,
            human_authority_required=finding.human_authority_required,
            structural_candidate=finding.structural_candidate,
            domain_detail={"rationale": finding.rationale},
        )
        for finding in result.findings
    ]


def _normalize_disaster(result: Any) -> list[NormalizedFinding]:
    return [
        NormalizedFinding(
            stage=finding.stage,
            problem_class=finding.problem_class,
            priority=finding.priority,
            recommended_action=finding.recommended_action,
            evidence_refs=finding.evidence_refs,
            human_authority_required=finding.human_authority_required,
            structural_candidate=finding.structural_candidate,
            domain_detail={
                "need_id": finding.need_id,
                "location_ref": finding.location_ref,
                "resource_refs": finding.resource_refs,
                "rationale": finding.rationale,
            },
        )
        for finding in result.findings
    ]


def _manifest_summary(case: PublicGoodCase, normalized: list[NormalizedFinding]) -> EvidenceManifestSummary:
    cited = sorted({ref for finding in normalized for ref in finding.evidence_refs if ref})
    if not case.evidence_manifest:
        return EvidenceManifestSummary(status="not_supplied", cited_ref_count=len(cited))
    by_ref = {entry.source_ref: entry for entry in case.evidence_manifest}
    missing = [ref for ref in cited if ref not in by_ref]
    return EvidenceManifestSummary(
        status="incomplete" if missing else "complete",
        cited_ref_count=len(cited),
        registered_ref_count=len(by_ref),
        missing_refs=missing,
        verified_ref_count=sum(1 for entry in by_ref.values() if entry.verification_status == "verified"),
        sensitive_ref_count=sum(1 for entry in by_ref.values() if entry.sensitivity in {"sensitive", "restricted"}),
    )


def assess_public_good_case(case: PublicGoodCase) -> PublicGoodAssessment:
    registry = _registry()
    profile = registry["domains"][case.domain.value]

    if case.domain == PublicGoodDomain.animal_welfare:
        payload = WelfareLandscape.model_validate(case.payload)
        domain_result = assess_area(payload)
        normalized = _normalize_animal(domain_result)
        data_gaps = list(domain_result.data_gaps)
        safe_conclusion = domain_result.safe_conclusion
    elif case.domain == PublicGoodDomain.mbg_public_nutrition:
        payload = MBGCaseSnapshot.model_validate(case.payload)
        domain_result = assess_mbg_case(payload)
        normalized = _normalize_mbg(domain_result)
        data_gaps = list(domain_result.data_gaps)
        safe_conclusion = domain_result.safe_conclusion
    elif case.domain == PublicGoodDomain.disaster_response:
        # Lazy import avoids coupling the core evidence model back through the
        # interoperability module during module initialization.
        from app.disaster_control import DisasterSnapshot, assess_disaster

        payload = DisasterSnapshot.model_validate(case.payload)
        domain_result = assess_disaster(payload)
        normalized = _normalize_disaster(domain_result)
        data_gaps = list(domain_result.data_gaps)
        safe_conclusion = domain_result.safe_conclusion
    else:  # defensive; enum validation should prevent this path.
        raise ValueError(f"unsupported public-good domain: {case.domain}")

    manifest = _manifest_summary(case, normalized)
    if manifest.status == "incomplete":
        data_gaps.append(
            "Evidence manifest does not register all source references cited by the assessment: "
            + ", ".join(manifest.missing_refs[:10])
        )

    return PublicGoodAssessment(
        case_id=case.case_id,
        domain=case.domain,
        constitution_ref=profile["constitution_ref"],
        unit_of_concern=profile["unit_of_concern"],
        desired_state=profile["desired_state"],
        shared_loop=registry["shared_loop"],
        hard_gates=profile["hard_gates"],
        normalized_findings=normalized,
        evidence_manifest=manifest,
        data_gaps=data_gaps,
        safe_conclusion=safe_conclusion,
        non_transfer_rule=registry["non_transfer_rule"],
        domain_result=domain_result.model_dump(mode="json"),
    )


def load_public_good_case(path: str | Path) -> PublicGoodCase:
    return PublicGoodCase.model_validate_json(Path(path).read_text(encoding="utf-8"))


def dump_public_good_assessment(assessment: PublicGoodAssessment) -> str:
    return json.dumps(assessment.model_dump(mode="json"), indent=2, ensure_ascii=False)
