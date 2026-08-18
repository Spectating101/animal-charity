from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.animal_welfare_control import (
    AreaControlAssessment,
    EvidenceTier,
    WelfareLandscape,
    assess_area,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}_{digest}"


class OneWelfareDomain(str, Enum):
    animal = "animal"
    human = "human"
    environment = "environment"


class DeterminantKind(str, Enum):
    income = "income"
    housing = "housing"
    transportation = "transportation"
    veterinary_access = "veterinary_access"
    food_access = "food_access"
    information_access = "information_access"
    language_access = "language_access"
    social_support = "social_support"
    service_capacity = "service_capacity"
    foster_capacity = "foster_capacity"
    population_control_access = "population_control_access"
    public_safety = "public_safety"
    ecology = "ecology"
    owner_health = "owner_health"
    time_care_capacity = "time_care_capacity"


class DeterminantObservation(BaseModel):
    observation_id: str
    area_id: str
    determinant: DeterminantKind
    value: Any
    source_ref: str
    source_tier: EvidenceTier
    confidence: float = Field(default=1.0, ge=0, le=1)
    observed_at: datetime = Field(default_factory=utcnow)
    scope: Literal["area", "household", "subject"] = "area"
    subject_ref: str | None = None
    relationship: Literal["context", "hypothesis", "established"] = "context"
    synthetic: bool = False
    notes: str | None = None


class ServiceAccessObservation(BaseModel):
    observation_id: str
    area_id: str
    service_kind: str
    source_ref: str
    source_tier: EvidenceTier
    available: bool | None = None
    affordable: bool | None = None
    geographically_accessible: bool | None = None
    transport_feasible: bool | None = None
    information_accessible: bool | None = None
    capacity_available: bool | None = None
    confidence: float = Field(default=1.0, ge=0, le=1)
    observed_at: datetime = Field(default_factory=utcnow)
    synthetic: bool = False
    notes: str | None = None


