from __future__ import annotations

import hashlib
import math
from collections import Counter
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class TransitionFailureEvent(BaseModel):
    event_id: str
    area_id: str
    subject_ref: str
    intervention_class: str
    occurred_at: datetime
    lat: float
    lon: float
    source_ref: str
    confidence: float = Field(default=1.0, ge=0, le=1)
    synthetic: bool = False


class ExistingWelfareService(BaseModel):
    service_id: str
    name: str
    supported_interventions: list[str]
    lat: float
    lon: float
    service_radius_km: float = Field(default=8, gt=0)
    verified: bool = True
    may_expand: bool = False
    source_ref: str


class CandidateWelfareHost(BaseModel):
    host_id: str
    name: str
    lat: float
    lon: float
    supported_interventions: list[str] = Field(default_factory=list)
    available: bool = False
    availability_evidence_ref: str | None = None
    source_ref: str


class LifecycleInitiativeLandscape(BaseModel):
    area_id: str
    area_name: str
    horizon_days: int = Field(default=90, gt=0)
    events: list[TransitionFailureEvent] = Field(default_factory=list)
    existing_services: list[ExistingWelfareService] = Field(default_factory=list)
    candidate_hosts: list[CandidateWelfareHost] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class LifecycleInitiativeOption(BaseModel):
    mode: Literal[
        "case_level_only",
        "partner_extension",
        "periodic_pop_up",
        "mobile_service",
        "permanent_service",
    ]
    intervention_class: str
    programme_label: str
    site_id: str | None = None
    site_name: str | None = None
    coverage_ratio: float = Field(default=0, ge=0, le=1)
    burden_score: float = Field(default=0, ge=0, le=100)
    benefit_score: float = Field(default=0, ge=0, le=100)
    total_score: float = 0
    blockers: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)


class LifecycleInitiativePlan(BaseModel):
    plan_id: str
    area_id: str
    area_name: str
    intervention_class: str
    status: Literal[
        "insufficient_evidence",
        "case_level_response_only",
        "pilot_candidate",
        "ready_for_human_validation",
    ]
    structural_gap_established: bool
    evidence_summary: dict
    recommended: LifecycleInitiativeOption
    alternatives: list[LifecycleInitiativeOption] = Field(default_factory=list)
    implementation_steps: list[str] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    synthetic: bool = False


PROGRAMMES = {
    "source_control": {
        "label": "targeted sterilization / registration / responsible-community-management outreach",
        "metrics": [
            "verified intact free-roaming animals remaining",
            "new litter / unmanaged recruitment observations",
            "registration and owner-engagement completion",
            "post-operative welfare incidents",
            "public-safety / wildlife-conflict trend",
        ],
    },
    "owner_retention": {
        "label": "pet owner-retention support and intake-diversion service",
        "metrics": [
            "verified relinquishments prevented",
            "30/90-day home stability after assistance",
            "repeat crisis requests",
            "cost per stable retained placement",
        ],
    },
    "foster_capacity": {
        "label": "verified foster recruitment and caregiver-support network",
        "metrics": [
            "verified foster capacity added",
            "days animals spend in foster vs shelter",
            "placement throughput",
            "foster breakdown / return rate",
            "30/90-day post-placement stability",
        ],
    },
    "foster_to_adoption": {
        "label": "foster/adoption throughput and placement-support programme",
        "metrics": [
            "time to stable placement",
            "adoption/foster return rate",
            "post-placement support use",
            "30/90-day placement stability",
        ],
    },
    "rescue_stabilize": {
        "label": "authorized rescue-response capacity extension",
        "metrics": [
            "time from verified urgent case to accepted response",
            "unresolved critical-case hours",
            "failed handoffs",
            "responder/animal safety incidents",
        ],
    },
    "reunification": {
        "label": "lost-animal identification and reunification support",
        "metrics": [
            "time to owner contact",
            "verified reunification rate",
            "shelter intake avoided",
            "repeat roaming/loss within 90 days",
        ],
    },
}

MODE_BURDEN = {
    "case_level_only": 5,
    "partner_extension": 15,
    "periodic_pop_up": 28,
    "mobile_service": 35,
    "permanent_service": 60,
}


