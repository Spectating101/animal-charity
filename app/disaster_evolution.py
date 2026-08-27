from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from app.disaster_control import DisasterSnapshot, assess_disaster


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


AccessState = Literal["open", "constrained", "isolated", "unknown"]
AccessTransitionClass = Literal["degradation", "recovery", "uncertainty_change"]


class AccessStateTransition(BaseModel):
    need_id: str
    location_ref: str
    from_as_of: datetime
    to_as_of: datetime
    from_state: AccessState
    to_state: AccessState
    transition_class: AccessTransitionClass
    evidence_refs: list[str] = Field(default_factory=list)


class AccessStateReversal(BaseModel):
    need_id: str
    location_ref: str
    first_as_of: datetime
    middle_as_of: datetime
    final_as_of: datetime
    initial_state: AccessState
    intermediate_state: AccessState
    final_state: AccessState
    first_transition: AccessStateTransition
    second_transition: AccessStateTransition
    evidence_refs: list[str] = Field(default_factory=list)


class DisasterOperationalHistory(BaseModel):
    incident_id: str
    from_as_of: datetime
    to_as_of: datetime
    assessed_at: datetime = Field(default_factory=utcnow)
    snapshot_count: int
    access_state_transitions: list[AccessStateTransition] = Field(default_factory=list)
    access_state_reversals: list[AccessStateReversal] = Field(default_factory=list)
    safe_conclusion: str


class DisasterEvolution(BaseModel):
    incident_id: str
    from_as_of: datetime
    to_as_of: datetime
    assessed_at: datetime = Field(default_factory=utcnow)
    newly_unmet_need_ids: list[str] = Field(default_factory=list)
    explicitly_resolved_need_ids: list[str] = Field(default_factory=list)
    missing_followup_need_ids: list[str] = Field(default_factory=list)
    still_unresolved_need_ids: list[str] = Field(default_factory=list)
    newly_deployable_resource_ids: list[str] = Field(default_factory=list)
    lost_deployable_resource_ids: list[str] = Field(default_factory=list)
    newly_stale_record_ids: list[str] = Field(default_factory=list)
    previous_reservations_invalidated: list[str] = Field(default_factory=list)
    recommendation_stage_changes: dict[str, dict[str, str | None]] = Field(default_factory=dict)
    access_state_transitions: list[AccessStateTransition] = Field(default_factory=list)
    command_context_changed: bool = False
    safe_conclusion: str


def _active_need_ids(snapshot: DisasterSnapshot) -> set[str]:
    return {
        need.need_id
        for need in snapshot.needs
        if need.status != "met" and (need.valid_until is None or need.valid_until >= snapshot.as_of)
    }


def _explicit_met_ids(snapshot: DisasterSnapshot) -> set[str]:
    return {need.need_id for need in snapshot.needs if need.status == "met"}


def _primary_stage_by_need(assessment) -> dict[str, str]:
    result: dict[str, str] = {}
    for finding in assessment.findings:
        if finding.need_id is None:
            continue
        # Preserve the first finding because assessment ordering places urgent
        # safety/evidence gates before lower-order routing/capacity actions.
        result.setdefault(finding.need_id, finding.stage)
    return result


def _transition_class(before: AccessState, after: AccessState) -> AccessTransitionClass:
    if "unknown" in {before, after}:
        return "uncertainty_change"
    severity = {"open": 0, "constrained": 1, "isolated": 2}
    return "degradation" if severity[after] > severity[before] else "recovery"


def _access_transitions(previous: DisasterSnapshot, current: DisasterSnapshot) -> list[AccessStateTransition]:
    previous_by_id = {need.need_id: need for need in previous.needs}
    current_by_id = {need.need_id: need for need in current.needs}
    transitions: list[AccessStateTransition] = []

    # Missing follow-up is deliberately not converted into an access state.
    # A transition exists only when the same need is explicitly observed in
    # both operational periods and its represented access state changed.
    for need_id in sorted(set(previous_by_id).intersection(current_by_id)):
        before = previous_by_id[need_id]
        after = current_by_id[need_id]
        if before.access_status == after.access_status:
            continue
        transitions.append(
            AccessStateTransition(
                need_id=need_id,
                location_ref=after.location_ref,
                from_as_of=previous.as_of,
                to_as_of=current.as_of,
                from_state=before.access_status,
                to_state=after.access_status,
                transition_class=_transition_class(before.access_status, after.access_status),
                evidence_refs=list(dict.fromkeys([before.source_ref, after.source_ref])),
            )
        )
    return transitions


