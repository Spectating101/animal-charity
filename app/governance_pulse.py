from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SignalDirection(str, Enum):
    adverse = "adverse"
    improvement = "improvement"
    ambiguous = "ambiguous"


class SignalLevel(str, Enum):
    activity = "activity"
    output = "output"
    outcome = "outcome"
    system = "system"


class Significance(str, Enum):
    watch = "watch"
    moderate = "moderate"
    major = "major"
    critical = "critical"


class ScopeLevel(str, Enum):
    local = "local"
    district = "district"
    province = "province"
    multi_region = "multi_region"
    national = "national"


class CoverageStatus(str, Enum):
    unknown = "unknown"
    partial = "partial"
    bounded = "bounded"
    complete = "complete"


class GovernanceSignal(BaseModel):
    signal_id: str
    domain: str
    topic: str
    geography: str
    scope_level: ScopeLevel = ScopeLevel.local
    observed_at: datetime
    effective_period_start: datetime | None = None
    effective_period_end: datetime | None = None
    source_ref: str
    direction: SignalDirection
    level: SignalLevel
    significance: Significance = Significance.moderate
    verification_status: Literal["reported", "corroborated", "verified"] = "reported"
    condition_class: str
    summary: str
    direction_basis: str | None = None
    significance_basis: str | None = None
    intervention_refs: list[str] = Field(default_factory=list)
    metric_name: str | None = None
    metric_value: float | None = None
    metric_unit: str | None = None
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def signal_is_coherent(self) -> "GovernanceSignal":
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        for value, name in (
            (self.effective_period_start, "effective_period_start"),
            (self.effective_period_end, "effective_period_end"),
        ):
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.effective_period_start and self.effective_period_end:
            if self.effective_period_end < self.effective_period_start:
                raise ValueError("effective_period_end cannot precede effective_period_start")
        if self.metric_value is not None and not self.metric_name:
            raise ValueError("metric_name is required when metric_value is supplied")
        if self.level == SignalLevel.activity and self.direction != SignalDirection.ambiguous:
            raise ValueError("activity records must use ambiguous direction; an attempted response is not itself state improvement")
        if self.direction != SignalDirection.ambiguous and not self.direction_basis:
            raise ValueError("direction_basis is required for adverse/improvement state claims")
        if self.significance in {Significance.major, Significance.critical} and not self.significance_basis:
            raise ValueError("significance_basis is required for major/critical signals")
        return self


class TopicPulse(BaseModel):
    domain: str
    topic: str
    adverse_signal_ids: list[str] = Field(default_factory=list)
    improvement_signal_ids: list[str] = Field(default_factory=list)
    output_signal_ids: list[str] = Field(default_factory=list)
    activity_signal_ids: list[str] = Field(default_factory=list)
    ambiguous_signal_ids: list[str] = Field(default_factory=list)
    lagged_signal_ids: list[str] = Field(default_factory=list)
    learning_candidate_ids: list[str] = Field(default_factory=list)
    preservation_candidate_ids: list[str] = Field(default_factory=list)
    regression_watch_ids: list[str] = Field(default_factory=list)
    scope_warning: str | None = None
    interpretation: str
    next_review_actions: list[str] = Field(default_factory=list)


class GovernancePulseInput(BaseModel):
    pulse_id: str
    period_start: datetime
    period_end: datetime
    coverage_status: CoverageStatus = CoverageStatus.unknown
    selection_protocol: str | None = None
    known_gaps: list[str] = Field(default_factory=list)
    signals: list[GovernanceSignal] = Field(default_factory=list)

    @model_validator(mode="after")
    def period_is_valid(self) -> "GovernancePulseInput":
        if self.period_start.tzinfo is None or self.period_end.tzinfo is None:
            raise ValueError("pulse period must be timezone-aware")
        if self.period_end < self.period_start:
            raise ValueError("period_end cannot precede period_start")
        ids = [signal.signal_id for signal in self.signals]
        if len(ids) != len(set(ids)):
            raise ValueError("signal_id values must be unique")
        for signal in self.signals:
            if not (self.period_start <= signal.observed_at <= self.period_end):
                raise ValueError(f"signal {signal.signal_id} was not observed/reported inside pulse period")
        if self.coverage_status != CoverageStatus.unknown and not self.selection_protocol:
            raise ValueError("selection_protocol is required when pulse coverage is characterized")
        return self


class GovernancePulse(BaseModel):
    pulse_id: str
    period_start: datetime
    period_end: datetime
    coverage_status: CoverageStatus
    selection_protocol: str | None = None
    known_gaps: list[str] = Field(default_factory=list)
    extreme_claim_allowed: bool = False
    adverse_frontier: list[GovernanceSignal] = Field(default_factory=list)
    progress_frontier: list[GovernanceSignal] = Field(default_factory=list)
    operational_outputs: list[GovernanceSignal] = Field(default_factory=list)
    response_activity: list[GovernanceSignal] = Field(default_factory=list)
    ambiguous_signals: list[GovernanceSignal] = Field(default_factory=list)
    lagged_context: list[GovernanceSignal] = Field(default_factory=list)
    topic_pulses: list[TopicPulse] = Field(default_factory=list)
    ranking_note: str
    safe_conclusion: str


