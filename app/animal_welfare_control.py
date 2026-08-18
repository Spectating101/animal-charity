from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}_{digest}"


class Species(str, Enum):
    dog = "dog"
    cat = "cat"


class WelfareState(str, Enum):
    owned_stable = "owned_stable"
    owned_at_risk = "owned_at_risk"
    lost = "lost"
    free_roaming_owned = "free_roaming_owned"
    community_cared = "community_cared"
    unowned_free_roaming = "unowned_free_roaming"
    shelter = "shelter"
    foster = "foster"
    adoption_trial = "adoption_trial"
    stable_home = "stable_home"
    sanctuary = "sanctuary"
    specialist_candidate = "specialist_candidate"
    specialist_program = "specialist_program"


class EvidenceTier(str, Enum):
    official = "official"
    partner = "partner"
    professional = "professional"
    operator = "operator"
    public_report = "public_report"
    synthetic = "synthetic"


class AnimalObservation(BaseModel):
    observation_id: str
    area_id: str
    subject_ref: str
    species: Species
    signal: str
    value: Any
    source_ref: str
    source_tier: EvidenceTier
    confidence: float = Field(default=1.0, ge=0, le=1)
    observed_at: datetime = Field(default_factory=utcnow)
    synthetic: bool = False
    notes: str | None = None


class AreaPolicyContext(BaseModel):
    area_id: str
    area_name: str
    jurisdiction: str
    policy_flags: list[str] = Field(default_factory=list)
    priority_level: int | None = Field(default=None, ge=1, le=3)
    source_refs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class WelfareLandscape(BaseModel):
    area_id: str
    area_name: str
    observations: list[AnimalObservation] = Field(default_factory=list)
    policy_context: AreaPolicyContext | None = None
    service_capabilities: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InterventionDecision(BaseModel):
    decision_id: str
    area_id: str
    subject_ref: str
    species: Species
    current_state: WelfareState
    problem_type: str
    priority: Literal["watch", "urgent", "critical"]
    intervention_class: str
    actuator: str
    intended_transition: WelfareState | None = None
    rationale: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    human_authority_required: bool = True
    specialist_referral_only: bool = False
    welfare_guardrails: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
    synthetic: bool = False


class AreaControlAssessment(BaseModel):
    area_id: str
    area_name: str
    assessed_at: datetime = Field(default_factory=utcnow)
    decisions: list[InterventionDecision] = Field(default_factory=list)
    transition_failures: dict[str, int] = Field(default_factory=dict)
    structural_signals: list[dict[str, Any]] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    safe_conclusion: str


def _latest(landscape: WelfareLandscape, subject_ref: str, signal: str) -> AnimalObservation | None:
    rows = [x for x in landscape.observations if x.subject_ref == subject_ref and x.signal == signal]
    return max(rows, key=lambda x: x.observed_at) if rows else None


def _bool(obs: AnimalObservation | None) -> bool | None:
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


def _num(obs: AnimalObservation | None) -> float | None:
    if obs is None:
        return None
    try:
        return float(obs.value)
    except (TypeError, ValueError):
        return None


def _text(obs: AnimalObservation | None) -> str | None:
    return None if obs is None else str(obs.value)


def _confidence(rows: list[AnimalObservation]) -> float:
    return round(min((x.confidence for x in rows), default=0.0), 3)


def _decision(
    landscape: WelfareLandscape,
    subject: str,
    species: Species,
    *,
    state: WelfareState,
    problem_type: str,
    priority: Literal["watch", "urgent", "critical"],
    intervention_class: str,
    actuator: str,
    intended_transition: WelfareState | None,
    support: list[AnimalObservation],
    rationale: list[str],
    prerequisites: list[str] | None = None,
    guardrails: list[str] | None = None,
    unknowns: list[str] | None = None,
    specialist_referral_only: bool = False,
) -> InterventionDecision:
    return InterventionDecision(
        decision_id=_stable_id("wdec", landscape.area_id, subject, problem_type, intervention_class),
        area_id=landscape.area_id,
        subject_ref=subject,
        species=species,
        current_state=state,
        problem_type=problem_type,
        priority=priority,
        intervention_class=intervention_class,
        actuator=actuator,
        intended_transition=intended_transition,
        rationale=rationale,
        evidence_refs=[x.source_ref for x in support],
        prerequisites=prerequisites or [],
        specialist_referral_only=specialist_referral_only,
        welfare_guardrails=guardrails or [],
        unknowns=unknowns or [],
        confidence=_confidence(support),
        synthetic=any(x.synthetic for x in support),
    )


