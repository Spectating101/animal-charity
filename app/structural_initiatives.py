from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class StructuralNeedEvent(BaseModel):
    event_id: str
    subject_ref: str
    problem_type: str
    bottleneck: str
    occurred_at: datetime
    lat: float
    lon: float
    severity: Literal["watch", "urgent", "critical"] = "urgent"
    estimated_gap_kg: float = Field(default=0, ge=0)
    source_ref: str
    confidence: float = Field(default=1.0, ge=0, le=1)
    synthetic: bool = False


class ExistingServiceNode(BaseModel):
    service_id: str
    name: str
    kind: str
    lat: float
    lon: float
    source_ref: str
    verified: bool = True
    may_host_extension: bool = False
    service_radius_km: float = Field(default=8, gt=0)


class CandidateSite(BaseModel):
    site_id: str
    name: str
    lat: float
    lon: float
    source_ref: str
    host_type: str = "candidate_host"
    available: bool = False
    availability_evidence_ref: str | None = None
    fixed_setup_cost_twd: float = Field(default=0, ge=0)
    weekly_operating_cost_twd: float = Field(default=0, ge=0)
    weekly_capacity_kg: float = Field(default=0, ge=0)


class StructuralLandscape(BaseModel):
    area_id: str
    area_name: str
    horizon_days: int = Field(default=90, gt=0)
    need_events: list[StructuralNeedEvent] = Field(default_factory=list)
    existing_services: list[ExistingServiceNode] = Field(default_factory=list)
    candidate_sites: list[CandidateSite] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class InitiativeOption(BaseModel):
    option_type: Literal[
        "case_level_only",
        "partner_extension",
        "weekly_pop_up_hub",
        "mobile_distribution_route",
        "permanent_microhub",
    ]
    site_id: str | None = None
    site_name: str | None = None
    coverage_ratio: float = Field(ge=0, le=1)
    estimated_weekly_gap_kg: float = Field(ge=0)
    estimated_weekly_cost_twd: float = Field(ge=0)
    setup_cost_twd: float = Field(ge=0)
    burden_score: float = Field(ge=0, le=100)
    benefit_score: float = Field(ge=0, le=100)
    total_score: float
    rationale: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class InitiativePlan(BaseModel):
    plan_id: str
    area_id: str
    area_name: str
    generated_at: datetime = Field(default_factory=utcnow)
    status: Literal[
        "insufficient_evidence",
        "case_level_response_only",
        "initiative_candidate",
        "ready_for_host_validation",
    ]
    structural_gap_established: bool
    evidence_summary: dict
    recommended: InitiativeOption
    alternatives: list[InitiativeOption] = Field(default_factory=list)
    implementation_steps: list[str] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    graduation_path: str | None = None
    synthetic: bool = False


SEVERITY_WEIGHT = {"watch": 0.5, "urgent": 1.0, "critical": 1.5}


def _weighted(events: list[StructuralNeedEvent]) -> float:
    return sum(SEVERITY_WEIGHT[e.severity] * e.confidence for e in events)


def _centroid(events: list[StructuralNeedEvent]) -> tuple[float, float]:
    weights = [max(0.1, SEVERITY_WEIGHT[e.severity] * e.confidence) for e in events]
    total = sum(weights)
    return (
        sum(e.lat * w for e, w in zip(events, weights)) / total,
        sum(e.lon * w for e, w in zip(events, weights)) / total,
    )


def _recurrence_summary(events: list[StructuralNeedEvent], horizon_days: int) -> dict:
    subjects = {e.subject_ref for e in events}
    days = {e.occurred_at.date().isoformat() for e in events}
    if events:
        span_days = max(1, (max(e.occurred_at for e in events) - min(e.occurred_at for e in events)).days + 1)
    else:
        span_days = 0
    weeks = max(1.0, min(horizon_days, max(span_days, 7)) / 7)
    weekly_gap = sum(e.estimated_gap_kg for e in events) / weeks
    return {
        "events": len(events),
        "distinct_subjects": len(subjects),
        "distinct_days": len(days),
        "span_days": span_days,
        "weighted_need": round(_weighted(events), 3),
        "estimated_weekly_gap_kg": round(weekly_gap, 3),
        "bottlenecks": dict(Counter(e.bottleneck for e in events)),
    }