def _summary(events: list[TransitionFailureEvent]) -> dict:
    if not events:
        return {"events": 0, "subjects": 0, "days": 0, "span_days": 0, "mean_confidence": 0.0}
    days = {e.occurred_at.date().isoformat() for e in events}
    span = max(1, (max(e.occurred_at for e in events) - min(e.occurred_at for e in events)).days + 1)
    return {
        "events": len(events),
        "subjects": len({e.subject_ref for e in events}),
        "days": len(days),
        "span_days": span,
        "mean_confidence": round(sum(e.confidence for e in events) / len(events), 3),
    }


def _centroid(events: list[TransitionFailureEvent]) -> tuple[float, float]:
    if not events:
        return 0.0, 0.0
    total = sum(max(0.1, e.confidence) for e in events)
    return (
        sum(e.lat * max(0.1, e.confidence) for e in events) / total,
        sum(e.lon * max(0.1, e.confidence) for e in events) / total,
    )


def _coverage(events: list[TransitionFailureEvent], lat: float, lon: float, radius_km: float) -> float:
    if not events:
        return 0.0
    total = sum(max(0.1, e.confidence) for e in events)
    reached = sum(max(0.1, e.confidence) for e in events if _km(e.lat, e.lon, lat, lon) <= radius_km)
    return round(reached / total, 3) if total else 0.0


def _option(
    intervention_class: str,
    mode: str,
    coverage: float,
    *,
    site_id: str | None = None,
    site_name: str | None = None,
    blockers: list[str] | None = None,
    rationale: list[str] | None = None,
    reuse_bonus: float = 0,
) -> LifecycleInitiativeOption:
    label = PROGRAMMES.get(intervention_class, {}).get("label", f"{intervention_class} service")
    burden = MODE_BURDEN[mode]
    benefit = min(100.0, coverage * 85 + reuse_bonus)
    blocker_penalty = 15 * len(blockers or [])
    score = round(benefit - 0.65 * burden - blocker_penalty, 3)
    return LifecycleInitiativeOption(
        mode=mode,
        intervention_class=intervention_class,
        programme_label=label,
        site_id=site_id,
        site_name=site_name,
        coverage_ratio=coverage,
        burden_score=burden,
        benefit_score=round(benefit, 3),
        total_score=score,
        blockers=blockers or [],
        rationale=rationale or [],
    )


