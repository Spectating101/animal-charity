from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from app.animal_welfare_control import WelfareState


class WelfareOutcome(BaseModel):
    outcome_id: str
    decision_id: str
    subject_ref: str
    intervention_class: str
    from_state: WelfareState
    to_state: WelfareState
    occurred_at: datetime
    verified: bool = False
    source_ref: str
    stable_days_observed: int = Field(default=0, ge=0)
    serious_welfare_incident: bool = False
    returned_to_bad_state: bool = False
    specialist_program: bool = False
    animal_showed_sustained_stress: bool = False
    notes: str | None = None


class OutcomeSummary(BaseModel):
    verified_outcomes: int
    stable_verified_outcomes: int
    interim_verified_outcomes: int
    unstable_or_failed_outcomes: int
    serious_welfare_incidents: int
    specialist_welfare_stops: int
    relapse_events: int
    transition_counts: dict[str, int]
    intervention_counts: dict[str, int]
    interpretation: str


STABLE_STATES = {
    WelfareState.owned_stable,
    WelfareState.stable_home,
    WelfareState.community_cared,
    WelfareState.sanctuary,
    WelfareState.specialist_program,
}

INTERIM_STATES = {
    WelfareState.shelter,
    WelfareState.foster,
    WelfareState.adoption_trial,
    WelfareState.specialist_candidate,
}

BAD_STATES = {
    WelfareState.owned_at_risk,
    WelfareState.lost,
    WelfareState.free_roaming_owned,
    WelfareState.unowned_free_roaming,
}


def classify_outcome(outcome: WelfareOutcome) -> Literal["unverified", "stable", "interim", "failed"]:
    if not outcome.verified:
        return "unverified"
    if outcome.serious_welfare_incident or outcome.returned_to_bad_state or outcome.animal_showed_sustained_stress:
        return "failed"
    if outcome.to_state in STABLE_STATES:
        return "stable"
    if outcome.to_state in INTERIM_STATES:
        return "interim"
    if outcome.to_state in BAD_STATES:
        return "failed"
    return "interim"


def summarize_outcomes(outcomes: list[WelfareOutcome]) -> OutcomeSummary:
    verified = [x for x in outcomes if x.verified]
    classes = [classify_outcome(x) for x in verified]
    transition_counts = Counter(f"{x.from_state.value}->{x.to_state.value}" for x in verified)
    intervention_counts = Counter(x.intervention_class for x in verified)
    serious = sum(1 for x in verified if x.serious_welfare_incident)
    specialist_stops = sum(
        1 for x in verified
        if x.specialist_program and (x.animal_showed_sustained_stress or x.serious_welfare_incident)
    )
    relapse = sum(1 for x in verified if x.returned_to_bad_state)

    if not verified:
        interpretation = "No verified outcomes are available; the control plane cannot claim welfare impact."
    elif classes.count("failed"):
        interpretation = (
            "Verified outcomes include welfare failures/relapses. Treat them symmetrically: investigate route quality, "
            "partner execution and whether structural policy should change before scaling."
        )
    else:
        interpretation = (
            "Verified outcomes show no recorded welfare failure in this sample, but stability should be judged over a "
            "long enough follow-up horizon rather than at handoff alone."
        )

    return OutcomeSummary(
        verified_outcomes=len(verified),
        stable_verified_outcomes=classes.count("stable"),
        interim_verified_outcomes=classes.count("interim"),
        unstable_or_failed_outcomes=classes.count("failed"),
        serious_welfare_incidents=serious,
        specialist_welfare_stops=specialist_stops,
        relapse_events=relapse,
        transition_counts=dict(transition_counts),
        intervention_counts=dict(intervention_counts),
        interpretation=interpretation,
    )