def _uncovered_events(landscape: StructuralLandscape) -> list[StructuralNeedEvent]:
    uncovered: list[StructuralNeedEvent] = []
    for event in landscape.need_events:
        covered = any(
            node.verified and _km(event.lat, event.lon, node.lat, node.lon) <= node.service_radius_km
            for node in landscape.existing_services
        )
        if not covered:
            uncovered.append(event)
    return uncovered


def _coverage(events: list[StructuralNeedEvent], lat: float, lon: float, radius_km: float) -> float:
    if not events:
        return 0.0
    total = _weighted(events)
    if total <= 0:
        return 0.0
    reached = _weighted([e for e in events if _km(e.lat, e.lon, lat, lon) <= radius_km])
    return max(0.0, min(1.0, reached / total))


def _score_option(*, coverage: float, weekly_cost: float, setup_cost: float, complexity: float, weekly_gap: float) -> tuple[float, float, float]:
    scale_bonus = min(20.0, weekly_gap / 5.0)
    benefit = min(100.0, coverage * 80 + scale_bonus)
    normalized_cost = min(60.0, weekly_cost / 100 + setup_cost / 1000)
    burden = min(100.0, normalized_cost + complexity)
    return round(benefit, 3), round(burden, 3), round(benefit - 0.65 * burden, 3)


def _case_level_option(summary: dict) -> InitiativeOption:
    return InitiativeOption(
        option_type="case_level_only",
        coverage_ratio=1.0,
        estimated_weekly_gap_kg=summary["estimated_weekly_gap_kg"],
        estimated_weekly_cost_twd=0,
        setup_cost_twd=0,
        burden_score=5,
        benefit_score=30,
        total_score=26.75,
        rationale=["Observed pattern does not yet justify new standing infrastructure."],
    )