class PreventiveWelfareSnapshot(BaseModel):
    area_id: str
    area_name: str
    landscape: WelfareLandscape
    determinants: list[DeterminantObservation] = Field(default_factory=list)
    service_access: list[ServiceAccessObservation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PreventionOpportunity(BaseModel):
    opportunity_id: str
    transition_type: str
    intervention_class: str
    priority: Literal["watch", "urgent", "critical"]
    prevention_window: Literal["upstream", "immediate", "post_transition"]
    causal_status: Literal["context_only", "hypothesis", "supported"]
    rationale: list[str] = Field(default_factory=list)
    determinant_refs: list[str] = Field(default_factory=list)
    service_refs: list[str] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    one_welfare_domains: list[OneWelfareDomain] = Field(default_factory=list)
    recommended_action: str
    structural_candidate: bool = False
    human_authority_required: bool = True
    transferable_architecture_pattern: str
    synthetic: bool = False


class PreventiveSystemAssessment(BaseModel):
    area_id: str
    area_name: str
    assessed_at: datetime = Field(default_factory=utcnow)
    lifecycle_assessment: AreaControlAssessment
    determinant_summary: dict[str, int] = Field(default_factory=dict)
    access_gaps: list[dict[str, Any]] = Field(default_factory=list)
    prevention_opportunities: list[PreventionOpportunity] = Field(default_factory=list)
    research_signals: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    transfer_boundary: str
    safe_conclusion: str


INTERVENTION_TO_TRANSITION = {
    "owner_retention": "stable_owned_to_relinquishment_or_abandonment",
    "reunification": "lost_or_roaming_owned_to_unmanaged_displacement",
    "owner_trace": "lost_or_roaming_owned_to_unmanaged_displacement",
    "source_control": "reproductively_active_roaming_to_new_unmanaged_animals",
    "foster_capacity": "placement_ready_to_prolonged_unstable_care",
    "foster_to_adoption": "unstable_placement_to_stable_home",
    "rescue_stabilize": "acute_condition_to_severe_welfare_or_safety_harm",
}

INTERVENTION_TO_DEFAULT_DETERMINANTS = {
    "owner_retention": {
        DeterminantKind.income,
        DeterminantKind.housing,
        DeterminantKind.veterinary_access,
        DeterminantKind.food_access,
        DeterminantKind.owner_health,
        DeterminantKind.time_care_capacity,
        DeterminantKind.transportation,
        DeterminantKind.information_access,
    },
    "reunification": {
        DeterminantKind.transportation,
        DeterminantKind.information_access,
        DeterminantKind.service_capacity,
    },
    "owner_trace": {
        DeterminantKind.information_access,
        DeterminantKind.service_capacity,
    },
    "source_control": {
        DeterminantKind.population_control_access,
        DeterminantKind.transportation,
        DeterminantKind.information_access,
        DeterminantKind.service_capacity,
    },
    "foster_capacity": {
        DeterminantKind.foster_capacity,
        DeterminantKind.social_support,
        DeterminantKind.service_capacity,
    },
    "foster_to_adoption": {
        DeterminantKind.foster_capacity,
        DeterminantKind.social_support,
        DeterminantKind.service_capacity,
    },
    "rescue_stabilize": {
        DeterminantKind.transportation,
        DeterminantKind.veterinary_access,
        DeterminantKind.service_capacity,
        DeterminantKind.public_safety,
    },
}


def _access_gaps(rows: list[ServiceAccessObservation]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for row in rows:
        dimensions: list[str] = []
        for field in (
            "available",
            "affordable",
            "geographically_accessible",
            "transport_feasible",
            "information_accessible",
            "capacity_available",
        ):
            if getattr(row, field) is False:
                dimensions.append(field)
        if dimensions:
            gaps.append({
                "service_kind": row.service_kind,
                "failed_dimensions": dimensions,
                "source_ref": row.source_ref,
                "confidence": row.confidence,
                "synthetic": row.synthetic,
            })
    return gaps


def _relevant_determinants(
    snapshot: PreventiveWelfareSnapshot,
    intervention_class: str,
    subject_ref: str,
) -> list[DeterminantObservation]:
    kinds = INTERVENTION_TO_DEFAULT_DETERMINANTS.get(intervention_class, set())
    rows = [d for d in snapshot.determinants if d.determinant in kinds]
    return [
        d for d in rows
        if d.scope == "area" or d.subject_ref == subject_ref
    ]


def _causal_status(rows: list[DeterminantObservation]) -> Literal["context_only", "hypothesis", "supported"]:
    if any(r.relationship == "established" for r in rows):
        return "supported"
    if any(r.relationship == "hypothesis" for r in rows):
        return "hypothesis"
    return "context_only"


def _domains(intervention_class: str, determinants: list[DeterminantObservation]) -> list[OneWelfareDomain]:
    domains = {OneWelfareDomain.animal}
    human_or_service_system_determinants = {
        DeterminantKind.income,
        DeterminantKind.housing,
        DeterminantKind.transportation,
        DeterminantKind.veterinary_access,
        DeterminantKind.food_access,
        DeterminantKind.information_access,
        DeterminantKind.language_access,
        DeterminantKind.social_support,
        DeterminantKind.service_capacity,
        DeterminantKind.foster_capacity,
        DeterminantKind.population_control_access,
        DeterminantKind.owner_health,
        DeterminantKind.time_care_capacity,
    }
    if any(d.determinant in human_or_service_system_determinants for d in determinants):
        domains.add(OneWelfareDomain.human)
    if intervention_class == "source_control" or any(
        d.determinant == DeterminantKind.ecology for d in determinants
    ):
        domains.add(OneWelfareDomain.environment)
    return sorted(domains, key=lambda x: x.value)


def _recommended_action(intervention_class: str, causal_status: str) -> str:
    prefix = "Verify the suspected determinant before scaling; then " if causal_status == "context_only" else ""
    return prefix + {
        "owner_retention": "resolve the smallest verified household barrier before shelter intake or abandonment occurs.",
        "reunification": "repair identification/contact/transport access and reunify before unmanaged displacement persists.",
        "owner_trace": "improve owner-tracing and temporary safe-care capacity before treating the animal as unowned.",
        "source_control": "increase targeted sterilization/registration/responsible-management access before new unmanaged recruitment occurs.",
        "foster_capacity": "expand verified foster capacity and caregiver support before placement-ready animals accumulate in unstable care.",
        "foster_to_adoption": "support stable placement and follow-up rather than maximizing one-time adoption transactions.",
        "rescue_stabilize": "repair emergency response, transport, or clinical access so acute cases are stabilized earlier.",
    }.get(intervention_class, "collect causal and service-access evidence before selecting a preventive programme.")


def assess_preventive_system(snapshot: PreventiveWelfareSnapshot) -> PreventiveSystemAssessment:
    if snapshot.landscape.area_id != snapshot.area_id:
        raise ValueError("landscape area_id must match preventive snapshot area_id")

    lifecycle = assess_area(snapshot.landscape)
    determinant_summary = dict(Counter(d.determinant.value for d in snapshot.determinants))
    access_gaps = _access_gaps(snapshot.service_access)

    opportunities: list[PreventionOpportunity] = []
    class_counts = Counter(d.intervention_class for d in lifecycle.decisions)

    for decision in lifecycle.decisions:
        if decision.intervention_class in {"specialist_referral", "evidence_collection"}:
            continue
        transition = INTERVENTION_TO_TRANSITION.get(decision.intervention_class)
        if not transition:
            continue
        determinants = _relevant_determinants(snapshot, decision.intervention_class, decision.subject_ref)
        causal_status = _causal_status(determinants)
        relevant_access = [
            row for row in snapshot.service_access
            if any(getattr(row, field) is False for field in (
                "available",
                "affordable",
                "geographically_accessible",
                "transport_feasible",
                "information_accessible",
                "capacity_available",
            ))
        ]
        structural = class_counts[decision.intervention_class] >= 3
        opportunities.append(PreventionOpportunity(
            opportunity_id=_stable_id("pwo", snapshot.area_id, decision.subject_ref, transition),
            transition_type=transition,
            intervention_class=decision.intervention_class,
            priority=decision.priority,
            prevention_window="immediate" if decision.priority == "critical" else "upstream",
            causal_status=causal_status,
            rationale=(
                [f"Lifecycle router identified {decision.intervention_class} for {decision.subject_ref}."]
                + (["Relevant social/service determinants are observed, but context is not proof of causation."] if determinants else ["No relevant determinant evidence is currently attached to this case."])
                + (["Repeated cases make this a structural-programme candidate, subject to temporal/service-gap gates."] if structural else [])
            ),
            determinant_refs=[d.source_ref for d in determinants],
            service_refs=[s.source_ref for s in relevant_access],
            decision_refs=[decision.decision_id],
            one_welfare_domains=_domains(decision.intervention_class, determinants),
            recommended_action=_recommended_action(decision.intervention_class, causal_status),
            structural_candidate=structural,
            transferable_architecture_pattern=(
                "detect_pre_crisis_transition->verify_driver->repair_access_or_resource_gap->verify_stable_outcome"
            ),
            synthetic=decision.synthetic or any(d.synthetic for d in determinants),
        ))

    research_signals: list[str] = []
    if access_gaps:
        research_signals.append(
            "Service-access failure is present: distinguish absolute resource scarcity from affordability, geography, transport, information, or capacity barriers."
        )
    if any(len(o.one_welfare_domains) >= 2 for o in opportunities):
        research_signals.append(
            "At least one prevention opportunity crosses animal and human/environmental domains; evaluate coupled outcomes rather than animal-only throughput."
        )
    structural_classes = sorted({o.intervention_class for o in opportunities if o.structural_candidate})
    if structural_classes:
        research_signals.append(
            "Repeated transition failures detected for: " + ", ".join(structural_classes) + ". Compare extension of existing services against reversible new initiatives."
        )

    data_gaps = list(lifecycle.data_gaps)
    if lifecycle.decisions and not snapshot.determinants:
        data_gaps.append("No social/service determinant evidence supplied; root-cause prevention remains under-specified.")
    if lifecycle.decisions and not snapshot.service_access:
        data_gaps.append("No structured service-access evidence supplied; welfare-desert/access hypotheses cannot be tested.")
    if any(o.causal_status == "context_only" for o in opportunities):
        data_gaps.append("Contextual determinants must not be promoted to causal claims without household/subject or stronger causal evidence.")

    if opportunities:
        safe_conclusion = (
            f"Identified {len(opportunities)} preventive transition opportunity/opportunities. "
            "Determinants and service gaps are treated as contextual evidence or hypotheses unless explicitly established."
        )
    else:
        safe_conclusion = (
            "No preventive transition opportunity can be justified from the supplied lifecycle and determinant evidence."
        )

    return PreventiveSystemAssessment(
        area_id=snapshot.area_id,
        area_name=snapshot.area_name,
        lifecycle_assessment=lifecycle,
        determinant_summary=determinant_summary,
        access_gaps=access_gaps,
        prevention_opportunities=opportunities,
        research_signals=research_signals,
        data_gaps=data_gaps,
        transfer_boundary=(
            "Only the evidence/transition/access/intervention/evaluation architecture may later generalize to human welfare. "
            "Animal-specific policy rules must not be transferred. Human applications require their own rights, autonomy, entitlement, consent, anti-discrimination, and governance model."
        ),
        safe_conclusion=safe_conclusion,
    )


def load_preventive_snapshot(path: str | Path) -> PreventiveWelfareSnapshot:
    return PreventiveWelfareSnapshot.model_validate_json(Path(path).read_text(encoding="utf-8"))


def dump_preventive_assessment(assessment: PreventiveSystemAssessment) -> str:
    return json.dumps(assessment.model_dump(mode="json"), indent=2, ensure_ascii=False)
