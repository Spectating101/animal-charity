from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class PopulationSnapshot(BaseModel):
    area_id: str
    observed_on: date
    observation_coverage: float = Field(ge=0, le=1)
    estimated_free_roaming_animals: int = Field(ge=0)
    estimated_intact_free_roaming_animals: int = Field(ge=0)
    new_litters_30d: int = Field(ge=0)
    public_safety_incidents_30d: int = Field(ge=0)
    wildlife_conflicts_30d: int = Field(ge=0)
    shelter_intakes_30d: int = Field(ge=0)
    verified_reunifications_30d: int = Field(ge=0)
    owner_relinquishments_30d: int = Field(ge=0)
    verified_owner_retention_cases_30d: int = Field(ge=0)
    verified_foster_capacity: int = Field(ge=0)
    stable_placements_30d: int = Field(ge=0)
    placement_returns_30d: int = Field(ge=0)
    source_ref: str
    synthetic: bool = False


class MetricDelta(BaseModel):
    metric: str
    baseline: int | float
    current: int | float
    absolute_change: int | float
    direction: Literal["improved", "worsened", "mixed_or_neutral", "not_interpreted"]


class PopulationComparison(BaseModel):
    area_id: str
    comparable: bool
    coverage_change: float
    deltas: list[MetricDelta]
    positive_signals: list[str]
    negative_signals: list[str]
    interpretation: str
    synthetic: bool = False


LOWER_IS_BETTER = {
    "estimated_free_roaming_animals",
    "estimated_intact_free_roaming_animals",
    "new_litters_30d",
    "public_safety_incidents_30d",
    "wildlife_conflicts_30d",
    "shelter_intakes_30d",
    "owner_relinquishments_30d",
    "placement_returns_30d",
}

HIGHER_IS_BETTER = {
    "verified_reunifications_30d",
    "verified_owner_retention_cases_30d",
    "verified_foster_capacity",
    "stable_placements_30d",
}


def compare_population_snapshots(
    baseline: PopulationSnapshot,
    current: PopulationSnapshot,
    *,
    maximum_coverage_drop: float = 0.15,
) -> PopulationComparison:
    if baseline.area_id != current.area_id:
        raise ValueError("area_id_mismatch")
    if current.observed_on <= baseline.observed_on:
        raise ValueError("current_snapshot_must_be_later")

    coverage_change = round(current.observation_coverage - baseline.observation_coverage, 4)
    comparable = coverage_change >= -maximum_coverage_drop
    deltas: list[MetricDelta] = []
    positive: list[str] = []
    negative: list[str] = []

    metrics = sorted(LOWER_IS_BETTER | HIGHER_IS_BETTER)
    for metric in metrics:
        old = getattr(baseline, metric)
        new = getattr(current, metric)
        change = new - old
        if not comparable:
            direction = "not_interpreted"
        elif change == 0:
            direction = "mixed_or_neutral"
        elif metric in LOWER_IS_BETTER:
            direction = "improved" if change < 0 else "worsened"
        else:
            direction = "improved" if change > 0 else "worsened"
        deltas.append(MetricDelta(
            metric=metric,
            baseline=old,
            current=new,
            absolute_change=change,
            direction=direction,
        ))
        if direction == "improved":
            positive.append(metric)
        elif direction == "worsened":
            negative.append(metric)

    if not comparable:
        interpretation = (
            "Observation coverage fell too much to interpret apparent outcome changes safely; improved-looking counts may be surveillance loss."
        )
    elif negative:
        interpretation = (
            "The landscape shows both positive and adverse outcome signals. Do not collapse them into one score; investigate the worsened metrics before scaling."
        )
    elif positive:
        interpretation = (
            "Several directional welfare/population signals improved with comparable observation coverage. Causal attribution still requires an evaluation design."
        )
    else:
        interpretation = "No directional change was established across the tracked outcome family."

    return PopulationComparison(
        area_id=baseline.area_id,
        comparable=comparable,
        coverage_change=coverage_change,
        deltas=deltas,
        positive_signals=positive,
        negative_signals=negative,
        interpretation=interpretation,
        synthetic=baseline.synthetic or current.synthetic,
    )