_SIGNIFICANCE_ORDER = {
    Significance.critical: 0,
    Significance.major: 1,
    Significance.moderate: 2,
    Significance.watch: 3,
}
_VERIFICATION_ORDER = {"verified": 0, "corroborated": 1, "reported": 2}
_LEVEL_ORDER = {
    SignalLevel.system: 0,
    SignalLevel.outcome: 1,
    SignalLevel.output: 2,
    SignalLevel.activity: 3,
}


def _sort_key(signal: GovernanceSignal) -> tuple[int, int, int, float, str]:
    return (
        _SIGNIFICANCE_ORDER[signal.significance],
        _VERIFICATION_ORDER[signal.verification_status],
        _LEVEL_ORDER[signal.level],
        -signal.observed_at.timestamp(),
        signal.signal_id,
    )


def _is_lagged(signal: GovernanceSignal, period_start: datetime) -> bool:
    effective_end = signal.effective_period_end or signal.effective_period_start
    return effective_end is not None and effective_end < period_start


def _is_learning_candidate(signal: GovernanceSignal) -> bool:
    return (
        signal.direction == SignalDirection.improvement
        and signal.level in {SignalLevel.outcome, SignalLevel.system}
        and signal.verification_status in {"corroborated", "verified"}
        and bool(signal.intervention_refs)
    )


def _is_preservation_candidate(signal: GovernanceSignal) -> bool:
    return (
        signal.direction == SignalDirection.improvement
        and signal.level in {SignalLevel.outcome, SignalLevel.system}
        and signal.verification_status in {"corroborated", "verified"}
        and bool(signal.intervention_refs)
    )


def _scope_warning(signals: list[GovernanceSignal]) -> str | None:
    comparison_signals = [
        signal
        for signal in signals
        if signal.level in {SignalLevel.outcome, SignalLevel.system}
        and signal.direction in {SignalDirection.adverse, SignalDirection.improvement}
    ]
    scopes = {signal.scope_level for signal in comparison_signals}
    if len(scopes) <= 1:
        return None
    names = ", ".join(sorted(scope.value for scope in scopes))
    return (
        f"Mixed geographic scopes are present ({names}). Use the parallel frontiers for issue selection, but do not treat local and broader signals as direct performance comparators without normalization."
    )