def plan_structural_initiative(landscape: StructuralLandscape) -> InitiativePlan:
    events = sorted(landscape.need_events, key=lambda e: e.occurred_at)
    summary = _recurrence_summary(events, landscape.horizon_days)
    synthetic = any(e.synthetic for e in events)
    evidence_gaps: list[str] = []

    # Structural infrastructure needs repeated need across time and more than one subject.
    recurrence_gate = (
        summary["events"] >= 4
        and summary["distinct_subjects"] >= 2
        and summary["distinct_days"] >= 3
        and summary["span_days"] >= 14
        and summary["weighted_need"] >= 3.0
    )
    if not recurrence_gate:
        evidence_gaps.append(
            "Need at least four credible events across two subjects, three dates and fourteen days before proposing standing infrastructure."
        )
        return InitiativePlan(
            plan_id=_stable_id("iplan", landscape.area_id, "case-level"),
            area_id=landscape.area_id,
            area_name=landscape.area_name,
            status="case_level_response_only" if events else "insufficient_evidence",
            structural_gap_established=False,
            evidence_summary=summary,
            recommended=_case_level_option(summary),
            implementation_steps=["Resolve current cases with existing services/actuators and continue collecting condition evidence."],
            success_metrics=["case resolution time", "preventable unresolved welfare-gap time"],
            stop_conditions=["No recurring pattern is observed after the monitoring horizon."],
            evidence_gaps=evidence_gaps,
            synthetic=synthetic,
        )

    uncovered = _uncovered_events(landscape)
    uncovered_weight = _weighted(uncovered)
    total_weight = max(_weighted(events), 0.001)
    uncovered_ratio = uncovered_weight / total_weight
    recurrent_access_bottleneck = sum(
        1 for e in events if e.bottleneck in {"last_mile_logistics", "coordination", "service_access_gap"}
    ) >= 3
    service_gap_gate = uncovered_ratio >= 0.5 or recurrent_access_bottleneck
    if not service_gap_gate:
        evidence_gaps.append("Repeated need is present, but current evidence does not establish a geographic/service-access gap.")
        return InitiativePlan(
            plan_id=_stable_id("iplan", landscape.area_id, "existing-services"),
            area_id=landscape.area_id,
            area_name=landscape.area_name,
            status="case_level_response_only",
            structural_gap_established=False,
            evidence_summary=summary | {"uncovered_weight_ratio": round(uncovered_ratio, 3)},
            recommended=_case_level_option(summary),
            implementation_steps=["Improve routing into existing services before creating new infrastructure."],
            success_metrics=["existing-service utilization", "case resolution time"],
            stop_conditions=["Existing service routing resolves the repeated gap."],
            evidence_gaps=evidence_gaps,
            synthetic=synthetic,
        )

    target_events = uncovered if uncovered else events
    weekly_gap = summary["estimated_weekly_gap_kg"]
    center_lat, center_lon = _centroid(target_events)
    options: list[InitiativeOption] = []

    # Extending an existing verified service is preferred when it is close enough and explicitly marked as extension-capable.
    for node in landscape.existing_services:
        if not node.verified or not node.may_host_extension:
            continue
        coverage = _coverage(target_events, node.lat, node.lon, max(node.service_radius_km, 10))
        if coverage < 0.5:
            continue
        benefit, burden, total = _score_option(
            coverage=coverage, weekly_cost=800, setup_cost=2000, complexity=12, weekly_gap=weekly_gap
        )
        options.append(InitiativeOption(
            option_type="partner_extension",
            site_id=node.service_id,
            site_name=node.name,
            coverage_ratio=round(coverage, 3),
            estimated_weekly_gap_kg=weekly_gap,
            estimated_weekly_cost_twd=800,
            setup_cost_twd=2000,
            burden_score=burden,
            benefit_score=benefit,
            total_score=total + 5,  # reuse bonus
            rationale=["Reuses a verified existing welfare node instead of creating a new institution."],
        ))

    for site in landscape.candidate_sites:
        coverage = _coverage(target_events, site.lat, site.lon, 8)
        if coverage < 0.5:
            continue
        blockers = [] if site.available and site.availability_evidence_ref else ["host_availability_not_verified"]
        weekly_cost = site.weekly_operating_cost_twd or 1500
        setup = site.fixed_setup_cost_twd or 3000
        benefit, burden, total = _score_option(
            coverage=coverage, weekly_cost=weekly_cost, setup_cost=setup, complexity=18, weekly_gap=weekly_gap
        )
        if blockers:
            total -= 15
        options.append(InitiativeOption(
            option_type="weekly_pop_up_hub",
            site_id=site.site_id,
            site_name=site.name,
            coverage_ratio=round(coverage, 3),
            estimated_weekly_gap_kg=weekly_gap,
            estimated_weekly_cost_twd=weekly_cost,
            setup_cost_twd=setup,
            burden_score=burden,
            benefit_score=benefit,
            total_score=round(total + 4, 3),
            rationale=["Creates a reversible weekly distribution point near the observed need cluster."],
            blockers=blockers,
        ))

        # Permanent infrastructure is penalized until the recurring load is large and host availability is proven.
        permanent_cost = max(weekly_cost * 2, 3000)
        permanent_setup = max(setup * 5, 20000)
        p_benefit, p_burden, p_total = _score_option(
            coverage=coverage, weekly_cost=permanent_cost, setup_cost=permanent_setup, complexity=35, weekly_gap=weekly_gap
        )
        p_blockers = list(blockers)
        if summary["span_days"] < 56:
            p_blockers.append("insufficient_duration_for_permanent_site")
        if weekly_gap < 100:
            p_blockers.append("insufficient_verified_weekly_volume_for_permanent_site")
        p_total -= 12 * len(p_blockers)
        options.append(InitiativeOption(
            option_type="permanent_microhub",
            site_id=site.site_id,
            site_name=site.name,
            coverage_ratio=round(coverage, 3),
            estimated_weekly_gap_kg=weekly_gap,
            estimated_weekly_cost_twd=permanent_cost,
            setup_cost_twd=permanent_setup,
            burden_score=p_burden,
            benefit_score=p_benefit,
            total_score=round(p_total, 3),
            rationale=["Could create durable local capacity, but only after sustained demand and host validation."],
            blockers=p_blockers,
        ))

    # A mobile route can serve a dispersed cluster without a new fixed site.
    distances = [_km(e.lat, e.lon, center_lat, center_lon) for e in target_events]
    dispersion = max(distances, default=0) - min(distances, default=0)
    mobile_coverage = 0.9 if target_events else 0
    m_benefit, m_burden, m_total = _score_option(
        coverage=mobile_coverage,
        weekly_cost=1800,
        setup_cost=1000,
        complexity=20 + min(20, dispersion * 2),
        weekly_gap=weekly_gap,
    )
    options.append(InitiativeOption(
        option_type="mobile_distribution_route",
        coverage_ratio=mobile_coverage,
        estimated_weekly_gap_kg=weekly_gap,
        estimated_weekly_cost_twd=1800,
        setup_cost_twd=1000,
        burden_score=m_burden,
        benefit_score=m_benefit,
        total_score=m_total,
        rationale=["Avoids fixed infrastructure and can serve multiple dispersed recipients on a scheduled route."],
    ))

    options.sort(key=lambda o: (o.total_score, o.coverage_ratio), reverse=True)
    recommended = options[0] if options else _case_level_option(summary)
    alternatives = options[1:4]

    if recommended.option_type == "case_level_only":
        status = "case_level_response_only"
    elif recommended.blockers:
        status = "initiative_candidate"
    else:
        status = "ready_for_host_validation"

    steps = [
        "Freeze the supporting ProblemCases and source references; do not use synthetic evidence for a live launch decision.",
        "Validate the proposed host/site and obtain explicit operator permission.",
        "Run an 8-week reversible pilot with a fixed service schedule, intake rules and named human owner.",
        "Route only verified appropriate resources through the existing human safety/eligibility gates.",
        "Measure whether unresolved welfare gaps, emergency trips and recipient travel burden actually fall.",
    ]
    if recommended.option_type == "mobile_distribution_route":
        steps[2] = "Run an 8-week scheduled mobile-route pilot with predefined stops and a named logistics owner."
    elif recommended.option_type == "partner_extension":
        steps[2] = "Run an 8-week extension pilot inside the existing partner workflow rather than creating a new entity."

    return InitiativePlan(
        plan_id=_stable_id("iplan", landscape.area_id, recommended.option_type, recommended.site_id or "none"),
        area_id=landscape.area_id,
        area_name=landscape.area_name,
        status=status,
        structural_gap_established=True,
        evidence_summary=summary | {
            "uncovered_weight_ratio": round(uncovered_ratio, 3),
            "target_centroid": {"lat": round(center_lat, 6), "lon": round(center_lon, 6)},
        },
        recommended=recommended,
        alternatives=alternatives,
        implementation_steps=steps,
        success_metrics=[
            "preventable unresolved welfare-gap hours/animal-days",
            "share of recurring cases resolved before crisis threshold",
            "recipient travel/transport burden",
            "resource spoilage or failed-delivery rate",
            "cost per verified protected animal-day",
            "human override and safety-incident rate",
        ],
        stop_conditions=[
            "No meaningful reduction in recurring unresolved gaps after the pilot horizon.",
            "Serious safety, custody, privacy or audit failure.",
            "Utilization is too low to justify the operating burden.",
            "An existing service can absorb the same need more cheaply or safely.",
        ],
        evidence_gaps=evidence_gaps + list(recommended.blockers),
        graduation_path=(
            "If the reversible pilot demonstrates sustained demand, safe operations and lower unresolved-gap burden, "
            "re-score a permanent microhub using real observed volume and costs."
        ),
        synthetic=synthetic,
    )


def load_structural_landscape(path: str | Path) -> StructuralLandscape:
    return StructuralLandscape.model_validate_json(Path(path).read_text(encoding="utf-8"))


def dump_plan(plan: InitiativePlan) -> str:
    return json.dumps(plan.model_dump(mode="json"), indent=2, ensure_ascii=False)
