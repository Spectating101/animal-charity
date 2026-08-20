from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.disaster_control import DisasterSnapshot, assess_disaster


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


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
        command_context_changed=previous_commands != current_commands,
        safe_conclusion=(
            "A need disappearing from a later feed is not evidence of resolution. Only explicit outcome evidence may mark a previously unmet "
            "need as resolved. Resource and command state must be revalidated each operational period; prior recommendations are not standing orders."
        ),
    )