def route_subject(landscape: WelfareLandscape, subject: str) -> list[InterventionDecision]:
    rows = [x for x in landscape.observations if x.subject_ref == subject]
    if not rows:
        return []
    species = rows[-1].species

    state_obs = _latest(landscape, subject, "welfare_state")
    try:
        state = WelfareState(_text(state_obs)) if state_obs else WelfareState.unowned_free_roaming
    except ValueError:
        state = WelfareState.unowned_free_roaming

    acute = _bool(_latest(landscape, subject, "acute_distress"))
    injury = _bool(_latest(landscape, subject, "injured"))
    immediate_danger = _bool(_latest(landscape, subject, "immediate_public_safety_risk"))
    ownership_known = _bool(_latest(landscape, subject, "ownership_known"))
    owner_contactable = _bool(_latest(landscape, subject, "owner_contactable"))
    owner_retention_risk = _bool(_latest(landscape, subject, "owner_retention_risk"))
    owner_crisis = _text(_latest(landscape, subject, "owner_crisis_type"))
    sterilized = _bool(_latest(landscape, subject, "sterilized"))
    reproductive_risk = _bool(_latest(landscape, subject, "reproductively_active"))
    foster_available = _bool(_latest(landscape, subject, "foster_available"))
    adoption_suitable = _bool(_latest(landscape, subject, "adoption_suitable"))
    community_caretaker = _bool(_latest(landscape, subject, "responsible_community_caretaker"))
    ecology_sensitive = _bool(_latest(landscape, subject, "ecology_sensitive_location"))
    medical_stable = _bool(_latest(landscape, subject, "medical_stable"))
    human_social = _bool(_latest(landscape, subject, "human_social"))
    low_fear = _bool(_latest(landscape, subject, "low_fear_in_public"))
    low_reactivity = _bool(_latest(landscape, subject, "low_reactivity"))
    enjoys_training = _bool(_latest(landscape, subject, "enjoys_training"))

    decisions: list[InterventionDecision] = []

    emergency_support = [x for x in rows if x.signal in {"acute_distress", "injured", "immediate_public_safety_risk"}]
    if acute or injury or immediate_danger:
        decisions.append(_decision(
            landscape, subject, species,
            state=state,
            problem_type="acute_welfare_or_safety",
            priority="critical",
            intervention_class="rescue_stabilize",
            actuator="rescue.authorized_dispatch",
            intended_transition=WelfareState.shelter,
            support=emergency_support,
            rationale=["Acute distress, injury, or immediate safety risk takes precedence over population-management optimization."],
            prerequisites=["authorized responder", "safe capture/transport protocol", "medical triage"],
            guardrails=["Do not delay emergency care while seeking optimization data."],
        ))
        return decisions

    if state in {WelfareState.lost, WelfareState.free_roaming_owned} and ownership_known:
        support = [x for x in rows if x.signal in {"welfare_state", "ownership_known", "owner_contactable"}]
        if owner_contactable:
            decisions.append(_decision(
                landscape, subject, species,
                state=state,
                problem_type="lost_or_roaming_owned",
                priority="urgent",
                intervention_class="reunification",
                actuator="reunification.owner_handoff",
                intended_transition=WelfareState.owned_stable,
                support=support,
                rationale=["Known and contactable ownership makes reunification the least disruptive stable-welfare path."],
                prerequisites=["verify identity/ownership", "safe handoff", "registration/contact details update where appropriate"],
                guardrails=["Do not rehome an animal away from a verified lawful owner without proper authority."],
            ))
            return decisions
        decisions.append(_decision(
            landscape, subject, species,
            state=state,
            problem_type="lost_or_roaming_owned",
            priority="urgent",
            intervention_class="owner_trace",
            actuator="reunification.trace_owner",
            intended_transition=None,
            support=support,
            rationale=["Ownership is evidenced but a safe handoff cannot yet be completed."],
            prerequisites=["verify current contact path", "temporary safe care if needed"],
            unknowns=["owner_handoff_feasibility"],
        ))
        return decisions

    if state in {WelfareState.owned_stable, WelfareState.owned_at_risk} and owner_retention_risk:
        support = [x for x in rows if x.signal in {"welfare_state", "owner_retention_risk", "owner_crisis_type"}]
        intervention = {
            "medical_cost": "owner_support.veterinary_gap",
            "food_cost": "owner_support.food_gap",
            "temporary_housing": "owner_support.temporary_foster",
            "behavior": "owner_support.behavior_referral",
            "housing": "owner_support.pet_housing_referral",
        }.get(owner_crisis or "", "owner_support.assess_retention_gap")
        decisions.append(_decision(
            landscape, subject, species,
            state=state,
            problem_type="preventable_relinquishment",
            priority="urgent",
            intervention_class="owner_retention",
            actuator=intervention,
            intended_transition=WelfareState.owned_stable,
            support=support,
            rationale=["Preventing avoidable relinquishment keeps a stable human-animal relationship intact and avoids creating shelter/stray intake."],
            prerequisites=["owner consents to support", "verify the stated retention bottleneck"],
            guardrails=["Support must not conceal abuse, severe neglect, or an unsafe home."],
        ))
        return decisions

    free_roaming = state in {WelfareState.unowned_free_roaming, WelfareState.community_cared}
    if free_roaming and species == Species.dog and (reproductive_risk or sterilized is False):
        support = [x for x in rows if x.signal in {"welfare_state", "reproductively_active", "sterilized", "responsible_community_caretaker"}]
        decisions.append(_decision(
            landscape, subject, species,
            state=state,
            problem_type="stray_population_recruitment",
            priority="urgent",
            intervention_class="source_control",
            actuator="population.sterilize_register_manage",
            intended_transition=WelfareState.community_cared if community_caretaker and not ecology_sensitive else None,
            support=support,
            rationale=["Reproductively active free-roaming dogs can replenish the unmanaged population; source control is a structural prevention intervention."],
            prerequisites=["professional veterinary assessment", "legal/local programme eligibility", "post-operative care plan"],
            guardrails=["Sterilization is not by itself a complete welfare plan.", "Do not return animals to an unsafe or ecologically inappropriate location."],
        ))

    if free_roaming and species == Species.cat and (reproductive_risk or sterilized is False):
        support = [x for x in rows if x.signal in {"welfare_state", "reproductively_active", "sterilized", "responsible_community_caretaker", "ecology_sensitive_location"}]
        actuator = "community_cat.tnvr_managed_care" if community_caretaker and not ecology_sensitive else "community_cat.professional_site_assessment"
        decisions.append(_decision(
            landscape, subject, species,
            state=state,
            problem_type="community_cat_population_recruitment",
            priority="urgent",
            intervention_class="source_control",
            actuator=actuator,
            intended_transition=WelfareState.community_cared if actuator.endswith("managed_care") else None,
            support=support,
            rationale=["Cat population management requires a species-specific community/placement policy rather than copying dog control logic."],
            prerequisites=["professional/local programme assessment"],
            guardrails=["Do not use return-to-field where ecological or site-specific welfare risk makes it inappropriate."],
        ))

    if free_roaming and adoption_suitable:
        support = [x for x in rows if x.signal in {"welfare_state", "adoption_suitable", "foster_available", "medical_stable"}]
        if foster_available:
            decisions.append(_decision(
                landscape, subject, species,
                state=state,
                problem_type="placement_opportunity",
                priority="watch",
                intervention_class="foster_to_adoption",
                actuator="placement.foster_match",
                intended_transition=WelfareState.foster,
                support=support,
                rationale=["A suitable foster pathway can improve welfare and produce longitudinal home-behaviour evidence before adoption."],
                prerequisites=["medical clearance appropriate to placement", "verified foster", "follow-up plan"],
                guardrails=["Do not force placement solely to reduce street/shelter counts."],
            ))
        else:
            decisions.append(_decision(
                landscape, subject, species,
                state=state,
                problem_type="placement_capacity_gap",
                priority="watch",
                intervention_class="foster_capacity",
                actuator="placement.recruit_foster",
                intended_transition=None,
                support=support,
                rationale=["The animal appears placement-suitable but no foster capacity is evidenced."],
                prerequisites=["verify adoption suitability through qualified human review"],
                guardrails=["Behaviour assessment should be longitudinal; one shelter test is not enough."],
            ))

    # Specialist/therapy/assistance work is always a referral, never an automatic destination.
    specialist_support = [x for x in rows if x.signal in {"medical_stable", "human_social", "low_fear_in_public", "low_reactivity", "enjoys_training"}]
    specialist_ready = all(v is True for v in (medical_stable, human_social, low_fear, low_reactivity, enjoys_training))
    if species == Species.dog and specialist_ready:
        decisions.append(_decision(
            landscape, subject, species,
            state=state,
            problem_type="specialist_role_candidate",
            priority="watch",
            intervention_class="specialist_referral",
            actuator="specialist.referral_only",
            intended_transition=WelfareState.specialist_candidate,
            support=specialist_support,
            rationale=["Observed traits may justify specialist assessment for therapy/education/assistance work, but suitability cannot be established by this control plane."],
            prerequisites=["independent qualified trainer/organization assessment", "medical screening", "animal-welfare monitoring throughout training"],
            guardrails=["An animal never needs to work to justify rescue or care.", "Ordinary companionship is an equally successful outcome.", "Stop training if the animal shows sustained stress or poor welfare."],
            specialist_referral_only=True,
        ))

    if not decisions:
        support = [state_obs] if state_obs else rows[-1:]
        decisions.append(_decision(
            landscape, subject, species,
            state=state,
            problem_type="unresolved_welfare_path",
            priority="watch",
            intervention_class="evidence_collection",
            actuator="evidence.request",
            intended_transition=None,
            support=[x for x in support if x is not None],
            rationale=["Current evidence does not establish a safe, welfare-positive transition."],
            unknowns=["ownership", "health", "reproductive_status", "behaviour", "placement_or_community_care_feasibility"],
            guardrails=["Do not infer aggression, adoptability, ownership, or working suitability from location alone."],
        ))
    return decisions