def build_governance_pulse(payload: GovernancePulseInput) -> GovernancePulse:
    lagged = sorted(
        [signal for signal in payload.signals if _is_lagged(signal, payload.period_start)],
        key=_sort_key,
    )
    current = [signal for signal in payload.signals if not _is_lagged(signal, payload.period_start)]

    adverse = sorted(
        [signal for signal in current if signal.direction == SignalDirection.adverse],
        key=_sort_key,
    )
    # Only current target-state outcomes/system changes count as the progress frontier.
    # Operational products remain valuable, but are kept in their own lane until
    # beneficiary/service/environmental outcome evidence exists.
    progress = sorted(
        [
            signal
            for signal in current
            if signal.direction == SignalDirection.improvement
            and signal.level in {SignalLevel.outcome, SignalLevel.system}
        ],
        key=_sort_key,
    )
    outputs = sorted(
        [signal for signal in current if signal.level == SignalLevel.output],
        key=_sort_key,
    )
    activity = sorted(
        [signal for signal in current if signal.level == SignalLevel.activity],
        key=_sort_key,
    )
    ambiguous = sorted(
        [
            signal
            for signal in current
            if signal.direction == SignalDirection.ambiguous and signal.level != SignalLevel.activity
        ],
        key=_sort_key,
    )

    grouped: dict[tuple[str, str], list[GovernanceSignal]] = defaultdict(list)
    for signal in payload.signals:
        grouped[(signal.domain, signal.topic)].append(signal)

    topic_pulses: list[TopicPulse] = []
    for (domain, topic), signals in sorted(grouped.items()):
        current_topic = [signal for signal in signals if not _is_lagged(signal, payload.period_start)]
        lagged_ids = [signal.signal_id for signal in signals if _is_lagged(signal, payload.period_start)]
        adverse_ids = [s.signal_id for s in current_topic if s.direction == SignalDirection.adverse]
        improvement_ids = [
            s.signal_id
            for s in current_topic
            if s.direction == SignalDirection.improvement and s.level in {SignalLevel.outcome, SignalLevel.system}
        ]
        output_ids = [s.signal_id for s in current_topic if s.level == SignalLevel.output]
        activity_ids = [s.signal_id for s in current_topic if s.level == SignalLevel.activity]
        ambiguous_ids = [
            s.signal_id for s in current_topic if s.direction == SignalDirection.ambiguous and s.level != SignalLevel.activity
        ]
        learning_ids = [s.signal_id for s in current_topic if _is_learning_candidate(s)]
        preservation_ids = [s.signal_id for s in current_topic if _is_preservation_candidate(s)]
        regression_watch_ids = [
            s.signal_id
            for s in current_topic
            if s.direction == SignalDirection.improvement
            and s.level in {SignalLevel.outcome, SignalLevel.system}
            and s.verification_status in {"corroborated", "verified"}
        ]
        scope_warning = _scope_warning(current_topic)

        next_actions: list[str] = []
        if adverse_ids:
            next_actions.append(
                "Keep adverse states open until the underlying condition improves; diagnose the broken edge instead of allowing positive cases elsewhere to close the problem."
            )
        if improvement_ids:
            next_actions.append(
                "Protect the verified gain from regression and avoid removing associated capability/practice without review; do not infer which intervention caused the gain until mechanism evidence exists."
            )
            next_actions.append(
                "Re-check improvement cases in the next period so temporary success is not mistaken for durable progress."
            )
        if learning_ids:
            next_actions.append(
                "Compare learning candidates against adverse cases only after matching/normalizing hazard, exposure, geography and operational context; then generate testable transfer hypotheses before replication."
            )
        if output_ids:
            next_actions.append(
                "Treat operational outputs as implementation progress only; request beneficiary/service/environmental outcome evidence before promoting them into the progress frontier."
            )
        if activity_ids:
            next_actions.append(
                "Request downstream output/outcome evidence for response activity before promoting it into any progress claim."
            )
        if ambiguous_ids:
            next_actions.append("Resolve ambiguous direction with additional condition/outcome evidence before using it for policy learning.")
        if lagged_ids:
            next_actions.append(
                "Use lagged reports as historical/risk context, not as proof that the same condition remains current; seek a current-period state update."
            )
        if scope_warning:
            next_actions.append("Normalize geographic/exposure scope before paired performance comparison.")

        if adverse_ids and improvement_ids:
            interpretation = (
                "The topic contains both unresolved adverse evidence and verified target-state progress. Preserve both; investigate why outcomes differ only after making the cases comparable."
            )
        elif adverse_ids:
            interpretation = "The topic currently contains adverse evidence without verified target-state progress in this pulse."
        elif improvement_ids:
            interpretation = "The topic contains verified target-state progress but no adverse signal in this pulse; do not infer that the broader problem is absent."
        elif output_ids:
            interpretation = "The topic contains operational outputs but not yet target-state outcome/system progress."
        else:
            interpretation = "The topic contains activity/ambiguous/lagged evidence but no current verified adverse-or-progress outcome classification."

        topic_pulses.append(
            TopicPulse(
                domain=domain,
                topic=topic,
                adverse_signal_ids=adverse_ids,
                improvement_signal_ids=improvement_ids,
                output_signal_ids=output_ids,
                activity_signal_ids=activity_ids,
                ambiguous_signal_ids=ambiguous_ids,
                lagged_signal_ids=lagged_ids,
                learning_candidate_ids=learning_ids,
                preservation_candidate_ids=preservation_ids,
                regression_watch_ids=regression_watch_ids,
                scope_warning=scope_warning,
                interpretation=interpretation,
                next_review_actions=next_actions,
            )
        )

    extreme_claim_allowed = payload.coverage_status == CoverageStatus.complete
    if extreme_claim_allowed:
        ranking_note = (
            "Coverage is declared complete for the stated selection protocol. Frontier ordering is still a triage ordering based on declared significance, verification, evidence level and recency—not a moral or government-performance score."
        )
    else:
        ranking_note = (
            "Coverage is not complete. Do not call the first entries the objectively 'worst' or 'best' news of the month; describe them as the highest-priority adverse/progress signals observed in this bounded corpus."
        )

    return GovernancePulse(
        pulse_id=payload.pulse_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        coverage_status=payload.coverage_status,
        selection_protocol=payload.selection_protocol,
        known_gaps=payload.known_gaps,
        extreme_claim_allowed=extreme_claim_allowed,
        adverse_frontier=adverse,
        progress_frontier=progress,
        operational_outputs=outputs,
        response_activity=activity,
        ambiguous_signals=ambiguous,
        lagged_context=lagged,
        topic_pulses=topic_pulses,
        ranking_note=ranking_note,
        safe_conclusion=(
            "Adverse and improvement signals are parallel governance frontiers, not positive and negative points in a net score. "
            "A successful local outcome does not cancel unresolved harm elsewhere. Activity and operational outputs are not target-state progress. "
            "Reports about a prior condition period remain lagged context rather than current-state proof. Direction and significance require an explicit evidence basis; mixed scopes require normalization before comparison. "
            "Verified progress may justify regression watch and learning review, but a learning/preservation candidate does not establish that the cited intervention caused the improvement or will transfer safely to another context."
        ),
    )