def compare_operational_periods(previous: DisasterSnapshot, current: DisasterSnapshot) -> DisasterEvolution:
    if previous.incident_id != current.incident_id:
        raise ValueError("cannot compare different disaster incidents")
    if current.as_of <= previous.as_of:
        raise ValueError("current disaster snapshot must be later than previous snapshot")

    previous_assessment = assess_disaster(previous)
    current_assessment = assess_disaster(current)

    previous_active = _active_need_ids(previous)
    current_active = _active_need_ids(current)
    current_present = {need.need_id for need in current.needs}
    current_met = _explicit_met_ids(current)

    newly_unmet = sorted(current_active - previous_active)
    explicitly_resolved = sorted(previous_active.intersection(current_met))
    missing_followup = sorted(previous_active - current_present)
    still_unresolved = sorted(previous_active.intersection(current_active))

    previous_resources = {r.record_id for r in previous_assessment.interoperability.deployable_resources}
    current_resources = {r.record_id for r in current_assessment.interoperability.deployable_resources}

    previous_stale = set(previous_assessment.interoperability.stale_record_ids)
    current_stale = set(current_assessment.interoperability.stale_record_ids)

    invalidated: list[str] = []
    for reservation in previous_assessment.proposed_reservations:
        if reservation.resource_record_id not in current_resources:
            invalidated.append(
                f"{reservation.resource_record_id}->{reservation.need_id}: resource no longer deployable"
            )
        elif reservation.need_id in current_met:
            invalidated.append(
                f"{reservation.resource_record_id}->{reservation.need_id}: need explicitly resolved"
            )
        elif reservation.need_id not in current_present:
            invalidated.append(
                f"{reservation.resource_record_id}->{reservation.need_id}: need missing from follow-up; do not assume resolved"
            )

    prev_stages = _primary_stage_by_need(previous_assessment)
    curr_stages = _primary_stage_by_need(current_assessment)
    stage_changes: dict[str, dict[str, str | None]] = {}
    for need_id in sorted(set(prev_stages).union(curr_stages)):
        before = prev_stages.get(need_id)
        after = curr_stages.get(need_id)
        if before != after:
            stage_changes[need_id] = {"from": before, "to": after}

    previous_commands = {
        (context.incident_id, context.authority_ref, context.operational_period)
        for context in previous_assessment.interoperability.command_contexts
    }
    current_commands = {
        (context.incident_id, context.authority_ref, context.operational_period)
        for context in current_assessment.interoperability.command_contexts
    }

    return DisasterEvolution(
        incident_id=current.incident_id,
        from_as_of=previous.as_of,
        to_as_of=current.as_of,
        newly_unmet_need_ids=newly_unmet,
        explicitly_resolved_need_ids=explicitly_resolved,
        missing_followup_need_ids=missing_followup,
        still_unresolved_need_ids=still_unresolved,
        newly_deployable_resource_ids=sorted(current_resources - previous_resources),
        lost_deployable_resource_ids=sorted(previous_resources - current_resources),
        newly_stale_record_ids=sorted(current_stale - previous_stale),
        previous_reservations_invalidated=invalidated,
        recommendation_stage_changes=stage_changes,
        access_state_transitions=_access_transitions(previous, current),
        command_context_changed=previous_commands != current_commands,
        safe_conclusion=(
            "A need disappearing from a later feed is not evidence of resolution. Only explicit outcome evidence may mark a previously unmet "
            "need as resolved. Resource, access and command state must be revalidated each operational period; prior recommendations are not standing orders."
        ),
    )


def trace_operational_history(snapshots: list[DisasterSnapshot]) -> DisasterOperationalHistory:
    if len(snapshots) < 2:
        raise ValueError("operational history requires at least two disaster snapshots")

    incident_id = snapshots[0].incident_id
    for index, snapshot in enumerate(snapshots):
        if snapshot.incident_id != incident_id:
            raise ValueError("cannot trace operational history across different disaster incidents")
        if index and snapshot.as_of <= snapshots[index - 1].as_of:
            raise ValueError("operational history snapshots must be strictly increasing in time")

    transitions: list[AccessStateTransition] = []
    for previous, current in zip(snapshots, snapshots[1:]):
        transitions.extend(_access_transitions(previous, current))

    # Detect A -> B -> A only across three consecutive explicit observations.
    # A missing middle observation or an unknown state cannot manufacture a
    # reversal signal.
    reversals: list[AccessStateReversal] = []
    for first, middle, final in zip(snapshots, snapshots[1:], snapshots[2:]):
        first_by_id = {need.need_id: need for need in first.needs}
        middle_by_id = {need.need_id: need for need in middle.needs}
        final_by_id = {need.need_id: need for need in final.needs}
        common_ids = sorted(set(first_by_id).intersection(middle_by_id, final_by_id))
        for need_id in common_ids:
            a = first_by_id[need_id]
            b = middle_by_id[need_id]
            c = final_by_id[need_id]
            if "unknown" in {a.access_status, b.access_status, c.access_status}:
                continue
            if a.access_status != c.access_status or a.access_status == b.access_status:
                continue

            first_transition = next(
                (
                    item
                    for item in transitions
                    if item.need_id == need_id
                    and item.from_as_of == first.as_of
                    and item.to_as_of == middle.as_of
                ),
                None,
            )
            second_transition = next(
                (
                    item
                    for item in transitions
                    if item.need_id == need_id
                    and item.from_as_of == middle.as_of
                    and item.to_as_of == final.as_of
                ),
                None,
            )
            if first_transition is None or second_transition is None:
                continue

            reversals.append(
                AccessStateReversal(
                    need_id=need_id,
                    location_ref=c.location_ref,
                    first_as_of=first.as_of,
                    middle_as_of=middle.as_of,
                    final_as_of=final.as_of,
                    initial_state=a.access_status,
                    intermediate_state=b.access_status,
                    final_state=c.access_status,
                    first_transition=first_transition,
                    second_transition=second_transition,
                    evidence_refs=list(dict.fromkeys([a.source_ref, b.source_ref, c.source_ref])),
                )
            )

    return DisasterOperationalHistory(
        incident_id=incident_id,
        from_as_of=snapshots[0].as_of,
        to_as_of=snapshots[-1].as_of,
        snapshot_count=len(snapshots),
        access_state_transitions=transitions,
        access_state_reversals=reversals,
        safe_conclusion=(
            "Operational truth is time-indexed. A route that was open can later become isolated and later reopen; the newest explicit observation supersedes prior state for current operations without erasing the historical transitions. Missing or unknown observations do not create a reversal by inference."
        ),
    )
