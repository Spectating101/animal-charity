from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.public_good_control import PublicGoodAssessment, PublicGoodCase, assess_public_good_case


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReplayReference(BaseModel):
    expected_primary_stages: list[Literal[
        "safety", "stabilize", "prevent", "route", "integrity", "capacity", "access", "outcome", "evidence"
    ]] = Field(default_factory=list)
    historical_action: str | None = None
    historical_outcome_summary: str | None = None
    reference_refs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ReplayPacket(BaseModel):
    replay_id: str
    decision_cutoff: datetime
    case: PublicGoodCase
    reference: ReplayReference | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReplayRun(BaseModel):
    replay_id: str
    decision_cutoff: datetime
    assessed_at: datetime = Field(default_factory=utcnow)
    assessment: PublicGoodAssessment
    hindsight_evidence_rejected: bool = True
    reference_hidden: bool = True


class ReplayScore(BaseModel):
    replay_id: str
    predicted_primary_stage: str | None
    expected_primary_stages: list[str]
    primary_stage_match: bool | None
    predicted_structural_candidate: bool
    historical_action: str | None = None
    historical_outcome_summary: str | None = None
    reference_refs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _future_evidence(value: Any, cutoff: datetime, path: str = "case.payload") -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in {"observed_at", "occurred_at", "confirmed_at", "measured_at", "recorded_at"}:
                dt = _parse_time(item)
                if dt is not None and dt > cutoff:
                    violations.append(child)
            violations.extend(_future_evidence(item, cutoff, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            violations.extend(_future_evidence(item, cutoff, f"{path}[{index}]"))
    return violations


def run_replay(packet: ReplayPacket) -> ReplayRun:
    if packet.decision_cutoff.tzinfo is None:
        raise ValueError("decision_cutoff must be timezone-aware")
    violations = _future_evidence(packet.case.payload, packet.decision_cutoff)
    if violations:
        raise ValueError(
            "replay contains evidence timestamped after the decision cutoff: " + ", ".join(violations[:10])
        )
    assessment = assess_public_good_case(packet.case)
    return ReplayRun(
        replay_id=packet.replay_id,
        decision_cutoff=packet.decision_cutoff,
        assessment=assessment,
    )


def score_replay(packet: ReplayPacket) -> ReplayScore:
    if packet.reference is None:
        raise ValueError("replay reference is required for scoring")
    run = run_replay(packet)
    predicted = run.assessment.normalized_findings[0].stage if run.assessment.normalized_findings else None
    expected = list(packet.reference.expected_primary_stages)
    matched = None if not expected else predicted in expected
    structural = any(finding.structural_candidate for finding in run.assessment.normalized_findings)
    notes = list(packet.reference.notes)
    notes.append(
        "Stage agreement is an R1 diagnostic measure only; it does not prove the recommendation caused or would have caused the historical outcome."
    )
    return ReplayScore(
        replay_id=packet.replay_id,
        predicted_primary_stage=predicted,
        expected_primary_stages=expected,
        primary_stage_match=matched,
        predicted_structural_candidate=structural,
        historical_action=packet.reference.historical_action,
        historical_outcome_summary=packet.reference.historical_outcome_summary,
        reference_refs=packet.reference.reference_refs,
        notes=notes,
    )
