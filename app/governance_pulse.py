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


class GovernanceSignal(BaseModel):
    signal_id: str
    domain: str
    topic: str
    geography: str
    observed_at: datetime
    source_ref: str
    direction: SignalDirection
    level: SignalLevel
    significance: Significance = Significance.moderate
    verification_status: Literal["reported", "corroborated", "verified"] = "reported"
    condition_class: str
    summary: str
    intervention_refs: list[str] = Field(default_factory=list)
    metric_name: str | None = None
    metric_value: float | None = None
    metric_unit: str | None = None
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def signal_is_coherent(self) -> "GovernanceSignal":
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if self.metric_value is not None and not self.metric_name:
            raise ValueError("metric_name is required when metric_value is supplied")
        return self


class TopicPulse(BaseModel):
    domain: str
    topic: str
    adverse_signal_ids: list[str] = Field(default_factory=list)
    improvement_signal_ids: list[str] = Field(default_factory=list)
    activity_signal_ids: list[str] = Field(default_factory=list)
    ambiguous_signal_ids: list[str] = Field(default_factory=list)
    learning_candidate_ids: list[str] = Field(default_factory=list)
    interpretation: str


class GovernancePulseInput(BaseModel):
    pulse_id: str
    period_start: datetime
    period_end: datetime
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
                raise ValueError(f"signal {signal.signal_id} falls outside pulse period")
        return self


class GovernancePulse(BaseModel):
    pulse_id: str
    period_start: datetime
    period_end: datetime
    adverse_frontier: list[GovernanceSignal] = Field(default_factory=list)
    progress_frontier: list[GovernanceSignal] = Field(default_factory=list)
    response_activity: list[GovernanceSignal] = Field(default_factory=list)
    ambiguous_signals: list[GovernanceSignal] = Field(default_factory=list)
    topic_pulses: list[TopicPulse] = Field(default_factory=list)
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


def _is_learning_candidate(signal: GovernanceSignal) -> bool:
    return (
        signal.direction == SignalDirection.improvement
        and signal.level in {SignalLevel.outcome, SignalLevel.system}
        and signal.verification_status in {"corroborated", "verified"}
        and bool(signal.intervention_refs)
    )


def build_governance_pulse(payload: GovernancePulseInput) -> GovernancePulse:
    adverse = sorted(
        [signal for signal in payload.signals if signal.direction == SignalDirection.adverse],
        key=_sort_key,
    )
    # Activity is deliberately separated from progress. Deploying personnel, aircraft,
    # money or equipment is evidence that a response occurred; it is not yet evidence
    # that the public-good state improved.
    progress = sorted(
        [
            signal
            for signal in payload.signals
            if signal.direction == SignalDirection.improvement and signal.level != SignalLevel.activity
        ],
        key=_sort_key,
    )
    activity = sorted(
        [signal for signal in payload.signals if signal.level == SignalLevel.activity],
        key=_sort_key,
    )
    ambiguous = sorted(
        [signal for signal in payload.signals if signal.direction == SignalDirection.ambiguous],
        key=_sort_key,
    )

    grouped: dict[tuple[str, str], list[GovernanceSignal]] = defaultdict(list)
    for signal in payload.signals:
        grouped[(signal.domain, signal.topic)].append(signal)

    topic_pulses: list[TopicPulse] = []
    for (domain, topic), signals in sorted(grouped.items()):
        adverse_ids = [s.signal_id for s in signals if s.direction == SignalDirection.adverse]
        improvement_ids = [
            s.signal_id
            for s in signals
            if s.direction == SignalDirection.improvement and s.level != SignalLevel.activity
        ]
        activity_ids = [s.signal_id for s in signals if s.level == SignalLevel.activity]
        ambiguous_ids = [s.signal_id for s in signals if s.direction == SignalDirection.ambiguous]
        learning_ids = [s.signal_id for s in signals if _is_learning_candidate(s)]

        if adverse_ids and improvement_ids:
            interpretation = (
                "The topic contains both unresolved adverse evidence and verified progress. Preserve both; investigate why outcomes differ across place/time before transferring a practice."
            )
        elif adverse_ids:
            interpretation = "The topic currently contains adverse evidence without a verified improvement signal in this pulse."
        elif improvement_ids:
            interpretation = "The topic contains verified progress but no adverse signal in this pulse; do not infer that the broader problem is absent."
        else:
            interpretation = "The topic contains activity/ambiguous evidence but no verified adverse-or-progress outcome classification."

        topic_pulses.append(
            TopicPulse(
                domain=domain,
                topic=topic,
                adverse_signal_ids=adverse_ids,
                improvement_signal_ids=improvement_ids,
                activity_signal_ids=activity_ids,
                ambiguous_signal_ids=ambiguous_ids,
                learning_candidate_ids=learning_ids,
                interpretation=interpretation,
            )
        )

    return GovernancePulse(
        pulse_id=payload.pulse_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        adverse_frontier=adverse,
        progress_frontier=progress,
        response_activity=activity,
        ambiguous_signals=ambiguous,
        topic_pulses=topic_pulses,
        safe_conclusion=(
            "Adverse and improvement signals are parallel governance frontiers, not positive and negative points in a net score. "
            "A successful local outcome does not cancel unresolved harm elsewhere. Response activity is not counted as progress until an output/outcome/system improvement is observed. "
            "A learning candidate identifies something worth studying; it does not establish that the cited intervention caused the improvement or will transfer safely to another context."
        ),
    )