def assess_area(landscape: WelfareLandscape) -> AreaControlAssessment:
    subjects = sorted({x.subject_ref for x in landscape.observations})
    decisions: list[InterventionDecision] = []
    for subject in subjects:
        decisions.extend(route_subject(landscape, subject))

    transition_failures = Counter(d.intervention_class for d in decisions if d.intervention_class not in {"specialist_referral", "evidence_collection"})
    structural_signals: list[dict[str, Any]] = []
    for intervention_class, count in transition_failures.items():
        if count >= 3:
            structural_signals.append({
                "intervention_class": intervention_class,
                "count": count,
                "proposal": {
                    "owner_retention": "Consider an owner-retention support programme if cases recur across households.",
                    "source_control": "Consider a targeted sterilization/registration/community-management initiative.",
                    "foster_capacity": "Consider a verified foster recruitment and support network.",
                    "foster_to_adoption": "Consider increasing foster/adoption throughput rather than building shelter capacity first.",
                    "rescue_stabilize": "Review rescue-response capacity and geographic access before adding permanent facilities.",
                }.get(intervention_class, "Review whether repeated case-level work indicates a structural service gap."),
            })

    data_gaps: list[str] = []
    if not landscape.observations:
        data_gaps.append("No animal-level condition evidence was supplied; policy priority alone cannot establish individual welfare states.")
    signals = {x.signal for x in landscape.observations}
    for signal in ("welfare_state", "ownership_known", "sterilized", "medical_stable"):
        if signal not in signals:
            data_gaps.append(f"Landscape lacks broad coverage for {signal}.")

    if decisions:
        safe_conclusion = (
            f"Generated {len(decisions)} evidence-bounded intervention decision(s) across {len(subjects)} subject(s). "
            "Specialist social/working roles are referral-only and never treated as a population-management objective."
        )
    else:
        safe_conclusion = "No animal-level intervention can be justified from the supplied evidence."

    return AreaControlAssessment(
        area_id=landscape.area_id,
        area_name=landscape.area_name,
        decisions=decisions,
        transition_failures=dict(transition_failures),
        structural_signals=structural_signals,
        data_gaps=data_gaps,
        safe_conclusion=safe_conclusion,
    )


def load_landscape(path: str | Path) -> WelfareLandscape:
    return WelfareLandscape.model_validate_json(Path(path).read_text(encoding="utf-8"))


def dump_assessment(assessment: AreaControlAssessment) -> str:
    return json.dumps(assessment.model_dump(mode="json"), indent=2, ensure_ascii=False)