def plan_lifecycle_initiatives(landscape: LifecycleInitiativeLandscape) -> list[LifecycleInitiativePlan]:
    plans: list[LifecycleInitiativePlan] = []
    by_class: dict[str, list[TransitionFailureEvent]] = {}
    for event in landscape.events:
        by_class.setdefault(event.intervention_class, []).append(event)

    for intervention_class, events in sorted(by_class.items()):
        events = sorted(events, key=lambda e: e.occurred_at)
        summary = _summary(events)
        synthetic = any(e.synthetic for e in events)
        programme = PROGRAMMES.get(intervention_class, {"label": f"{intervention_class} service", "metrics": ["verified welfare outcome"]})
        recurrence = (
            summary["events"] >= 4
            and summary["subjects"] >= 2
            and summary["days"] >= 3
            and summary["span_days"] >= 14
            and summary["mean_confidence"] >= 0.6
        )
        if not recurrence:
            recommended = _option(
                intervention_class, "case_level_only", 1.0,
                rationale=["Current evidence does not yet establish a recurring structural service gap."],
            )
            plans.append(LifecycleInitiativePlan(
                plan_id=_stable_id("lplan", landscape.area_id, intervention_class, "case"),
                area_id=landscape.area_id,
                area_name=landscape.area_name,
                intervention_class=intervention_class,
                status="case_level_response_only" if events else "insufficient_evidence",
                structural_gap_established=False,
                evidence_summary=summary,
                recommended=recommended,
                implementation_steps=["Resolve current cases using existing services and continue longitudinal observation."],
                success_metrics=programme["metrics"],
                stop_conditions=["No recurring pattern appears over the monitoring horizon."],
                evidence_gaps=["Need repeated evidence across subjects, dates and at least fourteen days before creating a programme."],
                synthetic=synthetic,
            ))
            continue

        options: list[LifecycleInitiativeOption] = []
        center_lat, center_lon = _centroid(events)

        for service in landscape.existing_services:
            if not service.verified or intervention_class not in service.supported_interventions:
                continue
            coverage = _coverage(events, service.lat, service.lon, service.service_radius_km)
            if coverage >= 0.5:
                blockers = [] if service.may_expand else ["existing_service_expansion_not_verified"]
                options.append(_option(
                    intervention_class, "partner_extension", coverage,
                    site_id=service.service_id, site_name=service.name, blockers=blockers,
                    rationale=["Prefer extending a verified existing service over creating a parallel institution."],
                    reuse_bonus=8,
                ))

        for host in landscape.candidate_hosts:
            if host.supported_interventions and intervention_class not in host.supported_interventions:
                continue
            coverage = _coverage(events, host.lat, host.lon, 8)
            if coverage < 0.5:
                continue
            blockers = [] if host.available and host.availability_evidence_ref else ["host_availability_not_verified"]
            options.append(_option(
                intervention_class, "periodic_pop_up", coverage,
                site_id=host.host_id, site_name=host.name, blockers=blockers,
                rationale=["A reversible periodic service can test whether local access is the structural bottleneck."],
            ))

            permanent_blockers = list(blockers)
            if summary["span_days"] < 56:
                permanent_blockers.append("insufficient_longitudinal_duration_for_permanent_service")
            if summary["events"] < 12 or summary["subjects"] < 4:
                permanent_blockers.append("insufficient_repeated_volume_for_permanent_service")
            options.append(_option(
                intervention_class, "permanent_service", coverage,
                site_id=host.host_id, site_name=host.name, blockers=permanent_blockers,
                rationale=["Permanent capacity is considered only after sustained repeated need and a successful reversible pilot."],
            ))

        distances = [_km(e.lat, e.lon, center_lat, center_lon) for e in events]
        dispersed = max(distances, default=0) >= 6
        mobile_coverage = 0.9
        options.append(_option(
            intervention_class, "mobile_service", mobile_coverage,
            rationale=[
                "A mobile service avoids fixed infrastructure and is especially useful for a dispersed landscape."
                if dispersed else
                "A mobile service remains an alternative when a fixed host is unavailable."
            ],
        ))

        options.sort(key=lambda x: (x.total_score, x.coverage_ratio), reverse=True)
        recommended = options[0]
        status = "ready_for_human_validation" if not recommended.blockers else "pilot_candidate"

        steps = [
            "Freeze the supporting transition-failure events and provenance; synthetic events cannot authorize a live programme.",
            "Verify that participating existing services cannot already absorb the repeated need at acceptable burden.",
            "Obtain explicit competent operator/partner approval for the proposed programme and any required professional authority.",
            "Run a time-bounded reversible pilot before creating permanent capacity.",
            "Measure the target transition outcome and animal-welfare failures, not activity volume alone.",
            "Stop, redesign or hand off if another existing service can achieve the same welfare outcome more safely or cheaply.",
        ]
        plans.append(LifecycleInitiativePlan(
            plan_id=_stable_id("lplan", landscape.area_id, intervention_class, recommended.mode, recommended.site_id or "none"),
            area_id=landscape.area_id,
            area_name=landscape.area_name,
            intervention_class=intervention_class,
            status=status,
            structural_gap_established=True,
            evidence_summary=summary | {"target_centroid": {"lat": round(center_lat, 6), "lon": round(center_lon, 6)}},
            recommended=recommended,
            alternatives=options[1:4],
            implementation_steps=steps,
            success_metrics=programme["metrics"],
            stop_conditions=[
                "No meaningful improvement in the target welfare transition after the pilot horizon.",
                "Serious animal-welfare, public-safety, privacy or audit failure.",
                "Utilization is too low to justify the programme burden.",
                "An existing service can absorb the need more safely/effectively.",
            ],
            evidence_gaps=list(recommended.blockers),
            synthetic=synthetic,
        ))
    return plans


def summarize_plan_types(plans: list[LifecycleInitiativePlan]) -> dict[str, int]:
    return dict(Counter(p.recommended.mode for p in plans))
